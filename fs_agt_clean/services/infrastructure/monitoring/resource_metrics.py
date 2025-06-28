"""
Resource Metrics Collector for FlipSync API

This module provides functionality to monitor and report system resource usage,
including CPU usage, memory consumption, and disk I/O metrics.
"""

import os
import platform
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import psutil


class ResourceMetricsCollector:
    """
    Collects and provides system resource metrics for monitoring.

    This class provides methods to get CPU usage, memory usage, disk utilization,
    and other system resource metrics. It's designed to be used by the metrics
    endpoint to expose resource usage information.
    """

    def __init__(self):
        """Initialize the resource metrics collector"""
        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()
        # Get initial CPU times for delta calculations
        self.last_cpu_times = psutil.cpu_times()
        self.last_cpu_check = time.time()

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get basic system information.

        Returns:
            Dict containing system information like OS, Python version, etc.
        """
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "node": platform.node(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=True),
            "physical_cpu_count": psutil.cpu_count(logical=False) or 1,
        }

    def get_cpu_metrics(self) -> Dict[str, float]:
        """
        Get CPU usage metrics.

        Returns:
            Dict containing CPU usage percentages (system and process).
        """
        # Get current CPU times
        current_cpu_times = psutil.cpu_times()
        current_time = time.time()

        # Calculate time difference
        time_diff = current_time - self.last_cpu_check

        # Ensure we don't divide by zero
        if time_diff < 0.001:
            time_diff = 0.001

        # Calculate CPU usage percentages
        system_cpu_percent = psutil.cpu_percent(interval=None)

        try:
            process_cpu_percent = (
                self.process.cpu_percent(interval=None) / psutil.cpu_count()
            )
        except:
            process_cpu_percent = 0.0

        # Update last CPU times and check time
        self.last_cpu_times = current_cpu_times
        self.last_cpu_check = current_time

        return {
            "system_cpu_percent": round(system_cpu_percent, 2),
            "process_cpu_percent": round(process_cpu_percent, 2),
        }

    def get_memory_metrics(self) -> Dict[str, Union[int, float]]:
        """
        Get memory usage metrics.

        Returns:
            Dict containing memory usage information in bytes and percentages.
        """
        # System memory info
        system_memory = psutil.virtual_memory()

        # Process memory info
        try:
            process_memory = self.process.memory_info()
            process_memory_percent = self.process.memory_percent()
        except:
            process_memory = psutil.virtual_memory()
            process_memory_percent = 0.0

        return {
            "system_total_memory": system_memory.total,
            "system_available_memory": system_memory.available,
            "system_used_memory": system_memory.used,
            "system_memory_percent": round(system_memory.percent, 2),
            "process_rss": getattr(process_memory, "rss", 0),  # Resident Set Size
            "process_vms": getattr(process_memory, "vms", 0),  # Virtual Memory Size
            "process_memory_percent": round(process_memory_percent, 2),
        }

    def get_disk_metrics(self) -> Dict[str, Union[int, float]]:
        """
        Get disk usage metrics.

        Returns:
            Dict containing disk usage information.
        """
        # Try to get the disk where this script is located
        try:
            disk_path = os.path.abspath(os.path.dirname(__file__))
            disk_usage = psutil.disk_usage(disk_path)
        except:
            # Fallback to root path
            try:
                disk_usage = psutil.disk_usage("/")
            except:
                # Return empty dict if we can't get disk info
                return {}

        # Get disk IO counters if available
        try:
            disk_io = psutil.disk_io_counters()
            io_metrics = {
                "disk_read_bytes": disk_io.read_bytes,
                "disk_write_bytes": disk_io.write_bytes,
                "disk_read_count": disk_io.read_count,
                "disk_write_count": disk_io.write_count,
            }
        except:
            io_metrics = {}

        metrics = {
            "disk_total": disk_usage.total,
            "disk_used": disk_usage.used,
            "disk_free": disk_usage.free,
            "disk_percent": round(disk_usage.percent, 2),
        }

        # Add IO metrics if available
        metrics.update(io_metrics)

        return metrics

    def get_network_metrics(self) -> Dict[str, int]:
        """
        Get network usage metrics.

        Returns:
            Dict containing network usage information.
        """
        try:
            network = psutil.net_io_counters()
            return {
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_received": network.bytes_recv,
                "network_packets_sent": network.packets_sent,
                "network_packets_received": network.packets_recv,
                "network_errors_in": network.errin,
                "network_errors_out": network.errout,
            }
        except:
            return {}

    def get_uptime(self) -> Dict[str, float]:
        """
        Get process and system uptime.

        Returns:
            Dict containing uptime information in seconds.
        """
        current_time = time.time()
        process_uptime = current_time - self.start_time

        try:
            system_uptime = current_time - psutil.boot_time()
        except:
            system_uptime = 0.0

        return {
            "process_uptime_seconds": round(process_uptime, 2),
            "system_uptime_seconds": round(system_uptime, 2),
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all resource metrics in a single dictionary.

        Returns:
            Dict containing all resource metrics.
        """
        return {
            "system_info": self.get_system_info(),
            "cpu": self.get_cpu_metrics(),
            "memory": self.get_memory_metrics(),
            "disk": self.get_disk_metrics(),
            "network": self.get_network_metrics(),
            "uptime": self.get_uptime(),
        }

    def get_prometheus_metrics(self) -> List[str]:
        """
        Format resource metrics for Prometheus.

        Returns:
            List of strings containing Prometheus-formatted metrics.
        """
        metrics = []
        all_data = self.get_all_metrics()

        # CPU metrics
        metrics.append(
            f"# HELP flipsync_system_cpu_percent System CPU usage percentage."
        )
        metrics.append(f"# TYPE flipsync_system_cpu_percent gauge")
        metrics.append(
            f'flipsync_system_cpu_percent {all_data["cpu"]["system_cpu_percent"]}'
        )

        metrics.append(
            f"# HELP flipsync_process_cpu_percent Process CPU usage percentage."
        )
        metrics.append(f"# TYPE flipsync_process_cpu_percent gauge")
        metrics.append(
            f'flipsync_process_cpu_percent {all_data["cpu"]["process_cpu_percent"]}'
        )

        # Memory metrics
        metrics.append(
            f"# HELP flipsync_system_memory_percent System memory usage percentage."
        )
        metrics.append(f"# TYPE flipsync_system_memory_percent gauge")
        metrics.append(
            f'flipsync_system_memory_percent {all_data["memory"]["system_memory_percent"]}'
        )

        metrics.append(
            f"# HELP flipsync_process_memory_percent Process memory usage percentage."
        )
        metrics.append(f"# TYPE flipsync_process_memory_percent gauge")
        metrics.append(
            f'flipsync_process_memory_percent {all_data["memory"]["process_memory_percent"]}'
        )

        metrics.append(
            f"# HELP flipsync_process_memory_rss Process resident memory size in bytes."
        )
        metrics.append(f"# TYPE flipsync_process_memory_rss gauge")
        metrics.append(
            f'flipsync_process_memory_rss {all_data["memory"]["process_rss"]}'
        )

        # Disk metrics
        if all_data["disk"]:
            metrics.append(f"# HELP flipsync_disk_usage_percent Disk usage percentage.")
            metrics.append(f"# TYPE flipsync_disk_usage_percent gauge")
            metrics.append(
                f'flipsync_disk_usage_percent {all_data["disk"]["disk_percent"]}'
            )

        # Uptime metrics
        metrics.append(
            f"# HELP flipsync_process_uptime_seconds Process uptime in seconds."
        )
        metrics.append(f"# TYPE flipsync_process_uptime_seconds counter")
        metrics.append(
            f'flipsync_process_uptime_seconds {all_data["uptime"]["process_uptime_seconds"]}'
        )

        return metrics


# Singleton instance
resource_metrics_collector = ResourceMetricsCollector()
