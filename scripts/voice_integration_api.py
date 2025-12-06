"""
VOICE INTEGRATION API
======================
Pipelines 17-20: Voice Cloning, Narration, Character Voice, Emotion Voice
Integrates GPT-SoVITS for voice synthesis.

Port: 8212
"""
import os
import sys
import json
import requests
import sqlite3
import wave
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
DATA_DIR = CIVITAI_PATH / "data"
VOICE_DIR = DATA_DIR / "voices"
OUTPUT_DIR = CIVITAI_PATH / "output" / "audio"
PROJECT_DIR = CIVITAI_PATH / "project"
DB_PATH = DATA_DIR / "voices.db"

# TTS API endpoints
GPT_SOVITS_URL = "http://127.0.0.1:9880"
GPT_SOVITS_PROJECT = PROJECT_DIR / "GPT-SoVITS-main" / "GPT-SoVITS-main"

# Ensure directories
VOICE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "stories").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "characters").mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
CORS(app)


# Voice profiles for Pipeline 19 (Character Voice)
CHARACTER_VOICES = {
    "narrator": {
        "name": "Narrator",
        "description": "Deep, authoritative voice for narration",
        "speed": 0.95,
        "emotion": "neutral"
    },
    "sheriff": {
        "name": "Sheriff",
        "description": "Gruff, commanding male voice",
        "speed": 0.85,
        "emotion": "stern"
    },
    "saloon_lady": {
        "name": "Saloon Lady",
        "description": "Sultry, confident female voice",
        "speed": 0.9,
        "emotion": "flirty"
    },
    "outlaw": {
        "name": "Outlaw",
        "description": "Rough, menacing voice",
        "speed": 0.8,
        "emotion": "threatening"
    },
    "native_chief": {
        "name": "Native Chief",
        "description": "Wise, measured voice",
        "speed": 0.75,
        "emotion": "wise"
    },
    "young_woman": {
        "name": "Young Woman",
        "description": "Bright, youthful female voice",
        "speed": 1.0,
        "emotion": "cheerful"
    },
    "old_timer": {
        "name": "Old Timer",
        "description": "Weathered, storytelling voice",
        "speed": 0.7,
        "emotion": "nostalgic"
    },
    "rancher": {
        "name": "Rancher",
        "description": "Solid, dependable male voice",
        "speed": 0.9,
        "emotion": "calm"
    }
}

# Emotion modifiers for Pipeline 20 (Emotion Voice)
EMOTION_MODIFIERS = {
    "neutral": {"speed": 1.0, "pitch": 0, "energy": 0.5},
    "happy": {"speed": 1.1, "pitch": 0.1, "energy": 0.8},
    "sad": {"speed": 0.85, "pitch": -0.1, "energy": 0.3},
    "angry": {"speed": 1.15, "pitch": 0.15, "energy": 0.9},
    "fearful": {"speed": 1.2, "pitch": 0.2, "energy": 0.7},
    "surprised": {"speed": 1.25, "pitch": 0.25, "energy": 0.85},
    "disgusted": {"speed": 0.9, "pitch": -0.05, "energy": 0.6},
    "stern": {"speed": 0.9, "pitch": -0.1, "energy": 0.7},
    "flirty": {"speed": 0.95, "pitch": 0.05, "energy": 0.65},
    "threatening": {"speed": 0.8, "pitch": -0.15, "energy": 0.75},
    "wise": {"speed": 0.75, "pitch": -0.1, "energy": 0.4},
    "cheerful": {"speed": 1.1, "pitch": 0.1, "energy": 0.75},
    "nostalgic": {"speed": 0.8, "pitch": -0.05, "energy": 0.45}
}


class VoiceDB:
    """Database for voice samples and generations"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS voice_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                character TEXT,
                reference_path TEXT,
                reference_text TEXT,
                language TEXT DEFAULT 'en',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline TEXT,
                text TEXT,
                character TEXT,
                emotion TEXT,
                output_path TEXT,
                duration_seconds REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS story_audio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                scene_number INTEGER,
                character TEXT,
                dialogue TEXT,
                emotion TEXT,
                audio_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS cloned_voices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                source_audio TEXT,
                source_text TEXT,
                quality_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()
    
    def add_voice_sample(self, name: str, character: str, ref_path: str, 
                         ref_text: str, language: str = 'en') -> int:
        cursor = self.conn.execute('''
            INSERT OR REPLACE INTO voice_samples 
            (name, character, reference_path, reference_text, language)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, character, ref_path, ref_text, language))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_voice_samples(self) -> List[Dict]:
        rows = self.conn.execute('SELECT * FROM voice_samples').fetchall()
        return [dict(r) for r in rows]
    
    def log_generation(self, pipeline: str, text: str, character: str,
                       emotion: str, output_path: str, duration: float):
        self.conn.execute('''
            INSERT INTO generations (pipeline, text, character, emotion, output_path, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (pipeline, text, character, emotion, output_path, duration))
        self.conn.commit()
    
    def get_stats(self) -> Dict:
        total_gens = self.conn.execute('SELECT COUNT(*) FROM generations').fetchone()[0]
        total_samples = self.conn.execute('SELECT COUNT(*) FROM voice_samples').fetchone()[0]
        total_stories = self.conn.execute('SELECT COUNT(DISTINCT story_id) FROM story_audio').fetchone()[0]
        
        by_pipeline = self.conn.execute('''
            SELECT pipeline, COUNT(*) as count FROM generations GROUP BY pipeline
        ''').fetchall()
        
        return {
            "total_generations": total_gens,
            "total_samples": total_samples,
            "total_stories": total_stories,
            "by_pipeline": {r[0]: r[1] for r in by_pipeline}
        }


db = VoiceDB()


class VoiceEngine:
    """Voice synthesis engine using GPT-SoVITS"""
    
    def __init__(self):
        self.gpt_sovits_available = self._check_gpt_sovits()
    
    def _check_gpt_sovits(self) -> bool:
        """Check if GPT-SoVITS is running"""
        try:
            resp = requests.get(f"{GPT_SOVITS_URL}/", timeout=2)
            return True
        except:
            return False
    
    def refresh_status(self):
        """Refresh GPT-SoVITS availability"""
        self.gpt_sovits_available = self._check_gpt_sovits()
        return self.gpt_sovits_available
    
    # ═══════════════════════════════════════════════════════════════
    # PIPELINE 17: Voice Cloning
    # ═══════════════════════════════════════════════════════════════
    
    def clone_voice(self, reference_audio: str, reference_text: str,
                    target_text: str, name: str = None,
                    language: str = "en") -> Dict:
        """Pipeline 17: Clone a voice from reference audio"""
        
        if not self.gpt_sovits_available:
            return {"success": False, "error": "GPT-SoVITS not running", "pipeline": "17_voice_clone"}
        
        try:
            # Generate with cloned voice
            params = {
                "refer_wav_path": reference_audio,
                "prompt_text": reference_text,
                "prompt_language": language,
                "text": target_text,
                "text_language": language
            }
            
            resp = requests.post(GPT_SOVITS_URL, json=params, timeout=120)
            
            if resp.status_code == 200:
                # Save audio
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                voice_name = name or f"cloned_{timestamp}"
                save_path = str(OUTPUT_DIR / "characters" / f"{voice_name}.wav")
                
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(resp.content)
                
                # Log
                db.log_generation("17_voice_clone", target_text, voice_name, 
                                  "cloned", save_path, len(resp.content) / 32000)
                
                # Save to cloned voices
                db.conn.execute('''
                    INSERT OR REPLACE INTO cloned_voices (name, source_audio, source_text)
                    VALUES (?, ?, ?)
                ''', (voice_name, reference_audio, reference_text))
                db.conn.commit()
                
                return {
                    "success": True,
                    "pipeline": "17_voice_clone",
                    "voice_name": voice_name,
                    "audio_path": save_path,
                    "text": target_text
                }
            else:
                return {"success": False, "error": resp.text, "pipeline": "17_voice_clone"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "pipeline": "17_voice_clone"}
    
    # ═══════════════════════════════════════════════════════════════
    # PIPELINE 18: Story Narration
    # ═══════════════════════════════════════════════════════════════
    
    def narrate_story(self, story_script: List[Dict], story_id: str = None) -> Dict:
        """Pipeline 18: Generate audio narration for a story"""
        
        if not story_id:
            story_id = datetime.now().strftime("story_%Y%m%d_%H%M%S")
        
        story_dir = OUTPUT_DIR / "stories" / story_id
        story_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        audio_files = []
        
        for i, scene in enumerate(story_script):
            text = scene.get('text', scene.get('dialogue', ''))
            character = scene.get('character', 'narrator')
            emotion = scene.get('emotion', 'neutral')
            
            if not text:
                continue
            
            # Get character voice settings
            char_config = CHARACTER_VOICES.get(character, CHARACTER_VOICES['narrator'])
            
            # Apply emotion
            emotion_mod = EMOTION_MODIFIERS.get(emotion, EMOTION_MODIFIERS['neutral'])
            speed = char_config['speed'] * emotion_mod['speed']
            
            # Generate audio
            audio_path = str(story_dir / f"{i:03d}_{character}.wav")
            
            result = self._generate_tts(text, speed, audio_path)
            result['scene'] = i
            result['character'] = character
            result['emotion'] = emotion
            
            if result.get('success'):
                audio_files.append(audio_path)
                
                # Log to database
                db.conn.execute('''
                    INSERT INTO story_audio (story_id, scene_number, character, dialogue, emotion, audio_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (story_id, i, character, text, emotion, audio_path))
                db.conn.commit()
            
            results.append(result)
        
        # Combine audio files
        combined_path = str(story_dir / "full_story.wav")
        self._combine_audio(audio_files, combined_path)
        
        db.log_generation("18_narration", f"Story: {story_id}", "narrator",
                          "story", combined_path, 0)
        
        return {
            "success": True,
            "pipeline": "18_narration",
            "story_id": story_id,
            "scenes": len(results),
            "successful": sum(1 for r in results if r.get('success')),
            "output_dir": str(story_dir),
            "combined_audio": combined_path,
            "results": results
        }
    
    # ═══════════════════════════════════════════════════════════════
    # PIPELINE 19: Character Voice
    # ═══════════════════════════════════════════════════════════════
    
    def generate_character_voice(self, text: str, character: str,
                                   save_path: str = None) -> Dict:
        """Pipeline 19: Generate speech with character voice"""
        
        char_config = CHARACTER_VOICES.get(character, CHARACTER_VOICES['narrator'])
        speed = char_config['speed']
        
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(OUTPUT_DIR / "characters" / f"{character}_{timestamp}.wav")
        
        result = self._generate_tts(text, speed, save_path)
        
        if result.get('success'):
            db.log_generation("19_character", text, character, 
                              char_config['emotion'], save_path, result.get('duration', 0))
        
        result['pipeline'] = "19_character"
        result['character'] = character
        result['character_info'] = char_config
        
        return result
    
    # ═══════════════════════════════════════════════════════════════
    # PIPELINE 20: Emotion Voice
    # ═══════════════════════════════════════════════════════════════
    
    def generate_emotion_voice(self, text: str, emotion: str,
                                character: str = "narrator",
                                save_path: str = None) -> Dict:
        """Pipeline 20: Generate speech with specific emotion"""
        
        char_config = CHARACTER_VOICES.get(character, CHARACTER_VOICES['narrator'])
        emotion_mod = EMOTION_MODIFIERS.get(emotion, EMOTION_MODIFIERS['neutral'])
        
        # Combine character speed with emotion modifier
        speed = char_config['speed'] * emotion_mod['speed']
        
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(OUTPUT_DIR / f"{emotion}_{character}_{timestamp}.wav")
        
        result = self._generate_tts(text, speed, save_path)
        
        if result.get('success'):
            db.log_generation("20_emotion", text, character, emotion, 
                              save_path, result.get('duration', 0))
        
        result['pipeline'] = "20_emotion"
        result['emotion'] = emotion
        result['emotion_settings'] = emotion_mod
        result['character'] = character
        
        return result
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def _generate_tts(self, text: str, speed: float = 1.0, 
                      save_path: str = None) -> Dict:
        """Core TTS generation"""
        
        if not self.gpt_sovits_available:
            # Return simulated response for testing
            return {
                "success": False,
                "error": "GPT-SoVITS not running. Start it on port 9880",
                "simulated": True
            }
        
        try:
            params = {
                "text": text,
                "text_language": "en",
                "speed": speed
            }
            
            resp = requests.post(GPT_SOVITS_URL, json=params, timeout=120)
            
            if resp.status_code == 200:
                if save_path:
                    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(resp.content)
                
                duration = len(resp.content) / 32000  # Estimate
                
                return {
                    "success": True,
                    "audio_path": save_path,
                    "duration": round(duration, 2),
                    "text": text
                }
            else:
                return {"success": False, "error": resp.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _combine_audio(self, audio_files: List[str], output_path: str):
        """Combine multiple WAV files"""
        if not audio_files:
            return
        
        try:
            combined_data = b''
            params = None
            
            for f in audio_files:
                if Path(f).exists():
                    with wave.open(f, 'rb') as w:
                        if params is None:
                            params = w.getparams()
                        combined_data += w.readframes(w.getnframes())
            
            if params and combined_data:
                with wave.open(output_path, 'wb') as out:
                    out.setparams(params)
                    out.writeframes(combined_data)
        except Exception as e:
            print(f"Audio combine error: {e}")


engine = VoiceEngine()


# ═══════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

# Pipeline 17: Voice Cloning
@app.route('/api/voice/clone', methods=['POST'])
def clone_voice():
    """Pipeline 17: Clone voice from reference"""
    data = request.json or {}
    
    required = ['reference_audio', 'reference_text', 'target_text']
    if not all(k in data for k in required):
        return jsonify({"success": False, "error": f"Required: {required}"}), 400
    
    return jsonify(engine.clone_voice(
        reference_audio=data['reference_audio'],
        reference_text=data['reference_text'],
        target_text=data['target_text'],
        name=data.get('name'),
        language=data.get('language', 'en')
    ))


# Pipeline 18: Story Narration
@app.route('/api/voice/narrate', methods=['POST'])
def narrate_story():
    """Pipeline 18: Narrate full story"""
    data = request.json or {}
    
    script = data.get('script', [])
    if not script:
        return jsonify({"success": False, "error": "No script provided"}), 400
    
    return jsonify(engine.narrate_story(
        story_script=script,
        story_id=data.get('story_id')
    ))


# Pipeline 19: Character Voice
@app.route('/api/voice/character', methods=['POST'])
def character_voice():
    """Pipeline 19: Generate character voice"""
    data = request.json or {}
    
    text = data.get('text', '')
    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400
    
    return jsonify(engine.generate_character_voice(
        text=text,
        character=data.get('character', 'narrator'),
        save_path=data.get('save_path')
    ))


# Pipeline 20: Emotion Voice
@app.route('/api/voice/emotion', methods=['POST'])
def emotion_voice():
    """Pipeline 20: Generate emotional voice"""
    data = request.json or {}
    
    text = data.get('text', '')
    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400
    
    return jsonify(engine.generate_emotion_voice(
        text=text,
        emotion=data.get('emotion', 'neutral'),
        character=data.get('character', 'narrator'),
        save_path=data.get('save_path')
    ))


# Utility Endpoints
@app.route('/api/voice/characters', methods=['GET'])
def list_characters():
    """List character voices"""
    return jsonify({
        "success": True,
        "characters": CHARACTER_VOICES
    })


@app.route('/api/voice/emotions', methods=['GET'])
def list_emotions():
    """List emotion modifiers"""
    return jsonify({
        "success": True,
        "emotions": EMOTION_MODIFIERS
    })


@app.route('/api/voice/samples', methods=['GET'])
def list_samples():
    """List voice samples"""
    return jsonify({
        "success": True,
        "samples": db.get_voice_samples()
    })


@app.route('/api/voice/stats', methods=['GET'])
def get_stats():
    """Get voice generation stats"""
    return jsonify({
        "success": True,
        **db.get_stats()
    })


@app.route('/api/voice/status', methods=['GET'])
def get_status():
    """Get TTS engine status"""
    engine.refresh_status()
    
    return jsonify({
        "success": True,
        "gpt_sovits": {
            "available": engine.gpt_sovits_available,
            "url": GPT_SOVITS_URL,
            "project_path": str(GPT_SOVITS_PROJECT)
        },
        "pipelines": {
            "17_voice_clone": "Clone voice from reference audio",
            "18_narration": "Generate story narration",
            "19_character": "Character-specific voices",
            "20_emotion": "Emotional voice synthesis"
        },
        "characters": list(CHARACTER_VOICES.keys()),
        "emotions": list(EMOTION_MODIFIERS.keys())
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "success": True,
        "service": "Voice Integration API",
        "version": "1.0.0",
        "port": 8212
    })


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "service": "Voice Integration API",
        "version": "1.0.0",
        "port": 8212,
        "description": "Pipelines 17-20: Voice Cloning, Narration, Character, Emotion",
        "tts_engine": {
            "name": "GPT-SoVITS",
            "available": engine.gpt_sovits_available,
            "url": GPT_SOVITS_URL
        },
        "pipelines": {
            "17": {"name": "Voice Clone", "endpoint": "POST /api/voice/clone"},
            "18": {"name": "Story Narration", "endpoint": "POST /api/voice/narrate"},
            "19": {"name": "Character Voice", "endpoint": "POST /api/voice/character"},
            "20": {"name": "Emotion Voice", "endpoint": "POST /api/voice/emotion"}
        },
        "characters": list(CHARACTER_VOICES.keys()),
        "emotions": list(EMOTION_MODIFIERS.keys())
    })


if __name__ == '__main__':
    print("=" * 70)
    print("  VOICE INTEGRATION API")
    print("  Pipelines 17-20: Voice Cloning, Narration, Character, Emotion")
    print("  Port: 8212")
    print("=" * 70)
    
    print(f"\n🎤 GPT-SoVITS: {'✅ Available' if engine.gpt_sovits_available else '❌ Not running'}")
    print(f"   URL: {GPT_SOVITS_URL}")
    
    print("\n📡 Pipelines:")
    print("    [17] POST /api/voice/clone     - Clone voice from reference")
    print("    [18] POST /api/voice/narrate   - Narrate full story")
    print("    [19] POST /api/voice/character - Character voice")
    print("    [20] POST /api/voice/emotion   - Emotional voice")
    
    print("\n🎭 Characters:", ", ".join(CHARACTER_VOICES.keys()))
    print("😊 Emotions:", ", ".join(EMOTION_MODIFIERS.keys()))
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=8212, debug=False)
