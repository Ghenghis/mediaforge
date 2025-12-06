"""
COMFYUI API INTEGRATION
========================
Direct API integration with ComfyUI
Workflow management, generation, and result handling

Port: 8204
"""
import json
import sqlite3
import uuid
import time
import httpx
import asyncio
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import websocket

# Configuration
PORT = 8204
COMFYUI_API = "http://127.0.0.1:8188"
COMFYUI_WS = "ws://127.0.0.1:8188/ws"
DB_PATH = Path(r"c:\Users\Admin\civitai\data\comfyui.db")
WORKFLOWS_DIR = Path(r"c:\Users\Admin\civitai\data\workflows")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\output\comfyui")

# Load rating config for prompt filtering
RATINGS_PATH = Path(r"c:\Users\Admin\civitai\data\comprehensive_ratings.json")
try:
    with open(RATINGS_PATH, encoding='utf-8') as f:
        RATINGS_CONFIG = json.load(f)
except:
    RATINGS_CONFIG = {"ratings": {}}

# Ensure directories exist
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ComfyUIDB:
    """Database for ComfyUI operations"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                workflow_json TEXT NOT NULL,
                rating TEXT DEFAULT 'PG',
                category TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id TEXT UNIQUE,
                client_id TEXT,
                workflow_name TEXT,
                prompt TEXT,
                negative_prompt TEXT,
                model TEXT,
                rating TEXT,
                country_code TEXT,
                status TEXT DEFAULT 'queued',
                output_images TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                path TEXT,
                type TEXT,
                rating_support TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS queue_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id TEXT,
                action TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()
        self._init_default_workflows()
    
    def _init_default_workflows(self):
        """Initialize default workflows"""
        default_workflows = [
            {
                "name": "txt2img_basic",
                "description": "Basic text to image generation",
                "rating": "PG",
                "category": "basic",
                "workflow": self._get_basic_txt2img_workflow()
            },
            {
                "name": "txt2img_hires",
                "description": "High resolution text to image",
                "rating": "PG",
                "category": "quality",
                "workflow": self._get_hires_workflow()
            }
        ]
        
        for wf in default_workflows:
            try:
                self.conn.execute('''
                    INSERT OR IGNORE INTO workflows (name, description, workflow_json, rating, category)
                    VALUES (?, ?, ?, ?, ?)
                ''', (wf['name'], wf['description'], json.dumps(wf['workflow']), 
                      wf['rating'], wf['category']))
            except:
                pass
        self.conn.commit()
    
    def _get_basic_txt2img_workflow(self):
        """Basic txt2img workflow template"""
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 7,
                    "denoise": 1,
                    "latent_image": ["5", 0],
                    "model": ["4", 0],
                    "negative": ["7", 0],
                    "positive": ["6", 0],
                    "sampler_name": "euler_ancestral",
                    "scheduler": "normal",
                    "seed": 0,
                    "steps": 20
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "{{MODEL}}"
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": 512,
                    "width": 512
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": "{{PROMPT}}"
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": "{{NEGATIVE}}"
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                }
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                }
            }
        }
    
    def _get_hires_workflow(self):
        """High resolution workflow template"""
        base = self._get_basic_txt2img_workflow()
        base["5"]["inputs"]["height"] = 1024
        base["5"]["inputs"]["width"] = 1024
        base["3"]["inputs"]["steps"] = 30
        return base
    
    def save_workflow(self, name, workflow_json, description=None, rating='PG', category=None):
        try:
            self.conn.execute('''
                INSERT OR REPLACE INTO workflows (name, description, workflow_json, rating, category, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, json.dumps(workflow_json), rating, category, 
                  datetime.now().isoformat()))
            self.conn.commit()
            return {'success': True, 'name': name}
        except Exception as e:
            return {'error': str(e)}
    
    def get_workflow(self, name):
        row = self.conn.execute('SELECT * FROM workflows WHERE name = ?', (name,)).fetchone()
        if row:
            result = dict(row)
            result['workflow_json'] = json.loads(result['workflow_json'])
            return result
        return None
    
    def list_workflows(self):
        return [dict(r) for r in self.conn.execute(
            'SELECT id, name, description, rating, category, created_at FROM workflows'
        ).fetchall()]
    
    def create_generation(self, prompt_id, client_id, workflow_name, prompt, 
                         negative_prompt, model, rating, country_code):
        self.conn.execute('''
            INSERT INTO generations 
            (prompt_id, client_id, workflow_name, prompt, negative_prompt, model, rating, country_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (prompt_id, client_id, workflow_name, prompt, negative_prompt, 
              model, rating, country_code))
        self.conn.commit()
    
    def update_generation(self, prompt_id, status, output_images=None, error=None):
        if status == 'completed':
            self.conn.execute('''
                UPDATE generations 
                SET status = ?, output_images = ?, completed_at = ?
                WHERE prompt_id = ?
            ''', (status, json.dumps(output_images) if output_images else None,
                  datetime.now().isoformat(), prompt_id))
        else:
            self.conn.execute('''
                UPDATE generations SET status = ?, error = ? WHERE prompt_id = ?
            ''', (status, error, prompt_id))
        self.conn.commit()
    
    def get_generation(self, prompt_id):
        row = self.conn.execute(
            'SELECT * FROM generations WHERE prompt_id = ?', (prompt_id,)
        ).fetchone()
        return dict(row) if row else None
    
    def get_stats(self):
        workflows = self.conn.execute('SELECT COUNT(*) FROM workflows').fetchone()[0]
        total_gen = self.conn.execute('SELECT COUNT(*) FROM generations').fetchone()[0]
        completed = self.conn.execute(
            'SELECT COUNT(*) FROM generations WHERE status = "completed"'
        ).fetchone()[0]
        failed = self.conn.execute(
            'SELECT COUNT(*) FROM generations WHERE status = "failed"'
        ).fetchone()[0]
        
        return {
            'workflows': workflows,
            'total_generations': total_gen,
            'completed': completed,
            'failed': failed
        }


class ComfyUIClient:
    """ComfyUI API Client"""
    
    def __init__(self, db: ComfyUIDB):
        self.db = db
        self.client_id = str(uuid.uuid4())
        self.connected = False
    
    def check_connection(self):
        """Check if ComfyUI is accessible"""
        try:
            response = httpx.get(f"{COMFYUI_API}/system_stats", timeout=5)
            self.connected = response.status_code == 200
            return {'connected': self.connected, 'stats': response.json() if self.connected else None}
        except Exception as e:
            self.connected = False
            return {'connected': False, 'error': str(e)}
    
    def get_models(self):
        """Get available models from ComfyUI"""
        try:
            response = httpx.get(f"{COMFYUI_API}/object_info/CheckpointLoaderSimple", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('CheckpointLoaderSimple', {}).get('input', {}).get('required', {}).get('ckpt_name', [[]])[0]
                return {'models': models}
            return {'error': 'Failed to get models'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_queue(self):
        """Get current queue status"""
        try:
            response = httpx.get(f"{COMFYUI_API}/queue", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {'error': 'Failed to get queue'}
        except Exception as e:
            return {'error': str(e)}
    
    def queue_prompt(self, workflow, prompt, negative_prompt, model, 
                     rating='PG', country_code='US'):
        """Queue a prompt for generation"""
        try:
            # Apply rating-based filtering to prompt
            filtered_prompt = self._filter_prompt(prompt, rating)
            filtered_negative = self._build_negative(negative_prompt, rating)
            
            # Prepare workflow with parameters
            workflow_json = self._prepare_workflow(
                workflow, filtered_prompt, filtered_negative, model
            )
            
            # Generate unique prompt ID
            prompt_id = str(uuid.uuid4())
            
            # Queue the prompt
            payload = {
                "prompt": workflow_json,
                "client_id": self.client_id
            }
            
            response = httpx.post(
                f"{COMFYUI_API}/prompt",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                actual_prompt_id = result.get('prompt_id', prompt_id)
                
                # Save to database
                self.db.create_generation(
                    actual_prompt_id, self.client_id, 'custom',
                    filtered_prompt, filtered_negative, model, rating, country_code
                )
                
                return {
                    'success': True,
                    'prompt_id': actual_prompt_id,
                    'original_prompt': prompt,
                    'filtered_prompt': filtered_prompt,
                    'rating': rating
                }
            else:
                return {'error': f'Failed to queue: {response.text}'}
        except Exception as e:
            return {'error': str(e)}
    
    def _filter_prompt(self, prompt, rating):
        """Filter prompt based on rating guardrails"""
        rating_info = RATINGS_CONFIG.get('ratings', {}).get(rating, {})
        forbidden = rating_info.get('forbidden_keywords', [])
        
        filtered = prompt
        for term in forbidden:
            if term.lower() in filtered.lower():
                # Remove forbidden term
                import re
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                filtered = pattern.sub('', filtered)
        
        return filtered.strip()
    
    def _build_negative(self, negative_prompt, rating):
        """Build negative prompt with rating-specific additions"""
        rating_info = RATINGS_CONFIG.get('ratings', {}).get(rating, {})
        guardrail_negatives = rating_info.get('guardrail_negative', '')
        
        base_negative = negative_prompt or ''
        if guardrail_negatives:
            return f"{base_negative}, {guardrail_negatives}".strip(', ')
        return base_negative
    
    def _prepare_workflow(self, workflow, prompt, negative, model):
        """Prepare workflow with actual values"""
        workflow_str = json.dumps(workflow)
        workflow_str = workflow_str.replace('{{PROMPT}}', prompt)
        workflow_str = workflow_str.replace('{{NEGATIVE}}', negative)
        workflow_str = workflow_str.replace('{{MODEL}}', model)
        return json.loads(workflow_str)
    
    def get_history(self, prompt_id):
        """Get generation history for prompt"""
        try:
            response = httpx.get(f"{COMFYUI_API}/history/{prompt_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
            return {'error': 'History not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def interrupt(self):
        """Interrupt current generation"""
        try:
            response = httpx.post(f"{COMFYUI_API}/interrupt", timeout=5)
            return {'success': response.status_code == 200}
        except Exception as e:
            return {'error': str(e)}
    
    def clear_queue(self):
        """Clear the queue"""
        try:
            response = httpx.post(
                f"{COMFYUI_API}/queue",
                json={"clear": True},
                timeout=5
            )
            return {'success': response.status_code == 200}
        except Exception as e:
            return {'error': str(e)}


# Initialize
db = ComfyUIDB()
client = ComfyUIClient(db)


class ComfyUIAPI(BaseHTTPRequestHandler):
    """ComfyUI Integration API Handler"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/':
            conn_status = client.check_connection()
            self._json({
                'service': 'ComfyUI Integration API',
                'version': '1.0',
                'comfyui_url': COMFYUI_API,
                'connected': conn_status.get('connected', False)
            })
        
        elif path == '/api/stats':
            self._json(db.get_stats())
        
        elif path == '/api/connection':
            self._json(client.check_connection())
        
        elif path == '/api/models':
            self._json(client.get_models())
        
        elif path == '/api/queue':
            self._json(client.get_queue())
        
        elif path == '/api/workflows':
            self._json(db.list_workflows())
        
        elif path.startswith('/api/workflow/'):
            name = path.split('/')[-1]
            workflow = db.get_workflow(name)
            if workflow:
                self._json(workflow)
            else:
                self._json({'error': 'Workflow not found'}, 404)
        
        elif path.startswith('/api/generation/'):
            prompt_id = path.split('/')[-1]
            gen = db.get_generation(prompt_id)
            if gen:
                self._json(gen)
            else:
                self._json({'error': 'Generation not found'}, 404)
        
        elif path.startswith('/api/history/'):
            prompt_id = path.split('/')[-1]
            self._json(client.get_history(prompt_id))
        
        elif path == '/api/generations':
            generations = [dict(r) for r in db.conn.execute(
                'SELECT * FROM generations ORDER BY created_at DESC LIMIT 50'
            ).fetchall()]
            self._json(generations)
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/generate':
            workflow_name = data.get('workflow', 'txt2img_basic')
            prompt = data.get('prompt', '')
            negative = data.get('negative_prompt', '')
            model = data.get('model', '')
            rating = data.get('rating', 'PG')
            country = data.get('country', 'US')
            
            # Get workflow
            workflow_data = db.get_workflow(workflow_name)
            if not workflow_data:
                self._json({'error': f'Workflow {workflow_name} not found'}, 404)
                return
            
            workflow = workflow_data['workflow_json']
            result = client.queue_prompt(workflow, prompt, negative, model, rating, country)
            self._json(result)
        
        elif path == '/api/workflows':
            name = data.get('name')
            workflow_json = data.get('workflow')
            description = data.get('description')
            rating = data.get('rating', 'PG')
            category = data.get('category')
            
            result = db.save_workflow(name, workflow_json, description, rating, category)
            self._json(result)
        
        elif path == '/api/interrupt':
            self._json(client.interrupt())
        
        elif path == '/api/queue/clear':
            self._json(client.clear_queue())
        
        elif path == '/api/batch':
            # Batch generation
            prompts = data.get('prompts', [])
            workflow_name = data.get('workflow', 'txt2img_basic')
            model = data.get('model', '')
            rating = data.get('rating', 'PG')
            country = data.get('country', 'US')
            
            workflow_data = db.get_workflow(workflow_name)
            if not workflow_data:
                self._json({'error': 'Workflow not found'}, 404)
                return
            
            results = []
            for item in prompts:
                prompt = item.get('prompt', '') if isinstance(item, dict) else item
                negative = item.get('negative', '') if isinstance(item, dict) else ''
                
                result = client.queue_prompt(
                    workflow_data['workflow_json'],
                    prompt, negative, model, rating, country
                )
                results.append(result)
            
            self._json({
                'batch_size': len(prompts),
                'results': results
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  COMFYUI INTEGRATION API")
    print("  Workflow Management | Generation | Queue Control")
    print("=" * 60)
    
    conn_status = client.check_connection()
    print(f"\nComfyUI URL: {COMFYUI_API}")
    print(f"Connected: {conn_status.get('connected', False)}")
    
    if not conn_status.get('connected'):
        print("  WARNING: ComfyUI not accessible. Start ComfyUI first.")
    
    stats = db.get_stats()
    print(f"\nWorkflows: {stats['workflows']}")
    print(f"Total Generations: {stats['total_generations']}")
    print(f"Completed: {stats['completed']}")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), ComfyUIAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
