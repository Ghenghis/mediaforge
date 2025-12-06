# Rating System Specification

## Overview

A 16-level (0-15) star rating system designed for iterative LoRA training dataset curation.

---

## Rating Scale Visual Guide

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RATING SCALE (0-15)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  0  ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆  REJECT    → Delete / Move to rejected/            │
│  ─────────────────────────────────────────────────────────────────────────  │
│  1  ★☆☆☆☆☆☆☆☆☆☆☆☆☆☆  POOR      ┐                                        │
│  2  ★★☆☆☆☆☆☆☆☆☆☆☆☆☆  WEAK      │                                        │
│  3  ★★★☆☆☆☆☆☆☆☆☆☆☆☆  FAIR      ├─ ARCHIVE (Basic quality)               │
│  4  ★★★★☆☆☆☆☆☆☆☆☆☆☆  OKAY      │                                        │
│  5  ★★★★★☆☆☆☆☆☆☆☆☆☆  DECENT    ┘                                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  6  ★★★★★★☆☆☆☆☆☆☆☆☆  GOOD      ┐                                        │
│  7  ★★★★★★★☆☆☆☆☆☆☆☆  NICE      ├─ BRONZE TIER (6-15★ training)          │
│  8  ★★★★★★★★☆☆☆☆☆☆☆  GREAT     │                                        │
│  9  ★★★★★★★★★☆☆☆☆☆☆  EXCELLENT ┘                                        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  10 ★★★★★★★★★★☆☆☆☆☆  HOT 10!   ─ SILVER TIER (10-15★ training)          │
│  ─────────────────────────────────────────────────────────────────────────  │
│  11 ★★★★★★★★★★★☆☆☆☆  STUNNING  ┐                                        │
│  12 ★★★★★★★★★★★★☆☆☆  AMAZING   │                                        │
│  13 ★★★★★★★★★★★★★☆☆  SUPERB    ├─ GOLD TIER (13-15★ training)           │
│  14 ★★★★★★★★★★★★★★☆  FLAWLESS  │                                        │
│  15 ★★★★★★★★★★★★★★★  PERFECT   ┘                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Rating Categories Detailed

### Rating 0: REJECT
**Action:** Delete or move to `rejected/` folder

**Criteria:**
- Bad anatomy (extra limbs, wrong proportions)
- Severe artifacts or noise
- Completely off-prompt
- Unwanted content
- Corrupted generation

```
Examples:
- Extra fingers/hands
- Face distortion
- Body horror elements
- Blurry/unrecognizable
```

---

### Ratings 1-5: BASIC (Archive)
**Action:** Archive only, not used for training

| Rating | Name | Description |
|--------|------|-------------|
| 1 | Poor | Barely acceptable, major issues |
| 2 | Weak | Multiple noticeable problems |
| 3 | Fair | Average quality, some issues |
| 4 | Okay | Acceptable but not impressive |
| 5 | Decent | Good attempt, minor flaws |

**Criteria:**
- Recognizable but not training-worthy
- Minor anatomy issues
- Inconsistent style
- Poor composition
- Lack of detail where needed

---

### Ratings 6-9: BRONZE TIER
**Action:** Include in Bronze model training (6-15★)

| Rating | Name | Description |
|--------|------|-------------|
| 6 | Good | Quality image, minor imperfections |
| 7 | Nice | Attractive, good composition |
| 8 | Great | Very good quality, appealing |
| 9 | Excellent | High quality, nearly perfect |

**Criteria:**
- Good anatomy and proportions
- Appealing composition
- Proper lighting and colors
- Style consistency
- Minor details might be off

---

### Rating 10: HOT 10 (Silver Threshold)
**Action:** Include in Silver model training (10-15★)

**The "Hot 10" Criteria:**
```
✓ Perfect or near-perfect anatomy
✓ Highly attractive/appealing
✓ Excellent composition
✓ Great detail in important areas
✓ Consistent style
✓ Good lighting and color
✓ Would proudly display/share
```

---

### Ratings 11-15: GOLD TIER (Perfection)
**Action:** Include in Gold model training (13-15★)

| Rating | Name | Description |
|--------|------|-------------|
| 11 | Stunning | Impressive quality, very attractive |
| 12 | Amazing | Outstanding in most aspects |
| 13 | Superb | Near-perfect, Gold threshold |
| 14 | Flawless | Exceptional quality |
| 15 | Perfect | Best possible output |

**Criteria:**
- Flawless anatomy
- Exceptional detail
- Perfect composition
- Ideal lighting
- Exactly matches desired style
- Would use as reference/example

---

## Rating UI Mockup

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IMAGE RATING INTERFACE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │                                                                     │   │
│  │                         [IMAGE PREVIEW]                             │   │
│  │                                                                     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  QUICK ACTIONS                                                      │   │
│  │  [0-REJECT]  [←PREV]  [NEXT→]  [SKIP]                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RATING                                                    [?]Help  │   │
│  │                                                                     │   │
│  │  Archive:    [1] [2] [3] [4] [5]         (Not for training)        │   │
│  │  Bronze:     [6] [7] [8] [9]             (Production v1)           │   │
│  │  Silver:     [10]                        (Production v2)           │   │
│  │  Gold:       [11] [12] [13] [14] [15]    (Production v3)           │   │
│  │                                                                     │   │
│  │  Current: ★★★★★★★★☆☆☆☆☆☆☆ (8 - GREAT)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PROGRESS: 47/300 images rated | Session time: 12:34               │   │
│  │  [████████░░░░░░░░░░░░] 15.7%                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `0` | Reject (delete) |
| `1-9` | Rate 1-9 |
| `Shift+0` | Rate 10 |
| `Shift+1-5` | Rate 11-15 |
| `←` / `A` | Previous image |
| `→` / `D` | Next image |
| `Space` | Skip (no rating) |
| `Z` | Undo last rating |
| `F` | Toggle fullscreen |
| `?` | Show help |

---

## Rating Workflow

### Fast Rating Process

```
1. Load batch of generated images (300)
2. View each image (1-3 seconds each)
3. Quick decision:
   - Obvious reject → Press 0
   - Basic quality → Press 1-5
   - Good quality → Press 6-9
   - Hot image → Press Shift+0 (10)
   - Perfect → Press Shift+1-5 (11-15)
4. Auto-advance to next image
5. Batch complete → Auto-sort by rating
```

### Time Estimate

| Images | Avg Time/Image | Total Time |
|--------|----------------|------------|
| 100 | 3 sec | ~5 min |
| 300 | 3 sec | ~15 min |
| 500 | 3 sec | ~25 min |

---

## Rating Distribution Goals

### Healthy Distribution

```
Expected distribution for well-tuned model:

Rating 0  (Reject):    5-15%   ████
Rating 1-5 (Archive):  20-30%  ████████████
Rating 6-9 (Bronze):   40-50%  ████████████████████
Rating 10 (Silver):    10-15%  ██████
Rating 11-15 (Gold):   5-10%   ████

If > 30% rejected → Model needs improvement
If < 5% Gold → Model not yet optimized
```

### Training Progression

```
CYCLE 1: Initial training
  → Expect high reject rate (20-30%)
  → Low Gold rate (1-3%)

CYCLE 5: Bronze model stable
  → Reject rate drops (10-15%)
  → Gold rate increases (5-8%)

CYCLE 10+: Silver/Gold models
  → Reject rate minimal (5-10%)
  → Gold rate healthy (10-15%)
```

---

## Tooltip Help Text

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RATING GUIDE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HOW TO RATE:                                                               │
│                                                                             │
│  0 = DELETE - Bad anatomy, artifacts, unwanted content                      │
│                                                                             │
│  1-5 = ARCHIVE - Okay but not training worthy                               │
│    1: Major issues    2: Multiple problems    3: Average                    │
│    4: Acceptable      5: Decent attempt                                     │
│                                                                             │
│  6-9 = BRONZE - Good quality, include in basic training                     │
│    6: Good    7: Nice    8: Great    9: Excellent                          │
│                                                                             │
│  10 = HOT 10 - Almost perfect, very attractive                              │
│        (Threshold for Silver model training)                                │
│                                                                             │
│  11-15 = GOLD - Perfection tier                                             │
│    11: Stunning    12: Amazing    13: Superb (Gold threshold)              │
│    14: Flawless    15: Perfect                                              │
│                                                                             │
│  TIP: Rate quickly! Trust your first impression.                            │
│       Average 2-3 seconds per image.                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
