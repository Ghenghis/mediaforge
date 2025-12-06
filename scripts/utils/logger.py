"""
LoRAForge Logger Utility
Structured logging with file and console output
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# ANSI Colors for console
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def setup_logger(
    name: str,
    log_dir: Optional[Path] = None,
    level: str = "INFO"
) -> logging.Logger:
    """
    Setup structured logger with file and console output
    
    Args:
        name: Logger name
        log_dir: Directory for log files (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Format
    fmt = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)
    
    # File handler (if log_dir provided)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name}_{datetime.now():%Y%m%d_%H%M%S}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
        logger.info(f"Logging to: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get existing logger by name"""
    return logging.getLogger(name)


# Console output helpers
def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}  {title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")


def print_success(msg: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.ENDC}")


def print_error(msg: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")


def print_warning(msg: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")


def print_info(msg: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {msg}{Colors.ENDC}")


def print_progress(current: int, total: int, prefix: str = ""):
    """Print progress bar"""
    percent = current / total * 100
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"\r{prefix} [{bar}] {percent:.1f}% ({current}/{total})", end='', flush=True)
    if current >= total:
        print()  # New line when complete


class StageTimer:
    """Context manager for timing pipeline stages"""
    
    def __init__(self, stage_name: str, logger: logging.Logger = None):
        self.stage_name = stage_name
        self.logger = logger
        self.start_time = None
        self.elapsed = 0
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        print_section(f"Stage: {self.stage_name}")
        if self.logger:
            self.logger.info(f"Starting stage: {self.stage_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.elapsed = time.time() - self.start_time
        
        if exc_type is None:
            print_success(f"{self.stage_name} completed in {self.elapsed:.2f}s")
            if self.logger:
                self.logger.info(f"Completed {self.stage_name} in {self.elapsed:.2f}s")
        else:
            print_error(f"{self.stage_name} failed after {self.elapsed:.2f}s: {exc_val}")
            if self.logger:
                self.logger.error(f"Failed {self.stage_name}: {exc_val}")
        
        return False  # Don't suppress exceptions
