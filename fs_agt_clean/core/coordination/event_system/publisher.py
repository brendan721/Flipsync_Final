"""
Event publisher interfaces and implementations for the FlipSync event system.

This module defines the interfaces and implementations for publishing events
in the FlipSync event system. It supports the interconnected agent vision by
providing a standardized way for agents to publish events.

The publisher is designed to be:
- Mobile-optimized: Efficient publishing with minimal overhead
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling high volumes of events
"""

import abc
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Type, Union

from fs_agt_clean.core.coordination.event_system.event import (
    CommandEvent,
    ErrorEvent,
    Event,
    EventPriority,
    EventStatus,
    NotificationEvent,
    QueryEvent,
    ResponseEvent,
)
from fs_agt_clean.core.monitoring import get_logger


class EventPublisher(abc.ABC):
    """
    Interface for publishing events to the event bus.

    Event publishers are responsible for sending events to the event bus
    for distribution to subscribers.
    """

    @abc.abstractmethod
    async def publish(self, event: Event) -> str:
        """
        Publish an event to the event bus.

        Args:
            event: The event to publish

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        pass

    @abc.abstractmethod
    async def publish_batch(self, events: List[Event]) -> List[str]:
        """
        Publish multiple events to the event bus.

        Args:
            events: The events to publish

        Returns:
            List of event IDs

        Raises:
            PublishError: If the events cannot be published
        """
        pass

    @abc.abstractmethod
    async def publish_command(
        self,
        command_name: str,
        parameters: Dict[str, Any] = None,
        target: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        **kwargs,
    ) -> str:
        """
        Publish a command event.

        Args:
            command_name: Name of the command
            parameters: Command parameters
            target: Target agent or component
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        pass

    @abc.abstractmethod
    async def publish_notification(
        self,
        notification_name: str,
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
        **kwargs,
    ) -> str:
        """
        Publish a notification event.

        Args:
            notification_name: Name of the notification
            data: Notification data
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        pass

    @abc.abstractmethod
    async def publish_query(
        self,
        query_name: str,
        parameters: Dict[str, Any] = None,
        target: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        **kwargs,
    ) -> str:
        """
        Publish a query event.

        Args:
            query_name: Name of the query
            parameters: Query parameters
            target: Target agent or component
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        pass

    @abc.abstractmethod
    async def publish_response(
        self,
        query_id: str,
        response_data: Any = None,
        is_success: bool = True,
        error_message: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        **kwargs,
    ) -> str:
        """
        Publish a response event.

        Args:
            query_id: ID of the query being responded to
            response_data: Response data
            is_success: Whether the query was successful
            error_message: Error message if the query failed
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        pass

    @abc.abstractmethod
    async def publish_error(
        self,
        error_code: str,
        error_message: str,
        source_event_id: Optional[str] = None,
        details: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.HIGH,
        **kwargs,
    ) -> str:
        """
        Publish an error event.

        Args:
            error_code: Error code
            error_message: Error message
            source_event_id: ID of the event that caused the error
            details: Additional error details
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        pass


class PublishError(Exception):
    """
    Exception raised when an event cannot be published.
    """

    def __init__(
        self,
        message: str,
        event_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize a publish error.

        Args:
            message: Error message
            event_id: ID of the event that could not be published
            cause: The exception that caused this error
        """
        self.event_id = event_id
        self.cause = cause
        super().__init__(message)


class BaseEventPublisher(EventPublisher):
    """
    Base implementation of the EventPublisher interface.

    This class provides a foundation for event publishers with common functionality.
    """

    def __init__(self, source_id: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the base event publisher.

        Args:
            source_id: ID of the event source (agent or component)
            logger: Logger instance, or None to create a default logger
        """
        self.source_id = source_id
        self.logger = logger or get_logger(f"event_publisher.{source_id}")

    async def publish(self, event: Event) -> str:
        """
        Publish an event to the event bus.

        Args:
            event: The event to publish

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        # Set source if not already set
        if not event.source:
            event.source = self.source_id

        # Mark as published
        event.mark_published()

        try:
            # Delegate to implementation-specific method
            await self._publish_event(event)

            self.logger.debug(
                f"Published event {event.event_id} of type {event.event_type.value}",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "event_name": event.metadata.event_name,
                    "correlation_id": event.correlation_id,
                },
            )

            return event.event_id
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
            raise PublishError(error_msg, event_id=event.event_id, cause=e)

    async def publish_batch(self, events: List[Event]) -> List[str]:
        """
        Publish multiple events to the event bus.

        Args:
            events: The events to publish

        Returns:
            List of event IDs

        Raises:
            PublishError: If the events cannot be published
        """
        # Set source for all events if not already set
        for event in events:
            if not event.source:
                event.source = self.source_id

            # Mark as published
            event.mark_published()

        try:
            # Delegate to implementation-specific method
            await self._publish_batch(events)

            event_ids = [event.event_id for event in events]

            self.logger.debug(
                f"Published batch of {len(events)} events",
                extra={
                    "event_count": len(events),
                    "event_ids": event_ids,
                },
            )

            return event_ids
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
            raise PublishError(error_msg, cause=e)

    async def publish_command(
        self,
        command_name: str,
        parameters: Dict[str, Any] = None,
        target: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        **kwargs,
    ) -> str:
        """
        Publish a command event.

        Args:
            command_name: Name of the command
            parameters: Command parameters
            target: Target agent or component
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        event = CommandEvent(
            command_name=command_name,
            parameters=parameters,
            target=target,
            source=self.source_id,
            priority=priority,
            **kwargs,
        )
        return await self.publish(event)

    async def publish_notification(
        self,
        notification_name: str,
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
        **kwargs,
    ) -> str:
        """
        Publish a notification event.

        Args:
            notification_name: Name of the notification
            data: Notification data
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        event = NotificationEvent(
            notification_name=notification_name,
            data=data,
            source=self.source_id,
            priority=priority,
            **kwargs,
        )
        return await self.publish(event)

    async def publish_query(
        self,
        query_name: str,
        parameters: Dict[str, Any] = None,
        target: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        **kwargs,
    ) -> str:
        """
        Publish a query event.

        Args:
            query_name: Name of the query
            parameters: Query parameters
            target: Target agent or component
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        event = QueryEvent(
            query_name=query_name,
            parameters=parameters,
            target=target,
            source=self.source_id,
            priority=priority,
            **kwargs,
        )
        return await self.publish(event)

    async def publish_response(
        self,
        query_id: str,
        response_data: Any = None,
        is_success: bool = True,
        error_message: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        **kwargs,
    ) -> str:
        """
        Publish a response event.

        Args:
            query_id: ID of the query being responded to
            response_data: Response data
            is_success: Whether the query was successful
            error_message: Error message if the query failed
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        event = ResponseEvent(
            query_id=query_id,
            response_data=response_data,
            is_success=is_success,
            error_message=error_message,
            source=self.source_id,
            priority=priority,
            **kwargs,
        )
        return await self.publish(event)

    async def publish_error(
        self,
        error_code: str,
        error_message: str,
        source_event_id: Optional[str] = None,
        details: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.HIGH,
        **kwargs,
    ) -> str:
        """
        Publish an error event.

        Args:
            error_code: Error code
            error_message: Error message
            source_event_id: ID of the event that caused the error
            details: Additional error details
            priority: Event priority
            **kwargs: Additional metadata fields

        Returns:
            The event ID

        Raises:
            PublishError: If the event cannot be published
        """
        event = ErrorEvent(
            error_code=error_code,
            error_message=error_message,
            source_event_id=source_event_id,
            details=details,
            source=self.source_id,
            priority=priority,
            **kwargs,
        )
        return await self.publish(event)

    @abc.abstractmethod
    async def _publish_event(self, event: Event) -> None:
        """
        Implementation-specific method to publish an event.

        Args:
            event: The event to publish

        Raises:
            Exception: If the event cannot be published
        """
        pass

    @abc.abstractmethod
    async def _publish_batch(self, events: List[Event]) -> None:
        """
        Implementation-specific method to publish multiple events.

        Args:
            events: The events to publish

        Raises:
            Exception: If the events cannot be published
        """
        pass


class InMemoryEventPublisher(BaseEventPublisher):
    """
    In-memory implementation of the EventPublisher interface.

    This publisher is used for testing and development, and publishes events
    to an in-memory event bus.
    """

    def __init__(
        self,
        source_id: str,
        event_bus: Any,  # Will be EventBus once defined
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the in-memory event publisher.

        Args:
            source_id: ID of the event source (agent or component)
            event_bus: The event bus to publish to
            logger: Logger instance, or None to create a default logger
        """
        super().__init__(source_id, logger)
        self.event_bus = event_bus

    async def _publish_event(self, event: Event) -> None:
        """
        Publish an event to the in-memory event bus.

        Args:
            event: The event to publish

        Raises:
            Exception: If the event cannot be published
        """
        await self.event_bus.publish(event)

    async def _publish_batch(self, events: List[Event]) -> None:
        """
        Publish multiple events to the in-memory event bus.

        Args:
            events: The events to publish

        Raises:
            Exception: If the events cannot be published
        """
        await self.event_bus.publish_batch(events)
