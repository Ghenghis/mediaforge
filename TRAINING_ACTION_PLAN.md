## Professional Training Action Plan

\> **Generated:** 2025-12-03 15:54  
\> **Dataset:** 559 videos (55.7 GB)  
\> **Target:** Maximum detail learning with model rotation

## 📊 DATASET ANALYSIS

| Metric | Value |
| --- | --- |
| Total Videos | 559 |
| Total Size | 55.7 GB |
| Batches | 6 × 10GB |
| Frames per Video | 30 |
| **Total Frames** | **16,770** |

## 🔄 TRAINING ROUNDS CALCULATION

### Formula

```plaintext
Total Rounds = Passes per Batch × 3 (multiplier) × Categories
```

### Your Configuration

| Parameter | Value | Explanation |
| --- | --- | --- |
| Epochs per Batch | 10 | Training iterations |
| Passes Multiplier | ×3 | For thorough learning |
| **Total Rounds/Category** | **30** | Complete training cycles |

### Round Distribution

*   **Pass 1 (Foundation):** Rounds 1-10 - Initial learning
*   **Pass 2 (Refinement):** Rounds 11-20 - Detail enhancement
*   **Pass 3 (Mastery):** Rounds 21-30 - Final polish

## 🔁 MODEL ROTATION STRATEGY

### Captioning Models (Rotate every 2 rounds)

*   **Model 1:** thesby\_Qwen2.5-VL-7B-NSFW-Caption-V3
*   **Model 2:** Qwen3-VL-8B-Abliterated-Caption-it
*   **Model 3:** amoral-gemma3-12B-vision

### Rotation Schedule

| Rounds | Model | Purpose |
| --- | --- | --- |
| 1-2 | thesby\_Qwen2.5-VL-7B-NSFW-Caption-V3 | Primary captioning |
| 3-4 | Qwen3-VL-8B-Abliterated-Caption-it | Cross-validation |
| 5+ | amoral-gemma3-12B-vision | Detail verification |

**Total Model Rotations:** 15

## 📦 BATCH PROCESSING PLAN

| Batch | Videos | Size | Frames | Status |
| --- | --- | --- | --- | --- |
| Batch 1 | 4 | 8.5GB | ~120 | Pending |
| Batch 2 | 6 | 8.9GB | ~180 | Pending |
| Batch 3 | 14 | 9.9GB | ~420 | Pending |
| Batch 4 | 40 | 9.9GB | ~1,200 | Pending |
| Batch 5 | 166 | 10.0GB | ~4,980 | Pending |
| Batch 6 | 329 | 8.5GB | ~9,870 | Pending |
| **Total** | **559** | **55.7GB** | **16,770** |   |

## ⏱️ TIME ESTIMATES

| Phase | Time | Notes |
| --- | --- | --- |
| Frame Extraction | 4.7h | ~30 sec/video |
| Captioning | 14.0h | ~3 sec/frame |
| Training (×3) | 69.9h | All passes |
| **Total** | **88.5h** | **~3.7 days** |

## 📋 EXECUTION CHECKLIST

### Phase 1: Setup (30 min)

*   Install ImDisk for RAMDrive
*   Create R: drive (32GB) for training data
*   Create M: drive (24GB) for model cache
*   Verify FFmpeg installed

### Phase 2: Frame Extraction (~4.7h)

*   Batch 1: Extract 4 videos
*   Batch 2: Extract 6 videos
*   Batch 3: Extract 14 videos
*   Batch 4: Extract 40 videos
*   Batch 5: Extract 166 videos
*   Batch 6: Extract 329 videos
*   Best Practices:  
     

<table><tbody><tr><td>Batch 4</td></tr><tr><td>Batch 5</td></tr><tr><td>Batch 6</td></tr></tbody></table>

<table><tbody><tr><td>Batch 4</td></tr><tr><td>Batch 5</td></tr><tr><td>Batch 6</td></tr></tbody></table>

### Phase 3: Captioning (~14.0h)

*   Load vision model in LM Studio
*   Run captioning pipeline on each batch
*   Verify caption quality (spot check 10%)
*   Generate training tags

### Phase 4: Quality Assessment

*   Score all frames (0-15 rating)
*   Sort into tiers: Gold (13+), Silver (10-12), Bronze (6-9)
*   Archive low quality (\<6)

### Phase 5: Training (~69.9h)

**Pass 1 - Foundation**

*   Train on Bronze tier (Rounds 1-3)
*   Train on Silver tier (Rounds 4-6)
*   Train on Gold tier (Rounds 7-10)

**Pass 2 - Refinement** (Rotate models)

*   Repeat with different model
*   Compare outputs
*   Adjust learning rate if needed

**Pass 3 - Mastery**

*   Final training pass
*   Generate sample outputs
*   Evaluate results

### Phase 6: Validation

*   Generate test images
*   Compare before/after
*   Document improvements

## 🎯 LORA SETTINGS FOR DETAIL

```plaintext
# Kohya_ss recommended settings for maximum detail

network_dim: 32          # Higher = more detail capacity
network_alpha: 16        # Half of dim is standard
learning_rate: 1e-4      # Conservative for detail
unet_lr: 1e-4
text_encoder_lr: 5e-5

batch_size: 4            # With 24GB VRAM
resolution: 1024         # High res for detail
training_epochs: 10

# Optimization
optimizer: AdamW8bit     # Memory efficient
gradient_checkpointing: true
mixed_precision: bf16
xformers: true

# Detail preservation
min_snr_gamma: 5
noise_offset: 0.05
adaptive_noise_scale: 0.01
```

## 🔧 COMMANDS

### Quick Start

```plaintext
cd C:\Users\Admin\civitai\scripts

# 1. Setup RAMDrives
python -m performance.ramdrive_complete --setup

# 2. Analyze videos
python -m training.batch_training_pipeline --analyze

# 3. Extract frames (Batch 1)
python -m training.batch_training_pipeline --extract --batch 1

# 4. Caption batch
python -m ai.production_pipeline --sweep "R:\batch_01" --limit 1000

# 5. Start training
python -m training.batch_training_pipeline --train --batch 1 --round 1
```

### Full Automation

```plaintext
# Run complete pipeline
python -m training.batch_training_pipeline --full-run
```

## 📈 PROGRESS TRACKING

| Phase | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Batch 5 | Batch 6 |
| --- | --- | --- | --- | --- | --- | --- |
| Extract | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Caption | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Quality | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Train P1 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Train P2 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Train P3 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

Legend: ⬜ Pending | 🔄 In Progress | ✅ Complete

_Generated by Batch Training Pipeline v1.0_