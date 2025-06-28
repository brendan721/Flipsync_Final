import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np

from fs_agt_clean.core.models.vector_store.store import VectorStore
from fs_agt_clean.core.monitoring.alerts.collectors import MetricCollector

"\nDynamic competitor analysis using vector-based similarity matching.\n"
logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class CompetitorProfile:
    """Competitor profile data."""

    competitor_id: str
    similarity_score: float
    price_position: str
    market_share: float
    strengths: List[str]
    weaknesses: List[str]
    threat_level: str
    last_updated: datetime


class CompetitorAnalyzer:
    """Dynamic competitor analysis using vector-based matching."""

    def __init__(
        self,
        vector_store: VectorStore,
        metric_collector: Optional[MetricCollector] = None,
        similarity_threshold: float = 0.7,
    ):
        self.vector_store = vector_store
        self.metric_collector = metric_collector
        self.similarity_threshold = similarity_threshold

    async def analyze_competitors(
        self, category_id: str, product_data: Dict
    ) -> List[CompetitorProfile]:
        """Analyze competitors using vector similarity."""
        try:
            if self.metric_collector:
                await self.metric_collector.record_start("competitor_analysis")
            product_vector = self._create_product_vector(product_data)
            similar_products = await self._find_similar_products(
                product_vector, category_id
            )
            competitor_data = self._group_by_competitor(similar_products)
            competitor_profiles = []
            for competitor_id, products in competitor_data.items():
                profile = self._analyze_competitor(
                    competitor_id, products, product_data
                )
                competitor_profiles.append(profile)
            competitor_profiles.sort(
                key=lambda x: (
                    {"high": 3, "medium": 2, "low": 1}[x.threat_level],
                    x.similarity_score,
                ),
                reverse=True,
            )
            if self.metric_collector:
                await self.metric_collector.record_success("competitor_analysis")
            return competitor_profiles
        except Exception as e:
            if self.metric_collector:
                await self.metric_collector.record_failure("competitor_analysis")
            logger.error("Failed to analyze competitors: %s", str(e))
            raise

    def _create_product_vector(self, product_data: Dict) -> np.ndarray:
        """Create vector representation of a product."""
        vector_components = [
            float(product_data["price"]),
            float(product_data["rating"]) if "rating" in product_data else 0.0,
            (
                float(product_data["reviews_count"])
                if "reviews_count" in product_data
                else 0.0
            ),
            float(product_data["sales_rank"]) if "sales_rank" in product_data else 0.0,
        ]
        vector = np.array(vector_components, dtype=np.float32)
        return vector / np.linalg.norm(vector)

    async def _find_similar_products(
        self, product_vector: np.ndarray, category_id: str, k: int = 100
    ) -> List[Dict]:
        """Find similar products using vector similarity."""
        results = await self.vector_store.search(
            query_vector=product_vector, filter_params={"category_id": category_id}, k=k
        )
        return [r for r in results if r["score"] >= self.similarity_threshold]

    def _group_by_competitor(
        self, similar_products: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """Group similar products by competitor."""
        competitor_products = {}
        for product in similar_products:
            competitor_id = product["metadata"]["seller_id"]
            if competitor_id not in competitor_products:
                competitor_products[competitor_id] = []
            competitor_products[competitor_id].append(product)
        return competitor_products

    def _analyze_competitor(
        self, competitor_id: str, products: List[Dict], our_product_data: Dict
    ) -> CompetitorProfile:
        """Analyze a competitor based on their products."""
        similarity_score = np.mean([p["score"] for p in products])
        our_price = float(our_product_data["price"])
        their_prices = [float(p["metadata"]["price"]) for p in products]
        avg_price = np.mean(their_prices)
        if avg_price < our_price * 0.9:
            price_position = "lower"
        elif avg_price > our_price * 1.1:
            price_position = "higher"
        else:
            price_position = "similar"
        total_products = sum((len(p["metadata"].get("products", [])) for p in products))
        market_share = len(products) / total_products if total_products > 0 else 0
        strengths = []
        weaknesses = []
        if price_position == "lower":
            strengths.append("competitive_pricing")
        elif price_position == "higher":
            weaknesses.append("higher_prices")
        their_avg_rating = np.mean(
            [float(p["metadata"].get("rating", 0)) for p in products]
        )
        our_rating = float(our_product_data.get("rating", 0))
        if their_avg_rating > our_rating:
            strengths.append("better_ratings")
        else:
            weaknesses.append("lower_ratings")
        their_avg_sales = np.mean(
            [float(p["metadata"].get("sales_count", 0)) for p in products]
        )
        our_sales = float(our_product_data.get("sales_count", 0))
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
            last_updated=datetime.now(),
        )

    def _calculate_threat_level(
        self, similarity_score: float, market_share: float, strength_count: int
    ) -> str:
        """Calculate competitor threat level."""
        threat_score = (
            similarity_score * 0.4 + market_share * 0.4 + strength_count / 5 * 0.2
        )
        if threat_score > 0.7:
            return "high"
        elif threat_score > 0.4:
            return "medium"
        return "low"
