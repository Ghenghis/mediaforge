"""
Vision Model Tester - Test top vision models with sample images
Tests via LM Studio API (OpenAI-compatible endpoint)
"""

import os
import sys
import json
import base64
import time
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# LM Studio API endpoint
LM_STUDIO_URL = "http://localhost:1234/v1"

# Top 5 vision models to test (in order of priority)
TOP_VISION_MODELS = [
    {
        "name": "Qwen3-VL-8B-Abliterated-Caption-it",
        "path": "mradermacher/qwen3-vl-8b-abliterated-caption-it-i1-gguf",
        "size_gb": 7.9,
        "expected": "Best quality NSFW captions"
    },
    {
        "name": "Qwen3-VL-8B-NSFW-Caption-v4.5",
        "path": "Sail2Dream/qwen3-vl-8b-nsfw-caption-v4.5",
        "size_gb": 5.0,
        "expected": "Fast NSFW captions"
    },
    {
        "name": "Eris_PrimeV3.05-Vision-7B",
        "path": "mradermacher/eris_primev3.05-vision-7b-i1-gguf",
        "size_gb": 6.6,
        "expected": "RP + Vision combo"
    },
    {
        "name": "RP_Vision_7B",
        "path": "Lewdiculous/rp_vision_7b-iq-imatrix",
        "size_gb": 8.3,
        "expected": "RP-focused vision"
    },
    {
        "name": "Qwen2.5-VL-3B-Abliterated-Caption",
        "path": "mradermacher/qwen2.5-vl-3b-abliterated-caption-it-i1-gguf",
        "size_gb": 2.8,
        "expected": "Quick small captions"
    },
]

# Test prompt for captioning
CAPTION_PROMPT = """Describe this image in extensive detail. Include:
- Subject description (appearance, pose, expression, clothing)
- Setting and environment
- Lighting, colors, and mood
- Art style if applicable
- Any notable details

Be thorough and descriptive."""


def encode_image_to_base64(image_path: Path) -> str:
    """Encode image to base64 for API"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_mime_type(image_path: Path) -> str:
    """Get MIME type from extension"""
    ext = image_path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_types.get(ext, "image/jpeg")


def check_lm_studio_running() -> bool:
    """Check if LM Studio API is available"""
    try:
        response = httpx.get(f"{LM_STUDIO_URL}/models", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_loaded_model() -> Optional[str]:
    """Get currently loaded model in LM Studio"""
    try:
        response = httpx.get(f"{LM_STUDIO_URL}/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return data["data"][0].get("id", "unknown")
    except:
        pass
    return None


def test_vision_model(image_path: Path, prompt: str = CAPTION_PROMPT) -> Dict:
    """Test vision model with an image"""
    
    # Encode image
    base64_image = encode_image_to_base64(image_path)
    mime_type = get_image_mime_type(image_path)
    
    # Build request
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]
    
    start_time = time.time()
    
    try:
        response = httpx.post(
            f"{LM_STUDIO_URL}/chat/completions",
            json={
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.3,
                "stream": False
            },
            timeout=120  # Vision models can be slow
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {})
            
            return {
                "success": True,
                "content": content,
                "elapsed_seconds": round(elapsed, 2),
                "prompt_tokens": tokens.get("prompt_tokens", 0),
                "completion_tokens": tokens.get("completion_tokens", 0),
                "tokens_per_second": round(tokens.get("completion_tokens", 0) / elapsed, 1) if elapsed > 0 else 0
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
                "elapsed_seconds": round(elapsed, 2)
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "elapsed_seconds": round(time.time() - start_time, 2)
        }


def find_test_images() -> List[Path]:
    """Find sample images to test with"""
    test_dirs = [
        Path(r"C:\Users\Admin\civitai\test_images"),
        Path(r"C:\Users\Admin\Pictures"),
        Path(r"G:\Github\Frontier-Stories\assets"),
    ]
    
    images = []
    for d in test_dirs:
        if d.exists():
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
                images.extend(list(d.glob(ext))[:3])
    
    return images[:5]  # Max 5 test images


def run_vision_test(image_path: Optional[Path] = None):
    """Run vision model test"""
    
    print("\n" + "="*60)
    print("  VISION MODEL TESTER")
    print("="*60)
    
    # Check LM Studio
    if not check_lm_studio_running():
        print("\n❌ LM Studio API not available at", LM_STUDIO_URL)
        print("   Please start LM Studio and load a vision model.")
        print("\n   Recommended models to load:")
        for i, m in enumerate(TOP_VISION_MODELS, 1):
            print(f"   {i}. {m['name']} ({m['size_gb']} GB) - {m['expected']}")
        return
    
    # Get loaded model
    model = get_loaded_model()
    print(f"\n✅ LM Studio running")
    print(f"📦 Loaded model: {model or 'Unknown'}")
    
    # Find or use provided image
    if image_path and image_path.exists():
        test_images = [image_path]
    else:
        test_images = find_test_images()
        if not test_images:
            print("\n⚠️  No test images found. Please provide an image path:")
            print("   python -m ai.vision_tester <image_path>")
            return
    
    print(f"\n🖼️  Testing with {len(test_images)} image(s)")
    
    # Run tests
    results = []
    for img in test_images:
        print(f"\n{'─'*60}")
        print(f"Testing: {img.name}")
        print(f"{'─'*60}")
        
        result = test_vision_model(img)
        result["image"] = img.name
        results.append(result)
        
        if result["success"]:
            print(f"⏱️  Time: {result['elapsed_seconds']}s")
            print(f"📊 Tokens: {result['completion_tokens']} @ {result['tokens_per_second']} tok/s")
            print(f"\n📝 Caption:\n{result['content'][:500]}...")
        else:
            print(f"❌ Error: {result['error']}")
    
    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    
    successful = [r for r in results if r["success"]]
    if successful:
        avg_time = sum(r["elapsed_seconds"] for r in successful) / len(successful)
        avg_tokens = sum(r["tokens_per_second"] for r in successful) / len(successful)
        avg_length = sum(len(r["content"]) for r in successful) / len(successful)
        
        print(f"✅ Successful: {len(successful)}/{len(results)}")
        print(f"⏱️  Avg time: {avg_time:.1f}s")
        print(f"📊 Avg speed: {avg_tokens:.1f} tok/s")
        print(f"📝 Avg length: {avg_length:.0f} chars")
        
        # Quality assessment
        if avg_length > 300:
            print("\n🏆 Quality: DETAILED (good for training)")
        elif avg_length > 150:
            print("\n👍 Quality: ADEQUATE")
        else:
            print("\n⚠️  Quality: BRIEF (may need different model)")
    else:
        print("❌ All tests failed. Check model loading.")
    
    # Save results
    results_dir = Path(r"C:\Users\Admin\civitai\reports")
    results_dir.mkdir(exist_ok=True)
    results_file = results_dir / f"vision_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(results_file, "w") as f:
        json.dump({
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"\n📁 Results saved: {results_file}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test vision models")
    parser.add_argument("image", nargs="?", help="Image path to test")
    parser.add_argument("--list", action="store_true", help="List top vision models")
    args = parser.parse_args()
    
    if args.list:
        print("\n🏆 TOP VISION MODELS FOR PROJECT:")
        print("─" * 50)
        for i, m in enumerate(TOP_VISION_MODELS, 1):
            print(f"{i}. {m['name']}")
            print(f"   Size: {m['size_gb']} GB")
            print(f"   Use: {m['expected']}")
            print()
        return
    
    image_path = Path(args.image) if args.image else None
    run_vision_test(image_path)


if __name__ == "__main__":
    main()
