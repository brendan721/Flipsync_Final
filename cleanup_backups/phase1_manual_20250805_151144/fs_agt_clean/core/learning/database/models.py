"""
Learning Data Database Models for FlipSync Agentic System
Phase 2 Cleanup: Learning Data Database Persistence

SQLAlchemy 2.0 models for learning data persistence in PostgreSQL.
Updated to use modern SQLAlchemy syntax and unified base.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fs_agt_clean.database.models.base import Base


class PolicyOptimizationHistory(Base):
    """Policy optimization history and strategy evolution."""

    __tablename__ = "policy_optimization_history"
    __table_args__ = (
        UniqueConstraint(
            "agent_id", "optimization_id", name="unique_agent_optimization"
        ),
        {"extend_existing": True},
    )

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Agent identification
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    optimization_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default=lambda: str(uuid.uuid4())
    )

    # Policy data
    current_policy: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    optimized_policy: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    optimization_objective: Mapped[str] = mapped_column(String(100), nullable=False)
    optimization_algorithm: Mapped[str] = mapped_column(String(100), nullable=False)

    # Performance metrics
    performance_metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    improvement_score: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6), default=0.0
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6), default=0.0
    )

    # Learning parameters
    learning_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), default=0.01)
    iteration_count: Mapped[int] = mapped_column(Integer, default=1)
    convergence_status: Mapped[str] = mapped_column(String(50), default="in_progress")

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class PolicyStrategyEvolution(Base):
    """Policy strategy evolution tracking."""

    __tablename__ = "policy_strategy_evolution"
    __table_args__ = (
        UniqueConstraint(
            "agent_id",
            "strategy_name",
            "strategy_version",
            name="unique_agent_strategy",
        ),
        {"extend_existing": True},
    )

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Agent identification
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, default=lambda: str(uuid.uuid4())
    )

    # Strategy data
    strategy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy_parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    strategy_version: Mapped[int] = mapped_column(Integer, default=1)

    # Performance tracking
    success_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), default=0.0)
    average_performance: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6), default=0.0
    )
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # Evolution metadata
    parent_strategy_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("policy_strategy_evolution.strategy_id"), nullable=True
    )
    evolution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    parent_strategy: Mapped[Optional["PolicyStrategyEvolution"]] = relationship(
        "PolicyStrategyEvolution", remote_side="PolicyStrategyEvolution.strategy_id"
    )


class LearningKnowledgeBase(Base):
    """Learning patterns and knowledge base (complementing vector store)."""

    __tablename__ = "learning_knowledge_base"
    __table_args__ = (
        UniqueConstraint("agent_id", "knowledge_id", name="unique_agent_knowledge"),
        {"extend_existing": True},
    )

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Agent identification
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    knowledge_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default=lambda: str(uuid.uuid4())
    )

    # Knowledge data
    knowledge_type: Mapped[str] = mapped_column(String(100), nullable=False)
    knowledge_content: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    knowledge_source: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # 'feedback', 'pattern', 'cross_agent'

    # Learning metrics
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6), default=0.0
    )
    usage_frequency: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), default=0.0)

    # Relationships
    related_asin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_accessed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LearningFeedbackHistory(Base):
    """Learning feedback processing results."""

    __tablename__ = "learning_feedback_history"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Agent identification
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    feedback_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default=lambda: str(uuid.uuid4())
    )

    # Feedback data
    asin: Mapped[str] = mapped_column(String(50), nullable=False)
    feedback_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    processing_result: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Learning outcomes
    patterns_discovered: Mapped[Optional[List[Any]]] = mapped_column(
        JSONB, default=lambda: []
    )
    knowledge_updated: Mapped[Optional[List[Any]]] = mapped_column(
        JSONB, default=lambda: []
    )
    performance_impact: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6), default=0.0
    )

    # Processing metadata
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False)
    vector_store_updated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LearningPerformanceMetrics(Base):
    """Learning performance metrics over time."""

    __tablename__ = "learning_performance_metrics"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Agent identification
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default=lambda: str(uuid.uuid4())
    )

    # Performance data
    metric_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # 'decision_accuracy', 'learning_speed', 'adaptation_rate'
    metric_value: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    baseline_value: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), default=0.0)
    improvement_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6), default=0.0
    )

    # Context
    measurement_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    measurement_period: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'daily', 'weekly', 'monthly'

    # Metadata
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CrossAgentLearningInsights(Base):
    """Cross-agent learning insights and knowledge sharing."""

    __tablename__ = "cross_agent_learning_insights"
    __table_args__ = (
        UniqueConstraint("insight_id", name="unique_insight"),
        {"extend_existing": True},
    )

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    insight_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default=lambda: str(uuid.uuid4())
    )

    # Source and target agents
    source_agent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_agents: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False
    )  # Array of agent IDs

    # Insight data
    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)
    insight_content: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    insight_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # Effectiveness tracking
    effectiveness_score: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6), default=0.0
    )
    adoption_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), default=0.0)
    impact_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, default=lambda: {}
    )

    # Sharing metadata
    shared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CrossAgentCoordinationState(Base):
    """Cross-agent learning coordination state."""

    __tablename__ = "cross_agent_coordination_state"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coordination_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default=lambda: str(uuid.uuid4())
    )

    # Coordination participants
    participating_agents: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    coordination_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # 'knowledge_sharing', 'collective_learning', 'conflict_resolution'

    # Coordination data
    coordination_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    coordination_status: Mapped[str] = mapped_column(
        String(50), default="active"
    )  # 'active', 'completed', 'failed'

    # Results
    coordination_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, default=lambda: {}
    )
    success_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, default=lambda: {}
    )

    # Metadata
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LearningConflictResolution(Base):
    """Learning conflict resolution for contradictory insights."""

    __tablename__ = "learning_conflict_resolution"
    __table_args__ = (
        UniqueConstraint("conflict_id", name="unique_conflict"),
        {"extend_existing": True},
    )

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conflict_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default=lambda: str(uuid.uuid4())
    )

    # Conflict participants
    conflicting_agents: Mapped[List[str]] = mapped_column(JSONB, nullable=False)
    conflict_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Conflict data
    conflicting_insights: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    conflict_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # Resolution
    resolution_strategy: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # 'majority_vote', 'performance_weighted', 'expert_agent', 'hybrid'
    resolution_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    resolution_confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6), default=0.0
    )

    # Metadata
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
