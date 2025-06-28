"""
Pricing Analysis Engine for FlipSync Market UnifiedAgent
=================================================

This module provides intelligent pricing analysis and recommendations
based on competitive data, market conditions, and business objectives.
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional, Tuple

from fs_agt_clean.core.models.marketplace_models import (
    CompetitorAnalysis,
    CompetitorListing,
    MarketMetrics,
    Price,
    PriceChangeDirection,
    PricingRecommendation,
    ProductIdentifier,
    calculate_price_change_percentage,
    get_price_position,
)

logger = logging.getLogger(__name__)


@dataclass
class PricingStrategy:
    """Pricing strategy configuration."""

    strategy_type: str  # "competitive", "premium", "value", "penetration"
    target_margin: float  # Target profit margin (0.0 to 1.0)
    max_price_change: float  # Maximum price change percentage
    min_price_threshold: Decimal  # Minimum acceptable price
    max_price_threshold: Decimal  # Maximum acceptable price
    competitor_weight: float = 0.6  # Weight given to competitor prices
    market_weight: float = 0.3  # Weight given to market conditions
    cost_weight: float = 0.1  # Weight given to cost considerations


@dataclass
class MarketConditions:
    """Current market conditions affecting pricing."""

    demand_level: str  # "low", "medium", "high"
    competition_intensity: str  # "low", "medium", "high"
    seasonality_factor: float  # Seasonal adjustment factor
    trend_direction: str  # "increasing", "decreasing", "stable"
    market_volatility: float  # Price volatility measure
    inventory_pressure: str  # "low", "medium", "high"


class PricingEngine:
    """Advanced pricing analysis and recommendation engine."""

    def __init__(self):
        """Initialize the pricing engine."""
        self.default_strategy = PricingStrategy(
            strategy_type="competitive",
            target_margin=0.25,
            max_price_change=0.15,  # 15% max change
            min_price_threshold=Decimal("5.00"),
            max_price_threshold=Decimal("1000.00"),
            competitor_weight=0.6,
            market_weight=0.3,
            cost_weight=0.1,
        )

        logger.info("Pricing engine initialized")

    async def analyze_pricing(
        self,
        product_id: ProductIdentifier,
        current_price: Price,
        competitor_prices: List[Price],
        market_metrics: Optional[MarketMetrics] = None,
        strategy: Optional[PricingStrategy] = None,
        cost_data: Optional[Dict[str, Any]] = None,
    ) -> PricingRecommendation:
        """
        Perform comprehensive pricing analysis and generate recommendations.

        Args:
            product_id: Product identifier
            current_price: Current product price
            competitor_prices: List of competitor prices
            market_metrics: Market performance metrics
            strategy: Pricing strategy to use
            cost_data: Product cost information

        Returns:
            PricingRecommendation with analysis and suggested price
        """
        try:
            # Use default strategy if none provided
            if strategy is None:
                strategy = self.default_strategy

            # Analyze market conditions
            market_conditions = self._analyze_market_conditions(
                competitor_prices, market_metrics
            )

            # Calculate competitive analysis
            competitive_analysis = self._analyze_competitors(
                current_price, competitor_prices
            )

            # Generate price recommendation
            recommended_price = self._calculate_recommended_price(
                current_price, competitor_prices, market_conditions, strategy, cost_data
            )

            # Determine price change direction
            price_change_direction = self._determine_price_direction(
                current_price, recommended_price
            )

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                competitor_prices, market_conditions, strategy
            )

            # Generate reasoning
            reasoning = self._generate_pricing_reasoning(
                current_price,
                recommended_price,
                competitive_analysis,
                market_conditions,
                strategy,
            )

            # Estimate impact
            expected_impact = self._estimate_pricing_impact(
                current_price, recommended_price, market_metrics
            )

            return PricingRecommendation(
                product_id=product_id,
                current_price=current_price,
                recommended_price=recommended_price,
                price_change_direction=price_change_direction,
                confidence_score=confidence_score,
                reasoning=reasoning,
                expected_impact=expected_impact,
                market_conditions=self._market_conditions_to_dict(market_conditions),
            )

        except Exception as e:
            logger.error(f"Error in pricing analysis: {e}")
            # Return safe recommendation to maintain current price
            return PricingRecommendation(
                product_id=product_id,
                current_price=current_price,
                recommended_price=current_price,
                price_change_direction=PriceChangeDirection.MAINTAIN,
                confidence_score=0.1,
                reasoning=f"Error in pricing analysis: {e}. Maintaining current price.",
                expected_impact={"error": str(e)},
            )

    def _analyze_market_conditions(
        self, competitor_prices: List[Price], market_metrics: Optional[MarketMetrics]
    ) -> MarketConditions:
        """Analyze current market conditions."""
        # Calculate competition intensity based on price spread
        if len(competitor_prices) >= 2:
            price_amounts = [p.amount for p in competitor_prices]
            price_std = float(statistics.stdev(price_amounts))
            price_mean = float(statistics.mean(price_amounts))
            coefficient_of_variation = price_std / price_mean if price_mean > 0 else 0

            if coefficient_of_variation > 0.2:
                competition_intensity = "high"
                market_volatility = coefficient_of_variation
            elif coefficient_of_variation > 0.1:
                competition_intensity = "medium"
                market_volatility = coefficient_of_variation
            else:
                competition_intensity = "low"
                market_volatility = coefficient_of_variation
        else:
            competition_intensity = "low"
            market_volatility = 0.0

        # Analyze demand based on market metrics
        demand_level = "medium"  # Default
        if market_metrics:
            if market_metrics.conversion_rate and market_metrics.conversion_rate > 15:
                demand_level = "high"
            elif market_metrics.conversion_rate and market_metrics.conversion_rate < 5:
                demand_level = "low"

        # Determine seasonality (simplified)
        current_month = datetime.now().month
        if current_month in [11, 12]:  # Holiday season
            seasonality_factor = 1.2
        elif current_month in [1, 2]:  # Post-holiday
            seasonality_factor = 0.8
        else:
            seasonality_factor = 1.0

        return MarketConditions(
            demand_level=demand_level,
            competition_intensity=competition_intensity,
            seasonality_factor=seasonality_factor,
            trend_direction="stable",  # Would be calculated from historical data
            market_volatility=market_volatility,
            inventory_pressure="medium",  # Would be based on inventory levels
        )

    def _analyze_competitors(
        self, current_price: Price, competitor_prices: List[Price]
    ) -> Dict[str, Any]:
        """Analyze competitive positioning."""
        if not competitor_prices:
            return {
                "position": "unknown",
                "price_advantage": 0.0,
                "competitor_count": 0,
            }

        competitor_amounts = [p.amount for p in competitor_prices]
        min_competitor = min(competitor_amounts)
        max_competitor = max(competitor_amounts)
        avg_competitor = sum(competitor_amounts) / len(competitor_amounts)

        # Calculate position
        position = get_price_position(current_price, competitor_prices)

        # Calculate price advantage (negative means we're more expensive)
        price_advantage = float(
            (avg_competitor - current_price.amount) / avg_competitor * 100
        )

        return {
            "position": position,
            "price_advantage": price_advantage,
            "competitor_count": len(competitor_prices),
            "min_competitor_price": float(min_competitor),
            "max_competitor_price": float(max_competitor),
            "avg_competitor_price": float(avg_competitor),
            "price_spread": float(max_competitor - min_competitor),
        }

    def _calculate_recommended_price(
        self,
        current_price: Price,
        competitor_prices: List[Price],
        market_conditions: MarketConditions,
        strategy: PricingStrategy,
        cost_data: Optional[Dict[str, Any]],
    ) -> Price:
        """Calculate the recommended price based on all factors."""
        if not competitor_prices:
            # No competitors, maintain current price with small adjustment
            adjustment = 1.0 + (market_conditions.seasonality_factor - 1.0) * 0.5
            new_amount = current_price.amount * Decimal(str(adjustment))
        else:
            # Calculate base price from competitors
            competitor_amounts = [p.amount for p in competitor_prices]

            if strategy.strategy_type == "competitive":
                # Price slightly below average
                avg_price = sum(competitor_amounts) / len(competitor_amounts)
                base_price = avg_price * Decimal("0.98")
            elif strategy.strategy_type == "premium":
                # Price above average but below maximum
                avg_price = sum(competitor_amounts) / len(competitor_amounts)
                max_price = max(competitor_amounts)
                base_price = (avg_price + max_price) / 2
            elif strategy.strategy_type == "value":
                # Price below average
                avg_price = sum(competitor_amounts) / len(competitor_amounts)
                base_price = avg_price * Decimal("0.95")
            elif strategy.strategy_type == "penetration":
                # Price at or below minimum
                min_price = min(competitor_amounts)
                base_price = min_price * Decimal("0.99")
            else:
                # Default to competitive
                avg_price = sum(competitor_amounts) / len(competitor_amounts)
                base_price = avg_price * Decimal("0.98")

            # Apply market condition adjustments
            market_adjustment = Decimal(str(market_conditions.seasonality_factor))

            # Demand adjustments
            if market_conditions.demand_level == "high":
                market_adjustment *= Decimal("1.05")
            elif market_conditions.demand_level == "low":
                market_adjustment *= Decimal("0.95")

            # Competition adjustments
            if market_conditions.competition_intensity == "high":
                market_adjustment *= Decimal("0.98")
            elif market_conditions.competition_intensity == "low":
                market_adjustment *= Decimal("1.02")

            new_amount = base_price * market_adjustment

        # Apply constraints
        max_change = strategy.max_price_change
        max_increase = current_price.amount * Decimal(str(1 + max_change))
        max_decrease = current_price.amount * Decimal(str(1 - max_change))

        # Constrain to maximum change
        if new_amount > max_increase:
            new_amount = max_increase
        elif new_amount < max_decrease:
            new_amount = max_decrease

        # Apply absolute thresholds
        if new_amount < strategy.min_price_threshold:
            new_amount = strategy.min_price_threshold
        elif new_amount > strategy.max_price_threshold:
            new_amount = strategy.max_price_threshold

        # Round to reasonable precision
        new_amount = new_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return Price(
            amount=new_amount,
            currency=current_price.currency,
            marketplace=current_price.marketplace,
        )

    def _determine_price_direction(
        self, current_price: Price, recommended_price: Price
    ) -> PriceChangeDirection:
        """Determine the direction of price change."""
        change_percent = calculate_price_change_percentage(
            current_price, recommended_price
        )

        if abs(change_percent) < 1.0:  # Less than 1% change
            return PriceChangeDirection.MAINTAIN
        elif change_percent > 0:
            return PriceChangeDirection.INCREASE
        else:
            return PriceChangeDirection.DECREASE

    def _calculate_confidence_score(
        self,
        competitor_prices: List[Price],
        market_conditions: MarketConditions,
        strategy: PricingStrategy,
    ) -> float:
        """Calculate confidence score for the recommendation."""
        base_confidence = 0.7

        # More competitors = higher confidence
        if len(competitor_prices) >= 5:
            base_confidence += 0.2
        elif len(competitor_prices) >= 3:
            base_confidence += 0.1
        elif len(competitor_prices) == 0:
            base_confidence -= 0.3

        # Lower volatility = higher confidence
        if market_conditions.market_volatility < 0.1:
            base_confidence += 0.1
        elif market_conditions.market_volatility > 0.3:
            base_confidence -= 0.2

        # Stable market conditions = higher confidence
        if market_conditions.competition_intensity == "medium":
            base_confidence += 0.05
        elif market_conditions.competition_intensity == "high":
            base_confidence -= 0.1

        return max(0.1, min(1.0, base_confidence))

    def _generate_pricing_reasoning(
        self,
        current_price: Price,
        recommended_price: Price,
        competitive_analysis: Dict[str, Any],
        market_conditions: MarketConditions,
        strategy: PricingStrategy,
    ) -> str:
        """Generate human-readable reasoning for the pricing recommendation."""
        reasoning_parts = []

        # Price change information
        change_percent = calculate_price_change_percentage(
            current_price, recommended_price
        )
        if abs(change_percent) < 1.0:
            reasoning_parts.append(
                "Maintaining current price due to stable market conditions"
            )
        elif change_percent > 0:
            reasoning_parts.append(f"Recommending {change_percent:.1f}% price increase")
        else:
            reasoning_parts.append(
                f"Recommending {abs(change_percent):.1f}% price decrease"
            )

        # Competitive positioning
        position = competitive_analysis.get("position", "unknown")
        if position == "lowest":
            reasoning_parts.append("Currently priced lowest among competitors")
        elif position == "highest":
            reasoning_parts.append("Currently priced highest among competitors")
        elif position == "below_average":
            reasoning_parts.append("Currently priced below competitor average")
        elif position == "above_average":
            reasoning_parts.append("Currently priced above competitor average")

        # Market conditions
        if market_conditions.demand_level == "high":
            reasoning_parts.append("High demand supports premium pricing")
        elif market_conditions.demand_level == "low":
            reasoning_parts.append("Low demand suggests competitive pricing")

        if market_conditions.competition_intensity == "high":
            reasoning_parts.append("High competition requires aggressive pricing")
        elif market_conditions.competition_intensity == "low":
            reasoning_parts.append("Low competition allows for premium pricing")

        # Seasonality
        if market_conditions.seasonality_factor > 1.1:
            reasoning_parts.append("Seasonal demand supports higher pricing")
        elif market_conditions.seasonality_factor < 0.9:
            reasoning_parts.append("Seasonal factors suggest lower pricing")

        # Strategy
        reasoning_parts.append(f"Using {strategy.strategy_type} pricing strategy")

        return ". ".join(reasoning_parts) + "."

    def _estimate_pricing_impact(
        self,
        current_price: Price,
        recommended_price: Price,
        market_metrics: Optional[MarketMetrics],
    ) -> Dict[str, Any]:
        """Estimate the impact of the pricing change."""
        change_percent = calculate_price_change_percentage(
            current_price, recommended_price
        )

        # Simplified impact estimation
        # In reality, this would use historical data and elasticity models

        estimated_impact = {
            "price_change_percent": round(change_percent, 2),
            "estimated_sales_impact_percent": round(
                -change_percent * 1.5, 2
            ),  # Price elasticity
            "estimated_revenue_impact_percent": round(change_percent * 0.5, 2),
            "estimated_profit_impact_percent": round(change_percent * 2.0, 2),
        }

        if market_metrics:
            # More detailed impact if we have metrics
            current_units = market_metrics.units_sold or 0
            estimated_new_units = current_units * (
                1 + estimated_impact["estimated_sales_impact_percent"] / 100
            )

            estimated_impact.update(
                {
                    "current_units_sold": current_units,
                    "estimated_new_units_sold": round(estimated_new_units),
                    "current_revenue": float(market_metrics.revenue or 0),
                    "estimated_new_revenue": round(
                        float(recommended_price.amount) * estimated_new_units, 2
                    ),
                }
            )

        return estimated_impact

    def _market_conditions_to_dict(
        self, conditions: MarketConditions
    ) -> Dict[str, Any]:
        """Convert MarketConditions to dictionary."""
        return {
            "demand_level": conditions.demand_level,
            "competition_intensity": conditions.competition_intensity,
            "seasonality_factor": conditions.seasonality_factor,
            "trend_direction": conditions.trend_direction,
            "market_volatility": conditions.market_volatility,
            "inventory_pressure": conditions.inventory_pressure,
        }

    def create_pricing_strategy(
        self,
        strategy_type: str,
        target_margin: float,
        max_price_change: float = 0.15,
        min_price: float = 5.00,
        max_price: float = 1000.00,
    ) -> PricingStrategy:
        """Create a custom pricing strategy."""
        return PricingStrategy(
            strategy_type=strategy_type,
            target_margin=target_margin,
            max_price_change=max_price_change,
            min_price_threshold=Decimal(str(min_price)),
            max_price_threshold=Decimal(str(max_price)),
        )
