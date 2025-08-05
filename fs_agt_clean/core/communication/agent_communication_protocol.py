"""
FlipSync Agent Communication Protocol
====================================

Implements secure, efficient communication between autonomous agents and
the conversational interface while maintaining 4+1 architecture separation.

Key Features:
- Message routing between autonomous agents
- Conversational interface control of autonomous agents
- Performance monitoring (<200ms communication targets)
- Architecture compliance enforcement
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timezone

from fs_agt_clean.core.architecture.boundaries import (
    ArchitecturalBoundaries,
    validate_agent_communication,
)

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of messages in the communication protocol."""

    COMMAND = "command"
    QUERY = "query"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    COORDINATION = "coordination"
    STATUS = "status"


class MessagePriority(str, Enum):
    """Message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AgentMessage:
    """Standard message format for agent communication."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_agent: str = ""
    recipient_agent: str = ""
    message_type: MessageType = MessageType.QUERY
    priority: MessagePriority = MessagePriority.NORMAL
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    timeout_seconds: float = 30.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "id": self.id,
            "sender_agent": self.sender_agent,
            "recipient_agent": self.recipient_agent,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary format."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            sender_agent=data.get("sender_agent", ""),
            recipient_agent=data.get("recipient_agent", ""),
            message_type=MessageType(data.get("message_type", MessageType.QUERY.value)),
            priority=MessagePriority(
                data.get("priority", MessagePriority.NORMAL.value)
            ),
            content=data.get("content", {}),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.now(timezone.utc).isoformat())
            ),
            correlation_id=data.get("correlation_id"),
            timeout_seconds=data.get("timeout_seconds", 30.0),
        )


@dataclass
class CommunicationMetrics:
    """Communication performance metrics."""

    total_messages: int = 0
    successful_messages: int = 0
    failed_messages: int = 0
    average_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float("inf")
    architecture_violations: int = 0

    def add_message_timing(self, response_time: float, success: bool = True):
        """Add timing data for a message."""
        self.total_messages += 1

        if success:
            self.successful_messages += 1
        else:
            self.failed_messages += 1

        if response_time > 0:
            self.max_response_time = max(self.max_response_time, response_time)
            self.min_response_time = min(self.min_response_time, response_time)

            # Update average (simple moving average)
            total_successful = self.successful_messages
            if total_successful > 0:
                self.average_response_time = (
                    self.average_response_time * (total_successful - 1) + response_time
                ) / total_successful

    def get_success_rate(self) -> float:
        """Get message success rate as percentage."""
        if self.total_messages == 0:
            return 0.0
        return (self.successful_messages / self.total_messages) * 100.0


class AgentCommunicationProtocol:
    """
    Central communication protocol for FlipSync 4+1 architecture.

    Handles message routing, validation, and performance monitoring
    while enforcing architectural boundaries.
    """

    def __init__(self):
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_messages: Dict[str, AgentMessage] = {}
        self.metrics = CommunicationMetrics()
        self.boundaries = ArchitecturalBoundaries()

    def register_agent_handler(self, agent_id: str, handler: Callable):
        """Register a message handler for an agent."""
        # Validate that the agent is a known agent in the 4+1 architecture
        agent_layer = self.boundaries.validate_agent_type(agent_id)
        if agent_layer.value == "unknown":
            logger.error(f"Cannot register handler for unknown agent: {agent_id}")
            self.metrics.architecture_violations += 1
            return False

        self.message_handlers[agent_id] = handler
        logger.info(f"Registered message handler for agent: {agent_id}")
        return True

    async def send_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Send a message between agents with architecture validation.

        Returns response message if successful, None if failed.
        """
        start_time = time.perf_counter()

        try:
            # Validate architecture compliance
            if not validate_agent_communication(
                message.sender_agent, message.recipient_agent
            ):
                logger.error(
                    f"Architecture violation: {message.sender_agent} -> {message.recipient_agent}"
                )
                self.metrics.architecture_violations += 1
                self.metrics.add_message_timing(0, success=False)
                return None

            # Check if recipient handler exists
            if message.recipient_agent not in self.message_handlers:
                logger.error(
                    f"No handler registered for recipient: {message.recipient_agent}"
                )
                self.metrics.add_message_timing(0, success=False)
                return None

            # Store pending message for correlation
            self.pending_messages[message.id] = message

            # Route message to handler
            handler = self.message_handlers[message.recipient_agent]

            try:
                # Call handler with timeout
                response = await asyncio.wait_for(
                    handler(message), timeout=message.timeout_seconds
                )

                # Calculate response time
                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000

                # Update metrics
                self.metrics.add_message_timing(response_time_ms, success=True)

                # Clean up pending message
                self.pending_messages.pop(message.id, None)

                # Validate response format
                if isinstance(response, AgentMessage):
                    response.correlation_id = message.id
                    logger.debug(
                        f"Message sent successfully: {message.sender_agent} -> {message.recipient_agent} ({response_time_ms:.1f}ms)"
                    )
                    return response
                else:
                    # Convert response to AgentMessage format
                    response_message = AgentMessage(
                        sender_agent=message.recipient_agent,
                        recipient_agent=message.sender_agent,
                        message_type=MessageType.RESPONSE,
                        content={"response": response} if response is not None else {},
                        correlation_id=message.id,
                    )
                    return response_message

            except asyncio.TimeoutError:
                logger.error(
                    f"Message timeout: {message.sender_agent} -> {message.recipient_agent}"
                )
                self.metrics.add_message_timing(
                    message.timeout_seconds * 1000, success=False
                )
                return None

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000
            self.metrics.add_message_timing(response_time_ms, success=False)
            return None
        finally:
            # Clean up pending message
            self.pending_messages.pop(message.id, None)

    async def broadcast_message(
        self,
        sender_agent: str,
        message_content: Dict[str, Any],
        message_type: MessageType = MessageType.NOTIFICATION,
    ) -> List[AgentMessage]:
        """
        Broadcast a message to all registered agents.

        Returns list of responses from agents.
        """
        responses = []

        for agent_id in self.message_handlers.keys():
            if agent_id != sender_agent:  # Don't send to self
                message = AgentMessage(
                    sender_agent=sender_agent,
                    recipient_agent=agent_id,
                    message_type=message_type,
                    content=message_content,
                )

                response = await self.send_message(message)
                if response:
                    responses.append(response)

        return responses

    def get_communication_metrics(self) -> Dict[str, Any]:
        """Get current communication metrics."""
        return {
            "total_messages": self.metrics.total_messages,
            "successful_messages": self.metrics.successful_messages,
            "failed_messages": self.metrics.failed_messages,
            "success_rate": self.metrics.get_success_rate(),
            "average_response_time_ms": self.metrics.average_response_time,
            "max_response_time_ms": self.metrics.max_response_time,
            "min_response_time_ms": (
                self.metrics.min_response_time
                if self.metrics.min_response_time != float("inf")
                else 0
            ),
            "architecture_violations": self.metrics.architecture_violations,
            "registered_agents": len(self.message_handlers),
            "pending_messages": len(self.pending_messages),
        }

    def validate_architecture_compliance(self) -> Dict[str, Any]:
        """Validate current communication setup against 4+1 architecture."""
        registered_agents = list(self.message_handlers.keys())

        autonomous_agents = []
        conversational_agents = []
        unknown_agents = []

        for agent_id in registered_agents:
            layer = self.boundaries.validate_agent_type(agent_id)
            if layer.value == "autonomous":
                autonomous_agents.append(agent_id)
            elif layer.value == "conversational":
                conversational_agents.append(agent_id)
            else:
                unknown_agents.append(agent_id)

        compliance_report = {
            "compliant": len(unknown_agents) == 0 and len(conversational_agents) <= 1,
            "registered_agents": len(registered_agents),
            "autonomous_agents": len(autonomous_agents),
            "conversational_agents": len(conversational_agents),
            "unknown_agents": len(unknown_agents),
            "architecture_violations": self.metrics.architecture_violations,
            "agent_breakdown": {
                "autonomous": autonomous_agents,
                "conversational": conversational_agents,
                "unknown": unknown_agents,
            },
        }

        return compliance_report


# Global communication protocol instance
_communication_protocol = None


def get_communication_protocol() -> AgentCommunicationProtocol:
    """Get the global communication protocol instance."""
    global _communication_protocol
    if _communication_protocol is None:
        _communication_protocol = AgentCommunicationProtocol()
    return _communication_protocol


# Convenience functions
async def send_agent_message(
    sender: str,
    recipient: str,
    content: Dict[str, Any],
    message_type: MessageType = MessageType.QUERY,
) -> Optional[AgentMessage]:
    """Send a message between agents."""
    protocol = get_communication_protocol()
    message = AgentMessage(
        sender_agent=sender,
        recipient_agent=recipient,
        message_type=message_type,
        content=content,
    )
    return await protocol.send_message(message)


def register_agent_handler(agent_id: str, handler: Callable) -> bool:
    """Register a message handler for an agent."""
    protocol = get_communication_protocol()
    return protocol.register_agent_handler(agent_id, handler)
