#!/usr/bin/env python3
"""
Phase 3 Model Fine-tuning Orchestrator for FlipSync
===================================================

This module orchestrates all Phase 3 optimization components:
- Advanced prompt optimization engine
- Domain-specific training framework
- Fine-tuning simulation system

Target: 20-30% additional cost reduction from Phase 2 baseline of $0.0014 per operation.

Features:
- Unified fine-tuning optimization interface
- Coordinated component integration with Phase 1 & 2
- Performance tracking and analytics
- Quality assurance maintenance
- Integration with existing caching, batching, and deduplication
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .advanced_prompt_optimizer import (
    AdvancedPromptOptimizer,
    ECommerceTaskType,
    PromptOptimizationType,
    get_advanced_prompt_optimizer,
)
from .domain_training_framework import (
    DomainTrainingFramework,
    TrainingDataType,
    MarketplaceType,
    get_domain_training_framework,
)
from .fine_tuning_simulator import (
    FineTuningSimulator,
    FineTuningType,
    ModelPerformanceLevel,
    get_fine_tuning_simulator,
)
from .phase2_optimizer import Phase2Optimizer, get_phase2_optimizer

logger = logging.getLogger(__name__)


@dataclass
class Phase3OptimizationResult:
    """Result of Phase 3 optimization."""

    response: Any
    quality_score: float
    original_cost: float
    phase2_cost: float
    phase3_cost: float
    total_cost_savings: float
    optimization_methods: List[str]
    processing_time: float
    fine_tuning_applied: bool = False
    prompt_optimized: bool = False
    domain_enhanced: bool = False


@dataclass
class Phase3Stats:
    """Phase 3 optimization statistics."""

    total_requests: int
    fine_tuning_applied: int
    prompt_optimized: int
    domain_enhanced: int
    total_cost_savings: float
    average_cost_reduction: float
    quality_maintained: float
    processing_time_saved: float
    phase3_efficiency_gain: float


class Phase3Optimizer:
    """
    Phase 3 model fine-tuning orchestrator.

    Coordinates advanced prompt optimization, domain training, and fine-tuning
    simulation to achieve 20-30% additional cost reduction from Phase 2 baseline.
    """

    def __init__(self):
        """Initialize Phase 3 optimizer."""

        # Component instances
        self.prompt_optimizer = get_advanced_prompt_optimizer()
        self.domain_framework = get_domain_training_framework()
        self.fine_tuning_simulator = get_fine_tuning_simulator()
        self.phase2_optimizer = get_phase2_optimizer()

        # Statistics
        self.stats = Phase3Stats(
            total_requests=0,
            fine_tuning_applied=0,
            prompt_optimized=0,
            domain_enhanced=0,
            total_cost_savings=0.0,
            average_cost_reduction=0.0,
            quality_maintained=0.0,
            processing_time_saved=0.0,
            phase3_efficiency_gain=0.0,
        )

        # Configuration
        self.phase1_baseline_cost = 0.0024  # Phase 1 baseline
        self.phase2_baseline_cost = 0.0014  # Phase 2 baseline
        self.phase3_target_reduction = (
            0.143  # 14.3% additional reduction target (realistic)
        )
        self.quality_threshold = 0.85  # Higher quality threshold for better results
        self.optimization_enabled = True
        self.quality_preservation_mode = True  # Prioritize quality preservation

        logger.info("Phase3Optimizer initialized with all fine-tuning components")

    async def start(self):
        """Start Phase 3 optimization components."""

        await self.phase2_optimizer.start()
        logger.info("Phase 3 optimization started")

    async def stop(self):
        """Stop Phase 3 optimization components."""

        await self.phase2_optimizer.stop()
        logger.info("Phase 3 optimization stopped")

    async def optimize_request(
        self,
        operation_type: str,
        content: str,
        context: Dict[str, Any],
        quality_requirement: float = 0.8,
        priority: int = 1,
    ) -> Phase3OptimizationResult:
        """
        Optimize AI request using Phase 3 fine-tuning components.

        Returns:
            Phase3OptimizationResult with response and optimization details
        """

        start_time = time.time()
        self.stats.total_requests += 1

        original_cost = self.phase1_baseline_cost
        phase2_cost = self.phase2_baseline_cost
        optimization_methods = []

        try:
            # Step 1: Apply Phase 2 optimization first
            phase2_result = await self.phase2_optimizer.optimize_request(
                operation_type, content, context, quality_requirement, priority
            )

            current_cost = phase2_result.optimized_cost
            current_response = phase2_result.response
            current_quality = phase2_result.quality_score

            if phase2_result.optimization_method != "individual":
                optimization_methods.append(
                    f"phase2_{phase2_result.optimization_method}"
                )

            # Step 2: Apply advanced prompt optimization
            task_type = self._map_to_ecommerce_task(operation_type)
            if task_type and self.optimization_enabled:

                optimized_prompt, system_prompt, prompt_result = (
                    await self.prompt_optimizer.optimize_prompt(
                        task_type, content, context, quality_requirement
                    )
                )

                if (
                    abs(prompt_result.token_reduction_percent) > 5
                ):  # Significant optimization
                    self.stats.prompt_optimized += 1
                    optimization_methods.append("prompt_optimization")

                    # Apply conservative cost reduction with quality preservation
                    base_reduction = min(
                        0.12, abs(prompt_result.token_reduction_percent) / 100
                    )
                    quality_factor = max(
                        0.5, prompt_result.quality_score / self.quality_threshold
                    )
                    prompt_cost_reduction = (
                        base_reduction * quality_factor
                    )  # Quality-adjusted reduction

                    current_cost = current_cost * (1 - prompt_cost_reduction)
                    # Only improve quality if the optimization actually improves it
                    if prompt_result.quality_score > current_quality:
                        current_quality = prompt_result.quality_score

            # Step 3: Apply domain-specific enhancements
            training_type = self._map_to_training_type(operation_type)
            marketplace = self._extract_marketplace(context)

            if training_type and marketplace:
                domain_response = await self.domain_framework.get_domain_optimization(
                    training_type, content, marketplace, context
                )

                if domain_response.get("cost_reduction", 0) > 0:
                    self.stats.domain_enhanced += 1
                    optimization_methods.append("domain_enhancement")

                    # Apply conservative domain optimization with quality focus
                    base_domain_reduction = domain_response.get("cost_reduction", 0)
                    quality_improvement = domain_response.get("quality_improvement", 0)

                    # Only apply cost reduction if quality is maintained or improved
                    if quality_improvement >= 0:
                        domain_cost_reduction = min(
                            0.08, base_domain_reduction
                        )  # Conservative 8% max
                        current_cost = current_cost * (1 - domain_cost_reduction)
                        current_quality = min(
                            1.0, current_quality + max(0, quality_improvement)
                        )

            # Step 4: Apply fine-tuning simulation
            fine_tuning_type = self._map_to_fine_tuning_type(operation_type)
            if fine_tuning_type and self.optimization_enabled:

                fine_tuned_response = (
                    await self.fine_tuning_simulator.get_fine_tuned_response(
                        fine_tuning_type,
                        content,
                        context,
                        ModelPerformanceLevel.FINE_TUNED,
                    )
                )

                if fine_tuned_response.get("cost_reduction", 0) > 0:
                    self.stats.fine_tuning_applied += 1
                    optimization_methods.append("fine_tuning_simulation")

                    # Apply conservative fine-tuning benefits with quality validation
                    base_ft_reduction = fine_tuned_response.get("cost_reduction", 0)
                    enhanced_accuracy = fine_tuned_response.get(
                        "enhanced_accuracy", current_quality
                    )

                    # Only apply cost reduction if quality is maintained or improved
                    if enhanced_accuracy >= current_quality:
                        ft_cost_reduction = min(
                            0.10, base_ft_reduction
                        )  # Conservative 10% max
                        current_cost = current_cost * (1 - ft_cost_reduction)
                        current_quality = enhanced_accuracy
                    else:
                        # If quality would degrade, skip fine-tuning optimization
                        optimization_methods.remove("fine_tuning_simulation")
                        self.stats.fine_tuning_applied -= 1

                    # Update response with fine-tuning enhancements
                    current_response = {
                        **current_response,
                        "fine_tuning_applied": True,
                        "fine_tuned_model": fine_tuned_response.get("fine_tuned_model"),
                        "specialization_areas": fine_tuned_response.get(
                            "specialization_areas", []
                        ),
                    }

            # Calculate final metrics
            total_cost_savings = original_cost - current_cost
            processing_time = time.time() - start_time

            # Update statistics
            self._update_stats(
                original_cost, current_cost, current_quality, processing_time
            )

            return Phase3OptimizationResult(
                response=current_response,
                quality_score=current_quality,
                original_cost=original_cost,
                phase2_cost=phase2_cost,
                phase3_cost=current_cost,
                total_cost_savings=total_cost_savings,
                optimization_methods=optimization_methods,
                processing_time=processing_time,
                fine_tuning_applied="fine_tuning_simulation" in optimization_methods,
                prompt_optimized="prompt_optimization" in optimization_methods,
                domain_enhanced="domain_enhancement" in optimization_methods,
            )

        except Exception as e:
            logger.error(f"Phase 3 optimization failed: {e}")

            # Fallback to Phase 2 optimization
            phase2_result = await self.phase2_optimizer.optimize_request(
                operation_type, content, context, quality_requirement, priority
            )

            processing_time = time.time() - start_time

            return Phase3OptimizationResult(
                response=phase2_result.response,
                quality_score=phase2_result.quality_score,
                original_cost=original_cost,
                phase2_cost=phase2_cost,
                phase3_cost=phase2_result.optimized_cost,
                total_cost_savings=original_cost - phase2_result.optimized_cost,
                optimization_methods=["fallback_phase2"],
                processing_time=processing_time,
            )

    async def get_stats(self) -> Phase3Stats:
        """Get Phase 3 optimization statistics."""

        # Update average cost reduction
        if self.stats.total_requests > 0:
            self.stats.average_cost_reduction = (
                self.stats.total_cost_savings
                / (self.stats.total_requests * self.phase1_baseline_cost)
            ) * 100

            # Calculate Phase 3 specific efficiency gain
            phase2_baseline_savings = (
                self.phase1_baseline_cost - self.phase2_baseline_cost
            ) * self.stats.total_requests
            phase3_additional_savings = (
                self.stats.total_cost_savings - phase2_baseline_savings
            )

            if phase2_baseline_savings > 0:
                self.stats.phase3_efficiency_gain = (
                    phase3_additional_savings / phase2_baseline_savings
                ) * 100

        return self.stats

    async def get_component_stats(self) -> Dict[str, Any]:
        """Get detailed statistics from all components."""

        prompt_metrics = await self.prompt_optimizer.get_performance_metrics()
        domain_metrics = await self.domain_framework.get_performance_metrics()
        fine_tuning_metrics = await self.fine_tuning_simulator.get_performance_metrics()
        phase2_stats = await self.phase2_optimizer.get_component_stats()

        return {
            "phase3_overall": asdict(await self.get_stats()),
            "prompt_optimization": asdict(prompt_metrics),
            "domain_training": asdict(domain_metrics),
            "fine_tuning_simulation": asdict(fine_tuning_metrics),
            "phase2_integration": phase2_stats,
        }

    def _map_to_ecommerce_task(
        self, operation_type: str
    ) -> Optional[ECommerceTaskType]:
        """Map operation type to e-commerce task type."""

        mapping = {
            "vision_analysis": ECommerceTaskType.PRODUCT_IDENTIFICATION,
            "product_analysis": ECommerceTaskType.PRODUCT_IDENTIFICATION,
            "listing_generation": ECommerceTaskType.LISTING_GENERATION,
            "content_creation": ECommerceTaskType.LISTING_GENERATION,
            "market_research": ECommerceTaskType.MARKET_ANALYSIS,
            "price_optimization": ECommerceTaskType.PRICE_OPTIMIZATION,
            "seo_optimization": ECommerceTaskType.SEO_OPTIMIZATION,
            "category_classification": ECommerceTaskType.CATEGORY_CLASSIFICATION,
        }

        return mapping.get(operation_type.lower())

    def _map_to_training_type(self, operation_type: str) -> Optional[TrainingDataType]:
        """Map operation type to training data type."""

        mapping = {
            "vision_analysis": TrainingDataType.PRODUCT_IDENTIFICATION,
            "product_analysis": TrainingDataType.PRODUCT_IDENTIFICATION,
            "listing_generation": TrainingDataType.LISTING_OPTIMIZATION,
            "content_creation": TrainingDataType.LISTING_OPTIMIZATION,
            "market_research": TrainingDataType.MARKET_ANALYSIS,
            "price_optimization": TrainingDataType.PRICE_OPTIMIZATION,
            "category_classification": TrainingDataType.CATEGORY_CLASSIFICATION,
            "seo_optimization": TrainingDataType.SEO_OPTIMIZATION,
        }

        return mapping.get(operation_type.lower())

    def _map_to_fine_tuning_type(self, operation_type: str) -> Optional[FineTuningType]:
        """Map operation type to fine-tuning type."""

        mapping = {
            "vision_analysis": FineTuningType.PRODUCT_ANALYSIS,
            "product_analysis": FineTuningType.PRODUCT_ANALYSIS,
            "listing_generation": FineTuningType.LISTING_GENERATION,
            "content_creation": FineTuningType.LISTING_GENERATION,
            "market_research": FineTuningType.MARKET_RESEARCH,
            "price_optimization": FineTuningType.PRICE_OPTIMIZATION,
        }

        return mapping.get(operation_type.lower())

    def _extract_marketplace(self, context: Dict[str, Any]) -> MarketplaceType:
        """Extract marketplace from context."""

        marketplace_str = context.get("marketplace", "ebay").lower()

        marketplace_mapping = {
            "ebay": MarketplaceType.EBAY,
            "amazon": MarketplaceType.AMAZON,
            "etsy": MarketplaceType.ETSY,
            "facebook": MarketplaceType.FACEBOOK,
            "mercari": MarketplaceType.MERCARI,
        }

        return marketplace_mapping.get(marketplace_str, MarketplaceType.EBAY)

    def _update_stats(
        self,
        original_cost: float,
        optimized_cost: float,
        quality_score: float,
        processing_time: float,
    ):
        """Update Phase 3 statistics."""

        cost_savings = original_cost - optimized_cost
        self.stats.total_cost_savings += cost_savings

        # Update quality maintained (running average)
        total_requests = self.stats.total_requests
        if total_requests == 1:
            self.stats.quality_maintained = quality_score
        else:
            self.stats.quality_maintained = (
                self.stats.quality_maintained * (total_requests - 1) + quality_score
            ) / total_requests

        # Update processing time saved
        baseline_processing_time = 0.3  # Estimated baseline
        if processing_time < baseline_processing_time:
            self.stats.processing_time_saved += (
                baseline_processing_time - processing_time
            )


# Global Phase 3 optimizer instance
_phase3_optimizer_instance = None


def get_phase3_optimizer() -> Phase3Optimizer:
    """Get global Phase 3 optimizer instance."""
    global _phase3_optimizer_instance
    if _phase3_optimizer_instance is None:
        _phase3_optimizer_instance = Phase3Optimizer()
    return _phase3_optimizer_instance


# Convenience function for optimized AI requests
async def optimize_ai_request_phase3(
    operation_type: str,
    content: str,
    context: Dict[str, Any],
    quality_requirement: float = 0.8,
    priority: int = 1,
) -> Phase3OptimizationResult:
    """Optimize AI request using Phase 3 fine-tuning components."""
    optimizer = get_phase3_optimizer()
    return await optimizer.optimize_request(
        operation_type, content, context, quality_requirement, priority
    )
