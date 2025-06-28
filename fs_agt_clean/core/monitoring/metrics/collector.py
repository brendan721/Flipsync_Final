"""
Metrics collector implementation for FlipSync.

This module provides a comprehensive metrics collection system that supports:
- Different metric types (gauge, counter, histogram)
- Labels/tags for metrics
- Efficient storage and retrieval
- Mobile-specific optimizations
- Integration with monitoring systems

It serves as the foundation for specialized metrics collection like
conversational metrics and decision intelligence metrics.
"""

import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.monitoring.logger import get_logger

# Default values
DEFAULT_COLLECTION_INTERVAL = 60  # seconds
DEFAULT_RETENTION_PERIOD = 86400  # 24 hours in seconds
DEFAULT_BATCH_SIZE = 100  # metrics per batch
DEFAULT_STORAGE_PATH = "data/metrics"


class MetricType(Enum):
    """Types of metrics with descriptions."""

    GAUGE = "gauge"  # A value that can go up and down
    COUNTER = "counter"  # A value that only increases
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Statistical summary of values


class MetricCategory(Enum):
    """Categories of metrics with descriptions."""

    SYSTEM = "system"  # System-level metrics (CPU, memory, etc.)
    PERFORMANCE = "performance"  # Performance metrics (latency, throughput, etc.)
    BUSINESS = "business"  # Business metrics (revenue, users, etc.)
    SECURITY = "security"  # Security metrics (login attempts, etc.)
    AGENT = "agent"  # UnifiedAgent-specific metrics
    CONVERSATION = "conversation"  # Conversation metrics
    DECISION = "decision"  # Decision intelligence metrics
    MOBILE = "mobile"  # Mobile-specific metrics
    API = "api"  # API-related metrics


class MetricDataPoint:
    """A single metric data point."""

    def __init__(
        self,
        name: str,
        value: float,
        type: MetricType = MetricType.GAUGE,
        category: MetricCategory = MetricCategory.SYSTEM,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize a metric data point.

        Args:
            name: Metric name
            value: Metric value
            type: Metric type
            category: Metric category
            labels: Optional labels/tags
            timestamp: Optional timestamp (defaults to now)
        """
        self.name = name
        self.value = value
        self.type = type
        self.category = category
        self.labels = labels or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "value": self.value,
            "type": self.type.value,
            "category": self.category.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricDataPoint":
        """
        Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            MetricDataPoint instance
        """
        return cls(
            name=data["name"],
            value=data["value"],
            type=MetricType(data["type"]),
            category=MetricCategory(data["category"]),
            labels=data["labels"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class MetricsCollector:
    """
    Collects and manages system metrics with mobile and vision awareness.

    This class provides a centralized metrics collection system that supports:
    - Different metric types (gauge, counter, histogram)
    - Labels/tags for metrics
    - Efficient storage and retrieval
    - Mobile-specific optimizations
    - Batching and compression for efficient transfer

    It serves as the foundation for specialized metrics collection.
    """

    _instance = None
    _lock = threading.RLock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsCollector, cls).__new__(cls)
            return cls._instance

    def __init__(
        self,
        service_name: str = "default",
        collection_interval: int = DEFAULT_COLLECTION_INTERVAL,
        retention_period: int = DEFAULT_RETENTION_PERIOD,
        storage_path: Optional[Union[str, Path]] = None,
        mobile_optimized: bool = False,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        """
        Initialize metrics collector.

        Args:
            service_name: Name of the service being monitored
            collection_interval: Interval between collections in seconds
            retention_period: How long to keep metrics in seconds
            storage_path: Path to store metrics
            mobile_optimized: Whether to optimize for mobile environments
            batch_size: Number of metrics to batch for storage/transfer
        """
        with self._lock:
            if self._initialized:
                return

            self.logger = get_logger(__name__)
            self.service_name = service_name
            self.collection_interval = collection_interval
            self.retention_period = retention_period
            self.mobile_optimized = mobile_optimized
            self.batch_size = batch_size

            # Set up storage path
            self.storage_path = (
                Path(storage_path) if storage_path else Path(DEFAULT_STORAGE_PATH)
            )
            os.makedirs(self.storage_path, exist_ok=True)

            # Initialize metric storage
            self.metrics: Dict[str, List[MetricDataPoint]] = {}
            self._counters: Dict[str, float] = {}  # Current counter values
            self._histograms: Dict[str, List[float]] = {}  # Values for histograms
            self._latency_metrics: Dict[str, List[float]] = {}  # Operation latencies
            self._error_counts: Dict[str, int] = {}  # Error counts by source
            self._success_counts: Dict[str, int] = {}  # Success counts by operation
            self._total_operations = 0  # Total operation count
            self._last_collection_time = None  # Last collection time
            self._collection_task = None  # Background collection task
            self._is_running = False  # Whether collection is running

            # Initialize async lock (lazy initialization)
            self._async_lock = None

            self._initialized = True

    def _ensure_async_lock(self) -> bool:
        """Ensure async lock is initialized.

        Returns:
            True if lock is available, False if no event loop
        """
        if self._async_lock is None:
            try:
                self._async_lock = asyncio.Lock()
                return True
            except RuntimeError:
                # No event loop running, skip metrics
                return False
        return True

    async def start(self) -> None:
        """Start metrics collection."""
        if self._is_running:
            return

        self._is_running = True
        self._last_collection_time = datetime.now(timezone.utc)

        # Start collection task if not already running
        if self._collection_task is None or self._collection_task.done():
            self._collection_task = asyncio.create_task(self._collection_loop())

        self.logger.info("Metrics collection started")

    async def stop(self) -> None:
        """Stop metrics collection."""
        if not self._is_running:
            return

        self._is_running = False

        # Cancel collection task if running
        if self._collection_task and not self._collection_task.done():
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Metrics collection stopped")

    async def _collection_loop(self) -> None:
        """Background task for metrics collection."""
        while self._is_running:
            try:
                # Collect metrics
                await self._collect_metrics()

                # Clean up old metrics
                await self._cleanup_old_metrics()

                # Store metrics
                if not self.mobile_optimized or (
                    self.mobile_optimized and len(self.metrics) >= self.batch_size
                ):
                    await self._store_metrics()
            except Exception as e:
                self.logger.error(f"Error in metrics collection: {e}")

            # Wait for next collection interval
            await asyncio.sleep(self.collection_interval)

    async def _collect_metrics(self) -> None:
        """Collect system metrics."""
        # This is a placeholder for system metric collection
        # In a real implementation, this would collect CPU, memory, etc.
        pass

    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.retention_period)

        async with self._async_lock:
            for name, points in list(self.metrics.items()):
                # Filter out old points
                self.metrics[name] = [p for p in points if p.timestamp >= cutoff]

                # Remove empty metrics
                if not self.metrics[name]:
                    del self.metrics[name]

    async def _store_metrics(self) -> None:
        """Store metrics to disk."""
        if not self.metrics:
            return

        now = datetime.now(timezone.utc)
        filename = f"{self.service_name}_{now.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.storage_path / filename

        async with self._async_lock:
            # Convert metrics to dictionaries
            metrics_data = {}
            for name, points in self.metrics.items():
                metrics_data[name] = [p.to_dict() for p in points]

            # Write to file
            with open(filepath, "w") as f:
                json.dump(metrics_data, f)

            self.logger.debug(
                f"Stored {sum(len(points) for points in self.metrics.values())} metrics to {filepath}"
            )

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        category: MetricCategory = MetricCategory.SYSTEM,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            category: Category of metric
            labels: Optional metric labels
        """
        if not self._ensure_async_lock():
            # No event loop, skip metrics collection
            return
        async with self._async_lock:
            # Create metric data point
            metric = MetricDataPoint(
                name=name,
                value=value,
                type=metric_type,
                category=category,
                labels=labels or {},
            )

            # Store in appropriate collection
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(metric)

            # Handle special metric types
            if metric_type == MetricType.COUNTER:
                # For counters, we store the current value
                self._counters[name] = value
            elif metric_type == MetricType.HISTOGRAM:
                # For histograms, we store all values
                if name not in self._histograms:
                    self._histograms[name] = []
                self._histograms[name].append(value)

    async def increment_counter(
        self,
        name: str,
        increment: float = 1.0,
        category: MetricCategory = MetricCategory.SYSTEM,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            increment: Amount to increment
            category: Metric category
            labels: Optional metric labels
        """
        if not self._ensure_async_lock():
            # No event loop, skip metrics collection
            return
        async with self._async_lock:
            # Get current value
            current_value = self._counters.get(name, 0.0)

            # Increment
            new_value = current_value + increment
            self._counters[name] = new_value

            # Record metric
            await self.record_metric(
                name=name,
                value=new_value,
                metric_type=MetricType.COUNTER,
                category=category,
                labels=labels,
            )

    async def observe_histogram(
        self,
        name: str,
        value: float,
        category: MetricCategory = MetricCategory.SYSTEM,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Add an observation to a histogram metric.

        Args:
            name: Metric name
            value: Observed value
            category: Metric category
            labels: Optional metric labels
        """
        await self.record_metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            category=category,
            labels=labels,
        )

    async def record_error(
        self,
        source: str,
        error_message: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record an error occurrence.

        Args:
            source: Error source
            error_message: Error message
            labels: Optional error labels
        """
        async with self._async_lock:
            self._error_counts[source] = self._error_counts.get(source, 0) + 1
            self._total_operations += 1

            # Create labels with error message
            error_labels = {"error": error_message}
            if labels:
                error_labels.update(labels)

            # Record metric
            await self.record_metric(
                name=f"{source}_error",
                value=1.0,
                metric_type=MetricType.COUNTER,
                category=MetricCategory.SECURITY,
                labels=error_labels,
            )

    async def record_success(
        self,
        operation: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a successful operation.

        Args:
            operation: Operation name
            labels: Optional operation labels
        """
        async with self._async_lock:
            self._success_counts[operation] = self._success_counts.get(operation, 0) + 1
            self._total_operations += 1

            # Record metric
            await self.record_metric(
                name=f"{operation}_success",
                value=1.0,
                metric_type=MetricType.COUNTER,
                category=MetricCategory.SYSTEM,
                labels=labels,
            )

    async def record_latency(
        self,
        operation: str,
        latency: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record operation latency.

        Args:
            operation: Operation name
            latency: Operation latency in seconds
            labels: Optional operation labels
        """
        async with self._async_lock:
            if operation not in self._latency_metrics:
                self._latency_metrics[operation] = []
            self._latency_metrics[operation].append(latency)

            # Record metric
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
        categories: Optional[List[MetricCategory]] = None,
    ) -> List[MetricDataPoint]:
        """
        Get metrics with optional filtering.

        Args:
            names: Optional list of metric names to filter
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            labels: Optional labels to filter by
            categories: Optional categories to filter by

        Returns:
            List of matching metrics
        """
        async with self._async_lock:
            metrics = []

            for name, points in self.metrics.items():
                # Filter by name
                if names and name not in names:
                    continue

                for point in points:
                    # Filter by time
                    if start_time and point.timestamp < start_time:
                        continue
                    if end_time and point.timestamp > end_time:
                        continue

                    # Filter by labels
                    if labels and not all(
                        point.labels.get(k) == v for k, v in labels.items()
                    ):
                        continue

                    # Filter by category
                    if categories and point.category not in categories:
                        continue

                    metrics.append(point)

            return metrics

    async def get_latest_metrics(
        self,
        names: Optional[List[str]] = None,
        labels: Optional[Dict[str, str]] = None,
        categories: Optional[List[MetricCategory]] = None,
    ) -> Dict[str, MetricDataPoint]:
        """
        Get latest metrics with optional filtering.

        Args:
            names: Optional list of metric names to filter
            labels: Optional labels to filter by
            categories: Optional categories to filter by

        Returns:
            Dictionary of metric name to latest data point
        """
        async with self._async_lock:
            latest_metrics = {}

            for name, points in self.metrics.items():
                # Filter by name
                if names and name not in names:
                    continue

                if not points:
                    continue

                # Get latest point
                latest = max(points, key=lambda p: p.timestamp)

                # Filter by labels
                if labels and not all(
                    latest.labels.get(k) == v for k, v in labels.items()
                ):
                    continue

                # Filter by category
                if categories and latest.category not in categories:
                    continue

                latest_metrics[name] = latest

            return latest_metrics

    async def get_error_count(self, source: str) -> int:
        """
        Get error count for a source.

        Args:
            source: Error source

        Returns:
            Number of errors for the source
        """
        async with self._async_lock:
            return self._error_counts.get(source, 0)

    async def get_success_rate(self) -> float:
        """
        Get overall success rate.

        Returns:
            Success rate as a float between 0 and 1
        """
        async with self._async_lock:
            if self._total_operations == 0:
                return 1.0

            total_successes = sum(self._success_counts.values())
            return total_successes / self._total_operations

    async def get_average_latency(self, operation: str) -> float:
        """
        Get average latency for an operation.

        Args:
            operation: Operation name

        Returns:
            Average latency in seconds
        """
        async with self._async_lock:
            if (
                operation not in self._latency_metrics
                or not self._latency_metrics[operation]
            ):
                return 0.0

            return sum(self._latency_metrics[operation]) / len(
                self._latency_metrics[operation]
            )

    async def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        async with self._async_lock:
            self.metrics.clear()
            self._counters.clear()
            self._histograms.clear()
            self._latency_metrics.clear()
            self._error_counts.clear()
            self._success_counts.clear()
            self._total_operations = 0

    async def export_metrics(
        self, format: str = "json", destination: Optional[Union[str, Path]] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Export metrics in various formats.

        Args:
            format: Export format (json, prometheus, etc.)
            destination: Optional file destination

        Returns:
            Exported metrics as string or dictionary
        """
        async with self._async_lock:
            if format == "json":
                # Convert metrics to JSON
                metrics_data = {}
                for name, points in self.metrics.items():
                    metrics_data[name] = [p.to_dict() for p in points]

                # Write to file if destination provided
                if destination:
                    path = Path(destination)
                    with open(path, "w") as f:
                        json.dump(metrics_data, f, indent=2)

                return metrics_data
            elif format == "prometheus":
                # Convert metrics to Prometheus format
                lines = []
                latest_metrics = {}

                # Get latest value for each metric
                for name, points in self.metrics.items():
                    if not points:
                        continue
                    latest = max(points, key=lambda p: p.timestamp)
                    latest_metrics[name] = latest

                # Format as Prometheus metrics
                for name, metric in latest_metrics.items():
                    # Add type comment
                    lines.append(f"# TYPE {name} {metric.type.value}")

                    # Add metric with labels
                    if metric.labels:
                        labels_str = ",".join(
                            f'{k}="{v}"' for k, v in metric.labels.items()
                        )
                        lines.append(f"{name}{{{labels_str}}} {metric.value}")
                    else:
                        lines.append(f"{name} {metric.value}")

                result = "\n".join(lines)

                # Write to file if destination provided
                if destination:
                    path = Path(destination)
                    with open(path, "w") as f:
                        f.write(result)

                return result
            else:
                raise ValueError(f"Unsupported export format: {format}")


# Singleton instance
_metrics_collector_instance = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get the singleton metrics collector instance.

    Returns:
        MetricsCollector instance
    """
    global _metrics_collector_instance
    if _metrics_collector_instance is None:
        _metrics_collector_instance = MetricsCollector()
    return _metrics_collector_instance


async def record_metric(
    name: str,
    value: float,
    metric_type: MetricType = MetricType.GAUGE,
    category: MetricCategory = MetricCategory.SYSTEM,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """
    Record a metric.

    Args:
        name: Metric name
        value: Metric value
        metric_type: Type of metric
        category: Category of metric
        labels: Optional metric labels
    """
    await get_metrics_collector().record_metric(
        name=name,
        value=value,
        metric_type=metric_type,
        category=category,
        labels=labels,
    )


async def increment_counter(
    name: str,
    increment: float = 1.0,
    category: MetricCategory = MetricCategory.SYSTEM,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """
    Increment a counter metric.

    Args:
        name: Metric name
        increment: Amount to increment
        category: Metric category
        labels: Optional metric labels
    """
    try:
        await get_metrics_collector().increment_counter(
            name=name,
            increment=increment,
            category=category,
            labels=labels,
        )
    except Exception:
        # Silently ignore metrics errors to prevent agent hanging
        pass


async def observe_histogram(
    name: str,
    value: float,
    category: MetricCategory = MetricCategory.SYSTEM,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """
    Add an observation to a histogram metric.

    Args:
        name: Metric name
        value: Observed value
        category: Metric category
        labels: Optional metric labels
    """
    await get_metrics_collector().observe_histogram(
        name=name,
        value=value,
        category=category,
        labels=labels,
    )


# Alias for backward compatibility
async def increment_metric(
    name: str,
    increment: float = 1.0,
    category: MetricCategory = MetricCategory.SYSTEM,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """
    Increment a metric (alias for increment_counter).

    Args:
        name: Metric name
        increment: Amount to increment
        category: Metric category
        labels: Optional metric labels
    """
    try:
        await increment_counter(
            name=name,
            increment=increment,
            category=category,
            labels=labels,
        )
    except Exception:
        # Silently ignore metrics errors to prevent agent hanging
        pass


# Additional alias for backward compatibility
async def register_metric(
    name: str,
    value: float,
    metric_type: MetricType = MetricType.GAUGE,
    category: MetricCategory = MetricCategory.SYSTEM,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """
    Register a metric (alias for record_metric).

    Args:
        name: Metric name
        value: Metric value
        metric_type: Type of metric
        category: Metric category
        labels: Optional metric labels
    """
    await record_metric(
        name=name,
        value=value,
        metric_type=metric_type,
        category=category,
        labels=labels,
    )


# Additional alias for backward compatibility
async def set_metric(
    name: str,
    value: float,
    metric_type: MetricType = MetricType.GAUGE,
    category: MetricCategory = MetricCategory.SYSTEM,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """
    Set a metric value (alias for record_metric).

    Args:
        name: Metric name
        value: Metric value
        metric_type: Type of metric
        category: Metric category
        labels: Optional metric labels
    """
    try:
        await record_metric(
            name=name,
            value=value,
            metric_type=metric_type,
            category=category,
            labels=labels,
        )
    except Exception:
        # Silently ignore metrics errors to prevent agent hanging
        pass
