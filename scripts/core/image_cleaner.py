"""
LORAFORGE - IMAGE CLEANER
Advanced image deduplication and quality filtering
Extracted and improved from anime-lora-pipeline
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
import json
import shutil
from datetime import datetime

# Try to import imagehash, provide fallback
try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False
    print("⚠ imagehash not installed. Run: pip install imagehash")

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_progress


@dataclass
class QualityCheckResult:
    """Result of quality check"""
    passed: bool
    resolution_ok: bool
    blur_ok: bool
    brightness_ok: bool
    width: int
    height: int
    blur_score: float
    brightness: float
    rejection_reasons: List[str]


@dataclass
class CleaningStats:
    """Statistics from cleaning operation"""
    input_images: int
    duplicates_removed: int
    quality_failed: int
    output_images: int
    duplicate_groups: int
    processing_time: float


class ImageCleaner:
    """
    Advanced image cleaning with:
    - Perceptual hash-based deduplication
    - Quality filtering (resolution, blur, brightness)
    - Best-of-duplicates selection
    - Detailed reporting
    """
    
    def __init__(
        self,
        min_resolution: Tuple[int, int] = (512, 512),
        blur_threshold: float = 100.0,
        brightness_range: Tuple[float, float] = (30, 225),
        hash_size: int = 8,
        hash_threshold: int = 5
    ):
        """
        Initialize ImageCleaner.
        
        Args:
            min_resolution: Minimum (width, height)
            blur_threshold: Below this = blurry (Laplacian variance)
            brightness_range: Acceptable (min, max) brightness
            hash_size: Perceptual hash size (8 = 64-bit hash)
            hash_threshold: Max Hamming distance for duplicates
        """
        self.min_resolution = min_resolution
        self.blur_threshold = blur_threshold
        self.brightness_range = brightness_range
        self.hash_size = hash_size
        self.hash_threshold = hash_threshold
    
    def check_quality(self, image_path: Path) -> QualityCheckResult:
        """
        Check image quality against thresholds.
        
        Args:
            image_path: Path to image
            
        Returns:
            QualityCheckResult with all metrics
        """
        reasons = []
        
        try:
            # Load image
            img = cv2.imread(str(image_path))
            if img is None:
                return QualityCheckResult(
                    passed=False, resolution_ok=False, blur_ok=False,
                    brightness_ok=False, width=0, height=0,
                    blur_score=0, brightness=0, rejection_reasons=["failed_to_load"]
                )
            
            h, w = img.shape[:2]
            
            # Resolution check
            resolution_ok = w >= self.min_resolution[0] and h >= self.min_resolution[1]
            if not resolution_ok:
                reasons.append(f"low_resolution_{w}x{h}")
            
            # Convert to grayscale for blur/brightness
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Blur check (Laplacian variance)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_ok = blur_score >= self.blur_threshold
            if not blur_ok:
                reasons.append(f"blurry_{blur_score:.1f}")
            
            # Brightness check
            brightness = np.mean(gray)
            brightness_ok = self.brightness_range[0] <= brightness <= self.brightness_range[1]
            if not brightness_ok:
                reasons.append(f"brightness_{brightness:.1f}")
            
            passed = resolution_ok and blur_ok and brightness_ok
            
            return QualityCheckResult(
                passed=passed,
                resolution_ok=resolution_ok,
                blur_ok=blur_ok,
                brightness_ok=brightness_ok,
                width=w,
                height=h,
                blur_score=float(blur_score),
                brightness=float(brightness),
                rejection_reasons=reasons
            )
            
        except Exception as e:
            return QualityCheckResult(
                passed=False, resolution_ok=False, blur_ok=False,
                brightness_ok=False, width=0, height=0,
                blur_score=0, brightness=0, rejection_reasons=[f"error_{str(e)}"]
            )
    
    def compute_hash(self, image_path: Path) -> Optional[str]:
        """
        Compute perceptual hash for image.
        
        Args:
            image_path: Path to image
            
        Returns:
            Hash string or None if failed
        """
        if not HAS_IMAGEHASH:
            return None
            
        try:
            img = Image.open(image_path)
            return str(imagehash.phash(img, hash_size=self.hash_size))
        except Exception as e:
            print_error(f"Hash failed for {image_path.name}: {e}")
            return None
    
    def compute_all_hashes(self, image_paths: List[Path]) -> Dict[Path, str]:
        """
        Compute hashes for all images.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Dict mapping paths to hashes
        """
        print_section("Computing Perceptual Hashes")
        
        hashes = {}
        total = len(image_paths)
        
        for i, path in enumerate(image_paths):
            hash_val = self.compute_hash(path)
            if hash_val:
                hashes[path] = hash_val
            print_progress(i + 1, total, "Hashing")
        
        print_success(f"Hashed {len(hashes)}/{total} images")
        return hashes
    
    def find_duplicates(self, image_hashes: Dict[Path, str]) -> List[List[Path]]:
        """
        Find duplicate images based on hash similarity.
        
        Args:
            image_hashes: Dict of paths to hashes
            
        Returns:
            List of duplicate groups
        """
        if not HAS_IMAGEHASH:
            return []
            
        print_section("Finding Duplicates")
        
        # Convert to hash objects
        hash_objects = {
            path: imagehash.hex_to_hash(hash_str)
            for path, hash_str in image_hashes.items()
        }
        
        duplicate_groups = []
        processed = set()
        total = len(hash_objects)
        
        for i, (path1, hash1) in enumerate(hash_objects.items()):
            if path1 in processed:
                continue
            
            # Find similar images
            group = [path1]
            
            for path2, hash2 in hash_objects.items():
                if path1 == path2 or path2 in processed:
                    continue
                
                # Hamming distance
                distance = hash1 - hash2
                
                if distance <= self.hash_threshold:
                    group.append(path2)
                    processed.add(path2)
            
            if len(group) > 1:
                duplicate_groups.append(group)
            
            processed.add(path1)
            print_progress(i + 1, total, "Comparing")
        
        print_info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups
    
    def select_best_from_group(self, group: List[Path]) -> Path:
        """
        Select the best quality image from a duplicate group.
        
        Args:
            group: List of duplicate image paths
            
        Returns:
            Path to best image
        """
        best_path = group[0]
        best_score = -1
        
        for path in group:
            result = self.check_quality(path)
            
            # Score: blur + resolution weighted
            score = result.blur_score + (result.width * result.height) / 10000
            
            if score > best_score:
                best_score = score
                best_path = path
        
        return best_path
    
    def clean_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        remove_duplicates: bool = True,
        remove_low_quality: bool = True,
        copy_files: bool = True,
        save_report: bool = True
    ) -> CleaningStats:
        """
        Clean an image directory.
        
        Args:
            input_dir: Input directory
            output_dir: Output directory
            remove_duplicates: Deduplicate images
            remove_low_quality: Filter quality
            copy_files: Actually copy (False = dry run)
            save_report: Save JSON report
            
        Returns:
            CleaningStats with results
        """
        import time
        start_time = time.time()
        
        print_section(f"Cleaning: {input_dir.name}")
        
        # Ensure output exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all images
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp']
        all_images = []
        for ext in extensions:
            all_images.extend(input_dir.glob(ext))
        
        print_info(f"Found {len(all_images)} images")
        
        stats = {
            'input_images': len(all_images),
            'duplicates_removed': 0,
            'quality_failed': 0,
            'duplicate_groups': 0
        }
        
        working_set = list(all_images)
        rejected = []
        
        # Step 1: Remove duplicates
        if remove_duplicates and len(working_set) > 1 and HAS_IMAGEHASH:
            hashes = self.compute_all_hashes(working_set)
            duplicate_groups = self.find_duplicates(hashes)
            
            stats['duplicate_groups'] = len(duplicate_groups)
            
            # Keep only best from each group
            to_remove = set()
            for group in duplicate_groups:
                best = self.select_best_from_group(group)
                for img in group:
                    if img != best:
                        to_remove.add(img)
                        rejected.append((img, "duplicate"))
            
            working_set = [img for img in working_set if img not in to_remove]
            stats['duplicates_removed'] = len(to_remove)
            print_info(f"Removed {len(to_remove)} duplicates")
        
        # Step 2: Quality filter
        if remove_low_quality:
            print_section("Quality Filtering")
            
            passed = []
            total = len(working_set)
            
            for i, img_path in enumerate(working_set):
                result = self.check_quality(img_path)
                
                if result.passed:
                    passed.append(img_path)
                else:
                    rejected.append((img_path, ", ".join(result.rejection_reasons)))
                
                print_progress(i + 1, total, "Checking")
            
            stats['quality_failed'] = len(working_set) - len(passed)
            working_set = passed
            print_success(f"Passed: {len(passed)}, Failed: {stats['quality_failed']}")
        
        stats['output_images'] = len(working_set)
        
        # Step 3: Copy files
        if copy_files:
            print_section("Copying Clean Images")
            
            for i, img_path in enumerate(working_set):
                dst = output_dir / img_path.name
                shutil.copy2(img_path, dst)
                print_progress(i + 1, len(working_set), "Copying")
            
            print_success(f"Copied {len(working_set)} images to {output_dir}")
        
        # Calculate time
        elapsed = time.time() - start_time
        
        # Save report
        if save_report:
            report = {
                'timestamp': datetime.now().isoformat(),
                'input_dir': str(input_dir),
                'output_dir': str(output_dir),
                'statistics': stats,
                'processing_time_seconds': elapsed,
                'cleaned_images': [str(p) for p in working_set],
                'rejected_images': [(str(p), r) for p, r in rejected]
            }
            
            report_path = output_dir / "cleaning_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print_info(f"Report: {report_path}")
        
        # Summary
        print_section("Cleaning Summary")
        print_info(f"Input: {stats['input_images']}")
        print_info(f"Duplicates removed: {stats['duplicates_removed']}")
        print_info(f"Quality failed: {stats['quality_failed']}")
        print_success(f"Output: {stats['output_images']}")
        print_info(f"Time: {elapsed:.2f}s")
        
        return CleaningStats(
            input_images=stats['input_images'],
            duplicates_removed=stats['duplicates_removed'],
            quality_failed=stats['quality_failed'],
            output_images=stats['output_images'],
            duplicate_groups=stats['duplicate_groups'],
            processing_time=elapsed
        )


def clean_images(input_dir: Path, output_dir: Path) -> CleaningStats:
    """Quick function to clean images"""
    cleaner = ImageCleaner()
    return cleaner.clean_directory(input_dir, output_dir)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean and deduplicate images")
    parser.add_argument("input_dir", type=Path, help="Input directory")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    parser.add_argument("--no-dedup", action="store_true", help="Skip deduplication")
    parser.add_argument("--no-quality", action="store_true", help="Skip quality filter")
    parser.add_argument("--dry-run", action="store_true", help="Don't copy files")
    
    args = parser.parse_args()
    
    cleaner = ImageCleaner()
    stats = cleaner.clean_directory(
        input_dir=args.input_dir,
        output_dir=args.output,
        remove_duplicates=not args.no_dedup,
        remove_low_quality=not args.no_quality,
        copy_files=not args.dry_run
    )
