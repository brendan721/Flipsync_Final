#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bundle Recommendation Engine

This module provides functionality for identifying and recommending product
bundles based on product relationships, purchase patterns, and business rules.

The implementation supports various bundle discovery methods, bundle ranking,
and personalized bundle recommendations.
"""

import itertools
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.recommendations.algorithms.collaborative import Recommendation

from .relationships import ProductRelationship, ProductRelationshipMap, RelationshipType

logger = logging.getLogger(__name__)


class BundleSource(str, Enum):
    """Sources for bundle recommendations."""

    EXPLICIT = "explicit"  # Explicitly defined bundles
    CO_PURCHASE = "co_purchase"  # Frequently co-purchased items
    COMPLEMENTARY = "complementary"  # Complementary product relationships
    ALGORITHM = "algorithm"  # Algorithmically discovered bundles
    MANUAL = "manual"  # Manually curated bundles


class BundleType(str, Enum):
    """Types of product bundles."""

    STARTER = "starter"  # Essential items for beginners
    COMPLETE = "complete"  # Complete solution for a specific need
    ACCESSORY = "accessory"  # Main product with accessories
    THEMED = "themed"  # Items with a common theme
    DISCOUNT = "discount"  # Items bundled for discount
    CROSS_SELL = "cross_sell"  # Related items across categories
    CUSTOM = "custom"  # Custom bundle type


@dataclass
class BundleItem:
    """An item in a product bundle."""

    product_id: str
    is_primary: bool = False  # Whether this is the primary item
    discount_percent: float = 0.0  # Item-specific discount
    required: bool = True  # Whether item is required in the bundle
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductBundle:
    """A bundle of related products."""

    bundle_id: str
    name: str
    description: str
    items: List[BundleItem]
    bundle_type: BundleType
    total_discount_percent: float = 0.0  # Overall bundle discount
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source: BundleSource = BundleSource.MANUAL
    active: bool = True

    def __post_init__(self) -> None:
        """Validate bundle after initialization."""
        if not isinstance(self.bundle_type, BundleType):
            self.bundle_type = BundleType(self.bundle_type)

        if not isinstance(self.source, BundleSource):
            self.source = BundleSource(self.source)

        # Ensure at least one primary item
        primary_exists = any(item.is_primary for item in self.items)
        if not primary_exists and self.items:
            self.items[0].is_primary = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert bundle to dictionary.

        Returns:
            Dictionary representation of bundle
        """
        return {
            "bundle_id": self.bundle_id,
            "name": self.name,
            "description": self.description,
            "items": [
                {
                    "product_id": item.product_id,
                    "is_primary": item.is_primary,
                    "discount_percent": item.discount_percent,
                    "required": item.required,
                    "metadata": item.metadata,
                }
                for item in self.items
            ],
            "bundle_type": self.bundle_type.value,
            "total_discount_percent": self.total_discount_percent,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source": self.source.value,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductBundle":
        """Create bundle from dictionary.

        Args:
            data: Dictionary representation of bundle

        Returns:
            ProductBundle instance
        """
        # Handle datetime conversion
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        # Convert items
        items = [
            BundleItem(
                product_id=item["product_id"],
                is_primary=item.get("is_primary", False),
                discount_percent=item.get("discount_percent", 0.0),
                required=item.get("required", True),
                metadata=item.get("metadata", {}),
            )
            for item in data.get("items", [])
        ]

        return cls(
            bundle_id=data["bundle_id"],
            name=data["name"],
            description=data["description"],
            items=items,
            bundle_type=data["bundle_type"],
            total_discount_percent=data.get("total_discount_percent", 0.0),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
            source=data.get("source", BundleSource.MANUAL),
            active=data.get("active", True),
        )

    def get_primary_items(self) -> List[BundleItem]:
        """Get primary items in the bundle.

        Returns:
            List of primary items
        """
        return [item for item in self.items if item.is_primary]

    def get_required_items(self) -> List[BundleItem]:
        """Get required items in the bundle.

        Returns:
            List of required items
        """
        return [item for item in self.items if item.required]

    def get_optional_items(self) -> List[BundleItem]:
        """Get optional items in the bundle.

        Returns:
            List of optional items
        """
        return [item for item in self.items if not item.required]

    def get_product_ids(self) -> List[str]:
        """Get all product IDs in the bundle.

        Returns:
            List of product IDs
        """
        return [item.product_id for item in self.items]

    def add_item(self, item: BundleItem) -> None:
        """Add an item to the bundle.

        Args:
            item: Bundle item to add
        """
        if item.product_id not in self.get_product_ids():
            self.items.append(item)
            self.updated_at = datetime.now()

    def remove_item(self, product_id: str) -> bool:
        """Remove an item from the bundle.

        Args:
            product_id: Product ID to remove

        Returns:
            True if item was removed, False if not found
        """
        original_length = len(self.items)
        self.items = [item for item in self.items if item.product_id != product_id]

        if len(self.items) < original_length:
            self.updated_at = datetime.now()
            return bool(True)
        return False

    def is_valid(self) -> bool:
        """Check if the bundle is valid.

        Returns:
            True if bundle is valid
        """
        # Must have at least one item
        if not self.items:
            return False

        # Must have at least one primary item
        if not any(item.is_primary for item in self.items):
            return False

        # Must have at least one required item
        if not any(item.required for item in self.items):
            return False

        return True


class BundleRecommender:
    """Recommends product bundles based on product relationships."""

    def __init__(
        self,
        relationship_map: Optional[ProductRelationshipMap] = None,
        explicit_bundles: Optional[List[ProductBundle]] = None,
    ):
        """
        Initialize the bundle recommender.

        Args:
            relationship_map: Product relationship map
            explicit_bundles: Explicit bundle definitions
        """
        self.relationship_map = relationship_map or ProductRelationshipMap()
        self.explicit_bundles: Dict[str, ProductBundle] = {}

        # Add explicit bundles if provided
        if explicit_bundles:
            for bundle in explicit_bundles:
                self.add_bundle(bundle)

        # Cache for discovered bundles
        self.discovered_bundles: Dict[str, ProductBundle] = {}

        # Product metadata for enriching recommendations
        self.product_metadata: Dict[str, Dict[str, Any]] = {}

        logger.info("Initialized bundle recommender")

    def add_bundle(self, bundle: ProductBundle) -> None:
        """Add an explicit bundle.

        Args:
            bundle: Bundle to add
        """
        if not bundle.is_valid():
            logger.warning("Invalid bundle: %s", bundle.bundle_id)
            return

        self.explicit_bundles[bundle.bundle_id] = bundle
        logger.debug("Added bundle: %s (%s)", bundle.bundle_id, bundle.name)

    def remove_bundle(self, bundle_id: str) -> bool:
        """Remove an explicit bundle.

        Args:
            bundle_id: ID of bundle to remove

        Returns:
            True if bundle was removed, False if not found
        """
        if bundle_id in self.explicit_bundles:
            del self.explicit_bundles[bundle_id]
            logger.debug("Removed bundle: %s", bundle_id)
            return True
        return False

    def set_product_metadata(self, product_metadata: Dict[str, Dict[str, Any]]) -> None:
        """Set product metadata for recommendation enrichment.

        Args:
            product_metadata: Dictionary mapping product IDs to metadata
        """
        self.product_metadata = product_metadata
        logger.info("Set metadata for %s products", len(product_metadata))

    def discover_bundles(
        self, discovery_methods: Optional[List[BundleSource]] = None
    ) -> List[ProductBundle]:
        """Discover bundles using various methods.

        Args:
            discovery_methods: Methods to use for discovery

        Returns:
            List of discovered bundles
        """
        if discovery_methods is None:
            discovery_methods = [BundleSource.COMPLEMENTARY, BundleSource.ALGORITHM]

        discovered = []

        for method in discovery_methods:
            if method == BundleSource.COMPLEMENTARY:
                bundles = self._discover_complementary_bundles()
                discovered.extend(bundles)
            elif method == BundleSource.ALGORITHM:
                bundles = self._discover_algorithmic_bundles()
                discovered.extend(bundles)

        # Cache discovered bundles
        for bundle in discovered:
            self.discovered_bundles[bundle.bundle_id] = bundle

        logger.info("Discovered %s bundles", len(discovered))
        return discovered

    def _discover_complementary_bundles(self) -> List[ProductBundle]:
        """Discover bundles based on complementary relationships.

        Returns:
            List of discovered bundles
        """
        bundles = []

        # Get all complementary relationships
        complementary_rels = self.relationship_map.get_relationships_by_type(
            RelationshipType.COMPLEMENTARY,
            min_strength=0.5,  # Only consider stronger relationships
        )

        # Group by source product
        by_source = defaultdict(list)
        for rel in complementary_rels:
            by_source[rel.source_id].append(rel)

        # Create bundles for products with multiple complementary items
        bundle_counter = 0
        for source_id, relationships in by_source.items():
            if len(relationships) < 2:
                continue  # Need at least 2 complementary items

            # Sort by strength
            relationships.sort(key=lambda r: r.strength, reverse=True)

            # Take top 3-5 items
            max_items = min(5, len(relationships))
            bundle_items = [
                BundleItem(product_id=source_id, is_primary=True, required=True)
            ]

            for rel in relationships[:max_items]:
                bundle_items.append(
                    BundleItem(
                        product_id=rel.target_id,
                        is_primary=False,
                        required=False,
                        metadata={"relationship_strength": rel.strength},
                    )
                )

            # Create the bundle
            bundle_counter += 1
            name = f"Complementary Bundle {bundle_counter}"
            description = "Products that work well together"

            # Try to enhance name and description with product metadata
            if source_id in self.product_metadata:
                product_name = self.product_metadata[source_id].get("name", "")
                if product_name:
                    name = f"{product_name} Bundle"
                    description = (
                        f"Complete your {product_name} with these compatible items"
                    )

            bundle = ProductBundle(
                bundle_id=f"comp_{source_id}_{bundle_counter}",
                name=name,
                description=description,
                items=bundle_items,
                bundle_type=BundleType.ACCESSORY,
                source=BundleSource.COMPLEMENTARY,
                metadata={
                    "auto_generated": True,
                    "base_product": source_id,
                    "average_strength": sum(
                        r.strength for r in relationships[:max_items]
                    )
                    / max_items,
                },
            )

            bundles.append(bundle)

        return bundles

    def _discover_algorithmic_bundles(self) -> List[ProductBundle]:
        """Discover bundles using algorithmic methods.

        Returns:
            List of discovered bundles
        """
        bundles = []

        # Get all product relationships
        all_rels = self.relationship_map.get_all_relationships()

        # Create a graph representation: product_id -> list of connected products
        graph = defaultdict(set)
        for rel in all_rels:
            if rel.active and rel.strength >= 0.3:
                graph[rel.source_id].add(rel.target_id)
                if rel.bidirectional:
                    graph[rel.target_id].add(rel.source_id)

        # Find densely connected subgraphs (potential bundles)
        visited = set()
        bundle_counter = 0

        for product_id in graph:
            if product_id in visited:
                continue

            # Find connected component
            component = self._find_connected_component(graph, product_id)

            # Skip small components
            if len(component) < 3:
                continue

            # Mark as visited
            visited.update(component)

            # Find central product (most connections)
            central_product = max(component, key=lambda p: len(graph[p] & component))

            # Create bundle items
            bundle_items = [
                BundleItem(product_id=central_product, is_primary=True, required=True)
            ]

            # Add other products
            for other_product in sorted(component - {central_product}):
                bundle_items.append(
                    BundleItem(
                        product_id=other_product, is_primary=False, required=False
                    )
                )

            # Create the bundle
            bundle_counter += 1
            name = f"Algorithmic Bundle {bundle_counter}"
            description = "Products that are frequently used together"

            # Try to enhance name and description with product metadata
            if central_product in self.product_metadata:
                product_name = self.product_metadata[central_product].get("name", "")
                category = self.product_metadata[central_product].get("category", "")

                if product_name and category:
                    name = f"{category} {product_name} Bundle"
                    description = (
                        f"Complete {category} solution built around {product_name}"
                    )
                elif product_name:
                    name = f"{product_name} Bundle"
                    description = f"Complete solution built around {product_name}"

            bundle = ProductBundle(
                bundle_id=f"algo_{central_product}_{bundle_counter}",
                name=name,
                description=description,
                items=bundle_items,
                bundle_type=BundleType.COMPLETE,
                source=BundleSource.ALGORITHM,
                metadata={
                    "auto_generated": True,
                    "central_product": central_product,
                    "graph_density": len(component)
                    / (len(component) * (len(component) - 1) / 2),
                },
            )

            bundles.append(bundle)

        return bundles

    def _find_connected_component(
        self, graph: Dict[str, Set[str]], start: str
    ) -> Set[str]:
        """Find connected component in the product graph.

        Args:
            graph: Product relationship graph
            start: Starting product ID

        Returns:
            Set of connected product IDs
        """
        component = set()
        queue = [start]

        while queue:
            product = queue.pop(0)
            if product not in component:
                component.add(product)
                queue.extend(graph[product] - component)

        return component

    def recommend_bundles(
        self,
        product_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 5,
        bundle_types: Optional[List[BundleType]] = None,
        include_discovered: bool = True,
    ) -> List[Recommendation]:
        """Recommend bundles for a product or user.

        Args:
            product_id: Product ID to recommend bundles for
            user_id: UnifiedUser ID to recommend bundles for
            limit: Maximum number of bundles to recommend
            bundle_types: Types of bundles to include
            include_discovered: Whether to include discovered bundles

        Returns:
            List of bundle recommendations
        """
        candidates = []

        # Add explicit bundles
        candidates.extend(
            bundle for bundle in self.explicit_bundles.values() if bundle.active
        )

        # Add discovered bundles if requested
        if include_discovered:
            candidates.extend(
                bundle for bundle in self.discovered_bundles.values() if bundle.active
            )

        # Filter by bundle type if specified
        if bundle_types:
            candidates = [
                bundle for bundle in candidates if bundle.bundle_type in bundle_types
            ]

        # Product-specific recommendations
        if product_id:
            return self._recommend_for_product(product_id, candidates, limit)

        # UnifiedUser-specific recommendations
        if user_id:
            return self._recommend_for_user(user_id, candidates, limit)

        # Generic recommendations (sort by number of items)
        candidates.sort(key=lambda b: len(b.items), reverse=True)

        # Convert to recommendations
        recommendations = [
            Recommendation(
                id=bundle.bundle_id,
                score=0.5,  # Generic score
                confidence=0.5,  # Generic confidence
                metadata={"bundle": bundle.to_dict()},
            )
            for bundle in candidates[:limit]
        ]

        return recommendations

    def _recommend_for_product(
        self, product_id: str, candidates: List[ProductBundle], limit: int
    ) -> List[Recommendation]:
        """Recommend bundles for a specific product.

        Args:
            product_id: Product ID to recommend for
            candidates: Candidate bundles
            limit: Maximum number of bundles to recommend

        Returns:
            List of bundle recommendations
        """
        scored_bundles = []

        for bundle in candidates:
            score = 0.0

            # Check if product is in the bundle
            product_in_bundle = product_id in bundle.get_product_ids()

            # Case 1: Product is in the bundle
            if product_in_bundle:
                # If it's the primary product, high score
                for item in bundle.items:
                    if item.product_id == product_id and item.is_primary:
                        score = 0.9
                        break

                # If not primary, medium score
                if score == 0.0:
                    score = 0.6

            # Case 2: Product is not in the bundle, check relationships
            else:
                # Check if bundle primary items are related to this product
                related_score = 0.0
                count = 0

                for primary_item in bundle.get_primary_items():
                    # Check relationship with primary item
                    rel = self.relationship_map.get_relationship(
                        product_id, primary_item.product_id
                    )
                    if rel and rel.active:
                        related_score += rel.strength
                        count += 1

                    # Also check reverse relationship
                    rel = self.relationship_map.get_relationship(
                        primary_item.product_id, product_id
                    )
                    if rel and rel.active:
                        related_score += rel.strength
                        count += 1

                if count > 0:
                    score = related_score / count * 0.8  # Scale to max 0.8

            # Add to scored bundles if score is significant
            if score > 0.1:
                scored_bundles.append((bundle, score))

        # Sort by score and take top N
        scored_bundles.sort(key=lambda x: x[1], reverse=True)
        top_bundles = scored_bundles[:limit]

        # Convert to recommendations
        recommendations = [
            Recommendation(
                id=bundle.bundle_id,
                score=score,
                confidence=score * 0.8,  # Slightly lower confidence
                metadata={"bundle": bundle.to_dict(), "product_id": product_id},
            )
            for bundle, score in top_bundles
        ]

        return recommendations

    def _recommend_for_user(
        self, user_id: str, candidates: List[ProductBundle], limit: int
    ) -> List[Recommendation]:
        """Recommend bundles for a specific user.

        Args:
            user_id: UnifiedUser ID to recommend for
            candidates: Candidate bundles
            limit: Maximum number of bundles to recommend

        Returns:
            List of bundle recommendations
        """
        # This would typically use user purchase history, preferences, etc.
        # For now, just return generic recommendations
        candidates.sort(key=lambda b: len(b.items), reverse=True)

        # Convert to recommendations
        recommendations = [
            Recommendation(
                id=bundle.bundle_id,
                score=0.5,  # Generic score
                confidence=0.5,  # Generic confidence
                metadata={"bundle": bundle.to_dict(), "user_id": user_id},
            )
            for bundle in candidates[:limit]
        ]

        return recommendations

    def get_bundle(self, bundle_id: str) -> Optional[ProductBundle]:
        """Get a specific bundle.

        Args:
            bundle_id: Bundle ID

        Returns:
            Bundle if found, None otherwise
        """
        # Check explicit bundles first
        if bundle_id in self.explicit_bundles:
            return self.explicit_bundles[bundle_id]

        # Check discovered bundles
        if bundle_id in self.discovered_bundles:
            return self.discovered_bundles[bundle_id]

        return None

    def get_all_bundles(
        self, include_discovered: bool = True, active_only: bool = True
    ) -> List[ProductBundle]:
        """Get all bundles.

        Args:
            include_discovered: Whether to include discovered bundles
            active_only: Whether to include only active bundles

        Returns:
            List of bundles
        """
        bundles = []

        # Add explicit bundles
        for bundle in self.explicit_bundles.values():
            if not active_only or bundle.active:
                bundles.append(bundle)

        # Add discovered bundles if requested
        if include_discovered:
            for bundle in self.discovered_bundles.values():
                if not active_only or bundle.active:
                    bundles.append(bundle)

        return bundles

    def get_bundles_containing_product(
        self,
        product_id: str,
        include_discovered: bool = True,
        primary_only: bool = False,
        active_only: bool = True,
    ) -> List[ProductBundle]:
        """Get bundles containing a specific product.

        Args:
            product_id: Product ID to search for
            include_discovered: Whether to include discovered bundles
            primary_only: Whether to include only bundles where product is primary
            active_only: Whether to include only active bundles

        Returns:
            List of bundles containing the product
        """
        result = []
        all_bundles = self.get_all_bundles(include_discovered, active_only)

        for bundle in all_bundles:
            # Check if product is in bundle
            for item in bundle.items:
                if item.product_id == product_id:
                    # Check if primary only
                    if primary_only and not item.is_primary:
                        continue
                    result.append(bundle)
                    break

        return result
