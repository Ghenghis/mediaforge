"""
LORAFORGE - SELF-LEARNING DATA SYSTEM
Tagging, feedback loops, and continuous improvement
Data enhances itself using collected learnings

CORE PRINCIPLES:
1. Never destroy data - archive and version everything
2. Learn from user feedback and model results
3. Tags evolve based on what produces good models
4. Quality criteria auto-adjust based on outcomes
5. Continuous polishing without damage

TAGGING SYSTEM:
- Source Tags: origin of data (video, upload, scrape)
- Content Tags: what's in the image (auto-generated)
- Quality Tags: technical quality metrics
- Training Tags: used in which model version
- Feedback Tags: user approval/rejection
- Learning Tags: auto-improved based on results
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Set, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import print_section, print_success, print_error, print_info, print_warning


# ============================================
# TAG TYPES
# ============================================

class TagCategory(Enum):
    """Tag categories for organization"""
    SOURCE = "source"           # Where data came from
    CONTENT = "content"         # What's in the image
    QUALITY = "quality"         # Technical quality
    TRAINING = "training"       # Training usage
    FEEDBACK = "feedback"       # User feedback
    LEARNING = "learning"       # Auto-learned tags
    CUSTOM = "custom"           # User-defined


class FeedbackType(Enum):
    """User feedback types"""
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    FAVORITE = "favorite"
    NEEDS_REVIEW = "needs_review"


@dataclass
class Tag:
    """A single tag"""
    name: str
    category: str
    confidence: float = 1.0  # 0-1, how confident in this tag
    source: str = "manual"   # manual, auto, learned
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class LearningRecord:
    """Record of what we learned from data"""
    media_id: int
    model_version: str
    outcome: str  # success, failure, partial
    metrics: Dict[str, float] = field(default_factory=dict)
    learned_at: str = None
    
    def __post_init__(self):
        if self.learned_at is None:
            self.learned_at = datetime.now().isoformat()


# ============================================
# DATABASE SCHEMA FOR LEARNING
# ============================================

LEARNING_SCHEMA = """
-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source TEXT DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(media_id, name, category)
);

-- User feedback
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL,
    feedback_type TEXT NOT NULL,
    rating INTEGER,  -- 1-10 scale
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Training usage tracking
CREATE TABLE IF NOT EXISTS training_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL,
    model_version TEXT NOT NULL,
    dataset_split TEXT,  -- train, val, test
    outcome TEXT,        -- success, failure
    contribution_score REAL,  -- how much this image helped
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learning history (what we learned from outcomes)
CREATE TABLE IF NOT EXISTS learning_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    learning_type TEXT,  -- filter_adjustment, tag_weight, quality_threshold
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    confidence REAL,
    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality criteria evolution
CREATE TABLE IF NOT EXISTS quality_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criteria_name TEXT UNIQUE,
    current_value REAL,
    min_value REAL,
    max_value REAL,
    adjustment_rate REAL DEFAULT 0.1,
    last_adjusted TIMESTAMP,
    adjustment_reason TEXT
);

-- Tag effectiveness tracking
CREATE TABLE IF NOT EXISTS tag_effectiveness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL,
    category TEXT NOT NULL,
    times_used INTEGER DEFAULT 0,
    times_successful INTEGER DEFAULT 0,
    effectiveness_score REAL DEFAULT 0.5,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tag_name, category)
);

-- Data provenance (track data history)
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- indexed, tagged, analyzed, trained, archived
    details TEXT,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tags_media ON tags(media_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category);
CREATE INDEX IF NOT EXISTS idx_feedback_media ON feedback(media_id);
CREATE INDEX IF NOT EXISTS idx_training_media ON training_usage(media_id);
CREATE INDEX IF NOT EXISTS idx_training_version ON training_usage(model_version);
"""


# ============================================
# SELF-LEARNING DATA MANAGER
# ============================================

class SelfLearningDataManager:
    """
    Manages data with self-learning capabilities.
    
    Features:
    - Comprehensive tagging system
    - User feedback integration
    - Training outcome tracking
    - Auto-adjusting quality criteria
    - Tag effectiveness learning
    - Full data provenance
    """
    
    def __init__(self, db_path: Path = None):
        """Initialize with database connection"""
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "loraforge.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_schema()
        self._init_default_criteria()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_schema(self):
        """Initialize learning schema"""
        conn = self._get_conn()
        conn.executescript(LEARNING_SCHEMA)
        conn.commit()
        conn.close()
    
    def _init_default_criteria(self):
        """Initialize default quality criteria"""
        defaults = [
            ("min_quality_score", 4.0, 1.0, 10.0, 0.1),
            ("min_attractiveness", 4.0, 1.0, 10.0, 0.1),
            ("blur_threshold", 100.0, 50.0, 500.0, 10.0),
            ("min_brightness", 30.0, 10.0, 100.0, 5.0),
            ("max_brightness", 225.0, 150.0, 250.0, 5.0),
            ("clip_score_threshold", 25.0, 15.0, 40.0, 1.0),
            ("consistency_threshold", 75.0, 50.0, 95.0, 2.0),
        ]
        
        conn = self._get_conn()
        for name, current, min_val, max_val, rate in defaults:
            conn.execute("""
                INSERT OR IGNORE INTO quality_criteria 
                (criteria_name, current_value, min_value, max_value, adjustment_rate)
                VALUES (?, ?, ?, ?, ?)
            """, (name, current, min_val, max_val, rate))
        conn.commit()
        conn.close()
    
    # ========================================
    # TAGGING OPERATIONS
    # ========================================
    
    def add_tag(
        self,
        media_id: int,
        tag_name: str,
        category: str,
        confidence: float = 1.0,
        source: str = "manual"
    ):
        """Add a tag to media"""
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO tags (media_id, name, category, confidence, source)
            VALUES (?, ?, ?, ?, ?)
        """, (media_id, tag_name.lower(), category, confidence, source))
        conn.commit()
        conn.close()
        
        self._record_provenance(media_id, "tagged", f"{category}:{tag_name}")
    
    def add_tags_batch(self, media_id: int, tags: List[Tag]):
        """Add multiple tags at once"""
        conn = self._get_conn()
        data = [(media_id, t.name.lower(), t.category, t.confidence, t.source) for t in tags]
        conn.executemany("""
            INSERT OR REPLACE INTO tags (media_id, name, category, confidence, source)
            VALUES (?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()
    
    def get_tags(self, media_id: int, category: str = None) -> List[Dict]:
        """Get tags for media"""
        conn = self._get_conn()
        if category:
            rows = conn.execute(
                "SELECT * FROM tags WHERE media_id = ? AND category = ?",
                (media_id, category)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tags WHERE media_id = ?",
                (media_id,)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def find_by_tags(
        self,
        tags: List[str],
        match_all: bool = True,
        limit: int = 100
    ) -> List[int]:
        """Find media IDs by tags"""
        conn = self._get_conn()
        
        if match_all:
            # Must have ALL tags
            query = """
                SELECT media_id FROM tags 
                WHERE name IN ({})
                GROUP BY media_id 
                HAVING COUNT(DISTINCT name) = ?
                LIMIT ?
            """.format(','.join('?' * len(tags)))
            params = tags + [len(tags), limit]
        else:
            # Must have ANY tag
            query = """
                SELECT DISTINCT media_id FROM tags 
                WHERE name IN ({})
                LIMIT ?
            """.format(','.join('?' * len(tags)))
            params = tags + [limit]
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [r[0] for r in rows]
    
    def auto_tag_from_analysis(self, media_id: int, analysis: Dict):
        """
        Auto-generate tags from analysis results.
        
        Args:
            media_id: Media ID
            analysis: Analysis dict (from vision AI, CLIP, etc.)
        """
        tags = []
        
        # Content tags from vision analysis
        if 'gender' in analysis:
            tags.append(Tag(analysis['gender'], TagCategory.CONTENT.value, 0.9, "auto"))
        
        if 'body_type' in analysis:
            tags.append(Tag(analysis['body_type'], TagCategory.CONTENT.value, 0.8, "auto"))
        
        # Quality tags
        if 'quality' in analysis:
            q = analysis['quality']
            if q >= 8:
                tags.append(Tag("high_quality", TagCategory.QUALITY.value, 0.9, "auto"))
            elif q >= 6:
                tags.append(Tag("good_quality", TagCategory.QUALITY.value, 0.8, "auto"))
            elif q >= 4:
                tags.append(Tag("acceptable_quality", TagCategory.QUALITY.value, 0.7, "auto"))
            else:
                tags.append(Tag("low_quality", TagCategory.QUALITY.value, 0.9, "auto"))
        
        if 'attractiveness' in analysis:
            a = analysis['attractiveness']
            if a >= 8:
                tags.append(Tag("highly_attractive", TagCategory.QUALITY.value, 0.9, "auto"))
            elif a >= 6:
                tags.append(Tag("attractive", TagCategory.QUALITY.value, 0.8, "auto"))
        
        # WD14 tags as content tags
        if 'wd14_tags' in analysis:
            for tag, conf in analysis['wd14_tags'].items():
                if conf >= 0.5:
                    tags.append(Tag(tag, TagCategory.CONTENT.value, conf, "auto_wd14"))
        
        # CLIP-based tags
        if 'clip_score' in analysis:
            cs = analysis['clip_score']
            if cs >= 30:
                tags.append(Tag("high_clip_score", TagCategory.QUALITY.value, 0.9, "auto"))
            elif cs >= 25:
                tags.append(Tag("good_clip_score", TagCategory.QUALITY.value, 0.8, "auto"))
        
        if tags:
            self.add_tags_batch(media_id, tags)
    
    # ========================================
    # FEEDBACK OPERATIONS
    # ========================================
    
    def add_feedback(
        self,
        media_id: int,
        feedback_type: str,
        rating: int = None,
        notes: str = None
    ):
        """Record user feedback"""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO feedback (media_id, feedback_type, rating, notes)
            VALUES (?, ?, ?, ?)
        """, (media_id, feedback_type, rating, notes))
        conn.commit()
        conn.close()
        
        # Add feedback tag
        self.add_tag(media_id, feedback_type, TagCategory.FEEDBACK.value, 1.0, "feedback")
        self._record_provenance(media_id, "feedback", f"{feedback_type}:{rating}")
        
        # Trigger learning from feedback
        self._learn_from_feedback(media_id, feedback_type, rating)
    
    def get_feedback(self, media_id: int) -> List[Dict]:
        """Get all feedback for media"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM feedback WHERE media_id = ? ORDER BY created_at DESC",
            (media_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def get_approved_media(self, limit: int = 100) -> List[int]:
        """Get media IDs that have been approved"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT DISTINCT media_id FROM feedback 
            WHERE feedback_type = 'approved'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [r[0] for r in rows]
    
    def get_rejected_media(self, limit: int = 100) -> List[int]:
        """Get media IDs that have been rejected"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT DISTINCT media_id FROM feedback 
            WHERE feedback_type = 'rejected'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [r[0] for r in rows]
    
    # ========================================
    # TRAINING TRACKING
    # ========================================
    
    def record_training_usage(
        self,
        media_id: int,
        model_version: str,
        split: str = "train",
        outcome: str = None,
        contribution_score: float = None
    ):
        """Record that media was used in training"""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO training_usage 
            (media_id, model_version, dataset_split, outcome, contribution_score)
            VALUES (?, ?, ?, ?, ?)
        """, (media_id, model_version, split, outcome, contribution_score))
        conn.commit()
        conn.close()
        
        # Add training tag
        self.add_tag(media_id, f"trained_{model_version}", TagCategory.TRAINING.value, 1.0, "training")
        self._record_provenance(media_id, "trained", f"{model_version}:{split}")
    
    def update_training_outcome(
        self,
        model_version: str,
        outcome: str,
        contribution_scores: Dict[int, float] = None
    ):
        """
        Update training outcomes after model evaluation.
        
        Args:
            model_version: Version that was trained
            outcome: Overall outcome (success/failure/partial)
            contribution_scores: Optional dict of media_id -> contribution score
        """
        conn = self._get_conn()
        
        # Update all usage records for this version
        conn.execute("""
            UPDATE training_usage SET outcome = ? WHERE model_version = ?
        """, (outcome, model_version))
        
        # Update individual contribution scores
        if contribution_scores:
            for media_id, score in contribution_scores.items():
                conn.execute("""
                    UPDATE training_usage 
                    SET contribution_score = ?
                    WHERE media_id = ? AND model_version = ?
                """, (score, media_id, model_version))
        
        conn.commit()
        conn.close()
        
        # Trigger learning from training results
        self._learn_from_training(model_version, outcome)
    
    def get_training_history(self, media_id: int) -> List[Dict]:
        """Get training history for media"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM training_usage 
            WHERE media_id = ? 
            ORDER BY used_at DESC
        """, (media_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def get_successful_training_data(self, limit: int = 100) -> List[int]:
        """Get media IDs that contributed to successful training"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT DISTINCT media_id FROM training_usage 
            WHERE outcome = 'success' AND contribution_score > 0.5
            ORDER BY contribution_score DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [r[0] for r in rows]
    
    # ========================================
    # SELF-LEARNING SYSTEM
    # ========================================
    
    def _learn_from_feedback(self, media_id: int, feedback_type: str, rating: int):
        """
        Learn from user feedback to improve future selections.
        
        This adjusts quality criteria based on what users approve/reject.
        """
        if feedback_type not in ['approved', 'rejected']:
            return
        
        # Get this media's analysis scores
        conn = self._get_conn()
        
        # Get tags and their effectiveness
        tags = conn.execute(
            "SELECT name, category FROM tags WHERE media_id = ?",
            (media_id,)
        ).fetchall()
        
        for tag in tags:
            # Update tag effectiveness
            if feedback_type == 'approved':
                conn.execute("""
                    UPDATE tag_effectiveness 
                    SET times_used = times_used + 1,
                        times_successful = times_successful + 1,
                        effectiveness_score = (times_successful + 1.0) / (times_used + 1.0),
                        last_updated = CURRENT_TIMESTAMP
                    WHERE tag_name = ? AND category = ?
                """, (tag['name'], tag['category']))
            else:
                conn.execute("""
                    UPDATE tag_effectiveness 
                    SET times_used = times_used + 1,
                        effectiveness_score = times_successful * 1.0 / (times_used + 1.0),
                        last_updated = CURRENT_TIMESTAMP
                    WHERE tag_name = ? AND category = ?
                """, (tag['name'], tag['category']))
            
            # Insert if not exists
            conn.execute("""
                INSERT OR IGNORE INTO tag_effectiveness (tag_name, category)
                VALUES (?, ?)
            """, (tag['name'], tag['category']))
        
        conn.commit()
        conn.close()
    
    def _learn_from_training(self, model_version: str, outcome: str):
        """
        Learn from training outcomes to improve future data selection.
        
        Adjusts quality criteria based on what produces good models.
        """
        conn = self._get_conn()
        
        # Get all media used in this version
        media_ids = conn.execute("""
            SELECT media_id FROM training_usage WHERE model_version = ?
        """, (model_version,)).fetchall()
        
        if not media_ids:
            conn.close()
            return
        
        # Record learning event
        conn.execute("""
            INSERT INTO learning_history 
            (learning_type, old_value, new_value, reason, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "training_outcome",
            None,
            outcome,
            f"Model {model_version} training {outcome}",
            0.8
        ))
        
        conn.commit()
        conn.close()
        
        # If successful, boost tags of used media
        if outcome == 'success':
            for row in media_ids:
                self._boost_successful_tags(row[0])
    
    def _boost_successful_tags(self, media_id: int):
        """Boost effectiveness of tags from successful media"""
        conn = self._get_conn()
        
        tags = conn.execute(
            "SELECT name, category FROM tags WHERE media_id = ?",
            (media_id,)
        ).fetchall()
        
        for tag in tags:
            conn.execute("""
                UPDATE tag_effectiveness 
                SET times_successful = times_successful + 1,
                    effectiveness_score = (times_successful + 1.0) / NULLIF(times_used, 0),
                    last_updated = CURRENT_TIMESTAMP
                WHERE tag_name = ? AND category = ?
            """, (tag['name'], tag['category']))
        
        conn.commit()
        conn.close()
    
    def adjust_quality_criteria(self, criteria_name: str, direction: str, reason: str):
        """
        Adjust a quality criterion based on learning.
        
        Args:
            criteria_name: Name of criterion to adjust
            direction: 'increase' or 'decrease'
            reason: Why we're adjusting
        """
        conn = self._get_conn()
        
        # Get current value
        row = conn.execute("""
            SELECT * FROM quality_criteria WHERE criteria_name = ?
        """, (criteria_name,)).fetchone()
        
        if not row:
            conn.close()
            return
        
        old_value = row['current_value']
        rate = row['adjustment_rate']
        min_val = row['min_value']
        max_val = row['max_value']
        
        # Calculate new value
        if direction == 'increase':
            new_value = min(max_val, old_value + rate)
        else:
            new_value = max(min_val, old_value - rate)
        
        # Update
        conn.execute("""
            UPDATE quality_criteria 
            SET current_value = ?, last_adjusted = CURRENT_TIMESTAMP, adjustment_reason = ?
            WHERE criteria_name = ?
        """, (new_value, reason, criteria_name))
        
        # Record learning
        conn.execute("""
            INSERT INTO learning_history 
            (learning_type, old_value, new_value, reason, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, ("criteria_adjustment", str(old_value), str(new_value), reason, 0.7))
        
        conn.commit()
        conn.close()
        
        print_info(f"Adjusted {criteria_name}: {old_value} → {new_value} ({reason})")
    
    def get_quality_criteria(self) -> Dict[str, float]:
        """Get current quality criteria values"""
        conn = self._get_conn()
        rows = conn.execute("SELECT criteria_name, current_value FROM quality_criteria").fetchall()
        conn.close()
        return {r['criteria_name']: r['current_value'] for r in rows}
    
    def get_effective_tags(self, min_effectiveness: float = 0.6, limit: int = 50) -> List[Dict]:
        """Get most effective tags"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM tag_effectiveness 
            WHERE effectiveness_score >= ? AND times_used >= 5
            ORDER BY effectiveness_score DESC
            LIMIT ?
        """, (min_effectiveness, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def get_ineffective_tags(self, max_effectiveness: float = 0.3, limit: int = 50) -> List[Dict]:
        """Get least effective tags (to avoid)"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM tag_effectiveness 
            WHERE effectiveness_score <= ? AND times_used >= 5
            ORDER BY effectiveness_score ASC
            LIMIT ?
        """, (max_effectiveness, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    # ========================================
    # PROVENANCE TRACKING
    # ========================================
    
    def _record_provenance(self, media_id: int, action: str, details: str = None):
        """Record data provenance"""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO provenance (media_id, action, details)
            VALUES (?, ?, ?)
        """, (media_id, action, details))
        conn.commit()
        conn.close()
    
    def get_provenance(self, media_id: int) -> List[Dict]:
        """Get full history of media"""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM provenance 
            WHERE media_id = ? 
            ORDER BY performed_at ASC
        """, (media_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    # ========================================
    # DATA ENHANCEMENT RECOMMENDATIONS
    # ========================================
    
    def get_recommendations(self) -> Dict:
        """
        Get recommendations for improving data quality.
        
        Returns suggestions based on learning history.
        """
        conn = self._get_conn()
        
        recommendations = {
            "tags_to_favor": [],
            "tags_to_avoid": [],
            "criteria_suggestions": [],
            "data_gaps": []
        }
        
        # Effective tags to favor
        effective = conn.execute("""
            SELECT tag_name, effectiveness_score 
            FROM tag_effectiveness 
            WHERE effectiveness_score > 0.7 AND times_used >= 10
            ORDER BY effectiveness_score DESC
            LIMIT 10
        """).fetchall()
        
        for row in effective:
            recommendations["tags_to_favor"].append({
                "tag": row['tag_name'],
                "score": row['effectiveness_score']
            })
        
        # Ineffective tags to avoid
        ineffective = conn.execute("""
            SELECT tag_name, effectiveness_score 
            FROM tag_effectiveness 
            WHERE effectiveness_score < 0.3 AND times_used >= 10
            ORDER BY effectiveness_score ASC
            LIMIT 10
        """).fetchall()
        
        for row in ineffective:
            recommendations["tags_to_avoid"].append({
                "tag": row['tag_name'],
                "score": row['effectiveness_score']
            })
        
        # Criteria that were recently adjusted
        adjusted = conn.execute("""
            SELECT * FROM quality_criteria 
            WHERE last_adjusted IS NOT NULL
            ORDER BY last_adjusted DESC
            LIMIT 5
        """).fetchall()
        
        for row in adjusted:
            recommendations["criteria_suggestions"].append({
                "criteria": row['criteria_name'],
                "current": row['current_value'],
                "reason": row['adjustment_reason']
            })
        
        conn.close()
        
        return recommendations
    
    def get_learning_summary(self) -> Dict:
        """Get summary of what we've learned"""
        conn = self._get_conn()
        
        summary = {
            "total_feedback": conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0],
            "total_training_uses": conn.execute("SELECT COUNT(*) FROM training_usage").fetchone()[0],
            "successful_trainings": conn.execute(
                "SELECT COUNT(DISTINCT model_version) FROM training_usage WHERE outcome = 'success'"
            ).fetchone()[0],
            "total_tags": conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0],
            "unique_tags": conn.execute("SELECT COUNT(DISTINCT name) FROM tags").fetchone()[0],
            "learning_events": conn.execute("SELECT COUNT(*) FROM learning_history").fetchone()[0],
            "criteria_adjustments": conn.execute(
                "SELECT COUNT(*) FROM learning_history WHERE learning_type = 'criteria_adjustment'"
            ).fetchone()[0],
        }
        
        conn.close()
        return summary


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

_learning_manager = None

def get_learning_manager(db_path: Path = None) -> SelfLearningDataManager:
    """Get singleton learning manager"""
    global _learning_manager
    if _learning_manager is None:
        _learning_manager = SelfLearningDataManager(db_path)
    return _learning_manager


def tag_media(media_id: int, tags: List[str], category: str = "custom"):
    """Quick function to tag media"""
    manager = get_learning_manager()
    for tag in tags:
        manager.add_tag(media_id, tag, category)


def approve_media(media_id: int, rating: int = None):
    """Quick function to approve media"""
    manager = get_learning_manager()
    manager.add_feedback(media_id, FeedbackType.APPROVED.value, rating)


def reject_media(media_id: int, reason: str = None):
    """Quick function to reject media"""
    manager = get_learning_manager()
    manager.add_feedback(media_id, FeedbackType.REJECTED.value, notes=reason)


if __name__ == "__main__":
    # Test the learning system
    print_section("Self-Learning Data System Test")
    
    manager = SelfLearningDataManager()
    
    # Test tagging
    manager.add_tag(1, "test_tag", TagCategory.CUSTOM.value)
    print_success("Added tag")
    
    # Test feedback
    manager.add_feedback(1, FeedbackType.APPROVED.value, rating=8)
    print_success("Added feedback")
    
    # Get recommendations
    recs = manager.get_recommendations()
    print_info(f"Recommendations: {recs}")
    
    # Get learning summary
    summary = manager.get_learning_summary()
    print_info(f"Learning summary: {summary}")
    
    # Get quality criteria
    criteria = manager.get_quality_criteria()
    print_info(f"Quality criteria: {criteria}")
