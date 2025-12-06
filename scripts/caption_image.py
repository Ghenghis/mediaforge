"""
Simple Image Captioner - Use vision model to caption images for training
Usage: python caption_image.py <image_path>
       python caption_image.py <folder_path> --batch
"""
import sys
import base64
import httpx
from pathlib import Path

LM_STUDIO_URL = "http://localhost:1234/v1"
MODEL = "lfm2-vl-1.6b"  # Fast model (use qwen3-vl-8b-abliterated-caption-it-i1 for quality)

PROMPT = """Describe this image in detail for AI training. Include:
- Subject appearance, pose, expression, clothing
- Setting, background, environment  
- Lighting, colors, art style
- Any text or notable elements
Be thorough and specific."""

def caption_image(image_path: Path) -> str:
    """Get caption for a single image"""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    
    ext = image_path.suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext[1:], "image/png")
    
    resp = httpx.post(
        f"{LM_STUDIO_URL}/chat/completions",
        json={
            "model": MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    {"type": "text", "text": PROMPT}
                ]
            }],
            "max_tokens": 500,
            "temperature": 0.3
        },
        timeout=180
    )
    
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API Error: {resp.status_code}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python caption_image.py <image_or_folder> [--batch]")
        return
    
    path = Path(sys.argv[1])
    batch_mode = "--batch" in sys.argv
    
    if path.is_file():
        print(f"Captioning: {path.name}")
        caption = caption_image(path)
        print(f"\n{caption}")
        
        # Save caption as .txt file (Kohya format)
        txt_path = path.with_suffix(".txt")
        txt_path.write_text(caption)
        print(f"\n✅ Saved: {txt_path}")
        
    elif path.is_dir() and batch_mode:
        images = list(path.glob("*.png")) + list(path.glob("*.jpg")) + list(path.glob("*.webp"))
        print(f"Found {len(images)} images")
        
        for i, img in enumerate(images, 1):
            txt_path = img.with_suffix(".txt")
            if txt_path.exists():
                print(f"[{i}/{len(images)}] Skip (exists): {img.name}")
                continue
                
            print(f"[{i}/{len(images)}] Captioning: {img.name}...")
            try:
                caption = caption_image(img)
                txt_path.write_text(caption)
                print(f"  ✅ Saved {len(caption)} chars")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        print("\n✅ Batch complete!")
    else:
        print("Provide an image file or use --batch for folders")

if __name__ == "__main__":
    main()
