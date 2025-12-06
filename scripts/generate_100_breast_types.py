"""
Generate 100 Images - All Cup Sizes & Breast Types
Uses PerfectBreastsPonyV2 LoRA for quality
Tests AI learning from user ratings
"""
import json
import random
import time
import urllib.request
import sqlite3
from pathlib import Path
from datetime import datetime

COMFY_URL = "http://localhost:8188"
DB_PATH = Path(r"c:\Users\Admin\civitai\data\preferences.db")
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")

# ============================================================
# CUP SIZES - Full Range
# ============================================================
CUP_SIZES = [
    # Smallest
    {"name": "flat", "tags": "(flat chest:1.3), (no breasts:1.2), (boyish figure:1.1)"},
    {"name": "AAA", "tags": "(AAA cup:1.3), (very flat chest:1.2), (tiny breasts:1.2), (barely visible breasts:1.1)"},
    {"name": "AA", "tags": "(AA cup:1.3), (very small breasts:1.2), (petite bust:1.2), (subtle curves:1.1)"},
    {"name": "A", "tags": "(A cup:1.3), (small breasts:1.2), (modest bust:1.1), (small perky breasts:1.2)"},
    {"name": "B", "tags": "(B cup:1.3), (small-medium breasts:1.2), (perky breasts:1.2)"},
    {"name": "C", "tags": "(C cup:1.3), (medium breasts:1.2), (average bust:1.1), (round breasts:1.2)"},
]

# ============================================================
# BREAST SHAPES - Perky, Pointy, Puffy, Lifelike
# ============================================================
BREAST_SHAPES = [
    {"name": "perky", "tags": "(perky breasts:1.4), (upturned breasts:1.3), (firm breasts:1.2), (lifted breasts:1.2)"},
    {"name": "pointy", "tags": "(pointy breasts:1.4), (cone shaped breasts:1.3), (pointed nipples:1.2), (torpedo breasts:1.2)"},
    {"name": "puffy", "tags": "(puffy nipples:1.4), (puffy areola:1.3), (soft puffy breasts:1.2), (rounded puffy:1.2)"},
    {"name": "round", "tags": "(round breasts:1.4), (perfectly round:1.3), (spherical breasts:1.2), (circular shape:1.2)"},
    {"name": "teardrop", "tags": "(teardrop breasts:1.4), (natural teardrop shape:1.3), (pear shaped:1.2)"},
    {"name": "athletic", "tags": "(athletic breasts:1.4), (firm athletic chest:1.3), (toned pectorals:1.2), (sporty bust:1.2)"},
]

# ============================================================
# NIPPLE TYPES
# ============================================================
NIPPLE_TYPES = [
    "(small nipples:1.2), (pink nipples:1.2), (delicate nipples:1.1)",
    "(perky nipples:1.2), (erect nipples:1.2), (prominent nipples:1.2)",
    "(puffy nipples:1.3), (soft puffy areola:1.2), (raised areola:1.2)",
    "(pointy nipples:1.2), (protruding nipples:1.2), (sharp nipples:1.1)",
    "(small areola:1.2), (tiny pink nipples:1.2), (subtle nipples:1.1)",
]

# ============================================================
# BODY FRAMES
# ============================================================
BODY_FRAMES = [
    "(petite:1.3), (small frame:1.2), (delicate build:1.1)",
    "(slim:1.3), (slender:1.2), (lean body:1.1)",
    "(athletic:1.3), (toned:1.2), (fit body:1.1)",
    "(lithe:1.2), (graceful:1.1), (elegant frame:1.1)",
]

# ============================================================
# MUSCLE TONE
# ============================================================
MUSCLE_TONES = [
    "(toned stomach:1.3), (visible abs:1.2), (flat stomach:1.2)",
    "(defined abs:1.3), (six pack:1.2), (muscular stomach:1.2)",
    "(athletic core:1.3), (toned muscles:1.2), (fit physique:1.2)",
    "(slim waist:1.2), (narrow waist:1.2), (hourglass figure:1.1)",
]

# ============================================================
# DATABASE FUNCTIONS
# ============================================================
def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        prompt TEXT,
        negative TEXT,
        tags TEXT,
        model TEXT,
        seed INTEGER,
        rating INTEGER DEFAULT 0,
        cup_size TEXT,
        breast_shape TEXT,
        created_at TEXT,
        rated_at TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS tag_weights (
        tag TEXT PRIMARY KEY,
        likes INTEGER DEFAULT 0,
        dislikes INTEGER DEFAULT 0,
        weight REAL DEFAULT 0.5
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        memory_type TEXT,
        content TEXT,
        is_like INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT,
        extracted_prefs TEXT,
        action_taken TEXT,
        created_at TEXT
    )''')
    
    conn.commit()
    return conn

def save_image(conn, filename, prompt, negative, tags, seed, cup_size, breast_shape):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO images 
        (filename, prompt, negative, tags, model, seed, cup_size, breast_shape, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (filename, prompt, negative, json.dumps(tags), "CyberRealistic+PerfectBreasts", 
          seed, cup_size, breast_shape, datetime.now().isoformat()))
    conn.commit()

def save_memory(conn, memory_type: str, content: str, is_like: bool = True):
    """Save user preference to memory"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_memory (memory_type, content, is_like, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (memory_type, content, 1 if is_like else 0, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()

def remove_memory(conn, memory_type: str, content: str):
    """Remove a preference from memory"""
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM user_memory WHERE memory_type = ? AND content = ?
    ''', (memory_type, content))
    conn.commit()

def get_memories(conn) -> list:
    """Get all user memories/preferences"""
    cursor = conn.cursor()
    cursor.execute('SELECT memory_type, content, is_like FROM user_memory ORDER BY created_at DESC')
    return [{'type': r[0], 'content': r[1], 'is_like': bool(r[2])} for r in cursor.fetchall()]

# ============================================================
# PROMPT BUILDING
# ============================================================
def build_prompt(cup_size: dict, breast_shape: dict, index: int) -> tuple:
    """Build detailed prompt for breast type generation"""
    
    body_frame = BODY_FRAMES[index % len(BODY_FRAMES)]
    muscle_tone = MUSCLE_TONES[index % len(MUSCLE_TONES)]
    nipple_type = NIPPLE_TYPES[index % len(NIPPLE_TYPES)]
    
    age = random.choice(["21yo", "22yo", "23yo", "24yo", "25yo"])
    skin = random.choice([
        "(fair skin:1.1), (porcelain skin:1.1)",
        "(tan skin:1.1), (sun-kissed:1.1)", 
        "(caramel skin:1.1), (warm tone:1.1)",
        "(olive skin:1.1), (mediterranean:1.1)",
        "(dark skin:1.1), (rich brown:1.1)"
    ])
    
    eyes = random.choice([
        "(heterochromia:1.3), (different colored eyes:1.2)",
        "(blue eyes:1.2), (piercing gaze:1.1)",
        "(green eyes:1.2), (cat eyes:1.1)",
        "(amber eyes:1.2), (golden eyes:1.1)"
    ])
    
    hair = random.choice([
        "long black hair, flowing hair",
        "short brown hair, messy hair",
        "blonde hair, wavy hair",
        "red hair, curly hair",
        "silver hair, straight hair"
    ])
    
    face_paint = random.choice([
        "(geometric face paint:1.3), (red and black patterns:1.2)",
        "(tribal war paint:1.3), (white stripes:1.2)",
        "(ceremonial face paint:1.3), (sacred symbols:1.2)",
        "(warrior markings:1.3), (bold lines:1.2)"
    ])
    
    body_paint = random.choice([
        "(tribal body paint:1.3), (geometric patterns on arms:1.2)",
        "(war paint on body:1.3), (red ochre patterns:1.2)",
        "(ceremonial body art:1.3), (sacred symbols on torso:1.2)"
    ])
    
    pose = random.choice([
        "standing, hands on hips, confident pose",
        "facing viewer, arms at sides, proud stance",
        "three quarter view, elegant pose",
        "profile view, looking over shoulder"
    ])
    
    lighting = random.choice([
        "(dramatic lighting:1.2), (rim lighting:1.1), (high contrast:1.1)",
        "(golden hour:1.2), (warm lighting:1.1), (soft shadows:1.1)",
        "(studio lighting:1.2), (professional:1.1), (even lighting:1.1)"
    ])
    
    positive = f"""masterpiece, best quality, ultra detailed, 8k resolution, photorealistic, RAW photo, DSLR,
realistic lighting, high detail skin texture, sharp focus, professional photography,
lifelike, hyperrealistic, photo-realistic skin,

(adult woman:1.3), ({age}:1.2), (tribal warrior woman:1.2),

{body_frame},
{muscle_tone},

{cup_size['tags']},
{breast_shape['tags']},
{nipple_type},
(realistic breasts:1.3), (natural breast shape:1.2), (lifelike breast texture:1.2),
(detailed breast skin:1.2), (no sag:1.3), (firm:1.2), (youthful breasts:1.2),

(beautiful face:1.2), (oval face:1.1), {eyes},
{hair},
{skin}, (realistic skin texture:1.2), (skin pores:1.1), (natural skin:1.1),

{face_paint},
{body_paint},
(feather headdress:1.2), tribal jewelry, bone accessories,

{pose},
{lighting},
forest background, nature setting"""

    negative = """EasyNegative, bad-hands-5, ng_deepnegative_v1_75t,
(child:2.0), (kid:2.0), (teen:2.0), (minor:2.0), (underage:2.0),
(saggy breasts:1.6), (droopy breasts:1.6), (hanging breasts:1.5), (deflated:1.5),
(asymmetrical breasts:1.4), (uneven breasts:1.4), (misshapen:1.4),
(bad anatomy:1.4), (bad proportions:1.4), (deformed:1.4),
(extra fingers:1.5), (missing fingers:1.5), (mutated hands:1.4),
(low quality:1.5), (worst quality:1.5), (blurry:1.3),
(watermark:1.5), (text:1.5),
(cartoon:1.5), (anime:1.5), (3d render:1.4),
ugly, disfigured, (old:1.3), (wrinkled:1.3)"""

    tags = [
        cup_size['name'], breast_shape['name'], 
        "perky", "lifelike", "realistic",
        body_frame.split(',')[0].strip('()').split(':')[0],
        muscle_tone.split(',')[0].strip('()').split(':')[0]
    ]
    
    return positive, negative, tags

def create_workflow(positive: str, negative: str, prefix: str) -> dict:
    seed = random.randint(0, 2**32)
    
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "CyberRealistic.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 768, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}},
        "10": {"class_type": "LoraLoader", "inputs": {
            "model": ["4", 0], "clip": ["4", 1],
            "lora_name": "add_detail.safetensors", "strength_model": 0.7, "strength_clip": 0.7
        }},
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["10", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0],
            "seed": seed, "steps": 35, "cfg": 7, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0
        }},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
        "_seed": seed
    }

def queue_prompt(workflow: dict) -> str:
    data = json.dumps({"prompt": {k: v for k, v in workflow.items() if not k.startswith('_')}}).encode()
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read()).get('prompt_id')
    except:
        return None

def wait_completion(prompt_id: str, timeout: int = 180) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
            if prompt_id in json.loads(resp.read()):
                return True
        except:
            pass
        time.sleep(2)
    return False

def main():
    print("="*70)
    print("  GENERATING 100 IMAGES - ALL CUP SIZES & BREAST TYPES")
    print("  Perky | Pointy | Puffy | Round | Lifelike")
    print("="*70)
    
    # Check ComfyUI
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        print("\n✅ ComfyUI connected")
    except:
        print("\n❌ ComfyUI not running!")
        return
    
    conn = init_db()
    
    print(f"\n📊 Generation Matrix:")
    print(f"   Cup sizes: {[c['name'] for c in CUP_SIZES]}")
    print(f"   Shapes: {[s['name'] for s in BREAST_SHAPES]}")
    print(f"   Total combinations: {len(CUP_SIZES)} × {len(BREAST_SHAPES)} = {len(CUP_SIZES) * len(BREAST_SHAPES)}")
    print(f"   Generating: 100 images (with variations)")
    
    # Save initial memories
    save_memory(conn, "preference", "perky breasts", True)
    save_memory(conn, "preference", "no sag", True)
    save_memory(conn, "preference", "lifelike", True)
    save_memory(conn, "dislike", "saggy", False)
    
    success = 0
    failed = 0
    
    print(f"\n🎨 Starting generation...\n")
    
    for i in range(100):
        # Cycle through all cup sizes and shapes
        cup_idx = i % len(CUP_SIZES)
        shape_idx = (i // len(CUP_SIZES)) % len(BREAST_SHAPES)
        
        cup_size = CUP_SIZES[cup_idx]
        breast_shape = BREAST_SHAPES[shape_idx]
        
        print(f"[{i+1:03d}/100] {cup_size['name']:5s} | {breast_shape['name']:10s}", end=" ")
        
        # Build prompt
        positive, negative, tags = build_prompt(cup_size, breast_shape, i)
        
        # Create workflow
        prefix = f"breast_{cup_size['name']}_{breast_shape['name']}_{i+1:03d}"
        workflow = create_workflow(positive, negative, prefix)
        seed = workflow['_seed']
        
        # Generate
        prompt_id = queue_prompt(workflow)
        
        if prompt_id:
            if wait_completion(prompt_id):
                filename = f"{prefix}_{seed}.png"
                save_image(conn, filename, positive, negative, tags, seed, cup_size['name'], breast_shape['name'])
                print("✅")
                success += 1
            else:
                print("⏱️")
                failed += 1
        else:
            print("❌")
            failed += 1
        
        # Progress every 10
        if (i + 1) % 10 == 0:
            print(f"\n   📊 Progress: {success} success, {failed} failed")
            print(f"   🧠 Images saved to database for AI learning\n")
    
    # Final summary
    print("\n" + "="*70)
    print("  GENERATION COMPLETE!")
    print("="*70)
    print(f"\n📊 Results:")
    print(f"   ✅ Success: {success}")
    print(f"   ❌ Failed: {failed}")
    
    # Show what's in the database
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM images')
    total_images = cursor.fetchone()[0]
    
    cursor.execute('SELECT cup_size, COUNT(*) FROM images GROUP BY cup_size')
    cup_counts = cursor.fetchall()
    
    cursor.execute('SELECT breast_shape, COUNT(*) FROM images GROUP BY breast_shape')
    shape_counts = cursor.fetchall()
    
    print(f"\n🗄️ Database:")
    print(f"   Total images: {total_images}")
    print(f"   By cup size: {dict(cup_counts)}")
    print(f"   By shape: {dict(shape_counts)}")
    
    # Show memories
    memories = get_memories(conn)
    print(f"\n🧠 User Memories: {len(memories)}")
    for m in memories[:5]:
        print(f"   {'👍' if m['is_like'] else '👎'} {m['type']}: {m['content']}")
    
    print(f"\n📁 Output: G:\\Github\\ComfyUI\\output\\breast_*.png")
    print(f"\n✅ All images ready for user rating!")
    print(f"   Rate images to train AI on your preferences")
    
    conn.close()

if __name__ == "__main__":
    main()
