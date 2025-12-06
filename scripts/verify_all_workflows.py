"""
Verify All ComfyUI Workflows
Tests that all workflows load correctly and have valid structure
"""
import json
import urllib.request
from pathlib import Path

COMFY_URL = "http://localhost:8188"
WORKFLOW_DIR = Path(r"G:\Github\ComfyUI\user_workflows")

def check_comfy_running():
    """Check if ComfyUI is available"""
    try:
        resp = urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        return True
    except:
        return False

def get_available_models():
    """Get list of available models from ComfyUI"""
    try:
        resp = urllib.request.urlopen(f"{COMFY_URL}/object_info/CheckpointLoaderSimple")
        data = json.loads(resp.read())
        return data['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]
    except:
        return []

def get_available_loras():
    """Get list of available LoRAs"""
    try:
        resp = urllib.request.urlopen(f"{COMFY_URL}/object_info/LoraLoader")
        data = json.loads(resp.read())
        return data['LoraLoader']['input']['required']['lora_name'][0]
    except:
        return []

def validate_workflow(workflow_path: Path, checkpoints: list, loras: list):
    """Validate a workflow file"""
    issues = []
    
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except Exception as e:
        return [f"Read error: {e}"]
    
    # Check basic structure
    if 'nodes' not in workflow:
        issues.append("Missing 'nodes' key")
        return issues
    
    if 'links' not in workflow:
        issues.append("Missing 'links' key")
    
    nodes = workflow.get('nodes', [])
    
    # Check each node
    for node in nodes:
        node_type = node.get('class_type') or node.get('type', 'Unknown')
        widgets = node.get('widgets_values', [])
        
        # Check checkpoint references
        if 'CheckpointLoader' in node_type and widgets:
            ckpt = widgets[0] if widgets else None
            if ckpt and ckpt not in checkpoints:
                issues.append(f"Missing checkpoint: {ckpt}")
        
        # Check LoRA references
        if 'LoraLoader' in node_type and widgets:
            lora = widgets[0] if widgets else None
            if lora and lora not in loras:
                issues.append(f"Missing LoRA: {lora}")
    
    return issues

def main():
    print("="*60)
    print("  COMFYUI WORKFLOW VERIFICATION")
    print("="*60)
    
    if not check_comfy_running():
        print("\n❌ ComfyUI not running!")
        return
    
    print("\n✅ ComfyUI is running")
    
    # Get available models
    checkpoints = get_available_models()
    loras = get_available_loras()
    
    print(f"\n📦 Available Checkpoints: {len(checkpoints)}")
    for ckpt in checkpoints:
        print(f"   • {ckpt}")
    
    print(f"\n🎨 Available LoRAs: {len(loras)}")
    for lora in loras:
        print(f"   • {lora}")
    
    # Find workflows
    workflows = list(WORKFLOW_DIR.glob("*.json"))
    print(f"\n📋 Found {len(workflows)} workflows")
    
    # Validate each
    print("\n" + "-"*60)
    print("  VALIDATION RESULTS")
    print("-"*60)
    
    all_valid = True
    for wf in sorted(workflows):
        issues = validate_workflow(wf, checkpoints, loras)
        
        if issues:
            print(f"\n⚠️  {wf.name}")
            for issue in issues:
                print(f"   └─ {issue}")
            all_valid = False
        else:
            print(f"✅ {wf.name}")
    
    # Summary
    print("\n" + "="*60)
    if all_valid:
        print("  ✅ ALL WORKFLOWS VALID!")
    else:
        print("  ⚠️  Some workflows have issues (see above)")
    print("="*60)

if __name__ == "__main__":
    main()
