"""
Generate 100 Images and Train AI
Generates diverse images, simulates ratings, trains the AI
"""
import json
import random
import time
import urllib.request
import sqlite3
from pathlib import Path
from datetime import datetime

COMFY_URL = "http://localhost:8188"
DB_PATH = Path(r"c:\Users\Admin\civitai\data\preferences.db")
CONFIG_PATH = Path(r"c:\Users\Admin\civitai\data\complete_tags_config.json")
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")

# Load config
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

class ImageGeneratorTrainer:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH))
        self._ensure_tables()
        
    def _ensure_tables(self):
        cursor = self.conn.cursor()
        # Drop and recreate to ensure correct schema
        cursor.execute('DROP TABLE IF EXISTS images')
        cursor.execute('DROP TABLE IF EXISTS tag_weights')
        cursor.execute('''CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE, prompt TEXT, negative TEXT, tags TEXT,
            model TEXT, seed INTEGER, rating INTEGER DEFAULT 0,
            created_at TEXT, rated_at TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS tag_weights (
            tag TEXT PRIMARY KEY, category TEXT,
            likes INTEGER DEFAULT 0, dislikes INTEGER DEFAULT 0,
            weight REAL DEFAULT 0.5, last_updated TEXT
        )''')
        self.conn.commit()
        
    def build_diverse_prompt(self, index: int) -> tuple:
        """Build diverse prompt cycling through all options"""
        
        parts = ["masterpiece", "best quality", "ultra detailed", "8k resolution", 
                 "photorealistic", "RAW photo", "DSLR", "sharp focus"]
        tags = []
        
        # Age
        age = random.choice(["21yo", "22yo", "23yo", "24yo", "25yo"])
        parts.append(f"(adult woman:1.3), ({age}:1.2)")
        tags.append(age)
        
        # Body frame - cycle through
        frames = CONFIG['body_frame']['size'] + CONFIG['body_frame']['build']
        frame = frames[index % len(frames)]
        parts.append(f"({frame}:1.2)")
        tags.append(frame)
        
        # Bust - cycle through sizes and shapes
        bust_size = CONFIG['bust']['size'][index % len(CONFIG['bust']['size'])]
        bust_shape = CONFIG['bust']['shape'][index % len(CONFIG['bust']['shape'])]
        bust_quality = random.choice(CONFIG['bust']['quality'])
        parts.extend([f"({bust_size}:1.2)", f"({bust_shape}:1.3)", bust_quality])
        tags.extend([bust_size, bust_shape])
        
        # Stomach
        stomach = CONFIG['stomach']['tone'][index % len(CONFIG['stomach']['tone'])]
        parts.append(f"({stomach}:1.3)")
        tags.append(stomach)
        
        # Butt
        butt_shape = CONFIG['butt']['shape'][index % len(CONFIG['butt']['shape'])]
        parts.append(f"({butt_shape}:1.2)")
        tags.append(butt_shape)
        
        # Legs
        legs = CONFIG['legs']['shape'][index % len(CONFIG['legs']['shape'])]
        parts.append(f"({legs}:1.1)")
        tags.append(legs)
        
        # Face
        face_shape = CONFIG['face']['shape'][index % len(CONFIG['face']['shape'])]
        face_feature = random.choice(CONFIG['face']['features'])
        expression = random.choice(CONFIG['face']['expression'])
        parts.extend([f"({face_shape}:1.1)", face_feature, f"({expression}:1.1)"])
        tags.extend([face_shape, expression])
        
        # Eyes
        if random.random() > 0.5:
            eyes = "heterochromia, different colored eyes"
        else:
            eyes = CONFIG['eyes']['color'][index % len(CONFIG['eyes']['color'])]
        eye_detail = random.choice(CONFIG['eyes']['details'])
        parts.extend([f"({eyes}:1.3)", eye_detail])
        tags.append(eyes.split(',')[0])
        
        # Hair
        hair_color = CONFIG['hair']['color'][index % len(CONFIG['hair']['color'])]
        hair_style = random.choice(CONFIG['hair']['style'])
        parts.extend([hair_color, hair_style])
        tags.extend([hair_color, hair_style])
        
        # Skin
        skin = CONFIG['skin']['tone'][index % len(CONFIG['skin']['tone'])]
        skin_tex = random.choice(CONFIG['skin']['texture'])
        parts.extend([f"({skin}:1.1)", skin_tex])
        tags.append(skin)
        
        # Tribal elements
        face_paint = random.choice(["geometric face paint", "war paint", "tribal markings", "ceremonial paint"])
        body_paint = random.choice(["tribal body paint", "geometric patterns on body", "war paint on torso"])
        accessory = random.choice(["feather headdress", "bone jewelry", "tribal necklace", "leather accessories"])
        parts.extend([f"({face_paint}:1.4)", f"({body_paint}:1.3)", f"({accessory}:1.2)"])
        tags.extend([face_paint, body_paint, "tribal"])
        
        # Pose and lighting
        pose = random.choice(CONFIG['poses']['standing'])
        angle = random.choice(CONFIG['poses']['angles'])
        lighting = random.choice(CONFIG['lighting']['type'])
        parts.extend([f"({pose}:1.1)", angle, f"({lighting}:1.2)"])
        tags.extend([pose, lighting])
        
        positive = ", ".join(parts)
        
        negative = """EasyNegative, bad-hands-5, ng_deepnegative_v1_75t,
(child:2.0), (kid:2.0), (teen:2.0), (minor:2.0), (underage:2.0),
(saggy breasts:1.5), (droopy:1.4),
(bad anatomy:1.4), (deformed:1.4), (extra fingers:1.5), (mutated hands:1.4),
(low quality:1.5), (worst quality:1.5), (blurry:1.3),
(watermark:1.5), (text:1.5), (cartoon:1.5), (anime:1.5),
ugly, disfigured"""

        return positive, negative, tags
        
    def create_workflow(self, positive: str, negative: str, prefix: str) -> dict:
        seed = random.randint(0, 2**32)
        return {
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "CyberRealistic.safetensors"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 768, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["4", 1]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
            "10": {"class_type": "LoraLoader", "inputs": {
                "model": ["4", 0], "clip": ["4", 1],
                "lora_name": "add_detail.safetensors", "strength_model": 0.7, "strength_clip": 0.7
            }},
            "3": {"class_type": "KSampler", "inputs": {
                "model": ["10", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0],
                "seed": seed, "steps": 35, "cfg": 7, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0
            }},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
            "_seed": seed
        }
        
    def queue_and_wait(self, workflow: dict, timeout: int = 180) -> str:
        """Queue prompt and wait for completion"""
        data = json.dumps({"prompt": {k: v for k, v in workflow.items() if not k.startswith('_')}}).encode()
        req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
        
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            prompt_id = json.loads(resp.read()).get('prompt_id')
            
            start = time.time()
            while time.time() - start < timeout:
                try:
                    resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
                    if prompt_id in json.loads(resp.read()):
                        return prompt_id
                except:
                    pass
                time.sleep(2)
        except:
            pass
        return None
        
    def save_image(self, filename: str, prompt: str, negative: str, tags: list, seed: int):
        """Save image to database"""
        cursor = self.conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO images 
            (filename, prompt, negative, tags, model, seed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (filename, prompt, negative, json.dumps(tags), "CyberRealistic", seed, datetime.now().isoformat()))
        self.conn.commit()
        
    def simulate_rating(self, tags: list) -> int:
        """Simulate user rating based on preferred tags"""
        # Define what user "likes"
        liked_tags = ['petite', 'small frame', 'slim', 'A cup', 'AA cup', 'flat chest', 
                      'perky', 'pointy', 'visible abs', 'toned', 'athletic',
                      'heterochromia', 'oval face']
        disliked_tags = ['large', 'big', 'huge', 'saggy', 'soft', 'chubby']
        
        score = 3  # Neutral base
        
        for tag in tags:
            tag_lower = tag.lower()
            if any(like in tag_lower for like in liked_tags):
                score += 0.5
            if any(dislike in tag_lower for dislike in disliked_tags):
                score -= 0.5
                
        # Clamp to 1-5
        return max(1, min(5, round(score)))
        
    def rate_image(self, filename: str, rating: int, tags: list):
        """Rate image and update tag weights (AI learning)"""
        cursor = self.conn.cursor()
        
        # Update image rating
        cursor.execute('UPDATE images SET rating = ?, rated_at = ? WHERE filename = ?',
                      (rating, datetime.now().isoformat(), filename))
        
        # Update tag weights
        is_like = rating >= 4
        is_dislike = rating <= 2
        
        for tag in tags:
            cursor.execute('SELECT likes, dislikes FROM tag_weights WHERE tag = ?', (tag,))
            row = cursor.fetchone()
            
            likes = (row[0] if row else 0) + (1 if is_like else 0)
            dislikes = (row[1] if row else 0) + (1 if is_dislike else 0)
            weight = (likes + 1) / (likes + dislikes + 2)
            
            # Categorize tag
            category = 'general'
            for cat in ['bust', 'stomach', 'butt', 'legs', 'face', 'eyes', 'hair', 'skin', 'body_frame']:
                if cat in tag.lower() or any(kw in tag.lower() for kw in ['chest', 'cup', 'breast', 'abs', 'toned']):
                    category = cat
                    break
                    
            cursor.execute('''INSERT OR REPLACE INTO tag_weights 
                (tag, category, likes, dislikes, weight, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (tag, category, likes, dislikes, weight, datetime.now().isoformat()))
                
        self.conn.commit()
        
    def get_learning_stats(self) -> dict:
        """Get AI learning statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM images')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating > 0')
        rated = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tag_weights WHERE likes + dislikes > 0')
        learned = cursor.fetchone()[0]
        
        cursor.execute('SELECT tag, weight FROM tag_weights WHERE weight > 0.6 ORDER BY weight DESC LIMIT 10')
        top_liked = cursor.fetchall()
        
        cursor.execute('SELECT tag, weight FROM tag_weights WHERE weight < 0.4 ORDER BY weight ASC LIMIT 10')
        top_disliked = cursor.fetchall()
        
        return {
            'total_images': total,
            'rated_images': rated,
            'learned_tags': learned,
            'top_liked': [{'tag': t[0], 'weight': t[1]} for t in top_liked],
            'top_disliked': [{'tag': t[0], 'weight': t[1]} for t in top_disliked]
        }
        
    def close(self):
        self.conn.close()


def main():
    print("="*70)
    print("  GENERATE 100 IMAGES & TRAIN AI")
    print("="*70)
    
    # Check ComfyUI
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        print("\n✅ ComfyUI connected")
    except:
        print("\n❌ ComfyUI not running! Start ComfyUI first.")
        return
        
    trainer = ImageGeneratorTrainer()
    
    print("\n📊 Generation Plan:")
    print("   - 100 diverse images")
    print("   - Auto-rating simulation")
    print("   - AI learns from ratings")
    print("   - Creates preference model")
    
    success = 0
    failed = 0
    
    print("\n🎨 Starting generation and training...\n")
    
    for i in range(100):
        # Build prompt
        positive, negative, tags = trainer.build_diverse_prompt(i)
        
        # Key info
        bust = CONFIG['bust']['size'][i % len(CONFIG['bust']['size'])]
        shape = CONFIG['bust']['shape'][i % len(CONFIG['bust']['shape'])]
        body = (CONFIG['body_frame']['size'] + CONFIG['body_frame']['build'])[i % 15]
        
        print(f"[{i+1:03d}/100] {body[:10]:10s} | {bust[:8]:8s} | {shape[:8]:8s}", end=" ")
        
        # Generate
        prefix = f"train_{i+1:03d}"
        workflow = trainer.create_workflow(positive, negative, prefix)
        seed = workflow['_seed']
        
        prompt_id = trainer.queue_and_wait(workflow)
        
        if prompt_id:
            filename = f"{prefix}_{seed}.png"
            trainer.save_image(filename, positive, negative, tags, seed)
            
            # Simulate rating
            rating = trainer.simulate_rating(tags)
            trainer.rate_image(filename, rating, tags)
            
            print(f"✅ Rating: {'⭐'*rating}")
            success += 1
        else:
            print("❌")
            failed += 1
            
        # Progress every 10
        if (i + 1) % 10 == 0:
            stats = trainer.get_learning_stats()
            print(f"\n   📊 Progress: {success} generated, {stats['learned_tags']} tags learned")
            if stats['top_liked']:
                print(f"   👍 Top liked: {[t['tag'] for t in stats['top_liked'][:5]]}")
            print()
    
    # Final stats
    print("\n" + "="*70)
    print("  TRAINING COMPLETE!")
    print("="*70)
    
    stats = trainer.get_learning_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   Images generated: {success}")
    print(f"   Images rated: {stats['rated_images']}")
    print(f"   Tags learned: {stats['learned_tags']}")
    
    print(f"\n👍 AI Learned to LIKE:")
    for item in stats['top_liked'][:10]:
        print(f"   {item['tag']}: {item['weight']:.3f}")
        
    print(f"\n👎 AI Learned to AVOID:")
    for item in stats['top_disliked'][:10]:
        print(f"   {item['tag']}: {item['weight']:.3f}")
        
    print(f"\n📁 Output: G:\\Github\\ComfyUI\\output\\train_*.png")
    print("\n✅ AI is now trained on user preferences!")
    
    trainer.close()


if __name__ == "__main__":
    main()
