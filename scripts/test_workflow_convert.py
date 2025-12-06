"""Quick test for workflow conversion"""
import json
import requests

# Load workflow
with open(r'G:\Github\ComfyUI\user\default\workflows\01_Pony_SDXL.json') as f:
    data = json.load(f)

# Build link map
link_map = {}
for link in data.get('links', []):
    link_id, from_node, from_slot, to_node, to_slot = link[:5]
    link_map[link_id] = (from_node, from_slot)

api_wf = {}
for node in data['nodes']:
    node_id = str(node['id'])
    class_type = node.get('type')
    if not class_type:
        continue
    
    inputs = {}
    widgets = node.get('widgets_values', [])
    
    # Node-specific handling
    if class_type == 'CheckpointLoaderSimple' and widgets:
        inputs['ckpt_name'] = widgets[0]
    elif class_type == 'CLIPTextEncode' and widgets:
        inputs['text'] = widgets[0]
    elif class_type == 'EmptyLatentImage' and len(widgets) >= 3:
        inputs['width'] = widgets[0]
        inputs['height'] = widgets[1]
        inputs['batch_size'] = widgets[2]
    elif class_type == 'KSampler' and len(widgets) >= 6:
        inputs['seed'] = widgets[0]
        inputs['control_after_generate'] = widgets[1]
        inputs['steps'] = widgets[2]
        inputs['cfg'] = widgets[3]
        inputs['sampler_name'] = widgets[4]
        inputs['scheduler'] = widgets[5]
        inputs['denoise'] = widgets[6] if len(widgets) > 6 else 1.0
    elif class_type == 'SaveImage' and widgets:
        inputs['filename_prefix'] = widgets[0]
    elif class_type == 'VAEDecode':
        pass  # VAEDecode has no widget values, only connections
    
    # Add connections
    for inp in node.get('inputs', []):
        link_id = inp.get('link')
        if link_id and link_id in link_map:
            from_node, from_slot = link_map[link_id]
            inputs[inp['name']] = [str(from_node), from_slot]
    
    api_wf[node_id] = {'class_type': class_type, 'inputs': inputs}

print("Converted workflow:")
for nid, node in api_wf.items():
    print(f"  [{nid}] {node['class_type']}: {list(node['inputs'].keys())}")

# Try to queue
print("\nQueuing to ComfyUI...")
try:
    r = requests.post('http://127.0.0.1:8188/prompt', json={'prompt': api_wf}, timeout=10)
    print(f'Status: {r.status_code}')
    resp = r.json()
    if 'prompt_id' in resp:
        print(f'SUCCESS! Prompt ID: {resp["prompt_id"]}')
    elif 'error' in resp:
        print(f'ERROR: {resp["error"]}')
        if 'node_errors' in resp:
            for node_id, errors in resp['node_errors'].items():
                print(f'  Node {node_id}: {errors}')
    else:
        print(f'Response: {json.dumps(resp, indent=2)[:500]}')
except Exception as e:
    print(f'Error: {e}')
