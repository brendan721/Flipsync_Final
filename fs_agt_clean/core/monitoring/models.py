"""Fixed monitoring models module with Pydantic v1 compatibility."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union
from uuid import uuid4

from fastapi import WebSocket
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, field_validator

from fs_agt_clean.core.monitoring.metric_types import MetricCategory, MetricType


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResourceType(Enum):
    """Types of resources that can be monitored."""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CUSTOM = "custom"


class SystemMetrics(PydanticBaseModel):
    """System metrics data model."""

    # Core metrics
    cpu_usage: float = Field(default=0.0, description="CPU usage percentage")
    memory_usage: float = Field(default=0.0, description="Memory usage percentage")
    disk_usage: float = Field(default=0.0, description="Disk usage percentage")
    network_in: float = Field(default=0.0, description="Network inbound traffic")
    network_out: float = Field(default=0.0, description="Network outbound traffic")

    # Performance metrics
    total_requests: int = Field(default=0, description="Total number of requests")
    success_rate: float = Field(default=1.0, description="Request success rate")
    avg_latency: float = Field(default=0.0, description="Average request latency")
    peak_latency: float = Field(default=0.0, description="Peak request latency")
    total_errors: int = Field(default=0, description="Total number of errors")

    # Metadata
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of metrics",
    )
    name: Optional[str] = Field(default=None, description="Metric name")
    type: Optional[MetricType] = Field(default=None, description="Metric type")
    category: Optional[MetricCategory] = Field(
        default=None, description="Metric category"
    )

    value: Optional[float] = Field(default=None, description="Generic metric value")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")
    resource_usage: Dict[str, float] = Field(
        default_factory=dict, description="Resource usage metrics"
    )

    # Error tracking
    error: Optional[str] = Field(default=None, description="Error message if any")
    error_context: Dict[str, Any] = Field(
        default_factory=dict, description="Error context information"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @field_validator(
        "cpu_usage",
        "memory_usage",
        "disk_usage",
        "network_in",
        "network_out",
        mode="before",
    )
    def validate_float(cls, v: Any) -> float:
        """Validate and convert numeric values to float."""
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str) and v.replace(".", "", 1).isdigit():
            return float(v)
        return 0.0

    # Compatible method that works with both Pydantic v1 and v2
    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Convert to dictionary."""
        # For Pydantic v1 compatibility
        if hasattr(self, "dict"):
            d = self.dict(*args, **kwargs)
        else:
            d = super().model_dump(*args, **kwargs)

        d["timestamp"] = (
            self.timestamp.isoformat()
            if isinstance(self.timestamp, datetime)
            else self.timestamp
        )
        return d

    @classmethod
    def from_system_metrics(cls, metrics: Dict[str, Any]) -> "SystemMetrics":
        """Create from system metrics dictionary."""
        return cls(
            cpu_usage=metrics.get("cpu_percent", 0.0),
            memory_usage=metrics.get("memory_percent", 0.0),
            disk_usage=metrics.get("disk_usage", 0.0),
            network_in=metrics.get("network_in", 0.0),
            network_out=metrics.get("network_out", 0.0),
            timestamp=metrics.get("timestamp", datetime.now(timezone.utc)),
            labels=metrics.get("labels", {}),
            resource_usage=metrics.get("resource_usage", {}),
        )


class MetricDataPoint(PydanticBaseModel):
    """Individual metric data point."""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the metric",
    )
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    type: MetricType = Field(default=MetricType.GAUGE, description="Metric type")
    category: MetricCategory = Field(
        default=MetricCategory.RESOURCE, description="Metric category"
    )
    resource_type: Optional[ResourceType] = Field(
        default=ResourceType.CUSTOM, description="Resource type"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    labels: Dict[str, str] = Field(default_factory=dict)

    @field_validator("type", mode="before")
    def validate_type(cls, v: Any) -> MetricType:
        """Validate metric type."""
        if isinstance(v, str):
            return MetricType(v)
        return v

    @field_validator("category", mode="before")
    def validate_category(cls, v: Any) -> MetricCategory:
        """Validate metric category."""
        if isinstance(v, str):
            return MetricCategory(v)
        return v

    @field_validator("resource_type", mode="before")
    def validate_resource_type(cls, v: Any) -> Optional[ResourceType]:
        """Validate resource type."""
        if v is None:
            return None
        if isinstance(v, str):
            return ResourceType(v)
        return v

    # Compatible serialization for both Pydantic versions
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        if hasattr(self, "dict"):
            return self.dict()
        else:
            return self.model_dump()

    @classmethod
    def from_system_metrics(
        cls, metrics: Union[SystemMetrics, Dict[str, Any]]
    ) -> List["MetricDataPoint"]:
        """Create metric data points from system metrics."""
        points: List[MetricDataPoint] = []

        # Handle both SystemMetrics object and dictionary
        if isinstance(metrics, dict):
            metrics_dict = metrics
            timestamp = metrics.get("timestamp", datetime.now(timezone.utc))
            labels = metrics.get("labels", {})
        else:
            # Try model_dump first, fall back to dict for Pydantic v1
            if hasattr(metrics, "model_dump"):
                metrics_dict = metrics.model_dump()
            else:
                metrics_dict = metrics.dict()
            timestamp = metrics.timestamp
            labels = metrics.labels

        for field, value in metrics_dict.items():
            if field in {"timestamp", "labels", "error", "error_context"}:
                continue
            if isinstance(value, (int, float)):
                points.append(
                    cls(
                        name=field,
                        value=float(value),
                        timestamp=timestamp,
                        labels=labels,
                    )
                )
        return points


# Add a utility function for model serialization compatibility
def get_dict(obj):
    """Get dictionary representation, compatible with Pydantic v1 and v2."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    else:
        return obj.__dict__


class MetricFilter(PydanticBaseModel):
    """Filter for metrics queries."""

    endpoints: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    metric_type: Optional[MetricType] = None
    category: Optional[MetricCategory] = None
    resource_type: Optional[ResourceType] = None
    labels: Optional[Dict[str, str]] = None


class ClientConfig(PydanticBaseModel):
    """Configuration for a metrics client."""

    client_id: str
    update_interval: int = 5
    batch_size: int = 100
    enabled_metrics: List[str] = Field(default_factory=list)
    alert_preferences: Dict[str, bool] = Field(default_factory=dict)
    filters: Optional[List[MetricFilter]] = None


class WSConnection(PydanticBaseModel):
    """WebSocket connection configuration."""

    websocket: WebSocket
    client_id: str
    filters: Optional[List[MetricFilter]] = None
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class MetricUpdate:
    """Metric update data class."""

    def __init__(
        self,
        metric_type: MetricType,
        category: MetricCategory,
        value: Any,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
        name: Optional[str] = None,
    ):
        """Initialize a metric update."""
        self.metric_type = metric_type
        self.category = category
        self.value = value
        self.labels = labels or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.name = name

        # Generate a unique ID based on the metric properties
        self._id = f"{self.name}_{self.category.value}_{self.metric_type.value}_{hash(frozenset(self.labels.items()))}"

    def __hash__(self) -> int:
        """Hash the metric update."""
        return hash(
            (
                self.metric_type,
                self.category,
                self.name,
                frozenset(self.labels.items()),
            )
        )

    def __eq__(self, other: object) -> bool:
        """Compare metric updates."""
        if not isinstance(other, MetricUpdate):
            return False
        return (
            self.metric_type == other.metric_type
            and self.category == other.category
            and self.name == other.name
            and self.labels == other.labels
        )

    def model_dump(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric_type": self.metric_type.value,
            "category": self.category.value,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricUpdate":
        """Create from dictionary."""
        return cls(
            metric_type=MetricType(data["metric_type"]),
            category=MetricCategory(data["category"]),
            value=data["value"],
            labels=data.get("labels", {}),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if isinstance(data["timestamp"], str)
                else data["timestamp"]
            ),
            name=data.get("name"),
        )
