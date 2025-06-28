"""Service for interacting with Qdrant vector database."""

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Protocol, cast
from urllib.parse import urlparse

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
from qdrant_client.models import Distance, VectorParams
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.models import Document
from fs_agt_clean.core.services.embeddings import EmbeddingService

from .metrics_adapter import QdrantMetricsAdapter

logger = logging.getLogger(__name__)


class MetricsCollector(Protocol):
    """Protocol for metrics collection."""

    async def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Mapping[str, str]] = None,
    ) -> None:
        """Record a metric value."""
        pass  # Protocol definition

    async def record_error(
        self,
        name: str,
        error: str,
        labels: Optional[Mapping[str, str]] = None,
    ) -> None:
        """Record an error."""
        pass  # Protocol definition


class QdrantService:
    """Service for interacting with Qdrant vector database."""

    VECTOR_SIZE = 1536  # Match Document model and OllamaEmbeddingService

    def __init__(
        self,
        config_manager: ConfigManager,
        metrics_collector: Optional[QdrantMetricsAdapter] = None,
        collection_name: str = "documents",
    ) -> None:
        """Initialize QdrantService.

        Args:
            config_manager: Configuration manager instance
            metrics_collector: Optional metrics collector for monitoring
            collection_name: Name of the collection to use
        """
        self.config = config_manager.get("qdrant", {})
        self.metrics = metrics_collector
        self.collection_name = collection_name
        self._client: Optional[QdrantClient] = None
        self.embedding_service = EmbeddingService()

        # Get Qdrant URL from environment with fallback to config
        self.url = os.getenv("QDRANT_URL", "")
        if not self.url:
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 6333)
            self.url = f"http://{host}:{port}"

        logger.info("Initializing Qdrant client with URL: %s", self.url)

    @property
    def client(self) -> QdrantClient:
        """Get the Qdrant client instance, initializing if needed."""
        if self._client is None:
            try:
                parsed_url = urlparse(self.url)
                self._client = QdrantClient(
                    url=self.url,
                    api_key=self.config.get("api_key"),
                    prefer_grpc=self.config.get("prefer_grpc", True),
                    timeout=self.config.get("timeout", 10.0),
                )
                logger.info("Successfully connected to Qdrant")
            except Exception as e:
                logger.error("Failed to connect to Qdrant at %s: %s", self.url, str(e))
                raise
        # We need to assert that _client is not None here for type checkers
        assert self._client is not None
        return self._client

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def init_schema(self) -> None:
        """Initialize the Qdrant collection schema."""
        try:
            # Create collection with appropriate settings
            await asyncio.to_thread(
                self.client.recreate_collection,
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Successfully initialized collection: %s", self.collection_name)
        except Exception as e:
            logger.error("Failed to initialize schema: %s", str(e))
            raise

    async def close(self) -> None:
        """Close the Qdrant client connection."""
        if self._client is not None:
            await asyncio.to_thread(self._client.close)
            self._client = None
            logger.info("Closed Qdrant client connection")

    def _prepare_vector(self, vector: List[float]) -> List[float]:
        """Prepare vector for storage."""
        if not isinstance(vector, list):
            vector = list(vector)
        if len(vector) != self.VECTOR_SIZE:
            raise ValueError(f"Vector must have size {self.VECTOR_SIZE}")
        return vector

    async def store_document(self, document: Document) -> bool:
        """Store a document in the vector database."""
        try:
            start_time = datetime.now()

            # Generate vector if not provided
            vector = document.vector
            if vector is None:
                try:
                    vector = await self.embedding_service.get_embedding(
                        document.content
                    )
                except Exception as e:
                    logger.error("Failed to generate embedding: %s", str(e))
                    # Use a zero vector as fallback for testing
                    vector = [0.0] * self.VECTOR_SIZE

            vector = self._prepare_vector(vector)

            # Ensure document ID is a valid UUID
            doc_id = str(document.id)
            if not doc_id:
                doc_id = str(uuid.uuid4())

            # Create point for Qdrant
            point = PointStruct(
                id=doc_id,
                vector=vector,
                payload={
                    "title": document.title,
                    "content": document.content,
                    "metadata": document.metadata or {},
                    "created_at": document.created_at or datetime.now().isoformat(),
                    "updated_at": document.updated_at or datetime.now().isoformat(),
                },
            )

            # Store in Qdrant
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=[point],
                wait=True,
            )

            # Record metrics if available
            if self.metrics:
                duration = (datetime.now() - start_time).total_seconds()
                await self.metrics.record_metric(
                    "qdrant_store",
                    duration,
                    {"collection": self.collection_name},
                )

            return True

        except Exception as e:
            logger.error("Failed to store document: %s", str(e))
            if self.metrics:
                await self.metrics.record_error(
                    "qdrant_store_error",
                    str(e),
                    {"collection": self.collection_name},
                )
            return False

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document from the vector database."""
        try:
            start_time = datetime.now()

            # Retrieve document from Qdrant
            points = await asyncio.to_thread(
                self.client.retrieve,
                collection_name=self.collection_name,
                ids=[str(document_id)],
                with_payload=True,
            )

            if not points or not points[0].payload:
                return None

            point = points[0]
            payload = cast(Dict[str, Any], point.payload)

            # Record metrics if available
            if self.metrics:
                duration = (datetime.now() - start_time).total_seconds()
                await self.metrics.record_metric(
                    "qdrant_retrieve",
                    duration,
                    {"collection": self.collection_name},
                )

            return {
                "id": document_id,
                "title": payload.get("title", ""),
                "content": payload.get("content", ""),
                "metadata": payload.get("metadata", {}),
                "created_at": payload.get("created_at", ""),
                "updated_at": payload.get("updated_at", ""),
            }

        except Exception as e:
            logger.error("Failed to get document: %s", str(e))
            if self.metrics:
                await self.metrics.record_error(
                    "qdrant_retrieve_error",
                    str(e),
                    {"collection": self.collection_name},
                )
            return None

    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        score_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for documents by text similarity."""
        try:
            start_time = datetime.now()

            # Generate vector embedding for query
            vector = await self.embedding_service.get_embedding(query)
            vector = self._prepare_vector(vector)

            # Search in Qdrant
            results = await asyncio.to_thread(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit,
                offset=offset,
                score_threshold=score_threshold,
                with_payload=True,
            )

            # Format results
            formatted_results = []
            for result in results:
                if not result.payload:
                    continue

                payload = cast(Dict[str, Any], result.payload)
                formatted_result = {
                    "id": result.id,
                    "title": payload.get("title", ""),
                    "content": payload.get("content", ""),
                    "metadata": payload.get("metadata", {}),
                    "created_at": payload.get("created_at", ""),
                    "updated_at": payload.get("updated_at", ""),
                    "score": result.score,
                }
                formatted_results.append(formatted_result)

            # Record metrics if available
            if self.metrics:
                duration = (datetime.now() - start_time).total_seconds()
                await self.metrics.record_metric(
                    "qdrant_search_duration",
                    duration,
                    {
                        "collection": self.collection_name,
                        "results": str(len(formatted_results)),
                    },
                )

            return formatted_results

        except Exception as e:
            logger.error("Failed to search documents: %s", str(e))
            if self.metrics:
                await self.metrics.record_error(
                    "qdrant_search_error",
                    str(e),
                    {"collection": self.collection_name},
                )
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the vector database."""
        try:
            start_time = datetime.now()

            # Delete from Qdrant
            await asyncio.to_thread(
                self.client.delete,
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[str(document_id)]),
                wait=True,
            )

            # Record metrics if available
            if self.metrics:
                duration = (datetime.now() - start_time).total_seconds()
                await self.metrics.record_metric(
                    "qdrant_delete",
                    duration,
                    {"collection": self.collection_name},
                )

            return True

        except Exception as e:
            logger.error("Failed to delete document: %s", str(e))
            if self.metrics:
                await self.metrics.record_error(
                    "qdrant_delete_error",
                    str(e),
                    {"collection": self.collection_name},
                )
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            collection_info = await asyncio.to_thread(
                self.client.get_collection, collection_name=self.collection_name
            )
            return {
                "vectors_count": collection_info.vectors_count,
                "segments_count": collection_info.segments_count,
                "status": "healthy",
                "last_update": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error("Failed to get collection stats: %s", str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def store_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Store multiple documents in batch."""
        try:
            start_time = datetime.now()
            doc_ids = []

            for doc_data in documents:
                # Convert dict to Document
                doc = Document(
                    id=doc_data.get("id", str(len(doc_ids))),
                    title=doc_data.get("title", ""),
                    content=doc_data.get("content", ""),
                    metadata=doc_data.get("metadata", {}),
                    created_at=doc_data.get("created_at"),
                    updated_at=doc_data.get("updated_at"),
                    vector=doc_data.get("vector"),
                )

                success = await self.store_document(doc)
                if success:
                    doc_ids.append(str(doc.id))

            # Record metrics if available
            if self.metrics:
                duration = (datetime.now() - start_time).total_seconds()
                await self.metrics.record_metric(
                    "qdrant_store_batch",
                    duration,
                    {"collection": self.collection_name, "count": str(len(doc_ids))},
                )

            return doc_ids

        except Exception as e:
            logger.error("Failed to store documents batch: %s", str(e))
            if self.metrics:
                await self.metrics.record_error(
                    "qdrant_store_batch_error",
                    str(e),
                    {"collection": self.collection_name},
                )
            return []

    async def update_document(self, document_id: str, document: Document) -> bool:
        """Update an existing document in the vector database.

        Args:
            document_id: ID of document to update
            document: Updated document data

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            start_time = datetime.now()

            # Check if document exists
            existing = await self.get_document(document_id)
            if not existing:
                logger.error("Document %s not found", document_id)
                return False

            # Generate vector if not provided
            vector = document.vector
            if vector is None:
                try:
                    vector = await self.embedding_service.get_embedding(
                        document.content
                    )
                except Exception as e:
                    logger.error("Failed to generate embedding: %s", str(e))
                    # Keep existing vector
                    vector = existing.get("vector")

            if vector:
                vector = self._prepare_vector(vector)
            else:
                # If no vector available, use zero vector
                vector = [0.0] * self.VECTOR_SIZE

            # Create point for Qdrant
            point = PointStruct(
                id=str(document_id),
                vector=vector,  # Now vector is always a List[float]
                payload={
                    "title": document.title,
                    "content": document.content,
                    "metadata": document.metadata or {},
                    "created_at": existing.get("created_at"),
                    "updated_at": document.updated_at or datetime.now().isoformat(),
                },
            )

            # Update in Qdrant
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=[point],
                wait=True,
            )

            # Record metrics if available
            if self.metrics:
                duration = (datetime.now() - start_time).total_seconds()
                await self.metrics.record_metric(
                    "qdrant_update",
                    duration,
                    {"collection": self.collection_name},
                )

            return True

        except Exception as e:
            logger.error("Failed to update document: %s", str(e))
            if self.metrics:
                await self.metrics.record_error(
                    "qdrant_update_error",
                    str(e),
                    {"collection": self.collection_name},
                )
            return False

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def upsert_points(
        self,
        points: List[PointStruct],
        collection_name: Optional[str] = None,
        wait: bool = True,
    ) -> None:
        """Upsert points directly into a specified Qdrant collection.

        Args:
            points: List of PointStruct objects to upsert.
            collection_name: Target collection name. Defaults to service's default.
            wait: Whether to wait for the operation to complete.

        Raises:
            Exception: If the upsert operation fails after retries.
        """
        target_collection = collection_name or self.collection_name
        start_time = time.time()
        try:
            qdrant_client = self.client
            await asyncio.to_thread(
                qdrant_client.upsert,
                collection_name=target_collection,
                points=points,
                wait=wait,
            )
            logger.debug(
                "Successfully upserted %d points to collection %s",
                len(points),
                target_collection,
            )
            if self.metrics:
                duration = time.time() - start_time
                await self.metrics.record_metric(
                    "qdrant_upsert_points",
                    duration,
                    {"collection": target_collection, "count": str(len(points))},
                )
        except Exception as e:
            logger.error(
                "Failed to upsert points to collection %s: %s", target_collection, e
            )
            if self.metrics:
                await self.metrics.record_error(
                    "qdrant_upsert_points_error",
                    str(e),
                    {"collection": target_collection},
                )
            raise
