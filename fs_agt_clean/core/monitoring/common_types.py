"""Common types for monitoring system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MetricType(Enum):
    """Metric type enumeration."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricCategory(Enum):
    """Metric category enumeration."""

    RESOURCE = "resource"
    BUSINESS = "business"
    SYSTEM = "system"
    AGENT = "agent"


class MetricDataPoint(BaseModel):
    """Data point for a metric."""

    name: str
    value: float
    timestamp: datetime
    metric_type: MetricType
    category: MetricCategory
    labels: Optional[Dict[str, str]] = None
    source: str = "system"

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type.value,
            "category": self.category.value,
            "labels": self.labels or {},
            "source": self.source,
        }


class MetricUpdate(BaseModel):
    """Metric update model."""

    timestamp: datetime
    metric_type: str
    value: Any
    labels: Optional[Dict[str, str]] = None
    source: str = "system"

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type,
            "value": self.value,
            "labels": self.labels or {},
            "source": self.source,
        }
