"""
IMAGE RATING STUDIO
- Grid of thumbnails
- Click to open large view
- Simple scroll zoom
- Easy rating buttons
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\master_learning.db")

class DB:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('''CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY, filename TEXT UNIQUE, rating REAL DEFAULT 0,
            is_gold_standard INTEGER DEFAULT 0, created_at TEXT, rated_at TEXT
        )''')
        self.conn.commit()
        
    def scan(self):
        imgs = list(OUTPUT_DIR.glob("*.png"))
        new = 0
        for img in imgs:
            if not self.conn.execute('SELECT 1 FROM images WHERE filename=?', (img.name,)).fetchone():
                self.conn.execute('INSERT INTO images (id, filename, created_at) VALUES (?,?,?)',
                    (f"img_{hash(img.name)%10**8}", img.name, datetime.now().isoformat()))
                new += 1
        self.conn.commit()
        return {'total': len(imgs), 'new': new}
        
    def get_all(self, show='all'):
        sql = 'SELECT id, filename, rating FROM images'
        if show == 'unrated': sql += ' WHERE rating = 0 OR rating IS NULL'
        elif show == 'rated': sql += ' WHERE rating > 0'
        elif show == 'excellent': sql += ' WHERE rating >= 10'
        sql += ' ORDER BY created_at DESC'
        return [dict(r) for r in self.conn.execute(sql).fetchall()]
        
    def rate(self, img_id, rating):
        rating = max(0, min(15, float(rating)))
        self.conn.execute('UPDATE images SET rating=?, rated_at=?, is_gold_standard=? WHERE id=?',
            (rating, datetime.now().isoformat(), 1 if rating >= 15 else 0, img_id))
        self.conn.commit()
        return {'id': img_id, 'rating': rating}
        
    def stats(self):
        t = self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]
        r = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
        e = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 10').fetchone()[0]
        g = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 15').fetchone()[0]
        return {'total': t, 'rated': r, 'unrated': t-r, 'excellent': e, 'gold': g}

db = DB()

HTML = '''<!DOCTYPE html>
<html>
<head>
<title>Image Rating Studio</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #1a1a1a; color: #fff; font-family: Arial, sans-serif; }

/* Top Bar */
.topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 60px;
    background: #222; display: flex; align-items: center;
    padding: 0 20px; gap: 30px; z-index: 100;
    border-bottom: 1px solid #333;
}
.logo { font-size: 20px; font-weight: bold; color: #4af; }
.stats { display: flex; gap: 25px; }
.stat { text-align: center; }
.stat-num { font-size: 22px; font-weight: bold; color: #4af; }
.stat-label { font-size: 10px; color: #888; }
.tools { display: flex; gap: 10px; margin-left: auto; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-blue { background: #4af; color: #000; }
.btn-gray { background: #444; color: #fff; }
.btn:hover { opacity: 0.8; }
select { padding: 8px; background: #333; color: #fff; border: 1px solid #555; border-radius: 6px; }

/* Grid */
.grid-container { padding: 80px 20px 20px; }
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 15px;
}
.thumb {
    background: #2a2a2a; border-radius: 8px; overflow: hidden;
    cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
    border: 3px solid transparent;
}
.thumb:hover { transform: scale(1.03); box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
.thumb.rated { border-color: #4af; }
.thumb.excellent { border-color: #fa0; }
.thumb.gold { border-color: #f44; box-shadow: 0 0 20px rgba(255,68,68,0.4); }
.thumb img { width: 100%; height: 150px; object-fit: cover; display: block; }
.thumb-info { padding: 8px; display: flex; justify-content: space-between; align-items: center; }
.thumb-rating { font-size: 20px; font-weight: bold; color: #4af; }
.thumb-name { font-size: 10px; color: #666; max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Viewer Modal */
.viewer {
    display: none; position: fixed; inset: 0; z-index: 200;
    background: rgba(0,0,0,0.95);
}
.viewer.open { display: flex; }
.viewer-main { flex: 1; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.viewer-img-wrap {
    max-width: 80%; max-height: 90vh; position: relative;
    overflow: auto; cursor: zoom-in;
}
.viewer-img-wrap.zoomed { cursor: zoom-out; max-width: none; max-height: none; }
.viewer-img-wrap img { display: block; max-width: 100%; max-height: 90vh; }
.viewer-img-wrap.zoomed img { max-width: none; max-height: none; }

/* Viewer Sidebar */
.viewer-side {
    width: 280px; background: #222; padding: 20px;
    display: flex; flex-direction: column; gap: 15px;
}
.viewer-close { position: absolute; top: 15px; right: 300px; font-size: 30px; cursor: pointer; color: #888; z-index: 210; }
.viewer-close:hover { color: #fff; }
.viewer-nav { position: absolute; top: 50%; transform: translateY(-50%); font-size: 50px; cursor: pointer; color: #555; padding: 20px; z-index: 210; }
.viewer-nav:hover { color: #fff; }
.viewer-prev { left: 10px; }
.viewer-next { right: 300px; }

/* Rating Panel */
.rating-panel h3 { color: #4af; margin-bottom: 10px; }
.rating-current { font-size: 60px; font-weight: bold; text-align: center; color: #4af; }
.rating-label { text-align: center; color: #888; margin-bottom: 15px; }
.rating-buttons { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.rate-btn {
    padding: 12px 8px; border: none; border-radius: 6px;
    font-size: 16px; font-weight: bold; cursor: pointer;
    transition: transform 0.1s;
}
.rate-btn:hover { transform: scale(1.1); }
.rate-btn.low { background: #444; color: #fff; }
.rate-btn.mid { background: #666; color: #fff; }
.rate-btn.good { background: #080; color: #fff; }
.rate-btn.great { background: #0a0; color: #fff; }
.rate-btn.excellent { background: #fa0; color: #000; }
.rate-btn.perfect { background: #f44; color: #fff; }

.save-next { padding: 15px; background: #4af; color: #000; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
.save-next:hover { background: #5bf; }

.img-details { font-size: 11px; color: #666; }
.img-details div { margin: 5px 0; }

.shortcuts { background: #333; padding: 12px; border-radius: 8px; font-size: 11px; color: #888; }
.shortcuts b { color: #4af; }
</style>
</head>
<body>

<!-- Top Bar -->
<div class="topbar">
    <div class="logo">Image Rating Studio</div>
    <div class="stats">
        <div class="stat"><div class="stat-num" id="sTotal">0</div><div class="stat-label">TOTAL</div></div>
        <div class="stat"><div class="stat-num" id="sRated">0</div><div class="stat-label">RATED</div></div>
        <div class="stat"><div class="stat-num" id="sLeft">0</div><div class="stat-label">LEFT</div></div>
        <div class="stat"><div class="stat-num" id="sExcellent">0</div><div class="stat-label">10+</div></div>
        <div class="stat"><div class="stat-num" id="sGold">0</div><div class="stat-label">GOLD</div></div>
    </div>
    <div class="tools">
        <select id="showFilter" onchange="loadImages()">
            <option value="all">Show All</option>
            <option value="unrated">Unrated Only</option>
            <option value="rated">Rated Only</option>
            <option value="excellent">Excellent (10+)</option>
        </select>
        <button class="btn btn-blue" onclick="scan()">Scan New</button>
        <button class="btn btn-gray" onclick="openViewer(0)">Start Rating</button>
    </div>
</div>

<!-- Grid -->
<div class="grid-container">
    <div class="grid" id="grid"></div>
</div>

<!-- Viewer -->
<div class="viewer" id="viewer">
    <span class="viewer-close" onclick="closeViewer()">X</span>
    <span class="viewer-nav viewer-prev" onclick="prevImg()">&#10094;</span>
    <span class="viewer-nav viewer-next" onclick="nextImg()">&#10095;</span>
    
    <div class="viewer-main">
        <div class="viewer-img-wrap" id="imgWrap" onclick="toggleZoom()">
            <img id="viewerImg" src="">
        </div>
    </div>
    
    <div class="viewer-side">
        <div class="rating-panel">
            <h3>RATING</h3>
            <div class="rating-current" id="ratingDisplay">-</div>
            <div class="rating-label" id="ratingLabel">Click to rate</div>
            <div class="rating-buttons">
                <button class="rate-btn low" onclick="setRating(0)">0</button>
                <button class="rate-btn low" onclick="setRating(1)">1</button>
                <button class="rate-btn low" onclick="setRating(2)">2</button>
                <button class="rate-btn low" onclick="setRating(3)">3</button>
                <button class="rate-btn low" onclick="setRating(4)">4</button>
                <button class="rate-btn mid" onclick="setRating(5)">5</button>
                <button class="rate-btn mid" onclick="setRating(6)">6</button>
                <button class="rate-btn mid" onclick="setRating(7)">7</button>
                <button class="rate-btn good" onclick="setRating(8)">8</button>
                <button class="rate-btn good" onclick="setRating(9)">9</button>
                <button class="rate-btn great" onclick="setRating(10)">10</button>
                <button class="rate-btn great" onclick="setRating(11)">11</button>
                <button class="rate-btn excellent" onclick="setRating(12)">12</button>
                <button class="rate-btn excellent" onclick="setRating(13)">13</button>
                <button class="rate-btn excellent" onclick="setRating(14)">14</button>
                <button class="rate-btn perfect" onclick="setRating(15)">15</button>
            </div>
        </div>
        
        <button class="save-next" onclick="saveAndNext()">SAVE & NEXT →</button>
        
        <div class="img-details">
            <div><b>File:</b> <span id="detailName">-</span></div>
            <div><b>Position:</b> <span id="detailPos">-</span></div>
        </div>
        
        <div class="shortcuts">
            <b>Arrow Keys</b> = Navigate<br>
            <b>0-9</b> = Quick Rate<br>
            <b>Click Image</b> = Zoom In/Out<br>
            <b>Enter</b> = Save & Next<br>
            <b>Esc</b> = Close
        </div>
    </div>
</div>

<script>
let images = [];
let currentIdx = 0;
let pendingRating = null;

// Load stats
async function loadStats() {
    const s = await (await fetch('/api/stats')).json();
    document.getElementById('sTotal').textContent = s.total;
    document.getElementById('sRated').textContent = s.rated;
    document.getElementById('sLeft').textContent = s.unrated;
    document.getElementById('sExcellent').textContent = s.excellent;
    document.getElementById('sGold').textContent = s.gold;
}

// Load images
async function loadImages() {
    const filter = document.getElementById('showFilter').value;
    images = await (await fetch('/api/images?show=' + filter)).json();
    renderGrid();
}

// Render grid
function renderGrid() {
    document.getElementById('grid').innerHTML = images.map((img, i) => {
        let cls = 'thumb';
        if (img.rating >= 15) cls += ' gold';
        else if (img.rating >= 10) cls += ' excellent';
        else if (img.rating > 0) cls += ' rated';
        return `
            <div class="${cls}" onclick="openViewer(${i})">
                <img src="/image/${img.filename}" loading="lazy">
                <div class="thumb-info">
                    <span class="thumb-rating">${img.rating || '-'}</span>
                    <span class="thumb-name">${img.filename}</span>
                </div>
            </div>
        `;
    }).join('');
}

// Open viewer
function openViewer(idx) {
    currentIdx = idx;
    showImage();
    document.getElementById('viewer').classList.add('open');
}

// Close viewer
function closeViewer() {
    document.getElementById('viewer').classList.remove('open');
    document.getElementById('imgWrap').classList.remove('zoomed');
}

// Show current image
function showImage() {
    const img = images[currentIdx];
    document.getElementById('viewerImg').src = '/image/' + img.filename;
    document.getElementById('ratingDisplay').textContent = img.rating || '-';
    document.getElementById('detailName').textContent = img.filename;
    document.getElementById('detailPos').textContent = (currentIdx + 1) + ' of ' + images.length;
    pendingRating = img.rating || 0;
    updateLabel(pendingRating);
    document.getElementById('imgWrap').classList.remove('zoomed');
}

// Navigate
function prevImg() { if (currentIdx > 0) { currentIdx--; showImage(); } }
function nextImg() { if (currentIdx < images.length - 1) { currentIdx++; showImage(); } }

// Toggle zoom
function toggleZoom() {
    document.getElementById('imgWrap').classList.toggle('zoomed');
}

// Set rating
function setRating(val) {
    pendingRating = val;
    document.getElementById('ratingDisplay').textContent = val;
    updateLabel(val);
}

// Update label
function updateLabel(val) {
    const labels = ['Skip', 'Poor', 'Poor', 'Bad', 'Bad', 'Average', 'OK', 'OK', 'Good', 'Good', 
                    'Excellent', 'Excellent', 'Great', 'Amazing', 'Near Perfect', 'PERFECT!'];
    document.getElementById('ratingLabel').textContent = labels[val] || '';
}

// Save and next
async function saveAndNext() {
    const img = images[currentIdx];
    await fetch('/api/rate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: img.id, rating: pendingRating})
    });
    img.rating = pendingRating;
    loadStats();
    renderGrid();
    nextImg();
}

// Scan
async function scan() {
    const r = await (await fetch('/api/scan')).json();
    alert('Found ' + r.new + ' new images!');
    loadStats();
    loadImages();
}

// Keyboard
document.addEventListener('keydown', (e) => {
    const viewer = document.getElementById('viewer');
    if (!viewer.classList.contains('open')) return;
    
    switch(e.key) {
        case 'ArrowLeft': prevImg(); break;
        case 'ArrowRight': nextImg(); break;
        case 'Escape': closeViewer(); break;
        case 'Enter': saveAndNext(); break;
        case '0': case '1': case '2': case '3': case '4':
        case '5': case '6': case '7': case '8': case '9':
            setRating(parseInt(e.key)); break;
    }
});

// Init
loadStats();
loadImages();
</script>
</body>
</html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        query = {}
        if '?' in self.path:
            query = dict(p.split('=') for p in self.path.split('?')[1].split('&') if '=' in p)
            
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
        elif path == '/api/images':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(db.get_all(query.get('show', 'all'))).encode())
        elif path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(db.stats()).encode())
        elif path == '/api/scan':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(db.scan()).encode())
        elif path.startswith('/image/'):
            fp = OUTPUT_DIR / path[7:]
            if fp.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                self.wfile.write(fp.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
                
    def do_POST(self):
        if self.path == '/api/rate':
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(db.rate(data['id'], data['rating'])).encode())
            
    def log_message(self, *args): pass


if __name__ == "__main__":
    print("="*50)
    print("  IMAGE RATING STUDIO")
    print("="*50)
    db.scan()
    s = db.stats()
    print(f"\nImages: {s['total']} | Rated: {s['rated']} | Left: {s['unrated']}")
    print(f"\nOpen: http://127.0.0.1:8194")
    print("\nHow to use:")
    print("  1. Click any thumbnail to open")
    print("  2. Click image to zoom in/out")
    print("  3. Click rating button (0-15)")
    print("  4. Click SAVE & NEXT")
    print("  5. Or use keyboard: 0-9, Enter, Arrows")
    HTTPServer(('0.0.0.0', 8194), Handler).serve_forever()
