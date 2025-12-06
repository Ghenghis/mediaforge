"""
LORAFORGE - AUTO CAPTIONER
Automatic image captioning for LoRA training
Enhanced from anime-lora-pipeline with uncensored support

HOW IT WORKS:
1. WD14 Tagger: ONNX model from HuggingFace for anime/image tagging
2. LM Studio: For detailed uncensored descriptions (our unique advantage)
3. Caption Generation: Combines trigger word + detected tags
4. Batch Processing: Generates .txt files for all images

SUPPORTED MODES:
- "wd14": Fast tag-based captioning using WD14
- "lmstudio": Detailed descriptions using vision AI (uncensored)
- "hybrid": WD14 tags + LM Studio description
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image
import json
import base64
import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning, print_progress

# Optional dependencies
ort = None
pd = None

def ensure_onnx():
    """Lazy load ONNX runtime"""
    global ort, pd
    if ort is None:
        try:
            import onnxruntime as _ort
            import pandas as _pd
            ort = _ort
            pd = _pd
            return True
        except ImportError:
            print_warning("onnxruntime/pandas not installed for WD14. Run: pip install onnxruntime pandas")
            return False
    return True


class WD14Tagger:
    """
    WD14 Tagger for anime/image tagging.
    Uses ONNX model from HuggingFace for fast inference.
    """
    
    MODEL_REPO = "SmilingWolf/wd-vit-tagger-v3"
    
    def __init__(
        self,
        model_repo: str = None,
        device: str = "cuda",
        general_threshold: float = 0.35,
        character_threshold: float = 0.85
    ):
        """
        Initialize WD14 Tagger.
        
        Args:
            model_repo: HuggingFace model repository
            device: cuda or cpu
            general_threshold: Confidence for general tags
            character_threshold: Confidence for character tags
        """
        self.model_repo = model_repo or self.MODEL_REPO
        self.device = device
        self.general_threshold = general_threshold
        self.character_threshold = character_threshold
        
        self.model = None
        self.tags = None
        self.loaded = False
    
    def load_model(self) -> bool:
        """Load the ONNX model and tags"""
        if self.loaded:
            return True
        
        if not ensure_onnx():
            return False
        
        try:
            from huggingface_hub import hf_hub_download
            
            print_info(f"Loading WD14 model from {self.model_repo}")
            
            # Download model
            model_path = hf_hub_download(
                self.model_repo,
                filename="model.onnx"
            )
            
            # Download tags
            tags_path = hf_hub_download(
                self.model_repo,
                filename="selected_tags.csv"
            )
            
            # Load ONNX model
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if self.device == "cuda" else ['CPUExecutionProvider']
            self.model = ort.InferenceSession(model_path, providers=providers)
            
            # Load tags
            self.tags = pd.read_csv(tags_path)
            
            self.loaded = True
            print_success(f"Loaded {len(self.tags)} tags")
            return True
            
        except Exception as e:
            print_error(f"Failed to load WD14: {e}")
            return False
    
    def preprocess_image(self, image: Image.Image, target_size: int = 448) -> np.ndarray:
        """
        Preprocess image for WD14 model.
        
        Args:
            image: PIL Image
            target_size: Model input size
            
        Returns:
            Preprocessed numpy array
        """
        image = image.convert('RGB')
        w, h = image.size
        
        # Pad to square
        max_dim = max(w, h)
        padded = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
        padded.paste(image, ((max_dim - w) // 2, (max_dim - h) // 2))
        
        # Resize
        padded = padded.resize((target_size, target_size), Image.BICUBIC)
        
        # Convert to array and normalize
        arr = np.array(padded, dtype=np.float32) / 255.0
        arr = np.expand_dims(arr, axis=0)  # Add batch dimension
        
        return arr
    
    def predict(
        self,
        image_path: Path,
        general_threshold: float = None,
        character_threshold: float = None
    ) -> Dict[str, float]:
        """
        Predict tags for an image.
        
        Args:
            image_path: Path to image
            general_threshold: Override general threshold
            character_threshold: Override character threshold
            
        Returns:
            Dict of {tag: confidence}
        """
        if not self.loaded and not self.load_model():
            return {}
        
        general_threshold = general_threshold or self.general_threshold
        character_threshold = character_threshold or self.character_threshold
        
        try:
            image = Image.open(image_path)
            input_arr = self.preprocess_image(image)
            
            # Run inference
            input_name = self.model.get_inputs()[0].name
            output = self.model.run(None, {input_name: input_arr})[0]
            predictions = output[0]
            
            # Filter by threshold
            results = {}
            for i, row in self.tags.iterrows():
                conf = float(predictions[i])
                tag = row['name']
                category = row['category']
                
                threshold = character_threshold if category == 4 else general_threshold
                
                if conf >= threshold:
                    results[tag] = conf
            
            return results
            
        except Exception as e:
            print_error(f"WD14 prediction failed for {image_path}: {e}")
            return {}


class LMStudioCaptioner:
    """
    LM Studio-based captioning for detailed, uncensored descriptions.
    This is our UNIQUE advantage over competitors.
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:1234/v1",
        model: str = "qwen3-vl-8b-abliterated-caption-it",
        timeout: int = 60
    ):
        """
        Initialize LM Studio captioner.
        
        Args:
            api_url: LM Studio API URL
            model: Model name
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.model = model
        self.timeout = timeout
    
    def generate_caption(
        self,
        image_path: Path,
        style: str = "detailed"
    ) -> str:
        """
        Generate caption using LM Studio vision model.
        
        Args:
            image_path: Path to image
            style: Caption style (detailed, minimal, tags)
            
        Returns:
            Generated caption
        """
        try:
            # Encode image
            with open(image_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            
            # Select prompt based on style
            if style == "minimal":
                prompt = "Describe this image in one short sentence."
            elif style == "tags":
                prompt = "List descriptive tags for this image, separated by commas."
            else:  # detailed
                prompt = """Describe this image in detail for AI training. Include:
- Subject description (appearance, clothing, pose)
- Setting/background
- Art style
- Key visual elements
Format as a comma-separated list of descriptive tags."""
            
            # Call API
            response = requests.post(
                f"{self.api_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                            ]
                        }
                    ],
                    "max_tokens": 300
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return content.strip()
            else:
                print_warning(f"LM Studio returned {response.status_code}")
                return ""
                
        except Exception as e:
            print_error(f"LM Studio captioning failed: {e}")
            return ""


class AutoCaptioner:
    """
    Unified auto-captioning interface supporting multiple backends.
    
    Modes:
    - "wd14": Fast WD14 tag-based captions
    - "lmstudio": Detailed LM Studio descriptions (uncensored)
    - "hybrid": Combine both for best results
    """
    
    def __init__(
        self,
        mode: str = "wd14",
        trigger_word: str = "",
        wd14_threshold: float = 0.35,
        lmstudio_url: str = "http://localhost:1234/v1",
        lmstudio_model: str = "qwen3-vl-8b-abliterated-caption-it"
    ):
        """
        Initialize AutoCaptioner.
        
        Args:
            mode: Captioning mode (wd14, lmstudio, hybrid)
            trigger_word: Trigger word to prepend to captions
            wd14_threshold: WD14 confidence threshold
            lmstudio_url: LM Studio API URL
            lmstudio_model: LM Studio model name
        """
        self.mode = mode
        self.trigger_word = trigger_word
        
        self.wd14 = None
        self.lmstudio = None
        
        # Initialize backends based on mode
        if mode in ["wd14", "hybrid"]:
            self.wd14 = WD14Tagger(general_threshold=wd14_threshold)
        
        if mode in ["lmstudio", "hybrid"]:
            self.lmstudio = LMStudioCaptioner(api_url=lmstudio_url, model=lmstudio_model)
    
    def generate_caption(
        self,
        image_path: Path,
        tag_blacklist: List[str] = None,
        max_tags: int = 30
    ) -> str:
        """
        Generate caption for single image.
        
        Args:
            image_path: Path to image
            tag_blacklist: Tags to exclude (WD14 mode)
            max_tags: Maximum tags to include
            
        Returns:
            Generated caption
        """
        tag_blacklist = tag_blacklist or ["solo", "1girl", "1boy", "anime_coloring"]
        
        caption_parts = []
        
        # Add trigger word first
        if self.trigger_word:
            caption_parts.append(self.trigger_word)
        
        # WD14 tags
        if self.wd14 and self.mode in ["wd14", "hybrid"]:
            tags = self.wd14.predict(image_path)
            
            # Filter and sort by confidence
            filtered = {
                tag: conf for tag, conf in tags.items()
                if tag not in tag_blacklist
            }
            sorted_tags = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
            tag_list = [tag for tag, _ in sorted_tags[:max_tags]]
            
            if tag_list:
                caption_parts.extend(tag_list)
        
        # LM Studio description
        if self.lmstudio and self.mode in ["lmstudio", "hybrid"]:
            description = self.lmstudio.generate_caption(image_path, style="tags")
            if description:
                # Clean up and add
                desc_tags = [t.strip() for t in description.split(',') if t.strip()]
                caption_parts.extend(desc_tags)
        
        # Join with commas
        return ", ".join(caption_parts)
    
    def batch_caption(
        self,
        image_dir: Path,
        output_dir: Path = None,
        tag_blacklist: List[str] = None,
        save_individual: bool = True,
        save_combined: bool = True
    ) -> Dict[Path, str]:
        """
        Generate captions for all images in directory.
        
        Args:
            image_dir: Directory with images
            output_dir: Output directory (default: same as image_dir)
            tag_blacklist: Tags to exclude
            save_individual: Save .txt files per image
            save_combined: Save combined metadata.json
            
        Returns:
            Dict mapping image paths to captions
        """
        image_dir = Path(image_dir)
        output_dir = Path(output_dir) if output_dir else image_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find images
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp']
        images = []
        for ext in extensions:
            images.extend(image_dir.glob(ext))
        
        print_section(f"Captioning {len(images)} images ({self.mode} mode)")
        
        captions = {}
        
        for i, img_path in enumerate(images):
            try:
                caption = self.generate_caption(img_path, tag_blacklist)
                captions[img_path] = caption
                
                # Save individual caption
                if save_individual:
                    txt_path = output_dir / f"{img_path.stem}.txt"
                    txt_path.write_text(caption, encoding='utf-8')
                
            except Exception as e:
                print_warning(f"Failed to caption {img_path.name}: {e}")
            
            print_progress(i + 1, len(images), "Captioning")
        
        # Save combined metadata
        if save_combined:
            metadata = {
                "mode": self.mode,
                "trigger_word": self.trigger_word,
                "captions": {
                    str(p.name): c for p, c in captions.items()
                }
            }
            
            meta_path = output_dir / "captions_metadata.json"
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print_info(f"Metadata: {meta_path}")
        
        print_success(f"Generated {len(captions)} captions")
        return captions


def caption_images(image_dir: Path, trigger_word: str = "", mode: str = "wd14") -> Dict:
    """Convenience function for batch captioning"""
    captioner = AutoCaptioner(mode=mode, trigger_word=trigger_word)
    return captioner.batch_caption(image_dir)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-caption images for LoRA training")
    parser.add_argument("image_dir", type=Path, help="Directory with images")
    parser.add_argument("--trigger", type=str, default="", help="Trigger word")
    parser.add_argument("--mode", choices=["wd14", "lmstudio", "hybrid"], default="wd14")
    parser.add_argument("--output", type=Path, help="Output directory")
    
    args = parser.parse_args()
    
    captioner = AutoCaptioner(mode=args.mode, trigger_word=args.trigger)
    captioner.batch_caption(args.image_dir, output_dir=args.output)
