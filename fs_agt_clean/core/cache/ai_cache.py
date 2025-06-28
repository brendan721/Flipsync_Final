"""
AI Analysis Caching Service for FlipSync.

This service provides Redis-based caching for AI analysis results:
- Image analysis result caching
- Hash-based cache keys for duplicate detection
- TTL-based cache expiration
- Performance monitoring and metrics
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

try:
    import aioredis
    from aioredis import Redis

    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    Redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheMetrics:
    """Cache performance metrics tracking."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.total_requests = 0
        self.average_retrieval_time = 0.0
        self.start_time = datetime.now(timezone.utc)

    def record_hit(self, retrieval_time: float):
        """Record a cache hit."""
        self.hits += 1
        self.total_requests += 1
        self._update_average_time(retrieval_time)

    def record_miss(self):
        """Record a cache miss."""
        self.misses += 1
        self.total_requests += 1

    def record_set(self):
        """Record a cache set operation."""
        self.sets += 1

    def record_delete(self):
        """Record a cache delete operation."""
        self.deletes += 1

    def record_error(self):
        """Record a cache error."""
        self.errors += 1

    def _update_average_time(self, retrieval_time: float):
        """Update average retrieval time."""
        if self.hits == 1:
            self.average_retrieval_time = retrieval_time
        else:
            self.average_retrieval_time = (
                self.average_retrieval_time * (self.hits - 1) + retrieval_time
            ) / self.hits

    def get_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        uptime = datetime.now(timezone.utc) - self.start_time

        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "total_requests": self.total_requests,
            "hit_rate_percentage": round(self.get_hit_rate(), 2),
            "average_retrieval_time_ms": round(self.average_retrieval_time * 1000, 2),
            "uptime_hours": round(uptime.total_seconds() / 3600, 2),
            "requests_per_hour": round(
                self.total_requests / max(uptime.total_seconds() / 3600, 0.01), 2
            ),
        }


class AICacheService:
    """
    AI analysis caching service using Redis.

    This service provides:
    - Hash-based caching for image analysis results
    - TTL-based cache expiration
    - Performance monitoring and metrics
    - Cache invalidation and cleanup
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 1):
        """Initialize the AI cache service."""
        self.redis_url = redis_url
        self.db = db
        self.redis: Optional[Redis] = None
        self.metrics = CacheMetrics()

        # Cache configuration
        self.config = {
            "default_ttl": 3600 * 24,  # 24 hours
            "image_analysis_ttl": 3600 * 24 * 7,  # 7 days
            "category_optimization_ttl": 3600 * 24 * 3,  # 3 days
            "pricing_analysis_ttl": 3600 * 6,  # 6 hours (pricing changes frequently)
            "max_cache_size": 10000,  # Maximum number of cached items
            "key_prefix": "flipsync:ai:",
        }

        logger.info("AI Cache Service initialized")

    async def connect(self):
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching will be disabled")
            self.redis = None
            return

        try:
            self.redis = await aioredis.from_url(
                self.redis_url, db=self.db, encoding="utf-8", decode_responses=True
            )

            # Test connection
            await self.redis.ping()
            logger.info("Connected to Redis for AI caching")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Disconnected from Redis")

    def _generate_cache_key(
        self, cache_type: str, data: Union[str, bytes, Dict[str, Any]]
    ) -> str:
        """Generate a cache key based on data hash."""

        # Convert data to string for hashing
        if isinstance(data, bytes):
            data_str = data.hex()
        elif isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        # Create hash
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]

        # Return formatted key
        return f"{self.config['key_prefix']}{cache_type}:{data_hash}"

    async def cache_image_analysis(
        self,
        image_data: bytes,
        analysis_result: Dict[str, Any],
        additional_context: str = "",
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache image analysis result.

        Args:
            image_data: Original image data for hash generation
            analysis_result: Analysis result to cache
            additional_context: Additional context used in analysis
            ttl: Time to live in seconds (optional)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.redis:
            return False

        try:
            # Generate cache key based on image data and context
            cache_data = {
                "image_hash": hashlib.sha256(image_data).hexdigest(),
                "context": additional_context,
            }
            cache_key = self._generate_cache_key("image_analysis", cache_data)

            # Prepare cache value
            cache_value = {
                "analysis_result": analysis_result,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "context": additional_context,
                "image_size": len(image_data),
            }

            # Set TTL
            cache_ttl = ttl or self.config["image_analysis_ttl"]

            # Cache the result
            await self.redis.setex(cache_key, cache_ttl, json.dumps(cache_value))

            self.metrics.record_set()
            logger.debug(f"Cached image analysis result: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Error caching image analysis: {e}")
            self.metrics.record_error()
            return False

    async def get_cached_image_analysis(
        self, image_data: bytes, additional_context: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached image analysis result.

        Args:
            image_data: Original image data for hash generation
            additional_context: Additional context used in analysis

        Returns:
            Cached analysis result or None if not found
        """
        if not self.redis:
            return None

        start_time = time.time()

        try:
            # Generate cache key
            cache_data = {
                "image_hash": hashlib.sha256(image_data).hexdigest(),
                "context": additional_context,
            }
            cache_key = self._generate_cache_key("image_analysis", cache_data)

            # Retrieve from cache
            cached_value = await self.redis.get(cache_key)

            if cached_value:
                retrieval_time = time.time() - start_time
                self.metrics.record_hit(retrieval_time)

                # Parse and return cached result
                cache_data = json.loads(cached_value)
                logger.debug(f"Cache hit for image analysis: {cache_key}")
                return cache_data["analysis_result"]
            else:
                self.metrics.record_miss()
                logger.debug(f"Cache miss for image analysis: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving cached image analysis: {e}")
            self.metrics.record_error()
            return None

    async def cache_category_optimization(
        self,
        product_name: str,
        current_category: str,
        marketplace: str,
        optimization_result: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache category optimization result."""
        if not self.redis:
            return False

        try:
            # Generate cache key
            cache_data = {
                "product_name": product_name.lower(),
                "current_category": current_category.lower(),
                "marketplace": marketplace.lower(),
            }
            cache_key = self._generate_cache_key("category_optimization", cache_data)

            # Prepare cache value
            cache_value = {
                "optimization_result": optimization_result,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "product_name": product_name,
                "marketplace": marketplace,
            }

            # Set TTL
            cache_ttl = ttl or self.config["category_optimization_ttl"]

            # Cache the result
            await self.redis.setex(cache_key, cache_ttl, json.dumps(cache_value))

            self.metrics.record_set()
            logger.debug(f"Cached category optimization: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Error caching category optimization: {e}")
            self.metrics.record_error()
            return False

    async def get_cached_category_optimization(
        self, product_name: str, current_category: str, marketplace: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached category optimization result."""
        if not self.redis:
            return None

        start_time = time.time()

        try:
            # Generate cache key
            cache_data = {
                "product_name": product_name.lower(),
                "current_category": current_category.lower(),
                "marketplace": marketplace.lower(),
            }
            cache_key = self._generate_cache_key("category_optimization", cache_data)

            # Retrieve from cache
            cached_value = await self.redis.get(cache_key)

            if cached_value:
                retrieval_time = time.time() - start_time
                self.metrics.record_hit(retrieval_time)

                cache_data = json.loads(cached_value)
                logger.debug(f"Cache hit for category optimization: {cache_key}")
                return cache_data["optimization_result"]
            else:
                self.metrics.record_miss()
                return None

        except Exception as e:
            logger.error(f"Error retrieving cached category optimization: {e}")
            self.metrics.record_error()
            return None

    async def invalidate_cache(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Redis key pattern to match

        Returns:
            Number of keys deleted
        """
        if not self.redis:
            return 0

        try:
            # Find matching keys
            keys = await self.redis.keys(f"{self.config['key_prefix']}{pattern}")

            if keys:
                # Delete matching keys
                deleted_count = await self.redis.delete(*keys)
                self.metrics.deletes += deleted_count
                logger.info(
                    f"Invalidated {deleted_count} cache entries matching pattern: {pattern}"
                )
                return deleted_count

            return 0

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            self.metrics.record_error()
            return 0

    async def cleanup_expired_cache(self) -> Dict[str, Any]:
        """Clean up expired cache entries and return statistics."""
        if not self.redis:
            return {"error": "Redis not connected"}

        try:
            # Get all cache keys
            all_keys = await self.redis.keys(f"{self.config['key_prefix']}*")

            expired_count = 0
            total_keys = len(all_keys)

            # Check each key for expiration
            for key in all_keys:
                ttl = await self.redis.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    expired_count += 1

            # Get memory usage info
            memory_info = await self.redis.info("memory")

            return {
                "total_keys": total_keys,
                "expired_keys": expired_count,
                "active_keys": total_keys - expired_count,
                "memory_used": memory_info.get("used_memory_human", "Unknown"),
                "cleanup_timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            return {"error": str(e)}

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = self.metrics.get_stats()

        if self.redis:
            try:
                # Get Redis info
                redis_info = await self.redis.info()
                redis_memory = await self.redis.info("memory")

                # Get cache key count
                cache_keys = await self.redis.keys(f"{self.config['key_prefix']}*")

                stats.update(
                    {
                        "redis_connected": True,
                        "redis_version": redis_info.get("redis_version", "Unknown"),
                        "total_cache_keys": len(cache_keys),
                        "redis_memory_used": redis_memory.get(
                            "used_memory_human", "Unknown"
                        ),
                        "redis_memory_peak": redis_memory.get(
                            "used_memory_peak_human", "Unknown"
                        ),
                    }
                )

            except Exception as e:
                stats.update({"redis_connected": False, "redis_error": str(e)})
        else:
            stats.update({"redis_connected": False})

        return stats


# Global cache service instance
ai_cache_service = AICacheService()
