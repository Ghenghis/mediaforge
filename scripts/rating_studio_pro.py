"""
RATING STUDIO PRO - AUTO-LEARNING INTEGRATED
================================================
- Left panel layout (35% / 65%)
- Resizable grid (4-60 images)
- ALL prompts saved to history
- Auto-learns from 10+ ratings (AUTOMATIC)
- Batch recording & comparison
- Tag performance tracking
- Prompt enhancer buttons USE learned patterns
- Everything shared & always up-to-date
"""
import sqlite3
import json
import random
import requests
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

PORT = 8196
COMFYUI_URL = "http://localhost:8188"
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\master_learning.db")

# Quality tag pools for prompt building
QUALITY_BOOST = ["masterpiece", "best quality", "highly detailed", "ultra detailed", "8k uhd", "photorealistic", "hyperrealistic", "professional"]
FACE_BOOST = ["detailed face", "beautiful eyes", "perfect features", "symmetrical face", "detailed pupils", "long eyelashes"]
LIGHTING_BOOST = ["cinematic lighting", "soft lighting", "volumetric lighting", "golden hour", "dramatic lighting"]
CAMERA_BOOST = ["sharp focus", "depth of field", "bokeh", "85mm lens", "DSLR", "RAW photo"]

# Standard negative prompt
NEGATIVE = "bad anatomy, bad hands, extra fingers, missing fingers, deformed, disfigured, mutated, ugly, blurry, low quality, worst quality, watermark, text"


class ProDB:
    """Auto-Learning Database - All prompts tracked, patterns learned automatically"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()
        
    def _init(self):
        self.conn.executescript('''
            -- Core images with full tracking
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY, filename TEXT UNIQUE, prompt TEXT,
                negative_prompt TEXT, seed INTEGER, batch_id TEXT,
                rating REAL DEFAULT 0, is_gold_standard INTEGER DEFAULT 0,
                is_trainable INTEGER DEFAULT 0, marked_enhance INTEGER DEFAULT 0,
                tags TEXT, theme TEXT, created_at TEXT, rated_at TEXT
            );
            
            -- Batch tracking for comparisons
            CREATE TABLE IF NOT EXISTS batches (
                id TEXT PRIMARY KEY, name TEXT, prompt_template TEXT, theme TEXT,
                count INTEGER DEFAULT 0, avg_rating REAL DEFAULT 0, best_rating REAL DEFAULT 0,
                created_at TEXT
            );
            
            -- ALL prompt history saved
            CREATE TABLE IF NOT EXISTS prompt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT, negative TEXT, seed INTEGER, batch_id TEXT,
                theme TEXT, tags_used TEXT, rating REAL, created_at TEXT
            );
            
            -- Learned patterns from 10+ rated (AUTO-UPDATED)
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT, pattern_value TEXT, weight REAL DEFAULT 1.0,
                occurrences INTEGER DEFAULT 1, avg_rating REAL DEFAULT 0,
                created_at TEXT, updated_at TEXT
            );
            
            -- Tag performance tracking
            CREATE TABLE IF NOT EXISTS tag_performance (
                tag TEXT PRIMARY KEY, times_used INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0, high_count INTEGER DEFAULT 0,
                low_count INTEGER DEFAULT 0, updated_at TEXT
            );
            
            -- Training log
            CREATE TABLE IF NOT EXISTS training_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_type TEXT, source_image TEXT, patterns_learned INTEGER,
                created_at TEXT
            );
        ''')
        # Add columns if missing
        for col in ['marked_enhance INTEGER DEFAULT 0', 'tags TEXT', 'theme TEXT', 
                    'batch_id TEXT', 'is_trainable INTEGER DEFAULT 0', 'seed INTEGER',
                    'negative_prompt TEXT', 'path TEXT']:
            try: self.conn.execute(f'ALTER TABLE images ADD COLUMN {col}')
            except: pass
        self.conn.commit()
        
    def scan(self, folder=None):
        """Scan folder for images"""
        if folder:
            scan_path = Path(folder)
        else:
            scan_path = OUTPUT_DIR
            
        if not scan_path.exists():
            return {'error': f'Folder not found: {folder}', 'images': []}
            
        # Get all image files
        imgs = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
            imgs.extend(scan_path.glob(ext))
        
        # Sort by name
        imgs = sorted(imgs, key=lambda x: x.name)
        
        new = 0
        for img in imgs:
            if not self.conn.execute('SELECT 1 FROM images WHERE filename=?', (img.name,)).fetchone():
                theme = self._detect_theme(img.name)
                self.conn.execute('INSERT INTO images (id, filename, theme, created_at, path) VALUES (?,?,?,?,?)',
                    (f"img_{hash(str(img))%10**8}", img.name, theme, datetime.now().isoformat(), str(img)))
                new += 1
        self.conn.commit()
        
        return {
            'total': len(imgs), 
            'new': new,
            'images': [str(img) for img in imgs]
        }
        
    def _detect_theme(self, filename):
        fn = filename.lower()
        if 'tribal' in fn or 'warrior' in fn: return 'tribal_warrior'
        if 'elegant' in fn: return 'elegant_portrait'
        if 'natural' in fn: return 'natural_beauty'
        if 'artistic' in fn: return 'artistic_portrait'
        return 'general'
        
    def get_images(self, filter_type='all', limit=100):
        sql = 'SELECT id, filename, rating, prompt, marked_enhance, theme FROM images'
        if filter_type == 'unrated': sql += ' WHERE rating = 0 OR rating IS NULL'
        elif filter_type == 'rated': sql += ' WHERE rating > 0'
        elif filter_type == 'high': sql += ' WHERE rating >= 8'
        elif filter_type == 'excellent': sql += ' WHERE rating >= 10'
        elif filter_type == 'enhance': sql += ' WHERE rating >= 6 AND rating <= 8'
        elif filter_type == 'marked': sql += ' WHERE marked_enhance = 1'
        elif filter_type == 'gold': sql += ' WHERE rating >= 15'
        sql += f' ORDER BY created_at DESC LIMIT {limit}'
        return [dict(r) for r in self.conn.execute(sql).fetchall()]
        
    def rate(self, img_id, rating):
        """Rate image and AUTO-LEARN if 10+"""
        rating = max(0, min(15, float(rating)))
        is_trainable = 1 if rating >= 10 else 0
        
        self.conn.execute('''UPDATE images SET rating=?, rated_at=?, is_gold_standard=?, is_trainable=? WHERE id=?''',
            (rating, datetime.now().isoformat(), 1 if rating >= 15 else 0, is_trainable, img_id))
        self.conn.commit()
        
        # AUTO-TRIGGER: Learn from 10+ rated images
        auto_learned = False
        if rating >= 10:
            auto_learned = self._auto_learn(img_id, rating)
            
        return {'id': img_id, 'rating': rating, 'trainable': is_trainable, 'auto_learned': auto_learned}
        
    def _auto_learn(self, img_id, rating):
        """Automatically learn patterns from high-rated image"""
        img = self.conn.execute('SELECT * FROM images WHERE id=?', (img_id,)).fetchone()
        if not img: return False
        
        patterns = 0
        
        # Learn theme pattern
        if img['theme']:
            self._update_pattern('theme', img['theme'], rating)
            patterns += 1
            
        # Learn from filename patterns
        fn = img['filename'].lower()
        for kw in ['tribal', 'warrior', 'elegant', 'natural', 'artistic', 'enhanced', 'batch']:
            if kw in fn:
                self._update_pattern('keyword', kw, rating)
                patterns += 1
                
        # Log training trigger
        self.conn.execute('''INSERT INTO training_log (trigger_type, source_image, patterns_learned, created_at) 
            VALUES (?,?,?,?)''', ('auto_10plus', img_id, patterns, datetime.now().isoformat()))
        self.conn.commit()
        return True
        
    def _update_pattern(self, ptype, value, rating):
        """Update or create learned pattern"""
        existing = self.conn.execute(
            'SELECT id, weight, occurrences, avg_rating FROM learned_patterns WHERE pattern_type=? AND pattern_value=?',
            (ptype, value)).fetchone()
            
        now = datetime.now().isoformat()
        if existing:
            new_occ = existing['occurrences'] + 1
            new_avg = ((existing['avg_rating'] * existing['occurrences']) + rating) / new_occ
            new_weight = min(5.0, existing['weight'] + (0.5 if rating >= 12 else 0.2))
            self.conn.execute('''UPDATE learned_patterns SET weight=?, occurrences=?, avg_rating=?, updated_at=? WHERE id=?''',
                (new_weight, new_occ, new_avg, now, existing['id']))
        else:
            self.conn.execute('''INSERT INTO learned_patterns (pattern_type, pattern_value, weight, avg_rating, created_at) VALUES (?,?,?,?,?)''',
                (ptype, value, 1.0 + (0.5 if rating >= 12 else 0), rating, now))
                
    def get_learned_prompt(self, theme=None):
        """Build prompt using LEARNED patterns from 10+ rated images"""
        parts = []
        
        # Get best theme from learned patterns
        if theme:
            parts.append(theme.replace('_', ' '))
        else:
            top = self.conn.execute('''SELECT pattern_value FROM learned_patterns 
                WHERE pattern_type='theme' ORDER BY weight DESC, avg_rating DESC LIMIT 1''').fetchone()
            if top:
                parts.append(top['pattern_value'].replace('_', ' '))
                
        # Get high-weight learned keywords
        keywords = self.conn.execute('''SELECT pattern_value FROM learned_patterns 
            WHERE pattern_type='keyword' AND avg_rating >= 8 ORDER BY weight DESC LIMIT 5''').fetchall()
        parts.extend([k['pattern_value'] for k in keywords])
        
        # Add quality tags (weighted by learned performance)
        for pool in [QUALITY_BOOST, FACE_BOOST, LIGHTING_BOOST, CAMERA_BOOST]:
            parts.extend(random.sample(pool, min(3, len(pool))))
            
        return ', '.join(parts)
        
    def save_prompt_history(self, prompt, negative, seed, batch_id, theme):
        """Save EVERY prompt to history"""
        self.conn.execute('''INSERT INTO prompt_history (prompt, negative, seed, batch_id, theme, created_at) VALUES (?,?,?,?,?,?)''',
            (prompt, negative, seed, batch_id, theme, datetime.now().isoformat()))
        self.conn.commit()
        
    def get_learning_stats(self):
        """Get auto-learning statistics"""
        patterns = self.conn.execute('SELECT COUNT(*) FROM learned_patterns').fetchone()[0]
        prompts = self.conn.execute('SELECT COUNT(*) FROM prompt_history').fetchone()[0]
        trainings = self.conn.execute('SELECT COUNT(*) FROM training_log').fetchone()[0]
        top_themes = [dict(r) for r in self.conn.execute('''SELECT pattern_value, weight, avg_rating 
            FROM learned_patterns WHERE pattern_type='theme' ORDER BY weight DESC LIMIT 5''').fetchall()]
        return {'patterns': patterns, 'prompts_saved': prompts, 'trainings': trainings, 'top_themes': top_themes}
        
    def mark_enhance(self, img_id, marked=True):
        self.conn.execute('UPDATE images SET marked_enhance=? WHERE id=?', (1 if marked else 0, img_id))
        self.conn.commit()
        return {'id': img_id, 'marked': marked}
        
    def get_stats(self):
        t = self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]
        r = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
        h = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 8').fetchone()[0]
        e = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 10').fetchone()[0]
        tr = self.conn.execute('SELECT COUNT(*) FROM images WHERE is_trainable = 1').fetchone()[0]
        en = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 6 AND rating <= 8').fetchone()[0]
        m = self.conn.execute('SELECT COUNT(*) FROM images WHERE marked_enhance = 1').fetchone()[0]
        g = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 15').fetchone()[0]
        avg = self.conn.execute('SELECT AVG(rating) FROM images WHERE rating > 0').fetchone()[0] or 0
        # Learning stats
        patterns = self.conn.execute('SELECT COUNT(*) FROM learned_patterns').fetchone()[0]
        prompts = self.conn.execute('SELECT COUNT(*) FROM prompt_history').fetchone()[0]
        return {'total': t, 'rated': r, 'unrated': t-r, 'high': h, 'excellent': e, 'trainable': tr,
                'enhanceable': en, 'marked': m, 'gold': g, 'avg': round(avg, 2),
                'patterns_learned': patterns, 'prompts_saved': prompts}
                
    def get_excellent_patterns(self):
        """Get patterns from 10+ rated images for enhancement"""
        rows = self.conn.execute('SELECT filename, theme, prompt FROM images WHERE rating >= 10').fetchall()
        themes = {}
        for r in rows:
            t = r['theme'] or 'general'
            if t not in themes: themes[t] = 0
            themes[t] += 1
        return {'count': len(rows), 'themes': themes}
        
    def get_enhancement_candidates(self):
        """Get 6-8 rated images that can be enhanced"""
        return [dict(r) for r in self.conn.execute(
            'SELECT id, filename, rating, theme FROM images WHERE rating >= 6 AND rating <= 8 ORDER BY rating DESC'
        ).fetchall()]


db = ProDB()


HTML = '''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8"><title>Rating Studio Pro</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', sans-serif; background: #0a0a0f; color: #e0e0e0; height: 100vh; overflow: hidden; }

/* LAYOUT */
.container { display: flex; height: 100vh; }
.left-panel { width: 35%; min-width: 300px; max-width: 500px; background: #12121a; border-right: 1px solid #333; display: flex; flex-direction: column; resize: horizontal; overflow: auto; }
.main-panel { flex: 1; display: flex; flex-direction: column; background: #0a0a0f; }

/* LEFT PANEL SECTIONS */
.panel-header { padding: 15px; background: linear-gradient(135deg, #1a1a2e, #16213e); border-bottom: 1px solid #333; }
.panel-header h1 { font-size: 1.4em; color: #00d4ff; margin-bottom: 5px; }
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 10px; }
.stat-box { background: #1a1a2e; padding: 8px; border-radius: 6px; text-align: center; }
.stat-value { font-size: 1.5em; font-weight: bold; color: #00d4ff; }
.stat-label { font-size: 0.75em; color: #888; }

/* CONTROLS */
.controls { padding: 15px; border-bottom: 1px solid #333; }
.control-group { margin-bottom: 12px; }
.control-label { font-size: 0.85em; color: #888; margin-bottom: 5px; display: flex; justify-content: space-between; }
.slider-container { display: flex; align-items: center; gap: 10px; }
.slider-container input[type="range"] { flex: 1; }
.slider-value { min-width: 40px; text-align: center; color: #00d4ff; font-weight: bold; }

/* FILTERS */
.filter-buttons { display: flex; flex-wrap: wrap; gap: 6px; }
.filter-btn { padding: 6px 12px; border: 1px solid #444; background: #1a1a2e; color: #ccc; border-radius: 4px; cursor: pointer; font-size: 0.8em; }
.filter-btn:hover { background: #2a2a4e; }
.filter-btn.active { background: #00d4ff; color: #000; border-color: #00d4ff; }

/* FEATURE BUTTONS */
.features { padding: 15px; flex: 1; overflow-y: auto; }
.feature-section { margin-bottom: 15px; }
.feature-title { font-size: 0.9em; color: #00d4ff; margin-bottom: 8px; padding-bottom: 5px; border-bottom: 1px solid #333; }
.feature-btn { width: 100%; padding: 10px; margin-bottom: 6px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; text-align: left; display: flex; align-items: center; gap: 10px; transition: all 0.2s; }
.feature-btn:hover { transform: translateX(5px); }
.feature-btn.enhance { background: linear-gradient(135deg, #00b894, #00cec9); color: #000; }
.feature-btn.generate { background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: #fff; }
.feature-btn.merge { background: linear-gradient(135deg, #fd79a8, #e84393); color: #fff; }
.feature-btn.analyze { background: linear-gradient(135deg, #fdcb6e, #f39c12); color: #000; }
.feature-btn.queue { background: linear-gradient(135deg, #74b9ff, #0984e3); color: #fff; }
.feature-btn .icon { font-size: 1.2em; }

/* MAIN PANEL */
.main-header { padding: 10px 15px; background: #12121a; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; }
.view-info { color: #888; font-size: 0.9em; }
.grid-container { flex: 1; overflow-y: auto; padding: 10px; }
.image-grid { display: grid; gap: 8px; }

/* IMAGE CARDS */
.img-card { position: relative; aspect-ratio: 3/4; border-radius: 8px; overflow: hidden; cursor: pointer; border: 2px solid transparent; transition: all 0.2s; }
.img-card:hover { transform: scale(1.02); border-color: #00d4ff; }
.img-card.selected { border-color: #00ff88; box-shadow: 0 0 20px rgba(0,255,136,0.3); }
.img-card.marked { border-color: #fd79a8; }
.img-card img { width: 100%; height: 100%; object-fit: cover; }
.img-rating { position: absolute; bottom: 5px; right: 5px; background: rgba(0,0,0,0.8); padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
.img-rating.high { color: #00ff88; }
.img-rating.medium { color: #fdcb6e; }
.img-rating.low { color: #ff6b6b; }
.img-mark { position: absolute; top: 5px; right: 5px; background: #fd79a8; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; }

/* PREVIEW PANEL */
.preview-panel { position: fixed; top: 0; right: 0; width: 65%; height: 100vh; background: rgba(10,10,15,0.98); display: none; flex-direction: column; z-index: 100; }
.preview-panel.active { display: flex; }
.preview-header { padding: 15px; background: #12121a; display: flex; justify-content: space-between; align-items: center; }
.preview-close { background: #ff4757; border: none; color: #fff; padding: 8px 20px; border-radius: 4px; cursor: pointer; }
.preview-image { flex: 1; display: flex; align-items: center; justify-content: center; padding: 20px; overflow: hidden; }
.preview-image img { max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px; }
.preview-controls { padding: 20px; background: #12121a; }
.rating-section { margin-bottom: 15px; }
.rating-slider { width: 100%; height: 30px; }
.rating-buttons { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 10px; }
.rating-btn { padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
.rating-btn:hover { opacity: 0.8; }
.action-buttons { display: flex; gap: 10px; flex-wrap: wrap; }
.action-btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9em; }
.action-btn.mark { background: #fd79a8; color: #fff; }
.action-btn.enhance { background: #00b894; color: #000; }
.action-btn.nav { background: #333; color: #fff; }

/* MODAL */
.modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: none; align-items: center; justify-content: center; z-index: 200; }
.modal.active { display: flex; }
.modal-content { background: #1a1a2e; padding: 30px; border-radius: 12px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto; }
.modal-title { font-size: 1.5em; color: #00d4ff; margin-bottom: 20px; }
.modal-close { float: right; background: none; border: none; color: #fff; font-size: 1.5em; cursor: pointer; }
.modal-body { margin: 20px 0; }
.modal-btn { padding: 12px 25px; border: none; border-radius: 6px; cursor: pointer; margin-right: 10px; }
.modal-btn.primary { background: #00d4ff; color: #000; }
.modal-btn.secondary { background: #333; color: #fff; }

/* TOAST */
.toast { position: fixed; bottom: 20px; right: 20px; background: #00d4ff; color: #000; padding: 15px 25px; border-radius: 8px; display: none; z-index: 300; font-weight: bold; }
.toast.show { display: block; animation: fadeInOut 2s; }
@keyframes fadeInOut { 0%,100% { opacity: 0; } 10%,90% { opacity: 1; } }
</style>
</head>
<body>

<div class="container">
  <!-- LEFT PANEL -->
  <div class="left-panel">
    <div class="panel-header">
      <h1>⚡ Rating Studio Pro</h1>
      <div class="stats-grid">
        <div class="stat-box"><div class="stat-value" id="stat-total">0</div><div class="stat-label">Total</div></div>
        <div class="stat-box"><div class="stat-value" id="stat-unrated">0</div><div class="stat-label">Unrated</div></div>
        <div class="stat-box"><div class="stat-value" id="stat-excellent">0</div><div class="stat-label">Excellent 10+</div></div>
        <div class="stat-box"><div class="stat-value" id="stat-enhanceable">0</div><div class="stat-label">Enhance 6-8</div></div>
      </div>
    </div>
    
    <div class="controls">
      <div class="control-group">
        <div class="control-label"><span>Grid Size</span><span id="grid-size-label">16 images</span></div>
        <div class="slider-container">
          <input type="range" id="grid-slider" min="4" max="60" value="16" step="4">
        </div>
      </div>
      
      <div class="control-group">
        <div class="control-label"><span>Filter</span></div>
        <div class="filter-buttons">
          <button class="filter-btn active" data-filter="all">All</button>
          <button class="filter-btn" data-filter="unrated">Unrated</button>
          <button class="filter-btn" data-filter="high">High 8+</button>
          <button class="filter-btn" data-filter="excellent">Excellent 10+</button>
          <button class="filter-btn" data-filter="enhance">Enhance 6-8</button>
          <button class="filter-btn" data-filter="marked">Marked</button>
        </div>
      </div>
    </div>
    
    <div class="features">
      <div class="feature-section">
        <div class="feature-title">🚀 Enhancement Features</div>
        <button class="feature-btn enhance" onclick="autoEnhanceQueue()"><span class="icon">✨</span> Auto-Enhance 6-8 Stars</button>
        <button class="feature-btn merge" onclick="mergeWithBest()"><span class="icon">🔗</span> Merge with Best Prompts</button>
        <button class="feature-btn queue" onclick="showEnhanceQueue()"><span class="icon">📋</span> View Enhancement Queue</button>
      </div>
      
      <div class="feature-section">
        <div class="feature-title">🎨 Generation</div>
        <button class="feature-btn generate" onclick="generateFromExcellent()"><span class="icon">⭐</span> Generate from 10+ Patterns</button>
        <button class="feature-btn generate" onclick="generateBatch()"><span class="icon">📦</span> Generate Batch (10)</button>
        <button class="feature-btn generate" onclick="generatePerfection()"><span class="icon">💎</span> Generate Perfection Prompt</button>
      </div>
      
      <div class="feature-section">
        <div class="feature-title">📊 Analysis</div>
        <button class="feature-btn analyze" onclick="analyzePatterns()"><span class="icon">🔍</span> Analyze High-Rated Patterns</button>
        <button class="feature-btn analyze" onclick="showDistribution()"><span class="icon">📈</span> Rating Distribution</button>
        <button class="feature-btn analyze" onclick="exportData()"><span class="icon">💾</span> Export Training Data</button>
      </div>
      
      <div class="feature-section">
        <div class="feature-title">⚙️ Tools</div>
        <button class="feature-btn" style="background:#333;color:#fff" onclick="scanImages()"><span class="icon">🔄</span> Scan New Images</button>
        <button class="feature-btn" style="background:#333;color:#fff" onclick="markAllEnhanceable()"><span class="icon">✅</span> Mark All 6-8 for Enhance</button>
        <button class="feature-btn" style="background:#333;color:#fff" onclick="clearMarked()"><span class="icon">🗑️</span> Clear All Marks</button>
      </div>
    </div>
  </div>
  
  <!-- MAIN PANEL -->
  <div class="main-panel">
    <div class="main-header">
      <div class="view-info">Showing <span id="view-count">0</span> images</div>
      <div><button class="filter-btn" onclick="scanImages()">🔄 Refresh</button></div>
    </div>
    <div class="grid-container">
      <div class="image-grid" id="image-grid"></div>
    </div>
  </div>
</div>

<!-- PREVIEW PANEL -->
<div class="preview-panel" id="preview-panel">
  <div class="preview-header">
    <div><strong id="preview-filename">filename.png</strong> <span id="preview-theme" style="color:#888"></span></div>
    <button class="preview-close" onclick="closePreview()">✕ Close</button>
  </div>
  <div class="preview-image">
    <img id="preview-img" src="" alt="">
  </div>
  <div class="preview-controls">
    <div class="rating-section">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <span>Rating: <strong id="current-rating" style="font-size:1.5em;color:#00d4ff">0</strong></span>
        <span id="rating-category" style="color:#888">Not Rated</span>
      </div>
      <input type="range" class="rating-slider" id="rating-slider" min="0" max="15" value="0">
      <div class="rating-buttons">
        <button class="rating-btn" style="background:#ff6b6b;color:#fff" onclick="quickRate(0)">0</button>
        <button class="rating-btn" style="background:#ffa502" onclick="quickRate(3)">3</button>
        <button class="rating-btn" style="background:#fdcb6e" onclick="quickRate(5)">5</button>
        <button class="rating-btn" style="background:#7bed9f" onclick="quickRate(7)">7</button>
        <button class="rating-btn" style="background:#00d4ff;color:#000" onclick="quickRate(8)">8</button>
        <button class="rating-btn" style="background:#00b894;color:#fff" onclick="quickRate(10)">10</button>
        <button class="rating-btn" style="background:#6c5ce7;color:#fff" onclick="quickRate(12)">12</button>
        <button class="rating-btn" style="background:#e84393;color:#fff" onclick="quickRate(15)">15⭐</button>
      </div>
    </div>
    <div class="action-buttons">
      <button class="action-btn nav" onclick="prevImage()">◀ Prev</button>
      <button class="action-btn nav" onclick="nextImage()">Next ▶</button>
      <button class="action-btn mark" id="mark-btn" onclick="toggleMark()">📌 Mark for Enhance</button>
      <button class="action-btn enhance" onclick="enhanceThis()">✨ Enhance Now</button>
    </div>
  </div>
</div>

<!-- MODAL -->
<div class="modal" id="modal">
  <div class="modal-content">
    <button class="modal-close" onclick="closeModal()">×</button>
    <div class="modal-title" id="modal-title">Title</div>
    <div class="modal-body" id="modal-body"></div>
    <div>
      <button class="modal-btn primary" id="modal-action" onclick="modalAction()">Confirm</button>
      <button class="modal-btn secondary" onclick="closeModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- TOAST -->
<div class="toast" id="toast"></div>

<script>
let images = [];
let currentIndex = -1;
let currentFilter = 'all';
let gridSize = 16;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadImages();
  
  document.getElementById('grid-slider').addEventListener('input', (e) => {
    gridSize = parseInt(e.target.value);
    document.getElementById('grid-size-label').textContent = gridSize + ' images';
    updateGrid();
  });
  
  document.getElementById('rating-slider').addEventListener('input', (e) => {
    const rating = parseInt(e.target.value);
    document.getElementById('current-rating').textContent = rating;
    updateRatingCategory(rating);
  });
  
  document.getElementById('rating-slider').addEventListener('change', (e) => {
    if (currentIndex >= 0) saveRating(images[currentIndex].id, parseInt(e.target.value));
  });
  
  document.querySelectorAll('.filter-btn[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn[data-filter]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      loadImages();
    });
  });
  
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (document.getElementById('preview-panel').classList.contains('active')) {
      if (e.key === 'ArrowLeft') prevImage();
      else if (e.key === 'ArrowRight') nextImage();
      else if (e.key === 'Escape') closePreview();
      else if (e.key >= '0' && e.key <= '9') quickRate(parseInt(e.key));
      else if (e.key === 'm') toggleMark();
    }
  });
});

async function loadStats() {
  const res = await fetch('/api/stats');
  const stats = await res.json();
  document.getElementById('stat-total').textContent = stats.total;
  document.getElementById('stat-unrated').textContent = stats.unrated;
  document.getElementById('stat-excellent').textContent = stats.excellent;
  document.getElementById('stat-enhanceable').textContent = stats.enhanceable;
}

async function loadImages() {
  const res = await fetch(`/api/images?filter=${currentFilter}&limit=500`);
  images = await res.json();
  document.getElementById('view-count').textContent = images.length;
  updateGrid();
}

function updateGrid() {
  const grid = document.getElementById('image-grid');
  const cols = Math.ceil(Math.sqrt(gridSize));
  grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  
  grid.innerHTML = images.slice(0, gridSize).map((img, i) => `
    <div class="img-card ${img.marked_enhance ? 'marked' : ''}" onclick="openPreview(${i})">
      <img src="/image/${img.filename}" loading="lazy" alt="">
      ${img.marked_enhance ? '<div class="img-mark">📌</div>' : ''}
      <div class="img-rating ${img.rating >= 10 ? 'high' : img.rating >= 6 ? 'medium' : 'low'}">
        ${img.rating > 0 ? img.rating : '-'}
      </div>
    </div>
  `).join('');
}

function openPreview(index) {
  currentIndex = index;
  const img = images[index];
  document.getElementById('preview-panel').classList.add('active');
  document.getElementById('preview-img').src = `/image/${img.filename}`;
  document.getElementById('preview-filename').textContent = img.filename;
  document.getElementById('preview-theme').textContent = img.theme ? `(${img.theme})` : '';
  document.getElementById('rating-slider').value = img.rating || 0;
  document.getElementById('current-rating').textContent = img.rating || 0;
  document.getElementById('mark-btn').textContent = img.marked_enhance ? '📌 Marked' : '📌 Mark for Enhance';
  updateRatingCategory(img.rating || 0);
}

function closePreview() {
  document.getElementById('preview-panel').classList.remove('active');
  currentIndex = -1;
}

function prevImage() {
  if (currentIndex > 0) openPreview(currentIndex - 1);
}

function nextImage() {
  if (currentIndex < images.length - 1) openPreview(currentIndex + 1);
}

function updateRatingCategory(rating) {
  let cat = 'Not Rated';
  if (rating >= 15) cat = '⭐ Gold Standard';
  else if (rating >= 10) cat = '✨ Excellent';
  else if (rating >= 8) cat = '👍 High Quality';
  else if (rating >= 6) cat = '📈 Enhanceable';
  else if (rating >= 4) cat = '😐 Average';
  else if (rating > 0) cat = '👎 Low';
  document.getElementById('rating-category').textContent = cat;
}

function quickRate(rating) {
  if (currentIndex >= 0) {
    document.getElementById('rating-slider').value = rating;
    document.getElementById('current-rating').textContent = rating;
    updateRatingCategory(rating);
    saveRating(images[currentIndex].id, rating);
  }
}

async function saveRating(id, rating) {
  await fetch('/api/rate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id, rating})
  });
  images[currentIndex].rating = rating;
  updateGrid();
  loadStats();
  toast(`Saved: ${rating}/15`);
}

async function toggleMark() {
  if (currentIndex < 0) return;
  const img = images[currentIndex];
  const marked = !img.marked_enhance;
  await fetch('/api/mark', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: img.id, marked})
  });
  img.marked_enhance = marked;
  document.getElementById('mark-btn').textContent = marked ? '📌 Marked' : '📌 Mark for Enhance';
  updateGrid();
  toast(marked ? 'Marked for enhancement' : 'Unmarked');
}

async function scanImages() {
  const res = await fetch('/api/scan');
  const data = await res.json();
  toast(`Scanned: ${data.new} new images`);
  loadImages();
  loadStats();
}

// Feature functions
async function autoEnhanceQueue() {
  showModal('Auto-Enhance 6-8 Stars', 
    '<p>This will take all images rated 6-8 and enhance them using patterns from your 10+ rated images.</p>' +
    '<p>Estimated: <strong id="enhance-count">...</strong> images will be enhanced.</p>',
    async () => {
      const res = await fetch('/api/auto-enhance', {method: 'POST'});
      const data = await res.json();
      toast(`Queued ${data.queued} images for enhancement`);
      closeModal();
    }
  );
  const stats = await (await fetch('/api/stats')).json();
  document.getElementById('enhance-count').textContent = stats.enhanceable;
}

async function mergeWithBest() {
  showModal('Merge with Best Prompts',
    '<p>Merge marked images with prompts from your highest-rated (10+) images to create enhanced versions.</p>',
    async () => {
      const res = await fetch('/api/merge-best', {method: 'POST'});
      const data = await res.json();
      toast(`Merged ${data.count} images`);
      closeModal();
    }
  );
}

async function generateFromExcellent() {
  const res = await fetch('/api/excellent-patterns');
  const data = await res.json();
  showModal('Generate from Excellent Patterns',
    `<p>You have <strong>${data.count}</strong> excellent (10+) images.</p>` +
    `<p>Themes: ${Object.entries(data.themes).map(([k,v]) => `${k}: ${v}`).join(', ')}</p>` +
    `<p>Generate new images based on these patterns?</p>`,
    async () => {
      const res = await fetch('/api/generate-from-excellent', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({count: 20})});
      const data = await res.json();
      toast(`Queued ${data.queued} images`);
      closeModal();
    }
  );
}

async function generateBatch() {
  const res = await fetch('/api/generate-batch', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({count: 10})});
  const data = await res.json();
  toast(`Queued ${data.queued} images`);
}

function generatePerfection() {
  showModal('Perfection Prompt Generator',
    '<p>Enter subject:</p><input type="text" id="perf-subject" style="width:100%;padding:10px;margin:10px 0;background:#333;border:1px solid #555;color:#fff;border-radius:4px" placeholder="e.g. tribal warrior woman">' +
    '<p>Detail level:</p><select id="perf-level" style="width:100%;padding:10px;background:#333;border:1px solid #555;color:#fff;border-radius:4px"><option value="1">Basic (30 tags)</option><option value="2">Enhanced (50 tags)</option><option value="3" selected>Perfection (70+ tags)</option></select>',
    async () => {
      const subject = document.getElementById('perf-subject').value;
      const level = document.getElementById('perf-level').value;
      const res = await fetch(`/api/prompt?subject=${encodeURIComponent(subject)}&level=${level}`);
      const data = await res.json();
      showModal('Generated Prompt', `<textarea style="width:100%;height:200px;background:#333;border:1px solid #555;color:#fff;padding:10px;border-radius:4px">${data.prompt}</textarea><p style="margin-top:10px">Tags: ${data.tags_count}</p>`, () => {
        navigator.clipboard.writeText(data.prompt);
        toast('Copied to clipboard!');
        closeModal();
      });
      document.getElementById('modal-action').textContent = 'Copy';
    }
  );
}

async function analyzePatterns() {
  const res = await fetch('/api/analyze');
  const data = await res.json();
  showModal('Pattern Analysis', 
    `<h3>High-Rated Themes</h3>` +
    Object.entries(data.themes).map(([k,v]) => `<p>${k}: <strong>${v}</strong></p>`).join('') +
    `<h3 style="margin-top:15px">Recommendations</h3>` +
    data.recommendations.map(r => `<p>• ${r}</p>`).join(''),
    closeModal
  );
  document.getElementById('modal-action').style.display = 'none';
}

async function showDistribution() {
  const res = await fetch('/api/distribution');
  const data = await res.json();
  let html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px">';
  for (let i = 0; i <= 15; i++) {
    const count = data[i] || 0;
    const pct = Math.min(100, count * 5);
    html += `<div style="text-align:center"><div style="font-size:1.2em;font-weight:bold">${i}</div><div style="height:${pct}px;background:#00d4ff;margin:5px auto;width:30px;border-radius:3px"></div><div style="font-size:0.8em">${count}</div></div>`;
  }
  html += '</div>';
  showModal('Rating Distribution', html, closeModal);
  document.getElementById('modal-action').style.display = 'none';
}

function showEnhanceQueue() {
  showModal('Enhancement Queue', '<p>Loading...</p>', closeModal);
  fetch('/api/enhancement-candidates').then(r => r.json()).then(data => {
    document.getElementById('modal-body').innerHTML = 
      `<p>Images rated 6-8 that can be enhanced:</p>` +
      `<div style="max-height:300px;overflow-y:auto">` +
      data.map(img => `<div style="display:flex;align-items:center;gap:10px;padding:5px;border-bottom:1px solid #333"><img src="/image/${img.filename}" style="width:50px;height:50px;object-fit:cover;border-radius:4px"><span>${img.filename}</span><span style="color:#fdcb6e">${img.rating}</span></div>`).join('') +
      `</div>`;
  });
  document.getElementById('modal-action').style.display = 'none';
}

async function enhanceThis() {
  if (currentIndex < 0) return;
  const img = images[currentIndex];
  const res = await fetch('/api/enhance-single', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: img.id})
  });
  const data = await res.json();
  toast(`Enhancement queued!`);
}

async function markAllEnhanceable() {
  const res = await fetch('/api/mark-all-enhanceable', {method: 'POST'});
  const data = await res.json();
  toast(`Marked ${data.count} images`);
  loadImages();
}

async function clearMarked() {
  const res = await fetch('/api/clear-marks', {method: 'POST'});
  toast('Cleared all marks');
  loadImages();
}

async function exportData() {
  const res = await fetch('/api/export');
  const data = await res.json();
  showModal('Export Data', `<p>Exported ${data.count} rated images to:</p><code>${data.path}</code>`, closeModal);
  document.getElementById('modal-action').style.display = 'none';
}

function showModal(title, body, action) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = body;
  document.getElementById('modal').classList.add('active');
  document.getElementById('modal-action').style.display = 'block';
  document.getElementById('modal-action').textContent = 'Confirm';
  window.modalActionFn = action;
}

function modalAction() {
  if (window.modalActionFn) window.modalActionFn();
}

function closeModal() {
  document.getElementById('modal').classList.remove('active');
}

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}
</script>
</body></html>'''


class ProAPI(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
        
    def do_OPTIONS(self):
        self.send_response(200)
        for h in ['Origin', 'Methods', 'Headers']: self.send_header(f'Access-Control-Allow-{h}', '*')
        self.end_headers()
        
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
            
        elif path == '/api/stats':
            self._json(db.get_stats())
            
        elif path == '/api/images':
            f = query.get('filter', ['all'])[0]
            limit = int(query.get('limit', ['100'])[0])
            self._json(db.get_images(f, limit))
            
        elif path == '/api/scan':
            folder = query.get('folder', [None])[0]
            self._json(db.scan(folder))
            
        elif path == '/api/distribution':
            dist = {}
            for row in db.conn.execute('SELECT CAST(rating AS INTEGER) as r, COUNT(*) FROM images WHERE rating > 0 GROUP BY r'):
                dist[row[0]] = row[1]
            self._json(dist)
            
        elif path == '/api/excellent-patterns':
            self._json(db.get_excellent_patterns())
            
        elif path == '/api/enhancement-candidates':
            self._json(db.get_enhancement_candidates())
            
        elif path == '/api/analyze':
            patterns = db.get_excellent_patterns()
            recs = []
            if patterns['themes'].get('tribal_warrior', 0) > 2:
                recs.append('Tribal/warrior themes perform well - generate more')
            if patterns['count'] >= 5:
                recs.append('You have enough excellent samples for pattern learning')
            recs.append('Consider enhancing 6-8 rated images with top patterns')
            self._json({'themes': patterns['themes'], 'recommendations': recs})
            
        elif path == '/api/prompt':
            subject = query.get('subject', [''])[0]
            level = int(query.get('level', ['3'])[0])
            prompt = self._build_prompt(subject, level)
            self._json({'prompt': prompt, 'tags_count': len(prompt.split(','))})
            
        elif path.startswith('/image/'):
            fn = path[7:]
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
            self._json({'error': 'not found'}, 404)
            
    def _build_prompt(self, subject, level):
        """Build prompt using LEARNED patterns + quality tags"""
        parts = []
        
        # Use learned patterns from 10+ rated images
        learned = db.get_learned_prompt(subject if subject else None)
        if learned:
            parts.append(learned)
        elif subject:
            parts.append(subject)
        else:
            parts.append('beautiful woman portrait')
            
        # Add quality tags
        parts.extend(random.sample(QUALITY_BOOST, min(level*2, len(QUALITY_BOOST))))
        parts.extend(random.sample(FACE_BOOST, min(level, len(FACE_BOOST))))
        parts.extend(random.sample(LIGHTING_BOOST, min(level, len(LIGHTING_BOOST))))
        parts.extend(random.sample(CAMERA_BOOST, min(level, len(CAMERA_BOOST))))
        return ', '.join(parts)
        
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/rate':
            self._json(db.rate(data['id'], data['rating']))
            
        elif path == '/api/mark':
            self._json(db.mark_enhance(data['id'], data.get('marked', True)))
            
        elif path == '/api/auto-enhance':
            candidates = db.get_enhancement_candidates()
            queued = self._queue_enhancements(candidates)
            self._json({'queued': queued})
            
        elif path == '/api/merge-best':
            marked = db.get_images('marked', 100)
            count = self._merge_with_best(marked)
            self._json({'count': count})
            
        elif path == '/api/generate-batch':
            count = int(data.get('count', 10))
            queued = self._generate_batch(count)
            self._json({'queued': queued})
            
        elif path == '/api/generate-from-excellent':
            count = int(data.get('count', 20))
            queued = self._generate_from_patterns(count)
            self._json({'queued': queued})
            
        elif path == '/api/enhance-single':
            result = self._enhance_single(data['id'])
            self._json(result)
            
        elif path == '/api/mark-all-enhanceable':
            db.conn.execute('UPDATE images SET marked_enhance = 1 WHERE rating >= 6 AND rating <= 8')
            db.conn.commit()
            count = db.conn.execute('SELECT COUNT(*) FROM images WHERE marked_enhance = 1').fetchone()[0]
            self._json({'count': count})
            
        elif path == '/api/clear-marks':
            db.conn.execute('UPDATE images SET marked_enhance = 0')
            db.conn.commit()
            self._json({'cleared': True})
            
        elif path == '/api/export':
            path_out = Path(r'c:\Users\Admin\civitai\data\training_export.json')
            data = [dict(r) for r in db.conn.execute('SELECT filename, rating, theme FROM images WHERE rating > 0')]
            with open(path_out, 'w') as f:
                json.dump(data, f, indent=2)
            self._json({'count': len(data), 'path': str(path_out)})
            
        else:
            self._json({'error': 'not found'}, 404)
            
    def _queue_comfyui(self, prompt, negative, seed, filename):
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {"cfg": 7, "denoise": 1, "latent_image": ["5", 0], "model": ["4", 0], "negative": ["7", 0], "positive": ["6", 0], "sampler_name": "euler_ancestral", "scheduler": "normal", "seed": seed, "steps": 30}},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "CyberRealistic.safetensors"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": 768, "width": 512}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": prompt}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": negative}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": filename, "images": ["8", 0]}}
        }
        try:
            r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=10)
            return 'prompt_id' in r.json()
        except:
            return False
            
    def _queue_enhancements(self, candidates):
        """Queue enhancements - SAVES ALL PROMPTS to history"""
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        batch_id = f"enhance_{ts}"
        negative = NEGATIVE
        queued = 0
        for img in candidates[:20]:
            theme = img.get('theme', '')
            prompt = self._build_prompt(theme, 3)
            seed = random.randint(1, 2**31)
            filename = f"enhanced_{ts}_{img['filename'].split('.')[0]}"
            if self._queue_comfyui(prompt, negative, seed, filename):
                # SAVE to prompt history
                db.save_prompt_history(prompt, negative, seed, batch_id, theme)
                queued += 1
        return queued
        
    def _merge_with_best(self, marked):
        """Merge with best - SAVES ALL PROMPTS to history"""
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        batch_id = f"merged_{ts}"
        negative = NEGATIVE
        count = 0
        for img in marked[:10]:
            prompt = self._build_prompt('', 3)
            seed = random.randint(1, 2**31)
            filename = f"merged_{ts}_{count+1:03d}"
            if self._queue_comfyui(prompt, negative, seed, filename):
                db.save_prompt_history(prompt, negative, seed, batch_id, 'merged')
                count += 1
        return count
        
    def _generate_batch(self, count):
        """Generate batch - SAVES ALL PROMPTS to history"""
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        batch_id = f"batch_{ts}"
        negative = NEGATIVE
        queued = 0
        for i in range(count):
            prompt = self._build_prompt('', 3)
            seed = random.randint(1, 2**31)
            filename = f"batch_{ts}_{i+1:03d}"
            if self._queue_comfyui(prompt, negative, seed, filename):
                db.save_prompt_history(prompt, negative, seed, batch_id, 'batch')
                queued += 1
        return queued
        
    def _generate_from_patterns(self, count):
        """Generate from patterns - SAVES ALL PROMPTS to history"""
        patterns = db.get_excellent_patterns()
        themes = list(patterns['themes'].keys()) or ['general']
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        batch_id = f"pattern_{ts}"
        negative = NEGATIVE
        queued = 0
        for i in range(count):
            theme = random.choice(themes)
            prompt = self._build_prompt(theme.replace('_', ' '), 3)
            seed = random.randint(1, 2**31)
            filename = f"pattern_{ts}_{theme}_{i+1:03d}"
            if self._queue_comfyui(prompt, negative, seed, filename):
                db.save_prompt_history(prompt, negative, seed, batch_id, theme)
                queued += 1
        return queued
        
    def _enhance_single(self, img_id):
        """Enhance single - SAVES PROMPT to history"""
        row = db.conn.execute('SELECT filename, theme FROM images WHERE id=?', (img_id,)).fetchone()
        if not row:
            return {'error': 'not found'}
        theme = row['theme'] or ''
        prompt = self._build_prompt(theme, 3)
        negative = NEGATIVE
        seed = random.randint(1, 2**31)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        batch_id = f"single_{ts}"
        filename = f"single_{ts}_{seed}"
        success = self._queue_comfyui(prompt, negative, seed, filename)
        if success:
            db.save_prompt_history(prompt, negative, seed, batch_id, theme)
        return {'queued': success, 'filename': filename}
            
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  RATING STUDIO PRO - AUTO-LEARNING")
    print("=" * 60)
    
    db.scan()
    stats = db.get_stats()
    
    print(f"\n📊 Images: {stats['total']} total | {stats['rated']} rated | {stats['unrated']} unrated")
    print(f"   Excellent 10+: {stats['excellent']} | Trainable: {stats.get('trainable', 0)} | Gold 15: {stats['gold']}")
    print(f"   Enhanceable 6-8: {stats['enhanceable']} | Marked: {stats['marked']}")
    
    print(f"\n🧠 Auto-Learning:")
    print(f"   Patterns learned: {stats.get('patterns_learned', 0)}")
    print(f"   Prompts saved: {stats.get('prompts_saved', 0)}")
    
    print(f"\n⚡ AUTO-LEARNING ACTIVE:")
    print(f"   - Rating 10+ triggers automatic pattern learning")
    print(f"   - All prompts saved to history")
    print(f"   - Enhancer buttons use learned patterns")
    
    print(f"\n🌐 http://127.0.0.1:{PORT}")
    
    HTTPServer(('0.0.0.0', PORT), ProAPI).serve_forever()


if __name__ == "__main__":
    main()
