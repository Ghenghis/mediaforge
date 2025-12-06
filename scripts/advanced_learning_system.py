"""
Advanced AI Learning System
- Image ID with full prompt tracking
- 0-15 Rating scale
- Real-time learning from rating changes
- Auto-generation on high ratings (10+)
- Pursuit of perfect rating (15)
"""
import sqlite3
import json
import uuid
import time
import random
import urllib.request
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = Path(r"c:\Users\Admin\civitai\data\advanced_learning.db")
CONFIG_PATH = Path(r"c:\Users\Admin\civitai\data\complete_tags_config.json")
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
COMFY_URL = "http://localhost:8188"

# Load config
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

class AdvancedLearningSystem:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._setup_database()
        self._load_gold_standards()
        self.generation_lock = threading.Lock()
        self.active_tasks = []
        
    def _setup_database(self):
        cursor = self.conn.cursor()
        
        # Images with UUID and full tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS images (
            image_id TEXT PRIMARY KEY,
            filename TEXT UNIQUE,
            prompt TEXT,
            negative_prompt TEXT,
            tags TEXT,
            model TEXT,
            seed INTEGER,
            rating REAL DEFAULT 0,
            rating_history TEXT DEFAULT '[]',
            analysis TEXT,
            generation_source TEXT,
            parent_image_id TEXT,
            created_at TEXT,
            rated_at TEXT,
            is_gold_standard INTEGER DEFAULT 0
        )''')
        
        # Tag weights with detailed tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS tag_analysis (
            tag TEXT PRIMARY KEY,
            category TEXT,
            avg_rating REAL DEFAULT 0,
            high_rating_count INTEGER DEFAULT 0,
            low_rating_count INTEGER DEFAULT 0,
            weight REAL DEFAULT 0.5,
            importance REAL DEFAULT 0.5,
            last_high_rating TEXT,
            associated_tags TEXT DEFAULT '[]',
            enhancement_suggestions TEXT DEFAULT '[]'
        )''')
        
        # Rating events for learning
        cursor.execute('''CREATE TABLE IF NOT EXISTS rating_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id TEXT,
            old_rating REAL,
            new_rating REAL,
            rating_change REAL,
            tags_analyzed TEXT,
            learning_applied TEXT,
            auto_generated INTEGER DEFAULT 0,
            timestamp TEXT,
            FOREIGN KEY (image_id) REFERENCES images(image_id)
        )''')
        
        # Gold standard images (rating 15)
        cursor.execute('''CREATE TABLE IF NOT EXISTS gold_standards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id TEXT,
            prompt TEXT,
            tags TEXT,
            key_features TEXT,
            created_at TEXT,
            FOREIGN KEY (image_id) REFERENCES images(image_id)
        )''')
        
        # Auto-generation queue
        cursor.execute('''CREATE TABLE IF NOT EXISTS generation_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_image_id TEXT,
            trigger_rating REAL,
            images_to_generate INTEGER,
            images_generated INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            prompt_enhancements TEXT,
            created_at TEXT,
            completed_at TEXT
        )''')
        
        # Prompt patterns (what works)
        cursor.execute('''CREATE TABLE IF NOT EXISTS prompt_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT,
            category TEXT,
            avg_rating REAL,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0,
            created_at TEXT
        )''')
        
        # Story collections
        cursor.execute('''CREATE TABLE IF NOT EXISTS story_collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_name TEXT,
            theme TEXT,
            story_content TEXT,
            total_scenes INTEGER DEFAULT 0,
            images_generated INTEGER DEFAULT 0,
            target_images INTEGER DEFAULT 500,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )''')
        
        self.conn.commit()
        
    def _load_gold_standards(self):
        """Load gold standard prompts for reference"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT prompt, tags, key_features FROM gold_standards')
        self.gold_standards = cursor.fetchall()
        
    # ==================== IMAGE CREATION ====================
    
    def create_image_record(self, filename: str, prompt: str, negative: str, 
                           tags: list, seed: int, source: str = "manual",
                           parent_id: str = None) -> str:
        """Create new image record with unique ID"""
        image_id = str(uuid.uuid4())[:8]
        
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO images 
            (image_id, filename, prompt, negative_prompt, tags, model, seed, 
             generation_source, parent_image_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (image_id, filename, prompt, negative, json.dumps(tags),
             "CyberRealistic", seed, source, parent_id, datetime.now().isoformat()))
        self.conn.commit()
        
        return image_id
        
    # ==================== RATING SYSTEM (0-15) ====================
    
    def rate_image(self, image_id: str, new_rating: float) -> dict:
        """
        Rate image on 0-15 scale
        - 0-5: Dislike
        - 6-9: Neutral/Good
        - 10-12: Excellent (triggers 50 variations)
        - 13-14: Near Perfect (intensive learning)
        - 15: Perfect (Gold Standard)
        """
        new_rating = max(0, min(15, new_rating))  # Clamp to 0-15
        
        cursor = self.conn.cursor()
        
        # Get current image data
        cursor.execute('SELECT rating, tags, prompt, rating_history FROM images WHERE image_id = ?', (image_id,))
        result = cursor.fetchone()
        if not result:
            return {'error': 'Image not found'}
            
        old_rating, tags_json, prompt, history_json = result
        old_rating = old_rating or 0
        tags = json.loads(tags_json) if tags_json else []
        history = json.loads(history_json) if history_json else []
        
        # Calculate rating change
        rating_change = new_rating - old_rating
        
        # Update history
        history.append({
            'rating': new_rating,
            'timestamp': datetime.now().isoformat(),
            'change': rating_change
        })
        
        # Update image
        cursor.execute('''UPDATE images SET 
            rating = ?, rating_history = ?, rated_at = ?
            WHERE image_id = ?''',
            (new_rating, json.dumps(history), datetime.now().isoformat(), image_id))
        
        # Analyze and learn
        analysis = self._analyze_rating(image_id, tags, prompt, old_rating, new_rating)
        
        # Log rating event
        cursor.execute('''INSERT INTO rating_events 
            (image_id, old_rating, new_rating, rating_change, tags_analyzed, learning_applied, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (image_id, old_rating, new_rating, rating_change, 
             json.dumps(tags), json.dumps(analysis), datetime.now().isoformat()))
        
        self.conn.commit()
        
        result = {
            'image_id': image_id,
            'old_rating': old_rating,
            'new_rating': new_rating,
            'change': rating_change,
            'analysis': analysis,
            'action': None
        }
        
        # TRIGGER ACTIONS BASED ON RATING
        if new_rating >= 15:
            # PERFECT - Gold Standard
            self._save_gold_standard(image_id, prompt, tags)
            result['action'] = 'GOLD_STANDARD_SAVED'
            
        elif new_rating >= 10:
            # EXCELLENT - Auto-generate 50 variations
            result['action'] = f'AUTO_GENERATING_50_VARIATIONS'
            threading.Thread(target=self._auto_generate_variations, 
                           args=(image_id, prompt, tags, new_rating, 50)).start()
                           
        elif new_rating >= 7 and rating_change >= 3:
            # Good improvement - Generate 10 variations
            result['action'] = 'GENERATING_10_VARIATIONS'
            threading.Thread(target=self._auto_generate_variations,
                           args=(image_id, prompt, tags, new_rating, 10)).start()
        
        return result
        
    def _analyze_rating(self, image_id: str, tags: list, prompt: str, 
                       old_rating: float, new_rating: float) -> dict:
        """Deep analysis of why rating changed"""
        cursor = self.conn.cursor()
        analysis = {
            'rating_level': self._get_rating_level(new_rating),
            'improvement': new_rating > old_rating,
            'tag_contributions': [],
            'prompt_patterns': [],
            'suggestions': []
        }
        
        # Update tag analytics
        for tag in tags:
            cursor.execute('SELECT avg_rating, high_rating_count, low_rating_count FROM tag_analysis WHERE tag = ?', (tag,))
            result = cursor.fetchone()
            
            if result:
                avg, high, low = result
                new_avg = (avg * (high + low) + new_rating) / (high + low + 1)
                new_high = high + (1 if new_rating >= 10 else 0)
                new_low = low + (1 if new_rating <= 5 else 0)
                weight = (new_high + 1) / (new_high + new_low + 2)
                importance = min(1.0, (high + low + 1) / 100)
            else:
                new_avg = new_rating
                new_high = 1 if new_rating >= 10 else 0
                new_low = 1 if new_rating <= 5 else 0
                weight = 0.5
                importance = 0.01
                
            cursor.execute('''INSERT OR REPLACE INTO tag_analysis 
                (tag, category, avg_rating, high_rating_count, low_rating_count, weight, importance, last_high_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (tag, self._categorize_tag(tag), new_avg, new_high, new_low, weight, importance,
                 datetime.now().isoformat() if new_rating >= 10 else None))
                 
            analysis['tag_contributions'].append({
                'tag': tag,
                'avg_rating': round(new_avg, 2),
                'weight': round(weight, 3),
                'high_count': new_high
            })
            
        self.conn.commit()
        
        # Extract prompt patterns
        if new_rating >= 10:
            patterns = self._extract_prompt_patterns(prompt)
            analysis['prompt_patterns'] = patterns
            
        # Generate suggestions for improvement
        if new_rating < 15:
            analysis['suggestions'] = self._generate_enhancement_suggestions(tags, new_rating)
            
        return analysis
        
    def _get_rating_level(self, rating: float) -> str:
        if rating >= 15: return "PERFECT"
        if rating >= 13: return "NEAR_PERFECT"
        if rating >= 10: return "EXCELLENT"
        if rating >= 7: return "GOOD"
        if rating >= 5: return "NEUTRAL"
        return "DISLIKE"
        
    def _categorize_tag(self, tag: str) -> str:
        tag_lower = tag.lower()
        categories = {
            'bust': ['breast', 'bust', 'chest', 'cup', 'nipple'],
            'body': ['petite', 'slim', 'athletic', 'toned', 'muscular'],
            'face': ['face', 'eye', 'hair', 'lips', 'cheek'],
            'style': ['tribal', 'western', 'native', 'ceremonial'],
            'quality': ['detailed', '8k', 'sharp', 'realistic']
        }
        for cat, keywords in categories.items():
            if any(kw in tag_lower for kw in keywords):
                return cat
        return 'general'
        
    def _extract_prompt_patterns(self, prompt: str) -> list:
        """Extract successful patterns from high-rated prompts"""
        patterns = []
        
        # Weight patterns
        import re
        weighted = re.findall(r'\(([^:]+):([0-9.]+)\)', prompt)
        for tag, weight in weighted:
            if float(weight) >= 1.2:
                patterns.append({'type': 'high_weight', 'tag': tag, 'weight': float(weight)})
                
        return patterns
        
    def _generate_enhancement_suggestions(self, tags: list, current_rating: float) -> list:
        """Suggest enhancements to reach rating 15"""
        suggestions = []
        cursor = self.conn.cursor()
        
        # Find high-performing tags not in current image
        cursor.execute('''SELECT tag, avg_rating, weight FROM tag_analysis 
            WHERE avg_rating > ? AND tag NOT IN ({})
            ORDER BY avg_rating DESC LIMIT 10'''.format(','.join('?' * len(tags))),
            [current_rating] + tags)
            
        for tag, avg, weight in cursor.fetchall():
            suggestions.append({
                'action': 'ADD_TAG',
                'tag': tag,
                'expected_improvement': round(avg - current_rating, 1)
            })
            
        return suggestions[:5]
        
    # ==================== GOLD STANDARD ====================
    
    def _save_gold_standard(self, image_id: str, prompt: str, tags: list):
        """Save perfect (15) rated image as gold standard"""
        cursor = self.conn.cursor()
        
        # Mark as gold standard
        cursor.execute('UPDATE images SET is_gold_standard = 1 WHERE image_id = ?', (image_id,))
        
        # Extract key features
        key_features = {
            'tags': tags,
            'patterns': self._extract_prompt_patterns(prompt),
            'timestamp': datetime.now().isoformat()
        }
        
        cursor.execute('''INSERT INTO gold_standards 
            (image_id, prompt, tags, key_features, created_at)
            VALUES (?, ?, ?, ?, ?)''',
            (image_id, prompt, json.dumps(tags), json.dumps(key_features), datetime.now().isoformat()))
            
        self.conn.commit()
        self._load_gold_standards()
        
        print(f"\n⭐ GOLD STANDARD SAVED: {image_id}")
        
    # ==================== AUTO-GENERATION ====================
    
    def _auto_generate_variations(self, parent_id: str, prompt: str, tags: list, 
                                  rating: float, count: int):
        """Auto-generate variations of high-rated image"""
        with self.generation_lock:
            print(f"\n🚀 AUTO-GENERATING {count} VARIATIONS (Rating: {rating})")
            
            cursor = self.conn.cursor()
            
            # Create queue entry
            cursor.execute('''INSERT INTO generation_queue 
                (trigger_image_id, trigger_rating, images_to_generate, status, created_at)
                VALUES (?, ?, ?, 'running', ?)''',
                (parent_id, rating, count, datetime.now().isoformat()))
            queue_id = cursor.lastrowid
            self.conn.commit()
            
            generated = 0
            for i in range(count):
                try:
                    # Enhance prompt based on rating level
                    enhanced_prompt = self._enhance_prompt(prompt, tags, rating)
                    enhanced_tags = tags.copy()
                    
                    # Add variations
                    if i % 5 == 0:  # Every 5th image, try new combinations
                        enhanced_prompt, enhanced_tags = self._add_variation(enhanced_prompt, enhanced_tags)
                        
                    # Generate
                    prefix = f"auto_{parent_id}_{i+1:03d}"
                    result = self._generate_image(enhanced_prompt, enhanced_tags, prefix, parent_id)
                    
                    if result.get('success'):
                        generated += 1
                        print(f"   [{generated}/{count}] ✅ {result.get('filename', 'unknown')}")
                    else:
                        print(f"   [{i+1}/{count}] ❌ Failed")
                        
                except Exception as e:
                    print(f"   [{i+1}/{count}] ❌ Error: {e}")
                    
            # Update queue
            cursor.execute('''UPDATE generation_queue SET 
                images_generated = ?, status = 'completed', completed_at = ?
                WHERE id = ?''',
                (generated, datetime.now().isoformat(), queue_id))
            self.conn.commit()
            
            print(f"\n✅ AUTO-GENERATION COMPLETE: {generated}/{count} images")
            
    def _enhance_prompt(self, prompt: str, tags: list, rating: float) -> str:
        """Enhance prompt based on rating level"""
        # Higher rating = more detail preservation
        if rating >= 13:
            # Near perfect - minimal changes
            return prompt
        elif rating >= 10:
            # Excellent - add quality boosters
            boosters = ["extremely detailed", "perfect composition", "award winning"]
            return prompt + ", " + random.choice(boosters)
        else:
            # Good - try enhancements
            cursor = self.conn.cursor()
            cursor.execute('SELECT tag FROM tag_analysis WHERE weight > 0.7 ORDER BY avg_rating DESC LIMIT 5')
            high_tags = [r[0] for r in cursor.fetchall()]
            
            new_tags = [t for t in high_tags if t not in tags][:2]
            if new_tags:
                return prompt + ", " + ", ".join(new_tags)
            return prompt
            
    def _add_variation(self, prompt: str, tags: list) -> tuple:
        """Add creative variations"""
        cursor = self.conn.cursor()
        
        # Find unexplored high-potential tags
        cursor.execute('''SELECT tag FROM tag_analysis 
            WHERE weight > 0.6 AND tag NOT IN ({})
            ORDER BY RANDOM() LIMIT 3'''.format(','.join('?' * len(tags))), tags)
        new_tags = [r[0] for r in cursor.fetchall()]
        
        if new_tags:
            tags = tags + new_tags
            prompt = prompt + ", " + ", ".join(new_tags)
            
        return prompt, tags
        
    def _generate_image(self, prompt: str, tags: list, prefix: str, parent_id: str) -> dict:
        """Generate single image via ComfyUI"""
        seed = random.randint(0, 2**32)
        
        negative = """EasyNegative, bad-hands-5, (child:2.0), (kid:2.0), (teen:2.0),
(saggy:1.5), (bad anatomy:1.4), (deformed:1.4), (low quality:1.5), 
(blurry:1.3), (watermark:1.5), ugly, disfigured"""

        workflow = {
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "CyberRealistic.safetensors"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 768, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
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
        }
        
        try:
            data = json.dumps({"prompt": workflow}).encode()
            req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
            resp = urllib.request.urlopen(req, timeout=30)
            prompt_id = json.loads(resp.read()).get('prompt_id')
            
            # Wait for completion
            start = time.time()
            while time.time() - start < 180:
                try:
                    resp = urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
                    if prompt_id in json.loads(resp.read()):
                        filename = f"{prefix}_{seed}.png"
                        image_id = self.create_image_record(filename, prompt, negative, tags, seed, 
                                                           "auto_generation", parent_id)
                        return {'success': True, 'image_id': image_id, 'filename': filename, 'seed': seed}
                except:
                    pass
                time.sleep(2)
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    # ==================== STATISTICS ====================
    
    def get_stats(self) -> dict:
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM images')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating > 0')
        rated = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM gold_standards')
        gold = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(rating) FROM images WHERE rating > 0')
        avg = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM tag_analysis WHERE weight > 0.6')
        good_tags = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(images_generated) FROM generation_queue')
        auto_gen = cursor.fetchone()[0] or 0
        
        return {
            'total_images': total,
            'rated_images': rated,
            'gold_standards': gold,
            'average_rating': round(avg, 2),
            'high_performing_tags': good_tags,
            'auto_generated': auto_gen
        }
        
    def close(self):
        self.conn.close()


# ==================== TEST ====================
def test_system():
    print("="*60)
    print("  ADVANCED LEARNING SYSTEM TEST")
    print("="*60)
    
    als = AdvancedLearningSystem()
    
    # Test 1: Create image
    print("\n📝 TEST 1: Create Image with ID")
    image_id = als.create_image_record(
        "test_img.png",
        "masterpiece, best quality, petite, A cup, perky, tribal",
        "low quality, bad anatomy",
        ['petite', 'A cup', 'perky', 'tribal'],
        12345
    )
    print(f"   Created image: {image_id}")
    
    # Test 2: Rate image
    print("\n📝 TEST 2: Rating System (0-15)")
    
    # Low rating
    result = als.rate_image(image_id, 4)
    print(f"   Rating 4: {result['analysis']['rating_level']}")
    
    # Medium rating
    result = als.rate_image(image_id, 8)
    print(f"   Rating 8: {result['analysis']['rating_level']}")
    
    # Test 3: High rating (triggers auto-generation)
    print("\n📝 TEST 3: High Rating (10+) - Auto-Generation")
    
    # Create another image for high rating test
    image_id2 = als.create_image_record(
        "test_img2.png",
        "masterpiece, ultra detailed, petite, AA cup, pointy, visible abs, tribal warrior",
        "low quality",
        ['petite', 'AA cup', 'pointy', 'visible abs', 'tribal'],
        54321
    )
    
    result = als.rate_image(image_id2, 12)
    print(f"   Rating 12: {result['action']}")
    
    # Test 4: Perfect rating
    print("\n📝 TEST 4: Perfect Rating (15) - Gold Standard")
    
    image_id3 = als.create_image_record(
        "test_perfect.png",
        "masterpiece, perfect composition, petite, small bust, perky, heterochromia, tribal queen",
        "low quality",
        ['petite', 'small bust', 'perky', 'heterochromia', 'tribal'],
        99999
    )
    
    result = als.rate_image(image_id3, 15)
    print(f"   Rating 15: {result['action']}")
    
    # Stats
    print("\n📊 Statistics:")
    stats = als.get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
        
    print("\n✅ Advanced Learning System operational!")
    
    # Cleanup test images
    cursor = als.conn.cursor()
    cursor.execute("DELETE FROM images WHERE filename LIKE 'test_%'")
    als.conn.commit()
    
    als.close()


if __name__ == "__main__":
    test_system()
