# 🔬 Vision Model Benchmark Status Report

**Last Updated:** 2025-12-03 19:49  
**Status:** ⏸️ Testing Paused - Issues Identified  
**Next Action:** Reboot PC, restart LM Studio, properly load models

---

## 📊 Current Rankings

| Rank | Model | Score | Time | Status |
|:----:|-------|:-----:|:----:|--------|
| 🥇 | **lfm2-vl-1.6b** | 49-65 | 2.6-8s | ✅ WORKING |
| 🥈 | llava:13b (Ollama) | 59 | 11.3s | ✅ WORKING |
| 🥉 | minicpm-v (Ollama) | 54 | 12.2s | ✅ WORKING |
| 4 | qwen2-vl-7b-captioner-relaxed | 18 | 9.4s | ⚠️ Low score |
| 5 | qwen3-vl-8b-abliterated | 10 | 50.7s | ⚠️ Very slow |

---

## ❌ Issues Identified

### 1. Wrong Model Versions Downloaded
**Problem:** Downloaded models return "completely black" for images  
**Cause:** These are TEXT-ONLY versions, not VISION models  
**Affected Models:**
- `amoral-gemma3-12b-vision-i1`
- `qwen2.5-vl-7b-abliterated-caption-it`
- `thesby_qwen2.5-vl-7b-nsfw-caption-v3`

**Solution:** Download correct vision-capable versions with multimodal components

### 2. LM Studio Context Too High
**Problem:** 262k context causes performance issues  
**Solution:** Lower to 25k-40k in LM Studio settings

### 3. Too Many Models Loaded
**Problem:** Loading 3-4 models causes crashes  
**Solution:** Load maximum 2 models at a time

### 4. API Connection Crashes
**Problem:** Connection pool errors during inference  
**Solution:** Restart LM Studio, load one model, test, then add second

---

## ✅ Working Models (Use These)

### lfm2-vl-1.6b (Recommended)
```
Size: 2.1GB
Score: 49-65/100
Speed: 2.6-8s per image
Details: cup_size, ethnicity, nipple, skin, hair, pose
Status: ✅ Confirmed working
```

### llava:13b (Ollama Backup)
```
Size: 8.0GB
Score: 59/100
Speed: 11.3s per image
Details: ethnicity, nipple, butt_shape, skin
Status: ✅ Confirmed working
```

---

## 🎯 Models to Try After Reboot

### High Priority (Best Expected):
1. **qwen3-vl-8b-nsfw-caption-v4.5** (5.0GB)
   - Expected Score: 90-95
   - Needs proper loading

### Medium Priority:
2. **amoral-gemma3-12b-vision-i1** (6.9GB)
   - Expected Score: 85-90
   - May need correct version

---

## 📋 After Reboot Checklist

1. ☐ Restart LM Studio
2. ☐ Go to Settings > Context Length > Set to 40k
3. ☐ Load ONLY `lfm2-vl-1.6b` first
4. ☐ Wait for green "READY" status
5. ☐ Run test: `python -m training.minimal_test`
6. ☐ If working, try loading `qwen3-vl-8b-nsfw-caption-v4.5`
7. ☐ Test again

---

## 🛠️ Test Scripts Available

| Script | Purpose | Command |
|--------|---------|---------|
| minimal_test.py | Quick API check + basic test | `python -m training.minimal_test` |
| test_two_models.py | Test 2 models side by side | `python -m training.test_two_models` |
| quick_model_test.py | Fast test top 3 models | `python -m training.quick_model_test` |

**Location:** `C:\Users\Admin\civitai\scripts\training\`

---

## 📁 Related Files

- **Reports:**
  - `C:\Users\Admin\civitai\docs\FINAL_MODEL_BENCHMARK_REPORT.md`
  - `C:\Users\Admin\civitai\docs\CORRECT_VISION_MODELS_TO_DOWNLOAD.md`
  
- **Logs:**
  - `C:\Users\Admin\civitai\logs\quick_model_test.json`
  - `C:\Users\Admin\civitai\logs\vision_models_test.json`

---

## 🎯 Goal

Find the best vision model for **ultra-detailed NSFW tag extraction** with:
- Cup size, measurements (bust-waist-hips)
- Breast shape, nipple type, areola details
- Butt shape and size
- Ethnicity, hair, skin tone
- Pose, clothing, setting
- 50+ tags per image

---

## 💡 Key Learnings

1. **"VL" in name doesn't guarantee vision** - Check for multimodal components
2. **Q6_K_L quants may be broken** - Use Q4_K_S or Q4_K_M
3. **Context 262k is too high** - Use 25k-40k for vision
4. **Max 2 models loaded** - Prevents crashes
5. **lfm2-vl-1.6b is reliable** - Use as baseline

---

*Report will be updated after reboot and successful testing*
