"""
Unified UnifiedAgent Models for FlipSync Database
==========================================

This module consolidates all agent-related database models into a single,
standardized hierarchy, eliminating duplication across:
- fs_agt_clean/database/models/agents.py (SQLAlchemy models)
- fs_agt_clean/core/models/database/agents.py (SQLAlchemy models)

AGENT_CONTEXT: Complete agent management system with status tracking, decisions, tasks, and performance metrics
AGENT_PRIORITY: Database models for agent coordination, decision tracking, and performance monitoring
AGENT_PATTERN: SQLAlchemy async models with proper relationships and comprehensive agent lifecycle management
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .unified_base import Base


# Enums for agent management
class UnifiedAgentType(str, Enum):
    """UnifiedAgent type classification"""

    MARKET = "market"
    EXECUTIVE = "executive"
    CONTENT = "content"
    LOGISTICS = "logistics"
    ANALYTICS = "analytics"
    COMMUNICATION = "communication"
    SECURITY = "security"
    OPTIMIZATION = "optimization"


class UnifiedAgentStatus(str, Enum):
    """UnifiedAgent operational status"""

    INITIALIZING = "initializing"
    RUNNING = "running"
    IDLE = "idle"
    BUSY = "busy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class UnifiedAgentPriority(str, Enum):
    """UnifiedAgent priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task execution status"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class DecisionStatus(str, Enum):
    """Decision approval status"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class UnifiedAgent(Base):
    """
    Unified UnifiedAgent Model - Consolidates all agent functionality

    This model combines features from:
    - UnifiedUnifiedAgent (core agent information)
    - UnifiedAgentStatus (status tracking)
    - UnifiedAgent performance and health monitoring
    """

    __tablename__ = "unified_agents"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Basic agent information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[UnifiedAgentType] = mapped_column(String(50), nullable=False)
    status: Mapped[UnifiedAgentStatus] = mapped_column(
        String(50), default=UnifiedAgentStatus.INITIALIZING
    )
    priority: Mapped[UnifiedAgentPriority] = mapped_column(
        String(20), default=UnifiedAgentPriority.MEDIUM
    )

    # UnifiedAgent configuration
    capabilities: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string
    configuration: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string
    authority_level: Mapped[UnifiedAgentPriority] = mapped_column(
        String(20), default=UnifiedAgentPriority.MEDIUM
    )

    # UnifiedAgent state and health
    health_status: Mapped[Optional[str]] = mapped_column(String(50), default="unknown")
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Performance metrics
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_tasks_completed: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_decisions_made: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # UnifiedAgent metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(50), default="1.0.0")
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string

    # Resource usage
    cpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
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
    decisions: Mapped[List["UnifiedAgentDecision"]] = relationship(
        "UnifiedAgentDecision", back_populates="agent", cascade="all, delete-orphan"
    )
    tasks: Mapped[List["UnifiedAgentTask"]] = relationship(
        "UnifiedAgentTask", back_populates="agent", cascade="all, delete-orphan"
    )
    communications: Mapped[List["UnifiedAgentCommunication"]] = relationship(
        "UnifiedAgentCommunication",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    performance_metrics: Mapped[List["UnifiedAgentPerformanceMetric"]] = relationship(
        "UnifiedAgentPerformanceMetric",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    def update_heartbeat(self):
        """Update agent heartbeat timestamp"""
        self.last_heartbeat = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)

    def increment_success(self):
        """Increment success counter"""
        self.success_count += 1

    def increment_error(self):
        """Increment error counter"""
        self.error_count += 1

    def calculate_success_rate(self) -> float:
        """Calculate agent success rate"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def is_healthy(self) -> bool:
        """Check if agent is healthy based on recent activity"""
        if not self.last_heartbeat:
            return False

        # Consider agent unhealthy if no heartbeat in last 5 minutes
        time_since_heartbeat = datetime.now(timezone.utc) - self.last_heartbeat
        return time_since_heartbeat.total_seconds() < 300

    def __repr__(self):
        return f"<UnifiedAgent(id={self.id}, name={self.name}, type={self.agent_type}, status={self.status})>"


class UnifiedAgentDecision(Base):
    """UnifiedAgent decision tracking and approval workflow"""

    __tablename__ = "agent_decisions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(String(255), ForeignKey("unified_agents.id"))

    # Decision details
    decision_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Decision status and approval
    status: Mapped[DecisionStatus] = mapped_column(
        String(20), default=DecisionStatus.PENDING
    )
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    execution_result: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    agent: Mapped["UnifiedAgent"] = relationship(
        "UnifiedAgent", back_populates="decisions"
    )

    def __repr__(self):
        return f"<UnifiedAgentDecision(id={self.id}, agent_id={self.agent_id}, type={self.decision_type}, status={self.status})>"


class UnifiedAgentTask(Base):
    """UnifiedAgent task management and execution tracking"""

    __tablename__ = "agent_tasks"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(String(255), ForeignKey("unified_agents.id"))

    # Task details
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_parameters: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string

    # Task execution
    status: Mapped[TaskStatus] = mapped_column(String(20), default=TaskStatus.QUEUED)
    priority: Mapped[int] = mapped_column(
        Integer, default=5
    )  # 1-10, where 1 is highest
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Progress tracking
    progress_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_duration: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # seconds
    actual_duration: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # seconds

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    agent: Mapped["UnifiedAgent"] = relationship("UnifiedAgent", back_populates="tasks")

    def calculate_duration(self) -> Optional[int]:
        """Calculate task duration in seconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    def __repr__(self):
        return f"<UnifiedAgentTask(id={self.id}, agent_id={self.agent_id}, name={self.task_name}, status={self.status})>"


class UnifiedAgentCommunication(Base):
    """UnifiedAgent-to-agent communication tracking"""

    __tablename__ = "agent_communications"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(String(255), ForeignKey("unified_agents.id"))

    # Communication details
    target_agent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message_content: Mapped[str] = mapped_column(Text, nullable=False)

    # Communication metadata
    priority: Mapped[int] = mapped_column(Integer, default=5)
    requires_response: Mapped[bool] = mapped_column(Boolean, default=False)
    response_received: Mapped[bool] = mapped_column(Boolean, default=False)
    response_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    agent: Mapped["UnifiedAgent"] = relationship(
        "UnifiedAgent", back_populates="communications"
    )

    def __repr__(self):
        return f"<UnifiedAgentCommunication(id={self.id}, agent_id={self.agent_id}, type={self.message_type})>"


class UnifiedAgentPerformanceMetric(Base):
    """UnifiedAgent performance metrics tracking"""

    __tablename__ = "agent_performance_metrics"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_id: Mapped[str] = mapped_column(String(255), ForeignKey("unified_agents.id"))

    # Metric details
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Metric metadata
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string

    # Timestamp
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    agent: Mapped["UnifiedAgent"] = relationship(
        "UnifiedAgent", back_populates="performance_metrics"
    )

    def __repr__(self):
        return f"<UnifiedAgentPerformanceMetric(id={self.id}, agent_id={self.agent_id}, metric={self.metric_name}, value={self.metric_value})>"


# Pydantic models for API responses
class UnifiedAgentResponse(BaseModel):
    """API response model for agent data"""

    id: str
    name: str
    agent_type: UnifiedAgentType
    status: UnifiedAgentStatus
    priority: UnifiedAgentPriority
    health_status: Optional[str]
    success_count: int
    error_count: int
    total_tasks_completed: int
    created_at: datetime
    last_activity: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UnifiedAgentCreate(BaseModel):
    """Model for creating a new agent"""

    name: str = Field(..., min_length=1, max_length=255)
    agent_type: UnifiedAgentType
    priority: UnifiedAgentPriority = UnifiedAgentPriority.MEDIUM
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None


class UnifiedAgentUpdate(BaseModel):
    """Model for updating an agent"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[UnifiedAgentStatus] = None
    priority: Optional[UnifiedAgentPriority] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """API response model for task data"""

    id: str
    agent_id: str
    task_type: str
    task_name: str
    status: TaskStatus
    priority: int
    progress_percentage: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    """Model for creating a new task"""

    agent_id: str
    task_type: str
    task_name: str = Field(..., min_length=1, max_length=200)
    task_parameters: Optional[Dict[str, Any]] = None
    priority: int = Field(5, ge=1, le=10)


# Backward compatibility aliases
AgentType = UnifiedAgentType
AgentStatus = UnifiedAgentStatus
AgentPriority = UnifiedAgentPriority
Agent = UnifiedAgent
AgentDecision = UnifiedAgentDecision
AgentTask = UnifiedAgentTask
AgentCommunication = UnifiedAgentCommunication
AgentPerformanceMetric = UnifiedAgentPerformanceMetric
AgentResponse = UnifiedAgentResponse
AgentCreate = UnifiedAgentCreate
AgentUpdate = UnifiedAgentUpdate

# Export all models
__all__ = [
    # Enums
    "AgentType",
    "AgentStatus",
    "AgentPriority",
    "TaskStatus",
    "DecisionStatus",
    # SQLAlchemy Models
    "UnifiedAgent",
    "Agent",  # Alias
    "AgentDecision",
    "AgentTask",
    "AgentCommunication",
    "AgentPerformanceMetric",
    # Pydantic Models
    "AgentResponse",
    "AgentCreate",
    "AgentUpdate",
    "TaskResponse",
    "TaskCreate",
]
