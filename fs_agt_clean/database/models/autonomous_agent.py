"""
Autonomous Agent Database Models for FlipSync 4+1 Architecture
=============================================================

Database models specifically designed for the 4+1 agent architecture:
- 4 Autonomous Agents (Market, Content, Executive, Logistics)
- 1 Conversational Interface (StrategicChatService)

Key Features:
- Strict 4+1 architecture compliance
- LLM-free autonomous agent tracking
- Conversational interface separation
- Performance metrics and health monitoring
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Float, Integer, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fs_agt_clean.database.models.base import Base


class AutonomousAgentType(str, Enum):
    """Autonomous agent types for 4+1 architecture."""

    MARKET = "market"
    CONTENT = "content"
    EXECUTIVE = "executive"
    LOGISTICS = "logistics"


class ConversationalInterfaceType(str, Enum):
    """Conversational interface types."""

    STRATEGIC_CHAT = "strategic_chat"


class AutonomousAgentStatus(str, Enum):
    """Status values for autonomous agents."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class DecisionStatus(str, Enum):
    """Status values for agent decisions."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AutonomousAgent(Base):
    """
    Autonomous Agent Model for 4+1 Architecture

    Represents one of the 4 autonomous agents:
    - MarketAutonomousAgent
    - ContentAutonomousAgent
    - ExecutiveAutonomousAgent
    - LogisticsAutonomousAgent

    Key constraints:
    - LLM-free operation (no LLM dependencies)
    - <1000ms decision times
    - Algorithmic decision making only
    """

    __tablename__ = "autonomous_agents"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Agent identification
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    agent_type: Mapped[AutonomousAgentType] = mapped_column(String(50), nullable=False)
    agent_class: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # e.g., "MarketAutonomousAgent"

    # Agent status and health
    status: Mapped[AutonomousAgentStatus] = mapped_column(
        String(50), default=AutonomousAgentStatus.INITIALIZING
    )
    health_status: Mapped[Optional[str]] = mapped_column(String(50), default="unknown")

    # LLM-free compliance tracking
    llm_free: Mapped[bool] = mapped_column(
        default=True
    )  # Must always be True for autonomous agents
    uses_standard_decision_pipeline: Mapped[bool] = mapped_column(default=True)

    # Performance metrics
    total_decisions: Mapped[int] = mapped_column(Integer, default=0)
    successful_decisions: Mapped[int] = mapped_column(Integer, default=0)
    average_decision_time_ms: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    last_decision_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Capabilities and configuration
    capabilities: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string
    optimization_config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string

    # Timestamps
    initialized_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    decisions: Mapped[List["AutonomousAgentDecision"]] = relationship(
        "AutonomousAgentDecision", back_populates="agent", cascade="all, delete-orphan"
    )


class ConversationalInterface(Base):
    """
    Conversational Interface Model for 4+1 Architecture

    Represents the +1 conversational interface:
    - StrategicChatService (Gemini-powered)

    Key constraints:
    - Gemini-exclusive LLM usage
    - User communication only
    - No autonomous decision making
    """

    __tablename__ = "conversational_interfaces"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Interface identification
    interface_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    interface_type: Mapped[ConversationalInterfaceType] = mapped_column(
        String(50), nullable=False
    )
    service_class: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # e.g., "StrategicChatService"

    # LLM provider tracking
    llm_provider: Mapped[str] = mapped_column(
        String(50), default="gemini"
    )  # Must be "gemini"
    llm_exclusive: Mapped[bool] = mapped_column(
        default=True
    )  # No autonomous decision making

    # Usage statistics
    total_conversations: Mapped[int] = mapped_column(Integer, default=0)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    daily_budget: Mapped[float] = mapped_column(Float, default=10.0)

    # Status and health
    status: Mapped[str] = mapped_column(String(50), default="active")
    health_status: Mapped[Optional[str]] = mapped_column(String(50), default="unknown")

    # Timestamps
    initialized_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AutonomousAgentDecision(Base):
    """
    Autonomous Agent Decision Tracking

    Tracks decisions made by autonomous agents using StandardDecisionPipeline.
    Ensures LLM-free decision making compliance.
    """

    __tablename__ = "autonomous_agent_decisions"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Decision identification
    decision_id: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("autonomous_agents.id"), nullable=False
    )

    # Decision details
    decision_type: Mapped[str] = mapped_column(String(255), nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string

    # Performance tracking
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[DecisionStatus] = mapped_column(String(50), nullable=False)

    # LLM-free compliance
    used_llm: Mapped[bool] = mapped_column(default=False)  # Must always be False
    used_standard_pipeline: Mapped[bool] = mapped_column(
        default=True
    )  # Must always be True
    algorithm_used: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Foreign key relationship
    agent: Mapped["AutonomousAgent"] = relationship(
        "AutonomousAgent", back_populates="decisions"
    )


# Pydantic models for API responses
class AutonomousAgentResponse(BaseModel):
    """Response model for autonomous agent data."""

    id: str
    agent_id: str
    agent_type: AutonomousAgentType
    agent_class: str
    status: AutonomousAgentStatus
    llm_free: bool
    total_decisions: int
    successful_decisions: int
    average_decision_time_ms: Optional[float]
    created_at: datetime
    updated_at: datetime


class ConversationalInterfaceResponse(BaseModel):
    """Response model for conversational interface data."""

    id: str
    interface_id: str
    interface_type: ConversationalInterfaceType
    service_class: str
    llm_provider: str
    total_conversations: int
    total_messages: int
    total_cost: float
    daily_budget: float
    status: str
    created_at: datetime
    updated_at: datetime


class AutonomousAgentDecisionResponse(BaseModel):
    """Response model for autonomous agent decision data."""

    id: str
    decision_id: str
    agent_id: str
    decision_type: str
    execution_time_ms: float
    confidence: float
    status: DecisionStatus
    used_llm: bool
    used_standard_pipeline: bool
    algorithm_used: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]


class ArchitectureComplianceResponse(BaseModel):
    """Response model for 4+1 architecture compliance status."""

    architecture_type: str = "4+1"
    autonomous_agents_count: int
    conversational_interfaces_count: int
    llm_free_compliance: bool
    gemini_exclusive_compliance: bool
    performance_compliance: bool
    total_decisions: int
    average_decision_time_ms: Optional[float]
    compliance_score: float  # 0.0 to 1.0


# Export all models
__all__ = [
    # Enums
    "AutonomousAgentType",
    "ConversationalInterfaceType",
    "AutonomousAgentStatus",
    "DecisionStatus",
    # SQLAlchemy Models
    "AutonomousAgent",
    "ConversationalInterface",
    "AutonomousAgentDecision",
    # Pydantic Models
    "AutonomousAgentResponse",
    "ConversationalInterfaceResponse",
    "AutonomousAgentDecisionResponse",
    "ArchitectureComplianceResponse",
]
