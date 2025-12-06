"""
Tribal Portrait Gallery Generator
Creates 40 professional tribal portraits (20 ceremonial + 20 warrior)
Uses extracted tags and user preferences
"""
import json
import random
import time
import urllib.request
from pathlib import Path

COMFY_URL = "http://localhost:8188"
PREFS_FILE = Path(r"c:\Users\Admin\civitai\data\user_preferences.json")
OUTPUT_PREFIX_A = "tribal_ceremonial"
OUTPUT_PREFIX_B = "tribal_warrior"

# Eye color variations (heterochromia)
EYE_COLORS = [
    "heterochromia eyes, one blue eye one green eye",
    "heterochromia eyes, one amber eye one blue eye",
    "heterochromia eyes, one violet eye one gold eye",
    "heterochromia eyes, one emerald eye one brown eye",
    "heterochromia eyes, one ice blue eye one hazel eye",
    "striking green eyes, cat eyes",
    "piercing blue eyes, detailed iris",
    "golden amber eyes, wolf eyes",
    "violet purple eyes, mystical",
    "turquoise eyes, oceanic"
]

# Face paint patterns
FACE_PAINT = [
    "geometric face paint, red and black patterns",
    "tribal war paint, white and red stripes",
    "ceremonial face paint, intricate symbols",
    "warrior markings, bold black lines",
    "ritual face paint, earth tone pigments",
    "shamanic patterns, spiritual symbols",
    "hunter face paint, camouflage patterns",
    "sacred geometry face paint",
    "ancestral markings, traditional patterns",
    "battle paint, fierce tribal design"
]

# Body paint patterns
BODY_PAINT = [
    "tribal body paint, geometric patterns on arms",
    "ceremonial body art, sacred symbols",
    "warrior markings on shoulders",
    "ritual paint on collarbone area",
    "traditional tribal patterns on back",
    "ancestral symbols on arms",
    "spiritual body art, natural pigments",
    "hunting tribe markings",
    "earth tone body paint accents",
    "bold tribal stripes on arms and shoulders"
]

# Ceremonial attire (Set A)
CEREMONIAL_ATTIRE = [
    "elaborate feather headdress, full ceremonial dress, beaded necklace layers",
    "ornate bone crown, flowing ceremonial robes, tribal jewelry",
    "massive feather crown, decorated leather dress, shell accessories",
    "ceremonial war bonnet, embroidered tribal gown, copper jewelry",
    "sacred headdress with feathers, ritual dress with patterns, turquoise jewelry",
    "elaborate horn headdress, ceremonial leather outfit, bone necklace",
    "feathered ceremonial crown, traditional woven dress, silver accessories",
    "ritual headdress, decorated hide dress, amber jewelry",
    "grand feather arrangement, ceremonial beaded outfit, jade accessories",
    "sacred war bonnet, traditional ceremonial wear, gold accents"
]

# Warrior attire (Set B)  
WARRIOR_ATTIRE = [
    "warrior headdress, leather armor top, arm bands",
    "battle feathers in hair, fitted leather vest, war bracelets",
    "hunter headband, tribal leather top, bone arm guards",
    "small feather crown, warrior chest piece, leather straps",
    "battle braids with feathers, leather shoulder armor, tribal bands",
    "warrior mohawk style, fitted hide top, war paint emphasis",
    "hunting tribe headpiece, minimal leather armor, tribal markings focus",
    "battle ready hair style, warrior leather outfit, bone accessories",
    "fierce warrior braids, tribal chest armor, arm tattoos",
    "combat feathers, fitted warrior gear, battle scars"
]

# Poses
POSES = [
    "standing proud, arms crossed, powerful stance",
    "looking over shoulder, mysterious gaze",
    "facing viewer, intense stare, commanding presence",
    "profile view, regal posture, dignified",
    "three quarter view, contemplative expression",
    "warrior stance, ready for battle",
    "seated on throne, royal presence",
    "holding ceremonial staff, authoritative",
    "hands on hips, confident pose",
    "looking up, spiritual connection"
]

# Lighting
LIGHTING = [
    "dramatic side lighting, deep shadows",
    "golden hour lighting, warm tones",
    "studio lighting, soft shadows",
    "firelight, warm orange glow",
    "moonlight, cool blue tones",
    "rim lighting, silhouette effect",
    "natural daylight, outdoor setting",
    "dramatic spotlight, dark background",
    "soft diffused light, ethereal",
    "harsh sunlight, high contrast"
]

# Skin tones
SKIN_TONES = [
    "dark mahogany skin, rich undertones",
    "caramel skin, warm golden undertones",
    "deep brown skin, natural glow",
    "olive skin, mediterranean tones",
    "tan skin, sun-kissed",
    "bronze skin, metallic sheen",
    "ebony skin, flawless complexion",
    "warm brown skin, healthy glow",
    "copper skin tone, radiant",
    "golden brown skin, luminous"
]

# Ages
AGES = ["21yo", "22yo", "23yo", "24yo", "25yo", "26yo", "27yo", "28yo"]

def load_preferences():
    with open(PREFS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_base_negative():
    """Comprehensive negative prompt"""
    return """EasyNegative, bad-hands-5, ng_deepnegative_v1_75t,
(child:2.0), (kid:2.0), (teen:2.0), (minor:2.0), (underage:2.0), (young:1.8),
(bad anatomy:1.4), (bad proportions:1.4), (deformed:1.4),
(extra fingers:1.5), (missing fingers:1.5), (fused fingers:1.4),
(mutated hands:1.4), (extra limbs:1.4), (missing limbs:1.4),
(low quality:1.5), (worst quality:1.5), (blurry:1.3),
(watermark:1.5), (text:1.5), (signature:1.4),
(cartoon:1.5), (anime:1.5), (3d render:1.4), (cgi:1.4),
(illustration:1.4), (painting:1.3), (sketch:1.4),
ugly, disfigured, deformed face, bad eyes"""

def build_ceremonial_prompt(index):
    """Build prompt for ceremonial attire (Set A)"""
    eyes = EYE_COLORS[index % len(EYE_COLORS)]
    face = FACE_PAINT[index % len(FACE_PAINT)]
    body = BODY_PAINT[index % len(BODY_PAINT)]
    attire = CEREMONIAL_ATTIRE[index % len(CEREMONIAL_ATTIRE)]
    pose = POSES[index % len(POSES)]
    light = LIGHTING[index % len(LIGHTING)]
    skin = SKIN_TONES[index % len(SKIN_TONES)]
    age = random.choice(AGES)
    
    return f"""masterpiece, best quality, 8k resolution, photorealistic, RAW photo, DSLR,
(adult woman:1.3), ({age}:1.2), (tribal warrior woman:1.2),

({eyes}:1.3), detailed iris, reflective eyes, expressive eyes,
({face}:1.3), detailed face paint, artistic makeup,
({body}:1.1),

({attire}:1.2),
tribal jewelry, feather accessories, bone ornaments,

({skin}:1.1), realistic skin texture, skin pores, natural skin,
(beautiful face:1.2), high cheekbones, defined jawline,
(medium breasts:1.0), (fit body:1.0), (toned:1.0),

({pose}:1.1),
({light}:1.2),
professional photography, fashion editorial, portrait,
sharp focus, detailed, high detail skin texture"""

def build_warrior_prompt(index):
    """Build prompt for warrior attire (Set B)"""
    eyes = EYE_COLORS[(index + 5) % len(EYE_COLORS)]
    face = FACE_PAINT[(index + 3) % len(FACE_PAINT)]
    body = BODY_PAINT[(index + 2) % len(BODY_PAINT)]
    attire = WARRIOR_ATTIRE[index % len(WARRIOR_ATTIRE)]
    pose = POSES[(index + 5) % len(POSES)]
    light = LIGHTING[(index + 3) % len(LIGHTING)]
    skin = SKIN_TONES[(index + 4) % len(SKIN_TONES)]
    age = random.choice(AGES)
    
    return f"""masterpiece, best quality, 8k resolution, photorealistic, RAW photo, DSLR,
(adult woman:1.3), ({age}:1.2), (fierce tribal warrior:1.2),

({eyes}:1.3), intense gaze, piercing eyes, detailed iris,
({face}:1.3), war paint, battle markings,
({body}:1.2), warrior body art,

({attire}:1.2),
leather accessories, bone jewelry, feather accents,

({skin}:1.1), realistic skin texture, battle-ready,
(beautiful fierce face:1.2), strong features, warrior expression,
(athletic body:1.1), (toned muscles:1.0), (fit:1.0),

({pose}:1.1),
({light}:1.2),
action photography, dramatic portrait,
sharp focus, high contrast, cinematic"""

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
                "strength_model": 0.65,
                "strength_clip": 0.65
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
                "steps": 35,
                "cfg": 7,
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
    """Queue prompt via API"""
    data = json.dumps({"prompt": workflow}).encode('utf-8')
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        return result.get('prompt_id')
    except Exception as e:
        print(f"   Error: {e}")
        return None

def wait_for_completion(prompt_id, timeout=180):
    """Wait for generation to complete"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}")
            history = json.loads(resp.read())
            if prompt_id in history:
                return True
        except:
            pass
        time.sleep(2)
    return False

def main():
    print("="*70)
    print("  TRIBAL PORTRAIT GALLERY GENERATOR")
    print("  40 Professional Portraits (20 Ceremonial + 20 Warrior)")
    print("="*70)
    
    # Check ComfyUI
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5)
        print("\n✅ ComfyUI connected")
    except:
        print("\n❌ ComfyUI not running! Start ComfyUI first.")
        return
    
    negative = build_base_negative()
    
    # === SET A: Ceremonial Attire (20 images) ===
    print("\n" + "="*70)
    print("  SET A: CEREMONIAL ATTIRE (20 images)")
    print("="*70)
    
    for i in range(20):
        print(f"\n[A-{i+1:02d}/20] Ceremonial Portrait")
        
        positive = build_ceremonial_prompt(i)
        eyes_used = EYE_COLORS[i % len(EYE_COLORS)].split(',')[0]
        print(f"   Eyes: {eyes_used}")
        print(f"   Paint: {FACE_PAINT[i % len(FACE_PAINT)].split(',')[0]}")
        
        workflow = create_workflow(positive, negative, OUTPUT_PREFIX_A)
        prompt_id = queue_prompt(workflow)
        
        if prompt_id:
            print(f"   Queued: {prompt_id[:8]}...")
            if wait_for_completion(prompt_id):
                print(f"   ✅ Complete!")
            else:
                print(f"   ⚠️ Timeout")
        else:
            print(f"   ❌ Failed to queue")
    
    # === SET B: Warrior Attire (20 images) ===
    print("\n" + "="*70)
    print("  SET B: WARRIOR ATTIRE (20 images)")
    print("="*70)
    
    for i in range(20):
        print(f"\n[B-{i+1:02d}/20] Warrior Portrait")
        
        positive = build_warrior_prompt(i)
        eyes_used = EYE_COLORS[(i+5) % len(EYE_COLORS)].split(',')[0]
        print(f"   Eyes: {eyes_used}")
        print(f"   Paint: {FACE_PAINT[(i+3) % len(FACE_PAINT)].split(',')[0]}")
        
        workflow = create_workflow(positive, negative, OUTPUT_PREFIX_B)
        prompt_id = queue_prompt(workflow)
        
        if prompt_id:
            print(f"   Queued: {prompt_id[:8]}...")
            if wait_for_completion(prompt_id):
                print(f"   ✅ Complete!")
            else:
                print(f"   ⚠️ Timeout")
        else:
            print(f"   ❌ Failed to queue")
    
    # Summary
    print("\n" + "="*70)
    print("  GALLERY GENERATION COMPLETE!")
    print("="*70)
    print(f"\n📁 Output Location: G:\\Github\\ComfyUI\\output\\")
    print(f"   Set A: {OUTPUT_PREFIX_A}_*.png (20 ceremonial)")
    print(f"   Set B: {OUTPUT_PREFIX_B}_*.png (20 warrior)")
    print(f"\n🎨 Features included:")
    print(f"   ✓ Heterochromia/unique eye colors")
    print(f"   ✓ Detailed face paint patterns")
    print(f"   ✓ Body paint artistic compositions")
    print(f"   ✓ Dramatic lighting variations")
    print(f"   ✓ Various skin tones")
    print(f"   ✓ Professional editorial styling")

if __name__ == "__main__":
    main()
