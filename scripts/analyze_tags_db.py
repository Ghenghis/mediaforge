"""
Analyze tags database to extract user preferences
"""
import sqlite3
from pathlib import Path
from collections import defaultdict
import json

DB_PATH = Path(r"c:\Users\Admin\civitai\data\tags.db")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\data")

def analyze_database():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables found: {tables}")
    
    results = {}
    
    for table in tables:
        # Get column info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"\n{table} columns: {columns}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table} rows: {count}")
        
        # Get sample data
        cursor.execute(f"SELECT * FROM {table} LIMIT 10")
        samples = cursor.fetchall()
        
        results[table] = {
            'columns': columns,
            'count': count,
            'samples': samples
        }
    
    conn.close()
    return results

def extract_tag_patterns(results):
    """Extract common tag patterns for preferences"""
    patterns = {
        'body_types': [],
        'breast_sizes': [],
        'face_types': [],
        'skin_tones': [],
        'paint_types': [],
        'poses': [],
        'ages': [],
        'expressions': []
    }
    
    # Keywords to look for
    keywords = {
        'body_types': ['slim', 'slender', 'toned', 'athletic', 'curvy', 'petite', 'fit', 'busty', 'lithe', 'well-built'],
        'breast_sizes': ['small breast', 'medium breast', 'large breast', 'flat chest', 'perfect breast', 'perky'],
        'face_types': ['oval face', 'round face', 'heart face', 'beautiful face', 'cute face', 'pretty face'],
        'skin_tones': ['fair skin', 'dark skin', 'caramel skin', 'pale', 'tanned', 'mahogany skin', 'light skin'],
        'paint_types': ['face paint', 'body paint', 'war paint', 'tribal paint', 'geometric paint', 'ritual paint'],
        'poses': ['standing', 'sitting', 'lying', 'action shot', 'medium shot', 'cowboy shot', 'full body'],
        'ages': ['18', '20', '21', '22', '23', '24', '25', 'young', 'adult'],
        'expressions': ['smile', 'smiling', 'serious', 'confident', 'seductive', 'dramatic', 'surprised']
    }
    
    return keywords

if __name__ == "__main__":
    print("="*60)
    print("  ANALYZING TAGS DATABASE")
    print("="*60)
    
    results = analyze_database()
    
    # Save results
    with open(OUTPUT_DIR / 'db_analysis.json', 'w', encoding='utf-8') as f:
        json.dump({k: {'columns': v['columns'], 'count': v['count']} for k, v in results.items()}, f, indent=2)
    
    print("\n✅ Analysis saved to db_analysis.json")
