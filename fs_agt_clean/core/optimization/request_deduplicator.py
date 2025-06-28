#!/usr/bin/env python3
"""
Request Deduplication System for FlipSync Phase 2 Optimization
==============================================================

This module provides intelligent request deduplication to eliminate
redundant API calls within time windows, contributing to cost reduction.

Features:
- Request fingerprinting and duplicate detection
- Time-window based deduplication (configurable windows)
- Deduplication savings tracking and analytics
- Request integrity maintenance and quality preservation
- Integration with caching and batch processing systems
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class DeduplicationStrategy(Enum):
    """Deduplication strategies."""
    EXACT_MATCH = "exact_match"
    CONTENT_SIMILARITY = "content_similarity"
    SEMANTIC_SIMILARITY = "semantic_similarity"


@dataclass
class RequestFingerprint:
    """Request fingerprint for deduplication."""
    fingerprint: str
    operation_type: str
    content_hash: str
    context_hash: str
    created_at: datetime
    expires_at: datetime
    request_count: int = 1
    last_seen: Optional[datetime] = None


@dataclass
class DeduplicationResult:
    """Result of deduplication check."""
    is_duplicate: bool
    original_fingerprint: Optional[str]
    similarity_score: float
    time_since_original: Optional[float]
    cost_saved: float


@dataclass
class DeduplicationStats:
    """Deduplication performance statistics."""
    total_requests: int
    duplicate_requests: int
    unique_requests: int
    deduplication_rate: float
    cost_savings: float
    average_similarity: float
    time_window_hits: int


class RequestDeduplicator:
    """
    Intelligent request deduplication system for FlipSync AI operations.
    
    Identifies and eliminates redundant API calls within configurable time
    windows to reduce costs while maintaining request integrity.
    """

    def __init__(
        self,
        deduplication_window: int = 3600,  # 1 hour default
        similarity_threshold: float = 0.9,
        max_fingerprints: int = 50000
    ):
        """Initialize request deduplicator."""
        self.deduplication_window = deduplication_window
        self.similarity_threshold = similarity_threshold
        self.max_fingerprints = max_fingerprints
        
        # Fingerprint storage
        self.fingerprints: Dict[str, RequestFingerprint] = {}
        self.content_index: Dict[str, Set[str]] = {}  # content_hash -> fingerprint_ids
        
        # Statistics
        self.stats = DeduplicationStats(
            total_requests=0,
            duplicate_requests=0,
            unique_requests=0,
            deduplication_rate=0.0,
            cost_savings=0.0,
            average_similarity=0.0,
            time_window_hits=0
        )
        
        # Configuration
        self.strategy = DeduplicationStrategy.CONTENT_SIMILARITY
        
        logger.info(f"RequestDeduplicator initialized: window={deduplication_window}s, threshold={similarity_threshold}")

    async def check_duplicate(
        self,
        operation_type: str,
        content: str,
        context: Dict[str, Any],
        cost_per_request: float = 0.0024
    ) -> DeduplicationResult:
        """
        Check if request is a duplicate of recent requests.
        
        Returns:
            DeduplicationResult with duplicate status and savings information
        """
        
        self.stats.total_requests += 1
        
        # Generate fingerprint
        fingerprint = self._generate_fingerprint(operation_type, content, context)
        content_hash = self._generate_content_hash(content)
        
        # Clean expired fingerprints
        await self._cleanup_expired()
        
        # Check for exact match
        if fingerprint in self.fingerprints:
            existing = self.fingerprints[fingerprint]
            
            # Update existing fingerprint
            existing.request_count += 1
            existing.last_seen = datetime.now()
            
            self.stats.duplicate_requests += 1
            self.stats.cost_savings += cost_per_request
            self._update_stats()
            
            time_since = (datetime.now() - existing.created_at).total_seconds()
            
            logger.debug(f"Exact duplicate found: {fingerprint[:8]} (count: {existing.request_count})")
            
            return DeduplicationResult(
                is_duplicate=True,
                original_fingerprint=fingerprint,
                similarity_score=1.0,
                time_since_original=time_since,
                cost_saved=cost_per_request
            )
        
        # Check for similar content
        similar_result = await self._find_similar_request(
            operation_type, content, context, cost_per_request
        )
        
        if similar_result.is_duplicate:
            self.stats.duplicate_requests += 1
            self.stats.cost_savings += cost_per_request
            self._update_stats()
            return similar_result
        
        # No duplicate found - register new fingerprint
        await self._register_fingerprint(operation_type, content, context, fingerprint, content_hash)
        
        self.stats.unique_requests += 1
        self._update_stats()
        
        return DeduplicationResult(
            is_duplicate=False,
            original_fingerprint=None,
            similarity_score=0.0,
            time_since_original=None,
            cost_saved=0.0
        )

    async def get_stats(self) -> DeduplicationStats:
        """Get deduplication performance statistics."""
        
        # Clean expired fingerprints
        await self._cleanup_expired()
        
        return self.stats

    async def clear_expired(self):
        """Remove expired fingerprints."""
        await self._cleanup_expired()

    async def clear_all(self):
        """Clear all fingerprints."""
        self.fingerprints.clear()
        self.content_index.clear()
        logger.info("Deduplication cache cleared")

    def _generate_fingerprint(
        self,
        operation_type: str,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate unique fingerprint for request."""
        
        # Create normalized request data
        normalized_request = {
            "operation_type": operation_type.lower(),
            "content": content.lower().strip(),
            "context": {
                k: str(v).lower() for k, v in context.items()
                if k in ["marketplace", "category", "analysis_type", "product_type", "quality_requirement"]
            }
        }
        
        # Generate hash
        request_str = json.dumps(normalized_request, sort_keys=True)
        return hashlib.sha256(request_str.encode()).hexdigest()

    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content similarity matching."""
        
        # Normalize content for similarity matching
        normalized_content = content.lower().strip()
        
        # Remove common words and punctuation for better similarity
        words = normalized_content.split()
        significant_words = [w for w in words if len(w) > 3]  # Keep longer words
        
        content_for_hash = " ".join(sorted(significant_words))
        return hashlib.md5(content_for_hash.encode()).hexdigest()[:16]

    async def _find_similar_request(
        self,
        operation_type: str,
        content: str,
        context: Dict[str, Any],
        cost_per_request: float
    ) -> DeduplicationResult:
        """Find similar request within deduplication window."""
        
        content_hash = self._generate_content_hash(content)
        
        # Check content index for similar content
        if content_hash in self.content_index:
            for fingerprint_id in self.content_index[content_hash]:
                if fingerprint_id in self.fingerprints:
                    existing = self.fingerprints[fingerprint_id]
                    
                    # Check if within time window
                    time_since = (datetime.now() - existing.created_at).total_seconds()
                    if time_since <= self.deduplication_window:
                        
                        # Calculate similarity
                        similarity = self._calculate_similarity(
                            operation_type, content, context,
                            existing.operation_type, existing
                        )
                        
                        if similarity >= self.similarity_threshold:
                            # Update existing fingerprint
                            existing.request_count += 1
                            existing.last_seen = datetime.now()
                            
                            self.stats.time_window_hits += 1
                            
                            logger.debug(f"Similar request found: {fingerprint_id[:8]} (similarity: {similarity:.2f})")
                            
                            return DeduplicationResult(
                                is_duplicate=True,
                                original_fingerprint=fingerprint_id,
                                similarity_score=similarity,
                                time_since_original=time_since,
                                cost_saved=cost_per_request
                            )
        
        return DeduplicationResult(
            is_duplicate=False,
            original_fingerprint=None,
            similarity_score=0.0,
            time_since_original=None,
            cost_saved=0.0
        )

    def _calculate_similarity(
        self,
        operation_type1: str,
        content1: str,
        context1: Dict[str, Any],
        operation_type2: str,
        existing_fingerprint: RequestFingerprint
    ) -> float:
        """Calculate similarity between requests."""
        
        # Operation type must match
        if operation_type1.lower() != operation_type2.lower():
            return 0.0
        
        # For now, use content hash similarity
        # In production, this could use semantic embeddings
        
        content_hash1 = self._generate_content_hash(content1)
        
        # If content hashes match, high similarity
        if content_hash1 == existing_fingerprint.content_hash:
            return 0.95
        
        # Calculate word overlap similarity
        words1 = set(content1.lower().split())
        
        # We don't have the original content, so use a simplified approach
        # In production, we'd store more content information
        
        # For now, return moderate similarity if content hashes are similar
        hash_similarity = self._hash_similarity(content_hash1, existing_fingerprint.content_hash)
        
        return hash_similarity

    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between content hashes."""
        
        # Simple character-based similarity
        matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        return matches / max(len(hash1), len(hash2))

    async def _register_fingerprint(
        self,
        operation_type: str,
        content: str,
        context: Dict[str, Any],
        fingerprint: str,
        content_hash: str
    ):
        """Register new fingerprint."""
        
        # Ensure fingerprint storage limit
        await self._ensure_storage_limit()
        
        # Create fingerprint entry
        expires_at = datetime.now() + timedelta(seconds=self.deduplication_window)
        
        fingerprint_entry = RequestFingerprint(
            fingerprint=fingerprint,
            operation_type=operation_type,
            content_hash=content_hash,
            context_hash=hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()[:16],
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        # Store fingerprint
        self.fingerprints[fingerprint] = fingerprint_entry
        
        # Update content index
        if content_hash not in self.content_index:
            self.content_index[content_hash] = set()
        self.content_index[content_hash].add(fingerprint)
        
        logger.debug(f"Registered fingerprint: {fingerprint[:8]} ({operation_type})")

    async def _ensure_storage_limit(self):
        """Ensure fingerprint storage doesn't exceed limit."""
        
        while len(self.fingerprints) >= self.max_fingerprints:
            # Remove oldest fingerprint
            oldest_fingerprint = min(
                self.fingerprints.keys(),
                key=lambda k: self.fingerprints[k].created_at
            )
            await self._remove_fingerprint(oldest_fingerprint)

    async def _remove_fingerprint(self, fingerprint: str):
        """Remove fingerprint and update indices."""
        
        if fingerprint in self.fingerprints:
            entry = self.fingerprints[fingerprint]
            
            # Remove from content index
            if entry.content_hash in self.content_index:
                self.content_index[entry.content_hash].discard(fingerprint)
                if not self.content_index[entry.content_hash]:
                    del self.content_index[entry.content_hash]
            
            # Remove fingerprint
            del self.fingerprints[fingerprint]

    async def _cleanup_expired(self):
        """Remove expired fingerprints."""
        
        now = datetime.now()
        expired_fingerprints = [
            fingerprint for fingerprint, entry in self.fingerprints.items()
            if now > entry.expires_at
        ]
        
        for fingerprint in expired_fingerprints:
            await self._remove_fingerprint(fingerprint)
        
        if expired_fingerprints:
            logger.debug(f"Cleaned up {len(expired_fingerprints)} expired fingerprints")

    def _update_stats(self):
        """Update deduplication statistics."""
        
        if self.stats.total_requests > 0:
            self.stats.deduplication_rate = self.stats.duplicate_requests / self.stats.total_requests
        
        # Update average similarity (simplified calculation)
        if self.stats.duplicate_requests > 0:
            self.stats.average_similarity = 0.85  # Placeholder - would calculate from actual similarities


# Global deduplicator instance
_deduplicator_instance = None


def get_request_deduplicator(
    deduplication_window: int = 3600,
    similarity_threshold: float = 0.9,
    max_fingerprints: int = 50000
) -> RequestDeduplicator:
    """Get global request deduplicator instance."""
    global _deduplicator_instance
    if _deduplicator_instance is None:
        _deduplicator_instance = RequestDeduplicator(
            deduplication_window, similarity_threshold, max_fingerprints
        )
    return _deduplicator_instance


# Convenience functions
async def check_request_duplicate(
    operation_type: str,
    content: str,
    context: Dict[str, Any],
    cost_per_request: float = 0.0024
) -> DeduplicationResult:
    """Check if request is a duplicate."""
    deduplicator = get_request_deduplicator()
    return await deduplicator.check_duplicate(operation_type, content, context, cost_per_request)
