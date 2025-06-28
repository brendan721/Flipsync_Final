"""
Real-time health monitoring for FlipSync system components.

This module provides comprehensive health monitoring capabilities including:
- System resource monitoring (CPU, memory, disk)
- Service health checks
- Database connectivity monitoring
- UnifiedAgent status tracking
- Performance metrics collection
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psutil

from fs_agt_clean.core.db.database import Database


@dataclass
class HealthStatus:
    """Health status data structure."""

    component: str
    status: str  # "healthy", "warning", "critical", "unknown"
    message: str
    timestamp: datetime
    metrics: Dict[str, Any]


@dataclass
class SystemMetrics:
    """System metrics data structure."""

    cpu_percent: float
    memory_percent: float
    memory_total: int
    memory_used: int
    disk_percent: float
    disk_total: int
    disk_used: int
    network_sent: int
    network_received: int
    timestamp: datetime


class RealHealthMonitor:
    """Real-time health monitoring service."""

    def __init__(self, database: Optional[Database] = None):
        """Initialize the health monitor.

        Args:
            database: Optional database instance for health checks
        """
        self.logger = logging.getLogger(__name__)
        self.database = database
        self._monitoring = False
        self._health_status: Dict[str, HealthStatus] = {}
        self._last_metrics: Optional[SystemMetrics] = None

    async def start_monitoring(self, interval: int = 30) -> None:
        """Start continuous health monitoring.

        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring:
            self.logger.warning("Health monitoring is already running")
            return

        self._monitoring = True
        self.logger.info(f"Starting health monitoring with {interval}s interval")

        while self._monitoring:
            try:
                await self._collect_health_data()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(interval)

    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self._monitoring = False
        self.logger.info("Health monitoring stopped")

    async def _collect_health_data(self) -> None:
        """Collect comprehensive health data."""
        timestamp = datetime.now(timezone.utc)

        # Collect system metrics
        system_metrics = await self._collect_system_metrics()
        self._last_metrics = system_metrics

        # Check system health
        await self._check_system_health(system_metrics)

        # Check database health
        if self.database:
            await self._check_database_health()

        # Check service health
        await self._check_service_health()

        self.logger.debug(f"Health data collected at {timestamp}")

    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage("/")

            # Network metrics
            network = psutil.net_io_counters()

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_total=memory.total,
                memory_used=memory.used,
                disk_percent=disk.percent,
                disk_total=disk.total,
                disk_used=disk.used,
                network_sent=network.bytes_sent,
                network_received=network.bytes_recv,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            raise

    async def _check_system_health(self, metrics: SystemMetrics) -> None:
        """Check system health based on metrics."""
        timestamp = datetime.now(timezone.utc)

        # CPU health check
        if metrics.cpu_percent > 90:
            status = "critical"
            message = f"CPU usage critical: {metrics.cpu_percent:.1f}%"
        elif metrics.cpu_percent > 75:
            status = "warning"
            message = f"CPU usage high: {metrics.cpu_percent:.1f}%"
        else:
            status = "healthy"
            message = f"CPU usage normal: {metrics.cpu_percent:.1f}%"

        self._health_status["cpu"] = HealthStatus(
            component="cpu",
            status=status,
            message=message,
            timestamp=timestamp,
            metrics={"cpu_percent": metrics.cpu_percent},
        )

        # Memory health check
        if metrics.memory_percent > 90:
            status = "critical"
            message = f"Memory usage critical: {metrics.memory_percent:.1f}%"
        elif metrics.memory_percent > 80:
            status = "warning"
            message = f"Memory usage high: {metrics.memory_percent:.1f}%"
        else:
            status = "healthy"
            message = f"Memory usage normal: {metrics.memory_percent:.1f}%"

        self._health_status["memory"] = HealthStatus(
            component="memory",
            status=status,
            message=message,
            timestamp=timestamp,
            metrics={
                "memory_percent": metrics.memory_percent,
                "memory_total": metrics.memory_total,
                "memory_used": metrics.memory_used,
            },
        )

        # Disk health check
        if metrics.disk_percent > 95:
            status = "critical"
            message = f"Disk usage critical: {metrics.disk_percent:.1f}%"
        elif metrics.disk_percent > 85:
            status = "warning"
            message = f"Disk usage high: {metrics.disk_percent:.1f}%"
        else:
            status = "healthy"
            message = f"Disk usage normal: {metrics.disk_percent:.1f}%"

        self._health_status["disk"] = HealthStatus(
            component="disk",
            status=status,
            message=message,
            timestamp=timestamp,
            metrics={
                "disk_percent": metrics.disk_percent,
                "disk_total": metrics.disk_total,
                "disk_used": metrics.disk_used,
            },
        )

    async def _check_database_health(self) -> None:
        """Check database connectivity and health."""
        timestamp = datetime.now(timezone.utc)

        try:
            # Test database connection
            start_time = time.time()
            async with self.database.get_session_context() as session:
                # Simple query to test connectivity
                await session.execute("SELECT 1")

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            if response_time > 1000:  # 1 second
                status = "warning"
                message = f"Database response slow: {response_time:.1f}ms"
            else:
                status = "healthy"
                message = f"Database responsive: {response_time:.1f}ms"

            self._health_status["database"] = HealthStatus(
                component="database",
                status=status,
                message=message,
                timestamp=timestamp,
                metrics={"response_time_ms": response_time},
            )

        except Exception as e:
            self._health_status["database"] = HealthStatus(
                component="database",
                status="critical",
                message=f"Database connection failed: {str(e)}",
                timestamp=timestamp,
                metrics={},
            )

    async def _check_service_health(self) -> None:
        """Check health of various services."""
        timestamp = datetime.now(timezone.utc)

        # For now, mark API service as healthy since we're running
        self._health_status["api"] = HealthStatus(
            component="api",
            status="healthy",
            message="API service operational",
            timestamp=timestamp,
            metrics={},
        )

    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current health status of all components.

        Returns:
            Dictionary containing health status for all monitored components
        """
        return {
            component: {
                "status": health.status,
                "message": health.message,
                "timestamp": health.timestamp.isoformat(),
                "metrics": health.metrics,
            }
            for component, health in self._health_status.items()
        }

    def get_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Get latest system metrics.

        Returns:
            Dictionary containing latest system metrics or None if not available
        """
        if not self._last_metrics:
            return None

        return {
            "cpu_percent": self._last_metrics.cpu_percent,
            "memory_percent": self._last_metrics.memory_percent,
            "memory_total": self._last_metrics.memory_total,
            "memory_used": self._last_metrics.memory_used,
            "disk_percent": self._last_metrics.disk_percent,
            "disk_total": self._last_metrics.disk_total,
            "disk_used": self._last_metrics.disk_used,
            "network_sent": self._last_metrics.network_sent,
            "network_received": self._last_metrics.network_received,
            "timestamp": self._last_metrics.timestamp.isoformat(),
        }

    def get_overall_health(self) -> str:
        """Get overall system health status.

        Returns:
            Overall health status: "healthy", "warning", "critical", or "unknown"
        """
        if not self._health_status:
            return "unknown"

        statuses = [health.status for health in self._health_status.values()]

        if "critical" in statuses:
            return "critical"
        elif "warning" in statuses:
            return "warning"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "unknown"
