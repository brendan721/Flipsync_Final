"""
Metrics service for FlipSync monitoring.

This module provides a service layer for recording and retrieving metrics,
integrating with the core metrics collector and providing a convenient API
for agents and other components.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fs_agt_clean.core.monitoring.metrics.collector import (
    MetricCategory,
    MetricDataPoint,
    MetricsCollector,
    MetricType,
)

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service for recording and retrieving metrics.

    This service provides a high-level API for metrics operations,
    abstracting the underlying metrics collector implementation.
    """

    def __init__(self, service_name: str = "default", **kwargs):
        """
        Initialize the metrics service.

        Args:
            service_name: Name of the service using metrics
            **kwargs: Additional arguments passed to MetricsCollector
        """
        self.service_name = service_name
        self.collector = MetricsCollector(service_name=service_name, **kwargs)
        self._started = False

    async def start(self) -> None:
        """Start the metrics service."""
        if not self._started:
            await self.collector.start()
            self._started = True
            logger.info(f"Metrics service started for {self.service_name}")

    async def stop(self) -> None:
        """Stop the metrics service."""
        if self._started:
            await self.collector.stop()
            self._started = False
            logger.info(f"Metrics service stopped for {self.service_name}")

    async def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        category: MetricCategory = MetricCategory.SYSTEM,
    ) -> None:
        """
        Record a gauge metric.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional metric labels
            category: Metric category
        """
        await self.collector.record_metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            category=category,
            labels=labels,
        )

    async def record_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
        category: MetricCategory = MetricCategory.SYSTEM,
    ) -> None:
        """
        Record a counter metric.

        Args:
            name: Metric name
            value: Increment value (default: 1.0)
            labels: Optional metric labels
            category: Metric category
        """
        await self.collector.increment_counter(
            name=name,
            increment=value,
            category=category,
            labels=labels,
        )

    async def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        category: MetricCategory = MetricCategory.PERFORMANCE,
    ) -> None:
        """
        Record a histogram metric.

        Args:
            name: Metric name
            value: Observed value
            labels: Optional metric labels
            category: Metric category
        """
        await self.collector.observe_histogram(
            name=name,
            value=value,
            category=category,
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
            latency: Latency in seconds
            labels: Optional operation labels
        """
        await self.collector.record_latency(
            operation=operation,
            latency=latency,
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
        await self.collector.record_error(
            source=source,
            error_message=error_message,
            labels=labels,
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
        await self.collector.record_success(
            operation=operation,
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
        return await self.collector.get_metrics(
            names=names,
            start_time=start_time,
            end_time=end_time,
            labels=labels,
            categories=categories,
        )

    async def get_metric_summary(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a metric.

        Args:
            name: Metric name
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering

        Returns:
            Summary statistics dictionary
        """
        return await self.collector.get_metric_summary(
            name=name,
            start_time=start_time,
            end_time=end_time,
        )

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the metrics service.

        Returns:
            Service information dictionary
        """
        return {
            "service_name": self.service_name,
            "started": self._started,
            "collector_info": {
                "collection_interval": self.collector.collection_interval,
                "retention_period": self.collector.retention_period,
                "mobile_optimized": self.collector.mobile_optimized,
                "storage_path": str(self.collector.storage_path),
            },
        }
