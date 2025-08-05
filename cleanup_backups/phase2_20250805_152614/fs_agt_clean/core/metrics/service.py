"""
Metrics Service compatibility module.

This module provides backward compatibility for metrics service imports.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MetricsService:
    """Simple metrics service for compatibility."""

    def __init__(self):
        """Initialize metrics service."""
        self._metrics = {}

    def increment_counter(
        self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric."""
        key = f"{name}:{tags}" if tags else name
        self._metrics[key] = self._metrics.get(key, 0) + value

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        key = f"{name}:{tags}" if tags else name
        self._metrics[key] = value

    def record_histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a histogram value."""
        key = f"{name}_hist:{tags}" if tags else f"{name}_hist"
        if key not in self._metrics:
            self._metrics[key] = []
        self._metrics[key].append(value)

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return self._metrics.copy()
