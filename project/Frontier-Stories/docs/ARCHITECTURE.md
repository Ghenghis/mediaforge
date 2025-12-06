# 🏗️ Frontier-Stories: System Architecture

> Technical blueprints, schematics, and system design

---

## 📐 High-Level Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           FRONTIER-STORIES SYSTEM                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                           PRESENTATION LAYER                             │ ║
║  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │ ║
║  │  │   Index     │ │  Portrait   │ │   Story     │ │  Settings   │       │ ║
║  │  │   (Home)    │ │   Gallery   │ │  Creation   │ │   Panel     │       │ ║
║  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │ ║
║  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │ ║
║  │  │   Voice     │ │   Story     │ │  Template   │ │ Storyboard  │       │ ║
║  │  │  Library    │ │  Library    │ │ Generator   │ │   Viewer    │       │ ║
║  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                      │                                        ║
║                                      ▼                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                           COMPONENT LAYER                                │ ║
║  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                  │ ║
║  │  │  ActorCard    │ │PortraitDialog │ │ VoiceSelector │                  │ ║
║  │  │  Component    │ │  Component    │ │  Component    │                  │ ║
║  │  └───────────────┘ └───────────────┘ └───────────────┘                  │ ║
║  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                  │ ║
║  │  │ ModelSelector │ │ PresetSystem  │ │  UI Library   │                  │ ║
║  │  │  Component    │ │  Components   │ │  (shadcn/ui)  │                  │ ║
║  │  └───────────────┘ └───────────────┘ └───────────────┘                  │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                      │                                        ║
║                                      ▼                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                           SERVICE LAYER                                  │ ║
║  │  ┌─────────────────────────────────────────────────────────────────┐    │ ║
║  │  │                    Supabase Client                               │    │ ║
║  │  │  • Authentication  • Database Queries  • Real-time Subscriptions │    │ ║
║  │  └─────────────────────────────────────────────────────────────────┘    │ ║
║  │  ┌─────────────────────────────────────────────────────────────────┐    │ ║
║  │  │                    Functions Client                              │    │ ║
║  │  │  • AI Generation   • Model Management  • Image Processing        │    │ ║
║  │  └─────────────────────────────────────────────────────────────────┘    │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                      │                                        ║
╚══════════════════════════════════════╪════════════════════════════════════════╝
                                       │
                                       ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                              BACKEND SERVICES                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌───────────────────────┐         ┌───────────────────────┐                 ║
║  │   SUPABASE CLOUD      │         │   LOCAL FUNCTIONS     │                 ║
║  │   (Lovable Backend)   │         │   SERVER (:3001)      │                 ║
║  │                       │         │                       │                 ║
║  │  ┌─────────────────┐  │         │  ┌─────────────────┐  │                 ║
║  │  │   PostgreSQL    │  │         │  │   Express.js    │  │                 ║
║  │  │   Database      │  │         │  │   API Server    │  │                 ║
║  │  │                 │  │         │  │                 │  │                 ║
║  │  │  • actors       │  │         │  │  • /health      │  │                 ║
║  │  │  • stories      │  │         │  │  • /models      │  │                 ║
║  │  │  • templates    │  │         │  │  • /generate-*  │  │                 ║
║  │  │  • portraits    │  │         │  │  • /actors      │  │                 ║
║  │  │  • presets      │  │         │  │                 │  │                 ║
║  │  └─────────────────┘  │         │  └────────┬────────┘  │                 ║
║  │                       │         │           │           │                 ║
║  │  ┌─────────────────┐  │         │           ▼           │                 ║
║  │  │   Storage       │  │         │  ┌─────────────────┐  │                 ║
║  │  │   (Images)      │  │         │  │   LM Studio     │  │                 ║
║  │  └─────────────────┘  │         │  │   Connection    │  │                 ║
║  │                       │         │  │   (:1234)       │  │                 ║
║  │  ┌─────────────────┐  │         │  └─────────────────┘  │                 ║
║  │  │   Edge          │  │         │                       │                 ║
║  │  │   Functions     │  │         └───────────────────────┘                 ║
║  │  └─────────────────┘  │                                                   ║
║  └───────────────────────┘                                                   ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
                                       │
                                       ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                              AI/ML LAYER                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                         LM STUDIO (:1234)                                │ ║
║  │                                                                          │ ║
║  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐            │ ║
║  │  │  VISION MODELS  │ │   TEXT MODELS   │ │  IMAGE MODELS   │            │ ║
║  │  │                 │ │                 │ │                 │            │ ║
║  │  │ • amoral-gemma3 │ │ • wizardlm-     │ │ • chroma-       │            │ ║
║  │  │   -12b-vision   │ │   uncensored-   │ │   unlocked-v29  │            │ ║
║  │  │ • llama-3.2-11b │ │   30b           │ │ • flux1-kontext │            │ ║
║  │  │   -abliterated  │ │ • dirty-shirley │ │                 │            │ ║
║  │  │ • qwen3-vl-8b   │ │   -9b           │ │                 │            │ ║
║  │  │                 │ │ • qwen2.5-14b   │ │                 │            │ ║
║  │  └─────────────────┘ └─────────────────┘ └─────────────────┘            │ ║
║  │                                                                          │ ║
║  │  Total: 254 Models | 1.16 TB | C:\Users\Admin\.lmstudio\models          │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 🐳 Docker Container Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DOCKER COMPOSE NETWORK                                │
│                        (frontier-network)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐    ┌────────────────────┐    ┌──────────────────┐  │
│  │ frontier-stories-  │    │ frontier-stories-  │    │ frontier-stories │  │
│  │ frontend           │    │ functions          │    │ -postgres        │  │
│  │                    │    │                    │    │                  │  │
│  │ Image: node:20     │    │ Image: node:20     │    │ Image: postgres  │  │
│  │ Port: 5173→8080    │    │ Port: 3001→3000    │    │ Port: 5432       │  │
│  │                    │    │                    │    │                  │  │
│  │ Volumes:           │    │ Volumes:           │    │ Volumes:         │  │
│  │ • ./src:/app/src   │    │ • LM Studio models │    │ • postgres_data  │  │
│  │ • ./public         │    │                    │    │                  │  │
│  │                    │    │ Env:               │    │ Env:             │  │
│  │ Env:               │    │ • DATABASE_URL     │    │ • POSTGRES_DB    │  │
│  │ • VITE_SUPABASE_*  │    │ • LM_STUDIO_URL    │    │ • POSTGRES_USER  │  │
│  │ • VITE_LM_STUDIO_* │    │                    │    │ • POSTGRES_PASS  │  │
│  └────────────────────┘    └────────────────────┘    └──────────────────┘  │
│           │                         │                         │             │
│           │                         │                         │             │
│           └─────────────────────────┼─────────────────────────┘             │
│                                     │                                        │
│                          ┌──────────┴──────────┐                            │
│                          │  frontier-stories   │                            │
│                          │  -pgadmin           │                            │
│                          │                     │                            │
│                          │  Image: dpage/      │                            │
│                          │  pgadmin4           │                            │
│                          │  Port: 5050→80      │                            │
│                          │                     │                            │
│                          │  Env:               │                            │
│                          │  • PGADMIN_EMAIL    │                            │
│                          │  • PGADMIN_PASSWORD │                            │
│                          └─────────────────────┘                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

                    EXTERNAL CONNECTIONS
                    
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   Host Machine                        Cloud Services                         │
│   ┌─────────────────┐                ┌─────────────────────────────────┐   │
│   │   LM Studio     │                │   Supabase (Lovable Cloud)      │   │
│   │   :1234         │                │   https://pvlqwxkgovjwqhpqnssl  │   │
│   │                 │                │   .supabase.co                   │   │
│   │   254 Models    │                │                                  │   │
│   │   1.16 TB       │                │   • Database (525+ actors)      │   │
│   └─────────────────┘                │   • Storage (images)            │   │
│                                      │   • Edge Functions              │   │
│   ┌─────────────────┐                └─────────────────────────────────┘   │
│   │   Browser       │                                                       │
│   │   localhost:    │                                                       │
│   │   5173          │                                                       │
│   └─────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project File Structure

```
G:\Github\Frontier-Stories\
│
├── 📁 docker/                    # Docker configuration
│   ├── 📁 frontend/
│   │   └── Dockerfile           # Frontend container
│   ├── 📁 functions/
│   │   ├── Dockerfile           # Functions server container
│   │   ├── server.js            # Express server (488 lines)
│   │   └── package.json
│   ├── init-db.sql              # Database initialization
│   ├── import-actors.sql        # Actor import script
│   └── seed-actors.sql          # Sample data
│
├── 📁 docs/                      # Documentation (NEW)
│   ├── PROJECT_STATUS.md
│   ├── FEATURES.md
│   ├── ACTION_PLAN.md
│   ├── ARCHITECTURE.md
│   └── MISSING_FEATURES.md
│
├── 📁 src/                       # Frontend source
│   ├── 📁 assets/               # Static assets
│   │   ├── wood-texture.jpg
│   │   ├── parchment-texture.jpg
│   │   └── actor-*.jpg
│   │
│   ├── 📁 components/           # React components
│   │   ├── 📁 ui/              # shadcn/ui components (49 items)
│   │   ├── ActorCard.tsx
│   │   ├── CreateActorDialog.tsx
│   │   ├── PortraitCustomizationDialog.tsx
│   │   ├── ModelSelector.tsx
│   │   ├── VoiceSelector.tsx
│   │   └── ... (16 components)
│   │
│   ├── 📁 pages/                # Page components
│   │   ├── Index.tsx            # Home/Actor list
│   │   ├── PortraitGallery.tsx  # Portrait management
│   │   ├── PortraitAnalytics.tsx
│   │   ├── StoryCreation.tsx    # Story editor
│   │   ├── StoryLibrary.tsx
│   │   ├── StoryTemplates.tsx
│   │   ├── TemplateGenerator.tsx
│   │   ├── StoryboardViewer.tsx
│   │   ├── VoiceLibrary.tsx
│   │   ├── Settings.tsx
│   │   └── NotFound.tsx
│   │
│   ├── 📁 hooks/                # Custom hooks
│   │   └── use-toast.ts
│   │
│   ├── 📁 integrations/         # External integrations
│   │   ├── 📁 supabase/
│   │   │   ├── client.ts        # Supabase client
│   │   │   └── types.ts         # Database types (890 lines)
│   │   └── 📁 local-api/
│   │       └── client.ts        # Local API client
│   │
│   ├── App.tsx                  # Main app component
│   ├── main.tsx                 # Entry point
│   └── index.css                # Global styles
│
├── 📁 supabase/                  # Supabase configuration
│   ├── config.toml              # Project config
│   └── 📁 functions/            # Edge functions
│       ├── analyze-story-scenes/
│       ├── colorize-portrait/
│       ├── export-story/
│       ├── generate-actor-portrait/
│       ├── generate-scene-imagery/
│       ├── generate-scenery/
│       ├── generate-template/
│       ├── style-transfer/
│       ├── text-to-speech/
│       ├── voice-clone/
│       └── voice-design/
│
├── 📁 cvs/                       # CSV data exports
│   ├── actors-export-*.csv      # 525 actors
│   ├── actor_portrait_history-*.csv
│   ├── story_templates-*.csv
│   └── story_template_lines-*.csv
│
├── 📁 models/                    # Model documentation
│   └── setup.md                 # Setup instructions
│
├── docker-compose.yml           # Docker orchestration
├── .env                         # Environment variables
├── package.json                 # Node dependencies
├── vite.config.ts              # Vite configuration
├── tailwind.config.ts          # Tailwind configuration
└── tsconfig.json               # TypeScript configuration
```

---

## 🔄 Data Flow Diagrams

### Portrait Generation Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │────▶│ Portrait │────▶│ Functions│────▶│LM Studio │
│  Click   │     │ Dialog   │     │ Server   │     │  API     │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                      │                │                │
                      │ Customization  │ POST           │ Vision
                      │ Options        │ /generate-     │ Model
                      │                │ actor-portrait │ Call
                      │                │                │
                      ▼                ▼                ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Toast   │◀────│ Display  │◀────│ Save to  │◀────│ Generate │
│ Success  │     │ Portrait │     │ Supabase │     │ Image    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### Story Creation Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Select  │────▶│  Write   │────▶│  Assign  │────▶│   Save   │
│  Actors  │     │  Lines   │     │  Voices  │     │  Story   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     ▼                ▼                ▼                ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Actor    │     │ AI Gen   │     │ Voice    │     │ Supabase │
│ Library  │     │ (opt.)   │     │ Preview  │     │ Database │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

---

## 🗄️ Database Schema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATABASE TABLES                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────┐       ┌─────────────────────┐                  │
│  │       actors        │       │  actor_portrait_    │                  │
│  ├─────────────────────┤       │      history        │                  │
│  │ id (uuid) PK        │       ├─────────────────────┤                  │
│  │ first_name          │◀──────│ actor_id FK         │                  │
│  │ middle_name         │       │ id (uuid) PK        │                  │
│  │ last_name           │       │ image_url           │                  │
│  │ full_name (gen)     │       │ color_mode          │                  │
│  │ role                │       │ generation_params   │                  │
│  │ era                 │       │ is_current          │                  │
│  │ bio                 │       │ created_at          │                  │
│  │ ethnicity           │       └─────────────────────┘                  │
│  │ voice_id            │                                                 │
│  │ voice_provider      │       ┌─────────────────────┐                  │
│  │ voice_settings      │       │   story_templates   │                  │
│  │ tags                │       ├─────────────────────┤                  │
│  │ image_url           │       │ id (uuid) PK        │                  │
│  │ metadata            │       │ title               │                  │
│  │ character_type      │       │ description         │                  │
│  │ is_active           │       │ category            │                  │
│  │ created_at          │       │ tags                │                  │
│  │ updated_at          │       │ created_at          │                  │
│  └─────────────────────┘       └──────────┬──────────┘                  │
│                                           │                              │
│  ┌─────────────────────┐                  │                              │
│  │       stories       │       ┌──────────┴──────────┐                  │
│  ├─────────────────────┤       │ story_template_     │                  │
│  │ id (uuid) PK        │       │     lines           │                  │
│  │ title               │       ├─────────────────────┤                  │
│  │ description         │       │ id (uuid) PK        │                  │
│  │ created_at          │       │ template_id FK      │                  │
│  │ updated_at          │       │ line_number         │                  │
│  └──────────┬──────────┘       │ actor_role          │                  │
│             │                  │ content             │                  │
│  ┌──────────┴──────────┐       │ stage_direction     │                  │
│  │    story_lines      │       └─────────────────────┘                  │
│  ├─────────────────────┤                                                 │
│  │ id (uuid) PK        │       ┌─────────────────────┐                  │
│  │ story_id FK         │       │  preset_collections │                  │
│  │ actor_id FK         │       ├─────────────────────┤                  │
│  │ line_number         │       │ id (uuid) PK        │                  │
│  │ content             │       │ name                │                  │
│  │ voice_settings      │       │ description         │                  │
│  └─────────────────────┘       │ presets             │                  │
│                                │ created_at          │                  │
│                                └─────────────────────┘                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Local Functions Server (localhost:3001)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | /health | Health check |
| GET | /models | List LM Studio models |
| POST | /generate-actor-portrait | Generate portrait |
| POST | /generate-story | Generate story text |
| GET | /actors | List all actors |
| GET | /actors/:id | Get actor by ID |
| POST | /actors | Create actor |
| PUT | /actors/:id | Update actor |
| DELETE | /actors/:id | Delete actor |

### Supabase Edge Functions

| Function | Purpose | Status |
|----------|---------|--------|
| generate-actor-portrait | AI portrait generation | ⚠️ Stub |
| colorize-portrait | B&W to color | ❌ |
| style-transfer | Apply art styles | ❌ |
| generate-template | AI story templates | ⚠️ Stub |
| analyze-story-scenes | Scene analysis | ⚠️ Stub |
| generate-scene-imagery | Scene images | ❌ |
| generate-scenery | Backgrounds | ❌ |
| text-to-speech | Voice synthesis | ❌ |
| voice-clone | Clone voices | ❌ |
| voice-design | Custom voices | ❌ |
| export-story | Export stories | ❌ |
