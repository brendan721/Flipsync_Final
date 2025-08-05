"""
HybridLLMAdapter - Compatibility Bridge for Legacy LLM Client Migration
=======================================================================

Provides seamless drop-in replacement for legacy LLM clients while routing
to HybridLLMClient's intelligent processing system.

Features:
- Backward-compatible generate_response() interface
- Intelligent use case detection from prompt analysis
- Performance-optimized routing (algorithmic → local → OpenAI)
- Docker-aware performance targets (<600ms algorithmic, <2500ms local, <5000ms OpenAI)
- Comprehensive error handling and fallback mechanisms
"""

import asyncio
import logging
import re
import time
from typing import Any, Dict, Optional, Union

from fs_agt_clean.core.ai.hybrid_llm_client import (
    HybridLLMClient,
    HybridLLMConfig,
    UseCase,
    ProcessingMode,
    ProcessingResult,
)
from fs_agt_clean.core.ai.llm_types import (
    LLMResponse,
    ModelProvider,
    SimpleLLMConfig,
)
from fs_agt_clean.core.cache.ai_cache import AICacheService

logger = logging.getLogger(__name__)


class UseCaseDetector:
    """Intelligent use case detection from prompt content."""

    def __init__(self):
        """Initialize use case detection patterns."""
        self.patterns = {
            # Algorithmic processing patterns
            UseCase.PRICING_OPTIMIZATION: [
                r"pric(e|ing)",
                r"cost",
                r"profit",
                r"margin",
                r"competitive",
                r"market.*analysis",
                r"revenue",
                r"optimization",
            ],
            UseCase.INVENTORY_MANAGEMENT: [
                r"inventory",
                r"stock",
                r"quantity",
                r"supply",
                r"demand",
                r"fulfillment",
                r"shipping",
                r"logistics",
            ],
            UseCase.PERFORMANCE_ANALYSIS: [
                r"performance",
                r"metrics",
                r"analytics",
                r"statistics",
                r"report",
                r"dashboard",
                r"kpi",
                r"analysis",
            ],
            UseCase.DECISION_VALIDATION: [
                r"validate",
                r"verify",
                r"check",
                r"confirm",
                r"decision",
                r"approval",
                r"review",
            ],
            # Local LLM processing patterns
            UseCase.CONTENT_TEMPLATES: [
                r"template",
                r"generate.*content",
                r"description",
                r"title",
                r"listing",
                r"product.*text",
                r"content.*creation",
            ],
            UseCase.BASIC_ANALYSIS: [
                r"analyze",
                r"summarize",
                r"explain",
                r"interpret",
                r"understand",
                r"process.*text",
            ],
            UseCase.DATA_SUMMARIZATION: [
                r"summary",
                r"summarize",
                r"overview",
                r"brief",
                r"key.*points",
                r"highlights",
            ],
            # OpenAI strategic processing patterns
            UseCase.VISION_ANALYSIS: [
                r"image",
                r"photo",
                r"picture",
                r"visual",
                r"vision",
                r"analyze.*image",
                r"product.*photo",
            ],
            UseCase.USER_COMMUNICATION: [
                r"user",
                r"customer",
                r"communication",
                r"response",
                r"chat",
                r"conversation",
                r"help",
                r"support",
            ],
            UseCase.TREND_INTELLIGENCE: [
                r"trend",
                r"market.*intelligence",
                r"forecast",
                r"prediction",
                r"insight",
                r"intelligence",
                r"strategic",
            ],
        }

    def detect_use_case(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> UseCase:
        """Detect use case from prompt content.

        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt

        Returns:
            Detected use case for routing
        """
        try:
            # Combine prompts for analysis
            combined_text = f"{prompt} {system_prompt or ''}".lower()

            # Score each use case based on pattern matches
            scores = {}
            for use_case, patterns in self.patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, combined_text))
                    score += matches
                scores[use_case] = score

            # Return highest scoring use case, default to basic analysis
            if scores:
                best_use_case = max(scores.items(), key=lambda x: x[1])
                if best_use_case[1] > 0:
                    logger.debug(
                        f"Detected use case: {best_use_case[0].value} (score: {best_use_case[1]})"
                    )
                    return best_use_case[0]

            # Default fallback
            logger.debug("No specific use case detected, using BASIC_ANALYSIS")
            return UseCase.BASIC_ANALYSIS

        except Exception as e:
            logger.warning(f"Use case detection failed: {e}")
            return UseCase.BASIC_ANALYSIS


class HybridLLMAdapter:
    """
    Compatibility adapter providing legacy LLM client interface with HybridLLMClient backend.

    This adapter enables seamless migration from legacy LLM clients to HybridLLMClient
    while maintaining backward compatibility and improving performance through
    intelligent routing.
    """

    def __init__(
        self, config: Optional[Union[SimpleLLMConfig, HybridLLMConfig]] = None
    ):
        """Initialize HybridLLMAdapter with backward compatibility.

        Args:
            config: SimpleLLMConfig or HybridLLMConfig for configuration
        """
        # Convert SimpleLLMConfig to HybridLLMConfig if needed
        if isinstance(config, SimpleLLMConfig):
            hybrid_config = HybridLLMConfig(
                openai_api_key=config.api_key,
                openai_model=(
                    config.model_type.value if config.model_type else "gemini-pro-mini"
                ),
                openai_timeout=config.timeout,
                # Docker-aware performance targets
                algorithmic_target_ms=600,  # +500ms Docker overhead
                local_llm_target_ms=2500,  # +500ms Docker overhead
                openai_target_ms=5000,  # +500ms Docker overhead
            )
        else:
            hybrid_config = config or HybridLLMConfig()

        # Initialize components
        self.hybrid_client = HybridLLMClient(hybrid_config)
        self.use_case_detector = UseCaseDetector()
        self.config = hybrid_config

        # Initialize caching (optional)
        self.cache_service = None
        self.enable_cache = True  # Enable by default for performance
        asyncio.create_task(self._initialize_cache())

        # Performance tracking
        self.request_count = 0
        self.total_processing_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info("HybridLLMAdapter initialized with intelligent routing and caching")

    async def _initialize_cache(self):
        """Initialize Redis cache service for response caching."""
        try:
            if self.enable_cache:
                self.cache_service = AICacheService(
                    redis_url="redis://flipsync-infrastructure-redis:6379",
                    db=3,  # Use different DB for hybrid client cache
                )
                await self.cache_service.connect()
                logger.info("HybridLLMAdapter cache service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize cache service: {e}")
            self.cache_service = None
            self.enable_cache = False

    async def generate_response(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """Generate response with legacy LLM client compatibility.

        This method provides the same interface as legacy LLM clients' generate_response()
        while internally using HybridLLMClient's intelligent routing.

        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt
            **kwargs: Additional parameters for compatibility

        Returns:
            LLMResponse compatible with legacy LLM clients
        """
        start_time = time.perf_counter()

        try:
            # Detect use case from prompt content
            use_case = self.use_case_detector.detect_use_case(prompt, system_prompt)

            # Prepare context for hybrid processing
            context = {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1024),
                "additional_params": kwargs,
            }

            # Process using hybrid client
            logger.debug(f"Processing with use case: {use_case.value}")
            result = await self.hybrid_client.process(use_case, context)

            # Convert ProcessingResult to LLMResponse for compatibility
            llm_response = self._convert_to_llm_response(result, prompt)

            # Track performance
            processing_time = time.perf_counter() - start_time
            self._update_performance_metrics(processing_time, result.mode_used)

            logger.info(
                f"HybridLLMAdapter: {use_case.value} -> {result.mode_used.value} "
                f"({processing_time*1000:.0f}ms, confidence: {result.confidence_score:.2f})"
            )

            return llm_response

        except Exception as e:
            logger.error(f"HybridLLMAdapter generate_response failed: {e}")
            # Fallback to strategic OpenAI for compatibility
            return await self._fallback_response(prompt, system_prompt, **kwargs)

    def _convert_to_llm_response(
        self, result: ProcessingResult, original_prompt: str
    ) -> LLMResponse:
        """Convert ProcessingResult to LLMResponse for backward compatibility."""
        # Map processing mode to provider
        provider_map = {
            ProcessingMode.ALGORITHMIC: ModelProvider.OPENAI,  # Maintain compatibility
            ProcessingMode.LOCAL_LLM: ModelProvider.OPENAI,  # Maintain compatibility
            ProcessingMode.OPENAI_STRATEGIC: ModelProvider.OPENAI,
        }

        # Estimate token usage (rough approximation)
        prompt_tokens = len(original_prompt.split()) * 1.3
        completion_tokens = len(result.content.split()) * 1.3

        return LLMResponse(
            content=result.content,
            provider=provider_map[result.mode_used],
            model=self._get_model_name(result.mode_used),
            response_time=result.processing_time_ms / 1000.0,
            token_usage={
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(prompt_tokens + completion_tokens),
            },
            cost_estimate=result.cost_estimate,
            metadata={
                "hybrid_mode": result.mode_used.value,
                "confidence_score": result.confidence_score,
                "fallback_used": result.fallback_used,
                "processing_time_ms": result.processing_time_ms,
            },
        )

    def _get_model_name(self, mode: ProcessingMode) -> str:
        """Get model name based on processing mode."""
        model_map = {
            ProcessingMode.ALGORITHMIC: "flipsync-algorithmic",
            ProcessingMode.LOCAL_LLM: f"ollama-{self.config.ollama_model}",
            ProcessingMode.OPENAI_STRATEGIC: self.config.openai_model,
        }
        return model_map.get(mode, "unknown")

    async def _fallback_response(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """Fallback to OpenAI for compatibility when hybrid processing fails."""
        try:
            # Use strategic OpenAI processor directly
            context = {"prompt": prompt, "system_prompt": system_prompt, **kwargs}

            result = (
                await self.hybrid_client.openai_processor.process_user_communication(
                    context
                )
            )
            return self._convert_to_llm_response(result, prompt)

        except Exception as e:
            logger.error(f"Fallback response failed: {e}")
            # Return error response
            return LLMResponse(
                content=f"Error: Unable to process request - {str(e)}",
                provider=ModelProvider.OPENAI,
                model="error",
                response_time=0.0,
                token_usage={
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                cost_estimate=0.0,
                metadata={"error": str(e)},
            )

    def _update_performance_metrics(self, processing_time: float, mode: ProcessingMode):
        """Update performance tracking metrics."""
        self.request_count += 1
        self.total_processing_time += processing_time

        # Log performance warnings if targets exceeded
        time_ms = processing_time * 1000
        if (
            mode == ProcessingMode.ALGORITHMIC
            and time_ms > self.config.algorithmic_target_ms
        ):
            logger.warning(
                f"Algorithmic processing exceeded target: {time_ms:.0f}ms > {self.config.algorithmic_target_ms}ms"
            )
        elif (
            mode == ProcessingMode.LOCAL_LLM
            and time_ms > self.config.local_llm_target_ms
        ):
            logger.warning(
                f"Local LLM processing exceeded target: {time_ms:.0f}ms > {self.config.local_llm_target_ms}ms"
            )
        elif (
            mode == ProcessingMode.OPENAI_STRATEGIC
            and time_ms > self.config.openai_target_ms
        ):
            logger.warning(
                f"OpenAI processing exceeded target: {time_ms:.0f}ms > {self.config.openai_target_ms}ms"
            )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        avg_time = self.total_processing_time / max(self.request_count, 1)
        return {
            "total_requests": self.request_count,
            "average_response_time_ms": avg_time * 1000,
            "total_processing_time_s": self.total_processing_time,
        }

    async def cleanup(self):
        """Cleanup resources."""
        if self.hybrid_client:
            await self.hybrid_client.cleanup()


# Factory class for backward compatibility
class HybridLLMAdapterFactory:
    """Factory for creating HybridLLMAdapter instances with legacy LLM client compatibility."""

    @staticmethod
    def create_smart_client() -> HybridLLMAdapter:
        """Create smart client with algorithmic processing priority."""
        config = HybridLLMConfig(
            enable_algorithmic=True,
            enable_local_llm=True,
            enable_openai=True,
            # Docker-aware performance targets
            algorithmic_target_ms=600,
            local_llm_target_ms=2500,
            openai_target_ms=5000,
        )
        return HybridLLMAdapter(config)

    @staticmethod
    def create_fast_client() -> HybridLLMAdapter:
        """Create fast client optimized for speed."""
        config = HybridLLMConfig(
            enable_algorithmic=True,
            enable_local_llm=False,  # Skip local LLM for speed
            enable_openai=True,
            algorithmic_target_ms=300,
            openai_target_ms=3000,
        )
        return HybridLLMAdapter(config)

    @staticmethod
    def create_business_client() -> HybridLLMAdapter:
        """Create business-optimized client."""
        config = HybridLLMConfig(
            enable_algorithmic=True,
            enable_local_llm=True,
            enable_openai=True,
            max_openai_calls_per_hour=50,  # Conservative for business
            algorithmic_target_ms=600,
            local_llm_target_ms=2500,
            openai_target_ms=5000,
        )
        return HybridLLMAdapter(config)

    @staticmethod
    def create_complex_agent_client(agent_type: str) -> HybridLLMAdapter:
        """Create complex agent client."""
        config = HybridLLMConfig(
            enable_algorithmic=True,
            enable_local_llm=True,
            enable_openai=True,
            # Agent-specific optimizations
            algorithmic_target_ms=600,
            local_llm_target_ms=2500,
            openai_target_ms=5000,
        )
        adapter = HybridLLMAdapter(config)
        logger.info(f"Created HybridLLMAdapter for {agent_type} agent")
        return adapter

    @staticmethod
    def create_liaison_client() -> HybridLLMAdapter:
        """Create liaison/concierge client for fast intent recognition."""
        config = HybridLLMConfig(
            enable_algorithmic=True,
            enable_local_llm=False,  # Skip for speed
            enable_openai=True,
            algorithmic_target_ms=300,
            openai_target_ms=2000,  # Fast response for user interaction
        )
        return HybridLLMAdapter(config)
