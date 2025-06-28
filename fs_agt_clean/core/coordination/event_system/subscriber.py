"""
Event subscriber interfaces and implementations for the FlipSync event system.

This module defines the interfaces and implementations for subscribing to events
in the FlipSync event system. It supports the interconnected agent vision by
providing a standardized way for agents to receive and process events.

The subscriber is designed to be:
- Mobile-optimized: Efficient event handling with minimal overhead
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling high volumes of events
"""

import abc
import asyncio
import inspect
import logging
import re
from dataclasses import dataclass, field
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Pattern,
    Set,
    Type,
    Union,
)

from fs_agt_clean.core.coordination.event_system.event import (
    Event,
    EventPriority,
    EventStatus,
    EventType,
)
from fs_agt_clean.core.monitoring import get_logger

# Type aliases for event handlers
EventHandler = Callable[[Event], Awaitable[None]]
EventPredicate = Callable[[Event], Awaitable[bool]]


class SubscriptionFilter(abc.ABC):
    """
    Interface for event subscription filters.

    Subscription filters determine which events a subscriber receives.
    """

    @abc.abstractmethod
    async def matches(self, event: Event) -> bool:
        """
        Check if an event matches this filter.

        Args:
            event: The event to check

        Returns:
            True if the event matches, False otherwise
        """
        pass


@dataclass
class EventTypeFilter(SubscriptionFilter):
    """
    Filter events by event type.
    """

    event_types: Set[EventType]

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        return event.event_type in self.event_types


@dataclass
class EventNameFilter(SubscriptionFilter):
    """
    Filter events by event name.
    """

    event_names: Set[str]

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        return event.metadata.event_name in self.event_names


@dataclass
class EventSourceFilter(SubscriptionFilter):
    """
    Filter events by source.
    """

    sources: Set[str]

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        return event.source in self.sources


@dataclass
class EventTargetFilter(SubscriptionFilter):
    """
    Filter events by target.
    """

    targets: Set[str]

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        return event.metadata.target in self.targets if event.metadata.target else False


@dataclass
class EventPriorityFilter(SubscriptionFilter):
    """
    Filter events by priority.
    """

    min_priority: EventPriority

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        return event.priority.value >= self.min_priority.value


@dataclass
class EventNamePatternFilter(SubscriptionFilter):
    """
    Filter events by event name pattern.
    """

    patterns: List[Pattern]

    def __init__(self, patterns: List[str]):
        """
        Initialize with string patterns.

        Args:
            patterns: List of regex patterns as strings
        """
        self.patterns = [re.compile(pattern) for pattern in patterns]

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        for pattern in self.patterns:
            if pattern.search(event.metadata.event_name):
                return True
        return False


@dataclass
class CompositeFilter(SubscriptionFilter):
    """
    Composite filter that combines multiple filters.
    """

    filters: List[SubscriptionFilter]
    require_all: bool = (
        True  # If True, all filters must match; if False, any filter can match
    )

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        if not self.filters:
            return True

        if self.require_all:
            # All filters must match
            for filter_obj in self.filters:
                if not await filter_obj.matches(event):
                    return False
            return True
        else:
            # Any filter can match
            for filter_obj in self.filters:
                if await filter_obj.matches(event):
                    return True
            return False


@dataclass
class CustomFilter(SubscriptionFilter):
    """
    Custom filter using a predicate function.
    """

    predicate: EventPredicate

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        return await self.predicate(event)


@dataclass
class Subscription:
    """
    Represents a subscription to events.

    A subscription combines a filter with a handler function.
    """

    id: str
    filter: SubscriptionFilter
    handler: EventHandler
    subscriber_id: str
    is_active: bool = True
    max_concurrent: int = 1  # Maximum number of concurrent event handling tasks
    active_tasks: int = field(default=0, init=False)  # Current number of active tasks

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this subscription's filter."""
        return await self.filter.matches(event)

    async def handle(self, event: Event) -> None:
        """Handle an event using this subscription's handler."""
        if not self.is_active:
            return

        if self.active_tasks >= self.max_concurrent:
            # Too many active tasks, can't handle this event now
            return

        try:
            self.active_tasks += 1
            await self.handler(event)
        finally:
            self.active_tasks -= 1


class EventSubscriber(abc.ABC):
    """
    Interface for subscribing to events from the event bus.

    Event subscribers register interest in specific types of events and
    provide handlers to process those events when they occur.
    """

    @abc.abstractmethod
    async def subscribe(
        self,
        filter: SubscriptionFilter,
        handler: EventHandler,
        subscriber_id: Optional[str] = None,
        max_concurrent: int = 1,
    ) -> str:
        """
        Subscribe to events matching the given filter.

        Args:
            filter: Filter determining which events to receive
            handler: Function to call when an event is received
            subscriber_id: ID of the subscriber, or None to use a default
            max_concurrent: Maximum number of concurrent event handling tasks

        Returns:
            Subscription ID

        Raises:
            SubscriptionError: If the subscription cannot be created
        """
        pass

    @abc.abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscription_id: ID of the subscription to remove

        Returns:
            True if the subscription was removed, False if it wasn't found

        Raises:
            SubscriptionError: If the subscription cannot be removed
        """
        pass

    @abc.abstractmethod
    async def pause_subscription(self, subscription_id: str) -> bool:
        """
        Pause a subscription temporarily.

        Args:
            subscription_id: ID of the subscription to pause

        Returns:
            True if the subscription was paused, False if it wasn't found

        Raises:
            SubscriptionError: If the subscription cannot be paused
        """
        pass

    @abc.abstractmethod
    async def resume_subscription(self, subscription_id: str) -> bool:
        """
        Resume a paused subscription.

        Args:
            subscription_id: ID of the subscription to resume

        Returns:
            True if the subscription was resumed, False if it wasn't found

        Raises:
            SubscriptionError: If the subscription cannot be resumed
        """
        pass

    @abc.abstractmethod
    async def get_subscriptions(
        self, subscriber_id: Optional[str] = None
    ) -> List[Subscription]:
        """
        Get all subscriptions for a subscriber.

        Args:
            subscriber_id: ID of the subscriber, or None to get all subscriptions

        Returns:
            List of subscriptions

        Raises:
            SubscriptionError: If the subscriptions cannot be retrieved
        """
        pass


class SubscriptionError(Exception):
    """
    Exception raised when a subscription operation fails.
    """

    def __init__(
        self,
        message: str,
        subscription_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize a subscription error.

        Args:
            message: Error message
            subscription_id: ID of the subscription that caused the error
            cause: The exception that caused this error
        """
        self.subscription_id = subscription_id
        self.cause = cause
        super().__init__(message)


class BaseEventSubscriber(EventSubscriber):
    """
    Base implementation of the EventSubscriber interface.

    This class provides a foundation for event subscribers with common functionality.
    """

    def __init__(self, subscriber_id: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the base event subscriber.

        Args:
            subscriber_id: ID of the subscriber
            logger: Logger instance, or None to create a default logger
        """
        self.subscriber_id = subscriber_id
        self.logger = logger or get_logger(f"event_subscriber.{subscriber_id}")
        self.subscriptions: Dict[str, Subscription] = {}

    async def subscribe(
        self,
        filter: Union[
            SubscriptionFilter,
            Callable[[Event], bool],
            Callable[[Event], Awaitable[bool]],
        ],
        handler: EventHandler,
        subscriber_id: Optional[str] = None,
        max_concurrent: int = 1,
    ) -> str:
        """
        Subscribe to events matching the given filter.

        Args:
            filter: Filter determining which events to receive. Can be a SubscriptionFilter object,
                   a lambda function, or an async function that takes an event and returns a boolean.
            handler: Function to call when an event is received
            subscriber_id: ID of the subscriber, or None to use this subscriber's ID
            max_concurrent: Maximum number of concurrent event handling tasks

        Returns:
            Subscription ID

        Raises:
            SubscriptionError: If the subscription cannot be created
        """
        sub_id = subscriber_id or self.subscriber_id
        subscription_id = f"{sub_id}_{len(self.subscriptions)}"

        # If filter is a callable but not a SubscriptionFilter, wrap it in a CustomFilter
        if callable(filter) and not isinstance(filter, SubscriptionFilter):
            # Check if it's an async function
            if inspect.iscoroutinefunction(filter):
                actual_filter = CustomFilter(predicate=filter)
            else:
                # Wrap non-async function in an async function
                async def async_wrapper(event):
                    return filter(event)

                actual_filter = CustomFilter(predicate=async_wrapper)
        else:
            actual_filter = filter

        subscription = Subscription(
            id=subscription_id,
            filter=actual_filter,
            handler=handler,
            subscriber_id=sub_id,
            max_concurrent=max_concurrent,
        )

        try:
            # Delegate to implementation-specific method
            await self._register_subscription(subscription)

            # Store the subscription
            self.subscriptions[subscription_id] = subscription

            self.logger.debug(
                f"Created subscription {subscription_id} for {sub_id}",
                extra={
                    "subscription_id": subscription_id,
                    "subscriber_id": sub_id,
                },
            )

            return subscription_id
        except Exception as e:
            error_msg = f"Failed to create subscription for {sub_id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "subscriber_id": sub_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise SubscriptionError(error_msg, cause=e)

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscription_id: ID of the subscription to remove

        Returns:
            True if the subscription was removed, False if it wasn't found

        Raises:
            SubscriptionError: If the subscription cannot be removed
        """
        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]

        try:
            # Delegate to implementation-specific method
            await self._unregister_subscription(subscription)

            # Remove the subscription
            del self.subscriptions[subscription_id]

            self.logger.debug(
                f"Removed subscription {subscription_id}",
                extra={
                    "subscription_id": subscription_id,
                    "subscriber_id": subscription.subscriber_id,
                },
            )

            return True
        except Exception as e:
            error_msg = f"Failed to remove subscription {subscription_id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "subscription_id": subscription_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise SubscriptionError(error_msg, subscription_id=subscription_id, cause=e)

    async def pause_subscription(self, subscription_id: str) -> bool:
        """
        Pause a subscription temporarily.

        Args:
            subscription_id: ID of the subscription to pause

        Returns:
            True if the subscription was paused, False if it wasn't found

        Raises:
            SubscriptionError: If the subscription cannot be paused
        """
        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]

        if not subscription.is_active:
            # Already paused
            return True

        try:
            # Pause the subscription
            subscription.is_active = False

            self.logger.debug(
                f"Paused subscription {subscription_id}",
                extra={
                    "subscription_id": subscription_id,
                    "subscriber_id": subscription.subscriber_id,
                },
            )

            return True
        except Exception as e:
            error_msg = f"Failed to pause subscription {subscription_id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "subscription_id": subscription_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise SubscriptionError(error_msg, subscription_id=subscription_id, cause=e)

    async def resume_subscription(self, subscription_id: str) -> bool:
        """
        Resume a paused subscription.

        Args:
            subscription_id: ID of the subscription to resume

        Returns:
            True if the subscription was resumed, False if it wasn't found

        Raises:
            SubscriptionError: If the subscription cannot be resumed
        """
        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]

        if subscription.is_active:
            # Already active
            return True

        try:
            # Resume the subscription
            subscription.is_active = True

            self.logger.debug(
                f"Resumed subscription {subscription_id}",
                extra={
                    "subscription_id": subscription_id,
                    "subscriber_id": subscription.subscriber_id,
                },
            )

            return True
        except Exception as e:
            error_msg = f"Failed to resume subscription {subscription_id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "subscription_id": subscription_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise SubscriptionError(error_msg, subscription_id=subscription_id, cause=e)

    async def get_subscriptions(
        self, subscriber_id: Optional[str] = None
    ) -> List[Subscription]:
        """
        Get all subscriptions for a subscriber.

        Args:
            subscriber_id: ID of the subscriber, or None to get all subscriptions

        Returns:
            List of subscriptions

        Raises:
            SubscriptionError: If the subscriptions cannot be retrieved
        """
        if subscriber_id is None:
            return list(self.subscriptions.values())

        return [
            subscription
            for subscription in self.subscriptions.values()
            if subscription.subscriber_id == subscriber_id
        ]

    @abc.abstractmethod
    async def _register_subscription(self, subscription: Subscription) -> None:
        """
        Implementation-specific method to register a subscription.

        Args:
            subscription: The subscription to register

        Raises:
            Exception: If the subscription cannot be registered
        """
        pass

    @abc.abstractmethod
    async def _unregister_subscription(self, subscription: Subscription) -> None:
        """
        Implementation-specific method to unregister a subscription.

        Args:
            subscription: The subscription to unregister

        Raises:
            Exception: If the subscription cannot be unregistered
        """
        pass


class InMemoryEventSubscriber(BaseEventSubscriber):
    """
    In-memory implementation of the EventSubscriber interface.

    This subscriber is used for testing and development, and subscribes to events
    from an in-memory event bus.
    """

    def __init__(
        self,
        subscriber_id: str,
        event_bus: Any,  # Will be EventBus once defined
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the in-memory event subscriber.

        Args:
            subscriber_id: ID of the subscriber
            event_bus: The event bus to subscribe to
            logger: Logger instance, or None to create a default logger
        """
        super().__init__(subscriber_id, logger)
        self.event_bus = event_bus

    async def _register_subscription(self, subscription: Subscription) -> None:
        """
        Register a subscription with the in-memory event bus.

        Args:
            subscription: The subscription to register

        Raises:
            Exception: If the subscription cannot be registered
        """
        await self.event_bus.register_subscription(subscription)

    async def _unregister_subscription(self, subscription: Subscription) -> None:
        """
        Unregister a subscription from the in-memory event bus.

        Args:
            subscription: The subscription to unregister

        Raises:
            Exception: If the subscription cannot be unregistered
        """
        await self.event_bus.unregister_subscription(subscription)
