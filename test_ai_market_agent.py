#!/usr/bin/env python3
"""
Test AI Market Agent Implementation
AGENT_CONTEXT: Validate real AI-powered market analysis
AGENT_PRIORITY: Test Phase 2 agent implementation
AGENT_PATTERN: AI integration testing, marketplace data validation
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict

import pytest
import pytest_asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAIMarketAgent:
    """Test the AI-powered Market Agent implementation."""

    @pytest_asyncio.fixture
    async def ai_market_agent(self):
        """Create AI Market Agent instance for testing."""
        try:
            from fs_agt_clean.agents.market.ai_market_agent import AIMarketAgent

            agent = AIMarketAgent(agent_id="test_ai_market_agent")
            await agent.initialize()
            return agent
        except ImportError as e:
            logger.warning(f"AI Market Agent not available: {e}")
            return None

    @pytest.fixture
    def sample_market_request(self):
        """Create sample market analysis request."""
        from fs_agt_clean.agents.market.ai_market_agent import MarketAnalysisRequest

        return MarketAnalysisRequest(
            product_query="wireless bluetooth headphones",
            target_marketplace="all",
            analysis_depth="standard",
            include_competitors=True,
            price_range=(20.0, 100.0),
        )

    @pytest.mark.asyncio
    async def test_ai_market_agent_initialization(self, ai_market_agent):
        """Test AI Market Agent initialization."""
        if not ai_market_agent:
            pytest.skip("AI Market Agent not available")

        assert ai_market_agent is not None
        assert ai_market_agent.agent_id == "test_ai_market_agent"
        assert hasattr(ai_market_agent, "ai_client")
        assert hasattr(ai_market_agent, "ebay_client")
        assert hasattr(ai_market_agent, "amazon_client")

        logger.info("✅ AI Market Agent initialization test passed")

    @pytest.mark.asyncio
    async def test_market_analysis_basic(self, ai_market_agent, sample_market_request):
        """Test basic market analysis functionality."""
        if not ai_market_agent:
            pytest.skip("AI Market Agent not available")

        try:
            result = await ai_market_agent.analyze_market(sample_market_request)

            # Validate result structure
            assert result is not None
            assert hasattr(result, "product_query")
            assert hasattr(result, "analysis_timestamp")
            assert hasattr(result, "market_summary")
            assert hasattr(result, "pricing_recommendation")
            assert hasattr(result, "competitor_analysis")
            assert hasattr(result, "confidence_score")

            # Validate content
            assert result.product_query == sample_market_request.product_query
            assert isinstance(result.analysis_timestamp, datetime)
            assert isinstance(result.market_summary, str)
            assert isinstance(result.pricing_recommendation, dict)
            assert isinstance(result.competitor_analysis, list)
            assert 0.0 <= result.confidence_score <= 1.0

            logger.info(
                f"✅ Market analysis completed with confidence: {result.confidence_score}"
            )
            logger.info(f"   Market summary: {result.market_summary[:100]}...")

        except Exception as e:
            logger.error(f"Market analysis test failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_marketplace_data_gathering(
        self, ai_market_agent, sample_market_request
    ):
        """Test marketplace data gathering functionality."""
        if not ai_market_agent:
            pytest.skip("AI Market Agent not available")

        try:
            # Test the internal data gathering method
            marketplace_data = await ai_market_agent._gather_marketplace_data(
                sample_market_request
            )

            # Validate data structure
            assert isinstance(marketplace_data, dict)
            assert "ebay_listings" in marketplace_data
            assert "amazon_listings" in marketplace_data
            assert "competitors" in marketplace_data
            assert "price_range" in marketplace_data

            # Validate data types
            assert isinstance(marketplace_data["ebay_listings"], list)
            assert isinstance(marketplace_data["amazon_listings"], list)
            assert isinstance(marketplace_data["competitors"], list)
            assert isinstance(marketplace_data["price_range"], dict)

            logger.info(f"✅ Marketplace data gathering test passed")
            logger.info(f"   eBay listings: {len(marketplace_data['ebay_listings'])}")
            logger.info(
                f"   Amazon listings: {len(marketplace_data['amazon_listings'])}"
            )
            logger.info(f"   Competitors: {len(marketplace_data['competitors'])}")

        except Exception as e:
            logger.error(f"Marketplace data gathering test failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_ai_analysis_functionality(
        self, ai_market_agent, sample_market_request
    ):
        """Test AI analysis functionality."""
        if not ai_market_agent:
            pytest.skip("AI Market Agent not available")

        try:
            # Create mock marketplace data
            mock_marketplace_data = {
                "ebay_listings": [
                    {
                        "title": "Test Product 1",
                        "current_price": {"amount": 29.99},
                        "marketplace": "ebay",
                    },
                    {
                        "title": "Test Product 2",
                        "current_price": {"amount": 34.99},
                        "marketplace": "ebay",
                    },
                ],
                "amazon_listings": [
                    {
                        "title": "Test Product 3",
                        "current_price": {"amount": 39.99},
                        "marketplace": "amazon",
                    }
                ],
                "competitors": [
                    {"title": "Competitor 1", "price": 29.99, "marketplace": "ebay"},
                    {"title": "Competitor 2", "price": 34.99, "ebay": "ebay"},
                    {"title": "Competitor 3", "price": 39.99, "marketplace": "amazon"},
                ],
                "price_range": {
                    "min": 29.99,
                    "max": 39.99,
                    "average": 34.99,
                    "count": 3,
                },
            }

            # Test AI analysis
            ai_analysis = await ai_market_agent._perform_ai_analysis(
                sample_market_request, mock_marketplace_data
            )

            # Validate analysis structure
            assert isinstance(ai_analysis, dict)
            assert "market_summary" in ai_analysis
            assert "confidence" in ai_analysis
            assert "actions" in ai_analysis

            # Validate content types
            assert isinstance(ai_analysis["market_summary"], str)
            assert isinstance(ai_analysis["confidence"], (int, float))
            assert isinstance(ai_analysis["actions"], list)

            logger.info(f"✅ AI analysis functionality test passed")
            logger.info(f"   Confidence: {ai_analysis['confidence']}")
            logger.info(f"   Actions: {len(ai_analysis['actions'])}")

        except Exception as e:
            logger.error(f"AI analysis functionality test failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_pricing_recommendations(
        self, ai_market_agent, sample_market_request
    ):
        """Test pricing recommendation generation."""
        if not ai_market_agent:
            pytest.skip("AI Market Agent not available")

        try:
            # Create mock data
            mock_marketplace_data = {
                "price_range": {
                    "min": 25.00,
                    "max": 45.00,
                    "average": 35.00,
                    "count": 10,
                }
            }

            mock_ai_analysis = {
                "confidence": 0.8,
                "pricing_insights": {"reasoning": "Based on competitive analysis"},
            }

            # Test pricing recommendations
            pricing_rec = await ai_market_agent._generate_pricing_recommendations(
                sample_market_request, mock_marketplace_data, mock_ai_analysis
            )

            # Validate recommendation structure
            assert isinstance(pricing_rec, dict)
            assert "recommended_price" in pricing_rec
            assert "price_strategy" in pricing_rec
            assert "confidence" in pricing_rec
            assert "reasoning" in pricing_rec

            # Validate recommendation content
            if pricing_rec["recommended_price"]:
                assert isinstance(pricing_rec["recommended_price"], (int, float))
                assert pricing_rec["recommended_price"] > 0

            assert isinstance(pricing_rec["price_strategy"], str)
            assert isinstance(pricing_rec["confidence"], (int, float))
            assert isinstance(pricing_rec["reasoning"], str)

            logger.info(f"✅ Pricing recommendations test passed")
            logger.info(
                f"   Recommended price: ${pricing_rec.get('recommended_price', 'N/A')}"
            )
            logger.info(f"   Strategy: {pricing_rec['price_strategy']}")

        except Exception as e:
            logger.error(f"Pricing recommendations test failed: {e}")
            raise

    @pytest.mark.asyncio
    async def test_caching_functionality(self, ai_market_agent, sample_market_request):
        """Test analysis caching functionality."""
        if not ai_market_agent:
            pytest.skip("AI Market Agent not available")

        try:
            # First analysis (should be fresh)
            result1 = await ai_market_agent.analyze_market(sample_market_request)

            # Second analysis (should use cache)
            result2 = await ai_market_agent.analyze_market(sample_market_request)

            # Validate both results exist
            assert result1 is not None
            assert result2 is not None

            # Results should be similar (from cache)
            assert result1.product_query == result2.product_query

            logger.info("✅ Caching functionality test passed")

        except Exception as e:
            logger.error(f"Caching functionality test failed: {e}")
            raise

    def test_fallback_analysis(self, ai_market_agent, sample_market_request):
        """Test fallback analysis when AI is unavailable."""
        if not ai_market_agent:
            pytest.skip("AI Market Agent not available")

        try:
            # Test fallback analysis creation
            fallback_result = ai_market_agent._create_fallback_analysis(
                sample_market_request
            )

            # Validate fallback structure
            assert fallback_result is not None
            assert hasattr(fallback_result, "product_query")
            assert hasattr(fallback_result, "market_summary")
            assert hasattr(fallback_result, "pricing_recommendation")
            assert hasattr(fallback_result, "confidence_score")

            # Validate fallback content
            assert fallback_result.product_query == sample_market_request.product_query
            assert isinstance(fallback_result.market_summary, str)
            assert isinstance(fallback_result.pricing_recommendation, dict)
            assert 0.0 <= fallback_result.confidence_score <= 1.0

            logger.info("✅ Fallback analysis test passed")

        except Exception as e:
            logger.error(f"Fallback analysis test failed: {e}")
            raise


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
