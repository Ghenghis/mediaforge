"""
LORAFORGE - MODEL CLEANUP ANALYZER
Analyze LM Studio models, find duplicates, outdated versions, and free up space

GOALS:
- Scan all models and their sizes
- Identify duplicates (same model, different quants)
- Find outdated models (replaced by newer versions)
- Track usage (tested vs untested)
- Recommend deletions to free 200GB+
- PROTECT new downloads (last 30 days)
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning


# ============================================
# MODEL INFO
# ============================================

@dataclass
class ModelFile:
    """Information about a model file"""
    path: Path
    name: str
    size_gb: float
    size_bytes: int
    family: str           # llama, qwen, gemma, etc.
    base_model: str       # The actual model name
    version: str          # Version if detectable
    parameter_count: str  # 7B, 3B, etc.
    quantization: str     # Q4_K_M, Q8_0, etc.
    created_date: datetime
    modified_date: datetime
    age_days: int
    is_vision: bool
    is_uncensored: bool
    is_tested: bool = False
    test_count: int = 0
    avg_speed: float = 0
    avg_quality: float = 0


@dataclass
class DuplicateGroup:
    """Group of duplicate/similar models"""
    base_model: str
    models: List[ModelFile]
    total_size_gb: float
    keep_recommendation: str
    delete_candidates: List[ModelFile]
    potential_savings_gb: float


@dataclass
class CleanupReport:
    """Full cleanup analysis report"""
    total_models: int
    total_size_gb: float
    duplicate_groups: List[DuplicateGroup]
    outdated_models: List[ModelFile]
    untested_old_models: List[ModelFile]
    large_unused_models: List[ModelFile]
    new_untested_models: List[ModelFile]  # Protect these!
    recommended_deletions: List[ModelFile]
    potential_savings_gb: float
    keep_list: List[ModelFile]


# ============================================
# MODEL FAMILIES & VERSIONS
# ============================================

# Known model families and their evolution
MODEL_FAMILIES = {
    "llama": {
        "versions": ["1", "2", "3", "3.1", "3.2", "3.3"],
        "latest": "3.3",
        "obsolete": ["1", "2"]
    },
    "qwen": {
        "versions": ["1", "1.5", "2", "2.5"],
        "latest": "2.5",
        "obsolete": ["1", "1.5"]
    },
    "gemma": {
        "versions": ["1", "2"],
        "latest": "2",
        "obsolete": []
    },
    "phi": {
        "versions": ["1", "2", "3", "4"],
        "latest": "4",
        "obsolete": ["1", "2"]
    },
    "mistral": {
        "versions": ["0.1", "0.2", "0.3"],
        "latest": "0.3",
        "obsolete": ["0.1"]
    },
    "deepseek": {
        "versions": ["1", "2", "2.5", "3"],
        "latest": "3",
        "obsolete": ["1"]
    },
    "yi": {
        "versions": ["1", "1.5"],
        "latest": "1.5",
        "obsolete": []
    },
    "codellama": {
        "versions": ["1"],
        "latest": "1",
        "obsolete": []
    },
    "starcoder": {
        "versions": ["1", "2"],
        "latest": "2",
        "obsolete": ["1"]
    }
}

# Quantization quality ranking (higher = better quality, larger size)
QUANT_RANKING = {
    "F32": 100,
    "F16": 95,
    "Q8_0": 90,
    "Q6_K": 85,
    "Q5_K_M": 80,
    "Q5_K_S": 75,
    "Q5_0": 70,
    "Q4_K_M": 65,
    "Q4_K_S": 60,
    "Q4_0": 55,
    "Q3_K_M": 50,
    "Q3_K_S": 45,
    "Q2_K": 40,
    "IQ4_XS": 35,
    "IQ3_XS": 30,
    "IQ2_XS": 25,
    "IQ1_M": 20
}


class ModelCleanupAnalyzer:
    """
    Analyzes LM Studio models and recommends cleanup.
    
    Features:
    - Scan all GGUF files with sizes
    - Identify duplicates (same model, different quants)
    - Find outdated versions
    - Track tested vs untested
    - Recommend deletions to free 200GB
    - PROTECT recent downloads
    """
    
    LMSTUDIO_PATH = Path(os.environ.get(
        "LMSTUDIO_MODELS_PATH", 
        "C:/Users/Admin/.lmstudio/models"
    ))
    
    # Days to consider a model "new" (protect from deletion)
    NEW_MODEL_DAYS = 30
    
    def __init__(self, target_free_gb: float = 200):
        self.target_free_gb = target_free_gb
        self.models: List[ModelFile] = []
        self.db_path = Path(__file__).parent.parent.parent / "data" / "loraforge.db"
    
    def scan_models(self) -> List[ModelFile]:
        """Scan all models in LM Studio directory"""
        print_section("SCANNING LM STUDIO MODELS")
        print_info(f"Path: {self.LMSTUDIO_PATH}")
        
        if not self.LMSTUDIO_PATH.exists():
            print_error(f"LM Studio path not found: {self.LMSTUDIO_PATH}")
            return []
        
        models = []
        total_size = 0
        
        for gguf_file in self.LMSTUDIO_PATH.rglob("*.gguf"):
            try:
                stat = gguf_file.stat()
                size_bytes = stat.st_size
                size_gb = size_bytes / (1024**3)
                total_size += size_gb
                
                created = datetime.fromtimestamp(stat.st_ctime)
                modified = datetime.fromtimestamp(stat.st_mtime)
                age_days = (datetime.now() - modified).days
                
                name = gguf_file.stem
                
                model = ModelFile(
                    path=gguf_file,
                    name=name,
                    size_gb=size_gb,
                    size_bytes=size_bytes,
                    family=self._detect_family(name),
                    base_model=self._extract_base_model(name),
                    version=self._detect_version(name),
                    parameter_count=self._detect_params(name),
                    quantization=self._detect_quantization(name),
                    created_date=created,
                    modified_date=modified,
                    age_days=age_days,
                    is_vision="vision" in name.lower() or "llava" in name.lower(),
                    is_uncensored="uncensored" in name.lower() or "abliterated" in name.lower()
                )
                
                models.append(model)
                
            except Exception as e:
                print_warning(f"Error scanning {gguf_file}: {e}")
        
        # Sort by size (largest first)
        models.sort(key=lambda x: x.size_gb, reverse=True)
        
        self.models = models
        
        print_success(f"Found {len(models)} models")
        print_info(f"Total size: {total_size:.1f} GB")
        
        # Load benchmark data if available
        self._load_benchmark_data()
        
        return models
    
    def _detect_family(self, name: str) -> str:
        """Detect model family from name"""
        name_lower = name.lower()
        
        for family in MODEL_FAMILIES:
            if family in name_lower:
                return family
        
        # Additional patterns
        patterns = [
            ("wizard", "wizard"),
            ("dolphin", "dolphin"),
            ("orca", "orca"),
            ("neural", "neural"),
            ("openchat", "openchat"),
            ("vicuna", "vicuna"),
            ("nous", "nous"),
            ("solar", "solar"),
            ("internlm", "internlm"),
            ("command", "command"),
        ]
        
        for pattern, family in patterns:
            if pattern in name_lower:
                return family
        
        return "unknown"
    
    def _extract_base_model(self, name: str) -> str:
        """Extract base model name (for grouping duplicates)"""
        # Remove quantization suffix
        base = re.sub(r'[-_.]?[QqFf]\d+[-_]?[KkMmSs]?[-_]?[MmSs]?$', '', name)
        base = re.sub(r'[-_.]?[QqFf]\d+[-_]?\d*$', '', base)
        base = re.sub(r'[-_.]?[Ii][Qq]\d+[-_]?[XxSsMm]*$', '', base)
        
        # Remove GGUF suffix
        base = re.sub(r'[-_.]?gguf$', '', base, flags=re.IGNORECASE)
        
        return base.strip('-_.')
    
    def _detect_version(self, name: str) -> str:
        """Detect model version"""
        # Look for version patterns
        patterns = [
            r'[-_]v?(\d+\.\d+)[-_]',
            r'[-_]v?(\d+)[-_]',
            r'llama[-_]?(\d+\.?\d*)[-_]',
            r'qwen[-_]?(\d+\.?\d*)[-_]',
            r'gemma[-_]?(\d+)[-_]',
            r'phi[-_]?(\d+)[-_]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _detect_params(self, name: str) -> str:
        """Detect parameter count"""
        patterns = [
            r'(\d+\.?\d*)[Bb]',
            r'(\d+)[Mm]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                num = match.group(1)
                if 'b' in name[match.start():match.end()].lower():
                    return f"{num}B"
                else:
                    return f"{num}M"
        
        return "unknown"
    
    def _detect_quantization(self, name: str) -> str:
        """Detect quantization level"""
        patterns = [
            r'([QqFf]\d+[-_]?[KkMmSs]?[-_]?[MmSs]?)',
            r'([Ii][Qq]\d+[-_]?[XxSsMm]*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                return match.group(1).upper().replace('-', '_').replace('.', '_')
        
        return "unknown"
    
    def _load_benchmark_data(self):
        """Load benchmark data from database"""
        if not self.db_path.exists():
            return
        
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            
            rows = conn.execute("""
                SELECT m.name, COUNT(b.id) as tests, 
                       AVG(b.tokens_per_second) as speed,
                       AVG(b.output_quality) as quality
                FROM models m
                LEFT JOIN benchmarks b ON b.model_id = m.id
                WHERE m.provider = 'lmstudio'
                GROUP BY m.id
            """).fetchall()
            
            conn.close()
            
            # Match to our models
            benchmark_data = {r["name"]: r for r in rows}
            
            for model in self.models:
                if model.name in benchmark_data:
                    data = benchmark_data[model.name]
                    model.is_tested = data["tests"] > 0
                    model.test_count = data["tests"] or 0
                    model.avg_speed = data["speed"] or 0
                    model.avg_quality = data["quality"] or 0
                    
        except Exception as e:
            print_warning(f"Could not load benchmark data: {e}")
    
    def find_duplicates(self) -> List[DuplicateGroup]:
        """Find duplicate/similar models (same base, different quants)"""
        print_section("FINDING DUPLICATES")
        
        # Group by base model
        groups = defaultdict(list)
        
        for model in self.models:
            key = f"{model.base_model}_{model.parameter_count}"
            groups[key].append(model)
        
        # Find groups with multiple models
        duplicate_groups = []
        
        for base, models in groups.items():
            if len(models) > 1:
                # Sort by quantization quality
                models.sort(key=lambda x: QUANT_RANKING.get(x.quantization, 50), reverse=True)
                
                total_size = sum(m.size_gb for m in models)
                
                # Recommend keeping the best balance of quality/size
                # Usually Q4_K_M or Q5_K_M is good
                keep = None
                for m in models:
                    if m.quantization in ["Q4_K_M", "Q5_K_M", "Q4_K_S"]:
                        keep = m
                        break
                
                if not keep:
                    keep = models[0]  # Keep highest quality
                
                delete_candidates = [m for m in models if m != keep]
                savings = sum(m.size_gb for m in delete_candidates)
                
                group = DuplicateGroup(
                    base_model=base,
                    models=models,
                    total_size_gb=total_size,
                    keep_recommendation=keep.name,
                    delete_candidates=delete_candidates,
                    potential_savings_gb=savings
                )
                
                duplicate_groups.append(group)
        
        # Sort by potential savings
        duplicate_groups.sort(key=lambda x: x.potential_savings_gb, reverse=True)
        
        total_savings = sum(g.potential_savings_gb for g in duplicate_groups)
        print_info(f"Found {len(duplicate_groups)} duplicate groups")
        print_success(f"Potential savings from duplicates: {total_savings:.1f} GB")
        
        return duplicate_groups
    
    def find_outdated(self) -> List[ModelFile]:
        """Find outdated model versions"""
        print_section("FINDING OUTDATED MODELS")
        
        outdated = []
        
        for model in self.models:
            family_info = MODEL_FAMILIES.get(model.family)
            
            if family_info and model.version != "unknown":
                if model.version in family_info.get("obsolete", []):
                    outdated.append(model)
                    continue
                
                # Check if there's a newer version
                latest = family_info.get("latest", "")
                try:
                    if float(model.version) < float(latest):
                        # Check if we have the newer version
                        has_newer = any(
                            m.family == model.family and 
                            m.parameter_count == model.parameter_count and
                            m.version == latest
                            for m in self.models
                        )
                        if has_newer:
                            outdated.append(model)
                except:
                    pass
        
        outdated.sort(key=lambda x: x.size_gb, reverse=True)
        
        total_size = sum(m.size_gb for m in outdated)
        print_info(f"Found {len(outdated)} outdated models")
        print_success(f"Potential savings from outdated: {total_size:.1f} GB")
        
        return outdated
    
    def find_large_unused(self, min_size_gb: float = 5) -> List[ModelFile]:
        """Find large models that haven't been used"""
        print_section("FINDING LARGE UNUSED MODELS")
        
        large_unused = []
        
        for model in self.models:
            # Skip new models
            if model.age_days < self.NEW_MODEL_DAYS:
                continue
            
            if model.size_gb >= min_size_gb and not model.is_tested:
                large_unused.append(model)
        
        large_unused.sort(key=lambda x: x.size_gb, reverse=True)
        
        total_size = sum(m.size_gb for m in large_unused)
        print_info(f"Found {len(large_unused)} large unused models (>{min_size_gb}GB)")
        print_success(f"Potential savings: {total_size:.1f} GB")
        
        return large_unused
    
    def find_new_untested(self) -> List[ModelFile]:
        """Find recently downloaded models that need testing (PROTECT THESE!)"""
        print_section("NEW MODELS TO TEST (PROTECTED)")
        
        new_models = []
        
        for model in self.models:
            if model.age_days <= self.NEW_MODEL_DAYS and not model.is_tested:
                new_models.append(model)
        
        new_models.sort(key=lambda x: x.age_days)
        
        total_size = sum(m.size_gb for m in new_models)
        print_info(f"Found {len(new_models)} new models (< {self.NEW_MODEL_DAYS} days)")
        print_warning(f"These are PROTECTED from deletion ({total_size:.1f} GB)")
        
        return new_models
    
    def generate_cleanup_report(self) -> CleanupReport:
        """Generate comprehensive cleanup report"""
        print_section("GENERATING CLEANUP REPORT")
        
        if not self.models:
            self.scan_models()
        
        # Find all categories
        duplicates = self.find_duplicates()
        outdated = self.find_outdated()
        large_unused = self.find_large_unused()
        new_untested = self.find_new_untested()
        
        # Build deletion recommendations
        recommended = []
        seen_paths = set()
        current_savings = 0
        
        # Priority 1: Duplicate lower-quality quants
        for group in duplicates:
            for model in group.delete_candidates:
                if model.path not in seen_paths:
                    if model.age_days > self.NEW_MODEL_DAYS:  # Don't delete new
                        recommended.append(model)
                        seen_paths.add(model.path)
                        current_savings += model.size_gb
        
        # Priority 2: Outdated models
        for model in outdated:
            if model.path not in seen_paths:
                if model.age_days > self.NEW_MODEL_DAYS:
                    recommended.append(model)
                    seen_paths.add(model.path)
                    current_savings += model.size_gb
        
        # Priority 3: Large unused (if we need more space)
        if current_savings < self.target_free_gb:
            for model in large_unused:
                if model.path not in seen_paths:
                    recommended.append(model)
                    seen_paths.add(model.path)
                    current_savings += model.size_gb
                    
                    if current_savings >= self.target_free_gb:
                        break
        
        # Build keep list
        keep_list = [m for m in self.models if m.path not in seen_paths]
        
        report = CleanupReport(
            total_models=len(self.models),
            total_size_gb=sum(m.size_gb for m in self.models),
            duplicate_groups=duplicates,
            outdated_models=outdated,
            untested_old_models=[m for m in self.models if not m.is_tested and m.age_days > self.NEW_MODEL_DAYS],
            large_unused_models=large_unused,
            new_untested_models=new_untested,
            recommended_deletions=recommended,
            potential_savings_gb=current_savings,
            keep_list=keep_list
        )
        
        return report
    
    def print_report(self, report: CleanupReport):
        """Print cleanup report"""
        print_section("=" * 60)
        print_section("MODEL CLEANUP REPORT")
        print_section("=" * 60)
        
        print(f"\n📊 OVERVIEW")
        print(f"   Total models: {report.total_models}")
        print(f"   Total size: {report.total_size_gb:.1f} GB")
        print(f"   Target free: {self.target_free_gb} GB")
        print(f"   Can free: {report.potential_savings_gb:.1f} GB")
        
        # New models (protected)
        print(f"\n🆕 NEW MODELS (PROTECTED - DO NOT DELETE)")
        print(f"   Count: {len(report.new_untested_models)}")
        for m in report.new_untested_models[:10]:
            print(f"   - {m.name[:50]} ({m.size_gb:.1f}GB, {m.age_days}d old)")
        if len(report.new_untested_models) > 10:
            print(f"   ... and {len(report.new_untested_models) - 10} more")
        
        # Duplicates
        print(f"\n🔄 DUPLICATE GROUPS ({len(report.duplicate_groups)} groups)")
        for group in report.duplicate_groups[:5]:
            print(f"\n   {group.base_model}")
            print(f"   ✓ KEEP: {group.keep_recommendation}")
            for m in group.delete_candidates[:3]:
                print(f"   ✗ DELETE: {m.name} ({m.size_gb:.1f}GB)")
            print(f"   Savings: {group.potential_savings_gb:.1f} GB")
        
        # Outdated
        print(f"\n📅 OUTDATED MODELS ({len(report.outdated_models)})")
        for m in report.outdated_models[:5]:
            print(f"   - {m.name[:50]} ({m.size_gb:.1f}GB, v{m.version})")
        
        # Large unused
        print(f"\n💾 LARGE UNUSED ({len(report.large_unused_models)})")
        for m in report.large_unused_models[:5]:
            print(f"   - {m.name[:50]} ({m.size_gb:.1f}GB, {m.age_days}d unused)")
        
        # Recommended deletions
        print(f"\n🗑️  RECOMMENDED DELETIONS ({len(report.recommended_deletions)} files)")
        print(f"   Total savings: {report.potential_savings_gb:.1f} GB")
        print(f"\n   Top 10 by size:")
        for m in sorted(report.recommended_deletions, key=lambda x: x.size_gb, reverse=True)[:10]:
            reason = "duplicate" if any(m in g.delete_candidates for g in report.duplicate_groups) else "outdated/unused"
            print(f"   - {m.name[:45]:<45} {m.size_gb:>6.1f}GB  [{reason}]")
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"   KEEP: {len(report.keep_list)} models ({sum(m.size_gb for m in report.keep_list):.1f} GB)")
        print(f"   DELETE: {len(report.recommended_deletions)} models ({report.potential_savings_gb:.1f} GB)")
        print(f"=" * 60)
    
    def export_deletion_list(self, report: CleanupReport, output_path: Path = None) -> Path:
        """Export deletion list to file for review"""
        if output_path is None:
            output_path = Path(__file__).parent.parent.parent / "reports" / "model_cleanup.json"
        
        output_path.parent.mkdir(exist_ok=True)
        
        data = {
            "generated": datetime.now().isoformat(),
            "summary": {
                "total_models": report.total_models,
                "total_size_gb": report.total_size_gb,
                "to_delete": len(report.recommended_deletions),
                "savings_gb": report.potential_savings_gb
            },
            "protected_new_models": [
                {"name": m.name, "size_gb": m.size_gb, "age_days": m.age_days}
                for m in report.new_untested_models
            ],
            "recommended_deletions": [
                {
                    "path": str(m.path),
                    "name": m.name,
                    "size_gb": m.size_gb,
                    "age_days": m.age_days,
                    "reason": self._get_deletion_reason(m, report)
                }
                for m in report.recommended_deletions
            ],
            "keep_list": [
                {"name": m.name, "size_gb": m.size_gb, "tested": m.is_tested}
                for m in report.keep_list
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print_success(f"Deletion list saved: {output_path}")
        
        # Also create a simple batch script
        batch_path = output_path.with_suffix('.ps1')
        with open(batch_path, 'w') as f:
            f.write("# LM Studio Model Cleanup Script\n")
            f.write("# REVIEW CAREFULLY BEFORE RUNNING!\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Total savings: {report.potential_savings_gb:.1f} GB\n\n")
            
            for m in report.recommended_deletions:
                f.write(f'# {m.name} ({m.size_gb:.1f}GB)\n')
                f.write(f'Remove-Item -Path "{m.path}" -WhatIf\n\n')
        
        print_info(f"PowerShell script saved: {batch_path}")
        print_warning("Remove -WhatIf to actually delete files!")
        
        return output_path
    
    def _get_deletion_reason(self, model: ModelFile, report: CleanupReport) -> str:
        """Get reason for deletion recommendation"""
        for group in report.duplicate_groups:
            if model in group.delete_candidates:
                return f"Duplicate of {group.keep_recommendation}"
        
        if model in report.outdated_models:
            return f"Outdated version (v{model.version})"
        
        if model in report.large_unused_models:
            return f"Large and unused for {model.age_days} days"
        
        return "Unknown"
    
    def execute_cleanup(self, report: CleanupReport, dry_run: bool = True) -> Dict:
        """Execute the cleanup (with dry_run safety!)"""
        print_section("EXECUTING CLEANUP" + (" (DRY RUN)" if dry_run else ""))
        
        results = {
            "deleted": [],
            "failed": [],
            "skipped": [],
            "total_freed_gb": 0
        }
        
        for model in report.recommended_deletions:
            # Safety check - never delete new models
            if model.age_days < self.NEW_MODEL_DAYS:
                results["skipped"].append({"path": str(model.path), "reason": "Too new"})
                continue
            
            if dry_run:
                print_info(f"Would delete: {model.name} ({model.size_gb:.1f}GB)")
                results["deleted"].append({"path": str(model.path), "size_gb": model.size_gb})
                results["total_freed_gb"] += model.size_gb
            else:
                try:
                    model.path.unlink()
                    print_success(f"Deleted: {model.name}")
                    results["deleted"].append({"path": str(model.path), "size_gb": model.size_gb})
                    results["total_freed_gb"] += model.size_gb
                except Exception as e:
                    print_error(f"Failed to delete {model.name}: {e}")
                    results["failed"].append({"path": str(model.path), "error": str(e)})
        
        print_section("CLEANUP COMPLETE")
        print_success(f"Freed: {results['total_freed_gb']:.1f} GB")
        print_info(f"Deleted: {len(results['deleted'])} files")
        if results["failed"]:
            print_warning(f"Failed: {len(results['failed'])} files")
        
        return results


def analyze_models():
    """Quick analysis of LM Studio models"""
    analyzer = ModelCleanupAnalyzer(target_free_gb=200)
    report = analyzer.generate_cleanup_report()
    analyzer.print_report(report)
    analyzer.export_deletion_list(report)
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Cleanup Analyzer")
    parser.add_argument("--scan", action="store_true", help="Just scan models")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--export", action="store_true", help="Export deletion list")
    parser.add_argument("--target", type=float, default=200, help="Target GB to free")
    parser.add_argument("--execute", action="store_true", help="Execute cleanup (DRY RUN)")
    parser.add_argument("--force", action="store_true", help="Actually delete (DANGEROUS!)")
    
    args = parser.parse_args()
    
    analyzer = ModelCleanupAnalyzer(target_free_gb=args.target)
    
    if args.scan:
        models = analyzer.scan_models()
        print(f"\nTop 20 largest models:")
        for m in models[:20]:
            tested = "✓" if m.is_tested else " "
            new = "🆕" if m.age_days < 30 else "  "
            print(f"  {new} [{tested}] {m.name[:45]:<45} {m.size_gb:>6.1f}GB  {m.age_days:>3}d")
    
    elif args.report or args.export:
        report = analyzer.generate_cleanup_report()
        analyzer.print_report(report)
        
        if args.export:
            analyzer.export_deletion_list(report)
    
    elif args.execute:
        report = analyzer.generate_cleanup_report()
        analyzer.print_report(report)
        
        if args.force:
            print_warning("\n⚠️  FORCE MODE - FILES WILL BE DELETED!")
            confirm = input("Type 'DELETE' to confirm: ")
            if confirm == "DELETE":
                analyzer.execute_cleanup(report, dry_run=False)
            else:
                print_info("Aborted")
        else:
            analyzer.execute_cleanup(report, dry_run=True)
    
    else:
        # Default: full analysis
        analyze_models()
