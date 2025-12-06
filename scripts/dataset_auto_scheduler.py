"""
DATASET AUTO-SCHEDULER
=======================
Automatically builds and organizes training datasets
Monitors output folders and creates balanced datasets

Port: 8222
"""
import os
import json
import sqlite3
import shutil
import hashlib
import threading
import time
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configuration
PORT = 8222
DB_PATH = Path(r"c:\Users\Admin\civitai\data\dataset_scheduler.db")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\output")
DATASET_DIR = Path(r"c:\Users\Admin\civitai\datasets")
TRAINING_DIR = Path(r"G:\AI_Training\datasets")

# Ensure directories
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATASET_DIR.mkdir(parents=True, exist_ok=True)

# Dataset configurations
DATASET_CONFIGS = {
    "tribal_portraits": {
        "source_patterns": ["tribal_*", "*tribal*", "*native*"],
        "target_size": 512,
        "min_images": 50,
        "max_images": 500,
        "caption_required": True
    },
    "western_scenes": {
        "source_patterns": ["western_*", "*cowboy*", "*frontier*"],
        "target_size": 768,
        "min_images": 100,
        "max_images": 1000,
        "caption_required": True
    },
    "anime_style": {
        "source_patterns": ["anime_*", "*illustrious*", "*noob*"],
        "target_size": 1024,
        "min_images": 200,
        "max_images": 2000,
        "caption_required": True
    },
    "realistic_photos": {
        "source_patterns": ["realistic_*", "*photo*", "*pony*"],
        "target_size": 1024,
        "min_images": 100,
        "max_images": 1500,
        "caption_required": True
    }
}


class DatasetDB:
    """Database for dataset tracking"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                config TEXT,
                status TEXT DEFAULT 'pending',
                image_count INTEGER DEFAULT 0,
                last_build TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER,
                filename TEXT NOT NULL,
                hash TEXT UNIQUE,
                caption TEXT,
                width INTEGER,
                height INTEGER,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS build_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER,
                action TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT,
                schedule_type TEXT,
                interval_hours INTEGER DEFAULT 24,
                last_run TEXT,
                next_run TEXT,
                enabled INTEGER DEFAULT 1
            );
        ''')
        self.conn.commit()
        self._init_datasets()
    
    def _init_datasets(self):
        for name, config in DATASET_CONFIGS.items():
            self.conn.execute('''
                INSERT OR IGNORE INTO datasets (name, config)
                VALUES (?, ?)
            ''', (name, json.dumps(config)))
        self.conn.commit()
    
    def get_dataset(self, name):
        row = self.conn.execute(
            'SELECT * FROM datasets WHERE name = ?', (name,)
        ).fetchone()
        return dict(row) if row else None
    
    def get_all_datasets(self):
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM datasets ORDER BY name'
        ).fetchall()]
    
    def update_dataset(self, name, **kwargs):
        sets = ', '.join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(
            f'UPDATE datasets SET {sets} WHERE name = ?',
            list(kwargs.values()) + [name]
        )
        self.conn.commit()
    
    def add_image(self, dataset_id, filename, hash_val, caption=None, width=0, height=0):
        try:
            self.conn.execute('''
                INSERT INTO images (dataset_id, filename, hash, caption, width, height)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (dataset_id, filename, hash_val, caption, width, height))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Duplicate hash
    
    def get_dataset_images(self, dataset_id):
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM images WHERE dataset_id = ?', (dataset_id,)
        ).fetchall()]
    
    def log_build(self, dataset_id, action, details):
        self.conn.execute('''
            INSERT INTO build_logs (dataset_id, action, details)
            VALUES (?, ?, ?)
        ''', (dataset_id, action, details))
        self.conn.commit()
    
    def get_logs(self, dataset_id=None, limit=100):
        if dataset_id:
            return [dict(r) for r in self.conn.execute('''
                SELECT l.*, d.name as dataset_name
                FROM build_logs l
                LEFT JOIN datasets d ON l.dataset_id = d.id
                WHERE l.dataset_id = ?
                ORDER BY l.created_at DESC LIMIT ?
            ''', (dataset_id, limit)).fetchall()]
        return [dict(r) for r in self.conn.execute('''
            SELECT l.*, d.name as dataset_name
            FROM build_logs l
            LEFT JOIN datasets d ON l.dataset_id = d.id
            ORDER BY l.created_at DESC LIMIT ?
        ''', (limit,)).fetchall()]
    
    def get_schedule(self, dataset_name):
        row = self.conn.execute(
            'SELECT * FROM schedules WHERE dataset_name = ?', (dataset_name,)
        ).fetchone()
        return dict(row) if row else None
    
    def set_schedule(self, dataset_name, schedule_type, interval_hours):
        next_run = datetime.now().isoformat()
        self.conn.execute('''
            INSERT OR REPLACE INTO schedules 
            (dataset_name, schedule_type, interval_hours, next_run, enabled)
            VALUES (?, ?, ?, ?, 1)
        ''', (dataset_name, schedule_type, interval_hours, next_run))
        self.conn.commit()


class DatasetBuilder:
    """Build and organize datasets"""
    
    def __init__(self, db: DatasetDB):
        self.db = db
    
    def scan_source_images(self, patterns):
        """Find images matching patterns in output directory"""
        images = []
        for pattern in patterns:
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
                for f in OUTPUT_DIR.rglob(f"{pattern}/{ext}"):
                    images.append(f)
                # Also search with pattern in filename
                for f in OUTPUT_DIR.rglob(ext):
                    if any(p.replace('*', '') in f.name.lower() for p in patterns if '*' in p):
                        if f not in images:
                            images.append(f)
        return images
    
    def compute_hash(self, filepath):
        """Compute file hash for deduplication"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def find_caption(self, image_path):
        """Find caption file for image"""
        caption_path = image_path.with_suffix('.txt')
        if caption_path.exists():
            return caption_path.read_text(encoding='utf-8').strip()
        
        # Try .caption extension
        caption_path = image_path.with_suffix('.caption')
        if caption_path.exists():
            return caption_path.read_text(encoding='utf-8').strip()
        
        return None
    
    def build_dataset(self, dataset_name):
        """Build a dataset from source images"""
        dataset = self.db.get_dataset(dataset_name)
        if not dataset:
            return False, "Dataset not found"
        
        config = json.loads(dataset['config'])
        self.db.update_dataset(dataset_name, status='building')
        self.db.log_build(dataset['id'], 'start', f'Building {dataset_name}')
        
        # Create dataset directory
        ds_path = DATASET_DIR / dataset_name
        ds_path.mkdir(parents=True, exist_ok=True)
        
        # Find source images
        source_images = self.scan_source_images(config['source_patterns'])
        self.db.log_build(dataset['id'], 'scan', f'Found {len(source_images)} source images')
        
        added = 0
        skipped = 0
        
        for img_path in source_images[:config['max_images']]:
            try:
                # Compute hash for dedup
                img_hash = self.compute_hash(img_path)
                
                # Check caption if required
                caption = self.find_caption(img_path)
                if config['caption_required'] and not caption:
                    skipped += 1
                    continue
                
                # Copy to dataset
                dest_name = f"{img_hash[:8]}_{img_path.name}"
                dest_path = ds_path / dest_name
                
                if not dest_path.exists():
                    shutil.copy2(img_path, dest_path)
                    
                    # Copy caption if exists
                    if caption:
                        caption_dest = dest_path.with_suffix('.txt')
                        caption_dest.write_text(caption, encoding='utf-8')
                    
                    # Add to database
                    if self.db.add_image(dataset['id'], dest_name, img_hash, caption):
                        added += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                self.db.log_build(dataset['id'], 'error', f'Failed: {img_path.name} - {e}')
        
        # Update dataset status
        total_images = len(list(ds_path.glob('*.png'))) + len(list(ds_path.glob('*.jpg')))
        self.db.update_dataset(
            dataset_name,
            status='ready' if total_images >= config['min_images'] else 'incomplete',
            image_count=total_images,
            last_build=datetime.now().isoformat()
        )
        
        self.db.log_build(dataset['id'], 'complete', 
                         f'Added {added}, skipped {skipped}, total {total_images}')
        
        return True, f"Dataset built: {added} added, {total_images} total"
    
    def export_for_training(self, dataset_name, target_dir=None):
        """Export dataset in Kohya format"""
        dataset = self.db.get_dataset(dataset_name)
        if not dataset:
            return False, "Dataset not found"
        
        ds_path = DATASET_DIR / dataset_name
        if not ds_path.exists():
            return False, "Dataset directory not found"
        
        # Target directory
        if target_dir:
            export_path = Path(target_dir)
        else:
            export_path = TRAINING_DIR / dataset_name
        
        export_path.mkdir(parents=True, exist_ok=True)
        
        # Create Kohya structure: repeats_concept
        concept_dir = export_path / f"10_{dataset_name}"
        concept_dir.mkdir(exist_ok=True)
        
        copied = 0
        for img in ds_path.glob('*'):
            if img.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                dest = concept_dir / img.name
                if not dest.exists():
                    shutil.copy2(img, dest)
                    # Copy caption
                    caption = img.with_suffix('.txt')
                    if caption.exists():
                        shutil.copy2(caption, dest.with_suffix('.txt'))
                    copied += 1
        
        self.db.log_build(dataset['id'], 'export', 
                         f'Exported {copied} images to {export_path}')
        
        return True, f"Exported to {export_path}"


# Initialize
db = DatasetDB()
builder = DatasetBuilder(db)

# Background scheduler
scheduler_running = False
scheduler_thread = None


def run_scheduler():
    """Background scheduler loop"""
    global scheduler_running
    while scheduler_running:
        try:
            for ds in db.get_all_datasets():
                schedule = db.get_schedule(ds['name'])
                if schedule and schedule['enabled']:
                    next_run = datetime.fromisoformat(schedule['next_run'])
                    if datetime.now() >= next_run:
                        print(f"[Scheduler] Building {ds['name']}...")
                        builder.build_dataset(ds['name'])
                        
                        # Update next run
                        interval = schedule['interval_hours']
                        new_next = datetime.now().timestamp() + (interval * 3600)
                        db.conn.execute(
                            'UPDATE schedules SET last_run = ?, next_run = ? WHERE dataset_name = ?',
                            (datetime.now().isoformat(), 
                             datetime.fromtimestamp(new_next).isoformat(),
                             ds['name'])
                        )
                        db.conn.commit()
        except Exception as e:
            print(f"[Scheduler] Error: {e}")
        
        time.sleep(60)  # Check every minute


class DatasetAPI(BaseHTTPRequestHandler):
    """Dataset Scheduler API"""
    
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
            self._json({
                'service': 'Dataset Auto-Scheduler',
                'version': '1.0',
                'port': PORT,
                'scheduler_running': scheduler_running,
                'datasets': len(db.get_all_datasets())
            })
        
        elif path == '/api/datasets':
            datasets = db.get_all_datasets()
            for ds in datasets:
                ds['config'] = json.loads(ds['config']) if ds.get('config') else {}
            self._json({'datasets': datasets})
        
        elif path.startswith('/api/dataset/'):
            name = path.split('/')[-1]
            dataset = db.get_dataset(name)
            if dataset:
                dataset['config'] = json.loads(dataset['config']) if dataset.get('config') else {}
                dataset['images'] = db.get_dataset_images(dataset['id'])
                dataset['schedule'] = db.get_schedule(name)
                self._json(dataset)
            else:
                self._json({'error': 'Not found'}, 404)
        
        elif path == '/api/logs':
            self._json({'logs': db.get_logs()})
        
        elif path == '/api/status':
            self._json({
                'scheduler_running': scheduler_running,
                'datasets': [
                    {'name': d['name'], 'status': d['status'], 'count': d['image_count']}
                    for d in db.get_all_datasets()
                ]
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/build':
            name = data.get('dataset')
            if name:
                success, msg = builder.build_dataset(name)
                self._json({'success': success, 'message': msg})
            else:
                self._json({'success': False, 'error': 'Dataset name required'})
        
        elif path == '/api/build-all':
            results = []
            for ds in db.get_all_datasets():
                success, msg = builder.build_dataset(ds['name'])
                results.append({'dataset': ds['name'], 'success': success, 'message': msg})
            self._json({'results': results})
        
        elif path == '/api/export':
            name = data.get('dataset')
            target = data.get('target_dir')
            if name:
                success, msg = builder.export_for_training(name, target)
                self._json({'success': success, 'message': msg})
            else:
                self._json({'success': False, 'error': 'Dataset name required'})
        
        elif path == '/api/schedule':
            name = data.get('dataset')
            schedule_type = data.get('type', 'interval')
            interval = data.get('interval_hours', 24)
            if name:
                db.set_schedule(name, schedule_type, interval)
                self._json({'success': True})
            else:
                self._json({'success': False, 'error': 'Dataset name required'})
        
        elif path == '/api/scheduler/start':
            global scheduler_running, scheduler_thread
            if not scheduler_running:
                scheduler_running = True
                scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
                scheduler_thread.start()
            self._json({'success': True, 'running': True})
        
        elif path == '/api/scheduler/stop':
            scheduler_running = False
            self._json({'success': True, 'running': False})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    global scheduler_running, scheduler_thread
    
    print("=" * 60)
    print("  DATASET AUTO-SCHEDULER")
    print("  Port:", PORT)
    print("=" * 60)
    
    datasets = db.get_all_datasets()
    print(f"\nDatasets configured: {len(datasets)}")
    for ds in datasets:
        print(f"  - {ds['name']}: {ds['status']} ({ds['image_count']} images)")
    
    # Start scheduler
    scheduler_running = True
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("\nScheduler: RUNNING")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), DatasetAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
