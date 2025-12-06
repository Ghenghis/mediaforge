"""
Extract User Preferences from Tags Database
Creates a comprehensive preferences file for quality control
"""
import sqlite3
import json
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(r"c:\Users\Admin\civitai\data\tags.db")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\data")

def get_top_tags_by_category():
    """Get top tags grouped by category"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Get categories
    cursor.execute("SELECT id, name FROM categories ORDER BY tag_count DESC")
    categories = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get top tags per category
    category_tags = {}
    for cat_id, cat_name in categories.items():
        cursor.execute("""
            SELECT tag, count FROM tags 
            WHERE category = ? 
            ORDER BY count DESC 
            LIMIT 50
        """, (cat_name,))
        category_tags[cat_name] = [(row[0], row[1]) for row in cursor.fetchall()]
    
    conn.close()
    return category_tags

def get_body_related_tags():
    """Extract body-related tags for preferences"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    body_keywords = [
        # Breast sizes
        '%breast%', '%chest%', '%bust%', '%nipple%',
        # Body types
        '%slim%', '%slender%', '%toned%', '%athletic%', '%curvy%', '%petite%', '%fit%',
        '%lithe%', '%busty%', '%thick%', '%thin%',
        # Face types
        '%face%', '%eyes%', '%lips%', '%cheek%', '%jaw%',
        # Skin
        '%skin%', '%tone%', '%dark%', '%fair%', '%pale%', '%tan%',
        # Paint
        '%paint%', '%tribal%', '%war%', '%makeup%', '%tattoo%',
        # Poses
        '%standing%', '%sitting%', '%lying%', '%pose%', '%shot%',
        # Body parts
        '%body%', '%thigh%', '%hip%', '%waist%', '%leg%', '%arm%'
    ]
    
    all_body_tags = []
    for keyword in body_keywords:
        cursor.execute("""
            SELECT tag, count, category FROM tags 
            WHERE tag LIKE ? 
            ORDER BY count DESC 
            LIMIT 20
        """, (keyword,))
        all_body_tags.extend(cursor.fetchall())
    
    conn.close()
    return all_body_tags

def categorize_preferences(body_tags):
    """Categorize tags into user preference groups"""
    prefs = {
        'breast_size': {
            'preferred': [],
            'excluded': []
        },
        'body_type': {
            'preferred': [],
            'excluded': []
        },
        'face_type': {
            'preferred': [],
            'excluded': []
        },
        'skin_tone': {
            'preferred': [],
            'excluded': []
        },
        'paint_style': {
            'preferred': [],
            'excluded': []
        },
        'pose_angle': {
            'preferred': [],
            'excluded': []
        },
        'age_range': {
            'preferred': [],
            'excluded': []
        }
    }
    
    for tag, count, category in body_tags:
        tag_lower = tag.lower()
        
        # Breast categorization
        if 'breast' in tag_lower or 'chest' in tag_lower or 'bust' in tag_lower:
            if count > 50:  # Frequently used = preferred
                prefs['breast_size']['preferred'].append({'tag': tag, 'count': count})
        
        # Body type
        if any(x in tag_lower for x in ['slim', 'slender', 'toned', 'athletic', 'fit', 'curvy', 'petite']):
            if count > 20:
                prefs['body_type']['preferred'].append({'tag': tag, 'count': count})
        if any(x in tag_lower for x in ['obese', 'overweight', 'fat']):
            prefs['body_type']['excluded'].append({'tag': tag, 'count': count})
        
        # Face type
        if 'face' in tag_lower:
            if count > 30:
                prefs['face_type']['preferred'].append({'tag': tag, 'count': count})
        
        # Skin tone
        if 'skin' in tag_lower or 'tone' in tag_lower:
            if count > 20:
                prefs['skin_tone']['preferred'].append({'tag': tag, 'count': count})
        
        # Paint style
        if 'paint' in tag_lower or 'tribal' in tag_lower or 'tattoo' in tag_lower:
            if count > 10:
                prefs['paint_style']['preferred'].append({'tag': tag, 'count': count})
    
    return prefs

def create_quality_standards():
    """Create quality standards based on user data"""
    return {
        "image_quality": {
            "required": [
                "masterpiece", "best quality", "8k", "high resolution",
                "detailed", "sharp focus", "realistic"
            ],
            "excluded": [
                "low quality", "worst quality", "blurry", "grainy",
                "low resolution", "jpeg artifacts", "watermark", "text"
            ]
        },
        "anatomy_standards": {
            "required": [
                "realistic anatomy", "correct proportions", "detailed hands",
                "detailed face", "detailed eyes"
            ],
            "excluded": [
                "bad anatomy", "bad proportions", "deformed hands", 
                "extra fingers", "missing fingers", "fused fingers",
                "mutated hands", "extra limbs", "missing limbs",
                "floating limbs", "disconnected limbs"
            ]
        },
        "style_standards": {
            "required": [
                "photorealistic", "realistic skin", "realistic textures",
                "realistic lighting"
            ],
            "excluded": [
                "cartoon", "anime", "3d render", "cgi", "illustration",
                "painting", "sketch", "drawing", "semi-realistic"
            ]
        },
        "content_boundaries": {
            "age_minimum": "adult",
            "age_tags": ["adult woman", "25yo", "22yo", "23yo", "24yo"],
            "excluded_ages": ["child", "kid", "young", "teen", "underage", "minor"]
        }
    }

def main():
    print("="*60)
    print("  EXTRACTING USER PREFERENCES")
    print("="*60)
    
    # Get category tags
    print("\n📊 Analyzing tag categories...")
    category_tags = get_top_tags_by_category()
    
    # Get body-related tags
    print("🔍 Extracting body-related tags...")
    body_tags = get_body_related_tags()
    print(f"   Found {len(body_tags)} body-related tags")
    
    # Categorize preferences
    print("📋 Categorizing preferences...")
    preferences = categorize_preferences(body_tags)
    
    # Create quality standards
    print("✅ Creating quality standards...")
    standards = create_quality_standards()
    
    # Combine into complete preferences file
    complete_prefs = {
        "user_preferences": preferences,
        "quality_standards": standards,
        "tribal_specific": {
            "paint_types": {
                "face_paint": [
                    "face paint", "geometric face paint", "tribal face paint",
                    "war paint", "ritual paint", "ceremonial paint"
                ],
                "body_paint": [
                    "body paint", "tribal body paint", "geometric patterns",
                    "ritual symbols", "shamanic symbols", "war paint"
                ],
                "colors": [
                    "red paint", "black paint", "white paint", "earth tones",
                    "bold colors", "natural pigments"
                ]
            },
            "accessories": [
                "feather headdress", "feathers", "bone jewelry",
                "tribal necklace", "ornamental earrings", "arm bands",
                "tribal patterns", "leather accessories"
            ],
            "themes": [
                "warrior", "shaman", "tribal beauty", "ceremonial",
                "primal", "exotic", "mystical", "fierce"
            ]
        },
        "body_standards": {
            "breast_size": {
                "preferred": ["medium breast", "medium breasts", "perfect breasts", "perky breasts"],
                "weights": {"medium breast": 1.0, "small breast": 0.8, "large breast": 0.6}
            },
            "body_type": {
                "preferred": ["slim body", "slender", "toned", "athletic", "fit", "lithe"],
                "excluded": ["obese", "overweight", "fat", "chubby"]
            },
            "face_type": {
                "preferred": ["beautiful face", "cute face", "oval face", "pretty face", "detailed face"],
                "features": ["freckles", "heterochromia", "detailed eyes", "striking makeup"]
            },
            "skin_tone": {
                "preferred": ["realistic skin", "detailed skin", "natural skin"],
                "tones": ["fair skin", "caramel skin", "dark skin", "mahogany skin", "tanned"]
            },
            "age_range": {
                "minimum": 18,
                "maximum": 30,
                "preferred": ["22yo", "23yo", "24yo", "25yo", "adult woman"]
            }
        },
        "generation_boundaries": {
            "always_include": [
                "masterpiece", "best quality", "8k", "detailed",
                "realistic skin", "sharp focus"
            ],
            "always_exclude": [
                "low quality", "worst quality", "bad anatomy",
                "deformed", "ugly", "cartoon", "anime",
                "child", "kid", "young", "teen", "minor"
            ],
            "fail_safes": {
                "anatomy_check": True,
                "quality_threshold": 0.7,
                "style_consistency": True,
                "age_verification": True
            }
        }
    }
    
    # Save preferences
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    with open(OUTPUT_DIR / 'user_preferences.json', 'w', encoding='utf-8') as f:
        json.dump(complete_prefs, f, indent=2, ensure_ascii=False)
    
    with open(OUTPUT_DIR / 'category_tags.json', 'w', encoding='utf-8') as f:
        json.dump({k: [{'tag': t[0], 'count': t[1]} for t in v[:30]] for k, v in category_tags.items()}, f, indent=2)
    
    print("\n" + "="*60)
    print("  PREFERENCES EXTRACTED!")
    print("="*60)
    print(f"\n📁 Files created:")
    print(f"   ✓ user_preferences.json")
    print(f"   ✓ category_tags.json")
    
    # Print summary
    print(f"\n📊 Summary:")
    for cat, prefs in preferences.items():
        preferred_count = len(prefs.get('preferred', []))
        excluded_count = len(prefs.get('excluded', []))
        print(f"   {cat}: {preferred_count} preferred, {excluded_count} excluded")

if __name__ == "__main__":
    main()
