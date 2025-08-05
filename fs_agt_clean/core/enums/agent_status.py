"""
Unified Agent Status Enums for FlipSync
======================================

This module provides the standardized status enums for all agents in the FlipSync system.
This consolidates and replaces the multiple conflicting status enums across the codebase:

- fs_agt_clean/database/models/unified_agent.py::AutonomousAgentStatus
- fs_agt_clean/core/models/database/agents.py::AgentStatus
- fs_agt_clean/core/coordination/coordinator/coordinator.py::AutonomousAgentStatus
- fs_agt_clean/core/coordination/realtime/agent_communication_hub.py::AgentStatus

AGENT_CONTEXT: Unified status system for 4+1 architecture compliance
AGENT_PRIORITY: Single source of truth for agent status across all components
AGENT_PATTERN: Standardized enum with comprehensive status lifecycle management
"""

from enum import Enum
from typing import Dict, List, Set


class AutonomousAgentStatus(str, Enum):
    """
    Unified agent status enum that consolidates all agent status types.

    This enum covers the complete lifecycle of autonomous agents from initialization
    through operation to shutdown, with error handling and maintenance states.
    """

    # Initialization states
    INITIALIZING = "initializing"
    REGISTERING = "registering"

    # Active operational states
    RUNNING = "running"
    ACTIVE = "active"  # Alias for RUNNING for backward compatibility
    IDLE = "idle"
    BUSY = "busy"

    # Transitional states
    STOPPING = "stopping"
    STOPPED = "stopped"
    INACTIVE = "inactive"  # Alias for STOPPED for backward compatibility

    # Error and maintenance states
    ERROR = "error"
    MAINTENANCE = "maintenance"
    RECOVERING = "recovering"
    DISCONNECTED = "disconnected"

    # Unknown state for uninitialized or untracked agents
    UNKNOWN = "unknown"


class AgentType(str, Enum):
    """
    Unified agent type enum for the 4+1 architecture.

    This enum defines the exact 4 autonomous agents + 1 conversational interface
    that comprise the FlipSync agent system.
    """

    # 4 Autonomous Agents
    MARKET = "market"
    CONTENT = "content"
    EXECUTIVE = "executive"
    LOGISTICS = "logistics"

    # 1 Conversational Interface
    STRATEGIC_CHAT = "strategic_chat"

    # Legacy aliases for backward compatibility
    MARKET_AGENT = "market"
    CONTENT_AGENT = "content"
    EXECUTIVE_AGENT = "executive"
    LOGISTICS_AGENT = "logistics"
    ASSISTANT = "strategic_chat"


class AgentPriority(str, Enum):
    """Agent priority levels for task and resource allocation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Status of agent tasks and operations."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class DecisionStatus(str, Enum):
    """Status of agent decisions in the decision pipeline."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


# Status transition mappings for validation
VALID_STATUS_TRANSITIONS: Dict[AutonomousAgentStatus, Set[AutonomousAgentStatus]] = {
    AutonomousAgentStatus.UNKNOWN: {
        AutonomousAgentStatus.INITIALIZING,
        AutonomousAgentStatus.ERROR,
    },
    AutonomousAgentStatus.INITIALIZING: {
        AutonomousAgentStatus.REGISTERING,
        AutonomousAgentStatus.RUNNING,
        AutonomousAgentStatus.ERROR,
    },
    AutonomousAgentStatus.REGISTERING: {
        AutonomousAgentStatus.RUNNING,
        AutonomousAgentStatus.IDLE,
        AutonomousAgentStatus.ERROR,
    },
    AutonomousAgentStatus.RUNNING: {
        AutonomousAgentStatus.IDLE,
        AutonomousAgentStatus.BUSY,
        AutonomousAgentStatus.STOPPING,
        AutonomousAgentStatus.ERROR,
        AutonomousAgentStatus.MAINTENANCE,
    },
    AutonomousAgentStatus.IDLE: {
        AutonomousAgentStatus.RUNNING,
        AutonomousAgentStatus.BUSY,
        AutonomousAgentStatus.STOPPING,
        AutonomousAgentStatus.ERROR,
        AutonomousAgentStatus.MAINTENANCE,
    },
    AutonomousAgentStatus.BUSY: {
        AutonomousAgentStatus.RUNNING,
        AutonomousAgentStatus.IDLE,
        AutonomousAgentStatus.STOPPING,
        AutonomousAgentStatus.ERROR,
    },
    AutonomousAgentStatus.STOPPING: {
        AutonomousAgentStatus.STOPPED,
        AutonomousAgentStatus.ERROR,
    },
    AutonomousAgentStatus.STOPPED: {
        AutonomousAgentStatus.INITIALIZING,
        AutonomousAgentStatus.RUNNING,
        AutonomousAgentStatus.MAINTENANCE,
    },
    AutonomousAgentStatus.ERROR: {
        AutonomousAgentStatus.RECOVERING,
        AutonomousAgentStatus.MAINTENANCE,
        AutonomousAgentStatus.STOPPED,
        AutonomousAgentStatus.INITIALIZING,
    },
    AutonomousAgentStatus.RECOVERING: {
        AutonomousAgentStatus.RUNNING,
        AutonomousAgentStatus.IDLE,
        AutonomousAgentStatus.ERROR,
        AutonomousAgentStatus.MAINTENANCE,
    },
    AutonomousAgentStatus.MAINTENANCE: {
        AutonomousAgentStatus.RUNNING,
        AutonomousAgentStatus.IDLE,
        AutonomousAgentStatus.STOPPED,
    },
    AutonomousAgentStatus.DISCONNECTED: {
        AutonomousAgentStatus.RECOVERING,
        AutonomousAgentStatus.ERROR,
        AutonomousAgentStatus.STOPPED,
    },
}

# Backward compatibility mappings
LEGACY_STATUS_MAPPING: Dict[str, AutonomousAgentStatus] = {
    # From fs_agt_clean/core/models/database/agents.py::AgentStatus
    "ACTIVE": AutonomousAgentStatus.RUNNING,
    "INACTIVE": AutonomousAgentStatus.STOPPED,
    "INITIALIZING": AutonomousAgentStatus.INITIALIZING,
    "ERROR": AutonomousAgentStatus.ERROR,
    "MAINTENANCE": AutonomousAgentStatus.MAINTENANCE,
    # From coordinator.py::AutonomousAgentStatus
    "unknown": AutonomousAgentStatus.UNKNOWN,
    "registering": AutonomousAgentStatus.REGISTERING,
    "active": AutonomousAgentStatus.RUNNING,
    "busy": AutonomousAgentStatus.BUSY,
    "inactive": AutonomousAgentStatus.STOPPED,
    "disconnected": AutonomousAgentStatus.DISCONNECTED,
    "error": AutonomousAgentStatus.ERROR,
    # From realtime communication hub
    "offline": AutonomousAgentStatus.DISCONNECTED,
    "recovering": AutonomousAgentStatus.RECOVERING,
}


def validate_status_transition(
    current_status: AutonomousAgentStatus, new_status: AutonomousAgentStatus
) -> bool:
    """
    Validate if a status transition is allowed.

    Args:
        current_status: Current agent status
        new_status: Desired new status

    Returns:
        True if transition is valid, False otherwise
    """
    if current_status not in VALID_STATUS_TRANSITIONS:
        return False

    return new_status in VALID_STATUS_TRANSITIONS[current_status]


def normalize_legacy_status(legacy_status: str) -> AutonomousAgentStatus:
    """
    Convert legacy status values to unified status.

    Args:
        legacy_status: Legacy status string

    Returns:
        Corresponding AutonomousAgentStatus value
    """
    return LEGACY_STATUS_MAPPING.get(legacy_status, AutonomousAgentStatus.UNKNOWN)


def get_operational_statuses() -> List[AutonomousAgentStatus]:
    """Get list of statuses that indicate the agent is operational."""
    return [
        AutonomousAgentStatus.RUNNING,
        AutonomousAgentStatus.IDLE,
        AutonomousAgentStatus.BUSY,
    ]


def get_error_statuses() -> List[AutonomousAgentStatus]:
    """Get list of statuses that indicate error conditions."""
    return [AutonomousAgentStatus.ERROR, AutonomousAgentStatus.DISCONNECTED]


def is_operational(status: AutonomousAgentStatus) -> bool:
    """Check if the agent status indicates operational state."""
    return status in get_operational_statuses()


def is_error_state(status: AutonomousAgentStatus) -> bool:
    """Check if the agent status indicates an error condition."""
    return status in get_error_statuses()


# Export all enums and utilities
__all__ = [
    "AutonomousAgentStatus",
    "AgentType",
    "AgentPriority",
    "TaskStatus",
    "DecisionStatus",
    "VALID_STATUS_TRANSITIONS",
    "LEGACY_STATUS_MAPPING",
    "validate_status_transition",
    "normalize_legacy_status",
    "get_operational_statuses",
    "get_error_statuses",
    "is_operational",
    "is_error_state",
]
