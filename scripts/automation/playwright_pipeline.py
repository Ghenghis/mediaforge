"""
PLAYWRIGHT AUTOMATION PIPELINE
===============================
Browser automation for ComfyUI and content generation
Handles UI interactions, form filling, and result collection

Port: 8203
"""
import asyncio
import json
import sqlite3
import base64
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

# Configuration
PORT = 8203
DB_PATH = Path(r"c:\Users\Admin\civitai\data\automation.db")
SCREENSHOTS_DIR = Path(r"c:\Users\Admin\civitai\output\screenshots")
COMFYUI_URL = "http://127.0.0.1:8188"

# Ensure directories exist
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Try to import playwright
try:
    from playwright.sync_api import sync_playwright, Page, Browser
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: Playwright not installed. Run: pip install playwright && playwright install")


class AutomationDB:
    """Database for automation tasks and results"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                config TEXT,
                result TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                started_at TEXT,
                completed_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                prompt TEXT,
                negative_prompt TEXT,
                model TEXT,
                rating TEXT,
                country_code TEXT,
                output_path TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS pipelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                steps TEXT,
                status TEXT DEFAULT 'idle',
                last_run TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()
    
    def create_task(self, task_type, config=None):
        cursor = self.conn.execute('''
            INSERT INTO tasks (task_type, config, created_at)
            VALUES (?, ?, ?)
        ''', (task_type, json.dumps(config) if config else None, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_task(self, task_id, status, result=None, error=None):
        if status == 'running':
            self.conn.execute('''
                UPDATE tasks SET status = ?, started_at = ? WHERE id = ?
            ''', (status, datetime.now().isoformat(), task_id))
        elif status in ['completed', 'failed']:
            self.conn.execute('''
                UPDATE tasks SET status = ?, result = ?, error = ?, completed_at = ?
                WHERE id = ?
            ''', (status, json.dumps(result) if result else None, error, 
                  datetime.now().isoformat(), task_id))
        else:
            self.conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
        self.conn.commit()
    
    def get_task(self, task_id):
        row = self.conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        return dict(row) if row else None
    
    def get_pending_tasks(self):
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM tasks WHERE status = "pending" ORDER BY created_at'
        ).fetchall()]
    
    def save_screenshot(self, task_id, filename, filepath, description=None):
        self.conn.execute('''
            INSERT INTO screenshots (task_id, filename, filepath, description)
            VALUES (?, ?, ?, ?)
        ''', (task_id, filename, filepath, description))
        self.conn.commit()
    
    def create_generation(self, task_id, prompt, negative_prompt, model, rating, country_code):
        cursor = self.conn.execute('''
            INSERT INTO generations (task_id, prompt, negative_prompt, model, rating, country_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_id, prompt, negative_prompt, model, rating, country_code))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_stats(self):
        total = self.conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
        pending = self.conn.execute('SELECT COUNT(*) FROM tasks WHERE status = "pending"').fetchone()[0]
        running = self.conn.execute('SELECT COUNT(*) FROM tasks WHERE status = "running"').fetchone()[0]
        completed = self.conn.execute('SELECT COUNT(*) FROM tasks WHERE status = "completed"').fetchone()[0]
        failed = self.conn.execute('SELECT COUNT(*) FROM tasks WHERE status = "failed"').fetchone()[0]
        screenshots = self.conn.execute('SELECT COUNT(*) FROM screenshots').fetchone()[0]
        generations = self.conn.execute('SELECT COUNT(*) FROM generations').fetchone()[0]
        
        return {
            'total_tasks': total,
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed,
            'screenshots': screenshots,
            'generations': generations
        }


class PlaywrightAutomation:
    """Playwright browser automation engine"""
    
    def __init__(self, db: AutomationDB):
        self.db = db
        self.browser = None
        self.page = None
        self.playwright = None
    
    def start_browser(self, headless=True):
        """Start browser instance"""
        if not PLAYWRIGHT_AVAILABLE:
            return {'error': 'Playwright not installed'}
        
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.page = self.browser.new_page()
            return {'success': True, 'message': 'Browser started'}
        except Exception as e:
            return {'error': str(e)}
    
    def stop_browser(self):
        """Stop browser instance"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def navigate(self, url):
        """Navigate to URL"""
        if not self.page:
            return {'error': 'Browser not started'}
        
        try:
            self.page.goto(url, timeout=30000)
            return {'success': True, 'url': url, 'title': self.page.title()}
        except Exception as e:
            return {'error': str(e)}
    
    def screenshot(self, task_id, description=None):
        """Take screenshot and save"""
        if not self.page:
            return {'error': 'Browser not started'}
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{task_id}_{timestamp}.png"
            filepath = str(SCREENSHOTS_DIR / filename)
            
            self.page.screenshot(path=filepath, full_page=True)
            self.db.save_screenshot(task_id, filename, filepath, description)
            
            return {'success': True, 'filename': filename, 'filepath': filepath}
        except Exception as e:
            return {'error': str(e)}
    
    def fill_form(self, selectors_values):
        """Fill form fields"""
        if not self.page:
            return {'error': 'Browser not started'}
        
        results = []
        for selector, value in selectors_values.items():
            try:
                self.page.fill(selector, value)
                results.append({'selector': selector, 'success': True})
            except Exception as e:
                results.append({'selector': selector, 'success': False, 'error': str(e)})
        
        return {'results': results}
    
    def click(self, selector):
        """Click element"""
        if not self.page:
            return {'error': 'Browser not started'}
        
        try:
            self.page.click(selector)
            return {'success': True, 'selector': selector}
        except Exception as e:
            return {'error': str(e)}
    
    def wait_for(self, selector, timeout=30000):
        """Wait for element"""
        if not self.page:
            return {'error': 'Browser not started'}
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return {'success': True, 'selector': selector}
        except Exception as e:
            return {'error': str(e)}
    
    def get_text(self, selector):
        """Get text content of element"""
        if not self.page:
            return {'error': 'Browser not started'}
        
        try:
            element = self.page.query_selector(selector)
            if element:
                return {'success': True, 'text': element.text_content()}
            return {'error': 'Element not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def execute_script(self, script):
        """Execute JavaScript"""
        if not self.page:
            return {'error': 'Browser not started'}
        
        try:
            result = self.page.evaluate(script)
            return {'success': True, 'result': result}
        except Exception as e:
            return {'error': str(e)}
    
    # ComfyUI Specific Methods
    def comfyui_connect(self):
        """Connect to ComfyUI"""
        result = self.navigate(COMFYUI_URL)
        if 'error' in result:
            return result
        
        # Wait for ComfyUI to load
        try:
            self.page.wait_for_load_state('networkidle', timeout=15000)
            return {'success': True, 'message': 'Connected to ComfyUI'}
        except:
            return {'success': True, 'message': 'Connected (may still be loading)'}
    
    def comfyui_queue_prompt(self, workflow_json):
        """Queue a prompt in ComfyUI via API"""
        try:
            # Use fetch API to queue prompt
            script = f'''
                (async () => {{
                    const response = await fetch('/prompt', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{prompt: {json.dumps(workflow_json)}}})
                    }});
                    return await response.json();
                }})()
            '''
            result = self.page.evaluate(script)
            return {'success': True, 'result': result}
        except Exception as e:
            return {'error': str(e)}
    
    def comfyui_get_queue(self):
        """Get ComfyUI queue status"""
        try:
            script = '''
                (async () => {
                    const response = await fetch('/queue');
                    return await response.json();
                })()
            '''
            result = self.page.evaluate(script)
            return {'success': True, 'queue': result}
        except Exception as e:
            return {'error': str(e)}


# Initialize
db = AutomationDB()
automation = PlaywrightAutomation(db)


class AutomationAPI(BaseHTTPRequestHandler):
    """Automation API Handler"""
    
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
            self._json({
                'service': 'Playwright Automation API',
                'version': '1.0',
                'playwright_available': PLAYWRIGHT_AVAILABLE,
                'comfyui_url': COMFYUI_URL
            })
        
        elif path == '/api/stats':
            self._json(db.get_stats())
        
        elif path == '/api/tasks':
            tasks = [dict(r) for r in db.conn.execute(
                'SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50'
            ).fetchall()]
            self._json(tasks)
        
        elif path == '/api/tasks/pending':
            self._json(db.get_pending_tasks())
        
        elif path.startswith('/api/task/'):
            task_id = int(path.split('/')[-1])
            task = db.get_task(task_id)
            if task:
                self._json(task)
            else:
                self._json({'error': 'Task not found'}, 404)
        
        elif path == '/api/screenshots':
            screenshots = [dict(r) for r in db.conn.execute(
                'SELECT * FROM screenshots ORDER BY created_at DESC LIMIT 50'
            ).fetchall()]
            self._json(screenshots)
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/browser/start':
            headless = data.get('headless', True)
            result = automation.start_browser(headless)
            self._json(result)
        
        elif path == '/api/browser/stop':
            result = automation.stop_browser()
            self._json(result)
        
        elif path == '/api/navigate':
            url = data.get('url', '')
            result = automation.navigate(url)
            self._json(result)
        
        elif path == '/api/screenshot':
            task_id = data.get('task_id', 0)
            description = data.get('description')
            result = automation.screenshot(task_id, description)
            self._json(result)
        
        elif path == '/api/click':
            selector = data.get('selector', '')
            result = automation.click(selector)
            self._json(result)
        
        elif path == '/api/fill':
            selectors_values = data.get('fields', {})
            result = automation.fill_form(selectors_values)
            self._json(result)
        
        elif path == '/api/wait':
            selector = data.get('selector', '')
            timeout = data.get('timeout', 30000)
            result = automation.wait_for(selector, timeout)
            self._json(result)
        
        elif path == '/api/script':
            script = data.get('script', '')
            result = automation.execute_script(script)
            self._json(result)
        
        # ComfyUI specific endpoints
        elif path == '/api/comfyui/connect':
            result = automation.comfyui_connect()
            self._json(result)
        
        elif path == '/api/comfyui/queue':
            workflow = data.get('workflow', {})
            result = automation.comfyui_queue_prompt(workflow)
            self._json(result)
        
        elif path == '/api/comfyui/status':
            result = automation.comfyui_get_queue()
            self._json(result)
        
        # Task management
        elif path == '/api/tasks/create':
            task_type = data.get('type', 'generic')
            config = data.get('config')
            task_id = db.create_task(task_type, config)
            self._json({'task_id': task_id})
        
        elif path == '/api/tasks/update':
            task_id = data.get('task_id')
            status = data.get('status')
            result = data.get('result')
            error = data.get('error')
            db.update_task(task_id, status, result, error)
            self._json({'success': True})
        
        # Pipeline execution
        elif path == '/api/pipeline/generate':
            # Full generation pipeline
            prompt = data.get('prompt', '')
            negative_prompt = data.get('negative_prompt', '')
            model = data.get('model', 'default')
            rating = data.get('rating', 'PG')
            country_code = data.get('country', 'US')
            
            # Create task
            task_id = db.create_task('generation', {
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'model': model,
                'rating': rating,
                'country_code': country_code
            })
            
            # Create generation record
            gen_id = db.create_generation(
                task_id, prompt, negative_prompt, model, rating, country_code
            )
            
            self._json({
                'task_id': task_id,
                'generation_id': gen_id,
                'status': 'queued',
                'message': 'Generation task created'
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  PLAYWRIGHT AUTOMATION API")
    print("  Browser Automation | ComfyUI Integration")
    print("=" * 60)
    
    print(f"\nPlaywright Available: {PLAYWRIGHT_AVAILABLE}")
    if not PLAYWRIGHT_AVAILABLE:
        print("  Install: pip install playwright && playwright install chromium")
    
    stats = db.get_stats()
    print(f"\nTasks: {stats['total_tasks']} (Pending: {stats['pending']})")
    print(f"Screenshots: {stats['screenshots']}")
    print(f"Generations: {stats['generations']}")
    
    print(f"\nComfyUI URL: {COMFYUI_URL}")
    print(f"Screenshots Dir: {SCREENSHOTS_DIR}")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), AutomationAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
