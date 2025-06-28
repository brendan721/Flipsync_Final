#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Product Relationship Mapping

This module provides functionality for defining, managing, and querying
relationships between products. It serves as the foundation for cross-product
recommendation features like bundles, complementary products, and upgrades.

The implementation supports various relationship types, relationship strengths,
bidirectional relationships, and batch operations for efficiency.
"""

import csv
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of relationships between products."""

    COMPLEMENTARY = "complementary"  # Products that work well together
    SUBSTITUTE = "substitute"  # Products that can replace each other
    UPGRADE = "upgrade"  # Product is an upgrade of another
    DOWNGRADE = "downgrade"  # Product is a downgrade of another
    BUNDLE = "bundle"  # Products often sold together as a bundle
    ACCESSORY = "accessory"  # Product is an accessory to another
    SIMILAR = "similar"  # Products that are similar
    CROSS_CATEGORY = "cross_category"  # Related products from different categories
    CUSTOM = "custom"  # Custom relationship type


@dataclass
class ProductRelationship:
    """Represents a relationship between products."""

    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float = 1.0  # Relationship strength (0.0 to 1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    bidirectional: bool = False  # Whether relationship applies in both directions
    active: bool = True  # Whether relationship is active

    def __post_init__(self) -> None:
        """Validate relationship after initialization."""
        if not isinstance(self.relationship_type, RelationshipType):
            self.relationship_type = RelationshipType(self.relationship_type)

        # Ensure strength is within valid range
        self.strength = max(0.0, min(1.0, self.strength))

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary.

        Returns:
            Dictionary representation of relationship
        """
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "strength": self.strength,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "bidirectional": self.bidirectional,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductRelationship":
        """Create relationship from dictionary.

        Args:
            data: Dictionary representation of relationship

        Returns:
            ProductRelationship instance
        """
        # Handle datetime conversion
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relationship_type=data["relationship_type"],
            strength=data.get("strength", 1.0),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at,
            bidirectional=data.get("bidirectional", False),
            active=data.get("active", True),
        )

    def get_reverse(self) -> "ProductRelationship":
        """Get reverse relationship (target → source).

        Returns:
            Reversed relationship
        """
        # Create a new relationship with source and target swapped
        return ProductRelationship(
            source_id=self.target_id,
            target_id=self.source_id,
            relationship_type=self._get_reverse_type(),
            strength=self.strength,
            metadata=self.metadata.copy(),
            created_at=self.created_at,
            updated_at=self.updated_at,
            bidirectional=self.bidirectional,
            active=self.active,
        )

    def _get_reverse_type(self) -> RelationshipType:
        """Get the appropriate relationship type for the reverse relationship.

        Returns:
            Appropriate relationship type for reverse
        """
        # Handle special cases where relationship type changes in reverse
        if self.relationship_type == RelationshipType.UPGRADE:
            return RelationshipType.DOWNGRADE
        elif self.relationship_type == RelationshipType.DOWNGRADE:
            return RelationshipType.UPGRADE
        elif self.relationship_type == RelationshipType.ACCESSORY:
            return RelationshipType.ACCESSORY
        else:
            # For other types, keep the same type
            return self.relationship_type


class ProductRelationshipMap:
    """Manages product relationships for recommendation purposes."""

    def __init__(self):
        """Initialize the product relationship map."""
        # Primary storage: source_id -> target_id -> relationship
        self.relationships: Dict[str, Dict[str, ProductRelationship]] = defaultdict(
            dict
        )

        # Secondary indices for efficient querying
        self.by_type: Dict[RelationshipType, List[ProductRelationship]] = defaultdict(
            list
        )
        self.by_target: Dict[str, List[ProductRelationship]] = defaultdict(list)

        logger.info("Initialized product relationship map")

    def add_relationship(self, relationship: ProductRelationship) -> None:
        """Add a relationship to the map.

        Args:
            relationship: Relationship to add
        """
        source_id = relationship.source_id
        target_id = relationship.target_id

        # Store the relationship
        self.relationships[source_id][target_id] = relationship

        # Update indices
        self.by_type[relationship.relationship_type].append(relationship)
        self.by_target[target_id].append(relationship)

        # Handle bidirectional relationships
        if relationship.bidirectional:
            reverse_rel = relationship.get_reverse()
            self.relationships[target_id][source_id] = reverse_rel
            self.by_type[reverse_rel.relationship_type].append(reverse_rel)
            self.by_target[source_id].append(reverse_rel)

        logger.debug(
            "Added relationship: %s → %s (%s)",
            source_id,
            target_id,
            relationship.relationship_type.value,
        )

    def add_relationships(self, relationships: List[ProductRelationship]) -> None:
        """Add multiple relationships at once.

        Args:
            relationships: List of relationships to add
        """
        for relationship in relationships:
            self.add_relationship(relationship)

        logger.info("Added %s relationships", len(relationships))

    def get_relationship(
        self, source_id: str, target_id: str
    ) -> Optional[ProductRelationship]:
        """Get the relationship between two products.

        Args:
            source_id: Source product ID
            target_id: Target product ID

        Returns:
            Relationship if exists, None otherwise
        """
        return self.relationships.get(source_id, {}).get(target_id)

    def get_related_products(
        self,
        product_id: str,
        relationship_types: Optional[List[RelationshipType]] = None,
        min_strength: float = 0.0,
        active_only: bool = True,
    ) -> List[Tuple[str, ProductRelationship]]:
        """Get products related to the specified product.

        Args:
            product_id: Product ID to find relations for
            relationship_types: Types of relationships to include (None for all)
            min_strength: Minimum relationship strength
            active_only: Whether to include only active relationships

        Returns:
            List of (related_product_id, relationship) tuples
        """
        if product_id not in self.relationships:
            return []

        result = []

        for target_id, relationship in self.relationships[product_id].items():
            # Apply filters
            if active_only and not relationship.active:
                continue

            if relationship.strength < min_strength:
                continue

            if (
                relationship_types
                and relationship.relationship_type not in relationship_types
            ):
                continue

            result.append((target_id, relationship))

        return result

    def get_relationships_by_type(
        self,
        relationship_type: RelationshipType,
        min_strength: float = 0.0,
        active_only: bool = True,
    ) -> List[ProductRelationship]:
        """Get all relationships of a specific type.

        Args:
            relationship_type: Type of relationships to get
            min_strength: Minimum relationship strength
            active_only: Whether to include only active relationships

        Returns:
            List of relationships
        """
        if relationship_type not in self.by_type:
            return []

        # Apply filters
        return [
            rel
            for rel in self.by_type[relationship_type]
            if (not active_only or rel.active) and rel.strength >= min_strength
        ]

    def get_incoming_relationships(
        self,
        product_id: str,
        relationship_types: Optional[List[RelationshipType]] = None,
        min_strength: float = 0.0,
        active_only: bool = True,
    ) -> List[Tuple[str, ProductRelationship]]:
        """Get relationships targeting the specified product.

        Args:
            product_id: Product ID that is the target
            relationship_types: Types of relationships to include (None for all)
            min_strength: Minimum relationship strength
            active_only: Whether to include only active relationships

        Returns:
            List of (source_product_id, relationship) tuples
        """
        if product_id not in self.by_target:
            return []

        result = []

        for relationship in self.by_target[product_id]:
            # Apply filters
            if active_only and not relationship.active:
                continue

            if relationship.strength < min_strength:
                continue

            if (
                relationship_types
                and relationship.relationship_type not in relationship_types
            ):
                continue

            result.append((relationship.source_id, relationship))

        return result

    def update_relationship(
        self, source_id: str, target_id: str, updates: Dict[str, Any]
    ) -> bool:
        """Update an existing relationship.

        Args:
            source_id: Source product ID
            target_id: Target product ID
            updates: Dictionary of attributes to update

        Returns:
            True if relationship was updated, False if not found
        """
        relationship = self.get_relationship(source_id, target_id)
        if not relationship:
            logger.warning("Relationship not found: %s → %s", source_id, target_id)
            return bool(False)

        # Track whether relationship type or bidirectionality changed
        old_type = relationship.relationship_type
        old_bidirectional = relationship.bidirectional

        # Apply updates
        for key, value in updates.items():
            if hasattr(relationship, key):
                if key == "relationship_type" and not isinstance(
                    value, RelationshipType
                ):
                    value = RelationshipType(value)
                setattr(relationship, key, value)

        # Update timestamp
        relationship.updated_at = datetime.now()

        # Handle index updates if relationship type changed
        if old_type != relationship.relationship_type:
            # Remove from old type index and add to new
            self.by_type[old_type] = [
                r
                for r in self.by_type[old_type]
                if not (r.source_id == source_id and r.target_id == target_id)
            ]
            self.by_type[relationship.relationship_type].append(relationship)

        # Handle bidirectional changes
        if old_bidirectional != relationship.bidirectional:
            reverse_rel = self.get_relationship(target_id, source_id)

            if relationship.bidirectional and not reverse_rel:
                # Add new reverse relationship
                self.add_relationship(relationship.get_reverse())
            elif (
                not relationship.bidirectional
                and reverse_rel
                and reverse_rel.bidirectional
            ):
                # Remove automatic reverse relationship
                self._remove_relationship(target_id, source_id)

        logger.info("Updated relationship: %s → %s", source_id, target_id)
        return True

    def deactivate_relationship(self, source_id: str, target_id: str) -> bool:
        """Deactivate a relationship (soft delete).

        Args:
            source_id: Source product ID
            target_id: Target product ID

        Returns:
            True if relationship was deactivated, False if not found
        """
        return bool(self.update_relationship(source_id, target_id, {"active": False}))

    def _remove_relationship(self, source_id: str, target_id: str) -> bool:
        """Remove a relationship from the map (internal use).

        Args:
            source_id: Source product ID
            target_id: Target product ID

        Returns:
            True if relationship was removed, False if not found
        """
        if (
            source_id not in self.relationships
            or target_id not in self.relationships[source_id]
        ):
            return False

        # Get relationship for index updates
        relationship = self.relationships[source_id][target_id]

        # Remove from main storage
        del self.relationships[source_id][target_id]
        if not self.relationships[source_id]:
            del self.relationships[source_id]

        # Remove from type index
        self.by_type[relationship.relationship_type] = [
            r
            for r in self.by_type[relationship.relationship_type]
            if not (r.source_id == source_id and r.target_id == target_id)
        ]
        if not self.by_type[relationship.relationship_type]:
            del self.by_type[relationship.relationship_type]

        # Remove from target index
        self.by_target[target_id] = [
            r
            for r in self.by_target[target_id]
            if not (r.source_id == source_id and r.target_id == target_id)
        ]
        if not self.by_target[target_id]:
            del self.by_target[target_id]

        return True

    def get_all_relationships(self) -> List[ProductRelationship]:
        """Get all relationships in the map.

        Returns:
            List of all relationships
        """
        result = []
        for source_relationships in self.relationships.values():
            result.extend(source_relationships.values())
        return result

    def clear(self) -> None:
        """Clear all relationships from the map."""
        self.relationships.clear()
        self.by_type.clear()
        self.by_target.clear()
        logger.info("Cleared product relationship map")

    def export_to_json(self, file_path: str) -> None:
        """Export relationships to a JSON file.

        Args:
            file_path: Path to export file
        """
        relationships = self.get_all_relationships()
        data = [rel.to_dict() for rel in relationships]

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("Exported %s relationships to %s", len(relationships), file_path)

    def import_from_json(self, file_path: str) -> int:
        """Import relationships from a JSON file.

        Args:
            file_path: Path to import file

        Returns:
            Number of relationships imported
        """
        with open(file_path, "r") as f:
            data = json.load(f)

        relationships = [ProductRelationship.from_dict(item) for item in data]
        self.add_relationships(relationships)

        logger.info("Imported %s relationships from %s", len(relationships), file_path)
        return len(relationships)

    def export_to_csv(self, file_path: str) -> None:
        """Export relationships to a CSV file.

        Args:
            file_path: Path to export file
        """
        relationships = self.get_all_relationships()

        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(
                [
                    "source_id",
                    "target_id",
                    "relationship_type",
                    "strength",
                    "bidirectional",
                    "active",
                    "created_at",
                    "updated_at",
                ]
            )

            # Write data
            for rel in relationships:
                writer.writerow(
                    [
                        rel.source_id,
                        rel.target_id,
                        rel.relationship_type.value,
                        rel.strength,
                        rel.bidirectional,
                        rel.active,
                        rel.created_at.isoformat(),
                        rel.updated_at.isoformat(),
                    ]
                )

        logger.info("Exported %s relationships to %s", len(relationships), file_path)

    def import_from_csv(self, file_path: str) -> int:
        """Import relationships from a CSV file.

        Args:
            file_path: Path to import file

        Returns:
            Number of relationships imported
        """
        relationships = []

        with open(file_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert some values to appropriate types
                rel = ProductRelationship(
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    relationship_type=row["relationship_type"],
                    strength=float(row["strength"]),
                    bidirectional=row["bidirectional"].lower() == "true",
                    active=row["active"].lower() == "true",
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                relationships.append(rel)

        self.add_relationships(relationships)

        logger.info("Imported %s relationships from %s", len(relationships), file_path)
        return len(relationships)

    def generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the relationships.

        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_relationships": len(self.get_all_relationships()),
            "total_products": len(self.relationships)
            + len(self.by_target)
            - len(set(self.relationships.keys()) & set(self.by_target.keys())),
            "by_type": {
                rel_type.value: len(rels) for rel_type, rels in self.by_type.items()
            },
            "bidirectional_count": len(
                [rel for rel in self.get_all_relationships() if rel.bidirectional]
            ),
            "active_count": len(
                [rel for rel in self.get_all_relationships() if rel.active]
            ),
        }
        return stats

    def __len__(self) -> int:
        """Get the number of relationships.

        Returns:
            Number of relationships
        """
        return len(self.get_all_relationships())

    def __iter__(self) -> Iterator[ProductRelationship]:
        """Iterate through all relationships.

        Returns:
            Iterator of relationships
        """
        for source_relationships in self.relationships.values():
            yield from source_relationships.values()
