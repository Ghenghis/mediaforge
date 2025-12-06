"""Check all databases for rating data"""
import sqlite3
from pathlib import Path

data_dir = Path(r"c:\Users\Admin\civitai\data")

for db_file in data_dir.glob("*.db"):
    print(f"\n=== {db_file.name} ===")
    try:
        conn = sqlite3.connect(str(db_file))
        c = conn.cursor()
        
        # Get tables
        tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print(f"  Tables: {tables}")
        
        # Check for images table
        if 'images' in tables:
            total = c.execute('SELECT COUNT(*) FROM images').fetchone()[0]
            rated = c.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
            print(f"  Images: {total} total, {rated} rated")
            
            if rated > 0:
                # Show rating distribution
                dist = c.execute('SELECT rating, COUNT(*) FROM images WHERE rating > 0 GROUP BY rating ORDER BY rating DESC').fetchall()
                print(f"  Distribution: {dict(dist)}")
                
        conn.close()
    except Exception as e:
        print(f"  Error: {e}")
