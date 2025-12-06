"""
COMFYUI AUTOMATION API
=======================
Complete automation for ComfyUI image generation.
Handles workflows, prompts, batch generation, and quality validation.

Port: 8213
"""
import os
import sys
import json
import random
import requests
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
DATA_DIR = CIVITAI_PATH / "data"
COMFYUI_PATH = Path("G:/Github/ComfyUI")
WORKFLOWS_DIR = COMFYUI_PATH / "user" / "default" / "workflows"
OUTPUT_DIR = COMFYUI_PATH / "output"
DB_PATH = DATA_DIR / "comfyui.db"

# ComfyUI API
COMFYUI_URL = "http://127.0.0.1:8188"

app = Flask(__name__)
CORS(app)


# Style templates
STYLE_TEMPLATES = {
    "tribal": {
        "name": "Tribal Face Paint",
        "model": "cyberrealistic_v42.safetensors",
        "lora": "TRIBAL-BEAUTY",
        "positive_prefix": "tribal face paint, war paint, indigenous warrior, detailed skin texture, ",
        "positive_suffix": ", masterpiece, best quality, 8K, realistic, HDR",
        "negative": "cartoon, anime, 3d render, low quality, blurry, watermark"
    },
    "anime": {
        "name": "Anime Illustrious",
        "model": "noobaiXLNAIXL_epsilonPred11.safetensors",
        "lora": "PowerPuffMixLora",
        "positive_prefix": "anime style, detailed illustration, ",
        "positive_suffix": ", masterpiece, best quality, absurdres, amazing quality",
        "negative": "realistic, photo, 3d, low quality, worst quality, blurry"
    },
    "realistic": {
        "name": "Photorealistic",
        "model": "cyberrealistic_v42.safetensors",
        "lora": None,
        "positive_prefix": "photorealistic, 8K photo, DSLR quality, ",
        "positive_suffix": ", masterpiece, best quality, realistic skin, detailed",
        "negative": "cartoon, anime, illustration, painting, low quality, blurry"
    },
    "fantasy": {
        "name": "Fantasy Mystical",
        "model": "ponyDiffusionV6XL.safetensors",
        "lora": None,
        "positive_prefix": "fantasy art, mystical, ethereal, magical, ",
        "positive_suffix": ", masterpiece, best quality, detailed, vibrant colors",
        "negative": "photo, realistic, mundane, low quality, blurry"
    },
    "western": {
        "name": "Western Frontier",
        "model": "ponyDiffusionV6XL.safetensors",
        "lora": None,
        "positive_prefix": "old west, frontier, western style, dusty, ",
        "positive_suffix": ", masterpiece, best quality, cinematic lighting",
        "negative": "modern, futuristic, low quality, blurry"
    }
}

# Generation presets
GENERATION_PRESETS = {
    "fast": {"steps": 20, "cfg": 7.0, "sampler": "euler_ancestral"},
    "balanced": {"steps": 30, "cfg": 7.5, "sampler": "dpmpp_2m"},
    "quality": {"steps": 40, "cfg": 8.0, "sampler": "dpmpp_2m_sde"},
    "maximum": {"steps": 50, "cfg": 8.5, "sampler": "dpmpp_3m_sde"}
}


class ComfyUIDB:
    """Database for ComfyUI automation"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                positive TEXT,
                negative TEXT,
                style TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER,
                workflow TEXT,
                style TEXT,
                output_path TEXT,
                seed INTEGER,
                steps INTEGER,
                cfg REAL,
                width INTEGER,
                height INTEGER,
                generation_time REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id)
            );
            
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                style TEXT,
                total_images INTEGER,
                completed INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT
            );
        ''')
        self.conn.commit()
    
    def add_prompt(self, category: str, positive: str, negative: str, 
                   style: str = None, tags: str = None) -> int:
        cursor = self.conn.execute('''
            INSERT INTO prompts (category, positive, negative, style, tags)
            VALUES (?, ?, ?, ?, ?)
        ''', (category, positive, negative, style, tags))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_prompts(self, category: str = None, limit: int = 100) -> List[Dict]:
        if category:
            rows = self.conn.execute(
                'SELECT * FROM prompts WHERE category = ? ORDER BY id DESC LIMIT ?',
                (category, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                'SELECT * FROM prompts ORDER BY id DESC LIMIT ?', (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
    
    def get_random_prompt(self, category: str = None) -> Optional[Dict]:
        if category:
            row = self.conn.execute(
                'SELECT * FROM prompts WHERE category = ? ORDER BY RANDOM() LIMIT 1',
                (category,)
            ).fetchone()
        else:
            row = self.conn.execute(
                'SELECT * FROM prompts ORDER BY RANDOM() LIMIT 1'
            ).fetchone()
        return dict(row) if row else None
    
    def log_generation(self, prompt_id: int, workflow: str, style: str,
                       output_path: str, seed: int, steps: int, cfg: float,
                       width: int, height: int, gen_time: float):
        self.conn.execute('''
            INSERT INTO generations 
            (prompt_id, workflow, style, output_path, seed, steps, cfg, width, height, generation_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (prompt_id, workflow, style, output_path, seed, steps, cfg, width, height, gen_time))
        self.conn.commit()


db = ComfyUIDB()


class ComfyUIClient:
    """Client for ComfyUI API"""
    
    def __init__(self):
        self.base_url = COMFYUI_URL
    
    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/system_stats", timeout=5)
            return resp.ok
        except:
            return False
    
    def get_queue(self) -> Dict:
        try:
            resp = requests.get(f"{self.base_url}/queue", timeout=5)
            return resp.json() if resp.ok else {}
        except:
            return {}
    
    def queue_prompt(self, workflow: Dict) -> Optional[str]:
        """Queue a workflow for execution"""
        try:
            resp = requests.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow},
                timeout=10
            )
            if resp.ok:
                return resp.json().get('prompt_id')
        except Exception as e:
            print(f"Queue error: {e}")
        return None
    
    def get_history(self, prompt_id: str) -> Dict:
        try:
            resp = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=10)
            return resp.json() if resp.ok else {}
        except:
            return {}
    
    def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> bool:
        """Wait for prompt to complete"""
        start = time.time()
        while time.time() - start < timeout:
            history = self.get_history(prompt_id)
            if prompt_id in history:
                return True
            time.sleep(1)
        return False
    
    def get_models(self) -> Dict:
        """Get available models"""
        try:
            resp = requests.get(f"{self.base_url}/object_info", timeout=10)
            if resp.ok:
                info = resp.json()
                checkpoints = info.get('CheckpointLoaderSimple', {}).get('input', {}).get('required', {}).get('ckpt_name', [[]])[0]
                loras = info.get('LoraLoader', {}).get('input', {}).get('required', {}).get('lora_name', [[]])[0]
                return {
                    "checkpoints": checkpoints if isinstance(checkpoints, list) else [],
                    "loras": loras if isinstance(loras, list) else []
                }
        except:
            pass
        return {"checkpoints": [], "loras": []}


client = ComfyUIClient()


class WorkflowBuilder:
    """Build ComfyUI workflows programmatically"""
    
    def build_txt2img(self, positive: str, negative: str,
                       model: str = "ponyDiffusionV6XL.safetensors",
                       lora: str = None, lora_strength: float = 0.8,
                       width: int = 1024, height: int = 1024,
                       steps: int = 30, cfg: float = 7.5,
                       sampler: str = "dpmpp_2m", scheduler: str = "normal",
                       seed: int = None) -> Dict:
        """Build a text-to-image workflow"""
        
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": model}
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": positive, "clip": ["4", 1]}
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative, "clip": ["4", 1]}
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]}
            }
        }
        
        # Add LoRA if specified
        if lora:
            workflow["10"] = {
                "class_type": "LoraLoader",
                "inputs": {
                    "lora_name": f"{lora}.safetensors",
                    "strength_model": lora_strength,
                    "strength_clip": lora_strength,
                    "model": ["4", 0],
                    "clip": ["4", 1]
                }
            }
            # Update connections
            workflow["3"]["inputs"]["model"] = ["10", 0]
            workflow["6"]["inputs"]["clip"] = ["10", 1]
            workflow["7"]["inputs"]["clip"] = ["10", 1]
        
        return workflow
    
    def apply_style(self, base_prompt: str, style: str) -> Dict:
        """Apply style template to prompt"""
        template = STYLE_TEMPLATES.get(style, STYLE_TEMPLATES["realistic"])
        
        positive = template["positive_prefix"] + base_prompt + template["positive_suffix"]
        negative = template["negative"]
        
        return {
            "positive": positive,
            "negative": negative,
            "model": template["model"],
            "lora": template.get("lora")
        }


builder = WorkflowBuilder()


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/comfyui/status', methods=['GET'])
def get_status():
    """Get ComfyUI status"""
    available = client.is_available()
    queue = client.get_queue() if available else {}
    
    return jsonify({
        "success": True,
        "available": available,
        "url": COMFYUI_URL,
        "queue": {
            "running": len(queue.get('queue_running', [])),
            "pending": len(queue.get('queue_pending', []))
        }
    })


@app.route('/api/comfyui/models', methods=['GET'])
def get_models():
    """Get available models"""
    return jsonify({
        "success": True,
        **client.get_models()
    })


@app.route('/api/comfyui/generate', methods=['POST'])
def generate_image():
    """Generate single image"""
    data = request.json or {}
    
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({"success": False, "error": "No prompt provided"}), 400
    
    style = data.get('style', 'realistic')
    preset = data.get('preset', 'balanced')
    
    # Apply style
    styled = builder.apply_style(prompt, style)
    
    # Get preset settings
    settings = GENERATION_PRESETS.get(preset, GENERATION_PRESETS["balanced"])
    
    # Build workflow
    workflow = builder.build_txt2img(
        positive=styled["positive"],
        negative=data.get('negative', styled["negative"]),
        model=data.get('model', styled["model"]),
        lora=styled.get("lora"),
        width=data.get('width', 1024),
        height=data.get('height', 1024),
        steps=data.get('steps', settings["steps"]),
        cfg=data.get('cfg', settings["cfg"]),
        sampler=data.get('sampler', settings["sampler"]),
        seed=data.get('seed')
    )
    
    # Queue
    prompt_id = client.queue_prompt(workflow)
    
    if prompt_id:
        return jsonify({
            "success": True,
            "prompt_id": prompt_id,
            "style": style,
            "preset": preset
        })
    
    return jsonify({"success": False, "error": "Failed to queue prompt"}), 500


@app.route('/api/comfyui/batch', methods=['POST'])
def generate_batch():
    """Generate batch of images"""
    data = request.json or {}
    
    prompts = data.get('prompts', [])
    count = data.get('count', 10)
    style = data.get('style', 'realistic')
    
    # If no prompts, use random from database
    if not prompts:
        prompts = [db.get_random_prompt() for _ in range(count)]
        prompts = [p['positive'] for p in prompts if p]
    
    if not prompts:
        return jsonify({"success": False, "error": "No prompts available"}), 400
    
    results = []
    for prompt in prompts[:count]:
        styled = builder.apply_style(prompt, style)
        workflow = builder.build_txt2img(
            positive=styled["positive"],
            negative=styled["negative"],
            model=styled["model"],
            lora=styled.get("lora")
        )
        
        prompt_id = client.queue_prompt(workflow)
        results.append({
            "prompt": prompt[:50] + "...",
            "prompt_id": prompt_id,
            "queued": prompt_id is not None
        })
    
    queued = sum(1 for r in results if r['queued'])
    
    return jsonify({
        "success": True,
        "total": len(results),
        "queued": queued,
        "style": style,
        "results": results
    })


@app.route('/api/comfyui/styles', methods=['GET'])
def get_styles():
    """Get available styles"""
    return jsonify({
        "success": True,
        "styles": {k: {"name": v["name"], "model": v["model"]} 
                   for k, v in STYLE_TEMPLATES.items()}
    })


@app.route('/api/comfyui/presets', methods=['GET'])
def get_presets():
    """Get generation presets"""
    return jsonify({
        "success": True,
        "presets": GENERATION_PRESETS
    })


@app.route('/api/prompts', methods=['GET'])
def list_prompts():
    """List prompts"""
    category = request.args.get('category')
    limit = int(request.args.get('limit', 100))
    return jsonify({
        "success": True,
        "prompts": db.get_prompts(category, limit)
    })


@app.route('/api/prompts', methods=['POST'])
def add_prompt():
    """Add prompt"""
    data = request.json or {}
    
    prompt_id = db.add_prompt(
        category=data.get('category', 'general'),
        positive=data.get('positive', ''),
        negative=data.get('negative', ''),
        style=data.get('style'),
        tags=data.get('tags')
    )
    
    return jsonify({"success": True, "prompt_id": prompt_id})


@app.route('/api/prompts/random', methods=['GET'])
def random_prompt():
    """Get random prompt"""
    category = request.args.get('category')
    prompt = db.get_random_prompt(category)
    
    if prompt:
        return jsonify({"success": True, "prompt": prompt})
    return jsonify({"success": False, "error": "No prompts found"}), 404


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "success": True,
        "service": "ComfyUI Automation",
        "comfyui_available": client.is_available()
    })


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "service": "ComfyUI Automation API",
        "version": "1.0.0",
        "port": 8213,
        "comfyui": {
            "url": COMFYUI_URL,
            "available": client.is_available()
        },
        "endpoints": {
            "status": "GET /api/comfyui/status",
            "models": "GET /api/comfyui/models",
            "generate": "POST /api/comfyui/generate",
            "batch": "POST /api/comfyui/batch",
            "styles": "GET /api/comfyui/styles",
            "presets": "GET /api/comfyui/presets",
            "prompts": "GET/POST /api/prompts"
        },
        "styles": list(STYLE_TEMPLATES.keys()),
        "presets": list(GENERATION_PRESETS.keys())
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  COMFYUI AUTOMATION API")
    print("  Port: 8213")
    print("=" * 60)
    
    comfyui_status = "[OK] Available" if client.is_available() else "[--] Not running"
    print(f"\nComfyUI: {comfyui_status}")
    print(f"   URL: {COMFYUI_URL}")
    
    print("\nStyles:", ", ".join(STYLE_TEMPLATES.keys()))
    print("Presets:", ", ".join(GENERATION_PRESETS.keys()))
    
    print("\nEndpoints:")
    print("    POST /api/comfyui/generate - Generate image")
    print("    POST /api/comfyui/batch    - Batch generate")
    print("    GET  /api/comfyui/styles   - List styles")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8213, debug=False)
