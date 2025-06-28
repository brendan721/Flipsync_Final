"""
Chat models for FlipSync.

This module provides data models for chat functionality including
messages, intents, responses, and entities.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MessageEntity:
    """Represents an entity extracted from a message."""

    entity_type: str
    value: str
    confidence: float = 0.0
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entity_type": self.entity_type,
            "value": self.value,
            "confidence": self.confidence,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "metadata": self.metadata,
        }


@dataclass
class MessageIntent:
    """Represents the intent of a user message."""

    intent_type: str
    confidence: float = 0.0
    entities: List[MessageEntity] = field(default_factory=list)
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "intent_type": self.intent_type,
            "confidence": self.confidence,
            "entities": [entity.to_dict() for entity in self.entities],
            "reasoning": self.reasoning,
            "metadata": self.metadata,
        }


@dataclass
class ChatMessage:
    """Represents a chat message."""

    user_id: str
    text: str
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    message_type: str = "user"  # user, agent, system
    intent: Optional[MessageIntent] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values after creation."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.message_id is None:
            self.message_id = f"msg_{self.timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message_id": self.message_id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "text": self.text,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "intent": self.intent.to_dict() if self.intent else None,
            "metadata": self.metadata,
        }


@dataclass
class UnifiedAgentResponse:
    """Represents a response from an agent."""

    text: str
    agent_type: Optional[str] = None
    confidence: float = 1.0
    response_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default values after creation."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.response_id is None:
            self.response_id = f"resp_{self.timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "response_id": self.response_id,
            "text": self.text,
            "agent_type": self.agent_type,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata,
            "recommendations": self.recommendations,
            "actions": self.actions,
        }


@dataclass
class ConversationContext:
    """Represents the context of a conversation."""

    conversation_id: str
    user_id: str
    current_agent: Optional[str] = None
    session_data: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[ChatMessage] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after creation."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append(message)
        self.updated_at = datetime.now()

    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """Get recent messages from the conversation."""
        return self.conversation_history[-limit:] if self.conversation_history else []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "current_agent": self.current_agent,
            "session_data": self.session_data,
            "conversation_history": [
                msg.to_dict() for msg in self.conversation_history
            ],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
