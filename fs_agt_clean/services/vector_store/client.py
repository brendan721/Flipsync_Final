"""Qdrant client wrapper with enhanced functionality"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union, cast

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.models import (
    Distance,
    Filter,
    PointIdsList,
    PointStruct,
    UpdateStatus,
    VectorParams,
)
from qdrant_client.models import (
    CollectionInfo,
    Condition,
    ExtendedPointId,
    FieldCondition,
    FilterSelector,
    Match,
    MatchValue,
    PointsSelector,
    Record,
    ScoredPoint,
    SearchRequest,
)

from fs_agt_clean.core.vector_store.models import (
    MetricCategory,
    MetricType,
    MetricUpdate,
)
from fs_agt_clean.core.vector_store.models import (
    ProductMetadata as ServiceProductMetadata,
)
from fs_agt_clean.core.vector_store.models import (
    SearchQuery,
    SearchResult,
    VectorStoreConfig,
)
from fs_agt_clean.core.vector_store.providers.qdrant import (
    QdrantVectorStore as QdrantClient,
)

logger = logging.getLogger(__name__)


def _convert_to_core_metadata(
    product: ServiceProductMetadata,
) -> ServiceProductMetadata:
    """Convert service product metadata to core product metadata."""
    return ServiceProductMetadata(
        product_id=product.product_id,
        title=product.title,
        description=product.description,
        price=product.price_range.min_price,  # Use min price as the reference price
        category=product.category.value,
        source=None,  # Source is handled by the core client
        timestamp=product.created_at,
        brand=product.brand,
        manufacturer=product.manufacturer,
        subcategory=product.subcategory,
        sku=product.sku,
        asin=product.asin,
        upc=product.upc,
        isbn=product.isbn,
        condition=product.condition.value,
        quantity=product.quantity_available,
        color=product.color,
        material=product.material,
        rating=product.rating,
        review_count=product.review_count,
        sales_rank=product.sales_rank,
        keywords=",".join(product.keywords),
        search_terms=",".join(product.search_terms),
        last_sale_at=product.last_sale_at,
        **product.attributes,
    )


def _build_field_condition(field: str, value: Any) -> Dict[str, Any]:
    """Build a field condition for filtering"""
    match_value = cast(MatchValue, value)
    return {"key": field, "match": {"value": match_value}}


def _create_filter(conditions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a Qdrant filter from conditions"""
    if not conditions:
        return None
    filter_conditions = [
        _build_field_condition(field, value) for field, value in conditions.items()
    ]
    return {"must": filter_conditions}


class QdrantStore(QdrantClient):
    """Wrapper for Qdrant vector store operations"""

    def __init__(
        self,
        config: VectorStoreConfig,
        metrics_callback: Optional[Any] = None,
    ):
        """Initialize QdrantStore."""
        super().__init__(config=config)
        self.metrics_callback = metrics_callback
        self.collection_name = config.store_id

    async def store_vectors(
        self,
        products: Sequence[ServiceProductMetadata],
        vectors: Sequence[List[float]],
        batch_size: int = 100,
    ) -> None:
        """Store vectors in Qdrant."""
        core_products = [_convert_to_core_metadata(p) for p in products]
        await self.upsert_products(core_products, vectors, batch_size)

    async def search_vectors(
        self,
        query: SearchQuery,
        score_threshold: float = 0.0,
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        return await super().search_vectors(
            query_vector=query.vector,
            limit=query.limit if query.limit else 10,
            filter_conditions=query.filters,
            score_threshold=score_threshold,
        )

    async def delete_vectors(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        await super().delete_vectors(ids)

        if self.metrics_callback:
            await self.metrics_callback(
                MetricUpdate(
                    name="vectors_deleted",
                    value=float(len(ids)),
                    metric_type=MetricType.COUNTER,
                    category=MetricCategory.SYSTEM,
                    source="vector_store",
                    labels={"collection": self.collection_name},
                )
            )

    async def get_collection_info(self) -> CollectionInfo:
        """Get collection info."""
        return await super().get_collection_info()

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return await super().get_collection_stats()

    async def list_collections(self) -> List[str]:
        """
        List all collections in the Qdrant database.

        Returns:
            List of collection names
        """
        try:
            collections = await self.client.get_collections()
            return [collection.name for collection in collections.collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise
