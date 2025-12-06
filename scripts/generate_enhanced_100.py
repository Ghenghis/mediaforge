"""
ENHANCED IMAGE GENERATOR
- Analyzes your 8+ rated images
- Creates enhanced prompts with perfection tags
- Generates 100 new images via ComfyUI
"""
import requests
import json
import time
import random
from pathlib import Path
from datetime import datetime

COMFYUI_URL = "http://localhost:8188"
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")

# Based on your high-rated images: tribal, warrior, smart themes
# These were your best performers (8-10 ratings)

# PERFECTION QUALITY TAGS
QUALITY_TAGS = [
    "masterpiece", "best quality", "highly detailed", "ultra detailed",
    "8k uhd", "high resolution", "photorealistic", "hyperrealistic",
    "professional photography", "award winning photo"
]

FACE_DETAIL_TAGS = [
    "detailed face", "beautiful face", "perfect face", "symmetrical face",
    "detailed eyes", "beautiful eyes", "sparkling eyes", "expressive eyes",
    "detailed pupils", "long eyelashes", "perfect nose", "detailed lips"
]

SKIN_DETAIL_TAGS = [
    "detailed skin", "flawless skin", "smooth skin", "skin texture",
    "subsurface scattering", "natural skin tone", "healthy skin", "glowing skin"
]

BODY_TAGS = [
    "perfect anatomy", "perfect proportions", "elegant pose", "natural pose"
]

LIGHTING_TAGS = [
    "cinematic lighting", "soft lighting", "natural lighting", "dramatic lighting",
    "rim lighting", "volumetric lighting", "golden hour lighting"
]

CAMERA_TAGS = [
    "sharp focus", "depth of field", "bokeh", "85mm lens", "DSLR", "RAW photo"
]

NEGATIVE_PROMPT = """bad anatomy, bad hands, bad fingers, extra fingers, missing fingers, 
deformed, disfigured, mutated, ugly, blurry, low quality, worst quality, 
jpeg artifacts, watermark, text, signature, extra limbs, missing limbs, 
poorly drawn, amateur, distorted, cropped, out of frame"""

# THEMES based on your 8-10 rated images
THEMES = {
    "tribal_warrior": {
        "base": "tribal warrior woman",
        "details": ["tribal paint", "war paint", "tribal jewelry", "feathers", 
                   "natural environment", "fierce expression", "strong pose",
                   "warrior stance", "traditional tribal attire", "ethnic beauty"],
        "weight": 4  # Most of your high-rated were tribal
    },
    "elegant_portrait": {
        "base": "beautiful woman portrait",
        "details": ["elegant", "sophisticated", "refined features", "graceful",
                   "poised", "stunning beauty", "captivating gaze", "alluring"],
        "weight": 3
    },
    "natural_beauty": {
        "base": "naturally beautiful woman",
        "details": ["no makeup", "natural look", "authentic beauty", "genuine smile",
                   "warm expression", "approachable", "wholesome", "radiant"],
        "weight": 2
    },
    "artistic_portrait": {
        "base": "artistic portrait of a woman",
        "details": ["fine art", "artistic composition", "creative lighting",
                   "studio portrait", "professional model", "fashion photography"],
        "weight": 1
    }
}


def build_enhanced_prompt(theme_key):
    """Build a perfection-level prompt for a theme"""
    theme = THEMES[theme_key]
    
    parts = [theme["base"]]
    
    # Add theme-specific details (random selection)
    parts.extend(random.sample(theme["details"], min(5, len(theme["details"]))))
    
    # Add quality tags
    parts.extend(random.sample(QUALITY_TAGS, 6))
    
    # Add face details
    parts.extend(random.sample(FACE_DETAIL_TAGS, 6))
    
    # Add skin details
    parts.extend(random.sample(SKIN_DETAIL_TAGS, 4))
    
    # Add body tags
    parts.extend(random.sample(BODY_TAGS, 2))
    
    # Add lighting
    parts.extend(random.sample(LIGHTING_TAGS, 3))
    
    # Add camera
    parts.extend(random.sample(CAMERA_TAGS, 3))
    
    return ", ".join(parts)


def get_weighted_theme():
    """Select theme based on weights (tribal has highest weight)"""
    themes = []
    for key, data in THEMES.items():
        themes.extend([key] * data["weight"])
    return random.choice(themes)


def create_workflow(prompt, negative, seed, filename):
    """Create ComfyUI workflow for image generation"""
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": 7,
                "denoise": 1,
                "latent_image": ["5", 0],
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "seed": seed,
                "steps": 30
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "CyberRealistic.safetensors"
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "batch_size": 1,
                "height": 768,
                "width": 512
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": prompt
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": negative
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename,
                "images": ["8", 0]
            }
        }
    }


def queue_prompt(workflow):
    """Send workflow to ComfyUI"""
    try:
        response = requests.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow},
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None


def check_comfyui():
    """Check if ComfyUI is running"""
    try:
        r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        return r.status_code == 200
    except:
        return False


def main():
    print("=" * 60)
    print("  ENHANCED IMAGE GENERATOR")
    print("  Based on your 8-10 rated images")
    print("=" * 60)
    
    # Check ComfyUI
    if not check_comfyui():
        print("\n❌ ComfyUI not running at", COMFYUI_URL)
        print("   Please start ComfyUI first!")
        return
    
    print("\n✅ ComfyUI connected")
    
    # Theme distribution
    print("\n📊 Theme Distribution (based on your ratings):")
    for key, data in THEMES.items():
        pct = data["weight"] / sum(t["weight"] for t in THEMES.values()) * 100
        print(f"   {key}: {pct:.0f}%")
    
    print(f"\n🎯 Generating 100 enhanced images...")
    print(f"   Output: {OUTPUT_DIR}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    generated = 0
    errors = 0
    
    prompts_used = []
    
    for i in range(100):
        theme = get_weighted_theme()
        prompt = build_enhanced_prompt(theme)
        seed = random.randint(1, 2**31)
        filename = f"enhanced_{timestamp}_{theme}_{i+1:03d}"
        
        workflow = create_workflow(prompt, NEGATIVE_PROMPT, seed, filename)
        result = queue_prompt(workflow)
        
        if result and "prompt_id" in result:
            generated += 1
            prompts_used.append({
                "num": i+1,
                "theme": theme,
                "prompt": prompt[:100] + "...",
                "seed": seed
            })
            print(f"   [{i+1:3d}/100] ✓ {theme} - seed {seed}")
        else:
            errors += 1
            print(f"   [{i+1:3d}/100] ✗ Failed")
        
        # Small delay to not overwhelm ComfyUI
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"  GENERATION COMPLETE")
    print(f"  Queued: {generated} | Errors: {errors}")
    print("=" * 60)
    
    # Save prompts log
    log_path = Path(r"c:\Users\Admin\civitai\data\enhanced_prompts_log.json")
    with open(log_path, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "total": generated,
            "themes": {k: v["weight"] for k, v in THEMES.items()},
            "prompts": prompts_used[:20]  # Save first 20 as sample
        }, f, indent=2)
    print(f"\n📝 Prompt log saved to: {log_path}")
    
    print("\n⏳ Images will generate in ComfyUI queue...")
    print("   Check ComfyUI for progress")
    print("   New images will appear in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
