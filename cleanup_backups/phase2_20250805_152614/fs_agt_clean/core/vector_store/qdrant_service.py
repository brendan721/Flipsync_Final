"""
Qdrant Service for FlipSync Production Integration
================================================

High-performance Qdrant vector database service for the FlipSync agentic system.
Provides vector storage, similarity search, and collection management.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams, CollectionInfo
    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None
    models = None
    Distance = None
    VectorParams = None
    CollectionInfo = None
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class QdrantConfig:
    """Qdrant configuration."""
    host: str = "174.138.77.110"
    port: int = 6333
    timeout: int = 30
    prefer_grpc: bool = False
    api_key: Optional[str] = None
    https: bool = False


class QdrantService:
    """Production Qdrant service with collection management and vector operations."""
    
    def __init__(self, config: Optional[QdrantConfig] = None):
        """Initialize Qdrant service."""
        self.config = config or QdrantConfig()
        self._client: Optional[QdrantClient] = None
        self._initialized = False
        
        # Use environment variables if available
        if os.getenv("QDRANT_HOST"):
            self.config.host = os.getenv("QDRANT_HOST")
        if os.getenv("QDRANT_PORT"):
            self.config.port = int(os.getenv("QDRANT_PORT"))
        if os.getenv("QDRANT_API_KEY"):
            self.config.api_key = os.getenv("QDRANT_API_KEY")
    
    async def initialize(self) -> bool:
        """Initialize Qdrant connection."""
        if self._initialized:
            return True
        
        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant not available - using mock client")
            self._client = MockQdrantClient()
            self._initialized = True
            return True
        
        try:
            start_time = time.perf_counter()
            
            # Create Qdrant client
            self._client = QdrantClient(
                host=self.config.host,
                port=self.config.port,
                timeout=self.config.timeout,
                prefer_grpc=self.config.prefer_grpc,
                api_key=self.config.api_key,
                https=self.config.https
            )
            
            # Test connection by getting cluster info
            cluster_info = await asyncio.to_thread(self._client.get_cluster_info)
            
            init_time = (time.perf_counter() - start_time) * 1000
            logger.info(f"Qdrant service initialized in {init_time:.2f}ms")
            logger.info(f"Connected to Qdrant cluster: {cluster_info}")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            # Fallback to mock client
            self._client = MockQdrantClient()
            self._initialized = True
            return False
    
    async def list_collections(self) -> List[str]:
        """List all collections in Qdrant."""
        if not self._initialized:
            await self.initialize()
        
        try:
            collections = await asyncio.to_thread(self._client.get_collections)
            if hasattr(collections, 'collections'):
                return [col.name for col in collections.collections]
            return []
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists."""
        if not self._initialized:
            await self.initialize()
        
        try:
            collections = await self.list_collections()
            return collection_name in collections
        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}")
            return False
    
    async def create_collection(
        self, 
        collection_name: str, 
        vector_size: int = 1536,
        distance: str = "Cosine"
    ) -> bool:
        """Create a new collection."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if QDRANT_AVAILABLE and hasattr(models, 'Distance'):
                distance_metric = getattr(models.Distance, distance.upper(), models.Distance.COSINE)
                
                await asyncio.to_thread(
                    self._client.create_collection,
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=distance_metric
                    )
                )
            else:
                # Mock implementation
                pass
            
            logger.info(f"Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information."""
        if not self._initialized:
            await self.initialize()
        
        try:
            info = await asyncio.to_thread(
                self._client.get_collection,
                collection_name=collection_name
            )
            
            if hasattr(info, 'dict'):
                return info.dict()
            return {"name": collection_name, "status": "active"}
            
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return None
    
    async def upsert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        ids: Optional[List[Union[str, int]]] = None,
        payloads: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Upsert vectors into collection."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if not ids:
                ids = list(range(len(vectors)))
            
            if not payloads:
                payloads = [{}] * len(vectors)
            
            if QDRANT_AVAILABLE and hasattr(models, 'PointStruct'):
                points = [
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                    for point_id, vector, payload in zip(ids, vectors, payloads)
                ]
                
                await asyncio.to_thread(
                    self._client.upsert,
                    collection_name=collection_name,
                    points=points
                )
            
            logger.debug(f"Upserted {len(vectors)} vectors to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors to {collection_name}: {e}")
            return False
    
    async def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if QDRANT_AVAILABLE:
                results = await asyncio.to_thread(
                    self._client.search,
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    score_threshold=score_threshold
                )
                
                return [
                    {
                        "id": result.id,
                        "score": result.score,
                        "payload": result.payload or {}
                    }
                    for result in results
                ]
            else:
                # Mock results
                return [
                    {
                        "id": f"mock_result_{i}",
                        "score": 0.9 - (i * 0.1),
                        "payload": {"mock": True}
                    }
                    for i in range(min(limit, 3))
                ]
            
        except Exception as e:
            logger.error(f"Failed to search vectors in {collection_name}: {e}")
            return []
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        if not self._initialized:
            await self.initialize()
        
        try:
            await asyncio.to_thread(
                self._client.delete_collection,
                collection_name=collection_name
            )
            
            logger.info(f"Deleted collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    async def close(self) -> None:
        """Close Qdrant connection."""
        if self._client and hasattr(self._client, 'close'):
            try:
                await asyncio.to_thread(self._client.close)
            except Exception as e:
                logger.warning(f"Error closing Qdrant connection: {e}")
        
        self._client = None
        self._initialized = False
        logger.info("Qdrant service closed")


class MockQdrantClient:
    """Mock Qdrant client for fallback when Qdrant is unavailable."""
    
    def __init__(self):
        self._collections = {
            "agent_memories": {"vectors": 150, "size": 1536},
            "product_embeddings": {"vectors": 200, "size": 1536},
            "content_templates": {"vectors": 75, "size": 1536},
            "market_analysis": {"vectors": 100, "size": 1536},
            "user_preferences": {"vectors": 50, "size": 1536},
            "search_history": {"vectors": 300, "size": 1536},
            "recommendation_cache": {"vectors": 125, "size": 1536},
            "pricing_models": {"vectors": 80, "size": 1536},
            "competitor_data": {"vectors": 90, "size": 1536},
            "inventory_patterns": {"vectors": 110, "size": 1536},
            "logistics_optimization": {"vectors": 60, "size": 1536},
            "performance_metrics": {"vectors": 40, "size": 1536}
        }
    
    def get_cluster_info(self):
        """Mock cluster info."""
        return {"status": "green", "peer_count": 1}
    
    def get_collections(self):
        """Mock collections list."""
        class MockCollection:
            def __init__(self, name):
                self.name = name
        
        class MockCollections:
            def __init__(self, collections):
                self.collections = [MockCollection(name) for name in collections]
        
        return MockCollections(list(self._collections.keys()))
    
    def get_collection(self, collection_name: str):
        """Mock collection info."""
        if collection_name in self._collections:
            return {"name": collection_name, "status": "active"}
        raise Exception(f"Collection {collection_name} not found")
    
    def create_collection(self, collection_name: str, vectors_config=None):
        """Mock create collection."""
        self._collections[collection_name] = {"vectors": 0, "size": 1536}
    
    def upsert(self, collection_name: str, points=None):
        """Mock upsert."""
        if collection_name in self._collections:
            self._collections[collection_name]["vectors"] += len(points or [])
    
    def search(self, collection_name: str, query_vector=None, limit=10, score_threshold=None):
        """Mock search."""
        return []
    
    def delete_collection(self, collection_name: str):
        """Mock delete collection."""
        if collection_name in self._collections:
            del self._collections[collection_name]
    
    def close(self):
        """Mock close."""
        pass


# Global Qdrant service instance
_qdrant_service_instance: Optional[QdrantService] = None


def get_qdrant_service() -> QdrantService:
    """Get global Qdrant service instance."""
    global _qdrant_service_instance
    if _qdrant_service_instance is None:
        _qdrant_service_instance = QdrantService()
    return _qdrant_service_instance


async def get_initialized_qdrant_service() -> QdrantService:
    """Get initialized Qdrant service."""
    service = get_qdrant_service()
    if not service._initialized:
        await service.initialize()
    return service
