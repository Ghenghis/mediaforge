"""
LORAFORGE - AUTO BENCHMARKER
Automatically test all models and find the best ones
Runs fair tests with proper load/unload cycles

FEATURES:
- Discover new models automatically
- Test each model individually (fair testing!)
- Focus on small/fast models (2B, 3B, 500M, 1B)
- Track winners for each task type
- Generate comprehensive reports
- Watch for new model downloads
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning, print_progress
from ai.model_manager import ModelManager, ModelProvider, get_model_manager


class AutoBenchmarker:
    """
    Automated model benchmarking system.
    
    Finds the BEST models for each task by:
    1. Discovering all available models
    2. Prioritizing small/fast models (500M - 3B)
    3. Testing each model fairly (load, test, unload)
    4. Tracking performance over multiple runs
    5. Generating winner reports
    """
    
    # Task types to benchmark
    TASKS = ["chat", "caption", "code", "creative"]
    
    # Size categories (prioritize smaller models first)
    SIZE_PRIORITY = [
        "500M", "1B", "2B", "3B", "4B", "7B", "8B", "13B", "14B", "70B"
    ]
    
    def __init__(self):
        self.manager = get_model_manager()
        self.running = False
        self.last_discovery = None
        self._watch_thread = None
    
    def discover_new_models(self) -> int:
        """Check for newly downloaded models"""
        models = self.manager.discover_all_models()
        total = len(models.get("ollama", [])) + len(models.get("lmstudio", []))
        self.last_discovery = datetime.now()
        return total
    
    def get_untested_models(self, task_type: str) -> List[Dict]:
        """Get models that haven't been tested for a task"""
        conn = self.manager._get_conn()
        
        rows = conn.execute("""
            SELECT m.name, m.provider, m.parameter_count, m.is_uncensored
            FROM models m
            WHERE m.id NOT IN (
                SELECT DISTINCT model_id FROM benchmarks 
                WHERE task_type = ? AND success = 1
            )
            ORDER BY 
                CASE m.parameter_count
                    WHEN '500M' THEN 1
                    WHEN '1B' THEN 2
                    WHEN '2B' THEN 3
                    WHEN '3B' THEN 4
                    WHEN '4B' THEN 5
                    WHEN '7B' THEN 6
                    WHEN '8B' THEN 7
                    ELSE 10
                END
        """, (task_type,)).fetchall()
        
        conn.close()
        
        return [
            {"name": r[0], "provider": r[1], "params": r[2], "uncensored": bool(r[3])}
            for r in rows
        ]
    
    def get_small_fast_models(self, max_size: str = "3B") -> List[Dict]:
        """Get small models that should be fast"""
        conn = self.manager._get_conn()
        
        # Convert size to number for comparison
        size_order = {"500M": 0.5, "1B": 1, "2B": 2, "3B": 3, "4B": 4}
        max_num = size_order.get(max_size, 3)
        
        rows = conn.execute("""
            SELECT name, provider, parameter_count
            FROM models
            WHERE parameter_count IN ('500M', '1B', '2B', '3B', '4B')
        """).fetchall()
        
        conn.close()
        
        results = []
        for r in rows:
            param = r[2]
            num = size_order.get(param, 999)
            if num <= max_num:
                results.append({"name": r[0], "provider": r[1], "params": param})
        
        return results
    
    def benchmark_all_untested(
        self,
        task_type: str = None,
        max_models: int = 10,
        small_only: bool = True
    ) -> Dict:
        """
        Benchmark all untested models.
        
        Args:
            task_type: Specific task or None for all
            max_models: Maximum models to test per task
            small_only: Only test small models (≤3B)
        """
        print_section("AUTO BENCHMARKER")
        
        # Discover models first
        print_info("Checking for new models...")
        self.discover_new_models()
        
        tasks = [task_type] if task_type else self.TASKS
        results = {"tested": 0, "success": 0, "failed": 0, "by_task": {}}
        
        for task in tasks:
            print_section(f"Testing: {task.upper()}")
            
            # Get models to test
            if small_only:
                models = self.get_small_fast_models("3B")
                # Filter to untested only
                untested = self.get_untested_models(task)
                untested_names = {m["name"] for m in untested}
                models = [m for m in models if m["name"] in untested_names]
            else:
                models = self.get_untested_models(task)
            
            models = models[:max_models]
            
            print_info(f"Models to test: {len(models)}")
            
            task_results = {"tested": 0, "success": 0, "failed": 0}
            
            for i, model in enumerate(models):
                print(f"\n[{i+1}/{len(models)}] {model['name']} ({model['params']})")
                
                try:
                    result = self.manager.benchmark_model(
                        model["name"],
                        model["provider"],
                        task
                    )
                    
                    task_results["tested"] += 1
                    
                    if result and result.success:
                        task_results["success"] += 1
                        print_success(f"  ✓ {result.tokens_per_second:.0f} tok/s, quality {result.output_quality:.1f}")
                    else:
                        task_results["failed"] += 1
                        print_warning(f"  ✗ Failed: {result.error if result else 'Unknown'}")
                    
                    # Wait between tests to avoid overload
                    time.sleep(2)
                    
                except Exception as e:
                    task_results["failed"] += 1
                    print_error(f"  Error: {e}")
            
            results["by_task"][task] = task_results
            results["tested"] += task_results["tested"]
            results["success"] += task_results["success"]
            results["failed"] += task_results["failed"]
        
        # Generate report
        self._print_report(results)
        
        return results
    
    def benchmark_specific_sizes(
        self,
        sizes: List[str] = None,
        tasks: List[str] = None
    ) -> Dict:
        """
        Benchmark models of specific sizes.
        
        Great for testing if small models (500M-2B) can handle your tasks!
        """
        sizes = sizes or ["500M", "1B", "2B"]
        tasks = tasks or self.TASKS
        
        print_section(f"TESTING MODEL SIZES: {', '.join(sizes)}")
        
        conn = self.manager._get_conn()
        
        # Get models of these sizes
        placeholders = ','.join('?' * len(sizes))
        rows = conn.execute(f"""
            SELECT name, provider, parameter_count
            FROM models
            WHERE parameter_count IN ({placeholders})
        """, sizes).fetchall()
        
        conn.close()
        
        models = [{"name": r[0], "provider": r[1], "params": r[2]} for r in rows]
        
        print_info(f"Found {len(models)} models of size {', '.join(sizes)}")
        
        results = {"by_size": {size: {"count": 0, "avg_speed": 0, "speeds": []} for size in sizes}}
        
        for model in models:
            for task in tasks:
                print(f"\nTesting {model['name']} ({model['params']}) on {task}")
                
                try:
                    result = self.manager.benchmark_model(
                        model["name"],
                        model["provider"],
                        task
                    )
                    
                    if result and result.success:
                        size = model["params"]
                        results["by_size"][size]["count"] += 1
                        results["by_size"][size]["speeds"].append(result.tokens_per_second)
                        
                        print_success(f"  {result.tokens_per_second:.0f} tok/s")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print_error(f"  Error: {e}")
        
        # Calculate averages
        for size, data in results["by_size"].items():
            if data["speeds"]:
                data["avg_speed"] = sum(data["speeds"]) / len(data["speeds"])
                data["max_speed"] = max(data["speeds"])
                data["min_speed"] = min(data["speeds"])
        
        # Print summary
        print_section("SIZE COMPARISON")
        for size in sizes:
            data = results["by_size"][size]
            if data["count"] > 0:
                print(f"{size}: avg {data['avg_speed']:.0f} tok/s "
                      f"(min {data.get('min_speed', 0):.0f}, max {data.get('max_speed', 0):.0f})")
        
        return results
    
    def find_winners(self) -> Dict[str, Dict]:
        """Find the best model for each task"""
        print_section("🏆 FINDING WINNERS")
        
        winners = {}
        
        for task in self.TASKS:
            best = self.manager.get_best_model(task)
            
            if best:
                winners[task] = best
                print(f"\n{task.upper()}:")
                print(f"  🥇 {best['name']}")
                print(f"     Speed: {best['speed_score']:.1f}/10")
                print(f"     Quality: {best['quality_score']:.1f}/10")
                print(f"     Overall: {best['overall_score']:.1f}/10")
            else:
                print(f"\n{task.upper()}: No winner yet (need more tests)")
        
        # Overall fastest
        fast = self.manager.get_fast_models(min_speed=100)
        if fast:
            print_section("⚡ SPEED CHAMPIONS (100+ tok/s)")
            for m in fast[:5]:
                print(f"  {m['name'][:40]:<40} {m['speed']:.0f} tok/s")
        
        # Uncensored winners
        print_section("🔓 UNCENSORED MODELS")
        uncensored = self.manager.get_uncensored_models()
        for m in uncensored[:10]:
            vision = "👁" if m.get("vision") else ""
            print(f"  {m['name'][:40]:<40} {m['provider']:<10} {vision}")
        
        return winners
    
    def _print_report(self, results: Dict):
        """Print benchmark report"""
        print_section("BENCHMARK REPORT")
        
        print(f"Total tested: {results['tested']}")
        print(f"Successful: {results['success']}")
        print(f"Failed: {results['failed']}")
        
        if results["success"] > 0:
            self.find_winners()
    
    def watch_for_new_models(self, check_interval: int = 300):
        """
        Watch for newly downloaded models and auto-test them.
        
        Args:
            check_interval: Seconds between checks (default 5 minutes)
        """
        print_section("MODEL WATCHER STARTED")
        print_info(f"Checking every {check_interval}s for new models")
        
        self.running = True
        known_models = set()
        
        # Get initial model list
        models = self.manager.discover_all_models()
        for provider_models in models.values():
            for m in provider_models:
                known_models.add(m.name)
        
        print_info(f"Tracking {len(known_models)} known models")
        
        while self.running:
            try:
                time.sleep(check_interval)
                
                # Check for new models
                models = self.manager.discover_all_models()
                current_models = set()
                
                for provider_models in models.values():
                    for m in provider_models:
                        current_models.add(m.name)
                
                new_models = current_models - known_models
                
                if new_models:
                    print_section(f"🆕 {len(new_models)} NEW MODELS DETECTED!")
                    
                    for model_name in new_models:
                        print_info(f"New: {model_name}")
                    
                    # Auto-benchmark new models
                    for model_name in new_models:
                        print_info(f"Auto-testing: {model_name}")
                        
                        # Find provider
                        provider = None
                        for prov, prov_models in models.items():
                            for m in prov_models:
                                if m.name == model_name:
                                    provider = m.provider
                                    break
                        
                        if provider:
                            for task in self.TASKS[:2]:  # Quick test on chat and caption
                                self.manager.benchmark_model(model_name, provider, task)
                                time.sleep(2)
                    
                    known_models.update(new_models)
                    print_success(f"Now tracking {len(known_models)} models")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print_warning(f"Watcher error: {e}")
        
        print_info("Model watcher stopped")
    
    def stop_watching(self):
        """Stop the model watcher"""
        self.running = False


def run_full_benchmark():
    """Run a complete benchmark of all models"""
    benchmarker = AutoBenchmarker()
    
    # First, discover all models
    benchmarker.discover_new_models()
    
    # Test small models first (they're fast!)
    print_section("PHASE 1: Small Model Speed Test")
    benchmarker.benchmark_specific_sizes(["500M", "1B", "2B", "3B"])
    
    # Test all untested models
    print_section("PHASE 2: Full Model Test")
    benchmarker.benchmark_all_untested(max_models=20, small_only=False)
    
    # Find winners
    winners = benchmarker.find_winners()
    
    # Save report
    report_path = Path(__file__).parent.parent.parent / "reports" / "benchmark_report.json"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "winners": winners
        }, f, indent=2, default=str)
    
    print_success(f"Report saved: {report_path}")
    
    return winners


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto Benchmarker")
    parser.add_argument("--full", action="store_true", help="Run full benchmark")
    parser.add_argument("--small", action="store_true", help="Test small models only")
    parser.add_argument("--watch", action="store_true", help="Watch for new models")
    parser.add_argument("--winners", action="store_true", help="Show current winners")
    parser.add_argument("--task", type=str, help="Test specific task only")
    parser.add_argument("--sizes", type=str, help="Test specific sizes (comma-separated)")
    
    args = parser.parse_args()
    
    benchmarker = AutoBenchmarker()
    
    if args.full:
        run_full_benchmark()
    elif args.small:
        benchmarker.benchmark_specific_sizes(["500M", "1B", "2B", "3B"])
        benchmarker.find_winners()
    elif args.watch:
        try:
            benchmarker.watch_for_new_models()
        except KeyboardInterrupt:
            benchmarker.stop_watching()
    elif args.winners:
        benchmarker.find_winners()
    elif args.task:
        benchmarker.benchmark_all_untested(task_type=args.task, max_models=10)
    elif args.sizes:
        sizes = args.sizes.split(",")
        benchmarker.benchmark_specific_sizes(sizes)
    else:
        # Default: quick test
        benchmarker.discover_new_models()
        benchmarker.benchmark_all_untested(max_models=5, small_only=True)
        benchmarker.find_winners()
