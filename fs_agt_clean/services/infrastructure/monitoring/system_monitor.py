"""System monitoring functionality."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, cast

import psutil
from psutil._common import snetio

from fs_agt_clean.core.monitoring.metrics.models import MetricDataPoint
from fs_agt_clean.core.monitoring.models import (
    MetricCategory,
    MetricType,
    ResourceType,
    SystemMetrics,
)


class SystemMonitor:
    """System monitoring functionality."""

    def __init__(self, history_size: int = 100):
        """Initialize system monitor.

        Args:
            history_size: Number of metrics to keep in history
        """
        self._history_size = history_size
        self.metrics_history: List[SystemMetrics] = []
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

    async def start_monitoring(self) -> None:
        """Start monitoring."""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop monitoring."""
        if self._monitoring:
            self._monitoring = False
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self._history_size:
                    self.metrics_history.pop(0)
                await asyncio.sleep(60)  # Monitor every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)

    async def collect_metrics(self) -> SystemMetrics:
        """Collect current metrics.

        Returns:
            Current system metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if not isinstance(cpu_percent, (int, float)):
                cpu_percent = 0.0

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = getattr(memory, "percent", 0.0)

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = getattr(disk, "percent", 0.0)

            # Network IO
            net_io = psutil.net_io_counters()
            if isinstance(net_io, tuple):
                net_io_dict = net_io._asdict()
                bytes_recv = float(net_io_dict.get("bytes_recv", 0))
                bytes_sent = float(net_io_dict.get("bytes_sent", 0))
            else:
                bytes_recv = 0.0
                bytes_sent = 0.0

            return SystemMetrics(
                cpu_usage=float(cpu_percent),
                memory_usage=float(memory_percent),
                disk_usage=float(disk_percent),
                network_in=bytes_recv,
                network_out=bytes_sent,
                timestamp=datetime.utcnow(),
                total_requests=0,
                success_rate=1.0,
                avg_latency=0.0,
                peak_latency=0.0,
                total_errors=0,
                resource_usage={},
            )
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_in=0.0,
                network_out=0.0,
                timestamp=datetime.utcnow(),
                total_requests=0,
                success_rate=1.0,
                avg_latency=0.0,
                peak_latency=0.0,
                total_errors=0,
                resource_usage={},
            )

    def get_metrics_history(self) -> List[SystemMetrics]:
        """Get metrics history.

        Returns:
            List of historical metrics
        """
        return self.metrics_history

    def clear_history(self) -> None:
        """Clear metrics history."""
        self.metrics_history.clear()

    def get_system_health(self) -> Dict[str, str]:
        """Get overall system health status.

        Returns:
            Dict with health status for different metrics
        """
        if not self.metrics_history:
            return {"status": "No metrics collected"}

        latest = self.metrics_history[-1]
        status = {
            "cpu": "Healthy" if latest.cpu_usage < 80 else "Warning",
            "memory": "Healthy" if latest.memory_usage < 80 else "Warning",
            "disk": "Healthy" if latest.disk_usage < 80 else "Warning",
        }
        return status
