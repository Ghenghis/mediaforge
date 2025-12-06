"""
Generate 200 images with perfectly round spherical breasts
Very petite tiny frames 80-135lb where 32AA looks huge
Extremely toned - stomach, legs, butt, muscles
Various nipple types
"""
import requests
import random
import time
from datetime import datetime

COMFYUI_URL = "http://localhost:8188"

# The PERFECT breast shape descriptors - spherical, no sag
PERFECT_BREASTS = [
    # Perfectly round/spherical emphasis
    "(perfectly round breasts:1.5)",
    "(spherical breasts:1.4)",
    "(circular breast shape:1.4)",
    "(ball shaped breasts:1.3)",
    "(perfectly symmetrical breasts:1.3)",
    # No sag/droop
    "(firm breasts:1.4)",
    "(perky breasts:1.4)",
    "(gravity defying breasts:1.3)",
    "(no sag:1.3)",
    # Shape
    "(round like spheres:1.3)",
    "(perfectly shaped:1.3)",
]

# Nipple varieties for user to choose favorites
NIPPLE_TYPES = [
    "small nipples",
    "puffy nipples", 
    "puffy areolas",
    "cone shaped nipples",
    "pointed nipples",
    "perky nipples",
    "raised nipples",
    "prominent nipples",
    "soft nipples",
    "pink nipples",
    "small areolas"
]

# Very petite tiny frames - 80 to 135lb
TINY_FRAMES = [
    "80 pound body", "85 pound body", "90 pound body",
    "95 pound body", "100 pound body", "105 pound body",
    "110 pound body", "115 pound body", "120 pound body",
    "125 pound body", "130 pound body", "135 pound body"
]

PETITE_DESCRIPTORS = [
    "extremely petite", "very tiny frame", "very small frame",
    "delicate frame", "miniature body", "very slim",
    "tiny body", "small build", "petite build", "compact frame"
]

# Extremely toned body
TONED_BODY = [
    # Stomach
    "(very toned stomach:1.4)", "(ripped abs:1.4)", "(six pack abs:1.3)",
    "(defined abs:1.3)", "(flat toned stomach:1.3)",
    # Legs
    "(toned legs:1.3)", "(muscular legs:1.3)", "(defined leg muscles:1.2)",
    # Butt
    "(very toned butt:1.3)", "(firm butt:1.3)", "(muscular glutes:1.2)",
    # Overall
    "(athletic build:1.3)", "(muscular definition:1.3)", "(fit body:1.3)",
    "(lean muscles:1.2)", "(toned arms:1.2)"
]

# Ages
AGES = ["21yo", "22yo", "23yo", "24yo", "25yo", "26yo", "27yo", "28yo"]

# Hair variety
HAIR = [
    "blonde hair", "brunette", "black hair", "red hair",
    "long hair", "short hair", "wavy hair", "straight hair"
]

# Eyes
EYES = ["blue eyes", "green eyes", "brown eyes", "hazel eyes"]

# Skin tones
SKIN = ["pale skin", "fair skin", "tan skin", "olive skin", "bronze skin"]

QUALITY = "(masterpiece:1.4), (best quality:1.4), (photorealistic:1.5), (8k:1.3), (ultra detailed:1.3), (detailed skin:1.4), beautiful face, detailed eyes, professional photography"

# Strong negative to prevent sag/bulge
NEGATIVE = "deformed, bad anatomy, disfigured, ugly, blurry, watermark, text, saggy breasts, droopy breasts, sagging, pendulous, deflated breasts, uneven breasts, asymmetrical breasts, side bulge, breast bulge, flat chest, large breasts, huge breasts, massive breasts, teardrop breasts, natural hang"

def build_prompt():
    """Build prompt for perfect round breasts on tiny frame"""
    age = random.choice(AGES)
    weight = random.choice(TINY_FRAMES)
    petite = random.choice(PETITE_DESCRIPTORS)
    
    # Perfect breast shape - use multiple descriptors
    breast_shape = random.sample(PERFECT_BREASTS, k=3)
    nipple = random.choice(NIPPLE_TYPES)
    
    # Toned body parts
    toned = random.sample(TONED_BODY, k=5)
    
    hair = random.sample(HAIR, k=2)
    eyes = random.choice(EYES)
    skin = random.choice(SKIN)
    
    parts = [
        QUALITY,
        f"({age} woman:1.3)",
        # Emphasize tiny frame with relatively larger looking breasts
        f"({petite}:1.4)",
        f"({weight}:1.3)",
        "(32AA cup breasts:1.3)",
        "(breasts look large on tiny frame:1.3)",
        # Perfect round shape
        ", ".join(breast_shape),
        f"({nipple}:1.2)",
        # Extremely toned
        ", ".join(toned),
        f"({', '.join(hair)}:1.1)",
        f"({eyes}:1.2)",
        f"({skin}:1.1)",
        "(sexy:1.2)", "(beautiful:1.2)",
        "full body shot", "studio lighting"
    ]
    return ", ".join(parts)

def queue_to_comfyui(prompt, negative, seed, filename):
    workflow = {
        "3": {"class_type": "KSampler", "inputs": {"cfg": 7.5, "denoise": 1, "latent_image": ["5", 0], "model": ["4", 0], "negative": ["7", 0], "positive": ["6", 0], "sampler_name": "euler_ancestral", "scheduler": "normal", "seed": seed, "steps": 35}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "CyberRealistic.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": 1024, "width": 680}},
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

def generate_batch(count=200):
    """Generate perfect round breasts on tiny frames"""
    print(f"\n{'='*60}")
    print(f"  GENERATING {count} PERFECT ROUND BREAST IMAGES")
    print(f"  Frame: 80-135lb very petite tiny")
    print(f"  Breasts: Perfectly round, spherical, no sag")
    print(f"  Body: Extremely toned stomach, legs, butt")
    print(f"  Nipples: Various types (puffy, cone, etc)")
    print(f"  32AA looking huge on tiny frames")
    print(f"{'='*60}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    queued = 0
    
    for i in range(count):
        prompt = build_prompt()
        seed = random.randint(1, 2**31)
        filename = f"perfect_round_{timestamp}_{i+1:03d}"
        
        if queue_to_comfyui(prompt, NEGATIVE, seed, filename):
            queued += 1
            if (i + 1) % 10 == 0:
                print(f"[{i+1:03d}/{count}] ✓ Queued {queued}...")
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
    
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    generate_batch(count)
