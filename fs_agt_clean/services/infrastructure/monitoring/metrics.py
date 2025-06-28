"""Core metrics module for monitoring."""

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from prometheus_client import Counter, Gauge, Histogram

# Import from new types module
from fs_agt_clean.core.monitoring.types import (
    MetricCategory,
    MetricsServiceProtocol,
    MetricType,
)

# Define logging - replace get_logger with standard logging
logger = logging.getLogger(__name__)

# ML Service Metrics
ML_REQUEST_LATENCY = Histogram(
    "ml_request_duration_seconds",
    "ML request processing duration",
    ["operation", "status"],
)

ML_REQUESTS_TOTAL = Counter(
    "ml_requests_total",
    "Total ML request count",
    ["operation", "status"],
)

DB_OPERATION_LATENCY = Histogram(
    "db_operation_duration_seconds",
    "Database operation duration",
    ["operation", "status"],
)

DB_OPERATIONS_TOTAL = Counter(
    "db_operations_total",
    "Total database operation count",
    ["operation", "status"],
)

API_REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds",
    "API request processing duration",
    ["endpoint", "method", "status"],
)

API_REQUESTS_TOTAL = Counter(
    "api_requests_total",
    "Total API request count",
    ["endpoint", "method", "status"],
)


class MetricCollector:
    """Collector for application metrics."""

    def __init__(self, service_name: str):
        """Initialize the metric collector.

        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.metrics: List[Dict[str, Any]] = []
        self.operation_start_times: Dict[str, datetime] = {}

    async def record_start(self, operation: str) -> None:
        """Record the start of an operation.

        Args:
            operation: Operation name
        """
        self.operation_start_times[operation] = datetime.utcnow()

    async def record_success(
        self, operation: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a successful operation completion.

        Args:
            operation: Operation name
            data: Additional data to record
        """
        start_time = self.operation_start_times.pop(operation, None)
        if start_time:
            duration = datetime.utcnow() - start_time
            self._record_metric(operation, "success", duration, data)

    async def record_failure(
        self, operation: str, error: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a failed operation.

        Args:
            operation: Operation name
            error: Error message
            data: Additional data to record
        """
        if data is None:
            data = {}
        data["error"] = error

        start_time = self.operation_start_times.pop(operation, None)
        if start_time:
            duration = datetime.utcnow() - start_time
            self._record_metric(operation, "failure", duration, data)

    def _record_metric(
        self,
        operation: str,
        status: str,
        duration: timedelta,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Internal method to record a metric.

        Args:
            operation: Operation name
            status: Status (success or failure)
            duration: Operation duration
            data: Additional data to record
        """
        if data is None:
            data = {}

        metric = {
            "service": self.service_name,
            "operation": operation,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": duration.total_seconds() * 1000,
            "data": data,
        }

        self.metrics.append(metric)

        # If metrics logging enabled, log the metric
        try:
            # Record relevant metrics based on operation type
            if "db" in operation.lower():
                DB_OPERATION_LATENCY.labels(operation=operation, status=status).observe(
                    duration.total_seconds()
                )
                DB_OPERATIONS_TOTAL.labels(operation=operation, status=status).inc()
            elif "ml" in operation.lower():
                ML_REQUEST_LATENCY.labels(operation=operation, status=status).observe(
                    duration.total_seconds()
                )
                ML_REQUESTS_TOTAL.labels(operation=operation, status=status).inc()
            elif "api" in operation.lower():
                endpoint = data.get("endpoint", "unknown")
                method = data.get("method", "unknown")
                API_REQUEST_LATENCY.labels(
                    endpoint=endpoint, method=method, status=status
                ).observe(duration.total_seconds())
                API_REQUESTS_TOTAL.labels(
                    endpoint=endpoint, method=method, status=status
                ).inc()
        except Exception as e:
            logger.warning("Failed to record Prometheus metric: %s", str(e))

    def get_metrics(
        self,
        operation: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get metrics with optional filtering.

        Args:
            operation: Filter by operation name
            status: Filter by status
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            List of filtered metrics
        """
        filtered_metrics = self.metrics.copy()

        if operation:
            filtered_metrics = [
                m for m in filtered_metrics if m["operation"] == operation
            ]

        if status:
            filtered_metrics = [m for m in filtered_metrics if m["status"] == status]

        if start_time:
            filtered_metrics = [
                m
                for m in filtered_metrics
                if datetime.fromisoformat(m["timestamp"]) >= start_time
            ]

        if end_time:
            filtered_metrics = [
                m
                for m in filtered_metrics
                if datetime.fromisoformat(m["timestamp"]) <= end_time
            ]

        return filtered_metrics


class MetricsMixin:
    """Mixin for adding metrics collection to a class."""

    def __init__(self):
        """Initialize the metrics mixin."""
        self.metrics_collector = MetricCollector(self.__class__.__name__)


class MetricsService(MetricsServiceProtocol):
    """Implementation of the MetricsServiceProtocol."""

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
        pass

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
        pass

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
        pass

    async def record_metric(
        self,
        name: str,
        value: Union[float, Dict[str, float]],
        metric_type: MetricType = MetricType.GAUGE,
        category: MetricCategory = MetricCategory.RESOURCE,
        labels: Optional[Dict[str, str]] = None,
        source: str = "system",
    ) -> Any:
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
            Metric update record
        """
        logger.debug("Recording metric %s=%s", name, value)
        # Implementation would be here
        return None


class MetricsMiddleware:
    """Middleware for tracking metrics."""

    @staticmethod
    async def track_token_metrics(token_type: str, start_time: datetime) -> None:
        """
        Track token validation metrics.

        Args:
            token_type: Type of token
            start_time: Start time of the operation
        """
        try:
            duration = (datetime.utcnow() - start_time).total_seconds()
            # Use instance method instead of static method
            metrics_service = MetricsService()
            await metrics_service.record_metric(
                name="token_validation_duration",
                value=duration,
                metric_type=MetricType.HISTOGRAM,
                labels={"token_type": token_type},
            )

        except Exception as e:
            logger.error("Failed to track token metrics: %s", str(e))

    @staticmethod
    async def track_redis_metrics(
        operation: str, start_time: datetime, success: bool = True
    ) -> None:
        """
        Track Redis operation metrics.

        Args:
            operation: Redis operation
            start_time: Start time of the operation
            success: Whether the operation was successful
        """
        try:
            duration = (datetime.utcnow() - start_time).total_seconds()
            status = "success" if success else "error"

            # Use instance method instead of static method
            metrics_service = MetricsService()
            await metrics_service.record_metric(
                name="redis_operation_duration",
                value=duration,
                metric_type=MetricType.HISTOGRAM,
                labels={"operation": operation, "status": status},
            )

            if not success:
                await metrics_service.record_metric(
                    name="redis_error_count",
                    value=1.0,
                    metric_type=MetricType.COUNTER,
                    labels={"operation": operation},
                )

        except Exception as e:
            logger.error("Failed to track Redis metrics: %s", str(e))


# Initialize metrics middleware
metrics_middleware = MetricsMiddleware()
