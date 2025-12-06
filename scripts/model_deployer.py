"""
MODEL AUTO-DEPLOYER
====================
Watches for new trained models and deploys them to ComfyUI
Validates models before deployment with quality gate

Port: 8215
"""
import json
import sqlite3
import threading
import time
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
PORT = 8215
DB_PATH = Path(r"c:\Users\Admin\civitai\data\deployer.db")

# Directories to watch
WATCH_DIRS = [
    Path(r"c:\Users\Admin\civitai\output\training\models"),
    Path(r"c:\Users\Admin\civitai\output\loras"),
]

# Deployment targets
TARGETS = {
    "comfyui": Path(r"G:\Github\ComfyUI\models\loras"),
    "backup": Path(r"c:\Users\Admin\civitai\models\deployed"),
}

# Ensure directories exist
for target in TARGETS.values():
    target.mkdir(parents=True, exist_ok=True)
for watch_dir in WATCH_DIRS:
    watch_dir.mkdir(parents=True, exist_ok=True)


class DeployerDB:
    """Database for deployment tracking"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                source_path TEXT NOT NULL,
                target_path TEXT,
                file_hash TEXT,
                file_size INTEGER,
                validated INTEGER DEFAULT 0,
                validation_score REAL,
                status TEXT DEFAULT 'pending',
                deployed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS deployment_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                path TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                last_deploy TEXT
            );
            
            CREATE TABLE IF NOT EXISTS validation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deployment_id INTEGER,
                test_type TEXT,
                score REAL,
                passed INTEGER,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            INSERT OR IGNORE INTO deployment_targets (name, path) 
            VALUES ('comfyui', 'G:\\Github\\ComfyUI\\models\\loras');
            
            INSERT OR IGNORE INTO deployment_targets (name, path) 
            VALUES ('backup', 'c:\\Users\\Admin\\civitai\\models\\deployed');
        ''')
        self.conn.commit()
    
    def create_deployment(self, model_name, source_path, file_hash, file_size):
        cursor = self.conn.execute('''
            INSERT INTO deployments (model_name, source_path, file_hash, file_size)
            VALUES (?, ?, ?, ?)
        ''', (model_name, source_path, file_hash, file_size))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_deployment(self, deploy_id, **kwargs):
        sets = ', '.join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(f'UPDATE deployments SET {sets} WHERE id = ?',
                         list(kwargs.values()) + [deploy_id])
        self.conn.commit()
    
    def add_validation(self, deploy_id, test_type, score, passed, details=None):
        self.conn.execute('''
            INSERT INTO validation_results (deployment_id, test_type, score, passed, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (deploy_id, test_type, score, passed, json.dumps(details) if details else None))
        self.conn.commit()
    
    def get_deployments(self, limit=50):
        return [dict(r) for r in self.conn.execute('''
            SELECT * FROM deployments ORDER BY created_at DESC LIMIT ?
        ''', (limit,)).fetchall()]
    
    def get_targets(self):
        return [dict(r) for r in self.conn.execute('''
            SELECT * FROM deployment_targets WHERE enabled = 1
        ''').fetchall()]
    
    def get_stats(self):
        total = self.conn.execute('SELECT COUNT(*) FROM deployments').fetchone()[0]
        deployed = self.conn.execute(
            'SELECT COUNT(*) FROM deployments WHERE status = "deployed"'
        ).fetchone()[0]
        failed = self.conn.execute(
            'SELECT COUNT(*) FROM deployments WHERE status = "failed"'
        ).fetchone()[0]
        
        return {
            'total_deployments': total,
            'deployed': deployed,
            'failed': failed,
            'success_rate': round(deployed / total * 100, 1) if total > 0 else 0
        }
    
    def model_exists(self, file_hash):
        row = self.conn.execute(
            'SELECT id FROM deployments WHERE file_hash = ?', (file_hash,)
        ).fetchone()
        return row is not None


class ModelValidator:
    """Validate models before deployment"""
    
    def __init__(self, db: DeployerDB):
        self.db = db
        self.min_size = 1024 * 1024  # 1MB minimum
        self.max_size = 500 * 1024 * 1024  # 500MB maximum
    
    def validate(self, deploy_id, model_path):
        """Run validation checks on a model"""
        path = Path(model_path)
        results = []
        
        # Check 1: File exists
        exists = path.exists()
        self.db.add_validation(deploy_id, "file_exists", 1.0 if exists else 0.0, exists)
        results.append(("file_exists", exists))
        
        if not exists:
            return False, 0.0, results
        
        # Check 2: File size
        size = path.stat().st_size
        size_ok = self.min_size <= size <= self.max_size
        size_score = 1.0 if size_ok else 0.5
        self.db.add_validation(deploy_id, "file_size", size_score, size_ok, 
                              {"size": size, "min": self.min_size, "max": self.max_size})
        results.append(("file_size", size_ok))
        
        # Check 3: File extension
        valid_ext = path.suffix.lower() in ['.safetensors', '.pt', '.ckpt', '.bin']
        self.db.add_validation(deploy_id, "file_extension", 1.0 if valid_ext else 0.0, valid_ext,
                              {"extension": path.suffix})
        results.append(("file_extension", valid_ext))
        
        # Check 4: File header (safetensors check)
        header_ok = True
        if path.suffix.lower() == '.safetensors':
            try:
                with open(path, 'rb') as f:
                    header = f.read(8)
                    # Safetensors files start with header length as little-endian uint64
                    header_ok = len(header) == 8
            except:
                header_ok = False
        self.db.add_validation(deploy_id, "file_header", 1.0 if header_ok else 0.0, header_ok)
        results.append(("file_header", header_ok))
        
        # Calculate overall score
        passed_count = sum(1 for _, passed in results if passed)
        total_score = passed_count / len(results)
        
        # Model passes if all critical checks pass
        all_passed = all(passed for _, passed in results)
        
        self.db.update_deployment(deploy_id, 
                                 validated=1 if all_passed else 0,
                                 validation_score=total_score)
        
        return all_passed, total_score, results


class ModelDeployer:
    """Deploy validated models to targets"""
    
    def __init__(self, db: DeployerDB):
        self.db = db
    
    def deploy(self, deploy_id, source_path, target_name="comfyui"):
        """Deploy model to specified target"""
        source = Path(source_path)
        targets = {t['name']: Path(t['path']) for t in self.db.get_targets()}
        
        if target_name not in targets:
            return False, f"Unknown target: {target_name}"
        
        target_dir = targets[target_name]
        
        if not target_dir.exists():
            return False, f"Target directory not found: {target_dir}"
        
        try:
            dest = target_dir / source.name
            
            # Handle existing file
            if dest.exists():
                # Add timestamp to avoid overwrite
                stem = source.stem
                suffix = source.suffix
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = target_dir / f"{stem}_{timestamp}{suffix}"
            
            # Copy file
            shutil.copy2(source, dest)
            
            self.db.update_deployment(deploy_id,
                                     target_path=str(dest),
                                     status="deployed",
                                     deployed_at=datetime.now().isoformat())
            
            return True, str(dest)
            
        except Exception as e:
            self.db.update_deployment(deploy_id, status="failed")
            return False, str(e)
    
    def deploy_to_all(self, deploy_id, source_path):
        """Deploy to all enabled targets"""
        results = {}
        for target in self.db.get_targets():
            success, result = self.deploy(deploy_id, source_path, target['name'])
            results[target['name']] = {"success": success, "result": result}
        return results


def calculate_hash(filepath):
    """Calculate SHA256 hash of file"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


# Initialize components
db = DeployerDB()
validator = ModelValidator(db)
deployer = ModelDeployer(db)


class NewModelHandler(FileSystemEventHandler):
    """Handle new model file events"""
    
    def __init__(self):
        self.processed = set()
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        # Check if it's a model file
        if path.suffix.lower() not in ['.safetensors', '.pt', '.ckpt', '.bin']:
            return
        
        # Avoid duplicate processing
        if str(path) in self.processed:
            return
        self.processed.add(str(path))
        
        # Wait for file to be fully written
        time.sleep(2)
        
        print(f"[DEPLOYER] New model detected: {path.name}")
        self._process_model(path)
    
    def _process_model(self, path):
        """Process a new model file"""
        try:
            # Calculate hash
            file_hash = calculate_hash(path)
            
            # Check if already deployed
            if db.model_exists(file_hash):
                print(f"[DEPLOYER] Model already deployed: {path.name}")
                return
            
            # Create deployment record
            deploy_id = db.create_deployment(
                model_name=path.stem,
                source_path=str(path),
                file_hash=file_hash,
                file_size=path.stat().st_size
            )
            
            # Validate
            print(f"[DEPLOYER] Validating: {path.name}")
            passed, score, results = validator.validate(deploy_id, path)
            
            if not passed:
                print(f"[DEPLOYER] Validation failed: {path.name} (score: {score:.2f})")
                db.update_deployment(deploy_id, status="validation_failed")
                return
            
            print(f"[DEPLOYER] Validation passed: {path.name} (score: {score:.2f})")
            
            # Deploy to ComfyUI
            success, result = deployer.deploy(deploy_id, path, "comfyui")
            
            if success:
                print(f"[DEPLOYER] Deployed to ComfyUI: {result}")
                
                # Also backup
                deployer.deploy(deploy_id, path, "backup")
            else:
                print(f"[DEPLOYER] Deployment failed: {result}")
                
        except Exception as e:
            print(f"[DEPLOYER] Error processing {path.name}: {e}")


class WatcherThread:
    """Background file watcher"""
    
    def __init__(self):
        self.observer = None
        self.running = False
    
    def start(self):
        if self.running:
            return
        
        self.observer = Observer()
        handler = NewModelHandler()
        
        for watch_dir in WATCH_DIRS:
            if watch_dir.exists():
                self.observer.schedule(handler, str(watch_dir), recursive=True)
                print(f"[DEPLOYER] Watching: {watch_dir}")
        
        self.observer.start()
        self.running = True
        print("[DEPLOYER] File watcher started")
    
    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.running = False
        print("[DEPLOYER] File watcher stopped")


# Initialize watcher
watcher = WatcherThread()


class DeployerAPI(BaseHTTPRequestHandler):
    """Model Deployer API"""
    
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
                'service': 'Model Auto-Deployer',
                'version': '1.0',
                'port': PORT,
                'status': 'running',
                'watcher_active': watcher.running
            })
        
        elif path == '/api/status':
            stats = db.get_stats()
            self._json({
                'watcher_running': watcher.running,
                'watch_dirs': [str(d) for d in WATCH_DIRS],
                'targets': db.get_targets(),
                **stats
            })
        
        elif path == '/api/deployments':
            self._json({'deployments': db.get_deployments()})
        
        elif path == '/api/targets':
            self._json({'targets': db.get_targets()})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/start':
            watcher.start()
            self._json({'success': True, 'message': 'Watcher started'})
        
        elif path == '/api/stop':
            watcher.stop()
            self._json({'success': True, 'message': 'Watcher stopped'})
        
        elif path == '/api/deploy':
            # Manual deployment
            model_path = data.get('path')
            target = data.get('target', 'comfyui')
            
            if not model_path or not Path(model_path).exists():
                self._json({'success': False, 'error': 'Invalid model path'})
                return
            
            path_obj = Path(model_path)
            file_hash = calculate_hash(path_obj)
            
            deploy_id = db.create_deployment(
                model_name=path_obj.stem,
                source_path=model_path,
                file_hash=file_hash,
                file_size=path_obj.stat().st_size
            )
            
            # Validate
            passed, score, _ = validator.validate(deploy_id, model_path)
            
            if not passed and not data.get('force'):
                self._json({
                    'success': False, 
                    'error': 'Validation failed',
                    'score': score,
                    'hint': 'Use force=true to deploy anyway'
                })
                return
            
            # Deploy
            success, result = deployer.deploy(deploy_id, model_path, target)
            
            self._json({
                'success': success,
                'deployment_id': deploy_id,
                'result': result,
                'validation_score': score
            })
        
        elif path == '/api/validate':
            # Validate without deploying
            model_path = data.get('path')
            
            if not model_path or not Path(model_path).exists():
                self._json({'success': False, 'error': 'Invalid model path'})
                return
            
            path_obj = Path(model_path)
            file_hash = calculate_hash(path_obj)
            
            deploy_id = db.create_deployment(
                model_name=path_obj.stem,
                source_path=model_path,
                file_hash=file_hash,
                file_size=path_obj.stat().st_size
            )
            
            passed, score, results = validator.validate(deploy_id, model_path)
            
            self._json({
                'valid': passed,
                'score': score,
                'checks': [{'name': name, 'passed': p} for name, p in results]
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  MODEL AUTO-DEPLOYER")
    print("  Automatic LoRA Deployment to ComfyUI")
    print("=" * 60)
    
    stats = db.get_stats()
    targets = db.get_targets()
    
    print(f"\nTotal Deployments: {stats['total_deployments']}")
    print(f"Success Rate: {stats['success_rate']}%")
    print(f"\nTargets:")
    for t in targets:
        status = "✓" if Path(t['path']).exists() else "✗"
        print(f"  [{status}] {t['name']}: {t['path']}")
    
    print(f"\nWatch Directories:")
    for d in WATCH_DIRS:
        status = "✓" if d.exists() else "✗"
        print(f"  [{status}] {d}")
    
    # Auto-start watcher
    watcher.start()
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), DeployerAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
