#!/usr/bin/env python3
"""
Intelligent Caching System for FlipSync Phase 2 Optimization
============================================================

This module provides intelligent response caching for similar product analyses
to achieve 30-55% cost reduction from the Phase 1 baseline of $0.0024 per operation.

Features:
- Content-based cache keys using semantic hashing
- 24-hour TTL for product analysis caching
- Cache hit/miss analytics and cost tracking
- Integration with Phase 1 intelligent model router
- Quality preservation with cached responses
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pickle

logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Types of cacheable operations."""
    PRODUCT_ANALYSIS = "product_analysis"
    TEXT_GENERATION = "text_generation"
    MARKET_RESEARCH = "market_research"
    CONVERSATION = "conversation"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    content: Any
    created_at: datetime
    expires_at: datetime
    operation_type: CacheType
    quality_score: float
    original_cost: float
    cache_hits: int = 0
    last_accessed: Optional[datetime] = None


@dataclass
class CacheStats:
    """Cache performance statistics."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    cost_savings: float
    quality_maintained: float
    storage_size: int


class IntelligentCache:
    """
    Intelligent caching system for FlipSync AI operations.
    
    Provides content-based caching with semantic similarity detection
    to reduce redundant API calls while maintaining quality standards.
    """

    def __init__(self, max_size: int = 10000, default_ttl: int = 86400):  # 24 hours
        """Initialize intelligent cache."""
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # LRU tracking
        
        # Statistics
        self.stats = CacheStats(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            hit_rate=0.0,
            cost_savings=0.0,
            quality_maintained=0.0,
            storage_size=0
        )
        
        # Configuration
        self.similarity_threshold = 0.85  # Minimum similarity for cache hit
        self.quality_threshold = 0.8  # Minimum quality for caching
        
        logger.info(f"IntelligentCache initialized: max_size={max_size}, ttl={default_ttl}s")

    async def get(
        self,
        operation_type: CacheType,
        content: str,
        context: Dict[str, Any],
        quality_requirement: float = 0.8
    ) -> Optional[Tuple[Any, float]]:
        """
        Get cached response for similar content.
        
        Returns:
            Tuple of (cached_response, quality_score) if cache hit, None if miss
        """
        
        self.stats.total_requests += 1
        
        # Generate cache key
        cache_key = self._generate_cache_key(operation_type, content, context)
        
        # Check for exact match first
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check if expired
            if datetime.now() > entry.expires_at:
                await self._remove_entry(cache_key)
                self.stats.cache_misses += 1
                self._update_stats()
                return None
            
            # Check quality requirement
            if entry.quality_score >= quality_requirement:
                # Update access tracking
                entry.cache_hits += 1
                entry.last_accessed = datetime.now()
                self._update_access_order(cache_key)
                
                self.stats.cache_hits += 1
                self.stats.cost_savings += entry.original_cost
                self._update_stats()
                
                logger.debug(f"Cache hit: {operation_type.value} (quality: {entry.quality_score:.2f})")
                return entry.content, entry.quality_score
        
        # Check for similar content
        similar_entry = await self._find_similar_entry(operation_type, content, context, quality_requirement)
        if similar_entry:
            # Update access tracking
            similar_entry.cache_hits += 1
            similar_entry.last_accessed = datetime.now()
            self._update_access_order(similar_entry.key)
            
            self.stats.cache_hits += 1
            self.stats.cost_savings += similar_entry.original_cost
            self._update_stats()
            
            logger.debug(f"Similar cache hit: {operation_type.value} (quality: {similar_entry.quality_score:.2f})")
            return similar_entry.content, similar_entry.quality_score
        
        # Cache miss
        self.stats.cache_misses += 1
        self._update_stats()
        logger.debug(f"Cache miss: {operation_type.value}")
        return None

    async def put(
        self,
        operation_type: CacheType,
        content: str,
        context: Dict[str, Any],
        response: Any,
        quality_score: float,
        original_cost: float,
        ttl: Optional[int] = None
    ):
        """Store response in cache."""
        
        # Only cache high-quality responses
        if quality_score < self.quality_threshold:
            logger.debug(f"Skipping cache: quality {quality_score:.2f} < {self.quality_threshold}")
            return
        
        # Generate cache key
        cache_key = self._generate_cache_key(operation_type, content, context)
        
        # Calculate expiration
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            content=response,
            created_at=datetime.now(),
            expires_at=expires_at,
            operation_type=operation_type,
            quality_score=quality_score,
            original_cost=original_cost
        )
        
        # Ensure cache size limit
        await self._ensure_cache_size()
        
        # Store entry
        self.cache[cache_key] = entry
        self.access_order.append(cache_key)
        
        # Update storage size
        self.stats.storage_size = len(self.cache)
        
        logger.debug(f"Cached: {operation_type.value} (quality: {quality_score:.2f}, cost: ${original_cost:.4f})")

    async def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        
        # Clean expired entries
        await self._cleanup_expired()
        
        # Update quality maintained
        if self.cache:
            total_quality = sum(entry.quality_score for entry in self.cache.values())
            self.stats.quality_maintained = total_quality / len(self.cache)
        
        return self.stats

    async def clear_expired(self):
        """Remove expired cache entries."""
        await self._cleanup_expired()

    async def clear_all(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()
        self.stats.storage_size = 0
        logger.info("Cache cleared")

    def _generate_cache_key(
        self,
        operation_type: CacheType,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate cache key based on content and context."""
        
        # Create normalized content for hashing
        normalized_content = {
            "operation_type": operation_type.value,
            "content": content.lower().strip(),
            "context": {k: str(v).lower() for k, v in context.items() if k in [
                "marketplace", "category", "analysis_type", "product_type"
            ]}
        }
        
        # Generate hash
        content_str = json.dumps(normalized_content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    async def _find_similar_entry(
        self,
        operation_type: CacheType,
        content: str,
        context: Dict[str, Any],
        quality_requirement: float
    ) -> Optional[CacheEntry]:
        """Find similar cached entry using content similarity."""
        
        # For now, implement basic similarity based on content overlap
        # In production, this could use semantic embeddings
        
        content_words = set(content.lower().split())
        best_entry = None
        best_similarity = 0.0
        
        for entry in self.cache.values():
            # Skip expired entries
            if datetime.now() > entry.expires_at:
                continue
            
            # Skip different operation types
            if entry.operation_type != operation_type:
                continue
            
            # Skip low quality entries
            if entry.quality_score < quality_requirement:
                continue
            
            # Calculate content similarity (simple word overlap)
            if hasattr(entry.content, 'get') and 'analysis_text' in entry.content:
                cached_words = set(entry.content['analysis_text'].lower().split())
                overlap = len(content_words.intersection(cached_words))
                similarity = overlap / max(len(content_words), len(cached_words), 1)
                
                if similarity >= self.similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_entry = entry
        
        return best_entry

    async def _ensure_cache_size(self):
        """Ensure cache doesn't exceed maximum size."""
        
        while len(self.cache) >= self.max_size:
            # Remove least recently used entry
            if self.access_order:
                lru_key = self.access_order.pop(0)
                if lru_key in self.cache:
                    await self._remove_entry(lru_key)

    async def _remove_entry(self, cache_key: str):
        """Remove cache entry."""
        
        if cache_key in self.cache:
            del self.cache[cache_key]
        
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        
        self.stats.storage_size = len(self.cache)

    def _update_access_order(self, cache_key: str):
        """Update LRU access order."""
        
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        self.access_order.append(cache_key)

    def _update_stats(self):
        """Update cache statistics."""
        
        if self.stats.total_requests > 0:
            self.stats.hit_rate = self.stats.cache_hits / self.stats.total_requests

    async def _cleanup_expired(self):
        """Remove expired cache entries."""
        
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now > entry.expires_at
        ]
        
        for key in expired_keys:
            await self._remove_entry(key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache instance
_cache_instance = None


def get_intelligent_cache(max_size: int = 10000, ttl: int = 86400) -> IntelligentCache:
    """Get global intelligent cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = IntelligentCache(max_size, ttl)
    return _cache_instance


# Convenience functions for common operations
async def cache_product_analysis(
    content: str,
    context: Dict[str, Any],
    response: Any,
    quality_score: float,
    original_cost: float
):
    """Cache product analysis response."""
    cache = get_intelligent_cache()
    await cache.put(
        CacheType.PRODUCT_ANALYSIS,
        content,
        context,
        response,
        quality_score,
        original_cost
    )


async def get_cached_product_analysis(
    content: str,
    context: Dict[str, Any],
    quality_requirement: float = 0.8
) -> Optional[Tuple[Any, float]]:
    """Get cached product analysis response."""
    cache = get_intelligent_cache()
    return await cache.get(
        CacheType.PRODUCT_ANALYSIS,
        content,
        context,
        quality_requirement
    )
