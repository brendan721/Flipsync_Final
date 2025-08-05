"""
Real-Time Coordination Module for FlipSync Phase 4
=================================================

Ultra-fast agent communication and coordination systems.
"""

from .agent_communication_hub import (
    RealTimeAgentCommunicationHub,
    CommunicationEvent,
    CommunicationEventType,
    AgentConnectionInfo,
)

# Import unified status enum from single source of truth
from fs_agt_clean.core.enums.agent_status import UnifiedAgentStatus as AgentStatus

__all__ = [
    "RealTimeAgentCommunicationHub",
    "CommunicationEvent",
    "CommunicationEventType",
    "AgentStatus",  # Now points to UnifiedAgentStatus
    "AgentConnectionInfo",
]
