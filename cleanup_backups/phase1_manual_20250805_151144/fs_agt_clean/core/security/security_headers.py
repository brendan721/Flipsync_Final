"""
Security Headers Middleware for FlipSync
========================================

Provides security headers middleware to enhance application security.
"""

import logging
from typing import Callable, Dict, Optional, Union

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Default security headers
DEFAULT_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


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
    ):
        """
        Initialize the security headers middleware.

        Args:
            app: The ASGI application
            hsts: HSTS header value or True to use default (disable with False/None)
            csp: Content-Security-Policy value (uses default if None)
            headers: Additional headers to add/override defaults
        """
        super().__init__(app)

        # Start with default headers
        self.headers = DEFAULT_SECURITY_HEADERS.copy()

        # Override with custom headers if provided
        if headers:
            self.headers.update(headers)

        # Handle HSTS configuration
        if hsts is False or hsts is None:
            self.headers.pop("Strict-Transport-Security", None)
        elif isinstance(hsts, str):
            self.headers["Strict-Transport-Security"] = hsts

        # Handle CSP configuration
        if csp:
            self.headers["Content-Security-Policy"] = csp

        logger.info(
            "SecurityHeadersMiddleware initialized with headers: %s",
            list(self.headers.keys()),
        )

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
