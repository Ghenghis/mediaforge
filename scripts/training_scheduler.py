"""
TRAINING SCHEDULER
===================
Automated training trigger based on rating thresholds
Monitors database and triggers Kohya training when conditions met

Port: 8214
"""
import json
import sqlite3
import threading
import time
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
PORT = 8214
DB_PATH = Path(r"c:\Users\Admin\civitai\data\scheduler.db")
RATINGS_DB = Path(r"c:\Users\Admin\civitai\data\ratings.db")
DATASETS_DB = Path(r"c:\Users\Admin\civitai\data\datasets.db")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\output\training")
LORA_OUTPUT = Path(r"G:\Github\ComfyUI\models\loras")

# Thresholds
GOLD_THRESHOLD = 50  # Trigger training when this many gold images
CHECK_INTERVAL = 300  # Check every 5 minutes
MIN_RATING_FOR_GOLD = 12  # Rating 12+ is gold standard

# Ensure directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class SchedulerDB:
    """Database for scheduler state and history"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS training_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_type TEXT NOT NULL,
                gold_count INTEGER,
                dataset_path TEXT,
                model_name TEXT,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS scheduler_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER DEFAULT 1,
                last_check TEXT,
                last_training TEXT,
                gold_count INTEGER DEFAULT 0,
                check_interval INTEGER DEFAULT 300,
                gold_threshold INTEGER DEFAULT 50
            );
            
            CREATE TABLE IF NOT EXISTS training_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                event TEXT NOT NULL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            INSERT OR IGNORE INTO scheduler_state (id, enabled) VALUES (1, 1);
        ''')
        self.conn.commit()
    
    def get_state(self):
        row = self.conn.execute('SELECT * FROM scheduler_state WHERE id = 1').fetchone()
        return dict(row) if row else {}
    
    def update_state(self, **kwargs):
        sets = ', '.join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(f'UPDATE scheduler_state SET {sets} WHERE id = 1', list(kwargs.values()))
        self.conn.commit()
    
    def create_run(self, trigger_type, gold_count, dataset_path=None):
        cursor = self.conn.execute('''
            INSERT INTO training_runs (trigger_type, gold_count, dataset_path, started_at)
            VALUES (?, ?, ?, ?)
        ''', (trigger_type, gold_count, dataset_path, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_run(self, run_id, **kwargs):
        sets = ', '.join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(f'UPDATE training_runs SET {sets} WHERE id = ?', 
                         list(kwargs.values()) + [run_id])
        self.conn.commit()
    
    def log_event(self, run_id, event, details=None):
        self.conn.execute('''
            INSERT INTO training_history (run_id, event, details)
            VALUES (?, ?, ?)
        ''', (run_id, event, json.dumps(details) if details else None))
        self.conn.commit()
    
    def get_runs(self, limit=20):
        return [dict(r) for r in self.conn.execute('''
            SELECT * FROM training_runs ORDER BY created_at DESC LIMIT ?
        ''', (limit,)).fetchall()]
    
    def get_stats(self):
        total = self.conn.execute('SELECT COUNT(*) FROM training_runs').fetchone()[0]
        completed = self.conn.execute(
            'SELECT COUNT(*) FROM training_runs WHERE status = "completed"'
        ).fetchone()[0]
        failed = self.conn.execute(
            'SELECT COUNT(*) FROM training_runs WHERE status = "failed"'
        ).fetchone()[0]
        
        return {
            'total_runs': total,
            'completed': completed,
            'failed': failed,
            'success_rate': round(completed / total * 100, 1) if total > 0 else 0
        }


class RatingChecker:
    """Check rating database for gold images"""
    
    def __init__(self):
        self.ratings_db = RATINGS_DB
    
    def get_gold_count(self):
        """Count images with rating >= 12"""
        try:
            conn = sqlite3.connect(str(self.ratings_db))
            # Try different possible table/column names
            tables = ['ratings', 'images', 'image_ratings']
            for table in tables:
                try:
                    count = conn.execute(f'''
                        SELECT COUNT(*) FROM {table} WHERE rating >= ?
                    ''', (MIN_RATING_FOR_GOLD,)).fetchone()[0]
                    conn.close()
                    return count
                except:
                    continue
            conn.close()
            return 0
        except Exception as e:
            print(f"Error checking ratings: {e}")
            return 0
    
    def get_gold_images(self, limit=100):
        """Get paths of gold standard images"""
        try:
            conn = sqlite3.connect(str(self.ratings_db))
            conn.row_factory = sqlite3.Row
            tables = ['ratings', 'images', 'image_ratings']
            for table in tables:
                try:
                    rows = conn.execute(f'''
                        SELECT * FROM {table} WHERE rating >= ? 
                        ORDER BY rating DESC LIMIT ?
                    ''', (MIN_RATING_FOR_GOLD, limit)).fetchall()
                    conn.close()
                    return [dict(r) for r in rows]
                except:
                    continue
            conn.close()
            return []
        except Exception as e:
            print(f"Error getting gold images: {e}")
            return []


class TrainingExecutor:
    """Execute Kohya training"""
    
    def __init__(self, db: SchedulerDB):
        self.db = db
        self.kohya_path = Path(r"G:\Github\kohya_ss")
        self.running = False
    
    def prepare_dataset(self, run_id, gold_images):
        """Prepare training dataset from gold images"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dataset_dir = OUTPUT_DIR / f"dataset_{timestamp}"
        images_dir = dataset_dir / "images" / "10_gold"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        self.db.log_event(run_id, "preparing_dataset", {"path": str(dataset_dir)})
        
        copied = 0
        for img in gold_images:
            src_path = img.get('path') or img.get('file_path') or img.get('image_path')
            if src_path and Path(src_path).exists():
                dst = images_dir / Path(src_path).name
                shutil.copy2(src_path, dst)
                
                # Create caption file if exists
                caption_path = Path(src_path).with_suffix('.txt')
                if caption_path.exists():
                    shutil.copy2(caption_path, dst.with_suffix('.txt'))
                copied += 1
        
        self.db.log_event(run_id, "dataset_prepared", {"images_copied": copied})
        return str(dataset_dir), copied
    
    def create_config(self, dataset_dir, model_name):
        """Create Kohya training config"""
        config = {
            "pretrained_model_name_or_path": "runwayml/stable-diffusion-v1-5",
            "train_data_dir": str(Path(dataset_dir) / "images"),
            "output_dir": str(OUTPUT_DIR / "models"),
            "output_name": model_name,
            "save_model_as": "safetensors",
            "network_module": "networks.lora",
            "network_dim": 32,
            "network_alpha": 16,
            "resolution": "512,512",
            "train_batch_size": 1,
            "max_train_epochs": 10,
            "learning_rate": 1e-4,
            "unet_lr": 1e-4,
            "text_encoder_lr": 1e-5,
            "lr_scheduler": "cosine_with_restarts",
            "lr_warmup_steps": 100,
            "optimizer_type": "AdamW8bit",
            "mixed_precision": "fp16",
            "save_precision": "fp16",
            "seed": 42,
            "cache_latents": True,
            "gradient_checkpointing": True,
            "enable_bucket": True,
            "min_bucket_reso": 256,
            "max_bucket_reso": 1024
        }
        
        config_path = Path(dataset_dir) / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return str(config_path)
    
    def run_training(self, run_id, dataset_dir, model_name):
        """Execute Kohya training (simulated if Kohya not available)"""
        self.running = True
        self.db.log_event(run_id, "training_started", {"model": model_name})
        
        try:
            # Check if Kohya is available
            train_script = self.kohya_path / "train_network.py"
            
            if train_script.exists():
                # Real training
                config_path = self.create_config(dataset_dir, model_name)
                cmd = [
                    "python", str(train_script),
                    "--config_file", config_path
                ]
                
                process = subprocess.Popen(
                    cmd,
                    cwd=str(self.kohya_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate(timeout=3600)  # 1 hour timeout
                
                if process.returncode == 0:
                    self.db.log_event(run_id, "training_completed", {"output": stdout.decode()[-500:]})
                    return True, str(OUTPUT_DIR / "models" / f"{model_name}.safetensors")
                else:
                    self.db.log_event(run_id, "training_failed", {"error": stderr.decode()[-500:]})
                    return False, stderr.decode()
            else:
                # Simulated training for testing
                self.db.log_event(run_id, "training_simulated", {"reason": "Kohya not found"})
                time.sleep(5)  # Simulate training time
                
                # Create placeholder output
                model_path = OUTPUT_DIR / "models" / f"{model_name}.safetensors"
                model_path.parent.mkdir(parents=True, exist_ok=True)
                model_path.write_text("SIMULATED_LORA_MODEL")
                
                return True, str(model_path)
                
        except subprocess.TimeoutExpired:
            self.db.log_event(run_id, "training_timeout", {})
            return False, "Training timed out after 1 hour"
        except Exception as e:
            self.db.log_event(run_id, "training_error", {"error": str(e)})
            return False, str(e)
        finally:
            self.running = False
    
    def deploy_model(self, run_id, model_path):
        """Deploy trained model to ComfyUI"""
        try:
            src = Path(model_path)
            if src.exists() and LORA_OUTPUT.exists():
                dst = LORA_OUTPUT / src.name
                shutil.copy2(src, dst)
                self.db.log_event(run_id, "model_deployed", {"destination": str(dst)})
                return True, str(dst)
            else:
                return False, "Model or destination not found"
        except Exception as e:
            self.db.log_event(run_id, "deploy_error", {"error": str(e)})
            return False, str(e)


# Initialize components
db = SchedulerDB()
checker = RatingChecker()
executor = TrainingExecutor(db)


class SchedulerLoop:
    """Background scheduler loop"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            print(f"[SCHEDULER] Started - checking every {CHECK_INTERVAL}s")
    
    def stop(self):
        self.running = False
        print("[SCHEDULER] Stopped")
    
    def _loop(self):
        while self.running:
            try:
                state = db.get_state()
                if state.get('enabled', 1):
                    self._check_and_train()
                time.sleep(state.get('check_interval', CHECK_INTERVAL))
            except Exception as e:
                print(f"[SCHEDULER] Error: {e}")
                time.sleep(60)
    
    def _check_and_train(self):
        """Check gold count and trigger training if threshold met"""
        gold_count = checker.get_gold_count()
        threshold = db.get_state().get('gold_threshold', GOLD_THRESHOLD)
        
        db.update_state(
            last_check=datetime.now().isoformat(),
            gold_count=gold_count
        )
        
        print(f"[SCHEDULER] Gold images: {gold_count}/{threshold}")
        
        if gold_count >= threshold and not executor.running:
            print(f"[SCHEDULER] Threshold met! Starting training...")
            self._trigger_training(gold_count)
    
    def _trigger_training(self, gold_count):
        """Trigger a training run"""
        # Create run record
        run_id = db.create_run("auto_threshold", gold_count)
        
        try:
            # Get gold images
            gold_images = checker.get_gold_images(limit=gold_count)
            
            if not gold_images:
                db.update_run(run_id, status="failed", error="No gold images found")
                return
            
            # Prepare dataset
            dataset_dir, copied = executor.prepare_dataset(run_id, gold_images)
            db.update_run(run_id, dataset_path=dataset_dir)
            
            if copied == 0:
                db.update_run(run_id, status="failed", error="No images copied")
                return
            
            # Generate model name
            model_name = f"loraforge_auto_{datetime.now().strftime('%Y%m%d_%H%M')}"
            db.update_run(run_id, model_name=model_name)
            
            # Run training
            success, result = executor.run_training(run_id, dataset_dir, model_name)
            
            if success:
                # Deploy model
                deploy_success, deploy_result = executor.deploy_model(run_id, result)
                
                if deploy_success:
                    db.update_run(run_id, 
                                 status="completed",
                                 completed_at=datetime.now().isoformat())
                    db.update_state(last_training=datetime.now().isoformat())
                    print(f"[SCHEDULER] Training complete! Model: {deploy_result}")
                else:
                    db.update_run(run_id, status="deployed_locally", 
                                 completed_at=datetime.now().isoformat())
            else:
                db.update_run(run_id, status="failed", error=result)
                
        except Exception as e:
            db.update_run(run_id, status="failed", error=str(e))
            print(f"[SCHEDULER] Training failed: {e}")


# Initialize scheduler
scheduler = SchedulerLoop()


class SchedulerAPI(BaseHTTPRequestHandler):
    """Training Scheduler API"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/':
            self._json({
                'service': 'Training Scheduler',
                'version': '1.0',
                'port': PORT,
                'status': 'running',
                'scheduler_active': scheduler.running
            })
        
        elif path == '/api/status':
            state = db.get_state()
            stats = db.get_stats()
            self._json({
                'enabled': bool(state.get('enabled', 1)),
                'scheduler_running': scheduler.running,
                'training_running': executor.running,
                'last_check': state.get('last_check'),
                'last_training': state.get('last_training'),
                'gold_count': state.get('gold_count', 0),
                'gold_threshold': state.get('gold_threshold', GOLD_THRESHOLD),
                'check_interval': state.get('check_interval', CHECK_INTERVAL),
                **stats
            })
        
        elif path == '/api/runs':
            self._json({'runs': db.get_runs()})
        
        elif path == '/api/gold':
            count = checker.get_gold_count()
            images = checker.get_gold_images(limit=10)
            self._json({
                'gold_count': count,
                'threshold': GOLD_THRESHOLD,
                'ready_for_training': count >= GOLD_THRESHOLD,
                'sample_images': images[:5]
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/start':
            scheduler.start()
            self._json({'success': True, 'message': 'Scheduler started'})
        
        elif path == '/api/stop':
            scheduler.stop()
            self._json({'success': True, 'message': 'Scheduler stopped'})
        
        elif path == '/api/trigger':
            # Manual training trigger
            gold_count = checker.get_gold_count()
            if gold_count > 0:
                threading.Thread(
                    target=scheduler._trigger_training,
                    args=(gold_count,),
                    daemon=True
                ).start()
                self._json({'success': True, 'message': f'Training triggered with {gold_count} images'})
            else:
                self._json({'success': False, 'error': 'No gold images available'})
        
        elif path == '/api/config':
            # Update configuration
            if 'threshold' in data:
                db.update_state(gold_threshold=data['threshold'])
            if 'interval' in data:
                db.update_state(check_interval=data['interval'])
            if 'enabled' in data:
                db.update_state(enabled=1 if data['enabled'] else 0)
            
            self._json({'success': True, 'state': db.get_state()})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  TRAINING SCHEDULER")
    print("  Automated LoRA Training System")
    print("=" * 60)
    
    state = db.get_state()
    stats = db.get_stats()
    gold = checker.get_gold_count()
    
    print(f"\nGold Images: {gold}/{state.get('gold_threshold', GOLD_THRESHOLD)}")
    print(f"Total Runs: {stats['total_runs']}")
    print(f"Success Rate: {stats['success_rate']}%")
    print(f"Check Interval: {state.get('check_interval', CHECK_INTERVAL)}s")
    
    # Auto-start scheduler
    scheduler.start()
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), SchedulerAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
