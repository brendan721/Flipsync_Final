import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.monitoring.logger import LogManager
from fs_agt_clean.core.services.embeddings import EmbeddingService
from fs_agt_clean.services.vector_store.service import ProductVectorService
from fs_agt_clean.services.llm.ollama_service import OllamaLLMService
from fs_agt_clean.services.metrics.service import MetricsService
from fs_agt_clean.services.search.analytics import SearchAnalyticsService, SearchMetrics

"Search Service Implementation\n\nThis service provides search functionality for the product vector database.\n"
logger: logging.Logger = logging.getLogger(__name__)

app = FastAPI(title="FlipSync Search API", version="1.0.0")


@dataclass
class SearchResult:
    """Container for search results"""

    products: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None


class SearchService:
    """Service for searching products using vector similarity."""

    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    def __init__(self, config_manager: ConfigManager):
        """Initialize search service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.llm_service = OllamaLLMService(config_manager)
        self.embedding_service = EmbeddingService(config_manager)
        self.product_service = ProductVectorService(config_manager)
        log_manager = LogManager()
        self.metrics_service = MetricsService(config_manager)
        self.analytics = SearchAnalyticsService(self.metrics_service)

    async def search_by_sku(
        self, sku: str, include_metadata: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Search for a product by SKU.

        Args:
            sku: Product SKU to search for
            include_metadata: Whether to include metadata in results

        Returns:
            Product data if found, None otherwise
        """
        start_time = datetime.now(timezone.utc)
        error = None
        product = None
        try:
            products = await self.product_service.get_products(filters={"sku": sku})
            if not products:
                logger.info("No product found with SKU: %s", sku)
                return None
            product = products[0]
            return product
        except Exception as e:
            logger.error("Error searching by SKU: %s", e)
            error = str(e)
            return None
        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            await self.analytics.track_search(
                search_params={"sku": sku, "include_metadata": include_metadata},
                results=[product] if product else [],
                execution_time=duration,
            )

    async def search_by_asin(
        self, asin: str, include_metadata: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Search for a product by ASIN.

        Args:
            asin: Product ASIN to search for
            include_metadata: Whether to include metadata in results

        Returns:
            Product data if found, None otherwise
        """
        start_time = datetime.now(timezone.utc)
        error = None
        product = None
        try:
            products = await self.product_service.get_products(filters={"asin": asin})
            if not products:
                logger.info("No product found with ASIN: %s", asin)
                return None
            product = products[0]
            return product
        except Exception as e:
            logger.error("Error searching by ASIN: %s", e)
            error = str(e)
            return None
        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            await self.analytics.track_search(
                search_params={"asin": asin, "include_metadata": include_metadata},
                results=[product] if product else [],
                execution_time=duration,
            )

    async def search_similar(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> SearchResult:
        """Search for products similar to query text.

        Args:
            query: Search query text
            filters: Optional metadata filters
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            SearchResult containing products and metadata
        """
        start_time = datetime.now(timezone.utc)
        error = None
        embedding_quality = None
        results = []
        try:
            embedding = await self.embedding_service.get_embedding(query)
            if not embedding:
                logger.error("Failed to generate query embedding")
                return SearchResult(
                    query=query,
                    products=[],
                    total=0,
                    page=1,
                    page_size=self.DEFAULT_PAGE_SIZE,
                    filters=filters or {},
                    duration_ms=0,
                )
            limit = min(limit or self.DEFAULT_PAGE_SIZE, self.MAX_PAGE_SIZE)
            page = (offset // limit) + 1
            results = await self.product_service.search_similar(
                vector=embedding, limit=limit
            )
            if results:
                embedding_quality = sum((r.get("score", 0) for r in results)) / len(
                    results
                )
            return SearchResult(
                query=query,
                products=results,
                total=len(results),
                page=page,
                page_size=limit,
                filters=filters or {},
                duration_ms=0,
            )
        except Exception as e:
            logger.error("Error searching similar products: %s", e)
            error = str(e)
            return SearchResult(
                query=query,
                products=[],
                total=0,
                page=1,
                page_size=limit or self.DEFAULT_PAGE_SIZE,
                filters=filters or {},
                duration_ms=0,
            )
        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            await self.analytics.track_search(
                search_params={
                    "query": query,
                    "filters": filters,
                    "limit": limit,
                    "offset": offset,
                },
                results=results,
                execution_time=duration,
            )

    async def filter_products(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> SearchResult:
        """Filter products by metadata.

        Args:
            filters: Metadata filters to apply
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            SearchResult containing filtered products
        """
        start_time = datetime.now(timezone.utc)
        try:
            error = None
            limit = min(limit or self.DEFAULT_PAGE_SIZE, self.MAX_PAGE_SIZE)
            page = (offset // limit) + 1
            results = await self.product_service.get_products(
                filters=filters,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.error("Error filtering products: %s", e)
            error = str(e)
            results = []
        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            await self.analytics.track_search(
                search_params={
                    "filters": filters,
                    "limit": limit,
                    "offset": offset,
                },
                results=results,
                execution_time=duration,
            )
        logger.info(
            "Found %s products matching filters in %.2fms", len(results), duration
        )

        return SearchResult(
            query="",
            products=results,
            total=len(results),
            page=page,
            page_size=limit,
            filters=filters,
            duration_ms=duration,
        )

    def get_analytics(self) -> Dict[str, Any]:
        """Get search analytics

        Returns:
            Dictionary of analytics data
        """
        return self.analytics.get_metrics()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/search/sku/{sku}")
async def search_by_sku_endpoint(sku: str, include_metadata: bool = True):
    service = SearchService(ConfigManager())
    result = await service.search_by_sku(sku, include_metadata)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@app.get("/search/asin/{asin}")
async def search_by_asin_endpoint(asin: str, include_metadata: bool = True):
    service = SearchService(ConfigManager())
    result = await service.search_by_asin(asin, include_metadata)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@app.post("/search/similar")
async def search_similar_endpoint(
    query: str,
    limit: Optional[int] = None,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None,
):
    service = SearchService(ConfigManager())
    result = await service.search_similar(query, filters, limit, offset)
    return result


@app.post("/search/filter")
async def filter_products_endpoint(
    filters: Dict[str, Any],
    limit: Optional[int] = None,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
):
    service = SearchService(ConfigManager())
    result = await service.filter_products(filters, limit, offset)
    return result


@app.get("/analytics")
async def get_analytics_endpoint():
    service = SearchService(ConfigManager())
    return service.get_analytics()
