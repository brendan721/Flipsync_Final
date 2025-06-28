"""Protocol definition for configuration management in FlipSync.

This module defines the core interfaces that all configuration managers
must implement, enabling standardized access to configuration across
the FlipSync system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class ConfigValidationResult:
    """Result of a configuration validation operation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]


class ConfigProtocol(ABC):
    """Base protocol interface for configuration management.

    This abstract class defines the methods that all configuration
    managers must implement. It ensures that all configuration
    implementations provide a consistent interface.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: Configuration key using dot notation (e.g., 'database.host')
            default: Default value if key not found

        Returns:
            Configuration value or default if not found
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key using dot notation
            value: Value to set
        """
        pass

    @abstractmethod
    def load(self, config_path: Union[str, Path]) -> None:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file

        Raises:
            FileNotFoundError: If configuration file not found
            ValueError: If configuration file cannot be parsed
        """
        pass

    @abstractmethod
    def reload(self) -> None:
        """Reload configuration from source.

        This method should reload all configuration files that were
        previously loaded.
        """
        pass

    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section.

        Args:
            section: Section name

        Returns:
            Dictionary containing the section configuration
        """
        pass

    @abstractmethod
    def register_change_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for configuration changes.

        Args:
            callback: Function to call when configuration changes.
                     Should accept (key, value) parameters.
        """
        pass

    @abstractmethod
    def validate(
        self, schema: Optional[Dict[str, Any]] = None
    ) -> ConfigValidationResult:
        """Validate configuration against schema.

        Args:
            schema: Optional schema to validate against. If None, uses built-in schema.

        Returns:
            Validation result
        """
        pass


class EnvironmentAwareConfigProtocol(ConfigProtocol):
    """Extended protocol that includes environment-specific configurations."""

    @abstractmethod
    def get_environment(self) -> str:
        """Get the current environment.

        Returns:
            Current environment name (development, staging, production, etc.)
        """
        pass

    @abstractmethod
    def set_environment(self, environment: str) -> None:
        """Set the current environment.

        Args:
            environment: Environment name

        This may trigger a configuration reload.
        """
        pass
