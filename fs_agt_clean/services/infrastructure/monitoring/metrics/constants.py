"""Metrics constants."""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

# Create a custom registry for our metrics
registry = CollectorRegistry()

# ML Service Metrics
ML_REQUEST_LATENCY = Histogram(
    "ml_request_duration_seconds",
    "ML request processing duration",
    ["model", "operation_type"],
    registry=registry,
)

ML_MODEL_LOAD_TIME = Histogram(
    "ml_model_load_duration_seconds",
    "Model loading duration",
    ["model"],
    registry=registry,
)

ML_MEMORY_USAGE = Gauge(
    "ml_memory_usage_bytes",
    "ML service memory usage",
    ["model"],
    registry=registry,
)

ML_REQUEST_RATE = Counter(
    "ml_requests_total",
    "Total ML service requests",
    ["model", "operation_type", "status"],
    registry=registry,
)

ML_ERROR_RATE = Counter(
    "ml_errors_total",
    "Total ML service errors",
    ["model", "error_type"],
    registry=registry,
)

ML_MODEL_CACHE_HITS = Counter(
    "ml_model_cache_hits_total",
    "Model cache hit count",
    ["model"],
    registry=registry,
)

ML_MODEL_CACHE_MISSES = Counter(
    "ml_model_cache_misses_total",
    "Model cache miss count",
    ["model"],
    registry=registry,
)

ML_BATCH_SIZE = Histogram(
    "ml_batch_size",
    "ML request batch size",
    ["model", "operation_type"],
    registry=registry,
)

# ASIN Finder metrics
ASIN_REQUEST_COUNT = Counter(
    "asin_requests_total",
    "Total number of ASIN lookup requests",
    ["endpoint", "client_id"],
    registry=registry,
)
ASIN_ERROR_COUNT = Counter(
    "asin_errors_total",
    "Total number of ASIN lookup errors",
    ["endpoint", "error_type", "client_id"],
    registry=registry,
)
ASIN_SYNC_DURATION = Histogram(
    "asin_sync_duration_seconds",
    "Duration of ASIN synchronization",
    ["source", "status"],
    registry=registry,
)
ASIN_SYNC_IN_PROGRESS = Gauge(
    "asin_sync_in_progress",
    "Number of ASIN synchronizations currently in progress",
    ["source"],
    registry=registry,
)
ACTIVE_SYNCS = Gauge(
    "active_syncs",
    "Number of active synchronization tasks",
    ["type", "status"],
    registry=registry,
)
ASIN_SYNC_SUCCESS = Counter(
    "asin_sync_success_total",
    "Total number of successful ASIN synchronizations",
    ["source"],
    registry=registry,
)
SYNC_SUCCESS = Counter(
    "sync_success_total",
    "Total number of successful synchronizations",
    ["source"],
    registry=registry,
)
SYNC_ERRORS = Counter(
    "sync_errors_total",
    "Total number of synchronization errors",
    ["source"],
    registry=registry,
)

# API metrics
API_REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["endpoint", "method", "client_id"],
    registry=registry,
)
API_ERROR_COUNT = Counter(
    "api_errors_total",
    "Total number of API errors",
    ["endpoint", "error_type", "client_id"],
    registry=registry,
)
API_REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "Duration of API requests",
    ["endpoint", "method"],
    registry=registry,
)

# Service metrics
SERVICE_HEALTH = Gauge(
    "service_health",
    "Health status of services",
    ["service_name"],
    registry=registry,
)
SERVICE_UPTIME = Counter(
    "service_uptime_seconds_total",
    "Total uptime of services",
    ["service_name"],
    registry=registry,
)

# Resource metrics
RESOURCE_USAGE = Gauge(
    "resource_usage",
    "Resource usage metrics",
    ["resource_type", "instance"],
    registry=registry,
)
RESOURCE_LIMIT = Gauge(
    "resource_limit",
    "Resource limits",
    ["resource_type", "instance"],
    registry=registry,
)

# System metrics
CPU_USAGE = Gauge("system_cpu_usage", "CPU usage percentage", registry=registry)
MEMORY_USAGE = Gauge("system_memory_usage", "Memory usage in bytes", registry=registry)
DISK_USAGE = Gauge("system_disk_usage", "Disk usage in bytes", registry=registry)
NETWORK_IN = Counter(
    "system_network_in", "Network inbound traffic in bytes", registry=registry
)
NETWORK_OUT = Counter(
    "system_network_out", "Network outbound traffic in bytes", registry=registry
)

# Application metrics
REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    ["endpoint", "method"],
    registry=registry,
)
REQUEST_COUNT = Counter(
    "request_total",
    "Total number of requests",
    ["endpoint", "method", "status"],
    registry=registry,
)
ERROR_COUNT = Counter(
    "error_total", "Total number of errors", ["type", "source"], registry=registry
)

# ASIN sync metrics
ASIN_SYNC_ERRORS = Counter(
    "asin_sync_errors_total",
    "Total number of ASIN sync errors",
    ["type", "source"],
    registry=registry,
)

# Export the registry and metrics
__all__ = [
    "registry",
    "ASIN_REQUEST_COUNT",
    "ASIN_ERROR_COUNT",
    "ASIN_SYNC_DURATION",
    "ASIN_SYNC_IN_PROGRESS",
    "ACTIVE_SYNCS",
    "ASIN_SYNC_SUCCESS",
    "SYNC_SUCCESS",
    "SYNC_ERRORS",
    "API_REQUEST_COUNT",
    "API_ERROR_COUNT",
    "API_REQUEST_DURATION",
    "SERVICE_HEALTH",
    "SERVICE_UPTIME",
    "RESOURCE_USAGE",
    "RESOURCE_LIMIT",
    "CPU_USAGE",
    "MEMORY_USAGE",
    "DISK_USAGE",
    "NETWORK_IN",
    "NETWORK_OUT",
    "REQUEST_LATENCY",
    "REQUEST_COUNT",
    "ERROR_COUNT",
    "ASIN_SYNC_ERRORS",
    "ML_REQUEST_LATENCY",
    "ML_MODEL_LOAD_TIME",
    "ML_MEMORY_USAGE",
    "ML_REQUEST_RATE",
    "ML_ERROR_RATE",
    "ML_MODEL_CACHE_HITS",
    "ML_MODEL_CACHE_MISSES",
    "ML_BATCH_SIZE",
]
