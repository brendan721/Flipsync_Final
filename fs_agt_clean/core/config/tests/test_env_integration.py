"""Tests for the integration of environment variables in ConfigManager."""

import os
import tempfile
import unittest
from pathlib import Path

import yaml
from fs_agt.core.config.config_manager import ConfigManager


class TestEnvironmentVariableIntegration(unittest.TestCase):
    """Tests for the integration of environment variables in ConfigManager."""

    def setUp(self):
        """Set up test environment."""
        # Save original environment
        self.original_env = os.environ.copy()

        # Create a temporary directory for test configurations
        self.temp_dir = tempfile.mkdtemp()

        # Set up test environment variables
        os.environ["TEST_DB_HOST"] = "testdb.example.com"
        os.environ["TEST_DB_PORT"] = "5432"
        os.environ["TEST_DB_USER"] = "test_user"
        os.environ["TEST_DB_PASSWORD"] = "test_password"
        os.environ["TEST_DEBUG"] = "true"
        os.environ["APP_API__URL"] = "https://api.example.com"
        os.environ["APP_API__TIMEOUT"] = "30"
        os.environ["APP_API__RETRY_COUNT"] = "3"
        os.environ["APP_LOGGING__LEVEL"] = "DEBUG"

        # Create test configuration file
        self.config_file = os.path.join(self.temp_dir, "config.yaml")
        config = {
            "database": {
                "host": "${TEST_DB_HOST}",
                "port": "${TEST_DB_PORT}",
                "username": "${TEST_DB_USER}",
                "password": "${TEST_DB_PASSWORD}",
                "pool_size": 10,
            },
            "debug": "${TEST_DEBUG}",
            "api": {"url": "default-url", "timeout": 10, "retry_count": 1},
            "logging": {"level": "INFO", "file": "app.log"},
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

        # Reset the singleton between tests
        ConfigManager._instance = None

    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary directory
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_environment_variable_interpolation(self):
        """Test environment variable interpolation in configuration files."""
        # Initialize ConfigManager with test directory
        config_manager = ConfigManager(config_dir=self.temp_dir)

        # Load test configuration
        config_manager.load(self.config_file)

        # Check that environment variables were interpolated
        self.assertEqual(config_manager.get("database.host"), "testdb.example.com")
        self.assertEqual(config_manager.get("database.port"), "5432")
        self.assertEqual(config_manager.get("database.username"), "test_user")
        self.assertEqual(config_manager.get("database.password"), "test_password")
        self.assertEqual(config_manager.get("debug"), "true")

    def test_environment_variable_update(self):
        """Test updating configuration from environment variables."""
        # Initialize ConfigManager with test directory
        config_manager = ConfigManager(config_dir=self.temp_dir)

        # Load test configuration
        config_manager.load(self.config_file)

        # Update from environment variables
        config_manager.update_from_env_vars(prefix="APP_")

        # Check that configuration was updated from environment variables
        self.assertEqual(config_manager.get("api.url"), "https://api.example.com")
        self.assertEqual(
            config_manager.get("api.timeout"), 30
        )  # Note: converted to integer
        self.assertEqual(
            config_manager.get("api.retry_count"), 3
        )  # Note: converted to integer
        self.assertEqual(config_manager.get("logging.level"), "DEBUG")

    def test_initialization_with_env_vars(self):
        """Test initialization with environment variable support."""
        # Initialize ConfigManager with environment variable support
        config_manager = ConfigManager(config_dir=self.temp_dir, env_var_prefix="APP_")

        # Load test configuration
        config_manager.load(self.config_file)

        # Check that both interpolation and update from environment variables worked
        self.assertEqual(config_manager.get("database.host"), "testdb.example.com")
        self.assertEqual(config_manager.get("api.url"), "https://api.example.com")

    def test_reload_with_env_vars(self):
        """Test reloading with environment variables."""
        # Initialize ConfigManager with environment variable support
        config_manager = ConfigManager(config_dir=self.temp_dir, env_var_prefix="APP_")

        # Load test configuration
        config_manager.load(self.config_file)

        # Modify environment variables
        os.environ["TEST_DB_HOST"] = "modified.example.com"
        os.environ["APP_API__URL"] = "https://modified.example.com"

        # Reload configuration
        config_manager.reload()

        # Check that configuration was reloaded with updated environment variables
        self.assertEqual(config_manager.get("database.host"), "modified.example.com")
        self.assertEqual(config_manager.get("api.url"), "https://modified.example.com")

    def test_change_notification_for_env_vars(self):
        """Test change notification when updating from environment variables."""
        # Initialize ConfigManager
        config_manager = ConfigManager(config_dir=self.temp_dir)

        # Load test configuration
        config_manager.load(self.config_file)

        # Set up change listener
        changes = []

        def listener(key, value):
            changes.append((key, value))

        config_manager.register_change_listener(listener)

        # Update from environment variables
        config_manager.update_from_env_vars(prefix="APP_")

        # Check that change notifications were sent
        self.assertGreater(len(changes), 0)

        # Check specific changes
        api_url_changed = any(
            key == "api.url" and value == "https://api.example.com"
            for key, value in changes
        )
        self.assertTrue(api_url_changed, "Change notification for api.url not found")


if __name__ == "__main__":
    unittest.main()
