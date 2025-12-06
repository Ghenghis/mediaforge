# Tools & Technology Stack

> **All Local • Open Source • Free**

---

## Core Tools

### 1. Image Generation

| Tool | Purpose | License | Repository |
|------|---------|---------|------------|
| **ComfyUI** | Node-based image generation | GPL-3.0 | [github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) |
| **Stable Diffusion XL** | Base model | CreativeML | [HuggingFace](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) |
| **Pony Diffusion V6** | Anime/stylized base | Fair AI | [Civitai](https://civitai.com/models/257749) |

**ComfyUI Custom Nodes (Required):**

| Node | Purpose | Repository |
|------|---------|------------|
| ComfyUI-WD14-Tagger | Auto image tagging | [pythongosssss/ComfyUI-WD14-Tagger](https://github.com/pythongosssss/ComfyUI-WD14-Tagger) |
| ComfyUI-BLIP | Image captioning | [1038lab/ComfyUI-Blip](https://github.com/1038lab/ComfyUI-Blip) |
| ComfyUI-Miaoshouai-Tagger | Florence-2 tagging | [miaoshouai/ComfyUI-Miaoshouai-Tagger](https://github.com/miaoshouai/ComfyUI-Miaoshouai-Tagger) |
| ComfyUI-AutoLabel | Description generation | [fexploit/ComfyUI-AutoLabel](https://github.com/fexploit/ComfyUI-AutoLabel) |

---

### 2. Image Gallery & Rating

| Tool | Purpose | License | Repository |
|------|---------|---------|------------|
| **DigiKam** | Photo management + rating | GPL-2.0 | [digikam.org](https://www.digikam.org/) |
| **PiGallery2** | Web gallery (optional) | MIT | [bpatrik/pigallery2](https://github.com/bpatrik/pigallery2) |
| **Home Gallery** | AI-powered gallery | MIT | [xemle/home-gallery](https://github.com/xemle/home-gallery) |

**DigiKam Features Used:**
- Star rating (0-5 native, extended via tags for 6-15)
- XMP sidecar metadata
- Batch operations
- SQLite database backend
- Face detection (optional)
- Similar image search

---

### 3. LoRA Training

| Tool | Purpose | License | Repository |
|------|---------|---------|------------|
| **Kohya_ss GUI** | Training interface | AGPL-3.0 | [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) |
| **sd-scripts** | Training backend | Apache-2.0 | [kohya-ss/sd-scripts](https://github.com/kohya-ss/sd-scripts) |

---

### 4. Dataset Preparation

| Tool | Purpose | License | Repository |
|------|---------|---------|------------|
| **BooruDatasetTagManager** | Tag editor GUI | GPL-3.0 | [starik222/BooruDatasetTagManager](https://github.com/starik222/BooruDatasetTagManager) |
| **DatasetTag** | Semi-auto captioning | MIT | [BinaryAlley/DatasetTag](https://github.com/BinaryAlley/DatasetTag) |
| **AutoCap** | Florence-2 captioning | MIT | [hoodini/autocap](https://github.com/hoodini/autocap) |
| **LoRA Caption Creator** | Manual caption helper | MIT | [redromnon/lora-caption-creator](https://github.com/redromnon/lora-caption-creator) |

---

### 5. Image Quality Assessment (Local)

| Tool | Purpose | License | Repository |
|------|---------|---------|------------|
| **LAION Aesthetic Predictor** | Aesthetic scoring | MIT | [LAION-AI/aesthetic-predictor](https://github.com/LAION-AI/aesthetic-predictor) |
| **Improved Aesthetic Predictor** | CLIP+MLP scoring | MIT | [christophschuhmann/improved-aesthetic-predictor](https://github.com/christophschuhmann/improved-aesthetic-predictor) |
| **Aesthetic Score Batch** | Batch processing | MIT | [JD-2006/improved-aesthetic-predictor-batch](https://github.com/JD-2006/improved-aesthetic-predictor-batch) |
| **Aesthetics Filter** | CSV filtering | MIT | [rockerBOO/aesthetics-score](https://github.com/rockerBOO/aesthetics-score) |

---

### 6. Automation & Scripting

| Tool | Purpose | License |
|------|---------|---------|
| **Python 3.10+** | Scripting | PSF |
| **PowerShell 7** | Windows automation | MIT |
| **SQLite** | Local database | Public Domain |
| **Watchdog** | File monitoring | Apache-2.0 |

---

## Python Dependencies

```txt
# requirements.txt for Automated Studio

# Core
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.30.0

# ComfyUI Integration
websocket-client>=1.6.0
requests>=2.31.0

# Image Processing
Pillow>=10.0.0
opencv-python>=4.8.0

# Aesthetic Scoring
open-clip-torch>=2.20.0
safetensors>=0.3.0

# Captioning
accelerate>=0.21.0
sentencepiece>=0.1.99

# Database & Automation
watchdog>=3.0.0
schedule>=1.2.0

# UI (optional)
gradio>=4.0.0
streamlit>=1.28.0
```

---

## Installation Scripts

### ComfyUI Custom Nodes

```powershell
# Install all required custom nodes
$ComfyUIPath = "C:\ComfyUI"
$CustomNodes = "$ComfyUIPath\custom_nodes"

cd $CustomNodes

# WD14 Tagger
git clone https://github.com/pythongosssss/ComfyUI-WD14-Tagger

# BLIP Captioning
git clone https://github.com/1038lab/ComfyUI-Blip

# Florence-2 Tagger
git clone https://github.com/miaoshouai/ComfyUI-Miaoshouai-Tagger

# AutoLabel
git clone https://github.com/fexploit/ComfyUI-AutoLabel

Write-Host "Custom nodes installed. Restart ComfyUI."
```

### Aesthetic Predictor Setup

```powershell
# Setup aesthetic predictor locally
cd C:\Users\Admin\civitai\tools

git clone https://github.com/christophschuhmann/improved-aesthetic-predictor
cd improved-aesthetic-predictor

# Create venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install torch torchvision open-clip-torch

Write-Host "Aesthetic predictor ready."
```

---

## Tool Comparison Matrix

| Feature | DigiKam | PiGallery2 | Home Gallery |
|---------|---------|------------|--------------|
| Star Rating | ✓ (0-5) | ✗ | ✗ |
| Tags | ✓ | ✓ | ✓ |
| Face Detection | ✓ | ✓ | ✓ |
| Similar Search | ✓ | ✗ | ✓ |
| XMP Sidecar | ✓ | ✗ | ✗ |
| SQLite Backend | ✓ | ✗ | ✓ |
| Batch Edit | ✓ | ✗ | ✗ |
| Offline | ✓ | ✓ | ✓ |
| Web Interface | ✗ | ✓ | ✓ |

**Recommendation:** Use **DigiKam** for rating workflow due to native star rating and XMP metadata support.

---

## Extended Rating System (DigiKam)

DigiKam natively supports 0-5 stars. For 0-15 rating system:

### Option A: Color Labels + Stars

```
Stars (0-5) × Color Labels (3) = 15 combinations

Green  + 1-5★ = Rating 1-5   (Basic)
Yellow + 1-5★ = Rating 6-10  (Good to Hot)
Red    + 1-5★ = Rating 11-15 (Perfect)
```

### Option B: Tags

```
Create tags:
- rating/06, rating/07, ... rating/15

Stars 0-5 = Native ratings
Tags = Extended ratings 6-15
```

### Option C: Custom Database

```
Use external SQLite database
DigiKam for viewing only
Custom UI for extended rating
```

---

## GPU Memory Requirements

| Task | VRAM Required | RTX 3090 Ti |
|------|---------------|-------------|
| SDXL Generation | 8-12GB | ✓ |
| LoRA Training (SDXL) | 12-20GB | ✓ |
| Aesthetic Scoring | 4-6GB | ✓ |
| BLIP Captioning | 4-8GB | ✓ |
| WD14 Tagging | 2-4GB | ✓ |

**Your RTX 3090 Ti (24GB)** can run all tasks comfortably.
