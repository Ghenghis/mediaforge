"""Quick Vision Model Benchmark - Test top models with sample image"""
import base64
import time
import json
import httpx
from pathlib import Path
from datetime import datetime

LM_STUDIO_URL = "http://localhost:1234/v1"

# Top vision models to benchmark
MODELS_TO_TEST = [
    "lfm2-vl-1.6b",                          # Small/fast baseline
    "qwen3-vl-8b-abliterated-caption-it-i1", # Best quality
    "qwen3-vl-8b-nsfw-caption-v4.5",         # NSFW focused
    "thesby_qwen2.5-vl-7b-nsfw-caption-v3",  # Alternative NSFW
]

CAPTION_PROMPT = """Describe this image in extensive detail. Include:
- Subject appearance (physical features, pose, expression, clothing)
- Setting and environment
- Lighting, colors, mood
- Art style
Be thorough and explicit in your description."""

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def test_model(model_id: str, image_path: Path):
    """Test a single model"""
    print(f"\n{'─'*60}")
    print(f"Testing: {model_id}")
    print(f"{'─'*60}")
    
    ext = image_path.suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext[1:], "image/png")
    
    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encode_image(image_path)}"}},
            {"type": "text", "text": CAPTION_PROMPT}
        ]
    }]
    
    start = time.time()
    try:
        resp = httpx.post(
            f"{LM_STUDIO_URL}/chat/completions",
            json={"model": model_id, "messages": messages, "max_tokens": 500, "temperature": 0.3},
            timeout=180
        )
        elapsed = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("completion_tokens", len(content.split()))
            
            print(f"✅ Success in {elapsed:.1f}s")
            print(f"📊 ~{tokens} tokens @ {tokens/elapsed:.1f} tok/s")
            print(f"📝 Length: {len(content)} chars")
            print(f"\n{content[:400]}...")
            
            return {
                "model": model_id,
                "success": True,
                "time_s": round(elapsed, 1),
                "tokens": tokens,
                "tok_per_s": round(tokens/elapsed, 1),
                "length": len(content),
                "content": content
            }
        else:
            print(f"❌ HTTP {resp.status_code}")
            return {"model": model_id, "success": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"model": model_id, "success": False, "error": str(e)}

def main():
    print("="*60)
    print("  VISION MODEL BENCHMARK")
    print("="*60)
    
    # Find test image
    test_dirs = [
        Path(r"C:\Users\Admin\civitai\compare\ai-image-dataset-pipeline\backend\input_images"),
        Path(r"C:\Users\Admin\Pictures"),
    ]
    
    image = None
    for d in test_dirs:
        if d.exists():
            images = list(d.glob("*.png")) + list(d.glob("*.jpg"))
            if images:
                image = images[0]
                break
    
    if not image:
        print("❌ No test images found")
        return
    
    print(f"\n🖼️ Test image: {image.name}")
    print(f"📦 Testing {len(MODELS_TO_TEST)} models...")
    
    results = []
    for model_id in MODELS_TO_TEST:
        result = test_model(model_id, image)
        results.append(result)
    
    # Summary
    print("\n" + "="*60)
    print("  BENCHMARK RESULTS")
    print("="*60)
    
    successful = [r for r in results if r.get("success")]
    if successful:
        print(f"\n{'Model':<45} {'Time':>8} {'Tok/s':>8} {'Length':>8}")
        print("─"*70)
        for r in sorted(successful, key=lambda x: x["tok_per_s"], reverse=True):
            print(f"{r['model']:<45} {r['time_s']:>7}s {r['tok_per_s']:>7} {r['length']:>7}")
        
        # Winner
        best_speed = max(successful, key=lambda x: x["tok_per_s"])
        best_quality = max(successful, key=lambda x: x["length"])
        
        print(f"\n🏆 FASTEST: {best_speed['model']} ({best_speed['tok_per_s']} tok/s)")
        print(f"🏆 MOST DETAILED: {best_quality['model']} ({best_quality['length']} chars)")
    
    # Save results
    out_file = Path(r"C:\Users\Admin\civitai\reports\vision_benchmark_results.json")
    with open(out_file, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "results": results}, f, indent=2)
    print(f"\n📁 Saved: {out_file}")

if __name__ == "__main__":
    main()
