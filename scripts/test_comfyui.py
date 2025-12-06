"""
ComfyUI API Test Script
Tests basic image generation via the ComfyUI API
"""
import json
import urllib.request
import urllib.parse
import time
from pathlib import Path

COMFY_URL = "http://localhost:8188"

def queue_prompt(prompt):
    """Queue a prompt for execution"""
    data = json.dumps({"prompt": prompt}).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, 
                                  headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def get_history(prompt_id):
    """Get execution history"""
    resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
    return json.loads(resp.read())

def check_comfy_running():
    """Check if ComfyUI is running"""
    try:
        resp = urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        data = json.loads(resp.read())
        print(f"✅ ComfyUI is running")
        print(f"   Version: {data['system']['comfyui_version']}")
        print(f"   PyTorch: {data['system']['pytorch_version']}")
        return True
    except Exception as e:
        print(f"❌ ComfyUI not available: {e}")
        return False

def get_available_checkpoints():
    """List available checkpoint models"""
    resp = urllib.request.urlopen(f"{COMFY_URL}/object_info/CheckpointLoaderSimple")
    data = json.loads(resp.read())
    checkpoints = data['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]
    return checkpoints

def test_simple_generation():
    """Test a simple image generation"""
    print("\n" + "="*60)
    print("  TESTING SIMPLE IMAGE GENERATION")
    print("="*60)
    
    # Get available models
    checkpoints = get_available_checkpoints()
    print(f"\n📦 Available checkpoints: {len(checkpoints)}")
    for ckpt in checkpoints[:5]:
        print(f"   - {ckpt}")
    
    if not checkpoints:
        print("❌ No checkpoints found!")
        return False
    
    # Use first available checkpoint
    checkpoint = checkpoints[0]
    print(f"\n🎯 Using: {checkpoint}")
    
    # Simple workflow
    prompt = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": 7,
                "denoise": 1,
                "latent_image": ["5", 0],
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": "euler",
                "scheduler": "normal",
                "seed": 42,
                "steps": 20
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"batch_size": 1, "height": 512, "width": 512}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": "a beautiful sunset over mountains, masterpiece, best quality"
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": "bad quality, blurry, ugly"
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "test_output", "images": ["8", 0]}
        }
    }
    
    print("\n⏳ Queueing generation...")
    try:
        result = queue_prompt(prompt)
        prompt_id = result['prompt_id']
        print(f"   Prompt ID: {prompt_id}")
        
        # Wait for completion
        print("⏳ Waiting for generation...")
        for i in range(60):  # Max 60 seconds
            time.sleep(2)
            history = get_history(prompt_id)
            if prompt_id in history:
                outputs = history[prompt_id].get('outputs', {})
                if '9' in outputs and 'images' in outputs['9']:
                    images = outputs['9']['images']
                    print(f"\n✅ Generation complete!")
                    print(f"   Output: {images[0]['filename']}")
                    return True
            print(f"   ... waiting ({i*2}s)")
        
        print("❌ Timeout waiting for generation")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("  COMFYUI API TEST")
    print("="*60)
    
    if not check_comfy_running():
        print("\nPlease start ComfyUI first:")
        print("  cd G:\\Github\\ComfyUI")
        print("  python main.py --listen 0.0.0.0 --port 8188")
        return
    
    test_simple_generation()
    
    print("\n" + "="*60)
    print("  TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
