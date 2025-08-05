"""
FlipSync UnifiedAgent Monitoring Service

This module provides a centralized monitoring service that integrates all monitoring components:
- UnifiedAgent Monitor
- Alert System
- Visualization

It serves as the main entry point for monitoring and alerting functionality.
"""

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

# Import monitoring components
from fs_agt_clean.core.monitoring.agent_monitor import UnifiedAgentEvent, UnifiedAgentMonitor
from fs_agt_clean.core.monitoring.alert_system import (
    AlertManager,
    EmailAlertNotifier,
    WebhookAlertNotifier,
)
from fs_agt_clean.core.monitoring.visualization import MonitoringDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("monitoring_service.log"), logging.StreamHandler()],
)
logger = logging.getLogger("monitoring_service")


class MonitoringService:
    """Central service that integrates all monitoring components."""

    def __init__(
        self,
        base_dir: str = "./monitoring",
        dashboard_refresh_interval: int = 300,  # 5 minutes
        alert_check_interval: int = 60,
    ):  # 1 minute

        # Create base directory
        os.makedirs(base_dir, exist_ok=True)

        # Initialize components
        self.monitor = UnifiedAgentMonitor(output_dir=f"{base_dir}/data")
        self.alert_manager = AlertManager(output_dir=f"{base_dir}/alerts")
        self.dashboard = MonitoringDashboard(
            monitor=self.monitor, output_dir=f"{base_dir}/dashboards"
        )

        # Set up intervals
        self.dashboard_refresh_interval = dashboard_refresh_interval
        self.alert_check_interval = alert_check_interval

        # Background services
        self.services_running = False
        self.refresh_thread = None
        self.alert_thread = None

        # Create default alert conditions
        self.alert_manager.create_default_config()

        logger.info("Monitoring service initialized")

    def start(self) -> None:
        """Start all monitoring services."""
        if self.services_running:
            return

        self.services_running = True

        # Start dashboard refresh service
        self.refresh_thread = threading.Thread(target=self._dashboard_refresh_service)
        self.refresh_thread.daemon = True
        self.refresh_thread.start()

        # Start alert checking service
        self.alert_thread = threading.Thread(target=self._alert_checking_service)
        self.alert_thread.daemon = True
        self.alert_thread.start()

        logger.info("Monitoring services started")

    def stop(self) -> None:
        """Stop all monitoring services."""
        self.services_running = False

        # Let threads finish
        if self.refresh_thread:
            self.refresh_thread.join(timeout=10.0)

        if self.alert_thread:
            self.alert_thread.join(timeout=10.0)

        logger.info("Monitoring services stopped")

    def register_agent(self, agent_id: str) -> None:
        """Register a new agent for monitoring."""
        self.monitor.register_agent(agent_id)

    def record_metric(self, agent_id: str, metric_name: str, value: Any) -> None:
        """Record a metric for an agent."""
        # Record in monitor
        self.monitor.record_metric(metric_name, value, agent_id)

        # Check for alerts
        self.alert_manager.check_metric(agent_id, metric_name, value)

    def record_event(
        self,
        agent_id: str,
        event_type: str,
        message: str,
        level: str = UnifiedAgentEvent.LEVEL_INFO,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an event for an agent."""
        # Record in monitor
        self.monitor.record_event(event_type, message, agent_id, level, details)

        # Check for alerts
        self.alert_manager.check_event(agent_id, event_type, level, details or {})

    def update_health_status(
        self,
        agent_id: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update the health status of an agent."""
        # Update in monitor
        self.monitor.update_health_status(agent_id, status, details)

        # Check for alerts
        self.alert_manager.check_health_status(agent_id, status, details or {})

    def get_agent_metrics(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all metrics for an agent."""
        return self.monitor.get_metrics(agent_id)

    def get_agent_events(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all events for an agent."""
        return self.monitor.get_events(agent_id)

    def get_agent_health_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the current health status for an agent."""
        return self.monitor.get_health_status(agent_id)

    def get_active_alerts(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active alerts, optionally filtered by agent."""
        if agent_id is None:
            return self.alert_manager.get_active_alerts()
        return self.alert_manager.get_active_alerts(agent_id=agent_id)

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        return self.alert_manager.resolve_alert(alert_id)

    def generate_agent_dashboard(self, agent_id: str, hours: int = 24) -> str:
        """Generate a dashboard for a specific agent."""
        return self.dashboard.generate_agent_dashboard(agent_id, hours)

    def generate_system_dashboard(self, hours: int = 24) -> str:
        """Generate a system-wide dashboard."""
        return self.dashboard.generate_system_dashboard(hours)

    def add_email_alert_notifier(
        self,
        name: str,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True,
    ) -> None:
        """Add an email alert notifier."""
        notifier = EmailAlertNotifier(
            name=name,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            from_email=from_email,
            to_emails=to_emails,
            use_tls=use_tls,
        )
        self.alert_manager.add_notifier(notifier)
        logger.info(f"Added email alert notifier: {name}")

    def add_webhook_alert_notifier(
        self,
        name: str,
        webhook_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 10,
    ) -> None:
        """Add a webhook alert notifier."""
        notifier = WebhookAlertNotifier(
            name=name,
            webhook_url=webhook_url,
            headers=headers or {},
            timeout_seconds=timeout_seconds,
        )
        self.alert_manager.add_notifier(notifier)
        logger.info(f"Added webhook alert notifier: {name}")

    def start_resource_monitoring(self, agent_id: str, interval: float = 5.0) -> None:
        """Start monitoring system resources for an agent."""
        self.monitor.start_resource_monitoring(agent_id, interval)

    def generate_agent_report(self, agent_id: str) -> Dict[str, Any]:
        """Generate a comprehensive report for an agent."""
        return self.monitor.generate_report(agent_id)

    def _dashboard_refresh_service(self) -> None:
        """Background service to refresh dashboards periodically."""
        next_refresh = time.time()

        while self.services_running:
            current_time = time.time()

            if current_time >= next_refresh:
                try:
                    # Generate system dashboard
                    self.dashboard.generate_system_dashboard()

                    # Get all agent IDs
                    agent_ids = set()

                    # Add agents from metrics
                    for agent_id in self.monitor.metrics.keys():
                        agent_ids.add(agent_id)

                    # Add agents from events
                    for agent_id in self.monitor.events.keys():
                        agent_ids.add(agent_id)

                    # Add agents from health status
                    for agent_id in self.monitor.health_status.keys():
                        agent_ids.add(agent_id)

                    # Generate dashboards for each agent
                    for agent_id in agent_ids:
                        self.dashboard.generate_agent_dashboard(agent_id)

                    logger.info("Dashboards refreshed")

                except Exception as e:
                    logger.error(f"Error refreshing dashboards: {str(e)}")

                # Set next refresh time
                next_refresh = current_time + self.dashboard_refresh_interval

            # Sleep for a short time
            time.sleep(1.0)

    def _alert_checking_service(self) -> None:
        """Background service to check for alerts periodically."""
        last_check = time.time()

        while self.services_running:
            current_time = time.time()

            if current_time - last_check >= self.alert_check_interval:
                try:
                    # For each agent, check resource metrics
                    for agent_id in self.monitor.health_status.keys():
                        # Get the latest metrics
                        metrics = self.monitor.get_metrics(agent_id)

                        # Filter to recent metrics
                        cutoff_time = current_time - 300  # Last 5 minutes
                        recent_metrics = [
                            m for m in metrics if m["timestamp"] >= cutoff_time
                        ]

                        # Check CPU and memory
                        for metric in recent_metrics:
                            self.alert_manager.check_metric(
                                agent_id=agent_id,
                                metric_name=metric["name"],
                                value=metric["value"],
                            )

                    logger.debug("Alert checking completed")

                except Exception as e:
                    logger.error(f"Error checking alerts: {str(e)}")

                last_check = current_time

            # Sleep for a short time
            time.sleep(1.0)


# Add a blank line here for E302

# Global instance for singleton pattern
_MONITORING_SERVICE_INSTANCE: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get the singleton instance of the monitoring service."""
    global _MONITORING_SERVICE_INSTANCE
    if _MONITORING_SERVICE_INSTANCE is None:
        _MONITORING_SERVICE_INSTANCE = MonitoringService()
    return _MONITORING_SERVICE_INSTANCE
