# 🔄 MASTER PIPELINE ARCHITECTURE
## Complete Multi-Pipeline Learning System for AI/Players/Users

**Created:** December 4, 2025  
**Total Pipelines:** 12 Core + 8 Advanced = 20 Pipelines

---

## 🎯 SYSTEM OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MASTER PIPELINE ARCHITECTURE                              │
│                    20 Integrated Learning Pipelines                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │  VIDEO      │   │   IMAGE     │   │   TEXT      │   │   AUDIO     │     │
│  │  PIPELINES  │   │  PIPELINES  │   │  PIPELINES  │   │  PIPELINES  │     │
│  │  (5 types)  │   │  (6 types)  │   │  (5 types)  │   │  (4 types)  │     │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘     │
│         │                 │                 │                 │             │
│         └─────────────────┼─────────────────┼─────────────────┘             │
│                           ▼                                                  │
│                  ┌─────────────────┐                                        │
│                  │   UNIFIED       │                                        │
│                  │   LEARNING      │                                        │
│                  │   ENGINE        │                                        │
│                  └────────┬────────┘                                        │
│                           │                                                  │
│         ┌─────────────────┼─────────────────┐                               │
│         ▼                 ▼                 ▼                               │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                       │
│  │   LORA      │   │   LLM       │   │   USER      │                       │
│  │   MODELS    │   │   FINE-TUNE │   │   PROFILES  │                       │
│  └─────────────┘   └─────────────┘   └─────────────┘                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 PIPELINE INVENTORY (20 Total)

### Category 1: VIDEO PIPELINES (5)

| # | Pipeline | Input | Output | Learning Type |
|---|----------|-------|--------|---------------|
| 1 | **Video Filter Pipeline** | Raw videos (55GB) | Filtered videos | Quality selection |
| 2 | **Frame Extraction Pipeline** | Videos | 16,770 frames | Scene detection |
| 3 | **Video Captioning Pipeline** | Frames | Detailed captions | Vision LLM |
| 4 | **Video Quality Pipeline** | Frames | 0-15 ratings | AI scoring |
| 5 | **Video-to-LoRA Pipeline** | Best frames | Trained LoRA | Kohya training |

### Category 2: IMAGE PIPELINES (6)

| # | Pipeline | Input | Output | Learning Type |
|---|----------|-------|--------|---------------|
| 6 | **Generation Pipeline** | Prompts | Images | ComfyUI batch |
| 7 | **Rating Pipeline** | Images | 0-15 ratings | User feedback |
| 8 | **Auto-Variation Pipeline** | High-rated (10+) | 50 variations | Automatic |
| 9 | **Gold Standard Pipeline** | Perfect (15) | Training data | Dataset building |
| 10 | **Style Transfer Pipeline** | Images + style | Styled images | Style learning |
| 11 | **Quality Upscale Pipeline** | Low-res | 8K images | Enhancement |

### Category 3: TEXT/PROMPT PIPELINES (5)

| # | Pipeline | Input | Output | Learning Type |
|---|----------|-------|--------|---------------|
| 12 | **Prompt Learning Pipeline** | Ratings + prompts | Tag weights | Correlation |
| 13 | **Story Extraction Pipeline** | Story files | Scene prompts | NLP parsing |
| 14 | **Dialog Generation Pipeline** | Characters | Dialog text | LLM creative |
| 15 | **Caption Enhancement Pipeline** | Basic captions | Detailed | LLM refinement |
| 16 | **Tag Optimization Pipeline** | All tags | Best combos | Statistical |

### Category 4: AUDIO/VOICE PIPELINES (4)

| # | Pipeline | Input | Output | Learning Type |
|---|----------|-------|--------|---------------|
| 17 | **Voice Cloning Pipeline** | Reference audio | Cloned voice | GPT-SoVITS |
| 18 | **Story Narration Pipeline** | Story text | Audio book | TTS |
| 19 | **Character Voice Pipeline** | Character profile | Unique voice | Voice synthesis |
| 20 | **Emotion Voice Pipeline** | Text + emotion | Expressive audio | Emotion TTS |

---

## 🔄 PIPELINE INTEGRATION MAP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE LEARNING FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────────────────────────────────────────────────────────┐
     │                      DATA SOURCES                                 │
     ├──────────────────────────────────────────────────────────────────┤
     │  📹 Videos (55GB)  │  📖 Stories  │  🖼️ Images  │  🎤 Audio      │
     └─────────┬──────────┴──────┬───────┴──────┬──────┴───────┬────────┘
               │                 │              │              │
               ▼                 ▼              ▼              ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                    EXTRACTION PIPELINES                          │
     ├─────────────────────────────────────────────────────────────────┤
     │  [1] Video Filter    [13] Story Extract   [8] Auto-Variation    │
     │  [2] Frame Extract   [14] Dialog Gen      [17] Voice Clone      │
     │  [3] Video Caption   [12] Prompt Learn    [18] Narration        │
     └─────────┬──────────────────┬────────────────────┬───────────────┘
               │                  │                    │
               ▼                  ▼                    ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                    ANALYSIS PIPELINES                            │
     ├─────────────────────────────────────────────────────────────────┤
     │  [4] Quality Score   [15] Caption Enhance   [19] Character Voice │
     │  [7] User Rating     [16] Tag Optimize      [20] Emotion Voice   │
     │  [10] Style Transfer                                             │
     └─────────┬──────────────────┬────────────────────┬───────────────┘
               │                  │                    │
               ▼                  ▼                    ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                    LEARNING PIPELINES                            │
     ├─────────────────────────────────────────────────────────────────┤
     │  Bronze → Silver → Gold → Platinum LoRA Training Progression    │
     │                                                                  │
     │  [5] Video-to-LoRA   [9] Gold Standard   [6] Generation         │
     │  [11] Upscale                                                    │
     └─────────┬──────────────────┬────────────────────┬───────────────┘
               │                  │                    │
               ▼                  ▼                    ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                    OUTPUT / DEPLOYMENT                           │
     ├─────────────────────────────────────────────────────────────────┤
     │  🎨 Generated Images  │  📚 Story Books  │  🎙️ Audio Books      │
     │  🤖 Trained LoRAs     │  👤 User Models  │  🎭 Character Voices  │
     └─────────────────────────────────────────────────────────────────┘
```

---

## 🎮 USE CASES BY USER TYPE

### For Players (End Users)
| Pipeline | What They Do | What AI Does |
|----------|--------------|--------------|
| Rating (7) | Rate 0-15 | Learn preferences |
| Generation (6) | Request images | Generate personalized |
| Narration (18) | Listen to stories | Generate audio |
| Character Voice (19) | Select voices | Clone/customize |

### For Creators (Content Makers)
| Pipeline | What They Do | What AI Does |
|----------|--------------|--------------|
| Story Extract (13) | Upload stories | Parse into scenes |
| Dialog Gen (14) | Define characters | Write dialog |
| Style Transfer (10) | Choose style | Apply to images |
| Voice Clone (17) | Provide sample | Create voice |

### For AI (Self-Learning)
| Pipeline | Input | Output |
|----------|-------|--------|
| Prompt Learn (12) | Rating history | Tag weight optimization |
| Auto-Variation (8) | High-rated images | 50 variations |
| Gold Standard (9) | Perfect images | Training dataset |
| Tag Optimize (16) | All generations | Best combinations |

### For Trainers (Model Builders)
| Pipeline | What They Do | What AI Does |
|----------|--------------|--------------|
| Video-to-LoRA (5) | Configure training | Full automation |
| Caption Enhance (15) | Review captions | Improve quality |
| Quality Upscale (11) | Select images | 8K enhancement |
| All Training | Monitor progress | Bronze→Platinum |

---

## 📈 LEARNING LOOPS

### Loop 1: Image Perfection Loop
```
Generate → Rate → Learn → Improve → Generate Better
    │       │       │        │           │
    └───────┴───────┴────────┴───────────┘
         (Continuous until Rating 15)
```

### Loop 2: Model Evolution Loop
```
Bronze (Video) → Silver (Rated) → Gold (High-Rated) → Platinum (Perfect)
      │              │                  │                    │
    rank=32        rank=64            rank=64             rank=128
    lr=1e-4        lr=5e-5            lr=2e-5             lr=1e-5
```

### Loop 3: Content Loop
```
Story → Scenes → Characters → Images → Captions → Audio
   │        │          │          │          │        │
   └────────┴──────────┴──────────┴──────────┴────────┘
              (Full multimedia content creation)
```

### Loop 4: Multi-Model Verification Loop
```
Model A → Caption → Model B → Verify → Model C → Finalize
   │         │          │         │         │         │
  7B        8B        12B       27B       Mix      Best
```

---

## 🛠️ TECHNICAL INTEGRATION

### API Ports Summary (All Services)
| Port | Service | Pipelines Served |
|------|---------|------------------|
| 8200 | Unified Gateway | ALL |
| 8205 | Full Pipeline | 1-5 (Video) |
| 8206 | Video Processing | 1-2 |
| 8207 | Auto-Captioner | 3, 15 |
| 8208 | Rating UI | 7 |
| 8210 | Master Orchestrator | 5, 8, 9 |
| 8211 | Dataset Builder | 9 |
| 8213 | ComfyUI Automation | 6, 8, 10, 11 |
| 8195 | Frontier Stories | 12-14 |
| 9880 | GPT-SoVITS | 17-20 |
| 1234 | LM Studio | 3, 4, 15, 16 |
| 11434 | Ollama | Backup LLM |
| 8188 | ComfyUI | 6, 10, 11 |

### Database Integration
```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED DATABASE LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  images.db      │ All images, ratings, prompts, tags            │
│  ratings.db     │ Rating history, user preferences              │
│  training.db    │ Datasets, model versions, training runs       │
│  gateway.db     │ Sessions, rate limits, API logs               │
│  orchestrator.db│ Pipeline state, cycles, history               │
│  comfyui.db     │ Prompts, generations, batches                 │
│  voices.db      │ Voice samples, generations, stories           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 PIPELINE METRICS

### Current Implementation Status

| Category | Implemented | Pending | Total |
|----------|-------------|---------|-------|
| Video Pipelines | 5 | 0 | 5 |
| Image Pipelines | 5 | 1 | 6 |
| Text Pipelines | 4 | 1 | 5 |
| Audio Pipelines | 0 | 4 | 4 |
| **TOTAL** | **14** | **6** | **20** |

### Completion Percentage: **70%**

---

## 🚀 QUICK START BY PIPELINE

### Start All Core Pipelines
```bash
python start_all_apis.py
```

### Individual Pipeline Commands

```bash
# Video Pipelines
curl -X POST http://localhost:8206/api/video/scan    # [1] Video Filter
curl -X POST http://localhost:8206/api/video/extract # [2] Frame Extract
curl -X POST http://localhost:8207/api/caption/batch # [3] Video Caption

# Image Pipelines
curl -X POST http://localhost:8213/api/comfyui/batch # [6] Generation
curl -X POST http://localhost:8208/api/rate          # [7] Rating
curl -X POST http://localhost:8210/api/orchestrator/start # [8,9] Auto & Gold

# Text Pipelines
curl -X POST http://localhost:8195/api/stories/parse # [13] Story Extract
curl http://localhost:8200/api/frontier/prompts      # [12] Prompt Learn

# Training
curl -X POST http://localhost:8211/api/dataset/build-all # Build datasets
curl -X POST http://localhost:8210/api/orchestrator/cycle # Train cycle
```

---

## 🎯 RECOMMENDED PIPELINE COMBINATIONS

### For Maximum Learning (AI Focus)
```
[1] → [2] → [3] → [4] → [5]    # Video to LoRA
[6] → [7] → [8] → [9]          # Image to Gold Standard
[12] → [16]                     # Prompt Optimization
```

### For Content Creation (User Focus)
```
[13] → [14] → [6] → [7]        # Story to Rated Images
[17] → [18] → [19]             # Voice Cloning to Narration
```

### For Quality Production (Output Focus)
```
[6] → [10] → [11]              # Generate → Style → Upscale
[15] → [9] → [5]               # Caption → Gold → Train
```

---

## ✅ NEXT ACTIONS

1. **Implement Audio Pipelines** (17-20) - GPT-SoVITS integration
2. **Complete Style Transfer** (10) - Multi-style support
3. **Add Tag Optimization** (16) - Statistical analysis
4. **Create Pipeline Dashboard** - Real-time monitoring
5. **Enable Cross-Pipeline Learning** - Unified feedback loop

---

*Total Pipelines: 20*  
*Implemented: 14 (70%)*  
*Learning Loops: 4*  
*API Endpoints: 50+*  
*Database Tables: 25+*
