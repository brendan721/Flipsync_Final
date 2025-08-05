"""
FlipSync Operational Monitoring & Alerting System
Week 4: Production Deployment & Operational Excellence - Objective 3

Real-time monitoring system for 4 autonomous agents and 24 service components
with <10ms monitoring overhead and sub-100ms consensus alerting.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringStatus(Enum):
    """Monitoring status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """Health metric data structure."""

    component_id: str
    component_type: str  # "agent" or "service"
    metric_name: str
    value: float
    threshold: float
    status: MonitoringStatus
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert data structure."""

    alert_id: str
    component_id: str
    component_type: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MonitoringTarget(BaseModel):
    """Monitoring target configuration."""

    component_id: str
    component_type: str
    health_check_interval_ms: int = 1000
    performance_thresholds: Dict[str, float]
    alert_thresholds: Dict[str, float]
    recovery_procedures: List[str] = []


class OperationalMonitoringSystem:
    """
    Advanced operational monitoring and alerting system.

    Features:
    - Real-time monitoring of 4 autonomous agents
    - Real-time monitoring of 24 service components
    - <10ms monitoring overhead target
    - Sub-100ms consensus alerting
    - Automated health checks and recovery
    - Integration with WebSocket infrastructure
    - Operational dashboards
    """

    def __init__(self):
        # Performance targets
        self.monitoring_overhead_target_ms = 10
        self.alerting_response_target_ms = 100
        self.health_check_interval_ms = 1000

        # Monitoring state
        self.is_monitoring_active = False
        self.monitoring_start_time: Optional[datetime] = None

        # Component tracking
        self.monitored_agents: Dict[str, MonitoringTarget] = {}
        self.monitored_services: Dict[str, MonitoringTarget] = {}

        # Health metrics storage
        self.health_metrics: deque = deque(maxlen=10000)
        self.current_health_status: Dict[str, MonitoringStatus] = {}

        # Alert management
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_callbacks: List[Callable] = []

        # Performance monitoring
        self.monitoring_performance: Dict[str, List[float]] = defaultdict(list)
        self.consensus_times: deque = deque(maxlen=100)

        # Recovery procedures
        self.recovery_procedures: Dict[str, Callable] = {}

        # WebSocket integration
        self.websocket_manager = None

        # Monitoring configuration
        self.monitoring_config = {
            "enable_real_time_monitoring": True,
            "enable_automated_recovery": True,
            "enable_consensus_alerting": True,
            "enable_performance_tracking": True,
            "health_check_timeout_ms": 5000,
            "alert_cooldown_seconds": 30,
            "max_concurrent_checks": 50,
        }

        # Agent monitoring targets
        self.agent_monitoring_targets = {
            "market_agent": MonitoringTarget(
                component_id="market_agent",
                component_type="agent",
                health_check_interval_ms=1000,
                performance_thresholds={
                    "decision_time_ms": 500,
                    "success_rate": 0.99,
                    "memory_usage_mb": 512,
                    "cpu_usage_percent": 80,
                },
                alert_thresholds={
                    "decision_time_ms": 750,
                    "success_rate": 0.95,
                    "memory_usage_mb": 768,
                    "cpu_usage_percent": 90,
                },
                recovery_procedures=["restart_agent", "clear_cache", "reduce_load"],
            ),
            "content_agent": MonitoringTarget(
                component_id="content_agent",
                component_type="agent",
                health_check_interval_ms=1000,
                performance_thresholds={
                    "decision_time_ms": 500,
                    "success_rate": 0.99,
                    "memory_usage_mb": 512,
                    "cpu_usage_percent": 80,
                },
                alert_thresholds={
                    "decision_time_ms": 750,
                    "success_rate": 0.95,
                    "memory_usage_mb": 768,
                    "cpu_usage_percent": 90,
                },
                recovery_procedures=["restart_agent", "clear_cache", "reduce_load"],
            ),
            "logistics_agent": MonitoringTarget(
                component_id="logistics_agent",
                component_type="agent",
                health_check_interval_ms=1000,
                performance_thresholds={
                    "decision_time_ms": 500,
                    "success_rate": 0.99,
                    "memory_usage_mb": 512,
                    "cpu_usage_percent": 80,
                },
                alert_thresholds={
                    "decision_time_ms": 750,
                    "success_rate": 0.95,
                    "memory_usage_mb": 768,
                    "cpu_usage_percent": 90,
                },
                recovery_procedures=["restart_agent", "clear_cache", "reduce_load"],
            ),
            "executive_agent": MonitoringTarget(
                component_id="executive_agent",
                component_type="agent",
                health_check_interval_ms=1000,
                performance_thresholds={
                    "decision_time_ms": 500,
                    "success_rate": 0.99,
                    "memory_usage_mb": 512,
                    "cpu_usage_percent": 80,
                },
                alert_thresholds={
                    "decision_time_ms": 750,
                    "success_rate": 0.95,
                    "memory_usage_mb": 768,
                    "cpu_usage_percent": 90,
                },
                recovery_procedures=["restart_agent", "clear_cache", "reduce_load"],
            ),
        }

        # Service monitoring targets (24 services)
        self.service_monitoring_targets = {
            # Infrastructure services
            "database_service": self._create_service_target(
                "database_service", {"response_time_ms": 100}
            ),
            "redis_service": self._create_service_target(
                "redis_service", {"response_time_ms": 50}
            ),
            "qdrant_service": self._create_service_target(
                "qdrant_service", {"response_time_ms": 200}
            ),
            "websocket_service": self._create_service_target(
                "websocket_service", {"response_time_ms": 100}
            ),
            "monitoring_service": self._create_service_target(
                "monitoring_service", {"response_time_ms": 10}
            ),
            # Market agent services
            "pricing_service": self._create_service_target(
                "pricing_service", {"execution_time_ms": 250}
            ),
            "competitor_analysis": self._create_service_target(
                "competitor_analysis", {"execution_time_ms": 300}
            ),
            "market_research": self._create_service_target(
                "market_research", {"execution_time_ms": 400}
            ),
            "demand_forecasting": self._create_service_target(
                "demand_forecasting", {"execution_time_ms": 350}
            ),
            # Content agent services
            "content_generation": self._create_service_target(
                "content_generation", {"execution_time_ms": 250}
            ),
            "seo_optimization": self._create_service_target(
                "seo_optimization", {"execution_time_ms": 200}
            ),
            "image_processing": self._create_service_target(
                "image_processing", {"execution_time_ms": 500}
            ),
            "template_management": self._create_service_target(
                "template_management", {"execution_time_ms": 150}
            ),
            "quality_assurance": self._create_service_target(
                "quality_assurance", {"execution_time_ms": 300}
            ),
            # Logistics agent services
            "route_optimization": self._create_service_target(
                "route_optimization", {"execution_time_ms": 250}
            ),
            "inventory_management": self._create_service_target(
                "inventory_management", {"execution_time_ms": 200}
            ),
            "shipping_calculation": self._create_service_target(
                "shipping_calculation", {"execution_time_ms": 150}
            ),
            "warehouse_coordination": self._create_service_target(
                "warehouse_coordination", {"execution_time_ms": 300}
            ),
            "delivery_tracking": self._create_service_target(
                "delivery_tracking", {"execution_time_ms": 200}
            ),
            # Executive agent services
            "strategic_planning": self._create_service_target(
                "strategic_planning", {"execution_time_ms": 250}
            ),
            "performance_analytics": self._create_service_target(
                "performance_analytics", {"execution_time_ms": 300}
            ),
            "resource_allocation": self._create_service_target(
                "resource_allocation", {"execution_time_ms": 200}
            ),
            "decision_coordination": self._create_service_target(
                "decision_coordination", {"execution_time_ms": 150}
            ),
            "reporting_service": self._create_service_target(
                "reporting_service", {"execution_time_ms": 250}
            ),
        }

    def _create_service_target(
        self, service_id: str, thresholds: Dict[str, float]
    ) -> MonitoringTarget:
        """Create a monitoring target for a service."""
        alert_thresholds = {
            k: v * 1.5 for k, v in thresholds.items()
        }  # 50% higher for alerts

        return MonitoringTarget(
            component_id=service_id,
            component_type="service",
            health_check_interval_ms=2000,  # Services checked every 2 seconds
            performance_thresholds=thresholds,
            alert_thresholds=alert_thresholds,
            recovery_procedures=["restart_service", "clear_cache", "scale_up"],
        )

    async def initialize(self) -> bool:
        """Initialize the operational monitoring system."""
        try:
            logger.info("🚀 Initializing Operational Monitoring & Alerting System")

            # Initialize monitoring targets
            await self._initialize_monitoring_targets()

            # Initialize WebSocket integration
            await self._initialize_websocket_integration()

            # Initialize recovery procedures
            await self._initialize_recovery_procedures()

            # Start monitoring loops
            await self._start_monitoring_loops()

            self.is_monitoring_active = True
            self.monitoring_start_time = datetime.now(timezone.utc)

            logger.info("✅ Operational monitoring system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize monitoring system: {e}")
            return False

    async def _initialize_monitoring_targets(self) -> None:
        """Initialize monitoring targets for agents and services."""
        logger.info("🎯 Initializing monitoring targets...")

        # Register agent monitoring targets
        for agent_id, target in self.agent_monitoring_targets.items():
            self.monitored_agents[agent_id] = target
            self.current_health_status[agent_id] = MonitoringStatus.HEALTHY

        # Register service monitoring targets
        for service_id, target in self.service_monitoring_targets.items():
            self.monitored_services[service_id] = target
            self.current_health_status[service_id] = MonitoringStatus.HEALTHY

        logger.info(
            f"✅ Monitoring targets initialized: {len(self.monitored_agents)} agents, {len(self.monitored_services)} services"
        )

    async def _initialize_websocket_integration(self) -> None:
        """Initialize WebSocket integration for real-time monitoring."""
        logger.info("🔌 Initializing WebSocket integration...")

        try:
            from fs_agt_clean.core.websocket.manager import websocket_manager

            self.websocket_manager = websocket_manager
            logger.info("✅ WebSocket integration initialized")
        except Exception as e:
            logger.warning(f"⚠️ WebSocket integration not available: {e}")

    async def _initialize_recovery_procedures(self) -> None:
        """Initialize automated recovery procedures."""
        logger.info("🔧 Initializing recovery procedures...")

        self.recovery_procedures = {
            "restart_agent": self._restart_agent_procedure,
            "restart_service": self._restart_service_procedure,
            "clear_cache": self._clear_cache_procedure,
            "reduce_load": self._reduce_load_procedure,
            "scale_up": self._scale_up_procedure,
        }

        logger.info(
            f"✅ Recovery procedures initialized: {len(self.recovery_procedures)} procedures"
        )

    async def _start_monitoring_loops(self) -> None:
        """Start the monitoring loops."""
        logger.info("🔄 Starting monitoring loops...")

        # Start agent monitoring loop
        asyncio.create_task(self._agent_monitoring_loop())

        # Start service monitoring loop
        asyncio.create_task(self._service_monitoring_loop())

        # Start alert processing loop
        asyncio.create_task(self._alert_processing_loop())

        logger.info("✅ Monitoring loops started")

    async def _agent_monitoring_loop(self) -> None:
        """Main monitoring loop for agents."""
        while self.is_monitoring_active:
            try:
                start_time = time.perf_counter()

                # Check all agents concurrently
                agent_tasks = []
                for agent_id, target in self.monitored_agents.items():
                    task = asyncio.create_task(
                        self._check_agent_health(agent_id, target)
                    )
                    agent_tasks.append(task)

                # Wait for all health checks with timeout
                if agent_tasks:
                    await asyncio.wait_for(
                        asyncio.gather(*agent_tasks, return_exceptions=True),
                        timeout=self.monitoring_config["health_check_timeout_ms"]
                        / 1000,
                    )

                # Record monitoring performance
                monitoring_time = (time.perf_counter() - start_time) * 1000
                self.monitoring_performance["agent_monitoring"].append(monitoring_time)

                # Keep only recent performance data
                if len(self.monitoring_performance["agent_monitoring"]) > 100:
                    self.monitoring_performance["agent_monitoring"] = (
                        self.monitoring_performance["agent_monitoring"][-100:]
                    )

                # Check if monitoring overhead target is met
                if monitoring_time <= self.monitoring_overhead_target_ms:
                    logger.debug(
                        f"✅ Agent monitoring: {monitoring_time:.2f}ms (target: {self.monitoring_overhead_target_ms}ms)"
                    )
                else:
                    logger.warning(
                        f"⚠️ Agent monitoring overhead: {monitoring_time:.2f}ms (target: {self.monitoring_overhead_target_ms}ms)"
                    )

                # Wait for next monitoring cycle
                await asyncio.sleep(self.health_check_interval_ms / 1000)

            except Exception as e:
                logger.error(f"❌ Agent monitoring loop error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

    async def _service_monitoring_loop(self) -> None:
        """Main monitoring loop for services."""
        while self.is_monitoring_active:
            try:
                start_time = time.perf_counter()

                # Check services in batches to avoid overwhelming the system
                service_items = list(self.monitored_services.items())
                batch_size = self.monitoring_config["max_concurrent_checks"]

                for i in range(0, len(service_items), batch_size):
                    batch = service_items[i : i + batch_size]

                    service_tasks = []
                    for service_id, target in batch:
                        task = asyncio.create_task(
                            self._check_service_health(service_id, target)
                        )
                        service_tasks.append(task)

                    # Wait for batch completion
                    if service_tasks:
                        await asyncio.wait_for(
                            asyncio.gather(*service_tasks, return_exceptions=True),
                            timeout=self.monitoring_config["health_check_timeout_ms"]
                            / 1000,
                        )

                # Record monitoring performance
                monitoring_time = (time.perf_counter() - start_time) * 1000
                self.monitoring_performance["service_monitoring"].append(
                    monitoring_time
                )

                # Keep only recent performance data
                if len(self.monitoring_performance["service_monitoring"]) > 100:
                    self.monitoring_performance["service_monitoring"] = (
                        self.monitoring_performance["service_monitoring"][-100:]
                    )

                # Check if monitoring overhead target is met
                if monitoring_time <= self.monitoring_overhead_target_ms:
                    logger.debug(
                        f"✅ Service monitoring: {monitoring_time:.2f}ms (target: {self.monitoring_overhead_target_ms}ms)"
                    )
                else:
                    logger.warning(
                        f"⚠️ Service monitoring overhead: {monitoring_time:.2f}ms (target: {self.monitoring_overhead_target_ms}ms)"
                    )

                # Wait for next monitoring cycle
                await asyncio.sleep(2)  # Services checked every 2 seconds

            except Exception as e:
                logger.error(f"❌ Service monitoring loop error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry

    async def _check_agent_health(
        self, agent_id: str, target: MonitoringTarget
    ) -> None:
        """Check health of a specific agent."""
        try:
            # Simulate agent health check (in real implementation, this would check actual agent status)
            health_metrics = await self._simulate_agent_health_check(agent_id)

            # Process health metrics
            for metric_name, value in health_metrics.items():
                threshold = target.performance_thresholds.get(metric_name, float("inf"))
                alert_threshold = target.alert_thresholds.get(metric_name, float("inf"))

                # Determine status
                if value <= threshold:
                    status = MonitoringStatus.HEALTHY
                elif value <= alert_threshold:
                    status = MonitoringStatus.DEGRADED
                else:
                    status = MonitoringStatus.UNHEALTHY

                # Create health metric
                metric = HealthMetric(
                    component_id=agent_id,
                    component_type="agent",
                    metric_name=metric_name,
                    value=value,
                    threshold=threshold,
                    status=status,
                    timestamp=datetime.now(timezone.utc),
                )

                self.health_metrics.append(metric)

                # Update current status
                if status != MonitoringStatus.HEALTHY:
                    self.current_health_status[agent_id] = status

                    # Generate alert if needed
                    if status in [
                        MonitoringStatus.UNHEALTHY,
                        MonitoringStatus.CRITICAL,
                    ]:
                        await self._generate_alert(
                            agent_id,
                            "agent",
                            (
                                AlertSeverity.ERROR
                                if status == MonitoringStatus.UNHEALTHY
                                else AlertSeverity.CRITICAL
                            ),
                            f"Agent {agent_id} {metric_name}: {value} exceeds threshold {alert_threshold}",
                        )

        except Exception as e:
            logger.error(f"❌ Agent health check failed for {agent_id}: {e}")

    async def _check_service_health(
        self, service_id: str, target: MonitoringTarget
    ) -> None:
        """Check health of a specific service."""
        try:
            # Simulate service health check (in real implementation, this would check actual service status)
            health_metrics = await self._simulate_service_health_check(service_id)

            # Process health metrics
            for metric_name, value in health_metrics.items():
                threshold = target.performance_thresholds.get(metric_name, float("inf"))
                alert_threshold = target.alert_thresholds.get(metric_name, float("inf"))

                # Determine status
                if value <= threshold:
                    status = MonitoringStatus.HEALTHY
                elif value <= alert_threshold:
                    status = MonitoringStatus.DEGRADED
                else:
                    status = MonitoringStatus.UNHEALTHY

                # Create health metric
                metric = HealthMetric(
                    component_id=service_id,
                    component_type="service",
                    metric_name=metric_name,
                    value=value,
                    threshold=threshold,
                    status=status,
                    timestamp=datetime.now(timezone.utc),
                )

                self.health_metrics.append(metric)

                # Update current status
                if status != MonitoringStatus.HEALTHY:
                    self.current_health_status[service_id] = status

                    # Generate alert if needed
                    if status in [
                        MonitoringStatus.UNHEALTHY,
                        MonitoringStatus.CRITICAL,
                    ]:
                        await self._generate_alert(
                            service_id,
                            "service",
                            (
                                AlertSeverity.WARNING
                                if status == MonitoringStatus.UNHEALTHY
                                else AlertSeverity.ERROR
                            ),
                            f"Service {service_id} {metric_name}: {value} exceeds threshold {alert_threshold}",
                        )

        except Exception as e:
            logger.error(f"❌ Service health check failed for {service_id}: {e}")

    async def _simulate_agent_health_check(self, agent_id: str) -> Dict[str, float]:
        """Simulate agent health check (replace with real implementation)."""
        import random

        # Simulate realistic agent metrics
        base_decision_time = 450 + random.uniform(
            -50, 100
        )  # Around 450ms with variance
        base_success_rate = 0.995 + random.uniform(-0.005, 0.005)  # Around 99.5%
        base_memory = 400 + random.uniform(-50, 100)  # Around 400MB
        base_cpu = 60 + random.uniform(-20, 30)  # Around 60%

        return {
            "decision_time_ms": base_decision_time,
            "success_rate": base_success_rate,
            "memory_usage_mb": base_memory,
            "cpu_usage_percent": base_cpu,
        }

    async def _simulate_service_health_check(self, service_id: str) -> Dict[str, float]:
        """Simulate service health check (replace with real implementation)."""
        import random

        # Get base execution time from service targets
        target = self.service_monitoring_targets.get(service_id)
        if target and "execution_time_ms" in target.performance_thresholds:
            base_time = target.performance_thresholds["execution_time_ms"]
        else:
            base_time = 200  # Default

        # Add some realistic variance
        execution_time = base_time * (0.8 + random.uniform(0, 0.4))  # 80-120% of target

        return {
            "execution_time_ms": execution_time,
            "success_rate": 0.99 + random.uniform(-0.01, 0.01),
            "memory_usage_mb": 100 + random.uniform(-20, 40),
        }

    async def _generate_alert(
        self,
        component_id: str,
        component_type: str,
        severity: AlertSeverity,
        message: str,
    ) -> None:
        """Generate and process an alert."""
        alert_id = f"{component_id}_{int(time.time())}"

        alert = Alert(
            alert_id=alert_id,
            component_id=component_id,
            component_type=component_type,
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc),
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Process alert with consensus timing
        start_time = time.perf_counter()
        await self._process_alert(alert)
        consensus_time = (time.perf_counter() - start_time) * 1000

        self.consensus_times.append(consensus_time)

        # Check consensus alerting target
        if consensus_time <= self.alerting_response_target_ms:
            logger.debug(
                f"✅ Alert processed: {consensus_time:.2f}ms (target: {self.alerting_response_target_ms}ms)"
            )
        else:
            logger.warning(
                f"⚠️ Alert processing slow: {consensus_time:.2f}ms (target: {self.alerting_response_target_ms}ms)"
            )

    async def _process_alert(self, alert: Alert) -> None:
        """Process an alert with automated response."""
        logger.warning(
            f"🚨 ALERT [{alert.severity.value.upper()}] {alert.component_type} {alert.component_id}: {alert.message}"
        )

        # Send alert via WebSocket if available
        if self.websocket_manager:
            try:
                alert_data = {
                    "type": "monitoring_alert",
                    "alert": {
                        "id": alert.alert_id,
                        "component_id": alert.component_id,
                        "component_type": alert.component_type,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                    },
                }
                await self.websocket_manager.broadcast_message(json.dumps(alert_data))
            except Exception as e:
                logger.error(f"❌ Failed to send alert via WebSocket: {e}")

        # Trigger automated recovery if enabled
        if self.monitoring_config["enable_automated_recovery"]:
            await self._trigger_automated_recovery(alert)

    async def _trigger_automated_recovery(self, alert: Alert) -> None:
        """Trigger automated recovery procedures."""
        try:
            # Get recovery procedures for the component
            if alert.component_type == "agent":
                target = self.monitored_agents.get(alert.component_id)
            else:
                target = self.monitored_services.get(alert.component_id)

            if target and target.recovery_procedures:
                for procedure_name in target.recovery_procedures:
                    if procedure_name in self.recovery_procedures:
                        logger.info(
                            f"🔧 Executing recovery procedure: {procedure_name} for {alert.component_id}"
                        )
                        await self.recovery_procedures[procedure_name](
                            alert.component_id, alert.component_type
                        )
                        break  # Execute only the first applicable procedure

        except Exception as e:
            logger.error(f"❌ Automated recovery failed for {alert.component_id}: {e}")

    async def _restart_agent_procedure(
        self, component_id: str, component_type: str
    ) -> None:
        """Restart agent recovery procedure."""
        logger.info(f"🔄 Simulating agent restart for {component_id}")
        # In real implementation, this would restart the actual agent
        await asyncio.sleep(0.1)  # Simulate restart time

    async def _restart_service_procedure(
        self, component_id: str, component_type: str
    ) -> None:
        """Restart service recovery procedure."""
        logger.info(f"🔄 Simulating service restart for {component_id}")
        # In real implementation, this would restart the actual service
        await asyncio.sleep(0.1)  # Simulate restart time

    async def _clear_cache_procedure(
        self, component_id: str, component_type: str
    ) -> None:
        """Clear cache recovery procedure."""
        logger.info(f"🗑️ Simulating cache clear for {component_id}")
        # In real implementation, this would clear relevant caches
        await asyncio.sleep(0.05)  # Simulate cache clear time

    async def _reduce_load_procedure(
        self, component_id: str, component_type: str
    ) -> None:
        """Reduce load recovery procedure."""
        logger.info(f"📉 Simulating load reduction for {component_id}")
        # In real implementation, this would reduce load on the component
        await asyncio.sleep(0.05)  # Simulate load reduction time

    async def _scale_up_procedure(self, component_id: str, component_type: str) -> None:
        """Scale up recovery procedure."""
        logger.info(f"📈 Simulating scale up for {component_id}")
        # In real implementation, this would scale up the service
        await asyncio.sleep(0.1)  # Simulate scale up time

    async def _alert_processing_loop(self) -> None:
        """Process and manage alerts."""
        while self.is_monitoring_active:
            try:
                # Clean up resolved alerts
                current_time = datetime.now(timezone.utc)
                resolved_alerts = []

                for alert_id, alert in self.active_alerts.items():
                    # Auto-resolve alerts after cooldown period
                    if (
                        current_time - alert.timestamp
                    ).total_seconds() > self.monitoring_config[
                        "alert_cooldown_seconds"
                    ]:
                        alert.resolved = True
                        alert.resolved_at = current_time
                        resolved_alerts.append(alert_id)

                # Remove resolved alerts from active list
                for alert_id in resolved_alerts:
                    del self.active_alerts[alert_id]

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"❌ Alert processing loop error: {e}")
                await asyncio.sleep(1)

    def get_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        current_time = datetime.now(timezone.utc)

        # Calculate monitoring performance
        agent_monitoring_avg = (
            sum(self.monitoring_performance["agent_monitoring"])
            / len(self.monitoring_performance["agent_monitoring"])
            if self.monitoring_performance["agent_monitoring"]
            else 0
        )

        service_monitoring_avg = (
            sum(self.monitoring_performance["service_monitoring"])
            / len(self.monitoring_performance["service_monitoring"])
            if self.monitoring_performance["service_monitoring"]
            else 0
        )

        consensus_avg = (
            sum(self.consensus_times) / len(self.consensus_times)
            if self.consensus_times
            else 0
        )

        # Count components by status
        status_counts = defaultdict(int)
        for status in self.current_health_status.values():
            status_counts[status.value] += 1

        # Calculate uptime
        uptime_seconds = (
            (current_time - self.monitoring_start_time).total_seconds()
            if self.monitoring_start_time
            else 0
        )

        return {
            "monitoring_summary": {
                "is_active": self.is_monitoring_active,
                "uptime_seconds": uptime_seconds,
                "monitored_agents": len(self.monitored_agents),
                "monitored_services": len(self.monitored_services),
                "total_components": len(self.monitored_agents)
                + len(self.monitored_services),
            },
            "performance_metrics": {
                "agent_monitoring_avg_ms": agent_monitoring_avg,
                "service_monitoring_avg_ms": service_monitoring_avg,
                "consensus_alerting_avg_ms": consensus_avg,
                "monitoring_overhead_target_ms": self.monitoring_overhead_target_ms,
                "alerting_response_target_ms": self.alerting_response_target_ms,
                "targets_met": {
                    "monitoring_overhead": agent_monitoring_avg
                    <= self.monitoring_overhead_target_ms
                    and service_monitoring_avg <= self.monitoring_overhead_target_ms,
                    "alerting_response": consensus_avg
                    <= self.alerting_response_target_ms,
                },
            },
            "health_status": {
                "status_distribution": dict(status_counts),
                "healthy_components": status_counts["healthy"],
                "degraded_components": status_counts["degraded"],
                "unhealthy_components": status_counts["unhealthy"],
                "critical_components": status_counts["critical"],
            },
            "alert_statistics": {
                "active_alerts": len(self.active_alerts),
                "total_alerts_generated": len(self.alert_history),
                "alert_rate_per_hour": len(self.alert_history)
                / max(uptime_seconds / 3600, 1),
            },
            "monitoring_configuration": self.monitoring_config,
            "timestamp": current_time.isoformat(),
        }

    async def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        logger.info("🛑 Stopping operational monitoring system...")
        self.is_monitoring_active = False
        logger.info("✅ Monitoring system stopped")


# Global monitoring system instance
_monitoring_system: Optional[OperationalMonitoringSystem] = None


def get_operational_monitoring_system() -> OperationalMonitoringSystem:
    """Get the global operational monitoring system instance."""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = OperationalMonitoringSystem()
    return _monitoring_system
