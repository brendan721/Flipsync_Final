"""
Alerting Service

This module provides functionality for monitoring metrics and sending alerts.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field

from fs_agt_clean.core.utils.logging import get_logger
from fs_agt_clean.services.metrics.service import MetricsService
from fs_agt_clean.services.notifications.service import NotificationService

logger = get_logger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class AlertRule(BaseModel):
    """Alert rule configuration."""

    id: str = Field(..., description="Unique identifier for the rule")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    metric_name: str = Field(..., description="Metric name to monitor")
    component: Optional[str] = Field(None, description="Metric component")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")

    # Threshold configuration
    threshold: float = Field(..., description="Threshold value")
    comparison: str = Field(
        ..., description="Comparison operator (>, <, >=, <=, ==, !=)"
    )
    duration: int = Field(
        0, description="Duration in seconds the threshold must be exceeded"
    )

    # Alert configuration
    severity: AlertSeverity = Field(AlertSeverity.WARNING, description="Alert severity")
    notification_channels: List[str] = Field(
        default_factory=list, description="Notification channels"
    )
    cooldown: int = Field(300, description="Cooldown period in seconds")

    # State
    enabled: bool = Field(True, description="Whether the rule is enabled")


class Alert(BaseModel):
    """Alert information."""

    id: str = Field(..., description="Unique identifier for the alert")
    rule_id: str = Field(..., description="ID of the rule that triggered the alert")
    name: str = Field(..., description="Alert name")
    description: str = Field(..., description="Alert description")
    metric_name: str = Field(..., description="Metric name")
    component: Optional[str] = Field(None, description="Metric component")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")

    # Alert details
    value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Threshold value")
    comparison: str = Field(..., description="Comparison operator")

    # Status
    status: AlertStatus = Field(AlertStatus.ACTIVE, description="Alert status")
    severity: AlertSeverity = Field(AlertSeverity.WARNING, description="Alert severity")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update time"
    )
    resolved_at: Optional[datetime] = Field(None, description="Resolution time")
    acknowledged_at: Optional[datetime] = Field(
        None, description="Acknowledgement time"
    )

    # Notification
    notification_channels: List[str] = Field(
        default_factory=list, description="Notification channels"
    )
    last_notification_time: Optional[datetime] = Field(
        None, description="Last notification time"
    )
    notification_count: int = Field(0, description="Number of notifications sent")


class AlertingService:
    """
    Service for monitoring metrics and sending alerts.

    This class monitors metrics and sends alerts when thresholds are exceeded.
    """

    def __init__(
        self,
        metrics_service: MetricsService,
        notification_service: Optional[NotificationService] = None,
        check_interval: int = 60,  # 1 minute
    ):
        """
        Initialize the alerting service.

        Args:
            metrics_service: Metrics service for retrieving metrics
            notification_service: Notification service for sending alerts
            check_interval: Interval between alert checks in seconds
        """
        self.metrics_service = metrics_service
        self.notification_service = notification_service
        self.check_interval = check_interval

        self.is_running = False
        self.check_task = None
        self.last_check_time = None

        # Alert rules
        self.rules: Dict[str, AlertRule] = {}

        # Active alerts
        self.alerts: Dict[str, Alert] = {}

        # Alert history
        self.alert_history: List[Alert] = []

        # Metric state for duration-based alerts
        self.metric_state: Dict[str, Dict[str, Any]] = {}

        logger.info("Alerting service initialized")

    async def start(self) -> None:
        """Start checking for alerts."""
        if self.is_running:
            logger.warning("Alerting service is already running")
            return

        self.is_running = True
        self.check_task = asyncio.create_task(self._check_alerts_loop())
        logger.info("Started alerting service")

    async def stop(self) -> None:
        """Stop checking for alerts."""
        if not self.is_running:
            logger.warning("Alerting service is not running")
            return

        self.is_running = False
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
            self.check_task = None

        logger.info("Stopped alerting service")

    async def _check_alerts_loop(self) -> None:
        """Continuously check for alerts at the configured interval."""
        while self.is_running:
            try:
                await self._check_alerts()
                self.last_check_time = datetime.utcnow()

                # Sleep until next check
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error checking alerts: %s", e)
                await asyncio.sleep(10)  # Sleep for a short time before retrying

    async def _check_alerts(self) -> None:
        """Check all alert rules."""
        try:
            # Get latest metrics
            latest_metrics = await self.metrics_service.get_latest_metrics()

            # Check each rule
            for rule_id, rule in self.rules.items():
                if not rule.enabled:
                    continue

                try:
                    # Find matching metrics
                    matching_metrics = []
                    for metric in latest_metrics:
                        if metric["name"] == rule.metric_name:
                            # Check component if specified
                            if (
                                rule.component
                                and metric.get("component") != rule.component
                            ):
                                continue

                            # Check labels if specified
                            if rule.labels:
                                metric_labels = metric.get("labels", {})
                                if not all(
                                    metric_labels.get(k) == v
                                    for k, v in rule.labels.items()
                                ):
                                    continue

                            matching_metrics.append(metric)

                    # Process matching metrics
                    for metric in matching_metrics:
                        await self._process_metric(rule, metric)
                except Exception as e:
                    logger.error("Error checking rule %s: %s", rule_id, e)

            # Check for resolved alerts
            await self._check_resolved_alerts(latest_metrics)

            logger.debug("Checked alerts")
        except Exception as e:
            logger.error("Error checking alerts: %s", e)

    async def _process_metric(self, rule: AlertRule, metric: Dict[str, Any]) -> None:
        """
        Process a metric against a rule.

        Args:
            rule: Alert rule
            metric: Metric data
        """
        try:
            # Get metric value
            value = metric["value"]

            # Check threshold
            threshold_exceeded = self._check_threshold(
                value, rule.threshold, rule.comparison
            )

            # Get metric key
            metric_key = self._get_metric_key(rule, metric)

            # Check if we need to track duration
            if rule.duration > 0:
                # Get or initialize metric state
                if metric_key not in self.metric_state:
                    self.metric_state[metric_key] = {
                        "exceeded_since": None,
                        "last_value": value,
                        "last_check": datetime.utcnow(),
                    }

                state = self.metric_state[metric_key]

                if threshold_exceeded:
                    # Start or continue tracking duration
                    if state["exceeded_since"] is None:
                        state["exceeded_since"] = datetime.utcnow()

                    # Check if duration threshold is met
                    duration = (
                        datetime.utcnow() - state["exceeded_since"]
                    ).total_seconds()
                    if duration >= rule.duration:
                        # Duration threshold met, create or update alert
                        await self._create_or_update_alert(rule, metric, value)
                else:
                    # Reset duration tracking
                    state["exceeded_since"] = None

                    # Check if alert should be resolved
                    alert_id = f"{rule.id}:{metric_key}"
                    if alert_id in self.alerts:
                        await self._resolve_alert(alert_id, value)

                # Update state
                state["last_value"] = value
                state["last_check"] = datetime.utcnow()
            else:
                # No duration tracking, create alert immediately if threshold is exceeded
                if threshold_exceeded:
                    await self._create_or_update_alert(rule, metric, value)
                else:
                    # Check if alert should be resolved
                    alert_id = f"{rule.id}:{metric_key}"
                    if alert_id in self.alerts:
                        await self._resolve_alert(alert_id, value)
        except Exception as e:
            logger.error("Error processing metric for rule %s: %s", rule.id, e)

    def _check_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """
        Check if a value exceeds a threshold.

        Args:
            value: Value to check
            threshold: Threshold value
            comparison: Comparison operator

        Returns:
            True if the threshold is exceeded, False otherwise
        """
        if comparison == ">":
            return value > threshold
        elif comparison == "<":
            return value < threshold
        elif comparison == ">=":
            return value >= threshold
        elif comparison == "<=":
            return value <= threshold
        elif comparison == "==":
            return value == threshold
        elif comparison == "!=":
            return value != threshold
        else:
            logger.warning("Unknown comparison operator: %s", comparison)
            return False

    def _get_metric_key(self, rule: AlertRule, metric: Dict[str, Any]) -> str:
        """
        Get a unique key for a metric.

        Args:
            rule: Alert rule
            metric: Metric data

        Returns:
            Unique metric key
        """
        # Start with metric name
        key_parts = [metric["name"]]

        # Add component if present
        if "component" in metric:
            key_parts.append(metric["component"])

        # Add labels if present
        if "labels" in metric and metric["labels"]:
            labels_str = ",".join(
                f"{k}={v}" for k, v in sorted(metric["labels"].items())
            )
            key_parts.append(labels_str)

        return ":".join(key_parts)

    async def _create_or_update_alert(
        self, rule: AlertRule, metric: Dict[str, Any], value: float
    ) -> None:
        """
        Create or update an alert.

        Args:
            rule: Alert rule
            metric: Metric data
            value: Current metric value
        """
        try:
            # Get metric key
            metric_key = self._get_metric_key(rule, metric)

            # Create alert ID
            alert_id = f"{rule.id}:{metric_key}"

            # Check if alert already exists
            if alert_id in self.alerts:
                # Update existing alert
                alert = self.alerts[alert_id]
                alert.value = value
                alert.updated_at = datetime.utcnow()

                # Check if we should send another notification
                if self.notification_service and rule.notification_channels:
                    # Check cooldown
                    if (
                        alert.last_notification_time is None
                        or (
                            datetime.utcnow() - alert.last_notification_time
                        ).total_seconds()
                        >= rule.cooldown
                    ):
                        # Send notification
                        await self._send_alert_notification(alert)
            else:
                # Create new alert
                alert = Alert(
                    id=alert_id,
                    rule_id=rule.id,
                    name=rule.name,
                    description=rule.description,
                    metric_name=metric["name"],
                    component=metric.get("component"),
                    labels=metric.get("labels", {}),
                    value=value,
                    threshold=rule.threshold,
                    comparison=rule.comparison,
                    severity=rule.severity,
                    notification_channels=rule.notification_channels,
                )

                # Add to active alerts
                self.alerts[alert_id] = alert

                # Send notification
                if self.notification_service and rule.notification_channels:
                    await self._send_alert_notification(alert)

                logger.info("Created alert: %s", alert_id)
        except Exception as e:
            logger.error("Error creating or updating alert: %s", e)

    async def _resolve_alert(self, alert_id: str, value: float) -> None:
        """
        Resolve an alert.

        Args:
            alert_id: Alert ID
            value: Current metric value
        """
        try:
            # Get alert
            alert = self.alerts.get(alert_id)
            if not alert:
                return

            # Update alert
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.value = value
            alert.updated_at = datetime.utcnow()

            # Send resolution notification
            if self.notification_service and alert.notification_channels:
                await self._send_alert_resolution_notification(alert)

            # Move to history
            self.alert_history.append(alert)

            # Remove from active alerts
            del self.alerts[alert_id]

            logger.info("Resolved alert: %s", alert_id)
        except Exception as e:
            logger.error("Error resolving alert: %s", e)

    async def _check_resolved_alerts(
        self, latest_metrics: List[Dict[str, Any]]
    ) -> None:
        """
        Check if any active alerts should be resolved.

        Args:
            latest_metrics: Latest metrics
        """
        try:
            # Build a map of metric keys to values
            metric_values = {}
            for metric in latest_metrics:
                metric_key = f"{metric['name']}:{metric.get('component', '')}:{','.join(f'{k}={v}' for k, v in sorted(metric.get('labels', {}).items()))}"
                metric_values[metric_key] = metric["value"]

            # Check each active alert
            for alert_id, alert in list(self.alerts.items()):
                # Get rule
                rule = self.rules.get(alert.rule_id)
                if not rule:
                    # Rule no longer exists, resolve alert
                    await self._resolve_alert(alert_id, alert.value)
                    continue

                # Build metric key
                metric_key = f"{alert.metric_name}:{alert.component or ''}:{','.join(f'{k}={v}' for k, v in sorted(alert.labels.items()))}"

                # Check if metric exists
                if metric_key not in metric_values:
                    # Metric no longer exists, keep alert active
                    continue

                # Get current value
                value = metric_values[metric_key]

                # Check threshold
                threshold_exceeded = self._check_threshold(
                    value, rule.threshold, rule.comparison
                )

                if not threshold_exceeded:
                    # Threshold no longer exceeded, resolve alert
                    await self._resolve_alert(alert_id, value)
        except Exception as e:
            logger.error("Error checking resolved alerts: %s", e)

    async def _send_alert_notification(self, alert: Alert) -> None:
        """
        Send an alert notification.

        Args:
            alert: Alert to send notification for
        """
        try:
            if not self.notification_service:
                return

            # Build notification data
            data = {
                "alert_id": alert.id,
                "name": alert.name,
                "description": alert.description,
                "metric_name": alert.metric_name,
                "component": alert.component,
                "labels": alert.labels,
                "value": alert.value,
                "threshold": alert.threshold,
                "comparison": alert.comparison,
                "severity": alert.severity,
                "status": alert.status,
                "created_at": alert.created_at.isoformat(),
                "updated_at": alert.updated_at.isoformat(),
            }

            # Send notification
            for channel in alert.notification_channels:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="alert",
                    category="alert",
                    data=data,
                    delivery_methods={channel},
                )

            # Update alert
            alert.last_notification_time = datetime.utcnow()
            alert.notification_count += 1

            logger.info("Sent alert notification: %s", alert.id)
        except Exception as e:
            logger.error("Error sending alert notification: %s", e)

    async def _send_alert_resolution_notification(self, alert: Alert) -> None:
        """
        Send an alert resolution notification.

        Args:
            alert: Alert to send notification for
        """
        try:
            if not self.notification_service:
                return

            # Build notification data
            data = {
                "alert_id": alert.id,
                "name": alert.name,
                "description": alert.description,
                "metric_name": alert.metric_name,
                "component": alert.component,
                "labels": alert.labels,
                "value": alert.value,
                "threshold": alert.threshold,
                "comparison": alert.comparison,
                "severity": alert.severity,
                "status": alert.status,
                "created_at": alert.created_at.isoformat(),
                "updated_at": alert.updated_at.isoformat(),
                "resolved_at": (
                    alert.resolved_at.isoformat() if alert.resolved_at else None
                ),
            }

            # Send notification
            for channel in alert.notification_channels:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="alert_resolved",
                    category="alert",
                    data=data,
                    delivery_methods={channel},
                )

            logger.info("Sent alert resolution notification: %s", alert.id)
        except Exception as e:
            logger.error("Error sending alert resolution notification: %s", e)

    def add_rule(self, rule: AlertRule) -> None:
        """
        Add an alert rule.

        Args:
            rule: Alert rule to add
        """
        self.rules[rule.id] = rule
        logger.info("Added alert rule: %s", rule.id)

    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove an alert rule.

        Args:
            rule_id: ID of the rule to remove

        Returns:
            True if the rule was removed, False otherwise
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info("Removed alert rule: %s", rule_id)
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """
        Get an alert rule.

        Args:
            rule_id: ID of the rule to get

        Returns:
            Alert rule if found, None otherwise
        """
        return self.rules.get(rule_id)

    def get_all_rules(self) -> Dict[str, AlertRule]:
        """
        Get all alert rules.

        Returns:
            Dictionary of alert rules
        """
        return self.rules.copy()

    def get_active_alerts(self) -> Dict[str, Alert]:
        """
        Get all active alerts.

        Returns:
            Dictionary of active alerts
        """
        return self.alerts.copy()

    def get_alert_history(self) -> List[Alert]:
        """
        Get alert history.

        Returns:
            List of historical alerts
        """
        return self.alert_history.copy()

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of the alert to acknowledge

        Returns:
            True if the alert was acknowledged, False otherwise
        """
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.updated_at = datetime.utcnow()
            logger.info("Acknowledged alert: %s", alert_id)
            return True
        return False

    def clear_alert_history(self) -> None:
        """Clear alert history."""
        self.alert_history.clear()
        logger.info("Cleared alert history")
