"""
FlipSync Phase 2 Cost Optimization Package
==========================================

This package provides Phase 2 cost optimization components for FlipSync's
AI operations, targeting 30-55% additional cost reduction from the Phase 1
baseline of $0.0024 per operation.

Components:
- Intelligent caching system for similar product analyses
- Batch processing framework for simultaneous operations
- Request deduplication to eliminate redundant API calls
- Phase 2 orchestrator for coordinated optimization

Features:
- Integration with Phase 1 intelligent model router
- Quality assurance maintenance (>80% threshold)
- Real-time cost tracking and analytics
- Production-ready Docker deployment
"""

from .intelligent_cache import (
    IntelligentCache,
    CacheType,
    CacheEntry,
    CacheStats,
    get_intelligent_cache,
    cache_product_analysis,
    get_cached_product_analysis,
)

from .batch_processor import (
    BatchProcessor,
    BatchType,
    BatchRequest,
    BatchResult,
    BatchStats,
    get_batch_processor,
)

from .request_deduplicator import (
    RequestDeduplicator,
    DeduplicationStrategy,
    RequestFingerprint,
    DeduplicationResult,
    DeduplicationStats,
    get_request_deduplicator,
    check_request_duplicate,
)

from .phase2_optimizer import (
    Phase2Optimizer,
    OptimizationResult,
    Phase2Stats,
    get_phase2_optimizer,
    optimize_ai_request,
)

from .advanced_prompt_optimizer import (
    AdvancedPromptOptimizer,
    ECommerceTaskType,
    PromptOptimizationType,
    OptimizedPrompt,
    PromptOptimizationResult,
    PromptPerformanceMetrics,
    get_advanced_prompt_optimizer,
    optimize_product_identification_prompt,
    optimize_listing_generation_prompt,
    optimize_market_analysis_prompt,
)

from .domain_training_framework import (
    DomainTrainingFramework,
    TrainingDataType,
    MarketplaceType,
    TrainingExample,
    DomainTrainingResult,
    DomainPerformanceMetrics,
    get_domain_training_framework,
    train_product_identification,
    train_listing_optimization,
)

from .fine_tuning_simulator import (
    FineTuningSimulator,
    FineTuningType,
    ModelPerformanceLevel,
    FineTuningResult,
    ModelPerformanceMetrics,
    FineTunedModelConfig,
    get_fine_tuning_simulator,
    simulate_product_analysis_tuning,
    simulate_listing_generation_tuning,
)

from .phase3_optimizer import (
    Phase3Optimizer,
    Phase3OptimizationResult,
    Phase3Stats,
    get_phase3_optimizer,
    optimize_ai_request_phase3,
)

__all__ = [
    # Intelligent Cache
    "IntelligentCache",
    "CacheType",
    "CacheEntry",
    "CacheStats",
    "get_intelligent_cache",
    "cache_product_analysis",
    "get_cached_product_analysis",
    # Batch Processor
    "BatchProcessor",
    "BatchType",
    "BatchRequest",
    "BatchResult",
    "BatchStats",
    "get_batch_processor",
    # Request Deduplicator
    "RequestDeduplicator",
    "DeduplicationStrategy",
    "RequestFingerprint",
    "DeduplicationResult",
    "DeduplicationStats",
    "get_request_deduplicator",
    "check_request_duplicate",
    # Phase 2 Optimizer
    "Phase2Optimizer",
    "OptimizationResult",
    "Phase2Stats",
    "get_phase2_optimizer",
    "optimize_ai_request",
    # Advanced Prompt Optimizer
    "AdvancedPromptOptimizer",
    "ECommerceTaskType",
    "PromptOptimizationType",
    "OptimizedPrompt",
    "PromptOptimizationResult",
    "PromptPerformanceMetrics",
    "get_advanced_prompt_optimizer",
    "optimize_product_identification_prompt",
    "optimize_listing_generation_prompt",
    "optimize_market_analysis_prompt",
    # Domain Training Framework
    "DomainTrainingFramework",
    "TrainingDataType",
    "MarketplaceType",
    "TrainingExample",
    "DomainTrainingResult",
    "DomainPerformanceMetrics",
    "get_domain_training_framework",
    "train_product_identification",
    "train_listing_optimization",
    # Fine-Tuning Simulator
    "FineTuningSimulator",
    "FineTuningType",
    "ModelPerformanceLevel",
    "FineTuningResult",
    "ModelPerformanceMetrics",
    "FineTunedModelConfig",
    "get_fine_tuning_simulator",
    "simulate_product_analysis_tuning",
    "simulate_listing_generation_tuning",
    # Phase 3 Optimizer
    "Phase3Optimizer",
    "Phase3OptimizationResult",
    "Phase3Stats",
    "get_phase3_optimizer",
    "optimize_ai_request_phase3",
]
