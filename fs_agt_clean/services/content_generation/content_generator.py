"""
Dynamic listing content generation with market trend integration.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

from fs_agt_clean.core.models.vector_store.store import VectorStore
from fs_agt_clean.services.market_analysis import (
    CompetitorProfile,
    MarketAnalyzer,
    TrendData,
)

logger = logging.getLogger(__name__)


@dataclass
class ContentTemplate:
    """Template for listing content."""

    title_patterns: List[str]
    description_blocks: Dict[str, List[str]]
    feature_patterns: List[str]
    benefit_patterns: List[str]
    call_to_action_patterns: List[str]


@dataclass
class ListingContent:
    """Generated listing content."""

    title: str
    description: str
    features: List[str]
    keywords: List[str]
    metadata: Dict[str, any]
    performance_metrics: Dict[str, float]


class ContentGenerator:
    """Dynamic listing content generator."""

    def __init__(
        self,
        market_analyzer: MarketAnalyzer,
        vector_store: VectorStore,
        templates_path: str = "templates/listing",
        max_keywords: int = 30,
    ):
        self.market_analyzer = market_analyzer
        self.vector_store = vector_store
        self.templates_path = templates_path
        self.max_keywords = max_keywords
        self.templates = self._load_templates()

    def generate_listing(
        self,
        product_data: Dict,
        market_trends: List[TrendData],
        competitors: List[CompetitorProfile],
        category_id: str,
    ) -> ListingContent:
        """Generate optimized listing content."""
        try:
            # Analyze market position
            market_position = self._analyze_market_position(
                product_data, market_trends, competitors
            )

            # Generate title
            title = self._generate_title(product_data, market_position)

            # Generate description
            description = self._generate_description(
                product_data, market_position, market_trends
            )

            # Generate features
            features = self._generate_features(product_data, competitors)

            # Generate keywords
            keywords = self._generate_keywords(product_data, market_trends, category_id)

            # Calculate performance metrics
            performance_metrics = self._calculate_metrics(
                title, description, features, keywords
            )

            return ListingContent(
                title=title,
                description=description,
                features=features,
                keywords=keywords,
                metadata={
                    "market_position": market_position,
                    "generation_timestamp": datetime.now().isoformat(),
                },
                performance_metrics=performance_metrics,
            )

        except Exception as e:
            logger.error("Failed to generate listing content: %s", str(e))
            raise

    def _analyze_market_position(
        self,
        product_data: Dict,
        market_trends: List[TrendData],
        competitors: List[CompetitorProfile],
    ) -> Dict[str, any]:
        """Analyze product's market position."""
        position = {
            "price_position": "competitive",
            "quality_position": "standard",
            "unique_features": [],
            "market_advantages": [],
            "target_segments": [],
        }

        # Analyze price position
        competitor_prices = [c.price_position for c in competitors]
        if "lower" in competitor_prices:
            position["price_position"] = "premium"
        elif "higher" in competitor_prices:
            position["price_position"] = "value"

        # Identify unique features
        competitor_features = set()
        for comp in competitors:
            for feature in comp.metadata.get("features", []):
                competitor_features.add(feature.lower())

        product_features = set(f.lower() for f in product_data.get("features", []))
        position["unique_features"] = list(product_features - competitor_features)

        # Analyze market advantages
        for trend in market_trends:
            if trend.trend_type == "demand" and trend.direction == "up":
                position["market_advantages"].append("growing_demand")
            if trend.trend_type == "price" and trend.direction == "up":
                position["market_advantages"].append("price_strength")

        return position

    def _generate_title(self, product_data: Dict, market_position: Dict) -> str:
        """Generate optimized listing title."""
        # Select title pattern based on market position
        pattern = self._select_template(self.templates.title_patterns, market_position)

        # Fill in template with product data
        title = pattern.format(
            brand=product_data.get("brand", ""),
            model=product_data.get("model", ""),
            key_feature=self._get_key_feature(product_data, market_position),
            value_prop=self._get_value_proposition(market_position),
        )

        return self._optimize_title_length(title)

    def _generate_description(
        self, product_data: Dict, market_position: Dict, market_trends: List[TrendData]
    ) -> str:
        """Generate optimized listing description."""
        description_blocks = []

        # Introduction
        intro_block = self._generate_intro_block(product_data, market_position)
        description_blocks.append(intro_block)

        # Features and benefits
        features_block = self._generate_features_block(product_data, market_position)
        description_blocks.append(features_block)

        # Market positioning
        position_block = self._generate_position_block(market_position, market_trends)
        description_blocks.append(position_block)

        # Call to action
        cta_block = self._generate_cta_block(market_position)
        description_blocks.append(cta_block)

        return "\n\n".join(description_blocks)

    def _generate_features(
        self, product_data: Dict, competitors: List[CompetitorProfile]
    ) -> List[str]:
        """Generate differentiated feature list."""
        features = []

        # Get competitor features for comparison
        competitor_features = self._analyze_competitor_features(competitors)

        # Process each product feature
        for feature in product_data.get("features", []):
            # Check if feature is unique
            if feature.lower() not in competitor_features:
                features.append(self._enhance_feature(feature, "unique"))
            else:
                features.append(self._enhance_feature(feature, "standard"))

        return features

    def _generate_keywords(
        self, product_data: Dict, market_trends: List[TrendData], category_id: str
    ) -> List[str]:
        """Generate optimized keywords."""
        keywords = set()

        # Add base keywords
        keywords.update(product_data.get("base_keywords", []))

        # Add trend-based keywords
        for trend in market_trends:
            if trend.confidence > 0.7:  # Only use high-confidence trends
                keywords.update(self._get_trend_keywords(trend))

        # Add category-specific keywords
        category_keywords = self._get_category_keywords(category_id)
        keywords.update(category_keywords)

        # Optimize and limit keywords
        return self._optimize_keywords(list(keywords))

    def _calculate_metrics(
        self, title: str, description: str, features: List[str], keywords: List[str]
    ) -> Dict[str, float]:
        """Calculate content performance metrics."""
        return {
            "title_score": self._calculate_title_score(title),
            "description_score": self._calculate_description_score(description),
            "feature_score": self._calculate_feature_score(features),
            "keyword_score": self._calculate_keyword_score(keywords),
        }

    def _optimize_title_length(self, title: str) -> str:
        """Optimize title length while maintaining key information."""
        max_length = 80  # eBay's title length limit
        if len(title) <= max_length:
            return title

        # Prioritize components
        components = title.split(" - ")
        essential = components[0]  # Brand and model
        if len(components) > 1:
            features = components[1].split(", ")

            # Add features until we hit length limit
            optimized_features = []
            remaining_length = max_length - len(essential) - 3  # Account for " - "

            for feature in features:
                if len(", ".join(optimized_features + [feature])) <= remaining_length:
                    optimized_features.append(feature)
                else:
                    break

            if optimized_features:
                return f"{essential} - {', '.join(optimized_features)}"
            return essential[:max_length]
        return essential[:max_length]

    def _enhance_feature(self, feature: str, feature_type: str) -> str:
        """Enhance feature presentation based on type."""
        if feature_type == "unique":
            return f"✨ {feature} (Exclusive Feature)"
        return f"• {feature}"

    def _optimize_keywords(self, keywords: List[str]) -> List[str]:
        """Optimize and prioritize keywords."""
        # Score each keyword
        keyword_scores = []
        for keyword in keywords:
            score = self._calculate_keyword_relevance(keyword)
            keyword_scores.append((keyword, score))

        # Sort by score and take top keywords
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        return [k for k, _ in keyword_scores[: self.max_keywords]]

    def _calculate_keyword_relevance(self, keyword: str) -> float:
        """Calculate keyword relevance score."""
        # Implement keyword scoring logic
        # This could consider search volume, competition, etc.
        return 1.0  # Placeholder

    def _get_trend_keywords(self, trend: TrendData) -> List[str]:
        """Get keywords based on market trends."""
        trend_keywords = []
        if trend.trend_type == "demand" and trend.direction == "up":
            trend_keywords.extend(["popular", "in-demand", "trending"])
        elif trend.trend_type == "price" and trend.direction == "up":
            trend_keywords.extend(["premium", "high-end", "luxury"])
        return trend_keywords

    def _get_category_keywords(self, category_id: str) -> List[str]:
        """Get category-specific keywords."""
        # Implement category keyword lookup
        return []  # Placeholder
