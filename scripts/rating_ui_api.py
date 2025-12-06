"""
RATING UI API
==============
Backend for image rating UI with keyboard shortcuts.
Auto-generates variations when rating >= 10.
Marks gold standards when rating = 15.

Port: 8208
"""
import os
import sys
import json
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import random

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
DATA_DIR = CIVITAI_PATH / "data"
OUTPUT_DIR = Path("G:/Github/ComfyUI/output")
DB_PATH = DATA_DIR / "ratings.db"

# API endpoints
COMFYUI_URL = "http://127.0.0.1:8188"
LM_STUDIO_URL = "http://localhost:1234/v1"

app = Flask(__name__)
CORS(app)


class RatingDB:
    """Database for image ratings"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE,
                filename TEXT,
                prompt TEXT,
                rating INTEGER DEFAULT 0,
                is_gold_standard BOOLEAN DEFAULT FALSE,
                variations_generated INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                rated_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS rating_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER,
                old_rating INTEGER,
                new_rating INTEGER,
                rated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id)
            );
            
            CREATE TABLE IF NOT EXISTS variation_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_image_id INTEGER,
                prompt TEXT,
                status TEXT DEFAULT 'pending',
                result_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_image_id) REFERENCES images(id)
            );
            
            CREATE TABLE IF NOT EXISTS session_stats (
                id INTEGER PRIMARY KEY,
                images_rated INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0,
                gold_standards INTEGER DEFAULT 0,
                variations_triggered INTEGER DEFAULT 0,
                session_start TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        if not self.conn.execute('SELECT 1 FROM session_stats WHERE id = 1').fetchone():
            self.conn.execute('''INSERT INTO session_stats (id, session_start) 
                               VALUES (1, ?)''', (datetime.now().isoformat(),))
        
        self.conn.commit()
    
    def scan_images(self, folder: str = None) -> int:
        """Scan folder for new images"""
        folder_path = Path(folder) if folder else OUTPUT_DIR
        
        if not folder_path.exists():
            return 0
        
        extensions = {'.png', '.jpg', '.jpeg', '.webp'}
        new_count = 0
        
        for img in folder_path.glob('*'):
            if img.suffix.lower() in extensions:
                try:
                    self.conn.execute('''
                        INSERT OR IGNORE INTO images (filepath, filename)
                        VALUES (?, ?)
                    ''', (str(img), img.name))
                    if self.conn.total_changes > 0:
                        new_count += 1
                except:
                    continue
        
        self.conn.commit()
        return new_count
    
    def get_unrated_images(self, limit: int = 100) -> List[Dict]:
        """Get unrated images"""
        rows = self.conn.execute('''
            SELECT * FROM images 
            WHERE rating = 0 OR rating IS NULL
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        return [dict(r) for r in rows]
    
    def get_next_unrated(self) -> Optional[Dict]:
        """Get next unrated image"""
        row = self.conn.execute('''
            SELECT * FROM images 
            WHERE rating = 0 OR rating IS NULL
            ORDER BY RANDOM()
            LIMIT 1
        ''').fetchone()
        return dict(row) if row else None
    
    def rate_image(self, image_id: int, rating: int) -> Dict:
        """Rate an image (0-15)"""
        rating = max(0, min(15, rating))  # Clamp to 0-15
        
        # Get current rating
        row = self.conn.execute('SELECT rating FROM images WHERE id = ?', (image_id,)).fetchone()
        old_rating = row[0] if row else 0
        
        # Update rating
        self.conn.execute('''
            UPDATE images 
            SET rating = ?, rated_at = ?, is_gold_standard = ?
            WHERE id = ?
        ''', (rating, datetime.now().isoformat(), rating == 15, image_id))
        
        # Log history
        self.conn.execute('''
            INSERT INTO rating_history (image_id, old_rating, new_rating)
            VALUES (?, ?, ?)
        ''', (image_id, old_rating, rating))
        
        # Update session stats
        self._update_session_stats()
        
        self.conn.commit()
        
        result = {
            "success": True,
            "image_id": image_id,
            "rating": rating,
            "is_gold_standard": rating == 15
        }
        
        # Trigger variations for high ratings
        if rating >= 10:
            variation_count = 50 if rating == 15 else 20 if rating >= 13 else 10
            result["variations_queued"] = self._queue_variations(image_id, variation_count)
        
        return result
    
    def _update_session_stats(self):
        """Update session statistics"""
        rated = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
        avg = self.conn.execute('SELECT AVG(rating) FROM images WHERE rating > 0').fetchone()[0]
        gold = self.conn.execute('SELECT COUNT(*) FROM images WHERE is_gold_standard = 1').fetchone()[0]
        variations = self.conn.execute('SELECT COUNT(*) FROM variation_queue').fetchone()[0]
        
        self.conn.execute('''
            UPDATE session_stats 
            SET images_rated = ?, avg_rating = ?, gold_standards = ?, 
                variations_triggered = ?, updated_at = ?
            WHERE id = 1
        ''', (rated, avg or 0, gold, variations, datetime.now().isoformat()))
    
    def _queue_variations(self, image_id: int, count: int) -> int:
        """Queue variation generation"""
        row = self.conn.execute('SELECT * FROM images WHERE id = ?', (image_id,)).fetchone()
        if not row:
            return 0
        
        prompt = row['prompt'] or "beautiful image, masterpiece, best quality"
        
        for i in range(count):
            # Add variation to prompt
            variation_prompt = self._create_variation_prompt(prompt, i)
            
            self.conn.execute('''
                INSERT INTO variation_queue (source_image_id, prompt)
                VALUES (?, ?)
            ''', (image_id, variation_prompt))
        
        self.conn.commit()
        return count
    
    def _create_variation_prompt(self, base_prompt: str, variation_num: int) -> str:
        """Create variation of prompt"""
        variations = [
            "different angle",
            "different lighting",
            "different pose",
            "closer view",
            "wider shot",
            "more dramatic",
            "softer lighting",
            "golden hour",
            "studio lighting",
            "natural light"
        ]
        
        variation = variations[variation_num % len(variations)]
        return f"{base_prompt}, {variation}"
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        row = self.conn.execute('SELECT * FROM session_stats WHERE id = 1').fetchone()
        
        total = self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0]
        unrated = self.conn.execute('SELECT COUNT(*) FROM images WHERE rating = 0 OR rating IS NULL').fetchone()[0]
        
        return {
            "total_images": total,
            "unrated": unrated,
            "rated": row['images_rated'] if row else 0,
            "avg_rating": round(row['avg_rating'] or 0, 1) if row else 0,
            "gold_standards": row['gold_standards'] if row else 0,
            "variations_triggered": row['variations_triggered'] if row else 0,
            "session_start": row['session_start'] if row else None
        }
    
    def get_rating_distribution(self) -> Dict:
        """Get rating distribution"""
        distribution = {}
        for i in range(16):
            count = self.conn.execute(
                'SELECT COUNT(*) FROM images WHERE rating = ?', (i,)
            ).fetchone()[0]
            distribution[i] = count
        return distribution


db = RatingDB()


# ============================================================
# KEYBOARD SHORTCUTS REFERENCE
# ============================================================
KEYBOARD_SHORTCUTS = {
    "0": {"action": "delete", "rating": 0, "description": "Delete/Reject image"},
    "1": {"action": "rate", "rating": 1, "description": "Very poor"},
    "2": {"action": "rate", "rating": 2, "description": "Poor"},
    "3": {"action": "rate", "rating": 3, "description": "Below average"},
    "4": {"action": "rate", "rating": 4, "description": "Average"},
    "5": {"action": "rate", "rating": 5, "description": "Acceptable"},
    "6": {"action": "rate", "rating": 6, "description": "Good"},
    "7": {"action": "rate", "rating": 7, "description": "Very good"},
    "8": {"action": "rate", "rating": 8, "description": "Great"},
    "9": {"action": "rate", "rating": 9, "description": "Excellent"},
    "+": {"action": "expand", "description": "Show 10-15 rating options"},
    "n": {"action": "next", "description": "Next image"},
    "p": {"action": "previous", "description": "Previous image"},
    "s": {"action": "skip", "description": "Skip (rate later)"},
    "r": {"action": "refresh", "description": "Refresh image list"},
    "g": {"action": "gold", "rating": 15, "description": "Mark as Gold Standard (15)"}
}


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/images/scan', methods=['POST'])
def scan_images():
    """Scan folder for images"""
    data = request.json or {}
    folder = data.get('folder', str(OUTPUT_DIR))
    
    new_count = db.scan_images(folder)
    
    return jsonify({
        "success": True,
        "new_images": new_count,
        "folder": folder
    })


@app.route('/api/images/unrated', methods=['GET'])
def get_unrated():
    """Get list of unrated images"""
    limit = int(request.args.get('limit', 100))
    images = db.get_unrated_images(limit)
    
    return jsonify({
        "success": True,
        "count": len(images),
        "images": images
    })


@app.route('/api/images/next', methods=['GET'])
def get_next():
    """Get next unrated image"""
    image = db.get_next_unrated()
    
    if image:
        return jsonify({
            "success": True,
            "image": image
        })
    return jsonify({
        "success": False,
        "message": "No unrated images"
    })


@app.route('/api/images/<int:image_id>/rate', methods=['POST'])
def rate_image(image_id: int):
    """Rate an image"""
    data = request.json or {}
    rating = data.get('rating', 0)
    
    result = db.rate_image(image_id, rating)
    return jsonify(result)


@app.route('/api/rate', methods=['POST'])
def quick_rate():
    """Quick rate by filepath"""
    data = request.json or {}
    filepath = data.get('filepath')
    rating = data.get('rating', 0)
    
    if not filepath:
        return jsonify({"success": False, "error": "filepath required"}), 400
    
    # Get or create image record
    row = db.conn.execute('SELECT id FROM images WHERE filepath = ?', (filepath,)).fetchone()
    
    if not row:
        db.conn.execute('INSERT INTO images (filepath, filename) VALUES (?, ?)',
                       (filepath, Path(filepath).name))
        db.conn.commit()
        row = db.conn.execute('SELECT id FROM images WHERE filepath = ?', (filepath,)).fetchone()
    
    result = db.rate_image(row[0], rating)
    return jsonify(result)


@app.route('/api/keyboard-shortcuts', methods=['GET'])
def get_shortcuts():
    """Get keyboard shortcuts reference"""
    return jsonify({
        "success": True,
        "shortcuts": KEYBOARD_SHORTCUTS,
        "usage": {
            "0-9": "Rate 0-9 directly",
            "+": "Expand for 10-15 ratings",
            "n/p": "Navigate next/previous",
            "s": "Skip current image",
            "r": "Refresh list",
            "g": "Quick mark as Gold (15)"
        }
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get rating statistics"""
    stats = db.get_stats()
    distribution = db.get_rating_distribution()
    
    return jsonify({
        "success": True,
        **stats,
        "distribution": distribution
    })


@app.route('/api/variations/pending', methods=['GET'])
def get_pending_variations():
    """Get pending variation queue"""
    rows = db.conn.execute('''
        SELECT v.*, i.filepath as source_image
        FROM variation_queue v
        JOIN images i ON v.source_image_id = i.id
        WHERE v.status = 'pending'
        ORDER BY v.created_at
        LIMIT 50
    ''').fetchall()
    
    return jsonify({
        "success": True,
        "count": len(rows),
        "variations": [dict(r) for r in rows]
    })


@app.route('/api/gold-standards', methods=['GET'])
def get_gold_standards():
    """Get all gold standard images"""
    rows = db.conn.execute('''
        SELECT * FROM images 
        WHERE is_gold_standard = 1
        ORDER BY rated_at DESC
    ''').fetchall()
    
    return jsonify({
        "success": True,
        "count": len(rows),
        "images": [dict(r) for r in rows]
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "success": True,
        "service": "Rating UI API",
        "version": "1.0.0",
        "stats": db.get_stats()
    })


@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        "service": "Rating UI API",
        "version": "1.0.0",
        "port": 8208,
        "features": {
            "keyboard_shortcuts": True,
            "auto_variations_on_high_rating": True,
            "gold_standard_marking": True,
            "session_tracking": True
        },
        "endpoints": {
            "scan": "POST /api/images/scan",
            "unrated": "GET /api/images/unrated",
            "next": "GET /api/images/next",
            "rate": "POST /api/images/{id}/rate",
            "quick_rate": "POST /api/rate",
            "shortcuts": "GET /api/keyboard-shortcuts",
            "stats": "GET /api/stats",
            "variations": "GET /api/variations/pending",
            "gold": "GET /api/gold-standards",
            "health": "GET /api/health"
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  RATING UI API")
    print("  Port: 8208")
    print("=" * 60)
    
    print("\n⌨️  Keyboard Shortcuts:")
    print("    0     = Delete (rating 0)")
    print("    1-9   = Rate 1-9")
    print("    +     = Expand 10-15 options")
    print("    n/p   = Next/Previous")
    print("    s     = Skip")
    print("    g     = Gold Standard (15)")
    
    print("\n🎯 Auto-Generation Triggers:")
    print("    Rating 10-12: Generate 10 variations")
    print("    Rating 13-14: Generate 20 variations")
    print("    Rating 15:    Generate 50 variations (Gold)")
    
    # Initial scan
    new = db.scan_images()
    stats = db.get_stats()
    print(f"\n📊 Stats: {stats['total_images']} total, {stats['unrated']} unrated")
    
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8208, debug=False)
