"""
Vector Database Configuration for FlipSync.

This module provides configuration and connection management for Qdrant vector database,
enabling semantic search and product recommendations.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, PointStruct, VectorParams

    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None
    models = None
    Distance = None
    VectorParams = None
    PointStruct = None
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)


class VectorCollectionType(str, Enum):
    """Vector collection types for different use cases."""

    PRODUCTS = "products"
    CATEGORIES = "categories"
    LISTINGS = "listings"
    MARKET_TRENDS = "market_trends"


@dataclass
class VectorConfig:
    """Configuration for vector database operations."""

    host: str = "localhost"
    port: int = 6333
    api_key: Optional[str] = None
    timeout: int = 30
    prefer_grpc: bool = False
    https: bool = False
    vector_size: int = 1536  # OpenAI embedding size
    distance_metric: str = "Cosine"

    @classmethod
    def from_environment(cls) -> "VectorConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=int(os.getenv("QDRANT_TIMEOUT", "30")),
            prefer_grpc=os.getenv("QDRANT_PREFER_GRPC", "false").lower() == "true",
            https=os.getenv("QDRANT_HTTPS", "false").lower() == "true",
            vector_size=int(os.getenv("VECTOR_SIZE", "1536")),
            distance_metric=os.getenv("VECTOR_DISTANCE_METRIC", "Cosine"),
        )


class VectorDatabaseManager:
    """
    Vector database manager for Qdrant integration.

    This manager handles:
    - Connection management to Qdrant
    - Collection creation and management
    - Vector operations (insert, search, delete)
    - Health monitoring and fallback handling
    """

    def __init__(self, config: Optional[VectorConfig] = None):
        """Initialize the vector database manager."""
        self.config = config or VectorConfig.from_environment()
        self.client: Optional[QdrantClient] = None
        self.connected = False

        # Collection configurations
        self.collections = {
            VectorCollectionType.PRODUCTS: {
                "name": "flipsync_products",
                "description": "Product embeddings for semantic search",
                "vector_size": self.config.vector_size,
            },
            VectorCollectionType.CATEGORIES: {
                "name": "flipsync_categories",
                "description": "Category embeddings for classification",
                "vector_size": self.config.vector_size,
            },
            VectorCollectionType.LISTINGS: {
                "name": "flipsync_listings",
                "description": "Listing embeddings for recommendations",
                "vector_size": self.config.vector_size,
            },
            VectorCollectionType.MARKET_TRENDS: {
                "name": "flipsync_market_trends",
                "description": "Market trend embeddings for analysis",
                "vector_size": self.config.vector_size,
            },
        }

        logger.info("Vector Database Manager initialized")

    async def connect(self) -> bool:
        """Connect to Qdrant vector database."""
        if not QDRANT_AVAILABLE:
            logger.warning(
                "Qdrant client not available - vector operations will be disabled"
            )
            return False

        try:
            # Create Qdrant client
            if self.config.api_key:
                self.client = QdrantClient(
                    host=self.config.host,
                    port=self.config.port,
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                    prefer_grpc=self.config.prefer_grpc,
                    https=self.config.https,
                )
            else:
                self.client = QdrantClient(
                    host=self.config.host,
                    port=self.config.port,
                    timeout=self.config.timeout,
                    prefer_grpc=self.config.prefer_grpc,
                )

            # Test connection
            health_info = self.client.get_cluster_info()
            logger.info(f"Connected to Qdrant: {health_info}")

            # Initialize collections
            await self._initialize_collections()

            self.connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from Qdrant."""
        if self.client:
            try:
                self.client.close()
                logger.info("Disconnected from Qdrant")
            except Exception as e:
                logger.error(f"Error disconnecting from Qdrant: {e}")
            finally:
                self.client = None
                self.connected = False

    async def _initialize_collections(self):
        """Initialize required collections in Qdrant."""
        if not self.client:
            return

        try:
            # Get existing collections
            existing_collections = self.client.get_collections().collections
            existing_names = {col.name for col in existing_collections}

            # Create missing collections
            for collection_type, config in self.collections.items():
                collection_name = config["name"]

                if collection_name not in existing_names:
                    logger.info(f"Creating collection: {collection_name}")

                    # Get distance metric
                    distance_metric = getattr(
                        Distance, self.config.distance_metric.upper()
                    )

                    # Create collection
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=config["vector_size"], distance=distance_metric
                        ),
                    )

                    logger.info(f"Created collection: {collection_name}")
                else:
                    logger.info(f"Collection already exists: {collection_name}")

        except Exception as e:
            logger.error(f"Error initializing collections: {e}")

    def get_collection_name(self, collection_type: VectorCollectionType) -> str:
        """Get collection name for a given type."""
        return self.collections[collection_type]["name"]

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on vector database."""
        if not self.connected or not self.client:
            return {
                "status": "disconnected",
                "qdrant_available": QDRANT_AVAILABLE,
                "connected": False,
                "collections": {},
            }

        try:
            # Get cluster info
            cluster_info = self.client.get_cluster_info()

            # Get collection info
            collections_info = {}
            for collection_type, config in self.collections.items():
                collection_name = config["name"]
                try:
                    collection_info = self.client.get_collection(collection_name)
                    collections_info[collection_type.value] = {
                        "name": collection_name,
                        "vectors_count": collection_info.vectors_count,
                        "points_count": collection_info.points_count,
                        "status": "healthy",
                    }
                except Exception as e:
                    collections_info[collection_type.value] = {
                        "name": collection_name,
                        "status": "error",
                        "error": str(e),
                    }

            return {
                "status": "connected",
                "qdrant_available": QDRANT_AVAILABLE,
                "connected": True,
                "cluster_info": cluster_info,
                "collections": collections_info,
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "vector_size": self.config.vector_size,
                    "distance_metric": self.config.distance_metric,
                },
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "qdrant_available": QDRANT_AVAILABLE,
                "connected": False,
                "error": str(e),
            }

    def is_available(self) -> bool:
        """Check if vector database is available."""
        return QDRANT_AVAILABLE and self.connected and self.client is not None


# Global vector database manager instance
vector_db_manager = VectorDatabaseManager()
