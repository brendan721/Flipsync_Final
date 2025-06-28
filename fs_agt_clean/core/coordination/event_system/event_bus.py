"""
Event bus interfaces and implementations for the FlipSync event system.

This module defines the interfaces and implementations for the event bus,
which is the central component of the event system. It routes events from
publishers to subscribers and provides event persistence and recovery.

The event bus is designed to be:
- Mobile-optimized: Efficient event routing with minimal overhead
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling high volumes of events
"""

import abc
import asyncio
import json
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

# Import event system components
from fs_agt_clean.core.coordination.event_system.event import Event, EventType
from fs_agt_clean.core.monitoring import create_alert, get_logger, record_metric
from fs_agt_clean.core.monitoring.models import AlertLevel, MetricCategory, MetricType


# Define Subscription class for type hints until circular imports are resolved
class Subscription:
    """Placeholder for Subscription class to avoid circular imports."""

    id: str
    subscriber_id: str
    is_active: bool

    async def matches(self, event: Event) -> bool:
        """Check if an event matches this subscription's filter."""
        return False  # Placeholder implementation

    async def handle(self, event: Event) -> None:
        """Handle an event using this subscription's handler."""
        pass  # Placeholder implementation


class EventBusError(Exception):
    """
    Exception raised when an event bus operation fails.
    """

    def __init__(
        self,
        message: str,
        event_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize an event bus error.

        Args:
            message: Error message
            event_id: ID of the event that caused the error
            cause: The exception that caused this error
        """
        self.event_id = event_id
        self.cause = cause
        super().__init__(message)


class EventBus(abc.ABC):
    """
    Interface for the event bus.

    The event bus is the central component of the event system. It routes events
    from publishers to subscribers and provides event persistence and recovery.
    """

    @abc.abstractmethod
    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.

        Args:
            event: The event to publish

        Raises:
            EventBusError: If the event cannot be published
        """
        pass

    @abc.abstractmethod
    async def publish_batch(self, events: List[Event]) -> None:
        """
        Publish multiple events to the bus.

        Args:
            events: The events to publish

        Raises:
            EventBusError: If the events cannot be published
        """
        pass

    @abc.abstractmethod
    async def register_subscription(self, subscription: Subscription) -> None:
        """
        Register a subscription with the bus.

        Args:
            subscription: The subscription to register

        Raises:
            EventBusError: If the subscription cannot be registered
        """
        pass

    @abc.abstractmethod
    async def unregister_subscription(self, subscription: Subscription) -> None:
        """
        Unregister a subscription from the bus.

        Args:
            subscription: The subscription to unregister

        Raises:
            EventBusError: If the subscription cannot be unregistered
        """
        pass

    @abc.abstractmethod
    async def get_event(self, event_id: str) -> Optional[Event]:
        """
        Get an event by ID.

        Args:
            event_id: ID of the event to get

        Returns:
            The event, or None if not found

        Raises:
            EventBusError: If the event cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        Get events matching the given criteria.

        Args:
            event_type: Type of events to get, or None for all types
            source: Source of events to get, or None for all sources
            target: Target of events to get, or None for all targets
            start_time: Start time for events to get, or None for no start time
            end_time: End time for events to get, or None for no end time
            limit: Maximum number of events to get

        Returns:
            List of events matching the criteria

        Raises:
            EventBusError: If the events cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def replay_events(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> None:
        """
        Replay events matching the given criteria.

        Args:
            event_type: Type of events to replay, or None for all types
            source: Source of events to replay, or None for all sources
            target: Target of events to replay, or None for all targets
            start_time: Start time for events to replay, or None for no start time
            end_time: End time for events to replay, or None for no end time
            limit: Maximum number of events to replay

        Raises:
            EventBusError: If the events cannot be replayed
        """
        pass

    @abc.abstractmethod
    async def get_dead_letter_events(
        self, limit: int = 100
    ) -> List[Tuple[Event, Exception]]:
        """
        Get events that could not be delivered.

        Args:
            limit: Maximum number of events to get

        Returns:
            List of tuples containing the event and the exception that caused the failure

        Raises:
            EventBusError: If the events cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def retry_dead_letter_event(self, event_id: str) -> bool:
        """
        Retry a dead letter event.

        Args:
            event_id: ID of the event to retry

        Returns:
            True if the event was retried, False if it wasn't found

        Raises:
            EventBusError: If the event cannot be retried
        """
        pass

    @abc.abstractmethod
    async def clear_dead_letter_event(self, event_id: str) -> bool:
        """
        Clear a dead letter event.

        Args:
            event_id: ID of the event to clear

        Returns:
            True if the event was cleared, False if it wasn't found

        Raises:
            EventBusError: If the event cannot be cleared
        """
        pass

    @abc.abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the event bus.

        Returns:
            Dictionary of metrics

        Raises:
            EventBusError: If the metrics cannot be retrieved
        """
        pass


class BaseEventBus(EventBus):
    """
    Base implementation of the EventBus interface.

    This class provides a foundation for event buses with common functionality.
    """

    def __init__(
        self,
        bus_id: str,
        logger: Optional[logging.Logger] = None,
        persistence_enabled: bool = True,
        max_retry_attempts: int = 3,
        retry_delay_seconds: float = 1.0,
        mobile_optimized: bool = False,
    ):
        """
        Initialize the base event bus.

        Args:
            bus_id: ID of the event bus
            logger: Logger instance, or None to create a default logger
            persistence_enabled: Whether to persist events
            max_retry_attempts: Maximum number of retry attempts for failed deliveries
            retry_delay_seconds: Delay between retry attempts in seconds
            mobile_optimized: Whether to optimize for mobile devices
        """
        self.bus_id = bus_id
        self.logger = logger or get_logger(f"event_bus.{bus_id}")
        self.persistence_enabled = persistence_enabled
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.mobile_optimized = mobile_optimized

        # Event storage
        self.events: Dict[str, Event] = {}

        # Subscription storage
        self.subscriptions: Dict[str, Subscription] = {}

        # Dead letter queue
        self.dead_letter_queue: Dict[str, Tuple[Event, Exception]] = {}

        # Metrics
        self.publish_count = 0
        self.delivery_count = 0
        self.failed_delivery_count = 0
        self.retry_count = 0
        self.dead_letter_count = 0

        # Start time
        self.start_time = datetime.now()

    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.

        Args:
            event: The event to publish

        Raises:
            EventBusError: If the event cannot be published
        """
        try:
            # Store the event if persistence is enabled
            if self.persistence_enabled:
                await self._store_event(event)

            # Find matching subscriptions
            matching_subscriptions = await self._find_matching_subscriptions(event)

            # Deliver the event to subscribers
            await self._deliver_event(event, matching_subscriptions)

            # Update metrics
            self.publish_count += 1
            await self._record_metrics("publish")

            self.logger.debug(
                f"Published event {event.event_id} of type {event.event_type.value}",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "event_name": event.metadata.event_name,
                    "correlation_id": event.correlation_id,
                    "matching_subscriptions": len(matching_subscriptions),
                },
            )
        except Exception as e:
            error_msg = f"Failed to publish event {event.event_id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "error": str(e),
                },
                exc_info=True,
            )

            # Create an alert for the failure
            await create_alert(
                title="Event Publish Failure",
                message=error_msg,
                level="error",  # Use string instead of enum to avoid type issues
                category="event_system",
                source="system",
                details={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "error": str(e),
                },
            )

            raise EventBusError(error_msg, event_id=event.event_id, cause=e)

    async def publish_batch(self, events: List[Event]) -> None:
        """
        Publish multiple events to the bus.

        Args:
            events: The events to publish

        Raises:
            EventBusError: If the events cannot be published
        """
        try:
            # Store the events if persistence is enabled
            if self.persistence_enabled:
                for event in events:
                    await self._store_event(event)

            # Process each event
            for event in events:
                # Find matching subscriptions
                matching_subscriptions = await self._find_matching_subscriptions(event)

                # Deliver the event to subscribers
                await self._deliver_event(event, matching_subscriptions)

            # Update metrics
            self.publish_count += len(events)
            await self._record_metrics("publish_batch")

            self.logger.debug(
                f"Published batch of {len(events)} events",
                extra={
                    "event_count": len(events),
                },
            )
        except Exception as e:
            error_msg = f"Failed to publish batch of {len(events)} events: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "event_count": len(events),
                    "error": str(e),
                },
                exc_info=True,
            )

            # Create an alert for the failure
            await create_alert(
                title="Event Batch Publish Failure",
                message=error_msg,
                level="error",
                category="event_system",
                source="system",
                details={
                    "event_count": len(events),
                    "error": str(e),
                },
            )

            raise EventBusError(error_msg, cause=e)

    async def register_subscription(self, subscription: Subscription) -> None:
        """
        Register a subscription with the bus.

        Args:
            subscription: The subscription to register

        Raises:
            EventBusError: If the subscription cannot be registered
        """
        try:
            # Store the subscription
            self.subscriptions[subscription.id] = subscription

            # Delegate to implementation-specific method
            await self._register_subscription(subscription)

            self.logger.debug(
                f"Registered subscription {subscription.id} for {subscription.subscriber_id}",
                extra={
                    "subscription_id": subscription.id,
                    "subscriber_id": subscription.subscriber_id,
                },
            )
        except Exception as e:
            error_msg = f"Failed to register subscription {subscription.id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "subscription_id": subscription.id,
                    "subscriber_id": subscription.subscriber_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EventBusError(error_msg, cause=e)

    async def unregister_subscription(self, subscription: Subscription) -> None:
        """
        Unregister a subscription from the bus.

        Args:
            subscription: The subscription to unregister

        Raises:
            EventBusError: If the subscription cannot be unregistered
        """
        try:
            # Remove the subscription
            if subscription.id in self.subscriptions:
                del self.subscriptions[subscription.id]

            # Delegate to implementation-specific method
            await self._unregister_subscription(subscription)

            self.logger.debug(
                f"Unregistered subscription {subscription.id} for {subscription.subscriber_id}",
                extra={
                    "subscription_id": subscription.id,
                    "subscriber_id": subscription.subscriber_id,
                },
            )
        except Exception as e:
            error_msg = f"Failed to unregister subscription {subscription.id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "subscription_id": subscription.id,
                    "subscriber_id": subscription.subscriber_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EventBusError(error_msg, cause=e)

    async def get_event(self, event_id: str) -> Optional[Event]:
        """
        Get an event by ID.

        Args:
            event_id: ID of the event to get

        Returns:
            The event, or None if not found

        Raises:
            EventBusError: If the event cannot be retrieved
        """
        try:
            # Check if the event is in memory
            if event_id in self.events:
                return self.events[event_id]

            # Try to load the event from storage
            event = await self._load_event(event_id)

            if event:
                # Cache the event in memory
                self.events[event_id] = event

            return event
        except Exception as e:
            error_msg = f"Failed to get event {event_id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "event_id": event_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EventBusError(error_msg, event_id=event_id, cause=e)

    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        Get events matching the given criteria.

        Args:
            event_type: Type of events to get, or None for all types
            source: Source of events to get, or None for all sources
            target: Target of events to get, or None for all targets
            start_time: Start time for events to get, or None for no start time
            end_time: End time for events to get, or None for no end time
            limit: Maximum number of events to get

        Returns:
            List of events matching the criteria

        Raises:
            EventBusError: If the events cannot be retrieved
        """
        try:
            # Delegate to implementation-specific method
            return await self._get_events(
                event_type=event_type,
                source=source,
                target=target,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )
        except Exception as e:
            error_msg = f"Failed to get events: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "event_type": event_type.value if event_type else None,
                    "source": source,
                    "target": target,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EventBusError(error_msg, cause=e)

    async def replay_events(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> None:
        """
        Replay events matching the given criteria.

        Args:
            event_type: Type of events to replay, or None for all types
            source: Source of events to replay, or None for all sources
            target: Target of events to replay, or None for all targets
            start_time: Start time for events to replay, or None for no start time
            end_time: End time for events to replay, or None for no end time
            limit: Maximum number of events to replay

        Raises:
            EventBusError: If the events cannot be replayed
        """
        try:
            # Get the events to replay
            events = await self.get_events(
                event_type=event_type,
                source=source,
                target=target,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )

            # Replay each event
            for event in events:
                # Find matching subscriptions
                matching_subscriptions = await self._find_matching_subscriptions(event)

                # Deliver the event to subscribers
                await self._deliver_event(event, matching_subscriptions)

            self.logger.info(
                f"Replayed {len(events)} events",
                extra={
                    "event_count": len(events),
                    "event_type": event_type.value if event_type else None,
                    "source": source,
                    "target": target,
                },
            )
        except Exception as e:
            error_msg = f"Failed to replay events: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "event_type": event_type.value if event_type else None,
                    "source": source,
                    "target": target,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EventBusError(error_msg, cause=e)

    async def get_dead_letter_events(
        self, limit: int = 100
    ) -> List[Tuple[Event, Exception]]:
        """
        Get events that could not be delivered.

        Args:
            limit: Maximum number of events to get

        Returns:
            List of tuples containing the event and the exception that caused the failure

        Raises:
            EventBusError: If the events cannot be retrieved
        """
        try:
            # Return dead letter events up to the limit
            events = list(self.dead_letter_queue.values())[:limit]
            return events
        except Exception as e:
            error_msg = f"Failed to get dead letter events: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "limit": limit,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EventBusError(error_msg, cause=e)

    async def retry_dead_letter_event(self, event_id: str) -> bool:
        """
        Retry a dead letter event.

        Args:
            event_id: ID of the event to retry

        Returns:
            True if the event was retried, False if it wasn't found

        Raises:
            EventBusError: If the event cannot be retried
        """
        try:
            # Check if the event is in the dead letter queue
            if event_id not in self.dead_letter_queue:
                return False

            # Get the event and remove it from the dead letter queue
            event, _ = self.dead_letter_queue.pop(event_id)

            # Publish the event again
            await self.publish(event)

            self.logger.info(
                f"Retried dead letter event {event_id}",
                extra={
                    "event_id": event_id,
                },
            )

            return True
        except Exception as e:
            error_msg = f"Failed to retry dead letter event {event_id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "event_id": event_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EventBusError(error_msg, event_id=event_id, cause=e)

    async def clear_dead_letter_event(self, event_id: str) -> bool:
        """
        Clear a dead letter event.

        Args:
            event_id: ID of the event to clear

        Returns:
            True if the event was cleared, False if it wasn't found

        Raises:
            EventBusError: If the event cannot be cleared
        """
        try:
            # Check if the event is in the dead letter queue
            if event_id not in self.dead_letter_queue:
                return False

            # Remove the event from the dead letter queue
            self.dead_letter_queue.pop(event_id)

            self.logger.info(
                f"Cleared dead letter event {event_id}",
                extra={
                    "event_id": event_id,
                },
            )

            return True
        except Exception as e:
            error_msg = f"Failed to clear dead letter event {event_id}: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "event_id": event_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EventBusError(error_msg, event_id=event_id, cause=e)

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the event bus.

        Returns:
            Dictionary of metrics

        Raises:
            EventBusError: If the metrics cannot be retrieved
        """
        try:
            # Calculate uptime
            uptime = datetime.now() - self.start_time

            # Build metrics dictionary
            metrics = {
                "publish_count": self.publish_count,
                "delivery_count": self.delivery_count,
                "failed_delivery_count": self.failed_delivery_count,
                "retry_count": self.retry_count,
                "dead_letter_count": len(self.dead_letter_queue),
                "subscription_count": len(self.subscriptions),
                "uptime_seconds": uptime.total_seconds(),
            }

            # Add implementation-specific metrics
            impl_metrics = await self._get_impl_metrics()
            metrics.update(impl_metrics)

            return metrics
        except Exception as e:
            error_msg = f"Failed to get metrics: {str(e)}"
            self.logger.error(
                error_msg,
                extra={
                    "error": str(e),
                },
                exc_info=True,
            )
            raise EventBusError(error_msg, cause=e)

    # Abstract methods that must be implemented by subclasses

    @abc.abstractmethod
    async def _store_event(self, event: Event) -> None:
        """
        Store an event.

        Args:
            event: The event to store

        Raises:
            Exception: If the event cannot be stored
        """
        pass

    @abc.abstractmethod
    async def _load_event(self, event_id: str) -> Optional[Event]:
        """
        Load an event by ID.

        Args:
            event_id: ID of the event to load

        Returns:
            The event, or None if not found

        Raises:
            Exception: If the event cannot be loaded
        """
        pass

    @abc.abstractmethod
    async def _find_matching_subscriptions(self, event: Event) -> List[Subscription]:
        """
        Find subscriptions matching an event.

        Args:
            event: The event to match

        Returns:
            List of matching subscriptions

        Raises:
            Exception: If the subscriptions cannot be found
        """
        pass

    @abc.abstractmethod
    async def _deliver_event(
        self, event: Event, subscriptions: List[Subscription]
    ) -> None:
        """
        Deliver an event to subscribers.

        Args:
            event: The event to deliver
            subscriptions: The subscriptions to deliver to

        Raises:
            Exception: If the event cannot be delivered
        """
        pass

    @abc.abstractmethod
    async def _register_subscription(self, subscription: Subscription) -> None:
        """
        Register a subscription.

        Args:
            subscription: The subscription to register

        Raises:
            Exception: If the subscription cannot be registered
        """
        pass

    @abc.abstractmethod
    async def _unregister_subscription(self, subscription: Subscription) -> None:
        """
        Unregister a subscription.

        Args:
            subscription: The subscription to unregister

        Raises:
            Exception: If the subscription cannot be unregistered
        """
        pass

    @abc.abstractmethod
    async def _get_events(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        Get events matching the given criteria.

        Args:
            event_type: Type of events to get, or None for all types
            source: Source of events to get, or None for all sources
            target: Target of events to get, or None for all targets
            start_time: Start time for events to get, or None for no start time
            end_time: End time for events to get, or None for no end time
            limit: Maximum number of events to get

        Returns:
            List of events matching the criteria

        Raises:
            Exception: If the events cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def _record_metrics(self, operation: str) -> None:
        """
        Record metrics for an operation.

        Args:
            operation: The operation to record metrics for

        Raises:
            Exception: If the metrics cannot be recorded
        """
        pass

    @abc.abstractmethod
    async def _get_impl_metrics(self) -> Dict[str, Any]:
        """
        Get implementation-specific metrics.

        Returns:
            Dictionary of metrics

        Raises:
            Exception: If the metrics cannot be retrieved
        """
        pass
