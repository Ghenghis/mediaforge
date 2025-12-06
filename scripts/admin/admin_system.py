"""
ADMIN ACCOUNT SYSTEM
=====================
Full access admin for testing
Bypasses all restrictions
Logs all admin actions

Port: 8201
"""
import json
import sqlite3
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
PORT = 8201
DB_PATH = Path(r"c:\Users\Admin\civitai\data\admin_system.db")

# Admin credentials (in production, use environment variables)
ADMIN_ACCOUNTS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "type": "super_admin",
        "permissions": {
            "full_access": True,
            "bypass_ratings": True,
            "bypass_country": True,
            "view_all_logs": True,
            "test_violations": True,
            "manage_users": True,
            "system_config": True
        }
    },
    "tester": {
        "password_hash": hashlib.sha256("test123".encode()).hexdigest(),
        "type": "tester",
        "permissions": {
            "full_access": False,
            "bypass_ratings": True,
            "bypass_country": True,
            "view_all_logs": True,
            "test_violations": True,
            "manage_users": False,
            "system_config": False
        }
    }
}


class AdminDB:
    """Database for admin system"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS admin_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_token TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                admin_type TEXT NOT NULL,
                permissions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                active INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_token TEXT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                country_code TEXT NOT NULL DEFAULT 'US',
                verified_age INTEGER,
                account_type TEXT DEFAULT 'user',
                restrictions_released INTEGER DEFAULT 0,
                flagged INTEGER DEFAULT 0,
                flag_reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            );
            
            CREATE TABLE IF NOT EXISTS user_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                flag_type TEXT NOT NULL,
                reason TEXT,
                flagged_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()
    
    def create_session(self, username, admin_type, permissions):
        token = secrets.token_hex(32)
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        
        self.conn.execute('''
            INSERT INTO admin_sessions (session_token, username, admin_type, permissions, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (token, username, admin_type, json.dumps(permissions), expires))
        self.conn.commit()
        
        return {
            'token': token,
            'username': username,
            'admin_type': admin_type,
            'permissions': permissions,
            'expires_at': expires
        }
    
    def validate_session(self, token):
        row = self.conn.execute('''
            SELECT * FROM admin_sessions WHERE session_token = ? AND active = 1
        ''', (token,)).fetchone()
        
        if not row:
            return None
        
        # Check expiry
        expires = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires:
            self.conn.execute('UPDATE admin_sessions SET active = 0 WHERE session_token = ?', (token,))
            self.conn.commit()
            return None
        
        return dict(row)
    
    def log_action(self, token, username, action, target=None, details=None):
        self.conn.execute('''
            INSERT INTO admin_actions (session_token, username, action, target, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (token, username, action, target, json.dumps(details) if details else None))
        self.conn.commit()
    
    def get_actions(self, limit=100):
        return [dict(r) for r in self.conn.execute('''
            SELECT * FROM admin_actions ORDER BY created_at DESC LIMIT ?
        ''', (limit,)).fetchall()]
    
    def create_user(self, username, country_code, email=None, verified_age=None):
        try:
            self.conn.execute('''
                INSERT INTO users (username, email, country_code, verified_age)
                VALUES (?, ?, ?, ?)
            ''', (username, email, country_code, verified_age))
            self.conn.commit()
            return {'success': True, 'username': username}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Username exists'}
    
    def get_users(self, limit=100):
        return [dict(r) for r in self.conn.execute('''
            SELECT * FROM users ORDER BY created_at DESC LIMIT ?
        ''', (limit,)).fetchall()]
    
    def flag_user(self, user_id, flag_type, reason, flagged_by):
        self.conn.execute('''
            UPDATE users SET flagged = 1, flag_reason = ? WHERE id = ?
        ''', (reason, user_id))
        
        self.conn.execute('''
            INSERT INTO user_flags (user_id, flag_type, reason, flagged_by)
            VALUES (?, ?, ?, ?)
        ''', (user_id, flag_type, reason, flagged_by))
        self.conn.commit()
    
    def get_flagged_users(self):
        return [dict(r) for r in self.conn.execute('''
            SELECT * FROM users WHERE flagged = 1
        ''').fetchall()]
    
    def get_stats(self):
        sessions = self.conn.execute('SELECT COUNT(*) FROM admin_sessions WHERE active = 1').fetchone()[0]
        actions = self.conn.execute('SELECT COUNT(*) FROM admin_actions').fetchone()[0]
        users = self.conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        flagged = self.conn.execute('SELECT COUNT(*) FROM users WHERE flagged = 1').fetchone()[0]
        
        return {
            'active_sessions': sessions,
            'total_actions': actions,
            'total_users': users,
            'flagged_users': flagged
        }


# Initialize
db = AdminDB()


class AdminAPI(BaseHTTPRequestHandler):
    """Admin System API Handler"""
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length)) if length else {}
    
    def _auth(self):
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
            return db.validate_session(token)
        return None
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        path = self.path.split('?')[0]
        
        if path == '/':
            self._json({
                'service': 'Admin System API',
                'version': '1.0',
                'status': 'running'
            })
        
        elif path == '/api/stats':
            session = self._auth()
            if not session:
                self._json({'error': 'Unauthorized'}, 401)
                return
            self._json(db.get_stats())
        
        elif path == '/api/actions':
            session = self._auth()
            if not session:
                self._json({'error': 'Unauthorized'}, 401)
                return
            self._json(db.get_actions())
        
        elif path == '/api/users':
            session = self._auth()
            if not session:
                self._json({'error': 'Unauthorized'}, 401)
                return
            
            permissions = json.loads(session.get('permissions', '{}'))
            if not permissions.get('manage_users'):
                self._json({'error': 'Permission denied'}, 403)
                return
            
            self._json(db.get_users())
        
        elif path == '/api/users/flagged':
            session = self._auth()
            if not session:
                self._json({'error': 'Unauthorized'}, 401)
                return
            self._json(db.get_flagged_users())
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def do_POST(self):
        path = self.path
        data = self._body()
        
        if path == '/api/login':
            username = data.get('username', '')
            password = data.get('password', '')
            
            admin = ADMIN_ACCOUNTS.get(username)
            if not admin:
                self._json({'error': 'Invalid credentials'}, 401)
                return
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != admin['password_hash']:
                self._json({'error': 'Invalid credentials'}, 401)
                return
            
            session = db.create_session(username, admin['type'], admin['permissions'])
            db.log_action(session['token'], username, 'login')
            
            self._json({
                'success': True,
                'token': session['token'],
                'admin_type': admin['type'],
                'permissions': admin['permissions'],
                'expires_at': session['expires_at']
            })
        
        elif path == '/api/logout':
            session = self._auth()
            if session:
                db.conn.execute('UPDATE admin_sessions SET active = 0 WHERE session_token = ?', 
                              (session['session_token'],))
                db.conn.commit()
                db.log_action(session['session_token'], session['username'], 'logout')
            self._json({'success': True})
        
        elif path == '/api/validate':
            session = self._auth()
            if not session:
                self._json({'valid': False}, 401)
                return
            
            permissions = json.loads(session.get('permissions', '{}'))
            self._json({
                'valid': True,
                'username': session['username'],
                'admin_type': session['admin_type'],
                'permissions': permissions,
                'bypass_ratings': permissions.get('bypass_ratings', False),
                'bypass_country': permissions.get('bypass_country', False)
            })
        
        elif path == '/api/users/create':
            session = self._auth()
            if not session:
                self._json({'error': 'Unauthorized'}, 401)
                return
            
            permissions = json.loads(session.get('permissions', '{}'))
            if not permissions.get('manage_users'):
                self._json({'error': 'Permission denied'}, 403)
                return
            
            result = db.create_user(
                data.get('username'),
                data.get('country_code', 'US'),
                data.get('email'),
                data.get('verified_age')
            )
            
            if result['success']:
                db.log_action(session['session_token'], session['username'], 
                            'create_user', data.get('username'))
            
            self._json(result)
        
        elif path == '/api/users/flag':
            session = self._auth()
            if not session:
                self._json({'error': 'Unauthorized'}, 401)
                return
            
            db.flag_user(
                data.get('user_id'),
                data.get('flag_type', 'manual'),
                data.get('reason', 'Flagged by admin'),
                session['username']
            )
            
            db.log_action(session['session_token'], session['username'],
                        'flag_user', str(data.get('user_id')), data)
            
            self._json({'success': True})
        
        elif path == '/api/test/violation':
            # Test endpoint - only for admins
            session = self._auth()
            if not session:
                self._json({'error': 'Unauthorized'}, 401)
                return
            
            permissions = json.loads(session.get('permissions', '{}'))
            if not permissions.get('test_violations'):
                self._json({'error': 'Permission denied'}, 403)
                return
            
            # Return bypass token for testing
            db.log_action(session['session_token'], session['username'],
                        'test_violation', data.get('test_type'))
            
            self._json({
                'admin_bypass': True,
                'message': 'Violation testing enabled',
                'can_test': ['rating_bypass', 'country_bypass', 'forbidden_terms']
            })
        
        else:
            self._json({'error': 'Not found'}, 404)
    
    def log_message(self, *args): pass


def main():
    print("=" * 60)
    print("  ADMIN SYSTEM API")
    print("  Full Access | User Management | Testing")
    print("=" * 60)
    
    stats = db.get_stats()
    print(f"\nActive Sessions: {stats['active_sessions']}")
    print(f"Total Actions: {stats['total_actions']}")
    print(f"Total Users: {stats['total_users']}")
    print(f"Flagged Users: {stats['flagged_users']}")
    
    print(f"\nAdmin Accounts:")
    for username, info in ADMIN_ACCOUNTS.items():
        print(f"  - {username} ({info['type']})")
    
    print(f"\nhttp://127.0.0.1:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('127.0.0.1', PORT), AdminAPI)
    server.serve_forever()


if __name__ == '__main__':
    main()
