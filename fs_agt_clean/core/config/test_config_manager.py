"""Test script for the config_manager module."""

import os
import tempfile
import unittest
from pathlib import Path

from fs_agt_clean.core.config.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Tests for the ConfigManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)

        # Create test config files
        self.base_config_path = self.config_dir / "base.yaml"
        with open(self.base_config_path, "w") as f:
            f.write(
                """
database:
  host: localhost
  port: 5432
  username: user
  password: password

api:
  host: localhost
  port: 8000
  debug: false
"""
            )

        self.dev_config_path = self.config_dir / "development.yaml"
        with open(self.dev_config_path, "w") as f:
            f.write(
                """
api:
  debug: true
"""
            )

        self.prod_config_path = self.config_dir / "production.yaml"
        with open(self.prod_config_path, "w") as f:
            f.write(
                """
database:
  host: db.example.com
  password: prod_password

api:
  debug: false
"""
            )

        # Create schema file
        self.schema_path = self.config_dir / "schema.yaml"
        with open(self.schema_path, "w") as f:
            f.write(
                """
required:
  - database
  - api
deprecated:
  - old_setting
"""
            )

        # Save original environment
        self.original_env = os.environ.copy()

        # Reset the singleton instance to ensure a clean test
        ConfigManager._instance = None

        # Create config manager
        self.config_manager = ConfigManager(
            config_dir=self.config_dir, environment="development"
        )

    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary directory
        self.temp_dir.cleanup()

        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Reset the singleton instance
        ConfigManager._instance = None
        # Also reset the global instance
        import sys

        module = sys.modules[ConfigManager.__module__]
        module._config_manager_instance = None

    def test_get(self):
        """Test get method."""
        # Test getting values
        self.assertEqual(self.config_manager.get("database.host"), "localhost")
        self.assertEqual(self.config_manager.get("database.port"), 5432)
        self.assertEqual(
            self.config_manager.get("api.debug"), True
        )  # Overridden by development.yaml

        # Test getting non-existent values
        self.assertIsNone(self.config_manager.get("non_existent"))
        self.assertEqual(self.config_manager.get("non_existent", "default"), "default")

    def test_set(self):
        """Test set method."""
        # Test setting values
        self.config_manager.set("database.host", "new_host")
        self.assertEqual(self.config_manager.get("database.host"), "new_host")

        # Test setting nested values
        self.config_manager.set("database.credentials.api_key", "secret")
        self.assertEqual(
            self.config_manager.get("database.credentials.api_key"), "secret"
        )

    def test_get_section(self):
        """Test get_section method."""
        # Test getting a section
        database_section = self.config_manager.get_section("database")
        self.assertIsInstance(database_section, dict)
        self.assertEqual(database_section["host"], "localhost")
        self.assertEqual(database_section["port"], 5432)

        # Test getting a non-existent section
        non_existent_section = self.config_manager.get_section("non_existent")
        self.assertEqual(non_existent_section, {})

    def test_environment(self):
        """Test environment-specific configuration."""
        # Test development environment
        self.assertEqual(self.config_manager.get_environment(), "development")
        self.assertTrue(self.config_manager.get("api.debug"))

        # Test production environment
        self.config_manager.set_environment("production")
        self.assertEqual(self.config_manager.get_environment(), "production")
        self.assertEqual(self.config_manager.get("database.host"), "db.example.com")
        self.assertEqual(self.config_manager.get("database.password"), "prod_password")
        self.assertFalse(self.config_manager.get("api.debug"))

    def test_reload(self):
        """Test reload method."""
        # Modify a config file
        with open(self.base_config_path, "w") as f:
            f.write(
                """
database:
  host: modified_host
  port: 5432
  username: user
  password: password

api:
  host: localhost
  port: 8000
  debug: false
"""
            )

        # Explicitly load the base config file to add it to config_paths
        self.config_manager.load(self.base_config_path)

        # Reload configuration
        self.config_manager.reload()

        # Check that the configuration was reloaded
        self.assertEqual(self.config_manager.get("database.host"), "modified_host")

    def test_register_change_listener(self):
        """Test register_change_listener method."""
        # Create a change listener
        changes = []

        def change_listener(key, value):
            changes.append((key, value))

        # Register the change listener
        self.config_manager.register_change_listener(change_listener)

        # Make a change
        self.config_manager.set("database.host", "new_host")

        # Check that the listener was called
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], ("database.host", "new_host"))

    def test_validate(self):
        """Test validate method."""
        # Create a schema
        schema = {"required": ["database", "api"], "deprecated": ["old_setting"]}

        # Test validation with valid configuration
        result = self.config_manager.validate(schema)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

        # Test validation with invalid configuration
        self.config_manager.set("old_setting", "value")
        result = self.config_manager.validate(schema)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.warnings[0], "Field 'old_setting' is deprecated")

        # Test validation with missing required field
        self.config_manager.config_data = {}  # Clear configuration
        result = self.config_manager.validate(schema)
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
        self.assertIn("Required field 'database' is missing", result.errors)
        self.assertIn("Required field 'api' is missing", result.errors)


if __name__ == "__main__":
    unittest.main()
