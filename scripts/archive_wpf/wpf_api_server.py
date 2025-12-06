"""
WPF API Server
REST API for WPF GUI integration with ComfyUI
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
from pathlib import Path
import threading

from preference_system import PreferenceSystem, get_dropdown_options
from smart_collection_generator import SmartGenerator

API_PORT = 8190
COMFY_URL = "http://localhost:8188"

class WPFAPIHandler(BaseHTTPRequestHandler):
    """Handle API requests from WPF application"""
    
    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
        
    def _read_json(self) -> dict:
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        return json.loads(body.decode('utf-8')) if body else {}
        
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_GET(self):
        """Handle GET requests"""
        path = urllib.parse.urlparse(self.path).path
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        
        # ==================== DROPDOWN OPTIONS ====================
        if path == '/api/options':
            # Return all dropdown options for UI
            options = get_dropdown_options()
            self._send_json(options)
            
        # ==================== STATISTICS ====================
        elif path == '/api/stats':
            pref = PreferenceSystem()
            stats = pref.get_stats()
            pref.close()
            self._send_json(stats)
            
        # ==================== PREFERRED TAGS ====================
        elif path == '/api/preferred-tags':
            limit = int(query.get('limit', [20])[0])
            pref = PreferenceSystem()
            tags = pref.get_preferred_tags(limit=limit)
            pref.close()
            self._send_json({
                'tags': [{'tag': t[0], 'weight': t[1], 'likes': t[2], 'dislikes': t[3]} for t in tags]
            })
            
        # ==================== AVOIDED TAGS ====================
        elif path == '/api/avoided-tags':
            limit = int(query.get('limit', [20])[0])
            pref = PreferenceSystem()
            tags = pref.get_avoided_tags(limit=limit)
            pref.close()
            self._send_json({
                'tags': [{'tag': t[0], 'weight': t[1], 'likes': t[2], 'dislikes': t[3]} for t in tags]
            })
            
        # ==================== COMFYUI STATUS ====================
        elif path == '/api/comfyui/status':
            try:
                import urllib.request
                resp = urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
                self._send_json({'status': 'running', 'url': COMFY_URL})
            except:
                self._send_json({'status': 'offline', 'url': COMFY_URL})
                
        # ==================== LIST IMAGES ====================
        elif path == '/api/images':
            output_dir = Path(r"G:\Github\ComfyUI\output")
            images = []
            for img in sorted(output_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:100]:
                images.append({
                    'filename': img.name,
                    'path': str(img),
                    'size_kb': round(img.stat().st_size / 1024, 1),
                    'modified': img.stat().st_mtime
                })
            self._send_json({'images': images, 'total': len(images)})
            
        else:
            self._send_json({'error': 'Not found'}, 404)
            
    def do_POST(self):
        """Handle POST requests"""
        path = urllib.parse.urlparse(self.path).path
        data = self._read_json()
        
        # ==================== RATE IMAGE ====================
        if path == '/api/rate':
            filename = data.get('filename')
            rating = data.get('rating', 0)
            
            if not filename:
                self._send_json({'error': 'filename required'}, 400)
                return
                
            pref = PreferenceSystem()
            pref.rate_image(filename, rating)
            pref.close()
            self._send_json({'status': 'success', 'filename': filename, 'rating': rating})
            
        # ==================== ENHANCE PROMPT ====================
        elif path == '/api/enhance-prompt':
            prompt = data.get('prompt', '')
            style = data.get('style', 'general')
            
            pref = PreferenceSystem()
            enhanced = pref.enhance_prompt(prompt, style)
            pref.close()
            self._send_json({'original': prompt, 'enhanced': enhanced})
            
        # ==================== BUILD PROMPT FROM SELECTIONS ====================
        elif path == '/api/build-prompt':
            selections = data.get('selections', {})
            
            pref = PreferenceSystem()
            prompt = pref.build_prompt_from_selections(selections)
            pref.close()
            self._send_json({'prompt': prompt, 'selections': selections})
            
        # ==================== CHAT LEARNING ====================
        elif path == '/api/chat-learn':
            message = data.get('message', '')
            
            pref = PreferenceSystem()
            preferences = pref.learn_from_chat(message)
            pref.close()
            self._send_json({'extracted_preferences': preferences, 'message': message})
            
        # ==================== GENERATE SINGLE IMAGE ====================
        elif path == '/api/generate':
            selections = data.get('selections', {})
            style = data.get('style', 'tribal')
            
            def generate_async():
                gen = SmartGenerator()
                gen.generate_collection(
                    'wpf_single',
                    style,
                    1,
                    selections
                )
                gen.close()
                
            thread = threading.Thread(target=generate_async)
            thread.start()
            self._send_json({'status': 'queued', 'style': style})
            
        # ==================== GENERATE COLLECTION ====================
        elif path == '/api/generate-collection':
            name = data.get('name', 'collection')
            style = data.get('style', 'tribal')
            count = data.get('count', 10)
            selections = data.get('selections', {})
            
            def generate_async():
                gen = SmartGenerator()
                gen.generate_collection(name, style, count, selections)
                gen.close()
                
            thread = threading.Thread(target=generate_async)
            thread.start()
            self._send_json({
                'status': 'started',
                'name': name,
                'style': style,
                'count': count
            })
            
        # ==================== BATCH RATE ====================
        elif path == '/api/batch-rate':
            ratings = data.get('ratings', [])  # [{filename: str, rating: int}, ...]
            
            pref = PreferenceSystem()
            for item in ratings:
                pref.rate_image(item['filename'], item['rating'])
            pref.close()
            self._send_json({'status': 'success', 'rated': len(ratings)})
            
        else:
            self._send_json({'error': 'Not found'}, 404)
            
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[API] {args[0]}")


def start_server():
    """Start the API server"""
    server = HTTPServer(('127.0.0.1', API_PORT), WPFAPIHandler)
    print(f"="*60)
    print(f"  WPF API SERVER")
    print(f"  Running on http://127.0.0.1:{API_PORT}")
    print(f"="*60)
    print(f"\n📡 Available Endpoints:")
    print(f"   GET  /api/options          - Dropdown options")
    print(f"   GET  /api/stats            - Learning statistics")
    print(f"   GET  /api/preferred-tags   - Top preferred tags")
    print(f"   GET  /api/avoided-tags     - Avoided tags")
    print(f"   GET  /api/comfyui/status   - ComfyUI status")
    print(f"   GET  /api/images           - List generated images")
    print(f"   POST /api/rate             - Rate an image")
    print(f"   POST /api/enhance-prompt   - AI enhance prompt")
    print(f"   POST /api/build-prompt     - Build from selections")
    print(f"   POST /api/chat-learn       - Learn from chat")
    print(f"   POST /api/generate         - Generate single image")
    print(f"   POST /api/generate-collection - Generate collection")
    print(f"   POST /api/batch-rate       - Batch rate images")
    print(f"\n✅ Server ready!")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()


if __name__ == "__main__":
    start_server()
