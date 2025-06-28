"""
UnifiedAgent Repository
================

Repository pattern for agent-related database operations.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.database.base_repository import BaseRepository
from fs_agt_clean.database.models.unified_agent import (
    UnifiedAgentCommunication,
    UnifiedAgentDecision,
    UnifiedAgentPerformanceMetric,
    UnifiedAgentStatus,
    UnifiedAgentTask,
)


class UnifiedAgentRepository(BaseRepository):
    """Repository for agent-related database operations."""

    def __init__(self):
        # Initialize with UnifiedAgentStatus as the primary model
        super().__init__(model_class=UnifiedAgentStatus, table_name="agent_status")

    async def create_or_update_agent_status(
        self,
        session: AsyncSession,
        agent_id: str,
        agent_type: str,
        status: str,
        metrics: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> UnifiedAgentStatus:
        """Create or update agent status.

        Args:
            session: Database session
            agent_id: Unique identifier for the agent
            agent_type: Type of agent ('market', 'executive', etc.)
            status: Current status ('running', 'stopped', 'error', etc.)
            metrics: Optional performance metrics
            config: Optional agent configuration

        Returns:
            Created or updated agent status
        """
        # Check if agent status already exists
        existing_query = select(UnifiedAgentStatus).where(UnifiedAgentStatus.agent_id == agent_id)
        result = await session.execute(existing_query)
        existing_status = result.scalar_one_or_none()

        if existing_status:
            # Update existing status
            existing_status.status = status
            existing_status.agent_type = agent_type
            existing_status.metrics = metrics or existing_status.metrics
            existing_status.config = config or existing_status.config
            existing_status.last_heartbeat = datetime.now(timezone.utc)

            await session.commit()
            await session.refresh(existing_status)
            return existing_status
        else:
            # Create new status
            agent_status = UnifiedAgentStatus(
                agent_id=agent_id,
                agent_type=agent_type,
                status=status,
                metrics=metrics or {},
                config=config or {},
            )

            session.add(agent_status)
            await session.commit()
            await session.refresh(agent_status)
            return agent_status

    async def get_agent_status(
        self, session: AsyncSession, agent_id: str
    ) -> Optional[UnifiedAgentStatus]:
        """Get agent status by ID.

        Args:
            session: Database session
            agent_id: ID of the agent

        Returns:
            UnifiedAgent status if found, None otherwise
        """
        query = select(UnifiedAgentStatus).where(UnifiedAgentStatus.agent_id == agent_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_agent_statuses(
        self,
        session: AsyncSession,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[UnifiedAgentStatus]:
        """Get all agent statuses with optional filtering.

        Args:
            session: Database session
            agent_type: Optional filter by agent type
            status: Optional filter by status

        Returns:
            List of agent statuses
        """
        query = select(UnifiedAgentStatus).order_by(
            UnifiedAgentStatus.agent_type, UnifiedAgentStatus.agent_id
        )

        if agent_type:
            query = query.where(UnifiedAgentStatus.agent_type == agent_type)

        if status:
            query = query.where(UnifiedAgentStatus.status == status)

        result = await session.execute(query)
        return result.scalars().all()

    async def create_agent_decision(
        self,
        session: AsyncSession,
        agent_id: str,
        decision_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        rationale: Optional[str] = None,
    ) -> UnifiedAgentDecision:
        """Create a new agent decision.

        Args:
            session: Database session
            agent_id: ID of the agent making the decision
            decision_type: Type of decision ('pricing', 'inventory', etc.)
            parameters: Decision parameters
            confidence: Confidence level (0.0 to 1.0)
            rationale: Explanation for the decision

        Returns:
            Created agent decision
        """
        decision = UnifiedAgentDecision(
            agent_id=agent_id,
            decision_type=decision_type,
            parameters=parameters or {},
            confidence=confidence,
            rationale=rationale,
            status="pending",
        )

        session.add(decision)
        await session.commit()
        await session.refresh(decision)

        return decision

    async def get_pending_decisions(
        self,
        session: AsyncSession,
        agent_id: Optional[str] = None,
        decision_type: Optional[str] = None,
    ) -> List[UnifiedAgentDecision]:
        """Get pending agent decisions.

        Args:
            session: Database session
            agent_id: Optional filter by agent ID
            decision_type: Optional filter by decision type

        Returns:
            List of pending decisions
        """
        query = (
            select(UnifiedAgentDecision)
            .where(UnifiedAgentDecision.status == "pending")
            .order_by(desc(UnifiedAgentDecision.created_at))
        )

        if agent_id:
            query = query.where(UnifiedAgentDecision.agent_id == agent_id)

        if decision_type:
            query = query.where(UnifiedAgentDecision.decision_type == decision_type)

        result = await session.execute(query)
        return result.scalars().all()

    async def approve_decision(
        self, session: AsyncSession, decision_id: str, approved_by: str
    ) -> Optional[UnifiedAgentDecision]:
        """Approve an agent decision.

        Args:
            session: Database session
            decision_id: ID of the decision to approve
            approved_by: ID of the user approving the decision

        Returns:
            Updated decision if found, None otherwise
        """
        query = select(UnifiedAgentDecision).where(UnifiedAgentDecision.id == uuid.UUID(decision_id))
        result = await session.execute(query)
        decision = result.scalar_one_or_none()

        if decision:
            decision.status = "approved"
            decision.approved_at = datetime.now(timezone.utc)
            decision.approved_by = uuid.UUID(approved_by)

            await session.commit()
            await session.refresh(decision)

        return decision

    async def log_agent_decision(
        self,
        session: AsyncSession,
        agent_id: str,
        agent_type: str,
        decision_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        rationale: Optional[str] = None,
        requires_approval: bool = False,
    ) -> UnifiedAgentDecision:
        """Log an agent decision for tracking and audit purposes.

        Args:
            session: Database session
            agent_id: ID of the agent making the decision
            agent_type: Type of agent making the decision
            decision_type: Type of decision being made
            parameters: Decision parameters
            confidence: Confidence level (0.0 to 1.0)
            rationale: Explanation for the decision
            requires_approval: Whether the decision requires approval

        Returns:
            Created agent decision
        """
        decision = UnifiedAgentDecision(
            agent_id=agent_id,
            decision_type=decision_type,
            parameters=parameters or {},
            confidence=confidence,
            rationale=rationale,
            status="approved" if not requires_approval else "pending",
        )

        session.add(decision)
        await session.commit()
        await session.refresh(decision)

        return decision

    async def reject_decision(
        self, session: AsyncSession, decision_id: str, approved_by: str
    ) -> Optional[UnifiedAgentDecision]:
        """Reject an agent decision.

        Args:
            session: Database session
            decision_id: ID of the decision to reject
            approved_by: ID of the user rejecting the decision

        Returns:
            Updated decision if found, None otherwise
        """
        query = select(UnifiedAgentDecision).where(UnifiedAgentDecision.id == uuid.UUID(decision_id))
        result = await session.execute(query)
        decision = result.scalar_one_or_none()

        if decision:
            decision.status = "rejected"
            decision.approved_at = datetime.now(timezone.utc)
            decision.approved_by = uuid.UUID(approved_by)

            await session.commit()
            await session.refresh(decision)

        return decision

    async def record_performance_metric(
        self,
        session: AsyncSession,
        agent_id: str,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UnifiedAgentPerformanceMetric:
        """Record a performance metric for an agent.

        Args:
            session: Database session
            agent_id: ID of the agent
            metric_name: Name of the metric
            metric_value: Value of the metric
            metric_unit: Optional unit of measurement
            metadata: Optional additional metadata

        Returns:
            Created performance metric
        """
        metric = UnifiedAgentPerformanceMetric(
            agent_id=agent_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            extra_metadata=metadata or {},
        )

        session.add(metric)
        await session.commit()
        await session.refresh(metric)

        return metric

    async def get_agent_metrics(
        self,
        session: AsyncSession,
        agent_id: str,
        metric_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[UnifiedAgentPerformanceMetric]:
        """Get performance metrics for an agent.

        Args:
            session: Database session
            agent_id: ID of the agent
            metric_name: Optional filter by metric name
            limit: Maximum number of metrics to return

        Returns:
            List of performance metrics
        """
        query = (
            select(UnifiedAgentPerformanceMetric)
            .where(UnifiedAgentPerformanceMetric.agent_id == agent_id)
            .order_by(desc(UnifiedAgentPerformanceMetric.timestamp))
            .limit(limit)
        )

        if metric_name:
            query = query.where(UnifiedAgentPerformanceMetric.metric_name == metric_name)

        result = await session.execute(query)
        return result.scalars().all()

    async def create_agent_task(
        self,
        session: AsyncSession,
        agent_id: str,
        task_type: str,
        task_name: str,
        task_parameters: Optional[Dict[str, Any]] = None,
        priority: int = 5,
    ) -> UnifiedAgentTask:
        """Create a new agent task.

        Args:
            session: Database session
            agent_id: ID of the agent
            task_type: Type of task
            task_name: Name of the task
            task_parameters: Optional task parameters
            priority: Task priority (1-10, where 1 is highest)

        Returns:
            Created agent task
        """
        task = UnifiedAgentTask(
            agent_id=agent_id,
            task_type=task_type,
            task_name=task_name,
            task_parameters=task_parameters or {},
            priority=priority,
            status="queued",
        )

        session.add(task)
        await session.commit()
        await session.refresh(task)

        return task

    async def get_agent_tasks(
        self,
        session: AsyncSession,
        agent_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[UnifiedAgentTask]:
        """Get tasks for an agent.

        Args:
            session: Database session
            agent_id: ID of the agent
            status: Optional filter by status
            limit: Maximum number of tasks to return

        Returns:
            List of agent tasks
        """
        query = (
            select(UnifiedAgentTask)
            .where(UnifiedAgentTask.agent_id == agent_id)
            .order_by(UnifiedAgentTask.priority, desc(UnifiedAgentTask.created_at))
            .limit(limit)
        )

        if status:
            query = query.where(UnifiedAgentTask.status == status)

        result = await session.execute(query)
        return result.scalars().all()
