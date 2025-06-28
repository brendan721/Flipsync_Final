"""
Models for listing generation and optimization.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ContentType(Enum):
    TITLE = "title"
    DESCRIPTION = "description"
    ITEM_SPECIFICS = "item_specifics"
    KEYWORDS = "keywords"


@dataclass
class KeywordMetrics:
    """Metrics for keyword performance."""

    keyword: str
    relevance_score: float
    search_volume: Optional[int]
    competition_level: float
    suggested_position: Optional[int]


@dataclass
class ContentMetrics:
    """Metrics for content performance."""

    content_type: ContentType
    character_count: int
    keyword_density: Dict[str, float]
    readability_score: float
    seo_score: float
    market_alignment: float


@dataclass
class ItemSpecific:
    """eBay item specific with validation."""

    name: str
    value: str
    is_required: bool
    valid_values: Optional[List[str]] = None
    recommendation_score: Optional[float] = None


@dataclass
class ListingContent:
    """Complete listing content with optimization metrics."""

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
    improvement_scores: Dict[ContentType, float]
    suggestions: List[str]
    timestamp: datetime


@dataclass
class ListingData:
    """Data for a complete listing."""

    listing_id: str
    content: ListingContent
    metrics: ContentMetrics
    optimization_result: Optional[OptimizationResult] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CompetitorProfile:
    """Profile of a competitor's listing."""

    seller_id: str
    price: float
    rating: float
    review_count: int
    fulfillment_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    threat_level: str = "medium"  # Can be "low", "medium", or "high"
    last_updated: datetime = field(default_factory=datetime.utcnow)
