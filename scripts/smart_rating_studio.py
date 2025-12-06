"""
SMART RATING STUDIO WITH AUTO-SAVE & LEARNING ENGINE
- Auto-saves every rating instantly
- Shows only unrated images
- Process button for AI training
- Prompt enhancement engine
- Detail enhancement suggestions
"""
import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import Counter

OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\master_learning.db")

class SmartDB:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()
        
    def _ensure_tables(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                filename TEXT UNIQUE,
                filepath TEXT,
                prompt TEXT,
                negative_prompt TEXT,
                tags TEXT,
                rating REAL DEFAULT 0,
                rating_history TEXT DEFAULT '[]',
                is_gold_standard INTEGER DEFAULT 0,
                created_at TEXT,
                rated_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS tag_learning (
                tag TEXT PRIMARY KEY,
                total_score REAL DEFAULT 0,
                count INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0,
                high_count INTEGER DEFAULT 0,
                low_count INTEGER DEFAULT 0,
                best_combos TEXT DEFAULT '[]',
                updated_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS prompt_enhancements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_prompt TEXT,
                enhanced_prompt TEXT,
                enhancement_type TEXT,
                rating_improvement REAL,
                created_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS training_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT,
                completed_at TEXT,
                images_processed INTEGER,
                insights TEXT,
                enhancements TEXT
            );
            
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_type TEXT,
                preference_value TEXT,
                weight REAL DEFAULT 1.0,
                source TEXT,
                created_at TEXT
            );
        ''')
        self.conn.commit()
        
    def scan_images(self):
        """Scan for new images"""
        images = list(OUTPUT_DIR.glob("*.png"))
        new_count = 0
        for img in images:
            exists = self.conn.execute('SELECT 1 FROM images WHERE filename=?', (img.name,)).fetchone()
            if not exists:
                img_id = f"img_{hash(img.name) % 10**8}"
                self.conn.execute('''INSERT INTO images (id, filename, filepath, created_at) 
                    VALUES (?,?,?,?)''', (img_id, img.name, str(img), datetime.now().isoformat()))
                new_count += 1
        self.conn.commit()
        return {'total': len(images), 'new': new_count}
        
    def get_unrated(self):
        """Get only unrated images"""
        return [dict(r) for r in self.conn.execute(
            'SELECT id, filename, rating FROM images WHERE rating = 0 OR rating IS NULL ORDER BY created_at DESC'
        ).fetchall()]
        
    def get_all(self, filter_type='all'):
        """Get images with filter"""
        sql = 'SELECT id, filename, rating FROM images'
        if filter_type == 'unrated':
            sql += ' WHERE rating = 0 OR rating IS NULL'
        elif filter_type == 'rated':
            sql += ' WHERE rating > 0'
        elif filter_type == 'high':
            sql += ' WHERE rating >= 8'
        elif filter_type == 'excellent':
            sql += ' WHERE rating >= 10'
        sql += ' ORDER BY created_at DESC'
        return [dict(r) for r in self.conn.execute(sql).fetchall()]
        
    def rate_image(self, img_id, rating):
        """Auto-save rating immediately"""
        rating = max(0, min(15, float(rating)))
        now = datetime.now().isoformat()
        
        # Get current rating history
        row = self.conn.execute('SELECT rating_history, rating FROM images WHERE id=?', (img_id,)).fetchone()
        history = json.loads(row['rating_history'] or '[]') if row else []
        if row and row['rating']:
            history.append({'rating': row['rating'], 'at': now})
        
        # Update
        self.conn.execute('''UPDATE images SET 
            rating=?, rated_at=?, is_gold_standard=?, rating_history=?
            WHERE id=?''', (rating, now, 1 if rating >= 15 else 0, json.dumps(history), img_id))
        self.conn.commit()
        
        return {'id': img_id, 'rating': rating, 'saved': True}
        
    def get_stats(self):
        """Get current statistics"""
        total = self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]
        rated = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
        excellent = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 10').fetchone()[0]
        gold = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 15').fetchone()[0]
        avg = self.conn.execute('SELECT AVG(rating) FROM images WHERE rating > 0').fetchone()[0] or 0
        
        # Rating distribution
        dist = {}
        for r in self.conn.execute('SELECT rating, COUNT(*) FROM images WHERE rating > 0 GROUP BY rating').fetchall():
            dist[int(r[0])] = r[1]
            
        return {
            'total': total, 'rated': rated, 'unrated': total - rated,
            'excellent': excellent, 'gold': gold, 'avg': round(avg, 2),
            'distribution': dist
        }


class LearningEngine:
    """AI Learning Engine for prompt enhancement"""
    
    def __init__(self, db):
        self.db = db
        
    def process_ratings(self):
        """Process all ratings and learn patterns"""
        results = {
            'images_processed': 0,
            'patterns_found': [],
            'enhancement_suggestions': [],
            'tag_weights': {},
            'preferred_features': [],
            'avoid_features': []
        }
        
        # Get all rated images
        rated = self.db.conn.execute('''
            SELECT id, filename, rating, prompt, tags FROM images WHERE rating > 0
        ''').fetchall()
        
        results['images_processed'] = len(rated)
        
        # Analyze high vs low rated
        high_rated = [r for r in rated if r['rating'] >= 8]
        low_rated = [r for r in rated if r['rating'] <= 4]
        
        # Extract patterns from filenames (since we may not have prompts stored)
        high_patterns = self._extract_patterns([r['filename'] for r in high_rated])
        low_patterns = self._extract_patterns([r['filename'] for r in low_rated])
        
        # Find preferred patterns (in high but not low)
        for pattern, count in high_patterns.items():
            if pattern not in low_patterns or high_patterns[pattern] > low_patterns.get(pattern, 0) * 2:
                results['preferred_features'].append({
                    'feature': pattern,
                    'high_count': count,
                    'low_count': low_patterns.get(pattern, 0)
                })
                
        # Find patterns to avoid (in low but not high)
        for pattern, count in low_patterns.items():
            if pattern not in high_patterns or low_patterns[pattern] > high_patterns.get(pattern, 0) * 2:
                results['avoid_features'].append({
                    'feature': pattern,
                    'low_count': count,
                    'high_count': high_patterns.get(pattern, 0)
                })
        
        # Calculate tag weights from rating distribution
        for rating in range(0, 16):
            count = self.db.conn.execute(
                'SELECT COUNT(*) FROM images WHERE rating = ?', (rating,)
            ).fetchone()[0]
            if count > 0:
                results['tag_weights'][rating] = count
                
        # Generate enhancement suggestions
        results['enhancement_suggestions'] = self._generate_enhancements(
            results['preferred_features'],
            results['avoid_features']
        )
        
        # Save training session
        session_id = self._save_session(results)
        results['session_id'] = session_id
        
        return results
        
    def _extract_patterns(self, filenames):
        """Extract patterns from filenames"""
        patterns = Counter()
        for fn in filenames:
            # Extract keywords from filename
            parts = re.split(r'[_\-\.\d]+', fn.lower())
            for part in parts:
                if len(part) > 2:
                    patterns[part] += 1
        return dict(patterns)
        
    def _generate_enhancements(self, preferred, avoid):
        """Generate prompt enhancement suggestions"""
        suggestions = []
        
        # Base quality enhancers
        quality_tags = [
            "highly detailed", "sharp focus", "professional lighting",
            "8k resolution", "masterpiece", "best quality",
            "intricate details", "photorealistic", "hyperrealistic"
        ]
        
        # Detail enhancers
        detail_tags = [
            "detailed eyes", "detailed skin texture", "detailed hair",
            "detailed clothing", "detailed background", "subsurface scattering",
            "ray tracing", "volumetric lighting", "ambient occlusion"
        ]
        
        # Style enhancers
        style_tags = [
            "cinematic lighting", "dramatic lighting", "soft lighting",
            "golden hour", "studio lighting", "natural lighting"
        ]
        
        suggestions.append({
            'type': 'quality',
            'title': 'Quality Enhancement',
            'tags': quality_tags,
            'reason': 'Add these to improve overall image quality'
        })
        
        suggestions.append({
            'type': 'detail',
            'title': 'Detail Enhancement',
            'tags': detail_tags,
            'reason': 'Add these to enhance specific details'
        })
        
        suggestions.append({
            'type': 'style',
            'title': 'Style Enhancement',
            'tags': style_tags,
            'reason': 'Add these to improve lighting and mood'
        })
        
        # Based on preferred features
        if preferred:
            top_preferred = sorted(preferred, key=lambda x: x['high_count'], reverse=True)[:5]
            suggestions.append({
                'type': 'learned',
                'title': 'Your Preferred Features',
                'tags': [p['feature'] for p in top_preferred],
                'reason': 'Based on your high-rated images'
            })
            
        # Based on features to avoid
        if avoid:
            top_avoid = sorted(avoid, key=lambda x: x['low_count'], reverse=True)[:5]
            suggestions.append({
                'type': 'avoid',
                'title': 'Features to Avoid',
                'tags': [a['feature'] for a in top_avoid],
                'reason': 'Based on your low-rated images'
            })
            
        return suggestions
        
    def _save_session(self, results):
        """Save training session"""
        self.db.conn.execute('''INSERT INTO training_sessions 
            (started_at, completed_at, images_processed, insights, enhancements)
            VALUES (?, ?, ?, ?, ?)''', (
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            results['images_processed'],
            json.dumps(results['preferred_features'][:10]),
            json.dumps(results['enhancement_suggestions'])
        ))
        self.db.conn.commit()
        return self.db.conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
    def get_enhanced_prompt(self, base_prompt=""):
        """Generate an enhanced prompt based on learned preferences"""
        # Get latest training insights
        session = self.db.conn.execute('''
            SELECT insights, enhancements FROM training_sessions 
            ORDER BY id DESC LIMIT 1
        ''').fetchone()
        
        enhancements = []
        if session:
            insights = json.loads(session['insights'] or '[]')
            suggestions = json.loads(session['enhancements'] or '[]')
            
            # Add quality enhancers
            for s in suggestions:
                if s['type'] in ['quality', 'detail']:
                    enhancements.extend(s['tags'][:3])
                    
        # Build enhanced prompt
        if base_prompt:
            enhanced = base_prompt
        else:
            enhanced = "beautiful woman, portrait"
            
        if enhancements:
            enhanced += ", " + ", ".join(enhancements[:8])
            
        return enhanced


db = SmartDB()
engine = LearningEngine(db)

HTML = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Smart Rating Studio</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #111; color: #fff; font-family: Arial, sans-serif; }

.header {
    position: fixed; top: 0; left: 0; right: 0; height: 60px;
    background: #1a1a1a; display: flex; align-items: center;
    padding: 0 20px; gap: 20px; z-index: 100; border-bottom: 1px solid #333;
}
.logo { font-size: 18px; font-weight: bold; color: #4af; }
.stats { display: flex; gap: 15px; }
.stat { text-align: center; }
.stat-num { font-size: 20px; font-weight: bold; color: #4af; }
.stat-label { font-size: 9px; color: #666; }
.progress-wrap { flex: 1; max-width: 300px; }
.progress { height: 8px; background: #333; border-radius: 4px; overflow: hidden; }
.progress-bar { height: 100%; background: linear-gradient(90deg, #4af, #f80); transition: width 0.3s; }
.tools { display: flex; gap: 10px; margin-left: auto; }
.btn { padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold; }
.btn-blue { background: #4af; color: #000; }
.btn-green { background: #0a0; color: #fff; }
.btn-orange { background: #f80; color: #000; }
.btn:hover { opacity: 0.8; }
select { padding: 8px 12px; background: #333; color: #fff; border: 1px solid #444; border-radius: 6px; }

.main { display: flex; margin-top: 60px; height: calc(100vh - 60px); }

.gallery {
    flex: 1; padding: 20px; overflow-y: auto;
    display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px; align-content: start;
}
.thumb {
    background: #222; border-radius: 8px; overflow: hidden;
    cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
    border: 2px solid transparent;
}
.thumb:hover { transform: scale(1.03); box-shadow: 0 8px 25px rgba(0,0,0,0.5); }
.thumb.selected { border-color: #4af; box-shadow: 0 0 20px rgba(68,170,255,0.3); }
.thumb.rated { border-color: #0a0; }
.thumb.excellent { border-color: #f80; }
.thumb img { width: 100%; height: 130px; object-fit: cover; }
.thumb-info { padding: 6px 8px; display: flex; justify-content: space-between; align-items: center; background: #1a1a1a; }
.thumb-rating { font-size: 18px; font-weight: bold; color: #4af; }
.thumb-status { font-size: 10px; color: #0a0; }

.sidebar {
    width: 380px; background: #1a1a1a; padding: 20px;
    display: flex; flex-direction: column; gap: 15px;
    border-left: 1px solid #333; overflow-y: auto;
}
.preview-wrap { 
    position: relative; background: #000; border-radius: 8px; 
    overflow: hidden; max-height: 350px;
}
.preview-img { width: 100%; max-height: 350px; object-fit: contain; cursor: zoom-in; }
.preview-img.zoomed { cursor: zoom-out; max-height: none; transform: scale(2); transform-origin: center; }

.rating-section { background: #222; padding: 15px; border-radius: 8px; }
.rating-section h3 { color: #4af; margin-bottom: 10px; font-size: 14px; }
.rating-display { font-size: 50px; font-weight: bold; text-align: center; color: #4af; }
.rating-label { text-align: center; color: #888; margin-bottom: 10px; font-size: 12px; }
.rating-slider { width: 100%; height: 30px; -webkit-appearance: none; background: linear-gradient(90deg, #444, #4af 50%, #f80 75%, #f44 100%); border-radius: 15px; margin: 10px 0; }
.rating-slider::-webkit-slider-thumb { -webkit-appearance: none; width: 28px; height: 28px; background: #fff; border-radius: 50%; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.5); }
.quick-btns { display: grid; grid-template-columns: repeat(8, 1fr); gap: 4px; margin-top: 10px; }
.quick-btn { padding: 8px 4px; border: none; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer; }
.quick-btn:hover { opacity: 0.8; }
.q-low { background: #444; color: #fff; }
.q-mid { background: #666; color: #fff; }
.q-good { background: #080; color: #fff; }
.q-great { background: #0a0; color: #fff; }
.q-exc { background: #f80; color: #000; }
.q-perf { background: #f44; color: #fff; }

.auto-save { text-align: center; padding: 8px; background: #0a03; border-radius: 6px; color: #0a0; font-size: 12px; }
.nav-btns { display: flex; gap: 10px; }
.nav-btns button { flex: 1; padding: 12px; font-size: 14px; }

.info-section { background: #222; padding: 12px; border-radius: 8px; font-size: 11px; color: #888; }
.info-section div { margin: 4px 0; }
.info-section b { color: #4af; }

.shortcuts { background: #333; padding: 10px; border-radius: 6px; font-size: 10px; color: #666; }
.shortcuts b { color: #4af; }

/* Training Modal */
.modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 200; overflow-y: auto; padding: 40px; }
.modal.open { display: block; }
.modal-content { max-width: 800px; margin: 0 auto; background: #222; border-radius: 12px; padding: 30px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-header h2 { color: #4af; }
.modal-close { font-size: 24px; cursor: pointer; color: #888; }
.modal-close:hover { color: #fff; }

.results-section { background: #1a1a1a; padding: 15px; border-radius: 8px; margin: 15px 0; }
.results-section h4 { color: #f80; margin-bottom: 10px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 4px 10px; background: #333; border-radius: 4px; font-size: 12px; }
.tag.good { background: #0a03; color: #0f0; }
.tag.bad { background: #a003; color: #f88; }

.enhanced-prompt { background: #000; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 12px; color: #0f0; white-space: pre-wrap; }
</style>
</head>
<body>

<div class="header">
    <div class="logo">Smart Rating Studio</div>
    <div class="stats">
        <div class="stat"><div class="stat-num" id="sTotal">0</div><div class="stat-label">TOTAL</div></div>
        <div class="stat"><div class="stat-num" id="sRated">0</div><div class="stat-label">RATED</div></div>
        <div class="stat"><div class="stat-num" id="sLeft">0</div><div class="stat-label">LEFT</div></div>
        <div class="stat"><div class="stat-num" id="sExc">0</div><div class="stat-label">EXCELLENT</div></div>
        <div class="stat"><div class="stat-num" id="sAvg">0</div><div class="stat-label">AVG</div></div>
    </div>
    <div class="progress-wrap">
        <div class="progress"><div class="progress-bar" id="progressBar" style="width:0%"></div></div>
    </div>
    <div class="tools">
        <select id="filterSelect" onchange="loadImages()">
            <option value="unrated">Unrated Only</option>
            <option value="all">All Images</option>
            <option value="rated">Rated Only</option>
            <option value="high">High Rated (8+)</option>
            <option value="excellent">Excellent (10+)</option>
        </select>
        <button class="btn btn-blue" onclick="scan()">Scan</button>
        <button class="btn btn-green" onclick="openTraining()">Process & Train</button>
    </div>
</div>

<div class="main">
    <div class="gallery" id="gallery"></div>
    
    <div class="sidebar">
        <div class="preview-wrap">
            <img class="preview-img" id="previewImg" src="" onclick="toggleZoom(this)">
        </div>
        
        <div class="rating-section">
            <h3>RATE THIS IMAGE</h3>
            <div class="rating-display" id="ratingDisplay">-</div>
            <div class="rating-label" id="ratingLabel">Select an image</div>
            <input type="range" class="rating-slider" id="ratingSlider" min="0" max="15" value="0" 
                   oninput="updateRating(this.value)" onchange="saveRating()">
            <div class="quick-btns">
                <button class="quick-btn q-low" onclick="quickRate(0)">0</button>
                <button class="quick-btn q-low" onclick="quickRate(2)">2</button>
                <button class="quick-btn q-mid" onclick="quickRate(4)">4</button>
                <button class="quick-btn q-mid" onclick="quickRate(6)">6</button>
                <button class="quick-btn q-good" onclick="quickRate(8)">8</button>
                <button class="quick-btn q-great" onclick="quickRate(10)">10</button>
                <button class="quick-btn q-exc" onclick="quickRate(12)">12</button>
                <button class="quick-btn q-perf" onclick="quickRate(15)">15</button>
            </div>
        </div>
        
        <div class="auto-save" id="saveStatus">Auto-save enabled</div>
        
        <div class="nav-btns">
            <button class="btn btn-blue" onclick="prevImage()">Previous</button>
            <button class="btn btn-blue" onclick="nextImage()">Next</button>
        </div>
        
        <div class="info-section">
            <div><b>File:</b> <span id="infoFile">-</span></div>
            <div><b>Position:</b> <span id="infoPos">-</span></div>
        </div>
        
        <div class="shortcuts">
            <b>Arrow Keys</b> = Navigate | <b>0-9</b> = Rate | <b>Click Image</b> = Zoom
        </div>
    </div>
</div>

<!-- Training Modal -->
<div class="modal" id="trainingModal">
    <div class="modal-content">
        <div class="modal-header">
            <h2>Training & Enhancement Results</h2>
            <span class="modal-close" onclick="closeTraining()">X</span>
        </div>
        <div id="trainingResults"></div>
    </div>
</div>

<script>
let images = [];
let currentIdx = -1;
let currentImage = null;

async function loadStats() {
    const s = await (await fetch('/api/stats')).json();
    document.getElementById('sTotal').textContent = s.total;
    document.getElementById('sRated').textContent = s.rated;
    document.getElementById('sLeft').textContent = s.unrated;
    document.getElementById('sExc').textContent = s.excellent;
    document.getElementById('sAvg').textContent = s.avg;
    document.getElementById('progressBar').style.width = (s.total > 0 ? s.rated/s.total*100 : 0) + '%';
}

async function loadImages() {
    const filter = document.getElementById('filterSelect').value;
    images = await (await fetch('/api/images?filter=' + filter)).json();
    renderGallery();
    if (images.length > 0 && currentIdx < 0) selectImage(0);
}

function renderGallery() {
    document.getElementById('gallery').innerHTML = images.map((img, i) => {
        let cls = 'thumb';
        if (i === currentIdx) cls += ' selected';
        if (img.rating >= 10) cls += ' excellent';
        else if (img.rating > 0) cls += ' rated';
        return `
            <div class="${cls}" onclick="selectImage(${i})" data-idx="${i}">
                <img src="/image/${img.filename}" loading="lazy">
                <div class="thumb-info">
                    <span class="thumb-rating">${img.rating || '-'}</span>
                    <span class="thumb-status">${img.rating > 0 ? 'Saved' : ''}</span>
                </div>
            </div>
        `;
    }).join('');
}

function selectImage(idx) {
    if (idx < 0 || idx >= images.length) return;
    currentIdx = idx;
    currentImage = images[idx];
    
    document.getElementById('previewImg').src = '/image/' + currentImage.filename;
    document.getElementById('previewImg').classList.remove('zoomed');
    document.getElementById('ratingSlider').value = currentImage.rating || 0;
    updateRating(currentImage.rating || 0);
    document.getElementById('infoFile').textContent = currentImage.filename;
    document.getElementById('infoPos').textContent = (idx + 1) + ' / ' + images.length;
    
    renderGallery();
}

function toggleZoom(img) {
    img.classList.toggle('zoomed');
}

function updateRating(val) {
    document.getElementById('ratingDisplay').textContent = val;
    const labels = ['Skip', 'Poor', 'Poor', 'Bad', 'Bad', 'Average', 'OK', 'OK', 'Good', 'Good', 
                    'Excellent', 'Excellent', 'Great', 'Amazing', 'Near Perfect', 'PERFECT!'];
    document.getElementById('ratingLabel').textContent = labels[parseInt(val)] || '';
}

async function saveRating() {
    if (!currentImage) return;
    const rating = parseInt(document.getElementById('ratingSlider').value);
    
    document.getElementById('saveStatus').textContent = 'Saving...';
    document.getElementById('saveStatus').style.background = '#ff03';
    
    const result = await fetch('/api/rate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id: currentImage.id, rating: rating})
    }).then(r => r.json());
    
    if (result.saved) {
        currentImage.rating = rating;
        document.getElementById('saveStatus').textContent = 'Saved! Rating: ' + rating;
        document.getElementById('saveStatus').style.background = '#0a03';
        loadStats();
        renderGallery();
    }
}

async function quickRate(val) {
    document.getElementById('ratingSlider').value = val;
    updateRating(val);
    await saveRating();
    nextImage();
}

function prevImage() { if (currentIdx > 0) selectImage(currentIdx - 1); }
function nextImage() { if (currentIdx < images.length - 1) selectImage(currentIdx + 1); }

async function scan() {
    const r = await (await fetch('/api/scan')).json();
    alert('Found ' + r.new + ' new images. Total: ' + r.total);
    loadStats();
    loadImages();
}

async function openTraining() {
    document.getElementById('trainingModal').classList.add('open');
    document.getElementById('trainingResults').innerHTML = '<p style="color:#888">Processing ratings and generating enhancements...</p>';
    
    const results = await (await fetch('/api/train', {method: 'POST'})).json();
    
    let html = `
        <div class="results-section">
            <h4>Processing Summary</h4>
            <p>Analyzed <b>${results.images_processed}</b> rated images</p>
        </div>
        
        <div class="results-section">
            <h4>Rating Distribution</h4>
            <div style="display:flex;gap:10px;flex-wrap:wrap">
                ${Object.entries(results.tag_weights || {}).map(([r, c]) => 
                    `<div class="tag">Rating ${r}: ${c}</div>`
                ).join('')}
            </div>
        </div>
        
        <div class="results-section">
            <h4>Your Preferred Features (High-Rated Images)</h4>
            <div class="tag-list">
                ${(results.preferred_features || []).slice(0, 10).map(p => 
                    `<span class="tag good">${p.feature} (${p.high_count})</span>`
                ).join('')}
            </div>
        </div>
        
        <div class="results-section">
            <h4>Features to Avoid (Low-Rated Images)</h4>
            <div class="tag-list">
                ${(results.avoid_features || []).slice(0, 10).map(a => 
                    `<span class="tag bad">${a.feature} (${a.low_count})</span>`
                ).join('')}
            </div>
        </div>
    `;
    
    // Enhancement suggestions
    for (const s of (results.enhancement_suggestions || [])) {
        html += `
            <div class="results-section">
                <h4>${s.title}</h4>
                <p style="color:#888;font-size:12px;margin-bottom:10px">${s.reason}</p>
                <div class="tag-list">
                    ${s.tags.map(t => `<span class="tag">${t}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    // Enhanced prompt
    const enhanced = await (await fetch('/api/enhanced-prompt')).json();
    html += `
        <div class="results-section">
            <h4>Sample Enhanced Prompt</h4>
            <div class="enhanced-prompt">${enhanced.prompt}</div>
        </div>
    `;
    
    document.getElementById('trainingResults').innerHTML = html;
}

function closeTraining() {
    document.getElementById('trainingModal').classList.remove('open');
}

// Keyboard
document.addEventListener('keydown', (e) => {
    if (document.getElementById('trainingModal').classList.contains('open')) {
        if (e.key === 'Escape') closeTraining();
        return;
    }
    
    switch(e.key) {
        case 'ArrowLeft': prevImage(); break;
        case 'ArrowRight': nextImage(); break;
        case '0': case '1': case '2': case '3': case '4':
        case '5': case '6': case '7': case '8': case '9':
            document.getElementById('ratingSlider').value = e.key;
            updateRating(e.key);
            saveRating();
            break;
    }
});

// Init
loadStats();
loadImages();
</script>
</body>
</html>'''


class Handler(BaseHTTPRequestHandler):
    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
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
        elif path == '/api/stats':
            self._json(db.get_stats())
        elif path == '/api/images':
            self._json(db.get_all(query.get('filter', 'unrated')))
        elif path == '/api/scan':
            self._json(db.scan_images())
        elif path == '/api/enhanced-prompt':
            self._json({'prompt': engine.get_enhanced_prompt()})
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
            self._json(db.rate_image(data['id'], data['rating']))
        elif path == '/api/train':
            self._json(engine.process_ratings())
        else:
            self._json({'error': 'not found'})
            
    def log_message(self, *args): pass


if __name__ == "__main__":
    print("=" * 60)
    print("  SMART RATING STUDIO")
    print("=" * 60)
    
    db.scan_images()
    s = db.get_stats()
    print(f"\nImages: {s['total']} | Rated: {s['rated']} | Unrated: {s['unrated']}")
    
    print(f"\nOpen: http://127.0.0.1:8195")
    print("\nFeatures:")
    print("  - Auto-saves every rating instantly")
    print("  - Shows unrated images by default")
    print("  - Process & Train button for AI learning")
    print("  - Generates enhanced prompts from your ratings")
    
    HTTPServer(('0.0.0.0', 8195), Handler).serve_forever()
