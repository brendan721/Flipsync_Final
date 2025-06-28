"""
Agent Database Models
====================

This module defines the database models for agent status, decisions, and monitoring.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .base import Base


class AgentStatus(Base):
    """Model for tracking agent status and health."""

    __tablename__ = "agent_status"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), unique=True, nullable=False)
    agent_type = Column(
        String(50), nullable=False
    )  # 'market', 'executive', 'content', 'logistics', 'analytics'
    status = Column(
        String(20), nullable=False
    )  # 'running', 'stopped', 'error', 'starting', 'stopping'
    last_heartbeat = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    metrics = Column(JSON, nullable=True)
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<AgentStatus(agent_id='{self.agent_id}', agent_type='{self.agent_type}', status='{self.status}')>"

    def to_dict(self):
        """Convert agent status to dictionary."""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "last_heartbeat": (
                self.last_heartbeat.isoformat() if self.last_heartbeat else None
            ),
            "metrics": self.metrics,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentDecision(Base):
    """Model for tracking agent decisions that require approval."""

    __tablename__ = "agent_decisions"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), nullable=False)
    decision_type = Column(
        String(50), nullable=False
    )  # 'pricing', 'inventory', 'listing', 'shipping', 'strategy'
    parameters = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    rationale = Column(Text, nullable=True)
    status = Column(
        String(20), default="pending"
    )  # 'pending', 'approved', 'rejected', 'executed', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    execution_result = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<AgentDecision(id={self.id}, agent_id='{self.agent_id}', decision_type='{self.decision_type}', status='{self.status}')>"

    def to_dict(self):
        """Convert agent decision to dictionary."""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "decision_type": self.decision_type,
            "parameters": self.parameters,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "execution_result": self.execution_result,
        }


class AgentPerformanceMetric(Base):
    """Model for tracking agent performance metrics over time."""

    __tablename__ = "agent_performance_metrics"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), nullable=False)
    metric_name = Column(
        String(100), nullable=False
    )  # 'response_time', 'success_rate', 'cpu_usage', 'memory_usage'
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # 'ms', 'percent', 'mb', 'count'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    extra_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<AgentPerformanceMetric(agent_id='{self.agent_id}', metric_name='{self.metric_name}', value={self.metric_value})>"

    def to_dict(self):
        """Convert agent performance metric to dictionary."""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_unit": self.metric_unit,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.extra_metadata,
        }


class AgentCommunication(Base):
    """Model for tracking inter-agent communication."""

    __tablename__ = "agent_communications"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_agent_id = Column(String(100), nullable=False)
    to_agent_id = Column(String(100), nullable=False)
    message_type = Column(
        String(50), nullable=False
    )  # 'request', 'response', 'notification', 'handoff'
    message_content = Column(JSON, nullable=False)
    priority = Column(String(10), default="normal")  # 'low', 'normal', 'high', 'urgent'
    status = Column(
        String(20), default="sent"
    )  # 'sent', 'delivered', 'processed', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    response_data = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<AgentCommunication(id={self.id}, from='{self.from_agent_id}', to='{self.to_agent_id}', type='{self.message_type}')>"

    def to_dict(self):
        """Convert agent communication to dictionary."""
        return {
            "id": str(self.id),
            "from_agent_id": self.from_agent_id,
            "to_agent_id": self.to_agent_id,
            "message_type": self.message_type,
            "message_content": self.message_content,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
            "response_data": self.response_data,
        }


class AgentTask(Base):
    """Model for tracking agent tasks and their execution."""

    __tablename__ = "agent_tasks"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), nullable=False)
    task_type = Column(
        String(50), nullable=False
    )  # 'analysis', 'optimization', 'monitoring', 'execution'
    task_name = Column(String(200), nullable=False)
    task_parameters = Column(JSON, nullable=True)
    status = Column(
        String(20), default="queued"
    )  # 'queued', 'running', 'completed', 'failed', 'cancelled'
    priority = Column(Integer, default=5)  # 1-10, where 1 is highest priority
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    def __repr__(self):
        return f"<AgentTask(id={self.id}, agent_id='{self.agent_id}', task_name='{self.task_name}', status='{self.status}')>"

    def to_dict(self):
        """Convert agent task to dictionary."""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "task_name": self.task_name,
            "task_parameters": self.task_parameters,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "result": self.result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }
