"""Vector store service for storing and retrieving product data."""

import logging
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from fs_agt_clean.core.services.embeddings import EmbeddingService


class VectorStoreService:
    """Service for storing and retrieving product data in vector format."""

    def __init__(
        self,
        collection_name: str = "products",
        host: str = "localhost",
        port: int = 6333,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """Initialize the vector store service.

        Args:
            collection_name: Name of the collection to store vectors
            host: Qdrant server host
            port: Qdrant server port
            embedding_service: Optional EmbeddingService instance
        """
        self.logger = logging.getLogger(__name__)
        self.collection_name = collection_name
        self.client = QdrantClient(host=host, port=port)
        self.embedding_service = embedding_service or EmbeddingService()

        # Ensure collection exists
        collections = self.client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

    async def store_product(self, product_data: Dict[str, Any]) -> str:
        """Store product data in the vector store.

        Args:
            product_data: Product data to store

        Returns:
            ID of the stored vector
        """
        try:
            # Generate embedding from product text
            text = (
                f"{product_data.get('title', '')} {product_data.get('description', '')}"
            )
            embedding = await self.embedding_service.get_embedding(text)

            # Store in Qdrant
            vector_id = product_data["asin"]
            point = PointStruct(id=vector_id, vector=embedding, payload=product_data)
            self.client.upsert(collection_name=self.collection_name, points=[point])

            return vector_id

        except Exception as e:
            self.logger.error(
                f"Failed to store product {product_data.get('asin')}: {e}"
            )
            raise

    async def search_similar(
        self, query: str, limit: int = 10, score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar products.

        Args:
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score

        Returns:
            List of similar products with scores
        """
        try:
            # Generate query embedding
            query_vector = await self.embedding_service.get_embedding(query)

            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )

            return [{"product": hit.payload, "score": hit.score} for hit in results]

        except Exception as e:
            self.logger.error(f"Failed to search with query '{query}': {e}")
            raise

    async def delete_product(self, product_id: str) -> bool:
        """Delete a product from the vector store.

        Args:
            product_id: ID of the product to delete

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete(
                collection_name=self.collection_name, points_selector=[product_id]
            )
            return True

        except Exception as e:
            self.logger.error("Failed to delete product %s: %s", product_id, e)
            return False


class ProductVectorService:
    """Product-specific vector store service for market analysis."""

    def __init__(self, config_manager=None):
        """Initialize the product vector service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.vector_store = VectorStoreService()
        self.logger = logging.getLogger(__name__)

    async def get_products(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get products with optional filtering.

        Args:
            filters: Optional filters to apply
            limit: Maximum number of products to return
            offset: Number of products to skip

        Returns:
            List of product data
        """
        try:
            # For now, return mock data since we don't have a full product database
            # In production, this would query the actual product database
            mock_products = []

            # Generate some mock products based on filters
            if filters:
                if "sku" in filters:
                    mock_products.append(
                        {
                            "id": "prod_001",
                            "sku": filters["sku"],
                            "name": f"Product for SKU {filters['sku']}",
                            "description": "Mock product description",
                            "price": 29.99,
                            "category": "electronics",
                        }
                    )
                elif "asin" in filters:
                    mock_products.append(
                        {
                            "id": "prod_002",
                            "asin": filters["asin"],
                            "name": f"Product for ASIN {filters['asin']}",
                            "description": "Mock product description",
                            "price": 39.99,
                            "category": "books",
                        }
                    )

            # Apply limit and offset
            start_idx = offset
            end_idx = offset + limit
            return mock_products[start_idx:end_idx]

        except Exception as e:
            self.logger.error("Error getting products: %s", e)
            return []

    async def search_similar(
        self, vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar products using vector similarity.

        Args:
            vector: Query vector for similarity search
            limit: Maximum number of results

        Returns:
            List of similar products with scores
        """
        try:
            # For now, return mock similar products
            # In production, this would use the actual vector store
            mock_results = [
                {
                    "id": "similar_001",
                    "name": "Similar Product 1",
                    "description": "A product similar to your query",
                    "price": 24.99,
                    "score": 0.85,
                },
                {
                    "id": "similar_002",
                    "name": "Similar Product 2",
                    "description": "Another similar product",
                    "price": 34.99,
                    "score": 0.78,
                },
            ]

            return mock_results[:limit]

        except Exception as e:
            self.logger.error("Error searching similar products: %s", e)
            return []
