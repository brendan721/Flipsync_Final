import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
from numpy.typing import NDArray

from fs_agt_clean.core.models.vector_store.indexer import VectorIndex
from fs_agt_clean.core.models.vector_store.models import SearchQuery, SearchResult
from fs_agt_clean.core.models.vector_store.optimizer import StoreOptimizer
from fs_agt_clean.core.models.vector_store.search import SearchEngine

"""Core vector store implementation with advanced indexing and optimization."""
logger = logging.getLogger(__name__)


class VectorStore:

    def __init__(
        self,
        dimension: int,
        index_type: str = "hnsw",
        cache_size_mb: int = 1024,
        max_threads: int = 4,
    ):
        self.dimension = dimension
        self.index_type = index_type
        self.cache_size_mb = cache_size_mb
        self.index = VectorIndex(dimension, index_type)
        self.optimizer = StoreOptimizer(cache_size_mb)
        self.search_engine = SearchEngine(self.index)
        self.max_threads = max_threads
        self.thread_pool = ThreadPoolExecutor(max_workers=max_threads)
        self.lock = threading.RLock()
        self.metrics = {
            "total_vectors": 0,
            "index_size_bytes": 0,
            "avg_query_time": 0.0,
            "cache_hit_rate": 0.0,
            "last_optimization": None,
        }

    def add_vectors(
        self,
        vectors: np.ndarray,
        metadata: List[Dict[str, Any]],
        batch_size: int = 1000,
    ) -> bool:
        """
        Add vectors to the store with batch processing.
        """
        try:
            total_vectors = len(vectors)
            if total_vectors == 0:
                return True
            for i in range(0, total_vectors, batch_size):
                batch_vectors = vectors[i : i + batch_size]
                batch_metadata = metadata[i : i + batch_size]
                with self.lock:
                    self.index.add_batch(batch_vectors, batch_metadata)
                self.metrics["total_vectors"] += len(batch_vectors)
                self.metrics["index_size_bytes"] = self.index.get_size_bytes()
            if self.optimizer.should_optimize(self.metrics):
                self.thread_pool.submit(self.optimize)
            return True
        except Exception as e:
            logger.error("Error adding vectors: %s", str(e))
            return False

    async def search(
        self,
        query_vector: Union[NDArray[np.float32], Sequence[float]],
        k: int = 10,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.

        Args:
            query_vector: Query vector as numpy array or sequence of floats
            k: Number of results to return
            filter_params: Optional filter parameters

        Returns:
            List of search results with scores and metadata
        """
        raise NotImplementedError("Subclasses must implement search method")

    def optimize(self) -> bool:
        """
        Optimize the vector store for better performance.
        """
        try:
            with self.lock:
                logger.info("Starting vector store optimization")
                self.index.optimize()
                self.optimizer.cleanup()
                self.metrics["last_optimization"] = datetime.now().isoformat()
                self.metrics["index_size_bytes"] = self.index.get_size_bytes()
                logger.info("Vector store optimization completed")
                return True
        except Exception as e:
            logger.error("Optimization error: %s", str(e))
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        """
        return self.metrics

    def _generate_cache_key(
        self, query_vector: np.ndarray, k: int, filter_params: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate a unique cache key for a query.
        """
        vector_hash = hash(query_vector.tobytes())
        filter_hash = hash(str(filter_params)) if filter_params else 0
        return f"{vector_hash}_{k}_{filter_hash}"

    def _update_query_metrics(self, query_time: float):
        """
        Update query performance metrics.
        """
        current_avg = self.metrics["avg_query_time"]
        total_queries = self.metrics.get("total_queries", 0) + 1
        alpha = 0.1
        new_avg = current_avg * (1 - alpha) + query_time * alpha
        self.metrics["avg_query_time"] = new_avg
        self.metrics["total_queries"] = total_queries

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get detailed index statistics.
        """
        return {
            "total_vectors": self.metrics["total_vectors"],
            "index_type": self.index_type,
            "dimension": self.dimension,
            "index_size_bytes": self.metrics["index_size_bytes"],
            "last_optimization": self.metrics["last_optimization"],
        }

    def get_cache_stats(self) -> Dict[str, float]:
        """
        Get cache performance statistics.
        """
        return {
            "cache_size_mb": self.cache_size_mb,
            "cache_hit_rate": self.metrics["cache_hit_rate"],
            "cache_usage": self.optimizer.get_cache_usage(),
        }

    async def add(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add documents to the vector store."""
        try:
            vectors = self.search_engine.encode_documents(documents)
            doc_metadata = [
                {"collection": collection, **(metadata or {})} for _ in documents
            ]
            return self.add_vectors(vectors, doc_metadata)
        except Exception as e:
            logger.error("Error adding documents to vector store: %s", str(e))
            return False

    async def close(self) -> None:
        """Close the vector store and cleanup resources."""
        try:
            self.thread_pool.shutdown(wait=True)
            self.optimizer.cleanup()
            self.index.cleanup()
        except Exception as e:
            logger.error("Error closing vector store: %s", str(e))
