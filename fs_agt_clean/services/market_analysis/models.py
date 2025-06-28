"""Search service data models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class SearchFilter(BaseModel):
    """Search filter parameters."""

    field: str
    operator: str
    value: Union[str, int, float, bool, List[Any]]


class SearchSort(BaseModel):
    """Search sort parameters."""

    field: str
    order: str = "desc"


class SearchResult(BaseModel):
    """Search result model."""

    id: str
    score: float
    document: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


class SearchResponse(BaseModel):
    """Search response model."""

    results: List[SearchResult]
    total: int
    page: int
    page_size: int
    took_ms: float
    facets: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class TrendData(BaseModel):
    """Market trend data model."""

    trend_id: str
    trend_type: str  # 'demand', 'price', 'competition', etc.
    direction: str  # 'up', 'down', 'stable'
    magnitude: float  # Strength of the trend (0.0 to 1.0)
    confidence: float  # Confidence in the trend (0.0 to 1.0)
    timeframe: str  # Time period for the trend
    category_id: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MarketTrend(BaseModel):
    """Market trend analysis model."""

    category_id: str
    trend_data: List[TrendData]
    analysis_period: str
    confidence_score: float
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CompetitorData(BaseModel):
    """Competitor analysis data model."""

    competitor_id: str
    name: str
    similarity_score: float
    price_position: str  # 'lower', 'similar', 'higher'
    market_share: Optional[float] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    threat_level: str = "medium"  # 'low', 'medium', 'high'
    features: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SearchQuery(BaseModel):
    """Search query model."""

    query: str
    filters: List[SearchFilter] = Field(default_factory=list)
    sort: List[SearchSort] = Field(default_factory=list)
    page: int = 1
    page_size: int = 20
    include_facets: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
