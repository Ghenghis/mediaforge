"""
MASTER WPF API SERVER
- All AI learning features
- Enhanced prompt generation
- Rating system
- Batch generation
- Real-time stats
"""
import sqlite3
import json
import random
import requests
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

API_PORT = 8190
COMFYUI_URL = "http://localhost:8188"
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\master_learning.db")

# PERFECTION TAGS
QUALITY_TAGS = ["masterpiece", "best quality", "highly detailed", "ultra detailed", "8k uhd", "photorealistic", "hyperrealistic", "professional photography", "award winning"]
FACE_TAGS = ["detailed face", "beautiful face", "perfect face", "detailed eyes", "beautiful eyes", "sparkling eyes", "detailed pupils", "long eyelashes", "detailed lips"]
SKIN_TAGS = ["detailed skin", "flawless skin", "smooth skin", "skin texture", "subsurface scattering", "glowing skin"]
LIGHTING_TAGS = ["cinematic lighting", "soft lighting", "natural lighting", "dramatic lighting", "volumetric lighting", "golden hour"]
CAMERA_TAGS = ["sharp focus", "depth of field", "bokeh", "85mm lens", "DSLR", "RAW photo"]
NEGATIVE = "bad anatomy, bad hands, extra fingers, deformed, blurry, low quality, worst quality, watermark, text, ugly, disfigured"

THEMES = {
    "tribal_warrior": {"base": "tribal warrior woman", "details": ["tribal paint", "war paint", "tribal jewelry", "feathers", "fierce expression", "warrior stance"], "weight": 4},
    "elegant_portrait": {"base": "beautiful woman portrait", "details": ["elegant", "sophisticated", "graceful", "stunning beauty", "captivating"], "weight": 3},
    "natural_beauty": {"base": "naturally beautiful woman", "details": ["natural look", "authentic beauty", "warm expression", "radiant"], "weight": 2},
    "artistic_portrait": {"base": "artistic portrait of a woman", "details": ["fine art", "creative lighting", "studio portrait"], "weight": 1}
}


class MasterDB:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()
        
    def _init(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY, filename TEXT UNIQUE, prompt TEXT, 
                rating REAL DEFAULT 0, is_gold_standard INTEGER DEFAULT 0,
                created_at TEXT, rated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS generation_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT, negative TEXT, theme TEXT, seed INTEGER,
                status TEXT DEFAULT 'pending', created_at TEXT
            );
        ''')
        self.conn.commit()
        
    def scan_images(self):
        imgs = list(OUTPUT_DIR.glob("*.png"))
        new = 0
        for img in imgs:
            if not self.conn.execute('SELECT 1 FROM images WHERE filename=?', (img.name,)).fetchone():
                self.conn.execute('INSERT INTO images (id, filename, created_at) VALUES (?,?,?)',
                    (f"img_{hash(img.name)%10**8}", img.name, datetime.now().isoformat()))
                new += 1
        self.conn.commit()
        return {'total': len(imgs), 'new': new}
        
    def get_images(self, filter_type='all', limit=100):
        sql = 'SELECT id, filename, rating, prompt FROM images'
        if filter_type == 'unrated': sql += ' WHERE rating = 0 OR rating IS NULL'
        elif filter_type == 'rated': sql += ' WHERE rating > 0'
        elif filter_type == 'high': sql += ' WHERE rating >= 8'
        elif filter_type == 'excellent': sql += ' WHERE rating >= 10'
        sql += f' ORDER BY created_at DESC LIMIT {limit}'
        return [dict(r) for r in self.conn.execute(sql).fetchall()]
        
    def rate_image(self, img_id, rating):
        rating = max(0, min(15, float(rating)))
        self.conn.execute('UPDATE images SET rating=?, rated_at=?, is_gold_standard=? WHERE id=?',
            (rating, datetime.now().isoformat(), 1 if rating >= 15 else 0, img_id))
        self.conn.commit()
        return {'id': img_id, 'rating': rating, 'saved': True}
        
    def get_stats(self):
        t = self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]
        r = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
        h = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 8').fetchone()[0]
        e = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 10').fetchone()[0]
        g = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 15').fetchone()[0]
        avg = self.conn.execute('SELECT AVG(rating) FROM images WHERE rating > 0').fetchone()[0] or 0
        return {'total': t, 'rated': r, 'unrated': t-r, 'high': h, 'excellent': e, 'gold': g, 'avg': round(avg, 2)}
        
    def get_distribution(self):
        dist = {}
        for row in self.conn.execute('SELECT rating, COUNT(*) FROM images WHERE rating > 0 GROUP BY rating ORDER BY rating DESC'):
            dist[int(row[0])] = row[1]
        return dist


db = MasterDB()


def build_enhanced_prompt(subject=None, theme=None, detail_level=3):
    """Build perfection-level prompt"""
    if theme and theme in THEMES:
        t = THEMES[theme]
        parts = [t["base"]]
        parts.extend(random.sample(t["details"], min(4, len(t["details"]))))
    elif subject:
        parts = [subject]
    else:
        parts = ["beautiful woman, portrait"]
    
    # Add quality tags
    parts.extend(random.sample(QUALITY_TAGS, min(5, detail_level * 2)))
    parts.extend(random.sample(FACE_TAGS, min(5, detail_level * 2)))
    parts.extend(random.sample(SKIN_TAGS, min(3, detail_level)))
    parts.extend(random.sample(LIGHTING_TAGS, min(3, detail_level)))
    parts.extend(random.sample(CAMERA_TAGS, min(3, detail_level)))
    
    return ", ".join(parts)


def get_weighted_theme():
    themes = []
    for key, data in THEMES.items():
        themes.extend([key] * data["weight"])
    return random.choice(themes)


def queue_comfyui(prompt, negative, seed, filename):
    """Send to ComfyUI"""
    workflow = {
        "3": {"class_type": "KSampler", "inputs": {"cfg": 7, "denoise": 1, "latent_image": ["5", 0], "model": ["4", 0], "negative": ["7", 0], "positive": ["6", 0], "sampler_name": "euler_ancestral", "scheduler": "normal", "seed": seed, "steps": 30}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "CyberRealistic.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": 768, "width": 512}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": prompt}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": negative}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename, "images": ["8", 0]}}
    }
    try:
        r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


class MasterAPI(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
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
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        if path == '/api/status':
            try:
                requests.get(f"{COMFYUI_URL}/system_stats", timeout=3)
                comfy = 'online'
            except:
                comfy = 'offline'
            self._json({'api': 'online', 'comfyui': comfy, 'stats': db.get_stats()})
            
        elif path == '/api/stats':
            self._json(db.get_stats())
            
        elif path == '/api/distribution':
            self._json(db.get_distribution())
            
        elif path == '/api/images':
            f = query.get('filter', ['all'])[0]
            limit = int(query.get('limit', ['100'])[0])
            self._json(db.get_images(f, limit))
            
        elif path == '/api/scan':
            self._json(db.scan_images())
            
        elif path == '/api/themes':
            self._json({'themes': list(THEMES.keys()), 'weights': {k: v['weight'] for k, v in THEMES.items()}})
            
        elif path == '/api/prompt':
            subject = query.get('subject', [''])[0]
            theme = query.get('theme', [''])[0]
            level = int(query.get('level', ['3'])[0])
            prompt = build_enhanced_prompt(subject or None, theme or None, level)
            self._json({'prompt': prompt, 'negative': NEGATIVE, 'tags_count': len(prompt.split(','))})
            
        elif path.startswith('/image/'):
            fn = path[7:]
            fp = OUTPUT_DIR / fn
            if fp.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                self.wfile.write(fp.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self._json({'error': 'not found'}, 404)
            
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/rate':
            result = db.rate_image(data['id'], data['rating'])
            self._json(result)
            
        elif path == '/api/generate':
            subject = data.get('subject', '')
            theme = data.get('theme', '')
            level = int(data.get('level', 3))
            
            prompt = build_enhanced_prompt(subject or None, theme or None, level)
            seed = data.get('seed', random.randint(1, 2**31))
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"wpf_{ts}_{seed}"
            
            result = queue_comfyui(prompt, NEGATIVE, seed, filename)
            self._json({'queued': 'prompt_id' in result, 'prompt': prompt, 'seed': seed, 'filename': filename})
            
        elif path == '/api/generate-batch':
            count = int(data.get('count', 10))
            theme = data.get('theme', '')
            level = int(data.get('level', 3))
            
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            results = []
            
            for i in range(count):
                t = theme if theme else get_weighted_theme()
                prompt = build_enhanced_prompt(None, t, level)
                seed = random.randint(1, 2**31)
                filename = f"batch_{ts}_{t}_{i+1:03d}"
                
                result = queue_comfyui(prompt, NEGATIVE, seed, filename)
                results.append({
                    'num': i+1, 'theme': t, 'seed': seed,
                    'queued': 'prompt_id' in result
                })
                
            self._json({'total': count, 'queued': sum(1 for r in results if r['queued']), 'results': results})
            
        elif path == '/api/generate-enhanced':
            # Generate 100 enhanced images based on high-rated themes
            count = int(data.get('count', 100))
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            queued = 0
            
            for i in range(count):
                theme = get_weighted_theme()
                prompt = build_enhanced_prompt(None, theme, 3)
                seed = random.randint(1, 2**31)
                filename = f"enhanced_{ts}_{theme}_{i+1:03d}"
                
                result = queue_comfyui(prompt, NEGATIVE, seed, filename)
                if 'prompt_id' in result:
                    queued += 1
                    
            self._json({'total': count, 'queued': queued})
            
        elif path == '/api/chat':
            # Process chat for learning
            message = data.get('message', '')
            # Extract preferences from message (simplified)
            preferences = []
            if 'like' in message.lower() or 'love' in message.lower():
                preferences.append({'type': 'like', 'text': message})
            if 'hate' in message.lower() or 'dislike' in message.lower():
                preferences.append({'type': 'dislike', 'text': message})
            self._json({'received': True, 'preferences': preferences})
            
        else:
            self._json({'error': 'not found'}, 404)
            
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  MASTER WPF API SERVER")
    print("=" * 60)
    
    db.scan_images()
    stats = db.get_stats()
    
    print(f"\n📊 Database: {stats['total']} images, {stats['rated']} rated")
    print(f"   High(8+): {stats['high']} | Excellent(10+): {stats['excellent']} | Gold(15): {stats['gold']}")
    
    print(f"\n🌐 API: http://127.0.0.1:{API_PORT}")
    print(f"\n📡 Endpoints:")
    print(f"   GET  /api/status      - System status")
    print(f"   GET  /api/stats       - Rating statistics")
    print(f"   GET  /api/images      - List images (?filter=all|rated|high)")
    print(f"   GET  /api/themes      - Available themes")
    print(f"   GET  /api/prompt      - Generate prompt (?theme=tribal_warrior&level=3)")
    print(f"   GET  /api/scan        - Scan new images")
    print(f"   POST /api/rate        - Rate image {{id, rating}}")
    print(f"   POST /api/generate    - Generate single image")
    print(f"   POST /api/generate-batch    - Generate batch {{count, theme}}")
    print(f"   POST /api/generate-enhanced - Generate 100 enhanced images")
    
    print(f"\n✅ Ready for WPF connection!")
    
    HTTPServer(('0.0.0.0', API_PORT), MasterAPI).serve_forever()


if __name__ == "__main__":
    main()
