"""Tests for the TrendDetector agent."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from fs_agt_clean.agents.market.specialized.trend_detector import (
    TrendAnalysisData,
    TrendDetector,
)
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.events.constants import EventType
from fs_agt_clean.core.monitoring.alerts.manager import AlertManager
from fs_agt_clean.core.monitoring.alerts.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from fs_agt_clean.core.monitoring.metric_types import MetricType
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "api_key": "test_key",
        "marketplace_id": "ebay",
        "rate_limit": 100,
        "timeout": 30,
        "trend_threshold": 0.6,
        "analysis_interval": 3600,
        "confidence_threshold": 0.7,
        "data_window_size": 24,
        "seasonal_adjustment": True,
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
def trend_detector(
    mock_config, mock_config_manager, mock_alert_manager, mock_battery_optimizer
):
    """Create TrendDetector instance for testing."""
    return TrendDetector(
        marketplace="ebay",
        config_manager=mock_config_manager,
        alert_manager=mock_alert_manager,
        battery_optimizer=mock_battery_optimizer,
        config=mock_config,
    )


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "price_history": [10.0, 10.5, 11.0, 11.5, 12.0],
        "volume_history": [100, 110, 120, 130, 140],
        "category": "electronics",
        "timestamp": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_trend_data():
    """Sample trend data for testing."""
    return TrendAnalysisData(
        trend_type="upward_trend",
        start_time=datetime.now(timezone.utc) - timedelta(hours=24),
        end_time=datetime.now(timezone.utc),
        confidence=0.8,
        metadata={"price_change": 0.2, "volume_change": 0.4},
    )


class TestTrendDetector:
    """Test cases for TrendDetector."""

    @pytest.mark.asyncio
    async def test_initialization(self, trend_detector):
        """Test agent initialization."""
        assert trend_detector.marketplace == "ebay"
        assert trend_detector.agent_id is not None
        assert trend_detector.trends == []

    @pytest.mark.asyncio
    async def test_required_config_fields(self, trend_detector):
        """Test required configuration fields."""
        required_fields = trend_detector._get_required_config_fields()
        expected_fields = [
            "api_key",
            "marketplace_id",
            "rate_limit",
            "timeout",
            "trend_threshold",
            "analysis_interval",
            "confidence_threshold",
            "data_window_size",
            "seasonal_adjustment",
        ]

        for field in expected_fields:
            assert field in required_fields

    @pytest.mark.asyncio
    async def test_analyze_trend_success(self, trend_detector, sample_market_data):
        """Test successful trend analysis."""
        result = await trend_detector.analyze_trend(sample_market_data)

        assert result is not None
        assert isinstance(result, TrendAnalysisData)
        assert result.trend_type in [
            "bullish_momentum",
            "bearish_momentum",
            "sideways_consolidation",
            "upward_trend",
            "downward_trend",
            "neutral",
        ]
        assert 0 <= result.confidence <= 1

    @pytest.mark.asyncio
    async def test_analyze_trend_insufficient_data(self, trend_detector):
        """Test trend analysis with insufficient data."""
        market_data = {"price_history": [10.0], "volume_history": []}

        result = await trend_detector.analyze_trend(market_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_trend_below_threshold(self, trend_detector):
        """Test trend analysis below confidence threshold."""
        # Set high threshold
        trend_detector.config["trend_threshold"] = 0.9

        market_data = {
            "price_history": [10.0, 10.01, 10.02],  # Very small changes
            "volume_history": [100, 101, 102],
        }

        result = await trend_detector.analyze_trend(market_data)

        # Should return None due to low confidence
        assert result is None

    @pytest.mark.asyncio
    async def test_detect_trend_types(self, trend_detector):
        """Test different trend type detection."""
        # Test bullish momentum
        price_data = [10.0, 11.0, 12.0]
        volume_data = [100, 120, 140]
        trend_type = trend_detector._detect_trend_type(price_data, volume_data)
        assert trend_type == "bullish_momentum"

        # Test bearish momentum
        price_data = [12.0, 11.0, 10.0]
        volume_data = [100, 120, 140]
        trend_type = trend_detector._detect_trend_type(price_data, volume_data)
        assert trend_type == "bearish_momentum"

        # Test sideways consolidation
        price_data = [10.0, 10.01, 10.02]
        volume_data = [100, 101, 102]
        trend_type = trend_detector._detect_trend_type(price_data, volume_data)
        assert trend_type == "sideways_consolidation"

    @pytest.mark.asyncio
    async def test_calculate_trend_confidence(self, trend_detector):
        """Test trend confidence calculation."""
        # Test with stable prices (low volatility)
        price_data = [10.0, 10.1, 10.2, 10.3, 10.4]
        volume_data = [100, 110, 120, 130, 140]
        confidence = trend_detector._calculate_trend_confidence(price_data, volume_data)

        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be reasonably confident with stable trend

        # Test with volatile prices
        price_data = [10.0, 15.0, 8.0, 12.0, 9.0]
        volume_data = [100, 110, 120, 130, 140]
        confidence = trend_detector._calculate_trend_confidence(price_data, volume_data)

        assert 0 <= confidence <= 1
        assert confidence < 0.5  # Should be less confident with volatile data

    @pytest.mark.asyncio
    async def test_get_historical_trends(self, trend_detector, sample_trend_data):
        """Test getting historical trends."""
        # Add some trends to the detector
        trend_detector.trends = [sample_trend_data]

        # Test 24h timeframe
        trends_24h = await trend_detector.get_historical_trends("24h")
        assert len(trends_24h) == 1

        # Test 1h timeframe (should be empty since trend is older)
        trends_1h = await trend_detector.get_historical_trends("1h")
        assert len(trends_1h) == 0

    @pytest.mark.asyncio
    async def test_handle_event_data_acquired(self, trend_detector, sample_market_data):
        """Test handling DATA_ACQUIRED event."""
        event = {"type": EventType.DATA_ACQUIRED.value, "data": sample_market_data}

        with patch.object(trend_detector, "analyze_trend") as mock_analyze:
            with patch.object(trend_detector, "_send_trend_alert") as mock_alert:
                mock_trend = TrendAnalysisData(
                    trend_type="upward_trend",
                    start_time=datetime.now(timezone.utc),
                    end_time=datetime.now(timezone.utc),
                    confidence=0.8,
                    metadata={},
                )
                mock_analyze.return_value = mock_trend

                await trend_detector._handle_event(event)

                mock_analyze.assert_called_once_with(sample_market_data)
                mock_alert.assert_called_once_with(mock_trend)
                assert len(trend_detector.trends) == 1

    @pytest.mark.asyncio
    async def test_send_trend_alert(self, trend_detector, sample_trend_data):
        """Test sending trend alert."""
        with patch.object(
            trend_detector.alert_manager, "process_alert"
        ) as mock_process:
            await trend_detector._send_trend_alert(sample_trend_data)

            mock_process.assert_called_once()
            alert_call = mock_process.call_args[0][0]
            assert isinstance(alert_call, Alert)
            assert alert_call.severity == AlertSeverity.LOW
            assert alert_call.alert_type == AlertType.CUSTOM
            assert "upward_trend" in alert_call.message
            assert alert_call.metric_type == MetricType.GAUGE

    @pytest.mark.asyncio
    async def test_parse_timeframe(self, trend_detector):
        """Test timeframe parsing."""
        now = datetime.now(timezone.utc)

        # Test 1 hour
        cutoff_1h = trend_detector._parse_timeframe("1h")
        assert (now - cutoff_1h).total_seconds() == pytest.approx(3600, rel=1e-2)

        # Test 24 hours
        cutoff_24h = trend_detector._parse_timeframe("24h")
        assert (now - cutoff_24h).total_seconds() == pytest.approx(86400, rel=1e-2)

        # Test 7 days
        cutoff_7d = trend_detector._parse_timeframe("7d")
        assert (now - cutoff_7d).total_seconds() == pytest.approx(604800, rel=1e-2)

        # Test default (unknown timeframe)
        cutoff_default = trend_detector._parse_timeframe("unknown")
        assert (now - cutoff_default).total_seconds() == pytest.approx(86400, rel=1e-2)

    @pytest.mark.asyncio
    async def test_get_trend_summary(self, trend_detector):
        """Test getting trend summary."""
        # Add multiple trends
        trends = [
            TrendAnalysisData(
                trend_type="upward_trend",
                start_time=datetime.now(timezone.utc) - timedelta(hours=1),
                end_time=datetime.now(timezone.utc),
                confidence=0.8,
                metadata={},
            ),
            TrendAnalysisData(
                trend_type="upward_trend",
                start_time=datetime.now(timezone.utc) - timedelta(hours=2),
                end_time=datetime.now(timezone.utc),
                confidence=0.7,
                metadata={},
            ),
            TrendAnalysisData(
                trend_type="downward_trend",
                start_time=datetime.now(timezone.utc) - timedelta(hours=3),
                end_time=datetime.now(timezone.utc),
                confidence=0.6,
                metadata={},
            ),
        ]
        trend_detector.trends = trends

        summary = await trend_detector.get_trend_summary()

        assert summary["total_trends"] == 3
        assert summary["trend_distribution"]["upward_trend"] == 2
        assert summary["trend_distribution"]["downward_trend"] == 1
        assert summary["average_confidence"] == pytest.approx(0.7, rel=1e-2)
        assert summary["dominant_trend"] == "upward_trend"
        assert "last_updated" in summary

    @pytest.mark.asyncio
    async def test_calculate_price_change(self, trend_detector):
        """Test price change calculation."""
        # Test positive change
        price_data = [10.0, 12.0]
        change = trend_detector._calculate_price_change(price_data)
        assert change == pytest.approx(0.2, rel=1e-2)

        # Test negative change
        price_data = [12.0, 10.0]
        change = trend_detector._calculate_price_change(price_data)
        assert change == pytest.approx(-0.167, rel=1e-2)

        # Test insufficient data
        price_data = [10.0]
        change = trend_detector._calculate_price_change(price_data)
        assert change == 0.0

    @pytest.mark.asyncio
    async def test_calculate_volume_change(self, trend_detector):
        """Test volume change calculation."""
        # Test positive change
        volume_data = [100, 120]
        change = trend_detector._calculate_volume_change(volume_data)
        assert change == pytest.approx(0.2, rel=1e-2)

        # Test empty data
        volume_data = []
        change = trend_detector._calculate_volume_change(volume_data)
        assert change == 0.0

    @pytest.mark.asyncio
    async def test_trend_analysis_data_to_dict(self, sample_trend_data):
        """Test TrendAnalysisData to_dict conversion."""
        result = sample_trend_data.to_dict()

        assert result["trend_type"] == "upward_trend"
        assert result["confidence"] == 0.8
        assert "start_time" in result
        assert "end_time" in result
        assert "metadata" in result
