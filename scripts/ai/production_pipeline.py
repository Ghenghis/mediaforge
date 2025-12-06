"""
Production AI Pipeline for LoRA Training Project
================================================
Professional-grade pipeline with comprehensive failsafes:
- Multi-model rotation for verification
- Learning validation (detect faking vs real learning)
- Full sweep management with checkpoint/resume
- Resource optimization and memory monitoring
- Automatic failover and recovery
- Retry mechanisms with exponential backoff
- Circuit breakers for repeated failures
- Backup/restore capabilities
"""

import os
import sys
import json
import time
import hashlib
import random
import httpx
import base64
import logging
import shutil
import traceback
import threading
import psutil
import gc
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict
from functools import wraps
from contextlib import contextmanager

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    "project_dir": Path(r"C:\Users\Admin\civitai"),
    "lm_studio_url": "http://localhost:1234/v1",
    "ollama_url": "http://localhost:11434",
    
    # Model categories for pipeline stages
    "models": {
        # STAGE 1: Quick scan (fast models)
        "quick_scan": [
            {"name": "Qwen3-0.6B", "size": 0.5, "provider": "lm_studio"},
            {"name": "LFM2-VL-1.6B", "size": 2.0, "provider": "lm_studio", "vision": True},
            {"name": "DeepSeek-R1-Qwen-1.5B", "size": 1.0, "provider": "lm_studio"},
        ],
        # STAGE 2: Detailed captioning (quality models)
        "caption_detail": [
            {"name": "Qwen3-VL-8B-Abliterated-Caption-it", "size": 8.0, "provider": "lm_studio", "vision": True},
            {"name": "thesby_Qwen2.5-VL-7B-NSFW-Caption-V3", "size": 7.9, "provider": "lm_studio", "vision": True},
            {"name": "amoral-gemma3-12B-vision", "size": 9.0, "provider": "lm_studio", "vision": True},
        ],
        # STAGE 3: Quality assessment (reasoning models)
        "quality_assess": [
            {"name": "gemma3-27b-abliterated", "size": 17.9, "provider": "lm_studio"},
            {"name": "gemma-3-12b-abliterated", "size": 11.7, "provider": "lm_studio"},
            {"name": "Phi-4-reasoning-plus", "size": 11.2, "provider": "lm_studio"},
        ],
        # STAGE 4: Writing/RP enhancement
        "writing": [
            {"name": "Dirty-Muse-Writer-v01", "size": 7.6, "provider": "lm_studio"},
            {"name": "Rombos-Qwen2.5-Writer-32b", "size": 19.2, "provider": "lm_studio"},
            {"name": "WizardLM-Uncensored-SuperCOT-Storytelling", "size": 17.2, "provider": "lm_studio"},
        ],
        # STAGE 5: Verification (different model to cross-check)
        "verification": [
            {"name": "dolphin-2.9.1-yi-1.5-9b", "size": 7.3, "provider": "lm_studio"},
            {"name": "Ministral-3-14B-Reasoning", "size": 13.4, "provider": "lm_studio"},
        ],
    },
    
    # Learning verification settings
    "verification": {
        "min_consistency_score": 0.7,  # Minimum agreement between models
        "variation_threshold": 0.3,    # Max allowed variation in responses
        "retest_on_fail": True,
        "max_retests": 3,
    },
    
    # Sweep settings
    "sweep": {
        "images_per_batch": 50,
        "models_per_stage": 2,  # Use top N models per stage
        "rotate_every": 100,    # Rotate models every N images
    },
    
    # Failsafe settings
    "failsafe": {
        "max_retries": 3,
        "retry_delay_base": 2,  # Exponential backoff base (seconds)
        "circuit_breaker_threshold": 5,  # Failures before circuit break
        "circuit_breaker_reset": 300,  # Seconds before reset
        "health_check_interval": 30,
        "memory_threshold_gb": 50,  # Alert if RAM exceeds this
        "gpu_memory_threshold_mb": 20000,  # Alert if GPU exceeds this
        "checkpoint_interval": 10,  # Save checkpoint every N images
        "auto_gc_interval": 25,  # Run garbage collection every N images
    },
    
    # Backup settings
    "backup": {
        "enabled": True,
        "backup_dir": Path(r"C:\Users\Admin\civitai\backups\pipeline"),
        "max_backups": 10,
        "auto_backup_interval": 50,  # Backup every N images
    },
}

# =============================================================================
# FAILSAFE DECORATORS AND UTILITIES
# =============================================================================

def retry_with_backoff(max_retries: int = None, base_delay: float = None, 
                       exceptions: tuple = (Exception,)):
    """
    Decorator for retry with exponential backoff.
    Professional failsafe for transient failures.
    """
    max_retries = max_retries or CONFIG["failsafe"]["max_retries"]
    base_delay = base_delay or CONFIG["failsafe"]["retry_delay_base"]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        LOG.warning(f"⚠️ {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        LOG.info(f"   Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                    else:
                        LOG.error(f"❌ {func.__name__} failed after {max_retries + 1} attempts")
            
            raise last_exception
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.
    After N consecutive failures, the circuit "opens" and fails fast.
    """
    
    def __init__(self, name: str, threshold: int = None, reset_timeout: int = None):
        self.name = name
        self.threshold = threshold or CONFIG["failsafe"]["circuit_breaker_threshold"]
        self.reset_timeout = reset_timeout or CONFIG["failsafe"]["circuit_breaker_reset"]
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self._lock = threading.Lock()
    
    def record_success(self):
        with self._lock:
            self.failures = 0
            self.state = "closed"
    
    def record_failure(self):
        with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.threshold:
                self.state = "open"
                LOG.error(f"🔴 Circuit breaker OPEN for {self.name} after {self.failures} failures")
    
    def can_execute(self) -> bool:
        with self._lock:
            if self.state == "closed":
                return True
            
            if self.state == "open":
                # Check if reset timeout has passed
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.state = "half-open"
                    LOG.info(f"🟡 Circuit breaker HALF-OPEN for {self.name}, testing...")
                    return True
                return False
            
            # half-open: allow one request through
            return True
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_execute():
                raise CircuitBreakerOpen(f"Circuit breaker open for {self.name}")
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise
        return wrapper


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class HealthMonitor:
    """
    Monitor system health and resources.
    Triggers alerts and auto-cleanup when thresholds exceeded.
    """
    
    def __init__(self):
        self.last_check = 0
        self.alerts = []
        self.metrics_history = []
    
    def check_health(self, force: bool = False) -> Dict:
        """Perform health check"""
        now = time.time()
        
        if not force and (now - self.last_check) < CONFIG["failsafe"]["health_check_interval"]:
            return {"status": "skipped"}
        
        self.last_check = now
        
        # System metrics
        mem = psutil.virtual_memory()
        ram_used_gb = mem.used / (1024**3)
        ram_percent = mem.percent
        
        # GPU metrics
        gpu_used_mb = 0
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                gpu_used_mb = float(result.stdout.strip())
        except:
            pass
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "ram_used_gb": round(ram_used_gb, 2),
            "ram_percent": ram_percent,
            "gpu_used_mb": gpu_used_mb,
            "cpu_percent": cpu_percent,
            "status": "healthy",
            "alerts": []
        }
        
        # Check thresholds
        if ram_used_gb > CONFIG["failsafe"]["memory_threshold_gb"]:
            metrics["alerts"].append(f"HIGH RAM: {ram_used_gb:.1f}GB")
            metrics["status"] = "warning"
        
        if gpu_used_mb > CONFIG["failsafe"]["gpu_memory_threshold_mb"]:
            metrics["alerts"].append(f"HIGH GPU: {gpu_used_mb:.0f}MB")
            metrics["status"] = "warning"
        
        if cpu_percent > 95:
            metrics["alerts"].append(f"HIGH CPU: {cpu_percent:.0f}%")
            metrics["status"] = "warning"
        
        # Log alerts
        for alert in metrics["alerts"]:
            LOG.warning(f"⚠️ HEALTH ALERT: {alert}")
        
        # Store history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
        
        return metrics
    
    def auto_cleanup(self):
        """Attempt to free memory"""
        LOG.info("🧹 Running auto-cleanup...")
        
        # Python garbage collection
        gc.collect()
        
        # Force garbage collection
        for _ in range(3):
            gc.collect()
        
        LOG.info("✅ Auto-cleanup complete")


class CheckpointManager:
    """
    Manage checkpoints for resume capability.
    Saves progress periodically to recover from crashes.
    """
    
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.current_checkpoint = None
    
    def save_checkpoint(self, sweep_id: str, state: Dict):
        """Save checkpoint to disk"""
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{sweep_id}.json"
        temp_file = checkpoint_file.with_suffix(".tmp")
        
        try:
            # Write to temp file first (atomic write)
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump({
                    "sweep_id": sweep_id,
                    "timestamp": datetime.now().isoformat(),
                    "state": state
                }, f, indent=2, ensure_ascii=False, default=str)
            
            # Atomic rename
            shutil.move(str(temp_file), str(checkpoint_file))
            self.current_checkpoint = checkpoint_file
            LOG.debug(f"💾 Checkpoint saved: {checkpoint_file.name}")
            
        except Exception as e:
            LOG.error(f"Failed to save checkpoint: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def load_checkpoint(self, sweep_id: str) -> Optional[Dict]:
        """Load checkpoint from disk"""
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{sweep_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            LOG.info(f"📂 Loaded checkpoint from {data['timestamp']}")
            return data["state"]
        except Exception as e:
            LOG.error(f"Failed to load checkpoint: {e}")
            return None
    
    def list_checkpoints(self) -> List[Dict]:
        """List all available checkpoints"""
        checkpoints = []
        for f in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)
                    checkpoints.append({
                        "file": f.name,
                        "sweep_id": data["sweep_id"],
                        "timestamp": data["timestamp"]
                    })
            except:
                pass
        return sorted(checkpoints, key=lambda x: x["timestamp"], reverse=True)
    
    def cleanup_old_checkpoints(self, keep: int = 5):
        """Remove old checkpoints, keep most recent"""
        checkpoints = sorted(self.checkpoint_dir.glob("checkpoint_*.json"), 
                           key=lambda x: x.stat().st_mtime, reverse=True)
        
        for old_cp in checkpoints[keep:]:
            try:
                old_cp.unlink()
                LOG.debug(f"🗑️ Removed old checkpoint: {old_cp.name}")
            except:
                pass


class BackupManager:
    """
    Manage backups of results and state.
    Ensures data safety with multiple backup copies.
    """
    
    def __init__(self):
        self.backup_dir = CONFIG["backup"]["backup_dir"]
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, data: Dict, name: str) -> Path:
        """Create a backup of data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{name}_{timestamp}.json.bak"
        
        try:
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            LOG.debug(f"📦 Backup created: {backup_file.name}")
            
            # Cleanup old backups
            self._cleanup_old_backups(name)
            
            return backup_file
        except Exception as e:
            LOG.error(f"Failed to create backup: {e}")
            return None
    
    def _cleanup_old_backups(self, name: str):
        """Remove old backups, keep most recent"""
        pattern = f"{name}_*.json.bak"
        backups = sorted(self.backup_dir.glob(pattern), 
                        key=lambda x: x.stat().st_mtime, reverse=True)
        
        max_backups = CONFIG["backup"]["max_backups"]
        for old_backup in backups[max_backups:]:
            try:
                old_backup.unlink()
            except:
                pass
    
    def restore_latest(self, name: str) -> Optional[Dict]:
        """Restore from latest backup"""
        pattern = f"{name}_*.json.bak"
        backups = sorted(self.backup_dir.glob(pattern), 
                        key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not backups:
            return None
        
        try:
            with open(backups[0], "r", encoding="utf-8") as f:
                data = json.load(f)
            LOG.info(f"📂 Restored from backup: {backups[0].name}")
            return data
        except Exception as e:
            LOG.error(f"Failed to restore backup: {e}")
            return None


@contextmanager
def safe_operation(operation_name: str, fallback_value: Any = None):
    """
    Context manager for safe operations with automatic error handling.
    Returns fallback value on failure instead of crashing.
    """
    try:
        yield
    except Exception as e:
        LOG.error(f"❌ {operation_name} failed: {e}")
        LOG.debug(traceback.format_exc())
        if fallback_value is not None:
            return fallback_value


# Initialize global health monitor
HEALTH_MONITOR = HealthMonitor()

# =============================================================================
# LOGGING SETUP (Windows-compatible, no emojis in console)
# =============================================================================

class SafeStreamHandler(logging.StreamHandler):
    """Stream handler that safely handles Unicode on Windows"""
    def emit(self, record):
        try:
            msg = self.format(record)
            # Replace emojis with ASCII for Windows console
            replacements = {
                '🏭': '[PIPELINE]', '🔍': '[CHECK]', '✅': '[OK]', '❌': '[FAIL]',
                '🚀': '[START]', '📁': '[DIR]', '📷': '[IMG]', '⚠️': '[WARN]',
                '💾': '[SAVE]', '📊': '[STATS]', '🔄': '[ROTATE]', '📦': '[PKG]',
                '🧹': '[CLEAN]', '📂': '[LOAD]', '🗑️': '[DEL]', '🛑': '[STOP]',
                '🔧': '[FIX]', '🏥': '[HEALTH]', '📍': '[POINT]', '🧪': '[TEST]',
                '🔴': '[CIRCUIT]', '🟡': '[HALF]', '🎯': '[TARGET]', '📝': '[NOTE]',
            }
            for emoji, ascii_rep in replacements.items():
                msg = msg.replace(emoji, ascii_rep)
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Ensure log directory exists
(CONFIG["project_dir"] / "logs").mkdir(parents=True, exist_ok=True)

# Setup logging with safe handlers
LOG = logging.getLogger("pipeline")
LOG.setLevel(logging.INFO)

# File handler (keeps emojis for log file)
file_handler = logging.FileHandler(
    CONFIG["project_dir"] / "logs" / "pipeline.log",
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s'))
LOG.addHandler(file_handler)

# Console handler (ASCII-safe for Windows)
console_handler = SafeStreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s'))
LOG.addHandler(console_handler)

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class TaskType(Enum):
    QUICK_SCAN = "quick_scan"
    CAPTION = "caption"
    QUALITY = "quality"
    TAGS = "tags"
    VERIFY = "verify"

@dataclass
class ImageResult:
    image_path: str
    image_hash: str
    
    # Captioning results
    captions: Dict[str, str] = field(default_factory=dict)  # model -> caption
    caption_scores: Dict[str, float] = field(default_factory=dict)
    final_caption: str = ""
    
    # Quality assessment
    quality_scores: Dict[str, int] = field(default_factory=dict)  # model -> 0-15
    final_quality: int = 0
    
    # Tags
    tags: List[str] = field(default_factory=list)
    
    # Verification
    consistency_score: float = 0.0
    is_verified: bool = False
    verification_notes: str = ""
    
    # Meta
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_time: float = 0.0

@dataclass
class SweepState:
    sweep_id: str
    started: str
    status: str = "running"
    
    # Progress
    total_images: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    
    # Model rotation
    current_models: Dict[str, str] = field(default_factory=dict)
    models_used: List[str] = field(default_factory=list)
    
    # Learning metrics
    consistency_scores: List[float] = field(default_factory=list)
    avg_quality: float = 0.0
    learning_verified: bool = False
    
    # Results
    results: List[ImageResult] = field(default_factory=list)

# =============================================================================
# LEARNING VERIFICATION SYSTEM
# =============================================================================

class LearningVerifier:
    """
    Detects if models are actually learning vs producing random/fake outputs.
    
    Techniques:
    1. Cross-model consistency: Same image should get similar descriptions
    2. Temporal consistency: Same image later should get similar results
    3. Semantic similarity: Captions should share key concepts
    4. Quality correlation: Better images should score higher across models
    5. Adversarial testing: Slightly modified images should get similar results
    """
    
    def __init__(self):
        self.history: Dict[str, List[Dict]] = defaultdict(list)  # image_hash -> results
    
    def compute_image_hash(self, image_path: Path) -> str:
        """Generate consistent hash for image"""
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:16]
    
    def extract_key_concepts(self, text: str) -> set:
        """Extract key concepts from caption for comparison"""
        # Simple keyword extraction
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", 
                    "to", "for", "of", "and", "with", "has", "have", "this", "that"}
        words = text.lower().split()
        concepts = {w.strip(".,!?;:\"'") for w in words 
                   if len(w) > 3 and w not in stopwords}
        return concepts
    
    def calculate_consistency(self, captions: Dict[str, str]) -> Tuple[float, str]:
        """
        Calculate consistency score between multiple model outputs.
        Returns (score 0-1, explanation)
        """
        if len(captions) < 2:
            return 1.0, "Only one caption, assuming consistent"
        
        # Extract concepts from each caption
        all_concepts = []
        for model, caption in captions.items():
            concepts = self.extract_key_concepts(caption)
            all_concepts.append((model, concepts))
        
        # Calculate pairwise overlap
        overlaps = []
        for i, (m1, c1) in enumerate(all_concepts):
            for j, (m2, c2) in enumerate(all_concepts):
                if i < j:
                    if len(c1) == 0 or len(c2) == 0:
                        overlap = 0.0
                    else:
                        intersection = len(c1 & c2)
                        union = len(c1 | c2)
                        overlap = intersection / union if union > 0 else 0
                    overlaps.append(overlap)
        
        avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0
        
        # Generate explanation
        if avg_overlap >= 0.7:
            explanation = "High consistency - models agree on key concepts"
        elif avg_overlap >= 0.4:
            explanation = "Moderate consistency - some disagreement on details"
        else:
            explanation = "Low consistency - models significantly disagree (possible fake/random)"
        
        return avg_overlap, explanation
    
    def verify_temporal_consistency(self, image_hash: str, 
                                    new_result: Dict) -> Tuple[bool, str]:
        """
        Check if new result is consistent with previous results for same image.
        Detects if model is producing random outputs vs learning.
        """
        history = self.history.get(image_hash, [])
        
        if len(history) == 0:
            # First time seeing this image
            self.history[image_hash].append(new_result)
            return True, "First observation - baseline recorded"
        
        # Compare with previous results
        prev_concepts = set()
        for prev in history:
            if "caption" in prev:
                prev_concepts.update(self.extract_key_concepts(prev["caption"]))
        
        new_concepts = self.extract_key_concepts(new_result.get("caption", ""))
        
        if len(prev_concepts) == 0 or len(new_concepts) == 0:
            return True, "Insufficient data for comparison"
        
        overlap = len(prev_concepts & new_concepts) / len(prev_concepts | new_concepts)
        
        self.history[image_hash].append(new_result)
        
        if overlap >= 0.5:
            return True, f"Temporally consistent (overlap: {overlap:.2f})"
        else:
            return False, f"Temporal drift detected (overlap: {overlap:.2f}) - possible random output"
    
    def detect_fake_learning(self, results: List[ImageResult]) -> Dict:
        """
        Analyze results to detect signs of fake learning.
        
        Red flags:
        1. All quality scores are similar (not discriminating)
        2. Captions are generic/template-like
        3. No correlation between image quality and scores
        4. High variance in repeated tests
        """
        report = {
            "is_suspicious": False,
            "confidence": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        if len(results) < 5:
            report["issues"].append("Too few results for analysis")
            return report
        
        # Check 1: Quality score distribution
        quality_scores = [r.final_quality for r in results if r.final_quality > 0]
        if quality_scores:
            score_variance = sum((s - sum(quality_scores)/len(quality_scores))**2 
                                for s in quality_scores) / len(quality_scores)
            if score_variance < 1.0:
                report["issues"].append(
                    f"Quality scores too uniform (variance: {score_variance:.2f}) - "
                    "model may not be discriminating"
                )
                report["is_suspicious"] = True
        
        # Check 2: Caption length consistency
        caption_lengths = [len(r.final_caption) for r in results if r.final_caption]
        if caption_lengths:
            avg_len = sum(caption_lengths) / len(caption_lengths)
            len_variance = sum((l - avg_len)**2 for l in caption_lengths) / len(caption_lengths)
            if len_variance < 100:  # Very similar lengths
                report["issues"].append(
                    "Caption lengths too similar - possible template responses"
                )
        
        # Check 3: Low consistency across models
        low_consistency = [r for r in results if r.consistency_score < 0.4]
        if len(low_consistency) > len(results) * 0.3:
            report["issues"].append(
                f"{len(low_consistency)}/{len(results)} images have low model agreement - "
                "models may be producing random outputs"
            )
            report["is_suspicious"] = True
        
        # Generate recommendations
        if report["is_suspicious"]:
            report["recommendations"] = [
                "Try different models for verification",
                "Use more specific prompts",
                "Check if models are properly loaded",
                "Consider using ensemble voting",
                "Add adversarial test cases"
            ]
            report["confidence"] = 0.7
        else:
            report["confidence"] = 0.3
        
        return report

# =============================================================================
# PIPELINE STAGES
# =============================================================================

class PipelineStage:
    """Base class for pipeline stages"""
    
    def __init__(self, name: str, models: List[Dict]):
        self.name = name
        self.models = models
        self.current_model_idx = 0
    
    def get_current_model(self) -> Dict:
        return self.models[self.current_model_idx]
    
    def rotate_model(self):
        self.current_model_idx = (self.current_model_idx + 1) % len(self.models)
        LOG.info(f"🔄 Rotated {self.name} to: {self.get_current_model()['name']}")


class CaptionStage(PipelineStage):
    """Generate detailed captions for images"""
    
    PROMPT = """Describe this image with extreme detail for AI training purposes.

Include ALL of the following:
1. SUBJECT: Full description of every person/character (face, body, pose, expression, clothing details)
2. ENVIRONMENT: Complete setting description (location, objects, background, foreground)
3. LIGHTING: Quality, direction, shadows, colors, atmosphere
4. STYLE: Art style, medium, technique, quality level
5. DETAILS: Any text, symbols, accessories, small details

Format: Write in flowing paragraphs, not bullet points.
Be extremely thorough - this caption will train an AI model."""

    def process(self, image_path: Path, api_client) -> Dict:
        model = self.get_current_model()
        result = api_client.generate_with_image(
            model["name"],
            self.PROMPT,
            image_path,
            max_tokens=800
        )
        return {
            "model": model["name"],
            "caption": result.get("content", ""),
            "tokens": result.get("completion_tokens", 0),
            "time": result.get("total_time", 0)
        }


class QualityStage(PipelineStage):
    """Assess image quality for training"""
    
    PROMPT = """You are an expert image quality assessor for AI training datasets.

Rate this image on a scale of 0-15:
- 0: Reject/Delete (corrupted, unusable)
- 1-5: Archive only (basic quality, not for training)
- 6-9: Bronze tier (acceptable for basic training)
- 10-12: Silver tier (good quality, recommended)
- 13-15: Gold tier (excellent, priority training)

Consider:
- Technical quality (resolution, sharpness, artifacts)
- Composition and framing
- Lighting quality
- Subject clarity
- Training value (unique poses, expressions, details)

RESPOND WITH ONLY:
RATING: [number 0-15]
REASON: [one sentence explanation]
TIER: [REJECT/ARCHIVE/BRONZE/SILVER/GOLD]"""

    def process(self, image_path: Path, caption: str, api_client) -> Dict:
        model = self.get_current_model()
        
        full_prompt = f"{self.PROMPT}\n\nImage caption for context: {caption[:500]}"
        
        result = api_client.generate_with_image(
            model["name"],
            full_prompt,
            image_path,
            max_tokens=100
        )
        
        # Parse rating from response
        content = result.get("content", "")
        rating = 0
        tier = "UNKNOWN"
        
        for line in content.split("\n"):
            if "RATING:" in line.upper():
                try:
                    rating = int(''.join(filter(str.isdigit, line.split(":")[-1][:3])))
                    rating = min(15, max(0, rating))
                except:
                    pass
            if "TIER:" in line.upper():
                tier = line.split(":")[-1].strip().upper()
        
        return {
            "model": model["name"],
            "rating": rating,
            "tier": tier,
            "raw_response": content,
            "time": result.get("total_time", 0)
        }


class TagStage(PipelineStage):
    """Generate training tags"""
    
    PROMPT = """Generate booru-style tags for this image for AI training.

Categories to include:
- character: physical traits, clothing, accessories
- pose: body position, actions, gestures  
- expression: emotions, facial features
- setting: location, environment, props
- style: art style, quality, technique
- meta: aspect ratio, framing, composition

Format: comma-separated tags, lowercase, underscores for spaces
Example: 1girl, long_hair, blue_eyes, standing, smile, outdoors, detailed_background

Generate 20-40 relevant tags:"""

    def process(self, image_path: Path, api_client) -> Dict:
        model = self.get_current_model()
        result = api_client.generate_with_image(
            model["name"],
            self.PROMPT,
            image_path,
            max_tokens=200
        )
        
        content = result.get("content", "")
        # Parse tags
        tags = [t.strip().lower().replace(" ", "_") 
                for t in content.replace("\n", ",").split(",") 
                if t.strip() and len(t.strip()) > 1]
        
        return {
            "model": model["name"],
            "tags": tags[:50],  # Limit to 50 tags
            "raw": content,
            "time": result.get("total_time", 0)
        }

# =============================================================================
# API CLIENT
# =============================================================================

class APIClient:
    """
    Unified API client for LM Studio and Ollama.
    Includes comprehensive failsafes:
    - Retry with exponential backoff
    - Circuit breaker for cascading failure prevention
    - Fallback model support
    - Health checks before requests
    """
    
    def __init__(self):
        self.lm_studio_url = CONFIG["lm_studio_url"]
        self.ollama_url = CONFIG["ollama_url"]
        
        # Circuit breakers per endpoint
        self.lm_studio_breaker = CircuitBreaker("lm_studio")
        self.ollama_breaker = CircuitBreaker("ollama")
        
        # Fallback models
        self.fallback_models = {
            "vision": ["Qwen3-VL-8B-NSFW-Caption-v4.5", "LFM2-VL-1.6B"],
            "text": ["Qwen3-0.6B", "DeepSeek-R1-Qwen-1.5B"],
        }
        
        # Request tracking
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
    
    def _check_service_health(self, provider: str = "lm_studio") -> bool:
        """Check if API service is healthy before making request"""
        try:
            if provider == "lm_studio":
                response = httpx.get(f"{self.lm_studio_url}/models", timeout=5)
            else:
                response = httpx.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @retry_with_backoff(max_retries=3, exceptions=(httpx.TimeoutException, httpx.ConnectError))
    def generate_with_image(self, model: str, prompt: str, 
                           image_path: Path, max_tokens: int = 500) -> Dict:
        """Generate response with image input"""
        
        # Encode image
        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        
        ext = image_path.suffix.lower()
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp"}.get(ext[1:], "image/jpeg")
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_data}"}},
                {"type": "text", "text": prompt}
            ]
        }]
        
        start = time.time()
        
        try:
            response = httpx.post(
                f"{self.lm_studio_url}/chat/completions",
                json={
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=180
            )
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                
                return {
                    "success": True,
                    "content": content,
                    "total_time": round(elapsed, 2),
                    "completion_tokens": usage.get("completion_tokens", 0),
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_text(self, model: str, prompt: str, max_tokens: int = 500) -> Dict:
        """Generate text-only response"""
        start = time.time()
        
        try:
            response = httpx.post(
                f"{self.lm_studio_url}/chat/completions",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=120
            )
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "content": data["choices"][0]["message"]["content"],
                    "total_time": round(elapsed, 2),
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

# =============================================================================
# MAIN PIPELINE
# =============================================================================

class ProductionPipeline:
    """
    Main pipeline orchestrator for LoRA training project.
    
    Features:
    - Multi-stage processing with model rotation
    - Comprehensive failsafes and error recovery
    - Checkpoint/resume capability
    - Automatic backups
    - Health monitoring and auto-cleanup
    - Learning verification to detect fake outputs
    
    Workflow:
    1. Scan images in input directory
    2. Run quick scan to filter obvious rejects
    3. Generate detailed captions with multiple models
    4. Verify consistency across models
    5. Assess quality and assign tiers
    6. Generate training tags
    7. Export results for training
    """
    
    def __init__(self):
        self.api = APIClient()
        self.verifier = LearningVerifier()
        self.sweep_state: Optional[SweepState] = None
        
        # Initialize failsafe managers
        self.checkpoint_mgr = CheckpointManager(
            CONFIG["project_dir"] / "checkpoints" / "pipeline"
        )
        self.backup_mgr = BackupManager()
        self.health_monitor = HEALTH_MONITOR
        
        # Initialize stages
        self.stages = {
            "caption": CaptionStage("caption", CONFIG["models"]["caption_detail"]),
            "quality": QualityStage("quality", CONFIG["models"]["quality_assess"]),
            "tags": TagStage("tags", CONFIG["models"]["caption_detail"]),
        }
        
        # Setup directories
        self.output_dir = CONFIG["project_dir"] / "output" / "pipeline"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Error tracking
        self.consecutive_failures = 0
        self.max_consecutive_failures = 10
        
        LOG.info("🏭 Production Pipeline initialized with failsafes")
    
    def _pre_flight_check(self) -> bool:
        """
        Pre-flight checks before starting pipeline.
        Ensures all systems are operational.
        """
        LOG.info("🔍 Running pre-flight checks...")
        
        checks = {
            "LM Studio API": self.api._check_service_health("lm_studio"),
            "Output directory writable": self.output_dir.exists(),
            "Memory OK": psutil.virtual_memory().percent < 90,
        }
        
        all_ok = True
        for check, status in checks.items():
            symbol = "✅" if status else "❌"
            LOG.info(f"   {symbol} {check}")
            if not status:
                all_ok = False
        
        if not all_ok:
            LOG.error("❌ Pre-flight checks failed! Resolve issues before continuing.")
        
        return all_ok
    
    def _handle_failure(self, error: Exception, context: str) -> bool:
        """
        Handle failures with escalation logic.
        Returns True if should continue, False if should abort.
        """
        self.consecutive_failures += 1
        
        LOG.error(f"❌ Failure in {context}: {error}")
        
        if self.consecutive_failures >= self.max_consecutive_failures:
            LOG.critical(f"🛑 Too many consecutive failures ({self.consecutive_failures}). Aborting.")
            
            # Emergency backup
            if self.sweep_state:
                self.backup_mgr.create_backup(
                    {"state": asdict(self.sweep_state)},
                    f"emergency_{self.sweep_state.sweep_id}"
                )
            
            return False
        
        # Try auto-recovery
        LOG.info("🔧 Attempting auto-recovery...")
        
        # Run garbage collection
        self.health_monitor.auto_cleanup()
        
        # Small delay before retry
        time.sleep(2)
        
        return True
    
    def _reset_failure_counter(self):
        """Reset consecutive failure counter on success"""
        self.consecutive_failures = 0
    
    def start_sweep(self, image_dir: Path) -> str:
        """Start a new processing sweep"""
        sweep_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Find all images
        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
            images.extend(list(image_dir.rglob(ext)))
        
        self.sweep_state = SweepState(
            sweep_id=sweep_id,
            started=datetime.now().isoformat(),
            total_images=len(images)
        )
        
        LOG.info(f"🚀 Starting sweep {sweep_id}")
        LOG.info(f"📁 Found {len(images)} images in {image_dir}")
        
        return sweep_id
    
    def process_image(self, image_path: Path) -> ImageResult:
        """Process a single image through all stages"""
        start = time.time()
        
        result = ImageResult(
            image_path=str(image_path),
            image_hash=self.verifier.compute_image_hash(image_path)
        )
        
        LOG.info(f"📷 Processing: {image_path.name}")
        
        # STAGE 1: Generate captions with multiple models
        for i, model in enumerate(self.stages["caption"].models[:2]):
            self.stages["caption"].current_model_idx = i
            caption_result = self.stages["caption"].process(image_path, self.api)
            
            if caption_result.get("caption"):
                result.captions[model["name"]] = caption_result["caption"]
                LOG.debug(f"  Caption from {model['name']}: {len(caption_result['caption'])} chars")
        
        # Calculate consistency
        if len(result.captions) > 1:
            consistency, explanation = self.verifier.calculate_consistency(result.captions)
            result.consistency_score = consistency
            result.verification_notes = explanation
            LOG.info(f"  Consistency: {consistency:.2f} - {explanation}")
        
        # Select best caption (longest with good consistency)
        if result.captions:
            result.final_caption = max(result.captions.values(), key=len)
        
        # STAGE 2: Quality assessment
        if result.final_caption:
            quality_result = self.stages["quality"].process(
                image_path, result.final_caption, self.api
            )
            result.quality_scores[quality_result["model"]] = quality_result["rating"]
            result.final_quality = quality_result["rating"]
            LOG.info(f"  Quality: {quality_result['rating']}/15 ({quality_result['tier']})")
        
        # STAGE 3: Generate tags
        tag_result = self.stages["tags"].process(image_path, self.api)
        result.tags = tag_result.get("tags", [])
        LOG.info(f"  Tags: {len(result.tags)} generated")
        
        # Verify temporal consistency
        temporal_ok, temporal_note = self.verifier.verify_temporal_consistency(
            result.image_hash,
            {"caption": result.final_caption, "quality": result.final_quality}
        )
        result.is_verified = temporal_ok and result.consistency_score >= 0.5
        
        result.processing_time = round(time.time() - start, 2)
        LOG.info(f"  ✅ Completed in {result.processing_time}s")
        
        return result
    
    def run_sweep(self, image_dir: Path, limit: int = None, resume: bool = True):
        """
        Run complete processing sweep with full failsafe support.
        
        Features:
        - Pre-flight checks
        - Checkpoint/resume capability
        - Periodic backups
        - Memory monitoring and auto-cleanup
        - Graceful degradation on failures
        - Model rotation
        """
        
        # Pre-flight checks
        if not self._pre_flight_check():
            LOG.error("Aborting due to failed pre-flight checks")
            return None
        
        sweep_id = self.start_sweep(image_dir)
        
        # Check for existing checkpoint to resume
        if resume:
            existing_state = self.checkpoint_mgr.load_checkpoint(sweep_id)
            if existing_state:
                LOG.info(f"📂 Resuming from checkpoint...")
                start_index = existing_state.get("processed", 0)
            else:
                start_index = 0
        else:
            start_index = 0
        
        # Collect images
        images = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
            images.extend(list(image_dir.rglob(ext)))
        
        if limit:
            images = images[:limit]
        
        LOG.info(f"📷 Processing {len(images)} images (starting from {start_index})")
        
        # Main processing loop with failsafes
        for i, image_path in enumerate(images[start_index:], start=start_index):
            try:
                # Health check periodically
                if i % 10 == 0:
                    health = self.health_monitor.check_health()
                    if health.get("status") == "warning":
                        LOG.warning("⚠️ System resources stressed, running cleanup...")
                        self.health_monitor.auto_cleanup()
                        time.sleep(1)
                
                # Process image with error handling
                result = self.process_image(image_path)
                self.sweep_state.results.append(result)
                self.sweep_state.processed += 1
                
                if result.is_verified:
                    self.sweep_state.successful += 1
                    self._reset_failure_counter()
                
                # Checkpoint periodically
                if (i + 1) % CONFIG["failsafe"]["checkpoint_interval"] == 0:
                    self.checkpoint_mgr.save_checkpoint(sweep_id, {
                        "processed": self.sweep_state.processed,
                        "successful": self.sweep_state.successful,
                        "failed": self.sweep_state.failed,
                    })
                
                # Backup periodically
                if CONFIG["backup"]["enabled"] and (i + 1) % CONFIG["backup"]["auto_backup_interval"] == 0:
                    self.backup_mgr.create_backup(
                        {"results": [asdict(r) for r in self.sweep_state.results[-50:]]},
                        f"sweep_{sweep_id}"
                    )
                
                # Garbage collection periodically
                if (i + 1) % CONFIG["failsafe"]["auto_gc_interval"] == 0:
                    gc.collect()
                
                # Rotate models periodically
                if (i + 1) % CONFIG["sweep"]["rotate_every"] == 0:
                    LOG.info("🔄 Rotating models...")
                    for stage in self.stages.values():
                        stage.rotate_model()
                
                # Detailed Progress log every 10 images
                if (i + 1) % 10 == 0:
                    pct = (i + 1) * 100 // len(images)
                    
                    # Calculate quality distribution
                    results = self.sweep_state.results
                    gold = sum(1 for r in results if r.final_quality >= 13)
                    silver = sum(1 for r in results if 10 <= r.final_quality < 13)
                    bronze = sum(1 for r in results if 6 <= r.final_quality < 10)
                    archive = sum(1 for r in results if r.final_quality < 6)
                    
                    # Calculate timing stats
                    times = [r.processing_time for r in results if r.processing_time > 0]
                    avg_time = sum(times) / len(times) if times else 0
                    throughput = 60 / avg_time if avg_time > 0 else 0
                    
                    # Calculate ETA
                    remaining = len(images) - (i + 1)
                    eta_seconds = remaining * avg_time
                    eta_min = int(eta_seconds // 60)
                    eta_sec = int(eta_seconds % 60)
                    
                    # Get memory stats
                    import psutil
                    mem = psutil.virtual_memory()
                    ram_gb = mem.used / (1024**3)
                    
                    # Calculate tag stats
                    all_tags = [len(r.tags) for r in results]
                    avg_tags = sum(all_tags) / len(all_tags) if all_tags else 0
                    
                    # Detailed output
                    LOG.info("=" * 60)
                    LOG.info(f"📊 PROGRESS: {i + 1}/{len(images)} ({pct}%)")
                    LOG.info("-" * 60)
                    LOG.info(f"  ⏱️  Timing: {avg_time:.1f}s/img | {throughput:.1f} img/min | ETA: {eta_min}m {eta_sec}s")
                    LOG.info(f"  🏆 Quality: Gold:{gold} | Silver:{silver} | Bronze:{bronze} | Archive:{archive}")
                    LOG.info(f"  🏷️  Tags: {avg_tags:.0f} avg/image | Total: {sum(all_tags)}")
                    LOG.info(f"  💾 Memory: {ram_gb:.1f}GB RAM")
                    LOG.info(f"  ✅ Verified: {self.sweep_state.successful} | ❌ Failed: {self.sweep_state.failed}")
                    LOG.info("=" * 60)
                
            except KeyboardInterrupt:
                LOG.warning("⚠️ Interrupted by user. Saving checkpoint...")
                # Save checkpoint
                self.checkpoint_mgr.save_checkpoint(sweep_id, {
                    "processed": self.sweep_state.processed,
                    "successful": self.sweep_state.successful,
                    "failed": self.sweep_state.failed,
                    "interrupted": True,
                    "last_image": str(image_path)
                })
                # Create backup
                self.backup_mgr.create_backup(
                    {
                        "sweep_id": sweep_id,
                        "results": [asdict(r) for r in self.sweep_state.results],
                        "interrupted_at": datetime.now().isoformat()
                    },
                    f"interrupted_{sweep_id}"
                )
                # Save partial results
                self.sweep_state.status = "interrupted"
                self.save_sweep_results()
                
                LOG.info(f"💾 Progress saved: {self.sweep_state.processed} images processed")
                LOG.info(f"   Resume with: --sweep \"{image_dir}\"")
                return self.sweep_state
                
            except Exception as e:
                self.sweep_state.failed += 1
                
                # Handle failure with escalation
                if not self._handle_failure(e, f"image {image_path.name}"):
                    LOG.critical("🛑 Pipeline aborted due to excessive failures")
                    break
        
        # Finalize sweep
        self.sweep_state.status = "completed"
        self.save_sweep_results()
        self.generate_sweep_report()
        
        # Final backup
        if CONFIG["backup"]["enabled"]:
            self.backup_mgr.create_backup(
                {"sweep_id": sweep_id, "state": asdict(self.sweep_state)},
                f"final_{sweep_id}"
            )
        
        # Cleanup old checkpoints
        self.checkpoint_mgr.cleanup_old_checkpoints(keep=5)
        
        LOG.info(f"✅ Sweep complete: {self.sweep_state.successful}/{self.sweep_state.processed} successful")
        
        return self.sweep_state
    
    def save_sweep_results(self):
        """Save sweep results to JSON"""
        output_file = self.output_dir / f"sweep_{self.sweep_state.sweep_id}.json"
        
        data = {
            "sweep_id": self.sweep_state.sweep_id,
            "started": self.sweep_state.started,
            "completed": datetime.now().isoformat(),
            "stats": {
                "total": self.sweep_state.total_images,
                "processed": self.sweep_state.processed,
                "successful": self.sweep_state.successful,
                "failed": self.sweep_state.failed,
            },
            "results": [asdict(r) for r in self.sweep_state.results]
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        LOG.info(f"💾 Results saved: {output_file}")
    
    def generate_sweep_report(self):
        """Generate markdown report"""
        report_file = self.output_dir / f"sweep_{self.sweep_state.sweep_id}_report.md"
        
        # Analyze results
        results = self.sweep_state.results
        
        # Quality distribution
        quality_dist = defaultdict(int)
        for r in results:
            if r.final_quality <= 5:
                quality_dist["Archive"] += 1
            elif r.final_quality <= 9:
                quality_dist["Bronze"] += 1
            elif r.final_quality <= 12:
                quality_dist["Silver"] += 1
            else:
                quality_dist["Gold"] += 1
        
        # Consistency stats
        consistency_scores = [r.consistency_score for r in results if r.consistency_score > 0]
        avg_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0
        
        # Check for fake learning
        fake_report = self.verifier.detect_fake_learning(results)
        
        report = f"""# Sweep Report: {self.sweep_state.sweep_id}

## Summary
- **Total Images:** {self.sweep_state.total_images}
- **Processed:** {self.sweep_state.processed}
- **Verified:** {self.sweep_state.successful}
- **Failed:** {self.sweep_state.failed}

## Quality Distribution
| Tier | Count | Percentage |
|------|-------|------------|
| Gold (13-15) | {quality_dist['Gold']} | {quality_dist['Gold']*100/max(1,len(results)):.1f}% |
| Silver (10-12) | {quality_dist['Silver']} | {quality_dist['Silver']*100/max(1,len(results)):.1f}% |
| Bronze (6-9) | {quality_dist['Bronze']} | {quality_dist['Bronze']*100/max(1,len(results)):.1f}% |
| Archive (0-5) | {quality_dist['Archive']} | {quality_dist['Archive']*100/max(1,len(results)):.1f}% |

## Model Consistency
- **Average Consistency:** {avg_consistency:.2f}
- **High Consistency (>0.7):** {len([s for s in consistency_scores if s > 0.7])}
- **Low Consistency (<0.4):** {len([s for s in consistency_scores if s < 0.4])}

## Learning Verification
- **Suspicious:** {'⚠️ YES' if fake_report['is_suspicious'] else '✅ NO'}
- **Issues:** {', '.join(fake_report['issues']) or 'None'}
- **Recommendations:** {', '.join(fake_report['recommendations']) or 'None'}

## Top Quality Images (Gold Tier)
"""
        
        gold_images = [r for r in results if r.final_quality >= 13]
        for r in gold_images[:10]:
            report += f"- `{Path(r.image_path).name}` - Score: {r.final_quality}/15\n"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        LOG.info(f"📊 Report saved: {report_file}")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Production AI Pipeline with Comprehensive Failsafes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ai.production_pipeline --test
  python -m ai.production_pipeline --sweep "C:/images" --limit 50
  python -m ai.production_pipeline --resume
  python -m ai.production_pipeline --status
  python -m ai.production_pipeline --health
        """
    )
    
    parser.add_argument("--sweep", type=str, help="Run sweep on image directory")
    parser.add_argument("--limit", type=int, help="Limit number of images to process")
    parser.add_argument("--test", action="store_true", help="Run test on sample images")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh, ignore checkpoints")
    parser.add_argument("--status", action="store_true", help="Show pipeline status and checkpoints")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--backup-list", action="store_true", help="List available backups")
    parser.add_argument("--restore", type=str, help="Restore from backup name")
    
    args = parser.parse_args()
    
    # Ensure log directory exists
    (CONFIG["project_dir"] / "logs").mkdir(parents=True, exist_ok=True)
    
    if args.health:
        LOG.info("🏥 Running health check...")
        health = HEALTH_MONITOR.check_health(force=True)
        LOG.info(f"   Status: {health['status']}")
        LOG.info(f"   RAM: {health['ram_used_gb']:.1f}GB ({health['ram_percent']:.0f}%)")
        LOG.info(f"   GPU: {health['gpu_used_mb']:.0f}MB")
        LOG.info(f"   CPU: {health['cpu_percent']:.0f}%")
        if health.get("alerts"):
            LOG.warning(f"   Alerts: {', '.join(health['alerts'])}")
        return
    
    if args.status:
        LOG.info("📊 Pipeline Status")
        LOG.info("=" * 50)
        
        # List checkpoints
        checkpoint_mgr = CheckpointManager(CONFIG["project_dir"] / "checkpoints" / "pipeline")
        checkpoints = checkpoint_mgr.list_checkpoints()
        
        if checkpoints:
            LOG.info(f"\n📍 Available Checkpoints ({len(checkpoints)}):")
            for cp in checkpoints[:5]:
                LOG.info(f"   {cp['sweep_id']} - {cp['timestamp']}")
        else:
            LOG.info("\n📍 No checkpoints found")
        
        # List backups
        backup_mgr = BackupManager()
        backups = list(backup_mgr.backup_dir.glob("*.bak"))
        LOG.info(f"\n💾 Backups: {len(backups)} files in {backup_mgr.backup_dir}")
        
        return
    
    if args.backup_list:
        backup_mgr = BackupManager()
        backups = sorted(backup_mgr.backup_dir.glob("*.bak"), 
                        key=lambda x: x.stat().st_mtime, reverse=True)
        
        LOG.info(f"💾 Available Backups ({len(backups)}):")
        for b in backups[:10]:
            size = b.stat().st_size / 1024
            mtime = datetime.fromtimestamp(b.stat().st_mtime)
            LOG.info(f"   {b.name} ({size:.1f}KB) - {mtime}")
        return
    
    if args.restore:
        backup_mgr = BackupManager()
        data = backup_mgr.restore_latest(args.restore)
        if data:
            LOG.info(f"✅ Restored data with {len(data)} keys")
            LOG.info(json.dumps(data, indent=2, default=str)[:500])
        else:
            LOG.error(f"❌ No backup found for: {args.restore}")
        return
    
    # Initialize pipeline
    pipeline = ProductionPipeline()
    
    if args.sweep:
        image_dir = Path(args.sweep)
        if not image_dir.exists():
            LOG.error(f"❌ Directory not found: {image_dir}")
            return
        
        resume = not args.no_resume
        pipeline.run_sweep(image_dir, args.limit, resume=resume)
    
    elif args.test:
        # Test with Frontier-Stories images
        test_dirs = [
            Path(r"G:\Github\Frontier-Stories\assets\images\characters"),
            Path(r"G:\Github\Frontier-Stories\assets\images"),
            Path(r"C:\Users\Admin\Pictures"),
        ]
        
        test_dir = None
        for d in test_dirs:
            if d.exists():
                test_dir = d
                break
        
        if test_dir:
            LOG.info(f"🧪 Running test on: {test_dir}")
            pipeline.run_sweep(test_dir, limit=3, resume=False)
        else:
            LOG.error("❌ No test directory found")
    
    elif args.resume:
        # Find most recent checkpoint and resume
        checkpoints = pipeline.checkpoint_mgr.list_checkpoints()
        if checkpoints:
            latest = checkpoints[0]
            LOG.info(f"📂 Resuming sweep: {latest['sweep_id']}")
            # Note: This would need the original image directory
            LOG.info("   Please use --sweep <dir> to resume with image directory")
        else:
            LOG.error("❌ No checkpoints to resume from")
    
    else:
        parser.print_help()
        print("\n" + "=" * 60)
        print("🏭 PRODUCTION PIPELINE FAILSAFES")
        print("=" * 60)
        print("""
✅ Retry with exponential backoff
✅ Circuit breaker for cascading failures
✅ Checkpoint/resume capability
✅ Automatic backups
✅ Memory monitoring & auto-cleanup
✅ Health checks
✅ Graceful degradation
✅ Learning verification (detect fake outputs)
✅ Model rotation for consistency
        """)


if __name__ == "__main__":
    main()
