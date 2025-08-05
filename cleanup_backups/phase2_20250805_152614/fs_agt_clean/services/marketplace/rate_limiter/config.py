"""Rate limiter configuration for marketplace services."""

from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """Rate limit configuration for marketplace services."""

    requests_per_second: float
    burst_limit: int
    retry_after: int = 1
