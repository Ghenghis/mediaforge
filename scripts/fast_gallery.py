"""
FAST IMAGE RATING GALLERY
- Large images for detail viewing
- Mouse wheel zoom
- Arrow key navigation
- Streamlined for 200+ images
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
        
    def get_all(self):
        return [dict(r) for r in self.conn.execute(
            'SELECT id, filename, rating FROM images ORDER BY created_at DESC').fetchall()]
        
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
        return {'total': t, 'rated': r, 'unrated': t-r, 'excellent': e}

db = DB()

HTML = '''<!DOCTYPE html>
<html><head><title>Fast Image Rater</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#111;color:#fff;font-family:Arial;overflow:hidden;height:100vh}
.top{position:fixed;top:0;left:0;right:0;height:50px;background:#222;display:flex;align-items:center;padding:0 20px;gap:20px;z-index:100}
.stat{font-size:14px}
.stat b{color:#0af;font-size:18px}
.progress{flex:1;height:8px;background:#333;border-radius:4px}
.progress-bar{height:100%;background:linear-gradient(90deg,#0af,#f66);border-radius:4px;transition:width 0.3s}

.main{position:fixed;top:50px;bottom:80px;left:0;right:0;display:flex;align-items:center;justify-content:center;background:#000}
.img-container{position:relative;width:100%;height:100%;overflow:hidden;cursor:grab}
.img-container:active{cursor:grabbing}
#mainImg{position:absolute;max-width:none;max-height:none;transition:transform 0.1s ease-out}

.nav{position:fixed;top:50%;transform:translateY(-50%);font-size:60px;color:#fff;cursor:pointer;opacity:0.3;z-index:50;padding:20px;user-select:none}
.nav:hover{opacity:1}
.prev{left:10px}
.next{right:10px}

.bottom{position:fixed;bottom:0;left:0;right:0;height:80px;background:#222;display:flex;align-items:center;padding:0 20px;gap:15px}
.rating-btns{display:flex;gap:5px}
.rating-btns button{width:45px;height:45px;border:none;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer;transition:transform 0.1s}
.rating-btns button:hover{transform:scale(1.1)}
.r0{background:#444;color:#fff}
.r5{background:#666;color:#fff}
.r8{background:#080;color:#fff}
.r10{background:#0a0;color:#fff}
.r12{background:#0c0;color:#000}
.r13{background:#fd0;color:#000}
.r15{background:#f60;color:#fff}
.current-rating{font-size:48px;font-weight:bold;color:#0af;min-width:80px;text-align:center}
.img-info{flex:1;text-align:right;color:#888;font-size:12px}
.zoom-info{color:#666;font-size:11px}

.help{position:fixed;top:60px;right:10px;background:#333;padding:10px 15px;border-radius:8px;font-size:11px;color:#888;z-index:50}
.help b{color:#0af}
</style>
</head>
<body>

<div class="top">
    <span class="stat">Total: <b id="total">0</b></span>
    <span class="stat">Rated: <b id="rated">0</b></span>
    <span class="stat">Left: <b id="unrated">0</b></span>
    <span class="stat">10+: <b id="excellent">0</b></span>
    <div class="progress"><div class="progress-bar" id="progressBar"></div></div>
</div>

<div class="main">
    <div class="img-container" id="imgContainer">
        <img id="mainImg" src="" draggable="false">
    </div>
</div>

<div class="nav prev" onclick="prev()">&lt;</div>
<div class="nav next" onclick="next()">&gt;</div>

<div class="help">
    <b>Mouse Wheel</b> = Zoom | <b>Drag</b> = Pan | <b>Arrow Keys</b> = Navigate<br>
    <b>0-9</b> = Rate | <b>Space</b> = Skip | <b>R</b> = Reset Zoom
</div>

<div class="bottom">
    <div class="rating-btns">
        <button class="r0" onclick="rate(0)">0</button>
        <button class="r0" onclick="rate(1)">1</button>
        <button class="r0" onclick="rate(2)">2</button>
        <button class="r0" onclick="rate(3)">3</button>
        <button class="r0" onclick="rate(4)">4</button>
        <button class="r5" onclick="rate(5)">5</button>
        <button class="r5" onclick="rate(6)">6</button>
        <button class="r5" onclick="rate(7)">7</button>
        <button class="r8" onclick="rate(8)">8</button>
        <button class="r8" onclick="rate(9)">9</button>
        <button class="r10" onclick="rate(10)">10</button>
        <button class="r10" onclick="rate(11)">11</button>
        <button class="r12" onclick="rate(12)">12</button>
        <button class="r13" onclick="rate(13)">13</button>
        <button class="r13" onclick="rate(14)">14</button>
        <button class="r15" onclick="rate(15)">15</button>
    </div>
    <div class="current-rating" id="currentRating">-</div>
    <div class="img-info">
        <div id="imgName">-</div>
        <div id="imgNum">-</div>
        <div class="zoom-info" id="zoomInfo">Zoom: 100%</div>
    </div>
</div>

<script>
let images = [];
let idx = 0;
let zoom = 1;
let panX = 0, panY = 0;
let isDragging = false;
let dragStartX, dragStartY, startPanX, startPanY;

const img = document.getElementById('mainImg');
const container = document.getElementById('imgContainer');

async function load() {
    images = await (await fetch('/api/images')).json();
    updateStats();
    show(0);
}

async function updateStats() {
    const s = await (await fetch('/api/stats')).json();
    document.getElementById('total').textContent = s.total;
    document.getElementById('rated').textContent = s.rated;
    document.getElementById('unrated').textContent = s.unrated;
    document.getElementById('excellent').textContent = s.excellent;
    document.getElementById('progressBar').style.width = (s.rated/s.total*100)+'%';
}

function show(i) {
    if (i < 0 || i >= images.length) return;
    idx = i;
    const item = images[idx];
    img.src = '/image/' + item.filename;
    document.getElementById('currentRating').textContent = item.rating || '-';
    document.getElementById('imgName').textContent = item.filename;
    document.getElementById('imgNum').textContent = `Image ${idx+1} of ${images.length}`;
    resetZoom();
}

function prev() { show(idx - 1); }
function next() { show(idx + 1); }

async function rate(val) {
    const item = images[idx];
    await fetch('/api/rate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: item.id, rating: val})
    });
    item.rating = val;
    document.getElementById('currentRating').textContent = val;
    updateStats();
    next();
}

// Zoom with mouse wheel
container.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = container.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(0.5, Math.min(10, zoom * delta));
    
    // Zoom toward mouse position
    const scale = newZoom / zoom;
    panX = mouseX - (mouseX - panX) * scale;
    panY = mouseY - (mouseY - panY) * scale;
    zoom = newZoom;
    
    updateTransform();
}, {passive: false});

// Pan with drag
container.addEventListener('mousedown', (e) => {
    isDragging = true;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    startPanX = panX;
    startPanY = panY;
});

document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    panX = startPanX + (e.clientX - dragStartX);
    panY = startPanY + (e.clientY - dragStartY);
    updateTransform();
});

document.addEventListener('mouseup', () => isDragging = false);

function updateTransform() {
    const rect = container.getBoundingClientRect();
    const imgW = img.naturalWidth * zoom;
    const imgH = img.naturalHeight * zoom;
    
    // Center image
    const centerX = (rect.width - imgW) / 2 + panX;
    const centerY = (rect.height - imgH) / 2 + panY;
    
    img.style.transform = `translate(${centerX}px, ${centerY}px) scale(${zoom})`;
    img.style.transformOrigin = 'top left';
    document.getElementById('zoomInfo').textContent = `Zoom: ${Math.round(zoom*100)}%`;
}

function resetZoom() {
    zoom = 1;
    panX = 0;
    panY = 0;
    img.onload = () => {
        const rect = container.getBoundingClientRect();
        const imgW = img.naturalWidth;
        const imgH = img.naturalHeight;
        
        // Fit to container
        const scaleW = rect.width / imgW;
        const scaleH = rect.height / imgH;
        zoom = Math.min(scaleW, scaleH, 1) * 0.95;
        
        updateTransform();
    };
    if (img.complete) img.onload();
}

// Keyboard
document.addEventListener('keydown', (e) => {
    switch(e.key) {
        case 'ArrowLeft': prev(); break;
        case 'ArrowRight': case ' ': e.preventDefault(); next(); break;
        case 'ArrowUp': zoom = Math.min(10, zoom * 1.2); updateTransform(); break;
        case 'ArrowDown': zoom = Math.max(0.5, zoom / 1.2); updateTransform(); break;
        case 'r': case 'R': resetZoom(); break;
        case '0': case '1': case '2': case '3': case '4':
        case '5': case '6': case '7': case '8': case '9':
            rate(parseInt(e.key)); break;
        case '+': case '=': rate(Math.min(15, (images[idx].rating||0)+1)); break;
        case '-': rate(Math.max(0, (images[idx].rating||0)-1)); break;
    }
});

// Double click to zoom
container.addEventListener('dblclick', (e) => {
    if (zoom < 2) {
        const rect = container.getBoundingClientRect();
        panX = rect.width/2 - e.clientX + rect.left;
        panY = rect.height/2 - e.clientY + rect.top;
        zoom = 3;
    } else {
        resetZoom();
    }
    updateTransform();
});

window.addEventListener('resize', () => updateTransform());
load();
</script>
</body></html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif path == '/api/images':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(db.get_all()).encode())
        elif path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(db.stats()).encode())
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
    print("  FAST IMAGE RATER")
    print("="*50)
    r = db.scan()
    s = db.stats()
    print(f"\nImages: {s['total']} | Rated: {s['rated']} | Left: {s['unrated']}")
    print(f"\nOpen: http://127.0.0.1:8193")
    print(f"\nControls:")
    print(f"  Mouse Wheel  = Zoom in/out")
    print(f"  Drag         = Pan image")
    print(f"  Double-click = Quick zoom 3x")
    print(f"  Arrow Left/Right = Navigate")
    print(f"  Arrow Up/Down = Zoom")
    print(f"  0-9          = Rate image")
    print(f"  Space        = Skip to next")
    print(f"  R            = Reset zoom")
    HTTPServer(('0.0.0.0', 8193), Handler).serve_forever()
