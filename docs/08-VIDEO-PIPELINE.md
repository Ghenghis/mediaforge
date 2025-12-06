# Video-to-Image Training Pipeline

## Overview

Two-stage training system that leverages 55GB of video data for initial training, then fine-tunes with user-rated images.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VIDEO-TO-IMAGE TRAINING PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STAGE 1: VIDEO FILTERING (Automated via Cloud AI)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  G:\Downloads\Vid (55GB)                                            │   │
│  │         │                                                           │   │
│  │         ▼                                                           │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │   │
│  │  │   Sample    │───▶│   Cloud AI  │───▶│   Filter    │             │   │
│  │  │   Frames    │    │   Analysis  │    │   Decision  │             │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘             │   │
│  │                                              │                      │   │
│  │                     ┌────────────────────────┼────────────────┐     │   │
│  │                     │                        │                │     │   │
│  │                     ▼                        ▼                ▼     │   │
│  │              ┌──────────┐           ┌──────────┐      ┌──────────┐ │   │
│  │              │ APPROVED │           │ REJECTED │      │  REVIEW  │ │   │
│  │              │ (Female  │           │ (Males/  │      │ (Manual) │ │   │
│  │              │  Only)   │           │  Ugly)   │      │          │ │   │
│  │              └──────────┘           └──────────┘      └──────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 2: FRAME EXTRACTION                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Approved Videos → Extract Quality Frames → Auto-Caption            │   │
│  │  - 1 frame per 2-5 seconds                                          │   │
│  │  - Quality filtering (blur, motion, lighting)                       │   │
│  │  - ~10,000+ training frames                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 3: BASE TRAINING (Video Frames)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Train LoRA on extracted video frames                               │   │
│  │  → Creates "Foundation" model with broad knowledge                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  STAGE 4: IMAGE FINE-TUNING (User Rated)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  User rates generated images → Fine-tune Foundation model           │   │
│  │  → Creates Bronze/Silver/Gold refined models                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Video Filtering Criteria

### INCLUDE (Female-Only)
```
✓ Solo female content
✓ Female-only scenes
✓ High quality/resolution
✓ Good lighting
✓ Attractive subjects (per user preference)
```

### EXCLUDE (Automatic Rejection)
```
✗ ANY male presence (automatic exclude)
✗ Overweight subjects
✗ Unattractive/ugly content
✗ Low quality/blurry
✗ Poor lighting
✗ Excessive text/watermarks
```

---

## Cloud AI Integration

### Available APIs (from .env.local.user)

| API | Purpose | Cost Model |
|-----|---------|------------|
| **OpenAI GPT-4V** | Image analysis, content filtering | Pay per token |
| **Anthropic Claude** | Content analysis, safety check | Pay per token |
| **Google Gemini** | Vision analysis | Pay per token |
| **HuggingFace** | Local model hosting | Free (self-hosted) |
| **Ollama** | Local LLM | Free (local) |
| **LM Studio** | Local LLM | Free (local) |

### Recommended Strategy

```
1. FIRST PASS (Free/Local):
   - Use local models (Ollama/LM Studio) for initial screening
   - Basic quality checks (resolution, blur detection)
   - Gender detection using local CV models

2. SECOND PASS (Cloud AI for uncertain cases):
   - Use GPT-4V or Claude for edge cases
   - More nuanced content analysis
   - Quality scoring
```

---

## Frame Analysis Prompt

```python
# For Cloud AI content filtering
ANALYSIS_PROMPT = """
Analyze this video frame for training dataset inclusion.

REQUIRED CRITERIA (all must be TRUE):
1. Contains female subject(s) ONLY - no males visible
2. Subject is attractive (conventional beauty standards)
3. Good image quality (not blurry, good lighting)
4. No excessive watermarks or text

AUTOMATIC REJECTION if:
- Any male is visible (even partially)
- Subject appears overweight
- Low quality or blurry image
- Poor lighting or composition

Return JSON:
{
    "approved": true/false,
    "confidence": 0.0-1.0,
    "rejection_reason": "reason if rejected" or null,
    "quality_score": 1-10,
    "subjects": ["female", "male", etc],
    "attractiveness_score": 1-10
}
"""
```

---

## Video Processing Scripts

### video_filter.py

```python
# scripts/video_filter.py
"""Filter videos based on content criteria using Cloud AI."""

import os
import cv2
import json
import base64
from pathlib import Path
from openai import OpenAI
from anthropic import Anthropic

# Configuration
VIDEO_SOURCE = Path("G:/Downloads/Vid")
APPROVED_DIR = Path("C:/Users/Admin/civitai/training/video_approved")
REJECTED_DIR = Path("C:/Users/Admin/civitai/training/video_rejected")
REVIEW_DIR = Path("C:/Users/Admin/civitai/training/video_review")

# Load API keys
from dotenv import load_dotenv
load_dotenv("C:/Users/Admin/civitai/.env.local.user")

# Initialize clients
openai_client = OpenAI()
anthropic_client = Anthropic()

def extract_sample_frames(video_path: Path, count: int = 5) -> list:
    """Extract evenly spaced sample frames from video."""
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames == 0:
        return []
    
    frame_indices = [int(i * total_frames / (count + 1)) for i in range(1, count + 1)]
    frames = []
    
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', frame)
            b64_frame = base64.b64encode(buffer).decode('utf-8')
            frames.append(b64_frame)
    
    cap.release()
    return frames

def analyze_frame_openai(frame_b64: str) -> dict:
    """Analyze frame using OpenAI GPT-4V."""
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ANALYSIS_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"}
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except:
        return {"approved": False, "rejection_reason": "Parse error", "confidence": 0}

def analyze_frame_claude(frame_b64: str) -> dict:
    """Analyze frame using Anthropic Claude."""
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": frame_b64
                        }
                    },
                    {"type": "text", "text": ANALYSIS_PROMPT}
                ]
            }
        ]
    )
    
    try:
        return json.loads(response.content[0].text)
    except:
        return {"approved": False, "rejection_reason": "Parse error", "confidence": 0}

def filter_video(video_path: Path, api: str = "openai") -> dict:
    """Filter single video based on sample frames."""
    
    print(f"Analyzing: {video_path.name}")
    
    # Extract sample frames
    frames = extract_sample_frames(video_path, count=5)
    
    if not frames:
        return {"approved": False, "reason": "Could not extract frames"}
    
    # Analyze each frame
    results = []
    for i, frame in enumerate(frames):
        if api == "openai":
            result = analyze_frame_openai(frame)
        else:
            result = analyze_frame_claude(frame)
        results.append(result)
        print(f"  Frame {i+1}: {'✓' if result.get('approved') else '✗'}")
    
    # Decision logic: ALL frames must be approved
    all_approved = all(r.get("approved", False) for r in results)
    any_male = any("male" in str(r.get("subjects", [])).lower() for r in results)
    avg_quality = sum(r.get("quality_score", 0) for r in results) / len(results)
    
    # Final decision
    if any_male:
        decision = "rejected"
        reason = "Male detected in video"
    elif not all_approved:
        rejection_reasons = [r.get("rejection_reason") for r in results if not r.get("approved")]
        decision = "rejected"
        reason = "; ".join(filter(None, rejection_reasons))
    elif avg_quality < 5:
        decision = "review"
        reason = f"Low quality score: {avg_quality:.1f}"
    else:
        decision = "approved"
        reason = None
    
    return {
        "video": video_path.name,
        "decision": decision,
        "reason": reason,
        "avg_quality": avg_quality,
        "frame_results": results
    }

def process_all_videos(api: str = "openai"):
    """Process all videos in source directory."""
    
    # Create output directories
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all video files
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv'}
    videos = [f for f in VIDEO_SOURCE.iterdir() 
              if f.suffix.lower() in video_extensions]
    
    print(f"Found {len(videos)} videos to process")
    
    results_log = []
    
    for i, video in enumerate(videos):
        print(f"\n[{i+1}/{len(videos)}] Processing: {video.name}")
        
        result = filter_video(video, api=api)
        results_log.append(result)
        
        # Move to appropriate directory
        if result["decision"] == "approved":
            dest = APPROVED_DIR / video.name
        elif result["decision"] == "review":
            dest = REVIEW_DIR / video.name
        else:
            dest = REJECTED_DIR / video.name
        
        # Create symlink instead of moving (preserve original)
        if not dest.exists():
            os.symlink(video, dest)
        
        print(f"  Decision: {result['decision'].upper()}")
        if result["reason"]:
            print(f"  Reason: {result['reason']}")
    
    # Save results log
    log_path = Path("C:/Users/Admin/civitai/training/video_filter_log.json")
    with open(log_path, 'w') as f:
        json.dump(results_log, f, indent=2)
    
    # Summary
    approved = sum(1 for r in results_log if r["decision"] == "approved")
    rejected = sum(1 for r in results_log if r["decision"] == "rejected")
    review = sum(1 for r in results_log if r["decision"] == "review")
    
    print(f"\n{'='*50}")
    print(f"FILTERING COMPLETE")
    print(f"  Approved: {approved}")
    print(f"  Rejected: {rejected}")
    print(f"  Review:   {review}")
    print(f"{'='*50}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", choices=["openai", "claude"], default="openai")
    args = parser.parse_args()
    
    process_all_videos(api=args.api)
```

### extract_frames.py

```python
# scripts/extract_frames.py
"""Extract quality frames from approved videos."""

import cv2
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib

APPROVED_VIDEOS = Path("C:/Users/Admin/civitai/training/video_approved")
FRAMES_OUTPUT = Path("C:/Users/Admin/civitai/training/video_frames")

def calculate_blur_score(frame) -> float:
    """Calculate blur score using Laplacian variance."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def calculate_brightness(frame) -> float:
    """Calculate average brightness."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return hsv[:, :, 2].mean()

def is_quality_frame(frame, min_blur=100, min_brightness=50, max_brightness=220) -> bool:
    """Check if frame meets quality criteria."""
    blur = calculate_blur_score(frame)
    brightness = calculate_brightness(frame)
    
    return (blur >= min_blur and 
            min_brightness <= brightness <= max_brightness)

def extract_frames_from_video(
    video_path: Path,
    output_dir: Path,
    interval_seconds: float = 3.0,
    min_blur: float = 100
) -> int:
    """Extract quality frames from single video."""
    
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if fps == 0 or total_frames == 0:
        return 0
    
    frame_interval = int(fps * interval_seconds)
    extracted_count = 0
    
    video_hash = hashlib.md5(video_path.name.encode()).hexdigest()[:8]
    
    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_num % frame_interval == 0:
            if is_quality_frame(frame, min_blur=min_blur):
                # Save frame
                output_path = output_dir / f"{video_hash}_{frame_num:06d}.png"
                cv2.imwrite(str(output_path), frame)
                extracted_count += 1
        
        frame_num += 1
    
    cap.release()
    return extracted_count

def extract_all_frames(interval: float = 3.0):
    """Extract frames from all approved videos."""
    
    FRAMES_OUTPUT.mkdir(parents=True, exist_ok=True)
    
    videos = list(APPROVED_VIDEOS.glob("*.mp4"))
    print(f"Processing {len(videos)} approved videos")
    
    total_frames = 0
    
    for i, video in enumerate(videos):
        print(f"[{i+1}/{len(videos)}] {video.name}")
        count = extract_frames_from_video(video, FRAMES_OUTPUT, interval)
        total_frames += count
        print(f"  Extracted: {count} frames")
    
    print(f"\nTotal frames extracted: {total_frames}")
    return total_frames

if __name__ == "__main__":
    extract_all_frames(interval=3.0)
```

---

## Training Strategy

### Stage 1: Foundation Model (Video Frames)

```yaml
# Train on ~10,000+ video frames
Dataset:
  Source: C:/Users/Admin/civitai/training/video_frames
  Images: 10,000+
  Repeats: 5
  
Training:
  Network Dim: 128
  Network Alpha: 64
  Learning Rate: 2e-4
  Epochs: 15-20
  Batch Size: 4
  
Output: mystyle_foundation_v1.safetensors
```

### Stage 2: Fine-Tuning (User Images)

```yaml
# Fine-tune foundation with user-rated images
Base: Foundation model
Dataset: User-rated 10-15★ images
Repeats: 20

Training:
  Network Dim: 64  # Lower to preserve foundation
  Learning Rate: 5e-5  # Much lower
  Epochs: 8-10
  
Output: mystyle_refined_v1.safetensors
```

---

## Smart Training Termination

```python
# scripts/smart_trainer.py
"""Training with automatic termination when learning plateaus."""

class SmartTrainer:
    def __init__(self, min_learning_rate: float = 0.90):
        self.min_learning_rate = min_learning_rate
        self.loss_history = []
        self.learning_scores = []
        
    def calculate_learning_rate(self, window: int = 10) -> float:
        """Calculate how well model is still learning."""
        if len(self.loss_history) < window * 2:
            return 1.0  # Not enough data
        
        recent = self.loss_history[-window:]
        previous = self.loss_history[-window*2:-window]
        
        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        
        if previous_avg == 0:
            return 1.0
        
        # Learning rate = how much loss improved
        improvement = (previous_avg - recent_avg) / previous_avg
        return max(0, min(1, improvement * 10))  # Scale to 0-1
    
    def should_continue(self) -> bool:
        """Check if training should continue."""
        learning_rate = self.calculate_learning_rate()
        self.learning_scores.append(learning_rate)
        
        # Continue if learning above threshold
        return learning_rate >= self.min_learning_rate
    
    def get_verbose_status(self) -> dict:
        """Get detailed training status."""
        return {
            "current_loss": self.loss_history[-1] if self.loss_history else None,
            "learning_rate": self.calculate_learning_rate(),
            "total_steps": len(self.loss_history),
            "avg_loss_recent": sum(self.loss_history[-10:]) / 10 if len(self.loss_history) >= 10 else None,
            "intelligence_score": self._calculate_intelligence(),
            "learning_speed": self._calculate_speed(),
            "recommendation": "CONTINUE" if self.should_continue() else "STOP"
        }
    
    def _calculate_intelligence(self) -> float:
        """Overall model intelligence metric."""
        if not self.loss_history:
            return 0
        
        # Lower loss = higher intelligence
        current_loss = self.loss_history[-1]
        return max(0, 100 * (1 - current_loss))
    
    def _calculate_speed(self) -> str:
        """Learning speed assessment."""
        rate = self.calculate_learning_rate()
        if rate > 0.95:
            return "FAST"
        elif rate > 0.90:
            return "GOOD"
        elif rate > 0.80:
            return "SLOW"
        else:
            return "STALLED"
```

---

## Verbose Training Dashboard

```python
# scripts/training_dashboard.py
"""Real-time training progress dashboard."""

import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

console = Console()

def display_training_status(trainer, refresh_rate: float = 1.0):
    """Display live training status."""
    
    def generate_table():
        status = trainer.get_verbose_status()
        
        table = Table(title="🧠 AI Training Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")
        
        # Learning metrics
        table.add_row(
            "Learning Rate",
            f"{status['learning_rate']*100:.1f}%",
            "✓" if status['learning_rate'] >= 0.90 else "⚠"
        )
        table.add_row(
            "Current Loss",
            f"{status['current_loss']:.4f}" if status['current_loss'] else "N/A",
            ""
        )
        table.add_row(
            "Intelligence Score",
            f"{status['intelligence_score']:.1f}",
            ""
        )
        table.add_row(
            "Learning Speed",
            status['learning_speed'],
            "🚀" if status['learning_speed'] == "FAST" else ""
        )
        table.add_row(
            "Total Steps",
            str(status['total_steps']),
            ""
        )
        table.add_row(
            "Recommendation",
            status['recommendation'],
            "✓" if status['recommendation'] == "CONTINUE" else "🛑"
        )
        
        return Panel(table, title="Training Progress", border_style="blue")
    
    with Live(generate_table(), refresh_per_second=1/refresh_rate) as live:
        while trainer.should_continue():
            time.sleep(refresh_rate)
            live.update(generate_table())
```
