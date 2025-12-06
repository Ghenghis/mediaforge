# 📋 LORAFORGE - MASTER TODO
## Automated Indexing & Database Integration Plan

**Created:** December 3, 2025  
**Status:** In Progress  
**Goal:** Complete automated indexing system with real data integration

---

## 🎯 OVERVIEW

Build a comprehensive media indexing system that:
- Scans and catalogs ALL image/video files
- Extracts metadata and quality metrics
- Stores in SQLite database for fast queries
- Integrates with all existing features
- Powers the dashboard with REAL data

---

## 📂 SUPPORTED FORMATS

### Images (25+ formats)
```
Standard: jpg, jpeg, png, gif, bmp, webp, tiff, tif
Modern: avif, heic, heif, jfif, jp2, jpx
Raw: cr2, cr3, nef, arw, dng, orf, rw2, pef, srw, raf
Vector: svg (metadata only)
Other: ico, cur, psd, xcf
```

### Videos (20+ formats)
```
Common: mp4, avi, mkv, mov, wmv, webm
Streaming: m4v, flv, f4v, ts, m2ts
Legacy: mpeg, mpg, vob, 3gp, 3g2
Professional: mxf, prores
```

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                     LORAFORGE INDEXER                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Scanner    │───▶│   Analyzer   │───▶│   Database   │  │
│  │              │    │              │    │   (SQLite)   │  │
│  │ - Find files │    │ - Quality    │    │              │  │
│  │ - Get meta   │    │ - CLIP score │    │ - Media      │  │
│  │ - Hash files │    │ - Captions   │    │ - Analysis   │  │
│  └──────────────┘    │ - Clusters   │    │ - Sessions   │  │
│                      └──────────────┘    └──────────────┘  │
│                             │                    │          │
│                             ▼                    ▼          │
│                      ┌──────────────┐    ┌──────────────┐  │
│                      │  Dashboard   │◀───│  REST API    │  │
│                      │    (WPF)     │    │  (FastAPI)   │  │
│                      └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ PHASE 1: Core Indexer (Priority: HIGH) - COMPLETED ✅
**Target:** Basic scanning and database storage

### Tasks:
- [x] 1.1 Create `media_indexer.py` - File scanner for all formats
- [x] 1.2 Create `database.py` - SQLite database manager
- [x] 1.3 Create database schema for media catalog
- [x] 1.4 Implement file hashing for deduplication
- [x] 1.5 Extract basic metadata (size, dimensions, duration)
- [x] 1.6 Create CLI for manual indexing
- [x] 1.7 Create `self_learning_data.py` - Self-improving tagging system

### Files Created:
```
scripts/indexer/
├── __init__.py               ✅ Module exports
├── media_indexer.py          ✅ Main scanner with all formats
├── database.py               ✅ SQLite manager with schema
└── self_learning_data.py     ✅ Tagging + feedback + learning
```

---

## ✅ PHASE 2: Analysis Integration (Priority: HIGH) - COMPLETED ✅
**Target:** Connect indexer to all analysis features

### Tasks:
- [x] 2.1 Integrate CLIP evaluation on indexed images
- [x] 2.2 Integrate quality scoring (blur, brightness)
- [x] 2.3 Integrate scene detection for videos
- [x] 2.4 Integrate auto-captioning (WD14/LMStudio)
- [x] 2.5 Integrate character clustering
- [x] 2.6 Store all analysis results in database

### Database Tables:
```sql
-- Analysis results
CREATE TABLE image_analysis (
    media_id INTEGER REFERENCES media(id),
    clip_score REAL,
    quality_score REAL,
    blur_score REAL,
    brightness REAL,
    caption TEXT,
    tags TEXT,  -- JSON array
    cluster_id INTEGER,
    analyzed_at TIMESTAMP
);

CREATE TABLE video_analysis (
    media_id INTEGER REFERENCES media(id),
    scene_count INTEGER,
    total_frames INTEGER,
    extracted_frames TEXT,  -- JSON array of frame paths
    analyzed_at TIMESTAMP
);
```

---

## ✅ PHASE 3: API Integration (Priority: MEDIUM)
**Target:** REST API for dashboard and external access

### Tasks:
- [ ] 3.1 Add indexer endpoints to dashboard_api.py
- [ ] 3.2 Create endpoints for browsing indexed media
- [ ] 3.3 Create endpoints for triggering analysis
- [ ] 3.4 Create endpoints for batch operations
- [ ] 3.5 WebSocket updates for indexing progress

### API Endpoints:
```
GET  /api/media                 - List all indexed media
GET  /api/media/{id}            - Get media details
GET  /api/media/images          - List images only
GET  /api/media/videos          - List videos only
POST /api/index/scan            - Start scan of directory
POST /api/index/analyze/{id}    - Analyze specific media
GET  /api/stats                 - Database statistics
GET  /api/clusters              - Get character clusters
```

---

## ✅ PHASE 4: UI Integration (Priority: MEDIUM)
**Target:** Real data in WPF dashboard

### Tasks:
- [ ] 4.1 Replace mock data with API calls
- [ ] 4.2 Add media browser view
- [ ] 4.3 Add indexing progress view
- [ ] 4.4 Add filtering and search
- [ ] 4.5 Add batch action buttons
- [ ] 4.6 Display real statistics

### WPF Views to Update:
```
MainWindow.xaml         - Real stats from API
MediaBrowserView.xaml   - Browse indexed media (NEW)
IndexingView.xaml       - Control indexing (NEW)
AnalysisView.xaml       - View analysis results (NEW)
```

---

## ✅ PHASE 5: Advanced Features (Priority: LOW)
**Target:** Optimization and advanced capabilities

### Tasks:
- [ ] 5.1 Background indexing service
- [ ] 5.2 File system watcher for auto-updates
- [ ] 5.3 Thumbnail generation
- [ ] 5.4 Export to training datasets
- [ ] 5.5 Import from existing datasets
- [ ] 5.6 Duplicate detection across directories

---

## 📊 DATABASE SCHEMA (SQLite)

```sql
-- Core media table
CREATE TABLE media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_hash TEXT,  -- SHA256 for dedup
    file_size INTEGER,
    media_type TEXT,  -- 'image' or 'video'
    format TEXT,      -- file extension
    width INTEGER,
    height INTEGER,
    duration REAL,    -- for videos (seconds)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'indexed'  -- indexed, analyzed, approved, rejected
);

-- Analysis results
CREATE TABLE analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
    analysis_type TEXT,  -- clip, quality, caption, cluster
    result_json TEXT,    -- Flexible JSON storage
    score REAL,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Training dataset assignments
CREATE TABLE dataset_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
    dataset_name TEXT,
    split TEXT,  -- train, val, test
    caption TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexing sessions
CREATE TABLE index_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_path TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    files_found INTEGER,
    files_indexed INTEGER,
    status TEXT
);

-- Indexes for performance
CREATE INDEX idx_media_type ON media(media_type);
CREATE INDEX idx_media_status ON media(status);
CREATE INDEX idx_media_hash ON media(file_hash);
CREATE INDEX idx_analysis_media ON analysis(media_id);
```

---

## 🔄 INTEGRATION MAP

```
Existing Feature         →  Indexer Integration
─────────────────────────────────────────────────
clip_evaluator.py        →  Store CLIP scores in analysis table
image_cleaner.py         →  Quality metrics + dedup via hash
scene_detector.py        →  Video scene analysis
auto_captioner.py        →  Generate and store captions
character_clusterer.py   →  Assign cluster IDs
model_comparator.py      →  Compare using indexed data
dashboard_api.py         →  Serve real indexed data
```

---

## 📅 TIMELINE

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Core Indexer | 1-2 hours | 🔄 In Progress |
| Phase 2: Analysis Integration | 1-2 hours | ⏳ Pending |
| Phase 3: API Integration | 1 hour | ⏳ Pending |
| Phase 4: UI Integration | 2 hours | ⏳ Pending |
| Phase 5: Advanced Features | Future | ⏳ Pending |

---

## 🚀 NEXT ACTIONS

1. **Create indexer module structure**
2. **Implement SQLite database manager**
3. **Build file scanner with all format support**
4. **Create metadata extractor**
5. **Integrate with existing analysis features**
6. **Update API to serve real data**
7. **Update UI to consume real data**

---

## 📝 NOTES

- Use SQLite for portability (no external database server needed)
- All paths stored as absolute for reliability
- File hashes enable cross-directory deduplication
- JSON columns for flexible analysis storage
- Background processing for large collections
- Real-time progress via WebSocket

---

## 🧠 SELF-LEARNING DATA SYSTEM

### Tagging Categories
| Category | Purpose | Source |
|----------|---------|--------|
| `source` | Where data came from | Auto |
| `content` | What's in the image | Auto/WD14 |
| `quality` | Technical quality | Auto |
| `training` | Model version used | System |
| `feedback` | User approval/rejection | User |
| `learning` | Improved from results | System |
| `custom` | User-defined tags | User |

### Feedback Loop
```
┌─────────────────────────────────────────────────────────────┐
│                    SELF-IMPROVEMENT LOOP                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Index   │───▶│ Analyze  │───▶│   Tag    │              │
│  │  Media   │    │  Content │    │  Auto    │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       ▲                               │                     │
│       │                               ▼                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Adjust  │◀───│  Learn   │◀───│   User   │              │
│  │ Criteria │    │  From    │    │ Feedback │              │
│  └──────────┘    │ Results  │    └──────────┘              │
│       │          └──────────┘                               │
│       │               ▲                                     │
│       ▼               │                                     │
│  ┌──────────┐    ┌──────────┐                              │
│  │  Better  │───▶│  Train   │                              │
│  │  Filter  │    │  Model   │                              │
│  └──────────┘    └──────────┘                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Learning Capabilities
1. **Tag Effectiveness Tracking**
   - Tracks which tags correlate with successful training
   - Recommends effective tags, warns about ineffective ones

2. **Quality Criteria Auto-Adjustment**
   - Criteria adjust based on what produces good models
   - Stays within safe bounds to prevent damage

3. **Feedback Integration**
   - User approvals boost tag effectiveness
   - User rejections reduce tag weights

4. **Provenance Tracking**
   - Full history of every action on data
   - Never lose track of data origin

### Safety Guarantees
- **Never delete original data** - Archive only
- **Bounded adjustments** - Criteria can't go extreme
- **Version everything** - Full audit trail
- **Learn gradually** - Small incremental changes

---

## 📊 CURRENT STATUS

| Component | Status | Location |
|-----------|--------|----------|
| Database Manager | ✅ Complete | `indexer/database.py` |
| Media Indexer | ✅ Complete | `indexer/media_indexer.py` |
| Self-Learning System | ✅ Complete | `indexer/self_learning_data.py` |
| CLIP Evaluator | ✅ Complete | `core/clip_evaluator.py` |
| Image Cleaner | ✅ Complete | `core/image_cleaner.py` |
| Scene Detector | ✅ Complete | `core/scene_detector.py` |
| Auto Captioner | ✅ Complete | `core/auto_captioner.py` |
| Character Clusterer | ✅ Complete | `core/character_clusterer.py` |
| Model Comparator | ✅ Complete | `core/model_comparator.py` |
| Pipeline Orchestrator | ✅ Complete | `core/pipeline_orchestrator.py` |
| **Model Manager** | ✅ Complete | `ai/model_manager.py` |
| **Auto Benchmarker** | ✅ Complete | `ai/auto_benchmarker.py` |
| **Model Rankings** | ✅ Complete | `ai/model_rankings.py` |
| **Dashboard API** | ✅ Complete | `api/dashboard_api.py` |
| UI Integration | ⏳ Pending | `ui/WPF/` |

---

## 🤖 AI MODEL MANAGEMENT SYSTEM

### Model Discovery
- Scans Ollama (http://localhost:11434)
- Scans LM Studio (~/.lmstudio/models)
- Finds 40+ image formats, 25+ video formats
- Auto-detects: size, family, quantization, vision, uncensored

### Fair Testing (CRITICAL!)
```
1. UNLOAD all models first (save memory!)
2. LOAD single model being tested
3. RUN benchmark (speed + quality)
4. UNLOAD model after test
5. REPEAT for next model
```

### Use Cases Ranked
| Use Case | Description | Speed Weight | Quality Weight |
|----------|-------------|--------------|----------------|
| caption | Image captioning | 40% | 60% |
| vision | Image analysis | 30% | 70% |
| chat | General conversation | 50% | 50% |
| code | Code generation | 30% | 70% |
| creative | Creative writing | 20% | 80% |
| speed | Fastest response | 90% | 10% |
| quality | Best output | 10% | 90% |

### Model Combinations
```
single           - One model for everything
dual_speed_quality - Fast for drafts, quality for polish
dual_small_large   - Small (2B) for simple, large (7B+) for complex
specialized        - Different model per task
```

### API Endpoints (Real Data!)
```
GET  /api/stats              - Overall statistics
GET  /api/media              - Indexed media list
GET  /api/models             - All discovered models
GET  /api/models/rankings    - Top 10/20 per use case
GET  /api/models/best/{task} - Best model for task
GET  /api/models/fast        - Speed champions
GET  /api/models/uncensored  - Uncensored models
GET  /api/models/configs     - Recommended configurations
POST /api/models/benchmark   - Benchmark specific model
POST /api/feedback           - Add user feedback
GET  /api/recommendations    - AI-powered suggestions
WS   /ws                     - Real-time updates
```

---

## 🎭 PHASE 7: CONTENT RATING SYSTEM (Priority: HIGH)
**Target:** Real-world fashion reflection system with strict guardrails

### Overview
Comprehensive content rating system that:
- Reflects real-world fashion across ALL historical eras (BC to Present)
- Supports ALL cultures (tribal, western, professional, luxury, etc.)
- Provides granular ratings from PG to 21+ with strict guardrails
- Integrates with rating, tagging, and learning systems

### Content Rating Levels
| Level | Coverage | Description |
|-------|----------|-------------|
| PG | 95%+ | Fully clothed, modest |
| PG-13 | 85%+ | Light revealing, summer casual |
| PG-14 | 75%+ | Swimwear appropriate |
| PG-15 | 65%+ | Bikini/lingerie hints |
| PG-16 | 50%+ | Lingerie/revealing fashion |
| PG-17 | 35%+ | Suggestive/risque |
| 18+ | 20%+ | Artistic/partial nudity |
| 19+ | 10%+ | Full artistic nudity |
| 20+ | 0%+ | Explicit content |
| 21+ | 0%+ | Unrestricted |

### Tasks:
- [x] 7.1 Create `content_rating_system.json` configuration
- [x] 7.2 Create `content_rating_validator.py` module
- [x] 7.3 Create `CONTENT_RATING_ACTION_PLAN.md`
- [ ] 7.4 Add database schema for content ratings
- [ ] 7.5 Integrate with rating studio UI
- [ ] 7.6 Add historical era selector (8 eras)
- [ ] 7.7 Add cultural style selector (5+ cultures)
- [ ] 7.8 Implement guardrail validation engine
- [ ] 7.9 Add LLM integration for rating-aware prompts
- [ ] 7.10 Implement learning from user corrections
- [ ] 7.11 Add batch generation by content rating

### Historical Eras Supported:
```
ancient_bc     - Ancient (BC) - Greek, Roman, Egyptian
medieval       - Medieval (500-1400) - European, Byzantine
renaissance    - Renaissance (1400-1600) - Italian, French
baroque_rococo - Baroque/Rococo (1600-1800) - French Court
victorian      - Victorian (1800-1900) - British, Colonial
early_modern   - Early Modern (1900-1950) - Pin-up, Hollywood
modern         - Modern (1950-2000) - Global fashion
contemporary   - Contemporary (2000-Present) - Current
```

### Cultural Styles Supported:
```
tribal         - Tribal/Indigenous (African, Polynesian, etc.)
western_classic - Western Classic (Cowgirl, Frontier)
professional   - Professional/Corporate
luxury_elite   - Luxury/High Society
casual_everyday - Casual/Everyday
```

### Files Created:
```
data/content_rating_system.json      ✅ Complete
scripts/content_rating_validator.py  ✅ Complete
CONTENT_RATING_ACTION_PLAN.md        ✅ Complete
```

### Guardrails & Failsafes:
- Global forbidden terms (child, minor, etc.) - ALWAYS blocked
- Rating-specific restrictions enforced
- Auto-sanitize prompts before generation
- Guardrail negative prompts added automatically
- Violation logging and tracking
- User correction learning

---
