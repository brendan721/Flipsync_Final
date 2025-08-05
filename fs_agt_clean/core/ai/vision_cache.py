"""
Vision Cache for FlipSync - Redis-based Caching Strategy
=======================================================

Provides Redis-based caching for vision analysis results to improve
performance and reduce API costs. Implements intelligent caching with
TTL management and cache hit rate optimization.

Features:
- Redis-based result caching with configurable TTL
- Image hash-based cache keys for deduplication
- Cache hit rate tracking and optimization
- Automatic cache cleanup and management
- Support for different cache tiers based on confidence
- Cost savings tracking through cache usage
"""

import json
import logging
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Redis for caching
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    try:
        import redis

        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False
        redis = None

from fs_agt_clean.core.ai.ebay_product_matcher import ProductMatch

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels based on result confidence."""

    HIGH_CONFIDENCE = "high"  # >0.8 confidence, long TTL
    MEDIUM_CONFIDENCE = "medium"  # 0.5-0.8 confidence, medium TTL
    LOW_CONFIDENCE = "low"  # <0.5 confidence, short TTL


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    result: ProductMatch
    confidence: float
    cache_level: CacheLevel
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0


@dataclass
class CacheStats:
    """Cache performance statistics."""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_writes: int = 0
    cache_evictions: int = 0
    hit_rate: float = 0.0
    average_lookup_time: float = 0.0
    cost_savings_estimate: float = 0.0


class VisionCache:
    """Redis-based caching for vision results."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize vision cache."""
        self.config = config or {}

        # Redis configuration
        self.redis_host = self.config.get("redis_host", "127.0.0.1")
        self.redis_port = self.config.get("redis_port", 6379)
        self.redis_password = self.config.get("redis_password", None)
        self.redis_db = self.config.get("redis_db", 0)

        # Cache configuration
        self.cache_prefix = self.config.get("cache_prefix", "flipsync:vision:")
        self.default_ttl = self.config.get("default_ttl", 86400)  # 24 hours

        # TTL by confidence level
        self.ttl_by_level = {
            CacheLevel.HIGH_CONFIDENCE: self.config.get(
                "high_confidence_ttl", 86400 * 7
            ),  # 7 days
            CacheLevel.MEDIUM_CONFIDENCE: self.config.get(
                "medium_confidence_ttl", 86400
            ),  # 1 day
            CacheLevel.LOW_CONFIDENCE: self.config.get(
                "low_confidence_ttl", 3600
            ),  # 1 hour
        }

        # Performance tracking
        self.stats = CacheStats()

        # Redis client
        self.redis_client = None
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            return

        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                db=self.redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            logger.info("Redis client initialized for vision caching")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.redis_client = None

    async def get_cached_result(self, image_hash: str) -> Optional[ProductMatch]:
        """
        Retrieve cached vision analysis result.

        Args:
            image_hash: SHA256 hash of the image

        Returns:
            Cached ProductMatch or None if not found
        """
        start_time = time.perf_counter()
        self.stats.total_requests += 1

        if not self.redis_client:
            self.stats.cache_misses += 1
            return None

        try:
            cache_key = f"{self.cache_prefix}{image_hash}"
            cached_data = await self.redis_client.get(cache_key)

            lookup_time = (time.perf_counter() - start_time) * 1000
            self._update_average_lookup_time(lookup_time)

            if cached_data:
                # Parse cached entry
                entry_data = json.loads(cached_data)
                entry = CacheEntry(**entry_data)

                # Update access statistics
                entry.access_count += 1
                entry.last_accessed = time.time()

                # Update cache entry with new access stats
                await self._update_cache_entry(cache_key, entry)

                self.stats.cache_hits += 1
                self._update_hit_rate()

                logger.debug(
                    f"Cache hit for image {image_hash[:8]}... (confidence: {entry.confidence:.3f})"
                )

                return entry.result
            else:
                self.stats.cache_misses += 1
                self._update_hit_rate()

                logger.debug(f"Cache miss for image {image_hash[:8]}...")

                return None

        except Exception as e:
            lookup_time = (time.perf_counter() - start_time) * 1000
            self._update_average_lookup_time(lookup_time)
            self.stats.cache_misses += 1
            logger.error(f"Cache lookup failed: {e}")
            return None

    async def cache_result(
        self,
        image_hash: str,
        result: ProductMatch,
        confidence: float,
        ttl: Optional[int] = None,
    ):
        """
        Cache vision result with appropriate TTL.

        Args:
            image_hash: SHA256 hash of the image
            result: ProductMatch to cache
            confidence: Confidence score for TTL determination
            ttl: Optional custom TTL in seconds
        """
        if not self.redis_client:
            return

        try:
            # Determine cache level and TTL
            cache_level = self._determine_cache_level(confidence)
            effective_ttl = ttl or self.ttl_by_level[cache_level]

            # Create cache entry
            entry = CacheEntry(
                result=result,
                confidence=confidence,
                cache_level=cache_level,
                created_at=time.time(),
                access_count=0,
                last_accessed=time.time(),
            )

            # Serialize entry
            cache_key = f"{self.cache_prefix}{image_hash}"
            entry_data = json.dumps(asdict(entry), default=str)

            # Store in Redis with TTL
            await self.redis_client.setex(cache_key, effective_ttl, entry_data)

            self.stats.cache_writes += 1

            logger.debug(
                f"Cached result for image {image_hash[:8]}... "
                f"(confidence: {confidence:.3f}, TTL: {effective_ttl}s, level: {cache_level.value})"
            )

        except Exception as e:
            logger.error(f"Failed to cache result: {e}")

    async def _update_cache_entry(self, cache_key: str, entry: CacheEntry):
        """Update cache entry with new access statistics."""
        try:
            # Get current TTL
            ttl = await self.redis_client.ttl(cache_key)
            if ttl > 0:
                # Update entry with new access stats
                entry_data = json.dumps(asdict(entry), default=str)
                await self.redis_client.setex(cache_key, ttl, entry_data)
        except Exception as e:
            logger.warning(f"Failed to update cache entry access stats: {e}")

    def _determine_cache_level(self, confidence: float) -> CacheLevel:
        """Determine cache level based on confidence score."""
        if confidence >= 0.8:
            return CacheLevel.HIGH_CONFIDENCE
        elif confidence >= 0.5:
            return CacheLevel.MEDIUM_CONFIDENCE
        else:
            return CacheLevel.LOW_CONFIDENCE

    def _update_hit_rate(self):
        """Update cache hit rate statistics."""
        total = self.stats.cache_hits + self.stats.cache_misses
        if total > 0:
            self.stats.hit_rate = self.stats.cache_hits / total

    def _update_average_lookup_time(self, lookup_time: float):
        """Update average lookup time statistics."""
        total = self.stats.total_requests
        current_avg = self.stats.average_lookup_time
        new_avg = ((current_avg * (total - 1)) + lookup_time) / total
        self.stats.average_lookup_time = new_avg

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache hit rates and performance metrics."""
        # Calculate cost savings estimate
        if self.stats.total_requests > 0:
            # Estimate cost savings based on cache hits
            # Assume average cloud vision cost of $0.001 per request
            avg_cloud_cost = 0.001
            cost_savings = self.stats.cache_hits * avg_cloud_cost
            self.stats.cost_savings_estimate = cost_savings

        # Get Redis info if available
        redis_info = {}
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                redis_info = {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
            except Exception as e:
                logger.warning(f"Failed to get Redis info: {e}")

        return {
            "cache_stats": asdict(self.stats),
            "redis_info": redis_info,
            "configuration": {
                "redis_host": self.redis_host,
                "redis_port": self.redis_port,
                "cache_prefix": self.cache_prefix,
                "ttl_by_level": {
                    level.value: ttl for level, ttl in self.ttl_by_level.items()
                },
            },
            "redis_available": REDIS_AVAILABLE,
            "redis_connected": self.redis_client is not None,
        }

    async def clear_cache(self, pattern: Optional[str] = None):
        """
        Clear cache entries matching pattern.

        Args:
            pattern: Redis pattern to match (default: all vision cache entries)
        """
        if not self.redis_client:
            return

        try:
            search_pattern = pattern or f"{self.cache_prefix}*"
            keys = await self.redis_client.keys(search_pattern)

            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.stats.cache_evictions += deleted
                logger.info(
                    f"Cleared {deleted} cache entries matching pattern: {search_pattern}"
                )
            else:
                logger.info(
                    f"No cache entries found matching pattern: {search_pattern}"
                )

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    async def cleanup_expired_entries(self):
        """Clean up expired cache entries (called by scheduler)."""
        if not self.redis_client:
            return

        try:
            # Redis automatically handles TTL expiration, but we can track it
            info = await self.redis_client.info()
            expired_keys = info.get("expired_keys", 0)

            if expired_keys > 0:
                logger.debug(
                    f"Redis automatically cleaned up {expired_keys} expired keys"
                )

        except Exception as e:
            logger.warning(f"Failed to get expiration info: {e}")

    async def health_check(self) -> Dict[str, bool]:
        """Check health of cache system."""
        health = {}

        if not self.redis_client:
            health["redis_connection"] = False
            health["cache_operations"] = False
            return health

        try:
            # Test Redis connection
            await self.redis_client.ping()
            health["redis_connection"] = True

            # Test cache operations
            test_key = f"{self.cache_prefix}health_check"
            await self.redis_client.setex(test_key, 10, "test")
            test_value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)

            health["cache_operations"] = test_value == "test"

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health["redis_connection"] = False
            health["cache_operations"] = False

        return health
