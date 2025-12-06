"""
AUTO-CAPTIONER API
===================
Generates captions for images using local LLMs (LM Studio, Ollama)
and WD14 tagger for training datasets.

Port: 8207
"""
import os
import sys
import json
import sqlite3
import base64
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
DATA_DIR = CIVITAI_PATH / "data"
DB_PATH = DATA_DIR / "captions.db"

# LLM endpoints
LM_STUDIO_URL = "http://localhost:1234/v1"
OLLAMA_URL = "http://localhost:11434"

app = Flask(__name__)
CORS(app)


class CaptionDB:
    """Database for captions"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS captions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT UNIQUE,
                caption TEXT,
                tags TEXT,
                trigger_word TEXT,
                model_used TEXT,
                quality_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS caption_stats (
                id INTEGER PRIMARY KEY,
                total_captions INTEGER DEFAULT 0,
                avg_length REAL DEFAULT 0,
                models_used TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        if not self.conn.execute('SELECT 1 FROM caption_stats WHERE id = 1').fetchone():
            self.conn.execute('INSERT INTO caption_stats (id) VALUES (1)')
        
        self.conn.commit()
    
    def save_caption(self, image_path: str, caption: str, tags: str = None,
                     trigger_word: str = None, model: str = None, quality: float = None):
        self.conn.execute('''
            INSERT OR REPLACE INTO captions 
            (image_path, caption, tags, trigger_word, model_used, quality_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (image_path, caption, tags, trigger_word, model, quality, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_caption(self, image_path: str) -> Optional[Dict]:
        row = self.conn.execute(
            'SELECT * FROM captions WHERE image_path = ?', (image_path,)
        ).fetchone()
        return dict(row) if row else None
    
    def get_stats(self) -> Dict:
        total = self.conn.execute('SELECT COUNT(*) FROM captions').fetchone()[0]
        avg_len = self.conn.execute('SELECT AVG(LENGTH(caption)) FROM captions').fetchone()[0]
        
        return {
            'total_captions': total,
            'avg_caption_length': round(avg_len or 0, 1)
        }


db = CaptionDB()


class AutoCaptioner:
    """Generate captions using various models"""
    
    # Default prompts for captioning
    CAPTION_PROMPT = """Describe this image in detail for AI image generation training.
Include: subject description, pose, expression, clothing, setting, lighting, camera angle.
Be specific and use comma-separated tags at the end.
Format: [detailed description], [tag1], [tag2], [tag3]..."""
    
    NSFW_CAPTION_PROMPT = """Describe this image in complete detail for AI training.
Include: physical appearance, pose, expression, attire or lack thereof, setting, lighting, mood.
Be explicit and detailed. Use comma-separated tags.
This is for training an uncensored AI model."""
    
    def __init__(self):
        self.lm_studio_available = self._check_lm_studio()
        self.ollama_available = self._check_ollama()
    
    def _check_lm_studio(self) -> bool:
        try:
            r = requests.get(f"{LM_STUDIO_URL}/models", timeout=5)
            return r.ok
        except:
            return False
    
    def _check_ollama(self) -> bool:
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            return r.ok
        except:
            return False
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def caption_with_lm_studio(self, image_path: str, prompt: str = None, 
                                nsfw: bool = False) -> Dict:
        """Generate caption using LM Studio vision model"""
        
        if not self.lm_studio_available:
            return {"success": False, "error": "LM Studio not available"}
        
        try:
            image_data = self._encode_image(image_path)
            
            caption_prompt = prompt or (self.NSFW_CAPTION_PROMPT if nsfw else self.CAPTION_PROMPT)
            
            response = requests.post(
                f"{LM_STUDIO_URL}/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": caption_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                            ]
                        }
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            if response.ok:
                result = response.json()
                caption = result['choices'][0]['message']['content']
                
                # Save to database
                db.save_caption(image_path, caption, model="lm_studio")
                
                return {
                    "success": True,
                    "caption": caption,
                    "model": "lm_studio",
                    "image": image_path
                }
            else:
                return {"success": False, "error": response.text}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def caption_with_ollama(self, image_path: str, model: str = "llava",
                             prompt: str = None, nsfw: bool = False) -> Dict:
        """Generate caption using Ollama vision model"""
        
        if not self.ollama_available:
            return {"success": False, "error": "Ollama not available"}
        
        try:
            image_data = self._encode_image(image_path)
            
            caption_prompt = prompt or (self.NSFW_CAPTION_PROMPT if nsfw else self.CAPTION_PROMPT)
            
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": caption_prompt,
                    "images": [image_data],
                    "stream": False
                },
                timeout=120
            )
            
            if response.ok:
                result = response.json()
                caption = result.get('response', '')
                
                # Save to database
                db.save_caption(image_path, caption, model=f"ollama:{model}")
                
                return {
                    "success": True,
                    "caption": caption,
                    "model": f"ollama:{model}",
                    "image": image_path
                }
            else:
                return {"success": False, "error": response.text}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def caption_image(self, image_path: str, nsfw: bool = False) -> Dict:
        """Caption using best available model"""
        
        # Try LM Studio first (usually has vision models loaded)
        if self.lm_studio_available:
            result = self.caption_with_lm_studio(image_path, nsfw=nsfw)
            if result.get('success'):
                return result
        
        # Try Ollama
        if self.ollama_available:
            result = self.caption_with_ollama(image_path, nsfw=nsfw)
            if result.get('success'):
                return result
        
        return {"success": False, "error": "No captioning models available"}
    
    def batch_caption(self, folder: str, nsfw: bool = False, 
                       limit: int = 100) -> Dict:
        """Caption all images in folder"""
        
        folder_path = Path(folder)
        if not folder_path.exists():
            return {"success": False, "error": f"Folder not found: {folder}"}
        
        extensions = {'.png', '.jpg', '.jpeg', '.webp'}
        images = [f for f in folder_path.iterdir() 
                  if f.suffix.lower() in extensions][:limit]
        
        results = []
        success_count = 0
        
        for image in images:
            # Skip if already captioned
            existing = db.get_caption(str(image))
            if existing:
                results.append({
                    "image": str(image),
                    "status": "skipped",
                    "caption": existing['caption'][:100] + "..."
                })
                continue
            
            result = self.caption_image(str(image), nsfw=nsfw)
            
            if result.get('success'):
                success_count += 1
                results.append({
                    "image": str(image),
                    "status": "success",
                    "caption": result['caption'][:100] + "..."
                })
            else:
                results.append({
                    "image": str(image),
                    "status": "failed",
                    "error": result.get('error', 'Unknown error')
                })
        
        return {
            "success": True,
            "total_images": len(images),
            "captioned": success_count,
            "results": results
        }
    
    def export_captions(self, folder: str, format: str = 'txt') -> Dict:
        """Export captions as .txt files alongside images"""
        
        folder_path = Path(folder)
        if not folder_path.exists():
            return {"success": False, "error": f"Folder not found: {folder}"}
        
        extensions = {'.png', '.jpg', '.jpeg', '.webp'}
        images = [f for f in folder_path.iterdir() 
                  if f.suffix.lower() in extensions]
        
        exported = 0
        
        for image in images:
            caption_data = db.get_caption(str(image))
            if caption_data and caption_data.get('caption'):
                txt_path = image.with_suffix('.txt')
                txt_path.write_text(caption_data['caption'], encoding='utf-8')
                exported += 1
        
        return {
            "success": True,
            "exported": exported,
            "total_images": len(images),
            "folder": str(folder_path)
        }


captioner = AutoCaptioner()


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/caption', methods=['POST'])
def caption_single():
    """Caption a single image"""
    data = request.json or {}
    image_path = data.get('image_path')
    nsfw = data.get('nsfw', False)
    
    if not image_path:
        return jsonify({"success": False, "error": "image_path required"}), 400
    
    return jsonify(captioner.caption_image(image_path, nsfw=nsfw))


@app.route('/api/caption/batch', methods=['POST'])
def caption_batch():
    """Caption all images in folder"""
    data = request.json or {}
    folder = data.get('folder')
    nsfw = data.get('nsfw', False)
    limit = data.get('limit', 100)
    
    if not folder:
        return jsonify({"success": False, "error": "folder required"}), 400
    
    return jsonify(captioner.batch_caption(folder, nsfw=nsfw, limit=limit))


@app.route('/api/caption/export', methods=['POST'])
def export_captions():
    """Export captions as .txt files"""
    data = request.json or {}
    folder = data.get('folder')
    
    if not folder:
        return jsonify({"success": False, "error": "folder required"}), 400
    
    return jsonify(captioner.export_captions(folder))


@app.route('/api/caption/<path:image_path>', methods=['GET'])
def get_caption(image_path: str):
    """Get existing caption for image"""
    caption = db.get_caption(image_path)
    if caption:
        return jsonify({"success": True, **caption})
    return jsonify({"success": False, "error": "Caption not found"}), 404


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get captioning statistics"""
    return jsonify({
        "success": True,
        "lm_studio_available": captioner.lm_studio_available,
        "ollama_available": captioner.ollama_available,
        **db.get_stats()
    })


@app.route('/api/models', methods=['GET'])
def list_models():
    """List available vision models"""
    models = []
    
    if captioner.lm_studio_available:
        try:
            r = requests.get(f"{LM_STUDIO_URL}/models", timeout=5)
            if r.ok:
                for m in r.json().get('data', []):
                    models.append({"name": m['id'], "source": "lm_studio"})
        except:
            pass
    
    if captioner.ollama_available:
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if r.ok:
                for m in r.json().get('models', []):
                    models.append({"name": m['name'], "source": "ollama"})
        except:
            pass
    
    return jsonify({
        "success": True,
        "models": models
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "success": True,
        "service": "Auto-Captioner API",
        "version": "1.0.0",
        "lm_studio": captioner.lm_studio_available,
        "ollama": captioner.ollama_available
    })


@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        "service": "Auto-Captioner API",
        "version": "1.0.0",
        "port": 8207,
        "endpoints": {
            "caption": "POST /api/caption",
            "batch": "POST /api/caption/batch",
            "export": "POST /api/caption/export",
            "get": "GET /api/caption/{path}",
            "models": "GET /api/models",
            "stats": "GET /api/stats",
            "health": "GET /api/health"
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  AUTO-CAPTIONER API")
    print("  Port: 8207")
    print("=" * 60)
    print(f"\n🤖 LM Studio: {'✅ Available' if captioner.lm_studio_available else '❌ Not available'}")
    print(f"🦙 Ollama: {'✅ Available' if captioner.ollama_available else '❌ Not available'}")
    print("\nEndpoints:")
    print("  POST /api/caption        - Caption single image")
    print("  POST /api/caption/batch  - Caption folder")
    print("  POST /api/caption/export - Export as .txt files")
    print("  GET  /api/models         - List vision models")
    print("  GET  /api/stats          - Captioning stats")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8207, debug=False)
