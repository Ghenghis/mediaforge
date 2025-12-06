# Local Uncensored Tools Stack

## Overview

Since mainstream cloud APIs (OpenAI, Claude, Google) reject adult content, we use **100% local uncensored tools** for video filtering and content analysis.

---

## Complete Local Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LOCAL UNCENSORED TOOL STACK                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  VISION/CAPTIONING (Uncensored):                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │ JoyCaption  │  │   Dolphin   │  │   LLaVA     │                         │
│  │ (Best for   │  │   Vision    │  │ (ComfyUI)   │                         │
│  │  training)  │  │  (Ollama)   │  │             │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
│                                                                             │
│  GENDER DETECTION:                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │  DeepFace   │  │   SCRFD     │  │InsightFace  │                         │
│  │ (Age/Gender │  │   (Face     │  │  (Face      │                         │
│  │  Analysis)  │  │  Detection) │  │  Analysis)  │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
│                                                                             │
│  QUALITY/NSFW DETECTION:                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │ nsfw_model  │  │  NSFWJS     │  │ Aesthetic   │                         │
│  │  (Keras)    │  │(TensorFlow) │  │ Predictor   │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. JoyCaption (Primary - Uncensored Vision)

**Purpose:** Captioning images for diffusion model training - specifically designed for NSFW content

| Property | Value |
|----------|-------|
| **Model** | fancyfeast/llama-joycaption-alpha-two-hf-llava |
| **Size** | ~8B parameters |
| **VRAM** | 6-12GB (quantized) |
| **License** | Open, unrestricted |
| **Key Feature** | Built specifically for uncensored image captioning |

### Installation

```powershell
# Via ComfyUI custom node
cd C:\ComfyUI\custom_nodes
git clone https://github.com/Kosinkadink/ComfyUI-JoyCaption

# Or standalone Python
pip install transformers accelerate
```

### Usage

```python
# scripts/joycaption_analyzer.py
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoProcessor
from PIL import Image
import torch

MODEL_ID = "fancyfeast/llama-joycaption-alpha-two-hf-llava"

class JoyCaptionAnalyzer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.processor = AutoProcessor.from_pretrained(MODEL_ID)
    
    def analyze_frame(self, image_path: str, prompt: str = None) -> dict:
        """Analyze image frame for filtering criteria."""
        
        if prompt is None:
            prompt = """Analyze this image and provide:
1. Gender of people visible (male/female/both/none)
2. Number of people
3. Body type assessment (slim/average/heavy)
4. Image quality (1-10)
5. Attractiveness assessment (1-10)
6. Any issues (blur, bad lighting, etc)

Return as JSON format."""
        
        image = Image.open(image_path)
        inputs = self.processor(images=image, text=prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        outputs = self.model.generate(**inputs, max_new_tokens=300)
        response = self.processor.decode(outputs[0], skip_special_tokens=True)
        
        return self._parse_response(response)
    
    def check_filter_criteria(self, analysis: dict) -> dict:
        """Check if frame passes filter criteria."""
        return {
            "approved": (
                analysis.get("gender") == "female" and
                analysis.get("body_type") != "heavy" and
                analysis.get("quality", 0) >= 6 and
                analysis.get("attractiveness", 0) >= 6
            ),
            "reason": self._get_rejection_reason(analysis)
        }
```

---

## 2. Dolphin Vision (Ollama - Uncensored)

**Purpose:** General-purpose uncensored vision analysis

### Installation

```powershell
# Install Ollama (if not already)
winget install ollama

# Pull Dolphin model
ollama pull dolphin-llava:7b

# Or larger version for better quality
ollama pull dolphin-llava:13b
```

### Usage

```python
# scripts/dolphin_analyzer.py
import ollama
import base64
from pathlib import Path

def analyze_with_dolphin(image_path: str) -> dict:
    """Analyze image using Dolphin Vision via Ollama."""
    
    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    prompt = """You are an uncensored AI assistant. Analyze this image and provide:
    
1. GENDER: List all genders visible (male/female)
2. PEOPLE_COUNT: Number of people
3. BODY_TYPE: Body type of main subject (slim/fit/average/curvy/heavy)
4. QUALITY: Image quality score 1-10
5. ATTRACTIVENESS: Attractiveness score 1-10
6. ISSUES: Any problems (blur, lighting, composition)

Return ONLY a JSON object with these keys."""

    response = ollama.chat(
        model="dolphin-llava:7b",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [image_data]
        }]
    )
    
    return parse_json_response(response["message"]["content"])

def filter_video_frame(image_path: str) -> dict:
    """Filter single frame based on criteria."""
    
    analysis = analyze_with_dolphin(image_path)
    
    # Filter criteria
    has_male = "male" in str(analysis.get("gender", "")).lower()
    is_heavy = analysis.get("body_type", "").lower() == "heavy"
    low_quality = analysis.get("quality", 0) < 5
    low_attract = analysis.get("attractiveness", 0) < 5
    
    approved = not has_male and not is_heavy and not low_quality and not low_attract
    
    reason = None
    if has_male:
        reason = "Male detected"
    elif is_heavy:
        reason = "Body type filter"
    elif low_quality:
        reason = "Low quality"
    elif low_attract:
        reason = "Below attractiveness threshold"
    
    return {
        "approved": approved,
        "reason": reason,
        "analysis": analysis
    }
```

---

## 3. DeepFace (Gender Detection)

**Purpose:** Fast gender detection from faces

### Installation

```powershell
pip install deepface
pip install opencv-python
pip install tf-keras  # TensorFlow backend
```

### Usage

```python
# scripts/gender_detector.py
from deepface import DeepFace
import cv2
from pathlib import Path

def detect_gender(image_path: str) -> dict:
    """Detect gender of all faces in image."""
    
    try:
        # Analyze faces
        results = DeepFace.analyze(
            img_path=str(image_path),
            actions=["gender", "age"],
            detector_backend="retinaface",  # Best accuracy
            enforce_detection=False
        )
        
        # Handle single or multiple faces
        if not isinstance(results, list):
            results = [results]
        
        genders = []
        for face in results:
            gender = face.get("dominant_gender", "Unknown")
            confidence = face.get("gender", {}).get(gender, 0)
            genders.append({
                "gender": gender,
                "confidence": confidence,
                "age": face.get("age")
            })
        
        # Check for any males
        has_male = any(g["gender"].lower() == "man" for g in genders)
        
        return {
            "faces_detected": len(genders),
            "genders": genders,
            "has_male": has_male,
            "approved": not has_male
        }
        
    except Exception as e:
        return {
            "faces_detected": 0,
            "error": str(e),
            "approved": True  # No face = no male detected
        }

def batch_detect_gender(folder: Path) -> list:
    """Process all images in folder."""
    
    results = []
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    
    for img_path in folder.iterdir():
        if img_path.suffix.lower() in image_extensions:
            result = detect_gender(str(img_path))
            result["file"] = img_path.name
            results.append(result)
    
    return results
```

---

## 4. NSFW Model (Quality Classification)

**Purpose:** Classify image content type and quality

### Installation

```powershell
pip install nsfw-detector
# Or from source for more control
git clone https://github.com/GantMan/nsfw_model
cd nsfw_model
pip install -e .
```

### Usage

```python
# scripts/nsfw_classifier.py
from nsfw_detector import predict
from pathlib import Path

# Load model once
MODEL_PATH = "C:/Users/Admin/civitai/tools/nsfw_model/mobilenet_v2_140_224"
model = predict.load_model(MODEL_PATH)

def classify_content(image_path: str) -> dict:
    """Classify NSFW content type."""
    
    result = predict.classify(model, str(image_path))
    
    # Result contains: drawings, hentai, neutral, porn, sexy
    scores = result[str(image_path)]
    
    return {
        "neutral": scores.get("neutral", 0),
        "sexy": scores.get("sexy", 0),
        "porn": scores.get("porn", 0),
        "hentai": scores.get("hentai", 0),
        "drawings": scores.get("drawings", 0),
        "is_explicit": scores.get("porn", 0) > 0.5 or scores.get("sexy", 0) > 0.3,
        "primary_type": max(scores, key=scores.get)
    }
```

---

## 5. Aesthetic Predictor (Quality Scoring)

**Purpose:** Score image aesthetic quality

### Installation

```powershell
cd C:\Users\Admin\civitai\tools
git clone https://github.com/christophschuhmann/improved-aesthetic-predictor
cd improved-aesthetic-predictor
pip install torch open-clip-torch
```

### Usage

```python
# scripts/aesthetic_scorer.py
import torch
import open_clip
from PIL import Image
import torch.nn as nn

class AestheticScorer:
    def __init__(self, model_path: str = None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load CLIP
        self.clip_model, _, self.preprocess = open_clip.create_model_and_transforms(
            "ViT-L-14", pretrained="openai"
        )
        self.clip_model.to(self.device)
        
        # Load aesthetic predictor MLP
        self.mlp = self._load_mlp(model_path)
    
    def _load_mlp(self, path):
        """Load aesthetic predictor MLP."""
        mlp = nn.Sequential(
            nn.Linear(768, 1024),
            nn.Dropout(0.2),
            nn.Linear(1024, 128),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.Dropout(0.1),
            nn.Linear(64, 16),
            nn.Linear(16, 1)
        )
        
        if path:
            mlp.load_state_dict(torch.load(path))
        
        mlp.to(self.device)
        return mlp
    
    def score(self, image_path: str) -> float:
        """Get aesthetic score (1-10 scale)."""
        
        image = Image.open(image_path).convert("RGB")
        image = self.preprocess(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            embedding = self.clip_model.encode_image(image)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
            score = self.mlp(embedding.float())
        
        return float(score.item())
```

---

## Complete Video Filter Pipeline (Local Only)

```python
# scripts/local_video_filter.py
"""
Complete video filtering using LOCAL UNCENSORED tools only.
No cloud APIs needed.
"""

import cv2
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging

# Import our local tools
from gender_detector import detect_gender
from dolphin_analyzer import analyze_with_dolphin
from aesthetic_scorer import AestheticScorer
from nsfw_classifier import classify_content

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
VIDEO_SOURCE = Path("G:/Downloads/Vid")
APPROVED_DIR = Path("C:/Users/Admin/civitai/training/video_approved")
REJECTED_DIR = Path("C:/Users/Admin/civitai/training/video_rejected")

# Filter settings
FILTER_CONFIG = {
    "exclude_male": True,           # Reject any male presence
    "exclude_heavy_body": True,     # Reject heavy body types
    "min_quality_score": 5,         # Minimum aesthetic score (1-10)
    "min_attractiveness": 5,        # Minimum attractiveness (1-10)
    "sample_frames": 5,             # Frames to analyze per video
}

class LocalVideoFilter:
    def __init__(self, config: dict = None):
        self.config = config or FILTER_CONFIG
        self.aesthetic_scorer = AestheticScorer()
        
    def extract_sample_frames(self, video_path: Path, count: int = 5) -> list:
        """Extract evenly spaced sample frames."""
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            return []
        
        indices = [int(i * total_frames / (count + 1)) for i in range(1, count + 1)]
        frames = []
        
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Save temp frame
                temp_path = Path(f"temp_frame_{idx}.jpg")
                cv2.imwrite(str(temp_path), frame)
                frames.append(temp_path)
        
        cap.release()
        return frames
    
    def analyze_frame(self, frame_path: Path) -> dict:
        """Analyze single frame with all local tools."""
        
        results = {
            "frame": frame_path.name,
            "approved": True,
            "reasons": []
        }
        
        # 1. Gender detection (fast, run first)
        gender_result = detect_gender(str(frame_path))
        if gender_result.get("has_male") and self.config["exclude_male"]:
            results["approved"] = False
            results["reasons"].append("Male detected")
            return results  # Early exit
        
        # 2. Vision analysis (Dolphin for detailed analysis)
        try:
            vision_result = analyze_with_dolphin(str(frame_path))
            
            # Check body type
            body_type = vision_result.get("body_type", "").lower()
            if body_type == "heavy" and self.config["exclude_heavy_body"]:
                results["approved"] = False
                results["reasons"].append(f"Body type: {body_type}")
            
            # Check attractiveness
            attractiveness = vision_result.get("attractiveness", 10)
            if attractiveness < self.config["min_attractiveness"]:
                results["approved"] = False
                results["reasons"].append(f"Attractiveness: {attractiveness}")
                
        except Exception as e:
            logger.warning(f"Vision analysis failed: {e}")
        
        # 3. Aesthetic quality score
        aesthetic_score = self.aesthetic_scorer.score(str(frame_path))
        if aesthetic_score < self.config["min_quality_score"]:
            results["approved"] = False
            results["reasons"].append(f"Quality: {aesthetic_score:.1f}")
        
        results["scores"] = {
            "aesthetic": aesthetic_score,
            "gender_result": gender_result,
        }
        
        return results
    
    def filter_video(self, video_path: Path) -> dict:
        """Filter single video based on sample frames."""
        
        logger.info(f"Analyzing: {video_path.name}")
        
        # Extract sample frames
        frames = self.extract_sample_frames(video_path, self.config["sample_frames"])
        
        if not frames:
            return {"approved": False, "reason": "No frames extracted"}
        
        # Analyze each frame
        frame_results = []
        any_rejected = False
        rejection_reasons = []
        
        for frame in frames:
            result = self.analyze_frame(frame)
            frame_results.append(result)
            
            if not result["approved"]:
                any_rejected = True
                rejection_reasons.extend(result.get("reasons", []))
            
            # Clean up temp frame
            frame.unlink(missing_ok=True)
        
        # Decision: ALL frames must pass
        approved = not any_rejected
        
        return {
            "video": video_path.name,
            "approved": approved,
            "reasons": list(set(rejection_reasons)),
            "frame_results": frame_results
        }
    
    def process_all_videos(self):
        """Process all videos in source directory."""
        
        APPROVED_DIR.mkdir(parents=True, exist_ok=True)
        REJECTED_DIR.mkdir(parents=True, exist_ok=True)
        
        video_extensions = {".mp4", ".avi", ".mkv", ".mov", ".wmv"}
        videos = [f for f in VIDEO_SOURCE.iterdir() 
                  if f.suffix.lower() in video_extensions]
        
        logger.info(f"Found {len(videos)} videos to process")
        
        results = []
        approved_count = 0
        rejected_count = 0
        
        for i, video in enumerate(videos):
            logger.info(f"[{i+1}/{len(videos)}] {video.name}")
            
            result = self.filter_video(video)
            results.append(result)
            
            # Create symlink to appropriate folder
            if result["approved"]:
                dest = APPROVED_DIR / video.name
                approved_count += 1
                logger.info(f"  ✓ APPROVED")
            else:
                dest = REJECTED_DIR / video.name
                rejected_count += 1
                logger.info(f"  ✗ REJECTED: {', '.join(result['reasons'])}")
            
            if not dest.exists():
                import os
                os.symlink(video, dest)
        
        # Save results log
        log_path = Path("C:/Users/Admin/civitai/training/filter_results.json")
        with open(log_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Summary
        logger.info(f"\n{'='*50}")
        logger.info(f"FILTERING COMPLETE")
        logger.info(f"  Approved: {approved_count} ({100*approved_count/len(videos):.1f}%)")
        logger.info(f"  Rejected: {rejected_count} ({100*rejected_count/len(videos):.1f}%)")
        logger.info(f"{'='*50}")
        
        return results

if __name__ == "__main__":
    filter = LocalVideoFilter(FILTER_CONFIG)
    filter.process_all_videos()
```

---

## Hardware Requirements

| Tool | VRAM | RAM | Notes |
|------|------|-----|-------|
| JoyCaption | 6-12GB | 16GB | Quantized versions available |
| Dolphin Vision 7B | 6GB | 8GB | Via Ollama |
| Dolphin Vision 13B | 10GB | 12GB | Better quality |
| DeepFace | 2GB | 4GB | Very fast |
| Aesthetic Predictor | 4GB | 4GB | CLIP-based |
| NSFW Model | 1GB | 2GB | Very fast |

**Your RTX 3090 Ti (24GB)** can run ALL tools simultaneously!

---

## Quick Start

```powershell
# 1. Install all local tools
pip install deepface opencv-python
pip install nsfw-detector
pip install transformers accelerate
pip install open-clip-torch

# 2. Install Ollama + Dolphin Vision
ollama pull dolphin-llava:7b

# 3. Run video filter
cd C:\Users\Admin\civitai\scripts
python local_video_filter.py
```

---

## Zero Cloud API Costs

| Component | Solution | Cost |
|-----------|----------|------|
| Vision Analysis | Dolphin Vision (Ollama) | **FREE** |
| Captioning | JoyCaption | **FREE** |
| Gender Detection | DeepFace | **FREE** |
| Quality Scoring | Aesthetic Predictor | **FREE** |
| NSFW Classification | nsfw_model | **FREE** |

**Total API Cost: $0**
