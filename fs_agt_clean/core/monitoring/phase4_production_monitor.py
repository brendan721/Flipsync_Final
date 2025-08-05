#!/usr/bin/env python3
"""
Phase 4: Production Monitoring & Validation System
=================================================

Extended monitoring systems for real-time multi-agent operations with comprehensive
performance tracking, health monitoring, and validation testing capabilities.

Features:
- Real-time multi-agent coordination monitoring
- Advanced performance metrics and analytics
- Health monitoring with predictive alerts
- Comprehensive validation testing framework
- Production-grade monitoring dashboard
- Integration with existing monitoring infrastructure

Technical Requirements:
- Real-time monitoring <50ms latency
- Health checks <25ms
- Production database integration
- 4+1 architecture compatibility
"""

import asyncio
import logging
import time
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

# Import existing monitoring infrastructure
from fs_agt_clean.core.monitoring.realtime_agent_monitor import RealTimeAgentMonitor
from fs_agt_clean.services.infrastructure.monitoring.realtime import (
    RealTimeMonitoringService,
)

# Import Phase 4 components for monitoring
from fs_agt_clean.core.coordination.phase4_multi_agent_coordinator import (
    Phase4MultiAgentCoordinator,
)

# MIGRATED: Use unified WebSocket system instead of Phase4EnhancedWebSocket
from fs_agt_clean.core.websocket.manager import EnhancedWebSocketManager
from fs_agt_clean.core.coordination.phase4_advanced_conflict_resolution import (
    Phase4AdvancedConflictResolver,
)

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""

    component_id: str
    component_type: str
    response_time_ms: float
    throughput_ops_per_sec: float
    error_rate_percentage: float
    cpu_usage_percentage: float
    memory_usage_mb: float
    success_rate_percentage: float
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class HealthCheck:
    """Health check result."""

    component_id: str
    status: HealthStatus
    check_time_ms: float
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None


@dataclass
class SystemAlert:
    """System alert notification."""

    alert_id: str
    level: AlertLevel
    component_id: str
    message: str
    details: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False


class Phase4ProductionMonitor:
    """
    Production monitoring system for Phase 4 multi-agent coordination.

    Provides comprehensive monitoring, health checks, and validation
    for all Phase 4 components with real-time analytics and alerting.
    """

    def __init__(self, monitoring_interval_ms: float = 30000.0):
        """Initialize the production monitoring system.

        Args:
            monitoring_interval_ms: Monitoring interval in milliseconds (default: 30 seconds)
        """
        self.monitoring_interval_ms = monitoring_interval_ms
        self.monitor_id = f"phase4_monitor_{uuid.uuid4().hex[:8]}"

        # Use existing monitoring infrastructure as foundation
        self.realtime_monitor = RealTimeAgentMonitor(health_check_interval_ms=25.0)
        self.monitoring_service = RealTimeMonitoringService()

        # Phase 4 component references
        self.coordinator: Optional[Phase4MultiAgentCoordinator] = None
        self.websocket_system: Optional[EnhancedWebSocketManager] = (
            None  # MIGRATED: Use unified WebSocket system
        )
        self.conflict_resolver: Optional[Phase4AdvancedConflictResolver] = None

        # Monitoring state
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        self.active_alerts: Dict[str, SystemAlert] = {}
        self.alert_history: List[SystemAlert] = []

        # Monitoring tasks
        self.is_monitoring = False
        self.monitoring_tasks: List[asyncio.Task] = []

        # Performance thresholds
        self.performance_thresholds = {
            "coordination_time_ms": 100.0,
            "websocket_delivery_ms": 100.0,
            "conflict_resolution_ms": 200.0,
            "health_check_ms": 25.0,
            "error_rate_percentage": 5.0,
            "success_rate_percentage": 95.0,
        }

        logger.info(f"🚀 Phase 4 Production Monitor initialized: {self.monitor_id}")
        logger.info(f"📊 Monitoring interval: {self.monitoring_interval_ms}ms")

    async def initialize(
        self,
        coordinator: Phase4MultiAgentCoordinator,
        websocket_system: EnhancedWebSocketManager,  # MIGRATED: Use unified WebSocket system
        conflict_resolver: Phase4AdvancedConflictResolver,
    ) -> bool:
        """Initialize monitoring with Phase 4 components.

        Args:
            coordinator: Phase 4 multi-agent coordinator
            websocket_system: Phase 4 enhanced WebSocket system
            conflict_resolver: Phase 4 advanced conflict resolver
        """
        try:
            start_time = time.perf_counter()

            # Store component references
            self.coordinator = coordinator
            self.websocket_system = websocket_system
            self.conflict_resolver = conflict_resolver

            # Initialize base monitoring
            await self.realtime_monitor.start_monitoring()

            # Register Phase 4 components for monitoring
            autonomous_agents = [
                "market_agent",
                "executive_agent",
                "content_agent",
                "logistics_agent",
            ]

            for agent_id in autonomous_agents:
                await self.realtime_monitor.register_agent(
                    agent_id=agent_id,
                    agent_type="autonomous",
                    health_check_interval_ms=25.0,
                )

                # Initialize performance metrics
                self.performance_metrics[agent_id] = PerformanceMetrics(
                    component_id=agent_id,
                    component_type="autonomous_agent",
                    response_time_ms=0.0,
                    throughput_ops_per_sec=0.0,
                    error_rate_percentage=0.0,
                    cpu_usage_percentage=0.0,
                    memory_usage_mb=0.0,
                    success_rate_percentage=100.0,
                )

                logger.info(f"✅ Registered agent for monitoring: {agent_id}")

            # Initialize Phase 4 component metrics
            phase4_components = [
                ("phase4_coordinator", "coordination"),
                ("phase4_websocket", "websocket"),
                ("phase4_conflict_resolver", "conflict_resolution"),
            ]

            for component_id, component_type in phase4_components:
                self.performance_metrics[component_id] = PerformanceMetrics(
                    component_id=component_id,
                    component_type=component_type,
                    response_time_ms=0.0,
                    throughput_ops_per_sec=0.0,
                    error_rate_percentage=0.0,
                    cpu_usage_percentage=0.0,
                    memory_usage_mb=0.0,
                    success_rate_percentage=100.0,
                )

            initialization_time = (time.perf_counter() - start_time) * 1000

            logger.info(
                f"✅ Phase 4 production monitor initialized in {initialization_time:.2f}ms"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize production monitor: {e}")
            return False

    async def start_monitoring(self) -> bool:
        """Start comprehensive production monitoring."""
        try:
            if self.is_monitoring:
                logger.warning("Production monitoring is already running")
                return True

            self.is_monitoring = True

            # Start performance monitoring
            performance_task = asyncio.create_task(self._monitor_performance())
            self.monitoring_tasks.append(performance_task)

            # Start health monitoring
            health_task = asyncio.create_task(self._monitor_health())
            self.monitoring_tasks.append(health_task)

            # Start alert monitoring
            alert_task = asyncio.create_task(self._monitor_alerts())
            self.monitoring_tasks.append(alert_task)

            # Start validation testing
            validation_task = asyncio.create_task(self._run_validation_tests())
            self.monitoring_tasks.append(validation_task)

            logger.info("🚀 Phase 4 production monitoring started")
            return True

        except Exception as e:
            logger.error(f"Failed to start production monitoring: {e}")
            self.is_monitoring = False
            return False

    async def _monitor_performance(self):
        """Monitor performance metrics for all components."""
        logger.info("📊 Starting performance monitoring")

        while self.is_monitoring:
            try:
                await asyncio.sleep(self.monitoring_interval_ms / 1000.0)

                # Monitor coordinator performance
                if self.coordinator:
                    await self._collect_coordinator_metrics()

                # Monitor WebSocket performance
                if self.websocket_system:
                    await self._collect_websocket_metrics()

                # Monitor conflict resolver performance
                if self.conflict_resolver:
                    await self._collect_conflict_resolver_metrics()

                # Monitor agent performance
                await self._collect_agent_metrics()

                # Check performance thresholds
                await self._check_performance_thresholds()

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")

    async def _monitor_health(self):
        """Monitor health status of all components."""
        logger.info("🏥 Starting health monitoring")

        while self.is_monitoring:
            try:
                await asyncio.sleep(5.0)  # Health checks every 5 seconds

                # Perform health checks
                await self._perform_health_checks()

            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")

    async def _monitor_alerts(self):
        """Monitor and manage system alerts."""
        logger.info("🚨 Starting alert monitoring")

        while self.is_monitoring:
            try:
                await asyncio.sleep(10.0)  # Check alerts every 10 seconds

                # Process active alerts
                await self._process_alerts()

                # Clean up resolved alerts
                await self._cleanup_alerts()

            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")

    async def _run_validation_tests(self):
        """Run periodic validation tests."""
        logger.info("🧪 Starting validation testing")

        while self.is_monitoring:
            try:
                await asyncio.sleep(300.0)  # Validation tests every 5 minutes

                # Run Phase 4 validation tests
                await self._validate_phase4_components()

            except Exception as e:
                logger.error(f"Error in validation testing: {e}")

    async def _collect_coordinator_metrics(self):
        """Collect metrics from the multi-agent coordinator."""
        try:
            start_time = time.perf_counter()

            # Get coordinator status
            status = await self.coordinator.get_coordination_status()

            collection_time = (time.perf_counter() - start_time) * 1000

            # Update metrics
            metrics = self.performance_metrics.get("phase4_coordinator")
            if metrics:
                metrics.response_time_ms = collection_time
                metrics.success_rate_percentage = status["metrics"][
                    "performance_target_met_percentage"
                ]
                metrics.throughput_ops_per_sec = status["metrics"][
                    "completed_tasks"
                ] / max(
                    1,
                    (
                        datetime.now(timezone.utc)
                        - datetime.fromisoformat(
                            status["metrics"]["last_updated"].replace("Z", "+00:00")
                        )
                    ).total_seconds(),
                )
                metrics.last_updated = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Error collecting coordinator metrics: {e}")

    async def _collect_websocket_metrics(self):
        """Collect metrics from the WebSocket system."""
        try:
            start_time = time.perf_counter()

            # Get WebSocket status
            status = await self.websocket_system.get_connection_status()

            collection_time = (time.perf_counter() - start_time) * 1000

            # Update metrics
            metrics = self.performance_metrics.get("phase4_websocket")
            if metrics:
                metrics.response_time_ms = collection_time

                # Calculate average success rate across all agents
                agent_metrics = status.get("metrics", {})
                if agent_metrics:
                    success_rates = [
                        agent_data.get("success_rate_percentage", 0.0)
                        for agent_data in agent_metrics.values()
                    ]
                    metrics.success_rate_percentage = (
                        sum(success_rates) / len(success_rates)
                        if success_rates
                        else 0.0
                    )

                metrics.last_updated = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Error collecting WebSocket metrics: {e}")

    async def _collect_conflict_resolver_metrics(self):
        """Collect metrics from the conflict resolver."""
        try:
            start_time = time.perf_counter()

            # Get conflict resolver status
            status = await self.conflict_resolver.get_conflict_status()

            collection_time = (time.perf_counter() - start_time) * 1000

            # Update metrics
            metrics = self.performance_metrics.get("phase4_conflict_resolver")
            if metrics:
                metrics.response_time_ms = collection_time
                metrics.success_rate_percentage = status["metrics"][
                    "performance_target_met_percentage"
                ]
                metrics.last_updated = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Error collecting conflict resolver metrics: {e}")

    async def _collect_agent_metrics(self):
        """Collect metrics from autonomous agents."""
        try:
            autonomous_agents = [
                "market_agent",
                "executive_agent",
                "content_agent",
                "logistics_agent",
            ]

            for agent_id in autonomous_agents:
                start_time = time.perf_counter()

                # Get agent health from realtime monitor using correct method
                health = await self.realtime_monitor.get_agent_health_status(agent_id)

                collection_time = (time.perf_counter() - start_time) * 1000

                # Update metrics
                metrics = self.performance_metrics.get(agent_id)
                if metrics:
                    metrics.response_time_ms = collection_time
                    metrics.success_rate_percentage = (
                        100.0 if health.get("status") == "healthy" else 50.0
                    )
                    metrics.last_updated = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Error collecting agent metrics: {e}")

    async def _check_performance_thresholds(self):
        """Check performance metrics against thresholds and generate alerts."""
        try:
            for component_id, metrics in self.performance_metrics.items():
                # Check response time thresholds
                threshold_key = f"{metrics.component_type}_time_ms"
                threshold = self.performance_thresholds.get(threshold_key, 1000.0)

                if metrics.response_time_ms > threshold:
                    await self._create_alert(
                        level=AlertLevel.WARNING,
                        component_id=component_id,
                        message=f"Response time exceeded threshold: {metrics.response_time_ms:.2f}ms > {threshold}ms",
                        details={
                            "response_time_ms": metrics.response_time_ms,
                            "threshold_ms": threshold,
                        },
                    )

                # Check success rate thresholds
                success_threshold = self.performance_thresholds.get(
                    "success_rate_percentage", 95.0
                )
                if metrics.success_rate_percentage < success_threshold:
                    await self._create_alert(
                        level=AlertLevel.ERROR,
                        component_id=component_id,
                        message=f"Success rate below threshold: {metrics.success_rate_percentage:.1f}% < {success_threshold}%",
                        details={
                            "success_rate": metrics.success_rate_percentage,
                            "threshold": success_threshold,
                        },
                    )

        except Exception as e:
            logger.error(f"Error checking performance thresholds: {e}")

    async def _perform_health_checks(self):
        """Perform health checks on all components."""
        try:
            # Health check coordinator
            if self.coordinator:
                await self._health_check_coordinator()

            # Health check WebSocket system
            if self.websocket_system:
                await self._health_check_websocket()

            # Health check conflict resolver
            if self.conflict_resolver:
                await self._health_check_conflict_resolver()

            # Health check agents
            await self._health_check_agents()

        except Exception as e:
            logger.error(f"Error performing health checks: {e}")

    async def _health_check_coordinator(self):
        """Health check for the multi-agent coordinator."""
        start_time = time.perf_counter()

        try:
            # Test coordinator responsiveness
            status = await asyncio.wait_for(
                self.coordinator.get_coordination_status(), timeout=1.0
            )

            check_time = (time.perf_counter() - start_time) * 1000

            # Determine health status
            if status["is_running"] and check_time < 50.0:
                health_status = HealthStatus.HEALTHY
            elif check_time < 100.0:
                health_status = HealthStatus.WARNING
            else:
                health_status = HealthStatus.CRITICAL

            self.health_checks["phase4_coordinator"] = HealthCheck(
                component_id="phase4_coordinator",
                status=health_status,
                check_time_ms=check_time,
                details={
                    "is_running": status["is_running"],
                    "active_tasks": status["active_tasks"],
                },
            )

        except Exception as e:
            check_time = (time.perf_counter() - start_time) * 1000
            self.health_checks["phase4_coordinator"] = HealthCheck(
                component_id="phase4_coordinator",
                status=HealthStatus.FAILED,
                check_time_ms=check_time,
                details={},
                error_message=str(e),
            )

    async def _health_check_websocket(self):
        """Health check for the WebSocket system."""
        start_time = time.perf_counter()

        try:
            # Test WebSocket responsiveness
            status = await asyncio.wait_for(
                self.websocket_system.get_connection_status(), timeout=1.0
            )

            check_time = (time.perf_counter() - start_time) * 1000

            # Determine health status
            if status["is_running"] and check_time < 50.0:
                health_status = HealthStatus.HEALTHY
            elif check_time < 100.0:
                health_status = HealthStatus.WARNING
            else:
                health_status = HealthStatus.CRITICAL

            self.health_checks["phase4_websocket"] = HealthCheck(
                component_id="phase4_websocket",
                status=health_status,
                check_time_ms=check_time,
                details={
                    "is_running": status["is_running"],
                    "active_connections": status["active_connections"],
                },
            )

        except Exception as e:
            check_time = (time.perf_counter() - start_time) * 1000
            self.health_checks["phase4_websocket"] = HealthCheck(
                component_id="phase4_websocket",
                status=HealthStatus.FAILED,
                check_time_ms=check_time,
                details={},
                error_message=str(e),
            )

    async def _health_check_conflict_resolver(self):
        """Health check for the conflict resolver."""
        start_time = time.perf_counter()

        try:
            # Test conflict resolver responsiveness
            status = await asyncio.wait_for(
                self.conflict_resolver.get_conflict_status(), timeout=1.0
            )

            check_time = (time.perf_counter() - start_time) * 1000

            # Determine health status
            if status["is_monitoring"] and check_time < 50.0:
                health_status = HealthStatus.HEALTHY
            elif check_time < 100.0:
                health_status = HealthStatus.WARNING
            else:
                health_status = HealthStatus.CRITICAL

            self.health_checks["phase4_conflict_resolver"] = HealthCheck(
                component_id="phase4_conflict_resolver",
                status=health_status,
                check_time_ms=check_time,
                details={
                    "is_monitoring": status["is_monitoring"],
                    "active_conflicts": status["active_conflicts"],
                },
            )

        except Exception as e:
            check_time = (time.perf_counter() - start_time) * 1000
            self.health_checks["phase4_conflict_resolver"] = HealthCheck(
                component_id="phase4_conflict_resolver",
                status=health_status,
                check_time_ms=check_time,
                details={},
                error_message=str(e),
            )

    async def _health_check_agents(self):
        """Health check for autonomous agents."""
        autonomous_agents = [
            "market_agent",
            "executive_agent",
            "content_agent",
            "logistics_agent",
        ]

        for agent_id in autonomous_agents:
            start_time = time.perf_counter()

            try:
                # Get agent health from realtime monitor using correct method
                health = await asyncio.wait_for(
                    self.realtime_monitor.get_agent_health_status(agent_id), timeout=0.5
                )

                check_time = (time.perf_counter() - start_time) * 1000

                # Map health status
                status_mapping = {
                    "healthy": HealthStatus.HEALTHY,
                    "warning": HealthStatus.WARNING,
                    "critical": HealthStatus.CRITICAL,
                    "failed": HealthStatus.FAILED,
                }

                health_status = status_mapping.get(
                    health.get("status", "unknown"), HealthStatus.UNKNOWN
                )

                self.health_checks[agent_id] = HealthCheck(
                    component_id=agent_id,
                    status=health_status,
                    check_time_ms=check_time,
                    details=health,
                )

            except Exception as e:
                check_time = (time.perf_counter() - start_time) * 1000
                self.health_checks[agent_id] = HealthCheck(
                    component_id=agent_id,
                    status=HealthStatus.FAILED,
                    check_time_ms=check_time,
                    details={},
                    error_message=str(e),
                )

    async def _create_alert(
        self,
        level: AlertLevel,
        component_id: str,
        message: str,
        details: Dict[str, Any],
    ):
        """Create a system alert."""
        alert_id = str(uuid.uuid4())

        alert = SystemAlert(
            alert_id=alert_id,
            level=level,
            component_id=component_id,
            message=message,
            details=details,
        )

        # Check if similar alert already exists
        existing_alert = None
        for existing_id, existing in self.active_alerts.items():
            if (
                existing.component_id == component_id
                and existing.level == level
                and existing.message == message
            ):
                existing_alert = existing
                break

        if not existing_alert:
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            logger.warning(
                f"🚨 {level.value.upper()} Alert: {component_id} - {message}"
            )

        return alert_id

    async def _process_alerts(self):
        """Process and manage active alerts."""
        try:
            # Auto-resolve alerts for healthy components
            for alert_id, alert in list(self.active_alerts.items()):
                health_check = self.health_checks.get(alert.component_id)

                if health_check and health_check.status == HealthStatus.HEALTHY:
                    # Auto-resolve alert
                    alert.resolved_at = datetime.now(timezone.utc)
                    self.active_alerts.pop(alert_id, None)

                    logger.info(
                        f"✅ Auto-resolved alert: {alert_id} for {alert.component_id}"
                    )

        except Exception as e:
            logger.error(f"Error processing alerts: {e}")

    async def _cleanup_alerts(self):
        """Clean up old alerts from history."""
        try:
            # Keep only last 1000 alerts in history
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-1000:]

        except Exception as e:
            logger.error(f"Error cleaning up alerts: {e}")
