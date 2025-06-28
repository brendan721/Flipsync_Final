"""Environment variable handling for the Configuration Manager.

This module provides functionality to interpolate environment variables in
configuration values and to update configuration from environment variables.
"""

import os
import re
from typing import Any, Dict, List, Optional, Pattern, Tuple, Union

# Regular expression to match environment variable references in strings
# Supports both ${VAR} and $VAR formats
ENV_VAR_PATTERN: Pattern = re.compile(r"(?:\${([^}]+)}|\$([a-zA-Z0-9_]+))")


def interpolate_env_vars(value: Any) -> Any:
    """Interpolate environment variables in a value.

    This function replaces environment variable references in strings with
    their actual values from the environment. It supports both ${VAR} and
    $VAR formats.

    Args:
        value: Value that may contain environment variable references

    Returns:
        Value with environment variables replaced
    """
    if not isinstance(value, str):
        return value

    def replace_env_var(match: re.Match) -> str:
        """Replace a matched environment variable with its value."""
        # Extract var name (either from ${VAR} or $VAR format)
        var_name = match.group(1) if match.group(1) else match.group(2)

        # Get value from environment or return the original reference if not found
        env_value = os.environ.get(var_name)
        if env_value is None:
            # Return the original reference
            return match.group(0)

        return env_value

    # Replace all occurrences of env var patterns
    return ENV_VAR_PATTERN.sub(replace_env_var, value)


def interpolate_env_vars_in_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively interpolate environment variables in a configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with environment variables replaced
    """
    if not config:
        return config

    result = {}

    for key, value in config.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            result[key] = interpolate_env_vars_in_config(value)
        elif isinstance(value, list):
            # Process lists
            result[key] = [interpolate_env_vars(item) for item in value]
        else:
            # Process scalar values
            result[key] = interpolate_env_vars(value)

    return result


def update_from_env_vars(
    config: Dict[str, Any], prefix: str = "APP_", separator: str = "__"
) -> Dict[str, Any]:
    """Update configuration from environment variables.

    This function looks for environment variables with the specified prefix
    and updates the configuration based on their values. The environment
    variable names are mapped to configuration keys using the separator.

    For example, with prefix='APP_' and separator='__':
    - APP_DATABASE__HOST=localhost maps to {"database": {"host": "localhost"}}
    - APP_DEBUG=true maps to {"debug": true}

    Args:
        config: Configuration dictionary to update
        prefix: Prefix for environment variables to consider
        separator: Separator to convert env var names to nested keys

    Returns:
        Updated configuration dictionary
    """
    result = config.copy()

    # Find all environment variables with the specified prefix
    for env_name, env_value in os.environ.items():
        if not env_name.startswith(prefix):
            continue

        # Remove prefix and convert to nested keys
        key_path = env_name[len(prefix) :].split(separator)

        # Skip empty key paths
        if not key_path[0]:
            continue

        # Convert value to appropriate type
        typed_value = _convert_value_type(env_value)

        # Update config
        _set_nested_value(result, key_path, typed_value)

    return result


def _convert_value_type(value: str) -> Any:
    """Convert a string value to an appropriate type.

    Args:
        value: String value to convert

    Returns:
        Converted value with appropriate type
    """
    # Check for boolean values
    if value.lower() in ("true", "yes", "on", "1"):
        return True
    if value.lower() in ("false", "no", "off", "0"):
        return False

    # Check for integer
    try:
        return int(value)
    except ValueError:
        pass

    # Check for float
    try:
        return float(value)
    except ValueError:
        pass

    # Check for list (comma-separated values)
    if "," in value:
        # Split and convert each item
        return [_convert_value_type(item.strip()) for item in value.split(",")]

    # Default to string
    return value


def _set_nested_value(config: Dict[str, Any], key_path: List[str], value: Any) -> None:
    """Set a value in a nested dictionary based on a key path.

    Args:
        config: Dictionary to update
        key_path: List of keys representing the path
        value: Value to set
    """
    current = config

    # Navigate to the correct nested level
    for i, key in enumerate(key_path[:-1]):
        # Convert key to lowercase for case-insensitivity
        key = key.lower()

        # Create nested dictionaries if they don't exist
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            # Handle case where a key exists but is not a dict
            current[key] = {}

        current = current[key]

    # Set the value at the final key
    current[key_path[-1].lower()] = value
