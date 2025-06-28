#!/usr/bin/env python3
"""
Phase 2 Cost Optimization Orchestrator for FlipSync
===================================================

This module orchestrates all Phase 2 optimization components:
- Intelligent caching system
- Batch processing framework  
- Request deduplication system

Target: 30-55% additional cost reduction from Phase 1 baseline of $0.0024 per operation.

Features:
- Unified optimization interface
- Coordinated component integration
- Performance tracking and analytics
- Quality assurance maintenance
- Integration with Phase 1 intelligent model router
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .intelligent_cache import (
    IntelligentCache, CacheType, get_intelligent_cache,
    cache_product_analysis, get_cached_product_analysis
)
from .batch_processor import (
    BatchProcessor, BatchType, BatchRequest, BatchResult,
    get_batch_processor
)
from .request_deduplicator import (
    RequestDeduplicator, DeduplicationResult,
    get_request_deduplicator, check_request_duplicate
)

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of Phase 2 optimization."""
    response: Any
    quality_score: float
    original_cost: float
    optimized_cost: float
    cost_savings: float
    optimization_method: str
    processing_time: float
    cache_hit: bool = False
    batch_processed: bool = False
    deduplicated: bool = False


@dataclass
class Phase2Stats:
    """Phase 2 optimization statistics."""
    total_requests: int
    cache_hits: int
    batch_processed: int
    deduplicated: int
    total_cost_savings: float
    average_cost_reduction: float
    quality_maintained: float
    processing_time_saved: float


class Phase2Optimizer:
    """
    Phase 2 cost optimization orchestrator.
    
    Coordinates caching, batch processing, and deduplication to achieve
    30-55% additional cost reduction from Phase 1 baseline.
    """

    def __init__(self):
        """Initialize Phase 2 optimizer."""
        
        # Component instances
        self.cache = get_intelligent_cache()
        self.batch_processor = get_batch_processor()
        self.deduplicator = get_request_deduplicator()
        
        # Statistics
        self.stats = Phase2Stats(
            total_requests=0,
            cache_hits=0,
            batch_processed=0,
            deduplicated=0,
            total_cost_savings=0.0,
            average_cost_reduction=0.0,
            quality_maintained=0.0,
            processing_time_saved=0.0
        )
        
        # Configuration
        self.phase1_baseline_cost = 0.0024  # Phase 1 validated baseline
        self.quality_threshold = 0.8
        self.optimization_enabled = True
        
        logger.info("Phase2Optimizer initialized with all components")

    async def start(self):
        """Start Phase 2 optimization components."""
        
        await self.batch_processor.start()
        logger.info("Phase 2 optimization started")

    async def stop(self):
        """Stop Phase 2 optimization components."""
        
        await self.batch_processor.stop()
        logger.info("Phase 2 optimization stopped")

    async def optimize_request(
        self,
        operation_type: str,
        content: str,
        context: Dict[str, Any],
        quality_requirement: float = 0.8,
        priority: int = 1
    ) -> OptimizationResult:
        """
        Optimize AI request using Phase 2 components.
        
        Returns:
            OptimizationResult with response and optimization details
        """
        
        start_time = time.time()
        self.stats.total_requests += 1
        
        original_cost = self.phase1_baseline_cost
        optimized_cost = original_cost
        optimization_method = "none"
        
        try:
            # Step 1: Check for request deduplication
            dedup_result = await check_request_duplicate(
                operation_type, content, context, original_cost
            )
            
            if dedup_result.is_duplicate:
                # Request is duplicate - return cached result or wait for original
                self.stats.deduplicated += 1
                optimized_cost = 0.0  # No cost for duplicate
                optimization_method = "deduplication"
                
                # For demo, return a simulated deduplicated response
                response = {
                    "result": f"Deduplicated response for {operation_type}",
                    "quality": "maintained",
                    "optimization": "deduplication"
                }
                quality_score = 0.85
                
                processing_time = time.time() - start_time
                self._update_stats(original_cost, optimized_cost, quality_score, processing_time)
                
                return OptimizationResult(
                    response=response,
                    quality_score=quality_score,
                    original_cost=original_cost,
                    optimized_cost=optimized_cost,
                    cost_savings=original_cost - optimized_cost,
                    optimization_method=optimization_method,
                    processing_time=processing_time,
                    deduplicated=True
                )
            
            # Step 2: Check intelligent cache
            cache_type = self._map_to_cache_type(operation_type)
            if cache_type:
                cached_result = await self.cache.get(
                    cache_type, content, context, quality_requirement
                )
                
                if cached_result:
                    response, quality_score = cached_result
                    self.stats.cache_hits += 1
                    optimized_cost = 0.0  # No cost for cache hit
                    optimization_method = "cache"
                    
                    processing_time = time.time() - start_time
                    self._update_stats(original_cost, optimized_cost, quality_score, processing_time)
                    
                    return OptimizationResult(
                        response=response,
                        quality_score=quality_score,
                        original_cost=original_cost,
                        optimized_cost=optimized_cost,
                        cost_savings=original_cost - optimized_cost,
                        optimization_method=optimization_method,
                        processing_time=processing_time,
                        cache_hit=True
                    )
            
            # Step 3: Use batch processing for new requests
            batch_type = self._map_to_batch_type(operation_type)
            if batch_type and self.optimization_enabled:
                
                # Submit to batch processor
                request_id = await self.batch_processor.submit_request(
                    batch_type, content, context, quality_requirement, priority
                )
                
                # Get batch result
                batch_result = await self.batch_processor.get_result(request_id)
                
                if batch_result.success:
                    self.stats.batch_processed += 1
                    optimized_cost = batch_result.cost
                    optimization_method = "batch_processing"
                    
                    # Cache the result for future use
                    if cache_type and batch_result.quality_score >= self.quality_threshold:
                        await self.cache.put(
                            cache_type, content, context,
                            batch_result.response, batch_result.quality_score, original_cost
                        )
                    
                    processing_time = time.time() - start_time
                    self._update_stats(original_cost, optimized_cost, batch_result.quality_score, processing_time)
                    
                    return OptimizationResult(
                        response=batch_result.response,
                        quality_score=batch_result.quality_score,
                        original_cost=original_cost,
                        optimized_cost=optimized_cost,
                        cost_savings=original_cost - optimized_cost,
                        optimization_method=optimization_method,
                        processing_time=processing_time,
                        batch_processed=True
                    )
            
            # Step 4: Fallback to individual processing (Phase 1 baseline)
            response, quality_score = await self._process_individual_request(
                operation_type, content, context, quality_requirement
            )
            
            optimization_method = "individual"
            optimized_cost = original_cost  # No optimization applied
            
            # Cache the result for future use
            if cache_type and quality_score >= self.quality_threshold:
                await self.cache.put(
                    cache_type, content, context,
                    response, quality_score, original_cost
                )
            
            processing_time = time.time() - start_time
            self._update_stats(original_cost, optimized_cost, quality_score, processing_time)
            
            return OptimizationResult(
                response=response,
                quality_score=quality_score,
                original_cost=original_cost,
                optimized_cost=optimized_cost,
                cost_savings=original_cost - optimized_cost,
                optimization_method=optimization_method,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Phase 2 optimization failed: {e}")
            
            # Fallback to basic processing
            response, quality_score = await self._process_individual_request(
                operation_type, content, context, quality_requirement
            )
            
            processing_time = time.time() - start_time
            
            return OptimizationResult(
                response=response,
                quality_score=quality_score,
                original_cost=original_cost,
                optimized_cost=original_cost,
                cost_savings=0.0,
                optimization_method="fallback",
                processing_time=processing_time
            )

    async def get_stats(self) -> Phase2Stats:
        """Get Phase 2 optimization statistics."""
        
        # Update average cost reduction
        if self.stats.total_requests > 0:
            self.stats.average_cost_reduction = (
                self.stats.total_cost_savings / (self.stats.total_requests * self.phase1_baseline_cost)
            ) * 100
        
        return self.stats

    async def get_component_stats(self) -> Dict[str, Any]:
        """Get detailed statistics from all components."""
        
        cache_stats = await self.cache.get_stats()
        batch_stats = await self.batch_processor.get_stats()
        dedup_stats = await self.deduplicator.get_stats()
        
        return {
            "phase2_overall": asdict(await self.get_stats()),
            "cache": asdict(cache_stats),
            "batch_processor": asdict(batch_stats),
            "deduplicator": asdict(dedup_stats)
        }

    def _map_to_cache_type(self, operation_type: str) -> Optional[CacheType]:
        """Map operation type to cache type."""
        
        mapping = {
            "vision_analysis": CacheType.PRODUCT_ANALYSIS,
            "product_analysis": CacheType.PRODUCT_ANALYSIS,
            "text_generation": CacheType.TEXT_GENERATION,
            "content_creation": CacheType.TEXT_GENERATION,
            "market_research": CacheType.MARKET_RESEARCH,
            "conversation": CacheType.CONVERSATION
        }
        
        return mapping.get(operation_type.lower())

    def _map_to_batch_type(self, operation_type: str) -> Optional[BatchType]:
        """Map operation type to batch type."""
        
        mapping = {
            "vision_analysis": BatchType.VISION_ANALYSIS,
            "product_analysis": BatchType.VISION_ANALYSIS,
            "text_generation": BatchType.TEXT_GENERATION,
            "content_creation": BatchType.TEXT_GENERATION,
            "market_research": BatchType.MARKET_RESEARCH,
            "content_optimization": BatchType.CONTENT_OPTIMIZATION
        }
        
        return mapping.get(operation_type.lower())

    async def _process_individual_request(
        self,
        operation_type: str,
        content: str,
        context: Dict[str, Any],
        quality_requirement: float
    ) -> Tuple[Any, float]:
        """Process individual request (Phase 1 baseline)."""
        
        # Simulate individual processing with Phase 1 baseline
        await asyncio.sleep(0.2)  # Simulate processing time
        
        response = {
            "result": f"Individual processing result for {operation_type}",
            "content": content,
            "context": context,
            "optimization": "none"
        }
        
        quality_score = 0.88  # Phase 1 validated quality
        
        return response, quality_score

    def _update_stats(
        self,
        original_cost: float,
        optimized_cost: float,
        quality_score: float,
        processing_time: float
    ):
        """Update Phase 2 statistics."""
        
        cost_savings = original_cost - optimized_cost
        self.stats.total_cost_savings += cost_savings
        
        # Update quality maintained (running average)
        total_requests = self.stats.total_requests
        if total_requests == 1:
            self.stats.quality_maintained = quality_score
        else:
            self.stats.quality_maintained = (
                (self.stats.quality_maintained * (total_requests - 1) + quality_score) / total_requests
            )
        
        # Update processing time saved (if optimization was applied)
        if optimized_cost < original_cost:
            self.stats.processing_time_saved += max(0, 0.2 - processing_time)  # Baseline 0.2s


# Global Phase 2 optimizer instance
_phase2_optimizer_instance = None


def get_phase2_optimizer() -> Phase2Optimizer:
    """Get global Phase 2 optimizer instance."""
    global _phase2_optimizer_instance
    if _phase2_optimizer_instance is None:
        _phase2_optimizer_instance = Phase2Optimizer()
    return _phase2_optimizer_instance


# Convenience function for optimized AI requests
async def optimize_ai_request(
    operation_type: str,
    content: str,
    context: Dict[str, Any],
    quality_requirement: float = 0.8,
    priority: int = 1
) -> OptimizationResult:
    """Optimize AI request using Phase 2 components."""
    optimizer = get_phase2_optimizer()
    return await optimizer.optimize_request(
        operation_type, content, context, quality_requirement, priority
    )
