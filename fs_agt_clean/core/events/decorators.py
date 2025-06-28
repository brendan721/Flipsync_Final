"""Event decorators for FlipSync."""

import asyncio
import functools
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from . import Event, event_bus

logger = logging.getLogger(__name__)
F = TypeVar("F", bound=Callable[..., Any])


def publish_event(event_name: str, **event_data: Any) -> Callable[[F], F]:
    """Decorator to publish an event after function execution.

    Args:
        event_name: Name of event to publish
        **event_data: Additional event data

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = (
                    await func(*args, **kwargs)
                    if asyncio.iscoroutinefunction(func)
                    else func(*args, **kwargs)
                )

                # Prepare event data
                data = {**event_data}
                if isinstance(result, dict):
                    data.update(result)
                elif result is not None:
                    data["result"] = result

                # Publish event
                event = Event(name=event_name, data=data)
                await event_bus.publish(event)

                return result
            except Exception as e:
                # Publish error event
                error_event = Event(
                    name=f"{event_name}.error",
                    data={"error": str(e), "function": func.__name__, **event_data},
                )
                await event_bus.publish(error_event)
                raise

        return cast(F, wrapper)

    return decorator


def subscribe_to(event_name: str) -> Callable[[F], F]:
    """Decorator to subscribe a function to an event.

    Args:
        event_name: Name of event to subscribe to

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            await event_bus.subscribe(event_name, func)
            return (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )

        return cast(F, wrapper)

    return decorator


def track_execution(event_prefix: str) -> Callable[[F], F]:
    """Decorator to track function execution with events.

    Args:
        event_prefix: Prefix for event names

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_event = Event(
                name=f"{event_prefix}.started", data={"function": func.__name__}
            )
            await event_bus.publish(start_event)

            try:
                result = (
                    await func(*args, **kwargs)
                    if asyncio.iscoroutinefunction(func)
                    else func(*args, **kwargs)
                )

                complete_event = Event(
                    name=f"{event_prefix}.completed",
                    data={"function": func.__name__, "success": True},
                )
                await event_bus.publish(complete_event)

                return result
            except Exception as e:
                error_event = Event(
                    name=f"{event_prefix}.error",
                    data={"function": func.__name__, "error": str(e), "success": False},
                )
                await event_bus.publish(error_event)
                raise

        return cast(F, wrapper)

    return decorator
