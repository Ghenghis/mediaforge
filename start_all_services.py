"""
UNIFIED SERVICE LAUNCHER
========================
Starts all services for the Western Story Generator system:
- Rating Studio Ultra (Port 8196)
- Story Generator API (Port 8197)

Also displays status of all systems.
"""
import subprocess
import sys
import time
import urllib.request
import json
from pathlib import Path

SCRIPTS_DIR = Path(r"c:\Users\Admin\civitai\scripts")

SERVICES = {
    "rating_studio": {
        "script": "rating_studio_ultra.py",
        "port": 8196,
        "name": "Rating Studio Ultra"
    },
    "story_generator": {
        "script": "story_generator_api.py", 
        "port": 8197,
        "name": "Western Story Generator"
    }
}

def check_port(port):
    """Check if service is running on port"""
    try:
        urllib.request.urlopen(f"http://localhost:{port}/api/stats", timeout=2)
        return True
    except:
        return False

def start_service(name, script, port):
    """Start a Python service"""
    script_path = SCRIPTS_DIR / script
    if not script_path.exists():
        print(f"   ❌ Script not found: {script}")
        return None
        
    if check_port(port):
        print(f"   ✅ Already running on port {port}")
        return None
        
    print(f"   🚀 Starting {script}...")
    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=str(SCRIPTS_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    # Wait for startup
    for i in range(10):
        time.sleep(1)
        if check_port(port):
            print(f"   ✅ Started on port {port}")
            return process
    
    print(f"   ⚠️ May be starting slowly...")
    return process

def get_stats(port):
    """Get stats from a service"""
    try:
        resp = urllib.request.urlopen(f"http://localhost:{port}/api/stats", timeout=5)
        return json.loads(resp.read())
    except:
        return None

def main():
    print("=" * 60)
    print("  WESTERN STORY GENERATOR - SERVICE LAUNCHER")
    print("=" * 60)
    
    processes = []
    
    for key, service in SERVICES.items():
        print(f"\n📦 {service['name']}")
        p = start_service(key, service['script'], service['port'])
        if p:
            processes.append(p)
    
    print("\n" + "=" * 60)
    print("  SERVICE STATUS")
    print("=" * 60)
    
    time.sleep(2)  # Wait for services to fully start
    
    for key, service in SERVICES.items():
        port = service['port']
        status = "🟢 ONLINE" if check_port(port) else "🔴 OFFLINE"
        print(f"\n{service['name']}: {status}")
        print(f"   URL: http://localhost:{port}")
        
        stats = get_stats(port)
        if stats:
            for k, v in stats.items():
                print(f"   {k}: {v}")
    
    print("\n" + "=" * 60)
    print("  QUICK LINKS")
    print("=" * 60)
    print(f"\n🎨 Rating Studio: http://localhost:8196")
    print(f"🤠 Story Generator: http://localhost:8197")
    
    print("\n" + "=" * 60)
    print("  NEXT STEPS")
    print("=" * 60)
    print("\n1. Open Rating Studio to rate images")
    print("2. Open Story Generator to create 525 actors")
    print("3. Generate images for actors")
    print("4. Rate generated images")
    
    print("\nPress Ctrl+C to stop all services...")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\nStopping services...")
        for p in processes:
            p.terminate()
        print("Done!")

if __name__ == "__main__":
    main()
