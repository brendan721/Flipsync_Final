"""
Production Monitoring Service for FlipSync.

This service provides comprehensive monitoring and alerting for production deployment:
- System health monitoring
- Performance metrics tracking
- Error rate monitoring and alerting
- Resource utilization tracking
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """System health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SystemMetrics:
    """System performance metrics."""

    def __init__(self):
        self.cpu_usage = 0.0
        self.memory_usage = 0.0
        self.disk_usage = 0.0
        self.network_io = {"bytes_sent": 0, "bytes_recv": 0}
        self.process_count = 0
        self.uptime_seconds = 0
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "cpu_usage_percent": self.cpu_usage,
            "memory_usage_percent": self.memory_usage,
            "disk_usage_percent": self.disk_usage,
            "network_io": self.network_io,
            "process_count": self.process_count,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat(),
        }


class ServiceHealthCheck:
    """Health check result for a service."""

    def __init__(
        self,
        service_name: str,
        status: HealthStatus,
        response_time_ms: float,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ):
        self.service_name = service_name
        self.status = status
        self.response_time_ms = response_time_ms
        self.details = details or {}
        self.error_message = error_message
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "service_name": self.service_name,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "details": self.details,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


class ProductionMonitoringService:
    """
    Production monitoring service for comprehensive system oversight.

    This service provides:
    - Real-time system health monitoring
    - Performance metrics collection and analysis
    - Error rate tracking and alerting
    - Service availability monitoring
    """

    def __init__(self):
        """Initialize the production monitoring service."""
        self.start_time = datetime.now(timezone.utc)
        self.metrics_history: List[SystemMetrics] = []
        self.health_checks: Dict[str, ServiceHealthCheck] = {}
        self.alerts: List[Dict[str, Any]] = []

        # Monitoring configuration
        self.config = {
            "cpu_warning_threshold": 70.0,
            "cpu_critical_threshold": 90.0,
            "memory_warning_threshold": 80.0,
            "memory_critical_threshold": 95.0,
            "disk_warning_threshold": 85.0,
            "disk_critical_threshold": 95.0,
            "response_time_warning_ms": 1000.0,
            "response_time_critical_ms": 5000.0,
            "metrics_retention_hours": 24,
            "health_check_interval_seconds": 60,
        }

        # Background monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._start_monitoring()

        logger.info("Production Monitoring Service initialized")

    def _start_monitoring(self):
        """Start background monitoring task."""
        try:
            self._monitoring_task = asyncio.create_task(self._monitor_system())
        except Exception as e:
            logger.error(f"Error starting monitoring task: {e}")

    async def _monitor_system(self):
        """Background system monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.config["health_check_interval_seconds"])

                # Collect system metrics
                await self._collect_system_metrics()

                # Perform health checks
                await self._perform_health_checks()

                # Clean up old data
                await self._cleanup_old_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    async def _collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            metrics = SystemMetrics()

            # CPU usage
            metrics.cpu_usage = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            metrics.memory_usage = memory.percent

            # Disk usage
            disk = psutil.disk_usage("/")
            metrics.disk_usage = (disk.used / disk.total) * 100

            # Network I/O
            network = psutil.net_io_counters()
            metrics.network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
            }

            # Process count
            metrics.process_count = len(psutil.pids())

            # Uptime
            metrics.uptime_seconds = (
                datetime.now(timezone.utc) - self.start_time
            ).total_seconds()

            # Store metrics
            self.metrics_history.append(metrics)

            # Check for alerts
            await self._check_metric_alerts(metrics)

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _perform_health_checks(self):
        """Perform health checks on all services."""
        try:
            # Check core services
            await self._check_vector_service_health()
            await self._check_subscription_service_health()
            await self._check_websocket_service_health()
            await self._check_workflow_service_health()

        except Exception as e:
            logger.error(f"Error performing health checks: {e}")

    async def _check_vector_service_health(self):
        """Check vector database service health."""
        try:
            start_time = time.time()

            from fs_agt_clean.services.vector.embedding_service import embedding_service

            # Test embedding generation
            test_embedding = await embedding_service.generate_embedding(
                "health check test"
            )
            response_time = (time.time() - start_time) * 1000

            if test_embedding:
                status = HealthStatus.HEALTHY
                details = {"embedding_dimension": len(test_embedding)}
                error_message = None
            else:
                status = HealthStatus.WARNING
                details = {}
                error_message = "Failed to generate test embedding"

            # Check response time
            if response_time > self.config["response_time_critical_ms"]:
                status = HealthStatus.CRITICAL
            elif response_time > self.config["response_time_warning_ms"]:
                status = (
                    HealthStatus.WARNING if status == HealthStatus.HEALTHY else status
                )

            self.health_checks["vector_service"] = ServiceHealthCheck(
                service_name="vector_service",
                status=status,
                response_time_ms=response_time,
                details=details,
                error_message=error_message,
            )

        except Exception as e:
            self.health_checks["vector_service"] = ServiceHealthCheck(
                service_name="vector_service",
                status=HealthStatus.CRITICAL,
                response_time_ms=0.0,
                error_message=str(e),
            )

    async def _check_subscription_service_health(self):
        """Check subscription service health."""
        try:
            start_time = time.time()

            from fs_agt_clean.services.subscription.enhanced_subscription_service import (
                enhanced_subscription_service,
            )

            # Test subscription plans retrieval
            plans = enhanced_subscription_service.get_subscription_plans()
            response_time = (time.time() - start_time) * 1000

            if plans and len(plans) > 0:
                status = HealthStatus.HEALTHY
                details = {"plans_count": len(plans)}
                error_message = None
            else:
                status = HealthStatus.WARNING
                details = {}
                error_message = "No subscription plans available"

            self.health_checks["subscription_service"] = ServiceHealthCheck(
                service_name="subscription_service",
                status=status,
                response_time_ms=response_time,
                details=details,
                error_message=error_message,
            )

        except Exception as e:
            self.health_checks["subscription_service"] = ServiceHealthCheck(
                service_name="subscription_service",
                status=HealthStatus.CRITICAL,
                response_time_ms=0.0,
                error_message=str(e),
            )

    async def _check_websocket_service_health(self):
        """Check WebSocket service health."""
        try:
            start_time = time.time()

            from fs_agt_clean.core.websocket.enhanced_websocket_manager import (
                enhanced_websocket_manager,
            )

            # Test WebSocket manager stats
            stats = enhanced_websocket_manager.get_connection_stats()
            response_time = (time.time() - start_time) * 1000

            status = HealthStatus.HEALTHY
            details = {
                "active_connections": stats.get("active_connections", 0),
                "total_connections": stats.get("total_connections", 0),
                "fastapi_available": stats.get("fastapi_available", False),
            }

            self.health_checks["websocket_service"] = ServiceHealthCheck(
                service_name="websocket_service",
                status=status,
                response_time_ms=response_time,
                details=details,
            )

        except Exception as e:
            self.health_checks["websocket_service"] = ServiceHealthCheck(
                service_name="websocket_service",
                status=HealthStatus.CRITICAL,
                response_time_ms=0.0,
                error_message=str(e),
            )

    async def _check_workflow_service_health(self):
        """Check approval workflow service health."""
        try:
            start_time = time.time()

            from fs_agt_clean.services.workflow.approval_workflow_service import (
                approval_workflow_service,
            )

            # Test workflow stats
            stats = approval_workflow_service.get_workflow_stats()
            response_time = (time.time() - start_time) * 1000

            status = HealthStatus.HEALTHY
            details = {
                "active_requests": stats.get("active_requests", 0),
                "completed_requests": stats.get("completed_requests", 0),
                "timeout_monitor_running": stats.get("timeout_monitor_running", False),
            }

            self.health_checks["workflow_service"] = ServiceHealthCheck(
                service_name="workflow_service",
                status=status,
                response_time_ms=response_time,
                details=details,
            )

        except Exception as e:
            self.health_checks["workflow_service"] = ServiceHealthCheck(
                service_name="workflow_service",
                status=HealthStatus.CRITICAL,
                response_time_ms=0.0,
                error_message=str(e),
            )

    async def _check_metric_alerts(self, metrics: SystemMetrics):
        """Check metrics for alert conditions."""
        try:
            # CPU alerts
            if metrics.cpu_usage >= self.config["cpu_critical_threshold"]:
                await self._create_alert(
                    AlertLevel.CRITICAL,
                    "High CPU Usage",
                    f"CPU usage is {metrics.cpu_usage:.1f}% (critical threshold: {self.config['cpu_critical_threshold']}%)",
                )
            elif metrics.cpu_usage >= self.config["cpu_warning_threshold"]:
                await self._create_alert(
                    AlertLevel.WARNING,
                    "Elevated CPU Usage",
                    f"CPU usage is {metrics.cpu_usage:.1f}% (warning threshold: {self.config['cpu_warning_threshold']}%)",
                )

            # Memory alerts
            if metrics.memory_usage >= self.config["memory_critical_threshold"]:
                await self._create_alert(
                    AlertLevel.CRITICAL,
                    "High Memory Usage",
                    f"Memory usage is {metrics.memory_usage:.1f}% (critical threshold: {self.config['memory_critical_threshold']}%)",
                )
            elif metrics.memory_usage >= self.config["memory_warning_threshold"]:
                await self._create_alert(
                    AlertLevel.WARNING,
                    "Elevated Memory Usage",
                    f"Memory usage is {metrics.memory_usage:.1f}% (warning threshold: {self.config['memory_warning_threshold']}%)",
                )

            # Disk alerts
            if metrics.disk_usage >= self.config["disk_critical_threshold"]:
                await self._create_alert(
                    AlertLevel.CRITICAL,
                    "High Disk Usage",
                    f"Disk usage is {metrics.disk_usage:.1f}% (critical threshold: {self.config['disk_critical_threshold']}%)",
                )
            elif metrics.disk_usage >= self.config["disk_warning_threshold"]:
                await self._create_alert(
                    AlertLevel.WARNING,
                    "Elevated Disk Usage",
                    f"Disk usage is {metrics.disk_usage:.1f}% (warning threshold: {self.config['disk_warning_threshold']}%)",
                )

        except Exception as e:
            logger.error(f"Error checking metric alerts: {e}")

    async def _create_alert(self, level: AlertLevel, title: str, message: str):
        """Create a new alert."""
        try:
            alert = {
                "id": f"alert_{int(time.time())}",
                "level": level.value,
                "title": title,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "acknowledged": False,
            }

            self.alerts.append(alert)

            # Keep only recent alerts (last 100)
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]

            logger.warning(f"Alert created: {level.value} - {title}: {message}")

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    async def _cleanup_old_data(self):
        """Clean up old metrics and data."""
        try:
            # Remove old metrics
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=self.config["metrics_retention_hours"]
            )
            self.metrics_history = [
                metric
                for metric in self.metrics_history
                if metric.timestamp > cutoff_time
            ]

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            # Determine overall health
            overall_status = HealthStatus.HEALTHY

            # Check service health
            for health_check in self.health_checks.values():
                if health_check.status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                    break
                elif (
                    health_check.status == HealthStatus.WARNING
                    and overall_status == HealthStatus.HEALTHY
                ):
                    overall_status = HealthStatus.WARNING

            # Get latest metrics
            latest_metrics = self.metrics_history[-1] if self.metrics_history else None

            # Count alerts by level
            alert_counts = {
                "critical": sum(
                    1
                    for alert in self.alerts
                    if alert["level"] == "critical" and not alert["acknowledged"]
                ),
                "error": sum(
                    1
                    for alert in self.alerts
                    if alert["level"] == "error" and not alert["acknowledged"]
                ),
                "warning": sum(
                    1
                    for alert in self.alerts
                    if alert["level"] == "warning" and not alert["acknowledged"]
                ),
                "info": sum(
                    1
                    for alert in self.alerts
                    if alert["level"] == "info" and not alert["acknowledged"]
                ),
            }

            return {
                "overall_status": overall_status.value,
                "uptime_seconds": (
                    datetime.now(timezone.utc) - self.start_time
                ).total_seconds(),
                "services": {
                    service_name: health_check.to_dict()
                    for service_name, health_check in self.health_checks.items()
                },
                "latest_metrics": latest_metrics.to_dict() if latest_metrics else None,
                "alert_counts": alert_counts,
                "monitoring_active": self._monitoring_task is not None
                and not self._monitoring_task.done(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "overall_status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def get_performance_metrics(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance metrics for the specified time period."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            recent_metrics = [
                metric
                for metric in self.metrics_history
                if metric.timestamp > cutoff_time
            ]

            if not recent_metrics:
                return {"error": "No metrics available for the specified time period"}

            # Calculate averages
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(
                recent_metrics
            )
            avg_disk = sum(m.disk_usage for m in recent_metrics) / len(recent_metrics)

            # Find peaks
            max_cpu = max(m.cpu_usage for m in recent_metrics)
            max_memory = max(m.memory_usage for m in recent_metrics)
            max_disk = max(m.disk_usage for m in recent_metrics)

            return {
                "time_period_hours": hours,
                "metrics_count": len(recent_metrics),
                "averages": {
                    "cpu_usage_percent": round(avg_cpu, 2),
                    "memory_usage_percent": round(avg_memory, 2),
                    "disk_usage_percent": round(avg_disk, 2),
                },
                "peaks": {
                    "max_cpu_usage_percent": round(max_cpu, 2),
                    "max_memory_usage_percent": round(max_memory, 2),
                    "max_disk_usage_percent": round(max_disk, 2),
                },
                "latest_metrics": recent_metrics[-1].to_dict(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}

    def get_alerts(self, acknowledged: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by acknowledgment status."""
        try:
            if acknowledged is None:
                return self.alerts.copy()
            else:
                return [
                    alert
                    for alert in self.alerts
                    if alert["acknowledged"] == acknowledged
                ]
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []


# Global production monitoring service instance
production_monitoring_service = ProductionMonitoringService()
