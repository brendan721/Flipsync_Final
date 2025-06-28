"""
Compatibility module for metrics collector.

This module defines the MetricsCollector class directly to avoid import issues.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union


# Define the MetricType enum (Moved before MetricConfig)
class MetricType(Enum):
    """Metric type enum."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


# Added from collectors.py
@dataclass
class MetricConfig:
    """Configuration for metric collection."""

    name: str
    type: MetricType
    window_size: int = 300  # 5 minutes default
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    enabled: bool = True


# Define the MetricDataPoint class
@dataclass
class MetricDataPoint:
    """Metric data point."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    type: MetricType = MetricType.GAUGE


# Define the BaseCollector class (Replaced with version from collectors.py)
class BaseCollector(ABC):
    """Base class for metric collectors."""

    def __init__(self):
        """Initialize collector."""
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._last_cleanup = datetime.now()
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    async def collect(
        self,
    ) -> Sequence[Union[Dict[str, Any], MetricDataPoint]]:
        """Collect metrics.

        Returns:
            Sequence[Union[Dict[str, Any], MetricDataPoint]]: List of collected
                metrics
        """
        pass

    @abstractmethod
    async def record(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels/tags
        """
        pass

    def get_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get current metrics.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Current metrics
        """
        return self.metrics.copy()

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()

    async def record_metrics(
        self, metrics: Dict[str, float], labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record multiple metrics at once.

        Args:
            metrics: Dictionary of metric names and values
            labels: Optional labels/tags to apply to all metrics
        """
        for name, value in metrics.items():
            await self.record(name, value, labels)

    async def get_latest_metrics(
        self,
    ) -> Sequence[Union[Dict[str, Any], MetricDataPoint]]:
        """Get the latest metrics.

        Returns:
            Sequence[Union[Dict[str, Any], MetricDataPoint]]: Latest metrics
        """
        return await self.collect()

    async def get_metrics_history(
        self,
    ) -> Sequence[Sequence[Union[Dict[str, Any], MetricDataPoint]]]:
        """Get historical metrics.

        Returns:
            Sequence[Sequence[Union[Dict[str, Any], MetricDataPoint]]]:
                Historical metrics
        """
        # Default implementation just returns current metrics as single history point
        metrics = await self.collect()
        return [metrics] if metrics else []

    async def get_resource_metrics(self, agent_id: str) -> Dict[str, float]:
        """Get resource metrics for an agent.

        Args:
            agent_id: ID of the agent to get metrics for

        Returns:
            Dictionary of resource metrics
        """
        metrics = {}
        for name, points in self.metrics.items():
            if points and name.startswith(f"{agent_id}_"):
                # Ensure value exists and is accessible safely
                if isinstance(points[-1], dict):
                    value = points[-1].get("value")
                    if value is not None:
                        # Use .get() for safer access
                        metrics[name.split("_", 1)[1]] = float(value)
        return metrics

    async def get_uptime(self, agent_id: str) -> float:
        """Get agent uptime in seconds."""
        metric_name = f"{agent_id}_uptime"
        if metric_name in self.metrics and self.metrics[metric_name]:
            last_point = self.metrics[metric_name][-1]
            if isinstance(last_point, dict):
                # Use .get() for safer access
                value = last_point.get("value")
                if value is not None:
                    return float(value)
        return 0.0

    async def get_error_count(self, agent_id: str) -> int:
        """Get agent error count."""
        metric_name = f"{agent_id}_errors"
        if metric_name in self.metrics and self.metrics[metric_name]:
            last_point = self.metrics[metric_name][-1]
            if isinstance(last_point, dict):
                # Use .get() for safer access
                value = last_point.get("value")
                if value is not None:
                    return int(value)
        return 0

    async def get_last_error(self, agent_id: str) -> Optional[datetime]:
        """Get timestamp of last error."""
        metric_name = f"{agent_id}_last_error"
        if metric_name in self.metrics and self.metrics[metric_name]:
            last_point = self.metrics[metric_name][-1]
            if isinstance(last_point, dict):
                # Use .get() for safer access
                timestamp = last_point.get("timestamp")
                # Check if timestamp is already datetime object
                if isinstance(timestamp, datetime):
                    return timestamp
                # Attempt conversion if it's a string (common case)
                elif isinstance(timestamp, str):
                    try:
                        return datetime.fromisoformat(timestamp)
                    except ValueError:
                        self.logger.warning(
                            f"Invalid timestamp format for {metric_name}: "
                            f"{timestamp}"
                        )
                        return None
        return None

    async def get_last_success(self, agent_id: str) -> Optional[datetime]:
        """Get timestamp of last success."""
        metric_name = f"{agent_id}_last_success"
        if metric_name in self.metrics and self.metrics[metric_name]:
            last_point = self.metrics[metric_name][-1]
            if isinstance(last_point, dict):
                # Use .get() for safer access
                timestamp = last_point.get("timestamp")
                # Check if timestamp is already datetime object
                if isinstance(timestamp, datetime):
                    return timestamp
                # Attempt conversion if it's a string (common case)
                elif isinstance(timestamp, str):
                    try:
                        return datetime.fromisoformat(timestamp)
                    except ValueError:
                        self.logger.warning(
                            f"Invalid timestamp format for {metric_name}: "
                            f"{timestamp}"
                        )
                        return None
        return None


# Define the MetricsCollector class
class MetricsCollector(BaseCollector):
    """Performance metrics collector."""

    def __init__(self):
        """Initialize performance metrics collector."""
        super().__init__()
        self.logger.info("Initialized MetricsCollector")

    async def collect(self) -> Sequence[Union[Dict[str, Any], MetricDataPoint]]:
        """Collect performance metrics."""
        metrics: List[Union[Dict[str, Any], MetricDataPoint]] = []
        for metric_list in self.metrics.values():
            metrics.extend(metric_list)
        return metrics

    async def record(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []

        metric: Dict[str, Any] = {
            "name": name,
            "value": value,
            "timestamp": datetime.now(),
            "type": MetricType.GAUGE.value,
            "labels": labels or {},
        }
        self.metrics[name].append(metric)

    async def record_metric(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric - alias for record() method to maintain compatibility with webhook_monitor.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels/tags
        """
        self.logger.debug(f"Recording metric: {name}={value} with labels={labels}")
        await self.record(name, value, labels)


# Export the class (Updated)
__all__ = [
    "MetricsCollector",
    "MetricType",
    "MetricDataPoint",
    "BaseCollector",
    "MetricConfig",
]
