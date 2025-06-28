"""Core metrics models."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from fs_agt_clean.core.monitoring.metric_types import MetricType


class MetricDataPoint(BaseModel):
    """Single metric data point."""

    id: str = Field(description="Unique identifier for the metric")
    name: str = Field(description="Name of the metric")
    value: float = Field(description="Value of the metric")
    metric_type: MetricType = Field(description="Type of metric")
    timestamp: datetime = Field(description="Time the metric was recorded")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")


class MetricFilter(BaseModel):
    """Filter for querying metrics."""

    names: Optional[List[str]] = Field(
        default=None, description="Filter by metric names"
    )
    start_time: Optional[datetime] = Field(
        default=None, description="Filter by start time"
    )
    end_time: Optional[datetime] = Field(default=None, description="Filter by end time")
    labels: Optional[Dict[str, str]] = Field(
        default=None, description="Filter by labels"
    )


@dataclass
class Metric:
    """Metric data point."""

    name: str
    value: float
    labels: Dict[str, str]
    metadata: Dict[str, str]
    timestamp: str
