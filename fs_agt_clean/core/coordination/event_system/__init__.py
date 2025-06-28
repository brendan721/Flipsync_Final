"""
Event system for the FlipSync application.

This module provides the event system for FlipSync, which enables asynchronous,
loosely-coupled communication between agents and components. It is a core part
of the interconnected agent vision.

The event system consists of:
- Events: Discrete pieces of information that can be published and consumed
- Event Bus: Central component that routes events from publishers to subscribers
- Publishers: Components that publish events to the event bus
- Subscribers: Components that subscribe to events from the event bus

The event system is designed to be:
- Mobile-optimized: Efficient event routing with minimal overhead
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling high volumes of events
"""

# Re-export core components
from fs_agt_clean.core.coordination.event_system.event import (
    CommandEvent,
    ErrorEvent,
    Event,
    EventPriority,
    EventStatus,
    EventType,
    NotificationEvent,
    QueryEvent,
    ResponseEvent,
    create_event_from_dict,
    create_event_from_json,
)
from fs_agt_clean.core.coordination.event_system.event_bus import (
    BaseEventBus,
    EventBus,
    EventBusError,
)
from fs_agt_clean.core.coordination.event_system.in_memory_event_bus import (
    InMemoryEventBus,
)
from fs_agt_clean.core.coordination.event_system.publisher import (
    BaseEventPublisher,
    EventPublisher,
    InMemoryEventPublisher,
    PublishError,
)
from fs_agt_clean.core.coordination.event_system.subscriber import (
    BaseEventSubscriber,
    CompositeFilter,
    CustomFilter,
    EventNameFilter,
    EventNamePatternFilter,
    EventPriorityFilter,
    EventSourceFilter,
    EventSubscriber,
    EventTargetFilter,
    EventTypeFilter,
    InMemoryEventSubscriber,
    Subscription,
    SubscriptionError,
    SubscriptionFilter,
)

# Singleton event bus instance
_event_bus = None


def get_event_bus() -> EventBus:
    """
    Get the singleton event bus instance.

    Returns:
        The event bus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    return _event_bus


def set_event_bus(event_bus: EventBus) -> None:
    """
    Set the singleton event bus instance.

    Args:
        event_bus: The event bus instance to set
    """
    global _event_bus
    _event_bus = event_bus


def create_publisher(source_id: str) -> EventPublisher:
    """
    Create an event publisher.

    Args:
        source_id: ID of the event source (agent or component)

    Returns:
        The event publisher
    """
    return InMemoryEventPublisher(source_id, get_event_bus())


def create_subscriber(subscriber_id: str) -> EventSubscriber:
    """
    Create an event subscriber.

    Args:
        subscriber_id: ID of the subscriber

    Returns:
        The event subscriber
    """
    return InMemoryEventSubscriber(subscriber_id, get_event_bus())
