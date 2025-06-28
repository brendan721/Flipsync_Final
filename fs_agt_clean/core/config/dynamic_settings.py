"""
Dynamic settings configuration with validation.

This module provides a system for runtime configuration changes with validation
and secure storage of sensitive configuration.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, get_type_hints

from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model

logger = logging.getLogger(__name__)


class SettingType(str, Enum):
    """Setting type for validation."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    PASSWORD = "password"
    EMAIL = "email"
    URL = "url"
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    CHOICE = "choice"
    LIST = "list"


class SettingVisibility(str, Enum):
    """Setting visibility levels."""

    PUBLIC = "public"  # Visible to all users
    PROTECTED = "protected"  # Visible in UI, but values masked
    PRIVATE = "private"  # Not visible in UI, only through API
    INTERNAL = "internal"  # Not visible at all, only accessible programmatically


class SettingSensitivity(str, Enum):
    """Setting sensitivity levels."""

    NORMAL = "normal"  # Normal setting, stored in plain text
    SENSITIVE = "sensitive"  # Sensitive setting, stored with encryption
    SECRET = "secret"  # Secret setting, stored with encryption and not logged


class SettingSchema(BaseModel):
    """Schema for a dynamic setting."""

    key: str = Field(..., description="Unique key for the setting")
    type: SettingType = Field(SettingType.STRING, description="Setting type")
    default: Any = Field(None, description="Default value")
    description: str = Field("", description="Description of the setting")
    required: bool = Field(False, description="Whether the setting is required")
    visibility: SettingVisibility = Field(
        SettingVisibility.PUBLIC, description="Visibility level"
    )
    sensitivity: SettingSensitivity = Field(
        SettingSensitivity.NORMAL, description="Sensitivity level"
    )
    group: str = Field("general", description="Setting group")
    options: List[Any] = Field(
        default_factory=list, description="Options for choice type"
    )
    validators: List[str] = Field(
        default_factory=list, description="Validator functions"
    )
    min_value: Optional[Union[int, float]] = Field(
        None, description="Minimum value for numeric types"
    )
    max_value: Optional[Union[int, float]] = Field(
        None, description="Maximum value for numeric types"
    )
    regex_pattern: Optional[str] = Field(
        None, description="Regex pattern for string validation"
    )
    immutable: bool = Field(
        False, description="Whether the setting is immutable after startup"
    )
    restart_required: bool = Field(
        False, description="Whether a restart is required after changing"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class SettingValue(BaseModel):
    """Value for a dynamic setting."""

    key: str = Field(..., description="Setting key")
    value: Any = Field(None, description="Setting value")
    schema_key: str = Field(..., description="Schema key")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )
    source: str = Field("default", description="Source of the setting value")
    overridden: bool = Field(False, description="Whether the setting is overridden")


class DynamicSettingsConfig(BaseModel):
    """Configuration for dynamic settings."""

    schemas: Dict[str, SettingSchema] = Field(
        default_factory=dict, description="Setting schemas"
    )
    values: Dict[str, SettingValue] = Field(
        default_factory=dict, description="Setting values"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )


class ValidationResult(BaseModel):
    """Result of setting validation."""

    valid: bool = Field(True, description="Whether the setting is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    value: Any = Field(None, description="Converted value")

    class Config:
        """Pydantic config for ValidationResult."""

        extra = "ignore"  # Allow extra attributes


class SettingValidator:
    """Validator for settings."""

    @staticmethod
    def create_result(
        valid: bool, errors: Optional[List[str]] = None, value: Any = None
    ) -> ValidationResult:
        """Create a validation result with proper parameters.

        Args:
            valid: Whether the setting is valid
            errors: Validation errors
            value: Converted value

        Returns:
            Validation result
        """
        return ValidationResult(valid=valid, errors=errors or [], value=value)

    @staticmethod
    def validate_string(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate a string setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        if not isinstance(value, str):
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be a string, got {type(value).__name__}"],
                value=value,
            )

        if schema.regex_pattern:
            import re

            if not re.match(schema.regex_pattern, value):
                return SettingValidator.create_result(
                    valid=False,
                    errors=[f"Value does not match pattern: {schema.regex_pattern}"],
                    value=value,
                )

        return SettingValidator.create_result(valid=True, value=value)

    @staticmethod
    def validate_integer(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate an integer setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be an integer, got {type(value).__name__}"],
                value=value,
            )

        if schema.min_value is not None and int_value < schema.min_value:
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be greater than or equal to {schema.min_value}"],
                value=int_value,
            )

        if schema.max_value is not None and int_value > schema.max_value:
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be less than or equal to {schema.max_value}"],
                value=int_value,
            )

        return SettingValidator.create_result(valid=True, value=int_value)

    @staticmethod
    def validate_float(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate a float setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be a number, got {type(value).__name__}"],
                value=value,
            )

        if schema.min_value is not None and float_value < schema.min_value:
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be greater than or equal to {schema.min_value}"],
                value=float_value,
            )

        if schema.max_value is not None and float_value > schema.max_value:
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be less than or equal to {schema.max_value}"],
                value=float_value,
            )

        return SettingValidator.create_result(valid=True, value=float_value)

    @staticmethod
    def validate_boolean(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate a boolean setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        if isinstance(value, bool):
            return SettingValidator.create_result(valid=True, value=value)

        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ("true", "yes", "1", "y", "t"):
                return SettingValidator.create_result(valid=True, value=True)
            if lower_value in ("false", "no", "0", "n", "f"):
                return SettingValidator.create_result(valid=True, value=False)

        if isinstance(value, int):
            if value == 1:
                return SettingValidator.create_result(valid=True, value=True)
            if value == 0:
                return SettingValidator.create_result(valid=True, value=False)

        return SettingValidator.create_result(
            valid=False,
            errors=[f"Value must be a boolean, got {type(value).__name__}"],
            value=value,
        )

    @staticmethod
    def validate_json(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate a JSON setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        if isinstance(value, (dict, list)):
            return SettingValidator.create_result(valid=True, value=value)

        if isinstance(value, str):
            try:
                json_value = json.loads(value)
                return SettingValidator.create_result(valid=True, value=json_value)
            except json.JSONDecodeError:
                return SettingValidator.create_result(
                    valid=False, errors=["Value is not valid JSON"], value=value
                )

        return SettingValidator.create_result(
            valid=False,
            errors=[f"Value must be JSON, got {type(value).__name__}"],
            value=value,
        )

    @staticmethod
    def validate_choice(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate a choice setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        if not schema.options:
            return SettingValidator.create_result(
                valid=False,
                errors=["No options defined for choice setting"],
                value=value,
            )

        if value not in schema.options:
            return SettingValidator.create_result(
                valid=False,
                errors=[
                    f"Value must be one of: {', '.join(str(o) for o in schema.options)}"
                ],
                value=value,
            )

        return SettingValidator.create_result(valid=True, value=value)

    @staticmethod
    def validate_list(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate a list setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        if isinstance(value, list):
            return SettingValidator.create_result(valid=True, value=value)

        if isinstance(value, str):
            try:
                list_value = json.loads(value)
                if not isinstance(list_value, list):
                    return SettingValidator.create_result(
                        valid=False, errors=["Value must be a list"], value=value
                    )
                return SettingValidator.create_result(valid=True, value=list_value)
            except json.JSONDecodeError:
                # Try comma-separated values
                list_value = [item.strip() for item in value.split(",")]
                return SettingValidator.create_result(valid=True, value=list_value)

        return SettingValidator.create_result(
            valid=False,
            errors=[f"Value must be a list, got {type(value).__name__}"],
            value=value,
        )

    @staticmethod
    def validate_file_path(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate a file path setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        if not isinstance(value, str):
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be a string, got {type(value).__name__}"],
                value=value,
            )

        path = Path(value)

        # If the path doesn't exist and that's required, check if it's a valid path
        if not path.exists():
            try:
                # Just check if it's a valid path
                path.absolute()
                return SettingValidator.create_result(valid=True, value=value)
            except (OSError, RuntimeError):
                return SettingValidator.create_result(
                    valid=False, errors=["Invalid file path"], value=value
                )

        # If the file exists, check that it's a file
        if not path.is_file():
            return SettingValidator.create_result(
                valid=False, errors=["Path exists but is not a file"], value=value
            )

        return SettingValidator.create_result(valid=True, value=value)

    @staticmethod
    def validate_directory_path(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate a directory path setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        if not isinstance(value, str):
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be a string, got {type(value).__name__}"],
                value=value,
            )

        path = Path(value)

        # If the path doesn't exist and that's required, check if it's a valid path
        if not path.exists():
            try:
                # Just check if it's a valid path
                path.absolute()
                return SettingValidator.create_result(valid=True, value=value)
            except (OSError, RuntimeError):
                return SettingValidator.create_result(
                    valid=False, errors=["Invalid directory path"], value=value
                )

        # If the directory exists, check that it's a directory
        if not path.is_dir():
            return SettingValidator.create_result(
                valid=False, errors=["Path exists but is not a directory"], value=value
            )

        return SettingValidator.create_result(valid=True, value=value)

    @staticmethod
    def validate_email(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate an email setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        if not isinstance(value, str):
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be a string, got {type(value).__name__}"],
                value=value,
            )

        # Simple email validation
        if "@" not in value or "." not in value:
            return SettingValidator.create_result(
                valid=False, errors=["Invalid email address"], value=value
            )

        return SettingValidator.create_result(valid=True, value=value)

    @staticmethod
    def validate_url(value: Any, schema: SettingSchema) -> ValidationResult:
        """Validate a URL setting.

        Args:
            value: Setting value
            schema: Setting schema

        Returns:
            Validation result
        """
        if not isinstance(value, str):
            return SettingValidator.create_result(
                valid=False,
                errors=[f"Value must be a string, got {type(value).__name__}"],
                value=value,
            )

        # Simple URL validation
        if not value.startswith(("http://", "https://")):
            return SettingValidator.create_result(
                valid=False,
                errors=["URL must start with http:// or https://"],
                value=value,
            )

        return SettingValidator.create_result(valid=True, value=value)


class DynamicSettingsService:
    """Service for dynamic settings."""

    def __init__(self, config_path: Union[str, Path], encryption_handler=None):
        """Initialize the dynamic settings service.

        Args:
            config_path: Path to the settings configuration file
            encryption_handler: Optional encryption handler for sensitive settings
        """
        self.config_path = Path(config_path)
        self.encryption_handler = encryption_handler
        self.config: DynamicSettingsConfig = DynamicSettingsConfig()
        self._last_read_time: float = 0
        self._read_interval: float = 5.0  # seconds
        self._initialized: bool = False
        self._validators: Dict[str, Callable] = {
            SettingType.STRING: SettingValidator.validate_string,
            SettingType.INTEGER: SettingValidator.validate_integer,
            SettingType.FLOAT: SettingValidator.validate_float,
            SettingType.BOOLEAN: SettingValidator.validate_boolean,
            SettingType.JSON: SettingValidator.validate_json,
            SettingType.CHOICE: SettingValidator.validate_choice,
            SettingType.LIST: SettingValidator.validate_list,
            SettingType.FILE_PATH: SettingValidator.validate_file_path,
            SettingType.DIRECTORY_PATH: SettingValidator.validate_directory_path,
            SettingType.EMAIL: SettingValidator.validate_email,
            SettingType.URL: SettingValidator.validate_url,
        }
        self._change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._load()

    def _load(self) -> None:
        """Load settings from storage."""
        if not self.config_path.exists():
            logger.info(
                "Settings configuration file %s does not exist, creating default config",
                self.config_path,
            )
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            self._save()
            return

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

                # Convert raw data to DynamicSettingsConfig
                schemas = {}
                for key, schema_data in data.get("schemas", {}).items():
                    schemas[key] = SettingSchema(**schema_data)

                values = {}
                for key, value_data in data.get("values", {}).items():
                    # Convert string timestamps to datetime
                    if "last_updated" in value_data and isinstance(
                        value_data["last_updated"], str
                    ):
                        value_data["last_updated"] = datetime.fromisoformat(
                            value_data["last_updated"]
                        )

                    # Decrypt sensitive values
                    if self.encryption_handler and key in schemas:
                        schema = schemas[key]
                        if schema.sensitivity in (
                            SettingSensitivity.SENSITIVE,
                            SettingSensitivity.SECRET,
                        ):
                            if "value" in value_data and value_data["value"]:
                                try:
                                    value_data["value"] = (
                                        self.encryption_handler.decrypt(
                                            value_data["value"]
                                        )
                                    )
                                except Exception as e:
                                    logger.error(
                                        "Error decrypting setting %s: %s", key, str(e)
                                    )
                                    # Use default value if decryption fails
                                    value_data["value"] = schema.default

                    values[key] = SettingValue(**value_data)

                last_updated = data.get("last_updated")
                if last_updated and isinstance(last_updated, str):
                    last_updated = datetime.fromisoformat(last_updated)
                else:
                    last_updated = datetime.now()

                self.config = DynamicSettingsConfig(
                    schemas=schemas, values=values, last_updated=last_updated
                )

                self._last_read_time = time.time()
                self._initialized = True
                logger.info(
                    "Loaded %s setting schemas and %s setting values from %s",
                    len(schemas),
                    len(values),
                    self.config_path,
                )
        except Exception as e:
            logger.error("Error loading settings: %s", str(e))
            # Create default config if loading fails
            self._initialized = True
            self._save()

    def _save(self) -> None:
        """Save settings to storage."""
        try:
            # Update last_updated timestamp
            self.config.last_updated = datetime.now()

            # Convert to serializable dict
            schemas_dict = {
                key: schema.dict() for key, schema in self.config.schemas.items()
            }

            values_dict = {}
            for key, value in self.config.values.items():
                value_dict = value.dict()

                # Encrypt sensitive values
                if self.encryption_handler and key in self.config.schemas:
                    schema = self.config.schemas[key]
                    if schema.sensitivity in (
                        SettingSensitivity.SENSITIVE,
                        SettingSensitivity.SECRET,
                    ):
                        if "value" in value_dict and value_dict["value"]:
                            try:
                                value_dict["value"] = self.encryption_handler.encrypt(
                                    value_dict["value"]
                                )
                            except Exception as e:
                                logger.error(
                                    "Error encrypting setting %s: %s", key, str(e)
                                )
                                # Skip saving this value if encryption fails
                                continue

                values_dict[key] = value_dict

            data = {
                "schemas": schemas_dict,
                "values": values_dict,
                "last_updated": self.config.last_updated.isoformat(),
            }

            # Create parent directories if they don't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(
                "Saved %s setting schemas and %s setting values to %s",
                len(schemas_dict),
                len(values_dict),
                self.config_path,
            )
        except Exception as e:
            logger.error("Error saving settings: %s", str(e))

    def _check_for_changes(self) -> None:
        """Check for changes in the settings configuration file."""
        current_time = time.time()
        if current_time - self._last_read_time < self._read_interval:
            return

        if not self.config_path.exists():
            logger.warning(
                "Settings configuration file %s does not exist", self.config_path
            )
            return

        file_mtime = self.config_path.stat().st_mtime
        if file_mtime > self._last_read_time:
            logger.info("Settings configuration file has changed, reloading")
            old_values = {key: value.value for key, value in self.config.values.items()}
            self._load()

            # Notify listeners of changes
            new_values = {key: value.value for key, value in self.config.values.items()}
            changes = {}

            for key, value in new_values.items():
                if key not in old_values or old_values[key] != value:
                    changes[key] = {"new": value, "old": old_values.get(key)}

            for key, value in old_values.items():
                if key not in new_values:
                    changes[key] = {"new": None, "old": value}

            if changes:
                for listener in self._change_listeners:
                    try:
                        listener(changes)
                    except Exception as e:
                        logger.error("Error notifying settings listener: %s", str(e))

    def validate_setting(self, key: str, value: Any) -> ValidationResult:
        """Validate a setting value against its schema.

        Args:
            key: Setting key
            value: Setting value

        Returns:
            Validation result

        Raises:
            ValueError: If setting schema is not found
        """
        schema = self.config.schemas.get(key)
        if not schema:
            raise ValueError(f"Setting schema not found for key: {key}")

        # Skip validation for None if not required
        if value is None and not schema.required:
            return SettingValidator.create_result(valid=True, value=None)

        # Check if setting is required
        if value is None and schema.required:
            return SettingValidator.create_result(
                valid=False, errors=["Setting is required"], value=None
            )

        # Get validator function for setting type
        validator = self._validators.get(schema.type)
        if not validator:
            logger.warning("No validator found for setting type: %s", schema.type)
            return SettingValidator.create_result(valid=True, value=value)

        # Validate setting value
        return validator(value, schema)

    def add_schema(self, schema: SettingSchema) -> None:
        """Add a setting schema.

        Args:
            schema: Setting schema

        Raises:
            ValueError: If setting schema already exists
        """
        if schema.key in self.config.schemas:
            raise ValueError(f"Setting schema already exists for key: {schema.key}")

        self.config.schemas[schema.key] = schema

        # Add default value if not already set
        if schema.key not in self.config.values and schema.default is not None:
            self.config.values[schema.key] = SettingValue(
                key=schema.key,
                value=schema.default,
                schema_key=schema.key,
                source="default",
                overridden=False,
            )

        self._save()

    def update_schema(self, schema: SettingSchema) -> None:
        """Update a setting schema.

        Args:
            schema: Setting schema

        Raises:
            ValueError: If setting schema is not found
        """
        if schema.key not in self.config.schemas:
            raise ValueError(f"Setting schema not found for key: {schema.key}")

        old_schema = self.config.schemas[schema.key]

        # Check if immutable flag is being changed
        if old_schema.immutable and not schema.immutable:
            logger.warning("Changing immutable flag for setting: %s", schema.key)

        self.config.schemas[schema.key] = schema

        # Update default value if not already set
        if schema.key not in self.config.values and schema.default is not None:
            self.config.values[schema.key] = SettingValue(
                key=schema.key,
                value=schema.default,
                schema_key=schema.key,
                source="default",
                overridden=False,
            )

        self._save()

    def delete_schema(self, key: str) -> bool:
        """Delete a setting schema.

        Args:
            key: Setting key

        Returns:
            True if schema was deleted, False otherwise
        """
        if key not in self.config.schemas:
            return bool(False)

        schema = self.config.schemas[key]
        if schema.immutable:
            logger.warning("Cannot delete immutable setting: %s", key)
            return False

        del self.config.schemas[key]

        # Delete associated value
        if key in self.config.values:
            del self.config.values[key]

        self._save()
        return True

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a setting value.

        Args:
            key: Setting key
            default: Default value if setting is not found

        Returns:
            Setting value
        """
        self._check_for_changes()

        value_obj = self.config.values.get(key)
        if value_obj is None:
            return default

        return value_obj.value

    def get_schema(self, key: str) -> Optional[SettingSchema]:
        """Get a setting schema.

        Args:
            key: Setting key

        Returns:
            Setting schema or None if not found
        """
        self._check_for_changes()

        return self.config.schemas.get(key)

    def set_value(self, key: str, value: Any, source: str = "user") -> None:
        """Set a setting value.

        Args:
            key: Setting key
            value: Setting value
            source: Source of the setting value

        Raises:
            ValueError: If setting schema is not found or validation fails
        """
        schema = self.config.schemas.get(key)
        if not schema:
            raise ValueError(f"Setting schema not found for key: {key}")

        # Check if immutable
        if schema.immutable:
            current_value = self.config.values.get(key)
            if current_value and current_value.source != "default":
                raise ValueError(f"Setting is immutable: {key}")

        # Validate value
        validation = self.validate_setting(key, value)
        if not validation.valid:
            raise ValueError(
                f"Invalid setting value for {key}: {', '.join(validation.errors)}"
            )

        # Update value
        current_value = self.config.values.get(key)
        if current_value:
            old_value = current_value.value
            current_value.value = validation.value
            current_value.last_updated = datetime.now()
            current_value.source = source

            # Update overridden flag if not default
            if source != "default":
                current_value.overridden = True

            # Notify listeners
            if old_value != validation.value:
                for listener in self._change_listeners:
                    try:
                        listener({key: {"new": validation.value, "old": old_value}})
                    except Exception as e:
                        logger.error("Error notifying settings listener: %s", str(e))
        else:
            self.config.values[key] = SettingValue(
                key=key,
                value=validation.value,
                schema_key=key,
                source=source,
                overridden=source != "default",
            )

            # Notify listeners
            for listener in self._change_listeners:
                try:
                    listener({key: {"new": validation.value, "old": None}})
                except Exception as e:
                    logger.error("Error notifying settings listener: %s", str(e))

        self._save()

    def reset_value(self, key: str) -> None:
        """Reset a setting to its default value.

        Args:
            key: Setting key

        Raises:
            ValueError: If setting schema is not found
        """
        schema = self.config.schemas.get(key)
        if not schema:
            raise ValueError(f"Setting schema not found for key: {key}")

        # Check if immutable
        if schema.immutable:
            current_value = self.config.values.get(key)
            if current_value and current_value.source != "default":
                raise ValueError(f"Setting is immutable: {key}")

        current_value = self.config.values.get(key)
        if current_value:
            old_value = current_value.value
            current_value.value = schema.default
            current_value.last_updated = datetime.now()
            current_value.source = "default"
            current_value.overridden = False

            # Notify listeners if value actually changed
            if old_value != schema.default:
                for listener in self._change_listeners:
                    try:
                        listener({key: {"new": schema.default, "old": old_value}})
                    except Exception as e:
                        logger.error("Error notifying settings listener: %s", str(e))
        else:
            self.config.values[key] = SettingValue(
                key=key,
                value=schema.default,
                schema_key=key,
                source="default",
                overridden=False,
            )

            # Notify listeners
            for listener in self._change_listeners:
                try:
                    listener({key: {"new": schema.default, "old": None}})
                except Exception as e:
                    logger.error("Error notifying settings listener: %s", str(e))

        self._save()

    def add_change_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Add a listener for setting changes.

        Args:
            listener: Function to call when settings change
        """
        if listener not in self._change_listeners:
            self._change_listeners.append(listener)

    def remove_change_listener(
        self, listener: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Remove a listener for setting changes.

        Args:
            listener: Function to remove from listeners
        """
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def get_settings_by_group(self, group: str) -> Dict[str, Dict[str, Any]]:
        """Get settings by group.

        Args:
            group: Setting group

        Returns:
            Dictionary of settings in the group
        """
        self._check_for_changes()

        result = {}
        for key, schema in self.config.schemas.items():
            if schema.group == group:
                value_obj = self.config.values.get(key)
                value = value_obj.value if value_obj else schema.default

                # Mask sensitive values
                if schema.sensitivity in (
                    SettingSensitivity.SENSITIVE,
                    SettingSensitivity.SECRET,
                ):
                    if value and isinstance(value, str):
                        value = "*" * min(len(value), 8)

                result[key] = {
                    "value": value,
                    "type": schema.type,
                    "description": schema.description,
                    "default": (
                        schema.default
                        if schema.sensitivity == SettingSensitivity.NORMAL
                        else None
                    ),
                    "required": schema.required,
                    "visibility": schema.visibility,
                    "options": schema.options,
                    "immutable": schema.immutable,
                    "restart_required": schema.restart_required,
                }

        return result

    def get_all_groups(self) -> Set[str]:
        """Get all setting groups.

        Returns:
            Set of group names
        """
        self._check_for_changes()

        return {schema.group for schema in self.config.schemas.values()}


# Singleton instance for application-wide settings
_instance: Optional[DynamicSettingsService] = None


def init_dynamic_settings(
    config_path: Union[str, Path], encryption_handler=None
) -> DynamicSettingsService:
    """Initialize the dynamic settings service.

    Args:
        config_path: Path to the settings configuration file
        encryption_handler: Optional encryption handler for sensitive settings

    Returns:
        Dynamic settings service instance
    """
    global _instance

    if _instance is None:
        _instance = DynamicSettingsService(config_path, encryption_handler)

    return _instance


def get_dynamic_settings() -> DynamicSettingsService:
    """Get the dynamic settings service instance.

    Returns:
        Dynamic settings service instance

    Raises:
        RuntimeError: If dynamic settings service is not initialized
    """
    if _instance is None:
        raise RuntimeError(
            "Dynamic settings service not initialized, call init_dynamic_settings first"
        )

    return _instance
