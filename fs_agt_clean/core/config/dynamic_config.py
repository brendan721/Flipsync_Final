"""Dynamic configuration management for FlipSync."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class DynamicConfig:
    """Dynamic configuration management class."""

    config_path: Path
    values: Dict[str, Any] = field(default_factory=dict)
    last_updated: Optional[datetime] = None
    auto_save: bool = True

    def __post_init__(self):
        """Initialize after dataclass creation."""
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    self.values = json.load(f)
                self.last_updated = datetime.fromtimestamp(
                    self.config_path.stat().st_mtime
                )
                logger.info("Loaded configuration from %s", self.config_path)
            else:
                logger.warning(
                    "Configuration file %s not found, using defaults", self.config_path
                )
        except Exception as e:
            logger.error("Error loading configuration: %s", str(e))
            self.values = {}

    def save(self) -> None:
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.values, f, indent=2)
            self.last_updated = datetime.now()
            logger.info("Saved configuration to %s", self.config_path)
        except Exception as e:
            logger.error("Error saving configuration: %s", str(e))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.values[key] = value
        if self.auto_save:
            self.save()

    def update(self, values: Dict[str, Any]) -> None:
        """Update multiple configuration values.

        Args:
            values: Dictionary of configuration values
        """
        self.values.update(values)
        if self.auto_save:
            self.save()

    def delete(self, key: str) -> None:
        """Delete configuration value.

        Args:
            key: Configuration key
        """
        if key in self.values:
            del self.values[key]
            if self.auto_save:
                self.save()

    def clear(self) -> None:
        """Clear all configuration values."""
        self.values.clear()
        if self.auto_save:
            self.save()

    def reload(self) -> None:
        """Reload configuration from file."""
        self.load()

    @property
    def is_empty(self) -> bool:
        """Check if configuration is empty.

        Returns:
            bool: True if empty
        """
        return not bool(self.values)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration.

        Args:
            key: Configuration key

        Returns:
            bool: True if key exists
        """
        return key in self.values
