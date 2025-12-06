"""
Simple Gallery Rater
- Load all images from output folder
- Rate 0-15 with simple interface
- One-click training button
"""
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading
import time

OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\advanced_learning.db")
THUMBS_PER_PAGE = 50

class GalleryRater:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._ensure_tables()
        
    def _ensure_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS images (
            image_id TEXT PRIMARY KEY,
            filename TEXT UNIQUE,
            prompt TEXT,
            negative_prompt TEXT,
            tags TEXT,
            model TEXT,
            seed INTEGER,
            rating REAL DEFAULT 0,
            rating_history TEXT DEFAULT '[]',
            created_at TEXT,
            rated_at TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS tag_analysis (
            tag TEXT PRIMARY KEY,
            category TEXT,
            avg_rating REAL DEFAULT 0,
            high_rating_count INTEGER DEFAULT 0,
            low_rating_count INTEGER DEFAULT 0,
            weight REAL DEFAULT 0.5,
            last_high_rating TEXT
        )''')
        self.conn.commit()
        
    def scan_images(self) -> dict:
        """Scan output folder and register all images"""
        images = list(OUTPUT_DIR.glob("*.png"))
        cursor = self.conn.cursor()
        
        new_count = 0
        for img in images:
            cursor.execute('SELECT 1 FROM images WHERE filename = ?', (img.name,))
            if not cursor.fetchone():
                image_id = f"img_{int(datetime.now().timestamp()*1000)}"
                cursor.execute('''INSERT INTO images (image_id, filename, created_at)
                    VALUES (?, ?, ?)''', (image_id, img.name, datetime.now().isoformat()))
                new_count += 1
                
        self.conn.commit()
        
        cursor.execute('SELECT COUNT(*) FROM images')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating > 0')
        rated = cursor.fetchone()[0]
        
        return {'total': total, 'new': new_count, 'rated': rated, 'unrated': total - rated}
        
    def get_unrated_images(self, limit: int = 50) -> list:
        """Get unrated images for rating"""
        cursor = self.conn.cursor()
        cursor.execute('''SELECT image_id, filename FROM images 
            WHERE rating = 0 OR rating IS NULL
            ORDER BY created_at DESC LIMIT ?''', (limit,))
        return [{'id': r[0], 'filename': r[1]} for r in cursor.fetchall()]
        
    def get_all_images(self, page: int = 1, per_page: int = 50) -> list:
        """Get all images paginated"""
        cursor = self.conn.cursor()
        offset = (page - 1) * per_page
        cursor.execute('''SELECT image_id, filename, rating FROM images 
            ORDER BY created_at DESC LIMIT ? OFFSET ?''', (per_page, offset))
        return [{'id': r[0], 'filename': r[1], 'rating': r[2] or 0} for r in cursor.fetchall()]
        
    def rate_image(self, image_id: str, rating: float) -> dict:
        """Rate an image"""
        rating = max(0, min(15, rating))
        cursor = self.conn.cursor()
        
        cursor.execute('UPDATE images SET rating = ?, rated_at = ? WHERE image_id = ?',
                      (rating, datetime.now().isoformat(), image_id))
        self.conn.commit()
        
        return {'image_id': image_id, 'rating': rating, 'status': 'saved'}
        
    def get_stats(self) -> dict:
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM images')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating > 0')
        rated = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating >= 10')
        excellent = cursor.fetchone()[0]
        cursor.execute('SELECT AVG(rating) FROM images WHERE rating > 0')
        avg = cursor.fetchone()[0] or 0
        
        return {
            'total_images': total,
            'rated': rated,
            'unrated': total - rated,
            'excellent': excellent,
            'avg_rating': round(avg, 1),
            'percent_rated': round((rated/total)*100, 1) if total else 0
        }
        
    def close(self):
        self.conn.close()


class TrainingProcessor:
    """Process ratings and build learning models"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.running = False
        self.progress = 0
        self.status = "idle"
        
    def start_training(self, duration_minutes: int = 30):
        """Start training process"""
        self.running = True
        self.progress = 0
        self.status = "Starting..."
        
        thread = threading.Thread(target=self._run_training, args=(duration_minutes,))
        thread.start()
        
        return {'status': 'started', 'duration': duration_minutes}
        
    def _run_training(self, duration_minutes: int):
        """Run the full training pipeline"""
        cursor = self.conn.cursor()
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        steps = [
            ("Analyzing rated images", self._analyze_ratings, 20),
            ("Building tag weights", self._build_tag_weights, 25),
            ("Finding patterns", self._find_patterns, 25),
            ("Creating model data", self._create_model, 20),
            ("Saving results", self._save_results, 10)
        ]
        
        total_weight = sum(s[2] for s in steps)
        progress_per_weight = 100 / total_weight
        
        for step_name, step_func, weight in steps:
            if not self.running:
                break
                
            self.status = step_name
            step_func(cursor)
            self.progress += weight * progress_per_weight
            
            # Wait proportionally
            step_duration = (weight / total_weight) * (duration_minutes * 60)
            time.sleep(min(step_duration, 60))  # Max 60 sec per step
            
        self.status = "Complete!"
        self.progress = 100
        self.running = False
        self.conn.commit()
        
    def _analyze_ratings(self, cursor):
        """Analyze all rated images"""
        cursor.execute('''SELECT filename, rating, tags FROM images WHERE rating > 0''')
        self.rated_images = cursor.fetchall()
        
    def _build_tag_weights(self, cursor):
        """Build tag weights from ratings"""
        from collections import defaultdict
        tag_ratings = defaultdict(list)
        
        for filename, rating, tags_json in self.rated_images:
            tags = json.loads(tags_json) if tags_json else []
            # Also extract from filename
            parts = filename.replace('.png', '').replace('_', ' ').split()
            tags.extend([p for p in parts if len(p) > 2])
            
            for tag in tags:
                tag_ratings[tag].append(rating)
                
        # Calculate weights
        for tag, ratings in tag_ratings.items():
            avg = sum(ratings) / len(ratings)
            high_count = sum(1 for r in ratings if r >= 10)
            low_count = sum(1 for r in ratings if r <= 5)
            weight = (high_count + 1) / (high_count + low_count + 2)
            
            cursor.execute('''INSERT OR REPLACE INTO tag_analysis 
                (tag, avg_rating, high_rating_count, low_rating_count, weight, last_high_rating)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (tag, avg, high_count, low_count, weight, 
                 datetime.now().isoformat() if high_count > 0 else None))
                 
    def _find_patterns(self, cursor):
        """Find winning patterns"""
        cursor.execute('''SELECT tag, weight FROM tag_analysis 
            WHERE weight > 0.6 ORDER BY weight DESC''')
        self.winning_tags = cursor.fetchall()
        
    def _create_model(self, cursor):
        """Create preference model"""
        model = {
            'created_at': datetime.now().isoformat(),
            'total_rated': len(self.rated_images),
            'winning_tags': [{'tag': t[0], 'weight': t[1]} for t in self.winning_tags[:50]],
            'avg_rating': sum(r[1] for r in self.rated_images) / len(self.rated_images) if self.rated_images else 0
        }
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS preference_models 
            (id INTEGER PRIMARY KEY, model_name TEXT, model_data TEXT, created_at TEXT)''')
        cursor.execute('''INSERT INTO preference_models (model_name, model_data, created_at)
            VALUES (?, ?, ?)''', ('user_preferences', json.dumps(model), datetime.now().isoformat()))
            
    def _save_results(self, cursor):
        """Save all results"""
        pass  # Commit happens in parent
        
    def get_status(self) -> dict:
        return {
            'running': self.running,
            'progress': round(self.progress, 1),
            'status': self.status
        }
        
    def close(self):
        self.conn.close()


# ==================== WEB GALLERY UI ====================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>Image Gallery Rater</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }
        h1 { text-align: center; margin-bottom: 20px; color: #00d4ff; }
        .stats { display: flex; justify-content: center; gap: 30px; margin-bottom: 20px; padding: 15px; background: #16213e; border-radius: 10px; }
        .stat { text-align: center; }
        .stat-value { font-size: 28px; font-weight: bold; color: #00d4ff; }
        .stat-label { font-size: 12px; color: #888; }
        .controls { display: flex; justify-content: center; gap: 15px; margin-bottom: 20px; }
        button { padding: 12px 25px; font-size: 16px; border: none; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
        .btn-scan { background: #00d4ff; color: #000; }
        .btn-train { background: #ff6b6b; color: #fff; }
        .btn-train:hover { background: #ff5252; }
        .progress-bar { width: 100%; height: 30px; background: #16213e; border-radius: 15px; margin: 20px 0; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #ff6b6b); transition: width 0.5s; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
        .image-card { background: #16213e; border-radius: 10px; overflow: hidden; transition: transform 0.3s; }
        .image-card:hover { transform: scale(1.02); }
        .image-card img { width: 100%; height: 200px; object-fit: cover; cursor: pointer; }
        .image-info { padding: 10px; }
        .rating-input { width: 100%; display: flex; gap: 5px; align-items: center; }
        .rating-input input { flex: 1; height: 30px; }
        .rating-input span { min-width: 30px; text-align: center; font-weight: bold; }
        .rating-btn { padding: 5px 15px; background: #00d4ff; color: #000; border: none; border-radius: 5px; cursor: pointer; }
        .rated { border: 3px solid #00d4ff; }
        .excellent { border: 3px solid #ffd700; }
        .status-bar { position: fixed; bottom: 0; left: 0; right: 0; background: #16213e; padding: 10px; text-align: center; }
    </style>
</head>
<body>
    <h1>🎨 Image Gallery Rater</h1>
    
    <div class="stats" id="stats">
        <div class="stat"><div class="stat-value" id="total">-</div><div class="stat-label">Total Images</div></div>
        <div class="stat"><div class="stat-value" id="rated">-</div><div class="stat-label">Rated</div></div>
        <div class="stat"><div class="stat-value" id="unrated">-</div><div class="stat-label">Unrated</div></div>
        <div class="stat"><div class="stat-value" id="excellent">-</div><div class="stat-label">Excellent (10+)</div></div>
        <div class="stat"><div class="stat-value" id="avg">-</div><div class="stat-label">Avg Rating</div></div>
    </div>
    
    <div class="controls">
        <button class="btn-scan" onclick="scanImages()">🔄 Scan New Images</button>
        <button class="btn-train" onclick="startTraining()">🚀 Start 30min Training</button>
    </div>
    
    <div class="progress-bar" id="progressBar" style="display:none;">
        <div class="progress-fill" id="progressFill" style="width:0%"></div>
    </div>
    <div id="trainingStatus" style="text-align:center; margin-bottom:20px;"></div>
    
    <div class="gallery" id="gallery"></div>
    
    <div class="status-bar" id="statusBar">Loading...</div>
    
    <script>
        const API = '';
        let images = [];
        
        async function loadStats() {
            const res = await fetch(API + '/api/stats');
            const stats = await res.json();
            document.getElementById('total').textContent = stats.total_images;
            document.getElementById('rated').textContent = stats.rated;
            document.getElementById('unrated').textContent = stats.unrated;
            document.getElementById('excellent').textContent = stats.excellent;
            document.getElementById('avg').textContent = stats.avg_rating;
        }
        
        async function loadImages() {
            const res = await fetch(API + '/api/images');
            images = await res.json();
            renderGallery();
        }
        
        function renderGallery() {
            const gallery = document.getElementById('gallery');
            gallery.innerHTML = images.map(img => `
                <div class="image-card ${img.rating >= 10 ? 'excellent' : img.rating > 0 ? 'rated' : ''}">
                    <img src="/image/${img.filename}" onclick="window.open('/image/${img.filename}', '_blank')">
                    <div class="image-info">
                        <div class="rating-input">
                            <input type="range" min="0" max="15" value="${img.rating}" 
                                   onchange="updateRatingDisplay(this, '${img.id}')" 
                                   oninput="this.nextElementSibling.textContent = this.value">
                            <span>${img.rating}</span>
                            <button class="rating-btn" onclick="saveRating('${img.id}', this.previousElementSibling.previousElementSibling.value)">✓</button>
                        </div>
                    </div>
                </div>
            `).join('');
            document.getElementById('statusBar').textContent = `Showing ${images.length} images`;
        }
        
        async function saveRating(id, rating) {
            await fetch(API + '/api/rate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({image_id: id, rating: parseFloat(rating)})
            });
            loadStats();
            loadImages();
        }
        
        async function scanImages() {
            document.getElementById('statusBar').textContent = 'Scanning...';
            const res = await fetch(API + '/api/scan');
            const result = await res.json();
            document.getElementById('statusBar').textContent = `Found ${result.new} new images. Total: ${result.total}`;
            loadStats();
            loadImages();
        }
        
        async function startTraining() {
            document.getElementById('progressBar').style.display = 'block';
            const res = await fetch(API + '/api/train', {method: 'POST'});
            checkTrainingStatus();
        }
        
        async function checkTrainingStatus() {
            const res = await fetch(API + '/api/train/status');
            const status = await res.json();
            document.getElementById('progressFill').style.width = status.progress + '%';
            document.getElementById('trainingStatus').textContent = status.status + ' (' + status.progress + '%)';
            
            if (status.running) {
                setTimeout(checkTrainingStatus, 2000);
            } else {
                document.getElementById('statusBar').textContent = 'Training complete!';
                loadStats();
            }
        }
        
        loadStats();
        loadImages();
    </script>
</body>
</html>'''


class GalleryHandler(BaseHTTPRequestHandler):
    rater = None
    trainer = None
    
    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
    def _html(self, content):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())
        
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/':
            self._html(HTML_TEMPLATE)
        elif path == '/api/stats':
            self._json(self.rater.get_stats())
        elif path == '/api/images':
            self._json(self.rater.get_all_images())
        elif path == '/api/scan':
            self._json(self.rater.scan_images())
        elif path == '/api/train/status':
            self._json(self.trainer.get_status())
        elif path.startswith('/image/'):
            filename = path.replace('/image/', '')
            img_path = OUTPUT_DIR / filename
            if img_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                with open(img_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self._json({'error': 'not found'})
            
    def do_POST(self):
        path = self.path
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length else {}
        
        if path == '/api/rate':
            result = self.rater.rate_image(data['image_id'], data['rating'])
            self._json(result)
        elif path == '/api/train':
            result = self.trainer.start_training(30)
            self._json(result)
        else:
            self._json({'error': 'not found'})
            
    def log_message(self, *args): pass


def start_gallery_server(port: int = 8191):
    """Start the gallery rating server"""
    print("="*60)
    print("  SIMPLE GALLERY RATER")
    print("="*60)
    
    GalleryHandler.rater = GalleryRater()
    GalleryHandler.trainer = TrainingProcessor()
    
    # Initial scan
    print("\n📷 Scanning images...")
    result = GalleryHandler.rater.scan_images()
    print(f"   Total: {result['total']} images")
    print(f"   Rated: {result['rated']}")
    print(f"   Unrated: {result['unrated']}")
    
    print(f"\n🌐 Gallery: http://127.0.0.1:{port}")
    print(f"\n📋 HOW TO USE:")
    print(f"   1. Open browser to http://127.0.0.1:{port}")
    print(f"   2. Use sliders to rate each image (0-15)")
    print(f"   3. Click ✓ to save rating")
    print(f"   4. Click 'Start 30min Training' when ready")
    print(f"\n✅ Server ready!")
    
    server = HTTPServer(('0.0.0.0', port), GalleryHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        GalleryHandler.rater.close()
        GalleryHandler.trainer.close()


if __name__ == "__main__":
    start_gallery_server()
