"""
FlipSync Redis Caching Middleware
=================================
Advanced caching middleware for FastAPI with Redis backend
"""

import json
import hashlib
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
import redis
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Setup logging
logger = logging.getLogger("flipsync-cache")

class RedisCacheConfig:
    """Redis cache configuration"""
    
    def __init__(self):
        self.redis_host = "127.0.0.1"
        self.redis_port = 6379
        self.redis_password = ""  # Set if Redis requires auth
        self.redis_db = 1  # Use separate DB for caching
        self.default_ttl = 300  # 5 minutes
        self.key_prefix = "flipsync:cache:"
        
        # Cache TTL by endpoint pattern
        self.endpoint_ttl = {
            "/api/v1/health": 60,  # 1 minute
            "/api/v1/agents/status": 300,  # 5 minutes
            "/api/v1/mobile/dashboard": 180,  # 3 minutes
            "/api/v1/inventory": 600,  # 10 minutes
            "/api/v1/marketplace/ebay": 1800,  # 30 minutes
        }
        
        # Endpoints to never cache
        self.no_cache_endpoints = {
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/auth/refresh",
            "/api/v1/marketplace/ebay/oauth",
        }
        
        # Cache only GET requests by default
        self.cacheable_methods = {"GET"}

class RedisCache:
    """Redis-based caching system"""
    
    def __init__(self, config: RedisCacheConfig):
        self.config = config
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            redis_kwargs = {
                "host": self.config.redis_host,
                "port": self.config.redis_port,
                "db": self.config.redis_db,
                "decode_responses": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            }
            
            if self.config.redis_password:
                redis_kwargs["password"] = self.config.redis_password
            
            self.redis_client = redis.Redis(**redis_kwargs)
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connection established")
            
        except Exception as e:
            logger.warning(f"Redis cache connection failed: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        # Include method, path, and query parameters
        key_data = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) if request.url.query else "",
        }
        
        # Include user context if available (for user-specific caching)
        if hasattr(request.state, "user_id"):
            key_data["user_id"] = request.state.user_id
        
        # Create hash of key data
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{self.config.key_prefix}{key_hash}"
    
    def _get_ttl_for_endpoint(self, path: str) -> int:
        """Get TTL for specific endpoint"""
        # Check for exact match first
        if path in self.config.endpoint_ttl:
            return self.config.endpoint_ttl[path]
        
        # Check for pattern matches
        for pattern, ttl in self.config.endpoint_ttl.items():
            if path.startswith(pattern):
                return ttl
        
        return self.config.default_ttl
    
    def _should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached"""
        # Check if Redis is available
        if not self.redis_client:
            return False
        
        # Check HTTP method
        if request.method not in self.config.cacheable_methods:
            return False
        
        # Check if endpoint is in no-cache list
        path = request.url.path
        for no_cache_path in self.config.no_cache_endpoints:
            if path.startswith(no_cache_path):
                return False
        
        return True
    
    def get(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        if not self._should_cache_request(request):
            return None
        
        try:
            cache_key = self._generate_cache_key(request)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache HIT for {request.url.path}")
                return data
            
            logger.debug(f"Cache MISS for {request.url.path}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, request: Request, response_data: Dict[str, Any], status_code: int = 200):
        """Cache response data"""
        if not self._should_cache_request(request):
            return
        
        # Don't cache error responses
        if status_code >= 400:
            return
        
        try:
            cache_key = self._generate_cache_key(request)
            ttl = self._get_ttl_for_endpoint(request.url.path)
            
            cache_data = {
                "data": response_data,
                "status_code": status_code,
                "cached_at": datetime.utcnow().isoformat(),
                "ttl": ttl
            }
            
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data)
            )
            
            logger.debug(f"Cached response for {request.url.path} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def delete(self, pattern: str = None):
        """Delete cached entries"""
        if not self.redis_client:
            return
        
        try:
            if pattern:
                # Delete by pattern
                keys = self.redis_client.keys(f"{self.config.key_prefix}{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Deleted {len(keys)} cache entries matching pattern: {pattern}")
            else:
                # Delete all cache entries
                keys = self.redis_client.keys(f"{self.config.key_prefix}*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Deleted all {len(keys)} cache entries")
                    
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "unavailable"}
        
        try:
            info = self.redis_client.info()
            
            # Count cache keys
            cache_keys = self.redis_client.keys(f"{self.config.key_prefix}*")
            
            return {
                "status": "available",
                "total_keys": len(cache_keys),
                "memory_used": info.get("used_memory_human", "unknown"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100

# Global cache instance
cache_config = RedisCacheConfig()
redis_cache = RedisCache(cache_config)

class CacheMiddleware:
    """FastAPI middleware for Redis caching"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Try to get cached response
        cached_response = redis_cache.get(request)
        if cached_response:
            response = JSONResponse(
                content=cached_response["data"],
                status_code=cached_response["status_code"],
                headers={"X-Cache-Status": "HIT"}
            )
            await response(scope, receive, send)
            return
        
        # Capture response for caching
        response_body = b""
        response_status_code = 200
        
        async def send_wrapper(message):
            nonlocal response_body, response_status_code
            
            if message["type"] == "http.response.start":
                response_status_code = message["status"]
                # Add cache miss header
                headers = list(message.get("headers", []))
                headers.append([b"x-cache-status", b"MISS"])
                message["headers"] = headers
            
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
                
                # Cache the response if it's complete
                if not message.get("more_body", False):
                    try:
                        if response_body and response_status_code == 200:
                            response_data = json.loads(response_body.decode())
                            redis_cache.set(request, response_data, response_status_code)
                    except Exception as e:
                        logger.debug(f"Could not cache response: {e}")
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

# Utility functions for manual cache management
def invalidate_cache(pattern: str = None):
    """Invalidate cache entries"""
    redis_cache.delete(pattern)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return redis_cache.get_stats()

def warm_cache_endpoint(endpoint: str, data: Dict[str, Any], ttl: int = None):
    """Manually warm cache for an endpoint"""
    if not redis_cache.redis_client:
        return False
    
    try:
        cache_key = f"{cache_config.key_prefix}{hashlib.md5(endpoint.encode()).hexdigest()}"
        ttl = ttl or cache_config.default_ttl
        
        cache_data = {
            "data": data,
            "status_code": 200,
            "cached_at": datetime.utcnow().isoformat(),
            "ttl": ttl
        }
        
        redis_cache.redis_client.setex(
            cache_key,
            ttl,
            json.dumps(cache_data)
        )
        
        logger.info(f"Cache warmed for endpoint: {endpoint}")
        return True
        
    except Exception as e:
        logger.error(f"Cache warm error: {e}")
        return False
