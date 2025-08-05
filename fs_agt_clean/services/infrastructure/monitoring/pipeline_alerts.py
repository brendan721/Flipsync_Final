"""Pipeline monitoring and alerting system."""

import logging
from typing import Any, Dict, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class NotificationHandler(Protocol):
    """Protocol for notification handlers."""

    async def __call__(self, message: str, data: Dict[str, Any]) -> None:
        """Handle a notification."""
        ...


class PipelineMonitor:
    """Monitor pipeline operations and send alerts."""

    def __init__(self, notification_handler: "NotificationHandler"):
        """Initialize the pipeline monitor.

        Args:
            notification_handler: Function to handle notifications
        """
        self.notification_handler = notification_handler
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, Dict[str, Any]] = {}

    async def log_api_call(self, service: str, duration: float, success: bool) -> None:
        """Log an API call with its duration and success status."""
        if service not in self.metrics:
            self.metrics[service] = {"calls": 0, "failures": 0, "total_duration": 0.0}

        self.metrics[service]["calls"] += 1
        if not success:
            self.metrics[service]["failures"] += 1
        self.metrics[service]["total_duration"] += duration

        await self.notification_handler(
            message=f"API call to {service}",
            data={
                "service": service,
                "duration": duration,
                "success": success,
                "type": "api_call",
                "metrics": self.metrics[service],
            },
        )

    async def log_error(
        self, error_type: str, message: str, context: Dict[str, Any]
    ) -> None:
        """Log an error with context."""
        if "errors" not in self.metrics:
            self.metrics["errors"] = {}
        if error_type not in self.metrics["errors"]:
            self.metrics["errors"][error_type] = 0
        self.metrics["errors"][error_type] += 1

        await self.notification_handler(
            message=f"Error in pipeline: {message}",
            data={
                "error_type": error_type,
                "message": message,
                "context": context,
                "type": "error",
                "metrics": self.metrics["errors"],
            },
        )

    async def log_processing(self, duration: float, success: bool) -> None:
        """Log processing duration and success status."""
        if "processing" not in self.metrics:
            self.metrics["processing"] = {
                "total": 0,
                "successes": 0,
                "failures": 0,
                "total_duration": 0.0,
            }

        metrics = self.metrics["processing"]
        metrics["total"] += 1
        if success:
            metrics["successes"] += 1
        else:
            metrics["failures"] += 1
        metrics["total_duration"] += duration

        await self.notification_handler(
            message="Pipeline processing completed",
            data={
                "duration": duration,
                "success": success,
                "type": "processing",
                "metrics": metrics,
            },
        )
