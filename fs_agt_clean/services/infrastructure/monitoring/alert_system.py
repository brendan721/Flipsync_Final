"""
FlipSync UnifiedAgent Alert System

This module provides alerting capabilities for the FlipSync agent monitoring system.
It allows defining alert conditions, sending notifications via various channels,
and managing alert policies.
"""

import asyncio
import json
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Callable, Dict, List, Optional, Set, Union

import requests

# Import agent monitor
from fs_agt_clean.core.monitoring.agent_monitor import UnifiedAgentEvent, UnifiedAgentHealthStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("agent_alerts.log"), logging.StreamHandler()],
)
logger = logging.getLogger("agent_alerts")


class AlertCondition:
    """Defines a condition that triggers an alert."""

    # Alert severity levels
    SEVERITY_INFO = "INFO"
    SEVERITY_WARNING = "WARNING"
    SEVERITY_ERROR = "ERROR"
    SEVERITY_CRITICAL = "CRITICAL"

    def __init__(
        self,
        name: str,
        description: str,
        severity: str = SEVERITY_WARNING,
        agent_ids: List[str] = None,
        threshold: float = None,
        metric_name: str = None,
        comparison: str = None,
        duration_seconds: int = 0,
        cooldown_seconds: int = 300,
    ):
        self.name = name
        self.description = description
        self.severity = severity
        self.agent_ids = agent_ids or []  # Empty list means all agents
        self.threshold = threshold
        self.metric_name = metric_name
        self.comparison = comparison  # '>', '<', '>=', '<=', '==', '!='
        self.duration_seconds = duration_seconds  # How long condition must persist
        self.cooldown_seconds = cooldown_seconds  # Time between repeated alerts
        self.last_triggered: Dict[str, float] = {}  # agent_id -> timestamp

    def check_condition(self, agent_id: str, metric_name: str, value: Any) -> bool:
        """Check if the condition is met for a given metric."""
        # Skip if agent is not in the list (unless list is empty)
        if self.agent_ids and agent_id not in self.agent_ids:
            return False

        # Skip if metric name doesn't match
        if metric_name != self.metric_name:
            return False

        # Skip if in cooldown period
        if agent_id in self.last_triggered:
            elapsed = time.time() - self.last_triggered[agent_id]
            if elapsed < self.cooldown_seconds:
                return False

        # Check condition
        if self.comparison == ">":
            return value > self.threshold
        elif self.comparison == "<":
            return value < self.threshold
        elif self.comparison == ">=":
            return value >= self.threshold
        elif self.comparison == "<=":
            return value <= self.threshold
        elif self.comparison == "==":
            return value == self.threshold
        elif self.comparison == "!=":
            return value != self.threshold
        else:
            return False

    def update_last_triggered(self, agent_id: str) -> None:
        """Update the last triggered time for this agent."""
        self.last_triggered[agent_id] = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "agent_ids": self.agent_ids,
            "threshold": self.threshold,
            "metric_name": self.metric_name,
            "comparison": self.comparison,
            "duration_seconds": self.duration_seconds,
            "cooldown_seconds": self.cooldown_seconds,
        }


class HealthStatusAlertCondition(AlertCondition):
    """Alert condition based on agent health status."""

    def __init__(
        self,
        name: str,
        description: str,
        severity: str = AlertCondition.SEVERITY_WARNING,
        agent_ids: List[str] = None,
        status_triggers: List[str] = None,
        cooldown_seconds: int = 300,
    ):
        super().__init__(
            name, description, severity, agent_ids, cooldown_seconds=cooldown_seconds
        )
        self.status_triggers = status_triggers or [
            UnifiedAgentHealthStatus.STATUS_DEGRADED,
            UnifiedAgentHealthStatus.STATUS_UNHEALTHY,
        ]

    def check_health_status(self, agent_id: str, status: str) -> bool:
        """Check if the health status triggers an alert."""
        # Skip if agent is not in the list (unless list is empty)
        if self.agent_ids and agent_id not in self.agent_ids:
            return False

        # Skip if in cooldown period
        if agent_id in self.last_triggered:
            elapsed = time.time() - self.last_triggered[agent_id]
            if elapsed < self.cooldown_seconds:
                return False

        # Check if status is in the trigger list
        return status in self.status_triggers

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        result = super().to_dict()
        result["status_triggers"] = self.status_triggers
        return result


class EventAlertCondition(AlertCondition):
    """Alert condition based on agent events."""

    def __init__(
        self,
        name: str,
        description: str,
        severity: str = AlertCondition.SEVERITY_WARNING,
        agent_ids: List[str] = None,
        event_types: List[str] = None,
        event_levels: List[str] = None,
        cooldown_seconds: int = 300,
    ):
        super().__init__(
            name, description, severity, agent_ids, cooldown_seconds=cooldown_seconds
        )
        self.event_types = event_types or []  # Empty list means all event types
        self.event_levels = event_levels or [
            UnifiedAgentEvent.LEVEL_ERROR,
            UnifiedAgentEvent.LEVEL_CRITICAL,
        ]

    def check_event(self, agent_id: str, event_type: str, event_level: str) -> bool:
        """Check if the event triggers an alert."""
        # Skip if agent is not in the list (unless list is empty)
        if self.agent_ids and agent_id not in self.agent_ids:
            return False

        # Skip if in cooldown period
        if agent_id in self.last_triggered:
            elapsed = time.time() - self.last_triggered[agent_id]
            if elapsed < self.cooldown_seconds:
                return False

        # Skip if event type is not in the list (unless list is empty)
        if self.event_types and event_type not in self.event_types:
            return False

        # Check if event level is in the trigger list
        return event_level in self.event_levels

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        result = super().to_dict()
        result["event_types"] = self.event_types
        result["event_levels"] = self.event_levels
        return result


class AlertNotifier:
    """Base class for alert notifiers."""

    def __init__(self, name: str):
        self.name = name
        self.enabled = True

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send an alert notification. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement send_alert")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "enabled": self.enabled,
        }


class EmailAlertNotifier(AlertNotifier):
    """Sends alert notifications via email."""

    def __init__(
        self,
        name: str,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True,
    ):
        super().__init__(name)
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send an alert notification via email."""
        if not self.enabled:
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            msg["Subject"] = (
                f"FlipSync Alert: {alert['severity']} - {alert['condition_name']}"
            )

            # Create email body
            body = f"""
<html>
<body>
<h2>FlipSync UnifiedAgent Alert</h2>
<p><strong>Severity:</strong> {alert['severity']}</p>
<p><strong>Condition:</strong> {alert['condition_name']}</p>
<p><strong>Description:</strong> {alert['description']}</p>
<p><strong>UnifiedAgent:</strong> {alert['agent_id']}</p>
<p><strong>Time:</strong> {alert['timestamp_formatted']}</p>
<h3>Details</h3>
<pre>{json.dumps(alert['details'], indent=2)}</pre>
</body>
</html>
"""
            msg.attach(MIMEText(body, "html"))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()

            logger.info(
                f"Sent email alert for {alert['condition_name']} to {', '.join(self.to_emails)}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        result = super().to_dict()
        result["smtp_server"] = self.smtp_server
        result["smtp_port"] = self.smtp_port
        result["username"] = self.username  # Consider omitting for security
        result["from_email"] = self.from_email
        result["to_emails"] = self.to_emails
        result["use_tls"] = self.use_tls
        return result


class WebhookAlertNotifier(AlertNotifier):
    """Sends alert notifications to a webhook endpoint."""

    def __init__(
        self,
        name: str,
        webhook_url: str,
        headers: Dict[str, str] = None,
        timeout_seconds: int = 10,
    ):
        super().__init__(name)
        self.webhook_url = webhook_url
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout_seconds = timeout_seconds

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send an alert notification to the webhook endpoint."""
        if not self.enabled:
            return False

        try:
            # Create the payload
            payload = {
                "alert_type": "agent_alert",
                "severity": alert["severity"],
                "condition_name": alert["condition_name"],
                "description": alert["description"],
                "agent_id": alert["agent_id"],
                "timestamp": alert["timestamp"],
                "timestamp_formatted": alert["timestamp_formatted"],
                "details": alert["details"],
            }

            # Send the request
            response = requests.post(
                self.webhook_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout_seconds,
            )

            # Check response
            if response.status_code < 400:  # Any 2xx or 3xx status code
                logger.info(
                    f"Sent webhook alert for {alert['condition_name']} to {self.webhook_url}"
                )
                return True
            else:
                logger.error(
                    f"Webhook alert failed with status {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {str(e)}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        result = super().to_dict()
        result["webhook_url"] = self.webhook_url
        result["headers"] = self.headers
        result["timeout_seconds"] = self.timeout_seconds
        return result


class AlertManager:
    """Manages alert conditions and notifications."""

    def __init__(self, output_dir: str = "alert_history"):
        self.output_dir = output_dir
        self.metric_conditions: List[AlertCondition] = []
        self.health_conditions: List[HealthStatusAlertCondition] = []
        self.event_conditions: List[EventAlertCondition] = []
        self.notifiers: List[AlertNotifier] = []
        self.alert_history: List[Dict[str, Any]] = []
        self.current_alerts: Dict[str, Dict[str, Any]] = {}  # alert_id -> alert

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

    def add_metric_condition(self, condition: AlertCondition) -> None:
        """Add a metric-based alert condition."""
        self.metric_conditions.append(condition)
        logger.info(f"Added metric alert condition: {condition.name}")

    def add_health_condition(self, condition: HealthStatusAlertCondition) -> None:
        """Add a health-based alert condition."""
        self.health_conditions.append(condition)
        logger.info(f"Added health alert condition: {condition.name}")

    def add_event_condition(self, condition: EventAlertCondition) -> None:
        """Add an event-based alert condition."""
        self.event_conditions.append(condition)
        logger.info(f"Added event alert condition: {condition.name}")

    def add_notifier(self, notifier: AlertNotifier) -> None:
        """Add an alert notifier."""
        self.notifiers.append(notifier)
        logger.info(f"Added alert notifier: {notifier.name}")

    def check_metric(self, agent_id: str, metric_name: str, value: Any) -> None:
        """Check if a metric triggers any alerts."""
        for condition in self.metric_conditions:
            if condition.check_condition(agent_id, metric_name, value):
                self._trigger_alert(
                    agent_id, condition, {"metric_name": metric_name, "value": value}
                )
                condition.update_last_triggered(agent_id)

    def check_health_status(
        self, agent_id: str, status: str, details: Dict[str, Any] = None
    ) -> None:
        """Check if a health status triggers any alerts."""
        for condition in self.health_conditions:
            if condition.check_health_status(agent_id, status):
                self._trigger_alert(
                    agent_id, condition, {"status": status, "details": details or {}}
                )
                condition.update_last_triggered(agent_id)

    def check_event(
        self,
        agent_id: str,
        event_type: str,
        event_level: str,
        details: Dict[str, Any] = None,
    ) -> None:
        """Check if an event triggers any alerts."""
        for condition in self.event_conditions:
            if condition.check_event(agent_id, event_type, event_level):
                self._trigger_alert(
                    agent_id,
                    condition,
                    {
                        "event_type": event_type,
                        "event_level": event_level,
                        "details": details or {},
                    },
                )
                condition.update_last_triggered(agent_id)

    def _trigger_alert(
        self, agent_id: str, condition: AlertCondition, details: Dict[str, Any]
    ) -> None:
        """Trigger an alert and send notifications."""
        # Create alert record
        timestamp = time.time()
        alert_id = f"{agent_id}_{condition.name}_{int(timestamp)}"

        alert = {
            "alert_id": alert_id,
            "agent_id": agent_id,
            "condition_name": condition.name,
            "description": condition.description,
            "severity": condition.severity,
            "timestamp": timestamp,
            "timestamp_formatted": datetime.fromtimestamp(timestamp).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "details": details,
            "resolved": False,
            "resolved_timestamp": None,
            "notifiers": [],
        }

        # Save to current alerts and history
        self.current_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Trim history if it gets too large
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

        # Log the alert
        log_func = logger.info
        if condition.severity == AlertCondition.SEVERITY_WARNING:
            log_func = logger.warning
        elif condition.severity == AlertCondition.SEVERITY_ERROR:
            log_func = logger.error
        elif condition.severity == AlertCondition.SEVERITY_CRITICAL:
            log_func = logger.critical

        log_func(f"Alert triggered: {condition.name} for agent {agent_id}")

        # Send notifications
        asyncio.create_task(self._send_notifications(alert))

        # Save alert to disk
        self._save_alert_to_disk(alert)

    async def _send_notifications(self, alert: Dict[str, Any]) -> None:
        """Send notifications for an alert."""
        for notifier in self.notifiers:
            if notifier.enabled:
                success = await notifier.send_alert(alert)
                alert["notifiers"].append(
                    {
                        "notifier": notifier.name,
                        "success": success,
                        "timestamp": time.time(),
                    }
                )

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        if alert_id not in self.current_alerts:
            return False

        # Update the alert
        alert = self.current_alerts[alert_id]
        alert["resolved"] = True
        alert["resolved_timestamp"] = time.time()

        # Remove from current alerts
        del self.current_alerts[alert_id]

        # Save the updated alert to disk
        self._save_alert_to_disk(alert)

        logger.info(
            f"Alert resolved: {alert['condition_name']} for agent {alert['agent_id']}"
        )
        return True

    def get_active_alerts(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts, optionally filtered by agent."""
        if agent_id:
            return [
                a for a in self.current_alerts.values() if a["agent_id"] == agent_id
            ]
        else:
            return list(self.current_alerts.values())

    def get_alert_history(
        self, agent_id: str = None, hours: int = 24, severity: str = None
    ) -> List[Dict[str, Any]]:
        """Get alert history, optionally filtered by agent, time, and severity."""
        cutoff_time = time.time() - (hours * 3600)

        result = []
        for alert in self.alert_history:
            if alert["timestamp"] < cutoff_time:
                continue

            if agent_id and alert["agent_id"] != agent_id:
                continue

            if severity and alert["severity"] != severity:
                continue

            result.append(alert)

        return result

    def _save_alert_to_disk(self, alert: Dict[str, Any]) -> None:
        """Save an alert to disk."""
        # Create agent directory if it doesn't exist
        agent_dir = f"{self.output_dir}/{alert['agent_id']}"
        os.makedirs(agent_dir, exist_ok=True)

        # Save alert to file
        alert_file = f"{agent_dir}/alert_{alert['alert_id']}.json"
        with open(alert_file, "w") as f:
            json.dump(alert, f, indent=2)

    def save_config(self) -> None:
        """Save the alert manager configuration to disk."""
        config = {
            "metric_conditions": [c.to_dict() for c in self.metric_conditions],
            "health_conditions": [c.to_dict() for c in self.health_conditions],
            "event_conditions": [c.to_dict() for c in self.event_conditions],
            "notifiers": [n.to_dict() for n in self.notifiers],
        }

        config_file = f"{self.output_dir}/alert_config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved alert manager configuration to {config_file}")

    def load_config(self, config_file: str) -> bool:
        """Load the alert manager configuration from disk."""
        try:
            with open(config_file, "r") as f:
                config = json.load(f)

            # Clear existing configuration
            self.metric_conditions = []
            self.health_conditions = []
            self.event_conditions = []
            self.notifiers = []

            # Load metric conditions
            for c_dict in config.get("metric_conditions", []):
                condition = AlertCondition(
                    name=c_dict["name"],
                    description=c_dict["description"],
                    severity=c_dict["severity"],
                    agent_ids=c_dict.get("agent_ids", []),
                    threshold=c_dict.get("threshold"),
                    metric_name=c_dict.get("metric_name"),
                    comparison=c_dict.get("comparison"),
                    duration_seconds=c_dict.get("duration_seconds", 0),
                    cooldown_seconds=c_dict.get("cooldown_seconds", 300),
                )
                self.metric_conditions.append(condition)

            # Load health conditions
            for c_dict in config.get("health_conditions", []):
                condition = HealthStatusAlertCondition(
                    name=c_dict["name"],
                    description=c_dict["description"],
                    severity=c_dict["severity"],
                    agent_ids=c_dict.get("agent_ids", []),
                    status_triggers=c_dict.get("status_triggers"),
                    cooldown_seconds=c_dict.get("cooldown_seconds", 300),
                )
                self.health_conditions.append(condition)

            # Load event conditions
            for c_dict in config.get("event_conditions", []):
                condition = EventAlertCondition(
                    name=c_dict["name"],
                    description=c_dict["description"],
                    severity=c_dict["severity"],
                    agent_ids=c_dict.get("agent_ids", []),
                    event_types=c_dict.get("event_types", []),
                    event_levels=c_dict.get("event_levels"),
                    cooldown_seconds=c_dict.get("cooldown_seconds", 300),
                )
                self.event_conditions.append(condition)

            # Note: Notifiers require more complex initialization
            # You would typically create specific notifier instances and add them
            # based on the notifier type in the config

            logger.info(f"Loaded alert manager configuration from {config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load alert manager configuration: {str(e)}")
            return False

    def create_default_config(self) -> None:
        """Create a default configuration with common alert conditions."""
        # CPU usage alerts
        self.add_metric_condition(
            AlertCondition(
                name="high_cpu_usage",
                description="CPU usage is above 80% for an extended period",
                severity=AlertCondition.SEVERITY_WARNING,
                metric_name="cpu_percent",
                threshold=80.0,
                comparison=">",
                duration_seconds=300,  # 5 minutes
                cooldown_seconds=1800,  # 30 minutes
            )
        )

        self.add_metric_condition(
            AlertCondition(
                name="critical_cpu_usage",
                description="CPU usage is above 95% for an extended period",
                severity=AlertCondition.SEVERITY_CRITICAL,
                metric_name="cpu_percent",
                threshold=95.0,
                comparison=">",
                duration_seconds=120,  # 2 minutes
                cooldown_seconds=900,  # 15 minutes
            )
        )

        # Memory usage alerts
        self.add_metric_condition(
            AlertCondition(
                name="high_memory_usage",
                description="Memory usage is above 300MB",
                severity=AlertCondition.SEVERITY_WARNING,
                metric_name="memory_mb",
                threshold=300.0,
                comparison=">",
                duration_seconds=300,  # 5 minutes
                cooldown_seconds=1800,  # 30 minutes
            )
        )

        self.add_metric_condition(
            AlertCondition(
                name="critical_memory_usage",
                description="Memory usage is above 500MB",
                severity=AlertCondition.SEVERITY_CRITICAL,
                metric_name="memory_mb",
                threshold=500.0,
                comparison=">",
                duration_seconds=120,  # 2 minutes
                cooldown_seconds=900,  # 15 minutes
            )
        )

        # Health status alerts
        self.add_health_condition(
            HealthStatusAlertCondition(
                name="degraded_health",
                description="UnifiedAgent health is degraded",
                severity=AlertCondition.SEVERITY_WARNING,
                status_triggers=[UnifiedAgentHealthStatus.STATUS_DEGRADED],
                cooldown_seconds=1800,  # 30 minutes
            )
        )

        self.add_health_condition(
            HealthStatusAlertCondition(
                name="unhealthy_status",
                description="UnifiedAgent is unhealthy",
                severity=AlertCondition.SEVERITY_CRITICAL,
                status_triggers=[UnifiedAgentHealthStatus.STATUS_UNHEALTHY],
                cooldown_seconds=900,  # 15 minutes
            )
        )

        # Error and critical event alerts
        self.add_event_condition(
            EventAlertCondition(
                name="error_events",
                description="UnifiedAgent encountered an error",
                severity=AlertCondition.SEVERITY_ERROR,
                event_levels=[UnifiedAgentEvent.LEVEL_ERROR],
                cooldown_seconds=1800,  # 30 minutes
            )
        )

        self.add_event_condition(
            EventAlertCondition(
                name="critical_events",
                description="UnifiedAgent encountered a critical error",
                severity=AlertCondition.SEVERITY_CRITICAL,
                event_levels=[UnifiedAgentEvent.LEVEL_CRITICAL],
                cooldown_seconds=900,  # 15 minutes
            )
        )

        logger.info("Created default alert conditions")

        # Save the configuration
        self.save_config()
