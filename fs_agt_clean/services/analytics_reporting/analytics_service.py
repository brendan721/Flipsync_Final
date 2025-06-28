"""Analytics service for processing and analyzing metrics data."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.metrics.models import MetricDataPoint, MetricType
from fs_agt_clean.core.monitoring.log_manager import LogManager


class AnalyticsService:
    """Service for processing and analyzing metrics data."""

    def __init__(self, config: ConfigManager, log_manager: LogManager):
        """Initialize analytics service.

        Args:
            config: Configuration manager
            log_manager: Log manager for recording events
        """
        self.config = config
        self.log_manager = log_manager
        self.metrics: Dict[str, List[MetricDataPoint]] = {}
        self._thresholds: Dict[str, float] = {}

    async def start(self) -> None:
        """Start the analytics service."""
        self.log_manager.info("Starting analytics service")

    async def stop(self) -> None:
        """Stop the analytics service."""
        self.log_manager.info("Stopping analytics service")

    async def process_metrics(
        self,
        category: str,
        metrics: Dict[str, float],
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Process incoming metrics.

        Args:
            category: Metric category
            metrics: Dictionary of metric names and values
            tags: Optional tags for the metrics
        """
        for name, value in metrics.items():
            point = MetricDataPoint(
                id=str(uuid.uuid4()),
                name=name,
                value=value,
                timestamp=datetime.now(),
                metric_type=MetricType.GAUGE,
                labels=tags or {},
            )
            if category not in self.metrics:
                self.metrics[category] = []
            self.metrics[category].append(point)

    async def check_thresholds(self, category: str) -> List[Dict[str, Any]]:
        """Check if any metrics exceed their thresholds.

        Args:
            category: Metric category to check

        Returns:
            List of threshold violations
        """
        violations = []
        if category in self.metrics:
            for point in self.metrics[category]:
                threshold = self._thresholds.get(point.name)
                if threshold is not None and point.value > threshold:
                    violations.append(
                        {
                            "metric": point.name,
                            "value": point.value,
                            "threshold": threshold,
                            "timestamp": point.timestamp,
                        }
                    )
        return violations

    async def get_metrics(
        self,
        category: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[MetricDataPoint]:
        """Get metrics with optional filtering.

        Args:
            category: Optional category filter
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of metric data points
        """
        metrics = []
        categories = [category] if category else self.metrics.keys()

        for cat in categories:
            if cat in self.metrics:
                for point in self.metrics[cat]:
                    if start_time and point.timestamp < start_time:
                        continue
                    if end_time and point.timestamp > end_time:
                        continue
                    metrics.append(point)

        return metrics
