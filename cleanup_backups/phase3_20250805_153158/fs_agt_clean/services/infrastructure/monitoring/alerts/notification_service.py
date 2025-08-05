"""Notification service implementation."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.monitoring.alerts.models import AlertSeverity
from fs_agt_clean.core.monitoring.alerts.notification_channels.email_service import (
    EmailService,
)
from fs_agt_clean.core.monitoring.alerts.notification_channels.sms_service import (
    SMSService,
)
from fs_agt_clean.core.monitoring.protocols import MetricsService
from fs_agt_clean.core.redis.redis_manager import RedisManager

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications through multiple channels."""

    def __init__(
        self,
        email_config: Dict[str, Any],
        sms_config: Dict[str, Any],
        redis_manager: RedisManager,
        metrics_service: Optional[MetricsService] = None,
    ):
        """Initialize notification service.

        Args:
            email_config: Email service configuration
            sms_config: SMS service configuration
            redis_manager: Redis manager instance
            metrics_service: Optional metrics service
        """
        self.email_service = EmailService(
            smtp_host=email_config["smtp_host"],
            smtp_port=email_config["smtp_port"],
            username=email_config["username"],
            password=email_config["password"],
            from_address=email_config["from_address"],
            metrics_service=metrics_service,
        )

        self.sms_service = SMSService(
            account_sid=sms_config["account_sid"],
            auth_token=sms_config["auth_token"],
            from_number=sms_config["from_number"],
            redis_manager=redis_manager,
            metrics_service=metrics_service,
        )

        self.metrics = metrics_service

    async def initialize(self) -> None:
        """Initialize notification channels."""
        await self.sms_service.initialize()

    async def send_alert(
        self,
        alert_id: str,
        severity: AlertSeverity,
        metric_name: str,
        value: float,
        threshold: float,
        component: str,
        email_recipients: List[str],
        sms_recipients: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """Send alert through configured channels.

        Args:
            alert_id: Unique alert identifier
            severity: Alert severity level
            metric_name: Name of metric that triggered alert
            value: Current metric value
            threshold: Threshold that was exceeded
            component: Component that triggered the alert
            email_recipients: List of email addresses to notify
            sms_recipients: Optional list of phone numbers for SMS

        Returns:
            Dict with status of each channel (email, sms)
        """
        timestamp = datetime.now(timezone.utc)
        template_data = {
            "metric_name": metric_name,
            "value": value,
            "threshold": threshold,
            "component": component,
            "timestamp": timestamp,
            "alert_id": alert_id,
        }

        # Track results
        results = {"email": False, "sms": False}

        # Send emails
        for recipient in email_recipients:
            email_id = f"{alert_id}_email_{recipient}"
            success = await self.email_service.send_email(
                to_address=recipient,
                subject=f"{severity.value.upper()} Alert: {metric_name} in {component}",
                template_name="critical_alert",  # TODO: Use different templates based on severity
                template_data=template_data,
                severity=severity,
                message_id=email_id,
            )
            results["email"] |= success

        # Send SMS if configured
        if sms_recipients:
            message = (
                f"{severity.value.upper()} Alert: {metric_name} in {component}\n"
                f"Value: {value} (threshold: {threshold})\n"
                f"Alert ID: {alert_id}"
            )

            for recipient in sms_recipients:
                sms_id = f"{alert_id}_sms_{recipient}"
                success = await self.sms_service.send_sms(
                    to_number=recipient,
                    message=message,
                    severity=severity,
                    message_id=sms_id,
                    template_data=template_data,
                )
                results["sms"] |= success

        # Track metrics
        if self.metrics:
            self.metrics.increment_counter(
                "notifications_sent_total",
                labels={
                    "severity": severity.value,
                    "email_success": str(results["email"]).lower(),
                    "sms_success": str(results["sms"]).lower(),
                },
            )

        return results

    def get_failed_notifications(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get list of failed notifications from all channels.

        Returns:
            Dict with failed notifications by channel
        """
        return {
            "email": self.email_service.get_failed_messages(),
            "sms": self.sms_service.get_failed_messages(),
        }

    def cleanup_old_status(self, max_age_hours: int = 24) -> None:
        """Clean up old delivery status entries from all channels.

        Args:
            max_age_hours: Maximum age of entries to keep in hours
        """
        self.email_service.cleanup_old_status(max_age_hours)
        self.sms_service.cleanup_old_status(max_age_hours)
