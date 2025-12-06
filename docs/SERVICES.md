# MediaForge Services Reference
> Complete API service documentation

## Service Map

```
┌─────────────────────────────────────────────────────────────┐
│                    UNIFIED GATEWAY (8300)                   │
│                    Routes all API traffic                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   CORE APIS   │  │   ML/AI APIS  │  │ CONTENT APIS  │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ 8210 Orchestr │  │ 8225 Learning │  │ 8197 Stories  │
│ 8213 ComfyUI  │  │ 8207 Caption  │  │ 8206 Video    │
│ 8196 Rating   │  │ 8230 Training │  │ 8220 Voice    │
│ 8211 Dataset  │  │ 8215 Deployer │  │ 8218 Realtime │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Core Services

### Unified Gateway
| Property | Value |
|----------|-------|
| **Port** | 8300 |
| **Script** | `unified_gateway.py` |
| **Database** | `gateway.db` |
| **Purpose** | Central API router for all services |

**Endpoints:**
- `GET /api/health` - Gateway health check
- `ANY /api/{service}/*` - Route to service

---

### Master Orchestrator
| Property | Value |
|----------|-------|
| **Port** | 8210 |
| **Script** | `master_orchestrator.py` |
| **Database** | `orchestrator.db` |
| **Purpose** | Coordinates workflows across services |

**Endpoints:**
- `GET /api/status` - Orchestrator status
- `POST /api/cycle` - Run orchestration cycle
- `GET /api/queue` - View job queue

---

### Rating Studio
| Property | Value |
|----------|-------|
| **Port** | 8196 |
| **Script** | `rating_studio_pro.py` |
| **Database** | `ratings.db` |
| **Purpose** | Image rating and filtering |

**Endpoints:**
- `GET /api/images` - List images with filters
- `POST /api/rate` - Rate an image
- `GET /api/stats` - Rating statistics

---

### Dataset Builder
| Property | Value |
|----------|-------|
| **Port** | 8211 |
| **Script** | `dataset_builder.py` |
| **Database** | `datasets.db` |
| **Purpose** | Create training datasets |

**Endpoints:**
- `POST /api/dataset/build` - Build new dataset
- `GET /api/datasets` - List datasets
- `POST /api/kohya/config` - Generate training config

---

### LoRA Training
| Property | Value |
|----------|-------|
| **Port** | 8230 |
| **Script** | `lora_training_integration.py` |
| **Database** | `training.db` |
| **Purpose** | Kohya LoRA training integration |

**Endpoints:**
- `GET /api/status` - Training status
- `POST /api/training/start` - Start training job
- `POST /api/training/stop` - Stop training
- `GET /api/models` - List available models

---

## AI/ML Services

### AI Learning Brain
| Property | Value |
|----------|-------|
| **Port** | 8225 |
| **Script** | `ai_learning_brain.py` |
| **Database** | `preferences.db` |
| **Purpose** | Learn user preferences |

**Endpoints:**
- `POST /api/rate` - Learn from rating
- `POST /api/chat` - Learn from chat
- `GET /api/prompt` - Generate smart prompt
- `GET /api/stats` - Learning statistics

---

### Auto Captioner
| Property | Value |
|----------|-------|
| **Port** | 8207 |
| **Script** | `auto_captioner_api.py` |
| **Database** | `captions.db` |
| **Purpose** | Generate image captions |

**Endpoints:**
- `POST /api/caption` - Caption single image
- `POST /api/batch` - Batch caption folder

---

### ComfyUI Automation
| Property | Value |
|----------|-------|
| **Port** | 8213 |
| **Script** | `comfyui_automation.py` |
| **Database** | `comfyui.db` |
| **Purpose** | Automated image generation |

**Endpoints:**
- `POST /api/generate` - Generate image
- `GET /api/workflows` - List workflows
- `GET /api/queue` - Generation queue

---

## Content Services

### Story Generator
| Property | Value |
|----------|-------|
| **Port** | 8197 |
| **Script** | `story_generator_api.py` |
| **Database** | `western_stories.db` |
| **Purpose** | Generate narrative content |

**Endpoints:**
- `POST /api/generate` - Generate story
- `GET /api/stories` - List stories
- `GET /api/templates` - Story templates

---

### Voice Tools
| Property | Value |
|----------|-------|
| **Port** | 8220 |
| **Script** | `voice_tools_unified.py` |
| **Database** | `voice_tools.db` |
| **Purpose** | Text-to-speech integration |

**Endpoints:**
- `POST /api/tts` - Generate speech
- `GET /api/voices` - List available voices

---

## Utility Services

### Workflow Manager
| Property | Value |
|----------|-------|
| **Port** | 8221 |
| **Script** | `workflow_manager.py` |
| **Database** | `workflows.db` |
| **Purpose** | Manage ComfyUI workflows |

---

### Realtime Hub
| Property | Value |
|----------|-------|
| **Port** | 8218 |
| **Script** | `realtime_hub.py` |
| **Purpose** | WebSocket event broadcasting |

---

### Auto Schedulers
| Port | Script | Purpose |
|------|--------|---------|
| 8222 | `dataset_auto_scheduler.py` | Scheduled dataset builds |
| 8223 | `gallery_auto_scheduler.py` | Gallery management |
| 8224 | `backup_auto_scheduler.py` | Automated backups |

---

## Quick Reference

### Start All Core Services
```powershell
# In separate terminals:
python scripts/unified_gateway.py
python scripts/master_orchestrator.py
python scripts/rating_studio_pro.py
python scripts/dataset_builder.py
python scripts/lora_training_integration.py
python scripts/ai_learning_brain.py
```

### Check Service Health
```powershell
$ports = @(8196, 8210, 8211, 8225, 8230, 8300)
foreach ($p in $ports) {
    $test = Test-NetConnection localhost -Port $p -WarningAction SilentlyContinue
    Write-Host "Port $p: $(if($test.TcpTestSucceeded){'UP'}else{'DOWN'})"
}
```

---

*Updated: December 5, 2025*
