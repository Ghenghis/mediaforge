"""
MODEL DOWNLOADER
=================
Downloads missing models useful for the MediaForge project.
Supports parallel downloads (3 at a time).
"""
import os
import sys
import json
import requests
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

# ComfyUI Models Directory
COMFYUI_MODELS = Path("G:/Github/ComfyUI/models")

# Model download configurations
MODELS_TO_DOWNLOAD = {
    # SDXL Base Models (Essential for SDXL LoRA training)
    "checkpoints": [
        {
            "name": "sd_xl_base_1.0.safetensors",
            "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors",
            "size_gb": 6.94,
            "description": "SDXL Base 1.0 - Essential for SDXL LoRA training"
        },
        {
            "name": "sd_xl_refiner_1.0.safetensors",
            "url": "https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0.safetensors",
            "size_gb": 6.08,
            "description": "SDXL Refiner - Improves image details"
        },
        {
            "name": "ponyDiffusionV6XL.safetensors",
            "url": "https://civitai.com/api/download/models/290640",
            "size_gb": 6.46,
            "description": "Pony Diffusion V6 XL - Popular stylized model"
        },
        {
            "name": "juggernautXL_v9.safetensors",
            "url": "https://civitai.com/api/download/models/456194",
            "size_gb": 6.46,
            "description": "Juggernaut XL V9 - High quality realistic SDXL"
        },
    ],
    
    # VAE Models
    "vae": [
        {
            "name": "sdxl_vae.safetensors",
            "url": "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors",
            "size_gb": 0.33,
            "description": "SDXL VAE - Better color/detail decoding"
        },
        {
            "name": "vae-ft-mse-840000-ema-pruned.safetensors",
            "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors",
            "size_gb": 0.32,
            "description": "SD1.5 VAE - Better for SD1.5 models"
        },
    ],
    
    # Upscale Models
    "upscale_models": [
        {
            "name": "4x-UltraSharp.pth",
            "url": "https://huggingface.co/Kim2091/UltraSharp/resolve/main/4x-UltraSharp.pth",
            "size_gb": 0.06,
            "description": "4x UltraSharp - Excellent upscaler"
        },
        {
            "name": "RealESRGAN_x4plus.pth",
            "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
            "size_gb": 0.06,
            "description": "Real-ESRGAN 4x - Standard upscaler"
        },
    ],
    
    # CLIP Models for SDXL
    "clip": [
        {
            "name": "clip_l.safetensors",
            "url": "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors",
            "size_gb": 0.24,
            "description": "CLIP-L text encoder"
        },
    ],
    
    # ControlNet for SDXL
    "controlnet": [
        {
            "name": "diffusers_xl_canny_full.safetensors",
            "url": "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/diffusers_xl_canny_full.safetensors",
            "size_gb": 2.50,
            "description": "SDXL ControlNet Canny - Edge detection control"
        },
        {
            "name": "diffusers_xl_depth_full.safetensors",
            "url": "https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/diffusers_xl_depth_full.safetensors",
            "size_gb": 2.50,
            "description": "SDXL ControlNet Depth - Depth map control"
        },
    ],
    
    # Embeddings/Textual Inversions
    "embeddings": [
        {
            "name": "EasyNegative.safetensors",
            "url": "https://civitai.com/api/download/models/9208",
            "size_gb": 0.001,
            "description": "EasyNegative - Popular negative embedding"
        },
        {
            "name": "badhandv4.pt",
            "url": "https://civitai.com/api/download/models/20068",
            "size_gb": 0.001,
            "description": "Bad Hands V4 - Fixes hand issues"
        },
    ],
}


def get_file_size(url: str, timeout: int = 10) -> int:
    """Get file size from URL headers"""
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        return int(response.headers.get('content-length', 0))
    except:
        return 0


def download_file(url: str, dest_path: Path, name: str) -> Tuple[bool, str]:
    """Download a file with progress tracking"""
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Skip if already exists
        if dest_path.exists():
            return True, f"[SKIP] {name} already exists"
        
        print(f"[START] Downloading {name}...")
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192*16):  # 128KB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Progress every 100MB
                    if total_size > 0 and downloaded % (100*1024*1024) < 8192*16:
                        pct = (downloaded / total_size) * 100
                        print(f"  {name}: {pct:.0f}% ({downloaded/1024/1024:.0f}MB / {total_size/1024/1024:.0f}MB)")
        
        size_mb = dest_path.stat().st_size / (1024*1024)
        return True, f"[DONE] {name} ({size_mb:.1f}MB)"
        
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()  # Remove partial download
        return False, f"[FAIL] {name}: {str(e)}"


def check_existing_models() -> Dict[str, List[str]]:
    """Check which models already exist"""
    existing = {}
    for category in MODELS_TO_DOWNLOAD.keys():
        category_path = COMFYUI_MODELS / category
        if category_path.exists():
            existing[category] = [f.name for f in category_path.glob("*") if f.is_file()]
        else:
            existing[category] = []
    return existing


def get_missing_models() -> List[Dict]:
    """Get list of models that need to be downloaded"""
    existing = check_existing_models()
    missing = []
    
    for category, models in MODELS_TO_DOWNLOAD.items():
        for model in models:
            if model["name"] not in existing.get(category, []):
                missing.append({
                    **model,
                    "category": category,
                    "dest_path": COMFYUI_MODELS / category / model["name"]
                })
    
    return missing


def download_models_parallel(models: List[Dict], max_workers: int = 3):
    """Download models in parallel"""
    print(f"\n{'='*60}")
    print(f"  DOWNLOADING {len(models)} MODELS ({max_workers} parallel)")
    print(f"{'='*60}\n")
    
    total_size = sum(m.get("size_gb", 0) for m in models)
    print(f"Total download size: ~{total_size:.1f} GB\n")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_file, m["url"], m["dest_path"], m["name"]): m
            for m in models
        }
        
        for future in as_completed(futures):
            model = futures[future]
            success, message = future.result()
            results.append((model["name"], success, message))
            print(message)
    
    # Summary
    print(f"\n{'='*60}")
    succeeded = sum(1 for _, s, _ in results if s)
    print(f"  COMPLETE: {succeeded}/{len(models)} models downloaded")
    print(f"{'='*60}\n")
    
    return results


def main():
    print("="*60)
    print("  MODEL DOWNLOADER - MediaForge Project")
    print("="*60)
    
    # Check existing
    existing = check_existing_models()
    print("\nExisting models:")
    for cat, files in existing.items():
        if files:
            print(f"  {cat}: {len(files)} files")
    
    # Get missing
    missing = get_missing_models()
    
    if not missing:
        print("\n[OK] All models already downloaded!")
        return
    
    print(f"\nMissing models ({len(missing)}):")
    for m in missing:
        print(f"  - {m['name']} ({m['size_gb']:.2f}GB) - {m['description']}")
    
    total_gb = sum(m['size_gb'] for m in missing)
    print(f"\nTotal to download: {total_gb:.1f} GB")
    
    # Download
    input("\nPress Enter to start downloading (3 at a time)...")
    download_models_parallel(missing, max_workers=3)


if __name__ == "__main__":
    main()
