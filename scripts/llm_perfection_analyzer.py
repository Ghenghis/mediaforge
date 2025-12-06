"""
LLM Perfection Analyzer
Uses local LLM to analyze prompts/tags/ratings to find Image Perfection
Connects to Ollama or LM Studio
"""
import sqlite3
import json
import urllib.request
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = Path(r"c:\Users\Admin\civitai\data\advanced_learning.db")
OLLAMA_URL = "http://localhost:11434"
LMSTUDIO_URL = "http://localhost:1234"

class LLMPerfectionAnalyzer:
    def __init__(self, llm_provider: str = "ollama", model: str = "llama3.2"):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.llm_provider = llm_provider
        self.model = model
        self.llm_url = OLLAMA_URL if llm_provider == "ollama" else LMSTUDIO_URL
        
    def check_llm_connection(self) -> dict:
        """Check if LLM is available"""
        try:
            if self.llm_provider == "ollama":
                resp = urllib.request.urlopen(f"{self.llm_url}/api/tags", timeout=5)
                models = json.loads(resp.read())
                return {'connected': True, 'models': [m['name'] for m in models.get('models', [])]}
            else:
                resp = urllib.request.urlopen(f"{self.llm_url}/v1/models", timeout=5)
                return {'connected': True, 'provider': 'lmstudio'}
        except:
            return {'connected': False}
            
    def _query_llm(self, prompt: str) -> str:
        """Query the LLM"""
        try:
            if self.llm_provider == "ollama":
                data = json.dumps({
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }).encode()
                req = urllib.request.Request(f"{self.llm_url}/api/generate", 
                    data=data, headers={'Content-Type': 'application/json'})
                resp = urllib.request.urlopen(req, timeout=120)
                return json.loads(resp.read()).get('response', '')
            else:
                data = json.dumps({
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }).encode()
                req = urllib.request.Request(f"{self.llm_url}/v1/chat/completions",
                    data=data, headers={'Content-Type': 'application/json'})
                resp = urllib.request.urlopen(req, timeout=120)
                result = json.loads(resp.read())
                return result['choices'][0]['message']['content']
        except Exception as e:
            return f"LLM Error: {e}"
            
    # ==================== ANALYSIS METHODS ====================
    
    def analyze_high_rated_patterns(self) -> dict:
        """Analyze patterns in high-rated images (10+)"""
        cursor = self.conn.cursor()
        
        # Get high-rated images
        cursor.execute('''SELECT prompt, tags, rating FROM images 
            WHERE rating >= 10 ORDER BY rating DESC LIMIT 50''')
        high_rated = cursor.fetchall()
        
        if not high_rated:
            return {'error': 'No high-rated images yet. Rate some images 10+ first.'}
            
        # Build analysis prompt
        analysis_prompt = f"""You are an AI analyzing image generation prompts to find what makes PERFECT images.

I have {len(high_rated)} images rated 10-15 out of 15 (excellent to perfect).

Here are the TOP rated image prompts and their ratings:

"""
        for prompt, tags, rating in high_rated[:10]:
            tags_list = json.loads(tags) if tags else []
            analysis_prompt += f"RATING {rating}/15:\nPrompt: {prompt[:300]}...\nTags: {tags_list[:15]}\n\n"
            
        analysis_prompt += """
Based on these high-rated prompts, analyze:

1. COMMON PATTERNS: What tags/phrases appear most in high ratings?
2. TAG COMBINATIONS: Which tag combinations seem to work best?
3. PROMPT STRUCTURE: What prompt structure gets highest ratings?
4. ENHANCEMENT SUGGESTIONS: How can we get even higher ratings?
5. PERFECTION FORMULA: What's the formula for a 15/15 perfect image?

Be specific and actionable. Focus on what WORKS.
"""
        
        # Query LLM
        response = self._query_llm(analysis_prompt)
        
        return {
            'images_analyzed': len(high_rated),
            'analysis': response,
            'timestamp': datetime.now().isoformat()
        }
        
    def analyze_rating_changes(self) -> dict:
        """Analyze what causes rating improvements"""
        cursor = self.conn.cursor()
        
        # Get rating events where rating improved
        cursor.execute('''SELECT re.old_rating, re.new_rating, re.tags_analyzed, i.prompt
            FROM rating_events re
            JOIN images i ON re.image_id = i.image_id
            WHERE re.rating_change > 0
            ORDER BY re.rating_change DESC LIMIT 20''')
        improvements = cursor.fetchall()
        
        if not improvements:
            return {'error': 'No rating improvements yet. Rate more images.'}
            
        analysis_prompt = f"""Analyze these rating IMPROVEMENTS to understand what users like:

"""
        for old_r, new_r, tags_json, prompt in improvements[:10]:
            tags = json.loads(tags_json) if tags_json else []
            analysis_prompt += f"Rating went from {old_r} → {new_r} (improved by {new_r-old_r})\n"
            analysis_prompt += f"Tags: {tags[:10]}\n"
            analysis_prompt += f"Prompt excerpt: {prompt[:150]}...\n\n"
            
        analysis_prompt += """
What patterns cause ratings to IMPROVE? What should we do MORE of?
What specific tags or combinations lead to higher user ratings?
"""
        
        response = self._query_llm(analysis_prompt)
        
        return {
            'improvements_analyzed': len(improvements),
            'analysis': response
        }
        
    def find_perfection_formula(self) -> dict:
        """Use all data to find the formula for Rating 15"""
        cursor = self.conn.cursor()
        
        # Get tag statistics
        cursor.execute('''SELECT tag, avg_rating, high_rating_count, weight 
            FROM tag_analysis WHERE high_rating_count > 0
            ORDER BY avg_rating DESC LIMIT 30''')
        top_tags = cursor.fetchall()
        
        # Get gold standards
        cursor.execute('SELECT prompt, tags FROM gold_standards LIMIT 5')
        gold = cursor.fetchall()
        
        # Get highest rated non-gold
        cursor.execute('''SELECT prompt, tags, rating FROM images 
            WHERE rating >= 12 AND rating < 15 ORDER BY rating DESC LIMIT 10''')
        near_perfect = cursor.fetchall()
        
        analysis_prompt = """You are finding the FORMULA for creating PERFECT images (Rating 15/15).

TOP PERFORMING TAGS (ordered by average rating):
"""
        for tag, avg, high_count, weight in top_tags[:20]:
            analysis_prompt += f"- {tag}: avg rating {avg:.1f}, used in {high_count} high-rated images\n"
            
        if gold:
            analysis_prompt += "\n\nGOLD STANDARD PROMPTS (already rated 15/15):\n"
            for prompt, tags in gold:
                analysis_prompt += f"Prompt: {prompt[:200]}...\n"
                
        if near_perfect:
            analysis_prompt += "\n\nNEAR PERFECT (12-14) - What's missing to reach 15?\n"
            for prompt, tags, rating in near_perfect[:5]:
                analysis_prompt += f"Rating {rating}: {prompt[:150]}...\n"
                
        analysis_prompt += """

Based on all this data, create:

1. THE PERFECT PROMPT TEMPLATE - A fill-in template that maximizes rating
2. MUST-HAVE TAGS - Tags that should ALWAYS be included
3. AVOID TAGS - Tags that hurt ratings
4. WEIGHT RECOMMENDATIONS - What weights work best (e.g., :1.3)
5. ENHANCEMENT TIPS - Specific ways to push from 12-14 to 15

Be very specific. Give actual tag names and weights.
"""
        
        response = self._query_llm(analysis_prompt)
        
        # Store the formula
        cursor.execute('''INSERT INTO prompt_patterns (pattern, category, avg_rating, usage_count, created_at)
            VALUES (?, 'llm_formula', 0, 0, ?)''',
            (response[:2000], datetime.now().isoformat()))
        self.conn.commit()
        
        return {
            'top_tags_count': len(top_tags),
            'gold_standards': len(gold),
            'near_perfect': len(near_perfect),
            'formula': response
        }
        
    def enhance_prompt(self, prompt: str, current_rating: float = 0) -> dict:
        """Use LLM to enhance a prompt for higher rating"""
        
        # Get learned preferences
        cursor = self.conn.cursor()
        cursor.execute('SELECT tag, weight FROM tag_analysis WHERE weight > 0.6 ORDER BY weight DESC LIMIT 20')
        good_tags = cursor.fetchall()
        
        cursor.execute('SELECT tag, weight FROM tag_analysis WHERE weight < 0.4 ORDER BY weight ASC LIMIT 10')
        bad_tags = cursor.fetchall()
        
        enhance_prompt = f"""Enhance this image generation prompt to achieve a HIGHER rating.

CURRENT PROMPT:
{prompt}

CURRENT RATING: {current_rating}/15

TAGS THAT WORK WELL (learned from user):
{[t[0] for t in good_tags]}

TAGS TO AVOID:
{[t[0] for t in bad_tags]}

Provide an ENHANCED version of the prompt that:
1. Keeps the core concept
2. Adds high-performing tags with appropriate weights
3. Removes or replaces low-performing elements
4. Uses proper weighting syntax like (tag:1.3)
5. Aims for Rating 15/15

Return ONLY the enhanced prompt, nothing else.
"""
        
        response = self._query_llm(enhance_prompt)
        
        return {
            'original': prompt,
            'enhanced': response,
            'good_tags_used': len(good_tags),
            'bad_tags_avoided': len(bad_tags)
        }
        
    def generate_perfect_prompt(self, theme: str = "tribal") -> dict:
        """Generate a new prompt optimized for Rating 15"""
        cursor = self.conn.cursor()
        
        # Get best performing tags per category
        cursor.execute('''SELECT category, tag, weight FROM tag_analysis 
            WHERE weight > 0.6 ORDER BY category, weight DESC''')
        tags_by_cat = defaultdict(list)
        for cat, tag, weight in cursor.fetchall():
            tags_by_cat[cat].append((tag, weight))
            
        generate_prompt = f"""Create the PERFECT image generation prompt for a {theme} themed image.

Use these HIGH-PERFORMING tags (learned from user ratings):
"""
        for cat, tags in tags_by_cat.items():
            generate_prompt += f"\n{cat.upper()}: {[t[0] for t in tags[:5]]}"
            
        generate_prompt += """

Create a complete prompt that:
1. Starts with quality tags (masterpiece, best quality, etc.)
2. Uses proper weighting for important tags (tag:1.3)
3. Includes body type, face, eyes, hair, skin details
4. Has appropriate lighting and setting
5. Is optimized for Rating 15/15

Return ONLY the prompt, nothing else.
"""
        
        response = self._query_llm(generate_prompt)
        
        return {
            'theme': theme,
            'prompt': response,
            'tags_used': sum(len(v) for v in tags_by_cat.values())
        }
        
    def get_stats(self) -> dict:
        """Get analyzer statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM images WHERE rating >= 10')
        high_rated = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM gold_standards')
        gold = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tag_analysis WHERE weight > 0.6')
        good_tags = cursor.fetchone()[0]
        
        return {
            'high_rated_images': high_rated,
            'gold_standards': gold,
            'high_performing_tags': good_tags,
            'llm_connected': self.check_llm_connection()['connected']
        }
        
    def close(self):
        self.conn.close()


# ==================== TEST ====================
def test_analyzer():
    print("="*60)
    print("  LLM PERFECTION ANALYZER TEST")
    print("="*60)
    
    analyzer = LLMPerfectionAnalyzer()
    
    # Check connection
    print("\n📡 Checking LLM connection...")
    conn = analyzer.check_llm_connection()
    
    if not conn['connected']:
        print("❌ LLM not connected!")
        print("\n👤 USER ACTION NEEDED:")
        print("   Start Ollama: ollama run llama3.2")
        print("   Or start LM Studio with a model")
        print("\n   Then run this test again.")
        return
        
    print(f"✅ Connected to {analyzer.llm_provider}")
    if 'models' in conn:
        print(f"   Available models: {conn['models'][:5]}")
        
    # Get stats
    print("\n📊 Current Data:")
    stats = analyzer.get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
        
    if stats['high_rated_images'] < 5:
        print("\n⚠️ Need more high-rated images for full analysis")
        print("   Rate some images 10+ first")
        
    # Test prompt enhancement
    print("\n🔧 Testing Prompt Enhancement...")
    result = analyzer.enhance_prompt(
        "masterpiece, petite, A cup, tribal woman, war paint",
        current_rating=8
    )
    print(f"   Original: {result['original'][:50]}...")
    print(f"   Enhanced: {result['enhanced'][:100]}...")
    
    # Generate perfect prompt
    print("\n✨ Generating Perfect Prompt...")
    result = analyzer.generate_perfect_prompt("tribal")
    print(f"   Theme: {result['theme']}")
    print(f"   Prompt: {result['prompt'][:150]}...")
    
    print("\n✅ LLM Perfection Analyzer operational!")
    
    analyzer.close()


if __name__ == "__main__":
    test_analyzer()
