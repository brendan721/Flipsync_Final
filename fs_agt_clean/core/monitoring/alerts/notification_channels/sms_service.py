"""SMS notification service implementation using Twilio."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, TypedDict, cast

try:
    from twilio.base.exceptions import TwilioRestException
    from twilio.rest import Client
    from twilio.rest.api.v2010.account.message import MessageInstance

    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioRestException = Exception
    Client = None
    MessageInstance = None

from fs_agt_clean.core.monitoring.alerts.models import AlertSeverity
from fs_agt_clean.core.redis.redis_manager import RedisManager
from fs_agt_clean.core.security.rate_limiter import RateLimitConfig, RateLimiter


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
    delivery_info: Optional[Dict[str, Any]]


class SMSDeliveryStatus:
    """SMS delivery status tracking."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class SMSService:
    """Service for sending SMS notifications using Twilio."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        redis_manager: RedisManager,
        metrics_service: Optional[MetricsService] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
        rate_limit_per_minute: int = 30,
    ):
        """Initialize SMS service."""
        if not TWILIO_AVAILABLE:
            logger.warning("Twilio not available - SMS service will be disabled")
            self.client = None
            self.enabled = False
        else:
            self.client = Client(account_sid, auth_token)
            self.enabled = True

        self.from_number = from_number
        self.metrics = metrics_service
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            redis=redis_manager,
            config={
                "sms": RateLimitConfig(
                    requests=rate_limit_per_minute,
                    window=60,  # 1 minute in seconds
                    key_prefix="sms_rate_limit",
                )
            },
        )

        # Track delivery status
        self._delivery_status: Dict[str, DeliveryStatusInfo] = {}

    async def initialize(self) -> None:
        """Initialize the service."""
        await self.rate_limiter.initialize()

    async def send_sms(
        self,
        to_number: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        message_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send an SMS message."""
        if not self.enabled:
            logger.warning("SMS service is disabled - skipping SMS send")
            return False

        if not message_id:
            message_id = f"sms_{datetime.now(timezone.utc).timestamp()}"

        # Check rate limit
        is_allowed, _ = await self.rate_limiter.is_allowed("sms", "send")
        if not is_allowed:
            logger.warning("SMS rate limit exceeded")
            if self.metrics:
                self.metrics.increment_counter(
                    "sms_rate_limited_total", labels={"severity": severity.value}
                )
            return bool(False)

        self._delivery_status[message_id] = {
            "status": SMSDeliveryStatus.PENDING,
            "attempts": 0,
            "last_attempt": None,
            "error": None,
            "delivery_info": None,
        }

        # Format phone number
        to_number = self._format_phone_number(to_number)

        for attempt in range(self.max_retries):
            try:
                self._delivery_status[message_id]["attempts"] += 1
                self._delivery_status[message_id]["last_attempt"] = datetime.now(
                    timezone.utc
                )

                # Send message through Twilio
                twilio_message: MessageInstance = await asyncio.to_thread(
                    self.client.messages.create,
                    to=to_number,
                    from_=self.from_number,
                    body=message,
                    status_callback=None,  # TODO: Add webhook for delivery updates
                )

                self._delivery_status[message_id].update(
                    {
                        "status": SMSDeliveryStatus.SENT,
                        "delivery_info": {
                            "twilio_sid": twilio_message.sid,
                            "status": twilio_message.status,
                            "price": twilio_message.price,
                            "sent_at": datetime.now(timezone.utc),
                        },
                    }
                )

                if self.metrics:
                    self.metrics.increment_counter(
                        "sms_sent_total",
                        labels={
                            "severity": severity.value,
                            "status": twilio_message.status,
                        },
                    )

                return True

            except TwilioRestException as e:
                logger.error("Twilio error (attempt %s): %s", attempt + 1, e)
                self._delivery_status[message_id]["error"] = str(e)

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self._delivery_status[message_id][
                        "status"
                    ] = SMSDeliveryStatus.FAILED
                    if self.metrics:
                        self.metrics.increment_counter(
                            "sms_failed_total",
                            labels={
                                "severity": severity.value,
                                "error": type(e).__name__,
                            },
                        )

            except Exception as e:
                logger.error("Error sending SMS (attempt %s): %s", attempt + 1, e)
                self._delivery_status[message_id]["error"] = str(e)

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self._delivery_status[message_id][
                        "status"
                    ] = SMSDeliveryStatus.FAILED
                    if self.metrics:
                        self.metrics.increment_counter(
                            "sms_failed_total",
                            labels={
                                "severity": severity.value,
                                "error": type(e).__name__,
                            },
                        )

        return False

    def _format_phone_number(self, number: str) -> str:
        """Format phone number for Twilio.

        Args:
            number: Phone number to format

        Returns:
            Formatted phone number
        """
        # Remove any non-numeric characters
        cleaned = "".join(filter(str.isdigit, number))

        # Add + prefix if not present
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned

        return cleaned

    def get_delivery_status(self, message_id: str) -> Optional[DeliveryStatusInfo]:
        """Get delivery status for a message.

        Args:
            message_id: ID of message to check

        Returns:
            Dict with delivery status info or None if not found
        """
        return self._delivery_status.get(message_id)

    async def update_delivery_status(self, message_id: str, status: str) -> None:
        """Update delivery status for a specific message.

        Args:
            message_id: The message ID to update
            status: New status value
        """
        if message_id in self._delivery_status:
            delivery_info = cast(
                Dict[str, Any],
                self._delivery_status[message_id].get("delivery_info", {}),
            )
            self._delivery_status[message_id].update(
                {
                    "status": (
                        SMSDeliveryStatus.DELIVERED if status == "delivered" else status
                    ),
                    "delivery_info": {
                        **delivery_info,
                        "status": status,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                }
            )

            if self.metrics and status == "delivered":
                self.metrics.increment_counter(
                    "sms_delivered_total",
                    labels={"severity": "unknown"},  # Original severity not available
                )

    def get_failed_messages(self) -> List[Dict[str, Any]]:
        """Get list of failed messages.

        Returns:
            List of message IDs and status info for failed deliveries
        """
        return [
            {"message_id": mid, **status}
            for mid, status in self._delivery_status.items()
            if status["status"] == SMSDeliveryStatus.FAILED
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
