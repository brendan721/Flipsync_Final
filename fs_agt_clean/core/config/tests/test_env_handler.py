"""Tests for the environment variable handler module."""

import os
import unittest
from unittest.mock import patch

from fs_agt.core.config.env_handler import (
    _convert_value_type,
    _set_nested_value,
    interpolate_env_vars,
    interpolate_env_vars_in_config,
    update_from_env_vars,
)


class TestEnvHandler(unittest.TestCase):
    """Tests for the environment variable handler."""

    def setUp(self):
        """Set up test environment."""
        # Save original environment
        self.original_env = os.environ.copy()

        # Set up test environment variables
        os.environ["TEST_VAR"] = "test_value"
        os.environ["TEST_INT"] = "42"
        os.environ["TEST_FLOAT"] = "3.14"
        os.environ["TEST_BOOL"] = "true"
        os.environ["TEST_LIST"] = "item1,item2,item3"
        os.environ["APP_DATABASE__HOST"] = "localhost"
        os.environ["APP_DATABASE__PORT"] = "5432"
        os.environ["APP_DATABASE__CREDENTIALS__USERNAME"] = "user"
        os.environ["APP_DATABASE__CREDENTIALS__PASSWORD"] = "password"
        os.environ["APP_DEBUG"] = "true"

    def tearDown(self):
        """Clean up test environment."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_interpolate_env_vars_dollar_brace(self):
        """Test interpolation of environment variables with ${VAR} format."""
        # Test string with ${VAR} format
        result = interpolate_env_vars("The value is ${TEST_VAR}")
        self.assertEqual(result, "The value is test_value")

        # Test string with multiple variables
        result = interpolate_env_vars("${TEST_VAR} and ${TEST_INT}")
        self.assertEqual(result, "test_value and 42")

        # Test string with non-existent variable
        result = interpolate_env_vars("${TEST_VAR} and ${NON_EXISTENT}")
        self.assertEqual(result, "test_value and ${NON_EXISTENT}")

    def test_interpolate_env_vars_dollar_name(self):
        """Test interpolation of environment variables with $VAR format."""
        # Test string with $VAR format
        result = interpolate_env_vars("The value is $TEST_VAR")
        self.assertEqual(result, "The value is test_value")

        # Test string with multiple variables
        result = interpolate_env_vars("$TEST_VAR and $TEST_INT")
        self.assertEqual(result, "test_value and 42")

        # Test string with non-existent variable
        result = interpolate_env_vars("$TEST_VAR and $NON_EXISTENT")
        self.assertEqual(result, "test_value and $NON_EXISTENT")

    def test_interpolate_env_vars_non_string(self):
        """Test interpolation of non-string values."""
        # Test non-string values (should be returned as-is)
        self.assertEqual(interpolate_env_vars(42), 42)
        self.assertEqual(interpolate_env_vars(True), True)
        self.assertEqual(interpolate_env_vars(None), None)
        self.assertEqual(interpolate_env_vars([1, 2, 3]), [1, 2, 3])
        self.assertEqual(interpolate_env_vars({"key": "value"}), {"key": "value"})

    def test_interpolate_env_vars_in_config(self):
        """Test interpolation of environment variables in a configuration."""
        # Test configuration with environment variables
        config = {
            "database": {
                "host": "${TEST_VAR}",
                "port": "$TEST_INT",
                "credentials": {"username": "user", "password": "${TEST_VAR}_password"},
            },
            "debug": True,
            "values": ["${TEST_VAR}", "$TEST_INT", "fixed"],
        }

        expected = {
            "database": {
                "host": "test_value",
                "port": "42",
                "credentials": {"username": "user", "password": "test_value_password"},
            },
            "debug": True,
            "values": ["test_value", "42", "fixed"],
        }

        result = interpolate_env_vars_in_config(config)
        self.assertEqual(result, expected)

    def test_convert_value_type(self):
        """Test conversion of string values to appropriate types."""
        # Test boolean values
        self.assertTrue(_convert_value_type("true"))
        self.assertTrue(_convert_value_type("True"))
        self.assertTrue(_convert_value_type("yes"))
        self.assertTrue(_convert_value_type("on"))
        self.assertTrue(_convert_value_type("1"))

        self.assertFalse(_convert_value_type("false"))
        self.assertFalse(_convert_value_type("False"))
        self.assertFalse(_convert_value_type("no"))
        self.assertFalse(_convert_value_type("off"))
        self.assertFalse(_convert_value_type("0"))

        # Test integer values
        self.assertEqual(_convert_value_type("42"), 42)
        self.assertEqual(_convert_value_type("-42"), -42)

        # Test float values
        self.assertEqual(_convert_value_type("3.14"), 3.14)
        self.assertEqual(_convert_value_type("-3.14"), -3.14)

        # Test list values
        self.assertEqual(
            _convert_value_type("item1,item2,item3"), ["item1", "item2", "item3"]
        )
        self.assertEqual(_convert_value_type("1,2,3"), [1, 2, 3])
        self.assertEqual(_convert_value_type("true,false"), [True, False])

        # Test string values
        self.assertEqual(_convert_value_type("hello"), "hello")
        self.assertEqual(_convert_value_type("hello-world"), "hello-world")

    def test_set_nested_value(self):
        """Test setting values in a nested dictionary."""
        # Test simple key
        config = {}
        _set_nested_value(config, ["key"], "value")
        self.assertEqual(config, {"key": "value"})

        # Test nested keys
        config = {}
        _set_nested_value(config, ["parent", "child"], "value")
        self.assertEqual(config, {"parent": {"child": "value"}})

        # Test deeply nested keys
        config = {}
        _set_nested_value(config, ["level1", "level2", "level3"], "value")
        self.assertEqual(config, {"level1": {"level2": {"level3": "value"}}})

        # Test with existing keys
        config = {"existing": "value", "parent": {"existing": "value"}}
        _set_nested_value(config, ["parent", "child"], "value")
        self.assertEqual(
            config,
            {"existing": "value", "parent": {"existing": "value", "child": "value"}},
        )

        # Test with key collision (non-dict value at path)
        config = {"parent": "value"}
        _set_nested_value(config, ["parent", "child"], "value")
        self.assertEqual(config, {"parent": {"child": "value"}})

    def test_update_from_env_vars(self):
        """Test updating configuration from environment variables."""
        # Starting configuration
        config = {
            "database": {
                "host": "default-host",
                "port": 0,
                "credentials": {"username": "", "password": ""},
            },
            "debug": False,
            "unchanged": "value",
        }

        # Expected result after update
        expected = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {"username": "user", "password": "password"},
            },
            "debug": True,
            "unchanged": "value",
        }

        # Update from environment variables
        result = update_from_env_vars(config)
        self.assertEqual(result, expected)

    def test_update_from_env_vars_custom_prefix(self):
        """Test updating configuration with custom prefix."""
        # Set up a custom environment variable
        os.environ["CUSTOM_KEY"] = "custom_value"

        # Starting configuration
        config = {"key": "default"}

        # Update with custom prefix
        result = update_from_env_vars(config, prefix="CUSTOM_")
        self.assertEqual(result, {"key": "custom_value"})

    def test_update_from_env_vars_custom_separator(self):
        """Test updating configuration with custom separator."""
        # Set up a custom environment variable
        os.environ["APP_DATABASE.HOST"] = "custom_host"

        # Starting configuration
        config = {"database": {"host": "default"}}

        # Update with custom separator
        result = update_from_env_vars(config, separator=".")
        self.assertEqual(result, {"database": {"host": "custom_host"}})


if __name__ == "__main__":
    unittest.main()
