"""
Monitoring UnifiedAgent for FlipSync - Health Monitoring System and Performance Analytics

This agent specializes in:
- System health monitoring and alerting
- UnifiedAgent performance tracking and analytics
- Resource utilization monitoring
- Error detection and reporting
- Performance optimization recommendations
- Real-time system status reporting
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels for system components."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of metrics being monitored."""

    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    RESOURCE_USAGE = "resource_usage"
    AGENT_AVAILABILITY = "agent_availability"
    WORKFLOW_SUCCESS_RATE = "workflow_success_rate"


@dataclass
class SystemMetric:
    """Represents a system metric measurement."""

    metric_id: str
    metric_type: MetricType
    component: str  # agent_id, service_name, etc.
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Represents a health check result."""

    check_id: str
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Represents a system alert."""

    alert_id: str
    severity: AlertSeverity
    component: str
    message: str
    description: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class MonitoringUnifiedAgent(BaseConversationalUnifiedAgent):
    """
    Monitoring UnifiedAgent for system health monitoring and performance analytics.

    Capabilities:
    - Real-time system health monitoring
    - UnifiedAgent performance tracking
    - Resource utilization monitoring
    - Automated alerting and notifications
    - Performance trend analysis
    - System optimization recommendations
    """

    def __init__(self, agent_id: Optional[str] = None, use_fast_model: bool = True):
        """Initialize the Monitoring UnifiedAgent."""
        super().__init__(UnifiedAgentRole.ASSISTANT, agent_id, use_fast_model)

        # Monitoring agent capabilities
        self.capabilities = [
            "system_health_monitoring",
            "performance_analytics",
            "resource_monitoring",
            "automated_alerting",
            "trend_analysis",
            "optimization_recommendations",
            "real_time_dashboards",
            "incident_management",
        ]

        # Monitoring data storage
        self.metrics: List[SystemMetric] = []
        self.health_checks: Dict[str, HealthCheck] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.resolved_alerts: List[Alert] = []

        # Monitoring configuration
        self.check_intervals = {
            "agents": 60,  # 1 minute
            "services": 120,  # 2 minutes
            "database": 180,  # 3 minutes
            "apis": 300,  # 5 minutes
        }

        # Alert thresholds
        self.thresholds = {
            "response_time": {"warning": 5.0, "critical": 10.0},  # seconds
            "error_rate": {"warning": 0.05, "critical": 0.10},  # 5%, 10%
            "cpu_usage": {"warning": 0.80, "critical": 0.95},  # 80%, 95%
            "memory_usage": {"warning": 0.85, "critical": 0.95},  # 85%, 95%
            "agent_availability": {"warning": 0.90, "critical": 0.80},  # 90%, 80%
        }

        # Components being monitored
        self.monitored_components = {
            "agents": [
                "market_agent",
                "content_agent",
                "logistics_agent",
                "executive_agent",
                "sync_agent",
                "service_agent",
                "monitoring_agent",
            ],
            "services": ["database", "redis", "api_gateway", "websocket_server"],
            "workflows": [
                "pricing_optimization",
                "inventory_management",
                "cross_platform_sync",
                "customer_service",
                "health_monitoring",
            ],
        }

        # Monitoring task
        self._monitoring_task = None
        self._is_monitoring = False

        logger.info(f"Monitoring UnifiedAgent initialized: {self.agent_id}")

    async def start_monitoring(self) -> bool:
        """Start the monitoring system."""
        if self._is_monitoring:
            return True

        try:
            self._is_monitoring = True
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Monitoring system started")
            return True
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            self._is_monitoring = False
            return False

    async def stop_monitoring(self) -> bool:
        """Stop the monitoring system."""
        if not self._is_monitoring:
            return True

        try:
            self._is_monitoring = False
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            logger.info("Monitoring system stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            return False

    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        current_time = datetime.now(timezone.utc)

        # Calculate overall health
        healthy_components = sum(
            1
            for check in self.health_checks.values()
            if check.status == HealthStatus.HEALTHY
        )
        total_components = len(self.health_checks)

        overall_health = HealthStatus.HEALTHY
        if total_components > 0:
            health_ratio = healthy_components / total_components
            if health_ratio < 0.5:
                overall_health = HealthStatus.CRITICAL
            elif health_ratio < 0.8:
                overall_health = HealthStatus.WARNING

        # Get recent metrics
        recent_metrics = [
            m
            for m in self.metrics
            if (current_time - m.timestamp).total_seconds() < 300  # Last 5 minutes
        ]

        # Count active alerts by severity
        alert_counts = {
            "critical": sum(
                1
                for a in self.active_alerts.values()
                if a.severity == AlertSeverity.CRITICAL
            ),
            "error": sum(
                1
                for a in self.active_alerts.values()
                if a.severity == AlertSeverity.ERROR
            ),
            "warning": sum(
                1
                for a in self.active_alerts.values()
                if a.severity == AlertSeverity.WARNING
            ),
            "info": sum(
                1
                for a in self.active_alerts.values()
                if a.severity == AlertSeverity.INFO
            ),
        }

        return {
            "overall_health": overall_health.value,
            "timestamp": current_time.isoformat(),
            "components": {
                "total": total_components,
                "healthy": healthy_components,
                "unhealthy": total_components - healthy_components,
            },
            "alerts": {
                "active": len(self.active_alerts),
                "by_severity": alert_counts,
            },
            "metrics": {
                "recent_count": len(recent_metrics),
                "total_count": len(self.metrics),
            },
            "monitoring_status": "active" if self._is_monitoring else "inactive",
        }

    async def get_component_health(self, component: str) -> Optional[HealthCheck]:
        """Get health status for a specific component."""
        return self.health_checks.get(component)

    async def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        # Sort by severity and creation time
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.ERROR: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 3,
        }

        alerts.sort(key=lambda a: (severity_order[a.severity], a.created_at))
        return alerts

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged")
            return True
        return False

    async def resolve_alert(
        self, alert_id: str, resolution_note: Optional[str] = None
    ) -> bool:
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.now(timezone.utc)

            if resolution_note:
                alert.metadata["resolution_note"] = resolution_note

            # Move to resolved alerts
            self.resolved_alerts.append(alert)
            del self.active_alerts[alert_id]

            logger.info(f"Alert {alert_id} resolved")
            return True
        return False

    async def get_performance_metrics(
        self,
        component: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        hours: int = 24,
    ) -> List[SystemMetric]:
        """Get performance metrics for analysis."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

        if component:
            metrics = [m for m in metrics if m.component == component]

        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]

        return sorted(metrics, key=lambda m: m.timestamp)

    # Required abstract methods from BaseConversationalUnifiedAgent

    async def _process_response(
        self,
        llm_response: str,
        original_message: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Process the LLM response with monitoring-specific logic."""
        # Add system status information for monitoring queries
        if any(
            keyword in original_message.lower()
            for keyword in ["status", "health", "monitor", "alert"]
        ):
            system_status = await self.get_system_status()

            status_info = f"\n\n🔍 **System Status:**\n"
            status_info += (
                f"• Overall Health: {system_status['overall_health'].upper()}\n"
            )
            status_info += f"• Components: {system_status['components']['healthy']}/{system_status['components']['total']} healthy\n"
            status_info += f"• Active Alerts: {system_status['alerts']['active']}\n"

            if system_status["alerts"]["by_severity"]["critical"] > 0:
                status_info += f"⚠️ **CRITICAL:** {system_status['alerts']['by_severity']['critical']} critical alerts require immediate attention!\n"
            elif system_status["alerts"]["by_severity"]["error"] > 0:
                status_info += f"⚠️ **ERROR:** {system_status['alerts']['by_severity']['error']} error alerts need attention.\n"

            llm_response += status_info

        return llm_response

    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get agent-specific context for prompt generation."""
        system_status = await self.get_system_status()

        return {
            "agent_type": "system_monitoring_specialist",
            "capabilities": self.capabilities,
            "specializations": [
                "System health monitoring",
                "Performance analytics",
                "Resource monitoring",
                "Automated alerting",
            ],
            "monitored_components": self.monitored_components,
            "current_status": {
                "overall_health": system_status["overall_health"],
                "active_alerts": system_status["alerts"]["active"],
                "monitoring_active": self._is_monitoring,
            },
            "thresholds": self.thresholds,
        }

    # Monitoring implementation methods

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._is_monitoring:
            try:
                # Perform health checks
                await self._perform_health_checks()

                # Collect metrics
                await self._collect_metrics()

                # Check for alerts
                await self._check_alert_conditions()

                # Clean up old data
                await self._cleanup_old_data()

                # Wait before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _perform_health_checks(self):
        """Perform health checks on all monitored components."""
        current_time = datetime.now(timezone.utc)

        # Check agents
        for agent_name in self.monitored_components["agents"]:
            try:
                # Simulate health check (in real implementation, this would ping the agent)
                response_time = await self._check_agent_health(agent_name)

                status = HealthStatus.HEALTHY
                message = "UnifiedAgent responding normally"

                if response_time > 5.0:
                    status = HealthStatus.WARNING
                    message = f"Slow response time: {response_time:.2f}s"
                elif response_time > 10.0:
                    status = HealthStatus.CRITICAL
                    message = f"Very slow response time: {response_time:.2f}s"

                health_check = HealthCheck(
                    check_id=f"health_{agent_name}_{current_time.strftime('%Y%m%d_%H%M%S')}",
                    component=agent_name,
                    status=status,
                    message=message,
                    timestamp=current_time,
                    response_time=response_time,
                )

                self.health_checks[agent_name] = health_check

            except Exception as e:
                # UnifiedAgent is down or unreachable
                health_check = HealthCheck(
                    check_id=f"health_{agent_name}_{current_time.strftime('%Y%m%d_%H%M%S')}",
                    component=agent_name,
                    status=HealthStatus.DOWN,
                    message=f"Health check failed: {str(e)}",
                    timestamp=current_time,
                )

                self.health_checks[agent_name] = health_check

        # Check services
        for service_name in self.monitored_components["services"]:
            try:
                # Simulate service health check
                is_healthy = await self._check_service_health(service_name)

                status = HealthStatus.HEALTHY if is_healthy else HealthStatus.DOWN
                message = "Service operational" if is_healthy else "Service unavailable"

                health_check = HealthCheck(
                    check_id=f"health_{service_name}_{current_time.strftime('%Y%m%d_%H%M%S')}",
                    component=service_name,
                    status=status,
                    message=message,
                    timestamp=current_time,
                )

                self.health_checks[service_name] = health_check

            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")

    async def _collect_metrics(self):
        """Collect performance metrics from system components."""
        current_time = datetime.now(timezone.utc)

        # Collect agent metrics
        for agent_name in self.monitored_components["agents"]:
            try:
                # Simulate metric collection (in real implementation, this would query actual metrics)
                metrics_data = await self._get_agent_metrics(agent_name)

                for metric_type, value in metrics_data.items():
                    metric = SystemMetric(
                        metric_id=f"metric_{agent_name}_{metric_type}_{current_time.strftime('%Y%m%d_%H%M%S')}",
                        metric_type=MetricType(metric_type),
                        component=agent_name,
                        value=value["value"],
                        unit=value["unit"],
                        timestamp=current_time,
                    )

                    self.metrics.append(metric)

            except Exception as e:
                logger.error(f"Failed to collect metrics for {agent_name}: {e}")

    async def _check_alert_conditions(self):
        """Check if any alert conditions are met."""
        current_time = datetime.now(timezone.utc)

        # Check recent metrics for threshold violations
        recent_metrics = [
            m
            for m in self.metrics
            if (current_time - m.timestamp).total_seconds() < 300  # Last 5 minutes
        ]

        for metric in recent_metrics:
            await self._check_metric_thresholds(metric)

        # Check health status for alerts
        for component, health_check in self.health_checks.items():
            if health_check.status in [HealthStatus.CRITICAL, HealthStatus.DOWN]:
                await self._create_alert(
                    component=component,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Component {component} is {health_check.status.value}",
                    description=health_check.message,
                )
            elif health_check.status == HealthStatus.WARNING:
                await self._create_alert(
                    component=component,
                    severity=AlertSeverity.WARNING,
                    message=f"Component {component} has warnings",
                    description=health_check.message,
                )

    async def _check_metric_thresholds(self, metric: SystemMetric):
        """Check if a metric violates thresholds."""
        metric_key = metric.metric_type.value

        if metric_key not in self.thresholds:
            return

        thresholds = self.thresholds[metric_key]

        if metric.value >= thresholds["critical"]:
            await self._create_alert(
                component=metric.component,
                severity=AlertSeverity.CRITICAL,
                message=f"{metric_key} critical threshold exceeded",
                description=f"{metric_key} is {metric.value} {metric.unit}, exceeding critical threshold of {thresholds['critical']}",
            )
        elif metric.value >= thresholds["warning"]:
            await self._create_alert(
                component=metric.component,
                severity=AlertSeverity.WARNING,
                message=f"{metric_key} warning threshold exceeded",
                description=f"{metric_key} is {metric.value} {metric.unit}, exceeding warning threshold of {thresholds['warning']}",
            )

    async def _create_alert(
        self, component: str, severity: AlertSeverity, message: str, description: str
    ):
        """Create a new alert if one doesn't already exist."""
        # Check if similar alert already exists
        for alert_id, alert in self.active_alerts.items():
            if (
                alert.component == component
                and alert.severity == severity
                and alert.message == message
            ):
                # Alert already exists, don't create duplicate
                return

        # Create new alert
        alert_id = f"alert_{component}_{severity.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            component=component,
            message=message,
            description=description,
            created_at=datetime.now(timezone.utc),
        )

        self.active_alerts[alert_id] = alert
        logger.warning("Alert created: %s - %s", alert_id, message)

    async def _cleanup_old_data(self):
        """Clean up old metrics and resolved alerts."""
        current_time = datetime.now(timezone.utc)

        # Keep metrics for last 24 hours
        cutoff_time = current_time - timedelta(hours=24)
        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]

        # Keep resolved alerts for last 7 days
        cutoff_time = current_time - timedelta(days=7)
        self.resolved_alerts = [
            a
            for a in self.resolved_alerts
            if a.resolved_at and a.resolved_at >= cutoff_time
        ]

    # Simulation methods (in real implementation, these would interface with actual systems)

    async def _check_agent_health(self, agent_name: str) -> float:
        """Simulate checking agent health."""
        # Simulate variable response times based on agent name
        base_time = 1.0
        # Add some variation based on agent name for realism
        agent_factor = len(agent_name) % 3 * 0.5
        variation = random.uniform(0.5, 3.0)
        return base_time + agent_factor + variation

    async def _check_service_health(self, service_name: str) -> bool:
        """Simulate checking service health."""
        # Simulate mostly healthy services with some variation by service
        base_reliability = 0.9
        service_factor = len(service_name) % 5 * 0.02  # Small variation by service
        return random.random() > (0.1 - service_factor)

    async def _get_agent_metrics(self, agent_name: str) -> Dict[str, Dict[str, Any]]:
        """Simulate getting agent metrics."""
        # Add some variation based on agent name
        agent_factor = len(agent_name) % 10 * 0.1

        return {
            "response_time": {
                "value": random.uniform(0.5 + agent_factor, 5.0),
                "unit": "seconds",
            },
            "error_rate": {"value": random.uniform(0.0, 0.1), "unit": "ratio"},
            "throughput": {
                "value": random.uniform(10 + agent_factor * 10, 100),
                "unit": "requests/minute",
            },
        }
