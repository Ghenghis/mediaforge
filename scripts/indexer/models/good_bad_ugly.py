"""
LORAFORGE - GOOD/BAD/UGLY REPORT GENERATOR
Comprehensive model analysis and production-readiness documentation
Creates detailed markdown reports with actionable fixes

OUTPUT:
- GOOD_BAD_UGLY.md - Complete model analysis
- PRODUCTION_READINESS.md - Fix guide for all issues
- MODEL_SKILLSETS.md - Capability matrix
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning


@dataclass
class ModelSkillset:
    """Model capability assessment"""
    model_name: str
    
    # Core skills (0-10)
    text_generation: int = 5
    instruction_following: int = 5
    code_generation: int = 5
    creative_writing: int = 5
    reasoning: int = 5
    math: int = 5
    vision: int = 0
    uncensored: int = 0
    
    # Speed tier
    speed_tier: str = "medium"  # fast, medium, slow
    
    # Quality tier
    quality_tier: str = "good"  # excellent, good, acceptable, poor
    
    # Recommended uses
    recommended_for: List[str] = field(default_factory=list)
    not_recommended_for: List[str] = field(default_factory=list)


@dataclass
class ProblemFix:
    """A problem with its fixes"""
    problem_id: str
    category: str  # performance, quality, reliability, compatibility
    severity: str  # critical, major, minor
    description: str
    symptoms: List[str]
    root_cause: str
    fixes: List[str]
    verification: str


class GoodBadUglyGenerator:
    """
    Generates comprehensive model analysis documentation.
    """
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent.parent / "data"
        
        self.data_dir = data_dir
        self.docs_dir = Path(__file__).parent.parent.parent.parent / "docs"
        self.reports_dir = Path(__file__).parent.parent.parent.parent / "reports"
        
        self.docs_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Load existing data
        self.model_benchmarks = self._load_benchmarks()
        self.problems = self._define_common_problems()
        self.skillsets = {}
    
    def _load_benchmarks(self) -> Dict:
        """Load benchmark data from database"""
        import sqlite3
        
        db_path = self.data_dir / "loraforge.db"
        
        if not db_path.exists():
            return {}
        
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            
            # Get all benchmarked models
            rows = conn.execute("""
                SELECT 
                    m.name,
                    m.provider,
                    m.parameter_count,
                    m.is_vision,
                    m.is_uncensored,
                    AVG(b.tokens_per_second) as avg_speed,
                    AVG(b.output_quality) as avg_quality,
                    COUNT(b.id) as test_count,
                    SUM(CASE WHEN b.success = 1 THEN 1 ELSE 0 END) as success_count
                FROM models m
                LEFT JOIN benchmarks b ON b.model_id = m.id
                GROUP BY m.id
            """).fetchall()
            
            conn.close()
            
            return {
                row["name"]: dict(row)
                for row in rows
            }
        except Exception as e:
            print_warning(f"Could not load benchmarks: {e}")
            return {}
    
    def _define_common_problems(self) -> List[ProblemFix]:
        """Define common problems and their fixes"""
        return [
            ProblemFix(
                problem_id="PERF-001",
                category="performance",
                severity="major",
                description="Slow inference speed (<20 tokens/second)",
                symptoms=[
                    "Response takes >10 seconds",
                    "High GPU utilization for extended periods",
                    "User complains about wait times"
                ],
                root_cause="Model too large for available VRAM, causing CPU offloading or slow quantization",
                fixes=[
                    "1. Use a smaller quantization (Q4_K_M or Q4_K_S instead of Q8)",
                    "2. Reduce context length in model config (try 4096 instead of 8192)",
                    "3. Enable GPU flash attention if available (--flash-attn flag)"
                ],
                verification="Run benchmark and confirm >50 tokens/second"
            ),
            ProblemFix(
                problem_id="PERF-002",
                category="performance",
                severity="critical",
                description="Out of memory (OOM) errors",
                symptoms=[
                    "CUDA out of memory error",
                    "Process killed by OOM killer",
                    "Model fails to load"
                ],
                root_cause="Model VRAM requirement exceeds available GPU memory",
                fixes=[
                    "1. Use a smaller model variant (7B instead of 13B)",
                    "2. Use more aggressive quantization (Q3_K_S or IQ2_XS)",
                    "3. Split model across CPU/GPU (set n_gpu_layers appropriately)"
                ],
                verification="Model loads and runs without memory errors"
            ),
            ProblemFix(
                problem_id="QUAL-001",
                category="quality",
                severity="major",
                description="Low quality/incoherent output",
                symptoms=[
                    "Responses don't make sense",
                    "Repetitive text patterns",
                    "Ignores instructions"
                ],
                root_cause="Model not suited for task, or poor prompting",
                fixes=[
                    "1. Try a different model family (switch from Llama to Qwen or Mistral)",
                    "2. Use explicit, detailed system prompts with examples",
                    "3. Lower temperature (0.1-0.3) for more focused output"
                ],
                verification="Output coherence and relevance improved"
            ),
            ProblemFix(
                problem_id="QUAL-002",
                category="quality",
                severity="major",
                description="Model refuses requests (censorship)",
                symptoms=[
                    "Responds with 'I cannot' or 'I won't'",
                    "Adds unnecessary safety warnings",
                    "Refuses to describe NSFW content"
                ],
                root_cause="Model has safety training that blocks certain outputs",
                fixes=[
                    "1. Use an abliterated/uncensored variant of the model",
                    "2. Try dolphin, hermes, or wizard-vicuna fine-tunes",
                    "3. Create custom modelfile with permissive system prompt"
                ],
                verification="Model provides requested content without refusal"
            ),
            ProblemFix(
                problem_id="QUAL-003",
                category="quality",
                severity="minor",
                description="Shallow/brief responses",
                symptoms=[
                    "Answers are too short",
                    "Missing important details",
                    "Doesn't elaborate when asked"
                ],
                root_cause="Model defaults to brevity, or prompt doesn't request detail",
                fixes=[
                    "1. Add 'Provide a detailed, comprehensive response' to prompt",
                    "2. Increase max_tokens parameter (try 1024+)",
                    "3. Use explicit structure: 'List at least 5 points' or 'Write 3 paragraphs'"
                ],
                verification="Responses are appropriately detailed"
            ),
            ProblemFix(
                problem_id="REL-001",
                category="reliability",
                severity="critical",
                description="Model crashes or hangs",
                symptoms=[
                    "Process becomes unresponsive",
                    "No output after long wait",
                    "Requires restart"
                ],
                root_cause="Memory leak, corrupted model file, or incompatible settings",
                fixes=[
                    "1. Re-download the model file (may be corrupted)",
                    "2. Reduce batch size and context length",
                    "3. Check for llama.cpp/ollama updates (bug fixes)"
                ],
                verification="Model runs stably for extended sessions"
            ),
            ProblemFix(
                problem_id="REL-002",
                category="reliability",
                severity="major",
                description="Inconsistent output quality",
                symptoms=[
                    "Sometimes great, sometimes terrible",
                    "Same prompt gives wildly different results",
                    "Quality varies unpredictably"
                ],
                root_cause="High temperature or inappropriate sampling settings",
                fixes=[
                    "1. Set temperature to 0.3-0.5 for consistency",
                    "2. Use fixed seed for reproducible results",
                    "3. Set top_p to 0.9 and top_k to 40 for balanced sampling"
                ],
                verification="Similar prompts produce consistent quality"
            ),
            ProblemFix(
                problem_id="VIS-001",
                category="vision",
                severity="major",
                description="Poor image understanding",
                symptoms=[
                    "Misidentifies objects in images",
                    "Ignores important visual elements",
                    "Hallucinates content not in image"
                ],
                root_cause="Vision model not well-trained or image preprocessing issue",
                fixes=[
                    "1. Use a larger vision model (13B+ for complex images)",
                    "2. Resize images to optimal resolution (typically 384x384 or 768x768)",
                    "3. Try different vision architectures (MiniCPM, LLaVA, CogVLM)"
                ],
                verification="Model correctly identifies key image elements"
            ),
            ProblemFix(
                problem_id="VIS-002",
                category="vision",
                severity="major",
                description="Vision model refuses NSFW content",
                symptoms=[
                    "Won't describe adult content",
                    "Adds content warnings",
                    "Provides sanitized descriptions"
                ],
                root_cause="Model has NSFW safety filters active",
                fixes=[
                    "1. Use llava-uncensored or minicpm-uncensored variants",
                    "2. Create abliterated vision model using abliterator tool",
                    "3. Modify system prompt to allow uncensored analysis"
                ],
                verification="Model describes all visible content without censorship"
            ),
            ProblemFix(
                problem_id="CAP-001",
                category="captioning",
                severity="major",
                description="Poor training captions",
                symptoms=[
                    "Captions too generic",
                    "Missing style/composition details",
                    "Inconsistent caption format"
                ],
                root_cause="Vision model not optimized for training data generation",
                fixes=[
                    "1. Use structured captioning prompt with required elements",
                    "2. Post-process with WD14 tagger for booru-style tags",
                    "3. Combine vision caption + tag list for best results"
                ],
                verification="Captions include subject, style, composition, and tags"
            ),
        ]

    def analyze_model(self, model_name: str, benchmark_data: Dict) -> Dict:
        """Analyze a single model and identify issues"""
        analysis = {
            "model_name": model_name,
            "good": [],
            "bad": [],
            "ugly": [],
            "applicable_fixes": [],
            "skillset": None
        }
        
        speed = benchmark_data.get("avg_speed", 0) or 0
        quality = benchmark_data.get("avg_quality", 0) or 0
        test_count = benchmark_data.get("test_count", 0) or 0
        success_count = benchmark_data.get("success_count", 0) or 0
        is_vision = benchmark_data.get("is_vision", 0)
        is_uncensored = benchmark_data.get("is_uncensored", 0)
        params = benchmark_data.get("parameter_count", "unknown")
        
        success_rate = success_count / test_count if test_count > 0 else 0
        
        # === GOOD ===
        if speed >= 100:
            analysis["good"].append("⚡ Excellent speed (100+ tok/s)")
        elif speed >= 50:
            analysis["good"].append("✓ Good speed (50+ tok/s)")
        
        if quality >= 8:
            analysis["good"].append("🌟 Excellent quality output")
        elif quality >= 6:
            analysis["good"].append("✓ Good quality output")
        
        if is_vision:
            analysis["good"].append("👁 Vision capable")
        
        if is_uncensored:
            analysis["good"].append("🔓 Uncensored")
        
        if success_rate >= 0.95:
            analysis["good"].append("✓ Highly reliable (95%+ success)")
        
        if params in ["500M", "1B", "2B", "3B"]:
            analysis["good"].append(f"📦 Small model ({params}) - fast and efficient")
        
        # === BAD ===
        if speed < 20 and speed > 0:
            analysis["bad"].append("🐌 Slow inference (<20 tok/s)")
            analysis["applicable_fixes"].append("PERF-001")
        
        if quality < 5 and quality > 0:
            analysis["bad"].append("⚠️ Low quality output")
            analysis["applicable_fixes"].append("QUAL-001")
        
        if 0.5 < success_rate < 0.9:
            analysis["bad"].append("⚠️ Somewhat unreliable")
        
        if not is_uncensored and is_vision:
            analysis["bad"].append("🔒 Vision model may refuse NSFW")
            analysis["applicable_fixes"].append("VIS-002")
        
        # === UGLY ===
        if speed == 0 and test_count > 0:
            analysis["ugly"].append("💀 Model fails to respond")
            analysis["applicable_fixes"].append("REL-001")
        
        if success_rate < 0.5 and test_count > 0:
            analysis["ugly"].append("💀 Critical reliability issues")
            analysis["applicable_fixes"].append("REL-001")
        
        if quality < 3 and quality > 0:
            analysis["ugly"].append("💀 Unacceptable output quality")
            analysis["applicable_fixes"].append("QUAL-001")
        
        # Generate skillset
        analysis["skillset"] = self._generate_skillset(model_name, benchmark_data)
        self.skillsets[model_name] = analysis["skillset"]
        
        return analysis
    
    def _generate_skillset(self, model_name: str, data: Dict) -> ModelSkillset:
        """Generate model skillset from benchmark data"""
        name_lower = model_name.lower()
        quality = data.get("avg_quality", 5) or 5
        speed = data.get("avg_speed", 50) or 50
        
        skillset = ModelSkillset(model_name=model_name)
        
        # Base text generation from quality
        skillset.text_generation = min(10, int(quality))
        skillset.instruction_following = min(10, int(quality * 0.9))
        
        # Detect specializations from name
        if any(x in name_lower for x in ["code", "coder", "deepseek-coder", "starcoder"]):
            skillset.code_generation = 8
            skillset.recommended_for.append("Code generation and analysis")
        else:
            skillset.code_generation = min(6, int(quality * 0.7))
        
        if any(x in name_lower for x in ["creative", "writer", "story"]):
            skillset.creative_writing = 8
            skillset.recommended_for.append("Creative writing and storytelling")
        else:
            skillset.creative_writing = min(7, int(quality * 0.8))
        
        if any(x in name_lower for x in ["math", "wizard-math", "deepseek-math"]):
            skillset.math = 8
            skillset.recommended_for.append("Mathematical reasoning")
        else:
            skillset.math = min(5, int(quality * 0.6))
        
        if any(x in name_lower for x in ["reason", "think", "o1"]):
            skillset.reasoning = 8
            skillset.recommended_for.append("Complex reasoning tasks")
        else:
            skillset.reasoning = min(6, int(quality * 0.7))
        
        # Vision capability
        if data.get("is_vision"):
            skillset.vision = 7
            skillset.recommended_for.append("Image analysis and captioning")
        
        # Uncensored capability
        if data.get("is_uncensored"):
            skillset.uncensored = 10
            skillset.recommended_for.append("Uncensored content generation")
        
        # Speed tier
        if speed >= 100:
            skillset.speed_tier = "fast"
            skillset.recommended_for.append("High-throughput batch processing")
        elif speed >= 40:
            skillset.speed_tier = "medium"
        else:
            skillset.speed_tier = "slow"
            skillset.not_recommended_for.append("Real-time applications")
        
        # Quality tier
        if quality >= 8:
            skillset.quality_tier = "excellent"
        elif quality >= 6:
            skillset.quality_tier = "good"
        elif quality >= 4:
            skillset.quality_tier = "acceptable"
        else:
            skillset.quality_tier = "poor"
            skillset.not_recommended_for.append("Production use")
        
        return skillset
    
    def generate_all_reports(self):
        """Generate all documentation files"""
        print_section("Generating Reports")
        
        # Analyze all models
        analyses = {}
        for name, data in self.model_benchmarks.items():
            analyses[name] = self.analyze_model(name, data)
        
        # Generate each report
        self._generate_good_bad_ugly_md(analyses)
        self._generate_production_readiness_md(analyses)
        self._generate_skillsets_md()
        self._generate_model_index_json()
        
        print_success("All reports generated!")
    
    def _generate_good_bad_ugly_md(self, analyses: Dict):
        """Generate GOOD_BAD_UGLY.md"""
        output_path = self.docs_dir / "GOOD_BAD_UGLY.md"
        
        report = f"""# 🎯 Model Analysis: Good, Bad & Ugly

> Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
> Models Analyzed: {len(analyses)}

This document provides a frank assessment of each model's strengths and weaknesses,
with actionable fixes for identified problems.

---

## 📊 Quick Summary

| Model | Good | Bad | Ugly | Action Needed |
|-------|------|-----|------|---------------|
"""
        
        for name, analysis in sorted(analyses.items()):
            good_count = len(analysis["good"])
            bad_count = len(analysis["bad"])
            ugly_count = len(analysis["ugly"])
            action = "✓ Ready" if ugly_count == 0 and bad_count == 0 else "⚠️ Needs work" if ugly_count == 0 else "❌ Critical issues"
            
            report += f"| {name[:40]} | {good_count} | {bad_count} | {ugly_count} | {action} |\n"
        
        report += "\n---\n\n## Detailed Analysis\n\n"
        
        for name, analysis in sorted(analyses.items()):
            report += f"### {name}\n\n"
            
            if analysis["good"]:
                report += "**✅ GOOD:**\n"
                for item in analysis["good"]:
                    report += f"- {item}\n"
                report += "\n"
            
            if analysis["bad"]:
                report += "**❌ BAD:**\n"
                for item in analysis["bad"]:
                    report += f"- {item}\n"
                report += "\n"
            
            if analysis["ugly"]:
                report += "**💀 UGLY:**\n"
                for item in analysis["ugly"]:
                    report += f"- {item}\n"
                report += "\n"
            
            if analysis["applicable_fixes"]:
                report += "**🔧 Required Fixes:**\n"
                for fix_id in analysis["applicable_fixes"]:
                    fix = next((p for p in self.problems if p.problem_id == fix_id), None)
                    if fix:
                        report += f"- [{fix_id}] {fix.description}\n"
                report += "\n"
            
            report += "---\n\n"
        
        output_path.write_text(report, encoding='utf-8')
        print_success(f"Generated: {output_path}")
