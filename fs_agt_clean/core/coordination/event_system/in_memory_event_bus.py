"""
In-memory implementation of the event bus for the FlipSync event system.

This module provides an in-memory implementation of the event bus for testing
and development purposes. It stores events and subscriptions in memory and
does not persist them to disk.

The in-memory event bus is designed to be:
- Simple: Easy to understand and use
- Fast: Efficient for testing and development
- Complete: Implements all event bus functionality
- Mobile-optimized: Efficient for mobile devices
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from fs_agt_clean.core.coordination.event_system.event import Event, EventType
from fs_agt_clean.core.coordination.event_system.event_bus import (
    BaseEventBus,
    EventBusError,
)
from fs_agt_clean.core.monitoring import get_logger, record_metric


class InMemoryEventBus(BaseEventBus):
    """
    In-memory implementation of the event bus.

    This implementation stores events and subscriptions in memory and does not
    persist them to disk. It is intended for testing and development purposes.
    """

    def __init__(
        self,
        bus_id: str = "in_memory_bus",
        logger: Optional[logging.Logger] = None,
        max_retry_attempts: int = 3,
        retry_delay_seconds: float = 1.0,
        mobile_optimized: bool = False,
    ):
        """
        Initialize the in-memory event bus.

        Args:
            bus_id: ID of the event bus
            logger: Logger instance, or None to create a default logger
            max_retry_attempts: Maximum number of retry attempts for failed deliveries
            retry_delay_seconds: Delay between retry attempts in seconds
            mobile_optimized: Whether to optimize for mobile devices
        """
        super().__init__(
            bus_id=bus_id,
            logger=logger,
            persistence_enabled=True,  # In-memory persistence
            max_retry_attempts=max_retry_attempts,
            retry_delay_seconds=retry_delay_seconds,
            mobile_optimized=mobile_optimized,
        )

        # Event storage by type and time
        self.events_by_type: Dict[EventType, List[Event]] = {
            event_type: [] for event_type in EventType
        }
        self.events_by_source: Dict[str, List[Event]] = {}
        self.events_by_target: Dict[str, List[Event]] = {}

        # Performance metrics
        self.avg_delivery_time: float = 0.0
        self.total_delivery_time: float = 0.0
        self.max_delivery_time: float = 0.0

    async def _store_event(self, event: Event) -> None:
        """
        Store an event in memory.

        Args:
            event: The event to store

        Raises:
            Exception: If the event cannot be stored
        """
        # Store in main events dictionary
        self.events[event.event_id] = event

        # Store by type
        self.events_by_type[event.event_type].append(event)

        # Store by source
        if event.source:
            if event.source not in self.events_by_source:
                self.events_by_source[event.source] = []
            self.events_by_source[event.source].append(event)

        # Store by target
        if event.metadata.target:
            if event.metadata.target not in self.events_by_target:
                self.events_by_target[event.metadata.target] = []
            self.events_by_target[event.metadata.target].append(event)

    async def _load_event(self, event_id: str) -> Optional[Event]:
        """
        Load an event from memory.

        Args:
            event_id: ID of the event to load

        Returns:
            The event, or None if not found

        Raises:
            Exception: If the event cannot be loaded
        """
        return self.events.get(event_id)

    async def _find_matching_subscriptions(self, event: Event) -> List["Subscription"]:
        """
        Find subscriptions matching an event.

        Args:
            event: The event to match

        Returns:
            List of matching subscriptions

        Raises:
            Exception: If the subscriptions cannot be found
        """
        matching = []

        for subscription in self.subscriptions.values():
            if subscription.is_active:
                if await subscription.matches(event):
                    matching.append(subscription)

        return matching

    async def _deliver_event(
        self, event: Event, subscriptions: List["Subscription"]
    ) -> None:
        """
        Deliver an event to subscribers.

        Args:
            event: The event to deliver
            subscriptions: The subscriptions to deliver to

        Raises:
            Exception: If the event cannot be delivered
        """
        if not subscriptions:
            return

        # Mark event as being delivered
        event.mark_delivered()

        # Track delivery metrics
        start_time = time.time()
        success_count = 0
        failure_count = 0

        # Deliver to each subscription
        for subscription in subscriptions:
            try:
                # Mark event as being processed
                event.mark_processing()

                # Handle the event
                await subscription.handle(event)

                # Mark event as completed for this subscription
                event.mark_completed()

                success_count += 1
            except Exception as e:
                # Mark event as failed for this subscription
                event.mark_failed()

                failure_count += 1

                # Log the error
                self.logger.error(
                    f"Failed to deliver event {event.event_id} to subscription {subscription.id}: {str(e)}",
                    extra={
                        "event_id": event.event_id,
                        "subscription_id": subscription.id,
                        "error": str(e),
                    },
                    exc_info=True,
                )

                # Retry if possible
                if event.can_retry:
                    event.increment_retry()

                    # Wait before retrying
                    await asyncio.sleep(self.retry_delay_seconds)

                    # Retry delivery
                    try:
                        await subscription.handle(event)

                        # Mark event as completed for this subscription
                        event.mark_completed()

                        success_count += 1
                        failure_count -= 1

                        self.retry_count += 1
                    except Exception as retry_e:
                        # Log the retry error
                        self.logger.error(
                            f"Failed to retry event {event.event_id} to subscription {subscription.id}: {str(retry_e)}",
                            extra={
                                "event_id": event.event_id,
                                "subscription_id": subscription.id,
                                "error": str(retry_e),
                                "retry_count": event.metadata.retry_count,
                            },
                            exc_info=True,
                        )
                        # Add to dead letter queue after retry failure
                        self.dead_letter_queue[event.event_id] = (event, retry_e)
                        self.dead_letter_count += 1
                        self.logger.warning(
                            f"Added event {event.event_id} to dead letter queue after {event.metadata.retry_count} retries",
                            extra={
                                "event_id": event.event_id,
                                "retry_count": event.metadata.retry_count,
                            },
                        )

        # Update delivery metrics
        end_time = time.time()
        delivery_time = end_time - start_time

        self.delivery_count += success_count
        self.failed_delivery_count += failure_count

        # Update average delivery time
        total_deliveries = self.delivery_count + self.failed_delivery_count
        if total_deliveries > 0:
            self.total_delivery_time += delivery_time
            self.avg_delivery_time = self.total_delivery_time / total_deliveries
            self.max_delivery_time = max(self.max_delivery_time, delivery_time)

    async def _register_subscription(self, subscription: "Subscription") -> None:
        """
        Register a subscription.

        Args:
            subscription: The subscription to register

        Raises:
            Exception: If the subscription cannot be registered
        """
        # Nothing to do for in-memory implementation
        pass

    async def _unregister_subscription(self, subscription: "Subscription") -> None:
        """
        Unregister a subscription.

        Args:
            subscription: The subscription to unregister

        Raises:
            Exception: If the subscription cannot be unregistered
        """
        # Nothing to do for in-memory implementation
        pass

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
        # Start with all events
        events = list(self.events.values())

        # Filter by type
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        # Filter by source
        if source is not None:
            events = [e for e in events if e.source == source]

        # Filter by target
        if target is not None:
            events = [e for e in events if e.metadata.target == target]

        # Filter by start time
        if start_time is not None:
            events = [e for e in events if e.created_at >= start_time]

        # Filter by end time
        if end_time is not None:
            events = [e for e in events if e.created_at <= end_time]

        # Sort by creation time (newest first)
        events.sort(key=lambda e: e.created_at, reverse=True)

        # Limit the number of events
        return events[:limit]

    async def _record_metrics(self, operation: str) -> None:
        """
        Record metrics for an operation.

        Args:
            operation: The operation to record metrics for

        Raises:
            Exception: If the metrics cannot be recorded
        """
        # Record metrics using the monitoring system
        await record_metric(
            name=f"event_bus_{operation}_count",
            value=1.0,
            metric_type="counter",
            category="event_system",
            labels={
                "bus_id": self.bus_id,
                "operation": operation,
            },
        )

        # Record delivery metrics if available
        if operation in ["publish", "publish_batch"] and self.delivery_count > 0:
            await record_metric(
                name="event_bus_delivery_time",
                value=self.avg_delivery_time,
                metric_type="gauge",
                category="event_system",
                labels={
                    "bus_id": self.bus_id,
                    "operation": operation,
                },
            )

    async def create_subscriber(self, subscriber_id: str) -> "EventSubscriber":
        """
        Create a subscriber for this event bus.

        Args:
            subscriber_id: ID of the subscriber

        Returns:
            A new subscriber instance

        Raises:
            EventBusError: If the subscriber cannot be created
        """
        from fs_agt_clean.core.coordination.event_system.subscriber import (
            InMemoryEventSubscriber,
        )

        return InMemoryEventSubscriber(subscriber_id, self)

    async def _get_impl_metrics(self) -> Dict[str, Any]:
        """
        Get implementation-specific metrics.

        Returns:
            Dictionary of metrics

        Raises:
            Exception: If the metrics cannot be retrieved
        """
        return {
            "avg_delivery_time": self.avg_delivery_time,
            "max_delivery_time": self.max_delivery_time,
            "events_by_type": {
                event_type.name: len(events)
                for event_type, events in self.events_by_type.items()
            },
            "events_by_source_count": len(self.events_by_source),
            "events_by_target_count": len(self.events_by_target),
            "mobile_optimized": self.mobile_optimized,
        }
