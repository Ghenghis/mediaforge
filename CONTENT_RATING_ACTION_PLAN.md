# CONTENT RATING SYSTEM - ACTION PLAN
## Real-World Fashion Reflection System (PG to 21+)

**Created:** December 4, 2025  
**Status:** In Progress  
**Priority:** HIGH

---

## OVERVIEW

Comprehensive content rating system that:
- Reflects **real-world fashion** across all historical eras
- Supports **all cultures** (tribal, western, professional, luxury, etc.)
- Provides **granular ratings** from PG to 21+ with strict guardrails
- Integrates with **rating, tagging, and learning systems**
- Includes **failsafes** at every level

---

## CONTENT RATING LEVELS

| Level | Label | Coverage | Description |
|-------|-------|----------|-------------|
| 1 | PG | 95%+ | Fully clothed, modest |
| 2 | PG-13 | 85%+ | Light revealing, summer casual |
| 3 | PG-14 | 75%+ | Swimwear appropriate |
| 4 | PG-15 | 65%+ | Bikini/lingerie hints |
| 5 | PG-16 | 50%+ | Lingerie/revealing fashion |
| 6 | PG-17 | 35%+ | Suggestive/risque |
| 7 | 18+ | 20%+ | Artistic/partial nudity |
| 8 | 19+ | 10%+ | Full artistic nudity |
| 9 | 20+ | 0%+ | Explicit content |
| 10 | 21+ | 0%+ | Unrestricted |

---

## HISTORICAL ERAS SUPPORTED

1. **Ancient (BC)** - Greek, Roman, Egyptian, Persian, Celtic
2. **Medieval (500-1400)** - European, Byzantine, Viking, Moorish
3. **Renaissance (1400-1600)** - Italian, French, Spanish, Flemish
4. **Baroque/Rococo (1600-1800)** - French Court, Dutch, Austrian
5. **Victorian (1800-1900)** - British, American, Colonial
6. **Early Modern (1900-1950)** - Flapper, Pin-up, Hollywood
7. **Modern (1950-2000)** - Diverse global fashion
8. **Contemporary (2000-Present)** - Current global styles

---

## PHASE 1: Core Configuration (Priority: HIGH)

### Tasks:
- [x] 1.1 Create `content_rating_system.json` with all levels
- [x] 1.2 Define historical era fashion mappings
- [x] 1.3 Define cultural style mappings
- [x] 1.4 Define socioeconomic style mappings
- [x] 1.5 Define guardrails and failsafes
- [ ] 1.6 Create validation module

### Files:
```
data/content_rating_system.json  ✅ Complete
scripts/content_rating_validator.py  ⏳ Pending
```

---

## PHASE 2: Database Integration (Priority: HIGH)

### Tasks:
- [ ] 2.1 Add content_rating fields to images table
- [ ] 2.2 Add historical_era field to images table
- [ ] 2.3 Add cultural_style field to images table
- [ ] 2.4 Create content_rating_history table
- [ ] 2.5 Create guardrail_violations table
- [ ] 2.6 Migration script for existing data

### Database Schema:
```sql
-- Add to images table
ALTER TABLE images ADD COLUMN content_rating TEXT DEFAULT 'PG';
ALTER TABLE images ADD COLUMN historical_era TEXT;
ALTER TABLE images ADD COLUMN cultural_style TEXT;
ALTER TABLE images ADD COLUMN socioeconomic_style TEXT;
ALTER TABLE images ADD COLUMN guardrail_status TEXT DEFAULT 'passed';

-- Content rating history
CREATE TABLE content_rating_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id TEXT REFERENCES images(id),
    old_rating TEXT,
    new_rating TEXT,
    changed_by TEXT,
    reason TEXT,
    created_at TIMESTAMP
);

-- Guardrail violations log
CREATE TABLE guardrail_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id TEXT,
    violation_type TEXT,
    expected_rating TEXT,
    actual_content TEXT,
    auto_corrected BOOLEAN,
    created_at TIMESTAMP
);
```

---

## PHASE 3: Validation Engine (Priority: HIGH)

### Tasks:
- [ ] 3.1 Create content rating validator module
- [ ] 3.2 Implement skin visibility calculator
- [ ] 3.3 Implement forbidden content detector
- [ ] 3.4 Implement era/culture tag validator
- [ ] 3.5 Create auto-correction system
- [ ] 3.6 Create violation reporting

### Validation Rules:
```python
# Skin visibility by rating
MAX_SKIN = {
    "PG": 15, "PG13": 25, "PG14": 35, "PG15": 45,
    "PG16": 55, "PG17": 70, "18+": 85, "19+": 95,
    "20+": 100, "21+": 100
}

# Required coverage areas
MUST_COVER = {
    "PG": ["chest", "groin", "buttocks", "midriff"],
    "PG13": ["chest", "groin", "buttocks"],
    # ... etc
}

# Global forbidden (ALL ratings)
FORBIDDEN = ["child", "minor", "underage", "teen", "loli", ...]
```

---

## PHASE 4: UI Integration (Priority: MEDIUM)

### Tasks:
- [ ] 4.1 Add content rating selector to rating modal
- [ ] 4.2 Add era selector dropdown
- [ ] 4.3 Add culture selector dropdown
- [ ] 4.4 Add visual rating indicator on cards
- [ ] 4.5 Add filter by content rating
- [ ] 4.6 Add guardrail status indicator
- [ ] 4.7 Implement blur for mature content

### UI Components:
```
- Content Rating Selector (10 levels)
- Historical Era Selector (8 eras)
- Cultural Style Selector (5+ cultures)
- Guardrail Status Badge
- Mature Content Blur Toggle
```

---

## PHASE 5: LLM Integration (Priority: MEDIUM)

### Tasks:
- [ ] 5.1 Add content rating to prompt builder
- [ ] 5.2 Era-aware prompt generation
- [ ] 5.3 Culture-aware prompt generation
- [ ] 5.4 Guardrail validation in LLM prompts
- [ ] 5.5 Auto-suggest content rating from prompt

### LLM Prompt Template:
```
Generate an image prompt with:
- Content Rating: {rating}
- Historical Era: {era}
- Cultural Style: {culture}
- Fashion appropriate for {rating} in {era} {culture} context

GUARDRAILS:
- Maximum skin visibility: {max_skin}%
- Must cover: {must_cover}
- Forbidden: {forbidden_tags}
```

---

## PHASE 6: Learning Integration (Priority: MEDIUM)

### Tasks:
- [ ] 6.1 Track content rating accuracy
- [ ] 6.2 Learn from user corrections
- [ ] 6.3 Improve era/culture suggestions
- [ ] 6.4 Track guardrail violation patterns
- [ ] 6.5 Auto-improve validation rules

### Learning Data:
```sql
CREATE TABLE rating_learning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    predicted_rating TEXT,
    user_corrected_rating TEXT,
    image_tags TEXT,
    prompt_used TEXT,
    accuracy_score REAL,
    created_at TIMESTAMP
);
```

---

## PHASE 7: Batch Generation (Priority: MEDIUM)

### Tasks:
- [ ] 7.1 Generate batches by content rating
- [ ] 7.2 Generate batches by historical era
- [ ] 7.3 Generate batches by cultural style
- [ ] 7.4 Mix era/culture/rating combinations
- [ ] 7.5 Guardrail enforcement in batches

---

## GUARDRAILS & FAILSAFES

### Level 1: Prompt Validation
- Check prompt against forbidden terms
- Validate rating-appropriate tags
- Block incompatible combinations

### Level 2: Generation Validation
- LLM validates prompt before sending to ComfyUI
- Add safety negative prompts automatically
- Flag suspicious prompts for review

### Level 3: Output Validation
- (Future) Image analysis for content rating
- Flag mismatched content for review
- Auto-adjust rating if needed

### Level 4: User Verification
- 18+ content requires verification
- Blur mature content by default
- User can adjust but system logs changes

---

## FILES TO CREATE/MODIFY

### New Files:
```
data/content_rating_system.json       ✅ Created
scripts/content_rating_validator.py   ⏳ Pending
scripts/era_culture_manager.py        ⏳ Pending
scripts/guardrail_engine.py           ⏳ Pending
```

### Files to Modify:
```
scripts/rating_studio_ultra.py        ⏳ Add content rating UI
data/master_learning.db               ⏳ Add new tables
data/complete_tags_config.json        ⏳ Add era/culture tags
```

---

## TESTING CHECKLIST

- [ ] All 10 content ratings work correctly
- [ ] All 8 historical eras generate appropriate content
- [ ] All cultural styles work with all ratings
- [ ] Guardrails block forbidden content
- [ ] Learning system improves over time
- [ ] UI displays all options correctly
- [ ] Batch generation respects ratings
- [ ] LLM integration works with all options

---

## SUCCESS CRITERIA

1. **Rating Accuracy**: 95%+ content matches selected rating
2. **Era Accuracy**: Fashion matches selected historical era
3. **Culture Accuracy**: Style matches selected culture
4. **Guardrail Effectiveness**: 100% forbidden content blocked
5. **User Satisfaction**: Easy to use, no confusion
6. **Learning Improvement**: Suggestions improve over 30 days

---

## NEXT STEPS

1. Complete Phase 2 (Database Integration)
2. Build validation engine (Phase 3)
3. Update UI with new selectors (Phase 4)
4. Integrate with LLM prompts (Phase 5)
5. Test all combinations
6. Deploy and monitor
