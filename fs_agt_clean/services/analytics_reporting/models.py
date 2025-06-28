from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

"\nModels for campaign performance analytics.\n"


class MetricType(Enum):
    ROI = "roi"
    ROAS = "roas"
    CPC = "cpc"
    CTR = "ctr"
    CONVERSION_RATE = "conversion_rate"
    REVENUE = "revenue"
    COST = "cost"
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PredictionInterval(Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class MetricValue:
    """Metric value with metadata."""

    value: float
    timestamp: datetime
    confidence_score: float
    source_platform: str
    is_predicted: bool


@dataclass
class PerformanceMetric:
    """Performance metric with historical values."""

    metric_type: MetricType
    current_value: MetricValue
    historical_values: List[MetricValue]
    trend: float
    baseline: float
    alert_threshold: float
    prediction_model: str


@dataclass
class AlertConfig:
    """Alert configuration."""

    metric_type: MetricType
    threshold: float
    severity: AlertSeverity
    enabled: bool
    cooldown_period: int
    last_triggered: Optional[datetime]


@dataclass
class Alert:
    """Performance alert."""

    id: str
    metric_type: MetricType
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: datetime
    campaign_id: str
    seller_id: str


@dataclass
class PerformancePrediction:
    """Performance prediction."""

    metric_type: MetricType
    predicted_value: float
    confidence_interval: tuple[float, float]
    prediction_interval: PredictionInterval
    features_used: List[str]
    model_version: str
    timestamp: datetime


@dataclass
class CampaignPerformance:
    """Campaign performance data."""

    campaign_id: str
    seller_id: str
    metrics: Dict[MetricType, PerformanceMetric]
    alerts: List[Alert]
    predictions: Dict[MetricType, PerformancePrediction]
    last_updated: datetime
    data_quality_score: float


@dataclass
class PerformanceComparison:
    """Cross-seller performance comparison."""

    metric_type: MetricType
    seller_metrics: Dict[str, PerformanceMetric]
    industry_average: float
    percentile_rank: float
    timestamp: datetime


@dataclass
class AnalyticsDashboard:
    """Performance analytics dashboard."""

    seller_id: str
    campaign_performances: Dict[str, CampaignPerformance]
    comparisons: Dict[MetricType, PerformanceComparison]
    overall_health_score: float
    recommendations: List[str]
    last_updated: datetime
