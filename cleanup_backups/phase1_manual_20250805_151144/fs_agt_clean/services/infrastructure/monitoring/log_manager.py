"""
Log module for fs_agt.
"""

import logging
import os
import sys
from typing import Dict, Optional, Union


class LogManager:
    """
    Manages logging for the application.
    """

    _instance = None
    _loggers: Dict[str, logging.Logger] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._setup_default_logger()
        return cls._instance

    def _setup_default_logger(self):
        """Set up the default logger."""
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        numeric_level = getattr(logging, log_level, logging.INFO)

        # Configure root logger
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger by name.

        Args:
            name: The name of the logger.

        Returns:
            The logger.
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]

    def set_level(self, level: Union[int, str], logger_name: Optional[str] = None):
        """
        Set the log level for a logger.

        Args:
            level: The log level to set.
            logger_name: The name of the logger to set the level for. If None, sets the level for all loggers.
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)

        if logger_name is None:
            # Set level for all loggers
            for logger in self._loggers.values():
                logger.setLevel(level)
            # Also set for root logger
            logging.getLogger().setLevel(level)
        elif logger_name in self._loggers:
            self._loggers[logger_name].setLevel(level)
