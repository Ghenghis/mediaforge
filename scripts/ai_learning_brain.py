"""
AI Learning Brain System
Comprehensive learning from all user actions
Creates datasets and preference models

Port: 8225
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import random

PORT = 8225
DB_PATH = Path(r"c:\Users\Admin\civitai\data\preferences.db")
CONFIG_PATH = Path(r"c:\Users\Admin\civitai\data\complete_tags_config.json")
DATASET_DIR = Path(r"c:\Users\Admin\civitai\data\datasets")
MODEL_DIR = Path(r"c:\Users\Admin\civitai\data\models")

class AILearningBrain:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._setup_database()
        self._load_config()
        DATASET_DIR.mkdir(exist_ok=True)
        MODEL_DIR.mkdir(exist_ok=True)
        
    def _setup_database(self):
        cursor = self.conn.cursor()
        
        # Drop old tables if they have wrong schema
        cursor.execute("DROP TABLE IF EXISTS tag_weights")
        cursor.execute("DROP TABLE IF EXISTS user_preferences")
        cursor.execute("DROP TABLE IF EXISTS learning_log")
        cursor.execute("DROP TABLE IF EXISTS preference_models")
        cursor.execute("DROP TABLE IF EXISTS chat_memory")
        
        # Core tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE, prompt TEXT, negative TEXT, tags TEXT,
            model TEXT, seed INTEGER, rating INTEGER DEFAULT 0,
            created_at TEXT, rated_at TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS tag_weights (
            tag TEXT PRIMARY KEY, category TEXT,
            likes INTEGER DEFAULT 0, dislikes INTEGER DEFAULT 0,
            weight REAL DEFAULT 0.5, last_updated TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT, subcategory TEXT, item TEXT,
            preference INTEGER DEFAULT 0, weight REAL DEFAULT 0.5,
            times_selected INTEGER DEFAULT 0,
            created_at TEXT, updated_at TEXT,
            UNIQUE(category, subcategory, item)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS learning_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT, category TEXT, item TEXT,
            old_weight REAL, new_weight REAL,
            source TEXT, timestamp TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS preference_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT UNIQUE, model_type TEXT,
            model_data TEXT, accuracy REAL DEFAULT 0,
            created_at TEXT, updated_at TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT, extracted_data TEXT,
            actions_taken TEXT, timestamp TEXT
        )''')
        
        self.conn.commit()
        
    def _load_config(self):
        with open(CONFIG_PATH, 'r') as f:
            self.config = json.load(f)
            
    # ==================== LEARNING FROM RATINGS ====================
    
    def rate_image(self, filename: str, rating: int) -> dict:
        """Learn from image rating"""
        cursor = self.conn.cursor()
        
        # Get image tags
        cursor.execute('SELECT tags, prompt FROM images WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        if not result:
            return {'error': 'Image not found'}
            
        tags = json.loads(result[0]) if result[0] else []
        
        # Update image rating
        cursor.execute('UPDATE images SET rating = ?, rated_at = ? WHERE filename = ?',
                      (rating, datetime.now().isoformat(), filename))
        
        # Update tag weights
        is_like = rating >= 4
        is_dislike = rating <= 2
        
        updated_tags = []
        for tag in tags:
            category = self._categorize_tag(tag)
            old_weight = self._get_tag_weight(tag)
            
            cursor.execute('SELECT likes, dislikes FROM tag_weights WHERE tag = ?', (tag,))
            row = cursor.fetchone()
            
            likes = (row[0] if row else 0) + (1 if is_like else 0)
            dislikes = (row[1] if row else 0) + (1 if is_dislike else 0)
            new_weight = (likes + 1) / (likes + dislikes + 2)
            
            cursor.execute('''INSERT OR REPLACE INTO tag_weights 
                (tag, category, likes, dislikes, weight, last_updated) VALUES (?, ?, ?, ?, ?, ?)''',
                (tag, category, likes, dislikes, new_weight, datetime.now().isoformat()))
            
            # Log learning
            cursor.execute('''INSERT INTO learning_log 
                (action_type, category, item, old_weight, new_weight, source, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                ('rating', category, tag, old_weight, new_weight, 'image_rating', datetime.now().isoformat()))
            
            updated_tags.append({'tag': tag, 'category': category, 'weight': new_weight})
            
        self.conn.commit()
        
        # Auto-update preference model
        self._update_preference_model()
        
        return {'status': 'learned', 'rating': rating, 'tags_updated': len(updated_tags), 'tags': updated_tags[:5]}
        
    def _categorize_tag(self, tag: str) -> str:
        """Determine category of a tag"""
        tag_lower = tag.lower()
        
        category_keywords = {
            'bust': ['breast', 'bust', 'chest', 'nipple', 'cup'],
            'body_frame': ['petite', 'slim', 'athletic', 'toned', 'muscular', 'frame', 'build'],
            'stomach': ['stomach', 'abs', 'waist', 'belly', 'core'],
            'butt': ['butt', 'glute', 'rear', 'bottom'],
            'legs': ['leg', 'thigh', 'calf', 'calves'],
            'face': ['face', 'cheek', 'jaw', 'chin', 'feature'],
            'eyes': ['eye', 'iris', 'gaze', 'heterochromia'],
            'hair': ['hair', 'braid', 'ponytail', 'bangs'],
            'skin': ['skin', 'complexion', 'tone', 'pale', 'tan', 'dark'],
            'pose': ['standing', 'sitting', 'pose', 'angle', 'view'],
            'lighting': ['light', 'shadow', 'golden', 'dramatic'],
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in tag_lower for kw in keywords):
                return category
        return 'general'
        
    def _get_tag_weight(self, tag: str) -> float:
        cursor = self.conn.cursor()
        cursor.execute('SELECT weight FROM tag_weights WHERE tag = ?', (tag,))
        result = cursor.fetchone()
        return result[0] if result else 0.5
        
    # ==================== CHAT LEARNING ====================
    
    def learn_from_chat(self, message: str) -> dict:
        """Extract and learn from chat message"""
        message_lower = message.lower()
        learned = {'likes': [], 'dislikes': [], 'preferences': []}
        actions = []
        
        # Process each category
        for category, subcats in self.config.items():
            if category == 'quality_tags':
                continue
            self._process_category_chat(category, subcats, message_lower, learned, actions)
        
        # Save chat
        self._save_chat_memory(message, learned, actions)
        return {'learned': learned, 'actions': actions}
    
    # Synonym mappings for common phrases
    PHRASE_MAPPINGS = {
        # Bust/breasts
        'smaller breasts': ['A cup', 'AA cup', 'flat chest'],
        'small breasts': ['A cup', 'AA cup', 'flat chest'],
        'small boobs': ['A cup', 'AA cup', 'flat chest'],
        'tiny breasts': ['AAA cup', 'flat chest'],
        'big breasts': ['D cup', 'C cup'],
        'large breasts': ['D cup', 'C cup'],
        'perky breasts': ['perky', 'firm'],
        # Body
        'petite': ['small frame', 'slender', 'petite'],
        'slim': ['slender', 'slim'],
        'curvy': ['curvy', 'hourglass'],
        'athletic': ['athletic', 'toned', 'fit'],
        'toned': ['toned', 'athletic', 'visible abs'],
        'fit': ['athletic', 'toned', 'fit'],
        # Eyes
        'blue eyes': ['blue eyes', 'light blue eyes', 'deep blue eyes'],
        'green eyes': ['green eyes', 'emerald eyes'],
        'brown eyes': ['brown eyes', 'dark brown eyes'],
        # Hair
        'blonde': ['blonde hair', 'golden blonde'],
        'brunette': ['brown hair', 'dark brown hair'],
        'redhead': ['red hair', 'auburn hair'],
        'black hair': ['black hair', 'jet black hair'],
        # Skin
        'pale': ['pale skin', 'porcelain skin', 'fair skin'],
        'tan': ['tanned skin', 'olive skin'],
        'dark': ['dark skin', 'ebony skin'],
    }
    
    def _is_negative_sentiment(self, message: str) -> bool:
        """Check if message has negative sentiment"""
        negative_words = ['no ', 'not ', "don't", "dont", 'hate', 'dislike', 'less', 'without', 'never']
        return any(neg in message for neg in negative_words)
    
    def _expand_phrase(self, message: str) -> list:
        """Expand common phrases to config terms"""
        expanded = []
        for phrase, terms in self.PHRASE_MAPPINGS.items():
            if phrase in message:
                expanded.extend(terms)
        return expanded
    
    def _process_category_chat(self, category: str, subcats: dict, message: str, learned: dict, actions: list):
        """Process a single category from chat"""
        # Expand phrases first
        expanded_terms = self._expand_phrase(message)
        
        for subcat, items in subcats.items():
            for item in items:
                # Check direct match or expanded match
                matched = item.lower() in message or item in expanded_terms
                if not matched:
                    continue
                is_negative = self._is_negative_sentiment(message)
                preference = -1 if is_negative else 1
                self._update_preference(category, subcat, item, preference)
                
                target = 'dislikes' if is_negative else 'likes'
                learned[target].append(f"{category}/{item}")
                actions.append(f"{'Dislike' if is_negative else 'Like'}: {category}/{item}")
    
    def _save_chat_memory(self, message: str, learned: dict, actions: list):
        """Save chat interaction to database"""
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO chat_memory (user_input, extracted_data, actions_taken, timestamp)
            VALUES (?, ?, ?, ?)''', (message, json.dumps(learned), json.dumps(actions), datetime.now().isoformat()))
        self.conn.commit()
        
    def _update_preference(self, category: str, subcategory: str, item: str, preference: int):
        """Update a specific preference"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT weight, times_selected FROM user_preferences WHERE category=? AND subcategory=? AND item=?',
                      (category, subcategory, item))
        result = cursor.fetchone()
        
        if result:
            old_weight = result[0]
            times = result[1] + 1
            # Weighted average
            new_weight = (old_weight * (times - 1) + (1 if preference > 0 else 0)) / times
        else:
            times = 1
            new_weight = 1.0 if preference > 0 else 0.0
            
        cursor.execute('''INSERT OR REPLACE INTO user_preferences 
            (category, subcategory, item, preference, weight, times_selected, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM user_preferences WHERE category=? AND subcategory=? AND item=?), ?), ?)''',
            (category, subcategory, item, preference, new_weight, times, category, subcategory, item, 
             datetime.now().isoformat(), datetime.now().isoformat()))
        self.conn.commit()
        
    # ==================== DATASET GENERATION ====================
    
    def generate_dataset(self, dataset_name: str = None) -> dict:
        """Generate training dataset from learned preferences"""
        if not dataset_name:
            dataset_name = f"preference_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        cursor = self.conn.cursor()
        
        # Get all preferences
        cursor.execute('SELECT category, subcategory, item, weight FROM user_preferences WHERE times_selected > 0')
        preferences = cursor.fetchall()
        
        # Get rated images
        cursor.execute('SELECT filename, prompt, tags, rating FROM images WHERE rating > 0')
        rated_images = cursor.fetchall()
        
        # Build dataset
        dataset = {
            'name': dataset_name,
            'created_at': datetime.now().isoformat(),
            'statistics': {
                'total_preferences': len(preferences),
                'total_rated_images': len(rated_images),
                'liked_images': len([r for r in rated_images if r[3] >= 4]),
                'disliked_images': len([r for r in rated_images if r[3] <= 2])
            },
            'preferences': {
                'liked': [],
                'disliked': []
            },
            'tag_weights': {},
            'training_pairs': []
        }
        
        # Process preferences
        for cat, subcat, item, weight in preferences:
            entry = {'category': cat, 'subcategory': subcat, 'item': item, 'weight': weight}
            if weight > 0.5:
                dataset['preferences']['liked'].append(entry)
            else:
                dataset['preferences']['disliked'].append(entry)
                
        # Get tag weights
        cursor.execute('SELECT tag, category, weight FROM tag_weights WHERE likes + dislikes > 0')
        for tag, cat, weight in cursor.fetchall():
            dataset['tag_weights'][tag] = {'category': cat, 'weight': weight}
            
        # Create training pairs (prompt + rating)
        for filename, prompt, tags, rating in rated_images:
            dataset['training_pairs'].append({
                'prompt': prompt[:500],
                'tags': json.loads(tags) if tags else [],
                'rating': rating,
                'label': 'positive' if rating >= 4 else 'negative' if rating <= 2 else 'neutral'
            })
            
        # Save dataset
        dataset_path = DATASET_DIR / f"{dataset_name}.json"
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2)
            
        return {'status': 'created', 'path': str(dataset_path), 'stats': dataset['statistics']}
        
    # ==================== PREFERENCE MODEL ====================
    
    def _update_preference_model(self):
        """Update the preference model from learned data"""
        cursor = self.conn.cursor()
        
        # Build model from tag weights
        cursor.execute('SELECT tag, category, weight, likes, dislikes FROM tag_weights')
        tag_data = cursor.fetchall()
        
        # Build model from preferences
        cursor.execute('SELECT category, subcategory, item, weight FROM user_preferences')
        pref_data = cursor.fetchall()
        
        model = {
            'version': datetime.now().isoformat(),
            'tag_preferences': {},
            'category_preferences': defaultdict(lambda: defaultdict(dict)),
            'top_liked': [],
            'top_disliked': []
        }
        
        # Process tags
        for tag, cat, weight, likes, dislikes in tag_data:
            model['tag_preferences'][tag] = {'weight': weight, 'category': cat, 'likes': likes, 'dislikes': dislikes}
            
        # Process preferences
        for cat, subcat, item, weight in pref_data:
            model['category_preferences'][cat][subcat][item] = weight
            
        # Top liked/disliked
        sorted_tags = sorted(tag_data, key=lambda x: x[2], reverse=True)
        model['top_liked'] = [{'tag': t[0], 'weight': t[2]} for t in sorted_tags[:20] if t[2] > 0.5]
        model['top_disliked'] = [{'tag': t[0], 'weight': t[2]} for t in sorted_tags[-20:] if t[2] < 0.5]
        
        # Save model
        model_data = json.dumps(model)
        cursor.execute('''INSERT OR REPLACE INTO preference_models 
            (model_name, model_type, model_data, accuracy, created_at, updated_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM preference_models WHERE model_name=?), ?), ?)''',
            ('user_preference_model', 'preference', model_data, 0.0, 'user_preference_model',
             datetime.now().isoformat(), datetime.now().isoformat()))
        self.conn.commit()
        
        return model
        
    def get_preference_model(self) -> dict:
        """Get current preference model"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT model_data FROM preference_models WHERE model_name = ?', ('user_preference_model',))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else {}
        
    # ==================== PROMPT GENERATION ====================
    
    def generate_smart_prompt(self, style: str = 'tribal') -> tuple:
        """Generate prompt using learned preferences"""
        model = self.get_preference_model()
        parts, tags_used = self._build_base_prompt()
        
        # Add category-based tags
        categories = ['body_frame', 'bust', 'stomach', 'butt', 'legs', 'face', 'eyes', 'hair', 'skin']
        for category in categories:
            self._add_category_tags(category, model, parts, tags_used)
        
        # Add style and liked tags
        self._add_style_tags(style, parts, tags_used)
        self._add_top_liked_tags(model, parts, tags_used)
        
        positive = ", ".join(parts)
        negative = self._build_negative_prompt(model)
        
        return positive, negative, tags_used
    
    def _build_base_prompt(self) -> tuple:
        """Build base prompt parts"""
        parts = list(self.config['quality_tags']['always_positive'])
        age = random.choice(['21yo', '22yo', '23yo', '24yo', '25yo'])
        parts.append(f"(adult woman:1.3), ({age}:1.2)")
        return parts, []
    
    def _add_category_tags(self, category: str, model: dict, parts: list, tags_used: list):
        """Add tags for a specific category"""
        if category not in self.config:
            return
        
        for subcategory, items in self.config[category].items():
            cat_prefs = model.get('category_preferences', {}).get(category, {}).get(subcategory, {})
            
            if cat_prefs:
                sorted_items = sorted(cat_prefs.items(), key=lambda x: x[1], reverse=True)
                if sorted_items and sorted_items[0][1] > 0.5:
                    item, weight = sorted_items[0]
                    parts.append(f"({item}:{0.8 + weight * 0.5:.1f})")
                    tags_used.append(item)
                    continue
            
            item = random.choice(items)
            tag_weight = model.get('tag_preferences', {}).get(item, {}).get('weight', 0.5)
            if tag_weight > 0.4:
                parts.append(f"({item}:{0.8 + tag_weight * 0.4:.1f})")
                tags_used.append(item)
    
    def _add_style_tags(self, style: str, parts: list, tags_used: list):
        """Add style-specific tags"""
        if style != 'tribal' or 'tribal_specific' not in self.config:
            return
        for subcat, items in self.config.get('tribal_specific', {}).items():
            if items:
                item = random.choice(items)
                parts.append(f"({item}:1.3)")
                tags_used.append(item)
    
    def _add_top_liked_tags(self, model: dict, parts: list, tags_used: list):
        """Add top liked tags"""
        for liked in model.get('top_liked', [])[:5]:
            if liked['tag'] not in tags_used:
                parts.append(f"({liked['tag']}:{liked['weight']:.1f})")
                tags_used.append(liked['tag'])
    
    def _build_negative_prompt(self, model: dict) -> str:
        """Build negative prompt"""
        negative_parts = list(self.config['quality_tags']['always_negative'])
        for disliked in model.get('top_disliked', [])[:10]:
            negative_parts.append(f"({disliked['tag']}:1.4)")
        return ", ".join(negative_parts)
        
    # ==================== STATISTICS ====================
    
    def get_learning_stats(self) -> dict:
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM images')
        total_images = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating > 0')
        rated_images = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tag_weights WHERE likes + dislikes > 0')
        learned_tags = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_preferences WHERE times_selected > 0')
        learned_prefs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM learning_log')
        learning_events = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM chat_memory')
        chat_interactions = cursor.fetchone()[0]
        
        cursor.execute('SELECT category, COUNT(*) FROM tag_weights GROUP BY category')
        by_category = dict(cursor.fetchall())
        
        return {
            'total_images': total_images,
            'rated_images': rated_images,
            'learned_tags': learned_tags,
            'learned_preferences': learned_prefs,
            'learning_events': learning_events,
            'chat_interactions': chat_interactions,
            'tags_by_category': by_category
        }
        
    def close(self):
        self.conn.close()


# ==================== TEST FUNCTION ====================
def test_ai_brain():
    print("="*60)
    print("  AI LEARNING BRAIN TEST")
    print("="*60)
    
    brain = AILearningBrain()
    
    # Test 1: Rate images
    print("\n📝 TEST 1: Learning from Ratings")
    print("-"*40)
    
    # Simulate image with tags
    cursor = brain.conn.cursor()
    test_tags = ['petite', 'A cup', 'perky', 'visible abs', 'oval face', 'blue eyes']
    cursor.execute('''INSERT OR REPLACE INTO images (filename, prompt, tags, created_at)
        VALUES (?, ?, ?, ?)''', ('test_img_1.png', 'test prompt', json.dumps(test_tags), datetime.now().isoformat()))
    brain.conn.commit()
    
    result = brain.rate_image('test_img_1.png', 5)
    print(f"   Rated image: {result['tags_updated']} tags updated")
    print(f"   Sample: {result['tags'][:3]}")
    
    test1_pass = result['tags_updated'] > 0
    print(f"\n   Result: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    
    # Test 2: Chat learning
    print("\n📝 TEST 2: Learning from Chat")
    print("-"*40)
    
    chats = [
        "I like petite women with small breasts and visible abs",
        "I prefer perky nipples and toned stomach",
        "I don't like saggy or large breasts",
    ]
    
    total_learned = 0
    for chat in chats:
        result = brain.learn_from_chat(chat)
        total_learned += len(result['learned']['likes']) + len(result['learned']['dislikes'])
        print(f"   '{chat[:40]}...' → {len(result['actions'])} actions")
        
    test2_pass = total_learned > 5
    print(f"\n   Result: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    # Test 3: Preference model
    print("\n📝 TEST 3: Preference Model")
    print("-"*40)
    
    model = brain.get_preference_model()
    print(f"   Tags in model: {len(model.get('tag_preferences', {}))}")
    print(f"   Top liked: {[t['tag'] for t in model.get('top_liked', [])[:5]]}")
    print(f"   Top disliked: {[t['tag'] for t in model.get('top_disliked', [])[:3]]}")
    
    test3_pass = len(model.get('tag_preferences', {})) > 0
    print(f"\n   Result: {'✅ PASS' if test3_pass else '❌ FAIL'}")
    
    # Test 4: Smart prompt generation
    print("\n📝 TEST 4: Smart Prompt Generation")
    print("-"*40)
    
    positive, negative, tags = brain.generate_smart_prompt()
    print(f"   Positive prompt: {positive[:100]}...")
    print(f"   Tags used: {len(tags)}")
    print(f"   Negative has {len(negative.split(','))} items")
    
    test4_pass = len(positive) > 100 and len(tags) > 5
    print(f"\n   Result: {'✅ PASS' if test4_pass else '❌ FAIL'}")
    
    # Test 5: Dataset generation
    print("\n📝 TEST 5: Dataset Generation")
    print("-"*40)
    
    result = brain.generate_dataset('test_dataset')
    print(f"   Dataset created: {result['path']}")
    print(f"   Stats: {result['stats']}")
    
    test5_pass = result['status'] == 'created'
    print(f"\n   Result: {'✅ PASS' if test5_pass else '❌ FAIL'}")
    
    # Test 6: Statistics
    print("\n📝 TEST 6: Learning Statistics")
    print("-"*40)
    
    stats = brain.get_learning_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
        
    test6_pass = stats['learning_events'] > 0
    print(f"\n   Result: {'✅ PASS' if test6_pass else '❌ FAIL'}")
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    all_pass = all([test1_pass, test2_pass, test3_pass, test4_pass, test5_pass, test6_pass])
    
    print(f"\n   Test 1 (Ratings): {'✅' if test1_pass else '❌'}")
    print(f"   Test 2 (Chat): {'✅' if test2_pass else '❌'}")
    print(f"   Test 3 (Model): {'✅' if test3_pass else '❌'}")
    print(f"   Test 4 (Prompts): {'✅' if test4_pass else '❌'}")
    print(f"   Test 5 (Dataset): {'✅' if test5_pass else '❌'}")
    print(f"   Test 6 (Stats): {'✅' if test6_pass else '❌'}")
    
    print(f"\n   Overall: {'✅ ALL TESTS PASSED' if all_pass else '❌ SOME TESTS FAILED'}")
    
    if all_pass:
        print("\n🧠 AI Learning Brain is fully operational!")
        print("   ✓ Learns from image ratings")
        print("   ✓ Learns from chat interactions")
        print("   ✓ Builds preference models")
        print("   ✓ Generates smart prompts")
        print("   ✓ Creates training datasets")
        print("   ✓ Tracks all learning statistics")
    
    # Cleanup
    cursor.execute("DELETE FROM images WHERE filename LIKE 'test_%'")
    brain.conn.commit()
    brain.close()
    
    return all_pass

# ==================== HTTP API ====================

# Global brain instance
brain = None

def get_brain():
    global brain
    if brain is None:
        brain = AILearningBrain()
    return brain


class LearningBrainAPI(BaseHTTPRequestHandler):
    """HTTP API for AI Learning Brain"""
    
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
        self._json({})
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        b = get_brain()
        
        if path == '/':
            stats = b.get_learning_stats()
            self._json({
                'service': 'AI Learning Brain',
                'version': '1.0',
                'port': PORT,
                'stats': stats
            })
        
        elif path == '/api/stats':
            self._json(b.get_learning_stats())
        
        elif path == '/api/preferences':
            model = b.get_preference_model()
            self._json({
                'model_version': model.get('version'),
                'tag_count': len(model.get('tag_preferences', {})),
                'top_liked': model.get('top_liked', [])[:10],
                'top_disliked': model.get('top_disliked', [])[:10]
            })
        
        elif path == '/api/tags':
            cursor = b.conn.cursor()
            cursor.execute('SELECT tag, category, weight, likes, dislikes FROM tag_weights ORDER BY weight DESC')
            tags = [{'tag': r[0], 'category': r[1], 'weight': r[2], 'likes': r[3], 'dislikes': r[4]} 
                    for r in cursor.fetchall()]
            self._json({'tags': tags, 'count': len(tags)})
        
        elif path == '/api/model':
            self._json(b.get_preference_model())
        
        elif path == '/api/suggest':
            style = params.get('style', ['tribal'])[0]
            count = int(params.get('count', ['1'])[0])
            
            suggestions = []
            for _ in range(count):
                positive, negative, tags = b.generate_smart_prompt(style)
                suggestions.append({
                    'positive': positive,
                    'negative': negative,
                    'tags_used': tags
                })
            
            self._json({'suggestions': suggestions})
        
        elif path == '/api/history':
            limit = int(params.get('limit', ['50'])[0])
            cursor = b.conn.cursor()
            cursor.execute('SELECT * FROM learning_log ORDER BY timestamp DESC LIMIT ?', (limit,))
            logs = [{'id': r[0], 'action': r[1], 'category': r[2], 'item': r[3], 
                    'old_weight': r[4], 'new_weight': r[5], 'source': r[6], 'timestamp': r[7]}
                    for r in cursor.fetchall()]
            self._json({'history': logs})
        
        elif path == '/api/datasets':
            datasets = list(DATASET_DIR.glob('*.json'))
            self._json({
                'datasets': [{'name': d.stem, 'path': str(d), 'size': d.stat().st_size} for d in datasets]
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        b = get_brain()
        
        if path == '/api/learn':
            # Learn from a rating action
            image_id = data.get('image_id') or data.get('filename')
            rating = data.get('rating', 0)
            tags = data.get('tags', [])
            prompt = data.get('prompt', '')
            
            if not image_id:
                self._json({'success': False, 'error': 'image_id or filename required'})
                return
            
            # Ensure image exists in DB
            cursor = b.conn.cursor()
            cursor.execute('SELECT 1 FROM images WHERE filename = ?', (image_id,))
            if not cursor.fetchone():
                cursor.execute('''INSERT INTO images (filename, prompt, tags, created_at)
                    VALUES (?, ?, ?, ?)''', 
                    (image_id, prompt, json.dumps(tags), datetime.now().isoformat()))
                b.conn.commit()
            
            result = b.rate_image(image_id, rating)
            self._json({'success': True, **result})
        
        elif path == '/api/learn/chat':
            message = data.get('message', '')
            if message:
                result = b.learn_from_chat(message)
                self._json({'success': True, **result})
            else:
                self._json({'success': False, 'error': 'message required'})
        
        elif path == '/api/tags/update':
            tag = data.get('tag')
            action = data.get('action', 'like')  # 'like' or 'dislike'
            
            if not tag:
                self._json({'success': False, 'error': 'tag required'})
                return
            
            cursor = b.conn.cursor()
            cursor.execute('SELECT likes, dislikes, weight FROM tag_weights WHERE tag = ?', (tag,))
            row = cursor.fetchone()
            
            likes = (row[0] if row else 0) + (1 if action == 'like' else 0)
            dislikes = (row[1] if row else 0) + (1 if action == 'dislike' else 0)
            new_weight = (likes + 1) / (likes + dislikes + 2)
            
            cursor.execute('''INSERT OR REPLACE INTO tag_weights 
                (tag, category, likes, dislikes, weight, last_updated) VALUES (?, ?, ?, ?, ?, ?)''',
                (tag, 'manual', likes, dislikes, new_weight, datetime.now().isoformat()))
            b.conn.commit()
            
            self._json({'success': True, 'tag': tag, 'new_weight': new_weight, 'likes': likes, 'dislikes': dislikes})
        
        elif path == '/api/dataset/generate':
            name = data.get('name')
            min_rating = data.get('min_rating', 0)
            
            result = b.generate_dataset(name)
            self._json({'success': True, **result})
        
        elif path == '/api/reset':
            confirm = data.get('confirm', False)
            if not confirm:
                self._json({'success': False, 'error': 'Set confirm=true to reset all learning data'})
                return
            
            cursor = b.conn.cursor()
            cursor.execute('DELETE FROM tag_weights')
            cursor.execute('DELETE FROM user_preferences')
            cursor.execute('DELETE FROM learning_log')
            cursor.execute('DELETE FROM preference_models')
            b.conn.commit()
            
            self._json({'success': True, 'message': 'All learning data reset'})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  AI LEARNING BRAIN API")
    print("  Port:", PORT)
    print("=" * 60)
    
    b = get_brain()
    stats = b.get_learning_stats()
    
    print(f"\nLearning Stats:")
    print(f"  Images: {stats['total_images']}")
    print(f"  Rated: {stats['rated_images']}")
    print(f"  Learned Tags: {stats['learned_tags']}")
    print(f"  Preferences: {stats['learned_preferences']}")
    print(f"  Learning Events: {stats['learning_events']}")
    
    print(f"\nEndpoints:")
    print(f"  GET  /api/stats        - Learning statistics")
    print(f"  GET  /api/preferences  - User preferences summary")
    print(f"  GET  /api/tags         - All tag weights")
    print(f"  GET  /api/model        - Full preference model")
    print(f"  GET  /api/suggest      - Get prompt suggestions")
    print(f"  POST /api/learn        - Learn from rating")
    print(f"  POST /api/learn/chat   - Learn from chat")
    print(f"  POST /api/tags/update  - Update tag weight")
    print(f"  POST /api/dataset/generate - Generate dataset")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), LearningBrainAPI)
    server.serve_forever()


if __name__ == "__main__":
    main()
