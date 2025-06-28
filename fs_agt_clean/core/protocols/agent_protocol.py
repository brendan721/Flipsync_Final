"""
Protocol definitions for agent communication in the FlipSync UnifiedAgent system.

This module provides the definitive implementation of the agent protocol, aligning
with the communication patterns and message types defined in AGENTIC_SYSTEM_OVERVIEW.md.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """
    Types of messages that can be exchanged between agents.

    These types align with the message types defined in AGENTIC_SYSTEM_OVERVIEW.md:
    1. Updates: Regular status updates
    2. Alerts: Urgent attention needed
    3. Queries: Information requests
    4. Commands: Action directives
    5. Responses: Reply messages
    """

    UPDATE = "update"  # Regular status updates
    ALERT = "alert"  # Urgent attention needed
    QUERY = "query"  # Information requests
    COMMAND = "command"  # Action directives
    RESPONSE = "response"  # Reply messages


class Priority(Enum):
    """Priority levels for agent messages."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class UnifiedAgentCategoryType(Enum):
    """Types of agents in the system."""

    MARKET = "market"
    EXECUTIVE = "executive"
    LOGISTICS = "logistics"
    CONTENT = "content"
    SYSTEM = "system"


@dataclass
class UnifiedAgentMessage:
    """Base message structure for agent communication."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.UPDATE
    sender_id: str = ""
    receiver_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    content: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    action_required: bool = False


@dataclass
class UpdateMessage(UnifiedAgentMessage):
    """Update message for regular status updates."""

    def __post_init__(self):
        self.message_type = MessageType.UPDATE
        self.action_required = False


@dataclass
class AlertMessage(UnifiedAgentMessage):
    """Alert message for urgent attention."""

    severity: str = "info"
    alert_type: str = "generic"

    def __post_init__(self):
        self.message_type = MessageType.ALERT
        self.priority = Priority.HIGH
        self.action_required = True


@dataclass
class QueryMessage(UnifiedAgentMessage):
    """Query message for information requests."""

    query: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.message_type = MessageType.QUERY
        self.action_required = True


@dataclass
class CommandMessage(UnifiedAgentMessage):
    """Command message for action directives."""

    command: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    deadline: Optional[datetime] = None

    def __post_init__(self):
        self.message_type = MessageType.COMMAND
        self.action_required = True


@dataclass
class ResponseMessage(UnifiedAgentMessage):
    """Response message for replies."""

    request_id: str = ""
    status: str = "success"
    result: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0

    def __post_init__(self):
        self.message_type = MessageType.RESPONSE
        self.action_required = False


class BaseUnifiedAgentState:
    """
    Base agent state that defines common state properties and transition methods.
    Each agent category will extend this with specific states and transitions.
    """

    def __init__(self):
        self.status = "initialized"
        self.last_active = datetime.now(timezone.utc)
        self.memory_usage = 0.0
        self.performance_metrics = {}
        self.is_operational = True

    def update_status(self, new_status: str) -> None:
        """Update the agent status."""
        self.status = new_status
        self.last_active = datetime.now(timezone.utc)

    def is_active(self) -> bool:
        """Check if the agent is currently active."""
        return bool(self.is_operational and self.status != "shutdown")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the state to a dictionary."""
        return {
            "status": self.status,
            "last_active": self.last_active.isoformat(),
            "memory_usage": self.memory_usage,
            "performance_metrics": self.performance_metrics,
            "is_operational": self.is_operational,
        }


class MarketUnifiedAgentState(BaseUnifiedAgentState):
    """
    Market agent state with specific states and transitions:
    [IDLE] ← [SCANNING] → [ANALYZING]
       ↓           ↓
    [UPDATING] → [VERIFYING]
    """

    class State(Enum):
        IDLE = auto()
        SCANNING = auto()
        ANALYZING = auto()
        UPDATING = auto()
        VERIFYING = auto()

    def __init__(self):
        super().__init__()
        self.current_state = self.State.IDLE
        self.status = "idle"

    def transition_to_scanning(self) -> None:
        """Transition from IDLE to SCANNING state."""
        if self.current_state == self.State.IDLE:
            self.current_state = self.State.SCANNING
            self.status = "scanning"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to SCANNING", self.current_state
            )

    def transition_to_analyzing(self) -> None:
        """Transition from SCANNING to ANALYZING state."""
        if self.current_state == self.State.SCANNING:
            self.current_state = self.State.ANALYZING
            self.status = "analyzing"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to ANALYZING", self.current_state
            )

    def transition_to_updating(self) -> None:
        """Transition from ANALYZING or IDLE to UPDATING state."""
        if self.current_state in [self.State.ANALYZING, self.State.IDLE]:
            self.current_state = self.State.UPDATING
            self.status = "updating"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to UPDATING", self.current_state
            )

    def transition_to_verifying(self) -> None:
        """Transition from UPDATING or SCANNING to VERIFYING state."""
        if self.current_state in [self.State.UPDATING, self.State.SCANNING]:
            self.current_state = self.State.VERIFYING
            self.status = "verifying"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to VERIFYING", self.current_state
            )

    def transition_to_idle(self) -> None:
        """Transition to IDLE state (can be from any state)."""
        self.current_state = self.State.IDLE
        self.status = "idle"
        self.last_active = datetime.now(timezone.utc)


class ExecutiveUnifiedAgentState(BaseUnifiedAgentState):
    """
    Executive agent state with specific states and transitions:
    [STANDBY] ← [EVALUATING] → [PLANNING]
       ↓             ↓
    [EXECUTING] → [REVIEWING]
    """

    class State(Enum):
        STANDBY = auto()
        EVALUATING = auto()
        PLANNING = auto()
        EXECUTING = auto()
        REVIEWING = auto()

    def __init__(self):
        super().__init__()
        self.current_state = self.State.STANDBY
        self.status = "standby"

    def transition_to_evaluating(self) -> None:
        """Transition from STANDBY to EVALUATING state."""
        if self.current_state == self.State.STANDBY:
            self.current_state = self.State.EVALUATING
            self.status = "evaluating"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to EVALUATING", self.current_state
            )

    def transition_to_planning(self) -> None:
        """Transition from EVALUATING to PLANNING state."""
        if self.current_state == self.State.EVALUATING:
            self.current_state = self.State.PLANNING
            self.status = "planning"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to PLANNING", self.current_state
            )

    def transition_to_executing(self) -> None:
        """Transition from PLANNING or STANDBY to EXECUTING state."""
        if self.current_state in [self.State.PLANNING, self.State.STANDBY]:
            self.current_state = self.State.EXECUTING
            self.status = "executing"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to EXECUTING", self.current_state
            )

    def transition_to_reviewing(self) -> None:
        """Transition from EXECUTING or EVALUATING to REVIEWING state."""
        if self.current_state in [self.State.EXECUTING, self.State.EVALUATING]:
            self.current_state = self.State.REVIEWING
            self.status = "reviewing"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to REVIEWING", self.current_state
            )

    def transition_to_standby(self) -> None:
        """Transition to STANDBY state (can be from any state)."""
        self.current_state = self.State.STANDBY
        self.status = "standby"
        self.last_active = datetime.now(timezone.utc)


class LogisticsUnifiedAgentState(BaseUnifiedAgentState):
    """Logistics agent state with appropriate states for logistics operations."""

    class State(Enum):
        IDLE = auto()
        INVENTORYING = auto()
        ROUTING = auto()
        SHIPPING = auto()
        TRACKING = auto()

    def __init__(self):
        super().__init__()
        self.current_state = self.State.IDLE
        self.status = "idle"

    # Add transition methods similar to other agent states


class ContentUnifiedAgentState(BaseUnifiedAgentState):
    """
    Content agent state with specific states and transitions:
    [READY] ← [CREATING] → [OPTIMIZING]
       ↓            ↓
    [PUBLISHING] → [MONITORING]
    """

    class State(Enum):
        READY = auto()
        CREATING = auto()
        OPTIMIZING = auto()
        PUBLISHING = auto()
        MONITORING = auto()

    def __init__(self):
        super().__init__()
        self.current_state = self.State.READY
        self.status = "ready"

    def transition_to_creating(self) -> None:
        """Transition from READY to CREATING state."""
        if self.current_state == self.State.READY:
            self.current_state = self.State.CREATING
            self.status = "creating"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to CREATING", self.current_state
            )

    def transition_to_optimizing(self) -> None:
        """Transition from CREATING to OPTIMIZING state."""
        if self.current_state == self.State.CREATING:
            self.current_state = self.State.OPTIMIZING
            self.status = "optimizing"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to OPTIMIZING", self.current_state
            )

    def transition_to_publishing(self) -> None:
        """Transition from OPTIMIZING or READY to PUBLISHING state."""
        if self.current_state in [self.State.OPTIMIZING, self.State.READY]:
            self.current_state = self.State.PUBLISHING
            self.status = "publishing"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to PUBLISHING", self.current_state
            )

    def transition_to_monitoring(self) -> None:
        """Transition from PUBLISHING or CREATING to MONITORING state."""
        if self.current_state in [self.State.PUBLISHING, self.State.CREATING]:
            self.current_state = self.State.MONITORING
            self.status = "monitoring"
            self.last_active = datetime.now(timezone.utc)
        else:
            logger.warning(
                "Invalid state transition from %s to MONITORING", self.current_state
            )

    def transition_to_ready(self) -> None:
        """Transition to READY state (can be from any state)."""
        self.current_state = self.State.READY
        self.status = "ready"
        self.last_active = datetime.now(timezone.utc)


class UnifiedAgentMemory:
    """
    UnifiedAgent memory management component that handles different memory types:
    - Working memory: Short-term task-specific memory
    - Short-term memory: Recent events and information
    - Long-term memory: Persistent knowledge and experiences
    """

    def __init__(self, capacity: Dict[str, int] = None):
        self._working_memory: Dict[str, Any] = {}
        self._short_term_memory: Dict[str, Any] = {}
        self._long_term_memory: Dict[str, Any] = {}
        self._capacity = capacity or {
            "working": 100,
            "short_term": 1000,
            "long_term": 10000,
        }

    def store_in_working_memory(self, key: str, value: Any) -> None:
        """Store a value in working memory."""
        self._working_memory[key] = value
        self._enforce_capacity("working", self._working_memory)

    def retrieve_from_working_memory(self, key: str) -> Optional[Any]:
        """Retrieve a value from working memory."""
        return self._working_memory.get(key)

    def store_in_short_term_memory(self, key: str, value: Any) -> None:
        """Store a value in short-term memory."""
        self._short_term_memory[key] = {
            "value": value,
            "timestamp": datetime.now(timezone.utc),
        }
        self._enforce_capacity("short_term", self._short_term_memory)

    def retrieve_from_short_term_memory(self, key: str) -> Optional[Any]:
        """Retrieve a value from short-term memory."""
        entry = self._short_term_memory.get(key)
        return entry["value"] if entry else None

    def store_in_long_term_memory(
        self, key: str, value: Any, metadata: Dict[str, Any] = None
    ) -> None:
        """Store a value in long-term memory with optional metadata."""
        self._long_term_memory[key] = {
            "value": value,
            "timestamp": datetime.now(timezone.utc),
            "metadata": metadata or {},
            "access_count": 0,
        }
        self._enforce_capacity("long_term", self._long_term_memory)

    def retrieve_from_long_term_memory(self, key: str) -> Optional[Any]:
        """Retrieve a value from long-term memory and update access statistics."""
        entry = self._long_term_memory.get(key)
        if entry:
            entry["access_count"] += 1
            entry["last_accessed"] = datetime.now(timezone.utc)
            return entry["value"]
        return None

    def query_memories(self, memory_type: str, query: Dict[str, Any]) -> List[Any]:
        """
        Query memories by attributes.

        Args:
            memory_type: The type of memory to query ("working", "short_term", or "long_term")
            query: Dictionary of attribute-value pairs to match

        Returns:
            List of matching memory values
        """
        if memory_type == "working":
            memory_store = self._working_memory
        elif memory_type == "short_term":
            memory_store = {k: v["value"] for k, v in self._short_term_memory.items()}
        elif memory_type == "long_term":
            memory_store = {k: v["value"] for k, v in self._long_term_memory.items()}
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")

        results = []
        for k, v in memory_store.items():
            if isinstance(v, dict) and all(v.get(qk) == qv for qk, qv in query.items()):
                results.append(v)
        return results

    def clear_working_memory(self) -> None:
        """Clear all working memory."""
        self._working_memory.clear()

    def _enforce_capacity(self, memory_type: str, memory_store: Dict) -> None:
        """Ensure memory doesn't exceed capacity by removing oldest items."""
        if memory_type not in self._capacity:
            return

        capacity = self._capacity[memory_type]
        if len(memory_store) <= capacity:
            return

        # For short and long term memories with timestamp info
        if memory_type in ["short_term", "long_term"]:
            # Sort by timestamp and remove oldest
            items = sorted(memory_store.items(), key=lambda x: x[1]["timestamp"])

            for key, _ in items[: len(memory_store) - capacity]:
                memory_store.pop(key)
        else:
            # For working memory, just remove random items
            keys_to_remove = list(memory_store.keys())[: (len(memory_store) - capacity)]
            for key in keys_to_remove:
                memory_store.pop(key)


class UnifiedAgentProtocol(ABC):
    """
    Base protocol for all agents in the system.

    This protocol defines the standard interface that all agents must implement
    to ensure consistent communication and behavior across the system.
    """

    def __init__(
        self,
        agent_id: str,
        agent_category: UnifiedAgentCategoryType,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        self.agent_category = agent_category
        self.config = config or {}

        # Initialize appropriate state based on agent category
        if agent_category == UnifiedAgentCategoryType.MARKET:
            self.state = MarketUnifiedAgentState()
        elif agent_category == UnifiedAgentCategoryType.EXECUTIVE:
            self.state = ExecutiveUnifiedAgentState()
        elif agent_category == UnifiedAgentCategoryType.LOGISTICS:
            self.state = LogisticsUnifiedAgentState()
        elif agent_category == UnifiedAgentCategoryType.CONTENT:
            self.state = ContentUnifiedAgentState()
        else:
            self.state = BaseUnifiedAgentState()

        self.memory = UnifiedAgentMemory()
        self._event_queue = asyncio.Queue()
        self._running = False
        self._processing_task = None

    @abstractmethod
    async def process_message(self, message: UnifiedAgentMessage) -> Optional[UnifiedAgentMessage]:
        """
        Process an incoming message and optionally return a response.

        Args:
            message: The incoming message to process

        Returns:
            Optional response message
        """
        pass

    @abstractmethod
    async def send_message(self, message: UnifiedAgentMessage) -> None:
        """
        Send a message to another agent.

        Args:
            message: The message to send
        """
        pass

    async def initialize(self) -> None:
        """
        Initialize the agent.

        This method should be called before the agent starts processing messages.
        Subclasses should override this method to perform any necessary initialization.
        """
        logger.info("Initializing agent %s", self.agent_id)

    async def start(self) -> None:
        """
        Start the agent.

        This method starts the agent's message processing loop.
        """
        if self._running:
            logger.warning("UnifiedAgent %s is already running", self.agent_id)
            return

        logger.info("Starting agent %s", self.agent_id)
        self._running = True
        self._processing_task = asyncio.create_task(self._process_messages())

    async def stop(self) -> None:
        """
        Stop the agent.

        This method stops the agent's message processing loop.
        """
        if not self._running:
            logger.warning("UnifiedAgent %s is not running", self.agent_id)
            return

        logger.info("Stopping agent %s", self.agent_id)
        self._running = False
        if self._processing_task:
            await self._processing_task
            self._processing_task = None

    async def cleanup(self) -> None:
        """
        Clean up resources.

        This method should be called when the agent is no longer needed.
        Subclasses should override this method to perform any necessary cleanup.
        """
        logger.info("Cleaning up agent %s", self.agent_id)

        # Ensure agent is stopped before cleanup
        if self._running:
            await self.stop()

        # Clear memory
        self.memory.clear_working_memory()

    async def queue_message(self, message: UnifiedAgentMessage) -> None:
        """
        Queue a message for processing.

        Args:
            message: The message to queue
        """
        await self._event_queue.put(message)

    async def _process_messages(self) -> None:
        """
        Process messages from the queue.

        This method runs in a loop until the agent is stopped.
        """
        while self._running:
            try:
                message = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # Store message in short-term memory
                self.memory.store_in_short_term_memory(
                    f"message_{message.message_id}", message
                )

                # Process the message
                response = await self.process_message(message)

                # If a response was generated, send it
                if response:
                    await self.send_message(response)

                # Mark the task as done
                self._event_queue.task_done()

            except asyncio.TimeoutError:
                # This is expected when no messages are in the queue
                pass
            except Exception as e:
                logger.error("Error processing message: %s", e, exc_info=True)

    # Factory methods for creating messages

    def create_update_message(
        self,
        content: Dict[str, Any],
        receiver_id: Optional[str] = None,
    ) -> UpdateMessage:
        """
        Create an update message.

        Args:
            content: The update content
            receiver_id: The ID of the receiving agent

        Returns:
            Update message
        """
        return UpdateMessage(
            sender_id=self.agent_id, receiver_id=receiver_id, content=content
        )

    def create_alert_message(
        self,
        content: Dict[str, Any],
        severity: str,
        alert_type: str,
        receiver_id: Optional[str] = None,
        priority: Priority = Priority.HIGH,
    ) -> AlertMessage:
        """
        Create an alert message.

        Args:
            content: The alert content
            severity: The alert severity
            alert_type: The alert type
            receiver_id: The ID of the receiving agent
            priority: The message priority

        Returns:
            Alert message
        """
        return AlertMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            content=content,
            priority=priority,
            severity=severity,
            alert_type=alert_type,
        )

    def create_query_message(
        self,
        query: str,
        context: Dict[str, Any],
        receiver_id: str,
    ) -> QueryMessage:
        """
        Create a query message.

        Args:
            query: The query string
            context: The query context
            receiver_id: The ID of the receiving agent

        Returns:
            Query message
        """
        return QueryMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            query=query,
            context=context,
        )

    def create_command_message(
        self,
        command: str,
        parameters: Dict[str, Any],
        receiver_id: str,
        deadline: Optional[datetime] = None,
        priority: Priority = Priority.NORMAL,
    ) -> CommandMessage:
        """
        Create a command message.

        Args:
            command: The command to execute
            parameters: The command parameters
            receiver_id: The ID of the receiving agent
            deadline: The deadline for command execution
            priority: The message priority

        Returns:
            Command message
        """
        return CommandMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            command=command,
            parameters=parameters,
            deadline=deadline,
            priority=priority,
        )

    def create_response_message(
        self,
        request_id: str,
        result: Dict[str, Any],
        status: str = "success",
        receiver_id: str = None,
        errors: List[str] = None,
        execution_time: float = 0.0,
    ) -> ResponseMessage:
        """
        Create a response message.

        Args:
            request_id: The ID of the request being responded to
            result: The response result
            status: The response status
            receiver_id: The ID of the receiving agent
            errors: Any errors that occurred
            execution_time: The time taken to execute the request

        Returns:
            Response message
        """
        return ResponseMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            request_id=request_id,
            result=result,
            status=status,
            errors=errors or [],
            execution_time=execution_time,
        )


# Helper function to create a backward compatibility layer
def create_legacy_message_format(message: UnifiedAgentMessage) -> Dict[str, Any]:
    """
    Convert a new-style message to the legacy format for backward compatibility.

    Args:
        message: The new-style message

    Returns:
        Legacy format message dictionary
    """
    legacy_format = {
        "id": message.message_id,
        "type": message.message_type.value,
        "sender": message.sender_id,
        "timestamp": message.timestamp.isoformat(),
        "payload": message.content,
    }

    if message.receiver_id:
        legacy_format["recipient"] = message.receiver_id

    if message.correlation_id:
        legacy_format["correlation_id"] = message.correlation_id

    if message.metadata:
        legacy_format["metadata"] = message.metadata

    return legacy_format


# Helper function to convert legacy message format to new format
def convert_from_legacy_format(legacy_message: Dict[str, Any]) -> UnifiedAgentMessage:
    """
    Convert a legacy format message to the new style.

    Args:
        legacy_message: The legacy format message

    Returns:
        New-style message
    """
    # Determine message type
    try:
        message_type = MessageType(legacy_message.get("type", "update"))
    except ValueError:
        # Default to update if type is not recognized
        message_type = MessageType.UPDATE

    # Create base message
    base_message = UnifiedAgentMessage(
        message_id=legacy_message.get("id", str(uuid4())),
        message_type=message_type,
        sender_id=legacy_message.get("sender", ""),
        receiver_id=legacy_message.get("recipient"),
        timestamp=datetime.fromisoformat(
            legacy_message.get("timestamp", datetime.now(timezone.utc).isoformat())
        ),
        content=legacy_message.get("payload", {}),
        correlation_id=legacy_message.get("correlation_id"),
        metadata=legacy_message.get("metadata", {}),
    )

    # Convert to specific message type if needed
    if message_type == MessageType.UPDATE:
        return UpdateMessage(
            **{k: v for k, v in base_message.__dict__.items() if not k.startswith("_")}
        )
    elif message_type == MessageType.ALERT:
        return AlertMessage(
            **{k: v for k, v in base_message.__dict__.items() if not k.startswith("_")},
            severity=legacy_message.get("payload", {}).get("severity", "info"),
            alert_type=legacy_message.get("payload", {}).get("alert_type", "generic"),
        )
    elif message_type == MessageType.QUERY:
        return QueryMessage(
            **{k: v for k, v in base_message.__dict__.items() if not k.startswith("_")},
            query=legacy_message.get("payload", {}).get("query", ""),
            context=legacy_message.get("payload", {}).get("context", {}),
        )
    elif message_type == MessageType.COMMAND:
        return CommandMessage(
            **{k: v for k, v in base_message.__dict__.items() if not k.startswith("_")},
            command=legacy_message.get("payload", {}).get("command", ""),
            parameters=legacy_message.get("payload", {}).get("parameters", {}),
            deadline=legacy_message.get("payload", {}).get("deadline"),
        )
    elif message_type == MessageType.RESPONSE:
        return ResponseMessage(
            **{k: v for k, v in base_message.__dict__.items() if not k.startswith("_")},
            request_id=legacy_message.get("payload", {}).get("request_id", ""),
            status=legacy_message.get("payload", {}).get("status", "success"),
            result=legacy_message.get("payload", {}).get("result", {}),
            errors=legacy_message.get("payload", {}).get("errors", []),
            execution_time=legacy_message.get("payload", {}).get("execution_time", 0.0),
        )

    return base_message
