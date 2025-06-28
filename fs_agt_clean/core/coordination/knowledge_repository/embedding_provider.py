"""
Embedding providers for knowledge items.

This module provides interfaces and implementations for generating vector
embeddings from knowledge items, enabling similarity search and other
vector-based operations.
"""

import abc
import hashlib
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

from fs_agt_clean.core.monitoring import get_logger


class EmbeddingError(Exception):
    """Base exception for embedding provider errors."""

    def __init__(
        self,
        message: str,
        content: Optional[Any] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize an embedding error.

        Args:
            message: Error message
            content: Content related to the error
            cause: Original exception that caused this error
        """
        self.message = message
        self.content = content
        self.cause = cause

        # Create a detailed error message
        detailed_message = message
        if content is not None:
            content_str = str(content)
            if len(content_str) > 100:
                content_str = content_str[:97] + "..."
            detailed_message += f" (content: {content_str})"
        if cause:
            detailed_message += f" - caused by: {str(cause)}"

        super().__init__(detailed_message)


class EmbeddingProvider(abc.ABC):
    """
    Interface for embedding providers.

    Embedding providers generate vector embeddings from content,
    enabling similarity search and other vector-based operations.
    """

    @abc.abstractmethod
    async def get_embedding(self, content: Any) -> np.ndarray:
        """
        Get an embedding for content.

        Args:
            content: Content to embed

        Returns:
            Vector embedding of the content

        Raises:
            EmbeddingError: If the embedding cannot be generated
        """
        pass

    @abc.abstractmethod
    async def get_embeddings(self, contents: List[Any]) -> List[np.ndarray]:
        """
        Get embeddings for multiple content items.

        Args:
            contents: Content items to embed

        Returns:
            List of vector embeddings

        Raises:
            EmbeddingError: If the embeddings cannot be generated
        """
        pass

    @abc.abstractmethod
    async def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings.

        Returns:
            Dimension of the embeddings
        """
        pass


class SimpleEmbeddingProvider(EmbeddingProvider):
    """
    Simple embedding provider using basic text processing.

    This implementation generates embeddings using a simple hash-based
    approach for demonstration purposes. In a real implementation, this
    would be replaced with a more sophisticated embedding model.
    """

    def __init__(self, provider_id: str, dimension: int = 128):
        """
        Initialize a simple embedding provider.

        Args:
            provider_id: Unique identifier for this provider
            dimension: Dimension of the embeddings
        """
        self.provider_id = provider_id
        self.dimension = dimension
        self.logger = get_logger(f"embedding_provider.{provider_id}")

    async def get_embedding(self, content: Any) -> np.ndarray:
        """
        Get an embedding for content.

        Args:
            content: Content to embed

        Returns:
            Vector embedding of the content

        Raises:
            EmbeddingError: If the embedding cannot be generated
        """
        try:
            # Convert content to string
            content_str = self._content_to_string(content)

            # Generate a deterministic embedding
            embedding = self._generate_embedding(content_str)

            return embedding
        except Exception as e:
            error_msg = f"Failed to generate embedding: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise EmbeddingError(error_msg, content=content, cause=e)

    async def get_embeddings(self, contents: List[Any]) -> List[np.ndarray]:
        """
        Get embeddings for multiple content items.

        Args:
            contents: Content items to embed

        Returns:
            List of vector embeddings

        Raises:
            EmbeddingError: If the embeddings cannot be generated
        """
        try:
            # Generate embeddings for each content item
            embeddings = []
            for content in contents:
                embedding = await self.get_embedding(content)
                embeddings.append(embedding)

            return embeddings
        except EmbeddingError:
            # Re-raise embedding errors
            raise
        except Exception as e:
            error_msg = f"Failed to generate embeddings: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise EmbeddingError(error_msg, content=contents, cause=e)

    async def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings.

        Returns:
            Dimension of the embeddings
        """
        return self.dimension

    def _content_to_string(self, content: Any) -> str:
        """
        Convert content to a string representation.

        Args:
            content: Content to convert

        Returns:
            String representation of the content
        """
        if content is None:
            return ""

        if isinstance(content, str):
            return content

        if isinstance(content, (int, float, bool)):
            return str(content)

        if isinstance(content, (list, tuple)):
            return " ".join(self._content_to_string(item) for item in content)

        if isinstance(content, dict):
            return " ".join(
                f"{self._content_to_string(key)} {self._content_to_string(value)}"
                for key, value in content.items()
            )

        # For other types, use the string representation
        return str(content)

    def _generate_embedding(self, content_str: str) -> np.ndarray:
        """
        Generate an embedding for a string.

        This is a simple hash-based approach for demonstration purposes.
        In a real implementation, this would be replaced with a more
        sophisticated embedding model.

        Args:
            content_str: String to embed

        Returns:
            Vector embedding of the string
        """
        # Normalize the string
        content_str = content_str.lower()
        content_str = re.sub(r"[^\w\s]", "", content_str)
        content_str = re.sub(r"\s+", " ", content_str).strip()

        # Generate a hash of the string
        hash_obj = hashlib.sha256(content_str.encode())
        hash_bytes = hash_obj.digest()

        # Convert the hash to a vector
        embedding = np.zeros(self.dimension, dtype=np.float32)
        for i in range(min(len(hash_bytes), self.dimension)):
            embedding[i] = float(hash_bytes[i]) / 255.0

        # Add some simple features based on the content
        words = content_str.split()
        if words:
            # Word count
            embedding[0] = min(1.0, len(words) / 100.0)

            # Average word length
            avg_word_len = sum(len(word) for word in words) / len(words)
            embedding[1] = min(1.0, avg_word_len / 10.0)

            # Unique word ratio
            unique_words = set(words)
            embedding[2] = len(unique_words) / len(words)

        # Normalize the embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding
