# Development Milestones

## Project Phases (Updated with Video Pipeline)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROJECT TIMELINE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 0        PHASE 1        PHASE 2        PHASE 3        PHASE 4       │
│  Video Data     Foundation     Core Tools     Automation     Polish        │
│  ──────────     ──────────     ──────────     ──────────     ──────        │
│  [░░░░░░░░░░]  [░░░░░░░░░░]  [░░░░░░░░░░]  [░░░░░░░░░░]  [░░░░░░░░░░]    │
│  Week 1         Week 2-3       Week 4-5       Week 6-7       Week 8+       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PHASE 0: Video Data Processing (NEW - Week 1)

### Milestone 0.1: Video Filtering
- [ ] Set up Cloud AI integration (OpenAI/Claude)
- [ ] Implement video_filter.py script
- [ ] Filter 55GB videos (female-only, quality filter)
- [ ] Review flagged videos manually
- [ ] Expected: ~30-40% approval rate

### Milestone 0.2: Frame Extraction
- [ ] Implement extract_frames.py
- [ ] Extract quality frames (1 per 3 sec)
- [ ] Quality filtering (blur, brightness)
- [ ] Target: 10,000+ training frames

### Milestone 0.3: Foundation Training
- [ ] Train foundation LoRA from video frames
- [ ] Higher network dim (128) for broad knowledge
- [ ] Validate foundation model quality
- [ ] Output: mystyle_foundation_v1.safetensors

**Deliverables:**
- Filtered video dataset
- 10,000+ extracted frames
- Foundation LoRA model

---

## Phase 1: Foundation (Week 1-2)

### Milestone 1.1: Environment Setup ✓
- [x] Install ComfyUI
- [x] Install Kohya_ss
- [x] Configure folder structure
- [x] Download base models
- [ ] Test basic image generation
- [ ] Test basic LoRA training

### Milestone 1.2: Documentation ✓
- [x] Project overview
- [x] Architecture documentation
- [x] Tools stack documentation
- [x] Rating system specification
- [x] Automation pipeline design
- [x] Training guide

### Milestone 1.3: Initial Dataset
- [ ] Collect 200+ seed images
- [ ] Convert all to standard format (PNG/JPG)
- [ ] Create initial captions
- [ ] Organize in Kohya structure
- [ ] Train initial Bronze v1 LoRA

**Deliverables:**
- Working ComfyUI installation
- Working Kohya_ss installation
- First Bronze LoRA model
- Complete documentation

---

## Phase 2: Core Tools (Week 3-4)

### Milestone 2.1: Rating System
- [ ] Install DigiKam
- [ ] Configure star rating (0-5 native)
- [ ] Implement extended rating (6-15 via tags)
- [ ] Test XMP sidecar generation
- [ ] Create rating workflow documentation

### Milestone 2.2: Batch Generation
- [ ] Create ComfyUI batch workflow
- [ ] Implement `generate_batch.py` script
- [ ] Test 300-image batch generation
- [ ] Set up output folder organization
- [ ] Add generation metadata logging

### Milestone 2.3: Auto-Captioning
- [ ] Install BLIP model locally
- [ ] Install WD14 tagger
- [ ] Create `auto_caption.py` script
- [ ] Test caption quality
- [ ] Compare BLIP vs WD14 output

**Deliverables:**
- Functional rating workflow
- Batch generation pipeline
- Auto-captioning system

---

## Phase 3: Automation (Week 5-6)

### Milestone 3.1: Sorting Automation
- [ ] Create SQLite database schema
- [ ] Implement `sort_by_rating.py`
- [ ] Add XMP/database sync
- [ ] Test sorting accuracy
- [ ] Add error handling

### Milestone 3.2: Dataset Builder
- [ ] Implement `build_dataset.py`
- [ ] Add tier-based filtering
- [ ] Implement repeat calculation
- [ ] Test dataset structure
- [ ] Add validation checks

### Milestone 3.3: Training Automation
- [ ] Implement `train_lora.py`
- [ ] Add tier configuration
- [ ] Implement progress logging
- [ ] Add completion notification
- [ ] Test end-to-end training

### Milestone 3.4: Orchestrator
- [ ] Create main orchestrator script
- [ ] Implement state machine
- [ ] Add file watching
- [ ] Test full cycle
- [ ] Add recovery from failures

**Deliverables:**
- Fully automated pipeline
- Working orchestrator
- End-to-end test results

---

## Phase 4: Polish (Week 7-8)

### Milestone 4.1: Rating UI
- [ ] Design custom rating interface
- [ ] Implement keyboard shortcuts
- [ ] Add progress tracking
- [ ] Implement tooltip help
- [ ] Test user experience

### Milestone 4.2: Dashboard
- [ ] Create status dashboard
- [ ] Show training progress
- [ ] Display image statistics
- [ ] Show model history
- [ ] Add export reports

### Milestone 4.3: Quality Improvements
- [ ] Add aesthetic pre-scoring
- [ ] Implement duplicate detection
- [ ] Add image quality validation
- [ ] Create backup system
- [ ] Add version control for models

**Deliverables:**
- Custom rating UI
- Status dashboard
- Quality control systems

---

## Phase 5: Scale (Week 9+)

### Milestone 5.1: Multi-Style Support
- [ ] Support multiple style projects
- [ ] Independent training pipelines
- [ ] Cross-style learning (optional)
- [ ] Style management interface

### Milestone 5.2: Performance Optimization
- [ ] Optimize batch generation
- [ ] Parallelize captioning
- [ ] Reduce training time
- [ ] Memory optimization

### Milestone 5.3: Advanced Features
- [ ] A/B testing for models
- [ ] Automatic hyperparameter tuning
- [ ] Model blending experiments
- [ ] Community sharing (optional)

**Deliverables:**
- Multi-project support
- Optimized performance
- Advanced features

---

## Detailed Task Breakdown

### Immediate Next Steps (This Week)

```
Priority 1: Fix Kohya_ss Installation
├── Clean up failed venv
├── Use conda environment instead
├── Verify CUDA/PyTorch compatibility
└── Test basic training

Priority 2: First Manual Cycle
├── Generate 100 test images
├── Manually rate in file explorer (rename 0-15)
├── Sort manually into folders
├── Create captions
└── Train Bronze v1

Priority 3: Rating Tool Setup
├── Install DigiKam
├── Import test images
├── Test star rating
├── Test tag-based extended rating
└── Document workflow
```

---

## Success Metrics

### Phase 1 Success
- [ ] Can generate 300 images in <30 min
- [ ] Can train LoRA in <4 hours
- [ ] Generated images show style consistency

### Phase 2 Success
- [ ] Rating 300 images takes <20 min
- [ ] Auto-captions match image content 80%+
- [ ] No manual file operations needed

### Phase 3 Success
- [ ] Full cycle runs unattended
- [ ] Recovery from interruptions works
- [ ] Bronze model quality improves each cycle

### Phase 4 Success
- [ ] Rating UI intuitive (minimal training needed)
- [ ] Dashboard shows useful information
- [ ] Quality control catches bad images

### Phase 5 Success
- [ ] Can run 3+ style projects simultaneously
- [ ] Training time reduced 20%+
- [ ] Advanced features provide measurable improvement

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Kohya_ss install issues | High | Medium | Use conda, document alternatives |
| VRAM limitations | Medium | Low | Optimize batch size, use gradient checkpointing |
| Rating fatigue | High | Medium | Improve UI, batch smaller sets |
| Model overfitting | Medium | Medium | Monitor loss, use regularization |
| Storage space | Low | Medium | Implement cleanup scripts |

---

## Resource Requirements

### Hardware (Already Available)
- RTX 3090 Ti 24GB ✓
- 32GB+ RAM (recommended)
- 500GB+ SSD storage

### Software (All Free/Open Source)
- ComfyUI
- Kohya_ss / sd-scripts
- DigiKam
- Python 3.10+
- SQLite

### Time Investment
- Phase 1: ~10-15 hours
- Phase 2: ~15-20 hours
- Phase 3: ~20-25 hours
- Phase 4: ~15-20 hours
- Phase 5: Ongoing

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2024-12-03 | Initial documentation created |
| | | Phase 1 foundation in progress |
