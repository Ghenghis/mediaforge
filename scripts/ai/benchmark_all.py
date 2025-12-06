"""
Comprehensive Model Benchmarker
Tests ALL models for speed and detail quality
Generates rankings for best overall performance
"""

import os
import sys
import json
import time
import httpx
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Configuration
LM_STUDIO_URL = "http://localhost:1234/v1"
RESULTS_DIR = Path(r"C:\Users\Admin\civitai\reports\benchmarks")
MODELS_DIR = Path(r"C:\Users\Admin\.lmstudio\models")

class ModelCategory(Enum):
    VISION_CAPTION = "vision_caption"      # Image/video description
    VISION_OCR = "vision_ocr"              # Text extraction
    WRITING_CREATIVE = "writing_creative"   # Stories, RP
    WRITING_TECHNICAL = "writing_technical" # Documentation
    CODING = "coding"                       # Code generation
    REASONING = "reasoning"                 # Logic, analysis
    SPEED = "speed"                         # Fast inference
    EMBEDDING = "embedding"                 # Vector embeddings

@dataclass
class BenchmarkResult:
    model_name: str
    category: str
    size_gb: float
    
    # Speed metrics
    tokens_per_second: float
    time_to_first_token: float
    total_time: float
    
    # Quality metrics
    output_length: int
    detail_score: float  # 0-10 based on content analysis
    
    # Computed scores
    speed_score: float   # Normalized 0-100
    quality_score: float # Normalized 0-100
    overall_score: float # Weighted combination
    
    timestamp: str = ""
    notes: str = ""


# Test prompts for different categories
TEST_PROMPTS = {
    "vision_detail": """Describe this image in extensive detail. Include:
- Every person/character visible (appearance, clothing, pose, expression)
- Complete environment description (setting, objects, background)
- Lighting, colors, shadows, and atmosphere
- Art style, composition, and technical quality
- Any text, symbols, or notable details
Be extremely thorough - describe everything you can see.""",

    "vision_quick": "Describe this image briefly but accurately.",
    
    "writing_detail": """Write a vivid, detailed scene about a mysterious stranger 
arriving at a frontier town at sunset. Include sensory details, character 
descriptions, and atmospheric elements. Make it immersive and literary.""",

    "writing_quick": "Write a brief scene about someone entering a saloon.",
    
    "coding": """Write a Python function that:
1. Takes a list of image paths
2. Loads each image and extracts EXIF data
3. Generates captions using an AI model
4. Saves results to a JSON file
Include error handling, type hints, and docstrings.""",

    "reasoning": """Analyze the following problem step by step:
A dataset has 10,000 images. 60% are high quality, 30% are medium, 10% are low.
You want to train a LoRA model using only the best images.
What's the optimal strategy for:
1. Quality threshold selection
2. Dataset size vs quality tradeoff  
3. Balancing diversity vs consistency
Show your reasoning.""",
}

# Model categories based on name patterns
MODEL_PATTERNS = {
    ModelCategory.VISION_CAPTION: [
        "vl", "vision", "caption", "qwen2.5-vl", "qwen3-vl", "llava", 
        "pixtral", "eris", "rp_vision"
    ],
    ModelCategory.VISION_OCR: ["ocr", "nanonets", "qari"],
    ModelCategory.WRITING_CREATIVE: [
        "writer", "story", "muse", "dolphin", "noromaid", "rp", 
        "uncensored", "nsfw", "abliterated", "gutenberg"
    ],
    ModelCategory.CODING: [
        "coder", "code", "deepcoder", "olympiccoder", "starcoder",
        "vibe-coder", "wolverine"
    ],
    ModelCategory.REASONING: [
        "reasoning", "deepseek-r1", "thinking", "reflect", "magistral"
    ],
    ModelCategory.SPEED: ["0.6b", "0.5b", "1b", "1.2b", "1.5b"],
    ModelCategory.EMBEDDING: ["embed", "reranker", "bge", "nomic"],
}


def categorize_model(model_name: str) -> ModelCategory:
    """Determine model category from name"""
    name_lower = model_name.lower()
    
    for category, patterns in MODEL_PATTERNS.items():
        if any(p in name_lower for p in patterns):
            return category
    
    # Default based on size
    return ModelCategory.WRITING_CREATIVE


def get_loaded_model() -> Optional[str]:
    """Get currently loaded model"""
    try:
        response = httpx.get(f"{LM_STUDIO_URL}/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return data["data"][0].get("id", "unknown")
    except:
        pass
    return None


def encode_image(path: Path) -> Tuple[str, str]:
    """Encode image to base64"""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    
    ext = path.suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", 
            "png": "image/png", "webp": "image/webp"}.get(ext[1:], "image/jpeg")
    
    return data, mime


def run_benchmark(prompt: str, image_path: Optional[Path] = None, 
                  max_tokens: int = 500) -> Dict:
    """Run a single benchmark test"""
    
    messages = []
    
    if image_path and image_path.exists():
        img_data, mime = encode_image(image_path)
        messages.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_data}"}},
                {"type": "text", "text": prompt}
            ]
        })
    else:
        messages.append({"role": "user", "content": prompt})
    
    start = time.time()
    first_token_time = None
    full_response = ""
    tokens_generated = 0
    
    try:
        # Try streaming for accurate timing
        with httpx.stream(
            "POST",
            f"{LM_STUDIO_URL}/chat/completions",
            json={
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": True
            },
            timeout=180
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    if first_token_time is None:
                        first_token_time = time.time() - start
                    
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_response += content
                            tokens_generated += 1
                    except:
                        pass
        
        total_time = time.time() - start
        
        return {
            "success": True,
            "content": full_response,
            "tokens": tokens_generated,
            "total_time": round(total_time, 2),
            "ttft": round(first_token_time or 0, 2),
            "tps": round(tokens_generated / total_time, 1) if total_time > 0 else 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total_time": time.time() - start
        }


def calculate_detail_score(text: str, category: ModelCategory) -> float:
    """Score output detail quality 0-10"""
    
    if not text:
        return 0.0
    
    score = 0.0
    length = len(text)
    
    # Base score from length
    if length > 1000:
        score += 3.0
    elif length > 500:
        score += 2.0
    elif length > 200:
        score += 1.0
    
    # Category-specific scoring
    if category in [ModelCategory.VISION_CAPTION, ModelCategory.WRITING_CREATIVE]:
        # Check for descriptive elements
        descriptors = ["wearing", "appears", "expression", "background", "lighting",
                      "atmosphere", "detailed", "visible", "showing", "positioned"]
        score += min(3.0, sum(0.3 for d in descriptors if d in text.lower()))
        
        # Check for structure
        if "\n" in text or ":" in text:
            score += 0.5
        
        # Check for specific details
        if any(c.isdigit() for c in text):  # Contains numbers
            score += 0.5
        
    elif category == ModelCategory.CODING:
        # Check for code quality markers
        if "def " in text or "function" in text:
            score += 1.0
        if "try:" in text or "except" in text:
            score += 1.0
        if '"""' in text or "'''" in text:  # Docstrings
            score += 1.0
        if "->" in text or ": str" in text:  # Type hints
            score += 1.0
    
    elif category == ModelCategory.REASONING:
        # Check for reasoning structure
        if any(x in text.lower() for x in ["step", "first", "therefore", "because"]):
            score += 2.0
        if any(x in text for x in ["1.", "2.", "3."]):
            score += 1.0
    
    return min(10.0, score)


def scan_models() -> List[Dict]:
    """Scan all models in LM Studio directory"""
    models = []
    
    for gguf in MODELS_DIR.rglob("*.gguf"):
        if "mmproj" in gguf.name.lower():
            continue
        
        size_gb = gguf.stat().st_size / (1024**3)
        category = categorize_model(gguf.stem)
        
        models.append({
            "name": gguf.stem,
            "path": str(gguf),
            "size_gb": round(size_gb, 2),
            "category": category.value,
            "parent": gguf.parent.name
        })
    
    return sorted(models, key=lambda x: x["size_gb"])


def print_model_summary():
    """Print summary of all models by category"""
    models = scan_models()
    
    print("\n" + "="*70)
    print("  MODEL INVENTORY BY CATEGORY")
    print("="*70)
    
    by_category = {}
    for m in models:
        cat = m["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(m)
    
    for cat, cat_models in sorted(by_category.items()):
        total_size = sum(m["size_gb"] for m in cat_models)
        print(f"\n📁 {cat.upper()} ({len(cat_models)} models, {total_size:.1f} GB)")
        print("-" * 50)
        
        # Show top 5 by size
        for m in sorted(cat_models, key=lambda x: x["size_gb"], reverse=True)[:5]:
            print(f"  {m['size_gb']:6.1f} GB  {m['name'][:45]}")
        
        if len(cat_models) > 5:
            print(f"  ... and {len(cat_models) - 5} more")


def generate_test_plan() -> Dict:
    """Generate optimized test plan"""
    models = scan_models()
    
    # Prioritize by usefulness for the project
    priority_order = [
        ModelCategory.VISION_CAPTION,
        ModelCategory.WRITING_CREATIVE, 
        ModelCategory.VISION_OCR,
        ModelCategory.REASONING,
        ModelCategory.CODING,
        ModelCategory.SPEED,
    ]
    
    plan = {
        "total_models": len(models),
        "estimated_time_hours": len(models) * 2 / 60,  # ~2 min per model
        "categories": {},
        "test_order": []
    }
    
    for cat in priority_order:
        cat_models = [m for m in models if m["category"] == cat.value]
        if cat_models:
            # Sort: smaller models first (faster to test)
            cat_models.sort(key=lambda x: x["size_gb"])
            plan["categories"][cat.value] = {
                "count": len(cat_models),
                "models": [m["name"] for m in cat_models]
            }
            plan["test_order"].extend(cat_models)
    
    return plan


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark all models")
    parser.add_argument("--scan", action="store_true", help="Scan and show model inventory")
    parser.add_argument("--plan", action="store_true", help="Generate test plan")
    parser.add_argument("--test", action="store_true", help="Run quick test on loaded model")
    parser.add_argument("--image", type=str, help="Image path for vision test")
    args = parser.parse_args()
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.scan:
        print_model_summary()
        return
    
    if args.plan:
        plan = generate_test_plan()
        print("\n" + "="*70)
        print("  BENCHMARK TEST PLAN")
        print("="*70)
        print(f"\nTotal models: {plan['total_models']}")
        print(f"Estimated time: {plan['estimated_time_hours']:.1f} hours")
        print("\nBy category:")
        for cat, info in plan["categories"].items():
            print(f"  {cat}: {info['count']} models")
        
        # Save plan
        plan_file = RESULTS_DIR / "test_plan.json"
        with open(plan_file, "w") as f:
            json.dump(plan, f, indent=2)
        print(f"\nPlan saved: {plan_file}")
        return
    
    if args.test:
        model = get_loaded_model()
        if not model:
            print("❌ No model loaded in LM Studio")
            return
        
        print(f"\n🧪 Testing: {model}")
        print("-" * 50)
        
        # Determine if vision model
        is_vision = any(x in model.lower() for x in ["vl", "vision", "llava", "pixtral"])
        
        if is_vision and args.image:
            img_path = Path(args.image)
            print(f"📷 Using image: {img_path.name}")
            result = run_benchmark(TEST_PROMPTS["vision_detail"], img_path)
        elif is_vision:
            print("⚠️  Vision model detected but no --image provided")
            print("   Using text prompt instead")
            result = run_benchmark(TEST_PROMPTS["writing_detail"])
        else:
            result = run_benchmark(TEST_PROMPTS["writing_detail"])
        
        if result["success"]:
            print(f"\n✅ Success!")
            print(f"⏱️  Time: {result['total_time']}s")
            print(f"🚀 Speed: {result['tps']} tok/s")
            print(f"📝 Output: {len(result['content'])} chars")
            print(f"\n--- Response Preview ---")
            print(result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"])
        else:
            print(f"❌ Error: {result.get('error', 'Unknown')}")
        
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
