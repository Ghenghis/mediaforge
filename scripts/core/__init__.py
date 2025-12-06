"""
LORAFORGE - Core Pipeline Modules

Complete feature set surpassing all competitor projects:
- CLIP evaluation & consistency scoring
- Image cleaning & deduplication
- Scene-based frame extraction
- Auto captioning (WD14 + LM Studio)
- Character clustering (HDBSCAN)
- Model version comparison with charts
- Full pipeline orchestration
"""

from .clip_evaluator import CLIPEvaluator, evaluate_images
from .image_cleaner import ImageCleaner, clean_images
from .pipeline_orchestrator import LoRAForgePipeline
from .scene_detector import SceneDetector, extract_with_scene_detection
from .auto_captioner import AutoCaptioner, WD14Tagger, LMStudioCaptioner, caption_images
from .character_clusterer import CharacterClusterer, cluster_characters
from .model_comparator import LoRAComparator, compare_models

__all__ = [
    # Evaluation
    "CLIPEvaluator",
    "evaluate_images",
    
    # Image Processing
    "ImageCleaner",
    "clean_images",
    
    # Video Processing
    "SceneDetector",
    "extract_with_scene_detection",
    
    # Captioning
    "AutoCaptioner",
    "WD14Tagger",
    "LMStudioCaptioner",
    "caption_images",
    
    # Clustering
    "CharacterClusterer",
    "cluster_characters",
    
    # Comparison
    "LoRAComparator",
    "compare_models",
    
    # Pipeline
    "LoRAForgePipeline"
]
