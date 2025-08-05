"""
Cross-Agent Learning Coordinator for FlipSync Agentic System

This module implements database-backed knowledge sharing and coordination between agents,
enabling collective intelligence and cross-agent learning through the coordination layer.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from fs_agt_clean.database.models.unified_agent import UnifiedAgentCommunication
from fs_agt_clean.core.coordination.database_multi_agent_coordinator import (
    DatabaseMultiAgentCoordinator,
)
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class CrossAgentLearningCoordinator:
    """Coordinates learning and knowledge sharing between agents via database.

    This class implements:
    - Cross-agent learning data sharing via database
    - Knowledge sharing protocols between agents
    - Learning conflict resolution mechanisms
    - Collective intelligence improvement tracking
    """

    def __init__(
        self,
        coordinator_id: str,
        database: Database,
        multi_agent_coordinator: DatabaseMultiAgentCoordinator,
    ):
        """Initialize the cross-agent learning coordinator.

        Args:
            coordinator_id: Unique identifier for this learning coordinator
            database: Database instance for persistence
            multi_agent_coordinator: Multi-agent coordinator for workflow integration
        """
        self.coordinator_id = coordinator_id
        self.database = database
        self.multi_agent_coordinator = multi_agent_coordinator
        self.learning_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Initialized CrossAgentLearningCoordinator {coordinator_id}")

    async def initialize(self) -> bool:
        """Initialize the cross-agent learning coordinator.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Load existing learning coordination state
            await self._load_learning_coordination_state()

            logger.info(
                f"✅ CrossAgentLearningCoordinator initialized for {self.coordinator_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CrossAgentLearningCoordinator: {e}")
            return False

    async def share_learning_insight(
        self,
        source_agent_id: str,
        target_agent_ids: List[str],
        insight_type: str,
        insight_data: Dict[str, Any],
        priority: str = "normal",
    ) -> bool:
        """Share a learning insight from one agent to others via database.

        Args:
            source_agent_id: Agent sharing the insight
            target_agent_ids: Agents to receive the insight
            insight_type: Type of insight (strategy, pattern, optimization, etc.)
            insight_data: The actual insight data to share
            priority: Priority level (low, normal, high, urgent)

        Returns:
            True if sharing was successful, False otherwise
        """
        try:
            insight_id = f"learning_insight_{uuid.uuid4()}"

            # Store learning insight communication in database
            async with self.database.get_session() as session:
                for target_agent_id in target_agent_ids:
                    communication_record = UnifiedAgentCommunication(
                        agent_id=source_agent_id,
                        target_agent_id=target_agent_id,
                        message_type="learning_insight_sharing",
                        message_content=f"Insight: {insight_type} - {insight_data}",
                        priority=(
                            5
                            if priority == "normal"
                            else (8 if priority == "high" else 3)
                        ),
                        requires_response=False,
                        response_received=False,
                    )

                    session.add(communication_record)

                await session.commit()

            # Update learning cache
            if source_agent_id not in self.learning_cache:
                self.learning_cache[source_agent_id] = {}

            self.learning_cache[source_agent_id][insight_type] = {
                "data": insight_data,
                "shared_to": target_agent_ids,
                "shared_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Shared learning insight {insight_type} from {source_agent_id} to {len(target_agent_ids)} agents"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to share learning insight: {e}")
            return False

    async def get_learning_insights_for_agent(
        self, agent_id: str, insight_types: Optional[List[str]] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get learning insights available for a specific agent.

        Args:
            agent_id: Agent to get insights for
            insight_types: Optional filter by insight types
            limit: Maximum number of insights to return

        Returns:
            List of learning insights available for the agent
        """
        try:
            async with self.database.get_session() as session:
                query = (
                    select(UnifiedAgentCommunication)
                    .where(
                        UnifiedAgentCommunication.target_agent_id == agent_id,
                        UnifiedAgentCommunication.message_type
                        == "learning_insight_sharing",
                    )
                    .order_by(UnifiedAgentCommunication.created_at.desc())
                    .limit(limit)
                )

                result = await session.execute(query)
                communications = result.scalars().all()

                insights = []
                for comm in communications:
                    # Parse insight type from message content
                    message_content = comm.message_content
                    if "Insight:" in message_content:
                        parts = message_content.split(" - ", 1)
                        insight_type = parts[0].replace("Insight: ", "")
                        insight_data = parts[1] if len(parts) > 1 else ""
                    else:
                        insight_type = "general"
                        insight_data = message_content

                    # Filter by insight types if specified
                    if insight_types and insight_type not in insight_types:
                        continue

                    insights.append(
                        {
                            "communication_id": comm.id,
                            "source_agent": comm.agent_id,
                            "insight_type": insight_type,
                            "insight_data": insight_data,
                            "shared_at": comm.created_at.isoformat(),
                            "priority": comm.priority,
                            "status": "delivered" if comm.delivered_at else "sent",
                        }
                    )

                return insights

        except Exception as e:
            logger.error(f"Failed to get learning insights for agent {agent_id}: {e}")
            return []

    async def apply_learning_insight(self, agent_id: str, insight_id: str) -> bool:
        """Apply a learning insight to an agent.

        Args:
            agent_id: Agent that will apply the insight
            insight_id: ID of the insight to apply

        Returns:
            True if insight was successfully applied, False otherwise
        """
        try:
            async with self.database.get_session() as session:
                # Get the insight communication record
                result = await session.execute(
                    select(UnifiedAgentCommunication)
                    .where(UnifiedAgentCommunication.id == insight_id)
                    .where(UnifiedAgentCommunication.target_agent_id == agent_id)
                    .where(
                        UnifiedAgentCommunication.message_type
                        == "learning_insight_sharing"
                    )
                )

                insight_record = result.scalar_one_or_none()

                if not insight_record:
                    logger.warning(
                        f"Learning insight {insight_id} not found for agent {agent_id}"
                    )
                    return False

                # Update status to applied
                await session.execute(
                    update(UnifiedAgentCommunication)
                    .where(UnifiedAgentCommunication.id == insight_id)
                    .where(UnifiedAgentCommunication.target_agent_id == agent_id)
                    .values(
                        responded_at=datetime.now(timezone.utc),
                        response_content="Applied learning insight",
                        response_received=True,
                    )
                )

                await session.commit()

                logger.info(f"✅ Learning insight {insight_id} applied by {agent_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to apply learning insight {insight_id}: {e}")
            return False

    async def acknowledge_learning_insight(
        self, agent_id: str, communication_id: str, application_result: Dict[str, Any]
    ) -> bool:
        """Acknowledge that an agent has processed a learning insight.

        Args:
            agent_id: Agent acknowledging the insight
            communication_id: ID of the communication being acknowledged
            application_result: Result of applying the insight

        Returns:
            True if acknowledgment was successful, False otherwise
        """
        try:
            async with self.database.get_session() as session:
                await session.execute(
                    update(UnifiedAgentCommunication)
                    .where(
                        UnifiedAgentCommunication.id == communication_id,
                        UnifiedAgentCommunication.target_agent_id == agent_id,
                    )
                    .values(
                        responded_at=datetime.now(timezone.utc),
                        response_content=str(application_result),
                        response_received=True,
                    )
                )

                await session.commit()

                logger.debug(
                    f"Agent {agent_id} acknowledged learning insight {communication_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to acknowledge learning insight: {e}")
            return False

    async def resolve_learning_conflict(
        self,
        conflicting_agents: List[str],
        conflict_type: str,
        conflict_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve conflicts between agents' learned strategies.

        Args:
            conflicting_agents: Agents with conflicting strategies
            conflict_type: Type of conflict (strategy, optimization, pattern, etc.)
            conflict_data: Data about the conflicting strategies

        Returns:
            Resolution result with recommended strategy
        """
        try:
            # Create coordination task for conflict resolution
            from fs_agt_clean.core.coordination.advanced_multi_agent_coordinator import (
                CoordinationTask,
                CoordinationStrategy,
            )

            conflict_resolution_task = CoordinationTask(
                task_id=f"learning_conflict_{uuid.uuid4()}",
                task_type="learning_conflict_resolution",
                description=f"Resolve {conflict_type} conflict between agents",
                assigned_agents=conflicting_agents,
                required_capabilities=["conflict_resolution", "strategy_analysis"],
                coordination_strategy=CoordinationStrategy.CONSENSUS,
            )

            # Use multi-agent coordinator to resolve conflict
            resolution_result = await self.multi_agent_coordinator.coordinate_task(
                conflict_resolution_task, store_in_database=True
            )

            # Store conflict resolution in database
            await self._store_conflict_resolution(
                conflicting_agents=conflicting_agents,
                conflict_type=conflict_type,
                conflict_data=conflict_data,
                resolution_result=resolution_result,
            )

            logger.info(
                f"Resolved learning conflict {conflict_type} between {len(conflicting_agents)} agents"
            )
            return resolution_result

        except Exception as e:
            logger.error(f"Failed to resolve learning conflict: {e}")
            return {
                "success": False,
                "error": str(e),
                "conflict_type": conflict_type,
                "conflicting_agents": conflicting_agents,
            }

    async def get_collective_intelligence_metrics(self) -> Dict[str, Any]:
        """Get metrics on collective intelligence improvement over time.

        Returns:
            Metrics on cross-agent learning effectiveness
        """
        try:
            async with self.database.get_session() as session:
                # Get learning insight sharing statistics
                insight_sharing_result = await session.execute(
                    select(UnifiedAgentCommunication).where(
                        UnifiedAgentCommunication.message_type
                        == "learning_insight_sharing"
                    )
                )

                insights = insight_sharing_result.scalars().all()

                # Calculate metrics
                total_insights_shared = len(insights)
                acknowledged_insights = len(
                    [i for i in insights if i.response_received]
                )
                unique_agents_sharing = len(set(i.agent_id for i in insights))
                unique_agents_receiving = len(
                    set(i.target_agent_id for i in insights if i.target_agent_id)
                )

                acknowledgment_rate = (
                    (acknowledged_insights / total_insights_shared)
                    if total_insights_shared > 0
                    else 0
                )

                # Get insight types distribution
                insight_types = {}
                for insight in insights:
                    # Parse insight type from message content
                    message_content = insight.message_content
                    if "Insight:" in message_content:
                        insight_type = message_content.split(" - ", 1)[0].replace(
                            "Insight: ", ""
                        )
                    else:
                        insight_type = "general"
                    insight_types[insight_type] = insight_types.get(insight_type, 0) + 1

                return {
                    "total_insights_shared": total_insights_shared,
                    "acknowledged_insights": acknowledged_insights,
                    "acknowledgment_rate": acknowledgment_rate,
                    "unique_agents_sharing": unique_agents_sharing,
                    "unique_agents_receiving": unique_agents_receiving,
                    "insight_types_distribution": insight_types,
                    "collective_intelligence_score": acknowledgment_rate
                    * (unique_agents_sharing / 4.0),  # Normalized by 4 agents
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to get collective intelligence metrics: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    async def _load_learning_coordination_state(self):
        """Load existing learning coordination state from database."""
        try:
            # Load recent learning insights into cache
            async with self.database.get_session() as session:
                result = await session.execute(
                    select(UnifiedAgentCommunication)
                    .where(
                        UnifiedAgentCommunication.message_type
                        == "learning_insight_sharing"
                    )
                    .order_by(UnifiedAgentCommunication.created_at.desc())
                    .limit(100)
                )

                recent_insights = result.scalars().all()

                for insight in recent_insights:
                    source_agent = insight.agent_id
                    if source_agent not in self.learning_cache:
                        self.learning_cache[source_agent] = {}

                    # Parse insight type from message content
                    message_content = insight.message_content
                    if "Insight:" in message_content:
                        parts = message_content.split(" - ", 1)
                        insight_type = parts[0].replace("Insight: ", "")
                        insight_data = parts[1] if len(parts) > 1 else ""
                    else:
                        insight_type = "general"
                        insight_data = message_content

                    self.learning_cache[source_agent][insight_type] = {
                        "data": insight_data,
                        "shared_at": insight.created_at.isoformat(),
                    }

                logger.info(
                    f"Loaded {len(recent_insights)} recent learning insights into cache"
                )

        except Exception as e:
            logger.error(f"Failed to load learning coordination state: {e}")

    async def _store_conflict_resolution(
        self,
        conflicting_agents: List[str],
        conflict_type: str,
        conflict_data: Dict[str, Any],
        resolution_result: Dict[str, Any],
    ):
        """Store conflict resolution result in database."""
        try:
            async with self.database.get_session() as session:
                conflict_communication = UnifiedAgentCommunication(
                    agent_id=self.coordinator_id,
                    target_agent_id="all_agents",
                    message_type="learning_conflict_resolution",
                    message_content=f"Conflict Resolution: {conflict_type} - {conflict_data}",
                    priority=8,  # High priority for conflict resolution
                    requires_response=False,
                    response_received=False,
                )

                session.add(conflict_communication)
                await session.commit()

                logger.debug(f"Stored conflict resolution for {conflict_type}")

        except Exception as e:
            logger.error(f"Failed to store conflict resolution: {e}")
