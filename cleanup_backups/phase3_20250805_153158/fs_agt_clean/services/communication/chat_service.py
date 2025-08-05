"""
Chat Service for FlipSync Conversational Interface
================================================

Provides chat functionality with agent integration and database persistence.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.websocket.events import SenderType, AutonomousAgentType
from fs_agt_clean.database.repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)


class ChatService:
    """Base chat service for FlipSync."""
    
    def __init__(self, database: Database = None):
        """Initialize chat service."""
        self.database = database
        self.chat_repository = ChatRepository() if database else None
        logger.info("Chat service initialized")
    
    async def send_message(
        self,
        conversation_id: str,
        content: str,
        sender: SenderType,
        user_id: Optional[str] = None,
        agent_type: Optional[AutonomousAgentType] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a chat message."""
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


class EnhancedChatService(ChatService):
    """Enhanced chat service with agent integration."""
    
    def __init__(self, database: Database = None, app=None):
        """Initialize enhanced chat service."""
        super().__init__(database)
        self.app = app
        self.agent_manager = None
        self.conversation_contexts = {}
        logger.info("Enhanced chat service initialized")
    
    async def process_chat_message(
        self,
        conversation_id: str,
        message: str,
        user_id: str,
        routing_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a chat message with agent integration."""
        start_time = time.perf_counter()
        
        try:
            # Store user message
            user_message = await self.send_message(
                conversation_id=conversation_id,
                content=message,
                sender=SenderType.USER,
                user_id=user_id
            )
            
            # Generate agent response (simplified for now)
            response_content = await self._generate_response(message, conversation_id, user_id)
            
            # Store agent response
            agent_message = await self.send_message(
                conversation_id=conversation_id,
                content=response_content,
                sender=SenderType.AGENT,
                agent_type=AutonomousAgentType.MARKET,  # Default to market agent
                metadata={"response_time": time.perf_counter() - start_time}
            )
            
            return {
                "user_message": user_message,
                "agent_response": agent_message,
                "processing_time": time.perf_counter() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                "error": str(e),
                "processing_time": time.perf_counter() - start_time
            }
    
    async def _generate_response(
        self,
        message: str,
        conversation_id: str,
        user_id: str
    ) -> str:
        """Generate a response to the user message."""
        # Simple response generation for now
        # In production, this would integrate with the agent system
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "Hello! I'm FlipSync's AI assistant. How can I help you with your e-commerce needs today?"
        elif any(word in message_lower for word in ["help", "support"]):
            return "I can help you with pricing strategies, inventory management, market analysis, and product optimization. What would you like to know?"
        elif any(word in message_lower for word in ["status", "health"]):
            return "FlipSync systems are running optimally. All autonomous agents are active and processing decisions."
        elif any(word in message_lower for word in ["price", "pricing"]):
            return "I can help you analyze pricing strategies and market trends. Would you like me to analyze a specific product or market segment?"
        else:
            return f"I understand you're asking about: '{message}'. Let me connect you with the appropriate agent to provide detailed assistance."
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history with context."""
        messages = await self.get_conversation_messages(conversation_id, limit)
        
        # Add context information
        for message in messages:
            if message.get("sender") == "agent" and message.get("agent_type"):
                message["agent_info"] = {
                    "type": message["agent_type"],
                    "capabilities": self._get_agent_capabilities(message["agent_type"])
                }
        
        return messages
    
    def _get_agent_capabilities(self, agent_type: str) -> List[str]:
        """Get capabilities for an agent type."""
        capabilities_map = {
            "market": ["Market analysis", "Pricing strategies", "Competitor research"],
            "content": ["Content optimization", "SEO enhancement", "Product descriptions"],
            "logistics": ["Shipping optimization", "Inventory management", "Cost analysis"],
            "executive": ["Strategic decisions", "Performance monitoring", "Resource allocation"]
        }
        
        return capabilities_map.get(agent_type, ["General assistance"])
    
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
