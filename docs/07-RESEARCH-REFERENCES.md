# Research & References

## Overview

Curated list of research papers, tools, and resources for the Automated AI Image Studio project.

---

## Research Papers

### Human Feedback & RLHF

| Paper | Topic | Link |
|-------|-------|------|
| **Rich Human Feedback for T2I** | Multi-dimensional feedback for image generation | [arXiv:2312.10240](https://arxiv.org/abs/2312.10240) |
| **RLHF for Diffusion Models** | Reinforcement learning from human feedback | [HuggingFace Blog](https://huggingface.co/blog/rlhf) |
| **Human-in-the-Loop ML** | Interactive feedback systems | [Stanford HAI](https://hai.stanford.edu/news/humans-loop-design-interactive-ai-systems) |

### LoRA & Fine-Tuning

| Paper | Topic | Link |
|-------|-------|------|
| **LoRA Survey** | Comprehensive LoRA techniques | [Springer](https://link.springer.com/article/10.1007/s11704-024-40663-9) |
| **DreamBooth + LoRA** | Combined training approach | [HuggingFace PEFT](https://huggingface.co/docs/peft/main/en/task_guides/dreambooth_lora) |
| **In-Context LoRA** | Task-agnostic LoRA training | [arXiv:2410.23775](https://arxiv.org/html/2410.23775v1) |

### Active Learning & Dataset Curation

| Paper | Topic | Link |
|-------|-------|------|
| **Active Learning for Image Classification** | Iterative sample selection | [arXiv:2505.06825](https://arxiv.org/html/2505.06825) |
| **Data Curation for CV** | Best practices | [Encord Blog](https://encord.com/blog/data-curation-for-computer-vision/) |
| **LLM-Driven Rating Systems** | Automated quality assessment | [arXiv:2410.10877](https://arxiv.org/html/2410.10877v1) |

### Aesthetic Prediction

| Paper | Topic | Link |
|-------|-------|------|
| **LAION Aesthetics** | Large-scale aesthetic scoring | [LAION Blog](https://laion.ai/blog/laion-aesthetics/) |
| **CLIP + MLP Predictor** | Aesthetic score training | [GitHub](https://github.com/christophschuhmann/improved-aesthetic-predictor) |

---

## GitHub Repositories

### Core Tools

| Repository | Purpose | Stars | License |
|------------|---------|-------|---------|
| [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) | Node-based image generation | 50k+ | GPL-3.0 |
| [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) | LoRA training GUI | 11k+ | AGPL-3.0 |
| [kohya-ss/sd-scripts](https://github.com/kohya-ss/sd-scripts) | Training scripts backend | 5k+ | Apache-2.0 |

### ComfyUI Extensions

| Repository | Purpose | License |
|------------|---------|---------|
| [pythongosssss/ComfyUI-WD14-Tagger](https://github.com/pythongosssss/ComfyUI-WD14-Tagger) | Booru-style tagging | MIT |
| [1038lab/ComfyUI-Blip](https://github.com/1038lab/ComfyUI-Blip) | BLIP captioning | MIT |
| [miaoshouai/ComfyUI-Miaoshouai-Tagger](https://github.com/miaoshouai/ComfyUI-Miaoshouai-Tagger) | Florence-2 tagging | MIT |
| [fexploit/ComfyUI-AutoLabel](https://github.com/fexploit/ComfyUI-AutoLabel) | Auto descriptions | MIT |
| [rsandagon/comfyui-batch-image-generation](https://github.com/rsandagon/comfyui-batch-image-generation) | Batch generation UI | MIT |

### Aesthetic Scoring

| Repository | Purpose | License |
|------------|---------|---------|
| [LAION-AI/aesthetic-predictor](https://github.com/LAION-AI/aesthetic-predictor) | CLIP-based scoring | MIT |
| [christophschuhmann/improved-aesthetic-predictor](https://github.com/christophschuhmann/improved-aesthetic-predictor) | Enhanced predictor | MIT |
| [rockerBOO/aesthetics-score](https://github.com/rockerBOO/aesthetics-score) | Batch scoring tool | MIT |
| [JD-2006/improved-aesthetic-predictor-batch](https://github.com/JD-2006/improved-aesthetic-predictor-batch) | Batch processing | MIT |

### Dataset Tools

| Repository | Purpose | License |
|------------|---------|---------|
| [starik222/BooruDatasetTagManager](https://github.com/starik222/BooruDatasetTagManager) | Tag editor GUI | GPL-3.0 |
| [BinaryAlley/DatasetTag](https://github.com/BinaryAlley/DatasetTag) | Semi-auto captioning | MIT |
| [hoodini/autocap](https://github.com/hoodini/autocap) | Florence-2 auto-captioning | MIT |
| [redromnon/lora-caption-creator](https://github.com/redromnon/lora-caption-creator) | Manual caption helper | MIT |
| [danbooru/autotagger](https://github.com/danbooru/autotagger) | Danbooru auto-tagging | MIT |

### Image Gallery/Rating

| Repository | Purpose | License |
|------------|---------|---------|
| [digikam.org](https://www.digikam.org/) | Photo management | GPL-2.0 |
| [xemle/home-gallery](https://github.com/xemle/home-gallery) | AI-powered gallery | MIT |
| [photoview/photoview](https://github.com/photoview/photoview) | Self-hosted gallery | AGPL-3.0 |
| [vladmandic/pigallery](https://github.com/vladmandic/pigallery) | AI gallery | MIT |

### Automation

| Repository | Purpose | License |
|------------|---------|---------|
| [gorakhargosh/watchdog](https://github.com/gorakhargosh/watchdog) | File system monitoring | Apache-2.0 |
| [dbader/schedule](https://github.com/dbader/schedule) | Python scheduling | MIT |

---

## HuggingFace Models & Datasets

### Base Models

| Model | Type | Link |
|-------|------|------|
| Stable Diffusion XL | Checkpoint | [stabilityai/stable-diffusion-xl-base-1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) |
| Pony Diffusion V6 XL | Checkpoint | [Civitai](https://civitai.com/models/257749) |

### Captioning Models

| Model | Type | Link |
|-------|------|------|
| BLIP Large | Captioning | [Salesforce/blip-image-captioning-large](https://huggingface.co/Salesforce/blip-image-captioning-large) |
| Florence-2 | Multi-task | [microsoft/Florence-2-large](https://huggingface.co/microsoft/Florence-2-large) |

### Quality Assessment

| Model | Type | Link |
|-------|------|------|
| Aesthetic Predictor | Scoring | [camenduru/improved-aesthetic-predictor](https://huggingface.co/camenduru/improved-aesthetic-predictor) |
| Image Quality Fusion | Multi-metric | [matthewyuan/image-quality-fusion](https://huggingface.co/matthewyuan/image-quality-fusion) |
| Aesthetic Scorer | 7-metric | [rsinema/aesthetic-scorer](https://huggingface.co/rsinema/aesthetic-scorer) |

### Tagging Models

| Model | Type | Link |
|-------|------|------|
| WD14 Tagger | Booru tags | [SmilingWolf/wd-v1-4-moat-tagger-v2](https://huggingface.co/SmilingWolf/wd-v1-4-moat-tagger-v2) |
| Florence PromptGen | Prompt generation | [MiaoshouAI/Florence-2-base-PromptGen-v1.5](https://huggingface.co/MiaoshouAI/Florence-2-base-PromptGen-v1.5) |

---

## Tutorials & Guides

### LoRA Training

| Resource | Topic | Link |
|----------|-------|------|
| Civitai Guide | Dreambooth LoRA with Kohya | [Civitai Article](https://civitai.com/articles/391/tutorial-dreambooth-lora-training-using-kohyass) |
| HuggingFace Diffusers | LoRA training | [Diffusers Docs](https://huggingface.co/docs/diffusers/training/lora) |
| Kohya Wiki | Training parameters | [GitHub Wiki](https://github.com/bmaltais/kohya_ss/wiki/LoRA-training-parameters) |

### ComfyUI

| Resource | Topic | Link |
|----------|-------|------|
| ComfyUI Examples | Workflow examples | [GitHub](https://github.com/comfyanonymous/ComfyUI_examples) |
| Batch Processing Guide | 1000+ images | [Apatero Blog](https://apatero.com/blog/batch-process-1000-images-comfyui-guide-2025) |

### Photo Management

| Resource | Topic | Link |
|----------|-------|------|
| DigiKam vs Darktable | Comparison | [WordPress](https://marcrphoto.wordpress.com/2025/07/21/deep-dive-in-photo-management-why-digikam-beats-darktable-part-1/) |
| Open Source Photography Workflow | Complete workflow | [LiT Guide](https://lifeintimelapse.github.io/an-open-source-photography-workflow.html) |

---

## Related Projects

### Similar Concepts

| Project | Description | Link |
|---------|-------------|------|
| Auto LoRA Trainer | Automated training pipeline | Research needed |
| Image Curator | Dataset curation tool | Research needed |
| Style Transfer Studio | Iterative style learning | Research needed |

### Inspiration Sources

| Source | Concept | Applicability |
|--------|---------|---------------|
| Midjourney ratings | Community rating system | Rating UI inspiration |
| Lightroom culling | Photo selection workflow | Workflow design |
| Active Learning | Iterative sample selection | Training strategy |

---

## Community Resources

### Forums & Discussion

| Platform | Community | Link |
|----------|-----------|------|
| Reddit | r/StableDiffusion | [Reddit](https://reddit.com/r/StableDiffusion) |
| Reddit | r/comfyui | [Reddit](https://reddit.com/r/comfyui) |
| Discord | Civitai | [Discord](https://discord.gg/civitai) |
| Discord | ComfyUI | [Discord](https://discord.gg/comfyui) |

### Model Resources

| Platform | Type | Link |
|----------|------|------|
| Civitai | Models, LoRAs | [civitai.com](https://civitai.com) |
| HuggingFace | Models, Datasets | [huggingface.co](https://huggingface.co) |

---

## Key Concepts Reference

### Human-in-the-Loop (HITL)
- Human feedback integrated into ML pipeline
- Iterative improvement through user input
- Reduces need for large pre-labeled datasets

### Active Learning
- Strategic sample selection for labeling
- Maximizes learning from minimal labels
- Uncertainty-based or diversity-based selection

### Aesthetic Scoring
- CLIP embeddings + linear classifier
- Predicts human aesthetic preferences
- Scale 1-10 (LAION model)

### LoRA (Low-Rank Adaptation)
- Efficient fine-tuning method
- Small adapter weights (~4-200MB)
- Preserves base model capabilities

### Iterative Refinement
- Progressive model improvement
- Each cycle builds on previous
- Human feedback guides direction
