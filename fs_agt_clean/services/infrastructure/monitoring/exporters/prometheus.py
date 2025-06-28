"""Prometheus metrics exporter for monitoring."""

import logging
from typing import Dict, List, Optional

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

# Create a custom registry
registry = CollectorRegistry()

# Define metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    registry=registry,
)

ERROR_COUNT = Counter(
    "error_total",
    "Total count of errors",
    ["type", "location"],
    registry=registry,
)

API_ERROR_COUNT = Counter(
    "api_error_total",
    "Total count of API errors",
    ["endpoint", "error_type"],
    registry=registry,
)

SERVICE_STATUS = Gauge(
    "service_status",
    "Status of services (1=up, 0=down)",
    ["service"],
    registry=registry,
)

# Set initial values for service status
SERVICE_STATUS.labels(service="api").set(1)
SERVICE_STATUS.labels(service="database").set(1)
SERVICE_STATUS.labels(service="redis").set(1)

logger = logging.getLogger(__name__)
