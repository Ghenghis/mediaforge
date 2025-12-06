"""
LORAFORGE - BENCHMARK COMPARISON
Compare our pipeline against competitor projects
Track improvements and identify areas for optimization
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import print_section, print_success, print_info, print_warning


@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    name: str
    category: str
    value: float
    unit: str
    better: str  # "higher" or "lower"


@dataclass
class ProjectComparison:
    """Comparison between projects"""
    project_name: str
    benchmarks: List[BenchmarkResult]
    features: Dict[str, bool]
    timestamp: str


class CompetitorBenchmark:
    """
    Benchmark our project against competitors.
    
    Categories:
    - Speed: Processing time for various operations
    - Quality: Output quality metrics
    - Features: Feature completeness
    - Automation: Level of automation
    """
    
    # Feature comparison matrix (UPDATED after comprehensive audit)
    FEATURE_MATRIX = {
        "LoRAForge": {
            "video_to_lora_pipeline": True,
            "uncensored_vision_ai": True,
            "multi_version_training": True,
            "model_evaluation_metrics": True,
            "clip_scoring": True,
            "image_deduplication": True,
            "quality_filtering": True,
            "real_time_dashboard": True,
            "anti_failure_training": True,
            "config_driven": True,
            "stage_pipeline": True,
            "local_only": True,
            "nsfw_support": True,
            "free_no_api_costs": True,
            # NEW FEATURES ADDED
            "scene_detection": True,
            "auto_captioning_wd14": True,
            "auto_captioning_lmstudio": True,
            "character_clustering": True,
            "model_comparison_charts": True,
            "pca_visualization": True,
        },
        "anime-lora-pipeline": {
            "video_to_lora_pipeline": True,
            "uncensored_vision_ai": False,
            "multi_version_training": False,
            "model_evaluation_metrics": True,
            "clip_scoring": True,
            "image_deduplication": True,
            "quality_filtering": True,
            "real_time_dashboard": False,
            "anti_failure_training": False,
            "config_driven": True,
            "stage_pipeline": True,
            "local_only": False,
            "nsfw_support": False,
            "free_no_api_costs": True,
            # Features they have
            "scene_detection": True,
            "auto_captioning_wd14": True,
            "auto_captioning_lmstudio": False,
            "character_clustering": True,
            "model_comparison_charts": True,
            "pca_visualization": True,
        },
        "ai-image-dataset-pipeline": {
            "video_to_lora_pipeline": False,
            "uncensored_vision_ai": False,
            "multi_version_training": False,
            "model_evaluation_metrics": False,
            "clip_scoring": False,
            "image_deduplication": False,
            "quality_filtering": True,
            "real_time_dashboard": False,
            "anti_failure_training": False,
            "config_driven": True,
            "stage_pipeline": True,
            "local_only": False,  # Uses OpenAI
            "nsfw_support": False,
            "free_no_api_costs": False,  # Requires OpenAI
        },
        "LoRA-Dataset-Automaker": {
            "video_to_lora_pipeline": False,
            "uncensored_vision_ai": False,
            "multi_version_training": False,
            "model_evaluation_metrics": False,
            "clip_scoring": True,
            "image_deduplication": True,
            "quality_filtering": True,
            "real_time_dashboard": False,
            "anti_failure_training": False,
            "config_driven": False,  # Jupyter notebook
            "stage_pipeline": False,
            "local_only": True,
            "nsfw_support": False,
            "free_no_api_costs": True,
        },
        "kohya-colab": {
            "video_to_lora_pipeline": False,
            "uncensored_vision_ai": False,
            "multi_version_training": False,
            "model_evaluation_metrics": False,
            "clip_scoring": False,
            "image_deduplication": False,
            "quality_filtering": False,
            "real_time_dashboard": False,
            "anti_failure_training": False,
            "config_driven": True,
            "stage_pipeline": False,
            "local_only": False,  # Colab
            "nsfw_support": True,  # Can train NSFW
            "free_no_api_costs": True,
        },
    }
    
    def __init__(self):
        self.results: List[ProjectComparison] = []
        self.our_benchmarks: List[BenchmarkResult] = []
    
    def benchmark_our_pipeline(self, test_images_dir: Path = None) -> List[BenchmarkResult]:
        """
        Run benchmarks on our pipeline.
        """
        benchmarks = []
        
        print_section("Running LoRAForge Benchmarks")
        
        # Benchmark 1: Image hash computation speed
        if test_images_dir and test_images_dir.exists():
            images = list(test_images_dir.glob("*.jpg"))[:50]
            
            if images:
                from core.image_cleaner import ImageCleaner
                cleaner = ImageCleaner()
                
                start = time.time()
                hashes = cleaner.compute_all_hashes(images)
                elapsed = time.time() - start
                
                benchmarks.append(BenchmarkResult(
                    name="hash_computation",
                    category="speed",
                    value=len(images) / elapsed if elapsed > 0 else 0,
                    unit="images/sec",
                    better="higher"
                ))
                print_info(f"Hash speed: {len(images)/elapsed:.1f} images/sec")
        
        # Benchmark 2: Quality check speed
        if test_images_dir and test_images_dir.exists():
            images = list(test_images_dir.glob("*.jpg"))[:50]
            
            if images:
                from core.image_cleaner import ImageCleaner
                cleaner = ImageCleaner()
                
                start = time.time()
                for img in images:
                    cleaner.check_quality(img)
                elapsed = time.time() - start
                
                benchmarks.append(BenchmarkResult(
                    name="quality_check",
                    category="speed",
                    value=len(images) / elapsed if elapsed > 0 else 0,
                    unit="images/sec",
                    better="higher"
                ))
                print_info(f"Quality check: {len(images)/elapsed:.1f} images/sec")
        
        # Feature count
        our_features = self.FEATURE_MATRIX.get("LoRAForge", {})
        feature_count = sum(1 for v in our_features.values() if v)
        
        benchmarks.append(BenchmarkResult(
            name="feature_count",
            category="features",
            value=feature_count,
            unit="features",
            better="higher"
        ))
        
        # Unique features
        unique_count = 0
        for feature, has_it in our_features.items():
            if has_it:
                # Check if any competitor has it
                others_have = any(
                    self.FEATURE_MATRIX.get(proj, {}).get(feature, False)
                    for proj in self.FEATURE_MATRIX
                    if proj != "LoRAForge"
                )
                if not others_have:
                    unique_count += 1
        
        benchmarks.append(BenchmarkResult(
            name="unique_features",
            category="features",
            value=unique_count,
            unit="features",
            better="higher"
        ))
        print_info(f"Unique features: {unique_count}")
        
        self.our_benchmarks = benchmarks
        return benchmarks
    
    def compare_features(self) -> Dict[str, Dict]:
        """
        Compare features across all projects.
        """
        print_section("Feature Comparison")
        
        comparison = {}
        
        for project, features in self.FEATURE_MATRIX.items():
            count = sum(1 for v in features.values() if v)
            comparison[project] = {
                "total_features": count,
                "features": features
            }
        
        # Print comparison table
        all_features = list(self.FEATURE_MATRIX["LoRAForge"].keys())
        
        print(f"\n{'Feature':<30}", end="")
        for project in self.FEATURE_MATRIX:
            print(f"{project[:12]:<14}", end="")
        print()
        print("-" * (30 + 14 * len(self.FEATURE_MATRIX)))
        
        for feature in all_features:
            print(f"{feature:<30}", end="")
            for project in self.FEATURE_MATRIX:
                has = self.FEATURE_MATRIX[project].get(feature, False)
                icon = "✓" if has else "✗"
                print(f"{icon:<14}", end="")
            print()
        
        print("-" * (30 + 14 * len(self.FEATURE_MATRIX)))
        print(f"{'TOTAL':<30}", end="")
        for project in self.FEATURE_MATRIX:
            count = comparison[project]["total_features"]
            print(f"{count:<14}", end="")
        print()
        
        return comparison
    
    def calculate_scores(self) -> Dict[str, float]:
        """
        Calculate overall scores for each project.
        """
        scores = {}
        
        # Weights for categories
        weights = {
            "video_to_lora_pipeline": 2.0,  # Critical feature
            "uncensored_vision_ai": 2.0,    # Unique advantage
            "multi_version_training": 1.5,
            "model_evaluation_metrics": 1.5,
            "clip_scoring": 1.0,
            "image_deduplication": 1.0,
            "quality_filtering": 1.0,
            "real_time_dashboard": 1.5,
            "anti_failure_training": 2.0,   # Unique
            "config_driven": 0.5,
            "stage_pipeline": 1.0,
            "local_only": 1.0,
            "nsfw_support": 1.5,
            "free_no_api_costs": 1.5,
        }
        
        for project, features in self.FEATURE_MATRIX.items():
            score = 0
            for feature, has_it in features.items():
                if has_it:
                    score += weights.get(feature, 1.0)
            scores[project] = score
        
        return scores
    
    def generate_report(self, output_path: Path = None) -> Dict:
        """
        Generate comprehensive comparison report.
        """
        print_section("COMPARISON REPORT")
        
        # Feature comparison
        feature_comparison = self.compare_features()
        
        # Scores
        scores = self.calculate_scores()
        
        print("\n--- PROJECT SCORES ---")
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for i, (project, score) in enumerate(sorted_scores, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            bar = "█" * int(score / 2) + "░" * (10 - int(score / 2))
            print(f"{medal} {project:<25} [{bar}] {score:.1f}")
        
        # Our advantages
        print("\n--- LORAFORGE UNIQUE ADVANTAGES ---")
        our_features = self.FEATURE_MATRIX["LoRAForge"]
        for feature, has_it in our_features.items():
            if has_it:
                others_have = any(
                    self.FEATURE_MATRIX.get(proj, {}).get(feature, False)
                    for proj in self.FEATURE_MATRIX
                    if proj != "LoRAForge"
                )
                if not others_have:
                    print(f"  ★ {feature.replace('_', ' ').title()}")
        
        # Areas to improve
        print("\n--- AREAS FOR IMPROVEMENT ---")
        max_features = max(
            sum(1 for v in f.values() if v)
            for f in self.FEATURE_MATRIX.values()
        )
        our_count = sum(1 for v in our_features.values() if v)
        
        if our_count == max_features:
            print("  ✓ We have the most features!")
        else:
            for feature, has_it in our_features.items():
                if not has_it:
                    print(f"  → Could add: {feature.replace('_', ' ').title()}")
        
        # Generate report data
        report = {
            "timestamp": datetime.now().isoformat(),
            "scores": scores,
            "winner": sorted_scores[0][0],
            "feature_comparison": feature_comparison,
            "our_benchmarks": [asdict(b) for b in self.our_benchmarks] if self.our_benchmarks else [],
            "unique_advantages": [
                f for f, has in our_features.items()
                if has and not any(
                    self.FEATURE_MATRIX.get(p, {}).get(f, False)
                    for p in self.FEATURE_MATRIX if p != "LoRAForge"
                )
            ]
        }
        
        # Save report
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            print_info(f"\nReport saved: {output_path}")
        
        return report


def main():
    """Run comparison benchmark"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark comparison")
    parser.add_argument("--test-images", type=Path, help="Directory with test images")
    parser.add_argument("--output", type=Path, default=Path("reports/benchmark_comparison.json"))
    
    args = parser.parse_args()
    
    benchmark = CompetitorBenchmark()
    
    # Run our benchmarks if test images provided
    if args.test_images:
        benchmark.benchmark_our_pipeline(args.test_images)
    
    # Generate comparison report
    report = benchmark.generate_report(args.output)
    
    print("\n" + "="*60)
    print(f"  WINNER: {report['winner'].upper()}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
