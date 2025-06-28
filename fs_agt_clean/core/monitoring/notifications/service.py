"""Notification Service Module.

This module provides a forwarding class for the NotificationService.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Union

from fs_agt_clean.core.monitoring.alerts.models import (
    Alert,
    AlertChannel,
    AlertSeverity,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Stub class for sending notifications.

    This stub forwards calls to the actual implementation in the services module.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize notification service.

        Args are forwarded to the actual implementation.
        """
        # Import here to avoid circular imports
        from fs_agt_clean.services.notification.service import (
            NotificationService as ActualService,
        )

        # Store the class for later use
        self._service_class = ActualService

        # Create the actual service
        self._actual_service = ActualService(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the actual service."""
        return getattr(self._actual_service, name)
