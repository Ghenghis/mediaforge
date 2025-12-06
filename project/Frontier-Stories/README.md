# Frontier-Stories

An 18+ adult content generation platform for creating stories and images using local AI models via LM Studio. Fully local operation with no paid external services.

## ⚠️ Content Warning

This is an **adult content (18+)** project designed for generating NSFW stories and images using uncensored AI models. All content is generated locally and never leaves your machine.

## Features

- **Story Generation**: Create adult narratives using uncensored text models
- **Image Analysis**: Analyze images without content restrictions
- **Portrait Generation**: Generate character portraits with Flux models
- **Automatic Model Switching**: Task-based model selection for optimal results
- **Local-Only Operation**: No external API calls, all processing on your machine
- **Docker Containerization**: Easy deployment on Windows 11

## Quick Start

### Prerequisites

- Windows 11
- Docker Desktop
- LM Studio (running on port 1234)
- Node.js 20+

### Installation

```powershell
# Clone the repository
git clone https://github.com/yourusername/Frontier-Stories.git
cd Frontier-Stories

# Install dependencies
npm install

# Start Docker containers (PostgreSQL, pgAdmin, Functions)
docker-compose up -d

# Start the development server
npm run dev
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | - |
| pgAdmin | http://localhost:5050 | admin@frontier-stories.local / admin |
| Functions API | http://localhost:54321 | - |
| LM Studio | http://localhost:1234 | - |

## Model Configuration

Your 254 local models (1.16 TB) are organized by use case. The system automatically selects the best model for each task.

### Recommended Uncensored Models

#### Text Generation (Stories)
| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| WizardLM-Uncensored-SuperCOT-Storytelling-30B | 18.44 GB | Ultra | Slow |
| Dirty-Shirley-Writer-v2-9B-Uncensored | 7.59 GB | High | Fast |
| Qwen2.5-14B-Instruct-Uncensored | 10.51 GB | High | Medium |
| DeepSeek-R1-NSFW-RP | 4.69 GB | Medium | Fast |
| Llama-3.2-3B-Fluxed-Uncensored | 3.42 GB | Medium | Fast |

#### Vision Models (Image Analysis)
| Model | Size | Quality | Notes |
|-------|------|---------|-------|
| Amoral-Gemma3-12B-Vision | 9.66 GB | High | **BEST** - No content restrictions |
| Llama-3.2-11B-Vision-Abliterated | 1.94 GB | High | Abliterated version |
| Qwen3-VL-30B-A3B | 21.73 GB | Ultra | Largest, highest quality |

#### Image Generation
| Model | Size | Type |
|-------|------|------|
| Chroma-Unlocked-v29 (Flux) | 10.29 GB | Unlocked |
| Flux1-Kontext-Dev | 9.85 GB | Context-aware |

### Automatic Task Switching

The system automatically selects models based on the task:

- `adult_story_generation` → WizardLM-Uncensored-SuperCOT-Storytelling-30B
- `adult_image_analysis` → Amoral-Gemma3-12B-Vision
- `portrait_generation` → Chroma-Unlocked-v29
- `quick_draft` → Llama-3.2-3B-Fluxed-Uncensored

Configure in Settings → Models or edit `src/config/modelConfig.ts`.

## Technology Stack

- **Frontend**: React, TypeScript, Vite, shadcn-ui, Tailwind CSS
- **Database**: PostgreSQL (local Docker container)
- **AI Integration**: LM Studio (local)
- **Containerization**: Docker Compose

## Project Structure

```
Frontier-Stories/
├── docker/
│   ├── frontend/Dockerfile
│   ├── functions/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── server.js
│   └── init-db.sql
├── src/
│   ├── components/
│   │   └── ModelSelector.tsx
│   ├── config/
│   │   └── modelConfig.ts
│   ├── pages/
│   │   └── Settings.tsx
│   └── integrations/
├── models/
│   └── models.md
├── docker-compose.yml
└── .env
```

## Settings

Access the comprehensive settings panel at `/settings`:

- **LM Studio**: Configure connection URL and model paths
- **Models**: Select models for each task type
- **Generation**: Adjust temperature, max tokens, top-p
- **Database**: View connection status and access pgAdmin
- **Content**: Enable/disable adult content, set default ratings

## Development

```powershell
# Run in development mode
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```

## Docker Commands

```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose build --no-cache
```

## Troubleshooting

### LM Studio Connection Failed
1. Ensure LM Studio is running on port 1234
2. Check that a model is loaded in LM Studio
3. Verify firewall isn't blocking the connection

### Docker Issues
1. Ensure Docker Desktop is running
2. Check available disk space
3. Run `docker-compose down -v` and restart

### Model Not Found
1. Check model paths in `src/config/modelConfig.ts`
2. Verify models exist in `C:\Users\Admin\.lmstudio\models`

## License

Private project - All rights reserved
