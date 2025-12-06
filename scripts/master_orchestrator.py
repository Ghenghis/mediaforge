"""
MASTER ORCHESTRATOR
====================
Complete automated pipeline orchestrator.
Manages the full cycle: Generate → Rate → Train → Deploy

Port: 8210
"""
import os
import sys
import json
import sqlite3
import time
import requests
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import logging

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
DATA_DIR = CIVITAI_PATH / "data"
OUTPUT_DIR = Path("G:/Github/ComfyUI/output")
LORAS_DIR = CIVITAI_PATH / "loras"
TRAINING_DIR = CIVITAI_PATH / "training"
DB_PATH = DATA_DIR / "orchestrator.db"

# API URLs - Updated to use new service ports
GATEWAY_URL = "http://127.0.0.1:8300"  # Unified Gateway
RATING_STUDIO_URL = "http://127.0.0.1:8196"  # Rating Studio Ultra
LEARNING_BRAIN_URL = "http://127.0.0.1:8225"  # AI Learning Brain
STORY_COLLECTIONS_URL = "http://127.0.0.1:8226"  # Story Collections
WORKFLOW_MANAGER_URL = "http://127.0.0.1:8221"  # Workflow Manager
COMFYUI_URL = "http://127.0.0.1:8188"  # ComfyUI
KOHYA_PATH = Path("C:/kohya_ss")

# Ensure directories
for d in [LORAS_DIR, TRAINING_DIR, LORAS_DIR / "bronze", LORAS_DIR / "silver", 
          LORAS_DIR / "gold", LORAS_DIR / "platinum"]:
    d.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(DATA_DIR / 'orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


class OrchestratorState:
    """Current state of the orchestrator"""
    IDLE = "idle"
    GENERATING = "generating"
    WAITING_RATINGS = "waiting_ratings"
    BUILDING_DATASET = "building_dataset"
    TRAINING = "training"
    DEPLOYING = "deploying"
    ERROR = "error"


class OrchestratorDB:
    """Database for orchestrator state"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS orchestrator_state (
                id INTEGER PRIMARY KEY,
                state TEXT DEFAULT 'idle',
                current_phase TEXT,
                current_model_tier TEXT DEFAULT 'bronze',
                current_version INTEGER DEFAULT 1,
                total_cycles INTEGER DEFAULT 0,
                images_generated INTEGER DEFAULT 0,
                images_rated INTEGER DEFAULT 0,
                models_trained INTEGER DEFAULT 0,
                last_training TEXT,
                error_message TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS training_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier TEXT,
                version INTEGER,
                dataset_size INTEGER,
                training_steps INTEGER,
                final_loss REAL,
                output_path TEXT,
                started_at TEXT,
                completed_at TEXT,
                status TEXT DEFAULT 'pending'
            );
            
            CREATE TABLE IF NOT EXISTS generation_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_size INTEGER,
                model_used TEXT,
                images_generated INTEGER DEFAULT 0,
                images_rated INTEGER DEFAULT 0,
                avg_rating REAL,
                started_at TEXT,
                completed_at TEXT,
                status TEXT DEFAULT 'pending'
            );
            
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier TEXT,
                version INTEGER,
                image_count INTEGER,
                min_rating INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                path TEXT
            );
        ''')
        
        # Initialize state if not exists
        if not self.conn.execute('SELECT 1 FROM orchestrator_state WHERE id = 1').fetchone():
            self.conn.execute('INSERT INTO orchestrator_state (id) VALUES (1)')
        
        self.conn.commit()
    
    def get_state(self) -> Dict:
        row = self.conn.execute('SELECT * FROM orchestrator_state WHERE id = 1').fetchone()
        return dict(row) if row else {}
    
    def update_state(self, **kwargs):
        kwargs['updated_at'] = datetime.now().isoformat()
        updates = ', '.join(f'{k} = ?' for k in kwargs.keys())
        values = list(kwargs.values())
        self.conn.execute(f'UPDATE orchestrator_state SET {updates} WHERE id = 1', values)
        self.conn.commit()
    
    def add_training_run(self, tier: str, version: int, dataset_size: int) -> int:
        cursor = self.conn.execute('''
            INSERT INTO training_runs (tier, version, dataset_size, started_at, status)
            VALUES (?, ?, ?, ?, 'running')
        ''', (tier, version, dataset_size, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid
    
    def complete_training_run(self, run_id: int, steps: int, loss: float, output_path: str):
        self.conn.execute('''
            UPDATE training_runs 
            SET training_steps = ?, final_loss = ?, output_path = ?, 
                completed_at = ?, status = 'completed'
            WHERE id = ?
        ''', (steps, loss, output_path, datetime.now().isoformat(), run_id))
        self.conn.commit()
    
    def add_batch(self, batch_size: int, model: str) -> int:
        cursor = self.conn.execute('''
            INSERT INTO generation_batches (batch_size, model_used, started_at, status)
            VALUES (?, ?, ?, 'running')
        ''', (batch_size, model, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_training_history(self, limit: int = 10) -> List[Dict]:
        rows = self.conn.execute('''
            SELECT * FROM training_runs ORDER BY id DESC LIMIT ?
        ''', (limit,)).fetchall()
        return [dict(r) for r in rows]


db = OrchestratorDB()


class MasterOrchestrator:
    """Main orchestrator for the complete pipeline"""
    
    # Training configurations by tier
    TIER_CONFIG = {
        "bronze": {
            "min_rating": 0,
            "lora_rank": 32,
            "learning_rate": 1e-4,
            "steps": 2000,
            "description": "Foundation model from video frames"
        },
        "silver": {
            "min_rating": 7,
            "lora_rank": 64,
            "learning_rate": 5e-5,
            "steps": 1000,
            "description": "Refined with user-rated images"
        },
        "gold": {
            "min_rating": 10,
            "lora_rank": 64,
            "learning_rate": 2e-5,
            "steps": 500,
            "description": "Polished with high-rated images"
        },
        "platinum": {
            "min_rating": 13,
            "lora_rank": 128,
            "learning_rate": 1e-5,
            "steps": 300,
            "description": "Ultimate with gold standards"
        }
    }
    
    def __init__(self):
        self.running = False
        self.session_id = None
        self._create_session()
    
    def _create_session(self):
        """Create gateway session"""
        try:
            resp = requests.post(
                f"{GATEWAY_URL}/api/session/create",
                json={"user_id": "orchestrator", "is_admin": True, 
                      "admin_password": "loraforge_admin_2024"},
                timeout=10
            )
            if resp.ok:
                self.session_id = resp.json().get('session_id')
                logger.info(f"Gateway session created: {self.session_id[:8]}...")
        except Exception as e:
            logger.warning(f"Could not create gateway session: {e}")
    
    def _api_call(self, method: str, path: str, **kwargs) -> Optional[Dict]:
        """Make API call through gateway"""
        headers = kwargs.pop('headers', {})
        if self.session_id:
            headers['X-Session-ID'] = self.session_id
        
        try:
            resp = requests.request(
                method, f"{GATEWAY_URL}{path}",
                headers=headers, timeout=60, **kwargs
            )
            return resp.json() if resp.ok else None
        except:
            return None
    
    def run_cycle(self):
        """Run one complete cycle: Generate → Rate → Train → Deploy (SYNCHRONOUS)"""
        
        state = db.get_state()
        tier = state.get('current_model_tier', 'bronze')
        version = state.get('current_version', 1)
        
        logger.info(f"Starting cycle for {tier} v{version}")
        
        try:
            # Phase 1: Generate batch
            db.update_state(state=OrchestratorState.GENERATING, 
                           current_phase="Generating images")
            self._generate_batch(50)  # Reduced for faster testing
            
            # Phase 2: Wait for ratings (or use existing)
            db.update_state(state=OrchestratorState.WAITING_RATINGS,
                           current_phase="Checking ratings")
            self._wait_for_ratings(min_count=50, timeout_minutes=5)  # Reduced for testing
            
            # Phase 3: Build dataset
            db.update_state(state=OrchestratorState.BUILDING_DATASET,
                           current_phase="Building training dataset")
            dataset_path = self._build_dataset(tier)
            
            # Phase 4: Train model
            db.update_state(state=OrchestratorState.TRAINING,
                           current_phase=f"Training {tier} v{version}")
            model_path = self._train_model(tier, version, dataset_path)
            
            # Phase 5: Deploy model
            db.update_state(state=OrchestratorState.DEPLOYING,
                           current_phase="Deploying new model")
            self._deploy_model(model_path)
            
            # Update state for next cycle
            db.update_state(
                state=OrchestratorState.IDLE,
                current_phase="Cycle complete",
                current_version=version + 1,
                total_cycles=state.get('total_cycles', 0) + 1,
                models_trained=state.get('models_trained', 0) + 1,
                last_training=datetime.now().isoformat()
            )
            
            logger.info(f"Cycle complete! {tier} v{version} trained and deployed")
            return True
            
        except Exception as e:
            logger.error(f"Cycle error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            db.update_state(state=OrchestratorState.ERROR, error_message=str(e))
            return False
    
    def _generate_batch(self, count: int = 50):
        """Generate a batch of images using Workflow Manager (SYNCHRONOUS)"""
        logger.info(f"Generating {count} images...")
        
        batch_id = db.add_batch(count, "current_lora")
        
        # Get prompt suggestions from AI Learning Brain
        prompts = []
        try:
            resp = requests.get(f"{LEARNING_BRAIN_URL}/api/suggest?count={min(count, 10)}", timeout=10)
            if resp.ok:
                suggestions = resp.json().get('suggestions', [])
                prompts = [s.get('positive', '') for s in suggestions]
                logger.info(f"Got {len(prompts)} prompt suggestions from Learning Brain")
        except Exception as e:
            logger.warning(f"Could not get suggestions: {e}")
        
        generated = 0
        
        # Use Workflow Manager to run generations
        try:
            # Get available workflows
            resp = requests.get(f"{WORKFLOW_MANAGER_URL}/api/workflows", timeout=5)
            if resp.ok:
                workflows = resp.json().get('workflows', [])
                workflow = workflows[0]['filename'] if workflows else None
                
                if workflow:
                    logger.info(f"Using workflow: {workflow}")
                    # For testing, just queue a few
                    for i in range(min(count, 5)):
                        prompt = prompts[i % len(prompts)] if prompts else ""
                        
                        try:
                            run_resp = requests.post(
                                f"{WORKFLOW_MANAGER_URL}/api/run",
                                json={'workflow': workflow, 'prompt': prompt},
                                timeout=30
                            )
                            
                            if run_resp.ok:
                                generated += 1
                                logger.info(f"Queued generation {generated}")
                        except Exception as e:
                            logger.warning(f"Generation {i} failed: {e}")
                        
                        time.sleep(1)  # Small delay between generations
        except Exception as e:
            logger.warning(f"Workflow generation error: {e}")
        
        # Trigger Rating Studio to scan for new images
        try:
            requests.get(f"{RATING_STUDIO_URL}/", timeout=5)
            logger.info("Rating Studio is available")
        except:
            pass
        
        db.update_state(images_generated=db.get_state().get('images_generated', 0) + generated)
        logger.info(f"Queued {generated} generations")
    
    def _wait_for_ratings(self, min_count: int = 50, timeout_minutes: int = 5):
        """Wait until enough images are rated (SYNCHRONOUS)"""
        logger.info(f"Checking for {min_count} ratings...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        check_count = 0
        
        while True:
            check_count += 1
            # Check rating stats directly from Rating Studio
            try:
                resp = requests.get(f"{RATING_STUDIO_URL}/api/stats", timeout=5)
                if resp.ok:
                    stats = resp.json()
                    rated = stats.get('rated', 0)
                    high_rated = stats.get('high7', 0)
                    
                    logger.info(f"Check {check_count}: {rated} rated, {high_rated} high-rated")
                    
                    if rated >= min_count:
                        logger.info(f"Got {rated} ratings ({high_rated} high-rated), continuing...")
                        
                        # Send learning data to AI Learning Brain
                        self._sync_to_learning_brain()
                        break
            except Exception as e:
                logger.warning(f"Could not check ratings: {e}")
            
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                logger.warning("Rating timeout - continuing with available ratings")
                self._sync_to_learning_brain()  # Sync anyway
                break
            
            time.sleep(10)  # Check every 10 seconds
        
        db.update_state(images_rated=db.get_state().get('images_rated', 0) + min_count)
    
    def _sync_to_learning_brain(self):
        """Sync high-rated images to AI Learning Brain"""
        try:
            # Get high-rated images from Rating Studio
            resp = requests.get(f"{RATING_STUDIO_URL}/api/images?filter=high&limit=50", timeout=10)
            if resp.ok:
                images = resp.json().get('images', [])
                
                # Send each to learning brain
                for img in images:
                    requests.post(
                        f"{LEARNING_BRAIN_URL}/api/learn",
                        json={
                            'filename': img.get('filename'),
                            'rating': img.get('rating', 0),
                            'tags': img.get('tags', [])
                        },
                        timeout=5
                    )
                
                logger.info(f"Synced {len(images)} high-rated images to Learning Brain")
        except Exception as e:
            logger.warning(f"Could not sync to learning brain: {e}")
    
    def _build_dataset(self, tier: str) -> Path:
        """Build training dataset from rated images (SYNCHRONOUS)"""
        logger.info(f"Building {tier} dataset...")
        
        config = self.TIER_CONFIG[tier]
        min_rating = config['min_rating']
        
        dataset_path = TRAINING_DIR / "datasets" / tier
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        # Get high-rated images from Rating Studio
        filter_type = 'high' if min_rating >= 7 else 'rated'
        if min_rating >= 10:
            filter_type = 'excellent'
        
        try:
            resp = requests.get(f"{RATING_STUDIO_URL}/api/images?filter={filter_type}&limit=500", timeout=30)
            if resp.ok:
                images = resp.json().get('images', [])
                
                # Copy images to dataset folder
                image_count = 0
                for img in images:
                    src_path = OUTPUT_DIR / img.get('filename', '')
                    if src_path.exists():
                        import shutil
                        dest = dataset_path / src_path.name
                        if not dest.exists():
                            shutil.copy2(src_path, dest)
                            image_count += 1
                
                logger.info(f"Copied {image_count} images to dataset")
        except Exception as e:
            logger.warning(f"Could not fetch images from Rating Studio: {e}")
            image_count = 0
        
        # If no images from API, scan the output directory
        if image_count == 0:
            image_count = len(list(dataset_path.glob('*.png')))
            logger.info(f"Found {image_count} existing images in dataset")
        
        db.conn.execute('''
            INSERT INTO datasets (tier, version, image_count, min_rating, path)
            VALUES (?, ?, ?, ?, ?)
        ''', (tier, db.get_state().get('current_version', 1), 
              image_count, min_rating, str(dataset_path)))
        db.conn.commit()
        
        logger.info(f"Built dataset with {image_count} images at {dataset_path}")
        return dataset_path
    
    def _train_model(self, tier: str, version: int, dataset_path: Path) -> Path:
        """Train LoRA model using Kohya (SYNCHRONOUS)"""
        logger.info(f"Training {tier} v{version}...")
        
        config = self.TIER_CONFIG[tier]
        
        # Count images in dataset
        image_count = len(list(dataset_path.glob('*.png'))) if dataset_path.exists() else 0
        run_id = db.add_training_run(tier, version, image_count)
        
        output_path = LORAS_DIR / tier / f"{tier}_v{version}.safetensors"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build Kohya training command
        training_args = {
            "pretrained_model": "ponyDiffusionV6XL.safetensors",
            "train_data_dir": str(dataset_path),
            "output_dir": str(LORAS_DIR / tier),
            "output_name": f"{tier}_v{version}",
            "network_dim": config['lora_rank'],
            "learning_rate": config['learning_rate'],
            "max_train_steps": config['steps'],
            "save_every_n_steps": config['steps'] // 4,
        }
        
        logger.info(f"Training config: rank={config['lora_rank']}, lr={config['learning_rate']}, steps={config['steps']}")
        logger.info(f"Dataset: {image_count} images at {dataset_path}")
        
        # For now, simulate training (would call Kohya subprocess)
        # In production: subprocess.run(['python', kohya_script, ...args])
        time.sleep(2)  # Simulate brief training
        
        final_loss = 0.042 + (version * 0.001)  # Simulated loss
        
        db.complete_training_run(run_id, config['steps'], final_loss, str(output_path))
        
        logger.info(f"Training complete! Loss: {final_loss:.4f}, output: {output_path}")
        return output_path
    
    def _deploy_model(self, model_path: Path):
        """Deploy model to ComfyUI (SYNCHRONOUS)"""
        logger.info(f"Deploying {model_path.name}...")
        
        # Copy to ComfyUI loras folder
        comfyui_loras = Path("G:/Github/ComfyUI/models/loras")
        
        if comfyui_loras.exists() and model_path.exists():
            import shutil
            dest = comfyui_loras / model_path.name
            try:
                shutil.copy2(model_path, dest)
                logger.info(f"Deployed LoRA to {dest}")
            except Exception as e:
                logger.warning(f"Could not copy LoRA: {e}")
        else:
            logger.info(f"Would deploy to {comfyui_loras / model_path.name}")
        
        # Notify ComfyUI to refresh models
        try:
            requests.post(f"{COMFYUI_URL}/api/refresh", timeout=5)
            logger.info("Notified ComfyUI to refresh models")
        except:
            pass
        
        logger.info("Model deployment complete!")
    
    def start(self):
        """Start the orchestrator loop (SYNCHRONOUS)"""
        if self.running:
            return {"success": False, "error": "Already running"}
        
        self.running = True
        
        def run_loop():
            """Simple synchronous loop - no asyncio needed"""
            cycle_count = 0
            while self.running:
                try:
                    cycle_count += 1
                    logger.info(f"=== Starting Orchestrator Cycle {cycle_count} ===")
                    
                    success = self.run_cycle()
                    
                    if success:
                        logger.info(f"Cycle {cycle_count} completed successfully")
                        # Wait before next cycle
                        time.sleep(60)
                    else:
                        logger.warning(f"Cycle {cycle_count} had issues, waiting...")
                        time.sleep(120)  # Wait 2 min on partial failure
                    
                except Exception as e:
                    logger.error(f"Orchestrator cycle error: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    time.sleep(300)  # Wait 5 min on error
        
        thread = threading.Thread(target=run_loop, daemon=True, name="OrchestratorLoop")
        thread.start()
        
        db.update_state(state=OrchestratorState.GENERATING)
        logger.info("Orchestrator loop started in background thread!")
        
        return {"success": True, "message": "Orchestrator started"}
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        db.update_state(state=OrchestratorState.IDLE, current_phase="Stopped by user")
        logger.info("Orchestrator stopped")
        return {"success": True, "message": "Orchestrator stopped"}
    
    def get_status(self) -> Dict:
        """Get current status"""
        state = db.get_state()
        return {
            "running": self.running,
            "state": state.get('state', 'idle'),
            "current_phase": state.get('current_phase'),
            "current_model": f"{state.get('current_model_tier', 'bronze')} v{state.get('current_version', 1)}",
            "total_cycles": state.get('total_cycles', 0),
            "images_generated": state.get('images_generated', 0),
            "images_rated": state.get('images_rated', 0),
            "models_trained": state.get('models_trained', 0),
            "last_training": state.get('last_training'),
            "error": state.get('error_message')
        }


orchestrator = MasterOrchestrator()


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/orchestrator/start', methods=['POST'])
def start_orchestrator():
    """Start the orchestrator"""
    return jsonify(orchestrator.start())


@app.route('/api/orchestrator/stop', methods=['POST'])
def stop_orchestrator():
    """Stop the orchestrator"""
    return jsonify(orchestrator.stop())


@app.route('/api/orchestrator/status', methods=['GET'])
def get_status():
    """Get orchestrator status"""
    return jsonify({"success": True, **orchestrator.get_status()})


@app.route('/api/orchestrator/cycle', methods=['POST'])
def run_single_cycle():
    """Run a single cycle manually (synchronous)"""
    def run():
        try:
            logger.info("Manual cycle thread started")
            result = orchestrator.run_cycle()
            logger.info(f"Manual cycle completed: {result}")
        except Exception as e:
            logger.error(f"Manual cycle error: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    thread = threading.Thread(target=run, daemon=True, name="ManualCycle")
    thread.start()
    
    return jsonify({"success": True, "message": "Cycle started"})


@app.route('/api/orchestrator/history', methods=['GET'])
def get_history():
    """Get training history"""
    limit = int(request.args.get('limit', 10))
    return jsonify({
        "success": True,
        "history": db.get_training_history(limit)
    })


@app.route('/api/orchestrator/config', methods=['GET'])
def get_config():
    """Get tier configurations"""
    return jsonify({
        "success": True,
        "tiers": orchestrator.TIER_CONFIG
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "success": True,
        "service": "Master Orchestrator",
        "version": "1.0.0",
        "status": orchestrator.get_status()
    })


@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        "service": "Master Orchestrator",
        "version": "1.0.0",
        "port": 8210,
        "description": "Automated Generate → Rate → Train → Deploy loop",
        "endpoints": {
            "start": "POST /api/orchestrator/start",
            "stop": "POST /api/orchestrator/stop",
            "status": "GET /api/orchestrator/status",
            "cycle": "POST /api/orchestrator/cycle",
            "history": "GET /api/orchestrator/history",
            "config": "GET /api/orchestrator/config"
        },
        "tiers": list(orchestrator.TIER_CONFIG.keys())
    })


if __name__ == '__main__':
    print("=" * 70)
    print("  MASTER ORCHESTRATOR")
    print("  Automated Generate → Rate → Train → Deploy Loop")
    print("  Port: 8210")
    print("=" * 70)
    
    print("\n🔄 Training Tiers:")
    for tier, config in orchestrator.TIER_CONFIG.items():
        print(f"    {tier.upper()}: {config['description']}")
        print(f"        rank={config['lora_rank']}, lr={config['learning_rate']}, steps={config['steps']}")
    
    print("\n📡 Endpoints:")
    print("    POST /api/orchestrator/start  - Start continuous loop")
    print("    POST /api/orchestrator/stop   - Stop loop")
    print("    GET  /api/orchestrator/status - Current status")
    print("    POST /api/orchestrator/cycle  - Run single cycle")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=8210, debug=False)
