"""Base classes for pattern recognition."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class Pattern:
    """Base class for recognized patterns."""

    pattern_id: str
    pattern_type: str
    confidence: float
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Pattern:
        """Create pattern from dictionary."""
        return cls(
            pattern_id=data["pattern_id"],
            pattern_type=data["pattern_type"],
            confidence=data["confidence"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            metadata=data.get("metadata"),
        )
