"""
Competitor Monitor for tracking and analyzing competitor behavior.

This module provides comprehensive competitor monitoring capabilities including
price tracking, strategy analysis, and competitive intelligence.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fs_agt_clean.core.analysis.models import (
    CompetitorData,
    CompetitorRank,
    MarketSegment,
    PricePoint,
)

logger = logging.getLogger(__name__)


class CompetitorMonitor:
    """
    Monitor and analyze competitor behavior in the marketplace.

    This class provides functionality to track competitor pricing, detect
    price changes, and analyze competitive strategies.
    """

    def __init__(self, config: Optional[Dict[str, Union[int, float, str]]] = None):
        """
        Initialize the competitor monitor.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.price_change_threshold = self.config.get("price_change_threshold", 0.05)
        self.price_history_days = self.config.get("price_history_days", 30)
        self.competitor_cache: Dict[str, Dict[str, CompetitorData]] = {}
        self.cache_ttl_hours = self.config.get("cache_ttl_hours", 6)

    async def monitor_competitors(
        self,
        product_id: str,
        marketplace: str,
        competitor_ids: Optional[List[str]] = None,
    ) -> List[CompetitorData]:
        """
        Monitor competitors for a specific product in a marketplace.

        Args:
            product_id: ID of the product to monitor
            marketplace: Marketplace to monitor
            competitor_ids: Optional list of specific competitor IDs

        Returns:
            List of CompetitorData objects with current competitor information
        """
        # Check cache first
        cache_key = f"{marketplace}_{product_id}"
        if cache_key in self.competitor_cache:
            # Check if cache is still valid
            cache_age = datetime.now() - self.competitor_cache[cache_key].get(
                "_cache_timestamp", datetime.min
            )
            if cache_age.total_seconds() < self.cache_ttl_hours * 3600:
                return list(self.competitor_cache[cache_key].values())

        # Fetch fresh competitor data
        competitors = await self._fetch_competitor_data(
            product_id, marketplace, competitor_ids
        )

        # Calculate market shares
        total_products = sum(c.product_count for c in competitors)
        for competitor in competitors:
            if total_products > 0:
                competitor.market_share = competitor.product_count / total_products
            else:
                competitor.market_share = 0.0

        # Assign competitive ranks
        for competitor in competitors:
            competitor.rank = self._determine_competitor_rank(competitor, competitors)

        # Cache results
        competitor_dict = {c.competitor_id: c for c in competitors}
        competitor_dict["_cache_timestamp"] = datetime.now()
        self.competitor_cache[cache_key] = competitor_dict

        return competitors

    async def _fetch_competitor_data(
        self,
        product_id: str,
        marketplace: str,
        competitor_ids: Optional[List[str]] = None,
    ) -> List[CompetitorData]:
        """
        Fetch competitor data from marketplace.

        Args:
            product_id: ID of the product
            marketplace: Marketplace to fetch from
            competitor_ids: Optional list of specific competitor IDs

        Returns:
            List of CompetitorData objects
        """
        # In a real implementation, this would call marketplace APIs
        # For this example, we'll generate mock data

        # Mock competitor data
        mock_competitors = []

        # Number of competitors to generate
        num_competitors = min(10, len(competitor_ids) if competitor_ids else 10)

        for i in range(num_competitors):
            competitor_id = (
                competitor_ids[i]
                if competitor_ids and i < len(competitor_ids)
                else f"comp_{i+1}"
            )

            # Generate price history
            price_history = self._generate_price_history(
                base_price=50.0 + (i * 5),  # Different price points
                days=self.price_history_days,
            )

            # Calculate price statistics
            prices = [p.price for p in price_history]
            avg_price = sum(prices) / len(prices) if prices else 0.0
            min_price = min(prices) if prices else 0.0
            max_price = max(prices) if prices else 0.0

            # Determine market segments
            segments = self._determine_segments(avg_price, min_price, max_price)

            # Create competitor data
            competitor = CompetitorData(
                competitor_id=competitor_id,
                name=f"Competitor {i+1}",
                market_share=0.0,  # Will be calculated later
                rank=CompetitorRank.FOLLOWER,  # Will be assigned later
                price_history=price_history,
                average_price=avg_price,
                min_price=min_price,
                max_price=max_price,
                product_count=100 - (i * 10),  # Decreasing counts
                rating=4.5 - (i * 0.2),  # Decreasing ratings
                review_count=500 - (i * 50),  # Decreasing review counts
                segments=segments,
                last_updated=datetime.now(),
            )

            mock_competitors.append(competitor)

        return mock_competitors

    def _generate_price_history(self, base_price: float, days: int) -> List[PricePoint]:
        """
        Generate mock price history data.

        Args:
            base_price: Base price to generate history around
            days: Number of days of history to generate

        Returns:
            List of PricePoint objects
        """
        import random

        price_history = []
        current_price = base_price

        # Generate a price point for each day
        for day in range(days, 0, -1):
            # Add some random variation
            price_change = random.uniform(-0.05, 0.05) * current_price
            current_price = max(0.01, current_price + price_change)

            # Create price point
            price_point = PricePoint(
                price=round(current_price, 2),
                timestamp=datetime.now() - timedelta(days=day),
                source="mock_data",
                currency="USD",
            )

            price_history.append(price_point)

        return price_history

    def _determine_segments(
        self, avg_price: float, min_price: float, max_price: float
    ) -> List[MarketSegment]:
        """
        Determine market segments based on pricing.

        Args:
            avg_price: Average price
            min_price: Minimum price
            max_price: Maximum price

        Returns:
            List of MarketSegment enum values
        """
        segments = []

        # Simple segmentation based on average price
        if avg_price < 30.0:
            segments.append(MarketSegment.BUDGET)
        elif avg_price < 70.0:
            segments.append(MarketSegment.MID_RANGE)
        elif avg_price < 150.0:
            segments.append(MarketSegment.PREMIUM)
        else:
            segments.append(MarketSegment.LUXURY)

        # Add secondary segment if price range is wide
        price_range = max_price - min_price
        if price_range > 20.0:
            if min_price < 30.0 and MarketSegment.BUDGET not in segments:
                segments.append(MarketSegment.BUDGET)
            if max_price > 70.0 and MarketSegment.PREMIUM not in segments:
                segments.append(MarketSegment.PREMIUM)

        return segments

    def _determine_competitor_rank(
        self, competitor: CompetitorData, all_competitors: List[CompetitorData]
    ) -> CompetitorRank:
        """
        Determine the competitive rank of a competitor.

        Args:
            competitor: Competitor to rank
            all_competitors: List of all competitors for comparison

        Returns:
            CompetitorRank enum value
        """
        # Sort competitors by product count (proxy for sales volume)
        sorted_competitors = sorted(
            all_competitors, key=lambda c: c.product_count, reverse=True
        )

        # Calculate total product count
        total_products = sum(c.product_count for c in all_competitors)

        if total_products == 0:
            return CompetitorRank.FOLLOWER

        # Calculate market share
        market_share = competitor.product_count / total_products

        # Determine rank based on position and market share
        if competitor == sorted_competitors[0] and market_share > 0.25:
            return CompetitorRank.LEADER
        elif market_share > 0.15:
            return CompetitorRank.CHALLENGER
        elif market_share < 0.05:
            return CompetitorRank.NICHE
        else:
            return CompetitorRank.FOLLOWER

    async def detect_price_changes(
        self, competitor_id: str, product_id: str, marketplace: str, days: int = 30
    ) -> Dict[str, Union[bool, float, datetime]]:
        """
        Detect significant price changes for a competitor.

        Args:
            competitor_id: ID of the competitor
            product_id: ID of the product
            marketplace: Marketplace to check
            days: Number of days to analyze

        Returns:
            Dictionary with price change information
        """
        # Get competitor data
        cache_key = f"{marketplace}_{product_id}"
        if cache_key not in self.competitor_cache:
            await self.monitor_competitors(product_id, marketplace)

        if (
            cache_key not in self.competitor_cache
            or competitor_id not in self.competitor_cache[cache_key]
        ):
            return {
                "has_price_change": False,
                "change_percent": 0.0,
                "last_change_date": datetime.now(),
            }

        competitor = self.competitor_cache[cache_key][competitor_id]

        # Filter price history to requested timeframe
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_prices = [
            p for p in competitor.price_history if p.timestamp >= cutoff_date
        ]

        if len(recent_prices) < 2:
            return {
                "has_price_change": False,
                "change_percent": 0.0,
                "last_change_date": datetime.now(),
            }

        # Sort by timestamp
        recent_prices.sort(key=lambda p: p.timestamp)

        # Calculate overall change
        first_price = recent_prices[0].price
        last_price = recent_prices[-1].price

        if first_price == 0:
            change_percent = 0.0
        else:
            change_percent = (last_price - first_price) / first_price

        # Detect significant changes
        has_significant_change = abs(change_percent) >= self.price_change_threshold

        # Find date of last significant change
        last_change_date = recent_prices[-1].timestamp
        for i in range(len(recent_prices) - 1, 0, -1):
            curr_price = recent_prices[i].price
            prev_price = recent_prices[i - 1].price

            if prev_price == 0:
                continue

            change = abs((curr_price - prev_price) / prev_price)

            if change >= self.price_change_threshold:
                last_change_date = recent_prices[i].timestamp
                break

        return {
            "has_price_change": has_significant_change,
            "change_percent": change_percent,
            "last_change_date": last_change_date,
        }

    async def analyze_pricing_strategy(
        self, competitor_id: str, product_id: str, marketplace: str
    ) -> Dict[str, Union[str, float, List[Dict[str, Union[str, float]]]]]:
        """
        Analyze the pricing strategy of a competitor.

        Args:
            competitor_id: ID of the competitor
            product_id: ID of the product
            marketplace: Marketplace to analyze

        Returns:
            Dictionary with pricing strategy analysis
        """
        # Get competitor data
        cache_key = f"{marketplace}_{product_id}"
        if cache_key not in self.competitor_cache:
            await self.monitor_competitors(product_id, marketplace)

        if (
            cache_key not in self.competitor_cache
            or competitor_id not in self.competitor_cache[cache_key]
        ):
            return {"strategy": "unknown", "confidence": 0.0, "patterns": []}

        competitor = self.competitor_cache[cache_key][competitor_id]

        # Analyze price history
        if not competitor.price_history or len(competitor.price_history) < 5:
            return {"strategy": "insufficient_data", "confidence": 0.0, "patterns": []}

        # Sort by timestamp
        prices = sorted(competitor.price_history, key=lambda p: p.timestamp)

        # Calculate price changes
        changes = []
        for i in range(1, len(prices)):
            prev_price = prices[i - 1].price
            curr_price = prices[i].price

            if prev_price == 0:
                continue

            change_percent = (curr_price - prev_price) / prev_price
            changes.append(
                {
                    "date": prices[i].timestamp,
                    "change": change_percent,
                    "price": curr_price,
                }
            )

        # Analyze patterns
        patterns = []

        # Check for consistent undercutting
        if self._is_undercutting(competitor, self.competitor_cache[cache_key].values()):
            patterns.append(
                {
                    "type": "undercutting",
                    "description": "Consistently prices below competitors",
                    "confidence": 0.8,
                }
            )

        # Check for price skimming
        if self._is_price_skimming(changes):
            patterns.append(
                {
                    "type": "price_skimming",
                    "description": "Starts high and gradually reduces price",
                    "confidence": 0.7,
                }
            )

        # Check for penetration pricing
        if self._is_penetration_pricing(changes):
            patterns.append(
                {
                    "type": "penetration_pricing",
                    "description": "Starts low and gradually increases price",
                    "confidence": 0.7,
                }
            )

        # Check for promotional pricing
        if self._is_promotional_pricing(changes):
            patterns.append(
                {
                    "type": "promotional_pricing",
                    "description": "Temporary price reductions followed by returns to higher price",
                    "confidence": 0.6,
                }
            )

        # Determine overall strategy
        if not patterns:
            return {"strategy": "stable_pricing", "confidence": 0.5, "patterns": []}

        # Sort patterns by confidence
        patterns.sort(key=lambda p: p.get("confidence", 0), reverse=True)

        return {
            "strategy": patterns[0]["type"],
            "confidence": patterns[0]["confidence"],
            "patterns": patterns,
        }

    def _is_undercutting(
        self, competitor: CompetitorData, all_competitors: List[CompetitorData]
    ) -> bool:
        """
        Check if competitor is consistently undercutting others.

        Args:
            competitor: Competitor to check
            all_competitors: All competitors for comparison

        Returns:
            True if undercutting, False otherwise
        """
        # Need at least 3 competitors for meaningful comparison
        if len(all_competitors) < 3:
            return False

        # Calculate average price of other competitors
        other_prices = [
            c.average_price
            for c in all_competitors
            if c.competitor_id != competitor.competitor_id
        ]

        if not other_prices:
            return False

        avg_other_price = sum(other_prices) / len(other_prices)

        # Check if consistently below average
        return competitor.average_price < avg_other_price * 0.95

    def _is_price_skimming(
        self, price_changes: List[Dict[str, Union[datetime, float]]]
    ) -> bool:
        """
        Check if price changes follow a skimming pattern (high to low).

        Args:
            price_changes: List of price change data

        Returns:
            True if skimming pattern detected, False otherwise
        """
        if len(price_changes) < 3:
            return False

        # Count decreases vs increases
        decreases = sum(1 for c in price_changes if c["change"] < -0.02)
        increases = sum(1 for c in price_changes if c["change"] > 0.02)

        # Price skimming has more decreases than increases
        return decreases > increases * 2

    def _is_penetration_pricing(
        self, price_changes: List[Dict[str, Union[datetime, float]]]
    ) -> bool:
        """
        Check if price changes follow a penetration pattern (low to high).

        Args:
            price_changes: List of price change data

        Returns:
            True if penetration pattern detected, False otherwise
        """
        if len(price_changes) < 3:
            return False

        # Count decreases vs increases
        decreases = sum(1 for c in price_changes if c["change"] < -0.02)
        increases = sum(1 for c in price_changes if c["change"] > 0.02)

        # Penetration pricing has more increases than decreases
        return increases > decreases * 2

    def _is_promotional_pricing(
        self, price_changes: List[Dict[str, Union[datetime, float]]]
    ) -> bool:
        """
        Check if price changes follow a promotional pattern (temporary drops).

        Args:
            price_changes: List of price change data

        Returns:
            True if promotional pattern detected, False otherwise
        """
        if len(price_changes) < 4:
            return False

        # Look for patterns of drop followed by increase
        patterns = 0

        for i in range(len(price_changes) - 1):
            current_change = price_changes[i]["change"]
            next_change = price_changes[i + 1]["change"]

            # Significant drop followed by increase
            if current_change < -0.05 and next_change > 0.03:
                patterns += 1

        # Need at least 2 promotional patterns
        return patterns >= 2
