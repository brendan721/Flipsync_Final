"""
Tests for the env_handler module.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fs_agt_clean.core.config.env_handler import (
    _convert_value_type,
    _set_nested_value,
    get_env_var,
    interpolate_env_vars,
    interpolate_env_vars_in_config,
    load_env_file,
    update_from_env_vars,
    validate_env_vars,
)


class TestEnvHandler(unittest.TestCase):
    """Tests for the env_handler module."""

    def setUp(self):
        """Set up test environment."""
        # Save original environment
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_interpolate_env_vars(self):
        """Test interpolate_env_vars function."""
        # Set environment variables
        os.environ["TEST_VAR"] = "test_value"
        os.environ["ANOTHER_VAR"] = "another_value"

        # Test with ${VAR} format
        self.assertEqual(
            interpolate_env_vars("Value: ${TEST_VAR}"), "Value: test_value"
        )

        # Test with $VAR format
        self.assertEqual(interpolate_env_vars("Value: $TEST_VAR"), "Value: test_value")

        # Test with multiple variables
        self.assertEqual(
            interpolate_env_vars("${TEST_VAR} and $ANOTHER_VAR"),
            "test_value and another_value",
        )

        # Test with non-existent variable
        self.assertEqual(
            interpolate_env_vars("Value: ${NON_EXISTENT}"), "Value: ${NON_EXISTENT}"
        )

        # Test with non-string value
        self.assertEqual(interpolate_env_vars(123), 123)
        self.assertEqual(interpolate_env_vars(None), None)
        self.assertEqual(interpolate_env_vars(True), True)

    def test_interpolate_env_vars_in_config(self):
        """Test interpolate_env_vars_in_config function."""
        # Set environment variables
        os.environ["TEST_VAR"] = "test_value"
        os.environ["ANOTHER_VAR"] = "another_value"

        # Test with nested dictionary
        config = {
            "key1": "${TEST_VAR}",
            "key2": {"nested_key": "$ANOTHER_VAR"},
            "key3": ["${TEST_VAR}", "$ANOTHER_VAR"],
            "key4": 123,
        }

        expected = {
            "key1": "test_value",
            "key2": {"nested_key": "another_value"},
            "key3": ["test_value", "another_value"],
            "key4": 123,
        }

        self.assertEqual(interpolate_env_vars_in_config(config), expected)

        # Test with empty config
        self.assertEqual(interpolate_env_vars_in_config({}), {})
        self.assertEqual(interpolate_env_vars_in_config(None), None)

    def test_update_from_env_vars(self):
        """Test update_from_env_vars function."""
        # Set environment variables
        os.environ["APP_KEY1"] = "value1"
        os.environ["APP_KEY2__NESTED"] = "nested_value"
        os.environ["APP_KEY3"] = "true"
        os.environ["APP_KEY4"] = "123"
        os.environ["APP_KEY5"] = "123.45"
        os.environ["APP_KEY6"] = "item1,item2,item3"
        os.environ["IGNORED"] = "ignored"

        # Test with empty config
        config = {}
        result = update_from_env_vars(config)

        self.assertEqual(result["key1"], "value1")
        self.assertEqual(result["key2"]["nested"], "nested_value")
        self.assertEqual(result["key3"], True)
        self.assertEqual(result["key4"], 123)
        self.assertEqual(result["key5"], 123.45)
        self.assertEqual(result["key6"], ["item1", "item2", "item3"])
        self.assertNotIn("ignored", result)

        # Test with existing config
        config = {"key1": "original", "key7": "unchanged"}
        result = update_from_env_vars(config)

        self.assertEqual(result["key1"], "value1")  # Overwritten
        self.assertEqual(result["key7"], "unchanged")  # Unchanged

        # Test with different prefix
        os.environ["CUSTOM_KEY"] = "custom_value"
        result = update_from_env_vars({}, prefix="CUSTOM_")
        self.assertEqual(result["key"], "custom_value")

        # Test with different separator
        os.environ["APP_KEY2-NESTED"] = "nested_value2"
        result = update_from_env_vars({}, separator="-")
        self.assertEqual(result["key2"]["nested"], "nested_value2")

    def test_convert_value_type(self):
        """Test _convert_value_type function."""
        # Test boolean values
        self.assertEqual(_convert_value_type("true"), True)
        self.assertEqual(_convert_value_type("True"), True)
        self.assertEqual(_convert_value_type("yes"), True)
        self.assertEqual(_convert_value_type("on"), True)
        self.assertEqual(_convert_value_type("1"), True)

        self.assertEqual(_convert_value_type("false"), False)
        self.assertEqual(_convert_value_type("False"), False)
        self.assertEqual(_convert_value_type("no"), False)
        self.assertEqual(_convert_value_type("off"), False)
        self.assertEqual(_convert_value_type("0"), False)

        # Test integer values
        self.assertEqual(_convert_value_type("123"), 123)
        self.assertEqual(_convert_value_type("-456"), -456)

        # Test float values
        self.assertEqual(_convert_value_type("123.45"), 123.45)
        self.assertEqual(_convert_value_type("-456.78"), -456.78)

        # Test list values
        self.assertEqual(
            _convert_value_type("item1,item2,item3"), ["item1", "item2", "item3"]
        )
        self.assertEqual(_convert_value_type("true,123,456.78"), [True, 123, 456.78])

        # Test string values
        self.assertEqual(_convert_value_type("hello"), "hello")
        self.assertEqual(_convert_value_type(""), "")

    def test_set_nested_value(self):
        """Test _set_nested_value function."""
        # Test with simple key
        config = {}
        _set_nested_value(config, ["key"], "value")
        self.assertEqual(config["key"], "value")

        # Test with nested keys
        config = {}
        _set_nested_value(config, ["key1", "key2", "key3"], "value")
        self.assertEqual(config["key1"]["key2"]["key3"], "value")

        # Test with existing keys
        config = {"key1": {"key2": "original"}}
        _set_nested_value(config, ["key1", "key2"], "new_value")
        self.assertEqual(config["key1"]["key2"], "new_value")

        # Test with mixed case keys
        config = {}
        _set_nested_value(config, ["KEY1", "Key2", "key3"], "value")
        self.assertEqual(config["key1"]["key2"]["key3"], "value")

        # Test with non-dict value at path
        config = {"key1": "not_a_dict"}
        _set_nested_value(config, ["key1", "key2"], "value")
        self.assertEqual(config["key1"]["key2"], "value")

    @mock.patch("fs_agt_clean.core.config.env_handler.DOTENV_AVAILABLE", True)
    @mock.patch("fs_agt_clean.core.config.env_handler.load_dotenv")
    def test_load_env_file(self, mock_load_dotenv):
        """Test load_env_file function."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Test successful load
            mock_load_dotenv.return_value = True
            result = load_env_file(temp_path)
            self.assertTrue(result)
            mock_load_dotenv.assert_called_once_with(temp_path, override=False)

            # Test with override
            mock_load_dotenv.reset_mock()
            result = load_env_file(temp_path, override=True)
            self.assertTrue(result)
            mock_load_dotenv.assert_called_once_with(temp_path, override=True)

            # Test with non-existent file
            mock_load_dotenv.reset_mock()
            non_existent_path = Path("non_existent_file")
            result = load_env_file(non_existent_path)
            self.assertFalse(result)
            mock_load_dotenv.assert_not_called()

            # Test with exception
            mock_load_dotenv.reset_mock()
            mock_load_dotenv.side_effect = Exception("Test error")
            result = load_env_file(temp_path)
            self.assertFalse(result)
            mock_load_dotenv.assert_called_once()
        finally:
            # Clean up
            temp_path.unlink(missing_ok=True)

    @mock.patch("fs_agt_clean.core.config.env_handler.DOTENV_AVAILABLE", False)
    def test_load_env_file_no_dotenv(self):
        """Test load_env_file function when dotenv is not available."""
        result = load_env_file("dummy_path")
        self.assertFalse(result)

    def test_validate_env_vars(self):
        """Test validate_env_vars function."""
        # Set environment variables
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"
        os.environ["PREFIX_VAR3"] = "value3"

        # Test with all required vars present
        is_valid, missing = validate_env_vars(["VAR1", "VAR2"])
        self.assertTrue(is_valid)
        self.assertEqual(missing, [])

        # Test with missing vars
        is_valid, missing = validate_env_vars(["VAR1", "VAR2", "VAR3"])
        self.assertFalse(is_valid)
        self.assertEqual(missing, ["VAR3"])

        # Test with prefix
        is_valid, missing = validate_env_vars(["VAR3"], prefix="PREFIX_")
        self.assertTrue(is_valid)
        self.assertEqual(missing, [])

        # Test with optional vars
        is_valid, missing = validate_env_vars(
            ["VAR1"], optional_vars=["VAR2", "VAR3", "VAR4"]
        )
        self.assertTrue(is_valid)
        self.assertEqual(missing, [])

    def test_get_env_var(self):
        """Test get_env_var function."""
        # Set environment variables
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "123"
        os.environ["PREFIX_VAR3"] = "true"

        # Test with existing var
        self.assertEqual(get_env_var("VAR1"), "value1")

        # Test with non-existent var
        self.assertIsNone(get_env_var("NON_EXISTENT"))
        self.assertEqual(get_env_var("NON_EXISTENT", default="default"), "default")

        # Test with type conversion
        self.assertEqual(get_env_var("VAR2", var_type=int), 123)
        self.assertEqual(
            get_env_var("VAR1", var_type=int, default=0), 0
        )  # Invalid conversion

        # Test with prefix
        self.assertEqual(get_env_var("VAR3", prefix="PREFIX_"), True)

        # Test with automatic type conversion
        self.assertEqual(get_env_var("VAR2"), 123)
        self.assertEqual(get_env_var("VAR3", prefix="PREFIX_"), True)


if __name__ == "__main__":
    unittest.main()
