#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Complementary Product Detection System

This module implements algorithms for detecting complementary products - items
that work well together or enhance each other's value when purchased or used
together.

The implementation supports various methods for detecting complementary
relationships, including co-purchase analysis, semantic complementarity,
and expert-defined rules.
"""

import heapq
import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# Import necessary components from other modules
from fs_agt_clean.services.recommendations.cross_product.relationships import (
    ProductRelationship,
    RelationshipType,
)

logger = logging.getLogger(__name__)


class ComplementaryMethod(str, Enum):
    """Methods for identifying complementary product relationships."""

    CO_PURCHASE = "co_purchase"  # Based on items frequently purchased together
    SEMANTIC = "semantic"  # Based on product descriptions and attributes
    SEQUENCE = "sequence"  # Based on purchase/view sequence analysis
    EXPERT_RULES = "expert_rules"  # Based on expert-defined rules
    HYBRID = "hybrid"  # Combination of multiple methods


class ComplementaryType(str, Enum):
    """Types of complementary relationships between products."""

    ACCESSORY = "accessory"  # One product is an accessory to another
    PART = "part"  # One product is a part of another
    EXTENSION = "extension"  # One product extends the functionality of another
    CONSUMABLE = "consumable"  # One product is consumed with another
    ENHANCEMENT = "enhancement"  # One product enhances another
    SET = "set"  # Products form a common set when used together
    GENERAL = "general"  # General complementary relationship


@dataclass
class ComplementaryConfig:
    """Configuration for complementary product detection."""

    min_confidence: float = 0.1  # Minimum confidence threshold
    min_support: int = 3  # Minimum number of co-purchases/views
    co_purchase_window_days: int = 30  # Window for co-purchase analysis
    max_complementary_items: int = 10  # Maximum complementary items per product
    co_purchase_weight: float = 1.0  # Weight for co-purchase signals
    semantic_weight: float = 0.8  # Weight for semantic signals
    sequence_weight: float = 0.7  # Weight for sequence signals
    expert_weight: float = 1.5  # Weight for expert-defined rules
    enable_co_purchase: bool = True
    enable_semantic: bool = True
    enable_sequence: bool = True
    enable_expert_rules: bool = True
    recency_boost_factor: float = 1.2  # Boost for recent signals
    recency_window_days: int = 14  # Window for recency boost


@dataclass
class ComplementaryRelationship:
    """Detailed relationship between complementary products."""

    source_id: str
    target_id: str
    confidence: float  # 0.0 to 1.0
    support: int  # Number of data points supporting this relationship
    complementary_type: ComplementaryType
    method: ComplementaryMethod
    bidirectional: bool = False  # Whether relationship applies in both directions
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_product_relationship(self) -> ProductRelationship:
        """Convert to a ProductRelationship for the general system."""
        return ProductRelationship(
            source_id=self.source_id,
            target_id=self.target_id,
            relationship_type=RelationshipType.COMPLEMENTARY,
            strength=self.confidence,
            metadata={
                "complementary_type": self.complementary_type,
                "method": self.method,
                "support": self.support,
                **self.metadata,
            },
            created_at=self.created_at,
            updated_at=self.updated_at,
            bidirectional=self.bidirectional,
        )


class ComplementaryProductDetector:
    """
    Complementary product detection system.

    This class implements multiple algorithms for detecting complementary product
    relationships based on purchase patterns, product attributes, and expert rules.
    """

    def __init__(self, config: Optional[ComplementaryConfig] = None):
        """
        Initialize the complementary product detector.

        Args:
            config: Configuration options (optional)
        """
        self.config = config or ComplementaryConfig()

        # Core data structures
        self.complementary_relationships: Dict[
            Tuple[str, str], ComplementaryRelationship
        ] = {}
        self.product_metadata: Dict[str, Dict[str, Any]] = {}
        self.product_categories: Dict[str, List[str]] = {}

        # Analysis data structures
        self.co_purchase_counts: Dict[Tuple[str, str], int] = {}
        self.purchase_sequences: Dict[Tuple[str, str], int] = {}
        self.semantic_scores: Dict[Tuple[str, str], float] = {}
        self.expert_rules: List[Dict[str, Any]] = []

        # Performance optimization
        self.product_complements: Dict[str, List[Tuple[str, float]]] = {}

        logger.info("Initialized complementary product detector")

    def fit(
        self,
        product_data: Dict[str, Dict[str, Any]],
        purchase_data: Optional[List[Dict[str, Any]]] = None,
        expert_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Build the complementary product model.

        Args:
            product_data: Dictionary of product data with attributes
            purchase_data: List of purchase/interaction data (optional)
            expert_rules: List of expert-defined complementary rules (optional)
        """
        logger.info(
            "Building complementary product model with %d products", len(product_data)
        )

        # Store product metadata
        self.product_metadata = product_data

        # Extract product categories if available
        self._extract_product_categories(product_data)

        # Process different data sources based on configuration
        if self.config.enable_co_purchase and purchase_data:
            self._analyze_co_purchases(purchase_data)

        if self.config.enable_semantic and product_data:
            self._analyze_semantic_complementarity(product_data)

        if self.config.enable_sequence and purchase_data:
            self._analyze_purchase_sequences(purchase_data)

        if self.config.enable_expert_rules and expert_rules:
            self.expert_rules = expert_rules
            self._apply_expert_rules(expert_rules)

        # Combine signals from different methods
        self._combine_complementary_signals()

        # Build optimized lookup structure
        self._build_product_complements_index()

        logger.info(
            "Complementary product model built with %d relationships",
            len(self.complementary_relationships),
        )

    def find_complementary_products(
        self,
        product_id: str,
        max_items: Optional[int] = None,
        min_confidence: Optional[float] = None,
        complement_type: Optional[ComplementaryType] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find complementary products for a given product.

        Args:
            product_id: Source product ID
            max_items: Maximum number of complementary items to return (optional)
            min_confidence: Minimum confidence threshold (optional)
            complement_type: Filter by complementary type (optional)

        Returns:
            List of complementary products with metadata
        """
        max_items = max_items or self.config.max_complementary_items
        min_confidence = min_confidence or self.config.min_confidence

        # Check if product exists
        if product_id not in self.product_metadata:
            logger.warning("Product %s not found in product data", product_id)
            return []

        # Use optimized lookup if available
        if product_id in self.product_complements:
            complementary_items = []

            for target_id, confidence in self.product_complements[product_id]:
                # Skip if below confidence threshold
                if confidence < min_confidence:
                    continue

                # Get relationship details
                relationship = self.complementary_relationships.get(
                    (product_id, target_id)
                ) or self.complementary_relationships.get((target_id, product_id))

                # Skip if relationship not found (shouldn't happen but defensive)
                if not relationship:
                    continue

                # Skip if not matching requested complement type
                if (
                    complement_type
                    and relationship.complementary_type != complement_type
                ):
                    continue

                # Add to results with metadata
                item_data = {
                    "product_id": target_id,
                    "confidence": confidence,
                    "complementary_type": relationship.complementary_type.value,
                    "method": relationship.method.value,
                    "support": relationship.support,
                }

                # Add product metadata if available
                if target_id in self.product_metadata:
                    item_data["product_data"] = self.product_metadata[target_id]

                complementary_items.append(item_data)

                # Stop if we've reached the limit
                if len(complementary_items) >= max_items:
                    break

            return complementary_items

        # Fallback to scanning all relationships
        complementary_items = []

        for (source, target), relationship in self.complementary_relationships.items():
            # Check if this relationship involves our product
            if source != product_id and target != product_id:
                continue

            # Determine the other product
            other_id = target if source == product_id else source

            # Skip if below confidence threshold
            if relationship.confidence < min_confidence:
                continue

            # Skip if not matching requested complement type
            if complement_type and relationship.complementary_type != complement_type:
                continue

            # For non-bidirectional relationships, check direction
            if not relationship.bidirectional and source != product_id:
                # This is a reverse relationship - only include if specifically requested
                # or if the relationship is suitable for reverse recommendation
                if relationship.complementary_type not in [
                    ComplementaryType.SET,
                    ComplementaryType.GENERAL,
                    ComplementaryType.ENHANCEMENT,
                ]:
                    continue

            # Add to results with metadata
            item_data = {
                "product_id": other_id,
                "confidence": relationship.confidence,
                "complementary_type": relationship.complementary_type.value,
                "method": relationship.method.value,
                "support": relationship.support,
            }

            # Add product metadata if available
            if other_id in self.product_metadata:
                item_data["product_data"] = self.product_metadata[other_id]

            complementary_items.append(item_data)

        # Sort by confidence and return top results
        complementary_items.sort(key=lambda x: x["confidence"], reverse=True)
        return complementary_items[:max_items]

    def get_all_complementary_pairs(
        self,
        min_confidence: Optional[float] = None,
        complement_type: Optional[ComplementaryType] = None,
    ) -> List[ComplementaryRelationship]:
        """
        Get all complementary product pairs matching the criteria.

        Args:
            min_confidence: Minimum confidence threshold (optional)
            complement_type: Filter by complementary type (optional)

        Returns:
            List of ComplementaryRelationship objects
        """
        min_confidence = min_confidence or self.config.min_confidence

        matching_relationships = []

        for relationship in self.complementary_relationships.values():
            if relationship.confidence < min_confidence:
                continue

            if complement_type and relationship.complementary_type != complement_type:
                continue

            matching_relationships.append(relationship)

        return matching_relationships

    def export_to_product_relationships(self) -> List[ProductRelationship]:
        """
        Export complementary relationships to standard ProductRelationship format.

        Returns:
            List of ProductRelationship objects
        """
        return [
            rel.to_product_relationship()
            for rel in self.complementary_relationships.values()
        ]

    def _extract_product_categories(
        self, product_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """Extract product category information from product data."""
        self.product_categories = {}

        for product_id, data in product_data.items():
            if "category" in data:
                # Handle both string and list category formats
                categories = (
                    data["category"]
                    if isinstance(data["category"], list)
                    else [data["category"]]
                )
                self.product_categories[product_id] = categories

    def _analyze_co_purchases(self, purchase_data: List[Dict[str, Any]]) -> None:
        """
        Analyze co-purchases to find complementary products.

        This method detects products frequently purchased together within
        the same order or by the same user within a time window.
        """
        logger.info("Analyzing co-purchases for complementary product detection")

        # Group purchases by order or user+time
        order_items: Dict[str, List[str]] = defaultdict(list)
        user_recent_purchases: Dict[str, List[Tuple[str, datetime]]] = defaultdict(list)

        for purchase in purchase_data:
            product_id = purchase.get("product_id")

            if not product_id:
                continue

            # Group by order ID if available
            order_id = purchase.get("order_id")
            if order_id:
                order_items[order_id].append(product_id)

            # Group by user and time window
            user_id = purchase.get("user_id")
            timestamp = purchase.get("timestamp")

            if user_id and timestamp:
                user_recent_purchases[user_id].append((product_id, timestamp))

        # Calculate co-purchase counts from order data
        co_purchase_counts = defaultdict(int)

        # First analyze order-based co-purchases
        for order_id, products in order_items.items():
            # Skip single-item orders
            if len(products) < 2:
                continue

            # Count all product pairs in this order
            for i, product1 in enumerate(products):
                for product2 in products[i + 1 :]:
                    # Ensure consistent ordering of product pairs
                    if product1 < product2:
                        co_purchase_counts[(product1, product2)] += 1
                    else:
                        co_purchase_counts[(product2, product1)] += 1

        # Then analyze time-window based co-purchases
        window_days = self.config.co_purchase_window_days

        for user_id, purchases in user_recent_purchases.items():
            # Sort purchases by timestamp
            purchases.sort(key=lambda x: x[1])

            # Find purchases within the time window
            for i, (product1, time1) in enumerate(purchases):
                for product2, time2 in purchases[i + 1 :]:
                    # Skip if same product
                    if product1 == product2:
                        continue

                    # Check if within time window
                    time_diff = time2 - time1
                    if time_diff.days > window_days:
                        break  # Too far apart, and later ones will be even further

                    # Ensure consistent ordering of product pairs
                    if product1 < product2:
                        co_purchase_counts[(product1, product2)] += 1
                    else:
                        co_purchase_counts[(product2, product1)] += 1

        # Store co-purchase counts
        self.co_purchase_counts = dict(co_purchase_counts)

        # Convert to complementary relationships
        for (product1, product2), count in co_purchase_counts.items():
            # Skip if below support threshold
            if count < self.config.min_support:
                continue

            # Calculate confidence score
            # We use a simple function that maps count to confidence with diminishing returns
            confidence = min(0.95, 1 - (1 / (1 + math.log(1 + count))))

            # Determine complementary type based on categories (if available)
            complement_type = self._determine_complementary_type(product1, product2)

            # Create relationship
            self.complementary_relationships[(product1, product2)] = (
                ComplementaryRelationship(
                    source_id=product1,
                    target_id=product2,
                    confidence=confidence,
                    support=count,
                    complementary_type=complement_type,
                    method=ComplementaryMethod.CO_PURCHASE,
                    # For co-purchases, we generally consider them bidirectional
                    bidirectional=True,
                )
            )

    def _analyze_semantic_complementarity(
        self, product_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Analyze semantic complementarity between products.

        This implementation would ideally use NLP/ML techniques to analyze product
        descriptions and attributes. For this implementation, we'll use a simplified
        approach based on product attributes and categories.
        """
        logger.info("Analyzing semantic complementarity between products")

        # Placeholder implementation - in a real system, this would use NLP techniques
        # to analyze product descriptions and attributes for complementary relationships

        # For demonstration, we'll look for complementary categories and attributes

        # Define some complementary category pairs (in a real system, these would be learned)
        complementary_categories = [
            ("Phones", "Phone Cases", 0.9, ComplementaryType.ACCESSORY),
            ("Laptops", "Laptop Bags", 0.85, ComplementaryType.ACCESSORY),
            ("Cameras", "Camera Lenses", 0.95, ComplementaryType.EXTENSION),
            ("Printers", "Ink Cartridges", 0.9, ComplementaryType.CONSUMABLE),
            ("Gaming Consoles", "Video Games", 0.8, ComplementaryType.CONSUMABLE),
            ("Coffee Makers", "Coffee Beans", 0.75, ComplementaryType.CONSUMABLE),
        ]

        # Find products in complementary categories
        for source_cat, target_cat, base_score, comp_type in complementary_categories:
            source_products = [
                pid
                for pid, data in product_data.items()
                if "category" in data
                and (
                    (
                        isinstance(data["category"], str)
                        and source_cat in data["category"]
                    )
                    or (
                        isinstance(data["category"], list)
                        and any(source_cat in cat for cat in data["category"])
                    )
                )
            ]

            target_products = [
                pid
                for pid, data in product_data.items()
                if "category" in data
                and (
                    (
                        isinstance(data["category"], str)
                        and target_cat in data["category"]
                    )
                    or (
                        isinstance(data["category"], list)
                        and any(target_cat in cat for cat in data["category"])
                    )
                )
            ]

            # Create semantic complementary relationships
            for source_id in source_products:
                for target_id in target_products:
                    # Skip self-relationships
                    if source_id == target_id:
                        continue

                    # Calculate confidence with some randomness for variety
                    # In a real implementation, this would be based on semantic similarity
                    confidence = base_score * (
                        0.9 + (hash(source_id + target_id) % 20) / 100
                    )

                    # Ensure consistent ordering of product pairs for lookup
                    key = (
                        (source_id, target_id)
                        if source_id < target_id
                        else (target_id, source_id)
                    )

                    # Store semantic score
                    self.semantic_scores[key] = confidence

                    # Only create relationship if we don't have a co-purchase based one
                    if key not in self.complementary_relationships:
                        self.complementary_relationships[key] = (
                            ComplementaryRelationship(
                                source_id=source_id,
                                target_id=target_id,
                                confidence=confidence,
                                support=5,  # Placeholder support value
                                complementary_type=comp_type,
                                method=ComplementaryMethod.SEMANTIC,
                                # For category-based, we typically have a direction
                                bidirectional=False,
                            )
                        )

    def _analyze_purchase_sequences(self, purchase_data: List[Dict[str, Any]]) -> None:
        """
        Analyze purchase sequences to find complementary products.

        This method looks at the sequence of purchases by users over time to
        identify products frequently purchased after others.
        """
        logger.info("Analyzing purchase sequences for complementary product detection")

        # Group purchases by user
        user_purchases = defaultdict(list)

        for purchase in purchase_data:
            user_id = purchase.get("user_id")
            product_id = purchase.get("product_id")
            timestamp = purchase.get("timestamp")

            if not user_id or not product_id or not timestamp:
                continue

            user_purchases[user_id].append((product_id, timestamp))

        # Analyze purchase sequences
        sequence_counts = defaultdict(int)

        for user_id, purchases in user_purchases.items():
            # Sort purchases by timestamp
            purchases.sort(key=lambda x: x[1])

            # Look at sequential purchases
            for i in range(len(purchases) - 1):
                product1, time1 = purchases[i]
                product2, time2 = purchases[i + 1]

                # Skip if same product
                if product1 == product2:
                    continue

                # Check if within reasonable time frame (e.g., 90 days)
                time_diff = time2 - time1
                if time_diff.days > 90:
                    continue

                # Record sequence
                sequence_counts[(product1, product2)] += 1

        # Store sequence counts
        self.purchase_sequences = dict(sequence_counts)

        # Convert to complementary relationships
        for (product1, product2), count in sequence_counts.items():
            # Skip if below support threshold
            if count < self.config.min_support:
                continue

            # Calculate confidence score
            confidence = min(0.9, 1 - (1 / (1 + math.log(1 + count))))

            # Determine complementary type
            complement_type = self._determine_complementary_type(product1, product2)

            # Create or update relationship
            key = (product1, product2) if product1 < product2 else (product2, product1)

            if key in self.complementary_relationships:
                # Update existing relationship
                existing = self.complementary_relationships[key]

                # If it's already a co-purchase, make it a hybrid
                if existing.method != ComplementaryMethod.SEQUENCE:
                    combined_confidence = (existing.confidence + confidence) / 2
                    combined_support = existing.support + count

                    self.complementary_relationships[key] = ComplementaryRelationship(
                        source_id=existing.source_id,
                        target_id=existing.target_id,
                        confidence=combined_confidence,
                        support=combined_support,
                        complementary_type=existing.complementary_type,
                        method=ComplementaryMethod.HYBRID,
                        bidirectional=existing.bidirectional,
                        metadata={
                            "component_methods": [
                                existing.method,
                                ComplementaryMethod.SEQUENCE,
                            ]
                        },
                    )
            else:
                # Create new relationship
                self.complementary_relationships[key] = ComplementaryRelationship(
                    source_id=product1,
                    target_id=product2,
                    confidence=confidence,
                    support=count,
                    complementary_type=complement_type,
                    method=ComplementaryMethod.SEQUENCE,
                    # For sequences, these are typically directional
                    bidirectional=False,
                )

    def _apply_expert_rules(self, expert_rules: List[Dict[str, Any]]) -> None:
        """
        Apply expert-defined rules for complementary products.

        Args:
            expert_rules: List of expert-defined complementary rules
        """
        logger.info("Applying expert-defined complementary product rules")

        for rule in expert_rules:
            source_id = rule.get("source_id")
            target_id = rule.get("target_id")

            if not source_id or not target_id:
                continue

            confidence = rule.get("confidence", 1.0)
            comp_type_str = rule.get("complementary_type", "general")

            # Convert string to enum
            try:
                comp_type = ComplementaryType(comp_type_str)
            except ValueError:
                comp_type = ComplementaryType.GENERAL

            # Ensure consistent ordering for lookup
            key = (
                (source_id, target_id)
                if source_id < target_id
                else (target_id, source_id)
            )

            # Create or update relationship
            if key in self.complementary_relationships:
                # For expert rules, we override existing information but mark as hybrid
                existing = self.complementary_relationships[key]
                self.complementary_relationships[key] = ComplementaryRelationship(
                    source_id=source_id,
                    target_id=target_id,
                    confidence=confidence,  # Use expert confidence
                    support=max(existing.support, 10),  # Ensure good support
                    complementary_type=comp_type,  # Use expert type
                    method=ComplementaryMethod.HYBRID,
                    bidirectional=rule.get("bidirectional", False),
                    metadata={
                        "expert_defined": True,
                        "previous_method": existing.method,
                    },
                )
            else:
                # Create new relationship
                self.complementary_relationships[key] = ComplementaryRelationship(
                    source_id=source_id,
                    target_id=target_id,
                    confidence=confidence,
                    support=10,  # Default support for expert rules
                    complementary_type=comp_type,
                    method=ComplementaryMethod.EXPERT_RULES,
                    bidirectional=rule.get("bidirectional", False),
                    metadata={"expert_defined": True},
                )

    def _combine_complementary_signals(self) -> None:
        """
        Combine complementary product signals from different sources.

        This method weights and combines signals from co-purchases, semantic analysis,
        purchase sequences, and expert rules into final complementary relationships.
        """
        logger.info("Combining complementary product signals from different sources")

        # The basic combination is already done incrementally in the analysis methods
        # Here we'll apply final adjustments and filtering

        # Apply recency boost if available
        self._apply_recency_boost()

        # Filter out low-confidence relationships
        to_remove = []
        for key, relationship in self.complementary_relationships.items():
            if relationship.confidence < self.config.min_confidence:
                to_remove.append(key)

        for key in to_remove:
            del self.complementary_relationships[key]

    def _apply_recency_boost(self) -> None:
        """Apply recency boost to recent complementary relationships."""
        # This would require timestamp data on when relationships were detected
        # For simplicity, we'll skip the actual implementation
        pass

    def _build_product_complements_index(self) -> None:
        """Build optimized index of complementary products for each product."""
        self.product_complements = defaultdict(list)

        for (source, target), relationship in self.complementary_relationships.items():
            # Always add in source->target direction
            self.product_complements[source].append((target, relationship.confidence))

            # If bidirectional, also add target->source
            if relationship.bidirectional:
                self.product_complements[target].append(
                    (source, relationship.confidence)
                )
            # Add reverse direction for certain types even if not explicitly bidirectional
            elif relationship.complementary_type in [
                ComplementaryType.SET,
                ComplementaryType.GENERAL,
            ]:
                self.product_complements[target].append(
                    (source, relationship.confidence * 0.9)
                )  # Slight penalty

        # Sort each product's complements by confidence
        for product_id, complements in self.product_complements.items():
            complements.sort(key=lambda x: x[1], reverse=True)
            # Limit to max items to avoid massive lists
            self.product_complements[product_id] = complements[:100]

    def _determine_complementary_type(
        self, product1: str, product2: str
    ) -> ComplementaryType:
        """
        Determine the most likely complementary relationship type between products.

        Args:
            product1: First product ID
            product2: Second product ID

        Returns:
            ComplementaryType enum value
        """
        # This is a simplified implementation
        # In a real system, this would use product attributes, categories, and ML

        # Check if we have category information
        if product1 in self.product_categories and product2 in self.product_categories:
            cat1 = self.product_categories[product1]
            cat2 = self.product_categories[product2]

            # Check for common accessory patterns
            for c1 in cat1:
                for c2 in cat2:
                    # Check for accessory relationship
                    if ("Accessories" in c2 and c1 in c2) or c2.endswith("Accessories"):
                        return ComplementaryType.ACCESSORY

                    # Check for part/extension relationships
                    if "Parts" in c2 or "Components" in c2:
                        return ComplementaryType.PART

                    # Check for consumable relationships
                    if any(
                        word in c2
                        for word in ["Ink", "Paper", "Cartridge", "Refill", "Filter"]
                    ):
                        return ComplementaryType.CONSUMABLE

        # Check for product attributes in metadata
        if product1 in self.product_metadata and product2 in self.product_metadata:
            meta1 = self.product_metadata[product1]
            meta2 = self.product_metadata[product2]

            # Check for set relationships
            if (
                "set_name" in meta1
                and "set_name" in meta2
                and meta1["set_name"] == meta2["set_name"]
            ):
                return ComplementaryType.SET

            # Check for part/extension relationships
            if "compatible_with" in meta2 and product1 in meta2.get(
                "compatible_with", []
            ):
                return ComplementaryType.EXTENSION

        # Default to general complementary relationship
        return ComplementaryType.GENERAL
