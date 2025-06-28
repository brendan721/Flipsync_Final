"""Metrics Service Module.

This module provides a forwarding class for the MetricsService.
"""

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Stub class for recording and retrieving metrics.

    This stub forwards calls to the actual implementation in the core metrics module.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize metrics service.

        Args are forwarded to the actual implementation.
        """
        # Import here to avoid circular imports
        from fs_agt_clean.core.metrics.service import MetricsService as ActualService

        # Store the class for later use
        self._service_class = ActualService

        # Create the actual service
        self._actual_service = ActualService(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the actual service."""
        return getattr(self._actual_service, name)
