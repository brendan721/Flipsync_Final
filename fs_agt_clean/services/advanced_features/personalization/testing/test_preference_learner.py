"""
Tests for the Preference Learner functionality

This module contains unit tests for the PreferenceLearner class and related
functionality in the personalization engine.
"""

import json
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

from fs_agt_clean.services.personalization.preference_learner import (
    PreferenceCategory,
    PreferenceLearner,
)
from fs_agt_clean.services.personalization.user_action_tracker import (
    UnifiedUserActionTracker,
    UnifiedUserActionType,
)


class TestPreferenceLearner(unittest.TestCase):
    """Test cases for the PreferenceLearner class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock database connection
        self.mock_db = MagicMock()

        # Mock cursor for database queries
        self.mock_cursor = MagicMock()
        self.mock_db.execute.return_value = self.mock_cursor

        # Mock the get_database function to return our mock connection
        self.get_db_patcher = patch("fs_agt.services.database.get_database")
        self.mock_get_db = self.get_db_patcher.start()
        self.mock_get_db.return_value = self.mock_db

        # Mock the UnifiedUserActionTracker
        self.action_tracker_patcher = patch(
            "fs_agt.services.personalization.user_action_tracker.UnifiedUserActionTracker"
        )
        self.mock_action_tracker_class = self.action_tracker_patcher.start()
        self.mock_action_tracker = MagicMock()
        self.mock_action_tracker_class.return_value = self.mock_action_tracker

        # Create the preference learner instance with a test user ID
        self.test_user_id = "test_user_123"
        self.preference_learner = PreferenceLearner(self.test_user_id)

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.get_db_patcher.stop()
        self.action_tracker_patcher.stop()

    def test_init_creates_tables(self):
        """Test that initialization creates the necessary database tables."""
        # Verify that the database execute method was called with the correct SQL
        self.mock_db.execute.assert_any_call(
            unittest.mock.ANY
        )  # Just check that execute was called

        # Count the number of CREATE TABLE statements
        create_table_calls = sum(
            1
            for call in self.mock_db.execute.call_args_list
            if "CREATE TABLE IF NOT EXISTS" in call[0][0]
        )
        self.assertGreaterEqual(create_table_calls, 2)  # At least two tables created

    def test_learn_preferences_no_actions(self):
        """Test learning preferences when no user actions exist."""
        # Set up the mock to return empty actions
        self.mock_action_tracker.get_user_actions.return_value = []

        # Call the method
        preferences = self.preference_learner.learn_preferences()

        # Verify results
        self.assertEqual({}, preferences)
        self.mock_action_tracker.get_user_actions.assert_called_once()

    def test_learn_preferences_with_actions(self):
        """Test learning preferences with sample user actions."""
        # Create sample user actions
        timestamp = int(time.time())
        sample_actions = [
            {
                "id": "action1",
                "user_id": self.test_user_id,
                "session_id": "session1",
                "action_type": UnifiedUserActionType.PAGE_VIEW,
                "action_context": "dashboard",
                "action_data": None,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "action2",
                "user_id": self.test_user_id,
                "session_id": "session1",
                "action_type": UnifiedUserActionType.BUTTON_CLICK,
                "action_context": "dashboard",
                "action_data": {"button_id": "refresh"},
                "timestamp": timestamp + 10,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "action3",
                "user_id": self.test_user_id,
                "session_id": "session1",
                "action_type": UnifiedUserActionType.PAGE_VIEW,
                "action_context": "products",
                "action_data": None,
                "timestamp": timestamp + 20,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "action4",
                "user_id": self.test_user_id,
                "session_id": "session1",
                "action_type": UnifiedUserActionType.FEATURE_USE,
                "action_context": "products",
                "action_data": {"feature_id": "sort"},
                "timestamp": timestamp + 30,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "action5",
                "user_id": self.test_user_id,
                "session_id": "session1",
                "action_type": UnifiedUserActionType.FEATURE_USE,
                "action_context": "products",
                "action_data": {"feature_id": "sort"},
                "timestamp": timestamp + 40,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "action6",
                "user_id": self.test_user_id,
                "session_id": "session1",
                "action_type": UnifiedUserActionType.FEATURE_USE,
                "action_context": "products",
                "action_data": {"feature_id": "filter"},
                "timestamp": timestamp + 50,
                "created_at": datetime.now().isoformat(),
            },
        ]

        # Set up the mock to return our sample actions
        self.mock_action_tracker.get_user_actions.return_value = sample_actions

        # Mock UUID for deterministic testing
        with patch("uuid.uuid4", return_value="mock-uuid"):
            # Call the method with a low confidence threshold to ensure we get results
            preferences = self.preference_learner.learn_preferences(min_confidence=0.0)

            # Verify that it attempted to learn preferences by checking some methods were called
            self.mock_action_tracker.get_user_actions.assert_called_once()

            # Verify at least some preferences were extracted
            self.assertGreater(len(preferences), 0)

            # We should at least have feature usage preferences
            if PreferenceCategory.FEATURE_USAGE in preferences:
                feature_prefs = preferences[PreferenceCategory.FEATURE_USAGE]
                if "most_used_features" in feature_prefs:
                    most_used = feature_prefs["most_used_features"]["value"]
                    # The most used feature should be 'sort' based on our sample data
                    self.assertEqual(most_used[0], "sort")

    def test_get_user_preferences(self):
        """Test retrieving stored user preferences."""
        # Mock the database cursor to return some preferences
        sample_preferences = [
            (
                PreferenceCategory.UI_LAYOUT,
                "preferred_pages",
                json.dumps(["dashboard", "products", "settings"]),
                0.85,
            ),
            (
                PreferenceCategory.FEATURE_USAGE,
                "most_used_features",
                json.dumps(["sort", "filter", "search"]),
                0.9,
            ),
        ]
        self.mock_cursor.fetchall.return_value = sample_preferences

        # Call the method
        preferences = self.preference_learner.get_user_preferences()

        # Verify the SQL execution
        self.mock_db.execute.assert_called_with(unittest.mock.ANY, unittest.mock.ANY)

        # Verify the results
        self.assertEqual(len(preferences), 2)
        self.assertIn(PreferenceCategory.UI_LAYOUT, preferences)
        self.assertIn(PreferenceCategory.FEATURE_USAGE, preferences)

        # Check specific preference values
        ui_prefs = preferences[PreferenceCategory.UI_LAYOUT]
        self.assertEqual(
            ui_prefs["preferred_pages"]["value"], ["dashboard", "products", "settings"]
        )
        self.assertEqual(ui_prefs["preferred_pages"]["confidence"], 0.85)

        feature_prefs = preferences[PreferenceCategory.FEATURE_USAGE]
        self.assertEqual(
            feature_prefs["most_used_features"]["value"], ["sort", "filter", "search"]
        )
        self.assertEqual(feature_prefs["most_used_features"]["confidence"], 0.9)

    def test_save_preferences(self):
        """Test saving learned preferences to the database."""
        # Sample preferences to save
        preferences = {
            PreferenceCategory.UI_LAYOUT: {
                "preferred_pages": {
                    "value": ["dashboard", "products"],
                    "confidence": 0.75,
                }
            },
            PreferenceCategory.FEATURE_USAGE: {
                "most_used_features": {"value": ["sort", "filter"], "confidence": 0.8}
            },
        }

        # Mock the database cursor for the existing check (no existing preferences)
        self.mock_cursor.fetchone.return_value = None

        # Mock UUID for deterministic testing
        with patch("uuid.uuid4", return_value="mock-uuid"):
            # Call the method
            self.preference_learner._save_preferences(preferences)

            # Verify database interactions
            # First it should check for existing preferences
            self.mock_db.execute.assert_any_call(unittest.mock.ANY, unittest.mock.ANY)

            # Then it should insert new preferences
            insert_calls = [
                call
                for call in self.mock_db.execute.call_args_list
                if "INSERT INTO user_preferences" in call[0][0]
            ]
            self.assertGreaterEqual(
                len(insert_calls), 2
            )  # At least 2 inserts (one for each preference)

            # And also insert into history
            history_calls = [
                call
                for call in self.mock_db.execute.call_args_list
                if "INSERT INTO user_preference_history" in call[0][0]
            ]
            self.assertGreaterEqual(len(history_calls), 2)  # At least 2 history entries


if __name__ == "__main__":
    unittest.main()
