"""
Vision Model Speed Benchmark
============================
Tests multiple vision models to find the fastest for training.
"""

import requests
import time
import base64
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Models to benchmark (organized by size)
VISION_MODELS = {
    # 1-2B (Ultra Fast)
    "1.6B": ["lfm2-vl-1.6b"],
    "2B": [
        "qwen2-vl-ocr-2b-instruct",
        "granite-vision-3.2-2b",
        "vlaa-thinker-qwen2vl-2b-i1",
        "blazer.1-2b-vision",
    ],
    # 3-4B (Fast)
    "3B": [
        "qwen2.5-vl-3b-abliterated-caption-it-i1",
        "qwen2.5-vl-3b-instruct",
        "nanonets-ocr2-3b",
    ],
    "4B": ["qwen/qwen3-vl-4b"],
    # 7-8B (Balanced)
    "7B": [
        "thesby_qwen2.5-vl-7b-nsfw-caption-v3",
        "eris_primev3.05-vision-7b-i1",
        "qwen2.5-vl-7b-instruct",
    ],
    "8B": [
        "qwen3-vl-8b-abliterated-caption-it",
        "qwen3-vl-8b-nsfw-caption-v4.5",
        "huihui-qwen3-vl-8b-instruct-abliterated",
    ],
    # 11-12B (Quality)
    "11B": ["llama-3.2-11b-vision-instruct@q4_k_m"],
    "12B": ["amoral-gemma3-12b-vision-i1"],
}

# Flatten for quick access
ALL_MODELS = []
for size, models in VISION_MODELS.items():
    for m in models:
        ALL_MODELS.append((size, m))


def benchmark_model(model_name: str, test_images: List[Path], prompt: str) -> Dict:
    """Benchmark a single model"""
    results = {
        "model": model_name,
        "times": [],
        "outputs": [],
        "errors": [],
    }
    
    for img_path in test_images:
        try:
            img_data = base64.b64encode(img_path.read_bytes()).decode()
            
            start = time.time()
            response = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json={
                    "model": model_name,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}
                        ]
                    }],
                    "max_tokens": 200,
                    "temperature": 0.3,
                },
                timeout=120
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                results["times"].append(elapsed)
                results["outputs"].append(content[:200])
            else:
                results["errors"].append(f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            results["errors"].append("TIMEOUT")
        except Exception as e:
            results["errors"].append(str(e)[:50])
    
    # Calculate stats
    if results["times"]:
        results["avg_time"] = sum(results["times"]) / len(results["times"])
        results["min_time"] = min(results["times"])
        results["max_time"] = max(results["times"])
        results["throughput_per_hour"] = 3600 / results["avg_time"]
    else:
        results["avg_time"] = 999
        results["throughput_per_hour"] = 0
    
    return results


def run_benchmark(models_to_test: List[str] = None, num_images: int = 3):
    """Run benchmark on selected models"""
    
    # Find test images
    test_dirs = [
        Path(r"C:\Users\Admin\civitai\training_data\batch_04\batch_04"),
        Path(r"C:\Users\Admin\civitai\training_data\batch_01\batch_01"),
    ]
    
    test_images = []
    for d in test_dirs:
        if d.exists():
            test_images = list(d.glob("*.jpg"))[:num_images]
            break
    
    if not test_images:
        print("ERROR: No test images found!")
        return []
    
    print(f"Testing with {len(test_images)} images")
    print()
    
    # Default prompt
    prompt = "Describe this image in detail. Include subjects, actions, setting, and style."
    
    # Select models to test
    if models_to_test is None:
        # Test one from each size category
        models_to_test = [
            "lfm2-vl-1.6b",                           # 1.6B
            "qwen2-vl-ocr-2b-instruct",               # 2B
            "qwen2.5-vl-3b-abliterated-caption-it-i1", # 3B
            "qwen/qwen3-vl-4b",                        # 4B
            "qwen2.5-vl-7b-instruct",                  # 7B
            "qwen3-vl-8b-abliterated-caption-it",     # 8B (current)
        ]
    
    all_results = []
    
    print("=" * 70)
    print("  VISION MODEL BENCHMARK")
    print("=" * 70)
    print()
    
    for i, model in enumerate(models_to_test):
        print(f"[{i+1}/{len(models_to_test)}] Testing: {model}")
        
        result = benchmark_model(model, test_images, prompt)
        all_results.append(result)
        
        if result["times"]:
            print(f"    Avg: {result['avg_time']:.1f}s | Range: {result['min_time']:.1f}-{result['max_time']:.1f}s")
            print(f"    Throughput: {result['throughput_per_hour']:.0f} img/hour")
        else:
            print(f"    FAILED: {result['errors']}")
        print()
    
    # Sort by speed
    all_results.sort(key=lambda x: x["avg_time"])
    
    # Print comparison table
    print()
    print("=" * 70)
    print("  RESULTS (sorted by speed)")
    print("=" * 70)
    print()
    print(f"{'Model':<45} {'Avg':<8} {'img/hr':<10} {'Speedup'}")
    print("-" * 70)
    
    baseline = all_results[-1]["avg_time"] if all_results else 1
    
    for r in all_results:
        speedup = baseline / r["avg_time"] if r["avg_time"] > 0 else 0
        status = "FASTEST" if r == all_results[0] else ""
        print(f"{r['model'][:44]:<45} {r['avg_time']:.1f}s{'':<4} {r['throughput_per_hour']:.0f}{'':<6} {speedup:.1f}x {status}")
    
    # Calculate time estimates for Batches 4+5
    print()
    print("=" * 70)
    print("  TIME ESTIMATES FOR BATCHES 4+5 (6,180 images)")
    print("=" * 70)
    print()
    
    for r in all_results[:5]:  # Top 5
        hours = (6180 * r["avg_time"]) / 3600
        hours_15x = hours * 15
        print(f"{r['model'][:35]:<36} 1x: {hours:.1f}h | 15x: {hours_15x:.0f}h ({hours_15x/24:.1f} days)")
    
    # Save results
    output_file = Path(r"C:\Users\Admin\civitai\output\benchmark_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_images": len(test_images),
            "results": [{
                "model": r["model"],
                "avg_time": r["avg_time"],
                "throughput_per_hour": r["throughput_per_hour"],
                "errors": r["errors"],
            } for r in all_results]
        }, f, indent=2)
    
    print()
    print(f"Results saved to: {output_file}")
    
    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", help="Specific models to test")
    parser.add_argument("--images", type=int, default=3, help="Number of test images")
    parser.add_argument("--all-2b", action="store_true", help="Test all 2B models")
    parser.add_argument("--all-3b", action="store_true", help="Test all 3B models")
    parser.add_argument("--quick", action="store_true", help="Quick test (1 image each)")
    
    args = parser.parse_args()
    
    models = args.models
    num_images = 1 if args.quick else args.images
    
    if args.all_2b:
        models = VISION_MODELS["2B"]
    elif args.all_3b:
        models = VISION_MODELS["3B"]
    
    run_benchmark(models, num_images)
