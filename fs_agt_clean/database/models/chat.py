"""
Chat Database Models
===================

This module defines the database models for chat conversations and messages.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Conversation(Base):
    """Model for chat conversations."""

    __tablename__ = "conversations"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    extra_metadata = Column(JSON, nullable=True)

    # Relationship to messages
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', user_id={self.user_id})>"

    def to_dict(self):
        """Convert conversation to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.extra_metadata,
            "message_count": len(self.messages) if self.messages else 0,
        }


class Message(Base):
    """Model for chat messages."""

    __tablename__ = "messages"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    content = Column(Text, nullable=False)
    sender = Column(String(50), nullable=False)  # 'user', 'agent', 'system'
    agent_type = Column(
        String(50), nullable=True
    )  # 'market', 'executive', 'content', 'logistics', 'analytics'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    thread_id = Column(UUID(as_uuid=True), nullable=True)  # For threading/replies
    parent_id = Column(UUID(as_uuid=True), nullable=True)  # For reply chains
    extra_metadata = Column(JSON, nullable=True)

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, sender='{self.sender}', agent_type='{self.agent_type}')>"

    def to_dict(self):
        """Convert message to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "content": self.content,
            "sender": self.sender,
            "agent_type": self.agent_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "thread_id": str(self.thread_id) if self.thread_id else None,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "metadata": self.extra_metadata,
        }


class ChatSession(Base):
    """Model for chat sessions to track active conversations."""

    __tablename__ = "chat_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    is_active = Column(String(10), default="true")  # 'true', 'false'
    last_activity = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    extra_metadata = Column(JSON, nullable=True)

    # Relationship to conversation
    conversation = relationship("Conversation")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, conversation_id={self.conversation_id}, is_active={self.is_active})>"

    def to_dict(self):
        """Convert chat session to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "session_token": self.session_token,
            "is_active": self.is_active == "true",
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.extra_metadata,
        }


class MessageReaction(Base):
    """Model for message reactions (likes, dislikes, etc.)."""

    __tablename__ = "message_reactions"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    reaction_type = Column(
        String(20), nullable=False
    )  # 'like', 'dislike', 'helpful', 'not_helpful'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to message
    message = relationship("Message")

    def __repr__(self):
        return f"<MessageReaction(id={self.id}, message_id={self.message_id}, reaction_type='{self.reaction_type}')>"

    def to_dict(self):
        """Convert message reaction to dictionary."""
        return {
            "id": str(self.id),
            "message_id": str(self.message_id),
            "user_id": str(self.user_id),
            "reaction_type": self.reaction_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
