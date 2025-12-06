"""
Model Repair Tool - Fix corrupt/incomplete LM Studio models
Handles:
1. Corrupt files (too small)
2. Vision models missing mmproj files
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Optional

LM_STUDIO_PATH = Path(r"C:\Users\Admin\.lmstudio\models")

# Known mmproj sources for vision models
MMPROJ_SOURCES = {
    # Model pattern -> (HuggingFace repo, mmproj filename)
    "Qwen3-VL-8B-Abliterated-Caption-it-i1": (
        "mradermacher/Qwen3-VL-8B-Abliterated-Caption-it-GGUF",
        "Qwen3-VL-8B-Abliterated-Caption-it.mmproj-f16.gguf"
    ),
    "Qwen2.5-VL-3B-Abliterated-Caption-it-i1": (
        "mradermacher/Qwen2.5-VL-3B-Abliterated-Caption-it-GGUF",
        "Qwen2.5-VL-3B-Abliterated-Caption-it.mmproj-f16.gguf"
    ),
    "Eris_PrimeV3.05-Vision-7B-i1": (
        "mradermacher/Eris_PrimeV3.05-Vision-7B-GGUF",
        "Eris_PrimeV3.05-Vision-7B.mmproj-f16.gguf"
    ),
    "Qwen3-VL-8B-NSFW-Caption": (
        "leonn07/qwen3-vl-8b-nsfw-caption-v4.5",
        "mmproj-model-f16.gguf"
    ),
    "RP_Vision_7B": (
        "GokouMoments/RP_Vision_7B-GGUF-IQ-Imatrix",
        "mmproj-model-f16.gguf"
    ),
}

# Expected minimum sizes for models (in MB)
MODEL_MIN_SIZES = {
    "0.5B": 300,
    "0.6B": 350,
    "1B": 500,
    "1.5B": 800,
    "2B": 1000,
    "3B": 1500,
    "4B": 2000,
    "7B": 3500,
    "8B": 4000,
    "9B": 4500,
    "12B": 6000,
    "14B": 7000,
}


def get_file_size_mb(path: Path) -> float:
    """Get file size in MB"""
    return path.stat().st_size / (1024 * 1024)


def check_gguf_header(path: Path) -> bool:
    """Check if file has valid GGUF header"""
    try:
        with open(path, 'rb') as f:
            magic = f.read(4)
            return magic == b'GGUF'
    except:
        return False


def estimate_model_size(name: str) -> Optional[int]:
    """Estimate expected minimum size based on model name"""
    for size_key, min_mb in MODEL_MIN_SIZES.items():
        if size_key in name:
            return min_mb
    return None


def scan_for_issues():
    """Scan models directory for corrupt/incomplete files"""
    print("\n" + "="*60)
    print("  SCANNING FOR MODEL ISSUES")
    print("="*60 + "\n")
    
    issues = {
        'corrupt': [],
        'missing_mmproj': [],
        'incomplete': []
    }
    
    # Get recent models (last 30 days)
    recent_cutoff = datetime.now().timestamp() - (30 * 24 * 60 * 60)
    
    for gguf in LM_STUDIO_PATH.rglob("*.gguf"):
        name = gguf.name
        size_mb = get_file_size_mb(gguf)
        mtime = gguf.stat().st_mtime
        
        # Skip mmproj files
        if 'mmproj' in name.lower():
            continue
        
        # Check for corrupt files (0 bytes or no valid header)
        if size_mb < 1:
            if not check_gguf_header(gguf):
                issues['corrupt'].append({
                    'path': gguf,
                    'size_mb': size_mb,
                    'reason': 'Empty or invalid file'
                })
                continue
        
        # Check for files too small for their model size
        expected_min = estimate_model_size(name)
        if expected_min and size_mb < expected_min * 0.5:  # Allow 50% margin
            issues['incomplete'].append({
                'path': gguf,
                'size_mb': size_mb,
                'expected_min': expected_min,
                'reason': f'File too small (expected >{expected_min}MB)'
            })
    
    # Check for vision models missing mmproj
    for model_dir in LM_STUDIO_PATH.iterdir():
        if not model_dir.is_dir():
            continue
        for subdir in model_dir.iterdir():
            if not subdir.is_dir():
                continue
            
            # Check if it's a vision model
            dir_name = subdir.name
            is_vision = any(x in dir_name.lower() for x in ['vl', 'vision', 'caption'])
            
            if is_vision:
                models = list(subdir.glob("*.gguf"))
                has_model = any(m for m in models if 'mmproj' not in m.name.lower() and m.stat().st_size > 1e9)
                has_mmproj = any(m for m in models if 'mmproj' in m.name.lower())
                
                if has_model and not has_mmproj:
                    # Find matching mmproj source
                    mmproj_source = None
                    for pattern, source in MMPROJ_SOURCES.items():
                        if pattern in dir_name:
                            mmproj_source = source
                            break
                    
                    issues['missing_mmproj'].append({
                        'dir': subdir,
                        'dir_name': dir_name,
                        'mmproj_source': mmproj_source
                    })
    
    return issues


def download_file(url: str, dest: Path, desc: str = ""):
    """Download a file with progress"""
    print(f"⬇️  Downloading: {desc or url}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            total = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(dest, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        mb = downloaded // (1024 * 1024)
                        print(f"\r   Progress: {pct}% ({mb} MB)", end='', flush=True)
            
            print(f"\r   ✅ Downloaded: {dest.name} ({downloaded // (1024*1024)} MB)")
            return True
    except Exception as e:
        print(f"\r   ❌ Failed: {e}")
        return False


def repair_models(issues: dict, dry_run: bool = True):
    """Repair found issues"""
    print("\n" + "="*60)
    print(f"  REPAIR PLAN {'(DRY RUN)' if dry_run else '(EXECUTING)'}")
    print("="*60 + "\n")
    
    # Handle corrupt files
    if issues['corrupt']:
        print("🗑️  CORRUPT FILES TO DELETE:")
        for item in issues['corrupt']:
            print(f"   - {item['path'].name} ({item['size_mb']:.1f} MB) - {item['reason']}")
            if not dry_run:
                try:
                    item['path'].unlink()
                    print(f"     ✅ Deleted")
                except Exception as e:
                    print(f"     ❌ Failed: {e}")
    
    # Handle incomplete files
    if issues['incomplete']:
        print("\n⚠️  INCOMPLETE FILES (may need redownload):")
        for item in issues['incomplete']:
            print(f"   - {item['path'].name} ({item['size_mb']:.1f} MB, expected >{item['expected_min']} MB)")
            if not dry_run:
                try:
                    item['path'].unlink()
                    print(f"     ✅ Deleted - please redownload from LM Studio")
                except Exception as e:
                    print(f"     ❌ Failed: {e}")
    
    # Handle missing mmproj files
    if issues['missing_mmproj']:
        print("\n📥 VISION MODELS MISSING MMPROJ:")
        for item in issues['missing_mmproj']:
            print(f"   - {item['dir_name']}")
            if item['mmproj_source']:
                repo, filename = item['mmproj_source']
                url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
                dest = item['dir'] / filename
                print(f"     Source: {repo}/{filename}")
                
                if not dry_run:
                    success = download_file(url, dest, filename)
                    if not success:
                        print(f"     ⚠️  You may need to download manually from HuggingFace")
            else:
                print(f"     ⚠️  No known mmproj source - check HuggingFace manually")
    
    # Summary
    total_issues = len(issues['corrupt']) + len(issues['incomplete']) + len(issues['missing_mmproj'])
    print("\n" + "="*60)
    print(f"  SUMMARY: {total_issues} issues found")
    if dry_run:
        print("  Run with --fix to repair")
    print("="*60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Repair corrupt LM Studio models')
    parser.add_argument('--scan', action='store_true', help='Scan for issues')
    parser.add_argument('--fix', action='store_true', help='Fix found issues')
    args = parser.parse_args()
    
    if not args.scan and not args.fix:
        args.scan = True
    
    issues = scan_for_issues()
    
    # Print summary
    print(f"Found issues:")
    print(f"  - Corrupt files: {len(issues['corrupt'])}")
    print(f"  - Incomplete files: {len(issues['incomplete'])}")
    print(f"  - Missing mmproj: {len(issues['missing_mmproj'])}")
    
    if args.fix:
        confirm = input("\n⚠️  This will delete corrupt files and download mmproj files. Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            repair_models(issues, dry_run=False)
        else:
            print("Aborted.")
    else:
        repair_models(issues, dry_run=True)


if __name__ == "__main__":
    main()
