"""Resource monitoring for system and application resources."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import Request

from fs_agt_clean.core.monitoring.metric_types import MetricCategory, MetricType
from fs_agt_clean.core.monitoring.models import SystemMetrics


class ResourceMonitor:
    """Monitor system and application resources."""

    def __init__(self):
        """Initialize the resource monitor."""
        self.last_network_stats: Dict[str, float] = {
            "rx_bytes": 0,
            "tx_bytes": 0,
            "timestamp": time.time(),
        }
        self.collection_interval = 5.0  # seconds
        self._running = False
        self._metrics_history: List[SystemMetrics] = []
        self._max_history_size = 1000

    async def start(self):
        """Start the resource monitoring loop."""
        if self._running:
            return

        self._running = True
        asyncio.create_task(self._monitoring_loop())

    async def stop(self):
        """Stop the resource monitoring loop."""
        self._running = False

    async def _monitoring_loop(self):
        """Background task to collect resource metrics periodically."""
        while self._running:
            try:
                metrics = await self.get_metrics()
                self._metrics_history.append(metrics)

                # Trim history if needed
                if len(self._metrics_history) > self._max_history_size:
                    self._metrics_history = self._metrics_history[
                        -self._max_history_size :
                    ]
            except Exception:
                # Log error but continue monitoring
                pass

            await asyncio.sleep(self.collection_interval)

    async def get_metrics(self) -> SystemMetrics:
        """
        Get current resource metrics.

        Returns:
            SystemMetrics: Current resource metrics.
        """
        # In a real implementation, this would use psutil or similar
        # For this test implementation, we'll return simulated metrics

        # Simulate CPU usage (0-100%)
        cpu_usage = 45.5

        # Simulate memory usage (in MB)
        memory_usage = 1024.5

        # Simulate disk usage (in MB)
        disk_usage = 5000.0

        # Simulate network usage (in bytes/sec)
        network_in = 1500.0
        network_out = 500.0

        return SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_in=network_in,
            network_out=network_out,
            type=MetricType.RESOURCE_USAGE,
            category=MetricCategory.RESOURCE,
            timestamp=datetime.now(timezone.utc),
        )

    async def get_metrics_by_type(self, resource_type: str) -> SystemMetrics:
        """
        Get metrics for a specific resource type.

        Args:
            resource_type: Type of resource to get metrics for.

        Returns:
            SystemMetrics: Resource metrics for the specified type.
        """
        # In a real implementation, this would filter metrics by type
        # For this test implementation, we'll return the same metrics
        metrics = await self.get_metrics()
        # Add a label to indicate the resource type
        metrics.labels = {"resource_type": resource_type}
        return metrics


# Dependency for FastAPI
def get_resource_monitor(request: Request) -> ResourceMonitor:
    """
    Get the resource monitor from the app state.

    Args:
        request: FastAPI request object.

    Returns:
        ResourceMonitor: Resource monitor instance.
    """
    return request.app.state.resource_monitor
