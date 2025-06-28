"""monitoring module."""

from .alerts.alert_manager import AlertCategory, AlertLevel, AlertManager, AlertSource
from .logger import configure_logging, get_log_manager, get_logger
from .metrics.collector import MetricsCollector

# Cost tracking and quality monitoring
from .cost_tracker import (
    CostTracker,
    CostCategory,
    CostEntry,
    BudgetAlert,
    get_cost_tracker,
    record_ai_cost,
)

from .quality_monitor import (
    QualityMonitor,
    QualityMetric,
    QualityEntry,
    get_quality_monitor,
)

# Create global instances
_metrics_collector = None
_alert_manager = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


async def record_metric(name: str, value: float, **kwargs):
    """Record a metric using the global metrics collector."""
    collector = get_metrics_collector()
    await collector.record_metric(name, value, **kwargs)


async def create_alert(title: str, message: str, **kwargs):
    """Create an alert using the global alert manager."""
    manager = get_alert_manager()
    return await manager.create_alert(title, message, **kwargs)


__all__ = [
    "get_logger",
    "get_log_manager",
    "configure_logging",
    "record_metric",
    "get_metrics_collector",
    "create_alert",
    "get_alert_manager",
    "AlertLevel",
    "AlertCategory",
    "AlertSource",
]
