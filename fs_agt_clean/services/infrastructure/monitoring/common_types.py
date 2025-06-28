"""Common types for monitoring system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from fs_agt_clean.core.monitoring.types import MetricCategory, MetricType


class MetricDataPoint(BaseModel):
    """Model for a metric data point."""

    name: str
    value: float
    timestamp: datetime
    metric_type: MetricType
    category: MetricCategory
    labels: Dict[str, str] = {}
    source: str = "system"

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metric_type": self.metric_type.value,
            "category": self.category.value,
            "labels": self.labels,
            "source": self.source,
        }
