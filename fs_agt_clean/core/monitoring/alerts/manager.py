"""Alert management system."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict, cast

from fs_agt_clean.core.monitoring.aggregation import MetricAggregationService
from fs_agt_clean.core.monitoring.alerts.models import (
    Alert,
    AlertSeverity,
    AlertType,
    MetricType,
)
from fs_agt_clean.core.monitoring.alerts.notification_service import NotificationService
from fs_agt_clean.core.monitoring.alerts.persistence import (
    AlertStorage,
    SQLiteAlertStorage,
)
from fs_agt_clean.core.monitoring.alerts.validation import (
    AlertValidationError,
    validate_alert,
)

logger = logging.getLogger(__name__)


class AnomalySettings(TypedDict):
    """Settings for anomaly detection."""

    window: str
    sigma_threshold: float


class TrendSettings(TypedDict):
    """Settings for trend analysis."""

    window: str
    threshold: float
    critical_threshold: float


class DeduplicationSettings(TypedDict):
    """Settings for alert deduplication."""

    window: timedelta
    rate_limit_window: timedelta
    max_alerts_per_window: int
    max_fingerprints: int


class AlertStats(TypedDict):
    """Alert statistics."""

    total_alerts: int
    alerts_by_severity: Dict[str, int]
    alerts_by_type: Dict[str, int]
    deduplicated_count: int
    rate_limited_count: int


class AlertManager:
    """Manages system alerts and notifications."""

    def __init__(
        self,
        storage: Optional[AlertStorage] = None,
        notification_service: Optional[NotificationService] = None,
        aggregation_service: Optional[MetricAggregationService] = None,
        db_path: str = "data/alerts.db",
    ):
        """Initialize the alert manager.

        Args:
            storage: Optional alert storage to use
            notification_service: Optional notification service to use
            aggregation_service: Optional metric aggregation service
            db_path: Path to SQLite database file (used if storage not provided)
        """
        self._storage = storage or SQLiteAlertStorage(Path(db_path))
        self._notification_service = notification_service
        self._aggregation_service = aggregation_service or MetricAggregationService()

        # Deduplication settings and state
        self._dedup_settings: DeduplicationSettings = {
            "window": timedelta(minutes=5),
            "rate_limit_window": timedelta(hours=1),
            "max_alerts_per_window": 10,
            "max_fingerprints": 10000,
        }
        self._last_alert_times: Dict[str, datetime] = {}
        self._alert_counts: Dict[str, int] = {}
        self._alert_fingerprints: Set[str] = set()

        # Alert statistics
        self._stats: AlertStats = {
            "total_alerts": 0,
            "alerts_by_severity": {},
            "alerts_by_type": {},
            "deduplicated_count": 0,
            "rate_limited_count": 0,
        }

        # Default thresholds for common metrics
        # Format: (warning_threshold, critical_threshold)
        self._thresholds: Dict[str, Tuple[float, float]] = {
            "cpu_usage": (75.0, 90.0),  # CPU usage percentage
            "memory_usage": (75.0, 90.0),  # Memory usage percentage
            "disk_usage": (75.0, 90.0),  # Disk usage percentage
            "battery_level": (20.0, 10.0),  # Battery percentage (reversed thresholds)
            "network_usage": (75.0, 90.0),  # Network bandwidth percentage
        }

        # Anomaly detection settings
        self._anomaly_settings: AnomalySettings = {
            "window": "5m",  # Time window for anomaly detection
            "sigma_threshold": 3.0,  # Standard deviations for anomaly threshold
        }

        # Trend analysis settings
        self._trend_settings: TrendSettings = {
            "window": "1h",  # Time window for trend analysis
            "threshold": 0.1,  # Minimum trend slope for alert
            "critical_threshold": 0.5,  # Slope threshold for critical alerts
        }

    def configure_deduplication(
        self,
        window_minutes: int = 5,
        rate_limit_hours: int = 1,
        max_alerts: int = 10,
        max_fingerprints: int = 10000,
    ) -> None:
        """Configure alert deduplication settings.

        Args:
            window_minutes: Deduplication window in minutes
            rate_limit_hours: Rate limiting window in hours
            max_alerts: Maximum alerts per rate limit window
            max_fingerprints: Maximum fingerprints to store

        Raises:
            ValueError: If parameters are invalid
        """
        if window_minutes <= 0 or rate_limit_hours <= 0:
            raise ValueError("Time windows must be positive")

        if max_alerts <= 0 or max_fingerprints <= 0:
            raise ValueError("Alert limits must be positive")

        self._dedup_settings.update(
            {
                "window": timedelta(minutes=window_minutes),
                "rate_limit_window": timedelta(hours=rate_limit_hours),
                "max_alerts_per_window": max_alerts,
                "max_fingerprints": max_fingerprints,
            }
        )

        # Clear state when settings change
        self._cleanup_dedup_state()

    def get_alert_stats(self) -> AlertStats:
        """Get current alert statistics.

        Returns:
            Dictionary containing alert statistics
        """
        return cast(
            AlertStats,
            {
                "total_alerts": self._stats["total_alerts"],
                "alerts_by_severity": self._stats["alerts_by_severity"].copy(),
                "alerts_by_type": self._stats["alerts_by_type"].copy(),
                "deduplicated_count": self._stats["deduplicated_count"],
                "rate_limited_count": self._stats["rate_limited_count"],
            },
        )

    def _generate_alert_fingerprint(self, alert: Alert) -> str:
        """Generate a unique fingerprint for an alert for deduplication.

        Args:
            alert: Alert to generate fingerprint for

        Returns:
            str: Alert fingerprint
        """
        # Create a fingerprint based on relevant alert attributes
        fingerprint_parts = [
            alert.component,
            str(alert.alert_type),
            str(alert.severity),
            str(alert.metric_type),
            str(round(alert.metric_value, 2)),  # Round to reduce noise
            str(round(alert.threshold, 2)),
        ]
        if alert.labels:
            # Sort labels to ensure consistent fingerprints
            sorted_labels = sorted(f"{k}:{v}" for k, v in alert.labels.items())
            fingerprint_parts.extend(sorted_labels)

        return "|".join(fingerprint_parts)

    def _should_deduplicate(self, alert: Alert, fingerprint: str) -> bool:
        """Check if an alert should be deduplicated.

        Args:
            alert: Alert to check
            fingerprint: Alert fingerprint

        Returns:
            bool: True if alert should be deduplicated
        """
        now = datetime.now(timezone.utc)

        # Check rate limiting
        alert_key = f"{alert.component}_{alert.alert_type}"
        if alert_key in self._alert_counts:
            if (
                self._alert_counts[alert_key]
                >= self._dedup_settings["max_alerts_per_window"]
            ):
                logger.warning("Rate limit exceeded for %s, ", alert_key)
                f"suppressing alert"

                self._stats["rate_limited_count"] += 1
                return bool(True)

        # Check time-based deduplication
        if alert_key in self._last_alert_times:
            last_time = self._last_alert_times[alert_key]
            if now - last_time < self._dedup_settings["window"]:
                logger.debug("Deduplicating alert for %s, ", alert_key)
                f"last alert was {now - last_time} ago"

                self._stats["deduplicated_count"] += 1
                return True

        # Check content-based deduplication
        if fingerprint in self._alert_fingerprints:
            logger.debug("Deduplicating alert with fingerprint %s", fingerprint)

            self._stats["deduplicated_count"] += 1
            return True

        return False

    def _update_dedup_state(self, alert: Alert, fingerprint: str) -> None:
        """Update deduplication state after processing an alert.

        Args:
            alert: Processed alert
            fingerprint: Alert fingerprint
        """
        now = datetime.now(timezone.utc)
        alert_key = f"{alert.component}_{alert.alert_type}"

        # Update last alert time
        self._last_alert_times[alert_key] = now

        # Update alert count for rate limiting
        if alert_key not in self._alert_counts:
            self._alert_counts[alert_key] = 1
        else:
            self._alert_counts[alert_key] += 1

        # Add fingerprint to set
        self._alert_fingerprints.add(fingerprint)

        # Update statistics
        self._stats["total_alerts"] += 1
        severity_key = alert.severity.value
        type_key = alert.alert_type.value

        self._stats["alerts_by_severity"][severity_key] = (
            self._stats["alerts_by_severity"].get(severity_key, 0) + 1
        )
        self._stats["alerts_by_type"][type_key] = (
            self._stats["alerts_by_type"].get(type_key, 0) + 1
        )

        # Clean up old state
        self._cleanup_dedup_state()

    def _cleanup_dedup_state(self) -> None:
        """Clean up old deduplication state."""
        now = datetime.now(timezone.utc)

        # Clean up old alert times
        self._last_alert_times = {
            k: v
            for k, v in self._last_alert_times.items()
            if now - v < self._dedup_settings["window"]
        }

        # Clean up old alert counts
        self._alert_counts = {
            k: v
            for k, v in self._alert_counts.items()
            if now - self._last_alert_times.get(k, now)
            < self._dedup_settings["rate_limit_window"]
        }

        # Clean up old fingerprints
        if len(self._alert_fingerprints) > self._dedup_settings["max_fingerprints"]:
            self._alert_fingerprints.clear()

    async def process_alert(self, alert: Alert) -> None:
        """Process a new alert.

        Args:
            alert: Alert to process

        Raises:
            AlertValidationError: If alert validation fails
            IOError: If storage operation fails
        """
        # Validate alert
        is_valid, errors = validate_alert(alert)
        if not is_valid:
            raise AlertValidationError(
                "Alert validation failed", validation_errors=errors
            )

        # Generate fingerprint and check deduplication
        fingerprint = self._generate_alert_fingerprint(alert)
        if self._should_deduplicate(alert, fingerprint):
            return

        # Update deduplication state
        self._update_dedup_state(alert, fingerprint)

        # Store alert
        try:
            await self._storage.store_alert(alert)
        except IOError as e:
            logger.error("Failed to store alert: %s", e)
            raise

        # Send notification if service is available
        if self._notification_service:
            template_id = (
                "alert_critical"
                if alert.severity == AlertSeverity.CRITICAL
                else "alert_warning"
            )

            try:
                await self._notification_service.send_notification(
                    user_id="system",
                    template_id=template_id,
                    data={
                        "metric_name": alert.component,
                        "value": float(alert.metric_value),
                        "severity": alert.severity,
                        "threshold": float(alert.threshold),
                        "timestamp": alert.timestamp,
                        "active": True,
                        "metric_type": alert.metric_type,
                        "component": alert.component,
                        "labels": alert.labels,
                    },
                    category="monitoring",
                )
            except Exception as e:
                logger.error("Failed to send notification: %s", e)

    async def get_alerts(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        component: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Alert]:
        """Get alerts with filtering and pagination.

        Args:
            limit: Maximum number of alerts to return
            offset: Number of alerts to skip
            component: Filter by component
            severity: Filter by severity
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            List of alerts matching the filters

        Raises:
            IOError: If retrieval operation fails
        """
        try:
            alerts = await self._storage.get_alerts(
                start_time=start_time,
                end_time=end_time,
                severity=severity,
                limit=limit,
                offset=offset,
            )

            if component:
                alerts = [a for a in alerts if a.component == component]

            return alerts
        except IOError as e:
            logger.error("Failed to retrieve alerts: %s", e)
            raise

    async def clear_alerts(
        self, component: Optional[str] = None, older_than: Optional[datetime] = None
    ) -> int:
        """Clear alerts with optional filtering.

        Args:
            component: Only clear alerts for this component
            older_than: Only clear alerts older than this time

        Returns:
            Number of alerts cleared

        Raises:
            IOError: If deletion operation fails
        """
        try:
            # Clear deduplication state
            self._last_alert_times.clear()
            self._alert_counts.clear()
            self._alert_fingerprints.clear()

            # Delete alerts from storage
            return await self._storage.delete_alerts(older_than=older_than)
        except IOError as e:
            logger.error("Failed to clear alerts: %s", e)
            raise

    async def set_threshold(
        self, metric_name: str, warning: float, critical: float, comparison: str = ">"
    ) -> None:
        """Set alert thresholds for a metric.

        Args:
            metric_name: Name of the metric
            warning: Warning threshold
            critical: Critical threshold
            comparison: Comparison operator (">", "<", ">=", "<=")

        Raises:
            ValueError: If thresholds are invalid
        """
        if warning < 0 or critical < 0:
            raise ValueError("Thresholds cannot be negative")

        if comparison not in {">", "<", ">=", "<="}:
            raise ValueError(f"Invalid comparison operator: {comparison}")

        if comparison in {">", ">="} and warning > critical:
            raise ValueError(
                "Warning threshold must be less than critical threshold "
                "for '>' comparisons"
            )

        if comparison in {"<", "<="} and warning < critical:
            raise ValueError(
                "Warning threshold must be greater than critical threshold "
                "for '<' comparisons"
            )

        self._thresholds[metric_name] = (warning, critical)

    async def check_threshold(self, metric_name: str, value: float) -> Optional[Alert]:
        """Check if a metric value exceeds its thresholds.

        Args:
            metric_name: Name of the metric
            value: Current value of the metric

        Returns:
            Alert if threshold is exceeded, None otherwise
        """
        if metric_name not in self._thresholds:
            return None

        warning, critical = self._thresholds[metric_name]
        value = float(value)  # Ensure float conversion

        if value > critical:
            return Alert(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.RESOURCE,
                source="system",
                component=metric_name,
                message=f"{metric_name} exceeded critical threshold: {value} > {critical}",
                metric_type=MetricType.GAUGE,
                metric_value=value,
                threshold=critical,
            )
        elif value > warning:
            return Alert(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                severity=AlertSeverity.HIGH,  # Changed from MEDIUM to HIGH
                alert_type=AlertType.RESOURCE,
                source="system",
                component=metric_name,
                message=f"{metric_name} exceeded warning threshold: {value} > {warning}",
                metric_type=MetricType.GAUGE,
                metric_value=value,
                threshold=warning,
            )

        return None

    async def process_metric(self, metric_name: str, value: float) -> None:
        """Process a new metric value and generate alerts if needed.

        This method performs three types of analysis:
        1. Threshold checking: Compares value against predefined thresholds
        2. Anomaly detection: Uses statistical analysis to detect outliers
        3. Trend analysis: Monitors significant changes over time

        Args:
            metric_name: Name of the metric
            value: Current metric value

        Thresholds:
            - cpu_usage: Warning at 75%, Critical at 90%
            - memory_usage: Warning at 75%, Critical at 90%
            - disk_usage: Warning at 75%, Critical at 90%
            - battery_level: Warning at 20%, Critical at 10%
            - network_usage: Warning at 75%, Critical at 90%

        Anomaly Detection:
            - Uses 5-minute window
            - Alerts on values > 3 standard deviations from mean

        Trend Analysis:
            - Uses 1-hour window
            - Alerts on slope > 0.1 (High) or > 0.5 (Critical)
        """
        # Add metric to aggregation service
        await self._aggregation_service.add_metric(metric_name, value)

        # Check static thresholds
        if metric_name in self._thresholds:
            warning_threshold, critical_threshold = self._thresholds[metric_name]
            if value >= critical_threshold:
                await self._create_threshold_alert(
                    metric_name, value, critical_threshold, AlertSeverity.CRITICAL
                )
            elif value >= warning_threshold:
                await self._create_threshold_alert(
                    metric_name, value, warning_threshold, AlertSeverity.HIGH
                )

        # Check for anomalies
        anomalies = await self._aggregation_service.detect_anomalies(
            metric_name,
            self._anomaly_settings["window"],
            threshold_sigmas=self._anomaly_settings["sigma_threshold"],
        )
        if anomalies and anomalies[-1][1] == value:  # If current value is anomalous
            await self._create_anomaly_alert(
                metric_name, value, anomalies[-1][0]
            )  # Timestamp

        # Check for concerning trends
        trend = await self._aggregation_service.get_trend(
            metric_name, self._trend_settings["window"]
        )
        if trend is not None:
            if abs(trend) > self._trend_settings["threshold"]:
                await self._create_trend_alert(metric_name, trend, value)

    async def _create_threshold_alert(
        self, metric_name: str, value: float, threshold: float, severity: AlertSeverity
    ) -> None:
        """Create and process a threshold-based alert.

        Args:
            metric_name: Name of the metric
            value: Current metric value
            threshold: Threshold that was exceeded
            severity: Alert severity
        """
        alert = Alert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.RESOURCE,
            severity=severity,
            metric_type=MetricType.GAUGE,
            metric_value=value,
            threshold=threshold,
            component=metric_name,
            source="monitoring",
            message=f"{metric_name} exceeded {severity.value} threshold: {value} > {threshold}",
            timestamp=datetime.now(timezone.utc),
            labels={
                "type": "threshold_breach",
                "threshold_type": severity.value.lower(),
            },
        )
        await self.process_alert(alert)

    async def _create_anomaly_alert(
        self, metric_name: str, value: float, timestamp: datetime
    ) -> None:
        """Create and process an anomaly-based alert.

        Args:
            metric_name: Name of the metric
            value: Anomalous value
            timestamp: Time of anomaly
        """
        alert = Alert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.PERFORMANCE,
            severity=AlertSeverity.HIGH,
            metric_type=MetricType.GAUGE,
            metric_value=value,
            threshold=0.0,  # Not applicable for anomalies
            component=metric_name,
            source="monitoring",
            message=f"Anomaly detected in {metric_name}: value {value} is statistically significant",
            timestamp=timestamp,
            labels={"type": "anomaly_detection", "detection_window": "5m"},
        )
        await self.process_alert(alert)

    async def _create_trend_alert(
        self, metric_name: str, trend: float, current_value: float
    ) -> None:
        """Create and process a trend-based alert.

        Args:
            metric_name: Name of the metric
            trend: Calculated trend value
            current_value: Current metric value
        """
        severity = (
            AlertSeverity.CRITICAL
            if abs(trend) > self._trend_settings["critical_threshold"]
            else AlertSeverity.HIGH
        )

        alert = Alert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.PERFORMANCE,
            severity=severity,
            metric_type=MetricType.GAUGE,
            metric_value=current_value,
            threshold=trend,
            component=metric_name,
            source="monitoring",
            message=f"Significant trend detected in {metric_name}: {trend:+.2f} per hour",
            timestamp=datetime.now(timezone.utc),
            labels={
                "type": "trend_detection",
                "trend_direction": "increasing" if trend > 0 else "decreasing",
                "trend_value": f"{trend:.3f}",
                "analysis_window": "1h",
            },
        )
        await self.process_alert(alert)

    def configure_thresholds(
        self, metric_name: str, warning: float, critical: float
    ) -> None:
        """Configure alert thresholds for a metric.

        Args:
            metric_name: Name of the metric
            warning: Warning threshold value
            critical: Critical threshold value

        Raises:
            ValueError: If thresholds are invalid
        """
        if warning < 0 or critical < 0:
            raise ValueError("Thresholds cannot be negative")

        if warning > critical:
            raise ValueError("Warning threshold must be less than critical threshold")

        self._thresholds[metric_name] = (warning, critical)

    def configure_anomaly_detection(
        self, window: str = "5m", sigma_threshold: float = 3.0
    ) -> None:
        """Configure anomaly detection settings.

        Args:
            window: Time window for detection ("1m", "5m", "1h")
            sigma_threshold: Number of standard deviations for anomaly threshold

        Raises:
            ValueError: If parameters are invalid
        """
        if window not in {"1m", "5m", "1h"}:
            raise ValueError("Invalid window size")

        if sigma_threshold <= 0:
            raise ValueError("Sigma threshold must be positive")

        self._anomaly_settings.update(
            {"window": window, "sigma_threshold": sigma_threshold}
        )

    def configure_trend_analysis(
        self,
        window: str = "1h",
        threshold: float = 0.1,
        critical_threshold: float = 0.5,
    ) -> None:
        """Configure trend analysis settings.

        Args:
            window: Time window for analysis ("1m", "5m", "1h")
            threshold: Minimum trend slope for alert
            critical_threshold: Slope threshold for critical alerts

        Raises:
            ValueError: If parameters are invalid
        """
        if window not in {"1m", "5m", "1h"}:
            raise ValueError("Invalid window size")

        if threshold <= 0 or critical_threshold <= 0:
            raise ValueError("Thresholds must be positive")

        if threshold > critical_threshold:
            raise ValueError("Alert threshold must be less than critical threshold")

        self._trend_settings.update(
            {
                "window": window,
                "threshold": threshold,
                "critical_threshold": critical_threshold,
            }
        )

    async def send_alert(
        self,
        message: str,
        severity: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send an alert with the specified severity level.

        Args:
            message: Alert message
            severity: Alert severity level (INFO, WARNING, ERROR, CRITICAL)
            metadata: Optional metadata to attach to the alert
        """
        timestamp = datetime.now(timezone.utc)
        alert_data = {
            "message": message,
            "severity": severity,
            "timestamp": timestamp,
            **(metadata or {}),
        }

        # Log the alert
        log_level = getattr(logging, severity.upper(), logging.INFO)
        logger.log(log_level, f"Alert: {message}")

        # Additional alert handling (e.g., sending to monitoring system)
        await self._process_alert(alert_data)

    async def _process_alert(self, alert_data: Dict[str, Any]) -> None:
        """Process the alert data."""
        # Implement alert processing logic here
        pass
