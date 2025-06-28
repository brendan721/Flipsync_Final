import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

import numpy as np
from pydantic import BaseModel, ConfigDict

from fs_agt_clean.core.monitoring.metrics_models import MetricUpdate
from fs_agt_clean.core.service.asin_finder.models import ASINData
from fs_agt_clean.services.metrics.service import MetricsService
from fs_agt_clean.services.types import MetricCategory, MetricType, ResourceType

"Search Analytics Service Implementation\n\nThis service tracks and analyzes search performance and usage patterns.\n"
logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class SearchMetrics:
    """Container for search performance metrics"""

    latency_ms: float
    result_count: int
    query_type: str
    filters_used: Optional[Dict[str, Any]] = None
    embedding_used: bool = False
    embedding_quality: Optional[float] = None
    cache_hit: bool = False
    error: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "latency_ms": self.latency_ms,
            "result_count": self.result_count,
            "query_type": self.query_type,
            "filters_used": self.filters_used,
            "embedding_used": self.embedding_used,
            "embedding_quality": self.embedding_quality,
            "cache_hit": self.cache_hit,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class SearchAnalytics:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.metrics: List[SearchMetrics] = []
        self._filter_usage: Dict[str, int] = defaultdict(int)
        self._embedding_stats: List[float] = []
        self._cache_stats = {"hits": 0, "misses": 0}
        self._error_counts: Dict[str, int] = defaultdict(int)

    @property
    def total_searches(self) -> int:
        return len(self.metrics)

    @property
    def average_results(self) -> float:
        if not self.metrics:
            return 0.0
        return sum(m.result_count for m in self.metrics) / len(self.metrics)

    @property
    def top_keywords(self) -> List[Dict[str, Union[str, int]]]:
        # TODO: Implement keyword tracking
        return []

    @property
    def category_distribution(self) -> Dict[str, int]:
        # TODO: Implement category tracking
        return {}

    @property
    def price_ranges(self) -> Dict[str, int]:
        # TODO: Implement price range tracking
        return {}

    @property
    def success_rate(self) -> float:
        if not self.metrics:
            return 0.0
        successful = sum(1 for m in self.metrics if m.error is None)
        return successful / len(self.metrics)

    @property
    def average_relevance(self) -> float:
        if not self._embedding_stats:
            return 0.0
        return sum(self._embedding_stats) / len(self._embedding_stats)

    @property
    def performance_metrics(self) -> Dict[str, float]:
        if not self.metrics:
            return {"avg_latency": 0.0}
        return {
            "avg_latency": sum(m.latency_ms for m in self.metrics) / len(self.metrics)
        }

    def get_daily_summary(
        self, target_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get summary of search metrics for the given date or last 24 hours"""
        now = datetime.now(timezone.utc)
        if target_date:
            start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        else:
            end_date = now
            start_date = now - timedelta(days=1)

        daily_metrics = [
            m
            for m in self.metrics
            if m.timestamp
            and start_date < datetime.fromisoformat(m.timestamp) < end_date
        ]

        if not daily_metrics:
            return {
                "total_searches": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "cache_hit_rate": 0.0,
                "error_rate": 0.0,
                "embedding_stats": {"count": 0, "avg_quality": 0.0},
                "filter_usage": {},
                "error_counts": {},
            }

        successful = sum(1 for m in daily_metrics if m.error is None)
        total = len(daily_metrics)
        embedding_metrics = [
            m for m in daily_metrics if m.embedding_used and m.embedding_quality
        ]

        summary = {
            "total_searches": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_latency_ms": (
                sum(m.latency_ms for m in daily_metrics) / total if total > 0 else 0.0
            ),
            "cache_hit_rate": (
                self._cache_stats["hits"]
                / (self._cache_stats["hits"] + self._cache_stats["misses"])
                if self._cache_stats["hits"] + self._cache_stats["misses"] > 0
                else 0.0
            ),
            "error_rate": (total - successful) / total if total > 0 else 0.0,
            "embedding_stats": {
                "count": len(embedding_metrics),
                "avg_quality": (
                    sum(
                        float(m.embedding_quality)
                        for m in embedding_metrics
                        if m.embedding_quality is not None
                    )
                    / len(embedding_metrics)
                    if embedding_metrics
                    else 0.0
                ),
            },
            "filter_usage": dict(self._filter_usage),
            "error_counts": dict(self._error_counts),
        }
        return summary

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        if not self.metrics:
            return {
                "latency": {"p50": 0.0, "p90": 0.0, "avg": 0.0, "max": 0.0},
                "embedding_quality": {"avg": 0.0, "min": 0.0, "max": 0.0},
                "cache": {"hit_ratio": 0.0},
                "filter_usage": {},
                "errors": {},
            }

        latencies = [m.latency_ms for m in self.metrics]
        embedding_qualities = [q for q in self._embedding_stats if q is not None]
        total_cache_ops = self._cache_stats["hits"] + self._cache_stats["misses"]

        return {
            "latency": {
                "p50": float(np.percentile(latencies, 50)),
                "p90": float(np.percentile(latencies, 90)),
                "avg": float(np.mean(latencies)),
                "max": float(np.max(latencies)),
            },
            "embedding_quality": {
                "avg": (
                    float(np.mean(embedding_qualities)) if embedding_qualities else 0.0
                ),
                "min": (
                    float(np.min(embedding_qualities)) if embedding_qualities else 0.0
                ),
                "max": (
                    float(np.max(embedding_qualities)) if embedding_qualities else 0.0
                ),
            },
            "cache": {
                "hit_ratio": (
                    self._cache_stats["hits"] / total_cache_ops
                    if total_cache_ops > 0
                    else 0.0
                )
            },
            "filter_usage": dict(self._filter_usage),
            "errors": dict(self._error_counts),
        }

    def get_optimization_suggestions(self) -> List[Dict[str, str]]:
        """Get suggestions for optimizing search performance"""
        suggestions = []
        metrics = self.get_performance_metrics()

        if metrics["latency"]["avg"] > 500:  # If average latency > 500ms
            suggestions.append(
                {
                    "type": "latency",
                    "message": "High average latency detected. Consider optimizing query execution or adding caching.",
                }
            )

        if metrics["cache"]["hit_ratio"] < 0.3:  # If cache hit rate < 30%
            suggestions.append(
                {
                    "type": "cache",
                    "message": "Low cache hit rate. Consider adjusting cache strategy or warming up cache.",
                }
            )

        if self.average_relevance < 0.7:  # If average relevance < 70%
            suggestions.append(
                {
                    "type": "embedding",
                    "message": "Low search relevance. Consider tuning embedding parameters or updating search algorithms.",
                }
            )

        return suggestions

    def _cleanup_old_metrics(self, max_age: timedelta = timedelta(days=30)) -> None:
        """Remove metrics older than max_age"""
        cutoff = datetime.now(timezone.utc) - max_age
        self.metrics = [
            m
            for m in self.metrics
            if m.timestamp and datetime.fromisoformat(m.timestamp) > cutoff
        ]

        # Reset counters and recalculate based on remaining metrics
        self._filter_usage.clear()
        self._embedding_stats.clear()
        self._cache_stats = {"hits": 0, "misses": 0}
        self._error_counts.clear()

        # Recalculate stats from remaining metrics
        for metric in self.metrics:
            if metric.filters_used:
                for filter_name in metric.filters_used:
                    self._filter_usage[filter_name] += 1
            if metric.embedding_quality is not None:
                self._embedding_stats.append(metric.embedding_quality)
            if metric.cache_hit:
                self._cache_stats["hits"] += 1
            else:
                self._cache_stats["misses"] += 1
            if metric.error:
                self._error_counts[metric.error] += 1

    def record_search(self, metrics: SearchMetrics) -> None:
        """Record search metrics"""
        self.metrics.append(metrics)
        if metrics.filters_used:
            for filter_name in metrics.filters_used:
                self._filter_usage[filter_name] += 1
        if metrics.embedding_quality is not None:
            self._embedding_stats.append(metrics.embedding_quality)
        if metrics.cache_hit:
            self._cache_stats["hits"] += 1
        else:
            self._cache_stats["misses"] += 1
        if metrics.error:
            self._error_counts[metrics.error] += 1


class SearchAnalyticsService:
    """Service for tracking and analyzing search metrics"""

    def __init__(self, metrics_service: MetricsService):
        """Initialize search analytics service.

        Args:
            metrics_service: Metrics service instance
        """
        self.metrics_service = metrics_service
        self._analytics = SearchAnalytics(metrics_service.config)

    async def track_search(
        self,
        search_params: Dict,
        results: List[Dict],
        execution_time: float = 0.0,
    ) -> None:
        """Track search operation metrics.

        Args:
            search_params: Search parameters used
            results: Search results
            execution_time: Search execution time in ms
        """
        try:
            metrics = {
                "search.latency_ms": execution_time,
                "search.results_count": len(results),
                "search.success": bool(results),
            }

            # Add search parameters as labels
            labels = {
                "query_type": "text" if "query" in search_params else "metadata",
                "filters_used": bool(search_params.get("filters")),
            }

            await self.metrics_service.collect_metrics(
                {
                    "metrics": metrics,
                    "labels": labels,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception as e:
            logger.error("Error tracking search: %s", e)

    async def get_analytics(
        self, time_range: timedelta = timedelta(days=7)
    ) -> SearchAnalytics:
        """
        Get aggregated search analytics for the specified time range.
        """
        cutoff_time = datetime.utcnow() - time_range
        recent_searches = [
            search
            for search in self._analytics._metrics
            if search.timestamp
            and datetime.fromisoformat(search.timestamp) > cutoff_time
        ]
        if not recent_searches:
            return self._analytics
        total_searches = len(recent_searches)
        average_results = np.mean([search.result_count for search in recent_searches])
        success_rate = np.mean(
            [float(search.error is None) for search in recent_searches]
        )
        top_keywords = sorted(
            [
                {"keyword": kw, "count": count}
                for kw, count in self._analytics._filter_usage.items()
            ],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]
        execution_times = [search.latency_ms for search in recent_searches]
        performance_metrics = {
            "avg_execution_time": float(np.mean(execution_times)),
            "p95_execution_time": float(np.percentile(execution_times, 95)),
            "max_execution_time": float(np.max(execution_times)),
        }
        for search in recent_searches:
            self._analytics.record_search(search)
        return self._analytics

    def _get_price_range(self, price: float) -> str:
        """
        Get price range bucket for a given price.
        """
        ranges = [
            (0, 10, "0-10"),
            (10, 25, "10-25"),
            (25, 50, "25-50"),
            (50, 100, "50-100"),
            (100, 250, "100-250"),
            (250, 500, "250-500"),
            (500, 1000, "500-1000"),
            (1000, float("inf"), "1000+"),
        ]
        for min_price, max_price, range_label in ranges:
            if min_price <= price < max_price:
                return range_label
        return "unknown"

    def _calculate_average_relevance(self, searches: List[Dict]) -> float:
        """
        Calculate average relevance score for recent searches.
        """
        relevance_scores = []
        for search in searches:
            if search.get("results_count", 0) > 0:
                relevance = min(search["results_count"] / 10, search["success"], 1.0)
                relevance_scores.append(relevance)
        return float(np.mean(relevance_scores)) if relevance_scores else 0.0

    async def cleanup_old_data(self, max_age: timedelta = timedelta(days=30)):
        """
        Clean up old search history and update frequency counters.
        """
        cutoff_time = datetime.utcnow() - max_age
        self._analytics._metrics = [
            m
            for m in self._analytics._metrics
            if m.timestamp and datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        self._analytics._filter_usage.clear()
        self._analytics._embedding_stats.clear()
        self._analytics._cache_stats = {"hits": 0, "misses": 0}
        self._analytics._error_counts.clear()

        # Recalculate stats from remaining metrics
        for metric in self._analytics._metrics:
            if metric.filters_used:
                for filter_name in metric.filters_used:
                    self._analytics._filter_usage[filter_name] += 1
            if metric.embedding_quality is not None:
                self._analytics._embedding_stats.append(metric.embedding_quality)
            if metric.cache_hit:
                self._analytics._cache_stats["hits"] += 1
            else:
                self._analytics._cache_stats["misses"] += 1
            if metric.error:
                self._analytics._error_counts[metric.error] += 1

    async def record_search_metrics(
        self, execution_time: float, results_count: int, success: bool
    ) -> None:
        """Record metrics for a search operation."""
        timestamp = datetime.now(timezone.utc)

        # Record execution time
        metric = MetricUpdate(
            timestamp=timestamp,
            type=MetricType.GAUGE,
            category=MetricCategory.APPLICATION,
            resource_type=ResourceType.CUSTOM,
            value=execution_time,
            metadata={"metric_name": "search_execution_time"},
        )
        await self.metrics_service.record_metric(metric)

        # Record results count
        metric = MetricUpdate(
            timestamp=timestamp,
            type=MetricType.COUNTER,
            category=MetricCategory.APPLICATION,
            resource_type=ResourceType.CUSTOM,
            value=results_count,
            metadata={"metric_name": "search_results_count"},
        )
        await self.metrics_service.record_metric(metric)

        # Record success rate
        metric = MetricUpdate(
            timestamp=timestamp,
            type=MetricType.GAUGE,
            category=MetricCategory.APPLICATION,
            resource_type=ResourceType.CUSTOM,
            value=1.0 if success else 0.0,
            metadata={"metric_name": "search_success_rate"},
        )
        await self.metrics_service.record_metric(metric)
