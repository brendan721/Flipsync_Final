"""Vector store client implementation."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeAlias,
    Union,
    cast,
)

import tenacity
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.models import (
    CollectionConfig,
    CollectionInfo,
    CollectionStatus,
    Distance,
    ExtendedPointId,
    FieldCondition,
    Filter,
    MatchValue,
    OptimizersStatus,
    OptimizersStatusOneOf,
    PayloadSchemaType,
    PointIdsList,
    PointStruct,
    SearchRequest,
    UpdateStatus,
    VectorParams,
)

from fs_agt_clean.core.monitoring.models import MetricCategory, MetricType, MetricUpdate

# Import directly from types to avoid confusion
from fs_agt_clean.core.monitoring.types import MetricCategory as MetricCategoryEnum

from .models import ProductMetadata, SearchQuery, SearchResult

logger = logging.getLogger(__name__)


def _build_field_condition(field: str, value: Any) -> Dict[str, Any]:
    """Build a field condition for filtering."""
    match_value = cast(MatchValue, value)
    return {"key": field, "match": {"value": match_value}}


def _create_filter(conditions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a Qdrant filter from conditions."""
    if not conditions:
        return None
    filter_conditions = [
        _build_field_condition(field, value) for field, value in conditions.items()
    ]
    return {"must": filter_conditions}


def _create_metric(
    name: str,
    value: float,
    labels: Dict[str, str],
) -> MetricUpdate:
    """Create a metric update."""
    return MetricUpdate(
        name=name,
        timestamp=datetime.now(timezone.utc),
        value=value,
        metric_type=MetricType.COUNTER,
        category=MetricCategoryEnum.SYSTEM,
        labels=labels,
    )


# Type alias for product types
ProductType = Union[ProductMetadata, Dict[str, Any]]


class QdrantClient:
    """Qdrant vector store client."""

    def __init__(
        self,
        collection_name: str,
        host: str = "localhost",
        port: int = 6333,
        vector_size: int = 1536,
        metrics_callback: Optional[Any] = None,
    ):
        """Initialize Qdrant client."""
        self.collection_name = collection_name
        self.client = AsyncQdrantClient(host=host, port=port)
        self.vector_size = vector_size
        self.metrics_callback = metrics_callback

    async def _record_metric(self, name: str, value: float = 1.0) -> None:
        """Record a metric if callback is configured."""
        if self.metrics_callback:
            metric = MetricUpdate(
                name=name,
                value=value,
                timestamp=datetime.now(timezone.utc),
                metric_type=MetricType.COUNTER,
                category=MetricCategoryEnum.SYSTEM,
                labels={"collection": self.collection_name},
            )
            await self.metrics_callback(metric)

    async def initialize(self) -> None:
        """Initialize the client asynchronously."""
        await self._ensure_collection()
        await self._create_payload_indexes()

    async def _ensure_collection(self) -> None:
        """Ensure collection exists with correct settings."""
        collections = await self.client.get_collections()
        if self.collection_name not in {c.name for c in collections.collections}:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )
            await self._create_payload_indexes()
            logger.info("Created collection %s", self.collection_name)

    async def _create_payload_indexes(self) -> None:
        """Create payload indexes for efficient filtering."""
        await self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="product_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        await self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="source",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        await self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="timestamp",
            field_schema=PayloadSchemaType.DATETIME,
        )

    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0,
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        try:
            search_filter = (
                _create_filter(filter_conditions) if filter_conditions else None
            )
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter,
                score_threshold=score_threshold,
            )
            await self._record_metric("vector_store_search_count")

            search_results = []
            for r in results:
                if r.payload:
                    metadata = {
                        k: v
                        for k, v in r.payload.items()
                        if isinstance(v, (str, float, datetime))
                    }
                    search_results.append(
                        SearchResult(
                            id=str(r.id),
                            score=r.score,
                            metadata=metadata,
                        )
                    )
            return search_results
        except Exception as e:
            logger.error("Error searching vectors: %s", str(e))
            raise

    async def upsert_products(
        self,
        products: Sequence[ProductType],
        vectors: Optional[Sequence[List[float]]] = None,
        batch_size: int = 100,
    ) -> None:
        """Upsert products with their vectors."""
        try:
            points = []
            for i, product in enumerate(products):
                if isinstance(product, dict):
                    payload = product
                else:
                    payload = product.to_dict()

                vector = vectors[i] if vectors else None

                # Create a unique ID if product_id is not provided
                product_id = payload.get("product_id")
                if not product_id:
                    product_id = str(uuid.uuid4())

                # Convert vector to the correct type
                vector_data = None
                if vector is not None:
                    vector_data = [
                        float(x) for x in vector
                    ]  # Ensure all elements are float

                point = PointStruct(
                    id=str(product_id),
                    payload=payload,
                    vector=vector_data,
                )
                points.append(point)

            for i in range(0, len(points), batch_size):
                batch = points[i : i + batch_size]
                await self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                )

            await self._record_metric(
                "vector_store_upsert_count", value=float(len(products))
            )
        except Exception as e:
            logger.error("Error upserting products: %s", str(e))
            raise

    async def delete_vectors(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        await self._ensure_collection()
        points_selector = PointIdsList(points=[str(id) for id in ids])
        result = await self.client.delete(
            collection_name=self.collection_name,
            points_selector=points_selector,
            wait=True,  # Ensure operation completes before returning
        )
        if result.status != UpdateStatus.COMPLETED:
            raise RuntimeError(f"Failed to delete vectors: {result.status}")

        if self.metrics_callback:
            await self.metrics_callback(
                _create_metric(
                    name="vector_store_delete",
                    value=float(len(ids)),
                    labels={
                        "operation": "delete_points",
                        "collection": self.collection_name,
                    },
                )
            )

    async def get_collection_info(self) -> CollectionInfo:
        """Get collection info."""
        await self._ensure_collection()
        result = await self.client.get_collection(self.collection_name)
        if not isinstance(result, CollectionInfo):
            raise TypeError(f"Expected CollectionInfo, got {type(result)}")
        return result

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            collection = await self.client.get_collection(self.collection_name)
            return {
                "points_count": collection.points_count,
                "vectors_count": collection.vectors_count,
                "segments_count": collection.segments_count,
                "status": collection.status,
                "optimizer_status": collection.optimizer_status,
                "config": collection.config,
            }
        except Exception as e:
            logger.error("Failed to get collection stats: %s", e)
            return {}
