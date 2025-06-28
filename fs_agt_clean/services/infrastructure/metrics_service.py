"""Metrics service for monitoring system metrics."""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from pydantic import BaseModel, ConfigDict

from fs_agt_clean.core.config.manager import ConfigManager

# from fs_agt_clean.core.monitoring.alerts.manager import AlertManager  # Temporarily disabled
from fs_agt_clean.core.monitoring.common_types import (
    MetricCategory,
    MetricDataPoint,
    MetricType,
    MetricUpdate,
)

# from fs_agt_clean.core.monitoring.log_manager import LogManager  # Temporarily disabled
# from fs_agt_clean.core.monitoring.metrics_models import MetricUpdate  # Temporarily disabled
# from fs_agt_clean.core.monitoring.types import (  # Temporarily disabled
#     MetricCategory,
#     MetricsServiceProtocol,
#     MetricType,
# )

logger = logging.getLogger(__name__)


class MetricsServiceProtocol:
    """Protocol for metrics service."""

    async def record_metric(self, name: str, value: Any, **kwargs) -> MetricUpdate:
        """Record a metric."""
        pass


async def initialize() -> None:
    """Initialize the metrics service."""
    logger.info("Initializing metrics service")
    # Additional initialization logic as needed


class MetricsService(MetricsServiceProtocol):
    """Service for recording and retrieving metrics."""

    def __init__(self):
        """Initialize the metrics service."""
        self.metrics: List[MetricDataPoint] = []
        self.batch_size = 100
        self.cleanup_task = None
        self.batch_task = None

    async def start(self) -> None:
        """Start the metrics service."""
        logger.info("Starting metrics service")
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.batch_task = asyncio.create_task(self._batch_loop())

    async def stop(self) -> None:
        """Stop the metrics service."""
        logger.info("Stopping metrics service")
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.batch_task:
            self.batch_task.cancel()

    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up old metrics."""
        while True:
            try:
                await cleanup()
            except Exception as e:
                logger.error("Error in metrics cleanup: %s", e)

            # Wait for next cleanup interval (1 hour)
            await asyncio.sleep(3600)

    async def _batch_loop(self) -> None:
        """Background task for batch processing metrics."""
        while True:
            try:
                # Process batched metrics
                pass
            except Exception as e:
                logger.error("Error in metrics batch processing: %s", e)

            # Wait for next batch interval (5 seconds)
            await asyncio.sleep(5)

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Value to increment by
            labels: Optional labels for the metric
        """
        if labels is None:
            labels = {}
        # Implementation details
        logger.debug("Incrementing counter %s by %s", name, value)

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric value.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels for the metric
        """
        if labels is None:
            labels = {}
        # Implementation details
        logger.debug("Setting gauge %s to %s", name, value)

    def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Observe a value for a histogram metric.

        Args:
            name: Metric name
            value: Value to observe
            labels: Optional labels for the metric
        """
        if labels is None:
            labels = {}
        # Implementation details
        logger.debug("Observing histogram %s with value %s", name, value)

    async def record_metric(
        self,
        name: str,
        value: Union[float, Dict[str, float]],
        metric_type: MetricType = MetricType.GAUGE,
        category: MetricCategory = MetricCategory.RESOURCE,
        labels: Optional[Dict[str, str]] = None,
        source: str = "system",
    ) -> MetricUpdate:
        """
        Record a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            category: Category of metric
            labels: Optional labels for the metric
            source: Source of the metric

        Returns:
            MetricUpdate object
        """
        if labels is None:
            labels = {}

        timestamp = datetime.now(timezone.utc)
        metric_id = f"{name}_{timestamp.isoformat()}_{source}"

        # Create metric update
        update = MetricUpdate(
            timestamp=timestamp,
            metric_type=(
                str(metric_type.value)
                if hasattr(metric_type, "value")
                else str(metric_type)
            ),
            value=value,
            labels=labels,
            source=source,
        )

        # Record metric data point
        if isinstance(value, (int, float)):
            data_point = MetricDataPoint(
                name=name,
                value=float(value),
                timestamp=timestamp,
                metric_type=metric_type,
                category=category,
                labels=labels,
                source=source,
            )
            self.metrics.append(data_point)

        # Log metric recording
        logger.debug("Recorded metric: %s=%s", name, value)

        return update

    async def get_metrics(
        self, metric_name: Optional[str] = None
    ) -> Dict[str, List[MetricDataPoint]]:
        """
        Get metrics, optionally filtered by name.

        Args:
            metric_name: Optional metric name to filter by

        Returns:
            Dictionary of metrics grouped by name
        """
        result: Dict[str, List[MetricDataPoint]] = defaultdict(list)

        for metric in self.metrics:
            if metric_name is None or metric.name == metric_name:
                result[metric.name].append(metric)

        return result

    def dict(self) -> Dict[str, Any]:
        """
        Convert the service to a dictionary.

        Returns:
            Dictionary representation of the metrics service
        """
        return {
            "metrics_count": len(self.metrics),
            "metrics": [m.dict() for m in self.metrics],
        }


def aggregate_metrics(
    metrics: List[MetricDataPoint],
    window: timedelta,
) -> Dict[str, Dict[str, float]]:
    """
    Aggregate metrics over a time window.

    Args:
        metrics: List of metrics to aggregate
        window: Time window for aggregation

    Returns:
        Aggregated metrics
    """
    now = datetime.now(timezone.utc)
    start_time = now - window

    # Group metrics by name and labels
    grouped: Dict[str, List[MetricDataPoint]] = defaultdict(list)

    for metric in metrics:
        if metric.timestamp >= start_time:
            key = f"{metric.name}_{str(sorted(metric.labels.items()))}"
            grouped[key].append(metric)

    # Aggregate each group
    result: Dict[str, Dict[str, float]] = {}

    for key, points in grouped.items():
        name = points[0].name if points else "unknown"
        labels = points[0].labels if points else {}

        values = [p.value for p in points]

        # Calculate aggregates
        aggregates = {
            "count": len(values),
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "avg": sum(values) / len(values) if values else 0,
            "sum": sum(values),
        }

        result_key = f"{name}_{str(sorted(labels.items()))}"
        result[result_key] = aggregates

    return result


def get_metric_history(
    metric_name: str, start_time: Optional[datetime] = None
) -> List[MetricDataPoint]:
    """
    Get historical metrics for a specific metric name.

    Args:
        metric_name: Name of the metric
        start_time: Optional start time for filtering

    Returns:
        List of metric data points
    """
    # Implementation placeholder - would normally query metrics storage
    return []


async def cleanup() -> None:
    """Clean up old metrics data."""
    logger.info("Cleaning up old metrics data")
    # Implementation placeholder - would clean up old metrics


async def start_cleanup_task() -> asyncio.Task:
    """Start the metrics cleanup background task."""
    return asyncio.create_task(_cleanup_loop())


async def _cleanup_loop() -> None:
    """Background task for cleaning up old metrics."""
    while True:
        try:
            await cleanup()
        except Exception as e:
            logger.error("Error in metrics cleanup: %s", e)

        # Wait for next cleanup interval (1 hour)
        await asyncio.sleep(3600)


# Export module members
__all__ = [
    "MetricsService",
    "aggregate_metrics",
    "cleanup",
    "start_cleanup_task",
    "MetricDataPoint",
    "MetricUpdate",
    "initialize",
]
