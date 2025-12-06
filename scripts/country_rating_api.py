"""
INTERNATIONAL COUNTRY RATING API
=================================
195+ Countries Rating Standards
Age Restrictions Dashboard
Content Compliance System

Port: 8199
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configuration
PORT = 8199
DB_PATH = Path(r"c:\Users\Admin\civitai\data\country_ratings.db")
INTL_RATINGS_PATH = Path(r"c:\Users\Admin\civitai\data\international_ratings.json")
COMP_RATINGS_PATH = Path(r"c:\Users\Admin\civitai\data\comprehensive_ratings.json")

# Load international ratings
try:
    with open(INTL_RATINGS_PATH, encoding='utf-8') as f:
        INTL_RATINGS = json.load(f)
except Exception as e:
    print(f"Error loading international ratings: {e}")
    INTL_RATINGS = {"countries": {}, "rating_systems": {}}

# Load comprehensive ratings
try:
    with open(COMP_RATINGS_PATH, encoding='utf-8') as f:
        COMP_RATINGS = json.load(f)
except:
    COMP_RATINGS = {"ratings": {}}

COUNTRIES = INTL_RATINGS.get("countries", {})
RATING_SYSTEMS = INTL_RATINGS.get("rating_systems", {})
CONTENT_RESTRICTIONS = INTL_RATINGS.get("content_restrictions", {})


class CountryDB:
    """Database for country rating compliance"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS country_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                country_code TEXT NOT NULL,
                country_name TEXT,
                rating_system TEXT,
                adult_legal_age INTEGER,
                explicit_banned INTEGER DEFAULT 0,
                max_allowed_rating TEXT,
                restrictions_applied TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS content_compliance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT NOT NULL,
                country_code TEXT NOT NULL,
                our_rating TEXT,
                country_rating TEXT,
                compliant INTEGER DEFAULT 1,
                violations TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS blocked_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT NOT NULL,
                country_code TEXT NOT NULL,
                reason TEXT,
                blocked_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()
    
    def get_stats(self):
        """Get system statistics"""
        total_countries = len(COUNTRIES)
        total_systems = len(RATING_SYSTEMS)
        explicit_banned = len([c for c, d in COUNTRIES.items() if d.get('explicit_banned')])
        sessions = self.conn.execute('SELECT COUNT(*) FROM country_sessions').fetchone()[0]
        
        return {
            'total_countries': total_countries,
            'rating_systems': total_systems,
            'explicit_banned_countries': explicit_banned,
            'active_sessions': sessions
        }
    
    def get_country(self, code):
        """Get country details with full rating info"""
        code = code.upper()
        if code not in COUNTRIES:
            return None
        
        country = COUNTRIES[code].copy()
        country['code'] = code
        
        # Get rating system details
        system_id = country.get('system')
        if system_id and system_id in RATING_SYSTEMS:
            system = RATING_SYSTEMS[system_id]
            country['rating_system_name'] = system.get('name')
            country['rating_system_ratings'] = system.get('ratings', {})
        
        # Calculate max allowed rating
        country['max_our_rating'] = self._get_max_rating(country)
        
        # Get content restrictions
        country['content_restrictions'] = self._get_country_restrictions(code)
        
        return country
    
    def _get_max_rating(self, country):
        """Calculate maximum allowed rating for country"""
        if country.get('explicit_banned'):
            if country.get('strict_censorship'):
                return 'PG-13'
            return 'NC-18'
        
        adult_age = country.get('adult_legal_age', 18)
        if adult_age >= 21:
            return 'R'  # More restrictive for 21+ countries
        
        return 'EXTREME'  # Full access
    
    def _get_country_restrictions(self, code):
        """Get specific content restrictions for country"""
        restrictions = []
        
        for restriction_type, data in CONTENT_RESTRICTIONS.items():
            if code in data.get('banned_countries', []):
                restrictions.append({
                    'type': restriction_type,
                    'level': 'banned',
                    'description': f'{restriction_type} content is banned'
                })
            elif code in data.get('restricted_countries', []):
                restrictions.append({
                    'type': restriction_type,
                    'level': 'restricted',
                    'description': f'{restriction_type} content is restricted'
                })
        
        return restrictions
    
    def get_all_countries(self):
        """Get all countries with basic info"""
        countries = []
        for code, data in COUNTRIES.items():
            countries.append({
                'code': code,
                'name': data.get('name'),
                'system': data.get('system'),
                'adult_legal_age': data.get('adult_legal_age', 18),
                'explicit_banned': data.get('explicit_banned', False)
            })
        return sorted(countries, key=lambda x: x['name'])
    
    def get_countries_by_restriction(self, restriction_type):
        """Get countries by restriction type"""
        result = {
            'banned': [],
            'restricted': [],
            'allowed': []
        }
        
        restriction_data = CONTENT_RESTRICTIONS.get(restriction_type, {})
        banned = restriction_data.get('banned_countries', [])
        restricted = restriction_data.get('restricted_countries', [])
        
        for code, data in COUNTRIES.items():
            country_info = {'code': code, 'name': data.get('name')}
            if code in banned:
                result['banned'].append(country_info)
            elif code in restricted:
                result['restricted'].append(country_info)
            else:
                result['allowed'].append(country_info)
        
        return result
    
    def check_compliance(self, our_rating, country_code):
        """Check if our rating is compliant with country restrictions"""
        country = self.get_country(country_code)
        if not country:
            return {'error': 'Country not found'}
        
        max_rating = country['max_our_rating']
        our_ratings = COMP_RATINGS.get('ratings', {})
        
        our_level = our_ratings.get(our_rating, {}).get('guardrail_level', 1)
        max_level = our_ratings.get(max_rating, {}).get('guardrail_level', 5)
        
        compliant = our_level <= max_level
        
        return {
            'compliant': compliant,
            'our_rating': our_rating,
            'our_guardrail_level': our_level,
            'country': country['name'],
            'country_code': country_code,
            'max_allowed_rating': max_rating,
            'max_guardrail_level': max_level,
            'explicit_banned': country.get('explicit_banned', False),
            'restrictions': country.get('content_restrictions', []),
            'message': 'Content is compliant' if compliant else f'Content exceeds {country["name"]} restrictions'
        }
    
    def create_session(self, session_id, country_code):
        """Create country-specific session"""
        country = self.get_country(country_code)
        if not country:
            return {'error': 'Country not found'}
        
        self.conn.execute('''
            INSERT OR REPLACE INTO country_sessions
            (session_id, country_code, country_name, rating_system, 
             adult_legal_age, explicit_banned, max_allowed_rating, 
             restrictions_applied, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, country_code, country['name'],
            country.get('system'), country.get('adult_legal_age', 18),
            1 if country.get('explicit_banned') else 0,
            country['max_our_rating'],
            json.dumps(country.get('content_restrictions', [])),
            datetime.now().isoformat()
        ))
        self.conn.commit()
        
        return {
            'session_id': session_id,
            'country': country['name'],
            'country_code': country_code,
            'max_allowed_rating': country['max_our_rating'],
            'explicit_banned': country.get('explicit_banned', False),
            'adult_legal_age': country.get('adult_legal_age', 18),
            'restrictions': country.get('content_restrictions', [])
        }
    
    def get_rating_systems(self):
        """Get all rating systems"""
        systems = []
        for system_id, data in RATING_SYSTEMS.items():
            systems.append({
                'id': system_id,
                'name': data.get('name'),
                'countries': data.get('countries', []),
                'ratings_count': len(data.get('ratings', {}))
            })
        return systems
    
    def get_system_details(self, system_id):
        """Get detailed rating system info"""
        if system_id not in RATING_SYSTEMS:
            return None
        
        system = RATING_SYSTEMS[system_id].copy()
        system['id'] = system_id
        
        # Map to our ratings
        for rating_code, rating_data in system.get('ratings', {}).items():
            our_equiv = rating_data.get('our_equivalent')
            if our_equiv and our_equiv in COMP_RATINGS.get('ratings', {}):
                rating_data['our_rating_details'] = COMP_RATINGS['ratings'][our_equiv]
        
        return system


# Initialize database
db = CountryDB()


class CountryAPI(BaseHTTPRequestHandler):
    """Country Rating API Handler"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, ensure_ascii=False).encode('utf-8'))
    
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
            self._json({
                'service': 'International Country Rating API',
                'version': '1.0',
                'countries': len(COUNTRIES),
                'rating_systems': len(RATING_SYSTEMS)
            })
        
        elif path == '/api/stats':
            self._json(db.get_stats())
        
        elif path == '/api/countries':
            self._json(db.get_all_countries())
        
        elif path.startswith('/api/country/'):
            code = path.split('/')[-1].upper()
            country = db.get_country(code)
            if country:
                self._json(country)
            else:
                self._json({'error': 'Country not found'}, 404)
        
        elif path == '/api/systems':
            self._json(db.get_rating_systems())
        
        elif path.startswith('/api/system/'):
            system_id = path.split('/')[-1]
            system = db.get_system_details(system_id)
            if system:
                self._json(system)
            else:
                self._json({'error': 'Rating system not found'}, 404)
        
        elif path == '/api/restrictions':
            restriction_type = params.get('type', [None])[0]
            if restriction_type:
                self._json(db.get_countries_by_restriction(restriction_type))
            else:
                self._json({
                    'available_types': list(CONTENT_RESTRICTIONS.keys()),
                    'data': CONTENT_RESTRICTIONS
                })
        
        elif path == '/api/dashboard':
            # Country age dashboard
            stats = db.get_stats()
            
            # Group by adult legal age
            age_groups = {'16': [], '17': [], '18': [], '19': [], '20': [], '21': []}
            for code, data in COUNTRIES.items():
                age = str(data.get('adult_legal_age', 18))
                if age in age_groups:
                    age_groups[age].append({
                        'code': code,
                        'name': data.get('name'),
                        'explicit_banned': data.get('explicit_banned', False)
                    })
            
            # Group by explicit banned status
            explicit_status = {
                'banned': [{'code': c, 'name': d['name']} for c, d in COUNTRIES.items() if d.get('explicit_banned')],
                'allowed': [{'code': c, 'name': d['name']} for c, d in COUNTRIES.items() if not d.get('explicit_banned')]
            }
            
            dashboard = {
                'summary': stats,
                'age_of_majority': age_groups,
                'explicit_content_status': explicit_status,
                'restriction_types': list(CONTENT_RESTRICTIONS.keys()),
                'rating_systems_count': len(RATING_SYSTEMS)
            }
            
            self._json(dashboard)
        
        elif path == '/api/explicit-banned':
            banned = [
                {'code': c, 'name': d['name'], 'adult_age': d.get('adult_legal_age', 18)}
                for c, d in COUNTRIES.items() if d.get('explicit_banned')
            ]
            self._json({
                'count': len(banned),
                'countries': sorted(banned, key=lambda x: x['name'])
            })
        
        elif path == '/api/strict-countries':
            strict = [
                {'code': c, 'name': d['name'], 'reason': 'strict censorship' if d.get('strict_censorship') else 'explicit banned'}
                for c, d in COUNTRIES.items() 
                if d.get('explicit_banned') or d.get('strict_censorship')
            ]
            self._json({
                'count': len(strict),
                'countries': sorted(strict, key=lambda x: x['name'])
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/check-compliance':
            our_rating = data.get('rating', 'PG')
            country_code = data.get('country', 'US')
            result = db.check_compliance(our_rating, country_code)
            self._json(result)
        
        elif path == '/api/session':
            session_id = data.get('session_id', '')
            country_code = data.get('country', 'US')
            result = db.create_session(session_id, country_code)
            self._json(result)
        
        elif path == '/api/batch-compliance':
            our_rating = data.get('rating', 'PG')
            countries = data.get('countries', list(COUNTRIES.keys())[:10])
            
            results = []
            for country_code in countries:
                result = db.check_compliance(our_rating, country_code)
                results.append(result)
            
            compliant_count = len([r for r in results if r.get('compliant')])
            
            self._json({
                'rating': our_rating,
                'total_checked': len(results),
                'compliant_count': compliant_count,
                'non_compliant_count': len(results) - compliant_count,
                'results': results
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  INTERNATIONAL COUNTRY RATING API")
    print("  195+ Countries | Age Restrictions | Compliance")
    print("=" * 60)
    
    stats = db.get_stats()
    print(f"\nCountries: {stats['total_countries']}")
    print(f"Rating Systems: {stats['rating_systems']}")
    print(f"Explicit Banned Countries: {stats['explicit_banned_countries']}")
    
    print(f"\nAdult Age Requirements:")
    for age in ['16', '17', '18', '19', '20', '21']:
        countries = [c for c, d in COUNTRIES.items() if str(d.get('adult_legal_age', 18)) == age]
        if countries:
            print(f"  {age}+: {len(countries)} countries")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), CountryAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
