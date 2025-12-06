"""
Smart Collection Generator
Creates collections with style switching, uses preference learning
"""
import json
import random
import time
import urllib.request
from pathlib import Path
from datetime import datetime
from preference_system import PreferenceSystem

COMFY_URL = "http://localhost:8188"
CONFIG_PATH = Path(r"c:\Users\Admin\civitai\data\generation_config.json")
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")

class SmartGenerator:
    def __init__(self):
        self.pref_system = PreferenceSystem()
        self.load_config()
        self.models = {
            'primary': 'CyberRealistic.safetensors',
            'backup1': 'ponyDiffusionV6XL_v6.safetensors',
            'backup2': 'NoobAI-XL-v1.0.safetensors'
        }
        self.current_model = self.models['primary']
        
    def load_config(self):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
    # ==================== RANDOMIZED PROMPT BUILDING ====================
    
    def random_selection(self, category: str, subcategory: str = None) -> str:
        """Get random selection from config"""
        if subcategory:
            options = self.config.get(category, {}).get(subcategory, [])
        else:
            # Flatten all subcategories
            options = []
            for sub in self.config.get(category, {}).values():
                if isinstance(sub, list):
                    options.extend(sub)
        return random.choice(options) if options else ""
        
    def build_randomized_prompt(self, style: str = "tribal", custom_selections: dict = None) -> tuple:
        """Build prompt with randomization and preference weighting"""
        
        parts = []
        tags_used = []
        
        # Quality base
        quality = ["masterpiece", "best quality", "ultra detailed", "8k resolution", "photorealistic", "RAW photo"]
        parts.extend(quality)
        tags_used.extend(quality)
        
        # Age (always adult)
        age = random.choice(["21yo", "22yo", "23yo", "24yo", "25yo", "adult woman"])
        parts.append(f"({age}:1.2)")
        tags_used.append(age)
        
        # Use custom selections or randomize
        sel = custom_selections or {}
        
        # Body type
        body = sel.get('body_type') or self.random_selection('body_types', 'frame')
        parts.append(f"({body}:1.2)")
        tags_used.append(body)
        
        # Build
        build = sel.get('build') or self.random_selection('body_types', 'build')
        parts.append(f"({build}:1.2)")
        tags_used.append(build)
        
        # Muscle tone
        muscle = sel.get('muscle_tone') or self.random_selection('body_types', 'muscle_tone')
        parts.append(f"({muscle}:1.3)")
        tags_used.append(muscle)
        
        # Bust size
        bust = sel.get('bust_size') or random.choice(self.config['bust_sizes']['sizes'])
        parts.append(f"({bust}:1.2)")
        tags_used.append(bust)
        
        # Face
        face_shape = sel.get('face_shape') or self.random_selection('face_types', 'shape')
        parts.append(f"({face_shape}:1.1)")
        tags_used.append(face_shape)
        
        face_feat = self.random_selection('face_types', 'features')
        parts.append(face_feat)
        tags_used.append(face_feat)
        
        expression = sel.get('expression') or self.random_selection('face_types', 'expressions')
        parts.append(f"({expression}:1.1)")
        tags_used.append(expression)
        
        # Eyes
        eye_color = sel.get('eye_color') or self.random_selection('eye_types', 'color')
        if random.random() > 0.5:  # 50% chance heterochromia
            eye_color = "heterochromia, different colored eyes"
        parts.append(f"({eye_color}:1.3)")
        tags_used.append(eye_color)
        
        eye_detail = self.random_selection('eye_types', 'details')
        parts.append(eye_detail)
        tags_used.append(eye_detail)
        
        # Hair
        hair_length = self.random_selection('hair_types', 'length')
        hair_style = self.random_selection('hair_types', 'style')
        hair_color = sel.get('hair_color') or self.random_selection('hair_types', 'color')
        parts.extend([hair_length, hair_style, hair_color])
        tags_used.extend([hair_length, hair_style, hair_color])
        
        # Skin
        skin_tone = sel.get('skin_tone') or self.random_selection('skin_types', 'tone')
        skin_tex = self.random_selection('skin_types', 'texture')
        parts.append(f"({skin_tone}:1.1)")
        parts.append(skin_tex)
        tags_used.extend([skin_tone, skin_tex])
        
        # Style-specific additions
        if style == "tribal":
            face_paint = self.random_selection('tribal_specific', 'face_paint')
            body_paint = self.random_selection('tribal_specific', 'body_paint')
            paint_color = self.random_selection('tribal_specific', 'colors')
            accessory = self.random_selection('tribal_specific', 'accessories')
            
            parts.extend([
                f"({face_paint}:1.4)",
                f"({body_paint}:1.3)",
                paint_color,
                f"({accessory}:1.2)",
                "tribal warrior woman"
            ])
            tags_used.extend([face_paint, body_paint, paint_color, accessory, "tribal"])
            
        # Pose
        pose = sel.get('pose') or self.random_selection('poses', 'standing')
        angle = self.random_selection('poses', 'angles')
        parts.extend([f"({pose}:1.1)", angle])
        tags_used.extend([pose, angle])
        
        # Lighting
        lighting = sel.get('lighting') or self.random_selection('lighting', 'type')
        mood = self.random_selection('lighting', 'mood')
        parts.extend([f"({lighting}:1.2)", mood])
        tags_used.extend([lighting, mood])
        
        # Background
        bg = sel.get('background') or self.random_selection('backgrounds', 'nature')
        parts.append(bg)
        tags_used.append(bg)
        
        # Photography style
        photo_style = self.random_selection('styles', 'photography')
        parts.append(photo_style)
        tags_used.append(photo_style)
        
        # Add learned preferred tags
        preferred = self.pref_system.get_preferred_tags(limit=5)
        for tag, weight, _, _ in preferred:
            if weight > 0.7 and tag not in tags_used:
                parts.append(f"({tag}:{weight:.1f})")
                tags_used.append(tag)
                
        positive = ", ".join(parts)
        
        # Build negative
        negative = self.build_negative()
        
        return positive, negative, tags_used
        
    def build_negative(self) -> str:
        """Build comprehensive negative prompt"""
        negative_parts = [
            "EasyNegative", "bad-hands-5", "ng_deepnegative_v1_75t",
            "(child:2.0)", "(kid:2.0)", "(teen:2.0)", "(minor:2.0)", "(underage:2.0)",
            "(bad anatomy:1.4)", "(bad proportions:1.4)", "(deformed:1.4)",
            "(extra fingers:1.5)", "(missing fingers:1.5)", "(mutated hands:1.4)",
            "(low quality:1.5)", "(worst quality:1.5)", "(blurry:1.3)",
            "(watermark:1.5)", "(text:1.5)", "(signature:1.4)",
            "(cartoon:1.5)", "(anime:1.5)", "(3d render:1.4)",
            "ugly", "disfigured"
        ]
        
        # Add avoided tags from learning
        avoided = self.pref_system.get_avoided_tags(limit=10)
        for tag, weight, _, _ in avoided:
            negative_parts.append(f"({tag}:1.3)")
            
        return ", ".join(negative_parts)
        
    # ==================== GENERATION ====================
    
    def create_workflow(self, positive: str, negative: str, prefix: str) -> dict:
        """Create ComfyUI workflow"""
        return {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": self.current_model}
            },
            "10": {
                "class_type": "LoraLoader",
                "inputs": {
                    "model": ["4", 0],
                    "clip": ["4", 1],
                    "lora_name": "add_detail.safetensors",
                    "strength_model": 0.7,
                    "strength_clip": 0.7
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
                "inputs": {"images": ["8", 0], "filename_prefix": prefix}
            }
        }
        
    def queue_prompt(self, workflow: dict) -> str:
        """Queue prompt with error handling and model fallback"""
        data = json.dumps({"prompt": workflow}).encode('utf-8')
        req = urllib.request.Request(
            f"{COMFY_URL}/prompt",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            resp = urllib.request.urlopen(req)
            return json.loads(resp.read()).get('prompt_id')
        except Exception as e:
            print(f"   ⚠️ Error with {self.current_model}: {e}")
            # Try backup model
            return self._try_backup_model(workflow)
            
    def _try_backup_model(self, workflow: dict) -> str:
        """Try backup models on failure"""
        for backup_name, backup_model in self.models.items():
            if backup_model != self.current_model:
                print(f"   🔄 Trying backup: {backup_model}")
                self.current_model = backup_model
                workflow["4"]["inputs"]["ckpt_name"] = backup_model
                
                try:
                    data = json.dumps({"prompt": workflow}).encode('utf-8')
                    req = urllib.request.Request(
                        f"{COMFY_URL}/prompt",
                        data=data,
                        headers={'Content-Type': 'application/json'}
                    )
                    resp = urllib.request.urlopen(req)
                    return json.loads(resp.read()).get('prompt_id')
                except:
                    continue
        return None
        
    def wait_for_completion(self, prompt_id: str, timeout: int = 180) -> bool:
        """Wait for generation"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
                if prompt_id in json.loads(resp.read()):
                    return True
            except:
                pass
            time.sleep(2)
        return False
        
    # ==================== COLLECTION GENERATION ====================
    
    def generate_collection(self, 
                           collection_name: str,
                           style: str = "tribal",
                           count: int = 10,
                           custom_selections: dict = None):
        """Generate a collection of images"""
        
        print(f"\n{'='*60}")
        print(f"  GENERATING COLLECTION: {collection_name}")
        print(f"  Style: {style} | Count: {count}")
        print(f"{'='*60}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        prefix = f"{collection_name}_{timestamp}"
        
        for i in range(count):
            print(f"\n[{i+1}/{count}] Generating...")
            
            # Build randomized prompt
            positive, negative, tags = self.build_randomized_prompt(style, custom_selections)
            
            # Show key tags
            print(f"   Body: {tags[2] if len(tags) > 2 else 'N/A'}")
            print(f"   Bust: {tags[4] if len(tags) > 4 else 'N/A'}")
            print(f"   Muscle: {tags[3] if len(tags) > 3 else 'N/A'}")
            
            # Create and queue
            workflow = self.create_workflow(positive, negative, prefix)
            seed = workflow["3"]["inputs"]["seed"]
            prompt_id = self.queue_prompt(workflow)
            
            if prompt_id:
                print(f"   Queued: {prompt_id[:8]}...")
                if self.wait_for_completion(prompt_id):
                    print(f"   ✅ Complete!")
                    
                    # Record in preference system
                    filename = f"{prefix}_{i+1:05d}_.png"
                    self.pref_system.save_image_record(
                        filename, positive, negative, tags, self.current_model, seed
                    )
                else:
                    print(f"   ⚠️ Timeout")
            else:
                print(f"   ❌ Failed")
                
        print(f"\n{'='*60}")
        print(f"  COLLECTION COMPLETE: {prefix}")
        print(f"{'='*60}")
        
    def generate_style_switch_collection(self,
                                         styles: list,
                                         images_per_style: int = 5,
                                         custom_selections: dict = None):
        """Generate collection with automatic style switching"""
        
        print(f"\n{'='*60}")
        print(f"  STYLE-SWITCH COLLECTION")
        print(f"  Styles: {styles}")
        print(f"  Images per style: {images_per_style}")
        print(f"{'='*60}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        for style in styles:
            prefix = f"collection_{style}_{timestamp}"
            print(f"\n🎨 Switching to style: {style.upper()}")
            
            for i in range(images_per_style):
                print(f"\n[{style} {i+1}/{images_per_style}]")
                
                positive, negative, tags = self.build_randomized_prompt(style, custom_selections)
                workflow = self.create_workflow(positive, negative, prefix)
                seed = workflow["3"]["inputs"]["seed"]
                prompt_id = self.queue_prompt(workflow)
                
                if prompt_id:
                    print(f"   Queued: {prompt_id[:8]}...")
                    if self.wait_for_completion(prompt_id):
                        print(f"   ✅ Complete!")
                        filename = f"{prefix}_{i+1:05d}_.png"
                        self.pref_system.save_image_record(
                            filename, positive, negative, tags, self.current_model, seed
                        )
                    else:
                        print(f"   ⚠️ Timeout")
                        
        print(f"\n✅ Style-switch collection complete!")
        
    def close(self):
        self.pref_system.close()


# ==================== CLI INTERFACE ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Collection Generator')
    parser.add_argument('--style', default='tribal', help='Generation style')
    parser.add_argument('--count', type=int, default=10, help='Number of images')
    parser.add_argument('--name', default='collection', help='Collection name')
    parser.add_argument('--body', help='Body type override')
    parser.add_argument('--bust', help='Bust size override')
    parser.add_argument('--muscle', help='Muscle tone override')
    
    args = parser.parse_args()
    
    # Check ComfyUI
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        print("✅ ComfyUI connected")
    except:
        print("❌ ComfyUI not running!")
        return
        
    # Build custom selections from args
    custom = {}
    if args.body:
        custom['body_type'] = args.body
    if args.bust:
        custom['bust_size'] = args.bust
    if args.muscle:
        custom['muscle_tone'] = args.muscle
        
    # Generate
    gen = SmartGenerator()
    gen.generate_collection(
        args.name,
        args.style,
        args.count,
        custom if custom else None
    )
    gen.close()
    

if __name__ == "__main__":
    main()
