# 📖 STORY GENERATOR - COMPREHENSIVE ACTION PLAN
## Western Stories & Family Character Image Generation System

---

## 🎯 PROJECT OVERVIEW

Create a complete story book character generation system with:
- 525 actors with family relationships
- PG to XXX content rating system with granular levels
- Actor dialog templates
- Historical era accuracy (1850-1900 Western)
- 8K quality image generation
- Full WPF GUI integration

---

## 📊 CONTENT RATING SYSTEM

### Rating Levels (12 Total)

| Level | Code | Description | Clothing Coverage | Family Safe |
|-------|------|-------------|-------------------|-------------|
| **Extra Light** | EL | All ages, fully modest | 100% coverage | ✅ Yes |
| **Light** | L | General audience | 95%+ coverage | ✅ Yes |
| **PG** | PG | Parental guidance | 90%+ coverage | ✅ Yes |
| **PG-13** | PG13 | Teen appropriate | 85%+ coverage | ✅ Yes |
| **PG-17** | PG17 | Older teen | 80%+ coverage | ✅ Yes |
| **Soft** | SOFT | Soft content, see-through | Transparent fabrics OK | ⚠️ Separate |
| **Medium** | MED | Medium adult content | 60%+ coverage | ❌ Adult |
| **R** | R | Restricted adult | 40%+ coverage | ❌ Adult |
| **Hard** | HARD | Hard content | Minimal coverage | ❌ Adult |
| **Hardcore** | HC | Hardcore content | Very minimal | ❌ Adult |
| **X** | X | Explicit | Limited coverage | ❌ Adult |
| **XXX** | XXX | Extreme explicit | No restrictions | ❌ Adult |

### Guardrails & Restrictions

#### Family Stories (EL through PG-17)
- ✅ Full clothing always required
- ✅ Age-appropriate poses
- ✅ Family-friendly expressions
- ✅ Period-accurate modest attire
- ❌ No revealing content
- ❌ No suggestive poses
- ❌ Strict child protection (always fully clothed, modest)

#### Adult Content (SOFT through XXX)
- 🔒 Requires age verification
- 🔒 Separate access controls
- 🔒 No minors in any adult content
- 🔒 Content warnings required

---

## 📋 TASK LIST

### PHASE 1: Core System Setup ✅
- [x] Create database schema for actors/families
- [x] Define content rating levels
- [x] Create western costume templates
- [x] Setup quality tag presets (8K)

### PHASE 2: Actor Templates
- [ ] Create 20 character role templates
- [ ] Define male/female costume variations per role
- [ ] Add age group modifiers (child, teen, adult, elder)
- [ ] Add ethnicity diversity options
- [ ] Create family relationship mappings

### PHASE 3: Dialog System
- [ ] Create dialog template structure
- [ ] Add character personality types
- [ ] Define story scene templates
- [ ] Add emotional expression mappings

### PHASE 4: Content Rating Integration
- [ ] Implement 12-level rating system
- [ ] Add guardrail validation
- [ ] Create rating-specific prompt modifiers
- [ ] Separate family/adult content paths

### PHASE 5: WPF GUI Integration
- [ ] Add Story Generator view to WPF app
- [ ] Create actor management panel
- [ ] Add family tree visualization
- [ ] Implement content rating selector
- [ ] Add batch generation controls
- [ ] Create image preview gallery

### PHASE 6: Generation Engine
- [ ] Connect to ComfyUI for generation
- [ ] Implement queue management
- [ ] Add progress tracking
- [ ] Create enhancement pipeline

### PHASE 7: Quality Assurance
- [ ] Add rating compliance checking
- [ ] Implement auto-correction for violations
- [ ] Create quality scoring system
- [ ] Add batch review interface

---

## 🎭 ACTOR TEMPLATE CATEGORIES

### Character Roles (20 Types)
1. **Sheriff** - Law enforcement, badge, authority
2. **Deputy** - Assistant lawman
3. **Rancher** - Wealthy landowner
4. **Cowboy/Cowgirl** - Ranch hand, working class
5. **Outlaw** - Bandits, wanted criminals
6. **Banker** - Town financier
7. **Doctor** - Medical professional
8. **Preacher** - Religious leader
9. **Saloon Owner** - Business owner
10. **Blacksmith** - Craftsman
11. **Merchant** - Store owner
12. **Farmer** - Agricultural worker
13. **Native Chief** - Indigenous leader
14. **Native Warrior** - Indigenous fighter
15. **Schoolteacher** - Educator
16. **Bartender** - Saloon worker
17. **Prospector** - Gold miner
18. **Cavalry Officer** - Military
19. **Judge** - Legal authority
20. **Mayor** - Town leader

### Family Roles
- **Patriarch** - Father/Grandfather
- **Matriarch** - Mother/Grandmother
- **Child** - Young family member
- **Teen** - Teenage family member
- **Young Adult** - Older child
- **Elder** - Grandparent

---

## 💬 DIALOG TEMPLATES

### Scene Types
1. **Introduction** - Character first appearance
2. **Conflict** - Dramatic confrontation
3. **Romance** - Love interest scenes
4. **Action** - Chase/fight scenes
5. **Resolution** - Story conclusion
6. **Family Moment** - Domestic scenes

### Dialog Structure
```json
{
  "scene_type": "introduction",
  "character_role": "sheriff",
  "mood": "confident",
  "dialog": [
    "Name's {first_name}. I keep the peace around here.",
    "You new in town? Best keep your nose clean.",
    "This badge ain't just for show, partner."
  ],
  "expression": "stern_gaze",
  "pose": "standing_confident"
}
```

---

## 🖥️ WPF INTEGRATION PLAN

### New Views Required

#### 1. StoryGeneratorView.xaml
- Actor creation panel
- Family tree editor
- Scene builder
- Dialog editor

#### 2. ActorGalleryView.xaml
- Grid view of all actors
- Filter by family/role/rating
- Bulk selection tools
- Image generation queue

#### 3. ContentRatingView.xaml
- Rating selector with visual guides
- Family/Adult separation toggle
- Guardrail status display
- Violation warnings

#### 4. SceneBuilderView.xaml
- Drag-drop scene composition
- Character positioning
- Background selection
- Dialog overlay editor

### API Endpoints (New)

```
POST /api/actors/generate     - Generate 525 actors
GET  /api/actors              - List all actors
GET  /api/actors/{id}         - Get actor details
GET  /api/families            - List all families
POST /api/images/generate     - Queue image generation
POST /api/dialogs/generate    - Generate dialog text
GET  /api/content-ratings     - Get rating definitions
POST /api/validate-rating     - Check content compliance
```

---

## 🔧 TECHNICAL SPECIFICATIONS

### Image Quality Presets

#### 8K Maximum Quality
```
Resolution: 7680x4320 (or max supported)
Steps: 50+
CFG: 7-8
Sampler: DPM++ 2M SDE Karras
Upscaler: 4x-UltraSharp
Denoise: 0.4 for upscale
```

#### Quality Tags (Always Include)
- 8k uhd, ultra high resolution
- masterpiece, best quality
- extremely detailed, photorealistic
- sharp focus, high detail skin texture
- subsurface scattering
- film grain, cinematic

### Era-Accurate Elements (1850-1900)
- No modern items (cars, phones, plastic)
- Period-accurate clothing materials
- Natural lighting (sun, oil lamps, candles)
- Appropriate settings (frontier towns, ranches)

---

## ✅ COMPLETION CHECKLIST

- [ ] All 525 actors generated
- [ ] All families with proper relationships
- [ ] All 12 content ratings functional
- [ ] Family/Adult separation working
- [ ] Guardrails preventing violations
- [ ] WPF GUI fully integrated
- [ ] 8K image generation working
- [ ] Dialog templates complete
- [ ] Quality assurance passing
- [ ] Full documentation complete

---

## 📅 TIMELINE

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1 | 1 day | ✅ Complete |
| Phase 2 | 1 day | 🔄 In Progress |
| Phase 3 | 1 day | ⏳ Pending |
| Phase 4 | 1 day | ⏳ Pending |
| Phase 5 | 2 days | ⏳ Pending |
| Phase 6 | 1 day | ⏳ Pending |
| Phase 7 | 1 day | ⏳ Pending |

**Total: 8 days**

---

## 🚨 GUARDRAILS & SAFETY

### Absolute Rules (Cannot Override)
1. **No minors in adult content** - EVER
2. **Child characters always fully clothed** - No exceptions
3. **Family content stays family-safe** - Strict enforcement
4. **Content warnings required** - For all R+ content
5. **Age verification required** - For adult access

### Soft Rules (Can Be Adjusted)
1. Clothing transparency levels (SOFT rating)
2. Pose suggestiveness (varies by rating)
3. Expression intensity (varies by rating)

---

*Last Updated: {datetime}*
*Project: Western Stories - 525 Actors*
