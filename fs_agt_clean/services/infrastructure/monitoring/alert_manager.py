"""
Alert Manager for Monitoring Services

This module provides alert management functionality for monitoring services,
including alert level definitions, alert creation, and alert routing.
"""

import enum
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class AlertLevel(enum.Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert:
    """Base class for alerts raised by monitoring services."""

    def __init__(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        source: str = "system",
        category: str = "general",
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize an alert.

        Args:
            level: Alert severity level
            title: Short alert title
            message: Detailed alert message
            details: Additional alert details
            source: Alert source (system, service name, etc.)
            category: Alert category
            timestamp: Alert timestamp (defaults to now)
        """
        self.level = level
        self.title = title
        self.message = message
        self.details = details or {}
        self.source = source
        self.category = category
        self.timestamp = timestamp or datetime.utcnow()

    def __str__(self) -> str:
        """Get string representation of the alert."""
        return f"[{self.level.value.upper()}] {self.title}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert alert to a dictionary.

        Returns:
            Dictionary representation of the alert
        """
        return {
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "source": self.source,
            "category": self.category,
            "timestamp": self.timestamp.isoformat(),
        }


class AlertManager:
    """
    Base class for alert management.

    Alert managers are responsible for creating, tracking, and routing alerts
    to appropriate notification channels.
    """

    def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        source: str = "system",
        category: str = "general",
    ) -> None:
        """
        Create and process an alert.

        Args:
            level: Alert severity level
            title: Short alert title
            message: Detailed alert message
            details: Additional alert details
            source: Alert source (system, service name, etc.)
            category: Alert category
        """
        alert = Alert(
            level=level,
            title=title,
            message=message,
            details=details,
            source=source,
            category=category,
        )

        # Log the alert
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical,
        }.get(level, logger.warning)

        log_method(f"Alert: {alert}")

        # Subclasses should override this method to handle the alert
        # (e.g., store in database, send notifications, etc.)


class MultiChannelAlertManager(AlertManager):
    """
    Alert manager that can route alerts to multiple notification channels.

    This implementation supports routing alerts to different channels based on
    alert level, category, and other properties.
    """

    def __init__(self):
        """Initialize the multi-channel alert manager."""
        self.channels = []
        self.alerts: List[Alert] = []
        self.max_stored_alerts = 1000

    def add_channel(
        self,
        channel: Callable[[Alert], None],
        name: str,
        levels: Optional[Set[AlertLevel]] = None,
        categories: Optional[Set[str]] = None,
    ) -> None:
        """
        Add a notification channel.

        Args:
            channel: Channel function that accepts an Alert
            name: Channel name
            levels: Set of alert levels to send to this channel (None = all)
            categories: Set of alert categories to send to this channel (None = all)
        """
        self.channels.append(
            {
                "channel": channel,
                "name": name,
                "levels": levels,
                "categories": categories,
            }
        )

    def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        source: str = "system",
        category: str = "general",
    ) -> None:
        """
        Create and route an alert to appropriate channels.

        Args:
            level: Alert severity level
            title: Short alert title
            message: Detailed alert message
            details: Additional alert details
            source: Alert source (system, service name, etc.)
            category: Alert category
        """
        # Create the alert
        alert = Alert(
            level=level,
            title=title,
            message=message,
            details=details,
            source=source,
            category=category,
        )

        # Log the alert
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical,
        }.get(level, logger.warning)

        log_method(f"Alert: {alert}")

        # Store the alert
        self.alerts.append(alert)

        # Trim old alerts if necessary
        if len(self.alerts) > self.max_stored_alerts:
            self.alerts = self.alerts[-self.max_stored_alerts :]

        # Route to channels
        for channel_config in self.channels:
            # Check if the channel should receive this alert
            should_route = True

            if channel_config.get("levels") is not None:
                if alert.level not in channel_config["levels"]:
                    should_route = False

            if channel_config.get("categories") is not None:
                if alert.category not in channel_config["categories"]:
                    should_route = False

            if should_route:
                try:
                    channel_config["channel"](alert)
                except Exception as e:
                    logger.error(
                        f"Error sending alert to channel {channel_config['name']}: {str(e)}"
                    )

    def get_recent_alerts(
        self,
        limit: int = 100,
        level: Optional[AlertLevel] = None,
        category: Optional[str] = None,
    ) -> List[Alert]:
        """
        Get recent alerts, optionally filtered by level or category.

        Args:
            limit: Maximum number of alerts to return
            level: Optional filter by alert level
            category: Optional filter by alert category

        Returns:
            List of recent alerts
        """
        filtered_alerts = self.alerts

        if level is not None:
            filtered_alerts = [a for a in filtered_alerts if a.level == level]

        if category is not None:
            filtered_alerts = [a for a in filtered_alerts if a.category == category]

        # Return most recent alerts first
        return list(sorted(filtered_alerts, key=lambda a: a.timestamp)[:limit])
