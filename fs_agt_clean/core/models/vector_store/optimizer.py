import gc
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np
import psutil

"\nVector store optimization and caching system.\n"
logger = logging.getLogger(__name__)


class StoreOptimizer:
    """Vector store optimization and caching system."""

    def __init__(
        self,
        cache_size_mb: int = 1024,
        memory_threshold: float = 0.85,
        optimization_interval: int = 1000,
    ):
        """Initialize the store optimizer with configuration parameters."""
        self.cache_size_mb = cache_size_mb
        self.memory_threshold = memory_threshold
        self.optimization_interval = optimization_interval

        self.cache = {}
        self.cache_usage = 0
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        self.memory_stats = {
            "last_check": datetime.now(),
            "peak_usage": 0.0,
            "current_usage": 0.0,
        }
        self.lock = threading.RLock()

    def should_optimize(self, metrics: Dict[str, Any]) -> bool:
        """
        Determine if optimization is needed based on metrics.
        """
        memory_usage = self._get_memory_usage()
        if memory_usage > self.memory_threshold:
            logger.info(f"Memory usage ({memory_usage:.2%}) exceeds threshold")
            return bool(True)
        total_ops = metrics.get("total_vectors", 0)
        if total_ops > 0 and total_ops % self.optimization_interval == 0:
            logger.info("Operation count (%s) triggers optimization", total_ops)
            return True
        return False

    def cleanup(self):
        """
        Perform cleanup and optimization tasks.
        """
        with self.lock:
            try:
                # Clear the cache
                self._cleanup_cache()

                # Force garbage collection
                gc.collect()

                # Reset cache statistics
                self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}

                # Update memory stats one final time
                self._update_memory_stats()

                logger.info("Cleanup completed successfully")
                return True
            except Exception as e:
                logger.error("Error during cleanup: %s", str(e))
                return False

    def get_from_cache(self, key: str) -> Optional[Any]:
        """
        Retrieve item from cache.
        """
        with self.lock:
            if key in self.cache:
                self.cache_stats["hits"] += 1
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            self.cache_stats["misses"] += 1
            return None

    def add_to_cache(self, key: str, value: Any):
        """
        Add item to cache with memory management.
        """
        with self.lock:
            try:
                item_size = self._estimate_size(value)
                while self.cache_usage + item_size > self.cache_size_mb * 1024 * 1024:
                    if not self.cache:
                        logger.warning("Cache full, cannot add new item")
                        return
                    oldest_key = next(iter(self.cache))
                    oldest_value = self.cache.pop(oldest_key)
                    self.cache_usage -= self._estimate_size(oldest_value)
                    self.cache_stats["evictions"] += 1
                self.cache[key] = value
                self.cache_usage += item_size
            except Exception as e:
                logger.error("Cache addition error: %s", str(e))

    def update_cache_stats(self, is_hit: bool) -> float:
        """
        Update cache statistics and return hit rate.
        """
        with self.lock:
            if is_hit:
                self.cache_stats["hits"] += 1
            else:
                self.cache_stats["misses"] += 1
            total = self.cache_stats["hits"] + self.cache_stats["misses"]
            return self.cache_stats["hits"] / total if total > 0 else 0.0

    def get_cache_usage(self) -> float:
        """
        Get current cache usage as a percentage.
        """
        max_size = self.cache_size_mb * 1024 * 1024
        return self.cache_usage / max_size if max_size > 0 else 0.0

    def _cleanup_cache(self):
        """
        Clear the cache and update usage statistics.
        """
        self.cache.clear()
        self.cache_usage = 0
        self.cache_stats["evictions"] += 1
        logger.debug("Cache cleared successfully")

    def _get_memory_usage(self) -> float:
        """
        Get current memory usage as a percentage.
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            total_memory = psutil.virtual_memory().total
            return memory_info.rss / total_memory
        except Exception as e:
            logger.error("Error getting memory usage: %s", str(e))
            return 0.0

    def _update_memory_stats(self):
        """
        Update memory usage statistics.
        """
        current_usage = self._get_memory_usage()
        self.memory_stats.update(
            {
                "last_check": datetime.now(),
                "current_usage": current_usage,
                "peak_usage": max(current_usage, self.memory_stats["peak_usage"]),
            }
        )

    def _estimate_size(self, obj: Any) -> int:
        """
        Estimate memory size of an object in bytes.
        """
        if isinstance(obj, (list, tuple)):
            return sum((self._estimate_size(item) for item in obj))
        elif isinstance(obj, dict):
            return sum(
                (
                    self._estimate_size(k) + self._estimate_size(v)
                    for k, v in obj.items()
                )
            )
        elif isinstance(obj, str):
            return len(obj.encode())
        elif isinstance(obj, (int, float)):
            return 8
        elif isinstance(obj, np.ndarray):
            return obj.nbytes
        return 100

    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Get optimization and memory statistics.
        """
        return {
            "cache_stats": self.cache_stats,
            "memory_stats": self.memory_stats,
            "cache_usage": self.get_cache_usage(),
            "cache_size_mb": self.cache_size_mb,
        }
