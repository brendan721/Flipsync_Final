"""
Metrics models for FlipSync monitoring system.

This module provides data models for metrics collection and reporting.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class MetricUpdate(BaseModel):
    """Model for metric updates."""
    
    metric_name: str
    value: Union[int, float]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricPoint(BaseModel):
    """Model for a single metric data point."""
    
    name: str
    value: Union[int, float]
    timestamp: datetime
    tags: Dict[str, str] = Field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None


class MetricSeries(BaseModel):
    """Model for a series of metric data points."""
    
    metric_name: str
    points: List[MetricPoint]
    start_time: datetime
    end_time: datetime
    aggregation_type: str = "raw"  # raw, avg, sum, count, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PerformanceMetric(BaseModel):
    """Model for performance metrics."""
    
    operation: str
    duration_ms: float
    success: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class BusinessMetric(BaseModel):
    """Model for business metrics."""
    
    metric_type: str  # sales, inventory, customer, etc.
    value: Union[int, float]
    period: str  # daily, weekly, monthly, etc.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dimensions: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SystemMetric(BaseModel):
    """Model for system metrics."""
    
    component: str
    metric_type: str  # cpu, memory, disk, network, etc.
    value: Union[int, float]
    unit: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    host: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)


class AlertMetric(BaseModel):
    """Model for alert metrics."""
    
    alert_name: str
    severity: str  # low, medium, high, critical
    message: str
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    source_metric: str
    threshold_value: Union[int, float]
    actual_value: Union[int, float]
    context: Dict[str, Any] = Field(default_factory=dict)


class MetricAggregation(BaseModel):
    """Model for aggregated metrics."""
    
    metric_name: str
    aggregation_type: str  # sum, avg, min, max, count
    value: Union[int, float]
    period_start: datetime
    period_end: datetime
    sample_count: int
    tags: Dict[str, str] = Field(default_factory=dict)


class MetricThreshold(BaseModel):
    """Model for metric thresholds."""
    
    metric_name: str
    threshold_type: str  # upper, lower, range
    warning_value: Optional[Union[int, float]] = None
    critical_value: Optional[Union[int, float]] = None
    enabled: bool = True
    tags: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MetricQuery(BaseModel):
    """Model for metric queries."""
    
    metric_names: List[str]
    start_time: datetime
    end_time: datetime
    aggregation: Optional[str] = None
    group_by: List[str] = Field(default_factory=list)
    filters: Dict[str, str] = Field(default_factory=dict)
    limit: Optional[int] = None


class MetricResponse(BaseModel):
    """Model for metric query responses."""
    
    query: MetricQuery
    series: List[MetricSeries]
    total_points: int
    execution_time_ms: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
