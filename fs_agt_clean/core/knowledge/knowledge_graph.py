"""
Knowledge Graph Module for FlipSync Knowledge Framework

This module implements a knowledge graph for storing and querying
structured knowledge.
"""

import datetime
import json
import logging
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in the knowledge graph."""

    ENTITY = "entity"
    CONCEPT = "concept"
    EVENT = "event"
    ATTRIBUTE = "attribute"
    LOCATION = "location"
    TIME = "time"
    PERSON = "person"
    ORGANIZATION = "organization"
    PRODUCT = "product"
    CUSTOM = "custom"


class EdgeType(Enum):
    """Types of edges in the knowledge graph."""

    IS_A = "is_a"
    HAS_A = "has_a"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    CAUSES = "causes"
    PRECEDES = "precedes"
    LOCATED_IN = "located_in"
    OCCURS_AT = "occurs_at"
    CREATED_BY = "created_by"
    OWNED_BY = "owned_by"
    CUSTOM = "custom"


class Node:
    """Represents a node in the knowledge graph."""

    def __init__(
        self,
        node_id: Optional[str] = None,
        node_type: NodeType = NodeType.ENTITY,
        name: str = "",
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        source: Optional[str] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
    ):
        self.node_id = node_id or str(uuid.uuid4())
        self.node_type = node_type
        self.name = name
        self.properties = properties or {}
        self.confidence = confidence
        self.source = source
        self.created_at = created_at or datetime.datetime.now()
        self.updated_at = updated_at or self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "properties": self.properties,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """Create node from dictionary representation."""
        return cls(
            node_id=data["node_id"],
            node_type=NodeType(data["node_type"]),
            name=data["name"],
            properties=data["properties"],
            confidence=data["confidence"],
            source=data.get("source"),
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.datetime.fromisoformat(data["updated_at"]),
        )

    def update(
        self,
        node_type: Optional[NodeType] = None,
        name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        source: Optional[str] = None,
    ) -> None:
        """
        Update node properties.

        Args:
            node_type: New node type
            name: New name
            properties: New properties
            confidence: New confidence
            source: New source
        """
        if node_type is not None:
            self.node_type = node_type
        if name is not None:
            self.name = name
        if properties is not None:
            self.properties.update(properties)
        if confidence is not None:
            self.confidence = confidence
        if source is not None:
            self.source = source
        self.updated_at = datetime.datetime.now()


class Edge:
    """Represents an edge in the knowledge graph."""

    def __init__(
        self,
        edge_id: Optional[str] = None,
        edge_type: EdgeType = EdgeType.RELATED_TO,
        source_id: str = "",
        target_id: str = "",
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        source: Optional[str] = None,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
    ):
        self.edge_id = edge_id or str(uuid.uuid4())
        self.edge_type = edge_type
        self.source_id = source_id
        self.target_id = target_id
        self.properties = properties or {}
        self.confidence = confidence
        self.source = source
        self.created_at = created_at or datetime.datetime.now()
        self.updated_at = updated_at or self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            "edge_id": self.edge_id,
            "edge_type": self.edge_type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Edge":
        """Create edge from dictionary representation."""
        return cls(
            edge_id=data["edge_id"],
            edge_type=EdgeType(data["edge_type"]),
            source_id=data["source_id"],
            target_id=data["target_id"],
            properties=data["properties"],
            confidence=data["confidence"],
            source=data.get("source"),
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.datetime.fromisoformat(data["updated_at"]),
        )

    def update(
        self,
        edge_type: Optional[EdgeType] = None,
        properties: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        source: Optional[str] = None,
    ) -> None:
        """
        Update edge properties.

        Args:
            edge_type: New edge type
            properties: New properties
            confidence: New confidence
            source: New source
        """
        if edge_type is not None:
            self.edge_type = edge_type
        if properties is not None:
            self.properties.update(properties)
        if confidence is not None:
            self.confidence = confidence
        if source is not None:
            self.source = source
        self.updated_at = datetime.datetime.now()


class KnowledgeGraph:
    """Knowledge graph for storing and querying structured knowledge."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.graph = nx.MultiDiGraph()

    def add_node(self, node: Node) -> str:
        """
        Add a node to the knowledge graph.

        Args:
            node: Node to add

        Returns:
            ID of the added node
        """
        # Check if node already exists
        if node.node_id in self.nodes:
            # Update existing node
            self.nodes[node.node_id].update(
                node_type=node.node_type,
                name=node.name,
                properties=node.properties,
                confidence=node.confidence,
                source=node.source,
            )
        else:
            # Add new node
            self.nodes[node.node_id] = node
            self.graph.add_node(
                node.node_id,
                node_type=node.node_type.value,
                name=node.name,
                properties=node.properties,
                confidence=node.confidence,
            )

        return node.node_id

    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Get a node by ID.

        Args:
            node_id: ID of the node to get

        Returns:
            Node, or None if not found
        """
        return self.nodes.get(node_id)

    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the knowledge graph.

        Args:
            node_id: ID of the node to remove

        Returns:
            True if the node was removed, False otherwise
        """
        if node_id not in self.nodes:
            return False

        # Remove all edges connected to this node
        edges_to_remove = []
        for edge_id, edge in self.edges.items():
            if edge.source_id == node_id or edge.target_id == node_id:
                edges_to_remove.append(edge_id)

        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

        # Remove the node
        del self.nodes[node_id]
        self.graph.remove_node(node_id)

        return True

    def add_edge(self, edge: Edge) -> str:
        """
        Add an edge to the knowledge graph.

        Args:
            edge: Edge to add

        Returns:
            ID of the added edge
        """
        # Check if source and target nodes exist
        if edge.source_id not in self.nodes:
            raise ValueError(f"Source node {edge.source_id} does not exist")

        if edge.target_id not in self.nodes:
            raise ValueError(f"Target node {edge.target_id} does not exist")

        # Check if edge already exists
        if edge.edge_id in self.edges:
            # Update existing edge
            self.edges[edge.edge_id].update(
                properties=edge.properties,
                confidence=edge.confidence,
                source=edge.source,
            )
        else:
            # Add new edge
            self.edges[edge.edge_id] = edge
            self.graph.add_edge(
                edge.source_id,
                edge.target_id,
                key=edge.edge_id,
                edge_type=edge.edge_type.value,
                properties=edge.properties,
                confidence=edge.confidence,
            )

        return edge.edge_id

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """
        Get an edge by ID.

        Args:
            edge_id: ID of the edge to get

        Returns:
            Edge, or None if not found
        """
        return self.edges.get(edge_id)

    def remove_edge(self, edge_id: str) -> bool:
        """
        Remove an edge from the knowledge graph.

        Args:
            edge_id: ID of the edge to remove

        Returns:
            True if the edge was removed, False otherwise
        """
        if edge_id not in self.edges:
            return False

        edge = self.edges[edge_id]
        del self.edges[edge_id]

        # Remove from networkx graph
        if self.graph.has_edge(edge.source_id, edge.target_id, key=edge_id):
            self.graph.remove_edge(edge.source_id, edge.target_id, key=edge_id)

        return True

    def get_neighbors(
        self, node_id: str, edge_type: Optional[EdgeType] = None
    ) -> List[Node]:
        """
        Get neighbors of a node.

        Args:
            node_id: ID of the node
            edge_type: Optional filter for edge type

        Returns:
            List of neighboring nodes
        """
        if node_id not in self.nodes:
            return []

        neighbors = []
        for _, target_id, edge_data in self.graph.out_edges(node_id, data=True):
            if edge_type is None or edge_data["edge_type"] == edge_type.value:
                neighbor = self.nodes.get(target_id)
                if neighbor:
                    neighbors.append(neighbor)

        return neighbors

    def get_incoming_neighbors(
        self, node_id: str, edge_type: Optional[EdgeType] = None
    ) -> List[Node]:
        """
        Get incoming neighbors of a node.

        Args:
            node_id: ID of the node
            edge_type: Optional filter for edge type

        Returns:
            List of incoming neighboring nodes
        """
        if node_id not in self.nodes:
            return []

        neighbors = []
        for source_id, _, edge_data in self.graph.in_edges(node_id, data=True):
            if edge_type is None or edge_data["edge_type"] == edge_type.value:
                neighbor = self.nodes.get(source_id)
                if neighbor:
                    neighbors.append(neighbor)

        return neighbors

    def get_edges_between(
        self, source_id: str, target_id: str, edge_type: Optional[EdgeType] = None
    ) -> List[Edge]:
        """
        Get edges between two nodes.

        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_type: Optional filter for edge type

        Returns:
            List of edges between the nodes
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []

        edges = []
        for _, _, key, edge_data in self.graph.edges(
            source_id, target_id, keys=True, data=True
        ):
            if edge_type is None or edge_data["edge_type"] == edge_type.value:
                edge = self.edges.get(key)
                if edge:
                    edges.append(edge)

        return edges

    def search_nodes(
        self, query: str, node_type: Optional[NodeType] = None
    ) -> List[Node]:
        """
        Search for nodes by name or properties.

        Args:
            query: Search query
            node_type: Optional filter for node type

        Returns:
            List of matching nodes
        """
        query = query.lower()
        results = []

        for node in self.nodes.values():
            if node_type is not None and node.node_type != node_type:
                continue

            # Check name
            if query in node.name.lower():
                results.append(node)
                continue

            # Check properties
            for key, value in node.properties.items():
                if isinstance(value, str) and query in value.lower():
                    results.append(node)
                    break

        return results

    def get_subgraph(self, node_ids: List[str], max_depth: int = 1) -> "KnowledgeGraph":
        """
        Get a subgraph centered on the specified nodes.

        Args:
            node_ids: IDs of the central nodes
            max_depth: Maximum depth of the subgraph

        Returns:
            Subgraph as a new KnowledgeGraph
        """
        # Create a new knowledge graph
        subgraph = KnowledgeGraph()

        # Add the central nodes
        nodes_to_process = set()
        for node_id in node_ids:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                subgraph.add_node(node)
                nodes_to_process.add(node_id)

        # Expand the subgraph
        for _ in range(max_depth):
            new_nodes = set()
            for node_id in nodes_to_process:
                # Add outgoing edges and nodes
                for _, target_id, key in self.graph.out_edges(node_id, keys=True):
                    if target_id not in subgraph.nodes:
                        target_node = self.nodes[target_id]
                        subgraph.add_node(target_node)
                        new_nodes.add(target_id)

                    edge = self.edges[key]
                    subgraph.add_edge(edge)

                # Add incoming edges and nodes
                for source_id, _, key in self.graph.in_edges(node_id, keys=True):
                    if source_id not in subgraph.nodes:
                        source_node = self.nodes[source_id]
                        subgraph.add_node(source_node)
                        new_nodes.add(source_id)

                    edge = self.edges[key]
                    subgraph.add_edge(edge)

            nodes_to_process = new_nodes
            if not nodes_to_process:
                break

        return subgraph

    def to_dict(self) -> Dict[str, Any]:
        """Convert knowledge graph to dictionary representation."""
        return {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": {edge_id: edge.to_dict() for edge_id, edge in self.edges.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeGraph":
        """Create knowledge graph from dictionary representation."""
        graph = cls()

        # Add nodes
        for node_id, node_data in data["nodes"].items():
            node = Node.from_dict(node_data)
            graph.add_node(node)

        # Add edges
        for edge_id, edge_data in data["edges"].items():
            edge = Edge.from_dict(edge_data)
            graph.add_edge(edge)

        return graph

    def to_json(self) -> str:
        """Convert knowledge graph to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "KnowledgeGraph":
        """Create knowledge graph from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_networkx(self) -> nx.MultiDiGraph:
        """Convert knowledge graph to NetworkX graph."""
        return self.graph.copy()

    def merge(self, other: "KnowledgeGraph") -> None:
        """
        Merge another knowledge graph into this one.

        Args:
            other: Knowledge graph to merge
        """
        # Merge nodes
        for node_id, node in other.nodes.items():
            self.add_node(node)

        # Merge edges
        for edge_id, edge in other.edges.items():
            try:
                self.add_edge(edge)
            except ValueError:
                # Skip edges with missing nodes
                pass
