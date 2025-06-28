"""Configuration manager interface.

This module defines the interface that all configuration manager implementations
should adhere to, ensuring type compatibility across the codebase.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class ConfigInterface(Protocol):
    """Protocol defining the basic interface for configuration managers."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (can be nested using dots)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        ...

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (can be nested using dots)
            value: Value to set
        """
        ...


class BaseConfigManager(ABC):
    """Abstract base class for configuration managers.

    This class defines the common interface that all configuration managers
    should implement, ensuring type compatibility across the codebase.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (can be nested using dots)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (can be nested using dots)
            value: Value to set
        """
        pass

    def get_section(self, section: str) -> Optional[Dict[str, Any]]:
        """Get a configuration section.

        Args:
            section: Section name

        Returns:
            Configuration section or None if not found
        """
        result = self.get(section)
        if isinstance(result, dict):
            return result
        return None

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get an integer configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Integer value or default
        """
        value = self.get(key, default)
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(
                f"Failed to convert {key}={value} to int, using default {default}"
            )
            return default

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """Get a float configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Float value or default
        """
        value = self.get(key, default)
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(
                f"Failed to convert {key}={value} to float, using default {default}"
            )
            return default

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """Get a boolean configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Boolean value or default
        """
        value = self.get(key, default)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "on")
        try:
            return bool(value)
        except (ValueError, TypeError):
            logger.warning(
                f"Failed to convert {key}={value} to bool, using default {default}"
            )
            return default

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a string configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            String value or default
        """
        value = self.get(key, default)
        if value is None:
            return default
        try:
            return str(value)
        except (ValueError, TypeError):
            logger.warning(
                f"Failed to convert {key}={value} to str, using default {default}"
            )
            return default
