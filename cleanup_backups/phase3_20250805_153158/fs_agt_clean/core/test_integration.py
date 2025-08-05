"""
Integration tests for the core components.
"""

import os
import tempfile
import unittest
from pathlib import Path

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.config.env_handler import (
    interpolate_env_vars,
    update_from_env_vars,
)
from fs_agt_clean.core.config.feature_flags import FeatureFlagManager
from fs_agt_clean.core.db.session import SessionManager
from fs_agt_clean.core.security.encryption import EncryptionHandler


class TestCoreIntegration(unittest.TestCase):
    """Integration tests for the core components."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for configuration
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)

        # Create a config file
        self.config_file = self.config_dir / "config.yaml"
        with open(self.config_file, "w") as f:
            f.write(
                """
database:
  url: "sqlite:///:memory:"
  echo: false
  pool_size: 5
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600
  pool_pre_ping: true

encryption:
  key: "test_key"
  algorithm: "aes-256-cbc"
  iterations: 100000
  salt_size: 16
  key_size: 32

feature_flags:
  storage_path: "${CONFIG_DIR}/feature_flags.json"
  read_interval: 5.0
"""
            )

        # Set environment variables
        os.environ["CONFIG_DIR"] = str(self.config_dir)

        # Create config manager
        self.config_manager = ConfigManager(config_dir=self.config_dir)

        # Load the config file
        self.config_manager.load(self.config_file)

    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary directory
        self.temp_dir.cleanup()

        # Reset environment variables
        if "CONFIG_DIR" in os.environ:
            del os.environ["CONFIG_DIR"]

    def test_config_manager(self):
        """Test ConfigManager integration."""
        # Test getting configuration values
        self.assertEqual(self.config_manager.get("database.url"), "sqlite:///:memory:")
        self.assertEqual(self.config_manager.get("encryption.key"), "test_key")
        self.assertEqual(self.config_manager.get("feature_flags.read_interval"), 5.0)

    def test_encryption_handler(self):
        """Test EncryptionHandler integration."""
        # Create encryption handler
        encryption_handler = EncryptionHandler(config_manager=self.config_manager)

        # Initialize with a test key
        test_key = b"test_key_for_encryption_handler_test"
        encryption_handler.initialize(master_key=test_key)

        # Test encryption and decryption
        plaintext = "test_plaintext"
        encrypted_data = encryption_handler.encrypt(plaintext)
        decrypted = encryption_handler.decrypt(encrypted_data)
        self.assertEqual(decrypted.decode(), plaintext)

        # Test password hashing and verification
        password = "test_password"
        hashed = encryption_handler.hash_password(password)
        self.assertTrue(encryption_handler.verify_password(password, hashed))
        self.assertFalse(encryption_handler.verify_password("wrong_password", hashed))

    def test_feature_flags(self):
        """Test FeatureFlagManager integration."""
        # Create feature flag manager
        feature_flag_manager = FeatureFlagManager(config_manager=self.config_manager)

        # Test setting and getting feature flags
        feature_flag_manager.set_enabled("test_flag", True)
        self.assertTrue(feature_flag_manager.is_enabled("test_flag"))
        self.assertFalse(feature_flag_manager.is_enabled("nonexistent_flag"))

        # Test percentage-based feature flags
        feature_flag_manager.set_percentage_flag("percentage_flag", 50.0)
        self.assertTrue(
            feature_flag_manager.is_enabled_for_percentage("percentage_flag", 25.0)
        )
        self.assertFalse(
            feature_flag_manager.is_enabled_for_percentage("percentage_flag", 75.0)
        )

        # Test user-specific feature flags
        feature_flag_manager.set_user_flag("user_flag", ["user1", "user2"])
        self.assertTrue(feature_flag_manager.is_enabled_for_user("user_flag", "user1"))
        self.assertFalse(feature_flag_manager.is_enabled_for_user("user_flag", "user3"))

    def test_env_handler(self):
        """Test environment variable handling integration."""
        # Test interpolation
        os.environ["TEST_VAR"] = "test_value"
        self.assertEqual(
            interpolate_env_vars("Value: ${TEST_VAR}"), "Value: test_value"
        )

        # Test updating configuration from environment variables
        os.environ["APP_DATABASE__URL"] = "sqlite:///test.db"
        config = {}
        config = update_from_env_vars(config)
        self.assertEqual(config["database"]["url"], "sqlite:///test.db")

    def test_database_connection(self):
        """Test database connection integration."""
        # Create session manager
        session_manager = SessionManager(config_manager=self.config_manager)

        # Test that the engine and session factory are initialized
        self.assertIsNotNone(session_manager._engine)
        self.assertIsNotNone(session_manager._session_factory)


if __name__ == "__main__":
    unittest.main()
