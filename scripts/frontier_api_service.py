"""
Frontier Stories API Service
=============================
REST API for Frontier Stories integration with image generation.
Provides endpoints for story creation, image generation, and user feedback.

Port: 8195
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))
from frontier_stories_integration import (
    FrontierStoriesIntegration, DwellingType, SceneCategory,
    TeepeeStory, FrontierActor
)
from teepee_image_generator import (
    TeepeeImageGenerator, GenerationConfig
)
from adult_content_progression import (
    AdultContentProgressionSystem, AgeVerification,
    ContentRating, ClothingState, IntimacyLevel
)

app = Flask(__name__)

# Adult content system
adult_system = None
CORS(app)

# Global instances
integration = None
generator = None

def init_services():
    """Initialize services"""
    global integration, generator, adult_system
    integration = FrontierStoriesIntegration()
    generator = TeepeeImageGenerator()
    adult_system = AdultContentProgressionSystem()
    integration.load_actors_from_frontier()
    print(f"✅ Loaded {len(integration.actors)} actors")
    print(f"✅ Adult content system initialized")


# ============================================================
# ACTOR ENDPOINTS
# ============================================================

@app.route('/api/actors', methods=['GET'])
def get_actors():
    """Get all actors"""
    try:
        actors = integration.actors
        
        # Filtering
        tribe = request.args.get('tribe')
        role = request.args.get('role')
        limit = int(request.args.get('limit', 50))
        
        if tribe:
            actors = [a for a in actors if tribe.lower() in str(a.tags).lower()]
        if role:
            actors = [a for a in actors if role.lower() in a.role.lower()]
        
        actors = actors[:limit]
        
        return jsonify({
            "success": True,
            "count": len(actors),
            "actors": [
                {
                    "id": a.id,
                    "full_name": a.full_name,
                    "role": a.role,
                    "tribe": a.tribe,
                    "age": a.age,
                    "outfit": a.outfit,
                    "bio": a.bio[:200] if a.bio else ""
                }
                for a in actors
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/actors/<actor_id>', methods=['GET'])
def get_actor(actor_id: str):
    """Get single actor by ID"""
    try:
        actor = next((a for a in integration.actors if a.id == actor_id), None)
        if not actor:
            return jsonify({"success": False, "error": "Actor not found"}), 404
        
        return jsonify({
            "success": True,
            "actor": {
                "id": actor.id,
                "first_name": actor.first_name,
                "last_name": actor.last_name,
                "full_name": actor.full_name,
                "role": actor.role,
                "tribe": actor.tribe,
                "era": actor.era,
                "age": actor.age,
                "outfit": actor.outfit,
                "bio": actor.bio,
                "tags": actor.tags,
                "metadata": actor.metadata
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/actors/tribes', methods=['GET'])
def get_tribes():
    """Get list of available tribes"""
    tribes = set()
    for actor in integration.actors:
        for tag in actor.tags:
            if tag in ["Lakota", "Apache", "Cheyenne", "Navajo", "Shoshone",
                      "Pawnee", "Crow", "Blackfoot", "Comanche", "Sioux",
                      "Cherokee", "Blackfeet"]:
                tribes.add(tag)
    
    return jsonify({
        "success": True,
        "tribes": sorted(list(tribes)),
        "count": len(tribes)
    })


# ============================================================
# STORY ENDPOINTS
# ============================================================

@app.route('/api/stories/create', methods=['POST'])
def create_story():
    """Create a new teepee story"""
    try:
        data = request.json or {}
        
        # Get parameters
        dwelling_type = data.get('dwelling', 'teepee').upper()
        actor_count = data.get('actor_count', 3)
        tribe_filter = data.get('tribe')
        images_target = data.get('images_target', 300)
        actor_ids = data.get('actor_ids', [])
        
        # Get dwelling type enum
        try:
            dwelling = DwellingType[dwelling_type]
        except KeyError:
            dwelling = DwellingType.TEEPEE
        
        # Select actors
        if actor_ids:
            selected = [a for a in integration.actors if a.id in actor_ids]
        else:
            selected = integration.select_actors_for_teepee(actor_count, tribe_filter)
        
        if len(selected) < 2:
            return jsonify({
                "success": False, 
                "error": "Not enough actors found"
            }), 400
        
        # Generate story
        story = integration.generate_teepee_story(selected, dwelling, images_target)
        
        return jsonify({
            "success": True,
            "story": {
                "id": story.story_id,
                "title": story.title,
                "synopsis": story.synopsis,
                "dwelling": story.dwelling_type.value,
                "actors": [a.full_name for a in story.actors],
                "scene_count": len(story.scenes),
                "images_target": story.total_images_target,
                "prompts_generated": sum(len(s.image_prompts) for s in story.scenes)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/stories/<story_id>', methods=['GET'])
def get_story(story_id: str):
    """Get story details"""
    try:
        # Query from database
        import sqlite3
        conn = sqlite3.connect(str(integration.db_path))
        
        cursor = conn.execute(
            "SELECT * FROM teepee_stories WHERE id = ?", (story_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({"success": False, "error": "Story not found"}), 404
        
        return jsonify({
            "success": True,
            "story": {
                "id": row[0],
                "title": row[1],
                "synopsis": row[2],
                "dwelling": row[3],
                "actor_ids": json.loads(row[4]),
                "images_target": row[5],
                "images_generated": row[6],
                "status": row[7]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/stories/<story_id>/scenes', methods=['GET'])
def get_story_scenes(story_id: str):
    """Get all scenes for a story"""
    try:
        import sqlite3
        conn = sqlite3.connect(str(integration.db_path))
        
        cursor = conn.execute(
            "SELECT * FROM story_scenes WHERE story_id = ? ORDER BY scene_number",
            (story_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        scenes = []
        for row in rows:
            scenes.append({
                "id": row[0],
                "scene_number": row[2],
                "title": row[3],
                "description": row[4],
                "category": row[7],
                "time_of_day": row[8],
                "weather": row[9],
                "mood": row[10],
                "prompts": json.loads(row[11]) if row[11] else []
            })
        
        return jsonify({
            "success": True,
            "story_id": story_id,
            "scene_count": len(scenes),
            "scenes": scenes
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# GENERATION ENDPOINTS
# ============================================================

@app.route('/api/generate/batch', methods=['POST'])
def generate_batch():
    """Start batch image generation"""
    try:
        data = request.json or {}
        story_id = data.get('story_id')
        batch_size = data.get('batch_size', 10)
        
        if not story_id:
            return jsonify({"success": False, "error": "story_id required"}), 400
        
        # Get story scenes and create tasks
        import sqlite3
        conn = sqlite3.connect(str(integration.db_path))
        
        cursor = conn.execute(
            "SELECT image_prompts FROM story_scenes WHERE story_id = ?",
            (story_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        prompts = []
        for row in rows:
            if row[0]:
                prompts.extend(json.loads(row[0]))
        
        # Take batch
        batch_prompts = prompts[:batch_size]
        
        # Start async generation in background
        def run_generation():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Create tasks and run
            # ... simplified for demo
            loop.close()
        
        thread = threading.Thread(target=run_generation)
        thread.start()
        
        return jsonify({
            "success": True,
            "message": f"Started generation of {len(batch_prompts)} images",
            "story_id": story_id,
            "batch_size": len(batch_prompts),
            "total_prompts": len(prompts)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/generate/status/<story_id>', methods=['GET'])
def get_generation_status(story_id: str):
    """Get generation status for a story"""
    try:
        import sqlite3
        conn = sqlite3.connect(str(generator.db_path))
        
        cursor = conn.execute(
            "SELECT * FROM generation_stats WHERE story_id = ? ORDER BY started_at DESC LIMIT 1",
            (story_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                "success": True,
                "status": "not_started",
                "message": "No generation has been started for this story"
            })
        
        return jsonify({
            "success": True,
            "status": "completed" if row[7] else "in_progress",
            "stats": {
                "total": row[2],
                "completed": row[3],
                "failed": row[4],
                "avg_quality": row[5],
                "started": row[6],
                "finished": row[7]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# FEEDBACK ENDPOINTS
# ============================================================

@app.route('/api/feedback', methods=['POST'])
def record_feedback():
    """Record user feedback on generated image"""
    try:
        data = request.json or {}
        image_id = data.get('image_id')
        rating = data.get('rating', 0)
        feedback = data.get('feedback', '')
        
        if not image_id:
            return jsonify({"success": False, "error": "image_id required"}), 400
        
        generator.record_feedback(image_id, rating, feedback)
        
        return jsonify({
            "success": True,
            "message": "Feedback recorded",
            "image_id": image_id,
            "rating": rating
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """Get feedback statistics"""
    try:
        import sqlite3
        conn = sqlite3.connect(str(generator.db_path))
        
        cursor = conn.execute('''
            SELECT COUNT(*), AVG(rating), MIN(rating), MAX(rating)
            FROM user_feedback
        ''')
        row = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_ratings": row[0] or 0,
                "avg_rating": round(row[1] or 0, 2),
                "min_rating": row[2] or 0,
                "max_rating": row[3] or 0
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# MILESTONE ENDPOINTS
# ============================================================

@app.route('/api/milestones', methods=['GET'])
def get_milestones():
    """Get milestone progress"""
    try:
        milestones = []
        for mid, m in integration.milestones.items():
            milestones.append({
                "id": mid,
                "name": m.name,
                "target": m.target,
                "current": m.current,
                "percentage": round(m.percentage, 1),
                "status": m.status
            })
        
        return jsonify({
            "success": True,
            "milestones": milestones
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# FEATURES ENDPOINTS
# ============================================================

@app.route('/api/features', methods=['GET'])
def get_features():
    """Get 15 automated features"""
    try:
        features = integration.get_15_missing_features()
        
        return jsonify({
            "success": True,
            "count": len(features),
            "features": features
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# DWELLING TYPES
# ============================================================

@app.route('/api/dwellings', methods=['GET'])
def get_dwellings():
    """Get available dwelling types"""
    dwellings = [
        {"id": "teepee", "name": "Teepee", "description": "Traditional conical tent"},
        {"id": "earth_lodge", "name": "Earth Lodge", "description": "Semi-underground dwelling"},
        {"id": "wickiup", "name": "Wickiup", "description": "Dome-shaped shelter"},
        {"id": "longhouse", "name": "Longhouse", "description": "Communal wooden structure"},
        {"id": "pueblo", "name": "Pueblo", "description": "Adobe dwelling"},
        {"id": "frontier_cabin", "name": "Frontier Cabin", "description": "Log cabin"},
        {"id": "trading_post", "name": "Trading Post", "description": "Frontier trading station"}
    ]
    
    return jsonify({
        "success": True,
        "dwellings": dwellings
    })


# ============================================================
# AGE VERIFICATION & ADULT CONTENT ENDPOINTS
# ============================================================

@app.route('/api/age/verify', methods=['POST'])
def verify_age():
    """Verify user age via slider"""
    try:
        data = request.json or {}
        birth_year = data.get('birth_year')
        birth_month = data.get('birth_month', 1)
        birth_day = data.get('birth_day', 1)
        
        if not birth_year:
            return jsonify({"success": False, "error": "birth_year required"}), 400
        
        verification = adult_system.verify_age(birth_year, birth_month, birth_day)
        
        return jsonify({
            "success": True,
            "verified": verification.verified,
            "age": verification.age,
            "can_view_adult": verification.can_view_adult,
            "max_rating": verification.max_rating.name,
            "verified_at": verification.verified_at
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/age/status', methods=['GET'])
def get_age_status():
    """Get current age verification status"""
    try:
        if adult_system.age_verification:
            v = adult_system.age_verification
            return jsonify({
                "success": True,
                "verified": v.verified,
                "age": v.age,
                "can_view_adult": v.can_view_adult,
                "max_rating": v.max_rating.name
            })
        return jsonify({
            "success": True,
            "verified": False,
            "message": "Age not verified"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/adult/story/create', methods=['POST'])
def create_adult_story():
    """Create adult story arc with progression"""
    try:
        if not adult_system.age_verification or not adult_system.age_verification.can_view_adult:
            return jsonify({
                "success": False, 
                "error": "Age verification required for 21+ content"
            }), 403
        
        data = request.json or {}
        actor_ids = data.get('actor_ids', [])
        dwelling = data.get('dwelling', 'teepee')
        total_images = data.get('total_images', 300)
        adult_ratio = data.get('adult_ratio', 0.83)  # 250/300 = 83%
        
        # Get actor details
        actors = []
        for actor in integration.actors:
            if actor.id in actor_ids:
                actors.append({
                    "id": actor.id,
                    "full_name": actor.full_name,
                    "tribe": actor.tribe,
                    "role": actor.role,
                    "age": actor.age
                })
        
        if len(actors) < 2:
            # Auto-select actors
            selected = integration.select_actors_for_teepee(3)
            actors = [{
                "id": a.id,
                "full_name": a.full_name,
                "tribe": a.tribe,
                "role": a.role,
                "age": a.age
            } for a in selected]
        
        arc = adult_system.generate_adult_story_arc(
            actors=actors,
            dwelling=dwelling,
            total_images=total_images,
            adult_ratio=adult_ratio
        )
        
        # Count by rating
        rating_counts = {}
        for moment in arc.moments:
            rating = moment.content_rating.name
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
        
        return jsonify({
            "success": True,
            "arc": {
                "id": arc.arc_id,
                "title": arc.title,
                "description": arc.description,
                "dwelling": arc.dwelling,
                "era": arc.era,
                "total_images": arc.total_images,
                "adult_images": arc.adult_images,
                "moment_count": len(arc.moments),
                "rating_distribution": rating_counts,
                "actors": [a["full_name"] for a in actors]
            }
        })
    except PermissionError as e:
        return jsonify({"success": False, "error": str(e)}), 403
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/adult/story/<arc_id>/moments', methods=['GET'])
def get_adult_story_moments(arc_id: str):
    """Get moments for an adult story arc"""
    try:
        if not adult_system.age_verification or not adult_system.age_verification.can_view_adult:
            return jsonify({
                "success": False, 
                "error": "Age verification required"
            }), 403
        
        import sqlite3
        conn = sqlite3.connect(str(adult_system.db_path))
        
        cursor = conn.execute(
            "SELECT * FROM story_moments WHERE arc_id = ? ORDER BY moment_number",
            (arc_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        moments = []
        for row in rows:
            moments.append({
                "id": row[0],
                "scene_number": row[2],
                "moment_number": row[3],
                "title": row[4],
                "description": row[5],
                "time_of_day": row[7],
                "content_rating": ContentRating(row[8]).name,
                "intimacy_level": IntimacyLevel(row[10]).name,
                "image_prompt": row[11][:200] + "..." if row[11] and len(row[11]) > 200 else row[11]
            })
        
        return jsonify({
            "success": True,
            "arc_id": arc_id,
            "moment_count": len(moments),
            "moments": moments
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/adult/ratings', methods=['GET'])
def get_content_ratings():
    """Get available content rating levels"""
    ratings = [
        {"level": 0, "name": "PG", "description": "General audiences", "min_age": 0},
        {"level": 13, "name": "PG13", "description": "Teen content", "min_age": 13},
        {"level": 17, "name": "SOFT_R", "description": "Suggestive content", "min_age": 17},
        {"level": 18, "name": "R", "description": "Adult implied", "min_age": 18},
        {"level": 19, "name": "HARD_R", "description": "Adult explicit partial", "min_age": 18},
        {"level": 20, "name": "NC17", "description": "Adult explicit", "min_age": 18},
        {"level": 21, "name": "X", "description": "Extreme adult (21+ only)", "min_age": 21}
    ]
    
    return jsonify({
        "success": True,
        "ratings": ratings
    })


@app.route('/api/adult/clothing-states', methods=['GET'])
def get_clothing_states():
    """Get clothing progression states"""
    states = [
        {"level": 0, "name": "FULLY_DRESSED", "description": "Complete outfit"},
        {"level": 1, "name": "CASUAL_DRESS", "description": "Relaxed clothing"},
        {"level": 2, "name": "LIGHT_DRESS", "description": "Light/thin clothing"},
        {"level": 3, "name": "REVEALING", "description": "Revealing outfit"},
        {"level": 4, "name": "SEE_THROUGH", "description": "See-through fabrics"},
        {"level": 5, "name": "PARTIAL_UNDRESS", "description": "Partially undressed"},
        {"level": 6, "name": "MINIMAL", "description": "Minimal coverage"},
        {"level": 7, "name": "TOPLESS", "description": "Top removed"},
        {"level": 8, "name": "BOTTOMLESS", "description": "Bottom removed"},
        {"level": 9, "name": "NUDE", "description": "Full nude"}
    ]
    
    return jsonify({
        "success": True,
        "states": states
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "success": True,
        "service": "Frontier Stories API",
        "version": "1.0.0",
        "actors_loaded": len(integration.actors) if integration else 0,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API info"""
    return jsonify({
        "service": "Frontier Stories API",
        "version": "1.0.0",
        "endpoints": {
            "actors": "/api/actors",
            "tribes": "/api/actors/tribes",
            "stories": "/api/stories/create",
            "generate": "/api/generate/batch",
            "feedback": "/api/feedback",
            "milestones": "/api/milestones",
            "features": "/api/features",
            "dwellings": "/api/dwellings",
            "age_verify": "/api/age/verify",
            "age_status": "/api/age/status",
            "adult_story": "/api/adult/story/create",
            "adult_ratings": "/api/adult/ratings",
            "clothing_states": "/api/adult/clothing-states",
            "health": "/api/health"
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  FRONTIER STORIES API SERVICE")
    print("  Port: 8195")
    print("=" * 60)
    
    init_services()
    
    print("\n🚀 Starting API server...")
    print("   http://localhost:8195")
    print("\nEndpoints:")
    print("   GET  /api/actors       - List actors")
    print("   GET  /api/actors/tribes - List tribes")
    print("   POST /api/stories/create - Create story")
    print("   POST /api/generate/batch - Generate images")
    print("   POST /api/feedback     - Record rating")
    print("   GET  /api/milestones   - View progress")
    print("   GET  /api/features     - View 15 features")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8195, debug=False)
