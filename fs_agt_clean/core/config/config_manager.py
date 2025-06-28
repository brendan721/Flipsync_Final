# AGENT_CONTEXT: config_manager - Core FlipSync component with established patterns
"""Configuration manager implementation.

This module provides a unified configuration manager that implements
the ConfigProtocol interface. It supports environment-specific configurations,
dynamic reloading, change listeners, and validation.
"""

import json
import logging
import os
import re
import threading
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union

import yaml

from fs_agt_clean.core.config.interface import BaseConfigManager

# Define a type variable for base classes
T = TypeVar("T")

# Try to import watchdog for file system monitoring
# This is an optional dependency
try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

    # Create dummy classes for type checking when watchdog is not available
    class FileSystemEvent:
        """Dummy class for when watchdog is not available."""

        src_path: str = ""

    class FileSystemEventHandler:
        """Dummy class for when watchdog is not available."""

        def dispatch(self, event: Any) -> None:
            """Dummy dispatch method."""
            pass


from fs_agt_clean.core.config.config_protocol import (
    ConfigProtocol,
    ConfigValidationResult,
    EnvironmentAwareConfigProtocol,
)
from fs_agt_clean.core.config.encryption_handler import (
    ConfigEncryptionHandler,
    find_sensitive_keys,
)
from fs_agt_clean.core.config.env_handler import (
    interpolate_env_vars_in_config,
    update_from_env_vars,
)


# Define event handler type that works whether watchdog is available or not
class ConfigChangeHandler(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """Watchdog event handler that triggers configuration reloading."""

    def __init__(self, callback: Callable[[str], None]):
        """Initialize the handler.

        Args:
            callback: Function to call when a file changes
        """
        super().__init__()
        self.callback = callback

    def on_modified(self, event):
        """Handle file modification events.

        Args:
            event: File system event
        """
        if hasattr(event, "is_directory") and not event.is_directory:
            self.callback(event.src_path)


class ConfigManager(BaseConfigManager, EnvironmentAwareConfigProtocol):
    """Unified configuration manager implementation.

    This class implements the EnvironmentAwareConfigProtocol interface and
    provides a comprehensive configuration management solution that combines
    the best features of all existing implementations.

    Features:
    - Singleton pattern for global access
    - Thread-safe operations
    - Environment-specific configuration
    - Dynamic reloading
    - Change notification
    - Schema validation
    - YAML and JSON support
    - Environment variable interpolation
    - Configuration encryption
    """

    _instance = None
    _lock = RLock()

    def __new__(cls, *args, **kwargs):
        """Create or return the singleton instance.

        This implements the singleton pattern to ensure that only one
        configuration manager exists in the application.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        config_dir: Optional[Union[str, Path]] = None,
        environment: Optional[str] = None,
        auto_reload: bool = False,
        env_var_prefix: Optional[str] = None,
        env_var_separator: str = "__",
        encryption_key: Optional[Union[str, bytes]] = None,
        encryption_key_file: Optional[Union[str, Path]] = None,
        encryption_password: Optional[str] = None,
    ):
        """Initialize the configuration manager.

        Args:
            config_dir: Directory to search for configuration files.
            environment: Current environment name (e.g., "development", "production").
            auto_reload: Whether to automatically reload configuration when files change.
            env_var_prefix: Prefix for environment variables to load into configuration.
            env_var_separator: Separator for nested keys in environment variables.
            encryption_key: Key to use for encrypting/decrypting sensitive configuration values.
            encryption_key_file: Path to file containing encryption key.
            encryption_password: Password to derive encryption key from.
        """
        with self._lock:
            if self._initialized:
                return

            self.logger = logging.getLogger(__name__)

            # Core properties
            self.config_data: Dict[str, Any] = {}
            self.config_paths: Set[Path] = set()
            self._environment = environment or os.environ.get(
                "APP_ENVIRONMENT", "development"
            )
            self._schema: Dict[str, Any] = {}
            self._change_listeners: List[Callable[[str, Any], None]] = []

            # Environment variable settings
            self._env_var_prefix = env_var_prefix
            self._env_var_separator = env_var_separator

            # File watching
            self._auto_reload = auto_reload and WATCHDOG_AVAILABLE
            if auto_reload and not WATCHDOG_AVAILABLE:
                self.logger.warning(
                    "Auto-reload is enabled but watchdog package is not installed. "
                    "Automatic configuration reloading will be disabled."
                )

            self._observers: List[Observer] = []
            self._file_watchers: Dict[str, tuple] = {}

            # Set config directory
            if config_dir:
                self.config_dir = Path(config_dir)
            else:
                # Try to find config directory in common locations
                for path in ["config", "fs_agt/config", "../config"]:
                    if Path(path).exists():
                        self.config_dir = Path(path)
                        break
                else:
                    self.config_dir = Path("config")  # Default

            # Create config directory if it doesn't exist
            os.makedirs(self.config_dir, exist_ok=True)

            # Initialize encryption handler if encryption is enabled
            self._encryption_handler = None
            if encryption_key or encryption_key_file or encryption_password:
                self._encryption_handler = ConfigEncryptionHandler(
                    key=encryption_key,
                    key_file=encryption_key_file,
                    password=encryption_password,
                )

            # Try to load default configs
            self._try_load_default_configs()

            self._initialized = True

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'database.host')
            default: Default value if key not found

        Returns:
            Configuration value or default if not found
        """
        with self._lock:
            if not key:
                return self.config_data

            keys = key.split(".")
            value = self.config_data

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'database.host')
            value: Value to set
        """
        with self._lock:
            keys = key.split(".")
            config = self.config_data

            for i, k in enumerate(keys[:-1]):
                if k not in config:
                    config[k] = {}
                elif not isinstance(config[k], dict):
                    config[k] = {}
                config = config[k]

            old_value = config.get(keys[-1])
            if old_value != value:
                config[keys[-1]] = value
                self._notify_change_listeners(key, value)

    def load(self, config_path: Union[str, Path]) -> None:
        """Load configuration from YAML or JSON file.

        Args:
            config_path: Path to configuration file

        Raises:
            FileNotFoundError: If configuration file not found
            ValueError: If configuration file cannot be parsed
        """
        with self._lock:
            # Convert to absolute path if relative
            path = Path(config_path)
            if not path.is_absolute():
                path = self.config_dir / path

            if not path.exists():
                raise FileNotFoundError(f"Configuration file not found: {path}")

            self.config_paths.add(path)

            try:
                with open(path, "r") as f:
                    if path.suffix.lower() in [".yaml", ".yml"]:
                        config_data = yaml.safe_load(f)
                    elif path.suffix.lower() == ".json":
                        config_data = json.load(f)
                    else:
                        raise ValueError(
                            f"Unsupported configuration format: {path.suffix}"
                        )
            except Exception as e:
                self.logger.error(
                    "Error loading configuration file %s: %s", path, str(e)
                )
                raise ValueError(f"Failed to parse configuration file: {str(e)}")

            if not config_data:
                self.logger.warning("Configuration file %s is empty", path)
                return

            # Apply environment variable interpolation
            if self._env_var_prefix or "$" in str(config_data):
                config_data = interpolate_env_vars_in_config(config_data)

            # Decrypt any encrypted values if encryption is enabled
            if self._encryption_handler:
                config_data = self._encryption_handler.decrypt_config(config_data)

            # Apply environment-specific overrides
            if self._environment and "environments" in config_data:
                env_config = config_data.get("environments", {}).get(
                    self._environment, {}
                )
                if env_config:
                    self._deep_merge(config_data, env_config)

            # Apply environment variable updates if prefix is set
            if self._env_var_prefix:
                config_data = update_from_env_vars(
                    config_data,
                    prefix=self._env_var_prefix,
                    separator=self._env_var_separator,
                )

            # Save schema if this is a schema file
            if path.name == "schema.yaml" or path.name == "schema.yml":
                self._schema = config_data
            else:
                # Merge with existing configuration
                self._deep_merge(self.config_data, config_data)

            # Set up file watcher if auto_reload is enabled
            if self._auto_reload:
                self._setup_file_watcher(path)

            self.logger.info("Loaded configuration from %s", path)

    def reload(self) -> None:
        """Reload configuration from all previously loaded files.

        This method reloads all configuration files that were previously loaded.
        It's useful when configuration files have changed on disk.
        """
        with self._lock:
            self.logger.info("Reloading configuration")
            old_config = self.config_data.copy()
            self.config_data = {}

            # Re-load all files in original order
            errors = []
            for path in self.config_paths:
                try:
                    self.load(path)
                except Exception as e:
                    errors.append(f"Error reloading {path}: {str(e)}")

            if errors:
                error_msg = "; ".join(errors)
                self.logger.error("Errors during configuration reload: %s", error_msg)

            # Apply environment variables if prefix is set
            if self._env_var_prefix:
                self.config_data = update_from_env_vars(
                    self.config_data,
                    prefix=self._env_var_prefix,
                    separator=self._env_var_separator,
                )

            # Notify listeners about all changes
            self._notify_all_change_listeners(old_config)

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section.

        Args:
            section: Section name

        Returns:
            Dictionary containing the section configuration
        """
        with self._lock:
            return self.get(section, {})

    def register_change_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for configuration changes.

        Args:
            callback: Function to call when configuration changes.
                     Should accept (key, value) parameters.
        """
        with self._lock:
            if callback not in self._change_listeners:
                self._change_listeners.append(callback)

    def validate(
        self, schema: Optional[Dict[str, Any]] = None
    ) -> ConfigValidationResult:
        """Validate configuration against schema.

        Args:
            schema: Optional schema to validate against. If None, uses built-in schema.

        Returns:
            Validation result
        """
        with self._lock:
            errors = []
            warnings = []

            validation_schema = schema or self._schema

            if not validation_schema:
                warnings.append("No schema available for validation")
                return ConfigValidationResult(True, errors, warnings)

            def validate_section(
                config_section: Dict[str, Any],
                schema_section: Dict[str, Any],
                path: str = "",
            ):
                """Validate a single section of the configuration.

                Args:
                    config_section: Configuration section to validate
                    schema_section: Schema section to validate against
                    path: Path to this section (for error reporting)
                """
                for key, schema_item in schema_section.items():
                    item_path = f"{path}.{key}" if path else key

                    # Check if required
                    required = schema_item.get("required", False)
                    if required and (key not in config_section):
                        errors.append(f"Missing required config value: {item_path}")
                        continue

                    # Skip validation if key doesn't exist and isn't required
                    if key not in config_section:
                        continue

                    value = config_section[key]

                    # Check type
                    if "type" in schema_item:
                        type_name = schema_item["type"]
                        expected_type = self._get_type(type_name)
                        if expected_type and not isinstance(value, expected_type):
                            errors.append(
                                f"Invalid type for {item_path}: expected {type_name}, got {type(value).__name__}"
                            )

                    # Check nested schema
                    if schema_item.get("properties") and isinstance(value, dict):
                        validate_section(value, schema_item["properties"], item_path)

                    # Check constraints
                    if schema_item.get("constraints"):
                        for constraint, constraint_value in schema_item[
                            "constraints"
                        ].items():
                            if not self._validate_constraint(
                                value, constraint, constraint_value
                            ):
                                errors.append(
                                    f"Constraint violation for {item_path}: {constraint}={constraint_value}"
                                )

                    # Check if deprecated
                    if schema_item.get("deprecated", False):
                        warnings.append(f"Using deprecated configuration: {item_path}")

            validate_section(self.config_data, validation_schema)
            return ConfigValidationResult(len(errors) == 0, errors, warnings)

    def get_environment(self) -> str:
        """Get the current environment.

        Returns:
            Current environment name (development, staging, production, etc.)
        """
        with self._lock:
            return self._environment

    def set_environment(self, environment: str) -> None:
        """Set the current environment.

        Args:
            environment: Environment name

        This triggers a configuration reload.
        """
        with self._lock:
            if self._environment != environment:
                self.logger.info(
                    "Changing environment from %s to %s", self._environment, environment
                )
                self._environment = environment
                self.reload()

    def _try_load_default_configs(self) -> None:
        """Try to load default configuration files."""
        default_files = ["base.yaml", f"{self._environment}.yaml", "schema.yaml"]

        for file in default_files:
            file_path = self.config_dir / file
            if file_path.exists():
                try:
                    self.load(file_path)
                except Exception as e:
                    self.logger.warning(
                        "Failed to load default config %s: %s", file_path, str(e)
                    )

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dict into target dict.

        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _setup_file_watcher(self, path: Path) -> None:
        """Set up a file watcher for automatic reloading.

        Args:
            path: Path to the file to watch
        """
        if not WATCHDOG_AVAILABLE:
            return

        path_str = str(path)
        if path_str in self._file_watchers:
            return

        observer = Observer()
        handler = ConfigChangeHandler(self._on_config_file_changed)
        observer.schedule(handler, path=path.parent, recursive=False)
        observer.start()

        self._observers.append(observer)
        self._file_watchers[path_str] = (observer, handler)

    def _on_config_file_changed(self, file_path: str) -> None:
        """Handle configuration file changes.

        Args:
            file_path: Path to the file that changed
        """
        if file_path in [str(p) for p in self.config_paths]:
            self.logger.info("Detected change in configuration file: %s", file_path)
            self.reload()

    def _notify_change_listeners(self, key: str, value: Any) -> None:
        """Notify all registered listeners of a configuration change.

        Args:
            key: Configuration key that changed
            value: New value
        """
        for listener in self._change_listeners:
            try:
                listener(key, value)
            except Exception as e:
                # Log error but don't break the notification chain
                self.logger.error("Error in config change listener: %s", str(e))

    def _notify_all_change_listeners(self, old_config: Dict[str, Any]) -> None:
        """Notify listeners of all configuration changes after reload.

        Args:
            old_config: Previous configuration dictionary
        """

        def find_changes(old: Dict[str, Any], new: Dict[str, Any], prefix: str = ""):
            for key, value in new.items():
                full_key = f"{prefix}.{key}" if prefix else key

                if key not in old:
                    self._notify_change_listeners(full_key, value)
                elif isinstance(value, dict) and isinstance(old[key], dict):
                    find_changes(old[key], value, full_key)
                elif old[key] != value:
                    self._notify_change_listeners(full_key, value)

        find_changes(old_config, self.config_data)

    def _get_type(self, type_name: str) -> Optional[Type]:
        """Get Python type from schema type name.

        Args:
            type_name: Type name from schema

        Returns:
            Python type or None if type name is unknown
        """
        type_map = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        return type_map.get(type_name)

    def _validate_constraint(
        self, value: Any, constraint: str, constraint_value: Any
    ) -> bool:
        """Validate a configuration value against a constraint.

        Args:
            value: Value to validate
            constraint: Constraint type
            constraint_value: Constraint value

        Returns:
            True if valid, False otherwise
        """
        if constraint == "min":
            return bool(value >= constraint_value)
        elif constraint == "max":
            return value <= constraint_value
        elif constraint == "pattern":
            return bool(re.match(constraint_value, str(value)))
        elif constraint == "enum":
            return value in constraint_value
        elif constraint == "length":
            return bool(len(value) == constraint_value)
        elif constraint == "min_length":
            return len(value) >= constraint_value
        elif constraint == "max_length":
            return len(value) <= constraint_value
        return True

    def update_from_env_vars(self, prefix: str = "APP_", separator: str = "__") -> None:
        """Update configuration from environment variables.

        This method looks for environment variables with the specified prefix
        and updates the configuration based on their values. The environment
        variable names are mapped to configuration keys using the separator.

        For example, with prefix='APP_' and separator='__':
        - APP_DATABASE__HOST=localhost maps to config.set("database.host", "localhost")
        - APP_DEBUG=true maps to config.set("debug", true)

        Args:
            prefix: Prefix for environment variables to consider
            separator: Separator to convert env var names to nested keys
        """
        with self._lock:
            old_config = self.config_data.copy()

            # Update config from environment variables
            self.config_data = update_from_env_vars(
                self.config_data, prefix=prefix, separator=separator
            )

            # Remember settings for reload
            self._env_var_prefix = prefix
            self._env_var_separator = separator

            # Notify listeners about changes
            self._notify_all_change_listeners(old_config)

    def encrypt_value(self, value: Any) -> str:
        """Encrypt a configuration value.

        Args:
            value: The value to encrypt.

        Returns:
            An encrypted string representation of the value.

        Raises:
            ValueError: If encryption is not enabled or key is not available.
        """
        if not self._encryption_handler:
            raise ValueError(
                "Encryption is not enabled. Initialize ConfigManager with encryption parameters."
            )

        return self._encryption_handler.encrypt(value)

    def decrypt_value(self, value: str) -> Any:
        """Decrypt an encrypted configuration value.

        Args:
            value: The encrypted value to decrypt.

        Returns:
            The decrypted value.

        Raises:
            ValueError: If encryption is not enabled or value is not encrypted.
        """
        if not self._encryption_handler:
            raise ValueError(
                "Encryption is not enabled. Initialize ConfigManager with encryption parameters."
            )

        return self._encryption_handler.decrypt(value)

    def is_encrypted(self, value: Any) -> bool:
        """Check if a value is encrypted.

        Args:
            value: The value to check.

        Returns:
            True if the value is encrypted, False otherwise.
        """
        if not self._encryption_handler:
            return False

        return self._encryption_handler.is_encrypted(value)

    def encrypt_sensitive_values(self, patterns: Optional[List[str]] = None) -> None:
        """Encrypt sensitive values in the configuration.

        Args:
            patterns: List of patterns to identify sensitive keys. If not provided,
                     a default list will be used.

        Raises:
            ValueError: If encryption is not enabled.
        """
        if not self._encryption_handler:
            raise ValueError(
                "Encryption is not enabled. Initialize ConfigManager with encryption parameters."
            )

        sensitive_keys = find_sensitive_keys(self.config_data, patterns)

        # Create a new config with encrypted values
        encrypted_config = self._encryption_handler.encrypt_config(
            self.config_data, sensitive_keys
        )

        # Track old config for change notifications
        old_config = self.config_data.copy()

        # Update the configuration
        with self._lock:
            self.config_data = encrypted_config

        # Notify listeners of changes
        self._notify_all_change_listeners(old_config)

    def generate_encryption_key(
        self, key_file: Optional[Union[str, Path]] = None
    ) -> bytes:
        """Generate a new encryption key and optionally save it to a file.

        Args:
            key_file: Path to save the key to. If not provided, the key will not be saved.

        Returns:
            The generated key as bytes.

        Raises:
            ValueError: If encryption is not enabled.
        """
        if not self._encryption_handler:
            self._encryption_handler = ConfigEncryptionHandler()

        key = self._encryption_handler.generate_key()

        if key_file:
            self._encryption_handler.save_key_to_file(key_file)

        return key

    def __del__(self):
        """Clean up observers when object is deleted."""
        try:
            for observer in self._observers:
                observer.stop()
                observer.join()
        except Exception:
            pass
