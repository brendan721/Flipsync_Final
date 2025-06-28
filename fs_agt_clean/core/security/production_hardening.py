"""
FlipSync Production Security Hardening
Comprehensive security measures for production deployment
"""

import asyncio
import hashlib
import hmac
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from fastapi import HTTPException, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityConfig(BaseModel):
    """Production security configuration."""

    # HTTPS/TLS Configuration
    force_https: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True

    # Rate Limiting (Production Scale)
    rate_limit_requests_per_minute: int = 1000  # Support high traffic
    rate_limit_burst_requests: int = 50
    rate_limit_auth_requests_per_minute: int = 500  # Support 100+ concurrent users
    rate_limit_upload_requests_per_minute: int = 10

    # Request Validation
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_json_depth: int = 10
    max_array_length: int = 1000
    max_string_length: int = 10000

    # Security Headers
    content_security_policy: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self' wss: https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # IP Security
    blocked_ips: Set[str] = Field(default_factory=set)
    allowed_ips: Optional[Set[str]] = None  # None = allow all, Set = whitelist
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30

    # API Security
    require_api_key: bool = False  # Enable for production API access
    api_key_header: str = "X-API-Key"
    request_signing_required: bool = False  # Enable for high-security APIs

    # Monitoring
    enable_security_logging: bool = True
    log_failed_requests: bool = True
    log_suspicious_activity: bool = True


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce HTTPS in production."""

    def __init__(self, app, force_https: bool = True):
        super().__init__(app)
        self.force_https = force_https

    async def dispatch(self, request: Request, call_next):
        # Skip HTTPS enforcement for health checks and local development
        if not self.force_https or request.url.hostname in ["localhost", "127.0.0.1"]:
            return await call_next(request)

        # Check if request is HTTPS
        if request.url.scheme != "https":
            # Redirect to HTTPS
            https_url = request.url.replace(scheme="https")
            return Response(status_code=301, headers={"Location": str(https_url)})

        return await call_next(request)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request validation."""

    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.suspicious_patterns = [
            r"<script[^>]*>.*?</script>",  # XSS attempts
            r"javascript:",  # JavaScript injection
            r"data:text/html",  # Data URI XSS
            r"vbscript:",  # VBScript injection
            r"onload\s*=",  # Event handler injection
            r"onerror\s*=",  # Error handler injection
            r"eval\s*\(",  # Code evaluation
            r"expression\s*\(",  # CSS expression
            r"import\s+",  # ES6 import
            r"require\s*\(",  # Node.js require
            r"\.\./",  # Path traversal
            r"\.\.\\",  # Windows path traversal
            r"union\s+select",  # SQL injection
            r"drop\s+table",  # SQL injection
            r"insert\s+into",  # SQL injection
            r"delete\s+from",  # SQL injection
        ]
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns
        ]

    async def dispatch(self, request: Request, call_next):
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.config.max_request_size:
            logger.warning(
                f"Request size too large: {content_length} bytes from {self.get_client_ip(request)}"
            )
            return JSONResponse(
                status_code=413, content={"error": "Request entity too large"}
            )

        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
                "text/plain",
            ]
            if not any(allowed_type in content_type for allowed_type in allowed_types):
                logger.warning(
                    f"Invalid content type: {content_type} from {self.get_client_ip(request)}"
                )
                return JSONResponse(
                    status_code=415, content={"error": "Unsupported media type"}
                )

        # Check for suspicious patterns in URL and headers
        suspicious_found = False
        check_strings = [
            str(request.url),
            request.headers.get("user-agent", ""),
            request.headers.get("referer", ""),
        ]

        for check_string in check_strings:
            for pattern in self.compiled_patterns:
                if pattern.search(check_string):
                    suspicious_found = True
                    logger.warning(
                        f"Suspicious pattern detected in request from {self.get_client_ip(request)}: {pattern.pattern}"
                    )
                    break
            if suspicious_found:
                break

        if suspicious_found:
            return JSONResponse(status_code=400, content={"error": "Invalid request"})

        return await call_next(request)

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for security monitoring and alerting."""

    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Set[str] = set()
        self.suspicious_activity: Dict[str, int] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        start_time = time.time()

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(status_code=403, content={"error": "Access denied"})

        # Process request
        response = await call_next(request)
        processing_time = time.time() - start_time

        # Monitor for security events
        await self.monitor_security_events(
            request, response, client_ip, processing_time
        )

        return response

    async def monitor_security_events(
        self,
        request: Request,
        response: Response,
        client_ip: str,
        processing_time: float,
    ):
        """Monitor and log security events."""

        # Log failed authentication attempts
        if response.status_code == 401:
            await self.log_failed_attempt(client_ip, request.url.path)

        # Log suspicious activity
        if response.status_code in [400, 403, 404, 429]:
            self.suspicious_activity[client_ip] = (
                self.suspicious_activity.get(client_ip, 0) + 1
            )

            # Block IP if too many suspicious requests
            if self.suspicious_activity[client_ip] > 20:  # 20 suspicious requests
                self.block_ip(client_ip, "Excessive suspicious activity")

        # Log slow requests (potential DoS)
        if processing_time > 10.0:  # 10 seconds
            logger.warning(
                f"Slow request detected: {processing_time:.2f}s from {client_ip} to {request.url.path}"
            )

        # Log security events if enabled
        if self.config.enable_security_logging:
            await self.log_security_event(request, response, client_ip, processing_time)

    async def log_failed_attempt(self, client_ip: str, path: str):
        """Log and track failed authentication attempts."""
        now = datetime.now()

        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = []

        # Add current attempt
        self.failed_attempts[client_ip].append(now)

        # Clean old attempts (older than lockout duration)
        cutoff = now - timedelta(minutes=self.config.lockout_duration_minutes)
        self.failed_attempts[client_ip] = [
            attempt for attempt in self.failed_attempts[client_ip] if attempt > cutoff
        ]

        # Check if should block IP
        if len(self.failed_attempts[client_ip]) >= self.config.max_failed_attempts:
            self.block_ip(
                client_ip,
                f"Too many failed attempts: {len(self.failed_attempts[client_ip])}",
            )

    def block_ip(self, client_ip: str, reason: str):
        """Block an IP address."""
        self.blocked_ips.add(client_ip)
        logger.critical(f"IP BLOCKED: {client_ip} - Reason: {reason}")

        # TODO: Integrate with external security systems
        # - Add to firewall rules
        # - Send alert to security team
        # - Update threat intelligence feeds

    async def log_security_event(
        self,
        request: Request,
        response: Response,
        client_ip: str,
        processing_time: float,
    ):
        """Log security events for monitoring."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "processing_time": processing_time,
            "user_agent": request.headers.get("user-agent", ""),
            "referer": request.headers.get("referer", ""),
        }

        # Log to security monitoring system
        logger.info(f"SECURITY_EVENT: {json.dumps(event)}")

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class ProductionSecurityHeaders:
    """Production-ready security headers."""

    @staticmethod
    def get_headers(config: SecurityConfig) -> Dict[str, str]:
        """Get production security headers."""
        headers = {
            # HSTS
            "Strict-Transport-Security": f"max-age={config.hsts_max_age}; includeSubDomains; preload",
            # Content Security Policy
            "Content-Security-Policy": config.content_security_policy,
            # Frame Options
            "X-Frame-Options": "DENY",
            # Content Type Options
            "X-Content-Type-Options": "nosniff",
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), payment=(), "
                "usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
            ),
            # Hide server information
            "Server": "FlipSync",
            # Cache Control for sensitive endpoints
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
        }

        return headers


def create_production_security_middleware(app, config: Optional[SecurityConfig] = None):
    """Create and configure production security middleware stack."""
    if config is None:
        config = SecurityConfig()

    # Add HTTPS redirect middleware
    app.add_middleware(HTTPSRedirectMiddleware, force_https=config.force_https)

    # Add request validation middleware
    app.add_middleware(RequestValidationMiddleware, config=config)

    # Add security monitoring middleware
    app.add_middleware(SecurityMonitoringMiddleware, config=config)

    # Add security headers middleware
    @app.middleware("http")
    async def add_production_security_headers(request: Request, call_next):
        response = await call_next(request)

        # Add production security headers
        headers = ProductionSecurityHeaders.get_headers(config)
        for header, value in headers.items():
            response.headers[header] = value

        return response

    logger.info("Production security middleware stack configured")
    return app


# Security utility functions
def validate_api_key(api_key: str, expected_key: str) -> bool:
    """Validate API key using constant-time comparison."""
    return hmac.compare_digest(api_key, expected_key)


def generate_security_token() -> str:
    """Generate a cryptographically secure token."""
    import secrets

    return secrets.token_urlsafe(32)


def hash_sensitive_data(data: str, salt: str = None) -> str:
    """Hash sensitive data with salt."""
    if salt is None:
        import secrets

        salt = secrets.token_hex(16)

    return hashlib.pbkdf2_hmac("sha256", data.encode(), salt.encode(), 100000).hex()


def is_safe_url(url: str, allowed_hosts: List[str]) -> bool:
    """Check if URL is safe for redirects."""
    try:
        parsed = urlparse(url)
        return parsed.netloc in allowed_hosts
    except Exception:
        return False
