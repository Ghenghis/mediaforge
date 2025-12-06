"""
Generate 300 images with different cup sizes on petite frame
Sends to ComfyUI for generation
"""
import requests
import random
import time
import json
from datetime import datetime

COMFYUI_URL = "http://localhost:8188"

# Cup sizes to cycle through - AAA, AA, and A cups
CUP_SIZES = [
    # AAA - smallest
    "AAA cup", "AAA breasts", "AAA tiny breasts", "flat AAA chest",
    # AA - very small
    "AA cup", "AA breasts", "AA small breasts", "tiny AA cup",
    # A cup band sizes
    "26A cup", "26A breasts", "26A small breasts",
    "28A cup", "28A breasts", "28A small breasts", 
    "30A cup", "30A breasts", "30A small breasts",
    "32A cup", "32A breasts", "32A small breasts",
    "34A cup", "34A breasts", "34A small breasts",
    "36A cup", "36A breasts", "36A small breasts",
    # Descriptive for variety
    "tiny A cup", "small A cup breasts", "petite A cup",
    "flat chest", "nearly flat chest", "very small breasts"
]

# Body frame descriptors for 85lb petite
BODY_FRAMES = [
    "petite frame", "85 pound body", "very slim", "slender build",
    "tiny frame", "small body", "delicate figure", "skinny",
    "lightweight build", "thin waist", "narrow hips"
]

# Quality tags
QUALITY = "(masterpiece:1.3), (best quality:1.3), (photorealistic:1.4), (8k:1.2), (detailed skin:1.2), (realistic:1.3)"

# Negative prompt
NEGATIVE = "deformed, bad anatomy, disfigured, poorly drawn face, mutation, mutated, extra limb, ugly, poorly drawn hands, missing limb, floating limbs, disconnected limbs, malformed hands, blurry, watermark, text, oversized breasts, huge breasts, massive breasts, gigantic, inflated"

def build_prompt(cup_size, body_frame):
    """Build a prompt with specific cup size"""
    # Base woman description
    age = random.choice(["21yo", "22yo", "23yo", "24yo", "25yo"])
    
    # Additional features
    eyes = random.choice(["blue eyes", "green eyes", "brown eyes", "hazel eyes"])
    hair = random.choice(["blonde hair", "brown hair", "black hair", "red hair", "auburn hair"])
    skin = random.choice(["pale skin", "fair skin", "light skin", "porcelain skin"])
    
    # Pose/setting
    pose = random.choice([
        "standing", "sitting", "portrait", "upper body shot", 
        "three quarter view", "front view", "soft lighting"
    ])
    
    prompt_parts = [
        QUALITY,
        f"({age} woman:1.3)",
        f"({body_frame}:1.3)",
        f"({cup_size}:1.4)",
        f"({eyes}:1.1)",
        f"({hair}:1.1)", 
        f"({skin}:1.1)",
        pose,
        "natural lighting", "detailed face", "beautiful"
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
                "ckpt_name": "CyberRealistic.safetensors"  # Change to your model
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
    
    try:
        r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=10)
        result = r.json()
        return 'prompt_id' in result, result.get('prompt_id', '')
    except Exception as e:
        print(f"Error: {e}")
        return False, ""

def generate_batch(count=300):
    """Generate batch of images"""
    print(f"\n{'='*60}")
    print(f"  GENERATING {count} IMAGES - CUP SIZE VARIATIONS")
    print(f"{'='*60}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    queued = 0
    failed = 0
    
    for i in range(count):
        # Cycle through cup sizes
        cup_size = CUP_SIZES[i % len(CUP_SIZES)]
        body_frame = random.choice(BODY_FRAMES)
        
        prompt = build_prompt(cup_size, body_frame)
        seed = random.randint(1, 2**31)
        
        # Create descriptive filename
        cup_clean = cup_size.replace(" ", "_").replace("(", "").replace(")", "")
        filename = f"petite_{cup_clean}_{timestamp}_{i+1:03d}"
        
        success, prompt_id = queue_to_comfyui(prompt, NEGATIVE, seed, filename)
        
        if success:
            queued += 1
            print(f"[{i+1:03d}/{count}] ✓ Queued: {cup_size} (seed: {seed})")
        else:
            failed += 1
            print(f"[{i+1:03d}/{count}] ✗ Failed: {cup_size}")
        
        # Small delay to not overwhelm ComfyUI
        if i > 0 and i % 10 == 0:
            time.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"  COMPLETE: {queued} queued, {failed} failed")
    print(f"  Images will appear in: ComfyUI/output/")
    print(f"{'='*60}\n")
    
    return queued

if __name__ == "__main__":
    import sys
    
    # Check ComfyUI is running
    try:
        r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
        print("✓ ComfyUI is running")
    except:
        print("✗ ComfyUI is not running! Start it first.")
        print("  cd G:\\Github\\ComfyUI && python main.py")
        sys.exit(1)
    
    # Get count from args or use default
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    
    print(f"\nQueuing {count} images to ComfyUI...")
    print("Cup sizes: 26A, 28A, 30A, 32A, 34A, 36A")
    print("Body: 85lb petite frame variations")
    
    # Start immediately
    generate_batch(count)
