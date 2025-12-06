"""
VOICE TOOLS UNIFIED
====================
Unified interface for all voice/TTS engines:
- GPT-SoVITS (primary)
- Orpheus-TTS
- Fish-Speech
- RealtimeTTS

Port: 8220
"""
import json
import sqlite3
import threading
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
PORT = 8220
DB_PATH = Path(r"c:\Users\Admin\civitai\data\voice_tools.db")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\output\audio")
PROJECT_DIR = Path(r"c:\Users\Admin\civitai\project")

# Ensure directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Voice engine configurations
ENGINES = {
    "gpt_sovits": {
        "name": "GPT-SoVITS",
        "url": "http://127.0.0.1:9880",
        "path": PROJECT_DIR / "GPT-SoVITS-main" / "GPT-SoVITS-main",
        "capabilities": ["clone", "tts", "emotion"],
        "quality": "high",
        "speed": "slow",
        "priority": 1
    },
    "orpheus": {
        "name": "Orpheus-TTS", 
        "url": None,  # Local library
        "path": PROJECT_DIR / "Orpheus-TTS-main",
        "capabilities": ["tts"],
        "quality": "medium",
        "speed": "fast",
        "priority": 2
    },
    "fish_speech": {
        "name": "Fish-Speech",
        "url": None,  # Local library
        "path": PROJECT_DIR / "fish-speech-main",
        "capabilities": ["clone", "tts"],
        "quality": "high",
        "speed": "medium",
        "priority": 3
    },
    "realtime_tts": {
        "name": "RealtimeTTS",
        "url": None,  # Local library
        "path": PROJECT_DIR / "RealtimeTTS-master",
        "capabilities": ["tts", "streaming"],
        "quality": "medium",
        "speed": "realtime",
        "priority": 4
    }
}

# Character voice profiles
VOICE_PROFILES = {
    "narrator": {"gender": "male", "age": "adult", "tone": "authoritative"},
    "sheriff": {"gender": "male", "age": "adult", "tone": "stern"},
    "saloon_lady": {"gender": "female", "age": "adult", "tone": "flirty"},
    "outlaw": {"gender": "male", "age": "adult", "tone": "gruff"},
    "native_chief": {"gender": "male", "age": "elder", "tone": "wise"},
    "young_woman": {"gender": "female", "age": "young", "tone": "cheerful"},
    "old_timer": {"gender": "male", "age": "elder", "tone": "nostalgic"},
    "rancher": {"gender": "male", "age": "adult", "tone": "friendly"},
    "schoolmarm": {"gender": "female", "age": "adult", "tone": "proper"},
    "preacher": {"gender": "male", "age": "adult", "tone": "solemn"}
}

# Emotion presets
EMOTIONS = {
    "neutral": {"pitch": 1.0, "speed": 1.0, "energy": 0.5},
    "happy": {"pitch": 1.1, "speed": 1.1, "energy": 0.8},
    "sad": {"pitch": 0.9, "speed": 0.85, "energy": 0.3},
    "angry": {"pitch": 1.05, "speed": 1.2, "energy": 0.9},
    "fearful": {"pitch": 1.15, "speed": 1.3, "energy": 0.7},
    "surprised": {"pitch": 1.2, "speed": 1.15, "energy": 0.85},
    "whisper": {"pitch": 1.0, "speed": 0.9, "energy": 0.2},
    "shout": {"pitch": 1.1, "speed": 1.0, "energy": 1.0}
}


class VoiceDB:
    """Database for voice generation tracking"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engine TEXT NOT NULL,
                text TEXT NOT NULL,
                character TEXT,
                emotion TEXT,
                output_path TEXT,
                duration REAL,
                status TEXT DEFAULT 'pending',
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS engine_status (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                available INTEGER DEFAULT 0,
                last_check TEXT,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS voice_clones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                reference_audio TEXT,
                reference_text TEXT,
                engine TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Initialize engine records
        for eid, engine in ENGINES.items():
            self.conn.execute('''
                INSERT OR IGNORE INTO engine_status (id, name)
                VALUES (?, ?)
            ''', (eid, engine['name']))
        
        self.conn.commit()
    
    def log_generation(self, engine, text, character=None, emotion=None):
        cursor = self.conn.execute('''
            INSERT INTO generations (engine, text, character, emotion)
            VALUES (?, ?, ?, ?)
        ''', (engine, text, character, emotion))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_generation(self, gen_id, **kwargs):
        sets = ', '.join(f"{k} = ?" for k in kwargs.keys())
        self.conn.execute(f'UPDATE generations SET {sets} WHERE id = ?',
                         list(kwargs.values()) + [gen_id])
        self.conn.commit()
    
    def update_engine_status(self, engine_id, available):
        self.conn.execute('''
            UPDATE engine_status SET available = ?, last_check = ?
            WHERE id = ?
        ''', (1 if available else 0, datetime.now().isoformat(), engine_id))
        self.conn.commit()
    
    def increment_success(self, engine_id):
        self.conn.execute('''
            UPDATE engine_status SET success_count = success_count + 1
            WHERE id = ?
        ''', (engine_id,))
        self.conn.commit()
    
    def increment_error(self, engine_id):
        self.conn.execute('''
            UPDATE engine_status SET error_count = error_count + 1
            WHERE id = ?
        ''', (engine_id,))
        self.conn.commit()
    
    def get_engine_status(self):
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM engine_status'
        ).fetchall()]
    
    def get_generations(self, limit=50):
        return [dict(r) for r in self.conn.execute('''
            SELECT * FROM generations ORDER BY created_at DESC LIMIT ?
        ''', (limit,)).fetchall()]
    
    def get_stats(self):
        total = self.conn.execute('SELECT COUNT(*) FROM generations').fetchone()[0]
        success = self.conn.execute(
            'SELECT COUNT(*) FROM generations WHERE status = "completed"'
        ).fetchone()[0]
        
        return {
            'total_generations': total,
            'successful': success,
            'success_rate': round(success / total * 100, 1) if total > 0 else 0
        }


class EngineChecker:
    """Check engine availability"""
    
    def __init__(self, db: VoiceDB):
        self.db = db
    
    def check(self, engine_id):
        """Check if an engine is available"""
        if engine_id not in ENGINES:
            return False, "Unknown engine"
        
        engine = ENGINES[engine_id]
        
        # Check if path exists
        if engine['path'] and not engine['path'].exists():
            self.db.update_engine_status(engine_id, False)
            return False, f"Path not found: {engine['path']}"
        
        # Check URL if available
        if engine['url']:
            try:
                r = requests.get(engine['url'], timeout=5)
                available = r.status_code < 500
                self.db.update_engine_status(engine_id, available)
                return available, "OK" if available else "Not responding"
            except:
                self.db.update_engine_status(engine_id, False)
                return False, "Connection failed"
        
        # For local libraries, just check path
        available = engine['path'] and engine['path'].exists()
        self.db.update_engine_status(engine_id, available)
        return available, "Available" if available else "Not installed"
    
    def check_all(self):
        """Check all engines"""
        results = {}
        for eid in ENGINES:
            available, message = self.check(eid)
            results[eid] = {
                "name": ENGINES[eid]['name'],
                "available": available,
                "message": message,
                "capabilities": ENGINES[eid]['capabilities'],
                "quality": ENGINES[eid]['quality'],
                "speed": ENGINES[eid]['speed']
            }
        return results
    
    def get_best_available(self, capability=None):
        """Get best available engine for a capability"""
        for eid, engine in sorted(ENGINES.items(), key=lambda x: x[1]['priority']):
            if capability and capability not in engine['capabilities']:
                continue
            
            available, _ = self.check(eid)
            if available:
                return eid
        return None


class VoiceGenerator:
    """Generate voice using available engines"""
    
    def __init__(self, db: VoiceDB, checker: EngineChecker):
        self.db = db
        self.checker = checker
    
    def generate(self, text, engine=None, character=None, emotion=None):
        """Generate voice audio"""
        # Auto-select engine if not specified
        if not engine:
            engine = self.checker.get_best_available("tts")
            if not engine:
                return None, "No voice engine available"
        
        # Log generation
        gen_id = self.db.log_generation(engine, text, character, emotion)
        
        try:
            # Get emotion parameters
            emotion_params = EMOTIONS.get(emotion, EMOTIONS['neutral'])
            
            # Get character profile
            voice_profile = VOICE_PROFILES.get(character, {})
            
            # Generate based on engine
            if engine == "gpt_sovits":
                result = self._generate_gpt_sovits(text, emotion_params, voice_profile)
            else:
                result = self._generate_fallback(engine, text, emotion_params)
            
            if result:
                output_path = OUTPUT_DIR / f"voice_{gen_id}_{datetime.now().strftime('%H%M%S')}.wav"
                
                # Save audio (result should be audio data or path)
                if isinstance(result, bytes):
                    output_path.write_bytes(result)
                elif isinstance(result, str) and Path(result).exists():
                    import shutil
                    shutil.copy2(result, output_path)
                else:
                    output_path = result
                
                self.db.update_generation(gen_id, 
                                         status="completed",
                                         output_path=str(output_path))
                self.db.increment_success(engine)
                
                return str(output_path), "Success"
            else:
                raise Exception("No audio generated")
                
        except Exception as e:
            self.db.update_generation(gen_id, status="failed", error=str(e))
            self.db.increment_error(engine)
            return None, str(e)
    
    def _generate_gpt_sovits(self, text, emotion_params, voice_profile):
        """Generate using GPT-SoVITS"""
        url = ENGINES['gpt_sovits']['url']
        
        params = {
            "text": text,
            "text_lang": "en",
            "speed": emotion_params.get('speed', 1.0)
        }
        
        try:
            response = requests.get(url, params=params, timeout=60)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"[VOICE] GPT-SoVITS error: {e}")
        
        return None
    
    def _generate_fallback(self, engine, text, emotion_params):
        """Fallback generation for other engines"""
        # Placeholder - would integrate with actual engines
        print(f"[VOICE] Using fallback for {engine}")
        return None
    
    def clone_voice(self, name, reference_audio, reference_text, engine="gpt_sovits"):
        """Clone a voice from reference audio"""
        if engine != "gpt_sovits":
            return False, "Voice cloning requires GPT-SoVITS"
        
        available, _ = self.checker.check(engine)
        if not available:
            return False, "GPT-SoVITS not available"
        
        # Store clone reference
        self.db.conn.execute('''
            INSERT OR REPLACE INTO voice_clones (name, reference_audio, reference_text, engine)
            VALUES (?, ?, ?, ?)
        ''', (name, reference_audio, reference_text, engine))
        self.db.conn.commit()
        
        return True, f"Voice clone '{name}' registered"


# Initialize components
db = VoiceDB()
checker = EngineChecker(db)
generator = VoiceGenerator(db, checker)


class VoiceToolsAPI(BaseHTTPRequestHandler):
    """Voice Tools Unified API"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/':
            self._json({
                'service': 'Voice Tools Unified',
                'version': '1.0',
                'port': PORT,
                'engines': list(ENGINES.keys()),
                'characters': list(VOICE_PROFILES.keys()),
                'emotions': list(EMOTIONS.keys())
            })
        
        elif path == '/api/status':
            engines = checker.check_all()
            stats = db.get_stats()
            
            available_count = sum(1 for e in engines.values() if e['available'])
            
            self._json({
                'engines': engines,
                'available_count': available_count,
                'total_engines': len(engines),
                'best_available': checker.get_best_available("tts"),
                **stats
            })
        
        elif path == '/api/engines':
            self._json({'engines': checker.check_all()})
        
        elif path == '/api/characters':
            self._json({'characters': VOICE_PROFILES})
        
        elif path == '/api/emotions':
            self._json({'emotions': EMOTIONS})
        
        elif path == '/api/generations':
            self._json({'generations': db.get_generations()})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/generate':
            text = data.get('text')
            if not text:
                self._json({'success': False, 'error': 'Text required'})
                return
            
            engine = data.get('engine')
            character = data.get('character')
            emotion = data.get('emotion', 'neutral')
            
            output_path, message = generator.generate(text, engine, character, emotion)
            
            self._json({
                'success': output_path is not None,
                'output_path': output_path,
                'message': message,
                'engine_used': engine or checker.get_best_available("tts")
            })
        
        elif path == '/api/clone':
            name = data.get('name')
            reference_audio = data.get('reference_audio')
            reference_text = data.get('reference_text')
            
            if not all([name, reference_audio]):
                self._json({'success': False, 'error': 'Name and reference_audio required'})
                return
            
            success, message = generator.clone_voice(name, reference_audio, reference_text)
            self._json({'success': success, 'message': message})
        
        elif path == '/api/narrate':
            # Narrate a story with multiple characters
            story = data.get('story', [])
            
            results = []
            for segment in story:
                text = segment.get('text')
                character = segment.get('character', 'narrator')
                emotion = segment.get('emotion', 'neutral')
                
                output_path, message = generator.generate(text, None, character, emotion)
                results.append({
                    'character': character,
                    'success': output_path is not None,
                    'output_path': output_path
                })
            
            self._json({
                'success': all(r['success'] for r in results),
                'segments': results
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  VOICE TOOLS UNIFIED")
    print("  Multi-Engine Voice Synthesis")
    print("=" * 60)
    
    # Check engines
    print("\nEngine Status:")
    for eid, result in checker.check_all().items():
        status = "✓ Available" if result['available'] else "✗ Not available"
        print(f"  [{status}] {result['name']} - {result['message']}")
    
    print(f"\nCharacters: {len(VOICE_PROFILES)}")
    print(f"Emotions: {len(EMOTIONS)}")
    
    stats = db.get_stats()
    print(f"\nTotal Generations: {stats['total_generations']}")
    print(f"Success Rate: {stats['success_rate']}%")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), VoiceToolsAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
