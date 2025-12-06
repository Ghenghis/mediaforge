# Performance Optimization Guide for AI Training Pipeline

> **Target:** Maximum training speed using RAMDrives, GPU optimization, and Docker acceleration

---

## System Requirements

| Component | Your System | Optimal Usage |
|-----------|-------------|---------------|
| **RAM** | 64 GB | 32GB RAMDrives + 24GB system + 8GB reserve |
| **GPU** | RTX 3090 Ti (24GB) | Full VRAM utilization |
| **Storage** | NVMe SSD | Backup only, training from RAM |

---

## RAMDrive Configuration

### Drive Layout

| Drive | Size | Purpose | Speed Gain |
|-------|------|---------|------------|
| **R:** | 8 GB | Training images & captions | 10-50x faster loading |
| **M:** | 16 GB | Model weights & checkpoints | 5-10x faster saves |
| **T:** | 4 GB | Temporary processing files | Instant temp I/O |
| **O:** | 4 GB | Output cache before sync | Fast generation |

### Commands

```powershell
cd C:\Users\Admin\civitai\scripts

# Initialize all RAMDrives
python -m performance.ramdrive_manager --init

# Check status
python -m performance.ramdrive_manager --status

# Show optimization techniques  
python -m performance.ramdrive_manager --techniques

# Generate Docker compose
python -m performance.ramdrive_manager --docker-compose > docker-compose.yml

# Cleanup (syncs to disk first)
python -m performance.ramdrive_manager --cleanup
```

---

## Top 10 Performance Techniques

### 1. RAMDrive Dataset Loading (10-50x faster I/O)
```python
# Load dataset to RAMDrive before training
shutil.copytree("C:/datasets/training", "R:/training")
# Point trainer to R:/training
```

### 2. Model Weight Caching (5-10x faster loading)
```python
# Cache models on M: drive
MODEL_CACHE = "M:/models"
os.environ["HF_HOME"] = MODEL_CACHE
os.environ["TRANSFORMERS_CACHE"] = MODEL_CACHE
```

### 3. GPU VRAM RAMDisk (100x+ faster than SSD)
```powershell
# Using GpuRamDrive (when GPU idle)
# Creates ultra-fast temp storage in unused VRAM
```

### 4. VRAM-RAM Block Swapping (Train larger models)
```yaml
# Kohya training config
blocks_to_swap: 20  # Each block = ~0.3GB VRAM saved
# Trade VRAM for system RAM
```

### 5. Mixed Precision Training (2-3x faster)
```yaml
mixed_precision: bf16  # or fp16
# Uses half precision for speed
```

### 6. Gradient Checkpointing (50% VRAM reduction)
```yaml
gradient_checkpointing: true
# Recomputes activations instead of storing
```

### 7. Prefetch DataLoader (20-30% faster epochs)
```python
DataLoader(
    dataset,
    num_workers=4,
    prefetch_factor=2,
    pin_memory=True,
    persistent_workers=True
)
```

### 8. Tensor Core Optimization (3-8x faster matrix ops)
```python
# Ensure dimensions are multiples of 8 (or 16 for FP16)
batch_size = 8  # Not 7 or 9
hidden_dim = 512  # Not 500
```

### 9. CUDA Graphs (10-20% faster inference)
```python
# Capture and replay GPU operations
with torch.cuda.graph(graph):
    output = model(input)
```

### 10. Docker GPU Containers (Isolated, optimized env)
```yaml
services:
  training:
    runtime: nvidia
    shm_size: '8g'  # Shared memory for data loading
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

---

## 5 Game-Changing Ideas (Beyond RAMDrive)

### 1. Distributed Training Across GPUs
```python
# If you add another GPU
accelerate launch --multi_gpu train.py
```

### 2. Flash Attention 2
```python
# 2-4x faster attention computation
model = AutoModel.from_pretrained(
    model_name,
    attn_implementation="flash_attention_2"
)
```

### 3. Quantized Training (QLoRA)
```yaml
# Train with 4-bit quantization
quantization: 4bit
# 4x less VRAM, similar quality
```

### 4. Streaming Dataset
```python
# Don't load entire dataset to RAM
dataset = load_dataset("path", streaming=True)
```

### 5. DeepSpeed ZeRO Stage 3
```yaml
# Partition optimizer/gradients/parameters
zero_stage: 3
# Train 8x larger models on same hardware
```

---

## 5 Additional Optimizations (Research-Based)

### 1. Compiled Models (torch.compile)
```python
model = torch.compile(model, mode="reduce-overhead")
# 10-30% faster after warmup
```

### 2. Async Data Loading
```python
# Overlap data loading with GPU compute
torch.cuda.set_stream(data_stream)
```

### 3. Memory-Efficient Optimizers
```python
# Use 8-bit Adam
from bitsandbytes.optim import Adam8bit
optimizer = Adam8bit(model.parameters())
```

### 4. Activation Offloading
```yaml
# Offload activations to CPU during forward pass
cpu_offload_activations: true
```

### 5. Smart Batching
```python
# Group similar-length sequences
from torch.utils.data import BatchSampler
# Reduces padding waste
```

---

## Docker GPU Setup

### Prerequisites
1. Docker Desktop with WSL2
2. NVIDIA Container Toolkit

### docker-compose.yml
```yaml
version: "3.8"

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
    shm_size: '8g'
    volumes:
      - R:/:/ramdrive/training_data
      - M:/:/ramdrive/model_cache
      - T:/:/ramdrive/temp
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

  jupyter:
    image: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
    runtime: nvidia
    ports:
      - "8888:8888"
    volumes:
      - R:/:/ramdrive/data
      - ./notebooks:/workspace
    command: jupyter lab --ip=0.0.0.0 --allow-root --no-browser
```

### Start Training Environment
```powershell
docker-compose up -d
docker exec -it ai_training bash
```

---

## Automated Memory Management

### Before RAMDrive Creation
```python
# Automatic memory cleanup
def cleanup_ram():
    import gc
    gc.collect()
    
    # Windows: Clear standby list
    subprocess.run([
        "powershell", "-Command",
        "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
    ])
    
    # Suggest heavy processes to close
    for proc in psutil.process_iter():
        if proc.memory_info().rss > 1GB:
            print(f"Consider closing: {proc.name()}")
```

### Continuous Monitoring
```python
# Alert when resources stressed
def monitor_loop():
    while True:
        ram = psutil.virtual_memory()
        gpu = get_gpu_memory()
        
        if ram.percent > 90:
            trigger_cleanup()
            
        if gpu.percent > 95:
            reduce_batch_size()
            
        time.sleep(30)
```

---

## Integration with Pipeline

### Updated Pipeline Flow
```
1. Cleanup RAM (free ~20GB)
2. Create RAMDrives (R:, M:, T:, O:)
3. Load dataset to R:
4. Load model to M:
5. Start Docker container
6. Run training (GPU accelerated)
7. Auto-sync outputs every 5 min
8. Final sync on completion
9. Cleanup RAMDrives
```

### Commands
```powershell
# Full automated training
python -m performance.ramdrive_manager --init
python -m ai.production_pipeline --sweep "R:\training" --limit 1000
python -m performance.ramdrive_manager --cleanup
```

---

## Expected Performance Gains

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Dataset loading | 30 sec | 0.5 sec | 60x faster |
| Model loading | 15 sec | 2 sec | 7.5x faster |
| Checkpoint save | 10 sec | 0.3 sec | 33x faster |
| Image captioning | 20 sec | 18 sec | 10% faster |
| Full training epoch | 2 hours | 45 min | 2.7x faster |

---

## Quick Start

```powershell
# 1. Install ImDisk (for RAMDrives)
# Download from: https://sourceforge.net/projects/imdisk-toolkit/

# 2. Initialize performance system
cd C:\Users\Admin\civitai\scripts
python -m performance.ramdrive_manager --init

# 3. Load training data
python -c "from performance.ramdrive_manager import *; mgr = PerformanceManager(); mgr.prepare_training_data(Path('C:/Users/Admin/civitai/images'), 'training_data')"

# 4. Run training
python -m ai.production_pipeline --sweep "R:\\" --limit 200

# 5. Cleanup
python -m performance.ramdrive_manager --cleanup
```

---

*Last Updated: December 3, 2025*
