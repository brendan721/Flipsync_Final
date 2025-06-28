"""API metrics collection for FlipSync.

This module provides comprehensive metrics collection for API endpoints,
including request counts, latencies, error rates, and business metrics.
"""

import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

from fs_agt_clean.core.config.manager import manager as config_manager
from fs_agt_clean.core.utils.logging import get_logger

logger = get_logger(__name__)


# Define metrics
API_REQUEST_COUNT = Counter(
    "flipsync_api_requests_total",
    "Total count of API requests",
    ["method", "endpoint", "status", "version", "environment"],
)

API_REQUEST_LATENCY = Histogram(
    "flipsync_api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "endpoint", "version", "environment"],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
)

API_REQUEST_SIZE = Histogram(
    "flipsync_api_request_size_bytes",
    "API request size in bytes",
    ["method", "endpoint", "version", "environment"],
    buckets=[10, 100, 1000, 10000, 100000, 1000000],
)

API_RESPONSE_SIZE = Histogram(
    "flipsync_api_response_size_bytes",
    "API response size in bytes",
    ["method", "endpoint", "status", "version", "environment"],
    buckets=[10, 100, 1000, 10000, 100000, 1000000],
)

API_ERROR_COUNT = Counter(
    "flipsync_api_errors_total",
    "Total count of API errors",
    ["method", "endpoint", "error_type", "version", "environment"],
)

API_ACTIVE_REQUESTS = Gauge(
    "flipsync_api_active_requests",
    "Number of active API requests",
    ["method", "endpoint", "version", "environment"],
)

API_RATE_LIMIT_HITS = Counter(
    "flipsync_api_rate_limit_hits_total",
    "Total count of rate limit hits",
    ["method", "endpoint", "client_ip", "version", "environment"],
)

API_AUTHENTICATION_FAILURES = Counter(
    "flipsync_api_authentication_failures_total",
    "Total count of authentication failures",
    ["method", "endpoint", "version", "environment"],
)

API_BUSINESS_OPERATIONS = Counter(
    "flipsync_api_business_operations_total",
    "Total count of business operations",
    ["operation_type", "status", "version", "environment"],
)

API_BUSINESS_OPERATION_LATENCY = Histogram(
    "flipsync_api_business_operation_duration_seconds",
    "Business operation latency in seconds",
    ["operation_type", "version", "environment"],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
)

API_DATABASE_OPERATIONS = Counter(
    "flipsync_api_database_operations_total",
    "Total count of database operations",
    ["operation_type", "status", "version", "environment"],
)

API_DATABASE_OPERATION_LATENCY = Histogram(
    "flipsync_api_database_operation_duration_seconds",
    "Database operation latency in seconds",
    ["operation_type", "version", "environment"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0],
)

API_EXTERNAL_SERVICE_CALLS = Counter(
    "flipsync_api_external_service_calls_total",
    "Total count of external service calls",
    ["service", "operation", "status", "version", "environment"],
)

API_EXTERNAL_SERVICE_LATENCY = Histogram(
    "flipsync_api_external_service_duration_seconds",
    "External service call latency in seconds",
    ["service", "operation", "version", "environment"],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
)


class APIMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting comprehensive API metrics."""

    def __init__(self, app: FastAPI):
        """Initialize the middleware.

        Args:
            app: The FastAPI application
        """
        super().__init__(app)
        self.app = app
        self.environment = config_manager.get_environment()
        self.api_version = config_manager.get("api.version", "v1")
        logger.info(
            f"API metrics middleware initialized for environment: {self.environment}, version: {self.api_version}"
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        """Process the request and collect metrics.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            The response from the next handler
        """
        # Extract request information
        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)
        start_time = time.time()
        request_size = int(request.headers.get("content-length", 0))

        # Track active requests
        API_ACTIVE_REQUESTS.labels(
            method=method,
            endpoint=endpoint,
            version=self.api_version,
            environment=self.environment,
        ).inc()

        # Record request size
        API_REQUEST_SIZE.labels(
            method=method,
            endpoint=endpoint,
            version=self.api_version,
            environment=self.environment,
        ).observe(request_size)

        try:
            # Process the request
            response = await call_next(request)

            # Extract response information
            status_code = response.status_code
            response_size = int(response.headers.get("content-length", 0))
            duration = time.time() - start_time

            # Record metrics
            API_REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code),
                version=self.api_version,
                environment=self.environment,
            ).inc()

            API_REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint,
                version=self.api_version,
                environment=self.environment,
            ).observe(duration)

            API_RESPONSE_SIZE.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code),
                version=self.api_version,
                environment=self.environment,
            ).observe(response_size)

            # Check for rate limiting
            if status_code == 429:
                API_RATE_LIMIT_HITS.labels(
                    method=method,
                    endpoint=endpoint,
                    client_ip=self._get_client_ip(request),
                    version=self.api_version,
                    environment=self.environment,
                ).inc()

            # Check for authentication failures
            if status_code == 401:
                API_AUTHENTICATION_FAILURES.labels(
                    method=method,
                    endpoint=endpoint,
                    version=self.api_version,
                    environment=self.environment,
                ).inc()

            return response

        except Exception as e:
            # Record error metrics
            error_type = type(e).__name__
            API_ERROR_COUNT.labels(
                method=method,
                endpoint=endpoint,
                error_type=error_type,
                version=self.api_version,
                environment=self.environment,
            ).inc()
            logger.error(f"API error: {error_type} in {method} {endpoint}: {str(e)}")
            raise
        finally:
            # Decrement active requests counter
            API_ACTIVE_REQUESTS.labels(
                method=method,
                endpoint=endpoint,
                version=self.api_version,
                environment=self.environment,
            ).dec()

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize the endpoint path for consistent metrics.

        Args:
            path: The raw URL path

        Returns:
            Normalized endpoint path
        """
        # Replace numeric IDs with placeholders
        import re

        # Replace UUIDs with {id}
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
        )

        # Replace numeric IDs with {id}
        path = re.sub(r"/\d+", "/{id}", path)

        return path

    def _get_client_ip(self, request: Request) -> str:
        """Get the client IP address from the request.

        Args:
            request: The incoming request

        Returns:
            Client IP address
        """
        # Try X-Forwarded-For header first (for clients behind proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fall back to client.host
        return request.client.host if request.client else "unknown"


def track_business_operation(operation_type: str):
    """Decorator to track business operations.

    Args:
        operation_type: Type of business operation
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            environment = config_manager.get_environment()
            api_version = config_manager.get("api.version", "v1")
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                API_BUSINESS_OPERATIONS.labels(
                    operation_type=operation_type,
                    status=status,
                    version=api_version,
                    environment=environment,
                ).inc()
                API_BUSINESS_OPERATION_LATENCY.labels(
                    operation_type=operation_type,
                    version=api_version,
                    environment=environment,
                ).observe(duration)

        return wrapper

    return decorator


def track_database_operation(operation_type: str):
    """Decorator to track database operations.

    Args:
        operation_type: Type of database operation
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            environment = config_manager.get_environment()
            api_version = config_manager.get("api.version", "v1")
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                API_DATABASE_OPERATIONS.labels(
                    operation_type=operation_type,
                    status=status,
                    version=api_version,
                    environment=environment,
                ).inc()
                API_DATABASE_OPERATION_LATENCY.labels(
                    operation_type=operation_type,
                    version=api_version,
                    environment=environment,
                ).observe(duration)

        return wrapper

    return decorator


def track_external_service(service: str, operation: str):
    """Decorator to track external service calls.

    Args:
        service: Name of the external service
        operation: Type of operation
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            environment = config_manager.get_environment()
            api_version = config_manager.get("api.version", "v1")
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                API_EXTERNAL_SERVICE_CALLS.labels(
                    service=service,
                    operation=operation,
                    status=status,
                    version=api_version,
                    environment=environment,
                ).inc()
                API_EXTERNAL_SERVICE_LATENCY.labels(
                    service=service,
                    operation=operation,
                    version=api_version,
                    environment=environment,
                ).observe(duration)

        return wrapper

    return decorator


def setup_api_metrics(app: FastAPI) -> None:
    """Set up API metrics collection for a FastAPI application.

    Args:
        app: The FastAPI application
    """
    # Add metrics middleware
    app.add_middleware(APIMetricsMiddleware)
    logger.info("API metrics middleware added to FastAPI application")
