"""Secure event bus implementation for agent communication."""

import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Union

from fs_agt_clean.core.events.base import Event, EventHandler, EventPriority, EventType
from fs_agt_clean.core.exceptions import ValidationError
from fs_agt_clean.core.security.message_security import (
    MessageSecurity,
    MessageValidator,
)

logger = logging.getLogger(__name__)


class SecureEventBus:
    """Secure event bus for agent communication with validation and encryption."""

    def __init__(
        self,
        message_security: Optional[MessageSecurity] = None,
        message_validator: Optional[MessageValidator] = None,
        encrypt_messages: bool = True,
    ):
        """Initialize secure event bus.

        Args:
            message_security: Message security utilities
            message_validator: Message validator
            encrypt_messages: Whether to encrypt messages by default
        """
        self.message_security = message_security or MessageSecurity()
        self.message_validator = message_validator or MessageValidator()
        self.encrypt_messages = encrypt_messages

        # Subscribers by event type
        self.subscribers: Dict[Union[EventType, str], List[EventHandler]] = {}

        # Event acknowledgments
        self.acknowledgments: Dict[str, asyncio.Future] = {}

        # Event metrics
        self.metrics = {
            "events_published": 0,
            "events_delivered": 0,
            "events_failed": 0,
            "events_acknowledged": 0,
            "events_by_type": {},
            "events_by_priority": {},
        }

    def subscribe(
        self,
        event_type: Union[EventType, str],
        handler: EventHandler,
    ) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Event type to subscribe to
            handler: Event handler to receive events
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        if handler not in self.subscribers[event_type]:
            self.subscribers[event_type].append(handler)
            logger.debug(
                f"Handler {handler.handler_id} subscribed to event type {event_type}"
            )

    def unsubscribe(
        self,
        event_type: Union[EventType, str],
        handler: EventHandler,
    ) -> None:
        """Unsubscribe from events of a specific type.

        Args:
            event_type: Event type to unsubscribe from
            handler: Event handler to remove
        """
        if event_type in self.subscribers and handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            logger.debug(
                f"Handler {handler.handler_id} unsubscribed from event type {event_type}"
            )

    async def publish(
        self,
        event: Event,
        wait_for_acknowledgment: bool = False,
        timeout: float = 10.0,
        encrypt: Optional[bool] = None,
    ) -> bool:
        """Publish an event to subscribers.

        Args:
            event: Event to publish
            wait_for_acknowledgment: Whether to wait for acknowledgment
            timeout: Timeout for acknowledgment in seconds
            encrypt: Whether to encrypt the event (defaults to self.encrypt_messages)

        Returns:
            True if the event was delivered successfully, False otherwise
        """
        # Update metrics
        self.metrics["events_published"] += 1

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

        # Validate event
        event_dict = event.to_dict()
        is_valid, error = self.message_validator.validate_event_message(event_dict)
        if not is_valid:
            logger.error(f"Invalid event: {error}")
            self.metrics["events_failed"] += 1
            return False

        # Create secure message
        encrypt_flag = self.encrypt_messages if encrypt is None else encrypt
        secure_message = self.message_security.create_secure_message(
            event_dict, encrypt=encrypt_flag
        )

        # Set up acknowledgment future if needed
        if wait_for_acknowledgment:
            self.acknowledgments[event.id] = asyncio.Future()

        # Find subscribers for this event type
        handlers = self.subscribers.get(event.type, [])

        # If no specific handlers, try generic handlers
        if not handlers and isinstance(event.type, EventType):
            handlers = self.subscribers.get("*", [])

        if not handlers:
            logger.debug(f"No subscribers for event type {event.type}")
            return True  # No subscribers is not a failure

        # Deliver to all subscribers
        delivery_tasks = []
        for handler in handlers:
            task = asyncio.create_task(
                self._deliver_to_handler(handler, secure_message, event)
            )
            delivery_tasks.append(task)

        # Wait for all deliveries to complete
        results = await asyncio.gather(*delivery_tasks, return_exceptions=True)

        # Check if any deliveries succeeded
        success = any(
            result is True for result in results if not isinstance(result, Exception)
        )

        if success:
            self.metrics["events_delivered"] += 1
        else:
            self.metrics["events_failed"] += 1

        # Wait for acknowledgment if requested
        if wait_for_acknowledgment:
            try:
                await asyncio.wait_for(self.acknowledgments[event.id], timeout)
                self.metrics["events_acknowledged"] += 1
                return True
            except asyncio.TimeoutError:
                logger.warning(f"Acknowledgment timeout for event {event.id}")
                return False
            finally:
                # Clean up
                if event.id in self.acknowledgments:
                    del self.acknowledgments[event.id]

        return success

    async def _deliver_to_handler(
        self,
        handler: EventHandler,
        secure_message: Dict[str, Any],
        original_event: Event,
    ) -> bool:
        """Deliver a secure message to a handler.

        Args:
            handler: Event handler to deliver to
            secure_message: Secure message to deliver
            original_event: Original event for reference

        Returns:
            True if delivery was successful, False otherwise
        """
        try:
            # Extract the message
            event_dict = self.message_security.verify_and_extract_message(
                secure_message
            )

            # Recreate the event
            event = Event.from_dict(event_dict)

            # Deliver to handler
            return await handler.handle_event(event)
        except Exception as e:
            logger.error(
                f"Error delivering event to handler {handler.handler_id}: {str(e)}"
            )
            return False

    async def acknowledge_event(self, event_id: str, result: Dict[str, Any]) -> None:
        """Acknowledge an event with a result.

        Args:
            event_id: ID of the event to acknowledge
            result: Result data
        """
        if event_id in self.acknowledgments:
            self.acknowledgments[event_id].set_result(result)

    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics.

        Returns:
            Dictionary of metrics
        """
        return self.metrics


class SecureEventBusProvider:
    """Provider for secure event bus instances."""

    _instance: Optional[SecureEventBus] = None

    @classmethod
    def get_instance(
        cls,
        message_security: Optional[MessageSecurity] = None,
        message_validator: Optional[MessageValidator] = None,
        encrypt_messages: bool = True,
    ) -> SecureEventBus:
        """Get the singleton event bus instance.

        Args:
            message_security: Message security utilities
            message_validator: Message validator
            encrypt_messages: Whether to encrypt messages by default

        Returns:
            Secure event bus instance
        """
        if cls._instance is None:
            cls._instance = SecureEventBus(
                message_security=message_security,
                message_validator=message_validator,
                encrypt_messages=encrypt_messages,
            )

        return cls._instance
