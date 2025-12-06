"""
VIDEO PROCESSING API
=====================
Extracts frames from videos for training data.
Integrates PySceneDetect for intelligent keyframe extraction.

Port: 8206
"""
import os
import sys
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import hashlib

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
DATA_DIR = CIVITAI_PATH / "data"
OUTPUT_DIR = CIVITAI_PATH / "output" / "frames"
VIDEO_DIR = Path("G:/Downloads/Vid")  # 55GB video source
DB_PATH = DATA_DIR / "video_processing.db"

# Ensure directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
CORS(app)


class VideoProcessingDB:
    """Database for video processing"""
    
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE,
                filename TEXT,
                filesize INTEGER,
                duration_seconds REAL,
                status TEXT DEFAULT 'pending',
                approved BOOLEAN,
                rejection_reason TEXT,
                frames_extracted INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                frame_number INTEGER,
                timestamp_seconds REAL,
                filepath TEXT,
                quality_score REAL,
                is_scene_change BOOLEAN DEFAULT FALSE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(id)
            );
            
            CREATE TABLE IF NOT EXISTS processing_stats (
                id INTEGER PRIMARY KEY,
                total_videos INTEGER DEFAULT 0,
                processed_videos INTEGER DEFAULT 0,
                approved_videos INTEGER DEFAULT 0,
                rejected_videos INTEGER DEFAULT 0,
                total_frames INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Initialize stats
        if not self.conn.execute('SELECT 1 FROM processing_stats WHERE id = 1').fetchone():
            self.conn.execute('INSERT INTO processing_stats (id) VALUES (1)')
        
        self.conn.commit()
    
    def add_video(self, filepath: str) -> int:
        path = Path(filepath)
        cursor = self.conn.execute('''
            INSERT OR IGNORE INTO videos (filepath, filename, filesize)
            VALUES (?, ?, ?)
        ''', (str(path), path.name, path.stat().st_size if path.exists() else 0))
        self.conn.commit()
        
        row = self.conn.execute('SELECT id FROM videos WHERE filepath = ?', (str(path),)).fetchone()
        return row[0] if row else cursor.lastrowid
    
    def update_video_status(self, video_id: int, status: str, approved: bool = None, 
                           rejection_reason: str = None, frames_extracted: int = None):
        updates = ['status = ?', 'processed_at = ?']
        values = [status, datetime.now().isoformat()]
        
        if approved is not None:
            updates.append('approved = ?')
            values.append(approved)
        if rejection_reason:
            updates.append('rejection_reason = ?')
            values.append(rejection_reason)
        if frames_extracted is not None:
            updates.append('frames_extracted = ?')
            values.append(frames_extracted)
        
        values.append(video_id)
        self.conn.execute(f'UPDATE videos SET {", ".join(updates)} WHERE id = ?', values)
        self.conn.commit()
    
    def add_frame(self, video_id: int, frame_number: int, timestamp: float, 
                  filepath: str, quality_score: float = 0, is_scene_change: bool = False):
        self.conn.execute('''
            INSERT INTO frames (video_id, frame_number, timestamp_seconds, filepath, quality_score, is_scene_change)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (video_id, frame_number, timestamp, filepath, quality_score, is_scene_change))
        self.conn.commit()
    
    def get_stats(self) -> Dict:
        videos = self.conn.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed,
                SUM(CASE WHEN approved = 1 THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN approved = 0 THEN 1 ELSE 0 END) as rejected
            FROM videos
        ''').fetchone()
        
        frames = self.conn.execute('SELECT COUNT(*) FROM frames').fetchone()[0]
        
        return {
            'total_videos': videos[0] or 0,
            'processed_videos': videos[1] or 0,
            'approved_videos': videos[2] or 0,
            'rejected_videos': videos[3] or 0,
            'total_frames': frames
        }
    
    def get_pending_videos(self, limit: int = 10) -> List[Dict]:
        rows = self.conn.execute('''
            SELECT * FROM videos WHERE status = 'pending' LIMIT ?
        ''', (limit,)).fetchall()
        return [dict(r) for r in rows]


db = VideoProcessingDB()


class VideoProcessor:
    """Process videos and extract frames"""
    
    def __init__(self):
        self.processing = False
        self.current_video = None
    
    def scan_video_folder(self, folder: str = None) -> Dict:
        """Scan folder for videos"""
        folder = Path(folder) if folder else VIDEO_DIR
        
        if not folder.exists():
            return {"success": False, "error": f"Folder not found: {folder}"}
        
        extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm'}
        videos_found = 0
        
        for video_file in folder.rglob('*'):
            if video_file.suffix.lower() in extensions:
                db.add_video(str(video_file))
                videos_found += 1
        
        return {
            "success": True,
            "videos_found": videos_found,
            "folder": str(folder)
        }
    
    def extract_frames(self, video_id: int, interval_seconds: float = 3.0,
                       use_scene_detect: bool = True) -> Dict:
        """Extract frames from video"""
        
        row = db.conn.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()
        if not row:
            return {"success": False, "error": "Video not found"}
        
        video_path = Path(row['filepath'])
        if not video_path.exists():
            return {"success": False, "error": f"Video file not found: {video_path}"}
        
        db.update_video_status(video_id, 'processing')
        
        # Create output folder for this video
        video_hash = hashlib.md5(str(video_path).encode()).hexdigest()[:8]
        frame_dir = OUTPUT_DIR / video_hash
        frame_dir.mkdir(parents=True, exist_ok=True)
        
        frames_extracted = 0
        
        try:
            if use_scene_detect:
                # Use PySceneDetect for intelligent keyframes
                frames_extracted = self._extract_with_scene_detect(video_path, frame_dir, video_id)
            else:
                # Simple interval-based extraction
                frames_extracted = self._extract_by_interval(video_path, frame_dir, video_id, interval_seconds)
            
            db.update_video_status(video_id, 'processed', approved=True, frames_extracted=frames_extracted)
            
            return {
                "success": True,
                "video_id": video_id,
                "frames_extracted": frames_extracted,
                "output_folder": str(frame_dir)
            }
        
        except Exception as e:
            db.update_video_status(video_id, 'failed', approved=False, rejection_reason=str(e))
            return {"success": False, "error": str(e)}
    
    def _extract_by_interval(self, video_path: Path, output_dir: Path, 
                              video_id: int, interval: float) -> int:
        """Extract frames at fixed intervals using FFmpeg"""
        
        output_pattern = str(output_dir / "frame_%04d.png")
        
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-vf', f'fps=1/{interval}',
            '-q:v', '2',
            output_pattern,
            '-y'
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=300)
        except FileNotFoundError:
            # FFmpeg not in PATH, try common locations
            for ffmpeg_path in ['C:/ffmpeg/bin/ffmpeg.exe', 'ffmpeg']:
                cmd[0] = ffmpeg_path
                try:
                    subprocess.run(cmd, capture_output=True, check=True, timeout=300)
                    break
                except:
                    continue
        
        # Count extracted frames and add to database
        frames = list(output_dir.glob('frame_*.png'))
        for i, frame_path in enumerate(frames):
            db.add_frame(video_id, i, i * interval, str(frame_path))
        
        return len(frames)
    
    def _extract_with_scene_detect(self, video_path: Path, output_dir: Path, 
                                    video_id: int) -> int:
        """Extract frames at scene changes using PySceneDetect"""
        try:
            from scenedetect import detect, ContentDetector
            from scenedetect.video_splitter import split_video_ffmpeg
            
            # Detect scenes
            scene_list = detect(str(video_path), ContentDetector())
            
            frames_extracted = 0
            for i, scene in enumerate(scene_list):
                start_time = scene[0].get_seconds()
                
                # Extract frame at scene start
                output_path = output_dir / f"scene_{i:04d}.png"
                
                cmd = [
                    'ffmpeg', '-ss', str(start_time),
                    '-i', str(video_path),
                    '-vframes', '1',
                    '-q:v', '2',
                    str(output_path),
                    '-y'
                ]
                
                try:
                    subprocess.run(cmd, capture_output=True, check=True, timeout=30)
                    db.add_frame(video_id, i, start_time, str(output_path), is_scene_change=True)
                    frames_extracted += 1
                except:
                    continue
            
            return frames_extracted
        
        except ImportError:
            # PySceneDetect not installed, fallback to interval
            return self._extract_by_interval(video_path, output_dir, video_id, 3.0)


processor = VideoProcessor()


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route('/api/videos/scan', methods=['POST'])
def scan_videos():
    """Scan folder for videos"""
    data = request.json or {}
    folder = data.get('folder', str(VIDEO_DIR))
    return jsonify(processor.scan_video_folder(folder))


@app.route('/api/videos/list', methods=['GET'])
def list_videos():
    """List all videos"""
    status = request.args.get('status', 'all')
    limit = int(request.args.get('limit', 100))
    
    if status == 'all':
        rows = db.conn.execute('SELECT * FROM videos LIMIT ?', (limit,)).fetchall()
    else:
        rows = db.conn.execute('SELECT * FROM videos WHERE status = ? LIMIT ?', (status, limit)).fetchall()
    
    return jsonify({
        "success": True,
        "count": len(rows),
        "videos": [dict(r) for r in rows]
    })


@app.route('/api/videos/<int:video_id>/extract', methods=['POST'])
def extract_video_frames(video_id: int):
    """Extract frames from video"""
    data = request.json or {}
    interval = data.get('interval_seconds', 3.0)
    use_scene_detect = data.get('use_scene_detect', True)
    
    return jsonify(processor.extract_frames(video_id, interval, use_scene_detect))


@app.route('/api/videos/batch-extract', methods=['POST'])
def batch_extract():
    """Extract frames from multiple videos"""
    data = request.json or {}
    limit = data.get('limit', 10)
    
    pending = db.get_pending_videos(limit)
    
    results = []
    for video in pending:
        result = processor.extract_frames(video['id'])
        results.append({
            "video_id": video['id'],
            "filename": video['filename'],
            "success": result.get('success', False),
            "frames": result.get('frames_extracted', 0)
        })
    
    return jsonify({
        "success": True,
        "processed": len(results),
        "results": results
    })


@app.route('/api/frames', methods=['GET'])
def list_frames():
    """List extracted frames"""
    video_id = request.args.get('video_id')
    limit = int(request.args.get('limit', 100))
    
    if video_id:
        rows = db.conn.execute(
            'SELECT * FROM frames WHERE video_id = ? LIMIT ?', 
            (video_id, limit)
        ).fetchall()
    else:
        rows = db.conn.execute('SELECT * FROM frames LIMIT ?', (limit,)).fetchall()
    
    return jsonify({
        "success": True,
        "count": len(rows),
        "frames": [dict(r) for r in rows]
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get processing statistics"""
    return jsonify({
        "success": True,
        **db.get_stats()
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "success": True,
        "service": "Video Processing API",
        "version": "1.0.0",
        "stats": db.get_stats()
    })


@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        "service": "Video Processing API",
        "version": "1.0.0",
        "port": 8206,
        "endpoints": {
            "scan": "POST /api/videos/scan",
            "list": "GET /api/videos/list",
            "extract": "POST /api/videos/{id}/extract",
            "batch": "POST /api/videos/batch-extract",
            "frames": "GET /api/frames",
            "stats": "GET /api/stats",
            "health": "GET /api/health"
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  VIDEO PROCESSING API")
    print("  Port: 8206")
    print("=" * 60)
    print(f"\n📂 Video Source: {VIDEO_DIR}")
    print(f"📁 Output Dir: {OUTPUT_DIR}")
    print("\nEndpoints:")
    print("  POST /api/videos/scan        - Scan folder for videos")
    print("  GET  /api/videos/list        - List videos")
    print("  POST /api/videos/{id}/extract - Extract frames")
    print("  POST /api/videos/batch-extract - Batch extract")
    print("  GET  /api/frames             - List frames")
    print("  GET  /api/stats              - Processing stats")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8206, debug=False)
