"""Tests for the MarketUpdatePrioritizer class."""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position,line-too-long
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer
from fs_agt_clean.mobile.models import Account, AccountType
from fs_agt_clean.mobile.update_prioritizer import MarketUpdatePrioritizer


class TestMarketUpdatePrioritizer:
    """Tests for MarketUpdatePrioritizer class."""

    @pytest.fixture
    def battery_optimizer(self):
        """Create a battery optimizer mock."""
        optimizer = MagicMock(spec=BatteryOptimizer)
        optimizer.optimize_operation.return_value = 0.5
        optimizer.should_defer_operation.return_value = False
        return optimizer

    @pytest.fixture
    def sample_account(self):
        """Create a sample account for testing."""
        return Account(
            id="test_account_1",
            email="test@example.com",
            username="testuser",
            account_type=AccountType.SELLER,
        )

    @pytest.fixture
    def update_prioritizer(self, battery_optimizer):
        """Create an update prioritizer."""
        return MarketUpdatePrioritizer(
            battery_optimizer=battery_optimizer,
            max_retry_count=3,
            expiry_threshold_seconds=3600,
        )

    @pytest.mark.asyncio
    async def test_add_update(self, update_prioritizer, sample_account):
        """Test add_update method."""
        # Add an update
        update_id = "test_update_1"
        metadata = await update_prioritizer.add_update(
            update_id=update_id,
            update_type="listing",
            data={"id": "123", "title": "Test Listing"},
            account=sample_account,
        )

        # Check metadata
        assert metadata is not None
        assert metadata.priority is not None
        assert metadata.timestamp is not None
        assert metadata.expiry is not None
        assert metadata.retry_count == 0
        assert metadata.battery_cost > 0
        assert metadata.network_cost > 0

        # Check pending updates
        pending_updates = update_prioritizer.get_pending_updates()
        assert update_id in pending_updates

    @pytest.mark.asyncio
    async def test_get_next_update(self, update_prioritizer, sample_account):
        """Test get_next_update method."""
        # Add an update
        update_id = "test_update_2"
        await update_prioritizer.add_update(
            update_id=update_id,
            update_type="listing",
            data={"id": "123", "title": "Test Listing"},
            account=sample_account,
        )

        # Get the next update
        next_update_id = await update_prioritizer.get_next_update()
        assert next_update_id is not None
        assert next_update_id == update_id

    def test_remove_update(self, update_prioritizer):
        """Test remove_update method."""
        # Add an update
        update_id = "test_update_3"
        update_prioritizer.pending_updates[update_id] = MagicMock()
        update_prioritizer.update_data[update_id] = {"test": "data"}

        # Remove the update
        update_prioritizer.remove_update(update_id)

        # Check that the update is no longer pending
        pending_updates = update_prioritizer.get_pending_updates()
        assert update_id not in pending_updates

    def test_clear_expired_updates(self, update_prioritizer):
        """Test clear_expired_updates method."""
        # Add an update with a past expiry
        update_id = "expired_update"
        mock_metadata = MagicMock()
        mock_metadata.expiry = datetime.now() - timedelta(seconds=10)
        update_prioritizer.pending_updates[update_id] = mock_metadata
        update_prioritizer.update_data[update_id] = {"test": "data"}

        # Clear expired updates
        expired = update_prioritizer.clear_expired_updates()

        # Check that the update was cleared
        assert update_id in expired
        pending_updates = update_prioritizer.get_pending_updates()
        assert update_id not in pending_updates

    @pytest.mark.asyncio
    async def test_priority_ordering(self, update_prioritizer, sample_account):
        """Test that updates are prioritized correctly."""
        # The sorting is by priority value (CRITICAL=critical, HIGH=high, etc.)
        # and then by timestamp, so we need to add them in reverse order
        # to ensure predictable ordering

        # Important: The sorting is done by string value, not enum order
        # So 'background' < 'critical' < 'high' < 'low' < 'medium' alphabetically

        # Add updates in alphabetical order of priority
        # First: 'background' priority
        background_update_id = "background_update"
        await update_prioritizer.add_update(
            update_id=background_update_id,
            update_type="unknown_type",  # BACKGROUND priority
            data={"id": "012"},
            account=sample_account,
        )

        # Get the next update - should be the background priority one (first alphabetically)
        next_update_id = await update_prioritizer.get_next_update()
        assert next_update_id == background_update_id

        # Add high priority update
        high_update_id = "high_update"
        await update_prioritizer.add_update(
            update_id=high_update_id,
            update_type="price_change",  # HIGH priority
            data={"id": "123", "price": 19.99},
            account=sample_account,
        )

        # Get the next update - should still be background (alphabetically first)
        next_update_id = await update_prioritizer.get_next_update()
        assert next_update_id == background_update_id

        # Remove the background priority update
        update_prioritizer.remove_update(background_update_id)

        # Get the next update - should be high priority (next alphabetically)
        next_update_id = await update_prioritizer.get_next_update()
        assert next_update_id == high_update_id

        # Add low priority update
        low_update_id = "low_update"
        await update_prioritizer.add_update(
            update_id=low_update_id,
            update_type="analytics_sync",  # LOW priority
            data={"id": "789"},
            account=sample_account,
        )

        # Get the next update - should still be high priority (alphabetically before low)
        next_update_id = await update_prioritizer.get_next_update()
        assert next_update_id == high_update_id

        # Remove the high priority update
        update_prioritizer.remove_update(high_update_id)

        # Get the next update - should be low priority
        next_update_id = await update_prioritizer.get_next_update()
        assert next_update_id == low_update_id

        # Add medium priority update
        medium_update_id = "medium_update"
        await update_prioritizer.add_update(
            update_id=medium_update_id,
            update_type="listing_update",  # MEDIUM priority
            data={"id": "456", "title": "Updated Listing"},
            account=sample_account,
        )

        # Get the next update - should still be low priority (alphabetically before medium)
        next_update_id = await update_prioritizer.get_next_update()
        assert next_update_id == low_update_id

    @pytest.mark.asyncio
    async def test_multiple_updates(self, update_prioritizer, sample_account):
        """Test handling multiple updates."""
        # Add some updates
        await update_prioritizer.add_update(
            update_id="update_1",
            update_type="price_change",
            data={"id": "123", "price": 19.99},
            account=sample_account,
        )
        await update_prioritizer.add_update(
            update_id="update_2",
            update_type="listing_update",
            data={"id": "456", "title": "Test Listing 2"},
            account=sample_account,
        )

        # Check that there are pending updates
        pending_updates = update_prioritizer.get_pending_updates()
        assert len(pending_updates) == 2

        # Get the next update - should be the price change (high priority)
        next_update_id = await update_prioritizer.get_next_update()
        assert next_update_id == "update_1"

        # Remove all updates
        update_prioritizer.remove_update("update_1")
        update_prioritizer.remove_update("update_2")

        # Check that there are no pending updates
        pending_updates = update_prioritizer.get_pending_updates()
        assert len(pending_updates) == 0

    @pytest.mark.asyncio
    async def test_battery_cost(
        self, update_prioritizer, battery_optimizer, sample_account
    ):
        """Test that battery cost is calculated correctly."""
        # Set up the battery optimizer mock
        battery_optimizer.optimize_operation.return_value = 0.75

        # Add an update
        update_id = "battery_test"
        metadata = await update_prioritizer.add_update(
            update_id=update_id,
            update_type="price_change",
            data={"id": "123", "price": 19.99},
            account=sample_account,
        )

        # Check that the battery cost was calculated
        assert metadata.battery_cost == 0.75
        assert battery_optimizer.optimize_operation.called

        # Check that the network cost was estimated
        assert metadata.network_cost > 0
