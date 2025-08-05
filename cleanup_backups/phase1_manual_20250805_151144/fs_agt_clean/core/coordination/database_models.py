"""
Database Models for Multi-Agent Coordination State Persistence

This module defines SQLAlchemy models for storing coordination state, workflow state,
and agent communication data in PostgreSQL for persistence across agent restarts.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from fs_agt_clean.core.coordination.decision.models import DecisionStatus, DecisionType

Base = declarative_base()


class CoordinationState(Base):
    """Stores multi-agent coordination state for persistence across restarts."""

    __tablename__ = "coordination_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coordinator_id = Column(String(255), nullable=False, index=True)
    coordination_type = Column(
        String(100), nullable=False
    )  # sequential, parallel, hierarchical, etc.
    task_id = Column(String(255), nullable=False, index=True)
    task_description = Column(Text, nullable=False)
    task_context = Column(JSON, nullable=False, default=dict)

    # Agent assignment and status
    assigned_agents = Column(JSON, nullable=False, default=list)  # List of agent IDs
    agent_capabilities = Column(
        JSON, nullable=False, default=dict
    )  # Agent capability mapping
    agent_status = Column(
        JSON, nullable=False, default=dict
    )  # Current status of each agent

    # Coordination progress
    coordination_status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, active, completed, failed
    current_step = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=1)
    step_results = Column(JSON, nullable=False, default=list)  # Results from each step

    # Timing and metrics
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    execution_time_ms = Column(Integer, nullable=True)

    # Coordination metadata
    coordination_metadata = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)

    # Relationships
    agent_communications = relationship(
        "AgentCommunication", back_populates="coordination_state"
    )
    workflow_states = relationship("WorkflowState", back_populates="coordination_state")

    __table_args__ = (
        UniqueConstraint("coordinator_id", "task_id", name="unique_coordinator_task"),
    )


class WorkflowState(Base):
    """Stores workflow execution state for persistence across restarts."""

    __tablename__ = "workflow_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(String(255), nullable=False, unique=True, index=True)
    workflow_type = Column(
        String(100), nullable=False
    )  # sales_optimization, market_sync, etc.
    workflow_name = Column(String(255), nullable=False)

    # Workflow configuration and context
    workflow_config = Column(JSON, nullable=False, default=dict)
    workflow_context = Column(JSON, nullable=False, default=dict)
    input_data = Column(JSON, nullable=False, default=dict)

    # Execution state
    current_step = Column(String(255), nullable=False, default="initialization")
    step_index = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=1)
    step_history = Column(
        JSON, nullable=False, default=list
    )  # History of completed steps
    step_results = Column(JSON, nullable=False, default=dict)  # Results from each step

    # Workflow status
    status = Column(
        String(50), nullable=False, default="pending"
    )  # pending, running, completed, failed, paused
    progress_percentage = Column(Float, nullable=False, default=0.0)

    # Agent involvement
    participating_agents = Column(
        JSON, nullable=False, default=list
    )  # List of agent IDs
    current_agent = Column(String(255), nullable=True)  # Currently executing agent
    agent_handoffs = Column(
        JSON, nullable=False, default=list
    )  # History of agent handoffs

    # Timing and performance
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    execution_time_ms = Column(Integer, nullable=True)

    # Results and metadata
    final_result = Column(JSON, nullable=True)
    workflow_metadata = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)

    # Foreign keys
    coordination_state_id = Column(
        UUID(as_uuid=True), ForeignKey("coordination_states.id"), nullable=True
    )

    # Relationships
    coordination_state = relationship(
        "CoordinationState", back_populates="workflow_states"
    )
    agent_communications = relationship(
        "AgentCommunication", back_populates="workflow_state"
    )


class AgentCommunication(Base):
    """Stores agent-to-agent communication for coordination persistence."""

    __tablename__ = "coordination_communications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    communication_id = Column(String(255), nullable=False, unique=True, index=True)

    # Communication participants
    sender_agent_id = Column(String(255), nullable=False, index=True)
    receiver_agent_id = Column(String(255), nullable=False, index=True)
    communication_type = Column(
        String(100), nullable=False
    )  # task_assignment, result_sharing, coordination, etc.

    # Message content
    message_content = Column(JSON, nullable=False, default=dict)
    message_priority = Column(
        String(20), nullable=False, default="normal"
    )  # low, normal, high, urgent

    # Communication context
    context_type = Column(
        String(100), nullable=True
    )  # workflow, coordination, decision, etc.
    context_id = Column(
        String(255), nullable=True
    )  # ID of related workflow/coordination/decision

    # Status and timing
    status = Column(
        String(50), nullable=False, default="sent"
    )  # sent, delivered, acknowledged, processed
    sent_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Response and results
    response_data = Column(JSON, nullable=True)
    processing_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Foreign keys
    coordination_state_id = Column(
        UUID(as_uuid=True), ForeignKey("coordination_states.id"), nullable=True
    )
    workflow_state_id = Column(
        UUID(as_uuid=True), ForeignKey("workflow_states.id"), nullable=True
    )

    # Relationships
    coordination_state = relationship(
        "CoordinationState", back_populates="agent_communications"
    )
    workflow_state = relationship(
        "WorkflowState", back_populates="agent_communications"
    )


class DistributedDecisionState(Base):
    """Stores distributed decision state for persistence across restarts."""

    __tablename__ = "distributed_decision_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id = Column(String(255), nullable=False, unique=True, index=True)
    decision_type = Column(Enum(DecisionType), nullable=False)
    decision_description = Column(Text, nullable=False)

    # Decision context and requirements
    decision_context = Column(JSON, nullable=False, default=dict)
    participating_agents = Column(
        JSON, nullable=False, default=list
    )  # List of agent IDs
    required_consensus = Column(Float, nullable=False, default=0.7)
    deadline = Column(DateTime(timezone=True), nullable=True)

    # Decision status and progress
    status = Column(
        Enum(DecisionStatus), nullable=False, default=DecisionStatus.PENDING
    )
    consensus_reached = Column(Boolean, nullable=False, default=False)
    consensus_score = Column(Float, nullable=True)

    # Agent inputs and voting
    agent_inputs = Column(
        JSON, nullable=False, default=list
    )  # List of agent decision inputs
    voting_results = Column(JSON, nullable=False, default=dict)
    final_decision = Column(JSON, nullable=True)

    # Timing and metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Results and quality metrics
    decision_quality_score = Column(Float, nullable=True)
    implementation_status = Column(String(50), nullable=False, default="pending")
    implementation_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)


class AgentCapabilityRegistry(Base):
    """Registry of agent capabilities for coordination and task assignment."""

    __tablename__ = "agent_capability_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(255), nullable=False, index=True)
    agent_type = Column(
        String(100), nullable=False
    )  # market, executive, content, logistics

    # Capability information
    capability_name = Column(String(255), nullable=False)
    capability_type = Column(
        String(100), nullable=False
    )  # analysis, optimization, coordination, etc.
    capability_description = Column(Text, nullable=False)

    # Capability metrics
    proficiency_score = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    success_rate = Column(Float, nullable=False, default=0.0)  # Historical success rate
    average_execution_time_ms = Column(Integer, nullable=False, default=0)
    total_executions = Column(Integer, nullable=False, default=0)

    # Capability status
    is_active = Column(Boolean, nullable=False, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Capability metadata
    capability_metadata = Column(JSON, nullable=False, default=dict)

    # Timing
    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("agent_id", "capability_name", name="unique_agent_capability"),
    )
