"""
Performance optimization module for the FlipSync Decision Engine.
Provides caching, memoization, and performance monitoring utilities.
"""

import functools
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

from fs_agt_clean.core.brain.types import Decision, Memory, Pattern, Strategy

T = TypeVar("T")
CacheKey = Union[str, int, tuple]
CacheValue = TypeVar("CacheValue")


class PerformanceMetrics:
    """Track and store performance metrics."""

    def __init__(self):
        self.execution_times: Dict[str, List[float]] = {}
        self.cache_hits: Dict[str, int] = {}
        self.cache_misses: Dict[str, int] = {}
        self.last_reset = datetime.now(timezone.utc)

    def record_execution(self, operation: str, duration: float):
        """Record execution time for an operation."""
        if operation not in self.execution_times:
            self.execution_times[operation] = []
        self.execution_times[operation].append(duration)

    def record_cache_hit(self, cache_name: str):
        """Record a cache hit."""
        self.cache_hits[cache_name] = self.cache_hits.get(cache_name, 0) + 1

    def record_cache_miss(self, cache_name: str):
        """Record a cache miss."""
        self.cache_misses[cache_name] = self.cache_misses.get(cache_name, 0) + 1

    def get_average_execution_time(self, operation: str) -> Optional[float]:
        """Get average execution time for an operation."""
        times = self.execution_times.get(operation, [])
        return sum(times) / len(times) if times else None

    def get_cache_hit_ratio(self, cache_name: str) -> Optional[float]:
        """Get cache hit ratio for a cache."""
        hits = self.cache_hits.get(cache_name, 0)
        misses = self.cache_misses.get(cache_name, 0)
        total = hits + misses
        return hits / total if total > 0 else None

    def reset(self):
        """Reset all metrics."""
        self.execution_times.clear()
        self.cache_hits.clear()
        self.cache_misses.clear()
        self.last_reset = datetime.now(timezone.utc)


class LRUCache(Generic[CacheKey, CacheValue]):
    """LRU cache implementation with size limit and TTL."""

    def __init__(self, max_size: int = 1000, ttl: Optional[int] = None):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[CacheKey, tuple[CacheValue, float]] = OrderedDict()
        self.metrics = PerformanceMetrics()

    def get(self, key: CacheKey) -> Optional[CacheValue]:
        """Get value from cache."""
        if key not in self.cache:
            self.metrics.record_cache_miss("lru_cache")
            return None

        value, timestamp = self.cache[key]
        current_time = time.time()

        # Check TTL
        if self.ttl and current_time - timestamp > self.ttl:
            self.cache.pop(key)
            self.metrics.record_cache_miss("lru_cache")
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.metrics.record_cache_hit("lru_cache")
        return value

    def put(self, key: CacheKey, value: CacheValue):
        """Put value in cache."""
        if key in self.cache:
            self.cache.pop(key)

        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        self.cache[key] = (value, time.time())
        self.cache.move_to_end(key)

    def clear(self):
        """Clear the cache."""
        self.cache.clear()


class PatternCache(LRUCache[str, List[Pattern]]):
    """Specialized cache for pattern recognition results."""

    def __init__(self, max_size: int = 100, ttl: int = 300):  # 5 minutes TTL
        super().__init__(max_size, ttl)

    def get_patterns(self, context_hash: str) -> Optional[List[Pattern]]:
        """Get patterns for a context hash."""
        return self.get(context_hash)

    def store_patterns(self, context_hash: str, patterns: List[Pattern]):
        """Store patterns for a context hash."""
        self.put(context_hash, patterns)


class DecisionCache(LRUCache[str, Decision]):
    """Specialized cache for decision results."""

    def __init__(self, max_size: int = 50, ttl: int = 60):  # 1 minute TTL
        super().__init__(max_size, ttl)

    def get_decision(self, context_hash: str) -> Optional[Decision]:
        """Get decision for a context hash."""
        return self.get(context_hash)

    def store_decision(self, context_hash: str, decision: Decision):
        """Store decision for a context hash."""
        self.put(context_hash, decision)


def memoize_with_ttl(ttl: int = 60):
    """Decorator for memoizing function results with TTL."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: Dict[str, tuple[T, float]] = {}
        metrics = PerformanceMetrics()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()

            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp <= ttl:
                    metrics.record_cache_hit(func.__name__)
                    return result

            # Cache miss or expired
            metrics.record_cache_miss(func.__name__)
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            metrics.record_execution(func.__name__, duration)

            # Update cache
            cache[key] = (result, current_time)
            return result

        # Add cache management methods
        wrapper.clear_cache = cache.clear  # type: ignore
        wrapper.get_metrics = lambda: metrics  # type: ignore

        return wrapper

    return decorator


def monitor_performance(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for monitoring function performance."""
    metrics = PerformanceMetrics()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            metrics.record_execution(func.__name__, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_execution(f"{func.__name__}_error", duration)
            raise e

    # Add metrics access method
    wrapper.get_metrics = lambda: metrics  # type: ignore

    return wrapper


__all__ = [
    "PerformanceMetrics",
    "LRUCache",
    "PatternCache",
    "DecisionCache",
    "memoize_with_ttl",
    "monitor_performance",
]
