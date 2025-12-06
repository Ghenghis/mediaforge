"""
MASTER IMAGE GENERATOR - RELIABLE & PHOTOREALISTIC
Fixed version with proper error handling and realistic output
"""
import requests
import random
import time
import json
import sys
from datetime import datetime
from pathlib import Path

COMFYUI_URL = "http://localhost:8188"

# Best models for photorealistic output
REALISTIC_MODELS = [
    "RealisticVisionV5.safetensors",  # Best for photorealism
    "CyberRealistic.safetensors",      # Good alternative
]

class ImageGenerator:
    def __init__(self):
        self.model = None
        self.check_comfyui()
        self.select_model()
        
    def check_comfyui(self):
        """Verify ComfyUI is running"""
        try:
            r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=10)
            if r.status_code == 200:
                print("[OK] ComfyUI is running")
                return True
        except Exception as e:
            print(f"[ERROR] ComfyUI not responding: {e}")
            print("Start ComfyUI first: cd G:\\Github\\ComfyUI && python main.py")
            sys.exit(1)
            
    def select_model(self):
        """Select best available model"""
        try:
            r = requests.get(f"{COMFYUI_URL}/object_info/CheckpointLoaderSimple", timeout=10)
            available = r.json()['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]
            
            for model in REALISTIC_MODELS:
                if model in available:
                    self.model = model
                    print(f"[OK] Using model: {model}")
                    return
            
            # Fallback to first available
            self.model = available[0]
            print(f"[OK] Using model: {self.model}")
        except:
            self.model = "RealisticVisionV5.safetensors"
            print(f"[OK] Using model: {self.model}")
    
    def build_realistic_workflow(self, prompt, negative, seed, filename):
        """Build workflow optimized for photorealistic output"""
        return {
            # KSampler - optimized for realism
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                    "seed": seed,
                    "control_after_generate": "randomize",
                    "steps": 30,           # Good quality
                    "cfg": 7.0,            # Not too high to avoid artifacts
                    "sampler_name": "dpmpp_2m",  # Better for realism
                    "scheduler": "karras",      # Smoother results
                    "denoise": 1.0
                }
            },
            # Model loader
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": self.model
                }
            },
            # Latent image - good resolution
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 512,
                    "height": 768,
                    "batch_size": 1
                }
            },
            # Positive prompt
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": prompt
                }
            },
            # Negative prompt
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": negative
                }
            },
            # VAE Decode
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                }
            },
            # Save Image
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["8", 0],
                    "filename_prefix": filename
                }
            }
        }
    
    def queue_image(self, prompt, negative, seed, filename):
        """Queue single image and wait for confirmation"""
        workflow = self.build_realistic_workflow(prompt, negative, seed, filename)
        
        try:
            r = requests.post(
                f"{COMFYUI_URL}/prompt",
                json={"prompt": workflow},
                timeout=30
            )
            result = r.json()
            
            if 'prompt_id' in result:
                return True, result['prompt_id']
            elif 'error' in result:
                print(f"    [ERROR] {result['error']}")
                return False, None
            else:
                return False, None
                
        except requests.exceptions.Timeout:
            print("    [ERROR] Request timeout")
            return False, None
        except Exception as e:
            print(f"    [ERROR] {e}")
            return False, None
    
    def get_queue_status(self):
        """Check how many items in queue"""
        try:
            r = requests.get(f"{COMFYUI_URL}/queue", timeout=10)
            data = r.json()
            running = len(data.get('queue_running', []))
            pending = len(data.get('queue_pending', []))
            return running, pending
        except:
            return 0, 0


# =============================================================
# PRESET GENERATORS
# =============================================================

def realistic_prompt(base_desc, extra_features=""):
    """Build photorealistic prompt"""
    quality = "professional photo, masterpiece, best quality, photorealistic, ultra realistic, 8k uhd, dslr, natural skin texture, detailed skin pores, sharp focus, natural lighting"
    return f"{quality}, {base_desc}, {extra_features}, beautiful, detailed face, detailed eyes"

def realistic_negative():
    """Negative prompt to avoid fake/game look"""
    return "cartoon, anime, illustration, painting, drawing, cgi, 3d render, game, fake, plastic skin, airbrushed, smooth skin, doll, mannequin, deformed, bad anatomy, ugly, blurry, watermark, text, oversaturated"


def generate_breast_sizes(generator, count_per_size=5):
    """Generate all breast sizes - FIXED VERSION"""
    
    # Complete size list
    bands = [28, 30, 32, 34, 36, 38, 40]
    cups = ["AA", "A", "B", "C", "D", "DD"]
    
    sizes = []
    for band in bands:
        for cup in cups:
            sizes.append(f"{band}{cup}")
    
    total = len(sizes) * count_per_size
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    print(f"\n{'='*60}")
    print(f"  BREAST SIZE DATABASE - PHOTOREALISTIC")
    print(f"  {len(sizes)} sizes × {count_per_size} each = {total} images")
    print(f"  Model: {generator.model}")
    print(f"{'='*60}\n")
    
    queued = 0
    current = 0
    
    for size in sizes:
        print(f"\n[{size}]")
        
        for i in range(count_per_size):
            current += 1
            
            # Randomize features
            age = random.randint(18, 27)
            weight = random.randint(95, 125)
            hair = random.choice(["blonde", "brunette", "black hair", "red hair"])
            eyes = random.choice(["blue eyes", "green eyes", "brown eyes"])
            skin = random.choice(["fair skin", "tan skin", "olive skin"])
            
            desc = f"{age} year old woman, {size} cup breasts, {weight}lb toned body, {hair}, {eyes}, {skin}, full body shot, standing"
            
            prompt = realistic_prompt(desc, "sexy, beautiful figure, toned stomach")
            negative = realistic_negative()
            seed = random.randint(1, 2**31)
            filename = f"size_{size}_{timestamp}_{i+1:02d}"
            
            success, pid = generator.queue_image(prompt, negative, seed, filename)
            
            if success:
                queued += 1
                print(f"  [{current}/{total}] ✓ #{i+1} queued")
            else:
                print(f"  [{current}/{total}] ✗ #{i+1} FAILED")
            
            # Pace ourselves
            time.sleep(0.2)
            
            # Check queue every 20 images
            if current % 20 == 0:
                running, pending = generator.get_queue_status()
                if pending > 50:
                    print(f"  [WAIT] Queue has {pending} pending, waiting...")
                    time.sleep(5)
    
    print(f"\n{'='*60}")
    print(f"  COMPLETE: {queued}/{total} queued successfully")
    print(f"  Output: G:\\Github\\ComfyUI\\output\\")
    print(f"{'='*60}\n")


def generate_custom(generator, description, count=10, prefix="custom"):
    """Generate custom images"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    print(f"\n{'='*60}")
    print(f"  CUSTOM GENERATION: {count} images")
    print(f"  Description: {description[:50]}...")
    print(f"{'='*60}\n")
    
    queued = 0
    
    for i in range(count):
        prompt = realistic_prompt(description)
        negative = realistic_negative()
        seed = random.randint(1, 2**31)
        filename = f"{prefix}_{timestamp}_{i+1:03d}"
        
        success, _ = generator.queue_image(prompt, negative, seed, filename)
        
        if success:
            queued += 1
            print(f"[{i+1}/{count}] ✓ Queued (seed: {seed})")
        else:
            print(f"[{i+1}/{count}] ✗ Failed")
        
        time.sleep(0.2)
    
    print(f"\n  Complete: {queued}/{count} queued")


# =============================================================
# MAIN MENU
# =============================================================

def main():
    print("\n" + "="*60)
    print("  MASTER IMAGE GENERATOR - PHOTOREALISTIC")
    print("="*60 + "\n")
    
    gen = ImageGenerator()
    
    print("\nOptions:")
    print("  1. Generate ALL breast sizes (comprehensive database)")
    print("  2. Generate specific size (e.g., 32AA)")
    print("  3. Custom description")
    print("  4. Quick test (5 images)")
    print("  0. Exit")
    
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        count = input("Images per size (default 5): ").strip() or "5"
        generate_breast_sizes(gen, int(count))
        
    elif choice == "2":
        size = input("Size (e.g., 32AA, 34B, 36D): ").strip().upper()
        count = int(input("How many images: ").strip() or "10")
        desc = f"woman with {size} cup breasts, toned body, beautiful, sexy"
        generate_custom(gen, desc, count, f"size_{size}")
        
    elif choice == "3":
        desc = input("Description: ").strip()
        count = int(input("How many images: ").strip() or "10")
        prefix = input("Filename prefix: ").strip() or "custom"
        generate_custom(gen, desc, count, prefix)
        
    elif choice == "4":
        desc = "beautiful 22 year old woman, 32B breasts, toned athletic body, blonde hair, blue eyes, full body"
        generate_custom(gen, desc, 5, "test")
        
    elif choice == "0":
        print("Exiting.")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        gen = ImageGenerator()
        if sys.argv[1] == "sizes":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            generate_breast_sizes(gen, count)
        elif sys.argv[1] == "test":
            desc = "beautiful 22yo woman, 32AA breasts, petite toned body, blonde, blue eyes"
            generate_custom(gen, desc, 5, "test")
    else:
        main()
