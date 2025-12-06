"""
Excellence Pursuit System
Handles images rated 10+ and pursues Rating 15 (Perfection)
Real-time AI learning from high-rated images
"""
import sqlite3
import json
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

DB_PATH = Path(r"c:\Users\Admin\civitai\data\advanced_learning.db")

class ExcellencePursuitSystem:
    """
    WHAT HAPPENS WHEN IMAGE REACHES 10+ RATING:
    
    1. IMMEDIATE ANALYSIS
       - Extract all tags from the prompt
       - Compare to other 10+ images
       - Find common patterns
       
    2. TAG WEIGHT BOOST
       - All tags get weight increase
       - More increase for higher ratings
       
    3. PATTERN DETECTION
       - Find tag combinations that work
       - Record prompt structure
       
    4. AUTO-GENERATION (50 variations)
       - Use enhanced prompt
       - Apply learned patterns
       - Test new combinations
       
    5. PURSUIT OF 15
       - Track progress toward perfection
       - Continuously refine
    """
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._ensure_tables()
        
    def _ensure_tables(self):
        cursor = self.conn.cursor()
        
        # Excellence tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS excellence_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id TEXT,
            rating REAL,
            prompt TEXT,
            tags TEXT,
            tag_patterns TEXT,
            common_with_others TEXT,
            unique_tags TEXT,
            enhancement_suggestions TEXT,
            variations_generated INTEGER DEFAULT 0,
            best_variation_rating REAL DEFAULT 0,
            analyzed_at TEXT
        )''')
        
        # Tag combinations that work
        cursor.execute('''CREATE TABLE IF NOT EXISTS winning_combinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            combination TEXT,
            avg_rating REAL,
            times_used INTEGER DEFAULT 1,
            created_at TEXT,
            UNIQUE(combination)
        )''')
        
        # Pursuit of 15 tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS perfection_pursuit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            starting_rating REAL,
            current_best REAL,
            iterations INTEGER DEFAULT 0,
            improvements TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT
        )''')
        
        # Real-time learning log
        cursor.execute('''CREATE TABLE IF NOT EXISTS realtime_learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            source_image_id TEXT,
            action_taken TEXT,
            tags_boosted TEXT,
            patterns_found TEXT,
            result TEXT,
            timestamp TEXT
        )''')
        
        self.conn.commit()
        
    # ==================== RATING 10+ HANDLER ====================
    
    def handle_excellent_rating(self, image_id: str, rating: float, 
                                prompt: str, tags: list) -> dict:
        """
        MAIN HANDLER: What happens when image gets 10+ rating
        
        Returns detailed analysis and next steps
        """
        if rating < 10:
            return {'error': 'Rating must be 10+ for excellence handling'}
            
        cursor = self.conn.cursor()
        result = {
            'image_id': image_id,
            'rating': rating,
            'level': self._get_level(rating),
            'actions_taken': [],
            'patterns_found': [],
            'next_steps': []
        }
        
        # STEP 1: Boost all tag weights
        boost_result = self._boost_tag_weights(tags, rating)
        result['actions_taken'].append(f"Boosted {len(tags)} tag weights")
        result['tags_boosted'] = boost_result
        
        # STEP 2: Compare with other 10+ images
        comparison = self._compare_with_excellence(prompt, tags)
        result['comparison'] = comparison
        result['patterns_found'] = comparison.get('common_patterns', [])
        
        # STEP 3: Find winning combinations
        combinations = self._find_winning_combinations(tags, rating)
        result['winning_combinations'] = combinations
        
        # STEP 4: Record for learning
        cursor.execute('''INSERT INTO excellence_analysis 
            (image_id, rating, prompt, tags, tag_patterns, common_with_others,
             unique_tags, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (image_id, rating, prompt, json.dumps(tags),
             json.dumps(result['patterns_found']),
             json.dumps(comparison.get('common_tags', [])),
             json.dumps(comparison.get('unique_tags', [])),
             datetime.now().isoformat()))
             
        # STEP 5: Log real-time learning
        cursor.execute('''INSERT INTO realtime_learning 
            (event_type, source_image_id, action_taken, tags_boosted, 
             patterns_found, result, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (f'excellence_{self._get_level(rating)}', image_id,
             'full_analysis', json.dumps(boost_result[:10]),
             json.dumps(result['patterns_found'][:5]),
             f'Rating {rating} analyzed', datetime.now().isoformat()))
             
        self.conn.commit()
        
        # STEP 6: Determine next steps
        result['next_steps'] = self._get_next_steps(rating, comparison)
        
        # STEP 7: If rating 10+, prepare variation generation
        if rating >= 10:
            result['variation_prompt'] = self._create_enhanced_prompt(prompt, tags, comparison)
            result['variations_to_generate'] = 50 if rating >= 10 else 10
            
        return result
        
    def _get_level(self, rating: float) -> str:
        if rating >= 15: return "PERFECT"
        if rating >= 13: return "NEAR_PERFECT"
        if rating >= 11: return "EXCELLENT"
        if rating >= 10: return "GREAT"
        return "GOOD"
        
    # ==================== TAG WEIGHT BOOSTING ====================
    
    def _boost_tag_weights(self, tags: list, rating: float) -> list:
        """Boost tag weights based on rating"""
        cursor = self.conn.cursor()
        boosted = []
        
        # Higher rating = bigger boost
        boost_factor = 1 + (rating - 9) * 0.1  # 10=1.1x, 15=1.6x
        
        for tag in tags:
            cursor.execute('SELECT weight, high_rating_count FROM tag_analysis WHERE tag = ?', (tag,))
            result = cursor.fetchone()
            
            if result:
                old_weight = result[0]
                high_count = result[1] + 1
                # Boost weight toward 1.0
                new_weight = min(0.99, old_weight + (1 - old_weight) * 0.1 * boost_factor)
            else:
                old_weight = 0.5
                high_count = 1
                new_weight = 0.5 + 0.1 * boost_factor
                
            cursor.execute('''INSERT OR REPLACE INTO tag_analysis 
                (tag, avg_rating, high_rating_count, weight, last_high_rating)
                VALUES (?, ?, ?, ?, ?)''',
                (tag, rating, high_count, new_weight, datetime.now().isoformat()))
                
            boosted.append({
                'tag': tag,
                'old_weight': round(old_weight, 3),
                'new_weight': round(new_weight, 3),
                'boost': round(new_weight - old_weight, 3)
            })
            
        self.conn.commit()
        return boosted
        
    # ==================== PROMPT COMPARISON ====================
    
    def _compare_with_excellence(self, prompt: str, tags: list) -> dict:
        """Compare this image with ALL other 10+ rated images"""
        cursor = self.conn.cursor()
        
        # Get all 10+ rated images
        cursor.execute('SELECT tags, rating FROM images WHERE rating >= 10')
        excellent_images = cursor.fetchall()
        
        if len(excellent_images) < 2:
            return {
                'total_excellent': len(excellent_images),
                'common_tags': [],
                'unique_tags': tags,
                'common_patterns': []
            }
            
        # Count tag frequency across excellent images
        all_tags = Counter()
        for tags_json, rating in excellent_images:
            img_tags = json.loads(tags_json) if tags_json else []
            for tag in img_tags:
                all_tags[tag] += 1
                
        total = len(excellent_images)
        
        # Find common tags (appear in 50%+ of excellent images)
        common_tags = [tag for tag, count in all_tags.items() 
                      if count >= total * 0.5]
        
        # Find unique tags (only in this image)
        unique_tags = [tag for tag in tags if all_tags[tag] == 1]
        
        # Find tag pairs that appear together often
        common_patterns = []
        for t1 in common_tags[:10]:
            for t2 in common_tags[10:20]:
                if t1 != t2:
                    common_patterns.append(f"{t1} + {t2}")
                    
        return {
            'total_excellent': total,
            'common_tags': common_tags[:20],
            'unique_tags': unique_tags[:10],
            'common_patterns': common_patterns[:10],
            'tag_frequency': dict(all_tags.most_common(20))
        }
        
    # ==================== WINNING COMBINATIONS ====================
    
    def _find_winning_combinations(self, tags: list, rating: float) -> list:
        """Find and record winning tag combinations"""
        cursor = self.conn.cursor()
        combinations = []
        
        # Generate 2-tag and 3-tag combinations
        for i, t1 in enumerate(tags[:10]):
            for t2 in tags[i+1:10]:
                combo = f"{t1}|{t2}"
                
                cursor.execute('SELECT avg_rating, times_used FROM winning_combinations WHERE combination = ?',
                              (combo,))
                result = cursor.fetchone()
                
                if result:
                    new_avg = (result[0] * result[1] + rating) / (result[1] + 1)
                    cursor.execute('UPDATE winning_combinations SET avg_rating = ?, times_used = ? WHERE combination = ?',
                                  (new_avg, result[1] + 1, combo))
                else:
                    cursor.execute('INSERT INTO winning_combinations (combination, avg_rating, times_used, created_at) VALUES (?, ?, 1, ?)',
                                  (combo, rating, datetime.now().isoformat()))
                    new_avg = rating
                    
                combinations.append({'combo': combo, 'avg_rating': round(new_avg, 1)})
                
        self.conn.commit()
        
        # Get top combinations
        cursor.execute('SELECT combination, avg_rating, times_used FROM winning_combinations ORDER BY avg_rating DESC LIMIT 20')
        top_combos = [{'combo': r[0], 'avg_rating': r[1], 'times': r[2]} for r in cursor.fetchall()]
        
        return top_combos
        
    # ==================== NEXT STEPS ====================
    
    def _get_next_steps(self, rating: float, comparison: dict) -> list:
        """Determine next steps based on rating"""
        steps = []
        
        if rating >= 15:
            steps.append("🏆 PERFECT! Save as Gold Standard")
            steps.append("📊 Analyze what made this perfect")
            steps.append("🎯 Use this prompt as template for future")
            
        elif rating >= 13:
            steps.append("🌟 NEAR PERFECT! Very close to goal")
            steps.append("🔬 Generate 50 variations with minor tweaks")
            steps.append("📈 Focus on: " + ", ".join(comparison.get('common_tags', [])[:5]))
            
        elif rating >= 11:
            steps.append("⭐ EXCELLENT! Making great progress")
            steps.append("🚀 Auto-generating 50 variations")
            steps.append("🧪 Try adding: " + ", ".join(comparison.get('unique_tags', [])[:3]))
            
        elif rating >= 10:
            steps.append("✅ GREAT! Above threshold")
            steps.append("🎨 Generate 50 variations to find better")
            steps.append("🔍 Compare patterns with other 10+ images")
            
        return steps
        
    # ==================== ENHANCED PROMPT ====================
    
    def _create_enhanced_prompt(self, original: str, tags: list, 
                                comparison: dict) -> str:
        """Create enhanced prompt using learned patterns"""
        cursor = self.conn.cursor()
        
        # Get top performing tags
        cursor.execute('SELECT tag, weight FROM tag_analysis WHERE weight > 0.7 ORDER BY weight DESC LIMIT 15')
        top_tags = cursor.fetchall()
        
        # Start with original
        enhanced_parts = original.split(", ")
        
        # Add high-performing tags not already present
        for tag, weight in top_tags:
            if tag not in original:
                enhanced_parts.append(f"({tag}:{weight:.1f})")
                
        # Add common tags from comparison
        for tag in comparison.get('common_tags', [])[:5]:
            if tag not in original:
                enhanced_parts.append(f"({tag}:1.2)")
                
        return ", ".join(enhanced_parts)
        
    # ==================== REAL-TIME LEARNING STATUS ====================
    
    def get_learning_status(self) -> dict:
        """Get current AI learning status"""
        cursor = self.conn.cursor()
        
        # Count excellent images
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating >= 10')
        excellent = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating >= 13')
        near_perfect = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating >= 15')
        perfect = cursor.fetchone()[0]
        
        # Get recent learning events
        cursor.execute('SELECT event_type, action_taken, timestamp FROM realtime_learning ORDER BY id DESC LIMIT 10')
        recent = [{'type': r[0], 'action': r[1], 'time': r[2]} for r in cursor.fetchall()]
        
        # Get top patterns
        cursor.execute('SELECT combination, avg_rating FROM winning_combinations ORDER BY avg_rating DESC LIMIT 10')
        top_patterns = [{'pattern': r[0], 'rating': r[1]} for r in cursor.fetchall()]
        
        # Get best tags
        cursor.execute('SELECT tag, weight, high_rating_count FROM tag_analysis ORDER BY weight DESC LIMIT 15')
        best_tags = [{'tag': r[0], 'weight': round(r[1], 3), 'high_uses': r[2]} for r in cursor.fetchall()]
        
        return {
            'status': 'LEARNING_ACTIVE',
            'excellent_images': excellent,
            'near_perfect_images': near_perfect,
            'perfect_images': perfect,
            'goal': 'Reach Rating 15',
            'progress': f'{perfect} perfect, {near_perfect} near-perfect, {excellent} excellent',
            'recent_learning': recent[:5],
            'top_patterns': top_patterns[:5],
            'best_tags': best_tags[:10],
            'auto_improvement': 'ENABLED',
            'variations_on_10plus': 50
        }
        
    def close(self):
        self.conn.close()


# ==================== DEMONSTRATION ====================
def demonstrate_system():
    print("="*70)
    print("  EXCELLENCE PURSUIT SYSTEM")
    print("  What happens when images reach 10+ rating")
    print("="*70)
    
    eps = ExcellencePursuitSystem()
    
    # Simulate a rating 12 image
    print("\n" + "="*70)
    print("  SCENARIO: User rates image 12/15 stars")
    print("="*70)
    
    test_prompt = "masterpiece, best quality, petite, A cup, perky, tribal warrior, war paint, heterochromia"
    test_tags = ['petite', 'A cup', 'perky', 'tribal warrior', 'war paint', 'heterochromia', 'tribal', 'exotic']
    
    result = eps.handle_excellent_rating('test_001', 12, test_prompt, test_tags)
    
    print(f"\n📊 ANALYSIS RESULT:")
    print(f"   Rating Level: {result['level']}")
    print(f"   Actions Taken: {len(result['actions_taken'])}")
    
    print(f"\n📈 TAGS BOOSTED:")
    for tag in result['tags_boosted'][:5]:
        print(f"   • {tag['tag']}: {tag['old_weight']} → {tag['new_weight']} (+{tag['boost']})")
        
    print(f"\n🔗 WINNING COMBINATIONS FOUND:")
    for combo in result['winning_combinations'][:5]:
        print(f"   • {combo['combo']} (avg rating: {combo['avg_rating']})")
        
    print(f"\n👣 NEXT STEPS:")
    for step in result['next_steps']:
        print(f"   {step}")
        
    print(f"\n🎨 ENHANCED PROMPT FOR VARIATIONS:")
    print(f"   {result.get('variation_prompt', 'N/A')[:150]}...")
    print(f"   Variations to generate: {result.get('variations_to_generate', 0)}")
    
    # Show learning status
    print("\n" + "="*70)
    print("  REAL-TIME LEARNING STATUS")
    print("="*70)
    
    status = eps.get_learning_status()
    print(f"\n   Status: {status['status']}")
    print(f"   Goal: {status['goal']}")
    print(f"   Progress: {status['progress']}")
    print(f"   Auto-improvement: {status['auto_improvement']}")
    print(f"   Variations on 10+: {status['variations_on_10plus']}")
    
    if status['best_tags']:
        print(f"\n   🏆 TOP PERFORMING TAGS:")
        for tag in status['best_tags'][:5]:
            print(f"      • {tag['tag']}: weight {tag['weight']}, used {tag['high_uses']}x in high ratings")
            
    if status['top_patterns']:
        print(f"\n   🔗 TOP WINNING PATTERNS:")
        for pattern in status['top_patterns'][:5]:
            print(f"      • {pattern['pattern']} → avg rating {pattern['rating']}")
    
    print("\n" + "="*70)
    print("  DATABASE RECORDING")
    print("="*70)
    print("""
   TABLES USED FOR REAL-TIME LEARNING:
   
   📊 excellence_analysis
      - Every 10+ image analyzed
      - Tags, patterns, comparisons stored
      - Enhancement suggestions saved
      
   🔗 winning_combinations  
      - Tag pairs that work together
      - Updated every time 10+ rating received
      - Avg rating tracked per combination
      
   🎯 perfection_pursuit
      - Sessions tracking progress to 15
      - Iterations counted
      - Improvements recorded
      
   ⚡ realtime_learning
      - Every learning event logged
      - Tags boosted
      - Patterns found
      - Actions taken
      
   📈 tag_analysis
      - Weight per tag (0-1)
      - High rating count
      - Last high rating timestamp
      - Auto-updates on every rating
""")
    
    eps.close()
    print("\n✅ Excellence Pursuit System ready for real-time learning!")


if __name__ == "__main__":
    demonstrate_system()
