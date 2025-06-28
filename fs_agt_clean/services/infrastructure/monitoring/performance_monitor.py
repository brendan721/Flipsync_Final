"""
Performance monitoring with real-time metrics for FlipSync.

This module implements comprehensive performance monitoring capabilities
with real-time metrics collection, analysis, and reporting for the FlipSync system.
It provides:
1. API endpoint performance tracking
2. Database query performance monitoring
3. External service call latency tracking
4. Resource utilization metrics (CPU, memory, network)
5. Custom business metrics for Amazon→eBay transformation pipeline
"""

import asyncio
import logging
import statistics
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

import prometheus_client
import psutil
from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client.exposition import start_http_server

# Configure logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricCategory(Enum):
    """Categories of metrics for organization."""

    API = "api"
    DATABASE = "database"
    EXTERNAL = "external"
    SYSTEM = "system"
    BUSINESS = "business"
    PIPELINE = "pipeline"


class PerformanceMonitor:
    """
    Performance monitoring system for FlipSync.

    This class provides methods for tracking, analyzing, and reporting
    performance metrics across the FlipSync system.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PerformanceMonitor, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        app_name: str = "flipsync",
        enable_prometheus: bool = True,
        prometheus_port: int = 9090,
        metrics_retention_days: int = 7,
        sampling_interval_seconds: int = 10,
        alert_thresholds: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        """
        Initialize the performance monitor.

        Args:
            app_name: Name of the application
            enable_prometheus: Whether to enable Prometheus metrics
            prometheus_port: Port to expose Prometheus metrics on
            metrics_retention_days: Number of days to retain metrics
            sampling_interval_seconds: Interval for sampling system metrics
            alert_thresholds: Thresholds for alerting on metrics
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return

        self.app_name = app_name
        self.enable_prometheus = enable_prometheus
        self.prometheus_port = prometheus_port
        self.metrics_retention_days = metrics_retention_days
        self.sampling_interval_seconds = sampling_interval_seconds
        self.alert_thresholds = alert_thresholds or {}

        # Initialize metrics storage
        self._metrics = {}
        self._prometheus_metrics = {}
        self._metric_data = {}
        self._metric_metadata = {}

        # Initialize system metrics
        self._system_metrics_task = None

        # Start Prometheus server if enabled
        if self.enable_prometheus:
            start_http_server(self.prometheus_port)
            logger.info(
                f"Prometheus metrics server started on port {self.prometheus_port}"
            )

        # Initialize default metrics
        self._initialize_default_metrics()

        # Mark as initialized
        self._initialized = True

        logger.info(f"Performance monitor initialized for {self.app_name}")

    def _initialize_default_metrics(self):
        """Initialize default metrics for the system."""
        # API metrics
        self.create_metric(
            name="api_request_count",
            description="Total number of API requests",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.API,
            labels=["endpoint", "method", "status"],
        )

        self.create_metric(
            name="api_request_duration_seconds",
            description="API request duration in seconds",
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.API,
            labels=["endpoint", "method"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
        )

        self.create_metric(
            name="api_request_size_bytes",
            description="API request size in bytes",
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.API,
            labels=["endpoint", "method"],
            buckets=[10, 100, 1000, 10000, 100000, 1000000],
        )

        self.create_metric(
            name="api_response_size_bytes",
            description="API response size in bytes",
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.API,
            labels=["endpoint", "method", "status"],
            buckets=[10, 100, 1000, 10000, 100000, 1000000],
        )

        self.create_metric(
            name="api_error_count",
            description="Total number of API errors",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.API,
            labels=["endpoint", "method", "error_type"],
        )

        # Database metrics
        self.create_metric(
            name="db_query_count",
            description="Total number of database queries",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.DATABASE,
            labels=["operation", "table"],
        )

        self.create_metric(
            name="db_query_duration_seconds",
            description="Database query duration in seconds",
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.DATABASE,
            labels=["operation", "table"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
        )

        self.create_metric(
            name="db_connection_pool_size",
            description="Database connection pool size",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.DATABASE,
            labels=["database"],
        )

        self.create_metric(
            name="db_connection_pool_used",
            description="Database connection pool used connections",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.DATABASE,
            labels=["database"],
        )

        # External service metrics
        self.create_metric(
            name="external_request_count",
            description="Total number of external service requests",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.EXTERNAL,
            labels=["service", "endpoint", "method", "status"],
        )

        self.create_metric(
            name="external_request_duration_seconds",
            description="External service request duration in seconds",
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.EXTERNAL,
            labels=["service", "endpoint", "method"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
        )

        self.create_metric(
            name="external_request_error_count",
            description="Total number of external service request errors",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.EXTERNAL,
            labels=["service", "endpoint", "method", "error_type"],
        )

        # System metrics
        self.create_metric(
            name="system_cpu_usage_percent",
            description="CPU usage percentage",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.SYSTEM,
        )

        self.create_metric(
            name="system_memory_usage_bytes",
            description="Memory usage in bytes",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.SYSTEM,
        )

        self.create_metric(
            name="system_memory_available_bytes",
            description="Available memory in bytes",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.SYSTEM,
        )

        self.create_metric(
            name="system_disk_usage_bytes",
            description="Disk usage in bytes",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.SYSTEM,
            labels=["device", "mountpoint"],
        )

        self.create_metric(
            name="system_disk_free_bytes",
            description="Free disk space in bytes",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.SYSTEM,
            labels=["device", "mountpoint"],
        )

        self.create_metric(
            name="system_network_bytes_sent",
            description="Network bytes sent",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.SYSTEM,
            labels=["interface"],
        )

        self.create_metric(
            name="system_network_bytes_received",
            description="Network bytes received",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.SYSTEM,
            labels=["interface"],
        )

        # Business metrics
        self.create_metric(
            name="business_active_users",
            description="Number of active users",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.BUSINESS,
        )

        self.create_metric(
            name="business_active_sessions",
            description="Number of active sessions",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.BUSINESS,
        )

        # Pipeline metrics (Amazon→eBay specific)
        self.create_metric(
            name="pipeline_amazon_to_ebay_transformations_count",
            description="Total number of Amazon to eBay transformations",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.PIPELINE,
            labels=["status"],
        )

        self.create_metric(
            name="pipeline_amazon_to_ebay_transformation_duration_seconds",
            description="Amazon to eBay transformation duration in seconds",
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.PIPELINE,
            buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
        )

        self.create_metric(
            name="pipeline_amazon_to_ebay_queue_size",
            description="Size of the Amazon to eBay transformation queue",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.PIPELINE,
        )

        self.create_metric(
            name="pipeline_amazon_to_ebay_error_count",
            description="Total number of Amazon to eBay transformation errors",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.PIPELINE,
            labels=["error_type"],
        )

        self.create_metric(
            name="pipeline_amazon_to_ebay_success_rate",
            description="Success rate of Amazon to eBay transformations",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.PIPELINE,
        )

    def create_metric(
        self,
        name: str,
        description: str,
        metric_type: MetricType,
        category: MetricCategory,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> str:
        """
        Create a new metric.

        Args:
            name: Metric name
            description: Metric description
            metric_type: Type of metric
            category: Category of metric
            labels: Labels for the metric
            buckets: Buckets for histogram metrics

        Returns:
            Metric name
        """
        # Generate full metric name
        full_name = f"{self.app_name}_{category.value}_{name}"

        # Store metric metadata
        self._metric_metadata[full_name] = {
            "name": name,
            "description": description,
            "type": metric_type,
            "category": category,
            "labels": labels or [],
            "buckets": buckets,
            "created_at": datetime.now(),
        }

        # Initialize metric data storage
        self._metric_data[full_name] = []

        # Create Prometheus metric if enabled
        if self.enable_prometheus:
            self._create_prometheus_metric(
                full_name, description, metric_type, labels, buckets
            )

        logger.debug(f"Created metric: {full_name}")
        return full_name

    def _create_prometheus_metric(
        self,
        full_name: str,
        description: str,
        metric_type: MetricType,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ):
        """
        Create a Prometheus metric.

        Args:
            full_name: Full metric name
            description: Metric description
            metric_type: Type of metric
            labels: Labels for the metric
            buckets: Buckets for histogram metrics
        """
        labels = labels or []

        if metric_type == MetricType.COUNTER:
            self._prometheus_metrics[full_name] = Counter(
                full_name, description, labels
            )
        elif metric_type == MetricType.GAUGE:
            self._prometheus_metrics[full_name] = Gauge(full_name, description, labels)
        elif metric_type == MetricType.HISTOGRAM:
            self._prometheus_metrics[full_name] = Histogram(
                full_name, description, labels, buckets=buckets
            )
        elif metric_type == MetricType.SUMMARY:
            self._prometheus_metrics[full_name] = Summary(
                full_name, description, labels
            )

    def record_metric(
        self,
        name: str,
        value: float,
        category: MetricCategory,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            category: Category of metric
            labels: Labels for the metric
        """
        # Generate full metric name
        full_name = f"{self.app_name}_{category.value}_{name}"

        # Check if metric exists
        if full_name not in self._metric_metadata:
            logger.warning(f"Metric {full_name} does not exist")
            return

        # Get metric metadata
        metadata = self._metric_metadata[full_name]
        metric_type = metadata["type"]

        # Record metric in Prometheus if enabled
        if self.enable_prometheus and full_name in self._prometheus_metrics:
            prometheus_metric = self._prometheus_metrics[full_name]

            if labels:
                if metric_type == MetricType.COUNTER:
                    prometheus_metric.labels(**labels).inc(value)
                elif metric_type == MetricType.GAUGE:
                    prometheus_metric.labels(**labels).set(value)
                elif metric_type == MetricType.HISTOGRAM:
                    prometheus_metric.labels(**labels).observe(value)
                elif metric_type == MetricType.SUMMARY:
                    prometheus_metric.labels(**labels).observe(value)
            else:
                if metric_type == MetricType.COUNTER:
                    pass
                elif metric_type == MetricType.GAUGE:
                    prometheus_metric.labels(**labels).set(value)
                elif metric_type == MetricType.HISTOGRAM:
                    prometheus_metric.labels(**labels).observe(value)
                elif metric_type == MetricType.SUMMARY:
                    prometheus_metric.labels(**labels).observe(value)
