"""
BACKUP AUTO-SCHEDULER
=====================
Automatically backs up databases, configs, and important files
Supports incremental and full backups

Port: 8224
"""
import os
import json
import sqlite3
import shutil
import zipfile
import hashlib
import threading
import time
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Configuration
PORT = 8224
PROJECT_DIR = Path(r"c:\Users\Admin\civitai")
BACKUP_DIR = Path(r"c:\Users\Admin\civitai\backups")
DB_PATH = BACKUP_DIR / "backup_scheduler.db"

# Ensure directories
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Backup configurations
BACKUP_CONFIGS = {
    "databases": {
        "paths": [
            "data/*.db",
            "data/*.sqlite",
            "*.db"
        ],
        "interval_hours": 6,
        "keep_count": 10,
        "compress": True
    },
    "configs": {
        "paths": [
            "data/*.json",
            "config/*.json",
            "*.json"
        ],
        "interval_hours": 24,
        "keep_count": 7,
        "compress": True
    },
    "scripts": {
        "paths": [
            "scripts/*.py"
        ],
        "interval_hours": 168,  # Weekly
        "keep_count": 4,
        "compress": True
    },
    "workflows": {
        "paths": [
            "G:/Github/ComfyUI/user/default/workflows/*.json"
        ],
        "interval_hours": 24,
        "keep_count": 7,
        "compress": True
    },
    "wpf": {
        "paths": [
            "ui/WPF/AIStudioDashboard/**/*.cs",
            "ui/WPF/AIStudioDashboard/**/*.xaml"
        ],
        "interval_hours": 168,
        "keep_count": 4,
        "compress": True
    }
}


class BackupDB:
    """Database for backup tracking"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS backup_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                config TEXT,
                last_backup TEXT,
                next_backup TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                size_bytes INTEGER,
                file_count INTEGER,
                backup_type TEXT DEFAULT 'full',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS backup_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                action TEXT,
                details TEXT,
                success INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()
        self._init_jobs()
    
    def _init_jobs(self):
        for name, config in BACKUP_CONFIGS.items():
            interval = config.get('interval_hours', 24)
            next_backup = datetime.now().isoformat()
            self.conn.execute('''
                INSERT OR IGNORE INTO backup_jobs (name, config, next_backup)
                VALUES (?, ?, ?)
            ''', (name, json.dumps(config), next_backup))
        self.conn.commit()
    
    def get_job(self, name):
        row = self.conn.execute(
            'SELECT * FROM backup_jobs WHERE name = ?', (name,)
        ).fetchone()
        return dict(row) if row else None
    
    def get_all_jobs(self):
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM backup_jobs ORDER BY name'
        ).fetchall()]
    
    def update_job(self, name, **kwargs):
        sets = ', '.join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(
            f'UPDATE backup_jobs SET {sets} WHERE name = ?',
            list(kwargs.values()) + [name]
        )
        self.conn.commit()
    
    def add_backup(self, job_id, filename, filepath, size_bytes, file_count, backup_type='full'):
        self.conn.execute('''
            INSERT INTO backups (job_id, filename, filepath, size_bytes, file_count, backup_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (job_id, filename, filepath, size_bytes, file_count, backup_type))
        self.conn.commit()
    
    def get_backups(self, job_id=None, limit=50):
        if job_id:
            return [dict(r) for r in self.conn.execute('''
                SELECT b.*, j.name as job_name
                FROM backups b
                LEFT JOIN backup_jobs j ON b.job_id = j.id
                WHERE b.job_id = ?
                ORDER BY b.created_at DESC LIMIT ?
            ''', (job_id, limit)).fetchall()]
        return [dict(r) for r in self.conn.execute('''
            SELECT b.*, j.name as job_name
            FROM backups b
            LEFT JOIN backup_jobs j ON b.job_id = j.id
            ORDER BY b.created_at DESC LIMIT ?
        ''', (limit,)).fetchall()]
    
    def log_action(self, job_id, action, details, success=True):
        self.conn.execute('''
            INSERT INTO backup_logs (job_id, action, details, success)
            VALUES (?, ?, ?, ?)
        ''', (job_id, action, details, 1 if success else 0))
        self.conn.commit()
    
    def get_logs(self, limit=100):
        return [dict(r) for r in self.conn.execute('''
            SELECT l.*, j.name as job_name
            FROM backup_logs l
            LEFT JOIN backup_jobs j ON l.job_id = j.id
            ORDER BY l.created_at DESC LIMIT ?
        ''', (limit,)).fetchall()]
    
    def cleanup_old_backups(self, job_id, keep_count):
        """Remove old backups beyond keep_count"""
        backups = self.get_backups(job_id, limit=1000)
        if len(backups) > keep_count:
            to_delete = backups[keep_count:]
            for b in to_delete:
                try:
                    Path(b['filepath']).unlink(missing_ok=True)
                    self.conn.execute('DELETE FROM backups WHERE id = ?', (b['id'],))
                except Exception as e:
                    print(f"Cleanup error: {e}")
            self.conn.commit()
            return len(to_delete)
        return 0


class BackupManager:
    """Manage backups"""
    
    def __init__(self, db: BackupDB):
        self.db = db
    
    def find_files(self, patterns):
        """Find files matching patterns"""
        files = []
        for pattern in patterns:
            if pattern.startswith(('C:', 'D:', 'E:', 'F:', 'G:')):
                # Absolute path
                base = Path(pattern).parent
                glob_pattern = Path(pattern).name
                if base.exists():
                    files.extend(base.glob(glob_pattern))
            else:
                # Relative to project
                files.extend(PROJECT_DIR.glob(pattern))
        return files
    
    def create_backup(self, job_name, backup_type='full'):
        """Create a backup for a job"""
        job = self.db.get_job(job_name)
        if not job:
            return False, "Job not found"
        
        config = json.loads(job['config'])
        
        # Find files
        files = self.find_files(config['paths'])
        if not files:
            self.db.log_action(job['id'], 'backup', 'No files found', False)
            return False, "No files found"
        
        # Create backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{job_name}_{timestamp}"
        
        if config.get('compress', True):
            backup_path = BACKUP_DIR / f"{backup_name}.zip"
            
            # Create zip
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    try:
                        arcname = str(f.relative_to(PROJECT_DIR)) if str(PROJECT_DIR) in str(f) else f.name
                        zf.write(f, arcname)
                    except Exception as e:
                        print(f"Error adding {f}: {e}")
        else:
            # Create folder backup
            backup_path = BACKUP_DIR / backup_name
            backup_path.mkdir(exist_ok=True)
            
            for f in files:
                try:
                    dest = backup_path / f.name
                    shutil.copy2(f, dest)
                except Exception as e:
                    print(f"Error copying {f}: {e}")
        
        # Get size
        if backup_path.is_file():
            size = backup_path.stat().st_size
        else:
            size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
        
        # Record backup
        self.db.add_backup(job['id'], backup_path.name, str(backup_path), size, len(files), backup_type)
        
        # Update job
        interval = config.get('interval_hours', 24)
        next_backup = datetime.now().timestamp() + (interval * 3600)
        self.db.update_job(
            job_name,
            last_backup=datetime.now().isoformat(),
            next_backup=datetime.fromtimestamp(next_backup).isoformat()
        )
        
        # Cleanup old backups
        keep_count = config.get('keep_count', 10)
        deleted = self.db.cleanup_old_backups(job['id'], keep_count)
        
        self.db.log_action(job['id'], 'backup', 
                          f'Created {backup_path.name} ({len(files)} files, {size} bytes), cleaned {deleted}')
        
        return True, f"Backup created: {backup_path.name}"
    
    def restore_backup(self, backup_id, target_dir=None):
        """Restore a backup"""
        backup = self.db.conn.execute(
            'SELECT * FROM backups WHERE id = ?', (backup_id,)
        ).fetchone()
        
        if not backup:
            return False, "Backup not found"
        
        backup = dict(backup)
        backup_path = Path(backup['filepath'])
        
        if not backup_path.exists():
            return False, "Backup file not found"
        
        target = Path(target_dir) if target_dir else PROJECT_DIR
        
        if backup_path.suffix == '.zip':
            with zipfile.ZipFile(backup_path, 'r') as zf:
                zf.extractall(target)
        else:
            for f in backup_path.iterdir():
                shutil.copy2(f, target / f.name)
        
        self.db.log_action(backup['job_id'], 'restore', 
                          f'Restored {backup["filename"]} to {target}')
        
        return True, f"Restored to {target}"
    
    def get_backup_info(self, backup_id):
        """Get backup contents"""
        backup = self.db.conn.execute(
            'SELECT * FROM backups WHERE id = ?', (backup_id,)
        ).fetchone()
        
        if not backup:
            return None
        
        backup = dict(backup)
        backup_path = Path(backup['filepath'])
        
        if not backup_path.exists():
            backup['files'] = []
            return backup
        
        if backup_path.suffix == '.zip':
            with zipfile.ZipFile(backup_path, 'r') as zf:
                backup['files'] = [
                    {'name': f.filename, 'size': f.file_size}
                    for f in zf.infolist()
                ]
        else:
            backup['files'] = [
                {'name': f.name, 'size': f.stat().st_size}
                for f in backup_path.iterdir()
            ]
        
        return backup


# Initialize
db = BackupDB()
manager = BackupManager(db)

# Scheduler
scheduler_running = False


def run_scheduler():
    """Background backup scheduler"""
    global scheduler_running
    
    while scheduler_running:
        try:
            for job in db.get_all_jobs():
                if not job['enabled']:
                    continue
                
                next_backup = datetime.fromisoformat(job['next_backup'])
                if datetime.now() >= next_backup:
                    print(f"[Backup Scheduler] Running backup: {job['name']}")
                    success, msg = manager.create_backup(job['name'])
                    print(f"[Backup Scheduler] {msg}")
        except Exception as e:
            print(f"[Backup Scheduler] Error: {e}")
        
        time.sleep(60)


class BackupAPI(BaseHTTPRequestHandler):
    """Backup Scheduler API"""
    
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
        path = urlparse(self.path).path
        
        if path == '/':
            backups = db.get_backups(limit=5)
            total_size = sum(b['size_bytes'] for b in db.get_backups(limit=1000))
            self._json({
                'service': 'Backup Auto-Scheduler',
                'version': '1.0',
                'port': PORT,
                'scheduler_running': scheduler_running,
                'jobs': len(db.get_all_jobs()),
                'total_backups': len(db.get_backups(limit=1000)),
                'total_size_mb': round(total_size / 1024 / 1024, 2)
            })
        
        elif path == '/api/jobs':
            jobs = db.get_all_jobs()
            for j in jobs:
                j['config'] = json.loads(j['config']) if j.get('config') else {}
            self._json({'jobs': jobs})
        
        elif path.startswith('/api/job/'):
            name = path.split('/')[-1]
            job = db.get_job(name)
            if job:
                job['config'] = json.loads(job['config']) if job.get('config') else {}
                job['backups'] = db.get_backups(job['id'])
                self._json(job)
            else:
                self._json({'error': 'Not found'}, 404)
        
        elif path == '/api/backups':
            self._json({'backups': db.get_backups()})
        
        elif path.startswith('/api/backup/'):
            bid = path.split('/')[-1]
            info = manager.get_backup_info(int(bid))
            if info:
                self._json(info)
            else:
                self._json({'error': 'Not found'}, 404)
        
        elif path == '/api/logs':
            self._json({'logs': db.get_logs()})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/backup':
            job_name = data.get('job')
            if job_name:
                success, msg = manager.create_backup(job_name)
                self._json({'success': success, 'message': msg})
            else:
                self._json({'success': False, 'error': 'Job name required'})
        
        elif path == '/api/backup-all':
            results = []
            for job in db.get_all_jobs():
                success, msg = manager.create_backup(job['name'])
                results.append({'job': job['name'], 'success': success, 'message': msg})
            self._json({'results': results})
        
        elif path == '/api/restore':
            backup_id = data.get('backup_id')
            target = data.get('target_dir')
            if backup_id:
                success, msg = manager.restore_backup(int(backup_id), target)
                self._json({'success': success, 'message': msg})
            else:
                self._json({'success': False, 'error': 'Backup ID required'})
        
        elif path == '/api/scheduler/start':
            global scheduler_running
            if not scheduler_running:
                scheduler_running = True
                threading.Thread(target=run_scheduler, daemon=True).start()
            self._json({'success': True, 'running': True})
        
        elif path == '/api/scheduler/stop':
            scheduler_running = False
            self._json({'success': True, 'running': False})
        
        elif path == '/api/job/enable':
            name = data.get('job')
            enabled = data.get('enabled', True)
            if name:
                db.update_job(name, enabled=1 if enabled else 0)
                self._json({'success': True})
            else:
                self._json({'success': False, 'error': 'Job name required'})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    global scheduler_running
    
    print("=" * 60)
    print("  BACKUP AUTO-SCHEDULER")
    print("  Port:", PORT)
    print("=" * 60)
    
    jobs = db.get_all_jobs()
    print(f"\nBackup jobs: {len(jobs)}")
    for j in jobs:
        config = json.loads(j['config'])
        print(f"  - {j['name']}: every {config.get('interval_hours', 24)}h, keep {config.get('keep_count', 10)}")
    
    backups = db.get_backups(limit=1000)
    total_size = sum(b['size_bytes'] for b in backups)
    print(f"\nTotal backups: {len(backups)} ({total_size / 1024 / 1024:.1f} MB)")
    
    # Start scheduler
    scheduler_running = True
    threading.Thread(target=run_scheduler, daemon=True).start()
    print("\nScheduler: RUNNING")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), BackupAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
