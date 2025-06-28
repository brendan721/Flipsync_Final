"""Optimized search implementation for vector similarity queries."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from fs_agt_clean.core.metrics.models import MetricDataPoint
from fs_agt_clean.core.monitoring.metric_types import MetricType

logger = logging.getLogger(__name__)


class SearchEngine:
    """Search engine for vector similarity search."""

    def __init__(self, index, max_threads: int = 4, cache_size: int = 1000):
        """Initialize search engine."""
        self.index = index
        self.max_threads = max_threads
        self.cache_size = cache_size
        self.query_cache = {}
        self.metrics: List[MetricDataPoint] = []
        self._cache_stats = {"hits": 0, "misses": 0}

    async def search(
        self,
        query_vector: np.ndarray,
        k: int = 10,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.

        Args:
            query_vector: Query vector
            k: Number of results to return
            filter_params: Optional filter parameters

        Returns:
            List of search results
        """
        try:
            query_key = self._get_query_key(query_vector, k, filter_params)

            # Check cache
            if query_key in self.query_cache:
                self._cache_stats["hits"] += 1
                await self.record_metric(
                    name="cache_hit", value=1, metric_type=MetricType.COUNTER
                )
                return self.query_cache[query_key]

            self._cache_stats["misses"] += 1
            await self.record_metric(
                name="cache_miss", value=1, metric_type=MetricType.COUNTER
            )

            # Perform search
            results = await self.index.search(
                query_vector, k=k, filter_params=filter_params
            )

            # Process results
            processed_results = self._post_process_results(results)

            # Update cache
            if len(self.query_cache) >= self.cache_size:
                # Evict oldest entry
                self.query_cache.pop(next(iter(self.query_cache)))
            self.query_cache[query_key] = processed_results

            await self.record_metric(
                name="search_success", value=1, metric_type=MetricType.COUNTER
            )
            return processed_results

        except Exception as e:
            await self.record_metric(
                name="search_error", value=1, metric_type=MetricType.COUNTER
            )
            raise

    def _get_query_key(
        self,
        query_vector: np.ndarray,
        k: int,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a unique key for caching search results."""
        key_parts = [str(query_vector.tobytes()), str(k)]
        if filter_params:
            key_parts.append(str(sorted(filter_params.items())))
        return "|".join(key_parts)

    def _post_process_results(
        self, results: List[Tuple[int, float, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Process raw search results into a standardized format."""
        processed_results = []
        for id_, score, metadata in results:
            processed_result = {
                "id": id_,
                "score": float(score),  # Convert to float for serialization
                "metadata": metadata,
            }
            processed_results.append(processed_result)
        return processed_results

    async def batch_search(
        self, query_vectors: List[np.ndarray], k: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """Perform batch search for multiple query vectors.

        Args:
            query_vectors: List of query vectors
            k: Number of results to return per query

        Returns:
            List of search results for each query
        """
        tasks = []
        for query_vector in query_vectors:
            tasks.append(self.search(query_vector, k=k))
        return await asyncio.gather(*tasks)

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Optional metric labels
        """
        metric = MetricDataPoint(
            id=str(len(self.metrics)),
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            labels=labels or {},
        )
        self.metrics.append(metric)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.

        Returns:
            Dictionary of metrics
        """
        metrics = {
            "cache_stats": self._cache_stats.copy(),
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "type": m.metric_type,
                    "timestamp": m.timestamp,
                    "labels": m.labels,
                }
                for m in self.metrics
            ],
        }
        return metrics

    async def get_latest_metrics(self) -> List[MetricDataPoint]:
        """Get latest metrics.

        Returns:
            List of latest metrics
        """
        return self.metrics[-10:] if self.metrics else []

    async def get_metrics_history(self) -> List[MetricDataPoint]:
        """Get historical metrics.

        Returns:
            List of all metrics
        """
        return self.metrics

    async def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
        self._cache_stats = {"hits": 0, "misses": 0}
