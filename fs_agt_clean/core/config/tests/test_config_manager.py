"""Test suite for the Configuration Manager.

This module contains unit tests for the ConfigManager class, testing
all the main functionality including environment-specific configuration,
validation, and change listeners.
"""

import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from fs_agt.core.config.config_manager import ConfigManager
from fs_agt.core.config.config_protocol import ConfigValidationResult


class TestConfigManager(unittest.TestCase):
    """Test case for the ConfigManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test configs
        self.temp_dir = tempfile.mkdtemp()

        # Create test configuration files
        self.base_config = {
            "app": {"name": "Test App", "version": "1.0.0", "debug": False},
            "database": {"type": "sqlite", "path": "./data/test.db"},
        }

        self.dev_config = {"app": {"debug": True}, "database": {"path": ":memory:"}}

        self.schema = {
            "app": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "required": True},
                    "version": {
                        "type": "string",
                        "required": True,
                        "pattern": "^\\d+\\.\\d+\\.\\d+$",
                    },
                    "debug": {"type": "boolean", "required": True},
                },
            },
            "database": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "required": True,
                        "constraints": {"enum": ["sqlite", "postgresql", "mysql"]},
                    },
                    "path": {"type": "string", "required": False},
                },
            },
        }

        # Write test files
        with open(Path(self.temp_dir) / "base.yaml", "w") as f:
            yaml.dump(self.base_config, f)

        with open(Path(self.temp_dir) / "development.yaml", "w") as f:
            yaml.dump(self.dev_config, f)

        with open(Path(self.temp_dir) / "schema.yaml", "w") as f:
            yaml.dump(self.schema, f)

        # Create a JSON config file for testing JSON support
        with open(Path(self.temp_dir) / "config.json", "w") as f:
            json.dump({"json_test": {"value": "JSON works"}}, f)

        # Reset singleton state between tests
        ConfigManager._instance = None

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_singleton_pattern(self):
        """Test that ConfigManager follows singleton pattern."""
        config1 = ConfigManager(config_dir=self.temp_dir)
        config2 = ConfigManager()

        self.assertIs(config1, config2, "ConfigManager should be a singleton")

    def test_load_config(self):
        """Test loading configuration from file."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Check if base config was loaded
        self.assertEqual(config.get("app.name"), "Test App")
        self.assertEqual(config.get("database.type"), "sqlite")

    def test_environment_specific_config(self):
        """Test environment-specific configuration loading."""
        # Create with development environment
        config = ConfigManager(config_dir=self.temp_dir, environment="development")

        # Check if development overrides were applied
        self.assertTrue(config.get("app.debug"), "Debug should be True in development")
        self.assertEqual(
            config.get("database.path"),
            ":memory:",
            "Database path should be overridden",
        )

        # Base values should still be preserved
        self.assertEqual(
            config.get("app.name"), "Test App", "App name should be preserved"
        )
        self.assertEqual(
            config.get("app.version"), "1.0.0", "App version should be preserved"
        )

    def test_get_section(self):
        """Test getting an entire configuration section."""
        config = ConfigManager(config_dir=self.temp_dir)

        db_section = config.get_section("database")
        self.assertIsInstance(db_section, dict)
        self.assertEqual(db_section["type"], "sqlite")
        self.assertTrue("path" in db_section)

    def test_set_value(self):
        """Test setting a configuration value."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Set a new value
        config.set("app.new_setting", "new value")
        self.assertEqual(config.get("app.new_setting"), "new value")

        # Update an existing value
        config.set("app.name", "Updated App Name")
        self.assertEqual(config.get("app.name"), "Updated App Name")

        # Set a nested value that doesn't exist yet
        config.set("services.api.port", 8080)
        self.assertEqual(config.get("services.api.port"), 8080)

    def test_change_listener(self):
        """Test configuration change listeners."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Keep track of changes in this dictionary
        changes = {}

        def listener(key, value):
            changes[key] = value

        config.register_change_listener(listener)

        # Make a change
        config.set("app.name", "New Name")

        # Check if listener was called
        self.assertIn("app.name", changes)
        self.assertEqual(changes["app.name"], "New Name")

    def test_validation(self):
        """Test configuration validation."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Valid configuration
        result = config.validate()
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

        # Introduce an error by changing a value to invalid type
        config.set("app.debug", "not a boolean")

        result = config.validate()
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)

        # Fix the error
        config.set("app.debug", False)

        result = config.validate()
        self.assertTrue(result.is_valid)

    def test_environment_change(self):
        """Test changing environments."""
        config = ConfigManager(config_dir=self.temp_dir, environment="development")

        # Check initial values in development
        self.assertTrue(config.get("app.debug"))
        self.assertEqual(config.get("database.path"), ":memory:")

        # Change to production (which will fall back to base config)
        config.set_environment("production")

        # Check values after environment change
        self.assertFalse(config.get("app.debug"))
        self.assertEqual(config.get("database.path"), "./data/test.db")

    def test_reload(self):
        """Test configuration reloading."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Original value
        self.assertEqual(config.get("app.name"), "Test App")

        # Modify the file directly
        modified_config = self.base_config.copy()
        modified_config["app"]["name"] = "Modified App"

        with open(Path(self.temp_dir) / "base.yaml", "w") as f:
            yaml.dump(modified_config, f)

        # Reload configuration
        config.reload()

        # Check if the new value was loaded
        self.assertEqual(config.get("app.name"), "Modified App")

    def test_constraints_validation(self):
        """Test validation against constraints."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Valid database type
        config.set("database.type", "postgresql")
        result = config.validate()
        self.assertTrue(result.is_valid)

        # Invalid database type
        config.set("database.type", "invalid_db")
        result = config.validate()
        self.assertFalse(result.is_valid)

        # Find the relevant error
        db_type_error = False
        for error in result.errors:
            if "database.type" in error and "enum" in error:
                db_type_error = True

        self.assertTrue(
            db_type_error, "Should have constraint violation for database.type"
        )

    def test_custom_schema_validation(self):
        """Test validation with a custom schema."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Create custom schema
        custom_schema = {
            "advanced": {
                "type": "object",
                "properties": {
                    "setting": {
                        "type": "integer",
                        "constraints": {"min": 1, "max": 100},
                    }
                },
            }
        }

        # Add a valid setting
        config.set("advanced.setting", 50)

        # Validate with custom schema
        result = config.validate(custom_schema)
        self.assertTrue(result.is_valid)

        # Add an invalid setting
        config.set("advanced.setting", 200)  # Over max

        # Validate again
        result = config.validate(custom_schema)
        self.assertFalse(result.is_valid)

    def test_json_config_loading(self):
        """Test loading JSON configuration files."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Load JSON config
        config.load("config.json")

        # Check if JSON config was loaded
        self.assertEqual(config.get("json_test.value"), "JSON works")

    def test_file_not_found(self):
        """Test handling of non-existent configuration files."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Try to load a non-existent file
        with self.assertRaises(FileNotFoundError):
            config.load("non_existent.yaml")

    def test_invalid_config_format(self):
        """Test handling of invalid configuration file formats."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Create an invalid YAML file
        with open(Path(self.temp_dir) / "invalid.yaml", "w") as f:
            f.write("This is not valid YAML: :")

        # Try to load the invalid file
        with self.assertRaises(ValueError):
            config.load("invalid.yaml")

    def test_empty_config(self):
        """Test handling of empty configuration files."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Create an empty file
        with open(Path(self.temp_dir) / "empty.yaml", "w") as f:
            f.write("")

        # Load the empty file (should not raise an exception)
        config.load("empty.yaml")

        # Configuration should remain unchanged
        self.assertEqual(config.get("app.name"), "Test App")

    def test_deep_merge(self):
        """Test deep merging of configuration dictionaries."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Create a config with nested dictionaries
        nested_config = {
            "services": {
                "api": {
                    "host": "localhost",
                    "port": 8000,
                    "settings": {"timeout": 30, "retries": 3},
                }
            }
        }

        # Write to file
        with open(Path(self.temp_dir) / "nested.yaml", "w") as f:
            yaml.dump(nested_config, f)

        # Load the nested config
        config.load("nested.yaml")

        # Create an override that changes some values but not others
        override_config = {
            "services": {"api": {"port": 9000, "settings": {"timeout": 60}}}
        }

        # Write to file
        with open(Path(self.temp_dir) / "override.yaml", "w") as f:
            yaml.dump(override_config, f)

        # Load the override
        config.load("override.yaml")

        # Check that values were properly merged
        self.assertEqual(config.get("services.api.host"), "localhost")  # Unchanged
        self.assertEqual(config.get("services.api.port"), 9000)  # Changed
        self.assertEqual(config.get("services.api.settings.timeout"), 60)  # Changed
        self.assertEqual(config.get("services.api.settings.retries"), 3)  # Unchanged

    def test_get_with_default(self):
        """Test getting configuration values with defaults."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Get existing value (default should be ignored)
        self.assertEqual(config.get("app.name", "Default Name"), "Test App")

        # Get non-existent value (should return default)
        self.assertEqual(
            config.get("non.existent.key", "Default Value"), "Default Value"
        )

        # Get non-existent value without default (should return None)
        self.assertIsNone(config.get("non.existent.key"))

    def test_multiple_change_listeners(self):
        """Test registering multiple change listeners."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Keep track of changes in these dictionaries
        changes1 = {}
        changes2 = {}

        def listener1(key, value):
            changes1[key] = value

        def listener2(key, value):
            changes2[key] = value

        # Register both listeners
        config.register_change_listener(listener1)
        config.register_change_listener(listener2)

        # Make a change
        config.set("app.name", "New Name")

        # Check if both listeners were called
        self.assertEqual(changes1["app.name"], "New Name")
        self.assertEqual(changes2["app.name"], "New Name")

    def test_listener_exception_handling(self):
        """Test that exceptions in change listeners are handled gracefully."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Create a listener that raises an exception
        def bad_listener(key, value):
            raise ValueError("Test exception")

        # Create a normal listener
        changes = {}

        def good_listener(key, value):
            changes[key] = value

        # Register both listeners
        config.register_change_listener(bad_listener)
        config.register_change_listener(good_listener)

        # Make a change (should not raise an exception)
        config.set("app.name", "New Name")

        # The good listener should still have been called
        self.assertEqual(changes["app.name"], "New Name")

    def test_all_constraint_types(self):
        """Test all constraint types in validation."""
        config = ConfigManager(config_dir=self.temp_dir)

        # Create a schema with all constraint types
        all_constraints_schema = {
            "test": {
                "type": "object",
                "properties": {
                    "min_value": {"type": "integer", "constraints": {"min": 10}},
                    "max_value": {"type": "integer", "constraints": {"max": 100}},
                    "pattern_value": {
                        "type": "string",
                        "constraints": {"pattern": "^[A-Z][a-z]+$"},
                    },
                    "enum_value": {
                        "type": "string",
                        "constraints": {"enum": ["one", "two", "three"]},
                    },
                    "length_value": {"type": "string", "constraints": {"length": 5}},
                    "min_length_value": {
                        "type": "string",
                        "constraints": {"min_length": 3},
                    },
                    "max_length_value": {
                        "type": "string",
                        "constraints": {"max_length": 10},
                    },
                },
            }
        }

        # Set valid values
        config.set("test.min_value", 15)
        config.set("test.max_value", 50)
        config.set("test.pattern_value", "Hello")
        config.set("test.enum_value", "two")
        config.set("test.length_value", "12345")
        config.set("test.min_length_value", "abcd")
        config.set("test.max_length_value", "abcdef")

        # Validate with all constraints (should pass)
        result = config.validate(all_constraints_schema)
        self.assertTrue(result.is_valid)

        # Set invalid values
        config.set("test.min_value", 5)  # Below min
        config.set("test.max_value", 200)  # Above max
        config.set("test.pattern_value", "invalid")  # Doesn't match pattern
        config.set("test.enum_value", "four")  # Not in enum
        config.set("test.length_value", "1234")  # Wrong length
        config.set("test.min_length_value", "ab")  # Too short
        config.set("test.max_length_value", "abcdefghijk")  # Too long

        # Validate again (should fail)
        result = config.validate(all_constraints_schema)
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 7)  # One error for each constraint

    @patch("fs_agt.core.config.config_manager.WATCHDOG_AVAILABLE", True)
    @patch("fs_agt.core.config.config_manager.Observer")
    def test_auto_reload(self, mock_observer):
        """Test auto-reload functionality."""
        # Mock the observer and handler
        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance

        # Create config manager with auto_reload enabled
        config = ConfigManager(config_dir=self.temp_dir, auto_reload=True)

        # Load a config file
        config.load("base.yaml")

        # Check that observer was started
        mock_observer_instance.start.assert_called_once()

        # Check that observer was scheduled
        self.assertEqual(mock_observer_instance.schedule.call_count, 1)

    def test_validation_with_no_schema(self):
        """Test validation when no schema is available."""
        # Create a new config manager without loading schema
        ConfigManager._instance = None
        config = ConfigManager(config_dir=self.temp_dir)

        # Remove schema from config data
        config._schema = {}

        # Validate (should pass but with a warning)
        result = config.validate()
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("No schema available", result.warnings[0])


if __name__ == "__main__":
    unittest.main()
