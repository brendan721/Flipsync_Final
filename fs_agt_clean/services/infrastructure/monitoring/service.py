"""
Monitoring Service

This module provides functionality for monitoring system health and performance.
"""

import asyncio
import logging
import os
import platform
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union

import psutil

from fs_agt_clean.core.utils.logging import get_logger
from fs_agt_clean.services.metrics.service import MetricsService

logger = get_logger(__name__)


class MonitoringService:
    """
    Service for monitoring system health and performance.

    This class collects system metrics and stores them using the metrics service.
    """

    def __init__(
        self,
        metrics_service: MetricsService,
        collection_interval: int = 60,  # 1 minute
        system_metrics_enabled: bool = True,
        process_metrics_enabled: bool = True,
        custom_metrics_enabled: bool = True,
    ):
        """
        Initialize the monitoring service.

        Args:
            metrics_service: Metrics service for storing metrics
            collection_interval: Interval between metric collections in seconds
            system_metrics_enabled: Whether to collect system metrics
            process_metrics_enabled: Whether to collect process metrics
            custom_metrics_enabled: Whether to collect custom metrics
        """
        self.metrics_service = metrics_service
        self.collection_interval = collection_interval
        self.system_metrics_enabled = system_metrics_enabled
        self.process_metrics_enabled = process_metrics_enabled
        self.custom_metrics_enabled = custom_metrics_enabled

        self.is_running = False
        self.collection_task = None
        self.last_collection_time = None

        # Process information
        self.process = psutil.Process()
        self.start_time = time.time()

        # Custom metrics
        self.custom_metrics: Dict[str, float] = {}

        logger.info("Monitoring service initialized")

    async def start(self) -> None:
        """Start collecting metrics."""
        if self.is_running:
            logger.warning("Monitoring service is already running")
            return

        self.is_running = True
        self.collection_task = asyncio.create_task(self._collect_metrics_loop())
        logger.info("Started monitoring service")

    async def stop(self) -> None:
        """Stop collecting metrics."""
        if not self.is_running:
            logger.warning("Monitoring service is not running")
            return

        self.is_running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
            self.collection_task = None

        logger.info("Stopped monitoring service")

    async def _collect_metrics_loop(self) -> None:
        """Continuously collect metrics at the configured interval."""
        while self.is_running:
            try:
                await self._collect_metrics()
                self.last_collection_time = datetime.utcnow()

                # Sleep until next collection
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error collecting metrics: %s", e)
                await asyncio.sleep(10)  # Sleep for a short time before retrying

    async def _collect_metrics(self) -> None:
        """Collect all metrics."""
        try:
            # Collect system metrics
            if self.system_metrics_enabled:
                await self._collect_system_metrics()

            # Collect process metrics
            if self.process_metrics_enabled:
                await self._collect_process_metrics()

            # Collect custom metrics
            if self.custom_metrics_enabled:
                await self._collect_custom_metrics()

            logger.debug("Collected metrics")
        except Exception as e:
            logger.error("Error collecting metrics: %s", e)

    async def _collect_system_metrics(self) -> None:
        """Collect system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            await self.metrics_service.record_metric(
                name="system.cpu.percent",
                value=cpu_percent,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.cpu.count",
                value=cpu_count,
                component="system",
            )

            # Memory metrics
            memory = psutil.virtual_memory()

            await self.metrics_service.record_metric(
                name="system.memory.total",
                value=memory.total,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.memory.available",
                value=memory.available,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.memory.used",
                value=memory.used,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.memory.percent",
                value=memory.percent,
                component="system",
            )

            # Disk metrics
            disk = psutil.disk_usage("/")

            await self.metrics_service.record_metric(
                name="system.disk.total",
                value=disk.total,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.disk.used",
                value=disk.used,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.disk.free",
                value=disk.free,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.disk.percent",
                value=disk.percent,
                component="system",
            )

            # Network metrics
            net_io = psutil.net_io_counters()

            await self.metrics_service.record_metric(
                name="system.network.bytes_sent",
                value=net_io.bytes_sent,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.network.bytes_recv",
                value=net_io.bytes_recv,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.network.packets_sent",
                value=net_io.packets_sent,
                component="system",
            )

            await self.metrics_service.record_metric(
                name="system.network.packets_recv",
                value=net_io.packets_recv,
                component="system",
            )

            # System uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time

            await self.metrics_service.record_metric(
                name="system.uptime",
                value=uptime,
                component="system",
            )

            logger.debug("Collected system metrics")
        except Exception as e:
            logger.error("Error collecting system metrics: %s", e)

    async def _collect_process_metrics(self) -> None:
        """Collect process metrics."""
        try:
            # Process CPU metrics
            process_cpu_percent = self.process.cpu_percent(interval=1)

            await self.metrics_service.record_metric(
                name="process.cpu.percent",
                value=process_cpu_percent,
                component="process",
            )

            # Process memory metrics
            process_memory = self.process.memory_info()

            await self.metrics_service.record_metric(
                name="process.memory.rss",
                value=process_memory.rss,
                component="process",
            )

            await self.metrics_service.record_metric(
                name="process.memory.vms",
                value=process_memory.vms,
                component="process",
            )

            # Process threads
            process_threads = self.process.num_threads()

            await self.metrics_service.record_metric(
                name="process.threads",
                value=process_threads,
                component="process",
            )

            # Process open files
            process_open_files = len(self.process.open_files())

            await self.metrics_service.record_metric(
                name="process.open_files",
                value=process_open_files,
                component="process",
            )

            # Process connections
            process_connections = len(self.process.connections())

            await self.metrics_service.record_metric(
                name="process.connections",
                value=process_connections,
                component="process",
            )

            # Process uptime
            process_uptime = time.time() - self.start_time

            await self.metrics_service.record_metric(
                name="process.uptime",
                value=process_uptime,
                component="process",
            )

            logger.debug("Collected process metrics")
        except Exception as e:
            logger.error("Error collecting process metrics: %s", e)

    async def _collect_custom_metrics(self) -> None:
        """Collect custom metrics."""
        try:
            # Record all custom metrics
            for name, value in self.custom_metrics.items():
                await self.metrics_service.record_metric(
                    name=name,
                    value=value,
                    component="custom",
                )

            logger.debug("Collected custom metrics")
        except Exception as e:
            logger.error("Error collecting custom metrics: %s", e)

    def set_custom_metric(self, name: str, value: float) -> None:
        """
        Set a custom metric.

        Args:
            name: Metric name
            value: Metric value
        """
        self.custom_metrics[name] = value

    def increment_custom_metric(self, name: str, value: float = 1.0) -> None:
        """
        Increment a custom metric.

        Args:
            name: Metric name
            value: Value to increment by
        """
        if name not in self.custom_metrics:
            self.custom_metrics[name] = 0.0

        self.custom_metrics[name] += value

    def get_custom_metric(self, name: str) -> Optional[float]:
        """
        Get a custom metric.

        Args:
            name: Metric name

        Returns:
            Metric value if it exists, None otherwise
        """
        return self.custom_metrics.get(name)

    def get_all_custom_metrics(self) -> Dict[str, float]:
        """
        Get all custom metrics.

        Returns:
            Dictionary of custom metrics
        """
        return self.custom_metrics.copy()

    def clear_custom_metrics(self) -> None:
        """Clear all custom metrics."""
        self.custom_metrics.clear()

    def get_system_info(self) -> Dict[str, str]:
        """
        Get system information.

        Returns:
            Dictionary of system information
        """
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        }

    def get_process_info(self) -> Dict[str, Union[str, int, float]]:
        """
        Get process information.

        Returns:
            Dictionary of process information
        """
        return {
            "pid": self.process.pid,
            "name": self.process.name(),
            "exe": self.process.exe(),
            "cwd": self.process.cwd(),
            "cmdline": " ".join(self.process.cmdline()),
            "create_time": datetime.fromtimestamp(
                self.process.create_time()
            ).isoformat(),
            "status": self.process.status(),
            "username": self.process.username(),
            "uptime": time.time() - self.start_time,
        }
