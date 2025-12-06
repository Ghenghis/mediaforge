"""
LORAFORGE - AI MODEL MANAGER
Automated model discovery, benchmarking, and switching
Supports both Ollama and LM Studio with proper load/unload

CAPABILITIES:
- Discover all models in Ollama and LM Studio
- Load/unload models properly (only one at a time for fair testing)
- Benchmark speed (tokens/second) and quality
- Track performance over time
- Auto-select best model for each task
- Learn from results to improve selection

CRITICAL: Always unload models after testing to save memory!
"""

import os
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import sqlite3
import re

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning, print_progress


# ============================================
# CONFIGURATION
# ============================================

class ModelProvider(Enum):
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"


@dataclass
class ModelInfo:
    """Information about a model"""
    name: str
    provider: str
    size_gb: float = 0
    parameter_count: str = ""  # e.g., "7B", "3B", "500M"
    family: str = ""           # e.g., "llama", "qwen", "gemma"
    quantization: str = ""     # e.g., "Q4_K_M", "Q8_0"
    is_vision: bool = False
    is_uncensored: bool = False
    path: str = ""
    last_tested: str = None


@dataclass
class BenchmarkResult:
    """Result of a model benchmark"""
    model_name: str
    provider: str
    task_type: str              # caption, chat, vision, code
    tokens_per_second: float
    time_to_first_token: float
    total_time: float
    output_quality: float       # 1-10 rating
    memory_used_gb: float
    success: bool
    error: str = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


# ============================================
# DATABASE SCHEMA
# ============================================

MODEL_SCHEMA = """
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    provider TEXT NOT NULL,
    size_gb REAL,
    parameter_count TEXT,
    family TEXT,
    quantization TEXT,
    is_vision INTEGER DEFAULT 0,
    is_uncensored INTEGER DEFAULT 0,
    path TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_tested TIMESTAMP
);

CREATE TABLE IF NOT EXISTS benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER REFERENCES models(id),
    task_type TEXT NOT NULL,
    tokens_per_second REAL,
    time_to_first_token REAL,
    total_time REAL,
    output_quality REAL,
    memory_used_gb REAL,
    success INTEGER,
    error TEXT,
    tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    model_id INTEGER REFERENCES models(id),
    overall_score REAL,
    speed_score REAL,
    quality_score REAL,
    reliability REAL,
    test_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_type, model_id)
);

CREATE TABLE IF NOT EXISTS active_model (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    model_name TEXT,
    provider TEXT,
    loaded_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_benchmarks_model ON benchmarks(model_id);
CREATE INDEX IF NOT EXISTS idx_benchmarks_task ON benchmarks(task_type);
CREATE INDEX IF NOT EXISTS idx_rankings_task ON model_rankings(task_type);
"""


# ============================================
# MODEL MANAGER
# ============================================

class ModelManager:
    """
    Manages AI models across Ollama and LM Studio.
    
    Features:
    - Auto-discover models
    - Load/unload properly (only one at a time!)
    - Benchmark speed and quality
    - Track performance in database
    - Auto-select best model for task
    """
    
    # LM Studio paths
    LMSTUDIO_MODELS_PATH = Path(os.environ.get(
        "LMSTUDIO_MODELS_PATH",
        "C:/Users/Admin/.lmstudio/models"
    ))
    
    # API endpoints
    OLLAMA_API = "http://localhost:11434"
    LMSTUDIO_API = "http://localhost:1234/v1"
    
    # Test prompts for different tasks
    TEST_PROMPTS = {
        "caption": "Describe this image in detail for AI training. Include appearance, pose, setting, and style.",
        "chat": "You are a helpful assistant. Answer concisely: What are the key benefits of local AI models?",
        "vision": "Analyze this image and describe what you see in detail.",
        "code": "Write a Python function that calculates the fibonacci sequence up to n terms.",
        "creative": "Write a short creative story about an AI that discovers art."
    }
    
    def __init__(self, db_path: Path = None):
        """Initialize model manager"""
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "loraforge.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        self.current_model = None
        self.current_provider = None
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database schema"""
        conn = self._get_conn()
        conn.executescript(MODEL_SCHEMA)
        conn.commit()
        conn.close()
    
    # ========================================
    # MODEL DISCOVERY
    # ========================================
    
    def discover_ollama_models(self) -> List[ModelInfo]:
        """Discover all models in Ollama"""
        models = []
        
        try:
            response = requests.get(f"{self.OLLAMA_API}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                for model in data.get("models", []):
                    name = model.get("name", "")
                    size_bytes = model.get("size", 0)
                    
                    # Parse model info from name
                    param_count = self._parse_param_count(name)
                    family = self._parse_family(name)
                    quant = self._parse_quantization(name)
                    
                    info = ModelInfo(
                        name=name,
                        provider=ModelProvider.OLLAMA.value,
                        size_gb=size_bytes / (1024**3),
                        parameter_count=param_count,
                        family=family,
                        quantization=quant,
                        is_vision="vision" in name.lower() or "llava" in name.lower(),
                        is_uncensored="uncensored" in name.lower() or "abliterated" in name.lower()
                    )
                    models.append(info)
                    
        except Exception as e:
            print_warning(f"Ollama not available: {e}")
        
        return models
    
    def discover_lmstudio_models(self) -> List[ModelInfo]:
        """Discover all models in LM Studio"""
        models = []
        
        if not self.LMSTUDIO_MODELS_PATH.exists():
            print_warning(f"LM Studio models path not found: {self.LMSTUDIO_MODELS_PATH}")
            return models
        
        # Find all .gguf files
        for gguf_file in self.LMSTUDIO_MODELS_PATH.rglob("*.gguf"):
            name = gguf_file.stem
            size_bytes = gguf_file.stat().st_size
            
            # Parse model info
            param_count = self._parse_param_count(name)
            family = self._parse_family(name)
            quant = self._parse_quantization(name)
            
            info = ModelInfo(
                name=name,
                provider=ModelProvider.LMSTUDIO.value,
                size_gb=size_bytes / (1024**3),
                parameter_count=param_count,
                family=family,
                quantization=quant,
                is_vision="vision" in name.lower() or "llava" in name.lower(),
                is_uncensored="uncensored" in name.lower() or "abliterated" in name.lower(),
                path=str(gguf_file)
            )
            models.append(info)
        
        return models
    
    def discover_all_models(self) -> Dict[str, List[ModelInfo]]:
        """Discover all models from all providers"""
        print_section("Discovering Models")
        
        ollama_models = self.discover_ollama_models()
        lmstudio_models = self.discover_lmstudio_models()
        
        print_info(f"Ollama: {len(ollama_models)} models")
        print_info(f"LM Studio: {len(lmstudio_models)} models")
        
        # Save to database
        conn = self._get_conn()
        
        for model in ollama_models + lmstudio_models:
            conn.execute("""
                INSERT OR REPLACE INTO models 
                (name, provider, size_gb, parameter_count, family, quantization,
                 is_vision, is_uncensored, path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model.name, model.provider, model.size_gb, model.parameter_count,
                model.family, model.quantization, int(model.is_vision),
                int(model.is_uncensored), model.path
            ))
        
        conn.commit()
        conn.close()
        
        total = len(ollama_models) + len(lmstudio_models)
        print_success(f"Discovered {total} total models")
        
        return {
            "ollama": ollama_models,
            "lmstudio": lmstudio_models
        }
    
    def _parse_param_count(self, name: str) -> str:
        """Extract parameter count from model name"""
        patterns = [
            r'(\d+\.?\d*)[Bb]',  # 7B, 3.5B
            r'(\d+)[Mm]',        # 500M
            r'-(\d+b)-',         # -7b-
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                num = match.group(1)
                if 'b' in name[match.start():match.end()].lower():
                    return f"{num}B"
                else:
                    return f"{num}M"
        
        return "unknown"
    
    def _parse_family(self, name: str) -> str:
        """Extract model family from name"""
        families = [
            "llama", "qwen", "gemma", "phi", "mistral", "deepseek",
            "yi", "falcon", "vicuna", "wizard", "openchat", "neural",
            "dolphin", "orca", "codellama", "starcoder"
        ]
        
        name_lower = name.lower()
        for family in families:
            if family in name_lower:
                return family
        
        return "unknown"
    
    def _parse_quantization(self, name: str) -> str:
        """Extract quantization from name"""
        patterns = [
            r'[Qq](\d+)_[Kk]_[MmSs]',  # Q4_K_M, Q5_K_S
            r'[Qq](\d+)_0',              # Q8_0
            r'[Qq](\d+)',                # Q4, Q8
            r'[Ff]16',                   # F16
            r'[Ff]32',                   # F32
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                return match.group(0)
        
        return "unknown"
    
    # ========================================
    # MODEL LOADING/UNLOADING (CRITICAL!)
    # ========================================
    
    def unload_all_ollama_models(self):
        """Unload ALL models from Ollama to free memory"""
        print_info("Unloading all Ollama models...")
        
        try:
            # Get running models
            response = requests.get(f"{self.OLLAMA_API}/api/ps", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                for model in data.get("models", []):
                    name = model.get("name", "")
                    if name:
                        # Unload by setting keep_alive to 0
                        requests.post(
                            f"{self.OLLAMA_API}/api/generate",
                            json={"model": name, "keep_alive": 0},
                            timeout=30
                        )
                        print_info(f"  Unloaded: {name}")
            
            print_success("All Ollama models unloaded")
            
        except Exception as e:
            print_warning(f"Could not unload Ollama models: {e}")
    
    def unload_lmstudio_model(self):
        """Request LM Studio to unload current model"""
        print_info("Requesting LM Studio model unload...")
        
        # LM Studio doesn't have a direct unload API, but we can
        # track what we loaded and note when to unload
        # The user needs to manually unload in LM Studio UI
        # or we can use the API to load a tiny model to replace
        
        print_warning("LM Studio: Please unload model manually or via UI")
        return True
    
    def load_ollama_model(self, model_name: str) -> bool:
        """Load a specific Ollama model (unloads others first!)"""
        print_info(f"Loading Ollama model: {model_name}")
        
        # CRITICAL: Unload all other models first!
        self.unload_all_ollama_models()
        
        try:
            # Warm up the model by making a simple request
            response = requests.post(
                f"{self.OLLAMA_API}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "Hi",
                    "stream": False,
                    "options": {"num_predict": 1}
                },
                timeout=120
            )
            
            if response.status_code == 200:
                self.current_model = model_name
                self.current_provider = ModelProvider.OLLAMA.value
                
                # Record in database
                conn = self._get_conn()
                conn.execute("""
                    INSERT OR REPLACE INTO active_model (id, model_name, provider, loaded_at)
                    VALUES (1, ?, ?, ?)
                """, (model_name, ModelProvider.OLLAMA.value, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                
                print_success(f"Loaded: {model_name}")
                return True
            else:
                print_error(f"Failed to load: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Error loading model: {e}")
            return False
    
    def load_lmstudio_model(self, model_name: str) -> bool:
        """Check if LM Studio has a model loaded"""
        print_info(f"Using LM Studio model: {model_name}")
        
        try:
            # Check if LM Studio is responding
            response = requests.get(f"{self.LMSTUDIO_API}/models", timeout=5)
            
            if response.status_code == 200:
                self.current_model = model_name
                self.current_provider = ModelProvider.LMSTUDIO.value
                
                conn = self._get_conn()
                conn.execute("""
                    INSERT OR REPLACE INTO active_model (id, model_name, provider, loaded_at)
                    VALUES (1, ?, ?, ?)
                """, (model_name, ModelProvider.LMSTUDIO.value, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                
                print_success(f"LM Studio ready: {model_name}")
                return True
            
        except Exception as e:
            print_warning(f"LM Studio not available: {e}")
        
        return False
    
    # ========================================
    # BENCHMARKING
    # ========================================
    
    def benchmark_model(
        self,
        model_name: str,
        provider: str,
        task_type: str = "chat"
    ) -> Optional[BenchmarkResult]:
        """
        Benchmark a single model on a task.
        
        IMPORTANT: Loads model first, measures performance, then unloads!
        """
        print_section(f"Benchmarking: {model_name}")
        print_info(f"Provider: {provider}, Task: {task_type}")
        
        # Load the model (unloads others first!)
        if provider == ModelProvider.OLLAMA.value:
            if not self.load_ollama_model(model_name):
                return BenchmarkResult(
                    model_name=model_name,
                    provider=provider,
                    task_type=task_type,
                    tokens_per_second=0,
                    time_to_first_token=0,
                    total_time=0,
                    output_quality=0,
                    memory_used_gb=0,
                    success=False,
                    error="Failed to load model"
                )
        
        # Get test prompt
        prompt = self.TEST_PROMPTS.get(task_type, self.TEST_PROMPTS["chat"])
        
        # Run benchmark
        try:
            start_time = time.time()
            first_token_time = None
            total_tokens = 0
            response_text = ""
            
            if provider == ModelProvider.OLLAMA.value:
                # Stream response to measure time to first token
                response = requests.post(
                    f"{self.OLLAMA_API}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": True,
                        "options": {"num_predict": 100}
                    },
                    stream=True,
                    timeout=120
                )
                
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        
                        if first_token_time is None:
                            first_token_time = time.time() - start_time
                        
                        response_text += data.get("response", "")
                        
                        if data.get("eval_count"):
                            total_tokens = data["eval_count"]
                        
                        if data.get("done"):
                            break
                
            elif provider == ModelProvider.LMSTUDIO.value:
                response = requests.post(
                    f"{self.LMSTUDIO_API}/chat/completions",
                    json={
                        "model": model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 100,
                        "stream": False
                    },
                    timeout=120
                )
                
                first_token_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data["choices"][0]["message"]["content"]
                    total_tokens = data.get("usage", {}).get("completion_tokens", len(response_text.split()))
            
            total_time = time.time() - start_time
            tokens_per_second = total_tokens / total_time if total_time > 0 else 0
            
            # Estimate quality (simple heuristic)
            quality = self._estimate_quality(response_text, task_type)
            
            result = BenchmarkResult(
                model_name=model_name,
                provider=provider,
                task_type=task_type,
                tokens_per_second=tokens_per_second,
                time_to_first_token=first_token_time or 0,
                total_time=total_time,
                output_quality=quality,
                memory_used_gb=0,  # Would need system monitoring
                success=True
            )
            
            print_success(f"Speed: {tokens_per_second:.1f} tok/s")
            print_info(f"Quality: {quality:.1f}/10")
            print_info(f"Time: {total_time:.2f}s")
            
            # Save to database
            self._save_benchmark(result)
            
            return result
            
        except Exception as e:
            print_error(f"Benchmark failed: {e}")
            return BenchmarkResult(
                model_name=model_name,
                provider=provider,
                task_type=task_type,
                tokens_per_second=0,
                time_to_first_token=0,
                total_time=0,
                output_quality=0,
                memory_used_gb=0,
                success=False,
                error=str(e)
            )
        
        finally:
            # ALWAYS unload after testing!
            if provider == ModelProvider.OLLAMA.value:
                self.unload_all_ollama_models()
    
    def _estimate_quality(self, response: str, task_type: str) -> float:
        """Estimate response quality (1-10)"""
        if not response:
            return 0
        
        score = 5.0  # Base score
        
        # Length check
        word_count = len(response.split())
        if word_count < 10:
            score -= 2
        elif word_count > 50:
            score += 1
        
        # Coherence check (simple: no repeated phrases)
        words = response.lower().split()
        unique_ratio = len(set(words)) / len(words) if words else 0
        if unique_ratio < 0.5:
            score -= 2
        elif unique_ratio > 0.8:
            score += 1
        
        # Task-specific checks
        if task_type == "code":
            if "def " in response or "function" in response:
                score += 1
            if "```" in response:
                score += 0.5
        
        if task_type == "caption":
            descriptive_words = ["wearing", "background", "style", "pose", "looking"]
            matches = sum(1 for w in descriptive_words if w in response.lower())
            score += min(matches * 0.5, 2)
        
        return max(1, min(10, score))
    
    def _save_benchmark(self, result: BenchmarkResult):
        """Save benchmark result to database"""
        conn = self._get_conn()
        
        # Get model ID
        row = conn.execute(
            "SELECT id FROM models WHERE name = ?", (result.model_name,)
        ).fetchone()
        
        if row:
            model_id = row[0]
            
            conn.execute("""
                INSERT INTO benchmarks 
                (model_id, task_type, tokens_per_second, time_to_first_token,
                 total_time, output_quality, memory_used_gb, success, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model_id, result.task_type, result.tokens_per_second,
                result.time_to_first_token, result.total_time,
                result.output_quality, result.memory_used_gb,
                int(result.success), result.error
            ))
            
            # Update rankings
            self._update_rankings(model_id, result.task_type)
            
            conn.commit()
        
        conn.close()
    
    def _update_rankings(self, model_id: int, task_type: str):
        """Update model rankings based on benchmark results"""
        conn = self._get_conn()
        
        # Get all benchmarks for this model/task
        rows = conn.execute("""
            SELECT tokens_per_second, output_quality, success
            FROM benchmarks
            WHERE model_id = ? AND task_type = ? AND success = 1
            ORDER BY tested_at DESC
            LIMIT 10
        """, (model_id, task_type)).fetchall()
        
        if not rows:
            conn.close()
            return
        
        # Calculate scores
        speeds = [r[0] for r in rows]
        qualities = [r[1] for r in rows]
        successes = [r[2] for r in rows]
        
        avg_speed = sum(speeds) / len(speeds)
        avg_quality = sum(qualities) / len(qualities)
        reliability = sum(successes) / len(successes)
        
        # Normalize speed score (0-10, assuming 100 tok/s is excellent)
        speed_score = min(10, avg_speed / 10)
        
        # Overall score (weighted)
        overall = (speed_score * 0.4) + (avg_quality * 0.4) + (reliability * 10 * 0.2)
        
        conn.execute("""
            INSERT OR REPLACE INTO model_rankings
            (task_type, model_id, overall_score, speed_score, quality_score, reliability, test_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (task_type, model_id, overall, speed_score, avg_quality, reliability, len(rows)))
        
        conn.commit()
        conn.close()
    
    # ========================================
    # MODEL SELECTION
    # ========================================
    
    def get_best_model(self, task_type: str, prefer_speed: bool = False) -> Optional[Dict]:
        """Get the best model for a specific task"""
        conn = self._get_conn()
        
        if prefer_speed:
            order = "speed_score DESC, overall_score DESC"
        else:
            order = "overall_score DESC"
        
        row = conn.execute(f"""
            SELECT m.name, m.provider, r.overall_score, r.speed_score, 
                   r.quality_score, r.reliability, r.test_count
            FROM model_rankings r
            JOIN models m ON m.id = r.model_id
            WHERE r.task_type = ? AND r.test_count >= 3
            ORDER BY {order}
            LIMIT 1
        """, (task_type,)).fetchone()
        
        conn.close()
        
        if row:
            return {
                "name": row[0],
                "provider": row[1],
                "overall_score": row[2],
                "speed_score": row[3],
                "quality_score": row[4],
                "reliability": row[5],
                "test_count": row[6]
            }
        
        return None
    
    def get_rankings(self, task_type: str = None, limit: int = 10) -> List[Dict]:
        """Get model rankings"""
        conn = self._get_conn()
        
        if task_type:
            rows = conn.execute("""
                SELECT m.name, m.provider, m.parameter_count, r.task_type,
                       r.overall_score, r.speed_score, r.quality_score, 
                       r.reliability, r.test_count
                FROM model_rankings r
                JOIN models m ON m.id = r.model_id
                WHERE r.task_type = ?
                ORDER BY r.overall_score DESC
                LIMIT ?
            """, (task_type, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT m.name, m.provider, m.parameter_count, r.task_type,
                       r.overall_score, r.speed_score, r.quality_score,
                       r.reliability, r.test_count
                FROM model_rankings r
                JOIN models m ON m.id = r.model_id
                ORDER BY r.overall_score DESC
                LIMIT ?
            """, (limit,)).fetchall()
        
        conn.close()
        
        return [
            {
                "name": r[0],
                "provider": r[1],
                "params": r[2],
                "task": r[3],
                "overall": r[4],
                "speed": r[5],
                "quality": r[6],
                "reliability": r[7],
                "tests": r[8]
            }
            for r in rows
        ]
    
    def get_fast_models(self, min_speed: float = 50) -> List[Dict]:
        """Get models that are fast (for quick tasks)"""
        conn = self._get_conn()
        
        rows = conn.execute("""
            SELECT DISTINCT m.name, m.provider, m.parameter_count,
                   AVG(b.tokens_per_second) as avg_speed
            FROM models m
            JOIN benchmarks b ON b.model_id = m.id
            WHERE b.success = 1
            GROUP BY m.id
            HAVING avg_speed >= ?
            ORDER BY avg_speed DESC
        """, (min_speed,)).fetchall()
        
        conn.close()
        
        return [
            {"name": r[0], "provider": r[1], "params": r[2], "speed": r[3]}
            for r in rows
        ]
    
    def get_uncensored_models(self) -> List[Dict]:
        """Get all uncensored models"""
        conn = self._get_conn()
        
        rows = conn.execute("""
            SELECT name, provider, parameter_count, is_vision
            FROM models
            WHERE is_uncensored = 1
        """).fetchall()
        
        conn.close()
        
        return [
            {"name": r[0], "provider": r[1], "params": r[2], "vision": bool(r[3])}
            for r in rows
        ]


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

_model_manager = None

def get_model_manager() -> ModelManager:
    """Get singleton model manager"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Manager")
    parser.add_argument("--discover", action="store_true", help="Discover all models")
    parser.add_argument("--benchmark", type=str, help="Benchmark a specific model")
    parser.add_argument("--provider", type=str, default="ollama", help="Provider (ollama/lmstudio)")
    parser.add_argument("--task", type=str, default="chat", help="Task type")
    parser.add_argument("--rankings", action="store_true", help="Show rankings")
    parser.add_argument("--best", type=str, help="Get best model for task")
    parser.add_argument("--fast", action="store_true", help="Show fast models")
    parser.add_argument("--uncensored", action="store_true", help="Show uncensored models")
    
    args = parser.parse_args()
    
    manager = ModelManager()
    
    if args.discover:
        manager.discover_all_models()
    elif args.benchmark:
        manager.benchmark_model(args.benchmark, args.provider, args.task)
    elif args.rankings:
        rankings = manager.get_rankings(limit=20)
        print_section("Model Rankings")
        for r in rankings:
            print(f"{r['name'][:30]:<30} {r['provider']:<10} {r['params']:<6} "
                  f"Score:{r['overall']:.1f} Speed:{r['speed']:.1f} Quality:{r['quality']:.1f}")
    elif args.best:
        best = manager.get_best_model(args.best)
        if best:
            print_success(f"Best for {args.best}: {best['name']} ({best['provider']})")
            print_info(f"Score: {best['overall_score']:.1f}")
        else:
            print_warning(f"No tested models for {args.best}")
    elif args.fast:
        fast = manager.get_fast_models()
        print_section("Fast Models")
        for m in fast:
            print(f"{m['name'][:40]:<40} {m['speed']:.0f} tok/s")
    elif args.uncensored:
        uncensored = manager.get_uncensored_models()
        print_section("Uncensored Models")
        for m in uncensored:
            vision = "👁" if m['vision'] else ""
            print(f"{m['name'][:40]:<40} {m['provider']:<10} {m['params']:<6} {vision}")
    else:
        print("Use --help for options")
