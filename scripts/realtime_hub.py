"""
REAL-TIME HUB (WebSocket Server)
=================================
Provides real-time updates to WPF dashboard via WebSocket
Broadcasts: service status, training progress, generation events

Port: 8218 (HTTP) / 8219 (WebSocket)
"""
import json
import asyncio
import threading
import time
import requests
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# WebSocket support
try:
    import websockets
    from websockets.server import serve
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("WARNING: websockets not installed. Run: pip install websockets")

# Configuration
HTTP_PORT = 8218
WS_PORT = 8219

# Connected clients
clients = set()
client_subscriptions = {}  # client -> set of channels

# Event channels
CHANNELS = {
    "services": "Service status updates",
    "training": "Training progress updates", 
    "generation": "Image generation events",
    "rating": "Rating updates",
    "quality": "Quality gate results",
    "system": "System-wide events"
}

# API endpoints to monitor
APIS = {
    "gateway": "http://127.0.0.1:8200",
    "orchestrator": "http://127.0.0.1:8210",
    "scheduler": "http://127.0.0.1:8214",
    "deployer": "http://127.0.0.1:8215",
    "quality_gate": "http://127.0.0.1:8216",
    "launcher": "http://127.0.0.1:8217",
    "rating_ui": "http://127.0.0.1:8208",
    "comfyui": "http://127.0.0.1:8213"
}


class EventBroadcaster:
    """Broadcast events to connected clients"""
    
    def __init__(self):
        self.event_queue = asyncio.Queue() if WEBSOCKET_AVAILABLE else None
        self.last_states = {}
    
    async def broadcast(self, channel, event_type, data):
        """Broadcast event to all subscribed clients"""
        message = json.dumps({
            "channel": channel,
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        for client in clients.copy():
            try:
                # Check if client subscribed to this channel
                subs = client_subscriptions.get(client, set())
                if channel in subs or "all" in subs:
                    await client.send(message)
            except Exception as e:
                print(f"[HUB] Broadcast error: {e}")
                clients.discard(client)
    
    async def broadcast_sync(self, channel, event_type, data):
        """Thread-safe broadcast wrapper"""
        if self.event_queue:
            await self.event_queue.put((channel, event_type, data))


broadcaster = EventBroadcaster()


async def handle_client(websocket):
    """Handle WebSocket client connection"""
    clients.add(websocket)
    client_subscriptions[websocket] = {"all"}  # Subscribe to all by default
    
    print(f"[HUB] Client connected. Total: {len(clients)}")
    
    # Send welcome message
    await websocket.send(json.dumps({
        "type": "connected",
        "channels": list(CHANNELS.keys()),
        "message": "Connected to LoraForge Real-time Hub"
    }))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_message(websocket, data)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON"}))
    except websockets.ConnectionClosed:
        pass
    finally:
        clients.discard(websocket)
        client_subscriptions.pop(websocket, None)
        print(f"[HUB] Client disconnected. Total: {len(clients)}")


async def handle_message(websocket, data):
    """Handle incoming client messages"""
    msg_type = data.get("type")
    
    if msg_type == "subscribe":
        channels = data.get("channels", [])
        client_subscriptions[websocket] = set(channels)
        await websocket.send(json.dumps({
            "type": "subscribed",
            "channels": channels
        }))
    
    elif msg_type == "unsubscribe":
        channels = data.get("channels", [])
        current = client_subscriptions.get(websocket, set())
        client_subscriptions[websocket] = current - set(channels)
        await websocket.send(json.dumps({
            "type": "unsubscribed",
            "channels": channels
        }))
    
    elif msg_type == "ping":
        await websocket.send(json.dumps({"type": "pong"}))
    
    elif msg_type == "get_status":
        status = await get_full_status()
        await websocket.send(json.dumps({
            "type": "status",
            "data": status
        }))


async def get_full_status():
    """Get full system status"""
    status = {
        "services": {},
        "training": None,
        "quality": None,
        "timestamp": datetime.now().isoformat()
    }
    
    # Check each API
    for name, url in APIS.items():
        try:
            response = requests.get(f"{url}/", timeout=2)
            if response.status_code == 200:
                status["services"][name] = {
                    "running": True,
                    "data": response.json()
                }
            else:
                status["services"][name] = {"running": False}
        except:
            status["services"][name] = {"running": False}
    
    # Get training status
    try:
        r = requests.get(f"{APIS['scheduler']}/api/status", timeout=2)
        if r.status_code == 200:
            status["training"] = r.json()
    except:
        pass
    
    # Get quality status
    try:
        r = requests.get(f"{APIS['quality_gate']}/api/status", timeout=2)
        if r.status_code == 200:
            status["quality"] = r.json()
    except:
        pass
    
    return status


class StatusMonitor:
    """Monitor APIs and broadcast changes"""
    
    def __init__(self):
        self.running = False
        self.last_status = {}
    
    async def start(self):
        self.running = True
        print("[HUB] Status monitor started")
        
        while self.running:
            try:
                await self._check_and_broadcast()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"[HUB] Monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _check_and_broadcast(self):
        """Check status and broadcast changes"""
        for name, url in APIS.items():
            try:
                response = requests.get(f"{url}/", timeout=2)
                running = response.status_code == 200
                
                # Check if status changed
                prev = self.last_status.get(name, {}).get("running")
                if prev is not None and prev != running:
                    await broadcaster.broadcast("services", "status_change", {
                        "service": name,
                        "running": running,
                        "previous": prev
                    })
                
                self.last_status[name] = {"running": running}
                
            except:
                if self.last_status.get(name, {}).get("running"):
                    await broadcaster.broadcast("services", "status_change", {
                        "service": name,
                        "running": False,
                        "previous": True
                    })
                self.last_status[name] = {"running": False}
        
        # Broadcast periodic status update
        await broadcaster.broadcast("system", "heartbeat", {
            "clients": len(clients),
            "services_up": sum(1 for s in self.last_status.values() if s.get("running"))
        })
    
    def stop(self):
        self.running = False


monitor = StatusMonitor()


async def websocket_server():
    """Run WebSocket server"""
    if not WEBSOCKET_AVAILABLE:
        print("[HUB] WebSocket not available")
        return
    
    async with serve(handle_client, "127.0.0.1", WS_PORT):
        print(f"[HUB] WebSocket server running on ws://127.0.0.1:{WS_PORT}")
        
        # Start status monitor
        monitor_task = asyncio.create_task(monitor.start())
        
        # Keep running
        await asyncio.Future()


class HubAPI(BaseHTTPRequestHandler):
    """HTTP API for Real-time Hub"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/':
            self._json({
                'service': 'Real-time Hub',
                'version': '1.0',
                'http_port': HTTP_PORT,
                'ws_port': WS_PORT,
                'ws_url': f'ws://127.0.0.1:{WS_PORT}',
                'websocket_available': WEBSOCKET_AVAILABLE,
                'connected_clients': len(clients),
                'channels': CHANNELS
            })
        
        elif path == '/api/status':
            loop = asyncio.new_event_loop()
            status = loop.run_until_complete(get_full_status())
            loop.close()
            self._json(status)
        
        elif path == '/api/clients':
            self._json({
                'connected': len(clients),
                'subscriptions': {
                    str(id(c)): list(s) 
                    for c, s in client_subscriptions.items()
                }
            })
        
        elif path == '/api/channels':
            self._json({'channels': CHANNELS})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/broadcast':
            # Manual broadcast (for testing or external events)
            channel = data.get('channel', 'system')
            event_type = data.get('type', 'custom')
            event_data = data.get('data', {})
            
            if WEBSOCKET_AVAILABLE and clients:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(
                    broadcaster.broadcast(channel, event_type, event_data)
                )
                loop.close()
                self._json({'success': True, 'clients_notified': len(clients)})
            else:
                self._json({'success': False, 'error': 'No clients connected'})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def run_http_server():
    """Run HTTP server in thread"""
    server = HTTPServer(('127.0.0.1', HTTP_PORT), HubAPI)
    print(f"[HUB] HTTP server running on http://127.0.0.1:{HTTP_PORT}")
    server.serve_forever()


def main():
    print("=" * 60)
    print("  REAL-TIME HUB")
    print("  WebSocket Server for Live Updates")
    print("=" * 60)
    
    print(f"\nWebSocket Available: {WEBSOCKET_AVAILABLE}")
    print(f"HTTP Port: {HTTP_PORT}")
    print(f"WebSocket Port: {WS_PORT}")
    print(f"\nChannels: {', '.join(CHANNELS.keys())}")
    
    # Start HTTP server in thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    print("=" * 60)
    
    # Run WebSocket server
    if WEBSOCKET_AVAILABLE:
        asyncio.run(websocket_server())
    else:
        print("[HUB] Running HTTP-only mode (install websockets for full functionality)")
        # Keep HTTP server running
        while True:
            time.sleep(1)


if __name__ == '__main__':
    main()
