"""
Security Middleware for FastAPI

This module provides security middleware for FastAPI applications:
1. SecurityHeadersMiddleware - Adds security headers to responses
2. HTTPSRedirectMiddleware - Redirects HTTP requests to HTTPS

Usage:
    app = FastAPI()
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Protocol, Union

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.types import ASGIApp

from fs_agt_clean.core.security.security_hardening import (
    SecurityEvent,
    input_validator,
    rate_limiter,
    threat_detector,
)

logger = logging.getLogger(__name__)

# Default security headers that should be applied to all responses
DEFAULT_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
    "Cache-Control": "no-store, max-age=0",
}

# Default CSP that allows only necessary resources
DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "media-src 'self'; "
    "object-src 'none'; "
    "child-src 'none'; "
    "frame-ancestors 'none'; "
    "form-action 'self'; "
    "base-uri 'self'; "
    "block-all-mixed-content"
)

# Default HSTS settings for production
DEFAULT_HSTS = "max-age=31536000; includeSubDomains"


class SSLServiceProtocol(Protocol):
    """Protocol defining the interface for SSL service objects."""

    def get_config(self) -> Dict[str, Any]:
        """Get SSL configuration."""
        pass


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS.

    This middleware should be one of the first in the middleware stack to
    ensure that all requests are served over HTTPS in production environments.
    """

    def __init__(
        self,
        app: ASGIApp,
        status_code: int = 301,
        exclude_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the HTTPS redirect middleware.

        Args:
            app: The ASGI application
            status_code: HTTP status code for the redirect (301 or 307 recommended)
            exclude_paths: List of paths to exclude from redirection
        """
        super().__init__(app)
        self.status_code = status_code
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Dispatch the middleware.

        If the request is not secure (HTTP), redirect to HTTPS.
        If the request is already secure or the app is in debug mode, pass through.
        """
        # Skip redirect for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Skip redirect for health check endpoints
        if request.url.path.startswith("/health"):
            return await call_next(request)

        # Check if we need to redirect (not secure and not localhost)
        if (
            not request.url.is_secure
            and request.url.hostname
            and "localhost" not in request.url.hostname
            and "127.0.0.1" not in request.url.hostname
        ):
            # Construct HTTPS URL with the same path
            https_url = str(request.url.replace(scheme="https"))
            return RedirectResponse(https_url, status_code=self.status_code)

        # Pass through for secure requests
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    This middleware adds various security headers to HTTP responses to enhance
    security by preventing common web vulnerabilities like XSS, clickjacking, etc.
    """

    def __init__(
        self,
        app: ASGIApp,
        hsts: Optional[Union[str, bool]] = None,
        csp: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        ssl_service: Optional[SSLServiceProtocol] = None,
    ):
        """
        Initialize the security headers middleware.

        Args:
            app: The ASGI application
            hsts: HSTS header value or True to use default (disable with False/None)
            csp: Content-Security-Policy value (uses DEFAULT_CSP if None)
            headers: Additional headers to add/override defaults
            ssl_service: Optional SSL service with get_config method
        """
        super().__init__(app)

        # Start with default headers
        self.headers = DEFAULT_SECURITY_HEADERS.copy()

        # Add Content-Security-Policy
        if csp is not None:
            self.headers["Content-Security-Policy"] = csp
        else:
            self.headers["Content-Security-Policy"] = DEFAULT_CSP

        # Add HSTS if enabled (default in production)
        # HSTS should only be enabled in production with HTTPS
        if hsts is True:
            self.headers["Strict-Transport-Security"] = DEFAULT_HSTS
        elif isinstance(hsts, str):
            self.headers["Strict-Transport-Security"] = hsts

        # Override with custom headers if provided
        if headers:
            self.headers.update(headers)

        # Use SSL service configuration if provided
        self.ssl_service = ssl_service
        if ssl_service:
            try:
                ssl_config = ssl_service.get_config()
                if ssl_config:
                    # Update headers based on SSL service configuration
                    if ssl_config.get("hsts_enabled", False):
                        hsts_value = ssl_config.get("hsts_value", DEFAULT_HSTS)
                        self.headers["Strict-Transport-Security"] = hsts_value

                    if ssl_config.get("csp"):
                        self.headers["Content-Security-Policy"] = ssl_config.get("csp")
            except Exception as e:
                logger.warning(f"Failed to load SSL configuration: {str(e)}")

        # Log the configured headers at debug level
        logger.debug(f"Security headers configured: {self.headers}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Dispatch the middleware.

        Add security headers to the response.
        """
        # Process the request and get the response
        response = await call_next(request)

        # Add security headers to the response
        for header_name, header_value in self.headers.items():
            response.headers[header_name] = header_value

        # For API routes, ensure proper content type
        if request.url.path.startswith("/api/"):
            if "Content-Type" not in response.headers:
                response.headers["Content-Type"] = "application/json"

        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect against CSRF attacks.

    This middleware implements custom CSRF protection for API endpoints.
    It should be used alongside proper CSRF token management in the application.
    """

    def __init__(
        self,
        app: ASGIApp,
        csrf_header: str = "X-CSRF-Token",
        csrf_cookie: str = "csrftoken",
        safe_methods: Optional[List[str]] = None,
        protected_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the CSRF protection middleware.

        Args:
            app: The ASGI application
            csrf_header: The name of the CSRF header
            csrf_cookie: The name of the CSRF cookie
            safe_methods: HTTP methods that don't require CSRF protection
            protected_paths: Paths that require CSRF protection (defaults to all /api paths)
        """
        super().__init__(app)
        self.csrf_header = csrf_header
        self.csrf_cookie = csrf_cookie
        self.safe_methods = safe_methods or ["GET", "HEAD", "OPTIONS"]
        self.protected_paths = protected_paths or ["/api/"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Dispatch the middleware.

        Check for valid CSRF token on protected paths and unsafe methods.
        """
        # Skip CSRF checks for safe methods
        if request.method in self.safe_methods:
            return await call_next(request)

        # Skip CSRF checks for non-protected paths
        if not any(request.url.path.startswith(path) for path in self.protected_paths):
            return await call_next(request)

        # Get the CSRF token from header and cookie
        csrf_token_header = request.headers.get(self.csrf_header)
        csrf_token_cookie = request.cookies.get(self.csrf_cookie)

        # If API key authentication is used, skip CSRF check
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # API key or JWT token auth doesn't need CSRF protection
            return await call_next(request)

        # For endpoints that require CSRF protection
        if (
            not csrf_token_header
            or not csrf_token_cookie
            or csrf_token_header != csrf_token_cookie
        ):
            # CSRF token missing or invalid
            return Response(
                content='{"detail":"CSRF token missing or incorrect"}',
                status_code=403,
                media_type="application/json",
            )

        # Token is valid, proceed with the request
        return await call_next(request)


class AdvancedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Advanced security middleware with rate limiting, input validation, and threat detection.

    This middleware provides comprehensive security hardening including:
    - Advanced rate limiting with burst protection
    - Input validation and sanitization
    - Threat detection and response
    - Security event logging
    """

    def __init__(self, app: ASGIApp):
        """Initialize the advanced security middleware."""
        super().__init__(app)
        logger.info("Advanced Security Middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Dispatch the middleware with comprehensive security checks.
        """
        start_time = datetime.now(timezone.utc)
        client_ip = self._get_client_ip(request)

        try:
            # 1. Check if IP is marked as suspicious
            if threat_detector.is_suspicious_ip(client_ip):
                threat_score = threat_detector.get_threat_score(client_ip)
                logger.warning(
                    f"Blocking request from suspicious IP {client_ip} (threat score: {threat_score})"
                )

                # Record security event
                threat_detector.record_security_event(
                    SecurityEvent(
                        event_type="blocked_request",
                        source_ip=client_ip,
                        user_id=getattr(request.state, "user_id", None),
                        endpoint=request.url.path,
                        timestamp=start_time,
                        severity="high",
                        details={
                            "reason": "suspicious_ip",
                            "threat_score": threat_score,
                        },
                    )
                )

                return JSONResponse(
                    status_code=429,
                    content={"detail": "Request blocked due to suspicious activity"},
                )

            # 2. Rate limiting check
            if not await rate_limiter.check_rate_limit(request):
                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {request.url.path}"
                )

                # Record security event
                threat_detector.record_security_event(
                    SecurityEvent(
                        event_type="rate_limit_exceeded",
                        source_ip=client_ip,
                        user_id=getattr(request.state, "user_id", None),
                        endpoint=request.url.path,
                        timestamp=start_time,
                        severity="medium",
                        details={"method": request.method},
                    )
                )

                return JSONResponse(
                    status_code=429, content={"detail": "Rate limit exceeded"}
                )

            # 3. Input validation for POST/PUT/PATCH requests
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_request_input(request, client_ip, start_time)

            # Process the request
            response = await call_next(request)

            # Add security headers if not already present
            self._add_security_headers(response)

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {e}")

            # Record security event for errors
            threat_detector.record_security_event(
                SecurityEvent(
                    event_type="middleware_error",
                    source_ip=client_ip,
                    user_id=getattr(request.state, "user_id", None),
                    endpoint=request.url.path,
                    timestamp=start_time,
                    severity="medium",
                    details={"error": str(e)},
                )
            )

            # Continue with request processing
            return await call_next(request)

    async def _validate_request_input(
        self, request: Request, client_ip: str, start_time: datetime
    ):
        """Validate request input for security threats."""
        try:
            # Get request body if present
            if hasattr(request, "_body"):
                body = request._body
            else:
                body = await request.body()

            if body:
                try:
                    # Try to parse as JSON
                    data = json.loads(body.decode())

                    # Validate the data
                    validation_result = input_validator.validate_request_data(data)

                    if not validation_result["valid"]:
                        logger.warning(
                            f"Suspicious input detected from {client_ip}: {validation_result['warnings']}"
                        )

                        # Record security event
                        threat_detector.record_security_event(
                            SecurityEvent(
                                event_type="suspicious_input",
                                source_ip=client_ip,
                                user_id=getattr(request.state, "user_id", None),
                                endpoint=request.url.path,
                                timestamp=start_time,
                                severity="high",
                                details={
                                    "blocked_patterns": validation_result[
                                        "blocked_patterns"
                                    ],
                                    "warnings": validation_result["warnings"],
                                },
                            )
                        )

                        raise HTTPException(
                            status_code=400, detail="Invalid input detected"
                        )

                except json.JSONDecodeError:
                    # Not JSON data, skip validation
                    pass
                except UnicodeDecodeError:
                    # Binary data, skip validation
                    pass

        except Exception as e:
            logger.debug(f"Input validation error: {e}")
            # Don't block request for validation errors
            pass

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    def _add_security_headers(self, response: Response):
        """Add additional security headers to response."""
        # Add security headers if not already present
        security_headers = {
            "X-Security-Hardened": "true",
            "X-Rate-Limited": "true",
            "X-Input-Validated": "true",
        }

        for header, value in security_headers.items():
            if header not in response.headers:
                response.headers[header] = value
