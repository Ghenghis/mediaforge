# 🎨 MEDIAFORGE
### Vision-to-Model Training Pipeline

> An automated, self-improving system that transforms videos and images into trained LoRA models through iterative human feedback and multi-stage refinement.

---

## 📋 Quick Overview

| Component | Status | Description |
|-----------|--------|-------------|
| **Video Filter** | ✅ Ready | LM Studio vision-based filtering |
| **Frame Extractor** | ✅ Ready | OpenCV-based quality extraction |
| **Model Evaluator** | ✅ Ready | Multi-metric comparison system |
| **WPF Dashboard** | ✅ Ready | Real-time monitoring UI |
| **Training Pipeline** | 🔨 Pending | Kohya_ss LoRA training |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       MEDIAFORGE                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   VIDEO SOURCE ──▶ FILTER ──▶ TRAINING ──▶ EVALUATION           │
│      55GB            LM Studio   4 Versions   Score & Grade     │
│                                                                  │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐        │
│   │ BRONZE  │──▶│ SILVER  │──▶│  GOLD   │──▶│PLATINUM │        │
│   │  v1.0   │   │  v2.0   │   │  v3.0   │   │  v4.0   │        │
│   │ Grade B │   │ Grade A │   │ Grade A+│   │ Grade S+│        │
│   └─────────┘   └─────────┘   └─────────┘   └─────────┘        │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              WPF DASHBOARD (Real-time Stats)              │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Start LM Studio
```powershell
# Load the vision model
# Model: qwen3-vl-8b-abliterated-caption-it
# Enable server on port 1234
```

### 2. Run Video Filter
```powershell
cd C:\Users\Admin\civitai\scripts
python video_filter_final.py
```

### 3. Start Dashboard API
```powershell
python dashboard_api.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 4. Launch WPF Dashboard
```powershell
cd C:\Users\Admin\civitai\ui\WPF\AIStudioDashboard
dotnet run
```

---

## 📁 Project Structure

```
C:\Users\Admin\civitai\
├── 📁 docs/                    # Documentation
│   ├── MASTER-BLUEPRINT.md     # Complete system design
│   ├── WPF-DASHBOARD-SPECS.md  # UI specifications
│   └── diagrams/               # Mermaid diagrams
│
├── 📁 scripts/                 # Python scripts
│   ├── video_filter_final.py   # Main video filter
│   ├── dashboard_api.py        # FastAPI backend
│   ├── model_evaluator.py      # Model comparison
│   ├── lmstudio_analyzer.py    # LM Studio integration
│   └── quick_test.py           # Testing utilities
│
├── 📁 ui/WPF/                  # WPF Dashboard
│   └── AIStudioDashboard/      # .NET 8 project
│
├── 📁 training/                # Training data
│   ├── video_approved/         # Approved videos
│   ├── video_rejected/         # Rejected videos
│   └── video_frames/           # Extracted frames
│
└── 📁 models_output/           # Trained models
    ├── bronze_v1/
    ├── silver_v2/
    ├── gold_v3/
    └── platinum_v4/
```

---

## 🔧 Model Versions

| Version | Purpose | Training Data | Expected Grade |
|---------|---------|---------------|----------------|
| **BRONZE v1.0** | Foundation | Video frames only | B |
| **SILVER v2.0** | Refinement | + User-rated images | A |
| **GOLD v3.0** | Polish | + Error corrections | A+ |
| **PLATINUM v4.0** | Ultimate | Best of all + anti-failure | S+ |

### Platinum Strategy
- Uses Gold v3.0 as base
- Includes top 10% outputs from all versions
- Anti-failure training with negative examples
- Strict quality gates (8.5+ aesthetic, <5% failure)
- Higher LoRA rank (128) for maximum capacity

---

## 📊 Evaluation Metrics

| Metric | Weight | Description |
|--------|--------|-------------|
| Aesthetic Score | 25% | LAION predictor visual appeal |
| Prompt Adherence | 15% | CLIP score text-image alignment |
| Technical Quality | 20% | Artifacts, sharpness, detail |
| Consistency | 10% | Style coherence across outputs |
| User Preference | 20% | Direct user ratings |
| Failure Rate | 10% | % of failed generations |

### Grading Scale
- **S+** (9.0+): Exceptional - Production ready
- **S** (8.5-8.9): Excellent
- **A** (7.0-8.4): Good
- **B** (5.5-6.9): Acceptable
- **C** (<5.5): Needs improvement

---

## 🖥️ Dashboard Features

- **System Status**: LM Studio, Ollama, GPU, VRAM monitoring
- **Video Processing**: Real-time progress, approval rates, rejection reasons
- **Model Comparison**: Side-by-side version metrics
- **Training Monitor**: Loss curves, ETA, sample outputs
- **Frame Preview**: Recent analyzed frames with scores

---

## 📋 Requirements

### Hardware
- **GPU**: RTX 3090 Ti (24GB VRAM) or better
- **RAM**: 32GB+ recommended
- **Storage**: 100GB+ for models and training data

### Software
- **Python**: 3.10+
- **.NET**: 8.0
- **LM Studio**: Latest version
- **Ollama**: Optional (backup)

### Python Dependencies
```
fastapi
uvicorn
opencv-python
requests
numpy
pydantic
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [MASTER-BLUEPRINT.md](docs/MASTER-BLUEPRINT.md) | Complete system architecture |
| [WPF-DASHBOARD-SPECS.md](docs/WPF-DASHBOARD-SPECS.md) | Dashboard specifications |
| [SYSTEM-DIAGRAMS.md](docs/diagrams/SYSTEM-DIAGRAMS.md) | Mermaid flow diagrams |
| [VIDEO-PIPELINE.md](docs/08-VIDEO-PIPELINE.md) | Video processing details |
| [LOCAL-UNCENSORED-TOOLS.md](docs/10-LOCAL-UNCENSORED-TOOLS.md) | Vision model setup |

---

## 🔮 Roadmap

### Phase 1: Foundation ✅
- [x] Video filtering with LM Studio
- [x] Model evaluation framework
- [x] WPF Dashboard design
- [x] Rating system (22 levels)
- [x] Guardrails engine
- [x] Country compliance system

### Phase 2: Story Integration ✅
- [x] Frontier Stories Engine (525 actors)
- [x] Real-time aging system
- [x] Age-based content restrictions
- [x] Family photo collections (100-750 images)
- [x] Story chapters & timelines
- [x] Interactive menu system
- [x] Master launcher (.bat)

### Phase 3: Automation 🔨
- [x] Playwright pipeline
- [x] ComfyUI integration
- [ ] Auto-repair scripts
- [ ] Proactive code quality
- [ ] Full Docker orchestration

### Phase 4: Training 📋
- [ ] Bronze v1.0 training
- [ ] Silver v2.0 training
- [ ] Gold v3.0 training
- [ ] Platinum v4.0 training

### Phase 5: Production 📋
- [ ] Full WPF implementation
- [ ] End-to-end testing
- [ ] Production deployment

---

## 🚀 Quick Launch

```powershell
# Start all services with one command
.\LAUNCH_MEDIAFORGE.bat
```

This launches:
- All API services (ratings, guardrails, stories)
- Story integration menu
- Automation pipelines (Playwright, ComfyUI)

---

## 📊 API Services

| Service | Port | Description |
|---------|------|-------------|
| Rating System | 8198 | 22-level content ratings |
| Country Rating | 8199 | Country compliance |
| Guardrails | 8200 | Content enforcement |
| Frontier Stories | 8195 | 525 actors, aging, photos |
| Dashboard | 8100 | Main API gateway |
| Playwright | 8203 | Browser automation |
| ComfyUI | 8204 | Image generation |

---

## 🎭 Story System Features

- **525 Actors** with full profiles (from Frontier-Stories)
- **5 Themes**: Western, Tribal, Victorian, Fantasy, Asian
- **Real-time Aging**: Birth date → story date = exact age
- **Age Restrictions**: Strictly enforced by age group
- **Photo Collections**: 100-750 images per family
- **Story Chapters**: Images linked to narrative
- **Content Unlocks**: Age-based restriction releases

---

## 🏕️ Frontier Stories Integration

**Source:** `G:\Github\Frontier-Stories` (525 actors)

### Teepee Story Generation
Generate 300-500 images for 3 people in a dwelling:

```python
from scripts.frontier_stories_integration import FrontierStoriesIntegration

integration = FrontierStoriesIntegration()
actors = integration.select_actors_for_teepee(3, tribe_filter="Lakota")
story = integration.generate_teepee_story(actors, DwellingType.TEEPEE, 300)
```

### 15 Automated Enhancements
1. Auto-Scene Continuation
2. Character Consistency Tracking
3. User Rating Feedback Loop
4. Content Rating Auto-Detection
5. Quality Gate System
6. Mood Progression System
7. Automatic Prompt Enhancement
8. Character Relationship Tracking
9. Batch Generation Queue
10. Environmental Consistency
11. Scene Transition Smoothing
12. Time Progression Visuals
13. Dialogue-to-Scene Conversion
14. Style Lock Feature
15. Auto-Retry on Failure

### Milestone Tracking
- ✅ 525 Actors Loaded
- 🔄 10 Stories Target
- 📋 300-500 Images per Story

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [MASTER-BLUEPRINT.md](docs/MASTER-BLUEPRINT.md) | Complete system architecture |
| [KNOWN_ISSUES_AND_FIXES.md](docs/KNOWN_ISSUES_AND_FIXES.md) | Code quality issues & fixes |
| [FRONTIER_STORIES_ENHANCEMENTS.md](docs/FRONTIER_STORIES_ENHANCEMENTS.md) | 15 automated features |
| [WPF-DASHBOARD-SPECS.md](docs/WPF-DASHBOARD-SPECS.md) | Dashboard specifications |
| [SYSTEM-DIAGRAMS.md](docs/diagrams/SYSTEM-DIAGRAMS.md) | Mermaid flow diagrams |

---

## 📄 License

Private project - All rights reserved.
