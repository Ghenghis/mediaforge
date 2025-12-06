"""
LORAFORGE - INDEXER MODULE
Complete media indexing with self-learning capabilities

Components:
- MediaIndexer: Scan and index all media files
- DatabaseManager: SQLite storage for catalog
- SelfLearningDataManager: Tags, feedback, continuous improvement

Usage:
    from indexer import MediaIndexer, index_directory
    
    # Quick index
    result = index_directory("/path/to/media")
    
    # Full control
    indexer = MediaIndexer()
    result = indexer.index_directory("/path/to/media")
    stats = indexer.get_stats()
"""

from .database import (
    DatabaseManager,
    MediaRecord,
    AnalysisRecord,
    get_database
)

from .self_learning_data import (
    SelfLearningDataManager,
    Tag,
    TagCategory,
    FeedbackType,
    LearningRecord,
    get_learning_manager,
    tag_media,
    approve_media,
    reject_media
)

from .media_indexer import (
    MediaIndexer,
    IndexResult,
    index_directory,
    get_indexer,
    IMAGE_FORMATS,
    VIDEO_FORMATS
)

__all__ = [
    # Database
    "DatabaseManager",
    "MediaRecord",
    "AnalysisRecord",
    "get_database",
    
    # Self-Learning
    "SelfLearningDataManager",
    "Tag",
    "TagCategory",
    "FeedbackType",
    "LearningRecord",
    "get_learning_manager",
    "tag_media",
    "approve_media",
    "reject_media",
    
    # Indexer
    "MediaIndexer",
    "IndexResult",
    "index_directory",
    "get_indexer",
    "IMAGE_FORMATS",
    "VIDEO_FORMATS"
]
