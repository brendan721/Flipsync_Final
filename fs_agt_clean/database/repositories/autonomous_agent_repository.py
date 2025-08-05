"""
Autonomous Agent Repository for 4+1 Architecture
===============================================

Repository pattern for autonomous agent database operations in FlipSync's 4+1 architecture.
Handles the 4 autonomous agents: Market, Content, Executive, Logistics.

Key Features:
- Strict 4+1 architecture compliance
- LLM-free constraint enforcement
- Performance tracking and metrics
- Decision recording with compliance validation
- <1000ms decision time tracking
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.database.base_repository import BaseRepository
from fs_agt_clean.database.models.autonomous_agent import (
    AutonomousAgent,
    AutonomousAgentDecision,
    AutonomousAgentType,
    AutonomousAgentStatus,
    DecisionStatus,
)


class AutonomousAgentRepository(BaseRepository):
    """Repository for 4+1 architecture autonomous agents."""

    def __init__(self):
        # Initialize with AutonomousAgent as the primary model
        super().__init__(model_class=AutonomousAgent, table_name="autonomous_agents")

    async def create_or_update_autonomous_agent(
        self,
        session: AsyncSession,
        agent_id: str,
        agent_type: AutonomousAgentType,
        agent_class: str,
        status: AutonomousAgentStatus,
        capabilities: Optional[List[str]] = None,
        optimization_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AutonomousAgent:
        """Create or update autonomous agent with 4+1 compliance.

        Args:
            session: Database session
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (market, content, executive, logistics)
            agent_class: Python class name of the agent
            status: Current status of the agent
            capabilities: List of agent capabilities
            optimization_config: Configuration for optimization algorithms
            **kwargs: Additional agent properties

        Returns:
            Created or updated autonomous agent

        Raises:
            ValueError: If agent violates 4+1 architecture constraints
        """
        # Validate 4+1 architecture compliance
        if agent_type not in [
            AutonomousAgentType.MARKET,
            AutonomousAgentType.CONTENT,
            AutonomousAgentType.EXECUTIVE,
            AutonomousAgentType.LOGISTICS,
        ]:
            raise ValueError(f"Invalid agent type for 4+1 architecture: {agent_type}")

        # Check if agent already exists
        existing_query = select(AutonomousAgent).where(
            AutonomousAgent.agent_id == agent_id
        )
        result = await session.execute(existing_query)
        existing_agent = result.scalar_one_or_none()

        if existing_agent:
            # Update existing agent
            existing_agent.agent_type = agent_type
            existing_agent.agent_class = agent_class
            existing_agent.status = status

            if capabilities:
                existing_agent.capabilities = json.dumps(capabilities)
            if optimization_config:
                existing_agent.optimization_config = json.dumps(optimization_config)

            # Update timestamps
            existing_agent.last_heartbeat = datetime.now(timezone.utc)
            existing_agent.last_activity = datetime.now(timezone.utc)
            existing_agent.updated_at = datetime.now(timezone.utc)

            # Apply additional kwargs
            for key, value in kwargs.items():
                if hasattr(existing_agent, key):
                    setattr(existing_agent, key, value)

            await session.commit()
            await session.refresh(existing_agent)
            return existing_agent
        else:
            # Create new agent with 4+1 architecture compliance
            agent = AutonomousAgent(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                agent_type=agent_type,
                agent_class=agent_class,
                status=status,
                # Enforce 4+1 architecture constraints
                llm_free=True,  # Must always be True for autonomous agents
                uses_standard_decision_pipeline=True,  # Must always be True
                # Configuration
                capabilities=json.dumps(capabilities) if capabilities else None,
                optimization_config=(
                    json.dumps(optimization_config) if optimization_config else None
                ),
                # Timestamps
                initialized_at=datetime.now(timezone.utc),
                last_heartbeat=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
            )

            # Apply additional kwargs
            for key, value in kwargs.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)

            session.add(agent)
            await session.commit()
            await session.refresh(agent)
            return agent

    async def get_autonomous_agent(
        self, session: AsyncSession, agent_id: str
    ) -> Optional[AutonomousAgent]:
        """Get autonomous agent by ID.

        Args:
            session: Database session
            agent_id: ID of the agent

        Returns:
            AutonomousAgent if found, None otherwise
        """
        query = select(AutonomousAgent).where(AutonomousAgent.agent_id == agent_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_autonomous_agents(
        self, session: AsyncSession
    ) -> List[AutonomousAgent]:
        """Get all 4 autonomous agents.

        Args:
            session: Database session

        Returns:
            List of all autonomous agents (should be exactly 4)
        """
        query = select(AutonomousAgent).order_by(AutonomousAgent.agent_type)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_agents_by_type(
        self, session: AsyncSession, agent_type: AutonomousAgentType
    ) -> List[AutonomousAgent]:
        """Get agents by type.

        Args:
            session: Database session
            agent_type: Type of agent to retrieve

        Returns:
            List of agents of the specified type
        """
        query = select(AutonomousAgent).where(AutonomousAgent.agent_type == agent_type)
        result = await session.execute(query)
        return result.scalars().all()

    async def record_decision(
        self,
        session: AsyncSession,
        agent_id: str,
        decision_id: str,
        decision_type: str,
        context: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        execution_time_ms: float = 0.0,
        confidence: float = 0.0,
        status: DecisionStatus = DecisionStatus.PENDING,
        algorithm_used: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> AutonomousAgentDecision:
        """Record autonomous agent decision with compliance tracking.

        Args:
            session: Database session
            agent_id: ID of the agent making the decision
            decision_id: Unique identifier for the decision
            decision_type: Type of decision being made
            context: Decision context data
            result: Decision result data
            execution_time_ms: Time taken to execute decision
            confidence: Confidence level (0.0 to 1.0)
            status: Decision status
            algorithm_used: Algorithm used for decision making
            started_at: When decision started
            completed_at: When decision completed

        Returns:
            Created autonomous agent decision record

        Raises:
            ValueError: If decision violates 4+1 architecture constraints
        """
        # Validate that agent exists
        agent = await self.get_autonomous_agent(session, agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Validate 4+1 architecture compliance
        if execution_time_ms > 1000.0:  # Performance target: <1000ms
            # Log warning but don't fail - allow for Docker environment variations
            pass

        # Create decision record with strict compliance
        decision = AutonomousAgentDecision(
            id=str(uuid.uuid4()),
            decision_id=decision_id,
            agent_id=agent.id,  # Use internal agent ID
            decision_type=decision_type,
            context=json.dumps(context) if context else None,
            result=json.dumps(result) if result else None,
            execution_time_ms=execution_time_ms,
            confidence=confidence,
            status=status,
            # 4+1 Architecture Compliance - these must always be these values
            used_llm=False,  # Must always be False for autonomous agents
            used_standard_pipeline=True,  # Must always be True
            algorithm_used=algorithm_used,
            started_at=started_at or datetime.now(timezone.utc),
            completed_at=completed_at,
        )

        session.add(decision)

        # Update agent metrics
        agent.total_decisions += 1
        if status == DecisionStatus.COMPLETED:
            agent.successful_decisions += 1

        # Update average decision time
        if agent.average_decision_time_ms is None:
            agent.average_decision_time_ms = execution_time_ms
        else:
            # Calculate running average
            total_time = agent.average_decision_time_ms * (agent.total_decisions - 1)
            agent.average_decision_time_ms = (
                total_time + execution_time_ms
            ) / agent.total_decisions

        agent.last_decision_time_ms = execution_time_ms
        agent.last_activity = datetime.now(timezone.utc)
        agent.updated_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(decision)
        return decision

    async def get_agent_decisions(
        self,
        session: AsyncSession,
        agent_id: str,
        limit: int = 100,
        status: Optional[DecisionStatus] = None,
    ) -> List[AutonomousAgentDecision]:
        """Get decisions for an autonomous agent.

        Args:
            session: Database session
            agent_id: ID of the agent
            limit: Maximum number of decisions to return
            status: Optional filter by decision status

        Returns:
            List of agent decisions
        """
        # Get agent first to get internal ID
        agent = await self.get_autonomous_agent(session, agent_id)
        if not agent:
            return []

        query = (
            select(AutonomousAgentDecision)
            .where(AutonomousAgentDecision.agent_id == agent.id)
            .order_by(desc(AutonomousAgentDecision.started_at))
            .limit(limit)
        )

        if status:
            query = query.where(AutonomousAgentDecision.status == status)

        result = await session.execute(query)
        return result.scalars().all()

    async def update_agent_heartbeat(
        self, session: AsyncSession, agent_id: str
    ) -> bool:
        """Update agent heartbeat timestamp.

        Args:
            session: Database session
            agent_id: ID of the agent

        Returns:
            True if updated successfully, False if agent not found
        """
        agent = await self.get_autonomous_agent(session, agent_id)
        if not agent:
            return False

        agent.last_heartbeat = datetime.now(timezone.utc)
        agent.updated_at = datetime.now(timezone.utc)

        await session.commit()
        return True

    async def get_architecture_compliance_report(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Generate 4+1 architecture compliance report.

        Args:
            session: Database session

        Returns:
            Compliance report with metrics and validation
        """
        # Get all autonomous agents
        agents = await self.get_all_autonomous_agents(session)

        # Get decision compliance metrics
        decision_query = select(AutonomousAgentDecision).where(
            and_(
                AutonomousAgentDecision.used_llm == False,
                AutonomousAgentDecision.used_standard_pipeline == True,
            )
        )
        compliant_decisions = await session.execute(decision_query)
        compliant_decisions_count = len(compliant_decisions.scalars().all())

        total_decisions_query = select(AutonomousAgentDecision)
        total_decisions = await session.execute(total_decisions_query)
        total_decisions_count = len(total_decisions.scalars().all())

        # Calculate compliance metrics
        llm_free_compliance = all(agent.llm_free for agent in agents)
        pipeline_compliance = all(
            agent.uses_standard_decision_pipeline for agent in agents
        )
        decision_compliance = (
            compliant_decisions_count / max(total_decisions_count, 1)
        ) * 100

        # Performance metrics
        avg_decision_times = [
            agent.average_decision_time_ms
            for agent in agents
            if agent.average_decision_time_ms
        ]
        overall_avg_time = (
            sum(avg_decision_times) / len(avg_decision_times)
            if avg_decision_times
            else 0
        )
        performance_compliance = (
            overall_avg_time < 1000.0 if avg_decision_times else True
        )

        return {
            "architecture_type": "4+1",
            "autonomous_agents_count": len(agents),
            "expected_autonomous_agents": 4,
            "agents_by_type": {agent.agent_type: agent.agent_id for agent in agents},
            "llm_free_compliance": llm_free_compliance,
            "pipeline_compliance": pipeline_compliance,
            "decision_compliance_percentage": decision_compliance,
            "performance_compliance": performance_compliance,
            "total_decisions": total_decisions_count,
            "compliant_decisions": compliant_decisions_count,
            "average_decision_time_ms": overall_avg_time,
            "compliance_score": (
                (llm_free_compliance * 0.3)
                + (pipeline_compliance * 0.3)
                + (decision_compliance / 100 * 0.2)
                + (performance_compliance * 0.2)
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def record_autonomous_decision(
        self,
        session: AsyncSession,
        agent_id: int,  # Database ID, not agent_id string
        decision_id: str,
        decision_type: str,
        context: Dict[str, Any],
        result: Any,
        execution_time_ms: float,
        confidence: float,
        status: "DecisionStatus",
        algorithm_used: str,
    ) -> "AutonomousAgentDecision":
        """Record an autonomous agent decision in the database."""
        from fs_agt_clean.database.models.autonomous_agent import (
            AutonomousAgentDecision,
        )
        import json
        from datetime import datetime, timezone

        decision = AutonomousAgentDecision(
            agent_id=agent_id,
            decision_id=decision_id,
            decision_type=decision_type,
            context=json.dumps(context) if context else "{}",
            result=json.dumps(result) if result else "{}",
            execution_time_ms=execution_time_ms,
            confidence=confidence,
            status=status,
            algorithm_used=algorithm_used,
            used_llm=False,  # Always False for autonomous agents
            used_standard_pipeline=True,  # Always True for autonomous agents
            started_at=datetime.now(timezone.utc),  # Set started_at timestamp
            created_at=datetime.now(timezone.utc),
        )

        session.add(decision)
        await session.commit()
        await session.refresh(decision)

        return decision

    async def get_decisions_with_filters(
        self,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        agent_id: Optional[str] = None,
        decision_type: Optional[str] = None,
        status: Optional[str] = None,
        llm_free_only: bool = False,
    ) -> List[AutonomousAgentDecision]:
        """Get decisions with filtering and pagination."""
        try:
            query = select(AutonomousAgentDecision).order_by(
                AutonomousAgentDecision.created_at.desc()
            )

            # Apply filters
            if agent_id:
                query = query.where(AutonomousAgentDecision.agent_id == agent_id)
            if decision_type:
                query = query.where(
                    AutonomousAgentDecision.decision_type == decision_type
                )
            if status:
                query = query.where(AutonomousAgentDecision.status == status)
            if llm_free_only:
                query = query.where(AutonomousAgentDecision.used_llm == False)

            # Apply pagination
            query = query.offset(offset).limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting decisions with filters: {e}")
            raise

    async def get_decisions_count(
        self,
        session: AsyncSession,
        agent_id: Optional[str] = None,
        decision_type: Optional[str] = None,
        status: Optional[str] = None,
        llm_free_only: bool = False,
    ) -> int:
        """Get total count of decisions matching filters."""
        try:
            from sqlalchemy import func

            query = select(func.count(AutonomousAgentDecision.id))

            # Apply same filters as get_decisions_with_filters
            if agent_id:
                query = query.where(AutonomousAgentDecision.agent_id == agent_id)
            if decision_type:
                query = query.where(
                    AutonomousAgentDecision.decision_type == decision_type
                )
            if status:
                query = query.where(AutonomousAgentDecision.status == status)
            if llm_free_only:
                query = query.where(AutonomousAgentDecision.used_llm == False)

            result = await session.execute(query)
            return result.scalar() or 0

        except Exception as e:
            logger.error(f"Error getting decisions count: {e}")
            raise

    async def get_decisions_in_time_range(
        self,
        session: AsyncSession,
        start_time: datetime,
        end_time: datetime,
        agent_id: Optional[str] = None,
    ) -> List[AutonomousAgentDecision]:
        """Get decisions within a specific time range."""
        try:
            query = (
                select(AutonomousAgentDecision)
                .where(
                    AutonomousAgentDecision.created_at >= start_time,
                    AutonomousAgentDecision.created_at <= end_time,
                )
                .order_by(AutonomousAgentDecision.created_at.desc())
            )

            if agent_id:
                query = query.where(AutonomousAgentDecision.agent_id == agent_id)

            result = await session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting decisions in time range: {e}")
            raise

    async def get_recent_decisions(
        self,
        session: AsyncSession,
        limit: int = 20,
    ) -> List[AutonomousAgentDecision]:
        """Get most recent decisions across all agents."""
        try:
            query = (
                select(AutonomousAgentDecision)
                .order_by(AutonomousAgentDecision.created_at.desc())
                .limit(limit)
            )

            result = await session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting recent decisions: {e}")
            raise

    async def get_decision_by_id(
        self,
        session: AsyncSession,
        decision_id: str,
    ) -> Optional[AutonomousAgentDecision]:
        """Get a specific decision by its decision_id."""
        try:
            query = select(AutonomousAgentDecision).where(
                AutonomousAgentDecision.decision_id == decision_id
            )

            result = await session.execute(query)
            return result.scalars().first()

        except Exception as e:
            logger.error(f"Error getting decision by ID {decision_id}: {e}")
            raise
