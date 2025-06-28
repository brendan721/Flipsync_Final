"""
Production monitoring and alerting system for FlipSync.
Implements comprehensive monitoring, error tracking, and performance metrics.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure."""

    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class MetricThreshold:
    """Metric threshold configuration."""

    warning: float
    error: float
    critical: float
    unit: str = ""
    description: str = ""


class SystemMetricsCollector:
    """Collect system-level metrics."""

    def __init__(self):
        self.process = psutil.Process()

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()
            process_memory = self.process.memory_info()

            # Disk metrics
            disk = psutil.disk_usage("/")

            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_stats = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                }
            except:
                network_stats = {}

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg": (
                        list(psutil.getloadavg())
                        if hasattr(psutil, "getloadavg")
                        else []
                    ),
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "process_rss": process_memory.rss,
                    "process_vms": process_memory.vms,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                },
                "network": network_stats,
            }

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


class ApplicationMetricsCollector:
    """Collect application-specific metrics."""

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=1000)
        self.endpoint_stats = defaultdict(
            lambda: {"count": 0, "errors": 0, "total_time": 0}
        )
        self.active_connections = 0

    def record_request(self, endpoint: str, response_time_ms: float, status_code: int):
        """Record request metrics."""
        self.request_count += 1
        self.response_times.append(response_time_ms)

        stats = self.endpoint_stats[endpoint]
        stats["count"] += 1
        stats["total_time"] += response_time_ms

        if status_code >= 400:
            self.error_count += 1
            stats["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current application metrics."""
        if not self.response_times:
            avg_response_time = 0
            p95_response_time = 0
        else:
            times = sorted(list(self.response_times))
            avg_response_time = sum(times) / len(times)
            p95_index = int(len(times) * 0.95)
            p95_response_time = (
                times[p95_index] if p95_index < len(times) else times[-1]
            )

        error_rate = (self.error_count / max(self.request_count, 1)) * 100

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "requests": {
                "total": self.request_count,
                "errors": self.error_count,
                "error_rate_percent": error_rate,
            },
            "response_times": {
                "avg_ms": avg_response_time,
                "p95_ms": p95_response_time,
                "count": len(self.response_times),
            },
            "connections": {"active": self.active_connections},
            "endpoints": dict(self.endpoint_stats),
        }


class ProductionMonitor:
    """Main production monitoring system."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

        # Metrics collectors
        self.system_collector = SystemMetricsCollector()
        self.app_collector = ApplicationMetricsCollector()

        # Alert management
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.thresholds = self._setup_thresholds()

        # Monitoring state
        self.is_monitoring = False
        self.last_check = datetime.utcnow()

        # Metrics history
        self.metrics_history = deque(maxlen=1000)

    def _default_config(self) -> Dict[str, Any]:
        """Default monitoring configuration."""
        return {
            "check_interval": 60,  # seconds
            "metrics_retention": 24,  # hours
            "alert_cooldown": 300,  # seconds
            "enable_system_monitoring": True,
            "enable_app_monitoring": True,
            "enable_alerting": True,
        }

    def _setup_thresholds(self) -> Dict[str, MetricThreshold]:
        """Setup metric thresholds for alerting."""
        return {
            "cpu_percent": MetricThreshold(70.0, 85.0, 95.0, "%", "CPU usage"),
            "memory_percent": MetricThreshold(70.0, 85.0, 95.0, "%", "Memory usage"),
            "disk_percent": MetricThreshold(80.0, 90.0, 95.0, "%", "Disk usage"),
            "error_rate": MetricThreshold(5.0, 10.0, 20.0, "%", "Error rate"),
            "avg_response_time": MetricThreshold(
                200.0, 500.0, 1000.0, "ms", "Average response time"
            ),
            "p95_response_time": MetricThreshold(
                500.0, 1000.0, 2000.0, "ms", "95th percentile response time"
            ),
        }

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add alert handler function."""
        self.alert_handlers.append(handler)

    def _trigger_alert(
        self,
        alert_id: str,
        level: AlertLevel,
        title: str,
        message: str,
        source: str = "monitor",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Trigger an alert."""
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            source=source,
            metadata=metadata or {},
            resolved=False,
        )

        self.alerts.append(alert)

        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

        logger.warning(f"ALERT [{level.value.upper()}] {title}: {message}")

    def _check_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and trigger alerts."""
        if not self.config.get("enable_alerting", True):
            return

        # Check system metrics
        if "cpu" in metrics and "percent" in metrics["cpu"]:
            cpu_percent = metrics["cpu"]["percent"]
            threshold = self.thresholds["cpu_percent"]

            if cpu_percent >= threshold.critical:
                self._trigger_alert(
                    "high_cpu_critical",
                    AlertLevel.CRITICAL,
                    "Critical CPU Usage",
                    f"CPU usage is {cpu_percent:.1f}% (threshold: {threshold.critical}%)",
                    metadata={"cpu_percent": cpu_percent},
                )
            elif cpu_percent >= threshold.error:
                self._trigger_alert(
                    "high_cpu_error",
                    AlertLevel.ERROR,
                    "High CPU Usage",
                    f"CPU usage is {cpu_percent:.1f}% (threshold: {threshold.error}%)",
                    metadata={"cpu_percent": cpu_percent},
                )

        # Check memory metrics
        if "memory" in metrics and "percent" in metrics["memory"]:
            memory_percent = metrics["memory"]["percent"]
            threshold = self.thresholds["memory_percent"]

            if memory_percent >= threshold.critical:
                self._trigger_alert(
                    "high_memory_critical",
                    AlertLevel.CRITICAL,
                    "Critical Memory Usage",
                    f"Memory usage is {memory_percent:.1f}% (threshold: {threshold.critical}%)",
                    metadata={"memory_percent": memory_percent},
                )

        # Check application metrics
        if "requests" in metrics and "error_rate_percent" in metrics["requests"]:
            error_rate = metrics["requests"]["error_rate_percent"]
            threshold = self.thresholds["error_rate"]

            if error_rate >= threshold.error:
                self._trigger_alert(
                    "high_error_rate",
                    AlertLevel.ERROR,
                    "High Error Rate",
                    f"Error rate is {error_rate:.1f}% (threshold: {threshold.error}%)",
                    metadata={"error_rate": error_rate},
                )

    async def start_monitoring(self):
        """Start the monitoring loop."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        logger.info("Starting production monitoring")

        while self.is_monitoring:
            try:
                await self._monitoring_cycle()
                await asyncio.sleep(self.config["check_interval"])
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(5)  # Short delay before retry

    async def _monitoring_cycle(self):
        """Single monitoring cycle."""
        # Collect metrics
        metrics = {}

        if self.config.get("enable_system_monitoring", True):
            system_metrics = self.system_collector.collect_metrics()
            metrics.update(system_metrics)

        if self.config.get("enable_app_monitoring", True):
            app_metrics = self.app_collector.get_metrics()
            metrics["application"] = app_metrics

        # Store metrics
        self.metrics_history.append(metrics)

        # Check thresholds
        combined_metrics = {**metrics}
        if "application" in metrics:
            combined_metrics.update(metrics["application"])

        self._check_thresholds(combined_metrics)

        self.last_check = datetime.utcnow()

    def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.is_monitoring = False
        logger.info("Stopped production monitoring")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        recent_metrics = (
            list(self.metrics_history)[-10:] if self.metrics_history else []
        )
        active_alerts = [alert for alert in self.alerts if not alert.resolved]

        return {
            "status": "monitoring" if self.is_monitoring else "stopped",
            "last_check": self.last_check.isoformat(),
            "recent_metrics": recent_metrics,
            "active_alerts": [asdict(alert) for alert in active_alerts],
            "alert_count": len(active_alerts),
            "total_alerts": len(self.alerts),
            "thresholds": {k: asdict(v) for k, v in self.thresholds.items()},
        }

    def record_request(self, endpoint: str, response_time_ms: float, status_code: int):
        """Record request for application monitoring."""
        self.app_collector.record_request(endpoint, response_time_ms, status_code)


# Global monitor instance
production_monitor = ProductionMonitor()


# Alert handler examples
def log_alert_handler(alert: Alert):
    """Log alert to file."""
    logger.critical(f"ALERT: {alert.title} - {alert.message}")


def console_alert_handler(alert: Alert):
    """Print alert to console."""
    print(f"🚨 [{alert.level.value.upper()}] {alert.title}: {alert.message}")


# Setup default handlers
production_monitor.add_alert_handler(log_alert_handler)
production_monitor.add_alert_handler(console_alert_handler)
