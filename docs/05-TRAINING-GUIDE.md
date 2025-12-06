# LoRA Training Guide

## Overview

Training parameters optimized for RTX 3090 Ti (24GB VRAM) for iterative style refinement.

---

## Training Tiers

### Bronze Model (Production v1)

**Purpose:** First production-ready model from 6-15★ images

```yaml
Dataset:
  Source: Images rated 6-15★
  Min Images: 200
  Repeats: 15
  Effective Samples: 3000+

Training Config:
  Base Model: Pony Diffusion V6 XL / SDXL
  Network Dim: 64
  Network Alpha: 32
  Learning Rate: 1e-4
  Batch Size: 4
  Epochs: 10-12
  Optimizer: AdamW8bit
  Resolution: 1024x1024
  
Expected Time: ~2-3 hours
```

### Silver Model (Production v2)

**Purpose:** Refined model from 10-15★ (Hot 10+) images

```yaml
Dataset:
  Source: Images rated 10-15★
  Min Images: 150
  Repeats: 20
  Effective Samples: 3000+

Training Config:
  Base Model: Bronze Model as base OR fresh SDXL
  Network Dim: 64
  Network Alpha: 32
  Learning Rate: 8e-5  # Lower than Bronze
  Batch Size: 4
  Epochs: 12-15
  Optimizer: Prodigy  # Adaptive optimizer
  Resolution: 1024x1024
  
Expected Time: ~3-4 hours
```

### Gold Model (Production v3)

**Purpose:** Best-of-best model from 13-15★ perfect images

```yaml
Dataset:
  Source: Images rated 13-15★
  Min Images: 100
  Repeats: 25
  Effective Samples: 2500+

Training Config:
  Base Model: Silver Model as base
  Network Dim: 128  # Higher for more detail
  Network Alpha: 64
  Learning Rate: 5e-5  # Even lower
  Batch Size: 2-4
  Epochs: 15-20
  Optimizer: Prodigy
  Resolution: 1024x1024
  
Expected Time: ~4-5 hours
```

---

## Kohya_ss Configuration

### Directory Structure Required

```
training/
├── datasets/
│   └── bronze_v1/           # Training data root
│       └── 15_mystyle/      # {repeats}_{concept}
│           ├── image001.png
│           ├── image001.txt  # Caption
│           ├── image002.png
│           ├── image002.txt
│           └── ...
├── output/                   # LoRA output
│   └── bronze/
└── logs/                     # Training logs
```

### Kohya_ss GUI Settings

#### Source Model Tab
```
Model Path: C:\Users\Admin\civitai\checkpoints\ponyDiffusionV6XL_v6.safetensors
Model Type: SDXL
```

#### Folders Tab
```
Image folder: C:\Users\Admin\civitai\training\datasets\bronze_v1
Output folder: C:\Users\Admin\civitai\training\output\bronze
Logging folder: C:\Users\Admin\civitai\training\logs
Model output name: mystyle_bronze_v1
```

#### Training Parameters Tab

```yaml
# Basic Settings
Train batch size: 4
Epoch: 10
Max train epochs: 12
Save every N epochs: 2
Caption extension: .txt
Max token length: 225

# Learning Rate
Learning rate: 1e-4
LR scheduler: cosine_with_restarts
LR warmup steps: 100

# Optimizer
Optimizer type: AdamW8bit
# OR for Silver/Gold:
Optimizer type: Prodigy
Prodigy d_coef: 2

# Network Settings
Network dim (Rank): 64
Network alpha: 32

# Resolution
Resolution: 1024,1024
Enable buckets: True
Min bucket resolution: 512
Max bucket resolution: 1536
```

#### Advanced Tab

```yaml
# Memory Optimization
Gradient checkpointing: True
Cache latents: True
Cache latents to disk: True

# Mixed Precision
Mixed precision: bf16
Full bf16: True

# Performance
Max data loader workers: 4
Persistent data loader: True

# Regularization
Noise offset: 0.0357
Adaptive noise scale: 0.00357
```

---

## Command Line Training

### Using sd-scripts Directly

```powershell
# Activate Kohya environment
cd C:\kohya_ss
.\venv\Scripts\Activate.ps1

# Bronze Training
accelerate launch --num_cpu_threads_per_process=4 train_network.py `
    --pretrained_model_name_or_path="C:\Users\Admin\civitai\checkpoints\ponyDiffusionV6XL_v6.safetensors" `
    --train_data_dir="C:\Users\Admin\civitai\training\datasets\bronze_v1" `
    --output_dir="C:\Users\Admin\civitai\training\output\bronze" `
    --output_name="mystyle_bronze_v1" `
    --save_model_as="safetensors" `
    --network_module="networks.lora" `
    --network_dim=64 `
    --network_alpha=32 `
    --resolution="1024,1024" `
    --train_batch_size=4 `
    --max_train_epochs=10 `
    --learning_rate=1e-4 `
    --lr_scheduler="cosine_with_restarts" `
    --optimizer_type="AdamW8bit" `
    --mixed_precision="bf16" `
    --cache_latents `
    --gradient_checkpointing `
    --save_every_n_epochs=2 `
    --caption_extension=".txt" `
    --enable_bucket `
    --xformers
```

---

## Training Script (Automated)

```python
# scripts/train_lora.py
"""Automated LoRA training script."""

import subprocess
import json
from pathlib import Path
from datetime import datetime

KOHYA_PATH = Path("C:/kohya_ss")
CONFIG_PATH = Path("C:/Users/Admin/civitai/config")

TIER_CONFIGS = {
    "bronze": {
        "network_dim": 64,
        "network_alpha": 32,
        "learning_rate": 1e-4,
        "epochs": 10,
        "optimizer": "AdamW8bit",
        "batch_size": 4,
    },
    "silver": {
        "network_dim": 64,
        "network_alpha": 32,
        "learning_rate": 8e-5,
        "epochs": 12,
        "optimizer": "Prodigy",
        "batch_size": 4,
    },
    "gold": {
        "network_dim": 128,
        "network_alpha": 64,
        "learning_rate": 5e-5,
        "epochs": 15,
        "optimizer": "Prodigy",
        "batch_size": 2,
    },
}

def train_lora(
    tier: str,
    version: int,
    base_model: str,
    dataset_path: Path,
    output_path: Path,
):
    """Train LoRA for specified tier."""
    
    config = TIER_CONFIGS[tier]
    output_name = f"mystyle_{tier}_v{version}"
    
    # Build command
    cmd = [
        "accelerate", "launch",
        "--num_cpu_threads_per_process=4",
        str(KOHYA_PATH / "train_network.py"),
        f"--pretrained_model_name_or_path={base_model}",
        f"--train_data_dir={dataset_path}",
        f"--output_dir={output_path}",
        f"--output_name={output_name}",
        "--save_model_as=safetensors",
        "--network_module=networks.lora",
        f"--network_dim={config['network_dim']}",
        f"--network_alpha={config['network_alpha']}",
        "--resolution=1024,1024",
        f"--train_batch_size={config['batch_size']}",
        f"--max_train_epochs={config['epochs']}",
        f"--learning_rate={config['learning_rate']}",
        "--lr_scheduler=cosine_with_restarts",
        f"--optimizer_type={config['optimizer']}",
        "--mixed_precision=bf16",
        "--cache_latents",
        "--gradient_checkpointing",
        "--save_every_n_epochs=2",
        "--caption_extension=.txt",
        "--enable_bucket",
        "--xformers",
    ]
    
    # Add Prodigy-specific args
    if config["optimizer"] == "Prodigy":
        cmd.extend([
            "--optimizer_args", "decouple=True",
            "--optimizer_args", "weight_decay=0.01",
        ])
    
    print(f"Starting {tier} v{version} training...")
    print(f"Dataset: {dataset_path}")
    print(f"Output: {output_path / output_name}.safetensors")
    
    # Execute training
    process = subprocess.Popen(
        cmd,
        cwd=KOHYA_PATH,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    
    # Stream output
    for line in process.stdout:
        print(line, end="")
    
    process.wait()
    
    if process.returncode == 0:
        print(f"\nTraining complete: {output_name}.safetensors")
        return output_path / f"{output_name}.safetensors"
    else:
        print(f"\nTraining failed with code {process.returncode}")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", choices=["bronze", "silver", "gold"], required=True)
    parser.add_argument("--version", type=int, default=1)
    parser.add_argument("--base-model", type=str, required=True)
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    
    args = parser.parse_args()
    
    train_lora(
        args.tier,
        args.version,
        args.base_model,
        Path(args.dataset),
        Path(args.output),
    )
```

---

## Training Progress Monitoring

### Log File Locations

```
C:\Users\Admin\civitai\training\logs\
├── bronze_v1_YYYYMMDD_HHMMSS.log
├── silver_v1_YYYYMMDD_HHMMSS.log
└── gold_v1_YYYYMMDD_HHMMSS.log
```

### Key Metrics to Watch

```
Loss: Should decrease over epochs
  - Starting: ~0.1-0.2
  - Target: ~0.05-0.08
  
Learning Rate: Following cosine schedule
  - Peak: At warmup end
  - Decay: Gradual decrease
  
VRAM Usage: ~18-22GB for batch=4
```

---

## Post-Training Validation

### Quick Test Script

```python
# scripts/test_lora.py
"""Quick test of trained LoRA."""

import requests
import json

COMFYUI_URL = "http://127.0.0.1:8188"

def test_lora(lora_path: str, prompt: str, count: int = 4):
    """Generate test images with new LoRA."""
    
    workflow = {
        # Your workflow with LoRA node
        # ...
    }
    
    # Queue prompts
    for i in range(count):
        response = requests.post(
            f"{COMFYUI_URL}/prompt",
            json={"prompt": workflow}
        )
        print(f"Queued test {i+1}/{count}")
    
    print(f"Test images queued. Check ComfyUI output.")

if __name__ == "__main__":
    import sys
    
    lora_path = sys.argv[1] if len(sys.argv) > 1 else None
    if lora_path:
        test_lora(
            lora_path,
            "mystyle, 1girl, portrait, high quality",
            count=4
        )
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| OOM Error | Batch too large | Reduce batch_size to 2 |
| Loss not decreasing | LR too low/high | Adjust learning_rate |
| Overfit | Too many epochs | Reduce epochs, add noise_offset |
| Style not learned | Too few images | Add more training images |
| Bad anatomy | Base model issue | Use better base checkpoint |

### VRAM Optimization

```yaml
# If running low on VRAM:
gradient_checkpointing: True    # Saves ~4GB
cache_latents_to_disk: True     # Saves ~2GB
train_batch_size: 2             # Saves ~2GB per batch reduction
network_dim: 32                 # Saves ~1GB (but reduces quality)
```
