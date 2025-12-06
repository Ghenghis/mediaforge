# 🏗️ AI IMAGE STUDIO - MASTER BLUEPRINT
## Engineering-Grade System Architecture & Design Document

**Version:** 2.0  
**Last Updated:** December 2024  
**Classification:** Complete System Blueprint

---

## 📋 TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Architecture Diagrams](#architecture-diagrams)
3. [Data Flow Schematics](#data-flow-schematics)
4. [Component Blueprints](#component-blueprints)
5. [Model Versioning Strategy](#model-versioning-strategy)
6. [UI Dashboard Specifications](#ui-dashboard-specifications)
7. [Quality Metrics & Evaluation](#quality-metrics--evaluation)

---

## 🎯 SYSTEM OVERVIEW

### Mission Statement
Build an automated AI image generation system that produces high-quality, aesthetically pleasing images through iterative model training with human feedback.

### Core Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI IMAGE STUDIO v2.0                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   VIDEO      │    │   FRAME      │    │   MODEL      │    │  IMAGE     │ │
│  │   INGESTION  │───▶│   ANALYSIS   │───▶│   TRAINING   │───▶│  RATING    │ │
│  │   PIPELINE   │    │   ENGINE     │    │   ENGINE     │    │  SYSTEM    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                   │                   │       │
│         ▼                   ▼                   ▼                   ▼       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    REAL-TIME DASHBOARD (WPF)                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐ │   │
│  │  │ Videos  │ │ Frames  │ │Training │ │ Model   │ │ Quality Metrics │ │   │
│  │  │ Stats   │ │ Stats   │ │ Progress│ │ Scores  │ │ & Comparisons   │ │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔷 ARCHITECTURE DIAGRAMS

### 1. High-Level System Architecture

```
                                    ┌─────────────────────┐
                                    │   VIDEO SOURCE      │
                                    │   G:\Downloads\Vid  │
                                    │   (~55GB, 400+)     │
                                    └──────────┬──────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: VIDEO FILTERING                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                         │  │
│  │   ┌─────────────┐    ┌──────────────────┐    ┌───────────────────┐    │  │
│  │   │   Video     │    │   LM Studio      │    │   Filter Engine   │    │  │
│  │   │   Decoder   │───▶│   Vision API     │───▶│                   │    │  │
│  │   │   (OpenCV)  │    │                  │    │   ┌───────────┐   │    │  │
│  │   └─────────────┘    │   Model:         │    │   │ Gender    │   │    │  │
│  │                      │   qwen3-vl-8b-   │    │   │ Body Type │   │    │  │
│  │   Extract 3          │   abliterated-   │    │   │ Quality   │   │    │  │
│  │   frames/video       │   caption-it     │    │   │ Attract.  │   │    │  │
│  │                      │                  │    │   └───────────┘   │    │  │
│  │                      │   Speed: 4s/img  │    │                   │    │  │
│  │                      └──────────────────┘    └───────────────────┘    │  │
│  │                                                        │              │  │
│  └────────────────────────────────────────────────────────┼──────────────┘  │
│                                                           │                  │
│                              ┌────────────────────────────┼────────────────┐ │
│                              │                            ▼                │ │
│                              │    ┌──────────────┐  ┌──────────────┐      │ │
│                              │    │   APPROVED   │  │   REJECTED   │      │ │
│                              │    │   ~25-30%    │  │   ~70-75%    │      │ │
│                              │    └──────────────┘  └──────────────┘      │ │
│                              └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 2: FRAME EXTRACTION                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                         │  │
│  │   Approved Videos ──▶ Extract 10-30 frames/video ──▶ Quality Filter    │  │
│  │                                                                         │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │   │  Frame Selection Criteria:                                       │  │  │
│  │   │  • Motion blur < threshold                                       │  │  │
│  │   │  • Face detected & clear                                         │  │  │
│  │   │  • Lighting quality score > 6                                    │  │  │
│  │   │  • Composition score > 5                                         │  │  │
│  │   └─────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                         │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│                                    ▼                                          │
│                         ┌──────────────────┐                                  │
│                         │  TRAINING FRAMES │                                  │
│                         │  ~3000-5000 imgs │                                  │
│                         └──────────────────┘                                  │
└──────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 3: MODEL TRAINING                               │
│                                                                               │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│   │                 │   │                 │   │                 │            │
│   │   BRONZE v1.0   │──▶│   SILVER v2.0   │──▶│   GOLD v3.0     │            │
│   │   Foundation    │   │   Refined       │   │   Polished      │            │
│   │                 │   │                 │   │                 │            │
│   │   Video frames  │   │   + User rated  │   │   + Error       │            │
│   │   only          │   │   images        │   │   correction    │            │
│   │                 │   │                 │   │                 │            │
│   └─────────────────┘   └─────────────────┘   └─────────────────┘            │
│                                                        │                      │
│                                                        ▼                      │
│                                              ┌─────────────────┐              │
│                                              │                 │              │
│                                              │  PLATINUM v4.0  │              │
│                                              │  Ultimate       │              │
│                                              │                 │              │
│                                              │  Best of all    │              │
│                                              │  + Anti-failure │              │
│                                              │  training       │              │
│                                              │                 │              │
│                                              └─────────────────┘              │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2. Data Flow Schematic

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW SCHEMATIC                                │
└─────────────────────────────────────────────────────────────────────────────┘

    RAW VIDEO DATA                    PROCESSED DATA                 TRAINING DATA
    ─────────────                    ───────────────                 ─────────────
         │                                 │                              │
         ▼                                 ▼                              ▼
    ┌─────────┐                      ┌─────────┐                    ┌─────────┐
    │  .mp4   │                      │  .jpg   │                    │  .png   │
    │  .avi   │ ──Frame Extract──▶   │  .png   │ ──Captioning──▶    │  .txt   │
    │  .mkv   │                      │  .webp  │                    │  pairs  │
    └─────────┘                      └─────────┘                    └─────────┘
         │                                 │                              │
         │                                 │                              │
    ┌────┴────┐                      ┌────┴────┐                    ┌────┴────┐
    │ 55 GB   │                      │ ~15 GB  │                    │ ~20 GB  │
    │ 400+    │                      │ 5000+   │                    │ 5000+   │
    │ videos  │                      │ frames  │                    │ pairs   │
    └─────────┘                      └─────────┘                    └─────────┘


                              FILTERING PIPELINE
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                                                                          │
    │   VIDEO ──▶ FRAME ──▶ VISION AI ──▶ JSON ──▶ FILTER ──▶ APPROVE/REJECT  │
    │                                                                          │
    │   ┌──────────────────────────────────────────────────────────────────┐  │
    │   │                                                                   │  │
    │   │  Vision AI Response:                                              │  │
    │   │  {                                                                │  │
    │   │    "gender": "female",     ◀── Must be "female" only             │  │
    │   │    "body_type": "slim",    ◀── Not "heavy"                       │  │
    │   │    "quality": 7,           ◀── Must be >= 4                      │  │
    │   │    "attractiveness": 8,    ◀── Must be >= 4                      │  │
    │   │    "people_count": 1       ◀── Logged for reference              │  │
    │   │  }                                                                │  │
    │   │                                                                   │  │
    │   └──────────────────────────────────────────────────────────────────┘  │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔷 COMPONENT BLUEPRINTS

### Component 1: Video Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VIDEO INGESTION PIPELINE BLUEPRINT                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INPUT                     PROCESSING                      OUTPUT            │
│  ─────                     ──────────                      ──────            │
│                                                                              │
│  ┌─────────┐         ┌───────────────────────┐         ┌─────────────┐      │
│  │         │         │                       │         │             │      │
│  │  Video  │────────▶│   Video Validator     │────────▶│  Valid      │      │
│  │  File   │         │   • Check codec       │         │  Queue      │      │
│  │         │         │   • Check duration    │         │             │      │
│  └─────────┘         │   • Check resolution  │         └─────────────┘      │
│                      │   • Check file size   │                │             │
│                      └───────────────────────┘                │             │
│                                                               ▼             │
│                      ┌───────────────────────┐         ┌─────────────┐      │
│                      │                       │         │             │      │
│                      │   Frame Extractor     │◀────────│  Scheduler  │      │
│                      │   • FFmpeg/OpenCV     │         │             │      │
│                      │   • Sample frames     │         └─────────────┘      │
│                      │   • Quality check     │                              │
│                      │                       │                              │
│                      └───────────────────────┘                              │
│                                 │                                            │
│                                 ▼                                            │
│                      ┌───────────────────────┐                              │
│                      │   Frame Buffer        │                              │
│                      │   [img1][img2][img3]  │───────▶  To Analysis         │
│                      └───────────────────────┘                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component 2: Vision Analysis Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VISION ANALYSIS ENGINE BLUEPRINT                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                         ┌─────────────────────────┐                         │
│                         │      LM STUDIO          │                         │
│                         │      localhost:1234     │                         │
│                         └────────────┬────────────┘                         │
│                                      │                                       │
│    ┌─────────────────────────────────┼─────────────────────────────────┐    │
│    │                                 ▼                                  │    │
│    │  ┌─────────────────────────────────────────────────────────────┐  │    │
│    │  │              qwen3-vl-8b-abliterated-caption-it             │  │    │
│    │  │                                                              │  │    │
│    │  │   Parameters:                                                │  │    │
│    │  │   • Context Length: 70000                                    │  │    │
│    │  │   • GPU Offload: 36/38 layers                                │  │    │
│    │  │   • Temperature: 0.2                                         │  │    │
│    │  │   • Max Tokens: 200                                          │  │    │
│    │  │                                                              │  │    │
│    │  │   Capabilities:                                              │  │    │
│    │  │   ✓ Uncensored analysis                                      │  │    │
│    │  │   ✓ Gender detection                                         │  │    │
│    │  │   ✓ Body type classification                                 │  │    │
│    │  │   ✓ Quality scoring                                          │  │    │
│    │  │   ✓ Attractiveness rating                                    │  │    │
│    │  │                                                              │  │    │
│    │  └─────────────────────────────────────────────────────────────┘  │    │
│    │                                                                    │    │
│    │  BACKUP MODELS (in priority order):                               │    │
│    │  ┌────────────────────────────────────────────────────────────┐   │    │
│    │  │ 1. dolphin3.0-l3.2-1b_rp_uncensored (fast, less accurate)  │   │    │
│    │  │ 2. llava-llama3 (Ollama, slower but reliable)              │   │    │
│    │  │ 3. llama3.2-vision (Ollama, standard)                      │   │    │
│    │  └────────────────────────────────────────────────────────────┘   │    │
│    │                                                                    │    │
│    └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│    API INTERFACE:                                                            │
│    ┌────────────────────────────────────────────────────────────────────┐   │
│    │  POST /v1/chat/completions                                         │   │
│    │  {                                                                  │   │
│    │    "model": "qwen3-vl-8b-abliterated-caption-it",                  │   │
│    │    "messages": [{                                                   │   │
│    │      "role": "user",                                                │   │
│    │      "content": [                                                   │   │
│    │        {"type": "text", "text": "<ANALYSIS_PROMPT>"},              │   │
│    │        {"type": "image_url", "image_url": {"url": "data:..."}}     │   │
│    │      ]                                                              │   │
│    │    }],                                                              │   │
│    │    "temperature": 0.2,                                              │   │
│    │    "max_tokens": 200                                                │   │
│    │  }                                                                  │   │
│    └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔷 MODEL VERSIONING STRATEGY

### Version Evolution Path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MODEL VERSION EVOLUTION                               │
└─────────────────────────────────────────────────────────────────────────────┘

    BRONZE v1.0                SILVER v2.0              GOLD v3.0
    ───────────                ───────────              ─────────
        │                          │                        │
        ▼                          ▼                        ▼
   ┌─────────┐              ┌─────────────┐          ┌───────────┐
   │         │              │             │          │           │
   │ SPEED   │              │ SPEED       │          │ SPEED     │
   │ ████░░  │              │ ███░░░      │          │ ██░░░░    │
   │         │              │             │          │           │
   │ QUALITY │              │ QUALITY     │          │ QUALITY   │
   │ ██░░░░  │              │ ████░░      │          │ █████░    │
   │         │              │             │          │           │
   │ ACCURACY│              │ ACCURACY    │          │ ACCURACY  │
   │ ███░░░  │              │ ████░░      │          │ █████░    │
   │         │              │             │          │           │
   └─────────┘              └─────────────┘          └───────────┘
        │                          │                        │
        │                          │                        │
        └──────────────────────────┼────────────────────────┘
                                   │
                                   ▼
                           ┌─────────────┐
                           │             │
                           │ PLATINUM    │
                           │ v4.0        │
                           │             │
                           │ SPEED       │
                           │ ███░░░      │
                           │             │
                           │ QUALITY     │
                           │ ██████      │
                           │             │
                           │ ACCURACY    │
                           │ ██████      │
                           │             │
                           │ "LEARNED    │
                           │  FROM ALL   │
                           │  MISTAKES"  │
                           │             │
                           └─────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         VERSION SPECIFICATIONS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ BRONZE v1.0 - Foundation Model                                        │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │ Training Data: Video frames only (auto-filtered)                      │  │
│  │ Dataset Size:  3,000-5,000 images                                     │  │
│  │ Training Time: ~4-6 hours                                             │  │
│  │ Purpose:       Establish base aesthetic understanding                 │  │
│  │ LoRA Rank:     32                                                     │  │
│  │ Learning Rate: 1e-4                                                   │  │
│  │ Steps:         2000                                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ SILVER v2.0 - Refined Model                                           │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │ Base:          Bronze v1.0                                            │  │
│  │ Additional:    User-rated images (rating >= 7)                        │  │
│  │ Dataset Size:  +500-1000 curated images                               │  │
│  │ Training Time: ~2-3 hours                                             │  │
│  │ Purpose:       Align with user preferences                            │  │
│  │ LoRA Rank:     64                                                     │  │
│  │ Learning Rate: 5e-5                                                   │  │
│  │ Steps:         1000                                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ GOLD v3.0 - Polished Model                                            │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │ Base:          Silver v2.0                                            │  │
│  │ Additional:    Error correction dataset                               │  │
│  │                (images that failed + correct versions)                │  │
│  │ Dataset Size:  +200-500 correction pairs                              │  │
│  │ Training Time: ~1-2 hours                                             │  │
│  │ Purpose:       Fix common failure modes                               │  │
│  │ LoRA Rank:     64                                                     │  │
│  │ Learning Rate: 2e-5                                                   │  │
│  │ Steps:         500                                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ PLATINUM v4.0 - Ultimate Model                                        │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │ Strategy:      Ensemble learning from all versions                    │  │
│  │ Training:      1. Merge best aspects of Bronze/Silver/Gold            │  │
│  │                2. Anti-failure training (negative examples)           │  │
│  │                3. Style consistency reinforcement                     │  │
│  │                4. Final user preference alignment                     │  │
│  │ Dataset:       Combined best + anti-patterns                          │  │
│  │ Training Time: ~3-4 hours                                             │  │
│  │ Purpose:       Production-ready, minimal failures                     │  │
│  │ LoRA Rank:     128                                                    │  │
│  │ Learning Rate: 1e-5                                                   │  │
│  │ Steps:         1500                                                   │  │
│  │                                                                       │  │
│  │ SPECIAL FEATURES:                                                     │  │
│  │ • Learned failure patterns → avoidance training                       │  │
│  │ • Quality gate: only top 10% rated images                            │  │
│  │ • Style lock: consistent aesthetic throughout                         │  │
│  │ • Error recovery: trained on "bad → good" pairs                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Model Evaluation Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MODEL EVALUATION FRAMEWORK                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  EVALUATION DIMENSIONS:                                                      │
│  ─────────────────────                                                       │
│                                                                              │
│  1. AESTHETIC SCORE (AS)                                                     │
│     ┌──────────────────────────────────────────────────────────────────┐    │
│     │ • Composition quality (rule of thirds, balance)                   │    │
│     │ • Lighting quality (exposure, contrast, shadows)                  │    │
│     │ • Color harmony (palette coherence)                               │    │
│     │ • Detail preservation (sharpness, clarity)                        │    │
│     │                                                                   │    │
│     │ Measured by: LAION Aesthetic Predictor + Custom CNN               │    │
│     │ Score Range: 0.0 - 10.0                                           │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  2. PROMPT ADHERENCE (PA)                                                    │
│     ┌──────────────────────────────────────────────────────────────────┐    │
│     │ • CLIP score (text-image alignment)                               │    │
│     │ • Key element presence check                                      │    │
│     │ • Style consistency with prompt                                   │    │
│     │                                                                   │    │
│     │ Measured by: CLIP-L/14 + Custom element detector                  │    │
│     │ Score Range: 0.0 - 1.0                                            │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  3. TECHNICAL QUALITY (TQ)                                                   │
│     ┌──────────────────────────────────────────────────────────────────┐    │
│     │ • Artifact detection (noise, compression, banding)                │    │
│     │ • Anatomical correctness (hands, faces, proportions)              │    │
│     │ • Resolution quality (detail at zoom)                             │    │
│     │                                                                   │    │
│     │ Measured by: Custom artifact detector + anatomical CNN            │    │
│     │ Score Range: 0.0 - 10.0                                           │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  4. USER PREFERENCE (UP)                                                     │
│     ┌──────────────────────────────────────────────────────────────────┐    │
│     │ • Direct user ratings (1-10 scale)                                │    │
│     │ • A/B comparison wins                                             │    │
│     │ • Selection frequency in galleries                                │    │
│     │                                                                   │    │
│     │ Measured by: User feedback + Selection tracking                   │    │
│     │ Score Range: 0.0 - 10.0                                           │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  5. FAILURE RATE (FR)                                                        │
│     ┌──────────────────────────────────────────────────────────────────┐    │
│     │ • % of outputs below quality threshold                            │    │
│     │ • % of anatomical errors                                          │    │
│     │ • % requiring regeneration                                        │    │
│     │                                                                   │    │
│     │ Measured by: Automated QA pipeline                                │    │
│     │ Score Range: 0% - 100% (lower is better)                          │    │
│     └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│                                                                              │
│  COMPOSITE SCORE CALCULATION:                                                │
│  ────────────────────────────                                                │
│                                                                              │
│    Model Score = (AS × 0.25) + (PA × 0.20) + (TQ × 0.20) +                  │
│                  (UP × 0.25) + ((100 - FR) × 0.10)                          │
│                                                                              │
│    Grade Thresholds:                                                         │
│    ┌────────────┬────────────┬────────────────────────────────────────┐     │
│    │ Grade      │ Score      │ Description                            │     │
│    ├────────────┼────────────┼────────────────────────────────────────┤     │
│    │ S+         │ 9.0+       │ Exceptional - Production ready         │     │
│    │ S          │ 8.0-8.9    │ Excellent - Minor polish needed        │     │
│    │ A          │ 7.0-7.9    │ Good - Solid for most uses             │     │
│    │ B          │ 6.0-6.9    │ Acceptable - Needs improvement         │     │
│    │ C          │ 5.0-5.9    │ Below average - Significant work       │     │
│    │ D          │ < 5.0      │ Poor - Requires retraining             │     │
│    └────────────┴────────────┴────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔷 DIRECTORY STRUCTURE

```
C:\Users\Admin\civitai\
├── 📁 docs/
│   ├── MASTER-BLUEPRINT.md          # This document
│   ├── 00-PROJECT-OVERVIEW.md
│   ├── 06-MILESTONES.md
│   ├── 08-VIDEO-PIPELINE.md
│   ├── 09-FULL-SYSTEM-INTEGRATION.md
│   ├── 10-LOCAL-UNCENSORED-TOOLS.md
│   └── 📁 diagrams/
│       ├── system-architecture.svg
│       ├── data-flow.svg
│       └── model-evolution.svg
│
├── 📁 scripts/
│   ├── video_filter_final.py        # Main filtering script
│   ├── lmstudio_analyzer.py         # LM Studio integration
│   ├── vision_analyzer.py           # Ollama integration
│   ├── quick_test.py                # Quick testing script
│   └── test_models.py               # Model comparison
│
├── 📁 models/
│   ├── Modelfile.llava-uncensored
│   ├── Modelfile.minicpm-uncensored
│   └── Modelfile.llava-llama3-uncensored
│
├── 📁 training/
│   ├── 📁 video_approved/           # Symlinks to approved videos
│   ├── 📁 video_rejected/           # Symlinks to rejected videos
│   ├── 📁 video_frames/             # Extracted training frames
│   ├── 📁 user_rated/               # User-rated images
│   └── 📁 error_corrections/        # Bad→Good training pairs
│
├── 📁 models_output/
│   ├── 📁 bronze_v1/
│   ├── 📁 silver_v2/
│   ├── 📁 gold_v3/
│   └── 📁 platinum_v4/
│
├── 📁 ui/
│   ├── 📁 WPF/                      # WPF Dashboard app
│   │   ├── AIStudioDashboard.sln
│   │   ├── 📁 Views/
│   │   ├── 📁 ViewModels/
│   │   └── 📁 Models/
│   └── 📁 Resources/
│       ├── icons/
│       └── styles/
│
├── 📁 logs/
│   ├── video_filter.log
│   ├── filter_results.json
│   └── training_metrics.json
│
└── 📁 config/
    ├── filter_config.yaml
    ├── training_config.yaml
    └── model_versions.yaml
```

---

## 🔷 NEXT: WPF DASHBOARD SPECIFICATIONS

See: `docs/WPF-DASHBOARD-SPECS.md` (next document)
