"""
Preference Learning System
Learns from user ratings to improve prompt generation
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = Path(r"c:\Users\Admin\civitai\data\preferences.db")
CONFIG_PATH = Path(r"c:\Users\Admin\civitai\data\generation_config.json")

class PreferenceSystem:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH))
        self.setup_database()
        self.load_config()
        
    def setup_database(self):
        """Create tables for preference tracking"""
        cursor = self.conn.cursor()
        
        # Images table - stores generated images
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE,
                prompt TEXT,
                negative_prompt TEXT,
                tags TEXT,
                model TEXT,
                seed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rating INTEGER DEFAULT 0,
                rated_at TIMESTAMP
            )
        ''')
        
        # Tag preferences - learned from ratings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tag_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT UNIQUE,
                category TEXT,
                positive_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                weight REAL DEFAULT 1.0,
                last_updated TIMESTAMP
            )
        ''')
        
        # User selections - tracks dropdown choices
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                selection TEXT,
                use_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.5,
                last_used TIMESTAMP,
                UNIQUE(category, selection)
            )
        ''')
        
        # Generation sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT,
                style TEXT,
                total_images INTEGER DEFAULT 0,
                liked_images INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Chat learning - stores user feedback from chat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT,
                extracted_preferences TEXT,
                applied_to_prompt INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print("✅ Database initialized")
        
    def load_config(self):
        """Load generation config"""
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
    # ==================== RATING SYSTEM ====================
    
    def rate_image(self, filename: str, rating: int):
        """
        Rate an image (1-5 stars or thumbs up/down)
        1-2 = dislike, 3 = neutral, 4-5 = like
        """
        cursor = self.conn.cursor()
        
        # Update image rating
        cursor.execute('''
            UPDATE images SET rating = ?, rated_at = ? WHERE filename = ?
        ''', (rating, datetime.now(), filename))
        
        # Get the image's tags
        cursor.execute('SELECT tags FROM images WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        
        if result and result[0]:
            tags = json.loads(result[0])
            self._update_tag_preferences(tags, rating)
            
        self.conn.commit()
        print(f"✅ Rated {filename}: {rating} stars")
        
    def _update_tag_preferences(self, tags: list, rating: int):
        """Update tag weights based on rating"""
        cursor = self.conn.cursor()
        is_positive = rating >= 4
        is_negative = rating <= 2
        
        for tag in tags:
            # Check if tag exists
            cursor.execute('SELECT id, positive_count, negative_count FROM tag_preferences WHERE tag = ?', (tag,))
            result = cursor.fetchone()
            
            if result:
                pos = result[1] + (1 if is_positive else 0)
                neg = result[2] + (1 if is_negative else 0)
                # Calculate new weight: more likes = higher weight
                weight = (pos + 1) / (pos + neg + 2)  # Bayesian average
                
                cursor.execute('''
                    UPDATE tag_preferences 
                    SET positive_count = ?, negative_count = ?, weight = ?, last_updated = ?
                    WHERE tag = ?
                ''', (pos, neg, weight, datetime.now(), tag))
            else:
                pos = 1 if is_positive else 0
                neg = 1 if is_negative else 0
                weight = (pos + 1) / (pos + neg + 2)
                
                cursor.execute('''
                    INSERT INTO tag_preferences (tag, positive_count, negative_count, weight, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                ''', (tag, pos, neg, weight, datetime.now()))
                
    def get_preferred_tags(self, category: str = None, limit: int = 20):
        """Get top-rated tags, optionally filtered by category"""
        cursor = self.conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT tag, weight, positive_count, negative_count 
                FROM tag_preferences 
                WHERE category = ? AND weight > 0.5
                ORDER BY weight DESC, positive_count DESC
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT tag, weight, positive_count, negative_count 
                FROM tag_preferences 
                WHERE weight > 0.5
                ORDER BY weight DESC, positive_count DESC
                LIMIT ?
            ''', (limit,))
            
        return cursor.fetchall()
        
    def get_avoided_tags(self, limit: int = 20):
        """Get tags user dislikes"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT tag, weight, positive_count, negative_count 
            FROM tag_preferences 
            WHERE weight < 0.4 AND negative_count > 0
            ORDER BY weight ASC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
        
    # ==================== PROMPT ENHANCEMENT ====================
    
    def enhance_prompt(self, base_prompt: str, style: str = "tribal") -> str:
        """AI-powered prompt enhancement using learned preferences"""
        
        # Get preferred tags
        preferred = self.get_preferred_tags(limit=10)
        preferred_tags = [t[0] for t in preferred if t[1] > 0.6]
        
        # Get quality tags from config
        quality = self.config['quality_tags']['positive']
        
        # Build enhanced prompt
        enhanced_parts = []
        
        # Add quality tags
        enhanced_parts.extend(quality[:4])
        
        # Add base prompt
        enhanced_parts.append(base_prompt)
        
        # Add learned preferred tags (weighted)
        for tag, weight, _, _ in preferred[:5]:
            if weight > 0.7:
                enhanced_parts.append(f"({tag}:{weight:.1f})")
            elif weight > 0.5:
                enhanced_parts.append(tag)
                
        return ", ".join(enhanced_parts)
        
    def build_prompt_from_selections(self, selections: dict) -> str:
        """Build prompt from UI dropdown selections"""
        parts = []
        
        # Quality base
        parts.extend(["masterpiece", "best quality", "8k resolution", "photorealistic"])
        
        # Add selections with appropriate weights
        if selections.get('body_type'):
            parts.append(f"({selections['body_type']}:1.2)")
        if selections.get('bust_size'):
            parts.append(f"({selections['bust_size']}:1.2)")
        if selections.get('muscle_tone'):
            parts.append(f"({selections['muscle_tone']}:1.3)")
        if selections.get('face_shape'):
            parts.append(f"({selections['face_shape']}:1.1)")
        if selections.get('eye_color'):
            parts.append(f"({selections['eye_color']}:1.2)")
        if selections.get('hair_style'):
            parts.append(selections['hair_style'])
        if selections.get('hair_color'):
            parts.append(selections['hair_color'])
        if selections.get('skin_tone'):
            parts.append(f"({selections['skin_tone']}:1.1)")
        if selections.get('expression'):
            parts.append(f"({selections['expression']}:1.1)")
        if selections.get('pose'):
            parts.append(f"({selections['pose']}:1.1)")
        if selections.get('lighting'):
            parts.append(f"({selections['lighting']}:1.2)")
        if selections.get('background'):
            parts.append(selections['background'])
            
        # Add any custom tags
        if selections.get('custom_tags'):
            parts.extend(selections['custom_tags'])
            
        # Track selection usage
        self._track_selections(selections)
        
        return ", ".join(parts)
        
    def _track_selections(self, selections: dict):
        """Track which selections are used"""
        cursor = self.conn.cursor()
        
        for category, selection in selections.items():
            if selection:
                cursor.execute('''
                    INSERT INTO user_selections (category, selection, use_count, last_used)
                    VALUES (?, ?, 1, ?)
                    ON CONFLICT(category, selection) DO UPDATE SET
                    use_count = use_count + 1, last_used = ?
                ''', (category, str(selection), datetime.now(), datetime.now()))
                
        self.conn.commit()
        
    # ==================== CHAT LEARNING ====================
    
    def learn_from_chat(self, user_message: str) -> dict:
        """Extract preferences from chat message"""
        preferences = {}
        message_lower = user_message.lower()
        
        # Body type detection
        body_keywords = {
            'petite': 'petite', 'small': 'small frame', 'slim': 'slim',
            'athletic': 'athletic', 'toned': 'toned', 'muscular': 'muscular',
            'skinny': 'skinny', 'fit': 'fit'
        }
        for keyword, value in body_keywords.items():
            if keyword in message_lower:
                preferences['body_type'] = value
                
        # Bust size detection
        bust_keywords = {
            'flat': 'flat chest', 'small bust': 'small bust', 'a cup': 'A cup',
            'aa': 'AA cup', 'aaa': 'AAA cup', 'b cup': 'B cup', 'petite bust': 'petite bust'
        }
        for keyword, value in bust_keywords.items():
            if keyword in message_lower:
                preferences['bust_size'] = value
                
        # Muscle tone detection
        muscle_keywords = {
            'abs': 'visible abs', 'six pack': 'six pack', 'ripped': 'ripped',
            'defined': 'defined muscles', 'toned': 'toned'
        }
        for keyword, value in muscle_keywords.items():
            if keyword in message_lower:
                preferences['muscle_tone'] = value
                
        # Eye detection
        if 'heterochromia' in message_lower:
            preferences['eye_type'] = 'heterochromia'
        for color in ['blue', 'green', 'brown', 'amber', 'violet', 'golden']:
            if f'{color} eye' in message_lower:
                preferences['eye_color'] = f'{color} eyes'
                
        # Store learning
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO chat_feedback (user_input, extracted_preferences)
            VALUES (?, ?)
        ''', (user_message, json.dumps(preferences)))
        self.conn.commit()
        
        return preferences
        
    # ==================== STATISTICS ====================
    
    def get_stats(self) -> dict:
        """Get learning statistics"""
        cursor = self.conn.cursor()
        
        # Total images
        cursor.execute('SELECT COUNT(*) FROM images')
        total_images = cursor.fetchone()[0]
        
        # Rated images
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating > 0')
        rated_images = cursor.fetchone()[0]
        
        # Average rating
        cursor.execute('SELECT AVG(rating) FROM images WHERE rating > 0')
        avg_rating = cursor.fetchone()[0] or 0
        
        # Learned tags
        cursor.execute('SELECT COUNT(*) FROM tag_preferences')
        learned_tags = cursor.fetchone()[0]
        
        # Top preferred tags
        top_tags = self.get_preferred_tags(limit=5)
        
        return {
            'total_images': total_images,
            'rated_images': rated_images,
            'average_rating': round(avg_rating, 2),
            'learned_tags': learned_tags,
            'top_preferred_tags': [t[0] for t in top_tags]
        }
        
    def save_image_record(self, filename: str, prompt: str, negative: str, 
                         tags: list, model: str, seed: int):
        """Save generated image record"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO images (filename, prompt, negative_prompt, tags, model, seed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, prompt, negative, json.dumps(tags), model, seed))
        self.conn.commit()
        
    def close(self):
        self.conn.close()


# ==================== API FOR WPF INTEGRATION ====================

def get_dropdown_options():
    """Return all dropdown options for WPF UI"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def rate_image_api(filename: str, rating: int):
    """API endpoint for rating"""
    pref = PreferenceSystem()
    pref.rate_image(filename, rating)
    pref.close()
    return {"status": "success", "filename": filename, "rating": rating}

def enhance_prompt_api(prompt: str, style: str = "general"):
    """API endpoint for prompt enhancement"""
    pref = PreferenceSystem()
    enhanced = pref.enhance_prompt(prompt, style)
    pref.close()
    return {"original": prompt, "enhanced": enhanced}

def build_prompt_api(selections: dict):
    """API endpoint for building prompt from selections"""
    pref = PreferenceSystem()
    prompt = pref.build_prompt_from_selections(selections)
    pref.close()
    return {"prompt": prompt, "selections": selections}

def chat_learn_api(message: str):
    """API endpoint for chat learning"""
    pref = PreferenceSystem()
    preferences = pref.learn_from_chat(message)
    pref.close()
    return {"extracted_preferences": preferences}

def get_stats_api():
    """API endpoint for statistics"""
    pref = PreferenceSystem()
    stats = pref.get_stats()
    pref.close()
    return stats


if __name__ == "__main__":
    print("="*60)
    print("  PREFERENCE SYSTEM TEST")
    print("="*60)
    
    pref = PreferenceSystem()
    
    # Test chat learning
    print("\n📝 Testing chat learning...")
    result = pref.learn_from_chat("I want petite women with small bust and visible abs")
    print(f"   Extracted: {result}")
    
    # Test prompt building
    print("\n🔧 Testing prompt building...")
    selections = {
        'body_type': 'petite',
        'bust_size': 'A cup',
        'muscle_tone': 'visible abs',
        'eye_color': 'heterochromia',
        'face_shape': 'oval face',
        'skin_tone': 'caramel skin'
    }
    prompt = pref.build_prompt_from_selections(selections)
    print(f"   Built prompt: {prompt[:100]}...")
    
    # Test enhancement
    print("\n✨ Testing prompt enhancement...")
    enhanced = pref.enhance_prompt("tribal warrior woman")
    print(f"   Enhanced: {enhanced[:100]}...")
    
    # Get stats
    print("\n📊 System stats:")
    stats = pref.get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    pref.close()
    print("\n✅ Preference system ready!")
