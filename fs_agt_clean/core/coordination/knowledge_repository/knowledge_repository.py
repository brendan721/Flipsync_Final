"""
Knowledge Repository interface and related classes.

This module defines the core interfaces and classes for the Knowledge Repository
component, including the KnowledgeItem, KnowledgeType, KnowledgeStatus, and
KnowledgeRepository classes.
"""

import abc
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

import numpy as np

from fs_agt_clean.core.monitoring import get_logger


class KnowledgeType(Enum):
    """Types of knowledge items."""

    FACT = auto()  # Factual information
    RULE = auto()  # Rules or constraints
    PROCEDURE = auto()  # Procedural knowledge
    CONCEPT = auto()  # Conceptual knowledge
    RELATION = auto()  # Relational knowledge
    METADATA = auto()  # Metadata about other knowledge
    OTHER = auto()  # Other types of knowledge


class KnowledgeStatus(Enum):
    """Status of knowledge items."""

    DRAFT = auto()  # Draft knowledge, not yet validated
    ACTIVE = auto()  # Active knowledge, validated and available
    DEPRECATED = auto()  # Deprecated knowledge, still available but not recommended
    ARCHIVED = auto()  # Archived knowledge, not actively available
    INVALID = auto()  # Invalid knowledge, failed validation


class KnowledgeError(Exception):
    """Base exception for knowledge repository errors."""

    def __init__(
        self,
        message: str,
        knowledge_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize a knowledge error.

        Args:
            message: Error message
            knowledge_id: ID of the knowledge item related to the error
            cause: Original exception that caused this error
        """
        self.message = message
        self.knowledge_id = knowledge_id
        self.cause = cause

        # Create a detailed error message
        detailed_message = message
        if knowledge_id:
            detailed_message += f" (knowledge_id: {knowledge_id})"
        if cause:
            detailed_message += f" - caused by: {str(cause)}"

        super().__init__(detailed_message)


class KnowledgeItem:
    """
    A knowledge item in the knowledge repository.

    A knowledge item represents a piece of knowledge with associated metadata,
    content, and vector representation.
    """

    def __init__(
        self,
        knowledge_id: str,
        knowledge_type: KnowledgeType,
        topic: str,
        content: Any,
        vector: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        status: KnowledgeStatus = KnowledgeStatus.DRAFT,
        version: int = 1,
        previous_version_id: Optional[str] = None,
        access_control: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
    ):
        """
        Initialize a knowledge item.

        Args:
            knowledge_id: Unique identifier for the knowledge item
            knowledge_type: Type of knowledge
            topic: Topic or category of the knowledge
            content: Content of the knowledge item
            vector: Vector representation of the knowledge
            metadata: Additional metadata about the knowledge
            source_id: ID of the source that created the knowledge
            created_at: Creation timestamp
            updated_at: Last update timestamp
            status: Status of the knowledge item
            version: Version number
            previous_version_id: ID of the previous version
            access_control: Access control information
            tags: Tags for categorizing the knowledge
        """
        self.knowledge_id = knowledge_id
        self.knowledge_type = knowledge_type
        self.topic = topic
        self.content = content
        self.vector = vector
        self.metadata = metadata or {}
        self.source_id = source_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or self.created_at
        self.status = status
        self.version = version
        self.previous_version_id = previous_version_id
        self.access_control = access_control or {}
        self.tags = tags or set()

    @classmethod
    def create(
        cls,
        knowledge_type: KnowledgeType,
        topic: str,
        content: Any,
        vector: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_id: Optional[str] = None,
        access_control: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
    ) -> "KnowledgeItem":
        """
        Create a new knowledge item with a generated ID.

        Args:
            knowledge_type: Type of knowledge
            topic: Topic or category of the knowledge
            content: Content of the knowledge item
            vector: Vector representation of the knowledge
            metadata: Additional metadata about the knowledge
            source_id: ID of the source that created the knowledge
            access_control: Access control information
            tags: Tags for categorizing the knowledge

        Returns:
            A new knowledge item
        """
        knowledge_id = str(uuid.uuid4())
        return cls(
            knowledge_id=knowledge_id,
            knowledge_type=knowledge_type,
            topic=topic,
            content=content,
            vector=vector,
            metadata=metadata,
            source_id=source_id,
            access_control=access_control,
            tags=tags,
        )

    def update(
        self,
        content: Optional[Any] = None,
        vector: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: Optional[KnowledgeStatus] = None,
        tags: Optional[Set[str]] = None,
    ) -> "KnowledgeItem":
        """
        Create an updated version of this knowledge item.

        Args:
            content: New content
            vector: New vector representation
            metadata: New or updated metadata
            status: New status
            tags: New or updated tags

        Returns:
            A new knowledge item representing the updated version
        """
        # Create a new ID for the updated version
        new_id = str(uuid.uuid4())

        # Create a new knowledge item with updated fields
        return KnowledgeItem(
            knowledge_id=new_id,
            knowledge_type=self.knowledge_type,
            topic=self.topic,
            content=content if content is not None else self.content,
            vector=vector if vector is not None else self.vector,
            metadata={**self.metadata, **(metadata or {})},
            source_id=self.source_id,
            created_at=self.created_at,
            updated_at=datetime.now(),
            status=status if status is not None else self.status,
            version=self.version + 1,
            previous_version_id=self.knowledge_id,
            access_control=self.access_control,
            tags=tags if tags is not None else self.tags,
        )

    def is_active(self) -> bool:
        """
        Check if the knowledge item is active.

        Returns:
            True if the knowledge item is active
        """
        return self.status == KnowledgeStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the knowledge item to a dictionary.

        Returns:
            Dictionary representation of the knowledge item
        """
        return {
            "knowledge_id": self.knowledge_id,
            "knowledge_type": self.knowledge_type.name,
            "topic": self.topic,
            "content": self.content,
            "vector": self.vector.tolist() if self.vector is not None else None,
            "metadata": self.metadata,
            "source_id": self.source_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.name,
            "version": self.version,
            "previous_version_id": self.previous_version_id,
            "access_control": self.access_control,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeItem":
        """
        Create a knowledge item from a dictionary.

        Args:
            data: Dictionary representation of a knowledge item

        Returns:
            A knowledge item
        """
        # Convert vector from list to numpy array if present
        vector = data.get("vector")
        if vector is not None:
            vector = np.array(vector)

        # Convert timestamps from ISO format to datetime
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])

        # Convert knowledge type and status from string to enum
        knowledge_type = KnowledgeType[data["knowledge_type"]]
        status = KnowledgeStatus[data["status"]]

        # Convert tags from list to set
        tags = set(data.get("tags", []))

        return cls(
            knowledge_id=data["knowledge_id"],
            knowledge_type=knowledge_type,
            topic=data["topic"],
            content=data["content"],
            vector=vector,
            metadata=data.get("metadata", {}),
            source_id=data.get("source_id"),
            created_at=created_at,
            updated_at=updated_at,
            status=status,
            version=data.get("version", 1),
            previous_version_id=data.get("previous_version_id"),
            access_control=data.get("access_control", {}),
            tags=tags,
        )


class KnowledgeRepository(abc.ABC):
    """
    Interface for a knowledge repository.

    A knowledge repository stores, retrieves, and manages knowledge items.
    It provides methods for adding, updating, retrieving, and querying
    knowledge items.
    """

    @abc.abstractmethod
    async def start(self) -> None:
        """
        Start the knowledge repository.
        """
        pass

    @abc.abstractmethod
    async def stop(self) -> None:
        """
        Stop the knowledge repository.
        """
        pass

    @abc.abstractmethod
    async def add_knowledge(self, knowledge: KnowledgeItem) -> str:
        """
        Add a knowledge item to the repository.

        Args:
            knowledge: The knowledge item to add

        Returns:
            ID of the added knowledge item

        Raises:
            KnowledgeError: If the knowledge item cannot be added
        """
        pass

    @abc.abstractmethod
    async def update_knowledge(self, knowledge: KnowledgeItem) -> str:
        """
        Update a knowledge item in the repository.

        Args:
            knowledge: The updated knowledge item

        Returns:
            ID of the updated knowledge item

        Raises:
            KnowledgeError: If the knowledge item cannot be updated
        """
        pass

    @abc.abstractmethod
    async def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        """
        Get a knowledge item by ID.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            The knowledge item, or None if not found

        Raises:
            KnowledgeError: If the knowledge item cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        Delete a knowledge item from the repository.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            True if the knowledge item was deleted

        Raises:
            KnowledgeError: If the knowledge item cannot be deleted
        """
        pass

    @abc.abstractmethod
    async def get_knowledge_by_topic(self, topic: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by topic.

        Args:
            topic: Topic to search for

        Returns:
            List of knowledge items with the specified topic

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def get_knowledge_by_type(
        self, knowledge_type: KnowledgeType
    ) -> List[KnowledgeItem]:
        """
        Get knowledge items by type.

        Args:
            knowledge_type: Type to search for

        Returns:
            List of knowledge items with the specified type

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def get_knowledge_by_source(self, source_id: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by source.

        Args:
            source_id: Source ID to search for

        Returns:
            List of knowledge items from the specified source

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def get_knowledge_by_tag(self, tag: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of knowledge items with the specified tag

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def search_knowledge(
        self, query: str, limit: int = 10
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        Search for knowledge items by similarity to a query.

        Args:
            query: Query string
            limit: Maximum number of results

        Returns:
            List of (knowledge item, similarity score) tuples

        Raises:
            KnowledgeError: If the search cannot be performed
        """
        pass

    @abc.abstractmethod
    async def similar_knowledge(
        self, knowledge_id: str, limit: int = 10
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        Find knowledge items similar to a given knowledge item.

        Args:
            knowledge_id: ID of the knowledge item
            limit: Maximum number of results

        Returns:
            List of (knowledge item, similarity score) tuples

        Raises:
            KnowledgeError: If the similarity search cannot be performed
        """
        pass

    @abc.abstractmethod
    async def get_knowledge_version_history(
        self, knowledge_id: str
    ) -> List[KnowledgeItem]:
        """
        Get the version history of a knowledge item.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            List of knowledge items representing the version history

        Raises:
            KnowledgeError: If the version history cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def get_knowledge_by_status(
        self, status: KnowledgeStatus
    ) -> List[KnowledgeItem]:
        """
        Get knowledge items by status.

        Args:
            status: Status to search for

        Returns:
            List of knowledge items with the specified status

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def get_all_knowledge(self) -> List[KnowledgeItem]:
        """
        Get all knowledge items in the repository.

        Returns:
            List of all knowledge items

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def get_knowledge_updates(
        self, since_timestamp: datetime
    ) -> List[KnowledgeItem]:
        """
        Get knowledge items updated since a timestamp.

        Args:
            since_timestamp: Timestamp to get updates since

        Returns:
            List of knowledge items updated since the timestamp

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def get_critical_updates(
        self, since_timestamp: datetime, priority_threshold: float = 0.5
    ) -> List[KnowledgeItem]:
        """
        Get critical knowledge updates since a timestamp.

        This method is optimized for mobile devices with limited bandwidth.
        It returns only high-priority knowledge updates.

        Args:
            since_timestamp: Timestamp to get updates since
            priority_threshold: Priority threshold (0.0 to 1.0)

        Returns:
            List of critical knowledge items updated since the timestamp

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        pass
