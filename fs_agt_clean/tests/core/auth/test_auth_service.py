"""
Tests for the Authentication Service.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from core.auth.auth_service import AuthService


class TestAuthService(unittest.TestCase):
    """Tests for the Authentication Service."""

    def setUp(self):
        """Set up the test environment."""
        # Create a simple AuthService with minimal dependencies
        from core.auth.auth_service import AuthConfig, RedisManager, VaultSecretManager

        config = AuthConfig()
        redis_manager = RedisManager()
        secret_manager = VaultSecretManager()
        self.auth_service = AuthService(config, redis_manager, secret_manager)

    def test_authenticate_user_success(self):
        """Test successful authentication."""
        # Use the test credentials defined in auth_service.py
        result = self.auth_service.authenticate_user("testuser", "testpassword")
        self.assertIsNotNone(result)
        self.assertEqual(result["username"], "testuser")
        self.assertTrue("admin" in result["permissions"])

    def test_authenticate_user_failure(self):
        """Test failed authentication."""
        result = self.auth_service.authenticate_user("testuser", "wrong_password")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
