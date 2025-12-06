"""
UNIFIED API GATEWAY
====================
Single entry point for all LoraForge APIs.
Handles authentication, rate limiting, and routing.

Port: 8200 (Master Gateway)
"""
import os
import sys
import json
import time
import uuid
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
import threading

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
DATA_DIR = CIVITAI_PATH / "data"
DB_PATH = DATA_DIR / "gateway.db"

# All backend services
SERVICES = {
    "frontier": {"url": "http://localhost:8195", "name": "Frontier Stories"},
    "pipeline": {"url": "http://localhost:8205", "name": "Full Pipeline"},
    "video": {"url": "http://localhost:8206", "name": "Video Processing"},
    "caption": {"url": "http://localhost:8207", "name": "Auto-Captioner"},
    "rating": {"url": "http://localhost:8208", "name": "Rating UI"},
    "playwright": {"url": "http://localhost:8203", "name": "Playwright"},
    "rating_system": {"url": "http://localhost:8198", "name": "Rating System"},
    "country": {"url": "http://localhost:8199", "name": "Country Rating"},
    "dashboard": {"url": "http://localhost:8100", "name": "Dashboard"},
    "comfyui": {"url": "http://127.0.0.1:8188", "name": "ComfyUI"},
    "lm_studio": {"url": "http://localhost:1234", "name": "LM Studio"},
    "ollama": {"url": "http://localhost:11434", "name": "Ollama"}
}

# Rate limits per minute
RATE_LIMITS = {
    "default": 60,
    "admin": 1000,
    "generation": 10,
    "heavy": 5
}

app = Flask(__name__)
CORS(app)


class GatewayDB:
    """Database for sessions and rate limiting"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                country_code TEXT DEFAULT 'US',
                max_rating TEXT DEFAULT 'PG',
                age_verified BOOLEAN DEFAULT FALSE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                last_activity TEXT
            );
            
            CREATE TABLE IF NOT EXISTS rate_limits (
                session_id TEXT,
                endpoint TEXT,
                request_count INTEGER DEFAULT 0,
                window_start TEXT,
                PRIMARY KEY (session_id, endpoint)
            );
            
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                endpoint TEXT,
                method TEXT,
                service TEXT,
                status_code INTEGER,
                response_time_ms REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS service_health (
                service_name TEXT PRIMARY KEY,
                url TEXT,
                is_healthy BOOLEAN DEFAULT FALSE,
                last_check TEXT,
                response_time_ms REAL
            );
        ''')
        self.conn.commit()
    
    def create_session(self, user_id: str = None, is_admin: bool = False) -> str:
        session_id = str(uuid.uuid4())
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        
        self.conn.execute('''
            INSERT INTO sessions (id, user_id, is_admin, expires_at, last_activity)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, is_admin, expires, datetime.now().isoformat()))
        self.conn.commit()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        row = self.conn.execute(
            'SELECT * FROM sessions WHERE id = ?', (session_id,)
        ).fetchone()
        
        if row:
            # Check expiry
            if row['expires_at'] and datetime.fromisoformat(row['expires_at']) < datetime.now():
                return None
            
            # Update last activity
            self.conn.execute(
                'UPDATE sessions SET last_activity = ? WHERE id = ?',
                (datetime.now().isoformat(), session_id)
            )
            self.conn.commit()
            
            return dict(row)
        return None
    
    def update_session(self, session_id: str, **kwargs):
        updates = ', '.join(f'{k} = ?' for k in kwargs.keys())
        values = list(kwargs.values()) + [session_id]
        self.conn.execute(f'UPDATE sessions SET {updates} WHERE id = ?', values)
        self.conn.commit()
    
    def check_rate_limit(self, session_id: str, endpoint: str, limit: int) -> bool:
        """Check if request is within rate limit. Returns True if allowed."""
        now = datetime.now()
        window_start = now.replace(second=0, microsecond=0).isoformat()
        
        row = self.conn.execute('''
            SELECT request_count, window_start 
            FROM rate_limits 
            WHERE session_id = ? AND endpoint = ?
        ''', (session_id, endpoint)).fetchone()
        
        if row:
            if row['window_start'] == window_start:
                if row['request_count'] >= limit:
                    return False
                self.conn.execute('''
                    UPDATE rate_limits 
                    SET request_count = request_count + 1
                    WHERE session_id = ? AND endpoint = ?
                ''', (session_id, endpoint))
            else:
                self.conn.execute('''
                    UPDATE rate_limits 
                    SET request_count = 1, window_start = ?
                    WHERE session_id = ? AND endpoint = ?
                ''', (window_start, session_id, endpoint))
        else:
            self.conn.execute('''
                INSERT INTO rate_limits (session_id, endpoint, request_count, window_start)
                VALUES (?, ?, 1, ?)
            ''', (session_id, endpoint, window_start))
        
        self.conn.commit()
        return True
    
    def log_request(self, session_id: str, endpoint: str, method: str, 
                    service: str, status_code: int, response_time: float):
        self.conn.execute('''
            INSERT INTO api_logs (session_id, endpoint, method, service, status_code, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, endpoint, method, service, status_code, response_time))
        self.conn.commit()
    
    def update_service_health(self, service_name: str, url: str, 
                               is_healthy: bool, response_time: float):
        self.conn.execute('''
            INSERT OR REPLACE INTO service_health 
            (service_name, url, is_healthy, last_check, response_time_ms)
            VALUES (?, ?, ?, ?, ?)
        ''', (service_name, url, is_healthy, datetime.now().isoformat(), response_time))
        self.conn.commit()
    
    def get_service_health(self) -> Dict:
        rows = self.conn.execute('SELECT * FROM service_health').fetchall()
        return {row['service_name']: dict(row) for row in rows}


db = GatewayDB()


# ============================================================
# MIDDLEWARE
# ============================================================

def get_session():
    """Get or create session from request"""
    session_id = request.headers.get('X-Session-ID') or request.cookies.get('session_id')
    
    if session_id:
        session = db.get_session(session_id)
        if session:
            return session
    
    # Create anonymous session
    session_id = db.create_session()
    return db.get_session(session_id)


def require_session(f):
    """Decorator to require valid session"""
    @wraps(f)
    def decorated(*args, **kwargs):
        g.session = get_session()
        if not g.session:
            return jsonify({"error": "Invalid session"}), 401
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator to require admin session"""
    @wraps(f)
    def decorated(*args, **kwargs):
        g.session = get_session()
        if not g.session or not g.session.get('is_admin'):
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


def rate_limit(limit_type: str = "default"):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            session = get_session()
            limit = RATE_LIMITS.get("admin" if session.get('is_admin') else limit_type, 60)
            
            if not db.check_rate_limit(session['id'], request.path, limit):
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": 60
                }), 429
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# ============================================================
# SERVICE PROXYING
# ============================================================

def proxy_request(service_key: str, path: str = ""):
    """Proxy request to backend service"""
    service = SERVICES.get(service_key)
    if not service:
        return jsonify({"error": f"Unknown service: {service_key}"}), 404
    
    url = f"{service['url']}/{path}".rstrip('/')
    
    start_time = time.time()
    
    try:
        # Forward request
        resp = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() not in ['host', 'content-length']},
            data=request.get_data(),
            params=request.args,
            timeout=60
        )
        
        response_time = (time.time() - start_time) * 1000
        
        # Log request
        session = get_session()
        db.log_request(
            session['id'], request.path, request.method,
            service_key, resp.status_code, response_time
        )
        
        # Return response
        return (resp.content, resp.status_code, dict(resp.headers))
    
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": f"Service unavailable: {service['name']}",
            "service": service_key
        }), 503
    
    except requests.exceptions.Timeout:
        return jsonify({
            "error": f"Service timeout: {service['name']}",
            "service": service_key
        }), 504


# ============================================================
# SESSION ENDPOINTS
# ============================================================

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create new session"""
    data = request.json or {}
    user_id = data.get('user_id')
    is_admin = data.get('is_admin', False)
    
    # Admin requires password
    if is_admin:
        admin_pass = data.get('admin_password')
        if admin_pass != "loraforge_admin_2024":  # Simple auth
            return jsonify({"error": "Invalid admin password"}), 403
    
    session_id = db.create_session(user_id, is_admin)
    
    response = jsonify({
        "success": True,
        "session_id": session_id,
        "is_admin": is_admin,
        "expires_in": "24 hours"
    })
    response.set_cookie('session_id', session_id, max_age=86400)
    return response


@app.route('/api/session', methods=['GET'])
@require_session
def get_current_session():
    """Get current session info"""
    return jsonify({
        "success": True,
        "session": {
            "id": g.session['id'],
            "is_admin": g.session['is_admin'],
            "country_code": g.session['country_code'],
            "max_rating": g.session['max_rating'],
            "age_verified": g.session['age_verified']
        }
    })


@app.route('/api/session/update', methods=['POST'])
@require_session
def update_current_session():
    """Update session settings"""
    data = request.json or {}
    
    allowed_updates = ['country_code', 'max_rating', 'age_verified']
    updates = {k: v for k, v in data.items() if k in allowed_updates}
    
    if updates:
        db.update_session(g.session['id'], **updates)
    
    return jsonify({"success": True, "updated": list(updates.keys())})


# ============================================================
# SERVICE PROXY ROUTES
# ============================================================

@app.route('/api/frontier/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_session
@rate_limit("default")
def proxy_frontier(path):
    return proxy_request("frontier", f"api/{path}")


@app.route('/api/pipeline/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_session
@rate_limit("default")
def proxy_pipeline(path):
    return proxy_request("pipeline", f"api/{path}")


@app.route('/api/video/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_session
@rate_limit("heavy")
def proxy_video(path):
    return proxy_request("video", f"api/{path}")


@app.route('/api/caption/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_session
@rate_limit("heavy")
def proxy_caption(path):
    return proxy_request("caption", f"api/{path}")


@app.route('/api/rating/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_session
@rate_limit("default")
def proxy_rating(path):
    return proxy_request("rating", f"api/{path}")


@app.route('/api/generation/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_session
@rate_limit("generation")
def proxy_generation(path):
    return proxy_request("comfyui", path)


# ============================================================
# HEALTH & MONITORING
# ============================================================

def check_all_services():
    """Check health of all services"""
    results = {}
    
    for name, service in SERVICES.items():
        start = time.time()
        try:
            resp = requests.get(f"{service['url']}/", timeout=5)
            is_healthy = resp.status_code < 500
            response_time = (time.time() - start) * 1000
        except:
            is_healthy = False
            response_time = 0
        
        db.update_service_health(name, service['url'], is_healthy, response_time)
        results[name] = {
            "name": service['name'],
            "url": service['url'],
            "healthy": is_healthy,
            "response_time_ms": round(response_time, 2)
        }
    
    return results


@app.route('/api/health', methods=['GET'])
def health_check():
    """Quick health check"""
    return jsonify({
        "success": True,
        "service": "Unified API Gateway",
        "version": "1.0.0",
        "port": 8200
    })


@app.route('/api/health/services', methods=['GET'])
def service_health():
    """Get health of all services"""
    # Check fresh or use cached
    cached = db.get_service_health()
    
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    if refresh or not cached:
        results = check_all_services()
    else:
        results = cached
    
    healthy_count = sum(1 for s in results.values() if s.get('healthy') or s.get('is_healthy'))
    
    return jsonify({
        "success": True,
        "healthy": healthy_count,
        "total": len(SERVICES),
        "services": results
    })


@app.route('/api/services', methods=['GET'])
def list_services():
    """List all available services"""
    return jsonify({
        "success": True,
        "services": {
            name: {
                "name": svc['name'],
                "url": svc['url'],
                "proxy_path": f"/api/{name}/"
            }
            for name, svc in SERVICES.items()
        }
    })


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@app.route('/api/admin/logs', methods=['GET'])
@require_admin
def get_logs():
    """Get API logs"""
    limit = int(request.args.get('limit', 100))
    
    rows = db.conn.execute('''
        SELECT * FROM api_logs ORDER BY created_at DESC LIMIT ?
    ''', (limit,)).fetchall()
    
    return jsonify({
        "success": True,
        "count": len(rows),
        "logs": [dict(r) for r in rows]
    })


@app.route('/api/admin/sessions', methods=['GET'])
@require_admin
def get_sessions():
    """Get all active sessions"""
    rows = db.conn.execute('''
        SELECT * FROM sessions 
        WHERE expires_at > datetime('now')
        ORDER BY last_activity DESC
    ''').fetchall()
    
    return jsonify({
        "success": True,
        "count": len(rows),
        "sessions": [dict(r) for r in rows]
    })


@app.route('/api/admin/stats', methods=['GET'])
@require_admin
def get_stats():
    """Get gateway statistics"""
    total_requests = db.conn.execute('SELECT COUNT(*) FROM api_logs').fetchone()[0]
    active_sessions = db.conn.execute('''
        SELECT COUNT(*) FROM sessions WHERE expires_at > datetime('now')
    ''').fetchone()[0]
    
    # Requests by service
    by_service = db.conn.execute('''
        SELECT service, COUNT(*) as count 
        FROM api_logs 
        GROUP BY service 
        ORDER BY count DESC
    ''').fetchall()
    
    return jsonify({
        "success": True,
        "total_requests": total_requests,
        "active_sessions": active_sessions,
        "requests_by_service": {r[0]: r[1] for r in by_service}
    })


# ============================================================
# ROOT
# ============================================================

@app.route('/', methods=['GET'])
def index():
    """Gateway info"""
    return jsonify({
        "service": "Unified API Gateway",
        "version": "1.0.0",
        "port": 8200,
        "description": "Single entry point for all LoraForge APIs",
        "endpoints": {
            "session": {
                "create": "POST /api/session/create",
                "get": "GET /api/session",
                "update": "POST /api/session/update"
            },
            "services": {
                "list": "GET /api/services",
                "health": "GET /api/health/services"
            },
            "proxies": {
                "frontier": "/api/frontier/*",
                "pipeline": "/api/pipeline/*",
                "video": "/api/video/*",
                "caption": "/api/caption/*",
                "rating": "/api/rating/*",
                "generation": "/api/generation/*"
            },
            "admin": {
                "logs": "GET /api/admin/logs",
                "sessions": "GET /api/admin/sessions",
                "stats": "GET /api/admin/stats"
            }
        },
        "features": {
            "session_management": True,
            "rate_limiting": True,
            "request_logging": True,
            "service_health_monitoring": True,
            "admin_dashboard": True
        }
    })


# ============================================================
# BACKGROUND HEALTH CHECK
# ============================================================

def background_health_check():
    """Periodically check service health"""
    while True:
        try:
            check_all_services()
        except Exception as e:
            print(f"Health check error: {e}")
        time.sleep(60)  # Every minute


if __name__ == '__main__':
    print("=" * 70)
    print("  UNIFIED API GATEWAY")
    print("  Single Entry Point for All LoraForge APIs")
    print("  Port: 8200")
    print("=" * 70)
    
    print("\n📡 Proxied Services:")
    for name, svc in SERVICES.items():
        print(f"    /api/{name}/* → {svc['url']} ({svc['name']})")
    
    print("\n🔐 Session Management:")
    print("    POST /api/session/create - Create session")
    print("    GET  /api/session        - Get current session")
    
    print("\n🛡️ Features:")
    print("    ✅ Session-based authentication")
    print("    ✅ Rate limiting (60/min default, 1000/min admin)")
    print("    ✅ Request logging")
    print("    ✅ Service health monitoring")
    print("=" * 70)
    
    # Start background health checker
    health_thread = threading.Thread(target=background_health_check, daemon=True)
    health_thread.start()
    
    app.run(host='0.0.0.0', port=8200, debug=False)
