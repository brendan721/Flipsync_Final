"""Competitor analysis agent for monitoring competitor activity and strategic intelligence."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, TypedDict, cast
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray

from fs_agt_clean.agents.market.base_market_agent import BaseMarketUnifiedAgent
from fs_agt_clean.agents.market.specialized.market_types import (
    CompetitorProfile,
    PricePosition,
    ProductData,
    ThreatLevel,
)
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.core.monitoring.metrics.collector import MetricsCollector
from fs_agt_clean.core.vector_store.providers.qdrant import QdrantVectorStore
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer

logger: logging.Logger = logging.getLogger(__name__)


class SearchResult(TypedDict):
    """Vector search result type."""

    score: float
    metadata: Dict[str, Any]


class CompetitorAnalyzer(BaseMarketUnifiedAgent):
    """
    UnifiedAgent for monitoring competitor activity and providing strategic intelligence.

    Capabilities:
    - Price monitoring and listing comparison
    - Strategic recommendations and competitive intelligence
    - Market share analysis
    - Competitor strength/weakness assessment
    - Threat level evaluation
    """

    def __init__(
        self,
        marketplace: str = "ebay",
        config_manager: Optional[ConfigManager] = None,
        alert_manager: Optional[AlertManager] = None,
        battery_optimizer: Optional[BatteryOptimizer] = None,
        vector_store: Optional[QdrantVectorStore] = None,
        metric_collector: Optional[MetricsCollector] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize competitor analyzer.

        Args:
            marketplace: The marketplace to analyze
            config_manager: Optional configuration manager
            alert_manager: Optional alert manager
            battery_optimizer: Optional battery optimizer for mobile efficiency
            vector_store: Vector store for similarity matching
            metric_collector: Optional metric collector for monitoring
            config: Optional configuration dictionary
        """
        agent_id = str(uuid4())
        if config_manager is None:
            config_manager = ConfigManager()
        if alert_manager is None:
            alert_manager = AlertManager()
        if battery_optimizer is None:
            battery_optimizer = BatteryOptimizer()

        super().__init__(
            agent_id,
            marketplace,
            config_manager,
            alert_manager,
            battery_optimizer,
            config,
        )

        self.vector_store = vector_store or QdrantVectorStore()
        self.metric_collector = metric_collector
        self.similarity_threshold = (
            config.get("similarity_threshold", 0.7) if config else 0.7
        )

    def _get_required_config_fields(self) -> List[str]:
        """Get required configuration fields."""
        fields = super()._get_required_config_fields()
        fields.extend(
            [
                "similarity_threshold",
                "analysis_interval",
                "threat_threshold",
                "market_share_threshold",
                "competitor_tracking_limit",
            ]
        )
        return fields

    async def analyze_competitors(
        self, category_id: str, product_data: ProductData
    ) -> List[CompetitorProfile]:
        """Analyze competitors using vector similarity.

        Args:
            category_id: Category ID to analyze
            product_data: Product data for comparison

        Returns:
            List of competitor profiles sorted by threat level and similarity
        """
        start_time = datetime.now(timezone.utc)
        try:
            if self.metric_collector:
                await self.metric_collector.record_latency(
                    "competitor_analysis_start", 0.0
                )
            product_vector = self._create_product_vector(product_data)
            similar_products = await self._find_similar_products(
                product_vector, category_id
            )
            competitor_data = self._group_by_competitor(similar_products)
            competitor_profiles: List[CompetitorProfile] = []
            for competitor_id, products in competitor_data.items():
                profile = self._analyze_competitor(
                    competitor_id, products, product_data
                )
                competitor_profiles.append(profile)

            # Sort by threat level and similarity score
            competitor_profiles.sort(
                key=lambda x: (
                    {"high": 3, "medium": 2, "low": 1}[x.threat_level.value],
                    x.similarity_score,
                ),
                reverse=True,
            )

            if self.metric_collector:
                end_time = datetime.now(timezone.utc)
                latency = (end_time - start_time).total_seconds()
                await self.metric_collector.record_latency(
                    "competitor_analysis", latency
                )
            return competitor_profiles
        except Exception as e:
            if self.metric_collector:
                await self.metric_collector.record_error("competitor_analysis", str(e))
            logger.error("Error analyzing competitors: %s", e)
            raise

    def _create_product_vector(self, product_data: ProductData) -> NDArray[np.float32]:
        """Create vector representation of a product."""
        vector_components = [
            float(product_data["price"]),
            float(product_data.get("rating", 0.0) or 0.0),
            float(product_data.get("reviews_count", 0) or 0),
            float(product_data.get("sales_rank", 0.0) or 0.0),
        ]
        # Ensure float32 dtype
        vector = np.array(vector_components, dtype=np.float32)
        normalized = vector / cast(float, np.linalg.norm(vector))
        return normalized.astype(np.float32)

    async def _find_similar_products(
        self, product_vector: NDArray[np.float32], category_id: str, k: int = 100
    ) -> List[SearchResult]:
        """Find similar products using vector similarity."""
        # Convert NDArray to list of floats
        vector_list: List[float] = [float(x) for x in product_vector.tolist()]

        # Await the coroutine
        results = await self.vector_store.search(
            query_vector=vector_list,
            filter_params={"category_id": category_id},
            k=k,
        )

        filtered_results: List[SearchResult] = []
        for result in results:
            if result.get("score", 0) >= self.similarity_threshold:
                filtered_results.append(
                    SearchResult(
                        score=float(result["score"]), metadata=dict(result["metadata"])
                    )
                )
        return filtered_results

    def _group_by_competitor(
        self, similar_products: List[SearchResult]
    ) -> Dict[str, List[SearchResult]]:
        """Group similar products by competitor."""
        competitor_products: Dict[str, List[SearchResult]] = {}
        for product in similar_products:
            competitor_id = product["metadata"]["seller_id"]
            if competitor_id not in competitor_products:
                competitor_products[competitor_id] = []
            competitor_products[competitor_id].append(product)
        return competitor_products

    def _analyze_competitor(
        self, competitor_id: str, products: List[SearchResult], our_product: ProductData
    ) -> CompetitorProfile:
        """Analyze a competitor based on their products."""
        similarity_score = float(np.mean([float(p["score"]) for p in products]))
        our_price = float(our_product["price"])
        their_prices = [float(p["metadata"]["price"]) for p in products]
        avg_price = float(np.mean(their_prices))

        if avg_price < our_price * 0.9:
            price_position = PricePosition.LOWER
        elif avg_price > our_price * 1.1:
            price_position = PricePosition.HIGHER
        else:
            price_position = PricePosition.SIMILAR

        total_products = sum((len(p["metadata"].get("products", [])) for p in products))
        market_share = float(
            len(products) / total_products if total_products > 0 else 0
        )

        strengths: List[str] = []
        weaknesses: List[str] = []
        if price_position == PricePosition.LOWER:
            strengths.append("competitive_pricing")
        elif price_position == PricePosition.HIGHER:
            weaknesses.append("higher_prices")

        their_avg_rating = float(
            np.mean([float(p["metadata"].get("rating", 0)) for p in products])
        )
        our_rating = float(our_product.get("rating", 0) or 0)

        if their_avg_rating > our_rating:
            strengths.append("better_ratings")
        else:
            weaknesses.append("lower_ratings")

        their_avg_sales = float(
            np.mean([float(p["metadata"].get("sales_count", 0)) for p in products])
        )
        our_sales = float(our_product.get("reviews_count", 0) or 0)

        if their_avg_sales > our_sales:
            strengths.append("higher_sales_volume")
        else:
            weaknesses.append("lower_sales_volume")

        threat_level = self._calculate_threat_level(
            similarity_score, market_share, len(strengths)
        )

        return CompetitorProfile(
            competitor_id=competitor_id,
            similarity_score=similarity_score,
            price_position=price_position,
            market_share=market_share,
            strengths=strengths,
            weaknesses=weaknesses,
            threat_level=threat_level,
            last_updated=datetime.now(timezone.utc),
        )

    def _calculate_threat_level(
        self, similarity_score: float, market_share: float, strength_count: int
    ) -> ThreatLevel:
        """Calculate competitor threat level."""
        threat_score = (
            similarity_score * 0.4 + market_share * 0.4 + strength_count / 5 * 0.2
        )
        if threat_score > 0.7:
            return ThreatLevel.HIGH
        elif threat_score > 0.4:
            return ThreatLevel.MEDIUM
        return ThreatLevel.LOW

    async def get_competitor_insights(
        self, competitor_profiles: List[CompetitorProfile]
    ) -> Dict[str, Any]:
        """Generate strategic insights from competitor analysis."""
        if not competitor_profiles:
            return {"insights": [], "recommendations": []}

        insights = []
        recommendations = []

        # Analyze pricing landscape
        price_positions = [p.price_position for p in competitor_profiles]
        lower_count = sum(1 for p in price_positions if p == PricePosition.LOWER)

        if lower_count > len(competitor_profiles) * 0.6:
            insights.append("Market is highly price-competitive")
            recommendations.append(
                "Consider cost optimization or value differentiation"
            )

        # Analyze threat levels
        high_threats = [
            p for p in competitor_profiles if p.threat_level == ThreatLevel.HIGH
        ]
        if high_threats:
            insights.append(f"Identified {len(high_threats)} high-threat competitors")
            recommendations.append(
                "Monitor high-threat competitors closely and develop counter-strategies"
            )

        # Analyze market share concentration
        total_share = sum(p.market_share for p in competitor_profiles)
        if total_share > 0.8:
            insights.append("Market is highly concentrated")
            recommendations.append("Focus on niche differentiation or market expansion")

        return {
            "insights": insights,
            "recommendations": recommendations,
            "competitor_count": len(competitor_profiles),
            "average_threat_level": self._calculate_average_threat_level(
                competitor_profiles
            ),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_average_threat_level(self, profiles: List[CompetitorProfile]) -> str:
        """Calculate average threat level across all competitors."""
        if not profiles:
            return "none"

        threat_scores = {ThreatLevel.HIGH: 3, ThreatLevel.MEDIUM: 2, ThreatLevel.LOW: 1}

        total_score = sum(threat_scores[p.threat_level] for p in profiles)
        avg_score = total_score / len(profiles)

        if avg_score >= 2.5:
            return "high"
        elif avg_score >= 1.5:
            return "medium"
        else:
            return "low"
