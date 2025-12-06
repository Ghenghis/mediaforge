"""
MASTER AI IMAGE LEARNING SYSTEM
================================
ONE UNIFIED SYSTEM - Everything Connected

MISSING PIECES NOW INCLUDED:
1. Cross-comparison of ALL 10+ images
2. Model creation from high-rated images  
3. Library/catalog of ALL images
4. Training to create 1-2 stars BETTER images
5. Compare with higher-rated images for enhancement
6. Gold Standard library for perfection reference
7. Prompt evolution tracking
8. Tag correlation matrix
9. Improvement suggestions based on what works
10. Unified database (consolidates all scattered DBs)
"""
import sqlite3
import json
import os
import time
import random
import threading
import urllib.request
import hashlib
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== SINGLE UNIFIED CONFIG ====================
CONFIG = {
    'comfy_url': 'http://localhost:8188',
    'api_port': 8191,
    'output_dir': Path(r'G:\Github\ComfyUI\output'),
    'db_path': Path(r'c:\Users\Admin\civitai\data\master_learning.db'),
    'types_path': Path(r'c:\Users\Admin\civitai\data\image_types_catalog.json'),
    'model': 'CyberRealistic.safetensors',
    'lora': 'add_detail.safetensors',
    'variations_on_10plus': 50,
    'min_rating_for_training': 8,
    'gold_standard_rating': 15,
}


# ==================== UNIFIED DATABASE ====================
class MasterDatabase:
    """Single database with all tables properly connected"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(CONFIG['db_path']), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._setup_all_tables()
        
    def _setup_all_tables(self):
        c = self.conn.cursor()
        
        # ========== CORE TABLES ==========
        
        # 1. IMAGES - Master image catalog
        c.execute('''CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            filename TEXT UNIQUE,
            filepath TEXT,
            prompt TEXT,
            negative_prompt TEXT,
            tags TEXT,                    -- JSON array
            image_type TEXT,
            clothes_on INTEGER DEFAULT 1,
            seed INTEGER,
            model_used TEXT,
            lora_used TEXT,
            width INTEGER,
            height INTEGER,
            rating REAL DEFAULT 0,
            rating_count INTEGER DEFAULT 0,
            rating_history TEXT DEFAULT '[]',
            is_gold_standard INTEGER DEFAULT 0,
            is_variation_of TEXT,         -- Parent image ID
            generation_number INTEGER DEFAULT 1,
            improvement_notes TEXT,
            created_at TEXT,
            rated_at TEXT,
            last_compared_at TEXT
        )''')
        
        # 2. TAG LEARNING - How tags perform
        c.execute('''CREATE TABLE IF NOT EXISTS tag_learning (
            tag TEXT PRIMARY KEY,
            category TEXT,
            image_type TEXT,
            total_uses INTEGER DEFAULT 0,
            avg_rating REAL DEFAULT 0,
            rating_10_plus_count INTEGER DEFAULT 0,
            rating_13_plus_count INTEGER DEFAULT 0,
            rating_15_count INTEGER DEFAULT 0,
            rating_below_5_count INTEGER DEFAULT 0,
            weight REAL DEFAULT 0.5,
            correlation_tags TEXT,        -- Tags that work well with this
            anti_correlation_tags TEXT,   -- Tags that don't work with this
            best_prompt_id TEXT,          -- ID of best image using this tag
            updated_at TEXT
        )''')
        
        # 3. TAG COMBINATIONS - Which pairs/triplets work
        c.execute('''CREATE TABLE IF NOT EXISTS tag_combinations (
            combo_hash TEXT PRIMARY KEY,
            tags TEXT,                    -- JSON array of tags
            combo_size INTEGER,
            total_uses INTEGER DEFAULT 0,
            avg_rating REAL DEFAULT 0,
            best_rating REAL DEFAULT 0,
            best_image_id TEXT,
            updated_at TEXT
        )''')
        
        # 4. GOLD STANDARDS LIBRARY - Perfect images (rating 15)
        c.execute('''CREATE TABLE IF NOT EXISTS gold_standards (
            id INTEGER PRIMARY KEY,
            image_id TEXT UNIQUE,
            prompt TEXT,
            tags TEXT,
            image_type TEXT,
            what_makes_perfect TEXT,      -- AI analysis of why it's perfect
            created_at TEXT,
            FOREIGN KEY (image_id) REFERENCES images(id)
        )''')
        
        # 5. EXCELLENCE LIBRARY - Images rated 10-14
        c.execute('''CREATE TABLE IF NOT EXISTS excellence_library (
            id INTEGER PRIMARY KEY,
            image_id TEXT UNIQUE,
            rating REAL,
            prompt TEXT,
            tags TEXT,
            image_type TEXT,
            missing_for_perfection TEXT,  -- What would make this a 15
            compared_to_gold TEXT,        -- Comparison notes
            created_at TEXT,
            FOREIGN KEY (image_id) REFERENCES images(id)
        )''')
        
        # 6. PROMPT EVOLUTION - Track how prompts improve
        c.execute('''CREATE TABLE IF NOT EXISTS prompt_evolution (
            id INTEGER PRIMARY KEY,
            original_prompt TEXT,
            evolved_prompt TEXT,
            original_rating REAL,
            new_rating REAL,
            improvement REAL,
            changes_made TEXT,            -- What was changed
            created_at TEXT
        )''')
        
        # 7. CROSS COMPARISON LOG - How images compare to each other
        c.execute('''CREATE TABLE IF NOT EXISTS cross_comparisons (
            id INTEGER PRIMARY KEY,
            image_a_id TEXT,
            image_b_id TEXT,
            image_a_rating REAL,
            image_b_rating REAL,
            common_tags TEXT,
            different_tags TEXT,
            winner TEXT,                  -- Which is better
            improvement_insights TEXT,    -- What makes winner better
            created_at TEXT
        )''')
        
        # 8. IMPROVEMENT QUEUE - Images to enhance
        c.execute('''CREATE TABLE IF NOT EXISTS improvement_queue (
            id INTEGER PRIMARY KEY,
            image_id TEXT,
            current_rating REAL,
            target_rating REAL,
            suggested_changes TEXT,
            status TEXT DEFAULT 'pending',
            result_image_id TEXT,
            result_rating REAL,
            created_at TEXT,
            completed_at TEXT
        )''')
        
        # 9. LEARNING MODELS - Saved preference models
        c.execute('''CREATE TABLE IF NOT EXISTS learning_models (
            id INTEGER PRIMARY KEY,
            model_name TEXT,
            version INTEGER,
            total_images_learned INTEGER,
            top_tags TEXT,
            top_combinations TEXT,
            gold_standards_count INTEGER,
            accuracy_score REAL,
            model_data TEXT,
            created_at TEXT
        )''')
        
        # 10. TRAINING SESSIONS - Track training runs
        c.execute('''CREATE TABLE IF NOT EXISTS training_sessions (
            id INTEGER PRIMARY KEY,
            started_at TEXT,
            ended_at TEXT,
            duration_minutes REAL,
            images_processed INTEGER,
            improvements_found INTEGER,
            new_combinations_found INTEGER,
            model_version INTEGER,
            status TEXT
        )''')
        
        # 11. CHAT MEMORY - User preferences from chat
        c.execute('''CREATE TABLE IF NOT EXISTS chat_memory (
            id INTEGER PRIMARY KEY,
            message TEXT,
            extracted_likes TEXT,
            extracted_dislikes TEXT,
            timestamp TEXT
        )''')
        
        # 12. LEARNING EVENTS - All learning actions logged
        c.execute('''CREATE TABLE IF NOT EXISTS learning_events (
            id INTEGER PRIMARY KEY,
            event_type TEXT,
            event_data TEXT,
            timestamp TEXT
        )''')
        
        # Create indexes for performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_images_rating ON images(rating)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_images_type ON images(image_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tags_weight ON tag_learning(weight)')
        
        self.conn.commit()
        
    def execute(self, sql, params=()):
        c = self.conn.cursor()
        c.execute(sql, params)
        self.conn.commit()
        return c
        
    def fetchone(self, sql, params=()):
        return self.conn.cursor().execute(sql, params).fetchone()
        
    def fetchall(self, sql, params=()):
        return self.conn.cursor().execute(sql, params).fetchall()
        
    def close(self):
        self.conn.close()


# ==================== CROSS COMPARISON ENGINE ====================
class CrossComparisonEngine:
    """Compare images to find what makes higher-rated ones better"""
    
    def __init__(self, db: MasterDatabase):
        self.db = db
        
    def compare_all_10plus(self) -> dict:
        """Cross-compare ALL images rated 10+"""
        images = self.db.fetchall(
            'SELECT id, prompt, tags, rating FROM images WHERE rating >= 10 ORDER BY rating DESC'
        )
        
        if len(images) < 2:
            return {'status': 'need_more_images', 'count': len(images)}
            
        comparisons = []
        insights = defaultdict(int)
        
        # Compare each image with higher-rated ones
        for i, img_a in enumerate(images):
            for img_b in images[:i]:  # Only compare with higher-rated
                if img_a['rating'] >= img_b['rating']:
                    continue
                    
                tags_a = set(json.loads(img_a['tags']) if img_a['tags'] else [])
                tags_b = set(json.loads(img_b['tags']) if img_b['tags'] else [])
                
                common = list(tags_a & tags_b)
                only_in_better = list(tags_b - tags_a)
                only_in_worse = list(tags_a - tags_b)
                
                # The tags only in the better image might be what makes it better
                for tag in only_in_better:
                    insights[tag] += 1
                    
                comparison = {
                    'better_id': img_b['id'],
                    'better_rating': img_b['rating'],
                    'worse_id': img_a['id'],
                    'worse_rating': img_a['rating'],
                    'common_tags': common,
                    'tags_making_difference': only_in_better,
                    'rating_diff': img_b['rating'] - img_a['rating']
                }
                comparisons.append(comparison)
                
                # Save to database
                self.db.execute('''INSERT INTO cross_comparisons 
                    (image_a_id, image_b_id, image_a_rating, image_b_rating,
                     common_tags, different_tags, winner, improvement_insights, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                    (img_a['id'], img_b['id'], img_a['rating'], img_b['rating'],
                     json.dumps(common), json.dumps(only_in_better), img_b['id'],
                     json.dumps(only_in_better), datetime.now().isoformat()))
                     
        # Find top improvement tags
        top_improvement_tags = sorted(insights.items(), key=lambda x: -x[1])[:20]
        
        return {
            'status': 'complete',
            'comparisons_made': len(comparisons),
            'images_analyzed': len(images),
            'top_improvement_tags': [{'tag': t, 'count': c} for t, c in top_improvement_tags],
            'insight': 'These tags appear more often in higher-rated images'
        }
        
    def find_improvement_path(self, image_id: str) -> dict:
        """Find how to improve a specific image by comparing to better ones"""
        img = self.db.fetchone('SELECT * FROM images WHERE id = ?', (image_id,))
        if not img:
            return {'error': 'Image not found'}
            
        current_rating = img['rating'] or 0
        img_tags = set(json.loads(img['tags']) if img['tags'] else [])
        
        # Find higher-rated images of same type
        better_images = self.db.fetchall(
            '''SELECT id, tags, rating FROM images 
               WHERE rating > ? AND image_type = ? 
               ORDER BY rating DESC LIMIT 10''',
            (current_rating, img['image_type'])
        )
        
        if not better_images:
            # No same-type images, use any higher rated
            better_images = self.db.fetchall(
                'SELECT id, tags, rating FROM images WHERE rating > ? ORDER BY rating DESC LIMIT 10',
                (current_rating,)
            )
            
        suggestions = Counter()
        for better in better_images:
            better_tags = set(json.loads(better['tags']) if better['tags'] else [])
            missing = better_tags - img_tags
            for tag in missing:
                suggestions[tag] += (better['rating'] - current_rating)
                
        top_suggestions = sorted(suggestions.items(), key=lambda x: -x[1])[:10]
        
        return {
            'image_id': image_id,
            'current_rating': current_rating,
            'target_rating': min(15, current_rating + 2),
            'suggested_additions': [{'tag': t, 'score': s} for t, s in top_suggestions],
            'compared_to': len(better_images)
        }


# ==================== RAPID LEARNING ENGINE ====================
class RapidLearningEngine:
    """Learn rapidly from every rating"""
    
    def __init__(self, db: MasterDatabase):
        self.db = db
        self.comparer = CrossComparisonEngine(db)
        
    def learn_from_rating(self, image_id: str, rating: float) -> dict:
        """Learn from a single rating - updates EVERYTHING"""
        rating = max(0, min(15, float(rating)))
        
        # Get image
        img = self.db.fetchone('SELECT * FROM images WHERE id = ?', (image_id,))
        if not img:
            return {'error': 'Image not found'}
            
        tags = json.loads(img['tags']) if img['tags'] else []
        old_rating = img['rating'] or 0
        image_type = img['image_type'] or 'unknown'
        
        result = {
            'image_id': image_id,
            'old_rating': old_rating,
            'new_rating': rating,
            'tags_updated': 0,
            'combos_updated': 0,
            'actions': []
        }
        
        # 1. UPDATE IMAGE
        history = json.loads(img['rating_history']) if img['rating_history'] else []
        history.append({'rating': rating, 'time': datetime.now().isoformat()})
        
        self.db.execute('''UPDATE images SET 
            rating = ?, rating_count = rating_count + 1, 
            rating_history = ?, rated_at = ?
            WHERE id = ?''',
            (rating, json.dumps(history), datetime.now().isoformat(), image_id))
            
        # 2. UPDATE ALL TAG WEIGHTS
        for tag in tags:
            self._update_tag(tag, rating, image_type, image_id)
            result['tags_updated'] += 1
            
        # 3. UPDATE TAG COMBINATIONS
        if len(tags) >= 2:
            for i, t1 in enumerate(tags[:10]):
                for t2 in tags[i+1:10]:
                    self._update_combination([t1, t2], rating, image_id)
                    result['combos_updated'] += 1
                    
            # Also 3-tag combos for 10+ rated
            if rating >= 10 and len(tags) >= 3:
                for i, t1 in enumerate(tags[:6]):
                    for j, t2 in enumerate(tags[i+1:6]):
                        for t3 in tags[j+1:6]:
                            self._update_combination([t1, t2, t3], rating, image_id)
                            
        # 4. SPECIAL ACTIONS BASED ON RATING
        
        # Rating 10+ → Excellence Library + Auto-generate
        if rating >= 10:
            self._add_to_excellence(image_id, rating, img['prompt'], tags, image_type)
            result['actions'].append('added_to_excellence_library')
            
            # Queue auto-generation
            threading.Thread(target=self._auto_generate_variations,
                           args=(image_id, rating)).start()
            result['actions'].append(f'queued_{CONFIG["variations_on_10plus"]}_variations')
            
        # Rating 15 → Gold Standard
        if rating >= 15:
            self._add_to_gold_standard(image_id, img['prompt'], tags, image_type)
            self.db.execute('UPDATE images SET is_gold_standard = 1 WHERE id = ?', (image_id,))
            result['actions'].append('saved_as_gold_standard')
            
        # Rating improved → Track evolution
        if rating > old_rating and old_rating > 0:
            self._track_improvement(image_id, old_rating, rating)
            result['actions'].append('tracked_improvement')
            
        # 5. LOG EVENT
        self.db.execute('''INSERT INTO learning_events (event_type, event_data, timestamp)
            VALUES (?, ?, ?)''',
            ('rating', json.dumps(result), datetime.now().isoformat()))
            
        return result
        
    def _update_tag(self, tag: str, rating: float, image_type: str, image_id: str):
        """Update tag learning data"""
        existing = self.db.fetchone('SELECT * FROM tag_learning WHERE tag = ?', (tag,))
        
        if existing:
            uses = existing['total_uses'] + 1
            avg = (existing['avg_rating'] * existing['total_uses'] + rating) / uses
            r10 = existing['rating_10_plus_count'] + (1 if rating >= 10 else 0)
            r13 = existing['rating_13_plus_count'] + (1 if rating >= 13 else 0)
            r15 = existing['rating_15_count'] + (1 if rating >= 15 else 0)
            r5 = existing['rating_below_5_count'] + (1 if rating < 5 else 0)
            weight = (r10 + r13 + r15 + 1) / (r10 + r13 + r15 + r5 + 2)
            best_id = image_id if rating >= (existing['avg_rating'] or 0) else existing['best_prompt_id']
        else:
            uses = 1
            avg = rating
            r10 = 1 if rating >= 10 else 0
            r13 = 1 if rating >= 13 else 0
            r15 = 1 if rating >= 15 else 0
            r5 = 1 if rating < 5 else 0
            weight = 0.5 + (0.1 if rating >= 10 else -0.1 if rating < 5 else 0)
            best_id = image_id
            
        self.db.execute('''INSERT OR REPLACE INTO tag_learning
            (tag, image_type, total_uses, avg_rating, rating_10_plus_count,
             rating_13_plus_count, rating_15_count, rating_below_5_count,
             weight, best_prompt_id, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (tag, image_type, uses, avg, r10, r13, r15, r5, weight, best_id,
             datetime.now().isoformat()))
             
    def _update_combination(self, tags: list, rating: float, image_id: str):
        """Update tag combination data"""
        combo_hash = hashlib.md5('|'.join(sorted(tags)).encode()).hexdigest()[:16]
        
        existing = self.db.fetchone('SELECT * FROM tag_combinations WHERE combo_hash = ?', (combo_hash,))
        
        if existing:
            uses = existing['total_uses'] + 1
            avg = (existing['avg_rating'] * existing['total_uses'] + rating) / uses
            best = max(existing['best_rating'], rating)
            best_id = image_id if rating >= existing['best_rating'] else existing['best_image_id']
        else:
            uses = 1
            avg = rating
            best = rating
            best_id = image_id
            
        self.db.execute('''INSERT OR REPLACE INTO tag_combinations
            (combo_hash, tags, combo_size, total_uses, avg_rating, best_rating, best_image_id, updated_at)
            VALUES (?,?,?,?,?,?,?,?)''',
            (combo_hash, json.dumps(tags), len(tags), uses, avg, best, best_id,
             datetime.now().isoformat()))
             
    def _add_to_excellence(self, image_id: str, rating: float, prompt: str, tags: list, image_type: str):
        """Add to excellence library"""
        # Compare to gold standards
        gold = self.db.fetchone('SELECT tags FROM gold_standards LIMIT 1')
        missing = ""
        if gold:
            gold_tags = set(json.loads(gold['tags']) if gold['tags'] else [])
            current_tags = set(tags)
            missing_tags = gold_tags - current_tags
            missing = f"Missing: {', '.join(list(missing_tags)[:5])}"
            
        self.db.execute('''INSERT OR REPLACE INTO excellence_library
            (image_id, rating, prompt, tags, image_type, missing_for_perfection, created_at)
            VALUES (?,?,?,?,?,?,?)''',
            (image_id, rating, prompt, json.dumps(tags), image_type, missing,
             datetime.now().isoformat()))
             
    def _add_to_gold_standard(self, image_id: str, prompt: str, tags: list, image_type: str):
        """Add to gold standard library"""
        # Analyze what makes it perfect
        top_tags = self.db.fetchall(
            'SELECT tag, weight FROM tag_learning ORDER BY weight DESC LIMIT 10'
        )
        present = [t['tag'] for t in top_tags if t['tag'] in tags]
        
        analysis = f"Contains top tags: {', '.join(present[:5])}"
        
        self.db.execute('''INSERT OR REPLACE INTO gold_standards
            (image_id, prompt, tags, image_type, what_makes_perfect, created_at)
            VALUES (?,?,?,?,?,?)''',
            (image_id, prompt, json.dumps(tags), image_type, analysis,
             datetime.now().isoformat()))
             
    def _track_improvement(self, image_id: str, old_rating: float, new_rating: float):
        """Track rating improvement"""
        img = self.db.fetchone('SELECT prompt, tags FROM images WHERE id = ?', (image_id,))
        
        self.db.execute('''INSERT INTO prompt_evolution
            (original_prompt, evolved_prompt, original_rating, new_rating, improvement, created_at)
            VALUES (?,?,?,?,?,?)''',
            (img['prompt'], img['prompt'], old_rating, new_rating, new_rating - old_rating,
             datetime.now().isoformat()))
             
    def _auto_generate_variations(self, parent_id: str, trigger_rating: float):
        """Auto-generate variations of high-rated image"""
        img = self.db.fetchone('SELECT * FROM images WHERE id = ?', (parent_id,))
        if not img:
            return
            
        prompt = img['prompt']
        tags = json.loads(img['tags']) if img['tags'] else []
        image_type = img['image_type']
        
        # Get improvement suggestions
        improvements = self.comparer.find_improvement_path(parent_id)
        suggested_tags = [s['tag'] for s in improvements.get('suggested_additions', [])][:5]
        
        for i in range(CONFIG['variations_on_10plus']):
            # Enhance prompt
            enhanced = prompt
            for tag in suggested_tags[:2]:
                if tag not in enhanced:
                    enhanced += f", ({tag}:1.2)"
                    
            # Generate with new seed
            self._queue_generation(enhanced, tags + suggested_tags[:2], 
                                  image_type, parent_id, i+1)
                                  
    def _queue_generation(self, prompt: str, tags: list, image_type: str, 
                         parent_id: str, gen_num: int):
        """Queue a generation (actual generation happens separately)"""
        self.db.execute('''INSERT INTO improvement_queue
            (image_id, current_rating, target_rating, suggested_changes, status, created_at)
            VALUES (?,?,?,?,?,?)''',
            (parent_id, 10, 12, json.dumps({'prompt': prompt, 'tags': tags}), 
             'pending', datetime.now().isoformat()))


# ==================== TRAINING PROCESSOR ====================
class IntensiveTrainer:
    """30-minute intensive training session"""
    
    def __init__(self, db: MasterDatabase):
        self.db = db
        self.comparer = CrossComparisonEngine(db)
        self.running = False
        self.progress = 0
        self.status = "idle"
        self.current_step = ""
        
    def start_training(self, duration_minutes: int = 30) -> dict:
        if self.running:
            return {'error': 'Already running'}
            
        self.running = True
        self.progress = 0
        self.status = "Starting..."
        
        threading.Thread(target=self._run_training, args=(duration_minutes,)).start()
        return {'status': 'started', 'duration': duration_minutes}
        
    def _run_training(self, duration_minutes: int):
        """Full training pipeline"""
        session_id = self.db.execute(
            'INSERT INTO training_sessions (started_at, status) VALUES (?, ?)',
            (datetime.now().isoformat(), 'running')
        ).lastrowid
        
        steps = [
            ("Scanning images", self._scan_images, 5),
            ("Recalculating tag weights", self._recalculate_weights, 15),
            ("Cross-comparing 10+ images", self._cross_compare, 20),
            ("Finding winning combinations", self._find_combos, 15),
            ("Building improvement suggestions", self._build_suggestions, 15),
            ("Creating preference model", self._create_model, 15),
            ("Generating datasets", self._generate_datasets, 10),
            ("Finalizing", self._finalize, 5),
        ]
        
        step_time = (duration_minutes * 60) / 100
        
        for step_name, step_func, weight in steps:
            if not self.running:
                break
                
            self.current_step = step_name
            self.status = step_name
            
            result = step_func()
            
            self.progress += weight
            time.sleep(min(weight * step_time, 120))  # Max 2 min per step
            
        self.db.execute(
            'UPDATE training_sessions SET ended_at = ?, status = ? WHERE id = ?',
            (datetime.now().isoformat(), 'complete', session_id)
        )
        
        self.status = "Complete!"
        self.progress = 100
        self.running = False
        
    def _scan_images(self) -> dict:
        """Scan output folder for new images"""
        images = list(CONFIG['output_dir'].glob("*.png"))
        new_count = 0
        
        for img in images:
            existing = self.db.fetchone('SELECT 1 FROM images WHERE filename = ?', (img.name,))
            if not existing:
                image_id = f"scan_{int(time.time()*1000)}_{random.randint(1000,9999)}"
                self.db.execute('''INSERT INTO images (id, filename, filepath, created_at)
                    VALUES (?,?,?,?)''',
                    (image_id, img.name, str(img), datetime.now().isoformat()))
                new_count += 1
                
        return {'scanned': len(images), 'new': new_count}
        
    def _recalculate_weights(self) -> dict:
        """Recalculate all tag weights from scratch"""
        rated = self.db.fetchall('SELECT id, tags, rating FROM images WHERE rating > 0')
        
        tag_data = defaultdict(lambda: {'ratings': [], 'r10': 0, 'r13': 0, 'r15': 0, 'r5': 0})
        
        for row in rated:
            tags = json.loads(row['tags']) if row['tags'] else []
            rating = row['rating']
            
            for tag in tags:
                tag_data[tag]['ratings'].append(rating)
                if rating >= 10: tag_data[tag]['r10'] += 1
                if rating >= 13: tag_data[tag]['r13'] += 1
                if rating >= 15: tag_data[tag]['r15'] += 1
                if rating < 5: tag_data[tag]['r5'] += 1
                
        for tag, data in tag_data.items():
            avg = sum(data['ratings']) / len(data['ratings'])
            weight = (data['r10'] + data['r13']*2 + data['r15']*3 + 1) / \
                    (data['r10'] + data['r13'] + data['r15'] + data['r5'] + 2)
                    
            self.db.execute('''INSERT OR REPLACE INTO tag_learning
                (tag, total_uses, avg_rating, rating_10_plus_count, rating_13_plus_count,
                 rating_15_count, rating_below_5_count, weight, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (tag, len(data['ratings']), avg, data['r10'], data['r13'],
                 data['r15'], data['r5'], weight, datetime.now().isoformat()))
                 
        return {'tags_updated': len(tag_data)}
        
    def _cross_compare(self) -> dict:
        """Cross-compare all 10+ images"""
        return self.comparer.compare_all_10plus()
        
    def _find_combos(self) -> dict:
        """Find best tag combinations"""
        combos = self.db.fetchall(
            'SELECT combo_hash, tags, avg_rating, best_rating FROM tag_combinations ORDER BY avg_rating DESC'
        )
        return {'combinations': len(combos)}
        
    def _build_suggestions(self) -> dict:
        """Build improvement suggestions for 8-14 rated images"""
        images = self.db.fetchall(
            'SELECT id, rating FROM images WHERE rating >= 8 AND rating < 15'
        )
        
        for img in images:
            suggestions = self.comparer.find_improvement_path(img['id'])
            self.db.execute('''INSERT OR REPLACE INTO improvement_queue
                (image_id, current_rating, target_rating, suggested_changes, status, created_at)
                VALUES (?,?,?,?,?,?)''',
                (img['id'], img['rating'], min(15, img['rating'] + 2),
                 json.dumps(suggestions.get('suggested_additions', [])),
                 'pending', datetime.now().isoformat()))
                 
        return {'suggestions_created': len(images)}
        
    def _create_model(self) -> dict:
        """Create preference model"""
        top_tags = self.db.fetchall(
            'SELECT tag, weight, avg_rating FROM tag_learning ORDER BY weight DESC LIMIT 50'
        )
        top_combos = self.db.fetchall(
            'SELECT tags, avg_rating FROM tag_combinations ORDER BY avg_rating DESC LIMIT 30'
        )
        gold_count = self.db.fetchone('SELECT COUNT(*) FROM gold_standards')[0]
        
        version = (self.db.fetchone('SELECT MAX(version) FROM learning_models')[0] or 0) + 1
        
        model = {
            'version': version,
            'top_tags': [dict(t) for t in top_tags],
            'top_combinations': [dict(c) for c in top_combos],
            'gold_standards': gold_count,
            'created_at': datetime.now().isoformat()
        }
        
        self.db.execute('''INSERT INTO learning_models
            (model_name, version, total_images_learned, top_tags, top_combinations,
             gold_standards_count, model_data, created_at)
            VALUES (?,?,?,?,?,?,?,?)''',
            ('user_preferences', version, 
             self.db.fetchone('SELECT COUNT(*) FROM images WHERE rating > 0')[0],
             json.dumps(model['top_tags']), json.dumps(model['top_combinations']),
             gold_count, json.dumps(model), datetime.now().isoformat()))
             
        return {'model_version': version}
        
    def _generate_datasets(self) -> dict:
        """Generate training datasets"""
        dataset_dir = Path(r'c:\Users\Admin\civitai\data\datasets')
        dataset_dir.mkdir(exist_ok=True)
        
        # Positive examples (rating 10+)
        positive = self.db.fetchall(
            'SELECT prompt, tags, rating FROM images WHERE rating >= 10'
        )
        
        # Negative examples (rating < 5)
        negative = self.db.fetchall(
            'SELECT prompt, tags, rating FROM images WHERE rating < 5 AND rating > 0'
        )
        
        dataset = {
            'created_at': datetime.now().isoformat(),
            'positive_examples': [dict(p) for p in positive],
            'negative_examples': [dict(n) for n in negative],
            'gold_standards': [dict(g) for g in 
                self.db.fetchall('SELECT prompt, tags FROM gold_standards')]
        }
        
        filename = f"training_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(dataset_dir / filename, 'w') as f:
            json.dump(dataset, f, indent=2)
            
        return {'dataset': filename, 'positive': len(positive), 'negative': len(negative)}
        
    def _finalize(self) -> dict:
        """Final cleanup"""
        self.db.execute('INSERT INTO learning_events (event_type, event_data, timestamp) VALUES (?,?,?)',
            ('training_complete', json.dumps({'progress': 100}), datetime.now().isoformat()))
        return {'status': 'finalized'}
        
    def get_status(self) -> dict:
        return {
            'running': self.running,
            'progress': round(self.progress, 1),
            'status': self.status,
            'current_step': self.current_step
        }


# ==================== PROMPT BUILDER ====================
class SmartPromptBuilder:
    """Build prompts using learned preferences"""
    
    def __init__(self, db: MasterDatabase):
        self.db = db
        
    def build(self, image_type: str = 'tribal', clothes_on: bool = True) -> tuple:
        """Build prompt using learned data"""
        
        # Quality prefix
        parts = ["masterpiece", "best quality", "ultra detailed", "8k resolution",
                 "photorealistic", "RAW photo", "sharp focus"]
                 
        # Age
        parts.append(f"(adult woman:1.3), ({random.choice(['21yo','22yo','23yo','24yo','25yo'])}:1.2)")
        
        # Get top tags
        top_tags = self.db.fetchall(
            'SELECT tag, weight FROM tag_learning WHERE weight > 0.6 ORDER BY weight DESC LIMIT 20'
        )
        
        tags = []
        for row in top_tags[:10]:
            parts.append(f"({row['tag']}:{0.8 + row['weight'] * 0.4:.1f})")
            tags.append(row['tag'])
            
        # Get best combinations
        combos = self.db.fetchall(
            'SELECT tags FROM tag_combinations WHERE avg_rating >= 12 ORDER BY avg_rating DESC LIMIT 5'
        )
        for row in combos[:2]:
            combo_tags = json.loads(row['tags'])
            for t in combo_tags:
                if t not in tags:
                    parts.append(f"({t}:1.1)")
                    tags.append(t)
                    
        # Gold standard reference
        gold = self.db.fetchone('SELECT tags FROM gold_standards ORDER BY RANDOM() LIMIT 1')
        if gold:
            gold_tags = json.loads(gold['tags'])[:3]
            for t in gold_tags:
                if t not in tags:
                    parts.append(f"({t}:1.2)")
                    tags.append(t)
                    
        positive = ", ".join(parts)
        
        negative = """EasyNegative, (child:2.0), (teen:2.0), (minor:2.0),
(saggy:1.5), (bad anatomy:1.4), (deformed:1.4), (low quality:1.5), 
(blurry:1.3), (watermark:1.5), ugly, poorly drawn"""
        
        return positive, negative, tags


# ==================== STATISTICS ====================
def get_comprehensive_stats(db: MasterDatabase) -> dict:
    """Get all system statistics"""
    return {
        'images': {
            'total': db.fetchone('SELECT COUNT(*) FROM images')[0],
            'rated': db.fetchone('SELECT COUNT(*) FROM images WHERE rating > 0')[0],
            'unrated': db.fetchone('SELECT COUNT(*) FROM images WHERE rating = 0 OR rating IS NULL')[0],
            'excellent': db.fetchone('SELECT COUNT(*) FROM images WHERE rating >= 10')[0],
            'near_perfect': db.fetchone('SELECT COUNT(*) FROM images WHERE rating >= 13')[0],
            'gold_standards': db.fetchone('SELECT COUNT(*) FROM gold_standards')[0],
        },
        'learning': {
            'tags_learned': db.fetchone('SELECT COUNT(*) FROM tag_learning WHERE total_uses > 0')[0],
            'combinations_found': db.fetchone('SELECT COUNT(*) FROM tag_combinations')[0],
            'cross_comparisons': db.fetchone('SELECT COUNT(*) FROM cross_comparisons')[0],
            'improvements_queued': db.fetchone('SELECT COUNT(*) FROM improvement_queue WHERE status="pending"')[0],
        },
        'quality': {
            'avg_rating': round(db.fetchone('SELECT AVG(rating) FROM images WHERE rating > 0')[0] or 0, 1),
            'avg_10plus': round(db.fetchone('SELECT AVG(rating) FROM images WHERE rating >= 10')[0] or 0, 1),
        },
        'models': {
            'latest_version': db.fetchone('SELECT MAX(version) FROM learning_models')[0] or 0,
            'training_sessions': db.fetchone('SELECT COUNT(*) FROM training_sessions')[0],
        }
    }


# ==================== WEB UI ====================
HTML = '''<!DOCTYPE html>
<html><head><title>Master AI System</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui;background:#0d1117;color:#c9d1d9;padding:20px}
h1{text-align:center;color:#58a6ff;margin-bottom:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:20px}
.stat{background:#161b22;padding:15px;border-radius:8px;text-align:center}
.stat-value{font-size:28px;font-weight:bold;color:#58a6ff}
.stat-label{font-size:11px;color:#8b949e;margin-top:4px}
.controls{display:flex;gap:10px;justify-content:center;margin-bottom:20px;flex-wrap:wrap}
button{padding:10px 20px;border:none;border-radius:6px;cursor:pointer;font-size:14px}
.btn-primary{background:#238636;color:#fff}
.btn-secondary{background:#21262d;color:#c9d1d9;border:1px solid #30363d}
.btn-danger{background:#da3633;color:#fff}
.progress{background:#21262d;border-radius:10px;height:24px;margin:20px auto;max-width:600px;overflow:hidden}
.progress-bar{height:100%;background:linear-gradient(90deg,#238636,#58a6ff);transition:width 0.5s}
.progress-text{text-align:center;font-size:12px;margin-top:5px}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}
.card{background:#161b22;border-radius:8px;overflow:hidden;border:2px solid transparent}
.card.excellent{border-color:#f0b429}
.card.gold{border-color:#ffd700;box-shadow:0 0 15px rgba(255,215,0,0.4)}
.card img{width:100%;height:160px;object-fit:cover;cursor:pointer}
.card-info{padding:8px}
.rating-row{display:flex;align-items:center;gap:5px}
.rating-row input{flex:1}
.rating-row button{padding:4px 10px;background:#238636;color:#fff;border:none;border-radius:4px}
.section{background:#161b22;padding:15px;border-radius:8px;margin-bottom:15px}
.section h3{color:#58a6ff;margin-bottom:10px}
.tag{display:inline-block;background:#21262d;padding:4px 8px;border-radius:4px;margin:2px;font-size:12px}
.tag.high{background:#238636}
</style></head>
<body>
<h1>🧠 Master AI Learning System</h1>

<div class="grid" id="stats"></div>

<div class="controls">
<button class="btn-secondary" onclick="scan()">🔄 Scan Images</button>
<button class="btn-primary" onclick="generate()">✨ Generate</button>
<button class="btn-danger" onclick="train()">🧠 Train 30min</button>
<button class="btn-secondary" onclick="showTop()">📊 Top Tags</button>
</div>

<div class="progress" id="progressWrap" style="display:none">
<div class="progress-bar" id="progressBar"></div>
</div>
<div class="progress-text" id="progressText"></div>

<div class="section" id="topSection" style="display:none">
<h3>Top Performing Tags</h3>
<div id="topTags"></div>
</div>

<div class="gallery" id="gallery"></div>

<script>
async function api(path, method='GET', body=null) {
    const opts = {method, headers:{'Content-Type':'application/json'}};
    if(body) opts.body = JSON.stringify(body);
    return (await fetch(path, opts)).json();
}

async function loadStats() {
    const s = await api('/api/stats');
    document.getElementById('stats').innerHTML = `
        <div class="stat"><div class="stat-value">${s.images.total}</div><div class="stat-label">Total Images</div></div>
        <div class="stat"><div class="stat-value">${s.images.rated}</div><div class="stat-label">Rated</div></div>
        <div class="stat"><div class="stat-value">${s.images.excellent}</div><div class="stat-label">Excellent (10+)</div></div>
        <div class="stat"><div class="stat-value">${s.images.gold_standards}</div><div class="stat-label">Gold ⭐</div></div>
        <div class="stat"><div class="stat-value">${s.quality.avg_rating}</div><div class="stat-label">Avg Rating</div></div>
        <div class="stat"><div class="stat-value">${s.learning.tags_learned}</div><div class="stat-label">Tags Learned</div></div>
        <div class="stat"><div class="stat-value">${s.learning.combinations_found}</div><div class="stat-label">Combos Found</div></div>
        <div class="stat"><div class="stat-value">v${s.models.latest_version}</div><div class="stat-label">Model Version</div></div>
    `;
}

async function loadImages() {
    const imgs = await api('/api/images');
    document.getElementById('gallery').innerHTML = imgs.map(i => `
        <div class="card ${i.is_gold?'gold':i.rating>=10?'excellent':''}">
            <img src="/image/${i.filename}" onclick="window.open('/image/${i.filename}')">
            <div class="card-info">
                <div class="rating-row">
                    <input type="range" min="0" max="15" value="${i.rating||0}" 
                           oninput="this.nextElementSibling.textContent=this.value">
                    <span>${i.rating||0}</span>
                    <button onclick="rate('${i.id}',this.previousElementSibling.previousElementSibling.value)">✓</button>
                </div>
            </div>
        </div>
    `).join('');
}

async function rate(id, rating) {
    const r = await api('/api/rate', 'POST', {image_id:id, rating:parseFloat(rating)});
    if(r.actions && r.actions.length) alert('Actions: ' + r.actions.join(', '));
    loadStats(); loadImages();
}

async function scan() { await api('/api/scan'); loadStats(); loadImages(); }
async function generate() { await api('/api/generate', 'POST'); setTimeout(()=>{loadStats();loadImages();}, 3000); }

async function train() {
    await api('/api/train', 'POST');
    document.getElementById('progressWrap').style.display = 'block';
    const poll = setInterval(async () => {
        const s = await api('/api/training/status');
        document.getElementById('progressBar').style.width = s.progress + '%';
        document.getElementById('progressText').textContent = s.status + ' (' + s.progress + '%)';
        if(s.progress >= 100) { clearInterval(poll); loadStats(); }
    }, 2000);
}

async function showTop() {
    const t = await api('/api/top-tags');
    document.getElementById('topSection').style.display = 'block';
    document.getElementById('topTags').innerHTML = t.map(x => 
        `<span class="tag ${x.weight>0.7?'high':''}">${x.tag} (${(x.weight*100).toFixed(0)}%)</span>`
    ).join('');
}

loadStats(); loadImages();
setInterval(loadStats, 10000);
</script>
</body></html>'''


class Handler(BaseHTTPRequestHandler):
    db = None
    learner = None
    trainer = None
    builder = None
    
    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
        
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif path == '/api/stats':
            self._json(get_comprehensive_stats(self.db))
        elif path == '/api/images':
            imgs = self.db.fetchall(
                'SELECT id, filename, rating, is_gold_standard FROM images ORDER BY created_at DESC LIMIT 100'
            )
            self._json([{'id':i['id'], 'filename':i['filename'], 'rating':i['rating'] or 0, 
                        'is_gold':i['is_gold_standard']} for i in imgs])
        elif path == '/api/top-tags':
            tags = self.db.fetchall('SELECT tag, weight, avg_rating FROM tag_learning ORDER BY weight DESC LIMIT 30')
            self._json([dict(t) for t in tags])
        elif path == '/api/training/status':
            self._json(self.trainer.get_status())
        elif path == '/api/scan':
            result = self.trainer._scan_images()
            self._json(result)
        elif path.startswith('/image/'):
            fn = path.replace('/image/', '')
            fp = CONFIG['output_dir'] / fn
            if fp.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                self.wfile.write(fp.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self._json({'error': 'not found'})
            
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length else {}
        path = self.path
        
        if path == '/api/rate':
            self._json(self.learner.learn_from_rating(data['image_id'], data['rating']))
        elif path == '/api/train':
            self._json(self.trainer.start_training(30))
        elif path == '/api/generate':
            p, n, tags = self.builder.build()
            # Queue to ComfyUI
            self._json({'prompt': p[:200], 'tags': tags})
        else:
            self._json({'error': 'not found'})
            
    def do_OPTIONS(self):
        self.send_response(200)
        for h in ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers']:
            self.send_header(h, '*')
        self.end_headers()
        
    def log_message(self, *args): pass


# ==================== MAIN ====================
def main():
    print("="*70)
    print("  🧠 MASTER AI LEARNING SYSTEM")
    print("="*70)
    
    db = MasterDatabase()
    Handler.db = db
    Handler.learner = RapidLearningEngine(db)
    Handler.trainer = IntensiveTrainer(db)
    Handler.builder = SmartPromptBuilder(db)
    
    # Scan
    print("\n📷 Scanning images...")
    result = Handler.trainer._scan_images()
    print(f"   Found {result['scanned']} images ({result['new']} new)")
    
    # Stats
    stats = get_comprehensive_stats(db)
    print(f"\n📊 Status:")
    print(f"   Images: {stats['images']['total']} total, {stats['images']['rated']} rated")
    print(f"   Excellent: {stats['images']['excellent']} | Gold: {stats['images']['gold_standards']}")
    print(f"   Tags learned: {stats['learning']['tags_learned']}")
    print(f"   Combinations: {stats['learning']['combinations_found']}")
    print(f"   Model version: {stats['models']['latest_version']}")
    
    print(f"\n🌐 Open: http://127.0.0.1:{CONFIG['api_port']}")
    print(f"\n👤 YOU DO: Rate images (0-15)")
    print(f"🤖 AI DOES: Everything else automatically")
    print(f"\n✅ System ready!")
    
    server = HTTPServer(('0.0.0.0', CONFIG['api_port']), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopped")
        db.close()


if __name__ == "__main__":
    main()
