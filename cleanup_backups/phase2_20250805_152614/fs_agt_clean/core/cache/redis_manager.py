"""
Redis Manager for FlipSync Production Integration
===============================================

High-performance Redis manager for caching and session management
in the FlipSync agentic system.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

try:
    import aioredis
    from aioredis import Redis

    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    Redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    """Redis configuration."""

    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    encoding: str = "utf-8"
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    max_connections: int = 20


class RedisManager:
    """Production Redis manager with connection pooling and error handling."""

    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize Redis manager."""
        self.config = config or RedisConfig()
        self._client: Optional[Redis] = None
        self._initialized = False

        # Use environment variables if available
        if os.getenv("REDIS_HOST"):
            self.config.host = os.getenv("REDIS_HOST")
        if os.getenv("REDIS_PORT"):
            self.config.port = int(os.getenv("REDIS_PORT"))
        if os.getenv("REDIS_PASSWORD"):
            self.config.password = os.getenv("REDIS_PASSWORD")
        if os.getenv("REDIS_DB"):
            self.config.db = int(os.getenv("REDIS_DB"))

    async def initialize(self) -> bool:
        """Initialize Redis connection."""
        if self._initialized:
            return True

        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - using fallback mode")
            self._client = MockRedisClient()
            self._initialized = True
            return True

        try:
            start_time = time.perf_counter()

            # Build Redis URL
            redis_url = f"redis://:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.db}"

            # Create Redis client
            self._client = await aioredis.from_url(
                redis_url,
                encoding=self.config.encoding,
                decode_responses=self.config.decode_responses,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                max_connections=self.config.max_connections,
            )

            # Test connection
            await self._client.ping()

            init_time = (time.perf_counter() - start_time) * 1000
            logger.info(f"Redis manager initialized in {init_time:.2f}ms")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            # Fallback to mock client
            self._client = MockRedisClient()
            self._initialized = True
            return False

    async def ping(self) -> bool:
        """Test Redis connectivity."""
        if not self._initialized:
            await self.initialize()

        try:
            if hasattr(self._client, "ping"):
                result = await self._client.ping()
                return result is True or result == b"PONG" or result == "PONG"
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self._initialized:
            await self.initialize()

        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set value in Redis."""
        if not self._initialized:
            await self.initialize()

        try:
            if expire:
                return await self._client.setex(key, expire, value)
            else:
                return await self._client.set(key, value)
        except Exception as e:
            logger.error(f"Redis set failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self._initialized:
            await self.initialize()

        try:
            result = await self._client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete failed for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self._initialized:
            await self.initialize()

        try:
            result = await self._client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis exists failed for key {key}: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client and hasattr(self._client, "close"):
            try:
                await self._client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

        self._client = None
        self._initialized = False
        logger.info("Redis manager closed")

    @classmethod
    async def create(cls, config: Optional[RedisConfig] = None) -> "RedisManager":
        """Create and initialize Redis manager."""
        manager = cls(config)
        await manager.initialize()
        return manager


class MockRedisClient:
    """Mock Redis client for fallback when Redis is unavailable."""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}

    async def ping(self) -> str:
        """Mock ping."""
        return "PONG"

    async def get(self, key: str) -> Optional[str]:
        """Mock get."""
        # Check expiry
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._data[key]
            del self._expiry[key]
            return None

        return self._data.get(key)

    async def set(self, key: str, value: str) -> bool:
        """Mock set."""
        self._data[key] = value
        return True

    async def setex(self, key: str, time_seconds: int, value: str) -> bool:
        """Mock setex."""
        self._data[key] = value
        self._expiry[key] = time.time() + time_seconds
        return True

    async def delete(self, key: str) -> int:
        """Mock delete."""
        if key in self._data:
            del self._data[key]
            if key in self._expiry:
                del self._expiry[key]
            return 1
        return 0

    async def exists(self, key: str) -> int:
        """Mock exists."""
        # Check expiry
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._data[key]
            del self._expiry[key]
            return 0

        return 1 if key in self._data else 0

    async def close(self) -> None:
        """Mock close."""
        pass


# Global Redis manager instance
_redis_manager_instance: Optional[RedisManager] = None


def get_redis_manager() -> RedisManager:
    """Get global Redis manager instance."""
    global _redis_manager_instance
    if _redis_manager_instance is None:
        _redis_manager_instance = RedisManager()
    return _redis_manager_instance


async def get_initialized_redis_manager() -> RedisManager:
    """Get initialized Redis manager."""
    manager = get_redis_manager()
    if not manager._initialized:
        await manager.initialize()
    return manager


async def test_redis_performance():
    """Test Redis manager performance."""
    print("🚀 Testing Redis Manager Performance")
    print("=" * 50)

    manager = await RedisManager.create()

    # Test basic operations
    operations = [
        ("ping", lambda: manager.ping()),
        ("set", lambda: manager.set("test_key", "test_value", 60)),
        ("get", lambda: manager.get("test_key")),
        ("exists", lambda: manager.exists("test_key")),
        ("delete", lambda: manager.delete("test_key")),
    ]

    for op_name, operation in operations:
        start_time = time.perf_counter()

        try:
            result = await operation()
            duration = (time.perf_counter() - start_time) * 1000
            print(f"  {op_name}: {duration:.2f}ms - Result: {result}")
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            print(f"  {op_name}: {duration:.2f}ms - Error: {e}")

    await manager.close()
    print("✅ Redis performance test completed")


if __name__ == "__main__":
    asyncio.run(test_redis_performance())
