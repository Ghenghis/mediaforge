"""
Integrated WPF API Server
Complete AI-powered image generation with learning
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
from pathlib import Path
import threading
import random
import time
from datetime import datetime

from ai_learning_brain import AILearningBrain

API_PORT = 8190
COMFY_URL = "http://localhost:8188"
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
CONFIG_PATH = Path(r"c:\Users\Admin\civitai\data\complete_tags_config.json")

# Global brain instance
brain = AILearningBrain()

with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

class IntegratedAPI(BaseHTTPRequestHandler):
    
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
            '/api/status': self._get_status,
            '/api/stats': self._get_stats,
            '/api/config': self._get_config,
            '/api/model': self._get_model,
            '/api/images': self._get_images,
            '/api/preferred': self._get_preferred,
            '/api/avoided': self._get_avoided,
        }
        
        handler = routes.get(path)
        if handler:
            handler()
        else:
            self._json({'error': 'not found'}, 404)
            
    def do_POST(self):
        path = self.path
        data = self._body()
        
        routes = {
            '/api/rate': self._rate_image,
            '/api/chat': self._chat_learn,
            '/api/generate': self._generate_image,
            '/api/generate-batch': self._generate_batch,
            '/api/dataset': self._create_dataset,
            '/api/smart-prompt': self._smart_prompt,
        }
        
        handler = routes.get(path)
        if handler:
            handler(data)
        else:
            self._json({'error': 'not found'}, 404)
            
    # ==================== GET HANDLERS ====================
    
    def _get_status(self):
        try:
            urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=3)
            comfy_status = 'online'
        except:
            comfy_status = 'offline'
            
        stats = brain.get_learning_stats()
        self._json({
            'api': 'online',
            'comfyui': comfy_status,
            'learning': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    def _get_stats(self):
        self._json(brain.get_learning_stats())
        
    def _get_config(self):
        self._json(CONFIG)
        
    def _get_model(self):
        self._json(brain.get_preference_model())
        
    def _get_images(self):
        images = sorted(OUTPUT_DIR.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:200]
        self._json([{
            'filename': i.name,
            'size_kb': round(i.stat().st_size / 1024),
            'time': i.stat().st_mtime
        } for i in images])
        
    def _get_preferred(self):
        model = brain.get_preference_model()
        self._json(model.get('top_liked', []))
        
    def _get_avoided(self):
        model = brain.get_preference_model()
        self._json(model.get('top_disliked', []))
        
    # ==================== POST HANDLERS ====================
    
    def _rate_image(self, data):
        result = brain.rate_image(data['filename'], data['rating'])
        self._json(result)
        
    def _chat_learn(self, data):
        result = brain.learn_from_chat(data['message'])
        self._json(result)
        
    def _smart_prompt(self, data):
        style = data.get('style', 'tribal')
        positive, negative, tags = brain.generate_smart_prompt(style)
        self._json({'positive': positive, 'negative': negative, 'tags': tags})
        
    def _create_dataset(self, data):
        name = data.get('name')
        result = brain.generate_dataset(name)
        self._json(result)
        
    def _generate_image(self, data):
        style = data.get('style', 'tribal')
        prefix = data.get('prefix', 'wpf_gen')
        
        positive, negative, tags = brain.generate_smart_prompt(style)
        result = self._do_generate(positive, negative, tags, prefix)
        self._json(result)
        
    def _generate_batch(self, data):
        count = data.get('count', 10)
        style = data.get('style', 'tribal')
        prefix = data.get('prefix', 'batch')
        
        def run_batch():
            for i in range(count):
                positive, negative, tags = brain.generate_smart_prompt(style)
                self._do_generate(positive, negative, tags, f"{prefix}_{i+1:03d}")
                
        threading.Thread(target=run_batch).start()
        self._json({'status': 'started', 'count': count})
        
    def _do_generate(self, positive, negative, tags, prefix):
        seed = random.randint(0, 2**32)
        workflow = {
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
        }
        
        try:
            data = json.dumps({"prompt": workflow}).encode()
            req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
            resp = urllib.request.urlopen(req, timeout=30)
            prompt_id = json.loads(resp.read()).get('prompt_id')
            
            # Wait for completion
            start = time.time()
            while time.time() - start < 180:
                try:
                    resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
                    if prompt_id in json.loads(resp.read()):
                        filename = f"{prefix}_{seed}.png"
                        # Save to database
                        cursor = brain.conn.cursor()
                        cursor.execute('''INSERT OR REPLACE INTO images (filename, prompt, negative, tags, model, seed, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (filename, positive, negative, json.dumps(tags), 'CyberRealistic', seed, datetime.now().isoformat()))
                        brain.conn.commit()
                        return {'status': 'success', 'filename': filename, 'seed': seed}
                except:
                    pass
                time.sleep(2)
            return {'status': 'timeout'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
            
    def log_message(self, *args): pass


def run_tests():
    """Run all system tests"""
    print("="*60)
    print("  COMPLETE SYSTEM VERIFICATION")
    print("="*60)
    
    results = {}
    
    # Test 1: AI Brain
    print("\n🧠 Testing AI Learning Brain...")
    from ai_learning_brain import test_ai_brain
    results['ai_brain'] = test_ai_brain()
    
    # Test 2: Chat Memory
    print("\n💬 Testing Chat Memory System...")
    from chat_memory_system import test_chat_memory
    results['chat_memory'] = test_chat_memory()
    
    # Test 3: Tag Learning
    print("\n🏷️ Testing Tag Learning...")
    from test_learning import test_learning
    results['tag_learning'] = test_learning()
    
    # Summary
    print("\n" + "="*60)
    print("  SYSTEM VERIFICATION COMPLETE")
    print("="*60)
    
    all_pass = all(results.values())
    
    for test, passed in results.items():
        print(f"   {test}: {'✅' if passed else '❌'}")
        
    print(f"\n   Overall: {'✅ ALL SYSTEMS OPERATIONAL' if all_pass else '❌ SOME SYSTEMS FAILED'}")
    
    return all_pass


def start_server():
    print("="*60)
    print("  INTEGRATED WPF API SERVER")
    print("  AI-Powered Image Generation with Learning")
    print("="*60)
    
    print(f"\n📡 Server: http://127.0.0.1:{API_PORT}")
    print(f"\n🔗 Endpoints:")
    print(f"   GET  /api/status    - System status")
    print(f"   GET  /api/stats     - Learning statistics")
    print(f"   GET  /api/config    - All tag options")
    print(f"   GET  /api/model     - Preference model")
    print(f"   GET  /api/images    - Generated images")
    print(f"   GET  /api/preferred - Liked tags")
    print(f"   GET  /api/avoided   - Disliked tags")
    print(f"   POST /api/rate      - Rate image (learn)")
    print(f"   POST /api/chat      - Chat learning")
    print(f"   POST /api/generate  - Generate image")
    print(f"   POST /api/generate-batch - Batch generate")
    print(f"   POST /api/dataset   - Create dataset")
    print(f"   POST /api/smart-prompt - AI prompt")
    
    print(f"\n✅ Server ready!")
    
    server = HTTPServer(('0.0.0.0', API_PORT), IntegratedAPI)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_tests()
    else:
        start_server()
