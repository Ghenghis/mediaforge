"""
Dashboard API Server
Provides real-time stats for the WPF Dashboard
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import asyncio
import json
from pathlib import Path
from datetime import datetime
import requests

app = FastAPI(title="MediaForge Dashboard API")

# CORS for WPF access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class VideoStats(BaseModel):
    total_videos: int = 0
    processed_videos: int = 0
    approved_videos: int = 0
    rejected_videos: int = 0
    rejection_reasons: Dict[str, int] = {}

class FrameAnalysis(BaseModel):
    video_name: str
    frame_number: int
    gender: str
    body_type: str
    quality: int
    attractiveness: int
    approved: bool
    rejection_reason: Optional[str] = None
    timestamp: datetime = datetime.now()

class ModelVersion(BaseModel):
    name: str
    version: str
    status: str  # Ready, Training, Pending, Failed
    aesthetic_score: float = 0.0
    accuracy_rate: float = 0.0
    quality_score: float = 0.0
    failure_rate: float = 0.0
    overall_grade: str = "--"
    composite_score: float = 0.0
    training_steps: int = 0
    total_steps: int = 0

class TrainingProgress(BaseModel):
    model_name: str
    current_step: int
    total_steps: int
    current_loss: float
    learning_rate: float
    elapsed_seconds: int
    estimated_remaining_seconds: int

class SystemHealth(BaseModel):
    lm_studio_online: bool = False
    ollama_online: bool = False
    gpu_usage: float = 0.0
    memory_usage_gb: float = 0.0
    memory_total_gb: float = 16.0
    current_model: str = ""
    processing_speed_seconds: float = 0.0

class CurrentTask(BaseModel):
    stage: str = "IDLE"
    video_name: str = ""
    current_frame: int = 0
    total_frames: int = 0
    processing_time: float = 0.0
    last_analysis: Optional[FrameAnalysis] = None

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class DashboardState:
    def __init__(self):
        self.video_stats = VideoStats()
        self.current_task = CurrentTask()
        self.model_versions: List[ModelVersion] = self._init_models()
        self.recent_frames: List[FrameAnalysis] = []
        self.training_progress: Optional[TrainingProgress] = None
        self.system_health = SystemHealth()
        self.active_connections: List[WebSocket] = []
    
    def _init_models(self) -> List[ModelVersion]:
        return [
            ModelVersion(name="BRONZE", version="v1.0", status="Pending", total_steps=2000),
            ModelVersion(name="SILVER", version="v2.0", status="Pending", total_steps=1000),
            ModelVersion(name="GOLD", version="v3.0", status="Pending", total_steps=500),
            ModelVersion(name="PLATINUM", version="v4.0", status="Pending", total_steps=1500),
        ]
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSocket clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

state = DashboardState()

# ============================================================================
# SYSTEM HEALTH MONITORING
# ============================================================================

async def check_lm_studio() -> tuple[bool, str]:
    """Check if LM Studio is online"""
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=3)
        if response.status_code == 200:
            models = response.json()
            if models.get("data"):
                return True, models["data"][0].get("id", "Unknown")
        return False, ""
    except:
        return False, ""

async def check_ollama() -> bool:
    """Check if Ollama is online"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False

async def get_gpu_stats() -> tuple[float, float]:
    """Get GPU usage and memory"""
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", 
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            gpu_usage = float(parts[0])
            memory_mb = float(parts[1])
            return gpu_usage, memory_mb / 1024  # Convert to GB
    except:
        pass
    return 0.0, 0.0

async def update_system_health():
    """Update system health stats"""
    lm_online, model = await check_lm_studio()
    ollama_online = await check_ollama()
    gpu_usage, memory_gb = await get_gpu_stats()
    
    state.system_health = SystemHealth(
        lm_studio_online=lm_online,
        ollama_online=ollama_online,
        gpu_usage=gpu_usage,
        memory_usage_gb=memory_gb,
        memory_total_gb=16.0,  # Adjust based on your GPU
        current_model=model,
        processing_speed_seconds=4.07  # Will be updated during processing
    )
    
    await state.broadcast({
        "type": "system_health",
        "data": state.system_health.model_dump()
    })

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/status")
async def get_status():
    """Get overall system status"""
    await update_system_health()
    return state.system_health

@app.get("/api/videos/stats")
async def get_video_stats():
    """Get video processing statistics"""
    return state.video_stats

@app.post("/api/videos/stats")
async def update_video_stats(stats: VideoStats):
    """Update video processing statistics"""
    state.video_stats = stats
    await state.broadcast({"type": "video_stats", "data": stats.model_dump()})
    return {"status": "updated"}

@app.get("/api/task/current")
async def get_current_task():
    """Get current task info"""
    return state.current_task

@app.post("/api/task/current")
async def update_current_task(task: CurrentTask):
    """Update current task"""
    state.current_task = task
    await state.broadcast({"type": "current_task", "data": task.model_dump()})
    return {"status": "updated"}

@app.get("/api/frames/recent")
async def get_recent_frames():
    """Get recently analyzed frames"""
    return state.recent_frames[-20:]  # Last 20 frames

@app.post("/api/frames/add")
async def add_frame_analysis(frame: FrameAnalysis):
    """Add a new frame analysis"""
    state.recent_frames.append(frame)
    if len(state.recent_frames) > 100:
        state.recent_frames = state.recent_frames[-100:]
    await state.broadcast({"type": "frame_analysis", "data": frame.model_dump()})
    return {"status": "added"}

@app.get("/api/models")
async def get_model_versions():
    """Get all model versions"""
    return state.model_versions

@app.get("/api/models/{name}")
async def get_model_version(name: str):
    """Get specific model version"""
    for model in state.model_versions:
        if model.name.upper() == name.upper():
            return model
    return {"error": "Model not found"}

@app.post("/api/models/{name}/update")
async def update_model_version(name: str, update: ModelVersion):
    """Update model version info"""
    for i, model in enumerate(state.model_versions):
        if model.name.upper() == name.upper():
            state.model_versions[i] = update
            await state.broadcast({"type": "model_update", "data": update.model_dump()})
            return {"status": "updated"}
    return {"error": "Model not found"}

@app.get("/api/training/current")
async def get_training_progress():
    """Get current training progress"""
    return state.training_progress

@app.post("/api/training/update")
async def update_training_progress(progress: TrainingProgress):
    """Update training progress"""
    state.training_progress = progress
    await state.broadcast({"type": "training_progress", "data": progress.model_dump()})
    return {"status": "updated"}

@app.post("/api/filter/start")
async def start_filtering():
    """Start video filtering process"""
    state.current_task.stage = "FILTERING"
    await state.broadcast({"type": "status", "data": {"stage": "FILTERING"}})
    return {"status": "started"}

@app.post("/api/filter/pause")
async def pause_filtering():
    """Pause video filtering"""
    state.current_task.stage = "PAUSED"
    await state.broadcast({"type": "status", "data": {"stage": "PAUSED"}})
    return {"status": "paused"}

@app.post("/api/filter/stop")
async def stop_filtering():
    """Stop video filtering"""
    state.current_task.stage = "STOPPED"
    await state.broadcast({"type": "status", "data": {"stage": "STOPPED"}})
    return {"status": "stopped"}

# ============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ============================================================================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.active_connections.append(websocket)
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "init",
            "data": {
                "system_health": state.system_health.model_dump(),
                "video_stats": state.video_stats.model_dump(),
                "current_task": state.current_task.model_dump(),
                "model_versions": [m.model_dump() for m in state.model_versions],
                "recent_frames": [f.model_dump() for f in state.recent_frames[-20:]]
            }
        })
        
        # Keep connection alive and listen for messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        state.active_connections.remove(websocket)
    except Exception as e:
        if websocket in state.active_connections:
            state.active_connections.remove(websocket)

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Start background health monitoring"""
    asyncio.create_task(health_monitor_loop())

async def health_monitor_loop():
    """Background loop to monitor system health"""
    while True:
        await update_system_health()
        await asyncio.sleep(5)  # Update every 5 seconds

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("Starting Dashboard API Server...")
    print("API: http://localhost:8500")
    print("WebSocket: ws://localhost:8500/ws/live")
    print("Docs: http://localhost:8500/docs")
    uvicorn.run(app, host="0.0.0.0", port=8500)
