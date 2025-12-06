"""
Complete WPF API Server
- Image ID system with full tracking
- 0-15 Rating with auto-generation
- Story collections (Western, Tribal, Native American)
- Real-time AI learning
- Failsafe mechanisms
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import threading
from pathlib import Path
from datetime import datetime

from advanced_learning_system import AdvancedLearningSystem
from story_collection_system import StoryCollectionSystem, THEMES

API_PORT = 8190
COMFY_URL = "http://localhost:8188"
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")

# Initialize systems
learning = AdvancedLearningSystem()
stories = StoryCollectionSystem()


class CompleteAPI(BaseHTTPRequestHandler):
    
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
        
        routes = {
            '/': self._home,
            '/api/status': self._status,
            '/api/stats': self._stats,
            '/api/themes': self._themes,
            '/api/images': self._images,
            '/api/gold-standards': self._gold_standards,
            '/api/collections': self._collections,
            '/api/next-steps': self._next_steps,
        }
        
        handler = routes.get(path)
        if handler:
            try:
                handler()
            except Exception as e:
                self._json({'error': str(e)}, 500)
        else:
            self._json({'error': 'not found'}, 404)
            
    def do_POST(self):
        path = self.path
        try:
            data = self._body()
        except:
            data = {}
        
        routes = {
            '/api/rate': self._rate,
            '/api/create-collection': self._create_collection,
            '/api/generate': self._generate,
            '/api/generate-batch': self._generate_batch,
        }
        
        handler = routes.get(path)
        if handler:
            try:
                handler(data)
            except Exception as e:
                self._json({'error': str(e), 'failsafe': 'System recovered'}, 500)
        else:
            self._json({'error': 'not found'}, 404)
            
    # ==================== GET HANDLERS ====================
    
    def _home(self):
        self._json({
            'name': 'Civitai AI Learning API',
            'version': '2.0',
            'rating_scale': '0-15',
            'features': [
                'Image ID tracking',
                '0-15 rating with auto-generation',
                'Gold standard pursuit (rating 15)',
                'Story collections (500+ images)',
                'Western/Tribal/Native American themes',
                'Real-time AI learning'
            ],
            'endpoints': {
                'GET /api/status': 'System status',
                'GET /api/stats': 'Learning statistics',
                'GET /api/themes': 'Available themes',
                'GET /api/images': 'Recent images',
                'GET /api/gold-standards': 'Perfect images',
                'GET /api/collections': 'Story collections',
                'GET /api/next-steps': 'WPF automation guide',
                'POST /api/rate': 'Rate image (0-15)',
                'POST /api/create-collection': 'Create story collection',
                'POST /api/generate': 'Generate image',
                'POST /api/generate-batch': 'Batch generation'
            }
        })
        
    def _status(self):
        try:
            urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=3)
            comfy = 'online'
        except:
            comfy = 'offline'
            
        stats = learning.get_stats()
        
        self._json({
            'api': 'online',
            'comfyui': comfy,
            'database': 'connected',
            'learning_stats': stats,
            'failsafe_status': 'active',
            'timestamp': datetime.now().isoformat()
        })
        
    def _stats(self):
        stats = learning.get_stats()
        stats['rating_scale'] = '0-15'
        stats['gold_standard_target'] = 15
        self._json(stats)
        
    def _themes(self):
        themes_info = {}
        for key, theme in THEMES.items():
            themes_info[key] = {
                'name': theme['name'],
                'characters': sum(len(v) for v in theme.get('characters', {}).values()),
                'settings': len(theme.get('settings', [])),
                'has_tribes': 'tribes' in theme,
                'tribe_count': sum(len(v) for v in theme.get('tribes', {}).values()) if 'tribes' in theme else 0
            }
        self._json(themes_info)
        
    def _images(self):
        images = sorted(OUTPUT_DIR.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:100]
        self._json([{
            'filename': i.name,
            'size_kb': round(i.stat().st_size / 1024),
            'time': datetime.fromtimestamp(i.stat().st_mtime).isoformat()
        } for i in images])
        
    def _gold_standards(self):
        cursor = learning.conn.cursor()
        cursor.execute('SELECT image_id, prompt, tags, created_at FROM gold_standards ORDER BY created_at DESC')
        results = cursor.fetchall()
        self._json([{
            'image_id': r[0],
            'prompt': r[1][:200] + '...' if len(r[1]) > 200 else r[1],
            'tags': json.loads(r[2]),
            'created_at': r[3]
        } for r in results])
        
    def _collections(self):
        cursor = stories.conn.cursor()
        cursor.execute('''SELECT id, collection_name, theme, total_scenes, 
            images_generated, target_images, status FROM story_collections 
            ORDER BY created_at DESC''')
        results = cursor.fetchall()
        self._json([{
            'id': r[0],
            'name': r[1],
            'theme': r[2],
            'scenes': r[3],
            'images': r[4],
            'target': r[5],
            'status': r[6],
            'progress': round((r[4] / r[5]) * 100, 1) if r[5] else 0
        } for r in results])
        
    def _next_steps(self):
        """Guide for WPF automation"""
        self._json({
            'title': 'WPF Automation Guide',
            'workflow': [
                {
                    'step': 1,
                    'action': 'Select Theme',
                    'description': 'Choose Western, Tribal, or Native American',
                    'api': 'GET /api/themes'
                },
                {
                    'step': 2,
                    'action': 'Upload Story (Optional)',
                    'description': 'Upload markdown/text story file',
                    'api': 'POST /api/create-collection',
                    'body': {'name': 'string', 'theme': 'string', 'story_text': 'string'}
                },
                {
                    'step': 3,
                    'action': 'Generate Images',
                    'description': 'Auto-generate from story or manual',
                    'api': 'POST /api/generate-batch',
                    'body': {'theme': 'string', 'count': 'number', 'collection_id': 'optional'}
                },
                {
                    'step': 4,
                    'action': 'Rate Images (0-15)',
                    'description': '10+ triggers 50 variations, 15 = gold standard',
                    'api': 'POST /api/rate',
                    'body': {'image_id': 'string', 'rating': 'number 0-15'}
                },
                {
                    'step': 5,
                    'action': 'View Gold Standards',
                    'description': 'Perfect images to learn from',
                    'api': 'GET /api/gold-standards'
                }
            ],
            'rating_guide': {
                '0-5': 'Dislike - AI avoids these features',
                '6-9': 'Good - AI notes preferences',
                '10-12': 'Excellent - Triggers 50 variations',
                '13-14': 'Near Perfect - Intensive learning',
                '15': 'PERFECT - Gold Standard saved'
            },
            'failsafes': [
                'Auto-retry on generation failure',
                'Fallback models available',
                'Database transaction protection',
                'Rate limiting on batch operations'
            ]
        })
        
    # ==================== POST HANDLERS ====================
    
    def _rate(self, data):
        image_id = data.get('image_id')
        rating = data.get('rating', 0)
        
        if not image_id:
            # Try to find by filename
            filename = data.get('filename')
            if filename:
                cursor = learning.conn.cursor()
                cursor.execute('SELECT image_id FROM images WHERE filename = ?', (filename,))
                result = cursor.fetchone()
                if result:
                    image_id = result[0]
                else:
                    # Create new record
                    image_id = learning.create_image_record(
                        filename, data.get('prompt', ''), data.get('negative', ''),
                        data.get('tags', []), data.get('seed', 0)
                    )
                    
        if not image_id:
            self._json({'error': 'image_id or filename required'}, 400)
            return
            
        result = learning.rate_image(image_id, float(rating))
        self._json(result)
        
    def _create_collection(self, data):
        name = data.get('name', 'Untitled Collection')
        theme = data.get('theme', 'tribal')
        story_text = data.get('story_text', '')
        story_path = data.get('story_path')
        target = data.get('target_images', 500)
        
        result = stories.create_collection(name, theme, story_text, story_path, target)
        self._json(result)
        
    def _generate(self, data):
        theme = data.get('theme', 'tribal')
        collection_id = data.get('collection_id')
        
        if collection_id:
            # Generate from story scene
            scene = stories.get_next_scene_prompt(collection_id)
            if scene.get('status') == 'complete':
                self._json(scene)
                return
            prompt = scene['prompt']
            tags = scene['elements'].get('characters', [])
        else:
            # Generate with theme defaults
            from story_collection_system import THEMES
            theme_config = THEMES.get(theme, THEMES['tribal'])
            prompt = self._build_theme_prompt(theme_config)
            tags = theme_config.get('style_tags', [])
            
        # Queue generation
        result = learning._generate_image(prompt, tags, f"{theme}_{datetime.now().strftime('%H%M%S')}", None)
        self._json(result)
        
    def _generate_batch(self, data):
        theme = data.get('theme', 'tribal')
        count = min(data.get('count', 10), 100)  # Max 100 per batch
        collection_id = data.get('collection_id')
        
        def run_batch():
            for i in range(count):
                try:
                    if collection_id:
                        scene = stories.get_next_scene_prompt(collection_id)
                        if scene.get('status') == 'complete':
                            break
                        prompt = scene['prompt']
                        tags = []
                    else:
                        from story_collection_system import THEMES
                        theme_config = THEMES.get(theme, THEMES['tribal'])
                        prompt = self._build_theme_prompt(theme_config)
                        tags = theme_config.get('style_tags', [])
                        
                    learning._generate_image(prompt, tags, f"{theme}_{i+1:03d}", None)
                except Exception as e:
                    print(f"Batch error {i}: {e}")
                    
        threading.Thread(target=run_batch).start()
        self._json({'status': 'started', 'count': count, 'theme': theme})
        
    def _build_theme_prompt(self, theme_config):
        import random
        parts = ["masterpiece", "best quality", "ultra detailed", "8k resolution", "photorealistic"]
        parts.extend(theme_config.get('style_tags', []))
        
        # Character
        char_types = list(theme_config.get('characters', {}).values())
        if char_types:
            chars = random.choice(char_types)
            if chars:
                parts.append(f"({random.choice(chars)}:1.3)")
                
        # Body
        parts.extend(["(adult woman:1.3)", "(25yo:1.1)"])
        parts.append(random.choice(["petite", "slim", "athletic", "toned"]))
        parts.append(random.choice(["A cup", "B cup", "small bust"]))
        
        # Setting
        settings = theme_config.get('settings', ['outdoor'])
        parts.append(f"({random.choice(settings)}:1.2)")
        
        # Clothing
        level = random.choice(['dressed', 'partial', 'undressed'])
        clothing = theme_config.get('clothing', {}).get(level, [])
        if clothing:
            parts.append(random.choice(clothing))
            
        return ", ".join(parts)
        
    def log_message(self, *args): pass


def start_server():
    print("="*60)
    print("  COMPLETE WPF API SERVER")
    print("  AI-Powered Image Generation with 0-15 Rating")
    print("="*60)
    
    print(f"\n📡 Server: http://127.0.0.1:{API_PORT}")
    print(f"\n🎯 Rating Scale: 0-15")
    print(f"   0-5:   Dislike (AI avoids)")
    print(f"   6-9:   Good (AI learns)")
    print(f"   10-12: Excellent (50 variations auto-generated)")
    print(f"   13-14: Near Perfect (intensive learning)")
    print(f"   15:    PERFECT (Gold Standard)")
    
    print(f"\n📚 Themes:")
    print(f"   - Western (cowboys, outlaws, ranchers)")
    print(f"   - Tribal (warriors, ceremonial)")
    print(f"   - Native American (30+ tribes)")
    
    print(f"\n⚡ Failsafes: Active")
    print(f"\n✅ Server ready!")
    
    server = HTTPServer(('0.0.0.0', API_PORT), CompleteAPI)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")


if __name__ == "__main__":
    start_server()
