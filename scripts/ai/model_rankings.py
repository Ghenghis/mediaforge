"""
LORAFORGE - MODEL RANKINGS & COMBINATIONS
Find top 10/20 models for each use case
Test single vs dual model configurations
Document best performers for seamless integration

USE CASES:
- caption: Image captioning for training data
- vision: Image analysis and understanding  
- chat: General conversation and instructions
- code: Code generation and analysis
- creative: Creative writing and storytelling
- speed: Fastest response for quick tasks
- quality: Highest quality output regardless of speed

MODEL CONFIGURATIONS:
- Single: One model handles everything
- Dual Speed+Quality: Fast model for drafts, quality model for refinement
- Dual Small+Large: Small for simple, large for complex
- Specialized: Different model per task type
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import sqlite3

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning
from ai.model_manager import ModelManager, get_model_manager


# ============================================
# RANKING SCHEMA
# ============================================

RANKING_SCHEMA = """
CREATE TABLE IF NOT EXISTS use_case_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    use_case TEXT NOT NULL,
    rank INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    provider TEXT NOT NULL,
    avg_speed REAL,
    avg_quality REAL,
    overall_score REAL,
    test_count INTEGER,
    strengths TEXT,      -- JSON array
    weaknesses TEXT,     -- JSON array
    best_for TEXT,       -- What this model excels at
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(use_case, rank)
);

CREATE TABLE IF NOT EXISTS model_combinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    combo_name TEXT UNIQUE NOT NULL,
    combo_type TEXT NOT NULL,  -- single, dual_speed_quality, dual_small_large, specialized
    primary_model TEXT,
    primary_provider TEXT,
    secondary_model TEXT,
    secondary_provider TEXT,
    use_case TEXT,
    combined_score REAL,
    speed_score REAL,
    quality_score REAL,
    notes TEXT,
    tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommended_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name TEXT UNIQUE NOT NULL,
    description TEXT,
    models_json TEXT,     -- JSON config
    total_vram_gb REAL,
    recommended_for TEXT,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rankings_usecase ON use_case_rankings(use_case);
CREATE INDEX IF NOT EXISTS idx_rankings_score ON use_case_rankings(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_combos_type ON model_combinations(combo_type);
"""


# ============================================
# USE CASE DEFINITIONS
# ============================================

USE_CASES = {
    "caption": {
        "name": "Image Captioning",
        "description": "Generate training captions for images",
        "requires_vision": True,
        "speed_weight": 0.4,
        "quality_weight": 0.6,
        "test_prompt": "Describe this image in detail for AI training. Include subject, pose, clothing, background, and art style."
    },
    "vision": {
        "name": "Vision Analysis", 
        "description": "Analyze and understand image content",
        "requires_vision": True,
        "speed_weight": 0.3,
        "quality_weight": 0.7,
        "test_prompt": "Analyze this image completely. Describe everything you see including people, objects, colors, composition, and mood."
    },
    "chat": {
        "name": "Chat/Instructions",
        "description": "General conversation and following instructions",
        "requires_vision": False,
        "speed_weight": 0.5,
        "quality_weight": 0.5,
        "test_prompt": "You are a helpful AI assistant. Explain the benefits of local AI models in 3 concise points."
    },
    "code": {
        "name": "Code Generation",
        "description": "Write and analyze code",
        "requires_vision": False,
        "speed_weight": 0.3,
        "quality_weight": 0.7,
        "test_prompt": "Write a Python function that efficiently finds duplicate files using SHA256 hashing."
    },
    "creative": {
        "name": "Creative Writing",
        "description": "Stories, descriptions, creative content",
        "requires_vision": False,
        "speed_weight": 0.2,
        "quality_weight": 0.8,
        "test_prompt": "Write a vivid, engaging paragraph describing a cyberpunk city at night."
    },
    "speed": {
        "name": "Speed Priority",
        "description": "Fastest possible response for simple tasks",
        "requires_vision": False,
        "speed_weight": 0.9,
        "quality_weight": 0.1,
        "test_prompt": "List 5 colors."
    },
    "quality": {
        "name": "Quality Priority",
        "description": "Best possible output regardless of time",
        "requires_vision": False,
        "speed_weight": 0.1,
        "quality_weight": 0.9,
        "test_prompt": "Provide a comprehensive analysis of the advantages and disadvantages of different AI model architectures."
    }
}


@dataclass
class ModelRanking:
    """A model's ranking for a use case"""
    use_case: str
    rank: int
    model_name: str
    provider: str
    avg_speed: float
    avg_quality: float
    overall_score: float
    test_count: int
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    best_for: str = ""


@dataclass 
class ModelCombination:
    """A combination of models for optimal performance"""
    combo_name: str
    combo_type: str
    primary_model: str
    primary_provider: str
    secondary_model: str = None
    secondary_provider: str = None
    use_case: str = "general"
    combined_score: float = 0
    speed_score: float = 0
    quality_score: float = 0
    notes: str = ""


class ModelRankingSystem:
    """
    Comprehensive model ranking and combination system.
    
    Features:
    - Top 10/20 models per use case
    - Single vs dual model comparisons
    - Small+Small vs Small+Large testing
    - Automatic best configuration selection
    - Documented strengths/weaknesses
    """
    
    def __init__(self, db_path: Path = None):
        self.manager = get_model_manager()
        
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "loraforge.db"
        
        self.db_path = db_path
        self._init_schema()
    
    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_schema(self):
        conn = self._get_conn()
        conn.executescript(RANKING_SCHEMA)
        conn.commit()
        conn.close()
    
    # ========================================
    # RANKING GENERATION
    # ========================================
    
    def generate_rankings(self, use_case: str, top_n: int = 20) -> List[ModelRanking]:
        """
        Generate top N rankings for a use case.
        
        Args:
            use_case: Use case to rank for
            top_n: Number of top models to return
        """
        print_section(f"Generating Top {top_n} for: {use_case.upper()}")
        
        uc_config = USE_CASES.get(use_case, USE_CASES["chat"])
        speed_weight = uc_config["speed_weight"]
        quality_weight = uc_config["quality_weight"]
        
        conn = self._get_conn()
        
        # Get all benchmarks for this task type
        # Map use_case to task_type in benchmarks
        task_type = use_case if use_case in ["chat", "caption", "code", "creative"] else "chat"
        
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
                MAX(b.tokens_per_second) as max_speed,
                MIN(b.tokens_per_second) as min_speed
            FROM models m
            JOIN benchmarks b ON b.model_id = m.id
            WHERE b.task_type = ? AND b.success = 1
            GROUP BY m.id
            HAVING test_count >= 1
            ORDER BY (AVG(b.tokens_per_second) / 100 * ? + AVG(b.output_quality) * ?) DESC
            LIMIT ?
        """, (task_type, speed_weight, quality_weight, top_n)).fetchall()
        
        conn.close()
        
        rankings = []
        
        for i, row in enumerate(rows, 1):
            # Calculate overall score
            speed_score = min(10, row["avg_speed"] / 10)  # Normalize to 0-10
            quality_score = row["avg_quality"]
            overall = speed_score * speed_weight + quality_score * quality_weight
            
            # Determine strengths/weaknesses
            strengths = []
            weaknesses = []
            
            if row["avg_speed"] > 100:
                strengths.append("Very fast (100+ tok/s)")
            elif row["avg_speed"] > 50:
                strengths.append("Good speed (50+ tok/s)")
            elif row["avg_speed"] < 20:
                weaknesses.append("Slow (<20 tok/s)")
            
            if row["avg_quality"] >= 8:
                strengths.append("Excellent quality")
            elif row["avg_quality"] >= 6:
                strengths.append("Good quality")
            elif row["avg_quality"] < 5:
                weaknesses.append("Quality needs improvement")
            
            if row["is_uncensored"]:
                strengths.append("Uncensored")
            
            if row["is_vision"]:
                strengths.append("Vision capable")
            
            param = row["parameter_count"]
            if param in ["500M", "1B", "2B", "3B"]:
                strengths.append(f"Small model ({param})")
            elif param in ["70B", "72B"]:
                weaknesses.append("Large model (high VRAM)")
            
            # Best for description
            if row["avg_speed"] > 80 and row["avg_quality"] >= 6:
                best_for = "Balanced speed and quality"
            elif row["avg_speed"] > 100:
                best_for = "Quick tasks, drafts, iteration"
            elif row["avg_quality"] >= 8:
                best_for = "Final output, quality-critical tasks"
            else:
                best_for = "General use"
            
            ranking = ModelRanking(
                use_case=use_case,
                rank=i,
                model_name=row["name"],
                provider=row["provider"],
                avg_speed=row["avg_speed"],
                avg_quality=row["avg_quality"],
                overall_score=overall,
                test_count=row["test_count"],
                strengths=strengths,
                weaknesses=weaknesses,
                best_for=best_for
            )
            
            rankings.append(ranking)
            
            # Save to database
            self._save_ranking(ranking)
        
        print_success(f"Generated {len(rankings)} rankings")
        
        return rankings
    
    def _save_ranking(self, ranking: ModelRanking):
        """Save ranking to database"""
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO use_case_rankings
            (use_case, rank, model_name, provider, avg_speed, avg_quality,
             overall_score, test_count, strengths, weaknesses, best_for)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ranking.use_case, ranking.rank, ranking.model_name, ranking.provider,
            ranking.avg_speed, ranking.avg_quality, ranking.overall_score,
            ranking.test_count, json.dumps(ranking.strengths),
            json.dumps(ranking.weaknesses), ranking.best_for
        ))
        conn.commit()
        conn.close()
    
    def generate_all_rankings(self, top_n: int = 20) -> Dict[str, List[ModelRanking]]:
        """Generate rankings for all use cases"""
        all_rankings = {}
        
        for use_case in USE_CASES:
            rankings = self.generate_rankings(use_case, top_n)
            all_rankings[use_case] = rankings
        
        return all_rankings
    
    # ========================================
    # MODEL COMBINATIONS
    # ========================================
    
    def test_combination(
        self,
        primary: str,
        primary_provider: str,
        secondary: str = None,
        secondary_provider: str = None,
        combo_type: str = "single"
    ) -> ModelCombination:
        """
        Test a model combination.
        
        Combo types:
        - single: One model for everything
        - dual_speed_quality: Fast model + quality model
        - dual_small_large: Small for simple, large for complex
        """
        print_section(f"Testing Combination: {combo_type}")
        
        combo_name = f"{primary}"
        if secondary:
            combo_name += f" + {secondary}"
        
        print_info(f"Primary: {primary} ({primary_provider})")
        if secondary:
            print_info(f"Secondary: {secondary} ({secondary_provider})")
        
        # Test primary model
        primary_result = self.manager.benchmark_model(primary, primary_provider, "chat")
        
        primary_speed = primary_result.tokens_per_second if primary_result else 0
        primary_quality = primary_result.output_quality if primary_result else 0
        
        # Test secondary if provided
        secondary_speed = 0
        secondary_quality = 0
        
        if secondary:
            secondary_result = self.manager.benchmark_model(secondary, secondary_provider, "chat")
            secondary_speed = secondary_result.tokens_per_second if secondary_result else 0
            secondary_quality = secondary_result.output_quality if secondary_result else 0
        
        # Calculate combined scores based on combo type
        if combo_type == "single":
            combined_speed = primary_speed
            combined_quality = primary_quality
            notes = "Single model configuration"
            
        elif combo_type == "dual_speed_quality":
            # Speed from primary, quality from secondary
            combined_speed = primary_speed * 0.7 + secondary_speed * 0.3  # Mostly use fast
            combined_quality = primary_quality * 0.3 + secondary_quality * 0.7  # Quality from second
            notes = f"Fast drafts with {primary}, polish with {secondary}"
            
        elif combo_type == "dual_small_large":
            # Use small for most, large for complex
            combined_speed = primary_speed * 0.6 + secondary_speed * 0.4
            combined_quality = primary_quality * 0.4 + secondary_quality * 0.6
            notes = f"Simple tasks: {primary}, Complex: {secondary}"
            
        else:
            combined_speed = primary_speed
            combined_quality = primary_quality
            notes = "Custom configuration"
        
        combined_score = (combined_speed / 20) + (combined_quality * 0.8)
        
        combo = ModelCombination(
            combo_name=combo_name,
            combo_type=combo_type,
            primary_model=primary,
            primary_provider=primary_provider,
            secondary_model=secondary,
            secondary_provider=secondary_provider,
            combined_score=combined_score,
            speed_score=combined_speed,
            quality_score=combined_quality,
            notes=notes
        )
        
        # Save to database
        self._save_combination(combo)
        
        print_success(f"Combined Score: {combined_score:.1f}")
        print_info(f"Speed: {combined_speed:.0f} tok/s")
        print_info(f"Quality: {combined_quality:.1f}/10")
        
        return combo
    
    def _save_combination(self, combo: ModelCombination):
        """Save combination to database"""
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO model_combinations
            (combo_name, combo_type, primary_model, primary_provider,
             secondary_model, secondary_provider, use_case,
             combined_score, speed_score, quality_score, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            combo.combo_name, combo.combo_type, combo.primary_model,
            combo.primary_provider, combo.secondary_model, combo.secondary_provider,
            combo.use_case, combo.combined_score, combo.speed_score,
            combo.quality_score, combo.notes
        ))
        conn.commit()
        conn.close()
    
    def find_best_combinations(self) -> Dict[str, ModelCombination]:
        """
        Find the best model combinations.
        
        Tests:
        - Best single model
        - Best small+small combo
        - Best small+large combo
        - Best speed+quality combo
        """
        print_section("FINDING BEST COMBINATIONS")
        
        results = {}
        
        # Get top models by category
        conn = self._get_conn()
        
        # Fast small models (for speed)
        fast_small = conn.execute("""
            SELECT m.name, m.provider, AVG(b.tokens_per_second) as speed
            FROM models m
            JOIN benchmarks b ON b.model_id = m.id
            WHERE m.parameter_count IN ('500M', '1B', '2B', '3B') AND b.success = 1
            GROUP BY m.id
            ORDER BY speed DESC
            LIMIT 5
        """).fetchall()
        
        # Quality models (larger)
        quality_large = conn.execute("""
            SELECT m.name, m.provider, AVG(b.output_quality) as quality
            FROM models m
            JOIN benchmarks b ON b.model_id = m.id
            WHERE m.parameter_count IN ('7B', '8B', '13B', '14B') AND b.success = 1
            GROUP BY m.id
            ORDER BY quality DESC
            LIMIT 5
        """).fetchall()
        
        # Best overall single
        best_single = conn.execute("""
            SELECT m.name, m.provider, 
                   AVG(b.tokens_per_second) as speed,
                   AVG(b.output_quality) as quality
            FROM models m
            JOIN benchmarks b ON b.model_id = m.id
            WHERE b.success = 1
            GROUP BY m.id
            ORDER BY (AVG(b.tokens_per_second)/20 + AVG(b.output_quality)*0.8) DESC
            LIMIT 1
        """).fetchone()
        
        conn.close()
        
        # Test best single
        if best_single:
            print_info(f"\n🥇 BEST SINGLE: {best_single['name']}")
            results["single"] = self.test_combination(
                best_single["name"], best_single["provider"], combo_type="single"
            )
        
        # Test best small + small
        if len(fast_small) >= 2:
            print_info(f"\n⚡ BEST SMALL+SMALL: {fast_small[0]['name']} + {fast_small[1]['name']}")
            results["small_small"] = self.test_combination(
                fast_small[0]["name"], fast_small[0]["provider"],
                fast_small[1]["name"], fast_small[1]["provider"],
                combo_type="dual_speed_quality"
            )
        
        # Test best small + large
        if fast_small and quality_large:
            print_info(f"\n🔄 BEST SMALL+LARGE: {fast_small[0]['name']} + {quality_large[0]['name']}")
            results["small_large"] = self.test_combination(
                fast_small[0]["name"], fast_small[0]["provider"],
                quality_large[0]["name"], quality_large[0]["provider"],
                combo_type="dual_small_large"
            )
        
        # Determine overall winner
        if results:
            winner = max(results.items(), key=lambda x: x[1].combined_score)
            print_section(f"🏆 WINNER: {winner[0].upper()}")
            print_success(f"{winner[1].combo_name}")
            print_info(f"Score: {winner[1].combined_score:.1f}")
            print_info(f"Notes: {winner[1].notes}")
        
        return results
    
    # ========================================
    # RECOMMENDED CONFIGURATIONS
    # ========================================
    
    def create_recommended_config(
        self,
        config_name: str,
        description: str,
        models: Dict,
        vram_gb: float,
        recommended_for: str
    ):
        """Create a recommended configuration"""
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO recommended_configs
            (config_name, description, models_json, total_vram_gb, recommended_for)
            VALUES (?, ?, ?, ?, ?)
        """, (config_name, description, json.dumps(models), vram_gb, recommended_for))
        conn.commit()
        conn.close()
    
    def generate_recommended_configs(self) -> List[Dict]:
        """Generate recommended configurations based on rankings"""
        print_section("GENERATING RECOMMENDED CONFIGS")
        
        configs = []
        
        # Config 1: Speed Priority (Small Models)
        rankings = self.get_rankings("speed", top_n=3)
        if rankings:
            config = {
                "name": "speed_priority",
                "description": "Maximum speed for quick iterations",
                "models": {
                    "primary": rankings[0]["model_name"],
                    "provider": rankings[0]["provider"],
                    "fallback": rankings[1]["model_name"] if len(rankings) > 1 else None
                },
                "vram_gb": 4,
                "recommended_for": "Quick tasks, drafts, high-volume processing"
            }
            self.create_recommended_config(**config)
            configs.append(config)
        
        # Config 2: Quality Priority (Best Quality)
        rankings = self.get_rankings("quality", top_n=3)
        if rankings:
            config = {
                "name": "quality_priority",
                "description": "Highest quality output",
                "models": {
                    "primary": rankings[0]["model_name"],
                    "provider": rankings[0]["provider"]
                },
                "vram_gb": 16,
                "recommended_for": "Final output, quality-critical content"
            }
            self.create_recommended_config(**config)
            configs.append(config)
        
        # Config 3: Balanced (Speed + Quality)
        speed_ranks = self.get_rankings("speed", top_n=1)
        quality_ranks = self.get_rankings("quality", top_n=1)
        if speed_ranks and quality_ranks:
            config = {
                "name": "balanced",
                "description": "Fast model for drafts, quality model for polish",
                "models": {
                    "fast": speed_ranks[0]["model_name"],
                    "fast_provider": speed_ranks[0]["provider"],
                    "quality": quality_ranks[0]["model_name"],
                    "quality_provider": quality_ranks[0]["provider"]
                },
                "vram_gb": 12,
                "recommended_for": "General use, iterative refinement"
            }
            self.create_recommended_config(**config)
            configs.append(config)
        
        # Config 4: Caption Specialist
        rankings = self.get_rankings("caption", top_n=1)
        if rankings:
            config = {
                "name": "caption_specialist",
                "description": "Optimized for image captioning",
                "models": {
                    "primary": rankings[0]["model_name"],
                    "provider": rankings[0]["provider"]
                },
                "vram_gb": 8,
                "recommended_for": "Dataset preparation, image captioning"
            }
            self.create_recommended_config(**config)
            configs.append(config)
        
        print_success(f"Generated {len(configs)} configurations")
        
        return configs
    
    # ========================================
    # RETRIEVAL
    # ========================================
    
    def get_rankings(self, use_case: str, top_n: int = 10) -> List[Dict]:
        """Get rankings for a use case"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM use_case_rankings
            WHERE use_case = ?
            ORDER BY rank ASC
            LIMIT ?
        """, (use_case, top_n)).fetchall()
        conn.close()
        
        return [
            {
                "rank": r["rank"],
                "model_name": r["model_name"],
                "provider": r["provider"],
                "avg_speed": r["avg_speed"],
                "avg_quality": r["avg_quality"],
                "overall_score": r["overall_score"],
                "test_count": r["test_count"],
                "strengths": json.loads(r["strengths"]) if r["strengths"] else [],
                "weaknesses": json.loads(r["weaknesses"]) if r["weaknesses"] else [],
                "best_for": r["best_for"]
            }
            for r in rows
        ]
    
    def get_all_rankings(self, top_n: int = 10) -> Dict[str, List[Dict]]:
        """Get rankings for all use cases"""
        return {uc: self.get_rankings(uc, top_n) for uc in USE_CASES}
    
    def get_recommended_configs(self) -> List[Dict]:
        """Get all recommended configurations"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM recommended_configs
            ORDER BY priority DESC
        """).fetchall()
        conn.close()
        
        return [
            {
                "name": r["config_name"],
                "description": r["description"],
                "models": json.loads(r["models_json"]),
                "vram_gb": r["total_vram_gb"],
                "recommended_for": r["recommended_for"]
            }
            for r in rows
        ]
    
    def get_best_for_task(self, task: str) -> Optional[Dict]:
        """Get the best model for a specific task"""
        rankings = self.get_rankings(task, top_n=1)
        return rankings[0] if rankings else None
    
    # ========================================
    # DOCUMENTATION
    # ========================================
    
    def generate_documentation(self) -> str:
        """Generate markdown documentation of all rankings"""
        doc = """# 🏆 LORAFORGE MODEL RANKINGS

## Overview
This document contains the top-performing models for each use case,
tested and ranked by the automated benchmarking system.

"""
        
        for use_case, config in USE_CASES.items():
            rankings = self.get_rankings(use_case, top_n=10)
            
            doc += f"""
## {config['name']}
**Purpose:** {config['description']}
**Speed Weight:** {config['speed_weight']:.0%} | **Quality Weight:** {config['quality_weight']:.0%}

| Rank | Model | Speed | Quality | Score | Best For |
|------|-------|-------|---------|-------|----------|
"""
            
            for r in rankings:
                doc += f"| {r['rank']} | {r['model_name'][:30]} | {r['avg_speed']:.0f} tok/s | {r['avg_quality']:.1f}/10 | {r['overall_score']:.1f} | {r['best_for']} |\n"
        
        # Combinations
        doc += """
## 🔄 Recommended Configurations

"""
        
        configs = self.get_recommended_configs()
        for config in configs:
            doc += f"""
### {config['name'].replace('_', ' ').title()}
**{config['description']}**
- VRAM Required: {config['vram_gb']} GB
- Recommended For: {config['recommended_for']}
- Models: {json.dumps(config['models'], indent=2)}

"""
        
        return doc
    
    def save_documentation(self, path: Path = None):
        """Save documentation to file"""
        if path is None:
            path = Path(__file__).parent.parent.parent / "docs" / "MODEL-RANKINGS.md"
        
        path.parent.mkdir(exist_ok=True)
        
        doc = self.generate_documentation()
        path.write_text(doc, encoding='utf-8')
        
        print_success(f"Documentation saved: {path}")


def print_top_models():
    """Print top models for each use case"""
    ranking_system = ModelRankingSystem()
    
    print_section("TOP 10 MODELS BY USE CASE")
    
    for use_case, config in USE_CASES.items():
        rankings = ranking_system.get_rankings(use_case, top_n=10)
        
        if rankings:
            print(f"\n{'='*60}")
            print(f"  {config['name'].upper()}")
            print(f"  {config['description']}")
            print(f"{'='*60}")
            
            for r in rankings:
                strengths = ', '.join(r['strengths'][:2]) if r['strengths'] else ''
                print(f"  {r['rank']:2}. {r['model_name'][:35]:<35}")
                print(f"      Speed: {r['avg_speed']:>6.0f} tok/s | Quality: {r['avg_quality']:.1f}/10 | Score: {r['overall_score']:.1f}")
                if strengths:
                    print(f"      ✓ {strengths}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Rankings")
    parser.add_argument("--generate", action="store_true", help="Generate all rankings")
    parser.add_argument("--combos", action="store_true", help="Find best combinations")
    parser.add_argument("--configs", action="store_true", help="Generate recommended configs")
    parser.add_argument("--show", action="store_true", help="Show current rankings")
    parser.add_argument("--docs", action="store_true", help="Generate documentation")
    parser.add_argument("--use-case", type=str, help="Specific use case")
    parser.add_argument("--top", type=int, default=10, help="Top N to show")
    
    args = parser.parse_args()
    
    ranking_system = ModelRankingSystem()
    
    if args.generate:
        ranking_system.generate_all_rankings(top_n=20)
    elif args.combos:
        ranking_system.find_best_combinations()
    elif args.configs:
        ranking_system.generate_recommended_configs()
    elif args.show:
        print_top_models()
    elif args.docs:
        ranking_system.save_documentation()
    elif args.use_case:
        rankings = ranking_system.get_rankings(args.use_case, args.top)
        for r in rankings:
            print(f"{r['rank']}. {r['model_name']} - Score: {r['overall_score']:.1f}")
    else:
        # Default: show rankings and best combos
        print_top_models()
        print("\n")
        ranking_system.find_best_combinations()
