"""Rate limiter implementation using Redis."""

import time
from dataclasses import dataclass
from typing import Dict, Optional

from redis.asyncio import Redis

from fs_agt_clean.core.redis.redis_manager import RedisManager
from fs_agt_clean.core.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    requests: int  # Number of requests allowed
    window: int  # Time window in seconds
    key_prefix: str = "rate_limit"


class RateLimiter:
    """Rate limiter implementation using Redis sliding window."""

    def __init__(
        self, redis: RedisManager, config: Optional[Dict[str, RateLimitConfig]] = None
    ):
        """Initialize rate limiter.

        Args:
            redis: Redis manager instance
            config: Rate limit configurations by endpoint/action
        """
        self.redis_client = redis.client
        self.config = config or {}
        self._script = None

    async def initialize(self):
        """Initialize rate limiter."""
        # Load Redis Lua script
        self._script = await self.redis_client.script_load(
            """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local window = tonumber(ARGV[2])
            local max_requests = tonumber(ARGV[3])

            -- Clean old requests
            redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

            -- Count requests in current window
            local count = redis.call('ZCARD', key)

            -- Check if limit exceeded
            if count >= max_requests then
                return {0, count}
            end

            -- Add new request
            redis.call('ZADD', key, now, now .. '-' .. math.random())
            redis.call('EXPIRE', key, window)

            return {1, count + 1}
        """
        )

    async def is_allowed(
        self, key: str, action: str, user_id: Optional[str] = None
    ) -> tuple[bool, int]:
        """Check if request is allowed under rate limit.

        Args:
            key: Rate limit key (e.g. IP address)
            action: Action being rate limited
            user_id: Optional user ID for per-user limits

        Returns:
            Tuple of (is_allowed, current_count)
        """
        try:
            config = self.config.get(action)
            if not config:
                # No rate limit configured
                return True, 0

            # Build redis key
            redis_key = f"{config.key_prefix}:{action}"
            if user_id:
                redis_key = f"{redis_key}:{user_id}"
            redis_key = f"{redis_key}:{key}"

            # Execute rate limit script
            now = int(time.time())
            result = await self.redis_client.evalsha(
                self._script,
                1,  # Number of keys
                redis_key,  # KEYS[1]
                now,  # ARGV[1]
                config.window,  # ARGV[2]
                config.requests,  # ARGV[3]
            )

            is_allowed = bool(result[0])
            current_count = int(result[1])

            if not is_allowed:
                logger.warning(
                    "Rate limit exceeded for %s by %s%s",
                    action,
                    key,
                    (f" (user: {user_id})" if user_id else ""),
                )

            return is_allowed, current_count

        except Exception as e:
            logger.error("Rate limit check failed: %s", str(e))
            # Fail open - allow request if rate limiting fails
            return True, 0

    async def reset(self, key: str, action: str, user_id: Optional[str] = None) -> bool:
        """Reset rate limit counter.

        Args:
            key: Rate limit key to reset
            action: Action to reset
            user_id: Optional user ID for per-user limits

        Returns:
            bool: True if successful
        """
        try:
            config = self.config.get(action)
            if not config:
                return True

            # Build redis key
            redis_key = f"{config.key_prefix}:{action}"
            if user_id:
                redis_key = f"{redis_key}:{user_id}"
            redis_key = f"{redis_key}:{key}"

            # Delete rate limit key
            await self.redis_client.delete(redis_key)
            return True

        except Exception as e:
            logger.error("Failed to reset rate limit: %s", str(e))
            return False

    def configure_limit(self, action: str, config: RateLimitConfig):
        """Configure rate limit for an action.

        Args:
            action: Action to configure limit for
            config: Rate limit configuration
        """
        self.config[action] = config

    def remove_limit(self, action: str):
        """Remove rate limit configuration for an action.

        Args:
            action: Action to remove limit for
        """
        self.config.pop(action, None)
