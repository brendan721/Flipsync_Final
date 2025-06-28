"""Metrics utilities."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


class MetricsMixin:
    """Mixin class for tracking operation metrics."""

    async def update_operation_metrics(
        self,
        operation: str,
        execution_time: float,
        success: bool,
        additional_metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update metrics for an operation.

        Args:
            operation: Name of the operation
            execution_time: Time taken to execute in seconds
            success: Whether the operation was successful
            additional_metrics: Additional metrics to track
        """
        # In a real implementation, this would send metrics to a monitoring system
        # For now, we'll just log them
        metrics = {
            "operation": operation,
            "execution_time": execution_time,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if additional_metrics:
            metrics.update(additional_metrics)
        # Here you would typically send these metrics to your monitoring system
        # For example: await self.metrics_client.send(metrics)
