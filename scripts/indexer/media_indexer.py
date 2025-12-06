"""
LORAFORGE - MEDIA INDEXER
Complete media indexing with analysis integration
Ties together all features into unified system

CAPABILITIES:
- Scan all image/video formats
- Extract metadata and compute hashes
- Run all analysis features
- Store in database with tags
- Enable self-learning from results
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Generator, Tuple
from datetime import datetime
from dataclasses import dataclass
import json
import cv2
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning, print_progress

from indexer.database import DatabaseManager, MediaRecord, get_database
from indexer.self_learning_data import SelfLearningDataManager, Tag, TagCategory, get_learning_manager


# ============================================
# SUPPORTED FORMATS
# ============================================

IMAGE_FORMATS = {
    # Standard
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif',
    # Modern
    '.avif', '.heic', '.heif', '.jfif', '.jp2', '.jpx', '.j2k',
    # RAW
    '.cr2', '.cr3', '.nef', '.arw', '.dng', '.orf', '.rw2', '.pef',
    '.srw', '.raf', '.raw', '.3fr', '.bay', '.dcr', '.erf', '.kdc',
    '.mef', '.mrw', '.nrw', '.ptx', '.rwl', '.sr2', '.srf', '.x3f',
    # Other
    '.ico', '.psd', '.xcf', '.tga', '.exr', '.hdr', '.pcx'
}

VIDEO_FORMATS = {
    # Common
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm',
    # Streaming
    '.m4v', '.flv', '.f4v', '.ts', '.m2ts', '.mts',
    # Legacy
    '.mpeg', '.mpg', '.vob', '.3gp', '.3g2', '.asf',
    # Professional
    '.mxf', '.prores',
    # Other
    '.ogv', '.rm', '.rmvb', '.divx', '.m2v'
}


@dataclass
class IndexResult:
    """Result of indexing operation"""
    total_found: int = 0
    indexed: int = 0
    skipped: int = 0
    errors: int = 0
    duplicates: int = 0
    elapsed_seconds: float = 0


class MediaIndexer:
    """
    Complete media indexing system.
    
    Features:
    - Scan directories for all media types
    - Extract metadata (dimensions, duration, etc.)
    - Compute file hashes for deduplication
    - Run analysis pipeline (quality, CLIP, captions)
    - Store in database with full provenance
    - Enable self-learning from results
    """
    
    def __init__(
        self,
        db_path: Path = None,
        compute_hashes: bool = True,
        run_analysis: bool = True,
        auto_tag: bool = True
    ):
        """
        Initialize indexer.
        
        Args:
            db_path: Path to database
            compute_hashes: Compute file hashes
            run_analysis: Run analysis features
            auto_tag: Auto-generate tags
        """
        self.db = get_database(db_path)
        self.learning = get_learning_manager(db_path)
        
        self.compute_hashes = compute_hashes
        self.run_analysis = run_analysis
        self.auto_tag = auto_tag
        
        # Analysis modules (lazy loaded)
        self._image_cleaner = None
        self._clip_evaluator = None
        self._auto_captioner = None
    
    def _get_media_type(self, path: Path) -> Optional[str]:
        """Determine media type from extension"""
        ext = path.suffix.lower()
        if ext in IMAGE_FORMATS:
            return 'image'
        elif ext in VIDEO_FORMATS:
            return 'video'
        return None
    
    def _compute_hash(self, path: Path) -> Optional[str]:
        """Compute SHA256 hash of file"""
        try:
            hasher = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print_warning(f"Hash failed: {path.name}: {e}")
            return None
    
    def _get_image_metadata(self, path: Path) -> Dict:
        """Extract image metadata"""
        try:
            with Image.open(path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
        except Exception as e:
            # Try OpenCV as fallback
            try:
                img = cv2.imread(str(path))
                if img is not None:
                    h, w = img.shape[:2]
                    return {'width': w, 'height': h}
            except:
                pass
            return {}
    
    def _get_video_metadata(self, path: Path) -> Dict:
        """Extract video metadata"""
        try:
            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                return {}
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                'width': width,
                'height': height,
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration
            }
        except Exception as e:
            return {}
    
    def _scan_directory(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Generator[Path, None, None]:
        """Scan directory for media files"""
        all_formats = IMAGE_FORMATS | VIDEO_FORMATS
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    path = Path(root) / file
                    if path.suffix.lower() in all_formats:
                        yield path
        else:
            for path in directory.iterdir():
                if path.is_file() and not path.name.startswith('.'):
                    if path.suffix.lower() in all_formats:
                        yield path
    
    def index_file(self, path: Path) -> Optional[int]:
        """
        Index a single media file.
        
        Args:
            path: Path to file
            
        Returns:
            Media ID or None if failed
        """
        path = Path(path)
        
        if not path.exists():
            return None
        
        media_type = self._get_media_type(path)
        if not media_type:
            return None
        
        # Get file stats
        stat = path.stat()
        
        # Compute hash if enabled
        file_hash = self._compute_hash(path) if self.compute_hashes else None
        
        # Check for duplicates
        if file_hash:
            existing = self.db.get_media_by_hash(file_hash)
            if existing:
                # Already indexed, return existing ID
                return existing[0]['id']
        
        # Get metadata based on type
        if media_type == 'image':
            meta = self._get_image_metadata(path)
        else:
            meta = self._get_video_metadata(path)
        
        # Create record
        record = MediaRecord(
            file_path=str(path.absolute()),
            file_name=path.name,
            file_hash=file_hash,
            file_size=stat.st_size,
            media_type=media_type,
            format=path.suffix.lower().lstrip('.'),
            width=meta.get('width', 0),
            height=meta.get('height', 0),
            duration=meta.get('duration'),
            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            status='indexed'
        )
        
        # Add to database
        media_id = self.db.add_media(record)
        
        # Add source tags
        if self.auto_tag:
            tags = [
                Tag(media_type, TagCategory.SOURCE.value, 1.0, "auto"),
                Tag(record.format, TagCategory.SOURCE.value, 1.0, "auto"),
            ]
            
            # Size tags
            if record.file_size > 10 * 1024 * 1024:  # > 10MB
                tags.append(Tag("large_file", TagCategory.SOURCE.value, 0.9, "auto"))
            
            # Resolution tags
            if record.width >= 1920 or record.height >= 1080:
                tags.append(Tag("high_resolution", TagCategory.QUALITY.value, 0.9, "auto"))
            elif record.width < 512 or record.height < 512:
                tags.append(Tag("low_resolution", TagCategory.QUALITY.value, 0.9, "auto"))
            
            self.learning.add_tags_batch(media_id, tags)
        
        return media_id
    
    def index_directory(
        self,
        directory: Path,
        recursive: bool = True,
        analyze: bool = None
    ) -> IndexResult:
        """
        Index all media in a directory.
        
        Args:
            directory: Directory to scan
            recursive: Scan subdirectories
            analyze: Run analysis (None = use default)
            
        Returns:
            IndexResult with statistics
        """
        import time
        start_time = time.time()
        
        directory = Path(directory)
        
        print_section(f"Indexing: {directory}")
        
        # Start session
        session_id = self.db.start_session(str(directory))
        
        result = IndexResult()
        
        # First pass: count files
        print_info("Scanning for media files...")
        files = list(self._scan_directory(directory, recursive))
        result.total_found = len(files)
        
        self.db.update_session(session_id, files_found=result.total_found)
        
        print_info(f"Found {result.total_found} media files")
        
        # Second pass: index files
        for i, path in enumerate(files):
            try:
                # Check if already indexed
                existing = self.db.get_media_by_path(str(path.absolute()))
                
                if existing:
                    result.skipped += 1
                else:
                    media_id = self.index_file(path)
                    
                    if media_id:
                        result.indexed += 1
                    else:
                        result.errors += 1
                
            except Exception as e:
                print_warning(f"Error indexing {path.name}: {e}")
                result.errors += 1
            
            # Update progress
            self.db.update_session(session_id, files_indexed=result.indexed)
            print_progress(i + 1, result.total_found, "Indexing")
        
        # Complete session
        elapsed = time.time() - start_time
        result.elapsed_seconds = elapsed
        
        self.db.complete_session(session_id)
        
        # Summary
        print_section("Indexing Complete")
        print_info(f"Total found: {result.total_found}")
        print_success(f"Indexed: {result.indexed}")
        print_info(f"Skipped: {result.skipped}")
        if result.errors > 0:
            print_warning(f"Errors: {result.errors}")
        print_info(f"Time: {elapsed:.2f}s")
        
        # Run analysis if enabled
        if analyze or (analyze is None and self.run_analysis):
            self.analyze_unprocessed()
        
        return result
    
    def analyze_media(self, media_id: int, analysis_types: List[str] = None):
        """
        Run analysis on a specific media item.
        
        Args:
            media_id: Media ID
            analysis_types: Types to run (None = all applicable)
        """
        media = self.db.get_media(media_id)
        if not media:
            return
        
        path = Path(media['file_path'])
        if not path.exists():
            return
        
        analysis_types = analysis_types or ['quality', 'clip', 'caption']
        
        # Quality analysis
        if 'quality' in analysis_types and media['media_type'] == 'image':
            self._analyze_quality(media_id, path)
        
        # CLIP evaluation
        if 'clip' in analysis_types and media['media_type'] == 'image':
            self._analyze_clip(media_id, path)
        
        # Auto caption
        if 'caption' in analysis_types and media['media_type'] == 'image':
            self._analyze_caption(media_id, path)
        
        # Update status
        self.db.update_media_status(media_id, 'analyzed')
    
    def _analyze_quality(self, media_id: int, path: Path):
        """Run quality analysis"""
        try:
            if self._image_cleaner is None:
                from core.image_cleaner import ImageCleaner
                self._image_cleaner = ImageCleaner()
            
            result = self._image_cleaner.check_quality(path)
            
            # Store analysis
            self.db.add_analysis(
                media_id,
                'quality',
                {
                    'passed': result.passed,
                    'blur_score': result.blur_score,
                    'brightness': result.brightness,
                    'resolution_ok': result.resolution_ok
                },
                score=result.blur_score
            )
            
            # Auto-tag based on quality
            if self.auto_tag:
                tags = []
                if result.passed:
                    tags.append(Tag("quality_passed", TagCategory.QUALITY.value, 0.9, "auto"))
                if not result.blur_ok:
                    tags.append(Tag("blurry", TagCategory.QUALITY.value, 0.9, "auto"))
                if not result.brightness_ok:
                    tags.append(Tag("bad_lighting", TagCategory.QUALITY.value, 0.9, "auto"))
                
                if tags:
                    self.learning.add_tags_batch(media_id, tags)
                    
        except Exception as e:
            print_warning(f"Quality analysis failed: {e}")
    
    def _analyze_clip(self, media_id: int, path: Path):
        """Run CLIP analysis"""
        try:
            if self._clip_evaluator is None:
                from core.clip_evaluator import CLIPEvaluator
                self._clip_evaluator = CLIPEvaluator()
            
            # Get quality metrics
            metrics = self._clip_evaluator.calculate_quality_metrics(path)
            
            self.db.add_analysis(
                media_id,
                'clip_quality',
                {
                    'sharpness': metrics.sharpness,
                    'brightness': metrics.mean_brightness,
                    'saturation': metrics.saturation
                },
                score=metrics.sharpness
            )
            
        except Exception as e:
            print_warning(f"CLIP analysis failed: {e}")
    
    def _analyze_caption(self, media_id: int, path: Path):
        """Run auto-captioning"""
        try:
            if self._auto_captioner is None:
                from core.auto_captioner import AutoCaptioner
                self._auto_captioner = AutoCaptioner(mode="wd14")
            
            caption = self._auto_captioner.generate_caption(path)
            
            self.db.add_analysis(
                media_id,
                'caption',
                {'caption': caption},
                score=None
            )
            
            # Parse tags from caption
            if self.auto_tag and caption:
                tags = [t.strip() for t in caption.split(',')[:20]]  # First 20 tags
                for tag in tags:
                    if tag:
                        self.learning.add_tag(
                            media_id, tag, TagCategory.CONTENT.value, 0.8, "auto_caption"
                        )
                        
        except Exception as e:
            print_warning(f"Caption analysis failed: {e}")
    
    def analyze_unprocessed(self, limit: int = 100):
        """Analyze media that hasn't been processed yet"""
        print_section("Analyzing Unprocessed Media")
        
        # Get unanalyzed images
        unanalyzed = self.db.get_unanalyzed_media('quality', limit)
        
        if not unanalyzed:
            print_info("No unanalyzed media found")
            return
        
        print_info(f"Analyzing {len(unanalyzed)} items")
        
        for i, media in enumerate(unanalyzed):
            self.analyze_media(media['id'])
            print_progress(i + 1, len(unanalyzed), "Analyzing")
        
        print_success("Analysis complete")
    
    def get_stats(self) -> Dict:
        """Get indexer statistics"""
        db_stats = self.db.get_stats()
        learning_summary = self.learning.get_learning_summary()
        
        return {
            **db_stats,
            'learning': learning_summary
        }
    
    def search(
        self,
        media_type: str = None,
        tags: List[str] = None,
        status: str = None,
        min_quality: float = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search indexed media.
        
        Args:
            media_type: Filter by type
            tags: Filter by tags (must have all)
            status: Filter by status
            min_quality: Minimum quality score
            limit: Max results
            
        Returns:
            List of media records
        """
        # Start with base query
        results = self.db.list_media(
            media_type=media_type,
            status=status,
            limit=limit * 2  # Get extra for filtering
        )
        
        # Filter by tags
        if tags:
            tag_media_ids = set(self.learning.find_by_tags(tags, match_all=True, limit=10000))
            results = [r for r in results if r['id'] in tag_media_ids]
        
        # Filter by quality
        if min_quality is not None:
            filtered = []
            for r in results:
                analysis = self.db.get_analysis(r['id'], 'quality')
                if analysis and analysis[0].get('score', 0) >= min_quality:
                    filtered.append(r)
            results = filtered
        
        return results[:limit]


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def index_directory(directory: Path, recursive: bool = True) -> IndexResult:
    """Quick function to index a directory"""
    indexer = MediaIndexer()
    return indexer.index_directory(directory, recursive)


def get_indexer() -> MediaIndexer:
    """Get singleton indexer"""
    return MediaIndexer()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Media Indexer")
    parser.add_argument("directory", type=Path, nargs="?", help="Directory to index")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--analyze", action="store_true", help="Analyze unprocessed")
    parser.add_argument("--no-recursive", action="store_true", help="Don't scan subdirectories")
    
    args = parser.parse_args()
    
    indexer = MediaIndexer()
    
    if args.stats:
        stats = indexer.get_stats()
        print_section("Indexer Statistics")
        print(json.dumps(stats, indent=2))
    elif args.analyze:
        indexer.analyze_unprocessed()
    elif args.directory:
        indexer.index_directory(args.directory, recursive=not args.no_recursive)
    else:
        print("Usage: python media_indexer.py <directory> or --stats or --analyze")
