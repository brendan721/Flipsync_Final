"""Metric types for monitoring and metrics collection."""

from enum import Enum
from typing import Any, Dict


class MetricCategory(str, Enum):
    """Categories of metrics for organizing and filtering.

    Attributes:
        PERFORMANCE: Metrics related to system performance (latency, throughput, etc.)
        RELIABILITY: Metrics related to system reliability (uptime, error rates, etc.)
        RESOURCE: Metrics related to resource utilization (CPU, memory, network, etc.)
        BUSINESS: Metrics related to business operations (transactions, revenue, etc.)
        MOBILE: Metrics specific to mobile devices (battery, network strength, etc.)
        SECURITY: Metrics related to security (auth failures, suspicious activity, etc.)
        CUSTOM: UnifiedUser-defined metric categories
    """

    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    RESOURCE = "resource"
    BUSINESS = "business"
    MOBILE = "mobile"
    SECURITY = "security"
    CUSTOM = "custom"


class MetricType(str, Enum):
    """Types of metrics that can be collected and monitored.

    Attributes:
        COUNTER: A cumulative metric that can only increase or be reset to zero
        GAUGE: A metric that can arbitrarily go up and down
        HISTOGRAM: A metric that samples observations and counts them in configurable buckets
        SUMMARY: Similar to histogram, but calculates configurable quantiles over a sliding time window
        RATE: A metric representing counts per time unit
        DELTA: A metric representing change between consecutive measurements
        UPTIME: A metric representing system availability
        LATENCY: A metric representing response time measurements
        ERROR_RATE: A metric representing the rate of errors
        RESOURCE_USAGE: A metric representing resource utilization (CPU, memory, etc.)
        THROUGHPUT: A metric representing the rate of operations/requests
        QUEUE_SIZE: A metric representing the size of a queue or buffer
        BATTERY_LEVEL: A metric specifically for mobile battery monitoring
        NETWORK_USAGE: A metric for network bandwidth consumption
        TASK: Task execution metrics
        STORAGE: Storage usage and performance metrics
        CUSTOM: A user-defined metric type
    """

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    RATE = "rate"
    DELTA = "delta"
    UPTIME = "uptime"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    THROUGHPUT = "throughput"
    QUEUE_SIZE = "queue_size"
    BATTERY_LEVEL = "battery_level"
    NETWORK_USAGE = "network_usage"
    TASK = "task"
    STORAGE = "storage"
    CUSTOM = "custom"

    @classmethod
    def get_default_config(cls, metric_type: "MetricType") -> Dict[str, Any]:
        """Get default configuration for a metric type.

        Args:
            metric_type: The type of metric to get configuration for

        Returns:
            Dictionary containing default configuration values
        """
        configs: Dict[MetricType, Dict[str, Any]] = {
            cls.COUNTER: {"aggregation": "sum", "reset_on_read": False},
            cls.GAUGE: {"aggregation": "last", "ttl": 300},  # 5 minutes
            cls.HISTOGRAM: {
                "buckets": [0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                "max_size": 10000,
            },
            cls.SUMMARY: {
                "quantiles": [0.5, 0.9, 0.95, 0.99],
                "window": 300,  # 5 minutes
            },
            cls.RATE: {"interval": 60, "mode": "exponential"},  # 1 minute
            cls.DELTA: {"compare_window": 300},  # 5 minutes
            cls.UPTIME: {
                "interval": 60,  # 1 minute
                "threshold": 0.999,  # 99.9% uptime target
            },
            cls.LATENCY: {"buckets": [0.01, 0.05, 0.1, 0.5, 1.0], "apdex_target": 0.5},
            cls.ERROR_RATE: {
                "window": 300,  # 5 minutes
                "threshold": 0.01,  # 1% error rate threshold
            },
            cls.RESOURCE_USAGE: {
                "warning_threshold": 0.75,  # 75%
                "critical_threshold": 0.9,  # 90%
            },
            cls.THROUGHPUT: {"interval": 60, "max_sustainable": 1000},  # 1 minute
            cls.QUEUE_SIZE: {"warning_threshold": 1000, "critical_threshold": 5000},
            cls.BATTERY_LEVEL: {
                "warning_threshold": 0.2,  # 20%
                "critical_threshold": 0.1,  # 10%
            },
            cls.NETWORK_USAGE: {
                "warning_threshold": 0.75,  # 75%
                "critical_threshold": 0.9,  # 90%
            },
            cls.TASK: {},
            cls.STORAGE: {
                "warning_threshold": 0.85,  # 85% storage usage
                "critical_threshold": 0.95,  # 95% storage usage
                "min_free_space": 1024 * 1024 * 100,  # 100MB minimum free space
            },
            cls.CUSTOM: {},
        }
        return configs.get(metric_type, {})
