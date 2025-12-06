# Automation Pipeline

## Overview

Fully automated workflow from image generation to LoRA training, requiring only user rating input.

---

## Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTOMATION PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STAGE 1: GENERATE                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ComfyUI Batch → 300 images → gallery/generated/batch_TIMESTAMP/   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 2: NOTIFY                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Alert user: "300 images ready for rating"                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 3: RATE (USER INPUT REQUIRED)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  User rates images 0-15 in DigiKam/Custom UI                        │   │
│  │  ⏱️ ~15-20 minutes for 300 images                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 4: SORT                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Auto-sort by rating → rejected/ archive/ bronze/ silver/ gold/     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 5: CAPTION                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Auto-caption training images with BLIP/WD14                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 6: BUILD DATASET                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Create Kohya-compatible folder structure                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 7: TRAIN                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Kohya_ss LoRA training → Bronze/Silver/Gold models                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 8: DEPLOY                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Copy new LoRA to loras/ → Update ComfyUI workflow                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              │ LOOP                                         │
│                              └──────────────────────────────────────────────┤
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Orchestrator Script

```python
# scripts/orchestrator.py
"""
Main automation orchestrator for AI Image Studio.
Runs continuously, managing the training pipeline.
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
CONFIG = {
    "batch_size": 300,
    "min_bronze_images": 200,
    "min_silver_images": 150,
    "min_gold_images": 100,
    "comfyui_url": "http://127.0.0.1:8188",
    "gallery_path": "C:/Users/Admin/civitai/gallery",
    "training_path": "C:/Users/Admin/civitai/training",
    "loras_path": "C:/Users/Admin/civitai/loras",
}

class StudioOrchestrator:
    def __init__(self, config):
        self.config = config
        self.current_version = self._get_current_version()
        self.state = "IDLE"
        
    def run_cycle(self):
        """Execute one complete training cycle."""
        
        # Stage 1: Generate
        self.state = "GENERATING"
        batch_path = self._generate_batch()
        
        # Stage 2: Notify
        self.state = "WAITING_FOR_RATING"
        self._notify_user(batch_path)
        
        # Stage 3: Wait for rating completion
        self._wait_for_ratings(batch_path)
        
        # Stage 4: Sort
        self.state = "SORTING"
        sorted_counts = self._sort_by_rating(batch_path)
        
        # Stage 5: Caption
        self.state = "CAPTIONING"
        self._auto_caption()
        
        # Stage 6: Build datasets
        self.state = "BUILDING_DATASET"
        datasets = self._build_datasets()
        
        # Stage 7: Train
        self.state = "TRAINING"
        self._train_loras(datasets)
        
        # Stage 8: Deploy
        self.state = "DEPLOYING"
        self._deploy_loras()
        
        self.state = "IDLE"
        self.current_version += 1
        
    def _generate_batch(self):
        """Generate batch of images via ComfyUI API."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_path = Path(self.config["gallery_path"]) / "generated" / f"batch_{timestamp}"
        batch_path.mkdir(parents=True, exist_ok=True)
        
        # Call ComfyUI API
        # ... (implementation)
        
        return batch_path
        
    def _wait_for_ratings(self, batch_path):
        """Wait until all images in batch are rated."""
        # Monitor for rating completion
        # ... (implementation)
        pass
        
    def _sort_by_rating(self, batch_path):
        """Sort images into tier folders based on rating."""
        # Read ratings from database/XMP
        # Move files to appropriate folders
        # ... (implementation)
        pass
        
    def _auto_caption(self):
        """Auto-caption training images."""
        # Use BLIP/WD14 for captioning
        # ... (implementation)
        pass
        
    def _build_datasets(self):
        """Build Kohya-compatible datasets."""
        # Create folder structure
        # ... (implementation)
        pass
        
    def _train_loras(self, datasets):
        """Train LoRA models for each tier."""
        # Call Kohya training script
        # ... (implementation)
        pass
        
    def _deploy_loras(self):
        """Deploy trained LoRAs."""
        # Copy to loras folder
        # Update ComfyUI workflow
        # ... (implementation)
        pass

if __name__ == "__main__":
    orchestrator = StudioOrchestrator(CONFIG)
    
    while True:
        orchestrator.run_cycle()
        logging.info("Cycle complete. Starting next cycle...")
```

---

## Individual Stage Scripts

### Stage 1: generate_batch.py

```python
# scripts/generate_batch.py
"""Generate batch of images via ComfyUI API."""

import json
import requests
import websocket
from pathlib import Path
from datetime import datetime

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_PATH = Path("C:/Users/Admin/civitai/gallery/generated")

def load_workflow(workflow_path: str) -> dict:
    """Load ComfyUI workflow JSON."""
    with open(workflow_path) as f:
        return json.load(f)

def queue_prompt(workflow: dict) -> str:
    """Queue prompt in ComfyUI and return prompt_id."""
    response = requests.post(
        f"{COMFYUI_URL}/prompt",
        json={"prompt": workflow}
    )
    return response.json()["prompt_id"]

def generate_batch(count: int = 300, workflow_path: str = None):
    """Generate batch of images."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = OUTPUT_PATH / f"batch_{timestamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    workflow = load_workflow(workflow_path or "config/comfyui_workflow.json")
    
    # Modify workflow to output to batch directory
    # ... (implementation specific to workflow)
    
    for i in range(count):
        # Randomize seed
        workflow["3"]["inputs"]["seed"] = random.randint(0, 2**32)
        
        # Queue and wait
        prompt_id = queue_prompt(workflow)
        wait_for_completion(prompt_id)
        
        print(f"Generated {i+1}/{count}")
    
    return batch_dir

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=300)
    parser.add_argument("--workflow", type=str, default=None)
    args = parser.parse_args()
    
    generate_batch(args.count, args.workflow)
```

### Stage 4: sort_by_rating.py

```python
# scripts/sort_by_rating.py
"""Sort images by rating into tier folders."""

import shutil
import sqlite3
from pathlib import Path

GALLERY_PATH = Path("C:/Users/Admin/civitai/gallery")
DB_PATH = Path("C:/Users/Admin/civitai/data/studio.db")

RATING_FOLDERS = {
    0: "rejected",
    (1, 5): "rated/01-05_archive",
    (6, 9): "rated/06-09_bronze",
    10: "rated/10_silver",
    (11, 15): "rated/11-15_gold",
}

def get_rating_folder(rating: int) -> str:
    """Get destination folder for rating."""
    if rating == 0:
        return RATING_FOLDERS[0]
    elif 1 <= rating <= 5:
        return RATING_FOLDERS[(1, 5)]
    elif 6 <= rating <= 9:
        return RATING_FOLDERS[(6, 9)]
    elif rating == 10:
        return RATING_FOLDERS[10]
    elif 11 <= rating <= 15:
        return RATING_FOLDERS[(11, 15)]
    return None

def sort_batch(batch_path: Path):
    """Sort all images in batch by their rating."""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    counts = {folder: 0 for folder in RATING_FOLDERS.values()}
    
    for image_path in batch_path.glob("*.png"):
        # Get rating from database
        cursor.execute(
            "SELECT rating FROM images WHERE filename = ?",
            (image_path.name,)
        )
        result = cursor.fetchone()
        
        if result is None:
            continue
            
        rating = result[0]
        dest_folder = get_rating_folder(rating)
        
        if dest_folder:
            dest_path = GALLERY_PATH / dest_folder / image_path.name
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(image_path), str(dest_path))
            counts[dest_folder] += 1
    
    conn.close()
    
    print("Sorting complete:")
    for folder, count in counts.items():
        print(f"  {folder}: {count} images")
    
    return counts

if __name__ == "__main__":
    import sys
    batch_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if batch_path:
        sort_batch(batch_path)
```

### Stage 5: auto_caption.py

```python
# scripts/auto_caption.py
"""Auto-caption images using BLIP or WD14."""

import torch
from PIL import Image
from pathlib import Path
from transformers import BlipProcessor, BlipForConditionalGeneration

# Configuration
MODEL_NAME = "Salesforce/blip-image-captioning-large"
TRIGGER_WORD = "mystyle"

class AutoCaptioner:
    def __init__(self, model_name: str = MODEL_NAME):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = BlipProcessor.from_pretrained(model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(model_name)
        self.model.to(self.device)
        
    def caption_image(self, image_path: Path) -> str:
        """Generate caption for single image."""
        image = Image.open(image_path).convert("RGB")
        
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            output = self.model.generate(**inputs, max_length=100)
        
        caption = self.processor.decode(output[0], skip_special_tokens=True)
        
        # Add trigger word
        caption = f"{TRIGGER_WORD}, {caption}"
        
        return caption
        
    def caption_folder(self, folder_path: Path):
        """Caption all images in folder, save as .txt files."""
        
        image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        
        for image_path in folder_path.iterdir():
            if image_path.suffix.lower() not in image_extensions:
                continue
                
            caption = self.caption_image(image_path)
            
            # Save caption
            caption_path = image_path.with_suffix(".txt")
            caption_path.write_text(caption)
            
            print(f"Captioned: {image_path.name}")

if __name__ == "__main__":
    import sys
    
    captioner = AutoCaptioner()
    
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    captioner.caption_folder(folder)
```

### Stage 6: build_dataset.py

```python
# scripts/build_dataset.py
"""Build Kohya-compatible dataset from rated images."""

import shutil
from pathlib import Path

GALLERY_PATH = Path("C:/Users/Admin/civitai/gallery/rated")
TRAINING_PATH = Path("C:/Users/Admin/civitai/training/datasets")

TIER_CONFIG = {
    "bronze": {
        "source_folders": ["06-09_bronze", "10_silver", "11-15_gold"],
        "repeats": 15,
        "min_images": 200,
    },
    "silver": {
        "source_folders": ["10_silver", "11-15_gold"],
        "repeats": 20,
        "min_images": 150,
    },
    "gold": {
        "source_folders": ["11-15_gold"],
        "repeats": 25,
        "min_images": 100,
    },
}

def build_dataset(tier: str, version: int = 1):
    """Build dataset for specified tier."""
    
    config = TIER_CONFIG[tier]
    dataset_name = f"{tier}_v{version}"
    
    # Create dataset folder
    dataset_path = TRAINING_PATH / dataset_name / f"{config['repeats']}_mystyle"
    dataset_path.mkdir(parents=True, exist_ok=True)
    
    # Copy images from source folders
    image_count = 0
    for source_folder in config["source_folders"]:
        source_path = GALLERY_PATH / source_folder
        
        if not source_path.exists():
            continue
            
        for image_path in source_path.glob("*.png"):
            # Copy image
            dest_image = dataset_path / image_path.name
            shutil.copy2(image_path, dest_image)
            
            # Copy caption if exists
            caption_path = image_path.with_suffix(".txt")
            if caption_path.exists():
                dest_caption = dataset_path / caption_path.name
                shutil.copy2(caption_path, dest_caption)
            
            image_count += 1
    
    print(f"Built {tier} dataset: {image_count} images")
    print(f"  Path: {dataset_path}")
    print(f"  Repeats: {config['repeats']}")
    print(f"  Effective samples: {image_count * config['repeats']}")
    
    if image_count < config["min_images"]:
        print(f"  WARNING: Below minimum ({config['min_images']}) images!")
        
    return dataset_path

if __name__ == "__main__":
    import sys
    
    tier = sys.argv[1] if len(sys.argv) > 1 else "bronze"
    version = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    build_dataset(tier, version)
```

---

## File Watchers

### Rating Monitor

```python
# scripts/rating_monitor.py
"""Monitor for rating changes and trigger pipeline stages."""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import time

class RatingHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        self.rated_count = 0
        
    def on_modified(self, event):
        if event.src_path.endswith('.xmp'):
            # XMP sidecar modified = rating changed
            self.rated_count += 1
            print(f"Rating detected: {self.rated_count}")
            
    def on_created(self, event):
        if event.src_path.endswith('.xmp'):
            self.rated_count += 1
            print(f"Rating detected: {self.rated_count}")

def watch_for_ratings(batch_path: Path, expected_count: int, timeout: int = 3600):
    """Watch batch folder until all images rated."""
    
    handler = RatingHandler(None)
    observer = Observer()
    observer.schedule(handler, str(batch_path), recursive=False)
    observer.start()
    
    start_time = time.time()
    
    try:
        while handler.rated_count < expected_count:
            if time.time() - start_time > timeout:
                print("Timeout waiting for ratings")
                break
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
    
    return handler.rated_count >= expected_count
```

---

## Scheduled Tasks

### Windows Task Scheduler Setup

```powershell
# Create scheduled task for nightly training
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\Users\Admin\civitai\scripts\orchestrator.py --mode=train-only"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "AI Studio Training" -Action $action -Trigger $trigger -Settings $settings
```

---

## Configuration File

```json
// config/studio_settings.json
{
    "generation": {
        "batch_size": 300,
        "workflow_path": "config/comfyui_workflow.json",
        "comfyui_url": "http://127.0.0.1:8188",
        "seed_mode": "random"
    },
    "rating": {
        "tool": "digikam",
        "extended_rating": true,
        "auto_sort_on_rate": false
    },
    "training": {
        "tiers": {
            "bronze": {
                "min_rating": 6,
                "max_rating": 15,
                "repeats": 15,
                "min_images": 200
            },
            "silver": {
                "min_rating": 10,
                "max_rating": 15,
                "repeats": 20,
                "min_images": 150
            },
            "gold": {
                "min_rating": 13,
                "max_rating": 15,
                "repeats": 25,
                "min_images": 100
            }
        },
        "base_model": "C:/Users/Admin/civitai/checkpoints/ponyDiffusionV6XL_v6.safetensors",
        "network_dim": 64,
        "network_alpha": 32,
        "learning_rate": 1e-4,
        "epochs": 10
    },
    "paths": {
        "gallery": "C:/Users/Admin/civitai/gallery",
        "training": "C:/Users/Admin/civitai/training",
        "loras": "C:/Users/Admin/civitai/loras",
        "database": "C:/Users/Admin/civitai/data/studio.db"
    }
}
```
