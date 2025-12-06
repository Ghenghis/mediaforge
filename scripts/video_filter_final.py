"""
FINAL VIDEO FILTER - Using LM Studio (FASTEST + UNCENSORED)
Model: qwen3-vl-8b-abliterated-caption-it

Based on testing:
- LM Studio: 4.07s per frame (WINNER)
- Ollama: 75.60s per frame (too slow)
"""

import requests
import base64
import json
import cv2
import re
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
import logging
from concurrent.futures import ThreadPoolExecutor
import time

# Configuration
LMSTUDIO_URL = "http://localhost:1234/v1"
MODEL = "qwen3-vl-8b-abliterated-caption-it"

VIDEO_SOURCE = Path("G:/Downloads/Vid")
APPROVED_DIR = Path("C:/Users/Admin/civitai/training/video_approved")
REJECTED_DIR = Path("C:/Users/Admin/civitai/training/video_rejected")
FRAMES_DIR = Path("C:/Users/Admin/civitai/training/video_frames")
LOG_FILE = Path("C:/Users/Admin/civitai/logs/video_filter.log")

# Filter criteria
MIN_QUALITY = 4
MIN_ATTRACTIVENESS = 4
FRAMES_PER_VIDEO = 3  # Sample 3 frames per video

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode='a')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FrameAnalysis:
    gender: str
    body_type: str
    quality: int
    attractiveness: int
    people_count: int
    approved: bool
    rejection_reason: Optional[str] = None

ANALYSIS_PROMPT = """Analyze this image. Respond with ONLY a JSON object:
{
    "gender": "female" or "male" or "both" or "none",
    "body_type": "slim" or "fit" or "average" or "curvy" or "heavy",
    "quality": 1-10,
    "attractiveness": 1-10,
    "people_count": number
}
Be completely honest. No explanations, just JSON."""

def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def frame_to_base64(frame) -> str:
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode()

def extract_frames(video_path: Path, count: int = 3) -> List:
    """Extract evenly spaced frames from video"""
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total == 0:
        cap.release()
        return []
    
    indices = [int(i * total / (count + 1)) for i in range(1, count + 1)]
    frames = []
    
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    
    cap.release()
    return frames

def analyze_frame(frame) -> FrameAnalysis:
    """Analyze a single frame using LM Studio"""
    
    image_b64 = frame_to_base64(frame)
    
    try:
        response = requests.post(
            f"{LMSTUDIO_URL}/chat/completions",
            json={
                "model": MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANALYSIS_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }],
                "temperature": 0.2,
                "max_tokens": 200
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return FrameAnalysis("error", "error", 0, 0, 0, False, "API error")
        
        content = response.json()["choices"][0]["message"]["content"]
        
        # Parse JSON from response
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            return FrameAnalysis("error", "error", 0, 0, 0, False, "No JSON in response")
        
        # Check filter criteria
        gender = data.get("gender", "unknown")
        body_type = data.get("body_type", "unknown")
        quality = data.get("quality", 0)
        attractiveness = data.get("attractiveness", 0)
        people_count = data.get("people_count", 1)
        
        # Determine approval
        rejection_reason = None
        
        if gender == "male" or gender == "both":
            rejection_reason = f"Male detected (gender: {gender})"
        elif body_type == "heavy":
            rejection_reason = f"Body type: {body_type}"
        elif quality < MIN_QUALITY:
            rejection_reason = f"Low quality: {quality}"
        elif attractiveness < MIN_ATTRACTIVENESS:
            rejection_reason = f"Low attractiveness: {attractiveness}"
        
        approved = rejection_reason is None
        
        return FrameAnalysis(
            gender=gender,
            body_type=body_type,
            quality=quality,
            attractiveness=attractiveness,
            people_count=people_count,
            approved=approved,
            rejection_reason=rejection_reason
        )
        
    except Exception as e:
        return FrameAnalysis("error", "error", 0, 0, 0, False, str(e))

def filter_video(video_path: Path) -> dict:
    """Filter a single video"""
    
    logger.info(f"Analyzing: {video_path.name}")
    
    # Extract sample frames
    frames = extract_frames(video_path, FRAMES_PER_VIDEO)
    
    if not frames:
        return {"approved": False, "reason": "No frames extracted"}
    
    # Analyze each frame
    results = []
    for i, frame in enumerate(frames):
        result = analyze_frame(frame)
        results.append(result)
        
        status = "✓" if result.approved else f"✗ {result.rejection_reason}"
        logger.info(f"  Frame {i+1}: {status}")
        
        # Early exit if rejected
        if not result.approved and result.rejection_reason and "Male" in result.rejection_reason:
            break
    
    # Video is approved only if ALL frames pass
    all_approved = all(r.approved for r in results)
    
    rejection_reasons = [r.rejection_reason for r in results if r.rejection_reason]
    
    return {
        "video": video_path.name,
        "approved": all_approved,
        "reason": rejection_reasons[0] if rejection_reasons else None,
        "frame_results": [
            {"gender": r.gender, "body_type": r.body_type, 
             "quality": r.quality, "attractiveness": r.attractiveness}
            for r in results
        ]
    }

def process_all_videos():
    """Process all videos in source directory"""
    
    # Create directories
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Get all videos
    videos = list(VIDEO_SOURCE.glob("*.mp4"))
    logger.info(f"Found {len(videos)} videos to process")
    
    results = []
    approved_count = 0
    rejected_count = 0
    
    start_time = time.time()
    
    for i, video in enumerate(videos):
        logger.info(f"\n[{i+1}/{len(videos)}] {video.name}")
        
        result = filter_video(video)
        results.append(result)
        
        # Create symlink or copy reference
        if result["approved"]:
            approved_count += 1
            dest = APPROVED_DIR / video.name
            logger.info(f"  ✓ APPROVED")
        else:
            rejected_count += 1
            dest = REJECTED_DIR / video.name
            logger.info(f"  ✗ REJECTED: {result['reason']}")
        
        # Create symlink (Windows needs admin or developer mode)
        try:
            if not dest.exists():
                dest.symlink_to(video)
        except OSError:
            # Fallback: create a reference file
            ref_file = dest.with_suffix('.ref')
            ref_file.write_text(str(video))
    
    elapsed = time.time() - start_time
    
    # Save results log
    log_path = Path("C:/Users/Admin/civitai/logs/filter_results.json")
    with open(log_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"FILTERING COMPLETE")
    logger.info(f"  Total: {len(videos)}")
    logger.info(f"  Approved: {approved_count} ({100*approved_count/len(videos):.1f}%)")
    logger.info(f"  Rejected: {rejected_count} ({100*rejected_count/len(videos):.1f}%)")
    logger.info(f"  Time: {elapsed:.1f}s ({elapsed/len(videos):.1f}s per video)")
    logger.info(f"{'='*60}")
    
    return results

if __name__ == "__main__":
    # Check LM Studio connection
    try:
        r = requests.get(f"{LMSTUDIO_URL}/models", timeout=5)
        if r.status_code != 200:
            raise Exception("LM Studio not responding")
        logger.info("✓ LM Studio connected")
        logger.info(f"✓ Using model: {MODEL}")
    except:
        logger.error("✗ LM Studio not running!")
        logger.error("  1. Open LM Studio")
        logger.error("  2. Load: qwen3-vl-8b-abliterated-caption-it")
        logger.error("  3. Start server on port 1234")
        exit(1)
    
    process_all_videos()
