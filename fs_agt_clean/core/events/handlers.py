"""Event handlers for FlipSync."""

import logging
from typing import Any, Dict, Optional

from . import Event, event_bus

logger = logging.getLogger(__name__)


async def handle_resource_event(event: Event) -> None:
    """Handle resource-related events.

    Args:
        event: Resource event to handle
    """
    try:
        if event.name == "resource.allocated":
            await _handle_resource_allocation(event.data)
        elif event.name == "resource.released":
            await _handle_resource_release(event.data)
        elif event.name == "resource.failed":
            await _handle_resource_failure(event.data)
    except Exception as e:
        logger.error("Error handling resource event: %s", e)
        raise


async def _handle_resource_allocation(data: Dict[str, Any]) -> None:
    """Handle resource allocation event.

    Args:
        data: Event data containing allocation details
    """
    resource_id = data.get("resource_id")
    owner = data.get("owner")
    logger.info("Resource %s allocated to %s", resource_id, owner)


async def _handle_resource_release(data: Dict[str, Any]) -> None:
    """Handle resource release event.

    Args:
        data: Event data containing release details
    """
    resource_id = data.get("resource_id")
    owner = data.get("previous_owner")
    logger.info("Resource %s released by %s", resource_id, owner)


async def _handle_resource_failure(data: Dict[str, Any]) -> None:
    """Handle resource failure event.

    Args:
        data: Event data containing failure details
    """
    resource_id = data.get("resource_id")
    error = data.get("error")
    logger.error("Resource %s failed: %s", resource_id, error)


# Register handlers
async def register_handlers() -> None:
    """Register all event handlers."""
    await event_bus.subscribe("resource.allocated", handle_resource_event)
    await event_bus.subscribe("resource.released", handle_resource_event)
    await event_bus.subscribe("resource.failed", handle_resource_event)
