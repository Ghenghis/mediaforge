"""
Generate 500 sexy 32AA images
21-28yo, 95-130lb, toned, variety of features
"""
import requests
import random
import time
from datetime import datetime

COMFYUI_URL = "http://localhost:8188"

# Fixed size
CUP_SIZE = "32AA"

# Ages 21-28
AGES = ["21yo", "22yo", "23yo", "24yo", "25yo", "26yo", "27yo", "28yo"]

# Weights 95-130lb
WEIGHTS = [
    "95 pound body", "100 pound body", "105 pound body",
    "110 pound body", "115 pound body", "120 pound body",
    "125 pound body", "130 pound body",
    "slim", "slender", "lean", "petite"
]

# Hair - long and short
HAIR_STYLES = [
    "long hair", "very long hair", "flowing long hair", "waist length hair",
    "short hair", "pixie cut", "bob haircut", "shoulder length hair",
    "hair down", "messy hair", "straight hair", "wavy hair", "curly hair"
]

HAIR_COLORS = [
    "blonde hair", "platinum blonde", "golden blonde",
    "brown hair", "brunette", "light brown hair", "dark brown hair",
    "black hair", "red hair", "auburn hair", "strawberry blonde"
]

# Eyes - blue and green only
EYE_COLORS = [
    "blue eyes", "bright blue eyes", "deep blue eyes", "light blue eyes",
    "green eyes", "bright green eyes", "emerald green eyes", "light green eyes",
    "blue-green eyes", "teal eyes"
]

# Different skin tones
SKIN_TONES = [
    "pale skin", "fair skin", "light skin", "porcelain skin",
    "tan skin", "golden tan", "sun-kissed skin",
    "olive skin", "mediterranean skin",
    "bronze skin", "caramel skin", "brown skin",
    "dark skin", "ebony skin"
]

# Breast shapes as requested
BREAST_SHAPES = [
    "pointy breasts", "pointed breasts", "pointy small breasts",
    "cone shaped breasts", "conical breasts", "torpedo shaped",
    "firm round breasts", "firm perky breasts",
    "perfectly round breasts", "round perky breasts",
    "pert breasts", "perky 32AA", "small firm breasts"
]

# Toned body
TONED = [
    "toned body", "toned abs", "flat stomach", "athletic build",
    "fit body", "in shape", "toned arms", "toned legs",
    "slim waist", "defined muscles", "lean muscles"
]

# Sexy elements
SEXY = [
    "sexy", "seductive", "alluring", "sensual", "attractive",
    "beautiful", "gorgeous", "stunning", "hot", "sultry",
    "bedroom eyes", "flirty", "confident pose"
]

# Settings/lighting
SETTINGS = [
    "studio lighting", "soft lighting", "natural lighting",
    "golden hour", "sunset lighting", "window light",
    "dramatic lighting", "professional photo", "glamour shot"
]

QUALITY = "(masterpiece:1.4), (best quality:1.4), (photorealistic:1.5), (8k:1.2), (ultra detailed:1.3), (detailed skin:1.3), beautiful face, detailed eyes, perfect face"

NEGATIVE = "deformed, bad anatomy, disfigured, poorly drawn, mutation, ugly, blurry, watermark, text, large breasts, big breasts, huge breasts, saggy, droopy, flat chest, masculine"

def build_prompt():
    """Build sexy 32AA prompt with variety"""
    age = random.choice(AGES)
    weight = random.choice(WEIGHTS)
    hair_style = random.choice(HAIR_STYLES)
    hair_color = random.choice(HAIR_COLORS)
    eyes = random.choice(EYE_COLORS)
    skin = random.choice(SKIN_TONES)
    shapes = random.sample(BREAST_SHAPES, k=2)
    toned = random.sample(TONED, k=2)
    sexy = random.sample(SEXY, k=2)
    setting = random.choice(SETTINGS)
    
    parts = [
        QUALITY,
        f"({age} woman:1.3)",
        f"({CUP_SIZE} cup breasts:1.4)",
        f"({', '.join(shapes)}:1.4)",
        f"({weight}:1.2)",
        f"({', '.join(toned)}:1.3)",
        f"({hair_color}:1.2)",
        f"({hair_style}:1.2)",
        f"({eyes}:1.3)",
        f"({skin}:1.2)",
        f"({', '.join(sexy)}:1.3)",
        setting
    ]
    return ", ".join(parts)

def queue_to_comfyui(prompt, negative, seed, filename):
    workflow = {
        "3": {"class_type": "KSampler", "inputs": {"cfg": 7, "denoise": 1, "latent_image": ["5", 0], "model": ["4", 0], "negative": ["7", 0], "positive": ["6", 0], "sampler_name": "euler_ancestral", "scheduler": "normal", "seed": seed, "steps": 30}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "CyberRealistic.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": 896, "width": 640}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": prompt}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": negative}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename, "images": ["8", 0]}}
    }
    try:
        r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=10)
        return 'prompt_id' in r.json()
    except:
        return False

def generate_batch(count=500):
    """Generate 500 32AA sexy images"""
    print(f"\n{'='*60}")
    print(f"  GENERATING {count} SEXY 32AA IMAGES")
    print(f"  Age: 21-28yo")
    print(f"  Body: 95-130lb, toned")
    print(f"  Eyes: Blue & Green")
    print(f"  Hair: Long & Short varieties")
    print(f"  Skin: Multiple tones")
    print(f"  Breasts: Pointy, Cone, Firm Round, Perfect Round")
    print(f"{'='*60}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    queued = 0
    
    for i in range(count):
        prompt = build_prompt()
        seed = random.randint(1, 2**31)
        filename = f"sexy_32AA_{timestamp}_{i+1:03d}"
        
        if queue_to_comfyui(prompt, NEGATIVE, seed, filename):
            queued += 1
            if (i + 1) % 10 == 0:
                print(f"[{i+1:03d}/{count}] ✓ Queued {queued} images...")
        else:
            print(f"[{i+1:03d}/{count}] ✗ FAILED")
        
        if (i + 1) % 25 == 0:
            time.sleep(0.3)
    
    print(f"\n{'='*60}")
    print(f"  COMPLETE: {queued}/{count} queued")
    print(f"  Output: G:\\Github\\ComfyUI\\output\\")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import sys
    try:
        requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        print("✓ ComfyUI running")
    except:
        print("✗ ComfyUI not running!")
        exit(1)
    
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    generate_batch(count)
