"""
Knowledge retriever for the knowledge repository.

This module provides interfaces and implementations for retrieving knowledge
from the knowledge repository, including similarity search and filtering.
"""

import abc
from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

import numpy as np

from fs_agt_clean.core.coordination.knowledge_repository.embedding_provider import (
    EmbeddingError,
    EmbeddingProvider,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_repository import (
    KnowledgeError,
    KnowledgeItem,
    KnowledgeStatus,
    KnowledgeType,
)
from fs_agt_clean.core.monitoring import get_logger


@dataclass
class QueryResult:
    """
    Result of a knowledge query.

    This class represents a knowledge item returned from a query,
    along with its relevance score.
    """

    knowledge: KnowledgeItem
    score: float


class SimilaritySearch(abc.ABC):
    """
    Interface for similarity search.

    Similarity search finds knowledge items similar to a query.
    """

    @abc.abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[QueryResult]:
        """
        Search for knowledge items similar to a query.

        Args:
            query: Query string
            limit: Maximum number of results

        Returns:
            List of query results
        """
        pass

    @abc.abstractmethod
    async def search_by_vector(
        self, query_vector: np.ndarray, limit: int = 10
    ) -> List[QueryResult]:
        """
        Search for knowledge items similar to a query vector.

        Args:
            query_vector: Query vector
            limit: Maximum number of results

        Returns:
            List of query results
        """
        pass

    @abc.abstractmethod
    async def search_by_id(
        self, knowledge_id: str, limit: int = 10
    ) -> List[QueryResult]:
        """
        Search for knowledge items similar to a given knowledge item.

        Args:
            knowledge_id: ID of the knowledge item
            limit: Maximum number of results

        Returns:
            List of query results
        """
        pass


class MetadataFilter(abc.ABC):
    """
    Interface for metadata filters.

    Metadata filters filter knowledge items based on their metadata.
    """

    @abc.abstractmethod
    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches the filter
        """
        pass


class KnowledgeRetriever(abc.ABC):
    """
    Interface for knowledge retrievers.

    Knowledge retrievers retrieve knowledge from the knowledge repository,
    including similarity search and filtering.
    """

    @abc.abstractmethod
    async def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        """
        Get a knowledge item by ID.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            The knowledge item, or None if not found
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
        """
        pass

    @abc.abstractmethod
    async def search_knowledge(self, query: str, limit: int = 10) -> List[QueryResult]:
        """
        Search for knowledge items by similarity to a query.

        Args:
            query: Query string
            limit: Maximum number of results

        Returns:
            List of query results
        """
        pass

    @abc.abstractmethod
    async def filter_knowledge(
        self, filter: MetadataFilter, limit: Optional[int] = None
    ) -> List[KnowledgeItem]:
        """
        Filter knowledge items based on metadata.

        Args:
            filter: Metadata filter
            limit: Maximum number of results

        Returns:
            List of knowledge items matching the filter
        """
        pass

    @abc.abstractmethod
    async def search_and_filter(
        self, query: str, filter: MetadataFilter, limit: int = 10
    ) -> List[QueryResult]:
        """
        Search for knowledge items and filter the results.

        Args:
            query: Query string
            filter: Metadata filter
            limit: Maximum number of results

        Returns:
            List of query results
        """
        pass
