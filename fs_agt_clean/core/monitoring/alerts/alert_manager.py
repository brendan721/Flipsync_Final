"""
Alert manager implementation for FlipSync.

This module provides a comprehensive alert management system that supports:
- Different alert levels and categories
- Alert routing to different channels
- Alert deduplication and rate limiting
- Mobile-specific optimizations
- Integration with notification systems

It serves as the foundation for specialized alert management like
agent interaction alerts, conversational quality alerts, and decision
intelligence alerts.
"""

import asyncio
import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.monitoring.logger import get_logger

# Default values
DEFAULT_ALERT_HISTORY_SIZE = 1000  # Number of alerts to keep in memory
DEFAULT_DEDUP_WINDOW = 300  # 5 minutes in seconds
DEFAULT_RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
DEFAULT_MAX_ALERTS_PER_WINDOW = 10  # Maximum alerts per rate limit window
DEFAULT_STORAGE_PATH = "data/alerts"


class AlertLevel(Enum):
    """Alert levels with descriptions."""

    INFO = "info"  # Informational alerts
    WARNING = "warning"  # Warning alerts
    ERROR = "error"  # Error alerts
    CRITICAL = "critical"  # Critical alerts


class AlertCategory(Enum):
    """Alert categories with descriptions."""

    SYSTEM = "system"  # System alerts (CPU, memory, etc.)
    PERFORMANCE = "performance"  # Performance alerts (latency, etc.)
    SECURITY = "security"  # Security alerts (login attempts, etc.)
    BUSINESS = "business"  # Business alerts (revenue, users, etc.)
    AGENT = "agent"  # UnifiedAgent-specific alerts
    CONVERSATION = "conversation"  # Conversation quality alerts
    DECISION = "decision"  # Decision intelligence alerts
    MOBILE = "mobile"  # Mobile-specific alerts


class AlertSource(Enum):
    """Alert sources with descriptions."""

    SYSTEM = "system"  # System-generated alerts
    USER = "user"  # UnifiedUser-generated alerts
    AGENT = "agent"  # UnifiedAgent-generated alerts
    MONITORING = "monitoring"  # Monitoring-generated alerts
    SECURITY = "security"  # Security-generated alerts


class Alert:
    """An alert notification."""

    def __init__(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        category: AlertCategory = AlertCategory.SYSTEM,
        source: AlertSource = AlertSource.SYSTEM,
        details: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
        alert_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        """
        Initialize an alert.

        Args:
            title: Alert title
            message: Alert message
            level: Alert level
            category: Alert category
            source: Alert source
            details: Optional alert details
            labels: Optional alert labels
            timestamp: Optional timestamp (defaults to now)
            alert_id: Optional alert ID (defaults to UUID)
            correlation_id: Optional correlation ID for tracking
        """
        self.title = title
        self.message = message
        self.level = level
        self.category = category
        self.source = source
        self.details = details or {}
        self.labels = labels or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.alert_id = alert_id or str(uuid.uuid4())
        self.correlation_id = correlation_id
        self.acknowledged = False
        self.acknowledged_time = None
        self.acknowledged_by = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "level": self.level.value,
            "category": self.category.value,
            "source": self.source.value,
            "details": self.details,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "acknowledged": self.acknowledged,
            "acknowledged_time": (
                self.acknowledged_time.isoformat() if self.acknowledged_time else None
            ),
            "acknowledged_by": self.acknowledged_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alert":
        """
        Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Alert instance
        """
        alert = cls(
            title=data["title"],
            message=data["message"],
            level=AlertLevel(data["level"]),
            category=AlertCategory(data["category"]),
            source=AlertSource(data["source"]),
            details=data["details"],
            labels=data["labels"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            alert_id=data["alert_id"],
            correlation_id=data.get("correlation_id"),
        )
        alert.acknowledged = data.get("acknowledged", False)
        if data.get("acknowledged_time"):
            alert.acknowledged_time = datetime.fromisoformat(data["acknowledged_time"])
        alert.acknowledged_by = data.get("acknowledged_by")
        return alert

    def acknowledge(self, user: Optional[str] = None) -> None:
        """
        Acknowledge the alert.

        Args:
            user: UnifiedUser who acknowledged the alert
        """
        self.acknowledged = True
        self.acknowledged_time = datetime.now(timezone.utc)
        self.acknowledged_by = user

    def get_fingerprint(self) -> str:
        """
        Get a fingerprint for deduplication.

        Returns:
            Alert fingerprint
        """
        # Create a fingerprint based on title, message, level, and category
        return f"{self.title}:{self.message}:{self.level.value}:{self.category.value}"


class AlertChannel:
    """A channel for sending alerts."""

    def __init__(
        self,
        name: str,
        send_func: Callable[[Alert], None],
        levels: Optional[Set[AlertLevel]] = None,
        categories: Optional[Set[AlertCategory]] = None,
    ):
        """
        Initialize an alert channel.

        Args:
            name: Channel name
            send_func: Function to send alerts
            levels: Optional set of levels to send (None = all)
            categories: Optional set of categories to send (None = all)
        """
        self.name = name
        self.send_func = send_func
        self.levels = levels
        self.categories = categories

    def should_send(self, alert: Alert) -> bool:
        """
        Check if alert should be sent to this channel.

        Args:
            alert: Alert to check

        Returns:
            True if alert should be sent, False otherwise
        """
        if self.levels and alert.level not in self.levels:
            return False
        if self.categories and alert.category not in self.categories:
            return False
        return True

    def send(self, alert: Alert) -> None:
        """
        Send alert to this channel.

        Args:
            alert: Alert to send
        """
        if self.should_send(alert):
            self.send_func(alert)


class AlertManager:
    """
    Manages alerts with mobile and vision awareness.

    This class provides a centralized alert management system that supports:
    - Different alert levels and categories
    - Alert routing to different channels
    - Alert deduplication and rate limiting
    - Mobile-specific optimizations
    - Integration with notification systems

    It serves as the foundation for specialized alert management.
    """

    _instance = None
    _lock = threading.RLock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AlertManager, cls).__new__(cls)
            return cls._instance

    def __init__(
        self,
        service_name: str = "default",
        max_history_size: int = DEFAULT_ALERT_HISTORY_SIZE,
        dedup_window: int = DEFAULT_DEDUP_WINDOW,
        rate_limit_window: int = DEFAULT_RATE_LIMIT_WINDOW,
        max_alerts_per_window: int = DEFAULT_MAX_ALERTS_PER_WINDOW,
        storage_path: Optional[Union[str, Path]] = None,
        mobile_optimized: bool = False,
    ):
        """
        Initialize alert manager.

        Args:
            service_name: Name of the service
            max_history_size: Maximum number of alerts to keep in memory
            dedup_window: Window for deduplication in seconds
            rate_limit_window: Window for rate limiting in seconds
            max_alerts_per_window: Maximum alerts per rate limit window
            storage_path: Path to store alerts
            mobile_optimized: Whether to optimize for mobile environments
        """
        with self._lock:
            if self._initialized:
                return

            self.logger = get_logger(__name__)
            self.service_name = service_name
            self.max_history_size = max_history_size
            self.dedup_window = dedup_window
            self.rate_limit_window = rate_limit_window
            self.max_alerts_per_window = max_alerts_per_window
            self.mobile_optimized = mobile_optimized

            # Set up storage path
            self.storage_path = (
                Path(storage_path) if storage_path else Path(DEFAULT_STORAGE_PATH)
            )
            os.makedirs(self.storage_path, exist_ok=True)

            # Initialize alert storage
            self.active_alerts: Dict[str, Alert] = {}  # alert_id -> alert
            self.alert_history: List[Alert] = []  # All alerts
            self.alert_fingerprints: Dict[str, datetime] = (
                {}
            )  # fingerprint -> last time
            self.alert_counts: Dict[str, int] = (
                {}
            )  # fingerprint -> count in rate limit window
            self.channels: List[AlertChannel] = []  # Alert channels
            self.thresholds: Dict[str, Tuple[float, float]] = (
                {}
            )  # metric_name -> (warning, critical)

            # Initialize async lock
            self._async_lock = asyncio.Lock()

            # Add default channels
            self._add_default_channels()

            self._initialized = True

    def _add_default_channels(self) -> None:
        """Add default alert channels."""
        # Add console channel
        self.add_channel(
            name="console",
            send_func=self._send_to_console,
        )

        # Add log channel
        self.add_channel(
            name="log",
            send_func=self._send_to_log,
        )

    def _send_to_console(self, alert: Alert) -> None:
        """
        Send alert to console.

        Args:
            alert: Alert to send
        """
        level_colors = {
            AlertLevel.INFO: "\033[94m",  # Blue
            AlertLevel.WARNING: "\033[93m",  # Yellow
            AlertLevel.ERROR: "\033[91m",  # Red
            AlertLevel.CRITICAL: "\033[91;1m",  # Bold Red
        }
        reset_color = "\033[0m"

        color = level_colors.get(alert.level, "")
        print(
            f"{color}[{alert.level.value.upper()}] {alert.title}: {alert.message}{reset_color}"
        )

    def _send_to_log(self, alert: Alert) -> None:
        """
        Send alert to log.

        Args:
            alert: Alert to send
        """
        log_levels = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }

        log_level = log_levels.get(alert.level, logging.INFO)
        self.logger.log(
            log_level, f"[{alert.category.value}] {alert.title}: {alert.message}"
        )

    def add_channel(
        self,
        name: str,
        send_func: Callable[[Alert], None],
        levels: Optional[Set[AlertLevel]] = None,
        categories: Optional[Set[AlertCategory]] = None,
    ) -> None:
        """
        Add an alert channel.

        Args:
            name: Channel name
            send_func: Function to send alerts
            levels: Optional set of levels to send (None = all)
            categories: Optional set of categories to send (None = all)
        """
        with self._lock:
            channel = AlertChannel(
                name=name,
                send_func=send_func,
                levels=levels,
                categories=categories,
            )
            self.channels.append(channel)
            self.logger.info(f"Added alert channel: {name}")

    def remove_channel(self, name: str) -> bool:
        """
        Remove an alert channel.

        Args:
            name: Channel name

        Returns:
            True if channel was removed, False otherwise
        """
        with self._lock:
            for i, channel in enumerate(self.channels):
                if channel.name == name:
                    self.channels.pop(i)
                    self.logger.info(f"Removed alert channel: {name}")
                    return True
            return False

    async def set_threshold(
        self, metric_name: str, warning_threshold: float, critical_threshold: float
    ) -> None:
        """
        Set thresholds for a metric.

        Args:
            metric_name: Metric name
            warning_threshold: Warning threshold
            critical_threshold: Critical threshold
        """
        async with self._async_lock:
            self.thresholds[metric_name] = (warning_threshold, critical_threshold)
            self.logger.info(
                f"Set thresholds for {metric_name}: warning={warning_threshold}, critical={critical_threshold}"
            )

    async def clear_threshold(self, metric_name: str) -> bool:
        """
        Clear thresholds for a metric.

        Args:
            metric_name: Metric name

        Returns:
            True if thresholds were cleared, False otherwise
        """
        async with self._async_lock:
            if metric_name in self.thresholds:
                del self.thresholds[metric_name]
                self.logger.info(f"Cleared thresholds for {metric_name}")
                return True
            return False

    async def process_metric(self, metric_name: str, value: float) -> None:
        """
        Process a metric and generate alerts if needed.

        Args:
            metric_name: Metric name
            value: Metric value
        """
        async with self._async_lock:
            if metric_name in self.thresholds:
                warning_threshold, critical_threshold = self.thresholds[metric_name]

                if value >= critical_threshold:
                    await self.create_alert(
                        title=f"{metric_name} exceeded critical threshold",
                        message=f"{metric_name} value {value} exceeded critical threshold {critical_threshold}",
                        level=AlertLevel.CRITICAL,
                        category=AlertCategory.PERFORMANCE,
                        source=AlertSource.MONITORING,
                        details={
                            "metric_name": metric_name,
                            "value": value,
                            "threshold": critical_threshold,
                            "threshold_type": "critical",
                        },
                    )
                elif value >= warning_threshold:
                    await self.create_alert(
                        title=f"{metric_name} exceeded warning threshold",
                        message=f"{metric_name} value {value} exceeded warning threshold {warning_threshold}",
                        level=AlertLevel.WARNING,
                        category=AlertCategory.PERFORMANCE,
                        source=AlertSource.MONITORING,
                        details={
                            "metric_name": metric_name,
                            "value": value,
                            "threshold": warning_threshold,
                            "threshold_type": "warning",
                        },
                    )

    async def create_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        category: AlertCategory = AlertCategory.SYSTEM,
        source: AlertSource = AlertSource.SYSTEM,
        details: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[Alert]:
        """
        Create and process an alert.

        Args:
            title: Alert title
            message: Alert message
            level: Alert level
            category: Alert category
            source: Alert source
            details: Optional alert details
            labels: Optional alert labels
            correlation_id: Optional correlation ID for tracking

        Returns:
            Created alert if processed, None if deduplicated or rate limited
        """
        # Create alert
        alert = Alert(
            title=title,
            message=message,
            level=level,
            category=category,
            source=source,
            details=details,
            labels=labels,
            correlation_id=correlation_id,
        )

        # Process alert
        return await self.process_alert(alert)

    async def process_alert(self, alert: Alert) -> Optional[Alert]:
        """
        Process an alert.

        Args:
            alert: Alert to process

        Returns:
            Processed alert if not deduplicated or rate limited, None otherwise
        """
        async with self._async_lock:
            # Check for deduplication
            if await self._is_duplicate(alert):
                self.logger.debug(f"Deduplicated alert: {alert.title}")
                return None

            # Check for rate limiting
            if not await self._check_rate_limit(alert):
                self.logger.debug(f"Rate limited alert: {alert.title}")
                return None

            # Store alert
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)

            # Trim history if needed
            if len(self.alert_history) > self.max_history_size:
                self.alert_history = self.alert_history[-self.max_history_size :]

            # Send to channels
            for channel in self.channels:
                try:
                    channel.send(alert)
                except Exception as e:
                    self.logger.error(
                        f"Error sending alert to channel {channel.name}: {e}"
                    )

            # Store alert
            await self._store_alert(alert)

            return alert

    async def _is_duplicate(self, alert: Alert) -> bool:
        """
        Check if alert is a duplicate.

        Args:
            alert: Alert to check

        Returns:
            True if alert is a duplicate, False otherwise
        """
        fingerprint = alert.get_fingerprint()
        now = datetime.now(timezone.utc)

        if fingerprint in self.alert_fingerprints:
            last_time = self.alert_fingerprints[fingerprint]
            if now - last_time < timedelta(seconds=self.dedup_window):
                return True

        self.alert_fingerprints[fingerprint] = now
        return False

    async def _check_rate_limit(self, alert: Alert) -> bool:
        """
        Check if alert is rate limited.

        Args:
            alert: Alert to check

        Returns:
            True if alert is not rate limited, False otherwise
        """
        fingerprint = alert.get_fingerprint()
        now = datetime.now(timezone.utc)

        # Clean up old fingerprints
        for fp, last_time in list(self.alert_fingerprints.items()):
            if now - last_time > timedelta(seconds=self.rate_limit_window):
                del self.alert_fingerprints[fp]
                if fp in self.alert_counts:
                    del self.alert_counts[fp]

        # Check rate limit
        count = self.alert_counts.get(fingerprint, 0)
        if count >= self.max_alerts_per_window:
            return False

        # Increment count
        self.alert_counts[fingerprint] = count + 1
        return True

    async def _store_alert(self, alert: Alert) -> None:
        """
        Store alert to disk.

        Args:
            alert: Alert to store
        """
        if self.mobile_optimized:
            # In mobile mode, we batch alerts for storage
            return

        # Store alert
        filename = f"{self.service_name}_{alert.timestamp.strftime('%Y%m%d')}.json"
        filepath = self.storage_path / filename

        # Append to file
        with open(filepath, "a") as f:
            f.write(json.dumps(alert.to_dict()) + "\n")

    async def get_active_alerts(
        self,
        level: Optional[AlertLevel] = None,
        category: Optional[AlertCategory] = None,
        source: Optional[AlertSource] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Alert]:
        """
        Get active alerts with optional filtering.

        Args:
            level: Optional level filter
            category: Optional category filter
            source: Optional source filter
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of matching active alerts
        """
        async with self._async_lock:
            alerts = list(self.active_alerts.values())

            # Apply filters
            if level:
                alerts = [a for a in alerts if a.level == level]
            if category:
                alerts = [a for a in alerts if a.category == category]
            if source:
                alerts = [a for a in alerts if a.source == source]
            if start_time:
                alerts = [a for a in alerts if a.timestamp >= start_time]
            if end_time:
                alerts = [a for a in alerts if a.timestamp <= end_time]

            return alerts

    async def get_alert_history(
        self,
        level: Optional[AlertLevel] = None,
        category: Optional[AlertCategory] = None,
        source: Optional[AlertSource] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Alert]:
        """
        Get alert history with optional filtering.

        Args:
            level: Optional level filter
            category: Optional category filter
            source: Optional source filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Optional limit on number of alerts

        Returns:
            List of matching alerts from history
        """
        async with self._async_lock:
            alerts = self.alert_history.copy()

            # Apply filters
            if level:
                alerts = [a for a in alerts if a.level == level]
            if category:
                alerts = [a for a in alerts if a.category == category]
            if source:
                alerts = [a for a in alerts if a.source == source]
            if start_time:
                alerts = [a for a in alerts if a.timestamp >= start_time]
            if end_time:
                alerts = [a for a in alerts if a.timestamp <= end_time]

            # Sort by timestamp (newest first)
            alerts.sort(key=lambda a: a.timestamp, reverse=True)

            # Apply limit
            if limit:
                alerts = alerts[:limit]

            return alerts

    async def acknowledge_alert(
        self, alert_id: str, user: Optional[str] = None
    ) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID
            user: UnifiedUser who acknowledged the alert

        Returns:
            True if alert was acknowledged, False otherwise
        """
        async with self._async_lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.acknowledge(user)

                # Remove from active alerts
                del self.active_alerts[alert_id]

                self.logger.info(f"Alert {alert_id} acknowledged by {user}")
                return True
            return False

    async def clear_alerts(self) -> None:
        """Clear all alerts."""
        async with self._async_lock:
            self.active_alerts.clear()
            self.alert_history.clear()
            self.alert_fingerprints.clear()
            self.alert_counts.clear()
            self.logger.info("Cleared all alerts")

    async def export_alerts(
        self, format: str = "json", destination: Optional[Union[str, Path]] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Export alerts in various formats.

        Args:
            format: Export format (json, html, etc.)
            destination: Optional file destination

        Returns:
            Exported alerts as string or dictionary
        """
        async with self._async_lock:
            if format == "json":
                # Convert alerts to JSON
                alerts_data = [a.to_dict() for a in self.alert_history]

                # Write to file if destination provided
                if destination:
                    path = Path(destination)
                    with open(path, "w") as f:
                        json.dump(alerts_data, f, indent=2)

                return alerts_data
            elif format == "html":
                # Convert alerts to HTML
                html = "<html><head><title>Alerts</title></head><body>"
                html += "<h1>Alerts</h1>"
                html += "<table border='1'>"
                html += "<tr><th>Time</th><th>Level</th><th>Category</th><th>Title</th><th>Message</th></tr>"

                for alert in sorted(
                    self.alert_history, key=lambda a: a.timestamp, reverse=True
                ):
                    level_colors = {
                        AlertLevel.INFO: "#0000FF",  # Blue
                        AlertLevel.WARNING: "#FFA500",  # Orange
                        AlertLevel.ERROR: "#FF0000",  # Red
                        AlertLevel.CRITICAL: "#8B0000",  # Dark Red
                    }
                    color = level_colors.get(alert.level, "#000000")

                    html += f"<tr>"
                    html += f"<td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>"
                    html += (
                        f"<td style='color: {color}'>{alert.level.value.upper()}</td>"
                    )
                    html += f"<td>{alert.category.value}</td>"
                    html += f"<td>{alert.title}</td>"
                    html += f"<td>{alert.message}</td>"
                    html += f"</tr>"

                html += "</table></body></html>"

                # Write to file if destination provided
                if destination:
                    path = Path(destination)
                    with open(path, "w") as f:
                        f.write(html)

                return html
            else:
                raise ValueError(f"Unsupported export format: {format}")


# Singleton instance
_alert_manager_instance = None


def get_alert_manager() -> AlertManager:
    """
    Get the singleton alert manager instance.

    Returns:
        AlertManager instance
    """
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager()
    return _alert_manager_instance


async def create_alert(
    title: str,
    message: str,
    level: AlertLevel = AlertLevel.INFO,
    category: AlertCategory = AlertCategory.SYSTEM,
    source: AlertSource = AlertSource.SYSTEM,
    details: Optional[Dict[str, Any]] = None,
    labels: Optional[Dict[str, str]] = None,
    correlation_id: Optional[str] = None,
) -> Optional[Alert]:
    """
    Create and process an alert.

    Args:
        title: Alert title
        message: Alert message
        level: Alert level
        category: Alert category
        source: Alert source
        details: Optional alert details
        labels: Optional alert labels
        correlation_id: Optional correlation ID for tracking

    Returns:
        Created alert if processed, None if deduplicated or rate limited
    """
    return await get_alert_manager().create_alert(
        title=title,
        message=message,
        level=level,
        category=category,
        source=source,
        details=details,
        labels=labels,
        correlation_id=correlation_id,
    )


async def set_threshold(
    metric_name: str, warning_threshold: float, critical_threshold: float
) -> None:
    """
    Set thresholds for a metric.

    Args:
        metric_name: Metric name
        warning_threshold: Warning threshold
        critical_threshold: Critical threshold
    """
    await get_alert_manager().set_threshold(
        metric_name=metric_name,
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold,
    )
