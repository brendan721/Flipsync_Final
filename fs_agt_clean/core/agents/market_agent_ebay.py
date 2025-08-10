"""
Market Agent with eBay Integration for 4+1 Architecture

This agent specializes in eBay marketplace analysis and decision-making,
integrating with the stored OAuth tokens to provide real-time market insights.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from fs_agt_clean.agents.base_autonomous_agent import (
    BaseAutonomousAgent,
    AutonomousAgentState,
)
from fs_agt_clean.core.coordination.decision.pipeline import StandardDecisionPipeline
from fs_agt_clean.services.marketplace.ebay_agent_service import (
    get_ebay_agent_service,
    EbayListingData,
    EbayMarketData,
)

logger = logging.getLogger(__name__)


class MarketAgentEbay(BaseAutonomousAgent):
    """
    Market Agent specialized for eBay marketplace analysis.

    Provides autonomous market research, pricing analysis, and opportunity
    identification using real eBay marketplace data.
    """

    def __init__(self, agent_id: str = "market_agent_ebay"):
        super().__init__(
            agent_id=agent_id,
            agent_type="market",
            optimization_config={
                "algorithm": "market_optimization",
                "performance_target": 0.95,
                "decision_timeout_ms": 1000,
            },
        )
        self.ebay_service = get_ebay_agent_service()

        # Custom capabilities for eBay integration
        self.capabilities = [
            "market_analysis",
            "price_research",
            "competition_analysis",
            "trend_identification",
            "opportunity_detection",
        ]

    async def initialize(self) -> bool:
        """Initialize the Market Agent."""
        try:
            logger.info(
                f"🏪 Initializing Market Agent with eBay integration: {self.agent_id}"
            )

            # Initialize base autonomous agent components
            base_init_success = await super().initialize_async()
            if not base_init_success:
                logger.warning(
                    "Base agent initialization failed, continuing with limited functionality"
                )

            # Test eBay service availability
            # Note: We'll need a user_id to test actual API calls

            # Set state using the proper enum
            self.state = AutonomousAgentState.IDLE  # Use IDLE as the active state
            logger.info(f"✅ Market Agent initialized successfully: {self.agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Market Agent {self.agent_id}: {e}")
            self.state = AutonomousAgentState.ERROR
            return False

    async def process_decision_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process market analysis decision requests.

        Supports various market analysis tasks using eBay data.
        """
        try:
            decision_type = request.get("decision_type", "market_analysis")
            user_id = request.get("user_id")

            if not user_id:
                return {
                    "success": False,
                    "error": "user_id required for eBay market analysis",
                    "agent_id": self.agent_id,
                }

            # Use StandardDecisionPipeline for consistent decision processing
            pipeline_input = {
                "request": request,
                "agent_capabilities": self.capabilities,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if decision_type == "market_analysis":
                result = await self._analyze_market(request)
            elif decision_type == "price_research":
                result = await self._research_pricing(request)
            elif decision_type == "competition_analysis":
                result = await self._analyze_competition(request)
            elif decision_type == "opportunity_detection":
                result = await self._detect_opportunities(request)
            else:
                result = {
                    "success": False,
                    "error": f"Unsupported decision type: {decision_type}",
                    "agent_id": self.agent_id,
                }

            # Process through decision pipeline
            pipeline_result = await self.decision_pipeline.process_decision(
                input_data=pipeline_input, decision_logic=lambda x: result
            )

            return {
                **result,
                "pipeline_metrics": pipeline_result.get("metrics", {}),
                "processing_time_ms": pipeline_result.get("processing_time_ms", 0),
            }

        except Exception as e:
            logger.error(f"Market Agent decision processing failed: {e}")
            return {"success": False, "error": str(e), "agent_id": self.agent_id}

    async def _analyze_market(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market conditions for a specific product or category."""
        try:
            user_id = request["user_id"]
            query = request.get("query", "")
            category_id = request.get("category_id")
            keywords = request.get("keywords", [query] if query else ["electronics"])

            logger.info(f"🔍 Analyzing market for query: {query} (user: {user_id})")

            # Get market data from eBay
            if category_id:
                market_data = await self.ebay_service.analyze_market_trends(
                    user_id=user_id, category_id=category_id, keywords=keywords
                )
            else:
                # Search marketplace for general analysis
                listings = await self.ebay_service.search_marketplace(
                    user_id=user_id, query=query, limit=50
                )

                # Create market data from search results
                prices = [listing.price for listing in listings if listing.price > 0]
                market_data = EbayMarketData(
                    category_id="general",
                    average_price=sum(prices) / len(prices) if prices else 0,
                    price_range={
                        "min": min(prices) if prices else 0,
                        "max": max(prices) if prices else 0,
                        "median": sorted(prices)[len(prices) // 2] if prices else 0,
                    },
                    total_listings=len(listings),
                    sold_listings=0,
                    success_rate=0.0,
                    trending_keywords=keywords,
                    competition_level="medium" if len(listings) > 25 else "low",
                )

            # Generate market insights
            insights = self._generate_market_insights(market_data)

            return {
                "success": True,
                "decision_type": "market_analysis",
                "data": {
                    "market_data": {
                        "category_id": market_data.category_id,
                        "average_price": market_data.average_price,
                        "price_range": market_data.price_range,
                        "total_listings": market_data.total_listings,
                        "competition_level": market_data.competition_level,
                        "trending_keywords": market_data.trending_keywords,
                    },
                    "insights": insights,
                    "recommendations": self._generate_recommendations(market_data),
                },
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {"success": False, "error": str(e), "agent_id": self.agent_id}

    async def _research_pricing(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Research optimal pricing for a product."""
        try:
            user_id = request["user_id"]
            product_title = request.get("product_title", "")
            target_category = request.get("category_id")

            logger.info(
                f"💰 Researching pricing for: {product_title} (user: {user_id})"
            )

            # Search for similar products
            listings = await self.ebay_service.search_marketplace(
                user_id=user_id,
                query=product_title,
                category_id=target_category,
                limit=30,
                sort="PricePlusShipping",
            )

            if not listings:
                return {
                    "success": False,
                    "error": "No comparable listings found",
                    "agent_id": self.agent_id,
                }

            # Analyze pricing data
            prices = [listing.price for listing in listings if listing.price > 0]
            prices.sort()

            pricing_analysis = {
                "comparable_listings": len(listings),
                "price_statistics": {
                    "min": min(prices) if prices else 0,
                    "max": max(prices) if prices else 0,
                    "average": sum(prices) / len(prices) if prices else 0,
                    "median": prices[len(prices) // 2] if prices else 0,
                    "percentile_25": prices[len(prices) // 4] if prices else 0,
                    "percentile_75": prices[3 * len(prices) // 4] if prices else 0,
                },
                "recommended_price_range": {
                    "competitive": prices[len(prices) // 4] if prices else 0,
                    "market_rate": prices[len(prices) // 2] if prices else 0,
                    "premium": prices[3 * len(prices) // 4] if prices else 0,
                },
            }

            return {
                "success": True,
                "decision_type": "price_research",
                "data": pricing_analysis,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Price research failed: {e}")
            return {"success": False, "error": str(e), "agent_id": self.agent_id}

    async def _analyze_competition(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competition in a specific market segment."""
        try:
            user_id = request["user_id"]
            query = request.get("query", "")

            logger.info(f"🏁 Analyzing competition for: {query} (user: {user_id})")

            # Get competitive listings
            listings = await self.ebay_service.search_marketplace(
                user_id=user_id, query=query, limit=50
            )

            # Analyze competition metrics
            competition_analysis = {
                "total_competitors": len(listings),
                "price_competition": {
                    "price_spread": (
                        max([l.price for l in listings])
                        - min([l.price for l in listings])
                        if listings
                        else 0
                    ),
                    "average_price": (
                        sum([l.price for l in listings]) / len(listings)
                        if listings
                        else 0
                    ),
                },
                "listing_quality": {
                    "with_images": len([l for l in listings if l.image_urls]),
                    "detailed_titles": len([l for l in listings if len(l.title) > 50]),
                    "watchers_average": (
                        sum([l.watchers for l in listings]) / len(listings)
                        if listings
                        else 0
                    ),
                },
                "market_saturation": (
                    "high"
                    if len(listings) > 40
                    else "medium" if len(listings) > 20 else "low"
                ),
            }

            return {
                "success": True,
                "decision_type": "competition_analysis",
                "data": competition_analysis,
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Competition analysis failed: {e}")
            return {"success": False, "error": str(e), "agent_id": self.agent_id}

    async def _detect_opportunities(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Detect market opportunities based on eBay data."""
        try:
            user_id = request["user_id"]
            categories = request.get(
                "categories", ["Electronics", "Home & Garden", "Fashion"]
            )

            logger.info(
                f"🎯 Detecting opportunities in categories: {categories} (user: {user_id})"
            )

            opportunities = []

            for category in categories[:3]:  # Limit to avoid rate limits
                # Search for trending items in category
                listings = await self.ebay_service.search_marketplace(
                    user_id=user_id, query=category.lower(), limit=20
                )

                if listings:
                    # Identify potential opportunities
                    high_watcher_items = [l for l in listings if l.watchers > 5]
                    low_competition_items = [l for l in listings if len(listings) < 15]

                    if high_watcher_items or low_competition_items:
                        opportunities.append(
                            {
                                "category": category,
                                "opportunity_type": (
                                    "high_demand"
                                    if high_watcher_items
                                    else "low_competition"
                                ),
                                "item_count": len(
                                    high_watcher_items or low_competition_items
                                ),
                                "average_price": sum(
                                    [
                                        l.price
                                        for l in (
                                            high_watcher_items or low_competition_items
                                        )
                                    ]
                                )
                                / len(high_watcher_items or low_competition_items),
                                "confidence": (
                                    "high" if len(high_watcher_items) > 3 else "medium"
                                ),
                            }
                        )

            return {
                "success": True,
                "decision_type": "opportunity_detection",
                "data": {
                    "opportunities": opportunities,
                    "total_opportunities": len(opportunities),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                },
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Opportunity detection failed: {e}")
            return {"success": False, "error": str(e), "agent_id": self.agent_id}

    def _generate_market_insights(self, market_data: EbayMarketData) -> List[str]:
        """Generate actionable market insights."""
        insights = []

        if market_data.competition_level == "low":
            insights.append(
                "Low competition detected - good opportunity for new listings"
            )
        elif market_data.competition_level == "high":
            insights.append(
                "High competition - focus on differentiation and competitive pricing"
            )

        if market_data.average_price > 100:
            insights.append("High-value market segment - consider premium positioning")
        elif market_data.average_price < 25:
            insights.append("Low-price market - focus on volume and cost efficiency")

        price_spread = market_data.price_range["max"] - market_data.price_range["min"]
        if price_spread > market_data.average_price:
            insights.append(
                "Wide price range indicates market segmentation opportunities"
            )

        return insights

    def _generate_recommendations(self, market_data: EbayMarketData) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if market_data.competition_level == "low":
            recommendations.append(
                "Consider entering this market with competitive pricing"
            )

        if market_data.average_price > 50:
            recommendations.append("Focus on quality and detailed product descriptions")

        recommendations.append(
            f"Target price range: ${market_data.price_range['min']:.2f} - ${market_data.price_range['max']:.2f}"
        )

        return recommendations

    def _get_algorithm_name(self, decision_type: str) -> str:
        """Get algorithm name for decision type."""
        algorithm_mapping = {
            "market_analysis": "market_trend_analysis",
            "price_research": "competitive_pricing_algorithm",
            "competition_analysis": "market_saturation_analysis",
            "opportunity_detection": "opportunity_scoring_algorithm",
        }
        return algorithm_mapping.get(decision_type, "standard_market_algorithm")

    async def _process_algorithmic_decision(
        self, decision_context: Dict[str, Any], decision_type: str
    ) -> Dict[str, Any]:
        """Process algorithmic decision for market analysis."""
        try:
            # Use the existing process_decision_request method
            request = {
                "decision_type": decision_type,
                "user_id": decision_context.get("user_id"),
                **decision_context,
            }

            result = await self.process_decision_request(request)

            return {
                "success": result.get("success", False),
                "result": result.get("data", {}),
                "algorithm": self._get_algorithm_name(decision_type),
                "processing_time_ms": result.get("processing_time_ms", 0),
            }

        except Exception as e:
            logger.error(f"Algorithmic decision processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "algorithm": self._get_algorithm_name(decision_type),
            }

    async def cleanup(self) -> None:
        """Cleanup Market Agent resources."""
        try:
            logger.info(f"🧹 Cleaning up Market Agent: {self.agent_id}")
            self.state = AutonomousAgentState.OFFLINE
        except Exception as e:
            logger.error(f"Error during Market Agent cleanup: {e}")


# Factory function for 4+1 architecture integration
def create_market_agent_ebay() -> MarketAgentEbay:
    """Create Market Agent with eBay integration for 4+1 architecture."""
    return MarketAgentEbay()
