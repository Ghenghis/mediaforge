"""
Chat Memory Learning System
AI learns from chat interactions and saves user preferences
"""
import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path(r"c:\Users\Admin\civitai\data\preferences.db")

class ChatMemorySystem:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._setup_tables()
        
    def _setup_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_type TEXT,
            content TEXT,
            is_like INTEGER DEFAULT 1,
            weight REAL DEFAULT 1.0,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(memory_type, content)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            extracted_prefs TEXT,
            action_taken TEXT,
            created_at TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS tag_weights (
            tag TEXT PRIMARY KEY,
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0,
            weight REAL DEFAULT 0.5
        )''')
        
        self.conn.commit()
        
    # ==================== MEMORY OPERATIONS ====================
    
    def add_like(self, category: str, item: str, weight: float = 1.0) -> dict:
        """Add a preference the user likes"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_memory (memory_type, content, is_like, weight, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?, ?)
        ''', (category, item, weight, datetime.now().isoformat(), datetime.now().isoformat()))
        self.conn.commit()
        return {'action': 'added_like', 'category': category, 'item': item}
        
    def add_dislike(self, category: str, item: str, weight: float = 1.0) -> dict:
        """Add something the user dislikes"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_memory (memory_type, content, is_like, weight, created_at, updated_at)
            VALUES (?, ?, 0, ?, ?, ?)
        ''', (category, item, weight, datetime.now().isoformat(), datetime.now().isoformat()))
        self.conn.commit()
        return {'action': 'added_dislike', 'category': category, 'item': item}
        
    def remove_memory(self, category: str, item: str) -> dict:
        """Remove a preference from memory"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM user_memory WHERE memory_type = ? AND content = ?', (category, item))
        self.conn.commit()
        return {'action': 'removed', 'category': category, 'item': item}
        
    def get_all_likes(self) -> list:
        """Get all things user likes"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT memory_type, content, weight FROM user_memory WHERE is_like = 1 ORDER BY weight DESC')
        return [{'category': r[0], 'item': r[1], 'weight': r[2]} for r in cursor.fetchall()]
        
    def get_all_dislikes(self) -> list:
        """Get all things user dislikes"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT memory_type, content, weight FROM user_memory WHERE is_like = 0 ORDER BY weight DESC')
        return [{'category': r[0], 'item': r[1], 'weight': r[2]} for r in cursor.fetchall()]
        
    def get_memories_by_category(self, category: str) -> dict:
        """Get likes and dislikes for a category"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT content, is_like, weight FROM user_memory WHERE memory_type = ?', (category,))
        results = cursor.fetchall()
        return {
            'likes': [{'item': r[0], 'weight': r[2]} for r in results if r[1] == 1],
            'dislikes': [{'item': r[0], 'weight': r[2]} for r in results if r[1] == 0]
        }
        
    # ==================== CHAT LEARNING ====================
    
    def process_chat(self, user_message: str) -> dict:
        """Process chat message and extract preferences"""
        message_lower = user_message.lower()
        extracted = {'likes': [], 'dislikes': [], 'removes': []}
        actions = []
        
        # Detect likes
        like_patterns = [
            r"i (?:like|love|prefer|want) (.+?)(?:\.|,|$)",
            r"(?:more|add) (.+?)(?:\.|,|$)",
            r"(.+?) (?:is good|looks good|is great)",
        ]
        
        for pattern in like_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                item = match.strip()
                if len(item) > 2 and len(item) < 50:
                    extracted['likes'].append(item)
                    self.add_like('chat_preference', item)
                    actions.append(f"Added like: {item}")
                    
        # Detect dislikes
        dislike_patterns = [
            r"i (?:don't like|hate|dislike) (.+?)(?:\.|,|$)",
            r"(?:no|remove|less) (.+?)(?:\.|,|$)",
            r"(.+?) (?:is bad|looks bad|is ugly)",
        ]
        
        for pattern in dislike_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                item = match.strip()
                if len(item) > 2 and len(item) < 50:
                    extracted['dislikes'].append(item)
                    self.add_dislike('chat_preference', item)
                    actions.append(f"Added dislike: {item}")
                    
        # Detect removals
        remove_patterns = [
            r"(?:forget|remove|delete) (?:that i (?:like|dislike) )?(.+?)(?:\.|,|$)",
            r"(?:actually|nevermind),? (?:i (?:don't|do) )?(.+?)(?:\.|,|$)",
        ]
        
        for pattern in remove_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                item = match.strip()
                if len(item) > 2 and len(item) < 50:
                    extracted['removes'].append(item)
                    self.remove_memory('chat_preference', item)
                    actions.append(f"Removed: {item}")
                    
        # Detect specific preferences
        specific_prefs = {
            'bust_size': ['flat', 'aaa', 'aa cup', 'a cup', 'b cup', 'c cup', 'small bust', 'petite bust'],
            'breast_shape': ['perky', 'pointy', 'puffy', 'round', 'teardrop', 'firm'],
            'body_type': ['petite', 'slim', 'athletic', 'toned', 'muscular', 'fit'],
            'muscle': ['abs', 'toned', 'defined', 'six pack', 'athletic'],
        }
        
        for category, keywords in specific_prefs.items():
            for keyword in keywords:
                if keyword in message_lower:
                    if any(neg in message_lower for neg in ['no ', 'not ', "don't", 'hate', 'dislike']):
                        self.add_dislike(category, keyword)
                        extracted['dislikes'].append(keyword)
                        actions.append(f"Added {category} dislike: {keyword}")
                    else:
                        self.add_like(category, keyword)
                        extracted['likes'].append(keyword)
                        actions.append(f"Added {category} like: {keyword}")
                        
        # Save chat history
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO chat_history (user_input, extracted_prefs, action_taken, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_message, json.dumps(extracted), json.dumps(actions), datetime.now().isoformat()))
        self.conn.commit()
        
        return {
            'extracted': extracted,
            'actions': actions,
            'total_likes': len(self.get_all_likes()),
            'total_dislikes': len(self.get_all_dislikes())
        }
        
    # ==================== APPLY TO PROMPTS ====================
    
    def get_prompt_modifiers(self) -> dict:
        """Get modifiers to apply to prompts based on memories"""
        likes = self.get_all_likes()
        dislikes = self.get_all_dislikes()
        
        positive_additions = []
        negative_additions = []
        
        for like in likes:
            weight = like.get('weight', 1.0)
            if weight > 0.8:
                positive_additions.append(f"({like['item']}:1.3)")
            elif weight > 0.5:
                positive_additions.append(f"({like['item']}:1.1)")
            else:
                positive_additions.append(like['item'])
                
        for dislike in dislikes:
            weight = dislike.get('weight', 1.0)
            if weight > 0.8:
                negative_additions.append(f"({dislike['item']}:1.5)")
            else:
                negative_additions.append(f"({dislike['item']}:1.3)")
                
        return {
            'positive_additions': positive_additions,
            'negative_additions': negative_additions
        }
        
    # ==================== STATS ====================
    
    def get_stats(self) -> dict:
        """Get memory statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM user_memory WHERE is_like = 1')
        total_likes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM user_memory WHERE is_like = 0')
        total_dislikes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM chat_history')
        total_chats = cursor.fetchone()[0]
        
        cursor.execute('SELECT memory_type, COUNT(*) FROM user_memory GROUP BY memory_type')
        by_category = dict(cursor.fetchall())
        
        return {
            'total_likes': total_likes,
            'total_dislikes': total_dislikes,
            'total_chat_interactions': total_chats,
            'by_category': by_category
        }
        
    def close(self):
        self.conn.close()


# ==================== TEST FUNCTION ====================
def test_chat_memory():
    """Test the chat memory system"""
    print("="*60)
    print("  CHAT MEMORY SYSTEM TEST")
    print("="*60)
    
    cms = ChatMemorySystem()
    
    # Test 1: Direct likes/dislikes
    print("\n📝 TEST 1: Direct Memory Operations")
    print("-"*40)
    
    cms.add_like('bust_size', 'A cup', 1.0)
    cms.add_like('bust_size', 'AA cup', 0.9)
    cms.add_like('breast_shape', 'perky', 1.0)
    cms.add_like('breast_shape', 'pointy', 0.8)
    cms.add_dislike('breast_shape', 'saggy', 1.0)
    cms.add_dislike('body_type', 'chubby', 1.0)
    
    likes = cms.get_all_likes()
    dislikes = cms.get_all_dislikes()
    
    print(f"   Added {len(likes)} likes, {len(dislikes)} dislikes")
    print(f"   Likes: {[l['item'] for l in likes]}")
    print(f"   Dislikes: {[d['item'] for d in dislikes]}")
    
    test1_pass = len(likes) >= 4 and len(dislikes) >= 2
    print(f"\n   Result: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    
    # Test 2: Chat processing
    print("\n📝 TEST 2: Chat Learning")
    print("-"*40)
    
    chat_tests = [
        "I like petite women with small bust",
        "I prefer perky breasts, not saggy",
        "I want toned abs and athletic body",
        "I don't like large breasts or chubby",
    ]
    
    for chat in chat_tests:
        result = cms.process_chat(chat)
        print(f"   '{chat[:40]}...'")
        print(f"      Actions: {result['actions'][:2]}")
    
    stats = cms.get_stats()
    print(f"\n   Total likes: {stats['total_likes']}")
    print(f"   Total dislikes: {stats['total_dislikes']}")
    print(f"   Chat interactions: {stats['total_chat_interactions']}")
    
    test2_pass = stats['total_likes'] > 4 and stats['total_chat_interactions'] >= 4
    print(f"\n   Result: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    # Test 3: Memory removal
    print("\n📝 TEST 3: Memory Removal")
    print("-"*40)
    
    before = len(cms.get_all_likes())
    cms.remove_memory('bust_size', 'A cup')
    after = len(cms.get_all_likes())
    
    print(f"   Before removal: {before} likes")
    print(f"   After removal: {after} likes")
    
    test3_pass = after == before - 1
    print(f"\n   Result: {'✅ PASS' if test3_pass else '❌ FAIL'}")
    
    # Test 4: Prompt modifiers
    print("\n📝 TEST 4: Prompt Modifiers")
    print("-"*40)
    
    modifiers = cms.get_prompt_modifiers()
    print(f"   Positive additions: {len(modifiers['positive_additions'])}")
    print(f"   Negative additions: {len(modifiers['negative_additions'])}")
    print(f"   Sample positive: {modifiers['positive_additions'][:3]}")
    print(f"   Sample negative: {modifiers['negative_additions'][:3]}")
    
    test4_pass = len(modifiers['positive_additions']) > 0 and len(modifiers['negative_additions']) > 0
    print(f"\n   Result: {'✅ PASS' if test4_pass else '❌ FAIL'}")
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    all_pass = test1_pass and test2_pass and test3_pass and test4_pass
    
    print(f"\n   Test 1 (Direct Operations): {'✅' if test1_pass else '❌'}")
    print(f"   Test 2 (Chat Learning): {'✅' if test2_pass else '❌'}")
    print(f"   Test 3 (Memory Removal): {'✅' if test3_pass else '❌'}")
    print(f"   Test 4 (Prompt Modifiers): {'✅' if test4_pass else '❌'}")
    
    print(f"\n   Overall: {'✅ ALL TESTS PASSED' if all_pass else '❌ SOME TESTS FAILED'}")
    
    if all_pass:
        print("\n🧠 Chat Memory System working correctly!")
        print("   - Learns from chat interactions")
        print("   - Saves likes and dislikes")
        print("   - Can remove memories on request")
        print("   - Generates prompt modifiers")
    
    cms.close()
    return all_pass


if __name__ == "__main__":
    test_chat_memory()
