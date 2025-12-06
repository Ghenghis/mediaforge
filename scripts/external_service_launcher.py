"""
EXTERNAL SERVICE LAUNCHER
==========================
Monitors and auto-starts external dependencies:
- ComfyUI (port 8188)
- GPT-SoVITS (port 9880)
- LM Studio (port 1234)
- Ollama (port 11434)

Port: 8217
"""
import json
import sqlite3
import subprocess
import threading
import time
import requests
import psutil
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
PORT = 8217
DB_PATH = Path(r"c:\Users\Admin\civitai\data\external_services.db")

# External service configurations
SERVICES = {
    "comfyui": {
        "name": "ComfyUI",
        "port": 8188,
        "url": "http://127.0.0.1:8188",
        "path": Path(r"G:\Github\ComfyUI"),
        "command": ["python", "main.py", "--listen", "127.0.0.1"],
        "check_endpoint": "/",
        "auto_start": False,  # Heavy - user control
        "startup_time": 30
    },
    "gpt_sovits": {
        "name": "GPT-SoVITS",
        "port": 9880,
        "url": "http://127.0.0.1:9880",
        "path": Path(r"c:\Users\Admin\civitai\project\GPT-SoVITS-main\GPT-SoVITS-main"),
        "command": ["python", "api.py"],
        "check_endpoint": "/",
        "auto_start": False,  # Heavy - user control
        "startup_time": 20
    },
    "lm_studio": {
        "name": "LM Studio",
        "port": 1234,
        "url": "http://127.0.0.1:1234",
        "path": None,  # Installed app
        "command": None,  # Manual start required
        "check_endpoint": "/v1/models",
        "auto_start": False,
        "startup_time": 10
    },
    "ollama": {
        "name": "Ollama",
        "port": 11434,
        "url": "http://127.0.0.1:11434",
        "path": None,  # System service
        "command": ["ollama", "serve"],
        "check_endpoint": "/api/tags",
        "auto_start": True,  # Lightweight
        "startup_time": 5
    }
}


class ServiceDB:
    """Database for service status tracking"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS service_status (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                port INTEGER,
                status TEXT DEFAULT 'unknown',
                pid INTEGER,
                last_check TEXT,
                last_start TEXT,
                start_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                last_error TEXT
            );
            
            CREATE TABLE IF NOT EXISTS service_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id TEXT,
                event TEXT NOT NULL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS service_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                auto_start_enabled INTEGER DEFAULT 1,
                check_interval INTEGER DEFAULT 30,
                max_restart_attempts INTEGER DEFAULT 3
            );
            
            INSERT OR IGNORE INTO service_config (id) VALUES (1);
        ''')
        
        # Initialize service records
        for sid, svc in SERVICES.items():
            self.conn.execute('''
                INSERT OR IGNORE INTO service_status (id, name, port)
                VALUES (?, ?, ?)
            ''', (sid, svc['name'], svc['port']))
        
        self.conn.commit()
    
    def get_config(self):
        row = self.conn.execute('SELECT * FROM service_config WHERE id = 1').fetchone()
        return dict(row) if row else {}
    
    def update_status(self, service_id, **kwargs):
        kwargs['last_check'] = datetime.now().isoformat()
        sets = ', '.join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(f'UPDATE service_status SET {sets} WHERE id = ?',
                         list(kwargs.values()) + [service_id])
        self.conn.commit()
    
    def increment_start(self, service_id):
        self.conn.execute('''
            UPDATE service_status SET start_count = start_count + 1,
            last_start = ? WHERE id = ?
        ''', (datetime.now().isoformat(), service_id))
        self.conn.commit()
    
    def increment_error(self, service_id, error):
        self.conn.execute('''
            UPDATE service_status SET error_count = error_count + 1,
            last_error = ? WHERE id = ?
        ''', (error, service_id))
        self.conn.commit()
    
    def log_event(self, service_id, event, details=None):
        self.conn.execute('''
            INSERT INTO service_logs (service_id, event, details)
            VALUES (?, ?, ?)
        ''', (service_id, event, json.dumps(details) if details else None))
        self.conn.commit()
    
    def get_all_status(self):
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM service_status'
        ).fetchall()]
    
    def get_logs(self, service_id=None, limit=50):
        if service_id:
            return [dict(r) for r in self.conn.execute('''
                SELECT * FROM service_logs WHERE service_id = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (service_id, limit)).fetchall()]
        else:
            return [dict(r) for r in self.conn.execute('''
                SELECT * FROM service_logs ORDER BY created_at DESC LIMIT ?
            ''', (limit,)).fetchall()]


class ServiceChecker:
    """Check service availability"""
    
    def check(self, service_id):
        """Check if a service is running"""
        if service_id not in SERVICES:
            return False, "Unknown service"
        
        svc = SERVICES[service_id]
        
        try:
            response = requests.get(
                f"{svc['url']}{svc['check_endpoint']}",
                timeout=5
            )
            return response.status_code < 500, "OK"
        except requests.ConnectionError:
            return False, "Connection refused"
        except requests.Timeout:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def check_all(self):
        """Check all services"""
        results = {}
        for sid in SERVICES:
            running, message = self.check(sid)
            results[sid] = {
                "name": SERVICES[sid]['name'],
                "port": SERVICES[sid]['port'],
                "running": running,
                "message": message
            }
        return results
    
    def find_process(self, port):
        """Find process using a port"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    return psutil.Process(conn.pid)
                except:
                    pass
        return None


class ServiceLauncher:
    """Start and manage external services"""
    
    def __init__(self, db: ServiceDB, checker: ServiceChecker):
        self.db = db
        self.checker = checker
        self.processes = {}
    
    def start(self, service_id):
        """Start a service"""
        if service_id not in SERVICES:
            return False, "Unknown service"
        
        svc = SERVICES[service_id]
        
        # Check if already running
        running, _ = self.checker.check(service_id)
        if running:
            return True, "Already running"
        
        # Check if we can start it
        if not svc['command']:
            return False, f"{svc['name']} requires manual start"
        
        if svc['path'] and not svc['path'].exists():
            return False, f"Path not found: {svc['path']}"
        
        try:
            # Start the process
            cwd = str(svc['path']) if svc['path'] else None
            
            process = subprocess.Popen(
                svc['command'],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            self.processes[service_id] = process
            self.db.increment_start(service_id)
            self.db.log_event(service_id, "started", {"pid": process.pid})
            
            # Wait for startup
            print(f"[LAUNCHER] Starting {svc['name']}...")
            time.sleep(svc['startup_time'])
            
            # Verify it started
            running, message = self.checker.check(service_id)
            
            if running:
                self.db.update_status(service_id, status="running", pid=process.pid)
                self.db.log_event(service_id, "started_ok")
                return True, f"{svc['name']} started (PID: {process.pid})"
            else:
                self.db.update_status(service_id, status="failed")
                self.db.increment_error(service_id, message)
                return False, f"Started but not responding: {message}"
                
        except Exception as e:
            self.db.update_status(service_id, status="error")
            self.db.increment_error(service_id, str(e))
            self.db.log_event(service_id, "start_error", {"error": str(e)})
            return False, str(e)
    
    def stop(self, service_id):
        """Stop a service"""
        if service_id not in SERVICES:
            return False, "Unknown service"
        
        svc = SERVICES[service_id]
        
        # Find and kill process
        proc = self.checker.find_process(svc['port'])
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=10)
                self.db.update_status(service_id, status="stopped", pid=None)
                self.db.log_event(service_id, "stopped")
                return True, f"{svc['name']} stopped"
            except Exception as e:
                return False, f"Failed to stop: {e}"
        
        # Also check our tracked process
        if service_id in self.processes:
            try:
                self.processes[service_id].terminate()
                del self.processes[service_id]
            except:
                pass
        
        return True, "Not running"
    
    def restart(self, service_id):
        """Restart a service"""
        self.stop(service_id)
        time.sleep(2)
        return self.start(service_id)


# Initialize components
db = ServiceDB()
checker = ServiceChecker()
launcher = ServiceLauncher(db, checker)


class MonitorThread:
    """Background service monitoring"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[LAUNCHER] Monitor started")
    
    def stop(self):
        self.running = False
        print("[LAUNCHER] Monitor stopped")
    
    def _loop(self):
        while self.running:
            try:
                config = db.get_config()
                interval = config.get('check_interval', 30)
                
                # Check all services
                for sid, svc in SERVICES.items():
                    running, message = checker.check(sid)
                    status = "running" if running else "stopped"
                    
                    db.update_status(sid, status=status)
                    
                    # Auto-start if configured
                    if not running and svc['auto_start'] and config.get('auto_start_enabled'):
                        print(f"[LAUNCHER] Auto-starting {svc['name']}...")
                        launcher.start(sid)
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"[LAUNCHER] Monitor error: {e}")
                time.sleep(60)


# Initialize monitor
monitor = MonitorThread()


class LauncherAPI(BaseHTTPRequestHandler):
    """External Service Launcher API"""
    
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
                'service': 'External Service Launcher',
                'version': '1.0',
                'port': PORT,
                'status': 'running',
                'monitor_active': monitor.running
            })
        
        elif path == '/api/status':
            results = checker.check_all()
            db_status = {s['id']: s for s in db.get_all_status()}
            
            for sid, result in results.items():
                if sid in db_status:
                    result['start_count'] = db_status[sid].get('start_count', 0)
                    result['error_count'] = db_status[sid].get('error_count', 0)
                    result['last_start'] = db_status[sid].get('last_start')
            
            running_count = sum(1 for r in results.values() if r['running'])
            
            self._json({
                'services': results,
                'summary': {
                    'total': len(results),
                    'running': running_count,
                    'stopped': len(results) - running_count
                },
                'monitor_active': monitor.running
            })
        
        elif path.startswith('/api/service/'):
            service_id = path.split('/')[-1]
            if service_id in SERVICES:
                running, message = checker.check(service_id)
                svc = SERVICES[service_id]
                self._json({
                    'id': service_id,
                    'name': svc['name'],
                    'port': svc['port'],
                    'running': running,
                    'message': message,
                    'auto_start': svc['auto_start'],
                    'can_auto_start': svc['command'] is not None
                })
            else:
                self._json({'error': 'Unknown service'}, 404)
        
        elif path == '/api/logs':
            self._json({'logs': db.get_logs(limit=100)})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/start':
            service_id = data.get('service')
            if not service_id:
                self._json({'success': False, 'error': 'Service ID required'})
                return
            
            success, message = launcher.start(service_id)
            self._json({'success': success, 'message': message})
        
        elif path == '/api/stop':
            service_id = data.get('service')
            if not service_id:
                self._json({'success': False, 'error': 'Service ID required'})
                return
            
            success, message = launcher.stop(service_id)
            self._json({'success': success, 'message': message})
        
        elif path == '/api/restart':
            service_id = data.get('service')
            if not service_id:
                self._json({'success': False, 'error': 'Service ID required'})
                return
            
            success, message = launcher.restart(service_id)
            self._json({'success': success, 'message': message})
        
        elif path == '/api/start-all':
            results = {}
            for sid, svc in SERVICES.items():
                if svc['command']:  # Only start services we can start
                    success, message = launcher.start(sid)
                    results[sid] = {'success': success, 'message': message}
            self._json({'results': results})
        
        elif path == '/api/monitor/start':
            monitor.start()
            self._json({'success': True, 'message': 'Monitor started'})
        
        elif path == '/api/monitor/stop':
            monitor.stop()
            self._json({'success': True, 'message': 'Monitor stopped'})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  EXTERNAL SERVICE LAUNCHER")
    print("  ComfyUI | GPT-SoVITS | LM Studio | Ollama")
    print("=" * 60)
    
    # Check current status
    print("\nService Status:")
    results = checker.check_all()
    for sid, result in results.items():
        status = "✓ Running" if result['running'] else "✗ Stopped"
        print(f"  [{status}] {result['name']} (:{result['port']})")
    
    # Start monitor
    monitor.start()
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), LauncherAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
