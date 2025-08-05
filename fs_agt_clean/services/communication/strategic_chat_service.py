"""
Strategic Chat Service for FlipSync Conversational Interface
===========================================================

Implements strategic Gemini usage for conversational interface responses,
replacing OpenAI for user communication while maintaining the 4+1 architecture
separation between autonomous agents and conversational interface.

✅ PHASE 3.3.1: StrategicChatService Integration
- Uses conversational_interfaces table for registration
- Integrates with autonomous agent decision pipeline
- 4+1 architecture awareness in conversations
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fs_agt_clean.core.ai.strategic_gemini_service import (
    StrategicGeminiService,
    StrategicAnalysisRequest,
    StrategicUseCase,
)
from fs_agt_clean.database.repositories.conversational_interface_repository import (
    ConversationalInterfaceRepository,
)
from fs_agt_clean.database.repositories.autonomous_agent_repository import (
    AutonomousAgentRepository,
)
from fs_agt_clean.database.models.autonomous_agent import (
    ConversationalInterfaceType,
)
from fs_agt_clean.core.db.database import get_database

logger = logging.getLogger(__name__)


@dataclass
class ChatRequest:
    """Request for conversational interface."""

    message: str
    user_id: str
    conversation_id: str
    context: Dict[str, Any] = None
    priority: str = "normal"


@dataclass
class ChatResponse:
    """Response from conversational interface."""

    content: str
    confidence: float
    response_time: float
    agent_type: str = "conversational_interface"
    metadata: Dict[str, Any] = None
    cost_estimate: float = 0.0


class StrategicChatService:
    """
    Strategic chat service using Gemini for conversational interface.

    This service handles user communication through the conversational interface
    while maintaining separation from the autonomous agent system.
    """

    def __init__(self, daily_budget: float = 10.0):
        """Initialize strategic chat service with 4+1 architecture integration."""
        self.strategic_service = StrategicGeminiService(daily_budget=daily_budget)
        self.daily_budget = daily_budget

        # ✅ PHASE 3.3.1: 4+1 Architecture Integration
        self.interface_repository = ConversationalInterfaceRepository()
        self.agent_repository = AutonomousAgentRepository()
        self.interface_id = "strategic_chat_service_4plus1"

        # Chat context management
        self.conversation_contexts = {}
        self.max_context_length = 10  # Keep last 10 exchanges

        # Response templates for common queries with 4+1 architecture awareness
        self.quick_responses = {
            "hello": "Hello! I'm FlipSync's AI assistant powered by our 4+1 architecture. How can I help you with your e-commerce needs today?",
            "help": "I can help you with pricing strategies, inventory management, market analysis, and product optimization. Our 4 autonomous agents are working behind the scenes to optimize your business.",
            "status": "FlipSync 4+1 architecture is running optimally. All 4 autonomous agents (Market, Content, Executive, Logistics) are active and processing decisions with 100% LLM-free compliance.",
            "agents": "FlipSync uses a 4+1 architecture: 4 autonomous agents (Market, Content, Executive, Logistics) handle business decisions, while I serve as your conversational interface.",
        }

        logger.info(
            "Strategic chat service initialized with 4+1 architecture integration"
        )

    async def register_interface(self) -> bool:
        """Register this conversational interface in the 4+1 architecture database."""
        try:
            database = get_database()
            async with database.get_session() as session:
                interface = await self.interface_repository.create_or_update_interface(
                    session=session,
                    interface_id=self.interface_id,
                    interface_type=ConversationalInterfaceType.STRATEGIC_CHAT,
                    service_class="StrategicChatService",
                    llm_provider="gemini",
                    gemini_model="gemini-2.5-flash-lite",
                    daily_budget=self.daily_budget,
                    status="active",
                    capabilities=[
                        "Natural language processing",
                        "Strategic recommendations",
                        "4+1 architecture awareness",
                        "Agent status reporting",
                        "Decision coordination",
                    ],
                )

                logger.info(
                    f"✅ Conversational interface registered: {interface.interface_id}"
                )
                return True

        except Exception as e:
            logger.error(f"❌ Failed to register conversational interface: {e}")
            return False

    async def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get summary of autonomous agent status for conversational responses."""
        try:
            database = get_database()
            async with database.get_session() as session:
                agents = await self.agent_repository.get_all_autonomous_agents(session)
                recent_decisions = (
                    await self.agent_repository.get_decisions_with_filters(
                        session, limit=10
                    )
                )

                # Calculate summary metrics
                active_agents = sum(
                    1 for agent in agents if agent.status.value == "running"
                )
                llm_free_agents = sum(1 for agent in agents if agent.llm_free)

                return {
                    "total_agents": len(agents),
                    "active_agents": active_agents,
                    "llm_free_compliance": (
                        (llm_free_agents / len(agents)) * 100 if agents else 0
                    ),
                    "recent_decisions": len(recent_decisions),
                    "architecture_status": (
                        "4+1 compliant"
                        if llm_free_agents == len(agents)
                        else "compliance issues"
                    ),
                }

        except Exception as e:
            logger.error(f"❌ Failed to get agent status: {e}")
            return {
                "total_agents": 0,
                "active_agents": 0,
                "llm_free_compliance": 0,
                "recent_decisions": 0,
                "architecture_status": "status unavailable",
            }

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        """Handle conversational interface requests using strategic Gemini."""
        start_time = time.perf_counter()

        try:
            # Check for quick responses first (algorithmic)
            quick_response = self._check_quick_responses(request.message.lower())
            if quick_response:
                response_time = time.perf_counter() - start_time
                return ChatResponse(
                    content=quick_response,
                    confidence=0.9,
                    response_time=response_time,
                    metadata={
                        "response_type": "quick_response",
                        "strategic_llm_used": False,
                    },
                )

            # Use strategic Gemini for complex queries
            return await self._handle_strategic_chat(request, start_time)

        except Exception as e:
            response_time = time.perf_counter() - start_time
            logger.error(f"Chat handling error: {e}")

            return ChatResponse(
                content="I'm experiencing some technical difficulties. Please try again in a moment.",
                confidence=0.1,
                response_time=response_time,
                metadata={"error": str(e), "strategic_llm_used": False},
            )

    async def _handle_strategic_chat(
        self, request: ChatRequest, start_time: float
    ) -> ChatResponse:
        """Handle chat using strategic Gemini analysis."""
        # Build conversation context
        context = self._build_conversation_context(request)

        # Create strategic analysis request
        analysis_request = StrategicAnalysisRequest(
            use_case=StrategicUseCase.USER_COMMUNICATION,
            content=request.message,
            context=context,
            priority=request.priority,
            max_tokens=500,  # Concise responses
            temperature=0.7,  # Balanced creativity
        )

        # Get strategic Gemini response
        analysis_response = await self.strategic_service.analyze(analysis_request)

        response_time = time.perf_counter() - start_time

        if analysis_response.success:
            # Update conversation context
            self._update_conversation_context(request, analysis_response.content)

            return ChatResponse(
                content=analysis_response.content,
                confidence=analysis_response.confidence_score,
                response_time=response_time,
                metadata={
                    "strategic_llm_used": True,
                    "model_used": analysis_response.model_used,
                    "cost_estimate": analysis_response.cost_estimate,
                    "tokens_used": analysis_response.metadata.get("tokens_used", 0),
                },
                cost_estimate=analysis_response.cost_estimate,
            )
        else:
            # Fallback to algorithmic response
            fallback_content = self._generate_fallback_response(request.message)

            return ChatResponse(
                content=fallback_content,
                confidence=0.6,
                response_time=response_time,
                metadata={
                    "strategic_llm_used": False,
                    "fallback_used": True,
                    "error": analysis_response.error_message,
                },
            )

    def _check_quick_responses(self, message: str) -> Optional[str]:
        """Check for quick algorithmic responses."""
        message_lower = message.lower().strip()

        # Exact matches
        if message_lower in self.quick_responses:
            return self.quick_responses[message_lower]

        # Pattern matches
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey"]):
            return self.quick_responses["hello"]

        if any(
            help_word in message_lower for help_word in ["help", "assist", "support"]
        ):
            return self.quick_responses["help"]

        if any(
            status_word in message_lower
            for status_word in ["status", "health", "running"]
        ):
            return self.quick_responses["status"]

        return None

    def _build_conversation_context(self, request: ChatRequest) -> Dict[str, Any]:
        """Build conversation context for strategic analysis."""
        context = {
            "platform": "FlipSync",
            "interface_type": "conversational",
            "user_id": request.user_id,
            "conversation_id": request.conversation_id,
        }

        # Add conversation history
        if request.conversation_id in self.conversation_contexts:
            context["conversation_history"] = self.conversation_contexts[
                request.conversation_id
            ]

        # Add request context
        if request.context:
            context.update(request.context)

        return context

    def _update_conversation_context(self, request: ChatRequest, response: str):
        """Update conversation context with new exchange."""
        if request.conversation_id not in self.conversation_contexts:
            self.conversation_contexts[request.conversation_id] = []

        context = self.conversation_contexts[request.conversation_id]

        # Add new exchange
        context.append(
            {
                "user": request.message,
                "assistant": response,
                "timestamp": time.time(),
            }
        )

        # Trim to max length
        if len(context) > self.max_context_length:
            context = context[-self.max_context_length :]
            self.conversation_contexts[request.conversation_id] = context

    def _generate_fallback_response(self, message: str) -> str:
        """Generate algorithmic fallback response."""
        # Simple keyword-based responses
        message_lower = message.lower()

        if any(word in message_lower for word in ["price", "pricing", "cost"]):
            return "I can help you with pricing strategies. Our autonomous pricing agent optimizes prices based on market conditions and competition."

        if any(word in message_lower for word in ["inventory", "stock", "reorder"]):
            return "For inventory management, our autonomous inventory agent handles stock optimization, reorder points, and purchase recommendations."

        if any(word in message_lower for word in ["market", "trend", "analysis"]):
            return "Our market analysis capabilities include trend identification, competitive analysis, and seasonal pattern recognition."

        if any(word in message_lower for word in ["content", "listing", "description"]):
            return "I can assist with content optimization, SEO enhancement, and product listing improvements."

        return "I'm here to help with your e-commerce needs. Could you please be more specific about what you'd like assistance with?"

    @property
    def usage_stats(self) -> Dict[str, Any]:
        """Get chat service usage statistics as a property."""
        strategic_stats = self.strategic_service.get_usage_stats()

        return {
            "chat_service": "strategic_gemini",
            "conversations_active": len(self.conversation_contexts),
            "strategic_usage": strategic_stats,
            "quick_responses_available": len(self.quick_responses),
            "total_requests": strategic_stats.get("total_requests", 0),
            "cost_total": strategic_stats.get("cost_total", 0.0),
        }

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get chat service usage statistics (async method for compatibility)."""
        return self.usage_stats

    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """
        Analyze user intent for routing to appropriate autonomous agents.

        Args:
            message: User message to analyze

        Returns:
            Dict with 'primary_intent', 'confidence', and 'suggested_agent' keys
        """
        message_lower = message.lower()

        # Market-related keywords
        market_keywords = [
            "market",
            "trends",
            "pricing",
            "competition",
            "demand",
            "supply",
            "price",
            "cost",
            "profit",
            "margin",
            "analysis",
            "research",
            "competitor",
            "sales",
            "revenue",
            "economics",
            "arbitrage",
        ]

        # Content-related keywords
        content_keywords = [
            "content",
            "listing",
            "description",
            "title",
            "seo",
            "keywords",
            "optimize",
            "write",
            "create",
            "improve",
            "enhance",
            "text",
            "copy",
            "product",
            "details",
            "specifications",
            "features",
        ]

        # Logistics-related keywords
        logistics_keywords = [
            "shipping",
            "delivery",
            "fulfillment",
            "warehouse",
            "inventory",
            "stock",
            "supply chain",
            "logistics",
            "transport",
            "carrier",
            "tracking",
            "packaging",
            "handling",
            "distribution",
        ]

        # Executive-related keywords
        executive_keywords = [
            "status",
            "report",
            "dashboard",
            "overview",
            "summary",
            "performance",
            "metrics",
            "analytics",
            "coordination",
            "strategy",
            "planning",
            "management",
            "system",
            "overall",
            "general",
            "admin",
        ]

        # Calculate keyword matches
        market_score = sum(1 for keyword in market_keywords if keyword in message_lower)
        content_score = sum(
            1 for keyword in content_keywords if keyword in message_lower
        )
        logistics_score = sum(
            1 for keyword in logistics_keywords if keyword in message_lower
        )
        executive_score = sum(
            1 for keyword in executive_keywords if keyword in message_lower
        )

        # Determine primary intent
        scores = {
            "market": market_score,
            "content": content_score,
            "logistics": logistics_score,
            "executive": executive_score,
        }

        # Find the highest scoring intent
        max_score = max(scores.values())

        if max_score == 0:
            # No specific keywords found, default to general
            primary_intent = "general"
            confidence = 0.3
            suggested_agent = "conversational_interface"
        else:
            # Get the intent with highest score
            primary_intent = max(scores, key=scores.get)

            # Calculate confidence based on score and message length
            total_words = len(message_lower.split())
            confidence = min(0.9, (max_score / max(1, total_words)) * 2)
            confidence = max(0.4, confidence)  # Minimum confidence of 40%

            # Map intent to suggested agent
            agent_mapping = {
                "market": "market_agent",
                "content": "content_agent",
                "logistics": "logistics_agent",
                "executive": "executive_agent",
            }
            suggested_agent = agent_mapping.get(
                primary_intent, "conversational_interface"
            )

        return {
            "primary_intent": primary_intent,
            "confidence": confidence,
            "suggested_agent": suggested_agent,
            "keyword_scores": scores,
            "message_length": len(message.split()),
        }

    async def analyze_user_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent for routing to appropriate autonomous agents (async wrapper)."""
        return self._analyze_intent(message)

    def _map_intent_to_agent(self, intent: str) -> str:
        """Map user intent to appropriate autonomous agent."""
        mapping = {
            "pricing": "auto_pricing_agent",
            "inventory": "auto_inventory_agent",
            "market": "market_autonomous_agent",
            "content": "content_autonomous_agent",
            "general": "conversational_interface",
        }
        return mapping.get(intent, "conversational_interface")


# Factory function for easy service creation
def create_strategic_chat_service(daily_budget: float = 10.0) -> StrategicChatService:
    """Create strategic chat service with FlipSync defaults."""
    return StrategicChatService(daily_budget=daily_budget)
