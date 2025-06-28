"""
Security Hardening Module for FlipSync Production Deployment.

This module implements advanced security measures to achieve 95%+ security audit score
including rate limiting, input validation, security headers, and threat detection.
"""

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class SecurityEvent:
    """Security event data structure."""

    event_type: str
    source_ip: str
    user_id: Optional[str]
    endpoint: str
    timestamp: datetime
    severity: str
    details: Dict[str, Any]


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""

    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int
    window_size: int = 60  # seconds


class AdvancedRateLimiter:
    """Advanced rate limiting with sliding window and burst protection."""

    def __init__(self):
        """Initialize the rate limiter."""
        self.request_history: Dict[str, deque] = defaultdict(deque)
        self.burst_counters: Dict[str, int] = defaultdict(int)
        self.blocked_ips: Dict[str, datetime] = {}

        # Rate limit rules by endpoint type
        self.rules = {
            "auth": RateLimitRule(
                500, 5000, 100
            ),  # Authentication endpoints - support 100+ concurrent users
            "api": RateLimitRule(100, 1000, 20),  # General API endpoints
            "upload": RateLimitRule(5, 50, 2),  # File upload endpoints
            "ai": RateLimitRule(20, 200, 5),  # AI analysis endpoints
            "default": RateLimitRule(60, 600, 10),  # Default rate limit
        }

        logger.info("Advanced Rate Limiter initialized with endpoint-specific rules")

    def get_client_key(self, request: Request) -> str:
        """Generate client identification key."""
        # Use IP address as primary identifier
        client_ip = self._get_client_ip(request)

        # Add user ID if authenticated
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"{client_ip}:{user_id}"

        return client_ip

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

    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type for rate limiting rules."""
        if "/auth/" in path or "/login" in path or "/register" in path:
            return "auth"
        elif "/upload" in path or "/files" in path:
            return "upload"
        elif "/ai/" in path or "/analyze" in path:
            return "ai"
        elif "/api/" in path:
            return "api"
        else:
            return "default"

    async def check_rate_limit(self, request: Request) -> bool:
        """
        Check if request should be rate limited.

        Returns:
            True if request is allowed, False if rate limited
        """
        client_key = self.get_client_key(request)
        endpoint_type = self._get_endpoint_type(request.url.path)
        rule = self.rules.get(endpoint_type, self.rules["default"])

        now = time.time()
        current_minute = int(now // 60)

        # Check if IP is temporarily blocked
        if client_key in self.blocked_ips:
            if datetime.now(timezone.utc) < self.blocked_ips[client_key]:
                return False
            else:
                del self.blocked_ips[client_key]

        # Initialize request history for client
        if client_key not in self.request_history:
            self.request_history[client_key] = deque()

        history = self.request_history[client_key]

        # Clean old entries (older than 1 hour)
        cutoff_time = now - 3600
        while history and history[0] < cutoff_time:
            history.popleft()

        # Check burst limit (requests in last 10 seconds)
        burst_cutoff = now - 10
        recent_requests = sum(1 for timestamp in history if timestamp > burst_cutoff)

        if recent_requests >= rule.burst_limit:
            logger.warning(
                f"Burst limit exceeded for {client_key}: {recent_requests} requests in 10s"
            )
            self._block_client(client_key, minutes=5)
            return False

        # Check per-minute limit
        minute_cutoff = now - 60
        minute_requests = sum(1 for timestamp in history if timestamp > minute_cutoff)

        if minute_requests >= rule.requests_per_minute:
            logger.warning(
                f"Per-minute limit exceeded for {client_key}: {minute_requests} requests/min"
            )
            return False

        # Check per-hour limit
        hour_requests = len(history)
        if hour_requests >= rule.requests_per_hour:
            logger.warning(
                f"Per-hour limit exceeded for {client_key}: {hour_requests} requests/hour"
            )
            return False

        # Record this request
        history.append(now)
        return True

    def _block_client(self, client_key: str, minutes: int = 5):
        """Temporarily block a client."""
        block_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        self.blocked_ips[client_key] = block_until
        logger.warning(f"Temporarily blocked {client_key} until {block_until}")


class InputValidator:
    """Advanced input validation and sanitization."""

    def __init__(self):
        """Initialize the input validator."""
        # Dangerous patterns to detect
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\bUNION\s+SELECT\b)",
        ]

        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
        ]

        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e\\",
        ]

        logger.info("Input Validator initialized with security patterns")

    def validate_request_data(self, data: Any) -> Dict[str, Any]:
        """
        Validate and sanitize request data.

        Returns:
            Validation result with sanitized data and security warnings
        """
        result = {
            "valid": True,
            "sanitized_data": data,
            "warnings": [],
            "blocked_patterns": [],
        }

        if isinstance(data, dict):
            result["sanitized_data"] = self._validate_dict(data, result)
        elif isinstance(data, list):
            result["sanitized_data"] = self._validate_list(data, result)
        elif isinstance(data, str):
            result["sanitized_data"] = self._validate_string(data, result)

        result["valid"] = len(result["blocked_patterns"]) == 0
        return result

    def _validate_dict(
        self, data: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate dictionary data."""
        sanitized = {}
        for key, value in data.items():
            # Validate key
            clean_key = self._validate_string(key, result)

            # Validate value
            if isinstance(value, dict):
                sanitized[clean_key] = self._validate_dict(value, result)
            elif isinstance(value, list):
                sanitized[clean_key] = self._validate_list(value, result)
            elif isinstance(value, str):
                sanitized[clean_key] = self._validate_string(value, result)
            else:
                sanitized[clean_key] = value

        return sanitized

    def _validate_list(self, data: List[Any], result: Dict[str, Any]) -> List[Any]:
        """Validate list data."""
        sanitized = []
        for item in data:
            if isinstance(item, dict):
                sanitized.append(self._validate_dict(item, result))
            elif isinstance(item, list):
                sanitized.append(self._validate_list(item, result))
            elif isinstance(item, str):
                sanitized.append(self._validate_string(item, result))
            else:
                sanitized.append(item)

        return sanitized

    def _validate_string(self, data: str, result: Dict[str, Any]) -> str:
        """Validate and sanitize string data."""
        import re

        original_data = data

        # Check for SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                result["blocked_patterns"].append(f"SQL injection pattern: {pattern}")
                result["warnings"].append(
                    f"Potential SQL injection detected in: {data[:50]}..."
                )

        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                result["blocked_patterns"].append(f"XSS pattern: {pattern}")
                result["warnings"].append(f"Potential XSS detected in: {data[:50]}...")
                # Remove dangerous HTML/JS
                data = re.sub(pattern, "", data, flags=re.IGNORECASE)

        # Check for path traversal patterns
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                result["blocked_patterns"].append(f"Path traversal pattern: {pattern}")
                result["warnings"].append(
                    f"Potential path traversal detected in: {data[:50]}..."
                )

        # Basic HTML encoding for safety
        data = data.replace("<", "&lt;").replace(">", "&gt;")

        return data


class ThreatDetectionSystem:
    """Advanced threat detection and response system."""

    def __init__(self):
        """Initialize the threat detection system."""
        self.security_events: deque = deque(maxlen=10000)
        self.threat_scores: Dict[str, float] = defaultdict(float)
        self.suspicious_ips: Set[str] = set()

        # Threat detection rules
        self.threat_thresholds = {
            "failed_auth_attempts": 5,
            "rapid_requests": 100,
            "suspicious_patterns": 3,
            "blocked_requests": 10,
        }

        logger.info("Threat Detection System initialized")

    def record_security_event(self, event: SecurityEvent):
        """Record a security event for analysis."""
        self.security_events.append(event)

        # Update threat score for source IP
        self._update_threat_score(event)

        # Check for immediate threats
        self._check_immediate_threats(event)

        logger.debug(
            f"Security event recorded: {event.event_type} from {event.source_ip}"
        )

    def _update_threat_score(self, event: SecurityEvent):
        """Update threat score based on event."""
        score_delta = 0

        if event.event_type == "failed_auth":
            score_delta = 2.0
        elif event.event_type == "rate_limit_exceeded":
            score_delta = 1.5
        elif event.event_type == "suspicious_input":
            score_delta = 3.0
        elif event.event_type == "blocked_request":
            score_delta = 1.0

        # Apply severity multiplier
        if event.severity == "high":
            score_delta *= 2.0
        elif event.severity == "critical":
            score_delta *= 3.0

        self.threat_scores[event.source_ip] += score_delta

        # Mark as suspicious if score exceeds threshold
        if self.threat_scores[event.source_ip] > 10.0:
            self.suspicious_ips.add(event.source_ip)
            logger.warning(
                f"IP {event.source_ip} marked as suspicious (score: {self.threat_scores[event.source_ip]})"
            )

    def _check_immediate_threats(self, event: SecurityEvent):
        """Check for immediate threat patterns."""
        # Check for rapid failed authentication attempts
        recent_failed_auth = [
            e
            for e in self.security_events
            if e.source_ip == event.source_ip
            and e.event_type == "failed_auth"
            and (datetime.now(timezone.utc) - e.timestamp).total_seconds()
            < 300  # 5 minutes
        ]

        if len(recent_failed_auth) >= self.threat_thresholds["failed_auth_attempts"]:
            logger.critical(
                f"Multiple failed auth attempts from {event.source_ip}: {len(recent_failed_auth)} in 5 minutes"
            )
            self.suspicious_ips.add(event.source_ip)

    def is_suspicious_ip(self, ip: str) -> bool:
        """Check if an IP is marked as suspicious."""
        return ip in self.suspicious_ips

    def get_threat_score(self, ip: str) -> float:
        """Get current threat score for an IP."""
        return self.threat_scores.get(ip, 0.0)


# Global instances
rate_limiter = AdvancedRateLimiter()
input_validator = InputValidator()
threat_detector = ThreatDetectionSystem()
