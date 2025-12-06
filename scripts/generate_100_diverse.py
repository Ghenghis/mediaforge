"""
Generate 100 Diverse High-Quality Images
Tests all variations: body types, sizes, poses, styles
"""
import json
import random
import time
import urllib.request
from pathlib import Path
from datetime import datetime

COMFY_URL = "http://localhost:8188"
CONFIG_PATH = Path(r"c:\Users\Admin\civitai\data\generation_config.json")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\preferences.db")

# Load config
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

# Diversity matrix - ensure all variations covered
BODY_FRAMES = ["petite", "small frame", "medium frame", "athletic build", "slim", "slender", "delicate"]
BUST_SIZES = ["flat chest", "AAA cup", "AA cup", "A cup", "B cup", "C cup"]
MUSCLE_LEVELS = ["soft", "toned", "defined muscles", "visible abs", "six pack", "ripped", "extremely toned"]
FACE_SHAPES = ["oval face", "round face", "heart shaped face", "angular face", "diamond face"]
SKIN_TONES = ["pale skin", "fair skin", "olive skin", "tan skin", "caramel skin", "brown skin", "dark skin", "ebony skin"]
EYE_TYPES = ["heterochromia", "blue eyes", "green eyes", "amber eyes", "violet eyes", "golden eyes"]
POSES = ["standing", "hands on hips", "arms crossed", "looking over shoulder", "profile view", "warrior stance"]
LIGHTING = ["dramatic lighting", "golden hour", "studio lighting", "firelight", "rim lighting"]

def build_diverse_prompt(index: int) -> tuple:
    """Build a unique prompt for each image"""
    
    # Rotate through all options to ensure diversity
    frame = BODY_FRAMES[index % len(BODY_FRAMES)]
    bust = BUST_SIZES[index % len(BUST_SIZES)]
    muscle = MUSCLE_LEVELS[index % len(MUSCLE_LEVELS)]
    face = FACE_SHAPES[index % len(FACE_SHAPES)]
    skin = SKIN_TONES[index % len(SKIN_TONES)]
    eyes = EYE_TYPES[index % len(EYE_TYPES)]
    pose = POSES[index % len(POSES)]
    light = LIGHTING[index % len(LIGHTING)]
    
    # Randomize some elements for variety
    hair_color = random.choice(CONFIG['hair_types']['color'])
    hair_style = random.choice(CONFIG['hair_types']['style'])
    face_paint = random.choice(CONFIG['tribal_specific']['face_paint'])
    body_paint = random.choice(CONFIG['tribal_specific']['body_paint'])
    accessory = random.choice(CONFIG['tribal_specific']['accessories'])
    
    age = random.choice(["21yo", "22yo", "23yo", "24yo", "25yo"])
    
    positive = f"""masterpiece, best quality, ultra detailed, 8k resolution, photorealistic, RAW photo, DSLR,
realistic lighting, high detail skin texture, sharp focus, professional photography,

(adult woman:1.3), ({age}:1.2), (tribal warrior woman:1.2),

({frame}:1.2), ({bust}:1.2), ({muscle}:1.3),
({face}:1.1), high cheekbones, defined jawline,
({eyes}:1.3), detailed iris, expressive eyes,
{hair_style}, {hair_color},
({skin}:1.1), realistic skin texture, skin pores, natural skin,

({face_paint}:1.4), detailed face paint patterns,
({body_paint}:1.3), tribal patterns on arms and torso,
({accessory}:1.2), tribal jewelry,

({pose}:1.1), facing viewer,
({light}:1.2),
forest background, nature setting"""

    negative = """EasyNegative, bad-hands-5, ng_deepnegative_v1_75t,
(child:2.0), (kid:2.0), (teen:2.0), (minor:2.0), (underage:2.0),
(bad anatomy:1.4), (bad proportions:1.4), (deformed:1.4),
(extra fingers:1.5), (missing fingers:1.5), (mutated hands:1.4),
(low quality:1.5), (worst quality:1.5), (blurry:1.3),
(watermark:1.5), (text:1.5),
(cartoon:1.5), (anime:1.5), (3d render:1.4),
ugly, disfigured"""

    tags = [frame, bust, muscle, face, skin, eyes, pose, light, face_paint, body_paint, "tribal"]
    
    return positive, negative, tags

def create_workflow(positive: str, negative: str, index: int) -> dict:
    seed = random.randint(0, 2**32)
    prefix = f"diverse_{index:03d}"
    
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "CyberRealistic.safetensors"}},
        "10": {"class_type": "LoraLoader", "inputs": {
            "model": ["4", 0], "clip": ["4", 1],
            "lora_name": "add_detail.safetensors", "strength_model": 0.7, "strength_clip": 0.7
        }},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 768, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["10", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0],
            "seed": seed, "steps": 35, "cfg": 7, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0
        }},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
        "_seed": seed, "_tags": None, "_prefix": prefix
    }

def queue_prompt(workflow: dict) -> str:
    data = json.dumps({"prompt": {k: v for k, v in workflow.items() if not k.startswith('_')}}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read()).get('prompt_id')
    except:
        return None

def wait_completion(prompt_id: str, timeout: int = 180) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            if prompt_id in json.loads(resp.read()):
                return True
        except:
            pass
        time.sleep(2)
    return False

def save_to_db(filename: str, prompt: str, negative: str, tags: list, seed: int):
    """Save image record to preferences database"""
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO images (filename, prompt, negative, tags, model, seed, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (filename, prompt, negative, json.dumps(tags), "CyberRealistic.safetensors", seed, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def main():
    print("="*70)
    print("  GENERATING 100 DIVERSE HIGH-QUALITY IMAGES")
    print("  All body types, sizes, poses, and styles")
    print("="*70)
    
    # Check ComfyUI
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        print("\n✅ ComfyUI connected")
    except:
        print("\n❌ ComfyUI not running!")
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    success = 0
    failed = 0
    
    print(f"\n📊 Diversity Coverage:")
    print(f"   Body frames: {len(BODY_FRAMES)}")
    print(f"   Bust sizes: {len(BUST_SIZES)}")
    print(f"   Muscle levels: {len(MUSCLE_LEVELS)}")
    print(f"   Face shapes: {len(FACE_SHAPES)}")
    print(f"   Skin tones: {len(SKIN_TONES)}")
    print(f"   Eye types: {len(EYE_TYPES)}")
    print(f"   Poses: {len(POSES)}")
    print(f"   Lighting: {len(LIGHTING)}")
    
    print(f"\n🎨 Starting generation of 100 images...\n")
    
    for i in range(100):
        print(f"[{i+1:03d}/100]", end=" ")
        
        # Build unique prompt
        positive, negative, tags = build_diverse_prompt(i)
        
        # Show key attributes
        frame = BODY_FRAMES[i % len(BODY_FRAMES)]
        bust = BUST_SIZES[i % len(BUST_SIZES)]
        muscle = MUSCLE_LEVELS[i % len(MUSCLE_LEVELS)]
        
        print(f"{frame[:8]:8s} | {bust[:8]:8s} | {muscle[:10]:10s}", end=" ")
        
        # Generate
        workflow = create_workflow(positive, negative, i+1)
        seed = workflow['_seed']
        prefix = workflow['_prefix']
        
        prompt_id = queue_prompt(workflow)
        
        if prompt_id:
            if wait_completion(prompt_id):
                filename = f"{prefix}_{seed}.png"
                save_to_db(filename, positive, negative, tags, seed)
                print("✅")
                success += 1
            else:
                print("⏱️ Timeout")
                failed += 1
        else:
            print("❌ Failed")
            failed += 1
            
        # Progress summary every 10
        if (i + 1) % 10 == 0:
            print(f"\n   Progress: {success} success, {failed} failed\n")
    
    print("\n" + "="*70)
    print("  100 IMAGE GENERATION COMPLETE!")
    print("="*70)
    print(f"\n📊 Results:")
    print(f"   ✅ Success: {success}")
    print(f"   ❌ Failed: {failed}")
    print(f"\n📁 Output: G:\\Github\\ComfyUI\\output\\diverse_*.png")
    print(f"\n🧠 All images saved to preferences database for learning!")

if __name__ == "__main__":
    main()
