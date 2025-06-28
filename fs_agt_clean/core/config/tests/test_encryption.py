"""Tests for the configuration encryption functionality."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from fs_agt.core.config.config_manager import ConfigManager
from fs_agt.core.config.encryption_handler import (
    ConfigEncryptionHandler,
    find_sensitive_keys,
)


class TestEncryptionHandler(unittest.TestCase):
    """Test suite for ConfigEncryptionHandler class."""

    def setUp(self):
        """Set up test environment."""
        # Create encryption handler with a fixed key for testing
        self.test_key = b"0123456789abcdef0123456789abcdef"  # 32 bytes
        self.handler = ConfigEncryptionHandler(key=self.test_key)

        # Create a temporary directory for key files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.key_file_path = Path(self.temp_dir.name) / "test_key.key"

        # Set up a test configuration
        self.test_config = {
            "app": {"name": "TestApp", "debug": True},
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "db_user",
                "password": "secret_password",
            },
            "api": {
                "key": "api_secret_key",
                "timeout": 30,
                "endpoints": [
                    {"name": "users", "url": "/api/users", "auth_token": "token123"},
                    {"name": "products", "url": "/api/products"},
                ],
            },
        }

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_encrypt_decrypt_string(self):
        """Test encryption and decryption of string values."""
        original = "test_value"
        encrypted = self.handler.encrypt(original)

        # Check that the result is different and has the prefix
        self.assertNotEqual(original, encrypted)
        self.assertTrue(encrypted.startswith(self.handler.ENCRYPTED_PREFIX))

        # Check that we can decrypt it back to the original
        decrypted = self.handler.decrypt(encrypted)
        self.assertEqual(original, decrypted)

    def test_encrypt_decrypt_complex_value(self):
        """Test encryption and decryption of complex data structures."""
        original = {"key": "value", "nested": {"list": [1, 2, 3]}}
        encrypted = self.handler.encrypt(original)

        # Check that the result is different and has the prefix
        self.assertNotEqual(str(original), encrypted)
        self.assertTrue(encrypted.startswith(self.handler.ENCRYPTED_PREFIX))

        # Check that we can decrypt it back to the original
        decrypted = self.handler.decrypt(encrypted)
        self.assertEqual(original, decrypted)

    def test_is_encrypted(self):
        """Test the is_encrypted method."""
        # Test with encrypted value
        encrypted = self.handler.encrypt("test")
        self.assertTrue(self.handler.is_encrypted(encrypted))

        # Test with unencrypted value
        self.assertFalse(self.handler.is_encrypted("test"))
        self.assertFalse(self.handler.is_encrypted(123))
        self.assertFalse(self.handler.is_encrypted(None))
        self.assertFalse(self.handler.is_encrypted({"key": "value"}))

    def test_decrypt_config(self):
        """Test decryption of configuration with encrypted values."""
        # Encrypt some values in the config
        config = self.test_config.copy()
        config["database"]["password"] = self.handler.encrypt("secret_password")
        config["api"]["key"] = self.handler.encrypt("api_secret_key")
        config["api"]["endpoints"][0]["auth_token"] = self.handler.encrypt("token123")

        # Decrypt the config
        decrypted = self.handler.decrypt_config(config)

        # Check that sensitive values were decrypted
        self.assertEqual(decrypted["database"]["password"], "secret_password")
        self.assertEqual(decrypted["api"]["key"], "api_secret_key")
        self.assertEqual(decrypted["api"]["endpoints"][0]["auth_token"], "token123")

        # Check that other values were left alone
        self.assertEqual(decrypted["app"]["name"], "TestApp")
        self.assertEqual(decrypted["database"]["port"], 5432)

    def test_encrypt_config(self):
        """Test encryption of sensitive values in configuration."""
        # Define sensitive keys to encrypt
        sensitive_keys = ["password", "key", "auth_token"]

        # Encrypt the config
        encrypted = self.handler.encrypt_config(self.test_config, sensitive_keys)

        # Check that sensitive values were encrypted
        self.assertTrue(self.handler.is_encrypted(encrypted["database"]["password"]))
        self.assertTrue(self.handler.is_encrypted(encrypted["api"]["key"]))
        self.assertTrue(
            self.handler.is_encrypted(encrypted["api"]["endpoints"][0]["auth_token"])
        )

        # Check that other values were left alone
        self.assertEqual(encrypted["app"]["name"], "TestApp")
        self.assertEqual(encrypted["database"]["port"], 5432)

        # Decrypt the config and check values
        decrypted = self.handler.decrypt_config(encrypted)
        self.assertEqual(decrypted["database"]["password"], "secret_password")
        self.assertEqual(decrypted["api"]["key"], "api_secret_key")
        self.assertEqual(decrypted["api"]["endpoints"][0]["auth_token"], "token123")

    def test_generate_key(self):
        """Test key generation."""
        # Generate a new key
        key = self.handler.generate_key()

        # Check that it's a valid key
        self.assertEqual(len(key), 32)

        # Ensure we can use it to encrypt/decrypt
        encrypted = self.handler.encrypt("test")
        decrypted = self.handler.decrypt(encrypted)
        self.assertEqual(decrypted, "test")

    def test_save_load_key(self):
        """Test saving and loading a key from file."""
        # Generate and save a key
        original_key = self.handler.generate_key()
        self.handler.save_key_to_file(self.key_file_path)

        # Ensure the file exists
        self.assertTrue(self.key_file_path.exists())

        # Create a new handler and load the key
        new_handler = ConfigEncryptionHandler(key_file=self.key_file_path)

        # Test that it works for encryption/decryption
        test_value = "test_value"
        encrypted = self.handler.encrypt(test_value)
        decrypted = new_handler.decrypt(encrypted)
        self.assertEqual(decrypted, test_value)

    def test_password_based_key(self):
        """Test using a password to derive a key."""
        # Create a handler with a password
        password_handler = ConfigEncryptionHandler(password="test_password")

        # Ensure we can use it to encrypt/decrypt
        test_value = "test_value"
        encrypted = password_handler.encrypt(test_value)
        decrypted = password_handler.decrypt(encrypted)
        self.assertEqual(decrypted, test_value)

        # Create another handler with the same password
        another_handler = ConfigEncryptionHandler(password="test_password")

        # Ensure it can decrypt values from the first handler
        decrypted = another_handler.decrypt(encrypted)
        self.assertEqual(decrypted, test_value)

    def test_find_sensitive_keys(self):
        """Test finding sensitive keys in a configuration."""
        # Find sensitive keys
        sensitive_keys = find_sensitive_keys(self.test_config)

        # Check that expected keys were found
        self.assertIn("database.password", sensitive_keys)
        self.assertIn("api.key", sensitive_keys)
        self.assertIn("api.endpoints.0.auth_token", sensitive_keys)

        # Check that non-sensitive keys were not included
        self.assertNotIn("app.name", sensitive_keys)
        self.assertNotIn("database.port", sensitive_keys)

        # Test with custom patterns
        custom_patterns = ["name"]
        custom_keys = find_sensitive_keys(self.test_config, custom_patterns)
        self.assertIn("app.name", custom_keys)
        self.assertIn("api.endpoints.0.name", custom_keys)


class TestConfigManagerEncryption(unittest.TestCase):
    """Test suite for encryption features in ConfigManager."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for config files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)

        # Create a test config file
        self.config_file = self.config_dir / "test_config.yaml"
        self.test_config = {
            "app": {"name": "TestApp", "debug": True},
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "db_user",
                "password": "secret_password",
            },
            "api": {"key": "api_secret_key"},
        }

        # Generate a test encryption key
        self.test_key = b"0123456789abcdef0123456789abcdef"
        self.key_file = self.config_dir / "test_key.key"

        # Write the key to file
        with open(self.key_file, "wb") as f:
            f.write(self.test_key)

        # Write config to file
        with open(self.config_file, "w") as f:
            import yaml

            yaml.dump(self.test_config, f)

        # Initialize config manager with encryption
        self.config_manager = ConfigManager(
            config_dir=str(self.config_dir), encryption_key=self.test_key
        )
        self.config_manager.load(str(self.config_file))

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_encrypt_decrypt_value(self):
        """Test encrypting and decrypting values via ConfigManager."""
        # Encrypt a value
        value = "test_value"
        encrypted = self.config_manager.encrypt_value(value)

        # Check it's encrypted
        self.assertNotEqual(value, encrypted)
        self.assertTrue(self.config_manager.is_encrypted(encrypted))

        # Decrypt it
        decrypted = self.config_manager.decrypt_value(encrypted)
        self.assertEqual(value, decrypted)

    def test_encrypt_sensitive_values(self):
        """Test encrypting sensitive values in the configuration."""
        # Encrypt sensitive values
        self.config_manager.encrypt_sensitive_values()

        # Get the encrypted values
        password = self.config_manager.get("database.password")
        api_key = self.config_manager.get("api.key")

        # Verify they're encrypted
        self.assertTrue(self.config_manager.is_encrypted(password))
        self.assertTrue(self.config_manager.is_encrypted(api_key))

        # Verify we can still get decrypted values (the get method should decrypt)
        decrypted_password = self.config_manager.decrypt_value(password)
        self.assertEqual(decrypted_password, "secret_password")

        # Test with custom patterns
        self.config_manager = ConfigManager(
            config_dir=str(self.config_dir), encryption_key=self.test_key
        )
        self.config_manager.load(str(self.config_file))
        self.config_manager.encrypt_sensitive_values(["name"])

        # Check that name was encrypted
        app_name = self.config_manager.get("app.name")
        self.assertTrue(self.config_manager.is_encrypted(app_name))

    def test_load_with_encryption(self):
        """Test loading an encrypted configuration file."""
        # Create a new encrypted config file
        encrypted_config = self.test_config.copy()
        handler = ConfigEncryptionHandler(key=self.test_key)
        encrypted_config["database"]["password"] = handler.encrypt("secret_password")
        encrypted_config["api"]["key"] = handler.encrypt("api_secret_key")

        encrypted_file = self.config_dir / "encrypted_config.yaml"
        with open(encrypted_file, "w") as f:
            import yaml

            yaml.dump(encrypted_config, f)

        # Create a new config manager and load the encrypted file
        config_manager = ConfigManager(
            config_dir=str(self.config_dir), encryption_key=self.test_key
        )
        config_manager.load(str(encrypted_file))

        # Check that values were properly decrypted
        self.assertEqual(config_manager.get("database.password"), "secret_password")
        self.assertEqual(config_manager.get("api.key"), "api_secret_key")

    def test_generate_encryption_key(self):
        """Test generating an encryption key via ConfigManager."""
        # Create manager without encryption
        config_manager = ConfigManager(config_dir=str(self.config_dir))

        # Generate a key
        key_file = self.config_dir / "generated_key.key"
        key = config_manager.generate_encryption_key(str(key_file))

        # Check the key was generated and file exists
        self.assertIsNotNone(key)
        self.assertTrue(key_file.exists())

        # Check that encryption is now enabled
        encrypted = config_manager.encrypt_value("test")
        self.assertTrue(config_manager.is_encrypted(encrypted))
        self.assertEqual(config_manager.decrypt_value(encrypted), "test")
