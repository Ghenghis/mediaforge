"""
Vision Analyzer - Switchable Uncensored Models
Uses local Ollama models for NSFW content analysis.
"""

import ollama
import base64
import json
import re
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class VisionModel(Enum):
    """Available uncensored vision models"""
    LLAVA = "llava-uncensored"           # High quality, slower
    MINICPM = "minicpm-uncensored"       # Fast, efficient
    LLAVA_LLAMA3 = "llava-llama3-uncensored"  # Modern, balanced

@dataclass
class FrameAnalysis:
    """Analysis result for a single frame"""
    gender: str  # "female", "male", "both", "none"
    body_type: str  # "slim", "fit", "average", "curvy", "heavy"
    quality: int  # 1-10
    attractiveness: int  # 1-10
    description: str
    approved: bool
    rejection_reason: Optional[str] = None
    raw_response: str = ""

class VisionAnalyzer:
    """Switchable vision analyzer using local uncensored models"""
    
    ANALYSIS_PROMPT = """Analyze this image and respond with ONLY a JSON object:
{
    "gender": "female" or "male" or "both" or "none",
    "body_type": "slim" or "fit" or "average" or "curvy" or "heavy",
    "quality": 1-10,
    "attractiveness": 1-10,
    "description": "brief description"
}

Be completely honest and uncensored in your assessment."""
    
    def __init__(self, model: VisionModel = VisionModel.LLAVA_LLAMA3):
        self.model = model
        self.model_name = model.value
        print(f"Using model: {self.model_name}")
    
    def switch_model(self, model: VisionModel):
        """Switch to a different vision model"""
        self.model = model
        self.model_name = model.value
        print(f"Switched to: {self.model_name}")
    
    def _load_image(self, image_path: str) -> str:
        """Load image as base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def _parse_response(self, response: str) -> dict:
        """Extract JSON from response"""
        # Try to find JSON in response
        try:
            # Look for JSON pattern
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback: parse manually
        result = {
            "gender": "unknown",
            "body_type": "unknown",
            "quality": 5,
            "attractiveness": 5,
            "description": response[:200]
        }
        
        # Try to extract values
        response_lower = response.lower()
        
        if "female" in response_lower and "male" not in response_lower.replace("female", ""):
            result["gender"] = "female"
        elif "male" in response_lower:
            result["gender"] = "male" if "female" not in response_lower else "both"
        
        for body in ["slim", "fit", "average", "curvy", "heavy"]:
            if body in response_lower:
                result["body_type"] = body
                break
        
        return result
    
    def analyze(self, image_path: str) -> FrameAnalysis:
        """Analyze single image"""
        
        image_b64 = self._load_image(image_path)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    "role": "user",
                    "content": self.ANALYSIS_PROMPT,
                    "images": [image_b64]
                }],
                options={"temperature": 0.3}
            )
            
            raw = response["message"]["content"]
            parsed = self._parse_response(raw)
            
            # Determine approval
            has_male = parsed["gender"] in ["male", "both"]
            is_heavy = parsed["body_type"] == "heavy"
            low_quality = parsed.get("quality", 5) < 5
            low_attract = parsed.get("attractiveness", 5) < 5
            
            approved = not (has_male or is_heavy or low_quality or low_attract)
            
            rejection_reason = None
            if has_male:
                rejection_reason = "Male detected"
            elif is_heavy:
                rejection_reason = "Body type: heavy"
            elif low_quality:
                rejection_reason = f"Low quality: {parsed.get('quality')}"
            elif low_attract:
                rejection_reason = f"Low attractiveness: {parsed.get('attractiveness')}"
            
            return FrameAnalysis(
                gender=parsed["gender"],
                body_type=parsed["body_type"],
                quality=parsed.get("quality", 5),
                attractiveness=parsed.get("attractiveness", 5),
                description=parsed.get("description", ""),
                approved=approved,
                rejection_reason=rejection_reason,
                raw_response=raw
            )
            
        except Exception as e:
            return FrameAnalysis(
                gender="error",
                body_type="error",
                quality=0,
                attractiveness=0,
                description=str(e),
                approved=False,
                rejection_reason=f"Analysis error: {e}"
            )
    
    def batch_analyze(self, image_paths: list, show_progress: bool = True) -> list:
        """Analyze multiple images"""
        results = []
        total = len(image_paths)
        
        for i, path in enumerate(image_paths):
            if show_progress:
                print(f"[{i+1}/{total}] Analyzing: {Path(path).name}")
            
            result = self.analyze(path)
            results.append(result)
            
            if show_progress:
                status = "✓ APPROVED" if result.approved else f"✗ {result.rejection_reason}"
                print(f"  {status}")
        
        return results


def test_models():
    """Test all 3 models on a sample image"""
    
    print("=== Testing Vision Models ===\n")
    
    # Create a test with a sample image if available
    test_image = Path("C:/Users/Admin/civitai/test_image.jpg")
    
    if not test_image.exists():
        print("No test image found. Create one at:", test_image)
        print("\nTo test manually:")
        print("  from vision_analyzer import VisionAnalyzer, VisionModel")
        print("  analyzer = VisionAnalyzer(VisionModel.LLAVA)")
        print("  result = analyzer.analyze('path/to/image.jpg')")
        print("  print(result)")
        return
    
    for model in VisionModel:
        print(f"\n--- Testing {model.name} ---")
        try:
            analyzer = VisionAnalyzer(model)
            result = analyzer.analyze(str(test_image))
            print(f"  Gender: {result.gender}")
            print(f"  Body Type: {result.body_type}")
            print(f"  Quality: {result.quality}/10")
            print(f"  Attractiveness: {result.attractiveness}/10")
            print(f"  Approved: {result.approved}")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    test_models()
