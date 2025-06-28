"""Metric data models."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from fs_agt_clean.core.monitoring.models import (
    MetricCategory,
    MetricDataPoint,
    MetricFilter,
    MetricType,
    MetricUpdate,
    ResourceType,
    SystemMetrics,
    WSConnection,
)
from fs_agt_clean.services.types import MetricType as ServiceMetricType

__all__ = [
    "MetricDataPoint",
    "MetricUpdate",
    "MetricFilter",
    "MetricType",
    "MetricCategory",
    "ResourceType",
    "SystemMetrics",
    "WSConnection",
]


class MetricDataPoint(BaseModel):
    """Individual metric data point."""

    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")
    type: MetricType = Field(default=MetricType.GAUGE, description="Metric type")
    labels: Optional[Dict[str, str]] = Field(
        default_factory=dict, description="Metric labels"
    )

    class Config:
        """Pydantic model configuration."""

        use_enum_values = True


class MetricUpdate:
    """Metric update model for monitoring metrics."""

    def __init__(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        category: MetricCategory,
        labels: Dict[str, str],
        source: str,
        timestamp: Optional[datetime] = None,
    ):
        """Initialize metric update.

        Args:
            name: Metric name
            value: Numeric value
            metric_type: Type of metric (gauge, counter, etc.)
            category: Category of metric
            labels: Additional labels/tags for the metric
            source: Source system or component
            timestamp: Optional timestamp (defaults to now)
        """
        self.name = name
        self.value = value
        self.metric_type = metric_type
        self.category = category
        self.labels = labels
        self.source = source
        self.timestamp = timestamp or datetime.now(timezone.utc)


class MetricDataPoint:
    """Single metric data point for time series metrics."""

    def __init__(
        self,
        name: str,
        value: float,
        type: MetricType,
        category: MetricCategory,
        labels: Dict[str, str],
        timestamp: Optional[datetime] = None,
    ):
        """Initialize metric data point.

        Args:
            name: Metric name
            value: Numeric value
            type: Type of metric
            category: Category of metric
            labels: Additional labels/tags
            timestamp: Optional timestamp (defaults to now)
        """
        self.name = name
        self.value = value
        self.type = type
        self.category = category
        self.labels = labels
        self.timestamp = timestamp or datetime.now(timezone.utc)
