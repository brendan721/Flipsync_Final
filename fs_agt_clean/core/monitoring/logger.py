"""
Logger implementation for FlipSync.

This module provides a comprehensive logging system that supports:
- Different log levels and formats
- File and console logging
- Log rotation and management
- Structured logging
- Sensitive data redaction
- Mobile-specific optimizations

It serves as the foundation for the more specialized logging components
like UnifiedAgentInteractionLogger.
"""

import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = logging.INFO


class LogLevel(Enum):
    """Log levels with mobile-aware descriptions."""

    DEBUG = (logging.DEBUG, "Detailed debug information (high battery usage)")
    INFO = (logging.INFO, "General information (moderate battery usage)")
    WARNING = (logging.WARNING, "Warning conditions (low battery usage)")
    ERROR = (logging.ERROR, "Error conditions (minimal battery usage)")
    CRITICAL = (logging.CRITICAL, "Critical conditions (minimal battery usage)")

    def __init__(self, level: int, description: str):
        self.level = level
        self.description = description


class LogFormat(Enum):
    """Log formats with different detail levels."""

    MINIMAL = "%(levelname)s: %(message)s"
    STANDARD = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED = (
        "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
    )
    JSON = "json"  # Special format for structured logging


class LogDestination(Enum):
    """Log destinations with mobile considerations."""

    CONSOLE = "console"
    FILE = "file"
    BOTH = "both"
    MEMORY = "memory"  # For offline logging in mobile environments


class LogManager:
    """
    Manages logging for the application with mobile and vision awareness.

    This class provides a centralized logging system that supports:
    - Different log levels and formats
    - File and console logging with rotation
    - Structured logging with JSON support
    - Sensitive data redaction
    - Mobile-specific optimizations
    - Correlation ID tracking

    It serves as the foundation for specialized logging components.
    """

    _instance = None
    _lock = threading.RLock()
    _initialized = False
    _loggers: Dict[str, logging.Logger] = {}
    _sensitive_patterns: List[re.Pattern] = []
    _correlation_ids: Dict[str, str] = {}
    _memory_buffer: List[Dict[str, Any]] = []
    _max_memory_logs = 1000  # Maximum number of logs to keep in memory

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LogManager, cls).__new__(cls)
            return cls._instance

    def __init__(
        self,
        log_level: Union[int, str, LogLevel] = DEFAULT_LOG_LEVEL,
        log_format: Union[str, LogFormat] = DEFAULT_FORMAT,
        log_destination: Union[str, LogDestination] = LogDestination.CONSOLE,
        log_dir: Optional[Union[str, Path]] = None,
        max_file_size_mb: int = 10,
        backup_count: int = 5,
        enable_json_logging: bool = False,
        enable_sensitive_data_redaction: bool = True,
        mobile_optimized: bool = False,
    ):
        """
        Initialize the log manager.

        Args:
            log_level: Logging level
            log_format: Log message format
            log_destination: Where to send logs
            log_dir: Directory for log files
            max_file_size_mb: Maximum log file size in MB
            backup_count: Number of backup log files to keep
            enable_json_logging: Whether to enable JSON structured logging
            enable_sensitive_data_redaction: Whether to redact sensitive data
            mobile_optimized: Whether to optimize for mobile environments
        """
        with self._lock:
            if self._initialized:
                return

            # Convert log level to int if needed
            if isinstance(log_level, str):
                log_level = getattr(logging, log_level.upper(), DEFAULT_LOG_LEVEL)
            elif isinstance(log_level, LogLevel):
                log_level = log_level.level

            # Convert log format to string if needed
            if isinstance(log_format, LogFormat):
                log_format = log_format.value

            # Convert log destination to enum if needed
            if isinstance(log_destination, str):
                try:
                    log_destination = LogDestination(log_destination)
                except ValueError:
                    log_destination = LogDestination.CONSOLE

            # Set up log directory
            self.log_dir = Path(log_dir) if log_dir else Path("logs")
            os.makedirs(self.log_dir, exist_ok=True)

            # Store configuration
            self.log_level = log_level
            self.log_format = log_format
            self.log_destination = log_destination
            self.max_file_size_mb = max_file_size_mb
            self.backup_count = backup_count
            self.enable_json_logging = enable_json_logging
            self.enable_sensitive_data_redaction = enable_sensitive_data_redaction
            self.mobile_optimized = mobile_optimized

            # Set up root logger
            self._setup_root_logger()

            # Add default sensitive patterns
            if enable_sensitive_data_redaction:
                self.add_sensitive_patterns(
                    [
                        r"password\s*[=:]\s*\S+",
                        r"secret\s*[=:]\s*\S+",
                        r"token\s*[=:]\s*\S+",
                        r"key\s*[=:]\s*\S+",
                        r"credential\s*[=:]\s*\S+",
                    ]
                )

            self._initialized = True

    def _setup_root_logger(self):
        """Set up the root logger."""
        # Get the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatter
        if self.log_format == LogFormat.JSON.value:
            formatter = logging.Formatter("%(message)s")
        else:
            formatter = logging.Formatter(self.log_format, datefmt=DEFAULT_DATE_FORMAT)

        # Add console handler if needed
        if self.log_destination in [LogDestination.CONSOLE, LogDestination.BOTH]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # Add file handler if needed
        if self.log_destination in [LogDestination.FILE, LogDestination.BOTH]:
            # Regular log file
            log_file = self.log_dir / "fs_agt.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.max_file_size_mb * 1024 * 1024,
                backupCount=self.backup_count,
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            # JSON log file if enabled
            if self.enable_json_logging:
                json_log_file = self.log_dir / "fs_agt.log.json"
                json_handler = TimedRotatingFileHandler(
                    json_log_file,
                    when="midnight",
                    backupCount=self.backup_count,
                )
                json_handler.setFormatter(formatter)
                root_logger.addHandler(json_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger by name.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        with self._lock:
            if name not in self._loggers:
                logger = logging.getLogger(name)

                # Add a filter for sensitive data redaction if enabled
                if self.enable_sensitive_data_redaction:
                    logger.addFilter(self._redact_sensitive_data)

                self._loggers[name] = logger

            return self._loggers[name]

    def _redact_sensitive_data(self, record: logging.LogRecord) -> bool:
        """
        Filter to redact sensitive data from log messages.

        Args:
            record: Log record

        Returns:
            True to include the record
        """
        if not self.enable_sensitive_data_redaction:
            return True

        if isinstance(record.msg, str):
            for pattern in self._sensitive_patterns:
                record.msg = pattern.sub(r"\1=*REDACTED*", record.msg)

        return True

    def add_sensitive_patterns(self, patterns: List[str]) -> None:
        """
        Add patterns for sensitive data redaction.

        Args:
            patterns: List of regex patterns
        """
        with self._lock:
            for pattern in patterns:
                # Convert pattern to capture the key part
                modified_pattern = re.compile(
                    r"(" + pattern.split(r"\s*[=:]\s*")[0] + r")\s*[=:]\s*\S+"
                )
                self._sensitive_patterns.append(modified_pattern)

    def set_level(
        self, level: Union[int, str, LogLevel], logger_name: Optional[str] = None
    ) -> None:
        """
        Set the log level for a logger.

        Args:
            level: Log level
            logger_name: Logger name (None for all loggers)
        """
        # Convert level to int if needed
        if isinstance(level, str):
            level = getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)
        elif isinstance(level, LogLevel):
            level = level.level

        with self._lock:
            if logger_name is None:
                # Set level for all loggers
                for logger in self._loggers.values():
                    logger.setLevel(level)
                # Also set for root logger
                logging.getLogger().setLevel(level)
            elif logger_name in self._loggers:
                self._loggers[logger_name].setLevel(level)

    def set_correlation_id(self, context_id: str, correlation_id: str) -> None:
        """
        Set a correlation ID for a context.

        Args:
            context_id: Context identifier
            correlation_id: Correlation ID
        """
        with self._lock:
            self._correlation_ids[context_id] = correlation_id

    def get_correlation_id(self, context_id: str = "default") -> Optional[str]:
        """
        Get the correlation ID for a context.

        Args:
            context_id: Context identifier (defaults to "default")

        Returns:
            Correlation ID if found, None otherwise
        """
        with self._lock:
            return self._correlation_ids.get(context_id)

    def clear_correlation_id(self, context_id: str) -> None:
        """
        Clear the correlation ID for a context.

        Args:
            context_id: Context identifier
        """
        with self._lock:
            if context_id in self._correlation_ids:
                del self._correlation_ids[context_id]

    def log_to_memory(
        self,
        level: int,
        name: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a message to memory buffer (for offline logging).

        Args:
            level: Log level
            name: Logger name
            message: Log message
            extra: Extra data
        """
        with self._lock:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "name": name,
                "message": message,
                "extra": extra or {},
            }

            self._memory_buffer.append(log_entry)

            # Trim buffer if needed
            if len(self._memory_buffer) > self._max_memory_logs:
                self._memory_buffer = self._memory_buffer[-self._max_memory_logs :]

    def flush_memory_logs(
        self, destination: Optional[Union[str, Path]] = None
    ) -> List[Dict[str, Any]]:
        """
        Flush memory logs to a destination.

        Args:
            destination: Optional file destination

        Returns:
            List of log entries
        """
        with self._lock:
            logs = self._memory_buffer.copy()

            if destination:
                path = Path(destination)
                with open(path, "a") as f:
                    for log in logs:
                        f.write(json.dumps(log) + "\n")

            self._memory_buffer.clear()
            return logs

    def get_memory_logs(self) -> List[Dict[str, Any]]:
        """
        Get all logs from memory buffer.

        Returns:
            List of log entries
        """
        with self._lock:
            return self._memory_buffer.copy()

    def cleanup(self) -> None:
        """Clean up resources."""
        with self._lock:
            # Close all handlers
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)

            # Clear memory buffer
            self._memory_buffer.clear()

            # Clear correlation IDs
            self._correlation_ids.clear()

            # Reset initialization flag
            self._initialized = False


# Singleton instance
_log_manager_instance = None


def get_log_manager() -> LogManager:
    """
    Get the singleton log manager instance.

    Returns:
        LogManager instance
    """
    global _log_manager_instance
    if _log_manager_instance is None:
        _log_manager_instance = LogManager()
    return _log_manager_instance


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return get_log_manager().get_logger(name)


def set_correlation_id(context_id: str, correlation_id: str) -> None:
    """
    Set a correlation ID for a context.

    Args:
        context_id: Context identifier
        correlation_id: Correlation ID
    """
    get_log_manager().set_correlation_id(context_id, correlation_id)


def get_correlation_id(context_id: str = "default") -> Optional[str]:
    """
    Get the correlation ID for a context.

    Args:
        context_id: Context identifier (defaults to "default")

    Returns:
        Correlation ID if found, None otherwise
    """
    return get_log_manager().get_correlation_id(context_id)


def configure_logging(
    log_level: Union[int, str, LogLevel] = DEFAULT_LOG_LEVEL,
    log_format: Union[str, LogFormat] = DEFAULT_FORMAT,
    log_destination: Union[str, LogDestination] = LogDestination.CONSOLE,
    log_dir: Optional[Union[str, Path]] = None,
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    enable_json_logging: bool = False,
    enable_sensitive_data_redaction: bool = True,
    mobile_optimized: bool = False,
) -> None:
    """
    Configure logging system.

    Args:
        log_level: Logging level
        log_format: Log message format
        log_destination: Where to send logs
        log_dir: Directory for log files
        max_file_size_mb: Maximum log file size in MB
        backup_count: Number of backup log files to keep
        enable_json_logging: Whether to enable JSON structured logging
        enable_sensitive_data_redaction: Whether to redact sensitive data
        mobile_optimized: Whether to optimize for mobile environments
    """
    global _log_manager_instance
    _log_manager_instance = LogManager(
        log_level=log_level,
        log_format=log_format,
        log_destination=log_destination,
        log_dir=log_dir,
        max_file_size_mb=max_file_size_mb,
        backup_count=backup_count,
        enable_json_logging=enable_json_logging,
        enable_sensitive_data_redaction=enable_sensitive_data_redaction,
        mobile_optimized=mobile_optimized,
    )
