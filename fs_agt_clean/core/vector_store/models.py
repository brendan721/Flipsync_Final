"""Vector store models and data structures."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class VectorDistanceMetric(Enum):
    """Distance metrics for vector similarity."""

    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot"


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class MetricCategory(Enum):
    """Categories of metrics."""

    SYSTEM = "system"
    BUSINESS = "business"
    PERFORMANCE = "performance"


@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""

    store_id: str
    dimension: int
    distance_metric: VectorDistanceMetric = VectorDistanceMetric.COSINE
    host: str = "localhost"
    port: int = 6333
    timeout: int = 30
    max_retries: int = 3
    api_key: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Set default additional_config if not provided."""
        if self.additional_config is None:
            self.additional_config = {}


@dataclass
class MetricUpdate:
    """Metric update data."""

    name: str
    value: float
    metric_type: MetricType
    category: MetricCategory
    source: str
    labels: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None


@dataclass
class SearchQuery:
    """Search query for vector store."""

    vector: List[float]
    limit: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = None
    score_threshold: float = 0.0


@dataclass
class SearchResult:
    """Search result from vector store."""

    id: str
    score: float
    payload: Dict[str, Any]


@dataclass
class ProductMetadata:
    """Product metadata for vector store."""

    product_id: str
    title: str
    description: str
    price: float
    category: str
    source: Optional[str] = None
    timestamp: Optional[datetime] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    subcategory: Optional[str] = None
    sku: Optional[str] = None
    asin: Optional[str] = None
    upc: Optional[str] = None
    isbn: Optional[str] = None
    condition: Optional[str] = None
    quantity: Optional[int] = None
    color: Optional[str] = None
    material: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    sales_rank: Optional[int] = None
    keywords: Optional[str] = None
    search_terms: Optional[str] = None
    last_sale_at: Optional[datetime] = None

    def __post_init__(self):
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class CollectionInfo:
    """Information about a vector collection."""

    name: str
    vectors_count: int
    indexed_vectors_count: int
    points_count: int
    segments_count: int
    disk_data_size: int
    ram_data_size: int
    config: Dict[str, Any]
