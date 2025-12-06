"""
LORAFORGE - MODEL COMPARATOR
Visual comparison of LoRA model versions with charts
Enhanced from anime-lora-pipeline with multi-metric support

HOW IT WORKS:
1. Load evaluation JSONs from multiple model versions
2. Extract metrics (CLIP score, consistency, quality)
3. Generate comparison charts using matplotlib
4. Identify best performers per metric
5. Create summary report with recommendations

METRICS COMPARED:
- CLIP Score: Prompt adherence (higher = better)
- Consistency: Character stability (higher = better)
- Quality: Image quality metrics (higher = better)
- Failure Rate: Error frequency (lower = better)
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning

# Optional dependencies
pd = None
plt = None
np = None

def ensure_visualization():
    """Lazy load visualization dependencies"""
    global pd, plt, np
    
    if pd is None:
        try:
            import pandas as _pd
            pd = _pd
        except ImportError:
            print_warning("pandas not installed")
            return False
    
    if plt is None:
        try:
            import matplotlib.pyplot as _plt
            plt = _plt
        except ImportError:
            print_warning("matplotlib not installed")
            return False
    
    if np is None:
        try:
            import numpy as _np
            np = _np
        except ImportError:
            return False
    
    return True


@dataclass
class ModelMetrics:
    """Metrics for a single model version"""
    name: str
    clip_score_mean: float
    clip_score_std: float
    consistency_mean: float
    consistency_std: float
    num_images: int
    overall_score: float
    grade: str


class LoRAComparator:
    """
    Compare multiple LoRA model versions.
    
    Supports:
    - Loading from evaluation JSON files
    - Chart generation (bar, radar, line)
    - Best performer identification
    - Export to various formats
    """
    
    def __init__(self):
        self.models: List[ModelMetrics] = []
        self.raw_data: List[Dict] = []
    
    def load_evaluation(self, json_path: Path) -> Optional[ModelMetrics]:
        """
        Load evaluation results from JSON file.
        
        Args:
            json_path: Path to evaluation JSON
            
        Returns:
            ModelMetrics or None if failed
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            self.raw_data.append(data)
            
            # Extract metrics
            overall = data.get('overall_metrics', data.get('metrics', {}))
            
            # Get model name from path or data
            name = data.get('model_name') or json_path.parent.name
            
            clip_data = overall.get('clip_score', {})
            consistency_data = overall.get('character_consistency', overall.get('consistency', {}))
            
            metrics = ModelMetrics(
                name=name,
                clip_score_mean=clip_data.get('mean', 0),
                clip_score_std=clip_data.get('std', 0),
                consistency_mean=consistency_data.get('mean', 0),
                consistency_std=consistency_data.get('std', 0),
                num_images=data.get('total_images', data.get('num_images', 0)),
                overall_score=data.get('overall_score', 0),
                grade=data.get('grade', 'N/A')
            )
            
            self.models.append(metrics)
            return metrics
            
        except Exception as e:
            print_error(f"Failed to load {json_path}: {e}")
            return None
    
    def load_directory(self, eval_dir: Path, pattern: str = "**/evaluation*.json"):
        """
        Load all evaluation files from directory.
        
        Args:
            eval_dir: Directory to search
            pattern: Glob pattern for evaluation files
        """
        eval_dir = Path(eval_dir)
        files = list(eval_dir.glob(pattern))
        
        # Also try quality_evaluation.json
        files.extend(eval_dir.glob("**/quality_evaluation.json"))
        
        print_info(f"Found {len(files)} evaluation files")
        
        for f in files:
            self.load_evaluation(f)
        
        print_success(f"Loaded {len(self.models)} models")
    
    def compare(self) -> Dict:
        """
        Generate comparison report.
        
        Returns:
            Comparison dictionary
        """
        if not self.models:
            return {'error': 'No models loaded'}
        
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'num_models': len(self.models),
            'models': [],
            'best_performers': {},
            'recommendations': []
        }
        
        # Collect all metrics
        for model in self.models:
            comparison['models'].append({
                'name': model.name,
                'clip_score': model.clip_score_mean,
                'consistency': model.consistency_mean,
                'images': model.num_images,
                'overall_score': model.overall_score,
                'grade': model.grade
            })
        
        # Find best performers
        if len(self.models) > 0:
            best_clip = max(self.models, key=lambda m: m.clip_score_mean)
            best_consistency = max(self.models, key=lambda m: m.consistency_mean)
            best_overall = max(self.models, key=lambda m: m.overall_score)
            
            comparison['best_performers'] = {
                'clip_score': best_clip.name,
                'consistency': best_consistency.name,
                'overall': best_overall.name
            }
            
            # Recommendations
            if best_clip.name == best_consistency.name == best_overall.name:
                comparison['recommendations'].append(
                    f"✓ {best_overall.name} is the clear winner across all metrics"
                )
            else:
                comparison['recommendations'].append(
                    f"CLIP: Use {best_clip.name} for best prompt adherence"
                )
                comparison['recommendations'].append(
                    f"Consistency: Use {best_consistency.name} for most stable character"
                )
                comparison['recommendations'].append(
                    f"Overall: Use {best_overall.name} for balanced performance"
                )
        
        return comparison
    
    def print_comparison(self, comparison: Dict = None):
        """Print comparison table to console"""
        if comparison is None:
            comparison = self.compare()
        
        print_section("MODEL COMPARISON")
        
        if 'error' in comparison:
            print_error(comparison['error'])
            return
        
        # Header
        print(f"{'Model':<20} {'CLIP':<10} {'Consist.':<10} {'Score':<10} {'Grade':<8} {'Images':<8}")
        print("-" * 70)
        
        # Sort by overall score
        sorted_models = sorted(
            comparison['models'],
            key=lambda m: m.get('overall_score', 0),
            reverse=True
        )
        
        for i, model in enumerate(sorted_models):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
            print(f"{medal} {model['name']:<18} {model['clip_score']:<10.2f} {model['consistency']:<10.1f} "
                  f"{model['overall_score']:<10.2f} {model['grade']:<8} {model['images']:<8}")
        
        print()
        
        # Best performers
        if comparison.get('best_performers'):
            print_info("Best Performers:")
            for metric, winner in comparison['best_performers'].items():
                print(f"  {metric}: {winner}")
        
        # Recommendations
        if comparison.get('recommendations'):
            print()
            print_info("Recommendations:")
            for rec in comparison['recommendations']:
                print(f"  {rec}")
    
    def create_bar_chart(self, output_path: Path, metric: str = "clip_score"):
        """
        Create bar chart comparing models.
        
        Args:
            output_path: Path to save chart
            metric: Metric to plot (clip_score, consistency, overall_score)
        """
        if not ensure_visualization():
            return
        
        if not self.models:
            print_error("No models to plot")
            return
        
        # Prepare data
        names = [m.name for m in self.models]
        
        if metric == "clip_score":
            values = [m.clip_score_mean for m in self.models]
            errors = [m.clip_score_std for m in self.models]
            ylabel = "CLIP Score"
            title = "Prompt Adherence Comparison"
            threshold_good = 30
            threshold_ok = 25
        elif metric == "consistency":
            values = [m.consistency_mean for m in self.models]
            errors = [m.consistency_std for m in self.models]
            ylabel = "Consistency (%)"
            title = "Character Consistency Comparison"
            threshold_good = 85
            threshold_ok = 75
        else:  # overall_score
            values = [m.overall_score for m in self.models]
            errors = [0] * len(self.models)
            ylabel = "Overall Score"
            title = "Overall Performance Comparison"
            threshold_good = 8
            threshold_ok = 6
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Bar colors based on value
        colors = []
        for v in values:
            if v >= threshold_good:
                colors.append('#2ecc71')  # Green
            elif v >= threshold_ok:
                colors.append('#f1c40f')  # Yellow
            else:
                colors.append('#e74c3c')  # Red
        
        # Plot
        bars = ax.bar(names, values, yerr=errors, capsize=5, color=colors, alpha=0.8)
        
        # Thresholds
        ax.axhline(y=threshold_good, color='green', linestyle='--', alpha=0.5, label=f'Excellent (≥{threshold_good})')
        ax.axhline(y=threshold_ok, color='orange', linestyle='--', alpha=0.5, label=f'Good (≥{threshold_ok})')
        
        # Labels
        ax.set_xlabel("Model Version", fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        # Rotate x labels if needed
        if len(names) > 4:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print_success(f"Chart saved: {output_path}")
    
    def create_comparison_charts(self, output_dir: Path):
        """
        Create all comparison charts.
        
        Args:
            output_dir: Directory to save charts
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print_section("Creating Comparison Charts")
        
        # CLIP Score chart
        self.create_bar_chart(output_dir / "clip_score_comparison.png", "clip_score")
        
        # Consistency chart
        self.create_bar_chart(output_dir / "consistency_comparison.png", "consistency")
        
        # Overall score chart
        self.create_bar_chart(output_dir / "overall_comparison.png", "overall_score")
        
        # Multi-metric comparison
        self._create_multi_chart(output_dir / "multi_metric_comparison.png")
    
    def _create_multi_chart(self, output_path: Path):
        """Create side-by-side multi-metric chart"""
        if not ensure_visualization():
            return
        
        if not self.models:
            return
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        names = [m.name for m in self.models]
        
        # CLIP Score
        values = [m.clip_score_mean for m in self.models]
        axes[0].bar(names, values, color='steelblue', alpha=0.8)
        axes[0].set_title("CLIP Score", fontweight='bold')
        axes[0].set_ylabel("Score")
        axes[0].tick_params(axis='x', rotation=45)
        
        # Consistency
        values = [m.consistency_mean for m in self.models]
        axes[1].bar(names, values, color='coral', alpha=0.8)
        axes[1].set_title("Consistency", fontweight='bold')
        axes[1].set_ylabel("Percentage")
        axes[1].tick_params(axis='x', rotation=45)
        
        # Overall
        values = [m.overall_score for m in self.models]
        axes[2].bar(names, values, color='mediumseagreen', alpha=0.8)
        axes[2].set_title("Overall Score", fontweight='bold')
        axes[2].set_ylabel("Score")
        axes[2].tick_params(axis='x', rotation=45)
        
        plt.suptitle("LoRA Model Comparison", fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print_success(f"Multi-chart saved: {output_path}")
    
    def save_report(self, output_path: Path):
        """Save comparison report to JSON"""
        comparison = self.compare()
        
        with open(output_path, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        print_success(f"Report saved: {output_path}")


def compare_models(eval_dirs: List[Path], output_dir: Path) -> Dict:
    """
    Convenience function for model comparison.
    
    Args:
        eval_dirs: List of directories with evaluation files
        output_dir: Output directory for reports/charts
        
    Returns:
        Comparison dictionary
    """
    comparator = LoRAComparator()
    
    for eval_dir in eval_dirs:
        comparator.load_directory(eval_dir)
    
    comparison = comparator.compare()
    comparator.print_comparison(comparison)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    comparator.save_report(output_dir / "comparison_report.json")
    comparator.create_comparison_charts(output_dir)
    
    return comparison


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare LoRA model versions")
    parser.add_argument("eval_dirs", type=Path, nargs="+", help="Evaluation directories")
    parser.add_argument("--output", type=Path, default=Path("reports"), help="Output directory")
    
    args = parser.parse_args()
    
    compare_models(args.eval_dirs, args.output)
