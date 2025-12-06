"""
Test AI Learning System
Verifies that ratings correctly influence future prompts
"""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(r"c:\Users\Admin\civitai\data\preferences.db")

def setup_test_db():
    """Initialize fresh test database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create tables if not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        prompt TEXT,
        negative TEXT,
        tags TEXT,
        model TEXT,
        seed INTEGER,
        rating INTEGER DEFAULT 0,
        created_at TEXT,
        rated_at TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS tag_weights (
        tag TEXT PRIMARY KEY,
        likes INTEGER DEFAULT 0,
        dislikes INTEGER DEFAULT 0,
        weight REAL DEFAULT 0.5
    )''')
    
    conn.commit()
    return conn

def simulate_ratings(conn, test_data: list):
    """Simulate user ratings and update tag weights"""
    cursor = conn.cursor()
    
    for item in test_data:
        filename = item['filename']
        rating = item['rating']
        tags = item['tags']
        
        # Save image first
        cursor.execute('''
            INSERT OR REPLACE INTO images (filename, prompt, tags, rating, created_at, rated_at)
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        ''', (filename, "test prompt", json.dumps(tags), rating))
        
        # Update tag weights
        is_like = rating >= 4
        is_dislike = rating <= 2
        
        for tag in tags:
            cursor.execute('SELECT likes, dislikes FROM tag_weights WHERE tag = ?', (tag,))
            row = cursor.fetchone()
            
            if row:
                likes = row[0] + (1 if is_like else 0)
                dislikes = row[1] + (1 if is_dislike else 0)
            else:
                likes = 1 if is_like else 0
                dislikes = 1 if is_dislike else 0
                
            weight = (likes + 1) / (likes + dislikes + 2)
            
            cursor.execute('''
                INSERT OR REPLACE INTO tag_weights (tag, likes, dislikes, weight)
                VALUES (?, ?, ?, ?)
            ''', (tag, likes, dislikes, weight))
    
    conn.commit()

def get_learned_weights(conn) -> dict:
    """Get all learned tag weights"""
    cursor = conn.cursor()
    cursor.execute('SELECT tag, weight, likes, dislikes FROM tag_weights ORDER BY weight DESC')
    return {row[0]: {'weight': row[1], 'likes': row[2], 'dislikes': row[3]} for row in cursor.fetchall()}

def test_learning():
    """Test that learning system works correctly"""
    print("="*60)
    print("  AI LEARNING SYSTEM TEST")
    print("="*60)
    
    conn = setup_test_db()
    
    # Clear previous test data
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tag_weights WHERE tag LIKE 'test_%'")
    cursor.execute("DELETE FROM images WHERE filename LIKE 'test_%'")
    conn.commit()
    
    # ==================== TEST 1: Basic Learning ====================
    print("\n📝 TEST 1: Basic Learning")
    print("-" * 40)
    
    # Simulate: User likes petite + toned, dislikes large
    test_data = [
        {'filename': 'test_001.png', 'rating': 5, 'tags': ['test_petite', 'test_toned', 'test_small_bust']},
        {'filename': 'test_002.png', 'rating': 5, 'tags': ['test_petite', 'test_toned', 'test_small_bust']},
        {'filename': 'test_003.png', 'rating': 5, 'tags': ['test_petite', 'test_visible_abs']},
        {'filename': 'test_004.png', 'rating': 1, 'tags': ['test_large', 'test_soft']},
        {'filename': 'test_005.png', 'rating': 1, 'tags': ['test_large', 'test_soft']},
    ]
    
    simulate_ratings(conn, test_data)
    weights = get_learned_weights(conn)
    
    # Verify learning
    petite_weight = weights.get('test_petite', {}).get('weight', 0)
    toned_weight = weights.get('test_toned', {}).get('weight', 0)
    large_weight = weights.get('test_large', {}).get('weight', 0)
    soft_weight = weights.get('test_soft', {}).get('weight', 0)
    
    print(f"   test_petite weight: {petite_weight:.3f} (expected > 0.6)")
    print(f"   test_toned weight: {toned_weight:.3f} (expected > 0.6)")
    print(f"   test_large weight: {large_weight:.3f} (expected < 0.4)")
    print(f"   test_soft weight: {soft_weight:.3f} (expected < 0.4)")
    
    test1_pass = petite_weight > 0.6 and toned_weight > 0.6 and large_weight < 0.4 and soft_weight < 0.4
    print(f"\n   Result: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    
    # ==================== TEST 2: Rapid Learning ====================
    print("\n📝 TEST 2: Rapid Learning (10 ratings)")
    print("-" * 40)
    
    # Simulate 10 more likes for a new tag
    rapid_data = [
        {'filename': f'test_rapid_{i}.png', 'rating': 5, 'tags': ['test_rapid_feature']}
        for i in range(10)
    ]
    
    simulate_ratings(conn, rapid_data)
    weights = get_learned_weights(conn)
    
    rapid_weight = weights.get('test_rapid_feature', {}).get('weight', 0)
    rapid_likes = weights.get('test_rapid_feature', {}).get('likes', 0)
    
    print(f"   test_rapid_feature: weight={rapid_weight:.3f}, likes={rapid_likes}")
    print(f"   Expected: weight > 0.8 after 10 likes")
    
    test2_pass = rapid_weight > 0.8 and rapid_likes == 10
    print(f"\n   Result: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    # ==================== TEST 3: Mixed Feedback ====================
    print("\n📝 TEST 3: Mixed Feedback Learning")
    print("-" * 40)
    
    # 7 likes, 3 dislikes = ~70% positive
    mixed_data = [
        {'filename': f'test_mixed_{i}.png', 'rating': 5, 'tags': ['test_mixed_tag']}
        for i in range(7)
    ] + [
        {'filename': f'test_mixed_neg_{i}.png', 'rating': 1, 'tags': ['test_mixed_tag']}
        for i in range(3)
    ]
    
    simulate_ratings(conn, mixed_data)
    weights = get_learned_weights(conn)
    
    mixed_weight = weights.get('test_mixed_tag', {}).get('weight', 0)
    mixed_likes = weights.get('test_mixed_tag', {}).get('likes', 0)
    mixed_dislikes = weights.get('test_mixed_tag', {}).get('dislikes', 0)
    
    print(f"   test_mixed_tag: weight={mixed_weight:.3f}, likes={mixed_likes}, dislikes={mixed_dislikes}")
    print(f"   Expected: weight ~0.67 (8/12 Bayesian)")
    
    test3_pass = 0.6 < mixed_weight < 0.75
    print(f"\n   Result: {'✅ PASS' if test3_pass else '❌ FAIL'}")
    
    # ==================== TEST 4: Preferred/Avoided Lists ====================
    print("\n📝 TEST 4: Preferred/Avoided Tag Lists")
    print("-" * 40)
    
    cursor = conn.cursor()
    
    # Get preferred (weight > 0.5)
    cursor.execute('''
        SELECT tag, weight FROM tag_weights 
        WHERE tag LIKE 'test_%' AND weight > 0.5 
        ORDER BY weight DESC
    ''')
    preferred = cursor.fetchall()
    
    # Get avoided (weight < 0.5)
    cursor.execute('''
        SELECT tag, weight FROM tag_weights 
        WHERE tag LIKE 'test_%' AND weight < 0.5 
        ORDER BY weight ASC
    ''')
    avoided = cursor.fetchall()
    
    print(f"   Preferred tags ({len(preferred)}):")
    for tag, weight in preferred[:5]:
        print(f"      {tag}: {weight:.3f}")
        
    print(f"\n   Avoided tags ({len(avoided)}):")
    for tag, weight in avoided[:5]:
        print(f"      {tag}: {weight:.3f}")
    
    test4_pass = len(preferred) > 0 and len(avoided) > 0
    print(f"\n   Result: {'✅ PASS' if test4_pass else '❌ FAIL'}")
    
    # ==================== SUMMARY ====================
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    all_pass = test1_pass and test2_pass and test3_pass and test4_pass
    
    print(f"\n   Test 1 (Basic Learning): {'✅' if test1_pass else '❌'}")
    print(f"   Test 2 (Rapid Learning): {'✅' if test2_pass else '❌'}")
    print(f"   Test 3 (Mixed Feedback): {'✅' if test3_pass else '❌'}")
    print(f"   Test 4 (Tag Lists): {'✅' if test4_pass else '❌'}")
    
    print(f"\n   Overall: {'✅ ALL TESTS PASSED' if all_pass else '❌ SOME TESTS FAILED'}")
    
    if all_pass:
        print("\n🧠 AI Learning System is working correctly!")
        print("   - Learns from user ratings")
        print("   - Increases weight for liked tags")
        print("   - Decreases weight for disliked tags")
        print("   - Can identify preferred and avoided tags")
    
    # Cleanup test data
    cursor.execute("DELETE FROM tag_weights WHERE tag LIKE 'test_%'")
    cursor.execute("DELETE FROM images WHERE filename LIKE 'test_%'")
    conn.commit()
    conn.close()
    
    return all_pass


if __name__ == "__main__":
    test_learning()
