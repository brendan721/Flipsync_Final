"""
UnifiedAgent Communication Protocol for FlipSync Multi-UnifiedAgent System
===========================================================

This module implements the communication protocol for the FlipSync agentic system
using unified gemma3:4b model for all agents, enabling intelligent routing
and agent-to-agent communication.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.core.ai.llm_adapter import FlipSyncLLMFactory

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Types of user intents for agent routing."""

    PRICING = "pricing"
    COMPETITION = "competition"
    LISTING = "listing"
    SEO = "seo"
    SHIPPING = "shipping"
    INVENTORY = "inventory"
    STRATEGY = "strategy"
    DECISION = "decision"
    GENERAL = "general"


class UnifiedAgentType(str, Enum):
    """Types of agents available for routing."""

    MARKET = "market"
    CONTENT = "content"
    LOGISTICS = "logistics"
    EXECUTIVE = "executive"
    LIAISON = "liaison"


@dataclass
class IntentRecognitionResult:
    """Result of intent recognition analysis."""

    intent: IntentType
    confidence: float
    target_agent: UnifiedAgentType
    reasoning: str
    keywords_matched: List[str]


@dataclass
class UnifiedAgentRoutingContext:
    """Context for agent routing decisions."""

    user_message: str
    conversation_id: str
    user_id: Optional[str]
    conversation_history: List[Dict[str, Any]]
    intent_result: Optional[IntentRecognitionResult]
    metadata: Dict[str, Any]


class IntentRecognizer:
    """Recognizes user intent and determines appropriate agent routing."""

    def __init__(self):
        """Initialize the intent recognizer."""
        self.intent_patterns = self._build_intent_patterns()
        logger.info("Intent recognizer initialized")

    def _build_intent_patterns(self) -> Dict[IntentType, Dict[str, Any]]:
        """Build intent recognition patterns."""
        return {
            IntentType.PRICING: {
                "keywords": [
                    "price",
                    "pricing",
                    "cost",
                    "expensive",
                    "cheap",
                    "value",
                    "competitor price",
                    "market price",
                    "pricing strategy",
                    "how much",
                    "what price",
                    "price point",
                    "underpriced",
                    "overpriced",
                ],
                "target_agent": UnifiedAgentType.MARKET,
                "confidence_boost": 0.2,
            },
            IntentType.COMPETITION: {
                "keywords": [
                    "competitor",
                    "competition",
                    "rival",
                    "compare",
                    "versus",
                    "market analysis",
                    "competitive",
                    "benchmark",
                    "outperform",
                    "market share",
                    "competitor analysis",
                ],
                "target_agent": UnifiedAgentType.MARKET,
                "confidence_boost": 0.2,
            },
            IntentType.LISTING: {
                "keywords": [
                    "listing",
                    "title",
                    "description",
                    "content",
                    "write",
                    "optimize listing",
                    "product description",
                    "bullet points",
                    "features",
                    "benefits",
                    "listing optimization",
                ],
                "target_agent": UnifiedAgentType.CONTENT,
                "confidence_boost": 0.2,
            },
            IntentType.SEO: {
                "keywords": [
                    "seo",
                    "search",
                    "keywords",
                    "visibility",
                    "ranking",
                    "search optimization",
                    "findable",
                    "discoverable",
                    "search terms",
                    "keyword research",
                ],
                "target_agent": UnifiedAgentType.CONTENT,
                "confidence_boost": 0.2,
            },
            IntentType.SHIPPING: {
                "keywords": [
                    "shipping",
                    "delivery",
                    "fulfillment",
                    "carrier",
                    "freight",
                    "shipping cost",
                    "delivery time",
                    "logistics",
                    "warehouse",
                    "ship",
                    "send",
                    "mail",
                ],
                "target_agent": UnifiedAgentType.LOGISTICS,
                "confidence_boost": 0.2,
            },
            IntentType.INVENTORY: {
                "keywords": [
                    "inventory",
                    "stock",
                    "quantity",
                    "reorder",
                    "supply",
                    "out of stock",
                    "low stock",
                    "inventory management",
                    "stock level",
                    "replenish",
                ],
                "target_agent": UnifiedAgentType.LOGISTICS,
                "confidence_boost": 0.2,
            },
            IntentType.STRATEGY: {
                "keywords": [
                    "strategy",
                    "plan",
                    "business",
                    "growth",
                    "expansion",
                    "strategic",
                    "roadmap",
                    "vision",
                    "goals",
                    "objectives",
                    "business plan",
                    "market strategy",
                ],
                "target_agent": UnifiedAgentType.EXECUTIVE,
                "confidence_boost": 0.2,
            },
            IntentType.DECISION: {
                "keywords": [
                    "decision",
                    "choose",
                    "recommend",
                    "suggest",
                    "advice",
                    "should i",
                    "what should",
                    "best option",
                    "recommendation",
                    "guidance",
                    "help me decide",
                ],
                "target_agent": UnifiedAgentType.EXECUTIVE,
                "confidence_boost": 0.2,
            },
        }

    async def recognize_intent(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> IntentRecognitionResult:
        """Recognize intent from user message."""
        try:
            message_lower = message.lower().strip()

            # Calculate scores for each intent
            intent_scores = {}
            matched_keywords = {}

            for intent_type, pattern in self.intent_patterns.items():
                score = 0.0
                keywords_found = []

                # Check for keyword matches
                for keyword in pattern["keywords"]:
                    if keyword in message_lower:
                        score += 1.0
                        keywords_found.append(keyword)

                # Apply confidence boost if keywords found
                if keywords_found:
                    score += pattern.get("confidence_boost", 0.0)

                # Normalize score by number of keywords
                if pattern["keywords"]:
                    score = score / len(pattern["keywords"])

                intent_scores[intent_type] = score
                matched_keywords[intent_type] = keywords_found

            # Find the best intent
            if intent_scores:
                best_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
                best_score = intent_scores[best_intent]

                # If no clear intent found, default to general
                if best_score < 0.1:
                    best_intent = IntentType.GENERAL
                    best_score = 0.5
                    target_agent = UnifiedAgentType.LIAISON
                    reasoning = (
                        "No specific intent detected, routing to general liaison"
                    )
                    keywords_found = []
                else:
                    target_agent = self.intent_patterns[best_intent]["target_agent"]
                    reasoning = f"Intent '{best_intent.value}' detected with confidence {best_score:.2f}"
                    keywords_found = matched_keywords[best_intent]
            else:
                # Fallback
                best_intent = IntentType.GENERAL
                best_score = 0.5
                target_agent = UnifiedAgentType.LIAISON
                reasoning = "Fallback to general intent"
                keywords_found = []

            result = IntentRecognitionResult(
                intent=best_intent,
                confidence=min(best_score, 1.0),
                target_agent=target_agent,
                reasoning=reasoning,
                keywords_matched=keywords_found,
            )

            logger.info(
                f"Intent recognized: {result.intent.value} -> {result.target_agent.value} (confidence: {result.confidence:.2f})"
            )
            return result

        except Exception as e:
            logger.error(f"Error recognizing intent: {e}")
            # Return safe fallback
            return IntentRecognitionResult(
                intent=IntentType.GENERAL,
                confidence=0.5,
                target_agent=UnifiedAgentType.LIAISON,
                reasoning=f"Error in intent recognition: {str(e)}",
                keywords_matched=[],
            )


class UnifiedAgentCommunicationProtocol:
    """Manages communication between liaison and complex agents."""

    def __init__(self, agent_orchestrator=None):
        """Initialize the communication protocol."""
        self.orchestrator = agent_orchestrator
        self.intent_recognizer = IntentRecognizer()
        self.liaison_client = None
        self.complex_agent_clients = {}

        logger.info("UnifiedAgent Communication Protocol initialized")

    async def initialize(self):
        """Initialize LLM clients for communication using unified gemma3:4b model."""
        try:
            # Initialize unified client for all agents (gemma3:4b)
            self.liaison_client = FlipSyncLLMFactory.create_liaison_client()
            logger.info("Unified liaison client initialized with gemma3:4b")

            # Initialize unified agent clients (all using gemma3:4b)
            for agent_type in [
                UnifiedAgentType.MARKET,
                UnifiedAgentType.CONTENT,
                UnifiedAgentType.LOGISTICS,
                UnifiedAgentType.EXECUTIVE,
            ]:
                self.complex_agent_clients[agent_type] = (
                    FlipSyncLLMFactory.create_complex_agent_client(agent_type.value)
                )
                logger.info(
                    f"Unified agent client initialized for {agent_type.value} with gemma3:4b"
                )

            logger.info(
                "All unified agent communication clients initialized successfully"
            )

        except Exception as e:
            logger.error(f"Error initializing agent communication clients: {e}")
            raise

    async def route_to_agent(self, context: UnifiedAgentRoutingContext) -> UnifiedAgentResponse:
        """Route message to appropriate agent based on intent."""
        try:
            # Recognize intent if not already done
            if not context.intent_result:
                context.intent_result = await self.intent_recognizer.recognize_intent(
                    context.user_message, context.metadata
                )

            intent_result = context.intent_result

            # Route based on target agent
            if intent_result.target_agent == UnifiedAgentType.LIAISON:
                return await self._handle_liaison_response(context)
            else:
                return await self._handle_complex_agent_response(context)

        except Exception as e:
            logger.error(f"Error routing to agent: {e}")
            return self._create_fallback_response(context.user_message, str(e))

    async def _handle_liaison_response(
        self, context: UnifiedAgentRoutingContext
    ) -> UnifiedAgentResponse:
        """Handle response using liaison agent (gemma3:4b)."""
        try:
            if not self.liaison_client:
                await self.initialize()

            # Create liaison system prompt (Phase 4 Enhancement)
            from fs_agt_clean.core.agents.agent_prompts import get_agent_system_prompt

            system_prompt = get_agent_system_prompt(UnifiedAgentType.LIAISON)

            # Generate response
            response = await self.liaison_client.generate_response(
                prompt=context.user_message, system_prompt=system_prompt
            )

            return UnifiedAgentResponse(
                content=response.content,
                agent_type="liaison",
                confidence=0.8,
                response_time=response.response_time,
                metadata={
                    "model_used": response.model,
                    "provider": response.provider.value,
                    "intent": (
                        context.intent_result.intent.value
                        if context.intent_result
                        else "general"
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Error in liaison response: {e}")
            return self._create_fallback_response(context.user_message, str(e))

    async def _handle_complex_agent_response(
        self, context: UnifiedAgentRoutingContext
    ) -> UnifiedAgentResponse:
        """Handle response using complex agent (gemma3:4b)."""
        try:
            if not self.complex_agent_clients:
                await self.initialize()

            target_agent = context.intent_result.target_agent
            agent_client = self.complex_agent_clients.get(target_agent)

            if not agent_client:
                logger.warning(
                    f"Complex agent client not available for {target_agent.value}, falling back to liaison"
                )
                return await self._handle_liaison_response(context)

            # Create specialized system prompt based on agent type
            system_prompt = self._get_agent_system_prompt(target_agent)

            # Generate response
            response = await agent_client.generate_response(
                prompt=context.user_message, system_prompt=system_prompt
            )

            return UnifiedAgentResponse(
                content=response.content,
                agent_type=target_agent.value,
                confidence=context.intent_result.confidence,
                response_time=response.response_time,
                metadata={
                    "model_used": response.model,
                    "provider": response.provider.value,
                    "intent": context.intent_result.intent.value,
                    "keywords_matched": context.intent_result.keywords_matched,
                },
            )

        except Exception as e:
            logger.error(f"Error in complex agent response: {e}")
            return self._create_fallback_response(context.user_message, str(e))

    def _get_agent_system_prompt(self, agent_type: UnifiedAgentType) -> str:
        """Get specialized system prompt for agent type (Phase 4 Enhancement)."""
        from fs_agt_clean.core.agents.agent_prompts import get_agent_system_prompt

        return get_agent_system_prompt(agent_type)

    def _create_fallback_response(self, message: str, error: str = "") -> UnifiedAgentResponse:
        """Create a fallback response when routing fails."""
        content = "I apologize, but I'm having trouble processing your request right now. Please try again or rephrase your question."
        if error:
            logger.error(f"Fallback response due to error: {error}")

        return UnifiedAgentResponse(
            content=content,
            agent_type="fallback",
            confidence=0.1,
            response_time=0.0,
            metadata={"error": error, "fallback": True},
        )


class UnifiedAgentCommunicationManager:
    """
    UnifiedAgent Communication Manager - High-level interface for agent communication.

    This class provides a unified interface for agent communication management,
    integrating with the Pipeline Controller and UnifiedAgent Manager for workflow coordination.
    """

    def __init__(self, agent_manager=None, pipeline_controller=None):
        """
        Initialize the UnifiedAgent Communication Manager.

        Args:
            agent_manager: The agent manager instance
            pipeline_controller: The pipeline controller instance
        """
        # Import here to avoid circular imports
        from fs_agt_clean.core.communication.communication_manager import (
            CommunicationManager,
        )

        # Create the underlying communication manager
        self._communication_manager = CommunicationManager(
            agent_manager=agent_manager, pipeline_controller=pipeline_controller
        )

        # Also create the communication protocol for intent-based routing
        self._communication_protocol = UnifiedAgentCommunicationProtocol()

        logger.info("UnifiedAgent Communication Manager initialized")

    async def initialize(self) -> bool:
        """Initialize the communication manager."""
        try:
            # Initialize both components
            comm_manager_success = await self._communication_manager.initialize()
            await self._communication_protocol.initialize()

            logger.info("UnifiedAgent Communication Manager initialization completed")
            return comm_manager_success

        except Exception as e:
            logger.error(f"Failed to initialize UnifiedAgent Communication Manager: {e}")
            return False

    async def send_message(self, message_data: Dict[str, Any]) -> bool:
        """Send a message between agents."""
        try:
            # Import here to avoid circular imports
            from fs_agt_clean.core.protocols.agent_protocol import (
                UnifiedAgentMessage,
                MessageType,
            )

            # Create UnifiedAgentMessage from data
            message = UnifiedAgentMessage(
                message_id=message_data.get("message_id", str(uuid4())),
                message_type=MessageType(message_data.get("type", "update")),
                sender_id=message_data.get("sender_id", "system"),
                recipient_id=message_data.get("recipient_id", "broadcast"),
                content=message_data.get("content", {}),
                metadata=message_data.get("metadata", {}),
            )

            return await self._communication_manager.send_agent_message(message)

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def route_user_message(
        self, user_message: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Route user message to appropriate agent using intent recognition."""
        try:
            # Create routing context
            routing_context = UnifiedAgentRoutingContext(
                user_message=user_message,
                conversation_id=context.get("conversation_id", str(uuid4())),
                user_id=context.get("user_id"),
                conversation_history=context.get("history", []),
                intent_result=None,
                metadata=context or {},
            )

            # Route to agent
            response = await self._communication_protocol.route_to_agent(
                routing_context
            )

            return {
                "content": response.content,
                "agent_type": response.agent_type,
                "confidence": response.confidence,
                "response_time": response.response_time,
                "metadata": response.metadata,
            }

        except Exception as e:
            logger.error(f"Failed to route user message: {e}")
            return {
                "content": "I apologize, but I encountered an error processing your request.",
                "agent_type": "error",
                "confidence": 0.0,
                "response_time": 0.0,
                "metadata": {"error": str(e)},
            }

    async def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics."""
        return await self._communication_manager.get_communication_stats()

    def get_intent_recognizer(self) -> IntentRecognizer:
        """Get the intent recognizer for advanced routing."""
        return self._communication_protocol.intent_recognizer
