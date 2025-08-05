"""
Communication and Conversational Interface Services.

This module provides comprehensive communication capabilities including:
- Chatbot and conversational AI
- Intent recognition and natural language processing
- Context management for conversations
- UnifiedAgent connectivity and coordination
- Recommendation services
- Multi-channel communication support
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Import communication components
try:
    from .chat_service import ChatService
except ImportError:
    ChatService = None

try:
    from .agent_connectivity_service import UnifiedAgentConnectivityService
except ImportError:
    UnifiedAgentConnectivityService = None

try:
    from .context_manager import ContextManager
except ImportError:
    ContextManager = None

try:
    from .conversation_context_manager import ConversationContextManager
except ImportError:
    ConversationContextManager = None

try:
    from .conversation_service import ConversationService
except ImportError:
    ConversationService = None

try:
    from .intent_recognition import IntentRecognition
except ImportError:
    IntentRecognition = None

try:
    from .recommendation_service import RecommendationService
except ImportError:
    RecommendationService = None


class CommunicationService:
    """Main service for communication and conversational interfaces."""

    def __init__(self, config_manager=None):
        """Initialize the communication service."""
        self.config_manager = config_manager

        # Initialize components
        self.chat_service = ChatService() if ChatService else None
        self.agent_connectivity = (
            UnifiedAgentConnectivityService() if UnifiedAgentConnectivityService else None
        )
        self.context_manager = ContextManager() if ContextManager else None
        self.conversation_context = (
            ConversationContextManager() if ConversationContextManager else None
        )
        self.conversation_service = (
            ConversationService() if ConversationService else None
        )
        self.intent_recognition = IntentRecognition() if IntentRecognition else None
        self.recommendation_service = (
            RecommendationService() if RecommendationService else None
        )

    async def process_chat_message(
        self, user_id: str, message: str, conversation_id: Optional[str] = None
    ) -> Dict:
        """Process a chat message and generate response."""
        try:
            if not self.chat_service:
                return {"error": "Chat service not available"}

            # Process the message through chat service
            response = await self.chat_service.process_message(
                user_id, message, conversation_id
            )
            return response
        except Exception as e:
            logger.error("Failed to process chat message: %s", str(e))
            return {"error": str(e)}

    async def recognize_intent(self, message: str) -> Dict:
        """Recognize intent from user message."""
        try:
            if not self.intent_recognition:
                return {"intent": "unknown", "confidence": 0.0}

            intent_result = await self.intent_recognition.recognize(message)
            return intent_result
        except Exception as e:
            logger.error("Failed to recognize intent: %s", str(e))
            return {"intent": "unknown", "confidence": 0.0}

    async def get_recommendations(self, user_id: str, context: Dict) -> List[Dict]:
        """Get recommendations for user."""
        try:
            if not self.recommendation_service:
                return []

            recommendations = await self.recommendation_service.get_recommendations(
                user_id, context
            )
            return recommendations
        except Exception as e:
            logger.error("Failed to get recommendations: %s", str(e))
            return []

    async def manage_conversation_context(
        self, conversation_id: str, context_data: Dict
    ) -> bool:
        """Manage conversation context."""
        try:
            if not self.conversation_context:
                return False

            success = await self.conversation_context.update_context(
                conversation_id, context_data
            )
            return success
        except Exception as e:
            logger.error("Failed to manage conversation context: %s", str(e))
            return False

    async def connect_to_agent(self, user_id: str, agent_type: str) -> Dict:
        """Connect user to appropriate agent."""
        try:
            if not self.agent_connectivity:
                return {"connected": False, "error": "UnifiedAgent connectivity not available"}

            connection_result = await self.agent_connectivity.connect_user_to_agent(
                user_id, agent_type
            )
            return connection_result
        except Exception as e:
            logger.error("Failed to connect to agent: %s", str(e))
            return {"connected": False, "error": str(e)}


__all__ = [
    "CommunicationService",
    "ChatService",
    "UnifiedAgentConnectivityService",
    "ContextManager",
    "ConversationContextManager",
    "ConversationService",
    "IntentRecognition",
    "RecommendationService",
]
