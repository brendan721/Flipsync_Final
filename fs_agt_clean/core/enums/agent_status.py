"""
Unified Agent Status Enums for FlipSync
======================================

This module provides the standardized status enums for all agents in the FlipSync system.
This consolidates and replaces the multiple conflicting status enums across the codebase:

- fs_agt_clean/database/models/unified_agent.py::UnifiedAgentStatus
- fs_agt_clean/core/models/database/agents.py::AgentStatus  
- fs_agt_clean/core/coordination/coordinator/coordinator.py::UnifiedAgentStatus
- fs_agt_clean/core/coordination/realtime/agent_communication_hub.py::AgentStatus

AGENT_CONTEXT: Unified status system for 4+1 architecture compliance
AGENT_PRIORITY: Single source of truth for agent status across all components
AGENT_PATTERN: Standardized enum with comprehensive status lifecycle management
"""

from enum import Enum
from typing import Dict, List, Set


class UnifiedAgentStatus(str, Enum):
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
VALID_STATUS_TRANSITIONS: Dict[UnifiedAgentStatus, Set[UnifiedAgentStatus]] = {
    UnifiedAgentStatus.UNKNOWN: {
        UnifiedAgentStatus.INITIALIZING,
        UnifiedAgentStatus.ERROR
    },
    UnifiedAgentStatus.INITIALIZING: {
        UnifiedAgentStatus.REGISTERING,
        UnifiedAgentStatus.RUNNING,
        UnifiedAgentStatus.ERROR
    },
    UnifiedAgentStatus.REGISTERING: {
        UnifiedAgentStatus.RUNNING,
        UnifiedAgentStatus.IDLE,
        UnifiedAgentStatus.ERROR
    },
    UnifiedAgentStatus.RUNNING: {
        UnifiedAgentStatus.IDLE,
        UnifiedAgentStatus.BUSY,
        UnifiedAgentStatus.STOPPING,
        UnifiedAgentStatus.ERROR,
        UnifiedAgentStatus.MAINTENANCE
    },
    UnifiedAgentStatus.IDLE: {
        UnifiedAgentStatus.RUNNING,
        UnifiedAgentStatus.BUSY,
        UnifiedAgentStatus.STOPPING,
        UnifiedAgentStatus.ERROR,
        UnifiedAgentStatus.MAINTENANCE
    },
    UnifiedAgentStatus.BUSY: {
        UnifiedAgentStatus.RUNNING,
        UnifiedAgentStatus.IDLE,
        UnifiedAgentStatus.STOPPING,
        UnifiedAgentStatus.ERROR
    },
    UnifiedAgentStatus.STOPPING: {
        UnifiedAgentStatus.STOPPED,
        UnifiedAgentStatus.ERROR
    },
    UnifiedAgentStatus.STOPPED: {
        UnifiedAgentStatus.INITIALIZING,
        UnifiedAgentStatus.RUNNING,
        UnifiedAgentStatus.MAINTENANCE
    },
    UnifiedAgentStatus.ERROR: {
        UnifiedAgentStatus.RECOVERING,
        UnifiedAgentStatus.MAINTENANCE,
        UnifiedAgentStatus.STOPPED,
        UnifiedAgentStatus.INITIALIZING
    },
    UnifiedAgentStatus.RECOVERING: {
        UnifiedAgentStatus.RUNNING,
        UnifiedAgentStatus.IDLE,
        UnifiedAgentStatus.ERROR,
        UnifiedAgentStatus.MAINTENANCE
    },
    UnifiedAgentStatus.MAINTENANCE: {
        UnifiedAgentStatus.RUNNING,
        UnifiedAgentStatus.IDLE,
        UnifiedAgentStatus.STOPPED
    },
    UnifiedAgentStatus.DISCONNECTED: {
        UnifiedAgentStatus.RECOVERING,
        UnifiedAgentStatus.ERROR,
        UnifiedAgentStatus.STOPPED
    }
}

# Backward compatibility mappings
LEGACY_STATUS_MAPPING: Dict[str, UnifiedAgentStatus] = {
    # From fs_agt_clean/core/models/database/agents.py::AgentStatus
    "ACTIVE": UnifiedAgentStatus.RUNNING,
    "INACTIVE": UnifiedAgentStatus.STOPPED,
    "INITIALIZING": UnifiedAgentStatus.INITIALIZING,
    "ERROR": UnifiedAgentStatus.ERROR,
    "MAINTENANCE": UnifiedAgentStatus.MAINTENANCE,
    
    # From coordinator.py::UnifiedAgentStatus
    "unknown": UnifiedAgentStatus.UNKNOWN,
    "registering": UnifiedAgentStatus.REGISTERING,
    "active": UnifiedAgentStatus.RUNNING,
    "busy": UnifiedAgentStatus.BUSY,
    "inactive": UnifiedAgentStatus.STOPPED,
    "disconnected": UnifiedAgentStatus.DISCONNECTED,
    "error": UnifiedAgentStatus.ERROR,
    
    # From realtime communication hub
    "offline": UnifiedAgentStatus.DISCONNECTED,
    "recovering": UnifiedAgentStatus.RECOVERING,
}


def validate_status_transition(
    current_status: UnifiedAgentStatus, 
    new_status: UnifiedAgentStatus
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


def normalize_legacy_status(legacy_status: str) -> UnifiedAgentStatus:
    """
    Convert legacy status values to unified status.
    
    Args:
        legacy_status: Legacy status string
        
    Returns:
        Corresponding UnifiedAgentStatus value
    """
    return LEGACY_STATUS_MAPPING.get(legacy_status, UnifiedAgentStatus.UNKNOWN)


def get_operational_statuses() -> List[UnifiedAgentStatus]:
    """Get list of statuses that indicate the agent is operational."""
    return [
        UnifiedAgentStatus.RUNNING,
        UnifiedAgentStatus.IDLE,
        UnifiedAgentStatus.BUSY
    ]


def get_error_statuses() -> List[UnifiedAgentStatus]:
    """Get list of statuses that indicate error conditions."""
    return [
        UnifiedAgentStatus.ERROR,
        UnifiedAgentStatus.DISCONNECTED
    ]


def is_operational(status: UnifiedAgentStatus) -> bool:
    """Check if the agent status indicates operational state."""
    return status in get_operational_statuses()


def is_error_state(status: UnifiedAgentStatus) -> bool:
    """Check if the agent status indicates an error condition."""
    return status in get_error_statuses()


# Export all enums and utilities
__all__ = [
    "UnifiedAgentStatus",
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
    "is_error_state"
]
