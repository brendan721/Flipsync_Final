"""Rate limiter implementation for marketplace services."""

import asyncio
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

from fs_agt_clean.services.marketplace.rate_limiter.config import RateLimitConfig
from fs_agt_clean.services.marketplace.rate_limiter.protocol import RateLimiterProtocol


class RateLimiter(RateLimiterProtocol):
    """Token bucket rate limiter implementation."""

    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.tokens: float = float(config.burst_limit)
        self.last_update = time.time()
        self._lock = asyncio.Lock()
        self._counters: Dict[str, Dict[str, float]] = {}

    async def check_limit(self, key: str, action: str) -> Tuple[bool, int]:
        """
        Check if a request is allowed under the rate limit.

        Args:
            key: Rate limit key
            action: Action to check limit for

        Returns:
            Tuple of (is_allowed, current_count)
        """
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(
                self.config.burst_limit,
                self.tokens + time_passed * self.config.requests_per_second,
            )
            self.last_update = now

            if self.tokens < 1:
                return False, 0

            self.tokens -= 1
            return True, int(self.tokens)

    async def wait_for_token(self, key: str, action: str) -> None:
        """
        Wait until a token is available.

        Args:
            key: Rate limit key
            action: Action to check limit for
        """
        while True:
            allowed, _ = await self.check_limit(key, action)
            if allowed:
                return
            await asyncio.sleep(self.config.retry_after)
