# 🎨 ComfyUI User Guide
> **Complete guide for non-coders to generate and caption images**

---

## 📍 Quick Reference

| Item | Location/Value |
|------|----------------|
| **ComfyUI Location** | `G:\Github\ComfyUI` |
| **Web Interface** | http://localhost:8188 |
| **Models Folder** | `C:\Users\Admin\civitai\checkpoints` |
| **Output Folder** | `G:\Github\ComfyUI\output` |
| **Input Folder** | `G:\Github\ComfyUI\input` |

---

## 🚀 Starting ComfyUI

### Option 1: Double-Click Start (Recommended)
1. Open File Explorer
2. Navigate to `G:\Github\ComfyUI`
3. Double-click `start_comfyui.bat` (we'll create this below)

### Option 2: PowerShell Command
```powershell
cd G:\Github\ComfyUI
python main.py --listen 0.0.0.0 --port 8188
```

### Option 3: Using the Dashboard API
```powershell
cd C:\Users\Admin\civitai\scripts
python -c "import webbrowser; webbrowser.open('http://localhost:8188')"
```

---

## 📦 Available Models

### Checkpoints (Base Models)
| Model | Type | Size | Best For |
|-------|------|------|----------|
| **ponyDiffusionV6XL** | SDXL | 6.5 GB | Anime/Stylized |
| **NoobAI-XL** | SDXL | 6.5 GB | General/Anime |
| **CyberRealistic** | SD1.5 | 2 GB | Realistic Photos |
| **RealisticVisionV5** | SD1.5 | 2 GB | Realistic Photos |
| **v1-5-pruned** | SD1.5 | 4 GB | General Purpose |

### Custom Nodes Installed
| Node | Purpose |
|------|---------|
| **ComfyUI-Manager** | Install/update nodes easily |
| **ComfyUI-WD14-Tagger** | Auto-tag images for training |
| **ComfyUI-Impact-Pack** | Face detection, upscaling |
| **ComfyUI-Custom-Scripts** | Extra utilities |
| **rgthree-comfy** | Better workflow nodes |

---

## 🖼️ How to Generate Images

### Step 1: Open ComfyUI
1. Start ComfyUI (see above)
2. Open browser to http://localhost:8188

### Step 2: Load a Workflow
1. Click **Load** button (top menu)
2. Navigate to `G:\Github\ComfyUI\user_workflows`
3. Select `basic_image_generation.json`

### Step 3: Configure Your Generation
1. **Checkpoint Node**: Select your model
2. **Positive Prompt**: Describe what you want
3. **Negative Prompt**: Describe what to avoid
4. **Empty Latent Image**: Set resolution (1024x1024 for SDXL)
5. **KSampler**: Adjust steps (20-30) and CFG (5-8)

### Step 4: Generate!
1. Click **Queue Prompt** button
2. Wait for generation (10-60 seconds)
3. Image appears in Save Image node
4. Find output in `G:\Github\ComfyUI\output`

---

## 🏷️ How to Auto-Tag Images

### Method 1: ComfyUI WD14 Tagger
1. Load `auto_caption_wd14.json` workflow
2. In **Load Image** node, select your image
3. Click **Queue Prompt**
4. Tags appear in **Show Text** node

### Method 2: Command Line (Batch)
```powershell
cd C:\Users\Admin\civitai\scripts
python caption_image.py "C:\path\to\your\images" --batch
```

This creates `.txt` files next to each image with tags.

---

## 🔧 Workflow Nodes Explained

### Core Nodes
```
┌─────────────────┐
│ CheckpointLoader│ ──▶ Loads the AI model
└─────────────────┘

┌─────────────────┐
│ CLIPTextEncode  │ ──▶ Converts text to AI-readable format
└─────────────────┘

┌─────────────────┐
│ EmptyLatentImage│ ──▶ Creates blank canvas at specified size
└─────────────────┘

┌─────────────────┐
│ KSampler        │ ──▶ The actual image generation process
└─────────────────┘

┌─────────────────┐
│ VAEDecode       │ ──▶ Converts AI output to viewable image
└─────────────────┘

┌─────────────────┐
│ SaveImage       │ ──▶ Saves the final image to disk
└─────────────────┘
```

### Tagging Nodes
```
┌─────────────────┐
│ LoadImage       │ ──▶ Load an image from input folder
└─────────────────┘

┌─────────────────┐
│ WD14Tagger      │ ──▶ Analyze image and generate tags
└─────────────────┘

┌─────────────────┐
│ ShowText        │ ──▶ Display the generated tags
└─────────────────┘
```

---

## ⚙️ Recommended Settings

### For Anime/Stylized (Pony/NoobAI)
```
Resolution: 1024 x 1024
Steps: 25-30
CFG Scale: 6-7
Sampler: euler_ancestral
Scheduler: normal
```

### For Realistic (CyberRealistic/RealisticVision)
```
Resolution: 512 x 768 (portrait) or 768 x 512 (landscape)
Steps: 20-25
CFG Scale: 7-8
Sampler: dpmpp_2m
Scheduler: karras
```

---

## 📝 Prompt Writing Tips

### Good Prompts Include:
- **Subject**: "1girl", "a man", "landscape"
- **Quality Tags**: "masterpiece", "best quality", "highly detailed"
- **Style**: "anime style", "photorealistic", "oil painting"
- **Details**: "blue eyes", "long hair", "sunset lighting"

### Example Positive Prompt:
```
masterpiece, best quality, 1girl, solo, long blonde hair, 
blue eyes, smile, white dress, standing in flower garden, 
soft lighting, detailed background
```

### Example Negative Prompt:
```
bad quality, worst quality, blurry, ugly, deformed, 
extra fingers, extra limbs, bad anatomy, watermark, text
```

---

## 🔄 Your Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. GENERATE IMAGES                                          │
│     ComfyUI → Load checkpoint → Write prompt → Generate      │
├─────────────────────────────────────────────────────────────┤
│  2. AUTO-TAG FOR TRAINING                                    │
│     Load image → WD14 Tagger → Copy tags to .txt file        │
│     OR: python caption_image.py folder --batch               │
├─────────────────────────────────────────────────────────────┤
│  3. TRAIN LORA (Future)                                      │
│     Use Kohya_ss with image + caption pairs                  │
├─────────────────────────────────────────────────────────────┤
│  4. USE YOUR LORA                                            │
│     Load LoRA node in ComfyUI → Apply to generation          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting

### ComfyUI Won't Start
```powershell
# Check if port is in use
netstat -ano | findstr :8188

# Kill existing process if needed
taskkill /PID <process_id> /F

# Restart ComfyUI
cd G:\Github\ComfyUI
python main.py --port 8188
```

### Model Not Loading
- Check GPU memory (need ~8GB for SD1.5, ~12GB for SDXL)
- Close other GPU-heavy applications
- Try a smaller model first

### WD14 Tagger Error
- First run downloads ~400MB model
- Wait for download to complete
- Check internet connection

### Out of Memory
- Reduce image resolution
- Use SD1.5 models instead of SDXL
- Close Chrome/other memory-heavy apps

---

## 📁 Folder Structure

```
G:\Github\ComfyUI\
├── input/              ← Put images here for tagging
├── output/             ← Generated images saved here
├── models/
│   ├── checkpoints/    ← Base models
│   ├── loras/          ← LoRA models
│   └── vae/            ← VAE models
├── custom_nodes/       ← Extensions
└── user_workflows/     ← Your saved workflows

C:\Users\Admin\civitai\
├── checkpoints/        ← Additional models (linked)
├── loras/              ← Your trained LoRAs
├── scripts/            ← Automation scripts
└── gallery/            ← Rated images
```

---

## 🎯 Quick Commands Reference

```powershell
# Start ComfyUI
cd G:\Github\ComfyUI
python main.py --listen 0.0.0.0 --port 8188

# Caption single image
cd C:\Users\Admin\civitai\scripts
python caption_image.py "path\to\image.png"

# Batch caption folder
python caption_image.py "path\to\folder" --batch

# Test ComfyUI connection
python test_comfyui.py

# Test WD14 tagger
python test_wd14_tagger.py
```

---

## 📚 Additional Resources

- [ComfyUI Documentation](https://docs.comfy.org/)
- [Civitai Model Downloads](https://civitai.com/)
- [Prompt Engineering Guide](https://stable-diffusion-art.com/prompt-guide/)

---

*Last updated: December 4, 2025*
