"""
UnifiedAgent Message Router for FlipSync UnifiedAgent Communication Protocol.

This module provides the infrastructure for structured inter-agent messaging
using the UnifiedAgentMessage protocol and event system integration.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from uuid import uuid4
import uuid

from fs_agt_clean.core.protocols.agent_protocol import (
    UnifiedAgentMessage,
    MessageType,
    Priority,
    UpdateMessage,
    AlertMessage,
    QueryMessage,
    CommandMessage,
    ResponseMessage,
)
from fs_agt_clean.core.coordination.event_system.in_memory_event_bus import (
    InMemoryEventBus,
)
from fs_agt_clean.core.coordination.event_system.publisher import InMemoryEventPublisher
from fs_agt_clean.core.coordination.event_system.subscriber import (
    InMemoryEventSubscriber,
)
from fs_agt_clean.core.coordination.event_system.event import (
    BaseEvent,
    EventType,
    EventMetadata,
)

logger = logging.getLogger(__name__)


class UnifiedAgentMessageRouter:
    """
    Router for agent-to-agent communication using the UnifiedAgentMessage protocol.

    This router integrates with the existing event system to provide structured
    messaging between agents in the FlipSync ecosystem.
    """

    def __init__(self, agent_manager=None):
        """
        Initialize the agent message router.

        Args:
            agent_manager: The agent manager instance for agent lookup
        """
        self.agent_manager = agent_manager
        self.event_bus = InMemoryEventBus(bus_id="agent_communication_bus")
        self.publishers: Dict[str, InMemoryEventPublisher] = {}
        self.subscribers: Dict[str, InMemoryEventSubscriber] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.active_conversations: Dict[str, List[UnifiedAgentMessage]] = {}
        self.message_history: List[UnifiedAgentMessage] = []

        logger.info("UnifiedAgent Message Router initialized")

    async def initialize(self) -> bool:
        """Initialize the message router."""
        try:
            logger.info("Initializing UnifiedAgent Message Router...")

            # Event bus is already initialized in constructor
            # Register default message handlers
            await self._register_default_handlers()

            logger.info("UnifiedAgent Message Router initialization completed")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize UnifiedAgent Message Router: {e}")
            return False

    async def register_agent(self, agent_id: str, message_handler: Callable) -> bool:
        """
        Register an agent for message routing.

        Args:
            agent_id: The unique identifier for the agent
            message_handler: Callback function to handle incoming messages

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Create publisher for the agent
            publisher = InMemoryEventPublisher(
                source_id=agent_id, event_bus=self.event_bus
            )
            self.publishers[agent_id] = publisher

            # Create subscriber for the agent
            subscriber = InMemoryEventSubscriber(
                subscriber_id=agent_id, event_bus=self.event_bus
            )

            # Subscribe to messages for this agent using the correct filter interface
            from fs_agt_clean.core.coordination.event_system.subscriber import (
                EventTypeFilter,
                EventNameFilter,
                CompositeFilter,
            )

            # Create filters for agent messages
            type_filter = EventTypeFilter({EventType.COMMAND})
            name_filter = EventNameFilter({"agent_message"})
            combined_filter = CompositeFilter(
                [type_filter, name_filter], require_all=True
            )

            await subscriber.subscribe(
                filter=combined_filter,
                handler=self._create_message_handler(agent_id, message_handler),
            )

            self.subscribers[agent_id] = subscriber
            self.message_handlers[agent_id] = message_handler

            logger.info(f"UnifiedAgent {agent_id} registered for message routing")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False

    async def send_message(self, message: UnifiedAgentMessage) -> bool:
        """
        Send a message from one agent to another.

        Args:
            message: The UnifiedAgentMessage to send

        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            # Validate message
            if not message.sender_id:
                logger.error("Message missing sender_id")
                return False

            if not message.receiver_id:
                logger.error("Message missing receiver_id")
                return False

            # Check if sender is registered
            if message.sender_id not in self.publishers:
                logger.error(f"Sender {message.sender_id} not registered")
                return False

            # Store message in history
            self.message_history.append(message)

            # Add to conversation if correlation_id exists
            if message.correlation_id:
                if message.correlation_id not in self.active_conversations:
                    self.active_conversations[message.correlation_id] = []
                self.active_conversations[message.correlation_id].append(message)

            # Convert UnifiedAgentMessage to Event
            event = self._convert_message_to_event(message)

            # Send via event bus
            publisher = self.publishers[message.sender_id]
            await publisher.publish(event)

            logger.info(
                f"Message sent from {message.sender_id} to {message.receiver_id} "
                f"(type: {message.message_type.value}, id: {message.message_id})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def broadcast_message(
        self, message: UnifiedAgentMessage, agent_category: Optional[str] = None
    ) -> int:
        """
        Broadcast a message to multiple agents.

        Args:
            message: The UnifiedAgentMessage to broadcast
            agent_category: Optional category filter for recipients

        Returns:
            Number of agents the message was sent to
        """
        try:
            recipients = []

            if self.agent_manager:
                # Get agents from agent manager
                for agent_id, agent_info in self.agent_manager.agents.items():
                    if agent_category and agent_info.get("type") != agent_category:
                        continue
                    if agent_info.get("status") == "active":
                        recipients.append(agent_id)
            else:
                # Use registered agents
                recipients = list(self.publishers.keys())

            sent_count = 0
            for recipient_id in recipients:
                if recipient_id != message.sender_id:  # Don't send to self
                    # Create a copy of the message for each recipient
                    recipient_message = UnifiedAgentMessage(
                        message_id=str(uuid4()),
                        message_type=message.message_type,
                        sender_id=message.sender_id,
                        receiver_id=recipient_id,
                        timestamp=message.timestamp,
                        content=message.content.copy(),
                        priority=message.priority,
                        correlation_id=message.correlation_id,
                        metadata=message.metadata.copy(),
                        action_required=message.action_required,
                    )

                    if await self.send_message(recipient_message):
                        sent_count += 1

            logger.info(f"Broadcast message sent to {sent_count} agents")
            return sent_count

        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            return 0

    def _convert_message_to_event(self, message: UnifiedAgentMessage) -> BaseEvent:
        """Convert an UnifiedAgentMessage to an Event for the event bus."""
        # Create metadata for the event
        metadata = EventMetadata(
            event_type=EventType.COMMAND,
            event_name="agent_message",
            source=message.sender_id,
            target=message.receiver_id,
            correlation_id=message.correlation_id or str(uuid4()),
            priority=message.priority.value,
        )

        # Create payload with agent message data
        payload = {
            "agent_message": {
                "message_id": message.message_id,
                "message_type": message.message_type.value,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "timestamp": message.timestamp.isoformat(),
                "content": message.content,
                "priority": message.priority.value,
                "correlation_id": message.correlation_id,
                "metadata": message.metadata,
                "action_required": message.action_required,
            }
        }

        return BaseEvent(payload=payload, metadata=metadata)

    def _convert_event_to_message(self, event: BaseEvent) -> UnifiedAgentMessage:
        """Convert an Event back to an UnifiedAgentMessage."""
        msg_data = event.payload["agent_message"]

        return UnifiedAgentMessage(
            message_id=msg_data["message_id"],
            message_type=MessageType(msg_data["message_type"]),
            sender_id=msg_data["sender_id"],
            receiver_id=msg_data["receiver_id"],
            timestamp=datetime.fromisoformat(msg_data["timestamp"]),
            content=msg_data["content"],
            priority=Priority(msg_data["priority"]),
            correlation_id=msg_data.get("correlation_id"),
            metadata=msg_data.get("metadata", {}),
            action_required=msg_data.get("action_required", False),
        )

    def _create_message_handler(self, agent_id: str, handler: Callable):
        """Create a message handler wrapper for the event system."""

        async def handle_event(event: BaseEvent):
            try:
                # Convert event back to UnifiedAgentMessage
                message = self._convert_event_to_message(event)

                # Call the agent's message handler
                response = await handler(message)

                # If handler returns a response message, send it
                if response and isinstance(response, UnifiedAgentMessage):
                    await self.send_message(response)

                logger.debug(f"Message handled by agent {agent_id}")

            except Exception as e:
                logger.error(f"Error handling message for agent {agent_id}: {e}")

        return handle_event

    async def _register_default_handlers(self):
        """Register default message handlers for system functionality."""
        # This can be extended with system-level message handlers
        pass

    async def get_conversation_history(self, correlation_id: str) -> List[UnifiedAgentMessage]:
        """Get the message history for a conversation."""
        return self.active_conversations.get(correlation_id, [])

    async def get_agent_message_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get message statistics for an agent."""
        sent_count = len(
            [msg for msg in self.message_history if msg.sender_id == agent_id]
        )
        received_count = len(
            [msg for msg in self.message_history if msg.receiver_id == agent_id]
        )

        return {
            "agent_id": agent_id,
            "messages_sent": sent_count,
            "messages_received": received_count,
            "is_registered": agent_id in self.publishers,
            "active_conversations": len(
                [
                    conv_id
                    for conv_id, messages in self.active_conversations.items()
                    if any(
                        msg.sender_id == agent_id or msg.receiver_id == agent_id
                        for msg in messages
                    )
                ]
            ),
        }

    async def shutdown(self):
        """Shutdown the message router and clean up resources."""
        try:
            # Close all subscribers
            for subscriber in self.subscribers.values():
                await subscriber.close()

            # Clear data structures
            self.publishers.clear()
            self.subscribers.clear()
            self.message_handlers.clear()
            self.active_conversations.clear()

            logger.info("UnifiedAgent Message Router shutdown completed")

        except Exception as e:
            logger.error(f"Error during message router shutdown: {e}")
