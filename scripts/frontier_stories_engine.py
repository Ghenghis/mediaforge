"""
FRONTIER STORIES ENGINE
========================
Complete Actor & Family System with Real-Time Aging
525 Actors | Family Photos | Timeline-Based Aging | Theme Integration

Features:
- 525 unique actors with full profiles
- Family relationship mapping with aging
- Theme system (Western, Tribal, etc.)
- Story timeline integration
- Real-time age calculation based on story date
- Automatic age-appropriate content restrictions
- 35-60 family photos per family
- Full database persistence for recreation

Port: 8195
"""
import sqlite3
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import uuid

PORT = 8195
DB_PATH = Path(r"c:\Users\Admin\civitai\data\frontier_stories.db")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\output\frontier_stories")

# Ensure directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# THEMES SYSTEM
# ============================================

THEMES = {
    "western": {
        "name": "Western Frontier",
        "era": "1850-1900",
        "included_styles": ["cowboys", "frontier", "saloon", "ranch", "gold_rush"],
        "typical_roles": [
            "Sheriff", "Deputy", "Rancher", "Cowboy", "Cowgirl", "Outlaw",
            "Saloon Owner", "Banker", "Doctor", "Preacher", "Schoolteacher",
            "Prospector", "Cavalry Officer", "Blacksmith", "Merchant"
        ],
        "settings": ["frontier_town", "ranch", "desert", "saloon", "mountains", "prairie"],
        "costume_base": "western_1870s"
    },
    "tribal": {
        "name": "Tribal Nations",
        "era": "pre-colonial to 1900",
        "included_styles": ["native_american", "indigenous", "ceremonial", "traditional"],
        "typical_roles": [
            "Chief", "Warrior", "Medicine Woman", "Shaman", "Scout",
            "Weaver", "Hunter", "Elder", "Healer", "Chief's Daughter"
        ],
        "settings": ["village", "plains", "forest", "riverside", "mountains", "tipi_camp"],
        "costume_base": "native_traditional",
        "cultural_sensitivity": True
    },
    "victorian": {
        "name": "Victorian Era",
        "era": "1837-1901",
        "included_styles": ["high_society", "servants", "industrial", "colonial"],
        "typical_roles": [
            "Noble Lady", "Gentleman", "Maid", "Butler", "Governess",
            "Factory Worker", "Shopkeeper", "Doctor", "Nurse", "Teacher"
        ],
        "settings": ["manor_house", "city_street", "factory", "park", "ballroom"],
        "costume_base": "victorian_formal"
    },
    "fantasy": {
        "name": "Fantasy Realm",
        "era": "timeless",
        "included_styles": ["medieval_fantasy", "high_fantasy", "dark_fantasy"],
        "typical_roles": [
            "Princess", "Knight", "Sorceress", "Warrior", "Elf", "Fairy",
            "Dragon Rider", "Ranger", "Healer", "Oracle", "Queen"
        ],
        "settings": ["castle", "forest", "mountain", "village", "magic_realm"],
        "costume_base": "fantasy_medieval"
    },
    "asian": {
        "name": "Asian Historical",
        "era": "various",
        "included_styles": ["japanese", "chinese", "korean", "southeast_asian"],
        "typical_roles": [
            "Geisha", "Samurai", "Empress", "Ninja", "Monk",
            "Merchant", "Tea Master", "Warrior Princess"
        ],
        "settings": ["palace", "temple", "garden", "village", "dojo"],
        "costume_base": "asian_traditional"
    }
}

# ============================================
# AGE GROUPS & RESTRICTIONS
# ============================================

AGE_GROUPS = {
    "newborn": {"range": (0, 0), "max_rating": "EL", "description": "Newborn baby"},
    "infant": {"range": (0, 2), "max_rating": "EL", "description": "Infant/baby"},
    "toddler": {"range": (2, 5), "max_rating": "L", "description": "Toddler"},
    "child": {"range": (5, 12), "max_rating": "PG", "description": "Child"},
    "teen": {"range": (13, 17), "max_rating": "PG-13", "description": "Teenager"},
    "young_adult": {"range": (18, 25), "max_rating": "EXTREME", "description": "Young adult"},
    "adult": {"range": (26, 55), "max_rating": "EXTREME", "description": "Adult"},
    "elder": {"range": (56, 100), "max_rating": "R", "description": "Elder"}
}

# Rating hierarchy for comparison
RATING_HIERARCHY = [
    "EL", "L", "G", "PG", "PG-13", "NC-14", "NC-15", "NC-16", "NC-17",
    "NC-18", "NC-19", "NC-20", "SOFT", "SOFTCORE", "MED", "R",
    "HARD", "HC", "X", "XXX", "EXTREME"
]

# ============================================
# DATABASE
# ============================================

class FrontierStoriesDB:
    """Database for actors, families, and story timelines"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            -- Actors table (525 actors)
            CREATE TABLE IF NOT EXISTS actors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                gender TEXT NOT NULL,
                theme TEXT NOT NULL,
                role TEXT NOT NULL,
                family_id TEXT,
                family_role TEXT,
                ethnicity TEXT,
                physical_traits TEXT,
                personality TEXT,
                prompt_base TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Families table
            CREATE TABLE IF NOT EXISTS families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT UNIQUE NOT NULL,
                family_name TEXT NOT NULL,
                theme TEXT NOT NULL,
                patriarch_id TEXT,
                matriarch_id TEXT,
                generation_count INTEGER DEFAULT 1,
                member_count INTEGER DEFAULT 0,
                story_start_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Family relationships
            CREATE TABLE IF NOT EXISTS family_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT NOT NULL,
                related_actor_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                UNIQUE(actor_id, related_actor_id)
            );
            
            -- Story timelines
            CREATE TABLE IF NOT EXISTS story_timelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timeline_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                theme TEXT NOT NULL,
                start_date TEXT NOT NULL,
                current_date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Story events (for timeline progression)
            CREATE TABLE IF NOT EXISTS story_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                timeline_id TEXT NOT NULL,
                event_date TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                actors_involved TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Generated images
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT UNIQUE NOT NULL,
                actor_id TEXT,
                family_id TEXT,
                timeline_id TEXT,
                story_date TEXT,
                age_at_generation INTEGER,
                prompt TEXT NOT NULL,
                negative_prompt TEXT,
                rating TEXT NOT NULL,
                theme TEXT,
                image_path TEXT,
                generation_params TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Photo collections (100-500 per family, expandable)
            CREATE TABLE IF NOT EXISTS photo_collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id TEXT UNIQUE NOT NULL,
                family_id TEXT NOT NULL,
                timeline_id TEXT,
                name TEXT NOT NULL,
                collection_size TEXT DEFAULT 'standard',
                target_count INTEGER DEFAULT 300,
                current_count INTEGER DEFAULT 0,
                story_date_start TEXT,
                story_date_end TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Story chapters (link images to narrative)
            CREATE TABLE IF NOT EXISTS story_chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id TEXT UNIQUE NOT NULL,
                family_id TEXT NOT NULL,
                timeline_id TEXT,
                chapter_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                story_date_start TEXT,
                story_date_end TEXT,
                chat_context TEXT,
                image_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Chapter-Image linkage
            CREATE TABLE IF NOT EXISTS chapter_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id TEXT NOT NULL,
                image_id TEXT NOT NULL,
                sequence_order INTEGER,
                caption TEXT,
                UNIQUE(chapter_id, image_id)
            );
            
            -- Actor age snapshots (track age at each story point)
            CREATE TABLE IF NOT EXISTS actor_age_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT NOT NULL,
                story_date TEXT NOT NULL,
                age_years INTEGER NOT NULL,
                age_group TEXT NOT NULL,
                max_rating TEXT NOT NULL,
                restrictions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(actor_id, story_date)
            );
            
            -- Restriction releases (when actors age into new ratings)
            CREATE TABLE IF NOT EXISTS restriction_releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT NOT NULL,
                release_date TEXT NOT NULL,
                previous_max_rating TEXT,
                new_max_rating TEXT,
                age_at_release INTEGER,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_actors_family ON actors(family_id);
            CREATE INDEX IF NOT EXISTS idx_chapters_family ON story_chapters(family_id);
            CREATE INDEX IF NOT EXISTS idx_age_snapshots ON actor_age_snapshots(actor_id, story_date);
            CREATE INDEX IF NOT EXISTS idx_actors_theme ON actors(theme);
            CREATE INDEX IF NOT EXISTS idx_images_actor ON images(actor_id);
            CREATE INDEX IF NOT EXISTS idx_images_family ON images(family_id);
        ''')
        self.conn.commit()
    
    # ----- Actors -----
    def create_actor(self, first_name, last_name, birth_date, gender, theme, role, 
                     family_id=None, family_role=None, ethnicity=None, physical_traits=None,
                     personality=None, prompt_base=None):
        actor_id = f"ACT_{uuid.uuid4().hex[:8].upper()}"
        self.conn.execute('''
            INSERT INTO actors (actor_id, first_name, last_name, birth_date, gender, 
                               theme, role, family_id, family_role, ethnicity, 
                               physical_traits, personality, prompt_base)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (actor_id, first_name, last_name, birth_date, gender, theme, role,
              family_id, family_role, ethnicity, json.dumps(physical_traits) if physical_traits else None,
              personality, prompt_base))
        self.conn.commit()
        return actor_id
    
    def get_actor(self, actor_id):
        row = self.conn.execute('SELECT * FROM actors WHERE actor_id = ?', (actor_id,)).fetchone()
        return dict(row) if row else None
    
    def get_actors_by_family(self, family_id):
        rows = self.conn.execute('SELECT * FROM actors WHERE family_id = ?', (family_id,)).fetchall()
        return [dict(r) for r in rows]
    
    def get_actors_by_theme(self, theme):
        rows = self.conn.execute('SELECT * FROM actors WHERE theme = ?', (theme,)).fetchall()
        return [dict(r) for r in rows]
    
    def get_all_actors(self, limit=525):
        rows = self.conn.execute('SELECT * FROM actors LIMIT ?', (limit,)).fetchall()
        return [dict(r) for r in rows]
    
    def count_actors(self):
        return self.conn.execute('SELECT COUNT(*) FROM actors').fetchone()[0]
    
    # ----- Families -----
    def create_family(self, family_name, theme, patriarch_id=None, matriarch_id=None,
                      story_start_date=None):
        family_id = f"FAM_{uuid.uuid4().hex[:8].upper()}"
        self.conn.execute('''
            INSERT INTO families (family_id, family_name, theme, patriarch_id, 
                                  matriarch_id, story_start_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (family_id, family_name, theme, patriarch_id, matriarch_id, story_start_date))
        self.conn.commit()
        return family_id
    
    def get_family(self, family_id):
        row = self.conn.execute('SELECT * FROM families WHERE family_id = ?', (family_id,)).fetchone()
        return dict(row) if row else None
    
    def get_families_by_theme(self, theme):
        rows = self.conn.execute('SELECT * FROM families WHERE theme = ?', (theme,)).fetchall()
        return [dict(r) for r in rows]
    
    def update_family_member_count(self, family_id):
        count = self.conn.execute(
            'SELECT COUNT(*) FROM actors WHERE family_id = ?', (family_id,)
        ).fetchone()[0]
        self.conn.execute(
            'UPDATE families SET member_count = ? WHERE family_id = ?', (count, family_id)
        )
        self.conn.commit()
    
    # ----- Timelines -----
    def create_timeline(self, name, theme, start_date, description=None):
        timeline_id = f"TL_{uuid.uuid4().hex[:8].upper()}"
        self.conn.execute('''
            INSERT INTO story_timelines (timeline_id, name, theme, start_date, current_date, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timeline_id, name, theme, start_date, start_date, description))
        self.conn.commit()
        return timeline_id
    
    def advance_timeline(self, timeline_id, new_date):
        self.conn.execute(
            'UPDATE story_timelines SET current_date = ? WHERE timeline_id = ?',
            (new_date, timeline_id)
        )
        self.conn.commit()
    
    def get_timeline(self, timeline_id):
        row = self.conn.execute(
            'SELECT * FROM story_timelines WHERE timeline_id = ?', (timeline_id,)
        ).fetchone()
        return dict(row) if row else None
    
    # ----- Images -----
    def save_image(self, actor_id, family_id, timeline_id, story_date, age_at_generation,
                   prompt, negative_prompt, rating, theme, image_path, generation_params):
        image_id = f"IMG_{uuid.uuid4().hex[:12].upper()}"
        self.conn.execute('''
            INSERT INTO images (image_id, actor_id, family_id, timeline_id, story_date,
                               age_at_generation, prompt, negative_prompt, rating, theme,
                               image_path, generation_params)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (image_id, actor_id, family_id, timeline_id, story_date, age_at_generation,
              prompt, negative_prompt, rating, theme, image_path,
              json.dumps(generation_params) if generation_params else None))
        self.conn.commit()
        return image_id
    
    def get_images_by_actor(self, actor_id):
        rows = self.conn.execute('SELECT * FROM images WHERE actor_id = ?', (actor_id,)).fetchall()
        return [dict(r) for r in rows]
    
    def get_images_by_family(self, family_id):
        rows = self.conn.execute('SELECT * FROM images WHERE family_id = ?', (family_id,)).fetchall()
        return [dict(r) for r in rows]
    
    def count_images_by_family(self, family_id):
        return self.conn.execute(
            'SELECT COUNT(*) FROM images WHERE family_id = ?', (family_id,)
        ).fetchone()[0]
    
    def get_stats(self):
        return {
            'total_actors': self.conn.execute('SELECT COUNT(*) FROM actors').fetchone()[0],
            'total_families': self.conn.execute('SELECT COUNT(*) FROM families').fetchone()[0],
            'total_timelines': self.conn.execute('SELECT COUNT(*) FROM story_timelines').fetchone()[0],
            'total_images': self.conn.execute('SELECT COUNT(*) FROM images').fetchone()[0],
            'total_chapters': self.conn.execute('SELECT COUNT(*) FROM story_chapters').fetchone()[0],
            'total_collections': self.conn.execute('SELECT COUNT(*) FROM photo_collections').fetchone()[0]
        }
    
    # ----- Story Chapters -----
    def create_chapter(self, family_id, timeline_id, chapter_number, title, 
                       description=None, story_date_start=None, story_date_end=None):
        chapter_id = f"CH_{uuid.uuid4().hex[:8].upper()}"
        self.conn.execute('''
            INSERT INTO story_chapters 
            (chapter_id, family_id, timeline_id, chapter_number, title, description, 
             story_date_start, story_date_end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chapter_id, family_id, timeline_id, chapter_number, title, description,
              story_date_start, story_date_end))
        self.conn.commit()
        return chapter_id
    
    def get_chapter(self, chapter_id):
        row = self.conn.execute(
            'SELECT * FROM story_chapters WHERE chapter_id = ?', (chapter_id,)
        ).fetchone()
        return dict(row) if row else None
    
    def get_chapters_by_family(self, family_id):
        rows = self.conn.execute(
            'SELECT * FROM story_chapters WHERE family_id = ? ORDER BY chapter_number',
            (family_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    
    def link_image_to_chapter(self, chapter_id, image_id, sequence_order=None, caption=None):
        self.conn.execute('''
            INSERT OR REPLACE INTO chapter_images (chapter_id, image_id, sequence_order, caption)
            VALUES (?, ?, ?, ?)
        ''', (chapter_id, image_id, sequence_order, caption))
        
        # Update chapter image count
        count = self.conn.execute(
            'SELECT COUNT(*) FROM chapter_images WHERE chapter_id = ?', (chapter_id,)
        ).fetchone()[0]
        self.conn.execute(
            'UPDATE story_chapters SET image_count = ? WHERE chapter_id = ?', (count, chapter_id)
        )
        self.conn.commit()
    
    def get_chapter_images(self, chapter_id):
        rows = self.conn.execute('''
            SELECT ci.*, i.* FROM chapter_images ci
            JOIN images i ON ci.image_id = i.image_id
            WHERE ci.chapter_id = ?
            ORDER BY ci.sequence_order
        ''', (chapter_id,)).fetchall()
        return [dict(r) for r in rows]
    
    # ----- Photo Collections -----
    def create_collection(self, family_id, name, timeline_id=None, 
                          collection_size='standard', story_date_start=None, story_date_end=None):
        collection_id = f"COL_{uuid.uuid4().hex[:8].upper()}"
        
        # Get target count based on size
        size_targets = {'minimal': 100, 'standard': 300, 'expanded': 500, 'complete': 750}
        target_count = size_targets.get(collection_size, 300)
        
        self.conn.execute('''
            INSERT INTO photo_collections 
            (collection_id, family_id, timeline_id, name, collection_size, target_count,
             story_date_start, story_date_end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (collection_id, family_id, timeline_id, name, collection_size, target_count,
              story_date_start, story_date_end))
        self.conn.commit()
        return collection_id
    
    def get_collection(self, collection_id):
        row = self.conn.execute(
            'SELECT * FROM photo_collections WHERE collection_id = ?', (collection_id,)
        ).fetchone()
        return dict(row) if row else None
    
    def get_collections_by_family(self, family_id):
        rows = self.conn.execute(
            'SELECT * FROM photo_collections WHERE family_id = ?', (family_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    
    def update_collection_count(self, collection_id, count):
        self.conn.execute(
            'UPDATE photo_collections SET current_count = ? WHERE collection_id = ?',
            (count, collection_id)
        )
        self.conn.commit()
    
    # ----- Age Snapshots & Restriction Releases -----
    def save_age_snapshot(self, actor_id, story_date, age_years, age_group, max_rating, restrictions=None):
        self.conn.execute('''
            INSERT OR REPLACE INTO actor_age_snapshots 
            (actor_id, story_date, age_years, age_group, max_rating, restrictions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (actor_id, story_date, age_years, age_group, max_rating,
              json.dumps(restrictions) if restrictions else None))
        self.conn.commit()
    
    def get_age_snapshot(self, actor_id, story_date):
        row = self.conn.execute('''
            SELECT * FROM actor_age_snapshots 
            WHERE actor_id = ? AND story_date = ?
        ''', (actor_id, story_date)).fetchone()
        return dict(row) if row else None
    
    def record_restriction_release(self, actor_id, release_date, previous_rating, 
                                    new_rating, age_at_release, reason=None):
        self.conn.execute('''
            INSERT INTO restriction_releases 
            (actor_id, release_date, previous_max_rating, new_max_rating, age_at_release, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (actor_id, release_date, previous_rating, new_rating, age_at_release, reason))
        self.conn.commit()
    
    def get_restriction_releases(self, actor_id):
        rows = self.conn.execute(
            'SELECT * FROM restriction_releases WHERE actor_id = ? ORDER BY release_date',
            (actor_id,)
        ).fetchall()
        return [dict(r) for r in rows]


# ============================================
# AGING ENGINE
# ============================================

class AgingEngine:
    """Real-time age calculation based on story timeline"""
    
    @staticmethod
    def calculate_age(birth_date_str, story_date_str):
        """Calculate age at a specific story date"""
        try:
            birth = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            story = datetime.strptime(story_date_str, "%Y-%m-%d").date()
            
            age = relativedelta(story, birth)
            return age.years
        except:
            return 0
    
    @staticmethod
    def get_age_group(age):
        """Get age group for an age"""
        for group_name, group_data in AGE_GROUPS.items():
            min_age, max_age = group_data["range"]
            if min_age <= age <= max_age:
                return group_name, group_data
        return "adult", AGE_GROUPS["adult"]
    
    @staticmethod
    def get_max_rating_for_age(age):
        """Get maximum allowed rating for an age"""
        group_name, group_data = AgingEngine.get_age_group(age)
        return group_data["max_rating"]
    
    @staticmethod
    def is_rating_allowed(age, requested_rating):
        """Check if a rating is allowed for an age"""
        max_rating = AgingEngine.get_max_rating_for_age(age)
        
        max_idx = RATING_HIERARCHY.index(max_rating)
        req_idx = RATING_HIERARCHY.index(requested_rating) if requested_rating in RATING_HIERARCHY else 0
        
        return req_idx <= max_idx
    
    @staticmethod
    def get_age_appropriate_prompt_mods(age):
        """Get prompt modifications based on age"""
        group_name, _ = AgingEngine.get_age_group(age)
        
        mods = {
            "newborn": {
                "add": ["newborn baby", "swaddled", "sleeping peacefully", "innocent"],
                "remove": ["adult", "mature", "revealing"],
                "clothing": "fully swaddled or dressed"
            },
            "infant": {
                "add": ["baby", "infant", "cute", "adorable", "innocent smile"],
                "remove": ["adult", "mature", "revealing"],
                "clothing": "baby clothes, fully covered"
            },
            "toddler": {
                "add": ["toddler", "young child", "playful", "curious", "innocent"],
                "remove": ["adult", "mature", "revealing", "sexy"],
                "clothing": "child clothes, fully modest"
            },
            "child": {
                "add": ["child", "young", "innocent", "playful"],
                "remove": ["adult", "mature", "revealing", "sexy", "sensual"],
                "clothing": "age-appropriate, fully modest clothes"
            },
            "teen": {
                "add": ["teenager", "young", "youthful"],
                "remove": ["adult", "mature", "revealing", "sexy", "sensual", "explicit"],
                "clothing": "teen-appropriate, modest clothes"
            },
            "young_adult": {
                "add": ["young adult", "vibrant"],
                "remove": [],
                "clothing": "age-appropriate attire"
            },
            "adult": {
                "add": ["adult", "mature"],
                "remove": [],
                "clothing": "period-appropriate attire"
            },
            "elder": {
                "add": ["elderly", "wise", "dignified", "gray hair", "aged features"],
                "remove": ["sexy", "seductive"],
                "clothing": "dignified, respectful attire"
            }
        }
        
        return mods.get(group_name, mods["adult"])


# ============================================
# ACTOR GENERATOR
# ============================================

class ActorGenerator:
    """Generate 525 unique actors with profiles"""
    
    # Name pools by ethnicity/theme
    FIRST_NAMES = {
        "western_male": ["John", "William", "James", "Thomas", "Charles", "George", "Henry", 
                         "Robert", "Joseph", "Edward", "Frank", "Samuel", "David", "Benjamin",
                         "Daniel", "Michael", "Patrick", "Andrew", "Walter", "Frederick"],
        "western_female": ["Mary", "Elizabeth", "Sarah", "Margaret", "Emma", "Catherine",
                           "Anna", "Jane", "Emily", "Grace", "Rose", "Clara", "Lillian",
                           "Florence", "Edith", "Mabel", "Ethel", "Helen", "Alice", "Ruth"],
        "native_male": ["Running Wolf", "Eagle Feather", "Strong Bear", "Thunder Cloud",
                        "Swift River", "Red Hawk", "Silent Arrow", "Brave Heart",
                        "Morning Star", "White Buffalo"],
        "native_female": ["White Dove", "Morning Flower", "Silver Moon", "Dancing Water",
                          "Gentle Wind", "Bright Star", "Autumn Leaf", "Singing Bird",
                          "Golden Sun", "Sweet Grass"]
    }
    
    LAST_NAMES = {
        "western": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Davis", "Miller",
                    "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White",
                    "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"],
        "native": ["of the Plains", "of the Mountain", "of the River", "of the Forest",
                   "of the Sun Clan", "of the Wolf Clan", "of the Bear Clan"]
    }
    
    PHYSICAL_TRAITS = {
        "hair_color": ["black", "brown", "auburn", "blonde", "gray", "white", "red"],
        "eye_color": ["brown", "blue", "green", "hazel", "gray", "amber"],
        "build": ["slim", "athletic", "average", "stocky", "muscular", "petite"],
        "height": ["short", "average height", "tall", "very tall"],
        "features": ["sharp features", "soft features", "weathered face", "youthful face",
                     "strong jaw", "high cheekbones", "gentle eyes", "piercing gaze"]
    }
    
    def __init__(self, db: FrontierStoriesDB):
        self.db = db
    
    def generate_actor(self, theme, gender, role, family_id=None, family_role=None,
                       birth_year=None, ethnicity=None):
        """Generate a single actor"""
        
        # Determine ethnicity based on theme
        if ethnicity is None:
            if theme == "tribal" or role in ["Chief", "Warrior", "Medicine Woman", "Shaman"]:
                ethnicity = "native_american"
            elif theme == "western":
                ethnicity = "caucasian"
            else:
                ethnicity = random.choice(["caucasian", "hispanic", "african_american"])
        
        # Select names
        name_key = f"{'native' if ethnicity == 'native_american' else 'western'}_{gender}"
        first_name = random.choice(self.FIRST_NAMES.get(name_key, self.FIRST_NAMES["western_male"]))
        
        last_key = "native" if ethnicity == "native_american" else "western"
        last_name = random.choice(self.LAST_NAMES.get(last_key, self.LAST_NAMES["western"]))
        
        # Generate birth date
        if birth_year is None:
            # Default to 1850-1880 for adults
            birth_year = random.randint(1830, 1880)
        
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birth_date = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
        
        # Physical traits
        traits = {
            "hair": random.choice(self.PHYSICAL_TRAITS["hair_color"]),
            "eyes": random.choice(self.PHYSICAL_TRAITS["eye_color"]),
            "build": random.choice(self.PHYSICAL_TRAITS["build"]),
            "height": random.choice(self.PHYSICAL_TRAITS["height"]),
            "features": random.choice(self.PHYSICAL_TRAITS["features"])
        }
        
        # Generate base prompt
        prompt_base = self._generate_prompt_base(gender, role, traits, theme, ethnicity)
        
        # Personality
        personalities = ["brave", "gentle", "stern", "wise", "adventurous", "quiet",
                         "passionate", "calculating", "kind", "fierce"]
        personality = random.choice(personalities)
        
        # Create actor
        actor_id = self.db.create_actor(
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            gender=gender,
            theme=theme,
            role=role,
            family_id=family_id,
            family_role=family_role,
            ethnicity=ethnicity,
            physical_traits=traits,
            personality=personality,
            prompt_base=prompt_base
        )
        
        return actor_id
    
    def _generate_prompt_base(self, gender, role, traits, theme, ethnicity):
        """Generate base prompt for actor consistency"""
        gender_word = "man" if gender == "male" else "woman"
        
        prompt = f"{traits['height']} {gender_word} with {traits['hair']} hair, "
        prompt += f"{traits['eyes']} eyes, {traits['build']} build, {traits['features']}, "
        prompt += f"{role}, {theme} era, {ethnicity}"
        
        return prompt
    
    def generate_525_actors(self):
        """Generate all 525 actors with families"""
        # Target: 525 actors in ~50 families
        
        actors_created = 0
        families_created = 0
        
        # Western families (30 families, ~10 actors each = 300 actors)
        for i in range(30):
            family_name = f"{random.choice(self.LAST_NAMES['western'])} Family"
            family_id = self.db.create_family(
                family_name=family_name,
                theme="western",
                story_start_date="1870-01-01"
            )
            families_created += 1
            
            # Create family members
            actors_created += self._generate_family_members(
                family_id, "western", 
                min_members=8, max_members=12
            )
        
        # Tribal families (15 families, ~10 actors each = 150 actors)
        for i in range(15):
            family_name = f"{random.choice(['Wolf', 'Eagle', 'Bear', 'Thunder', 'River', 'Sun'])} Clan"
            family_id = self.db.create_family(
                family_name=family_name,
                theme="tribal",
                story_start_date="1865-01-01"
            )
            families_created += 1
            
            actors_created += self._generate_family_members(
                family_id, "tribal",
                min_members=8, max_members=12,
                ethnicity="native_american"
            )
        
        # Individual actors (75 actors without family)
        theme_roles = {
            "western": ["Sheriff", "Outlaw", "Prospector", "Bartender", "Doctor"],
            "tribal": ["Shaman", "Scout", "Trader"]
        }
        
        for _ in range(75):
            theme = random.choice(["western", "tribal"])
            role = random.choice(theme_roles[theme])
            gender = random.choice(["male", "female"])
            
            self.generate_actor(
                theme=theme,
                gender=gender,
                role=role,
                ethnicity="native_american" if theme == "tribal" else None
            )
            actors_created += 1
        
        return {
            "actors_created": actors_created,
            "families_created": families_created
        }
    
    def _generate_family_members(self, family_id, theme, min_members=6, max_members=12,
                                  ethnicity=None):
        """Generate a complete family with multiple generations"""
        
        num_members = random.randint(min_members, max_members)
        roles = THEMES[theme]["typical_roles"]
        
        created = 0
        
        # Patriarch (grandfather) - born 1810-1830
        patriarch_role = random.choice([r for r in roles if r not in ["Cowgirl", "Chief's Daughter"]])
        self.generate_actor(theme, "male", patriarch_role, family_id, "grandfather",
                           birth_year=random.randint(1810, 1830), ethnicity=ethnicity)
        created += 1
        
        # Matriarch (grandmother)
        self.generate_actor(theme, "female", f"{patriarch_role}'s Wife" if "'s Wife" not in patriarch_role else "Matriarch",
                           family_id, "grandmother",
                           birth_year=random.randint(1815, 1835), ethnicity=ethnicity)
        created += 1
        
        # Father - born 1835-1850
        father_role = random.choice(roles)
        self.generate_actor(theme, "male", father_role, family_id, "father",
                           birth_year=random.randint(1835, 1850), ethnicity=ethnicity)
        created += 1
        
        # Mother
        self.generate_actor(theme, "female", "Mother", family_id, "mother",
                           birth_year=random.randint(1840, 1855), ethnicity=ethnicity)
        created += 1
        
        # Children (2-4)
        num_children = random.randint(2, min(4, num_members - 4))
        for c in range(num_children):
            birth_year = random.randint(1860, 1880)
            gender = random.choice(["male", "female"])
            child_role = "Son" if gender == "male" else "Daughter"
            
            self.generate_actor(theme, gender, child_role, family_id, f"child_{c+1}",
                               birth_year=birth_year, ethnicity=ethnicity)
            created += 1
        
        # Extended family
        remaining = num_members - created
        for _ in range(remaining):
            gender = random.choice(["male", "female"])
            relation = random.choice(["uncle", "aunt", "cousin", "in-law"])
            birth_year = random.randint(1830, 1870)
            
            self.generate_actor(theme, gender, "Family Member", family_id, relation,
                               birth_year=birth_year, ethnicity=ethnicity)
            created += 1
        
        self.db.update_family_member_count(family_id)
        
        return created


# ============================================
# PHOTO GENERATOR
# ============================================

class FamilyPhotoGenerator:
    """Generate 300-500 family photos per family with story chapter integration"""
    
    # Image counts per collection type
    COLLECTION_SIZES = {
        "minimal": 100,
        "standard": 300,
        "expanded": 500,
        "complete": 750
    }
    
    # Photo categories with counts (total ~300-500)
    PHOTO_CATEGORIES = {
        "portraits": {
            "count_range": (40, 60),
            "types": ["formal_portrait", "casual_portrait", "individual", "group", "generation"]
        },
        "milestones": {
            "count_range": (30, 50),
            "types": ["birth", "birthday", "coming_of_age", "wedding", "funeral", "anniversary"]
        },
        "daily_life": {
            "count_range": (60, 100),
            "types": ["morning_routine", "meals", "chores", "relaxation", "evening"]
        },
        "work": {
            "count_range": (40, 70),
            "types": ["ranch_work", "farming", "hunting", "trading", "crafting", "building"]
        },
        "celebrations": {
            "count_range": (25, 40),
            "types": ["holiday", "harvest", "religious", "community", "victory"]
        },
        "relationships": {
            "count_range": (30, 50),
            "types": ["romantic", "friendship", "mentorship", "rivalry", "reconciliation"]
        },
        "adventures": {
            "count_range": (35, 60),
            "types": ["journey", "discovery", "conflict", "rescue", "exploration"]
        },
        "seasons": {
            "count_range": (40, 70),
            "types": ["spring", "summer", "autumn", "winter", "storm", "drought"]
        }
    }
    
    # Legacy simple types for backward compatibility
    PHOTO_TYPES = [
        "family_portrait", "wedding", "birthday", "holiday", "working",
        "celebration", "daily_life", "special_event", "outdoor", "indoor"
    ]
    
    def __init__(self, db: FrontierStoriesDB):
        self.db = db
        self.aging = AgingEngine()
    
    def generate_collection(self, family_id, timeline_id, collection_size='standard',
                            create_chapters=True):
        """
        Generate 100-500 photos for a family with story chapters
        
        collection_size: 'minimal' (100), 'standard' (300), 'expanded' (500), 'complete' (750)
        """
        
        family = self.db.get_family(family_id)
        if not family:
            return {"error": "Family not found"}
        
        actors = self.db.get_actors_by_family(family_id)
        if not actors:
            return {"error": "No actors in family"}
        
        timeline = self.db.get_timeline(timeline_id)
        if not timeline:
            return {"error": "Timeline not found"}
        
        # Get target count
        target_count = self.COLLECTION_SIZES.get(collection_size, 300)
        
        # Create collection
        collection_id = self.db.create_collection(
            family_id=family_id,
            name=f"{family['family_name']} - {collection_size.title()} Collection",
            timeline_id=timeline_id,
            collection_size=collection_size,
            story_date_start=timeline["start_date"],
            story_date_end=timeline["current_date"]
        )
        
        # Parse dates
        start_date = datetime.strptime(timeline["start_date"], "%Y-%m-%d")
        current_date = datetime.strptime(timeline["current_date"], "%Y-%m-%d")
        date_range_days = (current_date - start_date).days
        if date_range_days <= 0:
            date_range_days = 365 * 30  # 30 years default
        
        # Create chapters if requested
        chapters = []
        if create_chapters:
            chapters = self._create_story_chapters(family_id, timeline_id, start_date, date_range_days)
        
        # Generate photos by category
        all_photos = []
        category_counts = self._calculate_category_counts(target_count)
        
        for category, count in category_counts.items():
            category_photos = self._generate_category_photos(
                family_id, timeline_id, family, actors, 
                category, count, start_date, date_range_days, chapters
            )
            all_photos.extend(category_photos)
        
        # Update collection count
        self.db.update_collection_count(collection_id, len(all_photos))
        
        return {
            "collection_id": collection_id,
            "family_id": family_id,
            "family_name": family["family_name"],
            "target_count": target_count,
            "photos_generated": len(all_photos),
            "chapters_created": len(chapters),
            "categories": category_counts,
            "date_range": f"{timeline['start_date']} to {timeline['current_date']}"
        }
    
    def _calculate_category_counts(self, target_total):
        """Calculate how many photos per category to reach target"""
        counts = {}
        running_total = 0
        
        for category, config in self.PHOTO_CATEGORIES.items():
            min_c, max_c = config["count_range"]
            # Scale based on target
            scale = target_total / 300  # 300 is baseline
            category_count = int(random.randint(min_c, max_c) * scale)
            counts[category] = category_count
            running_total += category_count
        
        return counts
    
    def _create_story_chapters(self, family_id, timeline_id, start_date, date_range_days):
        """Create story chapters spanning the timeline"""
        
        chapters = []
        years = max(1, date_range_days // 365)
        
        # Chapter structure: ~1 chapter per 2 years
        num_chapters = max(5, years // 2)
        days_per_chapter = date_range_days // num_chapters
        
        chapter_titles = [
            "The Beginning", "New Arrivals", "Growing Pains", "Hard Times",
            "New Horizons", "The Journey", "Trials and Tribulations", 
            "Bonds of Family", "Coming of Age", "New Generations",
            "The Homestead", "Frontier Life", "Seasons Change", 
            "Family Ties", "Legacy"
        ]
        
        for i in range(num_chapters):
            chapter_start = start_date + relativedelta(days=i * days_per_chapter)
            chapter_end = start_date + relativedelta(days=(i + 1) * days_per_chapter - 1)
            
            chapter_id = self.db.create_chapter(
                family_id=family_id,
                timeline_id=timeline_id,
                chapter_number=i + 1,
                title=chapter_titles[i % len(chapter_titles)],
                description=f"Chapter {i+1} of the {family_id} story",
                story_date_start=chapter_start.strftime("%Y-%m-%d"),
                story_date_end=chapter_end.strftime("%Y-%m-%d")
            )
            
            chapters.append({
                "chapter_id": chapter_id,
                "number": i + 1,
                "start": chapter_start,
                "end": chapter_end
            })
        
        return chapters
    
    def _generate_category_photos(self, family_id, timeline_id, family, actors,
                                   category, count, start_date, date_range_days, chapters):
        """Generate photos for a specific category"""
        
        photos = []
        category_config = self.PHOTO_CATEGORIES.get(category, {})
        photo_types = category_config.get("types", ["general"])
        
        for i in range(count):
            # Random date
            days_offset = random.randint(0, date_range_days)
            photo_date = start_date + relativedelta(days=days_offset)
            photo_date_str = photo_date.strftime("%Y-%m-%d")
            
            # Select actors
            num_actors = random.randint(1, min(6, len(actors)))
            selected_actors = random.sample(actors, num_actors)
            
            # Calculate ages and restrictions
            actor_data = []
            min_allowed_rating = "EXTREME"
            
            for actor in selected_actors:
                age = self.aging.calculate_age(actor["birth_date"], photo_date_str)
                age_group, _ = self.aging.get_age_group(age)
                max_rating = self.aging.get_max_rating_for_age(age)
                
                # Track strictest restriction
                if RATING_HIERARCHY.index(max_rating) < RATING_HIERARCHY.index(min_allowed_rating):
                    min_allowed_rating = max_rating
                
                # Save age snapshot
                self.db.save_age_snapshot(
                    actor["actor_id"], photo_date_str, age, age_group, max_rating
                )
                
                # Check for restriction release
                self._check_restriction_release(actor, photo_date_str, age, max_rating)
                
                mods = self.aging.get_age_appropriate_prompt_mods(age)
                actor_data.append({
                    "actor_id": actor["actor_id"],
                    "name": f"{actor['first_name']} {actor['last_name']}",
                    "age": age,
                    "age_group": age_group,
                    "max_rating": max_rating,
                    "clothing": mods["clothing"]
                })
            
            # Build prompt
            photo_type = random.choice(photo_types)
            theme_settings = THEMES.get(family["theme"], THEMES["western"])
            setting = random.choice(theme_settings["settings"])
            
            prompt = self._build_photo_prompt(
                actor_data, category, photo_type, setting, 
                family["theme"], min_allowed_rating
            )
            negative = self._build_negative_prompt(min_allowed_rating)
            
            # Save image
            image_id = self.db.save_image(
                actor_id=actor_data[0]["actor_id"] if len(actor_data) == 1 else None,
                family_id=family_id,
                timeline_id=timeline_id,
                story_date=photo_date_str,
                age_at_generation=actor_data[0]["age"] if len(actor_data) == 1 else None,
                prompt=prompt,
                negative_prompt=negative,
                rating=min_allowed_rating,
                theme=family["theme"],
                image_path=None,
                generation_params={
                    "category": category,
                    "photo_type": photo_type,
                    "setting": setting,
                    "actors": [a["actor_id"] for a in actor_data],
                    "age_restrictions": {a["actor_id"]: a["max_rating"] for a in actor_data}
                }
            )
            
            # Link to chapter
            matching_chapter = self._find_chapter_for_date(chapters, photo_date)
            if matching_chapter:
                self.db.link_image_to_chapter(
                    matching_chapter["chapter_id"], image_id, 
                    sequence_order=i, caption=f"{category}: {photo_type}"
                )
            
            photos.append({
                "image_id": image_id,
                "date": photo_date_str,
                "category": category,
                "type": photo_type,
                "actors": len(actor_data),
                "max_rating": min_allowed_rating
            })
        
        return photos
    
    def _check_restriction_release(self, actor, story_date, age, current_max_rating):
        """Check if actor has aged into a new rating tier"""
        
        # Key age thresholds
        thresholds = {
            13: ("PG", "PG-13"),
            14: ("PG-13", "NC-14"),
            15: ("NC-14", "NC-15"),
            16: ("NC-15", "NC-16"),
            17: ("NC-16", "NC-17"),
            18: ("NC-17", "NC-18"),
            21: ("R", "EXTREME")
        }
        
        if age in thresholds:
            prev_rating, new_rating = thresholds[age]
            self.db.record_restriction_release(
                actor["actor_id"],
                story_date,
                prev_rating,
                new_rating,
                age,
                f"Actor turned {age}, restrictions updated"
            )
    
    def _find_chapter_for_date(self, chapters, photo_date):
        """Find which chapter a photo date falls into"""
        for chapter in chapters:
            if chapter["start"] <= photo_date <= chapter["end"]:
                return chapter
        return chapters[-1] if chapters else None
    
    def _build_photo_prompt(self, actors, category, photo_type, setting, theme, rating):
        """Build complete photo prompt"""
        
        # Quality
        quality = "8k uhd, masterpiece, highly detailed, photorealistic, sharp focus"
        
        # Scene description
        scene_desc = f"{category} scene, {photo_type}, {setting}"
        
        # Actor descriptions
        actor_descs = []
        for a in actors[:4]:  # Limit for prompt length
            desc = f"{a['age_group']} ({a['age']} years), {a['clothing']}"
            actor_descs.append(desc)
        
        # Combine
        prompt = f"{quality}, {theme} era, {scene_desc}, "
        prompt += "characters: " + ", ".join(actor_descs)
        prompt += f", period-accurate {theme} setting, natural lighting"
        
        return prompt
    
    # Legacy method for backward compatibility
    def generate_family_photos(self, family_id, timeline_id, num_photos=300):
        """Generate photos for a family across timeline (legacy)"""
        
        # Determine collection size
        if num_photos <= 100:
            size = 'minimal'
        elif num_photos <= 300:
            size = 'standard'
        elif num_photos <= 500:
            size = 'expanded'
        else:
            size = 'complete'
        
        return self.generate_collection(family_id, timeline_id, size)
    
    def generate_family_photos_legacy(self, family_id, timeline_id, num_photos=45):
        """Original legacy method"""
        
        family = self.db.get_family(family_id)
        if not family:
            return {"error": "Family not found"}
        
        actors = self.db.get_actors_by_family(family_id)
        if not actors:
            return {"error": "No actors in family"}
        
        timeline = self.db.get_timeline(timeline_id)
        if not timeline:
            return {"error": "Timeline not found"}
        
        photos_generated = []
        start_date = datetime.strptime(timeline["start_date"], "%Y-%m-%d")
        current_date = datetime.strptime(timeline["current_date"], "%Y-%m-%d")
        
        # Distribute photos across timeline
        date_range = (current_date - start_date).days
        if date_range <= 0:
            date_range = 365  # Default 1 year
        
        for i in range(num_photos):
            # Random date within timeline
            days_offset = random.randint(0, date_range)
            photo_date = start_date + relativedelta(days=days_offset)
            photo_date_str = photo_date.strftime("%Y-%m-%d")
            
            # Select actors for this photo (2-8 family members)
            num_actors = random.randint(2, min(8, len(actors)))
            selected_actors = random.sample(actors, num_actors)
            
            # Calculate ages and check restrictions
            actor_prompts = []
            min_allowed_rating = "EXTREME"
            
            for actor in selected_actors:
                age = self.aging.calculate_age(actor["birth_date"], photo_date_str)
                age_group, _ = self.aging.get_age_group(age)
                max_rating = self.aging.get_max_rating_for_age(age)
                
                # Track minimum allowed rating
                if RATING_HIERARCHY.index(max_rating) < RATING_HIERARCHY.index(min_allowed_rating):
                    min_allowed_rating = max_rating
                
                # Get age-appropriate modifications
                mods = self.aging.get_age_appropriate_prompt_mods(age)
                
                # Build actor prompt
                actor_prompt = {
                    "actor_id": actor["actor_id"],
                    "name": f"{actor['first_name']} {actor['last_name']}",
                    "age": age,
                    "age_group": age_group,
                    "base_prompt": actor.get("prompt_base", ""),
                    "age_mods": mods,
                    "clothing": mods["clothing"]
                }
                actor_prompts.append(actor_prompt)
            
            # Photo type and scene
            photo_type = random.choice(self.PHOTO_TYPES)
            theme_settings = THEMES.get(family["theme"], THEMES["western"])
            setting = random.choice(theme_settings["settings"])
            
            # Build combined prompt
            prompt = self._build_family_photo_prompt(
                actor_prompts, photo_type, setting, family["theme"], min_allowed_rating
            )
            
            # Negative prompt
            negative = self._build_negative_prompt(min_allowed_rating)
            
            # Save photo record
            image_id = self.db.save_image(
                actor_id=None,  # Group photo
                family_id=family_id,
                timeline_id=timeline_id,
                story_date=photo_date_str,
                age_at_generation=None,
                prompt=prompt,
                negative_prompt=negative,
                rating=min_allowed_rating,
                theme=family["theme"],
                image_path=None,  # To be set after generation
                generation_params={
                    "photo_type": photo_type,
                    "setting": setting,
                    "actors": [a["actor_id"] for a in actor_prompts]
                }
            )
            
            photos_generated.append({
                "image_id": image_id,
                "photo_date": photo_date_str,
                "photo_type": photo_type,
                "actors": len(actor_prompts),
                "max_rating": min_allowed_rating,
                "prompt": prompt[:100] + "..."
            })
        
        return {
            "family_id": family_id,
            "photos_generated": len(photos_generated),
            "photos": photos_generated
        }
    
    def _build_family_photo_prompt(self, actor_prompts, photo_type, setting, theme, rating):
        """Build a complete prompt for family photo"""
        
        # Quality tags
        quality = "8k uhd, masterpiece, highly detailed, photorealistic, sharp focus"
        
        # Photo type description
        photo_desc = {
            "family_portrait": "formal family portrait, posed, looking at camera",
            "wedding": "wedding celebration, festive, joyful",
            "birthday": "birthday celebration, cake, gifts",
            "holiday": "holiday gathering, festive decorations",
            "working": "working scene, daily activities",
            "celebration": "celebration, happy moments",
            "daily_life": "candid daily life scene",
            "special_event": "special occasion, formal",
            "outdoor": "outdoor scene, natural lighting",
            "indoor": "indoor scene, warm lighting"
        }
        
        # Build character descriptions
        char_descs = []
        for actor in actor_prompts:
            age = actor["age"]
            name = actor["name"]
            age_group = actor["age_group"]
            clothing = actor["clothing"]
            
            char_desc = f"{age_group} ({age} years old), {clothing}"
            char_descs.append(char_desc)
        
        # Combine
        prompt = f"{quality}, {photo_desc.get(photo_type, 'family photo')}, "
        prompt += f"{theme} era setting, {setting}, "
        prompt += "family group: " + ", ".join(char_descs[:4])  # Limit for prompt length
        
        # Add era-appropriate lighting
        lighting = THEMES.get(theme, {}).get("costume_base", "period accurate")
        prompt += f", {lighting}, natural period lighting"
        
        return prompt
    
    def _build_negative_prompt(self, rating):
        """Build negative prompt based on rating"""
        
        base_neg = "blurry, low quality, watermark, text, modern items, anachronistic"
        
        # Add rating-specific negatives
        if rating in ["EL", "L", "G", "PG", "PG-13"]:
            base_neg += ", nude, naked, revealing, suggestive, adult content, nsfw, explicit"
        
        if rating in ["EL", "L"]:
            base_neg += ", scary, violent, weapons drawn, blood"
        
        return base_neg


# ============================================
# API
# ============================================

db = FrontierStoriesDB()
actor_gen = ActorGenerator(db)
photo_gen = FamilyPhotoGenerator(db)


class FrontierStoriesAPI(BaseHTTPRequestHandler):
    """API Handler"""
    
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
        
        if path == '/':
            stats = db.get_stats()
            self._json({
                'service': 'Frontier Stories Engine',
                'version': '1.0',
                'themes': list(THEMES.keys()),
                **stats
            })
        
        elif path == '/api/stats':
            self._json(db.get_stats())
        
        elif path == '/api/themes':
            self._json(THEMES)
        
        elif path == '/api/actors':
            actors = db.get_all_actors()
            self._json({'count': len(actors), 'actors': actors})
        
        elif path.startswith('/api/actor/'):
            actor_id = path.split('/')[-1]
            actor = db.get_actor(actor_id)
            if actor:
                self._json(actor)
            else:
                self._json({'error': 'Actor not found'}, 404)
        
        elif path == '/api/families':
            families = [dict(r) for r in db.conn.execute('SELECT * FROM families').fetchall()]
            self._json({'count': len(families), 'families': families})
        
        elif path.startswith('/api/family/'):
            parts = path.split('/')
            family_id = parts[-1]
            
            if len(parts) > 4 and parts[-2] == "actors":
                family_id = parts[-2]
                actors = db.get_actors_by_family(family_id)
                self._json({'count': len(actors), 'actors': actors})
            else:
                family = db.get_family(family_id)
                if family:
                    actors = db.get_actors_by_family(family_id)
                    family['members'] = actors
                    self._json(family)
                else:
                    self._json({'error': 'Family not found'}, 404)
        
        elif path == '/api/timelines':
            timelines = [dict(r) for r in db.conn.execute('SELECT * FROM story_timelines').fetchall()]
            self._json({'count': len(timelines), 'timelines': timelines})
        
        elif path == '/api/collections':
            collections = [dict(r) for r in db.conn.execute('SELECT * FROM photo_collections').fetchall()]
            self._json({'count': len(collections), 'collections': collections})
        
        elif path.startswith('/api/collection/'):
            collection_id = path.split('/')[-1]
            collection = db.get_collection(collection_id)
            if collection:
                # Get images in collection
                images = db.get_images_by_family(collection.get('family_id'))
                collection['image_count'] = len(images)
                self._json(collection)
            else:
                self._json({'error': 'Collection not found'}, 404)
        
        elif path == '/api/chapters':
            chapters = [dict(r) for r in db.conn.execute('SELECT * FROM story_chapters ORDER BY family_id, chapter_number').fetchall()]
            self._json({'count': len(chapters), 'chapters': chapters})
        
        elif path.startswith('/api/chapter/'):
            parts = path.split('/')
            chapter_id = parts[-1]
            
            if len(parts) > 4 and parts[-2] == "images":
                chapter_id = parts[-2]
                images = db.get_chapter_images(chapter_id)
                self._json({'chapter_id': chapter_id, 'images': images})
            else:
                chapter = db.get_chapter(chapter_id)
                if chapter:
                    images = db.get_chapter_images(chapter_id)
                    chapter['images'] = images
                    self._json(chapter)
                else:
                    self._json({'error': 'Chapter not found'}, 404)
        
        elif path == '/api/collection-sizes':
            self._json({
                'sizes': {
                    'minimal': {'count': 100, 'description': 'Basic photo set'},
                    'standard': {'count': 300, 'description': 'Complete family story'},
                    'expanded': {'count': 500, 'description': 'Detailed family chronicle'},
                    'complete': {'count': 750, 'description': 'Full family saga'}
                },
                'default': 'standard'
            })
        
        elif path == '/api/age-groups':
            self._json(AGE_GROUPS)
        
        elif path.startswith('/api/age/'):
            # /api/age/{actor_id}/{story_date}
            parts = path.split('/')
            if len(parts) >= 5:
                actor_id = parts[3]
                story_date = parts[4]
                
                actor = db.get_actor(actor_id)
                if actor:
                    age = AgingEngine.calculate_age(actor['birth_date'], story_date)
                    age_group, age_data = AgingEngine.get_age_group(age)
                    max_rating = AgingEngine.get_max_rating_for_age(age)
                    mods = AgingEngine.get_age_appropriate_prompt_mods(age)
                    
                    self._json({
                        'actor_id': actor_id,
                        'actor_name': f"{actor['first_name']} {actor['last_name']}",
                        'birth_date': actor['birth_date'],
                        'story_date': story_date,
                        'age': age,
                        'age_group': age_group,
                        'max_rating': max_rating,
                        'prompt_mods': mods
                    })
                else:
                    self._json({'error': 'Actor not found'}, 404)
            else:
                self._json({'error': 'Invalid path'}, 400)
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/generate-525':
            # Generate all 525 actors
            result = actor_gen.generate_525_actors()
            self._json(result)
        
        elif path == '/api/actor':
            # Create single actor
            actor_id = actor_gen.generate_actor(
                theme=data.get('theme', 'western'),
                gender=data.get('gender', 'male'),
                role=data.get('role', 'Cowboy'),
                family_id=data.get('family_id'),
                family_role=data.get('family_role'),
                birth_year=data.get('birth_year'),
                ethnicity=data.get('ethnicity')
            )
            self._json({'actor_id': actor_id})
        
        elif path == '/api/family':
            # Create family
            family_id = db.create_family(
                family_name=data.get('name', 'New Family'),
                theme=data.get('theme', 'western'),
                story_start_date=data.get('start_date', '1870-01-01')
            )
            self._json({'family_id': family_id})
        
        elif path == '/api/timeline':
            # Create timeline
            timeline_id = db.create_timeline(
                name=data.get('name', 'New Timeline'),
                theme=data.get('theme', 'western'),
                start_date=data.get('start_date', '1870-01-01'),
                description=data.get('description')
            )
            self._json({'timeline_id': timeline_id})
        
        elif path == '/api/timeline/advance':
            # Advance timeline
            timeline_id = data.get('timeline_id')
            new_date = data.get('new_date')
            db.advance_timeline(timeline_id, new_date)
            self._json({'success': True, 'new_date': new_date})
        
        elif path == '/api/photos/generate':
            # Generate family photos (legacy - 45)
            family_id = data.get('family_id')
            timeline_id = data.get('timeline_id')
            num_photos = data.get('num_photos', 300)
            
            result = photo_gen.generate_family_photos(family_id, timeline_id, num_photos)
            self._json(result)
        
        elif path == '/api/collection/generate':
            # Generate photo collection (100-500+ photos)
            family_id = data.get('family_id')
            timeline_id = data.get('timeline_id')
            collection_size = data.get('size', 'standard')  # minimal, standard, expanded, complete
            create_chapters = data.get('create_chapters', True)
            
            result = photo_gen.generate_collection(
                family_id, timeline_id, collection_size, create_chapters
            )
            self._json(result)
        
        elif path == '/api/chapter':
            # Create story chapter
            chapter_id = db.create_chapter(
                family_id=data.get('family_id'),
                timeline_id=data.get('timeline_id'),
                chapter_number=data.get('chapter_number', 1),
                title=data.get('title', 'New Chapter'),
                description=data.get('description'),
                story_date_start=data.get('start_date'),
                story_date_end=data.get('end_date')
            )
            self._json({'chapter_id': chapter_id})
        
        elif path == '/api/chapter/link-image':
            # Link image to chapter
            chapter_id = data.get('chapter_id')
            image_id = data.get('image_id')
            sequence = data.get('sequence_order')
            caption = data.get('caption')
            
            db.link_image_to_chapter(chapter_id, image_id, sequence, caption)
            self._json({'success': True})
        
        elif path == '/api/collection':
            # Create empty collection
            collection_id = db.create_collection(
                family_id=data.get('family_id'),
                name=data.get('name', 'New Collection'),
                timeline_id=data.get('timeline_id'),
                collection_size=data.get('size', 'standard'),
                story_date_start=data.get('start_date'),
                story_date_end=data.get('end_date')
            )
            self._json({'collection_id': collection_id})
        
        elif path == '/api/calculate-age':
            # Calculate age at story date
            birth_date = data.get('birth_date')
            story_date = data.get('story_date')
            
            age = AgingEngine.calculate_age(birth_date, story_date)
            age_group, age_data = AgingEngine.get_age_group(age)
            max_rating = AgingEngine.get_max_rating_for_age(age)
            
            self._json({
                'age': age,
                'age_group': age_group,
                'max_rating': max_rating,
                'rating_allowed': AgingEngine.is_rating_allowed(age, data.get('rating', 'PG'))
            })
        
        elif path == '/api/actor/restrictions':
            # Get actor's restriction releases over time
            actor_id = data.get('actor_id')
            releases = db.get_restriction_releases(actor_id)
            self._json({'actor_id': actor_id, 'releases': releases})
        
        elif path == '/api/actor/age-history':
            # Get actor's age snapshots
            actor_id = data.get('actor_id')
            snapshots = [dict(r) for r in db.conn.execute(
                'SELECT * FROM actor_age_snapshots WHERE actor_id = ? ORDER BY story_date',
                (actor_id,)
            ).fetchall()]
            self._json({'actor_id': actor_id, 'snapshots': snapshots})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  FRONTIER STORIES ENGINE")
    print("  525 Actors | Real-Time Aging | 300-500 Family Photos")
    print("=" * 60)
    
    stats = db.get_stats()
    print(f"\nActors: {stats['total_actors']}")
    print(f"Families: {stats['total_families']}")
    print(f"Timelines: {stats['total_timelines']}")
    print(f"Images: {stats['total_images']}")
    print(f"Chapters: {stats['total_chapters']}")
    print(f"Collections: {stats['total_collections']}")
    
    print(f"\nThemes: {', '.join(THEMES.keys())}")
    print(f"Age Groups: {len(AGE_GROUPS)}")
    
    print(f"\nCollection Sizes:")
    print(f"  minimal: 100 | standard: 300 | expanded: 500 | complete: 750")
    
    print(f"\nAge Restrictions (Strictly Enforced):")
    for group, data in AGE_GROUPS.items():
        print(f"  {group}: {data['range']} -> max {data['max_rating']}")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), FrontierStoriesAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
