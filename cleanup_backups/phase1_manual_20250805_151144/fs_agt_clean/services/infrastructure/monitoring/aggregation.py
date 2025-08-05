"""Metric aggregation service for monitoring system."""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class TimeWindow(str, Enum):
    """Time window for metrics aggregation."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class AggregationWindow:
    """Configuration for an aggregation window."""

    duration: timedelta
    granularity: timedelta
    retention: timedelta


class MetricAggregationService:
    """Service for aggregating and analyzing metric data."""

    def __init__(self):
        """Initialize the metric aggregation service."""
        self.metrics: Dict[str, Dict[datetime, float]] = defaultdict(dict)
        self._windows: Dict[str, AggregationWindow] = {
            "1m": AggregationWindow(
                duration=timedelta(minutes=1),
                granularity=timedelta(seconds=1),
                retention=timedelta(hours=24),
            ),
            "5m": AggregationWindow(
                duration=timedelta(minutes=5),
                granularity=timedelta(seconds=5),
                retention=timedelta(days=7),
            ),
            "1h": AggregationWindow(
                duration=timedelta(hours=1),
                granularity=timedelta(minutes=1),
                retention=timedelta(days=30),
            ),
        }

    async def add_metric(
        self, metric_name: str, value: float, timestamp: Optional[datetime] = None
    ) -> None:
        """Add a metric value for aggregation.

        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: Optional timestamp (defaults to now)
        """
        ts = timestamp or datetime.now(timezone.utc)
        self.metrics[metric_name][ts] = value
        await self._cleanup_old_metrics(metric_name)

    async def _cleanup_old_metrics(self, metric_name: str) -> None:
        """Remove metrics older than the maximum retention period.

        Args:
            metric_name: Name of the metric to clean up
        """
        now = datetime.now(timezone.utc)
        max_retention = max(w.retention for w in self._windows.values())
        cutoff = now - max_retention

        self.metrics[metric_name] = {
            ts: val for ts, val in self.metrics[metric_name].items() if ts > cutoff
        }

    async def get_aggregation(
        self,
        metric_name: str,
        window: str,
        aggregation_type: str = "mean",
        end_time: Optional[datetime] = None,
    ) -> Optional[float]:
        """Get aggregated metric value for a time window.

        Args:
            metric_name: Name of the metric
            window: Time window key (e.g., "1m", "5m", "1h")
            aggregation_type: Type of aggregation ("mean", "median", "min", "max", "sum")
            end_time: Optional end time (defaults to now)

        Returns:
            Aggregated value or None if no data available

        Raises:
            ValueError: If window or aggregation type is invalid
        """
        if window not in self._windows:
            raise ValueError(f"Invalid window: {window}")

        now = end_time or datetime.now(timezone.utc)
        window_config = self._windows[window]
        start_time = now - window_config.duration

        # Get values in window
        values = [
            val
            for ts, val in self.metrics[metric_name].items()
            if start_time <= ts <= now
        ]

        if not values:
            return None

        # Perform aggregation
        if aggregation_type == "mean":
            return float(np.mean(values))
        elif aggregation_type == "median":
            return float(np.median(values))
        elif aggregation_type == "min":
            return float(np.min(values))
        elif aggregation_type == "max":
            return float(np.max(values))
        elif aggregation_type == "sum":
            return float(np.sum(values))
        else:
            raise ValueError(f"Invalid aggregation type: {aggregation_type}")

    async def detect_anomalies(
        self, metric_name: str, window: str, threshold_sigmas: float = 3.0
    ) -> List[Tuple[datetime, float]]:
        """Detect anomalies in metric values using statistical methods.

        Args:
            metric_name: Name of the metric
            window: Time window key
            threshold_sigmas: Number of standard deviations for anomaly threshold

        Returns:
            List of (timestamp, value) tuples for anomalous points
        """
        if window not in self._windows:
            raise ValueError(f"Invalid window: {window}")

        now = datetime.now(timezone.utc)
        window_config = self._windows[window]
        start_time = now - window_config.duration

        # Get values in window
        points = [
            (ts, val)
            for ts, val in self.metrics[metric_name].items()
            if start_time <= ts <= now
        ]

        if len(points) < 2:  # Need at least 2 points for statistics
            return []

        values = [val for _, val in points]
        mean = np.mean(values)
        std = np.std(values)
        threshold = threshold_sigmas * std

        # Detect points outside threshold
        anomalies = [(ts, val) for ts, val in points if abs(val - mean) > threshold]

        return anomalies

    async def get_trend(self, metric_name: str, window: str) -> Optional[float]:
        """Calculate trend (slope) of metric values over time window.

        Args:
            metric_name: Name of the metric
            window: Time window key

        Returns:
            Trend value (positive for increasing, negative for decreasing)
            or None if insufficient data
        """
        if window not in self._windows:
            raise ValueError(f"Invalid window: {window}")

        now = datetime.now(timezone.utc)
        window_config = self._windows[window]
        start_time = now - window_config.duration

        # Get points in window
        points = sorted(
            [
                (ts.timestamp(), val)
                for ts, val in self.metrics[metric_name].items()
                if start_time <= ts <= now
            ]
        )

        if len(points) < 2:  # Need at least 2 points for trend
            return None

        # Calculate trend using numpy's polyfit
        x = np.array([t for t, _ in points])
        y = np.array([v for _, v in points])
        slope = np.polyfit(x, y, 1)[0]

        return float(slope)

    def get_supported_windows(self) -> List[str]:
        """Get list of supported aggregation windows.

        Returns:
            List of window keys
        """
        return list(self._windows.keys())

    def get_window_config(self, window: str) -> Optional[AggregationWindow]:
        """Get configuration for an aggregation window.

        Args:
            window: Window key

        Returns:
            Window configuration or None if window is invalid
        """
        return self._windows.get(window)
