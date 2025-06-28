#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cross-Category Suggestion System

This module implements a cross-category recommendation system that identifies
relationships between products from different categories and suggests items
that complement each other across categorical boundaries.

The implementation supports various methods for discovering cross-category
relationships, including collaborative filtering patterns, semantic similarity,
and purchase sequence analysis.
"""

import heapq
import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# Import necessary components from other modules
from fs_agt_clean.services.recommendations.cross_product.relationships import (
    ProductRelationship,
    RelationshipType,
)

logger = logging.getLogger(__name__)


class CrossCategoryMethod(str, Enum):
    """Methods for identifying cross-category relationships."""

    COLLABORATIVE_PATTERNS = (
        "collaborative_patterns"  # Based on user purchase/view patterns
    )
    SEMANTIC_SIMILARITY = (
        "semantic_similarity"  # Based on product description similarity
    )
    PURCHASE_SEQUENCE = "purchase_sequence"  # Based on purchase sequence analysis
    MANUAL_CURATION = "manual_curation"  # Based on manually curated relationships
    HYBRID = "hybrid"  # Combination of multiple methods


@dataclass
class CategoryRelationship:
    """Relationship between two product categories."""

    source_category: str
    target_category: str
    relationship_strength: float  # 0.0 to 1.0
    evidence_count: int  # Number of data points supporting this relationship
    method: CrossCategoryMethod
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossCategoryConfig:
    """Configuration for cross-category suggestion system."""

    min_relationship_strength: float = (
        0.1  # Minimum strength to consider a relationship valid
    )
    min_evidence_count: int = 3  # Minimum data points to establish a relationship
    max_category_distance: int = (
        2  # Maximum category tree distance for related categories
    )
    enable_collaborative_patterns: bool = True
    enable_semantic_similarity: bool = True
    enable_purchase_sequence: bool = True
    enable_manual_curation: bool = True
    max_suggestions_per_category: int = (
        5  # Maximum suggestions from each related category
    )
    recency_boost_factor: float = 1.5  # Boost factor for recent relationships
    recency_window_days: int = 30  # Window for recency boost


class CrossCategorySuggestion:
    """
    Cross-category product suggestion system.

    This class analyzes product interactions, descriptions, and purchase patterns
    to identify meaningful relationships between products from different categories.
    """

    def __init__(self, config: Optional[CrossCategoryConfig] = None):
        """
        Initialize the cross-category suggestion system.

        Args:
            config: Configuration options (optional)
        """
        self.config = config or CrossCategoryConfig()

        # Core data structures
        self.category_relationships: Dict[Tuple[str, str], CategoryRelationship] = {}
        self.category_hierarchy: Dict[str, Dict[str, Any]] = {}
        self.product_categories: Dict[str, List[str]] = {}
        self.category_products: DefaultDict[str, List[str]] = defaultdict(list)

        # Statistics and metadata
        self.category_popularity: Dict[str, int] = {}
        self.cross_purchases: DefaultDict[Tuple[str, str], int] = defaultdict(int)

        logger.info("Initialized cross-category suggestion system")

    def fit(
        self,
        product_data: Dict[str, Dict[str, Any]],
        user_interactions: Optional[List[Dict[str, Any]]] = None,
        manual_relationships: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Build the cross-category relationship model.

        Args:
            product_data: Dictionary of product data with categories
            user_interactions: List of user interaction data (optional)
            manual_relationships: List of manually defined relationships (optional)
        """
        logger.info(
            "Building cross-category relationship model with %d products",
            len(product_data),
        )

        # Process product category data
        self._process_product_categories(product_data)

        # Build category hierarchy if not already built
        if not self.category_hierarchy:
            self._build_category_hierarchy(product_data)

        # Process different relationship sources based on configuration
        if self.config.enable_collaborative_patterns and user_interactions:
            self._analyze_collaborative_patterns(user_interactions)

        if self.config.enable_semantic_similarity and product_data:
            self._analyze_semantic_similarity(product_data)

        if self.config.enable_purchase_sequence and user_interactions:
            self._analyze_purchase_sequences(user_interactions)

        if self.config.enable_manual_curation and manual_relationships:
            self._process_manual_relationships(manual_relationships)

        # Combine all relationship sources
        self._combine_relationship_sources()

        logger.info(
            "Cross-category model built with %d category relationships",
            len(self.category_relationships),
        )

    def suggest_cross_category_products(
        self,
        product_id: str,
        max_suggestions: int = 10,
        excluded_categories: Optional[List[str]] = None,
        excluded_products: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Suggest products from different categories based on the given product.

        Args:
            product_id: Source product ID
            max_suggestions: Maximum number of suggestions to return
            excluded_categories: Categories to exclude from suggestions
            excluded_products: Product IDs to exclude from suggestions

        Returns:
            List of cross-category product suggestions with metadata
        """
        excluded_categories = excluded_categories or []
        excluded_products = excluded_products or []

        if product_id not in self.product_categories:
            logger.warning("Product %s not found in category data", product_id)
            return []

        # Get product categories
        product_cats = self.product_categories[product_id]

        # Find related categories
        related_categories = self._find_related_categories(
            product_cats, excluded_categories
        )

        # Build suggestions from related categories
        suggestions = []

        for rel_cat, strength in related_categories:
            # Skip if this would exceed our suggestion limit
            if len(suggestions) >= max_suggestions:
                break

            # Get products from this category
            category_products = self.category_products.get(rel_cat, [])

            # Filter out excluded products
            category_products = [
                p for p in category_products if p not in excluded_products
            ]

            # Rank products within this category (implementation dependent on available data)
            ranked_products = self._rank_products_in_category(
                rel_cat, category_products, source_product=product_id
            )

            # Take top N from this category
            top_products = ranked_products[: self.config.max_suggestions_per_category]

            # Add to suggestions with relationship data
            for prod in top_products:
                if len(suggestions) >= max_suggestions:
                    break

                suggestions.append(
                    {
                        "product_id": prod["product_id"],
                        "score": prod["score"] * strength,
                        "category": rel_cat,
                        "relationship_strength": strength,
                        "source_categories": product_cats,
                        "suggestion_reason": f"Frequently purchased with products from {', '.join(product_cats)}",
                    }
                )

        # Sort by overall score
        suggestions.sort(key=lambda x: x["score"], reverse=True)

        return suggestions[:max_suggestions]

    def find_complementary_categories(
        self, category: str, max_categories: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find categories that complement the given category.

        Args:
            category: Source category
            max_categories: Maximum number of complementary categories to return

        Returns:
            List of tuples with (category, strength) sorted by strength
        """
        complementary_categories = []

        for (source, target), relationship in self.category_relationships.items():
            if source == category:
                complementary_categories.append(
                    (target, relationship.relationship_strength)
                )
            elif target == category:
                complementary_categories.append(
                    (source, relationship.relationship_strength)
                )

        # Sort by strength and return top results
        complementary_categories.sort(key=lambda x: x[1], reverse=True)
        return complementary_categories[:max_categories]

    def _process_product_categories(
        self, product_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Process product category information from product data."""
        self.product_categories = {}
        self.category_products = defaultdict(list)
        self.category_popularity = defaultdict(int)

        for product_id, data in product_data.items():
            if "category" not in data:
                continue

            # Handle both string and list category formats
            categories = (
                data["category"]
                if isinstance(data["category"], list)
                else [data["category"]]
            )

            # Store mapping from product to categories
            self.product_categories[product_id] = categories

            # Store mapping from category to products and update popularity
            for category in categories:
                self.category_products[category].append(product_id)
                self.category_popularity[category] += 1

    def _build_category_hierarchy(
        self, product_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Build category hierarchy from product data."""
        # This implementation will depend on how categories are structured in your system
        # For now, we'll implement a simple version that assumes categories may have
        # parent/child relationships encoded in their names (e.g., "Electronics/Computers")

        hierarchy = {}
        categories = set()

        # Gather all categories
        for product_data in product_data.values():
            if "category" in product_data:
                cats = (
                    product_data["category"]
                    if isinstance(product_data["category"], list)
                    else [product_data["category"]]
                )
                categories.update(cats)

        # Build hierarchy
        for category in categories:
            parts = category.split("/")
            current = hierarchy

            # Build path through hierarchy
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"products": 0, "subcategories": {}}

                if i < len(parts) - 1:
                    current = current[part]["subcategories"]

        self.category_hierarchy = hierarchy

    def _analyze_collaborative_patterns(
        self, user_interactions: List[Dict[str, Any]]
    ) -> None:
        """
        Analyze collaborative patterns to identify cross-category relationships.

        This method looks for patterns where users interact with products from
        different categories in close succession or in the same session.
        """
        # Group interactions by user
        user_interactions_map = defaultdict(list)
        for interaction in user_interactions:
            user_id = interaction.get("user_id")
            product_id = interaction.get("product_id")

            if (
                not user_id
                or not product_id
                or product_id not in self.product_categories
            ):
                continue

            user_interactions_map[user_id].append(interaction)

        # Analyze cross-category interactions for each user
        cross_category_counts = defaultdict(int)

        for user_id, interactions in user_interactions_map.items():
            # Sort by timestamp if available
            if "timestamp" in interactions[0]:
                interactions.sort(key=lambda x: x["timestamp"])

            # Find products from different categories that were interacted with
            seen_categories = set()
            for interaction in interactions:
                product_id = interaction.get("product_id")

                if product_id in self.product_categories:
                    for category in self.product_categories[product_id]:
                        # Check for cross-category relationships with previously seen categories
                        for seen_cat in seen_categories:
                            if seen_cat != category:
                                # Order categories alphabetically for consistent keys
                                if seen_cat < category:
                                    cross_category_counts[(seen_cat, category)] += 1
                                else:
                                    cross_category_counts[(category, seen_cat)] += 1

                        seen_categories.add(category)

        # Convert to relationship objects
        for (source, target), count in cross_category_counts.items():
            # Skip weak relationships
            if count < self.config.min_evidence_count:
                continue

            # Calculate strength based on evidence count relative to category popularity
            source_pop = self.category_popularity.get(source, 1)
            target_pop = self.category_popularity.get(target, 1)

            # Normalize by the geometric mean of category popularities
            strength = count / math.sqrt(source_pop * target_pop)

            # Create relationship object
            relationship = CategoryRelationship(
                source_category=source,
                target_category=target,
                relationship_strength=min(1.0, strength * 5),  # Scale and cap at 1.0
                evidence_count=count,
                method=CrossCategoryMethod.COLLABORATIVE_PATTERNS,
            )

            # Store relationship
            self.category_relationships[(source, target)] = relationship

    def _analyze_semantic_similarity(
        self, product_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Analyze semantic similarity between products from different categories.

        This implementation assumes product descriptions are available in the product data.
        """
        # Placeholder implementation - in a real system, this would use NLP techniques
        # to analyze product descriptions and identify semantic similarities
        logger.info("Semantic similarity analysis would be performed here")

        # For demonstration purposes, we'll create some example relationships
        # In a real implementation, these would be derived from text analysis
        example_relationships = [
            ("Electronics/Computers", "Electronics/Accessories", 0.8, 20),
            ("Clothing/Men", "Accessories/Men", 0.7, 15),
            ("Cooking/Appliances", "Cooking/Utensils", 0.9, 25),
        ]

        for source, target, strength, count in example_relationships:
            if (source, target) not in self.category_relationships:
                relationship = CategoryRelationship(
                    source_category=source,
                    target_category=target,
                    relationship_strength=strength,
                    evidence_count=count,
                    method=CrossCategoryMethod.SEMANTIC_SIMILARITY,
                )
                self.category_relationships[(source, target)] = relationship

    def _analyze_purchase_sequences(
        self, user_interactions: List[Dict[str, Any]]
    ) -> None:
        """
        Analyze purchase sequences to identify cross-category relationships.

        This method looks for sequential purchases across different categories
        to identify complementary product categories.
        """
        # Group purchase interactions by user
        user_purchases = defaultdict(list)

        for interaction in user_interactions:
            if interaction.get("interaction_type") != "purchase":
                continue

            user_id = interaction.get("user_id")
            product_id = interaction.get("product_id")
            timestamp = interaction.get("timestamp")

            if (
                not user_id
                or not product_id
                or product_id not in self.product_categories
            ):
                continue

            user_purchases[user_id].append((product_id, timestamp))

        # Analyze purchase sequences
        sequence_patterns = defaultdict(int)

        for user_id, purchases in user_purchases.items():
            # Sort by timestamp if available
            if purchases and purchases[0][1]:
                purchases.sort(key=lambda x: x[1])

            # Look at sequential purchases
            for i in range(len(purchases) - 1):
                current_product, _ = purchases[i]
                next_product, _ = purchases[i + 1]

                current_categories = self.product_categories.get(current_product, [])
                next_categories = self.product_categories.get(next_product, [])

                # Look for cross-category patterns
                for current_cat in current_categories:
                    for next_cat in next_categories:
                        if current_cat != next_cat:
                            # Order categories alphabetically for consistent keys
                            if current_cat < next_cat:
                                sequence_patterns[(current_cat, next_cat)] += 1
                            else:
                                sequence_patterns[(next_cat, current_cat)] += 1

        # Convert to relationship objects
        for (source, target), count in sequence_patterns.items():
            # Skip weak relationships
            if count < self.config.min_evidence_count:
                continue

            # Calculate strength based on evidence count
            source_pop = self.category_popularity.get(source, 1)
            target_pop = self.category_popularity.get(target, 1)

            # Normalize and apply a higher weight for purchase sequences
            strength = (count / math.sqrt(source_pop * target_pop)) * 1.5

            # Create or update relationship
            key = (source, target)
            if key in self.category_relationships:
                # Update existing relationship
                existing = self.category_relationships[key]
                if existing.method == CrossCategoryMethod.PURCHASE_SEQUENCE:
                    # Update evidence count and strength for the same method
                    existing.evidence_count += count
                    existing.relationship_strength = min(1.0, strength)
                    existing.updated_at = datetime.now()
                else:
                    # Different method, create a new hybrid relationship
                    combined_strength = (existing.relationship_strength + strength) / 2
                    self.category_relationships[key] = CategoryRelationship(
                        source_category=source,
                        target_category=target,
                        relationship_strength=min(1.0, combined_strength),
                        evidence_count=existing.evidence_count + count,
                        method=CrossCategoryMethod.HYBRID,
                        metadata={
                            "component_methods": [
                                existing.method,
                                CrossCategoryMethod.PURCHASE_SEQUENCE,
                            ]
                        },
                    )
            else:
                # Create new relationship
                self.category_relationships[key] = CategoryRelationship(
                    source_category=source,
                    target_category=target,
                    relationship_strength=min(1.0, strength),
                    evidence_count=count,
                    method=CrossCategoryMethod.PURCHASE_SEQUENCE,
                )

    def _process_manual_relationships(
        self, manual_relationships: List[Dict[str, Any]]
    ) -> None:
        """Process manually defined category relationships."""
        for rel_data in manual_relationships:
            source = rel_data.get("source_category")
            target = rel_data.get("target_category")
            strength = rel_data.get("strength", 1.0)

            if not source or not target:
                continue

            # Ensure consistent ordering
            if source > target:
                source, target = target, source

            # Create or update relationship
            key = (source, target)

            if key in self.category_relationships:
                # Update with manual data - prioritize manual curation
                existing = self.category_relationships[key]
                existing.relationship_strength = strength
                existing.method = CrossCategoryMethod.MANUAL_CURATION
                existing.updated_at = datetime.now()
                existing.metadata["manually_curated"] = True
            else:
                # Create new relationship
                self.category_relationships[key] = CategoryRelationship(
                    source_category=source,
                    target_category=target,
                    relationship_strength=strength,
                    evidence_count=10,  # Default value for manual relationships
                    method=CrossCategoryMethod.MANUAL_CURATION,
                    metadata={"manually_curated": True},
                )

    def _combine_relationship_sources(self) -> None:
        """Combine relationships from different sources into final model."""
        # This method would combine and normalize relationships from different sources
        # For now, we've been doing this incrementally in the analysis methods

        # Filter out weak relationships
        to_remove = []
        for key, relationship in self.category_relationships.items():
            if (
                relationship.relationship_strength
                < self.config.min_relationship_strength
                or relationship.evidence_count < self.config.min_evidence_count
            ):
                to_remove.append(key)

        for key in to_remove:
            del self.category_relationships[key]

    def _find_related_categories(
        self, source_categories: List[str], excluded_categories: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Find categories related to the source categories.

        Args:
            source_categories: List of source categories
            excluded_categories: Categories to exclude

        Returns:
            List of (category, strength) tuples sorted by strength
        """
        related_categories = {}

        # Check all relationships for matches with source categories
        for (source, target), relationship in self.category_relationships.items():
            if source in source_categories and target not in excluded_categories:
                if (
                    target not in related_categories
                    or relationship.relationship_strength > related_categories[target]
                ):
                    related_categories[target] = relationship.relationship_strength
            elif target in source_categories and source not in excluded_categories:
                if (
                    source not in related_categories
                    or relationship.relationship_strength > related_categories[source]
                ):
                    related_categories[source] = relationship.relationship_strength

        # Convert to list of tuples and sort by strength
        result = [(cat, strength) for cat, strength in related_categories.items()]
        result.sort(key=lambda x: x[1], reverse=True)

        return result

    def _rank_products_in_category(
        self, category: str, products: List[str], source_product: str
    ) -> List[Dict[str, Any]]:
        """
        Rank products within a category based on relevance to source product.

        Args:
            category: Category to rank products in
            products: List of product IDs to rank
            source_product: Source product ID for context

        Returns:
            List of ranked products with scores
        """
        # This is a placeholder implementation
        # In a real system, this would use product similarity, popularity, etc.

        ranked_products = []

        for product_id in products:
            # Skip the source product
            if product_id == source_product:
                continue

            # Create a random score for demonstration
            # In a real implementation, this would use actual relevance metrics
            score = 0.5 + (hash(product_id + source_product) % 100) / 200

            ranked_products.append({"product_id": product_id, "score": score})

        # Sort by score
        ranked_products.sort(key=lambda x: x["score"], reverse=True)

        return ranked_products
