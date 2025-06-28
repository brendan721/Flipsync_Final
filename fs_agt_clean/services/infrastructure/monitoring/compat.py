"""Compatibility layer for monitoring components.

This module provides compatibility between different monitoring component
implementations in the codebase.
"""

import logging
from typing import Any, Dict, Optional, Union

from fs_agt_clean.core.monitoring.log_manager import LogManager as CoreLogManager

logger = logging.getLogger(__name__)


class LogManagerCompat:
    """Compatibility wrapper for LogManager implementations.

    This class provides a unified interface that works with the LogManager
    from fs_agt_clean.core.monitoring.log_manager, adding support for the log_level
    parameter that some code expects.
    """

    def __init__(self, log_level: Optional[int] = None, **kwargs):
        """Initialize the compatibility wrapper.

        Args:
            log_level: Optional logging level
            **kwargs: Additional keyword arguments for specific implementations
        """
        self._manager = CoreLogManager()

        # Set log level if provided
        if log_level is not None:
            self._set_log_level(log_level)

    def _set_log_level(self, level: int) -> None:
        """Set the log level for all loggers.

        Args:
            level: Logging level
        """
        # Set root logger level
        logging.getLogger().setLevel(level)

        # Set level for our package loggers
        for name in ["fs_agt"]:
            logging.getLogger(name).setLevel(level)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        return self._manager.get_logger(name)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the underlying manager.

        Args:
            name: Attribute name

        Returns:
            Attribute value
        """
        return getattr(self._manager, name)


# Create a type alias for compatibility
LogManager = LogManagerCompat


# Singleton instance
_log_manager_instance = None


def get_log_manager(log_level: Optional[int] = None) -> LogManager:
    """Get a singleton instance of the LogManager.

    Args:
        log_level: Optional logging level

    Returns:
        LogManager instance
    """
    global _log_manager_instance
    if _log_manager_instance is None:
        _log_manager_instance = LogManager(log_level=log_level)
    return _log_manager_instance
