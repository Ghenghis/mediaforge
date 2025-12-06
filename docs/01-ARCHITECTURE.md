# System Architecture

## Overview

The Automated AI Image Studio is a closed-loop system that continuously improves image quality through human feedback and iterative LoRA training.

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                               │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   ComfyUI   │  │   DigiKam   │  │  Rating UI  │  │  Dashboard  │         │
│  │  (Generate) │  │  (Gallery)  │  │  (Custom)   │  │  (Status)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          AUTOMATION LAYER                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Batch     │  │   Rating    │  │   Dataset   │  │  Training   │         │
│  │ Generation  │  │  Collector  │  │   Builder   │  │  Scheduler  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Images    │  │   SQLite    │  │   Captions  │  │   Models    │         │
│  │  (Gallery)  │  │  (Ratings)  │  │   (.txt)    │  │  (.safet.)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ITERATIVE TRAINING CYCLE                            │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │   Base Model     │
    │  (SDXL/Pony)     │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐     ┌──────────────────┐
    │   ComfyUI        │────▶│   Generated      │
    │   + LoRA         │     │   Images         │
    │   (300 batch)    │     │   (gallery/)     │
    └──────────────────┘     └────────┬─────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │   User Rating    │
                             │   (0-15 stars)   │
                             │   via DigiKam    │
                             └────────┬─────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
    ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
    │   Rating 0       │   │   Rating 1-5     │   │   Rating 6-15    │
    │   (rejected/)    │   │   (archive/)     │   │   (training/)    │
    └──────────────────┘   └──────────────────┘   └────────┬─────────┘
                                                           │
                           ┌───────────────────────────────┤
                           │                               │
                           ▼                               ▼
                 ┌──────────────────┐           ┌──────────────────┐
                 │   Auto Caption   │           │   Dataset        │
                 │   (BLIP/WD14)    │           │   Structure      │
                 └────────┬─────────┘           └────────┬─────────┘
                          │                              │
                          └──────────────┬───────────────┘
                                         │
                                         ▼
                               ┌──────────────────┐
                               │   Kohya_ss      │
                               │   LoRA Training │
                               └────────┬─────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
          ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
          │   BRONZE     │    │   SILVER     │    │    GOLD      │
          │   (6-15★)    │    │   (10-15★)   │    │   (13-15★)   │
          └──────────────┘    └──────────────┘    └──────────────┘
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │   New LoRA       │
                              │   (loras/)       │
                              └────────┬─────────┘
                                       │
                                       │ LOOP BACK
                                       ▼
                              ┌──────────────────┐
                              │   Next Batch     │
                              │   Generation     │
                              └──────────────────┘
```

---

## Component Details

### 1. Image Generation (ComfyUI)

```
Input:
  - Base Model (checkpoint)
  - Current LoRA (if exists)
  - Prompt templates
  - Generation settings

Process:
  - Batch generate N images (default: 300)
  - Apply consistent quality settings
  - Save to gallery/generated/

Output:
  - PNG/JPG images
  - Generation metadata (JSON)
```

### 2. Rating System (DigiKam + Custom UI)

```
Input:
  - Generated images
  - User preferences

Process:
  - Display images in gallery view
  - Allow 0-15 star rating
  - Track rating in XMP sidecar / SQLite

Output:
  - Rated images with metadata
  - Rating database
```

### 3. Dataset Curation (Automation Scripts)

```
Input:
  - Rated images
  - Rating thresholds

Process:
  - Filter by rating tier (Bronze/Silver/Gold)
  - Auto-caption with BLIP/WD14
  - Create Kohya-compatible folder structure

Output:
  - training/datasets/XX_stylename/
  - image.png + image.txt pairs
```

### 4. LoRA Training (Kohya_ss)

```
Input:
  - Curated dataset
  - Base model
  - Training configuration

Process:
  - Train LoRA with specified parameters
  - Save checkpoints
  - Log training metrics

Output:
  - lora_name.safetensors
  - Training logs
```

---

## Database Schema (SQLite)

```sql
-- Images table
CREATE TABLE images (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    hash TEXT UNIQUE,
    rating INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    rated_at TIMESTAMP,
    generation_params TEXT,  -- JSON
    training_tier TEXT,      -- bronze/silver/gold/null
    trained_in_version INTEGER
);

-- Training runs table
CREATE TABLE training_runs (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    tier TEXT NOT NULL,      -- bronze/silver/gold
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    image_count INTEGER,
    lora_path TEXT,
    config TEXT,             -- JSON
    status TEXT              -- pending/running/completed/failed
);

-- Settings table
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

---

## File Organization

```
C:\Users\Admin\civitai\
│
├── gallery/
│   ├── generated/           # New images from ComfyUI
│   │   └── batch_YYYYMMDD_HHMMSS/
│   ├── rated/               # Images with ratings 1-15
│   │   ├── 01-05_archive/
│   │   ├── 06-09_bronze/
│   │   ├── 10_silver/
│   │   └── 11-15_gold/
│   └── rejected/            # Rating 0 images
│
├── training/
│   ├── datasets/
│   │   ├── bronze_v1/
│   │   │   └── 15_mystyle/  # repeat_concept format
│   │   ├── silver_v1/
│   │   └── gold_v1/
│   ├── output/
│   │   ├── bronze/
│   │   ├── silver/
│   │   └── gold/
│   └── logs/
│
├── loras/
│   ├── bronze/
│   │   └── mystyle_bronze_v1.safetensors
│   ├── silver/
│   │   └── mystyle_silver_v1.safetensors
│   └── gold/
│       └── mystyle_gold_v1.safetensors
│
├── scripts/
│   ├── generate_batch.py
│   ├── collect_ratings.py
│   ├── build_dataset.py
│   ├── train_lora.py
│   └── orchestrator.py      # Main automation loop
│
├── tools/
│   ├── aesthetic_scorer/
│   ├── auto_captioner/
│   └── rating_ui/
│
├── config/
│   ├── comfyui_workflow.json
│   ├── training_config.json
│   └── studio_settings.json
│
└── data/
    └── studio.db            # SQLite database
```
