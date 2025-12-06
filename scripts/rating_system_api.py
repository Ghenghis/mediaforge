"""
COMPREHENSIVE RATING SYSTEM API
================================
22-Level Rating System with Auto-Tagging
Supports EL to EXTREME ratings with strict guardrails

Port: 8198
"""
import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import hashlib

# Configuration
PORT = 8198
DB_PATH = Path(r"c:\Users\Admin\civitai\data\rating_system.db")
RATINGS_PATH = Path(r"c:\Users\Admin\civitai\data\comprehensive_ratings.json")

# Load ratings configuration
try:
    with open(RATINGS_PATH) as f:
        RATINGS_CONFIG = json.load(f)
except:
    RATINGS_CONFIG = {"ratings": {}, "guardrails": {}}

RATINGS = RATINGS_CONFIG.get("ratings", {})
GUARDRAILS = RATINGS_CONFIG.get("guardrails", {})
CATEGORIES = RATINGS_CONFIG.get("rating_categories", {})
AUTO_TAG_CONFIG = RATINGS_CONFIG.get("auto_tagging", {})


class RatingDB:
    """Database for rating system"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        self.conn.executescript('''
            -- Content ratings lookup
            CREATE TABLE IF NOT EXISTS content_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                full_name TEXT,
                category TEXT NOT NULL,
                min_age INTEGER NOT NULL,
                max_age INTEGER,
                clothing_coverage_min INTEGER NOT NULL,
                transparency_allowed INTEGER DEFAULT 0,
                nudity_allowed INTEGER DEFAULT 0,
                explicit_allowed INTEGER DEFAULT 0,
                guardrail_level INTEGER NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Auto-tagging results
            CREATE TABLE IF NOT EXISTS auto_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT NOT NULL,
                image_path TEXT,
                detected_rating TEXT,
                confidence REAL DEFAULT 0,
                clothing_coverage REAL,
                skin_visibility REAL,
                detected_keywords TEXT,
                suggested_tags TEXT,
                grey_areas TEXT,
                violations TEXT,
                auto_corrected INTEGER DEFAULT 0,
                reviewed INTEGER DEFAULT 0,
                reviewer_id TEXT,
                final_rating TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT
            );
            
            -- Guardrail violations log
            CREATE TABLE IF NOT EXISTS guardrail_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT,
                prompt TEXT,
                violation_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                expected_rating TEXT,
                detected_rating TEXT,
                blocked_keywords TEXT,
                details TEXT,
                auto_corrected INTEGER DEFAULT 0,
                admin_reviewed INTEGER DEFAULT 0,
                admin_action TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT
            );
            
            -- Age verification sessions
            CREATE TABLE IF NOT EXISTS age_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                verified_age INTEGER NOT NULL,
                verification_method TEXT,
                max_rating_allowed TEXT,
                restrictions_released INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            );
            
            -- Rating history
            CREATE TABLE IF NOT EXISTS rating_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT NOT NULL,
                old_rating TEXT,
                new_rating TEXT NOT NULL,
                change_reason TEXT,
                changed_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Populate ratings if empty
        existing = self.conn.execute('SELECT COUNT(*) FROM content_ratings').fetchone()[0]
        if existing == 0:
            self._populate_ratings()
        
        self.conn.commit()
    
    def _populate_ratings(self):
        """Populate ratings table from config"""
        for code, data in RATINGS.items():
            self.conn.execute('''
                INSERT OR REPLACE INTO content_ratings 
                (code, name, full_name, category, min_age, max_age, 
                 clothing_coverage_min, transparency_allowed, nudity_allowed,
                 explicit_allowed, guardrail_level, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                code, data.get('name'), data.get('full_name'),
                data.get('category'), data.get('min_age'), data.get('max_age'),
                data.get('clothing_coverage_min', 100),
                1 if data.get('transparency_allowed') else 0,
                1 if data.get('nudity_allowed') else 0,
                1 if data.get('explicit_allowed') else 0,
                data.get('guardrail_level', 1),
                data.get('description')
            ))
    
    def get_all_ratings(self):
        """Get all ratings"""
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM content_ratings ORDER BY min_age, guardrail_level').fetchall()]
    
    def get_rating(self, code):
        """Get specific rating"""
        row = self.conn.execute(
            'SELECT * FROM content_ratings WHERE code = ?', (code,)).fetchone()
        return dict(row) if row else None
    
    def get_ratings_by_category(self, category):
        """Get ratings by category"""
        return [dict(r) for r in self.conn.execute(
            'SELECT * FROM content_ratings WHERE category = ? ORDER BY min_age',
            (category,)).fetchall()]
    
    def get_stats(self):
        """Get system statistics"""
        total_ratings = self.conn.execute('SELECT COUNT(*) FROM content_ratings').fetchone()[0]
        total_tags = self.conn.execute('SELECT COUNT(*) FROM auto_tags').fetchone()[0]
        violations = self.conn.execute('SELECT COUNT(*) FROM guardrail_violations').fetchone()[0]
        pending_review = self.conn.execute(
            'SELECT COUNT(*) FROM auto_tags WHERE reviewed = 0').fetchone()[0]
        
        return {
            'total_ratings': total_ratings,
            'images_tagged': total_tags,
            'violations_logged': violations,
            'pending_review': pending_review
        }
    
    def log_auto_tag(self, image_id, image_path, detected_rating, confidence,
                     clothing_coverage, keywords, grey_areas, violations):
        """Log auto-tagging result"""
        self.conn.execute('''
            INSERT INTO auto_tags 
            (image_id, image_path, detected_rating, confidence, clothing_coverage,
             detected_keywords, grey_areas, violations, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            image_id, image_path, detected_rating, confidence, clothing_coverage,
            json.dumps(keywords), json.dumps(grey_areas), json.dumps(violations),
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def log_violation(self, image_id, prompt, violation_type, severity,
                      expected_rating, detected_rating, blocked_keywords, details):
        """Log guardrail violation"""
        self.conn.execute('''
            INSERT INTO guardrail_violations
            (image_id, prompt, violation_type, severity, expected_rating,
             detected_rating, blocked_keywords, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            image_id, prompt, violation_type, severity, expected_rating,
            detected_rating, json.dumps(blocked_keywords), details,
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def verify_age(self, session_id, age, method='self_declared'):
        """Verify age and create session"""
        # Calculate max allowed rating based on age
        if age < 13:
            max_rating = 'PG'
        elif age < 14:
            max_rating = 'PG-13'
        elif age < 15:
            max_rating = 'NC-14'
        elif age < 16:
            max_rating = 'NC-15'
        elif age < 17:
            max_rating = 'NC-16'
        elif age < 18:
            max_rating = 'NC-17'
        elif age < 19:
            max_rating = 'NC-18'
        elif age < 20:
            max_rating = 'NC-19'
        elif age < 21:
            max_rating = 'NC-20'
        else:
            max_rating = 'EXTREME'  # Full access at 21+
        
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        
        self.conn.execute('''
            INSERT OR REPLACE INTO age_verifications
            (session_id, verified_age, verification_method, max_rating_allowed,
             created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, age, method, max_rating, datetime.now().isoformat(), expires))
        self.conn.commit()
        
        return {
            'session_id': session_id,
            'verified_age': age,
            'max_rating_allowed': max_rating,
            'expires_at': expires
        }
    
    def release_restrictions(self, session_id):
        """Release adult restrictions for verified 21+ users"""
        session = self.conn.execute(
            'SELECT * FROM age_verifications WHERE session_id = ?',
            (session_id,)).fetchone()
        
        if not session:
            return {'error': 'Session not found'}
        
        if session['verified_age'] < 21:
            return {'error': 'Must be 21+ to release restrictions'}
        
        self.conn.execute('''
            UPDATE age_verifications SET restrictions_released = 1
            WHERE session_id = ?
        ''', (session_id,))
        self.conn.commit()
        
        return {
            'session_id': session_id,
            'restrictions_released': True,
            'max_rating_allowed': 'EXTREME'
        }
    
    def get_session(self, session_id):
        """Get session info"""
        row = self.conn.execute(
            'SELECT * FROM age_verifications WHERE session_id = ?',
            (session_id,)).fetchone()
        return dict(row) if row else None


class AutoTagger:
    """Auto-tagging engine for content rating"""
    
    def __init__(self, config=AUTO_TAG_CONFIG):
        self.config = config
        self.family_keywords = config.get('content_keywords', {}).get('family_safe', [])
        self.teen_keywords = config.get('content_keywords', {}).get('teen', [])
        self.adult_soft_keywords = config.get('content_keywords', {}).get('adult_soft', [])
        self.adult_explicit_keywords = config.get('content_keywords', {}).get('adult_explicit', [])
        self.always_block = config.get('auto_block_keywords', {}).get('always_block', [])
        self.family_block = config.get('auto_block_keywords', {}).get('family_block', [])
        self.teen_block = config.get('auto_block_keywords', {}).get('teen_block', [])
    
    def analyze_prompt(self, prompt, target_rating=None):
        """Analyze prompt and suggest rating"""
        prompt_lower = prompt.lower()
        
        detected_keywords = []
        violations = []
        grey_areas = []
        suggested_rating = 'PG'  # Default
        confidence = 0.5
        
        # Check for always-blocked content
        for keyword in self.always_block:
            if keyword in prompt_lower:
                violations.append({
                    'type': 'illegal_content',
                    'keyword': keyword,
                    'severity': 'critical'
                })
                return {
                    'suggested_rating': None,
                    'confidence': 1.0,
                    'blocked': True,
                    'violations': violations,
                    'reason': 'Contains illegal content keywords'
                }
        
        # Detect content level
        if any(kw in prompt_lower for kw in self.adult_explicit_keywords):
            suggested_rating = 'R'
            confidence = 0.8
            detected_keywords.extend([kw for kw in self.adult_explicit_keywords if kw in prompt_lower])
            
            if any(kw in prompt_lower for kw in ['hardcore', 'xxx', 'extreme']):
                suggested_rating = 'XXX'
                confidence = 0.9
            elif any(kw in prompt_lower for kw in ['explicit', 'graphic']):
                suggested_rating = 'HARD'
                confidence = 0.85
        
        elif any(kw in prompt_lower for kw in self.adult_soft_keywords):
            suggested_rating = 'SOFT'
            confidence = 0.75
            detected_keywords.extend([kw for kw in self.adult_soft_keywords if kw in prompt_lower])
            
            if any(kw in prompt_lower for kw in ['sheer', 'transparent']):
                suggested_rating = 'SOFT'
                grey_areas.append('sheer_clothing')
        
        elif any(kw in prompt_lower for kw in self.teen_keywords):
            suggested_rating = 'NC-15'
            confidence = 0.7
            detected_keywords.extend([kw for kw in self.teen_keywords if kw in prompt_lower])
        
        elif any(kw in prompt_lower for kw in self.family_keywords):
            suggested_rating = 'PG'
            confidence = 0.85
            detected_keywords.extend([kw for kw in self.family_keywords if kw in prompt_lower])
        
        # Check for rating violations if target specified
        if target_rating:
            target_info = RATINGS.get(target_rating, {})
            target_category = target_info.get('category', 'family_safe')
            
            if target_category == 'family_safe':
                for kw in self.family_block:
                    if kw in prompt_lower:
                        violations.append({
                            'type': 'family_safe_violation',
                            'keyword': kw,
                            'severity': 'block'
                        })
            
            elif target_category == 'teen':
                for kw in self.teen_block:
                    if kw in prompt_lower:
                        violations.append({
                            'type': 'teen_rating_violation',
                            'keyword': kw,
                            'severity': 'block'
                        })
        
        return {
            'suggested_rating': suggested_rating,
            'confidence': confidence,
            'detected_keywords': detected_keywords,
            'violations': violations,
            'grey_areas': grey_areas,
            'blocked': len([v for v in violations if v['severity'] in ['block', 'critical']]) > 0
        }
    
    def validate_content(self, prompt, target_rating):
        """Validate if prompt is appropriate for target rating"""
        analysis = self.analyze_prompt(prompt, target_rating)
        
        target_info = RATINGS.get(target_rating, {})
        suggested_info = RATINGS.get(analysis['suggested_rating'], {})
        
        target_level = target_info.get('guardrail_level', 1)
        suggested_level = suggested_info.get('guardrail_level', 1)
        
        is_valid = suggested_level <= target_level and not analysis['blocked']
        
        return {
            'valid': is_valid,
            'target_rating': target_rating,
            'suggested_rating': analysis['suggested_rating'],
            'target_guardrail_level': target_level,
            'detected_guardrail_level': suggested_level,
            'violations': analysis['violations'],
            'grey_areas': analysis['grey_areas'],
            'message': 'Content appropriate for rating' if is_valid else 'Content exceeds rating restrictions'
        }


# Initialize
db = RatingDB()
tagger = AutoTagger()


class RatingAPI(BaseHTTPRequestHandler):
    """Rating System API Handler"""
    
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
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        path = self.path.split('?')[0]
        params = parse_qs(urlparse(self.path).query)
        
        if path == '/':
            self._json({'service': 'Rating System API', 'version': '2.0', 'ratings': 22})
        
        elif path == '/api/stats':
            self._json(db.get_stats())
        
        elif path == '/api/ratings':
            self._json(db.get_all_ratings())
        
        elif path.startswith('/api/ratings/'):
            code = path.split('/')[-1]
            rating = db.get_rating(code)
            if rating:
                # Add full config info
                rating['config'] = RATINGS.get(code, {})
                self._json(rating)
            else:
                self._json({'error': 'Rating not found'}, 404)
        
        elif path == '/api/categories':
            self._json(CATEGORIES)
        
        elif path == '/api/guardrails':
            self._json(GUARDRAILS)
        
        elif path == '/api/session':
            session_id = params.get('id', [None])[0]
            if session_id:
                session = db.get_session(session_id)
                if session:
                    self._json(session)
                else:
                    self._json({'error': 'Session not found'}, 404)
            else:
                self._json({'error': 'Session ID required'}, 400)
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/analyze':
            prompt = data.get('prompt', '')
            target_rating = data.get('target_rating')
            
            result = tagger.analyze_prompt(prompt, target_rating)
            self._json(result)
        
        elif path == '/api/validate':
            prompt = data.get('prompt', '')
            target_rating = data.get('target_rating', 'PG')
            
            result = tagger.validate_content(prompt, target_rating)
            
            # Log violation if invalid
            if not result['valid']:
                db.log_violation(
                    data.get('image_id', 'unknown'),
                    prompt,
                    'content_violation',
                    'block' if result['violations'] else 'warning',
                    target_rating,
                    result['suggested_rating'],
                    [v['keyword'] for v in result['violations']],
                    result['message']
                )
            
            self._json(result)
        
        elif path == '/api/verify-age':
            session_id = data.get('session_id', hashlib.md5(str(datetime.now()).encode()).hexdigest())
            age = data.get('age', 0)
            
            if age < 1 or age > 120:
                self._json({'error': 'Invalid age'}, 400)
            else:
                result = db.verify_age(session_id, age)
                self._json(result)
        
        elif path == '/api/release-restrictions':
            session_id = data.get('session_id')
            if not session_id:
                self._json({'error': 'Session ID required'}, 400)
            else:
                result = db.release_restrictions(session_id)
                if 'error' in result:
                    self._json(result, 400)
                else:
                    self._json(result)
        
        elif path == '/api/auto-tag':
            image_id = data.get('image_id', '')
            image_path = data.get('image_path', '')
            prompt = data.get('prompt', '')
            
            # Analyze and tag
            analysis = tagger.analyze_prompt(prompt)
            
            db.log_auto_tag(
                image_id, image_path,
                analysis['suggested_rating'],
                analysis['confidence'],
                data.get('clothing_coverage', 100),
                analysis['detected_keywords'],
                analysis['grey_areas'],
                analysis['violations']
            )
            
            self._json({
                'image_id': image_id,
                'auto_tag_result': analysis,
                'logged': True
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  COMPREHENSIVE RATING SYSTEM API")
    print("  22 Ratings | Auto-Tagging | Guardrails")
    print("=" * 60)
    
    stats = db.get_stats()
    print(f"\n📊 Ratings Loaded: {stats['total_ratings']}")
    print(f"🏷️  Images Tagged: {stats['images_tagged']}")
    print(f"⚠️  Violations: {stats['violations_logged']}")
    print(f"📝 Pending Review: {stats['pending_review']}")
    
    print(f"\n📜 Rating Categories:")
    for cat, info in CATEGORIES.items():
        print(f"   {info['icon']} {info['name']} ({info['age_range']})")
    
    print(f"\n🌐 http://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), RatingAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
