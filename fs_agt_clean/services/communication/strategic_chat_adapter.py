"""
Strategic Chat Service Adapter for FlipSync
==========================================

Adapts the StrategicChatService to work with existing API interfaces
while maintaining the 4+1 architecture and Gemini-exclusive conversational interface.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fs_agt_clean.core.websocket.events import SenderType, UnifiedAgentType
from fs_agt_clean.database.repositories.chat_repository import ChatRepository
from fs_agt_clean.services.communication.strategic_chat_service import (
    StrategicChatService,
    ChatRequest,
    ChatResponse,
)

logger = logging.getLogger(__name__)


class StrategicChatAdapter:
    """
    Adapter that bridges StrategicChatService with existing API interfaces.
    
    This adapter maintains compatibility with existing chat API endpoints
    while using the sophisticated strategic chat system underneath.
    """
    
    def __init__(self, strategic_service: StrategicChatService, database=None):
        """Initialize the strategic chat adapter."""
        self.strategic_service = strategic_service
        self.database = database
        self.chat_repository = ChatRepository() if database else None
        logger.info("Strategic chat adapter initialized")
    
    async def send_message(
        self,
        conversation_id: str,
        content: str,
        sender: SenderType,
        user_id: Optional[str] = None,
        agent_type: Optional[UnifiedAgentType] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a chat message (compatible with basic ChatService interface)."""
        message_id = str(uuid4())
        timestamp = datetime.now(timezone.utc)
        
        message_data = {
            "id": message_id,
            "conversation_id": conversation_id,
            "content": content,
            "sender": sender.value if hasattr(sender, 'value') else str(sender),
            "user_id": user_id,
            "agent_type": agent_type.value if agent_type and hasattr(agent_type, 'value') else str(agent_type) if agent_type else None,
            "timestamp": timestamp.isoformat(),
            "metadata": metadata or {}
        }
        
        # Store in database if available
        if self.chat_repository:
            try:
                await self.chat_repository.create_message(message_data)
            except Exception as e:
                logger.warning(f"Failed to store message in database: {e}")
        
        return message_data
    
    async def process_chat_message(
        self,
        conversation_id: str,
        message: str,
        user_id: str,
        routing_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a chat message using strategic chat service."""
        start_time = time.perf_counter()
        
        try:
            # Store user message
            user_message = await self.send_message(
                conversation_id=conversation_id,
                content=message,
                sender=SenderType.USER,
                user_id=user_id
            )
            
            # Create strategic chat request
            chat_request = ChatRequest(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                context=routing_info or {},
                priority="normal"
            )
            
            # Get strategic response
            strategic_response = await self.strategic_service.handle_chat(chat_request)
            
            # Store agent response
            agent_message = await self.send_message(
                conversation_id=conversation_id,
                content=strategic_response.content,
                sender=SenderType.AGENT,
                agent_type=UnifiedAgentType.ASSISTANT,  # Conversational interface
                metadata={
                    "response_time": strategic_response.response_time,
                    "confidence": strategic_response.confidence,
                    "cost_estimate": strategic_response.cost_estimate,
                    "strategic_llm_used": strategic_response.metadata.get("strategic_llm_used", False),
                    "response_type": strategic_response.metadata.get("response_type", "strategic_response")
                }
            )
            
            return {
                "user_message": user_message,
                "agent_response": agent_message,
                "processing_time": time.perf_counter() - start_time,
                "strategic_metadata": {
                    "confidence": strategic_response.confidence,
                    "cost_estimate": strategic_response.cost_estimate,
                    "response_type": strategic_response.metadata.get("response_type", "strategic_response")
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing strategic chat message: {e}")
            return {
                "error": str(e),
                "processing_time": time.perf_counter() - start_time
            }
    
    async def handle_message_enhanced(
        self,
        user_id: str,
        message: str,
        conversation_id: str,
        app_context: str = "flipsync_web"
    ) -> Dict[str, Any]:
        """Enhanced message handling (compatible with existing API)."""
        try:
            # Create strategic chat request with app context
            chat_request = ChatRequest(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                context={"app_context": app_context},
                priority="normal"
            )
            
            # Get strategic response
            strategic_response = await self.strategic_service.handle_chat(chat_request)
            
            return {
                "response": strategic_response.content,
                "agent_type": "conversational_interface",
                "confidence": strategic_response.confidence,
                "response_time": strategic_response.response_time,
                "cost_estimate": strategic_response.cost_estimate,
                "metadata": strategic_response.metadata
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced message handling: {e}")
            return {
                "response": "I'm experiencing some technical difficulties. Please try again in a moment.",
                "agent_type": "conversational_interface",
                "confidence": 0.1,
                "error": str(e)
            }
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        if self.chat_repository:
            try:
                return await self.chat_repository.get_conversation_messages(
                    conversation_id, limit, offset
                )
            except Exception as e:
                logger.warning(f"Failed to get messages from database: {e}")
        
        return []
    
    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new conversation."""
        conversation_id = str(uuid4())
        
        conversation_data = {
            "id": conversation_id,
            "user_id": user_id,
            "title": title or f"Conversation {conversation_id[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        
        # Store in database if available
        if self.chat_repository:
            try:
                await self.chat_repository.create_conversation(conversation_data)
            except Exception as e:
                logger.warning(f"Failed to store conversation in database: {e}")
        
        return conversation_id
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get conversations for a user."""
        if self.chat_repository:
            try:
                return await self.chat_repository.get_user_conversations(
                    user_id, limit, offset
                )
            except Exception as e:
                logger.warning(f"Failed to get conversations from database: {e}")
        
        return []
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get strategic chat service usage statistics."""
        strategic_stats = await self.strategic_service.get_usage_stats()
        
        return {
            "service_type": "strategic_chat_adapter",
            "strategic_chat_stats": strategic_stats,
            "database_enabled": self.chat_repository is not None,
            "adapter_version": "1.0.0"
        }
