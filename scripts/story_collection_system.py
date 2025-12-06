"""
Story Collection System
- Parse stories (100k-2.5M words)
- Generate 500+ images per collection
- Western, Tribal, Native American themes
- Automatic scene extraction

Port: 8226
"""
import sqlite3
import json
import re
import random
import requests
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

PORT = 8226
DB_PATH = Path(r"c:\Users\Admin\civitai\data\advanced_learning.db")
STORIES_DIR = Path(r"c:\Users\Admin\civitai\data\stories")
STORIES_DIR.mkdir(exist_ok=True)

# Theme configurations
THEMES = {
    "western": {
        "name": "Western",
        "characters": {
            "cowboys": ["cowboy", "rancher", "outlaw", "sheriff", "deputy", "gunslinger", "marshal"],
            "women": ["saloon girl", "pioneer woman", "rancher's wife", "native woman", "outlaw woman"],
            "folk": ["blacksmith", "bartender", "merchant", "preacher", "doctor"]
        },
        "settings": ["saloon", "desert", "ranch", "canyon", "frontier town", "campfire", "stable", "sunset prairie"],
        "clothing": {
            "dressed": ["cowboy hat", "leather vest", "boots", "bandana", "chaps", "duster coat", "flannel shirt"],
            "partial": ["open shirt", "suspenders only", "bathing scene", "sleeping attire"],
            "undressed": ["nude bathing", "intimate scene", "private moment"]
        },
        "style_tags": ["western aesthetic", "wild west", "frontier style", "dusty atmosphere", "golden hour lighting"]
    },
    "tribal": {
        "name": "Tribal",
        "characters": {
            "warriors": ["tribal warrior", "hunter", "chief", "shaman", "scout"],
            "women": ["tribal woman", "priestess", "healer", "dancer", "maiden"],
            "elders": ["elder", "wise woman", "storyteller"]
        },
        "settings": ["jungle", "cave", "waterfall", "sacred grove", "tribal village", "river bank", "ancient temple"],
        "clothing": {
            "dressed": ["tribal attire", "ceremonial dress", "hunting gear", "feather headdress", "bone jewelry"],
            "partial": ["minimal clothing", "ritual attire", "body paint only"],
            "undressed": ["nude ritual", "bathing ceremony", "intimate moment"]
        },
        "style_tags": ["tribal aesthetic", "primal beauty", "exotic", "ceremonial", "dramatic lighting"]
    },
    "native_american": {
        "name": "Native American",
        "tribes": {
            "plains": ["Sioux", "Cheyenne", "Comanche", "Blackfoot", "Crow", "Arapaho"],
            "southwest": ["Apache", "Navajo", "Hopi", "Pueblo", "Zuni"],
            "eastern": ["Cherokee", "Iroquois", "Mohawk", "Seminole", "Creek"],
            "northwest": ["Nez Perce", "Chinook", "Haida", "Tlingit"],
            "california": ["Chumash", "Miwok", "Pomo", "Yurok"]
        },
        "characters": {
            "warriors": ["brave", "war chief", "scout", "hunter"],
            "women": ["native woman", "medicine woman", "chief's daughter", "weaver", "gatherer"],
            "spiritual": ["shaman", "medicine man", "spirit walker", "vision seeker"]
        },
        "settings": ["teepee camp", "prairie", "sacred mountain", "river crossing", "hunting grounds", "council fire"],
        "clothing": {
            "dressed": ["buckskin dress", "war bonnet", "moccasins", "beaded regalia", "buffalo robe"],
            "partial": ["summer attire", "ceremonial paint", "spirit dance attire"],
            "undressed": ["sweat lodge", "vision quest", "private moment"]
        },
        "style_tags": ["native american aesthetic", "spiritual", "connection to nature", "dignified", "proud"]
    }
}


class StoryCollectionSystem:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._ensure_tables()
        
    def _ensure_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS story_collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_name TEXT,
            theme TEXT,
            story_hash TEXT,
            total_scenes INTEGER DEFAULT 0,
            images_generated INTEGER DEFAULT 0,
            target_images INTEGER DEFAULT 500,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )''')
        
        # Add missing columns to existing tables
        for col in ['story_hash TEXT', 'status TEXT DEFAULT "pending"']:
            try: cursor.execute(f'ALTER TABLE story_collections ADD COLUMN {col}')
            except: pass
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS story_scenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_id INTEGER,
            scene_number INTEGER,
            scene_text TEXT,
            extracted_elements TEXT,
            prompt TEXT,
            images_generated INTEGER DEFAULT 0,
            FOREIGN KEY (collection_id) REFERENCES story_collections(id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS collection_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_id INTEGER,
            scene_id INTEGER,
            image_id TEXT,
            rating REAL DEFAULT 0,
            FOREIGN KEY (collection_id) REFERENCES story_collections(id)
        )''')
        
        self.conn.commit()
        
    # ==================== STORY PARSING ====================
    
    def create_collection(self, name: str, theme: str, story_text: str = None, 
                         story_path: str = None, target_images: int = 500) -> dict:
        """Create new story collection"""
        
        # Load story
        if story_path:
            with open(story_path, 'r', encoding='utf-8') as f:
                story_text = f.read()
        elif not story_text:
            return {'error': 'No story provided'}
            
        word_count = len(story_text.split())
        story_hash = str(hash(story_text[:1000]))[:8]
        
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO story_collections 
            (collection_name, theme, story_hash, target_images, created_at)
            VALUES (?, ?, ?, ?, ?)''',
            (name, theme, story_hash, target_images, datetime.now().isoformat()))
        collection_id = cursor.lastrowid
        self.conn.commit()
        
        # Parse scenes
        scenes = self._parse_story(story_text, theme)
        
        # Store scenes
        for i, scene in enumerate(scenes):
            cursor.execute('''INSERT INTO story_scenes 
                (collection_id, scene_number, scene_text, extracted_elements, prompt)
                VALUES (?, ?, ?, ?, ?)''',
                (collection_id, i+1, scene['text'][:500], 
                 json.dumps(scene['elements']), scene['prompt']))
                 
        cursor.execute('UPDATE story_collections SET total_scenes = ? WHERE id = ?',
                      (len(scenes), collection_id))
        self.conn.commit()
        
        return {
            'collection_id': collection_id,
            'name': name,
            'theme': theme,
            'word_count': word_count,
            'scenes_extracted': len(scenes),
            'target_images': target_images
        }
        
    def _parse_story(self, text: str, theme: str) -> list:
        """Parse story into scenes"""
        scenes = []
        theme_config = THEMES.get(theme, THEMES['tribal'])
        
        # Split by paragraphs/scenes
        paragraphs = re.split(r'\n\n+', text)
        
        # Group paragraphs into scenes
        current_scene = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            current_scene.append(para)
            
            # Check for scene break indicators
            if any(indicator in para.lower() for indicator in 
                   ['chapter', 'scene', '***', '---', 'later that', 'the next']):
                if current_scene:
                    scene_text = ' '.join(current_scene)
                    elements = self._extract_elements(scene_text, theme_config)
                    prompt = self._build_prompt(elements, theme_config)
                    scenes.append({
                        'text': scene_text,
                        'elements': elements,
                        'prompt': prompt
                    })
                    current_scene = []
                    
            # Also break on long scenes
            if len(current_scene) >= 5:
                scene_text = ' '.join(current_scene)
                elements = self._extract_elements(scene_text, theme_config)
                prompt = self._build_prompt(elements, theme_config)
                scenes.append({
                    'text': scene_text,
                    'elements': elements,
                    'prompt': prompt
                })
                current_scene = []
                
        # Don't forget last scene
        if current_scene:
            scene_text = ' '.join(current_scene)
            elements = self._extract_elements(scene_text, theme_config)
            prompt = self._build_prompt(elements, theme_config)
            scenes.append({
                'text': scene_text,
                'elements': elements,
                'prompt': prompt
            })
            
        return scenes
        
    def _extract_elements(self, text: str, theme_config: dict) -> dict:
        """Extract visual elements from scene text"""
        text_lower = text.lower()
        elements = {
            'characters': [],
            'setting': None,
            'clothing': 'dressed',
            'mood': 'neutral',
            'time': 'day'
        }
        
        # Find characters
        for char_type, chars in theme_config.get('characters', {}).items():
            for char in chars:
                if char in text_lower:
                    elements['characters'].append(char)
                    
        # Find setting
        for setting in theme_config.get('settings', []):
            if setting in text_lower:
                elements['setting'] = setting
                break
                
        # Determine clothing level
        clothing_keywords = {
            'undressed': ['nude', 'naked', 'bare', 'unclothed', 'intimate', 'passion'],
            'partial': ['bathing', 'undress', 'revealing', 'minimal', 'barely'],
            'dressed': ['dressed', 'wearing', 'clothed', 'outfit']
        }
        
        for level, keywords in clothing_keywords.items():
            if any(kw in text_lower for kw in keywords):
                elements['clothing'] = level
                break
                
        # Mood detection
        mood_keywords = {
            'dramatic': ['battle', 'fight', 'war', 'attack', 'death', 'danger'],
            'romantic': ['love', 'kiss', 'embrace', 'tender', 'passion'],
            'peaceful': ['calm', 'peaceful', 'serene', 'quiet', 'rest'],
            'mysterious': ['secret', 'hidden', 'ancient', 'mystery', 'ritual']
        }
        
        for mood, keywords in mood_keywords.items():
            if any(kw in text_lower for kw in keywords):
                elements['mood'] = mood
                break
                
        # Time of day
        if any(t in text_lower for t in ['night', 'moon', 'stars', 'dark']):
            elements['time'] = 'night'
        elif any(t in text_lower for t in ['sunset', 'dusk', 'evening']):
            elements['time'] = 'sunset'
        elif any(t in text_lower for t in ['dawn', 'sunrise', 'morning']):
            elements['time'] = 'dawn'
            
        return elements
        
    def _build_prompt(self, elements: dict, theme_config: dict) -> str:
        """Build image prompt from extracted elements"""
        parts = ["masterpiece", "best quality", "ultra detailed", "8k resolution",
                 "photorealistic", "RAW photo", "sharp focus"]
        
        # Add theme style
        parts.extend(theme_config.get('style_tags', []))
        
        # Add characters
        if elements['characters']:
            char = random.choice(elements['characters'])
            parts.append(f"({char}:1.3)")
        else:
            # Default character
            char_types = list(theme_config.get('characters', {}).values())
            if char_types:
                chars = random.choice(char_types)
                if chars:
                    parts.append(f"({random.choice(chars)}:1.3)")
                    
        # Add body details
        parts.extend([
            "(adult woman:1.3)", 
            random.choice(["petite", "slim", "athletic", "toned"]),
            random.choice(["A cup", "B cup", "small bust"]),
            random.choice(["perky", "firm", "natural"])
        ])
        
        # Add setting
        if elements['setting']:
            parts.append(f"({elements['setting']}:1.2)")
        else:
            settings = theme_config.get('settings', ['outdoor'])
            parts.append(f"({random.choice(settings)}:1.2)")
            
        # Add clothing
        clothing_level = elements['clothing']
        clothing_options = theme_config.get('clothing', {}).get(clothing_level, [])
        if clothing_options:
            parts.append(random.choice(clothing_options))
            
        # Add mood lighting
        mood_lighting = {
            'dramatic': 'dramatic lighting, high contrast',
            'romantic': 'soft lighting, warm tones',
            'peaceful': 'natural lighting, soft shadows',
            'mysterious': 'moody lighting, atmospheric'
        }
        parts.append(mood_lighting.get(elements['mood'], 'natural lighting'))
        
        # Time of day
        time_lighting = {
            'night': 'moonlight, night scene',
            'sunset': 'golden hour, sunset colors',
            'dawn': 'dawn lighting, soft morning light',
            'day': 'daylight, clear lighting'
        }
        parts.append(time_lighting.get(elements['time'], 'daylight'))
        
        return ", ".join(parts)
        
    # ==================== GENERATION ====================
    
    def get_collection_status(self, collection_id: int) -> dict:
        cursor = self.conn.cursor()
        cursor.execute('''SELECT collection_name, theme, total_scenes, 
            images_generated, target_images, status FROM story_collections WHERE id = ?''',
            (collection_id,))
        result = cursor.fetchone()
        
        if not result:
            return {'error': 'Collection not found'}
            
        return {
            'name': result[0],
            'theme': result[1],
            'scenes': result[2],
            'images_generated': result[3],
            'target': result[4],
            'status': result[5],
            'progress': round((result[3] / result[4]) * 100, 1) if result[4] else 0
        }
        
    def get_next_scene_prompt(self, collection_id: int) -> dict:
        """Get next scene to generate"""
        cursor = self.conn.cursor()
        cursor.execute('''SELECT id, scene_number, prompt, extracted_elements 
            FROM story_scenes 
            WHERE collection_id = ? AND images_generated < 5
            ORDER BY scene_number
            LIMIT 1''', (collection_id,))
        result = cursor.fetchone()
        
        if not result:
            return {'status': 'complete', 'message': 'All scenes generated'}
            
        return {
            'scene_id': result[0],
            'scene_number': result[1],
            'prompt': result[2],
            'elements': json.loads(result[3])
        }
        
    def close(self):
        self.conn.close()


# ==================== THEME BROWSER ====================
def list_themes():
    """List all available themes"""
    print("\n📚 AVAILABLE THEMES:\n")
    
    for theme_key, theme in THEMES.items():
        print(f"🎬 {theme['name'].upper()}")
        print(f"   Key: {theme_key}")
        
        if 'tribes' in theme:
            print(f"   Tribes: {sum(len(v) for v in theme['tribes'].values())} total")
            for region, tribes in theme['tribes'].items():
                print(f"      {region}: {', '.join(tribes[:3])}...")
                
        if 'characters' in theme:
            total_chars = sum(len(v) for v in theme['characters'].values())
            print(f"   Characters: {total_chars} types")
            
        print(f"   Settings: {len(theme.get('settings', []))} options")
        print(f"   Clothing levels: dressed, partial, undressed")
        print()


# ==================== TEST ====================
def test_system():
    print("="*60)
    print("  STORY COLLECTION SYSTEM TEST")
    print("="*60)
    
    list_themes()
    
    scs = StoryCollectionSystem()
    
    # Test story
    test_story = """
    Chapter 1: The Warrior's Dawn
    
    The sun rose over the prairie as Running Wolf prepared for the hunt.
    His muscular form silhouetted against the golden horizon.
    
    ***
    
    Later that morning, he encountered a beautiful woman bathing in the river.
    She was the chief's daughter, known for her striking features and grace.
    
    ---
    
    That night, the tribal council gathered around the sacred fire.
    The shaman performed an ancient ritual under the moonlight.
    The drums echoed through the canyon as dancers moved in ceremony.
    """
    
    print("\n📝 Creating test collection...")
    result = scs.create_collection(
        name="Test Native Story",
        theme="native_american",
        story_text=test_story,
        target_images=50
    )
    
    print(f"   Collection ID: {result['collection_id']}")
    print(f"   Scenes extracted: {result['scenes_extracted']}")
    print(f"   Target images: {result['target_images']}")
    
    # Get first scene
    print("\n📸 First scene prompt:")
    scene = scs.get_next_scene_prompt(result['collection_id'])
    print(f"   Scene {scene['scene_number']}:")
    print(f"   {scene['prompt'][:100]}...")
    
    print("\n✅ Story Collection System operational!")
    
    scs.close()


# ==================== HTTP API ====================

# Global system instance
scs = None

def get_system():
    global scs
    if scs is None:
        scs = StoryCollectionSystem()
    return scs


class StoryCollectionAPI(BaseHTTPRequestHandler):
    """HTTP API for Story Collection System"""
    
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
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        system = get_system()
        
        if path == '/':
            # Service info and stats
            cursor = system.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM story_collections')
            total_collections = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM story_scenes')
            total_scenes = cursor.fetchone()[0]
            cursor.execute('SELECT SUM(images_generated) FROM story_collections')
            total_images = cursor.fetchone()[0] or 0
            
            self._json({
                'service': 'Story Collection System',
                'version': '1.0',
                'port': PORT,
                'stats': {
                    'collections': total_collections,
                    'scenes': total_scenes,
                    'images_generated': total_images
                },
                'themes': list(THEMES.keys())
            })
        
        elif path == '/api/themes':
            # List available themes
            themes_info = {}
            for key, theme in THEMES.items():
                themes_info[key] = {
                    'name': theme['name'],
                    'settings': theme.get('settings', []),
                    'character_types': list(theme.get('characters', {}).keys()),
                    'style_tags': theme.get('style_tags', [])
                }
                if 'tribes' in theme:
                    themes_info[key]['tribes'] = {
                        region: tribes for region, tribes in theme['tribes'].items()
                    }
            self._json({'themes': themes_info})
        
        elif path == '/api/collections':
            # List all collections
            cursor = system.conn.cursor()
            cursor.execute('''SELECT id, collection_name, theme, total_scenes, 
                images_generated, target_images, status, created_at 
                FROM story_collections ORDER BY created_at DESC''')
            collections = [{
                'id': r[0], 'name': r[1], 'theme': r[2], 
                'scenes': r[3], 'images_generated': r[4], 
                'target': r[5], 'status': r[6], 'created_at': r[7],
                'progress': round((r[4] / r[5]) * 100, 1) if r[5] else 0
            } for r in cursor.fetchall()]
            self._json({'collections': collections, 'count': len(collections)})
        
        elif path.startswith('/api/collection/'):
            # Get specific collection
            try:
                collection_id = int(path.split('/')[-1])
                status = system.get_collection_status(collection_id)
                
                if 'error' in status:
                    self._json(status, 404)
                else:
                    # Add scenes
                    cursor = system.conn.cursor()
                    cursor.execute('''SELECT id, scene_number, scene_text, prompt, images_generated
                        FROM story_scenes WHERE collection_id = ? ORDER BY scene_number''', (collection_id,))
                    scenes = [{
                        'id': r[0], 'scene_number': r[1], 
                        'text': r[2][:200] + '...' if len(r[2]) > 200 else r[2],
                        'prompt': r[3][:150] + '...' if len(r[3]) > 150 else r[3],
                        'images_generated': r[4]
                    } for r in cursor.fetchall()]
                    status['scenes'] = scenes
                    self._json(status)
            except ValueError:
                self._json({'error': 'Invalid collection ID'}, 400)
        
        elif path == '/api/next':
            # Get next scene to generate
            collection_id = params.get('collection', [None])[0]
            if collection_id:
                scene = system.get_next_scene_prompt(int(collection_id))
                self._json(scene)
            else:
                # Find collection with pending work
                cursor = system.conn.cursor()
                cursor.execute('''SELECT id FROM story_collections 
                    WHERE images_generated < target_images 
                    ORDER BY created_at DESC LIMIT 1''')
                result = cursor.fetchone()
                if result:
                    scene = system.get_next_scene_prompt(result[0])
                    scene['collection_id'] = result[0]
                    self._json(scene)
                else:
                    self._json({'status': 'idle', 'message': 'No pending work'})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        system = get_system()
        
        if path == '/api/collection/create':
            # Create new collection
            name = data.get('name')
            theme = data.get('theme', 'tribal')
            story_text = data.get('story_text')
            story_path = data.get('story_path')
            target_images = data.get('target_images', 500)
            
            if not name:
                self._json({'success': False, 'error': 'name required'})
                return
            
            if not story_text and not story_path:
                self._json({'success': False, 'error': 'story_text or story_path required'})
                return
            
            result = system.create_collection(
                name=name,
                theme=theme,
                story_text=story_text,
                story_path=story_path,
                target_images=target_images
            )
            
            if 'error' in result:
                self._json({'success': False, **result})
            else:
                self._json({'success': True, **result})
        
        elif path == '/api/scene/complete':
            # Mark scene as having an image generated
            scene_id = data.get('scene_id')
            image_id = data.get('image_id')
            collection_id = data.get('collection_id')
            
            if not scene_id:
                self._json({'success': False, 'error': 'scene_id required'})
                return
            
            cursor = system.conn.cursor()
            
            # Update scene count
            cursor.execute('UPDATE story_scenes SET images_generated = images_generated + 1 WHERE id = ?', (scene_id,))
            
            # Get collection_id if not provided
            if not collection_id:
                cursor.execute('SELECT collection_id FROM story_scenes WHERE id = ?', (scene_id,))
                result = cursor.fetchone()
                collection_id = result[0] if result else None
            
            # Update collection count
            if collection_id:
                cursor.execute('UPDATE story_collections SET images_generated = images_generated + 1 WHERE id = ?', (collection_id,))
                
                # Record the image
                if image_id:
                    cursor.execute('''INSERT INTO collection_images (collection_id, scene_id, image_id)
                        VALUES (?, ?, ?)''', (collection_id, scene_id, image_id))
            
            system.conn.commit()
            self._json({'success': True, 'scene_id': scene_id, 'image_id': image_id})
        
        elif path == '/api/generate':
            # Generate images for a collection (integration with workflow manager)
            collection_id = data.get('collection_id')
            count = data.get('count', 1)
            
            if not collection_id:
                self._json({'success': False, 'error': 'collection_id required'})
                return
            
            generated = []
            for _ in range(count):
                scene = system.get_next_scene_prompt(collection_id)
                if scene.get('status') == 'complete':
                    break
                
                # Try to call workflow manager
                try:
                    response = requests.post(
                        'http://127.0.0.1:8221/api/run',
                        json={
                            'workflow': 'tribal_generator',
                            'prompt': scene.get('prompt', ''),
                            'overrides': {}
                        },
                        timeout=60
                    )
                    if response.ok:
                        result = response.json()
                        # Mark scene as complete
                        cursor = system.conn.cursor()
                        cursor.execute('UPDATE story_scenes SET images_generated = images_generated + 1 WHERE id = ?', 
                                      (scene['scene_id'],))
                        cursor.execute('UPDATE story_collections SET images_generated = images_generated + 1 WHERE id = ?',
                                      (collection_id,))
                        system.conn.commit()
                        
                        generated.append({
                            'scene_id': scene['scene_id'],
                            'scene_number': scene['scene_number'],
                            'result': result
                        })
                except Exception as e:
                    generated.append({
                        'scene_id': scene.get('scene_id'),
                        'error': str(e)
                    })
            
            self._json({
                'success': True,
                'collection_id': collection_id,
                'generated': generated,
                'count': len(generated)
            })
        
        elif path == '/api/collection/delete':
            # Delete a collection
            collection_id = data.get('collection_id')
            if not collection_id:
                self._json({'success': False, 'error': 'collection_id required'})
                return
            
            cursor = system.conn.cursor()
            cursor.execute('DELETE FROM collection_images WHERE collection_id = ?', (collection_id,))
            cursor.execute('DELETE FROM story_scenes WHERE collection_id = ?', (collection_id,))
            cursor.execute('DELETE FROM story_collections WHERE id = ?', (collection_id,))
            system.conn.commit()
            
            self._json({'success': True, 'deleted': collection_id})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  STORY COLLECTION SYSTEM API")
    print("  Port:", PORT)
    print("=" * 60)
    
    system = get_system()
    
    # Get stats
    cursor = system.conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM story_collections')
    collections = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM story_scenes')
    scenes = cursor.fetchone()[0]
    
    print(f"\nDatabase Stats:")
    print(f"  Collections: {collections}")
    print(f"  Scenes: {scenes}")
    print(f"  Themes: {', '.join(THEMES.keys())}")
    
    print(f"\nEndpoints:")
    print(f"  GET  /                     - Service info")
    print(f"  GET  /api/themes           - List themes")
    print(f"  GET  /api/collections      - List collections")
    print(f"  GET  /api/collection/:id   - Get collection details")
    print(f"  GET  /api/next             - Get next scene to generate")
    print(f"  POST /api/collection/create - Create collection")
    print(f"  POST /api/scene/complete   - Mark scene generated")
    print(f"  POST /api/generate         - Generate images")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), StoryCollectionAPI)
    server.serve_forever()


if __name__ == "__main__":
    main()
