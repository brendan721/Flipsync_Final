"""Prometheus metrics exporter for FlipSync monitoring."""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

# Create a custom registry for FlipSync metrics
registry = CollectorRegistry()

# Request metrics
REQUEST_COUNT = Counter(
    "flipsync_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

REQUEST_LATENCY = Histogram(
    "flipsync_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    registry=registry,
)

# Error metrics
ERROR_COUNT = Counter(
    "flipsync_errors_total",
    "Total number of errors",
    ["type", "location"],
    registry=registry,
)

API_ERROR_COUNT = Counter(
    "flipsync_api_errors_total",
    "Total number of API errors",
    ["endpoint", "error_type"],
    registry=registry,
)

# Service status metrics
SERVICE_STATUS = Gauge(
    "flipsync_service_status",
    "Service status (1=up, 0=down)",
    ["service"],
    registry=registry,
)

# Additional FlipSync-specific metrics
AGENT_STATUS = Gauge(
    "flipsync_agent_status",
    "UnifiedAgent status (1=active, 0=inactive)",
    ["agent_id", "agent_type"],
    registry=registry,
)

MARKETPLACE_OPERATIONS = Counter(
    "flipsync_marketplace_operations_total",
    "Total marketplace operations",
    ["marketplace", "operation_type", "status"],
    registry=registry,
)

INVENTORY_ITEMS = Gauge(
    "flipsync_inventory_items_total",
    "Total number of inventory items",
    ["status"],
    registry=registry,
)

DATABASE_CONNECTIONS = Gauge(
    "flipsync_database_connections",
    "Number of database connections",
    ["status"],
    registry=registry,
)

REDIS_OPERATIONS = Counter(
    "flipsync_redis_operations_total",
    "Total Redis operations",
    ["operation", "status"],
    registry=registry,
)

VECTOR_STORE_OPERATIONS = Counter(
    "flipsync_vector_store_operations_total",
    "Total vector store operations",
    ["operation", "status"],
    registry=registry,
)

# Initialize service status
SERVICE_STATUS.labels(service="flipsync").set(0)
