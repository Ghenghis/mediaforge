"""
Generate D cup tribal women - 25 images each size
22D to 40D, 85-115lb, 21yo, toned, tribal
"""
import requests
import random
import time
from datetime import datetime

COMFYUI_URL = "http://localhost:8188"

# D cup sizes requested
D_CUP_SIZES = [
    "22D", "24D", "26D", "28D", "30D", "32D", "34D", "36D", "38D", "40D"
]

IMAGES_PER_SIZE = 25

# Body weights 85-115lb
BODY_WEIGHTS = [
    "85 pound body", "90 pound body", "95 pound body",
    "100 pound body", "105 pound body", "110 pound body", "115 pound body",
    "slim", "petite", "slender", "lean"
]

# Breast shapes as requested
BREAST_SHAPES = [
    "perky breasts", "perky D cup",
    "puffy nipples", "puffy areolas",
    "pointed breasts", "pointed D cup",
    "round breasts", "round D cup", "perfectly round",
    "long nipples", "prominent nipples",
    "firm round breasts", "full round shape"
]

# Toned/fit body
TONED = [
    "toned body", "toned abs", "ripped stomach", "six pack",
    "athletic build", "fit body", "in shape", "muscular tone",
    "defined muscles", "lean muscles", "toned arms", "toned legs"
]

# Tribal/sexy elements
TRIBAL_SEXY = [
    "tribal woman", "tribal warrior", "amazon",
    "tribal body paint", "ceremonial paint", "war paint",
    "tribal face paint", "painted body",
    "sexy pose", "seductive", "alluring",
    "tribal jewelry", "bone necklace", "feathers",
    "minimal clothing", "tribal bikini"
]

SETTINGS = [
    "jungle background", "tribal village", "rainforest",
    "firelight", "sunset lighting", "golden hour",
    "dramatic lighting", "natural lighting"
]

QUALITY = "(masterpiece:1.3), (best quality:1.3), (photorealistic:1.4), (8k:1.2), (detailed skin:1.2), beautiful face, detailed eyes"

NEGATIVE = "deformed, bad anatomy, disfigured, poorly drawn, mutation, ugly, blurry, watermark, text, saggy breasts, deflated, droopy, misshapen"

def build_prompt(size):
    """Build prompt for D cup size"""
    band = size.replace("D", "")
    weight = random.choice(BODY_WEIGHTS)
    shapes = random.sample(BREAST_SHAPES, k=3)
    toned = random.sample(TONED, k=2)
    tribal = random.sample(TRIBAL_SEXY, k=4)
    setting = random.choice(SETTINGS)
    
    skin = random.choice(["tan skin", "bronze skin", "brown skin", "dark skin", "olive skin", "caramel skin"])
    
    parts = [
        QUALITY,
        "(21 year old woman:1.3)",
        f"({size} cup breasts:1.4)",
        f"({band} band size:1.2)",
        f"({', '.join(shapes)}:1.3)",
        f"({weight}:1.2)",
        f"({', '.join(toned)}:1.3)",
        f"({skin}:1.2)",
        f"({', '.join(tribal)}:1.2)",
        "(sexy:1.2)",
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

def generate_all():
    """Generate 25 of each D cup size"""
    total = len(D_CUP_SIZES) * IMAGES_PER_SIZE
    print(f"\n{'='*60}")
    print(f"  GENERATING {total} D CUP TRIBAL IMAGES")
    print(f"  Sizes: 22D - 40D ({len(D_CUP_SIZES)} sizes)")
    print(f"  {IMAGES_PER_SIZE} images each")
    print(f"  21yo, 85-115lb, toned, sexy, tribal")
    print(f"{'='*60}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    queued = 0
    current = 0
    
    for size in D_CUP_SIZES:
        print(f"\n--- {size} (25 images) ---")
        for i in range(IMAGES_PER_SIZE):
            current += 1
            prompt = build_prompt(size)
            seed = random.randint(1, 2**31)
            filename = f"tribal_Dcup_{size}_{timestamp}_{i+1:02d}"
            
            if queue_to_comfyui(prompt, NEGATIVE, seed, filename):
                queued += 1
                print(f"[{current:03d}/{total}] ✓ {size} #{i+1}")
            else:
                print(f"[{current:03d}/{total}] ✗ {size} #{i+1} FAILED")
            
            if current % 20 == 0:
                time.sleep(0.3)
    
    print(f"\n{'='*60}")
    print(f"  COMPLETE: {queued}/{total} queued")
    print(f"  Output: G:\\Github\\ComfyUI\\output\\")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    try:
        requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        print("✓ ComfyUI running")
    except:
        print("✗ ComfyUI not running!")
        exit(1)
    
    print(f"\nD Cup sizes: {', '.join(D_CUP_SIZES)}")
    print(f"{IMAGES_PER_SIZE} images each = {len(D_CUP_SIZES) * IMAGES_PER_SIZE} total")
    
    generate_all()
