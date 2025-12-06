"""
GALLERY AUTO-SCHEDULER
======================
Automatically organizes generated images into galleries
Sorts by style, quality, rating, and date

Port: 8223
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
from urllib.parse import urlparse

# Configuration
PORT = 8223
DB_PATH = Path(r"c:\Users\Admin\civitai\data\gallery_scheduler.db")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\output")
GALLERY_DIR = Path(r"c:\Users\Admin\civitai\galleries")
ARCHIVE_DIR = Path(r"c:\Users\Admin\civitai\archive")

# Ensure directories
for d in [DB_PATH.parent, GALLERY_DIR, ARCHIVE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Gallery categories
GALLERY_CATEGORIES = {
    "tribal": {"patterns": ["tribal", "native", "indigenous"], "subfolder": "tribal"},
    "western": {"patterns": ["western", "cowboy", "frontier"], "subfolder": "western"},
    "anime": {"patterns": ["anime", "illustrious", "noob"], "subfolder": "anime"},
    "realistic": {"patterns": ["realistic", "photo", "pony"], "subfolder": "realistic"},
    "fantasy": {"patterns": ["fantasy", "elf", "magic"], "subfolder": "fantasy"},
    "portraits": {"patterns": ["portrait", "face", "headshot"], "subfolder": "portraits"},
    "nsfw": {"patterns": ["nsfw", "adult", "explicit"], "subfolder": "nsfw"},
    "sfw": {"patterns": ["sfw", "safe", "clean"], "subfolder": "sfw"}
}


class GalleryDB:
    """Database for gallery tracking"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS galleries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                path TEXT,
                category TEXT,
                image_count INTEGER DEFAULT 0,
                last_updated TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gallery_id INTEGER,
                filename TEXT NOT NULL,
                original_path TEXT,
                hash TEXT UNIQUE,
                category TEXT,
                rating TEXT,
                quality_score REAL,
                width INTEGER,
                height INTEGER,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS organize_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                details TEXT,
                images_moved INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        ''')
        self.conn.commit()
        self._init_galleries()
    
    def _init_galleries(self):
        for name, config in GALLERY_CATEGORIES.items():
            path = str(GALLERY_DIR / config['subfolder'])
            self.conn.execute('''
                INSERT OR IGNORE INTO galleries (name, path, category)
                VALUES (?, ?, ?)
            ''', (name, path, name))
            Path(path).mkdir(parents=True, exist_ok=True)
        self.conn.commit()
    
    def get_gallery(self, name):
        row = self.conn.execute(
            'SELECT * FROM galleries WHERE name = ?', (name,)
        ).fetchone()
        return dict(row) if row else None
    
    def get_all_galleries(self):
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM galleries ORDER BY name'
        ).fetchall()]
    
    def update_gallery(self, name, **kwargs):
        sets = ', '.join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(
            f'UPDATE galleries SET {sets} WHERE name = ?',
            list(kwargs.values()) + [name]
        )
        self.conn.commit()
    
    def add_image(self, gallery_id, filename, original_path, hash_val, category=None, rating=None):
        try:
            self.conn.execute('''
                INSERT INTO images (gallery_id, filename, original_path, hash, category, rating)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (gallery_id, filename, original_path, hash_val, category, rating))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def image_exists(self, hash_val):
        return self.conn.execute(
            'SELECT 1 FROM images WHERE hash = ?', (hash_val,)
        ).fetchone() is not None
    
    def log_action(self, action, details, images_moved=0):
        self.conn.execute('''
            INSERT INTO organize_logs (action, details, images_moved)
            VALUES (?, ?, ?)
        ''', (action, details, images_moved))
        self.conn.commit()
    
    def get_logs(self, limit=100):
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM organize_logs ORDER BY created_at DESC LIMIT ?', (limit,)
        ).fetchall()]
    
    def get_stats(self):
        total = self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]
        by_gallery = self.conn.execute('''
            SELECT g.name, COUNT(i.id) as count
            FROM galleries g
            LEFT JOIN images i ON g.id = i.gallery_id
            GROUP BY g.name
        ''').fetchall()
        return {
            'total_images': total,
            'by_gallery': {r[0]: r[1] for r in by_gallery}
        }


class GalleryOrganizer:
    """Organize images into galleries"""
    
    def __init__(self, db: GalleryDB):
        self.db = db
    
    def compute_hash(self, filepath):
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def classify_image(self, filepath):
        """Classify image based on path and filename"""
        path_str = str(filepath).lower()
        
        for category, config in GALLERY_CATEGORIES.items():
            for pattern in config['patterns']:
                if pattern in path_str:
                    return category
        
        return "uncategorized"
    
    def get_rating_from_path(self, filepath):
        """Extract rating from path or filename"""
        path_str = str(filepath).lower()
        
        ratings = ['nsfw', 'sfw', 'r18', 'adult', 'explicit', 'safe']
        for rating in ratings:
            if rating in path_str:
                return rating
        
        return "unknown"
    
    def scan_and_organize(self, source_dir=None):
        """Scan source directory and organize images"""
        source = Path(source_dir) if source_dir else OUTPUT_DIR
        
        if not source.exists():
            return 0, "Source directory not found"
        
        self.db.log_action('scan_start', f'Scanning {source}')
        
        moved = 0
        skipped = 0
        errors = 0
        
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
            for img_path in source.rglob(ext):
                try:
                    # Skip if already in gallery
                    if str(GALLERY_DIR) in str(img_path):
                        continue
                    
                    # Compute hash
                    img_hash = self.compute_hash(img_path)
                    
                    # Skip if duplicate
                    if self.db.image_exists(img_hash):
                        skipped += 1
                        continue
                    
                    # Classify
                    category = self.classify_image(img_path)
                    rating = self.get_rating_from_path(img_path)
                    
                    # Get target gallery
                    gallery = self.db.get_gallery(category)
                    if not gallery:
                        gallery = self.db.get_gallery("uncategorized")
                        if not gallery:
                            # Create uncategorized gallery
                            uncat_path = GALLERY_DIR / "uncategorized"
                            uncat_path.mkdir(exist_ok=True)
                            self.db.conn.execute('''
                                INSERT INTO galleries (name, path, category)
                                VALUES ('uncategorized', ?, 'other')
                            ''', (str(uncat_path),))
                            self.db.conn.commit()
                            gallery = self.db.get_gallery("uncategorized")
                    
                    # Create date-based subfolder
                    date_folder = datetime.now().strftime("%Y-%m")
                    target_dir = Path(gallery['path']) / date_folder
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy to gallery
                    dest_name = f"{img_hash[:8]}_{img_path.name}"
                    dest_path = target_dir / dest_name
                    
                    shutil.copy2(img_path, dest_path)
                    
                    # Copy caption if exists
                    for ext in ['.txt', '.caption']:
                        caption_src = img_path.with_suffix(ext)
                        if caption_src.exists():
                            shutil.copy2(caption_src, dest_path.with_suffix(ext))
                    
                    # Record in database
                    self.db.add_image(
                        gallery['id'], dest_name, str(img_path),
                        img_hash, category, rating
                    )
                    
                    moved += 1
                    
                except Exception as e:
                    errors += 1
                    print(f"Error processing {img_path}: {e}")
        
        # Update gallery counts
        for gallery in self.db.get_all_galleries():
            path = Path(gallery['path'])
            count = sum(1 for _ in path.rglob('*.png')) + sum(1 for _ in path.rglob('*.jpg'))
            self.db.update_gallery(
                gallery['name'],
                image_count=count,
                last_updated=datetime.now().isoformat()
            )
        
        self.db.log_action('scan_complete', 
                          f'Moved {moved}, skipped {skipped}, errors {errors}',
                          moved)
        
        return moved, f"Organized {moved} images, skipped {skipped}, errors {errors}"
    
    def archive_old_images(self, days_old=30):
        """Archive images older than specified days"""
        cutoff = datetime.now().timestamp() - (days_old * 86400)
        archived = 0
        
        for gallery in self.db.get_all_galleries():
            path = Path(gallery['path'])
            for img in path.rglob('*'):
                if img.is_file() and img.stat().st_mtime < cutoff:
                    # Move to archive
                    archive_path = ARCHIVE_DIR / gallery['name'] / img.parent.name
                    archive_path.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(img), str(archive_path / img.name))
                    archived += 1
        
        self.db.log_action('archive', f'Archived {archived} images older than {days_old} days', archived)
        return archived


# Initialize
db = GalleryDB()
organizer = GalleryOrganizer(db)

# Scheduler
scheduler_running = False


def run_scheduler():
    """Background organization scheduler"""
    global scheduler_running
    last_run = 0
    interval = 3600  # 1 hour
    
    while scheduler_running:
        if time.time() - last_run >= interval:
            print("[Gallery Scheduler] Running organization...")
            moved, msg = organizer.scan_and_organize()
            print(f"[Gallery Scheduler] {msg}")
            last_run = time.time()
        
        time.sleep(60)


class GalleryAPI(BaseHTTPRequestHandler):
    """Gallery Scheduler API"""
    
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
            stats = db.get_stats()
            self._json({
                'service': 'Gallery Auto-Scheduler',
                'version': '1.0',
                'port': PORT,
                'scheduler_running': scheduler_running,
                'total_images': stats['total_images'],
                'galleries': len(db.get_all_galleries())
            })
        
        elif path == '/api/galleries':
            self._json({'galleries': db.get_all_galleries()})
        
        elif path.startswith('/api/gallery/'):
            name = path.split('/')[-1]
            gallery = db.get_gallery(name)
            if gallery:
                self._json(gallery)
            else:
                self._json({'error': 'Not found'}, 404)
        
        elif path == '/api/stats':
            self._json(db.get_stats())
        
        elif path == '/api/logs':
            self._json({'logs': db.get_logs()})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/organize':
            source = data.get('source_dir')
            moved, msg = organizer.scan_and_organize(source)
            self._json({'success': True, 'moved': moved, 'message': msg})
        
        elif path == '/api/archive':
            days = data.get('days_old', 30)
            archived = organizer.archive_old_images(days)
            self._json({'success': True, 'archived': archived})
        
        elif path == '/api/scheduler/start':
            global scheduler_running
            if not scheduler_running:
                scheduler_running = True
                threading.Thread(target=run_scheduler, daemon=True).start()
            self._json({'success': True, 'running': True})
        
        elif path == '/api/scheduler/stop':
            scheduler_running = False
            self._json({'success': True, 'running': False})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    global scheduler_running
    
    print("=" * 60)
    print("  GALLERY AUTO-SCHEDULER")
    print("  Port:", PORT)
    print("=" * 60)
    
    galleries = db.get_all_galleries()
    stats = db.get_stats()
    
    print(f"\nGalleries: {len(galleries)}")
    for g in galleries:
        print(f"  - {g['name']}: {g['image_count']} images")
    print(f"\nTotal images: {stats['total_images']}")
    
    # Start scheduler
    scheduler_running = True
    threading.Thread(target=run_scheduler, daemon=True).start()
    print("\nScheduler: RUNNING")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), GalleryAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
