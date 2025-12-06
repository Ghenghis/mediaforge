"""Check rating data from database"""
import sqlite3

conn = sqlite3.connect(r'c:\Users\Admin\civitai\data\master_learning.db')
c = conn.cursor()

print("=" * 50)
print("  RATING DATA SUMMARY")
print("=" * 50)

# Stats
r = c.execute('''SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) as rated,
    AVG(CASE WHEN rating > 0 THEN rating END) as avg_rating
FROM images''').fetchone()

print(f"\nTotal Images: {r[0]}")
print(f"Rated Images: {r[1]}")
if r[2]:
    print(f"Average Rating: {r[2]:.2f}")

# Distribution
print("\n--- RATING DISTRIBUTION ---")
dist = c.execute('''SELECT rating, COUNT(*) 
    FROM images WHERE rating > 0 
    GROUP BY rating ORDER BY rating DESC''').fetchall()
for row in dist:
    bar = "█" * int(row[1])
    print(f"  {int(row[0]):2d}: {row[1]:3d} {bar}")

# Excellent
print("\n--- EXCELLENT IMAGES (10+) ---")
excellent = c.execute('''SELECT filename, rating 
    FROM images WHERE rating >= 10 
    ORDER BY rating DESC''').fetchall()
print(f"  Count: {len(excellent)}")
for row in excellent[:15]:
    print(f"  ⭐ {row[1]:.0f} - {row[0]}")
if len(excellent) > 15:
    print(f"  ... and {len(excellent)-15} more")

# Gold
print("\n--- GOLD STANDARDS (15) ---")
gold = c.execute('SELECT filename FROM images WHERE rating >= 15').fetchall()
if gold:
    print(f"  Count: {len(gold)}")
    for row in gold[:10]:
        print(f"  🏆 {row[0]}")
else:
    print("  None yet")

# Low rated
print("\n--- LOW RATED (0-4) ---")
low = c.execute('SELECT COUNT(*) FROM images WHERE rating <= 4 AND rating > 0').fetchone()[0]
print(f"  Count: {low}")

# Sample of all ratings
print("\n--- SAMPLE RATED IMAGES ---")
sample = c.execute('''SELECT filename, rating 
    FROM images WHERE rating > 0 
    ORDER BY rated_at DESC LIMIT 10''').fetchall()
for row in sample:
    print(f"  {row[1]:5.1f} - {row[0]}")

print("\n" + "=" * 50)
print("  DATA CAPTURED SUCCESSFULLY!")
print("=" * 50)
