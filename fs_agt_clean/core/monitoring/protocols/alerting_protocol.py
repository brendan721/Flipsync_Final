"""
FlipSync Alerting Protocol

This module defines the protocols and interfaces for alert detection, notification,
and management within the FlipSync monitoring system.

This is part of the Phase 6 Monitoring Systems Consolidation effort.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar, Union

from .monitoring_protocol import MonitoringLevel


class AlertStatus(Enum):
    """Status values for alerts."""

    PENDING = "pending"  # Alert condition detected but not yet confirmed
    ACTIVE = "active"  # Alert is active and confirmed
    ACKNOWLEDGED = "acknowledged"  # Alert has been acknowledged by a user
    RESOLVED = "resolved"  # Alert has been resolved
    EXPIRED = "expired"  # Alert has expired without resolution


class AlertSeverity(Enum):
    """Severity levels for alerts."""

    INFO = "info"  # Informational, no action required
    WARNING = "warning"  # Warning, may require attention
    ERROR = "error"  # Error, requires attention
    CRITICAL = "critical"  # Critical, requires immediate attention
    FATAL = "fatal"  # Fatal, system is down or severely impacted


class AlertSource(Enum):
    """Sources of alert triggers."""

    METRIC = "metric"  # Alert triggered by metric condition
    LOG = "log"  # Alert triggered by log pattern
    HEALTH = "health"  # Alert triggered by health check
    SECURITY = "security"  # Alert triggered by security event
    EXTERNAL = "external"  # Alert triggered by external system
    MANUAL = "manual"  # Alert triggered manually
    SYSTEM = "system"  # Alert triggered by system condition


class Alert:
    """Represents an alert in the system."""

    def __init__(
        self,
        alert_id: Optional[str] = None,
        name: str = "",
        severity: AlertSeverity = AlertSeverity.WARNING,
        source: AlertSource = AlertSource.SYSTEM,
        component_id: Optional[str] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: AlertStatus = AlertStatus.PENDING,
        labels: Optional[Dict[str, str]] = None,
        acknowledged_by: Optional[str] = None,
        resolved_by: Optional[str] = None,
        notification_sent: bool = False,
        escalation_level: int = 0,
        parent_alert_id: Optional[str] = None,
        related_alert_ids: Optional[List[str]] = None,
    ):
        self.alert_id = alert_id or str(uuid.uuid4())
        self.name = name
        self.severity = severity
        self.source = source
        self.component_id = component_id
        self.message = message
        self.details = details or {}
        self.start_time = start_time or datetime.utcnow()
        self.end_time = end_time
        self.status = status
        self.labels = labels or {}
        self.acknowledged_by = acknowledged_by
        self.resolved_by = resolved_by
        self.notification_sent = notification_sent
        self.escalation_level = escalation_level
        self.parent_alert_id = parent_alert_id
        self.related_alert_ids = related_alert_ids or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert the alert to a dictionary."""
        return {
            "alert_id": self.alert_id,
            "name": self.name,
            "severity": self.severity.value,
            "source": self.source.value,
            "component_id": self.component_id,
            "message": self.message,
            "details": self.details,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "labels": self.labels,
            "acknowledged_by": self.acknowledged_by,
            "resolved_by": self.resolved_by,
            "notification_sent": self.notification_sent,
            "escalation_level": self.escalation_level,
            "parent_alert_id": self.parent_alert_id,
            "related_alert_ids": self.related_alert_ids,
        }


class AlertRule:
    """Defines conditions for triggering an alert."""

    def __init__(
        self,
        rule_id: Optional[str] = None,
        name: str = "",
        description: Optional[str] = None,
        enabled: bool = True,
        severity: AlertSeverity = AlertSeverity.WARNING,
        condition: Dict[str, Any] = None,
        components: Optional[List[str]] = None,
        labels: Optional[Dict[str, str]] = None,
        throttle_duration: Optional[timedelta] = None,
        auto_resolve_duration: Optional[timedelta] = None,
        notifications: Optional[List[Dict[str, Any]]] = None,
        escalation_policy: Optional[Dict[str, Any]] = None,
    ):
        self.rule_id = rule_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.enabled = enabled
        self.severity = severity
        self.condition = condition or {}
        self.components = components or []
        self.labels = labels or {}
        self.throttle_duration = throttle_duration
        self.auto_resolve_duration = auto_resolve_duration
        self.notifications = notifications or []
        self.escalation_policy = escalation_policy or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the alert rule to a dictionary."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "severity": self.severity.value,
            "condition": self.condition,
            "components": self.components,
            "labels": self.labels,
            "throttle_duration": (
                self.throttle_duration.total_seconds()
                if self.throttle_duration
                else None
            ),
            "auto_resolve_duration": (
                self.auto_resolve_duration.total_seconds()
                if self.auto_resolve_duration
                else None
            ),
            "notifications": self.notifications,
            "escalation_policy": self.escalation_policy,
        }


class AlertChannel:
    """Represents a notification channel for alerts."""

    def __init__(
        self,
        channel_id: Optional[str] = None,
        name: str = "",
        channel_type: str = "",
        enabled: bool = True,
        config: Optional[Dict[str, Any]] = None,
        min_severity: AlertSeverity = AlertSeverity.WARNING,
    ):
        self.channel_id = channel_id or str(uuid.uuid4())
        self.name = name
        self.channel_type = channel_type
        self.enabled = enabled
        self.config = config or {}
        self.min_severity = min_severity

    def to_dict(self) -> Dict[str, Any]:
        """Convert the alert channel to a dictionary."""
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "channel_type": self.channel_type,
            "enabled": self.enabled,
            "config": self.config,
            "min_severity": self.min_severity.value,
        }


class AlertingProtocol(ABC):
    """Core protocol for alerting functionality."""

    @abstractmethod
    def register_alert_rule(self, rule: AlertRule) -> str:
        """
        Register a new alert rule.

        Returns:
            str: Rule ID
        """
        pass

    @abstractmethod
    def unregister_alert_rule(self, rule_id: str) -> None:
        """Unregister an alert rule."""
        pass

    @abstractmethod
    def get_alert_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get an alert rule by ID."""
        pass

    @abstractmethod
    def get_alert_rules(
        self,
        enabled_only: bool = True,
        component_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> List[AlertRule]:
        """Get alert rules based on criteria."""
        pass

    @abstractmethod
    def trigger_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        component_id: Optional[str] = None,
        source: AlertSource = AlertSource.SYSTEM,
        details: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Trigger an alert manually.

        Returns:
            str: Alert ID
        """
        pass

    @abstractmethod
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge an alert.

        Returns:
            bool: Success status
        """
        pass

    @abstractmethod
    def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None) -> bool:
        """
        Resolve an alert.

        Returns:
            bool: Success status
        """
        pass

    @abstractmethod
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        pass

    @abstractmethod
    def get_alerts(
        self,
        status: Optional[Union[AlertStatus, List[AlertStatus]]] = None,
        severity: Optional[Union[AlertSeverity, List[AlertSeverity]]] = None,
        component_id: Optional[str] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Alert]:
        """Get alerts based on criteria."""
        pass

    @abstractmethod
    def register_alert_channel(self, channel: AlertChannel) -> str:
        """
        Register a notification channel.

        Returns:
            str: Channel ID
        """
        pass

    @abstractmethod
    def unregister_alert_channel(self, channel_id: str) -> None:
        """Unregister a notification channel."""
        pass

    @abstractmethod
    def get_alert_channel(self, channel_id: str) -> Optional[AlertChannel]:
        """Get a notification channel by ID."""
        pass

    @abstractmethod
    def get_alert_channels(
        self, enabled_only: bool = True, channel_type: Optional[str] = None
    ) -> List[AlertChannel]:
        """Get notification channels based on criteria."""
        pass

    @abstractmethod
    def send_notification(
        self, alert: Alert, channels: Optional[List[str]] = None, force: bool = False
    ) -> bool:
        """
        Send a notification for an alert.

        Args:
            alert: The alert to send a notification for
            channels: Optional list of channel IDs to send to, if None sends to all appropriate channels
            force: If True, sends notification even if one was already sent

        Returns:
            bool: Success status
        """
        pass


class AlertEvaluator(ABC):
    """Protocol for evaluating alert conditions."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the evaluator with configuration."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shutdown the evaluator."""
        pass

    @abstractmethod
    def evaluate_rule(
        self, rule: AlertRule, context: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Evaluate an alert rule against the provided context.

        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (triggered, details)
        """
        pass

    @abstractmethod
    def get_supported_condition_types(self) -> List[str]:
        """Get the condition types supported by this evaluator."""
        pass


class AlertNotifier(ABC):
    """Protocol for sending alert notifications."""

    @property
    @abstractmethod
    def notifier_id(self) -> str:
        """Unique identifier for this notifier."""
        pass

    @property
    @abstractmethod
    def notifier_name(self) -> str:
        """Human-readable name for this notifier."""
        pass

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """The channel type this notifier handles."""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the notifier with configuration."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shutdown the notifier."""
        pass

    @abstractmethod
    def send_notification(self, alert: Alert, channel: AlertChannel) -> bool:
        """
        Send a notification for an alert through the specified channel.

        Returns:
            bool: Success status
        """
        pass

    @abstractmethod
    def format_message(self, alert: Alert, template: Optional[str] = None) -> str:
        """Format an alert into a notification message."""
        pass
