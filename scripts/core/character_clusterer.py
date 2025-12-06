"""
LORAFORGE - CHARACTER CLUSTERER
Automatic character grouping using CLIP + HDBSCAN
Enhanced from anime-lora-pipeline with quality filtering

HOW IT WORKS:
1. Extract CLIP embeddings for all character images
2. Normalize embeddings to unit vectors
3. HDBSCAN clustering finds natural groupings
4. Quality filtering removes blurry/small images
5. Organize into character-specific folders
6. PCA visualization of cluster distribution

USE CASES:
- Group extracted frames by character
- Identify duplicate/similar images
- Create character-specific training sets
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image
import json
import shutil
from datetime import datetime
import cv2

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning, print_progress

# Lazy imports for optional dependencies
torch = None
clip = None
HDBSCAN = None
PCA = None
plt = None

def ensure_dependencies():
    """Lazy load optional dependencies"""
    global torch, clip, HDBSCAN, PCA, plt
    
    missing = []
    
    if torch is None:
        try:
            import torch as _torch
            torch = _torch
        except ImportError:
            missing.append("torch")
    
    if clip is None:
        try:
            import clip as _clip
            clip = _clip
        except ImportError:
            missing.append("clip (pip install git+https://github.com/openai/CLIP.git)")
    
    if HDBSCAN is None:
        try:
            from sklearn.cluster import HDBSCAN as _HDBSCAN
            HDBSCAN = _HDBSCAN
        except ImportError:
            missing.append("scikit-learn")
    
    if PCA is None:
        try:
            from sklearn.decomposition import PCA as _PCA
            PCA = _PCA
        except ImportError:
            pass  # Already caught above
    
    if plt is None:
        try:
            import matplotlib.pyplot as _plt
            plt = _plt
        except ImportError:
            missing.append("matplotlib")
    
    if missing:
        print_warning(f"Missing dependencies: {', '.join(missing)}")
        return False
    
    return True


class QualityFilter:
    """Filter low-quality character images"""
    
    def __init__(
        self,
        min_size: int = 64,
        blur_threshold: float = 100.0,
        min_content_coverage: float = 0.05
    ):
        """
        Initialize quality filter.
        
        Args:
            min_size: Minimum width/height in pixels
            blur_threshold: Laplacian variance threshold
            min_content_coverage: Minimum non-transparent pixel ratio
        """
        self.min_size = min_size
        self.blur_threshold = blur_threshold
        self.min_content_coverage = min_content_coverage
    
    def check_quality(self, image_path: Path) -> Dict:
        """
        Comprehensive quality check.
        
        Args:
            image_path: Path to image
            
        Returns:
            Dict with quality metrics and pass/fail
        """
        try:
            img = np.array(Image.open(image_path))
            h, w = img.shape[:2]
            
            # Size check
            size_ok = w >= self.min_size and h >= self.min_size
            
            # Blur check
            if len(img.shape) == 3:
                if img.shape[2] == 4:
                    gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_RGB2GRAY)
                else:
                    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            else:
                gray = img
            
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_ok = blur_score >= self.blur_threshold
            
            # Content coverage (for RGBA images)
            if len(img.shape) == 3 and img.shape[2] == 4:
                alpha = img[:, :, 3]
                coverage = (alpha > 0).sum() / alpha.size
                content_ok = coverage >= self.min_content_coverage
            else:
                coverage = 1.0
                content_ok = True
            
            return {
                'passed': size_ok and blur_ok and content_ok,
                'width': int(w),
                'height': int(h),
                'blur_score': float(blur_score),
                'coverage': float(coverage),
                'reasons': {
                    'size': size_ok,
                    'blur': blur_ok,
                    'content': content_ok
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'reasons': {'error': False}
            }


class CharacterClusterer:
    """
    CLIP-based character clustering with HDBSCAN.
    
    Automatically groups similar characters from extracted frames.
    """
    
    def __init__(
        self,
        model_name: str = "ViT-B/32",
        device: str = "cuda",
        min_cluster_size: int = 10,
        quality_filter: QualityFilter = None
    ):
        """
        Initialize character clusterer.
        
        Args:
            model_name: CLIP model (ViT-B/32, ViT-L/14)
            device: cuda or cpu
            min_cluster_size: Minimum images per cluster
            quality_filter: Optional QualityFilter instance
        """
        self.device = device
        self.min_cluster_size = min_cluster_size
        self.quality_filter = quality_filter or QualityFilter()
        
        self.model = None
        self.preprocess = None
        self.model_name = model_name
        self.loaded = False
    
    def load_model(self) -> bool:
        """Load CLIP model"""
        if self.loaded:
            return True
        
        if not ensure_dependencies():
            return False
        
        try:
            print_info(f"Loading CLIP model: {self.model_name}")
            self.model, self.preprocess = clip.load(self.model_name, device=self.device)
            self.model.eval()
            self.loaded = True
            print_success("CLIP model loaded")
            return True
        except Exception as e:
            print_error(f"Failed to load CLIP: {e}")
            return False
    
    def extract_features(
        self,
        image_paths: List[Path],
        batch_size: int = 32
    ) -> Tuple[np.ndarray, List[Path], List[Dict]]:
        """
        Extract CLIP features with quality filtering.
        
        Args:
            image_paths: List of image paths
            batch_size: Processing batch size
            
        Returns:
            (features, valid_paths, quality_reports)
        """
        if not self.load_model():
            return np.array([]), [], []
        
        print_section(f"Extracting features from {len(image_paths)} images")
        
        features_list = []
        valid_paths = []
        quality_reports = []
        
        with torch.no_grad():
            for i in range(0, len(image_paths), batch_size):
                batch_paths = image_paths[i:i + batch_size]
                batch_images = []
                batch_valid = []
                
                for img_path in batch_paths:
                    # Quality check
                    quality = self.quality_filter.check_quality(img_path)
                    quality_reports.append({
                        'path': str(img_path),
                        'quality': quality
                    })
                    
                    if not quality['passed']:
                        continue
                    
                    try:
                        img = Image.open(img_path).convert('RGB')
                        img_tensor = self.preprocess(img).unsqueeze(0)
                        batch_images.append(img_tensor)
                        batch_valid.append(img_path)
                    except Exception as e:
                        print_warning(f"Failed to load {img_path.name}: {e}")
                
                if not batch_images:
                    continue
                
                # Encode batch
                batch_tensor = torch.cat(batch_images).to(self.device)
                features = self.model.encode_image(batch_tensor)
                features = features.cpu().numpy()
                
                features_list.append(features)
                valid_paths.extend(batch_valid)
                
                print_progress(min(i + batch_size, len(image_paths)), len(image_paths), "Extracting")
        
        if not features_list:
            print_error("No valid images found!")
            return np.array([]), [], quality_reports
        
        all_features = np.vstack(features_list)
        print_success(f"Extracted features: {all_features.shape[0]} images")
        
        return all_features, valid_paths, quality_reports
    
    def cluster(
        self,
        features: np.ndarray,
        min_cluster_size: int = None
    ) -> np.ndarray:
        """
        Cluster features using HDBSCAN.
        
        Args:
            features: Feature vectors [N, D]
            min_cluster_size: Override default min cluster size
            
        Returns:
            Cluster labels (-1 for noise)
        """
        if not ensure_dependencies():
            return np.zeros(len(features), dtype=int)
        
        min_size = min_cluster_size or self.min_cluster_size
        
        print_section(f"Clustering {len(features)} images (min_size={min_size})")
        
        # Normalize features
        features_norm = features / np.linalg.norm(features, axis=1, keepdims=True)
        
        # HDBSCAN clustering
        clusterer = HDBSCAN(
            min_cluster_size=min_size,
            min_samples=5,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        
        labels = clusterer.fit_predict(features_norm)
        
        # Statistics
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        print_success(f"Found {n_clusters} character clusters")
        print_info(f"Noise/outliers: {n_noise}")
        
        # Cluster sizes
        unique, counts = np.unique(labels[labels >= 0], return_counts=True)
        print_info("Cluster distribution:")
        for label, count in sorted(zip(unique, counts), key=lambda x: -x[1]):
            print(f"  Character {label}: {count} images")
        
        return labels
    
    def visualize(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        output_path: Path
    ):
        """
        Create PCA visualization of clusters.
        
        Args:
            features: Feature vectors
            labels: Cluster labels
            output_path: Path to save visualization
        """
        if plt is None:
            print_warning("matplotlib not available, skipping visualization")
            return
        
        print_info("Creating cluster visualization...")
        
        # PCA to 2D
        pca = PCA(n_components=2)
        features_2d = pca.fit_transform(features)
        
        # Plot
        plt.figure(figsize=(12, 8))
        
        unique_labels = sorted(set(labels))
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_labels)))
        
        for label, color in zip(unique_labels, colors):
            mask = labels == label
            
            if label == -1:
                plt.scatter(
                    features_2d[mask, 0], features_2d[mask, 1],
                    c='gray', marker='x', alpha=0.3, s=30, label='Noise'
                )
            else:
                plt.scatter(
                    features_2d[mask, 0], features_2d[mask, 1],
                    c=[color], marker='o', alpha=0.6, s=50, label=f'Character {label}'
                )
        
        plt.title('Character Clustering (PCA Visualization)')
        plt.xlabel('PC1')
        plt.ylabel('PC2')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print_success(f"Visualization saved: {output_path}")
    
    def organize(
        self,
        image_paths: List[Path],
        labels: np.ndarray,
        output_dir: Path,
        copy_files: bool = True
    ) -> Dict:
        """
        Organize images into cluster folders.
        
        Args:
            image_paths: List of image paths
            labels: Cluster labels
            output_dir: Output directory
            copy_files: Copy files (False = create symlinks)
            
        Returns:
            Organization summary
        """
        print_section(f"Organizing into {output_dir}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        organization = {
            'total': len(image_paths),
            'clusters': {},
            'noise': 0
        }
        
        for img_path, label in zip(image_paths, labels):
            if label == -1:
                cluster_dir = output_dir / "noise"
                organization['noise'] += 1
            else:
                cluster_dir = output_dir / f"character_{label:03d}"
                if label not in organization['clusters']:
                    organization['clusters'][label] = 0
                organization['clusters'][label] += 1
            
            cluster_dir.mkdir(exist_ok=True)
            dst = cluster_dir / img_path.name
            
            if copy_files:
                shutil.copy2(img_path, dst)
            else:
                if not dst.exists():
                    dst.symlink_to(img_path.absolute())
        
        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'organization': {
                'total': organization['total'],
                'clusters': {int(k): v for k, v in organization['clusters'].items()},
                'noise': organization['noise']
            },
            'min_cluster_size': self.min_cluster_size
        }
        
        with open(output_dir / "clustering_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print_success(f"Organized {len(organization['clusters'])} character clusters")
        
        return organization
    
    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        visualize: bool = True
    ) -> Dict:
        """
        Full pipeline: extract, cluster, organize.
        
        Args:
            input_dir: Directory with character images
            output_dir: Output directory
            visualize: Create visualization
            
        Returns:
            Processing summary
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        
        # Find images
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp']
        images = []
        for ext in extensions:
            images.extend(input_dir.glob(f"**/{ext}"))
        
        if not images:
            print_error(f"No images found in {input_dir}")
            return {'error': 'No images found'}
        
        print_info(f"Found {len(images)} images")
        
        # Extract features
        features, valid_paths, quality_reports = self.extract_features(images)
        
        if len(features) == 0:
            return {'error': 'No valid images after quality filtering'}
        
        # Save quality report
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "quality_report.json", 'w') as f:
            json.dump(quality_reports, f, indent=2)
        
        # Cluster
        labels = self.cluster(features)
        
        # Visualize
        if visualize:
            self.visualize(features, labels, output_dir / "cluster_visualization.png")
        
        # Organize
        organization = self.organize(valid_paths, labels, output_dir)
        
        return {
            'total_images': len(images),
            'valid_images': len(valid_paths),
            'clusters': len(organization['clusters']),
            'noise': organization['noise']
        }


def cluster_characters(input_dir: Path, output_dir: Path) -> Dict:
    """Convenience function for character clustering"""
    clusterer = CharacterClusterer()
    return clusterer.process_directory(input_dir, output_dir)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cluster characters from images")
    parser.add_argument("input_dir", type=Path, help="Input directory")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    parser.add_argument("--min-cluster", type=int, default=10, help="Min cluster size")
    parser.add_argument("--no-viz", action="store_true", help="Skip visualization")
    
    args = parser.parse_args()
    
    clusterer = CharacterClusterer(min_cluster_size=args.min_cluster)
    clusterer.process_directory(args.input_dir, args.output, visualize=not args.no_viz)
