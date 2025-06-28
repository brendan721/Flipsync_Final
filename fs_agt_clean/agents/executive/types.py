"""Executive agent type definitions."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExecutiveState(str, Enum):
    """Executive agent state indicators."""

    IDLE = "idle"
    ANALYZING = "analyzing"
    DECIDING = "deciding"
    DELEGATING = "delegating"
    MONITORING = "monitoring"
    REVIEWING = "reviewing"
    SUSPENDED = "suspended"


class ExecutiveAction(str, Enum):
    """Executive action types."""

    ANALYZE = "analyze"
    DECIDE = "decide"
    DELEGATE = "delegate"
    MONITOR = "monitor"
    REVIEW = "review"
    APPROVE = "approve"
    REJECT = "reject"
    SUSPEND = "suspend"
    RESUME = "resume"


class DecisionImpact(BaseModel):
    """Impact assessment for decisions."""

    financial: float = Field(0.0, description="Financial impact value")
    operational: float = Field(
        0.0, ge=0.0, le=1.0, description="Operational impact score"
    )
    strategic: float = Field(
        0.0, ge=0.0, le=1.0, description="Strategic alignment score"
    )
    risk_level: float = Field(0.0, ge=0.0, le=1.0, description="Risk assessment score")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("financial", mode="before")
    @classmethod
    def validate_financial(cls, v: Any) -> float:
        """Validate financial impact."""
        try:
            return float(v)
        except (TypeError, ValueError):
            raise ValueError("invalid financial impact value")


class Decision(BaseModel):
    """Executive decision information."""

    id: str = Field(..., description="Decision identifier")
    type: str = Field(..., description="Decision type")
    description: str = Field(..., description="Decision description")
    priority: int = Field(1, ge=1, le=5, description="Priority level (1-5)")
    status: str = Field("pending", description="Decision status")
    impact: DecisionImpact
    prerequisites: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None

    model_config = {"json_encoders": {datetime: lambda dt: dt.isoformat()}}

    @field_validator("decided_at", "implemented_at", mode="before")
    @classmethod
    def validate_datetime(cls, v: Any) -> Optional[datetime]:
        """Validate datetime fields."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        raise ValueError("invalid datetime format")


class Strategy(BaseModel):
    """Strategic plan information."""

    id: str = Field(..., description="Strategy identifier")
    name: str = Field(..., description="Strategy name")
    objectives: List[str] = Field(..., description="Strategic objectives")
    timeframe: Dict[str, datetime] = Field(..., description="Strategy timeframe")
    kpis: Dict[str, float] = Field(default_factory=dict)
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Implementation progress")
    status: str = Field("draft", description="Strategy status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"json_encoders": {datetime: lambda dt: dt.isoformat()}}

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, v: Dict[str, Any]) -> Dict[str, datetime]:
        """Validate strategy timeframe."""
        required_keys = {"start", "end"}
        if not all(key in v for key in required_keys):
            raise ValueError("timeframe must include start and end dates")

        timeframe: Dict[str, datetime] = {}
        for key, value in v.items():
            if isinstance(value, datetime):
                timeframe[key] = value
            else:
                raise ValueError(f"invalid datetime for timeframe {key}")
        return timeframe


class ExecutiveMetrics(BaseModel):
    """Executive performance metrics."""

    timestamp: datetime = Field(..., description="Measurement timestamp")
    decisions_made: int = Field(0, ge=0, description="Number of decisions made")
    decisions_implemented: int = Field(
        0, ge=0, description="Number of implemented decisions"
    )
    avg_decision_time: float = Field(
        0.0, ge=0.0, description="Average decision time in hours"
    )
    strategic_alignment: float = Field(
        0.0, ge=0.0, le=1.0, description="Strategic alignment score"
    )
    operational_efficiency: float = Field(
        0.0, ge=0.0, le=1.0, description="Operational efficiency score"
    )
    risk_management: float = Field(
        0.0, ge=0.0, le=1.0, description="Risk management effectiveness"
    )

    model_config = {"json_encoders": {datetime: lambda dt: dt.isoformat()}}

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v: Any) -> datetime:
        """Validate timestamp."""
        if isinstance(v, datetime):
            return v
        raise ValueError("timestamp must be a datetime object")

    def to_dict(self) -> Dict[str, Union[datetime, float, int]]:
        """Convert metrics to dictionary."""
        return {
            "timestamp": self.timestamp,
            "decisions_made": self.decisions_made,
            "decisions_implemented": self.decisions_implemented,
            "avg_decision_time": self.avg_decision_time,
            "strategic_alignment": self.strategic_alignment,
            "operational_efficiency": self.operational_efficiency,
            "risk_management": self.risk_management,
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Union[datetime, float, int]]
    ) -> "ExecutiveMetrics":
        """Create metrics from dictionary."""
        return cls.model_validate(data)
