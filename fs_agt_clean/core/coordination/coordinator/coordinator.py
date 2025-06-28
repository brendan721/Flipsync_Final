"""
Core coordinator interfaces and base implementations for the FlipSync application.

This module defines the interfaces and base implementations for the coordinator
component, which manages agent registration, discovery, and task delegation.
It enables hierarchical coordination between agents, with executive agents
delegating tasks to specialist agents.

The coordinator is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling complex agent ecosystems
"""

import abc
import asyncio
import enum
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from fs_agt_clean.core.coordination.event_system import (
    CompositeFilter,
    Event,
    EventNameFilter,
    EventPriority,
    EventType,
    EventTypeFilter,
    create_publisher,
    create_subscriber,
)
from fs_agt_clean.core.monitoring import get_logger


class UnifiedAgentStatus(enum.Enum):
    """
    Status of an agent in the system.
    """

    UNKNOWN = "unknown"
    REGISTERING = "registering"
    ACTIVE = "active"
    BUSY = "busy"
    INACTIVE = "inactive"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class UnifiedAgentType(enum.Enum):
    """
    Type of agent in the coordination hierarchy.
    """

    EXECUTIVE = "executive"  # High-level decision-making agents
    SPECIALIST = "specialist"  # Domain-specific specialist agents
    UTILITY = "utility"  # Utility agents providing common services
    MOBILE = "mobile"  # Mobile-specific agents
    SYSTEM = "system"  # System-level agents


class UnifiedAgentCapability:
    """
    Capability that an agent can provide.

    Capabilities define what tasks an agent can perform and are used for
    task delegation and agent discovery.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        parameters: Dict[str, Any] = None,
        constraints: Dict[str, Any] = None,
        tags: Set[str] = None,
    ):
        """
        Initialize a capability.

        Args:
            name: Name of the capability
            description: Description of the capability
            parameters: Parameters that the capability accepts
            constraints: Constraints on the capability (e.g., rate limits)
            tags: Tags for categorizing the capability
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.constraints = constraints or {}
        self.tags = tags or set()

    def matches(self, required_capability: "UnifiedAgentCapability") -> bool:
        """
        Check if this capability matches a required capability.

        Args:
            required_capability: The capability to match against

        Returns:
            True if this capability matches the required capability
        """
        # Name must match
        if self.name != required_capability.name:
            return False

        # Check if all required parameters are supported
        for param_name in required_capability.parameters:
            if param_name not in self.parameters:
                return False

        # Check if all required tags are present
        if not required_capability.tags.issubset(self.tags):
            return False

        # Check constraints
        for (
            constraint_name,
            constraint_value,
        ) in required_capability.constraints.items():
            if constraint_name not in self.constraints:
                return False

            # For numeric constraints, the capability must meet or exceed the requirement
            if isinstance(constraint_value, (int, float)):
                if self.constraints[constraint_name] < constraint_value:
                    return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the capability to a dictionary.

        Returns:
            Dictionary representation of the capability
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "constraints": self.constraints,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedAgentCapability":
        """
        Create a capability from a dictionary.

        Args:
            data: Dictionary containing capability data

        Returns:
            UnifiedAgentCapability instance
        """
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            constraints=data.get("constraints", {}),
            tags=set(data.get("tags", [])),
        )

    def __eq__(self, other: object) -> bool:
        """Check if two capabilities are equal."""
        if not isinstance(other, UnifiedAgentCapability):
            return False

        return (
            self.name == other.name
            and self.parameters == other.parameters
            and self.constraints == other.constraints
            and self.tags == other.tags
        )

    def __hash__(self) -> int:
        """Get hash of the capability."""
        return hash((self.name, frozenset(self.tags)))

    def __str__(self) -> str:
        """Get string representation of the capability."""
        return f"Capability({self.name}, tags={self.tags})"


@dataclass
class UnifiedAgentInfo:
    """
    Information about an agent in the system.
    """

    agent_id: str
    agent_type: UnifiedAgentType
    name: str
    description: str = ""
    capabilities: List[UnifiedAgentCapability] = field(default_factory=list)
    status: UnifiedAgentStatus = UnifiedAgentStatus.UNKNOWN
    last_seen: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the agent info to a dictionary.

        Returns:
            Dictionary representation of the agent info
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "name": self.name,
            "description": self.description,
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedAgentInfo":
        """
        Create agent info from a dictionary.

        Args:
            data: Dictionary containing agent info data

        Returns:
            UnifiedAgentInfo instance
        """
        last_seen = None
        if data.get("last_seen"):
            last_seen = datetime.fromisoformat(data["last_seen"])

        return cls(
            agent_id=data["agent_id"],
            agent_type=UnifiedAgentType(data["agent_type"]),
            name=data["name"],
            description=data.get("description", ""),
            capabilities=[
                UnifiedAgentCapability.from_dict(cap) for cap in data.get("capabilities", [])
            ],
            status=UnifiedAgentStatus(data.get("status", UnifiedAgentStatus.UNKNOWN.value)),
            last_seen=last_seen,
            metadata=data.get("metadata", {}),
        )

    def has_capability(self, capability: UnifiedAgentCapability) -> bool:
        """
        Check if the agent has a specific capability.

        Args:
            capability: The capability to check for

        Returns:
            True if the agent has the capability
        """
        return any(cap.matches(capability) for cap in self.capabilities)

    def is_active(self) -> bool:
        """
        Check if the agent is active.

        Returns:
            True if the agent is active
        """
        return self.status in (UnifiedAgentStatus.ACTIVE, UnifiedAgentStatus.BUSY)

    def update_status(self, status: UnifiedAgentStatus) -> None:
        """
        Update the agent's status.

        Args:
            status: The new status
        """
        self.status = status
        self.last_seen = datetime.now()

    def update_last_seen(self) -> None:
        """Update the last seen timestamp."""
        self.last_seen = datetime.now()


class Coordinator(abc.ABC):
    """
    Interface for the coordinator component.

    The coordinator manages agent registration, discovery, and task delegation.
    It enables hierarchical coordination between agents, with executive agents
    delegating tasks to specialist agents.
    """

    @abc.abstractmethod
    async def register_agent(self, agent_info: UnifiedAgentInfo) -> bool:
        """
        Register an agent with the coordinator.

        Args:
            agent_info: Information about the agent

        Returns:
            True if registration was successful

        Raises:
            CoordinationError: If registration fails
        """
        pass

    @abc.abstractmethod
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the coordinator.

        Args:
            agent_id: ID of the agent to unregister

        Returns:
            True if unregistration was successful

        Raises:
            CoordinationError: If unregistration fails
        """
        pass

    @abc.abstractmethod
    async def update_agent_status(self, agent_id: str, status: UnifiedAgentStatus) -> bool:
        """
        Update an agent's status.

        Args:
            agent_id: ID of the agent
            status: New status of the agent

        Returns:
            True if the update was successful

        Raises:
            CoordinationError: If the update fails
        """
        pass

    @abc.abstractmethod
    async def update_agent_capabilities(
        self, agent_id: str, capabilities: List[UnifiedAgentCapability]
    ) -> bool:
        """
        Update an agent's capabilities.

        Args:
            agent_id: ID of the agent
            capabilities: New capabilities of the agent

        Returns:
            True if the update was successful

        Raises:
            CoordinationError: If the update fails
        """
        pass

    @abc.abstractmethod
    async def get_agent_info(self, agent_id: str) -> Optional[UnifiedAgentInfo]:
        """
        Get information about an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            UnifiedAgent information, or None if not found

        Raises:
            CoordinationError: If the retrieval fails
        """
        pass

    @abc.abstractmethod
    async def find_agents_by_type(self, agent_type: UnifiedAgentType) -> List[UnifiedAgentInfo]:
        """
        Find agents by type.

        Args:
            agent_type: Type of agents to find

        Returns:
            List of matching agents

        Raises:
            CoordinationError: If the search fails
        """
        pass

    @abc.abstractmethod
    async def find_agents_by_capability(
        self, capability: UnifiedAgentCapability
    ) -> List[UnifiedAgentInfo]:
        """
        Find agents by capability.

        Args:
            capability: Capability to search for

        Returns:
            List of agents with the capability

        Raises:
            CoordinationError: If the search fails
        """
        pass

    @abc.abstractmethod
    async def find_agents_by_status(self, status: UnifiedAgentStatus) -> List[UnifiedAgentInfo]:
        """
        Find agents by status.

        Args:
            status: Status to search for

        Returns:
            List of agents with the status

        Raises:
            CoordinationError: If the search fails
        """
        pass

    @abc.abstractmethod
    async def get_all_agents(self) -> List[UnifiedAgentInfo]:
        """
        Get all registered agents.

        Returns:
            List of all agents

        Raises:
            CoordinationError: If the retrieval fails
        """
        pass

    @abc.abstractmethod
    async def check_agent_health(self, agent_id: str) -> bool:
        """
        Check if an agent is healthy.

        Args:
            agent_id: ID of the agent

        Returns:
            True if the agent is healthy

        Raises:
            CoordinationError: If the health check fails
        """
        pass

    @abc.abstractmethod
    async def delegate_task(
        self,
        task_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        target_agent_id: Optional[str] = None,
        required_capability: Optional[UnifiedAgentCapability] = None,
        priority: int = 0,
        deadline: Optional[datetime] = None,
    ) -> str:
        """
        Delegate a task to an agent.

        Args:
            task_id: ID of the task
            task_type: Type of the task
            parameters: Task parameters
            target_agent_id: ID of the target agent, or None to auto-select
            required_capability: Required capability for the task
            priority: Priority of the task (higher values = higher priority)
            deadline: Deadline for task completion

        Returns:
            ID of the assigned task

        Raises:
            CoordinationError: If delegation fails
        """
        pass

    @abc.abstractmethod
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task.

        Args:
            task_id: ID of the task

        Returns:
            Task status information

        Raises:
            CoordinationError: If the retrieval fails
        """
        pass

    @abc.abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: ID of the task

        Returns:
            True if cancellation was successful

        Raises:
            CoordinationError: If cancellation fails
        """
        pass

    @abc.abstractmethod
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get the result of a completed task.

        Args:
            task_id: ID of the task

        Returns:
            Task result

        Raises:
            CoordinationError: If the retrieval fails
        """
        pass

    @abc.abstractmethod
    async def get_agent_tasks(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks assigned to an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of tasks assigned to the agent

        Raises:
            CoordinationError: If the retrieval fails
        """
        pass

    @abc.abstractmethod
    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution_strategy: str,
        resolution_parameters: Dict[str, Any],
    ) -> bool:
        """
        Resolve a conflict between agents or tasks.

        Args:
            conflict_id: ID of the conflict
            resolution_strategy: Strategy to use for resolution
            resolution_parameters: Parameters for the resolution strategy

        Returns:
            True if resolution was successful

        Raises:
            CoordinationError: If resolution fails
        """
        pass


class CoordinationError(Exception):
    """
    Exception raised when a coordination operation fails.
    """

    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize a coordination error.

        Args:
            message: Error message
            agent_id: ID of the agent involved, if any
            task_id: ID of the task involved, if any
            cause: The exception that caused this error
        """
        self.agent_id = agent_id
        self.task_id = task_id
        self.cause = cause
        super().__init__(message)
