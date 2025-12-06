"""
LORAFORGE - GGUF PARSER (PRODUCTION-READY)
Extracts REAL metadata from GGUF model files
No mocked data - only actual file analysis

GGUF Format Specification:
- Magic: GGUF (0x46554747)
- Version: uint32
- Tensor count: uint64
- Metadata KV count: uint64
- Metadata key-value pairs
"""

import os
import struct
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import IntEnum
import hashlib

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning


# GGUF Constants
GGUF_MAGIC = 0x46554747  # "GGUF" in little-endian
GGUF_VERSION_MIN = 2
GGUF_VERSION_MAX = 3


class GGUFValueType(IntEnum):
    """GGUF metadata value types"""
    UINT8 = 0
    INT8 = 1
    UINT16 = 2
    INT16 = 3
    UINT32 = 4
    INT32 = 5
    FLOAT32 = 6
    BOOL = 7
    STRING = 8
    ARRAY = 9
    UINT64 = 10
    INT64 = 11
    FLOAT64 = 12


@dataclass
class GGUFMetadata:
    """Complete GGUF model metadata"""
    # File info
    file_path: str = ""
    file_name: str = ""
    file_size_gb: float = 0.0
    file_hash_sha256: str = ""
    
    # GGUF header
    gguf_version: int = 0
    tensor_count: int = 0
    metadata_kv_count: int = 0
    
    # Model architecture
    architecture: str = ""
    context_length: int = 0
    embedding_length: int = 0
    block_count: int = 0
    attention_head_count: int = 0
    attention_head_count_kv: int = 0
    
    # Quantization
    quantization_version: int = 0
    quantization_type: str = ""
    
    # Model info
    model_name: str = ""
    model_author: str = ""
    model_description: str = ""
    model_license: str = ""
    model_url: str = ""
    
    # Tokenizer
    tokenizer_model: str = ""
    vocab_size: int = 0
    bos_token_id: int = 0
    eos_token_id: int = 0
    
    # Capabilities (derived)
    parameter_count: str = ""
    is_vision: bool = False
    is_uncensored: bool = False
    is_chat_tuned: bool = False
    estimated_vram_gb: float = 0.0
    
    # Quality indicators
    quality_tier: str = ""  # excellent, good, acceptable, poor
    speed_tier: str = ""    # fast, medium, slow
    
    # Raw metadata
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Parsing info
    parsed_at: str = ""
    parse_errors: List[str] = field(default_factory=list)


class GGUFParser:
    """
    Production-ready GGUF file parser.
    Extracts all available metadata from GGUF files.
    """
    
    # Known architecture patterns
    ARCHITECTURES = {
        "llama": ["llama", "llama2", "llama3", "codellama"],
        "qwen": ["qwen", "qwen2"],
        "gemma": ["gemma", "gemma2"],
        "phi": ["phi", "phi2", "phi3"],
        "mistral": ["mistral", "mixtral"],
        "falcon": ["falcon"],
        "deepseek": ["deepseek"],
        "yi": ["yi"],
        "starcoder": ["starcoder", "starcoder2"],
        "gpt2": ["gpt2"],
        "bloom": ["bloom"],
        "mpt": ["mpt"],
        "stablelm": ["stablelm"],
        "internlm": ["internlm"],
        "baichuan": ["baichuan"],
        "command": ["command"],
        "olmo": ["olmo"],
    }
    
    # Vision model indicators
    VISION_INDICATORS = [
        "llava", "bakllava", "vision", "vl", "visual", "image",
        "minicpm-v", "cogvlm", "internvl", "qwen-vl"
    ]
    
    # Uncensored model indicators
    UNCENSORED_INDICATORS = [
        "uncensored", "abliterated", "unfiltered", "nsfw",
        "no-censor", "dolphin", "wizard-vicuna", "hermes"
    ]
    
    def __init__(self):
        self.current_file = None
    
    def parse_file(self, file_path: Path) -> GGUFMetadata:
        """
        Parse a GGUF file and extract all metadata.
        
        Args:
            file_path: Path to GGUF file
            
        Returns:
            GGUFMetadata with all extracted information
        """
        file_path = Path(file_path)
        
        metadata = GGUFMetadata(
            file_path=str(file_path),
            file_name=file_path.name,
            parsed_at=datetime.now().isoformat()
        )
        
        if not file_path.exists():
            metadata.parse_errors.append(f"File not found: {file_path}")
            return metadata
        
        try:
            # Get file size
            stat = file_path.stat()
            metadata.file_size_gb = stat.st_size / (1024 ** 3)
            
            # Parse GGUF structure
            with open(file_path, 'rb') as f:
                self.current_file = f
                
                # Read and validate magic
                magic = struct.unpack('<I', f.read(4))[0]
                if magic != GGUF_MAGIC:
                    metadata.parse_errors.append(f"Invalid GGUF magic: {hex(magic)}")
                    return metadata
                
                # Read version
                metadata.gguf_version = struct.unpack('<I', f.read(4))[0]
                
                if metadata.gguf_version < GGUF_VERSION_MIN:
                    metadata.parse_errors.append(f"Unsupported GGUF version: {metadata.gguf_version}")
                    return metadata
                
                # Read counts
                metadata.tensor_count = struct.unpack('<Q', f.read(8))[0]
                metadata.metadata_kv_count = struct.unpack('<Q', f.read(8))[0]
                
                # Read all metadata key-value pairs
                for _ in range(metadata.metadata_kv_count):
                    try:
                        key, value = self._read_kv_pair(f)
                        if key:
                            metadata.raw_metadata[key] = value
                            self._assign_metadata_field(metadata, key, value)
                    except Exception as e:
                        metadata.parse_errors.append(f"KV parse error: {e}")
                        break
            
            # Derive additional properties
            self._derive_properties(metadata)
            
            # Compute file hash (first 10MB for speed)
            metadata.file_hash_sha256 = self._compute_partial_hash(file_path)
            
        except Exception as e:
            metadata.parse_errors.append(f"Parse error: {e}")
        
        return metadata

    def _read_string(self, f) -> str:
        """Read a GGUF string (length-prefixed)"""
        length = struct.unpack('<Q', f.read(8))[0]
        if length > 1024 * 1024:  # Sanity check: 1MB max
            return ""
        return f.read(length).decode('utf-8', errors='replace')
    
    def _read_value(self, f, value_type: int) -> Any:
        """Read a typed value from GGUF file"""
        if value_type == GGUFValueType.UINT8:
            return struct.unpack('<B', f.read(1))[0]
        elif value_type == GGUFValueType.INT8:
            return struct.unpack('<b', f.read(1))[0]
        elif value_type == GGUFValueType.UINT16:
            return struct.unpack('<H', f.read(2))[0]
        elif value_type == GGUFValueType.INT16:
            return struct.unpack('<h', f.read(2))[0]
        elif value_type == GGUFValueType.UINT32:
            return struct.unpack('<I', f.read(4))[0]
        elif value_type == GGUFValueType.INT32:
            return struct.unpack('<i', f.read(4))[0]
        elif value_type == GGUFValueType.FLOAT32:
            return struct.unpack('<f', f.read(4))[0]
        elif value_type == GGUFValueType.BOOL:
            return struct.unpack('<?', f.read(1))[0]
        elif value_type == GGUFValueType.STRING:
            return self._read_string(f)
        elif value_type == GGUFValueType.ARRAY:
            arr_type = struct.unpack('<I', f.read(4))[0]
            arr_len = struct.unpack('<Q', f.read(8))[0]
            if arr_len > 10000:  # Sanity limit
                return []
            return [self._read_value(f, arr_type) for _ in range(arr_len)]
        elif value_type == GGUFValueType.UINT64:
            return struct.unpack('<Q', f.read(8))[0]
        elif value_type == GGUFValueType.INT64:
            return struct.unpack('<q', f.read(8))[0]
        elif value_type == GGUFValueType.FLOAT64:
            return struct.unpack('<d', f.read(8))[0]
        return None
    
    def _read_kv_pair(self, f) -> Tuple[str, Any]:
        """Read a key-value pair from GGUF file"""
        key = self._read_string(f)
        value_type = struct.unpack('<I', f.read(4))[0]
        value = self._read_value(f, value_type)
        return key, value
    
    def _assign_metadata_field(self, metadata: GGUFMetadata, key: str, value: Any):
        """Assign parsed value to appropriate metadata field"""
        key_lower = key.lower()
        
        # Architecture
        if "general.architecture" in key_lower:
            metadata.architecture = str(value)
        elif "general.name" in key_lower:
            metadata.model_name = str(value)
        elif "general.author" in key_lower:
            metadata.model_author = str(value)
        elif "general.description" in key_lower:
            metadata.model_description = str(value)
        elif "general.license" in key_lower:
            metadata.model_license = str(value)
        elif "general.url" in key_lower:
            metadata.model_url = str(value)
        elif "general.quantization_version" in key_lower:
            metadata.quantization_version = int(value)
        
        # Context
        elif ".context_length" in key_lower:
            metadata.context_length = int(value)
        elif ".embedding_length" in key_lower:
            metadata.embedding_length = int(value)
        elif ".block_count" in key_lower:
            metadata.block_count = int(value)
        elif ".attention.head_count" in key_lower and "_kv" not in key_lower:
            metadata.attention_head_count = int(value)
        elif ".attention.head_count_kv" in key_lower:
            metadata.attention_head_count_kv = int(value)
        
        # Tokenizer
        elif "tokenizer.ggml.model" in key_lower:
            metadata.tokenizer_model = str(value)
        elif "tokenizer.ggml.bos_token_id" in key_lower:
            metadata.bos_token_id = int(value)
        elif "tokenizer.ggml.eos_token_id" in key_lower:
            metadata.eos_token_id = int(value)
        
        # Vocab (array length)
        elif "tokenizer.ggml.tokens" in key_lower and isinstance(value, list):
            metadata.vocab_size = len(value)
    
    def _derive_properties(self, metadata: GGUFMetadata):
        """Derive additional properties from parsed metadata"""
        name_lower = (metadata.file_name + " " + metadata.model_name).lower()
        
        # Detect vision capability
        metadata.is_vision = any(
            ind in name_lower for ind in self.VISION_INDICATORS
        )
        
        # Detect uncensored
        metadata.is_uncensored = any(
            ind in name_lower for ind in self.UNCENSORED_INDICATORS
        )
        
        # Detect chat tuning
        chat_indicators = ["chat", "instruct", "it", "assistant", "rlhf"]
        metadata.is_chat_tuned = any(ind in name_lower for ind in chat_indicators)
        
        # Estimate parameter count from embedding and blocks
        if metadata.embedding_length > 0 and metadata.block_count > 0:
            # Rough estimation based on transformer architecture
            params = (
                metadata.embedding_length * metadata.embedding_length * 4 *  # attention
                metadata.block_count +
                metadata.embedding_length * metadata.vocab_size * 2  # embeddings
            )
            
            if params > 50e9:
                metadata.parameter_count = "70B+"
            elif params > 10e9:
                metadata.parameter_count = f"{int(params/1e9)}B"
            elif params > 1e9:
                metadata.parameter_count = f"{int(params/1e9)}B"
            elif params > 100e6:
                metadata.parameter_count = f"{int(params/1e6)}M"
            else:
                metadata.parameter_count = "small"
        else:
            # Fallback: parse from filename
            metadata.parameter_count = self._parse_params_from_name(name_lower)
        
        # Parse quantization from filename if not in metadata
        if not metadata.quantization_type:
            metadata.quantization_type = self._parse_quantization(name_lower)
        
        # Estimate VRAM requirement
        metadata.estimated_vram_gb = self._estimate_vram(metadata)
        
        # Assign quality tiers
        metadata.quality_tier = self._assign_quality_tier(metadata)
        metadata.speed_tier = self._assign_speed_tier(metadata)

    def _parse_params_from_name(self, name: str) -> str:
        """Parse parameter count from filename"""
        import re
        
        # Common patterns
        patterns = [
            r'(\d+\.?\d*)[xX]?[bB]',  # 7B, 3.5B, 70b
            r'(\d+)[mM]',              # 500M, 1m
            r'-(\d+b)-',               # -7b-
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                num = match.group(1)
                if 'b' in name[match.start():match.end()].lower():
                    return f"{num}B"
                else:
                    return f"{num}M"
        
        return "unknown"
    
    def _parse_quantization(self, name: str) -> str:
        """Parse quantization type from filename"""
        import re
        
        patterns = [
            r'[Qq](\d+)_[Kk]_([MmSs])',  # Q4_K_M, Q5_K_S
            r'[Qq](\d+)_0',               # Q8_0
            r'[Qq](\d+)',                 # Q4, Q8
            r'[Ff]16',                    # F16
            r'[Ff]32',                    # F32
            r'IQ\d+_[XSML]+',             # IQ4_XS
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(0).upper()
        
        return "unknown"
    
    def _estimate_vram(self, metadata: GGUFMetadata) -> float:
        """Estimate VRAM requirement in GB"""
        # Base on file size with quantization overhead
        base_vram = metadata.file_size_gb * 1.2  # 20% overhead
        
        # Add context overhead
        if metadata.context_length > 0:
            ctx_overhead = (metadata.context_length / 4096) * 0.5  # ~0.5GB per 4K context
            base_vram += ctx_overhead
        
        return round(base_vram, 1)
    
    def _assign_quality_tier(self, metadata: GGUFMetadata) -> str:
        """Assign quality tier based on model characteristics"""
        quant = metadata.quantization_type.upper()
        
        # Higher bit quantization = better quality
        if "F32" in quant or "F16" in quant:
            return "excellent"
        elif "Q8" in quant:
            return "excellent"
        elif "Q6" in quant:
            return "good"
        elif "Q5" in quant:
            return "good"
        elif "Q4_K_M" in quant or "Q4_K_L" in quant:
            return "good"
        elif "Q4" in quant:
            return "acceptable"
        elif "Q3" in quant or "Q2" in quant:
            return "poor"
        elif "IQ" in quant:
            return "acceptable"  # imatrix quants are decent
        
        return "unknown"
    
    def _assign_speed_tier(self, metadata: GGUFMetadata) -> str:
        """Assign speed tier based on model size"""
        size = metadata.file_size_gb
        
        if size < 2:
            return "fast"
        elif size < 5:
            return "medium"
        elif size < 10:
            return "slow"
        else:
            return "very_slow"
    
    def _compute_partial_hash(self, file_path: Path, max_bytes: int = 10 * 1024 * 1024) -> str:
        """Compute SHA256 hash of first N bytes for quick identification"""
        hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            data = f.read(max_bytes)
            hasher.update(data)
        
        return hasher.hexdigest()[:16]  # First 16 chars for brevity


@dataclass
class ModelCapabilities:
    """Model capabilities assessment"""
    model_name: str
    
    # Core capabilities (0-10 scale)
    text_generation: int = 0
    instruction_following: int = 0
    code_generation: int = 0
    creative_writing: int = 0
    reasoning: int = 0
    image_understanding: int = 0
    
    # Task suitability
    good_for: List[str] = field(default_factory=list)
    bad_for: List[str] = field(default_factory=list)
    
    # Known issues
    known_issues: List[str] = field(default_factory=list)
    fixes: Dict[str, List[str]] = field(default_factory=dict)


class ModelIndexer:
    """
    Comprehensive model indexer with real metadata extraction.
    """
    
    def __init__(self, models_dir: Path = None):
        self.parser = GGUFParser()
        
        # Default to LM Studio models directory
        if models_dir is None:
            models_dir = Path(os.environ.get(
                "LMSTUDIO_MODELS_PATH",
                "C:/Users/Admin/.lmstudio/models"
            ))
        
        self.models_dir = Path(models_dir)
        self.index: Dict[str, GGUFMetadata] = {}
        self.capabilities: Dict[str, ModelCapabilities] = {}
    
    def scan_all_models(self) -> List[GGUFMetadata]:
        """Scan all GGUF models in directory"""
        print_section("Scanning GGUF Models")
        
        if not self.models_dir.exists():
            print_error(f"Models directory not found: {self.models_dir}")
            return []
        
        models = []
        gguf_files = list(self.models_dir.rglob("*.gguf"))
        
        print_info(f"Found {len(gguf_files)} GGUF files")
        
        for i, file_path in enumerate(gguf_files):
            print_info(f"[{i+1}/{len(gguf_files)}] Parsing: {file_path.name}")
            
            metadata = self.parser.parse_file(file_path)
            models.append(metadata)
            self.index[file_path.name] = metadata
            
            if metadata.parse_errors:
                print_warning(f"  Errors: {len(metadata.parse_errors)}")
        
        print_success(f"Indexed {len(models)} models")
        return models
    
    def get_vision_models(self) -> List[GGUFMetadata]:
        """Get all vision-capable models"""
        return [m for m in self.index.values() if m.is_vision]
    
    def get_uncensored_models(self) -> List[GGUFMetadata]:
        """Get all uncensored models"""
        return [m for m in self.index.values() if m.is_uncensored]
    
    def get_by_size(self, max_size_gb: float) -> List[GGUFMetadata]:
        """Get models smaller than specified size"""
        return [m for m in self.index.values() if m.file_size_gb <= max_size_gb]
    
    def save_index(self, output_path: Path = None):
        """Save index to JSON file"""
        if output_path is None:
            output_path = Path(__file__).parent.parent.parent.parent / "reports" / "model_index.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "generated_at": datetime.now().isoformat(),
            "total_models": len(self.index),
            "models": {
                name: asdict(meta) 
                for name, meta in self.index.items()
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        print_success(f"Index saved: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GGUF Model Parser")
    parser.add_argument("path", type=Path, nargs="?", help="GGUF file or directory")
    parser.add_argument("--scan", action="store_true", help="Scan all models")
    parser.add_argument("--vision", action="store_true", help="List vision models")
    parser.add_argument("--uncensored", action="store_true", help="List uncensored models")
    
    args = parser.parse_args()
    
    if args.scan or args.vision or args.uncensored:
        indexer = ModelIndexer()
        indexer.scan_all_models()
        
        if args.vision:
            print_section("Vision Models")
            for m in indexer.get_vision_models():
                print(f"  {m.file_name}: {m.parameter_count}, VRAM: {m.estimated_vram_gb}GB")
        
        if args.uncensored:
            print_section("Uncensored Models")
            for m in indexer.get_uncensored_models():
                print(f"  {m.file_name}: {m.parameter_count}")
        
        indexer.save_index()
    
    elif args.path:
        gguf_parser = GGUFParser()
        metadata = gguf_parser.parse_file(args.path)
        print(json.dumps(asdict(metadata), indent=2, default=str))
    
    else:
        print("Usage: python gguf_parser.py <file.gguf> or --scan")
