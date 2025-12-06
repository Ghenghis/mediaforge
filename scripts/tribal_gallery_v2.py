"""
Tribal Portrait Gallery Generator V2
UPDATED: Petite, small bust, toned muscles, detailed paint
"""
import json
import random
import time
import urllib.request
from pathlib import Path

COMFY_URL = "http://localhost:8188"
OUTPUT_PREFIX_A = "tribal_v2_ceremonial"
OUTPUT_PREFIX_B = "tribal_v2_warrior"

# ============================================================
# BODY TYPE - Petite, Small Frame, Toned
# ============================================================
BODY_TYPES = [
    "(petite:1.3), (small frame:1.2), (delicate build:1.1), (slim:1.2)",
    "(petite body:1.3), (slender:1.2), (small stature:1.1), (lithe:1.2)",
    "(tiny frame:1.2), (petite figure:1.3), (slim build:1.2), (delicate:1.1)",
    "(small body:1.2), (petite:1.3), (lightweight build:1.1), (slim waist:1.2)",
    "(compact body:1.2), (petite frame:1.3), (slender figure:1.2), (narrow waist:1.2)"
]

# ============================================================
# BREAST SIZE - Small: A, AA, AAA cups
# ============================================================
BREAST_SIZES = [
    "(flat chest:1.3), (very small breasts:1.2), (AAA cup:1.2), (nearly flat:1.2)",
    "(tiny breasts:1.3), (AA cup:1.2), (small bust:1.2), (minimal chest:1.2)",
    "(small breasts:1.2), (A cup:1.2), (petite bust:1.2), (modest chest:1.1)",
    "(very small bust:1.3), (flat:1.2), (small chest:1.2), (subtle curves:1.1)",
    "(micro breasts:1.2), (AAA cup:1.3), (flat chested:1.2), (boyish chest:1.1)"
]

# ============================================================
# MUSCLE TONE - Athletic, Defined, Visible
# ============================================================
MUSCLE_TONE = [
    "(extremely toned:1.3), (visible abs:1.3), (six pack abs:1.2), (defined stomach muscles:1.3), (athletic build:1.2), (lean muscle:1.2)",
    "(ripped abs:1.3), (toned stomach:1.3), (visible muscle definition:1.3), (athletic body:1.2), (muscular arms:1.2), (toned legs:1.2)",
    "(washboard abs:1.3), (extremely fit:1.2), (defined muscles:1.3), (toned physique:1.3), (visible obliques:1.2), (lean:1.2)",
    "(chiseled abs:1.3), (muscle tone:1.3), (fit body:1.2), (athletic frame:1.2), (defined arm muscles:1.2), (toned thighs:1.2)",
    "(sculpted abs:1.3), (visible stomach muscles:1.3), (extremely athletic:1.2), (defined physique:1.3), (toned core:1.3), (muscular definition:1.2)"
]

# ============================================================
# FACE PAINT - Detailed, Colorful, Patterns
# ============================================================
FACE_PAINT_DETAILED = [
    "(intricate geometric face paint:1.4), (red war paint stripes across cheeks:1.3), (black tribal lines on forehead:1.3), (white dot patterns around eyes:1.2), (detailed face markings:1.3)",
    "(elaborate ceremonial face paint:1.4), (bold red and black face patterns:1.3), (white clay face markings:1.3), (tribal symbols on cheeks:1.2), (geometric eye designs:1.3)",
    "(detailed war paint:1.4), (red ochre across face:1.3), (black charcoal lines:1.3), (white ash patterns:1.2), (fierce tribal markings:1.3), (painted forehead symbols:1.2)",
    "(colorful face paint:1.4), (red stripe across nose:1.3), (black geometric patterns on chin:1.3), (white circles around eyes:1.2), (yellow accent dots:1.2), (intricate designs:1.3)",
    "(bold tribal face paint:1.4), (crimson war stripes:1.3), (onyx black lines:1.3), (ivory white dots:1.2), (earth tone accents:1.2), (sacred face symbols:1.3)",
    "(ritual face paint:1.4), (blood red markings:1.3), (coal black patterns:1.3), (bone white highlights:1.2), (ochre yellow accents:1.2), (spiritual face designs:1.3)",
    "(warrior face paint:1.4), (scarlet diagonal stripes:1.3), (jet black eye lines:1.3), (chalk white forehead mark:1.2), (detailed tribal patterns:1.3)",
    "(shamanic face paint:1.4), (rust red swirls:1.3), (deep black symbols:1.3), (bright white streaks:1.2), (natural pigment colors:1.2), (mystical face markings:1.3)"
]

# ============================================================
# BODY PAINT - Extensive, Colorful, Detailed
# ============================================================
BODY_PAINT_DETAILED = [
    "(extensive body paint:1.4), (red tribal patterns on arms:1.3), (black geometric designs on torso:1.3), (white stripe patterns on stomach:1.3), (painted shoulders:1.2), (decorated collarbone:1.2), (body art covering arms and chest:1.3)",
    "(full body tribal paint:1.4), (red ochre on arms and shoulders:1.3), (black charcoal patterns on abdomen:1.3), (white clay designs on back:1.2), (intricate body markings:1.3), (painted ribs area:1.2)",
    "(colorful war paint on body:1.4), (crimson stripes down arms:1.3), (onyx patterns on stomach:1.3), (ivory dots on shoulders:1.2), (painted chest area:1.2), (tribal body art:1.3)",
    "(detailed body paint patterns:1.4), (red geometric shapes on torso:1.3), (black spiral designs on arms:1.3), (white accent lines on collarbone:1.2), (painted abs area:1.3), (decorated biceps:1.2)",
    "(elaborate tribal body art:1.4), (scarlet symbols on shoulders:1.3), (jet black lines on stomach:1.3), (chalk white highlights on arms:1.2), (intricate torso paint:1.3), (body covered in paint:1.2)",
    "(warrior body paint:1.4), (blood red war markings on arms:1.3), (coal black battle patterns on chest:1.3), (bone white tribal symbols:1.2), (painted muscle definition:1.3), (decorated abs:1.3)",
    "(ceremonial body paint:1.4), (rust red sacred patterns:1.3), (deep black spiritual symbols on torso:1.3), (bright white accent designs:1.2), (fully painted arms:1.2), (decorated upper body:1.3)",
    "(shamanic body art:1.4), (ochre swirl patterns on body:1.3), (charcoal tribal lines on stomach:1.3), (white clay dots on shoulders:1.2), (mystical body markings:1.3), (paint on visible skin:1.3)"
]

# ============================================================
# EYE COLORS - Heterochromia and Unique
# ============================================================
EYE_COLORS = [
    "(heterochromia:1.4), (one bright blue eye:1.3), (one vivid green eye:1.3), (different colored eyes:1.3), (detailed iris:1.2), (striking eyes:1.2)",
    "(heterochromia eyes:1.4), (one amber gold eye:1.3), (one ice blue eye:1.3), (mismatched eye colors:1.3), (captivating gaze:1.2)",
    "(heterochromia:1.4), (one violet purple eye:1.3), (one emerald green eye:1.3), (unique eye colors:1.3), (mesmerizing eyes:1.2)",
    "(striking heterochromia:1.4), (one golden eye:1.3), (one silver gray eye:1.3), (contrasting eye colors:1.3), (piercing gaze:1.2)",
    "(vivid heterochromia:1.4), (one turquoise eye:1.3), (one honey brown eye:1.3), (beautiful mismatched eyes:1.3), (intense stare:1.2)",
    "(piercing green eyes:1.3), (cat-like eyes:1.2), (vivid emerald iris:1.3), (detailed eye texture:1.2), (intense gaze:1.2)",
    "(striking blue eyes:1.3), (ice blue iris:1.3), (wolf-like eyes:1.2), (piercing stare:1.2), (detailed eye reflections:1.2)",
    "(golden amber eyes:1.3), (fierce predator eyes:1.2), (warm gold iris:1.3), (intense warrior gaze:1.2)"
]

# ============================================================
# CEREMONIAL ATTIRE - Minimal, Tribal
# ============================================================
CEREMONIAL_ATTIRE = [
    "(elaborate feather headdress:1.3), (minimal leather top:1.2), (beaded necklace layers:1.2), (bone jewelry:1.2), (feather accessories:1.2)",
    "(grand ceremonial headdress:1.3), (tribal leather chest piece:1.2), (shell necklaces:1.2), (arm bands:1.2), (feathered earrings:1.2)",
    "(ornate feather crown:1.3), (decorated hide top:1.2), (turquoise jewelry:1.3), (leather arm wraps:1.2), (bone piercings:1.2)",
    "(sacred war bonnet:1.3), (minimal chest covering:1.2), (copper jewelry:1.2), (feather hair accessories:1.2), (tribal bands:1.2)",
    "(ceremonial horn headdress:1.3), (leather strap top:1.2), (jade necklace:1.2), (bone arm guards:1.2), (feather cape:1.2)"
]

# ============================================================
# WARRIOR ATTIRE - Battle Ready, Minimal
# ============================================================
WARRIOR_ATTIRE = [
    "(warrior feathers in hair:1.2), (leather chest armor:1.2), (bone arm guards:1.2), (war bracelets:1.2), (battle-worn accessories:1.2)",
    "(battle braids with beads:1.2), (minimal leather armor:1.2), (tribal arm bands:1.3), (warrior necklace:1.2), (combat-ready gear:1.2)",
    "(hunter headband:1.2), (fitted hide vest:1.2), (leather wrist guards:1.2), (bone earrings:1.2), (warrior tattoos visible:1.2)",
    "(mohawk with feathers:1.2), (leather shoulder straps:1.2), (tribal chest piece:1.2), (arm tattoos:1.2), (fierce accessories:1.2)",
    "(warrior braids:1.2), (minimal battle top:1.2), (bone jewelry:1.2), (leather leg wraps:1.2), (combat feathers:1.2)"
]

# ============================================================
# POSES - Dynamic, Powerful
# ============================================================
POSES = [
    "(powerful stance:1.2), (hands on hips:1.1), (confident pose:1.2), (standing tall:1.1)",
    "(warrior stance:1.2), (arms crossed:1.1), (fierce expression:1.2), (ready for battle:1.1)",
    "(dynamic pose:1.2), (looking over shoulder:1.1), (mysterious gaze:1.2), (profile view:1.1)",
    "(athletic pose:1.2), (one hand raised:1.1), (intense stare:1.2), (commanding presence:1.1)",
    "(action pose:1.2), (mid-movement:1.1), (powerful expression:1.2), (dramatic angle:1.1)"
]

# ============================================================
# LIGHTING - Dramatic
# ============================================================
LIGHTING = [
    "(dramatic rim lighting:1.3), (deep shadows:1.2), (high contrast:1.2), (cinematic lighting:1.2)",
    "(golden hour light:1.3), (warm sunset tones:1.2), (soft shadows:1.1), (natural lighting:1.2)",
    "(firelight illumination:1.3), (warm orange glow:1.2), (flickering light:1.1), (dramatic shadows:1.2)",
    "(harsh side lighting:1.3), (strong shadows:1.2), (defined features:1.2), (dramatic contrast:1.2)",
    "(studio spotlight:1.3), (dark background:1.2), (focused light:1.2), (professional lighting:1.2)"
]

# ============================================================
# SKIN TONES
# ============================================================
SKIN_TONES = [
    "(dark mahogany skin:1.2), (rich deep brown:1.2), (flawless complexion:1.1), (natural skin texture:1.2)",
    "(caramel skin tone:1.2), (warm golden undertones:1.2), (smooth skin:1.1), (realistic skin:1.2)",
    "(bronze skin:1.2), (sun-kissed complexion:1.2), (healthy glow:1.1), (detailed skin pores:1.2)",
    "(ebony skin:1.2), (deep rich tone:1.2), (luminous skin:1.1), (natural beauty:1.2)",
    "(olive skin:1.2), (mediterranean tone:1.2), (warm complexion:1.1), (realistic texture:1.2)"
]

AGES = ["21yo", "22yo", "23yo", "24yo", "25yo"]

def build_negative():
    """Comprehensive negative prompt"""
    return """EasyNegative, bad-hands-5, ng_deepnegative_v1_75t,
(child:2.0), (kid:2.0), (teen:2.0), (minor:2.0), (underage:2.0), (young:1.8),
(large breasts:1.5), (big breasts:1.5), (huge breasts:1.6), (massive breasts:1.6), (medium breasts:1.3),
(busty:1.5), (big bust:1.5), (curvy:1.3), (voluptuous:1.4),
(chubby:1.4), (fat:1.5), (overweight:1.5), (obese:1.6), (thick:1.3),
(bad anatomy:1.4), (bad proportions:1.4), (deformed:1.4),
(extra fingers:1.5), (missing fingers:1.5), (fused fingers:1.4),
(mutated hands:1.4), (extra limbs:1.4), (missing limbs:1.4),
(low quality:1.5), (worst quality:1.5), (blurry:1.3),
(watermark:1.5), (text:1.5), (signature:1.4),
(cartoon:1.5), (anime:1.5), (3d render:1.4), (cgi:1.4),
(illustration:1.4), (painting:1.3), (sketch:1.4),
ugly, disfigured, soft body, no muscle definition, flabby"""

def build_ceremonial_prompt(index):
    """Build detailed ceremonial prompt"""
    body = BODY_TYPES[index % len(BODY_TYPES)]
    breast = BREAST_SIZES[index % len(BREAST_SIZES)]
    muscle = MUSCLE_TONE[index % len(MUSCLE_TONE)]
    eyes = EYE_COLORS[index % len(EYE_COLORS)]
    face_paint = FACE_PAINT_DETAILED[index % len(FACE_PAINT_DETAILED)]
    body_paint = BODY_PAINT_DETAILED[index % len(BODY_PAINT_DETAILED)]
    attire = CEREMONIAL_ATTIRE[index % len(CEREMONIAL_ATTIRE)]
    pose = POSES[index % len(POSES)]
    light = LIGHTING[index % len(LIGHTING)]
    skin = SKIN_TONES[index % len(SKIN_TONES)]
    age = random.choice(AGES)
    
    return f"""masterpiece, best quality, ultra detailed, 8k resolution, photorealistic, RAW photo, DSLR, professional photography,
(adult woman:1.3), ({age}:1.2), (tribal warrior woman:1.2),

{body},
{breast},
{muscle},

{eyes},
{face_paint},
{body_paint},

{attire},

{skin},
(beautiful face:1.2), (high cheekbones:1.1), (defined jawline:1.1), (fierce expression:1.2),

{pose},
{light},

(full body visible:1.1), (showing muscle definition:1.2), (detailed skin texture:1.2), (visible abs:1.2),
sharp focus, high detail, film grain, fashion photography, editorial portrait"""

def build_warrior_prompt(index):
    """Build detailed warrior prompt"""
    body = BODY_TYPES[(index + 2) % len(BODY_TYPES)]
    breast = BREAST_SIZES[(index + 1) % len(BREAST_SIZES)]
    muscle = MUSCLE_TONE[(index + 3) % len(MUSCLE_TONE)]
    eyes = EYE_COLORS[(index + 4) % len(EYE_COLORS)]
    face_paint = FACE_PAINT_DETAILED[(index + 2) % len(FACE_PAINT_DETAILED)]
    body_paint = BODY_PAINT_DETAILED[(index + 3) % len(BODY_PAINT_DETAILED)]
    attire = WARRIOR_ATTIRE[index % len(WARRIOR_ATTIRE)]
    pose = POSES[(index + 2) % len(POSES)]
    light = LIGHTING[(index + 1) % len(LIGHTING)]
    skin = SKIN_TONES[(index + 3) % len(SKIN_TONES)]
    age = random.choice(AGES)
    
    return f"""masterpiece, best quality, ultra detailed, 8k resolution, photorealistic, RAW photo, DSLR, action photography,
(adult woman:1.3), ({age}:1.2), (fierce tribal warrior:1.2),

{body},
{breast},
{muscle},

{eyes},
{face_paint},
{body_paint},

{attire},

{skin},
(warrior face:1.2), (intense expression:1.2), (battle-ready:1.1), (fierce beauty:1.2),

{pose},
{light},

(full body visible:1.1), (defined muscles:1.3), (athletic physique:1.2), (toned abs visible:1.3),
sharp focus, high contrast, cinematic, dramatic portrait"""

def create_workflow(positive, negative, prefix, model='CyberRealistic.safetensors'):
    """Create ComfyUI API workflow"""
    return {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": model}
        },
        "10": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["4", 0],
                "clip": ["4", 1],
                "lora_name": "add_detail.safetensors",
                "strength_model": 0.7,
                "strength_clip": 0.7
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 512, "height": 768, "batch_size": 1}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive, "clip": ["4", 1]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]}
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["10", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
                "seed": random.randint(0, 2**32),
                "steps": 40,
                "cfg": 7.5,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1.0
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": prefix}
        }
    }

def queue_prompt(workflow):
    data = json.dumps({"prompt": workflow}).encode('utf-8')
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read()).get('prompt_id')
    except Exception as e:
        print(f"   Error: {e}")
        return None

def wait_for_completion(prompt_id, timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            if prompt_id in json.loads(resp.read()):
                return True
        except:
            pass
        time.sleep(2)
    return False

def main():
    print("="*70)
    print("  TRIBAL PORTRAIT GALLERY V2")
    print("  Petite | Small Bust | Toned Muscles | Detailed Paint")
    print("="*70)
    
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        print("\n✅ ComfyUI connected")
    except:
        print("\n❌ ComfyUI not running!")
        return
    
    negative = build_negative()
    
    print("\n📋 UPDATED SPECIFICATIONS:")
    print("   • Body: Petite, small frame, delicate")
    print("   • Bust: A, AA, AAA cup sizes")
    print("   • Muscle: Extremely toned, visible abs, defined")
    print("   • Paint: Detailed face & body paint with colors")
    print("   • Eyes: Heterochromia variations")
    
    # SET A: Ceremonial
    print("\n" + "="*70)
    print("  SET A: CEREMONIAL (20 images)")
    print("="*70)
    
    for i in range(20):
        print(f"\n[A-{i+1:02d}/20] Ceremonial - Petite Warrior")
        prompt = build_ceremonial_prompt(i)
        
        # Show key tags
        breast_tag = BREAST_SIZES[i % len(BREAST_SIZES)].split(',')[0]
        muscle_tag = MUSCLE_TONE[i % len(MUSCLE_TONE)].split(',')[0]
        paint_tag = FACE_PAINT_DETAILED[i % len(FACE_PAINT_DETAILED)].split(',')[0]
        
        print(f"   Bust: {breast_tag}")
        print(f"   Body: {muscle_tag}")
        print(f"   Paint: {paint_tag}")
        
        workflow = create_workflow(prompt, negative, OUTPUT_PREFIX_A)
        prompt_id = queue_prompt(workflow)
        
        if prompt_id:
            print(f"   Queued: {prompt_id[:8]}...")
            if wait_for_completion(prompt_id):
                print(f"   ✅ Complete!")
            else:
                print(f"   ⚠️ Timeout")
    
    # SET B: Warrior
    print("\n" + "="*70)
    print("  SET B: WARRIOR (20 images)")
    print("="*70)
    
    for i in range(20):
        print(f"\n[B-{i+1:02d}/20] Warrior - Athletic Fighter")
        prompt = build_warrior_prompt(i)
        
        breast_tag = BREAST_SIZES[(i+1) % len(BREAST_SIZES)].split(',')[0]
        muscle_tag = MUSCLE_TONE[(i+3) % len(MUSCLE_TONE)].split(',')[0]
        paint_tag = BODY_PAINT_DETAILED[(i+3) % len(BODY_PAINT_DETAILED)].split(',')[0]
        
        print(f"   Bust: {breast_tag}")
        print(f"   Body: {muscle_tag}")
        print(f"   Paint: {paint_tag}")
        
        workflow = create_workflow(prompt, negative, OUTPUT_PREFIX_B)
        prompt_id = queue_prompt(workflow)
        
        if prompt_id:
            print(f"   Queued: {prompt_id[:8]}...")
            if wait_for_completion(prompt_id):
                print(f"   ✅ Complete!")
            else:
                print(f"   ⚠️ Timeout")
    
    print("\n" + "="*70)
    print("  V2 GALLERY COMPLETE!")
    print("="*70)
    print(f"\n📁 Output: G:\\Github\\ComfyUI\\output\\")
    print(f"   {OUTPUT_PREFIX_A}_*.png (20)")
    print(f"   {OUTPUT_PREFIX_B}_*.png (20)")

if __name__ == "__main__":
    main()
