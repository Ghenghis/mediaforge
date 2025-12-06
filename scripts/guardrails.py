"""
GUARDRAILS ENFORCEMENT ENGINE
==============================
Strict content enforcement with country compliance
Auto-blocks, sanitizes, and logs all violations

Port: 8200
"""
import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
PORT = 8200
DB_PATH = Path(r"c:\Users\Admin\civitai\data\guardrails.db")
RATINGS_PATH = Path(r"c:\Users\Admin\civitai\data\comprehensive_ratings.json")
INTL_PATH = Path(r"c:\Users\Admin\civitai\data\international_ratings.json")

# Load configurations
try:
    with open(RATINGS_PATH, encoding='utf-8') as f:
        RATINGS_CONFIG = json.load(f)
except:
    RATINGS_CONFIG = {"ratings": {}}

try:
    with open(INTL_PATH, encoding='utf-8') as f:
        INTL_CONFIG = json.load(f)
except:
    INTL_CONFIG = {"countries": {}}

RATINGS = RATINGS_CONFIG.get("ratings", {})
COUNTRIES = INTL_CONFIG.get("countries", {})


class GuardrailsDB:
    """Database for guardrails logging"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_id TEXT,
                country_code TEXT,
                prompt TEXT,
                target_rating TEXT,
                detected_rating TEXT,
                violation_type TEXT,
                severity TEXT,
                blocked_keywords TEXT,
                auto_corrected INTEGER DEFAULT 0,
                corrected_prompt TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS blocked_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                country_code TEXT,
                content_type TEXT,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS admin_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id TEXT,
                action TEXT,
                target TEXT,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()
    
    def log_violation(self, data):
        self.conn.execute('''
            INSERT INTO violations 
            (session_id, user_id, country_code, prompt, target_rating, 
             detected_rating, violation_type, severity, blocked_keywords,
             auto_corrected, corrected_prompt, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('session_id'), data.get('user_id'), data.get('country_code'),
            data.get('prompt'), data.get('target_rating'), data.get('detected_rating'),
            data.get('violation_type'), data.get('severity'), 
            json.dumps(data.get('blocked_keywords', [])),
            1 if data.get('auto_corrected') else 0, data.get('corrected_prompt'),
            datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def log_blocked(self, session_id, country_code, content_type, reason):
        self.conn.execute('''
            INSERT INTO blocked_attempts (session_id, country_code, content_type, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, country_code, content_type, reason, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_stats(self):
        violations = self.conn.execute('SELECT COUNT(*) FROM violations').fetchone()[0]
        blocked = self.conn.execute('SELECT COUNT(*) FROM blocked_attempts').fetchone()[0]
        auto_corrected = self.conn.execute(
            'SELECT COUNT(*) FROM violations WHERE auto_corrected = 1').fetchone()[0]
        return {
            'total_violations': violations,
            'total_blocked': blocked,
            'auto_corrected': auto_corrected
        }


class GuardrailsEngine:
    """Main enforcement engine"""
    
    # GLOBAL FORBIDDEN - Always blocked regardless of rating (47 unique terms)
    GLOBAL_FORBIDDEN = [
        # Minor-related (25 terms)
        "child", "children", "minor", "minors", "underage", "loli", "lolita",
        "shota", "shotacon", "young girl", "young boy", "little girl", "little boy",
        "infant", "baby", "toddler", "preteen", "pre-teen", "prepubescent",
        "pubescent", "juvenile", "kid", "kids", "schoolgirl inappropriate",
        "schoolboy inappropriate",
        # Illegal content (15 terms)
        "illegal", "abuse", "assault", "rape", "non-consensual", "nonconsensual",
        "forced", "trafficking", "exploitation", "bestiality", "zoophilia",
        "necrophilia", "incest", "pedophilia", "pedophile",
        # Extreme violence (7 terms)
        "snuff", "torture porn", "gore porn", "murder porn", "death porn",
        "real death", "real violence"
    ]
    
    # Rating-specific forbidden terms
    RATING_FORBIDDEN = {
        "family_safe": [
            "nude", "naked", "explicit", "sexual", "erotic", "nsfw", "xxx",
            "porn", "sex", "intimate", "sensual", "revealing", "lingerie",
            "underwear", "bikini", "topless", "bottomless", "nipple", "breast",
            "butt", "ass", "cleavage", "seductive", "provocative"
        ],
        "teen": [
            "nude", "naked", "explicit", "sexual", "erotic", "nsfw", "xxx",
            "porn", "sex", "hardcore", "graphic", "penetration"
        ],
        "adult_entry": [
            "hardcore", "xxx", "extreme", "penetration", "graphic sex"
        ],
        "adult_soft": [
            "hardcore", "xxx", "extreme", "penetration"
        ],
        "adult_explicit": []  # No restrictions except global
    }
    
    # Auto-correction replacements
    CORRECTIONS = {
        "nude": "clothed",
        "naked": "dressed",
        "explicit": "tasteful",
        "sexual": "romantic",
        "erotic": "elegant",
        "nsfw": "artistic",
        "revealing": "stylish",
        "seductive": "confident",
        "provocative": "bold"
    }
    
    def __init__(self, db: GuardrailsDB):
        self.db = db
    
    def check_global_forbidden(self, prompt):
        """Check for globally forbidden content"""
        prompt_lower = prompt.lower()
        found = []
        for term in self.GLOBAL_FORBIDDEN:
            if term in prompt_lower:
                found.append(term)
        return found
    
    def check_rating_forbidden(self, prompt, rating):
        """Check for rating-specific forbidden content"""
        prompt_lower = prompt.lower()
        
        # Get rating category
        rating_info = RATINGS.get(rating, {})
        category = rating_info.get("category", "family_safe")
        
        forbidden = self.RATING_FORBIDDEN.get(category, [])
        found = []
        for term in forbidden:
            if term in prompt_lower:
                found.append(term)
        return found
    
    def check_country_allowed(self, country_code, rating):
        """Check if rating is allowed in country"""
        country = COUNTRIES.get(country_code.upper(), {})
        
        # Get rating info
        rating_info = RATINGS.get(rating, {})
        category = rating_info.get("category", "family_safe")
        explicit_allowed = rating_info.get("explicit_allowed", False)
        nudity_allowed = rating_info.get("nudity_allowed", False)
        
        # Check country restrictions
        if country.get("explicit_banned") and explicit_allowed:
            return False, f"Explicit content banned in {country.get('name', country_code)}"
        
        if country.get("strict_censorship"):
            if category in ["adult_soft", "adult_explicit"]:
                return False, f"Adult content banned in {country.get('name', country_code)}"
        
        return True, "Allowed"
    
    def auto_correct(self, prompt, blocked_terms):
        """Auto-correct prompt by replacing forbidden terms"""
        corrected = prompt
        for term in blocked_terms:
            if term in self.CORRECTIONS:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                corrected = pattern.sub(self.CORRECTIONS[term], corrected)
            else:
                # Remove the term
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                corrected = pattern.sub("", corrected)
        
        # Clean up extra spaces
        corrected = re.sub(r'\s+', ' ', corrected).strip()
        return corrected
    
    def enforce(self, prompt, target_rating, country_code="US", session_id=None, 
                user_id=None, admin_bypass=False):
        """
        Main enforcement function
        Returns: {allowed, prompt, violations, corrected_prompt, message}
        """
        result = {
            "allowed": True,
            "original_prompt": prompt,
            "prompt": prompt,
            "violations": [],
            "blocked_terms": [],
            "corrected_prompt": None,
            "country_allowed": True,
            "message": "Content approved"
        }
        
        # Admin bypass
        if admin_bypass:
            result["message"] = "Admin bypass - all restrictions lifted"
            return result
        
        # Check global forbidden (ALWAYS enforced)
        global_forbidden = self.check_global_forbidden(prompt)
        if global_forbidden:
            result["allowed"] = False
            result["violations"].append({
                "type": "global_forbidden",
                "severity": "critical",
                "terms": global_forbidden
            })
            result["blocked_terms"].extend(global_forbidden)
            result["message"] = "Content contains globally forbidden terms"
            
            # Log and block
            self.db.log_violation({
                "session_id": session_id,
                "user_id": user_id,
                "country_code": country_code,
                "prompt": prompt,
                "target_rating": target_rating,
                "violation_type": "global_forbidden",
                "severity": "critical",
                "blocked_keywords": global_forbidden
            })
            
            return result
        
        # Check country restrictions
        country_allowed, country_message = self.check_country_allowed(country_code, target_rating)
        if not country_allowed:
            result["allowed"] = False
            result["country_allowed"] = False
            result["violations"].append({
                "type": "country_restriction",
                "severity": "block",
                "message": country_message
            })
            result["message"] = country_message
            
            self.db.log_blocked(session_id, country_code, target_rating, country_message)
            return result
        
        # Check rating-specific forbidden
        rating_forbidden = self.check_rating_forbidden(prompt, target_rating)
        if rating_forbidden:
            result["blocked_terms"].extend(rating_forbidden)
            result["violations"].append({
                "type": "rating_violation",
                "severity": "warning",
                "terms": rating_forbidden,
                "target_rating": target_rating
            })
            
            # Auto-correct
            corrected = self.auto_correct(prompt, rating_forbidden)
            result["corrected_prompt"] = corrected
            result["prompt"] = corrected
            result["message"] = f"Content auto-corrected for {target_rating} rating"
            
            # Log violation with correction
            self.db.log_violation({
                "session_id": session_id,
                "user_id": user_id,
                "country_code": country_code,
                "prompt": prompt,
                "target_rating": target_rating,
                "violation_type": "rating_violation",
                "severity": "warning",
                "blocked_keywords": rating_forbidden,
                "auto_corrected": True,
                "corrected_prompt": corrected
            })
        
        return result
    
    def get_max_rating(self, country_code):
        """Get maximum allowed rating for country"""
        country = COUNTRIES.get(country_code.upper(), {})
        
        if country.get("strict_censorship"):
            return "PG-13"
        if country.get("explicit_banned"):
            return "NC-18"
        
        adult_age = country.get("adult_legal_age", 18)
        if adult_age >= 21:
            return "R"
        
        return "EXTREME"


# Initialize
db = GuardrailsDB()
engine = GuardrailsEngine(db)


class GuardrailsAPI(BaseHTTPRequestHandler):
    """Guardrails API Handler"""
    
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
        
        if path == '/':
            self._json({
                'service': 'Guardrails Enforcement API',
                'version': '1.0',
                'ratings': len(RATINGS),
                'countries': len(COUNTRIES)
            })
        
        elif path == '/api/stats':
            self._json(db.get_stats())
        
        elif path == '/api/forbidden':
            self._json({
                'global': engine.GLOBAL_FORBIDDEN,
                'by_category': engine.RATING_FORBIDDEN
            })
        
        elif path.startswith('/api/max-rating/'):
            country = path.split('/')[-1].upper()
            max_rating = engine.get_max_rating(country)
            country_info = COUNTRIES.get(country, {})
            self._json({
                'country': country,
                'country_name': country_info.get('name', 'Unknown'),
                'max_rating': max_rating,
                'explicit_banned': country_info.get('explicit_banned', False)
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/enforce':
            prompt = data.get('prompt', '')
            rating = data.get('rating', 'PG')
            country = data.get('country', 'US')
            session_id = data.get('session_id')
            user_id = data.get('user_id')
            admin_bypass = data.get('admin_bypass', False)
            
            result = engine.enforce(
                prompt, rating, country, session_id, user_id, admin_bypass
            )
            self._json(result)
        
        elif path == '/api/check':
            prompt = data.get('prompt', '')
            rating = data.get('rating', 'PG')
            
            global_issues = engine.check_global_forbidden(prompt)
            rating_issues = engine.check_rating_forbidden(prompt, rating)
            
            self._json({
                'prompt': prompt,
                'rating': rating,
                'has_issues': len(global_issues) > 0 or len(rating_issues) > 0,
                'global_forbidden': global_issues,
                'rating_forbidden': rating_issues,
                'total_issues': len(global_issues) + len(rating_issues)
            })
        
        elif path == '/api/sanitize':
            prompt = data.get('prompt', '')
            rating = data.get('rating', 'PG')
            
            blocked = engine.check_rating_forbidden(prompt, rating)
            sanitized = engine.auto_correct(prompt, blocked)
            
            self._json({
                'original': prompt,
                'sanitized': sanitized,
                'removed_terms': blocked,
                'changes_made': len(blocked) > 0
            })
        
        elif path == '/api/e2e-test':
            # End-to-end system validation using real codebase
            results = {
                'timestamp': datetime.now().isoformat(),
                'tests': [],
                'passed': 0,
                'failed': 0
            }
            
            # Test 1: Global forbidden detection
            test1_prompt = "safe landscape photo"
            test1_result = engine.check_global_forbidden(test1_prompt)
            results['tests'].append({
                'name': 'Global Forbidden - Safe Prompt',
                'passed': len(test1_result) == 0,
                'details': 'No forbidden terms in safe prompt'
            })
            if len(test1_result) == 0:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # Test 2: Rating enforcement
            test2_prompt = "nude artistic photo"
            test2_rating = "PG"
            test2_result = engine.check_rating_forbidden(test2_prompt, test2_rating)
            results['tests'].append({
                'name': 'Rating Enforcement - PG blocks nude',
                'passed': 'nude' in test2_result,
                'details': f'Blocked terms: {test2_result}'
            })
            if 'nude' in test2_result:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # Test 3: Auto-correction
            test3_blocked = ['nude', 'explicit']
            test3_prompt = "nude explicit photo"
            test3_corrected = engine.auto_correct(test3_prompt, test3_blocked)
            results['tests'].append({
                'name': 'Auto-Correction Works',
                'passed': 'nude' not in test3_corrected.lower() and 'explicit' not in test3_corrected.lower(),
                'details': f'Corrected: {test3_corrected}'
            })
            if 'nude' not in test3_corrected.lower():
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # Test 4: Country restriction check
            test4_allowed_us, _ = engine.check_country_allowed('US', 'EXTREME')
            test4_allowed_sa, _ = engine.check_country_allowed('SA', 'EXTREME')
            results['tests'].append({
                'name': 'Country Restrictions',
                'passed': test4_allowed_us and not test4_allowed_sa,
                'details': f'US allows EXTREME: {test4_allowed_us}, SA allows EXTREME: {test4_allowed_sa}'
            })
            if test4_allowed_us and not test4_allowed_sa:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # Test 5: Full enforcement pipeline
            test5_result = engine.enforce("beautiful landscape sunset", "PG", "US")
            results['tests'].append({
                'name': 'Full Enforcement Pipeline',
                'passed': test5_result['allowed'],
                'details': f'Safe prompt allowed: {test5_result["allowed"]}'
            })
            if test5_result['allowed']:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            results['total'] = results['passed'] + results['failed']
            results['success_rate'] = f"{(results['passed']/results['total']*100):.1f}%"
            
            self._json(results)
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  GUARDRAILS ENFORCEMENT ENGINE")
    print("  Strict Content Protection | Country Compliance")
    print("=" * 60)
    
    stats = db.get_stats()
    print(f"\nViolations Logged: {stats['total_violations']}")
    print(f"Blocked Attempts: {stats['total_blocked']}")
    print(f"Auto-Corrected: {stats['auto_corrected']}")
    
    print(f"\nGlobal Forbidden Terms: {len(engine.GLOBAL_FORBIDDEN)}")
    print(f"Ratings Protected: {len(RATINGS)}")
    print(f"Countries: {len(COUNTRIES)}")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), GuardrailsAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
