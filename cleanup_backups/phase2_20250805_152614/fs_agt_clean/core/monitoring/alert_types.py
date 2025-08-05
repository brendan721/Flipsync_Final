"""Alert-specific types."""

from enum import Enum
from typing import Any, Literal

ComparisonOperator = Literal["gt", "lt", "eq", "ne", "ge", "le"]


class AlertSeverity(str, Enum):
    """Alert severity levels, ordered from lowest to highest."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __lt__(self, other: Any) -> bool:
        """Compare severity levels."""
        if not isinstance(other, AlertSeverity):
            return NotImplemented
        order = {
            AlertSeverity.INFO: 0,
            AlertSeverity.LOW: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.HIGH: 3,
            AlertSeverity.CRITICAL: 4,
        }
        return order[self] < order[other]

    def __gt__(self, other: Any) -> bool:
        """Compare severity levels."""
        if not isinstance(other, AlertSeverity):
            return NotImplemented
        return not (self <= other)

    def __le__(self, other: Any) -> bool:
        """Compare severity levels."""
        if not isinstance(other, AlertSeverity):
            return NotImplemented
        return bool(self < other or self == other)

    def __ge__(self, other: Any) -> bool:
        """Compare severity levels."""
        if not isinstance(other, AlertSeverity):
            return NotImplemented
        return not (self < other)


class AlertStatus(Enum):
    """Alert status."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AlertType(Enum):
    """Type of alert."""

    RESOURCE = "resource"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CUSTOM = "custom"
