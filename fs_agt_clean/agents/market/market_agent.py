"""
Market UnifiedAgent for FlipSync AI System
===================================

This module implements the Market Intelligence UnifiedAgent that specializes in
pricing analysis, inventory management, competitor monitoring, and marketplace optimization.
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.agents.market.amazon_client import AmazonClient
from fs_agt_clean.agents.market.ebay_client import eBayClient
from fs_agt_clean.agents.market.pricing_engine import PricingEngine, PricingStrategy
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole
from fs_agt_clean.core.models.marketplace_models import (
    CompetitorAnalysis,
    DemandForecast,
    InventoryStatus,
    ListingOptimization,
    MarketMetrics,
    MarketplaceType,
    Price,
    PricingRecommendation,
    ProductIdentifier,
    create_price,
    create_product_identifier,
)

logger = logging.getLogger(__name__)


class MarketUnifiedAgent(BaseConversationalUnifiedAgent):
    """Market Intelligence UnifiedAgent for pricing and marketplace optimization."""

    def __init__(self, agent_id: Optional[str] = None, use_fast_model: bool = True):
        """Initialize the Market UnifiedAgent."""
        super().__init__(UnifiedAgentRole.MARKET, agent_id, use_fast_model)

        # Initialize marketplace clients
        self.amazon_client = None
        self.ebay_client = None

        # Initialize pricing engine
        self.pricing_engine = PricingEngine()

        # Cache for recent analyses
        self.analysis_cache = {}
        self.cache_ttl = 300  # 5 minutes

        logger.info(f"Market UnifiedAgent initialized: {self.agent_id}")

    async def analyze_market(self, product_query: str) -> Dict[str, Any]:
        """Analyze market conditions for a product."""
        try:
            # Extract product information from query
            product_info = self._extract_product_info(product_query)

            # Initialize clients if needed
            await self._ensure_clients_initialized()

            # Perform market analysis
            analysis = {
                "product_query": product_query,
                "listings": [],
                "price_range": {"min": 0, "max": 0, "average": 0},
                "market_trends": "stable",
                "competition_level": "moderate",
                "demand_indicators": "normal",
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

            # Get listings from multiple marketplaces
            try:
                # eBay listings
                async with self.ebay_client:
                    ebay_listings = await self.ebay_client.search_products(
                        product_query, limit=10
                    )
                    for listing in ebay_listings:
                        analysis["listings"].append(
                            {
                                "marketplace": "ebay",
                                "title": listing.title,
                                "price": float(listing.current_price.amount),
                                "condition": getattr(listing, "condition", "unknown"),
                                "seller_rating": getattr(
                                    listing, "seller_rating", "N/A"
                                ),
                            }
                        )
            except Exception as e:
                logger.warning(f"eBay search failed: {e}")

            # Calculate price statistics
            if analysis["listings"]:
                prices = [listing["price"] for listing in analysis["listings"]]
                analysis["price_range"] = {
                    "min": min(prices),
                    "max": max(prices),
                    "average": sum(prices) / len(prices),
                }

                # Determine competition level based on number of listings
                listing_count = len(analysis["listings"])
                if listing_count > 20:
                    analysis["competition_level"] = "high"
                elif listing_count > 10:
                    analysis["competition_level"] = "moderate"
                else:
                    analysis["competition_level"] = "low"

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing market: {e}")
            return {
                "product_query": product_query,
                "listings": [],
                "price_range": {"min": 0, "max": 0, "average": 0},
                "market_trends": "unknown",
                "competition_level": "unknown",
                "demand_indicators": "unknown",
                "error": str(e),
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

    async def analyze_product_pricing(
        self, product_name: str, category: str
    ) -> Dict[str, Any]:
        """Analyze pricing for a specific product and category."""
        try:
            # Perform market analysis first
            market_data = await self.analyze_market(product_name)

            # Calculate pricing recommendations
            pricing_analysis = {
                "product_name": product_name,
                "category": category,
                "market_data": market_data,
                "recommended_price": 0,
                "price_confidence": 0.8,
                "pricing_strategy": "competitive",
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

            # Calculate recommended price based on market data
            if market_data["listings"]:
                avg_price = market_data["price_range"]["average"]
                pricing_analysis["recommended_price"] = (
                    avg_price * 0.95
                )  # Slightly below average
                pricing_analysis["average_price"] = avg_price
                pricing_analysis["min_price"] = market_data["price_range"]["min"]
                pricing_analysis["max_price"] = market_data["price_range"]["max"]
            else:
                # Default pricing if no market data
                pricing_analysis["recommended_price"] = 29.99
                pricing_analysis["average_price"] = 29.99

            return pricing_analysis

        except Exception as e:
            logger.error(f"Error analyzing pricing: {e}")
            return {
                "product_name": product_name,
                "category": category,
                "recommended_price": 29.99,
                "average_price": 29.99,
                "price_confidence": 0.5,
                "pricing_strategy": "default",
                "error": str(e),
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

    async def _process_response(
        self,
        llm_response: str,
        original_message: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Process LLM response with market-specific enhancements."""
        try:
            # Extract any product identifiers from the original message
            product_info = self._extract_product_info(original_message)

            # Determine the type of market query
            query_type = self._classify_market_query(original_message)

            # Enhance response with market data if relevant
            enhanced_response = await self._enhance_with_market_data(
                llm_response, query_type, product_info, conversation_id
            )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error processing market agent response: {e}")
            return llm_response  # Return original response if enhancement fails

    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get market-specific context for prompt generation."""
        return {
            "business_type": "e-commerce marketplace seller",
            "marketplaces": "Amazon, eBay, Walmart",
            "categories": "electronics, home goods, consumer products",
            "metrics": "pricing, inventory, sales rank, competition",
            "specializations": "pricing analysis, inventory management, competitor monitoring, marketplace optimization, demand forecasting",
        }

    def _extract_product_info(self, message: str) -> Dict[str, Any]:
        """Extract product identifiers and information from user message."""
        product_info = {}

        # Extract ASIN (Amazon Standard Identification Number)
        asin_pattern = r"\b[A-Z0-9]{10}\b"
        asin_matches = re.findall(asin_pattern, message)
        if asin_matches:
            product_info["asin"] = asin_matches[0]

        # Extract SKU patterns
        sku_pattern = r"\bSKU[:\-\s]*([A-Z0-9\-]+)\b"
        sku_matches = re.findall(sku_pattern, message, re.IGNORECASE)
        if sku_matches:
            product_info["sku"] = sku_matches[0]

        # Extract UPC/EAN patterns
        upc_pattern = r"\b\d{12,13}\b"
        upc_matches = re.findall(upc_pattern, message)
        if upc_matches:
            product_info["upc"] = upc_matches[0]

        # Extract price mentions
        price_pattern = r"\$(\d+(?:\.\d{2})?)"
        price_matches = re.findall(price_pattern, message)
        if price_matches:
            product_info["mentioned_price"] = float(price_matches[0])

        # Extract product titles/names (simple heuristic)
        # Look for quoted strings or capitalized phrases
        title_pattern = r'"([^"]+)"'
        title_matches = re.findall(title_pattern, message)
        if title_matches:
            product_info["product_title"] = title_matches[0]

        return product_info

    def _classify_market_query(self, message: str) -> str:
        """Classify the type of market query."""
        message_lower = message.lower()

        # Pricing queries
        pricing_keywords = [
            "price",
            "pricing",
            "cost",
            "expensive",
            "cheap",
            "competitive",
        ]
        if any(keyword in message_lower for keyword in pricing_keywords):
            return "pricing"

        # Inventory queries
        inventory_keywords = [
            "inventory",
            "stock",
            "quantity",
            "available",
            "out of stock",
        ]
        if any(keyword in message_lower for keyword in inventory_keywords):
            return "inventory"

        # Competitor queries
        competitor_keywords = ["competitor", "competition", "compare", "vs", "versus"]
        if any(keyword in message_lower for keyword in competitor_keywords):
            return "competitor"

        # Optimization queries
        optimization_keywords = [
            "optimize",
            "improve",
            "better",
            "increase sales",
            "ranking",
        ]
        if any(keyword in message_lower for keyword in optimization_keywords):
            return "optimization"

        # Forecasting queries
        forecast_keywords = ["forecast", "predict", "demand", "trend", "future"]
        if any(keyword in message_lower for keyword in forecast_keywords):
            return "forecast"

        return "general"

    async def _enhance_with_market_data(
        self,
        llm_response: str,
        query_type: str,
        product_info: Dict[str, Any],
        conversation_id: str,
    ) -> str:
        """Enhance LLM response with actual market data."""
        try:
            # Initialize clients if needed
            await self._ensure_clients_initialized()

            enhanced_parts = [llm_response]

            if query_type == "pricing" and product_info:
                pricing_data = await self._get_pricing_analysis(product_info)
                if pricing_data:
                    enhanced_parts.append(
                        f"\n\n📊 **Pricing Analysis:**\n{pricing_data}"
                    )

            elif query_type == "inventory" and product_info:
                inventory_data = await self._get_inventory_analysis(product_info)
                if inventory_data:
                    enhanced_parts.append(
                        f"\n\n📦 **Inventory Status:**\n{inventory_data}"
                    )

            elif query_type == "competitor" and product_info:
                competitor_data = await self._get_competitor_analysis(product_info)
                if competitor_data:
                    enhanced_parts.append(
                        f"\n\n🏆 **Competitor Analysis:**\n{competitor_data}"
                    )

            elif query_type == "optimization" and product_info:
                optimization_data = await self._get_optimization_suggestions(
                    product_info
                )
                if optimization_data:
                    enhanced_parts.append(
                        f"\n\n🚀 **Optimization Suggestions:**\n{optimization_data}"
                    )

            elif query_type == "forecast" and product_info:
                forecast_data = await self._get_demand_forecast(product_info)
                if forecast_data:
                    enhanced_parts.append(
                        f"\n\n📈 **Demand Forecast:**\n{forecast_data}"
                    )

            return "\n".join(enhanced_parts)

        except Exception as e:
            logger.error(f"Error enhancing response with market data: {e}")
            return llm_response

    async def _ensure_clients_initialized(self):
        """Ensure marketplace clients are initialized."""
        if self.amazon_client is None:
            self.amazon_client = AmazonClient()

        if self.ebay_client is None:
            self.ebay_client = eBayClient()

    async def _get_pricing_analysis(
        self, product_info: Dict[str, Any]
    ) -> Optional[str]:
        """Get pricing analysis for a product."""
        try:
            # Create product identifier
            product_id = create_product_identifier(
                asin=product_info.get("asin"),
                sku=product_info.get("sku"),
                upc=product_info.get("upc"),
            )

            # Get current price (mock for now)
            current_price = create_price(
                product_info.get("mentioned_price", 29.99),
                marketplace=MarketplaceType.AMAZON,
            )

            # Get competitor prices
            competitor_prices = []

            # Amazon competitive pricing
            async with self.amazon_client:
                if product_info.get("asin"):
                    amazon_prices = await self.amazon_client.get_competitive_pricing(
                        product_info["asin"]
                    )
                    competitor_prices.extend(amazon_prices)

            # eBay competitive pricing
            async with self.ebay_client:
                if product_info.get("product_title"):
                    ebay_prices = await self.ebay_client.get_competitive_prices(
                        product_info["product_title"]
                    )
                    competitor_prices.extend(ebay_prices[:5])  # Limit to top 5

            # Perform pricing analysis
            recommendation = await self.pricing_engine.analyze_pricing(
                product_id=product_id,
                current_price=current_price,
                competitor_prices=competitor_prices,
            )

            # Format the analysis
            return self._format_pricing_analysis(recommendation)

        except Exception as e:
            logger.error(f"Error in pricing analysis: {e}")
            return None

    async def _get_inventory_analysis(
        self, product_info: Dict[str, Any]
    ) -> Optional[str]:
        """Get inventory analysis for a product."""
        try:
            if not product_info.get("sku"):
                return "Please provide a SKU for inventory analysis."

            async with self.amazon_client:
                inventory_status = await self.amazon_client.get_inventory_status(
                    product_info["sku"]
                )

            if inventory_status:
                return self._format_inventory_analysis(inventory_status)

            return "Unable to retrieve inventory information at this time."

        except Exception as e:
            logger.error(f"Error in inventory analysis: {e}")
            return None

    async def _get_competitor_analysis(
        self, product_info: Dict[str, Any]
    ) -> Optional[str]:
        """Get competitor analysis for a product."""
        try:
            # This would perform comprehensive competitor analysis
            # For now, return a summary based on available data

            analysis_parts = []

            # Amazon competitors
            if product_info.get("asin"):
                async with self.amazon_client:
                    amazon_listing = await self.amazon_client.get_product_details(
                        product_info["asin"]
                    )
                    if amazon_listing:
                        analysis_parts.append(
                            f"Amazon: {amazon_listing.title} - ${amazon_listing.current_price.amount}"
                        )

            # eBay competitors
            if product_info.get("product_title"):
                async with self.ebay_client:
                    ebay_listings = await self.ebay_client.search_products(
                        product_info["product_title"], limit=3
                    )
                    for listing in ebay_listings:
                        analysis_parts.append(
                            f"eBay: {listing.title[:50]}... - ${listing.current_price.amount}"
                        )

            if analysis_parts:
                return "\n".join(analysis_parts)

            return "No competitor data available for this product."

        except Exception as e:
            logger.error(f"Error in competitor analysis: {e}")
            return None

    async def _get_optimization_suggestions(
        self, product_info: Dict[str, Any]
    ) -> Optional[str]:
        """Get optimization suggestions for a product."""
        try:
            suggestions = []

            # Price optimization
            if product_info.get("mentioned_price"):
                suggestions.append("Consider competitive pricing analysis")

            # Title optimization
            if product_info.get("product_title"):
                suggestions.append("Optimize product title with relevant keywords")

            # General suggestions
            suggestions.extend(
                [
                    "Improve product images quality",
                    "Enhance product description with benefits",
                    "Monitor competitor pricing regularly",
                    "Track inventory levels to avoid stockouts",
                ]
            )

            return "\n".join(f"• {suggestion}" for suggestion in suggestions)

        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {e}")
            return None

    async def _get_demand_forecast(self, product_info: Dict[str, Any]) -> Optional[str]:
        """Get demand forecast for a product."""
        try:
            # This would use historical data and ML models
            # For now, provide a basic forecast

            forecast_parts = [
                "Based on current market trends:",
                "• Expected demand: Moderate to High",
                "• Seasonal factors: Consider holiday season impact",
                "• Recommendation: Maintain adequate inventory levels",
            ]

            return "\n".join(forecast_parts)

        except Exception as e:
            logger.error(f"Error generating demand forecast: {e}")
            return None

    def _format_pricing_analysis(self, recommendation: PricingRecommendation) -> str:
        """Format pricing recommendation for display."""
        current = recommendation.current_price.amount
        recommended = recommendation.recommended_price.amount
        change_percent = float((recommended - current) / current * 100)

        parts = [
            f"Current Price: ${current}",
            f"Recommended Price: ${recommended}",
            f"Change: {change_percent:+.1f}%",
            f"Confidence: {recommendation.confidence_score:.1%}",
            f"Reasoning: {recommendation.reasoning}",
        ]

        return "\n".join(parts)

    def _format_inventory_analysis(self, inventory: InventoryStatus) -> str:
        """Format inventory status for display."""
        parts = [
            f"Available: {inventory.quantity_available} units",
            f"Reserved: {inventory.quantity_reserved} units",
            f"Inbound: {inventory.quantity_inbound} units",
        ]

        if inventory.reorder_point:
            parts.append(f"Reorder Point: {inventory.reorder_point} units")

        if inventory.fulfillment_method:
            parts.append(f"Fulfillment: {inventory.fulfillment_method}")

        return "\n".join(parts)

    # Public API methods for direct agent calls

    async def analyze_pricing(self, product_id: str) -> PricingRecommendation:
        """Analyze pricing for a product."""
        # This would be called directly by other systems
        pass

    async def check_inventory(self, sku: str) -> InventoryStatus:
        """Check inventory status for a SKU."""
        # This would be called directly by other systems
        pass

    async def monitor_competitors(self, product_id: str) -> CompetitorAnalysis:
        """Monitor competitors for a product."""
        # This would be called directly by other systems
        pass

    async def optimize_listing(self, listing_id: str) -> ListingOptimization:
        """Optimize a product listing."""
        # This would be called directly by other systems
        pass

    async def forecast_demand(self, product_id: str) -> DemandForecast:
        """Forecast demand for a product."""
        # This would be called directly by other systems
        pass

    # Phase 2D: Methods required by orchestration workflows

    async def analyze_pricing_strategy(
        self, product_data: Dict[str, Any], user_message: str
    ) -> Dict[str, Any]:
        """Analyze pricing strategy for a product based on user request."""
        try:
            logger.info(
                f"Market UnifiedAgent analyzing pricing strategy for: {user_message[:50]}..."
            )

            # Extract product information from user message and product data
            product_info = {
                "product_name": product_data.get("name", "electronics product"),
                "category": product_data.get("category", "electronics"),
                "current_price": product_data.get("price", 0),
                "user_query": user_message,
            }

            # Generate AI-powered pricing analysis
            analysis_prompt = f"""
            Analyze the pricing strategy for this product request:

            UnifiedUser Request: {user_message}
            Product: {product_info['product_name']}
            Category: {product_info['category']}
            Current Price: ${product_info['current_price']}

            Provide a comprehensive pricing strategy analysis including:
            1. Market positioning recommendations
            2. Competitive pricing insights
            3. Price optimization suggestions
            4. Risk factors and considerations
            5. Implementation timeline

            Focus on actionable insights for electronics products.
            """

            # Get AI analysis
            response = await self.llm_client.generate_response(
                prompt=analysis_prompt,
                system_prompt="You are an expert market analyst specializing in e-commerce pricing strategies.",
            )

            # Structure the analysis
            pricing_analysis = {
                "analysis_type": "pricing_strategy",
                "product_info": product_info,
                "ai_insights": response.content,
                "confidence_score": response.confidence_score,
                "recommendations": self._extract_pricing_recommendations(
                    response.content
                ),
                "market_position": self._determine_market_position(product_info),
                "competitive_factors": self._analyze_competitive_factors(product_info),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Market UnifiedAgent completed pricing strategy analysis with confidence: {response.confidence_score}"
            )
            return pricing_analysis

        except Exception as e:
            logger.error(f"Error in pricing strategy analysis: {e}")
            return {
                "analysis_type": "pricing_strategy",
                "status": "error",
                "error_message": str(e),
                "fallback_recommendations": [
                    "Research competitor pricing in your category",
                    "Consider cost-plus pricing as a baseline",
                    "Test different price points with A/B testing",
                    "Monitor market response and adjust accordingly",
                ],
            }

    async def conduct_market_research(
        self, research_topic: str, research_scope: str = "general"
    ) -> Dict[str, Any]:
        """Conduct comprehensive market research on a topic."""
        try:
            logger.info(
                f"Market UnifiedAgent conducting research on: {research_topic[:50]}..."
            )

            # Generate research analysis
            research_prompt = f"""
            Conduct comprehensive market research on this topic:

            Research Topic: {research_topic}
            Research Scope: {research_scope}

            Provide detailed analysis covering:
            1. Market size and growth trends
            2. Key competitors and market share
            3. Consumer behavior and preferences
            4. Pricing trends and strategies
            5. Market opportunities and threats
            6. Technology and innovation trends
            7. Regulatory and economic factors

            Focus on actionable insights for e-commerce sellers.
            """

            # Get AI research analysis
            response = await self.llm_client.generate_response(
                prompt=research_prompt,
                system_prompt="You are an expert market researcher with deep knowledge of e-commerce markets and consumer behavior.",
            )

            # Structure the research
            market_research = {
                "research_type": "market_analysis",
                "topic": research_topic,
                "scope": research_scope,
                "ai_analysis": response.content,
                "confidence_score": response.confidence_score,
                "key_findings": self._extract_key_findings(response.content),
                "market_trends": self._identify_market_trends(response.content),
                "opportunities": self._extract_opportunities(response.content),
                "threats": self._extract_threats(response.content),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Market UnifiedAgent completed market research with confidence: {response.confidence_score}"
            )
            return market_research

        except Exception as e:
            logger.error(f"Error in market research: {e}")
            return {
                "research_type": "market_analysis",
                "status": "error",
                "error_message": str(e),
                "fallback_insights": [
                    "Research your target market demographics",
                    "Analyze competitor strategies and positioning",
                    "Monitor industry trends and news",
                    "Survey potential customers for insights",
                ],
            }

    def _extract_pricing_recommendations(self, ai_content: str) -> List[str]:
        """Extract pricing recommendations from AI analysis."""
        recommendations = []

        # Look for numbered lists or bullet points
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("1.", "2.", "3.", "4.", "5.", "-", "•")) and any(
                keyword in line.lower()
                for keyword in ["price", "cost", "margin", "competitive"]
            ):
                recommendations.append(line)

        # Fallback recommendations if none found
        if not recommendations:
            recommendations = [
                "Analyze competitor pricing in your category",
                "Consider value-based pricing strategies",
                "Test price elasticity with small adjustments",
                "Monitor profit margins and adjust accordingly",
            ]

        return recommendations[:5]  # Limit to top 5

    def _determine_market_position(self, product_info: Dict[str, Any]) -> str:
        """Determine market positioning based on product info."""
        category = product_info.get("category", "").lower()
        price = product_info.get("current_price", 0)

        if "electronics" in category:
            if price > 500:
                return "premium"
            elif price > 100:
                return "mid-market"
            else:
                return "budget"

        return "general"

    def _analyze_competitive_factors(self, product_info: Dict[str, Any]) -> List[str]:
        """Analyze competitive factors affecting pricing."""
        factors = []

        category = product_info.get("category", "").lower()

        if "electronics" in category:
            factors.extend(
                [
                    "Technology lifecycle and obsolescence",
                    "Brand recognition and reputation",
                    "Feature differentiation",
                    "Warranty and support services",
                ]
            )

        factors.extend(
            [
                "Market demand and seasonality",
                "Competitor pricing strategies",
                "Distribution channel costs",
                "Customer price sensitivity",
            ]
        )

        return factors

    def _extract_key_findings(self, ai_content: str) -> List[str]:
        """Extract key findings from market research."""
        findings = []

        # Look for key insights in the content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("Key", "Important", "Notable", "Significant")) or any(
                keyword in line.lower()
                for keyword in ["trend", "growth", "market", "consumer"]
            ):
                if len(line) > 20:  # Avoid short lines
                    findings.append(line)

        return findings[:5]  # Limit to top 5

    def _identify_market_trends(self, ai_content: str) -> List[str]:
        """Identify market trends from research content."""
        trends = []

        # Look for trend-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in ["trend", "growing", "increasing", "emerging", "rising"]
            ):
                if len(line) > 15:
                    trends.append(line)

        return trends[:5]  # Limit to top 5

    def _extract_opportunities(self, ai_content: str) -> List[str]:
        """Extract market opportunities from research."""
        opportunities = []

        # Look for opportunity-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in ["opportunity", "potential", "gap", "untapped", "growth"]
            ):
                if len(line) > 15:
                    opportunities.append(line)

        return opportunities[:5]  # Limit to top 5

    def _extract_threats(self, ai_content: str) -> List[str]:
        """Extract market threats from research."""
        threats = []

        # Look for threat-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in ["threat", "risk", "challenge", "competition", "decline"]
            ):
                if len(line) > 15:
                    threats.append(line)

        return threats[:5]  # Limit to top 5
