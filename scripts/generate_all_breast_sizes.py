"""
COMPREHENSIVE BREAST SIZE DATABASE
Generate 5 images of EVERY possible breast size
Properly named and organized
Ages 18-27, 95-125lb, toned sexy bodies
Full body detailed shots
"""
import requests
import random
import time
from datetime import datetime

COMFYUI_URL = "http://localhost:8188"

# ============================================================
# COMPLETE BREAST SIZE CHART
# ============================================================

# Band sizes (ribcage measurement)
BAND_SIZES = [28, 30, 32, 34, 36, 38, 40, 42, 44]

# Cup sizes from smallest to largest
CUP_SIZES = [
    ("AAA", "flat chest, nearly no breast tissue"),
    ("AA", "very small breasts, minimal breast tissue"),
    ("A", "small breasts, petite bust"),
    ("B", "small-medium breasts, modest bust"),
    ("C", "medium breasts, average bust"),
    ("D", "medium-large breasts, full bust"),
    ("DD", "large breasts, very full bust"),
    ("E", "large breasts, heavy bust"),  # Also called DDD
    ("F", "very large breasts, big bust"),
    ("G", "huge breasts, extremely full"),
    ("H", "massive breasts, very heavy bust"),
]

# Generate all size combinations
def get_all_sizes():
    """Generate all band+cup combinations"""
    sizes = []
    for band in BAND_SIZES:
        for cup, desc in CUP_SIZES:
            size_code = f"{band}{cup}"
            sizes.append({
                "code": size_code,
                "band": band,
                "cup": cup,
                "description": desc,
                "category": get_category(cup)
            })
    return sizes

def get_category(cup):
    """Categorize cup size"""
    if cup in ["AAA", "AA"]:
        return "tiny"
    elif cup in ["A", "B"]:
        return "small"
    elif cup in ["C", "D"]:
        return "medium"
    elif cup in ["DD", "E"]:
        return "large"
    else:
        return "huge"

ALL_SIZES = get_all_sizes()
IMAGES_PER_SIZE = 5

# Body weights 95-125lb
WEIGHTS = ["95lb", "100lb", "105lb", "110lb", "115lb", "120lb", "125lb"]

# Ages 18-27
AGES = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

# Breast shapes to vary
BREAST_SHAPES = [
    "round breasts", "perky breasts", "firm breasts",
    "natural shape", "teardrop shape", "full breasts"
]

# Toned sexy body
BODY_FEATURES = [
    "toned body", "athletic build", "fit body",
    "toned stomach", "toned legs", "slim waist",
    "sexy curves", "beautiful figure"
]

# Hair and details
HAIR_STYLES = ["long hair", "medium hair", "short hair", "wavy hair", "straight hair"]
HAIR_COLORS = ["blonde", "brunette", "black hair", "red hair", "auburn"]

# Skin tones
SKIN_TONES = ["pale skin", "fair skin", "tan skin", "olive skin", "bronze skin", "brown skin"]

# Eye colors
EYES = ["blue eyes", "green eyes", "brown eyes", "hazel eyes"]

QUALITY = "(masterpiece:1.4), (best quality:1.4), (photorealistic:1.5), (ultra realistic:1.4), (8k:1.3), (detailed skin texture:1.4), (pores:1.2), beautiful face, detailed eyes, professional photography, studio lighting, sharp focus"

def get_negative(category):
    """Get negative prompt based on size category"""
    base = "deformed, bad anatomy, disfigured, ugly, blurry, watermark, text, mutation, extra limbs"
    if category == "tiny":
        return base + ", large breasts, medium breasts, saggy"
    elif category == "small":
        return base + ", huge breasts, large breasts, saggy"
    elif category == "medium":
        return base + ", tiny breasts, flat chest, huge breasts"
    elif category == "large":
        return base + ", flat chest, tiny breasts, small breasts"
    else:  # huge
        return base + ", flat chest, small breasts, medium breasts"

def build_prompt(size_info, image_num):
    """Build detailed prompt for specific size"""
    age = random.choice(AGES)
    weight = random.choice(WEIGHTS)
    shape = random.choice(BREAST_SHAPES)
    body = random.sample(BODY_FEATURES, k=3)
    hair_style = random.choice(HAIR_STYLES)
    hair_color = random.choice(HAIR_COLORS)
    skin = random.choice(SKIN_TONES)
    eyes = random.choice(EYES)
    
    # Size-specific emphasis
    size_prompt = f"({size_info['code']} cup size:1.5), ({size_info['description']}:1.4)"
    
    parts = [
        QUALITY,
        f"({age} year old woman:1.3)",
        size_prompt,
        f"({shape}:1.3)",
        f"({weight} body:1.2)",
        f"({', '.join(body)}:1.3)",
        f"({hair_color} {hair_style}:1.2)",
        f"({eyes}:1.2)",
        f"({skin}:1.2)",
        "(extremely beautiful:1.3)",
        "(sexy:1.3)",
        "(full body shot:1.2)",
        "(trimmed pubic hair:1.2)",
        "(detailed:1.2)",
        "standing pose"
    ]
    return ", ".join(parts)

def queue_to_comfyui(prompt, negative, seed, filename):
    workflow = {
        "3": {"class_type": "KSampler", "inputs": {
            "cfg": 7.5, "denoise": 1, "latent_image": ["5", 0], 
            "model": ["4", 0], "negative": ["7", 0], "positive": ["6", 0], 
            "sampler_name": "euler_ancestral", "scheduler": "normal", 
            "seed": seed, "steps": 35
        }},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {
            "ckpt_name": "CyberRealistic.safetensors"
        }},
        "5": {"class_type": "EmptyLatentImage", "inputs": {
            "batch_size": 1, "height": 1024, "width": 680
        }},
        "6": {"class_type": "CLIPTextEncode", "inputs": {
            "clip": ["4", 1], "text": prompt
        }},
        "7": {"class_type": "CLIPTextEncode", "inputs": {
            "clip": ["4", 1], "text": negative
        }},
        "8": {"class_type": "VAEDecode", "inputs": {
            "samples": ["3", 0], "vae": ["4", 2]
        }},
        "9": {"class_type": "SaveImage", "inputs": {
            "filename_prefix": filename, "images": ["8", 0]
        }}
    }
    try:
        r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=10)
        return 'prompt_id' in r.json()
    except:
        return False

def generate_size_chart():
    """Generate the complete size chart"""
    total = len(ALL_SIZES) * IMAGES_PER_SIZE
    
    print(f"\n{'='*70}")
    print(f"  COMPREHENSIVE BREAST SIZE DATABASE GENERATOR")
    print(f"{'='*70}")
    print(f"\n  SIZES BREAKDOWN:")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Band sizes: {', '.join(str(b) for b in BAND_SIZES)}")
    print(f"  Cup sizes:  {', '.join(c[0] for c in CUP_SIZES)}")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Total unique sizes: {len(ALL_SIZES)}")
    print(f"  Images per size: {IMAGES_PER_SIZE}")
    print(f"  TOTAL IMAGES: {total}")
    print(f"{'='*70}")
    print(f"\n  FEATURES:")
    print(f"  • Ages: 18-27 years old")
    print(f"  • Body: 95-125lb, toned, sexy")
    print(f"  • Full body detailed shots")
    print(f"  • Various hair, eyes, skin tones")
    print(f"{'='*70}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    queued = 0
    current = 0
    
    # Group by category for organized output
    for category in ["tiny", "small", "medium", "large", "huge"]:
        cat_sizes = [s for s in ALL_SIZES if s["category"] == category]
        print(f"\n{'─'*50}")
        print(f"  CATEGORY: {category.upper()} ({len(cat_sizes)} sizes)")
        print(f"{'─'*50}")
        
        for size_info in cat_sizes:
            size_code = size_info["code"]
            print(f"\n  [{size_code}] - {size_info['description']}")
            
            for i in range(IMAGES_PER_SIZE):
                current += 1
                prompt = build_prompt(size_info, i+1)
                negative = get_negative(size_info["category"])
                seed = random.randint(1, 2**31)
                
                # Descriptive filename
                filename = f"size_{size_code}_{category}_{timestamp}_{i+1:02d}"
                
                if queue_to_comfyui(prompt, negative, seed, filename):
                    queued += 1
                    print(f"    [{current}/{total}] ✓ #{i+1}")
                else:
                    print(f"    [{current}/{total}] ✗ FAILED")
                
                if current % 30 == 0:
                    time.sleep(0.5)
    
    print(f"\n{'='*70}")
    print(f"  GENERATION COMPLETE")
    print(f"  Queued: {queued}/{total} images")
    print(f"  Output: G:\\Github\\ComfyUI\\output\\")
    print(f"{'='*70}\n")
    
    # Print size reference chart
    print_size_chart()

def print_size_chart():
    """Print reference chart of all sizes"""
    print(f"\n{'='*70}")
    print(f"  BREAST SIZE REFERENCE CHART")
    print(f"{'='*70}\n")
    
    # Header
    print(f"  {'Band':<6}", end="")
    for cup, _ in CUP_SIZES:
        print(f"{cup:>5}", end="")
    print()
    print(f"  {'─'*6}", end="")
    print("─" * (5 * len(CUP_SIZES)))
    
    # Each band size row
    for band in BAND_SIZES:
        print(f"  {band:<6}", end="")
        for cup, _ in CUP_SIZES:
            print(f"  ✓  ", end="")
        print()
    
    print(f"\n  Total: {len(ALL_SIZES)} unique sizes × {IMAGES_PER_SIZE} = {len(ALL_SIZES) * IMAGES_PER_SIZE} images")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    import sys
    
    try:
        requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        print("✓ ComfyUI running")
    except:
        print("✗ ComfyUI not running!")
        exit(1)
    
    # Show what we're about to generate
    print(f"\nThis will generate {len(ALL_SIZES) * IMAGES_PER_SIZE} images")
    print(f"({len(ALL_SIZES)} sizes × {IMAGES_PER_SIZE} each)")
    print("\nPress Enter to start or Ctrl+C to cancel...")
    
    try:
        input()
        generate_size_chart()
    except KeyboardInterrupt:
        print("\nCancelled.")
