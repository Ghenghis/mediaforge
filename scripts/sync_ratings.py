"""Sync all ratings to master database"""
import sqlite3
from pathlib import Path

MASTER_DB = r"c:\Users\Admin\civitai\data\master_learning.db"
PREF_DB = r"c:\Users\Admin\civitai\data\preferences.db"

print("=" * 50)
print("  SYNCING RATINGS TO MASTER DATABASE")
print("=" * 50)

# Connect to both
master = sqlite3.connect(MASTER_DB)
pref = sqlite3.connect(PREF_DB)

# Get ratings from preferences.db
pref_ratings = pref.execute('''
    SELECT filename, rating FROM images WHERE rating > 0
''').fetchall()
print(f"\nFound {len(pref_ratings)} ratings in preferences.db")

# Sync to master
synced = 0
for filename, rating in pref_ratings:
    # Check if exists in master
    exists = master.execute('SELECT id FROM images WHERE filename = ?', (filename,)).fetchone()
    if exists:
        master.execute('UPDATE images SET rating = ? WHERE filename = ?', (rating, filename))
        synced += 1
    else:
        # Add new entry
        img_id = f"img_{hash(filename) % 10**8}"
        master.execute('''INSERT OR IGNORE INTO images (id, filename, rating) VALUES (?, ?, ?)''',
                      (img_id, filename, rating))
        synced += 1

master.commit()
print(f"Synced {synced} ratings to master_learning.db")

# Show final stats
print("\n--- MASTER DATABASE STATS ---")
total = master.execute('SELECT COUNT(*) FROM images').fetchone()[0]
rated = master.execute('SELECT COUNT(*) FROM images WHERE rating > 0').fetchone()[0]
print(f"Total images: {total}")
print(f"Rated images: {rated}")

dist = master.execute('''
    SELECT rating, COUNT(*) FROM images WHERE rating > 0 
    GROUP BY rating ORDER BY rating DESC
''').fetchall()
print("\nDistribution:")
for r, c in dist:
    print(f"  Rating {int(r):2d}: {c} images")

master.close()
pref.close()

print("\n" + "=" * 50)
print("  SYNC COMPLETE!")
print("=" * 50)
