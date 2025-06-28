"""Tests for the AdvertisingUnifiedAgent."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from fs_agt_clean.agents.market.specialized.advertising_agent import AdvertisingUnifiedAgent
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.manager import AlertManager
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "api_key": "test_key",
        "marketplace_id": "ebay",
        "rate_limit": 100,
        "timeout": 30,
        "ebay_app_id": "test_app_id",
        "ebay_dev_id": "test_dev_id",
        "ebay_cert_id": "test_cert_id",
        "ebay_token": "test_token",
        "ai_service_url": "http://test-ai-service",
        "campaign_budget_limit": 1000.0,
        "optimization_interval": 3600,
    }


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager for testing."""
    manager = MagicMock(spec=ConfigManager)
    return manager


@pytest.fixture
def mock_alert_manager():
    """Mock AlertManager for testing."""
    manager = AsyncMock(spec=AlertManager)
    return manager


@pytest.fixture
def mock_battery_optimizer():
    """Mock BatteryOptimizer for testing."""
    optimizer = MagicMock(spec=BatteryOptimizer)
    return optimizer


@pytest.fixture
def advertising_agent(
    mock_config, mock_config_manager, mock_alert_manager, mock_battery_optimizer
):
    """Create AdvertisingUnifiedAgent instance for testing."""
    return AdvertisingUnifiedAgent(
        marketplace="ebay",
        config_manager=mock_config_manager,
        alert_manager=mock_alert_manager,
        battery_optimizer=mock_battery_optimizer,
        config=mock_config,
    )


class TestAdvertisingUnifiedAgent:
    """Test cases for AdvertisingUnifiedAgent."""

    @pytest.mark.asyncio
    async def test_initialization(self, advertising_agent):
        """Test agent initialization."""
        assert advertising_agent.marketplace == "ebay"
        assert advertising_agent.agent_id is not None
        assert advertising_agent.request_semaphore._value == 2
        assert advertising_agent.cache_duration == timedelta(hours=1)

    @pytest.mark.asyncio
    async def test_required_config_fields(self, advertising_agent):
        """Test required configuration fields."""
        required_fields = advertising_agent._get_required_config_fields()
        expected_fields = [
            "api_key",
            "marketplace_id",
            "rate_limit",
            "timeout",
            "ebay_app_id",
            "ebay_dev_id",
            "ebay_cert_id",
            "ebay_token",
            "ai_service_url",
            "campaign_budget_limit",
            "optimization_interval",
        ]

        for field in expected_fields:
            assert field in required_fields

    @pytest.mark.asyncio
    async def test_create_ad_campaign_success(self, advertising_agent):
        """Test successful ad campaign creation."""
        campaign_data = {
            "name": "Test Campaign",
            "budget": 100.0,
            "target_keywords": ["test", "product"],
        }

        with patch.object(advertising_agent, "_mock_ebay_call") as mock_call:
            mock_call.return_value = {"success": True, "campaignId": "campaign_123"}

            result = await advertising_agent.create_ad_campaign(campaign_data)

            assert result["success"] is True
            assert "campaignId" in result
            mock_call.assert_called_once_with("createCampaign", campaign_data)

    @pytest.mark.asyncio
    async def test_create_ad_campaign_failure(self, advertising_agent):
        """Test ad campaign creation failure."""
        campaign_data = {"name": "Test Campaign"}

        with patch.object(advertising_agent, "_mock_ebay_call") as mock_call:
            mock_call.side_effect = Exception("API Error")

            result = await advertising_agent.create_ad_campaign(campaign_data)

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_get_ad_campaigns(self, advertising_agent):
        """Test getting ad campaigns."""
        with patch.object(advertising_agent, "_mock_ebay_call") as mock_call:
            mock_call.return_value = {
                "campaigns": [
                    {"id": "campaign_1", "name": "Campaign 1"},
                    {"id": "campaign_2", "name": "Campaign 2"},
                ]
            }

            result = await advertising_agent.get_ad_campaigns()

            assert "campaigns" in result
            assert len(result["campaigns"]) == 2
            mock_call.assert_called_once_with("getCampaigns", {})

    @pytest.mark.asyncio
    async def test_update_ad_campaign(self, advertising_agent):
        """Test updating ad campaign."""
        campaign_id = "campaign_123"
        update_data = {"budget": 200.0}

        with patch.object(advertising_agent, "_mock_ebay_call") as mock_call:
            mock_call.return_value = {"success": True}

            result = await advertising_agent.update_ad_campaign(
                campaign_id, update_data
            )

            assert result["success"] is True
            expected_data = {"campaign_id": campaign_id, **update_data}
            mock_call.assert_called_once_with("updateCampaign", expected_data)

    @pytest.mark.asyncio
    async def test_create_optimized_campaign(self, advertising_agent):
        """Test creating optimized campaign."""
        listing_id = "listing_123"
        market_data = {"competition": "medium", "demand": "high"}
        budget_constraints = {"max_daily": 50.0}

        with patch.object(
            advertising_agent, "_optimize_campaign_strategy"
        ) as mock_optimize:
            with patch.object(advertising_agent, "_create_campaign") as mock_create:
                with patch.object(
                    advertising_agent, "_setup_bid_optimization"
                ) as mock_setup:
                    mock_optimize.return_value = {
                        "daily_budget": 50.0,
                        "bidding_strategy": {"type": "auto"},
                    }
                    mock_create.return_value = "campaign_123"

                    result = await advertising_agent.create_optimized_campaign(
                        listing_id, market_data, budget_constraints
                    )

                    assert result["success"] is True
                    assert result["campaign_id"] == "campaign_123"
                    assert "strategy" in result
                    assert "monitoring_task" in result

    @pytest.mark.asyncio
    async def test_optimize_existing_campaign(self, advertising_agent):
        """Test optimizing existing campaign."""
        campaign_id = "campaign_123"
        performance_data = {
            "roas": 1.5,
            "cost_per_click": 0.6,
            "impression_share": 0.05,
        }

        with patch.object(advertising_agent, "_get_campaign_data") as mock_get_data:
            with patch.object(advertising_agent, "_optimize_campaign") as mock_optimize:
                with patch.object(
                    advertising_agent, "_apply_campaign_optimizations"
                ) as mock_apply:
                    mock_get_data.return_value = {"campaign_id": campaign_id}
                    mock_optimize.return_value = {
                        "bid_adjustments": {"keyword1": 0.5},
                        "budget_adjustment": 10.0,
                    }

                    result = await advertising_agent.optimize_existing_campaign(
                        campaign_id, performance_data
                    )

                    assert result["success"] is True
                    assert result["campaign_id"] == campaign_id
                    assert "optimizations" in result

    @pytest.mark.asyncio
    async def test_should_optimize_campaign_triggers(self, advertising_agent):
        """Test campaign optimization triggers."""
        # Test low ROAS trigger
        performance_data = {"roas": 1.0}
        assert advertising_agent._should_optimize_campaign(performance_data) is True

        # Test high cost trigger
        performance_data = {"cost_per_click": 0.6}
        assert advertising_agent._should_optimize_campaign(performance_data) is True

        # Test low impressions trigger
        performance_data = {"impression_share": 0.05}
        assert advertising_agent._should_optimize_campaign(performance_data) is True

        # Test poor conversion trigger
        performance_data = {"conversion_rate": 0.005}
        assert advertising_agent._should_optimize_campaign(performance_data) is True

        # Test no optimization needed
        performance_data = {
            "roas": 3.0,
            "cost_per_click": 0.3,
            "impression_share": 0.2,
            "conversion_rate": 0.02,
        }
        assert advertising_agent._should_optimize_campaign(performance_data) is False

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, advertising_agent):
        """Test getting performance metrics."""
        campaign_id = "campaign_123"

        with patch.object(advertising_agent, "_mock_ebay_call") as mock_call:
            with patch.object(
                advertising_agent, "_process_performance_data"
            ) as mock_process:
                mock_call.return_value = {"metrics": "raw_data"}
                mock_process.return_value = {
                    "roas": 2.5,
                    "cost_per_click": 0.3,
                    "impression_share": 0.15,
                }

                result = await advertising_agent._get_performance_metrics(campaign_id)

                assert result["roas"] == 2.5
                assert result["cost_per_click"] == 0.3
                assert result["impression_share"] == 0.15

    @pytest.mark.asyncio
    async def test_create_campaign(self, advertising_agent):
        """Test campaign creation."""
        listing_id = "listing_123"
        campaign_strategy = {
            "daily_budget": 50.0,
            "bidding_strategy": {"type": "manual"},
        }

        with patch.object(advertising_agent, "_mock_ebay_call") as mock_call:
            mock_call.return_value = {"campaignId": "campaign_123"}

            result = await advertising_agent._create_campaign(
                listing_id, campaign_strategy
            )

            assert result == "campaign_123"

            # Verify the call was made with correct parameters
            call_args = mock_call.call_args[0]
            assert call_args[0] == "createCampaign"
            assert call_args[1]["targetListing"] == listing_id
            assert call_args[1]["fundingStrategy"]["dailyBudget"] == 50.0

    @pytest.mark.asyncio
    async def test_apply_campaign_optimizations(self, advertising_agent):
        """Test applying campaign optimizations."""
        campaign_id = "campaign_123"
        optimizations = {
            "bid_adjustments": {"keyword1": 0.5},
            "budget_adjustment": 10.0,
            "targeting_updates": {"location": "US"},
        }

        with patch.object(advertising_agent, "_update_bids") as mock_bids:
            with patch.object(advertising_agent, "_update_budget") as mock_budget:
                with patch.object(
                    advertising_agent, "_update_targeting"
                ) as mock_targeting:
                    await advertising_agent._apply_campaign_optimizations(
                        campaign_id, optimizations
                    )

                    mock_bids.assert_called_once_with(campaign_id, {"keyword1": 0.5})
                    mock_budget.assert_called_once_with(campaign_id, 10.0)
                    mock_targeting.assert_called_once_with(
                        campaign_id, {"location": "US"}
                    )

    @pytest.mark.asyncio
    async def test_monitor_campaign_performance(self, advertising_agent):
        """Test campaign performance monitoring."""
        campaign_id = "campaign_123"

        # Mock the monitoring loop to run only once
        with patch.object(
            advertising_agent, "_get_performance_metrics"
        ) as mock_metrics:
            with patch.object(
                advertising_agent, "_should_optimize_campaign"
            ) as mock_should_optimize:
                with patch.object(
                    advertising_agent, "optimize_existing_campaign"
                ) as mock_optimize:
                    with patch("asyncio.sleep") as mock_sleep:
                        mock_metrics.return_value = {"roas": 1.0}
                        mock_should_optimize.return_value = True
                        mock_sleep.side_effect = Exception(
                            "Stop monitoring"
                        )  # Stop the loop

                        with pytest.raises(Exception, match="Stop monitoring"):
                            await advertising_agent._monitor_campaign_performance(
                                campaign_id
                            )

                        mock_metrics.assert_called_once_with(campaign_id)
                        mock_should_optimize.assert_called_once_with({"roas": 1.0})
                        mock_optimize.assert_called_once_with(
                            campaign_id, {"roas": 1.0}
                        )
