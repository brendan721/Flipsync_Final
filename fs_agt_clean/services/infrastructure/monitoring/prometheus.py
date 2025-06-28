"""
Prometheus Metrics Handler for FlipSync

This module provides a wrapper for Prometheus metrics to track various aspects of the system
performance and operations.
"""

import logging
from typing import Dict, List, Optional, Union

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Summary,
        push_to_gateway,
        start_http_server,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Create dummy classes for type checking
    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, value=1):
            pass

        def labels(self, **kwargs):
            return self

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def set(self, value):
            pass

        def inc(self, value=1):
            pass

        def dec(self, value=1):
            pass

        def labels(self, **kwargs):
            return self

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, value):
            pass

        def labels(self, **kwargs):
            return self

    class Summary:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, value):
            pass

        def labels(self, **kwargs):
            return self


logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Prometheus metrics handler for FlipSync."""

    def __init__(self, namespace: str = "flipsync", subsystem: str = ""):
        """Initialize Prometheus metrics.

        Args:
            namespace: Metrics namespace (default: flipsync)
            subsystem: Metrics subsystem (optional)
        """
        self.namespace = namespace
        self.subsystem = subsystem
        self.metrics = {}

        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available. Metrics will be disabled.")

    def register_counter(
        self, name: str, description: str, labels: Optional[List[str]] = None
    ) -> None:
        """Register a counter metric.

        Args:
            name: Counter name
            description: Counter description
            labels: Optional list of label names
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics[name] = Counter(
                name=name,
                documentation=description,
                labelnames=labels or [],
                namespace=self.namespace,
                subsystem=self.subsystem,
            )
            logger.debug(f"Registered counter metric: {name}")
        except Exception as e:
            logger.error(f"Failed to register counter metric {name}: {e}")

    def register_gauge(
        self, name: str, description: str, labels: Optional[List[str]] = None
    ) -> None:
        """Register a gauge metric.

        Args:
            name: Gauge name
            description: Gauge description
            labels: Optional list of label names
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics[name] = Gauge(
                name=name,
                documentation=description,
                labelnames=labels or [],
                namespace=self.namespace,
                subsystem=self.subsystem,
            )
            logger.debug(f"Registered gauge metric: {name}")
        except Exception as e:
            logger.error(f"Failed to register gauge metric {name}: {e}")

    def register_histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> None:
        """Register a histogram metric.

        Args:
            name: Histogram name
            description: Histogram description
            labels: Optional list of label names
            buckets: Optional list of histogram buckets
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            kwargs = {
                "name": name,
                "documentation": description,
                "labelnames": labels or [],
                "namespace": self.namespace,
                "subsystem": self.subsystem,
            }

            if buckets:
                kwargs["buckets"] = buckets

            self.metrics[name] = Histogram(**kwargs)
            logger.debug(f"Registered histogram metric: {name}")
        except Exception as e:
            logger.error(f"Failed to register histogram metric {name}: {e}")

    def register_summary(
        self, name: str, description: str, labels: Optional[List[str]] = None
    ) -> None:
        """Register a summary metric.

        Args:
            name: Summary name
            description: Summary description
            labels: Optional list of label names
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.metrics[name] = Summary(
                name=name,
                documentation=description,
                labelnames=labels or [],
                namespace=self.namespace,
                subsystem=self.subsystem,
            )
            logger.debug(f"Registered summary metric: {name}")
        except Exception as e:
            logger.error(f"Failed to register summary metric {name}: {e}")

    def increment_counter(
        self, name: str, labels: Optional[Dict[str, str]] = None, value: float = 1
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name
            labels: Optional dictionary of label values
            value: Value to increment by (default: 1)
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Metric {name} not registered")
                return

            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)

            logger.debug(f"Incremented counter {name} by {value}")
        except Exception as e:
            logger.error(f"Failed to increment counter {name}: {e}")

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric.

        Args:
            name: Gauge name
            value: Value to set
            labels: Optional dictionary of label values
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Metric {name} not registered")
                return

            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)

            logger.debug(f"Set gauge {name} to {value}")
        except Exception as e:
            logger.error(f"Failed to set gauge {name}: {e}")

    def increment_gauge(
        self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a gauge metric.

        Args:
            name: Gauge name
            value: Value to increment by (default: 1)
            labels: Optional dictionary of label values
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Metric {name} not registered")
                return

            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)

            logger.debug(f"Incremented gauge {name} by {value}")
        except Exception as e:
            logger.error(f"Failed to increment gauge {name}: {e}")

    def decrement_gauge(
        self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Decrement a gauge metric.

        Args:
            name: Gauge name
            value: Value to decrement by (default: 1)
            labels: Optional dictionary of label values
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Metric {name} not registered")
                return

            if labels:
                metric.labels(**labels).dec(value)
            else:
                metric.dec(value)

            logger.debug(f"Decremented gauge {name} by {value}")
        except Exception as e:
            logger.error(f"Failed to decrement gauge {name}: {e}")

    def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Observe a histogram metric.

        Args:
            name: Histogram name
            value: Value to observe
            labels: Optional dictionary of label values
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Metric {name} not registered")
                return

            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

            logger.debug(f"Observed histogram {name} value {value}")
        except Exception as e:
            logger.error(f"Failed to observe histogram {name}: {e}")

    def observe_summary(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Observe a summary metric.

        Args:
            name: Summary name
            value: Value to observe
            labels: Optional dictionary of label values
        """
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            metric = self.metrics.get(name)
            if not metric:
                logger.warning(f"Metric {name} not registered")
                return

            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)

            logger.debug(f"Observed summary {name} value {value}")
        except Exception as e:
            logger.error(f"Failed to observe summary {name}: {e}")

    def start_http_server(self, port: int = 8000, addr: str = "") -> None:
        """Start HTTP server to expose metrics.

        Args:
            port: Port to listen on (default: 8000)
            addr: Address to bind to (default: all interfaces)
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available. Cannot start HTTP server.")
            return

        try:
            start_http_server(port, addr)
            logger.info(f"Started Prometheus metrics HTTP server on port {port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus metrics HTTP server: {e}")

    def push_to_gateway(self, gateway: str, job: str, registry=None) -> None:
        """Push metrics to a Prometheus Pushgateway.

        Args:
            gateway: Pushgateway address (host:port)
            job: Job label to be attached to the metrics
            registry: Registry to get metrics from (optional)
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available. Cannot push to gateway.")
            return

        try:
            push_to_gateway(gateway, job, registry)
            logger.info(f"Pushed metrics to Prometheus Pushgateway at {gateway}")
        except Exception as e:
            logger.error(f"Failed to push metrics to Prometheus Pushgateway: {e}")

    def get_metric(self, name: str) -> Union[Counter, Gauge, Histogram, Summary, None]:
        """Get a metric by name.

        Args:
            name: Metric name

        Returns:
            Metric object or None if not found
        """
        return self.metrics.get(name)
