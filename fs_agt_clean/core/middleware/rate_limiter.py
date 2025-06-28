"""
Rate limiting middleware for FlipSync API.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Dict, Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter implementation."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()

    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for the given identifier."""
        async with self.lock:
            now = time.time()
            window_start = now - self.window_seconds

            # Clean old requests
            request_times = self.requests[identifier]
            while request_times and request_times[0] < window_start:
                request_times.popleft()

            # Check if under limit
            if len(request_times) < self.max_requests:
                request_times.append(now)
                return True

            return False

    def get_reset_time(self, identifier: str) -> int:
        """Get the time when the rate limit resets."""
        request_times = self.requests[identifier]
        if not request_times:
            return int(time.time())

        return int(request_times[0] + self.window_seconds)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""

    def __init__(self, app, calls_per_minute: int = 100, burst_limit: int = 20):
        super().__init__(app)

        # Different rate limits for different types of requests
        self.general_limiter = RateLimiter(calls_per_minute, 60)  # General API calls
        self.burst_limiter = RateLimiter(
            burst_limit, 10
        )  # Burst protection (10 seconds)
        self.auth_limiter = RateLimiter(
            500, 60
        )  # Authentication endpoints - support 100+ concurrent users
        self.upload_limiter = RateLimiter(5, 60)  # File upload endpoints

        # Exempt paths from rate limiting
        self.exempt_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        }

    def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get real IP from headers (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Include user agent for additional fingerprinting
        user_agent = request.headers.get("UnifiedUser-UnifiedAgent", "")[:50]  # Limit length

        return f"{client_ip}:{hash(user_agent) % 10000}"

    def get_rate_limiter(self, request: Request) -> RateLimiter:
        """Get appropriate rate limiter based on request path."""
        path = request.url.path

        # Authentication endpoints - stricter limits
        if any(auth_path in path for auth_path in ["/auth", "/login", "/token"]):
            return self.auth_limiter

        # Upload endpoints - stricter limits
        if any(upload_path in path for upload_path in ["/upload", "/file"]):
            return self.upload_limiter

        # Default to general limiter
        return self.general_limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""

        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Skip rate limiting for WebSocket connections
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        client_id = self.get_client_identifier(request)

        # Check burst protection first, but exempt authentication endpoints for concurrent users
        path = request.url.path
        is_auth_endpoint = any(
            auth_path in path for auth_path in ["/auth", "/login", "/token"]
        )

        # For auth endpoints, use a more lenient burst check to allow concurrent authentication
        if not is_auth_endpoint and not await self.burst_limiter.is_allowed(client_id):
            logger.warning(f"Burst rate limit exceeded for client: {client_id}")
            return self._create_rate_limit_response(
                "Too many requests in short time",
                self.burst_limiter.get_reset_time(client_id),
            )

        # Check general rate limit
        rate_limiter = self.get_rate_limiter(request)
        if not await rate_limiter.is_allowed(client_id):
            logger.warning(
                f"Rate limit exceeded for client: {client_id} on path: {request.url.path}"
            )
            return self._create_rate_limit_response(
                "Rate limit exceeded", rate_limiter.get_reset_time(client_id)
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Window"] = str(rate_limiter.window_seconds)
        response.headers["X-RateLimit-Reset"] = str(
            rate_limiter.get_reset_time(client_id)
        )

        return response

    def _create_rate_limit_response(self, message: str, reset_time: int) -> Response:
        """Create rate limit exceeded response."""
        return Response(
            content=f'{{"error": "{message}", "reset_time": {reset_time}}}',
            status_code=429,
            headers={
                "Content-Type": "application/json",
                "Retry-After": str(max(1, reset_time - int(time.time()))),
                "X-RateLimit-Reset": str(reset_time),
            },
        )


# Production rate limiting configuration
def create_production_rate_limiter() -> RateLimitMiddleware:
    """Create production-ready rate limiter with enhanced security."""
    return RateLimitMiddleware(
        app=None,  # Will be set by FastAPI
        calls_per_minute=1000,  # 1000 calls per minute for production
        burst_limit=50,  # 50 calls in 10 seconds burst protection
    )


# Enhanced production rate limiter with IP blocking
class ProductionRateLimiter(RateLimitMiddleware):
    """Production-grade rate limiter with advanced features."""

    def __init__(self, app, calls_per_minute: int = 1000, burst_limit: int = 50):
        super().__init__(app, calls_per_minute, burst_limit)

        # Enhanced rate limits for production
        self.auth_limiter = RateLimiter(
            500, 60
        )  # Production auth limits - support 100+ concurrent users
        self.api_limiter = RateLimiter(calls_per_minute, 60)
        self.upload_limiter = RateLimiter(3, 60)  # Very strict upload limits

        # IP blocking for repeated violations
        self.blocked_ips = {}
        self.violation_counts = defaultdict(int)
        self.block_duration = 3600  # 1 hour block

    def is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is currently blocked."""
        if client_ip in self.blocked_ips:
            if time.time() < self.blocked_ips[client_ip]:
                return True
            else:
                # Block expired, remove it
                del self.blocked_ips[client_ip]
                self.violation_counts[client_ip] = 0
        return False

    def block_ip(self, client_ip: str, duration: int = None):
        """Block an IP address for specified duration."""
        block_time = duration or self.block_duration
        self.blocked_ips[client_ip] = time.time() + block_time
        logger.warning(f"Blocked IP {client_ip} for {block_time} seconds")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Enhanced dispatch with IP blocking."""
        client_ip = self.get_client_identifier(request)

        # Check if IP is blocked
        if self.is_ip_blocked(client_ip):
            return Response(
                content='{"error": "IP address blocked due to rate limit violations"}',
                status_code=429,
                headers={"Content-Type": "application/json"},
            )

        # Call parent dispatch
        response = await super().dispatch(request, call_next)

        # Track violations and block repeat offenders
        if response.status_code == 429:
            self.violation_counts[client_ip] += 1
            if self.violation_counts[client_ip] >= 5:  # 5 violations = block
                self.block_ip(client_ip)

        return response


# Development rate limiting configuration
def create_development_rate_limiter() -> RateLimitMiddleware:
    """Create development-friendly rate limiter."""
    return RateLimitMiddleware(
        app=None,  # Will be set by FastAPI
        calls_per_minute=10000,  # Higher limit for development
        burst_limit=100,  # Higher burst limit for development
    )
