"""Vector store protocol definitions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from .models import CollectionInfo, ProductMetadata, SearchResult, VectorStoreConfig


class VectorStoreProtocol(ABC):
    """Protocol for vector store implementations."""

    def __init__(self, config: VectorStoreConfig):
        """Initialize the vector store with configuration."""
        self.config = config

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the vector store connection.

        Returns:
            True if initialization was successful
        """
        pass

    @abstractmethod
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection.

        Args:
            collection_name: Name of the collection
            dimension: Vector dimension

        Returns:
            True if creation was successful
        """
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            True if deletion was successful
        """
        pass

    @abstractmethod
    async def upsert_products(
        self,
        products: Sequence[ProductMetadata],
        vectors: Sequence[List[float]],
        batch_size: int = 100,
    ) -> bool:
        """Upsert products with their vectors.

        Args:
            products: Product metadata
            vectors: Product vectors
            batch_size: Batch size for processing

        Returns:
            True if upsert was successful
        """
        pass

    @abstractmethod
    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
    ) -> List[SearchResult]:
        """Search for similar vectors.

        Args:
            query_vector: Query vector
            limit: Maximum number of results
            filter_conditions: Optional filters
            score_threshold: Minimum similarity score

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def delete_vectors(self, ids: List[str]) -> bool:
        """Delete vectors by ID.

        Args:
            ids: List of vector IDs to delete

        Returns:
            True if deletion was successful
        """
        pass

    @abstractmethod
    async def get_collection_info(self) -> CollectionInfo:
        """Get collection information.

        Returns:
            Collection information
        """
        pass

    @abstractmethod
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Collection statistics
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the vector store connection."""
        pass
