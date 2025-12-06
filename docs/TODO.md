# MediaForge TODO List
> Priority-ordered task list

## 🔴 Critical (Blocking)

### LoRA Training Pipeline
- [ ] Test Kohya training with SDXL base model
- [ ] Verify dataset format compatibility
- [ ] Test training API endpoint
- [ ] Monitor first training run

### Service Startup
- [ ] Create `start_services.ps1` master script
- [ ] Define service dependencies
- [ ] Add health check validation
- [ ] Create service restart logic

---

## 🟡 High Priority

### Integration Testing
- [ ] Test Rating Studio → Dataset Builder flow
- [ ] Test Dataset Builder → LoRA Training flow
- [ ] Test ComfyUI automation end-to-end
- [ ] Validate API gateway routing

### Code Quality
- [ ] Fix duplicate port 8190 assignments
- [ ] Add error handling to API endpoints
- [ ] Implement request validation
- [ ] Add structured logging

### Documentation
- [x] Create PROJECT_AUDIT.md
- [x] Create TODO.md
- [ ] Create API_REFERENCE.md
- [ ] Create SERVICES.md
- [ ] Add inline code documentation

---

## 🟢 Medium Priority

### WPF Dashboard
- [ ] Connect to real API endpoints
- [ ] Add service status indicators
- [ ] Implement training progress view
- [ ] Add model management UI

### Voice/TTS Integration
- [ ] Test GPT-SoVITS integration
- [ ] Wire voice tools to story generator
- [ ] Add voice preview in UI
- [ ] Implement batch voice generation

### Story System
- [ ] Complete story generation UI
- [ ] Add story editing features
- [ ] Implement story-to-image pipeline
- [ ] Add character consistency

---

## 🔵 Low Priority (Nice to Have)

### Performance
- [ ] Implement caching layer
- [ ] Add database indexing
- [ ] Optimize image processing
- [ ] Profile slow endpoints

### DevOps
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Automated testing
- [ ] Production deployment

### Features
- [ ] User authentication
- [ ] Multi-user support
- [ ] Cloud backup
- [ ] Mobile UI

---

## ✅ Recently Completed

- [x] Download SDXL models (base, refiner, pony, juggernaut)
- [x] Download ControlNet models (canny, depth)
- [x] Download VAE models
- [x] Download upscalers
- [x] Install Kohya toml dependency
- [x] Refactor ai_learning_brain.py
- [x] Clean up 200GB+ old LLM models
- [x] Create project audit documentation

---

## Progress Tracking

| Category | Done | Total | % |
|----------|------|-------|---|
| Core Services | 6 | 10 | 60% |
| Model Downloads | 12 | 12 | 100% |
| Documentation | 2 | 6 | 33% |
| Testing | 0 | 10 | 0% |
| UI Integration | 2 | 8 | 25% |

**Overall: ~70% Complete**

---

*Updated: December 5, 2025*
