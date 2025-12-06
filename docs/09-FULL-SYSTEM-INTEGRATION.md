# Full System Integration

## Complete Automated Pipeline

User's only task: **Rate images (0-15★)**

Everything else is automated.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUTOMATED AI IMAGE STUDIO                              │
│                    Complete Integrated System                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DATA SOURCES                                      │   │
│  │  ┌─────────────┐              ┌─────────────┐                       │   │
│  │  │   VIDEOS    │              │   IMAGES    │                       │   │
│  │  │   55GB      │              │   Gallery   │                       │   │
│  │  │ G:\Vid      │              │   Generated │                       │   │
│  │  └──────┬──────┘              └──────┬──────┘                       │   │
│  │         │                            │                              │   │
│  │         ▼                            ▼                              │   │
│  │  ┌─────────────┐              ┌─────────────┐                       │   │
│  │  │   FILTER    │              │    USER     │                       │   │
│  │  │  (Cloud AI) │              │   RATING    │ ◀── ONLY USER TASK   │   │
│  │  │ Female-only │              │   (0-15★)   │                       │   │
│  │  └──────┬──────┘              └──────┬──────┘                       │   │
│  │         │                            │                              │   │
│  │         ▼                            ▼                              │   │
│  │  ┌─────────────┐              ┌─────────────┐                       │   │
│  │  │   EXTRACT   │              │   CURATE    │                       │   │
│  │  │   FRAMES    │              │   DATASET   │                       │   │
│  │  └──────┬──────┘              └──────┬──────┘                       │   │
│  │         │                            │                              │   │
│  │         └────────────┬───────────────┘                              │   │
│  │                      │                                              │   │
│  │                      ▼                                              │   │
│  │               ┌─────────────┐                                       │   │
│  │               │   TRAIN     │                                       │   │
│  │               │   LoRA      │                                       │   │
│  │               │  (Smart)    │                                       │   │
│  │               └──────┬──────┘                                       │   │
│  │                      │                                              │   │
│  │                      ▼                                              │   │
│  │               ┌─────────────┐                                       │   │
│  │               │   DEPLOY    │                                       │   │
│  │               │   MODEL     │                                       │   │
│  │               └──────┬──────┘                                       │   │
│  │                      │                                              │   │
│  │                      ▼                                              │   │
│  │               ┌─────────────┐                                       │   │
│  │               │  GENERATE   │                                       │   │
│  │               │   IMAGES    │──────────────────────┐                │   │
│  │               └─────────────┘                      │                │   │
│  │                                                    │                │   │
│  │                                    FEEDBACK LOOP ──┘                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## User Interface: Rating Only

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IMAGE RATING INTERFACE                               │
│                     (USER'S ONLY INTERACTION)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         [IMAGE PREVIEW]                             │   │
│  │                                                                     │   │
│  │                                                                     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  QUICK RATE:  [0:DEL] [1-5:BASIC] [6-9:GOOD] [10:HOT] [11-15:PERFECT]   │
│  │               Press number key or click                            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  [←PREV]  [NEXT→]  [SKIP]                [🔄 REFRESH]              │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  📊 Progress: 127/300 rated | 🧠 Training: Ready in 173 images    │    │
│  │  ⏱️ Session: 8:42 | 🎯 Avg Rating: 7.3★                          │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Real-Time Refresh
- **Auto-refresh**: Every 30 seconds or on demand
- **[🔄 REFRESH] button**: Manual refresh
- **Rating sync**: Instant save to database
- **Live stats**: Update as you rate

---

## Cloud API Usage

### Available APIs

```python
# From C:\Users\Admin\civitai\.env.local.user

APIS = {
    # Paid (use sparingly for filtering)
    "openai": {
        "key": "OPENAI_API_KEY",
        "model": "gpt-4o",
        "use_for": ["video_filtering", "content_analysis"]
    },
    "anthropic": {
        "key": "ANTHROPIC_API_KEY", 
        "model": "claude-3-5-sonnet",
        "use_for": ["video_filtering", "quality_scoring"]
    },
    "google": {
        "key": "GOOGLE_GENERATIVE_AI_API_KEY",
        "model": "gemini-pro-vision",
        "use_for": ["backup_filtering"]
    },
    "xai": {
        "key": "XAI_API_KEY",
        "model": "grok-vision",
        "use_for": ["experimental"]
    },
    
    # Free (local)
    "ollama": {
        "url": "http://localhost:11434",
        "use_for": ["captioning", "tagging", "quality_check"]
    },
    "lmstudio": {
        "url": "http://localhost:1234",
        "use_for": ["captioning", "tagging"]
    },
    
    # Free (cloud)
    "huggingface": {
        "token": "HUGGINGFACE_TOKEN",
        "use_for": ["model_hosting", "inference"]
    }
}
```

### Cost Optimization Strategy

```
TIER 1 - FREE (Local/HuggingFace):
├── Image captioning (BLIP, WD14)
├── Quality scoring (Aesthetic Predictor)
├── Basic content detection
└── Tagging

TIER 2 - PAID (Use strategically):
├── Video content filtering (5 frames per video)
├── Uncertain content review
├── Complex analysis tasks
└── ~$0.01-0.05 per video filtered
```

---

## Automation Scripts

### Master Orchestrator

```python
# scripts/master_orchestrator.py
"""Complete automated pipeline orchestrator."""

import asyncio
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('C:/Users/Admin/civitai/logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MasterOrchestrator:
    """Automated pipeline orchestrator."""
    
    def __init__(self):
        self.state = "IDLE"
        self.current_phase = None
        self.video_frames_ready = False
        self.foundation_model_ready = False
        
    async def run_initial_setup(self):
        """One-time setup: Filter videos and extract frames."""
        
        # Phase 1: Filter videos
        logger.info("PHASE 1: Filtering videos...")
        self.current_phase = "VIDEO_FILTERING"
        
        from video_filter import process_all_videos
        await asyncio.to_thread(process_all_videos, api="openai")
        
        # Phase 2: Extract frames
        logger.info("PHASE 2: Extracting frames from approved videos...")
        self.current_phase = "FRAME_EXTRACTION"
        
        from extract_frames import extract_all_frames
        frame_count = await asyncio.to_thread(extract_all_frames, interval=3.0)
        
        if frame_count > 5000:
            self.video_frames_ready = True
            logger.info(f"Extracted {frame_count} frames - ready for foundation training")
        
        # Phase 3: Train foundation model
        if self.video_frames_ready:
            logger.info("PHASE 3: Training foundation model...")
            self.current_phase = "FOUNDATION_TRAINING"
            
            await self._train_foundation_model()
            self.foundation_model_ready = True
        
        logger.info("Initial setup complete!")
    
    async def run_continuous_loop(self):
        """Main continuous training loop."""
        
        while True:
            try:
                # Generate new batch
                logger.info("Generating new image batch...")
                await self._generate_batch()
                
                # Wait for user ratings
                logger.info("Waiting for user to rate images...")
                await self._wait_for_ratings()
                
                # Curate and build dataset
                logger.info("Building training dataset from ratings...")
                await self._build_dataset()
                
                # Train refined model
                logger.info("Training refined model...")
                await self._train_refined_model()
                
                # Deploy new model
                logger.info("Deploying new model...")
                await self._deploy_model()
                
                logger.info("Cycle complete! Starting next cycle...")
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def _train_foundation_model(self):
        """Train foundation model from video frames."""
        from train_lora import train_lora
        
        await asyncio.to_thread(
            train_lora,
            tier="foundation",
            version=1,
            base_model="C:/Users/Admin/civitai/checkpoints/ponyDiffusionV6XL.safetensors",
            dataset_path=Path("C:/Users/Admin/civitai/training/video_frames"),
            output_path=Path("C:/Users/Admin/civitai/training/output/foundation")
        )
    
    async def _generate_batch(self, count: int = 300):
        """Generate batch of images."""
        from generate_batch import generate_batch
        await asyncio.to_thread(generate_batch, count)
    
    async def _wait_for_ratings(self, min_count: int = 200):
        """Wait until enough images are rated."""
        from rating_monitor import wait_for_ratings
        await asyncio.to_thread(wait_for_ratings, min_count)
    
    async def _build_dataset(self):
        """Build dataset from rated images."""
        from build_dataset import build_dataset
        for tier in ["bronze", "silver", "gold"]:
            await asyncio.to_thread(build_dataset, tier)
    
    async def _train_refined_model(self):
        """Train refined model with smart termination."""
        from smart_trainer import SmartTrainer
        
        trainer = SmartTrainer(min_learning_rate=0.90)
        # Training with automatic stopping when learning < 90%
        await asyncio.to_thread(trainer.train_with_monitoring)
    
    async def _deploy_model(self):
        """Deploy trained model to ComfyUI."""
        from deploy_model import deploy_latest_model
        await asyncio.to_thread(deploy_latest_model)

async def main():
    orchestrator = MasterOrchestrator()
    
    # Run initial setup (one-time)
    await orchestrator.run_initial_setup()
    
    # Run continuous loop
    await orchestrator.run_continuous_loop()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Directory Structure (Complete)

```
C:\Users\Admin\civitai\
│
├── .env.local.user           # API keys (protected)
│
├── checkpoints/              # Base models
├── loras/                    # Trained LoRAs
│   ├── foundation/           # Video-trained base
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── training/
│   ├── video_approved/       # Filtered videos (symlinks)
│   ├── video_rejected/       # Rejected videos
│   ├── video_review/         # Needs manual review
│   ├── video_frames/         # Extracted frames
│   ├── datasets/
│   │   ├── foundation/
│   │   ├── bronze/
│   │   ├── silver/
│   │   └── gold/
│   └── output/
│
├── gallery/
│   ├── generated/            # New images
│   ├── rated/                # User-rated
│   └── rejected/
│
├── scripts/
│   ├── master_orchestrator.py
│   ├── video_filter.py
│   ├── extract_frames.py
│   ├── generate_batch.py
│   ├── rating_monitor.py
│   ├── build_dataset.py
│   ├── train_lora.py
│   ├── smart_trainer.py
│   └── deploy_model.py
│
├── tools/
│   ├── rating_ui/            # Custom rating interface
│   └── dashboard/            # Training dashboard
│
├── logs/
│   ├── orchestrator.log
│   ├── training.log
│   └── video_filter_log.json
│
├── config/
│   └── studio_settings.json
│
├── data/
│   └── studio.db             # SQLite database
│
└── docs/                     # Documentation
```

---

## Training Verbosity

### Console Output During Training

```
================================================================================
🧠 AI IMAGE STUDIO - TRAINING SESSION
================================================================================

📊 TRAINING METRICS (Live)
├── Current Epoch: 7/15
├── Step: 2,847/5,000
├── Loss: 0.0423 (↓ improving)
├── Learning Rate: 94.2% (above 90% threshold ✓)
├── Learning Speed: FAST 🚀
├── Intelligence Score: 87.4
└── ETA: 1h 23m

📈 PROGRESS GRAPH
Loss: ████████░░░░░░░░░░░░ 42%
[0.12 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 0.04]

💡 STATUS: LEARNING ACTIVELY
   Model is improving at 94.2% efficiency
   Recommendation: CONTINUE

================================================================================
Press [Q] to stop early | [P] to pause | [S] for detailed stats
================================================================================
```

### When Learning Declines

```
================================================================================
⚠️ LEARNING DECLINING

📊 CURRENT METRICS
├── Learning Rate: 87.3% (BELOW 90% threshold)
├── Decline detected for: 15 consecutive steps
├── Loss plateau at: 0.0398
└── Intelligence Score: 91.2 (stable)

🛑 AUTO-STOPPING IN: 50 steps
   Unless learning rate recovers above 90%

💾 Checkpoint saved: mystyle_silver_v1_epoch7_step2900.safetensors

================================================================================
```

---

## Quick Start Commands

```powershell
# 1. Initial Setup (run once)
cd C:\Users\Admin\civitai\scripts
python master_orchestrator.py --setup-only

# 2. Start Continuous Loop
python master_orchestrator.py

# 3. Launch Rating UI (separate terminal)
python -m tools.rating_ui

# 4. Monitor Training (separate terminal)
python -m tools.dashboard
```
