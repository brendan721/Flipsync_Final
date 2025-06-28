"""Event handling base classes for standardizing event processing across agents."""

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Union

from fs_agt_clean.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types for the FlipSync system."""

    # System events
    SYSTEM_STARTUP = auto()
    SYSTEM_SHUTDOWN = auto()
    CONFIGURATION_CHANGED = auto()

    # UnifiedAgent lifecycle events
    AGENT_INITIALIZED = auto()
    AGENT_READY = auto()
    AGENT_BUSY = auto()
    AGENT_WAITING = auto()
    AGENT_ERROR = auto()
    AGENT_TERMINATED = auto()

    # Communication events
    COMMAND_RECEIVED = auto()
    COMMAND_COMPLETED = auto()
    EXECUTION_RESULT = auto()
    ERROR_OCCURRED = auto()

    # Marketplace events
    LISTING_CREATED = auto()
    LISTING_UPDATED = auto()
    LISTING_DELETED = auto()
    ORDER_RECEIVED = auto()
    ORDER_UPDATED = auto()
    ORDER_SHIPPED = auto()
    INVENTORY_UPDATED = auto()
    PRICE_CHANGED = auto()

    # UnifiedUser events
    USER_ACTION = auto()
    USER_NOTIFICATION = auto()


class EventPriority(Enum):
    """Priority levels for events."""

    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


class Event:
    """Standard event structure for the FlipSync system."""

    def __init__(
        self,
        type: Union[EventType, str],
        source: str,
        data: Dict[str, Any],
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        priority: Optional[EventPriority] = None,
        target: Optional[str] = None,
    ):
        """Initialize event.

        Args:
            type: Event type
            source: Source of the event
            data: Event data
            id: Event ID (generated if not provided)
            timestamp: Event timestamp (current time if not provided)
            priority: Event priority (MEDIUM if not provided)
            target: Target agent or component (if applicable)
        """
        self.id = id or f"evt_{uuid.uuid4()}"
        self.type = type
        self.source = source
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.priority = priority or EventPriority.MEDIUM
        self.target = target

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "id": self.id,
            "type": self.type.name if isinstance(self.type, EventType) else self.type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": (
                self.priority.name
                if isinstance(self.priority, EventPriority)
                else self.priority
            ),
            "target": self.target,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            Event instance

        Raises:
            ValidationError: If the dictionary is invalid
        """
        required_fields = ["type", "source", "data"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}", field=field)

        # Convert string type to enum if possible
        event_type = data["type"]
        if isinstance(event_type, str):
            try:
                event_type = EventType[event_type]
            except KeyError:
                # Keep as string if not a known enum value
                pass

        # Convert string priority to enum if possible
        priority = data.get("priority")
        if isinstance(priority, str):
            try:
                priority = EventPriority[priority]
            except KeyError:
                # Default to MEDIUM if not a known enum value
                priority = EventPriority.MEDIUM

        # Parse timestamp if provided
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            type=event_type,
            source=data["source"],
            data=data["data"],
            id=data.get("id"),
            timestamp=timestamp,
            priority=priority,
            target=data.get("target"),
        )


class EventHandler:
    """Base class for event handlers with common functionality."""

    def __init__(self, handler_id: str):
        """Initialize event handler.

        Args:
            handler_id: Unique identifier for this handler
        """
        self.handler_id = handler_id
        self.event_handlers: Dict[Union[EventType, str], List[Callable]] = {}
        self.processed_events: Set[str] = set()
        self.metrics = {
            "events_received": 0,
            "events_processed": 0,
            "events_failed": 0,
            "events_by_type": {},
            "events_by_priority": {},
        }

    def register_handler(
        self, event_type: Union[EventType, str], handler: Callable
    ) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: Event type to handle
            handler: Async function to call when event is received
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type {event_type}")

    async def handle_event(self, event: Event) -> bool:
        """Handle an event by dispatching to registered handlers.

        Args:
            event: Event to handle

        Returns:
            True if event was handled, False otherwise
        """
        # Update metrics
        self.metrics["events_received"] += 1

        # Track events by type
        event_type_str = (
            event.type.name if isinstance(event.type, EventType) else str(event.type)
        )
        if event_type_str not in self.metrics["events_by_type"]:
            self.metrics["events_by_type"][event_type_str] = 0
        self.metrics["events_by_type"][event_type_str] += 1

        # Track events by priority
        priority_str = (
            event.priority.name
            if isinstance(event.priority, EventPriority)
            else str(event.priority)
        )
        if priority_str not in self.metrics["events_by_priority"]:
            self.metrics["events_by_priority"][priority_str] = 0
        self.metrics["events_by_priority"][priority_str] += 1

        # Check if we've already processed this event
        if event.id in self.processed_events:
            logger.debug(f"Event {event.id} already processed, skipping")
            return True

        # Find handlers for this event type
        handlers = self.event_handlers.get(event.type, [])

        # If no specific handlers, try generic handlers
        if not handlers and isinstance(event.type, EventType):
            handlers = self.event_handlers.get("*", [])

        if not handlers:
            logger.debug(f"No handlers registered for event type {event.type}")
            return False

        # Process the event with all registered handlers
        try:
            # Execute all handlers concurrently
            tasks = [handler(event) for handler in handlers]
            await asyncio.gather(*tasks)

            # Mark as processed
            self.processed_events.add(event.id)
            self.metrics["events_processed"] += 1

            return True
        except Exception as e:
            logger.error(f"Error handling event {event.id}: {str(e)}")
            self.metrics["events_failed"] += 1
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get event handler metrics.

        Returns:
            Dictionary of metrics
        """
        return self.metrics
