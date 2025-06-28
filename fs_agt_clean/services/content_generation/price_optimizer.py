"""
Dynamic price optimization based on market trends and competitor analysis.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..market_analysis import CompetitorProfile, MarketAnalyzer, TrendData

logger = logging.getLogger(__name__)


@dataclass
class PriceRange:
    """Price range with confidence score."""

    min_price: float
    max_price: float
    optimal_price: float
    confidence: float


@dataclass
class PricingStrategy:
    """Pricing strategy details."""

    position: str  # premium, competitive, value
    rationale: List[str]
    market_factors: Dict[str, float]
    confidence: float


class PriceOptimizer:
    """Dynamic price optimization engine."""

    def __init__(
        self,
        market_analyzer: MarketAnalyzer,
        min_confidence: float = 0.7,
        max_premium_factor: float = 1.5,
        min_margin_factor: float = 1.1,
    ):
        self.market_analyzer = market_analyzer
        self.min_confidence = min_confidence
        self.max_premium_factor = max_premium_factor
        self.min_margin_factor = min_margin_factor

    async def optimize_price(
        self,
        product_data: Dict,
        market_trends: List[TrendData],
        competitors: List[CompetitorProfile],
        cost_basis: float,
    ) -> Tuple[PriceRange, PricingStrategy]:
        """Optimize price based on market conditions."""
        try:
            # Analyze market position
            strategy = self._determine_pricing_strategy(
                market_trends, competitors, product_data
            )

            # Calculate base price range
            base_range = self._calculate_base_range(competitors, cost_basis)

            # Adjust for market trends
            trend_adjusted = self._adjust_for_trends(base_range, market_trends)

            # Apply strategy adjustments
            final_range = self._apply_strategy_adjustments(
                trend_adjusted, strategy, cost_basis
            )

            # Validate final price
            final_range = self._validate_price_range(final_range, cost_basis)

            return final_range, strategy

        except Exception as e:
            logger.error("Failed to optimize price: %s", str(e))
            raise

    def _determine_pricing_strategy(
        self,
        market_trends: List[TrendData],
        competitors: List[CompetitorProfile],
        product_data: Dict,
    ) -> PricingStrategy:
        """Determine optimal pricing strategy."""
        market_factors = {}
        rationale = []

        # Analyze demand trends
        demand_score = self._analyze_demand_trends(market_trends)
        market_factors["demand_strength"] = demand_score

        if demand_score > 0.8:
            rationale.append("Strong market demand supports premium pricing")
        elif demand_score < 0.3:
            rationale.append("Weak demand suggests competitive pricing")

        # Analyze competition
        competition_score = self._analyze_competition(competitors)
        market_factors["competition_intensity"] = competition_score

        if competition_score > 0.7:
            rationale.append("High competition requires competitive pricing")
        elif competition_score < 0.3:
            rationale.append("Low competition allows premium positioning")

        # Analyze product differentiation
        diff_score = self._analyze_differentiation(product_data, competitors)
        market_factors["differentiation"] = diff_score

        if diff_score > 0.7:
            rationale.append("Strong differentiation supports premium pricing")
        elif diff_score < 0.3:
            rationale.append("Limited differentiation suggests value pricing")

        # Determine position
        position = self._calculate_position(market_factors)

        # Add position-specific rationale
        if position == "competitive":
            rationale.append(
                "Market conditions favor competitive pricing to maintain market share"
            )
        elif position == "premium":
            rationale.append("Strong market position supports premium pricing strategy")
        else:  # value
            rationale.append("Market conditions suggest value-based pricing approach")

        confidence = self._calculate_strategy_confidence(market_factors)

        return PricingStrategy(
            position=position,
            rationale=rationale,
            market_factors=market_factors,
            confidence=confidence,
        )

    def _calculate_base_range(
        self, competitors: List[CompetitorProfile], cost_basis: float
    ) -> PriceRange:
        """Calculate base price range from competitor data."""
        competitor_prices = []
        for comp in competitors:
            if hasattr(comp, "price"):
                competitor_prices.append(comp.price)

        if not competitor_prices:
            # Fallback if no competitor prices
            return PriceRange(
                min_price=cost_basis * self.min_margin_factor,
                max_price=cost_basis * self.max_premium_factor,
                optimal_price=cost_basis * 1.3,  # Default markup
                confidence=0.5,
            )

        min_price = max(
            np.percentile(competitor_prices, 25), cost_basis * self.min_margin_factor
        )
        max_price = min(
            np.percentile(competitor_prices, 75), cost_basis * self.max_premium_factor
        )
        optimal_price = np.median(competitor_prices)

        return PriceRange(
            min_price=min_price,
            max_price=max_price,
            optimal_price=optimal_price,
            confidence=self._calculate_range_confidence(competitor_prices),
        )

    def _adjust_for_trends(
        self, base_range: PriceRange, market_trends: List[TrendData]
    ) -> PriceRange:
        """Adjust price range based on market trends."""
        adjustment_factor = 1.0
        confidence_impact = 0.0

        for trend in market_trends:
            if trend.trend_type == "price":
                if trend.direction == "up":
                    adjustment_factor += 0.1 * trend.strength * trend.confidence
                elif trend.direction == "down":
                    adjustment_factor -= 0.1 * trend.strength * trend.confidence
                confidence_impact += trend.confidence

        # Apply adjustments
        return PriceRange(
            min_price=base_range.min_price * adjustment_factor,
            max_price=base_range.max_price * adjustment_factor,
            optimal_price=base_range.optimal_price * adjustment_factor,
            confidence=self._combine_confidence(
                base_range.confidence,
                confidence_impact / len(market_trends) if market_trends else 0,
            ),
        )

    def _apply_strategy_adjustments(
        self, price_range: PriceRange, strategy: PricingStrategy, cost_basis: float
    ) -> PriceRange:
        """Apply strategic pricing adjustments."""
        if strategy.position == "premium":
            optimal_price = (
                price_range.max_price * 0.8 + price_range.optimal_price * 0.2
            )
        elif strategy.position == "value":
            optimal_price = (
                price_range.min_price * 0.8 + price_range.optimal_price * 0.2
            )
        else:  # competitive
            optimal_price = price_range.optimal_price

        # Ensure minimum margin
        optimal_price = max(optimal_price, cost_basis * self.min_margin_factor)

        return PriceRange(
            min_price=price_range.min_price,
            max_price=price_range.max_price,
            optimal_price=optimal_price,
            confidence=self._combine_confidence(
                price_range.confidence, strategy.confidence
            ),
        )

    def _validate_price_range(
        self, price_range: PriceRange, cost_basis: float
    ) -> PriceRange:
        """Validate and adjust price range."""
        # Ensure minimum margin
        min_price = max(price_range.min_price, cost_basis * self.min_margin_factor)

        # Ensure maximum premium
        max_price = min(price_range.max_price, cost_basis * self.max_premium_factor)

        # Adjust optimal price if needed
        optimal_price = min(max(price_range.optimal_price, min_price), max_price)

        return PriceRange(
            min_price=min_price,
            max_price=max_price,
            optimal_price=optimal_price,
            confidence=price_range.confidence,
        )

    def _analyze_demand_trends(self, market_trends: List[TrendData]) -> float:
        """Analyze demand trends for pricing impact."""
        demand_score = 0.5  # Neutral baseline
        relevant_trends = 0

        for trend in market_trends:
            if trend.trend_type == "demand":
                if trend.direction == "up":
                    demand_score += 0.1 * trend.strength * trend.confidence
                elif trend.direction == "down":
                    demand_score -= 0.1 * trend.strength * trend.confidence
                relevant_trends += 1

        if relevant_trends > 0:
            demand_score = min(max(demand_score, 0.0), 1.0)
            return demand_score
        return 0.5  # Neutral if no relevant trends

    def _analyze_competition(self, competitors: List[CompetitorProfile]) -> float:
        """Analyze competition intensity."""
        if not competitors:
            return 0.3  # Low competition if no competitors

        # Count high-threat competitors
        high_threat = sum(1 for c in competitors if c.threat_level == "high")
        med_threat = sum(1 for c in competitors if c.threat_level == "medium")

        # Calculate competition score
        competition_score = (high_threat * 0.5 + med_threat * 0.3) / len(competitors)

        return min(competition_score, 1.0)

    def _analyze_differentiation(
        self, product_data: Dict, competitors: List[CompetitorProfile]
    ) -> float:
        """Analyze product differentiation based on features and brand."""
        # Count premium features
        product_features = set(product_data.get("features", []))
        premium_features = sum(1 for f in product_features if "premium" in f.lower())

        # Compare against competitors
        competitor_features = set()
        for comp in competitors:
            comp_features = set(comp.metadata.get("features", []))
            competitor_features.update(comp_features)

        unique_features = len(product_features - competitor_features)
        total_features = len(product_features)

        # Calculate differentiation score
        feature_score = (unique_features + premium_features) / max(total_features, 1)
        brand_score = 1.0 if "premium" in product_data.get("brand", "").lower() else 0.0

        return min(1.0, (feature_score * 0.7 + brand_score * 0.3))

    def _calculate_position(self, market_factors: Dict[str, float]) -> str:
        """Calculate pricing position based on market factors."""
        competition = market_factors["competition_intensity"]
        differentiation = market_factors["differentiation"]
        demand = market_factors["demand_strength"]

        # Premium position if high differentiation and manageable competition
        if differentiation > 0.6 and competition < 0.5:
            return "premium"

        # Competitive position if high competition or low differentiation
        if competition > 0.5 or differentiation < 0.4:
            return "competitive"

        # Value position as default when no strong factors
        return "value"

    def _calculate_strategy_confidence(self, market_factors: Dict[str, float]) -> float:
        """Calculate confidence in pricing strategy."""
        # Weight the factors based on importance
        weights = {
            "competition_intensity": 0.4,
            "differentiation": 0.4,
            "demand_strength": 0.2,
        }

        confidence = sum(
            market_factors[factor] * weight for factor, weight in weights.items()
        )

        # Boost confidence if factors align well
        if (
            abs(
                market_factors["competition_intensity"]
                - market_factors["differentiation"]
            )
            < 0.2
        ):
            confidence *= 1.2

        return min(1.0, confidence)

    def _calculate_range_confidence(self, prices: List[float]) -> float:
        """Calculate confidence in price range."""
        if len(prices) < 3:
            return 0.7  # Default to minimum confidence with few data points

        # Calculate coefficient of variation
        cv = np.std(prices) / np.mean(prices)

        # Convert to confidence score (lower variance = higher confidence)
        # Further reduce impact of variance and increase base confidence
        base_confidence = 1.0 - min(cv * 0.3, 0.3)  # Reduce impact of variance

        # Boost confidence based on number of data points and market factors
        data_boost = min(1.2, (len(prices) + 2) / 5)  # Data points boost
        market_boost = 1.1  # Additional market confidence boost

        confidence = base_confidence * data_boost * market_boost

        # Ensure minimum confidence
        return max(confidence, self.min_confidence)

    def _combine_confidence(self, confidence1: float, confidence2: float) -> float:
        """Combine two confidence scores."""
        # Weighted average of confidence scores
        return 0.7 * confidence1 + 0.3 * confidence2
