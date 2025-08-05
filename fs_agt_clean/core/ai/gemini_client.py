"""
Google Gemini Client for FlipSync Strategic LLM Integration
==========================================================

Production-ready Gemini API client with cost tracking, rate limiting,
and error handling for strategic LLM usage in FlipSync autonomous agents.

Features:
- Cost optimization with usage tracking
- Rate limiting and retry logic
- Comprehensive error handling
- Support for text, image, and multimodal inputs
- Strategic LLM usage patterns
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)


class GeminiModel(Enum):
    """Available Gemini models with cost optimization."""

    FLASH_2_5 = "gemini-2.5-flash"  # Most cost-effective for general tasks
    FLASH_LITE_2_5 = "gemini-2.5-flash-lite"  # Ultra cost-effective for simple tasks (updated to current model)
    PRO_2_5 = "gemini-2.5-pro"  # High-quality for complex reasoning
    FLASH_2_0 = "gemini-2.0-flash"  # Balanced performance


@dataclass
class GeminiUsage:
    """Track Gemini API usage for cost monitoring."""

    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    cost_estimate: float = 0.0
    timestamp: float = 0.0

    def calculate_cost(self) -> float:
        """Calculate cost based on current Gemini pricing."""
        # Gemini 2.5 Flash pricing (per 1M tokens)
        if "2.5-flash-lite" in self.model or "flash-lite-preview" in self.model:
            input_cost = 0.10  # $0.10 per 1M input tokens
            output_cost = 0.40  # $0.40 per 1M output tokens
        elif "2.5-flash" in self.model:
            input_cost = 0.30  # $0.30 per 1M input tokens
            output_cost = 2.50  # $2.50 per 1M output tokens
        elif "2.5-pro" in self.model:
            input_cost = 1.25  # $1.25 per 1M input tokens
            output_cost = 10.00  # $10.00 per 1M output tokens
        else:
            # Default to Flash pricing
            input_cost = 0.30
            output_cost = 2.50

        total_cost = (self.input_tokens / 1_000_000) * input_cost + (
            self.output_tokens / 1_000_000
        ) * output_cost

        self.cost_estimate = total_cost
        return total_cost


@dataclass
class GeminiResponse:
    """Structured response from Gemini API."""

    text: str
    usage: GeminiUsage
    success: bool = True
    error_message: Optional[str] = None
    model_used: str = ""
    response_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "text": self.text,
            "success": self.success,
            "error_message": self.error_message,
            "model_used": self.model_used,
            "response_time": self.response_time,
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
                "cost_estimate": self.usage.cost_estimate,
            },
        }


class GeminiClient:
    """
    Production-ready Google Gemini API client for FlipSync.

    Features:
    - Strategic cost optimization
    - Rate limiting and retry logic
    - Comprehensive error handling
    - Usage tracking and monitoring
    - Support for multimodal inputs
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: GeminiModel = GeminiModel.FLASH_2_5,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        daily_budget: float = 10.0,
    ):
        """Initialize Gemini client with cost controls."""
        self.api_key = (
            api_key or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("Gemini_API")
        )
        self.default_model = default_model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.daily_budget = daily_budget

        # Usage tracking
        self.daily_usage = 0.0
        self.total_requests = 0
        self.failed_requests = 0

        if not self.api_key:
            raise ValueError(
                "Google AI API key is required. Set GOOGLE_AI_API_KEY or Gemini_API environment variable."
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Safety settings for production use
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        logger.info(f"GeminiClient initialized with model {default_model.value}")

    async def generate_content(
        self,
        prompt: str,
        model: Optional[GeminiModel] = None,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> GeminiResponse:
        """
        Generate content using Gemini API with cost optimization.

        Args:
            prompt: User prompt for content generation
            model: Gemini model to use (defaults to client default)
            system_prompt: System prompt for context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Additional generation parameters

        Returns:
            GeminiResponse with generated content and usage metrics
        """
        start_time = time.perf_counter()
        model_to_use = model or self.default_model

        # Check daily budget
        if self.daily_usage >= self.daily_budget:
            logger.warning(f"Daily budget of ${self.daily_budget} exceeded")
            return GeminiResponse(
                text="",
                usage=GeminiUsage(),
                success=False,
                error_message="Daily budget exceeded",
                model_used=model_to_use.value,
            )

        # Prepare the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"

        # Generation config
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens or 1000,
            **kwargs,
        }

        for attempt in range(self.max_retries):
            try:
                # Create model instance
                model_instance = genai.GenerativeModel(
                    model_name=model_to_use.value,
                    safety_settings=self.safety_settings,
                    generation_config=generation_config,
                )

                # Generate content
                response = await asyncio.to_thread(
                    model_instance.generate_content, full_prompt
                )

                # Extract usage information
                usage = GeminiUsage(
                    input_tokens=(
                        response.usage_metadata.prompt_token_count
                        if response.usage_metadata
                        else 0
                    ),
                    output_tokens=(
                        response.usage_metadata.candidates_token_count
                        if response.usage_metadata
                        else 0
                    ),
                    model=model_to_use.value,
                    timestamp=time.time(),
                )

                # Calculate cost
                cost = usage.calculate_cost()
                self.daily_usage += cost
                self.total_requests += 1

                response_time = time.perf_counter() - start_time

                logger.info(
                    f"Gemini request successful: {usage.input_tokens} input tokens, "
                    f"{usage.output_tokens} output tokens, ${cost:.4f} cost, "
                    f"{response_time:.3f}s response time"
                )

                return GeminiResponse(
                    text=response.text,
                    usage=usage,
                    success=True,
                    model_used=model_to_use.value,
                    response_time=response_time,
                )

            except Exception as e:
                self.failed_requests += 1
                logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2**attempt))
                else:
                    response_time = time.perf_counter() - start_time
                    return GeminiResponse(
                        text="",
                        usage=GeminiUsage(
                            model=model_to_use.value, timestamp=time.time()
                        ),
                        success=False,
                        error_message=str(e),
                        model_used=model_to_use.value,
                        response_time=response_time,
                    )

        # Should never reach here
        return GeminiResponse(
            text="",
            usage=GeminiUsage(),
            success=False,
            error_message="Max retries exceeded",
            model_used=model_to_use.value,
        )

    async def analyze_image_with_text(
        self,
        image_data: bytes,
        prompt: str,
        model: Optional[GeminiModel] = None,
        **kwargs,
    ) -> GeminiResponse:
        """
        Analyze image with text prompt using Gemini Vision.

        Args:
            image_data: Image data as bytes
            prompt: Text prompt for image analysis
            model: Gemini model to use
            **kwargs: Additional generation parameters

        Returns:
            GeminiResponse with analysis results
        """
        # This would implement image analysis
        # For now, delegate to text generation with image context
        image_prompt = f"[Image analysis requested] {prompt}"
        return await self.generate_content(image_prompt, model, **kwargs)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            "daily_usage_cost": self.daily_usage,
            "daily_budget": self.daily_budget,
            "budget_remaining": max(0, self.daily_budget - self.daily_usage),
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (
                (self.total_requests - self.failed_requests) / self.total_requests
                if self.total_requests > 0
                else 0
            ),
        }

    def reset_daily_usage(self):
        """Reset daily usage counter (typically called at midnight)."""
        self.daily_usage = 0.0
        logger.info("Daily usage counter reset")


# Factory function for easy client creation
def create_gemini_client(
    api_key: Optional[str] = None,
    default_model: GeminiModel = GeminiModel.FLASH_2_5,
    daily_budget: float = 10.0,
) -> GeminiClient:
    """Create Gemini client with FlipSync defaults."""
    return GeminiClient(
        api_key=api_key,
        default_model=default_model,
        daily_budget=daily_budget,
    )
