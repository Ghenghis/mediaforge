"""
Generate 50 images of each specific cup size
21yo, toned, 85-95lb small frame, tribal
"""
import requests
import random
import time
from datetime import datetime

COMFYUI_URL = "http://localhost:8188"

# Specific sizes requested - 50 of each
SPECIFIC_SIZES = [
    # AAA sizes
    "30AAA", "32AAA", "34AAA", "36AAA", "38AAA", "40AAA", "42AAA", "44AAA", "46AAA",
    # AAAA (flat/micro) sizes
    "34AAAA", "36AAAA", "38AAAA", "40AAAA", "42AAAA", "44AAAA", "46AAAA", "48AAAA",
    # AA sizes
    "30AA",
    # BBBB (tiny B) sizes  
    "30BBBB", "32BBBB", "34BBBB", "36BBBB", "38BBBB", "40BBBB",
    # BB sizes
    "30BB", "32BB", "34BB", "36BB", "38BB", "40BB", "42BB", "44BB"
]

IMAGES_PER_SIZE = 50

# Map special sizes to prompts
def size_to_prompt(size):
    """Convert size code to descriptive prompt"""
    if "AAAA" in size:
        band = size.replace("AAAA", "")
        return f"completely flat chest, {band} band size, no breasts, flat as board"
    elif "AAA" in size:
        band = size.replace("AAA", "")
        return f"AAA cup, {band} band, nearly flat chest, tiny breasts"
    elif "BBBB" in size:
        band = size.replace("BBBB", "")
        return f"very small B cup, {band} band, tiny B cup breasts, minimal breasts"
    elif "BB" in size:
        band = size.replace("BB", "")
        return f"small B cup, {band} band, petite B cup breasts"
    elif "AA" in size:
        band = size.replace("AA", "")
        return f"AA cup, {band} band, very small breasts"
    else:
        return f"{size} cup breasts"

# Breast shapes
BREAST_SHAPES = [
    "perky", "puffy nipples", "pointed breasts", "upward pointing",
    "outward pointing", "round shape", "firm", "pert",
    "long nipples", "puffy areolas", "pointed nipples", "small nipples"
]

# Body descriptors - 85-95lb
BODY = [
    "85 pound body", "90 pound body", "95 pound body",
    "very petite", "tiny frame", "small frame", "slender"
]

# Toned/athletic
TONED = [
    "toned body", "toned abs", "ripped stomach", "six pack abs",
    "defined muscles", "athletic", "fit", "lean muscles",
    "toned arms", "toned legs", "muscular definition"
]

# Tribal elements
TRIBAL = [
    "tribal woman", "tribal warrior", "amazon warrior",
    "tribal body paint", "face paint", "war paint",
    "tribal jewelry", "bone necklace", "feathers",
    "jungle background", "tribal setting"
]

QUALITY = "(masterpiece:1.3), (best quality:1.3), (photorealistic:1.4), (8k:1.2), (detailed skin:1.2)"

NEGATIVE = "deformed, bad anatomy, disfigured, poorly drawn, mutation, ugly, blurry, watermark, text, huge breasts, massive breasts, large breasts, big breasts, C cup, D cup, DD cup, oversized"

def build_prompt(size):
    """Build prompt for specific size"""
    size_desc = size_to_prompt(size)
    body = random.choice(BODY)
    toned = random.sample(TONED, k=2)
    shapes = random.sample(BREAST_SHAPES, k=2)
    tribal = random.sample(TRIBAL, k=3)
    
    skin = random.choice(["tan skin", "bronze skin", "brown skin", "dark skin", "olive skin"])
    
    parts = [
        QUALITY,
        "(21 year old woman:1.3)",
        f"({size_desc}:1.4)",
        f"({', '.join(shapes)}:1.3)",
        f"({body}:1.3)",
        f"({', '.join(toned)}:1.3)",
        f"({skin}:1.2)",
        f"({', '.join(tribal)}:1.2)",
        "natural lighting", "full body"
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
    """Generate 50 of each size"""
    total = len(SPECIFIC_SIZES) * IMAGES_PER_SIZE
    print(f"\n{'='*60}")
    print(f"  GENERATING {total} IMAGES")
    print(f"  {len(SPECIFIC_SIZES)} sizes × {IMAGES_PER_SIZE} each")
    print(f"  21yo, toned, 85-95lb, tribal")
    print(f"{'='*60}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    queued = 0
    current = 0
    
    for size in SPECIFIC_SIZES:
        print(f"\n--- {size} (50 images) ---")
        for i in range(IMAGES_PER_SIZE):
            current += 1
            prompt = build_prompt(size)
            seed = random.randint(1, 2**31)
            filename = f"tribal_{size}_{timestamp}_{i+1:02d}"
            
            if queue_to_comfyui(prompt, NEGATIVE, seed, filename):
                queued += 1
                print(f"[{current:04d}/{total}] ✓ {size} #{i+1}")
            else:
                print(f"[{current:04d}/{total}] ✗ {size} #{i+1} FAILED")
            
            if current % 20 == 0:
                time.sleep(0.5)
    
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
    
    print(f"\nSizes to generate ({len(SPECIFIC_SIZES)} total):")
    for s in SPECIFIC_SIZES:
        print(f"  - {s}")
    print(f"\n{IMAGES_PER_SIZE} images each = {len(SPECIFIC_SIZES) * IMAGES_PER_SIZE} total")
    
    generate_all()
