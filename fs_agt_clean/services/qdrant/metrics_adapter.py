"""Metrics adapter for Qdrant service."""

import logging
from typing import Dict, Mapping, Optional

from fs_agt_clean.core.metrics.service import MetricsService

logger = logging.getLogger(__name__)


class QdrantMetricsAdapter:
    """Adapter for collecting metrics from Qdrant operations."""

    def __init__(self, metrics_service: Optional[MetricsService] = None):
        """Initialize the metrics adapter.

        Args:
            metrics_service: Optional metrics service to use
        """
        self.metrics = metrics_service

    async def record_metric(
        self, name: str, value: float, labels: Optional[Mapping[str, str]] = None
    ) -> None:
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional metric labels
        """
        if self.metrics:
            try:
                await self.metrics.increment_counter(name, value, labels)
            except Exception as e:
                logger.error("Failed to record metric %s: %s", name, str(e))

    async def record_error(
        self, name: str, error: str, labels: Optional[Mapping[str, str]] = None
    ) -> None:
        """Record an error metric.

        Args:
            name: Error metric name
            error: Error message
            labels: Optional metric labels
        """
        if self.metrics:
            try:
                error_labels = {"error": error}
                if labels:
                    error_labels.update(labels)
                await self.metrics.increment_counter(f"{name}_count", 1.0, error_labels)
            except Exception as e:
                logger.error("Failed to record error metric %s: %s", name, str(e))
