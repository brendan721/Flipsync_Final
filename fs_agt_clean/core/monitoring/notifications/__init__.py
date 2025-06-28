"""Notification system for monitoring.

This module provides a notification system for monitoring alerts and metrics.
"""

from enum import Enum


class NotificationChannel(str, Enum):
    """Notification channels."""

    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"


# Import after NotificationChannel to avoid circular imports
from fs_agt_clean.core.monitoring.notifications.config import (
    AlertSeverity,
    ChannelConfig,
    EmailConfig,
    NotificationConfig,
    RateLimitConfig,
    SlackConfig,
    SmsConfig,
    WebhookConfig,
)
from fs_agt_clean.core.monitoring.notifications.handler import NotificationHandler
from fs_agt_clean.core.monitoring.notifications.models import Alert, Notification

__all__ = [
    "Alert",
    "AlertSeverity",
    "ChannelConfig",
    "EmailConfig",
    "Notification",
    "NotificationChannel",
    "NotificationConfig",
    "NotificationHandler",
    "RateLimitConfig",
    "SlackConfig",
    "SmsConfig",
    "WebhookConfig",
]
