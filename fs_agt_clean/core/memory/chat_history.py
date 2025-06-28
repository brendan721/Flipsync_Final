"""
Chat history management for FlipSync.

This module provides chat history management capabilities
for maintaining conversation context and memory.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """
    Legacy chat history manager for backward compatibility.

    This class provides basic chat history management capabilities
    that are used by the chat service for legacy support.
    """

    def __init__(self):
        """Initialize the chat history manager."""
        self.chat_histories: Dict[str, List[Dict[str, Any]]] = {}
        self.initialized = True
        logger.info("ChatHistoryManager initialized for legacy support")

    def add_message(
        self,
        conversation_id: str,
        user_id: str,
        message: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message and response to chat history.

        Args:
            conversation_id: Conversation identifier
            user_id: UnifiedUser identifier
            message: UnifiedUser message
            response: System response
            metadata: Optional metadata
        """
        try:
            if conversation_id not in self.chat_histories:
                self.chat_histories[conversation_id] = []

            entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "message": message,
                "response": response,
                "metadata": metadata or {},
            }

            self.chat_histories[conversation_id].append(entry)
            logger.debug(
                f"Added message to chat history for conversation {conversation_id}"
            )

        except Exception as e:
            logger.error(f"Error adding message to chat history: {e}")

    def get_history(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a conversation.

        Args:
            conversation_id: Conversation identifier
            limit: Optional limit on number of messages

        Returns:
            List of chat history entries
        """
        try:
            history = self.chat_histories.get(conversation_id, [])
            if limit:
                history = history[-limit:]
            return history

        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    def clear_history(self, conversation_id: str) -> None:
        """
        Clear chat history for a conversation.

        Args:
            conversation_id: Conversation identifier
        """
        try:
            if conversation_id in self.chat_histories:
                del self.chat_histories[conversation_id]
                logger.info(f"Cleared chat history for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Error clearing chat history: {e}")
