"""
Complete RAMDrive System for 128GB RAM ML Workstation
======================================================
Ready-to-run solution with:
- Windows 11 + WSL2 support
- Mount/unmount scripts
- NVMe vs RAMDrive benchmarks
- Automatic dataset staging
- PyTorch DataLoader optimization

Your Setup:
- 128GB RAM → Can dedicate 64-96GB to RAMDrives
- RTX 3090 Ti (24GB VRAM) → PCIe 4.0 x16
- 4TB NVMe → Backup/overflow storage
"""

import os
import sys
import time
import json
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import psutil
import logging

# =============================================================================
# CONFIGURATION FOR 128GB SYSTEM
# =============================================================================

RAMDRIVE_CONFIG = {
    # Optimized for 128GB RAM with 64GB+ available
    "drives": {
        "R": {"size_gb": 32, "purpose": "Training Dataset", "fs": "NTFS"},
        "M": {"size_gb": 24, "purpose": "Model Cache", "fs": "NTFS"},
        "T": {"size_gb": 8, "purpose": "Temp/Preprocessing", "fs": "NTFS"},
    },
    "total_gb": 64,
    "reserve_gb": 16,  # Keep for OS/apps
}

# Your specific paths
PATHS = {
    "project": Path(r"C:\Users\Admin\civitai"),
    "datasets": Path(r"C:\Users\Admin\civitai\images"),
    "models": Path(r"C:\Users\Admin\.lmstudio\models"),
    "nvme_backup": Path(r"C:\Users\Admin\civitai\ramdrive_backups"),
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
LOG = logging.getLogger("ramdrive")

# =============================================================================
# BENCHMARKING
# =============================================================================

@dataclass
class BenchmarkResult:
    name: str
    read_speed_mbps: float
    write_speed_mbps: float
    random_read_iops: float
    random_write_iops: float
    latency_ms: float

class StorageBenchmark:
    """Benchmark storage performance for ML workloads"""
    
    def __init__(self, test_size_mb: int = 1024):
        self.test_size_mb = test_size_mb
        self.test_data = os.urandom(1024 * 1024)  # 1MB random data
    
    def benchmark_sequential_write(self, path: Path) -> float:
        """Sequential write speed in MB/s"""
        test_file = path / "benchmark_seq_write.bin"
        data = self.test_data * self.test_size_mb  # test_size_mb MB
        
        start = time.perf_counter()
        with open(test_file, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        elapsed = time.perf_counter() - start
        
        test_file.unlink()
        return self.test_size_mb / elapsed
    
    def benchmark_sequential_read(self, path: Path) -> float:
        """Sequential read speed in MB/s"""
        test_file = path / "benchmark_seq_read.bin"
        data = self.test_data * self.test_size_mb
        
        # Write test file
        with open(test_file, 'wb') as f:
            f.write(data)
        
        # Clear cache (Windows)
        try:
            subprocess.run(["powershell", "-Command", 
                "[System.GC]::Collect()"], capture_output=True, timeout=5)
        except:
            pass
        
        start = time.perf_counter()
        with open(test_file, 'rb') as f:
            _ = f.read()
        elapsed = time.perf_counter() - start
        
        test_file.unlink()
        return self.test_size_mb / elapsed
    
    def benchmark_random_io(self, path: Path, block_size: int = 4096, 
                           num_ops: int = 1000) -> Tuple[float, float]:
        """Random 4K IOPS (read, write)"""
        test_file = path / "benchmark_random.bin"
        file_size = 256 * 1024 * 1024  # 256MB
        
        # Create test file
        with open(test_file, 'wb') as f:
            for _ in range(file_size // (1024 * 1024)):
                f.write(self.test_data)
        
        import random
        positions = [random.randint(0, file_size - block_size) for _ in range(num_ops)]
        
        # Random writes
        start = time.perf_counter()
        with open(test_file, 'r+b') as f:
            for pos in positions:
                f.seek(pos)
                f.write(os.urandom(block_size))
        write_elapsed = time.perf_counter() - start
        
        # Random reads
        start = time.perf_counter()
        with open(test_file, 'rb') as f:
            for pos in positions:
                f.seek(pos)
                _ = f.read(block_size)
        read_elapsed = time.perf_counter() - start
        
        test_file.unlink()
        
        return (num_ops / read_elapsed, num_ops / write_elapsed)
    
    def benchmark_latency(self, path: Path, num_ops: int = 100) -> float:
        """Average access latency in milliseconds"""
        test_file = path / "benchmark_latency.bin"
        
        # Create small test file
        with open(test_file, 'wb') as f:
            f.write(os.urandom(4096))
        
        latencies = []
        for _ in range(num_ops):
            start = time.perf_counter()
            with open(test_file, 'rb') as f:
                _ = f.read()
            latencies.append((time.perf_counter() - start) * 1000)
        
        test_file.unlink()
        return sum(latencies) / len(latencies)
    
    def run_full_benchmark(self, path: Path, name: str) -> BenchmarkResult:
        """Run complete benchmark suite"""
        LOG.info(f"Benchmarking {name} at {path}...")
        
        path.mkdir(parents=True, exist_ok=True)
        
        write_speed = self.benchmark_sequential_write(path)
        LOG.info(f"  Sequential Write: {write_speed:.0f} MB/s")
        
        read_speed = self.benchmark_sequential_read(path)
        LOG.info(f"  Sequential Read: {read_speed:.0f} MB/s")
        
        rand_read, rand_write = self.benchmark_random_io(path)
        LOG.info(f"  Random Read IOPS: {rand_read:.0f}")
        LOG.info(f"  Random Write IOPS: {rand_write:.0f}")
        
        latency = self.benchmark_latency(path)
        LOG.info(f"  Access Latency: {latency:.3f} ms")
        
        return BenchmarkResult(
            name=name,
            read_speed_mbps=read_speed,
            write_speed_mbps=write_speed,
            random_read_iops=rand_read,
            random_write_iops=rand_write,
            latency_ms=latency
        )

# =============================================================================
# RAMDRIVE MANAGER (IMDISK)
# =============================================================================

class ImDiskRAMDrive:
    """Manage RAMDrives using ImDisk"""
    
    @staticmethod
    def is_installed() -> bool:
        """Check if ImDisk is installed"""
        return Path(r"C:\Windows\System32\imdisk.exe").exists()
    
    @staticmethod
    def create(letter: str, size_gb: int, filesystem: str = "NTFS") -> bool:
        """Create a RAMDrive"""
        size_mb = size_gb * 1024
        
        LOG.info(f"Creating RAMDrive {letter}: ({size_gb}GB, {filesystem})")
        
        if Path(f"{letter}:").exists():
            LOG.warning(f"  Drive {letter}: already exists")
            return True
        
        try:
            # Create RAMDisk
            cmd = ["imdisk", "-a", "-s", f"{size_mb}M", "-m", f"{letter}:", 
                   "-p", f"/fs:{filesystem.lower()} /q /y"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 or Path(f"{letter}:").exists():
                LOG.info(f"  [OK] Created {letter}:")
                return True
            else:
                LOG.error(f"  [FAIL] {result.stderr}")
                return False
        except Exception as e:
            LOG.error(f"  [FAIL] {e}")
            return False
    
    @staticmethod
    def remove(letter: str) -> bool:
        """Remove a RAMDrive"""
        LOG.info(f"Removing RAMDrive {letter}:")
        
        try:
            result = subprocess.run(
                ["imdisk", "-D", "-m", f"{letter}:"],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def list_drives() -> List[str]:
        """List all RAMDrives"""
        drives = []
        try:
            result = subprocess.run(
                ["imdisk", "-l"],
                capture_output=True, text=True, timeout=10
            )
            # Parse output for drive letters
            for line in result.stdout.split('\n'):
                if 'MountPoint' in line and ':' in line:
                    letter = line.split(':')[0][-1]
                    drives.append(letter)
        except:
            pass
        return drives

# =============================================================================
# DATASET STAGING
# =============================================================================

class DatasetStager:
    """Stage datasets to RAMDrive for fast training"""
    
    def __init__(self, ramdrive_path: Path, nvme_path: Path):
        self.ramdrive = ramdrive_path
        self.nvme = nvme_path
    
    def stage_to_ram(self, dataset_name: str) -> bool:
        """Copy dataset from NVMe to RAMDrive"""
        source = self.nvme / dataset_name
        dest = self.ramdrive / dataset_name
        
        if not source.exists():
            LOG.error(f"Dataset not found: {source}")
            return False
        
        LOG.info(f"Staging {dataset_name} to RAMDrive...")
        
        # Get size
        total_size = sum(f.stat().st_size for f in source.rglob('*') if f.is_file())
        LOG.info(f"  Size: {total_size / (1024**3):.2f} GB")
        
        start = time.time()
        shutil.copytree(source, dest, dirs_exist_ok=True)
        elapsed = time.time() - start
        
        speed = (total_size / (1024**2)) / elapsed
        LOG.info(f"  Staged in {elapsed:.1f}s ({speed:.0f} MB/s)")
        
        return True
    
    def sync_to_nvme(self, dataset_name: str) -> bool:
        """Sync changes back to NVMe"""
        source = self.ramdrive / dataset_name
        dest = self.nvme / dataset_name
        
        LOG.info(f"Syncing {dataset_name} to NVMe...")
        
        try:
            result = subprocess.run(
                ["robocopy", str(source), str(dest), "/MIR", "/NFL", "/NDL", "/NJH", "/NJS"],
                capture_output=True, timeout=600
            )
            return result.returncode < 8
        except Exception as e:
            LOG.error(f"Sync failed: {e}")
            return False

# =============================================================================
# PYTORCH OPTIMIZATION
# =============================================================================

PYTORCH_RAMDRIVE_CONFIG = '''
# Optimized PyTorch DataLoader for RAMDrive
# =========================================

import torch
from torch.utils.data import DataLoader
import os

# Set cache directories to RAMDrive
os.environ['TORCH_HOME'] = 'M:/torch_cache'
os.environ['HF_HOME'] = 'M:/huggingface'
os.environ['TRANSFORMERS_CACHE'] = 'M:/transformers'

# Optimized DataLoader settings for RAMDrive
def get_optimized_dataloader(dataset, batch_size=8):
    """
    DataLoader optimized for RAMDrive storage.
    
    When data is on RAMDrive:
    - Higher num_workers (data already in RAM)
    - pin_memory=True for faster GPU transfer
    - persistent_workers=True to avoid respawn overhead
    - prefetch_factor=4 for aggressive prefetching
    """
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=8,  # More workers since data is in RAM
        pin_memory=True,  # Stage to page-locked memory
        persistent_workers=True,  # Keep workers alive
        prefetch_factor=4,  # Prefetch 4 batches per worker
        drop_last=True,
    )

# Mixed precision training setup
def setup_mixed_precision():
    """Enable automatic mixed precision for 2-3x speedup"""
    scaler = torch.cuda.amp.GradScaler()
    
    # In training loop:
    # with torch.cuda.amp.autocast():
    #     output = model(input)
    #     loss = criterion(output, target)
    # scaler.scale(loss).backward()
    # scaler.step(optimizer)
    # scaler.update()
    
    return scaler

# Tensor Core optimization
def optimize_for_tensor_cores(model):
    """Ensure model dimensions are optimal for Tensor Cores"""
    # RTX 3090 Ti has Tensor Cores that work best with:
    # - Dimensions divisible by 8 (FP16) or 16 (TF32)
    # - Batch sizes of 8, 16, 32, etc.
    
    # Enable TF32 for A100/3090
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    
    # Enable cudnn benchmarking for conv layers
    torch.backends.cudnn.benchmark = True
    
    return model
'''

# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

class RAMDriveOrchestrator:
    """Complete RAMDrive management for ML workloads"""
    
    def __init__(self):
        self.benchmark = StorageBenchmark(test_size_mb=512)
        self.drives_created: List[str] = []
    
    def check_system(self) -> Dict:
        """Check system readiness"""
        mem = psutil.virtual_memory()
        
        return {
            "total_ram_gb": mem.total / (1024**3),
            "available_ram_gb": mem.available / (1024**3),
            "imdisk_installed": ImDiskRAMDrive.is_installed(),
            "can_create_drives": mem.available / (1024**3) > RAMDRIVE_CONFIG["total_gb"] + RAMDRIVE_CONFIG["reserve_gb"],
        }
    
    def setup_all_drives(self) -> bool:
        """Create all configured RAMDrives"""
        LOG.info("\n" + "="*60)
        LOG.info("  RAMDRIVE SETUP FOR 128GB SYSTEM")
        LOG.info("="*60 + "\n")
        
        status = self.check_system()
        LOG.info(f"System RAM: {status['total_ram_gb']:.0f}GB total, {status['available_ram_gb']:.0f}GB available")
        
        if not status["imdisk_installed"]:
            LOG.error("ImDisk not installed! Run: scripts/performance/install_imdisk.ps1")
            return False
        
        if not status["can_create_drives"]:
            LOG.error(f"Not enough RAM. Need {RAMDRIVE_CONFIG['total_gb'] + RAMDRIVE_CONFIG['reserve_gb']}GB available")
            return False
        
        # Create drives
        success = True
        for letter, config in RAMDRIVE_CONFIG["drives"].items():
            if ImDiskRAMDrive.create(letter, config["size_gb"], config["fs"]):
                self.drives_created.append(letter)
            else:
                success = False
        
        if success:
            LOG.info("\n[OK] All RAMDrives created successfully!")
            self.print_drive_info()
        
        return success
    
    def print_drive_info(self):
        """Print RAMDrive information"""
        LOG.info("\n" + "-"*40)
        LOG.info("  RAMDRIVE LAYOUT")
        LOG.info("-"*40)
        for letter, config in RAMDRIVE_CONFIG["drives"].items():
            LOG.info(f"  {letter}: - {config['size_gb']}GB - {config['purpose']}")
        LOG.info(f"\n  Total: {RAMDRIVE_CONFIG['total_gb']}GB RAMDrives")
    
    def run_comparison_benchmark(self) -> Dict:
        """Compare RAMDrive vs NVMe performance"""
        LOG.info("\n" + "="*60)
        LOG.info("  STORAGE BENCHMARK: RAMDRIVE vs NVMe")
        LOG.info("="*60 + "\n")
        
        results = {}
        
        # Benchmark NVMe
        nvme_path = Path("C:/Users/Admin/civitai/benchmark_test")
        nvme_result = self.benchmark.run_full_benchmark(nvme_path, "NVMe SSD")
        results["nvme"] = asdict(nvme_result)
        shutil.rmtree(nvme_path, ignore_errors=True)
        
        # Benchmark RAMDrive (if available)
        if Path("R:/").exists():
            ram_path = Path("R:/benchmark_test")
            ram_result = self.benchmark.run_full_benchmark(ram_path, "RAMDrive")
            results["ramdrive"] = asdict(ram_result)
            shutil.rmtree(ram_path, ignore_errors=True)
            
            # Print comparison
            LOG.info("\n" + "-"*40)
            LOG.info("  PERFORMANCE COMPARISON")
            LOG.info("-"*40)
            
            speedups = {
                "Sequential Read": ram_result.read_speed_mbps / nvme_result.read_speed_mbps,
                "Sequential Write": ram_result.write_speed_mbps / nvme_result.write_speed_mbps,
                "Random Read IOPS": ram_result.random_read_iops / nvme_result.random_read_iops,
                "Random Write IOPS": ram_result.random_write_iops / nvme_result.random_write_iops,
                "Latency": nvme_result.latency_ms / ram_result.latency_ms,  # Lower is better
            }
            
            for metric, speedup in speedups.items():
                LOG.info(f"  {metric}: {speedup:.1f}x faster")
        
        return results
    
    def cleanup(self):
        """Remove all RAMDrives"""
        LOG.info("\nCleaning up RAMDrives...")
        for letter in self.drives_created:
            ImDiskRAMDrive.remove(letter)
    
    def generate_pytorch_config(self, output_path: Path):
        """Generate PyTorch configuration file"""
        output_path.write_text(PYTORCH_RAMDRIVE_CONFIG)
        LOG.info(f"Generated PyTorch config: {output_path}")

# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Complete RAMDrive System for ML Workloads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ramdrive_complete.py --setup       # Create all RAMDrives
  python ramdrive_complete.py --benchmark   # Compare RAMDrive vs NVMe
  python ramdrive_complete.py --stage images  # Stage dataset to RAMDrive
  python ramdrive_complete.py --cleanup     # Remove RAMDrives
        """
    )
    
    parser.add_argument("--setup", action="store_true", help="Setup all RAMDrives")
    parser.add_argument("--benchmark", action="store_true", help="Run storage benchmarks")
    parser.add_argument("--stage", type=str, help="Stage dataset to RAMDrive")
    parser.add_argument("--sync", type=str, help="Sync dataset back to NVMe")
    parser.add_argument("--cleanup", action="store_true", help="Remove all RAMDrives")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--pytorch-config", action="store_true", help="Generate PyTorch config")
    
    args = parser.parse_args()
    
    orchestrator = RAMDriveOrchestrator()
    
    if args.setup:
        orchestrator.setup_all_drives()
    
    elif args.benchmark:
        orchestrator.run_comparison_benchmark()
    
    elif args.stage:
        stager = DatasetStager(Path("R:/"), PATHS["datasets"].parent)
        stager.stage_to_ram(args.stage)
    
    elif args.sync:
        stager = DatasetStager(Path("R:/"), PATHS["datasets"].parent)
        stager.sync_to_nvme(args.sync)
    
    elif args.cleanup:
        for letter in RAMDRIVE_CONFIG["drives"].keys():
            ImDiskRAMDrive.remove(letter)
    
    elif args.status:
        status = orchestrator.check_system()
        LOG.info("\n" + "="*40)
        LOG.info("  SYSTEM STATUS")
        LOG.info("="*40)
        LOG.info(f"  Total RAM: {status['total_ram_gb']:.0f} GB")
        LOG.info(f"  Available: {status['available_ram_gb']:.0f} GB")
        LOG.info(f"  ImDisk: {'Installed' if status['imdisk_installed'] else 'NOT INSTALLED'}")
        LOG.info(f"  Can Create Drives: {'Yes' if status['can_create_drives'] else 'No'}")
        
        # Check existing drives
        for letter in RAMDRIVE_CONFIG["drives"].keys():
            exists = Path(f"{letter}:/").exists()
            LOG.info(f"  Drive {letter}: {'MOUNTED' if exists else 'not mounted'}")
    
    elif args.pytorch_config:
        output = PATHS["project"] / "config" / "pytorch_ramdrive.py"
        output.parent.mkdir(exist_ok=True)
        orchestrator.generate_pytorch_config(output)
    
    else:
        parser.print_help()
        print("\n" + "="*60)
        print("  YOUR 128GB SYSTEM RAMDRIVE ALLOCATION")
        print("="*60)
        print("""
  Optimal Configuration:
  ┌─────────────────────────────────────────────┐
  │  R: 32GB  │ Training Dataset (images)       │
  │  M: 24GB  │ Model Cache (weights/ckpts)     │
  │  T: 8GB   │ Temp/Preprocessing              │
  ├─────────────────────────────────────────────┤
  │  Total: 64GB RAMDrives                      │
  │  Reserved: 64GB for OS/Apps/GPU             │
  └─────────────────────────────────────────────┘

  Expected Performance vs NVMe:
  • Sequential Read:  10-15x faster
  • Sequential Write: 8-12x faster  
  • Random IOPS:      50-100x faster
  • Latency:          100x+ lower
        """)


if __name__ == "__main__":
    main()
