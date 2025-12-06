"""
RATING STUDIO ULTRA - Compact UI + LLM Integration
===================================================
- Compact left panel (no scrolling)
- LLM-powered prompt enhancement (LM Studio/Ollama)
- Content rating system (PG to 21+)
- AI prompt builder with questions
- Tag selection (30+ tags)
- Generate from 7+ rated only
"""
import sqlite3
import json
import random
import requests
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

PORT = 8196
COMFYUI_URL = "http://localhost:8188"
LM_STUDIO_URL = "http://localhost:1234/v1"  # LM Studio default
OLLAMA_URL = "http://localhost:11434"  # Ollama default
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\master_learning.db")

# Quality tags
QUALITY = ["masterpiece", "best quality", "highly detailed", "ultra detailed", "8k uhd", "photorealistic"]
FACE = ["detailed face", "beautiful eyes", "perfect features", "symmetrical face"]
LIGHTING = ["cinematic lighting", "soft lighting", "volumetric lighting", "golden hour"]
CAMERA = ["sharp focus", "depth of field", "bokeh", "85mm lens", "DSLR"]
NEGATIVE = "bad anatomy, bad hands, extra fingers, deformed, blurry, low quality, worst quality, watermark, text"

# Import content rating validator
try:
    from content_rating_validator import get_validator, get_era_manager, validate_and_sanitize, ContentRating
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False

# Content Rating Guidelines (PG to 21+ with coverage %)
CONTENT_RATINGS = {
    "PG": {"label": "PG", "coverage": 95, "desc": "Fully clothed, modest"},
    "PG13": {"label": "PG-13", "coverage": 85, "desc": "Light revealing, summer casual"},
    "PG14": {"label": "PG-14", "coverage": 75, "desc": "Swimwear appropriate"},
    "PG15": {"label": "PG-15", "coverage": 65, "desc": "Bikini/lingerie hints"},
    "PG16": {"label": "PG-16", "coverage": 50, "desc": "Lingerie/revealing"},
    "PG17": {"label": "PG-17", "coverage": 35, "desc": "Suggestive/risque"},
    "18+": {"label": "18+", "coverage": 20, "desc": "Artistic/partial"},
    "19+": {"label": "19+", "coverage": 10, "desc": "Full artistic"},
    "20+": {"label": "20+", "coverage": 0, "desc": "Explicit"},
    "21+": {"label": "21+", "coverage": 0, "desc": "Unrestricted"}
}

# Historical Eras
HISTORICAL_ERAS = {
    "contemporary": {"label": "Contemporary (2000+)", "prefix": "modern fashion"},
    "modern": {"label": "Modern (1950-2000)", "prefix": "retro fashion"},
    "early_modern": {"label": "Early Modern (1900-1950)", "prefix": "vintage pin-up style"},
    "victorian": {"label": "Victorian (1800-1900)", "prefix": "victorian era fashion"},
    "baroque": {"label": "Baroque (1600-1800)", "prefix": "baroque elegant fashion"},
    "renaissance": {"label": "Renaissance (1400-1600)", "prefix": "renaissance classical"},
    "medieval": {"label": "Medieval (500-1400)", "prefix": "medieval period fashion"},
    "ancient": {"label": "Ancient (BC)", "prefix": "ancient classical greco-roman"}
}

# Cultural Styles  
CULTURAL_STYLES = {
    "global": {"label": "Global/Diverse", "prefix": "diverse multicultural"},
    "tribal": {"label": "Tribal/Indigenous", "prefix": "tribal indigenous aesthetic"},
    "western": {"label": "Western/Cowgirl", "prefix": "western cowgirl style"},
    "professional": {"label": "Professional/Corporate", "prefix": "professional business"},
    "luxury": {"label": "Luxury/Elite", "prefix": "luxury high fashion elegant"},
    "casual": {"label": "Casual/Everyday", "prefix": "casual everyday style"}
}

# Tag categories for selection
TAG_CATEGORIES = {
    "style": ["photorealistic", "artistic", "portrait", "fashion", "editorial", "glamour", "fine art"],
    "mood": ["elegant", "fierce", "serene", "confident", "mysterious", "playful", "sensual"],
    "lighting": ["natural light", "studio light", "golden hour", "dramatic", "soft", "rim light", "backlit"],
    "pose": ["standing", "sitting", "profile", "three-quarter", "dynamic", "relaxed", "powerful"],
    "setting": ["indoor", "outdoor", "studio", "nature", "urban", "beach", "forest"],
    "ethnicity": ["diverse", "asian", "european", "african", "latina", "middle eastern", "mixed"],
    "hair": ["long hair", "short hair", "curly", "straight", "braided", "flowing", "styled"],
    "features": ["detailed eyes", "full lips", "high cheekbones", "soft features", "sharp features"],
    "body": ["athletic", "slim", "curvy", "petite", "tall", "graceful", "toned"],
    "accessories": ["jewelry", "earrings", "necklace", "headpiece", "bracelet", "rings"]
}


class UltraDB:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()
        
    def _init(self):
        # Create tables if they don't exist (compatible with Pro schema)
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY, filename TEXT UNIQUE, prompt TEXT,
                negative_prompt TEXT, seed INTEGER, batch_id TEXT,
                rating REAL DEFAULT 0, is_gold_standard INTEGER DEFAULT 0,
                is_trainable INTEGER DEFAULT 0, marked_enhance INTEGER DEFAULT 0,
                tags TEXT, theme TEXT, content_rating TEXT DEFAULT 'PG',
                historical_era TEXT DEFAULT 'contemporary',
                cultural_style TEXT DEFAULT 'global',
                guardrail_status TEXT DEFAULT 'passed',
                created_at TEXT, rated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS prompt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT, negative TEXT, seed INTEGER, batch_id TEXT,
                content_rating TEXT, historical_era TEXT, cultural_style TEXT,
                theme TEXT, tags TEXT, llm_enhanced INTEGER DEFAULT 0, 
                validated INTEGER DEFAULT 1, created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT, pattern_value TEXT, weight REAL DEFAULT 1.0,
                occurrences INTEGER DEFAULT 1, avg_rating REAL DEFAULT 0,
                created_at TEXT, updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS guardrail_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT, violation_type TEXT, details TEXT,
                auto_corrected INTEGER DEFAULT 0, created_at TEXT
            );
        ''')
        # Add new columns to existing table if missing
        for col in ['content_rating TEXT DEFAULT "PG"', 'historical_era TEXT DEFAULT "contemporary"',
                    'cultural_style TEXT DEFAULT "global"', 'guardrail_status TEXT DEFAULT "passed"',
                    'is_trainable INTEGER DEFAULT 0', 'marked_enhance INTEGER DEFAULT 0']:
            try: self.conn.execute(f'ALTER TABLE images ADD COLUMN {col}')
            except: pass
        self.conn.commit()
        
    def scan(self):
        """Scan multiple directories for images"""
        # Multiple source directories
        source_dirs = [
            OUTPUT_DIR,  # G:\Github\ComfyUI\output
            Path(r"c:\Users\Admin\civitai\output\comfyui"),
            Path(r"c:\Users\Admin\civitai\output\pipeline"),
            Path(r"c:\Users\Admin\civitai\output\teepee_images"),
        ]
        
        all_imgs = []
        for src in source_dirs:
            if src.exists():
                # Scan root level and one level deep
                for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
                    all_imgs.extend(src.glob(ext))
                    all_imgs.extend(src.glob(f'*/{ext}'))
        
        # Dedupe by filename
        seen = set()
        imgs = []
        for img in all_imgs:
            if img.name not in seen:
                seen.add(img.name)
                imgs.append(img)
        
        new = 0
        for img in imgs:
            if not self.conn.execute('SELECT 1 FROM images WHERE filename=?', (img.name,)).fetchone():
                # Auto-detect theme from filename/path
                path_str = str(img).lower()
                if 'tribal' in path_str:
                    theme = 'tribal_warrior'
                elif 'western' in path_str or 'cowgirl' in path_str:
                    theme = 'western'
                elif 'anime' in path_str:
                    theme = 'anime'
                else:
                    theme = 'general'
                
                self.conn.execute('INSERT INTO images (id, filename, theme, created_at) VALUES (?,?,?,?)',
                    (f"img_{hash(img.name)%10**8}", img.name, theme, datetime.now().isoformat()))
                new += 1
        self.conn.commit()
        return {'total': len(imgs), 'new': new, 'sources': len([s for s in source_dirs if s.exists()])}
        
    def get_images(self, filter_type='all', limit=500):
        """Get images with filter - compatible with Pro schema"""
        # Use basic columns that exist in both schemas
        sql = 'SELECT id, filename, rating, theme FROM images'
        if filter_type == 'unrated': sql += ' WHERE rating = 0 OR rating IS NULL'
        elif filter_type == 'rated': sql += ' WHERE rating > 0'
        elif filter_type == 'high': sql += ' WHERE rating >= 7'
        elif filter_type == 'excellent': sql += ' WHERE rating >= 10'
        elif filter_type == 'batch': sql += ' WHERE rating >= 7'
        sql += f' ORDER BY created_at DESC LIMIT {limit}'
        
        results = []
        for r in self.conn.execute(sql).fetchall():
            img = dict(r)
            # Add defaults for new columns if missing
            img.setdefault('content_rating', 'PG')
            img.setdefault('historical_era', 'contemporary')
            img.setdefault('cultural_style', 'global')
            results.append(img)
        return results
        
    def rate(self, img_id, rating, content_rating='PG', era='contemporary', culture='global'):
        """Rate image with content rating, era, and culture"""
        rating = max(0, min(15, float(rating)))
        now = datetime.now().isoformat()
        is_trainable = 1 if rating >= 10 else 0
        
        # Try full update first, fallback to basic if columns missing
        try:
            self.conn.execute('''UPDATE images SET rating=?, content_rating=?, historical_era=?, 
                cultural_style=?, rated_at=?, is_trainable=? WHERE id=?''',
                (rating, content_rating, era, culture, now, is_trainable, img_id))
        except sqlite3.OperationalError:
            # Fallback: basic update for old schema
            self.conn.execute('UPDATE images SET rating=?, rated_at=? WHERE id=?',
                (rating, now, img_id))
        
        if rating >= 10:
            self._learn(img_id, rating, content_rating, era, culture)
        self.conn.commit()
        return {'id': img_id, 'rating': rating, 'content_rating': content_rating, 
                'era': era, 'culture': culture}
        
    def _learn(self, img_id, rating, content_rating='PG', era='contemporary', culture='global'):
        """Learn from high-rated images - themes, eras, cultures"""
        now = datetime.now().isoformat()
        
        # Learn theme
        img = self.conn.execute('SELECT theme FROM images WHERE id=?', (img_id,)).fetchone()
        if img and img['theme']:
            self._update_pattern('theme', img['theme'], rating, now)
            
        # Learn content rating preference
        self._update_pattern('content_rating', content_rating, rating, now)
        
        # Learn era preference
        self._update_pattern('era', era, rating, now)
        
        # Learn culture preference
        self._update_pattern('culture', culture, rating, now)
        
    def _update_pattern(self, ptype, value, rating, now):
        """Update or create a learned pattern"""
        existing = self.conn.execute(
            'SELECT id, occurrences, avg_rating FROM learned_patterns WHERE pattern_type=? AND pattern_value=?',
            (ptype, value)).fetchone()
        if existing:
            new_avg = ((existing['avg_rating'] * existing['occurrences']) + rating) / (existing['occurrences'] + 1)
            self.conn.execute('UPDATE learned_patterns SET occurrences=occurrences+1, avg_rating=? WHERE id=?',
                (new_avg, existing['id']))
        else:
            self.conn.execute('INSERT INTO learned_patterns (pattern_type, pattern_value, avg_rating, created_at) VALUES (?,?,?,?)',
                (ptype, value, rating, now))
                    
    def get_stats(self):
        t = self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]
        r = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
        h7 = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 7').fetchone()[0]
        e10 = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating >= 10').fetchone()[0]
        patterns = self.conn.execute('SELECT COUNT(*) FROM learned_patterns').fetchone()[0]
        return {'total': t, 'rated': r, 'unrated': t-r, 'high7': h7, 'excellent10': e10, 'patterns': patterns}
        
    def save_prompt(self, prompt, negative, seed, batch_id, content_rating, era, culture, tags, llm_enhanced=False, validated=True):
        self.conn.execute('''INSERT INTO prompt_history 
            (prompt, negative, seed, batch_id, content_rating, historical_era, cultural_style, tags, llm_enhanced, validated, created_at) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (prompt, negative, seed, batch_id, content_rating, era, culture, tags, 
             1 if llm_enhanced else 0, 1 if validated else 0, datetime.now().isoformat()))
        self.conn.commit()
        
    def log_violation(self, image_id, violation_type, details, auto_corrected=False):
        """Log guardrail violation"""
        self.conn.execute('INSERT INTO guardrail_violations (image_id, violation_type, details, auto_corrected, created_at) VALUES (?,?,?,?,?)',
            (image_id, violation_type, details, 1 if auto_corrected else 0, datetime.now().isoformat()))
        self.conn.commit()
        
    def get_top_patterns(self, ptype, limit=5):
        """Get top patterns by type"""
        return [dict(r) for r in self.conn.execute(
            'SELECT pattern_value, avg_rating, occurrences FROM learned_patterns WHERE pattern_type=? ORDER BY avg_rating DESC LIMIT ?',
            (ptype, limit)).fetchall()]
        
    def get_high_rated_for_batch(self, min_rating=7, limit=50):
        return [dict(r) for r in self.conn.execute(
            'SELECT id, filename, rating, theme, content_rating FROM images WHERE rating >= ? ORDER BY rating DESC LIMIT ?',
            (min_rating, limit)).fetchall()]


db = UltraDB()


def call_llm(prompt, system="You are an AI assistant helping create image generation prompts."):
    """Try LM Studio first, then Ollama"""
    # Try LM Studio
    try:
        r = requests.post(f"{LM_STUDIO_URL}/chat/completions", json={
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": 0.7, "max_tokens": 500
        }, timeout=30)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
    except: pass
    
    # Try Ollama
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "llama2", "prompt": f"{system}\n\nUser: {prompt}", "stream": False
        }, timeout=30)
        if r.status_code == 200:
            return r.json().get('response', '')
    except: pass
    
    return None


def enhance_prompt_with_llm(base_prompt, tags, content_rating):
    """Use LLM to enhance the prompt"""
    llm_prompt = f"""Enhance this image generation prompt with more detail and artistic direction.

Base prompt: {base_prompt}
Selected tags: {', '.join(tags)}
Content rating: {content_rating}

Create an enhanced, detailed prompt that:
1. Incorporates all selected tags naturally
2. Adds artistic and technical photography terms
3. Keeps within {content_rating} content guidelines
4. Is optimized for Stable Diffusion

Return ONLY the enhanced prompt, nothing else."""

    result = call_llm(llm_prompt)
    if result:
        return result.strip()
    return base_prompt


def build_prompt(tags, content_rating, era='contemporary', culture='global', theme=None):
    """Build prompt from tags, rating, era, and culture with guardrails"""
    parts = []
    
    # Add era prefix
    if era in HISTORICAL_ERAS:
        parts.append(HISTORICAL_ERAS[era]['prefix'])
        
    # Add culture prefix
    if culture in CULTURAL_STYLES:
        parts.append(CULTURAL_STYLES[culture]['prefix'])
    
    if theme: parts.append(theme)
    parts.extend(tags)
    parts.extend(random.sample(QUALITY, 4))
    parts.extend(random.sample(LIGHTING, 2))
    parts.extend(random.sample(CAMERA, 2))
    
    prompt = ', '.join(parts)
    
    # Validate and sanitize if validator available
    if VALIDATOR_AVAILABLE:
        result = validate_and_sanitize(prompt, content_rating)
        if not result['valid']:
            prompt = result['sanitized_prompt']
            
    return prompt


def get_guardrail_negative(content_rating):
    """Get negative prompt with guardrails for content rating"""
    base_neg = NEGATIVE
    
    if VALIDATOR_AVAILABLE:
        validator = get_validator()
        rating_enum = ContentRating.from_string(content_rating)
        guardrail_neg = validator.get_guardrail_negative(rating_enum)
        return f"{base_neg}, {guardrail_neg}"
        
    # Basic guardrails if validator not available
    forbidden = "child, minor, underage, teen, kid, loli, shota"
    return f"{base_neg}, {forbidden}"


HTML = '''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8"><title>Rating Studio Ultra</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', sans-serif; background: #0a0a0f; color: #e0e0e0; height: 100vh; overflow: hidden; }

.container { display: flex; height: 100vh; }

/* COMPACT LEFT PANEL */
.left { width: 280px; background: #12121a; border-right: 1px solid #333; padding: 10px; display: flex; flex-direction: column; gap: 8px; }

.logo { font-size: 1.1em; color: #00d4ff; font-weight: bold; padding: 5px 0; border-bottom: 1px solid #333; display: flex; align-items: center; gap: 8px; }
.logo .llm { font-size: 0.6em; background: #00ff88; color: #000; padding: 2px 6px; border-radius: 8px; }

/* Compact stats */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; }
.stat { background: #1a1a2e; padding: 6px 4px; border-radius: 4px; text-align: center; }
.stat-val { font-size: 1.1em; font-weight: bold; color: #00d4ff; }
.stat-lbl { font-size: 0.6em; color: #888; }

/* Compact controls */
.ctrl-row { display: flex; gap: 6px; align-items: center; }
.ctrl-lbl { font-size: 0.75em; color: #888; min-width: 50px; }
.grid-input { width: 60px; background: #1a1a2e; border: 1px solid #333; color: #fff; padding: 4px 8px; border-radius: 4px; text-align: center; }

/* Filter chips */
.filters { display: flex; flex-wrap: wrap; gap: 4px; }
.chip { padding: 4px 8px; background: #1a1a2e; border: 1px solid #333; border-radius: 12px; font-size: 0.7em; cursor: pointer; }
.chip:hover { background: #2a2a4e; }
.chip.active { background: #00d4ff; color: #000; border-color: #00d4ff; }

/* Compact buttons */
.actions { display: flex; flex-direction: column; gap: 4px; }
.btn { padding: 8px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.75em; display: flex; align-items: center; gap: 6px; transition: all 0.15s; }
.btn:hover { opacity: 0.85; transform: translateX(2px); }
.btn-gen { background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: #fff; }
.btn-llm { background: linear-gradient(135deg, #00b894, #00cec9); color: #000; }
.btn-analyze { background: linear-gradient(135deg, #fdcb6e, #f39c12); color: #000; }
.btn-sm { background: #2a2a3e; color: #ccc; }

/* Content rating dropdown */
.rating-select { background: #1a1a2e; border: 1px solid #333; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.75em; }

/* Divider */
.divider { height: 1px; background: #333; margin: 4px 0; }

/* MAIN PANEL */
.main { flex: 1; display: flex; flex-direction: column; }
.main-header { padding: 8px 12px; background: #12121a; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; font-size: 0.85em; }

.grid-wrap { flex: 1; overflow-y: auto; padding: 8px; }
.grid { display: grid; gap: 6px; }
.card { position: relative; aspect-ratio: 3/4; border-radius: 6px; overflow: hidden; cursor: pointer; border: 2px solid transparent; }
.card:hover { border-color: #00d4ff; }
.card.selected { border-color: #00ff88; box-shadow: 0 0 15px rgba(0,255,136,0.3); }
.card img { width: 100%; height: 100%; object-fit: cover; }
.card-info { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(transparent, rgba(0,0,0,0.9)); padding: 20px 6px 6px; }
.card-rating { font-weight: bold; font-size: 0.9em; }
.card-rating.high { color: #00ff88; }
.card-rating.med { color: #fdcb6e; }
.card-rating.low { color: #888; }
.card-content { font-size: 0.6em; color: #aaa; }

/* PREVIEW MODAL */
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.95); display: none; z-index: 100; }
.modal.active { display: flex; }
.modal-content { flex: 1; display: flex; }
.modal-img { flex: 1; display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal-img img { max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px; }
.modal-side { width: 320px; background: #12121a; padding: 15px; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.modal-close { position: absolute; top: 10px; right: 10px; background: #ff4757; border: none; color: #fff; padding: 8px 16px; border-radius: 4px; cursor: pointer; }

/* Rating controls in modal */
.rate-section { background: #1a1a2e; padding: 12px; border-radius: 6px; }
.rate-section h4 { font-size: 0.85em; color: #00d4ff; margin-bottom: 8px; }
.rate-slider { width: 100%; margin: 8px 0; }
.rate-btns { display: flex; flex-wrap: wrap; gap: 4px; }
.rate-btn { padding: 6px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.75em; font-weight: bold; }
.rate-btn:hover { opacity: 0.8; }

/* Content rating in modal */
.content-section { background: #1a1a2e; padding: 12px; border-radius: 6px; }
.content-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 4px; margin-top: 8px; }
.content-opt { padding: 6px; background: #2a2a3e; border: 1px solid #333; border-radius: 4px; cursor: pointer; text-align: center; font-size: 0.7em; }
.content-opt:hover { border-color: #00d4ff; }
.content-opt.active { background: #00d4ff; color: #000; border-color: #00d4ff; }

/* AI WIZARD MODAL */
.wizard { position: fixed; inset: 0; background: rgba(0,0,0,0.95); display: none; z-index: 200; align-items: center; justify-content: center; }
.wizard.active { display: flex; }
.wizard-box { background: #12121a; border-radius: 12px; width: 90%; max-width: 800px; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }
.wizard-header { padding: 15px 20px; background: linear-gradient(135deg, #1a1a2e, #16213e); border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; }
.wizard-header h2 { font-size: 1.2em; color: #00d4ff; }
.wizard-body { flex: 1; overflow-y: auto; padding: 20px; }
.wizard-footer { padding: 15px 20px; background: #1a1a2e; border-top: 1px solid #333; display: flex; justify-content: space-between; }

/* Wizard steps */
.step { display: none; }
.step.active { display: block; }
.step h3 { font-size: 1em; color: #00d4ff; margin-bottom: 15px; }
.step p { font-size: 0.85em; color: #888; margin-bottom: 15px; }

/* Tag selection */
.tag-category { margin-bottom: 15px; }
.tag-category h4 { font-size: 0.85em; color: #888; margin-bottom: 8px; text-transform: uppercase; }
.tag-options { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-opt { padding: 6px 12px; background: #2a2a3e; border: 1px solid #444; border-radius: 16px; cursor: pointer; font-size: 0.8em; }
.tag-opt:hover { border-color: #00d4ff; }
.tag-opt.selected { background: #00d4ff; color: #000; border-color: #00d4ff; }

/* Question input */
.question { margin-bottom: 15px; }
.question label { display: block; font-size: 0.85em; color: #ccc; margin-bottom: 6px; }
.question input, .question select { width: 100%; padding: 10px; background: #2a2a3e; border: 1px solid #444; color: #fff; border-radius: 6px; font-size: 0.9em; }
.question input:focus { border-color: #00d4ff; outline: none; }

/* Image selection grid */
.img-select-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; max-height: 300px; overflow-y: auto; }
.img-select { aspect-ratio: 3/4; border-radius: 6px; overflow: hidden; cursor: pointer; border: 2px solid transparent; }
.img-select:hover { border-color: #00d4ff; }
.img-select.selected { border-color: #00ff88; }
.img-select img { width: 100%; height: 100%; object-fit: cover; }

/* Progress */
.tag-count { font-size: 0.9em; color: #00d4ff; margin-top: 10px; }
.progress-bar { height: 4px; background: #333; border-radius: 2px; margin-top: 8px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #00ff88); border-radius: 2px; transition: width 0.3s; }

/* Generated prompt display */
.prompt-result { background: #1a1a2e; padding: 15px; border-radius: 8px; margin-top: 15px; }
.prompt-result h4 { color: #00d4ff; margin-bottom: 10px; }
.prompt-text { background: #2a2a3e; padding: 12px; border-radius: 6px; font-size: 0.85em; line-height: 1.5; max-height: 200px; overflow-y: auto; }

/* Toast */
.toast { position: fixed; bottom: 20px; right: 20px; background: #00d4ff; color: #000; padding: 12px 20px; border-radius: 6px; display: none; z-index: 300; font-weight: bold; }
.toast.show { display: block; animation: fadeInOut 2s; }
@keyframes fadeInOut { 0%,100% { opacity: 0; } 10%,90% { opacity: 1; } }
</style>
</head>
<body>

<div class="container">
  <!-- COMPACT LEFT PANEL -->
  <div class="left">
    <div class="logo">⚡ Rating Studio <span class="llm">LLM</span></div>
    
    <div class="stats">
      <div class="stat"><div class="stat-val" id="s-total">0</div><div class="stat-lbl">Total</div></div>
      <div class="stat"><div class="stat-val" id="s-unrated">0</div><div class="stat-lbl">Unrated</div></div>
      <div class="stat"><div class="stat-val" id="s-high">0</div><div class="stat-lbl">7+</div></div>
      <div class="stat"><div class="stat-val" id="s-exc">0</div><div class="stat-lbl">10+</div></div>
    </div>
    
    <div class="ctrl-row">
      <span class="ctrl-lbl">Grid:</span>
      <input type="number" class="grid-input" id="grid-size" value="24" min="4" max="60" step="4">
      <select class="rating-select" id="content-filter">
        <option value="all">All Ratings</option>
        <option value="PG">PG Only</option>
        <option value="18+">18+ Only</option>
      </select>
    </div>
    
    <div class="filters">
      <span class="chip active" data-f="all">All</span>
      <span class="chip" data-f="unrated">Unrated</span>
      <span class="chip" data-f="high">7+</span>
      <span class="chip" data-f="excellent">10+</span>
    </div>
    
    <div class="divider"></div>
    
    <div class="actions">
      <button class="btn btn-llm" onclick="openWizard()">🧠 AI Prompt Builder</button>
      <button class="btn btn-gen" onclick="genFromHigh()">⭐ Generate from 7+</button>
      <button class="btn btn-gen" onclick="genBatch(10)">📦 Quick Batch (10)</button>
      <button class="btn btn-analyze" onclick="showPatterns()">📊 View Patterns</button>
      <button class="btn btn-sm" onclick="scanImages()">🔄 Scan</button>
    </div>
    
    <div class="divider"></div>
    
    <div style="font-size:0.7em;color:#666">
      <div>LLM: <span id="llm-status">Checking...</span></div>
      <div>Patterns: <span id="pattern-count">0</span></div>
    </div>
  </div>
  
  <!-- MAIN PANEL -->
  <div class="main">
    <div class="main-header">
      <span>Showing <b id="img-count">0</b> images</span>
      <span id="selected-count" style="color:#00ff88"></span>
    </div>
    <div class="grid-wrap">
      <div class="grid" id="grid"></div>
    </div>
  </div>
</div>

<!-- PREVIEW MODAL -->
<div class="modal" id="preview-modal">
  <button class="modal-close" onclick="closePreview()">✕</button>
  <div class="modal-content">
    <div class="modal-img"><img id="preview-img" src=""></div>
    <div class="modal-side">
      <h3 id="preview-name">filename.png</h3>
      
      <div class="rate-section">
        <h4>Quality Rating (0-15)</h4>
        <input type="range" class="rate-slider" id="rate-slider" min="0" max="15" value="0">
        <div style="display:flex;justify-content:space-between;font-size:0.8em"><span>Poor</span><span id="rate-val">0</span><span>Perfect</span></div>
        <div class="rate-btns">
          <button class="rate-btn" style="background:#ff6b6b;color:#fff" onclick="qRate(0)">0</button>
          <button class="rate-btn" style="background:#ffa502" onclick="qRate(5)">5</button>
          <button class="rate-btn" style="background:#7bed9f" onclick="qRate(7)">7</button>
          <button class="rate-btn" style="background:#00d4ff;color:#000" onclick="qRate(10)">10</button>
          <button class="rate-btn" style="background:#6c5ce7;color:#fff" onclick="qRate(12)">12</button>
          <button class="rate-btn" style="background:#e84393;color:#fff" onclick="qRate(15)">15⭐</button>
        </div>
      </div>
      
      <div class="content-section">
        <h4>Content Rating</h4>
        <div class="content-grid" id="content-opts"></div>
      </div>
      
      <div class="content-section">
        <h4>Historical Era</h4>
        <select class="rating-select" id="era-select" style="width:100%;padding:8px">
          <option value="contemporary">Contemporary (2000+)</option>
          <option value="modern">Modern (1950-2000)</option>
          <option value="early_modern">Early Modern (1900-1950)</option>
          <option value="victorian">Victorian (1800-1900)</option>
          <option value="baroque">Baroque (1600-1800)</option>
          <option value="renaissance">Renaissance (1400-1600)</option>
          <option value="medieval">Medieval (500-1400)</option>
          <option value="ancient">Ancient (BC)</option>
        </select>
      </div>
      
      <div class="content-section">
        <h4>Cultural Style</h4>
        <select class="rating-select" id="culture-select" style="width:100%;padding:8px">
          <option value="global">Global/Diverse</option>
          <option value="tribal">Tribal/Indigenous</option>
          <option value="western">Western/Cowgirl</option>
          <option value="professional">Professional/Corporate</option>
          <option value="luxury">Luxury/Elite</option>
          <option value="casual">Casual/Everyday</option>
        </select>
      </div>
      
      <div style="display:flex;gap:8px;margin-top:auto">
        <button class="btn btn-sm" style="flex:1" onclick="prevImg()">◀ Prev</button>
        <button class="btn btn-sm" style="flex:1" onclick="nextImg()">Next ▶</button>
      </div>
    </div>
  </div>
</div>

<!-- AI WIZARD -->
<div class="wizard" id="wizard">
  <div class="wizard-box">
    <div class="wizard-header">
      <h2>🧠 AI Prompt Builder</h2>
      <button class="btn btn-sm" onclick="closeWizard()">✕ Close</button>
    </div>
    <div class="wizard-body">
      <!-- Step 1: Select Base Images -->
      <div class="step active" id="step1">
        <h3>Step 1: Select Reference Images (10-50)</h3>
        <p>Select your favorite images rated 7+ to use as inspiration</p>
        <div class="img-select-grid" id="ref-images"></div>
        <div class="tag-count">Selected: <span id="ref-count">0</span>/50 images</div>
        <div class="progress-bar"><div class="progress-fill" id="ref-progress" style="width:0%"></div></div>
      </div>
      
      <!-- Step 2: Content Rating, Era, Culture -->
      <div class="step" id="step2">
        <h3>Step 2: Select Content Rating, Era & Culture</h3>
        <p>Choose content level and style for your western story family characters</p>
        
        <div style="margin-bottom:20px">
          <h4 style="color:#00d4ff;margin-bottom:10px">Content Rating (PG to 21+)</h4>
          <div class="content-grid" id="wizard-content" style="grid-template-columns:repeat(5,1fr)"></div>
        </div>
        
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px">
          <div>
            <h4 style="color:#00d4ff;margin-bottom:10px">Historical Era</h4>
            <select class="rating-select" id="wizard-era" style="width:100%;padding:10px;font-size:0.9em">
              <option value="contemporary">Contemporary (2000+)</option>
              <option value="modern">Modern (1950-2000)</option>
              <option value="early_modern">Early Modern (1900-1950)</option>
              <option value="victorian">Victorian (1800-1900)</option>
              <option value="baroque">Baroque (1600-1800)</option>
              <option value="renaissance">Renaissance (1400-1600)</option>
              <option value="medieval">Medieval (500-1400)</option>
              <option value="ancient">Ancient (BC)</option>
            </select>
          </div>
          <div>
            <h4 style="color:#00d4ff;margin-bottom:10px">Cultural Style</h4>
            <select class="rating-select" id="wizard-culture" style="width:100%;padding:10px;font-size:0.9em">
              <option value="global">Global/Diverse</option>
              <option value="tribal">Tribal/Indigenous</option>
              <option value="western" selected>Western/Cowgirl</option>
              <option value="professional">Professional/Corporate</option>
              <option value="luxury">Luxury/Elite</option>
              <option value="casual">Casual/Everyday</option>
            </select>
          </div>
        </div>
        
        <div style="margin-top:15px;padding:12px;background:#1a1a2e;border-radius:6px">
          <div style="color:#888;font-size:0.8em">💡 For Western Story Builder: Select "Western/Cowgirl" culture with appropriate era and family-friendly content rating (PG-PG17 for families)</div>
        </div>
      </div>
      
      <!-- Step 3: Select Tags (30+ required) -->
      <div class="step" id="step3">
        <h3>Step 3: Select Tags (minimum 30)</h3>
        <p>Choose tags that describe your desired images</p>
        <div id="tag-categories"></div>
        <div class="tag-count">Selected: <span id="tag-count">0</span>/30+ tags</div>
        <div class="progress-bar"><div class="progress-fill" id="tag-progress" style="width:0%"></div></div>
      </div>
      
      <!-- Step 4: Answer Questions -->
      <div class="step" id="step4">
        <h3>Step 4: Answer Questions for Detail</h3>
        <div id="questions"></div>
      </div>
      
      <!-- Step 5: Generate -->
      <div class="step" id="step5">
        <h3>Step 5: Review & Generate</h3>
        <div class="prompt-result">
          <h4>Generated Prompt</h4>
          <div class="prompt-text" id="final-prompt">Loading...</div>
        </div>
        <div style="margin-top:15px">
          <label style="font-size:0.85em">Number of images to generate:</label>
          <input type="number" id="gen-count" value="20" min="1" max="100" style="width:80px;padding:8px;background:#2a2a3e;border:1px solid #444;color:#fff;border-radius:4px">
        </div>
      </div>
    </div>
    <div class="wizard-footer">
      <button class="btn btn-sm" id="prev-step" onclick="prevStep()" style="display:none">← Back</button>
      <button class="btn btn-llm" id="next-step" onclick="nextStep()">Next →</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let images = [], currentIdx = -1, currentFilter = 'all', gridSize = 24;
let selectedRefs = [], selectedTags = [], wizardStep = 1, selectedContent = 'PG';
const QUESTIONS = [
  {q: "What is the primary mood/feeling?", opts: ["Elegant", "Fierce", "Serene", "Confident", "Mysterious", "Playful"]},
  {q: "Preferred lighting style?", opts: ["Natural daylight", "Golden hour", "Studio", "Dramatic", "Soft diffused"]},
  {q: "Setting/Environment?", opts: ["Studio backdrop", "Nature/Outdoor", "Urban", "Beach", "Indoor elegant"]},
  {q: "Camera perspective?", opts: ["Close-up portrait", "Upper body", "Full body", "Three-quarter view"]},
  {q: "Color palette?", opts: ["Warm tones", "Cool tones", "Neutral", "Vibrant", "Moody/Dark"]},
  {q: "Level of detail?", opts: ["Hyper-realistic", "Artistic/Stylized", "Soft focus", "Sharp throughout"]},
  {q: "Expression?", opts: ["Neutral", "Smiling", "Intense gaze", "Looking away", "Contemplative"]},
  {q: "Hair style preference?", opts: ["Flowing/Long", "Styled/Formal", "Natural/Casual", "Braided", "Short"]}
];
let answers = {};

const CONTENT_RATINGS = ${json.dumps(CONTENT_RATINGS)};
const TAG_CATS = ${json.dumps(TAG_CATEGORIES)};

document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadImages();
  checkLLM();
  setupContentOpts();
  
  document.getElementById('grid-size').addEventListener('change', e => {
    gridSize = Math.max(4, Math.min(60, parseInt(e.target.value) || 24));
    e.target.value = gridSize;
    updateGrid();
  });
  
  document.getElementById('rate-slider').addEventListener('input', e => {
    document.getElementById('rate-val').textContent = e.target.value;
  });
  document.getElementById('rate-slider').addEventListener('change', e => {
    if (currentIdx >= 0) saveRating(images[currentIdx].id, parseInt(e.target.value));
  });
  
  document.querySelectorAll('.chip').forEach(c => {
    c.addEventListener('click', () => {
      document.querySelectorAll('.chip').forEach(x => x.classList.remove('active'));
      c.classList.add('active');
      currentFilter = c.dataset.f;
      loadImages();
    });
  });
  
  document.addEventListener('keydown', e => {
    if (document.getElementById('preview-modal').classList.contains('active')) {
      if (e.key === 'ArrowLeft') prevImg();
      else if (e.key === 'ArrowRight') nextImg();
      else if (e.key === 'Escape') closePreview();
      else if (e.key >= '0' && e.key <= '9') qRate(parseInt(e.key));
    }
  });
});

async function loadStats() {
  const s = await (await fetch('/api/stats')).json();
  document.getElementById('s-total').textContent = s.total;
  document.getElementById('s-unrated').textContent = s.unrated;
  document.getElementById('s-high').textContent = s.high7;
  document.getElementById('s-exc').textContent = s.excellent10;
  document.getElementById('pattern-count').textContent = s.patterns;
}

async function loadImages() {
  images = await (await fetch(`/api/images?filter=${currentFilter}&limit=500`)).json();
  document.getElementById('img-count').textContent = images.length;
  updateGrid();
}

function updateGrid() {
  const g = document.getElementById('grid');
  const cols = Math.ceil(Math.sqrt(gridSize * 1.5));
  g.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  g.innerHTML = images.slice(0, gridSize).map((img, i) => `
    <div class="card" onclick="openPreview(${i})">
      <img src="/image/${img.filename}" loading="lazy">
      <div class="card-info">
        <span class="card-rating ${img.rating >= 10 ? 'high' : img.rating >= 7 ? 'med' : 'low'}">${img.rating || '-'}</span>
        <span class="card-content">${img.content_rating || 'PG'}</span>
      </div>
    </div>
  `).join('');
}

function setupContentOpts() {
  const html = Object.entries(CONTENT_RATINGS).map(([k,v]) => 
    `<div class="content-opt" data-r="${k}" onclick="setContent('${k}')">${v.label}</div>`
  ).join('');
  document.getElementById('content-opts').innerHTML = html;
}

function setContent(r) {
  selectedContent = r;
  document.querySelectorAll('#content-opts .content-opt').forEach(o => {
    o.classList.toggle('active', o.dataset.r === r);
  });
}

function openPreview(idx) {
  currentIdx = idx;
  const img = images[idx];
  document.getElementById('preview-modal').classList.add('active');
  document.getElementById('preview-img').src = `/image/${img.filename}`;
  document.getElementById('preview-name').textContent = img.filename;
  document.getElementById('rate-slider').value = img.rating || 0;
  document.getElementById('rate-val').textContent = img.rating || 0;
  setContent(img.content_rating || 'PG');
  document.getElementById('era-select').value = img.historical_era || 'contemporary';
  document.getElementById('culture-select').value = img.cultural_style || 'global';
}

function closePreview() {
  document.getElementById('preview-modal').classList.remove('active');
}

function prevImg() { if (currentIdx > 0) openPreview(currentIdx - 1); }
function nextImg() { if (currentIdx < images.length - 1) openPreview(currentIdx + 1); }

function qRate(r) {
  document.getElementById('rate-slider').value = r;
  document.getElementById('rate-val').textContent = r;
  if (currentIdx >= 0) saveRating(images[currentIdx].id, r);
}

async function saveRating(id, rating) {
  const era = document.getElementById('era-select').value;
  const culture = document.getElementById('culture-select').value;
  await fetch('/api/rate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id, rating, content_rating: selectedContent, era, culture})
  });
  images[currentIdx].rating = rating;
  images[currentIdx].content_rating = selectedContent;
  images[currentIdx].historical_era = era;
  images[currentIdx].cultural_style = culture;
  updateGrid();
  loadStats();
  toast(`Saved: ${rating}/15 (${selectedContent}) - ${culture}`);
}

async function scanImages() {
  const r = await (await fetch('/api/scan')).json();
  toast(`Scanned: ${r.new} new`);
  loadImages();
  loadStats();
}

async function genFromHigh() {
  const era = document.getElementById('era-select')?.value || 'contemporary';
  const culture = document.getElementById('culture-select')?.value || 'western';
  const r = await fetch('/api/generate-from-high', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({count:20, content_rating: selectedContent, era, culture})
  });
  const d = await r.json();
  toast(`Queued ${d.queued} from 7+ (${culture})`);
}

async function genBatch(n) {
  const era = document.getElementById('era-select')?.value || 'contemporary';
  const culture = document.getElementById('culture-select')?.value || 'western';
  const r = await fetch('/api/generate-batch', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({count:n, content_rating: selectedContent, era, culture})
  });
  const d = await r.json();
  toast(`Queued ${d.queued} (${culture})`);
}

async function showPatterns() {
  const p = await (await fetch('/api/patterns')).json();
  alert('Learned Patterns:\\n' + p.map(x => `${x.pattern_value}: ${x.avg_rating.toFixed(1)} (${x.occurrences}x)`).join('\\n'));
}

async function checkLLM() {
  const r = await fetch('/api/llm-status');
  const d = await r.json();
  document.getElementById('llm-status').textContent = d.available ? '✅ Connected' : '❌ Offline';
  document.getElementById('llm-status').style.color = d.available ? '#00ff88' : '#ff6b6b';
}

// WIZARD
function openWizard() {
  document.getElementById('wizard').classList.add('active');
  wizardStep = 1;
  selectedRefs = [];
  selectedTags = [];
  answers = {};
  showStep(1);
  loadRefImages();
}

function closeWizard() {
  document.getElementById('wizard').classList.remove('active');
}

async function loadRefImages() {
  const imgs = await (await fetch('/api/images?filter=high&limit=50')).json();
  document.getElementById('ref-images').innerHTML = imgs.map(img => `
    <div class="img-select" data-id="${img.id}" onclick="toggleRef('${img.id}', this)">
      <img src="/image/${img.filename}" loading="lazy">
    </div>
  `).join('');
}

function toggleRef(id, el) {
  if (selectedRefs.includes(id)) {
    selectedRefs = selectedRefs.filter(x => x !== id);
    el.classList.remove('selected');
  } else if (selectedRefs.length < 50) {
    selectedRefs.push(id);
    el.classList.add('selected');
  }
  document.getElementById('ref-count').textContent = selectedRefs.length;
  document.getElementById('ref-progress').style.width = Math.min(100, selectedRefs.length * 2) + '%';
}

function showStep(n) {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  document.getElementById(`step${n}`).classList.add('active');
  document.getElementById('prev-step').style.display = n > 1 ? 'block' : 'none';
  document.getElementById('next-step').textContent = n === 5 ? '🚀 Generate!' : 'Next →';
  
  if (n === 2) setupWizardContent();
  if (n === 3) setupTags();
  if (n === 4) setupQuestions();
  if (n === 5) generateFinalPrompt();
}

function setupWizardContent() {
  document.getElementById('wizard-content').innerHTML = Object.entries(CONTENT_RATINGS).map(([k,v]) =>
    `<div class="content-opt ${k===selectedContent?'active':''}" onclick="selectWizardContent('${k}', this)">${v.label}<br><small>${v.desc}</small></div>`
  ).join('');
}

function selectWizardContent(r, el) {
  selectedContent = r;
  document.querySelectorAll('#wizard-content .content-opt').forEach(o => o.classList.remove('active'));
  el.classList.add('active');
}

function setupTags() {
  let html = '';
  for (const [cat, tags] of Object.entries(TAG_CATS)) {
    html += `<div class="tag-category"><h4>${cat}</h4><div class="tag-options">`;
    html += tags.map(t => `<span class="tag-opt ${selectedTags.includes(t)?'selected':''}" onclick="toggleTag('${t}', this)">${t}</span>`).join('');
    html += '</div></div>';
  }
  document.getElementById('tag-categories').innerHTML = html;
  updateTagCount();
}

function toggleTag(t, el) {
  if (selectedTags.includes(t)) {
    selectedTags = selectedTags.filter(x => x !== t);
    el.classList.remove('selected');
  } else {
    selectedTags.push(t);
    el.classList.add('selected');
  }
  updateTagCount();
}

function updateTagCount() {
  document.getElementById('tag-count').textContent = selectedTags.length;
  document.getElementById('tag-progress').style.width = Math.min(100, selectedTags.length * 100 / 30) + '%';
}

function setupQuestions() {
  document.getElementById('questions').innerHTML = QUESTIONS.map((q, i) => `
    <div class="question">
      <label>${i+1}. ${q.q}</label>
      <select onchange="answers[${i}]=this.value">
        <option value="">Select...</option>
        ${q.opts.map(o => `<option value="${o}">${o}</option>`).join('')}
      </select>
    </div>
  `).join('');
}

async function generateFinalPrompt() {
  const era = document.getElementById('wizard-era')?.value || 'contemporary';
  const culture = document.getElementById('wizard-culture')?.value || 'western';
  const r = await fetch('/api/build-prompt', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      ref_images: selectedRefs,
      tags: selectedTags,
      content_rating: selectedContent,
      era: era,
      culture: culture,
      answers: answers
    })
  });
  const d = await r.json();
  document.getElementById('final-prompt').textContent = d.prompt;
}

function prevStep() {
  if (wizardStep > 1) {
    wizardStep--;
    showStep(wizardStep);
  }
}

async function nextStep() {
  if (wizardStep === 1 && selectedRefs.length < 10) {
    toast('Select at least 10 reference images');
    return;
  }
  if (wizardStep === 3 && selectedTags.length < 30) {
    toast('Select at least 30 tags');
    return;
  }
  if (wizardStep === 5) {
    // Generate!
    const count = parseInt(document.getElementById('gen-count').value) || 20;
    const prompt = document.getElementById('final-prompt').textContent;
    const era = document.getElementById('wizard-era')?.value || 'contemporary';
    const culture = document.getElementById('wizard-culture')?.value || 'western';
    const r = await fetch('/api/generate-custom', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt, count, content_rating: selectedContent, era, culture, tags: selectedTags})
    });
    const d = await r.json();
    toast(`Queued ${d.queued} ${culture} images (${selectedContent})!`);
    closeWizard();
    return;
  }
  wizardStep++;
  showStep(wizardStep);
}

function toast(m) {
  const t = document.getElementById('toast');
  t.textContent = m;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}
</script>
</body></html>'''


class UltraAPI(BaseHTTPRequestHandler):
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
            self._json(db.scan())
        elif path == '/api/patterns':
            patterns = [dict(r) for r in db.conn.execute('SELECT * FROM learned_patterns ORDER BY avg_rating DESC LIMIT 20').fetchall()]
            self._json(patterns)
        elif path == '/api/llm-status':
            available = call_llm("test", "Reply with OK") is not None
            self._json({'available': available})
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
            
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/rate':
            # Rate with content rating, era, and culture
            self._json(db.rate(
                data['id'], data['rating'], 
                data.get('content_rating', 'PG'),
                data.get('era', 'contemporary'),
                data.get('culture', 'global')
            ))
            
        elif path == '/api/generate-from-high':
            count = int(data.get('count', 20))
            era = data.get('era', 'contemporary')
            culture = data.get('culture', 'global')
            content = data.get('content_rating', 'PG')
            queued = self._gen_from_high(count, content, era, culture)
            self._json({'queued': queued})
            
        elif path == '/api/generate-batch':
            count = int(data.get('count', 10))
            era = data.get('era', 'contemporary')
            culture = data.get('culture', 'global')
            content = data.get('content_rating', 'PG')
            queued = self._gen_batch(count, content, era, culture)
            self._json({'queued': queued})
            
        elif path == '/api/build-prompt':
            tags = data.get('tags', [])
            content = data.get('content_rating', 'PG')
            era = data.get('era', 'contemporary')
            culture = data.get('culture', 'global')
            answers = data.get('answers', {})
            
            # Build base prompt with era and culture
            base = build_prompt(tags, content, era, culture)
            
            # Add answers
            ans_text = ', '.join([str(v) for v in answers.values() if v])
            if ans_text:
                base = f"{base}, {ans_text}"
            
            # Try LLM enhancement
            enhanced = enhance_prompt_with_llm(base, tags, content)
            
            self._json({'prompt': enhanced or base, 'llm_enhanced': enhanced is not None})
            
        elif path == '/api/generate-custom':
            prompt = data.get('prompt', '')
            count = int(data.get('count', 20))
            content = data.get('content_rating', 'PG')
            era = data.get('era', 'contemporary')
            culture = data.get('culture', 'global')
            tags = data.get('tags', [])
            queued = self._gen_custom(prompt, count, content, era, culture, tags)
            self._json({'queued': queued})
            
        elif path == '/api/validate-prompt':
            # Validate prompt against content rating
            prompt = data.get('prompt', '')
            content = data.get('content_rating', 'PG')
            if VALIDATOR_AVAILABLE:
                result = validate_and_sanitize(prompt, content)
                self._json(result)
            else:
                self._json({'valid': True, 'prompt': prompt, 'message': 'Validator not available'})
            
        else:
            self._json({'error': 'not found'}, 404)
            
    def _queue(self, prompt, seed, filename, content_rating='PG'):
        """Queue generation with guardrail-enhanced negative prompt"""
        negative = get_guardrail_negative(content_rating)
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
            
    def _gen_from_high(self, count, content='PG', era='contemporary', culture='global'):
        """Generate from 7+ rated images with era and culture"""
        high = db.get_high_rated_for_batch(7, 50)
        if not high: return 0
        
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        batch_id = f"high7_{ts}"
        negative = get_guardrail_negative(content)
        queued = 0
        
        for i in range(count):
            ref = random.choice(high)
            ref_content = ref.get('content_rating', content)
            prompt = build_prompt([], ref_content, era, culture, ref.get('theme'))
            seed = random.randint(1, 2**31)
            filename = f"from7plus_{ts}_{i+1:03d}"
            if self._queue(prompt, seed, filename, ref_content):
                db.save_prompt(prompt, negative, seed, batch_id, ref_content, era, culture, '', False)
                queued += 1
        return queued
        
    def _gen_batch(self, count, content='PG', era='contemporary', culture='global'):
        """Generate batch with era, culture, and content rating"""
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        batch_id = f"batch_{ts}"
        negative = get_guardrail_negative(content)
        queued = 0
        for i in range(count):
            prompt = build_prompt(random.sample(QUALITY, 4), content, era, culture)
            seed = random.randint(1, 2**31)
            filename = f"batch_{ts}_{i+1:03d}"
            if self._queue(prompt, seed, filename, content):
                db.save_prompt(prompt, negative, seed, batch_id, content, era, culture, '', False)
                queued += 1
        return queued
        
    def _gen_custom(self, prompt, count, content, era, culture, tags):
        """Generate custom with full options and guardrails"""
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        batch_id = f"custom_{ts}"
        negative = get_guardrail_negative(content)
        queued = 0
        for i in range(count):
            seed = random.randint(1, 2**31)
            filename = f"custom_{ts}_{i+1:03d}"
            if self._queue(prompt, seed, filename, content):
                db.save_prompt(prompt, negative, seed, batch_id, content, era, culture, ','.join(tags), True)
                queued += 1
        return queued
            
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  RATING STUDIO ULTRA + CONTENT RATING SYSTEM")
    print("  Real-world fashion | PG to 21+ | Guardrails")
    print("=" * 60)
    
    db.scan()
    stats = db.get_stats()
    
    print(f"\nImages: {stats['total']} total | {stats['high7']} rated 7+ | {stats['excellent10']} rated 10+")
    print(f"Patterns learned: {stats['patterns']}")
    
    # Check LLM
    llm = call_llm("test", "Reply OK")
    llm_status = "[OK] Connected" if llm else "[--] Not available"
    print(f"LLM: {llm_status}")
    
    # Check validator
    guard_status = "[OK] Active" if VALIDATOR_AVAILABLE else "[!!] Basic mode"
    print(f"Guardrails: {guard_status}")
    
    print(f"\nHistorical Eras: {len(HISTORICAL_ERAS)} (Ancient BC to Contemporary)")
    print(f"Cultural Styles: {len(CULTURAL_STYLES)}")
    print(f"Content Ratings: {len(CONTENT_RATINGS)} (PG to 21+)")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    
    HTTPServer(('0.0.0.0', PORT), UltraAPI).serve_forever()


if __name__ == "__main__":
    main()
