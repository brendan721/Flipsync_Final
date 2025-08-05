"""
Notifications service compatibility layer.

This module provides compatibility functions for accessing notification services
across different parts of the application.
"""

from typing import Optional

from .service import NotificationService

# Global notification service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """
    Get the global notification service instance.

    Returns:
        NotificationService: The notification service instance

    Raises:
        RuntimeError: If notification service is not initialized
    """
    global _notification_service

    if _notification_service is None:
        # Initialize with default configuration
        _notification_service = NotificationService()

    return _notification_service


def set_notification_service(service: NotificationService) -> None:
    """
    Set the global notification service instance.

    Args:
        service: The notification service instance to set
    """
    global _notification_service
    _notification_service = service


def reset_notification_service() -> None:
    """Reset the global notification service instance."""
    global _notification_service
    _notification_service = None


__all__ = [
    "get_notification_service",
    "set_notification_service",
    "reset_notification_service",
]
