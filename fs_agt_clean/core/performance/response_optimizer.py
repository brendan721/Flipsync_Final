"""
Response optimization middleware for FlipSync API.
Implements caching, compression, and response time monitoring.
"""

import asyncio
import gzip
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class ResponseCache:
    """Simple in-memory response cache with TTL."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.access_times: Dict[str, float] = {}

    def _generate_key(self, request: Request) -> str:
        """Generate cache key from request."""
        # Only cache GET requests
        if request.method != "GET":
            return None

        # Skip caching for authenticated requests (for now)
        if "authorization" in request.headers:
            return None

        # Generate key from path and query params
        key = f"{request.url.path}?{request.url.query}"
        return key

    def get(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired."""
        key = self._generate_key(request)
        if not key or key not in self.cache:
            return None

        cached_item = self.cache[key]

        # Check if expired
        if time.time() > cached_item["expires_at"]:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return None

        # Update access time
        self.access_times[key] = time.time()
        return cached_item["response"]

    def set(
        self, request: Request, response_data: Dict[str, Any], ttl: Optional[int] = None
    ):
        """Cache response data."""
        key = self._generate_key(request)
        if not key:
            return

        # Evict oldest items if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        ttl = ttl or self.default_ttl
        self.cache[key] = {
            "response": response_data,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
        }
        self.access_times[key] = time.time()

    def _evict_oldest(self):
        """Evict the least recently accessed item."""
        if not self.access_times:
            return

        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        if oldest_key in self.cache:
            del self.cache[oldest_key]
        del self.access_times[oldest_key]


class ResponseTimeMonitor:
    """Monitor API response times and track performance metrics."""

    def __init__(self, window_size: int = 1000):
        self.response_times: deque = deque(maxlen=window_size)
        self.endpoint_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.slow_requests: List[Dict[str, Any]] = []
        self.slow_threshold_ms = 200  # 200ms threshold

    def record_response_time(self, request: Request, response_time_ms: float):
        """Record response time for monitoring."""
        self.response_times.append(response_time_ms)

        # Track by endpoint
        endpoint = f"{request.method} {request.url.path}"
        self.endpoint_times[endpoint].append(response_time_ms)

        # Track slow requests
        if response_time_ms > self.slow_threshold_ms:
            self.slow_requests.append(
                {
                    "endpoint": endpoint,
                    "response_time_ms": response_time_ms,
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_params": str(request.query_params),
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )

            # Keep only recent slow requests
            if len(self.slow_requests) > 100:
                self.slow_requests = self.slow_requests[-100:]

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.response_times:
            return {"message": "No data available"}

        times = list(self.response_times)
        times.sort()

        return {
            "total_requests": len(times),
            "avg_response_time_ms": sum(times) / len(times),
            "median_response_time_ms": times[len(times) // 2],
            "p95_response_time_ms": (
                times[int(len(times) * 0.95)] if len(times) > 20 else times[-1]
            ),
            "p99_response_time_ms": (
                times[int(len(times) * 0.99)] if len(times) > 100 else times[-1]
            ),
            "slow_requests_count": len(
                [t for t in times if t > self.slow_threshold_ms]
            ),
            "fastest_response_ms": min(times),
            "slowest_response_ms": max(times),
        }


class ResponseOptimizationMiddleware(BaseHTTPMiddleware):
    """Middleware for response optimization including caching and compression."""

    def __init__(
        self,
        app,
        enable_caching: bool = True,
        enable_compression: bool = True,
        cache_size: int = 1000,
        cache_ttl: int = 300,
        compression_threshold: int = 1024,
    ):
        super().__init__(app)
        self.enable_caching = enable_caching
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold

        # Initialize cache and monitor
        self.cache = (
            ResponseCache(max_size=cache_size, default_ttl=cache_ttl)
            if enable_caching
            else None
        )
        self.monitor = ResponseTimeMonitor()

        # Cacheable endpoints (GET requests only)
        self.cacheable_paths = {
            "/api/v1/products",
            "/api/v1/categories",
            "/api/v1/health",
            "/api/v1/analytics/dashboard",
        }

        # Compressible content types
        self.compressible_types = {
            "application/json",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with optimization."""
        start_time = time.time()

        # Try cache first (for GET requests)
        if self.enable_caching and self.cache and request.method == "GET":
            cached_response = self.cache.get(request)
            if cached_response:
                response = JSONResponse(content=cached_response)
                response.headers["X-Cache"] = "HIT"

                # Record cache hit time
                response_time_ms = (time.time() - start_time) * 1000
                self.monitor.record_response_time(request, response_time_ms)
                response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"

                return response

        # Process request
        response = await call_next(request)
        response_time_ms = (time.time() - start_time) * 1000

        # Record response time
        self.monitor.record_response_time(request, response_time_ms)
        response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"

        # Cache successful GET responses
        if (
            self.enable_caching
            and self.cache
            and request.method == "GET"
            and response.status_code == 200
            and any(path in request.url.path for path in self.cacheable_paths)
        ):

            try:
                # Only cache JSON responses
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    response_body = b""
                    async for chunk in response.body_iterator:
                        response_body += chunk

                    response_data = json.loads(response_body.decode())
                    self.cache.set(request, response_data)
                    response.headers["X-Cache"] = "MISS"

                    # Recreate response with cached data
                    response = JSONResponse(content=response_data)
                    response.headers["X-Cache"] = "MISS"
                    response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"

            except Exception as e:
                logger.warning(f"Failed to cache response: {e}")

        # Apply compression if enabled and beneficial
        if (
            self.enable_compression
            and response.status_code == 200
            and "gzip" in request.headers.get("accept-encoding", "")
            and response.headers.get("content-type", "").split(";")[0]
            in self.compressible_types
        ):

            try:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Only compress if above threshold
                if len(response_body) > self.compression_threshold:
                    compressed_body = gzip.compress(response_body)

                    # Only use compression if it actually reduces size
                    if len(compressed_body) < len(response_body):
                        response.headers["content-encoding"] = "gzip"
                        response.headers["content-length"] = str(len(compressed_body))

                        # Create new response with compressed body
                        response = Response(
                            content=compressed_body,
                            status_code=response.status_code,
                            headers=dict(response.headers),
                            media_type=response.media_type,
                        )
                        response.headers["X-Response-Time"] = (
                            f"{response_time_ms:.2f}ms"
                        )

            except Exception as e:
                logger.warning(f"Failed to compress response: {e}")

        return response

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self.monitor.get_stats()

        if self.cache:
            stats["cache"] = {
                "size": len(self.cache.cache),
                "max_size": self.cache.max_size,
                "hit_rate": "N/A",  # Would need to track hits/misses
            }

        return stats


# Factory functions for different environments
def create_production_optimizer() -> ResponseOptimizationMiddleware:
    """Create production-optimized middleware."""
    return ResponseOptimizationMiddleware(
        app=None,
        enable_caching=True,
        enable_compression=True,
        cache_size=2000,
        cache_ttl=600,  # 10 minutes
        compression_threshold=512,
    )


def create_development_optimizer() -> ResponseOptimizationMiddleware:
    """Create development-friendly middleware."""
    return ResponseOptimizationMiddleware(
        app=None,
        enable_caching=False,  # Disable caching in development
        enable_compression=False,  # Disable compression in development
        cache_size=100,
        cache_ttl=60,
        compression_threshold=1024,
    )
