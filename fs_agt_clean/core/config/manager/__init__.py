"""Configuration management for FlipSync."""

import os
from typing import Any, Dict, Optional

import yaml

# Global config manager instance
_config_manager = None


def get_config_manager() -> "ConfigManager":
    """Get the global config manager instance.

    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        config_path = os.environ.get("CONFIG_PATH", "/app/config/config.yaml")
        _config_manager = ConfigManager(config_path)
    return _config_manager


class ConfigManager:
    """Manages configuration settings for the application."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.

        Args:
            config_path: Optional path to the configuration file. If not provided, uses default empty config.
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        if config_path:
            self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        self.config = loaded_config
        except Exception as e:
            # Just log error and continue with empty config
            print(f"Warning: Failed to load config from {self.config_path}: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (can be nested using dots)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        try:
            value = self.config
            for part in key.split("."):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        if self.config_path:
            self._save_config()

    def _save_config(self) -> None:
        """Save configuration to file."""
        if not self.config_path:
            return
        try:
            with open(self.config_path, "w") as f:
                yaml.safe_dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Warning: Failed to save config to {self.config_path}: {str(e)}")

    def get_section(self, section: str) -> Optional[Dict[str, Any]]:
        """Get a configuration section.

        Args:
            section: Section name

        Returns:
            Section configuration or None if not found
        """
        return self.config.get(section)

    def update_section(self, section: str, values: Dict[str, Any]) -> None:
        """Update a configuration section.

        Args:
            section: Section name
            values: Section values
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section].update(values)
        if self.config_path:
            self._save_config()

    def delete_section(self, section: str) -> None:
        """Delete a configuration section.

        Args:
            section: Section name
        """
        if section in self.config:
            del self.config[section]
            if self.config_path:
                self._save_config()

    def clear(self) -> None:
        """Clear all configuration."""
        self.config = {}
        if self.config_path:
            self._save_config()


# Create a default manager instance for import
manager = ConfigManager()
