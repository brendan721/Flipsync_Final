#!/usr/bin/env python3
"""
Optimized API Client with Parallec-inspired patterns.

This client implements:
- Connection pooling for high performance
- Circuit breaker pattern for fault tolerance
- Batch processing for efficiency
- Timeout and retry management
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import json

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker implementation for API fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, success_threshold: int = 3):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            success_threshold: Successes needed in half-open to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        
        logger.info(f"Circuit breaker initialized: {failure_threshold} failures, {recovery_timeout}s recovery")
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful operation."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker CLOSED - service recovered")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker returned to OPEN from HALF_OPEN")


class OptimizedApiClient:
    """High-performance API client with Parallec-inspired patterns."""
    
    def __init__(self, base_url: str = None, max_connections: int = 100, timeout: int = 30):
        """Initialize optimized API client.
        
        Args:
            base_url: Base URL for API requests
            max_connections: Maximum concurrent connections
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.max_connections = max_connections
        self.timeout = timeout
        
        # Connection pool configuration
        self.connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections // 2,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # Client session with optimized settings
        self.timeout_config = aiohttp.ClientTimeout(total=timeout, connect=10)
        self.session = None
        
        # Circuit breakers for different endpoints
        self.circuit_breakers = {}
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'circuit_breaker_rejections': 0,
            'avg_response_time_ms': 0,
            'connection_pool_hits': 0,
            'batch_requests': 0
        }
        
        logger.info(f"OptimizedApiClient initialized: {max_connections} connections, {timeout}s timeout")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Start the API client session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout_config,
                headers={'User-Agent': 'FlipSync-OptimizedClient/1.0'}
            )
            logger.info("API client session started")
    
    async def close(self):
        """Close the API client session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("API client session closed")
    
    def get_circuit_breaker(self, endpoint: str) -> CircuitBreaker:
        """Get or create circuit breaker for endpoint."""
        if endpoint not in self.circuit_breakers:
            self.circuit_breakers[endpoint] = CircuitBreaker()
        return self.circuit_breakers[endpoint]
    
    async def request(self, method: str, url: str, endpoint_key: str = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Make optimized HTTP request with circuit breaker protection.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            endpoint_key: Key for circuit breaker (defaults to URL)
            **kwargs: Additional request parameters
            
        Returns:
            Response data or None if failed
        """
        if not self.session:
            await self.start()
        
        endpoint_key = endpoint_key or url
        circuit_breaker = self.get_circuit_breaker(endpoint_key)
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            self.metrics['circuit_breaker_rejections'] += 1
            logger.warning(f"Circuit breaker OPEN for {endpoint_key}")
            return None
        
        start_time = time.perf_counter()
        self.metrics['total_requests'] += 1
        
        try:
            # Make request with connection pooling
            async with self.session.request(method, url, **kwargs) as response:
                self.metrics['connection_pool_hits'] += 1
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Record success
                    circuit_breaker.record_success()
                    self.metrics['successful_requests'] += 1
                    self._update_response_time(start_time)
                    
                    return data
                else:
                    # HTTP error
                    circuit_breaker.record_failure()
                    self.metrics['failed_requests'] += 1
                    self._update_response_time(start_time)
                    
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except asyncio.TimeoutError:
            circuit_breaker.record_failure()
            self.metrics['failed_requests'] += 1
            self._update_response_time(start_time)
            logger.error(f"Timeout for {url}")
            return None
            
        except Exception as e:
            circuit_breaker.record_failure()
            self.metrics['failed_requests'] += 1
            self._update_response_time(start_time)
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    async def batch_requests(self, requests: List[Dict[str, Any]], max_concurrent: int = 10) -> List[Optional[Dict[str, Any]]]:
        """Execute multiple requests concurrently with controlled concurrency.
        
        Args:
            requests: List of request dictionaries with 'method', 'url', and optional params
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of response data (None for failed requests)
        """
        if not self.session:
            await self.start()
        
        self.metrics['batch_requests'] += 1
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_request(request_data):
            async with semaphore:
                return await self.request(**request_data)
        
        # Execute all requests concurrently
        tasks = [bounded_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to None
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch request failed: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        logger.info(f"Batch completed: {len(requests)} requests, {max_concurrent} concurrent")
        return processed_results
    
    def _update_response_time(self, start_time: float):
        """Update average response time metric."""
        response_time = (time.perf_counter() - start_time) * 1000
        
        total = self.metrics['total_requests']
        current_avg = self.metrics['avg_response_time_ms']
        self.metrics['avg_response_time_ms'] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics."""
        total_requests = self.metrics['total_requests']
        if total_requests == 0:
            return self.metrics
        
        success_rate = (self.metrics['successful_requests'] / total_requests) * 100
        failure_rate = (self.metrics['failed_requests'] / total_requests) * 100
        
        return {
            **self.metrics,
            'success_rate_percentage': success_rate,
            'failure_rate_percentage': failure_rate,
            'circuit_breaker_count': len(self.circuit_breakers),
            'active_connections': getattr(self.connector, '_acquired_per_host', {})
        }
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        status = {}
        for endpoint, breaker in self.circuit_breakers.items():
            status[endpoint] = {
                'state': breaker.state.value,
                'failure_count': breaker.failure_count,
                'success_count': breaker.success_count,
                'last_failure_time': breaker.last_failure_time
            }
        return status


class EbayOptimizedApiClient(OptimizedApiClient):
    """eBay-specific optimized API client."""
    
    def __init__(self, environment: str = "sandbox"):
        """Initialize eBay optimized API client.
        
        Args:
            environment: eBay environment ("sandbox" or "production")
        """
        if environment == "sandbox":
            base_url = "https://api.sandbox.ebay.com"
        else:
            base_url = "https://api.ebay.com"
        
        super().__init__(base_url=base_url, max_connections=50, timeout=30)
        self.environment = environment
        
        logger.info(f"EbayOptimizedApiClient initialized for {environment}")
    
    async def get_category_specifics_batch(self, category_ids: List[str], auth_headers: Dict[str, str]) -> List[Optional[Dict[str, Any]]]:
        """Get category specifics for multiple categories efficiently.
        
        Args:
            category_ids: List of eBay category IDs
            auth_headers: Authorization headers
            
        Returns:
            List of category specifics data
        """
        # Prepare batch requests
        requests = []
        for category_id in category_ids:
            requests.append({
                'method': 'GET',
                'url': f"{self.base_url}/commerce/taxonomy/v1/category_tree/0/get_category_specifics",
                'endpoint_key': 'category_specifics',
                'params': {'category_id': category_id},
                'headers': auth_headers
            })
        
        # Execute batch with controlled concurrency
        results = await self.batch_requests(requests, max_concurrent=5)
        
        logger.info(f"Batch category specifics: {len(category_ids)} categories, "
                   f"{sum(1 for r in results if r)} successful")
        
        return results
    
    async def health_check(self, auth_headers: Dict[str, str]) -> bool:
        """Perform health check on eBay API.
        
        Args:
            auth_headers: Authorization headers
            
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            result = await self.request(
                'GET',
                f"{self.base_url}/commerce/taxonomy/v1/category_tree/0",
                endpoint_key='health_check',
                headers=auth_headers
            )
            return result is not None
        except Exception as e:
            logger.error(f"eBay API health check failed: {e}")
            return False


# Global client instance
_ebay_api_client = None


async def get_ebay_api_client(environment: str = "sandbox") -> EbayOptimizedApiClient:
    """Get global eBay API client instance.
    
    Args:
        environment: eBay environment ("sandbox" or "production")
        
    Returns:
        EbayOptimizedApiClient instance
    """
    global _ebay_api_client
    
    if _ebay_api_client is None:
        _ebay_api_client = EbayOptimizedApiClient(environment)
        await _ebay_api_client.start()
    
    return _ebay_api_client
