"""
Vector Embedding Service for FlipSync.

This service provides vector embedding generation and management for semantic search,
product recommendations, and market analysis.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

from fs_agt_clean.core.ai.simple_llm_client import (
    ModelProvider,
    ModelType,
    SimpleLLMClient,
)
from fs_agt_clean.core.ai.simple_llm_client import SimpleLLMConfig as LLMConfig
from fs_agt_clean.core.config.vector_config import (
    VectorCollectionType,
    vector_db_manager,
)

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Embedding model configuration and metadata."""

    def __init__(
        self,
        name: str,
        dimension: int,
        max_tokens: int,
        cost_per_1k_tokens: float = 0.0,
    ):
        self.name = name
        self.dimension = dimension
        self.max_tokens = max_tokens
        self.cost_per_1k_tokens = cost_per_1k_tokens


class VectorEmbeddingService:
    """
    Vector embedding service for semantic operations.

    This service provides:
    - Text embedding generation using various models
    - Vector storage and retrieval in Qdrant
    - Semantic similarity search
    - Product and category embeddings
    """

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize the vector embedding service."""
        self.llm_config = llm_config or LLMConfig(
            provider=ModelProvider.OLLAMA, model_type=ModelType.GEMMA3_4B
        )

        # Available embedding models
        self.embedding_models = {
            "text-embedding-ada-002": EmbeddingModel(
                name="text-embedding-ada-002",
                dimension=1536,
                max_tokens=8191,
                cost_per_1k_tokens=0.0001,
            ),
            "local-embedding": EmbeddingModel(
                name="local-embedding",
                dimension=384,  # Sentence transformers default
                max_tokens=512,
                cost_per_1k_tokens=0.0,
            ),
        }

        self.default_model = "text-embedding-ada-002"
        self.embedding_cache = {}  # Simple in-memory cache

        logger.info("Vector Embedding Service initialized")

    async def generate_embedding(
        self,
        text: str,
        model_name: Optional[str] = None,
        cache_key: Optional[str] = None,
    ) -> Optional[List[float]]:
        """
        Generate vector embedding for text.

        Args:
            text: Text to embed
            model_name: Embedding model to use
            cache_key: Optional cache key for the embedding

        Returns:
            Vector embedding as list of floats
        """
        model_name = model_name or self.default_model

        # Generate cache key if not provided
        if cache_key is None:
            cache_key = self._generate_cache_key(text, model_name)

        # Check cache first
        if cache_key in self.embedding_cache:
            logger.debug(f"Using cached embedding for: {cache_key[:16]}...")
            return self.embedding_cache[cache_key]

        try:
            # Generate embedding based on model
            if model_name == "text-embedding-ada-002":
                embedding = await self._generate_openai_embedding(text)
            else:
                embedding = await self._generate_local_embedding(text)

            # Cache the result
            if embedding:
                self.embedding_cache[cache_key] = embedding
                logger.debug(
                    f"Generated and cached embedding: {len(embedding)} dimensions"
                )

            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    async def _generate_openai_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using real OpenAI API."""
        try:
            import openai
            import os
            from fs_agt_clean.core.monitoring.cost_tracker import (
                record_ai_cost,
                CostCategory,
            )

            # Get OpenAI API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not configured, using mock embedding")
                return await self._generate_mock_embedding(text, 1536)

            # Initialize OpenAI client
            client = openai.AsyncOpenAI(api_key=api_key)

            # Record start time for cost tracking
            start_time = time.time()

            # Generate real OpenAI embedding
            response = await client.embeddings.create(
                model="text-embedding-ada-002", input=text, encoding_format="float"
            )

            # Extract embedding from response
            embedding = response.data[0].embedding

            # Calculate response time and cost
            response_time = time.time() - start_time
            tokens_used = response.usage.total_tokens
            cost = tokens_used * 0.0001 / 1000  # $0.0001 per 1K tokens

            # Record AI cost for embedding generation
            try:
                await record_ai_cost(
                    category=CostCategory.EMBEDDINGS,
                    cost=cost,
                    tokens_used=tokens_used,
                    model="text-embedding-ada-002",
                    operation="embedding_generation",
                    metadata={
                        "text_length": len(text),
                        "embedding_dimension": len(embedding),
                        "response_time": response_time,
                    },
                )
            except Exception as cost_error:
                logger.warning(f"Failed to record embedding cost: {cost_error}")

            logger.info(
                f"Generated real OpenAI embedding: {len(embedding)} dimensions, "
                f"cost: ${cost:.6f}, time: {response_time:.2f}s"
            )

            return embedding

        except ImportError:
            logger.warning("OpenAI library not available, using mock embedding")
            return await self._generate_mock_embedding(text, 1536)
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            logger.warning("Falling back to mock embedding")
            return await self._generate_mock_embedding(text, 1536)

    async def _generate_local_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using local model."""
        # This would use sentence-transformers or similar
        # For now, return a mock embedding
        logger.debug("Generating local embedding (mock)")
        return await self._generate_mock_embedding(text, 384)

    async def _generate_mock_embedding(self, text: str, dimension: int) -> List[float]:
        """Generate mock embedding for testing purposes."""
        if not NUMPY_AVAILABLE:
            # Simple hash-based mock embedding
            text_hash = hashlib.md5(text.encode()).hexdigest()
            seed = int(text_hash[:8], 16)

            # Generate deterministic "embedding"
            embedding = []
            for i in range(dimension):
                seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
                embedding.append((seed % 2000 - 1000) / 1000.0)

            return embedding
        else:
            # Use numpy for better mock embeddings
            np.random.seed(hash(text) % 2**32)
            embedding = np.random.normal(0, 1, dimension)
            return embedding.tolist()

    def _generate_cache_key(self, text: str, model_name: str) -> str:
        """Generate cache key for embedding."""
        content = f"{model_name}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def embed_product(
        self,
        product_id: str,
        product_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Generate and store embedding for a product.

        Args:
            product_id: Unique product identifier
            product_data: Product information (name, description, category, etc.)
            user_id: Optional user ID for tracking

        Returns:
            True if embedding was successfully stored
        """
        try:
            # Create text representation of product
            product_text = self._create_product_text(product_data)

            # Generate embedding
            embedding = await self.generate_embedding(product_text)
            if not embedding:
                logger.error(f"Failed to generate embedding for product: {product_id}")
                return False

            # Store in vector database
            success = await self._store_vector(
                collection_type=VectorCollectionType.PRODUCTS,
                point_id=product_id,
                vector=embedding,
                payload={
                    "product_id": product_id,
                    "user_id": user_id,
                    "product_name": product_data.get("name", ""),
                    "category": product_data.get("category", ""),
                    "description": product_data.get("description", ""),
                    "price": product_data.get("price", 0),
                    "condition": product_data.get("condition", ""),
                    "marketplace": product_data.get("marketplace", ""),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "text_content": product_text,
                },
            )

            if success:
                logger.info(f"Successfully embedded product: {product_id}")
            else:
                logger.error(f"Failed to store embedding for product: {product_id}")

            return success

        except Exception as e:
            logger.error(f"Error embedding product {product_id}: {e}")
            return False

    def _create_product_text(self, product_data: Dict[str, Any]) -> str:
        """Create text representation of product for embedding."""
        text_parts = []

        # Add product name
        if product_data.get("name"):
            text_parts.append(f"Product: {product_data['name']}")

        # Add category
        if product_data.get("category"):
            text_parts.append(f"Category: {product_data['category']}")

        # Add description
        if product_data.get("description"):
            text_parts.append(f"Description: {product_data['description']}")

        # Add condition
        if product_data.get("condition"):
            text_parts.append(f"Condition: {product_data['condition']}")

        # Add brand if available
        if product_data.get("brand"):
            text_parts.append(f"Brand: {product_data['brand']}")

        # Add key features
        if product_data.get("features"):
            features = product_data["features"]
            if isinstance(features, list):
                text_parts.append(f"Features: {', '.join(features)}")
            elif isinstance(features, str):
                text_parts.append(f"Features: {features}")

        return " | ".join(text_parts)

    async def _store_vector(
        self,
        collection_type: VectorCollectionType,
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> bool:
        """Store vector in Qdrant database."""
        if not vector_db_manager.is_available():
            logger.warning("Vector database not available - skipping vector storage")
            return False

        try:
            from qdrant_client.http.models import PointStruct

            collection_name = vector_db_manager.get_collection_name(collection_type)

            # Create point
            point = PointStruct(id=point_id, vector=vector, payload=payload)

            # Upsert point
            vector_db_manager.client.upsert(
                collection_name=collection_name, points=[point]
            )

            logger.debug(f"Stored vector in collection {collection_name}: {point_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing vector: {e}")
            return False

    async def search_similar_products(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar products using semantic similarity.

        Args:
            query_text: Search query text
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Optional filters for search

        Returns:
            List of similar products with scores
        """
        if not vector_db_manager.is_available():
            logger.warning("Vector database not available - returning empty results")
            return []

        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query_text)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Search in vector database
            collection_name = vector_db_manager.get_collection_name(
                VectorCollectionType.PRODUCTS
            )

            search_results = vector_db_manager.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filters,
            )

            # Format results
            results = []
            for result in search_results:
                results.append(
                    {
                        "product_id": result.payload.get("product_id"),
                        "product_name": result.payload.get("product_name"),
                        "category": result.payload.get("category"),
                        "description": result.payload.get("description"),
                        "price": result.payload.get("price"),
                        "condition": result.payload.get("condition"),
                        "marketplace": result.payload.get("marketplace"),
                        "similarity_score": result.score,
                        "created_at": result.payload.get("created_at"),
                    }
                )

            logger.info(
                f"Found {len(results)} similar products for query: {query_text[:50]}..."
            )
            return results

        except Exception as e:
            logger.error(f"Error searching similar products: {e}")
            return []

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics."""
        stats = {
            "cache_size": len(self.embedding_cache),
            "available_models": list(self.embedding_models.keys()),
            "default_model": self.default_model,
            "vector_db_available": vector_db_manager.is_available(),
            "numpy_available": NUMPY_AVAILABLE,
        }

        # Add vector database stats if available
        if vector_db_manager.is_available():
            health_info = await vector_db_manager.health_check()
            stats["vector_db_health"] = health_info

        return stats


# Global embedding service instance
embedding_service = VectorEmbeddingService()
