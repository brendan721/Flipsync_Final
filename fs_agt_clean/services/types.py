"""
Common types and enums for FlipSync services.

This module provides shared type definitions used across different services.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class ServiceStatus(Enum):
    """Service status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class Priority(Enum):
    """Priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OperationType(Enum):
    """Operation types."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    ANALYZE = "analyze"


class DataSource(Enum):
    """Data source types."""

    EBAY = "ebay"
    AMAZON = "amazon"
    INTERNAL = "internal"
    EXTERNAL_API = "external_api"
    USER_INPUT = "user_input"


class ContentType(Enum):
    """Content types."""

    PRODUCT_DESCRIPTION = "product_description"
    LISTING_TITLE = "listing_title"
    MARKETING_COPY = "marketing_copy"
    CATEGORY_DESCRIPTION = "category_description"
    SEARCH_KEYWORDS = "search_keywords"


class AnalysisType(Enum):
    """Analysis types."""

    MARKET_ANALYSIS = "market_analysis"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    PRICE_ANALYSIS = "price_analysis"
    TREND_ANALYSIS = "trend_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"


class NotificationType(Enum):
    """Notification types."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    ALERT = "alert"


class WorkflowStatus(Enum):
    """Workflow status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class UnifiedAgentType(Enum):
    """UnifiedAgent types."""

    MARKET_AGENT = "market_agent"
    CONTENT_AGENT = "content_agent"
    INVENTORY_AGENT = "inventory_agent"
    PRICING_AGENT = "pricing_agent"
    LOGISTICS_AGENT = "logistics_agent"
    EXECUTIVE_AGENT = "executive_agent"


class EventType(Enum):
    """Event types."""

    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_PROGRESS = "workflow_progress"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    AGENT_COORDINATION = "agent_coordination"
    SYSTEM_ALERT = "system_alert"


class MetricType(Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class MetricCategory(Enum):
    """Metric categories."""

    PERFORMANCE = "performance"
    BUSINESS = "business"
    SYSTEM = "system"
    USER = "user"
    SECURITY = "security"
    QUALITY = "quality"
    AVAILABILITY = "availability"


class SearchResultType(Enum):
    """Search result types."""

    PRODUCT = "product"
    LISTING = "listing"
    COMPETITOR = "competitor"
    MARKET_DATA = "market_data"
    TREND = "trend"


class QualityScore(Enum):
    """Quality score levels."""

    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    UNKNOWN = "unknown"


class ResourceType(Enum):
    """Resource types."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    API = "api"
    AGENT = "agent"
    SERVICE = "service"


# Common data structures


class ServiceResponse(BaseModel):
    """Standard service response format."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: Optional[str] = None


class PaginationInfo(BaseModel):
    """Pagination information."""

    page: int = 1
    page_size: int = 20
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_previous: bool = False


class FilterCriteria(BaseModel):
    """Filter criteria for searches and queries."""

    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, contains
    value: Union[str, int, float, List[Any]]
    case_sensitive: bool = False


class SortCriteria(BaseModel):
    """Sort criteria for results."""

    field: str
    direction: str = "asc"  # asc, desc


class SearchRequest(BaseModel):
    """Standard search request format."""

    query: Optional[str] = None
    filters: List[FilterCriteria] = []
    sort: List[SortCriteria] = []
    pagination: PaginationInfo = PaginationInfo()
    include_metadata: bool = False


class HealthCheck(BaseModel):
    """Health check response."""

    service_name: str
    status: ServiceStatus
    version: str
    uptime_seconds: float
    dependencies: Dict[str, ServiceStatus] = {}
    metrics: Dict[str, Union[int, float]] = {}
    last_check: Optional[str] = None


class ConfigurationItem(BaseModel):
    """Configuration item."""

    key: str
    value: Any
    description: Optional[str] = None
    is_sensitive: bool = False
    last_updated: Optional[str] = None


class TaskResult(BaseModel):
    """Task execution result."""

    task_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float
    metadata: Dict[str, Any] = {}


class BatchOperation(BaseModel):
    """Batch operation request."""

    operation_type: OperationType
    items: List[Dict[str, Any]]
    options: Dict[str, Any] = {}
    priority: Priority = Priority.MEDIUM


class BatchResult(BaseModel):
    """Batch operation result."""

    total_items: int
    successful_items: int
    failed_items: int
    results: List[TaskResult]
    execution_time_ms: float
    errors: List[str] = []


# Type aliases for common patterns
ServiceConfig = Dict[str, Any]
ServiceMetrics = Dict[str, Union[int, float]]
ServiceTags = Dict[str, str]
ServiceData = Dict[str, Any]
