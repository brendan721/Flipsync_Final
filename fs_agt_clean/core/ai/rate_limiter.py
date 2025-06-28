"""
Rate Limiting and Concurrency Control for FlipSync AI
====================================================

Production-grade rate limiting based on OpenAI Cookbook patterns with:
- Token bucket algorithm for smooth rate limiting
- Semaphore-based concurrency control
- Request queuing with priority
- Adaptive backoff strategies
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class RequestPriority(int, Enum):
    """Request priority levels for queue management."""
    
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    
    requests_per_minute: int = 50
    tokens_per_minute: int = 40000
    max_concurrent_requests: int = 10
    max_queue_size: int = 100
    default_timeout: float = 30.0


class TokenBucket:
    """
    Token bucket implementation for smooth rate limiting.
    
    Based on OpenAI Cookbook rate limiting patterns.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Returns True if tokens were available, False otherwise.
        """
        async with self._lock:
            now = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + (elapsed * self.refill_rate)
            )
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def wait_for_tokens(self, tokens: int = 1, timeout: float = 30.0) -> bool:
        """
        Wait for tokens to become available.
        
        Returns True if tokens were acquired, False if timeout.
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if await self.consume(tokens):
                return True
            
            # Calculate wait time until next token is available
            async with self._lock:
                if self.tokens < tokens:
                    needed_tokens = tokens - self.tokens
                    wait_time = needed_tokens / self.refill_rate
                    wait_time = min(wait_time, 1.0)  # Max 1 second wait
                    
                    await asyncio.sleep(wait_time)
        
        return False


@dataclass
class QueuedRequest:
    """Queued request with priority and metadata."""
    
    func: Callable
    args: tuple
    kwargs: dict
    priority: RequestPriority
    future: asyncio.Future
    created_at: float
    timeout: float


class FlipSyncRateLimiter:
    """
    Production-grade rate limiter for FlipSync AI operations.
    
    Features:
    - Token bucket rate limiting
    - Concurrent request limiting
    - Priority-based request queuing
    - Adaptive timeout handling
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        
        # Token buckets for different limits
        self.request_bucket = TokenBucket(
            capacity=config.requests_per_minute,
            refill_rate=config.requests_per_minute / 60.0  # per second
        )
        
        self.token_bucket = TokenBucket(
            capacity=config.tokens_per_minute,
            refill_rate=config.tokens_per_minute / 60.0  # per second
        )
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        
        # Request queue with priority
        self.request_queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=config.max_queue_size
        )
        
        # Queue processor task
        self._queue_processor_task = None
        self._running = False
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "queued_requests": 0,
            "rate_limited_requests": 0,
            "timeout_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        
        logger.info(f"Initialized FlipSyncRateLimiter: {config.requests_per_minute} req/min, "
                   f"{config.max_concurrent_requests} concurrent")
    
    async def start(self):
        """Start the rate limiter queue processor."""
        if self._running:
            return
        
        self._running = True
        self._queue_processor_task = asyncio.create_task(self._process_queue())
        logger.info("Rate limiter queue processor started")
    
    async def stop(self):
        """Stop the rate limiter and clean up."""
        self._running = False
        
        if self._queue_processor_task:
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Rate limiter stopped")
    
    async def _process_queue(self):
        """Process queued requests with rate limiting."""
        while self._running:
            try:
                # Get next request from queue (blocks if empty)
                try:
                    # Use timeout to allow periodic cleanup
                    priority, request = await asyncio.wait_for(
                        self.request_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Check if request has timed out
                if time.time() - request.created_at > request.timeout:
                    self.stats["timeout_requests"] += 1
                    request.future.set_exception(
                        asyncio.TimeoutError("Request timed out in queue")
                    )
                    continue
                
                # Wait for rate limit tokens
                if not await self.request_bucket.wait_for_tokens(1, timeout=5.0):
                    self.stats["rate_limited_requests"] += 1
                    request.future.set_exception(
                        Exception("Rate limit exceeded")
                    )
                    continue
                
                # Execute request with concurrency control
                async with self.semaphore:
                    try:
                        result = await request.func(*request.args, **request.kwargs)
                        request.future.set_result(result)
                        self.stats["successful_requests"] += 1
                    
                    except Exception as e:
                        request.future.set_exception(e)
                        self.stats["failed_requests"] += 1
                
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(0.1)
    
    async def execute(self, func: Callable, *args, 
                     priority: RequestPriority = RequestPriority.NORMAL,
                     timeout: float = None, **kwargs) -> Any:
        """
        Execute function with rate limiting and concurrency control.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            priority: Request priority
            timeout: Request timeout (defaults to config default)
            **kwargs: Function keyword arguments
        """
        if not self._running:
            await self.start()
        
        timeout = timeout or self.config.default_timeout
        
        # Check queue capacity
        if self.request_queue.qsize() >= self.config.max_queue_size:
            self.stats["rate_limited_requests"] += 1
            raise Exception("Request queue is full")
        
        # Create queued request
        future = asyncio.Future()
        request = QueuedRequest(
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            future=future,
            created_at=time.time(),
            timeout=timeout
        )
        
        # Add to priority queue (lower priority value = higher priority)
        await self.request_queue.put((-priority.value, request))
        
        self.stats["total_requests"] += 1
        self.stats["queued_requests"] += 1
        
        # Wait for result
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        
        except asyncio.TimeoutError:
            self.stats["timeout_requests"] += 1
            raise
        
        finally:
            self.stats["queued_requests"] -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            **self.stats,
            "queue_size": self.request_queue.qsize(),
            "available_concurrent_slots": self.semaphore._value,
            "request_tokens_available": int(self.request_bucket.tokens),
            "token_bucket_available": int(self.token_bucket.tokens)
        }


# Global rate limiter instance
_global_rate_limiter: Optional[FlipSyncRateLimiter] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> FlipSyncRateLimiter:
    """Get or create global rate limiter instance."""
    global _global_rate_limiter
    
    if _global_rate_limiter is None:
        if config is None:
            config = RateLimitConfig()
        _global_rate_limiter = FlipSyncRateLimiter(config)
    
    return _global_rate_limiter


async def rate_limited(func: Callable, *args, 
                      priority: RequestPriority = RequestPriority.NORMAL,
                      **kwargs) -> Any:
    """
    Decorator-style function for rate-limited execution.
    
    Usage:
        result = await rate_limited(my_async_function, arg1, arg2, priority=RequestPriority.HIGH)
    """
    rate_limiter = get_rate_limiter()
    return await rate_limiter.execute(func, *args, priority=priority, **kwargs)
