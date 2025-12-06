"""
LORAFORGE - SCENE DETECTOR
Intelligent keyframe extraction using scene detection
Enhanced from anime-lora-pipeline with better error handling

HOW IT WORKS:
1. PySceneDetect analyzes frame-to-frame pixel changes
2. ContentDetector identifies scene boundaries
3. Extracts optimal frames from each scene (avoiding transitions)
4. Quality filtering on extracted frames
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime

# Lazy import for scenedetect (optional dependency)
scenedetect = None

def ensure_scenedetect():
    """Lazy load scenedetect"""
    global scenedetect
    if scenedetect is None:
        try:
            import scenedetect as sd
            from scenedetect import VideoManager, SceneManager
            from scenedetect.detectors import ContentDetector
            scenedetect = sd
            return True
        except ImportError:
            print("⚠ scenedetect not installed. Run: pip install scenedetect[opencv]")
            return False
    return True

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning, print_progress


class SceneDetector:
    """
    Intelligent scene-based frame extraction.
    
    Advantages over position-based extraction:
    - Avoids blurry transition frames
    - Captures scene beginnings (usually clearest)
    - Adapts to video content automatically
    - Better coverage of diverse content
    """
    
    def __init__(
        self,
        threshold: float = 27.0,
        min_scene_length: float = 1.0,
        min_resolution: Tuple[int, int] = (512, 512),
        blur_threshold: float = 100.0,
        brightness_range: Tuple[float, float] = (30, 225)
    ):
        """
        Initialize SceneDetector.
        
        Args:
            threshold: Scene detection sensitivity (lower = more sensitive)
            min_scene_length: Minimum scene duration in seconds
            min_resolution: Minimum frame resolution (width, height)
            blur_threshold: Laplacian variance threshold for blur
            brightness_range: Acceptable brightness range (min, max)
        """
        self.threshold = threshold
        self.min_scene_length = min_scene_length
        self.min_resolution = min_resolution
        self.blur_threshold = blur_threshold
        self.brightness_range = brightness_range
        
        self.use_scenedetect = ensure_scenedetect()
    
    def detect_scenes(self, video_path: Path) -> List[Tuple[float, float]]:
        """
        Detect scene boundaries in video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of (start_time, end_time) tuples in seconds
        """
        if not self.use_scenedetect:
            # Fallback: divide video into equal segments
            return self._fallback_scenes(video_path)
        
        print_info(f"Detecting scenes in {video_path.name}")
        
        try:
            from scenedetect import VideoManager, SceneManager
            from scenedetect.detectors import ContentDetector
            
            # Create managers
            video_manager = VideoManager([str(video_path)])
            scene_manager = SceneManager()
            
            # Get frame rate for min_scene_length calculation
            video_manager.start()
            fps = video_manager.get_framerate()
            video_manager.release()
            
            # Reinitialize for detection
            video_manager = VideoManager([str(video_path)])
            
            # Add detector
            scene_manager.add_detector(
                ContentDetector(
                    threshold=self.threshold,
                    min_scene_len=int(self.min_scene_length * fps)
                )
            )
            
            # Detect scenes
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()
            video_manager.release()
            
            # Convert to seconds
            scenes = [
                (scene[0].get_seconds(), scene[1].get_seconds())
                for scene in scene_list
            ]
            
            print_info(f"Detected {len(scenes)} scenes")
            return scenes
            
        except Exception as e:
            print_warning(f"Scene detection failed: {e}, using fallback")
            return self._fallback_scenes(video_path)
    
    def _fallback_scenes(self, video_path: Path, num_segments: int = 10) -> List[Tuple[float, float]]:
        """
        Fallback: divide video into equal segments.
        
        Args:
            video_path: Path to video
            num_segments: Number of segments to create
            
        Returns:
            List of (start, end) tuples
        """
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if fps <= 0 or total_frames <= 0:
            return []
        
        duration = total_frames / fps
        segment_length = duration / num_segments
        
        scenes = []
        for i in range(num_segments):
            start = i * segment_length
            end = (i + 1) * segment_length
            scenes.append((start, end))
        
        return scenes
    
    def check_frame_quality(self, frame: np.ndarray) -> Tuple[bool, Dict]:
        """
        Check if frame meets quality criteria.
        
        Args:
            frame: BGR frame from OpenCV
            
        Returns:
            (passes_check, metrics_dict)
        """
        metrics = {}
        
        try:
            h, w = frame.shape[:2]
            metrics['width'] = w
            metrics['height'] = h
            metrics['resolution_ok'] = w >= self.min_resolution[0] and h >= self.min_resolution[1]
            
            # Blur check
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            metrics['blur_score'] = float(blur_score)
            metrics['blur_ok'] = blur_score >= self.blur_threshold
            
            # Brightness check
            brightness = np.mean(gray)
            metrics['brightness'] = float(brightness)
            metrics['brightness_ok'] = self.brightness_range[0] <= brightness <= self.brightness_range[1]
            
            passed = metrics['resolution_ok'] and metrics['blur_ok'] and metrics['brightness_ok']
            return passed, metrics
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def extract_scene_frames(
        self,
        video_path: Path,
        scenes: List[Tuple[float, float]],
        output_dir: Path,
        frames_per_scene: int = 1,
        position: str = "start"  # start, middle, end
    ) -> List[Dict]:
        """
        Extract frames from detected scenes.
        
        Args:
            video_path: Path to video
            scenes: List of (start, end) scene times
            output_dir: Output directory
            frames_per_scene: Number of frames per scene
            position: Where in scene to extract (start/middle/end)
            
        Returns:
            List of extracted frame metadata
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print_error(f"Could not open video: {video_path}")
            return []
        
        extracted = []
        failed = []
        quality_rejected = []
        
        print_section(f"Extracting {len(scenes)} scenes from {video_path.name}")
        
        for i, (start, end) in enumerate(scenes):
            # Calculate timestamp based on position
            duration = end - start
            if position == "start":
                timestamp = start + 0.1  # Slightly after scene start
            elif position == "middle":
                timestamp = start + duration / 2
            else:  # end
                timestamp = end - 0.1
            
            # Seek to timestamp
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            
            if not ret:
                failed.append({'scene': i, 'timestamp': timestamp, 'reason': 'read_failed'})
                continue
            
            # Quality check
            passed, metrics = self.check_frame_quality(frame)
            
            if not passed:
                quality_rejected.append({
                    'scene': i,
                    'timestamp': timestamp,
                    'metrics': metrics
                })
                continue
            
            # Save frame
            frame_name = f"{video_path.stem}_scene{i:04d}_t{timestamp:.2f}s.jpg"
            frame_path = output_dir / frame_name
            
            cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            extracted.append({
                'frame': frame_name,
                'scene_idx': i,
                'timestamp': timestamp,
                'scene_duration': duration,
                'metrics': metrics
            })
            
            print_progress(i + 1, len(scenes), "Extracting")
        
        cap.release()
        
        print_success(f"Extracted {len(extracted)} frames")
        print_info(f"Failed: {len(failed)}, Quality rejected: {len(quality_rejected)}")
        
        return extracted
    
    def process_video(
        self,
        video_path: Path,
        output_dir: Path,
        save_metadata: bool = True
    ) -> Dict:
        """
        Full pipeline: detect scenes and extract frames.
        
        Args:
            video_path: Path to video
            output_dir: Output directory
            save_metadata: Save metadata JSON
            
        Returns:
            Processing statistics
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        
        # Detect scenes
        scenes = self.detect_scenes(video_path)
        
        if not scenes:
            return {'error': 'No scenes detected', 'video': video_path.name}
        
        # Extract frames
        extracted = self.extract_scene_frames(
            video_path, scenes, output_dir,
            frames_per_scene=1, position="start"
        )
        
        stats = {
            'video': video_path.name,
            'total_scenes': len(scenes),
            'frames_extracted': len(extracted),
            'output_dir': str(output_dir),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save metadata
        if save_metadata and extracted:
            metadata = {
                'video': video_path.name,
                'scenes': len(scenes),
                'extracted_frames': extracted,
                'stats': stats
            }
            
            meta_path = output_dir / f"{video_path.stem}_metadata.json"
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print_info(f"Metadata: {meta_path}")
        
        return stats
    
    def batch_process(
        self,
        video_dir: Path,
        output_dir: Path,
        max_videos: int = None
    ) -> List[Dict]:
        """
        Process multiple videos.
        
        Args:
            video_dir: Directory containing videos
            output_dir: Output root directory
            max_videos: Maximum videos to process (None = all)
            
        Returns:
            List of processing statistics
        """
        video_dir = Path(video_dir)
        output_dir = Path(output_dir)
        
        # Find videos
        extensions = ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.wmv', '*.webm']
        videos = []
        for ext in extensions:
            videos.extend(video_dir.glob(ext))
        
        if max_videos:
            videos = videos[:max_videos]
        
        print_section(f"Processing {len(videos)} videos")
        
        all_stats = []
        for i, video in enumerate(videos):
            print(f"\n[{i+1}/{len(videos)}] {video.name}")
            
            video_output = output_dir / video.stem
            stats = self.process_video(video, video_output)
            all_stats.append(stats)
        
        # Summary
        total_extracted = sum(s.get('frames_extracted', 0) for s in all_stats)
        print_success(f"\nTotal: {total_extracted} frames from {len(videos)} videos")
        
        return all_stats


def extract_with_scene_detection(video_path: Path, output_dir: Path) -> Dict:
    """Convenience function for scene-based extraction"""
    detector = SceneDetector()
    return detector.process_video(video_path, output_dir)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scene-based frame extraction")
    parser.add_argument("video", type=Path, help="Video file or directory")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    parser.add_argument("--threshold", type=float, default=27.0, help="Scene sensitivity")
    parser.add_argument("--batch", action="store_true", help="Process directory of videos")
    
    args = parser.parse_args()
    
    detector = SceneDetector(threshold=args.threshold)
    
    if args.batch:
        detector.batch_process(args.video, args.output)
    else:
        detector.process_video(args.video, args.output)
