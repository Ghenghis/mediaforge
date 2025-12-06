"""
LORAFORGE - MASTER PIPELINE ORCHESTRATOR
Complete video-to-model pipeline with stage management
Surpasses all competitors with comprehensive automation
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import (
    setup_logger, get_logger, print_section, print_success,
    print_error, print_info, print_warning, StageTimer
)
from utils.config_loader import load_config, get_filter_config, ensure_paths


@dataclass
class StageResult:
    """Result from a pipeline stage"""
    name: str
    status: str  # success, failed, skipped
    elapsed_time: float
    output_path: Optional[str]
    stats: Dict[str, Any]
    error: Optional[str]


@dataclass
class PipelineResult:
    """Complete pipeline execution result"""
    status: str
    start_time: str
    end_time: str
    total_time: float
    stages: List[StageResult]
    final_output: Optional[str]


class LoRAForgePipeline:
    """
    Master pipeline orchestrator for LoRAForge.
    
    Stages:
    1. Video Discovery - Find and validate videos
    2. Frame Extraction - Extract frames at key positions
    3. Vision Analysis - AI analysis of frame content
    4. Quality Filtering - Apply filtering criteria
    5. Image Cleaning - Deduplicate and quality check
    6. Dataset Preparation - Prepare for training
    7. (Optional) CLIP Evaluation - Score dataset quality
    
    Features that surpass competitors:
    - Stage-based execution with timing
    - Error handling and recovery
    - Progress reporting
    - Comprehensive logging
    - Config-driven parameters
    - Real-time dashboard integration
    """
    
    def __init__(self, config_path: str = "config/global_config.yaml"):
        """
        Initialize pipeline.
        
        Args:
            config_path: Path to config file
        """
        try:
            self.config = load_config(config_path)
        except FileNotFoundError:
            print_warning("Config not found, using defaults")
            self.config = self._default_config()
        
        self.logger = setup_logger("LoRAForge", Path(self.config.get("paths", {}).get("logs", "logs")))
        self.stages: List[StageResult] = []
        self.start_time = None
        self.dashboard_api = self.config.get("dashboard", {}).get("api", {}).get("port", 8500)
    
    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            "paths": {
                "video_source": "G:/Downloads/Vid",
                "training_root": "C:/Users/Admin/civitai/training",
                "video_frames": "C:/Users/Admin/civitai/training/video_frames",
                "logs": "C:/Users/Admin/civitai/logs"
            },
            "filtering": {
                "gender": {"required": "female"},
                "quality": {"min_score": 4},
                "attractiveness": {"min_score": 4}
            },
            "vision_model": {
                "primary": {
                    "url": "http://localhost:1234/v1",
                    "model": "qwen3-vl-8b-abliterated-caption-it"
                }
            }
        }
    
    def run_stage(
        self,
        name: str,
        func,
        skip_on_error: bool = False
    ) -> StageResult:
        """
        Execute a pipeline stage with tracking.
        
        Args:
            name: Stage name
            func: Function to execute
            skip_on_error: Continue pipeline if this stage fails
            
        Returns:
            StageResult
        """
        print_section(f"STAGE: {name}")
        self.logger.info(f"Starting stage: {name}")
        
        start = time.time()
        result = StageResult(
            name=name,
            status="running",
            elapsed_time=0,
            output_path=None,
            stats={},
            error=None
        )
        
        try:
            output = func()
            elapsed = time.time() - start
            
            result.status = "success"
            result.elapsed_time = elapsed
            
            if isinstance(output, dict):
                result.stats = output
                result.output_path = output.get("output_path")
            elif isinstance(output, Path):
                result.output_path = str(output)
            
            print_success(f"{name} completed in {elapsed:.2f}s")
            self.logger.info(f"Completed {name} in {elapsed:.2f}s")
            
        except Exception as e:
            elapsed = time.time() - start
            result.status = "failed"
            result.elapsed_time = elapsed
            result.error = str(e)
            
            print_error(f"{name} failed: {e}")
            self.logger.error(f"Stage {name} failed: {e}")
            
            if not skip_on_error:
                raise
        
        self.stages.append(result)
        self._update_dashboard(result)
        
        return result
    
    def _update_dashboard(self, stage_result: StageResult):
        """Send stage update to dashboard API"""
        try:
            import requests
            requests.post(
                f"http://localhost:{self.dashboard_api}/api/task/current",
                json={
                    "stage": stage_result.name,
                    "video_name": "",
                    "current_frame": 0,
                    "total_frames": 0,
                    "processing_time": stage_result.elapsed_time
                },
                timeout=2
            )
        except:
            pass  # Dashboard may not be running
    
    # ========================================
    # STAGE IMPLEMENTATIONS
    # ========================================
    
    def stage_video_discovery(self, source_dir: Path = None) -> Dict:
        """
        Stage 1: Discover and validate video files.
        """
        if source_dir is None:
            source_dir = Path(self.config["paths"]["video_source"])
        
        print_info(f"Scanning: {source_dir}")
        
        # Find video files
        extensions = ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.wmv', '*.webm']
        videos = []
        for ext in extensions:
            videos.extend(source_dir.glob(ext))
        
        # Validate and get info
        valid_videos = []
        total_size = 0
        
        for video in videos:
            if video.stat().st_size > 1024:  # > 1KB
                valid_videos.append(video)
                total_size += video.stat().st_size
        
        print_info(f"Found {len(valid_videos)} videos ({total_size / 1e9:.2f} GB)")
        
        return {
            "videos": [str(v) for v in valid_videos],
            "count": len(valid_videos),
            "total_size_gb": total_size / 1e9,
            "output_path": str(source_dir)
        }
    
    def stage_frame_extraction(
        self,
        video_paths: List[Path],
        output_dir: Path = None,
        frames_per_video: int = 3,
        positions: List[float] = [0.25, 0.5, 0.75]
    ) -> Dict:
        """
        Stage 2: Extract frames from videos at specified positions.
        """
        import cv2
        
        if output_dir is None:
            output_dir = Path(self.config["paths"]["video_frames"])
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        extracted = []
        failed = []
        
        for i, video_path in enumerate(video_paths):
            video_path = Path(video_path)
            print_info(f"[{i+1}/{len(video_paths)}] {video_path.name}")
            
            try:
                cap = cv2.VideoCapture(str(video_path))
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                if total_frames < 10:
                    failed.append((video_path, "too_short"))
                    cap.release()
                    continue
                
                for j, pos in enumerate(positions):
                    frame_num = int(total_frames * pos)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                    ret, frame = cap.read()
                    
                    if ret:
                        frame_path = output_dir / f"{video_path.stem}_f{j+1}.jpg"
                        cv2.imwrite(str(frame_path), frame)
                        extracted.append({
                            "video": video_path.name,
                            "frame": str(frame_path),
                            "position": pos
                        })
                
                cap.release()
                
            except Exception as e:
                failed.append((video_path, str(e)))
        
        print_success(f"Extracted {len(extracted)} frames from {len(video_paths)} videos")
        
        return {
            "extracted": len(extracted),
            "failed": len(failed),
            "output_path": str(output_dir),
            "frames": extracted
        }
    
    def stage_vision_analysis(
        self,
        frames_dir: Path,
        output_file: Path = None
    ) -> Dict:
        """
        Stage 3: Analyze frames using vision AI.
        """
        import requests
        import base64
        
        config = self.config.get("vision_model", {}).get("primary", {})
        api_url = config.get("url", "http://localhost:1234/v1")
        model = config.get("model", "qwen3-vl-8b-abliterated-caption-it")
        
        frames_dir = Path(frames_dir)
        frames = list(frames_dir.glob("*.jpg")) + list(frames_dir.glob("*.png"))
        
        results = []
        
        prompt = """Analyze this image and respond in JSON format:
{
    "gender": "male/female/unknown",
    "body_type": "slim/average/athletic/heavy",
    "quality": 1-10,
    "attractiveness": 1-10,
    "description": "brief description"
}"""
        
        for i, frame_path in enumerate(frames):
            print_info(f"[{i+1}/{len(frames)}] {frame_path.name}")
            
            try:
                # Encode image
                with open(frame_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                
                # Call API
                response = requests.post(
                    f"{api_url}/chat/completions",
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                                ]
                            }
                        ],
                        "max_tokens": 500
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    # Parse JSON from response
                    import re
                    json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                        analysis["frame"] = str(frame_path)
                        results.append(analysis)
                        
            except Exception as e:
                print_warning(f"Analysis failed: {e}")
                results.append({"frame": str(frame_path), "error": str(e)})
        
        # Save results
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
        
        return {
            "analyzed": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r]),
            "results": results
        }
    
    def stage_quality_filtering(
        self,
        analysis_results: List[Dict],
        frames_dir: Path,
        approved_dir: Path,
        rejected_dir: Path
    ) -> Dict:
        """
        Stage 4: Filter frames based on criteria.
        """
        import shutil
        
        filter_config = self.config.get("filtering", {})
        required_gender = filter_config.get("gender", {}).get("required", "female")
        min_quality = filter_config.get("quality", {}).get("min_score", 4)
        min_attractiveness = filter_config.get("attractiveness", {}).get("min_score", 4)
        excluded_body_types = filter_config.get("body_type", {}).get("exclude", ["heavy", "obese"])
        
        approved_dir.mkdir(parents=True, exist_ok=True)
        rejected_dir.mkdir(parents=True, exist_ok=True)
        
        approved = []
        rejected = []
        
        for result in analysis_results:
            if "error" in result:
                continue
            
            frame_path = Path(result.get("frame", ""))
            if not frame_path.exists():
                continue
            
            # Check criteria
            reasons = []
            
            gender = result.get("gender", "").lower()
            if required_gender and gender != required_gender:
                reasons.append(f"gender_{gender}")
            
            quality = result.get("quality", 0)
            if quality < min_quality:
                reasons.append(f"quality_{quality}")
            
            attractiveness = result.get("attractiveness", 0)
            if attractiveness < min_attractiveness:
                reasons.append(f"attractiveness_{attractiveness}")
            
            body_type = result.get("body_type", "").lower()
            if body_type in excluded_body_types:
                reasons.append(f"body_type_{body_type}")
            
            # Move file
            if reasons:
                dst = rejected_dir / frame_path.name
                shutil.copy2(frame_path, dst)
                rejected.append({"frame": frame_path.name, "reasons": reasons})
            else:
                dst = approved_dir / frame_path.name
                shutil.copy2(frame_path, dst)
                approved.append({"frame": frame_path.name, "analysis": result})
        
        print_success(f"Approved: {len(approved)}, Rejected: {len(rejected)}")
        
        return {
            "approved": len(approved),
            "rejected": len(rejected),
            "approval_rate": len(approved) / max(1, len(approved) + len(rejected)) * 100,
            "approved_frames": approved,
            "rejected_frames": rejected,
            "output_path": str(approved_dir)
        }
    
    def stage_image_cleaning(
        self,
        input_dir: Path,
        output_dir: Path
    ) -> Dict:
        """
        Stage 5: Clean and deduplicate images.
        """
        from core.image_cleaner import ImageCleaner
        
        cleaner = ImageCleaner(
            min_resolution=(512, 512),
            blur_threshold=100,
            hash_threshold=5
        )
        
        stats = cleaner.clean_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            remove_duplicates=True,
            remove_low_quality=True
        )
        
        return {
            "input": stats.input_images,
            "output": stats.output_images,
            "duplicates_removed": stats.duplicates_removed,
            "quality_failed": stats.quality_failed,
            "output_path": str(output_dir)
        }
    
    def stage_clip_evaluation(
        self,
        images_dir: Path,
        prompt: str = ""
    ) -> Dict:
        """
        Stage 6: CLIP evaluation of dataset quality.
        """
        from core.clip_evaluator import CLIPEvaluator
        
        evaluator = CLIPEvaluator()
        
        images = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
        
        if not images:
            return {"error": "No images found", "score": 0, "grade": "N/A"}
        
        result = evaluator.evaluate_batch(images, prompt)
        
        return {
            "num_images": result.num_images,
            "overall_score": result.overall_score,
            "grade": result.grade,
            "consistency": result.consistency.mean_similarity if result.consistency else 0
        }
    
    # ========================================
    # FULL PIPELINE
    # ========================================
    
    def run_full_pipeline(
        self,
        video_source: Path = None,
        output_root: Path = None,
        skip_stages: List[str] = None
    ) -> PipelineResult:
        """
        Run the complete pipeline.
        
        Args:
            video_source: Source directory with videos
            output_root: Root output directory
            skip_stages: Stage names to skip
            
        Returns:
            PipelineResult with all stage results
        """
        self.start_time = datetime.now()
        skip_stages = skip_stages or []
        
        print("\n" + "="*70)
        print("  LORAFORGE - FULL PIPELINE EXECUTION")
        print("="*70 + "\n")
        
        # Setup paths
        video_source = video_source or Path(self.config["paths"]["video_source"])
        output_root = output_root or Path(self.config["paths"]["training_root"])
        
        frames_dir = output_root / "01_frames"
        analysis_file = output_root / "02_analysis.json"
        approved_dir = output_root / "03_approved"
        rejected_dir = output_root / "03_rejected"
        cleaned_dir = output_root / "04_cleaned"
        
        try:
            # Stage 1: Video Discovery
            if "discovery" not in skip_stages:
                discovery = self.run_stage(
                    "Video Discovery",
                    lambda: self.stage_video_discovery(video_source)
                )
                video_paths = [Path(v) for v in discovery.stats.get("videos", [])]
            else:
                # Find existing videos
                video_paths = list(video_source.glob("*.mp4"))
            
            # Stage 2: Frame Extraction
            if "extraction" not in skip_stages:
                extraction = self.run_stage(
                    "Frame Extraction",
                    lambda: self.stage_frame_extraction(video_paths, frames_dir)
                )
            
            # Stage 3: Vision Analysis
            if "analysis" not in skip_stages:
                analysis = self.run_stage(
                    "Vision Analysis",
                    lambda: self.stage_vision_analysis(frames_dir, analysis_file)
                )
                analysis_results = analysis.stats.get("results", [])
            else:
                # Load existing
                if analysis_file.exists():
                    analysis_results = json.loads(analysis_file.read_text())
                else:
                    analysis_results = []
            
            # Stage 4: Quality Filtering
            if "filtering" not in skip_stages:
                filtering = self.run_stage(
                    "Quality Filtering",
                    lambda: self.stage_quality_filtering(
                        analysis_results, frames_dir, approved_dir, rejected_dir
                    )
                )
            
            # Stage 5: Image Cleaning
            if "cleaning" not in skip_stages:
                cleaning = self.run_stage(
                    "Image Cleaning",
                    lambda: self.stage_image_cleaning(approved_dir, cleaned_dir)
                )
            
            # Stage 6: CLIP Evaluation
            if "evaluation" not in skip_stages:
                evaluation = self.run_stage(
                    "CLIP Evaluation",
                    lambda: self.stage_clip_evaluation(cleaned_dir),
                    skip_on_error=True  # Non-critical
                )
            
            status = "success"
            final_output = str(cleaned_dir)
            
        except Exception as e:
            status = "failed"
            final_output = None
            print_error(f"Pipeline failed: {e}")
        
        # Calculate total time
        end_time = datetime.now()
        total_time = (end_time - self.start_time).total_seconds()
        
        # Create result
        result = PipelineResult(
            status=status,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_time=total_time,
            stages=self.stages,
            final_output=final_output
        )
        
        # Save pipeline report
        self._save_report(result, output_root)
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    def _save_report(self, result: PipelineResult, output_dir: Path):
        """Save pipeline report to JSON"""
        report = {
            "status": result.status,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "total_time_seconds": result.total_time,
            "stages": [asdict(s) for s in result.stages],
            "final_output": result.final_output
        }
        
        report_path = output_dir / "pipeline_report.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print_info(f"Report saved: {report_path}")
    
    def _print_summary(self, result: PipelineResult):
        """Print pipeline summary"""
        print("\n" + "="*70)
        print("  PIPELINE SUMMARY")
        print("="*70 + "\n")
        
        print(f"Status: {result.status.upper()}")
        print(f"Total Time: {result.total_time:.2f}s")
        print(f"Final Output: {result.final_output}")
        print()
        
        print(f"{'Stage':<25} {'Status':<10} {'Time':<10}")
        print("-" * 50)
        
        for stage in result.stages:
            status_icon = "✓" if stage.status == "success" else "✗"
            print(f"{stage.name:<25} {status_icon} {stage.status:<8} {stage.elapsed_time:.2f}s")
        
        print()


def main():
    """Run pipeline from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LoRAForge Pipeline")
    parser.add_argument("--source", type=Path, help="Video source directory")
    parser.add_argument("--output", type=Path, help="Output directory")
    parser.add_argument("--config", type=str, default="config/global_config.yaml")
    parser.add_argument("--skip", nargs="+", default=[], help="Stages to skip")
    
    args = parser.parse_args()
    
    pipeline = LoRAForgePipeline(args.config)
    result = pipeline.run_full_pipeline(
        video_source=args.source,
        output_root=args.output,
        skip_stages=args.skip
    )
    
    exit(0 if result.status == "success" else 1)


if __name__ == "__main__":
    main()
