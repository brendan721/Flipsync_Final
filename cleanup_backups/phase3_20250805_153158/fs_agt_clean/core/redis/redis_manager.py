import asyncio
import logging
from typing import Optional

import redis.asyncio as redis
from pydantic import BaseModel
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisConfig(BaseModel):
    """Redis configuration settings."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    encoding: str = "utf-8"
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    max_connections: int = 10


class RedisManager:
    """Manager for Redis connections."""

    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize Redis manager.

        Args:
            config: Optional Redis configuration
        """
        self.config = config or RedisConfig()
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        if self._pool is None:
            try:
                self._pool = ConnectionPool(
                    host=self.config.host,
                    port=self.config.port,
                    db=self.config.db,
                    password=self.config.password,
                    encoding=self.config.encoding,
                    decode_responses=self.config.decode_responses,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.socket_connect_timeout,
                    retry_on_timeout=self.config.retry_on_timeout,
                    max_connections=self.config.max_connections,
                )
                self._client = redis.Redis(connection_pool=self._pool)
                await self._client.ping()
            except RedisError as e:
                logger.error("Failed to initialize Redis connection: %s", str(e))
                raise

    @property
    def client(self) -> redis.Redis:
        """Get Redis client.

        Returns:
            Redis client instance

        Raises:
            RuntimeError: If client is not initialized
        """
        if self._client is None:
            raise RuntimeError("Redis client not initialized. Call initialize() first.")
        return self._client

    async def get_client(self) -> redis.Redis:
        """Get Redis client, initializing if necessary.

        Returns:
            Redis client instance
        """
        if self._client is None:
            await self.initialize()
        return self._client

    async def close(self) -> None:
        """Close Redis connections."""
        if self._client is not None:
            await self._client.close()
            self._client = None
        if self._pool is not None:
            await self._pool.disconnect()
            self._pool = None

    @classmethod
    async def create(cls, config: Optional[RedisConfig] = None) -> "RedisManager":
        """Create and initialize a Redis manager.

        Args:
            config: Optional Redis configuration

        Returns:
            Initialized Redis manager
        """
        manager = cls(config)
        await manager.initialize()
        return manager

    async def ping(self) -> bool:
        """
        Ping Redis server to check connectivity.

        Returns:
            True if connected, otherwise raises exception
        """
        if self._client is None:
            await self.initialize()

        if self._client is None:
            raise RuntimeError("Redis client is not initialized")

        result = await asyncio.to_thread(self._client.ping)
        return result

    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis.

        Args:
            key: Redis key

        Returns:
            Optional[str]: Value if found, None otherwise
        """
        try:
            client = await self.get_client()
            return await client.get(key)
        except RedisError as e:
            logger.error(f"Error getting value from Redis: {str(e)}")
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set a value in Redis.

        Args:
            key: Redis key
            value: Value to set
            expire: Optional expiration time in seconds

        Returns:
            bool: True if value was set
        """
        try:
            client = await self.get_client()
            if expire is not None:
                return await client.setex(key, expire, value)
            else:
                return await client.set(key, value)
        except RedisError as e:
            logger.error(f"Error setting value in Redis: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from Redis.

        Args:
            key: Redis key

        Returns:
            bool: True if value was deleted
        """
        try:
            client = await self.get_client()
            return await client.delete(key) > 0
        except RedisError as e:
            logger.error(f"Error deleting value from Redis: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis.

        Args:
            key: Redis key

        Returns:
            bool: True if key exists
        """
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Error checking if key exists in Redis: {str(e)}")
            return False
