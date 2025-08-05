"""Rate limiter protocol for marketplace services."""

from typing import Protocol, Tuple


class RateLimiterProtocol(Protocol):
    """Protocol for rate limiters."""

    async def check_limit(self, key: str, action: str) -> Tuple[bool, int]:
        """
        Check if a request is allowed under the rate limit.

        Args:
            key: Rate limit key
            action: Action to check limit for

        Returns:
            Tuple of (is_allowed, current_count)
        """
        ...
