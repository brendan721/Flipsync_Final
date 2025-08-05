"""
Tests for the encryption module.
"""

import base64
import unittest
from unittest import mock

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.security.encryption import (
    EncryptedData,
    EncryptionConfig,
    EncryptionHandler,
    get_encryption_handler,
)


class TestEncryptionHandler(unittest.TestCase):
    """Tests for the EncryptionHandler class."""

    def setUp(self):
        """Set up test environment."""
        # Mock the ConfigManager
        self.mock_config_manager = mock.MagicMock(spec=ConfigManager)
        self.mock_config_manager.get_section.return_value = {
            "algorithm": "AES-256-GCM",
            "key_size": 32,
            "salt_size": 16,
            "iterations": 100000,
        }
        self.mock_config_manager.get.return_value = None

        # Reset the singleton instance
        EncryptionHandler._instance = None

        # Create encryption handler
        self.encryption_handler = EncryptionHandler(
            config_manager=self.mock_config_manager
        )

        # Initialize with a test key
        self.test_key = b"0" * 32
        self.encryption_handler.initialize(master_key=self.test_key)

    def tearDown(self):
        """Clean up test environment."""
        # Reset the singleton instance
        EncryptionHandler._instance = None

        # Reset the global instance
        import sys

        module = sys.modules[EncryptionHandler.__module__]
        module._encryption_handler_instance = None

    def test_singleton(self):
        """Test that EncryptionHandler is a singleton."""
        handler1 = EncryptionHandler()
        handler2 = EncryptionHandler()
        self.assertIs(handler1, handler2)

    def test_get_encryption_handler(self):
        """Test get_encryption_handler function."""
        handler = get_encryption_handler()
        self.assertIsInstance(handler, EncryptionHandler)

        # Should return the same instance
        handler2 = get_encryption_handler()
        self.assertIs(handler, handler2)

    def test_initialize(self):
        """Test initialization."""
        # Reset handler
        self.encryption_handler._master_key = None

        # Initialize with a new key
        result = self.encryption_handler.initialize(master_key=b"1" * 32)
        self.assertTrue(result)
        self.assertEqual(self.encryption_handler._master_key, b"1" * 32)

    def test_initialize_from_config(self):
        """Test initialization from config."""
        # Reset handler
        self.encryption_handler._master_key = None

        # Mock config
        key_str = base64.b64encode(b"2" * 32).decode()
        self.mock_config_manager.get.return_value = key_str

        # Initialize
        result = self.encryption_handler.initialize()
        self.assertTrue(result)
        self.assertEqual(self.encryption_handler._master_key, b"2" * 32)

    def test_initialize_generate_key(self):
        """Test initialization with key generation."""
        # Reset handler
        self.encryption_handler._master_key = None

        # Mock config
        self.mock_config_manager.get.return_value = None

        # Initialize
        result = self.encryption_handler.initialize()
        self.assertTrue(result)
        self.assertIsNotNone(self.encryption_handler._master_key)
        self.assertEqual(len(self.encryption_handler._master_key), 32)

        # Should save to config
        self.mock_config_manager.set.assert_called_once()
        args, _ = self.mock_config_manager.set.call_args
        self.assertEqual(args[0], "encryption.master_key")

    def test_encrypt_decrypt_string(self):
        """Test encrypting and decrypting a string."""
        # Encrypt
        plaintext = "Hello, world!"
        encrypted = self.encryption_handler.encrypt(plaintext)

        # Verify structure
        self.assertIsInstance(encrypted, dict)
        self.assertEqual(encrypted["version"], "1")
        self.assertEqual(encrypted["algorithm"], "AES-256-GCM")
        self.assertIn("salt", encrypted)
        self.assertIn("nonce", encrypted)
        self.assertIn("ciphertext", encrypted)

        # Decrypt
        decrypted = self.encryption_handler.decrypt(encrypted)
        self.assertEqual(decrypted.decode(), plaintext)

    def test_encrypt_decrypt_bytes(self):
        """Test encrypting and decrypting bytes."""
        # Encrypt
        plaintext = b"Hello, world!"
        encrypted = self.encryption_handler.encrypt(plaintext)

        # Decrypt
        decrypted = self.encryption_handler.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)

    def test_encrypt_decrypt_dict(self):
        """Test encrypting and decrypting a dictionary."""
        # Encrypt
        plaintext = {"name": "John", "age": 30}
        encrypted = self.encryption_handler.encrypt(plaintext)

        # Decrypt
        decrypted = self.encryption_handler.decrypt(encrypted)
        self.assertEqual(decrypted, str(plaintext).encode())

    def test_encrypt_decrypt_with_context(self):
        """Test encrypting and decrypting with context."""
        # Encrypt
        plaintext = "Hello, world!"
        context = "test_context"
        encrypted = self.encryption_handler.encrypt(plaintext, context)

        # Verify context
        self.assertEqual(encrypted["context"], context)

        # Decrypt
        decrypted = self.encryption_handler.decrypt(encrypted)
        self.assertEqual(decrypted.decode(), plaintext)

    def test_encrypt_not_initialized(self):
        """Test encrypting when not initialized."""
        # Reset handler
        self.encryption_handler._master_key = None

        # Encrypt
        with self.assertRaises(RuntimeError):
            self.encryption_handler.encrypt("Hello, world!")

    def test_decrypt_not_initialized(self):
        """Test decrypting when not initialized."""
        # Reset handler
        self.encryption_handler._master_key = None

        # Decrypt
        encrypted_data = EncryptedData(
            version="1",
            algorithm="AES-256-GCM",
            salt="salt",
            nonce="nonce",
            ciphertext="ciphertext",
            context="",
        )
        with self.assertRaises(RuntimeError):
            self.encryption_handler.decrypt(encrypted_data)

    def test_decrypt_invalid_version(self):
        """Test decrypting with invalid version."""
        # Create encrypted data with invalid version
        encrypted_data = EncryptedData(
            version="2",
            algorithm="AES-256-GCM",
            salt=base64.b64encode(b"salt").decode(),
            nonce=base64.b64encode(b"nonce").decode(),
            ciphertext=base64.b64encode(b"ciphertext").decode(),
            context="",
        )

        # Decrypt
        with self.assertRaises(ValueError):
            self.encryption_handler.decrypt(encrypted_data)

    def test_decrypt_invalid_algorithm(self):
        """Test decrypting with invalid algorithm."""
        # Create encrypted data with invalid algorithm
        encrypted_data = EncryptedData(
            version="1",
            algorithm="invalid",
            salt=base64.b64encode(b"salt").decode(),
            nonce=base64.b64encode(b"nonce").decode(),
            ciphertext=base64.b64encode(b"ciphertext").decode(),
            context="",
        )

        # Decrypt
        with self.assertRaises(ValueError):
            self.encryption_handler.decrypt(encrypted_data)

    def test_rotate_master_key(self):
        """Test rotating the master key."""
        # Store original key
        original_key = self.encryption_handler._master_key

        # Rotate key
        result = self.encryption_handler.rotate_master_key()
        self.assertTrue(result)

        # Verify key changed
        self.assertNotEqual(self.encryption_handler._master_key, original_key)

        # Should save to config
        self.mock_config_manager.set.assert_called_with(
            "encryption.master_key",
            base64.b64encode(self.encryption_handler._master_key).decode(),
        )

    def test_get_config(self):
        """Test getting the encryption configuration."""
        config = self.encryption_handler.get_config()
        self.assertIsInstance(config, EncryptionConfig)
        self.assertEqual(config.algorithm, "AES-256-GCM")
        self.assertEqual(config.key_size, 32)
        self.assertEqual(config.salt_size, 16)
        self.assertEqual(config.iterations, 100000)

    def test_hash_verify_password(self):
        """Test hashing and verifying a password."""
        # Hash password
        password = "password123"
        password_hash = self.encryption_handler.hash_password(password)

        # Verify structure
        self.assertIsInstance(password_hash, str)

        # Verify password
        result = self.encryption_handler.verify_password(password, password_hash)
        self.assertTrue(result)

        # Verify wrong password
        result = self.encryption_handler.verify_password("wrong", password_hash)
        self.assertFalse(result)

    def test_verify_password_invalid_hash(self):
        """Test verifying a password with invalid hash."""
        result = self.encryption_handler.verify_password("password", "invalid")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
