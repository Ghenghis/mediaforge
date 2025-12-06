"""
LORA TRAINING INTEGRATION
==========================
Connects to Kohya_ss for actual LoRA training.
Generates real .safetensors files from datasets.

Port: 8230
"""
import os
import sys
import json
import subprocess
import time
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
KOHYA_PATH = Path("C:/kohya_ss")
DATA_DIR = CIVITAI_PATH / "data"
TRAINING_DIR = CIVITAI_PATH / "training"
LORAS_DIR = CIVITAI_PATH / "loras"
DATASETS_DIR = TRAINING_DIR / "datasets"
CONFIGS_DIR = TRAINING_DIR / "configs"
DB_PATH = DATA_DIR / "training.db"

# Ensure directories
for d in [TRAINING_DIR, LORAS_DIR, DATASETS_DIR, CONFIGS_DIR,
          LORAS_DIR / "bronze", LORAS_DIR / "silver", LORAS_DIR / "gold", LORAS_DIR / "platinum"]:
    d.mkdir(parents=True, exist_ok=True)

PORT = 8230

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(DATA_DIR / 'lora_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrainingDB:
    """Database for training jobs"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS training_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tier TEXT DEFAULT 'bronze',
                status TEXT DEFAULT 'pending',
                dataset_path TEXT,
                output_path TEXT,
                config_path TEXT,
                image_count INTEGER DEFAULT 0,
                steps INTEGER DEFAULT 0,
                current_step INTEGER DEFAULT 0,
                loss REAL,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                started_at TEXT,
                completed_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS training_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                config_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()
    
    def create_job(self, name: str, tier: str, dataset_path: str, config: dict) -> int:
        config_path = str(CONFIGS_DIR / f"{name}.toml")
        cursor = self.conn.execute('''
            INSERT INTO training_jobs (name, tier, dataset_path, config_path, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (name, tier, dataset_path, config_path))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_job(self, job_id: int, **kwargs):
        updates = ', '.join(f'{k} = ?' for k in kwargs.keys())
        values = list(kwargs.values()) + [job_id]
        self.conn.execute(f'UPDATE training_jobs SET {updates} WHERE id = ?', values)
        self.conn.commit()
    
    def get_job(self, job_id: int) -> Optional[Dict]:
        row = self.conn.execute('SELECT * FROM training_jobs WHERE id = ?', (job_id,)).fetchone()
        return dict(row) if row else None
    
    def get_active_jobs(self) -> List[Dict]:
        rows = self.conn.execute(
            'SELECT * FROM training_jobs WHERE status IN ("pending", "running") ORDER BY id'
        ).fetchall()
        return [dict(r) for r in rows]
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict]:
        rows = self.conn.execute(
            'SELECT * FROM training_jobs ORDER BY id DESC LIMIT ?', (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


db = TrainingDB()


class KohyaIntegration:
    """Integration with Kohya_ss for LoRA training"""
    
    # Training presets by tier
    TIER_CONFIGS = {
        "bronze": {
            "network_dim": 32,
            "network_alpha": 16,
            "learning_rate": 1e-4,
            "unet_lr": 1e-4,
            "text_encoder_lr": 5e-5,
            "max_train_steps": 2000,
            "save_every_n_steps": 500,
            "lr_scheduler": "cosine_with_restarts",
            "lr_warmup_steps": 100,
            "resolution": "1024,1024",
            "train_batch_size": 1,
            "gradient_accumulation_steps": 4,
        },
        "silver": {
            "network_dim": 64,
            "network_alpha": 32,
            "learning_rate": 5e-5,
            "unet_lr": 5e-5,
            "text_encoder_lr": 2e-5,
            "max_train_steps": 1500,
            "save_every_n_steps": 300,
            "lr_scheduler": "cosine_with_restarts",
            "lr_warmup_steps": 75,
            "resolution": "1024,1024",
            "train_batch_size": 1,
            "gradient_accumulation_steps": 4,
        },
        "gold": {
            "network_dim": 64,
            "network_alpha": 32,
            "learning_rate": 2e-5,
            "unet_lr": 2e-5,
            "text_encoder_lr": 1e-5,
            "max_train_steps": 1000,
            "save_every_n_steps": 200,
            "lr_scheduler": "cosine",
            "lr_warmup_steps": 50,
            "resolution": "1024,1024",
            "train_batch_size": 1,
            "gradient_accumulation_steps": 4,
        },
        "platinum": {
            "network_dim": 128,
            "network_alpha": 64,
            "learning_rate": 1e-5,
            "unet_lr": 1e-5,
            "text_encoder_lr": 5e-6,
            "max_train_steps": 500,
            "save_every_n_steps": 100,
            "lr_scheduler": "constant",
            "lr_warmup_steps": 25,
            "resolution": "1024,1024",
            "train_batch_size": 1,
            "gradient_accumulation_steps": 4,
        }
    }
    
    def __init__(self):
        self.current_process = None
        self.is_training = False
        self.current_job_id = None
    
    def check_kohya_setup(self) -> Tuple[bool, str]:
        """Check if Kohya is properly set up"""
        issues = []
        
        # Check Kohya path
        if not KOHYA_PATH.exists():
            issues.append(f"Kohya not found at {KOHYA_PATH}")
            return False, "; ".join(issues)
        
        # Check venv
        venv_python = KOHYA_PATH / "venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            issues.append("Kohya venv not found")
        
        # Check sd-scripts
        sd_scripts = KOHYA_PATH / "sd-scripts"
        train_script = sd_scripts / "sdxl_train_network.py"
        
        if not sd_scripts.exists() or not any(sd_scripts.iterdir()):
            issues.append("sd-scripts submodule not initialized. Run: cd C:\\kohya_ss && git submodule update --init --recursive")
        elif not train_script.exists():
            issues.append(f"Training script not found: {train_script}")
        
        # Check accelerate
        accelerate = KOHYA_PATH / "venv" / "Scripts" / "accelerate.exe"
        if not accelerate.exists():
            issues.append("accelerate not found in venv")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, "Kohya is properly configured"
    
    def generate_config(self, job_name: str, tier: str, dataset_path: str, 
                       base_model: str = None, output_dir: str = None) -> str:
        """Generate TOML config for training"""
        
        tier_config = self.TIER_CONFIGS.get(tier, self.TIER_CONFIGS["bronze"])
        
        # Find available base model
        if not base_model:
            # Check for models in ComfyUI
            comfyui_models = Path("G:/Github/ComfyUI/models/checkpoints")
            if comfyui_models.exists():
                for model_file in comfyui_models.glob("*.safetensors"):
                    base_model = str(model_file)
                    break
            
            # Fallback to default
            if not base_model:
                base_model = "G:/Github/ComfyUI/models/checkpoints/RealisticVisionV5.safetensors"
        
        # Detect if SDXL based on file size (SDXL > 5GB, SD1.5 ~2GB)
        is_sdxl = False
        if Path(base_model).exists():
            model_size_gb = Path(base_model).stat().st_size / (1024**3)
            is_sdxl = model_size_gb > 5
            logger.info(f"Model: {Path(base_model).name} ({model_size_gb:.1f}GB) - {'SDXL' if is_sdxl else 'SD1.5'}")
        
        if not output_dir:
            output_dir = str(LORAS_DIR / tier)
        
        # Count images in dataset
        dataset = Path(dataset_path)
        image_count = len(list(dataset.glob("**/*.png"))) + len(list(dataset.glob("**/*.jpg")))
        
        # Calculate repeats (aim for ~1500-2000 total steps with the images)
        repeats = max(1, 1500 // max(image_count, 1))
        
        # Build config based on model type
        config = {}
        
        if is_sdxl:
            config["sdxl_arguments"] = {
                "sdxl": True,
                "cache_text_encoder_outputs": True,
                "no_half_vae": True,
            }
            resolution = "1024,1024"
        else:
            # SD1.5 settings
            resolution = "512,512"
        
        config["model_arguments"] = {
            "pretrained_model_name_or_path": base_model,
            "vae": "",
        }
        
        # Store model type for training script selection
        config["_model_type"] = "sdxl" if is_sdxl else "sd15"
        
        config["dataset_arguments"] = {
            "debug_dataset": False,
        }
        
        config["training_arguments"] = {
            "output_dir": output_dir,
            "output_name": job_name,
            "save_precision": "fp16",
            "save_model_as": "safetensors",
            "max_train_steps": tier_config["max_train_steps"],
            "learning_rate": tier_config["learning_rate"],
            "unet_lr": tier_config["unet_lr"],
            "text_encoder_lr": tier_config["text_encoder_lr"],
            "lr_scheduler": tier_config["lr_scheduler"],
            "lr_warmup_steps": tier_config["lr_warmup_steps"],
            "train_batch_size": tier_config["train_batch_size"],
            "gradient_accumulation_steps": tier_config["gradient_accumulation_steps"],
            "save_every_n_steps": tier_config["save_every_n_steps"],
            "mixed_precision": "fp16",
            "seed": 42,
            "cache_latents": True,
            "cache_latents_to_disk": True,
            "optimizer_type": "AdamW8bit",
            "max_data_loader_n_workers": 2,
            "gradient_checkpointing": True,
            "xformers": True,
            "bucket_no_upscale": True,
            "min_bucket_reso": 256 if is_sdxl else 256,
            "max_bucket_reso": 2048 if is_sdxl else 768,
            "bucket_reso_steps": 64,
            "resolution": resolution,
        }
        
        config["network_arguments"] = {
            "network_module": "networks.lora",
            "network_dim": tier_config["network_dim"],
            "network_alpha": tier_config["network_alpha"],
            "network_train_unet_only": False,
        }
        
        config["dataset_config"] = {
            "datasets": [{
                "subsets": [{
                    "image_dir": dataset_path,
                    "num_repeats": repeats,
                }]
            }]
        }
        
        # Save config
        config_path = CONFIGS_DIR / f"{job_name}.toml"
        
        # Convert to TOML format
        import toml
        with open(config_path, 'w') as f:
            toml.dump(config, f)
        
        logger.info(f"Generated config: {config_path}")
        return str(config_path)
    
    def start_training(self, job_id: int) -> Tuple[bool, str]:
        """Start a training job"""
        
        if self.is_training:
            return False, "Another training job is already running"
        
        job = db.get_job(job_id)
        if not job:
            return False, f"Job {job_id} not found"
        
        # Check Kohya setup
        ok, msg = self.check_kohya_setup()
        if not ok:
            db.update_job(job_id, status='error', error_message=msg)
            return False, msg
        
        # Determine model type from config
        import toml
        with open(job['config_path'], 'r') as f:
            config = toml.load(f)
        model_type = config.get('_model_type', 'sd15')
        
        # Build command - select script based on model type
        venv_python = KOHYA_PATH / "venv" / "Scripts" / "python.exe"
        accelerate = KOHYA_PATH / "venv" / "Scripts" / "accelerate.exe"
        
        if model_type == 'sdxl':
            train_script = KOHYA_PATH / "sd-scripts" / "sdxl_train_network.py"
        else:
            train_script = KOHYA_PATH / "sd-scripts" / "train_network.py"
        
        logger.info(f"Using {model_type.upper()} training script: {train_script.name}")
        
        cmd = [
            str(accelerate), "launch",
            "--mixed_precision", "fp16",
            "--num_processes", "1",
            "--num_machines", "1",
            str(train_script),
            "--config_file", job['config_path']
        ]
        
        logger.info(f"Starting training: {' '.join(cmd)}")
        
        try:
            # Set environment
            env = os.environ.copy()
            env['PYTHONPATH'] = str(KOHYA_PATH / "sd-scripts")
            
            # Start training process
            self.current_process = subprocess.Popen(
                cmd,
                cwd=str(KOHYA_PATH),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1
            )
            
            self.is_training = True
            self.current_job_id = job_id
            
            db.update_job(job_id, 
                         status='running',
                         started_at=datetime.now().isoformat())
            
            # Start output monitoring thread
            def monitor_output():
                try:
                    for line in self.current_process.stdout:
                        line = line.strip()
                        if line:
                            logger.info(f"[TRAINING] {line}")
                            
                            # Parse progress from output
                            if "steps:" in line.lower() or "step" in line.lower():
                                # Try to extract step number
                                import re
                                match = re.search(r'step[s]?\s*[:\s]*(\d+)', line, re.I)
                                if match:
                                    current_step = int(match.group(1))
                                    db.update_job(job_id, current_step=current_step)
                            
                            # Check for loss
                            if "loss" in line.lower():
                                match = re.search(r'loss[:\s]*([0-9.]+)', line, re.I)
                                if match:
                                    loss = float(match.group(1))
                                    db.update_job(job_id, loss=loss)
                    
                    # Process finished
                    return_code = self.current_process.wait()
                    
                    if return_code == 0:
                        # Check if output file exists
                        job = db.get_job(job_id)
                        tier = job.get('tier', 'bronze')
                        name = job.get('name', 'lora')
                        output_file = LORAS_DIR / tier / f"{name}.safetensors"
                        
                        if output_file.exists():
                            db.update_job(job_id,
                                         status='completed',
                                         output_path=str(output_file),
                                         completed_at=datetime.now().isoformat())
                            logger.info(f"Training completed: {output_file}")
                        else:
                            db.update_job(job_id,
                                         status='completed',
                                         completed_at=datetime.now().isoformat())
                            logger.warning("Training completed but output file not found")
                    else:
                        db.update_job(job_id,
                                     status='error',
                                     error_message=f"Training failed with code {return_code}",
                                     completed_at=datetime.now().isoformat())
                        logger.error(f"Training failed with return code {return_code}")
                        
                except Exception as e:
                    logger.error(f"Monitor error: {e}")
                    db.update_job(job_id, status='error', error_message=str(e))
                finally:
                    self.is_training = False
                    self.current_job_id = None
                    self.current_process = None
            
            thread = threading.Thread(target=monitor_output, daemon=True)
            thread.start()
            
            return True, f"Training started for job {job_id}"
            
        except Exception as e:
            logger.error(f"Failed to start training: {e}")
            db.update_job(job_id, status='error', error_message=str(e))
            self.is_training = False
            return False, str(e)
    
    def stop_training(self) -> Tuple[bool, str]:
        """Stop current training"""
        if not self.is_training or not self.current_process:
            return False, "No training in progress"
        
        try:
            self.current_process.terminate()
            self.current_process.wait(timeout=10)
            
            if self.current_job_id:
                db.update_job(self.current_job_id, 
                             status='cancelled',
                             completed_at=datetime.now().isoformat())
            
            self.is_training = False
            self.current_job_id = None
            self.current_process = None
            
            return True, "Training stopped"
        except Exception as e:
            return False, str(e)
    
    def get_status(self) -> Dict:
        """Get current training status"""
        status = {
            "is_training": self.is_training,
            "current_job_id": self.current_job_id,
            "kohya_ready": self.check_kohya_setup()[0],
        }
        
        if self.current_job_id:
            job = db.get_job(self.current_job_id)
            if job:
                status["current_job"] = job
        
        return status


kohya = KohyaIntegration()


# ============================================================
# HTTP API
# ============================================================

class TrainingAPI(BaseHTTPRequestHandler):
    """HTTP API for LoRA training"""
    
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")
    
    def send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/':
            self.send_json({
                "service": "LoRA Training Integration",
                "port": PORT,
                "version": "1.0.0",
                "endpoints": {
                    "status": "GET /api/status",
                    "check": "GET /api/check",
                    "jobs": "GET /api/jobs",
                    "job": "GET /api/job/<id>",
                    "create": "POST /api/create",
                    "start": "POST /api/start/<id>",
                    "stop": "POST /api/stop"
                }
            })
        
        elif path == '/api/status':
            self.send_json({"success": True, **kohya.get_status()})
        
        elif path == '/api/check':
            ok, msg = kohya.check_kohya_setup()
            self.send_json({"success": True, "ready": ok, "message": msg})
        
        elif path == '/api/jobs':
            jobs = db.get_recent_jobs(20)
            self.send_json({"success": True, "jobs": jobs})
        
        elif path.startswith('/api/job/'):
            try:
                job_id = int(path.split('/')[-1])
                job = db.get_job(job_id)
                if job:
                    self.send_json({"success": True, "job": job})
                else:
                    self.send_json({"success": False, "error": "Job not found"}, 404)
            except:
                self.send_json({"success": False, "error": "Invalid job ID"}, 400)
        
        elif path == '/api/health':
            self.send_json({"success": True, "service": "LoRA Training"})
        
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = self.path.split('?')[0]
        
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = {}
        if content_length > 0:
            body = json.loads(self.rfile.read(content_length).decode())
        
        if path == '/api/create':
            # Create a new training job
            name = body.get('name', f"lora_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            tier = body.get('tier', 'bronze')
            dataset_path = body.get('dataset_path')
            base_model = body.get('base_model')
            
            if not dataset_path:
                self.send_json({"success": False, "error": "dataset_path required"}, 400)
                return
            
            # Generate config
            config_path = kohya.generate_config(name, tier, dataset_path, base_model)
            
            # Create job in database
            job_id = db.create_job(name, tier, dataset_path, {"config_path": config_path})
            
            # Count images
            image_count = len(list(Path(dataset_path).glob("**/*.png"))) + \
                         len(list(Path(dataset_path).glob("**/*.jpg")))
            db.update_job(job_id, image_count=image_count, 
                         steps=kohya.TIER_CONFIGS[tier]["max_train_steps"])
            
            self.send_json({
                "success": True, 
                "job_id": job_id,
                "config_path": config_path,
                "image_count": image_count
            })
        
        elif path.startswith('/api/start/'):
            try:
                job_id = int(path.split('/')[-1])
                ok, msg = kohya.start_training(job_id)
                self.send_json({"success": ok, "message": msg})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
        
        elif path == '/api/stop':
            ok, msg = kohya.stop_training()
            self.send_json({"success": ok, "message": msg})
        
        elif path == '/api/quick_train':
            # Quick train - create and start in one call
            name = body.get('name', f"lora_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            tier = body.get('tier', 'bronze')
            dataset_path = body.get('dataset_path')
            base_model = body.get('base_model')
            
            if not dataset_path:
                self.send_json({"success": False, "error": "dataset_path required"}, 400)
                return
            
            # Generate config
            config_path = kohya.generate_config(name, tier, dataset_path, base_model)
            
            # Create job
            job_id = db.create_job(name, tier, dataset_path, {"config_path": config_path})
            image_count = len(list(Path(dataset_path).glob("**/*.png")))
            db.update_job(job_id, image_count=image_count)
            
            # Start training
            ok, msg = kohya.start_training(job_id)
            
            self.send_json({
                "success": ok,
                "job_id": job_id,
                "message": msg
            })
        
        else:
            self.send_json({"error": "Not found"}, 404)


def main():
    """Start the training API server"""
    print("=" * 60)
    print("  LORA TRAINING INTEGRATION")
    print(f"  Port: {PORT}")
    print("=" * 60)
    
    # Check Kohya setup
    ok, msg = kohya.check_kohya_setup()
    if ok:
        print(f"\n[OK] Kohya: {msg}")
    else:
        print(f"\n[!] Kohya: {msg}")
        print("\nTo fix: cd C:\\kohya_ss && git submodule update --init --recursive")
    
    print(f"\nEndpoints:")
    print(f"  GET  /api/status     - Training status")
    print(f"  GET  /api/check      - Check Kohya setup")
    print(f"  GET  /api/jobs       - List jobs")
    print(f"  POST /api/create     - Create job")
    print(f"  POST /api/start/<id> - Start training")
    print(f"  POST /api/stop       - Stop training")
    print(f"  POST /api/quick_train - Create & start")
    print("=" * 60)
    
    server = HTTPServer(('0.0.0.0', PORT), TrainingAPI)
    logger.info(f"LoRA Training API running on port {PORT}")
    server.serve_forever()


if __name__ == '__main__':
    main()
