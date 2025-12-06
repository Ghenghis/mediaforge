"""
DATASET BUILDER
================
Builds training datasets from rated images.
Organizes by tier (Bronze/Silver/Gold/Platinum) based on ratings.

Port: 8211
"""
import os
import sys
import json
import shutil
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
DATA_DIR = CIVITAI_PATH / "data"
OUTPUT_DIR = Path("G:/Github/ComfyUI/output")
TRAINING_DIR = CIVITAI_PATH / "training"
DATASETS_DIR = TRAINING_DIR / "datasets"
DB_PATH = DATA_DIR / "datasets.db"

# Service APIs
CAPTION_API = "http://localhost:8207"
RATING_STUDIO_API = "http://localhost:8196"

# Ensure directories
for tier in ["bronze", "silver", "gold", "platinum", "foundation"]:
    (DATASETS_DIR / tier).mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
CORS(app)


# Tier thresholds
TIER_THRESHOLDS = {
    "foundation": {"min": 0, "max": 15, "desc": "All video frames"},
    "bronze": {"min": 1, "max": 15, "desc": "Any rated images"},
    "silver": {"min": 7, "max": 15, "desc": "Good images (7+)"},
    "gold": {"min": 10, "max": 15, "desc": "Excellent images (10+)"},
    "platinum": {"min": 13, "max": 15, "desc": "Gold standards (13+)"}
}


class DatasetDB:
    """Database for datasets"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                tier TEXT,
                image_count INTEGER DEFAULT 0,
                min_rating INTEGER,
                max_rating INTEGER,
                total_size_mb REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                path TEXT
            );
            
            CREATE TABLE IF NOT EXISTS dataset_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER,
                source_path TEXT,
                dest_path TEXT,
                caption_path TEXT,
                rating INTEGER,
                caption TEXT,
                copied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dataset_id) REFERENCES datasets(id)
            );
        ''')
        self.conn.commit()
    
    def create_dataset(self, name: str, tier: str, path: str) -> int:
        thresholds = TIER_THRESHOLDS.get(tier, {"min": 0, "max": 15})
        
        cursor = self.conn.execute('''
            INSERT OR REPLACE INTO datasets (name, tier, min_rating, max_rating, path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, tier, thresholds['min'], thresholds['max'], path, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid
    
    def add_image(self, dataset_id: int, source: str, dest: str, caption_path: str, 
                  rating: int, caption: str):
        self.conn.execute('''
            INSERT INTO dataset_images (dataset_id, source_path, dest_path, caption_path, rating, caption)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (dataset_id, source, dest, caption_path, rating, caption))
        self.conn.commit()
    
    def update_dataset_stats(self, dataset_id: int, image_count: int, total_size: float):
        self.conn.execute('''
            UPDATE datasets SET image_count = ?, total_size_mb = ? WHERE id = ?
        ''', (image_count, total_size, dataset_id))
        self.conn.commit()
    
    def get_datasets(self) -> List[Dict]:
        rows = self.conn.execute('SELECT * FROM datasets ORDER BY created_at DESC').fetchall()
        return [dict(r) for r in rows]
    
    def get_dataset(self, dataset_id: int) -> Optional[Dict]:
        row = self.conn.execute('SELECT * FROM datasets WHERE id = ?', (dataset_id,)).fetchone()
        return dict(row) if row else None


db = DatasetDB()


class DatasetBuilder:
    """Build training datasets from rated images"""
    
    def __init__(self):
        self.rating_db = self._connect_rating_db()
    
    def _connect_rating_db(self):
        """Connect to the rating database (Rating Studio Ultra)"""
        # Try the Rating Studio database directly
        rating_db_path = DATA_DIR / "rating_studio.db"
        if rating_db_path.exists():
            conn = sqlite3.connect(str(rating_db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        
        # Fallback to legacy path
        rating_db_path = DATA_DIR / "ratings.db"
        if rating_db_path.exists():
            conn = sqlite3.connect(str(rating_db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        
        return None
    
    def get_rated_images(self, min_rating: int = 0, max_rating: int = 15) -> List[Dict]:
        """Get images within rating range from Rating Studio"""
        images = []
        
        # Try Rating Studio API first
        try:
            filter_type = 'all'
            if min_rating >= 10:
                filter_type = 'excellent'
            elif min_rating >= 7:
                filter_type = 'high'
            elif min_rating >= 1:
                filter_type = 'rated'
            
            resp = requests.get(
                f"{RATING_STUDIO_API}/api/images",
                params={'filter': filter_type, 'limit': 1000},
                timeout=30
            )
            
            if resp.ok:
                data = resp.json()
                # Handle both array and object formats
                if isinstance(data, list):
                    api_images = data
                else:
                    api_images = data.get('images', [])
                
                # Filter by rating range
                for img in api_images:
                    rating = img.get('rating', 0)
                    if min_rating <= rating <= max_rating:
                        # Map to expected format
                        images.append({
                            'filepath': str(OUTPUT_DIR / img.get('filename', '')),
                            'filename': img.get('filename', ''),
                            'rating': rating,
                            'tags': img.get('tags', [])
                        })
                
                if images:
                    print(f"  Got {len(images)} images from Rating Studio API")
                    return images
        except Exception as e:
            print(f"  API failed, falling back to DB: {e}")
        
        # Fallback to direct database access
        if self.rating_db:
            try:
                rows = self.rating_db.execute('''
                    SELECT * FROM images 
                    WHERE rating >= ? AND rating <= ?
                    ORDER BY rating DESC
                ''', (min_rating, max_rating)).fetchall()
                
                for row in rows:
                    images.append({
                        'filepath': str(OUTPUT_DIR / row['filename']),
                        'filename': row['filename'],
                        'rating': row['rating'],
                        'tags': []
                    })
                
                print(f"  Got {len(images)} images from database")
            except Exception as e:
                print(f"  DB query failed: {e}")
        
        return images
    
    def get_caption(self, image_path: str, tags: list = None, force_regenerate: bool = False) -> str:
        """Get or generate caption for image"""
        # Try to get existing caption (unless force regenerating)
        txt_path = Path(image_path).with_suffix('.txt')
        if not force_regenerate and txt_path.exists():
            existing = txt_path.read_text(encoding='utf-8').strip()
            # Only use existing if it's a good caption (not default fallback)
            if existing and existing not in [
                "high quality image, detailed, masterpiece",
                "high quality image, detailed, professional photography"
            ]:
                return existing
        
        # Try caption API
        try:
            resp = requests.post(
                f"{CAPTION_API}/api/caption",
                json={"image_path": image_path},
                timeout=60
            )
            if resp.ok:
                result = resp.json()
                if result.get('success') and result.get('caption'):
                    return result.get('caption', '')
        except:
            pass
        
        # Try to get metadata from Rating Studio for this image
        filename = Path(image_path).name
        try:
            resp = requests.get(
                f"{RATING_STUDIO_API}/api/images",
                params={'filter': 'all', 'limit': 500},
                timeout=10
            )
            if resp.ok:
                images = resp.json() if isinstance(resp.json(), list) else resp.json().get('images', [])
                for img in images:
                    if img.get('filename') == filename:
                        # Build caption from metadata
                        parts = []
                        
                        # Content rating context
                        content_rating = img.get('content_rating', '')
                        if content_rating:
                            if content_rating in ['PG', 'PG-13']:
                                parts.append("tasteful artistic photo")
                            elif content_rating in ['R', 'NC-17']:
                                parts.append("mature artistic photo")
                            elif content_rating == '21+':
                                parts.append("adult artistic photo")
                        
                        # Historical era
                        era = img.get('historical_era', '')
                        if era and era != 'contemporary':
                            parts.append(f"{era} era")
                        
                        # Cultural style
                        culture = img.get('cultural_style', '')
                        if culture and culture != 'global':
                            parts.append(f"{culture} cultural style")
                        
                        # Theme
                        theme = img.get('theme')
                        if theme:
                            parts.append(theme)
                        
                        # Add tags if provided
                        if tags:
                            parts.extend(tags[:5])
                        
                        # Quality tags based on rating
                        rating = img.get('rating', 0)
                        if rating >= 10:
                            parts.extend(["masterpiece", "excellent quality", "highly detailed"])
                        elif rating >= 7:
                            parts.extend(["high quality", "detailed", "professional"])
                        else:
                            parts.extend(["good quality", "detailed"])
                        
                        if parts:
                            return ", ".join(parts)
                        break
        except:
            pass
        
        # Generate caption from filename hints
        filename = Path(image_path).stem.lower()
        parts = []
        
        # Extract hints from filename
        if 'warrior' in filename:
            parts.append("warrior character")
        if 'tribal' in filename:
            parts.append("tribal aesthetic")
        if 'portrait' in filename:
            parts.append("portrait style")
        if 'landscape' in filename:
            parts.append("landscape scene")
        if 'fantasy' in filename:
            parts.append("fantasy theme")
        if 'smart' in filename or 'test' in filename:
            parts.append("test generation")
        if 'train' in filename:
            parts.append("training image")
        
        # Add quality tags
        parts.extend(["high quality", "detailed", "masterpiece"])
        
        return ", ".join(parts) if parts else "high quality image, detailed, masterpiece"
    
    def build_dataset(self, tier: str, name: str = None, 
                       include_captions: bool = True, regenerate_captions: bool = False) -> Dict:
        """Build a dataset for the specified tier"""
        
        thresholds = TIER_THRESHOLDS.get(tier)
        if not thresholds:
            return {"success": False, "error": f"Unknown tier: {tier}"}
        
        # Get images in rating range
        images = self.get_rated_images(thresholds['min'], thresholds['max'])
        
        if not images:
            return {"success": False, "error": "No images found in rating range"}
        
        # Create dataset directory
        dataset_name = name or f"{tier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dataset_path = DATASETS_DIR / tier / dataset_name
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        # Create database entry
        dataset_id = db.create_dataset(dataset_name, tier, str(dataset_path))
        
        # Copy images and captions
        copied = 0
        total_size = 0
        
        for img in images:
            source = Path(img['filepath'])
            if not source.exists():
                continue
            
            # Copy image
            dest = dataset_path / source.name
            shutil.copy2(source, dest)
            
            # Get/generate caption
            caption = ""
            caption_path = ""
            
            if include_captions:
                caption = self.get_caption(str(source), tags=img.get('tags', []), 
                                          force_regenerate=regenerate_captions)
                caption_path = dest.with_suffix('.txt')
                caption_path.write_text(caption, encoding='utf-8')
            
            # Add to database
            db.add_image(dataset_id, str(source), str(dest), str(caption_path),
                        img.get('rating', 0), caption)
            
            copied += 1
            total_size += dest.stat().st_size / (1024 * 1024)
        
        # Update stats
        db.update_dataset_stats(dataset_id, copied, total_size)
        
        return {
            "success": True,
            "dataset_id": dataset_id,
            "name": dataset_name,
            "tier": tier,
            "images_copied": copied,
            "total_size_mb": round(total_size, 2),
            "path": str(dataset_path),
            "rating_range": f"{thresholds['min']}-{thresholds['max']}"
        }
    
    def build_all_tiers(self) -> Dict:
        """Build datasets for all tiers"""
        results = {}
        
        for tier in ["bronze", "silver", "gold", "platinum"]:
            result = self.build_dataset(tier)
            results[tier] = result
        
        return {
            "success": True,
            "results": results
        }
    
    def create_kohya_config(self, dataset_path: str, output_name: str,
                             lora_rank: int = 64, learning_rate: float = 1e-4,
                             steps: int = 1000) -> Dict:
        """Create Kohya training config file"""
        
        config = {
            "pretrained_model_name_or_path": "ponyDiffusionV6XL.safetensors",
            "train_data_dir": dataset_path,
            "output_dir": str(CIVITAI_PATH / "loras"),
            "output_name": output_name,
            "save_model_as": "safetensors",
            "network_module": "networks.lora",
            "network_dim": lora_rank,
            "network_alpha": lora_rank // 2,
            "learning_rate": learning_rate,
            "unet_lr": learning_rate,
            "text_encoder_lr": learning_rate / 2,
            "lr_scheduler": "cosine_with_restarts",
            "lr_warmup_steps": steps // 10,
            "max_train_steps": steps,
            "save_every_n_steps": steps // 4,
            "mixed_precision": "fp16",
            "save_precision": "fp16",
            "seed": 42,
            "cache_latents": True,
            "cache_latents_to_disk": True,
            "optimizer_type": "AdamW8bit",
            "max_data_loader_n_workers": 2,
            "bucket_no_upscale": True,
            "resolution": "1024,1024",
            "enable_bucket": True,
            "min_bucket_reso": 512,
            "max_bucket_reso": 2048,
            "caption_extension": ".txt",
            "shuffle_caption": True,
            "keep_tokens": 1
        }
        
        config_path = Path(dataset_path) / "training_config.json"
        config_path.write_text(json.dumps(config, indent=2))
        
        return {
            "success": True,
            "config_path": str(config_path),
            "config": config
        }


builder = DatasetBuilder()


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/dataset/build', methods=['POST'])
def build_dataset():
    """Build dataset for a tier"""
    data = request.json or {}
    tier = data.get('tier', 'bronze')
    name = data.get('name')
    include_captions = data.get('include_captions', True)
    regenerate_captions = data.get('regenerate_captions', False)
    
    return jsonify(builder.build_dataset(tier, name, include_captions, regenerate_captions))


@app.route('/api/dataset/build-all', methods=['POST'])
def build_all():
    """Build datasets for all tiers"""
    return jsonify(builder.build_all_tiers())


@app.route('/api/dataset/list', methods=['GET'])
def list_datasets():
    """List all datasets"""
    return jsonify({
        "success": True,
        "datasets": db.get_datasets()
    })


@app.route('/api/dataset/<int:dataset_id>', methods=['GET'])
def get_dataset(dataset_id: int):
    """Get dataset details"""
    dataset = db.get_dataset(dataset_id)
    if dataset:
        return jsonify({"success": True, "dataset": dataset})
    return jsonify({"success": False, "error": "Dataset not found"}), 404


@app.route('/api/dataset/<int:dataset_id>/config', methods=['POST'])
def create_config(dataset_id: int):
    """Create Kohya training config"""
    dataset = db.get_dataset(dataset_id)
    if not dataset:
        return jsonify({"success": False, "error": "Dataset not found"}), 404
    
    data = request.json or {}
    
    return jsonify(builder.create_kohya_config(
        dataset['path'],
        data.get('output_name', dataset['name']),
        data.get('lora_rank', 64),
        data.get('learning_rate', 1e-4),
        data.get('steps', 1000)
    ))


@app.route('/api/tiers', methods=['GET'])
def get_tiers():
    """Get tier configurations"""
    return jsonify({
        "success": True,
        "tiers": TIER_THRESHOLDS
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dataset statistics"""
    datasets = db.get_datasets()
    
    total_images = sum(d.get('image_count', 0) for d in datasets)
    total_size = sum(d.get('total_size_mb', 0) for d in datasets)
    
    by_tier = {}
    for d in datasets:
        tier = d.get('tier', 'unknown')
        if tier not in by_tier:
            by_tier[tier] = {"count": 0, "images": 0, "size_mb": 0}
        by_tier[tier]["count"] += 1
        by_tier[tier]["images"] += d.get('image_count', 0)
        by_tier[tier]["size_mb"] += d.get('total_size_mb', 0)
    
    return jsonify({
        "success": True,
        "total_datasets": len(datasets),
        "total_images": total_images,
        "total_size_mb": round(total_size, 2),
        "by_tier": by_tier
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "success": True,
        "service": "Dataset Builder",
        "version": "1.0.0"
    })


@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        "service": "Dataset Builder",
        "version": "1.0.0",
        "port": 8211,
        "description": "Builds training datasets from rated images",
        "endpoints": {
            "build": "POST /api/dataset/build",
            "build_all": "POST /api/dataset/build-all",
            "list": "GET /api/dataset/list",
            "get": "GET /api/dataset/{id}",
            "config": "POST /api/dataset/{id}/config",
            "tiers": "GET /api/tiers",
            "stats": "GET /api/stats"
        },
        "tiers": TIER_THRESHOLDS
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  DATASET BUILDER")
    print("  Build Training Datasets from Rated Images")
    print("  Port: 8211")
    print("=" * 60)
    
    print("\n📊 Tier Thresholds:")
    for tier, info in TIER_THRESHOLDS.items():
        print(f"    {tier.upper()}: ratings {info['min']}-{info['max']} - {info['desc']}")
    
    print("\n📡 Endpoints:")
    print("    POST /api/dataset/build     - Build single tier")
    print("    POST /api/dataset/build-all - Build all tiers")
    print("    GET  /api/dataset/list      - List datasets")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8211, debug=False)
