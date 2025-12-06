"""
Smart Generation with Quality Control
Uses user preferences to generate and validate images
"""
import json
import random
import time
import urllib.request
from pathlib import Path

COMFY_URL = "http://localhost:8188"
PREFS_FILE = Path(r"c:\Users\Admin\civitai\data\user_preferences.json")

def load_preferences():
    """Load user preferences"""
    with open(PREFS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_prompt(prefs, style='tribal'):
    """Build prompt from preferences with proper weighting"""
    
    # Quality base
    quality = prefs['generation_boundaries']['always_include']
    quality_str = ', '.join(quality)
    
    # Age safety
    age = random.choice(prefs['body_standards']['age_range']['preferred'])
    
    # Body type
    body = random.choice(prefs['body_standards']['body_type']['preferred'])
    
    # Breast size
    breast = random.choice(prefs['body_standards']['breast_size']['preferred'])
    
    # Face type
    face = random.choice(prefs['body_standards']['face_type']['preferred'])
    face_feature = random.choice(prefs['body_standards']['face_type']['features'])
    
    # Skin tone
    skin_base = random.choice(prefs['body_standards']['skin_tone']['preferred'])
    skin_tone = random.choice(prefs['body_standards']['skin_tone']['tones'])
    
    if style == 'tribal':
        # Tribal specifics
        face_paint = random.choice(prefs['tribal_specific']['paint_types']['face_paint'])
        body_paint = random.choice(prefs['tribal_specific']['paint_types']['body_paint'])
        paint_color = random.choice(prefs['tribal_specific']['paint_types']['colors'])
        accessory = random.choice(prefs['tribal_specific']['accessories'])
        theme = random.choice(prefs['tribal_specific']['themes'])
        
        prompt = f"""masterpiece, best quality, 8k, photorealistic, RAW photo,
(adult woman:1.3), ({age}:1.2),
({theme} tribal woman:1.2), fierce expression,
({face_paint}:1.3), ({body_paint}:1.2),
{paint_color}, geometric patterns,
({breast}:1.1), ({body}:1.1),
({face}:1.2), {face_feature},
({skin_base}:1.2), ({skin_tone}:1.0),
{accessory}, tribal jewelry,
standing, medium shot, facing viewer,
dramatic lighting, sharp focus, DSLR"""
    else:
        prompt = f"""{quality_str},
(adult woman:1.3), ({age}:1.2),
({breast}:1.1), ({body}:1.1),
({face}:1.2), {face_feature},
({skin_base}:1.2), ({skin_tone}:1.0),
looking at viewer, detailed eyes,
soft lighting, sharp focus"""
    
    return prompt

def build_negative(prefs):
    """Build comprehensive negative prompt"""
    
    # Always exclude
    always_exclude = prefs['generation_boundaries']['always_exclude']
    
    # Body exclusions
    body_exclude = prefs['body_standards']['body_type']['excluded']
    
    # Anatomy standards
    anatomy_exclude = prefs['quality_standards']['anatomy_standards']['excluded']
    
    # Style exclusions
    style_exclude = prefs['quality_standards']['style_standards']['excluded']
    
    # Age protection (weighted heavily)
    age_exclude = prefs['quality_standards']['content_boundaries']['excluded_ages']
    age_str = ', '.join([f'({a}:2.0)' for a in age_exclude])
    
    # Body type exclusions (weighted)
    body_str = ', '.join([f'({b}:1.5)' for b in body_exclude])
    
    negative = f"""EasyNegative, bad-hands-5, ng_deepnegative_v1_75t,
{age_str},
{body_str},
({', '.join(anatomy_exclude)}:1.4),
({', '.join(style_exclude)}:1.4),
({', '.join(always_exclude)}:1.3),
ugly, disfigured, deformed, tan lines"""
    
    return negative

def create_workflow(positive, negative, model='CyberRealistic.safetensors'):
    """Create ComfyUI API workflow"""
    return {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": model}
        },
        "10": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["4", 0],
                "clip": ["4", 1],
                "lora_name": "add_detail.safetensors",
                "strength_model": 0.6,
                "strength_clip": 0.6
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 512, "height": 768, "batch_size": 1}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive, "clip": ["4", 1]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]}
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["10", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
                "seed": random.randint(0, 2**32),
                "steps": 35,
                "cfg": 7,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1.0
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": "smart_tribal"}
        }
    }

def queue_prompt(workflow):
    """Queue prompt via API"""
    data = json.dumps({"prompt": workflow}).encode('utf-8')
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        return result.get('prompt_id')
    except Exception as e:
        print(f"Error: {e}")
        return None

def wait_for_completion(prompt_id, timeout=120):
    """Wait for generation to complete"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            history = json.loads(resp.read())
            if prompt_id in history:
                return True
        except:
            pass
        time.sleep(2)
    return False

def main():
    print("="*60)
    print("  SMART GENERATION WITH QUALITY CONTROL")
    print("="*60)
    
    # Check ComfyUI
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        print("✅ ComfyUI connected")
    except:
        print("❌ ComfyUI not running!")
        return
    
    # Load preferences
    prefs = load_preferences()
    print("✅ Preferences loaded")
    
    # Show what's being used
    print("\n📋 QUALITY CONTROLS ACTIVE:")
    print(f"   Age: {prefs['body_standards']['age_range']['preferred']}")
    print(f"   Body: {prefs['body_standards']['body_type']['preferred']}")
    print(f"   Breast: {prefs['body_standards']['breast_size']['preferred']}")
    print(f"   Face: {prefs['body_standards']['face_type']['preferred']}")
    
    print("\n🚫 EXCLUSIONS ACTIVE:")
    print(f"   Ages: {prefs['quality_standards']['content_boundaries']['excluded_ages']}")
    print(f"   Body: {prefs['body_standards']['body_type']['excluded']}")
    
    # Generate
    num_images = 3
    print(f"\n🎨 Generating {num_images} quality-controlled tribal images...")
    
    for i in range(num_images):
        print(f"\n[{i+1}/{num_images}] Building prompt from preferences...")
        
        positive = build_prompt(prefs, style='tribal')
        negative = build_negative(prefs)
        
        print(f"   Positive: {positive[:100]}...")
        print(f"   Negative includes {len(negative.split(','))} exclusions")
        
        workflow = create_workflow(positive, negative)
        prompt_id = queue_prompt(workflow)
        
        if prompt_id:
            print(f"   Queued: {prompt_id[:8]}...")
            if wait_for_completion(prompt_id):
                print(f"   ✅ Generated!")
            else:
                print(f"   ⚠️ Timeout")
        else:
            print(f"   ❌ Failed")
    
    print("\n" + "="*60)
    print("  GENERATION COMPLETE")
    print("="*60)
    print("\n📁 Output: G:\\Github\\ComfyUI\\output\\smart_tribal_*.png")

if __name__ == "__main__":
    main()
