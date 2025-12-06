"""
SUPABASE LOCAL INTEGRATION
===========================
Local SQLite database mimicking Supabase features
User logging, session tracking, country access logs

Port: 8202
"""
import json
import sqlite3
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
PORT = 8202
DB_PATH = Path(r"c:\Users\Admin\civitai\data\supabase_local.db")


class SupabaseLocal:
    """Local Supabase-like database"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            -- Users table
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                country_code TEXT NOT NULL DEFAULT 'US',
                verified_age INTEGER,
                account_type TEXT DEFAULT 'user',
                restrictions_released INTEGER DEFAULT 0,
                max_rating_allowed TEXT DEFAULT 'PG',
                flagged INTEGER DEFAULT 0,
                flag_reason TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Sessions table
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id),
                country_code TEXT NOT NULL,
                max_rating TEXT,
                restrictions_released INTEGER DEFAULT 0,
                ip_address TEXT,
                user_agent TEXT,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                active INTEGER DEFAULT 1
            );
            
            -- Access logs (every content access)
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                country_code TEXT NOT NULL,
                content_type TEXT,
                content_rating TEXT,
                action TEXT NOT NULL,
                allowed INTEGER DEFAULT 1,
                blocked_reason TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Violation logs
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                country_code TEXT,
                prompt TEXT,
                rating_attempted TEXT,
                rating_allowed TEXT,
                violation_type TEXT NOT NULL,
                severity TEXT,
                auto_corrected INTEGER DEFAULT 0,
                admin_reviewed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Country access statistics
            CREATE TABLE IF NOT EXISTS country_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_code TEXT NOT NULL,
                date TEXT NOT NULL,
                total_sessions INTEGER DEFAULT 0,
                total_accesses INTEGER DEFAULT 0,
                violations INTEGER DEFAULT 0,
                blocks INTEGER DEFAULT 0,
                UNIQUE(country_code, date)
            );
            
            -- Flagged users from low-restriction countries
            CREATE TABLE IF NOT EXISTS flagged_country_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT REFERENCES users(id),
                country_code TEXT NOT NULL,
                flag_type TEXT NOT NULL,
                reason TEXT,
                access_pattern TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Analytics events
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                user_id TEXT,
                session_id TEXT,
                country_code TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_access_user ON access_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_access_country ON access_logs(country_code);
            CREATE INDEX IF NOT EXISTS idx_violations_user ON violations(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        ''')
        self.conn.commit()
    
    # ===== USER MANAGEMENT =====
    
    def create_user(self, username, country_code, email=None, verified_age=None):
        user_id = secrets.token_hex(16)
        try:
            self.conn.execute('''
                INSERT INTO users (id, username, email, country_code, verified_age)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, email, country_code, verified_age))
            self.conn.commit()
            return {'success': True, 'user_id': user_id, 'username': username}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Username exists'}
    
    def get_user(self, user_id):
        row = self.conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return dict(row) if row else None
    
    def update_user(self, user_id, data):
        updates = []
        values = []
        for key in ['email', 'country_code', 'verified_age', 'restrictions_released', 'max_rating_allowed']:
            if key in data:
                updates.append(f"{key} = ?")
                values.append(data[key])
        
        if updates:
            values.append(datetime.now().isoformat())
            values.append(user_id)
            self.conn.execute(f'''
                UPDATE users SET {', '.join(updates)}, updated_at = ? WHERE id = ?
            ''', values)
            self.conn.commit()
        return True
    
    # ===== SESSION MANAGEMENT =====
    
    def create_session(self, user_id, country_code, max_rating='PG', 
                       restrictions_released=False, ip_address=None):
        session_id = secrets.token_hex(16)
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        
        self.conn.execute('''
            INSERT INTO sessions (id, user_id, country_code, max_rating, 
                                 restrictions_released, ip_address, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, country_code, max_rating, 
              1 if restrictions_released else 0, ip_address, expires))
        self.conn.commit()
        
        # Update country stats
        self._update_country_stat(country_code, 'sessions')
        
        return {
            'session_id': session_id,
            'user_id': user_id,
            'country_code': country_code,
            'max_rating': max_rating,
            'restrictions_released': restrictions_released,
            'expires_at': expires
        }
    
    def validate_session(self, session_id):
        row = self.conn.execute('''
            SELECT s.*, u.username, u.account_type
            FROM sessions s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE s.id = ? AND s.active = 1
        ''', (session_id,)).fetchone()
        
        if not row:
            return None
        
        # Check expiry
        if row['expires_at']:
            expires = datetime.fromisoformat(row['expires_at'])
            if datetime.now() > expires:
                self.conn.execute('UPDATE sessions SET active = 0 WHERE id = ?', (session_id,))
                self.conn.commit()
                return None
        
        return dict(row)
    
    # ===== ACCESS LOGGING =====
    
    def log_access(self, user_id, session_id, country_code, content_type, 
                   content_rating, action, allowed=True, blocked_reason=None):
        self.conn.execute('''
            INSERT INTO access_logs 
            (user_id, session_id, country_code, content_type, content_rating, 
             action, allowed, blocked_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, session_id, country_code, content_type, content_rating,
              action, 1 if allowed else 0, blocked_reason))
        self.conn.commit()
        
        # Update country stats
        self._update_country_stat(country_code, 'accesses')
        if not allowed:
            self._update_country_stat(country_code, 'blocks')
    
    def log_violation(self, user_id, session_id, country_code, prompt,
                      rating_attempted, rating_allowed, violation_type, severity):
        self.conn.execute('''
            INSERT INTO violations
            (user_id, session_id, country_code, prompt, rating_attempted,
             rating_allowed, violation_type, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, session_id, country_code, prompt, rating_attempted,
              rating_allowed, violation_type, severity))
        self.conn.commit()
        
        self._update_country_stat(country_code, 'violations')
    
    # ===== FLAGGING SYSTEM =====
    
    def flag_user(self, user_id, country_code, flag_type, reason, access_pattern=None):
        self.conn.execute('''
            UPDATE users SET flagged = 1, flag_reason = ? WHERE id = ?
        ''', (reason, user_id))
        
        self.conn.execute('''
            INSERT INTO flagged_country_users 
            (user_id, country_code, flag_type, reason, access_pattern)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, country_code, flag_type, reason, 
              json.dumps(access_pattern) if access_pattern else None))
        self.conn.commit()
    
    def get_flagged_users(self):
        return [dict(r) for r in self.conn.execute('''
            SELECT u.*, f.flag_type, f.access_pattern
            FROM users u
            JOIN flagged_country_users f ON u.id = f.user_id
            WHERE u.flagged = 1
        ''').fetchall()]
    
    # ===== ANALYTICS =====
    
    def log_event(self, event_type, event_data, user_id=None, session_id=None, country_code=None):
        self.conn.execute('''
            INSERT INTO analytics (event_type, event_data, user_id, session_id, country_code)
            VALUES (?, ?, ?, ?, ?)
        ''', (event_type, json.dumps(event_data) if event_data else None,
              user_id, session_id, country_code))
        self.conn.commit()
    
    def _update_country_stat(self, country_code, stat_type):
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Try to update existing
        if stat_type == 'sessions':
            self.conn.execute('''
                INSERT INTO country_stats (country_code, date, total_sessions)
                VALUES (?, ?, 1)
                ON CONFLICT(country_code, date) DO UPDATE SET total_sessions = total_sessions + 1
            ''', (country_code, today))
        elif stat_type == 'accesses':
            self.conn.execute('''
                INSERT INTO country_stats (country_code, date, total_accesses)
                VALUES (?, ?, 1)
                ON CONFLICT(country_code, date) DO UPDATE SET total_accesses = total_accesses + 1
            ''', (country_code, today))
        elif stat_type == 'violations':
            self.conn.execute('''
                INSERT INTO country_stats (country_code, date, violations)
                VALUES (?, ?, 1)
                ON CONFLICT(country_code, date) DO UPDATE SET violations = violations + 1
            ''', (country_code, today))
        elif stat_type == 'blocks':
            self.conn.execute('''
                INSERT INTO country_stats (country_code, date, blocks)
                VALUES (?, ?, 1)
                ON CONFLICT(country_code, date) DO UPDATE SET blocks = blocks + 1
            ''', (country_code, today))
        
        self.conn.commit()
    
    def get_country_stats(self, country_code=None, days=7):
        if country_code:
            return [dict(r) for r in self.conn.execute('''
                SELECT * FROM country_stats 
                WHERE country_code = ? 
                ORDER BY date DESC LIMIT ?
            ''', (country_code, days)).fetchall()]
        else:
            return [dict(r) for r in self.conn.execute('''
                SELECT country_code, 
                       SUM(total_sessions) as total_sessions,
                       SUM(total_accesses) as total_accesses,
                       SUM(violations) as violations,
                       SUM(blocks) as blocks
                FROM country_stats
                GROUP BY country_code
                ORDER BY total_accesses DESC
            ''').fetchall()]
    
    def get_stats(self):
        users = self.conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        sessions = self.conn.execute('SELECT COUNT(*) FROM sessions WHERE active = 1').fetchone()[0]
        accesses = self.conn.execute('SELECT COUNT(*) FROM access_logs').fetchone()[0]
        violations = self.conn.execute('SELECT COUNT(*) FROM violations').fetchone()[0]
        flagged = self.conn.execute('SELECT COUNT(*) FROM users WHERE flagged = 1').fetchone()[0]
        
        return {
            'total_users': users,
            'active_sessions': sessions,
            'total_accesses': accesses,
            'total_violations': violations,
            'flagged_users': flagged
        }


# Initialize
db = SupabaseLocal()


class SupabaseAPI(BaseHTTPRequestHandler):
    """Supabase Local API Handler"""
    
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
                'service': 'Supabase Local API',
                'version': '1.0',
                'database': 'SQLite',
                'status': 'running'
            })
        
        elif path == '/api/stats':
            self._json(db.get_stats())
        
        elif path == '/api/country-stats':
            self._json(db.get_country_stats())
        
        elif path.startswith('/api/country-stats/'):
            country = path.split('/')[-1].upper()
            self._json(db.get_country_stats(country))
        
        elif path == '/api/users/flagged':
            self._json(db.get_flagged_users())
        
        elif path.startswith('/api/user/'):
            user_id = path.split('/')[-1]
            user = db.get_user(user_id)
            if user:
                self._json(user)
            else:
                self._json({'error': 'User not found'}, 404)
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/users':
            result = db.create_user(
                data.get('username'),
                data.get('country_code', 'US'),
                data.get('email'),
                data.get('verified_age')
            )
            self._json(result)
        
        elif path == '/api/sessions':
            result = db.create_session(
                data.get('user_id'),
                data.get('country_code', 'US'),
                data.get('max_rating', 'PG'),
                data.get('restrictions_released', False),
                data.get('ip_address')
            )
            self._json(result)
        
        elif path == '/api/sessions/validate':
            session = db.validate_session(data.get('session_id'))
            if session:
                self._json(session)
            else:
                self._json({'valid': False}, 401)
        
        elif path == '/api/access':
            db.log_access(
                data.get('user_id'),
                data.get('session_id'),
                data.get('country_code', 'US'),
                data.get('content_type'),
                data.get('content_rating'),
                data.get('action'),
                data.get('allowed', True),
                data.get('blocked_reason')
            )
            self._json({'logged': True})
        
        elif path == '/api/violations':
            db.log_violation(
                data.get('user_id'),
                data.get('session_id'),
                data.get('country_code'),
                data.get('prompt'),
                data.get('rating_attempted'),
                data.get('rating_allowed'),
                data.get('violation_type'),
                data.get('severity')
            )
            self._json({'logged': True})
        
        elif path == '/api/users/flag':
            db.flag_user(
                data.get('user_id'),
                data.get('country_code'),
                data.get('flag_type', 'manual'),
                data.get('reason'),
                data.get('access_pattern')
            )
            self._json({'flagged': True})
        
        elif path == '/api/events':
            db.log_event(
                data.get('event_type'),
                data.get('event_data'),
                data.get('user_id'),
                data.get('session_id'),
                data.get('country_code')
            )
            self._json({'logged': True})
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  SUPABASE LOCAL API")
    print("  User Logging | Session Tracking | Analytics")
    print("=" * 60)
    
    stats = db.get_stats()
    print(f"\nTotal Users: {stats['total_users']}")
    print(f"Active Sessions: {stats['active_sessions']}")
    print(f"Total Accesses: {stats['total_accesses']}")
    print(f"Violations: {stats['total_violations']}")
    print(f"Flagged Users: {stats['flagged_users']}")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), SupabaseAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
