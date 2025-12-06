# Known Issues and Fixes

## Code Quality Issues Detected

### lm_studio_mcp.py
| Line | Issue | Severity | Status |
|------|-------|----------|--------|
| 1 | Low Cohesion | Warning | Improved |
| 1 | Overall Code Complexity | Warning | **FIXED** |
| 111 | Code Duplication (get_models) | Warning | **FIXED** |
| 127 | Code Duplication (get_current_model) | Warning | **FIXED** |
| 218 | Large Method (177 lines) - list_tools | Warning | Acceptable |
| 397 | Bumpy Road (13 bumps) - call_tool | Warning | **FIXED** |
| 397 | Deep Nesting (5 levels) | Warning | **FIXED** |
| 397 | Complex Method (cc=69) | Warning | **FIXED** → cc=5 |
| 397 | Large Method (292 lines) | Warning | **FIXED** → 10 lines |

**Fixes Applied:**
1. ✅ Extracted `_fetch_models_data()` to eliminate HTTP duplication
2. ✅ Split `call_tool` into 10 handler functions via `TOOL_HANDLERS` registry
3. ✅ Reduced cyclomatic complexity from 69 to ~5
4. ✅ Removed legacy code (380+ lines deleted)
5. ✅ Added helper functions: `_detect_content_category()`, `_detect_rating_from_prompt()`

### advanced_learning_system.py
| Line | Issue | Severity | Status |
|------|-------|----------|--------|
| 37 | Large Method (84 lines) | Warning | Pending split |
| 145 | Excess Arguments (7) | Warning | Use dataclass |
| 245 | Bumpy Road (2 bumps) | Warning | Simplify |
| 245 | Excess Arguments (5) | Warning | Use dataclass |
| 385 | Excess Arguments (5) | Warning | Use dataclass |

**Fix Plan:**
1. Create `LearningConfig` dataclass for method parameters
2. Split large method into sub-methods
3. Extract configuration to external dict

### ai_learning_brain.py
| Line | Issue | Severity | Status |
|------|-------|----------|--------|
| 169 | Bumpy Road (2 bumps) | Warning | Simplify |
| 169 | Deep Nesting (5 levels) | Warning | Flatten |
| 169 | Complex Method (cc=9) | Warning | Pending |
| 227 | Complex Method (cc=9) | Warning | Pending |
| 344 | Bumpy Road (3 bumps) | Warning | Simplify |
| 344 | Deep Nesting (5 levels) | Warning | Flatten |
| 344 | Complex Method (cc=15) | Warning | Pending |
| 448 | Large Method (84 lines) | Warning | Split |

**Fix Plan:**
1. Use helper functions for nested conditionals
2. Extract tag checking to separate method
3. Implement early returns to reduce nesting

### story_collection_system.py
| Line | Issue | Severity | Status |
|------|-------|----------|--------|
| 1 | Overall Code Complexity | Warning | Pending |
| 120 | Excess Arguments (5) | Warning | Use dataclass |
| 166 | Bumpy Road (2 bumps) | Warning | Simplify |
| 222 | Bumpy Road (4 bumps) | Warning | Simplify |
| 222 | Complex Method (cc=18) | Warning | Split |

---

## Missing Features Identified

### Automation Tools Needed
- [ ] Auto-repair scripts for code issues
- [ ] Event handling verification system
- [ ] Proactive code quality framework
- [ ] Automated linting integration
- [ ] Error suggestion system

### Story Integration Missing
- [x] Storyline chat integration - **IMPLEMENTED**
- [x] Menu system for projects - **IMPLEMENTED**
- [x] Actor profile viewing - **IMPLEMENTED**
- [x] Age-based content rules - **IMPLEMENTED**
- [ ] Video generation pipeline
- [ ] Scenery auto-generation
- [ ] Background matching to actors

### MCP Server Issues
- [ ] Playwright health check failing
- [ ] Docker container orchestration incomplete
- [ ] LM Studio connection retry logic
- [ ] Context window management for 160k+ models

### Database Issues
- [ ] Missing indexes on frequently queried columns
- [ ] No cleanup for orphaned records
- [ ] Transaction handling incomplete

---

## Refactoring Priority

### Critical (Must Fix)
1. `lm_studio_mcp.py:call_tool` - 292 lines, cc=69
2. `story_collection_system.py:line 222` - cc=18
3. `ai_learning_brain.py:line 344` - cc=15

### Important (Should Fix)
1. All methods with 5+ arguments
2. Methods with deep nesting (5+ levels)
3. Duplicate code sections

### Nice to Have
1. Low cohesion improvements
2. Overall complexity reduction
3. Better documentation

---

## How to Use Auto-Repair

```python
# Run code quality checker
python scripts/code_quality_checker.py

# Auto-fix common issues
python scripts/auto_repair.py --fix-style
python scripts/auto_repair.py --reduce-complexity
```

---

## Service Health Checklist

| Service | Port | Health Check | Status |
|---------|------|--------------|--------|
| Rating System | 8198 | GET / | Check |
| Country Rating | 8199 | GET / | Check |
| Guardrails | 8200 | GET / | Check |
| Frontier Stories | 8195 | GET / | Check |
| Dashboard API | 8100 | GET / | Check |
| Playwright | 8203 | GET /health | Check |
| ComfyUI | 8204 | GET /health | Check |
| LM Studio | 1234 | GET /v1/models | External |

---

## Fix Implementation Log

### 2024-12-04

1. Created `LAUNCH_MEDIAFORGE.bat` - Master launcher
2. Created `story_integration_menu.py` - Full menu system
3. Added age-based content rules
4. Documented all code quality issues
5. Created fix priority list
6. **FIXED** `lm_studio_mcp.py` - Refactored call_tool (cc: 69→5)
7. Created `code_quality_checker.py` - Automated analysis tool
8. Updated `start_all_apis.py` with all services
9. Updated `README.md` with milestones
10. Fixed code duplication in LMStudioClient

### Pending

- Add dataclasses for excess arguments in learning systems
- Reduce cyclomatic complexity in `story_collection_system.py`
- Implement auto-fix for missing docstrings
- Add Docker health check integration

---

## Automation Tools Status

| Tool | Status | Description |
|------|--------|-------------|
| `LAUNCH_MEDIAFORGE.bat` | ✅ Ready | Master launcher |
| `story_integration_menu.py` | ✅ Ready | Interactive menu |
| `code_quality_checker.py` | ✅ Ready | Analyzes code issues |
| `start_all_apis.py` | ✅ Ready | Starts all services |
| `frontier_stories_integration.py` | ✅ Ready | 525 actors, story generation |
| `teepee_image_generator.py` | ✅ Ready | Batch image generation |
| `frontier_api_service.py` | ✅ Ready | REST API (port 8195) |
| Auto-repair scripts | 🔨 Planned | Fix issues automatically |
| Playwright health | 🔨 In Progress | Browser automation |
| Docker orchestration | 📋 Planned | Container management |
