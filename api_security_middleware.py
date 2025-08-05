"""
FlipSync API Security Middleware
===============================
Enhanced security middleware for FastAPI with rate limiting, authentication, and monitoring
"""

import time
import hashlib
import logging
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Setup logging
logger = logging.getLogger("flipsync-security")

class SecurityConfig:
    """Security configuration"""
    
    def __init__(self):
        # Rate limiting configuration
        self.rate_limits = {
            "/api/v1/auth/login": {"requests": 5, "window": 300},  # 5 requests per 5 minutes
            "/api/v1/auth/register": {"requests": 3, "window": 3600},  # 3 requests per hour
            "/api/v1/marketplace/ebay/oauth": {"requests": 10, "window": 3600},  # 10 per hour
            "default": {"requests": 100, "window": 60}  # 100 requests per minute default
        }
        
        # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "X-FlipSync-Security": "enabled",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        # Blocked user agents (bots, scanners)
        self.blocked_user_agents = {
            "sqlmap", "nikto", "nmap", "masscan", "zap", "burp",
            "acunetix", "nessus", "openvas", "w3af", "skipfish"
        }
        
        # Suspicious patterns in requests
        self.suspicious_patterns = {
            "sql_injection": ["union", "select", "insert", "delete", "drop", "exec", "script"],
            "xss": ["<script", "javascript:", "onload=", "onerror=", "alert("],
            "path_traversal": ["../", "..\\", "/etc/passwd", "/windows/system32"],
            "command_injection": [";", "|", "&", "`", "$", "$(", "&&", "||"]
        }
        
        # JWT configuration
        self.jwt_secret = "FlipSync_JWT_Prod_2024_Secure_Key_7NaznE9ddVcN_Lq0LVHIFBKa9taUQnVOWZU6IjcV7Ww"
        self.jwt_algorithm = "HS256"
        self.jwt_expiry = 3600  # 1 hour

class RateLimiter:
    """Advanced rate limiting with sliding window"""
    
    def __init__(self):
        self.requests = defaultdict(lambda: deque())
        self.blocked_ips = {}  # IP -> unblock_time
    
    def is_rate_limited(self, client_ip: str, endpoint: str, config: SecurityConfig) -> bool:
        """Check if client is rate limited"""
        now = time.time()
        
        # Check if IP is temporarily blocked
        if client_ip in self.blocked_ips:
            if now < self.blocked_ips[client_ip]:
                return True
            else:
                del self.blocked_ips[client_ip]
        
        # Get rate limit for endpoint
        rate_limit = config.rate_limits.get(endpoint, config.rate_limits["default"])
        window = rate_limit["window"]
        max_requests = rate_limit["requests"]
        
        # Clean old requests
        key = f"{client_ip}:{endpoint}"
        request_times = self.requests[key]
        
        # Remove requests outside the window
        while request_times and request_times[0] < now - window:
            request_times.popleft()
        
        # Check if limit exceeded
        if len(request_times) >= max_requests:
            # Block IP for additional time if severely over limit
            if len(request_times) > max_requests * 2:
                self.blocked_ips[client_ip] = now + 3600  # Block for 1 hour
                logger.warning(f"IP {client_ip} blocked for 1 hour due to severe rate limit violation")
            return True
        
        # Add current request
        request_times.append(now)
        return False
    
    def get_rate_limit_info(self, client_ip: str, endpoint: str, config: SecurityConfig) -> Dict:
        """Get rate limit information for headers"""
        rate_limit = config.rate_limits.get(endpoint, config.rate_limits["default"])
        key = f"{client_ip}:{endpoint}"
        request_times = self.requests[key]
        
        now = time.time()
        window = rate_limit["window"]
        
        # Count requests in current window
        current_requests = sum(1 for req_time in request_times if req_time > now - window)
        
        return {
            "limit": rate_limit["requests"],
            "remaining": max(0, rate_limit["requests"] - current_requests),
            "reset": int(now + window),
            "window": window
        }

class SecurityAnalyzer:
    """Analyze requests for security threats"""
    
    def __init__(self):
        self.threat_scores = defaultdict(int)
    
    def analyze_request(self, request: Request, config: SecurityConfig) -> Dict:
        """Analyze request for security threats"""
        threats = []
        threat_score = 0
        
        # Check User-Agent
        user_agent = request.headers.get("user-agent", "").lower()
        for blocked_agent in config.blocked_user_agents:
            if blocked_agent in user_agent:
                threats.append(f"Blocked user agent: {blocked_agent}")
                threat_score += 10
        
        # Check for suspicious patterns in URL and query parameters
        url_path = str(request.url.path).lower()
        query_string = str(request.url.query).lower()
        
        for pattern_type, patterns in config.suspicious_patterns.items():
            for pattern in patterns:
                if pattern in url_path or pattern in query_string:
                    threats.append(f"{pattern_type.replace('_', ' ').title()}: {pattern}")
                    threat_score += 5
        
        # Check for unusual request patterns
        if len(url_path) > 1000:
            threats.append("Unusually long URL")
            threat_score += 3
        
        # Check for multiple slashes (potential path traversal)
        if "//" in url_path or "\\\\" in url_path:
            threats.append("Multiple slashes in path")
            threat_score += 2
        
        # Update threat score for client IP
        client_ip = self._get_client_ip(request)
        self.threat_scores[client_ip] += threat_score
        
        return {
            "threats": threats,
            "threat_score": threat_score,
            "total_threat_score": self.threat_scores[client_ip],
            "client_ip": client_ip
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP considering proxies"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class JWTValidator:
    """JWT token validation"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            
            # Check expiration
            if payload.get("exp", 0) < time.time():
                return None
            
            return payload
            
        except jwt.InvalidTokenError:
            return None
    
    def create_token(self, user_data: Dict) -> str:
        """Create JWT token"""
        payload = {
            **user_data,
            "exp": time.time() + self.config.jwt_expiry,
            "iat": time.time()
        }
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.config = SecurityConfig()
        self.rate_limiter = RateLimiter()
        self.security_analyzer = SecurityAnalyzer()
        self.jwt_validator = JWTValidator(self.config)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks"""
        start_time = time.time()
        
        # Get client IP
        client_ip = self.security_analyzer._get_client_ip(request)
        
        # Security analysis
        security_analysis = self.security_analyzer.analyze_request(request, self.config)
        
        # Block high-threat requests
        if security_analysis["threat_score"] > 20:
            logger.warning(f"Blocked high-threat request from {client_ip}: {security_analysis['threats']}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Request blocked for security reasons"}
            )
        
        # Rate limiting
        endpoint = request.url.path
        if self.rate_limiter.is_rate_limited(client_ip, endpoint, self.config):
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.config.security_headers.items():
            response.headers[header] = value
        
        # Add rate limit headers
        rate_info = self.rate_limiter.get_rate_limit_info(client_ip, endpoint, self.config)
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
        response.headers["X-RateLimit-Window"] = str(rate_info["window"])
        
        # Add processing time header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Log security events
        if security_analysis["threats"]:
            logger.info(f"Security threats detected from {client_ip}: {security_analysis['threats']}")
        
        return response

# Authentication helper functions
def get_current_user(request: Request, security_middleware: SecurityMiddleware) -> Optional[Dict]:
    """Get current authenticated user from request"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    return security_middleware.jwt_validator.validate_token(token)

def require_authentication(request: Request, security_middleware: SecurityMiddleware) -> Dict:
    """Require authentication and return user data"""
    user = get_current_user(request, security_middleware)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

# Security monitoring functions
def log_security_event(event_type: str, details: Dict, client_ip: str):
    """Log security events for monitoring"""
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": event_type,
        "client_ip": client_ip,
        "details": details
    }
    
    logger.warning(f"Security Event: {event}")

def get_security_stats() -> Dict:
    """Get security statistics"""
    # This would typically query a database or cache
    # For now, return basic stats
    return {
        "total_blocked_requests": 0,  # Would be tracked in production
        "rate_limited_requests": 0,
        "threat_detections": 0,
        "active_sessions": 0
    }

# Example usage in FastAPI app:
"""
from fastapi import FastAPI
from api_security_middleware import SecurityMiddleware

app = FastAPI()

# Add security middleware
app.add_middleware(SecurityMiddleware)

@app.get("/api/v1/secure-endpoint")
async def secure_endpoint(request: Request):
    # Get security middleware instance
    security_middleware = None
    for middleware in app.user_middleware:
        if isinstance(middleware.cls, SecurityMiddleware):
            security_middleware = middleware.cls
            break
    
    # Require authentication
    user = require_authentication(request, security_middleware)
    
    return {"message": "Secure data", "user": user}
"""
