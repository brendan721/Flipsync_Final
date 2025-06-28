"""
Competitive UnifiedAgent for FlipSync marketplace competitive analysis.

This agent provides competitive intelligence, price monitoring, and market analysis
capabilities for the FlipSync agent ecosystem.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fs_agt_clean.agents.base.base import BaseUnifiedAgent

logger = logging.getLogger(__name__)


@dataclass
class CompetitorData:
    """Competitor data structure."""

    competitor_id: str
    marketplace: str
    product_id: str
    price: float
    availability: bool
    rating: Optional[float]
    review_count: Optional[int]
    last_updated: datetime


@dataclass
class PriceAnalysis:
    """Price analysis results."""

    product_id: str
    marketplace: str
    min_price: float
    max_price: float
    avg_price: float
    median_price: float
    competitor_count: int
    price_trend: str  # "increasing", "decreasing", "stable"
    analysis_date: datetime


class CompetitiveUnifiedAgent(BaseUnifiedAgent):
    """
    Competitive UnifiedAgent for marketplace competitive analysis.

    Provides competitive intelligence, price monitoring, and market analysis
    capabilities for the FlipSync agent ecosystem.
    """

    def __init__(
        self, agent_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Competitive UnifiedAgent.

        Args:
            agent_id: Unique identifier for this agent instance (auto-generated if None)
            config: Optional configuration dictionary
        """
        if agent_id is None:
            agent_id = f"competitive_agent_{str(uuid4())[:8]}"

        super().__init__(agent_id=agent_id, config=config or {})

        # Competitive data storage
        self.competitor_data: Dict[str, List[CompetitorData]] = {}
        self.price_analyses: Dict[str, PriceAnalysis] = {}

        # Monitoring configuration
        config = config or {}
        self.monitoring_enabled = config.get("monitoring_enabled", True)
        self.analysis_interval = config.get("analysis_interval", 3600)  # 1 hour default

        logger.info(f"CompetitiveUnifiedAgent {agent_id} initialized")

    async def analyze_competition(
        self, product_id: str, marketplace: str, competitor_data: List[Dict[str, Any]]
    ) -> PriceAnalysis:
        """
        Analyze competition for a specific product.

        Args:
            product_id: Product identifier
            marketplace: Marketplace name
            competitor_data: List of competitor data dictionaries

        Returns:
            Price analysis results
        """
        # Convert competitor data to structured format
        competitors = []
        for data in competitor_data:
            competitor = CompetitorData(
                competitor_id=data.get("competitor_id", str(uuid4())),
                marketplace=marketplace,
                product_id=product_id,
                price=float(data.get("price", 0.0)),
                availability=data.get("availability", True),
                rating=data.get("rating"),
                review_count=data.get("review_count"),
                last_updated=datetime.utcnow(),
            )
            competitors.append(competitor)

        # Store competitor data
        key = f"{marketplace}:{product_id}"
        self.competitor_data[key] = competitors

        # Perform price analysis
        prices = [c.price for c in competitors if c.availability and c.price > 0]

        if not prices:
            logger.warning(f"No valid prices found for {product_id} on {marketplace}")
            return PriceAnalysis(
                product_id=product_id,
                marketplace=marketplace,
                min_price=0.0,
                max_price=0.0,
                avg_price=0.0,
                median_price=0.0,
                competitor_count=0,
                price_trend="unknown",
                analysis_date=datetime.utcnow(),
            )

        # Calculate price statistics
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        # Calculate median
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        median_price = (
            sorted_prices[n // 2]
            if n % 2 == 1
            else (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / 2
        )

        # Determine price trend (simplified)
        price_trend = (
            "stable"  # Default, would need historical data for real trend analysis
        )

        analysis = PriceAnalysis(
            product_id=product_id,
            marketplace=marketplace,
            min_price=min_price,
            max_price=max_price,
            avg_price=avg_price,
            median_price=median_price,
            competitor_count=len(competitors),
            price_trend=price_trend,
            analysis_date=datetime.utcnow(),
        )

        # Store analysis
        self.price_analyses[key] = analysis

        logger.info(f"Competitive analysis completed for {product_id} on {marketplace}")
        return analysis

    async def get_price_recommendations(
        self, product_id: str, marketplace: str, current_price: float
    ) -> Dict[str, Any]:
        """
        Get pricing recommendations based on competitive analysis.

        Args:
            product_id: Product identifier
            marketplace: Marketplace name
            current_price: Current product price

        Returns:
            Pricing recommendations
        """
        key = f"{marketplace}:{product_id}"
        analysis = self.price_analyses.get(key)

        if not analysis:
            return {
                "status": "no_analysis",
                "message": "No competitive analysis available for this product",
            }

        recommendations = {
            "current_price": current_price,
            "market_position": "unknown",
            "recommended_action": "maintain",
            "suggested_price_range": {
                "min": analysis.min_price,
                "max": analysis.max_price,
            },
            "competitive_advantage": "neutral",
        }

        # Determine market position
        if current_price <= analysis.min_price:
            recommendations["market_position"] = "lowest"
            recommendations["competitive_advantage"] = "price_leader"
        elif current_price >= analysis.max_price:
            recommendations["market_position"] = "highest"
            recommendations["competitive_advantage"] = "premium"
        elif current_price <= analysis.median_price:
            recommendations["market_position"] = "below_median"
            recommendations["competitive_advantage"] = "competitive"
        else:
            recommendations["market_position"] = "above_median"
            recommendations["competitive_advantage"] = "premium"

        # Generate recommendations
        if current_price > analysis.avg_price * 1.2:
            recommendations["recommended_action"] = "decrease"
            recommendations["suggested_price"] = analysis.avg_price * 1.1
        elif current_price < analysis.avg_price * 0.8:
            recommendations["recommended_action"] = "increase"
            recommendations["suggested_price"] = analysis.avg_price * 0.9
        else:
            recommendations["recommended_action"] = "maintain"
            recommendations["suggested_price"] = current_price

        return recommendations

    async def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process incoming message.

        Args:
            message: Message to process
        """
        message_type = message.get("type", "unknown")

        if message_type == "analyze_competition":
            await self.analyze_competition(
                product_id=message.get("product_id", ""),
                marketplace=message.get("marketplace", ""),
                competitor_data=message.get("competitor_data", []),
            )
        elif message_type == "get_recommendations":
            await self.get_price_recommendations(
                product_id=message.get("product_id", ""),
                marketplace=message.get("marketplace", ""),
                current_price=message.get("current_price", 0.0),
            )
        elif message_type == "get_status":
            self.get_status()
        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def take_action(self, action: Dict[str, Any]) -> None:
        """
        Take a specific action.

        Args:
            action: Action dictionary containing action type and parameters
        """
        action_type = action.get("type", "unknown")
        params = action.get("parameters", {})

        if action_type == "analyze_competition":
            await self.analyze_competition(
                product_id=params.get("product_id", ""),
                marketplace=params.get("marketplace", ""),
                competitor_data=params.get("competitor_data", []),
            )
        else:
            logger.warning(f"Unknown action type: {action_type}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status.

        Returns:
            UnifiedAgent status information
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": "CompetitiveUnifiedAgent",
            "monitored_products": len(self.competitor_data),
            "completed_analyses": len(self.price_analyses),
            "monitoring_enabled": self.monitoring_enabled,
            "status": "operational",
            "last_activity": datetime.utcnow().isoformat(),
        }
