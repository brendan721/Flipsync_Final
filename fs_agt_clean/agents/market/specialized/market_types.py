"""Shared data types for market analysis."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, TypedDict, Union

import numpy as np

from fs_agt_clean.core.monitoring.metrics.service import MetricsCollector


class ProductData(TypedDict):
    """Product data type for market analysis."""

    price: float
    rating: Optional[float]
    reviews_count: Optional[int]
    sales_rank: Optional[float]
    category_id: str
    seller_id: str
    title: str
    description: Optional[str]
    metadata: Dict[str, Any]


class TimeSeriesMetrics(TypedDict):
    """Time series metrics data type."""

    average_price: float
    median_price: float
    total_listings: int
    active_listings: int
    sales_velocity: float
    market_health: float
    demand_score: float


class TimeSeriesDataPoint(TypedDict):
    """Time series data point type."""

    timestamp: datetime
    metrics: TimeSeriesMetrics


class TrendDirection(str, Enum):
    """Market trend direction."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class TrendMetric(str, Enum):
    """Market trend metric types."""

    DEMAND = "demand"
    COMPETITION = "competition"
    PRICE = "price"
    VELOCITY = "velocity"
    LISTINGS = "listings"


class PricePosition(str, Enum):
    """Competitor price position."""

    LOWER = "lower"
    HIGHER = "higher"
    SIMILAR = "similar"


class ThreatLevel(str, Enum):
    """Competitor threat level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class MarketData:
    """Market analysis results."""

    average_price: float
    median_price: float
    price_range: Tuple[float, float]
    total_listings: int
    active_listings: int
    sales_velocity: float
    top_keywords: List[str]
    competitors: List[Dict[str, Any]]
    trends: Dict[str, Any]
    timestamp: datetime


@dataclass
class CompetitorProfile:
    """Competitor analysis data."""

    competitor_id: str
    similarity_score: float
    price_position: PricePosition
    market_share: float
    strengths: List[str]
    weaknesses: List[str]
    threat_level: ThreatLevel
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "competitor_id": self.competitor_id,
            "similarity_score": self.similarity_score,
            "price_position": self.price_position.value,
            "market_share": self.market_share,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "threat_level": self.threat_level.value,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class TrendData:
    """Market trend data."""

    metric: TrendMetric
    direction: TrendDirection
    strength: float
    confidence: float
    start_time: datetime
    end_time: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric": self.metric.value,
            "direction": self.direction.value,
            "strength": self.strength,
            "confidence": self.confidence,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
        }


class TrendDetectorService:
    """Detects market trends using time series analysis."""

    def __init__(
        self,
        window_size: int = 30,
        confidence_threshold: float = 0.7,
        metric_collector: Optional[MetricsCollector] = None,
    ):
        self.window_size = window_size
        self.confidence_threshold = confidence_threshold
        self.metric_collector = metric_collector

    async def detect_trends(
        self, time_series: Sequence[TimeSeriesDataPoint]
    ) -> List[TrendData]:
        """Detect trends in a time series.

        Args:
            time_series: Sequence of time series data points containing metrics
                        and timestamps.

        Returns:
            List of detected trends with their metrics, direction, and confidence.
        """
        start_time = datetime.now(timezone.utc)
        try:
            if self.metric_collector:
                await self.metric_collector.record_latency("trend_detection_start", 0.0)
            if not time_series:
                return []

            # Initialize trends list
            trends: List[TrendData] = []

            # Get the time range
            end_time = time_series[-1]["timestamp"]

            # Analyze each metric
            metrics = time_series[-1]["metrics"]
            for metric_name in metrics:
                if metric_name not in TrendMetric.__members__:
                    continue

                metric = TrendMetric(metric_name)
                direction = self._determine_trend_direction(time_series, metric)
                strength = self._calculate_trend_strength(time_series, metric)
                confidence = self._calculate_confidence(strength, len(time_series))

                if confidence >= self.confidence_threshold:
                    trends.append(
                        TrendData(
                            metric=metric,
                            direction=direction,
                            strength=strength,
                            confidence=confidence,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )

            return trends

        except Exception as e:
            if self.metric_collector:
                await self.metric_collector.record_error(
                    "trend_detection_error", str(e)
                )
            return []

    def _determine_trend_direction(
        self, time_series: Sequence[TimeSeriesDataPoint], metric: TrendMetric
    ) -> TrendDirection:
        """Determine the direction of a trend for a specific metric."""
        # Implementation details...
        return TrendDirection.STABLE

    def _calculate_trend_strength(
        self, time_series: Sequence[TimeSeriesDataPoint], metric: TrendMetric
    ) -> float:
        """Calculate the strength of a trend for a specific metric."""
        # Implementation details...
        return 0.5

    def _calculate_confidence(self, strength: float, sample_size: int) -> float:
        """Calculate confidence level based on trend strength and sample size."""
        # Implementation details...
        return min(strength * (1 + np.log10(sample_size) / 10), 1.0)
