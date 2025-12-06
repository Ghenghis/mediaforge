"""
WD14 Tagger Test via ComfyUI API
Tests the auto-tagging functionality
"""
import json
import urllib.request
import time

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

def get_available_images():
    """List available input images"""
    resp = urllib.request.urlopen(f"{COMFY_URL}/object_info/LoadImage")
    data = json.loads(resp.read())
    images = data['LoadImage']['input']['required']['image'][0]
    return images

def test_wd14_tagger():
    """Test WD14 tagger with an image"""
    print("\n" + "="*60)
    print("  TESTING WD14 AUTO-TAGGER")
    print("="*60)
    
    # Check available images
    images = get_available_images()
    print(f"\n📷 Available images: {len(images)}")
    for img in images[:5]:
        print(f"   - {img}")
    
    if not images:
        print("❌ No images in input folder!")
        print("   Copy images to: G:\\Github\\ComfyUI\\input\\")
        return False
    
    # Use test_image if available, otherwise first image
    test_img = "test_image.png" if "test_image.png" in images else images[0]
    print(f"\n🎯 Testing with: {test_img}")
    
    # WD14 Tagger workflow
    prompt = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": test_img}
        },
        "2": {
            "class_type": "WD14Tagger|pysssss",
            "inputs": {
                "image": ["1", 0],
                "model": "wd-v1-4-moat-tagger-v2",
                "threshold": 0.35,
                "character_threshold": 0.85,
                "exclude_tags": "",
                "replace_underscore": True,
                "trailing_comma": False,
                "use_escape": False
            }
        }
    }
    
    print("\n⏳ Queueing WD14 tagging...")
    print("   (First run downloads ~400MB model)")
    
    try:
        result = queue_prompt(prompt)
        prompt_id = result['prompt_id']
        print(f"   Prompt ID: {prompt_id}")
        
        # Wait for completion (longer for first run with model download)
        print("⏳ Waiting for tagging...")
        for i in range(90):  # Max 3 minutes for model download
            time.sleep(2)
            history = get_history(prompt_id)
            if prompt_id in history:
                outputs = history[prompt_id].get('outputs', {})
                if '2' in outputs:
                    tags_data = outputs['2']
                    if 'tags' in tags_data:
                        tags = tags_data['tags'][0]  # Get the string output
                        print(f"\n✅ Tagging complete!")
                        print(f"\n📝 Generated Tags:")
                        print("-" * 40)
                        # Split and display nicely
                        tag_list = tags.split(", ")
                        for j in range(0, len(tag_list), 5):
                            print(", ".join(tag_list[j:j+5]))
                        print("-" * 40)
                        print(f"Total tags: {len(tag_list)}")
                        return True
            
            if i % 5 == 0:
                print(f"   ... waiting ({i*2}s)")
        
        print("❌ Timeout waiting for tagging")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("  WD14 TAGGER TEST")
    print("="*60)
    
    # Check ComfyUI
    try:
        resp = urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        print("✅ ComfyUI is running")
    except:
        print("❌ ComfyUI not running! Start it first.")
        return
    
    test_wd14_tagger()
    
    print("\n" + "="*60)
    print("  TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
