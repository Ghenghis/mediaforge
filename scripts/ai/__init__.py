"""
LORAFORGE - AI MODULE
Model management, benchmarking, ranking, and auto-selection

Components:
- ModelManager: Load/unload models, track performance
- AutoBenchmarker: Automated testing and winner finding
- ModelRankingSystem: Top 10/20 per use case, combinations

Usage:
    from ai import get_model_manager, AutoBenchmarker, ModelRankingSystem
    
    # Get best model for a task
    manager = get_model_manager()
    best = manager.get_best_model("caption")
    
    # Benchmark all models
    benchmarker = AutoBenchmarker()
    winners = benchmarker.find_winners()
    
    # Get top 10 for each use case
    rankings = ModelRankingSystem()
    top_caption = rankings.get_rankings("caption", top_n=10)
"""

from .model_manager import (
    ModelManager,
    ModelProvider,
    ModelInfo,
    BenchmarkResult,
    get_model_manager
)

from .auto_benchmarker import (
    AutoBenchmarker,
    run_full_benchmark
)

from .model_rankings import (
    ModelRankingSystem,
    ModelRanking,
    ModelCombination,
    USE_CASES,
    print_top_models
)

__all__ = [
    # Model Manager
    "ModelManager",
    "ModelProvider", 
    "ModelInfo",
    "BenchmarkResult",
    "get_model_manager",
    
    # Benchmarker
    "AutoBenchmarker",
    "run_full_benchmark",
    
    # Rankings
    "ModelRankingSystem",
    "ModelRanking",
    "ModelCombination",
    "USE_CASES",
    "print_top_models"
]
