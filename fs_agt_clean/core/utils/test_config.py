"""Tests for the configuration utility module."""

import os
import sys
import unittest
from typing import Any, Dict

sys.path.append("/root/venvs/Flipsync-1/.Flipsync")
from fs_agt_clean.core.utils.config import (
    Settings,
    get_settings,
    get_settings_for_agent,
    get_settings_with_mobile_context,
)


class TestSettings(unittest.TestCase):
    """Test cases for the Settings class."""

    def test_default_settings(self):
        """Test that default settings are created correctly."""
        settings = Settings()
        self.assertEqual(settings.redis_host, "localhost")
        self.assertEqual(settings.redis_port, 6379)
        self.assertEqual(settings.jwt_algorithm, "HS256")
        self.assertEqual(settings.enable_metrics, True)
        self.assertEqual(settings.mobile.context, None)
        self.assertEqual(settings.mobile.battery_optimization_enabled, True)
        self.assertEqual(settings.mobile.offline_mode_enabled, False)
        self.assertEqual(settings.mobile.payload_optimization_enabled, True)
        self.assertEqual(settings.agent_coordination.hierarchical_enabled, True)
        self.assertEqual(settings.conversational.nlp_enabled, True)
        self.assertEqual(settings.security.encryption_enabled, True)

    def test_is_mobile_context(self):
        """Test the is_mobile_context method."""
        settings = Settings()
        self.assertFalse(settings.is_mobile_context())

        settings.mobile.context = {"battery_level": 50}
        self.assertTrue(settings.is_mobile_context())

    def test_is_low_battery(self):
        """Test the is_low_battery method."""
        settings = Settings()
        self.assertFalse(settings.is_low_battery())

        settings.mobile.context = {"battery_level": 50}
        self.assertFalse(settings.is_low_battery())

        settings.mobile.context = {"battery_level": 15}
        self.assertTrue(settings.is_low_battery())

        settings.mobile.battery_optimization_enabled = False
        self.assertFalse(settings.is_low_battery())

    def test_adjust_processing_intensity(self):
        """Test the adjust_processing_intensity method."""
        settings = Settings()
        self.assertEqual(settings.adjust_processing_intensity(1.0), 1.0)

        settings.mobile.context = {"battery_level": 15}
        self.assertEqual(settings.adjust_processing_intensity(1.0), 0.5)

        settings.mobile.battery_optimization_enabled = False
        self.assertEqual(settings.adjust_processing_intensity(1.0), 1.0)

    def test_optimize_payload(self):
        """Test the optimize_payload method."""
        settings = Settings()
        payload = {"key1": "value1", "key2": "x" * 200}

        # Without mobile context, no optimization
        self.assertEqual(settings.optimize_payload(payload), payload)

        # With mobile context, optimization happens
        settings.mobile.context = {"battery_level": 50}
        optimized = settings.optimize_payload(payload)
        self.assertEqual(optimized["key1"], "value1")
        self.assertEqual(optimized["key2"], "x" * 100 + "...")

        # With optimization disabled
        settings.mobile.payload_optimization_enabled = False
        self.assertEqual(settings.optimize_payload(payload), payload)

    def test_is_offline(self):
        """Test the is_offline method."""
        settings = Settings()
        self.assertFalse(settings.is_offline())

        settings.mobile.context = {"network_state": "online"}
        settings.mobile.offline_mode_enabled = True
        self.assertFalse(settings.is_offline())

        settings.mobile.context = {"network_state": "offline"}
        self.assertTrue(settings.is_offline())

    def test_handle_offline(self):
        """Test the handle_offline method."""
        settings = Settings()
        operation = "save_data"
        data = {"id": 1, "name": "Test"}

        # Without offline mode
        result = settings.handle_offline(operation, data)
        self.assertEqual(result["status"], "online")

        # With offline mode
        settings.mobile.context = {"network_state": "offline"}
        settings.mobile.offline_mode_enabled = True
        result = settings.handle_offline(operation, data)
        self.assertEqual(result["status"], "queued")
        self.assertEqual(result["operation"], operation)
        self.assertEqual(result["data"], data)

    def test_save_load_local_state(self):
        """Test the save_local_state and load_local_state methods."""
        settings = Settings()
        state = {"key": "value"}

        # Without mobile context
        self.assertFalse(settings.save_local_state(state))
        self.assertEqual(settings.load_local_state(), {})

        # With mobile context but offline mode disabled
        settings.mobile.context = {"battery_level": 50}
        self.assertFalse(settings.save_local_state(state))
        self.assertEqual(settings.load_local_state(), {})

        # With mobile context and offline mode enabled
        settings.mobile.offline_mode_enabled = True
        self.assertTrue(settings.save_local_state(state))
        self.assertEqual(settings.load_local_state(), {"loaded": True})

    def test_format_for_mobile_ui(self):
        """Test the format_for_mobile_ui method."""
        settings = Settings()
        data = {"key1": "value1", "key2": "x" * 200}

        # Without mobile context, no formatting
        self.assertEqual(settings.format_for_mobile_ui(data), data)

        # With mobile context, formatting happens
        settings.mobile.context = {"battery_level": 50}
        formatted = settings.format_for_mobile_ui(data)
        self.assertTrue(formatted["mobile_optimized"])
        self.assertEqual(formatted["data"]["key1"], "value1")
        self.assertEqual(formatted["data"]["key2"], "x" * 100 + "...")

    def test_agent_coordination_methods(self):
        """Test the agent coordination methods."""
        settings = Settings()

        # Test get_agent_hierarchy
        hierarchy = settings.get_agent_hierarchy()
        self.assertIn("executive", hierarchy)
        self.assertIn("market", hierarchy["executive"])

        # Test get_orchestration_config
        orchestration = settings.get_orchestration_config()
        self.assertEqual(orchestration["protocol"], "event-based")

        # Test get_decision_engine_config
        decision = settings.get_decision_engine_config()
        self.assertEqual(decision["strategy"], "hierarchical")

        # Test get_pipeline_config
        pipeline = settings.get_pipeline_config()
        self.assertEqual(pipeline["max_parallel_tasks"], 5)

        # Test with features disabled
        settings.agent_coordination.hierarchical_enabled = False
        self.assertEqual(settings.get_agent_hierarchy(), {})

        settings.agent_coordination.orchestration_enabled = False
        self.assertEqual(settings.get_orchestration_config(), {})

        settings.agent_coordination.decision_engine_enabled = False
        self.assertEqual(settings.get_decision_engine_config(), {})

        settings.agent_coordination.pipeline_enabled = False
        self.assertEqual(settings.get_pipeline_config(), {})

    def test_conversational_methods(self):
        """Test the conversational interface methods."""
        settings = Settings()

        # Test format_for_nlp
        data = {"title": "Product Title", "description": "Product Description"}
        nlp_data = settings.format_for_nlp(data)
        self.assertEqual(nlp_data["nlp_data"]["title"], "Product Title")
        self.assertEqual(nlp_data["language"], "en")

        # Test route_query
        query = "What is the price of this product?"
        context = {"product_id": 123}
        route = settings.route_query(query, context)
        self.assertEqual(route["handler"], "pricing")
        self.assertEqual(route["query"], query)

        # Test personalize_response
        response = {"message": "Your order has been placed."}
        user_profile = {"name": "John", "preferences": {"notifications": "email"}}
        personalized = settings.personalize_response(response, user_profile)
        self.assertTrue("Hi John" in personalized["message"])
        self.assertTrue(personalized["personalized"])

        # Test generate_recommendations
        user_data = {
            "recent_searches": ["laptop", "smartphone", "headphones"],
            "purchase_history": ["laptop"],
        }
        recommendations = settings.generate_recommendations(user_data)
        self.assertEqual(len(recommendations), 2)
        self.assertEqual(recommendations[0]["type"], "search_based")

        # Test with features disabled
        settings.conversational.nlp_enabled = False
        self.assertEqual(settings.format_for_nlp(data), data)

        settings.conversational.query_routing_enabled = False
        self.assertEqual(settings.route_query(query, context)["handler"], "default")

        settings.conversational.personalization_enabled = False
        self.assertEqual(
            settings.personalize_response(response, user_profile), response
        )

        settings.conversational.proactive_recommendations_enabled = False
        self.assertEqual(settings.generate_recommendations(user_data), [])

    def test_technical_implementation_methods(self):
        """Test the technical implementation methods."""
        settings = Settings()

        # Test format_message
        payload = {"data": "test"}
        message = settings.format_message("test_message", payload)
        self.assertEqual(message["message_type"], "test_message")
        self.assertEqual(message["priority"], "medium")
        self.assertEqual(message["payload"], payload)

        # Test persist_state and retrieve_state
        self.assertTrue(settings.persist_state("test_key", {"data": "test"}))
        state = settings.retrieve_state("test_key")
        self.assertEqual(state["state_key"], "test_key")

        # Test secure_data
        data = {"sensitive": "data"}
        secured = settings.secure_data(data)
        self.assertTrue(secured["encrypted"])
        self.assertEqual(secured["algorithm"], "AES-256")

        # Test with features disabled
        settings.agent_coordination.correlation_id_enabled = False
        self.assertEqual(settings.format_message("test", payload), payload)

        settings.state_persistence_enabled = False
        self.assertFalse(settings.persist_state("test", {}))
        self.assertEqual(settings.retrieve_state("test"), {})

        settings.security.encryption_enabled = False
        self.assertEqual(settings.secure_data(data), data)

    def test_get_settings(self):
        """Test the get_settings function."""
        settings = get_settings()
        self.assertIsInstance(settings, Settings)

        # Test that it's cached (same instance)
        settings2 = get_settings()
        self.assertIs(settings, settings2)

    def test_get_settings_with_mobile_context(self):
        """Test the get_settings_with_mobile_context function."""
        mobile_context = {"battery_level": 50, "network_state": "online"}
        settings = get_settings_with_mobile_context(mobile_context)

        self.assertIsInstance(settings, Settings)
        self.assertEqual(settings.mobile.context, mobile_context)
        self.assertTrue(settings.is_mobile_context())

    def test_get_settings_for_agent(self):
        """Test the get_settings_for_agent function."""
        # Test executive agent settings
        executive_settings = get_settings_for_agent("executive")
        self.assertTrue(executive_settings.agent_coordination.hierarchical_enabled)
        self.assertTrue(executive_settings.agent_coordination.orchestration_enabled)
        self.assertTrue(executive_settings.agent_coordination.decision_engine_enabled)

        # Test market agent settings
        market_settings = get_settings_for_agent("market")
        self.assertTrue(market_settings.agent_coordination.hierarchical_enabled)
        self.assertFalse(market_settings.agent_coordination.orchestration_enabled)
        self.assertTrue(market_settings.agent_coordination.decision_engine_enabled)

        # Test mobile agent settings
        mobile_settings = get_settings_for_agent("mobile")
        self.assertTrue(mobile_settings.mobile.battery_optimization_enabled)
        self.assertTrue(mobile_settings.mobile.offline_mode_enabled)
        self.assertTrue(mobile_settings.mobile.payload_optimization_enabled)
        self.assertTrue(mobile_settings.mobile.ui_optimization_enabled)


if __name__ == "__main__":
    unittest.main()
