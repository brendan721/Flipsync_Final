"""
Market Analyzer for comprehensive market analysis.

This module provides a comprehensive market analysis system that combines
trend analysis, competitor monitoring, and demand forecasting to provide
actionable market insights.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.analysis.competitor_monitor import CompetitorMonitor
from fs_agt_clean.core.analysis.demand_forecaster import DemandForecaster
from fs_agt_clean.core.analysis.models import (
    CompetitorData,
    DemandForecast,
    MarketMetrics,
    MarketSegment,
    MarketTrend,
)
from fs_agt_clean.core.analysis.trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """
    Comprehensive market analysis system.

    This class combines trend analysis, competitor monitoring, and demand
    forecasting to provide actionable market insights.
    """

    def __init__(self, config: Optional[Dict[str, Union[int, float, str]]] = None):
        """
        Initialize the market analyzer.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.trend_analyzer = TrendAnalyzer(config)
        self.competitor_monitor = CompetitorMonitor(config)
        self.demand_forecaster = DemandForecaster(config)
        self.analysis_cache: Dict[str, Dict[str, Union[MarketMetrics, datetime]]] = {}
        self.cache_ttl_hours = self.config.get("cache_ttl_hours", 24)

    async def analyze_market_trends(
        self,
        category_id: str,
        timeframe_days: int = 90,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, MarketTrend]:
        """
        Analyze trends in a specific market category.

        Args:
            category_id: ID of the category to analyze
            timeframe_days: Number of days of data to analyze
            metrics: Optional list of specific metrics to analyze

        Returns:
            Dictionary mapping metric names to MarketTrend objects
        """
        # Default metrics if not specified
        if not metrics:
            metrics = [
                "price",
                "sales_volume",
                "listing_count",
                "search_volume",
                "conversion_rate",
            ]

        # Get historical data for each metric
        metric_data = await self._get_metric_data(category_id, metrics, timeframe_days)

        # Analyze trends for each metric
        trends = {}

        for metric_name, data in metric_data.items():
            if not data:
                continue

            # Sort by date
            data.sort(key=lambda x: x[0])

            # Extract dates and values
            dates = [entry[0] for entry in data]
            values = [entry[1] for entry in data]

            # Analyze trend
            trend = await self.trend_analyzer.analyze_trend(values, dates, metric_name)
            trends[metric_name] = trend

        return trends

    async def monitor_competitors(
        self,
        product_id: str,
        marketplace: str,
        competitor_ids: Optional[List[str]] = None,
    ) -> Dict[str, Union[List[CompetitorData], Dict[str, Union[str, float]]]]:
        """
        Monitor competitor pricing and strategies.

        Args:
            product_id: ID of the product to monitor
            marketplace: Marketplace to monitor
            competitor_ids: Optional list of specific competitor IDs

        Returns:
            Dictionary with competitor analysis results
        """
        # Get competitor data
        competitors = await self.competitor_monitor.monitor_competitors(
            product_id, marketplace, competitor_ids
        )

        # Analyze pricing strategies for top competitors
        top_competitors = sorted(
            competitors, key=lambda c: c.market_share, reverse=True
        )[
            :5
        ]  # Top 5 competitors

        pricing_strategies = {}

        for competitor in top_competitors:
            strategy = await self.competitor_monitor.analyze_pricing_strategy(
                competitor.competitor_id, product_id, marketplace
            )
            pricing_strategies[competitor.competitor_id] = strategy

        # Calculate market concentration
        market_concentration = self._calculate_market_concentration(competitors)

        # Calculate price distribution
        price_distribution = self._calculate_price_distribution(competitors)

        return {
            "competitors": competitors,
            "pricing_strategies": pricing_strategies,
            "market_concentration": market_concentration,
            "price_distribution": price_distribution,
        }

    async def forecast_demand(
        self,
        product_id: Optional[str] = None,
        category_id: Optional[str] = None,
        timeframe_days: int = 30,
        external_factors: Optional[Dict[str, float]] = None,
    ) -> DemandForecast:
        """
        Forecast demand for a product or category.

        Args:
            product_id: Optional ID of the product
            category_id: Optional ID of the category
            timeframe_days: Number of days to forecast
            external_factors: Optional external factors affecting demand

        Returns:
            DemandForecast object with forecast results

        Raises:
            ValueError: If neither product_id nor category_id is provided
        """
        # Delegate to demand forecaster
        return await self.demand_forecaster.forecast_demand(
            product_id=product_id,
            category_id=category_id,
            timeframe_days=timeframe_days,
            external_factors=external_factors,
        )

    async def analyze_market(
        self,
        category_id: str,
        marketplace: str,
        timeframe_days: int = 90,
        include_competitors: bool = True,
        include_forecast: bool = True,
    ) -> MarketMetrics:
        """
        Perform comprehensive market analysis for a category.

        Args:
            category_id: ID of the category to analyze
            marketplace: Marketplace to analyze
            timeframe_days: Number of days of data to analyze
            include_competitors: Whether to include competitor analysis
            include_forecast: Whether to include demand forecast

        Returns:
            MarketMetrics object with comprehensive market analysis
        """
        # Check cache
        cache_key = f"{marketplace}_{category_id}"
        if cache_key in self.analysis_cache:
            cache_entry = self.analysis_cache[cache_key]
            cache_age = datetime.now() - cache_entry["timestamp"]

            if cache_age.total_seconds() < self.cache_ttl_hours * 3600:
                return cache_entry["metrics"]

        # Get market data
        market_data = await self._get_market_data(category_id, marketplace)

        # Analyze trends
        trends = await self.analyze_market_trends(
            category_id, timeframe_days=timeframe_days
        )

        # Get competitor data if requested
        top_competitors = []
        if include_competitors:
            competitor_results = await self.monitor_competitors(
                category_id, marketplace
            )
            top_competitors = competitor_results["competitors"][:10]  # Top 10

        # Get demand forecast if requested
        demand_forecast = None
        if include_forecast:
            demand_forecast = await self.forecast_demand(
                category_id=category_id, timeframe_days=timeframe_days
            )

        # Calculate market segments
        market_segments = self._calculate_market_segments(top_competitors)

        # Calculate opportunity score
        opportunity_score = self._calculate_opportunity_score(
            market_data, trends, top_competitors, demand_forecast
        )

        # Calculate competition level
        competition_level = self._calculate_competition_level(
            market_data, top_competitors
        )

        # Create market metrics
        metrics = MarketMetrics(
            category_id=category_id,
            total_listings=market_data.get("total_listings", 0),
            active_listings=market_data.get("active_listings", 0),
            average_price=market_data.get("average_price", 0.0),
            price_range={
                "min": market_data.get("min_price", 0.0),
                "max": market_data.get("max_price", 0.0),
                "median": market_data.get("median_price", 0.0),
            },
            sales_velocity=market_data.get("sales_velocity", 0.0),
            market_size=market_data.get("market_size", 0.0),
            growth_rate=market_data.get("growth_rate", 0.0),
            top_competitors=top_competitors,
            trends=list(trends.values()),
            demand_forecast=demand_forecast,
            market_segments=market_segments,
            opportunity_score=opportunity_score,
            competition_level=competition_level,
            price_elasticity=market_data.get("price_elasticity"),
            seasonality_index=market_data.get("seasonality_index"),
            last_updated=datetime.now(),
        )

        # Cache results
        self.analysis_cache[cache_key] = {
            "metrics": metrics,
            "timestamp": datetime.now(),
        }

        return metrics

    async def _get_metric_data(
        self, category_id: str, metrics: List[str], timeframe_days: int
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """
        Get historical data for specified metrics.

        Args:
            category_id: ID of the category
            metrics: List of metrics to get data for
            timeframe_days: Number of days of data to get

        Returns:
            Dictionary mapping metric names to lists of (date, value) tuples
        """
        # In a real implementation, this would fetch data from a database
        # For this example, we'll generate mock data

        import random
        from datetime import timedelta

        # Generate mock data for each metric
        metric_data = {}

        for metric in metrics:
            # Generate timeframe_days days of data
            data = []

            # Set base value and trend based on metric
            if metric == "price":
                base_value = 50.0
                trend = 0.001  # Slight upward trend
                noise = 2.0
            elif metric == "sales_volume":
                base_value = 100.0
                trend = 0.005  # Stronger upward trend
                noise = 10.0
            elif metric == "listing_count":
                base_value = 200.0
                trend = -0.001  # Slight downward trend
                noise = 5.0
            elif metric == "search_volume":
                base_value = 500.0
                trend = 0.002  # Upward trend
                noise = 50.0
            elif metric == "conversion_rate":
                base_value = 0.05  # 5%
                trend = 0.0001  # Very slight upward trend
                noise = 0.005
            else:
                base_value = 100.0
                trend = 0.0
                noise = 10.0

            # Generate data points
            for day in range(timeframe_days, 0, -1):
                date = datetime.now() - timedelta(days=day)

                # Calculate value with trend and noise
                trend_factor = 1.0 + (trend * (timeframe_days - day))
                noise_factor = 1.0 + (random.uniform(-1.0, 1.0) * noise / base_value)

                # Add weekly seasonality
                weekday = date.weekday()
                weekly_factor = 1.1 if weekday >= 5 else 1.0  # Weekend boost

                value = base_value * trend_factor * noise_factor * weekly_factor

                # Ensure non-negative values
                value = max(0.0, value)

                # Add to data
                data.append((date, round(value, 4)))

            metric_data[metric] = data

        return metric_data

    async def _get_market_data(
        self, category_id: str, marketplace: str
    ) -> Dict[str, Union[int, float, str]]:
        """
        Get market data for a category.

        Args:
            category_id: ID of the category
            marketplace: Marketplace to get data for

        Returns:
            Dictionary with market data
        """
        # In a real implementation, this would fetch data from marketplace APIs
        # For this example, we'll generate mock data

        import random

        # Generate mock market data
        market_data = {
            "category_id": category_id,
            "marketplace": marketplace,
            "total_listings": random.randint(1000, 5000),
            "active_listings": random.randint(800, 4000),
            "average_price": round(random.uniform(50.0, 200.0), 2),
            "min_price": round(random.uniform(20.0, 40.0), 2),
            "max_price": round(random.uniform(250.0, 500.0), 2),
            "median_price": round(random.uniform(60.0, 150.0), 2),
            "sales_velocity": round(random.uniform(10.0, 50.0), 2),  # Sales per day
            "market_size": round(
                random.uniform(100000.0, 1000000.0), 2
            ),  # Total market value
            "growth_rate": round(random.uniform(-0.05, 0.15), 4),  # Annual growth rate
            "price_elasticity": round(random.uniform(-2.0, -0.5), 2),
            "seasonality_index": round(random.uniform(0.1, 0.5), 2),
        }

        return market_data

    def _calculate_market_segments(
        self, competitors: List[CompetitorData]
    ) -> Dict[MarketSegment, float]:
        """
        Calculate market segment distribution.

        Args:
            competitors: List of competitor data

        Returns:
            Dictionary mapping segments to their market share
        """
        if not competitors:
            return {
                MarketSegment.BUDGET: 0.25,
                MarketSegment.MID_RANGE: 0.5,
                MarketSegment.PREMIUM: 0.2,
                MarketSegment.LUXURY: 0.05,
            }

        # Count products in each segment
        segment_counts = {segment: 0 for segment in MarketSegment}

        for competitor in competitors:
            for segment in competitor.segments:
                segment_counts[segment] += competitor.product_count

        # Calculate total products
        total_products = sum(segment_counts.values())

        if total_products == 0:
            return {segment: 0.0 for segment in MarketSegment}

        # Calculate segment shares
        segment_shares = {
            segment: count / total_products for segment, count in segment_counts.items()
        }

        return segment_shares

    def _calculate_market_concentration(
        self, competitors: List[CompetitorData]
    ) -> Dict[str, float]:
        """
        Calculate market concentration metrics.

        Args:
            competitors: List of competitor data

        Returns:
            Dictionary with market concentration metrics
        """
        if not competitors:
            return {"hhi": 0.0, "cr4": 0.0, "top_share": 0.0}

        # Sort by market share
        sorted_competitors = sorted(
            competitors, key=lambda c: c.market_share, reverse=True
        )

        # Calculate Herfindahl-Hirschman Index (HHI)
        hhi = sum(c.market_share**2 for c in competitors) * 10000

        # Calculate CR4 (4-firm concentration ratio)
        cr4 = sum(c.market_share for c in sorted_competitors[:4])

        # Get top competitor's market share
        top_share = sorted_competitors[0].market_share if sorted_competitors else 0.0

        return {
            "hhi": round(hhi, 2),
            "cr4": round(cr4, 4),
            "top_share": round(top_share, 4),
        }

    def _calculate_price_distribution(
        self, competitors: List[CompetitorData]
    ) -> Dict[str, int]:
        """
        Calculate price distribution across competitors.

        Args:
            competitors: List of competitor data

        Returns:
            Dictionary mapping price ranges to counts
        """
        if not competitors:
            return {}

        # Get all prices
        prices = []
        for competitor in competitors:
            # Use average price as representative
            prices.append(competitor.average_price)

        if not prices:
            return {}

        # Calculate price ranges
        min_price = min(prices)
        max_price = max(prices)

        if min_price == max_price:
            return {f"{min_price:.2f}": len(prices)}

        # Create price buckets
        range_size = (max_price - min_price) / 5
        buckets = {}

        for i in range(5):
            lower = min_price + (i * range_size)
            upper = min_price + ((i + 1) * range_size)
            bucket_key = f"{lower:.2f}-{upper:.2f}"
            buckets[bucket_key] = 0

        # Count prices in each bucket
        for price in prices:
            bucket_index = min(4, int((price - min_price) / range_size))
            lower = min_price + (bucket_index * range_size)
            upper = min_price + ((bucket_index + 1) * range_size)
            bucket_key = f"{lower:.2f}-{upper:.2f}"
            buckets[bucket_key] += 1

        return buckets

    def _calculate_opportunity_score(
        self,
        market_data: Dict[str, Union[int, float, str]],
        trends: Dict[str, MarketTrend],
        competitors: List[CompetitorData],
        forecast: Optional[DemandForecast],
    ) -> float:
        """
        Calculate market opportunity score.

        Args:
            market_data: Market data
            trends: Market trends
            competitors: Competitor data
            forecast: Demand forecast

        Returns:
            Opportunity score between 0.0 and 1.0
        """
        # Start with base score
        score = 0.5

        # Factor 1: Market growth (25%)
        growth_rate = market_data.get("growth_rate", 0.0)
        growth_score = min(
            1.0, max(0.0, (growth_rate + 0.05) / 0.2)
        )  # Normalize to 0-1
        score += growth_score * 0.25

        # Factor 2: Competition level (25%)
        competition_level = self._calculate_competition_level(market_data, competitors)
        competition_score = 1.0 - competition_level  # Lower competition = higher score
        score += competition_score * 0.25

        # Factor 3: Trend direction (25%)
        trend_score = 0.5  # Default
        if "sales_volume" in trends:
            sales_trend = trends["sales_volume"]
            if sales_trend.direction == "increasing":
                trend_score = 0.75 + (sales_trend.magnitude * 0.25)
            elif sales_trend.direction == "decreasing":
                trend_score = 0.5 - (sales_trend.magnitude * 0.5)
            elif sales_trend.direction == "volatile":
                trend_score = 0.3
        score += trend_score * 0.25

        # Factor 4: Forecast growth (25%)
        forecast_score = 0.5  # Default
        if forecast and forecast.growth_rate > 0:
            forecast_score = min(1.0, 0.5 + forecast.growth_rate)
        score += forecast_score * 0.25

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))

    def _calculate_competition_level(
        self,
        market_data: Dict[str, Union[int, float, str]],
        competitors: List[CompetitorData],
    ) -> float:
        """
        Calculate competition level in the market.

        Args:
            market_data: Market data
            competitors: Competitor data

        Returns:
            Competition level between 0.0 and 1.0
        """
        # Start with base level
        level = 0.5

        # Factor 1: Number of competitors (30%)
        competitor_count = len(competitors)
        if competitor_count <= 5:
            competitor_factor = 0.2
        elif competitor_count <= 10:
            competitor_factor = 0.4
        elif competitor_count <= 20:
            competitor_factor = 0.6
        elif competitor_count <= 50:
            competitor_factor = 0.8
        else:
            competitor_factor = 1.0
        level += competitor_factor * 0.3

        # Factor 2: Market concentration (40%)
        concentration = self._calculate_market_concentration(competitors)
        hhi = concentration.get("hhi", 0.0)

        if hhi > 2500:  # Highly concentrated
            concentration_factor = 0.3
        elif hhi > 1500:  # Moderately concentrated
            concentration_factor = 0.5
        else:  # Competitive
            concentration_factor = 0.8
        level += concentration_factor * 0.4

        # Factor 3: Price competition (30%)
        price_range = market_data.get("max_price", 0.0) - market_data.get(
            "min_price", 0.0
        )
        avg_price = market_data.get("average_price", 1.0)

        if avg_price > 0:
            price_variation = price_range / avg_price

            if price_variation < 0.2:  # Low price variation
                price_factor = 0.8  # High competition
            elif price_variation < 0.5:
                price_factor = 0.6
            elif price_variation < 1.0:
                price_factor = 0.4
            else:
                price_factor = 0.2  # Low competition
        else:
            price_factor = 0.5

        level += price_factor * 0.3

        # Ensure level is between 0 and 1
        return max(0.0, min(1.0, level))
