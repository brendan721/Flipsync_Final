"""
Market Analysis and Intelligence Services.

This module provides comprehensive market analysis capabilities including:
- Market trend analysis and forecasting
- Competitor analysis and profiling
- Advanced search and discovery
- Market intelligence and insights
- Vector-based similarity matching
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Import market analysis components
try:
    from .market_analyzer import MarketAnalyzer
except ImportError:
    MarketAnalyzer = None

try:
    from .competitor_analyzer import CompetitorAnalyzer, CompetitorProfile
except ImportError:
    CompetitorAnalyzer = None
    CompetitorProfile = None

try:
    from .advanced_search import AdvancedSearch
except ImportError:
    AdvancedSearch = None

try:
    from .analytics import SearchAnalytics
except ImportError:
    SearchAnalytics = None

try:
    from .service import SearchService
except ImportError:
    SearchService = None

try:
    from .models import (
        CompetitorData,
        MarketTrend,
        SearchQuery,
        SearchResult,
        TrendData,
    )
except ImportError:
    SearchQuery = None
    SearchResult = None
    MarketTrend = None
    CompetitorData = None
    TrendData = None


class MarketAnalysisService:
    """Main service for market analysis and intelligence."""

    def __init__(self, vector_store=None, metric_collector=None):
        """Initialize the market analysis service."""
        self.vector_store = vector_store
        self.metric_collector = metric_collector

        # Initialize components
        self.market_analyzer = MarketAnalyzer() if MarketAnalyzer else None
        self.competitor_analyzer = (
            CompetitorAnalyzer(
                vector_store=vector_store, metric_collector=metric_collector
            )
            if CompetitorAnalyzer and vector_store
            else None
        )
        self.advanced_search = AdvancedSearch() if AdvancedSearch else None
        self.search_analytics = SearchAnalytics() if SearchAnalytics else None
        self.search_service = SearchService() if SearchService else None

    async def analyze_market_trends(
        self, category_id: str, timeframe: str = "30d"
    ) -> Dict:
        """Analyze market trends for a category."""
        try:
            if not self.market_analyzer:
                return {"error": "Market analyzer not available"}

            trends = await self.market_analyzer.analyze_trends(category_id, timeframe)
            return {
                "category_id": category_id,
                "timeframe": timeframe,
                "trends": trends,
                "analysis_timestamp": "2024-01-01T00:00:00Z",
            }
        except Exception as e:
            logger.error("Failed to analyze market trends: %s", str(e))
            return {"error": str(e)}

    async def analyze_competitors(
        self, category_id: str, product_data: Dict
    ) -> List[Dict]:
        """Analyze competitors using vector similarity."""
        try:
            if not self.competitor_analyzer:
                return []

            competitor_profiles = await self.competitor_analyzer.analyze_competitors(
                category_id, product_data
            )

            return [
                {
                    "competitor_id": profile.competitor_id,
                    "similarity_score": profile.similarity_score,
                    "price_position": profile.price_position,
                    "market_share": profile.market_share,
                    "strengths": profile.strengths,
                    "weaknesses": profile.weaknesses,
                    "threat_level": profile.threat_level,
                    "last_updated": profile.last_updated.isoformat(),
                }
                for profile in competitor_profiles
            ]
        except Exception as e:
            logger.error("Failed to analyze competitors: %s", str(e))
            return []

    async def perform_advanced_search(
        self, query: str, filters: Optional[Dict] = None
    ) -> Dict:
        """Perform advanced search with analytics."""
        try:
            if not self.advanced_search:
                return {"error": "Advanced search not available"}

            search_results = await self.advanced_search.search(query, filters)

            # Analyze search results if analytics available
            if self.search_analytics:
                analytics = await self.search_analytics.analyze_results(search_results)
                return {
                    "query": query,
                    "filters": filters,
                    "results": search_results,
                    "analytics": analytics,
                }

            return {"query": query, "filters": filters, "results": search_results}
        except Exception as e:
            logger.error("Failed to perform advanced search: %s", str(e))
            return {"error": str(e)}

    async def get_market_intelligence(
        self, category_id: str, product_data: Optional[Dict] = None
    ) -> Dict:
        """Get comprehensive market intelligence."""
        try:
            intelligence = {
                "category_id": category_id,
                "market_trends": {},
                "competitor_analysis": [],
                "search_insights": {},
                "recommendations": [],
            }

            # Get market trends
            if self.market_analyzer:
                trends = await self.analyze_market_trends(category_id)
                intelligence["market_trends"] = trends

            # Get competitor analysis if product data provided
            if product_data and self.competitor_analyzer:
                competitors = await self.analyze_competitors(category_id, product_data)
                intelligence["competitor_analysis"] = competitors

            # Generate recommendations based on analysis
            intelligence["recommendations"] = self._generate_recommendations(
                intelligence["market_trends"], intelligence["competitor_analysis"]
            )

            return intelligence
        except Exception as e:
            logger.error("Failed to get market intelligence: %s", str(e))
            return {"error": str(e)}

    def _generate_recommendations(
        self, market_trends: Dict, competitor_analysis: List[Dict]
    ) -> List[str]:
        """Generate recommendations based on market analysis."""
        recommendations = []

        # Basic recommendations based on available data
        if market_trends.get("trends"):
            recommendations.append("Monitor market trends for pricing opportunities")

        if competitor_analysis:
            high_threat_competitors = [
                c for c in competitor_analysis if c.get("threat_level") == "high"
            ]
            if high_threat_competitors:
                recommendations.append(
                    "Focus on differentiation from high-threat competitors"
                )

            low_price_competitors = [
                c for c in competitor_analysis if c.get("price_position") == "lower"
            ]
            if low_price_competitors:
                recommendations.append(
                    "Consider value-based positioning against lower-priced competitors"
                )

        return recommendations


__all__ = [
    "MarketAnalysisService",
    "MarketAnalyzer",
    "CompetitorAnalyzer",
    "CompetitorProfile",
    "AdvancedSearch",
    "SearchAnalytics",
    "SearchService",
    "SearchQuery",
    "SearchResult",
    "MarketTrend",
    "CompetitorData",
    "TrendData",
]
