"""Alert correlation engine for identifying patterns and relationships between alerts."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, TypedDict

from fs_agt_clean.core.monitoring.alerts.models import Alert, AlertSeverity, AlertType
from fs_agt_clean.core.monitoring.alerts.notification_service import NotificationService

logger = logging.getLogger(__name__)


class CorrelationData(TypedDict):
    """Data for correlation notifications."""

    rule_name: str
    rule_description: str
    component: str
    timestamp: datetime
    confidence: float
    alert_count: int
    time_window: str
    latest_alert: str
    root_cause: str
    pattern_description: Optional[str]
    recommendations: Optional[str]
    alert_message: Optional[str]


class CorrelationType(str, Enum):
    """Types of alert correlations."""

    CAUSATION = "causation"  # One alert likely caused another
    TEMPORAL = "temporal"  # Alerts occurred close in time
    COMPONENT = "component"  # Alerts from same/related components
    PATTERN = "pattern"  # Alerts form a recognized pattern


@dataclass
class CorrelationRule:
    """Rule for correlating alerts."""

    id: str
    name: str
    description: str
    correlation_type: CorrelationType
    time_window: timedelta
    alert_types: Set[AlertType]
    min_severity: AlertSeverity
    component_pattern: Optional[str] = None
    causation_metrics: Optional[List[str]] = None
    pattern_sequence: Optional[List[AlertType]] = None

    def matches(self, alert: Alert) -> bool:
        """Check if an alert matches this rule."""
        alert_type = AlertType(alert.alert_type)
        if alert_type not in self.alert_types:
            return bool(False)

        if alert.severity < self.min_severity:
            return False

        if self.component_pattern and self.component_pattern not in alert.component:
            return False

        return True


@dataclass
class AlertCorrelation:
    """Group of correlated alerts."""

    id: str
    rule: CorrelationRule
    alerts: List[Alert]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    root_cause: Optional[Alert] = None
    confidence: float = 0.0

    def add_alert(self, alert: Alert) -> None:
        """Add an alert to the correlation group.

        Args:
            alert: Alert to add
        """
        self.alerts.append(alert)
        self.updated_at = datetime.now(timezone.utc)

    def analyze_root_cause(self) -> None:
        """Analyze alerts to determine likely root cause."""
        if not self.alerts:
            return

        if self.rule.correlation_type == CorrelationType.CAUSATION:
            self._analyze_causation()
        elif self.rule.correlation_type == CorrelationType.TEMPORAL:
            self._analyze_temporal()
        elif self.rule.correlation_type == CorrelationType.PATTERN:
            self._analyze_pattern()

    def _analyze_causation(self) -> None:
        """Analyze causation-based correlations."""
        # Sort by time
        sorted_alerts = sorted(self.alerts, key=lambda a: a.timestamp)

        # First alert in causation chain is likely root cause
        self.root_cause = sorted_alerts[0]

        # Higher confidence if we have causation metrics defined
        if self.rule.causation_metrics:
            matching_metrics = sum(
                1
                for a in self.alerts
                if a.component in (self.rule.causation_metrics or [])
            )
            self.confidence = matching_metrics / len(self.alerts)
        else:
            self.confidence = 0.7  # Default confidence for causation

    def _analyze_temporal(self) -> None:
        """Analyze time-based correlations."""
        # Sort by time
        sorted_alerts = sorted(self.alerts, key=lambda a: a.timestamp)

        # Find alert that started the temporal cluster
        self.root_cause = sorted_alerts[0]

        # Confidence based on temporal clustering
        total_duration = sorted_alerts[-1].timestamp - sorted_alerts[0].timestamp
        if total_duration > self.rule.time_window:
            self.confidence = 0.3
        else:
            # Higher confidence for tighter clustering
            self.confidence = 0.8 * (1 - total_duration / self.rule.time_window)

    def _analyze_pattern(self) -> None:
        """Analyze pattern-based correlations."""
        if not self.rule.pattern_sequence:
            return

        # Sort by time
        sorted_alerts = sorted(self.alerts, key=lambda a: a.timestamp)

        # Check if alerts match expected sequence
        alert_types = [a.alert_type for a in sorted_alerts]
        expected_types = self.rule.pattern_sequence

        if len(alert_types) != len(expected_types):
            self.confidence = 0.0
            return

        # Calculate pattern match confidence
        matches = sum(
            1
            for actual, expected in zip(alert_types, expected_types)
            if actual == expected
        )
        self.confidence = matches / len(expected_types)

        if self.confidence > 0.7:
            # First alert in matching pattern is root cause
            self.root_cause = sorted_alerts[0]


class AlertCorrelationEngine:
    """Engine for correlating alerts and identifying patterns."""

    def __init__(self, notification_service: Optional[NotificationService] = None):
        """Initialize the correlation engine.

        Args:
            notification_service: Optional notification service for sending correlation alerts
        """
        self._rules: List[CorrelationRule] = []
        self._correlations: Dict[str, AlertCorrelation] = {}
        self._notification_service = notification_service

        # Initialize default rules
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """Initialize default correlation rules."""
        # Resource exhaustion pattern
        self._rules.append(
            CorrelationRule(
                id="resource_exhaustion",
                name="Resource Exhaustion Pattern",
                description="Sequence of resource alerts indicating system stress",
                correlation_type=CorrelationType.PATTERN,
                time_window=timedelta(minutes=5),
                alert_types={AlertType.RESOURCE, AlertType.PERFORMANCE},
                min_severity=AlertSeverity.HIGH,
                pattern_sequence=[
                    AlertType.RESOURCE,
                    AlertType.PERFORMANCE,
                    AlertType.SECURITY,
                ],
            )
        )

        # Cascading failure pattern
        self._rules.append(
            CorrelationRule(
                id="cascading_failure",
                name="Cascading Failure Pattern",
                description="Multiple component failures in sequence",
                correlation_type=CorrelationType.CAUSATION,
                time_window=timedelta(minutes=10),
                alert_types={AlertType.SECURITY, AlertType.CUSTOM},
                min_severity=AlertSeverity.CRITICAL,
            )
        )

        # Component cluster pattern
        self._rules.append(
            CorrelationRule(
                id="component_cluster",
                name="Component Failure Cluster",
                description="Multiple alerts from same component",
                correlation_type=CorrelationType.COMPONENT,
                time_window=timedelta(minutes=15),
                alert_types={AlertType.RESOURCE, AlertType.PERFORMANCE},
                min_severity=AlertSeverity.HIGH,
            )
        )

    async def _notify_correlation(
        self,
        correlation: AlertCorrelation,
        template_id: str,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send notification about a correlation.

        Args:
            correlation: Correlation to notify about
            template_id: ID of template to use
            additional_data: Optional additional template data
        """
        if not self._notification_service:
            return

        # Prepare base notification data
        data: Dict[str, Any] = {
            "rule_name": correlation.rule.name,
            "rule_description": correlation.rule.description,
            "component": correlation.alerts[0].component,
            "timestamp": correlation.created_at,
            "confidence": correlation.confidence,
            "alert_count": len(correlation.alerts),
            "time_window": f"{correlation.rule.time_window.total_seconds() / 60:.1f} minutes",
            "latest_alert": (
                correlation.alerts[-1].message if correlation.alerts else "N/A"
            ),
            "root_cause": (
                correlation.root_cause.message if correlation.root_cause else "Unknown"
            ),
            "pattern_description": None,
            "recommendations": None,
        }

        # Add pattern-specific information
        if correlation.rule.correlation_type == CorrelationType.PATTERN:
            pattern_desc = (
                " → ".join(t.value for t in correlation.rule.pattern_sequence)
                if correlation.rule.pattern_sequence
                else "N/A"
            )
            data["pattern_description"] = pattern_desc

            # Add recommendations based on pattern
            if correlation.rule.id == "resource_exhaustion":
                data["recommendations"] = (
                    "1. Check system resource allocation\n"
                    "2. Review resource-intensive processes\n"
                    "3. Consider scaling resources if pattern persists"
                )
            elif correlation.rule.id == "cascading_failure":
                data["recommendations"] = (
                    "1. Investigate root cause alert first\n"
                    "2. Check component dependencies\n"
                    "3. Review system architecture for cascading failure points"
                )

        # Add any additional data
        if additional_data:
            data.update(additional_data)

        await self._notification_service.send_alert(
            alert_id=correlation.id,
            severity=AlertSeverity.HIGH,
            metric_name=f"correlation_{correlation.rule.correlation_type}",
            value=correlation.confidence * 100,
            threshold=70.0,
            component=correlation.alerts[0].component,
            email_recipients=["alerts@example.com"],  # TODO: Configure recipients
            sms_recipients=None,
        )

    def add_rule(self, rule: CorrelationRule) -> None:
        """Add a correlation rule.

        Args:
            rule: Rule to add
        """
        self._rules.append(rule)

    async def process_alert(self, alert: Alert) -> List[AlertCorrelation]:
        """Process a new alert and update correlations.

        Args:
            alert: New alert to process

        Returns:
            List of affected/new correlations
        """
        matched_correlations: List[AlertCorrelation] = []

        # Check existing correlations
        for correlation in self._correlations.values():
            if (
                correlation.rule.matches(alert)
                and alert.timestamp - correlation.created_at
                <= correlation.rule.time_window
            ):
                correlation.send_alert(alert)
                correlation.analyze_root_cause()
                matched_correlations.append(correlation)

                if correlation.confidence >= 0.7:
                    await self._notify_correlation(
                        correlation,
                        "correlation_confirmed",
                        {
                            "pattern_description": (
                                f"Detected {correlation.rule.correlation_type} "
                                f"pattern with {len(correlation.alerts)} alerts"
                            ),
                            "recommendations": self._get_recommendations(correlation),
                        },
                    )

        # Create new correlations for unmatched rules
        for rule in self._rules:
            if rule.matches(alert):
                correlation_id = f"{rule.id}_{datetime.now(timezone.utc).timestamp()}"
                correlation = AlertCorrelation(
                    id=correlation_id, rule=rule, alerts=[alert]
                )
                self._correlations[correlation_id] = correlation
                matched_correlations.append(correlation)

                await self._notify_correlation(
                    correlation, "correlation_new", {"alert_message": alert.message}
                )

        return matched_correlations

    def get_correlations(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_confidence: float = 0.5,
    ) -> List[AlertCorrelation]:
        """Get correlations within time range.

        Args:
            start_time: Optional start of time range
            end_time: Optional end of time range
            min_confidence: Minimum correlation confidence

        Returns:
            List of correlations meeting criteria
        """
        correlations: List[AlertCorrelation] = []

        for correlation in self._correlations.values():
            # Check time range
            if start_time and correlation.updated_at < start_time:
                continue
            if end_time and correlation.created_at > end_time:
                continue

            # Check confidence
            if correlation.confidence < min_confidence:
                continue

            correlations.append(correlation)

        return sorted(correlations, key=lambda c: c.confidence, reverse=True)

    def cleanup_old_correlations(
        self, max_age: timedelta = timedelta(hours=24)
    ) -> None:
        """Remove old correlations.

        Args:
            max_age: Maximum age of correlations to keep
        """
        now = datetime.now(timezone.utc)
        old_ids = [
            cid for cid, c in self._correlations.items() if now - c.updated_at > max_age
        ]
        for cid in old_ids:
            del self._correlations[cid]

    def _get_recommendations(self, correlation: AlertCorrelation) -> str:
        """Get recommendations based on correlation type."""
        if correlation.rule.correlation_type == CorrelationType.CAUSATION:
            return (
                "1. Investigate root cause alert first\n"
                "2. Check component dependencies\n"
                "3. Review system architecture for cascading failure points"
            )
        elif correlation.rule.correlation_type == CorrelationType.PATTERN:
            return (
                "1. Review system capacity and scaling\n"
                "2. Check for resource bottlenecks\n"
                "3. Consider implementing circuit breakers"
            )
        elif correlation.rule.correlation_type == CorrelationType.COMPONENT:
            return (
                "1. Check component health and metrics\n"
                "2. Review recent changes or deployments\n"
                "3. Consider component redundancy"
            )
        else:
            return (
                "1. Monitor system closely\n"
                "2. Review alert patterns\n"
                "3. Update correlation rules if needed"
            )
