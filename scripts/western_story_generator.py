"""
WESTERN STORIES - ACTOR & FAMILY IMAGE GENERATOR
=================================================
525 Actors with family members in authentic Western Era style
8K Color, Highest Detail, Family Appropriate (PG-R ratings)
Historical accuracy for 1850-1900 American West

Features:
- Actor profile generation (name, role, family ties)
- Family relationship mapping
- Era-accurate costume generation
- Content ratings: PG, PG-13, R (family appropriate)
- Batch generation with tracking
- Quality enhancement pipeline
"""
import sqlite3
import json
import random
import requests
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import hashlib

PORT = 8197
COMFYUI_URL = "http://localhost:8188"
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output\western_stories")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\western_stories.db")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 8K Quality Tags
QUALITY_8K = [
    "8k uhd", "ultra high resolution", "masterpiece", "best quality",
    "extremely detailed", "photorealistic", "hyperrealistic", "RAW photo",
    "professional photography", "sharp focus", "high detail skin texture",
    "subsurface scattering", "intricate details", "film grain"
]

# Western Era Lighting
WESTERN_LIGHTING = [
    "golden hour lighting", "natural sunlight", "dusty atmosphere",
    "warm desert light", "dramatic shadows", "cinematic lighting",
    "oil lamp lighting", "campfire glow", "sunset silhouette"
]

# Content Ratings for Families
CONTENT_RATINGS = {
    "PG": {
        "label": "PG - All Ages",
        "desc": "Fully clothed, modest western attire",
        "allowed": True,
        "clothing_level": "full_coverage"
    },
    "PG-13": {
        "label": "PG-13 - Teen",
        "desc": "Period-appropriate, slightly revealing",
        "allowed": True,
        "clothing_level": "modest"
    },
    "R": {
        "label": "R - Mature",
        "desc": "Adult western themes, saloon style",
        "allowed": True,
        "clothing_level": "revealing"
    }
}

# Western Character Roles
CHARACTER_ROLES = {
    "sheriff": {"male": "Sheriff", "female": "Sheriff's Wife"},
    "deputy": {"male": "Deputy", "female": "Deputy's Wife"},
    "rancher": {"male": "Rancher", "female": "Rancher's Wife"},
    "cowboy": {"male": "Cowboy", "female": "Cowgirl"},
    "outlaw": {"male": "Outlaw", "female": "Outlaw's Woman"},
    "banker": {"male": "Banker", "female": "Banker's Wife"},
    "doctor": {"male": "Doctor", "female": "Nurse"},
    "preacher": {"male": "Preacher", "female": "Preacher's Wife"},
    "saloon_owner": {"male": "Saloon Owner", "female": "Saloon Madame"},
    "blacksmith": {"male": "Blacksmith", "female": "Blacksmith's Wife"},
    "merchant": {"male": "Merchant", "female": "Merchant's Wife"},
    "farmer": {"male": "Farmer", "female": "Farmer's Wife"},
    "native_chief": {"male": "Native Chief", "female": "Chief's Wife"},
    "native_warrior": {"male": "Native Warrior", "female": "Native Woman"},
    "schoolteacher": {"male": "Schoolmaster", "female": "Schoolteacher"},
    "bartender": {"male": "Bartender", "female": "Barmaid"},
    "prospector": {"male": "Gold Prospector", "female": "Prospector's Wife"},
    "cavalry": {"male": "Cavalry Officer", "female": "Officer's Wife"},
    "judge": {"male": "Judge", "female": "Judge's Wife"},
    "mayor": {"male": "Mayor", "female": "Mayor's Wife"}
}

# Western Costumes by Role and Gender
WESTERN_COSTUMES = {
    "sheriff": {
        "male": "silver star badge, leather vest, white shirt, brown trousers, gun belt, cowboy hat, boots with spurs",
        "female": "modest prairie dress, apron, bonnet, leather boots, simple jewelry"
    },
    "cowboy": {
        "male": "worn leather chaps, dusty denim jeans, plaid shirt, bandana, wide-brimmed cowboy hat, leather boots, rope at belt",
        "female": "split riding skirt, embroidered blouse, cowgirl hat, leather boots, bandana"
    },
    "rancher": {
        "male": "quality leather vest, clean white shirt, dark trousers, expensive boots, silver belt buckle, felt cowboy hat",
        "female": "fine cotton dress, lace collar, cameo brooch, elegant bonnet, button boots"
    },
    "outlaw": {
        "male": "dusty black duster coat, worn hat, dark clothing, bandana mask around neck, multiple gun belts",
        "female": "dark riding outfit, leather corset, split skirt, boots, mysterious expression"
    },
    "saloon_owner": {
        "male": "fine embroidered vest, silk cravat, gold watch chain, pomaded hair, expensive suit",
        "female": "elegant satin dress, feather accessories, jewelry, styled hair, beauty mark"
    },
    "native_chief": {
        "male": "traditional headdress with feathers, beaded leather vest, ceremonial necklace, face paint",
        "female": "beaded buckskin dress, turquoise jewelry, braided hair, traditional patterns"
    },
    "cavalry": {
        "male": "blue cavalry uniform, brass buttons, yellow neckerchief, campaign hat, sword belt",
        "female": "fine Victorian dress, military-style jacket, elegant hat, gloves"
    },
    "preacher": {
        "male": "black suit, white collar, black hat, Bible in hand, serious expression",
        "female": "modest dark dress, high collar, simple cross necklace, hair in bun"
    },
    "doctor": {
        "male": "formal suit, vest, pocket watch, medical bag, spectacles, clean appearance",
        "female": "white apron over dark dress, hair pinned up, caring expression"
    },
    "merchant": {
        "male": "striped shirt, sleeve garters, apron, spectacles, friendly expression",
        "female": "practical dress, shop apron, hair in neat bun, welcoming smile"
    }
}

# Age Groups for Families
AGE_GROUPS = {
    "child": {"age_range": "8-12", "suffix": "young", "family_role": "child"},
    "teen": {"age_range": "13-17", "suffix": "teenage", "family_role": "teen"},
    "young_adult": {"age_range": "18-25", "suffix": "young adult", "family_role": "young"},
    "adult": {"age_range": "26-45", "suffix": "adult", "family_role": "parent"},
    "elder": {"age_range": "50-70", "suffix": "elderly", "family_role": "grandparent"}
}

# Ethnicities for Diversity
ETHNICITIES = [
    "caucasian american",
    "mexican",
    "native american",
    "african american",
    "chinese american",
    "irish american",
    "german american",
    "spanish"
]

# First Names for Generation
MALE_NAMES = [
    "William", "James", "John", "Thomas", "Henry", "Charles", "Robert", "Joseph",
    "Samuel", "Benjamin", "Ezekiel", "Wyatt", "Jesse", "Cole", "Hank", "Buck",
    "Clayton", "Dustin", "Earl", "Frank", "George", "Howard", "Isaac", "Jack",
    "Levi", "Marshall", "Nathan", "Oscar", "Pete", "Quinn", "Roy", "Silas",
    "Theodore", "Vernon", "Walter", "Zachariah", "Abraham", "Cornelius", "Daniel"
]

FEMALE_NAMES = [
    "Mary", "Elizabeth", "Sarah", "Margaret", "Emma", "Anna", "Clara", "Rose",
    "Grace", "Lucy", "Katherine", "Martha", "Ruth", "Dorothy", "Abigail", "Charlotte",
    "Eleanor", "Florence", "Georgia", "Hannah", "Ida", "Josephine", "Lillian",
    "Matilda", "Nellie", "Olive", "Prudence", "Rachel", "Susanna", "Virginia",
    "Winifred", "Adelaide", "Beatrice", "Constance", "Delilah", "Evangeline"
]

LAST_NAMES = [
    "Anderson", "Baker", "Carson", "Davis", "Evans", "Foster", "Garrett", "Harper",
    "Johnson", "Kelly", "Logan", "Mitchell", "Nelson", "O'Brien", "Parker", "Quinn",
    "Reynolds", "Smith", "Thompson", "Walker", "Williams", "Young", "Blackwood",
    "Calhoun", "Dalton", "Earp", "Holliday", "Masterson", "Ringo", "Starr"
]

NEGATIVE_PROMPT = """
bad anatomy, bad hands, extra fingers, missing fingers, deformed, disfigured,
mutated, ugly, blurry, low quality, worst quality, watermark, text, signature,
modern clothing, anachronistic items, cars, phones, electricity, plastic,
synthetic materials, neon colors, contemporary fashion, child, minor, underage
"""


class WesternDB:
    """Database for Western Stories Actor Management"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()
        
    def _init(self):
        self.conn.executescript('''
            -- Actors table
            CREATE TABLE IF NOT EXISTS actors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                gender TEXT,
                age_group TEXT,
                role TEXT,
                ethnicity TEXT,
                family_id TEXT,
                family_role TEXT,
                content_rating TEXT DEFAULT 'PG',
                created_at TEXT
            );
            
            -- Families table
            CREATE TABLE IF NOT EXISTS families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT UNIQUE,
                family_name TEXT,
                patriarch_id TEXT,
                matriarch_id TEXT,
                member_count INTEGER DEFAULT 0,
                created_at TEXT
            );
            
            -- Generated Images
            CREATE TABLE IF NOT EXISTS actor_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT,
                filename TEXT,
                prompt TEXT,
                negative TEXT,
                seed INTEGER,
                quality TEXT,
                content_rating TEXT,
                is_primary INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                created_at TEXT
            );
            
            -- Generation batches
            CREATE TABLE IF NOT EXISTS generation_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT UNIQUE,
                batch_type TEXT,
                actors_count INTEGER,
                images_generated INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                completed_at TEXT
            );
        ''')
        self.conn.commit()
        
    def create_actor(self, first_name, last_name, gender, age_group, role, 
                     ethnicity, family_id=None, family_role=None, content_rating='PG'):
        """Create a new actor"""
        actor_id = f"actor_{hashlib.md5(f'{first_name}{last_name}{role}'.encode()).hexdigest()[:8]}"
        
        try:
            self.conn.execute('''
                INSERT INTO actors (actor_id, first_name, last_name, gender, age_group, 
                                   role, ethnicity, family_id, family_role, content_rating, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (actor_id, first_name, last_name, gender, age_group, role, 
                  ethnicity, family_id, family_role, content_rating, datetime.now().isoformat()))
            self.conn.commit()
            return actor_id
        except sqlite3.IntegrityError:
            return actor_id  # Already exists
            
    def create_family(self, family_name):
        """Create a new family unit"""
        family_id = f"family_{hashlib.md5(family_name.encode()).hexdigest()[:8]}"
        
        try:
            self.conn.execute('''
                INSERT INTO families (family_id, family_name, created_at)
                VALUES (?, ?, ?)
            ''', (family_id, family_name, datetime.now().isoformat()))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass
        return family_id
        
    def generate_actors(self, count=525):
        """Generate the full cast of 525 actors with families"""
        actors_created = 0
        families_created = 0
        
        # Calculate distribution
        num_families = count // 4  # Average 4 members per family
        roles = list(CHARACTER_ROLES.keys())
        
        for i in range(num_families):
            # Create family
            last_name = random.choice(LAST_NAMES)
            family_id = self.create_family(f"The {last_name} Family")
            families_created += 1
            
            # Assign role to family
            role = random.choice(roles)
            ethnicity = random.choice(ETHNICITIES)
            
            # Father (adult male)
            father_name = random.choice(MALE_NAMES)
            father_id = self.create_actor(
                father_name, last_name, "male", "adult", role,
                ethnicity, family_id, "father", "PG"
            )
            actors_created += 1
            
            # Mother (adult female)
            mother_name = random.choice(FEMALE_NAMES)
            mother_id = self.create_actor(
                mother_name, last_name, "female", "adult", role,
                ethnicity, family_id, "mother", "PG"
            )
            actors_created += 1
            
            # Children (1-3)
            num_children = random.randint(1, 3)
            for c in range(num_children):
                child_gender = random.choice(["male", "female"])
                child_name = random.choice(MALE_NAMES if child_gender == "male" else FEMALE_NAMES)
                child_age = random.choice(["child", "teen", "young_adult"])
                self.create_actor(
                    child_name, last_name, child_gender, child_age, role,
                    ethnicity, family_id, f"child_{c+1}", "PG"
                )
                actors_created += 1
                
            # Update family with patriarch/matriarch
            self.conn.execute('''
                UPDATE families SET patriarch_id=?, matriarch_id=?, member_count=?
                WHERE family_id=?
            ''', (father_id, mother_id, 2 + num_children, family_id))
            
            if actors_created >= count:
                break
                
        self.conn.commit()
        return {"actors": actors_created, "families": families_created}
        
    def get_actors(self, limit=100, family_id=None, role=None):
        """Get actors with optional filters"""
        sql = 'SELECT * FROM actors WHERE 1=1'
        params = []
        
        if family_id:
            sql += ' AND family_id = ?'
            params.append(family_id)
        if role:
            sql += ' AND role = ?'
            params.append(role)
            
        sql += f' ORDER BY family_id, family_role LIMIT {limit}'
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]
        
    def get_families(self, limit=100):
        """Get all families"""
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM families ORDER BY family_name LIMIT ?', (limit,)
        ).fetchall()]
        
    def get_stats(self):
        """Get database statistics"""
        actors = self.conn.execute('SELECT COUNT(*) FROM actors').fetchone()[0]
        families = self.conn.execute('SELECT COUNT(*) FROM families').fetchone()[0]
        images = self.conn.execute('SELECT COUNT(*) FROM actor_images').fetchone()[0]
        rated = self.conn.execute('SELECT COUNT(*) FROM actor_images WHERE rating > 0').fetchone()[0]
        
        return {
            "actors": actors,
            "families": families,
            "images_generated": images,
            "images_rated": rated
        }
        
    def save_image(self, actor_id, filename, prompt, seed, content_rating):
        """Save generated image record"""
        self.conn.execute('''
            INSERT INTO actor_images (actor_id, filename, prompt, negative, seed, 
                                     content_rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (actor_id, filename, prompt, NEGATIVE_PROMPT, seed, content_rating, 
              datetime.now().isoformat()))
        self.conn.commit()


def build_actor_prompt(actor, quality_level="8k"):
    """Build prompt for actor image generation"""
    
    # Get costume for role
    role = actor.get('role', 'cowboy')
    gender = actor.get('gender', 'male')
    costumes = WESTERN_COSTUMES.get(role, WESTERN_COSTUMES['cowboy'])
    costume = costumes.get(gender, costumes['male'])
    
    # Age modifier
    age_group = actor.get('age_group', 'adult')
    age_info = AGE_GROUPS.get(age_group, AGE_GROUPS['adult'])
    age_desc = age_info['suffix']
    
    # Build character description
    ethnicity = actor.get('ethnicity', 'caucasian american')
    name = f"{actor.get('first_name', 'John')} {actor.get('last_name', 'Doe')}"
    role_title = CHARACTER_ROLES.get(role, {}).get(gender, 'Cowboy')
    
    # Base prompt
    prompt_parts = [
        f"portrait of {age_desc} {ethnicity} {gender}",
        f"character named {name}",
        f"Western {role_title} from 1870s American frontier",
        costume,
        "authentic period-accurate western clothing",
        "1870s Old West setting",
        "dusty frontier town background",
    ]
    
    # Add quality tags
    if quality_level == "8k":
        prompt_parts.extend(QUALITY_8K[:8])
    
    # Add lighting
    prompt_parts.extend(random.sample(WESTERN_LIGHTING, 3))
    
    # Face details
    prompt_parts.extend([
        "detailed face", "expressive eyes", "weathered skin texture",
        "period-accurate hairstyle", "authentic expression"
    ])
    
    return ", ".join(prompt_parts)


db = WesternDB()


class WesternAPI(BaseHTTPRequestHandler):
    """API Handler for Western Story Generator"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
        
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
            
        elif path == '/api/stats':
            self._json(db.get_stats())
            
        elif path == '/api/actors':
            params = parse_qs(urlparse(self.path).query)
            limit = int(params.get('limit', [100])[0])
            actors = db.get_actors(limit=limit)
            self._json(actors)
            
        elif path == '/api/families':
            families = db.get_families()
            self._json(families)
            
        elif path == '/api/roles':
            self._json(list(CHARACTER_ROLES.keys()))
            
        else:
            self._json({'error': 'not found'}, 404)
            
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/generate-actors':
            count = int(data.get('count', 525))
            result = db.generate_actors(count)
            self._json(result)
            
        elif path == '/api/generate-images':
            actor_ids = data.get('actor_ids', [])
            content_rating = data.get('content_rating', 'PG')
            queued = self._generate_actor_images(actor_ids, content_rating)
            self._json({'queued': queued})
            
        elif path == '/api/generate-family':
            family_id = data.get('family_id')
            content_rating = data.get('content_rating', 'PG')
            queued = self._generate_family_images(family_id, content_rating)
            self._json({'queued': queued})
            
        elif path == '/api/generate-all':
            content_rating = data.get('content_rating', 'PG')
            batch_size = int(data.get('batch_size', 50))
            queued = self._generate_all_actors(content_rating, batch_size)
            self._json({'queued': queued})
            
        else:
            self._json({'error': 'not found'}, 404)
            
    def _queue_comfyui(self, prompt, seed, filename):
        """Queue image to ComfyUI"""
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {
                "cfg": 7, "denoise": 1, "latent_image": ["5", 0], 
                "model": ["4", 0], "negative": ["7", 0], "positive": ["6", 0],
                "sampler_name": "euler_ancestral", "scheduler": "normal",
                "seed": seed, "steps": 35
            }},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {
                "ckpt_name": "CyberRealistic.safetensors"
            }},
            "5": {"class_type": "EmptyLatentImage", "inputs": {
                "batch_size": 1, "height": 1024, "width": 768
            }},
            "6": {"class_type": "CLIPTextEncode", "inputs": {
                "clip": ["4", 1], "text": prompt
            }},
            "7": {"class_type": "CLIPTextEncode", "inputs": {
                "clip": ["4", 1], "text": NEGATIVE_PROMPT
            }},
            "8": {"class_type": "VAEDecode", "inputs": {
                "samples": ["3", 0], "vae": ["4", 2]
            }},
            "9": {"class_type": "SaveImage", "inputs": {
                "filename_prefix": f"western/{filename}", "images": ["8", 0]
            }}
        }
        try:
            r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=10)
            return 'prompt_id' in r.json()
        except:
            return False
            
    def _generate_actor_images(self, actor_ids, content_rating):
        """Generate images for specific actors"""
        queued = 0
        for actor_id in actor_ids:
            actor = db.conn.execute('SELECT * FROM actors WHERE actor_id=?', (actor_id,)).fetchone()
            if not actor:
                continue
                
            actor_dict = dict(actor)
            prompt = build_actor_prompt(actor_dict)
            seed = random.randint(1, 2**31)
            filename = f"{actor_dict['first_name']}_{actor_dict['last_name']}_{seed}"
            
            if self._queue_comfyui(prompt, seed, filename):
                db.save_image(actor_id, filename, prompt, seed, content_rating)
                queued += 1
                
        return queued
        
    def _generate_family_images(self, family_id, content_rating):
        """Generate images for entire family"""
        actors = db.get_actors(limit=20, family_id=family_id)
        actor_ids = [a['actor_id'] for a in actors]
        return self._generate_actor_images(actor_ids, content_rating)
        
    def _generate_all_actors(self, content_rating, batch_size):
        """Generate images for all actors in batches"""
        actors = db.get_actors(limit=batch_size)
        actor_ids = [a['actor_id'] for a in actors]
        return self._generate_actor_images(actor_ids, content_rating)
        
    def log_message(self, *args): pass


HTML = '''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>Western Stories - Actor Generator</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Georgia', serif; background: linear-gradient(135deg, #2c1810 0%, #4a2c17 100%); color: #f4e4bc; min-height: 100vh; }

.container { max-width: 1400px; margin: 0 auto; padding: 20px; }

.header { text-align: center; padding: 30px; border-bottom: 3px solid #8b6914; margin-bottom: 30px; }
.header h1 { font-size: 2.5em; color: #d4a84b; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
.header p { color: #c9b896; margin-top: 10px; font-style: italic; }

.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
.stat { background: rgba(139, 105, 20, 0.3); border: 2px solid #8b6914; border-radius: 10px; padding: 20px; text-align: center; }
.stat-val { font-size: 2.5em; color: #d4a84b; font-weight: bold; }
.stat-lbl { color: #c9b896; font-size: 0.9em; margin-top: 5px; }

.panels { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }

.panel { background: rgba(44, 24, 16, 0.8); border: 2px solid #8b6914; border-radius: 10px; padding: 25px; }
.panel h2 { color: #d4a84b; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #8b6914; }

.btn { padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 1em; margin: 5px; transition: all 0.3s; }
.btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
.btn-gold { background: linear-gradient(135deg, #d4a84b 0%, #8b6914 100%); color: #2c1810; font-weight: bold; }
.btn-brown { background: linear-gradient(135deg, #6b4423 0%, #4a2c17 100%); color: #f4e4bc; border: 1px solid #8b6914; }

.form-group { margin-bottom: 15px; }
.form-group label { display: block; color: #c9b896; margin-bottom: 8px; }
.form-group input, .form-group select { width: 100%; padding: 10px; background: #3a2010; border: 1px solid #8b6914; color: #f4e4bc; border-radius: 4px; font-size: 1em; }
.form-group input:focus, .form-group select:focus { outline: none; border-color: #d4a84b; }

.actor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; max-height: 400px; overflow-y: auto; margin-top: 20px; padding: 10px; }
.actor-card { background: rgba(74, 44, 23, 0.5); border: 1px solid #8b6914; border-radius: 8px; padding: 15px; }
.actor-name { font-weight: bold; color: #d4a84b; }
.actor-role { font-size: 0.85em; color: #c9b896; }
.actor-family { font-size: 0.8em; color: #a08060; margin-top: 5px; }

.content-rating { display: flex; gap: 10px; margin: 15px 0; }
.rating-opt { flex: 1; padding: 15px; background: #3a2010; border: 2px solid #6b4423; border-radius: 8px; cursor: pointer; text-align: center; transition: all 0.2s; }
.rating-opt:hover { border-color: #8b6914; }
.rating-opt.active { border-color: #d4a84b; background: rgba(212, 168, 75, 0.2); }
.rating-opt .label { font-weight: bold; color: #d4a84b; }
.rating-opt .desc { font-size: 0.8em; color: #a08060; margin-top: 5px; }

.log { background: #1a0f08; border: 1px solid #4a2c17; border-radius: 6px; padding: 15px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 0.85em; color: #8b8b6a; }

.toast { position: fixed; bottom: 30px; right: 30px; background: #d4a84b; color: #2c1810; padding: 15px 25px; border-radius: 8px; font-weight: bold; display: none; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
.toast.show { display: block; animation: fadeInUp 0.3s; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🤠 Western Stories - Actor Generator</h1>
        <p>525 Actors & Families • 1850-1900 American West • 8K Quality</p>
    </div>
    
    <div class="stats">
        <div class="stat"><div class="stat-val" id="s-actors">0</div><div class="stat-lbl">Actors</div></div>
        <div class="stat"><div class="stat-val" id="s-families">0</div><div class="stat-lbl">Families</div></div>
        <div class="stat"><div class="stat-val" id="s-images">0</div><div class="stat-lbl">Images Generated</div></div>
        <div class="stat"><div class="stat-val" id="s-rated">0</div><div class="stat-lbl">Images Rated</div></div>
    </div>
    
    <div class="panels">
        <div class="panel">
            <h2>📋 Actor Management</h2>
            
            <div class="form-group">
                <label>Number of Actors to Generate</label>
                <input type="number" id="actor-count" value="525" min="1" max="1000">
            </div>
            
            <button class="btn btn-gold" onclick="generateActors()">🎭 Generate 525 Actors & Families</button>
            <button class="btn btn-brown" onclick="loadActors()">📜 View All Actors</button>
            
            <div class="actor-grid" id="actor-list"></div>
        </div>
        
        <div class="panel">
            <h2>🎨 Image Generation</h2>
            
            <div class="form-group">
                <label>Content Rating (Family Appropriate)</label>
                <div class="content-rating" id="content-ratings">
                    <div class="rating-opt active" data-r="PG" onclick="selectRating('PG')">
                        <div class="label">PG</div>
                        <div class="desc">All Ages - Fully Modest</div>
                    </div>
                    <div class="rating-opt" data-r="PG-13" onclick="selectRating('PG-13')">
                        <div class="label">PG-13</div>
                        <div class="desc">Teen - Period Accurate</div>
                    </div>
                    <div class="rating-opt" data-r="R" onclick="selectRating('R')">
                        <div class="label">R</div>
                        <div class="desc">Mature - Saloon Style</div>
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label>Batch Size</label>
                <input type="number" id="batch-size" value="50" min="1" max="100">
            </div>
            
            <button class="btn btn-gold" onclick="generateAllImages()">📸 Generate All Actor Images</button>
            <button class="btn btn-brown" onclick="generateFamilyImages()">👨‍👩‍👧‍👦 Generate Family Images</button>
            
            <h3 style="margin-top:20px;color:#c9b896">Generation Log</h3>
            <div class="log" id="log">Ready to generate Western actor images...</div>
        </div>
    </div>
</div>

<div class="toast" id="toast"></div>

<script>
let selectedRating = 'PG';

async function loadStats() {
    const s = await (await fetch('/api/stats')).json();
    document.getElementById('s-actors').textContent = s.actors;
    document.getElementById('s-families').textContent = s.families;
    document.getElementById('s-images').textContent = s.images_generated;
    document.getElementById('s-rated').textContent = s.images_rated;
}

async function loadActors() {
    const actors = await (await fetch('/api/actors?limit=100')).json();
    document.getElementById('actor-list').innerHTML = actors.map(a => `
        <div class="actor-card">
            <div class="actor-name">${a.first_name} ${a.last_name}</div>
            <div class="actor-role">${a.role} (${a.gender}, ${a.age_group})</div>
            <div class="actor-family">${a.family_role || 'Unknown'}</div>
        </div>
    `).join('');
}

function selectRating(r) {
    selectedRating = r;
    document.querySelectorAll('.rating-opt').forEach(el => {
        el.classList.toggle('active', el.dataset.r === r);
    });
}

async function generateActors() {
    const count = document.getElementById('actor-count').value;
    log('Generating ' + count + ' actors with families...');
    
    const r = await fetch('/api/generate-actors', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({count: parseInt(count)})
    });
    const d = await r.json();
    
    log(`Created ${d.actors} actors in ${d.families} families!`);
    toast(`Created ${d.actors} actors!`);
    loadStats();
    loadActors();
}

async function generateAllImages() {
    const batchSize = document.getElementById('batch-size').value;
    log(`Generating images for ${batchSize} actors (${selectedRating})...`);
    
    const r = await fetch('/api/generate-all', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({content_rating: selectedRating, batch_size: parseInt(batchSize)})
    });
    const d = await r.json();
    
    log(`Queued ${d.queued} images for generation!`);
    toast(`Queued ${d.queued} images!`);
    loadStats();
}

async function generateFamilyImages() {
    log('Generating family group images...');
    toast('Select a family first');
}

function log(msg) {
    const el = document.getElementById('log');
    const time = new Date().toLocaleTimeString();
    el.innerHTML = `[${time}] ${msg}<br>` + el.innerHTML;
}

function toast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3000);
}

// Init
loadStats();
loadActors();
</script>
</body>
</html>
'''


def main():
    print("=" * 60)
    print("  WESTERN STORIES - ACTOR & FAMILY GENERATOR")
    print("  525 Actors | 8K Quality | Family Appropriate")
    print("=" * 60)
    
    stats = db.get_stats()
    print(f"\n🤠 Actors: {stats['actors']}")
    print(f"👨‍👩‍👧 Families: {stats['families']}")
    print(f"📸 Images: {stats['images_generated']}")
    
    print(f"\n🌐 http://127.0.0.1:{PORT}")
    
    HTTPServer(('0.0.0.0', PORT), WesternAPI).serve_forever()


if __name__ == "__main__":
    main()
