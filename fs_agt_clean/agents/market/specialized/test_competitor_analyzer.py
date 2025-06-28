"""Tests for the CompetitorAnalyzer agent."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest

from fs_agt_clean.agents.market.specialized.competitor_analyzer import (
    CompetitorAnalyzer,
    SearchResult,
)
from fs_agt_clean.agents.market.specialized.market_types import (
    CompetitorProfile,
    PricePosition,
    ProductData,
    ThreatLevel,
)
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.manager import AlertManager
from fs_agt_clean.core.monitoring.metrics.service import MetricsCollector
from fs_agt_clean.core.vector_store.service import VectorStoreService
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "api_key": "test_key",
        "marketplace_id": "ebay",
        "rate_limit": 100,
        "timeout": 30,
        "similarity_threshold": 0.7,
        "analysis_interval": 3600,
        "threat_threshold": 0.6,
        "market_share_threshold": 0.1,
        "competitor_tracking_limit": 50,
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
def mock_vector_store():
    """Mock VectorStoreService for testing."""
    store = AsyncMock(spec=VectorStoreService)
    return store


@pytest.fixture
def mock_metric_collector():
    """Mock MetricsCollector for testing."""
    collector = AsyncMock(spec=MetricsCollector)
    return collector


@pytest.fixture
def competitor_analyzer(
    mock_config,
    mock_config_manager,
    mock_alert_manager,
    mock_battery_optimizer,
    mock_vector_store,
    mock_metric_collector,
):
    """Create CompetitorAnalyzer instance for testing."""
    return CompetitorAnalyzer(
        marketplace="ebay",
        config_manager=mock_config_manager,
        alert_manager=mock_alert_manager,
        battery_optimizer=mock_battery_optimizer,
        vector_store=mock_vector_store,
        metric_collector=mock_metric_collector,
        config=mock_config,
    )


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return ProductData(
        price=25.99,
        rating=4.5,
        reviews_count=150,
        sales_rank=1000.0,
        category_id="electronics",
        seller_id="our_seller",
        title="Test Product",
        description="Test product description",
        metadata={"brand": "TestBrand"},
    )


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return [
        SearchResult(
            score=0.85,
            metadata={
                "price": 24.99,
                "rating": 4.3,
                "reviews_count": 120,
                "sales_rank": 1200.0,
                "seller_id": "competitor_1",
                "products": ["prod1", "prod2"],
            },
        ),
        SearchResult(
            score=0.78,
            metadata={
                "price": 27.99,
                "rating": 4.7,
                "reviews_count": 200,
                "sales_rank": 800.0,
                "seller_id": "competitor_2",
                "products": ["prod3"],
            },
        ),
        SearchResult(
            score=0.72,
            metadata={
                "price": 23.99,
                "rating": 4.1,
                "reviews_count": 80,
                "sales_rank": 1500.0,
                "seller_id": "competitor_1",
                "products": ["prod4"],
            },
        ),
    ]


class TestCompetitorAnalyzer:
    """Test cases for CompetitorAnalyzer."""

    @pytest.mark.asyncio
    async def test_initialization(self, competitor_analyzer):
        """Test agent initialization."""
        assert competitor_analyzer.marketplace == "ebay"
        assert competitor_analyzer.agent_id is not None
        assert competitor_analyzer.similarity_threshold == 0.7

    @pytest.mark.asyncio
    async def test_required_config_fields(self, competitor_analyzer):
        """Test required configuration fields."""
        required_fields = competitor_analyzer._get_required_config_fields()
        expected_fields = [
            "api_key",
            "marketplace_id",
            "rate_limit",
            "timeout",
            "similarity_threshold",
            "analysis_interval",
            "threat_threshold",
            "market_share_threshold",
            "competitor_tracking_limit",
        ]

        for field in expected_fields:
            assert field in required_fields

    @pytest.mark.asyncio
    async def test_analyze_competitors_success(
        self, competitor_analyzer, sample_product_data, sample_search_results
    ):
        """Test successful competitor analysis."""
        with patch.object(competitor_analyzer, "_create_product_vector") as mock_vector:
            with patch.object(
                competitor_analyzer, "_find_similar_products"
            ) as mock_find:
                with patch.object(
                    competitor_analyzer, "_group_by_competitor"
                ) as mock_group:
                    mock_vector.return_value = np.array(
                        [1.0, 2.0, 3.0, 4.0], dtype=np.float32
                    )
                    mock_find.return_value = sample_search_results
                    mock_group.return_value = {
                        "competitor_1": sample_search_results[:2],
                        "competitor_2": sample_search_results[2:],
                    }

                    result = await competitor_analyzer.analyze_competitors(
                        "electronics", sample_product_data
                    )

                    assert len(result) == 2
                    assert all(
                        isinstance(profile, CompetitorProfile) for profile in result
                    )
                    # Results should be sorted by threat level and similarity
                    assert result[0].similarity_score >= result[1].similarity_score

    @pytest.mark.asyncio
    async def test_create_product_vector(
        self, competitor_analyzer, sample_product_data
    ):
        """Test product vector creation."""
        vector = competitor_analyzer._create_product_vector(sample_product_data)

        assert isinstance(vector, np.ndarray)
        assert vector.dtype == np.float32
        assert len(vector) == 4
        # Vector should be normalized
        assert np.isclose(np.linalg.norm(vector), 1.0)

    @pytest.mark.asyncio
    async def test_find_similar_products(self, competitor_analyzer):
        """Test finding similar products."""
        product_vector = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        category_id = "electronics"

        mock_results = [
            {"score": 0.85, "metadata": {"seller_id": "comp1", "price": 25.0}},
            {
                "score": 0.65,
                "metadata": {"seller_id": "comp2", "price": 30.0},
            },  # Below threshold
            {"score": 0.75, "metadata": {"seller_id": "comp3", "price": 20.0}},
        ]

        competitor_analyzer.vector_store.search.return_value = mock_results

        results = await competitor_analyzer._find_similar_products(
            product_vector, category_id
        )

        # Should filter out results below similarity threshold (0.7)
        assert len(results) == 2
        assert all(result["score"] >= 0.7 for result in results)

    @pytest.mark.asyncio
    async def test_group_by_competitor(
        self, competitor_analyzer, sample_search_results
    ):
        """Test grouping products by competitor."""
        grouped = competitor_analyzer._group_by_competitor(sample_search_results)

        assert len(grouped) == 2
        assert "competitor_1" in grouped
        assert "competitor_2" in grouped
        assert len(grouped["competitor_1"]) == 2  # Two products from competitor_1
        assert len(grouped["competitor_2"]) == 1  # One product from competitor_2

    @pytest.mark.asyncio
    async def test_analyze_competitor(self, competitor_analyzer, sample_product_data):
        """Test analyzing individual competitor."""
        competitor_products = [
            SearchResult(
                score=0.8,
                metadata={
                    "price": 20.0,  # Lower than our price (25.99)
                    "rating": 4.7,  # Higher than our rating (4.5)
                    "sales_count": 200,  # Higher than our reviews (150)
                    "products": ["p1", "p2"],
                },
            )
        ]

        profile = competitor_analyzer._analyze_competitor(
            "competitor_1", competitor_products, sample_product_data
        )

        assert isinstance(profile, CompetitorProfile)
        assert profile.competitor_id == "competitor_1"
        assert profile.similarity_score == 0.8
        assert profile.price_position == PricePosition.LOWER
        assert "competitive_pricing" in profile.strengths
        assert "better_ratings" in profile.strengths
        assert "higher_sales_volume" in profile.strengths

    @pytest.mark.asyncio
    async def test_calculate_threat_level(self, competitor_analyzer):
        """Test threat level calculation."""
        # High threat scenario
        threat_level = competitor_analyzer._calculate_threat_level(
            similarity_score=0.9, market_share=0.3, strength_count=4
        )
        assert threat_level == ThreatLevel.HIGH

        # Medium threat scenario
        threat_level = competitor_analyzer._calculate_threat_level(
            similarity_score=0.6, market_share=0.2, strength_count=2
        )
        assert threat_level == ThreatLevel.MEDIUM

        # Low threat scenario
        threat_level = competitor_analyzer._calculate_threat_level(
            similarity_score=0.3, market_share=0.1, strength_count=1
        )
        assert threat_level == ThreatLevel.LOW

    @pytest.mark.asyncio
    async def test_get_competitor_insights_empty(self, competitor_analyzer):
        """Test getting insights with no competitors."""
        insights = await competitor_analyzer.get_competitor_insights([])

        assert insights["insights"] == []
        assert insights["recommendations"] == []

    @pytest.mark.asyncio
    async def test_get_competitor_insights_with_data(self, competitor_analyzer):
        """Test getting insights with competitor data."""
        competitors = [
            CompetitorProfile(
                competitor_id="comp1",
                similarity_score=0.8,
                price_position=PricePosition.LOWER,
                market_share=0.3,
                strengths=["competitive_pricing"],
                weaknesses=[],
                threat_level=ThreatLevel.HIGH,
                last_updated=datetime.now(timezone.utc),
            ),
            CompetitorProfile(
                competitor_id="comp2",
                similarity_score=0.7,
                price_position=PricePosition.LOWER,
                market_share=0.4,
                strengths=["competitive_pricing"],
                weaknesses=[],
                threat_level=ThreatLevel.HIGH,
                last_updated=datetime.now(timezone.utc),
            ),
        ]

        insights = await competitor_analyzer.get_competitor_insights(competitors)

        assert len(insights["insights"]) > 0
        assert len(insights["recommendations"]) > 0
        assert insights["competitor_count"] == 2
        assert "high-threat competitors" in insights["insights"][0]
        assert insights["average_threat_level"] == "high"

    @pytest.mark.asyncio
    async def test_calculate_average_threat_level(self, competitor_analyzer):
        """Test average threat level calculation."""
        # Test with high threat average
        profiles = [
            CompetitorProfile(
                competitor_id="comp1",
                similarity_score=0.8,
                price_position=PricePosition.LOWER,
                market_share=0.3,
                strengths=[],
                weaknesses=[],
                threat_level=ThreatLevel.HIGH,
                last_updated=datetime.now(timezone.utc),
            ),
            CompetitorProfile(
                competitor_id="comp2",
                similarity_score=0.7,
                price_position=PricePosition.SIMILAR,
                market_share=0.2,
                strengths=[],
                weaknesses=[],
                threat_level=ThreatLevel.HIGH,
                last_updated=datetime.now(timezone.utc),
            ),
        ]

        avg_threat = competitor_analyzer._calculate_average_threat_level(profiles)
        assert avg_threat == "high"

        # Test with medium threat average
        profiles[1].threat_level = ThreatLevel.MEDIUM
        avg_threat = competitor_analyzer._calculate_average_threat_level(profiles)
        assert avg_threat == "high"  # Still high due to one high threat

        # Test with low threat average
        profiles = [
            CompetitorProfile(
                competitor_id="comp1",
                similarity_score=0.5,
                price_position=PricePosition.HIGHER,
                market_share=0.1,
                strengths=[],
                weaknesses=[],
                threat_level=ThreatLevel.LOW,
                last_updated=datetime.now(timezone.utc),
            )
        ]
        avg_threat = competitor_analyzer._calculate_average_threat_level(profiles)
        assert avg_threat == "low"

    @pytest.mark.asyncio
    async def test_price_position_determination(
        self, competitor_analyzer, sample_product_data
    ):
        """Test price position determination logic."""
        # Test lower price position
        competitor_products = [
            SearchResult(
                score=0.8,
                metadata={
                    "price": 20.0,
                    "rating": 4.0,
                    "sales_count": 100,
                    "products": ["p1"],
                },
            )
        ]
        profile = competitor_analyzer._analyze_competitor(
            "comp1", competitor_products, sample_product_data
        )
        assert profile.price_position == PricePosition.LOWER

        # Test higher price position
        competitor_products[0]["metadata"]["price"] = 35.0
        profile = competitor_analyzer._analyze_competitor(
            "comp1", competitor_products, sample_product_data
        )
        assert profile.price_position == PricePosition.HIGHER

        # Test similar price position
        competitor_products[0]["metadata"]["price"] = 26.0
        profile = competitor_analyzer._analyze_competitor(
            "comp1", competitor_products, sample_product_data
        )
        assert profile.price_position == PricePosition.SIMILAR

    @pytest.mark.asyncio
    async def test_metrics_collection(self, competitor_analyzer, sample_product_data):
        """Test metrics collection during analysis."""
        with patch.object(competitor_analyzer, "_create_product_vector") as mock_vector:
            with patch.object(
                competitor_analyzer, "_find_similar_products"
            ) as mock_find:
                mock_vector.return_value = np.array(
                    [1.0, 2.0, 3.0, 4.0], dtype=np.float32
                )
                mock_find.return_value = []

                await competitor_analyzer.analyze_competitors(
                    "electronics", sample_product_data
                )

                # Verify metrics were recorded
                competitor_analyzer.metric_collector.record_latency.assert_called()

    @pytest.mark.asyncio
    async def test_error_handling(self, competitor_analyzer, sample_product_data):
        """Test error handling in competitor analysis."""
        with patch.object(competitor_analyzer, "_create_product_vector") as mock_vector:
            mock_vector.side_effect = Exception("Vector creation failed")

            with pytest.raises(Exception, match="Vector creation failed"):
                await competitor_analyzer.analyze_competitors(
                    "electronics", sample_product_data
                )

            # Verify error was recorded
            competitor_analyzer.metric_collector.record_error.assert_called_once()
