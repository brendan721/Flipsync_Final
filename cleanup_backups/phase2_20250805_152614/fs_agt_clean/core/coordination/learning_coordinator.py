"""
Cross-Agent Learning Coordinator for Phase 3 Learning System Integration
=========================================================================

This module coordinates learning between multiple agents, enabling them to share
insights, learn from each other's decisions, and improve collective intelligence.

Features:
- Cross-agent insight sharing
- Collective learning coordination
- Learning performance aggregation
- Multi-agent learning optimization
- Knowledge transfer between agents
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class AgentLearningProfile:
    """Profile of an agent's learning capabilities and performance."""
    agent_id: str
    agent_type: str
    learning_effectiveness: float = 0.0
    decision_types: Set[str] = field(default_factory=set)
    specializations: List[str] = field(default_factory=list)
    collaboration_score: float = 0.0
    last_activity: Optional[datetime] = None


@dataclass
class CollectiveLearningInsight:
    """Insight derived from collective learning across multiple agents."""
    insight_id: str
    decision_type: str
    contributing_agents: List[str]
    aggregated_data: Dict[str, Any]
    confidence_score: float
    effectiveness_score: float
    created_at: datetime


class CrossAgentLearningCoordinator:
    """Coordinates learning between multiple agents for collective intelligence."""
    
    def __init__(self, coordinator_id: str = "cross_agent_learning_coordinator"):
        """Initialize the cross-agent learning coordinator.
        
        Args:
            coordinator_id: Unique identifier for this coordinator
        """
        self.coordinator_id = coordinator_id
        self.agent_profiles: Dict[str, AgentLearningProfile] = {}
        self.collective_insights: Dict[str, CollectiveLearningInsight] = {}
        self.learning_networks: Dict[str, Set[str]] = defaultdict(set)  # decision_type -> agent_ids
        self.insight_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # agent_id -> decision_types
        
        # Coordination parameters
        self.min_agents_for_collective = 2
        self.insight_aggregation_threshold = 0.7
        self.collaboration_bonus = 0.1
        
        # Performance tracking
        self.coordination_metrics = {
            "total_agents": 0,
            "active_networks": 0,
            "collective_insights": 0,
            "successful_transfers": 0,
            "coordination_effectiveness": 0.0,
            "last_coordination": None
        }
        
        logger.info(f"✅ Cross-Agent Learning Coordinator initialized: {self.coordinator_id}")
    
    async def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str] = None) -> bool:
        """Register an agent for cross-agent learning coordination.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (market, executive, content, logistics)
            capabilities: List of agent capabilities/specializations
            
        Returns:
            True if registration was successful, False otherwise
        """
        try:
            profile = AgentLearningProfile(
                agent_id=agent_id,
                agent_type=agent_type,
                specializations=capabilities or [],
                last_activity=datetime.now()
            )
            
            self.agent_profiles[agent_id] = profile
            self.coordination_metrics["total_agents"] = len(self.agent_profiles)
            
            logger.info(f"📝 Registered agent for cross-learning: {agent_id} ({agent_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering agent {agent_id}: {e}")
            return False
    
    async def subscribe_to_insights(self, agent_id: str, decision_types: List[str]) -> bool:
        """Subscribe an agent to receive insights for specific decision types.
        
        Args:
            agent_id: Agent identifier
            decision_types: List of decision types to subscribe to
            
        Returns:
            True if subscription was successful, False otherwise
        """
        try:
            if agent_id not in self.agent_profiles:
                logger.warning(f"Agent {agent_id} not registered for cross-learning")
                return False
            
            # Update subscriptions
            self.insight_subscriptions[agent_id].update(decision_types)
            
            # Update learning networks
            for decision_type in decision_types:
                self.learning_networks[decision_type].add(agent_id)
                self.agent_profiles[agent_id].decision_types.add(decision_type)
            
            self.coordination_metrics["active_networks"] = len(self.learning_networks)
            
            logger.debug(f"📡 Agent {agent_id} subscribed to insights: {decision_types}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing agent {agent_id} to insights: {e}")
            return False
    
    async def share_learning_insight(self, source_agent: str, insight_data: Dict[str, Any]) -> bool:
        """Share a learning insight from one agent with relevant other agents.
        
        Args:
            source_agent: Agent sharing the insight
            insight_data: Insight data including decision_type, effectiveness, etc.
            
        Returns:
            True if sharing was successful, False otherwise
        """
        try:
            decision_type = insight_data.get("decision_type", "unknown")
            effectiveness = insight_data.get("effectiveness_score", 0.0)
            
            if effectiveness < self.insight_aggregation_threshold:
                logger.debug(f"Insight from {source_agent} below threshold: {effectiveness}")
                return False
            
            # Find agents interested in this decision type
            interested_agents = self.learning_networks.get(decision_type, set())
            interested_agents.discard(source_agent)  # Don't share with self
            
            if not interested_agents:
                logger.debug(f"No agents interested in {decision_type} insights")
                return False
            
            # Update source agent's collaboration score
            if source_agent in self.agent_profiles:
                self.agent_profiles[source_agent].collaboration_score += self.collaboration_bonus
                self.agent_profiles[source_agent].last_activity = datetime.now()
            
            # Create collective insight if multiple agents contribute
            await self._process_collective_insight(source_agent, insight_data, interested_agents)
            
            self.coordination_metrics["successful_transfers"] += len(interested_agents)
            self.coordination_metrics["last_coordination"] = datetime.now().isoformat()
            
            logger.info(f"🔄 Shared insight from {source_agent} to {len(interested_agents)} agents")
            return True
            
        except Exception as e:
            logger.error(f"Error sharing insight from {source_agent}: {e}")
            return False
    
    async def _process_collective_insight(self, source_agent: str, insight_data: Dict[str, Any], interested_agents: Set[str]):
        """Process and potentially create collective insights from multiple agents."""
        decision_type = insight_data.get("decision_type", "unknown")
        
        # Check if we have enough agents for collective learning
        total_agents = len(interested_agents) + 1  # +1 for source agent
        if total_agents < self.min_agents_for_collective:
            return
        
        # Look for existing collective insights for this decision type
        existing_insights = [
            insight for insight in self.collective_insights.values()
            if insight.decision_type == decision_type
        ]
        
        # Create or update collective insight
        if existing_insights:
            # Update existing insight
            insight = existing_insights[0]  # Take the most recent one
            if source_agent not in insight.contributing_agents:
                insight.contributing_agents.append(source_agent)
                await self._update_collective_insight(insight, insight_data)
        else:
            # Create new collective insight
            insight_id = f"collective_{decision_type}_{datetime.now().timestamp()}"
            collective_insight = CollectiveLearningInsight(
                insight_id=insight_id,
                decision_type=decision_type,
                contributing_agents=[source_agent],
                aggregated_data=self._aggregate_insight_data([insight_data]),
                confidence_score=insight_data.get("effectiveness_score", 0.0),
                effectiveness_score=insight_data.get("effectiveness_score", 0.0),
                created_at=datetime.now()
            )
            
            self.collective_insights[insight_id] = collective_insight
            self.coordination_metrics["collective_insights"] = len(self.collective_insights)
            
            logger.info(f"🧠 Created collective insight: {insight_id}")
    
    async def _update_collective_insight(self, insight: CollectiveLearningInsight, new_data: Dict[str, Any]):
        """Update an existing collective insight with new data."""
        # Add new data to aggregated data
        insight.aggregated_data = self._aggregate_insight_data([insight.aggregated_data, new_data])
        
        # Update effectiveness score (weighted average)
        new_effectiveness = new_data.get("effectiveness_score", 0.0)
        current_weight = len(insight.contributing_agents) - 1  # Exclude the new agent
        insight.effectiveness_score = (
            (insight.effectiveness_score * current_weight + new_effectiveness) / 
            len(insight.contributing_agents)
        )
        
        # Update confidence score
        insight.confidence_score = min(1.0, insight.confidence_score + 0.1)  # Increase with more contributors
        
        logger.debug(f"🔄 Updated collective insight: {insight.insight_id}")
    
    def _aggregate_insight_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate multiple insight data points into a collective insight."""
        if not data_list:
            return {}
        
        aggregated = {
            "strategies": [],
            "contexts": [],
            "outcomes": [],
            "quality_scores": [],
            "effectiveness_scores": []
        }
        
        for data in data_list:
            if isinstance(data, dict):
                aggregated["strategies"].append(data.get("strategy", "unknown"))
                aggregated["contexts"].append(data.get("context", {}))
                aggregated["outcomes"].append(data.get("outcome", "unknown"))
                aggregated["quality_scores"].append(data.get("quality", 0.0))
                aggregated["effectiveness_scores"].append(data.get("effectiveness_score", 0.0))
        
        # Calculate aggregated metrics
        if aggregated["quality_scores"]:
            aggregated["avg_quality"] = sum(aggregated["quality_scores"]) / len(aggregated["quality_scores"])
            aggregated["avg_effectiveness"] = sum(aggregated["effectiveness_scores"]) / len(aggregated["effectiveness_scores"])
        
        # Find most common strategy and outcome
        if aggregated["strategies"]:
            aggregated["most_common_strategy"] = max(set(aggregated["strategies"]), key=aggregated["strategies"].count)
        if aggregated["outcomes"]:
            aggregated["most_common_outcome"] = max(set(aggregated["outcomes"]), key=aggregated["outcomes"].count)
        
        return aggregated
    
    async def get_collective_recommendations(self, agent_id: str, decision_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get collective learning recommendations for an agent's decision.
        
        Args:
            agent_id: Agent requesting recommendations
            decision_type: Type of decision being made
            context: Decision context
            
        Returns:
            Dictionary containing collective recommendations
        """
        recommendations = {
            "collective_insights": [],
            "peer_strategies": [],
            "collaboration_opportunities": [],
            "confidence_boost": 0.0
        }
        
        try:
            # Find relevant collective insights
            relevant_insights = [
                insight for insight in self.collective_insights.values()
                if insight.decision_type == decision_type and insight.effectiveness_score > 0.7
            ]
            
            for insight in relevant_insights:
                recommendations["collective_insights"].append({
                    "insight_id": insight.insight_id,
                    "contributing_agents": insight.contributing_agents,
                    "effectiveness_score": insight.effectiveness_score,
                    "recommended_strategy": insight.aggregated_data.get("most_common_strategy", "unknown"),
                    "avg_quality": insight.aggregated_data.get("avg_quality", 0.0)
                })
            
            # Find peer agents with similar decision types
            peer_agents = self.learning_networks.get(decision_type, set())
            peer_agents.discard(agent_id)
            
            for peer_id in peer_agents:
                if peer_id in self.agent_profiles:
                    peer_profile = self.agent_profiles[peer_id]
                    recommendations["peer_strategies"].append({
                        "agent_id": peer_id,
                        "agent_type": peer_profile.agent_type,
                        "learning_effectiveness": peer_profile.learning_effectiveness,
                        "collaboration_score": peer_profile.collaboration_score
                    })
            
            # Calculate confidence boost from collective learning
            if recommendations["collective_insights"]:
                avg_effectiveness = sum(
                    insight["effectiveness_score"] for insight in recommendations["collective_insights"]
                ) / len(recommendations["collective_insights"])
                recommendations["confidence_boost"] = min(0.2, avg_effectiveness * 0.2)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting collective recommendations for {agent_id}: {e}")
            return recommendations
    
    async def update_agent_performance(self, agent_id: str, learning_effectiveness: float, decision_types: List[str] = None):
        """Update an agent's learning performance metrics.
        
        Args:
            agent_id: Agent identifier
            learning_effectiveness: Current learning effectiveness score
            decision_types: Decision types the agent is working with
        """
        try:
            if agent_id not in self.agent_profiles:
                logger.warning(f"Agent {agent_id} not registered for performance update")
                return
            
            profile = self.agent_profiles[agent_id]
            profile.learning_effectiveness = learning_effectiveness
            profile.last_activity = datetime.now()
            
            if decision_types:
                profile.decision_types.update(decision_types)
            
            # Update coordination effectiveness
            total_effectiveness = sum(
                profile.learning_effectiveness for profile in self.agent_profiles.values()
            )
            self.coordination_metrics["coordination_effectiveness"] = total_effectiveness / len(self.agent_profiles)
            
            logger.debug(f"📊 Updated performance for {agent_id}: {learning_effectiveness:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating performance for {agent_id}: {e}")
    
    async def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get comprehensive coordination metrics."""
        return {
            **self.coordination_metrics,
            "agent_profiles": {
                agent_id: {
                    "agent_type": profile.agent_type,
                    "learning_effectiveness": profile.learning_effectiveness,
                    "collaboration_score": profile.collaboration_score,
                    "decision_types": list(profile.decision_types),
                    "specializations": profile.specializations
                }
                for agent_id, profile in self.agent_profiles.items()
            },
            "learning_networks": {
                decision_type: list(agents) for decision_type, agents in self.learning_networks.items()
            },
            "collective_insights_summary": [
                {
                    "insight_id": insight.insight_id,
                    "decision_type": insight.decision_type,
                    "contributing_agents": insight.contributing_agents,
                    "effectiveness_score": insight.effectiveness_score
                }
                for insight in self.collective_insights.values()
            ]
        }
