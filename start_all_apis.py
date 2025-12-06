"""
LORAFORGE - START ALL APIS
============================
Starts all API services for the platform
"""
import subprocess
import sys
import time
import os
from pathlib import Path

# Service configuration
# All services to start
SERVICES = [
    {
        "name": "Rating System API",
        "script": "rating_system_api.py",
        "port": 8198
    },
    {
        "name": "Country Rating API",
        "script": "country_rating_api.py",
        "port": 8199
    },
    {
        "name": "Guardrails Engine",
        "script": "guardrails.py",
        "port": 8200
    },
    {
        "name": "Frontier Stories API",
        "script": "frontier_api_service.py",
        "port": 8195
    },
    {
        "name": "Teepee Image Generator",
        "script": "teepee_image_generator.py",
        "port": 8194
    },
    {
        "name": "Rating Studio Ultra",
        "script": "rating_studio_ultra.py",
        "port": 8196
    },
    {
        "name": "Story Generator API",
        "script": "story_generator_api.py",
        "port": 8197
    },
    {
        "name": "Admin System",
        "script": "admin/admin_system.py",
        "port": 8201
    },
    {
        "name": "Supabase Local",
        "script": "db/supabase_local.py",
        "port": 8202
    },
    {
        "name": "Playwright Automation",
        "script": "automation/playwright_pipeline.py",
        "port": 8203
    },
    {
        "name": "ComfyUI Integration",
        "script": "comfyui/comfyui_api.py",
        "port": 8204
    },
    {
        "name": "Dashboard API",
        "script": "api/dashboard_api.py",
        "port": 8100
    },
    {
        "name": "Full Pipeline Integration",
        "script": "full_pipeline_integration.py",
        "port": 8205
    },
    {
        "name": "Video Processing API",
        "script": "video_processing_api.py",
        "port": 8206
    },
    {
        "name": "Auto-Captioner API",
        "script": "auto_captioner_api.py",
        "port": 8207
    },
    {
        "name": "Rating UI API",
        "script": "rating_ui_api.py",
        "port": 8208
    },
    {
        "name": "Master Orchestrator",
        "script": "master_orchestrator.py",
        "port": 8210
    },
    {
        "name": "Dataset Builder",
        "script": "dataset_builder.py",
        "port": 8211
    },
    {
        "name": "ComfyUI Automation",
        "script": "comfyui_automation.py",
        "port": 8213
    },
    {
        "name": "Voice Integration",
        "script": "voice_integration_api.py",
        "port": 8212
    },
    {
        "name": "Training Scheduler",
        "script": "training_scheduler.py",
        "port": 8214
    },
    {
        "name": "Model Deployer",
        "script": "model_deployer.py",
        "port": 8215
    },
    {
        "name": "Quality Gate",
        "script": "quality_gate.py",
        "port": 8216
    },
    {
        "name": "External Launcher",
        "script": "external_service_launcher.py",
        "port": 8217
    },
    {
        "name": "Real-time Hub",
        "script": "realtime_hub.py",
        "port": 8218
    },
    {
        "name": "Voice Tools Unified",
        "script": "voice_tools_unified.py",
        "port": 8220
    },
    {
        "name": "Workflow Manager",
        "script": "workflow_manager.py",
        "port": 8221
    },
    {
        "name": "Dataset Auto-Scheduler",
        "script": "dataset_auto_scheduler.py",
        "port": 8222
    },
    {
        "name": "Gallery Auto-Scheduler",
        "script": "gallery_auto_scheduler.py",
        "port": 8223
    },
    {
        "name": "Backup Auto-Scheduler",
        "script": "backup_auto_scheduler.py",
        "port": 8224
    },
    {
        "name": "AI Learning Brain",
        "script": "ai_learning_brain.py",
        "port": 8225
    },
    {
        "name": "Story Collections",
        "script": "story_collection_system.py",
        "port": 8226
    },
    {
        "name": "LoRA Training",
        "script": "lora_training_integration.py",
        "port": 8230
    },
    {
        "name": "Unified Gateway",
        "script": "unified_gateway.py",
        "port": 8300
    },
    {
        "name": "Code Repair System",
        "script": "code_repair_system.py",
        "port": 8350
    }
]

SCRIPTS_DIR = Path(__file__).parent / "scripts"


def start_service(service):
    """Start a single service"""
    script_path = SCRIPTS_DIR / service["script"]
    
    if not script_path.exists():
        print(f"  [SKIP] {service['name']} - Script not found")
        return None
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(SCRIPTS_DIR)
        )
        time.sleep(1)  # Wait for startup
        
        if process.poll() is None:
            print(f"  [OK] {service['name']} - http://127.0.0.1:{service['port']}")
            return process
        else:
            print(f"  [FAIL] {service['name']} - Failed to start")
            return None
    except Exception as e:
        print(f"  [ERROR] {service['name']} - {e}")
        return None


def main():
    print("=" * 60)
    print("  LORAFORGE - STARTING ALL SERVICES")
    print("=" * 60)
    print()
    
    processes = []
    
    for service in SERVICES:
        proc = start_service(service)
        if proc:
            processes.append((service["name"], proc))
    
    print()
    print("=" * 60)
    print(f"  Started {len(processes)}/{len(SERVICES)} services")
    print("=" * 60)
    print()
    print("API Endpoints:")
    print("-" * 40)
    print("  Rating System:    http://127.0.0.1:8198")
    print("  Country Ratings:  http://127.0.0.1:8199")
    print("  Guardrails:       http://127.0.0.1:8200")
    print("  Frontier Stories: http://127.0.0.1:8195")
    print("  Story Collection: http://127.0.0.1:8196")
    print("  AI Learning:      http://127.0.0.1:8197")
    print("  Admin System:     http://127.0.0.1:8201")
    print("  Supabase Local:   http://127.0.0.1:8202")
    print("  Playwright:       http://127.0.0.1:8203")
    print("  ComfyUI:          http://127.0.0.1:8204")
    print("  Dashboard API:    http://127.0.0.1:8100")
    print("-" * 40)
    print()
    print("Press Ctrl+C to stop all services...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all services...")
        for name, proc in processes:
            proc.terminate()
            print(f"  Stopped {name}")
        print("All services stopped.")


if __name__ == "__main__":
    main()
