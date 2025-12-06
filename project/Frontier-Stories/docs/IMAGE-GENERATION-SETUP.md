# Image Generation Setup Guide
## Seamless A1111/ComfyUI Integration for Frontier-Stories

This guide explains how to set up Automatic1111 or ComfyUI for generating portraits with sexy Native American model outfits.

---

## Quick Start

### Option 1: Automatic1111 (Recommended for Beginners)

1. **Install Automatic1111/Forge**
   ```bash
   # Clone the repo
   git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
   cd stable-diffusion-webui
   
   # Or use Forge (faster, recommended)
   git clone https://github.com/lllyasviel/stable-diffusion-webui-forge
   cd stable-diffusion-webui-forge
   ```

2. **Start with API enabled**
   ```bash
   # Windows
   webui-user.bat --api --listen
   
   # Linux/Mac
   ./webui.sh --api --listen
   ```

3. **Verify it's running**
   - Web UI: http://localhost:7860
   - API: http://localhost:7860/sdapi/v1/options

### Option 2: ComfyUI (Recommended for Power Users)

1. **Install ComfyUI**
   ```bash
   git clone https://github.com/comfyanonymous/ComfyUI
   cd ComfyUI
   pip install -r requirements.txt
   ```

2. **Start ComfyUI**
   ```bash
   python main.py --listen
   ```

3. **Verify it's running**
   - Web UI: http://localhost:8188
   - API: http://localhost:8188/system_stats

---

## Recommended Models for Native American Portraits

### Realistic Models (Best Results)
- **Realistic Vision V6** - Excellent for photorealistic portraits
- **MajicMix Realistic** - Great skin textures
- **CyberRealistic** - Modern, high-detail portraits
- **Beautiful Realistic Asians** - Good ethnic features

### NSFW-Capable Models
- **Pony Diffusion V6** - Excellent for stylized adult content
- **Anything V5** - Anime-style with adult capabilities
- **AbyssOrangeMix3** - Balanced realism with uncensored output

### Download from:
- [CivitAI](https://civitai.com) - Main source
- [Hugging Face](https://huggingface.co) - Alternative source

---

## Configuration

### Environment Variables

Add to your `.env` file:
```env
# Image Generation Backend
A1111_URL=http://host.docker.internal:7860
COMFYUI_URL=http://host.docker.internal:8188
IMAGE_GEN_BACKEND=a1111
```

### Optimal Settings for Portraits

| Setting | Recommended Value | Notes |
|---------|------------------|-------|
| Steps | 30-40 | Higher = more detail |
| CFG Scale | 6-8 | Lower for creativity, higher for prompt adherence |
| Sampler | DPM++ 2M Karras | Best balance of speed/quality |
| Width | 768 | Portrait aspect ratio |
| Height | 1024 | Portrait aspect ratio |
| Restore Faces | On | Improves facial details |
| Hi-Res Fix | Optional | Enable for 1.5x upscale |

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontier-Stories                          │
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │ Portrait     │   │ Image Gen    │   │ Model          │  │
│  │ Gallery      │   │ Settings     │   │ Selector       │  │
│  └──────┬───────┘   └──────┬───────┘   └───────┬────────┘  │
│         │                  │                   │            │
│         ▼                  ▼                   ▼            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              aiService.generatePortrait()            │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Functions Server (Docker :3001)                 │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         /generate-actor-portrait endpoint            │   │
│  │                                                       │   │
│  │  1. Fetch actor metadata (sexy outfit)               │   │
│  │  2. Build Stable Diffusion prompt                    │   │
│  │  3. Call A1111/ComfyUI API                           │   │
│  │  4. Save generated image                             │   │
│  │  5. Update database                                  │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
┌─────────────────────┐          ┌─────────────────────┐
│   Automatic1111     │    OR    │      ComfyUI        │
│   (port 7860)       │          │    (port 8188)      │
│                     │          │                     │
│  ┌───────────────┐  │          │  ┌───────────────┐  │
│  │ SD Model      │  │          │  │ Workflow      │  │
│  │ + LoRAs       │  │          │  │ + Custom      │  │
│  │ + VAE         │  │          │  │   Nodes       │  │
│  └───────────────┘  │          │  └───────────────┘  │
└─────────────────────┘          └─────────────────────┘
```

---

## API Endpoints

The functions server exposes these endpoints for image generation:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/image-gen/status` | GET | Check A1111/ComfyUI connection |
| `/image-gen/models` | GET | List available SD models |
| `/image-gen/samplers` | GET | List available samplers |
| `/image-gen/options` | GET | Get current settings |
| `/image-gen/set-model` | POST | Change active model |
| `/image-gen/progress` | GET | Get generation progress |
| `/generate-actor-portrait` | POST | Generate portrait image |

---

## Troubleshooting

### A1111 Not Connecting
1. Ensure A1111 is started with `--api` flag
2. Check firewall allows port 7860
3. Use `--listen` flag for external access
4. Verify URL in docker-compose environment

### ComfyUI Not Connecting  
1. Start with `--listen` flag
2. Check port 8188 is accessible
3. Ensure ComfyUI has API enabled (default)

### Images Not Generating
1. Check model is loaded in A1111/ComfyUI
2. Verify enough VRAM available
3. Check functions server logs: `docker logs frontier-stories-functions`

### Low Quality Images
1. Increase steps to 30-40
2. Use a better model (Realistic Vision V6)
3. Enable Restore Faces
4. Enable Hi-Res Fix for larger images

---

## Testing the Integration

```bash
# Check functions server is running
curl http://localhost:3001/health

# Check image gen backend status
curl http://localhost:3001/image-gen/status

# Test portrait generation
curl -X POST http://localhost:3001/generate-actor-portrait \
  -H "Content-Type: application/json" \
  -d '{"actorId":"test","fullName":"Test Actor","role":"Model"}'
```

---

## Performance Tips

1. **Use SDXL models** for best quality (requires 8GB+ VRAM)
2. **Enable xformers** for faster generation
3. **Use bf16/fp16** precision for memory efficiency
4. **Batch generation** processes multiple images efficiently
5. **Use Forge** instead of base A1111 for 30-50% speed improvement
