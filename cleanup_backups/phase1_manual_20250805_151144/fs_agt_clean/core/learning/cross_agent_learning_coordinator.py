#!/usr/bin/env python3
"""
Cross-Agent Learning Coordinator
===============================

Implements sophisticated cross-agent learning coordination that enables agents
to share knowledge, learn from each other's decisions, and evolve collective
intelligence across the FlipSync agentic system.

Key Features:
- Knowledge sharing protocols between agents
- Learning insight distribution mechanisms
- Collective intelligence evolution
- Cross-agent decision outcome analysis
- Distributed learning optimization

Technical Requirements:
- Production database integration (flipsync_agentic_test)
- OpenAI API integration for knowledge synthesis
- Real-time learning coordination
- Measurable cross-agent learning improvements
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LearningInsightType(Enum):
    """Types of learning insights that can be shared between agents."""

    DECISION_PATTERN = "decision_pattern"
    OPTIMIZATION_STRATEGY = "optimization_strategy"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    ERROR_PREVENTION = "error_prevention"
    COORDINATION_ENHANCEMENT = "coordination_enhancement"


@dataclass
class LearningInsight:
    """Represents a learning insight that can be shared between agents."""

    insight_id: str
    source_agent_id: str
    source_agent_type: str
    insight_type: LearningInsightType
    content: Dict[str, Any]
    confidence_score: float
    applicability_score: float
    created_at: str
    metadata: Dict[str, Any]


@dataclass
class CrossAgentLearningMetrics:
    """Metrics for measuring cross-agent learning effectiveness."""

    total_insights_shared: int
    insights_applied: int
    performance_improvements: List[Dict[str, Any]]
    knowledge_transfer_rate: float
    collective_intelligence_score: float
    coordination_efficiency: float


class CrossAgentLearningCoordinator:
    """
    Coordinates learning and knowledge sharing across multiple agents.

    This system enables agents to:
    1. Share learning insights with other agents
    2. Receive and evaluate insights from other agents
    3. Apply relevant insights to improve their own decision-making
    4. Contribute to collective intelligence evolution
    """

    def __init__(
        self,
        coordinator_id: str,
        database,
        llm_service,
        vector_store=None,
    ):
        """Initialize the Cross-Agent Learning Coordinator."""
        self.coordinator_id = coordinator_id
        self.database = database
        self.llm_service = llm_service
        self.vector_store = vector_store

        # Agent registry and learning state
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        self.learning_insights: Dict[str, LearningInsight] = {}
        self.agent_learning_profiles: Dict[str, Dict[str, Any]] = {}

        # Learning coordination metrics
        self.metrics = CrossAgentLearningMetrics(
            total_insights_shared=0,
            insights_applied=0,
            performance_improvements=[],
            knowledge_transfer_rate=0.0,
            collective_intelligence_score=0.0,
            coordination_efficiency=0.0,
        )

        # Learning coordination settings
        self.insight_sharing_enabled = True
        self.min_confidence_threshold = 0.7
        self.max_insights_per_agent = 100
        self.learning_sync_interval = 300  # 5 minutes

        logger.info(f"Initialized CrossAgentLearningCoordinator: {coordinator_id}")

    async def initialize(self) -> bool:
        """Initialize the cross-agent learning coordinator."""
        try:
            # Create database tables for cross-agent learning
            await self._create_learning_tables()

            # Initialize learning coordination state
            await self._initialize_learning_state()

            logger.info(
                f"✅ CrossAgentLearningCoordinator initialized: {self.coordinator_id}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize CrossAgentLearningCoordinator: {e}")
            return False

    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        learning_capabilities: List[str],
        specializations: List[str],
    ) -> bool:
        """Register an agent for cross-agent learning coordination."""
        try:
            agent_info = {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "learning_capabilities": learning_capabilities,
                "specializations": specializations,
                "registered_at": datetime.now(timezone.utc),
                "learning_score": 0.0,
                "insights_shared": 0,
                "insights_received": 0,
                "insights_applied": 0,
            }

            self.registered_agents[agent_id] = agent_info

            # Initialize learning profile for the agent
            self.agent_learning_profiles[agent_id] = {
                "strengths": specializations,
                "learning_patterns": [],
                "preferred_insight_types": [],
                "collaboration_history": {},
                "performance_trends": [],
            }

            # Store in database
            await self._store_agent_registration(agent_info)

            logger.info(
                f"✅ Agent registered for cross-learning: {agent_id} ({agent_type})"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to register agent {agent_id}: {e}")
            return False

    async def share_learning_insight(
        self,
        source_agent_id: str,
        insight_type: LearningInsightType,
        content: Dict[str, Any],
        confidence_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Share a learning insight from one agent to the coordination system."""
        try:
            if source_agent_id not in self.registered_agents:
                raise ValueError(f"Agent {source_agent_id} not registered")

            if confidence_score < self.min_confidence_threshold:
                logger.warning(
                    f"Insight confidence {confidence_score} below threshold {self.min_confidence_threshold}"
                )
                return None

            # Generate proper UUID for insight ID
            import uuid

            insight_id = str(uuid.uuid4())

            # Calculate applicability score using LLM
            applicability_score = await self._calculate_applicability_score(
                content, insight_type, source_agent_id
            )

            # Create learning insight
            insight = LearningInsight(
                insight_id=insight_id,
                source_agent_id=source_agent_id,
                source_agent_type=self.registered_agents[source_agent_id]["agent_type"],
                insight_type=insight_type,
                content=content,
                confidence_score=confidence_score,
                applicability_score=applicability_score,
                created_at=datetime.now(timezone.utc),
                metadata=metadata or {},
            )

            # Store insight
            self.learning_insights[insight_id] = insight
            await self._store_learning_insight(insight)

            # Update metrics
            self.metrics.total_insights_shared += 1
            self.registered_agents[source_agent_id]["insights_shared"] += 1

            # Distribute insight to relevant agents
            await self._distribute_insight_to_agents(insight)

            logger.info(
                f"✅ Learning insight shared: {insight_id} from {source_agent_id}"
            )
            return insight_id

        except Exception as e:
            logger.error(
                f"❌ Failed to share learning insight from {source_agent_id}: {e}"
            )
            return None

    async def get_relevant_insights(
        self,
        agent_id: str,
        insight_types: Optional[List[LearningInsightType]] = None,
        limit: int = 10,
    ) -> List[LearningInsight]:
        """Get learning insights relevant to a specific agent."""
        try:
            if agent_id not in self.registered_agents:
                raise ValueError(f"Agent {agent_id} not registered")

            # Filter insights based on relevance
            relevant_insights = []
            agent_profile = self.agent_learning_profiles[agent_id]

            for insight in self.learning_insights.values():
                # Skip insights from the same agent
                if insight.source_agent_id == agent_id:
                    continue

                # Filter by insight type if specified
                if insight_types and insight.insight_type not in insight_types:
                    continue

                # Calculate relevance score
                relevance_score = await self._calculate_insight_relevance(
                    insight, agent_id, agent_profile
                )

                if relevance_score > 0.5:  # Relevance threshold
                    relevant_insights.append((insight, relevance_score))

            # Sort by relevance and return top insights
            relevant_insights.sort(key=lambda x: x[1], reverse=True)
            return [insight for insight, _ in relevant_insights[:limit]]

        except Exception as e:
            logger.error(f"❌ Failed to get relevant insights for {agent_id}: {e}")
            return []

    async def apply_learning_insight(
        self, agent_id: str, insight_id: str, application_result: Dict[str, Any]
    ) -> bool:
        """Record that an agent has applied a learning insight."""
        try:
            if agent_id not in self.registered_agents:
                raise ValueError(f"Agent {agent_id} not registered")

            if insight_id not in self.learning_insights:
                raise ValueError(f"Insight {insight_id} not found")

            # Record application
            application_record = {
                "agent_id": agent_id,
                "insight_id": insight_id,
                "applied_at": datetime.now(timezone.utc),
                "result": application_result,
            }

            await self._store_insight_application(application_record)

            # Update metrics
            self.metrics.insights_applied += 1
            self.registered_agents[agent_id]["insights_applied"] += 1

            # Track performance improvement if provided
            if "performance_improvement" in application_result:
                self.metrics.performance_improvements.append(
                    {
                        "agent_id": agent_id,
                        "insight_id": insight_id,
                        "improvement": application_result["performance_improvement"],
                        "timestamp": application_record["applied_at"],
                    }
                )

            # Update agent learning profile
            await self._update_agent_learning_profile(
                agent_id, insight_id, application_result
            )

            logger.info(f"✅ Learning insight applied: {insight_id} by {agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to record insight application: {e}")
            return False

    async def get_coordination_metrics(self) -> CrossAgentLearningMetrics:
        """Get current cross-agent learning coordination metrics."""
        try:
            # Update dynamic metrics
            await self._update_coordination_metrics()
            return self.metrics

        except Exception as e:
            logger.error(f"❌ Failed to get coordination metrics: {e}")
            return self.metrics

    async def _create_learning_tables(self):
        """Create database tables for cross-agent learning coordination."""
        try:
            from sqlalchemy import text

            async with self.database.get_session() as session:
                # Create tables using raw SQL with proper text() wrapper
                await session.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS cross_agent_learning_insights (
                        insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        source_agent_id VARCHAR NOT NULL,
                        source_agent_type VARCHAR NOT NULL,
                        insight_type VARCHAR NOT NULL,
                        content JSONB NOT NULL,
                        confidence_score FLOAT NOT NULL,
                        applicability_score FLOAT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        metadata JSONB
                    )
                """
                    )
                )

                await session.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS cross_agent_registrations (
                        agent_id VARCHAR PRIMARY KEY,
                        agent_type VARCHAR NOT NULL,
                        learning_capabilities JSONB NOT NULL,
                        specializations JSONB NOT NULL,
                        registered_at TIMESTAMP NOT NULL,
                        learning_score FLOAT DEFAULT 0.0,
                        insights_shared INTEGER DEFAULT 0,
                        insights_received INTEGER DEFAULT 0,
                        insights_applied INTEGER DEFAULT 0
                    )
                """
                    )
                )

                await session.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS cross_agent_insight_applications (
                        id SERIAL PRIMARY KEY,
                        agent_id VARCHAR NOT NULL,
                        insight_id VARCHAR NOT NULL,
                        applied_at TIMESTAMP NOT NULL,
                        result JSONB NOT NULL
                    )
                """
                    )
                )

                await session.commit()

        except Exception as e:
            logger.error(f"Failed to create learning tables: {e}")
            raise

    async def _initialize_learning_state(self):
        """Initialize learning coordination state from database."""
        try:
            from sqlalchemy import text

            # Load existing agent registrations
            async with self.database.get_session() as session:
                result = await session.execute(
                    text("SELECT * FROM cross_agent_registrations")
                )
                registrations = result.fetchall()

                for reg in registrations:
                    self.registered_agents[reg.agent_id] = {
                        "agent_id": reg.agent_id,
                        "agent_type": reg.agent_type,
                        "learning_capabilities": reg.learning_capabilities,
                        "specializations": reg.specializations,
                        "registered_at": reg.registered_at,
                        "learning_score": reg.learning_score,
                        "insights_shared": reg.insights_shared,
                        "insights_received": reg.insights_received,
                        "insights_applied": reg.insights_applied,
                    }

                # Load recent learning insights
                result = await session.execute(
                    text(
                        """
                    SELECT * FROM cross_agent_learning_insights
                    ORDER BY created_at DESC LIMIT 1000
                """
                    )
                )
                insights = result.fetchall()

                for insight_row in insights:
                    insight = LearningInsight(
                        insight_id=insight_row.insight_id,
                        source_agent_id=insight_row.source_agent_id,
                        source_agent_type=insight_row.source_agent_type,
                        insight_type=LearningInsightType(insight_row.insight_type),
                        content=insight_row.content,
                        confidence_score=insight_row.confidence_score,
                        applicability_score=insight_row.applicability_score,
                        created_at=insight_row.created_at,
                        metadata=insight_row.metadata or {},
                    )
                    self.learning_insights[insight.insight_id] = insight

        except Exception as e:
            logger.warning(f"Failed to initialize learning state: {e}")

    async def _calculate_applicability_score(
        self,
        content: Dict[str, Any],
        insight_type: LearningInsightType,
        source_agent_id: str,
    ) -> float:
        """Calculate how applicable an insight is across different agents."""
        try:
            # Use LLM to analyze insight applicability
            analysis_prompt = f"""
            Analyze the applicability of this learning insight across different agent types:
            
            Insight Type: {insight_type.value}
            Source Agent: {source_agent_id}
            Content: {json.dumps(content, indent=2)}
            
            Rate the applicability on a scale of 0.0 to 1.0 where:
            - 0.0-0.3: Highly specific, limited applicability
            - 0.4-0.6: Moderately applicable with adaptation
            - 0.7-1.0: Broadly applicable across agent types
            
            Return only a numeric score.
            """

            response = await self.llm_service.generate_response(
                prompt=analysis_prompt,
                system_prompt="You are an expert in multi-agent learning systems.",
                max_tokens=50,
            )

            # Extract numeric score
            score_text = response.content.strip()
            try:
                score = float(score_text)
                return max(0.0, min(1.0, score))  # Clamp to [0, 1]
            except ValueError:
                logger.warning(f"Invalid applicability score: {score_text}")
                return 0.5  # Default moderate applicability

        except Exception as e:
            logger.error(f"Failed to calculate applicability score: {e}")
            return 0.5  # Default moderate applicability

    async def _calculate_insight_relevance(
        self, insight: LearningInsight, agent_id: str, agent_profile: Dict[str, Any]
    ) -> float:
        """Calculate how relevant an insight is to a specific agent."""
        try:
            # Base relevance factors
            relevance_score = 0.0

            # Factor 1: Agent type compatibility
            agent_type = self.registered_agents[agent_id]["agent_type"]
            if insight.source_agent_type == agent_type:
                relevance_score += 0.3  # Same type agents have higher relevance
            else:
                relevance_score += 0.1  # Different types still have some relevance

            # Factor 2: Specialization overlap
            agent_specializations = set(agent_profile.get("strengths", []))
            insight_specializations = set(insight.metadata.get("specializations", []))
            overlap = len(agent_specializations.intersection(insight_specializations))
            if overlap > 0:
                relevance_score += min(0.4, overlap * 0.2)

            # Factor 3: Insight applicability score
            relevance_score += insight.applicability_score * 0.3

            # Factor 4: Historical application success
            historical_success = agent_profile.get("collaboration_history", {}).get(
                insight.source_agent_id, 0.5
            )
            relevance_score += historical_success * 0.2

            return min(1.0, relevance_score)

        except Exception as e:
            logger.error(f"Failed to calculate insight relevance: {e}")
            return 0.5

    async def _distribute_insight_to_agents(self, insight: LearningInsight):
        """Distribute a learning insight to relevant agents."""
        try:
            for agent_id in self.registered_agents:
                if agent_id == insight.source_agent_id:
                    continue  # Don't send insight back to source

                agent_profile = self.agent_learning_profiles.get(agent_id, {})
                relevance = await self._calculate_insight_relevance(
                    insight, agent_id, agent_profile
                )

                if relevance > 0.6:  # High relevance threshold for distribution
                    # Store insight distribution record
                    await self._store_insight_distribution(
                        insight.insight_id, agent_id, relevance
                    )
                    self.registered_agents[agent_id]["insights_received"] += 1

                    logger.debug(
                        f"Distributed insight {insight.insight_id} to {agent_id} (relevance: {relevance:.2f})"
                    )

        except Exception as e:
            logger.error(f"Failed to distribute insight: {e}")

    async def _update_agent_learning_profile(
        self, agent_id: str, insight_id: str, application_result: Dict[str, Any]
    ):
        """Update an agent's learning profile based on insight application."""
        try:
            profile = self.agent_learning_profiles[agent_id]
            insight = self.learning_insights[insight_id]

            # Update collaboration history
            source_agent = insight.source_agent_id
            if source_agent not in profile["collaboration_history"]:
                profile["collaboration_history"][source_agent] = 0.5

            # Adjust collaboration score based on application success
            success_score = application_result.get("success_score", 0.5)
            current_score = profile["collaboration_history"][source_agent]
            profile["collaboration_history"][source_agent] = (current_score * 0.8) + (
                success_score * 0.2
            )

            # Update preferred insight types
            if success_score > 0.7:
                insight_type = insight.insight_type.value
                if insight_type not in profile["preferred_insight_types"]:
                    profile["preferred_insight_types"].append(insight_type)

            # Update performance trends
            if "performance_improvement" in application_result:
                profile["performance_trends"].append(
                    {
                        "timestamp": datetime.now(timezone.utc),
                        "improvement": application_result["performance_improvement"],
                        "insight_type": insight.insight_type.value,
                    }
                )

                # Keep only recent trends (last 100)
                profile["performance_trends"] = profile["performance_trends"][-100:]

        except Exception as e:
            logger.error(f"Failed to update agent learning profile: {e}")

    async def _update_coordination_metrics(self):
        """Update dynamic coordination metrics."""
        try:
            if not self.registered_agents:
                return

            # Calculate knowledge transfer rate
            total_insights = self.metrics.total_insights_shared
            applied_insights = self.metrics.insights_applied
            self.metrics.knowledge_transfer_rate = (
                applied_insights / total_insights if total_insights > 0 else 0.0
            )

            # Calculate collective intelligence score
            agent_scores = [
                agent["learning_score"] for agent in self.registered_agents.values()
            ]
            self.metrics.collective_intelligence_score = (
                sum(agent_scores) / len(agent_scores) if agent_scores else 0.0
            )

            # Calculate coordination efficiency
            total_agents = len(self.registered_agents)
            active_collaborations = sum(
                1
                for agent in self.registered_agents.values()
                if agent["insights_shared"] > 0 and agent["insights_applied"] > 0
            )
            self.metrics.coordination_efficiency = (
                active_collaborations / total_agents if total_agents > 0 else 0.0
            )

        except Exception as e:
            logger.error(f"Failed to update coordination metrics: {e}")

    async def _store_agent_registration(self, agent_info: Dict[str, Any]):
        """Store agent registration in database."""
        try:
            from sqlalchemy import text

            async with self.database.get_session() as session:
                await session.execute(
                    text(
                        """
                    INSERT INTO cross_agent_registrations
                    (agent_id, agent_type, learning_capabilities, specializations,
                     registered_at, learning_score, insights_shared, insights_received, insights_applied)
                    VALUES (:agent_id, :agent_type, :learning_capabilities, :specializations,
                            :registered_at, :learning_score, :insights_shared, :insights_received, :insights_applied)
                    ON CONFLICT (agent_id) DO UPDATE SET
                        agent_type = EXCLUDED.agent_type,
                        learning_capabilities = EXCLUDED.learning_capabilities,
                        specializations = EXCLUDED.specializations,
                        registered_at = EXCLUDED.registered_at
                """
                    ),
                    {
                        "agent_id": agent_info["agent_id"],
                        "agent_type": agent_info["agent_type"],
                        "learning_capabilities": json.dumps(
                            agent_info["learning_capabilities"]
                        ),
                        "specializations": json.dumps(agent_info["specializations"]),
                        "registered_at": (
                            agent_info["registered_at"].replace(tzinfo=None)
                            if hasattr(agent_info["registered_at"], "replace")
                            else agent_info["registered_at"]
                        ),  # Remove timezone
                        "learning_score": agent_info["learning_score"],
                        "insights_shared": agent_info["insights_shared"],
                        "insights_received": agent_info["insights_received"],
                        "insights_applied": agent_info["insights_applied"],
                    },
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to store agent registration: {e}")
            raise

    async def _store_learning_insight(self, insight: LearningInsight):
        """Store learning insight in database."""
        try:
            from sqlalchemy import text

            async with self.database.get_session() as session:
                await session.execute(
                    text(
                        """
                    INSERT INTO cross_agent_learning_insights
                    (insight_id, source_agent_id, source_agent_type, insight_type,
                     insight_content, effectiveness_score, adoption_rate, created_at, insight_context, target_agents)
                    VALUES (:insight_id, :source_agent_id, :source_agent_type, :insight_type,
                            :insight_content, :effectiveness_score, :adoption_rate, :created_at, :insight_context, :target_agents)
                """
                    ),
                    {
                        "insight_id": insight.insight_id,
                        "source_agent_id": insight.source_agent_id,
                        "source_agent_type": insight.source_agent_type,
                        "insight_type": insight.insight_type.value,
                        "insight_content": json.dumps(insight.content),
                        "effectiveness_score": insight.confidence_score,
                        "adoption_rate": insight.applicability_score,
                        "created_at": (
                            insight.created_at.replace(tzinfo=None)
                            if hasattr(insight.created_at, "replace")
                            else insight.created_at
                        ),  # Remove timezone
                        "insight_context": json.dumps(insight.metadata),
                        "target_agents": json.dumps(
                            []
                        ),  # Empty array for now, will be populated during distribution
                    },
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to store learning insight: {e}")
            raise

    async def _store_insight_application(self, application_record: Dict[str, Any]):
        """Store insight application record in database."""
        try:
            from sqlalchemy import text

            async with self.database.get_session() as session:
                await session.execute(
                    text(
                        """
                    INSERT INTO cross_agent_insight_applications
                    (agent_id, insight_id, applied_at, result)
                    VALUES (:agent_id, :insight_id, :applied_at, :result)
                """
                    ),
                    {
                        "agent_id": application_record["agent_id"],
                        "insight_id": application_record["insight_id"],
                        "applied_at": (
                            application_record["applied_at"].replace(tzinfo=None)
                            if hasattr(application_record["applied_at"], "replace")
                            else application_record["applied_at"]
                        ),  # Remove timezone
                        "result": json.dumps(application_record["result"]),
                    },
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to store insight application: {e}")
            raise

    async def _store_insight_distribution(
        self, insight_id: str, agent_id: str, relevance: float
    ):
        """Store insight distribution record."""
        try:
            # For now, just log the distribution
            # In a full implementation, this would be stored in a separate table
            logger.debug(
                f"Insight {insight_id} distributed to {agent_id} with relevance {relevance:.2f}"
            )

        except Exception as e:
            logger.error(f"Failed to store insight distribution: {e}")
