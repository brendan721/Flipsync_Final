"""
Learning Data Database Models for FlipSync Agentic System
Phase 3 Step 3: Learning Data Database Persistence

SQLAlchemy models for learning data persistence in PostgreSQL.
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class PolicyOptimizationHistory(Base):
    """Policy optimization history and strategy evolution."""

    __tablename__ = "policy_optimization_history"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String(255), nullable=False)
    agent_type = Column(String(50), nullable=False)
    optimization_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

    # Policy data
    current_policy = Column(JSONB, nullable=False)
    optimized_policy = Column(JSONB, nullable=False)
    optimization_objective = Column(String(100), nullable=False)
    optimization_algorithm = Column(String(100), nullable=False)

    # Performance metrics
    performance_metrics = Column(JSONB, nullable=False)
    improvement_score = Column(Numeric(10, 6), default=0.0)
    confidence_score = Column(Numeric(10, 6), default=0.0)

    # Learning parameters
    learning_rate = Column(Numeric(10, 6), default=0.01)
    iteration_count = Column(Integer, default=1)
    convergence_status = Column(String(50), default="in_progress")

    # Metadata
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "agent_id", "optimization_id", name="unique_agent_optimization"
        ),
    )


class PolicyStrategyEvolution(Base):
    """Policy strategy evolution tracking."""

    __tablename__ = "policy_strategy_evolution"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String(255), nullable=False)
    strategy_id = Column(
        UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True
    )

    # Strategy data
    strategy_name = Column(String(255), nullable=False)
    strategy_parameters = Column(JSONB, nullable=False)
    strategy_version = Column(Integer, default=1)

    # Performance tracking
    success_rate = Column(Numeric(10, 6), default=0.0)
    average_performance = Column(Numeric(10, 6), default=0.0)
    usage_count = Column(Integer, default=0)

    # Evolution metadata
    parent_strategy_id = Column(
        UUID(as_uuid=True), ForeignKey("policy_strategy_evolution.strategy_id")
    )
    evolution_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    parent_strategy = relationship("PolicyStrategyEvolution", remote_side=[strategy_id])

    __table_args__ = (
        UniqueConstraint(
            "agent_id",
            "strategy_name",
            "strategy_version",
            name="unique_agent_strategy",
        ),
    )


class LearningKnowledgeBase(Base):
    """Learning patterns and knowledge base (complementing vector store)."""

    __tablename__ = "learning_knowledge_base"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String(255), nullable=False)
    knowledge_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

    # Knowledge data
    knowledge_type = Column(String(100), nullable=False)
    knowledge_content = Column(JSONB, nullable=False)
    knowledge_source = Column(
        String(100), nullable=False
    )  # 'feedback', 'pattern', 'cross_agent'

    # Learning metrics
    confidence_score = Column(Numeric(10, 6), default=0.0)
    usage_frequency = Column(Integer, default=0)
    success_rate = Column(Numeric(10, 6), default=0.0)

    # Relationships
    related_asin = Column(String(50))
    related_context = Column(JSONB)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    last_accessed = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        UniqueConstraint("agent_id", "knowledge_id", name="unique_agent_knowledge"),
    )


class LearningFeedbackHistory(Base):
    """Learning feedback processing results."""

    __tablename__ = "learning_feedback_history"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String(255), nullable=False)
    feedback_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

    # Feedback data
    asin = Column(String(50), nullable=False)
    feedback_data = Column(JSONB, nullable=False)
    processing_result = Column(JSONB, nullable=False)

    # Learning outcomes
    patterns_discovered = Column(JSONB, default=lambda: [])
    knowledge_updated = Column(JSONB, default=lambda: [])
    performance_impact = Column(Numeric(10, 6), default=0.0)

    # Processing metadata
    processing_time_ms = Column(Integer, default=0)
    llm_used = Column(Boolean, default=False)
    vector_store_updated = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    processed_at = Column(DateTime(timezone=True), default=func.now())


class LearningPerformanceMetrics(Base):
    """Learning performance metrics over time."""

    __tablename__ = "learning_performance_metrics"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String(255), nullable=False)
    metric_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

    # Performance data
    metric_type = Column(
        String(100), nullable=False
    )  # 'decision_accuracy', 'learning_speed', 'adaptation_rate'
    metric_value = Column(Numeric(10, 6), nullable=False)
    baseline_value = Column(Numeric(10, 6), default=0.0)
    improvement_percentage = Column(Numeric(10, 6), default=0.0)

    # Context
    measurement_context = Column(JSONB)
    measurement_period = Column(String(50))  # 'daily', 'weekly', 'monthly'

    # Metadata
    measured_at = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())


class CrossAgentLearningInsights(Base):
    """Cross-agent learning insights and knowledge sharing."""

    __tablename__ = "cross_agent_learning_insights"

    id = Column(Integer, primary_key=True)
    insight_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

    # Source and target agents
    source_agent_id = Column(String(255), nullable=False)
    source_agent_type = Column(String(50), nullable=False)
    target_agents = Column(JSONB, nullable=False)  # Array of agent IDs

    # Insight data
    insight_type = Column(String(100), nullable=False)
    insight_content = Column(JSONB, nullable=False)
    insight_context = Column(JSONB)

    # Effectiveness tracking
    effectiveness_score = Column(Numeric(10, 6), default=0.0)
    adoption_rate = Column(Numeric(10, 6), default=0.0)
    impact_metrics = Column(JSONB, default=lambda: {})

    # Sharing metadata
    shared_at = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (UniqueConstraint("insight_id", name="unique_insight"),)


class CrossAgentCoordinationState(Base):
    """Cross-agent learning coordination state."""

    __tablename__ = "cross_agent_coordination_state"

    id = Column(Integer, primary_key=True)
    coordination_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

    # Coordination participants
    participating_agents = Column(JSONB, nullable=False)
    coordination_type = Column(
        String(100), nullable=False
    )  # 'knowledge_sharing', 'collective_learning', 'conflict_resolution'

    # Coordination data
    coordination_data = Column(JSONB, nullable=False)
    coordination_status = Column(
        String(50), default="active"
    )  # 'active', 'completed', 'failed'

    # Results
    coordination_results = Column(JSONB, default=lambda: {})
    success_metrics = Column(JSONB, default=lambda: {})

    # Metadata
    started_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())


class LearningConflictResolution(Base):
    """Learning conflict resolution for contradictory insights."""

    __tablename__ = "learning_conflict_resolution"

    id = Column(Integer, primary_key=True)
    conflict_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

    # Conflict participants
    conflicting_agents = Column(JSONB, nullable=False)
    conflict_type = Column(String(100), nullable=False)

    # Conflict data
    conflicting_insights = Column(JSONB, nullable=False)
    conflict_context = Column(JSONB)

    # Resolution
    resolution_strategy = Column(
        String(100)
    )  # 'majority_vote', 'performance_weighted', 'expert_agent', 'hybrid'
    resolution_result = Column(JSONB)
    resolution_confidence = Column(Numeric(10, 6), default=0.0)

    # Metadata
    detected_at = Column(DateTime(timezone=True), default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (UniqueConstraint("conflict_id", name="unique_conflict"),)
