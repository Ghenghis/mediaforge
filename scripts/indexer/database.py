"""
LORAFORGE - DATABASE MANAGER
SQLite database for media catalog and analysis results
Portable, no external server required

TABLES:
- media: All indexed image/video files
- analysis: Analysis results (CLIP, quality, captions, etc.)
- dataset_items: Training dataset assignments
- index_sessions: Indexing history
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass, asdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info


# Default database location
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "loraforge.db"


@dataclass
class MediaRecord:
    """Media file record"""
    id: int = None
    file_path: str = ""
    file_name: str = ""
    file_hash: str = None
    file_size: int = 0
    media_type: str = ""  # image, video
    format: str = ""
    width: int = 0
    height: int = 0
    duration: float = None
    status: str = "indexed"
    created_at: str = None
    indexed_at: str = None


@dataclass
class AnalysisRecord:
    """Analysis result record"""
    id: int = None
    media_id: int = None
    analysis_type: str = ""  # clip, quality, caption, cluster, vision
    result_json: str = "{}"
    score: float = None
    analyzed_at: str = None


class DatabaseManager:
    """
    SQLite database manager for LoRAForge media catalog.
    
    Features:
    - Automatic schema creation
    - Connection pooling via context manager
    - JSON storage for flexible analysis results
    - Efficient batch operations
    """
    
    SCHEMA = """
    -- Core media table
    CREATE TABLE IF NOT EXISTS media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE NOT NULL,
        file_name TEXT NOT NULL,
        file_hash TEXT,
        file_size INTEGER,
        media_type TEXT,
        format TEXT,
        width INTEGER,
        height INTEGER,
        duration REAL,
        created_at TIMESTAMP,
        modified_at TIMESTAMP,
        indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'indexed'
    );
    
    -- Analysis results
    CREATE TABLE IF NOT EXISTS analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
        analysis_type TEXT,
        result_json TEXT,
        score REAL,
        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Training dataset assignments
    CREATE TABLE IF NOT EXISTS dataset_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
        dataset_name TEXT,
        split TEXT,
        caption TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Indexing sessions
    CREATE TABLE IF NOT EXISTS index_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_path TEXT,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        files_found INTEGER DEFAULT 0,
        files_indexed INTEGER DEFAULT 0,
        status TEXT DEFAULT 'running'
    );
    
    -- Character clusters
    CREATE TABLE IF NOT EXISTS clusters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_name TEXT,
        sample_image_id INTEGER REFERENCES media(id),
        image_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_media_type ON media(media_type);
    CREATE INDEX IF NOT EXISTS idx_media_status ON media(status);
    CREATE INDEX IF NOT EXISTS idx_media_hash ON media(file_hash);
    CREATE INDEX IF NOT EXISTS idx_media_format ON media(format);
    CREATE INDEX IF NOT EXISTS idx_analysis_media ON analysis(media_id);
    CREATE INDEX IF NOT EXISTS idx_analysis_type ON analysis(analysis_type);
    CREATE INDEX IF NOT EXISTS idx_dataset_name ON dataset_items(dataset_name);
    """
    
    def __init__(self, db_path: Path = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()
        print_info(f"Database initialized: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection as context manager"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ========================================
    # MEDIA OPERATIONS
    # ========================================
    
    def add_media(self, record: MediaRecord) -> int:
        """
        Add media file to database.
        
        Args:
            record: MediaRecord to add
            
        Returns:
            Inserted record ID
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO media 
                (file_path, file_name, file_hash, file_size, media_type, 
                 format, width, height, duration, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.file_path, record.file_name, record.file_hash,
                record.file_size, record.media_type, record.format,
                record.width, record.height, record.duration,
                record.created_at, record.status
            ))
            conn.commit()
            return cursor.lastrowid
    
    def add_media_batch(self, records: List[MediaRecord]) -> int:
        """
        Add multiple media files in a batch.
        
        Args:
            records: List of MediaRecord
            
        Returns:
            Number of records inserted
        """
        with self.get_connection() as conn:
            data = [
                (r.file_path, r.file_name, r.file_hash, r.file_size,
                 r.media_type, r.format, r.width, r.height, r.duration,
                 r.created_at, r.status)
                for r in records
            ]
            conn.executemany("""
                INSERT OR IGNORE INTO media 
                (file_path, file_name, file_hash, file_size, media_type,
                 format, width, height, duration, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()
            return len(data)
    
    def get_media(self, media_id: int) -> Optional[Dict]:
        """Get media by ID"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM media WHERE id = ?", (media_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def get_media_by_path(self, file_path: str) -> Optional[Dict]:
        """Get media by file path"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM media WHERE file_path = ?", (file_path,)
            ).fetchone()
            return dict(row) if row else None
    
    def get_media_by_hash(self, file_hash: str) -> List[Dict]:
        """Get all media with same hash (duplicates)"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM media WHERE file_hash = ?", (file_hash,)
            ).fetchall()
            return [dict(r) for r in rows]
    
    def list_media(
        self,
        media_type: str = None,
        status: str = None,
        format: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        List media with optional filters.
        
        Args:
            media_type: Filter by type (image/video)
            status: Filter by status
            format: Filter by format
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of media records
        """
        query = "SELECT * FROM media WHERE 1=1"
        params = []
        
        if media_type:
            query += " AND media_type = ?"
            params.append(media_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        if format:
            query += " AND format = ?"
            params.append(format)
        
        query += " ORDER BY indexed_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
    
    def update_media_status(self, media_id: int, status: str):
        """Update media status"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE media SET status = ? WHERE id = ?",
                (status, media_id)
            )
            conn.commit()
    
    def delete_media(self, media_id: int):
        """Delete media and associated analysis"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM media WHERE id = ?", (media_id,))
            conn.commit()
    
    # ========================================
    # ANALYSIS OPERATIONS
    # ========================================
    
    def add_analysis(
        self,
        media_id: int,
        analysis_type: str,
        result: Dict,
        score: float = None
    ) -> int:
        """
        Add analysis result.
        
        Args:
            media_id: Media ID
            analysis_type: Type of analysis (clip, quality, caption, etc.)
            result: Analysis result dict (stored as JSON)
            score: Optional numeric score
            
        Returns:
            Analysis record ID
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO analysis (media_id, analysis_type, result_json, score)
                VALUES (?, ?, ?, ?)
            """, (media_id, analysis_type, json.dumps(result), score))
            conn.commit()
            return cursor.lastrowid
    
    def get_analysis(self, media_id: int, analysis_type: str = None) -> List[Dict]:
        """Get analysis results for media"""
        with self.get_connection() as conn:
            if analysis_type:
                rows = conn.execute(
                    "SELECT * FROM analysis WHERE media_id = ? AND analysis_type = ?",
                    (media_id, analysis_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM analysis WHERE media_id = ?",
                    (media_id,)
                ).fetchall()
            
            results = []
            for row in rows:
                d = dict(row)
                d['result'] = json.loads(d.pop('result_json', '{}'))
                results.append(d)
            return results
    
    def get_unanalyzed_media(self, analysis_type: str, limit: int = 100) -> List[Dict]:
        """Get media that hasn't been analyzed with specific type"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT m.* FROM media m
                WHERE m.id NOT IN (
                    SELECT media_id FROM analysis WHERE analysis_type = ?
                )
                LIMIT ?
            """, (analysis_type, limit)).fetchall()
            return [dict(r) for r in rows]
    
    # ========================================
    # STATISTICS
    # ========================================
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            stats = {
                'total_media': conn.execute("SELECT COUNT(*) FROM media").fetchone()[0],
                'total_images': conn.execute(
                    "SELECT COUNT(*) FROM media WHERE media_type = 'image'"
                ).fetchone()[0],
                'total_videos': conn.execute(
                    "SELECT COUNT(*) FROM media WHERE media_type = 'video'"
                ).fetchone()[0],
                'total_analyzed': conn.execute(
                    "SELECT COUNT(DISTINCT media_id) FROM analysis"
                ).fetchone()[0],
                'total_size_mb': conn.execute(
                    "SELECT COALESCE(SUM(file_size), 0) / 1048576.0 FROM media"
                ).fetchone()[0],
                'by_status': {},
                'by_format': {},
                'analysis_types': {}
            }
            
            # By status
            for row in conn.execute(
                "SELECT status, COUNT(*) FROM media GROUP BY status"
            ):
                stats['by_status'][row[0] or 'unknown'] = row[1]
            
            # By format
            for row in conn.execute(
                "SELECT format, COUNT(*) FROM media GROUP BY format ORDER BY COUNT(*) DESC LIMIT 10"
            ):
                stats['by_format'][row[0] or 'unknown'] = row[1]
            
            # Analysis types
            for row in conn.execute(
                "SELECT analysis_type, COUNT(*) FROM analysis GROUP BY analysis_type"
            ):
                stats['analysis_types'][row[0]] = row[1]
            
            return stats
    
    # ========================================
    # INDEXING SESSIONS
    # ========================================
    
    def start_session(self, source_path: str) -> int:
        """Start a new indexing session"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO index_sessions (source_path, started_at, status)
                VALUES (?, ?, 'running')
            """, (source_path, datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def update_session(self, session_id: int, files_found: int = None, files_indexed: int = None):
        """Update session progress"""
        with self.get_connection() as conn:
            if files_found is not None:
                conn.execute(
                    "UPDATE index_sessions SET files_found = ? WHERE id = ?",
                    (files_found, session_id)
                )
            if files_indexed is not None:
                conn.execute(
                    "UPDATE index_sessions SET files_indexed = ? WHERE id = ?",
                    (files_indexed, session_id)
                )
            conn.commit()
    
    def complete_session(self, session_id: int, status: str = 'completed'):
        """Complete indexing session"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE index_sessions 
                SET completed_at = ?, status = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), status, session_id))
            conn.commit()
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent indexing sessions"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM index_sessions 
                ORDER BY started_at DESC LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]


# Singleton instance
_db_instance = None

def get_database(db_path: Path = None) -> DatabaseManager:
    """Get database singleton"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance


if __name__ == "__main__":
    # Test database
    db = DatabaseManager()
    
    print_section("Database Test")
    
    # Add test media
    test_record = MediaRecord(
        file_path="/test/image.jpg",
        file_name="image.jpg",
        file_size=1024,
        media_type="image",
        format="jpg",
        width=1920,
        height=1080,
        status="indexed"
    )
    
    media_id = db.add_media(test_record)
    print_success(f"Added media ID: {media_id}")
    
    # Get stats
    stats = db.get_stats()
    print_info(f"Stats: {stats}")
