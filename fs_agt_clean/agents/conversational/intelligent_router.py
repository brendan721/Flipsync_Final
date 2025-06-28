"""
Intelligent UnifiedAgent Router for FlipSync Conversational Interface.

This module provides intelligent routing of user queries to the most appropriate
specialized agents based on intent, context, and agent capabilities.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .advanced_nlu import Entity, Intent

logger = logging.getLogger(__name__)


@dataclass
class UnifiedAgentCapability:
    """Represents an agent's capabilities and specializations."""

    agent_id: str
    agent_type: str
    specializations: List[str]
    supported_intents: List[str]
    current_load: float = 0.0
    availability: bool = True
    performance_score: float = 1.0
    response_time_avg: float = 1.0  # seconds


@dataclass
class RoutingDecision:
    """Represents a routing decision with reasoning."""

    selected_agent: str
    confidence: float
    reasoning: List[str]
    alternative_agents: List[str] = field(default_factory=list)
    estimated_response_time: float = 1.0
    routing_metadata: Dict[str, Any] = field(default_factory=dict)


class IntelligentRouter:
    """
    Intelligent agent router for conversational interface.

    Features:
    - Intent-based routing
    - Load balancing across agents
    - Context-aware routing decisions
    - Performance-based agent selection
    - Fallback routing strategies
    - Real-time agent availability tracking
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Intelligent Router.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.registered_agents: Dict[str, UnifiedAgentCapability] = {}
        self.routing_history: List[Dict[str, Any]] = []
        self.load_balancing_enabled = self.config.get("load_balancing", True)
        self.performance_tracking_enabled = self.config.get(
            "performance_tracking", True
        )

        # Initialize default agent capabilities
        self._initialize_default_agents()

        logger.info("IntelligentRouter initialized")

    def _initialize_default_agents(self) -> None:
        """Initialize default agent capabilities."""
        default_agents = [
            UnifiedAgentCapability(
                agent_id="market_agent",
                agent_type="MarketUnifiedAgent",
                specializations=["pricing", "market_analysis", "competitor_monitoring"],
                supported_intents=[
                    "price_inquiry",
                    "competitor_analysis",
                    "market_trends",
                ],
            ),
            UnifiedAgentCapability(
                agent_id="inventory_agent",
                agent_type="InventoryUnifiedAgent",
                specializations=[
                    "stock_management",
                    "inventory_tracking",
                    "reorder_alerts",
                ],
                supported_intents=[
                    "inventory_check",
                    "stock_inquiry",
                    "reorder_request",
                ],
            ),
            UnifiedAgentCapability(
                agent_id="content_agent",
                agent_type="ContentUnifiedAgent",
                specializations=[
                    "listing_creation",
                    "seo_optimization",
                    "content_enhancement",
                ],
                supported_intents=[
                    "listing_management",
                    "content_optimization",
                    "seo_inquiry",
                ],
            ),
            UnifiedAgentCapability(
                agent_id="logistics_agent",
                agent_type="LogisticsUnifiedAgent",
                specializations=[
                    "shipping",
                    "delivery_tracking",
                    "warehouse_management",
                ],
                supported_intents=[
                    "shipping_inquiry",
                    "delivery_status",
                    "warehouse_operations",
                ],
            ),
            UnifiedAgentCapability(
                agent_id="strategy_agent",
                agent_type="StrategyUnifiedAgent",
                specializations=[
                    "strategic_planning",
                    "decision_making",
                    "optimization",
                ],
                supported_intents=[
                    "strategy_planning",
                    "optimization_request",
                    "decision_support",
                ],
            ),
            UnifiedAgentCapability(
                agent_id="executive_agent",
                agent_type="ExecutiveUnifiedAgent",
                specializations=["analytics", "reporting", "performance_monitoring"],
                supported_intents=[
                    "sales_analytics",
                    "performance_report",
                    "business_insights",
                ],
            ),
        ]

        for agent in default_agents:
            self.registered_agents[agent.agent_id] = agent

    async def route_request(
        self, intent: Intent, context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Route a request to the most appropriate agent.

        Args:
            intent: Recognized user intent
            context: Optional conversation context

        Returns:
            Routing decision with selected agent and reasoning
        """
        context = context or {}

        # Find candidate agents
        candidates = self._find_candidate_agents(intent)

        if not candidates:
            # Fallback to general assistant
            return RoutingDecision(
                selected_agent="general_assistant",
                confidence=0.5,
                reasoning=[
                    "No specialized agents found for intent",
                    "Routing to general assistant",
                ],
                estimated_response_time=2.0,
            )

        # Score and rank candidates
        scored_candidates = self._score_candidates(candidates, intent, context)

        # Select best candidate
        best_agent, best_score = scored_candidates[0]

        # Generate routing decision
        decision = RoutingDecision(
            selected_agent=best_agent.agent_id,
            confidence=best_score,
            reasoning=self._generate_routing_reasoning(best_agent, intent, best_score),
            alternative_agents=[agent.agent_id for agent, _ in scored_candidates[1:3]],
            estimated_response_time=best_agent.response_time_avg,
            routing_metadata={
                "intent_name": intent.intent_name,
                "intent_confidence": intent.confidence,
                "agent_type": best_agent.agent_type,
                "agent_load": best_agent.current_load,
            },
        )

        # Update routing history
        self._update_routing_history(decision, intent, context)

        logger.info(
            f"Routed {intent.intent_name} to {best_agent.agent_id} (confidence: {best_score:.2f})"
        )
        return decision

    def _find_candidate_agents(self, intent: Intent) -> List[UnifiedAgentCapability]:
        """Find candidate agents that can handle the intent."""
        candidates = []

        for agent in self.registered_agents.values():
            if not agent.availability:
                continue

            # Check if agent supports the intent
            if intent.intent_name in agent.supported_intents:
                candidates.append(agent)
                continue

            # Check if agent has relevant specializations
            for entity in intent.entities:
                if any(
                    spec in entity.entity_type.lower()
                    or entity.entity_type.lower() in spec
                    for spec in agent.specializations
                ):
                    candidates.append(agent)
                    break

        return candidates

    def _score_candidates(
        self, candidates: List[UnifiedAgentCapability], intent: Intent, context: Dict[str, Any]
    ) -> List[Tuple[UnifiedAgentCapability, float]]:
        """Score and rank candidate agents."""
        scored_candidates = []

        for agent in candidates:
            score = self._calculate_agent_score(agent, intent, context)
            scored_candidates.append((agent, score))

        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        return scored_candidates

    def _calculate_agent_score(
        self, agent: UnifiedAgentCapability, intent: Intent, context: Dict[str, Any]
    ) -> float:
        """Calculate score for an agent based on multiple factors."""
        score = 0.0

        # Intent match score (40% weight)
        if intent.intent_name in agent.supported_intents:
            score += 0.4

        # Specialization match score (30% weight)
        specialization_matches = 0
        for entity in intent.entities:
            for spec in agent.specializations:
                if (
                    spec in entity.entity_type.lower()
                    or entity.entity_type.lower() in spec
                ):
                    specialization_matches += 1

        if agent.specializations:
            specialization_score = min(
                1.0, specialization_matches / len(agent.specializations)
            )
            score += specialization_score * 0.3

        # Performance score (15% weight)
        if self.performance_tracking_enabled:
            score += agent.performance_score * 0.15

        # Load balancing score (15% weight)
        if self.load_balancing_enabled:
            load_score = max(0.0, 1.0 - agent.current_load)
            score += load_score * 0.15

        # Context relevance bonus
        if context.get("preferred_agent") == agent.agent_id:
            score += 0.1

        return min(1.0, score)

    def _generate_routing_reasoning(
        self, agent: UnifiedAgentCapability, intent: Intent, score: float
    ) -> List[str]:
        """Generate human-readable reasoning for routing decision."""
        reasoning = []

        if intent.intent_name in agent.supported_intents:
            reasoning.append(f"UnifiedAgent directly supports '{intent.intent_name}' intent")

        if agent.specializations:
            matching_specs = []
            for entity in intent.entities:
                for spec in agent.specializations:
                    if spec in entity.entity_type.lower():
                        matching_specs.append(spec)

            if matching_specs:
                reasoning.append(f"UnifiedAgent specializes in: {', '.join(matching_specs)}")

        if agent.performance_score > 0.8:
            reasoning.append("UnifiedAgent has high performance rating")

        if agent.current_load < 0.5:
            reasoning.append("UnifiedAgent has low current load")

        reasoning.append(f"Overall confidence score: {score:.2f}")

        return reasoning

    def _update_routing_history(
        self, decision: RoutingDecision, intent: Intent, context: Dict[str, Any]
    ) -> None:
        """Update routing history for analytics."""
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "intent_name": intent.intent_name,
            "intent_confidence": intent.confidence,
            "selected_agent": decision.selected_agent,
            "routing_confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "estimated_response_time": decision.estimated_response_time,
        }

        self.routing_history.append(history_entry)

        # Keep only last 100 routing decisions
        if len(self.routing_history) > 100:
            self.routing_history = self.routing_history[-100:]

    async def register_agent(self, agent_capability: UnifiedAgentCapability) -> bool:
        """Register a new agent with the router."""
        self.registered_agents[agent_capability.agent_id] = agent_capability
        logger.info(f"Registered agent: {agent_capability.agent_id}")
        return True

    async def update_agent_status(
        self,
        agent_id: str,
        availability: Optional[bool] = None,
        current_load: Optional[float] = None,
        performance_score: Optional[float] = None,
        response_time_avg: Optional[float] = None,
    ) -> bool:
        """Update agent status and metrics."""
        if agent_id not in self.registered_agents:
            return False

        agent = self.registered_agents[agent_id]

        if availability is not None:
            agent.availability = availability

        if current_load is not None:
            agent.current_load = max(0.0, min(1.0, current_load))

        if performance_score is not None:
            agent.performance_score = max(0.0, min(1.0, performance_score))

        if response_time_avg is not None:
            agent.response_time_avg = max(0.1, response_time_avg)

        return True

    async def get_routing_analytics(self) -> Dict[str, Any]:
        """Get routing analytics and statistics."""
        if not self.routing_history:
            return {"message": "No routing history available"}

        # Calculate statistics
        total_routes = len(self.routing_history)
        agent_usage = {}
        avg_confidence = 0.0
        avg_response_time = 0.0

        for entry in self.routing_history:
            agent = entry["selected_agent"]
            agent_usage[agent] = agent_usage.get(agent, 0) + 1
            avg_confidence += entry["routing_confidence"]
            avg_response_time += entry["estimated_response_time"]

        avg_confidence /= total_routes
        avg_response_time /= total_routes

        # Most used agent
        most_used_agent = max(agent_usage.items(), key=lambda x: x[1])[0]

        return {
            "total_routing_decisions": total_routes,
            "average_routing_confidence": avg_confidence,
            "average_estimated_response_time": avg_response_time,
            "agent_usage_distribution": agent_usage,
            "most_used_agent": most_used_agent,
            "registered_agents": len(self.registered_agents),
            "available_agents": sum(
                1 for agent in self.registered_agents.values() if agent.availability
            ),
        }

    async def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents."""
        return {
            agent_id: {
                "agent_type": agent.agent_type,
                "specializations": agent.specializations,
                "supported_intents": agent.supported_intents,
                "availability": agent.availability,
                "current_load": agent.current_load,
                "performance_score": agent.performance_score,
                "response_time_avg": agent.response_time_avg,
            }
            for agent_id, agent in self.registered_agents.items()
        }
