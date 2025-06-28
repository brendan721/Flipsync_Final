"""
Real-time Service for FlipSync
==============================

This service provides high-level real-time communication capabilities
for the FlipSync application, integrating WebSocket management with
business logic and database operations.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.core.websocket.events import (
    UnifiedAgentType,
    EventType,
    SenderType,
    create_agent_status_event,
    create_error_event,
    create_message_event,
    create_system_alert_event,
    create_typing_event,
)
from fs_agt_clean.core.websocket.manager import websocket_manager
from fs_agt_clean.database.repositories.agent_repository import UnifiedAgentRepository
from fs_agt_clean.database.repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)


class RealtimeService:
    """High-level real-time communication service."""

    def __init__(self, database=None):
        # Initialize repositories as None - they will be created when needed
        self._chat_repository = None
        self._agent_repository = None
        self._database = database

        # Performance tracking
        self.message_latency_samples = []
        self.max_latency_samples = 1000

    @property
    def chat_repository(self):
        """Lazy initialization of chat repository."""
        if self._chat_repository is None:
            self._chat_repository = ChatRepository()
        return self._chat_repository

    @property
    def agent_repository(self):
        """Lazy initialization of agent repository."""
        if self._agent_repository is None:
            self._agent_repository = UnifiedAgentRepository()
        return self._agent_repository

    @property
    def database(self):
        """Get database instance."""
        if self._database is None:
            raise RuntimeError(
                "Database not initialized - RealtimeService requires database injection"
            )
        return self._database

    async def send_chat_message(
        self,
        conversation_id: str,
        content: str,
        sender: SenderType,
        agent_type: Optional[UnifiedAgentType] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session=None,
    ) -> Dict[str, Any]:
        """
        Send a chat message and broadcast it to conversation participants.

        Args:
            conversation_id: Target conversation ID
            content: Message content
            sender: Message sender type
            agent_type: UnifiedAgent type if sender is agent
            user_id: UnifiedUser ID if sender is user
            thread_id: Optional thread ID
            parent_id: Optional parent message ID
            metadata: Optional message metadata

        Returns:
            Dictionary with message details and delivery status
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Store message in database
            if session:
                # Use provided session
                db_message = await self.chat_repository.create_message(
                    session=session,
                    conversation_id=conversation_id,
                    content=content,
                    sender=sender.value,
                    agent_type=agent_type.value if agent_type else None,
                    thread_id=thread_id,
                    parent_id=parent_id,
                    metadata=metadata or {},
                )
            else:
                # Use own database session (fallback)
                async with self.database.get_session() as db_session:
                    db_message = await self.chat_repository.create_message(
                        session=db_session,
                        conversation_id=conversation_id,
                        content=content,
                        sender=sender.value,
                        agent_type=agent_type.value if agent_type else None,
                        thread_id=thread_id,
                        parent_id=parent_id,
                        metadata=metadata or {},
                    )

            # Create WebSocket event
            message_event = create_message_event(
                conversation_id=conversation_id,
                message_id=str(db_message.id),
                content=content,
                sender=sender,
                agent_type=agent_type,
                thread_id=thread_id,
                parent_id=parent_id,
                metadata=metadata,
            )

            # Broadcast to conversation participants
            recipients = await websocket_manager.send_to_conversation(
                conversation_id, message_event.dict()
            )

            # Track latency
            end_time = datetime.now(timezone.utc)
            latency_ms = (end_time - start_time).total_seconds() * 1000
            self._track_latency(latency_ms)

            logger.info(
                f"Message sent to conversation {conversation_id}: "
                f"{recipients} recipients, {latency_ms:.2f}ms latency"
            )

            return {
                "message_id": str(db_message.id),
                "conversation_id": conversation_id,
                "recipients": recipients,
                "latency_ms": latency_ms,
                "timestamp": db_message.timestamp.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
            raise

    async def send_typing_indicator(
        self,
        conversation_id: str,
        is_typing: bool,
        user_id: Optional[str] = None,
        agent_type: Optional[UnifiedAgentType] = None,
    ) -> int:
        """
        Send typing indicator to conversation participants.

        Args:
            conversation_id: Target conversation ID
            is_typing: Whether user/agent is typing
            user_id: UnifiedUser ID if user is typing
            agent_type: UnifiedAgent type if agent is typing

        Returns:
            Number of recipients
        """
        try:
            typing_event = create_typing_event(
                conversation_id=conversation_id,
                is_typing=is_typing,
                user_id=user_id,
                agent_type=agent_type,
            )

            recipients = await websocket_manager.send_to_conversation(
                conversation_id, typing_event.dict()
            )

            logger.debug(f"Typing indicator sent to {recipients} recipients")
            return recipients

        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")
            return 0

    async def broadcast_agent_status(
        self,
        agent_id: str,
        agent_type: UnifiedAgentType,
        status: str,
        metrics: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> int:
        """
        Broadcast agent status update to all connected clients.

        Args:
            agent_id: UnifiedAgent identifier
            agent_type: Type of agent
            status: Current status
            metrics: Optional performance metrics
            error_message: Optional error message

        Returns:
            Number of recipients
        """
        try:
            # Update database
            async with self.database.get_session() as session:
                await self.agent_repository.create_or_update_agent_status(
                    session=session,
                    agent_id=agent_id,
                    agent_type=agent_type.value,
                    status=status,
                    metrics=metrics,
                    config={},
                )

            # Create status event
            status_event = create_agent_status_event(
                agent_id=agent_id,
                agent_type=agent_type,
                status=status,
                metrics=metrics,
                error_message=error_message,
            )

            # Broadcast to all clients
            recipients = await websocket_manager.broadcast(status_event.dict())

            logger.info(
                f"UnifiedAgent status broadcasted: {agent_id} -> {status} ({recipients} recipients)"
            )
            return recipients

        except Exception as e:
            logger.error(f"Error broadcasting agent status: {e}")
            return 0

    async def send_system_alert(
        self,
        severity: str,
        title: str,
        message: str,
        source: str,
        action_required: bool = False,
        action_url: Optional[str] = None,
        target_users: Optional[List[str]] = None,
    ) -> int:
        """
        Send system alert to users.

        Args:
            severity: Alert severity level
            title: Alert title
            message: Alert message
            source: Alert source
            action_required: Whether action is required
            action_url: Optional action URL
            target_users: Optional list of target user IDs

        Returns:
            Number of recipients
        """
        try:
            alert_event = create_system_alert_event(
                severity=severity,
                title=title,
                message=message,
                source=source,
                action_required=action_required,
                action_url=action_url,
            )

            recipients = 0

            if target_users:
                # Send to specific users
                for user_id in target_users:
                    user_recipients = await websocket_manager.send_to_user(
                        user_id, alert_event.dict()
                    )
                    recipients += user_recipients
            else:
                # Broadcast to all clients
                recipients = await websocket_manager.broadcast(alert_event.dict())

            logger.info(f"System alert sent: {title} ({recipients} recipients)")
            return recipients

        except Exception as e:
            logger.error(f"Error sending system alert: {e}")
            return 0

    async def get_conversation_participants(self, conversation_id: str) -> List[str]:
        """Get list of clients connected to a conversation."""
        return websocket_manager.get_conversation_clients(conversation_id)

    async def get_user_connections(self, user_id: str) -> List[str]:
        """Get list of connections for a user."""
        return websocket_manager.get_user_clients(user_id)

    async def disconnect_user(
        self, user_id: str, reason: str = "admin_disconnect"
    ) -> int:
        """Disconnect all connections for a user."""
        client_ids = websocket_manager.get_user_clients(user_id)

        disconnected = 0
        for client_id in client_ids:
            if await websocket_manager.disconnect(client_id, reason):
                disconnected += 1

        logger.info(f"Disconnected {disconnected} connections for user {user_id}")
        return disconnected

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get real-time service performance metrics."""
        connection_stats = websocket_manager.get_connection_stats()

        # Calculate average latency
        avg_latency = 0
        if self.message_latency_samples:
            avg_latency = sum(self.message_latency_samples) / len(
                self.message_latency_samples
            )

        return {
            **connection_stats,
            "average_latency_ms": round(avg_latency, 2),
            "latency_samples": len(self.message_latency_samples),
            "service_status": "operational",
        }

    def _track_latency(self, latency_ms: float):
        """Track message latency for performance monitoring."""
        self.message_latency_samples.append(latency_ms)

        # Keep only recent samples
        if len(self.message_latency_samples) > self.max_latency_samples:
            self.message_latency_samples = self.message_latency_samples[
                -self.max_latency_samples :
            ]

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the real-time service."""
        try:
            stats = websocket_manager.get_connection_stats()

            # Test database connectivity
            database_healthy = True
            try:
                async with self.database.get_session() as session:
                    # Simple query to test database
                    await session.execute("SELECT 1")
            except Exception as e:
                database_healthy = False
                logger.error(f"Database health check failed: {e}")

            # Calculate health score
            health_score = 100
            if not database_healthy:
                health_score -= 50

            if (
                stats["errors"] > stats["messages_sent"] * 0.1
            ):  # More than 10% error rate
                health_score -= 30

            status = (
                "healthy"
                if health_score >= 80
                else "degraded" if health_score >= 50 else "unhealthy"
            )

            return {
                "status": status,
                "health_score": health_score,
                "database_healthy": database_healthy,
                "websocket_stats": stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "health_score": 0,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# Global service instance - will be initialized with database in main.py
realtime_service = None
