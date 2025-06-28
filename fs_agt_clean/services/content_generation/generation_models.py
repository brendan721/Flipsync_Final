"""Models for listing generation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Dict, List, Optional


class ContentType(Enum):
    """Types of listing content."""

    TITLE = auto()
    DESCRIPTION = auto()
    ITEM_SPECIFICS = auto()
    KEYWORDS = auto()


@dataclass
class ContentMetrics:
    """Metrics for content quality."""

    relevance_score: float
    keyword_density: float
    readability_score: float
    character_count: int
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class KeywordMetrics:
    """Metrics for keyword performance."""

    keyword: str
    relevance_score: float
    search_volume: int
    competition_level: float
    suggested_position: int


@dataclass
class ItemSpecific:
    """Item specific attribute."""

    name: str
    value: str
    is_required: bool = False
    suggested_values: List[str] = field(default_factory=list)


@dataclass
class ListingContent:
    """Content for a product listing."""

    title: str
    description: str
    item_specifics: List[ItemSpecific]
    keywords: List[KeywordMetrics]
    category_id: str
    metrics: Dict[ContentType, ContentMetrics]
    last_updated: datetime
    version: int


@dataclass
class OptimizationResult:
    """Result of content optimization."""

    original_content: ListingContent
    optimized_content: ListingContent
    improvement_metrics: Dict[ContentType, float]
    suggestions: List[str]
    optimization_timestamp: datetime = field(default_factory=datetime.utcnow)
