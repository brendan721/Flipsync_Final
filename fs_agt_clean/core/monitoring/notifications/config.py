"""Notification configuration for monitoring.

This module provides configuration classes for the notification system.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationChannel(str, Enum):
    """Notification channels."""

    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"


logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RateLimitConfig(BaseModel):
    """Rate limit configuration for notifications."""

    interval_seconds: int = Field(
        60, description="Minimum interval between notifications in seconds"
    )
    max_notifications: int = Field(
        10, description="Maximum number of notifications per interval"
    )
    cooldown_seconds: int = Field(
        300, description="Cooldown period after reaching max notifications"
    )

    @field_validator("interval_seconds", "cooldown_seconds")
    def validate_time_values(cls, v):
        """Validate time values are positive."""
        if v <= 0:
            raise ValueError("Time values must be positive")
        return v

    @field_validator("max_notifications")
    def validate_max_notifications(cls, v):
        """Validate max notifications is positive."""
        if v <= 0:
            raise ValueError("Max notifications must be positive")
        return v


class EmailConfig(BaseModel):
    """Email notification configuration."""

    enabled: bool = Field(True, description="Whether email notifications are enabled")
    recipients: List[str] = Field(
        default_factory=list, description="List of email recipients"
    )
    from_address: str = Field(
        "notifications@flipsync.io", description="From email address"
    )
    smtp_host: str = Field("smtp.example.com", description="SMTP host")
    smtp_port: int = Field(587, description="SMTP port")
    smtp_username: Optional[str] = Field(None, description="SMTP username")
    smtp_password: Optional[str] = Field(None, description="SMTP password")
    use_tls: bool = Field(True, description="Whether to use TLS")

    @field_validator("recipients")
    def validate_recipients(cls, v):
        """Validate email recipients."""
        if not v:
            raise ValueError("At least one recipient is required")
        return v


class SlackConfig(BaseModel):
    """Slack notification configuration."""

    enabled: bool = Field(True, description="Whether Slack notifications are enabled")
    webhook_url: str = Field(
        "https://hooks.slack.com/services/example", description="Slack webhook URL"
    )
    channel: Optional[str] = Field(None, description="Slack channel")
    username: str = Field("FlipSync Monitor", description="Bot username")
    icon_emoji: Optional[str] = Field(":robot_face:", description="Bot icon emoji")


class SmsConfig(BaseModel):
    """SMS notification configuration."""

    enabled: bool = Field(False, description="Whether SMS notifications are enabled")
    provider: str = Field("twilio", description="SMS provider")
    account_sid: Optional[str] = Field(None, description="Twilio account SID")
    auth_token: Optional[str] = Field(None, description="Twilio auth token")
    from_number: Optional[str] = Field(None, description="From phone number")
    to_numbers: List[str] = Field(default_factory=list, description="To phone numbers")


class WebhookConfig(BaseModel):
    """Webhook notification configuration."""

    enabled: bool = Field(
        False, description="Whether webhook notifications are enabled"
    )
    url: str = Field("https://example.com/webhook", description="Webhook URL")
    method: str = Field("POST", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    timeout_seconds: int = Field(5, description="Request timeout in seconds")


class ChannelConfig(BaseModel):
    """Configuration for a notification channel."""

    email: EmailConfig = Field(default_factory=lambda: EmailConfig())
    slack: SlackConfig = Field(default_factory=lambda: SlackConfig())
    sms: SmsConfig = Field(default_factory=lambda: SmsConfig())
    webhook: WebhookConfig = Field(default_factory=lambda: WebhookConfig())


class NotificationConfig(BaseModel):
    """Notification system configuration."""

    enabled: bool = Field(True, description="Whether notifications are enabled")
    channels: List[NotificationChannel] = Field(
        default_factory=lambda: [NotificationChannel.EMAIL],
        description="Enabled notification channels",
    )
    rate_limit: RateLimitConfig = Field(
        default_factory=lambda: RateLimitConfig(),
        description="Rate limit configuration",
    )
    channel_config: ChannelConfig = Field(
        default_factory=lambda: ChannelConfig(),
        description="Channel-specific configuration",
    )
    severity_threshold: AlertSeverity = Field(
        AlertSeverity.WARNING,
        description="Minimum severity level to trigger notifications",
    )

    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if a notification channel is enabled.

        Args:
            channel: The notification channel to check

        Returns:
            True if the channel is enabled, False otherwise
        """
        if not self.enabled:
            return False

        if channel not in self.channels:
            return False

        if channel == NotificationChannel.EMAIL:
            return self.channel_config.email.enabled
        elif channel == NotificationChannel.SLACK:
            return self.channel_config.slack.enabled
        elif channel == NotificationChannel.SMS:
            return self.channel_config.sms.enabled
        elif channel == NotificationChannel.WEBHOOK:
            return self.channel_config.webhook.enabled

        return False

    def should_notify(self, severity: AlertSeverity) -> bool:
        """Check if a notification should be sent based on severity.

        Args:
            severity: The severity of the alert

        Returns:
            True if a notification should be sent, False otherwise
        """
        if not self.enabled:
            return False

        severity_values = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 1,
            AlertSeverity.ERROR: 2,
            AlertSeverity.CRITICAL: 3,
        }

        threshold_value = severity_values.get(self.severity_threshold, 0)
        severity_value = severity_values.get(severity, 0)

        return severity_value >= threshold_value
