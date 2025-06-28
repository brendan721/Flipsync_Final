#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Upgrade/Downgrade Recommendation System

This module implements algorithms to identify and recommend product upgrades
and downgrades based on product relationships, specifications, and user behavior.

The system can identify products that represent:
1. Direct upgrades (newer versions of the same product)
2. Feature upgrades (products with enhanced capabilities)
3. Downgrades (more economical or simpler alternatives)
4. Sidegrades (alternative products with different trade-offs)
"""

import heapq
import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# Import necessary components from other modules
from fs_agt_clean.services.recommendations.cross_product.relationships import (
    ProductRelationship,
    RelationshipType,
)

logger = logging.getLogger(__name__)

# Sort each product's upgrades, downgrades, and sidegrades by confidence
for product_id in self.product_upgrades:
    self.product_upgrades[product_id].sort(key=lambda x: safe_float(x[1]), reverse=True)

for product_id in self.product_downgrades:
    self.product_downgrades[product_id].sort(
        key=lambda x: safe_float(x[1]), reverse=True
    )

for product_id in self.product_sidegrades:
    self.product_sidegrades[product_id].sort(
        key=lambda x: safe_float(x[1]), reverse=True
    )


# Helper functions for safe type conversions
def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def confidence_key(item: Dict[str, Any]) -> float:
    """Extract confidence as float for sorting."""
    conf = item.get("confidence", 0)
    return safe_float(conf)


def version_key(item: Tuple[str, Any]) -> float:
    """Extract version as float for sorting."""
    version = item[1]
    return safe_float(version)


class UpgradeMethod(str, Enum):
    """Methods for identifying upgrade/downgrade relationships."""

    VERSION_BASED = "version_based"  # Based on product version numbers
    SPEC_COMPARISON = "spec_comparison"  # Based on comparing specifications
    PRICE_TIER = "price_tier"  # Based on price tier analysis
    PURCHASE_PATTERN = "purchase_pattern"  # Based on user purchase patterns
    EXPERT_DEFINED = "expert_defined"  # Based on manually defined relationships
    HYBRID = "hybrid"  # Combination of multiple methods


class UpgradeType(str, Enum):
    """Types of upgrade relationships between products."""

    DIRECT_UPGRADE = "direct_upgrade"  # Direct replacement or newer version
    FEATURE_UPGRADE = "feature_upgrade"  # Better features/capabilities
    DOWNGRADE = "downgrade"  # More economical or simpler alternative
    SIDEGRADE = "sidegrade"  # Alternative with different trade-offs
    GENERATION_UPGRADE = "generation_upgrade"  # Next generation product


@dataclass
class UpgradeConfig:
    """Configuration for upgrade/downgrade detection."""

    min_confidence: float = 0.1  # Minimum confidence threshold
    min_version_diff: float = 0.1  # Minimum version difference to consider an upgrade
    max_price_ratio_upgrade: float = 3.0  # Maximum price ratio for an upgrade
    max_price_ratio_downgrade: float = 1.0  # Maximum price ratio for a downgrade
    enable_version_based: bool = True
    enable_spec_comparison: bool = True
    enable_price_tier: bool = True
    enable_purchase_pattern: bool = True
    enable_expert_defined: bool = True
    version_weight: float = 1.0
    spec_weight: float = 0.8
    price_weight: float = 0.6
    purchase_weight: float = 0.7
    expert_weight: float = 1.0
    recency_boost_factor: float = 1.2  # Boost for recent products
    recency_threshold_days: int = 365  # Days threshold for "recent" products
    max_recommendations: int = 5  # Default max recommendations per product


@dataclass
class UpgradeRelationship:
    """Detailed relationship between a product and its upgrade/downgrade options."""

    source_id: str
    target_id: str
    upgrade_type: UpgradeType
    confidence: float  # 0.0 to 1.0
    price_ratio: float = 1.0  # Target price / Source price
    specs_comparison: Dict[str, Any] = field(default_factory=dict)
    method: UpgradeMethod = UpgradeMethod.HYBRID
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    bidirectional: bool = False  # Usually False for upgrades
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_product_relationship(self) -> ProductRelationship:
        """Convert to a ProductRelationship for the general system."""
        relationship_type = RelationshipType.UPGRADE
        if self.upgrade_type == UpgradeType.DOWNGRADE:
            relationship_type = RelationshipType.DOWNGRADE
        elif self.upgrade_type == UpgradeType.SIDEGRADE:
            # Since ALTERNATIVE and RELATED don't exist, use a generic relationship type
            relationship_type = (
                RelationshipType.RECOMMENDED
            )  # Or another value that actually exists

        return ProductRelationship(
            source_id=self.source_id,
            target_id=self.target_id,
            relationship_type=relationship_type,
            strength=self.confidence,
            metadata={
                "upgrade_type": self.upgrade_type,
                "method": self.method,
                "price_ratio": self.price_ratio,
                "specs_comparison": self.specs_comparison,
                **self.metadata,
            },
            created_at=self.created_at,
            updated_at=self.updated_at,
            bidirectional=self.bidirectional,
        )


class UpgradeDowngradeDetector:
    """
    Upgrade and downgrade recommendation system.

    This class implements multiple algorithms for detecting upgrade and downgrade
    relationships between products based on specifications, versions, prices,
    and purchase patterns.
    """

    def __init__(self, config: Optional[UpgradeConfig] = None):
        """
        Initialize the upgrade/downgrade detector.

        Args:
            config: Configuration options (optional)
        """
        self.config = config or UpgradeConfig()

        # Core data structures
        self.upgrade_relationships: Dict[Tuple[str, str], UpgradeRelationship] = {}
        self.product_metadata: Dict[str, Dict[str, Any]] = {}
        self.product_categories: Dict[str, List[str]] = {}
        self.product_families: Dict[str, str] = {}
        self.product_versions: Dict[str, Union[str, float]] = {}
        self.product_specs: Dict[str, Dict[str, Any]] = {}
        self.product_prices: Dict[str, float] = {}
        self.product_release_dates: Dict[str, datetime] = {}

        # Analysis data structures
        self.version_scores: Dict[Tuple[str, str], float] = {}
        self.spec_scores: Dict[Tuple[str, str], Dict[str, float]] = {}
        self.price_tier_data: Dict[str, List[Tuple[str, float]]] = {}
        self.purchase_pattern_data: Dict[Tuple[str, str], int] = {}

        # Output data structures for quick lookup
        self.product_upgrades: Dict[str, List[Tuple[str, float]]] = {}
        self.product_downgrades: Dict[str, List[Tuple[str, float]]] = {}
        self.product_sidegrades: Dict[str, List[Tuple[str, float]]] = {}

        logger.info("Initialized upgrade/downgrade detector")

    def fit(
        self,
        product_data: Dict[str, Dict[str, Any]],
        purchase_data: Optional[List[Dict[str, Any]]] = None,
        expert_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Build the upgrade/downgrade relationship model.

        Args:
            product_data: Dictionary of product data with attributes
            purchase_data: List of purchase/interaction data (optional)
            expert_rules: List of expert-defined upgrade rules (optional)
        """
        logger.info(
            "Building upgrade/downgrade model with %d products", len(product_data)
        )

        # Store product metadata and extract core attributes
        self._extract_product_attributes(product_data)

        # Process different data sources based on configuration
        if self.config.enable_version_based:
            self._analyze_version_based_upgrades()

        if self.config.enable_spec_comparison and len(self.product_specs) > 0:
            self._analyze_spec_based_upgrades()

        if self.config.enable_price_tier and len(self.product_prices) > 0:
            self._analyze_price_tier_relationships()

        if self.config.enable_purchase_pattern and purchase_data:
            self._analyze_purchase_patterns(purchase_data)

        if self.config.enable_expert_defined and expert_rules:
            self._apply_expert_rules(expert_rules)

        # Combine signals from different methods
        self._combine_upgrade_signals()

        # Build optimized lookup structures
        self._build_product_upgrades_index()

        logger.info(
            "Upgrade/downgrade model built with %d relationships",
            len(self.upgrade_relationships),
        )

    def find_upgrades(
        self,
        product_id: str,
        max_items: Optional[int] = None,
        min_confidence: Optional[float] = None,
        upgrade_type: Optional[UpgradeType] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find upgrade options for a given product.

        Args:
            product_id: Source product ID
            max_items: Maximum number of upgrades to return (optional)
            min_confidence: Minimum confidence threshold (optional)
            upgrade_type: Filter by upgrade type (optional)

        Returns:
            List of upgrade products with metadata
        """
        max_items = max_items or self.config.max_recommendations
        min_confidence = min_confidence or self.config.min_confidence

        # Check if product exists
        if product_id not in self.product_metadata:
            logger.warning("Product %s not found in product data", product_id)
            return []

        # Use optimized lookup if available and no specific upgrade type is requested
        if product_id in self.product_upgrades and not upgrade_type:
            upgrades = []

            for target_id, confidence in self.product_upgrades[product_id]:
                # Skip if below confidence threshold
                if confidence < min_confidence:
                    continue

                # Get relationship details
                relationship = self.upgrade_relationships.get((product_id, target_id))

                # Skip if relationship not found (shouldn't happen but defensive)
                if not relationship:
                    continue

                # Add to results with metadata
                upgrade_data = {
                    "product_id": target_id,
                    "confidence": confidence,
                    "upgrade_type": relationship.upgrade_type.value,
                    "price_ratio": relationship.price_ratio,
                    "method": relationship.method.value,
                }

                # Add product metadata if available
                if target_id in self.product_metadata:
                    upgrade_data["product_data"] = self.product_metadata[target_id]

                # Add spec comparison if available
                if relationship.specs_comparison:
                    upgrade_data["specs_comparison"] = relationship.specs_comparison

                upgrades.append(upgrade_data)

                # Stop if we've reached the limit
                if len(upgrades) >= max_items:
                    break

            upgrades.sort(key=confidence_key, reverse=True)
            return upgrades[:max_items]

        # Fallback or specific upgrade type requested
        upgrades = []

        for (source, target), relationship in self.upgrade_relationships.items():
            # Check if this is an upgrade for our product
            if source != product_id:
                continue

            # Skip if below confidence threshold
            if relationship.confidence < min_confidence:
                continue

            # Skip if not matching requested upgrade type
            if upgrade_type and relationship.upgrade_type != upgrade_type:
                continue

            # Skip if not an upgrade (e.g., downgrade relationship)
            if relationship.upgrade_type not in [
                UpgradeType.DIRECT_UPGRADE,
                UpgradeType.FEATURE_UPGRADE,
                UpgradeType.GENERATION_UPGRADE,
            ]:
                continue

            # Add to results with metadata
            upgrade_data = {
                "product_id": target,
                "confidence": relationship.confidence,
                "upgrade_type": relationship.upgrade_type.value,
                "price_ratio": relationship.price_ratio,
                "method": relationship.method.value,
            }

            # Add product metadata if available
            if target in self.product_metadata:
                upgrade_data["product_data"] = self.product_metadata[target]

            # Add spec comparison if available
            if relationship.specs_comparison:
                upgrade_data["specs_comparison"] = relationship.specs_comparison

            upgrades.append(upgrade_data)

        # Sort by confidence and return top results
        upgrades.sort(key=confidence_key, reverse=True)
        return upgrades[:max_items]

    def find_downgrades(
        self,
        product_id: str,
        max_items: Optional[int] = None,
        min_confidence: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find downgrade options for a given product.

        Args:
            product_id: Source product ID
            max_items: Maximum number of downgrades to return (optional)
            min_confidence: Minimum confidence threshold (optional)

        Returns:
            List of downgrade products with metadata
        """
        max_items = max_items or self.config.max_recommendations
        min_confidence = min_confidence or self.config.min_confidence

        # Check if product exists
        if product_id not in self.product_metadata:
            logger.warning("Product %s not found in product data", product_id)
            return []

        # Use optimized lookup if available
        if product_id in self.product_downgrades:
            downgrades = []

            for target_id, confidence in self.product_downgrades[product_id]:
                # Skip if below confidence threshold
                if confidence < min_confidence:
                    continue

                # Get relationship details
                relationship = self.upgrade_relationships.get(
                    (target_id, product_id)
                ) or self.upgrade_relationships.get((product_id, target_id))

                # Skip if relationship not found
                if not relationship:
                    continue

                # Add to results with metadata
                downgrade_data = {
                    "product_id": target_id,
                    "confidence": confidence,
                    "downgrade_type": relationship.upgrade_type.value,
                    "price_ratio": (
                        1.0 / relationship.price_ratio
                        if relationship.price_ratio > 0
                        else 0
                    ),
                    "method": relationship.method.value,
                }

                # Add product metadata if available
                if target_id in self.product_metadata:
                    downgrade_data["product_data"] = self.product_metadata[target_id]

                # Add spec comparison if available
                if relationship.specs_comparison:
                    # Reverse the comparison for downgrades
                    downgrade_data["specs_comparison"] = {
                        k: -safe_float(v) if isinstance(v, (int, float, str)) else v
                        for k, v in relationship.specs_comparison.items()
                    }

                downgrades.append(downgrade_data)

                # Stop if we've reached the limit
                if len(downgrades) >= max_items:
                    break

            downgrades.sort(key=confidence_key, reverse=True)
            return downgrades[:max_items]

        # Fallback to scanning all relationships
        downgrades = []

        for (source, target), relationship in self.upgrade_relationships.items():
            # Two cases: either it's a downgrade relationship from product_id
            # or it's an upgrade relationship to product_id (which means product_id is a downgrade of source)
            is_downgrade = (
                source == product_id
                and relationship.upgrade_type == UpgradeType.DOWNGRADE
            )
            is_upgrade_to_product = (
                target == product_id
                and relationship.upgrade_type
                in [
                    UpgradeType.DIRECT_UPGRADE,
                    UpgradeType.FEATURE_UPGRADE,
                    UpgradeType.GENERATION_UPGRADE,
                ]
            )

            if not (is_downgrade or is_upgrade_to_product):
                continue

            # Determine the other product
            other_id = target if source == product_id else source

            # Skip if below confidence threshold
            if relationship.confidence < min_confidence:
                continue

            # Add to results with metadata
            downgrade_data = {
                "product_id": other_id,
                "confidence": relationship.confidence,
                "downgrade_type": (
                    "explicit_downgrade" if is_downgrade else "inverse_upgrade"
                ),
                "price_ratio": (
                    relationship.price_ratio
                    if is_downgrade
                    else (
                        1.0 / relationship.price_ratio
                        if relationship.price_ratio > 0
                        else 0
                    )
                ),
                "method": relationship.method.value,
            }

            # Add product metadata if available
            if other_id in self.product_metadata:
                downgrade_data["product_data"] = self.product_metadata[other_id]

            # Add spec comparison if available
            if relationship.specs_comparison:
                # For upgrades to product_id, we need to reverse the comparison
                if is_upgrade_to_product:
                    downgrade_data["specs_comparison"] = {
                        k: -safe_float(v) if isinstance(v, (int, float, str)) else v
                        for k, v in relationship.specs_comparison.items()
                    }
                else:
                    downgrade_data["specs_comparison"] = relationship.specs_comparison

            downgrades.append(downgrade_data)

        # Sort by confidence and return top results
        downgrades.sort(key=confidence_key, reverse=True)
        return downgrades[:max_items]

    def find_alternatives(
        self,
        product_id: str,
        max_items: Optional[int] = None,
        min_confidence: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find alternative options (sidegrades) for a given product.

        Args:
            product_id: Source product ID
            max_items: Maximum number of alternatives to return (optional)
            min_confidence: Minimum confidence threshold (optional)

        Returns:
            List of alternative products with metadata
        """
        max_items = max_items or self.config.max_recommendations
        min_confidence = min_confidence or self.config.min_confidence

        # Check if product exists
        if product_id not in self.product_metadata:
            logger.warning("Product %s not found in product data", product_id)
            return []

        # Use optimized lookup if available
        if product_id in self.product_sidegrades:
            alternatives = []

            for target_id, confidence in self.product_sidegrades[product_id]:
                # Skip if below confidence threshold
                if confidence < min_confidence:
                    continue

                # Get relationship details
                relationship = self.upgrade_relationships.get(
                    (product_id, target_id)
                ) or self.upgrade_relationships.get((target_id, product_id))

                # Skip if relationship not found
                if not relationship:
                    continue

                # Add to results with metadata
                alt_data = {
                    "product_id": target_id,
                    "confidence": confidence,
                    "alternative_type": "sidegrade",
                    "price_ratio": relationship.price_ratio,
                    "method": relationship.method.value,
                }

                # Add product metadata if available
                if target_id in self.product_metadata:
                    alt_data["product_data"] = self.product_metadata[target_id]

                # Add spec comparison if available
                if relationship.specs_comparison:
                    alt_data["specs_comparison"] = relationship.specs_comparison

                alternatives.append(alt_data)

                # Stop if we've reached the limit
                if len(alternatives) >= max_items:
                    break

            alternatives.sort(key=confidence_key, reverse=True)
            return alternatives[:max_items]

        # Fallback to scanning all relationships
        alternatives = []

        for (source, target), relationship in self.upgrade_relationships.items():
            # Check if this relationship involves our product
            if source != product_id and target != product_id:
                continue

            # Determine the other product
            other_id = target if source == product_id else source

            # Skip if below confidence threshold
            if relationship.confidence < min_confidence:
                continue

            # Skip if not a sidegrade relationship
            if relationship.upgrade_type != UpgradeType.SIDEGRADE:
                continue

            # Add to results with metadata
            alt_data = {
                "product_id": other_id,
                "confidence": relationship.confidence,
                "alternative_type": "sidegrade",
                "price_ratio": (
                    relationship.price_ratio
                    if source == product_id
                    else 1.0 / relationship.price_ratio
                ),
                "method": relationship.method.value,
            }

            # Add product metadata if available
            if other_id in self.product_metadata:
                alt_data["product_data"] = self.product_metadata[other_id]

            # Add spec comparison if available
            if relationship.specs_comparison:
                # If product_id is the target, reverse the comparison
                if target == product_id:
                    alt_data["specs_comparison"] = {
                        k: -safe_float(v) if isinstance(v, (int, float, str)) else v
                        for k, v in relationship.specs_comparison.items()
                    }
                else:
                    alt_data["specs_comparison"] = relationship.specs_comparison

            alternatives.append(alt_data)

        # Sort by confidence and return top results
        alternatives.sort(key=confidence_key, reverse=True)
        return alternatives[:max_items]

    def export_to_product_relationships(self) -> List[ProductRelationship]:
        """
        Export upgrade/downgrade relationships to standard ProductRelationship format.

        Returns:
            List of ProductRelationship objects
        """
        return [
            rel.to_product_relationship() for rel in self.upgrade_relationships.values()
        ]

    def _extract_product_attributes(
        self, product_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Extract relevant product attributes from product data.

        This method extracts product families, versions, specifications, prices,
        and other attributes needed for upgrade/downgrade analysis.
        """
        self.product_metadata = product_data

        for product_id, data in product_data.items():
            # Extract product family/line information
            family = (
                data.get("product_family")
                or data.get("product_line")
                or data.get("series")
            )
            if family:
                self.product_families[product_id] = family

            # Extract version information
            version = data.get("version") or data.get("model_version")
            if version:
                # Try to convert to float for easier comparison
                try:
                    self.product_versions[product_id] = float(version)
                except (ValueError, TypeError):
                    self.product_versions[product_id] = version

            # Extract price information
            price = data.get("price") or data.get("msrp") or data.get("base_price")
            if price:
                try:
                    self.product_prices[product_id] = float(price)
                except (ValueError, TypeError):
                    pass

            # Extract release date
            release_date = data.get("release_date") or data.get("launch_date")
            if release_date and isinstance(release_date, (datetime, str)):
                if isinstance(release_date, str):
                    try:
                        release_date = datetime.fromisoformat(release_date)
                        self.product_release_dates[product_id] = release_date
                    except (ValueError, TypeError):
                        pass
                else:
                    self.product_release_dates[product_id] = release_date

            # Extract specifications
            specs = data.get("specifications") or data.get("specs") or {}
            if specs and isinstance(specs, dict):
                self.product_specs[product_id] = specs

            # Extract categories
            category = data.get("category") or data.get("categories") or []
            if category:
                if isinstance(category, str):
                    self.product_categories[product_id] = [category]
                elif isinstance(category, list):
                    self.product_categories[product_id] = category

    def _analyze_version_based_upgrades(self) -> None:
        """
        Analyze version-based upgrades within product families.

        This method identifies upgrade relationships based on version numbers
        within the same product family/line.
        """
        logger.info("Analyzing version-based upgrades")

        # Group products by family
        family_products = defaultdict(list)
        for product_id, family in self.product_families.items():
            family_products[family].append(product_id)

        # For each family, analyze version-based relationships
        for family, products in family_products.items():
            # Skip families with only one product
            if len(products) < 2:
                continue

            # Find products with version information
            versioned_products = [p for p in products if p in self.product_versions]

            # Skip if not enough versioned products
            if len(versioned_products) < 2:
                continue

            # For numeric versions, sort and analyze
            numeric_versions = []
            non_numeric = []

            for product in versioned_products:
                version = self.product_versions[product]
                if isinstance(version, (int, float)):
                    numeric_versions.append((product, version))
                else:
                    non_numeric.append((product, version))

            # Analyze numeric versions
            if len(numeric_versions) >= 2:
                # Sort by version
                numeric_versions.sort(key=version_key)

                # Create upgrade relationships
                for i in range(len(numeric_versions) - 1):
                    for j in range(i + 1, len(numeric_versions)):
                        source_id, source_ver = numeric_versions[i]
                        target_id, target_ver = numeric_versions[j]

                        # Skip if version difference is too small
                        if target_ver - source_ver < self.config.min_version_diff:
                            continue

                        # Calculate confidence based on version difference and recency
                        version_diff_factor = min(1.0, (target_ver - source_ver) / 10.0)

                        # Add recency boost if available
                        recency_factor = 1.0
                        if (
                            source_id in self.product_release_dates
                            and target_id in self.product_release_dates
                        ):
                            source_date = self.product_release_dates[source_id]
                            target_date = self.product_release_dates[target_id]

                            # Only consider newer products as upgrades
                            if target_date <= source_date:
                                continue

                            # Apply recency boost for recent products
                            now = datetime.now()
                            if (
                                now - target_date
                            ).days < self.config.recency_threshold_days:
                                recency_factor = self.config.recency_boost_factor

                        # Calculate confidence
                        confidence = (
                            min(0.95, 0.5 + (version_diff_factor * 0.5))
                            * recency_factor
                        )

                        # Store version score
                        self.version_scores[(source_id, target_id)] = confidence

                        # Calculate price ratio if available
                        price_ratio = 1.0
                        if (
                            source_id in self.product_prices
                            and target_id in self.product_prices
                        ):
                            source_price = self.product_prices[source_id]
                            target_price = self.product_prices[target_id]

                            if source_price > 0:
                                price_ratio = target_price / source_price

                        # Determine upgrade type based on version and price
                        upgrade_type = UpgradeType.DIRECT_UPGRADE

                        # If there are products in between, it's a generation upgrade
                        if j - i > 1:
                            upgrade_type = UpgradeType.GENERATION_UPGRADE

                        # Create relationship
                        relationship = UpgradeRelationship(
                            source_id=source_id,
                            target_id=target_id,
                            upgrade_type=upgrade_type,
                            confidence=confidence,
                            price_ratio=price_ratio,
                            method=UpgradeMethod.VERSION_BASED,
                            metadata={
                                "version_diff": target_ver - source_ver,
                                "family": family,
                            },
                        )

                        # Store relationship
                        self.upgrade_relationships[(source_id, target_id)] = (
                            relationship
                        )

            # TODO: Implement non-numeric version comparison if needed
            # This would require string parsing and comparison logic specific to
            # version string formats (e.g., "v1.0.2" vs "v1.1.0")

    def _analyze_spec_based_upgrades(self) -> None:
        """
        Analyze specification-based upgrades.

        This method compares product specifications to identify upgrades, downgrades,
        and sidegrades based on feature improvements.
        """
        logger.info("Analyzing specification-based upgrades")

        # Group products by category for better comparison
        category_products = defaultdict(list)

        for product_id, categories in self.product_categories.items():
            for category in categories:
                category_products[category].append(product_id)

        # Define key specs and their importance weights
        # This would ideally come from configuration or be learned
        spec_weights = {
            "processor": 1.0,
            "cpu": 1.0,
            "ram": 0.9,
            "memory": 0.9,
            "storage": 0.8,
            "screen_size": 0.7,
            "resolution": 0.8,
            "camera": 0.8,
            "battery": 0.8,
            "weight": -0.5,  # Lower is better
            "thickness": -0.6,  # Lower is better
            "size": -0.3,  # Lower is better (for some products)
        }

        # For each category, compare products
        for category, products in category_products.items():
            # Skip categories with too few products
            if len(products) < 2:
                continue

            # Filter products with specs
            products_with_specs = [p for p in products if p in self.product_specs]

            # Skip if not enough products with specs
            if len(products_with_specs) < 2:
                continue

            # Compare each pair of products
            for i, source_id in enumerate(products_with_specs):
                for target_id in products_with_specs[i + 1 :]:
                    # Skip same product
                    if source_id == target_id:
                        continue

                    source_specs = self.product_specs[source_id]
                    target_specs = self.product_specs[target_id]

                    # Skip if not enough comparable specs
                    common_specs = set(source_specs.keys()) & set(target_specs.keys())
                    if len(common_specs) < 2:
                        continue

                    # Compare specs and calculate score
                    better_specs = 0
                    worse_specs = 0
                    equal_specs = 0
                    spec_diff_scores = {}

                    for spec in common_specs:
                        spec_key = next(
                            (k for k in spec_weights.keys() if k in spec.lower()), None
                        )
                        weight = spec_weights.get(spec_key, 0.5) if spec_key else 0.5

                        # Attempt to compare as numeric values if possible
                        try:
                            source_val = float(source_specs[spec])
                            target_val = float(target_specs[spec])

                            # Adjust comparison for specs where lower is better
                            if weight < 0:
                                if target_val < source_val:
                                    better_specs += 1
                                    spec_diff_scores[spec] = (
                                        abs(weight)
                                        * (source_val - target_val)
                                        / source_val
                                    )
                                elif target_val > source_val:
                                    worse_specs += 1
                                    spec_diff_scores[spec] = (
                                        weight * (target_val - source_val) / source_val
                                    )
                                else:
                                    equal_specs += 1
                                    spec_diff_scores[spec] = 0
                            else:
                                if target_val > source_val:
                                    better_specs += 1
                                    spec_diff_scores[spec] = (
                                        weight * (target_val - source_val) / source_val
                                    )
                                elif target_val < source_val:
                                    worse_specs += 1
                                    spec_diff_scores[spec] = (
                                        -weight * (source_val - target_val) / source_val
                                    )
                                else:
                                    equal_specs += 1
                                    spec_diff_scores[spec] = 0
                        except (ValueError, TypeError):
                            # Non-numeric comparison
                            # In a real system, this would use NLP or specific comparison logic
                            # For now, we'll consider them equal
                            equal_specs += 1
                            spec_diff_scores[spec] = 0

                    # Skip if not enough comparable specs
                    if (better_specs + worse_specs + equal_specs) < 2:
                        continue

                    # Calculate overall score
                    if better_specs > worse_specs:
                        # target is an upgrade of source
                        score_ratio = better_specs / (
                            better_specs + worse_specs + equal_specs
                        )
                        confidence = min(0.9, 0.5 + (score_ratio * 0.5))

                        # Store spec scores
                        self.spec_scores[(source_id, target_id)] = spec_diff_scores

                        # Check price ratio
                        price_ratio = 1.0
                        if (
                            source_id in self.product_prices
                            and target_id in self.product_prices
                        ):
                            source_price = self.product_prices[source_id]
                            target_price = self.product_prices[target_id]

                            if source_price > 0:
                                price_ratio = target_price / source_price

                        # Skip if price ratio is too high for an upgrade
                        if price_ratio > self.config.max_price_ratio_upgrade:
                            continue

                        # Determine upgrade type
                        upgrade_type = UpgradeType.FEATURE_UPGRADE

                        # Create relationship if not already exists
                        if (source_id, target_id) not in self.upgrade_relationships:
                            relationship = UpgradeRelationship(
                                source_id=source_id,
                                target_id=target_id,
                                upgrade_type=upgrade_type,
                                confidence=confidence,
                                price_ratio=price_ratio,
                                specs_comparison=spec_diff_scores,
                                method=UpgradeMethod.SPEC_COMPARISON,
                            )
                            self.upgrade_relationships[(source_id, target_id)] = (
                                relationship
                            )
                    elif worse_specs > better_specs:
                        # target is a downgrade of source
                        score_ratio = worse_specs / (
                            better_specs + worse_specs + equal_specs
                        )
                        confidence = min(0.9, 0.5 + (score_ratio * 0.5))

                        # Store spec scores (inverted)
                        self.spec_scores[(source_id, target_id)] = {
                            k: -v for k, v in spec_diff_scores.items()
                        }

                        # Check price ratio
                        price_ratio = 1.0
                        if (
                            source_id in self.product_prices
                            and target_id in self.product_prices
                        ):
                            source_price = self.product_prices[source_id]
                            target_price = self.product_prices[target_id]

                            if source_price > 0:
                                price_ratio = target_price / source_price

                        # Skip if price isn't lower for a downgrade
                        if price_ratio >= self.config.max_price_ratio_downgrade:
                            continue

                        # Create relationship if not already exists
                        if (source_id, target_id) not in self.upgrade_relationships:
                            relationship = UpgradeRelationship(
                                source_id=source_id,
                                target_id=target_id,
                                upgrade_type=UpgradeType.DOWNGRADE,
                                confidence=confidence,
                                price_ratio=price_ratio,
                                specs_comparison=spec_diff_scores,
                                method=UpgradeMethod.SPEC_COMPARISON,
                            )
                            self.upgrade_relationships[(source_id, target_id)] = (
                                relationship
                            )
                    else:
                        # Similar products, potential sidegrade
                        # Only consider as sidegrade if the specs are different but similar quality
                        if better_specs > 0 and worse_specs > 0:
                            balance_ratio = min(better_specs, worse_specs) / max(
                                better_specs, worse_specs
                            )
                            if balance_ratio > 0.5:  # Reasonably balanced trade-offs
                                confidence = min(0.8, 0.4 + (balance_ratio * 0.5))

                                # Store spec scores
                                self.spec_scores[(source_id, target_id)] = (
                                    spec_diff_scores
                                )

                                # Create relationship if not already exists
                                if (
                                    source_id,
                                    target_id,
                                ) not in self.upgrade_relationships:
                                    relationship = UpgradeRelationship(
                                        source_id=source_id,
                                        target_id=target_id,
                                        upgrade_type=UpgradeType.SIDEGRADE,
                                        confidence=confidence,
                                        price_ratio=(
                                            price_ratio
                                            if "price_ratio" in locals()
                                            else 1.0
                                        ),
                                        specs_comparison=spec_diff_scores,
                                        method=UpgradeMethod.SPEC_COMPARISON,
                                        bidirectional=True,
                                    )
                                    self.upgrade_relationships[
                                        (source_id, target_id)
                                    ] = relationship

    def _analyze_price_tier_relationships(self) -> None:
        """
        Analyze relationships based on price tiers.

        This method identifies upgrade and downgrade relationships based on
        price differences within the same product categories.
        """
        logger.info("Analyzing price tier relationships")

        # Skip if not enough price data
        if len(self.product_prices) < 3:
            logger.info("Not enough price data for price tier analysis")
            return

        # Group products by category
        category_products = defaultdict(list)

        for product_id, categories in self.product_categories.items():
            if product_id in self.product_prices:
                for category in categories:
                    category_products[category].append(product_id)

        # Analyze price tiers within each category
        for category, products in category_products.items():
            # Skip categories with too few products
            if len(products) < 3:
                continue

            # Get products with prices
            products_with_prices = [
                (p, self.product_prices[p])
                for p in products
                if p in self.product_prices
            ]

            # Skip if not enough products with prices
            if len(products_with_prices) < 3:
                continue

            # Sort by price
            products_with_prices.sort(key=version_key)

            # Create price tiers (simplified approach - in real systems this would be more sophisticated)
            # For now, we'll divide into price quartiles
            tier_size = max(1, len(products_with_prices) // 4)
            price_tiers: List[Dict[str, Any]] = []

            for i in range(0, len(products_with_prices), tier_size):
                tier_products = products_with_prices[i : i + tier_size]
                tier_min = tier_products[0][1]
                tier_max = tier_products[-1][1]

                price_tiers.append(
                    {
                        "tier": len(price_tiers),
                        "min_price": tier_min,
                        "max_price": tier_max,
                        "products": [p[0] for p in tier_products],
                        "avg_price": sum(p[1] for p in tier_products)
                        / len(tier_products),
                    }
                )

            # Store price tier data
            for tier in price_tiers:
                if "products" in tier and isinstance(tier["products"], list):
                    for product_id in tier["products"]:
                        self.price_tier_data[product_id] = [
                            (p, self.product_prices[p])
                            for p in products
                            if p in self.product_prices
                        ]

            # Create relationships between tiers
            for i in range(len(price_tiers) - 1):
                lower_tier = price_tiers[i]
                upper_tier = price_tiers[i + 1]

                # For each product in lower tier, suggest upper tier products as upgrades
                for source_id in lower_tier["products"]:
                    for target_id in upper_tier["products"]:
                        # Skip if relationship already exists
                        if (source_id, target_id) in self.upgrade_relationships:
                            continue

                        # Calculate price ratio
                        source_price = self.product_prices[source_id]
                        target_price = self.product_prices[target_id]
                        price_ratio = (
                            target_price / source_price if source_price > 0 else 0
                        )

                        # Skip if price ratio is too high
                        if price_ratio > self.config.max_price_ratio_upgrade:
                            continue

                        # Check if products have specs for better classification
                        has_specs = (
                            source_id in self.product_specs
                            and target_id in self.product_specs
                        )

                        # Calculate confidence based on price difference and tier separation
                        tier_diff = upper_tier["tier"] - lower_tier["tier"]
                        price_diff_ratio = (
                            (target_price - source_price) / source_price
                            if source_price > 0
                            else 0
                        )

                        # Higher confidence for reasonable price differences
                        confidence = min(0.7, 0.3 + (price_diff_ratio * 0.5))

                        # If we don't have spec data, be more conservative
                        if not has_specs:
                            confidence *= 0.8

                        # Create upgrade relationship
                        relationship = UpgradeRelationship(
                            source_id=source_id,
                            target_id=target_id,
                            upgrade_type=UpgradeType.FEATURE_UPGRADE,
                            confidence=confidence,
                            price_ratio=price_ratio,
                            method=UpgradeMethod.PRICE_TIER,
                            metadata={
                                "category": category,
                                "source_tier": lower_tier["tier"],
                                "target_tier": upper_tier["tier"],
                                "tier_diff": tier_diff,
                            },
                        )

                        self.upgrade_relationships[(source_id, target_id)] = (
                            relationship
                        )

                # For each product in upper tier, suggest lower tier products as downgrades
                for source_id in upper_tier["products"]:
                    for target_id in lower_tier["products"]:
                        # Skip if relationship already exists
                        if (source_id, target_id) in self.upgrade_relationships:
                            continue

                        # Calculate price ratio
                        source_price = self.product_prices[source_id]
                        target_price = self.product_prices[target_id]
                        price_ratio = (
                            target_price / source_price if source_price > 0 else 0
                        )

                        # Calculate confidence based on price difference and tier separation
                        tier_diff = upper_tier["tier"] - lower_tier["tier"]
                        price_diff_ratio = (
                            (source_price - target_price) / source_price
                            if source_price > 0
                            else 0
                        )

                        # Higher confidence for significant price differences
                        confidence = min(0.7, 0.3 + (price_diff_ratio * 0.5))

                        # Create downgrade relationship
                        relationship = UpgradeRelationship(
                            source_id=source_id,
                            target_id=target_id,
                            upgrade_type=UpgradeType.DOWNGRADE,
                            confidence=confidence,
                            price_ratio=price_ratio,
                            method=UpgradeMethod.PRICE_TIER,
                            metadata={
                                "category": category,
                                "source_tier": upper_tier["tier"],
                                "target_tier": lower_tier["tier"],
                                "tier_diff": -tier_diff,
                            },
                        )

                        self.upgrade_relationships[(source_id, target_id)] = (
                            relationship
                        )

    def _analyze_purchase_patterns(self, purchase_data: List[Dict[str, Any]]) -> None:
        """
        Analyze purchase patterns to identify upgrade/downgrade relationships.

        This method looks at user purchase sequences to identify common upgrade
        paths and typical product progression patterns.
        """
        logger.info("Analyzing purchase patterns for upgrade/downgrade relationships")

        # Group purchases by user
        user_purchases = defaultdict(list)

        for purchase in purchase_data:
            user_id = purchase.get("user_id")
            product_id = purchase.get("product_id")
            timestamp = purchase.get("timestamp")

            if not user_id or not product_id or not timestamp:
                continue

            # Skip products without category information
            if product_id not in self.product_categories:
                continue

            user_purchases[user_id].append((product_id, timestamp))

        # Skip if not enough user purchase data
        if len(user_purchases) < 10:
            logger.info("Not enough user purchase data for purchase pattern analysis")
            return

        # Analysis data structures
        upgrade_patterns: DefaultDict[Tuple[str, str], int] = defaultdict(int)
        same_category_upgrades: DefaultDict[Tuple[str, str], int] = defaultdict(int)
        cross_category_upgrades: DefaultDict[Tuple[str, str], int] = defaultdict(int)

        # Analyze purchase sequences for each user
        for user_id, purchases in user_purchases.items():
            # Skip users with only one purchase
            if len(purchases) < 2:
                continue

            # Sort purchases by timestamp
            purchases.sort(key=version_key)

            # Analyze sequential purchases
            for i in range(len(purchases) - 1):
                current_product, current_time = purchases[i]
                next_product, next_time = purchases[i + 1]

                # Skip if same product
                if current_product == next_product:
                    continue

                # Get time difference in days
                time_diff = (next_time - current_time).days

                # Skip if too far apart (e.g., more than 2 years)
                if time_diff > 730:
                    continue

                # Check if products are in the same category
                current_categories = self.product_categories[current_product]
                next_categories = self.product_categories[next_product]

                # Check for category overlap
                common_categories = set(current_categories) & set(next_categories)

                # If common categories, might be an upgrade
                if common_categories:
                    pair_key = (current_product, next_product)
                    same_category_upgrades[pair_key] += 1
                    upgrade_patterns[pair_key] += 1
                else:
                    # Cross-category relationship
                    pair_key = (current_product, next_product)
                    cross_category_upgrades[pair_key] += 1
                    upgrade_patterns[pair_key] += 1

        # Convert purchase patterns to relationships
        for (source_id, target_id), count in upgrade_patterns.items():
            # Skip if count too low
            if count < 3:
                continue

            # Skip if relationship already exists
            if (source_id, target_id) in self.upgrade_relationships:
                continue

            # Check if this is same-category or cross-category
            is_same_category = (source_id, target_id) in same_category_upgrades

            # Calculate confidence based on frequency
            max_count = (
                max(same_category_upgrades.values())
                if is_same_category
                else max(cross_category_upgrades.values())
            )
            normalized_count = count / max_count if max_count > 0 else 0
            confidence = min(0.85, 0.4 + (normalized_count * 0.5))

            # Determine relationship type
            # For purchase patterns, we assume later purchases are upgrades if in same category
            # and sidegrades if in different categories
            upgrade_type = (
                UpgradeType.FEATURE_UPGRADE
                if is_same_category
                else UpgradeType.SIDEGRADE
            )

            # Check price ratio if available
            price_ratio = 1.0
            if source_id in self.product_prices and target_id in self.product_prices:
                source_price = self.product_prices[source_id]
                target_price = self.product_prices[target_id]

                if source_price > 0:
                    price_ratio = target_price / source_price

                    # If price is significantly lower, it's more likely a downgrade
                    if price_ratio < 0.7 and is_same_category:
                        upgrade_type = UpgradeType.DOWNGRADE
                    # If price is significantly higher and is_same_category, it supports upgrade hypothesis
                    elif price_ratio > 1.3 and is_same_category:
                        confidence *= 1.1  # Slight boost to confidence

            # Create relationship
            relationship = UpgradeRelationship(
                source_id=source_id,
                target_id=target_id,
                upgrade_type=upgrade_type,
                confidence=confidence,
                price_ratio=price_ratio,
                method=UpgradeMethod.PURCHASE_PATTERN,
                metadata={
                    "purchase_count": count,
                    "is_same_category": is_same_category,
                },
            )

            self.upgrade_relationships[(source_id, target_id)] = relationship

            # Store purchase pattern data
            self.purchase_pattern_data[(source_id, target_id)] = count

    def _apply_expert_rules(self, expert_rules: List[Dict[str, Any]]) -> None:
        """
        Apply expert-defined rules for upgrade/downgrade relationships.

        Args:
            expert_rules: List of expert-defined upgrade/downgrade rules
        """
        logger.info("Applying expert-defined upgrade/downgrade rules")

        for rule in expert_rules:
            source_id = rule.get("source_id")
            target_id = rule.get("target_id")

            if not source_id or not target_id:
                continue

            upgrade_type_str = rule.get("upgrade_type", "direct_upgrade")
            confidence = rule.get("confidence", 0.9)

            # Convert string to enum
            try:
                upgrade_type = UpgradeType(upgrade_type_str)
            except ValueError:
                upgrade_type = UpgradeType.DIRECT_UPGRADE

            # Get price ratio if available
            price_ratio = rule.get("price_ratio", 1.0)

            # Get or compute price ratio from product data if not provided and available
            if (
                price_ratio == 1.0
                and source_id in self.product_prices
                and target_id in self.product_prices
            ):
                source_price = self.product_prices[source_id]
                target_price = self.product_prices[target_id]

                if source_price > 0:
                    price_ratio = target_price / source_price

            # Create or update relationship
            if (source_id, target_id) in self.upgrade_relationships:
                # For expert rules, we override existing information but mark as hybrid
                existing = self.upgrade_relationships[(source_id, target_id)]
                self.upgrade_relationships[(source_id, target_id)] = (
                    UpgradeRelationship(
                        source_id=source_id,
                        target_id=target_id,
                        upgrade_type=upgrade_type,  # Use expert type
                        confidence=confidence,  # Use expert confidence
                        price_ratio=price_ratio,
                        specs_comparison=existing.specs_comparison,
                        method=UpgradeMethod.HYBRID,
                        bidirectional=rule.get("bidirectional", False),
                        metadata={
                            "expert_defined": True,
                            "previous_method": existing.method,
                        },
                    )
                )
            else:
                # Create new relationship
                self.upgrade_relationships[(source_id, target_id)] = (
                    UpgradeRelationship(
                        source_id=source_id,
                        target_id=target_id,
                        upgrade_type=upgrade_type,
                        confidence=confidence,
                        price_ratio=price_ratio,
                        method=UpgradeMethod.EXPERT_DEFINED,
                        bidirectional=rule.get("bidirectional", False),
                        metadata={"expert_defined": True},
                    )
                )

    def _combine_upgrade_signals(self) -> None:
        """
        Combine upgrade signals from different methods.

        This method weights and combines signals from version-based, spec-based,
        price-tier, purchase pattern, and expert-defined rules into final relationships.
        """
        logger.info("Combining upgrade signals from different methods")

        # For each relationship, check if we have multiple signals
        hybrid_relationships = []

        for (source_id, target_id), relationship in self.upgrade_relationships.items():
            signals = []

            # Version-based signal
            if (source_id, target_id) in self.version_scores:
                signals.append(
                    {
                        "method": UpgradeMethod.VERSION_BASED,
                        "confidence": self.version_scores[(source_id, target_id)],
                        "weight": self.config.version_weight,
                    }
                )

            # Spec-based signal
            if (source_id, target_id) in self.spec_scores:
                signals.append(
                    {
                        "method": UpgradeMethod.SPEC_COMPARISON,
                        "confidence": (
                            relationship.confidence
                            if relationship.method == UpgradeMethod.SPEC_COMPARISON
                            else 0.5
                        ),
                        "weight": self.config.spec_weight,
                    }
                )

            # Price-tier signal
            if relationship.method == UpgradeMethod.PRICE_TIER:
                signals.append(
                    {
                        "method": UpgradeMethod.PRICE_TIER,
                        "confidence": relationship.confidence,
                        "weight": self.config.price_weight,
                    }
                )

            # Purchase pattern signal
            if (source_id, target_id) in self.purchase_pattern_data:
                signals.append(
                    {
                        "method": UpgradeMethod.PURCHASE_PATTERN,
                        "confidence": (
                            relationship.confidence
                            if relationship.method == UpgradeMethod.PURCHASE_PATTERN
                            else 0.5
                        ),
                        "weight": self.config.purchase_weight,
                    }
                )

            # Expert-defined signal
            if relationship.method == UpgradeMethod.EXPERT_DEFINED:
                signals.append(
                    {
                        "method": UpgradeMethod.EXPERT_DEFINED,
                        "confidence": relationship.confidence,
                        "weight": self.config.expert_weight,
                    }
                )

            # If multiple signals, create hybrid relationship
            if len(signals) > 1:
                # Weight and combine confidences
                weighted_confidence = 0.0
                total_weight = 0.0

                for s in signals:
                    conf = safe_float(s.get("confidence", 0))
                    weight = safe_float(s.get("weight", 0))
                    weighted_confidence += conf * weight
                    total_weight += weight

                combined_confidence = (
                    weighted_confidence / total_weight if total_weight > 0 else 0
                )

                # Create hybrid relationship
                hybrid_rel = UpgradeRelationship(
                    source_id=source_id,
                    target_id=target_id,
                    upgrade_type=relationship.upgrade_type,
                    confidence=combined_confidence,
                    price_ratio=relationship.price_ratio,
                    specs_comparison=relationship.specs_comparison,
                    method=UpgradeMethod.HYBRID,
                    bidirectional=relationship.bidirectional,
                    metadata={
                        "component_methods": [
                            str(s.get("method", "")) for s in signals
                        ],
                        "component_weights": [
                            safe_float(s.get("weight", 0)) for s in signals
                        ],
                        "component_confidences": [
                            safe_float(s.get("confidence", 0)) for s in signals
                        ],
                    },
                )

                hybrid_relationships.append((source_id, target_id, hybrid_rel))

        # Update relationships with hybrid versions
        for source_id, target_id, hybrid_rel in hybrid_relationships:
            self.upgrade_relationships[(source_id, target_id)] = hybrid_rel

        # Filter out low-confidence relationships
        to_remove = []
        for key, relationship in self.upgrade_relationships.items():
            if relationship.confidence < self.config.min_confidence:
                to_remove.append(key)

        for key in to_remove:
            del self.upgrade_relationships[key]

    def _build_product_upgrades_index(self) -> None:
        """
        Build optimized indices of upgrade/downgrade/sidegrade products.

        This method builds lookup structures for quick access to a product's
        upgrades, downgrades, and sidegrades.
        """
        self.product_upgrades = defaultdict(list)
        self.product_downgrades = defaultdict(list)
        self.product_sidegrades = defaultdict(list)

        for (source_id, target_id), relationship in self.upgrade_relationships.items():
            # Add to appropriate index based on relationship type
            if relationship.upgrade_type in [
                UpgradeType.DIRECT_UPGRADE,
                UpgradeType.FEATURE_UPGRADE,
                UpgradeType.GENERATION_UPGRADE,
            ]:
                self.product_upgrades[source_id].append(
                    (target_id, relationship.confidence)
                )
                # Also add as downgrade in reverse direction
                self.product_downgrades[target_id].append(
                    (source_id, relationship.confidence * 0.9)
                )
            elif relationship.upgrade_type == UpgradeType.DOWNGRADE:
                self.product_downgrades[source_id].append(
                    (target_id, relationship.confidence)
                )
                # Also add as upgrade in reverse direction
                self.product_upgrades[target_id].append(
                    (source_id, relationship.confidence * 0.9)
                )
            elif relationship.upgrade_type == UpgradeType.SIDEGRADE:
                self.product_sidegrades[source_id].append(
                    (target_id, relationship.confidence)
                )
                # For sidegrades, also add in reverse direction if bidirectional
                if relationship.bidirectional:
                    self.product_sidegrades[target_id].append(
                        (source_id, relationship.confidence)
                    )
