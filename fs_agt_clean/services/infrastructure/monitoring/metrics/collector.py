"""Metrics collector implementation."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fs_agt_clean.core.monitoring.metrics.models import MetricDataPoint, MetricUpdate
from fs_agt_clean.core.monitoring.types import MetricCategory, MetricType, ResourceType

# Global metrics registry
_metrics_registry = {}


# Standalone metric functions for backward compatibility
async def register_metric(
    name: str,
    initial_value: float = 0.0,
    metric_type: MetricType = MetricType.GAUGE,
    category: MetricCategory = MetricCategory.SYSTEM,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """Register a new metric.

    Args:
        name: Metric name
        initial_value: Initial metric value
        metric_type: Type of metric
        category: Category of metric
        labels: Optional metric labels
    """
    _metrics_registry[name] = {
        "value": initial_value,
        "type": metric_type,
        "category": category,
        "labels": labels or {},
        "timestamp": datetime.now(timezone.utc),
    }


async def increment_metric(
    name: str, amount: float = 1.0, labels: Optional[Dict[str, str]] = None
) -> None:
    """Increment a counter metric.

    Args:
        name: Metric name
        amount: Amount to increment
        labels: Optional updated labels
    """
    if name not in _metrics_registry:
        await register_metric(
            name, 0.0, MetricType.COUNTER, MetricCategory.SYSTEM, labels
        )

    _metrics_registry[name]["value"] += amount
    _metrics_registry[name]["timestamp"] = datetime.now(timezone.utc)
    if labels:
        _metrics_registry[name]["labels"].update(labels)


async def set_metric(
    name: str, value: float, labels: Optional[Dict[str, str]] = None
) -> None:
    """Set a gauge metric value.

    Args:
        name: Metric name
        value: Metric value
        labels: Optional updated labels
    """
    if name not in _metrics_registry:
        await register_metric(
            name, value, MetricType.GAUGE, MetricCategory.SYSTEM, labels
        )
    else:
        _metrics_registry[name]["value"] = value
        _metrics_registry[name]["timestamp"] = datetime.now(timezone.utc)
        if labels:
            _metrics_registry[name]["labels"].update(labels)


class MetricsCollector:
    """Collects and manages system metrics."""

    def __init__(self, service_name: Optional[str] = None):
        """Initialize metrics collector.

        Args:
            service_name: Optional name of the service being monitored
        """
        self.service_name = service_name or "default"
        self.metrics: Dict[str, List[MetricDataPoint]] = {}
        self._latency_metrics: Dict[str, List[float]] = {}
        self._error_counts: Dict[str, int] = {}
        self._success_counts: Dict[str, int] = {}
        self._total_operations = 0
        self._lock = asyncio.Lock()

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        category: MetricCategory = MetricCategory.SYSTEM,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            category: Category of metric
            labels: Optional metric labels
        """
        async with self._lock:
            metric = MetricDataPoint(
                name=name,
                value=value,
                type=metric_type,
                category=category,
                labels=labels or {},
                timestamp=datetime.now(timezone.utc),
            )
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(metric)

    async def collect_metrics(self) -> List[MetricDataPoint]:
        """Collect all current metrics.

        Returns:
            List of current metrics
        """
        async with self._lock:
            return [metric[-1] for metric in self.metrics.values() if metric]

    async def record_error(
        self, source: str, error_message: str, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record an error occurrence.

        Args:
            source: Error source
            error_message: Error message
            labels: Optional error labels
        """
        async with self._lock:
            self._error_counts[source] = self._error_counts.get(source, 0) + 1
            self._total_operations += 1
            await self.record_metric(
                name=f"{source}_error",
                value=1.0,
                metric_type=MetricType.COUNTER,
                category=MetricCategory.SECURITY,
                labels={"error": error_message, **(labels or {})},
            )

    async def record_success(
        self, operation: str, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a successful operation.

        Args:
            operation: Operation name
            labels: Optional operation labels
        """
        async with self._lock:
            self._success_counts[operation] = self._success_counts.get(operation, 0) + 1
            self._total_operations += 1
            await self.record_metric(
                name=f"{operation}_success",
                value=1.0,
                metric_type=MetricType.COUNTER,
                category=MetricCategory.SYSTEM,
                labels=labels,
            )

    async def record_latency(
        self, operation: str, latency: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record operation latency.

        Args:
            operation: Operation name
            latency: Operation latency in seconds
            labels: Optional operation labels
        """
        async with self._lock:
            if operation not in self._latency_metrics:
                self._latency_metrics[operation] = []
            self._latency_metrics[operation].append(latency)
            await self.record_metric(
                name=f"{operation}_latency",
                value=latency,
                metric_type=MetricType.GAUGE,
                category=MetricCategory.PERFORMANCE,
                labels=labels,
            )

    async def get_metrics(
        self,
        names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> List[MetricDataPoint]:
        """Get metrics with optional filtering.

        Args:
            names: Optional list of metric names to filter
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            labels: Optional labels to filter by

        Returns:
            List of matching metrics
        """
        async with self._lock:
            metrics = []
            for name, points in self.metrics.items():
                if names and name not in names:
                    continue
                for point in points:
                    if start_time and point.timestamp < start_time:
                        continue
                    if end_time and point.timestamp > end_time:
                        continue
                    if labels and not all(
                        point.labels.get(k) == v for k, v in labels.items()
                    ):
                        continue
                    metrics.append(point)
            return metrics

    async def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        async with self._lock:
            self.metrics.clear()
            self._latency_metrics.clear()
            self._error_counts.clear()
            self._success_counts.clear()
            self._total_operations = 0

    async def get_error_count(self, source: str) -> int:
        """Get error count for a source.

        Args:
            source: Error source

        Returns:
            Number of errors for the source
        """
        return self._error_counts.get(source, 0)

    async def get_success_rate(self) -> float:
        """Get overall success rate.

        Returns:
            Success rate as a float between 0 and 1
        """
        if self._total_operations == 0:
            return 1.0
        total_successes = sum(self._success_counts.values())
        return total_successes / self._total_operations

    async def get_average_latency(self, operation: str) -> float:
        """Get average latency for an operation.

        Args:
            operation: Operation name

        Returns:
            Average latency in seconds
        """
        if (
            operation not in self._latency_metrics
            or not self._latency_metrics[operation]
        ):
            return 0.0
        return sum(self._latency_metrics[operation]) / len(
            self._latency_metrics[operation]
        )
