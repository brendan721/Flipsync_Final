"""
Qdrant Vector Store Implementation.

This module provides an implementation of the VectorStoreProtocol
using the Qdrant vector database for efficient similarity search.

Usage:
    from fs_agt_clean.core.vector_store.models import VectorStoreConfig, VectorDistanceMetric
    from fs_agt_clean.core.vector_store.providers.qdrant import QdrantVectorStore

    # Create configuration
    config = VectorStoreConfig(
        store_id="my-collection",
        dimension=1536,
        distance_metric=VectorDistanceMetric.COSINE,
        host="localhost",
        port=6333,
    )

    # Create and initialize the store
    store = QdrantVectorStore(config)
    await store.initialize()

    # Add vectors
    ids = await store.add_vectors(
        vectors=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        metadatas=[{"text": "first document"}, {"text": "second document"}]
    )

    # Search
    results = await store.search_by_vector([0.1, 0.2, 0.3], limit=5)
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np

# Import models from the models module
from fs_agt_clean.core.vector_store.models import (
    SearchQuery,
    SearchResult,
    VectorDistanceMetric,
    VectorStoreConfig,
)

# Import protocol separately
from fs_agt_clean.core.vector_store.protocol import VectorStoreProtocol

# Import Qdrant client if available
try:
    import qdrant_client
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.exceptions import UnexpectedResponse

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStoreProtocol):
    """
    Qdrant implementation of the VectorStoreProtocol.

    This implementation uses Qdrant's AsyncQdrantClient to interact with
    a Qdrant vector database instance.
    """

    def __init__(self, config: VectorStoreConfig):
        """
        Initialize the Qdrant vector store.

        Args:
            config: Configuration for the vector store
        """
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "Qdrant is not available. Please install qdrant-client: "
                "pip install qdrant-client"
            )

        self.config = config
        self.dimension = config.dimension
        self.store_id = config.store_id  # Used as collection name

        # Connection parameters
        self.host = config.host or "localhost"
        self.port = config.port or 6333
        self.api_key = config.api_key
        self.prefer_grpc = config.additional_config.get("prefer_grpc", False)
        self.timeout = config.additional_config.get("timeout", 60.0)

        # Map the distance metric
        self.distance_metric = self._map_distance_metric(config.distance_metric)

        # Client instance (initialized later)
        self.client: Optional[QdrantClient] = None

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """
        Initialize the vector store and ensure the collection exists.

        Returns:
            Success status
        """
        try:
            # Create client
            self.client = QdrantClient(
                url=self.host,
                api_key=self.api_key,
                prefer_grpc=self.prefer_grpc,
                timeout=self.timeout,
            )

            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(
                c.name == self.store_id for c in collections.collections
            )

            if not collection_exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.store_id,
                    vectors_config=models.VectorParams(
                        size=self.dimension, distance=self.distance_metric
                    ),
                )

                # Create payload indexes for efficient filtering
                await self._create_payload_indexes()

                logger.info(
                    f"Created Qdrant collection '{self.store_id}' with dimension {self.dimension}"
                )
            else:
                logger.info(f"Using existing Qdrant collection '{self.store_id}'")

            return bool(True)
        except Exception as e:
            logger.error("Error initializing Qdrant vector store: %s", e)
            return False

    async def add_vectors(
        self,
        vectors: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> List[str]:
        """
        Add vectors to the store with associated metadata.

        Args:
            vectors: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: Optional list of IDs (generated if not provided)
            batch_size: Batch size for adding vectors

        Returns:
            List of IDs for the added vectors
        """
        if not self.client:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Failed to initialize Qdrant client")

        if len(vectors) != len(metadatas):
            raise ValueError("Number of vectors and metadata must match")

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
        elif len(ids) != len(vectors):
            raise ValueError("Number of IDs and vectors must match")

        # Add default collection to metadata if not present
        for metadata in metadatas:
            if "collection" not in metadata:
                metadata["collection"] = self.store_id

        # Add timestamps if not present
        current_time = datetime.now().isoformat()
        for metadata in metadatas:
            if "created_at" not in metadata:
                metadata["created_at"] = current_time
            if "updated_at" not in metadata:
                metadata["updated_at"] = current_time

        # Prepare points
        points = []
        for i, (point_id, vector, metadata) in enumerate(zip(ids, vectors, metadatas)):
            points.append(
                models.PointStruct(id=point_id, vector=vector, payload=metadata)
            )

        # Batch upsert
        try:
            for i in range(0, len(points), batch_size):
                batch = points[i : i + batch_size]
                self.client.upsert(collection_name=self.store_id, points=batch)
                logger.debug(
                    f"Upserted {len(batch)} vectors to Qdrant collection '{self.store_id}'"
                )

            return ids
        except Exception as e:
            logger.error("Error upserting vectors to Qdrant: %s", e)
            raise

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            query: Search query parameters

        Returns:
            List of search results
        """
        if not self.client:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Failed to initialize Qdrant client")

        # Determine the search vector
        if query.query_vector is not None:
            vector = query.query_vector
        elif query.query_text is not None:
            # This would typically use an embedding model to convert text to vector
            # For this stub implementation, just use a placeholder
            logger.warning(
                "Text-to-vector conversion not implemented in QdrantVectorStore"
            )
            return []
        else:
            raise ValueError("Either query_vector or query_text must be provided")

        return await self.search_by_vector(
            vector=vector,
            limit=query.limit,
            filters=query.filters,
            include_metadata=query.include_metadata,
        )

    async def search_by_vector(
        self,
        vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[SearchResult]:
        """
        Search using a raw vector.

        Args:
            vector: Query vector
            limit: Maximum number of results
            filters: Optional filters to apply
            include_metadata: Whether to include metadata in results

        Returns:
            List of search results
        """
        if not self.client:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Failed to initialize Qdrant client")

        # Create filter if needed
        qdrant_filter = self._create_filter(filters) if filters else None

        # Search
        try:
            results = self.client.search(
                collection_name=self.store_id,
                query_vector=vector,
                limit=limit,
                query_filter=qdrant_filter,
                with_payload=include_metadata,
                with_vectors=include_metadata,
            )

            # Convert to SearchResult objects
            search_results = []
            for result in results:
                search_results.append(
                    SearchResult(
                        id=str(result.id),
                        score=result.score,
                        metadata=result.payload if include_metadata else None,
                        vector=result.vector if include_metadata else None,
                        text=(
                            result.payload.get("text")
                            if include_metadata and result.payload
                            else None
                        ),
                    )
                )

            return search_results
        except Exception as e:
            logger.error("Error searching Qdrant: %s", e)
            raise

    async def search_by_text(
        self,
        text: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[SearchResult]:
        """
        Search using text that will be converted to a vector.

        Args:
            text: Query text
            limit: Maximum number of results
            filters: Optional filters to apply
            include_metadata: Whether to include metadata in results

        Returns:
            List of search results
        """
        # This would typically use an embedding model to convert text to vector
        # For this stub implementation, just use a placeholder
        logger.warning("Text-to-vector conversion not implemented in QdrantVectorStore")
        return []

    async def delete(self, ids: List[str]) -> bool:
        """
        Delete vectors by ID.

        Args:
            ids: List of vector IDs to delete

        Returns:
            Success status
        """
        if not self.client:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Failed to initialize Qdrant client")

        try:
            # Convert IDs to the correct format
            points_selector = models.PointIdsList(points=ids)

            # Delete points
            self.client.delete(
                collection_name=self.store_id, points_selector=points_selector
            )

            return True
        except Exception as e:
            logger.error("Error deleting vectors from Qdrant: %s", e)
            return False

    async def get_by_id(self, id: str) -> Optional[Tuple[List[float], Dict[str, Any]]]:
        """
        Retrieve a vector and its metadata by ID.

        Args:
            id: Vector ID

        Returns:
            Tuple of (vector, metadata) if found, None otherwise
        """
        if not self.client:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Failed to initialize Qdrant client")

        try:
            points = self.client.retrieve(
                collection_name=self.store_id,
                ids=[id],
                with_payload=True,
                with_vectors=True,
            )

            if not points:
                return None

            point = points[0]
            return (point.vector, point.payload)
        except Exception as e:
            logger.error("Error retrieving vector from Qdrant: %s", e)
            return None

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary of statistics
        """
        if not self.client:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Failed to initialize Qdrant client")

        try:
            collection_info = self.client.get_collection(collection_name=self.store_id)

            vectors_count = collection_info.vectors_count

            # Get collection metrics
            telemetry = self.client.get_collection_metrics(
                collection_name=self.store_id
            )

            metrics = {
                "store_id": self.store_id,
                "dimension": self.dimension,
                "distance_metric": self.distance_metric,
                "total_vectors": vectors_count or 0,
            }

            # Add telemetry details
            if telemetry and telemetry.metrics:
                for metric in telemetry.metrics:
                    metrics[metric.name] = metric.value

            return metrics
        except Exception as e:
            logger.error("Error getting Qdrant stats: %s", e)
            return {"store_id": self.store_id, "error": str(e)}

    async def clear(self, collection: Optional[str] = None) -> bool:
        """
        Clear all vectors (or from a specific collection).

        Args:
            collection: Optional collection name to filter on

        Returns:
            Success status
        """
        if not self.client:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Failed to initialize Qdrant client")

        try:
            # If a specific collection is specified, only delete points from that collection
            if collection:
                # Create a filter for the collection
                filter_condition = models.FieldCondition(
                    key="collection", match=models.MatchValue(value=collection)
                )
                filter_obj = models.Filter(must=[filter_condition])

                # Delete points matching the filter
                self.client.delete(
                    collection_name=self.store_id, points_selector=filter_obj
                )
            else:
                # Delete all points by recreating the collection
                self.client.delete_collection(collection_name=self.store_id)
                await self.initialize()

            return True
        except Exception as e:
            logger.error("Error clearing Qdrant vectors: %s", e)
            return False

    async def optimize(self) -> bool:
        """
        Optimize the vector store for better performance.

        Returns:
            Success status
        """
        # Qdrant doesn't have a direct "optimize" operation, but we can
        # trigger an indexing optimization by calling this
        if not self.client:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Failed to initialize Qdrant client")

        try:
            # Trigger optimization
            self.client.update_collection(
                collection_name=self.store_id,
                optimizer_config=models.OptimizersConfig(
                    indexing_threshold=0
                ),  # Force indexing
            )

            return True
        except Exception as e:
            logger.error("Error optimizing Qdrant collection: %s", e)
            return False

    async def close(self) -> None:
        """Close the vector store and cleanup resources."""
        if self.client:
            self.client.close()
            self.client = None

    async def _create_payload_indexes(self) -> None:
        """Create payload indexes for efficient filtering."""
        if not self.client:
            await self.initialize()

        if not self.client:
            raise RuntimeError("Failed to initialize Qdrant client")

        # Common fields to index
        indexes = [
            ("collection", "keyword"),
            ("created_at", "text"),
            ("updated_at", "text"),
            ("text", "text"),
        ]

        for field_name, field_type in indexes:
            try:
                self.client.create_payload_index(
                    collection_name=self.store_id,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except Exception as e:
                logger.warning("Error creating payload index for %s: %s", field_name, e)

    def _map_distance_metric(self, metric: VectorDistanceMetric) -> str:
        """Map protocol distance metric to Qdrant distance."""
        if metric == VectorDistanceMetric.COSINE:
            return models.Distance.COSINE
        elif metric == VectorDistanceMetric.EUCLIDEAN:
            return models.Distance.EUCLID
        elif metric == VectorDistanceMetric.DOT_PRODUCT:
            return models.Distance.DOT
        else:
            logger.warning(
                "Unsupported distance metric %s, falling back to COSINE", metric
            )
            return models.Distance.COSINE

    def _create_filter(self, filters: Dict[str, Any]) -> models.Filter:
        """Convert dict filters to Qdrant Filter object."""
        conditions = []

        for key, value in filters.items():
            # Handle nested keys (e.g., "metadata.field")
            if isinstance(value, (str, int, float, bool)):
                # Simple equality match
                conditions.append(
                    models.FieldCondition(key=key, match=models.MatchValue(value=value))
                )
            elif isinstance(value, dict):
                # Range condition
                if "gt" in value or "gte" in value or "lt" in value or "lte" in value:
                    gt = value.get("gt")
                    gte = value.get("gte")
                    lt = value.get("lt")
                    lte = value.get("lte")

                    conditions.append(
                        models.FieldCondition(
                            key=key, range=models.Range(gt=gt, gte=gte, lt=lt, lte=lte)
                        )
                    )
            elif isinstance(value, list):
                # List of values for matching
                conditions.append(
                    models.FieldCondition(key=key, match=models.MatchValue(value=value))
                )

        return models.Filter(must=conditions)

    # Abstract methods required by VectorStoreProtocol

    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a new collection.

        Args:
            collection_name: Name of the collection
            dimension: Vector dimension

        Returns:
            True if creation was successful
        """
        try:
            if not self.client:
                await self.initialize()

            if not self.client:
                raise RuntimeError("Failed to initialize Qdrant client")

            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=dimension, distance=self.distance_metric
                ),
            )

            logger.info(
                f"Created Qdrant collection '{collection_name}' with dimension {dimension}"
            )
            return True
        except Exception as e:
            logger.error(f"Error creating collection '{collection_name}': {e}")
            return False

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            True if deletion was successful
        """
        try:
            if not self.client:
                await self.initialize()

            if not self.client:
                raise RuntimeError("Failed to initialize Qdrant client")

            # Delete collection
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted Qdrant collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection '{collection_name}': {e}")
            return False

    async def upsert_products(
        self,
        products: List[Any],  # ProductMetadata sequence
        vectors: List[List[float]],
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
        try:
            if len(products) != len(vectors):
                raise ValueError("Number of products and vectors must match")

            # Convert products to metadata dictionaries
            metadatas = []
            for product in products:
                if hasattr(product, "to_dict"):
                    metadatas.append(product.to_dict())
                elif isinstance(product, dict):
                    metadatas.append(product)
                else:
                    metadatas.append({"product": str(product)})

            # Use existing add_vectors method
            await self.add_vectors(
                vectors=vectors, metadatas=metadatas, batch_size=batch_size
            )
            return True
        except Exception as e:
            logger.error(f"Error upserting products: {e}")
            return False

    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
    ) -> List[Any]:  # List[SearchResult]
        """Search for similar vectors.

        Args:
            query_vector: Query vector
            limit: Maximum number of results
            filter_conditions: Optional filters
            score_threshold: Minimum similarity score

        Returns:
            List of search results
        """
        try:
            # Use existing search_by_vector method
            results = await self.search_by_vector(
                vector=query_vector,
                limit=limit,
                filters=filter_conditions,
                include_metadata=True,
            )

            # Filter by score threshold
            if score_threshold > 0.0:
                results = [r for r in results if r.score >= score_threshold]

            return results
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []

    async def delete_vectors(self, ids: List[str]) -> bool:
        """Delete vectors by ID.

        Args:
            ids: List of vector IDs to delete

        Returns:
            True if deletion was successful
        """
        try:
            # Use existing delete method
            return await self.delete(ids)
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False

    async def get_collection_info(self) -> Dict[str, Any]:  # CollectionInfo
        """Get collection information.

        Returns:
            Collection information
        """
        try:
            if not self.client:
                await self.initialize()

            if not self.client:
                raise RuntimeError("Failed to initialize Qdrant client")

            collection_info = self.client.get_collection(collection_name=self.store_id)

            return {
                "name": self.store_id,
                "dimension": self.dimension,
                "distance_metric": str(self.distance_metric),
                "vectors_count": collection_info.vectors_count or 0,
                "status": collection_info.status,
                "config": {
                    "distance": str(self.distance_metric),
                    "vector_size": self.dimension,
                },
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "name": self.store_id,
                "dimension": self.dimension,
                "distance_metric": str(self.distance_metric),
                "vectors_count": 0,
                "status": "error",
                "error": str(e),
            }

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Collection statistics
        """
        try:
            # Use existing get_stats method
            return await self.get_stats()
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}

    async def close(self) -> None:
        """Close the vector store connection."""
        try:
            if self.client:
                # Qdrant client doesn't have an explicit close method
                # but we can set it to None to release resources
                self.client = None
                logger.info("Closed Qdrant vector store connection")
        except Exception as e:
            logger.error(f"Error closing Qdrant connection: {e}")
