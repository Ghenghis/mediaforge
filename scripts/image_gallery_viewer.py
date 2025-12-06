"""
IMAGE GALLERY VIEWER WITH 3D EFFECTS
- Browse all 207 images
- 3D perspective viewer
- Quick rating (0-15)
- Keyboard shortcuts
"""
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\master_learning.db")

class GalleryDB:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()
        
    def _ensure_tables(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY, filename TEXT UNIQUE, filepath TEXT,
            prompt TEXT, negative_prompt TEXT, tags TEXT, image_type TEXT,
            rating REAL DEFAULT 0, rating_count INTEGER DEFAULT 0,
            rating_history TEXT DEFAULT '[]', is_gold_standard INTEGER DEFAULT 0,
            created_at TEXT, rated_at TEXT
        )''')
        self.conn.commit()
        
    def scan_all(self):
        images = list(OUTPUT_DIR.glob("*.png"))
        new = 0
        for img in images:
            exists = self.conn.execute('SELECT 1 FROM images WHERE filename=?', (img.name,)).fetchone()
            if not exists:
                img_id = f"img_{hash(img.name) % 10**8}"
                self.conn.execute('INSERT INTO images (id, filename, filepath, created_at) VALUES (?,?,?,?)',
                    (img_id, img.name, str(img), datetime.now().isoformat()))
                new += 1
        self.conn.commit()
        return {'total': len(images), 'new': new}
        
    def get_all(self, sort='date', filter_rated=None):
        sql = 'SELECT id, filename, rating, is_gold_standard, created_at FROM images'
        if filter_rated == 'unrated':
            sql += ' WHERE rating = 0 OR rating IS NULL'
        elif filter_rated == 'rated':
            sql += ' WHERE rating > 0'
        elif filter_rated == 'excellent':
            sql += ' WHERE rating >= 10'
            
        if sort == 'rating':
            sql += ' ORDER BY rating DESC'
        elif sort == 'name':
            sql += ' ORDER BY filename'
        else:
            sql += ' ORDER BY created_at DESC'
            
        return [dict(r) for r in self.conn.execute(sql).fetchall()]
        
    def rate(self, img_id, rating):
        rating = max(0, min(15, float(rating)))
        self.conn.execute('UPDATE images SET rating=?, rated_at=?, is_gold_standard=? WHERE id=?',
            (rating, datetime.now().isoformat(), 1 if rating >= 15 else 0, img_id))
        self.conn.commit()
        return {'id': img_id, 'rating': rating}
        
    def get_stats(self):
        total = self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]
        rated = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
        excellent = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 10').fetchone()[0]
        gold = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 15').fetchone()[0]
        avg = self.conn.execute('SELECT AVG(rating) FROM images WHERE rating > 0').fetchone()[0] or 0
        return {'total': total, 'rated': rated, 'unrated': total-rated, 
                'excellent': excellent, 'gold': gold, 'avg': round(avg, 1)}

db = GalleryDB()

HTML = '''<!DOCTYPE html>
<html><head><title>3D Image Gallery</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui; background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%); 
       color: #fff; min-height: 100vh; overflow-x: hidden; }

/* Header */
.header { background: rgba(0,0,0,0.5); padding: 15px 20px; display: flex; 
          justify-content: space-between; align-items: center; backdrop-filter: blur(10px); 
          position: sticky; top: 0; z-index: 100; }
.header h1 { font-size: 24px; background: linear-gradient(90deg, #00d4ff, #ff6b6b); 
             -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stats { display: flex; gap: 20px; }
.stat { text-align: center; }
.stat-value { font-size: 24px; font-weight: bold; color: #00d4ff; }
.stat-label { font-size: 10px; color: #888; }

/* Controls */
.controls { padding: 15px 20px; display: flex; gap: 10px; flex-wrap: wrap; 
            background: rgba(0,0,0,0.3); }
button { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; 
         font-size: 14px; transition: all 0.3s; }
.btn-primary { background: linear-gradient(135deg, #00d4ff, #0099cc); color: #000; }
.btn-secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); }
.btn-gold { background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; }
button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,212,255,0.3); }
select { padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.1); 
         color: #fff; border: 1px solid rgba(255,255,255,0.2); }

/* 3D Gallery */
.gallery-3d { perspective: 2000px; padding: 40px 20px; min-height: 60vh; }
.gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); 
                gap: 20px; transform-style: preserve-3d; }
.card-3d { background: rgba(255,255,255,0.05); border-radius: 15px; overflow: hidden;
           transform-style: preserve-3d; transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
           border: 2px solid transparent; cursor: pointer; }
.card-3d:hover { transform: translateZ(50px) rotateY(5deg) scale(1.05); 
                 box-shadow: 0 25px 50px rgba(0,0,0,0.5), 0 0 30px rgba(0,212,255,0.3); }
.card-3d.excellent { border-color: #ffd700; box-shadow: 0 0 20px rgba(255,215,0,0.3); }
.card-3d.gold { border-color: #ff6b6b; box-shadow: 0 0 30px rgba(255,107,107,0.5); 
                animation: glow 2s ease-in-out infinite; }
@keyframes glow { 0%, 100% { box-shadow: 0 0 30px rgba(255,107,107,0.5); } 
                  50% { box-shadow: 0 0 50px rgba(255,107,107,0.8); } }
.card-3d img { width: 100%; height: 180px; object-fit: cover; transition: transform 0.3s; }
.card-3d:hover img { transform: scale(1.1); }
.card-info { padding: 12px; background: rgba(0,0,0,0.5); }
.card-name { font-size: 11px; color: #888; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rating-display { display: flex; align-items: center; gap: 10px; margin-top: 8px; }
.rating-value { font-size: 28px; font-weight: bold; 
                background: linear-gradient(90deg, #00d4ff, #ff6b6b); 
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.rating-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; }
.rating-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #ff6b6b); transition: width 0.3s; }

/* Modal Viewer */
.modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000;
         backdrop-filter: blur(20px); }
.modal.active { display: flex; }
.modal-content { display: flex; width: 100%; height: 100%; }
.modal-image-container { flex: 1; display: flex; align-items: center; justify-content: center;
                         perspective: 1000px; padding: 40px; }
.modal-image { max-width: 90%; max-height: 90vh; border-radius: 10px; 
               box-shadow: 0 30px 100px rgba(0,0,0,0.8); transition: transform 0.5s;
               transform-style: preserve-3d; }
.modal-image:hover { transform: rotateY(5deg) rotateX(2deg) scale(1.02); }
.modal-sidebar { width: 350px; background: rgba(255,255,255,0.05); padding: 30px;
                 display: flex; flex-direction: column; gap: 20px; }
.modal-close { position: absolute; top: 20px; right: 20px; font-size: 30px; 
               color: #fff; cursor: pointer; opacity: 0.7; z-index: 1001; }
.modal-close:hover { opacity: 1; }
.modal-nav { position: absolute; top: 50%; transform: translateY(-50%); 
             font-size: 50px; color: #fff; cursor: pointer; opacity: 0.5; padding: 20px; }
.modal-nav:hover { opacity: 1; }
.modal-prev { left: 10px; }
.modal-next { right: 370px; }

/* Rating Slider */
.rating-slider { width: 100%; }
.rating-slider input { width: 100%; height: 40px; -webkit-appearance: none; 
                       background: linear-gradient(90deg, #333 0%, #00d4ff 50%, #ffd700 75%, #ff6b6b 100%);
                       border-radius: 20px; outline: none; }
.rating-slider input::-webkit-slider-thumb { -webkit-appearance: none; width: 30px; height: 30px;
                                              background: #fff; border-radius: 50%; cursor: pointer;
                                              box-shadow: 0 0 10px rgba(0,0,0,0.5); }
.rating-big { font-size: 80px; text-align: center; font-weight: bold;
              background: linear-gradient(90deg, #00d4ff, #ff6b6b); 
              -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.rating-label { text-align: center; color: #888; font-size: 14px; }

/* Quick rate buttons */
.quick-rate { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.quick-rate button { padding: 15px 10px; font-size: 16px; font-weight: bold; }

/* Keyboard hints */
.keyboard-hints { background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; }
.keyboard-hints h4 { margin-bottom: 10px; color: #00d4ff; }
.key { display: inline-block; background: rgba(255,255,255,0.1); padding: 4px 10px;
       border-radius: 5px; margin: 2px; font-family: monospace; }
</style>
</head>
<body>

<div class="header">
    <h1>🎨 3D Image Gallery Viewer</h1>
    <div class="stats" id="stats"></div>
</div>

<div class="controls">
    <button class="btn-primary" onclick="scan()">🔄 Scan Images</button>
    <select id="sortBy" onchange="loadImages()">
        <option value="date">Sort: Newest</option>
        <option value="rating">Sort: Rating</option>
        <option value="name">Sort: Name</option>
    </select>
    <select id="filterBy" onchange="loadImages()">
        <option value="">Show: All</option>
        <option value="unrated">Show: Unrated</option>
        <option value="rated">Show: Rated</option>
        <option value="excellent">Show: Excellent (10+)</option>
    </select>
    <button class="btn-gold" onclick="filterBy.value='excellent';loadImages()">⭐ View Excellent</button>
    <span style="margin-left:auto; color:#888;">Click image or press SPACE to open viewer</span>
</div>

<div class="gallery-3d">
    <div class="gallery-grid" id="gallery"></div>
</div>

<!-- Modal Viewer -->
<div class="modal" id="modal">
    <span class="modal-close" onclick="closeModal()">✕</span>
    <span class="modal-nav modal-prev" onclick="prevImage()">❮</span>
    <span class="modal-nav modal-next" onclick="nextImage()">❯</span>
    
    <div class="modal-content">
        <div class="modal-image-container">
            <img class="modal-image" id="modalImage" src="">
        </div>
        <div class="modal-sidebar">
            <div class="rating-big" id="modalRating">0</div>
            <div class="rating-label" id="ratingLabel">Unrated</div>
            
            <div class="rating-slider">
                <input type="range" min="0" max="15" value="0" id="ratingSlider" 
                       oninput="updateRatingPreview(this.value)">
            </div>
            
            <button class="btn-primary" onclick="saveRating()" style="padding:15px;font-size:18px;">
                💾 Save Rating
            </button>
            
            <div class="quick-rate">
                <button class="btn-secondary" onclick="quickRate(0)">0</button>
                <button class="btn-secondary" onclick="quickRate(5)">5</button>
                <button class="btn-secondary" onclick="quickRate(8)">8</button>
                <button class="btn-secondary" onclick="quickRate(10)">10</button>
                <button class="btn-secondary" onclick="quickRate(11)">11</button>
                <button class="btn-secondary" onclick="quickRate(12)">12</button>
                <button class="btn-secondary" onclick="quickRate(13)">13</button>
                <button class="btn-gold" onclick="quickRate(15)">15⭐</button>
            </div>
            
            <div class="keyboard-hints">
                <h4>⌨️ Keyboard Shortcuts</h4>
                <div><span class="key">←</span> <span class="key">→</span> Navigate</div>
                <div><span class="key">0-9</span> Quick rate</div>
                <div><span class="key">+</span> Rate 10-15</div>
                <div><span class="key">Enter</span> Save & Next</div>
                <div><span class="key">Esc</span> Close</div>
            </div>
            
            <div id="imageInfo" style="color:#888;font-size:12px;"></div>
        </div>
    </div>
</div>

<script>
let images = [];
let currentIndex = 0;
let currentImage = null;

async function api(path, method='GET', body=null) {
    const opts = {method, headers:{'Content-Type':'application/json'}};
    if(body) opts.body = JSON.stringify(body);
    return (await fetch(path, opts)).json();
}

async function loadStats() {
    const s = await api('/api/stats');
    document.getElementById('stats').innerHTML = `
        <div class="stat"><div class="stat-value">${s.total}</div><div class="stat-label">Total</div></div>
        <div class="stat"><div class="stat-value">${s.rated}</div><div class="stat-label">Rated</div></div>
        <div class="stat"><div class="stat-value">${s.unrated}</div><div class="stat-label">Unrated</div></div>
        <div class="stat"><div class="stat-value">${s.excellent}</div><div class="stat-label">Excellent</div></div>
        <div class="stat"><div class="stat-value">${s.gold}</div><div class="stat-label">Gold ⭐</div></div>
        <div class="stat"><div class="stat-value">${s.avg}</div><div class="stat-label">Avg</div></div>
    `;
}

async function loadImages() {
    const sort = document.getElementById('sortBy').value;
    const filter = document.getElementById('filterBy').value;
    images = await api(`/api/images?sort=${sort}&filter=${filter}`);
    renderGallery();
}

function renderGallery() {
    document.getElementById('gallery').innerHTML = images.map((img, i) => `
        <div class="card-3d ${img.rating>=15?'gold':img.rating>=10?'excellent':''}" 
             onclick="openModal(${i})" data-index="${i}">
            <img src="/image/${img.filename}" loading="lazy">
            <div class="card-info">
                <div class="card-name">${img.filename}</div>
                <div class="rating-display">
                    <span class="rating-value">${img.rating || 0}</span>
                    <div class="rating-bar"><div class="rating-fill" style="width:${(img.rating||0)/15*100}%"></div></div>
                </div>
            </div>
        </div>
    `).join('');
}

function openModal(index) {
    currentIndex = index;
    currentImage = images[index];
    document.getElementById('modal').classList.add('active');
    document.getElementById('modalImage').src = `/image/${currentImage.filename}`;
    document.getElementById('ratingSlider').value = currentImage.rating || 0;
    updateRatingPreview(currentImage.rating || 0);
    document.getElementById('imageInfo').innerHTML = `
        <strong>${currentImage.filename}</strong><br>
        Image ${index + 1} of ${images.length}
    `;
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

function prevImage() {
    if (currentIndex > 0) openModal(currentIndex - 1);
}

function nextImage() {
    if (currentIndex < images.length - 1) openModal(currentIndex + 1);
}

function updateRatingPreview(val) {
    document.getElementById('modalRating').textContent = val;
    const labels = {
        0: 'Unrated', 1: 'Poor', 2: 'Poor', 3: 'Poor', 4: 'Below Average', 5: 'Average',
        6: 'Above Average', 7: 'Good', 8: 'Good', 9: 'Very Good', 10: 'Excellent',
        11: 'Excellent', 12: 'Outstanding', 13: 'Near Perfect', 14: 'Almost Perfect', 15: 'PERFECT ⭐'
    };
    document.getElementById('ratingLabel').textContent = labels[parseInt(val)] || '';
}

async function saveRating() {
    const rating = parseFloat(document.getElementById('ratingSlider').value);
    await api('/api/rate', 'POST', {id: currentImage.id, rating});
    currentImage.rating = rating;
    loadStats();
    loadImages();
    nextImage();
}

async function quickRate(val) {
    document.getElementById('ratingSlider').value = val;
    updateRatingPreview(val);
    await saveRating();
}

async function scan() {
    const r = await api('/api/scan');
    alert(`Scanned! Found ${r.new} new images. Total: ${r.total}`);
    loadStats();
    loadImages();
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (!document.getElementById('modal').classList.contains('active')) {
        if (e.code === 'Space' && images.length) { e.preventDefault(); openModal(0); }
        return;
    }
    
    switch(e.key) {
        case 'ArrowLeft': prevImage(); break;
        case 'ArrowRight': nextImage(); break;
        case 'Escape': closeModal(); break;
        case 'Enter': saveRating(); break;
        case '0': case '1': case '2': case '3': case '4': 
        case '5': case '6': case '7': case '8': case '9':
            document.getElementById('ratingSlider').value = e.key;
            updateRatingPreview(e.key);
            break;
        case '+': case '=':
            const cur = parseInt(document.getElementById('ratingSlider').value);
            if (cur < 15) {
                document.getElementById('ratingSlider').value = cur + 1;
                updateRatingPreview(cur + 1);
            }
            break;
        case '-':
            const cur2 = parseInt(document.getElementById('ratingSlider').value);
            if (cur2 > 0) {
                document.getElementById('ratingSlider').value = cur2 - 1;
                updateRatingPreview(cur2 - 1);
            }
            break;
    }
});

loadStats();
loadImages();
</script>
</body></html>'''


class Handler(BaseHTTPRequestHandler):
    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
    def do_GET(self):
        path = self.path.split('?')[0]
        query = dict(p.split('=') for p in self.path.split('?')[1].split('&')) if '?' in self.path else {}
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif path == '/api/stats':
            self._json(db.get_stats())
        elif path == '/api/images':
            self._json(db.get_all(query.get('sort', 'date'), query.get('filter')))
        elif path == '/api/scan':
            self._json(db.scan_all())
        elif path.startswith('/image/'):
            fn = path.replace('/image/', '')
            fp = OUTPUT_DIR / fn
            if fp.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Cache-Control', 'max-age=3600')
                self.end_headers()
                self.wfile.write(fp.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self._json({'error': 'not found'})
            
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length else {}
        
        if self.path == '/api/rate':
            self._json(db.rate(data['id'], data['rating']))
        else:
            self._json({'error': 'not found'})
            
    def log_message(self, *args): pass


def main():
    print("="*60)
    print("  🎨 3D IMAGE GALLERY VIEWER")
    print("="*60)
    
    print("\n📷 Scanning images...")
    result = db.scan_all()
    print(f"   Found {result['total']} images ({result['new']} new)")
    
    stats = db.get_stats()
    print(f"\n📊 Status:")
    print(f"   Total: {stats['total']} | Rated: {stats['rated']} | Unrated: {stats['unrated']}")
    print(f"   Excellent: {stats['excellent']} | Gold: {stats['gold']}")
    
    print(f"\n🌐 Open: http://127.0.0.1:8192")
    print(f"\n⌨️  SHORTCUTS:")
    print(f"   SPACE     - Open first image")
    print(f"   ← →       - Navigate images")
    print(f"   0-9       - Quick rate")
    print(f"   + -       - Adjust rating")
    print(f"   ENTER     - Save & next")
    print(f"   ESC       - Close viewer")
    
    print(f"\n✅ Gallery ready!")
    
    server = HTTPServer(('0.0.0.0', 8192), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
