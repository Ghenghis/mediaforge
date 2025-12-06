"""
WORKFLOW MANAGER
==================
Loads, manages, and runs ComfyUI workflows
Persists user preferences and favorites

Port: 8221
"""
import json
import sqlite3
import requests
import re
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configuration
PORT = 8221
COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_DIR = Path(r"G:\Github\ComfyUI\user\default\workflows")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\workflows.db")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\output\comfyui")

# Ensure directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class WorkflowDB:
    """Database for workflow preferences and history"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                favorite INTEGER DEFAULT 0,
                use_count INTEGER DEFAULT 0,
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS workflow_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER,
                prompt TEXT,
                negative_prompt TEXT,
                settings TEXT,
                output_path TEXT,
                status TEXT DEFAULT 'pending',
                prompt_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS user_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER,
                name TEXT NOT NULL,
                settings TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()
    
    def register_workflow(self, filename, name, description=None, category=None):
        self.conn.execute('''
            INSERT OR IGNORE INTO workflows (filename, name, description, category)
            VALUES (?, ?, ?, ?)
        ''', (filename, name, description, category))
        self.conn.commit()
    
    def get_workflow(self, filename):
        row = self.conn.execute(
            'SELECT * FROM workflows WHERE filename = ?', (filename,)
        ).fetchone()
        return dict(row) if row else None
    
    def get_all_workflows(self):
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM workflows ORDER BY favorite DESC, use_count DESC'
        ).fetchall()]
    
    def set_favorite(self, filename, favorite):
        self.conn.execute(
            'UPDATE workflows SET favorite = ? WHERE filename = ?',
            (1 if favorite else 0, filename)
        )
        self.conn.commit()
    
    def increment_use(self, filename):
        self.conn.execute('''
            UPDATE workflows SET use_count = use_count + 1, last_used = ?
            WHERE filename = ?
        ''', (datetime.now().isoformat(), filename))
        self.conn.commit()
    
    def log_run(self, workflow_id, prompt, negative_prompt, settings, prompt_id):
        cursor = self.conn.execute('''
            INSERT INTO workflow_runs (workflow_id, prompt, negative_prompt, settings, prompt_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (workflow_id, prompt, negative_prompt, json.dumps(settings), prompt_id))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_run(self, run_id, **kwargs):
        sets = ', '.join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(f'UPDATE workflow_runs SET {sets} WHERE id = ?',
                         list(kwargs.values()) + [run_id])
        self.conn.commit()
    
    def get_runs(self, limit=50):
        return [dict(r) for r in self.conn.execute('''
            SELECT r.*, w.name as workflow_name 
            FROM workflow_runs r
            LEFT JOIN workflows w ON r.workflow_id = w.id
            ORDER BY r.created_at DESC LIMIT ?
        ''', (limit,)).fetchall()]
    
    def save_preset(self, workflow_id, name, settings):
        self.conn.execute('''
            INSERT INTO user_presets (workflow_id, name, settings)
            VALUES (?, ?, ?)
        ''', (workflow_id, name, json.dumps(settings)))
        self.conn.commit()
    
    def get_presets(self, workflow_id=None):
        if workflow_id:
            return [dict(r) for r in self.conn.execute(
                'SELECT * FROM user_presets WHERE workflow_id = ?', (workflow_id,)
            ).fetchall()]
        return [dict(r) for r in self.conn.execute('SELECT * FROM user_presets').fetchall()]


class WorkflowLoader:
    """Load and parse ComfyUI workflows"""
    
    def __init__(self, workflow_dir: Path):
        self.workflow_dir = workflow_dir
    
    def list_workflows(self):
        """List all available workflow files"""
        if not self.workflow_dir.exists():
            return []
        
        workflows = []
        for f in sorted(self.workflow_dir.glob("*.json")):
            workflows.append({
                "filename": f.name,
                "name": self._parse_name(f.name),
                "path": str(f),
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
        return workflows
    
    def _parse_name(self, filename):
        """Convert filename to display name"""
        name = filename.replace(".json", "")
        # Remove number prefix like "01_"
        name = re.sub(r'^\d+_', '', name)
        # Replace underscores with spaces
        name = name.replace("_", " ")
        return name
    
    def load_workflow(self, filename):
        """Load workflow JSON (handles both frontend and API formats)"""
        path = self.workflow_dir / filename
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if this is frontend format (has 'nodes' array)
        if 'nodes' in data and isinstance(data['nodes'], list):
            return self._convert_to_api_format(data)
        
        # Already in API format
        return data
    
    def _convert_to_api_format(self, frontend_workflow):
        """Convert ComfyUI frontend format to API format"""
        api_workflow = {}
        nodes = frontend_workflow.get('nodes', [])
        links = frontend_workflow.get('links', [])
        
        # Build link map: link_id -> (from_node, from_slot)
        link_map = {}
        for link in links:
            if len(link) >= 5:
                link_id, from_node, from_slot, to_node, to_slot = link[:5]
                link_map[link_id] = (from_node, from_slot)
        
        for node in nodes:
            node_id = str(node.get('id'))
            class_type = node.get('type')
            
            if not class_type:
                continue
            
            inputs = {}
            widgets = node.get('widgets_values', [])
            
            # Node-specific widget handling
            if class_type == 'CheckpointLoaderSimple' and widgets:
                inputs['ckpt_name'] = widgets[0]
            elif class_type in ['CLIPTextEncode', 'CLIPTextEncodeSDXL'] and widgets:
                inputs['text'] = widgets[0]
            elif class_type == 'EmptyLatentImage' and len(widgets) >= 3:
                inputs['width'] = widgets[0]
                inputs['height'] = widgets[1]
                inputs['batch_size'] = widgets[2]
            elif class_type == 'KSampler' and len(widgets) >= 6:
                inputs['seed'] = widgets[0]
                inputs['control_after_generate'] = widgets[1]
                inputs['steps'] = widgets[2]
                inputs['cfg'] = widgets[3]
                inputs['sampler_name'] = widgets[4]
                inputs['scheduler'] = widgets[5]
                inputs['denoise'] = widgets[6] if len(widgets) > 6 else 1.0
            elif class_type == 'KSamplerAdvanced' and len(widgets) >= 8:
                inputs['add_noise'] = widgets[0]
                inputs['noise_seed'] = widgets[1]
                inputs['control_after_generate'] = widgets[2]
                inputs['steps'] = widgets[3]
                inputs['cfg'] = widgets[4]
                inputs['sampler_name'] = widgets[5]
                inputs['scheduler'] = widgets[6]
                inputs['start_at_step'] = widgets[7]
                inputs['end_at_step'] = widgets[8] if len(widgets) > 8 else 10000
                inputs['return_with_leftover_noise'] = widgets[9] if len(widgets) > 9 else 'disable'
            elif class_type == 'LoraLoader' and len(widgets) >= 3:
                inputs['lora_name'] = widgets[0]
                inputs['strength_model'] = widgets[1]
                inputs['strength_clip'] = widgets[2]
            elif class_type == 'SaveImage' and widgets:
                inputs['filename_prefix'] = widgets[0]
            elif class_type == 'LoadImage' and widgets:
                inputs['image'] = widgets[0]
            # VAEDecode, VAEEncode etc have no widgets, only connections
            
            # Add all link connections
            for inp in node.get('inputs', []):
                link_id = inp.get('link')
                if link_id and link_id in link_map:
                    from_node, from_slot = link_map[link_id]
                    inputs[inp['name']] = [str(from_node), from_slot]
            
            api_workflow[node_id] = {
                'class_type': class_type,
                'inputs': inputs
            }
        
        return api_workflow
    
    def get_workflow_info(self, filename):
        """Get workflow info including editable fields"""
        path = self.workflow_dir / filename
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        info = {
            "filename": filename,
            "name": self._parse_name(filename),
            "format": "frontend" if 'nodes' in raw_data else "api",
            "nodes": [],
            "editable_fields": []
        }
        
        # Parse frontend format
        if 'nodes' in raw_data and isinstance(raw_data['nodes'], list):
            for node in raw_data['nodes']:
                node_id = node.get('id')
                class_type = node.get('type', '')
                widgets = node.get('widgets_values', [])
                
                info["nodes"].append({
                    "id": node_id,
                    "type": class_type,
                    "title": node.get('title', class_type)
                })
                
                # Find editable text fields (prompts)
                if class_type in ['CLIPTextEncode', 'CLIPTextEncodeSDXL']:
                    is_negative = 'negative' in node.get('title', '').lower()
                    info["editable_fields"].append({
                        "node_id": node_id,
                        "field": "text",
                        "type": "text",
                        "current_value": widgets[0] if widgets else "",
                        "node_type": class_type,
                        "is_negative": is_negative
                    })
                
                # Find KSampler for seed/steps/cfg
                if class_type == 'KSampler' and len(widgets) >= 6:
                    info["editable_fields"].append({
                        "node_id": node_id,
                        "field": "seed",
                        "type": "number",
                        "current_value": widgets[0],
                        "node_type": class_type
                    })
                    info["editable_fields"].append({
                        "node_id": node_id,
                        "field": "steps",
                        "type": "number",
                        "current_value": widgets[2],
                        "node_type": class_type
                    })
                    info["editable_fields"].append({
                        "node_id": node_id,
                        "field": "cfg",
                        "type": "number",
                        "current_value": widgets[3],
                        "node_type": class_type
                    })
                
                # Find dimensions
                if class_type == 'EmptyLatentImage' and len(widgets) >= 2:
                    info["editable_fields"].append({
                        "node_id": node_id,
                        "field": "width",
                        "type": "number",
                        "current_value": widgets[0],
                        "node_type": class_type
                    })
                    info["editable_fields"].append({
                        "node_id": node_id,
                        "field": "height",
                        "type": "number",
                        "current_value": widgets[1],
                        "node_type": class_type
                    })
        else:
            # Parse API format
            for node_id, node in raw_data.items():
                if not isinstance(node, dict):
                    continue
                
                class_type = node.get("class_type", "")
                inputs = node.get("inputs", {})
                
                info["nodes"].append({
                    "id": node_id,
                    "type": class_type
                })
                
                if "text" in inputs:
                    info["editable_fields"].append({
                        "node_id": node_id,
                        "field": "text",
                        "type": "text",
                        "current_value": inputs.get("text", ""),
                        "node_type": class_type
                    })
                
                if "seed" in inputs:
                    info["editable_fields"].append({
                        "node_id": node_id,
                        "field": "seed",
                        "type": "number",
                        "current_value": inputs.get("seed", -1),
                        "node_type": class_type
                    })
            
            # Find dimension inputs
            for dim in ["width", "height"]:
                if dim in inputs:
                    info["editable_fields"].append({
                        "node_id": node_id,
                        "field": dim,
                        "type": "number",
                        "current_value": inputs.get(dim, 512),
                        "node_type": class_type
                    })
        
        return info


class ComfyUIRunner:
    """Execute workflows on ComfyUI"""
    
    def __init__(self, comfyui_url: str):
        self.url = comfyui_url
    
    def is_available(self):
        try:
            r = requests.get(f"{self.url}/system_stats", timeout=5)
            return r.status_code == 200
        except:
            return False
    
    def run_workflow(self, workflow, overrides=None):
        """Execute a workflow with optional overrides"""
        if overrides:
            workflow = self._apply_overrides(workflow, overrides)
        
        try:
            response = requests.post(
                f"{self.url}/prompt",
                json={"prompt": workflow},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get("prompt_id")
            else:
                return False, f"Error: {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def _apply_overrides(self, workflow, overrides):
        """Apply user overrides to workflow"""
        workflow = workflow.copy()
        
        for override in overrides:
            node_id = str(override.get("node_id"))
            field = override.get("field")
            value = override.get("value")
            
            if node_id in workflow and field:
                if "inputs" in workflow[node_id]:
                    workflow[node_id]["inputs"][field] = value
        
        return workflow
    
    def get_queue(self):
        """Get current queue status"""
        try:
            r = requests.get(f"{self.url}/queue", timeout=5)
            return r.json() if r.status_code == 200 else None
        except:
            return None
    
    def get_history(self, prompt_id=None):
        """Get generation history"""
        try:
            url = f"{self.url}/history"
            if prompt_id:
                url += f"/{prompt_id}"
            r = requests.get(url, timeout=5)
            return r.json() if r.status_code == 200 else None
        except:
            return None


# Initialize components
db = WorkflowDB()
loader = WorkflowLoader(WORKFLOW_DIR)
runner = ComfyUIRunner(COMFYUI_URL)


def sync_workflows():
    """Sync filesystem workflows to database"""
    for wf in loader.list_workflows():
        info = loader.get_workflow_info(wf["filename"])
        category = None
        
        # Auto-categorize based on name
        name_lower = wf["filename"].lower()
        if "anime" in name_lower or "illustrious" in name_lower:
            category = "anime"
        elif "realistic" in name_lower or "photo" in name_lower:
            category = "realistic"
        elif "tribal" in name_lower:
            category = "tribal"
        elif "pony" in name_lower:
            category = "pony"
        elif "tagger" in name_lower:
            category = "utility"
        elif "lora" in name_lower:
            category = "lora"
        
        db.register_workflow(
            wf["filename"],
            wf["name"],
            description=f"{len(info['nodes']) if info else 0} nodes",
            category=category
        )


class WorkflowAPI(BaseHTTPRequestHandler):
    """Workflow Manager API"""
    
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
        self._json({})
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        if path == '/':
            self._json({
                'service': 'Workflow Manager',
                'version': '1.0',
                'port': PORT,
                'comfyui_available': runner.is_available(),
                'workflow_count': len(loader.list_workflows())
            })
        
        elif path == '/api/workflows':
            # List all workflows with database info
            files = {wf["filename"]: wf for wf in loader.list_workflows()}
            db_records = {wf["filename"]: wf for wf in db.get_all_workflows()}
            
            workflows = []
            for filename, file_info in files.items():
                db_info = db_records.get(filename, {})
                workflows.append({
                    **file_info,
                    "favorite": db_info.get("favorite", 0),
                    "use_count": db_info.get("use_count", 0),
                    "last_used": db_info.get("last_used"),
                    "category": db_info.get("category")
                })
            
            self._json({'workflows': workflows})
        
        elif path.startswith('/api/workflow/'):
            filename = path.split('/')[-1]
            if not filename.endswith('.json'):
                filename += '.json'
            
            info = loader.get_workflow_info(filename)
            if info:
                db_info = db.get_workflow(filename)
                if db_info:
                    info.update({
                        "favorite": db_info.get("favorite", 0),
                        "use_count": db_info.get("use_count", 0),
                        "category": db_info.get("category")
                    })
                self._json(info)
            else:
                self._json({'error': 'Workflow not found'}, 404)
        
        elif path == '/api/history':
            self._json({'runs': db.get_runs()})
        
        elif path == '/api/queue':
            queue = runner.get_queue()
            self._json({'queue': queue})
        
        elif path == '/api/presets':
            workflow_id = params.get('workflow_id', [None])[0]
            presets = db.get_presets(int(workflow_id) if workflow_id else None)
            self._json({'presets': presets})
        
        elif path == '/api/categories':
            workflows = db.get_all_workflows()
            categories = {}
            for wf in workflows:
                cat = wf.get("category") or "uncategorized"
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(wf["filename"])
            self._json({'categories': categories})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/run':
            # Run a workflow
            filename = data.get('workflow')
            if not filename:
                self._json({'success': False, 'error': 'Workflow filename required'})
                return
            
            if not filename.endswith('.json'):
                filename += '.json'
            
            workflow = loader.load_workflow(filename)
            if not workflow:
                self._json({'success': False, 'error': 'Workflow not found'})
                return
            
            if not runner.is_available():
                self._json({'success': False, 'error': 'ComfyUI not available'})
                return
            
            # Apply overrides if provided
            overrides = data.get('overrides', [])
            
            # Quick override for common fields
            if 'prompt' in data:
                # Find first text node and override
                info = loader.get_workflow_info(filename)
                for field in info.get('editable_fields', []):
                    if field['type'] == 'text' and 'positive' in field.get('node_type', '').lower():
                        overrides.append({
                            'node_id': field['node_id'],
                            'field': field['field'],
                            'value': data['prompt']
                        })
                        break
            
            if 'negative_prompt' in data:
                info = loader.get_workflow_info(filename)
                for field in info.get('editable_fields', []):
                    if field['type'] == 'text' and 'negative' in field.get('node_type', '').lower():
                        overrides.append({
                            'node_id': field['node_id'],
                            'field': field['field'],
                            'value': data['negative_prompt']
                        })
                        break
            
            if 'seed' in data:
                info = loader.get_workflow_info(filename)
                for field in info.get('editable_fields', []):
                    if field['field'] == 'seed':
                        overrides.append({
                            'node_id': field['node_id'],
                            'field': 'seed',
                            'value': data['seed']
                        })
            
            # Run workflow
            success, result = runner.run_workflow(workflow, overrides if overrides else None)
            
            if success:
                # Log to database
                db_wf = db.get_workflow(filename)
                if db_wf:
                    db.increment_use(filename)
                    db.log_run(
                        db_wf['id'],
                        data.get('prompt', ''),
                        data.get('negative_prompt', ''),
                        data.get('overrides', {}),
                        result
                    )
                
                self._json({
                    'success': True,
                    'prompt_id': result,
                    'message': f'Workflow {filename} queued'
                })
            else:
                self._json({'success': False, 'error': result})
        
        elif path == '/api/favorite':
            filename = data.get('workflow')
            favorite = data.get('favorite', True)
            
            if filename:
                if not filename.endswith('.json'):
                    filename += '.json'
                db.set_favorite(filename, favorite)
                self._json({'success': True})
            else:
                self._json({'success': False, 'error': 'Workflow required'})
        
        elif path == '/api/preset':
            workflow = data.get('workflow')
            name = data.get('name')
            settings = data.get('settings')
            
            if all([workflow, name, settings]):
                db_wf = db.get_workflow(workflow)
                if db_wf:
                    db.save_preset(db_wf['id'], name, settings)
                    self._json({'success': True})
                else:
                    self._json({'success': False, 'error': 'Workflow not found'})
            else:
                self._json({'success': False, 'error': 'workflow, name, and settings required'})
        
        elif path == '/api/batch':
            # Run same workflow multiple times with variations
            filename = data.get('workflow')
            count = data.get('count', 1)
            prompts = data.get('prompts', [])
            
            if not filename:
                self._json({'success': False, 'error': 'Workflow required'})
                return
            
            results = []
            for i in range(count):
                prompt = prompts[i] if i < len(prompts) else data.get('prompt', '')
                run_data = {
                    'workflow': filename,
                    'prompt': prompt,
                    'seed': data.get('seed', -1)  # -1 = random
                }
                
                workflow = loader.load_workflow(filename if filename.endswith('.json') else filename + '.json')
                if workflow:
                    success, result = runner.run_workflow(workflow)
                    results.append({'index': i, 'success': success, 'prompt_id': result})
            
            self._json({'success': True, 'results': results})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  WORKFLOW MANAGER")
    print("  ComfyUI Workflow Loader & Runner")
    print("=" * 60)
    
    # Sync workflows to database
    print("\nSyncing workflows...")
    sync_workflows()
    
    workflows = loader.list_workflows()
    print(f"Found {len(workflows)} workflows:")
    for wf in workflows:
        print(f"  - {wf['name']}")
    
    print(f"\nComfyUI: {'Available' if runner.is_available() else 'Not running'}")
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), WorkflowAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
