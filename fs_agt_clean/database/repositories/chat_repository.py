"""
Chat Repository
===============

Repository pattern for chat-related database operations.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fs_agt_clean.database.base_repository import BaseRepository
from fs_agt_clean.database.models.chat import (
    ChatSession,
    Conversation,
    Message,
    MessageReaction,
)


class ChatRepository(BaseRepository):
    """Repository for chat-related database operations."""

    def __init__(self):
        # Initialize with Conversation as the primary model
        super().__init__(model_class=Conversation, table_name="conversations")

    async def create_conversation(
        self,
        session: AsyncSession,
        user_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            session: Database session
            user_id: ID of the user creating the conversation
            title: Optional title for the conversation
            metadata: Optional metadata for the conversation

        Returns:
            Created conversation
        """
        conversation = Conversation(
            user_id=uuid.UUID(user_id), title=title, extra_metadata=metadata or {}
        )

        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

        return conversation

    async def get_conversation(
        self,
        session: AsyncSession,
        conversation_id: str,
        include_messages: bool = False,
    ) -> Optional[Conversation]:
        """Get a conversation by ID.

        Args:
            session: Database session
            conversation_id: ID of the conversation
            include_messages: Whether to include messages in the result

        Returns:
            Conversation if found, None otherwise
        """
        query = select(Conversation).where(
            Conversation.id == uuid.UUID(conversation_id)
        )

        if include_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_conversations(
        self, session: AsyncSession, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """Get conversations for a user.

        Args:
            session: Database session
            user_id: ID of the user
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List of conversations
        """
        query = (
            select(Conversation)
            .where(Conversation.user_id == uuid.UUID(user_id))
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)
        return result.scalars().all()

    async def create_message(
        self,
        session: AsyncSession,
        conversation_id: str,
        content: str,
        sender: str,
        agent_type: Optional[str] = None,
        thread_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Create a new message.

        Args:
            session: Database session
            conversation_id: ID of the conversation
            content: Message content
            sender: Message sender ('user', 'agent', 'system')
            agent_type: Type of agent if sender is 'agent'
            thread_id: Optional thread ID for threading
            parent_id: Optional parent message ID for replies
            metadata: Optional metadata for the message

        Returns:
            Created message
        """
        message = Message(
            conversation_id=uuid.UUID(conversation_id),
            content=content,
            sender=sender,
            agent_type=agent_type,
            thread_id=uuid.UUID(thread_id) if thread_id else None,
            parent_id=uuid.UUID(parent_id) if parent_id else None,
            extra_metadata=metadata or {},
        )

        session.add(message)
        await session.commit()
        await session.refresh(message)

        # Update conversation's updated_at timestamp
        await session.execute(
            text(
                "UPDATE conversations SET updated_at = NOW() WHERE id = :conversation_id"
            ),
            {"conversation_id": conversation_id},
        )
        await session.commit()

        return message

    async def get_conversation_messages(
        self,
        session: AsyncSession,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
        include_reactions: bool = False,
    ) -> List[Message]:
        """Get messages for a conversation.

        Args:
            session: Database session
            conversation_id: ID of the conversation
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            include_reactions: Whether to include message reactions

        Returns:
            List of messages
        """
        query = (
            select(Message)
            .where(Message.conversation_id == uuid.UUID(conversation_id))
            .order_by(Message.timestamp)
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)
        return result.scalars().all()

    async def get_message(
        self, session: AsyncSession, message_id: str
    ) -> Optional[Message]:
        """Get a message by ID.

        Args:
            session: Database session
            message_id: ID of the message

        Returns:
            Message if found, None otherwise
        """
        query = select(Message).where(Message.id == uuid.UUID(message_id))
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_chat_session(
        self,
        session: AsyncSession,
        conversation_id: str,
        user_id: str,
        session_token: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatSession:
        """Create a new chat session.

        Args:
            session: Database session
            conversation_id: ID of the conversation
            user_id: ID of the user
            session_token: Unique session token
            metadata: Optional metadata for the session

        Returns:
            Created chat session
        """
        chat_session = ChatSession(
            conversation_id=uuid.UUID(conversation_id),
            user_id=uuid.UUID(user_id),
            session_token=session_token,
            extra_metadata=metadata or {},
        )

        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)

        return chat_session

    async def get_active_chat_sessions(
        self, session: AsyncSession, conversation_id: str
    ) -> List[ChatSession]:
        """Get active chat sessions for a conversation.

        Args:
            session: Database session
            conversation_id: ID of the conversation

        Returns:
            List of active chat sessions
        """
        query = (
            select(ChatSession)
            .where(
                ChatSession.conversation_id == uuid.UUID(conversation_id),
                ChatSession.is_active == "true",
            )
            .order_by(desc(ChatSession.last_activity))
        )

        result = await session.execute(query)
        return result.scalars().all()

    async def add_message_reaction(
        self, session: AsyncSession, message_id: str, user_id: str, reaction_type: str
    ) -> MessageReaction:
        """Add a reaction to a message.

        Args:
            session: Database session
            message_id: ID of the message
            user_id: ID of the user
            reaction_type: Type of reaction ('like', 'dislike', 'helpful', 'not_helpful')

        Returns:
            Created message reaction
        """
        # Remove existing reaction from this user for this message
        await session.execute(
            f"DELETE FROM message_reactions WHERE message_id = '{message_id}' AND user_id = '{user_id}'"
        )

        reaction = MessageReaction(
            message_id=uuid.UUID(message_id),
            user_id=uuid.UUID(user_id),
            reaction_type=reaction_type,
        )

        session.add(reaction)
        await session.commit()
        await session.refresh(reaction)

        return reaction

    async def get_conversation_stats(
        self, session: AsyncSession, conversation_id: str
    ) -> Dict[str, Any]:
        """Get statistics for a conversation.

        Args:
            session: Database session
            conversation_id: ID of the conversation

        Returns:
            Dictionary with conversation statistics
        """
        # Get message count
        message_count_query = select(func.count(Message.id)).where(
            Message.conversation_id == uuid.UUID(conversation_id)
        )
        message_count_result = await session.execute(message_count_query)
        message_count = message_count_result.scalar()

        # Get last message timestamp
        last_message_query = (
            select(Message.timestamp)
            .where(Message.conversation_id == uuid.UUID(conversation_id))
            .order_by(desc(Message.timestamp))
            .limit(1)
        )
        last_message_result = await session.execute(last_message_query)
        last_message_time = last_message_result.scalar()

        return {
            "message_count": message_count,
            "last_message_at": (
                last_message_time.isoformat() if last_message_time else None
            ),
        }
