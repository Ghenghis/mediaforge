"""
LORAFORGE - CLIP EVALUATOR
Advanced image quality and consistency evaluation using CLIP
Surpasses competitors by combining multiple metrics
"""

import torch
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import json
from datetime import datetime

# Lazy imports for optional dependencies
clip = None
clip_model = None
clip_preprocess = None

def ensure_clip_loaded(device: str = "cuda"):
    """Lazy load CLIP model"""
    global clip, clip_model, clip_preprocess
    if clip is None:
        try:
            import clip as clip_module
            clip = clip_module
            clip_model, clip_preprocess = clip.load("ViT-L/14", device=device)
            print(f"✓ CLIP model loaded on {device}")
        except ImportError:
            print("⚠ CLIP not installed. Run: pip install git+https://github.com/openai/CLIP.git")
            return False
    return True


@dataclass
class CLIPScore:
    """CLIP evaluation score"""
    image_path: str
    prompt: str
    score: float  # 0-100 scale
    
@dataclass  
class ConsistencyResult:
    """Character consistency result"""
    mean_similarity: float
    std_similarity: float
    min_similarity: float
    max_similarity: float
    num_images: int
    pairwise_scores: List[float]


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics"""
    resolution: int
    aspect_ratio: float
    mean_brightness: float
    std_brightness: float
    saturation: float
    sharpness: float  # Laplacian variance
    

@dataclass
class EvaluationResult:
    """Complete evaluation result for an image set"""
    timestamp: str
    num_images: int
    clip_scores: Dict[str, float]  # per-image scores
    consistency: ConsistencyResult
    quality_metrics: Dict[str, QualityMetrics]
    overall_score: float
    grade: str


class CLIPEvaluator:
    """
    Advanced CLIP-based evaluator for LoRA quality assessment.
    
    Features (surpassing competitors):
    - CLIP prompt adherence scoring
    - Character consistency across variations
    - Image quality metrics
    - Composite scoring with grades
    - Batch processing with progress
    - JSON export for tracking
    """
    
    def __init__(self, device: str = "cuda"):
        self.device = device
        self.model_loaded = False
        
    def _ensure_loaded(self) -> bool:
        """Ensure CLIP is loaded"""
        if not self.model_loaded:
            self.model_loaded = ensure_clip_loaded(self.device)
        return self.model_loaded
    
    def score_image_prompt(self, image_path: Path, prompt: str) -> float:
        """
        Calculate CLIP score between image and prompt.
        
        Args:
            image_path: Path to image
            prompt: Text prompt to compare against
            
        Returns:
            Score 0-100 (higher = better match)
        """
        if not self._ensure_loaded():
            return 0.0
            
        try:
            image = Image.open(image_path).convert("RGB")
            image_input = clip_preprocess(image).unsqueeze(0).to(self.device)
            text_input = clip.tokenize([prompt]).to(self.device)
            
            with torch.no_grad():
                image_features = clip_model.encode_image(image_input)
                text_features = clip_model.encode_text(text_input)
                
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                # Cosine similarity
                similarity = (image_features @ text_features.T).squeeze()
            
            # Convert to 0-100 scale
            return float(similarity.cpu()) * 100
            
        except Exception as e:
            print(f"Error scoring {image_path}: {e}")
            return 0.0
    
    def calculate_consistency(self, image_paths: List[Path]) -> ConsistencyResult:
        """
        Calculate visual consistency across multiple images.
        Used to measure character consistency in LoRA outputs.
        
        Args:
            image_paths: List of image paths to compare
            
        Returns:
            ConsistencyResult with statistics
        """
        if not self._ensure_loaded():
            return ConsistencyResult(0, 0, 0, 0, 0, [])
            
        if len(image_paths) < 2:
            return ConsistencyResult(100, 0, 100, 100, len(image_paths), [100])
        
        # Encode all images
        features = []
        for img_path in image_paths:
            try:
                image = Image.open(img_path).convert("RGB")
                image_input = clip_preprocess(image).unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    feat = clip_model.encode_image(image_input)
                    feat = feat / feat.norm(dim=-1, keepdim=True)
                    features.append(feat)
            except Exception as e:
                print(f"Error encoding {img_path}: {e}")
                continue
        
        if len(features) < 2:
            return ConsistencyResult(0, 0, 0, 0, len(features), [])
        
        # Stack features
        features = torch.cat(features, dim=0)
        
        # Calculate pairwise similarities
        similarities = []
        n = len(features)
        for i in range(n):
            for j in range(i + 1, n):
                sim = float((features[i] @ features[j].T).cpu()) * 100
                similarities.append(sim)
        
        similarities = np.array(similarities)
        
        return ConsistencyResult(
            mean_similarity=float(similarities.mean()),
            std_similarity=float(similarities.std()),
            min_similarity=float(similarities.min()),
            max_similarity=float(similarities.max()),
            num_images=len(features),
            pairwise_scores=similarities.tolist()
        )
    
    def calculate_quality_metrics(self, image_path: Path) -> QualityMetrics:
        """
        Calculate comprehensive image quality metrics.
        
        Args:
            image_path: Path to image
            
        Returns:
            QualityMetrics dataclass
        """
        try:
            import cv2
            
            image = Image.open(image_path).convert("RGB")
            img_array = np.array(image)
            
            # Resolution
            resolution = image.width * image.height
            aspect_ratio = image.width / image.height
            
            # Brightness
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            mean_brightness = float(gray.mean())
            std_brightness = float(gray.std())
            
            # Saturation (from HSV)
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            saturation = float(hsv[:, :, 1].mean())
            
            # Sharpness (Laplacian variance)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = float(laplacian.var())
            
            return QualityMetrics(
                resolution=resolution,
                aspect_ratio=aspect_ratio,
                mean_brightness=mean_brightness,
                std_brightness=std_brightness,
                saturation=saturation,
                sharpness=sharpness
            )
            
        except Exception as e:
            print(f"Error calculating quality for {image_path}: {e}")
            return QualityMetrics(0, 0, 0, 0, 0, 0)
    
    def evaluate_batch(
        self,
        image_paths: List[Path],
        prompt: str = "",
        calculate_consistency: bool = True
    ) -> EvaluationResult:
        """
        Comprehensive evaluation of an image batch.
        
        Args:
            image_paths: List of image paths
            prompt: Optional prompt to score against
            calculate_consistency: Whether to calculate consistency
            
        Returns:
            EvaluationResult with all metrics
        """
        print(f"\n{'='*60}")
        print(f"CLIP EVALUATION - {len(image_paths)} images")
        print(f"{'='*60}\n")
        
        clip_scores = {}
        quality_metrics = {}
        
        # Score each image
        for i, img_path in enumerate(image_paths):
            print(f"  [{i+1}/{len(image_paths)}] {img_path.name}")
            
            # CLIP score (if prompt provided)
            if prompt:
                score = self.score_image_prompt(img_path, prompt)
                clip_scores[str(img_path)] = score
                print(f"    CLIP Score: {score:.1f}")
            
            # Quality metrics
            metrics = self.calculate_quality_metrics(img_path)
            quality_metrics[str(img_path)] = metrics
            print(f"    Sharpness: {metrics.sharpness:.1f}")
        
        # Consistency
        consistency = ConsistencyResult(0, 0, 0, 0, 0, [])
        if calculate_consistency and len(image_paths) >= 2:
            print("\nCalculating consistency...")
            consistency = self.calculate_consistency(image_paths)
            print(f"  Mean Similarity: {consistency.mean_similarity:.1f}%")
            print(f"  Std: {consistency.std_similarity:.1f}%")
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            clip_scores, consistency, quality_metrics
        )
        
        # Determine grade
        grade = self._score_to_grade(overall_score)
        
        result = EvaluationResult(
            timestamp=datetime.now().isoformat(),
            num_images=len(image_paths),
            clip_scores=clip_scores,
            consistency=consistency,
            quality_metrics={k: asdict(v) for k, v in quality_metrics.items()},
            overall_score=overall_score,
            grade=grade
        )
        
        print(f"\n{'='*60}")
        print(f"OVERALL SCORE: {overall_score:.2f} | GRADE: {grade}")
        print(f"{'='*60}\n")
        
        return result
    
    def _calculate_overall_score(
        self,
        clip_scores: Dict[str, float],
        consistency: ConsistencyResult,
        quality_metrics: Dict[str, QualityMetrics]
    ) -> float:
        """Calculate weighted overall score"""
        scores = []
        
        # CLIP scores (if available)
        if clip_scores:
            avg_clip = np.mean(list(clip_scores.values()))
            # Normalize: CLIP typically 20-35, map to 0-10
            clip_normalized = min(10, max(0, (avg_clip - 15) / 2))
            scores.append(('clip', clip_normalized, 0.3))
        
        # Consistency (if available)
        if consistency.num_images >= 2:
            # Map 70-100% to 0-10
            cons_normalized = min(10, max(0, (consistency.mean_similarity - 70) / 3))
            scores.append(('consistency', cons_normalized, 0.3))
        
        # Quality (sharpness)
        if quality_metrics:
            avg_sharpness = np.mean([
                m.sharpness if isinstance(m, QualityMetrics) else m.get('sharpness', 0)
                for m in quality_metrics.values()
            ])
            # Map 100-1000 to 0-10
            sharp_normalized = min(10, max(0, avg_sharpness / 100))
            scores.append(('sharpness', sharp_normalized, 0.4))
        
        if not scores:
            return 0.0
        
        # Weighted average
        total_weight = sum(s[2] for s in scores)
        weighted_sum = sum(s[1] * s[2] for s in scores)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _score_to_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 9.0:
            return "S+"
        elif score >= 8.5:
            return "S"
        elif score >= 8.0:
            return "A+"
        elif score >= 7.5:
            return "A"
        elif score >= 7.0:
            return "A-"
        elif score >= 6.5:
            return "B+"
        elif score >= 6.0:
            return "B"
        elif score >= 5.5:
            return "B-"
        elif score >= 5.0:
            return "C"
        else:
            return "D"
    
    def save_evaluation(self, result: EvaluationResult, output_path: Path):
        """Save evaluation results to JSON"""
        data = {
            'timestamp': result.timestamp,
            'num_images': result.num_images,
            'clip_scores': result.clip_scores,
            'consistency': asdict(result.consistency),
            'quality_metrics': result.quality_metrics,
            'overall_score': result.overall_score,
            'grade': result.grade
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Evaluation saved to {output_path}")
    
    def compare_versions(
        self,
        version_dirs: Dict[str, Path],
        prompt: str = ""
    ) -> Dict[str, EvaluationResult]:
        """
        Compare multiple model versions.
        
        Args:
            version_dirs: Dict mapping version names to image directories
            prompt: Optional prompt to score against
            
        Returns:
            Dict of version names to evaluation results
        """
        print(f"\n{'='*60}")
        print("MODEL VERSION COMPARISON")
        print(f"{'='*60}\n")
        
        results = {}
        
        for version_name, dir_path in version_dirs.items():
            print(f"\n--- {version_name} ---")
            
            if not dir_path.exists():
                print(f"  Directory not found: {dir_path}")
                continue
            
            # Find images
            images = list(dir_path.glob("*.png")) + list(dir_path.glob("*.jpg"))
            
            if not images:
                print(f"  No images found")
                continue
            
            # Evaluate
            result = self.evaluate_batch(images, prompt)
            results[version_name] = result
        
        # Print comparison
        print(f"\n{'='*60}")
        print("COMPARISON SUMMARY")
        print(f"{'='*60}\n")
        
        print(f"{'Version':<15} {'Score':<8} {'Grade':<6} {'Consistency':<12} {'Images':<8}")
        print("-" * 60)
        
        for name, result in sorted(results.items(), key=lambda x: x[1].overall_score, reverse=True):
            cons = result.consistency.mean_similarity if result.consistency.num_images >= 2 else 0
            print(f"{name:<15} {result.overall_score:<8.2f} {result.grade:<6} {cons:<12.1f} {result.num_images:<8}")
        
        return results


# Convenience function
def evaluate_images(image_paths: List[Path], prompt: str = "") -> EvaluationResult:
    """Quick evaluation of images"""
    evaluator = CLIPEvaluator()
    return evaluator.evaluate_batch(image_paths, prompt)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CLIP-based image evaluation")
    parser.add_argument("image_dir", type=Path, help="Directory with images")
    parser.add_argument("--prompt", type=str, default="", help="Prompt to score against")
    parser.add_argument("--output", type=Path, help="Output JSON path")
    
    args = parser.parse_args()
    
    evaluator = CLIPEvaluator()
    
    images = list(args.image_dir.glob("*.png")) + list(args.image_dir.glob("*.jpg"))
    result = evaluator.evaluate_batch(images, args.prompt)
    
    if args.output:
        evaluator.save_evaluation(result, args.output)
