"""Metrics collection and management module."""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple

# Export key classes for easier imports
from fs_agt_clean.core.monitoring.metrics.collector import MetricsCollector
from fs_agt_clean.core.monitoring.metrics.models import MetricDataPoint, MetricUpdate

# Standard metric names
REQUEST_COUNT = "request_count"
REQUEST_LATENCY = "request_latency"
API_ERROR_COUNT = "api_error_count"
ERROR_COUNT = "error_count"

logger = logging.getLogger(__name__)


class TimeRange(NamedTuple):
    """Time range for querying metrics."""

    start: datetime
    end: datetime


class MetricsHistory:
    """Container for historical metrics data."""

    def __init__(self):
        self.data: Dict[str, List[Dict[str, Any]]] = {}

    def add_metric(self, metric_type: str, data: Dict[str, Any]):
        """Add a metric data point to history."""
        if metric_type not in self.data:
            self.data[metric_type] = []
        self.data[metric_type].append(data)

    def get_metrics(
        self, metric_type: str, time_range: Optional[TimeRange] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics of a specific type within a time range."""
        if metric_type not in self.data:
            return []

        if not time_range:
            return self.data[metric_type]

        return [
            m
            for m in self.data[metric_type]
            if "timestamp" in m
            and time_range.start
            <= datetime.fromisoformat(m["timestamp"])
            <= time_range.end
        ]


class MetricsStorage:
    """Storage for metrics data with query capabilities."""

    def __init__(self):
        self.history = MetricsHistory()
        self.retention_period = timedelta(days=30)  # Default retention period
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the metrics storage service."""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("Metrics storage started")

    async def stop(self):
        """Stop the metrics storage service."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics storage stopped")

    async def _periodic_cleanup(self):
        """Periodically clean up old metrics data."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run cleanup every hour
                await self.cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during metrics cleanup: {e}")

    async def cleanup_old_data(self):
        """Remove metrics data older than the retention period."""
        cutoff_time = datetime.now(timezone.utc) - self.retention_period
        for metric_type in list(self.history.data.keys()):
            self.history.data[metric_type] = [
                m
                for m in self.history.data[metric_type]
                if "timestamp" in m
                and datetime.fromisoformat(m["timestamp"]) > cutoff_time
            ]
        logger.info("Cleaned up old metrics data")

    async def store_metrics(self, metric_type: str, data: Dict[str, Any]):
        """Store metrics data."""
        if "timestamp" not in data:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.history.add_metric(metric_type, data)

    async def get_metrics(
        self,
        metric_type: str,
        time_range: TimeRange,
        window: Any = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Get metrics with filtering capabilities."""
        metrics = self.history.get_metrics(metric_type, time_range)

        # Apply filters if provided
        if filters:
            filtered_metrics = []
            for metric in metrics:
                match = True
                for key, value in filters.items():
                    if key not in metric or metric[key] != value:
                        match = False
                        break
                if match:
                    filtered_metrics.append(metric)
            return filtered_metrics

        return metrics


class HistoryStorage:
    """Storage for historical metrics data."""

    def __init__(self):
        self.history = MetricsHistory()
        self.retention_period = timedelta(days=7)  # Default retention period
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the history storage service."""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("History storage started")

    async def stop(self):
        """Stop the history storage service."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("History storage stopped")

    async def _periodic_cleanup(self):
        """Periodically clean up old metrics data."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run cleanup every hour
                await self.cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during metrics history cleanup: {e}")

    async def cleanup_old_data(self):
        """Remove metrics data older than the retention period."""
        cutoff_time = datetime.now(timezone.utc) - self.retention_period
        for metric_type in list(self.history.data.keys()):
            self.history.data[metric_type] = [
                m
                for m in self.history.data[metric_type]
                if "timestamp" in m
                and datetime.fromisoformat(m["timestamp"]) > cutoff_time
            ]
        logger.info("Cleaned up old metrics history data")

    async def store_metric(self, metric_type: str, data: Dict[str, Any]):
        """Store a metric data point."""
        if "timestamp" not in data:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.history.add_metric(metric_type, data)

    async def get_metrics(
        self, metric_type: str, time_range: Optional[TimeRange] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics of a specific type within a time range."""
        return self.history.get_metrics(metric_type, time_range)


__all__ = [
    "MetricUpdate",
    "MetricDataPoint",
    "MetricsCollector",
    "HistoryStorage",
    "MetricsHistory",
    "TimeRange",
    "MetricsStorage",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "API_ERROR_COUNT",
    "ERROR_COUNT",
]
