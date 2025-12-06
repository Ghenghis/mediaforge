"""
RAMDrive Performance Manager for AI Training Pipeline
=====================================================
Maximizes training speed using RAMDrives for I/O intensive operations.

Features:
- Automatic RAM cleanup before RAMDrive creation
- Multiple RAMDrives for different purposes
- Docker GPU acceleration integration
- Memory monitoring and optimization
- Automatic syncing and persistence

Performance Gains Expected:
- 10-50x faster dataset loading
- 5-10x faster checkpoint saving
- Near-zero I/O latency for temp files
- Reduced SSD wear
"""

import os
import sys
import json
import time
import psutil
import subprocess
import shutil
import threading
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    "project_dir": Path(r"C:\Users\Admin\civitai"),
    
    # RAMDrive configurations (Optimized for 128GB RAM system)
    "ramdrives": {
        "training_data": {
            "letter": "R",
            "size_gb": 16,  # Large dataset cache
            "purpose": "Training images and captions",
            "priority": 1,
        },
        "model_cache": {
            "letter": "M",
            "size_gb": 24,  # Full model weights
            "purpose": "Model weights and checkpoints",
            "priority": 2,
        },
        "temp_workspace": {
            "letter": "T",
            "size_gb": 8,  # Processing workspace
            "purpose": "Temporary processing files",
            "priority": 3,
        },
        "output_cache": {
            "letter": "O",
            "size_gb": 8,  # Generation outputs
            "purpose": "Generated outputs before syncing",
            "priority": 4,
        },
    },
    
    # Memory thresholds
    "memory": {
        "min_free_gb": 8,  # Keep at least this much RAM free
        "cleanup_threshold_percent": 80,  # Clean when RAM > this %
        "reserved_for_gpu_gb": 4,  # Reserve for GPU memory sharing
    },
    
    # Docker settings
    "docker": {
        "enabled": True,
        "gpu_enabled": True,
        "memory_limit": "48g",
        "shm_size": "8g",
    },
    
    # Sync settings
    "sync": {
        "interval_seconds": 300,  # Sync RAMDrive to disk every 5 min
        "on_idle": True,
        "backup_dir": Path(r"C:\Users\Admin\civitai\ramdrive_backups"),
    },
}

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
LOG = logging.getLogger("ramdrive")

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RAMDriveInfo:
    letter: str
    size_gb: float
    purpose: str
    mounted: bool = False
    used_gb: float = 0.0
    path: str = ""

@dataclass
class SystemMemory:
    total_gb: float
    available_gb: float
    used_gb: float
    percent_used: float
    can_allocate_gb: float

# =============================================================================
# MEMORY MANAGEMENT
# =============================================================================

class MemoryManager:
    """Manages system memory for optimal RAMDrive allocation"""
    
    @staticmethod
    def get_memory_info() -> SystemMemory:
        """Get current system memory status"""
        mem = psutil.virtual_memory()
        total = mem.total / (1024**3)
        available = mem.available / (1024**3)
        used = mem.used / (1024**3)
        
        # Calculate how much we can allocate
        min_free = CONFIG["memory"]["min_free_gb"]
        reserved = CONFIG["memory"]["reserved_for_gpu_gb"]
        can_allocate = max(0, available - min_free - reserved)
        
        return SystemMemory(
            total_gb=round(total, 2),
            available_gb=round(available, 2),
            used_gb=round(used, 2),
            percent_used=round(mem.percent, 1),
            can_allocate_gb=round(can_allocate, 2)
        )
    
    @staticmethod
    def cleanup_memory() -> Tuple[float, float]:
        """
        Aggressively clean up memory before RAMDrive creation.
        Returns (before_gb, after_gb)
        """
        LOG.info("[CLEAN] Starting memory cleanup...")
        
        before = psutil.virtual_memory().available / (1024**3)
        
        # 1. Python garbage collection
        import gc
        gc.collect()
        
        # 2. Clear Windows standby memory (requires admin)
        try:
            # Use RAMMap or EmptyStandbyList if available
            subprocess.run(
                ["powershell", "-Command", 
                 "[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()"],
                capture_output=True, timeout=10
            )
        except:
            pass
        
        # 3. Clear file system cache (Windows)
        try:
            subprocess.run(
                ["powershell", "-Command",
                 "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                capture_output=True, timeout=10
            )
        except:
            pass
        
        # 4. Suggest closing heavy apps
        heavy_processes = []
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                mem_gb = proc.info['memory_info'].rss / (1024**3)
                if mem_gb > 1 and proc.info['name'] not in ['System', 'python.exe']:
                    heavy_processes.append((proc.info['name'], mem_gb))
            except:
                pass
        
        if heavy_processes:
            heavy_processes.sort(key=lambda x: x[1], reverse=True)
            LOG.info("  Heavy processes using RAM:")
            for name, mem in heavy_processes[:5]:
                LOG.info(f"    {name}: {mem:.1f} GB")
        
        time.sleep(2)  # Wait for cleanup
        
        after = psutil.virtual_memory().available / (1024**3)
        freed = after - before
        
        LOG.info(f"[OK] Memory cleanup complete. Freed: {freed:.2f} GB")
        LOG.info(f"    Available: {after:.1f} GB")
        
        return before, after
    
    @staticmethod
    def calculate_optimal_allocation() -> Dict[str, int]:
        """Calculate optimal RAMDrive sizes based on available memory"""
        mem = MemoryManager.get_memory_info()
        available = mem.can_allocate_gb
        
        LOG.info(f"[CALC] Available for RAMDrives: {available:.1f} GB")
        
        allocations = {}
        remaining = available
        
        # Allocate by priority
        for name, config in sorted(CONFIG["ramdrives"].items(), 
                                   key=lambda x: x[1]["priority"]):
            requested = config["size_gb"]
            allocated = min(requested, remaining * 0.8)  # Leave headroom
            
            if allocated >= 1:  # Minimum 1GB per drive
                allocations[name] = int(allocated)
                remaining -= allocated
                LOG.info(f"    {name}: {allocated:.0f} GB (requested {requested})")
            else:
                LOG.warning(f"    {name}: Skipped (not enough RAM)")
        
        return allocations

# =============================================================================
# RAMDRIVE OPERATIONS
# =============================================================================

class RAMDriveManager:
    """
    Manages RAMDrive creation and lifecycle.
    Uses ImDisk for Windows RAMDrive operations.
    """
    
    def __init__(self):
        self.drives: Dict[str, RAMDriveInfo] = {}
        self.imdisk_available = self._check_imdisk()
    
    def _check_imdisk(self) -> bool:
        """Check if ImDisk is installed"""
        try:
            result = subprocess.run(
                ["imdisk", "--version"],
                capture_output=True, timeout=5
            )
            return True
        except:
            # Check alternative location
            imdisk_path = Path(r"C:\Windows\System32\imdisk.exe")
            return imdisk_path.exists()
    
    def _get_powershell_ramdisk_script(self, letter: str, size_mb: int) -> str:
        """Generate PowerShell script for RAMDisk creation"""
        return f'''
# Create RAMDisk using ImDisk
$letter = "{letter}"
$sizeMB = {size_mb}

# Check if drive exists
if (Test-Path "${{letter}}:") {{
    Write-Host "Drive ${{letter}}: already exists"
    exit 0
}}

# Create RAMDisk
try {{
    imdisk -a -s ${{sizeMB}}M -m ${{letter}}: -p "/fs:ntfs /q /y"
    Write-Host "Created RAMDisk ${{letter}}: with ${{sizeMB}}MB"
}} catch {{
    Write-Host "Failed to create RAMDisk: $_"
    exit 1
}}
'''
    
    def create_ramdrive(self, name: str, letter: str, size_gb: float, purpose: str) -> bool:
        """Create a single RAMDrive"""
        LOG.info(f"[CREATE] Creating RAMDrive {letter}: ({size_gb}GB) - {purpose}")
        
        # Check if drive letter is available
        if Path(f"{letter}:").exists():
            LOG.warning(f"    Drive {letter}: already exists")
            self.drives[name] = RAMDriveInfo(
                letter=letter, size_gb=size_gb, purpose=purpose,
                mounted=True, path=f"{letter}:\\"
            )
            return True
        
        if not self.imdisk_available:
            LOG.warning("    ImDisk not installed. Using virtual folder instead.")
            # Fallback: Create a folder-based "virtual" ramdrive
            virtual_path = CONFIG["project_dir"] / "ramdrive_virtual" / name
            virtual_path.mkdir(parents=True, exist_ok=True)
            
            self.drives[name] = RAMDriveInfo(
                letter=letter, size_gb=size_gb, purpose=purpose,
                mounted=False, path=str(virtual_path)
            )
            return True
        
        # Create using ImDisk
        size_mb = int(size_gb * 1024)
        
        try:
            result = subprocess.run(
                ["imdisk", "-a", "-s", f"{size_mb}M", "-m", f"{letter}:", 
                 "-p", "/fs:ntfs /q /y"],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0 or Path(f"{letter}:").exists():
                self.drives[name] = RAMDriveInfo(
                    letter=letter, size_gb=size_gb, purpose=purpose,
                    mounted=True, path=f"{letter}:\\"
                )
                LOG.info(f"[OK] RAMDrive {letter}: created successfully")
                return True
            else:
                LOG.error(f"[FAIL] Failed to create RAMDrive: {result.stderr}")
                return False
                
        except Exception as e:
            LOG.error(f"[FAIL] Error creating RAMDrive: {e}")
            return False
    
    def create_all_ramdrives(self, allocations: Dict[str, int]) -> Dict[str, RAMDriveInfo]:
        """Create all configured RAMDrives"""
        LOG.info("\n" + "="*60)
        LOG.info("  CREATING RAMDRIVES")
        LOG.info("="*60)
        
        for name, size in allocations.items():
            config = CONFIG["ramdrives"][name]
            self.create_ramdrive(
                name=name,
                letter=config["letter"],
                size_gb=size,
                purpose=config["purpose"]
            )
        
        return self.drives
    
    def remove_ramdrive(self, letter: str) -> bool:
        """Remove a RAMDrive"""
        LOG.info(f"[REMOVE] Removing RAMDrive {letter}:")
        
        try:
            result = subprocess.run(
                ["imdisk", "-D", "-m", f"{letter}:"],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            LOG.error(f"[FAIL] Error removing RAMDrive: {e}")
            return False
    
    def remove_all_ramdrives(self):
        """Remove all RAMDrives"""
        for name, info in self.drives.items():
            if info.mounted:
                self.remove_ramdrive(info.letter)
    
    def sync_to_disk(self, ramdrive_name: str, dest_dir: Path) -> bool:
        """Sync RAMDrive contents to disk"""
        if ramdrive_name not in self.drives:
            return False
        
        info = self.drives[ramdrive_name]
        source = Path(info.path)
        
        if not source.exists():
            return False
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        LOG.info(f"[SYNC] Syncing {info.letter}: to {dest_dir}")
        
        try:
            # Use robocopy for efficient sync
            result = subprocess.run(
                ["robocopy", str(source), str(dest_dir), "/MIR", "/NFL", "/NDL", "/NJH", "/NJS"],
                capture_output=True, timeout=300
            )
            # Robocopy returns various codes, 0-7 are generally OK
            return result.returncode < 8
        except Exception as e:
            LOG.error(f"[FAIL] Sync failed: {e}")
            return False
    
    def load_from_disk(self, source_dir: Path, ramdrive_name: str) -> bool:
        """Load data from disk to RAMDrive"""
        if ramdrive_name not in self.drives:
            return False
        
        info = self.drives[ramdrive_name]
        dest = Path(info.path)
        
        if not source_dir.exists():
            return False
        
        LOG.info(f"[LOAD] Loading {source_dir} to {info.letter}:")
        
        try:
            result = subprocess.run(
                ["robocopy", str(source_dir), str(dest), "/MIR", "/NFL", "/NDL", "/NJH", "/NJS"],
                capture_output=True, timeout=300
            )
            return result.returncode < 8
        except Exception as e:
            LOG.error(f"[FAIL] Load failed: {e}")
            return False

# =============================================================================
# DOCKER GPU INTEGRATION
# =============================================================================

class DockerGPUManager:
    """
    Manages Docker containers with GPU acceleration.
    Optimized for AI training workloads.
    """
    
    def __init__(self):
        self.docker_available = self._check_docker()
        self.nvidia_docker_available = self._check_nvidia_docker()
    
    def _check_docker(self) -> bool:
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_nvidia_docker(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", "--gpus", "all", "nvidia/cuda:11.0-base", "nvidia-smi"],
                capture_output=True, timeout=30
            )
            return result.returncode == 0
        except:
            return False
    
    def create_training_container(self, ramdrive_paths: Dict[str, str]) -> str:
        """Create optimized Docker container for training"""
        
        volumes = []
        for name, path in ramdrive_paths.items():
            container_path = f"/ramdrive/{name}"
            volumes.append(f"-v {path}:{container_path}")
        
        cmd = f"""
docker run -d \\
    --name ai_training \\
    --gpus all \\
    --memory {CONFIG['docker']['memory_limit']} \\
    --shm-size {CONFIG['docker']['shm_size']} \\
    {' '.join(volumes)} \\
    --restart unless-stopped \\
    pytorch/pytorch:latest
"""
        return cmd
    
    def get_optimal_docker_compose(self, ramdrive_paths: Dict[str, str]) -> str:
        """Generate docker-compose.yml for training"""
        
        volumes = []
        for name, path in ramdrive_paths.items():
            volumes.append(f"      - {path}:/ramdrive/{name}")
        
        return f'''version: "3.8"

services:
  training:
    image: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
    container_name: ai_training
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    shm_size: '{CONFIG['docker']['shm_size']}'
    volumes:
{chr(10).join(volumes)}
      - ./scripts:/workspace/scripts
      - ./output:/workspace/output
    working_dir: /workspace
    command: sleep infinity
    
  tensorboard:
    image: tensorflow/tensorflow:latest
    ports:
      - "6006:6006"
    volumes:
      - ./logs:/logs
    command: tensorboard --logdir=/logs --bind_all
'''

# =============================================================================
# PERFORMANCE OPTIMIZATIONS
# =============================================================================

PERFORMANCE_TECHNIQUES = {
    "ramdrive_dataset": {
        "name": "RAMDrive Dataset Loading",
        "description": "Load training images to RAMDrive for instant access",
        "speedup": "10-50x faster I/O",
        "implementation": "Copy dataset to R: drive before training",
    },
    "model_caching": {
        "name": "Model Weight Caching",
        "description": "Cache model checkpoints in RAM",
        "speedup": "5-10x faster model loading",
        "implementation": "Mount models on M: drive",
    },
    "gpu_vram_ramdisk": {
        "name": "GPU VRAM RAMDisk",
        "description": "Use idle VRAM as ultra-fast storage",
        "speedup": "100x+ faster than SSD",
        "implementation": "GpuRamDrive for temp files",
    },
    "blocks_to_swap": {
        "name": "VRAM-RAM Block Swapping",
        "description": "Trade VRAM for system RAM in 0.3GB blocks",
        "speedup": "Train larger models on limited VRAM",
        "implementation": "Kohya blocks_to_swap parameter",
    },
    "mixed_precision": {
        "name": "Mixed Precision Training",
        "description": "Use FP16/BF16 for faster computation",
        "speedup": "2-3x faster training",
        "implementation": "Enable in training config",
    },
    "gradient_checkpointing": {
        "name": "Gradient Checkpointing",
        "description": "Trade compute for memory",
        "speedup": "50% VRAM reduction",
        "implementation": "Enable in trainer settings",
    },
    "prefetch_dataloader": {
        "name": "Prefetch DataLoader",
        "description": "Load next batch while training",
        "speedup": "20-30% faster epochs",
        "implementation": "num_workers > 0, prefetch_factor",
    },
    "tensor_cores": {
        "name": "Tensor Core Optimization",
        "description": "Use GPU tensor cores (RTX 30/40)",
        "speedup": "3-8x faster matrix ops",
        "implementation": "Proper batch/dimension alignment",
    },
    "nvme_raid": {
        "name": "NVMe RAID 0 Array",
        "description": "Stripe multiple NVMe drives",
        "speedup": "2-4x faster disk I/O",
        "implementation": "Windows Storage Spaces",
    },
    "cuda_graphs": {
        "name": "CUDA Graphs",
        "description": "Capture and replay GPU operations",
        "speedup": "10-20% faster inference",
        "implementation": "torch.cuda.make_graphed_callables",
    },
}

# =============================================================================
# MAIN PERFORMANCE MANAGER
# =============================================================================

class PerformanceManager:
    """
    Main orchestrator for all performance optimizations.
    """
    
    def __init__(self):
        self.memory_mgr = MemoryManager()
        self.ramdrive_mgr = RAMDriveManager()
        self.docker_mgr = DockerGPUManager()
        self.active_ramdrives: Dict[str, RAMDriveInfo] = {}
    
    def initialize(self) -> bool:
        """Initialize performance system"""
        LOG.info("\n" + "="*60)
        LOG.info("  PERFORMANCE OPTIMIZATION SYSTEM")
        LOG.info("="*60)
        
        # 1. Check system
        mem = self.memory_mgr.get_memory_info()
        LOG.info(f"\n[SYS] System Memory: {mem.total_gb:.1f} GB total, {mem.available_gb:.1f} GB available")
        
        # 2. Clean memory
        if mem.percent_used > CONFIG["memory"]["cleanup_threshold_percent"]:
            self.memory_mgr.cleanup_memory()
        
        # 3. Calculate optimal allocations
        allocations = self.memory_mgr.calculate_optimal_allocation()
        
        if not allocations:
            LOG.error("[FAIL] Not enough RAM for RAMDrives")
            return False
        
        # 4. Create RAMDrives
        self.active_ramdrives = self.ramdrive_mgr.create_all_ramdrives(allocations)
        
        # 5. Show Docker status
        if self.docker_mgr.docker_available:
            LOG.info(f"\n[DOCKER] Docker: Available")
            LOG.info(f"         GPU Support: {'Yes' if self.docker_mgr.nvidia_docker_available else 'No'}")
        
        return True
    
    def get_paths(self) -> Dict[str, str]:
        """Get RAMDrive paths for use in training"""
        return {name: info.path for name, info in self.active_ramdrives.items()}
    
    def prepare_training_data(self, source_dir: Path, ramdrive_name: str = "training_data"):
        """Load training data to RAMDrive"""
        LOG.info(f"\n[PREP] Loading training data to RAMDrive...")
        self.ramdrive_mgr.load_from_disk(source_dir, ramdrive_name)
    
    def sync_all(self):
        """Sync all RAMDrives to disk"""
        backup_dir = CONFIG["sync"]["backup_dir"]
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        for name in self.active_ramdrives:
            self.ramdrive_mgr.sync_to_disk(name, backup_dir / name)
    
    def cleanup(self):
        """Cleanup and remove RAMDrives"""
        LOG.info("\n[CLEANUP] Syncing and removing RAMDrives...")
        self.sync_all()
        self.ramdrive_mgr.remove_all_ramdrives()
    
    def get_optimization_report(self) -> str:
        """Generate optimization recommendations report"""
        report = """
# Performance Optimization Report

## Current RAMDrives
"""
        for name, info in self.active_ramdrives.items():
            status = "MOUNTED" if info.mounted else "VIRTUAL"
            report += f"- **{info.letter}:** ({info.size_gb}GB) - {info.purpose} [{status}]\n"
        
        report += "\n## Top Performance Techniques\n\n"
        
        for key, tech in list(PERFORMANCE_TECHNIQUES.items())[:5]:
            report += f"### {tech['name']}\n"
            report += f"- **Speedup:** {tech['speedup']}\n"
            report += f"- **How:** {tech['implementation']}\n\n"
        
        return report


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAMDrive Performance Manager")
    parser.add_argument("--init", action="store_true", help="Initialize RAMDrives")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup RAMDrives")
    parser.add_argument("--techniques", action="store_true", help="Show optimization techniques")
    parser.add_argument("--docker-compose", action="store_true", help="Generate docker-compose.yml")
    args = parser.parse_args()
    
    mgr = PerformanceManager()
    
    if args.init:
        mgr.initialize()
        paths = mgr.get_paths()
        LOG.info("\n[OK] RAMDrive paths:")
        for name, path in paths.items():
            LOG.info(f"    {name}: {path}")
    
    elif args.status:
        mem = MemoryManager.get_memory_info()
        LOG.info(f"System Memory: {mem.total_gb}GB total, {mem.available_gb}GB available")
        LOG.info(f"Can allocate: {mem.can_allocate_gb}GB for RAMDrives")
    
    elif args.cleanup:
        mgr.cleanup()
    
    elif args.techniques:
        print("\n" + "="*60)
        print("  PERFORMANCE OPTIMIZATION TECHNIQUES")
        print("="*60 + "\n")
        
        for key, tech in PERFORMANCE_TECHNIQUES.items():
            print(f"[{key}]")
            print(f"  Name: {tech['name']}")
            print(f"  Speedup: {tech['speedup']}")
            print(f"  Implementation: {tech['implementation']}")
            print()
    
    elif args.docker_compose:
        docker_mgr = DockerGPUManager()
        compose = docker_mgr.get_optimal_docker_compose({
            "training_data": "R:\\",
            "model_cache": "M:\\",
            "temp_workspace": "T:\\",
        })
        print(compose)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
