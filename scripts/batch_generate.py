"""
Batch Generation Script
Generates images using prompts from user's database via ComfyUI API
"""
import json
import random
import time
import urllib.request
from pathlib import Path

COMFY_URL = "http://localhost:8188"
PROMPTS_FILE = Path(r"c:\Users\Admin\civitai\data\user_prompts.json")
TEMPLATES_FILE = Path(r"c:\Users\Admin\civitai\data\style_templates.json")

# Available models
MODELS = {
    'tribal': 'CyberRealistic.safetensors',
    'anime': 'NoobAI-XL-v1.0.safetensors',
    'realistic': 'CyberRealistic.safetensors',
    'general': 'ponyDiffusionV6XL_v6.safetensors'
}

# Resolution presets
RESOLUTIONS = {
    'tribal': (512, 768),      # Portrait
    'anime': (1024, 1024),     # Square SDXL
    'realistic': (512, 768),   # Portrait
    'general': (832, 1216)     # Tall SDXL
}

def check_comfy():
    """Check if ComfyUI is running"""
    try:
        resp = urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        return True
    except:
        return False

def load_prompts():
    """Load prompts from JSON file"""
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_templates():
    """Load style templates"""
    with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_workflow(prompt_data, style='general'):
    """Create a ComfyUI API workflow from prompt data"""
    model = MODELS.get(style, MODELS['general'])
    width, height = RESOLUTIONS.get(style, RESOLUTIONS['general'])
    
    # Extract prompt parts
    positive = prompt_data.get('positive', 'masterpiece, best quality, 1girl')
    negative = prompt_data.get('negative', 'low quality, worst quality, bad anatomy')
    
    # Get settings if available
    settings = prompt_data.get('settings', {})
    steps = int(settings.get('steps', 25))
    cfg = float(settings.get('cfg', 7))
    sampler = settings.get('sampler', 'euler_ancestral')
    
    # Map samplers to ComfyUI names
    sampler_map = {
        'DPM++ 2M': 'dpmpp_2m',
        'DPM++ 2M Karras': 'dpmpp_2m',
        'DPM++ SDE': 'dpmpp_sde',
        'DPM++ SDE Karras': 'dpmpp_sde',
        'Euler a': 'euler_ancestral',
        'Euler': 'euler',
    }
    sampler_name = sampler_map.get(sampler, 'euler_ancestral')
    
    # Create API workflow (not graph workflow)
    workflow = {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": model}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1}
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
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
                "seed": random.randint(0, 2**32),
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": f"batch_{style}"}
        }
    }
    
    return workflow

def queue_prompt(workflow):
    """Queue a prompt via ComfyUI API"""
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
        print(f"Error queuing prompt: {e}")
        return None

def wait_for_completion(prompt_id, timeout=300):
    """Wait for a prompt to complete"""
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
    print("  BATCH GENERATION FROM USER DATABASE")
    print("="*60)
    
    if not check_comfy():
        print("\n❌ ComfyUI is not running!")
        print("   Start ComfyUI first: G:\\Github\\ComfyUI\\start_comfyui.bat")
        return
    
    print("\n✅ ComfyUI is running")
    
    # Load data
    prompts = load_prompts()
    templates = load_templates()
    
    print(f"\n📊 Loaded {len(prompts)} prompts")
    print(f"   Styles: {', '.join(templates.keys())}")
    
    # Select prompts to generate
    styles_to_generate = ['tribal', 'anime', 'realistic']
    prompts_per_style = 2
    
    print(f"\n🎯 Generating {prompts_per_style} images per style")
    
    generated = 0
    for style in styles_to_generate:
        if style not in templates:
            continue
            
        print(f"\n📁 Style: {style.upper()}")
        
        # Get sample prompts for this style
        sample_prompts = templates[style].get('sample_prompts', [])
        
        for i in range(min(prompts_per_style, len(sample_prompts))):
            prompt_text = sample_prompts[i]
            
            # Create prompt data
            prompt_data = {
                'positive': prompt_text,
                'negative': ' '.join(templates[style].get('common_negative', [])[:15])
            }
            
            print(f"   [{i+1}] Generating...")
            
            workflow = create_workflow(prompt_data, style)
            prompt_id = queue_prompt(workflow)
            
            if prompt_id:
                print(f"       Queued: {prompt_id[:8]}...")
                if wait_for_completion(prompt_id, timeout=120):
                    print(f"       ✅ Complete!")
                    generated += 1
                else:
                    print(f"       ⚠️ Timeout")
            else:
                print(f"       ❌ Failed to queue")
    
    print("\n" + "="*60)
    print(f"  BATCH COMPLETE: {generated} images generated")
    print("="*60)
    print(f"\n📁 Output: G:\\Github\\ComfyUI\\output\\")

if __name__ == "__main__":
    main()
