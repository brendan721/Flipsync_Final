"""
Vector storage for knowledge items.

This module provides interfaces and implementations for storing and retrieving
vector representations of knowledge items, enabling similarity search and
other vector-based operations.
"""

import abc
import heapq
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

import numpy as np

from fs_agt_clean.core.monitoring import get_logger


class VectorStorageError(Exception):
    """Base exception for vector storage errors."""

    def __init__(
        self,
        message: str,
        item_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize a vector storage error.

        Args:
            message: Error message
            item_id: ID of the item related to the error
            cause: Original exception that caused this error
        """
        self.message = message
        self.item_id = item_id
        self.cause = cause

        # Create a detailed error message
        detailed_message = message
        if item_id:
            detailed_message += f" (item_id: {item_id})"
        if cause:
            detailed_message += f" - caused by: {str(cause)}"

        super().__init__(detailed_message)


class VectorStorage(abc.ABC):
    """
    Interface for vector storage.

    Vector storage stores and retrieves vector representations of items,
    enabling similarity search and other vector-based operations.
    """

    @abc.abstractmethod
    async def add_vector(
        self,
        item_id: str,
        vector: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a vector to the storage.

        Args:
            item_id: ID of the item
            vector: Vector representation of the item
            metadata: Additional metadata about the item

        Raises:
            VectorStorageError: If the vector cannot be added
        """
        pass

    @abc.abstractmethod
    async def update_vector(
        self,
        item_id: str,
        vector: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update a vector in the storage.

        Args:
            item_id: ID of the item
            vector: New vector representation of the item
            metadata: New or updated metadata about the item

        Raises:
            VectorStorageError: If the vector cannot be updated
        """
        pass

    @abc.abstractmethod
    async def get_vector(self, item_id: str) -> Optional[np.ndarray]:
        """
        Get a vector by item ID.

        Args:
            item_id: ID of the item

        Returns:
            Vector representation of the item, or None if not found

        Raises:
            VectorStorageError: If the vector cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def delete_vector(self, item_id: str) -> bool:
        """
        Delete a vector from the storage.

        Args:
            item_id: ID of the item

        Returns:
            True if the vector was deleted

        Raises:
            VectorStorageError: If the vector cannot be deleted
        """
        pass

    @abc.abstractmethod
    async def get_metadata(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an item.

        Args:
            item_id: ID of the item

        Returns:
            Metadata for the item, or None if not found

        Raises:
            VectorStorageError: If the metadata cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def update_metadata(self, item_id: str, metadata: Dict[str, Any]) -> None:
        """
        Update metadata for an item.

        Args:
            item_id: ID of the item
            metadata: New or updated metadata

        Raises:
            VectorStorageError: If the metadata cannot be updated
        """
        pass

    @abc.abstractmethod
    async def search_by_vector(
        self, query_vector: np.ndarray, limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search for items by similarity to a query vector.

        Args:
            query_vector: Query vector
            limit: Maximum number of results

        Returns:
            List of (item_id, similarity score) tuples

        Raises:
            VectorStorageError: If the search cannot be performed
        """
        pass

    @abc.abstractmethod
    async def search_by_id(
        self, item_id: str, limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search for items similar to a given item.

        Args:
            item_id: ID of the item
            limit: Maximum number of results

        Returns:
            List of (item_id, similarity score) tuples

        Raises:
            VectorStorageError: If the search cannot be performed
        """
        pass

    @abc.abstractmethod
    async def get_all_ids(self) -> List[str]:
        """
        Get all item IDs in the storage.

        Returns:
            List of all item IDs

        Raises:
            VectorStorageError: If the IDs cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def get_count(self) -> int:
        """
        Get the number of items in the storage.

        Returns:
            Number of items

        Raises:
            VectorStorageError: If the count cannot be retrieved
        """
        pass

    @abc.abstractmethod
    async def clear(self) -> None:
        """
        Clear all items from the storage.

        Raises:
            VectorStorageError: If the storage cannot be cleared
        """
        pass


class InMemoryVectorStorage(VectorStorage):
    """
    In-memory implementation of vector storage.

    This implementation stores vectors and metadata in memory, providing
    efficient similarity search using cosine similarity.
    """

    def __init__(self, storage_id: str):
        """
        Initialize in-memory vector storage.

        Args:
            storage_id: Unique identifier for this storage
        """
        self.storage_id = storage_id
        self.logger = get_logger(f"vector_storage.{storage_id}")

        # Initialize storage
        self.vectors: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    async def add_vector(
        self,
        item_id: str,
        vector: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a vector to the storage.

        Args:
            item_id: ID of the item
            vector: Vector representation of the item
            metadata: Additional metadata about the item

        Raises:
            VectorStorageError: If the vector cannot be added
        """
        try:
            # Check if the item already exists
            if item_id in self.vectors:
                raise VectorStorageError(
                    f"Item already exists: {item_id}", item_id=item_id
                )

            # Normalize the vector for cosine similarity
            normalized_vector = self._normalize_vector(vector)

            # Store the vector and metadata
            self.vectors[item_id] = normalized_vector
            self.metadata[item_id] = metadata or {}

            self.logger.debug(f"Added vector for item: {item_id}")
        except VectorStorageError:
            # Re-raise vector storage errors
            raise
        except Exception as e:
            error_msg = f"Failed to add vector for item {item_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, item_id=item_id, cause=e)

    async def update_vector(
        self,
        item_id: str,
        vector: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update a vector in the storage.

        Args:
            item_id: ID of the item
            vector: New vector representation of the item
            metadata: New or updated metadata about the item

        Raises:
            VectorStorageError: If the vector cannot be updated
        """
        try:
            # Check if the item exists
            if item_id not in self.vectors:
                raise VectorStorageError(f"Item not found: {item_id}", item_id=item_id)

            # Normalize the vector for cosine similarity
            normalized_vector = self._normalize_vector(vector)

            # Update the vector
            self.vectors[item_id] = normalized_vector

            # Update the metadata if provided
            if metadata is not None:
                self.metadata[item_id] = metadata

            self.logger.debug(f"Updated vector for item: {item_id}")
        except VectorStorageError:
            # Re-raise vector storage errors
            raise
        except Exception as e:
            error_msg = f"Failed to update vector for item {item_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, item_id=item_id, cause=e)

    async def get_vector(self, item_id: str) -> Optional[np.ndarray]:
        """
        Get a vector by item ID.

        Args:
            item_id: ID of the item

        Returns:
            Vector representation of the item, or None if not found

        Raises:
            VectorStorageError: If the vector cannot be retrieved
        """
        try:
            # Return the vector if it exists
            return self.vectors.get(item_id)
        except Exception as e:
            error_msg = f"Failed to get vector for item {item_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, item_id=item_id, cause=e)

    async def delete_vector(self, item_id: str) -> bool:
        """
        Delete a vector from the storage.

        Args:
            item_id: ID of the item

        Returns:
            True if the vector was deleted

        Raises:
            VectorStorageError: If the vector cannot be deleted
        """
        try:
            # Check if the item exists
            if item_id not in self.vectors:
                return False

            # Delete the vector and metadata
            del self.vectors[item_id]
            del self.metadata[item_id]

            self.logger.debug(f"Deleted vector for item: {item_id}")
            return True
        except Exception as e:
            error_msg = f"Failed to delete vector for item {item_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, item_id=item_id, cause=e)

    async def get_metadata(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an item.

        Args:
            item_id: ID of the item

        Returns:
            Metadata for the item, or None if not found

        Raises:
            VectorStorageError: If the metadata cannot be retrieved
        """
        try:
            # Return the metadata if it exists
            return self.metadata.get(item_id)
        except Exception as e:
            error_msg = f"Failed to get metadata for item {item_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, item_id=item_id, cause=e)

    async def update_metadata(self, item_id: str, metadata: Dict[str, Any]) -> None:
        """
        Update metadata for an item.

        Args:
            item_id: ID of the item
            metadata: New or updated metadata

        Raises:
            VectorStorageError: If the metadata cannot be updated
        """
        try:
            # Check if the item exists
            if item_id not in self.vectors:
                raise VectorStorageError(f"Item not found: {item_id}", item_id=item_id)

            # Update the metadata
            self.metadata[item_id] = metadata

            self.logger.debug(f"Updated metadata for item: {item_id}")
        except VectorStorageError:
            # Re-raise vector storage errors
            raise
        except Exception as e:
            error_msg = f"Failed to update metadata for item {item_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, item_id=item_id, cause=e)

    async def search_by_vector(
        self, query_vector: np.ndarray, limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search for items by similarity to a query vector.

        Args:
            query_vector: Query vector
            limit: Maximum number of results

        Returns:
            List of (item_id, similarity score) tuples

        Raises:
            VectorStorageError: If the search cannot be performed
        """
        try:
            # Normalize the query vector
            normalized_query = self._normalize_vector(query_vector)

            # Calculate similarity scores
            scores = []
            for item_id, vector in self.vectors.items():
                similarity = self._cosine_similarity(normalized_query, vector)
                scores.append((item_id, similarity))

            # Sort by similarity (highest first) and limit results
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:limit]
        except Exception as e:
            error_msg = f"Failed to search by vector: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, cause=e)

    async def search_by_id(
        self, item_id: str, limit: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search for items similar to a given item.

        Args:
            item_id: ID of the item
            limit: Maximum number of results

        Returns:
            List of (item_id, similarity score) tuples

        Raises:
            VectorStorageError: If the search cannot be performed
        """
        try:
            # Check if the item exists
            if item_id not in self.vectors:
                raise VectorStorageError(f"Item not found: {item_id}", item_id=item_id)

            # Get the vector for the item
            vector = self.vectors[item_id]

            # Search by vector
            results = await self.search_by_vector(vector, limit + 1)

            # Remove the item itself from the results
            return [result for result in results if result[0] != item_id][:limit]
        except VectorStorageError:
            # Re-raise vector storage errors
            raise
        except Exception as e:
            error_msg = f"Failed to search by ID {item_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, item_id=item_id, cause=e)

    async def get_all_ids(self) -> List[str]:
        """
        Get all item IDs in the storage.

        Returns:
            List of all item IDs

        Raises:
            VectorStorageError: If the IDs cannot be retrieved
        """
        try:
            return list(self.vectors.keys())
        except Exception as e:
            error_msg = f"Failed to get all IDs: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, cause=e)

    async def get_count(self) -> int:
        """
        Get the number of items in the storage.

        Returns:
            Number of items

        Raises:
            VectorStorageError: If the count cannot be retrieved
        """
        try:
            return len(self.vectors)
        except Exception as e:
            error_msg = f"Failed to get count: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, cause=e)

    async def clear(self) -> None:
        """
        Clear all items from the storage.

        Raises:
            VectorStorageError: If the storage cannot be cleared
        """
        try:
            self.vectors.clear()
            self.metadata.clear()
            self.logger.debug("Cleared vector storage")
        except Exception as e:
            error_msg = f"Failed to clear storage: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise VectorStorageError(error_msg, cause=e)

    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """
        Normalize a vector for cosine similarity.

        Args:
            vector: Vector to normalize

        Returns:
            Normalized vector
        """
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Cosine similarity
        """
        return float(np.dot(a, b))
