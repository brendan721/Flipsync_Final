#!/usr/bin/env python3
"""
Real-time Agent Health Monitoring System
=======================================

Phase 3.3 implementation for comprehensive real-time agent health monitoring
with automated recovery, performance analytics, and adaptive behavior.

Features:
- Real-time agent health monitoring
- Automated recovery mechanisms
- Performance analytics dashboard
- Health score calculation
- Alert generation and escalation
- Predictive health analysis

Technical Requirements:
- Health checks <50ms
- Recovery actions <500ms
- Production database integration
- Real-time dashboard updates
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

from fs_agt_clean.core.coordination.event_system import get_event_bus, Event, EventType
from fs_agt_clean.core.db.database import get_database

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Agent health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class RecoveryAction(Enum):
    """Types of recovery actions."""

    RESTART_AGENT = "restart_agent"
    REDUCE_LOAD = "reduce_load"
    REALLOCATE_RESOURCES = "reallocate_resources"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"
    PERFORMANCE_TUNING = "performance_tuning"


@dataclass
class HealthMetric:
    """Individual health metric measurement."""

    metric_name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    is_healthy: bool = True


@dataclass
class AgentHealthProfile:
    """Comprehensive health profile for an agent."""

    agent_id: str
    status: HealthStatus = HealthStatus.UNKNOWN
    health_score: float = 100.0
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_count: int = 0
    success_count: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0
    queue_size: int = 0
    metrics_history: Dict[str, deque] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=100))
    )
    alerts_generated: int = 0
    recovery_attempts: int = 0
    last_recovery_time: Optional[datetime] = None


@dataclass
class HealthAlert:
    """Health monitoring alert."""

    alert_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    message: str = ""
    metric_name: str = ""
    metric_value: float = 0.0
    threshold: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    resolved: bool = False
    recovery_action: Optional[RecoveryAction] = None


class RealTimeAgentHealthMonitor:
    """
    Comprehensive real-time agent health monitoring system with automated
    recovery and performance analytics.
    """

    def __init__(self, db_session=None):
        """Initialize the health monitoring system."""
        self.db_session = db_session or get_database()
        self.event_bus = get_event_bus()

        # Agent health profiles
        self.agent_profiles: Dict[str, AgentHealthProfile] = {}
        self.active_alerts: Dict[str, HealthAlert] = {}
        self.resolved_alerts: Dict[str, HealthAlert] = {}

        # Monitoring configuration
        self.health_check_interval = 5.0  # seconds
        self.heartbeat_timeout = 30.0  # seconds
        self.recovery_timeout = 300.0  # seconds
        self.alert_cooldown = 60.0  # seconds

        # Health thresholds
        self.health_thresholds = {
            "response_time": {"warning": 1000.0, "critical": 5000.0},  # ms
            "error_rate": {"warning": 5.0, "critical": 15.0},  # percentage
            "cpu_usage": {"warning": 80.0, "critical": 95.0},  # percentage
            "memory_usage": {"warning": 85.0, "critical": 95.0},  # percentage
            "queue_size": {"warning": 50, "critical": 100},  # count
            "health_score": {"warning": 70.0, "critical": 50.0},  # score
        }

        # Performance metrics
        self.monitoring_metrics = {
            "agents_monitored": 0,
            "health_checks_performed": 0,
            "alerts_generated": 0,
            "recovery_actions_taken": 0,
            "average_health_score": 100.0,
            "system_uptime": 0.0,
        }

        # Recovery handlers
        self.recovery_handlers: Dict[RecoveryAction, Callable] = {}
        self.alert_handlers: Dict[AlertSeverity, List[Callable]] = defaultdict(list)

        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        self._start_time = datetime.now(timezone.utc)

        logger.info("RealTimeAgentHealthMonitor initialized")

    async def start(self) -> None:
        """Start the health monitoring system."""
        try:
            # Start background monitoring tasks
            self._background_tasks.add(
                asyncio.create_task(self._health_check_monitor())
            )
            self._background_tasks.add(asyncio.create_task(self._alert_processor()))
            self._background_tasks.add(asyncio.create_task(self._recovery_monitor()))
            self._background_tasks.add(
                asyncio.create_task(self._performance_analytics())
            )

            # Register default recovery handlers
            await self._register_default_recovery_handlers()

            logger.info("Real-time agent health monitoring system started")

        except Exception as e:
            logger.error(f"Failed to start health monitoring system: {e}")
            raise

    async def stop(self) -> None:
        """Stop the health monitoring system."""
        try:
            # Signal shutdown
            self._shutdown_event.set()

            # Cancel background tasks
            for task in self._background_tasks:
                task.cancel()

            # Wait for tasks to complete
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            logger.info("Real-time agent health monitoring system stopped")

        except Exception as e:
            logger.error(f"Error stopping health monitoring system: {e}")

    async def register_agent(
        self, agent_id: str, capabilities: Optional[Set[str]] = None
    ) -> None:
        """Register an agent for health monitoring."""
        try:
            if agent_id not in self.agent_profiles:
                self.agent_profiles[agent_id] = AgentHealthProfile(agent_id=agent_id)
                self.monitoring_metrics["agents_monitored"] = len(self.agent_profiles)

                logger.info(f"Agent {agent_id} registered for health monitoring")

                # Publish registration event
                await self._publish_health_event(
                    agent_id,
                    "agent_registered",
                    {"capabilities": list(capabilities or [])},
                )

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")

    async def update_agent_metrics(
        self, agent_id: str, metrics: Dict[str, float]
    ) -> None:
        """Update agent health metrics."""
        start_time = time.perf_counter()

        try:
            if agent_id not in self.agent_profiles:
                await self.register_agent(agent_id)

            profile = self.agent_profiles[agent_id]
            profile.last_heartbeat = datetime.now(timezone.utc)

            # Update individual metrics
            for metric_name, value in metrics.items():
                if metric_name == "response_time":
                    profile.response_times.append(value)
                elif metric_name == "cpu_usage":
                    profile.cpu_usage = value
                elif metric_name == "memory_usage":
                    profile.memory_usage = value
                elif metric_name == "active_tasks":
                    profile.active_tasks = int(value)
                elif metric_name == "queue_size":
                    profile.queue_size = int(value)
                elif metric_name == "error_count":
                    profile.error_count = int(value)
                elif metric_name == "success_count":
                    profile.success_count = int(value)

                # Store in metrics history
                profile.metrics_history[metric_name].append(value)

            # Calculate health score
            profile.health_score = await self._calculate_health_score(profile)

            # Update health status
            profile.status = await self._determine_health_status(profile)

            # Check for alerts
            await self._check_health_alerts(profile)

            elapsed_time = (time.perf_counter() - start_time) * 1000

            if elapsed_time > 50:  # Log if health check takes too long
                logger.warning(f"Health check for {agent_id} took {elapsed_time:.2f}ms")

        except Exception as e:
            logger.error(f"Failed to update metrics for agent {agent_id}: {e}")

    async def get_agent_health(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get current health status for an agent."""
        if agent_id not in self.agent_profiles:
            return None

        profile = self.agent_profiles[agent_id]

        return {
            "agent_id": agent_id,
            "status": profile.status.value,
            "health_score": profile.health_score,
            "last_heartbeat": profile.last_heartbeat.isoformat(),
            "response_times": {
                "current": profile.response_times[-1] if profile.response_times else 0,
                "average": (
                    statistics.mean(profile.response_times)
                    if profile.response_times
                    else 0
                ),
                "p95": (
                    statistics.quantiles(profile.response_times, n=20)[18]
                    if len(profile.response_times) > 10
                    else 0
                ),
            },
            "error_rate": self._calculate_error_rate(profile),
            "cpu_usage": profile.cpu_usage,
            "memory_usage": profile.memory_usage,
            "active_tasks": profile.active_tasks,
            "queue_size": profile.queue_size,
            "alerts_count": len(
                [a for a in self.active_alerts.values() if a.agent_id == agent_id]
            ),
            "recovery_attempts": profile.recovery_attempts,
        }

    async def get_system_health_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive system health dashboard data."""
        try:
            # Calculate system-wide metrics
            total_agents = len(self.agent_profiles)
            healthy_agents = len(
                [
                    p
                    for p in self.agent_profiles.values()
                    if p.status == HealthStatus.HEALTHY
                ]
            )
            warning_agents = len(
                [
                    p
                    for p in self.agent_profiles.values()
                    if p.status == HealthStatus.WARNING
                ]
            )
            critical_agents = len(
                [
                    p
                    for p in self.agent_profiles.values()
                    if p.status == HealthStatus.CRITICAL
                ]
            )
            failed_agents = len(
                [
                    p
                    for p in self.agent_profiles.values()
                    if p.status == HealthStatus.FAILED
                ]
            )

            # Calculate average health score
            if self.agent_profiles:
                avg_health_score = statistics.mean(
                    [p.health_score for p in self.agent_profiles.values()]
                )
            else:
                avg_health_score = 100.0

            # System uptime
            uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system_overview": {
                    "total_agents": total_agents,
                    "healthy_agents": healthy_agents,
                    "warning_agents": warning_agents,
                    "critical_agents": critical_agents,
                    "failed_agents": failed_agents,
                    "system_health_percentage": (
                        (healthy_agents / total_agents * 100)
                        if total_agents > 0
                        else 100
                    ),
                    "average_health_score": avg_health_score,
                    "system_uptime_seconds": uptime,
                },
                "active_alerts": {
                    "total": len(self.active_alerts),
                    "critical": len(
                        [
                            a
                            for a in self.active_alerts.values()
                            if a.severity == AlertSeverity.CRITICAL
                        ]
                    ),
                    "warning": len(
                        [
                            a
                            for a in self.active_alerts.values()
                            if a.severity == AlertSeverity.WARNING
                        ]
                    ),
                    "emergency": len(
                        [
                            a
                            for a in self.active_alerts.values()
                            if a.severity == AlertSeverity.EMERGENCY
                        ]
                    ),
                },
                "performance_metrics": self.monitoring_metrics.copy(),
                "agent_details": [
                    {
                        "agent_id": profile.agent_id,
                        "status": profile.status.value,
                        "health_score": profile.health_score,
                        "last_heartbeat": profile.last_heartbeat.isoformat(),
                        "active_tasks": profile.active_tasks,
                        "queue_size": profile.queue_size,
                    }
                    for profile in self.agent_profiles.values()
                ],
            }

        except Exception as e:
            logger.error(f"Failed to generate health dashboard: {e}")
            return {"error": str(e)}

    # Private helper methods

    async def _calculate_health_score(self, profile: AgentHealthProfile) -> float:
        """Calculate overall health score for an agent."""
        try:
            scores = []

            # Response time score (lower is better)
            if profile.response_times:
                avg_response_time = statistics.mean(profile.response_times)
                response_score = max(
                    0, 100 - (avg_response_time / 50)
                )  # 50ms = 100 points
                scores.append(min(100, response_score))

            # Error rate score
            error_rate = self._calculate_error_rate(profile)
            error_score = max(0, 100 - (error_rate * 2))  # 50% error rate = 0 points
            scores.append(error_score)

            # Resource usage score
            cpu_score = max(0, 100 - profile.cpu_usage)
            memory_score = max(0, 100 - profile.memory_usage)
            scores.extend([cpu_score, memory_score])

            # Queue size score
            queue_score = max(0, 100 - (profile.queue_size * 2))  # 50 items = 0 points
            scores.append(queue_score)

            # Heartbeat freshness score
            time_since_heartbeat = (
                datetime.now(timezone.utc) - profile.last_heartbeat
            ).total_seconds()
            heartbeat_score = max(
                0, 100 - (time_since_heartbeat / 3)
            )  # 300s = 0 points
            scores.append(heartbeat_score)

            # Calculate weighted average
            return statistics.mean(scores) if scores else 0.0

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0

    def _calculate_error_rate(self, profile: AgentHealthProfile) -> float:
        """Calculate error rate percentage for an agent."""
        total_requests = profile.error_count + profile.success_count
        if total_requests == 0:
            return 0.0
        return (profile.error_count / total_requests) * 100

    async def _determine_health_status(
        self, profile: AgentHealthProfile
    ) -> HealthStatus:
        """Determine health status based on metrics and thresholds."""
        try:
            # Check for failed status (no heartbeat)
            time_since_heartbeat = (
                datetime.now(timezone.utc) - profile.last_heartbeat
            ).total_seconds()
            if time_since_heartbeat > self.heartbeat_timeout * 2:
                return HealthStatus.FAILED

            # Check for critical status
            if (
                profile.health_score
                < self.health_thresholds["health_score"]["critical"]
                or profile.cpu_usage > self.health_thresholds["cpu_usage"]["critical"]
                or profile.memory_usage
                > self.health_thresholds["memory_usage"]["critical"]
                or self._calculate_error_rate(profile)
                > self.health_thresholds["error_rate"]["critical"]
            ):
                return HealthStatus.CRITICAL

            # Check for warning status
            if (
                profile.health_score < self.health_thresholds["health_score"]["warning"]
                or profile.cpu_usage > self.health_thresholds["cpu_usage"]["warning"]
                or profile.memory_usage
                > self.health_thresholds["memory_usage"]["warning"]
                or self._calculate_error_rate(profile)
                > self.health_thresholds["error_rate"]["warning"]
            ):
                return HealthStatus.WARNING

            # Check if recovering
            if profile.last_recovery_time:
                time_since_recovery = (
                    datetime.now(timezone.utc) - profile.last_recovery_time
                ).total_seconds()
                if time_since_recovery < self.recovery_timeout:
                    return HealthStatus.RECOVERING

            return HealthStatus.HEALTHY

        except Exception as e:
            logger.error(f"Error determining health status: {e}")
            return HealthStatus.UNKNOWN

    async def _check_health_alerts(self, profile: AgentHealthProfile) -> None:
        """Check if any health alerts should be generated."""
        try:
            current_time = datetime.now(timezone.utc)

            # Check each metric against thresholds
            metrics_to_check = {
                "health_score": profile.health_score,
                "cpu_usage": profile.cpu_usage,
                "memory_usage": profile.memory_usage,
                "error_rate": self._calculate_error_rate(profile),
                "queue_size": profile.queue_size,
            }

            for metric_name, value in metrics_to_check.items():
                thresholds = self.health_thresholds.get(metric_name, {})

                # Check critical threshold
                if "critical" in thresholds and value > thresholds["critical"]:
                    await self._generate_alert(
                        profile.agent_id,
                        AlertSeverity.CRITICAL,
                        metric_name,
                        value,
                        thresholds["critical"],
                    )

                # Check warning threshold
                elif "warning" in thresholds and value > thresholds["warning"]:
                    await self._generate_alert(
                        profile.agent_id,
                        AlertSeverity.WARNING,
                        metric_name,
                        value,
                        thresholds["warning"],
                    )

            # Check for heartbeat timeout
            time_since_heartbeat = (
                current_time - profile.last_heartbeat
            ).total_seconds()
            if time_since_heartbeat > self.heartbeat_timeout:
                await self._generate_alert(
                    profile.agent_id,
                    AlertSeverity.EMERGENCY,
                    "heartbeat_timeout",
                    time_since_heartbeat,
                    self.heartbeat_timeout,
                )

        except Exception as e:
            logger.error(f"Error checking health alerts: {e}")

    async def _generate_alert(
        self,
        agent_id: str,
        severity: AlertSeverity,
        metric_name: str,
        value: float,
        threshold: float,
    ) -> None:
        """Generate a health alert."""
        try:
            # Check for alert cooldown to prevent spam
            recent_alerts = [
                alert
                for alert in self.active_alerts.values()
                if (
                    alert.agent_id == agent_id
                    and alert.metric_name == metric_name
                    and (datetime.now(timezone.utc) - alert.timestamp).total_seconds()
                    < self.alert_cooldown
                )
            ]

            if recent_alerts:
                return  # Skip duplicate alert

            # Create alert
            alert = HealthAlert(
                agent_id=agent_id,
                severity=severity,
                metric_name=metric_name,
                metric_value=value,
                threshold=threshold,
                message=f"Agent {agent_id} {metric_name} ({value:.2f}) exceeded {severity.value} threshold ({threshold:.2f})",
            )

            # Determine recovery action
            alert.recovery_action = await self._determine_recovery_action(alert)

            # Store alert
            self.active_alerts[alert.alert_id] = alert

            # Update metrics
            self.monitoring_metrics["alerts_generated"] += 1
            if agent_id in self.agent_profiles:
                self.agent_profiles[agent_id].alerts_generated += 1

            # Publish alert event
            await self._publish_alert_event(alert)

            # Trigger recovery action if needed
            if alert.recovery_action and severity in [
                AlertSeverity.CRITICAL,
                AlertSeverity.EMERGENCY,
            ]:
                await self._trigger_recovery_action(alert)

            logger.warning(
                f"Generated {severity.value} alert for agent {agent_id}: {alert.message}"
            )

        except Exception as e:
            logger.error(f"Error generating alert: {e}")

    async def _determine_recovery_action(
        self, alert: HealthAlert
    ) -> Optional[RecoveryAction]:
        """Determine appropriate recovery action for an alert."""
        try:
            if alert.severity == AlertSeverity.EMERGENCY:
                if alert.metric_name == "heartbeat_timeout":
                    return RecoveryAction.RESTART_AGENT
                else:
                    return RecoveryAction.ESCALATE_TO_HUMAN

            elif alert.severity == AlertSeverity.CRITICAL:
                if alert.metric_name in ["cpu_usage", "memory_usage"]:
                    return RecoveryAction.REDUCE_LOAD
                elif alert.metric_name == "error_rate":
                    return RecoveryAction.PERFORMANCE_TUNING
                elif alert.metric_name == "queue_size":
                    return RecoveryAction.REALLOCATE_RESOURCES
                else:
                    return RecoveryAction.RESTART_AGENT

            elif alert.severity == AlertSeverity.WARNING:
                return RecoveryAction.PERFORMANCE_TUNING

            return None

        except Exception as e:
            logger.error(f"Error determining recovery action: {e}")
            return None

    async def _trigger_recovery_action(self, alert: HealthAlert) -> None:
        """Trigger automated recovery action."""
        try:
            if not alert.recovery_action:
                return

            start_time = time.perf_counter()

            # Get recovery handler
            handler = self.recovery_handlers.get(alert.recovery_action)
            if handler:
                success = await handler(alert)

                if success:
                    # Update agent profile
                    if alert.agent_id in self.agent_profiles:
                        profile = self.agent_profiles[alert.agent_id]
                        profile.recovery_attempts += 1
                        profile.last_recovery_time = datetime.now(timezone.utc)

                    # Update metrics
                    self.monitoring_metrics["recovery_actions_taken"] += 1

                    elapsed_time = (time.perf_counter() - start_time) * 1000
                    logger.info(
                        f"Recovery action {alert.recovery_action.value} completed for agent "
                        f"{alert.agent_id} ({elapsed_time:.2f}ms)"
                    )
                else:
                    logger.error(
                        f"Recovery action {alert.recovery_action.value} failed for agent {alert.agent_id}"
                    )
            else:
                logger.warning(
                    f"No handler registered for recovery action {alert.recovery_action.value}"
                )

        except Exception as e:
            logger.error(f"Error triggering recovery action: {e}")

    async def _register_default_recovery_handlers(self) -> None:
        """Register default recovery action handlers."""
        try:
            self.recovery_handlers[RecoveryAction.RESTART_AGENT] = (
                self._handle_restart_agent
            )
            self.recovery_handlers[RecoveryAction.REDUCE_LOAD] = (
                self._handle_reduce_load
            )
            self.recovery_handlers[RecoveryAction.REALLOCATE_RESOURCES] = (
                self._handle_reallocate_resources
            )
            self.recovery_handlers[RecoveryAction.PERFORMANCE_TUNING] = (
                self._handle_performance_tuning
            )
            self.recovery_handlers[RecoveryAction.ESCALATE_TO_HUMAN] = (
                self._handle_escalate_to_human
            )

        except Exception as e:
            logger.error(f"Error registering recovery handlers: {e}")

    # Default recovery handlers

    async def _handle_restart_agent(self, alert: HealthAlert) -> bool:
        """Handle agent restart recovery action."""
        try:
            # In a real implementation, this would trigger agent restart
            logger.info(f"Simulating restart for agent {alert.agent_id}")

            # Publish restart event
            await self._publish_health_event(
                alert.agent_id,
                "agent_restart_triggered",
                {"reason": alert.message, "recovery_action": "restart"},
            )

            return True

        except Exception as e:
            logger.error(f"Error handling agent restart: {e}")
            return False

    async def _handle_reduce_load(self, alert: HealthAlert) -> bool:
        """Handle load reduction recovery action."""
        try:
            # In a real implementation, this would reduce agent workload
            logger.info(f"Simulating load reduction for agent {alert.agent_id}")

            # Publish load reduction event
            await self._publish_health_event(
                alert.agent_id,
                "load_reduction_triggered",
                {"reason": alert.message, "recovery_action": "reduce_load"},
            )

            return True

        except Exception as e:
            logger.error(f"Error handling load reduction: {e}")
            return False

    async def _handle_reallocate_resources(self, alert: HealthAlert) -> bool:
        """Handle resource reallocation recovery action."""
        try:
            # In a real implementation, this would reallocate resources
            logger.info(f"Simulating resource reallocation for agent {alert.agent_id}")

            # Publish reallocation event
            await self._publish_health_event(
                alert.agent_id,
                "resource_reallocation_triggered",
                {"reason": alert.message, "recovery_action": "reallocate_resources"},
            )

            return True

        except Exception as e:
            logger.error(f"Error handling resource reallocation: {e}")
            return False

    async def _handle_performance_tuning(self, alert: HealthAlert) -> bool:
        """Handle performance tuning recovery action."""
        try:
            # In a real implementation, this would adjust performance parameters
            logger.info(f"Simulating performance tuning for agent {alert.agent_id}")

            # Publish tuning event
            await self._publish_health_event(
                alert.agent_id,
                "performance_tuning_triggered",
                {"reason": alert.message, "recovery_action": "performance_tuning"},
            )

            return True

        except Exception as e:
            logger.error(f"Error handling performance tuning: {e}")
            return False

    async def _handle_escalate_to_human(self, alert: HealthAlert) -> bool:
        """Handle escalation to human operators."""
        try:
            # In a real implementation, this would notify human operators
            logger.critical(
                f"ESCALATING TO HUMAN: Agent {alert.agent_id} - {alert.message}"
            )

            # Publish escalation event
            await self._publish_health_event(
                alert.agent_id,
                "human_escalation_triggered",
                {
                    "reason": alert.message,
                    "recovery_action": "escalate_to_human",
                    "severity": "CRITICAL",
                },
            )

            return True

        except Exception as e:
            logger.error(f"Error handling human escalation: {e}")
            return False

    # Event publishing helpers

    async def _publish_health_event(
        self, agent_id: str, event_name: str, data: Dict[str, Any]
    ) -> None:
        """Publish a health monitoring event."""
        try:
            event = Event(
                event_type=EventType.NOTIFICATION,
                source="health_monitor",
                target=agent_id,
                data={
                    "agent_id": agent_id,
                    "event_name": event_name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **data,
                },
            )
            await self.event_bus.publish(event)

        except Exception as e:
            logger.error(f"Failed to publish health event: {e}")

    async def _publish_alert_event(self, alert: HealthAlert) -> None:
        """Publish an alert event."""
        try:
            event = Event(
                event_type=EventType.NOTIFICATION,
                source="health_monitor",
                target="system",
                data={
                    "alert_id": alert.alert_id,
                    "agent_id": alert.agent_id,
                    "severity": alert.severity.value,
                    "metric_name": alert.metric_name,
                    "metric_value": alert.metric_value,
                    "threshold": alert.threshold,
                    "message": alert.message,
                    "recovery_action": (
                        alert.recovery_action.value if alert.recovery_action else None
                    ),
                    "timestamp": alert.timestamp.isoformat(),
                },
            )
            await self.event_bus.publish(event)

        except Exception as e:
            logger.error(f"Failed to publish alert event: {e}")

    # Background monitoring tasks

    async def _health_check_monitor(self) -> None:
        """Continuously monitor agent health."""
        while not self._shutdown_event.is_set():
            try:
                start_time = time.perf_counter()

                # Perform health checks for all registered agents
                for agent_id, profile in list(self.agent_profiles.items()):
                    # Check heartbeat timeout
                    time_since_heartbeat = (
                        datetime.now(timezone.utc) - profile.last_heartbeat
                    ).total_seconds()

                    if time_since_heartbeat > self.heartbeat_timeout:
                        # Update status to failed
                        profile.status = HealthStatus.FAILED
                        profile.health_score = 0.0

                        # Generate emergency alert if not already generated
                        await self._check_health_alerts(profile)

                    # Update health score and status for active agents
                    elif time_since_heartbeat < self.heartbeat_timeout:
                        profile.health_score = await self._calculate_health_score(
                            profile
                        )
                        profile.status = await self._determine_health_status(profile)

                # Update system metrics
                self.monitoring_metrics["health_checks_performed"] += 1
                if self.agent_profiles:
                    self.monitoring_metrics["average_health_score"] = statistics.mean(
                        [p.health_score for p in self.agent_profiles.values()]
                    )

                elapsed_time = (time.perf_counter() - start_time) * 1000

                if elapsed_time > 50:  # Log if health check cycle takes too long
                    logger.warning(f"Health check cycle took {elapsed_time:.2f}ms")

                # Wait before next health check cycle
                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Health check monitor error: {e}")
                await asyncio.sleep(5.0)

    async def _alert_processor(self) -> None:
        """Process and manage health alerts."""
        while not self._shutdown_event.is_set():
            try:
                datetime.now(timezone.utc)
                alerts_to_resolve = []

                # Check for alerts that can be auto-resolved
                for alert_id, alert in list(self.active_alerts.items()):
                    # Check if the underlying issue has been resolved
                    if alert.agent_id in self.agent_profiles:
                        profile = self.agent_profiles[alert.agent_id]

                        # Check if the metric that triggered the alert is now healthy
                        current_value = self._get_current_metric_value(
                            profile, alert.metric_name
                        )

                        if current_value is not None:
                            # Check if value is below warning threshold
                            thresholds = self.health_thresholds.get(
                                alert.metric_name, {}
                            )
                            warning_threshold = thresholds.get("warning", float("inf"))

                            if current_value < warning_threshold:
                                alerts_to_resolve.append(alert_id)

                # Resolve alerts
                for alert_id in alerts_to_resolve:
                    alert = self.active_alerts[alert_id]
                    alert.resolved = True

                    # Move to resolved alerts
                    self.resolved_alerts[alert_id] = alert
                    del self.active_alerts[alert_id]

                    logger.info(
                        f"Auto-resolved alert {alert_id} for agent {alert.agent_id}"
                    )

                # Wait before next alert processing cycle
                await asyncio.sleep(10.0)

            except Exception as e:
                logger.error(f"Alert processor error: {e}")
                await asyncio.sleep(5.0)

    async def _recovery_monitor(self) -> None:
        """Monitor recovery actions and their effectiveness."""
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.now(timezone.utc)

                # Check agents that are in recovery
                for agent_id, profile in list(self.agent_profiles.items()):
                    if (
                        profile.status == HealthStatus.RECOVERING
                        and profile.last_recovery_time
                    ):

                        time_since_recovery = (
                            current_time - profile.last_recovery_time
                        ).total_seconds()

                        # Check if recovery timeout has been exceeded
                        if time_since_recovery > self.recovery_timeout:
                            # Recovery failed, escalate
                            logger.warning(
                                f"Recovery timeout for agent {agent_id}, escalating"
                            )

                            # Generate escalation alert
                            await self._generate_alert(
                                agent_id,
                                AlertSeverity.EMERGENCY,
                                "recovery_timeout",
                                time_since_recovery,
                                self.recovery_timeout,
                            )

                # Wait before next recovery monitoring cycle
                await asyncio.sleep(30.0)

            except Exception as e:
                logger.error(f"Recovery monitor error: {e}")
                await asyncio.sleep(10.0)

    async def _performance_analytics(self) -> None:
        """Perform performance analytics and system optimization."""
        while not self._shutdown_event.is_set():
            try:
                # Update system uptime
                uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
                self.monitoring_metrics["system_uptime"] = uptime

                # Calculate system-wide performance metrics
                if self.agent_profiles:
                    # Calculate average response time across all agents
                    all_response_times = []
                    for profile in self.agent_profiles.values():
                        if profile.response_times:
                            all_response_times.extend(profile.response_times)

                    if all_response_times:
                        avg_response_time = statistics.mean(all_response_times)
                        self.monitoring_metrics["average_response_time"] = (
                            avg_response_time
                        )

                    # Calculate system error rate
                    total_errors = sum(
                        p.error_count for p in self.agent_profiles.values()
                    )
                    total_successes = sum(
                        p.success_count for p in self.agent_profiles.values()
                    )
                    total_requests = total_errors + total_successes

                    if total_requests > 0:
                        system_error_rate = (total_errors / total_requests) * 100
                        self.monitoring_metrics["system_error_rate"] = system_error_rate

                # Log performance analytics
                logger.debug(f"Performance analytics: {self.monitoring_metrics}")

                # Wait before next analytics cycle
                await asyncio.sleep(60.0)  # Run analytics every minute

            except Exception as e:
                logger.error(f"Performance analytics error: {e}")
                await asyncio.sleep(10.0)

    def _get_current_metric_value(
        self, profile: AgentHealthProfile, metric_name: str
    ) -> Optional[float]:
        """Get current value for a specific metric."""
        try:
            if metric_name == "health_score":
                return profile.health_score
            elif metric_name == "cpu_usage":
                return profile.cpu_usage
            elif metric_name == "memory_usage":
                return profile.memory_usage
            elif metric_name == "error_rate":
                return self._calculate_error_rate(profile)
            elif metric_name == "queue_size":
                return float(profile.queue_size)
            elif metric_name == "response_time" and profile.response_times:
                return profile.response_times[-1]
            else:
                return None

        except Exception as e:
            logger.error(f"Error getting metric value: {e}")
            return None
