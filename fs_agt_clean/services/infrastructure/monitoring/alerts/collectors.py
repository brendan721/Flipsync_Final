import asyncio
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fs_agt_clean.core.monitoring.alerts.models import ErrorMetrics, LatencyMetrics

"""Metric Collection System"""


class MetricCollector:

    def __init__(self, window_size: int = 300):
        self.window_size = window_size
        self.latency_buffer: Dict[str, List[float]] = {}
        self.error_buffer: Dict[str, List[tuple[str, datetime]]] = {}
        self._lock = asyncio.Lock()

    async def record_latency(
        self, endpoint: str, value: float, timestamp: Optional[datetime] = None
    ) -> None:
        """Record a latency measurement for an endpoint"""
        async with self._lock:
            if endpoint not in self.latency_buffer:
                self.latency_buffer[endpoint] = []

            self.latency_buffer[endpoint].append(value)
            # Keep only recent measurements
            while len(self.latency_buffer[endpoint]) > self.window_size:
                self.latency_buffer[endpoint].pop(0)

    async def record_error(
        self, category: str, error_message: str, timestamp: Optional[datetime] = None
    ) -> None:
        """Record an error for a category"""
        async with self._lock:
            if category not in self.error_buffer:
                self.error_buffer[category] = []

            ts = timestamp or datetime.utcnow()
            self.error_buffer[category].append((error_message, ts))
            # Keep only recent errors
            cutoff = datetime.utcnow() - timedelta(seconds=self.window_size)
            self.error_buffer[category] = [
                (msg, ts) for msg, ts in self.error_buffer[category] if ts > cutoff
            ]

    async def get_latency_metrics(self, endpoint: str) -> Optional[LatencyMetrics]:
        """Get latency metrics for an endpoint"""
        async with self._lock:
            if endpoint not in self.latency_buffer or not self.latency_buffer[endpoint]:
                return None

            values = self.latency_buffer[endpoint]
            return LatencyMetrics(
                endpoint=endpoint,
                avg_latency=statistics.mean(values),
                p95_latency=statistics.quantiles(values, n=20)[-1],
                p99_latency=statistics.quantiles(values, n=100)[-1],
                max_latency=max(values),
            )

    async def get_error_metrics(self, category: str) -> Optional[ErrorMetrics]:
        """Get error metrics for a category"""
        async with self._lock:
            if category not in self.error_buffer or not self.error_buffer[category]:
                return None

            # Count errors in the last window
            cutoff = datetime.utcnow() - timedelta(seconds=self.window_size)
            recent_errors = [
                (msg, ts) for msg, ts in self.error_buffer[category] if ts > cutoff
            ]

            if not recent_errors:
                return None

            error_count = len(recent_errors)
            error_rate = error_count / self.window_size  # errors per second

            # Use the most common error type
            error_types = [msg.split(":")[0] for msg, _ in recent_errors]
            error_type = max(set(error_types), key=error_types.count)

            return ErrorMetrics(
                endpoint=category,
                error_count=error_count,
                error_rate=error_rate,
                error_type=error_type,
            )

    async def record_start(self, operation: str, context: str) -> None:
        """Record the start of an operation."""
        await self.record_latency(f"{operation}_{context}_start", 0.0)

    async def record_success(self, operation: str, context: str) -> None:
        """Record a successful operation."""
        await self.record_latency(f"{operation}_{context}_success", 0.0)

    async def record_failure(
        self, operation: str, context: str, error_msg: str
    ) -> None:
        """Record a failed operation."""
        await self.record_error(f"{operation}_{context}", error_msg)
