"""
Relationship Graph for modeling entity relationships.

This module provides a graph-based model for representing relationships between
entities in the system, supporting various relationship types, strengths, and
directional properties.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of relationships between entities."""

    CAUSAL = "causal"  # A causes B
    CORRELATION = "correlation"  # A is correlated with B
    DEPENDENCY = "dependency"  # A depends on B
    INFLUENCE = "influence"  # A influences B
    SIMILARITY = "similarity"  # A is similar to B
    SEQUENCE = "sequence"  # A precedes B in sequence
    COMPOSITION = "composition"  # A is composed of B
    ASSOCIATION = "association"  # A is associated with B
    CUSTOM = "custom"  # Custom relationship type


class EntityType(str, Enum):
    """Types of entities in the relationship graph."""

    PRODUCT = "product"
    CATEGORY = "category"
    MARKETPLACE = "marketplace"
    PRICE = "price"
    INVENTORY = "inventory"
    SALES = "sales"
    COMPETITOR = "competitor"
    CUSTOMER = "customer"
    METRIC = "metric"
    EVENT = "event"
    DECISION = "decision"
    CUSTOM = "custom"


class Relationship:
    """Represents a relationship between two entities."""

    def __init__(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        strength: float = 1.0,
        bidirectional: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize a relationship.

        Args:
            source_id: ID of the source entity
            target_id: ID of the target entity
            relationship_type: Type of relationship
            strength: Strength of the relationship (0.0 to 1.0)
            bidirectional: Whether the relationship applies in both directions
            metadata: Additional metadata about the relationship
            confidence: Confidence in the relationship (0.0 to 1.0)
            timestamp: When the relationship was established
        """
        self.source_id = source_id
        self.target_id = target_id
        self.relationship_type = relationship_type
        self.strength = max(0.0, min(1.0, strength))  # Clamp to [0, 1]
        self.bidirectional = bidirectional
        self.metadata = metadata or {}
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        self.timestamp = timestamp or datetime.now()

    def get_reverse(self) -> "Relationship":
        """
        Get the reverse of this relationship.

        Returns:
            A new Relationship object with source and target swapped
        """
        return Relationship(
            source_id=self.target_id,
            target_id=self.source_id,
            relationship_type=self.relationship_type,
            strength=self.strength,
            bidirectional=self.bidirectional,
            metadata=self.metadata.copy(),
            confidence=self.confidence,
            timestamp=self.timestamp,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.

        Returns:
            Dictionary representation of the relationship
        """
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "strength": self.strength,
            "bidirectional": self.bidirectional,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        """
        Create a Relationship from a dictionary.

        Args:
            data: Dictionary representation of a relationship

        Returns:
            Relationship object
        """
        # Convert string timestamp to datetime
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # Convert string relationship type to enum
        rel_type = data.get("relationship_type")
        if isinstance(rel_type, str):
            rel_type = RelationshipType(rel_type)

        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relationship_type=rel_type,
            strength=data.get("strength", 1.0),
            bidirectional=data.get("bidirectional", False),
            metadata=data.get("metadata", {}),
            confidence=data.get("confidence", 1.0),
            timestamp=timestamp,
        )

    def __str__(self) -> str:
        """String representation of the relationship."""
        direction = "<->" if self.bidirectional else "->"
        return f"{self.source_id} {direction} {self.target_id} ({self.relationship_type.value}, {self.strength:.2f})"


class Entity:
    """Represents an entity in the relationship graph."""

    def __init__(
        self,
        entity_id: str,
        entity_type: EntityType,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an entity.

        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity
            name: Human-readable name for the entity
            attributes: Entity attributes
            metadata: Additional metadata
        """
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.name = name or entity_id
        self.attributes = attributes or {}
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.

        Returns:
            Dictionary representation of the entity
        """
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "attributes": self.attributes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """
        Create an Entity from a dictionary.

        Args:
            data: Dictionary representation of an entity

        Returns:
            Entity object
        """
        # Convert string entity type to enum
        entity_type = data.get("entity_type")
        if isinstance(entity_type, str):
            entity_type = EntityType(entity_type)

        return cls(
            entity_id=data["entity_id"],
            entity_type=entity_type,
            name=data.get("name"),
            attributes=data.get("attributes", {}),
            metadata=data.get("metadata", {}),
        )

    def __str__(self) -> str:
        """String representation of the entity."""
        return f"{self.name} ({self.entity_type.value})"


class RelationshipGraph:
    """
    Graph-based model for entity relationships.

    This class provides a graph structure for modeling relationships between
    entities, with support for querying, traversal, and analysis.
    """

    def __init__(self):
        """Initialize the relationship graph."""
        # Use NetworkX for the graph structure
        self.graph = nx.DiGraph()
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Dict[str, Relationship]] = {}

    def add_entity(self, entity: Entity) -> None:
        """
        Add an entity to the graph.

        Args:
            entity: Entity to add
        """
        # Store the entity
        self.entities[entity.entity_id] = entity

        # Add to graph with attributes
        self.graph.add_node(
            entity.entity_id,
            entity_type=entity.entity_type.value,
            name=entity.name,
            attributes=entity.attributes,
            metadata=entity.metadata,
        )

        logger.debug(f"Added entity: {entity}")

    def add_relationship(self, relationship: Relationship) -> None:
        """
        Add a relationship to the graph.

        Args:
            relationship: Relationship to add
        """
        source_id = relationship.source_id
        target_id = relationship.target_id

        # Ensure entities exist
        if source_id not in self.entities:
            logger.warning(f"Source entity {source_id} not found, creating placeholder")
            self.add_entity(Entity(source_id, EntityType.CUSTOM))

        if target_id not in self.entities:
            logger.warning(f"Target entity {target_id} not found, creating placeholder")
            self.add_entity(Entity(target_id, EntityType.CUSTOM))

        # Initialize relationship dictionaries if needed
        if source_id not in self.relationships:
            self.relationships[source_id] = {}

        # Store the relationship
        self.relationships[source_id][target_id] = relationship

        # Add to graph with attributes
        self.graph.add_edge(
            source_id,
            target_id,
            relationship_type=relationship.relationship_type.value,
            strength=relationship.strength,
            bidirectional=relationship.bidirectional,
            metadata=relationship.metadata,
            confidence=relationship.confidence,
            timestamp=relationship.timestamp,
        )

        # Handle bidirectional relationships
        if relationship.bidirectional:
            reverse_rel = relationship.get_reverse()

            if target_id not in self.relationships:
                self.relationships[target_id] = {}

            self.relationships[target_id][source_id] = reverse_rel

            # Add reverse edge to graph
            self.graph.add_edge(
                target_id,
                source_id,
                relationship_type=reverse_rel.relationship_type.value,
                strength=reverse_rel.strength,
                bidirectional=reverse_rel.bidirectional,
                metadata=reverse_rel.metadata,
                confidence=reverse_rel.confidence,
                timestamp=reverse_rel.timestamp,
            )

        logger.debug(f"Added relationship: {relationship}")

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Get an entity by ID.

        Args:
            entity_id: ID of the entity

        Returns:
            Entity if found, None otherwise
        """
        return self.entities.get(entity_id)

    def get_relationship(
        self, source_id: str, target_id: str
    ) -> Optional[Relationship]:
        """
        Get a relationship between two entities.

        Args:
            source_id: ID of the source entity
            target_id: ID of the target entity

        Returns:
            Relationship if found, None otherwise
        """
        if source_id in self.relationships:
            return self.relationships[source_id].get(target_id)
        return None

    def get_relationships_from(self, entity_id: str) -> List[Relationship]:
        """
        Get all relationships from an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            List of relationships
        """
        if entity_id in self.relationships:
            return list(self.relationships[entity_id].values())
        return []

    def get_relationships_to(self, entity_id: str) -> List[Relationship]:
        """
        Get all relationships to an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            List of relationships
        """
        result = []
        for source_id, targets in self.relationships.items():
            if entity_id in targets:
                result.append(targets[entity_id])
        return result

    def get_related_entities(
        self,
        entity_id: str,
        relationship_types: Optional[List[RelationshipType]] = None,
        min_strength: float = 0.0,
        direction: str = "outgoing",
    ) -> List[Tuple[Entity, Relationship]]:
        """
        Get entities related to the specified entity.

        Args:
            entity_id: ID of the entity
            relationship_types: Optional filter for relationship types
            min_strength: Minimum relationship strength
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of (entity, relationship) tuples
        """
        result = []

        # Get outgoing relationships
        if direction in ["outgoing", "both"]:
            if entity_id in self.relationships:
                for target_id, relationship in self.relationships[entity_id].items():
                    if relationship.strength >= min_strength:
                        if (
                            relationship_types is None
                            or relationship.relationship_type in relationship_types
                        ):
                            target_entity = self.entities.get(target_id)
                            if target_entity:
                                result.append((target_entity, relationship))

        # Get incoming relationships
        if direction in ["incoming", "both"]:
            for source_id, targets in self.relationships.items():
                if entity_id in targets:
                    relationship = targets[entity_id]
                    if relationship.strength >= min_strength:
                        if (
                            relationship_types is None
                            or relationship.relationship_type in relationship_types
                        ):
                            source_entity = self.entities.get(source_id)
                            if source_entity:
                                result.append((source_entity, relationship))

        return result

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 5,
        min_strength: float = 0.0,
    ) -> List[Tuple[Entity, Relationship]]:
        """
        Find a path between two entities.

        Args:
            source_id: ID of the source entity
            target_id: ID of the target entity
            max_length: Maximum path length
            min_strength: Minimum relationship strength

        Returns:
            List of (entity, relationship) tuples representing the path
        """
        # Create a subgraph with edges meeting the strength threshold
        subgraph = nx.DiGraph()

        for u, v, data in self.graph.edges(data=True):
            if data["strength"] >= min_strength:
                subgraph.add_edge(u, v)

        # Try to find a path
        try:
            path = nx.shortest_path(subgraph, source_id, target_id, weight=None)

            # Check if path is within max length
            if len(path) > max_length + 1:
                return []

            # Convert path to entity-relationship format
            result = []
            for i in range(len(path) - 1):
                current_id = path[i]
                next_id = path[i + 1]

                current_entity = self.entities.get(current_id)
                relationship = self.get_relationship(current_id, next_id)

                if current_entity and relationship:
                    result.append((current_entity, relationship))

            return result
        except nx.NetworkXNoPath:
            return []

    def find_all_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 3,
        min_strength: float = 0.0,
    ) -> List[List[Tuple[Entity, Relationship]]]:
        """
        Find all paths between two entities.

        Args:
            source_id: ID of the source entity
            target_id: ID of the target entity
            max_length: Maximum path length
            min_strength: Minimum relationship strength

        Returns:
            List of paths, each a list of (entity, relationship) tuples
        """
        # Create a subgraph with edges meeting the strength threshold
        subgraph = nx.DiGraph()

        for u, v, data in self.graph.edges(data=True):
            if data["strength"] >= min_strength:
                subgraph.add_edge(u, v)

        # Try to find all paths
        try:
            all_paths = list(
                nx.all_simple_paths(subgraph, source_id, target_id, cutoff=max_length)
            )

            # Convert paths to entity-relationship format
            result = []

            for path in all_paths:
                path_result = []
                for i in range(len(path) - 1):
                    current_id = path[i]
                    next_id = path[i + 1]

                    current_entity = self.entities.get(current_id)
                    relationship = self.get_relationship(current_id, next_id)

                    if current_entity and relationship:
                        path_result.append((current_entity, relationship))

                result.append(path_result)

            return result
        except (nx.NetworkXNoPath, nx.NetworkXError):
            return []

    def get_entity_neighborhood(
        self, entity_id: str, depth: int = 1, min_strength: float = 0.0
    ) -> Dict[str, Any]:
        """
        Get the neighborhood of an entity.

        Args:
            entity_id: ID of the entity
            depth: Neighborhood depth
            min_strength: Minimum relationship strength

        Returns:
            Dictionary with neighborhood information
        """
        if entity_id not in self.entities:
            return {"entity_id": entity_id, "found": False}

        # Create a subgraph with edges meeting the strength threshold
        subgraph = nx.DiGraph()

        for u, v, data in self.graph.edges(data=True):
            if data["strength"] >= min_strength:
                subgraph.add_edge(u, v)

        # Get neighborhood nodes
        neighborhood = set()
        current_nodes = {entity_id}

        for _ in range(depth):
            next_nodes = set()

            for node in current_nodes:
                # Add outgoing neighbors
                next_nodes.update(subgraph.successors(node))

                # Add incoming neighbors
                next_nodes.update(subgraph.predecessors(node))

            neighborhood.update(current_nodes)
            current_nodes = next_nodes - neighborhood

        # Convert to entity-relationship structure
        entities = {}
        relationships = []

        for node_id in neighborhood:
            if node_id in self.entities:
                entities[node_id] = self.entities[node_id].to_dict()

        for source_id in neighborhood:
            for target_id in neighborhood:
                relationship = self.get_relationship(source_id, target_id)
                if relationship and relationship.strength >= min_strength:
                    relationships.append(relationship.to_dict())

        return {
            "entity_id": entity_id,
            "found": True,
            "depth": depth,
            "entities": entities,
            "relationships": relationships,
        }

    def calculate_centrality(self, centrality_type: str = "degree") -> Dict[str, float]:
        """
        Calculate centrality measures for entities.

        Args:
            centrality_type: Type of centrality ("degree", "betweenness", "closeness", "eigenvector")

        Returns:
            Dictionary mapping entity IDs to centrality values
        """
        if centrality_type == "degree":
            centrality = nx.degree_centrality(self.graph)
        elif centrality_type == "betweenness":
            centrality = nx.betweenness_centrality(self.graph)
        elif centrality_type == "closeness":
            centrality = nx.closeness_centrality(self.graph)
        elif centrality_type == "eigenvector":
            centrality = nx.eigenvector_centrality_numpy(self.graph)
        else:
            raise ValueError(f"Unsupported centrality type: {centrality_type}")

        return centrality

    def find_communities(self, algorithm: str = "louvain") -> List[Set[str]]:
        """
        Find communities in the graph.

        Args:
            algorithm: Community detection algorithm ("louvain", "label_propagation")

        Returns:
            List of communities, each a set of entity IDs
        """
        # Convert to undirected graph for community detection
        undirected = self.graph.to_undirected()

        if algorithm == "louvain":
            import community as community_louvain

            partition = community_louvain.best_partition(undirected)

            # Group by community
            communities = {}
            for node, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = set()
                communities[community_id].add(node)

            return list(communities.values())

        elif algorithm == "label_propagation":
            from networkx.algorithms import community

            communities = community.label_propagation_communities(undirected)
            return list(communities)

        else:
            raise ValueError(f"Unsupported community detection algorithm: {algorithm}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the graph to a dictionary representation.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "entities": {
                entity_id: entity.to_dict()
                for entity_id, entity in self.entities.items()
            },
            "relationships": [
                relationship.to_dict()
                for source_dict in self.relationships.values()
                for relationship in source_dict.values()
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationshipGraph":
        """
        Create a RelationshipGraph from a dictionary.

        Args:
            data: Dictionary representation of a graph

        Returns:
            RelationshipGraph object
        """
        graph = cls()

        # Add entities
        for entity_data in data.get("entities", {}).values():
            graph.add_entity(Entity.from_dict(entity_data))

        # Add relationships
        for relationship_data in data.get("relationships", []):
            graph.add_relationship(Relationship.from_dict(relationship_data))

        return graph

    def __str__(self) -> str:
        """String representation of the graph."""
        return f"RelationshipGraph with {len(self.entities)} entities and {sum(len(targets) for targets in self.relationships.values())} relationships"
