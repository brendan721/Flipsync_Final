"""
Core event interfaces and base classes for the FlipSync event system.

This module defines the fundamental event types and interfaces that form the
foundation of FlipSync's event-based communication system. It supports the
interconnected agent vision by providing a standardized way for agents to
communicate asynchronously.

The event system is designed to be:
- Mobile-optimized: Efficient serialization and minimal overhead
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling high volumes of events
"""

import abc
import enum
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union

# Type variable for event types
T = TypeVar("T", bound="Event")


class EventPriority(enum.IntEnum):
    """
    Priority levels for events.

    Higher values indicate higher priority.
    """

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3
    CRITICAL = 4


class EventType(enum.Enum):
    """
    Core event types in the system.
    """

    COMMAND = "command"  # Directive to perform an action
    NOTIFICATION = "notification"  # Information about a state change
    QUERY = "query"  # Request for information
    RESPONSE = "response"  # Reply to a query
    ERROR = "error"  # Error notification


class EventStatus(enum.Enum):
    """
    Status of an event in its lifecycle.
    """

    CREATED = "created"  # Event has been created but not published
    PUBLISHED = "published"  # Event has been published to the event bus
    DELIVERED = "delivered"  # Event has been delivered to subscribers
    PROCESSING = "processing"  # Event is being processed by subscribers
    COMPLETED = "completed"  # Event has been fully processed
    FAILED = "failed"  # Event processing has failed
    RETRYING = "retrying"  # Event is being retried after failure


@dataclass
class EventMetadata:
    """
    Metadata for events.

    Contains information about the event itself, not its payload.
    """

    # Core identification
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    # Classification
    event_type: EventType = EventType.NOTIFICATION
    event_name: str = ""
    version: str = "1.0"

    # Routing
    source: str = ""
    target: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Processing
    status: EventStatus = EventStatus.CREATED
    retry_count: int = 0
    max_retries: int = 3

    # Mobile optimization
    is_compressed: bool = False
    size_bytes: Optional[int] = None

    # Conversational context
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

    # Decision context
    decision_id: Optional[str] = None
    confidence: Optional[float] = None

    # Custom metadata
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "event_name": self.event_name,
            "version": self.version,
            "source": self.source,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "is_compressed": self.is_compressed,
        }

        # Add optional fields if present
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        if self.causation_id:
            result["causation_id"] = self.causation_id
        if self.target:
            result["target"] = self.target
        if self.published_at:
            result["published_at"] = self.published_at.isoformat()
        if self.expires_at:
            result["expires_at"] = self.expires_at.isoformat()
        if self.size_bytes:
            result["size_bytes"] = self.size_bytes
        if self.conversation_id:
            result["conversation_id"] = self.conversation_id
        if self.user_id:
            result["user_id"] = self.user_id
        if self.decision_id:
            result["decision_id"] = self.decision_id
        if self.confidence is not None:
            result["confidence"] = self.confidence
        if self.custom:
            result["custom"] = self.custom

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventMetadata":
        """Create metadata from dictionary."""
        # Handle required fields with appropriate conversions
        metadata = cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=EventType(data.get("event_type", EventType.NOTIFICATION.value)),
            event_name=data.get("event_name", ""),
            version=data.get("version", "1.0"),
            source=data.get("source", ""),
            priority=EventPriority(data.get("priority", EventPriority.NORMAL.value)),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now().isoformat())
            ),
            status=EventStatus(data.get("status", EventStatus.CREATED.value)),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            is_compressed=data.get("is_compressed", False),
        )

        # Handle optional fields
        if "correlation_id" in data:
            metadata.correlation_id = data["correlation_id"]
        if "causation_id" in data:
            metadata.causation_id = data["causation_id"]
        if "target" in data:
            metadata.target = data["target"]
        if "published_at" in data:
            metadata.published_at = datetime.fromisoformat(data["published_at"])
        if "expires_at" in data:
            metadata.expires_at = datetime.fromisoformat(data["expires_at"])
        if "size_bytes" in data:
            metadata.size_bytes = data["size_bytes"]
        if "conversation_id" in data:
            metadata.conversation_id = data["conversation_id"]
        if "user_id" in data:
            metadata.user_id = data["user_id"]
        if "decision_id" in data:
            metadata.decision_id = data["decision_id"]
        if "confidence" in data:
            metadata.confidence = data["confidence"]
        if "custom" in data:
            metadata.custom = data["custom"]

        return metadata


class Event(abc.ABC):
    """
    Base interface for all events in the system.

    Events are the primary means of communication between agents and components
    in the FlipSync system. They represent discrete pieces of information that
    can be published, routed, and consumed asynchronously.
    """

    def __init__(
        self, payload: Any = None, metadata: Optional[EventMetadata] = None, **kwargs
    ):
        """
        Initialize a new event.

        Args:
            payload: The event payload
            metadata: Event metadata, or None to create default metadata
            **kwargs: Additional metadata fields to set
        """
        self.payload = payload
        self.metadata = metadata or EventMetadata()

        # Set additional metadata fields from kwargs
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
            else:
                self.metadata.custom[key] = value

    @property
    def event_id(self) -> str:
        """Get the event ID."""
        return self.metadata.event_id

    @property
    def correlation_id(self) -> Optional[str]:
        """Get the correlation ID."""
        return self.metadata.correlation_id

    @correlation_id.setter
    def correlation_id(self, value: str) -> None:
        """Set the correlation ID."""
        self.metadata.correlation_id = value

    @property
    def event_type(self) -> EventType:
        """Get the event type."""
        return self.metadata.event_type

    @property
    def source(self) -> str:
        """Get the event source."""
        return self.metadata.source

    @source.setter
    def source(self, value: str) -> None:
        """Set the event source."""
        self.metadata.source = value

    @property
    def priority(self) -> EventPriority:
        """Get the event priority."""
        return self.metadata.priority

    @priority.setter
    def priority(self, value: EventPriority) -> None:
        """Set the event priority."""
        self.metadata.priority = value

    @property
    def created_at(self) -> datetime:
        """Get the event creation time."""
        return self.metadata.created_at

    @property
    def status(self) -> EventStatus:
        """Get the event status."""
        return self.metadata.status

    @status.setter
    def status(self, value: EventStatus) -> None:
        """Set the event status."""
        self.metadata.status = value

    def mark_published(self) -> None:
        """Mark the event as published."""
        self.metadata.status = EventStatus.PUBLISHED
        self.metadata.published_at = datetime.now()

    def mark_delivered(self) -> None:
        """Mark the event as delivered."""
        self.metadata.status = EventStatus.DELIVERED

    def mark_processing(self) -> None:
        """Mark the event as being processed."""
        self.metadata.status = EventStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark the event as completed."""
        self.metadata.status = EventStatus.COMPLETED

    def mark_failed(self) -> None:
        """Mark the event as failed."""
        self.metadata.status = EventStatus.FAILED

    def increment_retry(self) -> None:
        """Increment the retry count and mark as retrying."""
        self.metadata.retry_count += 1
        self.metadata.status = EventStatus.RETRYING

    @property
    def can_retry(self) -> bool:
        """Check if the event can be retried."""
        return self.metadata.retry_count < self.metadata.max_retries

    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary.

        Returns:
            Dict containing the event data
        """
        pass

    @classmethod
    @abc.abstractmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create an event from a dictionary.

        Args:
            data: Dictionary containing event data

        Returns:
            Event instance
        """
        pass

    def serialize(self) -> str:
        """
        Serialize the event to a JSON string.

        Returns:
            JSON string representation of the event
        """
        return json.dumps(self.to_dict())

    @classmethod
    def deserialize(cls: Type[T], data: str) -> T:
        """
        Deserialize an event from a JSON string.

        Args:
            data: JSON string representation of the event

        Returns:
            Event instance
        """
        return cls.from_dict(json.loads(data))

    def __str__(self) -> str:
        """String representation of the event."""
        return f"{self.__class__.__name__}(id={self.event_id}, type={self.event_type.value})"


class BaseEvent(Event):
    """
    Base implementation of the Event interface.

    Provides a standard implementation for common event functionality.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary."""
        result = {
            "metadata": self.metadata.to_dict(),
            "payload": self.payload,
        }
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an event from a dictionary."""
        metadata = EventMetadata.from_dict(data.get("metadata", {}))
        payload = data.get("payload")
        return cls(payload=payload, metadata=metadata)


class CommandEvent(BaseEvent):
    """
    Event representing a command to be executed.

    Commands are directives for agents or components to perform specific actions.
    """

    def __init__(
        self,
        command_name: str,
        parameters: Dict[str, Any] = None,
        target: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize a command event.

        Args:
            command_name: Name of the command
            parameters: Command parameters
            target: Target agent or component
            **kwargs: Additional metadata fields
        """
        payload = {
            "command_name": command_name,
            "parameters": parameters or {},
        }

        metadata = kwargs.pop("metadata", None) or EventMetadata(
            event_type=EventType.COMMAND,
            event_name=command_name,
            target=target,
            priority=kwargs.pop("priority", EventPriority.NORMAL),
        )

        super().__init__(payload=payload, metadata=metadata, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandEvent":
        """Create a command event from a dictionary."""
        metadata = EventMetadata.from_dict(data.get("metadata", {}))
        payload = data.get("payload", {})

        command_name = payload.get("command_name", "")
        parameters = payload.get("parameters", {})

        return cls(command_name=command_name, parameters=parameters, metadata=metadata)

    @property
    def command_name(self) -> str:
        """Get the command name."""
        return self.payload.get("command_name", "")

    @property
    def parameters(self) -> Dict[str, Any]:
        """Get the command parameters."""
        return self.payload.get("parameters", {})

    @property
    def target(self) -> Optional[str]:
        """Get the command target."""
        return self.metadata.target

    @target.setter
    def target(self, value: str) -> None:
        """Set the command target."""
        self.metadata.target = value


class NotificationEvent(BaseEvent):
    """
    Event representing a notification of a state change.

    Notifications inform subscribers about changes in the system state.
    """

    def __init__(self, notification_name: str, data: Dict[str, Any] = None, **kwargs):
        """
        Initialize a notification event.

        Args:
            notification_name: Name of the notification
            data: Notification data
            **kwargs: Additional metadata fields
        """
        payload = {
            "notification_name": notification_name,
            "data": data or {},
        }

        metadata = kwargs.pop("metadata", None) or EventMetadata(
            event_type=EventType.NOTIFICATION,
            event_name=notification_name,
            priority=kwargs.pop("priority", EventPriority.NORMAL),
        )

        super().__init__(payload=payload, metadata=metadata, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationEvent":
        """Create a notification event from a dictionary."""
        metadata = EventMetadata.from_dict(data.get("metadata", {}))
        payload = data.get("payload", {})

        notification_name = payload.get("notification_name", "")
        notification_data = payload.get("data", {})

        return cls(
            notification_name=notification_name,
            data=notification_data,
            metadata=metadata,
        )

    @property
    def notification_name(self) -> str:
        """Get the notification name."""
        return self.payload.get("notification_name", "")

    @property
    def data(self) -> Dict[str, Any]:
        """Get the notification data."""
        return self.payload.get("data", {})


class QueryEvent(BaseEvent):
    """
    Event representing a query for information.

    Queries request information from other agents or components.
    """

    def __init__(
        self,
        query_name: str,
        parameters: Dict[str, Any] = None,
        target: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize a query event.

        Args:
            query_name: Name of the query
            parameters: Query parameters
            target: Target agent or component
            **kwargs: Additional metadata fields
        """
        payload = {
            "query_name": query_name,
            "parameters": parameters or {},
        }

        metadata = kwargs.pop("metadata", None) or EventMetadata(
            event_type=EventType.QUERY,
            event_name=query_name,
            target=target,
            priority=kwargs.pop("priority", EventPriority.NORMAL),
        )

        super().__init__(payload=payload, metadata=metadata, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryEvent":
        """Create a query event from a dictionary."""
        metadata = EventMetadata.from_dict(data.get("metadata", {}))
        payload = data.get("payload", {})

        query_name = payload.get("query_name", "")
        parameters = payload.get("parameters", {})

        return cls(query_name=query_name, parameters=parameters, metadata=metadata)

    @property
    def query_name(self) -> str:
        """Get the query name."""
        return self.payload.get("query_name", "")

    @property
    def parameters(self) -> Dict[str, Any]:
        """Get the query parameters."""
        return self.payload.get("parameters", {})

    @property
    def target(self) -> Optional[str]:
        """Get the query target."""
        return self.metadata.target

    @target.setter
    def target(self, value: str) -> None:
        """Set the query target."""
        self.metadata.target = value


class ResponseEvent(BaseEvent):
    """
    Event representing a response to a query.

    Responses provide information requested by a query.
    """

    def __init__(
        self,
        query_id: str,
        response_data: Any = None,
        is_success: bool = True,
        error_message: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize a response event.

        Args:
            query_id: ID of the query being responded to
            response_data: Response data
            is_success: Whether the query was successful
            error_message: Error message if the query failed
            **kwargs: Additional metadata fields
        """
        payload = {
            "query_id": query_id,
            "response_data": response_data,
            "is_success": is_success,
            "error_message": error_message,
        }

        metadata = kwargs.pop("metadata", None) or EventMetadata(
            event_type=EventType.RESPONSE,
            event_name=f"response_to_{query_id}",
            causation_id=query_id,
            priority=kwargs.pop("priority", EventPriority.NORMAL),
        )

        super().__init__(payload=payload, metadata=metadata, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponseEvent":
        """Create a response event from a dictionary."""
        metadata = EventMetadata.from_dict(data.get("metadata", {}))
        payload = data.get("payload", {})

        query_id = payload.get("query_id", "")
        response_data = payload.get("response_data")
        is_success = payload.get("is_success", True)
        error_message = payload.get("error_message")

        return cls(
            query_id=query_id,
            response_data=response_data,
            is_success=is_success,
            error_message=error_message,
            metadata=metadata,
        )

    @property
    def query_id(self) -> str:
        """Get the query ID."""
        return self.payload.get("query_id", "")

    @property
    def response_data(self) -> Any:
        """Get the response data."""
        return self.payload.get("response_data")

    @property
    def is_success(self) -> bool:
        """Check if the query was successful."""
        return self.payload.get("is_success", True)

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message if the query failed."""
        return self.payload.get("error_message")


class ErrorEvent(BaseEvent):
    """
    Event representing an error.

    Error events notify subscribers about errors in the system.
    """

    def __init__(
        self,
        error_code: str,
        error_message: str,
        source_event_id: Optional[str] = None,
        details: Dict[str, Any] = None,
        **kwargs,
    ):
        """
        Initialize an error event.

        Args:
            error_code: Error code
            error_message: Error message
            source_event_id: ID of the event that caused the error
            details: Additional error details
            **kwargs: Additional metadata fields
        """
        payload = {
            "error_code": error_code,
            "error_message": error_message,
            "source_event_id": source_event_id,
            "details": details or {},
        }

        metadata = kwargs.pop("metadata", None) or EventMetadata(
            event_type=EventType.ERROR,
            event_name=f"error_{error_code}",
            causation_id=source_event_id,
            priority=kwargs.pop("priority", EventPriority.HIGH),
        )

        super().__init__(payload=payload, metadata=metadata, **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorEvent":
        """Create an error event from a dictionary."""
        metadata = EventMetadata.from_dict(data.get("metadata", {}))
        payload = data.get("payload", {})

        error_code = payload.get("error_code", "")
        error_message = payload.get("error_message", "")
        source_event_id = payload.get("source_event_id")
        details = payload.get("details", {})

        return cls(
            error_code=error_code,
            error_message=error_message,
            source_event_id=source_event_id,
            details=details,
            metadata=metadata,
        )

    @property
    def error_code(self) -> str:
        """Get the error code."""
        return self.payload.get("error_code", "")

    @property
    def error_message(self) -> str:
        """Get the error message."""
        return self.payload.get("error_message", "")

    @property
    def source_event_id(self) -> Optional[str]:
        """Get the ID of the event that caused the error."""
        return self.payload.get("source_event_id")

    @property
    def details(self) -> Dict[str, Any]:
        """Get additional error details."""
        return self.payload.get("details", {})


# Factory function to create events from dictionaries
def create_event_from_dict(data: Dict[str, Any]) -> Event:
    """
    Create an event from a dictionary based on the event type.

    Args:
        data: Dictionary containing event data

    Returns:
        Event instance

    Raises:
        ValueError: If the event type is unknown
    """
    metadata = data.get("metadata", {})
    event_type_str = metadata.get("event_type")

    if not event_type_str:
        raise ValueError("Event type not specified in metadata")

    event_type = EventType(event_type_str)

    if event_type == EventType.COMMAND:
        return CommandEvent.from_dict(data)
    elif event_type == EventType.NOTIFICATION:
        return NotificationEvent.from_dict(data)
    elif event_type == EventType.QUERY:
        return QueryEvent.from_dict(data)
    elif event_type == EventType.RESPONSE:
        return ResponseEvent.from_dict(data)
    elif event_type == EventType.ERROR:
        return ErrorEvent.from_dict(data)
    else:
        raise ValueError(f"Unknown event type: {event_type_str}")


# Factory function to create events from JSON strings
def create_event_from_json(json_str: str) -> Event:
    """
    Create an event from a JSON string based on the event type.

    Args:
        json_str: JSON string containing event data

    Returns:
        Event instance

    Raises:
        ValueError: If the event type is unknown
        json.JSONDecodeError: If the JSON string is invalid
    """
    data = json.loads(json_str)
    return create_event_from_dict(data)
