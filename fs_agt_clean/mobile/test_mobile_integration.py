"""
Integration tests for mobile features and services.

Tests the complete mobile application stack including:
- Mobile service coordinator
- Mobile features API
- Battery optimization
- Update prioritization
- Cross-platform integration
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from fs_agt_clean.mobile.lib.features.mobile_features_api import MobileFeaturesAPI
from fs_agt_clean.mobile.mobile_service_coordinator import MobileServiceCoordinator
from fs_agt_clean.mobile.models import Account


class TestMobileIntegration:
    """Integration tests for mobile features."""

    @pytest.fixture
    async def mobile_coordinator(self):
        """Create and initialize mobile service coordinator."""
        coordinator = MobileServiceCoordinator(
            {"max_retry_count": 3, "expiry_threshold": 3600}
        )
        await coordinator.initialize()
        yield coordinator
        await coordinator.cleanup()

    @pytest.fixture
    async def mobile_api(self):
        """Create and initialize mobile features API."""
        api = MobileFeaturesAPI({"max_retry_count": 3, "expiry_threshold": 3600})
        await api.initialize()
        yield api
        await api.cleanup()

    @pytest.mark.asyncio
    async def test_mobile_coordinator_initialization(self, mobile_coordinator):
        """Test mobile coordinator initialization."""
        assert mobile_coordinator.is_initialized

        status = mobile_coordinator.get_service_status()
        assert status["initialized"]
        assert "battery_optimizer" in status
        assert "update_prioritizer" in status

    @pytest.mark.asyncio
    async def test_battery_optimization_flow(self, mobile_coordinator):
        """Test battery optimization workflow."""
        # Test high battery scenario
        high_battery_data = {
            "level": 85.0,
            "charging": False,
            "temperature": 25.0,
            "voltage": 3.8,
            "current_draw": 150.0,
        }

        result = await mobile_coordinator.update_battery_status(high_battery_data)
        assert "power_mode" in result
        assert result["power_mode"] in ["performance", "balanced"]
        assert result["learning_rate"] > 0.5

        # Test low battery scenario
        low_battery_data = {
            "level": 15.0,
            "charging": False,
            "temperature": 30.0,
            "voltage": 3.5,
            "current_draw": 50.0,
        }

        result = await mobile_coordinator.update_battery_status(low_battery_data)
        assert result["power_mode"] in ["power_saver", "critical"]
        assert result["learning_rate"] <= 0.5

    @pytest.mark.asyncio
    async def test_update_prioritization_flow(self, mobile_coordinator):
        """Test update prioritization workflow."""
        account_data = {
            "account_id": "test_account",
            "marketplace": "ebay",
            "credentials": {"api_key": "test_key"},
            "settings": {"priority": "high"},
        }

        # Add high priority update
        result = await mobile_coordinator.add_market_update(
            "high_priority_update",
            "price_change",
            {"product_id": "123", "new_price": 99.99},
            account_data,
        )

        assert "update_id" in result
        assert result["priority"] == "high"
        assert "battery_cost" in result

        # Add low priority update
        result = await mobile_coordinator.add_market_update(
            "low_priority_update",
            "analytics_sync",
            {"metrics": {"views": 100}},
            account_data,
        )

        assert result["priority"] == "low"

        # Get prioritized updates
        updates = await mobile_coordinator.get_prioritized_updates()
        assert len(updates) >= 2

        # High priority should come first
        priorities = [update["priority"] for update in updates]
        high_index = priorities.index("high") if "high" in priorities else -1
        low_index = priorities.index("low") if "low" in priorities else -1

        if high_index >= 0 and low_index >= 0:
            assert high_index < low_index

    @pytest.mark.asyncio
    async def test_mobile_features_api_initialization(self, mobile_api):
        """Test mobile features API initialization."""
        assert mobile_api.is_initialized

        # Test feature status
        status = await mobile_api.get_feature_status("agent_monitoring")
        assert "feature" in status
        assert status["feature"] == "agent_monitoring"

    @pytest.mark.asyncio
    async def test_agent_monitoring_features(self, mobile_api):
        """Test agent monitoring features."""
        # Get agent monitoring data
        data = await mobile_api.get_agent_monitoring_data()
        assert "agent_status" in data
        assert "power_status" in data
        assert "service_status" in data

        # Get agent health metrics
        metrics = await mobile_api.get_agent_health_metrics()
        assert "metrics" in metrics
        assert "response_time" in metrics["metrics"]
        assert "success_rate" in metrics["metrics"]

    @pytest.mark.asyncio
    async def test_analytics_dashboard_features(self, mobile_api):
        """Test analytics dashboard features."""
        data = await mobile_api.get_analytics_dashboard_data()
        assert "business_metrics" in data
        assert "marketplace_performance" in data
        assert "trends" in data
        assert data["feature"] == "analytics"

    @pytest.mark.asyncio
    async def test_store_management_features(self, mobile_api):
        """Test store management features."""
        data = await mobile_api.get_store_management_data()
        assert "stores" in data
        assert "recent_activity" in data
        assert data["feature"] == "store_management"

        # Check store data structure
        stores = data["stores"]
        for marketplace in ["ebay", "amazon"]:
            if marketplace in stores:
                store = stores[marketplace]
                assert "status" in store
                assert "listings" in store

    @pytest.mark.asyncio
    async def test_chat_interface_features(self, mobile_api):
        """Test chat interface features."""
        # Get chat data
        data = await mobile_api.get_chat_interface_data()
        assert "active_conversations" in data
        assert "available_agents" in data
        assert data["feature"] == "chat"

        # Test sending a message
        response = await mobile_api.send_chat_message(
            "What's the current market status?", "market"
        )
        assert "message_id" in response
        assert "response" in response
        assert response["agent_type"] == "market"

    @pytest.mark.asyncio
    async def test_product_import_features(self, mobile_api):
        """Test product import features."""
        data = await mobile_api.get_product_import_data()
        assert "import_status" in data
        assert "recent_imports" in data
        assert "import_sources" in data
        assert data["feature"] == "product_import"

    @pytest.mark.asyncio
    async def test_notifications_features(self, mobile_api):
        """Test notifications features."""
        data = await mobile_api.get_notifications_data()
        assert "notifications" in data
        assert "unread_count" in data
        assert data["feature"] == "notifications"

        # Check notification structure
        notifications = data["notifications"]
        if notifications:
            notification = notifications[0]
            assert "id" in notification
            assert "type" in notification
            assert "title" in notification
            assert "priority" in notification

    @pytest.mark.asyncio
    async def test_cross_feature_integration(self, mobile_api):
        """Test integration between different mobile features."""
        # Update battery status
        battery_result = await mobile_api.update_battery_status(
            {
                "level": 25.0,
                "charging": False,
                "temperature": 28.0,
                "voltage": 3.6,
                "current_draw": 100.0,
            }
        )

        assert "power_mode" in battery_result

        # Get agent monitoring data (should reflect battery status)
        monitoring_data = await mobile_api.get_agent_monitoring_data()
        assert "power_status" in monitoring_data

        # The power mode should be consistent
        assert monitoring_data["power_status"]["mode"] == battery_result["power_mode"]

    @pytest.mark.asyncio
    async def test_error_handling(self, mobile_api):
        """Test error handling in mobile features."""
        # Test invalid feature
        result = await mobile_api.get_feature_status("invalid_feature")
        assert "error" in result
        assert "available_features" in result

        # Test chat with invalid agent type
        response = await mobile_api.send_chat_message("Test message", "invalid_agent")
        # Should still work with default response
        assert "response" in response

    @pytest.mark.asyncio
    async def test_performance_under_load(self, mobile_api):
        """Test mobile features performance under load."""
        # Simulate multiple concurrent requests
        tasks = []

        for i in range(10):
            tasks.append(mobile_api.get_agent_monitoring_data())
            tasks.append(mobile_api.get_analytics_dashboard_data())
            tasks.append(mobile_api.get_notifications_data())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that most requests succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= len(tasks) * 0.8  # At least 80% success rate

    @pytest.mark.asyncio
    async def test_mobile_service_cleanup(self, mobile_coordinator):
        """Test proper cleanup of mobile services."""
        # Add some updates
        account_data = {
            "account_id": "test_account",
            "marketplace": "ebay",
            "credentials": {},
            "settings": {},
        }

        await mobile_coordinator.add_market_update(
            "cleanup_test_update", "price_change", {"test": "data"}, account_data
        )

        # Verify update exists
        updates = await mobile_coordinator.get_prioritized_updates()
        assert len(updates) > 0

        # Cleanup should clear everything
        await mobile_coordinator.cleanup()

        # Verify cleanup
        assert not mobile_coordinator.is_initialized


if __name__ == "__main__":
    # Run basic integration test
    async def run_basic_test():
        coordinator = MobileServiceCoordinator()
        await coordinator.initialize()

        print("✅ Mobile coordinator initialized")

        # Test battery optimization
        result = await coordinator.update_battery_status(
            {
                "level": 50.0,
                "charging": False,
                "temperature": 25.0,
                "voltage": 3.7,
                "current_draw": 100.0,
            }
        )

        print(f"✅ Battery optimization: {result['power_mode']}")

        # Test mobile API
        api = MobileFeaturesAPI()
        await api.initialize()

        monitoring_data = await api.get_agent_monitoring_data()
        print(f"✅ UnifiedAgent monitoring: {len(monitoring_data)} data points")

        await api.cleanup()
        await coordinator.cleanup()

        print("✅ Mobile integration test completed successfully")

    # Run the test
    asyncio.run(run_basic_test())
