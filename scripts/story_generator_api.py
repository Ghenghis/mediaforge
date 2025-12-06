"""
STORY GENERATOR API - Complete WPF Integration
===============================================
Comprehensive API for Western Story character generation
with full content rating system, actor management,
family relationships, and dialog templates.

Endpoints for WPF GUI integration.
"""
import sqlite3
import json
import random
import requests
import hashlib
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

# Configuration
PORT = 8197
COMFYUI_URL = "http://localhost:8188"
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output\western_stories")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\western_stories.db")
CONFIG_PATH = Path(r"c:\Users\Admin\civitai\data\story_content_ratings.json")
MODELS_CATALOG_PATH = Path(r"c:\Users\Admin\civitai\data\models_actors_catalog.json")

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load content ratings config
try:
    with open(CONFIG_PATH) as f:
        CONTENT_CONFIG = json.load(f)
except:
    CONTENT_CONFIG = {"ratings": {}}

# Load Models/Actors catalog
try:
    with open(MODELS_CATALOG_PATH) as f:
        MODELS_CATALOG = json.load(f)
except:
    MODELS_CATALOG = {"actor_roles_az": {}, "grey_areas": {}, "content_modes": {}}

# Content Ratings with full details
CONTENT_RATINGS = {
    "EL": {"name": "Extra Light", "family_safe": True, "min_coverage": 100, "transparency": 0},
    "L": {"name": "Light", "family_safe": True, "min_coverage": 95, "transparency": 0},
    "PG": {"name": "PG", "family_safe": True, "min_coverage": 90, "transparency": 0},
    "PG13": {"name": "PG-13", "family_safe": True, "min_coverage": 85, "transparency": 0},
    "PG17": {"name": "PG-17", "family_safe": True, "min_coverage": 80, "transparency": 0},
    "SOFT": {"name": "Soft", "family_safe": False, "min_coverage": 70, "transparency": 50,
             "note": "See-through fabrics OK, NOT nude"},
    "MED": {"name": "Medium", "family_safe": False, "min_coverage": 60, "transparency": 70},
    "R": {"name": "R-Rated", "family_safe": False, "min_coverage": 40, "transparency": 90},
    "HARD": {"name": "Hard", "family_safe": False, "min_coverage": 20, "transparency": 100},
    "HC": {"name": "Hardcore", "family_safe": False, "min_coverage": 10, "transparency": 100},
    "X": {"name": "X-Rated", "family_safe": False, "min_coverage": 5, "transparency": 100},
    "XXX": {"name": "XXX", "family_safe": False, "min_coverage": 0, "transparency": 100}
}

# Western Character Roles
CHARACTER_ROLES = {
    "sheriff": {"title": {"male": "Sheriff", "female": "Sheriff's Wife"}, 
                "costume": {"male": "silver star badge, leather vest, white shirt, gun belt, cowboy hat",
                           "female": "modest prairie dress, apron, bonnet"}},
    "deputy": {"title": {"male": "Deputy", "female": "Deputy's Wife"},
               "costume": {"male": "deputy badge, simple vest, work shirt, holster",
                          "female": "simple cotton dress, practical bonnet"}},
    "cowboy": {"title": {"male": "Cowboy", "female": "Cowgirl"},
               "costume": {"male": "worn chaps, denim jeans, plaid shirt, bandana, cowboy hat",
                          "female": "split riding skirt, embroidered blouse, cowgirl hat"}},
    "rancher": {"title": {"male": "Rancher", "female": "Rancher's Wife"},
                "costume": {"male": "quality leather vest, clean shirt, silver belt buckle",
                           "female": "fine cotton dress, lace collar, elegant bonnet"}},
    "outlaw": {"title": {"male": "Outlaw", "female": "Outlaw's Woman"},
               "costume": {"male": "dusty black duster, worn hat, bandana mask, multiple guns",
                          "female": "dark riding outfit, leather accents, mysterious"}},
    "banker": {"title": {"male": "Banker", "female": "Banker's Wife"},
               "costume": {"male": "formal suit, pocket watch, spectacles, clean appearance",
                          "female": "elegant Victorian dress, jewelry, styled hair"}},
    "doctor": {"title": {"male": "Doctor", "female": "Nurse"},
               "costume": {"male": "formal suit, vest, medical bag, spectacles",
                          "female": "white apron over dark dress, caring expression"}},
    "preacher": {"title": {"male": "Preacher", "female": "Preacher's Wife"},
                 "costume": {"male": "black suit, white collar, Bible, solemn expression",
                            "female": "modest dark dress, high collar, cross necklace"}},
    "saloon_owner": {"title": {"male": "Saloon Owner", "female": "Saloon Madame"},
                     "costume": {"male": "embroidered vest, silk cravat, gold watch chain",
                                "female": "elegant satin dress, feather accessories, styled hair"}},
    "merchant": {"title": {"male": "Merchant", "female": "Merchant's Wife"},
                 "costume": {"male": "striped shirt, sleeve garters, apron",
                            "female": "practical dress, shop apron, welcoming"}},
    "native_chief": {"title": {"male": "Native Chief", "female": "Chief's Wife"},
                     "costume": {"male": "traditional headdress, beaded vest, ceremonial necklace",
                                "female": "beaded buckskin dress, turquoise jewelry, braids"}},
    "cavalry": {"title": {"male": "Cavalry Officer", "female": "Officer's Wife"},
                "costume": {"male": "blue cavalry uniform, brass buttons, campaign hat",
                           "female": "elegant Victorian dress, military jacket"}},
    "schoolteacher": {"title": {"male": "Schoolmaster", "female": "Schoolteacher"},
                      "costume": {"male": "simple suit, spectacles, stern expression",
                                 "female": "modest high-collar dress, hair in bun, kind expression"}},
    "prospector": {"title": {"male": "Gold Prospector", "female": "Prospector's Wife"},
                   "costume": {"male": "worn overalls, pick axe, dusty hat, weathered face",
                              "female": "simple work dress, apron, practical"}},
    "bartender": {"title": {"male": "Bartender", "female": "Barmaid"},
                  "costume": {"male": "white shirt, vest, bow tie, apron",
                             "female": "period-appropriate serving attire"}},
    "farmer": {"title": {"male": "Farmer", "female": "Farmer's Wife"},
               "costume": {"male": "overalls, straw hat, work boots, weathered hands",
                          "female": "simple dress, apron, bonnet, hardworking"}},
    "judge": {"title": {"male": "Judge", "female": "Judge's Wife"},
              "costume": {"male": "formal black robes, stern expression, authority",
                         "female": "elegant formal dress, refined appearance"}},
    "mayor": {"title": {"male": "Mayor", "female": "Mayor's Wife"},
              "costume": {"male": "fine suit, top hat, pocket watch, prosperous",
                         "female": "finest Victorian dress, jewelry, society leader"}},
    "blacksmith": {"title": {"male": "Blacksmith", "female": "Blacksmith's Wife"},
                   "costume": {"male": "leather apron, muscular, soot-covered, forge",
                              "female": "practical dress, strong appearance"}}
}

# Name pools
MALE_NAMES = ["William", "James", "John", "Thomas", "Henry", "Charles", "Robert", "Joseph",
              "Samuel", "Benjamin", "Ezekiel", "Wyatt", "Jesse", "Cole", "Hank", "Buck",
              "Clayton", "Dustin", "Earl", "Frank", "George", "Howard", "Isaac", "Jack"]
FEMALE_NAMES = ["Mary", "Elizabeth", "Sarah", "Margaret", "Emma", "Anna", "Clara", "Rose",
                "Grace", "Lucy", "Katherine", "Martha", "Ruth", "Dorothy", "Abigail", "Charlotte"]
LAST_NAMES = ["Anderson", "Baker", "Carson", "Davis", "Evans", "Foster", "Garrett", "Harper",
              "Johnson", "Kelly", "Logan", "Mitchell", "Nelson", "O'Brien", "Parker", "Quinn"]

ETHNICITIES = ["caucasian american", "mexican", "native american", "african american",
               "chinese american", "irish american", "german american", "spanish"]

# Quality tags for 8K
QUALITY_8K = [
    "8k uhd", "ultra high resolution", "masterpiece", "best quality",
    "extremely detailed", "photorealistic", "hyperrealistic", "RAW photo",
    "sharp focus", "high detail skin texture", "subsurface scattering"
]

WESTERN_LIGHTING = ["golden hour lighting", "natural sunlight", "dusty atmosphere",
                    "warm desert light", "dramatic shadows", "cinematic lighting"]

NEGATIVE_PROMPT = """bad anatomy, bad hands, extra fingers, missing fingers, deformed, 
disfigured, mutated, ugly, blurry, low quality, worst quality, watermark, text, 
modern clothing, anachronistic items, cars, phones, electricity, plastic"""

# Add forbidden terms for child safety
FORBIDDEN_CHILD_TERMS = ["nude", "naked", "undressed", "revealing", "exposed", 
                         "suggestive", "provocative", "sexual", "explicit"]


class StoryDB:
    """Complete Story Database with Actor/Family/Dialog Management"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()
        
    def _init(self):
        self.conn.executescript('''
            -- Actors
            CREATE TABLE IF NOT EXISTS actors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                full_name TEXT,
                gender TEXT,
                age_group TEXT,
                age_years INTEGER,
                role TEXT,
                role_title TEXT,
                ethnicity TEXT,
                family_id TEXT,
                family_role TEXT,
                personality TEXT,
                content_rating TEXT DEFAULT 'PG',
                costume_description TEXT,
                created_at TEXT
            );
            
            -- Families
            CREATE TABLE IF NOT EXISTS families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT UNIQUE,
                family_name TEXT,
                patriarch_id TEXT,
                matriarch_id TEXT,
                member_count INTEGER DEFAULT 0,
                primary_role TEXT,
                content_rating TEXT DEFAULT 'PG',
                created_at TEXT
            );
            
            -- Generated Images
            CREATE TABLE IF NOT EXISTS actor_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT,
                family_id TEXT,
                filename TEXT,
                prompt TEXT,
                negative_prompt TEXT,
                seed INTEGER,
                content_rating TEXT,
                quality_level TEXT DEFAULT '8k',
                is_primary INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                status TEXT DEFAULT 'generated',
                created_at TEXT
            );
            
            -- Dialogs
            CREATE TABLE IF NOT EXISTS actor_dialogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT,
                scene_type TEXT,
                mood TEXT,
                dialog_text TEXT,
                context TEXT,
                created_at TEXT
            );
            
            -- Scenes
            CREATE TABLE IF NOT EXISTS story_scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scene_id TEXT UNIQUE,
                scene_name TEXT,
                scene_type TEXT,
                actors TEXT,
                setting TEXT,
                dialog_script TEXT,
                content_rating TEXT,
                created_at TEXT
            );
            
            -- Generation Queue
            CREATE TABLE IF NOT EXISTS generation_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT,
                prompt TEXT,
                content_rating TEXT,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                completed_at TEXT
            );
        ''')
        self.conn.commit()
        
    def create_actor(self, first_name, last_name, gender, age_group, role, 
                     ethnicity, family_id=None, family_role=None, content_rating='PG'):
        """Create a new actor with full details"""
        actor_id = f"actor_{hashlib.md5(f'{first_name}{last_name}{role}{random.randint(1,9999)}'.encode()).hexdigest()[:8]}"
        
        # Get role title
        role_info = CHARACTER_ROLES.get(role, CHARACTER_ROLES['cowboy'])
        role_title = role_info['title'].get(gender, role)
        costume = role_info['costume'].get(gender, "period-accurate western attire")
        
        # Calculate age
        age_map = {"child": random.randint(8, 12), "teen": random.randint(13, 17),
                   "young_adult": random.randint(18, 25), "adult": random.randint(26, 50),
                   "elder": random.randint(55, 75)}
        age_years = age_map.get(age_group, 30)
        
        # Ensure children have family-safe ratings only
        if age_group in ['child', 'teen']:
            if content_rating not in ['EL', 'L', 'PG', 'PG13']:
                content_rating = 'PG'
        
        full_name = f"{first_name} {last_name}"
        
        try:
            self.conn.execute('''
                INSERT INTO actors (actor_id, first_name, last_name, full_name, gender, 
                    age_group, age_years, role, role_title, ethnicity, family_id, 
                    family_role, content_rating, costume_description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (actor_id, first_name, last_name, full_name, gender, age_group, 
                  age_years, role, role_title, ethnicity, family_id, family_role, 
                  content_rating, costume, datetime.now().isoformat()))
            self.conn.commit()
            return actor_id
        except sqlite3.IntegrityError:
            return None
            
    def create_family(self, family_name, primary_role='rancher', content_rating='PG'):
        """Create a family unit"""
        family_id = f"fam_{hashlib.md5(f'{family_name}{random.randint(1,9999)}'.encode()).hexdigest()[:8]}"
        
        try:
            self.conn.execute('''
                INSERT INTO families (family_id, family_name, primary_role, content_rating, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (family_id, family_name, primary_role, content_rating, datetime.now().isoformat()))
            self.conn.commit()
            return family_id
        except:
            return None
            
    def generate_full_cast(self, count=525):
        """Generate the complete 525 actor cast with families"""
        actors_created = 0
        families_created = 0
        
        roles = list(CHARACTER_ROLES.keys())
        num_families = count // 4  # ~4 members per family
        
        for i in range(num_families):
            last_name = random.choice(LAST_NAMES)
            role = random.choice(roles)
            ethnicity = random.choice(ETHNICITIES)
            
            family_id = self.create_family(f"The {last_name} Family", role, 'PG')
            if not family_id:
                continue
            families_created += 1
            
            # Father
            father_id = self.create_actor(
                random.choice(MALE_NAMES), last_name, "male", "adult",
                role, ethnicity, family_id, "father", "PG"
            )
            if father_id:
                actors_created += 1
                
            # Mother
            mother_id = self.create_actor(
                random.choice(FEMALE_NAMES), last_name, "female", "adult",
                role, ethnicity, family_id, "mother", "PG"
            )
            if mother_id:
                actors_created += 1
                
            # Update family
            self.conn.execute('''UPDATE families SET patriarch_id=?, matriarch_id=? WHERE family_id=?''',
                            (father_id, mother_id, family_id))
            
            # Children (1-3)
            num_children = random.randint(1, 3)
            for c in range(num_children):
                child_gender = random.choice(["male", "female"])
                child_name = random.choice(MALE_NAMES if child_gender == "male" else FEMALE_NAMES)
                child_age = random.choice(["child", "teen", "young_adult"])
                child_id = self.create_actor(
                    child_name, last_name, child_gender, child_age,
                    role, ethnicity, family_id, f"child_{c+1}", "PG"
                )
                if child_id:
                    actors_created += 1
                    
            # Update member count
            self.conn.execute('''UPDATE families SET member_count=? WHERE family_id=?''',
                            (2 + num_children, family_id))
            
            if actors_created >= count:
                break
                
        self.conn.commit()
        return {"actors": actors_created, "families": families_created}
        
    def get_actors(self, limit=100, family_id=None, role=None, content_rating=None):
        """Get actors with filters"""
        sql = 'SELECT * FROM actors WHERE 1=1'
        params = []
        
        if family_id:
            sql += ' AND family_id = ?'
            params.append(family_id)
        if role:
            sql += ' AND role = ?'
            params.append(role)
        if content_rating:
            sql += ' AND content_rating = ?'
            params.append(content_rating)
            
        sql += f' ORDER BY family_id, family_role LIMIT {limit}'
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]
        
    def get_families(self, limit=100):
        """Get all families"""
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM families ORDER BY family_name LIMIT ?', (limit,)
        ).fetchall()]
        
    def get_stats(self):
        """Get database statistics"""
        return {
            "actors": self.conn.execute('SELECT COUNT(*) FROM actors').fetchone()[0],
            "families": self.conn.execute('SELECT COUNT(*) FROM families').fetchone()[0],
            "images": self.conn.execute('SELECT COUNT(*) FROM actor_images').fetchone()[0],
            "dialogs": self.conn.execute('SELECT COUNT(*) FROM actor_dialogs').fetchone()[0],
            "pending_queue": self.conn.execute("SELECT COUNT(*) FROM generation_queue WHERE status='pending'").fetchone()[0]
        }
        
    def save_image(self, actor_id, filename, prompt, negative, seed, content_rating, family_id=None):
        """Save generated image record"""
        self.conn.execute('''
            INSERT INTO actor_images (actor_id, family_id, filename, prompt, negative_prompt, 
                seed, content_rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (actor_id, family_id, filename, prompt, negative, seed, content_rating, 
              datetime.now().isoformat()))
        self.conn.commit()
        
    def add_to_queue(self, actor_id, prompt, content_rating, priority=5):
        """Add to generation queue"""
        self.conn.execute('''
            INSERT INTO generation_queue (actor_id, prompt, content_rating, priority, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (actor_id, prompt, content_rating, priority, datetime.now().isoformat()))
        self.conn.commit()


def build_actor_prompt(actor, content_rating='PG'):
    """Build complete prompt for actor with content rating compliance"""
    
    # Get base info
    gender = actor.get('gender', 'female')
    age_group = actor.get('age_group', 'adult')
    role = actor.get('role', 'cowboy')
    ethnicity = actor.get('ethnicity', 'caucasian american')
    costume = actor.get('costume_description', 'period-accurate western attire')
    name = actor.get('full_name', 'Unknown')
    
    # Get rating config
    rating_config = CONTENT_RATINGS.get(content_rating, CONTENT_RATINGS['PG'])
    
    # GUARDRAIL: Children and teens always get family-safe ratings
    if age_group in ['child', 'teen']:
        content_rating = 'PG'
        rating_config = CONTENT_RATINGS['PG']
    
    # Build age description
    age_desc = {
        "child": "young child",
        "teen": "teenage",
        "young_adult": "young adult",
        "adult": "adult",
        "elder": "elderly"
    }.get(age_group, "adult")
    
    # Build prompt parts
    parts = [
        f"portrait of {age_desc} {ethnicity} {gender}",
        f"western character from 1870s American frontier",
        costume,
        "authentic period-accurate western clothing",
        "1870s Old West setting"
    ]
    
    # Add rating-specific modifiers
    if rating_config['family_safe']:
        parts.extend(["modest attire", "fully clothed", "family-appropriate"])
    elif content_rating == 'SOFT':
        parts.extend(["elegant sheer fabric details", "fashion-forward", "tasteful"])
    
    # Add quality tags
    parts.extend(QUALITY_8K[:6])
    parts.extend(random.sample(WESTERN_LIGHTING, 2))
    parts.extend(["detailed face", "expressive eyes", "period hairstyle"])
    
    return ", ".join(parts)


def get_rating_negative(content_rating, age_group='adult'):
    """Get negative prompt with guardrails based on rating and age"""
    base_neg = NEGATIVE_PROMPT
    
    # GUARDRAIL: Always forbid child exploitation terms
    child_guard = ", ".join(FORBIDDEN_CHILD_TERMS)
    
    # Children/teens get extra protection
    if age_group in ['child', 'teen']:
        return f"{base_neg}, {child_guard}, child, minor, underage, teen, young"
    
    # Family-safe ratings
    if CONTENT_RATINGS.get(content_rating, {}).get('family_safe', True):
        return f"{base_neg}, {child_guard}, nude, naked, revealing, suggestive"
    
    # SOFT rating - allows sheer but not nude
    if content_rating == 'SOFT':
        return f"{base_neg}, {child_guard}, full nudity, explicit, graphic"
    
    # Adult ratings
    return f"{base_neg}, child, minor, underage, teen, kid, young"


# Database instance
db = StoryDB()


class StoryAPI(BaseHTTPRequestHandler):
    """Complete API for WPF Integration"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
        
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_GET(self):
        path = self.path.split('?')[0]
        params = parse_qs(urlparse(self.path).query)
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
            
        elif path == '/api/health':
            self._json({"status": "online", "version": "2.0"})
            
        elif path == '/api/stats':
            self._json(db.get_stats())
            
        elif path == '/api/actors':
            limit = int(params.get('limit', [100])[0])
            family_id = params.get('family_id', [None])[0]
            role = params.get('role', [None])[0]
            self._json(db.get_actors(limit=limit, family_id=family_id, role=role))
            
        elif path == '/api/families':
            self._json(db.get_families())
            
        elif path == '/api/roles':
            self._json([{"id": k, **v} for k, v in CHARACTER_ROLES.items()])
            
        elif path == '/api/content-ratings':
            self._json(CONTENT_RATINGS)
            
        elif path == '/api/content-ratings/full':
            self._json(CONTENT_CONFIG)
            
        # Models/Actors Catalog Endpoints
        elif path == '/api/models/catalog':
            self._json(MODELS_CATALOG)
            
        elif path == '/api/models/roles':
            # Get all roles A-Z
            self._json(MODELS_CATALOG.get('actor_roles_az', {}))
            
        elif path == '/api/models/roles-by-letter':
            letter = params.get('letter', ['A'])[0].upper()
            roles = MODELS_CATALOG.get('actor_roles_az', {}).get(letter, [])
            self._json(roles)
            
        elif path == '/api/models/grey-areas':
            self._json(MODELS_CATALOG.get('grey_areas', {}))
            
        elif path == '/api/models/content-modes':
            self._json(MODELS_CATALOG.get('content_modes', {}))
            
        elif path == '/api/models/age-groups':
            self._json(MODELS_CATALOG.get('age_groups', {}))
            
        elif path == '/api/models/story-themes':
            self._json(MODELS_CATALOG.get('story_themes', {}))
            
        elif path == '/api/models/family-structures':
            self._json(MODELS_CATALOG.get('family_structures', {}))
            
        elif path == '/api/models/validate-role':
            role = params.get('role', [''])[0]
            age_group = params.get('age_group', ['adult'])[0]
            mode = params.get('mode', ['FAMILY'])[0]
            result = self._validate_role_for_mode(role, age_group, mode)
            self._json(result)
            
        else:
            self._json({'error': 'not found'}, 404)
            
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/actors/generate':
            count = int(data.get('count', 525))
            result = db.generate_full_cast(count)
            self._json(result)
            
        elif path == '/api/images/generate':
            actor_ids = data.get('actor_ids', [])
            content_rating = data.get('content_rating', 'PG')
            queued = self._generate_images(actor_ids, content_rating)
            self._json({'queued': queued})
            
        elif path == '/api/images/generate-family':
            family_id = data.get('family_id')
            content_rating = data.get('content_rating', 'PG')
            queued = self._generate_family(family_id, content_rating)
            self._json({'queued': queued})
            
        elif path == '/api/images/generate-all':
            batch_size = int(data.get('batch_size', 50))
            content_rating = data.get('content_rating', 'PG')
            queued = self._generate_batch(batch_size, content_rating)
            self._json({'queued': queued})
            
        elif path == '/api/validate-content':
            prompt = data.get('prompt', '')
            rating = data.get('content_rating', 'PG')
            result = self._validate_content(prompt, rating)
            self._json(result)
            
        else:
            self._json({'error': 'not found'}, 404)
            
    def _queue_comfyui(self, prompt, negative, seed, filename):
        """Queue to ComfyUI"""
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {
                "cfg": 7.5, "denoise": 1, "latent_image": ["5", 0],
                "model": ["4", 0], "negative": ["7", 0], "positive": ["6", 0],
                "sampler_name": "dpmpp_2m_sde", "scheduler": "karras",
                "seed": seed, "steps": 40
            }},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {
                "ckpt_name": "CyberRealistic.safetensors"
            }},
            "5": {"class_type": "EmptyLatentImage", "inputs": {
                "batch_size": 1, "height": 1024, "width": 768
            }},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": prompt}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": negative}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage", "inputs": {
                "filename_prefix": f"western/{filename}", "images": ["8", 0]
            }}
        }
        try:
            r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow}, timeout=10)
            return 'prompt_id' in r.json()
        except:
            return False
            
    def _generate_images(self, actor_ids, content_rating):
        """Generate images for specific actors"""
        queued = 0
        for actor_id in actor_ids:
            actor = db.conn.execute('SELECT * FROM actors WHERE actor_id=?', (actor_id,)).fetchone()
            if not actor:
                continue
                
            actor_dict = dict(actor)
            prompt = build_actor_prompt(actor_dict, content_rating)
            negative = get_rating_negative(content_rating, actor_dict.get('age_group', 'adult'))
            seed = random.randint(1, 2**31)
            filename = f"{actor_dict['first_name']}_{actor_dict['last_name']}_{seed}"
            
            if self._queue_comfyui(prompt, negative, seed, filename):
                db.save_image(actor_id, filename, prompt, negative, seed, content_rating,
                            actor_dict.get('family_id'))
                queued += 1
                
        return queued
        
    def _generate_family(self, family_id, content_rating):
        """Generate images for entire family"""
        actors = db.get_actors(limit=20, family_id=family_id)
        actor_ids = [a['actor_id'] for a in actors]
        return self._generate_images(actor_ids, content_rating)
        
    def _generate_batch(self, batch_size, content_rating):
        """Generate images for batch of actors"""
        actors = db.get_actors(limit=batch_size)
        actor_ids = [a['actor_id'] for a in actors]
        return self._generate_images(actor_ids, content_rating)
        
    def _validate_content(self, prompt, rating):
        """Validate prompt against content rating"""
        rating_config = CONTENT_RATINGS.get(rating, CONTENT_RATINGS['PG'])
        violations = []
        
        prompt_lower = prompt.lower()
        
        # Check for forbidden terms
        for term in FORBIDDEN_CHILD_TERMS:
            if term in prompt_lower:
                if rating_config['family_safe']:
                    violations.append(f"Term '{term}' not allowed in family-safe rating")
                    
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'rating': rating,
            'family_safe': rating_config['family_safe']
        }
    
    def _validate_role_for_mode(self, role, age_group, mode):
        """Validate if a role is allowed for given age group and content mode"""
        age_groups = MODELS_CATALOG.get('age_groups', {})
        content_modes = MODELS_CATALOG.get('content_modes', {})
        roles_az = MODELS_CATALOG.get('actor_roles_az', {})
        
        result = {
            'valid': True,
            'role': role,
            'age_group': age_group,
            'mode': mode,
            'grey_areas': [],
            'warnings': [],
            'status': 'GREEN'  # GREEN, YELLOW, RED
        }
        
        # Check age group restrictions
        age_config = age_groups.get(age_group, {})
        allowed_modes = age_config.get('allowed_modes', ['FAMILY'])
        
        if mode not in allowed_modes:
            result['valid'] = False
            result['status'] = 'RED'
            result['warnings'].append(f"Age group '{age_group}' not allowed in mode '{mode}'")
            return result
        
        # Find role in catalog
        role_info = None
        for letter, roles in roles_az.items():
            for r in roles:
                if r.get('role', '').lower() == role.lower():
                    role_info = r
                    break
        
        if role_info:
            # Check if role requires specific mode
            required_mode = role_info.get('mode')
            if required_mode and required_mode != mode:
                if mode == 'FAMILY' and required_mode in ['MATURE', 'ADULT']:
                    result['valid'] = False
                    result['status'] = 'RED'
                    result['warnings'].append(f"Role '{role}' requires {required_mode} mode")
            
            # Check grey areas
            grey_area = role_info.get('grey_area')
            if grey_area:
                result['grey_areas'].append(grey_area)
                if result['status'] == 'GREEN':
                    result['status'] = 'YELLOW'
                result['warnings'].append(f"Grey area: {grey_area}")
            
            # Check age group
            allowed_ages = role_info.get('age_groups', ['adult'])
            if age_group not in allowed_ages:
                result['valid'] = False
                result['status'] = 'RED'
                result['warnings'].append(f"Role not available for age group '{age_group}'")
        
        return result
        
    def log_message(self, *args): pass


HTML = '''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>Story Generator - Western 525</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; }
.container { max-width: 1400px; margin: 0 auto; padding: 20px; }
.header { text-align: center; padding: 30px; border-bottom: 2px solid #4a4a6a; }
.header h1 { color: #00d4ff; font-size: 2em; }
.stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin: 20px 0; }
.stat { background: #2a2a4a; padding: 20px; border-radius: 8px; text-align: center; }
.stat-val { font-size: 2em; color: #00d4ff; font-weight: bold; }
.stat-lbl { color: #888; }
.panels { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.panel { background: #2a2a4a; border-radius: 8px; padding: 20px; }
.panel h2 { color: #00d4ff; margin-bottom: 15px; border-bottom: 1px solid #4a4a6a; padding-bottom: 10px; }
.btn { padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; margin: 5px; font-weight: bold; }
.btn-primary { background: linear-gradient(135deg, #00d4ff, #0099cc); color: #000; }
.btn-success { background: linear-gradient(135deg, #00ff88, #00cc6a); color: #000; }
.btn-warning { background: linear-gradient(135deg, #ffcc00, #ff9900); color: #000; }
.rating-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0; }
.rating-opt { padding: 15px; background: #1a1a2e; border: 2px solid #4a4a6a; border-radius: 8px; cursor: pointer; text-align: center; }
.rating-opt:hover { border-color: #00d4ff; }
.rating-opt.active { border-color: #00ff88; background: rgba(0,255,136,0.1); }
.rating-opt.family { border-left: 4px solid #00ff88; }
.rating-opt.adult { border-left: 4px solid #ff6b6b; }
.input { width: 100%; padding: 10px; background: #1a1a2e; border: 1px solid #4a4a6a; color: #fff; border-radius: 4px; margin: 10px 0; }
.log { background: #111; padding: 15px; border-radius: 4px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 0.85em; }
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🤠 Western Stories - 525 Actor Generator</h1>
        <p>Complete family-safe story book character system with 12 content rating levels</p>
    </div>
    
    <div class="stats">
        <div class="stat"><div class="stat-val" id="s-actors">0</div><div class="stat-lbl">Actors</div></div>
        <div class="stat"><div class="stat-val" id="s-families">0</div><div class="stat-lbl">Families</div></div>
        <div class="stat"><div class="stat-val" id="s-images">0</div><div class="stat-lbl">Images</div></div>
        <div class="stat"><div class="stat-val" id="s-dialogs">0</div><div class="stat-lbl">Dialogs</div></div>
        <div class="stat"><div class="stat-val" id="s-queue">0</div><div class="stat-lbl">In Queue</div></div>
    </div>
    
    <div class="panels">
        <div class="panel">
            <h2>📋 Actor Management</h2>
            <input type="number" class="input" id="actor-count" value="525" placeholder="Number of actors">
            <button class="btn btn-primary" onclick="generateActors()">🎭 Generate 525 Actors & Families</button>
            <button class="btn btn-success" onclick="loadActors()">📜 View Actors</button>
            
            <h3 style="margin-top:20px;color:#888">Content Rating</h3>
            <div class="rating-grid" id="ratings"></div>
        </div>
        
        <div class="panel">
            <h2>🎨 Image Generation</h2>
            <input type="number" class="input" id="batch-size" value="50" placeholder="Batch size">
            <button class="btn btn-primary" onclick="generateAll()">📸 Generate All Images</button>
            <button class="btn btn-warning" onclick="generateFamily()">👨‍👩‍👧 Generate Family</button>
            
            <h3 style="margin-top:20px;color:#888">Generation Log</h3>
            <div class="log" id="log">Ready...</div>
        </div>
    </div>
</div>

<script>
let selectedRating = 'PG';
const RATINGS = {
    'EL': {name: 'Extra Light', family: true},
    'L': {name: 'Light', family: true},
    'PG': {name: 'PG', family: true},
    'PG13': {name: 'PG-13', family: true},
    'PG17': {name: 'PG-17', family: true},
    'SOFT': {name: 'Soft', family: false},
    'MED': {name: 'Medium', family: false},
    'R': {name: 'R-Rated', family: false},
    'HARD': {name: 'Hard', family: false},
    'HC': {name: 'Hardcore', family: false},
    'X': {name: 'X-Rated', family: false},
    'XXX': {name: 'XXX', family: false}
};

function init() {
    loadStats();
    renderRatings();
}

function renderRatings() {
    const container = document.getElementById('ratings');
    container.innerHTML = Object.entries(RATINGS).map(([code, info]) => `
        <div class="rating-opt ${info.family ? 'family' : 'adult'} ${code === selectedRating ? 'active' : ''}" 
             onclick="selectRating('${code}')">
            <strong>${code}</strong><br>
            <small>${info.name}</small>
        </div>
    `).join('');
}

function selectRating(r) {
    selectedRating = r;
    renderRatings();
    log('Selected rating: ' + RATINGS[r].name);
}

async function loadStats() {
    const s = await (await fetch('/api/stats')).json();
    document.getElementById('s-actors').textContent = s.actors;
    document.getElementById('s-families').textContent = s.families;
    document.getElementById('s-images').textContent = s.images;
    document.getElementById('s-dialogs').textContent = s.dialogs;
    document.getElementById('s-queue').textContent = s.pending_queue;
}

async function generateActors() {
    const count = document.getElementById('actor-count').value;
    log('Generating ' + count + ' actors...');
    const r = await fetch('/api/actors/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({count: parseInt(count)})
    });
    const d = await r.json();
    log('Created ' + d.actors + ' actors in ' + d.families + ' families!');
    loadStats();
}

async function generateAll() {
    const size = document.getElementById('batch-size').value;
    log('Generating images for ' + size + ' actors (' + selectedRating + ')...');
    const r = await fetch('/api/images/generate-all', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({batch_size: parseInt(size), content_rating: selectedRating})
    });
    const d = await r.json();
    log('Queued ' + d.queued + ' images!');
    loadStats();
}

async function loadActors() {
    const actors = await (await fetch('/api/actors?limit=50')).json();
    log('Loaded ' + actors.length + ' actors');
    console.log(actors);
}

function generateFamily() {
    log('Select a family first');
}

function log(msg) {
    const el = document.getElementById('log');
    const time = new Date().toLocaleTimeString();
    el.innerHTML = '[' + time + '] ' + msg + '<br>' + el.innerHTML;
}

init();
</script>
</body>
</html>
'''


def main():
    print("=" * 60)
    print("  WESTERN STORIES - COMPLETE ACTOR GENERATOR")
    print("  525 Actors | 12 Content Ratings | WPF Ready")
    print("=" * 60)
    
    stats = db.get_stats()
    print(f"\n🎭 Actors: {stats['actors']}")
    print(f"👨‍👩‍👧 Families: {stats['families']}")
    print(f"📸 Images: {stats['images']}")
    print(f"📋 Queue: {stats['pending_queue']}")
    
    print(f"\n📊 Content Ratings: {len(CONTENT_RATINGS)}")
    print("   Family-Safe: EL, L, PG, PG13, PG17")
    print("   Adult: SOFT, MED, R, HARD, HC, X, XXX")
    
    print(f"\n🌐 http://127.0.0.1:{PORT}")
    print("   API ready for WPF integration")
    
    HTTPServer(('0.0.0.0', PORT), StoryAPI).serve_forever()


if __name__ == "__main__":
    main()
