"""
Tests for the feature_flags module.
"""

import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.config.feature_flags import (
    FeatureFlag,
    FeatureFlagManager,
    FeatureFlagStorage,
    PercentageFeatureFlag,
    UnifiedUserFeatureFlag,
    get_feature_flag_manager,
    is_feature_enabled,
    is_feature_enabled_for_user,
)


class TestFeatureFlags(unittest.TestCase):
    """Tests for the feature_flags module."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for feature flag storage
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "feature_flags.json"

        # Mock the ConfigManager
        self.mock_config_manager = mock.MagicMock(spec=ConfigManager)
        self.mock_config_manager.get.return_value = None
        self.mock_config_manager.config_dir = Path(self.temp_dir.name)

        # Reset the singleton instance
        FeatureFlagManager._instance = None

        # Reset the global instance
        import sys

        module = sys.modules[FeatureFlagManager.__module__]
        module._feature_flag_manager_instance = None

        # Create feature flag manager
        self.feature_flag_manager = FeatureFlagManager(
            config_manager=self.mock_config_manager,
            storage_path=self.storage_path,
        )

        # Ensure _last_read_time is initialized
        self.feature_flag_manager._last_read_time = time.time()

    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary directory
        self.temp_dir.cleanup()

        # Reset the singleton instance
        FeatureFlagManager._instance = None

        # Reset the global instance
        import sys

        module = sys.modules[FeatureFlagManager.__module__]
        module._feature_flag_manager_instance = None

    def test_singleton(self):
        """Test that FeatureFlagManager is a singleton."""
        manager1 = FeatureFlagManager()
        manager2 = FeatureFlagManager()
        self.assertIs(manager1, manager2)

    def test_get_feature_flag_manager(self):
        """Test get_feature_flag_manager function."""
        manager = get_feature_flag_manager()
        self.assertIsInstance(manager, FeatureFlagManager)

        # Should return the same instance
        manager2 = get_feature_flag_manager()
        self.assertIs(manager, manager2)

    def test_is_feature_enabled(self):
        """Test is_feature_enabled function."""
        # Set up a feature flag
        self.feature_flag_manager.set_enabled("test_flag", True)

        # Test the function
        self.assertTrue(is_feature_enabled("test_flag"))
        self.assertFalse(is_feature_enabled("nonexistent_flag"))
        self.assertTrue(is_feature_enabled("nonexistent_flag", default=True))

    def test_is_feature_enabled_for_user(self):
        """Test is_feature_enabled_for_user function."""
        # Set up a user feature flag
        self.feature_flag_manager.set_user_flag(
            "test_user_flag", ["user1", "user2"], True
        )

        # Test the function
        self.assertTrue(is_feature_enabled_for_user("test_user_flag", "user1"))
        self.assertTrue(is_feature_enabled_for_user("test_user_flag", "user2"))
        self.assertFalse(is_feature_enabled_for_user("test_user_flag", "user3"))
        self.assertTrue(
            is_feature_enabled_for_user("nonexistent_flag", "user1", default=True)
        )

    def test_set_enabled(self):
        """Test set_enabled method."""
        # Set a feature flag
        flag = self.feature_flag_manager.set_enabled(
            "test_flag",
            True,
            description="Test flag",
            group="test_group",
            owner="test_owner",
        )

        # Verify flag properties
        self.assertEqual(flag.key, "test_flag")
        self.assertTrue(flag.enabled)
        self.assertEqual(flag.description, "Test flag")
        self.assertEqual(flag.group, "test_group")
        self.assertEqual(flag.owner, "test_owner")

        # Verify flag is in storage
        self.assertIn("test_flag", self.feature_flag_manager.storage.flags)

        # Verify file was created
        self.assertTrue(self.storage_path.exists())

        # Load file and verify contents
        with open(self.storage_path, "r") as f:
            data = json.load(f)
            self.assertIn("flags", data)
            self.assertIn("test_flag", data["flags"])
            self.assertTrue(data["flags"]["test_flag"]["enabled"])

    def test_set_percentage_flag(self):
        """Test set_percentage_flag method."""
        # Set a percentage feature flag
        flag = self.feature_flag_manager.set_percentage_flag(
            "test_percentage_flag",
            50.0,
            True,
            description="Test percentage flag",
            group="test_group",
            owner="test_owner",
        )

        # Verify flag properties
        self.assertEqual(flag.key, "test_percentage_flag")
        self.assertTrue(flag.enabled)
        self.assertEqual(flag.percentage, 50.0)
        self.assertEqual(flag.description, "Test percentage flag")
        self.assertEqual(flag.group, "test_group")
        self.assertEqual(flag.owner, "test_owner")

        # Verify flag is in storage
        self.assertIn("test_percentage_flag", self.feature_flag_manager.storage.flags)

        # Verify file was created
        self.assertTrue(self.storage_path.exists())

        # Load file and verify contents
        with open(self.storage_path, "r") as f:
            data = json.load(f)
            self.assertIn("flags", data)
            self.assertIn("test_percentage_flag", data["flags"])
            self.assertTrue(data["flags"]["test_percentage_flag"]["enabled"])
            self.assertEqual(data["flags"]["test_percentage_flag"]["percentage"], 50.0)

    def test_set_user_flag(self):
        """Test set_user_flag method."""
        # Set a user feature flag
        flag = self.feature_flag_manager.set_user_flag(
            "test_user_flag",
            ["user1", "user2"],
            True,
            description="Test user flag",
            group="test_group",
            owner="test_owner",
        )

        # Verify flag properties
        self.assertEqual(flag.key, "test_user_flag")
        self.assertTrue(flag.enabled)
        self.assertEqual(flag.user_ids, ["user1", "user2"])
        self.assertEqual(flag.description, "Test user flag")
        self.assertEqual(flag.group, "test_group")
        self.assertEqual(flag.owner, "test_owner")

        # Verify flag is in storage
        self.assertIn("test_user_flag", self.feature_flag_manager.storage.flags)

        # Verify file was created
        self.assertTrue(self.storage_path.exists())

        # Load file and verify contents
        with open(self.storage_path, "r") as f:
            data = json.load(f)
            self.assertIn("flags", data)
            self.assertIn("test_user_flag", data["flags"])
            self.assertTrue(data["flags"]["test_user_flag"]["enabled"])
            self.assertEqual(
                data["flags"]["test_user_flag"]["user_ids"], ["user1", "user2"]
            )

    def test_add_user_to_flag(self):
        """Test add_user_to_flag method."""
        # Set a user feature flag
        self.feature_flag_manager.set_user_flag(
            "test_user_flag", ["user1", "user2"], True
        )

        # Add a user
        result = self.feature_flag_manager.add_user_to_flag("test_user_flag", "user3")
        self.assertTrue(result)

        # Verify user was added
        flag = self.feature_flag_manager.get_flag("test_user_flag")
        self.assertIn("user3", flag.user_ids)

        # Try to add the same user again
        result = self.feature_flag_manager.add_user_to_flag("test_user_flag", "user3")
        self.assertFalse(result)

        # Try to add a user to a non-existent flag
        result = self.feature_flag_manager.add_user_to_flag("nonexistent_flag", "user1")
        self.assertFalse(result)

        # Add a user to a non-user flag
        self.feature_flag_manager.set_enabled("test_flag", True)
        result = self.feature_flag_manager.add_user_to_flag("test_flag", "user1")
        self.assertTrue(result)

        # Verify flag was converted to a user flag
        flag = self.feature_flag_manager.get_flag("test_flag")
        self.assertIsInstance(flag, UnifiedUserFeatureFlag)
        self.assertIn("user1", flag.user_ids)

    def test_remove_user_from_flag(self):
        """Test remove_user_from_flag method."""
        # Set a user feature flag
        self.feature_flag_manager.set_user_flag(
            "test_user_flag", ["user1", "user2"], True
        )

        # Remove a user
        result = self.feature_flag_manager.remove_user_from_flag(
            "test_user_flag", "user1"
        )
        self.assertTrue(result)

        # Verify user was removed
        flag = self.feature_flag_manager.get_flag("test_user_flag")
        self.assertNotIn("user1", flag.user_ids)

        # Try to remove a non-existent user
        result = self.feature_flag_manager.remove_user_from_flag(
            "test_user_flag", "user3"
        )
        self.assertFalse(result)

        # Try to remove a user from a non-existent flag
        result = self.feature_flag_manager.remove_user_from_flag(
            "nonexistent_flag", "user1"
        )
        self.assertFalse(result)

        # Try to remove a user from a non-user flag
        self.feature_flag_manager.set_enabled("test_flag", True)
        result = self.feature_flag_manager.remove_user_from_flag("test_flag", "user1")
        self.assertFalse(result)

    def test_delete_flag(self):
        """Test delete_flag method."""
        # Set a feature flag
        self.feature_flag_manager.set_enabled("test_flag", True)

        # Delete the flag
        result = self.feature_flag_manager.delete_flag("test_flag")
        self.assertTrue(result)

        # Verify flag was deleted
        self.assertNotIn("test_flag", self.feature_flag_manager.storage.flags)

        # Try to delete a non-existent flag
        result = self.feature_flag_manager.delete_flag("nonexistent_flag")
        self.assertFalse(result)

    def test_list_flags(self):
        """Test list_flags method."""
        # Set some feature flags
        self.feature_flag_manager.set_enabled("flag1", True, group="group1")
        self.feature_flag_manager.set_enabled("flag2", False, group="group1")
        self.feature_flag_manager.set_enabled("flag3", True, group="group2")

        # List all flags
        flags = self.feature_flag_manager.list_flags()
        self.assertEqual(len(flags), 3)

        # List flags by group
        flags = self.feature_flag_manager.list_flags(group="group1")
        self.assertEqual(len(flags), 2)
        self.assertEqual({flag.key for flag in flags}, {"flag1", "flag2"})

        flags = self.feature_flag_manager.list_flags(group="group2")
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].key, "flag3")

        # List flags for non-existent group
        flags = self.feature_flag_manager.list_flags(group="nonexistent_group")
        self.assertEqual(len(flags), 0)

    def test_list_groups(self):
        """Test list_groups method."""
        # Set some feature flags
        self.feature_flag_manager.set_enabled("flag1", True, group="group1")
        self.feature_flag_manager.set_enabled("flag2", False, group="group1")
        self.feature_flag_manager.set_enabled("flag3", True, group="group2")

        # List groups
        groups = self.feature_flag_manager.list_groups()
        self.assertEqual(groups, {"group1", "group2"})

    def test_list_owners(self):
        """Test list_owners method."""
        # Set some feature flags
        self.feature_flag_manager.set_enabled("flag1", True, owner="owner1")
        self.feature_flag_manager.set_enabled("flag2", False, owner="owner1")
        self.feature_flag_manager.set_enabled("flag3", True, owner="owner2")

        # List owners
        owners = self.feature_flag_manager.list_owners()
        self.assertEqual(owners, {"owner1", "owner2"})

    def test_reload(self):
        """Test reload method."""
        # Set a feature flag
        self.feature_flag_manager.set_enabled("test_flag", True)

        # Modify the flag directly in memory
        self.feature_flag_manager.storage.flags["test_flag"].enabled = False

        # Save to disk
        self.feature_flag_manager._save()

        # Create a new instance to test reload
        new_manager = FeatureFlagManager(
            config_manager=self.mock_config_manager,
            storage_path=self.storage_path,
        )

        # Verify flag is loaded with the new value
        flag = new_manager.get_flag("test_flag")
        self.assertFalse(flag.enabled)

    def test_change_listener(self):
        """Test change listener."""
        # Create a mock listener
        listener = mock.MagicMock()

        # Add the listener directly to the list
        self.feature_flag_manager._change_listeners.append(listener)

        # Manually call the notify method
        self.feature_flag_manager._notify_listeners({}, {"test_flag": True})

        # Verify listener was called
        listener.assert_called_once()

        # Reset the mock
        listener.reset_mock()

        # Test toggling a flag
        self.feature_flag_manager._notify_listeners(
            {"test_flag": True}, {"test_flag": False}
        )

        # Verify listener was called
        listener.assert_called_once()

        # Reset the mock
        listener.reset_mock()

        # Test removing a flag
        self.feature_flag_manager._notify_listeners({"test_flag": False}, {})

        # Verify listener was called
        listener.assert_called_once()

        # Remove the listener
        self.feature_flag_manager._change_listeners.remove(listener)

        # Reset the mock
        listener.reset_mock()

        # Test adding another flag
        self.feature_flag_manager._notify_listeners({}, {"another_flag": True})

        # Verify listener was not called
        listener.assert_not_called()

    def test_is_enabled_for_user(self):
        """Test is_enabled_for_user method."""
        # Set a standard feature flag
        self.feature_flag_manager.set_enabled("standard_flag", True)

        # Set a user feature flag
        self.feature_flag_manager.set_user_flag("user_flag", ["user1", "user2"], True)

        # Set a percentage feature flag
        self.feature_flag_manager.set_percentage_flag("percentage_flag", 50.0, True)

        # Test standard flag
        self.assertTrue(
            self.feature_flag_manager.is_enabled_for_user("standard_flag", "user1")
        )
        self.assertTrue(
            self.feature_flag_manager.is_enabled_for_user("standard_flag", "user2")
        )

        # Test user flag
        self.assertTrue(
            self.feature_flag_manager.is_enabled_for_user("user_flag", "user1")
        )
        self.assertTrue(
            self.feature_flag_manager.is_enabled_for_user("user_flag", "user2")
        )
        self.assertFalse(
            self.feature_flag_manager.is_enabled_for_user("user_flag", "user3")
        )

        # Test percentage flag - this is probabilistic, so we can't assert exact values
        # Just make sure it doesn't crash
        result = self.feature_flag_manager.is_enabled_for_user(
            "percentage_flag", "user1"
        )
        self.assertIsInstance(result, bool)

    def test_is_enabled_for_percentage(self):
        """Test is_enabled_for_percentage method."""
        # Set a standard feature flag
        self.feature_flag_manager.set_enabled("standard_flag", True)

        # Set a percentage feature flag
        self.feature_flag_manager.set_percentage_flag("percentage_flag", 50.0, True)

        # Test standard flag
        self.assertTrue(
            self.feature_flag_manager.is_enabled_for_percentage("standard_flag", 25.0)
        )
        self.assertTrue(
            self.feature_flag_manager.is_enabled_for_percentage("standard_flag", 75.0)
        )

        # Test percentage flag
        self.assertTrue(
            self.feature_flag_manager.is_enabled_for_percentage("percentage_flag", 25.0)
        )
        self.assertFalse(
            self.feature_flag_manager.is_enabled_for_percentage("percentage_flag", 75.0)
        )


if __name__ == "__main__":
    unittest.main()
