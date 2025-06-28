"""Type definitions for monitoring components."""

from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Mapping, Optional, Protocol, Set, Union

from pydantic import BaseModel, ConfigDict, Field

from .alert_types import AlertSeverity

# Define MetricValue type
MetricValue = Union[float, int]
MetricDict = Dict[str, Union[MetricValue, List[MetricValue]]]


class ResourceType(str, Enum):
    """Type of resource being monitored."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    API = "api"
    CUSTOM = "custom"
    PROCESS = "process"
    CONTAINER = "container"
    NODE = "node"
    CLUSTER = "cluster"


class HealthStatus(Enum):
    """Health status indicators for system components."""

    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    WARNING = "warning"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"

    def __str__(self) -> str:
        """Return string representation of health status."""
        return self.value


class ResourceMetrics(BaseModel):
    """Resource metrics data."""

    resource_type: ResourceType
    value: float = Field(0.0, ge=0.0, le=100.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemMetrics(BaseModel):
    """System-wide metrics data."""

    cpu_usage: float = Field(0.0, ge=0.0, le=100.0)
    memory_usage: float = Field(0.0, ge=0.0, le=100.0)
    disk_usage: float = Field(0.0, ge=0.0, le=100.0)
    network_in: float = 0.0
    network_out: float = 0.0
    total_requests: int = 0
    success_rate: float = Field(0.0, ge=0.0, le=1.0)
    avg_latency: float = 0.0
    peak_latency: float = 0.0
    total_errors: int = 0
    resource_usage: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UnifiedAgentHealth(BaseModel):
    """Health status of an agent."""

    agent_id: str
    status: HealthStatus
    uptime: float
    error_count: int
    last_error: Optional[datetime] = None
    last_success: Optional[datetime] = None
    resource_metrics: Mapping[ResourceType, ResourceMetrics]
    system_metrics: SystemMetrics
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthAlert(BaseModel):
    """Health-related alert."""

    id: str
    severity: AlertSeverity
    message: str
    component: str
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None


class HealthSnapshot(BaseModel):
    """System health snapshot."""

    status: HealthStatus
    overall_status: HealthStatus
    agent_health: Dict[str, UnifiedAgentHealth]
    system_metrics: SystemMetrics
    active_alerts: List[HealthAlert] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MaintenanceWindow(BaseModel):
    """Scheduled maintenance window."""

    id: str
    start_time: datetime
    end_time: datetime
    components: Set[str]
    maintenance_type: str
    priority: str
    status: str = "scheduled"


class OptimizationRecommendation(BaseModel):
    """Resource optimization recommendation."""

    resource_type: ResourceType
    current_usage: float
    recommended_limit: float
    potential_savings: float
    priority: str
    justification: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RecoveryAction(BaseModel):
    """Recovery action for unhealthy components."""

    component: str
    action: str
    priority: str
    estimated_duration: int
    impact: str
    prerequisites: List[str] = []


class MetricValue(float):
    """Extended float type for metrics with metadata."""

    def __new__(
        cls,
        value: Union[int, float],
        timestamp: Optional[datetime] = None,
        unit: Optional[str] = None,
    ) -> "MetricValue":
        """Create new metric value.

        Args:
            value: Numeric value
            timestamp: Optional timestamp
            unit: Optional unit of measurement

        Returns:
            New MetricValue instance
        """
        instance = float.__new__(cls, value)
        instance._timestamp = timestamp or datetime.now(timezone.utc)
        instance._unit = unit or ""
        return instance

    def __init__(self, *args, **kwargs) -> None:
        """Initialize metric value."""
        pass

    @property
    def timestamp(self) -> datetime:
        """Get timestamp."""
        return self._timestamp

    @property
    def unit(self) -> str:
        """Get unit."""
        return self._unit


class MetricCategory(str, Enum):
    """Categories for metrics."""

    RESOURCE = "resource"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SYSTEM = "system"
    SECURITY = "security"


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class NotificationCategory(str, Enum):
    """Categories for notifications."""

    SYSTEM_ALERT = "SYSTEM_ALERT"
    SYSTEM_INFO = "SYSTEM_INFO"
    USER_ALERT = "USER_ALERT"
    USER_INFO = "USER_INFO"


class MetricsServiceProtocol(Protocol):
    """Protocol defining the metrics service interface."""

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Value to increment by
            labels: Optional labels for the metric
        """
        ...

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric value.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels for the metric
        """
        ...

    def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Observe a value for a histogram metric.

        Args:
            name: Metric name
            value: Value to observe
            labels: Optional labels for the metric
        """
        ...

    async def record_metric(
        self,
        name: str,
        value: Union[float, Dict[str, float]],
        metric_type: MetricType = MetricType.GAUGE,
        category: MetricCategory = MetricCategory.RESOURCE,
        labels: Optional[Dict[str, str]] = None,
        source: str = "system",
    ) -> Any:
        """
        Record a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            category: Category of metric
            labels: Optional labels for the metric
            source: Source of the metric

        Returns:
            Metric update record
        """
        ...


# Export module members
__all__ = [
    "MetricCategory",
    "MetricType",
    "ResourceType",
    "HealthStatus",
    "SystemMetrics",
    "ResourceMetrics",
    "UnifiedAgentHealth",
    "HealthAlert",
    "HealthSnapshot",
    "MaintenanceWindow",
    "OptimizationRecommendation",
    "RecoveryAction",
    "MetricValue",
    "MetricDict",
    "NotificationCategory",
    "MetricsServiceProtocol",
]
