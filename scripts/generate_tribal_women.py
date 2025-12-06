"""
Generate 300-400 tribal women images
Small cups (AAA, AA, A, B) on various band sizes 28-48
Toned athletic bodies with body paint
"""
import requests
import random
import time
from datetime import datetime

COMFYUI_URL = "http://localhost:8188"

# Band sizes from 28 to 48
BAND_SIZES = [28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48]

# Cup sizes - small only
CUP_SIZES = ["AAA", "AA", "A", "B"]

# Generate all combinations
def get_all_bra_sizes():
    sizes = []
    for band in BAND_SIZES:
        for cup in CUP_SIZES:
            sizes.append(f"{band}{cup}")
    return sizes

BRA_SIZES = get_all_bra_sizes()

# Breast shape descriptors
BREAST_SHAPES = [
    "perky breasts", "puffy nipples", "pointed breasts",
    "upward pointing breasts", "outward pointing breasts",
    "round breasts", "firm breasts", "pert breasts",
    "small perky breasts", "tiny perky breasts",
    "long nipples", "puffy areolas", "pointed nipples"
]

# Body weights
BODY_WEIGHTS = [
    "70 pound body", "75 pound body", "80 pound body",
    "85 pound body", "90 pound body", "95 pound body",
    "very slim", "slender", "lean body", "thin frame"
]

# Athletic/toned descriptors
ATHLETIC = [
    "toned body", "muscle tone", "ripped abs", "ripped stomach",
    "six pack abs", "defined muscles", "athletic build",
    "toned stomach", "flat toned stomach", "muscular definition",
    "fit body", "lean muscles", "toned arms", "toned legs"
]

# Tribal elements
TRIBAL_STYLE = [
    "tribal woman", "tribal warrior", "indigenous woman",
    "amazon warrior", "tribal princess", "native woman"
]

TRIBAL_PAINT = [
    "tribal body paint", "ceremonial body paint", "war paint",
    "tribal face paint", "painted body", "decorative body paint",
    "white body paint patterns", "red body paint", "black tribal markings",
    "geometric body paint", "symbolic tribal paint"
]

TRIBAL_CLOTHING = [
    "tribal jewelry", "bone necklace", "feather headdress",
    "tribal beads", "leather straps", "see through cloth",
    "sheer fabric", "transparent tribal cloth", "minimal clothing",
    "tribal loincloth", "beaded top", "string bikini tribal style"
]

TRIBAL_SETTING = [
    "jungle background", "tribal village", "rainforest",
    "savanna", "desert tribe", "mountain tribe",
    "river bank", "ancient temple", "tribal fire"
]

# Quality tags
QUALITY = "(masterpiece:1.3), (best quality:1.3), (photorealistic:1.4), (8k:1.2), (detailed skin:1.2), (realistic:1.3), detailed face"

# Negative prompt
NEGATIVE = "deformed, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, floating limbs, disconnected limbs, malformed hands, blurry, watermark, text, huge breasts, massive breasts, gigantic breasts, oversized breasts, C cup, D cup, DD cup, large breasts, big breasts"

def build_prompt(bra_size, include_sheer=False):
    """Build a tribal woman prompt"""
    
    # Random selections
    weight = random.choice(BODY_WEIGHTS)
    athletic = random.sample(ATHLETIC, k=random.randint(2, 3))
    breast_shape = random.sample(BREAST_SHAPES, k=random.randint(1, 2))
    tribal = random.choice(TRIBAL_STYLE)
    paint = random.sample(TRIBAL_PAINT, k=random.randint(1, 2))
    setting = random.choice(TRIBAL_SETTING)
    
    # Clothing - sometimes sheer
    if include_sheer:
        clothing = random.sample([c for c in TRIBAL_CLOTHING if 'see through' in c or 'sheer' in c or 'transparent' in c], k=1)
    else:
        clothing = random.sample(TRIBAL_CLOTHING, k=random.randint(1, 2))
    
    # Age
    age = random.choice(["21yo", "22yo", "23yo", "24yo", "25yo", "26yo"])
    
    # Skin tones for tribal variety
    skin = random.choice([
        "dark skin", "brown skin", "tan skin", "bronze skin",
        "ebony skin", "caramel skin", "olive skin"
    ])
    
    prompt_parts = [
        QUALITY,
        f"({tribal}:1.3)",
        f"({age} woman:1.2)",
        f"({skin}:1.2)",
        f"({weight}:1.2)",
        f"({bra_size} cup breasts:1.4)",
        f"({', '.join(breast_shape)}:1.3)",
        f"({', '.join(athletic)}:1.3)",
        f"({', '.join(paint)}:1.2)",
        f"({', '.join(clothing)}:1.1)",
        setting,
        "natural lighting", "full body shot"
    ]
    
    return ", ".join(prompt_parts)

def queue_to_comfyui(prompt, negative, seed, filename):
    """Send prompt to ComfyUI"""
    workflow = {
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
                "height": 896,
                "width": 640
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
    
    try:
        r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=10)
        result = r.json()
        return 'prompt_id' in result
    except Exception as e:
        print(f"Error: {e}")
        return False

def generate_batch(count=400):
    """Generate batch of tribal women images"""
    print(f"\n{'='*60}")
    print(f"  GENERATING {count} TRIBAL WOMEN IMAGES")
    print(f"  Cup sizes: AAA, AA, A, B on bands 28-48")
    print(f"  Body: 70-95lb, toned, athletic")
    print(f"  Style: Body paint, face paint, tribal")
    print(f"{'='*60}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    queued = 0
    failed = 0
    
    for i in range(count):
        # Cycle through bra sizes
        bra_size = BRA_SIZES[i % len(BRA_SIZES)]
        
        # 30% chance of sheer clothing
        include_sheer = random.random() < 0.3
        
        prompt = build_prompt(bra_size, include_sheer)
        seed = random.randint(1, 2**31)
        
        # Create filename
        sheer_tag = "_sheer" if include_sheer else ""
        filename = f"tribal_{bra_size}{sheer_tag}_{timestamp}_{i+1:03d}"
        
        success = queue_to_comfyui(prompt, NEGATIVE, seed, filename)
        
        if success:
            queued += 1
            style = "sheer" if include_sheer else "tribal"
            print(f"[{i+1:03d}/{count}] ✓ {bra_size} - {style} (seed: {seed})")
        else:
            failed += 1
            print(f"[{i+1:03d}/{count}] ✗ Failed: {bra_size}")
        
        # Small delay every 10 images
        if i > 0 and i % 10 == 0:
            time.sleep(0.3)
    
    print(f"\n{'='*60}")
    print(f"  COMPLETE: {queued} queued, {failed} failed")
    print(f"  Images: G:\\Github\\ComfyUI\\output\\")
    print(f"{'='*60}\n")
    
    return queued

if __name__ == "__main__":
    import sys
    
    # Check ComfyUI
    try:
        r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        print("✓ ComfyUI is running")
    except:
        print("✗ ComfyUI not running! Start it first.")
        sys.exit(1)
    
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    generate_batch(count)
