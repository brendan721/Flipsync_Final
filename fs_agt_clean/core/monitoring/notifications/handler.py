"""Notification handler for monitoring.

This module provides the handler class for sending notifications.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fs_agt_clean.core.monitoring.notifications.config import (
    AlertSeverity,
    NotificationChannel,
    NotificationConfig,
)
from fs_agt_clean.core.monitoring.notifications.models import Alert, Notification

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Handles sending notifications through configured channels."""

    def __init__(self, config: NotificationConfig):
        """Initialize notification handler.

        Args:
            config: Notification configuration
        """
        self.config = config
        self._last_notification: Dict[str, datetime] = {}
        self._notification_count: Dict[str, int] = {}
        self._cooldown_until: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        self.logger = logger

    async def notify(self, alert: Alert) -> Optional[Notification]:
        """Send notification for an alert.

        Args:
            alert: Alert to send notification for

        Returns:
            Notification object if sent, None otherwise
        """
        # Check if notifications are enabled
        if not self.config.enabled:
            self.logger.debug(
                "Notifications are disabled, skipping alert: %s", alert.title
            )
            return None

        # Check severity threshold
        if not self.config.should_notify(alert.severity):
            self.logger.debug(
                "Alert severity %s below threshold %s, skipping: %s",
                alert.severity,
                self.config.severity_threshold,
                alert.title,
            )
            return None

        # Check rate limiting
        async with self._lock:
            if not self._should_send(alert):
                return None

            # Create notification
            notification = Notification(alert=alert)

            # Update rate limiting counters
            component_key = f"{alert.component}:{alert.severity}"
            self._last_notification[component_key] = datetime.now(timezone.utc)
            self._notification_count[component_key] = (
                self._notification_count.get(component_key, 0) + 1
            )

            # Check if we need to enter cooldown
            if (
                self.config.rate_limit
                and self._notification_count.get(component_key, 0)
                >= self.config.rate_limit.max_notifications
            ):
                self._cooldown_until[component_key] = datetime.now(
                    timezone.utc
                ).replace(microsecond=0) + asyncio.timedelta(
                    seconds=self.config.rate_limit.cooldown_seconds
                )
                self.logger.warning(
                    "Rate limit reached for %s:%s, entering cooldown until %s",
                    alert.component,
                    alert.severity,
                    self._cooldown_until[component_key],
                )

        # Send to all enabled channels
        channels_sent = []
        for channel in self.config.channels:
            if self.config.is_channel_enabled(channel):
                try:
                    await self._send_to_channel(channel, notification)
                    channels_sent.append(channel)
                except Exception as e:
                    self.logger.error(
                        "Failed to send notification to %s: %s", channel, str(e)
                    )

        if channels_sent:
            notification.mark_as_sent()
            self.logger.info(
                "Sent notification for alert: %s [%s] via %s",
                alert.title,
                alert.severity,
                ", ".join([c.value for c in channels_sent]),
            )
            return notification
        else:
            self.logger.warning(
                "Failed to send notification for alert: %s [%s]",
                alert.title,
                alert.severity,
            )
            notification.mark_as_failed()
            return None

    def _should_send(self, alert: Alert) -> bool:
        """Check if notification should be sent based on rate limit.

        Args:
            alert: Alert to check

        Returns:
            True if notification should be sent, False otherwise
        """
        if not self.config.rate_limit:
            return True

        component_key = f"{alert.component}:{alert.severity}"

        # Check if in cooldown
        cooldown_until = self._cooldown_until.get(component_key)
        if cooldown_until and datetime.now(timezone.utc) < cooldown_until:
            self.logger.debug(
                "In cooldown for %s:%s until %s, skipping alert: %s",
                alert.component,
                alert.severity,
                cooldown_until,
                alert.title,
            )
            return False

        # Check interval
        last_sent = self._last_notification.get(component_key)
        if last_sent:
            time_since_last = (datetime.now(timezone.utc) - last_sent).total_seconds()
            if time_since_last < self.config.rate_limit.interval_seconds:
                self.logger.debug(
                    "Rate limited for %s:%s, last sent %d seconds ago, skipping alert: %s",
                    alert.component,
                    alert.severity,
                    time_since_last,
                    alert.title,
                )
                return False

        # Reset notification count if out of cooldown and interval
        if cooldown_until and datetime.now(timezone.utc) >= cooldown_until:
            self._notification_count[component_key] = 0
            del self._cooldown_until[component_key]

        return True

    async def _send_to_channel(
        self, channel: NotificationChannel, notification: Notification
    ):
        """Send to specific notification channel.

        Args:
            channel: Channel to send to
            notification: Notification to send
        """
        if channel == NotificationChannel.EMAIL:
            await self._send_email(notification)
        elif channel == NotificationChannel.SLACK:
            await self._send_slack(notification)
        elif channel == NotificationChannel.SMS:
            await self._send_sms(notification)
        elif channel == NotificationChannel.WEBHOOK:
            await self._send_webhook(notification)

    async def _send_email(self, notification: Notification):
        """Send email notification.

        Args:
            notification: Notification to send
        """
        if not self.config.channel_config.email.enabled:
            return

        # Add recipients to notification
        notification.recipients.extend(self.config.channel_config.email.recipients)

        # In a real implementation, this would send an email
        self.logger.debug(
            "Would send email notification to %s: %s",
            self.config.channel_config.email.recipients,
            notification.alert.title,
        )

    async def _send_slack(self, notification: Notification):
        """Send Slack notification.

        Args:
            notification: Notification to send
        """
        if not self.config.channel_config.slack.enabled:
            return

        # In a real implementation, this would send a Slack message
        self.logger.debug(
            "Would send Slack notification to %s: %s",
            self.config.channel_config.slack.channel or "default channel",
            notification.alert.title,
        )

    async def _send_sms(self, notification: Notification):
        """Send SMS notification.

        Args:
            notification: Notification to send
        """
        if not self.config.channel_config.sms.enabled:
            return

        # Add recipients to notification
        notification.recipients.extend(self.config.channel_config.sms.to_numbers)

        # In a real implementation, this would send an SMS
        self.logger.debug(
            "Would send SMS notification to %s: %s",
            self.config.channel_config.sms.to_numbers,
            notification.alert.title,
        )

    async def _send_webhook(self, notification: Notification):
        """Send webhook notification.

        Args:
            notification: Notification to send
        """
        if not self.config.channel_config.webhook.enabled:
            return

        # In a real implementation, this would send a webhook request
        self.logger.debug(
            "Would send webhook notification to %s: %s",
            self.config.channel_config.webhook.url,
            notification.alert.title,
        )
