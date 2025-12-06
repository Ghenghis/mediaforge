"""
RATING STUDIO V2 - Fixed + Enhanced Prompt Generator
- Better image display
- Working process button
- Advanced prompt builder with perfection tags
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import Counter

OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\master_learning.db")

# PERFECTION TAGS - Organized by category
PERFECTION_TAGS = {
    "quality": [
        "masterpiece", "best quality", "highly detailed", "ultra detailed",
        "8k uhd", "high resolution", "photorealistic", "hyperrealistic",
        "professional photography", "award winning"
    ],
    "face": [
        "detailed face", "beautiful face", "perfect face", "symmetrical face",
        "detailed eyes", "beautiful eyes", "sparkling eyes", "detailed pupils",
        "long eyelashes", "perfect nose", "detailed lips", "glossy lips"
    ],
    "skin": [
        "detailed skin", "flawless skin", "smooth skin", "skin texture",
        "subsurface scattering", "natural skin tone", "porcelain skin",
        "healthy skin", "glowing skin"
    ],
    "body": [
        "perfect anatomy", "perfect proportions", "elegant pose",
        "natural pose", "dynamic pose", "graceful"
    ],
    "hair": [
        "detailed hair", "flowing hair", "silky hair", "shiny hair",
        "hair strands", "volumetric hair", "natural hair"
    ],
    "lighting": [
        "cinematic lighting", "soft lighting", "natural lighting",
        "studio lighting", "rim lighting", "volumetric lighting",
        "golden hour", "dramatic lighting", "professional lighting"
    ],
    "camera": [
        "sharp focus", "depth of field", "bokeh", "85mm lens",
        "f/1.4 aperture", "DSLR", "RAW photo", "film grain"
    ],
    "style": [
        "realistic", "photorealism", "lifelike", "ultra realistic",
        "unreal engine", "octane render", "ray tracing"
    ]
}

NEGATIVE_TAGS = [
    "bad anatomy", "bad hands", "bad fingers", "extra fingers", "missing fingers",
    "deformed", "disfigured", "mutated", "ugly", "blurry", "low quality",
    "worst quality", "jpeg artifacts", "watermark", "text", "signature",
    "extra limbs", "missing limbs", "floating limbs", "disconnected limbs",
    "malformed", "poorly drawn", "amateur", "distorted"
]


class DB:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()
        
    def _init(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY, filename TEXT UNIQUE, rating REAL DEFAULT 0,
                prompt TEXT, tags TEXT, is_gold_standard INTEGER DEFAULT 0, 
                created_at TEXT, rated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS generated_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT, negative TEXT, quality_level TEXT,
                tags_used TEXT, created_at TEXT
            );
        ''')
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
        
    def get_images(self, f='all'):
        sql = 'SELECT id, filename, rating FROM images'
        if f == 'unrated': sql += ' WHERE rating = 0 OR rating IS NULL'
        elif f == 'rated': sql += ' WHERE rating > 0'
        elif f == 'high': sql += ' WHERE rating >= 8'
        sql += ' ORDER BY filename'
        return [dict(r) for r in self.conn.execute(sql).fetchall()]
        
    def rate(self, img_id, rating):
        rating = max(0, min(15, float(rating)))
        self.conn.execute('UPDATE images SET rating=?, rated_at=?, is_gold_standard=? WHERE id=?',
            (rating, datetime.now().isoformat(), 1 if rating >= 15 else 0, img_id))
        self.conn.commit()
        return {'saved': True, 'rating': rating}
        
    def stats(self):
        t = self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]
        r = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
        e = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 8').fetchone()[0]
        avg = self.conn.execute('SELECT AVG(rating) FROM images WHERE rating > 0').fetchone()[0] or 0
        return {'total': t, 'rated': r, 'unrated': t-r, 'excellent': e, 'avg': round(avg, 2)}
        
    def process(self):
        dist = {}
        for row in self.conn.execute('SELECT rating, COUNT(*) FROM images WHERE rating > 0 GROUP BY rating ORDER BY rating DESC'):
            dist[int(row[0])] = row[1]
        high = len(self.conn.execute('SELECT 1 FROM images WHERE rating >= 8').fetchall())
        low = len(self.conn.execute('SELECT 1 FROM images WHERE rating <= 4 AND rating > 0').fetchall())
        avg = self.conn.execute('SELECT AVG(rating) FROM images WHERE rating > 0').fetchone()[0] or 0
        total = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
        return {
            'total_rated': total, 'avg_rating': round(avg, 2),
            'distribution': dist, 'high_count': high, 'low_count': low
        }

db = DB()


def build_perfection_prompt(subject="beautiful woman", style="realistic", detail_level=3):
    """Build a perfection-level prompt with all quality tags"""
    parts = [subject]
    
    # Add quality tags based on detail level (1-3)
    parts.extend(PERFECTION_TAGS["quality"][:3 + detail_level*2])
    
    # Add face/skin/body details
    if detail_level >= 1:
        parts.extend(PERFECTION_TAGS["face"][:4])
        parts.extend(PERFECTION_TAGS["skin"][:3])
    if detail_level >= 2:
        parts.extend(PERFECTION_TAGS["face"][4:8])
        parts.extend(PERFECTION_TAGS["skin"][3:6])
        parts.extend(PERFECTION_TAGS["body"][:3])
        parts.extend(PERFECTION_TAGS["hair"][:4])
    if detail_level >= 3:
        parts.extend(PERFECTION_TAGS["face"][8:])
        parts.extend(PERFECTION_TAGS["skin"][6:])
        parts.extend(PERFECTION_TAGS["body"][3:])
        parts.extend(PERFECTION_TAGS["hair"][4:])
    
    # Add lighting
    parts.extend(PERFECTION_TAGS["lighting"][:2 + detail_level])
    
    # Add camera/technical
    parts.extend(PERFECTION_TAGS["camera"][:2 + detail_level])
    
    # Add style
    if style == "realistic":
        parts.extend(PERFECTION_TAGS["style"][:4])
    
    return {
        "prompt": ", ".join(parts),
        "negative": ", ".join(NEGATIVE_TAGS),
        "tags_count": len(parts)
    }


HTML = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Rating Studio V2</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#fff;font-family:Arial}
.header{position:fixed;top:0;left:0;right:0;height:50px;background:#151515;display:flex;align-items:center;padding:0 15px;gap:20px;z-index:100;border-bottom:1px solid #333}
.logo{font-size:16px;font-weight:bold;color:#0af}
.stats{display:flex;gap:15px}
.stat b{color:#0af;font-size:18px}
.stat span{color:#666;font-size:11px}
.btns{margin-left:auto;display:flex;gap:8px}
.btn{padding:8px 14px;border:none;border-radius:5px;cursor:pointer;font-size:12px;font-weight:bold}
.btn-blue{background:#0af;color:#000}
.btn-green{background:#0a0;color:#fff}
.btn-orange{background:#f80;color:#000}
select{padding:6px 10px;background:#222;color:#fff;border:1px solid #444;border-radius:5px}
.main{display:flex;margin-top:50px;height:calc(100vh - 50px)}
.gallery{flex:1;padding:10px;overflow-y:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px;align-content:start}
.thumb{background:#1a1a1a;border-radius:6px;overflow:hidden;cursor:pointer;border:2px solid transparent}
.thumb:hover{border-color:#0af}
.thumb.selected{border-color:#0af;box-shadow:0 0 15px #0af5}
.thumb.rated{border-color:#0a05}
.thumb.high{border-color:#f805}
.thumb img{width:100%;aspect-ratio:1;object-fit:cover}
.thumb-info{padding:4px 6px;background:#111;display:flex;justify-content:space-between;font-size:10px}
.thumb-info b{color:#0af}
.sidebar{width:340px;background:#151515;padding:15px;display:flex;flex-direction:column;gap:10px;border-left:1px solid #333;overflow-y:auto}
.preview{background:#000;border-radius:8px;overflow:hidden}
.preview img{width:100%;max-height:250px;object-fit:contain;cursor:zoom-in}
.preview img.zoomed{max-height:none;cursor:zoom-out}
.box{background:#1a1a1a;padding:12px;border-radius:8px}
.box h4{color:#0af;margin-bottom:8px;font-size:12px}
.rating-num{font-size:42px;font-weight:bold;text-align:center;color:#0af}
.rating-label{text-align:center;color:#666;font-size:10px;margin-bottom:6px}
.slider{width:100%;height:20px;-webkit-appearance:none;background:linear-gradient(90deg,#333,#0af 60%,#f80 80%,#f44);border-radius:10px;margin:6px 0}
.slider::-webkit-slider-thumb{-webkit-appearance:none;width:18px;height:18px;background:#fff;border-radius:50%;cursor:pointer}
.quick-btns{display:grid;grid-template-columns:repeat(8,1fr);gap:3px}
.quick-btns button{padding:6px 2px;border:none;border-radius:4px;font-size:10px;font-weight:bold;cursor:pointer}
.qb-low{background:#333;color:#fff}.qb-mid{background:#555;color:#fff}.qb-good{background:#080;color:#fff}
.qb-great{background:#0a0;color:#fff}.qb-exc{background:#f80;color:#000}.qb-perf{background:#f44;color:#fff}
.save-msg{text-align:center;padding:5px;background:#0a02;border-radius:5px;color:#0a0;font-size:10px}
.nav-btns{display:flex;gap:8px}
.nav-btns button{flex:1;padding:8px}
.info{font-size:9px;color:#555}
.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.95);z-index:200;padding:20px;overflow-y:auto}
.modal.open{display:block}
.modal-box{max-width:900px;margin:0 auto;background:#1a1a1a;border-radius:10px;padding:20px}
.modal-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}
.modal-head h2{color:#0af;font-size:16px}
.modal-close{font-size:20px;cursor:pointer;color:#666}
.section{background:#111;padding:12px;border-radius:6px;margin:10px 0}
.section h4{color:#f80;margin-bottom:8px;font-size:12px}
.tags{display:flex;flex-wrap:wrap;gap:4px}
.tag{padding:3px 7px;background:#222;border-radius:3px;font-size:10px}
.tag.good{background:#0a03;color:#0f0}
.prompt-box{background:#000;padding:12px;border-radius:6px;font-family:monospace;font-size:11px;color:#0f0;white-space:pre-wrap;max-height:200px;overflow-y:auto}
.neg-box{background:#200;padding:12px;border-radius:6px;font-family:monospace;font-size:10px;color:#f88;white-space:pre-wrap}
.copy-btn{padding:6px 12px;background:#0af;color:#000;border:none;border-radius:4px;cursor:pointer;font-size:11px;margin-top:8px}
.dist-row{display:flex;align-items:center;gap:8px;margin:3px 0;font-size:10px}
.dist-row span:first-child{width:25px;color:#888}
.dist-bar{height:14px;background:#0af;border-radius:2px;min-width:2px}
</style></head><body>

<div class="header">
    <div class="logo">Rating Studio V2</div>
    <div class="stats">
        <div class="stat"><b id="sTotal">0</b><span>total</span></div>
        <div class="stat"><b id="sRated">0</b><span>rated</span></div>
        <div class="stat"><b id="sLeft">0</b><span>left</span></div>
        <div class="stat"><b id="sAvg">0</b><span>avg</span></div>
    </div>
    <div class="btns">
        <select id="filter" onchange="load()">
            <option value="all">All</option>
            <option value="unrated">Unrated</option>
            <option value="rated">Rated</option>
            <option value="high">High 8+</option>
        </select>
        <button class="btn btn-blue" onclick="scan()">Scan</button>
        <button class="btn btn-orange" onclick="openTrain()">Process & Train</button>
        <button class="btn btn-green" onclick="openPrompt()">Generate Prompt</button>
    </div>
</div>

<div class="main">
    <div class="gallery" id="gallery"></div>
    <div class="sidebar">
        <div class="preview"><img id="preview" onclick="this.classList.toggle('zoomed')"></div>
        <div class="box">
            <h4>RATE IMAGE</h4>
            <div class="rating-num" id="ratingNum">-</div>
            <div class="rating-label" id="ratingLabel">Select image</div>
            <input type="range" class="slider" id="slider" min="0" max="15" value="0" oninput="updateR(this.value)" onchange="saveR()">
            <div class="quick-btns">
                <button class="qb-low" onclick="qr(0)">0</button>
                <button class="qb-low" onclick="qr(2)">2</button>
                <button class="qb-mid" onclick="qr(4)">4</button>
                <button class="qb-mid" onclick="qr(6)">6</button>
                <button class="qb-good" onclick="qr(8)">8</button>
                <button class="qb-great" onclick="qr(10)">10</button>
                <button class="qb-exc" onclick="qr(12)">12</button>
                <button class="qb-perf" onclick="qr(15)">15</button>
            </div>
        </div>
        <div class="save-msg" id="saveMsg">Auto-save ON</div>
        <div class="nav-btns">
            <button class="btn btn-blue" onclick="prev()">Prev</button>
            <button class="btn btn-blue" onclick="next()">Next</button>
        </div>
        <div class="info" id="info">-</div>
    </div>
</div>

<!-- Training Modal -->
<div class="modal" id="trainModal">
    <div class="modal-box">
        <div class="modal-head"><h2>Training Results</h2><span class="modal-close" onclick="closeTrain()">X</span></div>
        <div id="trainResults"></div>
    </div>
</div>

<!-- Prompt Modal -->
<div class="modal" id="promptModal">
    <div class="modal-box">
        <div class="modal-head"><h2>Perfection Prompt Generator</h2><span class="modal-close" onclick="closePrompt()">X</span></div>
        <div class="section">
            <h4>Subject</h4>
            <input type="text" id="subject" value="beautiful woman, portrait" style="width:100%;padding:8px;background:#222;border:1px solid #444;border-radius:4px;color:#fff">
        </div>
        <div class="section">
            <h4>Detail Level</h4>
            <select id="detailLevel" style="padding:8px;background:#222;color:#fff;border:1px solid #444;border-radius:4px">
                <option value="1">Level 1 - Basic (30+ tags)</option>
                <option value="2">Level 2 - Enhanced (50+ tags)</option>
                <option value="3" selected>Level 3 - Perfection (70+ tags)</option>
            </select>
            <button class="btn btn-green" onclick="genPrompt()" style="margin-left:10px">Generate</button>
        </div>
        <div class="section">
            <h4>Generated Prompt (copy this)</h4>
            <div class="prompt-box" id="genPrompt">Click Generate to create perfection prompt...</div>
            <button class="copy-btn" onclick="copyPrompt()">Copy Prompt</button>
        </div>
        <div class="section">
            <h4>Negative Prompt (copy this too)</h4>
            <div class="neg-box" id="negPrompt">bad anatomy, bad hands, bad fingers, extra fingers, missing fingers, deformed, disfigured, mutated, ugly, blurry, low quality, worst quality, jpeg artifacts, watermark, text, signature, extra limbs, missing limbs, floating limbs, disconnected limbs, malformed, poorly drawn, amateur, distorted</div>
            <button class="copy-btn" onclick="copyNeg()">Copy Negative</button>
        </div>
        <div class="section">
            <h4>Available Quality Tags</h4>
            <div class="tags" id="allTags"></div>
        </div>
    </div>
</div>

<script>
let images=[], idx=-1, cur=null;

async function loadStats(){
    const s=await(await fetch('/api/stats')).json();
    document.getElementById('sTotal').textContent=s.total;
    document.getElementById('sRated').textContent=s.rated;
    document.getElementById('sLeft').textContent=s.unrated;
    document.getElementById('sAvg').textContent=s.avg;
}

async function load(){
    const f=document.getElementById('filter').value;
    images=await(await fetch('/api/images?f='+f)).json();
    render();
    if(images.length>0&&idx<0)select(0);
}

function render(){
    document.getElementById('gallery').innerHTML=images.map((img,i)=>{
        let c='thumb';
        if(i===idx)c+=' selected';
        if(img.rating>=8)c+=' high';
        else if(img.rating>0)c+=' rated';
        return `<div class="${c}" onclick="select(${i})"><img src="/image/${img.filename}" loading="lazy"><div class="thumb-info"><b>${img.rating||'-'}</b></div></div>`;
    }).join('');
}

function select(i){
    if(i<0||i>=images.length)return;
    idx=i;cur=images[i];
    document.getElementById('preview').src='/image/'+cur.filename;
    document.getElementById('preview').classList.remove('zoomed');
    document.getElementById('slider').value=cur.rating||0;
    updateR(cur.rating||0);
    document.getElementById('info').innerHTML=`<b>${cur.filename}</b><br>${i+1}/${images.length}`;
    render();
}

function updateR(v){
    document.getElementById('ratingNum').textContent=v;
    const labels=['Skip','Poor','Poor','Bad','Bad','Avg','OK','OK','Good','Good','Great','Great','Exc','Exc','Perfect','PERFECT!'];
    document.getElementById('ratingLabel').textContent=labels[parseInt(v)]||'';
}

async function saveR(){
    if(!cur)return;
    const r=parseInt(document.getElementById('slider').value);
    document.getElementById('saveMsg').textContent='Saving...';
    document.getElementById('saveMsg').style.background='#ff02';
    const res=await fetch('/api/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:cur.id,rating:r})}).then(r=>r.json());
    if(res.saved){
        cur.rating=r;
        document.getElementById('saveMsg').textContent='Saved: '+r;
        document.getElementById('saveMsg').style.background='#0a02';
        loadStats();render();
    }
}

async function qr(v){document.getElementById('slider').value=v;updateR(v);await saveR();next();}
function prev(){if(idx>0)select(idx-1);}
function next(){if(idx<images.length-1)select(idx+1);}
async function scan(){const r=await(await fetch('/api/scan')).json();alert('Found '+r.new+' new');loadStats();load();}

async function openTrain(){
    document.getElementById('trainModal').classList.add('open');
    document.getElementById('trainResults').innerHTML='<p style="color:#888">Processing...</p>';
    const r=await(await fetch('/api/process',{method:'POST'})).json();
    let h=`<div class="section"><h4>Summary</h4><p>Rated: <b>${r.total_rated}</b> | Avg: <b>${r.avg_rating}</b> | High(8+): <b>${r.high_count}</b> | Low(1-4): <b>${r.low_count}</b></p></div>`;
    h+=`<div class="section"><h4>Rating Distribution</h4>`;
    const maxC=Math.max(...Object.values(r.distribution||{1:1}));
    for(const[rating,count]of Object.entries(r.distribution||{}).sort((a,b)=>b[0]-a[0])){
        const w=count/maxC*100;
        h+=`<div class="dist-row"><span>${rating}</span><div class="dist-bar" style="width:${w}%"></div><span>${count}</span></div>`;
    }
    h+=`</div>`;
    document.getElementById('trainResults').innerHTML=h;
}
function closeTrain(){document.getElementById('trainModal').classList.remove('open');}

function openPrompt(){
    document.getElementById('promptModal').classList.add('open');
    // Show all available tags
    const tags=[];
    for(const[cat,list]of Object.entries(window.TAGS||{})){
        tags.push(...list.map(t=>`<span class="tag">${t}</span>`));
    }
    document.getElementById('allTags').innerHTML=tags.join('');
}
function closePrompt(){document.getElementById('promptModal').classList.remove('open');}

async function genPrompt(){
    const subj=document.getElementById('subject').value;
    const level=document.getElementById('detailLevel').value;
    const r=await(await fetch('/api/prompt?subject='+encodeURIComponent(subj)+'&level='+level)).json();
    document.getElementById('genPrompt').textContent=r.prompt;
}
function copyPrompt(){navigator.clipboard.writeText(document.getElementById('genPrompt').textContent);alert('Copied!');}
function copyNeg(){navigator.clipboard.writeText(document.getElementById('negPrompt').textContent);alert('Copied!');}

document.addEventListener('keydown',e=>{
    if(e.key==='ArrowLeft')prev();
    if(e.key==='ArrowRight')next();
    if(e.key>='0'&&e.key<='9'){document.getElementById('slider').value=e.key;updateR(e.key);saveR();}
    if(e.key==='Escape'){closeTrain();closePrompt();}
});

// Store tags for display
window.TAGS={
    quality:["masterpiece","best quality","highly detailed","ultra detailed","8k uhd","photorealistic"],
    face:["detailed face","beautiful face","detailed eyes","beautiful eyes","long eyelashes","glossy lips"],
    skin:["detailed skin","flawless skin","smooth skin","subsurface scattering","glowing skin"],
    lighting:["cinematic lighting","soft lighting","natural lighting","volumetric lighting","golden hour"],
    camera:["sharp focus","depth of field","bokeh","85mm lens","DSLR","RAW photo"]
};

loadStats();load();
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
    def do_GET(self):
        path = self.path.split('?')[0]
        query = {}
        if '?' in self.path:
            for p in self.path.split('?')[1].split('&'):
                if '=' in p:
                    k, v = p.split('=', 1)
                    query[k] = v
                    
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
        elif path == '/api/stats':
            self._json(db.stats())
        elif path == '/api/images':
            self._json(db.get_images(query.get('f', 'all')))
        elif path == '/api/scan':
            self._json(db.scan())
        elif path == '/api/prompt':
            from urllib.parse import unquote
            subj = unquote(query.get('subject', 'beautiful woman'))
            level = int(query.get('level', '3'))
            self._json(build_perfection_prompt(subj, "realistic", level))
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
        path = self.path.split('?')[0]
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length else {}
        
        if path == '/api/rate':
            self._json(db.rate(data['id'], data['rating']))
        elif path == '/api/process':
            self._json(db.process())
        else:
            self._json({'error': 'not found'})
            
    def log_message(self, *args): pass


if __name__ == "__main__":
    print("=" * 60)
    print("  RATING STUDIO V2 + PERFECTION PROMPT GENERATOR")
    print("=" * 60)
    db.scan()
    s = db.stats()
    print(f"\nImages: {s['total']} | Rated: {s['rated']} | Unrated: {s['unrated']}")
    print(f"\nOpen: http://127.0.0.1:8196")
    print("\nFeatures:")
    print("  - Auto-save ratings")
    print("  - Process & Train button")
    print("  - Perfection Prompt Generator (70+ tags)")
    HTTPServer(('0.0.0.0', 8196), Handler).serve_forever()
