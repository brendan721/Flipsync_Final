"""
Vector Database Repository for FlipSync.

This repository provides data access patterns for vector operations,
maintaining consistency with the existing repository pattern.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

# Vector repository doesn't use traditional database tables
from fs_agt_clean.core.config.vector_config import (
    VectorCollectionType,
    vector_db_manager,
)

logger = logging.getLogger(__name__)


class VectorEmbedding:
    """Vector embedding model for database operations."""

    def __init__(
        self,
        id: str,
        entity_id: str,
        entity_type: str,
        vector: List[float],
        metadata: Dict[str, Any],
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.vector = vector
        self.metadata = metadata
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "vector_dimension": len(self.vector),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class VectorEmbeddingRepository:
    """Repository for vector embedding operations."""

    def __init__(self):
        """Initialize the vector embedding repository."""
        self.model_class = VectorEmbedding

        # Collection type mapping
        self.collection_mapping = {
            "product": VectorCollectionType.PRODUCTS,
            "category": VectorCollectionType.CATEGORIES,
            "listing": VectorCollectionType.LISTINGS,
            "market_trend": VectorCollectionType.MARKET_TRENDS,
        }

        logger.info("Vector Embedding Repository initialized")

    async def create_embedding(
        self,
        entity_id: str,
        entity_type: str,
        vector: List[float],
        metadata: Dict[str, Any],
    ) -> Optional[VectorEmbedding]:
        """
        Create a new vector embedding.

        Args:
            entity_id: ID of the entity being embedded
            entity_type: Type of entity (product, category, etc.)
            vector: Vector embedding
            metadata: Additional metadata

        Returns:
            Created VectorEmbedding or None if failed
        """
        try:
            # Generate unique ID for the embedding
            embedding_id = str(uuid4())

            # Create embedding object
            embedding = VectorEmbedding(
                id=embedding_id,
                entity_id=entity_id,
                entity_type=entity_type,
                vector=vector,
                metadata=metadata,
            )

            # Store in vector database if available
            if vector_db_manager.is_available():
                success = await self._store_in_vector_db(embedding)
                if not success:
                    logger.warning(
                        f"Failed to store embedding in vector DB: {embedding_id}"
                    )

            # Store in traditional database (if implemented)
            # For now, we'll just return the embedding object
            logger.info(
                f"Created vector embedding: {embedding_id} for {entity_type}:{entity_id}"
            )
            return embedding

        except Exception as e:
            logger.error(f"Error creating vector embedding: {e}")
            return None

    async def _store_in_vector_db(self, embedding: VectorEmbedding) -> bool:
        """Store embedding in Qdrant vector database."""
        try:
            # Get collection type
            collection_type = self.collection_mapping.get(embedding.entity_type)
            if not collection_type:
                logger.error(f"Unknown entity type: {embedding.entity_type}")
                return False

            # Prepare payload
            payload = {
                "embedding_id": embedding.id,
                "entity_id": embedding.entity_id,
                "entity_type": embedding.entity_type,
                "created_at": embedding.created_at.isoformat(),
                "updated_at": embedding.updated_at.isoformat(),
                **embedding.metadata,
            }

            # Store in vector database
            from qdrant_client.http.models import PointStruct

            collection_name = vector_db_manager.get_collection_name(collection_type)

            point = PointStruct(
                id=embedding.id, vector=embedding.vector, payload=payload
            )

            vector_db_manager.client.upsert(
                collection_name=collection_name, points=[point]
            )

            logger.debug(f"Stored embedding in vector DB: {embedding.id}")
            return True

        except Exception as e:
            logger.error(f"Error storing embedding in vector DB: {e}")
            return False

    async def get_embedding_by_id(self, embedding_id: str) -> Optional[VectorEmbedding]:
        """Get embedding by ID."""
        if not vector_db_manager.is_available():
            logger.warning("Vector database not available")
            return None

        try:
            # Search across all collections
            for entity_type, collection_type in self.collection_mapping.items():
                collection_name = vector_db_manager.get_collection_name(collection_type)

                try:
                    points = vector_db_manager.client.retrieve(
                        collection_name=collection_name,
                        ids=[embedding_id],
                        with_payload=True,
                        with_vectors=True,
                    )

                    if points:
                        point = points[0]
                        return VectorEmbedding(
                            id=point.id,
                            entity_id=point.payload.get("entity_id"),
                            entity_type=point.payload.get("entity_type"),
                            vector=point.vector,
                            metadata={
                                k: v
                                for k, v in point.payload.items()
                                if k
                                not in [
                                    "embedding_id",
                                    "entity_id",
                                    "entity_type",
                                    "created_at",
                                    "updated_at",
                                ]
                            },
                            created_at=datetime.fromisoformat(
                                point.payload.get("created_at")
                            ),
                            updated_at=datetime.fromisoformat(
                                point.payload.get("updated_at")
                            ),
                        )
                except Exception:
                    continue

            logger.warning(f"Embedding not found: {embedding_id}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving embedding: {e}")
            return None

    async def get_embeddings_by_entity(
        self, entity_id: str, entity_type: str
    ) -> List[VectorEmbedding]:
        """Get all embeddings for a specific entity."""
        if not vector_db_manager.is_available():
            logger.warning("Vector database not available")
            return []

        try:
            collection_type = self.collection_mapping.get(entity_type)
            if not collection_type:
                logger.error(f"Unknown entity type: {entity_type}")
                return []

            collection_name = vector_db_manager.get_collection_name(collection_type)

            # Search with filter
            search_results = vector_db_manager.client.scroll(
                collection_name=collection_name,
                scroll_filter={
                    "must": [{"key": "entity_id", "match": {"value": entity_id}}]
                },
                with_payload=True,
                with_vectors=True,
            )

            embeddings = []
            for point in search_results[0]:  # scroll returns (points, next_page_offset)
                embedding = VectorEmbedding(
                    id=point.id,
                    entity_id=point.payload.get("entity_id"),
                    entity_type=point.payload.get("entity_type"),
                    vector=point.vector,
                    metadata={
                        k: v
                        for k, v in point.payload.items()
                        if k
                        not in [
                            "embedding_id",
                            "entity_id",
                            "entity_type",
                            "created_at",
                            "updated_at",
                        ]
                    },
                    created_at=datetime.fromisoformat(point.payload.get("created_at")),
                    updated_at=datetime.fromisoformat(point.payload.get("updated_at")),
                )
                embeddings.append(embedding)

            logger.info(
                f"Found {len(embeddings)} embeddings for {entity_type}:{entity_id}"
            )
            return embeddings

        except Exception as e:
            logger.error(f"Error retrieving embeddings for entity: {e}")
            return []

    async def search_similar_embeddings(
        self,
        query_vector: List[float],
        entity_type: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[VectorEmbedding, float]]:
        """
        Search for similar embeddings.

        Args:
            query_vector: Query vector
            entity_type: Type of entities to search
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Optional filters

        Returns:
            List of (embedding, score) tuples
        """
        if not vector_db_manager.is_available():
            logger.warning("Vector database not available")
            return []

        try:
            collection_type = self.collection_mapping.get(entity_type)
            if not collection_type:
                logger.error(f"Unknown entity type: {entity_type}")
                return []

            collection_name = vector_db_manager.get_collection_name(collection_type)

            # Perform similarity search
            search_results = vector_db_manager.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filters,
                with_payload=True,
                with_vectors=True,
            )

            results = []
            for result in search_results:
                embedding = VectorEmbedding(
                    id=result.id,
                    entity_id=result.payload.get("entity_id"),
                    entity_type=result.payload.get("entity_type"),
                    vector=result.vector,
                    metadata={
                        k: v
                        for k, v in result.payload.items()
                        if k
                        not in [
                            "embedding_id",
                            "entity_id",
                            "entity_type",
                            "created_at",
                            "updated_at",
                        ]
                    },
                    created_at=datetime.fromisoformat(result.payload.get("created_at")),
                    updated_at=datetime.fromisoformat(result.payload.get("updated_at")),
                )
                results.append((embedding, result.score))

            logger.info(f"Found {len(results)} similar embeddings for {entity_type}")
            return results

        except Exception as e:
            logger.error(f"Error searching similar embeddings: {e}")
            return []

    async def delete_embedding(self, embedding_id: str) -> bool:
        """Delete an embedding by ID."""
        if not vector_db_manager.is_available():
            logger.warning("Vector database not available")
            return False

        try:
            # Delete from all collections (since we don't know which one)
            deleted = False
            for entity_type, collection_type in self.collection_mapping.items():
                collection_name = vector_db_manager.get_collection_name(collection_type)

                try:
                    vector_db_manager.client.delete(
                        collection_name=collection_name, points_selector=[embedding_id]
                    )
                    deleted = True
                    logger.info(f"Deleted embedding: {embedding_id}")
                    break
                except Exception:
                    continue

            return deleted

        except Exception as e:
            logger.error(f"Error deleting embedding: {e}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all vector collections."""
        if not vector_db_manager.is_available():
            return {"error": "Vector database not available"}

        try:
            stats = {}

            for entity_type, collection_type in self.collection_mapping.items():
                collection_name = vector_db_manager.get_collection_name(collection_type)

                try:
                    collection_info = vector_db_manager.client.get_collection(
                        collection_name
                    )
                    stats[entity_type] = {
                        "collection_name": collection_name,
                        "vectors_count": collection_info.vectors_count,
                        "points_count": collection_info.points_count,
                        "status": "healthy",
                    }
                except Exception as e:
                    stats[entity_type] = {
                        "collection_name": collection_name,
                        "status": "error",
                        "error": str(e),
                    }

            return stats

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}


# Global repository instance
vector_embedding_repository = VectorEmbeddingRepository()
