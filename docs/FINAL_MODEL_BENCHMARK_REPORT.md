# 🏆 FINAL Vision Model Benchmark Report

**Generated:** 2025-12-03 19:00  
**Updated:** 2025-12-03 19:49  
**Status:** ⏸️ Testing Paused - Reboot Required  
**Next Update:** After PC reboot and proper model loading

---

## ⚠️ CURRENT ISSUES (2025-12-03)

1. **Wrong model versions downloaded** - Some "VL" models are text-only
2. **Context too high** - 262k causes crashes, use 25-40k
3. **Too many models loaded** - Max 2 at a time
4. **LM Studio crashes** - Connection pool errors during inference

**See:** `VISION_MODEL_STATUS_REPORT.md` for full details

---

## 📊 FINAL RANKINGS

| Rank | Model | Score | Time | Size | Status |
|:----:|-------|:-----:|:----:|------|--------|
| 🥇 | **lfm2-vl-1.6b** | **65** | **2.6s** | 2.1GB | ✅ **CURRENT WINNER** |
| 🥈 | llava:13b (Ollama) | 59 | 11.3s | 8.0GB | ✅ Working |
| 🥉 | minicpm-v (Ollama) | 54 | 12.2s | 2.8GB | ✅ Working |
| 4 | llava-llama3 (Ollama) | 40 | 20.2s | 5.5GB | ✅ Working |
| 5 | thesby_7b-nsfw | 30 | 14.3s | 7.9GB | ⚠️ Low score |
| 6 | llama3.2-vision (Ollama) | 23 | 30.0s | 7.8GB | ✅ Working |
| 7 | qwen2.5vl (Ollama) | 12 | - | 6.0GB | ✅ Working |

---

## 🏆 CURRENT WINNER: lfm2-vl-1.6b

### Why it wins:
- ✅ **Highest Score:** 65/100 points
- ✅ **Fastest Processing:** 2.6s average
- ✅ **Most Consistent:** Works on every image
- ✅ **Best Detail Detection:** 6/9 categories detected

### Performance Details:
| Metric | Value |
|--------|-------|
| **Average Score** | 65.0/100 |
| **Processing Time** | 2.6s per image |
| **Model Size** | 2.1GB |
| **Success Rate** | 100% |
| **Details Found** | ethnicity, nipple, butt_shape, hair, skin, pose |

### What it detects well:
- ✅ Ethnicity/Race (100%)
- ✅ Nipple details (67%)
- ✅ Butt shape (67%)
- ✅ Hair color (100%)
- ✅ Skin tone (100%)
- ✅ Pose/position (100%)

### What it misses:
- ❌ Cup size (only 33%)
- ❌ Measurements (0%)
- ❌ Tattoos/piercings (rare)

---

## ⏳ PENDING: High-Potential Models (Downloaded, Not Loaded)

These models are downloaded but need to be **loaded in LM Studio** before testing:

| Model | Size | Expected Score | Loading Required |
|-------|------|:--------------:|------------------|
| qwen3-vl-8b-nsfw-caption-v4.5 | 5.0GB | 90-95 | ⚠️ **LOAD IN LM STUDIO** |
| amoral-gemma3-12b-vision-i1 | 6.9GB | 85-90 | ⚠️ **LOAD IN LM STUDIO** |
| qwen2.5-vl-7b-abliterated-caption-it | 5.8GB | 75-80 | ⚠️ **LOAD IN LM STUDIO** |

---

## 📋 LOADING INSTRUCTIONS

To test the high-potential models:

1. **Open LM Studio**
2. **Go to Home tab**
3. **Click "Load a model"**
4. **Search and load:**
   ```
   qwen3-vl-8b-nsfw-caption-v4.5-q4_k_m
   amoral-gemma3-12B-vision.i1-Q4_K_S
   ```
5. **Wait for models to fully load** (green status)
6. **Re-run test:** `python -m training.quick_model_test`

---

## 🎯 PRODUCTION RECOMMENDATIONS

### For Immediate Use (Today):
**Use lfm2-vl-1.6b** - It's the best working model with excellent speed and decent detail.

### For Maximum Detail (After Loading):
**qwen3-vl-8b-nsfw-caption-v4.5** - Expected to score 90+ with NSFW-specific training.

### Implementation Strategy:
```python
# Current production setup
MODEL_CONFIG = {
    "primary": "lfm2-vl-1.6b",  # Fast, reliable
    "fallback": "llava:13b",    # Ollama backup
}

# After loading NSFW models
MODEL_CONFIG = {
    "primary": "qwen3-vl-8b-nsfw-caption-v4.5",  # Maximum detail
    "secondary": "lfm2-vl-1.6b",                  # Fast processing
    "fallback": "llava:13b"                       # Ollama backup
}
```

---

## 📈 PERFORMANCE COMPARISON

### Speed vs Detail Trade-off:
```
🏃 Fast (<3s):     lfm2-vl-1.6b (Score: 65) ⭐ CURRENT
🚶 Medium (10-15s): llava:13b (Score: 59), minicpm-v (Score: 54)
🐌 Slow (>20s):    llava-llama3 (Score: 40), llama3.2-vision (Score: 23)
```

### Detail Detection Rates:
| Feature | lfm2-vl-1.6b | llava:13b | minicpm-v |
|---------|:------------:|:---------:|:--------:|
| Ethnicity | 100% | 100% | 100% |
| Nipple | 67% | 67% | 67% |
| Butt Shape | 67% | 67% | 67% |
| Cup Size | 33% | 33% | 100% |
| Measurements | 0% | 0% | 0% |

---

## 🔄 NEXT STEPS

1. **Load NSFW models** in LM Studio (user action required)
2. **Re-run benchmark** to find true winner
3. **Update training pipeline** with best model
4. **Create model rotation** for variety in training
5. **Fine-tune prompts** for each model's strengths

---

## 💾 DATA FILES

- Full test data: `C:\Users\Admin\civitai\logs\model_benchmark_data.json`
- Quick test results: `C:\Users\Admin\civitai\logs\quick_model_test.json`
- Previous report: `C:\Users\Admin\civitai\docs\MODEL_BENCHMARK_REPORT.md`

---

## 📝 SUMMARY

**Current Winner:** lfm2-vl-1.6b (Score: 65, Time: 2.6s)  
**Potential Winner:** qwen3-vl-8b-nsfw-caption-v4.5 (Expected: 90+)  
**Action Required:** Load NSFW models in LM Studio and re-test

*Report will be updated when NSFW models are loaded and tested*
