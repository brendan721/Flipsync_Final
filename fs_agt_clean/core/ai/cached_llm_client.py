"""
Cached LLM Client for FlipSync
=============================

A wrapper around SimpleLLMClient that adds Redis-based caching for improved performance.
Reduces AI response times for repeated queries and provides fallback mechanisms.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fs_agt_clean.core.ai.simple_llm_client import LLMResponse, SimpleLLMClient
from fs_agt_clean.core.cache.ai_cache import AICacheService

logger = logging.getLogger(__name__)


class CachedLLMClient:
    """LLM client with Redis-based response caching."""

    def __init__(
        self,
        llm_client: SimpleLLMClient,
        cache_service: Optional[AICacheService] = None,
    ):
        """Initialize cached LLM client."""
        self.llm_client = llm_client
        self.cache_service = cache_service
        self.cache_enabled = cache_service is not None

        # Cache configuration
        self.cache_config = {
            "default_ttl": 3600,  # 1 hour
            "short_ttl": 300,  # 5 minutes for dynamic content
            "long_ttl": 86400,  # 24 hours for stable content
            "key_prefix": "flipsync:llm:",
        }

        logger.info(f"Initialized CachedLLMClient (cache_enabled={self.cache_enabled})")

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        cache_ttl: Optional[int] = None,
        cache_key_suffix: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate response with caching support."""
        start_time = time.time()

        # Generate cache key
        cache_key = self._generate_cache_key(prompt, system_prompt, cache_key_suffix)

        # Try to get from cache first
        if self.cache_enabled:
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                logger.info(f"Cache hit for key: {cache_key[:50]}...")
                return cached_response

        # Generate new response
        try:
            response = await self.llm_client.generate_response(
                prompt=prompt, system_prompt=system_prompt, **kwargs
            )

            # Cache the response
            if self.cache_enabled:
                await self._cache_response(cache_key, response, cache_ttl)

            return response

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Try to return stale cache if available
            if self.cache_enabled:
                stale_response = await self._get_stale_cached_response(cache_key)
                if stale_response:
                    logger.warning(f"Returning stale cached response due to error: {e}")
                    return stale_response
            raise

    def _generate_cache_key(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        suffix: Optional[str] = None,
    ) -> str:
        """Generate cache key for the request."""
        # Create hash of prompt and system prompt
        content = f"{prompt}|{system_prompt or ''}|{self.llm_client.model}"
        if suffix:
            content += f"|{suffix}"

        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{self.cache_config['key_prefix']}{content_hash}"

    async def _get_cached_response(self, cache_key: str) -> Optional[LLMResponse]:
        """Get cached response if available."""
        try:
            cached_data = await self.cache_service.get_cached_result(cache_key)
            if cached_data:
                # Reconstruct LLMResponse from cached data
                return LLMResponse(
                    content=cached_data["content"],
                    provider=self.llm_client.provider,
                    model=cached_data["model"],
                    response_time=cached_data["response_time"],
                    metadata={
                        **cached_data.get("metadata", {}),
                        "cached": True,
                        "cache_hit_time": datetime.now(timezone.utc).isoformat(),
                    },
                    tokens_used=cached_data.get("tokens_used", 0),
                )
        except Exception as e:
            logger.warning(f"Error retrieving cached response: {e}")
        return None

    async def _get_stale_cached_response(self, cache_key: str) -> Optional[LLMResponse]:
        """Get stale cached response as fallback."""
        # This would require implementing stale cache retrieval in AICacheService
        # For now, return None
        return None

    async def _cache_response(
        self, cache_key: str, response: LLMResponse, ttl: Optional[int] = None
    ) -> None:
        """Cache the LLM response."""
        try:
            cache_data = {
                "content": response.content,
                "model": response.model,
                "response_time": response.response_time,
                "metadata": response.metadata,
                "tokens_used": response.tokens_used,
                "cached_at": datetime.now(timezone.utc).isoformat(),
            }

            cache_ttl = ttl or self.cache_config["default_ttl"]
            await self.cache_service.cache_result(cache_key, cache_data, ttl=cache_ttl)

            logger.debug(f"Cached response with key: {cache_key[:50]}...")

        except Exception as e:
            logger.warning(f"Error caching response: {e}")


class CachedLLMClientFactory:
    """Factory for creating cached LLM clients."""

    @staticmethod
    async def create_cached_client(
        llm_client: SimpleLLMClient,
        redis_url: str = "redis://flipsync-infrastructure-redis:6379",
        cache_db: int = 2,
    ) -> CachedLLMClient:
        """Create a cached LLM client with Redis cache."""
        try:
            # Initialize cache service
            cache_service = AICacheService(redis_url=redis_url, db=cache_db)
            await cache_service.connect()

            return CachedLLMClient(llm_client, cache_service)

        except Exception as e:
            logger.warning(f"Failed to initialize cache service: {e}")
            logger.warning("Creating non-cached LLM client")
            return CachedLLMClient(llm_client, None)

    @staticmethod
    def create_non_cached_client(llm_client: SimpleLLMClient) -> CachedLLMClient:
        """Create a non-cached LLM client (cache disabled)."""
        return CachedLLMClient(llm_client, None)


# Convenience functions for common use cases
async def create_fast_cached_client() -> CachedLLMClient:
    """Create a fast cached client for simple queries."""
    from fs_agt_clean.core.ai.llm_adapter import FlipSyncLLMFactory

    fast_client = FlipSyncLLMFactory.create_fast_client()
    return await CachedLLMClientFactory.create_cached_client(fast_client.client)


async def create_smart_cached_client() -> CachedLLMClient:
    """Create a smart cached client for complex queries."""
    from fs_agt_clean.core.ai.llm_adapter import FlipSyncLLMFactory

    smart_client = FlipSyncLLMFactory.create_smart_client()
    return await CachedLLMClientFactory.create_cached_client(smart_client.client)
