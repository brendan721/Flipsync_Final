"""
UnifiedAgent connectivity service for the FlipSync chatbot.

This module provides the connectivity layer between the chatbot interface
and the specialized agent services, handling intent recognition, agent routing,
and response formatting.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from fs_agt_clean.core.models.chat import UnifiedAgentResponse, ChatMessage, MessageIntent
from fs_agt_clean.core.models.recommendation import ChatRecommendationContext
from fs_agt_clean.core.services.agent_service import UnifiedAgentService
from fs_agt_clean.services.chatbot.intent_recognition import IntentRecognizer
from fs_agt_clean.services.chatbot.recommendation_service import (
    ChatbotRecommendationService,
)

# Configure logging
logger = logging.getLogger(__name__)


class UnifiedAgentConnectivityService:
    """
    Service for connecting the chatbot interface with specialized agent services.

    This service handles:
    - Routing messages to appropriate agent services based on intent
    - Formatting responses from agents for the chatbot interface
    - Handling errors and fallbacks when agent services are unavailable
    - Providing context and history to agent services
    """

    def __init__(
        self,
        intent_recognizer: IntentRecognizer,
        recommendation_service: Optional[ChatbotRecommendationService] = None,
        agent_services: Optional[Dict[str, UnifiedAgentService]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the agent connectivity service.

        Args:
            intent_recognizer: Service for recognizing user intents
            recommendation_service: Optional service for generating recommendations
            agent_services: Dictionary mapping agent types to agent services
            config: Configuration options
        """
        self.intent_recognizer = intent_recognizer
        self.recommendation_service = recommendation_service
        self.agent_services = agent_services or {}
        self.config = config or {}

        # Load response templates
        self._response_templates = self.config.get("response_templates", {})
        if not self._response_templates:
            self._load_default_templates()

        # Configure timeouts
        self.request_timeout = self.config.get("request_timeout", 10.0)  # seconds

        logger.info(
            "UnifiedAgent connectivity service initialized with %d agent services",
            len(self.agent_services),
        )

    def _load_default_templates(self) -> None:
        """Load default response templates."""
        self._response_templates = {
            "default": {
                "greeting": "Hello! How can I help you today?",
                "farewell": "Thank you for chatting. Have a great day!",
                "error": "I'm sorry, but I encountered an error processing your request.",
                "not_understood": "I'm not sure I understand. Could you rephrase that?",
                "thinking": "Let me think about that...",
                "no_agent": "I don't have an agent that can help with that right now.",
            },
            "listing_agent": {
                "greeting": "Hello! I can help you with listing products on marketplaces.",
                "error": "I encountered an issue with the listing process. Please try again.",
                "success": "Your product has been successfully listed!",
            },
            "pricing_agent": {
                "greeting": "Hello! I can help you optimize your product pricing.",
                "error": "I encountered an issue with the pricing analysis. Please try again.",
                "success": "I've analyzed the market and have pricing recommendations for you.",
            },
            "inventory_agent": {
                "greeting": "Hello! I can help you manage your inventory.",
                "error": "I encountered an issue with the inventory management. Please try again.",
                "success": "Your inventory has been updated successfully.",
            },
            "customer_service_agent": {
                "greeting": "Hello! I can help you with customer service inquiries.",
                "error": "I encountered an issue processing your customer service request. Please try again.",
                "success": "I've processed your customer service request successfully.",
            },
        }

    def register_agent_service(self, agent_type: str, service: UnifiedAgentService) -> None:
        """
        Register an agent service.

        Args:
            agent_type: Type of agent service
            service: UnifiedAgent service instance
        """
        self.agent_services[agent_type] = service
        logger.info("Registered agent service: %s", agent_type)

    def unregister_agent_service(self, agent_type: str) -> bool:
        """
        Unregister an agent service.

        Args:
            agent_type: Type of agent service to unregister

        Returns:
            True if the service was unregistered, False otherwise
        """
        if agent_type in self.agent_services:
            del self.agent_services[agent_type]
            logger.info("Unregistered agent service: %s", agent_type)
            return True
        return False

    async def process_message(
        self,
        message: ChatMessage,
        conversation_history: Optional[List[ChatMessage]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> UnifiedAgentResponse:
        """
        Process a user message and route it to the appropriate agent service.

        Args:
            message: UnifiedUser message to process
            conversation_history: Optional conversation history
            context: Optional context information

        Returns:
            UnifiedAgent response
        """
        try:
            # Recognize intent
            intent = await self.intent_recognizer.recognize_intent(
                message.text,
                conversation_history=conversation_history,
                context=context,
            )

            # Determine agent type from intent
            agent_type = self._get_agent_type_for_intent(intent)

            # Check if we have a service for this agent type
            if agent_type and agent_type in self.agent_services:
                # Route to appropriate agent service
                agent_service = self.agent_services[agent_type]

                # Process message with agent service
                response = await agent_service.process_message(
                    message=message,
                    intent=intent,
                    conversation_history=conversation_history,
                    context=context,
                )

                # Add recommendations if available
                if self.recommendation_service and context:
                    recommendation_context = ChatRecommendationContext(
                        user_id=message.user_id,
                        message=message.text,
                        intent=intent,
                        agent_response=response,
                        context=context,
                    )
                    recommendations = (
                        await self.recommendation_service.get_recommendations(
                            recommendation_context
                        )
                    )
                    if recommendations:
                        response.recommendations = recommendations

                return response
            else:
                # No agent service available for this intent
                logger.warning(
                    "No agent service available for intent: %s (agent type: %s)",
                    intent.intent_type,
                    agent_type,
                )
                return UnifiedAgentResponse(
                    text=self._response_templates.get("default", {}).get(
                        "no_agent",
                        "I don't have an agent that can help with that right now.",
                    ),
                    metadata={
                        "intent": intent.to_dict() if intent else None,
                        "agent_type": agent_type,
                        "error": "no_agent_available",
                    },
                )
        except Exception as e:
            # Handle errors
            logger.error("Error processing message: %s", str(e), exc_info=True)
            return UnifiedAgentResponse(
                text=self._response_templates.get(agent_type, {}).get(
                    "error",
                    "I'm having trouble processing your request. Please try again.",
                ),
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    def _get_agent_type_for_intent(self, intent: MessageIntent) -> Optional[str]:
        """
        Determine the agent type for a given intent.

        Args:
            intent: Message intent

        Returns:
            UnifiedAgent type, or None if no matching agent type
        """
        # Map intent types to agent types
        intent_to_agent_map = {
            "listing": "listing_agent",
            "pricing": "pricing_agent",
            "inventory": "inventory_agent",
            "customer_service": "customer_service_agent",
            "order": "order_agent",
            "shipping": "shipping_agent",
            "returns": "returns_agent",
            "product_research": "research_agent",
            "analytics": "analytics_agent",
            "help": "help_agent",
            "greeting": "greeting_agent",
            "farewell": "farewell_agent",
        }

        # Check for direct mapping
        if intent.intent_type in intent_to_agent_map:
            return intent_to_agent_map[intent.intent_type]

        # Check for intent type prefix matches
        for intent_prefix, agent_type in intent_to_agent_map.items():
            if intent.intent_type.startswith(intent_prefix + "_"):
                return agent_type

        # Check for entity-based routing
        if intent.entities:
            for entity in intent.entities:
                if entity.entity_type == "agent_type" and entity.value:
                    return entity.value

        # Default to None if no matching agent type
        return None

    async def get_agent_status(
        self, agent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the status of agent services.

        Args:
            agent_type: Optional agent type to get status for

        Returns:
            Dictionary of agent statuses
        """
        result = {}

        if agent_type:
            # Get status for specific agent type
            if agent_type in self.agent_services:
                service = self.agent_services[agent_type]
                try:
                    status = await service.get_status()
                    result[agent_type] = status
                except Exception as e:
                    logger.error(
                        "Error getting status for agent %s: %s", agent_type, str(e)
                    )
                    result[agent_type] = {"status": "error", "error": str(e)}
            else:
                result[agent_type] = {"status": "not_found"}
        else:
            # Get status for all agent types
            for agent_type, service in self.agent_services.items():
                try:
                    status = await service.get_status()
                    result[agent_type] = status
                except Exception as e:
                    logger.error(
                        "Error getting status for agent %s: %s", agent_type, str(e)
                    )
                    result[agent_type] = {"status": "error", "error": str(e)}

        return result
