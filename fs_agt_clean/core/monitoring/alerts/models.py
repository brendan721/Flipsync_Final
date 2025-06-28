"""Alert models for monitoring system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

from fs_agt_clean.core.monitoring.alert_types import (
    AlertSeverity,
    AlertStatus,
    AlertType,
    ComparisonOperator,
)
from fs_agt_clean.core.monitoring.metric_types import MetricType
from fs_agt_clean.core.monitoring.notifications import NotificationChannel


@dataclass
class AlertConfig:
    """Alert configuration."""

    name: str
    alert_type: AlertType
    severity: AlertSeverity
    metric_type: MetricType
    threshold: float
    comparison: ComparisonOperator = "gt"
    window_size: int = 300  # 5 minutes in seconds
    cooldown: int = 600  # 10 minutes in seconds
    enabled: bool = True
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class ErrorMetrics:
    """Error metrics data."""

    endpoint: str
    error_count: int
    error_rate: float
    error_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class LatencyMetrics:
    """Latency metrics data."""

    endpoint: str
    avg_latency: float
    p95_latency: float
    p99_latency: float
    max_latency: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


class Alert(BaseModel):
    """Alert data model."""

    id: str = Field(..., description="Unique alert identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: AlertSeverity
    alert_type: AlertType
    component: str
    source: str
    message: str
    metric_type: MetricType
    metric_value: float
    threshold: float
    status: AlertStatus = Field(default=AlertStatus.NEW)
    labels: Dict[str, str] = Field(default_factory=dict)
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_message: Optional[str] = None


class PerformancePredictor(BaseModel):
    """Performance prediction model."""

    metric_type: str
    current_value: float
    predicted_value: float
    confidence: float = Field(ge=0.0, le=1.0)
    trend: str
    forecast_window: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class AlertChannel(str, Enum):
    """Alert notification channels."""

    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"


class AlertModel(BaseModel):
    """Alert model."""

    id: str
    severity: AlertSeverity
    component: str
    message: str
    details: Optional[Dict] = None
    timestamp: datetime
    channels: List[AlertChannel]
    acknowledged: bool = False
    resolved: bool = False


class AlertConfiguration(BaseModel):
    """Alert configuration."""

    slack_webhook_url: Optional[str] = None
    pagerduty_api_key: Optional[str] = None
    email_config: Optional[Dict] = None
    alert_channels: List[AlertChannel] = [AlertChannel.SLACK]
    thresholds: Dict[str, Dict[str, float]] = {
        "latency": {"critical": 5.0, "error": 2.0, "warning": 1.0},
        "error_rate": {"critical": 0.1, "error": 0.05, "warning": 0.01},
        "resource_usage": {"critical": 90.0, "error": 80.0, "warning": 70.0},
    }


@dataclass
class NotificationTemplate:
    """Notification template details."""

    id: str
    title: str
    body: str
    severity: str
    channels: Set[NotificationChannel]

    def format(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Format template with data."""
        return {
            "title": self.title.format(**data),
            "body": self.body.format(**data),
        }


# Default alert thresholds by metric type
DEFAULT_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "latency": {"critical": 5.0, "error": 2.0, "warning": 1.0},
    "error_rate": {"critical": 0.1, "error": 0.05, "warning": 0.01},
    "resource_usage": {"critical": 90.0, "error": 80.0, "warning": 70.0},
}

__all__ = [
    "AlertStatus",
    "Alert",
    "ErrorMetrics",
    "LatencyMetrics",
    "AlertConfig",
    "ComparisonOperator",
    "PerformancePredictor",
    "AlertChannel",
    "AlertModel",
    "AlertConfiguration",
    "NotificationTemplate",
]
