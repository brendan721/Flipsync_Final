"""Health monitoring for the FlipSync agent system."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Mapping, Optional, Set
from uuid import uuid4

from sklearn.linear_model import LinearRegression

from fs_agt_clean.core.campaign_analytics.analytics_engine import AnalyticsEngine
from fs_agt_clean.core.monitoring.alerts.models import AlertSeverity
from fs_agt_clean.core.monitoring.metrics_collector import MetricsCollector
from fs_agt_clean.core.monitoring.types import (
    UnifiedAgentHealth,
    HealthAlert,
    HealthSnapshot,
    HealthStatus,
    MaintenanceWindow,
    MetricCategory,
    MetricType,
    OptimizationRecommendation,
    RecoveryAction,
    ResourceMetrics,
    ResourceType,
    SystemMetrics,
)
from fs_agt_clean.core.optimization.budget import BudgetOptimizer
from fs_agt_clean.core.services.communication import Event, EventBus, EventType

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Health monitoring system."""

    def __init__(
        self,
        event_bus: EventBus,
        metrics_collector: MetricsCollector,
        budget_optimizer: BudgetOptimizer,
        analytics_engine: AnalyticsEngine,
        check_interval: int = 60,
        prediction_window: int = 3600,
    ):
        """Initialize health monitor.

        Args:
            event_bus: Event bus for communication
            metrics_collector: Metrics collector instance
            budget_optimizer: Budget optimizer instance
            analytics_engine: Analytics engine instance
            check_interval: Health check interval in seconds
            prediction_window: Performance prediction window in seconds
        """
        self.event_bus = event_bus
        self.metrics_collector = metrics_collector
        self.budget_optimizer = budget_optimizer
        self.analytics_engine = analytics_engine
        self.check_interval = check_interval
        self.prediction_window = prediction_window
        self.agent_health: Dict[str, UnifiedAgentHealth] = {}
        self.active_alerts: Dict[str, HealthAlert] = {}
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        self.maintenance_windows: Dict[str, MaintenanceWindow] = {}
        self.metric_history: Dict[MetricType, List[float]] = {
            metric_type: [] for metric_type in MetricType
        }
        self.predictors: Dict[MetricType, LinearRegression] = {}

    async def _initialize(self) -> None:
        """Initialize the health monitor."""
        await self._setup_subscriptions()
        asyncio.create_task(self._monitoring_loop())

    async def _setup_subscriptions(self) -> None:
        """Set up event subscriptions."""
        self.event_bus.subscribe(EventType.AGENT_STATUS, self._handle_agent_status)
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, self._handle_error)

    async def check_health(self, agent_id: str) -> UnifiedAgentHealth:
        """Check health of a specific agent."""
        try:
            metrics = await self._collect_resource_metrics(agent_id)
            status = self._calculate_health_status(metrics)
            system_metrics = await self._collect_system_metrics()
            try:
                uptime = await self._get_uptime(agent_id)
            except Exception as e:
                logger.error("Error getting uptime for %s: %s", agent_id, str(e))
                await self._publish_error(str(e))
                uptime = 0.0

            health = UnifiedAgentHealth(
                agent_id=agent_id,
                status=status,
                uptime=uptime,
                resource_metrics=metrics,
                system_metrics=system_metrics,
                error_count=await self._get_error_count(agent_id),
                last_error=await self._get_last_error(agent_id),
                last_success=await self._get_last_success(agent_id),
                timestamp=datetime.now(timezone.utc),
            )
            self.agent_health[agent_id] = health
            await self._check_alerts(health)
            return health
        except Exception as e:
            logger.error("Error checking health for %s: %s", agent_id, str(e))
            await self._publish_error(str(e))
            raise

    async def get_system_health(self) -> HealthSnapshot:
        """Get system-wide health snapshot."""
        try:
            status = self._calculate_overall_status()
            snapshot = HealthSnapshot(
                status=status,
                overall_status=status,  # Use same status for both fields
                agent_health=self.agent_health.copy(),
                system_metrics=await self._collect_system_metrics(),
                active_alerts=list(self.active_alerts.values()),
                timestamp=datetime.now(timezone.utc),
            )
            await self._publish_health_snapshot(snapshot)
            return snapshot
        except Exception as e:
            logger.error("Error getting system health: %s", e)
            await self._publish_error(str(e))
            raise

    async def get_recommendations(self) -> List[OptimizationRecommendation]:
        """Get optimization recommendations."""
        try:
            snapshot = await self.get_system_health()
            recommendations = []
            for agent_id, health in snapshot.agent_health.items():
                if health.status != HealthStatus.HEALTHY:
                    recommendation = OptimizationRecommendation(
                        resource_type=ResourceType.CPU,  # Example resource type
                        current_usage=0.8,  # Example usage
                        recommended_limit=0.6,  # Example limit
                        potential_savings=0.2,  # Example savings
                        priority="high",
                        justification=f"Optimize resource usage for agent {agent_id}",
                    )
                    recommendations.append(recommendation)
            return recommendations
        except Exception as e:
            logger.error("Error getting recommendations: %s", str(e))
            await self._publish_error(str(e))
            raise

    async def schedule_maintenance(
        self,
        start_time: datetime,
        end_time: datetime,
        components: Set[str],
        maintenance_type: str,
        priority: str,
    ) -> MaintenanceWindow:
        """Schedule a maintenance window."""
        window = MaintenanceWindow(
            id=str(uuid4()),
            start_time=start_time,
            end_time=end_time,
            components=components,
            maintenance_type=maintenance_type,
            priority=priority,
            status="scheduled",
        )
        self.maintenance_windows[window.id] = window
        return window

    async def get_recovery_action(self, health: UnifiedAgentHealth) -> RecoveryAction:
        """Get recovery action for an unhealthy agent."""
        action = RecoveryAction(
            component=health.agent_id,
            action="restart",
            priority="high",
            estimated_duration=300,  # 5 minutes
            impact="medium",
            prerequisites=[],
        )
        self.recovery_actions[action.component] = action
        return action

    async def create_alert(
        self, health: UnifiedAgentHealth, severity: AlertSeverity, message: str
    ) -> HealthAlert:
        """Create health alert."""
        alert = HealthAlert(
            id=str(uuid4()),
            severity=severity,
            message=message,
            component=health.agent_id,
            status="active",
            created_at=datetime.now(timezone.utc),
        )
        self.active_alerts[alert.id] = alert
        return alert

    async def predict_performance(
        self: MetricCategory, hours: int = 1
    ) -> List[float]:
        """Predict performance metrics."""
        predictions = []
        current_time = datetime.now(timezone.utc)
        for i in range(hours):
            prediction = 0.5  # TODO: Implement actual prediction logic
            predictions.append(prediction)
        return predictions

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while True:
            try:
                for agent_id in self.agent_health:
                    await self.check_health(agent_id)
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error("Error in monitoring loop: %s", str(e))
                await self._publish_error(str(e))
                await asyncio.sleep(self.check_interval)

    async def _publish_error(self, error_message: str) -> None:
        """Publish an error event."""
        event = Event(
            id=f"error_{datetime.now(timezone.utc).timestamp()}",
            type=EventType.ERROR_OCCURRED,
            source="health_monitor",
            data={"message": error_message},
            timestamp=datetime.now(timezone.utc),
            metadata=None,
        )
        await self.event_bus.publish(event)

    async def _publish_health_snapshot(self, snapshot: HealthSnapshot) -> None:
        """Publish a health snapshot event."""
        event = Event(
            id=f"health_{datetime.now(timezone.utc).timestamp()}",
            type=EventType.SYSTEM_STATUS,
            source="health_monitor",
            data={"snapshot": snapshot},
            timestamp=datetime.now(timezone.utc),
            metadata=None,
        )
        await self.event_bus.publish(event)

    async def _handle_agent_status(self, event: Event) -> None:
        """Handle agent status events."""
        agent_id = event.data.get("agent_id")
        if agent_id:
            await self.check_health(agent_id)

    async def _handle_error(self, event: Event) -> None:
        """Handle error events."""
        agent_id = event.data.get("agent_id")
        if agent_id and agent_id in self.agent_health:
            health = self.agent_health[agent_id]
            await self.create_alert(
                health, AlertSeverity.HIGH, event.data.get("message", "Unknown error")
            )

    async def _collect_resource_metrics(
        self, agent_id: str
    ) -> Mapping[ResourceType, ResourceMetrics]:
        """Collect resource metrics for an agent."""
        try:
            raw_metrics = await self.metrics_collector.get_resource_metrics(agent_id)
            metrics: Dict[ResourceType, ResourceMetrics] = {}
            for resource_type in ResourceType:
                metrics[resource_type] = ResourceMetrics(
                    resource_type=resource_type,
                    value=0.0,
                    timestamp=datetime.now(timezone.utc),
                )
                if resource_type in raw_metrics:
                    raw_metric = raw_metrics[resource_type]
                    if isinstance(raw_metric, ResourceMetrics):
                        metrics[resource_type] = raw_metric
            return metrics
        except Exception as e:
            logger.error("Error collecting resource metrics for %s: %s", agent_id, e)
            # Only publish error once, let the caller handle re-raising
            return {
                resource_type: ResourceMetrics(
                    resource_type=resource_type,
                    value=0.0,
                    timestamp=datetime.now(timezone.utc),
                )
                for resource_type in ResourceType
            }

    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide metrics."""
        try:
            return SystemMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_in=0.0,
                network_out=0.0,
                total_requests=0,
                success_rate=0.0,
                avg_latency=0.0,
                peak_latency=0.0,
                total_errors=0,
                resource_usage={},
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error("Error collecting system metrics: %s", e)
            raise

    def _calculate_health_status(
        self, metrics: Mapping[ResourceType, ResourceMetrics]
    ) -> HealthStatus:
        """Calculate health status from metrics."""
        # TODO: Implement actual health status calculation
        return HealthStatus.HEALTHY

    def _calculate_overall_status(self) -> HealthStatus:
        """Calculate overall system health status."""
        if not self.agent_health:
            return HealthStatus.HEALTHY  # Default to healthy when no agents

        # If any agent is unhealthy, the system is unhealthy
        for health in self.agent_health.values():
            if health.status == HealthStatus.UNHEALTHY:
                return HealthStatus.UNHEALTHY
            elif health.status == HealthStatus.DEGRADED:
                return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    async def _get_uptime(self, agent_id: str) -> float:
        """Get agent uptime."""
        try:
            return await self.metrics_collector.get_uptime(agent_id)
        except Exception as e:
            logger.error("Error getting uptime for %s: %s", agent_id, str(e))
            await self._publish_error(str(e))
            return 0.0

    async def _get_error_count(self, agent_id: str) -> int:
        """Get agent error count."""
        # TODO: Implement actual error count calculation
        return 0

    async def _get_last_error(self, agent_id: str) -> Optional[datetime]:
        """Get agent's last error time."""
        # TODO: Implement actual last error time calculation
        return None

    async def _get_last_success(self, agent_id: str) -> Optional[datetime]:
        """Get agent's last success time."""
        # TODO: Implement actual last success time calculation
        return datetime.now(timezone.utc)

    async def _check_alerts(self, health: UnifiedAgentHealth) -> None:
        """Check and create alerts based on health status."""
        if health.status != HealthStatus.HEALTHY:
            await self.create_alert(
                health,
                AlertSeverity.HIGH,
                f"UnifiedAgent {health.agent_id} is in {health.status.value} state",
            )

    async def update_health_status(self, agent_id: str, status: HealthStatus) -> None:
        """Update health status for an agent."""
        health = UnifiedAgentHealth(
            agent_id=agent_id,
            status=status,
            uptime=await self._get_uptime(agent_id),
            resource_metrics=await self._collect_resource_metrics(agent_id),
            system_metrics=await self._collect_system_metrics(),
            error_count=await self._get_error_count(agent_id),
            last_error=await self._get_last_error(agent_id),
            last_success=await self._get_last_success(agent_id),
            timestamp=datetime.now(timezone.utc),
        )
        self.agent_health[agent_id] = health
        await self._check_alerts(health)

    async def get_health_snapshot(self) -> HealthSnapshot:
        """Get system-wide health snapshot (alias for get_system_health)."""
        return await self.get_system_health()

    async def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        return await self._collect_system_metrics()
