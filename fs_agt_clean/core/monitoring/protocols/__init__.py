# This file is kept empty to preserve package structure
# Define protocol classes directly to avoid circular imports
from typing import Dict, Optional, Protocol



class MetricsService(Protocol):
    """Protocol for metrics service implementations."""

    async def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None: ...

    async def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None: ...

    async def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None: ...


class AlertService(Protocol):
    """Protocol for alert service implementations."""

    async def send_alert(
        self,
        metric_name: str,
        value: float,
        threshold: float,
        component: str,
        severity: str,
    ) -> bool: ...

    def get_active_alerts(self) -> Dict[str, Dict[str, str]]: ...
