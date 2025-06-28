"""
FlipSync Metrics Protocol

This module defines the protocols and interfaces for metric collection, processing,
and storage within the FlipSync monitoring system.

This is part of the Phase 6 Monitoring Systems Consolidation effort.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"  # Cumulative value that only increases
    GAUGE = "gauge"  # Value that can go up and down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Summary statistics (e.g., percentiles)
    TIMER = "timer"  # Duration measurements


class MetricUnit(Enum):
    """Units for metric values."""

    COUNT = "count"
    BYTES = "bytes"
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    MICROSECONDS = "microseconds"
    PERCENTAGE = "percentage"
    REQUESTS = "requests"
    OPERATIONS = "operations"
    ERRORS = "errors"
    CUSTOM = "custom"


class MetricValue:
    """Represents a single metric value with metadata."""

    def __init__(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType,
        unit: MetricUnit = MetricUnit.COUNT,
        timestamp: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.value = value
        self.metric_type = metric_type
        self.unit = unit
        self.timestamp = timestamp or datetime.utcnow()
        self.labels = labels or {}
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric value to a dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "unit": self.unit.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "description": self.description,
        }


class MetricAggregation(Enum):
    """Aggregation methods for metrics."""

    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"
    RATE = "rate"
    DELTA = "delta"


class MetricProtocol(ABC):
    """Core protocol for metric management."""

    @abstractmethod
    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.COUNT,
        default_labels: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Register a new metric.

        Returns:
            str: Metric ID
        """
        pass

    @abstractmethod
    def unregister_metric(self, metric_id: str) -> None:
        """Unregister a metric."""
        pass

    @abstractmethod
    def collect_metric(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Collect a metric value."""
        pass

    @abstractmethod
    def increment_counter(
        self, name: str, increment: int = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        pass

    @abstractmethod
    def set_gauge(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge metric."""
        pass

    @abstractmethod
    def observe_histogram(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add an observation to a histogram metric."""
        pass

    @abstractmethod
    def start_timer(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Callable[[], None]:
        """
        Start a timer and return a function that stops the timer and records the duration.

        Returns:
            Callable[[], None]: Function to stop the timer and record duration
        """
        pass

    @abstractmethod
    def query_metrics(
        self,
        name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        aggregation: Optional[MetricAggregation] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query metrics based on criteria."""
        pass

    @abstractmethod
    def get_metric_names(self) -> List[str]:
        """Get all registered metric names."""
        pass

    @abstractmethod
    def get_label_keys(self, metric_name: Optional[str] = None) -> Set[str]:
        """Get all label keys for one or all metrics."""
        pass

    @abstractmethod
    def get_label_values(
        self: str, metric_name: Optional[str] = None
    ) -> Set[str]:
        """Get all values for a specific label key."""
        pass


class MetricCollector(ABC):
    """Protocol for metric collectors that gather metrics from components."""

    @property
    @abstractmethod
    def collector_id(self) -> str:
        """Unique identifier for this collector."""
        pass

    @property
    @abstractmethod
    def collector_name(self) -> str:
        """Human-readable name for this collector."""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the collector with configuration."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shutdown the collector."""
        pass

    @abstractmethod
    def collect_metrics(self) -> List[MetricValue]:
        """Collect metrics and return them."""
        pass

    @abstractmethod
    def get_collection_interval(self) -> timedelta:
        """Get the interval at which metrics should be collected from this collector."""
        pass

    @abstractmethod
    def get_last_collection_time(self) -> Optional[datetime]:
        """Get the time when metrics were last collected from this collector."""
        pass


class MetricStore(ABC):
    """Protocol for metric storage backends."""

    @abstractmethod
    def store_metric(self, metric: MetricValue) -> None:
        """Store a single metric value."""
        pass

    @abstractmethod
    def store_metrics(self, metrics: List[MetricValue]) -> None:
        """Store multiple metric values."""
        pass

    @abstractmethod
    def query_metrics(
        self,
        name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        aggregation: Optional[MetricAggregation] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query metrics based on criteria."""
        pass

    @abstractmethod
    def get_metric_names(self) -> List[str]:
        """Get all metric names in the store."""
        pass

    @abstractmethod
    def get_metric_labels(self, metric_name: str) -> Dict[str, Set[str]]:
        """Get all labels and their values for a specific metric."""
        pass

    @abstractmethod
    def prune_metrics(self, older_than: datetime) -> int:
        """Remove metrics older than the specified time, returns count of pruned metrics."""
        pass
