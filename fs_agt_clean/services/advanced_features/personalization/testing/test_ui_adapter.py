"""
Tests for the UI Adapter functionality

This module contains unit tests for the UIAdapter class and related
functionality in the personalization engine.
"""

import json
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

from fs_agt_clean.services.personalization.preference_learner import PreferenceCategory
from fs_agt_clean.services.personalization.ui.ui_adapter import UIAdapter, UIComponent


class TestUIAdapter(unittest.TestCase):
    """Test cases for the UIAdapter class."""

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

        # Mock PreferenceLearner
        self.preference_learner_patcher = patch(
            "fs_agt.services.personalization.preference_learner.PreferenceLearner"
        )
        self.mock_preference_learner_class = self.preference_learner_patcher.start()
        self.mock_preference_learner = MagicMock()
        self.mock_preference_learner_class.return_value = self.mock_preference_learner

        # Create the UI adapter instance with a test user ID
        self.test_user_id = "test_user_123"
        self.ui_adapter = UIAdapter(self.test_user_id)

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.get_db_patcher.stop()
        self.preference_learner_patcher.stop()

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
        self.assertGreaterEqual(create_table_calls, 1)  # At least one table created

    def test_get_personalized_ui_dashboard(self):
        """Test getting personalized UI settings for the dashboard component."""
        # Set up mock preferences
        mock_preferences = {
            PreferenceCategory.FEATURE_USAGE: {
                "most_used_features": {
                    "value": ["analytics", "inventory", "orders"],
                    "confidence": 0.85,
                }
            },
            PreferenceCategory.UI_LAYOUT: {
                "preferred_pages": {
                    "value": ["dashboard-analytics", "products", "settings"],
                    "confidence": 0.8,
                }
            },
            PreferenceCategory.CONTENT_INTERESTS: {
                "favorite_categories": {
                    "value": ["sales", "inventory", "marketing"],
                    "confidence": 0.9,
                }
            },
            PreferenceCategory.TIME_OF_DAY: {
                "active_period": {"value": "morning", "confidence": 0.75}
            },
        }
        self.mock_preference_learner.get_user_preferences.return_value = (
            mock_preferences
        )

        # Mock cursor for checking existing personalization
        self.mock_cursor.fetchone.return_value = None

        # Mock UUID
        with patch("uuid.uuid4", return_value="mock-uuid"):
            # Call the method with some context
            context = {"current_hour": 9}  # 9 AM
            ui_settings = self.ui_adapter.get_personalized_ui(
                UIComponent.DASHBOARD, context=context, min_confidence=0.7
            )

            # Verify the preferences were retrieved
            self.mock_preference_learner.get_user_preferences.assert_called_once_with(
                min_confidence=0.7
            )

            # Verify the personalized settings
            self.assertEqual(
                ui_settings["layout"], "focused"
            )  # Morning = focused layout
            self.assertEqual(
                ui_settings["default_view"], "analytics"
            )  # From preferred pages

            # Check widgets
            self.assertIn("analytics_summary", ui_settings["widgets"])
            self.assertIn("inventory_status", ui_settings["widgets"])
            self.assertIn("recent_orders", ui_settings["widgets"])

            # Check highlighted categories
            self.assertEqual(
                ui_settings["highlighted_categories"],
                ["sales", "inventory", "marketing"],
            )

            # Verify personalization was saved
            self.mock_db.execute.assert_any_call(unittest.mock.ANY, unittest.mock.ANY)

    def test_get_personalized_ui_navigation(self):
        """Test getting personalized UI settings for the navigation component."""
        # Set up mock preferences
        mock_preferences = {
            PreferenceCategory.UI_LAYOUT: {
                "preferred_pages": {
                    "value": ["dashboard", "products", "settings"],
                    "confidence": 0.8,
                },
                "navigation_patterns": {
                    "value": ["dashboard->products", "products->orders"],
                    "confidence": 0.75,
                },
            },
            PreferenceCategory.FEATURE_USAGE: {
                "most_used_features": {
                    "value": ["sort", "filter", "search"],
                    "confidence": 0.85,
                }
            },
            PreferenceCategory.WORKFLOW_PATTERNS: {
                "common_workflows": {
                    "value": [
                        ["dashboard", "products", "orders"],
                        ["settings", "profile", "logout"],
                    ],
                    "confidence": 0.8,
                }
            },
        }
        self.mock_preference_learner.get_user_preferences.return_value = (
            mock_preferences
        )

        # Mock cursor for checking existing personalization
        self.mock_cursor.fetchone.return_value = None

        # Mock UUID
        with patch("uuid.uuid4", return_value="mock-uuid"):
            # Call the method with context indicating we're on the dashboard
            context = {"current_page": "dashboard"}
            ui_settings = self.ui_adapter.get_personalized_ui(
                UIComponent.NAVIGATION, context=context, min_confidence=0.7
            )

            # Verify the personalized settings
            self.assertEqual(
                ui_settings["quick_links"], ["dashboard", "products", "settings"]
            )

            # Should have expanded dashboard section since it's a common starting point
            self.assertIn("dashboard", ui_settings["expanded_sections"])

            # Should suggest "products" as the next page since that follows dashboard in workflow
            self.assertEqual(ui_settings["suggested_next"], ["products"])

            # Should highlight most used features
            self.assertEqual(
                ui_settings["highlighted_sections"], ["sort", "filter", "search"]
            )

            # Verify personalization was saved
            self.mock_db.execute.assert_any_call(unittest.mock.ANY, unittest.mock.ANY)

    def test_get_personalized_ui_unknown_component(self):
        """Test getting personalized UI settings for an unknown component."""
        # Set up mock preferences
        self.mock_preference_learner.get_user_preferences.return_value = {}

        # Call the method with an unknown component
        ui_settings = self.ui_adapter.get_personalized_ui("unknown_component")

        # Verify empty settings returned
        self.assertEqual(ui_settings, {})

        # Verify no personalization was saved (since settings are empty)
        save_calls = [
            call
            for call in self.mock_db.execute.call_args_list
            if "INSERT INTO ui_personalization" in str(call)
        ]
        self.assertEqual(len(save_calls), 0)

    def test_get_all_personalization_settings(self):
        """Test retrieving all saved UI personalization settings."""
        # Mock the database cursor to return some settings
        sample_settings = [
            (
                UIComponent.DASHBOARD,
                json.dumps(
                    {
                        "layout": "focused",
                        "widgets": [
                            "analytics_summary",
                            "inventory_status",
                            "recent_orders",
                        ],
                    }
                ),
            ),
            (
                UIComponent.NAVIGATION,
                json.dumps(
                    {
                        "quick_links": ["dashboard", "products", "settings"],
                        "expanded_sections": ["dashboard"],
                    }
                ),
            ),
        ]
        self.mock_cursor.fetchall.return_value = sample_settings

        # Call the method
        settings = self.ui_adapter.get_all_personalization_settings()

        # Verify the SQL execution
        self.mock_db.execute.assert_called_with(unittest.mock.ANY, (self.test_user_id,))

        # Verify the results
        self.assertEqual(len(settings), 2)
        self.assertIn(UIComponent.DASHBOARD, settings)
        self.assertIn(UIComponent.NAVIGATION, settings)

        # Check specific settings values
        dashboard_settings = settings[UIComponent.DASHBOARD]
        self.assertEqual(dashboard_settings["layout"], "focused")
        self.assertEqual(
            dashboard_settings["widgets"],
            ["analytics_summary", "inventory_status", "recent_orders"],
        )

        nav_settings = settings[UIComponent.NAVIGATION]
        self.assertEqual(
            nav_settings["quick_links"], ["dashboard", "products", "settings"]
        )
        self.assertEqual(nav_settings["expanded_sections"], ["dashboard"])

    def test_save_personalization_new(self):
        """Test saving new personalization settings."""
        # Settings to save
        component = UIComponent.DASHBOARD
        settings = {
            "layout": "focused",
            "widgets": ["analytics_summary", "inventory_status"],
            "default_view": "overview",
        }

        # Mock cursor for the existing check (no existing settings)
        self.mock_cursor.fetchone.return_value = None

        # Mock UUID and datetime
        with (
            patch("uuid.uuid4", return_value="mock-uuid"),
            patch(
                "fs_agt.services.utils.time_utils.get_current_timestamp",
                return_value=12345,
            ),
        ):

            # Call the method
            self.ui_adapter._save_personalization(component, settings)

            # Verify database interactions
            # First it should check for existing settings
            self.mock_db.execute.assert_any_call(
                unittest.mock.ANY, (self.test_user_id, component)
            )

            # Then it should insert new settings
            insert_calls = [
                call
                for call in self.mock_db.execute.call_args_list
                if "INSERT INTO ui_personalization" in call[0][0]
            ]
            self.assertEqual(len(insert_calls), 1)

    def test_save_personalization_update(self):
        """Test updating existing personalization settings."""
        # Settings to save
        component = UIComponent.DASHBOARD
        settings = {
            "layout": "focused",
            "widgets": ["analytics_summary", "inventory_status"],
            "default_view": "overview",
        }

        # Mock cursor for the existing check (existing settings)
        self.mock_cursor.fetchone.return_value = ("existing-id",)

        # Mock timestamp
        with patch(
            "fs_agt.services.utils.time_utils.get_current_timestamp", return_value=12345
        ):

            # Call the method
            self.ui_adapter._save_personalization(component, settings)

            # Verify database interactions
            # First it should check for existing settings
            self.mock_db.execute.assert_any_call(
                unittest.mock.ANY, (self.test_user_id, component)
            )

            # Then it should update existing settings
            update_calls = [
                call
                for call in self.mock_db.execute.call_args_list
                if "UPDATE ui_personalization" in call[0][0]
            ]
            self.assertEqual(len(update_calls), 1)


if __name__ == "__main__":
    unittest.main()
