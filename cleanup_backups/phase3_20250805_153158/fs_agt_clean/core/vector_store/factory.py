"""
Vector Store Factory Module

This module provides factory methods for creating and configuring vector stores
for the FlipSync agentic system. It handles the vector_store=None issue by
providing properly configured vector store instances.
"""

import os
import logging
from typing import Optional

from fs_agt_clean.core.vector_store.models import (
    VectorDistanceMetric,
    VectorStoreConfig,
)
from fs_agt_clean.core.vector_store.providers.qdrant import QdrantVectorStore

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """Factory for creating vector store instances"""

    _instance: Optional["VectorStoreFactory"] = None
    _vector_store: Optional[QdrantVectorStore] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def get_vector_store(
        cls, store_id: str = "flipsync-vectors"
    ) -> Optional[QdrantVectorStore]:
        """Get or create a vector store instance

        Args:
            store_id: Identifier for the vector store collection

        Returns:
            QdrantVectorStore instance or None if initialization fails
        """
        if cls._vector_store is not None:
            return cls._vector_store

        try:
            # Create vector store configuration with production server settings
            config = VectorStoreConfig(
                store_id=store_id,
                dimension=1536,  # Standard OpenAI embedding dimension
                distance_metric=VectorDistanceMetric.COSINE,
                host=os.getenv("QDRANT_HOST", "174.138.77.110"),  # Production server
                port=int(os.getenv("QDRANT_PORT", "6333")),
                additional_config={
                    "timeout": 10.0,
                    "prefer_grpc": False,
                },  # HTTP mode for better compatibility
            )

            # Create and initialize vector store
            vector_store = QdrantVectorStore(config)
            success = await vector_store.initialize()

            if success:
                cls._vector_store = vector_store
                logger.info(f"Vector store initialized successfully: {store_id}")
                return vector_store
            else:
                logger.warning("Vector store initialization returned False")
                return None

        except Exception as e:
            logger.warning(f"Failed to initialize vector store: {e}")
            logger.info("Agents will operate without vector store functionality")
            return None

    @classmethod
    async def create_agent_vector_store(
        cls, agent_id: str
    ) -> Optional[QdrantVectorStore]:
        """Create a vector store instance for a specific agent

        Args:
            agent_id: ID of the agent requesting the vector store

        Returns:
            QdrantVectorStore instance or None if initialization fails
        """
        store_id = f"flipsync-{agent_id}-vectors"
        return await cls.get_vector_store(store_id)

    @classmethod
    def reset(cls):
        """Reset the factory (for testing purposes)"""
        cls._vector_store = None
        cls._instance = None


# Convenience functions for backward compatibility
async def get_vector_store(
    store_id: str = "flipsync-vectors",
) -> Optional[QdrantVectorStore]:
    """Get a vector store instance

    Args:
        store_id: Identifier for the vector store collection

    Returns:
        QdrantVectorStore instance or None if initialization fails
    """
    factory = VectorStoreFactory()
    return await factory.get_vector_store(store_id)


async def create_agent_vector_store(agent_id: str) -> Optional[QdrantVectorStore]:
    """Create a vector store instance for a specific agent

    Args:
        agent_id: ID of the agent requesting the vector store

    Returns:
        QdrantVectorStore instance or None if initialization fails
    """
    factory = VectorStoreFactory()
    return await factory.create_agent_vector_store(agent_id)


class MockVectorStore:
    """Mock vector store for environments where Qdrant is not available"""

    def __init__(self, store_id: str = "mock-vectors"):
        self.store_id = store_id
        self.vectors = {}
        self.metadata = {}
        self._next_id = 1
        logger.info(f"Initialized MockVectorStore: {store_id}")

    async def initialize(self):
        """Initialize the mock vector store"""

    async def add_vectors(self, vectors, metadatas=None):
        """Add vectors to the mock store"""
        ids = []
        for i, vector in enumerate(vectors):
            vector_id = str(self._next_id)
            self.vectors[vector_id] = vector
            if metadatas and i < len(metadatas):
                self.metadata[vector_id] = metadatas[i]
            ids.append(vector_id)
            self._next_id += 1
        return ids

    async def search_by_vector(self, vector, limit=5):
        """Search for similar vectors (mock implementation)"""
        # Return mock results
        results = []
        for i, (vid, stored_vector) in enumerate(list(self.vectors.items())[:limit]):
            result = type(
                "SearchResult",
                (),
                {
                    "id": vid,
                    "score": 0.9 - (i * 0.1),  # Mock decreasing scores
                    "metadata": self.metadata.get(vid, {}),
                    "vector": stored_vector,
                },
            )()
            results.append(result)
        return results

    async def delete_collection(self):
        """Delete the mock collection"""
        self.vectors.clear()
        self.metadata.clear()


async def get_vector_store_or_mock(store_id: str = "flipsync-vectors"):
    """Get a vector store instance or return a mock if Qdrant is unavailable

    Args:
        store_id: Identifier for the vector store collection

    Returns:
        QdrantVectorStore instance or MockVectorStore if Qdrant is unavailable
    """
    try:
        # Try to get real vector store with short timeout
        vector_store = await get_vector_store(store_id)
        if vector_store is not None:
            return vector_store
    except Exception as e:
        logger.warning(f"Vector store initialization failed: {e}")

    # Return mock vector store
    logger.info("Using MockVectorStore for development/testing")
    return MockVectorStore(store_id)
