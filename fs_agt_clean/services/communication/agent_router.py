"""
UnifiedAgent Router for FlipSync AI System
===================================

This module provides intelligent routing of user messages to appropriate
specialized agents based on intent recognition and conversation context.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.database.repositories.agent_repository import UnifiedAgentRepository
from fs_agt_clean.database.repositories.chat_repository import ChatRepository
from fs_agt_clean.services.communication.intent_recognizer import (
    IntentRecognizer,
    IntentResult,
)

logger = logging.getLogger(__name__)


class UnifiedAgentType(str, Enum):
    """Available agent types in the FlipSync system."""

    MARKET = "market"
    ANALYTICS = "analytics"
    LOGISTICS = "logistics"
    CONTENT = "content"
    EXECUTIVE = "executive"
    ASSISTANT = "assistant"  # General purpose assistant


class UnifiedAgentStatus(str, Enum):
    """UnifiedAgent availability status."""

    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class RoutingDecision:
    """Result of agent routing decision."""

    target_agent: UnifiedAgentType
    confidence: float
    reasoning: str
    requires_handoff: bool
    handoff_context: Optional[Dict[str, Any]] = None
    fallback_agent: Optional[UnifiedAgentType] = None
    estimated_response_time: Optional[int] = None  # seconds


@dataclass
class UnifiedAgentCapability:
    """Defines an agent's capabilities and specializations."""

    agent_type: UnifiedAgentType
    specializations: List[str]
    supported_intents: List[str]
    max_concurrent_conversations: int
    average_response_time: int  # seconds
    availability_hours: Optional[Tuple[int, int]] = None  # (start_hour, end_hour)


class UnifiedAgentRouter:
    """Intelligent agent routing system with load balancing and context awareness."""

    def __init__(self, database=None):
        """Initialize the agent router."""
        self.intent_recognizer = IntentRecognizer()
        self.chat_repository = ChatRepository()
        self.agent_repository = UnifiedAgentRepository()
        self.database = database

        # Define agent capabilities
        self.agent_capabilities = {
            UnifiedAgentType.MARKET: UnifiedAgentCapability(
                agent_type=UnifiedAgentType.MARKET,
                specializations=[
                    "pricing_analysis",
                    "inventory_management",
                    "competitor_monitoring",
                    "marketplace_optimization",
                    "demand_forecasting",
                    "ebay_integration",
                    "marketplace_inventory",
                ],
                supported_intents=[
                    "market_query",
                    "ebay_inventory_query",
                    "marketplace_inventory_query",
                ],
                max_concurrent_conversations=5,
                average_response_time=30,
            ),
            UnifiedAgentType.ANALYTICS: UnifiedAgentCapability(
                agent_type=UnifiedAgentType.ANALYTICS,
                specializations=[
                    "performance_reporting",
                    "data_visualization",
                    "kpi_tracking",
                    "trend_analysis",
                    "business_intelligence",
                ],
                supported_intents=["analytics_query"],
                max_concurrent_conversations=3,
                average_response_time=45,
            ),
            UnifiedAgentType.LOGISTICS: UnifiedAgentCapability(
                agent_type=UnifiedAgentType.LOGISTICS,
                specializations=[
                    "shipping_optimization",
                    "fulfillment_planning",
                    "carrier_management",
                    "delivery_tracking",
                    "warehouse_operations",
                ],
                supported_intents=["logistics_query"],
                max_concurrent_conversations=4,
                average_response_time=25,
            ),
            UnifiedAgentType.CONTENT: UnifiedAgentCapability(
                agent_type=UnifiedAgentType.CONTENT,
                specializations=[
                    "listing_optimization",
                    "seo_enhancement",
                    "content_creation",
                    "image_optimization",
                    "keyword_research",
                ],
                supported_intents=["content_query"],
                max_concurrent_conversations=3,
                average_response_time=60,
            ),
            UnifiedAgentType.EXECUTIVE: UnifiedAgentCapability(
                agent_type=UnifiedAgentType.EXECUTIVE,
                specializations=[
                    "strategic_planning",
                    "decision_support",
                    "risk_assessment",
                    "business_growth",
                    "investment_analysis",
                ],
                supported_intents=["executive_query"],
                max_concurrent_conversations=2,
                average_response_time=90,
            ),
            UnifiedAgentType.ASSISTANT: UnifiedAgentCapability(
                agent_type=UnifiedAgentType.ASSISTANT,
                specializations=[
                    "general_assistance",
                    "onboarding",
                    "basic_queries",
                    "system_navigation",
                    "troubleshooting",
                ],
                supported_intents=["general_query"],
                max_concurrent_conversations=10,
                average_response_time=15,
            ),
        }

        # Track active conversations per agent
        self.active_conversations = {
            agent_type: set() for agent_type in UnifiedAgentType
        }

        # UnifiedAgent status tracking
        self.agent_status = {
            agent_type: UnifiedAgentStatus.AVAILABLE for agent_type in UnifiedAgentType
        }

    async def route_message(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        conversation_history: Optional[List[Dict]] = None,
        current_agent: Optional[UnifiedAgentType] = None,
    ) -> RoutingDecision:
        """
        Route a message to the most appropriate agent.

        Args:
            message: UnifiedUser message content
            user_id: UnifiedUser identifier
            conversation_id: Conversation identifier
            conversation_history: Previous conversation messages
            current_agent: Currently assigned agent (if any)

        Returns:
            RoutingDecision with target agent and routing details
        """
        try:
            # Recognize intent
            intent_result = self.intent_recognizer.recognize_intent(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                conversation_history=conversation_history,
            )

            # Determine target agent based on intent
            target_agent = self._determine_target_agent(intent_result, current_agent)

            # Check agent availability and load
            available_agent, routing_confidence = await self._select_available_agent(
                target_agent, conversation_id
            )

            # Determine if handoff is required
            requires_handoff = self._requires_handoff(current_agent, available_agent)

            # Prepare handoff context if needed
            handoff_context = None
            if requires_handoff:
                handoff_context = await self._prepare_handoff_context(
                    conversation_id, current_agent, available_agent, intent_result
                )

            # Generate routing reasoning
            reasoning = self._generate_routing_reasoning(
                intent_result, target_agent, available_agent, routing_confidence
            )

            # Estimate response time
            estimated_response_time = self._estimate_response_time(available_agent)

            # Determine fallback agent
            fallback_agent = self._determine_fallback_agent(available_agent)

            # Update conversation tracking
            await self._update_conversation_tracking(
                conversation_id, available_agent, requires_handoff
            )

            return RoutingDecision(
                target_agent=available_agent,
                confidence=routing_confidence,
                reasoning=reasoning,
                requires_handoff=requires_handoff,
                handoff_context=handoff_context,
                fallback_agent=fallback_agent,
                estimated_response_time=estimated_response_time,
            )

        except Exception as e:
            logger.error(f"Error in agent routing: {e}")
            return RoutingDecision(
                target_agent=UnifiedAgentType.ASSISTANT,
                confidence=0.1,
                reasoning=f"Error in routing, defaulting to assistant: {e}",
                requires_handoff=False,
                fallback_agent=None,
                estimated_response_time=15,
            )

    def _determine_target_agent(
        self, intent_result: IntentResult, current_agent: Optional[UnifiedAgentType]
    ) -> UnifiedAgentType:
        """Determine the target agent based on intent recognition."""
        # Map intents to agents
        intent_to_agent = {
            "market_query": UnifiedAgentType.MARKET,
            "analytics_query": UnifiedAgentType.ANALYTICS,
            "logistics_query": UnifiedAgentType.LOGISTICS,
            "content_query": UnifiedAgentType.CONTENT,
            "executive_query": UnifiedAgentType.EXECUTIVE,
            "general_query": UnifiedAgentType.ASSISTANT,
            # eBay-specific intents route to MARKET agent (which handles marketplace functionality)
            "ebay_inventory_query": UnifiedAgentType.MARKET,
            "marketplace_inventory_query": UnifiedAgentType.MARKET,
        }

        # Get primary target
        target_agent = intent_to_agent.get(
            intent_result.primary_intent, UnifiedAgentType.ASSISTANT
        )

        # Consider confidence level
        if intent_result.confidence < 0.5:
            # Low confidence, prefer current agent if available
            if current_agent and current_agent != UnifiedAgentType.ASSISTANT:
                return current_agent
            else:
                return UnifiedAgentType.ASSISTANT

        return target_agent

    async def _select_available_agent(
        self, target_agent: UnifiedAgentType, conversation_id: str
    ) -> Tuple[UnifiedAgentType, float]:
        """Select an available agent considering load and status."""
        # Check if target agent is available
        if await self._is_agent_available(target_agent, conversation_id):
            return target_agent, 1.0

        # Find alternative agents that can handle the request
        alternative_agents = self._find_alternative_agents(target_agent)

        for agent in alternative_agents:
            if await self._is_agent_available(agent, conversation_id):
                return agent, 0.7  # Lower confidence for alternative

        # Fallback to assistant if no specialized agents available
        return UnifiedAgentType.ASSISTANT, 0.3

    async def _is_agent_available(
        self, agent_type: UnifiedAgentType, conversation_id: str
    ) -> bool:
        """Check if an agent is available to handle a new conversation."""
        # Check agent status
        if self.agent_status[agent_type] != UnifiedAgentStatus.AVAILABLE:
            return False

        # Check load capacity
        capability = self.agent_capabilities[agent_type]
        current_load = len(self.active_conversations[agent_type])

        # If conversation is already assigned to this agent, it's available
        if conversation_id in self.active_conversations[agent_type]:
            return True

        # Check if under capacity
        return current_load < capability.max_concurrent_conversations

    def _find_alternative_agents(
        self, target_agent: UnifiedAgentType
    ) -> List[UnifiedAgentType]:
        """Find alternative agents that might handle the request."""
        alternatives = []

        # Define agent compatibility matrix
        compatibility = {
            UnifiedAgentType.MARKET: [
                UnifiedAgentType.ANALYTICS,
                UnifiedAgentType.EXECUTIVE,
            ],
            UnifiedAgentType.ANALYTICS: [
                UnifiedAgentType.MARKET,
                UnifiedAgentType.EXECUTIVE,
            ],
            UnifiedAgentType.LOGISTICS: [
                UnifiedAgentType.MARKET,
                UnifiedAgentType.EXECUTIVE,
            ],
            UnifiedAgentType.CONTENT: [
                UnifiedAgentType.MARKET,
                UnifiedAgentType.ANALYTICS,
            ],
            UnifiedAgentType.EXECUTIVE: [
                UnifiedAgentType.MARKET,
                UnifiedAgentType.ANALYTICS,
            ],
            UnifiedAgentType.ASSISTANT: [],  # Assistant doesn't have alternatives
        }

        alternatives = compatibility.get(target_agent, [])
        alternatives.append(
            UnifiedAgentType.ASSISTANT
        )  # Always include assistant as final fallback

        return alternatives

    def _requires_handoff(
        self, current_agent: Optional[UnifiedAgentType], target_agent: UnifiedAgentType
    ) -> bool:
        """Determine if a handoff between agents is required."""
        if not current_agent:
            return False

        return current_agent != target_agent

    async def _prepare_handoff_context(
        self,
        conversation_id: str,
        from_agent: Optional[UnifiedAgentType],
        to_agent: UnifiedAgentType,
        intent_result: IntentResult,
    ) -> Dict[str, Any]:
        """Prepare context information for agent handoff."""
        context = {
            "handoff_timestamp": datetime.now(timezone.utc).isoformat(),
            "from_agent": from_agent.value if from_agent else None,
            "to_agent": to_agent.value,
            "handoff_reason": intent_result.reasoning,
            "intent_confidence": intent_result.confidence,
            "extracted_entities": intent_result.extracted_entities,
            "conversation_summary": await self._get_conversation_summary(
                conversation_id
            ),
        }

        return context

    async def _get_conversation_summary(self, conversation_id: str) -> str:
        """Get a summary of the conversation for handoff context."""
        try:
            if not self.database:
                logger.warning("Database not available for conversation summary")
                return "No conversation history available"

            async with self.database.get_session() as session:
                messages = await self.chat_repository.get_conversation_messages(
                    session, conversation_id, limit=5
                )

                if not messages:
                    return "No previous conversation history"

                # Create a simple summary
                summary_parts = []
                for msg in messages[-3:]:  # Last 3 messages
                    sender = "UnifiedUser" if msg.sender == "user" else "UnifiedAgent"
                    content = (
                        msg.content[:100] + "..."
                        if len(msg.content) > 100
                        else msg.content
                    )
                    summary_parts.append(f"{sender}: {content}")

                return " | ".join(summary_parts)

        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return "Error retrieving conversation history"

    def _generate_routing_reasoning(
        self,
        intent_result: IntentResult,
        target_agent: UnifiedAgentType,
        selected_agent: UnifiedAgentType,
        confidence: float,
    ) -> str:
        """Generate human-readable reasoning for the routing decision."""
        reasoning_parts = []

        # Intent-based reasoning
        reasoning_parts.append(
            f"Intent: {intent_result.primary_intent} (confidence: {intent_result.confidence:.2f})"
        )

        # UnifiedAgent selection reasoning
        if target_agent == selected_agent:
            reasoning_parts.append(f"Routed to preferred agent: {selected_agent.value}")
        else:
            reasoning_parts.append(
                f"Target agent {target_agent.value} unavailable, using {selected_agent.value}"
            )

        # Confidence reasoning
        if confidence >= 0.8:
            reasoning_parts.append("High routing confidence")
        elif confidence >= 0.5:
            reasoning_parts.append("Medium routing confidence")
        else:
            reasoning_parts.append("Low routing confidence")

        return "; ".join(reasoning_parts)

    def _estimate_response_time(self, agent_type: UnifiedAgentType) -> int:
        """Estimate response time for the selected agent."""
        base_time = self.agent_capabilities[agent_type].average_response_time

        # Adjust based on current load
        current_load = len(self.active_conversations[agent_type])
        max_load = self.agent_capabilities[agent_type].max_concurrent_conversations

        load_factor = current_load / max_load if max_load > 0 else 0
        adjusted_time = int(base_time * (1 + load_factor))

        return adjusted_time

    def _determine_fallback_agent(
        self, selected_agent: UnifiedAgentType
    ) -> Optional[UnifiedAgentType]:
        """Determine fallback agent if selected agent becomes unavailable."""
        if selected_agent == UnifiedAgentType.ASSISTANT:
            return None  # Assistant is the ultimate fallback

        return UnifiedAgentType.ASSISTANT

    async def _update_conversation_tracking(
        self, conversation_id: str, agent_type: UnifiedAgentType, is_handoff: bool
    ):
        """Update conversation tracking for load management."""
        # Add conversation to agent's active list
        self.active_conversations[agent_type].add(conversation_id)

        # Log the routing decision in database
        try:
            if not self.database:
                logger.warning("Database not available for logging routing decision")
                return decision

            async with self.database.get_session() as session:
                await self.agent_repository.log_agent_decision(
                    session=session,
                    agent_id=f"{agent_type.value}_router",
                    agent_type=agent_type.value,
                    decision_type="message_routing",
                    parameters={
                        "conversation_id": conversation_id,
                        "is_handoff": is_handoff,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    confidence=1.0,
                    rationale=f"Routed conversation {conversation_id} to {agent_type.value}",
                    requires_approval=False,
                )
        except Exception as e:
            logger.error(f"Error logging routing decision: {e}")

    async def release_conversation(
        self, conversation_id: str, agent_type: UnifiedAgentType
    ):
        """Release a conversation from an agent's active list."""
        self.active_conversations[agent_type].discard(conversation_id)

    def update_agent_status(
        self, agent_type: UnifiedAgentType, status: UnifiedAgentStatus
    ):
        """Update the status of an agent."""
        self.agent_status[agent_type] = status
        logger.info(f"UnifiedAgent {agent_type.value} status updated to {status.value}")

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics and agent load information."""
        stats = {
            "agent_status": {
                agent.value: status.value for agent, status in self.agent_status.items()
            },
            "active_conversations": {
                agent.value: len(conversations)
                for agent, conversations in self.active_conversations.items()
            },
            "agent_capabilities": {
                agent.value: {
                    "max_concurrent": cap.max_concurrent_conversations,
                    "avg_response_time": cap.average_response_time,
                    "specializations": cap.specializations,
                }
                for agent, cap in self.agent_capabilities.items()
            },
            "load_percentages": {
                agent.value: (
                    len(self.active_conversations[agent])
                    / self.agent_capabilities[agent].max_concurrent_conversations
                    * 100
                )
                for agent in UnifiedAgentType
            },
        }

        return stats
