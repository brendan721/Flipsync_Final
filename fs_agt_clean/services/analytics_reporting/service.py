#!/usr/bin/env python3
"""
Metrics Service Implementation
Features:
1. Counter tracking
2. Histogram metrics
3. Gauge metrics
4. Label support
5. Database persistence
6. Aggregation support
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from prometheus_client import Counter, Gauge, Histogram

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.database.models import (
    Metric,
    MetricAggregation,
    MetricSeries,
    MetricType,
)
from fs_agt_clean.database.repositories.metrics_repository import (
    MetricAggregationRepository,
    MetricRepository,
    MetricSeriesRepository,
)

logger = logging.getLogger(__name__)


class MetricsService:
    """Handles metrics collection and reporting."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        database: Optional[Database] = None,
    ):
        """Initialize metrics service.

        Args:
            config_manager: Optional configuration manager instance
            database: Optional database instance
        """
        self.config = config_manager
        self.database = database

        # Initialize repositories (will be set up with session when needed)
        self.metric_repository = None
        self.metric_series_repository = None
        self.metric_aggregation_repository = None

        # Initialize database if provided
        if self.database:
            self._initialize_repositories()

        # Initialize Prometheus metrics for backward compatibility
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}

        # In-memory cache for performance
        self._metric_cache: Dict[str, Dict[str, Any]] = {}
        self._last_aggregation_time: Dict[str, datetime] = {}
        self._aggregation_interval = timedelta(minutes=5)  # Aggregate every 5 minutes

        # Initialize document operation metrics
        self._histograms["document_operation_duration"] = Histogram(
            "document_operation_duration_seconds",
            "Duration of document operations",
            ["operation_type"],
        )

        self._counters["document_operation_errors"] = Counter(
            "document_operation_errors_total",
            "Total number of document operation errors",
            ["operation_type", "error_type"],
        )

        self._counters["document_operations_total"] = Counter(
            "document_operations_total",
            "Total number of document operations",
            ["operation_type"],
        )

        # Search performance metrics
        self._histograms["search_duration"] = Histogram(
            "search_duration_seconds", "Duration of search operations", ["query_type"]
        )

        # Load testing metrics
        self._histograms["response_time"] = Histogram(
            "response_time_seconds", "Response time for requests", ["endpoint"]
        )

        self._counters["requests_total"] = Counter(
            "requests_total", "Total number of requests", ["endpoint", "status"]
        )

        logger.info("MetricsService initialized with document operation tracking")

    def _initialize_repositories(self):
        """Initialize repositories with database session.

        Note: Repositories will be initialized with session when database operations are needed.
        This is a placeholder for future async session management.
        """
        # Repositories will be created with sessions when needed in async methods
        pass

    async def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict] = None
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name
            value: Value to increment by
            labels: Optional metric labels
        """
        try:
            # Update Prometheus counter for backward compatibility
            if name not in self._counters:
                self._counters[name] = Counter(
                    name, name, list(labels.keys()) if labels else []
                )

            if labels:
                self._counters[name].labels(**labels).inc(value)
            else:
                self._counters[name].inc(value)

            # Store in database
            await self.record_metric(name, value, MetricType.COUNTER, labels)

            logger.debug("Incremented counter %s by %s", name, value)
        except Exception as e:
            logger.error("Failed to increment counter %s: %s", name, e)

    def _get_cache_key(self, name: str, labels: Optional[Dict] = None) -> str:
        """Generate a cache key for a metric.

        Args:
            name: Metric name
            labels: Optional metric labels

        Returns:
            Cache key string
        """
        if not labels:
            return name

        # Sort labels by key to ensure consistent cache keys
        sorted_labels = sorted(labels.items())
        label_str = ",".join(f"{k}={v}" for k, v in sorted_labels)
        return f"{name}{{{label_str}}}"

    async def _check_aggregation(
        self, name: str, labels: Optional[Dict] = None
    ) -> None:
        """Check if we need to aggregate metrics.

        Args:
            name: Metric name
            labels: Optional metric labels
        """
        cache_key = self._get_cache_key(name, labels)
        now = datetime.utcnow()

        # Check if we need to aggregate
        last_aggregation = self._last_aggregation_time.get(cache_key)
        if last_aggregation and (now - last_aggregation) < self._aggregation_interval:
            return

        # Update last aggregation time
        self._last_aggregation_time[cache_key] = now

        # Get metrics for aggregation
        try:
            # Get metrics from the last hour
            start_time = now - timedelta(hours=1)
            metrics = await self.metric_repository.get_by_time_range(start_time, now)

            # Filter by name and labels
            filtered_metrics = []
            for metric in metrics:
                if metric.name != name:
                    continue

                if labels and metric.labels != labels:
                    continue

                filtered_metrics.append(metric)

            if not filtered_metrics:
                return

            # Get values for aggregation
            values = [metric.value for metric in filtered_metrics]

            # Create aggregation
            await self.metric_aggregation_repository.create_metric_aggregation(
                name=name,
                metric_type=filtered_metrics[0].type,
                values=values,
                start_time=start_time,
                end_time=now,
                description=f"Aggregation of {name}",
                labels=labels,
                component=filtered_metrics[0].component,
                user_id=filtered_metrics[0].user_id,
            )

            logger.debug("Created aggregation for %s with %d values", name, len(values))
        except Exception as e:
            logger.error("Failed to create aggregation for %s: %s", name, e)

    async def record_operation_duration(
        self, operation_type: str, duration: float
    ) -> None:
        """Record duration of a document operation.

        Args:
            operation_type: Type of operation (create/update/delete/get)
            duration: Duration in seconds
        """
        try:
            # Update Prometheus metrics for backward compatibility
            self._histograms["document_operation_duration"].labels(
                operation_type=operation_type
            ).observe(duration)
            self._counters["document_operations_total"].labels(
                operation_type=operation_type
            ).inc()

            # Store in database
            await self.record_metric(
                name="document_operation_duration",
                value=duration,
                metric_type=MetricType.HISTOGRAM,
                labels={"operation_type": operation_type},
                component="document_operations",
            )

            await self.record_metric(
                name="document_operations_total",
                value=1.0,
                metric_type=MetricType.COUNTER,
                labels={"operation_type": operation_type},
                component="document_operations",
            )
        except Exception as e:
            logger.error("Failed to record operation duration: %s", e)

    async def record_operation_error(
        self, operation_type: str, error_type: str
    ) -> None:
        """Record a document operation error.

        Args:
            operation_type: Type of operation that failed
            error_type: Type of error encountered
        """
        try:
            # Update Prometheus metrics for backward compatibility
            self._counters["document_operation_errors"].labels(
                operation_type=operation_type, error_type=error_type
            ).inc()

            # Store in database
            await self.record_metric(
                name="document_operation_errors",
                value=1.0,
                metric_type=MetricType.COUNTER,
                labels={
                    "operation_type": operation_type,
                    "error_type": error_type,
                },
                component="document_operations",
            )

            logger.error(
                "Document operation error: %s - %s", operation_type, error_type
            )
        except Exception as e:
            logger.error("Failed to record operation error: %s", e)

    async def record_search_duration(self, query_type: str, duration: float) -> None:
        """Record duration of a search operation.

        Args:
            query_type: Type of search query
            duration: Duration in seconds
        """
        try:
            # Update Prometheus metrics for backward compatibility
            self._histograms["search_duration"].labels(query_type=query_type).observe(
                duration
            )

            # Store in database
            await self.record_metric(
                name="search_duration",
                value=duration,
                metric_type=MetricType.HISTOGRAM,
                labels={"query_type": query_type},
                component="search_operations",
            )
        except Exception as e:
            logger.error("Failed to record search duration: %s", e)

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: Optional[MetricType] = None,
        labels: Optional[Dict] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric (counter, gauge, histogram)
            labels: Optional metric labels
            component: Optional component name
            user_id: Optional user ID
            description: Optional metric description
        """
        try:
            # Determine metric type if not provided
            if metric_type is None:
                if "time" in name.lower() or "duration" in name.lower():
                    metric_type = MetricType.HISTOGRAM
                elif "count" in name.lower() or "total" in name.lower():
                    metric_type = MetricType.COUNTER
                else:
                    metric_type = MetricType.GAUGE

            # Update Prometheus metrics for backward compatibility
            if metric_type == MetricType.HISTOGRAM:
                if name not in self._histograms:
                    self._histograms[name] = Histogram(
                        f"{name}_seconds",
                        f"{name} in seconds",
                        list(labels.keys()) if labels else [],
                    )
                if labels:
                    self._histograms[name].labels(**labels).observe(value)
                else:
                    self._histograms[name].observe(value)
            elif metric_type == MetricType.COUNTER:
                if name not in self._counters:
                    self._counters[name] = Counter(
                        name, name, list(labels.keys()) if labels else []
                    )
                if labels:
                    self._counters[name].labels(**labels).inc(value)
                else:
                    self._counters[name].inc(value)
            else:  # GAUGE
                if name not in self._gauges:
                    self._gauges[name] = Gauge(
                        name, name, list(labels.keys()) if labels else []
                    )
                if labels:
                    self._gauges[name].labels(**labels).set(value)
                else:
                    self._gauges[name].set(value)

            # Store in database
            await self.metric_repository.create_metric(
                name=name,
                metric_type=metric_type,
                value=value,
                description=description,
                labels=labels,
                user_id=user_id,
                component=component,
            )

            # Update cache
            cache_key = self._get_cache_key(name, labels)
            self._metric_cache[cache_key] = {
                "name": name,
                "value": value,
                "type": metric_type,
                "labels": labels,
                "timestamp": datetime.utcnow(),
            }

            # Check if we need to aggregate
            await self._check_aggregation(name, labels)

            logger.debug("Recorded metric %s = %s", name, value)
        except Exception as e:
            logger.error("Failed to record metric %s: %s", name, e)

    async def get_metrics(
        self,
        names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get metrics with optional filtering.

        Args:
            names: Optional list of metric names to filter
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            labels: Optional labels to filter by
            component: Optional component to filter by
            user_id: Optional user ID to filter by
            limit: Maximum number of metrics to return

        Returns:
            List of metrics as dictionaries
        """
        try:
            # Set default time range if not provided
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=1)

            # Get metrics from database
            metrics = await self.metric_repository.get_by_time_range(
                start_time, end_time
            )

            # Filter by name if provided
            if names:
                metrics = [m for m in metrics if m.name in names]

            # Filter by component if provided
            if component:
                metrics = [m for m in metrics if m.component == component]

            # Filter by user ID if provided
            if user_id:
                metrics = [m for m in metrics if m.user_id == user_id]

            # Filter by labels if provided
            if labels:
                filtered_metrics = []
                for metric in metrics:
                    if not metric.labels:
                        continue

                    match = True
                    for k, v in labels.items():
                        if k not in metric.labels or metric.labels[k] != v:
                            match = False
                            break

                    if match:
                        filtered_metrics.append(metric)

                metrics = filtered_metrics

            # Convert to dictionaries and limit results
            return [m.to_dict() for m in metrics[:limit]]
        except Exception as e:
            logger.error("Failed to get metrics: %s", e)
            return []

    async def get_aggregations(
        self,
        names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get metric aggregations with optional filtering.

        Args:
            names: Optional list of metric names to filter
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            labels: Optional labels to filter by
            component: Optional component to filter by
            user_id: Optional user ID to filter by
            limit: Maximum number of aggregations to return

        Returns:
            List of aggregations as dictionaries
        """
        try:
            # Set default time range if not provided
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(days=7)  # Default to last week

            # Get aggregations from database
            aggregations = await self.metric_aggregation_repository.get_by_time_range(
                start_time, end_time
            )

            # Filter by name if provided
            if names:
                aggregations = [a for a in aggregations if a.name in names]

            # Filter by component if provided
            if component:
                aggregations = [a for a in aggregations if a.component == component]

            # Filter by user ID if provided
            if user_id:
                aggregations = [a for a in aggregations if a.user_id == user_id]

            # Filter by labels if provided
            if labels:
                filtered_aggregations = []
                for agg in aggregations:
                    if not agg.labels:
                        continue

                    match = True
                    for k, v in labels.items():
                        if k not in agg.labels or agg.labels[k] != v:
                            match = False
                            break

                    if match:
                        filtered_aggregations.append(agg)

                aggregations = filtered_aggregations

            # Convert to dictionaries and limit results
            return [a.to_dict() for a in aggregations[:limit]]
        except Exception as e:
            logger.error("Failed to get aggregations: %s", e)
            return []

    async def get_metric_series(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 1000,
    ) -> Dict[str, Any]:
        """Get a time series for a specific metric.

        Args:
            name: Metric name
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            labels: Optional labels to filter by
            component: Optional component to filter by
            user_id: Optional user ID to filter by
            limit: Maximum number of data points to return

        Returns:
            Dictionary with time series data
        """
        try:
            # Set default time range if not provided
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(hours=24)  # Default to last 24 hours

            # Get metrics from database
            metrics = await self.metric_repository.get_by_time_range(
                start_time, end_time
            )

            # Filter by name
            metrics = [m for m in metrics if m.name == name]

            # Filter by component if provided
            if component:
                metrics = [m for m in metrics if m.component == component]

            # Filter by user ID if provided
            if user_id:
                metrics = [m for m in metrics if m.user_id == user_id]

            # Filter by labels if provided
            if labels:
                filtered_metrics = []
                for metric in metrics:
                    if not metric.labels:
                        continue

                    match = True
                    for k, v in labels.items():
                        if k not in metric.labels or metric.labels[k] != v:
                            match = False
                            break

                    if match:
                        filtered_metrics.append(metric)

                metrics = filtered_metrics

            # Sort by timestamp
            metrics.sort(key=lambda m: m.timestamp)

            # Limit the number of data points
            metrics = metrics[:limit]

            # Create time series data
            values = []
            for metric in metrics:
                values.append(
                    {
                        "timestamp": metric.timestamp.isoformat(),
                        "value": metric.value,
                    }
                )

            # Create series object
            series = {
                "name": name,
                "values": values,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "labels": labels,
                "component": component,
                "user_id": user_id,
            }

            return series
        except Exception as e:
            logger.error("Failed to get metric series: %s", e)
            return {
                "name": name,
                "values": [],
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "labels": labels,
                "component": component,
                "user_id": user_id,
                "error": str(e),
            }


# Global metrics service instance
_metrics_service_instance = None


def get_metrics_service() -> MetricsService:
    """Get the global metrics service instance.

    Returns:
        MetricsService: Metrics service instance
    """
    global _metrics_service_instance
    if _metrics_service_instance is None:
        from fs_agt_clean.core.config.manager import ConfigManager
        from fs_agt_clean.core.db.database import get_database

        _metrics_service_instance = MetricsService(
            config_manager=ConfigManager(),
            database=get_database(),
        )
    return _metrics_service_instance
