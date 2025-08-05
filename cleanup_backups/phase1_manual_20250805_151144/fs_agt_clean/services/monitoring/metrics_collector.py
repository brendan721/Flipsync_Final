"""
Background metrics collector service.

This service automatically collects and stores system and agent metrics
at regular intervals for historical analysis and monitoring.
"""

import asyncio
import logging
import socket
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import psutil

from fs_agt_clean.core.monitoring.health_monitor import RealHealthMonitor
from fs_agt_clean.database.models.metrics import MetricCategory, MetricType
from fs_agt_clean.services.monitoring.metrics_service import MetricsService


class MetricsCollector:
    """Background service for collecting and storing metrics."""

    def __init__(
        self,
        metrics_service: MetricsService,
        health_monitor: Optional[RealHealthMonitor] = None,
        collection_interval: int = 60,  # seconds
        service_name: str = "flipsync-api",
    ):
        """Initialize the metrics collector.

        Args:
            metrics_service: Metrics service for storing data
            health_monitor: Health monitor for agent status
            collection_interval: Collection interval in seconds
            service_name: Name of the service
        """
        self.metrics_service = metrics_service
        self.health_monitor = health_monitor or RealHealthMonitor()
        self.collection_interval = collection_interval
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)

        # Control flags
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Get hostname
        self.hostname = socket.gethostname()

    async def start(self) -> None:
        """Start the metrics collection service."""
        if self._running:
            self.logger.warning("Metrics collector is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        self.logger.info(
            f"Started metrics collector with {self.collection_interval}s interval"
        )

    async def stop(self) -> None:
        """Stop the metrics collection service."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.logger.info("Stopped metrics collector")

    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while self._running:
            try:
                await self._collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_all_metrics(self) -> None:
        """Collect all types of metrics."""
        timestamp = datetime.now(timezone.utc)

        # Collect system metrics
        await self._collect_system_metrics(timestamp)

        # Collect agent metrics if health monitor is available
        if self.health_monitor:
            await self._collect_agent_metrics(timestamp)

        # Collect individual metric data points
        await self._collect_individual_metrics(timestamp)

    async def _collect_system_metrics(self, timestamp: datetime) -> None:
        """Collect and store system metrics."""
        try:
            # Get system metrics from health monitor
            system_metrics = self.health_monitor.get_system_metrics()

            if system_metrics:
                # Store system metrics snapshot
                await self.metrics_service.store_system_metrics(
                    cpu_usage_percent=system_metrics["cpu_percent"],
                    memory_total_bytes=system_metrics["memory_total"],
                    memory_used_bytes=system_metrics["memory_used"],
                    memory_usage_percent=system_metrics["memory_percent"],
                    disk_total_bytes=system_metrics["disk_total"],
                    disk_used_bytes=system_metrics["disk_used"],
                    disk_usage_percent=system_metrics["disk_percent"],
                    network_bytes_sent=system_metrics["network_sent"],
                    network_bytes_received=system_metrics["network_received"],
                    process_cpu_percent=0.0,  # Not available from health monitor
                    process_memory_percent=0.0,  # Not available from health monitor
                    process_memory_rss=0,  # Not available from health monitor
                    process_memory_vms=0,  # Not available from health monitor
                    process_num_threads=0,  # Not available from health monitor
                    process_num_fds=0,  # Not available from health monitor
                    hostname=self.hostname,
                    service_name=self.service_name,
                    timestamp=timestamp,
                )

                self.logger.debug("Collected system metrics")
            else:
                self.logger.debug("No system metrics available from health monitor")
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")

    async def _collect_agent_metrics(self, timestamp: datetime) -> None:
        """Collect and store agent metrics."""
        try:
            # For now, skip agent metrics collection since RealHealthMonitor
            # doesn't have get_agent_status method
            # This can be implemented when agent management is added
            self.logger.debug(
                "UnifiedAgent metrics collection skipped - no agent management available"
            )
        except Exception as e:
            self.logger.error(f"Error collecting agent metrics: {e}")

    async def _collect_individual_metrics(self, timestamp: datetime) -> None:
        """Collect individual metric data points."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.metrics_service.store_metric_data_point(
                name="cpu_usage_percent",
                value=cpu_percent,
                metric_type=MetricType.GAUGE,
                category=MetricCategory.SYSTEM,
                service_name=self.service_name,
                timestamp=timestamp,
            )

            # Memory metrics
            memory = psutil.virtual_memory()
            await self.metrics_service.store_metric_data_point(
                name="memory_usage_percent",
                value=memory.percent,
                metric_type=MetricType.GAUGE,
                category=MetricCategory.SYSTEM,
                service_name=self.service_name,
                timestamp=timestamp,
            )

            await self.metrics_service.store_metric_data_point(
                name="memory_available_bytes",
                value=float(memory.available),
                metric_type=MetricType.GAUGE,
                category=MetricCategory.SYSTEM,
                service_name=self.service_name,
                timestamp=timestamp,
            )

            # Disk metrics
            disk = psutil.disk_usage("/")
            await self.metrics_service.store_metric_data_point(
                name="disk_usage_percent",
                value=(disk.used / disk.total) * 100,
                metric_type=MetricType.GAUGE,
                category=MetricCategory.SYSTEM,
                service_name=self.service_name,
                timestamp=timestamp,
            )

            # Network metrics
            network = psutil.net_io_counters()
            await self.metrics_service.store_metric_data_point(
                name="network_bytes_sent_total",
                value=float(network.bytes_sent),
                metric_type=MetricType.COUNTER,
                category=MetricCategory.SYSTEM,
                service_name=self.service_name,
                timestamp=timestamp,
            )

            await self.metrics_service.store_metric_data_point(
                name="network_bytes_received_total",
                value=float(network.bytes_recv),
                metric_type=MetricType.COUNTER,
                category=MetricCategory.SYSTEM,
                service_name=self.service_name,
                timestamp=timestamp,
            )

            self.logger.debug("Collected individual metrics")
        except Exception as e:
            self.logger.error(f"Error collecting individual metrics: {e}")

    async def collect_once(self) -> Dict[str, Any]:
        """Collect metrics once and return the data.

        Returns:
            Dictionary containing collected metrics
        """
        timestamp = datetime.now(timezone.utc)

        try:
            # Collect all metrics
            await self._collect_all_metrics()

            return {
                "timestamp": timestamp.isoformat(),
                "status": "success",
                "message": "Metrics collected successfully",
            }
        except Exception as e:
            self.logger.error(f"Error in one-time collection: {e}")
            return {
                "timestamp": timestamp.isoformat(),
                "status": "error",
                "message": str(e),
            }

    @property
    def is_running(self) -> bool:
        """Check if the collector is running."""
        return self._running


@asynccontextmanager
async def metrics_collector_context(
    metrics_service: MetricsService,
    health_monitor: Optional[RealHealthMonitor] = None,
    collection_interval: int = 60,
    service_name: str = "flipsync-api",
):
    """Context manager for metrics collector lifecycle.

    Args:
        metrics_service: Metrics service for storing data
        health_monitor: Health monitor for agent status
        collection_interval: Collection interval in seconds
        service_name: Name of the service
    """
    collector = MetricsCollector(
        metrics_service=metrics_service,
        health_monitor=health_monitor,
        collection_interval=collection_interval,
        service_name=service_name,
    )

    try:
        await collector.start()
        yield collector
    finally:
        await collector.stop()
