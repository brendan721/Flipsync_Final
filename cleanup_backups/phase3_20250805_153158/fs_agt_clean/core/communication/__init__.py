"""
FlipSync Core Communication Module
=================================

Provides agent communication protocol and messaging infrastructure
for the 4+1 architecture.
"""

from .agent_communication_protocol import (
    AgentMessage,
    MessageType,
    MessagePriority,
    AgentCommunicationProtocol,
    CommunicationMetrics,
    get_communication_protocol,
    send_agent_message,
    register_agent_handler
)

__all__ = [
    "AgentMessage",
    "MessageType", 
    "MessagePriority",
    "AgentCommunicationProtocol",
    "CommunicationMetrics",
    "get_communication_protocol",
    "send_agent_message",
    "register_agent_handler"
]
