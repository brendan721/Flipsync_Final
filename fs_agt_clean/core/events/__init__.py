"""Event system for FlipSync."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of system events."""

    SYSTEM_STATUS = auto()
    RESOURCE_USAGE = auto()
    QUOTA_EXCEEDED = auto()
    THRESHOLD_EXCEEDED = auto()
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass
class Event:
    """Base event class."""

    name: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    event_type: EventType = EventType.INFO


class EventBus:
    """Event bus for handling system events."""

    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)

    async def subscribe(self, event_name: str, callback: Callable) -> None:
        """Subscribe to an event.

        Args:
            event_name: Name of event to subscribe to
            callback: Callback function to execute when event occurs
        """
        async with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(callback)
            self.logger.debug("Subscribed to event: %s", event_name)

    async def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """Unsubscribe from an event.

        Args:
            event_name: Name of event to unsubscribe from
            callback: Callback function to remove
        """
        async with self._lock:
            if event_name in self._subscribers:
                try:
                    self._subscribers[event_name].remove(callback)
                    self.logger.debug("Unsubscribed from event: %s", event_name)
                except ValueError:
                    pass

    async def publish(self, event: Event) -> None:
        """Publish an event.

        Args:
            event: Event to publish
        """
        async with self._lock:
            if event.name in self._subscribers:
                for callback in self._subscribers[event.name]:
                    try:
                        await callback(event)
                    except Exception as e:
                        self.logger.error("Error in event callback: %s", e)

    async def clear_subscribers(self) -> None:
        """Clear all subscribers."""
        async with self._lock:
            self._subscribers.clear()
            self.logger.debug("Cleared all event subscribers")

    def get_subscriber_count(self, event_name: str) -> int:
        """Get number of subscribers for an event.

        Args:
            event_name: Name of event

        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_name, []))


# Global event bus instance
event_bus = EventBus()
