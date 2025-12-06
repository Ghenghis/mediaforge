"""
LORAFORGE - QUICK HEALTH CHECK
================================
Fast system health verification without starting any services.
Run this after PC crash or when issues are suspected.
"""
import os
import sys
import json
import sqlite3
import socket
from pathlib import Path
from datetime import datetime

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
SCRIPTS_DIR = CIVITAI_PATH / "scripts"
DATA_DIR = CIVITAI_PATH / "data"

# ANSI Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

def check_port(port: int) -> bool:
    """Check if port is available (not in use)"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True  # Available
        except OSError:
            return False  # In use

def check_database(db_path: Path) -> dict:
    """Check database health"""
    if not db_path.exists():
        return {"status": "missing", "error": "File not found"}
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=5)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        conn.close()
        
        if result == "ok":
            return {"status": "healthy", "size_kb": db_path.stat().st_size // 1024}
        return {"status": "corrupted", "error": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_script(script_path: Path) -> dict:
    """Check if Python script is valid"""
    if not script_path.exists():
        return {"status": "missing"}
    
    try:
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        compile(code, script_path.name, 'exec')
        return {"status": "valid", "size_kb": script_path.stat().st_size // 1024}
    except SyntaxError as e:
        return {"status": "syntax_error", "error": f"Line {e.lineno}: {e.msg}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_config(config_path: Path) -> dict:
    """Check JSON config file"""
    if not config_path.exists():
        return {"status": "missing"}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return {"status": "valid", "size_kb": config_path.stat().st_size // 1024}
    except json.JSONDecodeError as e:
        return {"status": "invalid_json", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  LORAFORGE - QUICK HEALTH CHECK{RESET}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")
    
    issues_found = 0
    
    # Check critical directories
    print(f"{BOLD}📁 DIRECTORIES{RESET}")
    dirs_to_check = [
        SCRIPTS_DIR, 
        DATA_DIR, 
        SCRIPTS_DIR / "core",
        SCRIPTS_DIR / "ai",
        SCRIPTS_DIR / "indexer",
        CIVITAI_PATH / "ui" / "WPF"
    ]
    
    for d in dirs_to_check:
        if d.exists():
            item_count = len(list(d.iterdir())) if d.is_dir() else 0
            print(f"  {GREEN}✓{RESET} {d.name}/ ({item_count} items)")
        else:
            print(f"  {RED}✗{RESET} {d.name}/ - MISSING")
            issues_found += 1
    
    # Check critical scripts
    print(f"\n{BOLD}📜 CRITICAL SCRIPTS{RESET}")
    scripts = [
        "story_generator_api.py",
        "rating_system_api.py",
        "country_rating_api.py",
        "master_orchestrator.py",
        "unified_gateway.py",
        "guardrails.py",
        "code_repair_system.py"
    ]
    
    for script in scripts:
        path = SCRIPTS_DIR / script
        result = check_script(path)
        if result["status"] == "valid":
            print(f"  {GREEN}✓{RESET} {script} ({result['size_kb']}KB)")
        elif result["status"] == "missing":
            print(f"  {YELLOW}!{RESET} {script} - NOT FOUND")
            issues_found += 1
        else:
            print(f"  {RED}✗{RESET} {script} - {result['status']}: {result.get('error', '')}")
            issues_found += 1
    
    # Check databases
    print(f"\n{BOLD}🗄️ DATABASES{RESET}")
    databases = [
        "rating_system.db",
        "country_ratings.db",
        "orchestrator.db",
        "western_stories.db",
        "guardrails.db",
        "loraforge.db"
    ]
    
    for db in databases:
        path = DATA_DIR / db
        result = check_database(path)
        if result["status"] == "healthy":
            print(f"  {GREEN}✓{RESET} {db} ({result['size_kb']}KB)")
        elif result["status"] == "missing":
            print(f"  {YELLOW}!{RESET} {db} - Will be created on first run")
        else:
            print(f"  {RED}✗{RESET} {db} - {result['status']}: {result.get('error', '')}")
            issues_found += 1
    
    # Check config files
    print(f"\n{BOLD}⚙️ CONFIG FILES{RESET}")
    configs = [
        "comprehensive_ratings.json",
        "international_ratings.json",
        "content_rating_system.json",
        "user_preferences.json"
    ]
    
    for config in configs:
        path = DATA_DIR / config
        result = check_config(path)
        if result["status"] == "valid":
            print(f"  {GREEN}✓{RESET} {config} ({result['size_kb']}KB)")
        elif result["status"] == "missing":
            print(f"  {YELLOW}!{RESET} {config} - NOT FOUND")
            issues_found += 1
        else:
            print(f"  {RED}✗{RESET} {config} - {result['status']}: {result.get('error', '')}")
            issues_found += 1
    
    # Check key ports
    print(f"\n{BOLD}🔌 PORT AVAILABILITY{RESET}")
    ports = {
        8195: "Frontier Stories",
        8197: "Story Generator",
        8198: "Rating System",
        8199: "Country Ratings",
        8200: "Guardrails",
        8210: "Master Orchestrator",
        8300: "Unified Gateway",
        8350: "Code Repair"
    }
    
    for port, name in ports.items():
        available = check_port(port)
        if available:
            print(f"  {GREEN}✓{RESET} :{port} available ({name})")
        else:
            print(f"  {YELLOW}!{RESET} :{port} IN USE ({name})")
    
    # Summary
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    if issues_found == 0:
        print(f"  {GREEN}✓ ALL CHECKS PASSED{RESET}")
        print(f"  System ready to start: python start_all_apis.py")
    else:
        print(f"  {YELLOW}! {issues_found} ISSUES FOUND{RESET}")
        print(f"  Review above and fix issues before starting services")
    print(f"{BOLD}{'=' * 60}{RESET}\n")
    
    return issues_found


if __name__ == "__main__":
    sys.exit(main())
