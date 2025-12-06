# 📋 Correct Vision Models to Download

## ❌ WRONG Models Downloaded (Text-only, NOT vision):
- `amoral-gemma3-12b-vision-i1` - Wrong quant/version
- `qwen3-vl-8b-nsfw-caption-v4.5` - Wrong quant/version  
- `qwen2.5-vl-7b-abliterated-caption-it` - Wrong quant/version
- `thesby_qwen2.5-vl-7b-nsfw-caption-v3` - Wrong quant/version

## ✅ CORRECT Vision Models to Download:

### 1. qwen3-vl-8b-nsfw-caption-v4.5
**Search in LM Studio:** `Sail2Dream/Qwen3-VL-8B-NSFW-Caption-V4.5`
**Correct file:** `qwen3-vl-8b-nsfw-caption-v4.5-q4_k_m.gguf`
**Size:** ~5.0 GB
**Expected Score:** 90-95

### 2. amoral-gemma3-12b-vision-i1  
**Search in LM Studio:** `mradermacher/amoral-gemma3-12B-vision-i1`
**Correct file:** `amoral-gemma3-12B-vision.i1-Q4_K_S.gguf`
**Size:** ~6.9 GB
**Expected Score:** 85-90

### 3. qwen2.5-vl-7b-abliterated-caption-it
**Search in LM Studio:** `mradermacher/qwen2.5-VL-7B-Abliterated-Caption-it`
**Correct file:** `Qwen2.5-VL-7B-Abliterated-Caption-it.Q4_K_S.gguf`
**Size:** ~5.8 GB
**Expected Score:** 75-80

## 🔍 How to Identify Vision Models:
1. Look for "VL" (Vision-Language) in the name
2. Check the model card - must mention "vision" or "multimodal"
3. Avoid models without vision components

## ⚠️ Current Working Model:
**lfm2-vl-1.6b** (Score: 49) - Working but limited detail

## 📥 Download Instructions:
1. Open LM Studio
2. Click "Discover/Search"
3. Search for the exact names above
4. Download the Q4_K_S or Q4_K_M quants (not Q6_K_L)
5. Load and test

## 🎯 After Download:
Run: `python -m training.test_real_vision_models`

Expected results after correct downloads:
1. qwen3-vl-8b-nsfw: 90+ score
2. amoral-gemma3-12b: 85+ score  
3. qwen2.5-vl-7b-abliterated: 75+ score
