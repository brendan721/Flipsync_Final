"""
OpenAI Client Implementation for FlipSync
=========================================

Production-ready OpenAI integration with cost optimization, rate limiting,
and comprehensive error handling based on OpenAI Cookbook best practices.

Features:
- Intelligent model selection (GPT-4o-mini for simple tasks, GPT-4o for complex)
- Vision API integration with structured outputs
- Exponential backoff and rate limiting
- Cost monitoring and usage tracking
- Production-grade error handling
"""

import asyncio
import base64
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp
from openai import AsyncOpenAI, RateLimitError
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_random_exponential

logger = logging.getLogger(__name__)

# Import Phase 4 optimization
try:
    from ..optimization.phase4_optimizer import (
        get_phase4_optimizer,
        Phase4OptimizationLevel,
    )

    PHASE4_AVAILABLE = True
except ImportError:
    PHASE4_AVAILABLE = False
    logger.warning("Phase 4 optimization not available")


class OpenAIModel(str, Enum):
    """Available OpenAI models with cost optimization."""

    # Cost-efficient models for simple tasks
    GPT_4O_MINI = "gpt-4o-mini"  # $0.15/1M input, $0.60/1M output

    # Advanced models for complex tasks
    GPT_4O = "gpt-4o"  # $2.50/1M input, $10.00/1M output
    GPT_4O_LATEST = "gpt-4o-2024-11-20"  # Latest with vision + function calling

    # Reasoning models for complex analysis
    O1_MINI = "o1-mini"  # $3.00/1M input, $12.00/1M output
    O1_PREVIEW = "o1-preview"  # $15.00/1M input, $60.00/1M output


class TaskComplexity(str, Enum):
    """Task complexity levels for intelligent model selection."""

    SIMPLE = "simple"  # Basic text generation, simple analysis
    MODERATE = "moderate"  # Content generation, basic vision
    COMPLEX = "complex"  # Advanced vision, function calling
    REASONING = "reasoning"  # Complex reasoning, multi-step analysis


@dataclass
class OpenAIConfig:
    """OpenAI client configuration with cost optimization."""

    api_key: str
    project_id: Optional[str] = None
    model: OpenAIModel = OpenAIModel.GPT_4O_MINI
    temperature: float = 0.7
    max_tokens: Optional[int] = 1000
    timeout: float = 30.0
    max_retries: int = 3

    # Cost control
    max_cost_per_request: float = 0.10  # $0.10 max per request
    daily_budget: float = 10.00  # $10 daily budget

    # Rate limiting
    requests_per_minute: int = 50
    tokens_per_minute: int = 40000


@dataclass
class OpenAIResponse:
    """Standardized OpenAI response container."""

    content: str
    model: str
    usage: Dict[str, Any]
    cost_estimate: float
    response_time: float
    metadata: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None


class OpenAIUsageTracker:
    """Track OpenAI usage and costs for budget management."""

    def __init__(self):
        self.daily_usage = {}
        self.total_requests = 0
        self.total_cost = 0.0
        self.last_reset = datetime.now().date()

    def reset_daily_usage(self):
        """Reset daily usage counters."""
        today = datetime.now().date()
        if today != self.last_reset:
            self.daily_usage = {}
            self.last_reset = today

    def record_usage(
        self, model: str, input_tokens: int, output_tokens: int, cost: float
    ):
        """Record API usage for tracking."""
        self.reset_daily_usage()

        if model not in self.daily_usage:
            self.daily_usage[model] = {
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
            }

        self.daily_usage[model]["requests"] += 1
        self.daily_usage[model]["input_tokens"] += input_tokens
        self.daily_usage[model]["output_tokens"] += output_tokens
        self.daily_usage[model]["cost"] += cost

        self.total_requests += 1
        self.total_cost += cost

    def get_daily_cost(self) -> float:
        """Get total daily cost."""
        self.reset_daily_usage()
        return sum(usage["cost"] for usage in self.daily_usage.values())

    def check_budget(self, config: OpenAIConfig) -> bool:
        """Check if within daily budget."""
        return self.get_daily_cost() < config.daily_budget


class FlipSyncOpenAIClient:
    """
    Production-ready OpenAI client for FlipSync with intelligent model selection,
    cost optimization, and comprehensive error handling.
    """

    def __init__(self, config: OpenAIConfig):
        self.config = config
        # Initialize OpenAI client with project ID and proper SSL configuration
        import ssl
        import httpx

        # Create proper SSL context for Docker environments
        ssl_context = ssl.create_default_context()

        # Create HTTP client with proper SSL configuration
        http_client = httpx.AsyncClient(verify=ssl_context, timeout=config.timeout)

        client_kwargs = {"api_key": config.api_key, "http_client": http_client}
        if config.project_id:
            client_kwargs["project"] = config.project_id
        self.client = AsyncOpenAI(**client_kwargs)
        self.usage_tracker = OpenAIUsageTracker()

        # Model pricing (per 1M tokens)
        self.pricing = {
            OpenAIModel.GPT_4O_MINI: {"input": 0.15, "output": 0.60},
            OpenAIModel.GPT_4O: {"input": 2.50, "output": 10.00},
            OpenAIModel.GPT_4O_LATEST: {"input": 2.50, "output": 10.00},
            OpenAIModel.O1_MINI: {"input": 3.00, "output": 12.00},
            OpenAIModel.O1_PREVIEW: {"input": 15.00, "output": 60.00},
        }

        # Initialize Phase 4 optimization if available
        self.phase4_optimizer = None
        self.phase4_enabled = False
        if PHASE4_AVAILABLE:
            try:
                self.phase4_optimizer = get_phase4_optimizer()
                self.phase4_enabled = True
                logger.info("Phase 4 optimization enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Phase 4 optimization: {e}")

        logger.info(f"Initialized FlipSyncOpenAIClient with model: {config.model}")

    async def start_optimization(self):
        """Start Phase 4 optimization components."""
        if self.phase4_enabled and self.phase4_optimizer:
            try:
                await self.phase4_optimizer.start()
                logger.info("Phase 4 optimization started")
            except Exception as e:
                logger.error(f"Failed to start Phase 4 optimization: {e}")

    async def stop_optimization(self):
        """Stop Phase 4 optimization components."""
        if self.phase4_enabled and self.phase4_optimizer:
            try:
                await self.phase4_optimizer.stop()
                logger.info("Phase 4 optimization stopped")
            except Exception as e:
                logger.error(f"Failed to stop Phase 4 optimization: {e}")

    def select_optimal_model(
        self, task_complexity: TaskComplexity, has_vision: bool = False
    ) -> OpenAIModel:
        """
        Intelligently select the most cost-effective model for the task.

        Based on OpenAI Cookbook recommendations for cost optimization.
        """
        if task_complexity == TaskComplexity.SIMPLE:
            return OpenAIModel.GPT_4O_MINI

        elif task_complexity == TaskComplexity.MODERATE:
            if has_vision:
                return OpenAIModel.GPT_4O_LATEST  # Vision requires GPT-4o
            return OpenAIModel.GPT_4O_MINI

        elif task_complexity == TaskComplexity.COMPLEX:
            return OpenAIModel.GPT_4O_LATEST

        elif task_complexity == TaskComplexity.REASONING:
            return OpenAIModel.O1_MINI  # Cost-effective reasoning model

        return OpenAIModel.GPT_4O_MINI  # Default fallback

    def estimate_cost(
        self, model: OpenAIModel, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate cost for a request."""
        pricing = self.pricing.get(model, self.pricing[OpenAIModel.GPT_4O_MINI])

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def check_request_viability(self, estimated_cost: float) -> bool:
        """Check if request is within budget constraints."""
        # Check per-request limit
        if estimated_cost > self.config.max_cost_per_request:
            logger.warning(
                f"Request cost ${estimated_cost:.4f} exceeds limit ${self.config.max_cost_per_request}"
            )
            return False

        # Check daily budget
        if not self.usage_tracker.check_budget(self.config):
            logger.warning("Daily budget exceeded")
            return False

        return True

    @retry(
        wait=wait_random_exponential(multiplier=1, max=40),
        stop=stop_after_attempt(3),
        retry_error_callback=lambda retry_state: logger.error(
            f"OpenAI request failed after {retry_state.attempt_number} attempts"
        ),
    )
    async def _make_request(
        self, messages: List[Dict[str, Any]], model: OpenAIModel, **kwargs
    ) -> OpenAIResponse:
        """
        Make OpenAI API request with exponential backoff and error handling.

        Based on OpenAI Cookbook rate limiting patterns.
        """
        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=model.value,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
                **kwargs,
            )

            response_time = time.time() - start_time

            # Extract usage information
            usage = response.usage.model_dump() if response.usage else {}
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            # Calculate cost
            cost = self.estimate_cost(model, input_tokens, output_tokens)

            # Record usage
            self.usage_tracker.record_usage(
                model.value, input_tokens, output_tokens, cost
            )

            content = response.choices[0].message.content or ""

            logger.info(
                f"OpenAI request successful: {model.value}, "
                f"tokens: {input_tokens}+{output_tokens}, "
                f"cost: ${cost:.4f}, time: {response_time:.2f}s"
            )

            return OpenAIResponse(
                content=content,
                model=model.value,
                usage=usage,
                cost_estimate=cost,
                response_time=response_time,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "system_fingerprint": getattr(response, "system_fingerprint", None),
                },
            )

        except RateLimitError as e:
            logger.warning(f"Rate limit hit for {model.value}: {e}")
            raise

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                f"OpenAI request failed: {model.value}, error: {e}, time: {response_time:.2f}s"
            )

            return OpenAIResponse(
                content="",
                model=model.value,
                usage={},
                cost_estimate=0.0,
                response_time=response_time,
                metadata={},
                success=False,
                error_message=str(e),
            )

    async def generate_text(
        self,
        prompt: str,
        task_complexity: TaskComplexity = TaskComplexity.SIMPLE,
        system_prompt: Optional[str] = None,
    ) -> OpenAIResponse:
        """
        Generate text using optimal model selection.

        Args:
            prompt: UnifiedUser prompt
            task_complexity: Complexity level for model selection
            system_prompt: Optional system prompt
        """
        # Select optimal model
        model = self.select_optimal_model(task_complexity)

        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Estimate cost and check viability
        estimated_tokens = len(prompt.split()) * 1.3  # Rough estimation
        estimated_cost = self.estimate_cost(
            model, int(estimated_tokens), self.config.max_tokens or 1000
        )

        if not self.check_request_viability(estimated_cost):
            return OpenAIResponse(
                content="",
                model=model.value,
                usage={},
                cost_estimate=estimated_cost,
                response_time=0.0,
                metadata={},
                success=False,
                error_message="Request exceeds budget constraints",
            )

        return await self._make_request(messages, model)

    async def generate_text_optimized(
        self,
        prompt: str,
        operation_type: str = "text_generation",
        task_complexity: TaskComplexity = TaskComplexity.SIMPLE,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        optimization_level: Optional[str] = "advanced",
    ) -> OpenAIResponse:
        """
        Generate text with Phase 4 optimization integration.

        Args:
            prompt: UnifiedUser prompt
            operation_type: Type of operation for optimization
            task_complexity: Complexity level for model selection
            system_prompt: Optional system prompt
            context: Additional context for optimization
            optimization_level: Phase 4 optimization level
        """
        if context is None:
            context = {}

        # Use Phase 4 optimization if available
        if self.phase4_enabled and self.phase4_optimizer:
            try:
                # Convert optimization level string to enum
                opt_level = Phase4OptimizationLevel.ADVANCED
                if optimization_level == "basic":
                    opt_level = Phase4OptimizationLevel.BASIC
                elif optimization_level == "standard":
                    opt_level = Phase4OptimizationLevel.STANDARD
                elif optimization_level == "maximum":
                    opt_level = Phase4OptimizationLevel.MAXIMUM

                # Apply Phase 4 optimization
                phase4_result = await self.phase4_optimizer.optimize_request(
                    operation_type=operation_type,
                    content=prompt,
                    context=context,
                    quality_requirement=0.8,
                    optimization_level=opt_level,
                )

                # Create optimized response
                return OpenAIResponse(
                    content=str(phase4_result.response),
                    model="phase4_optimized",
                    usage={
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                    cost_estimate=phase4_result.phase4_cost,
                    response_time=phase4_result.response_time,
                    metadata={
                        "optimization_methods": phase4_result.optimization_methods,
                        "cost_reduction_phase4": phase4_result.cost_reduction_phase4,
                        "total_cost_reduction": phase4_result.total_cost_reduction,
                        "quality_score": phase4_result.quality_score,
                        "predictive_cache_hit": phase4_result.predictive_cache_hit,
                        "dynamic_routing_applied": phase4_result.dynamic_routing_applied,
                        "response_streaming_applied": phase4_result.response_streaming_applied,
                        "performance_metrics": phase4_result.performance_metrics,
                    },
                )

            except Exception as e:
                logger.warning(
                    f"Phase 4 optimization failed, falling back to standard: {e}"
                )

        # Fallback to standard generation
        return await self.generate_text(prompt, task_complexity, system_prompt)

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        task_complexity: TaskComplexity = TaskComplexity.MODERATE,
    ) -> OpenAIResponse:
        """
        Analyze image using GPT-4o Vision API.

        Args:
            image_data: Image bytes (JPEG/PNG)
            prompt: Analysis prompt
            task_complexity: Complexity level for model selection
        """
        # Vision requires GPT-4o models
        model = self.select_optimal_model(task_complexity, has_vision=True)

        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        # Prepare vision message
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "high",  # High detail for better analysis
                        },
                    },
                ],
            }
        ]

        # Estimate cost (vision is more expensive)
        estimated_cost = self.estimate_cost(model, 1000, 500)  # Conservative estimate

        if not self.check_request_viability(estimated_cost):
            return OpenAIResponse(
                content="",
                model=model.value,
                usage={},
                cost_estimate=estimated_cost,
                response_time=0.0,
                metadata={},
                success=False,
                error_message="Vision request exceeds budget constraints",
            )

        return await self._make_request(messages, model)

    async def analyze_image_structured(
        self, image_data: bytes, response_format: BaseModel
    ) -> OpenAIResponse:
        """
        Analyze image with structured output using OpenAI's structured outputs feature.

        Based on OpenAI Cookbook structured outputs patterns.
        """
        model = OpenAIModel.GPT_4O_LATEST  # Structured outputs require latest model

        # Encode image
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        # Create analysis prompt
        prompt = f"""
        Analyze this product image and extract structured information.
        Focus on:
        1. Product identification and category
        2. Key features and selling points
        3. Condition assessment
        4. Market positioning insights
        5. SEO-optimized content suggestions

        Provide detailed, accurate information suitable for e-commerce listing creation.
        """

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "high",
                        },
                    },
                ],
            }
        ]

        # Use structured outputs
        return await self._make_request(
            messages, model, response_format=response_format.model_json_schema()
        )

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""
        self.usage_tracker.reset_daily_usage()

        return {
            "daily_usage": self.usage_tracker.daily_usage,
            "daily_cost": self.usage_tracker.get_daily_cost(),
            "total_requests": self.usage_tracker.total_requests,
            "total_cost": self.usage_tracker.total_cost,
            "budget_remaining": self.config.daily_budget
            - self.usage_tracker.get_daily_cost(),
            "budget_utilization": (
                self.usage_tracker.get_daily_cost() / self.config.daily_budget
            )
            * 100,
        }


# Structured output models for product analysis
class ProductDetails(BaseModel):
    """Structured product details from image analysis."""

    title: str = Field(description="SEO-optimized product title")
    category: str = Field(description="Primary product category")
    subcategory: Optional[str] = Field(description="Product subcategory")
    brand: Optional[str] = Field(description="Product brand if identifiable")
    model: Optional[str] = Field(description="Product model if identifiable")
    condition: str = Field(description="Product condition assessment")
    key_features: List[str] = Field(
        description="Key product features and selling points"
    )
    estimated_price_range: Dict[str, float] = Field(
        description="Price range with min/max values"
    )
    target_audience: str = Field(description="Primary target audience")
    marketplace_categories: Dict[str, str] = Field(
        description="Category mappings for different marketplaces"
    )


class MarketplaceOptimization(BaseModel):
    """Marketplace-specific optimization suggestions."""

    ebay_title: str = Field(description="eBay-optimized title (80 chars max)")
    ebay_category: str = Field(description="Suggested eBay category")
    amazon_title: str = Field(description="Amazon-optimized title")
    amazon_bullet_points: List[str] = Field(description="Amazon bullet points")
    seo_keywords: List[str] = Field(description="SEO keywords for search optimization")
    description: str = Field(description="Detailed product description")


class ProductAnalysisResult(BaseModel):
    """Complete structured product analysis result."""

    product_details: ProductDetails
    marketplace_optimization: MarketplaceOptimization
    confidence_score: float = Field(description="Analysis confidence (0-1)")
    analysis_notes: List[str] = Field(description="Additional analysis notes")
    recommended_actions: List[str] = Field(description="Recommended next steps")


# Factory function for easy client creation
def create_openai_client(
    api_key: Optional[str] = None,
    model: OpenAIModel = OpenAIModel.GPT_4O_MINI,
    daily_budget: float = 10.0,
) -> FlipSyncOpenAIClient:
    """
    Create OpenAI client with FlipSync defaults.

    Args:
        api_key: OpenAI API key (defaults to env var)
        model: Default model to use
        daily_budget: Daily spending limit in USD
    """
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not provided and OPENAI_API_KEY env var not set"
            )

    # Get project ID from environment if available
    project_id = os.getenv("OPENAI_PROJECT_ID")

    config = OpenAIConfig(
        api_key=api_key,
        project_id=project_id,
        model=model,
        daily_budget=daily_budget,
        max_cost_per_request=0.10,  # $0.10 max per request
        timeout=30.0,
    )

    return FlipSyncOpenAIClient(config)
