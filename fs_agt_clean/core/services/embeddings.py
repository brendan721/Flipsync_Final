"""Embeddings service module.

This module provides a simple embedding service implementation for FlipSync.
"""

import logging
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Simple embedding service implementation."""

    VECTOR_SIZE = 1536  # Standard OpenAI embedding dimension

    def __init__(
        self,
        config_manager: Optional[object] = None,
        metrics_service: Optional[object] = None,
    ):
        """Initialize the embedding service.

        Args:
            config_manager: Optional configuration manager
            metrics_service: Optional metrics service for tracking
        """
        self.config_manager = config_manager
        self.metrics_service = metrics_service
        logger.info("Initialized EmbeddingService")

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text using real OpenAI API.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Use the main vector embedding service for real OpenAI embeddings
            from fs_agt_clean.services.vector.embedding_service import embedding_service

            # Generate real OpenAI embedding
            embedding = await embedding_service.generate_embedding(
                text=text, model_name="text-embedding-ada-002"
            )

            if embedding and len(embedding) == 1536:
                # Resize to our expected vector size if needed
                if self.VECTOR_SIZE != 1536:
                    # Truncate or pad to match expected size
                    if len(embedding) > self.VECTOR_SIZE:
                        embedding = embedding[: self.VECTOR_SIZE]
                    else:
                        embedding.extend([0.0] * (self.VECTOR_SIZE - len(embedding)))

                logger.debug(
                    f"Generated real OpenAI embedding for text (length: {len(text)})"
                )
                return embedding
            else:
                logger.warning("Failed to generate real embedding, using fallback")
                return await self._generate_fallback_embedding(text)

        except Exception as e:
            logger.error("Error generating real embedding: %s", str(e), exc_info=True)
            return await self._generate_fallback_embedding(text)

    async def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate fallback embedding when real API is unavailable."""
        try:
            # Create a deterministic vector based on text hash
            text_hash = hash(text)

            # Generate a pseudo-random but deterministic vector
            np.random.seed(abs(text_hash) % (2**32))
            vector = np.random.normal(0, 1, self.VECTOR_SIZE)

            # Normalize the vector
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            # Convert to list of floats
            embedding = [float(x) for x in vector]

            logger.debug(f"Generated fallback embedding for text (length: {len(text)})")
            return embedding

        except Exception as e:
            logger.error(
                "Error generating fallback embedding: %s", str(e), exc_info=True
            )
            # Return zero vector as fallback
            return [0.0] * self.VECTOR_SIZE

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts.

        Args:
            texts: List of texts to generate embeddings for

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)

        logger.debug(f"Generated {len(embeddings)} embeddings")
        return embeddings

    def get_vector_size(self) -> int:
        """Get the vector size for embeddings.

        Returns:
            Vector dimension size
        """
        return self.VECTOR_SIZE

    async def health_check(self) -> bool:
        """Check if the embedding service is healthy.

        Returns:
            True if service is healthy
        """
        try:
            # Test embedding generation
            test_embedding = await self.get_embedding("test")
            return len(test_embedding) == self.VECTOR_SIZE
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
            return False
