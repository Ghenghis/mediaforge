"""
LORAFORGE - VISION MODEL ANALYZER (PRODUCTION-READY)
Real quality assessment of vision models
No mocked data - actual API testing and metrics

CAPABILITIES:
- Test vision models with real images
- Measure response quality, speed, accuracy
- Compare models head-to-head
- Generate Good/Bad/Ugly reports
- Identify specific weaknesses per model
"""

import os
import json
import time
import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import re

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning


class VisionProvider(Enum):
    """Supported vision model providers"""
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"


@dataclass
class VisionTestResult:
    """Result of a single vision model test"""
    model_name: str
    provider: str
    test_type: str  # caption, analysis, ocr, quality, nsfw
    
    # Performance
    response_time_ms: float = 0
    tokens_per_second: float = 0
    time_to_first_token_ms: float = 0
    
    # Quality metrics (0-10)
    accuracy_score: float = 0      # How accurate was the description
    detail_score: float = 0        # Level of detail provided
    relevance_score: float = 0     # How relevant to the prompt
    coherence_score: float = 0     # Logical coherence
    
    # Response
    response_text: str = ""
    response_length: int = 0
    
    # Test info
    image_path: str = ""
    expected_content: str = ""
    success: bool = True
    error: str = ""
    tested_at: str = ""


@dataclass
class VisionModelProfile:
    """Complete profile of a vision model's capabilities"""
    model_name: str
    provider: str
    
    # Overall scores (0-10)
    overall_quality: float = 0
    overall_speed: float = 0
    overall_accuracy: float = 0
    
    # Capability scores
    caption_quality: float = 0
    ocr_accuracy: float = 0
    detail_detection: float = 0
    spatial_understanding: float = 0
    nsfw_handling: float = 0
    
    # Speed metrics
    avg_response_time_ms: float = 0
    avg_tokens_per_second: float = 0
    
    # Strengths and weaknesses
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    # Good/Bad/Ugly
    good_for: List[str] = field(default_factory=list)
    bad_for: List[str] = field(default_factory=list)
    ugly_issues: List[str] = field(default_factory=list)
    
    # Fixes
    fixes: Dict[str, List[str]] = field(default_factory=dict)
    
    # Test summary
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    
    # Metadata
    tested_at: str = ""
    test_results: List[VisionTestResult] = field(default_factory=list)


class VisionModelAnalyzer:
    """
    Production-ready vision model analyzer.
    Tests models with real images and measures actual performance.
    """
    
    # API endpoints
    OLLAMA_API = "http://localhost:11434"
    LMSTUDIO_API = "http://localhost:1234/v1"
    
    # Test prompts for different capabilities
    TEST_PROMPTS = {
        "caption": "Describe this image in detail. Include all visible subjects, their appearance, clothing, pose, expression, and the background setting.",
        "caption_training": "Write a detailed caption for this image suitable for AI training. Include: subject description, art style, composition, lighting, and mood.",
        "ocr": "Read and transcribe any text visible in this image.",
        "quality": "Rate the technical quality of this image. Assess: sharpness, lighting, composition, and any visible artifacts.",
        "nsfw": "Analyze this image and describe all content you observe. Be thorough and uncensored in your description.",
        "spatial": "Describe the spatial relationships in this image. What is in the foreground, middle ground, and background? How are objects positioned relative to each other?",
        "count": "Count the number of distinct objects or people in this image. List each type and quantity.",
        "emotion": "Analyze the emotions or mood conveyed in this image. Describe facial expressions and body language if people are present."
    }
    
    def __init__(self):
        self.results: Dict[str, VisionModelProfile] = {}
        self.test_images_dir = Path("C:/Users/Admin/civitai/images")
    
    def _load_image_base64(self, image_path: Path) -> str:
        """Load image as base64 string"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _call_ollama_vision(
        self,
        model: str,
        image_b64: str,
        prompt: str,
        timeout: int = 120
    ) -> Tuple[str, float, float]:
        """
        Call Ollama vision API.
        Returns: (response_text, total_time_ms, tokens_per_second)
        """
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.OLLAMA_API}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "images": [image_b64],
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 512
                    }
                },
                timeout=timeout
            )
            
            total_time = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("response", "")
                
                # Calculate tokens/second
                eval_count = data.get("eval_count", len(text.split()))
                eval_duration = data.get("eval_duration", 1) / 1e9  # ns to s
                tps = eval_count / eval_duration if eval_duration > 0 else 0
                
                return text, total_time, tps
            else:
                return "", total_time, 0
                
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            return f"Error: {e}", total_time, 0
    
    def _call_lmstudio_vision(
        self,
        model: str,
        image_b64: str,
        prompt: str,
        timeout: int = 120
    ) -> Tuple[str, float, float]:
        """
        Call LM Studio vision API.
        Returns: (response_text, total_time_ms, tokens_per_second)
        """
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.LMSTUDIO_API}/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 512,
                    "temperature": 0.3
                },
                timeout=timeout
            )
            
            total_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                
                # Estimate tokens/second
                tokens = data.get("usage", {}).get("completion_tokens", len(text.split()))
                tps = tokens / (total_time / 1000) if total_time > 0 else 0
                
                return text, total_time, tps
            else:
                return f"Error: {response.status_code}", total_time, 0
                
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            return f"Error: {e}", total_time, 0

    def test_model(
        self,
        model_name: str,
        provider: str,
        image_path: Path,
        test_type: str = "caption"
    ) -> VisionTestResult:
        """
        Test a vision model with a specific image and test type.
        """
        image_path = Path(image_path)
        
        result = VisionTestResult(
            model_name=model_name,
            provider=provider,
            test_type=test_type,
            image_path=str(image_path),
            tested_at=datetime.now().isoformat()
        )
        
        if not image_path.exists():
            result.success = False
            result.error = f"Image not found: {image_path}"
            return result
        
        try:
            # Load image
            image_b64 = self._load_image_base64(image_path)
            
            # Get appropriate prompt
            prompt = self.TEST_PROMPTS.get(test_type, self.TEST_PROMPTS["caption"])
            
            # Call appropriate API
            if provider == VisionProvider.OLLAMA.value:
                text, time_ms, tps = self._call_ollama_vision(model_name, image_b64, prompt)
            else:
                text, time_ms, tps = self._call_lmstudio_vision(model_name, image_b64, prompt)
            
            result.response_text = text
            result.response_length = len(text)
            result.response_time_ms = time_ms
            result.tokens_per_second = tps
            
            # Score the response
            scores = self._score_response(text, test_type)
            result.accuracy_score = scores["accuracy"]
            result.detail_score = scores["detail"]
            result.relevance_score = scores["relevance"]
            result.coherence_score = scores["coherence"]
            
            result.success = not text.startswith("Error:")
            
        except Exception as e:
            result.success = False
            result.error = str(e)
        
        return result
    
    def _score_response(self, response: str, test_type: str) -> Dict[str, float]:
        """
        Score a vision model response.
        Uses heuristics for real-time scoring without external AI.
        """
        scores = {
            "accuracy": 5.0,
            "detail": 5.0,
            "relevance": 5.0,
            "coherence": 5.0
        }
        
        if not response or response.startswith("Error"):
            return {k: 0.0 for k in scores}
        
        # Length-based detail score
        word_count = len(response.split())
        if word_count < 20:
            scores["detail"] = 3.0
        elif word_count < 50:
            scores["detail"] = 5.0
        elif word_count < 100:
            scores["detail"] = 7.0
        elif word_count < 200:
            scores["detail"] = 8.0
        else:
            scores["detail"] = 9.0
        
        # Coherence: check for repetition
        words = response.lower().split()
        unique_ratio = len(set(words)) / len(words) if words else 0
        if unique_ratio < 0.4:
            scores["coherence"] = 3.0
        elif unique_ratio < 0.6:
            scores["coherence"] = 5.0
        elif unique_ratio < 0.8:
            scores["coherence"] = 7.0
        else:
            scores["coherence"] = 8.5
        
        # Test-type specific scoring
        if test_type == "caption" or test_type == "caption_training":
            # Good captions mention visual elements
            visual_terms = ["wearing", "background", "standing", "sitting", "looking",
                          "hair", "eyes", "style", "lighting", "composition", "pose"]
            matches = sum(1 for term in visual_terms if term in response.lower())
            scores["relevance"] = min(10, 4 + matches * 0.6)
            scores["accuracy"] = min(10, 4 + matches * 0.5)
        
        elif test_type == "ocr":
            # OCR should have structured output
            if any(char.isalnum() for char in response):
                scores["accuracy"] = 7.0
            # Check for proper formatting
            if "\n" in response or ":" in response:
                scores["relevance"] = 8.0
        
        elif test_type == "spatial":
            spatial_terms = ["left", "right", "above", "below", "foreground", 
                           "background", "center", "behind", "front", "next to"]
            matches = sum(1 for term in spatial_terms if term in response.lower())
            scores["accuracy"] = min(10, 3 + matches * 0.8)
        
        elif test_type == "nsfw":
            # NSFW descriptions should be detailed and not refuse
            refusal_indicators = ["cannot", "won't", "unable", "sorry", "inappropriate"]
            if any(ind in response.lower() for ind in refusal_indicators):
                scores["accuracy"] = 2.0
                scores["relevance"] = 2.0
            else:
                scores["accuracy"] = 8.0
                scores["relevance"] = 8.0
        
        return scores
    
    def run_full_analysis(
        self,
        model_name: str,
        provider: str,
        test_images: List[Path] = None,
        test_types: List[str] = None
    ) -> VisionModelProfile:
        """
        Run comprehensive analysis on a vision model.
        """
        print_section(f"Analyzing: {model_name}")
        
        profile = VisionModelProfile(
            model_name=model_name,
            provider=provider,
            tested_at=datetime.now().isoformat()
        )
        
        # Get test images
        if test_images is None:
            if self.test_images_dir.exists():
                test_images = list(self.test_images_dir.glob("*.png"))[:10]
                test_images += list(self.test_images_dir.glob("*.jpg"))[:10]
            else:
                print_warning("No test images found")
                return profile
        
        # Get test types
        if test_types is None:
            test_types = ["caption", "caption_training", "spatial"]
        
        print_info(f"Testing with {len(test_images)} images, {len(test_types)} test types")
        
        all_results = []
        
        for image_path in test_images:
            for test_type in test_types:
                print_info(f"  {image_path.name} - {test_type}")
                
                result = self.test_model(model_name, provider, image_path, test_type)
                all_results.append(result)
                profile.total_tests += 1
                
                if result.success:
                    profile.passed_tests += 1
                else:
                    profile.failed_tests += 1
                
                # Rate limit
                time.sleep(0.5)
        
        profile.test_results = all_results
        
        # Calculate aggregate scores
        self._calculate_profile_scores(profile)
        
        # Generate Good/Bad/Ugly analysis
        self._analyze_good_bad_ugly(profile)
        
        # Store in results
        self.results[model_name] = profile
        
        return profile

    def _calculate_profile_scores(self, profile: VisionModelProfile):
        """Calculate aggregate scores from test results"""
        if not profile.test_results:
            return
        
        successful = [r for r in profile.test_results if r.success]
        
        if not successful:
            return
        
        # Speed metrics
        times = [r.response_time_ms for r in successful]
        tps_values = [r.tokens_per_second for r in successful if r.tokens_per_second > 0]
        
        profile.avg_response_time_ms = sum(times) / len(times)
        profile.avg_tokens_per_second = sum(tps_values) / len(tps_values) if tps_values else 0
        
        # Speed score (10 = <1s, 0 = >10s)
        profile.overall_speed = max(0, min(10, 10 - (profile.avg_response_time_ms / 1000)))
        
        # Quality scores by test type
        caption_results = [r for r in successful if "caption" in r.test_type]
        if caption_results:
            profile.caption_quality = sum(
                (r.accuracy_score + r.detail_score + r.relevance_score) / 3 
                for r in caption_results
            ) / len(caption_results)
        
        spatial_results = [r for r in successful if r.test_type == "spatial"]
        if spatial_results:
            profile.spatial_understanding = sum(r.accuracy_score for r in spatial_results) / len(spatial_results)
        
        # Overall quality
        accuracy_scores = [r.accuracy_score for r in successful]
        detail_scores = [r.detail_score for r in successful]
        relevance_scores = [r.relevance_score for r in successful]
        
        profile.overall_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        profile.overall_quality = (
            sum(accuracy_scores) / len(accuracy_scores) * 0.4 +
            sum(detail_scores) / len(detail_scores) * 0.3 +
            sum(relevance_scores) / len(relevance_scores) * 0.3
        )
    
    def _analyze_good_bad_ugly(self, profile: VisionModelProfile):
        """Generate Good/Bad/Ugly analysis with fixes"""
        
        # === GOOD ===
        if profile.overall_quality >= 7:
            profile.good_for.append("High-quality image descriptions")
        if profile.avg_response_time_ms < 3000:
            profile.good_for.append("Fast response times (<3s)")
            profile.strengths.append("Speed")
        if profile.caption_quality >= 7:
            profile.good_for.append("Training data captioning")
            profile.strengths.append("Detailed captions")
        if profile.spatial_understanding >= 7:
            profile.good_for.append("Scene composition analysis")
            profile.strengths.append("Spatial understanding")
        if profile.overall_accuracy >= 7:
            profile.strengths.append("High accuracy")
        
        # === BAD ===
        if profile.overall_quality < 5:
            profile.bad_for.append("Production captioning (quality too low)")
            profile.weaknesses.append("Low overall quality")
        if profile.avg_response_time_ms > 10000:
            profile.bad_for.append("Real-time applications (too slow)")
            profile.weaknesses.append("Slow response time")
        if profile.caption_quality < 5:
            profile.bad_for.append("Detailed captioning work")
            profile.weaknesses.append("Shallow descriptions")
        if profile.passed_tests < profile.total_tests * 0.8:
            profile.bad_for.append("Reliable batch processing")
            profile.weaknesses.append("Unreliable/crashes")
        
        # === UGLY (Critical Issues) ===
        failed_results = [r for r in profile.test_results if not r.success]
        
        if len(failed_results) > 0:
            error_types = {}
            for r in failed_results:
                error_key = r.error[:50] if r.error else "Unknown error"
                error_types[error_key] = error_types.get(error_key, 0) + 1
            
            for error, count in error_types.items():
                profile.ugly_issues.append(f"Error ({count}x): {error}")
        
        # Check for refusals
        refusal_count = sum(
            1 for r in profile.test_results 
            if r.success and any(
                word in r.response_text.lower() 
                for word in ["cannot", "won't", "unable", "inappropriate"]
            )
        )
        if refusal_count > 2:
            profile.ugly_issues.append(f"Refuses {refusal_count} requests (censored model)")
        
        # Check for repetitive outputs
        repetitive = sum(
            1 for r in profile.test_results 
            if r.success and r.coherence_score < 4
        )
        if repetitive > 2:
            profile.ugly_issues.append(f"Repetitive/incoherent output ({repetitive} times)")
        
        # === FIXES ===
        profile.fixes = self._generate_fixes(profile)
    
    def _generate_fixes(self, profile: VisionModelProfile) -> Dict[str, List[str]]:
        """Generate 3 fixes for each identified problem"""
        fixes = {}
        
        # Fix: Slow response
        if profile.avg_response_time_ms > 5000:
            fixes["Slow Response Time"] = [
                "1. Reduce max_tokens parameter (try 256 instead of 512)",
                "2. Use a smaller quantization (Q4_K_M instead of Q8)",
                "3. Ensure GPU offloading is enabled (check CUDA availability)"
            ]
        
        # Fix: Low quality
        if profile.overall_quality < 5:
            fixes["Low Quality Output"] = [
                "1. Try a larger variant of the same model family",
                "2. Use better prompts with more specific instructions",
                "3. Lower temperature (try 0.1-0.3 for more focused output)"
            ]
        
        # Fix: Shallow descriptions
        if profile.caption_quality < 5:
            fixes["Shallow Descriptions"] = [
                "1. Add explicit instructions: 'Describe in at least 100 words'",
                "2. Use structured prompts: 'Describe: subject, setting, style, mood'",
                "3. Try chain-of-thought: 'First describe what you see, then analyze'"
            ]
        
        # Fix: Refusals
        refusal_issues = [i for i in profile.ugly_issues if "Refuses" in i]
        if refusal_issues:
            fixes["Model Refusals (Censorship)"] = [
                "1. Switch to an abliterated/uncensored variant",
                "2. Modify system prompt to allow detailed analysis",
                "3. Use local uncensored models (llava-uncensored, minicpm-uncensored)"
            ]
        
        # Fix: Errors/crashes
        error_issues = [i for i in profile.ugly_issues if "Error" in i]
        if error_issues:
            fixes["Errors and Crashes"] = [
                "1. Reduce image resolution before sending (max 1024x1024)",
                "2. Increase timeout value (try 180s for large models)",
                "3. Check VRAM availability and reduce context length"
            ]
        
        # Fix: Repetition
        if any("Repetitive" in i for i in profile.ugly_issues):
            fixes["Repetitive Output"] = [
                "1. Increase temperature slightly (try 0.5-0.7)",
                "2. Add 'Do not repeat yourself' to the prompt",
                "3. Use a different model - repetition often indicates poor training"
            ]
        
        return fixes
    
    def generate_report(self, output_path: Path = None) -> str:
        """Generate comprehensive markdown report"""
        if output_path is None:
            output_path = Path(__file__).parent.parent.parent.parent / "docs" / "VISION-MODEL-ANALYSIS.md"
        
        report = """# 🔍 Vision Model Analysis Report

> Generated: {timestamp}
> Total Models Analyzed: {total_models}

## Overview

This report provides a comprehensive analysis of vision models tested for the LoRAForge pipeline.
Each model is evaluated on multiple dimensions with specific recommendations.

---

""".format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            total_models=len(self.results)
        )
        
        # Sort by overall quality
        sorted_profiles = sorted(
            self.results.values(),
            key=lambda p: p.overall_quality,
            reverse=True
        )
        
        for profile in sorted_profiles:
            report += self._format_profile_section(profile)
        
        # Summary table
        report += self._generate_summary_table()
        
        # Save report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding='utf-8')
        
        print_success(f"Report saved: {output_path}")
        
        return report

    def _format_profile_section(self, profile: VisionModelProfile) -> str:
        """Format a single model profile as markdown"""
        # Grade calculation
        if profile.overall_quality >= 8:
            grade = "A"
            grade_emoji = "🟢"
        elif profile.overall_quality >= 6:
            grade = "B"
            grade_emoji = "🟡"
        elif profile.overall_quality >= 4:
            grade = "C"
            grade_emoji = "🟠"
        else:
            grade = "D"
            grade_emoji = "🔴"
        
        section = f"""
## {grade_emoji} {profile.model_name}

**Provider:** {profile.provider} | **Grade:** {grade} | **Quality:** {profile.overall_quality:.1f}/10

### Performance Metrics

| Metric | Value |
|--------|-------|
| Overall Quality | {profile.overall_quality:.1f}/10 |
| Caption Quality | {profile.caption_quality:.1f}/10 |
| Accuracy | {profile.overall_accuracy:.1f}/10 |
| Speed | {profile.overall_speed:.1f}/10 |
| Avg Response | {profile.avg_response_time_ms:.0f}ms |
| Tokens/Second | {profile.avg_tokens_per_second:.1f} |
| Pass Rate | {profile.passed_tests}/{profile.total_tests} |

### ✅ Good For
"""
        
        if profile.good_for:
            for item in profile.good_for:
                section += f"- {item}\n"
        else:
            section += "- (No notable strengths identified)\n"
        
        section += "\n### ❌ Bad For\n"
        if profile.bad_for:
            for item in profile.bad_for:
                section += f"- {item}\n"
        else:
            section += "- (No notable weaknesses identified)\n"
        
        section += "\n### 💀 Ugly (Critical Issues)\n"
        if profile.ugly_issues:
            for item in profile.ugly_issues:
                section += f"- ⚠️ {item}\n"
        else:
            section += "- ✓ No critical issues found\n"
        
        section += "\n### 🔧 Fixes\n"
        if profile.fixes:
            for problem, fix_list in profile.fixes.items():
                section += f"\n**{problem}:**\n"
                for fix in fix_list:
                    section += f"- {fix}\n"
        else:
            section += "- No fixes required\n"
        
        section += "\n---\n"
        
        return section
    
    def _generate_summary_table(self) -> str:
        """Generate summary comparison table"""
        table = """
## 📊 Summary Comparison

| Model | Quality | Speed | Caption | Pass Rate | Grade |
|-------|---------|-------|---------|-----------|-------|
"""
        
        for name, profile in sorted(
            self.results.items(),
            key=lambda x: x[1].overall_quality,
            reverse=True
        ):
            grade = "A" if profile.overall_quality >= 8 else "B" if profile.overall_quality >= 6 else "C" if profile.overall_quality >= 4 else "D"
            pass_rate = f"{profile.passed_tests}/{profile.total_tests}"
            
            table += f"| {name[:30]} | {profile.overall_quality:.1f} | {profile.overall_speed:.1f} | {profile.caption_quality:.1f} | {pass_rate} | {grade} |\n"
        
        table += """

### Legend
- **Quality**: Overall output quality (0-10)
- **Speed**: Response speed (10 = <1s, 0 = >10s)
- **Caption**: Caption generation quality (0-10)
- **Pass Rate**: Successful tests / Total tests
- **Grade**: A (8+), B (6-8), C (4-6), D (<4)

"""
        return table
    
    def save_results_json(self, output_path: Path = None):
        """Save results as JSON for programmatic access"""
        if output_path is None:
            output_path = Path(__file__).parent.parent.parent.parent / "reports" / "vision_model_analysis.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "generated_at": datetime.now().isoformat(),
            "total_models": len(self.results),
            "models": {}
        }
        
        for name, profile in self.results.items():
            # Convert to dict without the large test_results
            profile_dict = asdict(profile)
            profile_dict["test_results"] = len(profile.test_results)  # Just count
            data["models"][name] = profile_dict
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        print_success(f"JSON saved: {output_path}")


def analyze_available_models():
    """Analyze all available vision models"""
    analyzer = VisionModelAnalyzer()
    
    # Known vision models to test
    models_to_test = [
        ("llava-uncensored", "ollama"),
        ("minicpm-uncensored", "ollama"),
        ("llava-llama3-uncensored", "ollama"),
        ("bakllava", "ollama"),
        ("llava:7b", "ollama"),
        ("llava:13b", "ollama"),
    ]
    
    print_section("Vision Model Analysis")
    
    for model_name, provider in models_to_test:
        try:
            print_info(f"\nTesting: {model_name}")
            profile = analyzer.run_full_analysis(model_name, provider)
            print_success(f"  Quality: {profile.overall_quality:.1f}/10")
        except Exception as e:
            print_error(f"  Failed: {e}")
    
    # Generate reports
    analyzer.generate_report()
    analyzer.save_results_json()
    
    return analyzer.results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Vision Model Analyzer")
    parser.add_argument("--model", type=str, help="Specific model to test")
    parser.add_argument("--provider", type=str, default="ollama", help="Provider")
    parser.add_argument("--all", action="store_true", help="Test all known models")
    parser.add_argument("--report", action="store_true", help="Generate reports only")
    
    args = parser.parse_args()
    
    analyzer = VisionModelAnalyzer()
    
    if args.all:
        analyze_available_models()
    elif args.model:
        profile = analyzer.run_full_analysis(args.model, args.provider)
        print(json.dumps(asdict(profile), indent=2, default=str))
    elif args.report:
        analyzer.generate_report()
    else:
        print("Usage: python vision_analyzer.py --model <name> --provider <provider>")
        print("       python vision_analyzer.py --all")
