"""
CODE REPAIR & QUALITY SYSTEM
==============================
Automated repair scripts that identify and fix coding issues
without disrupting functionality.

Features:
- Port conflict detection and resolution
- Database integrity checks
- Import validation
- API health monitoring
- Auto-recovery mechanisms
- Error classification and suggested fixes

Port: 8350
"""
import os
import sys
import json
import sqlite3
import socket
import importlib.util
import subprocess
import ast
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import time

# Configuration
PORT = 8350
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
SCRIPTS_DIR = CIVITAI_PATH / "scripts"
DATA_DIR = CIVITAI_PATH / "data"
LOG_PATH = DATA_DIR / "code_repair.log"

# Service port registry (correct assignments)
SERVICE_PORTS = {
    8100: "Dashboard API",
    8194: "Teepee Image Generator",
    8195: "Frontier Stories API",
    8196: "Rating Studio Ultra",
    8197: "Story Generator API",
    8198: "Rating System API",
    8199: "Country Rating API",
    8200: "Guardrails Engine",
    8201: "Admin System",
    8202: "Supabase Local",
    8203: "Playwright Automation",
    8204: "ComfyUI Integration",
    8205: "Full Pipeline Integration",
    8206: "Video Processing API",
    8207: "Auto-Captioner API",
    8208: "Rating UI API",
    8210: "Master Orchestrator",
    8211: "Dataset Builder",
    8212: "Voice Integration",
    8213: "ComfyUI Automation",
    8214: "Training Scheduler",
    8215: "Model Deployer",
    8216: "Quality Gate",
    8217: "External Launcher",
    8218: "Real-time Hub",
    8220: "Voice Tools Unified",
    8221: "Workflow Manager",
    8222: "Dataset Auto-Scheduler",
    8223: "Gallery Auto-Scheduler",
    8224: "Backup Auto-Scheduler",
    8225: "AI Learning Brain",
    8226: "Story Collections",
    8230: "LoRA Training",
    8300: "Unified Gateway",
    8350: "Code Repair System"
}


class RepairLog:
    """Logging for repair operations"""
    
    def __init__(self):
        self.entries = []
    
    def log(self, level: str, message: str, details: dict = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details or {}
        }
        self.entries.append(entry)
        
        # Write to file
        with open(LOG_PATH, 'a') as f:
            f.write(f"[{entry['timestamp']}] [{level}] {message}\n")
        
        print(f"[{level}] {message}")
        return entry
    
    def get_recent(self, count: int = 50):
        return self.entries[-count:]


repair_log = RepairLog()


class PortConflictChecker:
    """Detect and resolve port conflicts"""
    
    @staticmethod
    def check_port_in_use(port: int) -> bool:
        """Check if a port is currently in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return False
            except OSError:
                return True
    
    @staticmethod
    def get_port_conflicts() -> list:
        """Find all port conflicts"""
        conflicts = []
        for port, service in SERVICE_PORTS.items():
            if PortConflictChecker.check_port_in_use(port):
                conflicts.append({
                    "port": port,
                    "service": service,
                    "status": "in_use"
                })
        return conflicts
    
    @staticmethod
    def scan_scripts_for_port(port: int) -> list:
        """Find which scripts declare a specific port"""
        scripts_using_port = []
        for py_file in SCRIPTS_DIR.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if f"PORT = {port}" in content or f"port={port}" in content or f":{port}" in content:
                    scripts_using_port.append(str(py_file))
            except Exception:
                pass
        return scripts_using_port
    
    @staticmethod
    def suggest_fix(port: int) -> dict:
        """Suggest a fix for port conflict"""
        # Find next available port
        test_port = port + 1
        while PortConflictChecker.check_port_in_use(test_port) and test_port < port + 100:
            test_port += 1
        
        return {
            "original_port": port,
            "suggested_port": test_port,
            "action": f"Change PORT from {port} to {test_port}",
            "scripts": PortConflictChecker.scan_scripts_for_port(port)
        }


class DatabaseIntegrityChecker:
    """Check database health and repair issues"""
    
    @staticmethod
    def check_database(db_path: Path) -> dict:
        """Check a single database for integrity"""
        result = {
            "path": str(db_path),
            "exists": db_path.exists(),
            "readable": False,
            "tables": [],
            "size_bytes": 0,
            "issues": [],
            "status": "unknown"
        }
        
        if not db_path.exists():
            result["issues"].append("Database file does not exist")
            result["status"] = "missing"
            return result
        
        result["size_bytes"] = db_path.stat().st_size
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check integrity
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            if integrity != "ok":
                result["issues"].append(f"Integrity check failed: {integrity}")
                result["status"] = "corrupted"
            else:
                result["readable"] = True
                result["status"] = "healthy"
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            result["tables"] = [row[0] for row in cursor.fetchall()]
            
            conn.close()
        except Exception as e:
            result["issues"].append(f"Error accessing database: {str(e)}")
            result["status"] = "error"
        
        return result
    
    @staticmethod
    def check_all_databases() -> list:
        """Check all databases in data directory"""
        results = []
        for db_file in DATA_DIR.glob("*.db"):
            result = DatabaseIntegrityChecker.check_database(db_file)
            results.append(result)
        return results
    
    @staticmethod
    def repair_database(db_path: Path) -> dict:
        """Attempt to repair a corrupted database"""
        repair_result = {
            "path": str(db_path),
            "action": "repair_attempted",
            "success": False,
            "message": ""
        }
        
        try:
            # Create backup
            backup_path = db_path.with_suffix('.db.backup')
            import shutil
            shutil.copy2(db_path, backup_path)
            
            # Try to recover data
            conn = sqlite3.connect(str(db_path))
            conn.execute("VACUUM")
            conn.close()
            
            repair_result["success"] = True
            repair_result["message"] = f"Database vacuumed successfully. Backup at {backup_path}"
        except Exception as e:
            repair_result["message"] = f"Repair failed: {str(e)}"
        
        return repair_result


class ImportValidator:
    """Validate Python imports and dependencies"""
    
    @staticmethod
    def check_imports(py_file: Path) -> dict:
        """Check if a Python file has valid imports"""
        result = {
            "file": str(py_file),
            "syntax_valid": False,
            "imports": [],
            "missing_imports": [],
            "issues": []
        }
        
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
            result["syntax_valid"] = True
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["imports"].append(node.module)
            
            # Check if imports are available
            for imp in result["imports"]:
                try:
                    base_module = imp.split('.')[0]
                    importlib.util.find_spec(base_module)
                except ModuleNotFoundError:
                    # Check if it's a local import
                    local_path = SCRIPTS_DIR / base_module
                    if not local_path.exists() and not (local_path.parent / f"{base_module}.py").exists():
                        result["missing_imports"].append(imp)
                except Exception:
                    pass
        
        except SyntaxError as e:
            result["issues"].append(f"Syntax error: {e}")
        except Exception as e:
            result["issues"].append(f"Parse error: {e}")
        
        return result
    
    @staticmethod
    def scan_all_scripts() -> list:
        """Scan all Python scripts for import issues"""
        results = []
        for py_file in SCRIPTS_DIR.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                result = ImportValidator.check_imports(py_file)
                if result["missing_imports"] or result["issues"]:
                    results.append(result)
        return results


class APIHealthMonitor:
    """Monitor API service health"""
    
    @staticmethod
    def check_service(port: int, timeout: float = 2.0) -> dict:
        """Check if a service is responding"""
        import requests
        
        result = {
            "port": port,
            "service": SERVICE_PORTS.get(port, "Unknown"),
            "healthy": False,
            "response_time_ms": None,
            "error": None
        }
        
        try:
            start = time.time()
            resp = requests.get(f"http://127.0.0.1:{port}/", timeout=timeout)
            elapsed = (time.time() - start) * 1000
            
            result["healthy"] = resp.status_code == 200
            result["response_time_ms"] = round(elapsed, 2)
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection refused"
        except requests.exceptions.Timeout:
            result["error"] = "Timeout"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def check_all_services() -> dict:
        """Check health of all registered services"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "services": [],
            "healthy_count": 0,
            "unhealthy_count": 0
        }
        
        for port in SERVICE_PORTS.keys():
            if port != PORT:  # Don't check ourselves
                service_result = APIHealthMonitor.check_service(port)
                results["services"].append(service_result)
                if service_result["healthy"]:
                    results["healthy_count"] += 1
                else:
                    results["unhealthy_count"] += 1
        
        return results


class ErrorClassifier:
    """Classify errors and suggest fixes"""
    
    COMMON_ERRORS = {
        "ModuleNotFoundError": {
            "category": "dependency",
            "suggestion": "Install missing module with: pip install {module}",
            "auto_fix": True
        },
        "ConnectionRefusedError": {
            "category": "network",
            "suggestion": "Service not running. Start the service or check port availability.",
            "auto_fix": False
        },
        "sqlite3.OperationalError": {
            "category": "database",
            "suggestion": "Database locked or corrupted. Try closing other connections or run repair.",
            "auto_fix": True
        },
        "PermissionError": {
            "category": "filesystem",
            "suggestion": "Check file permissions or close programs using the file.",
            "auto_fix": False
        },
        "JSONDecodeError": {
            "category": "data",
            "suggestion": "Invalid JSON file. Check for syntax errors in configuration.",
            "auto_fix": False
        },
        "KeyError": {
            "category": "code",
            "suggestion": "Missing key in dictionary. Check configuration files for required fields.",
            "auto_fix": False
        },
        "AttributeError": {
            "category": "code",
            "suggestion": "Object missing expected attribute. Check class initialization.",
            "auto_fix": False
        },
        "TypeError": {
            "category": "code",
            "suggestion": "Type mismatch. Check function arguments and return types.",
            "auto_fix": False
        }
    }
    
    @staticmethod
    def classify_error(error_type: str, error_message: str) -> dict:
        """Classify an error and suggest fixes"""
        result = {
            "error_type": error_type,
            "error_message": error_message,
            "category": "unknown",
            "suggestion": "Review the error message and stack trace for details.",
            "auto_fix": False,
            "severity": "medium"
        }
        
        for err_pattern, info in ErrorClassifier.COMMON_ERRORS.items():
            if err_pattern in error_type:
                result["category"] = info["category"]
                result["suggestion"] = info["suggestion"]
                result["auto_fix"] = info["auto_fix"]
                break
        
        # Determine severity
        if "critical" in error_message.lower() or "fatal" in error_message.lower():
            result["severity"] = "critical"
        elif "warning" in error_message.lower():
            result["severity"] = "low"
        
        return result


class CodeQualityAnalyzer:
    """Analyze code quality metrics"""
    
    @staticmethod
    def analyze_file(py_file: Path) -> dict:
        """Analyze a single Python file for quality metrics"""
        result = {
            "file": str(py_file),
            "lines_total": 0,
            "lines_code": 0,
            "lines_comment": 0,
            "lines_blank": 0,
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "docstrings": 0,
            "issues": []
        }
        
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            result["lines_total"] = len(lines)
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    result["lines_blank"] += 1
                elif stripped.startswith('#'):
                    result["lines_comment"] += 1
                else:
                    result["lines_code"] += 1
            
            # Parse AST for metrics
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    result["functions"] += 1
                    # Check for docstring
                    if ast.get_docstring(node):
                        result["docstrings"] += 1
                elif isinstance(node, ast.ClassDef):
                    result["classes"] += 1
                    if ast.get_docstring(node):
                        result["docstrings"] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    result["imports"] += 1
            
            # Quality checks
            if result["lines_code"] > 500 and result["functions"] < 3:
                result["issues"].append("Large file with few functions - consider refactoring")
            
            if result["functions"] > 0 and result["docstrings"] / result["functions"] < 0.5:
                result["issues"].append("Low docstring coverage")
        
        except Exception as e:
            result["issues"].append(f"Analysis error: {e}")
        
        return result


# Initialize components
port_checker = PortConflictChecker()
db_checker = DatabaseIntegrityChecker()
import_validator = ImportValidator()
api_monitor = APIHealthMonitor()
error_classifier = ErrorClassifier()
quality_analyzer = CodeQualityAnalyzer()


class CodeRepairAPI(BaseHTTPRequestHandler):
    """API for code repair system"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
    
    def do_OPTIONS(self):
        self._json({})
    
    def do_GET(self):
        path = self.path.split('?')[0]
        params = parse_qs(urlparse(self.path).query)
        
        if path == '/':
            self._json({
                "service": "Code Repair System",
                "version": "1.0",
                "port": PORT,
                "endpoints": {
                    "/api/health": "System health check",
                    "/api/ports": "Check port conflicts",
                    "/api/databases": "Check database integrity",
                    "/api/imports": "Validate Python imports",
                    "/api/services": "Check API services",
                    "/api/quality": "Code quality metrics",
                    "/api/logs": "Recent repair logs",
                    "/api/full-scan": "Complete system scan"
                }
            })
        
        elif path == '/api/health':
            self._json({"status": "healthy", "timestamp": datetime.now().isoformat()})
        
        elif path == '/api/ports':
            conflicts = port_checker.get_port_conflicts()
            suggestions = [port_checker.suggest_fix(c["port"]) for c in conflicts]
            self._json({
                "conflicts": conflicts,
                "suggestions": suggestions,
                "total_ports": len(SERVICE_PORTS)
            })
        
        elif path == '/api/databases':
            results = db_checker.check_all_databases()
            healthy = sum(1 for r in results if r["status"] == "healthy")
            self._json({
                "databases": results,
                "total": len(results),
                "healthy": healthy,
                "issues": len(results) - healthy
            })
        
        elif path == '/api/imports':
            results = import_validator.scan_all_scripts()
            self._json({
                "scripts_with_issues": results,
                "total_issues": len(results)
            })
        
        elif path == '/api/services':
            results = api_monitor.check_all_services()
            self._json(results)
        
        elif path == '/api/quality':
            # Analyze key scripts
            key_scripts = [
                SCRIPTS_DIR / "story_generator_api.py",
                SCRIPTS_DIR / "rating_system_api.py",
                SCRIPTS_DIR / "country_rating_api.py",
                SCRIPTS_DIR / "master_orchestrator.py",
                SCRIPTS_DIR / "unified_gateway.py"
            ]
            results = [quality_analyzer.analyze_file(s) for s in key_scripts if s.exists()]
            self._json({"analyses": results})
        
        elif path == '/api/logs':
            count = int(params.get('count', [50])[0])
            self._json({"logs": repair_log.get_recent(count)})
        
        elif path == '/api/full-scan':
            repair_log.log("INFO", "Starting full system scan")
            
            scan_result = {
                "timestamp": datetime.now().isoformat(),
                "port_conflicts": port_checker.get_port_conflicts(),
                "database_health": db_checker.check_all_databases(),
                "import_issues": import_validator.scan_all_scripts(),
                "service_health": api_monitor.check_all_services(),
                "summary": {}
            }
            
            # Calculate summary
            scan_result["summary"] = {
                "port_conflicts": len(scan_result["port_conflicts"]),
                "database_issues": sum(1 for d in scan_result["database_health"] if d["status"] != "healthy"),
                "import_issues": len(scan_result["import_issues"]),
                "services_down": scan_result["service_health"]["unhealthy_count"]
            }
            
            repair_log.log("INFO", "Full scan complete", scan_result["summary"])
            self._json(scan_result)
        
        else:
            self._json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/repair/database':
            db_path = Path(data.get('path', ''))
            if db_path.exists():
                result = db_checker.repair_database(db_path)
                repair_log.log("INFO", f"Database repair attempted: {db_path}", result)
                self._json(result)
            else:
                self._json({"error": "Database not found"}, 404)
        
        elif path == '/api/classify-error':
            error_type = data.get('error_type', '')
            error_message = data.get('error_message', '')
            result = error_classifier.classify_error(error_type, error_message)
            self._json(result)
        
        else:
            self._json({"error": "Not found"}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  CODE REPAIR & QUALITY SYSTEM")
    print("  Automated Issue Detection & Resolution")
    print("=" * 60)
    
    repair_log.log("INFO", "Code Repair System starting")
    
    # Initial scan
    print("\n🔍 Running initial system scan...")
    
    conflicts = port_checker.get_port_conflicts()
    print(f"   Port conflicts: {len(conflicts)}")
    
    db_results = db_checker.check_all_databases()
    healthy_dbs = sum(1 for r in db_results if r["status"] == "healthy")
    print(f"   Databases: {healthy_dbs}/{len(db_results)} healthy")
    
    import_issues = import_validator.scan_all_scripts()
    print(f"   Import issues: {len(import_issues)}")
    
    print(f"\n🌐 http://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), CodeRepairAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
