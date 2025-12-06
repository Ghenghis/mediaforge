"""
LoRAForge Configuration Loader
Load and validate YAML configuration files
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


def load_config(config_path: str = "config/global_config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config file (relative to project root)
    
    Returns:
        Configuration dictionary
    """
    # Find project root (where config folder is)
    current = Path(__file__).parent
    while current.parent != current:
        if (current / "config").exists():
            break
        current = current.parent
    
    config_file = current / config_path
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config not found: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_path(config: Dict, key: str) -> Path:
    """Get path from config and ensure it exists"""
    path_str = config.get("paths", {}).get(key)
    if not path_str:
        raise KeyError(f"Path not found in config: {key}")
    
    path = Path(path_str)
    return path


def ensure_paths(config: Dict) -> None:
    """Create all configured directories if they don't exist"""
    paths = config.get("paths", {})
    for key, path_str in paths.items():
        if path_str and not path_str.startswith("http"):
            path = Path(path_str)
            if not path.suffix:  # It's a directory, not a file
                path.mkdir(parents=True, exist_ok=True)


@dataclass
class FilterConfig:
    """Filtering configuration"""
    required_gender: str
    excluded_genders: list
    excluded_body_types: list
    min_quality: int
    min_attractiveness: int
    frames_per_video: int
    frame_positions: list


@dataclass
class TrainingVersionConfig:
    """Training version configuration"""
    name: str
    version: str
    description: str
    data_source: str
    lora_rank: int
    learning_rate: float
    steps: int
    batch_size: int


def get_filter_config(config: Dict) -> FilterConfig:
    """Extract filtering configuration"""
    filtering = config.get("filtering", {})
    return FilterConfig(
        required_gender=filtering.get("gender", {}).get("required", "female"),
        excluded_genders=filtering.get("gender", {}).get("exclude", []),
        excluded_body_types=filtering.get("body_type", {}).get("exclude", []),
        min_quality=filtering.get("quality", {}).get("min_score", 4),
        min_attractiveness=filtering.get("attractiveness", {}).get("min_score", 4),
        frames_per_video=filtering.get("frame_extraction", {}).get("frames_per_video", 3),
        frame_positions=filtering.get("frame_extraction", {}).get("positions", [0.25, 0.5, 0.75])
    )


def get_training_version(config: Dict, version_name: str) -> TrainingVersionConfig:
    """Get training configuration for a specific version"""
    versions = config.get("training", {}).get("versions", {})
    version = versions.get(version_name.lower())
    
    if not version:
        raise KeyError(f"Training version not found: {version_name}")
    
    return TrainingVersionConfig(
        name=version.get("name", version_name),
        version=version.get("version", "v1.0"),
        description=version.get("description", ""),
        data_source=version.get("data_source", ""),
        lora_rank=version.get("lora_rank", 32),
        learning_rate=version.get("learning_rate", 0.0001),
        steps=version.get("steps", 1000),
        batch_size=version.get("batch_size", 4)
    )


def get_vision_model_config(config: Dict) -> Dict:
    """Get vision model configuration"""
    return config.get("vision_model", {}).get("primary", {
        "provider": "lmstudio",
        "url": "http://localhost:1234/v1",
        "model": "qwen3-vl-8b-abliterated-caption-it"
    })


# Convenience function for quick access
_config_cache = None

def get_config() -> Dict:
    """Get cached configuration"""
    global _config_cache
    if _config_cache is None:
        _config_cache = load_config()
    return _config_cache
