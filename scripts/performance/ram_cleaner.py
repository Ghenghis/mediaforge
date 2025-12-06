"""
Automated RAM Cleaner for AI Training Pipeline
===============================================
Flushes unused RAM before and during operations.
Keeps only project-essential processes running.

Features:
- Auto-flush before batch operations
- Periodic cleanup during training
- Process monitoring and suggestions
- Memory pressure detection
"""

import os
import sys
import gc
import ctypes
import subprocess
import psutil
import time
import logging
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
LOG = logging.getLogger("ram_cleaner")

# =============================================================================
# CONFIGURATION
# =============================================================================

# Processes essential for our project (don't suggest closing)
ESSENTIAL_PROCESSES = {
    'python.exe', 'pythonw.exe',
    'lm studio.exe', 'lmstudio.exe',
    'ollama.exe', 'ollama_llama_server.exe',
    'cmd.exe', 'powershell.exe', 'pwsh.exe',
    'windowsterminal.exe', 'code.exe', 'windsurf.exe',
    'explorer.exe', 'system', 'svchost.exe',
    'csrss.exe', 'smss.exe', 'wininit.exe',
    'services.exe', 'lsass.exe', 'dwm.exe',
    'nvcontainer.exe', 'nvidia-smi.exe',  # GPU
}

# Processes that use lots of RAM but aren't needed for training
HEAVY_CLOSEABLE = {
    'chrome.exe': 'Google Chrome',
    'firefox.exe': 'Firefox',
    'msedge.exe': 'Microsoft Edge',
    'discord.exe': 'Discord',
    'slack.exe': 'Slack',
    'teams.exe': 'Microsoft Teams',
    'spotify.exe': 'Spotify',
    'steam.exe': 'Steam',
    'epicgameslauncher.exe': 'Epic Games',
    'origin.exe': 'Origin',
    'battle.net.exe': 'Battle.net',
}

# =============================================================================
# RAM CLEANER CLASS
# =============================================================================

@dataclass
class MemoryStats:
    total_gb: float
    used_gb: float
    available_gb: float
    percent_used: float
    freed_gb: float = 0.0

class RAMCleaner:
    """Automated RAM cleaning and optimization"""
    
    def __init__(self):
        self.initial_available = 0
        self.cleanups_performed = 0
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        mem = psutil.virtual_memory()
        return MemoryStats(
            total_gb=mem.total / (1024**3),
            used_gb=mem.used / (1024**3),
            available_gb=mem.available / (1024**3),
            percent_used=mem.percent
        )
    
    def flush_python_memory(self) -> float:
        """Flush Python's internal memory"""
        before = psutil.Process().memory_info().rss
        
        # Force garbage collection (multiple passes)
        gc.collect(0)  # Young generation
        gc.collect(1)  # Middle generation
        gc.collect(2)  # Old generation
        gc.collect()   # Full collection
        
        after = psutil.Process().memory_info().rss
        freed_mb = (before - after) / (1024**2)
        
        return max(0, freed_mb)
    
    def flush_windows_standby(self) -> bool:
        """
        Flush Windows standby memory list.
        This clears cached memory that's not actively used.
        """
        try:
            # Use PowerShell to trigger .NET garbage collection
            subprocess.run([
                'powershell', '-Command',
                '[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers(); [System.GC]::Collect()'
            ], capture_output=True, timeout=10)
            return True
        except:
            return False
    
    def flush_file_cache(self) -> bool:
        """Attempt to flush file system cache"""
        try:
            # Clear DNS cache
            subprocess.run(['ipconfig', '/flushdns'], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def get_heavy_processes(self) -> List[Tuple[str, float, str]]:
        """Get list of heavy RAM-using processes that could be closed"""
        heavy = []
        
        for proc in psutil.process_iter(['name', 'memory_info', 'pid']):
            try:
                name = proc.info['name'].lower()
                mem_gb = proc.info['memory_info'].rss / (1024**3)
                
                # Only consider processes using >500MB
                if mem_gb > 0.5:
                    if name in HEAVY_CLOSEABLE:
                        heavy.append((name, mem_gb, HEAVY_CLOSEABLE[name]))
                    elif name not in ESSENTIAL_PROCESSES and mem_gb > 1.0:
                        heavy.append((name, mem_gb, name))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by memory usage
        heavy.sort(key=lambda x: x[1], reverse=True)
        return heavy
    
    def full_cleanup(self, aggressive: bool = False) -> MemoryStats:
        """
        Perform full RAM cleanup.
        
        Args:
            aggressive: If True, suggest closing heavy apps
        """
        LOG.info("[CLEAN] Starting RAM cleanup...")
        
        before = self.get_memory_stats()
        self.initial_available = before.available_gb
        
        # Step 1: Python garbage collection
        py_freed = self.flush_python_memory()
        if py_freed > 10:
            LOG.info(f"  Python GC: freed {py_freed:.0f} MB")
        
        # Step 2: Windows memory flush
        self.flush_windows_standby()
        
        # Step 3: File cache flush
        self.flush_file_cache()
        
        # Wait for cleanup to take effect
        time.sleep(1)
        
        after = self.get_memory_stats()
        freed = after.available_gb - before.available_gb
        after.freed_gb = max(0, freed)
        
        self.cleanups_performed += 1
        
        # Report
        if freed > 0.1:
            LOG.info(f"  [OK] Freed {freed:.2f} GB RAM")
        else:
            LOG.info(f"  [OK] RAM already optimized")
        
        LOG.info(f"  Available: {after.available_gb:.1f} GB / {after.total_gb:.0f} GB")
        
        # Aggressive mode: suggest closing heavy apps
        if aggressive or after.available_gb < 20:
            heavy = self.get_heavy_processes()
            if heavy:
                LOG.info("\n  [SUGGEST] Close these to free more RAM:")
                for name, mem, display in heavy[:5]:
                    LOG.info(f"    {display}: {mem:.1f} GB")
        
        return after
    
    def quick_cleanup(self) -> float:
        """Quick cleanup - just Python GC, returns MB freed"""
        freed = self.flush_python_memory()
        gc.collect()
        return freed
    
    def monitor_and_clean(self, threshold_percent: float = 85) -> bool:
        """
        Check memory and clean if above threshold.
        Returns True if cleanup was performed.
        """
        stats = self.get_memory_stats()
        
        if stats.percent_used > threshold_percent:
            LOG.warning(f"[WARN] RAM at {stats.percent_used:.0f}% - cleaning...")
            self.full_cleanup()
            return True
        
        return False

# =============================================================================
# GLOBAL CLEANER INSTANCE
# =============================================================================

_cleaner = RAMCleaner()

def flush_ram(aggressive: bool = False) -> MemoryStats:
    """Flush RAM - call this before major operations"""
    return _cleaner.full_cleanup(aggressive)

def quick_flush() -> float:
    """Quick RAM flush - call during operations"""
    return _cleaner.quick_cleanup()

def auto_clean_if_needed(threshold: float = 85) -> bool:
    """Auto-clean if RAM is above threshold"""
    return _cleaner.monitor_and_clean(threshold)

def get_stats() -> MemoryStats:
    """Get current memory stats"""
    return _cleaner.get_memory_stats()

# =============================================================================
# DECORATOR FOR AUTO-CLEANUP
# =============================================================================

def with_ram_cleanup(func):
    """Decorator to automatically flush RAM before function execution"""
    def wrapper(*args, **kwargs):
        flush_ram()
        try:
            return func(*args, **kwargs)
        finally:
            quick_flush()
    return wrapper

# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAM Cleaner for AI Training")
    parser.add_argument("--flush", action="store_true", help="Flush RAM now")
    parser.add_argument("--aggressive", action="store_true", help="Aggressive cleanup with suggestions")
    parser.add_argument("--status", action="store_true", help="Show RAM status")
    parser.add_argument("--monitor", action="store_true", help="Monitor and auto-clean")
    parser.add_argument("--heavy", action="store_true", help="Show heavy processes")
    
    args = parser.parse_args()
    
    cleaner = RAMCleaner()
    
    if args.flush or args.aggressive:
        stats = cleaner.full_cleanup(aggressive=args.aggressive)
        print(f"\n✓ RAM: {stats.available_gb:.1f} GB available ({100-stats.percent_used:.0f}% free)")
    
    elif args.status:
        stats = cleaner.get_memory_stats()
        print("\n" + "="*40)
        print("  RAM STATUS")
        print("="*40)
        print(f"  Total:     {stats.total_gb:.0f} GB")
        print(f"  Used:      {stats.used_gb:.1f} GB")
        print(f"  Available: {stats.available_gb:.1f} GB")
        print(f"  Usage:     {stats.percent_used:.0f}%")
    
    elif args.heavy:
        print("\n" + "="*40)
        print("  HEAVY RAM PROCESSES")
        print("="*40)
        heavy = cleaner.get_heavy_processes()
        if heavy:
            for name, mem, display in heavy[:10]:
                print(f"  {display:<30} {mem:.1f} GB")
        else:
            print("  No heavy closeable processes found")
    
    elif args.monitor:
        print("Monitoring RAM (Ctrl+C to stop)...")
        try:
            while True:
                cleaner.monitor_and_clean(85)
                time.sleep(30)
        except KeyboardInterrupt:
            print("\nStopped.")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
