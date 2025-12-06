# 🤖 AI Model Management Action Plan

> **Last Updated:** December 3, 2025 3:10 PM  
> **Models Directory:** `C:\Users\Admin\.lmstudio\models`  
> **Hardware:** RTX 3090 Ti (24GB VRAM) | 64GB RAM  

---

## 🚨 CURRENT STATUS

| Service | Status |
|---------|--------|
| Ollama | ✅ Running |
| LM Studio | ✅ Running |
| RAM Usage | ⚠️ 41GB (HIGH - close unused apps!) |

**Next Action:** Load a vision model in LM Studio and run benchmark

---

## 📊 MODEL INVENTORY SUMMARY

| Metric | Count | Notes |
|--------|-------|-------|
| **Total Models** | 210 | After cleanup |
| **Total Size** | 925 GB | Optimized from 1.17 TB |
| **Space Freed** | ~245 GB | Removed duplicates, video models, corrupt |
| **Recent Downloads** | ~32 | Last 30 days |

### By Category
| Type | Count | Purpose |
|------|-------|---------|
| **Text LLMs** | ~140 | Chat, coding, writing |
| **Vision Models** | ~35 | Image captioning, OCR |
| **Embeddings** | ~20 | RAG, search |
| **Speed Models (<2GB)** | ~45 | Fast inference |
| **Uncensored** | ~25 | NSFW capable |

---

## 🏆 TOP MODELS BY USE CASE

### 🖼️ VISION/CAPTIONING (Best for Your Project)
| Priority | Model | Size | Speed | Quality | Use |
|----------|-------|------|-------|---------|-----|
| ⭐1 | Qwen3-VL-8B-Abliterated-Caption-it | 7.9 GB | Med | ⭐⭐⭐⭐⭐ | Detailed NSFW captions |
| ⭐2 | Qwen3-VL-8B-NSFW-Caption-v4.5 | 5 GB | Fast | ⭐⭐⭐⭐ | Quick NSFW captions |
| ⭐3 | Eris_PrimeV3.05-Vision-7B | 6.6 GB | Med | ⭐⭐⭐⭐ | RP + Vision |
| 4 | RP_Vision_7B | 8.3 GB | Med | ⭐⭐⭐⭐ | RP-focused |
| 5 | Qwen2.5-VL-7B-Instruct | 4.7 GB | Fast | ⭐⭐⭐ | General vision |
| 6 | Qwen2.5-VL-3B-Abliterated-Caption | 2.8 GB | V.Fast | ⭐⭐⭐ | Quick pass |
| 7 | LFM2-VL-1.6B | 2 GB | V.Fast | ⭐⭐ | Speed demon |
| 8 | Qwen2-VL-OCR-2B | 1 GB | Ultra | ⭐⭐⭐ | OCR/text |

### ✍️ WRITING/RP (Creative Generation)
| Priority | Model | Size | Uncensored | Quality |
|----------|-------|------|------------|---------|
| ⭐1 | Dirty-Muse-Writer-v01 | 7.6 GB | ✅ | ⭐⭐⭐⭐⭐ |
| ⭐2 | dolphin-2.9.1-yi-1.5-9b | 7.3 GB | ✅ | ⭐⭐⭐⭐ |
| ⭐3 | gemma3-27b-abliterated | 17.9 GB | ✅ | ⭐⭐⭐⭐⭐ |
| 4 | MistralRP-Noromaid-NSFW-7B | 4.1 GB | ✅ | ⭐⭐⭐⭐ |
| 5 | Dolphin3.0-Qwen2.5-3b | 2.5 GB | ✅ | ⭐⭐⭐ |
| 6 | Looking_Glass_Alice-1B | 0.9 GB | ✅ | ⭐⭐ |

### ⚡ SPEED MODELS (< 2GB, 50+ tok/s)
| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| Qwen3-0.6B | 484 MB | 100+ t/s | Ultra-fast tasks |
| DeepSeek-R1-Qwen-1.5B | 1 GB | 60+ t/s | Reasoning |
| Dolphin3.0-L3.2-1B | 743 MB | 80+ t/s | Uncensored quick |
| LFM2-1.2B | 680 MB | 70+ t/s | General |
| DeepCoder-1.5B | 1.1 GB | 55+ t/s | Code |

### 💻 CODING
| Model | Size | Quality |
|-------|------|---------|
| Qwen2.5-Vibe-Coder-14B | 8.6 GB | ⭐⭐⭐⭐⭐ |
| Qwen2.5-Coder-3B | 2.5 GB | ⭐⭐⭐⭐ |
| DeepCoder-1.5B | 1.1 GB | ⭐⭐⭐ |
| Blitzar-Coder-4B | 2.4 GB | ⭐⭐⭐ |

### 🧠 REASONING (Deep Thinking)
| Model | Size | Quality |
|-------|------|---------|
| gemma3-27b-abliterated | 17.9 GB | ⭐⭐⭐⭐⭐ |
| gemma-3-12b-abliterated | 11.7 GB | ⭐⭐⭐⭐ |
| Phi-4-reasoning-plus | 11.2 GB | ⭐⭐⭐⭐ |
| DeepSeek-R1-Distill-Qwen-14B | 8 GB | ⭐⭐⭐⭐ |

---

## 🎯 RECOMMENDED MODEL COMBINATIONS

### For Image Captioning Pipeline
```
PASS 1 (Speed): Qwen3-VL-8B-NSFW-Caption-v4.5 (5GB)
  → Quick initial captions, filter obvious rejects
  
PASS 2 (Quality): Qwen3-VL-8B-Abliterated-Caption-it (7.9GB)  
  → Detailed captions for keepers
  
PASS 3 (Verify): gemma3-27b-abliterated (17.9GB)
  → Final review of top-tier images
```

### For Dataset Curation
```
OCR/Text: Qwen2-VL-OCR-2B (1GB) - Extract text from images
Vision: Qwen3-VL-8B-NSFW-Caption (5GB) - Describe content
Tagging: Qwen3-0.6B (484MB) - Quick tag generation
Quality: gemma-3-12b-abliterated (11.7GB) - Rate quality
```

---

## ✅ INTERACTIVE TASK CHECKLIST

### Phase 1: Model Validation (TODAY)
- [x] Scan all models for corruption
- [x] Remove video models (WAN, HunyuanVideo) - Freed 50+ GB
- [x] Remove duplicate quantizations - Freed 200+ GB
- [x] Download missing mmproj files for vision models
- [x] Verify recent downloads work
- [x] Created vision_tester.py for automated testing
- [ ] **IN PROGRESS:** Test top 5 vision models with sample images
  - Load model in LM Studio, then run: `python -m ai.vision_tester <image>`
- [ ] Test top 3 writing models with prompts

### Phase 2: Benchmarking (NEXT)
- [ ] Run speed test on all models < 4GB
- [ ] Run quality test on vision models
- [ ] Compare caption detail across models
- [ ] Identify best speed/quality ratio
- [ ] Document winners per category

### Phase 3: Integration (AFTER BENCHMARKS)
- [ ] Configure captioning pipeline
- [ ] Set up model switching logic
- [ ] Create prompt templates per model
- [ ] Test end-to-end workflow
- [ ] Optimize memory usage

### Phase 4: Automation (FINAL)
- [ ] Auto-select model by task type
- [ ] Implement fallback chain
- [ ] Add quality scoring
- [ ] Create feedback loop
- [ ] Self-learning improvements

---

## 📋 AI TASK TEMPLATES

### Template 1: Image Captioning Task
```yaml
task: image_caption
model: Qwen3-VL-8B-Abliterated-Caption-it
fallback: Qwen3-VL-8B-NSFW-Caption-v4.5
prompt: |
  Describe this image in extensive detail. Include:
  - Subject description (appearance, pose, expression)
  - Setting and environment
  - Lighting and mood
  - Art style if applicable
  - Any text visible
  Be thorough and descriptive.
max_tokens: 500
temperature: 0.3
```

### Template 2: Quality Assessment Task
```yaml
task: quality_check
model: gemma3-27b-abliterated  
fallback: gemma-3-12b-abliterated
prompt: |
  Rate this image 0-15 based on:
  - Technical quality (sharpness, composition)
  - Aesthetic appeal
  - Training value for LoRA
  
  Output format:
  RATING: [0-15]
  REASON: [brief explanation]
  TAGS: [comma-separated tags]
max_tokens: 100
temperature: 0.1
```

### Template 3: Tag Generation Task
```yaml
task: generate_tags
model: Qwen3-0.6B  # Speed priority
fallback: Qwen3-4B-Instruct
prompt: |
  Generate booru-style tags for this content.
  Categories: character, setting, action, style, quality
  Format: tag1, tag2, tag3, ...
max_tokens: 100
temperature: 0.2
```

### Template 4: Writing/RP Task
```yaml
task: creative_writing
model: Dirty-Muse-Writer-v01
fallback: dolphin-2.9.1-yi-1.5-9b
prompt: |
  [USER PROMPT HERE]
  
  Write creatively with rich detail and natural dialogue.
max_tokens: 2000
temperature: 0.8
```

---

## 🔧 MODEL SWITCHING LOGIC

```python
# Recommended model selection logic
def select_model(task_type: str, quality_priority: bool = False) -> str:
    """Select best model for task"""
    
    models = {
        "caption_fast": "Qwen3-VL-8B-NSFW-Caption-v4.5",
        "caption_quality": "Qwen3-VL-8B-Abliterated-Caption-it",
        "caption_27b": "gemma3-27b-abliterated",
        "ocr": "Qwen2-VL-OCR-2B",
        "tags": "Qwen3-0.6B",
        "writing": "Dirty-Muse-Writer-v01",
        "code": "Qwen2.5-Vibe-Coder-14B",
        "reasoning": "gemma3-27b-abliterated",
    }
    
    if task_type == "caption":
        return models["caption_27b"] if quality_priority else models["caption_fast"]
    
    return models.get(task_type, models["caption_fast"])
```

---

## 📈 NEXT STEPS

1. **TODAY**: Test your top vision models on 5-10 sample images
2. **TOMORROW**: Run automated benchmarks to get speed/quality scores  
3. **THIS WEEK**: Set up captioning pipeline with model switching
4. **ONGOING**: Feed results back to improve model selection

---

## 📁 Related Files

- `scripts/ai/model_manager.py` - Model discovery and loading
- `scripts/ai/model_cleanup.py` - Cleanup and analysis
- `scripts/ai/model_repair.py` - Fix corrupt/incomplete models
- `scripts/ai/model_benchmark_suite.py` - Comprehensive benchmarking
- `scripts/ai/production_pipeline.py` - **Full production pipeline**

---

## 🏭 PRODUCTION PIPELINE SYSTEM

### Pipeline Stages
```
STAGE 1: Quick Scan (Speed Models)
├── Qwen3-0.6B, LFM2-VL-1.6B
└── Filter obvious rejects, quick classification

STAGE 2: Detailed Captioning (Vision Models)
├── Qwen3-VL-8B-Abliterated-Caption-it
├── thesby_Qwen2.5-VL-7B-NSFW-Caption-V3
└── Generate exhaustive descriptions

STAGE 3: Quality Assessment (Reasoning Models)  
├── gemma3-27b-abliterated
├── Phi-4-reasoning-plus
└── Rate 0-15, assign tiers (Gold/Silver/Bronze/Archive)

STAGE 4: Verification (Different Models)
├── dolphin-2.9.1-yi-1.5-9b
├── Ministral-3-14B-Reasoning
└── Cross-check for consistency, detect fake learning

STAGE 5: Tag Generation
└── Generate booru-style training tags
```

### Learning Verification Techniques
1. **Cross-Model Consistency** - Same image should get similar descriptions across models
2. **Temporal Consistency** - Re-testing same image later should match
3. **Semantic Overlap** - Key concepts should be shared between captions
4. **Quality Correlation** - Better images should score higher across all models
5. **Variance Detection** - Too-uniform outputs indicate template/fake responses

### Model Rotation Strategy
```python
# After every 100 images:
- Rotate to next model in each stage
- Log which models were used
- Compare results between rotations
- Detect if any model is underperforming
```

### Commands
```powershell
cd C:\Users\Admin\civitai\scripts

# Run test on sample images
python -m ai.production_pipeline --test

# Run full sweep on directory
python -m ai.production_pipeline --sweep "path/to/images" --limit 50
```

---

## 🎯 PRODUCTION CHECKLIST

### Phase 1: Infrastructure ✅
- [x] Model cleanup (freed 245GB)
- [x] Fix corrupt/incomplete models
- [x] Download missing mmproj files
- [x] Create benchmark suite
- [x] Create production pipeline

### Phase 2: Benchmarking (CURRENT)
- [ ] Free RAM (close apps, target <20GB)
- [ ] Load vision model in LM Studio
- [ ] Run benchmarks on top 5 vision models
- [ ] Generate speed/quality rankings
- [ ] Select optimal models per stage

### Phase 3: Pipeline Testing
- [ ] Test pipeline on 10 sample images
- [ ] Verify cross-model consistency
- [ ] Check learning verification works
- [ ] Fine-tune prompts for better output

### Phase 4: Production Run
- [ ] Run full sweep on training dataset
- [ ] Review quality tier distribution
- [ ] Export captions for training
- [ ] Generate training tags
- [ ] Create dataset manifest

### Phase 5: LoRA Training
- [ ] Filter to Gold/Silver tier images
- [ ] Prepare captions in Kohya format
- [ ] Configure training parameters
- [ ] Run training
- [ ] Evaluate results

---

## 📊 MODEL USAGE BY STAGE

| Stage | Models | RAM Needed | Purpose |
|-------|--------|------------|---------|
| Quick Scan | Qwen3-0.6B, LFM2-1.6B | ~2GB | Fast filtering |
| Caption | Qwen3-VL-8B, thesby-7B | ~10GB | Detailed descriptions |
| Quality | gemma3-27b | ~20GB | Quality scoring |
| Verify | dolphin-9b | ~8GB | Cross-check |
| Tags | Qwen3-VL-8B | ~10GB | Training tags |

**Strategy:** Load one model at a time, unload before loading next!

---

*Last updated: December 3, 2025 3:15 PM*
