"""
LORAFORGE - DASHBOARD API
Dashboard API for LoraForge
FastAPI-based REST API serving real data from the indexer

Includes end-to-end system validation

ENDPOINTS:
- /api/stats: Overall statistics
- /api/media: Indexed media
- /api/models: Model rankings and benchmarks
- /api/pipeline: Pipeline status
- /api/learning: Self-learning data
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from indexer import get_database, get_learning_manager
from ai import get_model_manager, ModelRankingSystem, AutoBenchmarker


# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="LoRAForge Dashboard API",
    description="Real-time data API for LoRAForge dashboard",
    version="1.0.0"
)

# CORS for WPF
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
db = None
learning = None
model_manager = None
ranking_system = None


def get_instances():
    """Initialize global instances"""
    global db, learning, model_manager, ranking_system
    
    if db is None:
        db = get_database()
    if learning is None:
        learning = get_learning_manager()
    if model_manager is None:
        model_manager = get_model_manager()
    if ranking_system is None:
        ranking_system = ModelRankingSystem()
    
    return db, learning, model_manager, ranking_system


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class IndexRequest(BaseModel):
    directory: str
    recursive: bool = True
    analyze: bool = True


class FeedbackRequest(BaseModel):
    media_id: int
    feedback_type: str
    rating: int = None
    notes: str = None


class TagRequest(BaseModel):
    media_id: int
    tags: List[str]
    category: str = "custom"


class BenchmarkRequest(BaseModel):
    model_name: str
    provider: str
    task_type: str = "chat"


# ============================================
# STATISTICS ENDPOINTS
# ============================================

@app.get("/api/stats")
async def get_stats():
    """Get overall system statistics - REAL DATA"""
    db, learning, model_manager, ranking_system = get_instances()
    
    # Database stats
    db_stats = db.get_stats()
    
    # Learning stats
    learning_stats = learning.get_learning_summary()
    
    # Model stats
    try:
        all_models = model_manager.discover_all_models()
        model_count = len(all_models.get("ollama", [])) + len(all_models.get("lmstudio", []))
    except:
        model_count = 0
    
    # Get rankings count
    rankings = ranking_system.get_all_rankings(top_n=10)
    ranked_count = sum(len(r) for r in rankings.values())
    
    return {
        "timestamp": datetime.now().isoformat(),
        "database": db_stats,
        "learning": learning_stats,
        "models": {
            "total": model_count,
            "ranked": ranked_count
        },
        "status": "operational"
    }


@app.get("/api/stats/quick")
async def get_quick_stats():
    """Quick stats for dashboard header"""
    db, learning, _, _ = get_instances()
    
    stats = db.get_stats()
    
    return {
        "total_media": stats["total_media"],
        "total_images": stats["total_images"],
        "total_videos": stats["total_videos"],
        "analyzed": stats["total_analyzed"],
        "size_mb": round(stats["total_size_mb"], 1)
    }


# ============================================
# MEDIA ENDPOINTS
# ============================================

@app.get("/api/media")
async def list_media(
    media_type: str = None,
    status: str = None,
    limit: int = 100,
    offset: int = 0
):
    """List indexed media - REAL DATA"""
    db, _, _, _ = get_instances()
    
    media = db.list_media(
        media_type=media_type,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return {
        "count": len(media),
        "media": media
    }


@app.get("/api/media/{media_id}")
async def get_media(media_id: int):
    """Get single media with analysis"""
    db, learning, _, _ = get_instances()
    
    media = db.get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Get analysis
    analysis = db.get_analysis(media_id)
    
    # Get tags
    tags = learning.get_tags(media_id)
    
    # Get feedback
    feedback = learning.get_feedback(media_id)
    
    return {
        "media": media,
        "analysis": analysis,
        "tags": tags,
        "feedback": feedback
    }


@app.post("/api/media/index")
async def index_directory(request: IndexRequest):
    """Start indexing a directory"""
    from indexer import MediaIndexer
    
    indexer = MediaIndexer()
    
    # Run in background
    import threading
    
    def run_index():
        indexer.index_directory(
            Path(request.directory),
            recursive=request.recursive,
            analyze=request.analyze
        )
    
    thread = threading.Thread(target=run_index)
    thread.start()
    
    return {
        "status": "started",
        "directory": request.directory,
        "message": "Indexing started in background"
    }


@app.get("/api/media/duplicates")
async def get_duplicates():
    """Get duplicate files based on hash"""
    db, _, _, _ = get_instances()
    
    conn = db.get_connection()
    with conn:
        rows = conn.execute("""
            SELECT file_hash, COUNT(*) as count, GROUP_CONCAT(file_path) as paths
            FROM media
            WHERE file_hash IS NOT NULL
            GROUP BY file_hash
            HAVING count > 1
            LIMIT 50
        """).fetchall()
    
    return {
        "count": len(rows),
        "duplicates": [
            {"hash": r[0], "count": r[1], "paths": r[2].split(",")}
            for r in rows
        ]
    }


# ============================================
# FEEDBACK & TAGS ENDPOINTS
# ============================================

@app.post("/api/feedback")
async def add_feedback(request: FeedbackRequest):
    """Add user feedback for media"""
    _, learning, _, _ = get_instances()
    
    learning.add_feedback(
        request.media_id,
        request.feedback_type,
        request.rating,
        request.notes
    )
    
    return {"status": "success", "message": "Feedback recorded"}


@app.post("/api/tags")
async def add_tags(request: TagRequest):
    """Add tags to media"""
    _, learning, _, _ = get_instances()
    
    for tag in request.tags:
        learning.add_tag(request.media_id, tag, request.category)
    
    return {"status": "success", "tags_added": len(request.tags)}


@app.get("/api/tags/effective")
async def get_effective_tags():
    """Get most effective tags based on learning"""
    _, learning, _, _ = get_instances()
    
    effective = learning.get_effective_tags(min_effectiveness=0.6)
    ineffective = learning.get_ineffective_tags(max_effectiveness=0.3)
    
    return {
        "effective": effective,
        "ineffective": ineffective
    }


@app.get("/api/recommendations")
async def get_recommendations():
    """Get AI-powered recommendations"""
    _, learning, _, _ = get_instances()
    
    return learning.get_recommendations()


# ============================================
# MODEL ENDPOINTS
# ============================================

@app.get("/api/models")
async def list_models():
    """List all discovered models - REAL DATA"""
    _, _, model_manager, _ = get_instances()
    
    models = model_manager.discover_all_models()
    
    return {
        "ollama": [{"name": m.name, "provider": m.provider, "size_gb": m.size_gb, 
                    "params": m.parameter_count, "vision": m.is_vision, 
                    "uncensored": m.is_uncensored} 
                   for m in models.get("ollama", [])],
        "lmstudio": [{"name": m.name, "provider": m.provider, "size_gb": m.size_gb,
                      "params": m.parameter_count, "vision": m.is_vision,
                      "uncensored": m.is_uncensored}
                     for m in models.get("lmstudio", [])]
    }


@app.get("/api/models/rankings")
async def get_model_rankings(use_case: str = None, top_n: int = 10):
    """Get model rankings - REAL DATA"""
    _, _, _, ranking_system = get_instances()
    
    if use_case:
        rankings = ranking_system.get_rankings(use_case, top_n)
        return {use_case: rankings}
    else:
        return ranking_system.get_all_rankings(top_n)


@app.get("/api/models/best/{task}")
async def get_best_model(task: str):
    """Get best model for a task"""
    _, _, model_manager, ranking_system = get_instances()
    
    # Try rankings first
    ranking = ranking_system.get_best_for_task(task)
    
    if ranking:
        return ranking
    
    # Fall back to model manager
    best = model_manager.get_best_model(task)
    
    if best:
        return best
    
    raise HTTPException(status_code=404, detail=f"No tested models for {task}")


@app.get("/api/models/fast")
async def get_fast_models(min_speed: float = 50):
    """Get fast models"""
    _, _, model_manager, _ = get_instances()
    
    return model_manager.get_fast_models(min_speed)


@app.get("/api/models/uncensored")
async def get_uncensored_models():
    """Get uncensored models"""
    _, _, model_manager, _ = get_instances()
    
    return model_manager.get_uncensored_models()


@app.get("/api/models/configs")
async def get_recommended_configs():
    """Get recommended model configurations"""
    _, _, _, ranking_system = get_instances()
    
    return ranking_system.get_recommended_configs()


@app.post("/api/models/benchmark")
async def benchmark_model(request: BenchmarkRequest):
    """Benchmark a specific model"""
    _, _, model_manager, _ = get_instances()
    
    result = model_manager.benchmark_model(
        request.model_name,
        request.provider,
        request.task_type
    )
    
    if result:
        return {
            "success": result.success,
            "tokens_per_second": result.tokens_per_second,
            "quality": result.output_quality,
            "time": result.total_time,
            "error": result.error
        }
    
    raise HTTPException(status_code=500, detail="Benchmark failed")


@app.post("/api/models/benchmark/all")
async def benchmark_all_models():
    """Start benchmarking all models"""
    benchmarker = AutoBenchmarker()
    
    import threading
    
    def run_benchmark():
        benchmarker.benchmark_all_untested(max_models=20)
    
    thread = threading.Thread(target=run_benchmark)
    thread.start()
    
    return {"status": "started", "message": "Benchmarking started in background"}


# ============================================
# QUALITY CRITERIA ENDPOINTS
# ============================================

@app.get("/api/criteria")
async def get_quality_criteria():
    """Get current quality criteria"""
    _, learning, _, _ = get_instances()
    
    return learning.get_quality_criteria()


@app.post("/api/criteria/adjust")
async def adjust_criteria(criteria_name: str, direction: str, reason: str):
    """Manually adjust a quality criterion"""
    _, learning, _, _ = get_instances()
    
    learning.adjust_quality_criteria(criteria_name, direction, reason)
    
    return {"status": "adjusted", "criteria": criteria_name}


# ============================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ============================================

active_connections: List[WebSocket] = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time dashboard updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            db, learning, _, _ = get_instances()
            
            stats = db.get_stats()
            
            await websocket.send_json({
                "type": "stats_update",
                "data": {
                    "total_media": stats["total_media"],
                    "analyzed": stats["total_analyzed"],
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_update(update_type: str, data: dict):
    """Broadcast update to all connected clients"""
    for connection in active_connections:
        try:
            await connection.send_json({
                "type": update_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass


# ============================================
# STARTUP
# ============================================

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    get_instances()
    print("LoRAForge Dashboard API started")
    print("Endpoints: http://localhost:8000/docs")


def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api()
