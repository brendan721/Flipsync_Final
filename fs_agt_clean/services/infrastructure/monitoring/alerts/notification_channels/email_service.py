"""Email notification service implementation."""

import asyncio
import logging
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Protocol, TypedDict

import aiosmtplib
from jinja2 import Environment, PackageLoader, select_autoescape

from fs_agt_clean.core.monitoring.alerts.models import AlertSeverity


class MetricsService(Protocol):
    """Protocol for metrics service implementations."""

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None: ...

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None: ...

    def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None: ...


logger = logging.getLogger(__name__)


class DeliveryStatusInfo(TypedDict):
    """Type definition for delivery status information."""

    status: str
    attempts: int
    last_attempt: Optional[datetime]
    error: Optional[str]


class EmailDeliveryStatus:
    """Email delivery status tracking."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class EmailService:
    """Service for sending email notifications."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_address: str,
        metrics_service: Optional[MetricsService] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        """Initialize email service."""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.metrics = metrics_service
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize Jinja2 template environment
        self.template_env = Environment(
            loader=PackageLoader("fs_agt.core.monitoring.alerts", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Track delivery status
        self._delivery_status: Dict[str, DeliveryStatusInfo] = {}

    async def send_email(
        self,
        to_address: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        severity: AlertSeverity = AlertSeverity.INFO,
        message_id: Optional[str] = None,
    ) -> bool:
        """Send an email using a template."""
        if not message_id:
            message_id = f"email_{datetime.now(timezone.utc).timestamp()}"

        self._delivery_status[message_id] = {
            "status": EmailDeliveryStatus.PENDING,
            "attempts": 0,
            "last_attempt": None,
            "error": None,
        }

        try:
            # Render templates
            html_template = self.template_env.get_template(f"{template_name}.html")
            text_template = self.template_env.get_template(f"{template_name}.txt")

            html_content = html_template.render(**template_data)
            text_content = text_template.render(**template_data)

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_address
            message["To"] = to_address
            message["Message-ID"] = message_id

            # Add text and HTML parts
            message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            # Send with retries
            for attempt in range(self.max_retries):
                try:
                    self._delivery_status[message_id]["attempts"] += 1
                    self._delivery_status[message_id]["last_attempt"] = datetime.now(
                        timezone.utc
                    )

                    async with aiosmtplib.SMTP(
                        hostname=self.smtp_host, port=self.smtp_port, use_tls=True
                    ) as smtp:
                        await smtp.login(self.username, self.password)
                        await smtp.send_message(message)

                    self._delivery_status[message_id][
                        "status"
                    ] = EmailDeliveryStatus.SENT

                    if self.metrics:
                        self.metrics.increment_counter(
                            "email_sent_total",
                            labels={
                                "severity": severity.value,
                                "template": template_name,
                            },
                        )

                    return bool(True)

                except Exception as e:
                    logger.error(
                        "Failed to send email (attempt %s): %s", attempt + 1, e
                    )
                    self._delivery_status[message_id]["error"] = str(e)

                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                    else:
                        self._delivery_status[message_id][
                            "status"
                        ] = EmailDeliveryStatus.FAILED

                        if self.metrics:
                            self.metrics.increment_counter(
                                "email_failed_total",
                                labels={
                                    "severity": severity.value,
                                    "template": template_name,
                                    "error": type(e).__name__,
                                },
                            )

            return False

        except Exception as e:
            logger.error("Error preparing email: %s", e)
            self._delivery_status[message_id]["status"] = EmailDeliveryStatus.FAILED
            self._delivery_status[message_id]["error"] = str(e)

            if self.metrics:
                self.metrics.increment_counter(
                    "email_failed_total",
                    labels={
                        "severity": severity.value,
                        "template": template_name,
                        "error": type(e).__name__,
                    },
                )

            return False

    def get_delivery_status(self, message_id: str) -> Optional[DeliveryStatusInfo]:
        """Get delivery status for a message.

        Args:
            message_id: ID of message to check

        Returns:
            Dict with delivery status info or None if not found
        """
        return self._delivery_status.get(message_id)

    def get_failed_messages(self) -> List[Dict[str, Any]]:
        """Get all failed messages.

        Returns:
            List of message IDs and status info for failed deliveries
        """
        return [
            {"message_id": mid, **status}
            for mid, status in self._delivery_status.items()
            if status["status"] == EmailDeliveryStatus.FAILED
        ]

    def cleanup_old_status(self, max_age_hours: int = 24) -> None:
        """Clean up old delivery status entries.

        Args:
            max_age_hours: Maximum age of entries to keep in hours
        """
        now = datetime.now(timezone.utc)
        self._delivery_status = {
            mid: status
            for mid, status in self._delivery_status.items()
            if status["last_attempt"]
            and (now - status["last_attempt"]).total_seconds() < max_age_hours * 3600
        }
