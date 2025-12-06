"""
WPF Bridge - Complete Integration Layer
Handles all communication between WPF GUI and ComfyUI
"""
import json
import sqlite3
import random
import time
import urllib.request
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os

# Paths
DB_PATH = Path(r"c:\Users\Admin\civitai\data\preferences.db")
CONFIG_PATH = Path(r"c:\Users\Admin\civitai\data\generation_config.json")
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
COMFY_URL = "http://localhost:8188"
API_PORT = 8190

# ============================================================
# DATABASE MANAGER
# ============================================================
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.lock = threading.Lock()
        self._setup()
        
    def _setup(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            prompt TEXT,
            negative TEXT,
            tags TEXT,
            model TEXT,
            seed INTEGER,
            rating INTEGER DEFAULT 0,
            created_at TEXT,
            rated_at TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS tag_weights (
            tag TEXT PRIMARY KEY,
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0,
            weight REAL DEFAULT 0.5
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS learning_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            data TEXT,
            timestamp TEXT
        )''')
        
        self.conn.commit()
        
    def rate_image(self, filename: str, rating: int) -> dict:
        """Rate image and update tag weights"""
        with self.lock:
            cursor = self.conn.cursor()
            
            # Get image tags
            cursor.execute('SELECT tags FROM images WHERE filename = ?', (filename,))
            result = cursor.fetchone()
            
            if not result:
                return {'error': 'Image not found'}
                
            tags = json.loads(result[0]) if result[0] else []
            
            # Update image rating
            cursor.execute('''
                UPDATE images SET rating = ?, rated_at = ? WHERE filename = ?
            ''', (rating, datetime.now().isoformat(), filename))
            
            # Update tag weights based on rating
            is_like = rating >= 4
            is_dislike = rating <= 2
            
            updated_tags = []
            for tag in tags:
                cursor.execute('SELECT likes, dislikes FROM tag_weights WHERE tag = ?', (tag,))
                row = cursor.fetchone()
                
                if row:
                    likes = row[0] + (1 if is_like else 0)
                    dislikes = row[1] + (1 if is_dislike else 0)
                else:
                    likes = 1 if is_like else 0
                    dislikes = 1 if is_dislike else 0
                    
                # Bayesian weight calculation
                weight = (likes + 1) / (likes + dislikes + 2)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO tag_weights (tag, likes, dislikes, weight)
                    VALUES (?, ?, ?, ?)
                ''', (tag, likes, dislikes, weight))
                
                updated_tags.append({'tag': tag, 'weight': round(weight, 3)})
                
            # Log learning
            cursor.execute('''
                INSERT INTO learning_log (action, data, timestamp)
                VALUES (?, ?, ?)
            ''', ('rate', json.dumps({'filename': filename, 'rating': rating, 'tags_updated': len(tags)}), 
                  datetime.now().isoformat()))
            
            self.conn.commit()
            
            return {
                'status': 'success',
                'filename': filename,
                'rating': rating,
                'tags_updated': updated_tags
            }
            
    def get_preferred_tags(self, limit: int = 20) -> list:
        """Get tags with highest weights"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT tag, weight, likes, dislikes FROM tag_weights
            WHERE weight > 0.5 ORDER BY weight DESC, likes DESC LIMIT ?
        ''', (limit,))
        return [{'tag': r[0], 'weight': r[1], 'likes': r[2], 'dislikes': r[3]} for r in cursor.fetchall()]
        
    def get_avoided_tags(self, limit: int = 20) -> list:
        """Get tags user dislikes"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT tag, weight, likes, dislikes FROM tag_weights
            WHERE weight < 0.4 AND dislikes > 0 ORDER BY weight ASC LIMIT ?
        ''', (limit,))
        return [{'tag': r[0], 'weight': r[1], 'likes': r[2], 'dislikes': r[3]} for r in cursor.fetchall()]
        
    def save_image(self, filename: str, prompt: str, negative: str, tags: list, model: str, seed: int):
        """Save generated image record"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO images (filename, prompt, negative, tags, model, seed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (filename, prompt, negative, json.dumps(tags), model, seed, datetime.now().isoformat()))
            self.conn.commit()
            
    def get_stats(self) -> dict:
        """Get learning statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM images')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating > 0')
        rated = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(rating) FROM images WHERE rating > 0')
        avg = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM tag_weights')
        tags_learned = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tag_weights WHERE weight > 0.6')
        preferred = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tag_weights WHERE weight < 0.4')
        avoided = cursor.fetchone()[0]
        
        return {
            'total_images': total,
            'rated_images': rated,
            'average_rating': round(avg, 2),
            'tags_learned': tags_learned,
            'preferred_tags': preferred,
            'avoided_tags': avoided
        }
        
    def get_learning_log(self, limit: int = 50) -> list:
        """Get recent learning actions"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT action, data, timestamp FROM learning_log
            ORDER BY id DESC LIMIT ?
        ''', (limit,))
        return [{'action': r[0], 'data': json.loads(r[1]), 'timestamp': r[2]} for r in cursor.fetchall()]


# ============================================================
# PROMPT BUILDER WITH LEARNING
# ============================================================
class SmartPromptBuilder:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.load_config()
        
    def load_config(self):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
    def build_prompt(self, selections: dict = None, style: str = "tribal") -> tuple:
        """Build prompt with learned preferences applied"""
        
        sel = selections or {}
        parts = []
        tags_used = []
        
        # Quality base
        quality = ["masterpiece", "best quality", "ultra detailed", "8k resolution", 
                   "photorealistic", "RAW photo", "DSLR", "realistic lighting",
                   "high detail skin texture", "sharp focus"]
        parts.extend(quality)
        tags_used.extend(quality)
        
        # Age (always adult)
        age = sel.get('age') or random.choice(["21yo", "22yo", "23yo", "24yo", "25yo"])
        parts.append(f"(adult woman:1.3), ({age}:1.2)")
        tags_used.extend(["adult woman", age])
        
        # Body frame
        frame = sel.get('body_frame') or random.choice(self.config['body_types']['frame'])
        parts.append(f"({frame}:1.2)")
        tags_used.append(frame)
        
        # Build type
        build = sel.get('body_build') or random.choice(self.config['body_types']['build'])
        parts.append(f"({build}:1.2)")
        tags_used.append(build)
        
        # Muscle tone
        muscle = sel.get('muscle_tone') or random.choice(self.config['body_types']['muscle_tone'])
        parts.append(f"({muscle}:1.3)")
        tags_used.append(muscle)
        
        # Bust size
        bust = sel.get('bust_size') or random.choice(self.config['bust_sizes']['sizes'])
        parts.append(f"({bust}:1.2)")
        tags_used.append(bust)
        
        # Face
        face = sel.get('face_shape') or random.choice(self.config['face_types']['shape'])
        parts.append(f"({face}:1.1)")
        tags_used.append(face)
        
        features = sel.get('face_features') or random.choice(self.config['face_types']['features'])
        parts.append(features)
        tags_used.append(features)
        
        expression = sel.get('expression') or random.choice(self.config['face_types']['expressions'])
        parts.append(f"({expression}:1.1)")
        tags_used.append(expression)
        
        # Eyes
        if sel.get('heterochromia') or random.random() > 0.5:
            eyes = "heterochromia, different colored eyes, one blue eye one green eye"
        else:
            eyes = sel.get('eye_color') or random.choice(self.config['eye_types']['color'])
        parts.append(f"({eyes}:1.3)")
        tags_used.append(eyes)
        
        eye_detail = random.choice(self.config['eye_types']['details'])
        parts.append(eye_detail)
        tags_used.append(eye_detail)
        
        # Hair
        hair_len = sel.get('hair_length') or random.choice(self.config['hair_types']['length'])
        hair_style = sel.get('hair_style') or random.choice(self.config['hair_types']['style'])
        hair_color = sel.get('hair_color') or random.choice(self.config['hair_types']['color'])
        parts.extend([hair_len, hair_style, hair_color])
        tags_used.extend([hair_len, hair_style, hair_color])
        
        # Skin
        skin = sel.get('skin_tone') or random.choice(self.config['skin_types']['tone'])
        skin_tex = random.choice(self.config['skin_types']['texture'])
        parts.append(f"({skin}:1.1), {skin_tex}")
        tags_used.extend([skin, skin_tex])
        
        # Style-specific
        if style == "tribal":
            face_paint = sel.get('face_paint') or random.choice(self.config['tribal_specific']['face_paint'])
            body_paint = sel.get('body_paint') or random.choice(self.config['tribal_specific']['body_paint'])
            paint_color = random.choice(self.config['tribal_specific']['colors'])
            accessory = random.choice(self.config['tribal_specific']['accessories'])
            
            parts.extend([
                f"({face_paint}:1.4)", f"({body_paint}:1.3)",
                paint_color, f"({accessory}:1.2)", "tribal warrior woman"
            ])
            tags_used.extend([face_paint, body_paint, paint_color, accessory, "tribal"])
            
        # Pose
        pose = sel.get('pose') or random.choice(self.config['poses']['standing'])
        angle = sel.get('angle') or random.choice(self.config['poses']['angles'])
        parts.extend([f"({pose}:1.1)", angle])
        tags_used.extend([pose, angle])
        
        # Lighting
        lighting = sel.get('lighting') or random.choice(self.config['lighting']['type'])
        mood = random.choice(self.config['lighting']['mood'])
        parts.extend([f"({lighting}:1.2)", mood])
        tags_used.extend([lighting, mood])
        
        # Background
        bg = sel.get('background') or random.choice(self.config['backgrounds']['nature'])
        parts.append(bg)
        tags_used.append(bg)
        
        # Apply learned preferences
        preferred = self.db.get_preferred_tags(limit=5)
        for item in preferred:
            if item['tag'] not in tags_used and item['weight'] > 0.65:
                parts.append(f"({item['tag']}:{item['weight']:.1f})")
                tags_used.append(item['tag'])
                
        positive = ", ".join(parts)
        
        # Build negative with avoided tags
        negative = self._build_negative()
        
        return positive, negative, tags_used
        
    def _build_negative(self) -> str:
        """Build negative prompt with learned avoidances"""
        base_negative = [
            "EasyNegative", "bad-hands-5", "ng_deepnegative_v1_75t",
            "(child:2.0)", "(kid:2.0)", "(teen:2.0)", "(minor:2.0)", "(underage:2.0)",
            "(bad anatomy:1.4)", "(bad proportions:1.4)", "(deformed:1.4)",
            "(extra fingers:1.5)", "(missing fingers:1.5)", "(mutated hands:1.4)",
            "(low quality:1.5)", "(worst quality:1.5)", "(blurry:1.3)",
            "(watermark:1.5)", "(text:1.5)",
            "(cartoon:1.5)", "(anime:1.5)", "(3d render:1.4)",
            "ugly", "disfigured"
        ]
        
        # Add learned avoided tags
        avoided = self.db.get_avoided_tags(limit=10)
        for item in avoided:
            base_negative.append(f"({item['tag']}:1.3)")
            
        return ", ".join(base_negative)
        
    def enhance_prompt(self, prompt: str) -> str:
        """AI-enhance a user prompt"""
        quality = ["masterpiece", "best quality", "8k resolution", "photorealistic", "ultra detailed"]
        preferred = self.db.get_preferred_tags(limit=5)
        
        enhanced_parts = quality + [prompt]
        for item in preferred:
            if item['weight'] > 0.6:
                enhanced_parts.append(f"({item['tag']}:{item['weight']:.1f})")
                
        return ", ".join(enhanced_parts)


# ============================================================
# IMAGE GENERATOR
# ============================================================
class ImageGenerator:
    def __init__(self, db: DatabaseManager, prompt_builder: SmartPromptBuilder):
        self.db = db
        self.builder = prompt_builder
        self.models = {
            'primary': 'CyberRealistic.safetensors',
            'backup': 'ponyDiffusionV6XL_v6.safetensors'
        }
        self.current_model = self.models['primary']
        
    def create_workflow(self, positive: str, negative: str, prefix: str) -> dict:
        seed = random.randint(0, 2**32)
        return {
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": self.current_model}},
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
            "_seed": seed
        }
        
    def queue(self, workflow: dict) -> str:
        data = json.dumps({"prompt": {k: v for k, v in workflow.items() if not k.startswith('_')}}).encode()
        req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read()).get('prompt_id')
        except Exception as e:
            # Try backup model
            if self.current_model != self.models['backup']:
                self.current_model = self.models['backup']
                workflow["4"]["inputs"]["ckpt_name"] = self.current_model
                return self.queue(workflow)
            return None
            
    def wait(self, prompt_id: str, timeout: int = 180) -> bool:
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
        
    def generate_one(self, selections: dict = None, style: str = "tribal", prefix: str = "gen") -> dict:
        """Generate single image"""
        positive, negative, tags = self.builder.build_prompt(selections, style)
        workflow = self.create_workflow(positive, negative, prefix)
        seed = workflow['_seed']
        
        prompt_id = self.queue(workflow)
        if prompt_id and self.wait(prompt_id):
            filename = f"{prefix}_{seed}.png"
            self.db.save_image(filename, positive, negative, tags, self.current_model, seed)
            return {'status': 'success', 'filename': filename, 'seed': seed, 'tags': tags[:5]}
        return {'status': 'failed'}
        
    def generate_batch(self, count: int, selections: dict = None, style: str = "tribal", prefix: str = "batch"):
        """Generate batch of images"""
        results = []
        for i in range(count):
            result = self.generate_one(selections, style, f"{prefix}_{i+1:03d}")
            results.append(result)
            yield {'progress': i+1, 'total': count, 'result': result}


# ============================================================
# API SERVER
# ============================================================
db = DatabaseManager()
builder = SmartPromptBuilder(db)
generator = ImageGenerator(db, builder)

class APIHandler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
        
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/api/options':
            with open(CONFIG_PATH) as f:
                self._json(json.load(f))
        elif path == '/api/stats':
            self._json(db.get_stats())
        elif path == '/api/preferred':
            self._json(db.get_preferred_tags(30))
        elif path == '/api/avoided':
            self._json(db.get_avoided_tags(30))
        elif path == '/api/learning-log':
            self._json(db.get_learning_log(50))
        elif path == '/api/images':
            images = sorted(OUTPUT_DIR.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:200]
            self._json([{'name': i.name, 'size': i.stat().st_size, 'time': i.stat().st_mtime} for i in images])
        elif path == '/api/status':
            try:
                urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=3)
                self._json({'comfyui': 'online', 'api': 'online', 'learning': db.get_stats()})
            except:
                self._json({'comfyui': 'offline', 'api': 'online'})
        else:
            self._json({'error': 'not found'}, 404)
            
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/rate':
            result = db.rate_image(data['filename'], data['rating'])
            self._json(result)
        elif path == '/api/enhance':
            enhanced = builder.enhance_prompt(data.get('prompt', ''))
            self._json({'enhanced': enhanced})
        elif path == '/api/build-prompt':
            positive, negative, tags = builder.build_prompt(data.get('selections'), data.get('style', 'tribal'))
            self._json({'positive': positive, 'negative': negative, 'tags': tags})
        elif path == '/api/generate':
            result = generator.generate_one(data.get('selections'), data.get('style', 'tribal'), data.get('prefix', 'wpf'))
            self._json(result)
        elif path == '/api/generate-batch':
            count = data.get('count', 10)
            def run():
                for progress in generator.generate_batch(count, data.get('selections'), data.get('style', 'tribal'), data.get('prefix', 'batch')):
                    pass
            threading.Thread(target=run).start()
            self._json({'status': 'started', 'count': count})
        else:
            self._json({'error': 'not found'}, 404)
            
    def log_message(self, *args): pass


def start_api():
    server = HTTPServer(('0.0.0.0', API_PORT), APIHandler)
    print(f"✅ WPF API running on http://127.0.0.1:{API_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    print("="*60)
    print("  WPF BRIDGE - AI Learning Image Generation")
    print("="*60)
    print(f"\n📡 Endpoints:")
    print(f"   GET  /api/options     - Dropdown options")
    print(f"   GET  /api/stats       - Learning stats")
    print(f"   GET  /api/preferred   - Preferred tags")
    print(f"   GET  /api/avoided     - Avoided tags")
    print(f"   GET  /api/images      - Generated images")
    print(f"   GET  /api/status      - System status")
    print(f"   POST /api/rate        - Rate image")
    print(f"   POST /api/enhance     - Enhance prompt")
    print(f"   POST /api/build-prompt- Build from selections")
    print(f"   POST /api/generate    - Generate single")
    print(f"   POST /api/generate-batch - Generate batch")
    start_api()
