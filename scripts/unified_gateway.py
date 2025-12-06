"""
UNIFIED API GATEWAY
====================
Single entry point for all LoraForge APIs
Routes requests to appropriate backend services

Port: 8300
"""
import json
import requests
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, urlencode
from datetime import datetime

PORT = 8300

# Service Registry - All backend services
SERVICE_REGISTRY = {
    "frontier": {"port": 8195, "name": "Frontier Stories API", "prefix": "/api/frontier"},
    "rating_studio": {"port": 8196, "name": "Rating Studio Ultra", "prefix": "/api/rating"},
    "story": {"port": 8197, "name": "Story Generator API", "prefix": "/api/story"},
    "country": {"port": 8199, "name": "Country Rating API", "prefix": "/api/country"},
    "guardrails": {"port": 8200, "name": "Guardrails Engine", "prefix": "/api/guardrails"},
    "admin": {"port": 8201, "name": "Admin System", "prefix": "/api/admin"},
    "playwright": {"port": 8203, "name": "Playwright Automation", "prefix": "/api/playwright"},
    "pipeline": {"port": 8205, "name": "Full Pipeline", "prefix": "/api/pipeline"},
    "video": {"port": 8206, "name": "Video Processing", "prefix": "/api/video"},
    "captioner": {"port": 8207, "name": "Auto-Captioner", "prefix": "/api/captioner"},
    "rating_ui": {"port": 8208, "name": "Rating UI API", "prefix": "/api/rating_ui"},
    "orchestrator": {"port": 8210, "name": "Master Orchestrator", "prefix": "/api/orchestrator"},
    "dataset_builder": {"port": 8211, "name": "Dataset Builder", "prefix": "/api/dataset"},
    "voice": {"port": 8212, "name": "Voice Integration", "prefix": "/api/voice"},
    "comfyui": {"port": 8213, "name": "ComfyUI Automation", "prefix": "/api/comfyui"},
    "training": {"port": 8214, "name": "Training Scheduler", "prefix": "/api/training"},
    "deployer": {"port": 8215, "name": "Model Deployer", "prefix": "/api/deployer"},
    "quality": {"port": 8216, "name": "Quality Gate", "prefix": "/api/quality"},
    "launcher": {"port": 8217, "name": "External Launcher", "prefix": "/api/launcher"},
    "realtime": {"port": 8218, "name": "Real-time Hub", "prefix": "/api/realtime"},
    "voice_unified": {"port": 8220, "name": "Voice Tools Unified", "prefix": "/api/voice_tools"},
    "workflows": {"port": 8221, "name": "Workflow Manager", "prefix": "/api/workflows"},
    "dataset_scheduler": {"port": 8222, "name": "Dataset Auto-Scheduler", "prefix": "/api/dataset_auto"},
    "gallery_scheduler": {"port": 8223, "name": "Gallery Auto-Scheduler", "prefix": "/api/gallery"},
    "backup_scheduler": {"port": 8224, "name": "Backup Auto-Scheduler", "prefix": "/api/backup"},
    "learning": {"port": 8225, "name": "AI Learning Brain", "prefix": "/api/learning"},
    "stories": {"port": 8226, "name": "Story Collections", "prefix": "/api/stories"},
    "lora_training": {"port": 8230, "name": "LoRA Training", "prefix": "/api/training"},
}

# Service health cache
service_health = {}
health_check_interval = 30  # seconds
last_health_check = 0

# Request metrics
metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "requests_by_service": {},
    "started_at": datetime.now().isoformat()
}


def check_service_health(service_key, config):
    """Check if a service is healthy"""
    try:
        url = f"http://127.0.0.1:{config['port']}/"
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except:
        return False


def update_all_health():
    """Update health status for all services"""
    global service_health, last_health_check
    
    for key, config in SERVICE_REGISTRY.items():
        service_health[key] = {
            "healthy": check_service_health(key, config),
            "checked_at": datetime.now().isoformat()
        }
    
    last_health_check = time.time()


def get_service_for_path(path):
    """Find which service should handle a path"""
    for key, config in SERVICE_REGISTRY.items():
        if path.startswith(config["prefix"]):
            return key, config
    return None, None


def proxy_request(method, service_config, path, headers=None, body=None, query=None):
    """Proxy a request to a backend service"""
    # Some services (Flask) need the full path, others need prefix stripped
    # Flask services: orchestrator, dataset_builder, etc. - keep full path
    flask_services = {'orchestrator', 'dataset_builder', 'deployer', 'quality', 'launcher', 'realtime'}
    
    if service_config.get('name', '').lower().replace(' ', '_').replace('-', '_') in flask_services or \
       any(fs in path.lower() for fs in flask_services):
        # Keep full path for Flask services
        backend_path = path
    else:
        # Remove the gateway prefix for standard http.server services
        prefix = service_config["prefix"]
        backend_path = path[len(prefix):] if path.startswith(prefix) else path
        if not backend_path:
            backend_path = "/"
    
    url = f"http://127.0.0.1:{service_config['port']}{backend_path}"
    if query:
        url += f"?{query}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=body, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, data=body, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            return None, 405, "Method not allowed"
        
        return response.content, response.status_code, response.headers.get('Content-Type', 'application/json')
    
    except requests.exceptions.ConnectionError:
        return json.dumps({"error": "Service unavailable", "service": service_config["name"]}).encode(), 503, 'application/json'
    except requests.exceptions.Timeout:
        return json.dumps({"error": "Service timeout", "service": service_config["name"]}).encode(), 504, 'application/json'
    except Exception as e:
        return json.dumps({"error": str(e)}).encode(), 500, 'application/json'


class GatewayAPI(BaseHTTPRequestHandler):
    """Unified Gateway API Handler"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _proxy_response(self, content, status, content_type):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content)
    
    def do_OPTIONS(self):
        self._json({})
    
    def _handle_request(self, method):
        global metrics
        metrics["total_requests"] += 1
        
        parsed = urlparse(self.path)
        path = parsed.path
        query = parsed.query
        
        # Gateway endpoints
        if path == '/':
            self._handle_root()
            return
        elif path == '/health':
            self._handle_health()
            return
        elif path == '/services':
            self._handle_services()
            return
        elif path == '/metrics':
            self._handle_metrics()
            return
        
        # Find service for this path
        service_key, service_config = get_service_for_path(path)
        
        if not service_config:
            metrics["failed_requests"] += 1
            self._json({"error": "No service found for path", "path": path}, 404)
            return
        
        # Track metrics
        if service_key not in metrics["requests_by_service"]:
            metrics["requests_by_service"][service_key] = 0
        metrics["requests_by_service"][service_key] += 1
        
        # Get request body for POST/PUT
        body = None
        if method in ["POST", "PUT"]:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length else None
        
        # Proxy the request
        content, status, content_type = proxy_request(
            method, service_config, path,
            headers=dict(self.headers),
            body=body,
            query=query
        )
        
        if status < 400:
            metrics["successful_requests"] += 1
        else:
            metrics["failed_requests"] += 1
        
        self._proxy_response(content, status, content_type)
    
    def do_GET(self):
        self._handle_request("GET")
    
    def do_POST(self):
        self._handle_request("POST")
    
    def do_PUT(self):
        self._handle_request("PUT")
    
    def do_DELETE(self):
        self._handle_request("DELETE")
    
    def _handle_root(self):
        """Gateway info and quick health"""
        global last_health_check
        
        # Update health if stale
        if time.time() - last_health_check > health_check_interval:
            update_all_health()
        
        online = sum(1 for h in service_health.values() if h.get("healthy"))
        total = len(SERVICE_REGISTRY)
        
        self._json({
            "service": "Unified API Gateway",
            "version": "1.0",
            "port": PORT,
            "services_online": online,
            "services_total": total,
            "health_percent": round(online / total * 100) if total > 0 else 0,
            "endpoints": {
                "/": "Gateway info",
                "/health": "Full health check",
                "/services": "List all services",
                "/metrics": "Request metrics"
            },
            "routing": "Use /api/{service}/* to route to backend"
        })
    
    def _handle_health(self):
        """Full health check of all services"""
        update_all_health()
        
        results = {}
        for key, config in SERVICE_REGISTRY.items():
            health = service_health.get(key, {})
            results[key] = {
                "name": config["name"],
                "port": config["port"],
                "prefix": config["prefix"],
                "healthy": health.get("healthy", False),
                "checked_at": health.get("checked_at")
            }
        
        online = sum(1 for r in results.values() if r["healthy"])
        
        self._json({
            "status": "healthy" if online > len(results) * 0.8 else "degraded" if online > 0 else "unhealthy",
            "online": online,
            "total": len(results),
            "services": results
        })
    
    def _handle_services(self):
        """List all registered services"""
        services = []
        for key, config in SERVICE_REGISTRY.items():
            health = service_health.get(key, {})
            services.append({
                "key": key,
                "name": config["name"],
                "port": config["port"],
                "prefix": config["prefix"],
                "healthy": health.get("healthy", False),
                "url": f"http://127.0.0.1:{config['port']}"
            })
        
        self._json({"services": services, "count": len(services)})
    
    def _handle_metrics(self):
        """Return request metrics"""
        self._json(metrics)
    
    def log_message(self, *args): pass


def health_check_loop():
    """Background health check loop"""
    while True:
        update_all_health()
        time.sleep(health_check_interval)


def main():
    print("=" * 60)
    print("  UNIFIED API GATEWAY")
    print("  Port:", PORT)
    print("=" * 60)
    
    # Initial health check
    print("\nChecking services...")
    update_all_health()
    
    online = sum(1 for h in service_health.values() if h.get("healthy"))
    total = len(SERVICE_REGISTRY)
    
    print(f"\nServices: {online}/{total} online ({round(online/total*100)}%)")
    print("\nOnline services:")
    for key, config in SERVICE_REGISTRY.items():
        if service_health.get(key, {}).get("healthy"):
            print(f"  [{config['port']}] {config['name']}")
    
    print("\nRouting prefixes:")
    for key, config in SERVICE_REGISTRY.items():
        print(f"  {config['prefix']}/* -> :{config['port']}")
    
    print(f"\nGateway Endpoints:")
    print(f"  GET  /          - Gateway info")
    print(f"  GET  /health    - Full health check")
    print(f"  GET  /services  - List all services")
    print(f"  GET  /metrics   - Request metrics")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    # Start background health checker
    health_thread = threading.Thread(target=health_check_loop, daemon=True)
    health_thread.start()
    
    # Start server
    server = HTTPServer(('127.0.0.1', PORT), GatewayAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
