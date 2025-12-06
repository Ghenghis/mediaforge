"""
Image Type System
- Catalog any image type (Tribal, Western, Fantasy, etc.)
- Learn from each type the same way
- Simple clothes ON/OFF toggle
- Types can include other types (Western includes Tribal + Native)
"""
import sqlite3
import json
import random
from pathlib import Path
from datetime import datetime

CATALOG_PATH = Path(r"c:\Users\Admin\civitai\data\image_types_catalog.json")
DB_PATH = Path(r"c:\Users\Admin\civitai\data\advanced_learning.db")

class ImageTypeSystem:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._load_catalog()
        self._ensure_tables()
        
    def _load_catalog(self):
        with open(CATALOG_PATH, 'r') as f:
            self.catalog = json.load(f)
            
    def _save_catalog(self):
        with open(CATALOG_PATH, 'w') as f:
            json.dump(self.catalog, f, indent=2)
            
    def _ensure_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS type_learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT,
            tag TEXT,
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0,
            weight REAL DEFAULT 0.5,
            updated_at TEXT,
            UNIQUE(type_name, tag)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS type_stats (
            type_name TEXT PRIMARY KEY,
            images_generated INTEGER DEFAULT 0,
            images_rated INTEGER DEFAULT 0,
            avg_rating REAL DEFAULT 0,
            best_rating REAL DEFAULT 0,
            gold_standards INTEGER DEFAULT 0,
            updated_at TEXT
        )''')
        self.conn.commit()
        
    # ==================== TYPE MANAGEMENT ====================
    
    def list_types(self) -> list:
        """List all available image types"""
        types = []
        for key, type_data in self.catalog['types'].items():
            types.append({
                'key': key,
                'name': type_data['name'],
                'description': type_data['description'],
                'enabled': type_data.get('enabled', True),
                'includes': type_data.get('includes_types', [])
            })
        return types
        
    def get_type(self, type_key: str) -> dict:
        """Get full type configuration"""
        if type_key in self.catalog['types']:
            return self.catalog['types'][type_key]
        return None
        
    def create_type(self, key: str, name: str, description: str, 
                   base_tags: list, characters: list = None,
                   settings: list = None, includes_types: list = None) -> dict:
        """Create a new custom image type"""
        
        new_type = {
            'name': name,
            'description': description,
            'enabled': True,
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'base_tags': base_tags,
            'characters': characters or [],
            'settings': settings or [],
            'clothing': {
                'on': ['dressed', 'wearing clothes'],
                'off': ['nude', 'unclothed']
            },
            'accessories': [],
            'style_tags': [],
            'includes_types': includes_types or []
        }
        
        self.catalog['types'][key] = new_type
        self._save_catalog()
        
        return {'status': 'created', 'type_key': key, 'name': name}
        
    # ==================== CLOTHES TOGGLE ====================
    
    def get_clothes_tags(self, clothes_on: bool, type_key: str = None) -> list:
        """Get clothing tags based on toggle"""
        toggle = self.catalog['clothes_toggle']
        
        base_tags = toggle['on']['tags'] if clothes_on else toggle['off']['tags']
        
        # Add type-specific clothing
        if type_key and type_key in self.catalog['types']:
            type_data = self.catalog['types'][type_key]
            clothing = type_data.get('clothing', {})
            specific = clothing.get('on' if clothes_on else 'off', [])
            base_tags.extend(specific)
            
        return base_tags
        
    # ==================== PROMPT BUILDING ====================
    
    def build_prompt(self, type_key: str, clothes_on: bool = True,
                    specific_character: str = None,
                    specific_setting: str = None) -> tuple:
        """Build prompt for a type with clothes toggle"""
        
        if type_key not in self.catalog['types']:
            return None, None, []
            
        type_data = self.catalog['types'][type_key]
        tags = []
        
        # Quality base
        parts = ["masterpiece", "best quality", "ultra detailed", "8k resolution",
                 "photorealistic", "RAW photo", "DSLR", "sharp focus"]
        
        # Age/Adult
        age = random.choice(["21yo", "22yo", "23yo", "24yo", "25yo"])
        parts.extend([f"(adult woman:1.3)", f"({age}:1.2)"])
        
        # Type base tags
        for tag in type_data.get('base_tags', []):
            parts.append(f"({tag}:1.2)")
            tags.append(tag)
            
        # Character
        characters = type_data.get('characters', [])
        if isinstance(characters, dict):
            # Flatten if nested dict
            all_chars = []
            for char_list in characters.values():
                all_chars.extend(char_list)
            characters = all_chars
            
        if specific_character and specific_character in characters:
            char = specific_character
        elif characters:
            char = random.choice(characters)
        else:
            char = "woman"
        parts.append(f"({char}:1.3)")
        tags.append(char)
        
        # Body details (learned preferences)
        body_tags = self._get_learned_tags(type_key, 'body', 5)
        if body_tags:
            parts.extend([f"({t}:1.1)" for t in body_tags])
            tags.extend(body_tags)
        else:
            # Defaults
            parts.extend([
                f"({random.choice(['petite', 'slim', 'athletic', 'toned'])}:1.2)",
                f"({random.choice(['A cup', 'B cup', 'small bust'])}:1.1)",
                f"({random.choice(['perky', 'firm', 'natural'])}:1.2)"
            ])
            
        # Setting
        settings = type_data.get('settings', [])
        if specific_setting and specific_setting in settings:
            setting = specific_setting
        elif settings:
            setting = random.choice(settings)
        else:
            setting = "outdoor"
        parts.append(f"({setting}:1.2)")
        tags.append(setting)
        
        # Clothes toggle
        clothes_tags = self.get_clothes_tags(clothes_on, type_key)
        for tag in clothes_tags[:3]:
            parts.append(f"({tag}:1.2)")
        tags.extend(clothes_tags[:3])
        
        # Accessories
        accessories = type_data.get('accessories', [])
        if accessories:
            acc = random.choice(accessories)
            parts.append(f"({acc}:1.1)")
            tags.append(acc)
            
        # Style tags
        for style in type_data.get('style_tags', []):
            parts.append(f"({style}:1.1)")
            tags.append(style)
            
        # Include parent types
        for included_type in type_data.get('includes_types', []):
            if included_type in self.catalog['types']:
                inc_data = self.catalog['types'][included_type]
                for tag in inc_data.get('style_tags', [])[:2]:
                    parts.append(f"({tag}:0.8)")
                    
        positive = ", ".join(parts)
        
        # Negative prompt
        negative = """EasyNegative, bad-hands-5, (child:2.0), (kid:2.0), (teen:2.0), (minor:2.0),
(saggy:1.5), (bad anatomy:1.4), (deformed:1.4), (extra fingers:1.5),
(low quality:1.5), (worst quality:1.5), (blurry:1.3),
(watermark:1.5), (text:1.5), ugly, disfigured"""
        
        return positive, negative, tags
        
    def _get_learned_tags(self, type_key: str, category: str, limit: int = 5) -> list:
        """Get learned high-performing tags for a type"""
        cursor = self.conn.cursor()
        cursor.execute('''SELECT tag FROM type_learning 
            WHERE type_name = ? AND weight > 0.6
            ORDER BY weight DESC LIMIT ?''', (type_key, limit))
        return [r[0] for r in cursor.fetchall()]
        
    # ==================== LEARNING ====================
    
    def learn_from_rating(self, type_key: str, tags: list, rating: float):
        """Learn from a rating for a specific type"""
        cursor = self.conn.cursor()
        
        is_like = rating >= 10
        is_dislike = rating <= 5
        
        for tag in tags:
            cursor.execute('SELECT likes, dislikes FROM type_learning WHERE type_name = ? AND tag = ?',
                          (type_key, tag))
            result = cursor.fetchone()
            
            if result:
                likes = result[0] + (1 if is_like else 0)
                dislikes = result[1] + (1 if is_dislike else 0)
            else:
                likes = 1 if is_like else 0
                dislikes = 1 if is_dislike else 0
                
            weight = (likes + 1) / (likes + dislikes + 2)
            
            cursor.execute('''INSERT OR REPLACE INTO type_learning 
                (type_name, tag, likes, dislikes, weight, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (type_key, tag, likes, dislikes, weight, datetime.now().isoformat()))
                
        # Update type stats
        cursor.execute('SELECT images_rated, avg_rating, best_rating FROM type_stats WHERE type_name = ?',
                      (type_key,))
        result = cursor.fetchone()
        
        if result:
            rated = result[0] + 1
            avg = (result[1] * result[0] + rating) / rated
            best = max(result[2], rating)
        else:
            rated = 1
            avg = rating
            best = rating
            
        cursor.execute('''INSERT OR REPLACE INTO type_stats 
            (type_name, images_rated, avg_rating, best_rating, updated_at)
            VALUES (?, ?, ?, ?, ?)''',
            (type_key, rated, avg, best, datetime.now().isoformat()))
            
        self.conn.commit()
        
        return {'type': type_key, 'tags_learned': len(tags), 'rating': rating}
        
    def get_type_stats(self, type_key: str) -> dict:
        """Get learning stats for a type"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT * FROM type_stats WHERE type_name = ?', (type_key,))
        stats = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*) FROM type_learning WHERE type_name = ? AND weight > 0.6',
                      (type_key,))
        good_tags = cursor.fetchone()[0]
        
        cursor.execute('SELECT tag, weight FROM type_learning WHERE type_name = ? ORDER BY weight DESC LIMIT 10',
                      (type_key,))
        top_tags = cursor.fetchall()
        
        return {
            'type': type_key,
            'images_rated': stats[2] if stats else 0,
            'avg_rating': round(stats[3], 2) if stats else 0,
            'best_rating': stats[4] if stats else 0,
            'gold_standards': stats[5] if stats else 0,
            'high_performing_tags': good_tags,
            'top_tags': [{'tag': t[0], 'weight': round(t[1], 3)} for t in top_tags]
        }
        
    def get_all_type_stats(self) -> list:
        """Get stats for all types"""
        stats = []
        for type_key in self.catalog['types'].keys():
            stats.append(self.get_type_stats(type_key))
        return stats
        
    def close(self):
        self.conn.close()


# ==================== API HELPERS ====================

def build_prompt_for_api(type_key: str, clothes_on: bool = True) -> dict:
    """Helper for API usage"""
    its = ImageTypeSystem()
    positive, negative, tags = its.build_prompt(type_key, clothes_on)
    its.close()
    
    return {
        'type': type_key,
        'clothes': 'on' if clothes_on else 'off',
        'positive': positive,
        'negative': negative,
        'tags': tags
    }


# ==================== TEST ====================
def test_system():
    print("="*60)
    print("  IMAGE TYPE SYSTEM TEST")
    print("="*60)
    
    its = ImageTypeSystem()
    
    # List types
    print("\n📚 AVAILABLE IMAGE TYPES:")
    for t in its.list_types():
        includes = f" (includes: {', '.join(t['includes'])})" if t['includes'] else ""
        print(f"   • {t['name']}: {t['description'][:50]}...{includes}")
        
    # Test clothes toggle
    print("\n👗 CLOTHES TOGGLE TEST:")
    
    print("\n   Tribal - Clothes ON:")
    positive, negative, tags = its.build_prompt('tribal', clothes_on=True)
    print(f"   {positive[:100]}...")
    
    print("\n   Tribal - Clothes OFF:")
    positive, negative, tags = its.build_prompt('tribal', clothes_on=False)
    print(f"   {positive[:100]}...")
    
    print("\n   Western - Clothes ON:")
    positive, negative, tags = its.build_prompt('western', clothes_on=True)
    print(f"   {positive[:100]}...")
    
    # Test learning
    print("\n🧠 LEARNING TEST:")
    result = its.learn_from_rating('tribal', ['petite', 'A cup', 'perky', 'war paint'], 12)
    print(f"   Learned from rating 12: {result}")
    
    result = its.learn_from_rating('tribal', ['athletic', 'perky', 'ceremonial paint'], 14)
    print(f"   Learned from rating 14: {result}")
    
    # Get stats
    print("\n📊 TYPE STATS:")
    stats = its.get_type_stats('tribal')
    print(f"   Tribal: {stats}")
    
    # Create custom type
    print("\n➕ CREATING CUSTOM TYPE:")
    result = its.create_type(
        key='steampunk',
        name='Steampunk',
        description='Victorian era with steam-powered technology',
        base_tags=['steampunk', 'victorian', 'mechanical', 'brass'],
        characters=['inventor', 'pilot', 'aristocrat', 'engineer'],
        settings=['airship', 'clockwork factory', 'victorian city', 'brass laboratory']
    )
    print(f"   Created: {result}")
    
    print("\n   Steampunk prompt:")
    positive, negative, tags = its.build_prompt('steampunk', clothes_on=True)
    print(f"   {positive[:100]}...")
    
    print("\n✅ Image Type System operational!")
    print("\n📋 SUMMARY:")
    print(f"   • {len(its.catalog['types'])} types available")
    print(f"   • Clothes toggle: ON/OFF")
    print(f"   • Learning per type")
    print(f"   • Custom types supported")
    
    its.close()


if __name__ == "__main__":
    test_system()
