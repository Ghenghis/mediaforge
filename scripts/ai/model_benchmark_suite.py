"""
Comprehensive Model Benchmark Suite
- Tests models one by one with proper load/unload
- Supports both Ollama and LM Studio
- Monitors memory and performance
- Logs everything for analysis
- Auto-corrects issues
"""

import os
import sys
import json
import time
import httpx
import base64
import psutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    "lm_studio": {
        "api_url": "http://localhost:1234/v1",
        "models_dir": Path(r"C:\Users\Admin\.lmstudio\models"),
    },
    "ollama": {
        "api_url": "http://localhost:11434",
    },
    "logs_dir": Path(r"C:\Users\Admin\civitai\logs\benchmarks"),
    "results_dir": Path(r"C:\Users\Admin\civitai\reports\benchmarks"),
    "test_images_dir": Path(r"G:\Github\Frontier-Stories\assets\images"),
    "max_memory_gb": 20,  # Alert if memory exceeds this
    "test_timeout": 180,  # seconds
}

# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """Setup comprehensive logging"""
    CONFIG["logs_dir"].mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = CONFIG["logs_dir"] / f"benchmark_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger("benchmark")
    logger.setLevel(logging.DEBUG)
    
    # File handler - detailed
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    ))
    
    # Console handler - summary
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(message)s'))
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    logger.info(f"📝 Logging to: {log_file}")
    return logger, log_file

LOG, LOG_FILE = setup_logging()

# =============================================================================
# MEMORY MONITORING
# =============================================================================

@dataclass
class MemorySnapshot:
    timestamp: str
    ram_used_gb: float
    ram_total_gb: float
    ram_percent: float
    gpu_used_mb: float = 0
    gpu_total_mb: float = 0
    process_name: str = ""

def get_memory_snapshot(process_name: str = "") -> MemorySnapshot:
    """Get current memory usage"""
    mem = psutil.virtual_memory()
    
    gpu_used = 0
    gpu_total = 0
    
    # Try to get GPU memory via nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", 
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            gpu_used = float(parts[0].strip())
            gpu_total = float(parts[1].strip())
    except:
        pass
    
    return MemorySnapshot(
        timestamp=datetime.now().isoformat(),
        ram_used_gb=round(mem.used / (1024**3), 2),
        ram_total_gb=round(mem.total / (1024**3), 2),
        ram_percent=round(mem.percent, 1),
        gpu_used_mb=gpu_used,
        gpu_total_mb=gpu_total,
        process_name=process_name
    )

def log_memory(label: str = ""):
    """Log current memory state"""
    snap = get_memory_snapshot(label)
    LOG.debug(f"Memory [{label}]: RAM {snap.ram_used_gb}/{snap.ram_total_gb}GB ({snap.ram_percent}%), "
              f"GPU {snap.gpu_used_mb}/{snap.gpu_total_mb}MB")
    
    # Alert if memory too high
    if snap.ram_used_gb > CONFIG["max_memory_gb"]:
        LOG.warning(f"⚠️ HIGH MEMORY: {snap.ram_used_gb}GB RAM used!")
    
    return snap

# =============================================================================
# OLLAMA MANAGEMENT
# =============================================================================

class OllamaManager:
    """Manage Ollama models"""
    
    def __init__(self):
        self.api_url = CONFIG["ollama"]["api_url"]
    
    def is_running(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = httpx.get(f"{self.api_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[Dict]:
        """List available Ollama models"""
        try:
            response = httpx.get(f"{self.api_url}/api/tags", timeout=10)
            if response.status_code == 200:
                return response.json().get("models", [])
        except Exception as e:
            LOG.error(f"Ollama list error: {e}")
        return []
    
    def get_loaded_models(self) -> List[str]:
        """Get currently loaded models"""
        try:
            response = httpx.get(f"{self.api_url}/api/ps", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
        except:
            pass
        return []
    
    def unload_all(self) -> bool:
        """Unload all models from memory"""
        LOG.info("🔄 Unloading all Ollama models...")
        loaded = self.get_loaded_models()
        
        for model in loaded:
            try:
                # Send empty keep_alive to unload
                httpx.post(
                    f"{self.api_url}/api/generate",
                    json={"model": model, "keep_alive": 0},
                    timeout=30
                )
                LOG.debug(f"  Unloaded: {model}")
            except Exception as e:
                LOG.error(f"  Failed to unload {model}: {e}")
        
        time.sleep(2)
        
        remaining = self.get_loaded_models()
        if remaining:
            LOG.warning(f"⚠️ Models still loaded: {remaining}")
            return False
        
        LOG.info("✅ All Ollama models unloaded")
        return True
    
    def load_model(self, model_name: str) -> bool:
        """Load a specific model"""
        LOG.info(f"📦 Loading Ollama model: {model_name}")
        log_memory("before_load")
        
        try:
            # Warm up the model
            response = httpx.post(
                f"{self.api_url}/api/generate",
                json={"model": model_name, "prompt": "test", "stream": False},
                timeout=120
            )
            
            if response.status_code == 200:
                log_memory("after_load")
                LOG.info(f"✅ Loaded: {model_name}")
                return True
            else:
                LOG.error(f"❌ Load failed: {response.status_code}")
                return False
                
        except Exception as e:
            LOG.error(f"❌ Load error: {e}")
            return False
    
    def generate(self, model: str, prompt: str, max_tokens: int = 500) -> Dict:
        """Generate response from model"""
        start = time.time()
        
        try:
            response = httpx.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens}
                },
                timeout=CONFIG["test_timeout"]
            )
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("response", "")
                
                return {
                    "success": True,
                    "content": content,
                    "total_time": round(elapsed, 2),
                    "eval_count": data.get("eval_count", len(content.split())),
                    "tps": round(data.get("eval_count", 0) / elapsed, 1) if elapsed > 0 else 0
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "total_time": time.time() - start}

# =============================================================================
# LM STUDIO MANAGEMENT
# =============================================================================

class LMStudioManager:
    """Manage LM Studio models"""
    
    def __init__(self):
        self.api_url = CONFIG["lm_studio"]["api_url"]
        self.models_dir = CONFIG["lm_studio"]["models_dir"]
    
    def is_running(self) -> bool:
        """Check if LM Studio API is running"""
        try:
            response = httpx.get(f"{self.api_url}/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_loaded_model(self) -> Optional[str]:
        """Get currently loaded model"""
        try:
            response = httpx.get(f"{self.api_url}/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    return data["data"][0].get("id")
        except:
            pass
        return None
    
    def scan_models(self) -> List[Dict]:
        """Scan all available models"""
        models = []
        
        for gguf in self.models_dir.rglob("*.gguf"):
            if "mmproj" in gguf.name.lower():
                continue
            
            size_gb = gguf.stat().st_size / (1024**3)
            is_vision = any(x in gguf.name.lower() for x in 
                          ["vl", "vision", "llava", "pixtral", "caption"])
            
            models.append({
                "name": gguf.stem,
                "path": str(gguf),
                "size_gb": round(size_gb, 2),
                "is_vision": is_vision,
                "parent": gguf.parent.name
            })
        
        return sorted(models, key=lambda x: x["size_gb"])
    
    def generate(self, prompt: str, image_path: Optional[Path] = None,
                 max_tokens: int = 500) -> Dict:
        """Generate response from loaded model"""
        
        messages = []
        
        if image_path and image_path.exists():
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            
            ext = image_path.suffix.lower()
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png", "webp": "image/webp"}.get(ext[1:], "image/jpeg")
            
            messages.append({
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_data}"}},
                    {"type": "text", "text": prompt}
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})
        
        start = time.time()
        
        try:
            response = httpx.post(
                f"{self.api_url}/chat/completions",
                json={
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=CONFIG["test_timeout"]
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
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "tps": round(usage.get("completion_tokens", 0) / elapsed, 1) if elapsed > 0 else 0
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "total_time": time.time() - start}

# =============================================================================
# BENCHMARK TESTS
# =============================================================================

TEST_PROMPTS = {
    "detail_vision": """Describe this image with extreme detail. Include:
- Every visible person/character (full appearance, clothing, pose, expression, body language)
- Complete environment (setting, all objects, background elements, foreground)
- Lighting quality (direction, color, shadows, highlights, atmosphere)
- Technical aspects (composition, focus, art style, quality)
- Any text, symbols, logos, or notable small details
Be exhaustive - describe absolutely everything visible.""",

    "detail_text": """Write an extremely detailed scene: A mysterious stranger rides into 
a frontier town at sunset. Include:
- Full physical description of the stranger (clothing, weapons, horse, posture)
- Town environment (buildings, people watching, sounds, smells)
- Atmospheric details (lighting, dust, temperature, mood)
- Subtle hints about the stranger's past
- Sensory immersion (what characters would see, hear, feel, smell)
Make it 3-4 paragraphs of rich, literary prose.""",

    "speed_vision": "Briefly describe this image in 2-3 sentences.",
    
    "speed_text": "Write a one-paragraph scene of someone entering a saloon.",
    
    "coding": """Write a Python class for managing AI model benchmarks with:
- Methods: run_test, save_results, load_results, generate_report
- Proper error handling and logging
- Type hints and docstrings
- Example usage""",

    "reasoning": """Analyze step-by-step: You have 10,000 images for LoRA training.
60% high quality, 30% medium, 10% low. GPU has 24GB VRAM. 
Training takes 2 hours per 1000 images.
Question: What's the optimal dataset size and quality threshold?
Show your complete reasoning process."""
}

@dataclass  
class TestResult:
    model_name: str
    provider: str  # "ollama" or "lm_studio"
    test_type: str
    
    # Timing
    total_time: float
    tokens_per_second: float
    
    # Quality
    output_length: int
    detail_score: float
    
    # Memory
    memory_before_gb: float
    memory_after_gb: float
    memory_delta_gb: float
    gpu_memory_mb: float
    
    # Meta
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    error: str = ""
    notes: str = ""

def calculate_detail_score(text: str) -> float:
    """Score output detail 0-10"""
    if not text:
        return 0.0
    
    score = 0.0
    length = len(text)
    
    # Length scoring
    if length > 1500: score += 4.0
    elif length > 1000: score += 3.0
    elif length > 500: score += 2.0
    elif length > 200: score += 1.0
    
    # Detail markers
    detail_words = ["wearing", "appears", "expression", "positioned", "visible",
                   "background", "foreground", "lighting", "shadow", "color",
                   "detailed", "specifically", "notably", "features", "style"]
    score += min(3.0, sum(0.3 for w in detail_words if w in text.lower()))
    
    # Structure
    if text.count("\n") > 3: score += 1.0
    if text.count(":") > 2: score += 0.5
    if any(f"{i}." in text for i in range(1, 6)): score += 0.5
    
    return min(10.0, round(score, 1))

# =============================================================================
# MAIN BENCHMARK RUNNER
# =============================================================================

class BenchmarkSuite:
    """Main benchmark orchestrator"""
    
    def __init__(self):
        self.ollama = OllamaManager()
        self.lmstudio = LMStudioManager()
        self.results: List[TestResult] = []
        self.results_file = CONFIG["results_dir"] / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        CONFIG["results_dir"].mkdir(parents=True, exist_ok=True)
    
    def check_services(self) -> Dict[str, bool]:
        """Check which services are available"""
        status = {
            "ollama": self.ollama.is_running(),
            "lm_studio": self.lmstudio.is_running()
        }
        
        LOG.info("=" * 60)
        LOG.info("  SERVICE STATUS")
        LOG.info("=" * 60)
        LOG.info(f"  Ollama:    {'✅ Running' if status['ollama'] else '❌ Not running'}")
        LOG.info(f"  LM Studio: {'✅ Running' if status['lm_studio'] else '❌ Not running'}")
        
        return status
    
    def prepare_test_environment(self) -> bool:
        """Ensure clean test environment"""
        LOG.info("\n" + "=" * 60)
        LOG.info("  PREPARING TEST ENVIRONMENT")
        LOG.info("=" * 60)
        
        initial_mem = log_memory("initial")
        
        # Unload Ollama models
        if self.ollama.is_running():
            self.ollama.unload_all()
        
        # Check LM Studio (user must manually unload)
        if self.lmstudio.is_running():
            loaded = self.lmstudio.get_loaded_model()
            if loaded:
                LOG.info(f"📦 LM Studio has model loaded: {loaded}")
                LOG.info("   (Will test this model)")
        
        time.sleep(3)
        final_mem = log_memory("after_cleanup")
        
        LOG.info(f"✅ Environment ready. RAM freed: {initial_mem.ram_used_gb - final_mem.ram_used_gb:.1f} GB")
        return True
    
    def run_single_test(self, provider: str, model_name: str, 
                        test_type: str, image_path: Optional[Path] = None) -> TestResult:
        """Run a single benchmark test"""
        
        LOG.info(f"\n{'─' * 50}")
        LOG.info(f"🧪 Testing: {model_name}")
        LOG.info(f"   Provider: {provider} | Test: {test_type}")
        LOG.info(f"{'─' * 50}")
        
        mem_before = get_memory_snapshot()
        
        # Select prompt
        if "vision" in test_type and image_path:
            prompt = TEST_PROMPTS.get(test_type, TEST_PROMPTS["detail_vision"])
        else:
            prompt = TEST_PROMPTS.get(test_type, TEST_PROMPTS["detail_text"])
        
        # Run test
        if provider == "ollama":
            result = self.ollama.generate(model_name, prompt)
        else:
            result = self.lmstudio.generate(prompt, image_path)
        
        mem_after = get_memory_snapshot()
        
        # Calculate scores
        content = result.get("content", "")
        detail_score = calculate_detail_score(content)
        
        test_result = TestResult(
            model_name=model_name,
            provider=provider,
            test_type=test_type,
            total_time=result.get("total_time", 0),
            tokens_per_second=result.get("tps", 0),
            output_length=len(content),
            detail_score=detail_score,
            memory_before_gb=mem_before.ram_used_gb,
            memory_after_gb=mem_after.ram_used_gb,
            memory_delta_gb=round(mem_after.ram_used_gb - mem_before.ram_used_gb, 2),
            gpu_memory_mb=mem_after.gpu_used_mb,
            success=result.get("success", False),
            error=result.get("error", "")
        )
        
        # Log results
        if test_result.success:
            LOG.info(f"✅ Success!")
            LOG.info(f"   ⏱️  Time: {test_result.total_time}s | Speed: {test_result.tokens_per_second} tok/s")
            LOG.info(f"   📝 Output: {test_result.output_length} chars | Detail: {test_result.detail_score}/10")
            LOG.info(f"   💾 Memory Δ: {test_result.memory_delta_gb:+.2f} GB | GPU: {test_result.gpu_memory_mb} MB")
        else:
            LOG.error(f"❌ Failed: {test_result.error}")
        
        self.results.append(test_result)
        return test_result
    
    def run_lmstudio_test(self, image_path: Optional[Path] = None):
        """Test currently loaded LM Studio model"""
        if not self.lmstudio.is_running():
            LOG.error("LM Studio not running!")
            return
        
        model = self.lmstudio.get_loaded_model()
        if not model:
            LOG.error("No model loaded in LM Studio!")
            return
        
        # Determine test type
        is_vision = any(x in model.lower() for x in ["vl", "vision", "caption", "llava"])
        
        if is_vision and image_path:
            self.run_single_test("lm_studio", model, "detail_vision", image_path)
            self.run_single_test("lm_studio", model, "speed_vision", image_path)
        else:
            self.run_single_test("lm_studio", model, "detail_text")
            self.run_single_test("lm_studio", model, "speed_text")
    
    def save_results(self):
        """Save all results to JSON"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "results": [asdict(r) for r in self.results]
        }
        
        with open(self.results_file, "w") as f:
            json.dump(data, f, indent=2)
        
        LOG.info(f"\n📁 Results saved: {self.results_file}")
    
    def generate_summary(self):
        """Generate summary of results"""
        if not self.results:
            LOG.info("No results to summarize")
            return
        
        LOG.info("\n" + "=" * 60)
        LOG.info("  BENCHMARK SUMMARY")
        LOG.info("=" * 60)
        
        successful = [r for r in self.results if r.success]
        
        if successful:
            # Best detail
            best_detail = max(successful, key=lambda x: x.detail_score)
            LOG.info(f"\n🏆 Best Detail: {best_detail.model_name}")
            LOG.info(f"   Score: {best_detail.detail_score}/10 | {best_detail.output_length} chars")
            
            # Best speed
            best_speed = max(successful, key=lambda x: x.tokens_per_second)
            LOG.info(f"\n⚡ Fastest: {best_speed.model_name}")
            LOG.info(f"   Speed: {best_speed.tokens_per_second} tok/s")
            
            # Memory efficiency
            lowest_mem = min(successful, key=lambda x: x.memory_delta_gb)
            LOG.info(f"\n💾 Most Efficient: {lowest_mem.model_name}")
            LOG.info(f"   Memory Δ: {lowest_mem.memory_delta_gb:+.2f} GB")
        
        LOG.info(f"\n📊 Total tests: {len(self.results)} | Successful: {len(successful)}")

# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Model Benchmark Suite")
    parser.add_argument("--check", action="store_true", help="Check service status")
    parser.add_argument("--prepare", action="store_true", help="Prepare test environment")
    parser.add_argument("--test", action="store_true", help="Test loaded LM Studio model")
    parser.add_argument("--image", type=str, help="Image path for vision tests")
    parser.add_argument("--scan", action="store_true", help="Scan all models")
    args = parser.parse_args()
    
    suite = BenchmarkSuite()
    
    if args.check:
        suite.check_services()
        return
    
    if args.prepare:
        suite.prepare_test_environment()
        return
    
    if args.scan:
        models = suite.lmstudio.scan_models()
        LOG.info(f"\n📦 Found {len(models)} LM Studio models")
        
        vision = [m for m in models if m["is_vision"]]
        text = [m for m in models if not m["is_vision"]]
        
        LOG.info(f"\n🖼️  Vision models: {len(vision)}")
        for m in sorted(vision, key=lambda x: x["size_gb"], reverse=True)[:10]:
            LOG.info(f"   {m['size_gb']:6.1f} GB  {m['name'][:50]}")
        
        LOG.info(f"\n📝 Text models: {len(text)}")
        for m in sorted(text, key=lambda x: x["size_gb"], reverse=True)[:10]:
            LOG.info(f"   {m['size_gb']:6.1f} GB  {m['name'][:50]}")
        return
    
    if args.test:
        image_path = Path(args.image) if args.image else None
        
        # Find test image if not provided
        if not image_path:
            test_dir = CONFIG["test_images_dir"]
            if test_dir.exists():
                images = list(test_dir.rglob("*.jpg"))[:1]
                if images:
                    image_path = images[0]
                    LOG.info(f"📷 Using test image: {image_path.name}")
        
        suite.prepare_test_environment()
        suite.run_lmstudio_test(image_path)
        suite.save_results()
        suite.generate_summary()
        return
    
    parser.print_help()

if __name__ == "__main__":
    main()
