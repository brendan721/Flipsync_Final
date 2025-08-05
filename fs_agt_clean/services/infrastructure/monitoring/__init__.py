"""
Monitoring package for FlipSync.

This package provides monitoring capabilities for the FlipSync system, including
metrics collection, logging, and health checks.

Main components:
- UnifiedAgent Monitor: Tracks agent metrics, events, and health status
- Alert System: Manages alert conditions and notifications
- Visualization: Generates dashboards and charts for monitoring data
- Monitoring Service: Central service that integrates all components
"""

# Import key components for easier access
# Note: Core monitoring modules not yet migrated - commenting out for now
# from fs_agt_clean.core.monitoring.agent_monitor import (
#     UnifiedAgentEvent,
#     UnifiedAgentHealthStatus,
#     UnifiedAgentMetric,
#     UnifiedAgentMonitor,
#     UnifiedAgentMonitoringMixin,
# )
# from fs_agt_clean.core.monitoring.alert_system import (
#     AlertCondition,
#     AlertManager,
#     EventAlertCondition,
#     HealthStatusAlertCondition,
# )
# from fs_agt_clean.core.monitoring.monitoring_service import (
#     MonitoringService,
#     get_monitoring_service,
# )
# from fs_agt_clean.core.monitoring.visualization import MonitoringDashboard


# Define a metrics mixin for components that need to report metrics
class MetricsMixin:
    """
    Mixin class for components that need to report metrics.

    This mixin provides methods for recording metrics and events
    that can be used by any component in the system.
    """

    def __init__(self, component_name: str = None):
        """
        Initialize the metrics mixin.

        Args:
            component_name: The name of the component using this mixin
        """
        self._component_name = component_name or self.__class__.__name__
        self._metrics = {}

    def record_metric(self, name: str, value: float, tags: dict = None):
        """
        Record a metric value.

        Args:
            name: The name of the metric
            value: The value of the metric
            tags: Optional tags to associate with the metric
        """
        if tags is None:
            tags = {}

        tags["component"] = self._component_name

        # Store the metric locally
        self._metrics[name] = {"value": value, "tags": tags}

        # If monitoring service is available, report the metric
        # Note: Monitoring service not yet migrated - skipping for now
        # try:
        #     from fs_agt_clean.core.monitoring.monitoring_service import get_monitoring_service
        #     monitoring_service = get_monitoring_service()
        #     if monitoring_service:
        #         monitoring_service.record_metric(name, value, tags)
        # except Exception:
        #     # Silently ignore errors in metric reporting
        #     pass

    def record_event(self, name: str, data: dict = None):
        """
        Record an event.

        Args:
            name: The name of the event
            data: Optional data to associate with the event
        """
        if data is None:
            data = {}

        data["component"] = self._component_name

        # If monitoring service is available, report the event
        # Note: Monitoring service not yet migrated - skipping for now
        # try:
        #     from fs_agt_clean.core.monitoring.monitoring_service import get_monitoring_service
        #     monitoring_service = get_monitoring_service()
        #     if monitoring_service:
        #         monitoring_service.record_event(name, data)
        # except Exception:
        #     # Silently ignore errors in event reporting
        #     pass


# Define the public API
__all__ = [
    # Metrics Mixin (only available component for now)
    "MetricsMixin",
    # Note: Other monitoring components not yet migrated
]
