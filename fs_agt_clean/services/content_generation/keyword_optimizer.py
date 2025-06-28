"""
SEO keyword optimization using market insights and trend analysis.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

from fs_agt_clean.agents.market.specialized.market_analyzer import MarketAnalyzer
from fs_agt_clean.agents.market.specialized.trend_detector import TrendData
from fs_agt_clean.core.models.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class KeywordMetrics:
    """Keyword performance metrics."""

    search_volume: int
    competition: float
    relevance: float
    trend_score: float
    seasonal_score: float
    overall_score: float


@dataclass
class KeywordSet:
    """Optimized keyword set."""

    primary: List[str]
    secondary: List[str]
    long_tail: List[str]
    metrics: Dict[str, KeywordMetrics]
    performance_score: float


class KeywordOptimizer:
    """SEO keyword optimization engine."""

    def __init__(
        self,
        market_analyzer: MarketAnalyzer,
        vector_store: VectorStore,
        max_primary: int = 5,
        max_secondary: int = 15,
        max_long_tail: int = 30,
    ):
        self.market_analyzer = market_analyzer
        self.vector_store = vector_store
        self.max_primary = max_primary
        self.max_secondary = max_secondary
        self.max_long_tail = max_long_tail

    async def optimize_keywords(
        self, product_data: Dict, market_trends: List[TrendData], category_id: str
    ) -> KeywordSet:
        """Generate optimized keyword set."""
        try:
            # Generate candidate keywords
            candidates = await self._generate_candidates(product_data, category_id)

            # Calculate metrics
            keyword_metrics = self._calculate_metrics(candidates, market_trends)

            # Optimize selection
            primary, secondary, long_tail = self._optimize_selection(
                candidates, keyword_metrics
            )

            # Calculate performance score
            performance_score = self._calculate_performance_score(
                primary, secondary, long_tail, keyword_metrics
            )

            return KeywordSet(
                primary=primary,
                secondary=secondary,
                long_tail=long_tail,
                metrics=keyword_metrics,
                performance_score=performance_score,
            )

        except Exception as e:
            logger.error("Failed to optimize keywords: %s", str(e))
            raise

    async def _generate_candidates(
        self, product_data: Dict, category_id: str
    ) -> List[str]:
        """Generate candidate keywords."""
        candidates = set()

        # Add base product keywords
        candidates.update(self._extract_product_keywords(product_data))

        # Add category keywords
        category_keywords = await self._get_category_keywords(category_id)
        candidates.update(category_keywords)

        # Add attribute-based keywords
        attribute_keywords = self._generate_attribute_keywords(product_data)
        candidates.update(attribute_keywords)

        # Add semantic variations
        semantic_keywords = await self._generate_semantic_keywords(candidates)
        candidates.update(semantic_keywords)

        return list(candidates)

    def _calculate_metrics(
        self, keywords: List[str], market_trends: List[TrendData]
    ) -> Dict[str, KeywordMetrics]:
        """Calculate metrics for each keyword."""
        metrics = {}

        for keyword in keywords:
            # Get base metrics
            search_volume = self._get_search_volume(keyword)
            competition = self._get_competition_score(keyword)
            relevance = self._calculate_relevance(keyword)

            # Calculate trend score
            trend_score = self._calculate_trend_score(keyword, market_trends)

            # Calculate seasonal score
            seasonal_score = self._calculate_seasonal_score(keyword)

            # Calculate overall score
            overall_score = self._calculate_overall_score(
                search_volume, competition, relevance, trend_score, seasonal_score
            )

            metrics[keyword] = KeywordMetrics(
                search_volume=search_volume,
                competition=competition,
                relevance=relevance,
                trend_score=trend_score,
                seasonal_score=seasonal_score,
                overall_score=overall_score,
            )

        return metrics

    def _optimize_selection(
        self, candidates: List[str], metrics: Dict[str, KeywordMetrics]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Optimize keyword selection."""
        # Sort candidates by overall score
        sorted_keywords = sorted(
            candidates, key=lambda k: metrics[k].overall_score, reverse=True
        )

        # Select primary keywords (highest overall score)
        primary = self._select_diverse_keywords(
            sorted_keywords, metrics, self.max_primary, min_score=0.8
        )

        # Remove selected keywords
        remaining = [k for k in sorted_keywords if k not in primary]

        # Select secondary keywords (balance of metrics)
        secondary = self._select_diverse_keywords(
            remaining, metrics, self.max_secondary, min_score=0.6
        )

        # Remove selected keywords
        remaining = [k for k in remaining if k not in secondary]

        # Select long-tail keywords (focus on low competition)
        long_tail = self._select_long_tail_keywords(
            remaining, metrics, self.max_long_tail
        )

        return primary, secondary, long_tail

    def _extract_product_keywords(self, product_data: Dict) -> List[str]:
        """Extract keywords from product data."""
        keywords = set()

        # Add brand and model
        if "brand" in product_data:
            keywords.add(product_data["brand"].lower())
        if "model" in product_data:
            keywords.add(product_data["model"].lower())

        # Add category and subcategory
        if "category" in product_data:
            keywords.add(product_data["category"].lower())
        if "subcategory" in product_data:
            keywords.add(product_data["subcategory"].lower())

        # Add features
        for feature in product_data.get("features", []):
            keywords.update(self._tokenize(feature.lower()))

        return list(keywords)

    async def _get_category_keywords(self, category_id: str) -> List[str]:
        """Get category-specific keywords."""
        # Query vector store for category keywords
        results = await self.vector_store.search(
            category_id, filter_params={"type": "category_keywords"}, k=50
        )

        return [r["keyword"] for r in results]

    def _generate_attribute_keywords(self, product_data: Dict) -> List[str]:
        """Generate keywords from product attributes."""
        keywords = set()

        # Process each attribute
        for attr, value in product_data.get("attributes", {}).items():
            # Add attribute name
            keywords.add(attr.lower())

            # Add attribute value
            if isinstance(value, str):
                keywords.update(self._tokenize(value.lower()))
            elif isinstance(value, (int, float)):
                keywords.add(str(value))

        return list(keywords)

    async def _generate_semantic_keywords(self, base_keywords: List[str]) -> List[str]:
        """Generate semantic variations of keywords."""
        semantic_keywords = set()

        for keyword in base_keywords:
            # Query vector store for similar terms
            results = await self.vector_store.search(
                keyword, filter_params={"type": "semantic_keywords"}, k=5
            )

            semantic_keywords.update([r["keyword"] for r in results])

        return list(semantic_keywords)

    def _get_search_volume(self, keyword: str) -> int:
        """Get search volume for keyword."""
        # Implement search volume lookup
        return 1000  # Placeholder

    def _get_competition_score(self, keyword: str) -> float:
        """Get competition score for keyword."""
        # Implement competition scoring
        return 0.5  # Placeholder

    def _calculate_relevance(self, keyword: str) -> float:
        """Calculate keyword relevance score."""
        # Implement relevance scoring
        return 0.8  # Placeholder

    def _calculate_trend_score(
        self, keyword: str, market_trends: List[TrendData]
    ) -> float:
        """Calculate trend score for keyword."""
        trend_score = 0.5  # Neutral baseline
        relevant_trends = 0

        for trend in market_trends:
            if keyword in trend.related_terms:
                if trend.direction == "up":
                    trend_score += 0.1 * trend.strength * trend.confidence
                elif trend.direction == "down":
                    trend_score -= 0.1 * trend.strength * trend.confidence
                relevant_trends += 1

        if relevant_trends > 0:
            trend_score = min(max(trend_score, 0.0), 1.0)
            return trend_score
        return 0.5

    def _calculate_seasonal_score(self, keyword: str) -> float:
        """Calculate seasonal relevance score."""
        # Implement seasonal scoring
        return 0.7  # Placeholder

    def _calculate_overall_score(
        self,
        search_volume: int,
        competition: float,
        relevance: float,
        trend_score: float,
        seasonal_score: float,
    ) -> float:
        """Calculate overall keyword score."""
        # Normalize search volume (log scale)
        volume_score = min(np.log10(search_volume) / 6.0, 1.0)

        # Calculate weighted score
        score = (
            volume_score * 0.3
            + (1 - competition) * 0.2  # Lower competition is better
            + relevance * 0.2
            + trend_score * 0.2
            + seasonal_score * 0.1
        )

        return min(score, 1.0)

    def _select_diverse_keywords(
        self,
        candidates: List[str],
        metrics: Dict[str, KeywordMetrics],
        max_count: int,
        min_score: float,
    ) -> List[str]:
        """Select diverse set of keywords."""
        selected = []
        selected_vectors = []

        for keyword in candidates:
            if len(selected) >= max_count:
                break

            if metrics[keyword].overall_score < min_score:
                continue

            # Check diversity
            if self._is_diverse_enough(keyword, selected_vectors):
                selected.append(keyword)
                selected_vectors.append(self._get_keyword_vector(keyword))

        return selected

    def _select_long_tail_keywords(
        self, candidates: List[str], metrics: Dict[str, KeywordMetrics], max_count: int
    ) -> List[str]:
        """Select long-tail keywords."""
        # Sort by combination of low competition and relevance
        scored_candidates = [
            (k, metrics[k].relevance * (1 - metrics[k].competition)) for k in candidates
        ]
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        return [k for k, _ in scored_candidates[:max_count]]

    def _calculate_performance_score(
        self,
        primary: List[str],
        secondary: List[str],
        long_tail: List[str],
        metrics: Dict[str, KeywordMetrics],
    ) -> float:
        """Calculate overall keyword set performance score."""
        scores = []

        # Weight primary keywords most heavily
        for keyword in primary:
            scores.append(metrics[keyword].overall_score * 0.5)

        # Secondary keywords
        for keyword in secondary:
            scores.append(metrics[keyword].overall_score * 0.3)

        # Long-tail keywords
        for keyword in long_tail:
            scores.append(metrics[keyword].overall_score * 0.2)

        return sum(scores) / len(scores) if scores else 0.0

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into keywords."""
        # Simple whitespace tokenization
        return text.split()

    def _is_diverse_enough(
        self, keyword: str, selected_vectors: List[np.ndarray]
    ) -> bool:
        """Check if keyword is diverse enough from selected ones."""
        if not selected_vectors:
            return True

        keyword_vector = self._get_keyword_vector(keyword)

        # Calculate similarity with existing keywords
        max_similarity = max(
            np.dot(keyword_vector, vector) for vector in selected_vectors
        )

        return max_similarity < 0.8  # Diversity threshold

    def _get_keyword_vector(self, keyword: str) -> np.ndarray:
        """Get vector representation of keyword."""
        # Implement keyword vectorization
        return np.random.rand(384)  # Placeholder
