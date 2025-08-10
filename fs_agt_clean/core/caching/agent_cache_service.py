"""
Agent Cache Service for FlipSync 4+1 Architecture
================================================

High-performance Redis caching for autonomous agents:
- Content Agent: Cache SEO analysis and content optimization results
- Market Agent: Cache pricing analysis and market trend data
- Executive Agent: Cache strategic planning decisions
- Logistics Agent: Cache shipping optimization calculations

Performance targets:
- 40-60% response time reduction
- 5-minute cache TTL for decisions
- 1-minute cache TTL for database queries
"""

import asyncio
import json
import hashlib
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from fs_agt_clean.core.config.redis_config_unified import get_global_redis_config

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    data: Any
    created_at: datetime
    ttl_seconds: int
    agent_id: str
    cache_key: str
    hit_count: int = 0


class AgentCacheService:
    """High-performance caching service for autonomous agents."""

    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: int = 3,  # Use DB 3 for agent caching
        default_ttl: int = 300,  # 5 minutes default
        max_connections: int = 20,
    ):
        cfg = get_global_redis_config()
        self.redis_host = redis_host or cfg.host
        self.redis_port = redis_port or cfg.port
        self.redis_db = redis_db
        self._redis_password = cfg.password
        self.default_ttl = default_ttl
        self.max_connections = max_connections

        self.redis_pool = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
            "total_requests": 0,
        }

        # Agent-specific cache configurations
        self.agent_cache_config = {
            "content_autonomous_agent": {
                "ttl": 300,  # 5 minutes for content optimization
                "prefix": "content:",
                "enabled": True,
            },
            "market_autonomous_agent": {
                "ttl": 180,  # 3 minutes for market analysis (more dynamic)
                "prefix": "market:",
                "enabled": True,
            },
            "executive_autonomous_agent": {
                "ttl": 600,  # 10 minutes for strategic planning
                "prefix": "executive:",
                "enabled": True,
            },
            "logistics_autonomous_agent": {
                "ttl": 240,  # 4 minutes for logistics optimization
                "prefix": "logistics:",
                "enabled": True,
            },
        }

        logger.info("🚀 Agent Cache Service initialized")

    async def initialize(self):
        """Initialize Redis connection pool."""
        try:
            pool_kwargs = {
                "host": self.redis_host,
                "port": self.redis_port,
                "db": self.redis_db,
                "max_connections": self.max_connections,
                "retry_on_timeout": True,
                "socket_keepalive": True,
                "socket_keepalive_options": {},
                "health_check_interval": 30,
            }
            if self._redis_password:
                pool_kwargs["password"] = self._redis_password
            self.redis_pool = redis.ConnectionPool(**pool_kwargs)

            # Test connection
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            await redis_client.ping()
            await redis_client.close()

            logger.info("✅ Redis connection pool initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis connection: {e}")
            return False

    def _generate_cache_key(
        self, agent_id: str, task_type: str, parameters: Dict[str, Any]
    ) -> str:
        """Generate deterministic cache key for agent requests."""
        # Create a stable hash of the parameters
        # Sort keys and ensure consistent serialization
        clean_params = {}
        for key, value in parameters.items():
            if isinstance(value, (str, int, float, bool)):
                clean_params[key] = value
            else:
                clean_params[key] = str(value)

        param_str = json.dumps(clean_params, sort_keys=True, separators=(",", ":"))
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]

        # Get agent prefix
        config = self.agent_cache_config.get(agent_id, {})
        prefix = config.get("prefix", "agent:")

        cache_key = f"{prefix}{task_type}:{param_hash}"
        logger.debug(f"🔑 Generated cache key: {cache_key} for params: {param_str}")

        return cache_key

    async def get_cached_decision(
        self, agent_id: str, task_type: str, parameters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get cached agent decision if available."""
        if not self._is_caching_enabled(agent_id):
            return None

        cache_key = self._generate_cache_key(agent_id, task_type, parameters)

        try:
            self.cache_stats["total_requests"] += 1

            redis_client = redis.Redis(connection_pool=self.redis_pool)
            cached_data = await redis_client.get(cache_key)
            await redis_client.close()

            if cached_data:
                self.cache_stats["hits"] += 1

                # Parse cached data
                cache_entry = json.loads(cached_data)

                # Update hit count
                cache_entry["hit_count"] = cache_entry.get("hit_count", 0) + 1

                logger.info(
                    f"🎯 Cache HIT for {agent_id}:{task_type} (key: {cache_key[:20]}...)"
                )

                return {
                    "success": True,
                    "result": cache_entry["data"],
                    "cached": True,
                    "cache_created_at": cache_entry["created_at"],
                    "cache_hit_count": cache_entry["hit_count"],
                    "execution_time_ms": 1.0,  # Cache retrieval time
                }
            else:
                self.cache_stats["misses"] += 1
                logger.debug(f"💨 Cache MISS for {agent_id}:{task_type}")
                return None

        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Cache retrieval error for {agent_id}: {e}")
            return None

    async def cache_decision(
        self,
        agent_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        decision_result: Dict[str, Any],
    ) -> bool:
        """Cache agent decision result."""
        if not self._is_caching_enabled(agent_id):
            return False

        cache_key = self._generate_cache_key(agent_id, task_type, parameters)
        config = self.agent_cache_config.get(agent_id, {})
        ttl = config.get("ttl", self.default_ttl)

        try:
            # Create cache entry
            cache_entry = {
                "data": decision_result,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "ttl_seconds": ttl,
                "agent_id": agent_id,
                "cache_key": cache_key,
                "hit_count": 0,
            }

            redis_client = redis.Redis(connection_pool=self.redis_pool)
            await redis_client.setex(cache_key, ttl, json.dumps(cache_entry))
            await redis_client.close()

            self.cache_stats["sets"] += 1
            logger.info(f"💾 Cached decision for {agent_id}:{task_type} (TTL: {ttl}s)")

            return True

        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Cache storage error for {agent_id}: {e}")
            return False

    async def invalidate_agent_cache(self, agent_id: str) -> int:
        """Invalidate all cached decisions for a specific agent."""
        config = self.agent_cache_config.get(agent_id, {})
        prefix = config.get("prefix", "agent:")

        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)

            # Find all keys with the agent prefix
            pattern = f"{prefix}*"
            keys = await redis_client.keys(pattern)

            if keys:
                deleted_count = await redis_client.delete(*keys)
                logger.info(
                    f"🗑️ Invalidated {deleted_count} cache entries for {agent_id}"
                )
                await redis_client.close()
                return deleted_count
            else:
                await redis_client.close()
                return 0

        except Exception as e:
            logger.error(f"❌ Cache invalidation error for {agent_id}: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)

            # Get Redis info
            redis_info = await redis_client.info("memory")
            redis_keyspace = await redis_client.info("keyspace")

            # Calculate hit rate
            total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
            hit_rate = (
                (self.cache_stats["hits"] / total_requests * 100)
                if total_requests > 0
                else 0
            )

            # Get agent-specific stats
            agent_stats = {}
            for agent_id, config in self.agent_cache_config.items():
                if config["enabled"]:
                    prefix = config["prefix"]
                    pattern = f"{prefix}*"
                    keys = await redis_client.keys(pattern)
                    agent_stats[agent_id] = {
                        "cached_entries": len(keys),
                        "ttl": config["ttl"],
                        "enabled": config["enabled"],
                    }

            await redis_client.close()

            return {
                "cache_performance": {
                    "hit_rate_percent": round(hit_rate, 2),
                    "total_requests": total_requests,
                    "hits": self.cache_stats["hits"],
                    "misses": self.cache_stats["misses"],
                    "sets": self.cache_stats["sets"],
                    "errors": self.cache_stats["errors"],
                },
                "redis_memory": {
                    "used_memory_human": redis_info.get("used_memory_human", "N/A"),
                    "used_memory_peak_human": redis_info.get(
                        "used_memory_peak_human", "N/A"
                    ),
                    "maxmemory_human": redis_info.get("maxmemory_human", "N/A"),
                },
                "agent_cache_stats": agent_stats,
                "keyspace_info": redis_keyspace,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return {
                "error": str(e),
                "cache_performance": self.cache_stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _is_caching_enabled(self, agent_id: str) -> bool:
        """Check if caching is enabled for the agent."""
        config = self.agent_cache_config.get(agent_id, {})
        return config.get("enabled", False)

    async def warm_cache(
        self, agent_id: str, common_parameters: List[Dict[str, Any]]
    ) -> int:
        """Pre-warm cache with common agent requests."""
        if not self._is_caching_enabled(agent_id):
            return 0

        warmed_count = 0

        # This would typically trigger actual agent decisions to populate cache
        # For now, we'll just log the intent
        logger.info(
            f"🔥 Cache warming initiated for {agent_id} with {len(common_parameters)} parameter sets"
        )

        return warmed_count

    async def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries (Redis handles this automatically, but useful for stats)."""
        try:
            redis_client = redis.Redis(connection_pool=self.redis_pool)

            # Get all keys in our database
            all_keys = await redis_client.keys("*")
            expired_count = 0

            for key in all_keys:
                ttl = await redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    expired_count += 1

            await redis_client.close()

            if expired_count > 0:
                logger.info(f"🧹 Found {expired_count} expired cache entries")

            return expired_count

        except Exception as e:
            logger.error(f"❌ Error during cache cleanup: {e}")
            return 0

    async def close(self):
        """Close Redis connection pool."""
        if self.redis_pool:
            await self.redis_pool.disconnect()
            logger.info("🔌 Redis connection pool closed")


# Global cache service instance
agent_cache_service = AgentCacheService()
