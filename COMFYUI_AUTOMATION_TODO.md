# 🎯 ComfyUI Automation - Complete Action Plan

> **Objective**: Fully automated image generation pipeline using your training data, prompts, and styles

---

## 📊 Current Status

### ✅ Completed
- [x] ComfyUI installed and running
- [x] 6 base workflows created and tested
- [x] Models linked (checkpoints, LoRAs, VAEs)
- [x] Playwright automation verified
- [x] Prompts extracted from `image_data.md` (43 entries)
- [x] Negative prompts configured
- [x] Embeddings linked (EasyNegative, bad-hands-5, ng_deepnegative)
- [x] Style templates extracted (tribal, anime, realistic, general)
- [x] Batch generation script working
- [x] 8 workflows total (6 base + 2 style-specific)

### ⏳ In Progress
- [x] ComfyUI Automation API (port 8213) ✅ CREATED
- [x] Style templates (tribal, anime, realistic, fantasy, western) ✅
- [x] Generation presets (fast, balanced, quality, maximum) ✅
- [x] Workflow builder (txt2img with LoRA support) ✅
- [ ] Training/comparison pipeline
- [ ] Quality validation system
- [ ] Reference image comparison

---

## 🔄 Phase 1: Data Extraction & Integration

### Task 1.1: Extract User Prompts Database
**Status**: `[ ] PENDING`
- Parse `image_data.md` (181 entries)
- Extract prompt templates
- Extract negative prompt patterns
- Extract generation settings (steps, CFG, sampler)
- Store in structured JSON format

**Files to create**:
```
c:\Users\Admin\civitai\data\
├── user_prompts.json          # All positive prompts
├── negative_prompts.json      # All negative prompts  
├── style_templates.json       # Categorized styles
└── generation_settings.json   # Steps, CFG, samplers
```

### Task 1.2: Categorize Styles from Training Data
**Status**: `[ ] PENDING`
- Tribal/Face Paint styles (TRIBAL-BEAUTY)
- Anime/Illustration styles (Illustrious)
- Realistic Photo styles (CyberRealistic)
- Fantasy/Mystical styles
- Character-based styles

### Task 1.3: Link Embeddings
**Status**: `[ ] PENDING`
- Copy embeddings to ComfyUI folder:
  - `EasyNegative.safetensors`
  - `bad-hands-5.safetensors`
  - `ng_deepnegative_v1_75t.safetensors`

---

## 🔧 Phase 2: Workflow Enhancement

### Task 2.1: Create Style-Specific Workflows
**Status**: `[ ] PENDING`

| Workflow | Style | Model | Status |
|----------|-------|-------|--------|
| `Tribal_FacePaint.json` | Tribal Beauty | Realistic | [ ] |
| `Anime_Illustrious.json` | Anime/Manga | NoobAI-XL | [ ] |
| `Fantasy_Mystical.json` | Fantasy | Pony SDXL | [ ] |
| `Realistic_Portrait.json` | Photorealistic | CyberRealistic | [ ] |
| `Character_Cosplay.json` | Character | Pony SDXL | [ ] |

### Task 2.2: Add Embedding Support to Workflows
**Status**: `[ ] PENDING`
- Add EmbeddingLoader nodes
- Configure negative prompt embeddings
- Test embedding effectiveness

### Task 2.3: Add Quality Control Nodes
**Status**: `[ ] PENDING`
- Add upscaling nodes
- Add face enhancement (ADetailer if available)
- Add comparison output nodes

---

## 🤖 Phase 3: Automation Pipeline

### Task 3.1: Prompt Randomizer System
**Status**: `[ ] PENDING`
- Create prompt template system
- Random selection from user database
- Style mixing capability

### Task 3.2: Batch Generation Pipeline
**Status**: `[ ] PENDING`
- Load multiple prompts automatically
- Generate variations
- Save with metadata
- Compare against reference images

### Task 3.3: Quality Validation System
**Status**: `[ ] PENDING`
- Compare generated vs reference images
- Calculate similarity scores
- Flag low-quality outputs
- Auto-regenerate failures

---

## 📈 Phase 4: Training Integration

### Task 4.1: Dataset Preparation Workflow
**Status**: `[ ] PENDING`
- Auto-tag images with WD14
- Generate caption files
- Organize for Kohya training

### Task 4.2: LoRA Training Pipeline
**Status**: `[ ] PENDING`
- Connect to anime-lora-pipeline
- Automated training triggers
- Model evaluation workflow

### Task 4.3: Continuous Improvement Loop
**Status**: `[ ] PENDING`
- Generate → Evaluate → Train → Improve
- Track quality metrics over time
- Auto-select best outputs for training

---

## 📁 File Structure Required

```
G:\Github\ComfyUI\
├── user\default\workflows\     # Active workflows
│   ├── 01_Pony_SDXL.json
│   ├── 02_Realistic_Photo.json
│   ├── 03_NoobAI_Anime.json
│   ├── 04_WD14_Tagger.json
│   ├── 05_Image_to_Image.json
│   ├── 06_Pony_with_LoRA.json
│   ├── 07_Tribal_FacePaint.json    ← NEW
│   ├── 08_Anime_Illustrious.json   ← NEW
│   ├── 09_Fantasy_Mystical.json    ← NEW
│   └── 10_Batch_Training.json      ← NEW
├── input\                      # Source images
│   └── training_samples\       # Reference images
├── output\                     # Generated images
│   ├── tribal\
│   ├── anime\
│   ├── realistic\
│   └── comparison\
└── models\embeddings\          # Linked embeddings
```

```
c:\Users\Admin\civitai\
├── data\
│   ├── user_prompts.json
│   ├── negative_prompts.json
│   ├── style_templates.json
│   └── tags.db (existing)
├── scripts\
│   ├── extract_prompts.py      ← NEW
│   ├── generate_batch.py       ← NEW
│   ├── compare_images.py       ← NEW
│   └── training_prep.py        ← NEW
└── output\
    └── quality_reports\
```

---

## 🚀 Immediate Next Steps

### Step 1: Extract Prompts (NOW)
```bash
python scripts/extract_prompts.py
```

### Step 2: Link Embeddings (NOW)
```bash
Copy embeddings to G:\Github\ComfyUI\models\embeddings\
```

### Step 3: Create Style Workflows (NOW)
```bash
Create Tribal, Anime, Fantasy workflows with user data
```

### Step 4: Test Full Pipeline
```bash
Run batch generation with user prompts
Compare output quality
```

---

## 📋 User Style Summary (from image_data.md)

### Primary Styles Detected:
1. **Tribal/Face Paint** - TRIBAL-BEAUTY LoRA, face paint, war paint
2. **Anime Illustrious** - PowerPuffMixLora, Face_Enhancer, detailed illustration
3. **Realistic Portrait** - photorealistic, 8K, detailed skin
4. **Fantasy/Mystical** - ethereal, magical settings
5. **Character Cosplay** - specific character references

### Common Positive Elements:
- `masterpiece, best quality, absurdres, amazing quality, 8K`
- `realistic skin, realistic textures, detailed skin`
- `HDR, raytracing, pathtracing, 3d render`
- `focused subject, sharp focus`

### Common Negative Elements:
- `lowres, bad anatomy, bad proportions`
- `deformed hands, extra fingers, missing fingers`
- `worst quality, low quality, blurry`
- `watermark, text, signature`
- `cartoon, anime` (for realistic styles)

---

## 🎯 Success Criteria

| Metric | Target | Current |
|--------|--------|---------|
| Workflow Count | 10+ | 6 |
| Prompts Integrated | 181 | 0 |
| Embeddings Loaded | 3 | 0 |
| Style Templates | 5+ | 0 |
| Automation Scripts | 4 | 2 |
| Quality Validation | Yes | No |
| Training Pipeline | Yes | No |

---

*Last Updated: December 4, 2025*
