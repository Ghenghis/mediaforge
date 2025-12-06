# Automated AI Image Studio

> **All Local • Open Source • Free**

## Project Vision

An intelligent, self-improving image generation system that uses iterative human feedback to progressively train better LoRA models. The system creates images, allows users to rate them, and automatically retrains based on highly-rated selections.

---

## System Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AUTOMATED AI IMAGE STUDIO                          │
│                    (Local • Open Source • Free)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐     │
│  │   ComfyUI  │──▶│   Image    │──▶│   User     │──▶│  Dataset   │     │
│  │ Generation │   │   Gallery  │   │   Rating   │   │  Curation  │     │
│  │  (Batch)   │   │  (DigiKam) │   │  (0-15★)   │   │(Automatic) │     │
│  └────────────┘   └────────────┘   └────────────┘   └────────────┘     │
│        ▲                                                   │            │
│        │                                                   ▼            │
│  ┌────────────┐                                     ┌────────────┐     │
│  │  Trained   │◀────────────────────────────────────│  Kohya_ss  │     │
│  │   LoRA     │         FEEDBACK LOOP               │  Training  │     │
│  └────────────┘                                     └────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Model Progression Tiers

| Tier | Rating | Model | Training Data |
|------|--------|-------|---------------|
| **Bronze** | 6-15★ | Production v1 | First quality filter |
| **Silver** | 10-15★ | Production v2 | Hot images only |
| **Gold** | 13-15★ | Production v3 | Perfection tier |

---

## Star Rating System (0-15)

### Visual Guide

```
Rating 0:     ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆  → DELETE (Move to rejected/)
Rating 1-5:   ★☆☆☆☆☆☆☆☆☆☆☆☆☆☆  → ARCHIVE (Basic quality)
Rating 6-9:   ★★★★★★☆☆☆☆☆☆☆☆☆  → BRONZE TIER (Good quality)
Rating 10:    ★★★★★★★★★★☆☆☆☆☆  → SILVER TIER (Hot 10!)
Rating 11-15: ★★★★★★★★★★★★★★★  → GOLD TIER (Perfection)
```

### Rating Descriptions

| Rating | Name | Description | Action |
|--------|------|-------------|--------|
| **0** | Reject | Unwanted, bad anatomy, artifacts | Delete/Move to `rejected/` |
| **1-5** | Basic | Acceptable but not training-worthy | Archive only |
| **6-7** | Good | Nice composition, minor issues | → Bronze training |
| **8-9** | Great | Quality images, good details | → Bronze training |
| **10** | Hot 10 | Almost perfect, very attractive | → Silver training |
| **11-12** | Excellent | Near-perfect features | → Gold training |
| **13-15** | Perfect | Best possible output, ideal | → Gold training |

---

## Hardware Requirements

| Component | Minimum | Recommended (Your Setup) |
|-----------|---------|--------------------------|
| GPU | RTX 3060 12GB | **RTX 3090 Ti 24GB** ✓ |
| RAM | 16GB | 32GB+ |
| Storage | 100GB SSD | 500GB+ NVMe |
| OS | Windows 10/11 | Windows 11 |

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [01-ARCHITECTURE.md](01-ARCHITECTURE.md) | System architecture & data flow |
| [02-TOOLS-STACK.md](02-TOOLS-STACK.md) | All tools & dependencies |
| [03-RATING-SYSTEM.md](03-RATING-SYSTEM.md) | Rating UI specification |
| [04-AUTOMATION-PIPELINE.md](04-AUTOMATION-PIPELINE.md) | Automation workflows |
| [05-TRAINING-GUIDE.md](05-TRAINING-GUIDE.md) | LoRA training procedures |
| [06-MILESTONES.md](06-MILESTONES.md) | Development roadmap |
| [07-RESEARCH-REFERENCES.md](07-RESEARCH-REFERENCES.md) | Papers & resources |

---

## Quick Start

```powershell
# 1. Generate images with ComfyUI (batch mode)
# 2. Rate images in DigiKam (0-15 stars)
# 3. Run curation script to sort by rating
# 4. Train LoRA with Kohya_ss
# 5. Load new LoRA, repeat cycle
```

---

## Directory Structure

```
C:\Users\Admin\civitai\
├── checkpoints/          # Base models (SDXL, Pony, etc.)
├── loras/                # Trained LoRA models
│   ├── bronze/           # Bronze tier models
│   ├── silver/           # Silver tier models
│   └── gold/             # Gold tier models
├── training/
│   ├── datasets/         # Training datasets
│   ├── output/           # Training output
│   └── logs/             # Training logs
├── gallery/
│   ├── generated/        # New generated images
│   ├── rated/            # User-rated images
│   └── rejected/         # Rating 0 images
├── scripts/              # Automation scripts
├── tools/                # Helper tools
└── docs/                 # Documentation
```
