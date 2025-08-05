"""
Unified Redis Configuration for FlipSync.

This module provides a single, consistent Redis configuration that resolves
the inconsistencies found across the codebase.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UnifiedRedisConfig:
    """Unified Redis configuration for all FlipSync services."""

    host: str
    port: int
    db: int
    password: Optional[str]
    ssl: bool = False
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    max_connections: int = 20
    encoding: str = "utf-8"
    decode_responses: bool = True

    @property
    def connection_string(self) -> str:
        """Get Redis connection string."""
        protocol = "rediss" if self.ssl else "redis"
        auth = f":{self.password}@" if self.password else ""
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"

    @property
    def connection_kwargs(self) -> dict:
        """Get connection kwargs for Redis client."""
        kwargs = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "encoding": self.encoding,
            "decode_responses": self.decode_responses,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "retry_on_timeout": self.retry_on_timeout,
            "max_connections": self.max_connections,
        }

        if self.password:
            kwargs["password"] = self.password

        return kwargs


def get_unified_redis_config() -> UnifiedRedisConfig:
    """
    Get unified Redis configuration based on environment.

    This function resolves the Redis configuration inconsistencies by:
    1. Detecting the deployment environment (Docker, local, production server)
    2. Using appropriate host and authentication settings
    3. Providing consistent configuration across all services

    Returns:
        UnifiedRedisConfig: Properly configured Redis settings
    """

    # Detect environment
    in_docker = os.path.exists("/.dockerenv")
    is_production_server = os.path.exists(
        "/opt/flipsync"
    )  # DigitalOcean droplet indicator

    # Environment-specific defaults
    if in_docker:
        # Docker environment - Redis service name
        default_host = "redis"
        default_password = os.getenv("REDIS_PASSWORD")  # Use env var in Docker
        logger.info("Detected Docker environment - using Redis service name")

    elif is_production_server:
        # Production server (DigitalOcean droplet) - Redis with authentication
        default_host = "174.138.77.110"
        default_password = "FlipSync2024SecureRedis!"  # Production Redis password
        logger.info(
            "Detected production server environment - using authenticated Redis"
        )

    else:
        # Development environment
        default_host = "localhost"
        default_password = None
        logger.info("Detected development environment - using localhost Redis")

    # Build configuration with environment variables override
    config = UnifiedRedisConfig(
        host=os.getenv("REDIS_HOST", default_host),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD", default_password),
        ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
        socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
        socket_connect_timeout=int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")),
        max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
    )

    logger.info(
        f"Unified Redis config: {config.host}:{config.port} "
        f"(db: {config.db}, auth: {'yes' if config.password else 'no'})"
    )

    return config


def get_redis_connection_string() -> str:
    """Get Redis connection string using unified configuration."""
    config = get_unified_redis_config()
    return config.connection_string


def get_redis_connection_kwargs() -> dict:
    """Get Redis connection kwargs using unified configuration."""
    config = get_unified_redis_config()
    return config.connection_kwargs


# Global configuration instance
_unified_config: Optional[UnifiedRedisConfig] = None


def get_global_redis_config() -> UnifiedRedisConfig:
    """Get global Redis configuration instance (singleton pattern)."""
    global _unified_config

    if _unified_config is None:
        _unified_config = get_unified_redis_config()

    return _unified_config


def reset_global_redis_config():
    """Reset global Redis configuration (for testing)."""
    global _unified_config
    _unified_config = None


# Compatibility functions for existing code
def get_redis_config():
    """Compatibility function for existing code."""
    return get_global_redis_config()


def get_redis_url():
    """Compatibility function for existing code."""
    return get_redis_connection_string()
