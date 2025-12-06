"""
UNIFIED WPF API
================
Single consolidated API for WPF Dashboard integration.
Replaces: complete_wpf_api.py, integrated_wpf_api.py, master_wpf_api.py, 
          wpf_api_server.py, wpf_bridge.py

Port: 8190
"""
import json
import sqlite3
import threading
import requests
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import logging

# Configuration
PORT = 8190
DATA_DIR = Path(r"c:\Users\Admin\civitai\data")
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DB_PATH = DATA_DIR / "preferences.db"

# Service endpoints
SERVICES = {
    "gateway": "http://localhost:8300",
    "rating": "http://localhost:8196",
    "training": "http://localhost:8230",
    "dataset": "http://localhost:8211",
    "learning": "http://localhost:8225",
    "orchestrator": "http://localhost:8210",
    "captioner": "http://localhost:8207",
    "comfyui": "http://localhost:8188"
}

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [WPF-API] %(message)s')
logger = logging.getLogger(__name__)


class UnifiedDatabase:
    """Unified database access for WPF"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
    
    def get_stats(self) -> dict:
        """Get overall statistics"""
        with self.lock:
            cursor = self.conn.cursor()
            
            stats = {}
            
            # Image stats
            cursor.execute('SELECT COUNT(*) FROM images')
            stats['total_images'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM images WHERE rating > 0')
            stats['rated_images'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(rating) FROM images WHERE rating > 0')
            avg = cursor.fetchone()[0]
            stats['avg_rating'] = round(avg, 2) if avg else 0
            
            # Tag stats
            cursor.execute('SELECT COUNT(*) FROM tag_weights WHERE likes + dislikes > 0')
            stats['learned_tags'] = cursor.fetchone()[0]
            
            return stats
    
    def get_recent_images(self, limit: int = 20) -> list:
        """Get recent images"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT filename, prompt, rating, created_at 
                FROM images 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]


db = UnifiedDatabase()


def proxy_request(service: str, path: str, method: str = "GET", body: dict = None) -> dict:
    """Proxy request to a service"""
    if service not in SERVICES:
        return {"error": f"Unknown service: {service}"}
    
    url = f"{SERVICES[service]}{path}"
    
    try:
        if method == "GET":
            resp = requests.get(url, timeout=10)
        else:
            resp = requests.post(url, json=body, timeout=30)
        
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Service {service} not available"}
    except Exception as e:
        return {"error": str(e)}


def get_system_health() -> dict:
    """Check health of all services - fast version"""
    health = {
        "services": {},
        "overall": "healthy"
    }
    
    # Only check core services with very short timeout
    core_services = ["rating", "training", "learning", "dataset"]
    for name in core_services:
        if name not in SERVICES:
            continue
        url = SERVICES[name]
        try:
            resp = requests.get(f"{url}/", timeout=0.5)
            health["services"][name] = {
                "status": "online" if resp.status_code == 200 else "error",
                "port": url.split(":")[-1]
            }
        except:
            health["services"][name] = {"status": "offline"}
            health["overall"] = "degraded"
    
    return health


class WPFApiHandler(BaseHTTPRequestHandler):
    """HTTP Handler for WPF API"""
    
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")
    
    def send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        path = self.path.split('?')[0]
        query = parse_qs(urlparse(self.path).query)
        
        # Root - API info
        if path == '/':
            self.send_json({
                "service": "Unified WPF API",
                "version": "2.0.0",
                "port": PORT,
                "endpoints": {
                    "health": "GET /api/health",
                    "stats": "GET /api/stats",
                    "images": "GET /api/images",
                    "services": "GET /api/services",
                    "training": "GET /api/training/status",
                    "chat": "POST /api/chat"
                }
            })
        
        # Health check
        elif path == '/api/health':
            self.send_json(get_system_health())
        
        # Overall stats
        elif path == '/api/stats':
            stats = db.get_stats()
            self.send_json({"success": True, **stats})
        
        # Recent images
        elif path == '/api/images':
            limit = int(query.get('limit', [20])[0])
            images = db.get_recent_images(limit)
            self.send_json({"success": True, "images": images})
        
        # Service status
        elif path == '/api/services':
            health = get_system_health()
            self.send_json({"success": True, **health})
        
        # Training status (proxy)
        elif path == '/api/training/status':
            result = proxy_request("training", "/api/status")
            self.send_json(result)
        
        # Rating stats (proxy)
        elif path == '/api/rating/stats':
            result = proxy_request("rating", "/api/stats")
            self.send_json(result)
        
        # Learning stats (proxy)
        elif path == '/api/learning/stats':
            result = proxy_request("learning", "/api/stats")
            self.send_json(result)
        
        # Dataset list (proxy)
        elif path == '/api/datasets':
            result = proxy_request("dataset", "/api/datasets")
            self.send_json(result)
        
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = self.path.split('?')[0]
        
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = {}
        if content_length > 0:
            body = json.loads(self.rfile.read(content_length).decode())
        
        # Chat with AI
        if path == '/api/chat':
            message = body.get('message', '')
            result = proxy_request("learning", "/api/chat", "POST", {"message": message})
            self.send_json(result)
        
        # Rate image
        elif path == '/api/rate':
            filename = body.get('filename')
            rating = body.get('rating')
            result = proxy_request("rating", "/api/rate", "POST", body)
            self.send_json(result)
        
        # Start training
        elif path == '/api/training/start':
            result = proxy_request("training", "/api/create", "POST", body)
            self.send_json(result)
        
        # Generate prompt
        elif path == '/api/prompt/generate':
            result = proxy_request("learning", "/api/prompt", "GET")
            self.send_json(result)
        
        # Build dataset
        elif path == '/api/dataset/build':
            result = proxy_request("dataset", "/api/dataset/build", "POST", body)
            self.send_json(result)
        
        else:
            self.send_json({"error": "Not found"}, 404)


def run_server():
    """Run the WPF API server"""
    server = HTTPServer(('0.0.0.0', PORT), WPFApiHandler)
    logger.info(f"Unified WPF API running on port {PORT}")
    logger.info(f"Endpoints: http://localhost:{PORT}/")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.shutdown()


if __name__ == '__main__':
    print("="*60)
    print("  UNIFIED WPF API")
    print("  Port: 8190")
    print("="*60)
    run_server()
