"""
Hybrid LLM Client - Strategic OpenAI Reduction Implementation
============================================================

Intelligent routing between:
- Algorithmic/Rule-based processing (primary)
- Local Ollama models (secondary)
- OpenAI (strategic use cases only)

Designed for scaling to thousands of users with cost optimization.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

import aiohttp

# import pandas as pd

# Import Gemini client for strategic LLM usage
from fs_agt_clean.core.ai.gemini_client import GeminiClient, GeminiModel


# Optional ML dependencies removed for production deployment
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class ProcessingMode(str, Enum):
    """Processing modes for different use cases."""

    ALGORITHMIC = "algorithmic"  # Pure rule-based/mathematical
    LOCAL_LLM = "local_llm"  # Ollama for general knowledge
    OPENAI_STRATEGIC = "openai_strategic"  # OpenAI for strategic use cases only


class UseCase(str, Enum):
    """Specific use cases that determine processing mode."""

    # Algorithmic processing (no LLM needed)
    PRICING_OPTIMIZATION = "pricing_optimization"
    INVENTORY_MANAGEMENT = "inventory_management"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    DECISION_VALIDATION = "decision_validation"

    # Local LLM processing (Ollama)
    CONTENT_TEMPLATES = "content_templates"
    BASIC_ANALYSIS = "basic_analysis"
    DATA_SUMMARIZATION = "data_summarization"

    # OpenAI strategic processing (high-value only)
    VISION_ANALYSIS = "vision_analysis"
    USER_COMMUNICATION = "user_communication"
    TREND_INTELLIGENCE = "trend_intelligence"


@dataclass
class HybridLLMConfig:
    """Configuration for hybrid LLM processing."""

    # Algorithmic processing
    enable_algorithmic: bool = True

    # Local LLM (Ollama)
    enable_local_llm: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma2:2b"  # Lightweight for general tasks
    ollama_timeout: float = 10.0

    # OpenAI strategic (disabled by default for cost optimization)
    enable_openai: bool = False
    openai_api_key: Optional[str] = None
    openai_model: str = "gemini-pro-mini"
    openai_timeout: float = 30.0

    # Gemini strategic (15% usage target for cost optimization)
    enable_gemini: bool = True
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"  # Cost-effective model
    gemini_timeout: float = 30.0
    gemini_usage_percentage: float = 0.15  # 15% target usage

    # Cost controls
    max_openai_calls_per_hour: int = 100  # Strict limits
    max_openai_tokens_per_day: int = 50000

    # Performance targets
    algorithmic_target_ms: int = 100
    local_llm_target_ms: int = 2000
    openai_target_ms: int = 5000


@dataclass
class ProcessingResult:
    """Result from hybrid processing."""

    content: str
    mode_used: ProcessingMode
    processing_time_ms: int
    confidence_score: float
    cost_estimate: float = 0.0
    fallback_used: bool = False


class AlgorithmicProcessor:
    """Pure algorithmic processing for core operations."""

    def __init__(self):
        self.pricing_rules = self._load_pricing_rules()
        self.inventory_thresholds = self._load_inventory_thresholds()
        self.performance_metrics = {}

    def _load_pricing_rules(self) -> Dict[str, Any]:
        """Load pricing optimization rules."""
        return {
            "competitive_margin": 0.05,  # 5% above lowest competitor
            "demand_multiplier": {"high": 1.15, "medium": 1.05, "low": 0.95},
            "inventory_factor": {
                "overstocked": 0.90,
                "normal": 1.00,
                "understocked": 1.10,
            },
        }

    def _load_inventory_thresholds(self) -> Dict[str, int]:
        """Load inventory management thresholds."""
        return {"reorder_point": 10, "max_stock": 100, "safety_stock": 5}

    async def process_pricing_optimization(
        self, context: Dict[str, Any]
    ) -> ProcessingResult:
        """Algorithmic pricing optimization."""
        start_time = time.perf_counter()

        try:
            # Extract data
            current_price = context.get("current_price", 0)
            competitor_prices = context.get("competitor_prices", [])
            demand_level = context.get("demand_level", "medium")
            inventory_status = context.get("inventory_status", "normal")

            # Algorithmic calculation
            if competitor_prices:
                min_competitor = min(competitor_prices)
                base_price = min_competitor * (
                    1 + self.pricing_rules["competitive_margin"]
                )
            else:
                base_price = current_price

            # Apply demand multiplier
            demand_multiplier = self.pricing_rules["demand_multiplier"][demand_level]
            inventory_factor = self.pricing_rules["inventory_factor"][inventory_status]

            optimized_price = base_price * demand_multiplier * inventory_factor

            # Generate result
            result_content = json.dumps(
                {
                    "optimized_price": round(optimized_price, 2),
                    "price_change": round(optimized_price - current_price, 2),
                    "reasoning": f"Applied {demand_level} demand and {inventory_status} inventory factors",
                    "confidence": 0.95,
                }
            )

            processing_time = int((time.perf_counter() - start_time) * 1000)

            return ProcessingResult(
                content=result_content,
                mode_used=ProcessingMode.ALGORITHMIC,
                processing_time_ms=processing_time,
                confidence_score=0.95,
                cost_estimate=0.0,
            )

        except Exception as e:
            logger.error(f"Algorithmic pricing optimization failed: {e}")
            raise

    async def process_inventory_management(
        self, context: Dict[str, Any]
    ) -> ProcessingResult:
        """Algorithmic inventory management."""
        start_time = time.perf_counter()

        try:
            current_stock = context.get("current_stock", 0)
            daily_sales = context.get("daily_sales", 0)
            lead_time_days = context.get("lead_time_days", 7)

            # Calculate reorder point
            reorder_point = (daily_sales * lead_time_days) + self.inventory_thresholds[
                "safety_stock"
            ]

            # Determine action
            if current_stock <= reorder_point:
                action = "reorder"
                quantity = self.inventory_thresholds["max_stock"] - current_stock
            elif current_stock > self.inventory_thresholds["max_stock"]:
                action = "reduce_pricing"
                quantity = 0
            else:
                action = "maintain"
                quantity = 0

            result_content = json.dumps(
                {
                    "action": action,
                    "reorder_quantity": quantity,
                    "reorder_point": reorder_point,
                    "current_stock": current_stock,
                    "confidence": 0.90,
                }
            )

            processing_time = int((time.perf_counter() - start_time) * 1000)

            return ProcessingResult(
                content=result_content,
                mode_used=ProcessingMode.ALGORITHMIC,
                processing_time_ms=processing_time,
                confidence_score=0.90,
                cost_estimate=0.0,
            )

        except Exception as e:
            logger.error(f"Algorithmic inventory management failed: {e}")
            raise


class LocalLLMProcessor:
    """Local LLM processing using Ollama for general knowledge tasks."""

    def __init__(self, config: HybridLLMConfig):
        self.config = config
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.ollama_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def process_content_templates(
        self, context: Dict[str, Any]
    ) -> ProcessingResult:
        """Generate content using local LLM with templates."""
        start_time = time.perf_counter()

        try:
            session = await self._get_session()

            # Prepare prompt for Ollama
            product_name = context.get("product_name", "Product")
            category = context.get("category", "General")
            features = context.get("features", [])

            prompt = f"""Generate a product description for:
Product: {product_name}
Category: {category}
Features: {', '.join(features)}

Keep it concise, professional, and SEO-friendly. Focus on benefits."""

            # Call Ollama API
            async with session.post(
                f"{self.config.ollama_base_url}/api/generate",
                json={
                    "model": self.config.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result.get("response", "")

                    processing_time = int((time.perf_counter() - start_time) * 1000)

                    return ProcessingResult(
                        content=content,
                        mode_used=ProcessingMode.LOCAL_LLM,
                        processing_time_ms=processing_time,
                        confidence_score=0.75,
                        cost_estimate=0.0,  # Local processing
                    )
                else:
                    raise Exception(f"Ollama API error: {response.status}")

        except Exception as e:
            logger.error(f"Local LLM processing failed: {e}")
            # Fallback to template-based generation
            return await self._template_fallback(context, start_time)

    async def _template_fallback(
        self, context: Dict[str, Any], start_time: float
    ) -> ProcessingResult:
        """Template-based fallback when Ollama is unavailable."""
        product_name = context.get("product_name", "Product")
        category = context.get("category", "General")
        features = context.get("features", [])

        # Simple template-based generation
        template = f"High-quality {product_name} in {category} category. "
        if features:
            template += f"Features include: {', '.join(features)}. "
        template += "Perfect for your needs with reliable performance and great value."

        processing_time = int((time.perf_counter() - start_time) * 1000)

        return ProcessingResult(
            content=template,
            mode_used=ProcessingMode.ALGORITHMIC,  # Fallback to algorithmic
            processing_time_ms=processing_time,
            confidence_score=0.60,
            cost_estimate=0.0,
            fallback_used=True,
        )


class StrategicOpenAIProcessor:
    """Strategic OpenAI processing for high-value use cases only."""

    def __init__(self, config: HybridLLMConfig):
        self.config = config
        self.session = None
        self.usage_tracker = {
            "hourly_calls": 0,
            "daily_tokens": 0,
            "last_reset": datetime.now(timezone.utc),
        }

    def _check_usage_limits(self) -> bool:
        """Check if within usage limits."""
        now = datetime.now(timezone.utc)

        # Reset hourly counter
        if (now - self.usage_tracker["last_reset"]).seconds >= 3600:
            self.usage_tracker["hourly_calls"] = 0
            self.usage_tracker["last_reset"] = now

        # Check limits
        if self.usage_tracker["hourly_calls"] >= self.config.max_openai_calls_per_hour:
            return False
        if self.usage_tracker["daily_tokens"] >= self.config.max_openai_tokens_per_day:
            return False

        return True

    async def process_vision_analysis(
        self, context: Dict[str, Any]
    ) -> ProcessingResult:
        """Process vision analysis using OpenAI GPT-4o Vision."""
        if not self._check_usage_limits():
            raise Exception("OpenAI usage limits exceeded")

        start_time = time.perf_counter()

        # Implementation would go here for vision analysis
        # This is a strategic use case where OpenAI provides significant value

        processing_time = int((time.perf_counter() - start_time) * 1000)

        return ProcessingResult(
            content="Vision analysis result",
            mode_used=ProcessingMode.OPENAI_STRATEGIC,
            processing_time_ms=processing_time,
            confidence_score=0.90,
            cost_estimate=0.01,  # Estimated cost
        )


class StrategicGeminiProcessor:
    """Strategic Gemini processing for cost-optimized LLM usage."""

    def __init__(self, config: HybridLLMConfig):
        self.config = config
        self.gemini_client = None
        self.usage_tracker = {
            "hourly_calls": 0,
            "daily_tokens": 0,
            "last_reset": time.time(),
        }

    async def _get_gemini_client(self) -> GeminiClient:
        """Get or create Gemini client."""
        if self.gemini_client is None:
            api_key = self.config.gemini_api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Gemini API key not configured")

            # Map config model to GeminiModel enum
            model_mapping = {
                "gemini-2.5-flash": GeminiModel.FLASH_2_5,
                "gemini-2.5-flash-lite": GeminiModel.FLASH_LITE_2_5,
                "gemini-2.5-pro": GeminiModel.PRO_2_5,
                "gemini-2.0-flash": GeminiModel.FLASH_2_0,
            }

            default_model = model_mapping.get(
                self.config.gemini_model, GeminiModel.FLASH_2_5
            )

            self.gemini_client = GeminiClient(
                api_key=api_key,
                default_model=default_model,
                daily_budget=10.0,  # $10 daily budget for cost control
            )
        return self.gemini_client

    async def process(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> ProcessingResult:
        """Process using Gemini with cost tracking."""
        start_time = time.perf_counter()

        try:
            client = await self._get_gemini_client()

            # Generate content using Gemini
            response = await client.generate_content(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1000,
            )

            # Track usage
            self.usage_tracker["hourly_calls"] += 1
            self.usage_tracker["daily_tokens"] += (
                response.usage.input_tokens + response.usage.output_tokens
            )

            processing_time = int((time.perf_counter() - start_time) * 1000)

            return ProcessingResult(
                content=response.content,
                mode_used=ProcessingMode.OPENAI_STRATEGIC,  # Using OPENAI_STRATEGIC for Gemini
                processing_time_ms=processing_time,
                confidence_score=0.85,
                cost_estimate=response.usage.cost,
            )

        except Exception as e:
            logger.error(f"Gemini processing failed: {e}")
            processing_time = int((time.perf_counter() - start_time) * 1000)

            return ProcessingResult(
                content=f"Gemini processing failed: {str(e)}",
                mode_used=ProcessingMode.OPENAI_STRATEGIC,  # Using OPENAI_STRATEGIC for Gemini
                processing_time_ms=processing_time,
                confidence_score=0.0,
                cost_estimate=0.0,
            )


class HybridLLMClient:
    """Hybrid LLM client with intelligent routing."""

    def __init__(self, config: Optional[HybridLLMConfig] = None):
        self.config = config or HybridLLMConfig()
        self.algorithmic_processor = AlgorithmicProcessor()
        self.local_llm_processor = LocalLLMProcessor(self.config)
        self.openai_processor = StrategicOpenAIProcessor(self.config)
        self.gemini_processor = StrategicGeminiProcessor(self.config)

        # Use case routing
        self.routing_map = {
            UseCase.PRICING_OPTIMIZATION: self.algorithmic_processor.process_pricing_optimization,
            UseCase.INVENTORY_MANAGEMENT: self.algorithmic_processor.process_inventory_management,
            UseCase.CONTENT_TEMPLATES: self.local_llm_processor.process_content_templates,
            UseCase.VISION_ANALYSIS: self.openai_processor.process_vision_analysis,
        }

    async def process(
        self, use_case: UseCase, context: Dict[str, Any]
    ) -> ProcessingResult:
        """Process request using appropriate method based on use case."""
        try:
            processor = self.routing_map.get(use_case)
            if not processor:
                raise ValueError(f"Unsupported use case: {use_case}")

            result = await processor(context)

            logger.info(
                f"Processed {use_case.value} using {result.mode_used.value} "
                f"in {result.processing_time_ms}ms (confidence: {result.confidence_score:.2f})"
            )

            return result

        except Exception as e:
            logger.error(f"Processing failed for {use_case.value}: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources."""
        if (
            hasattr(self.local_llm_processor, "session")
            and self.local_llm_processor.session
        ):
            await self.local_llm_processor.session.close()


# Factory methods for creating hybrid LLM clients
class HybridLLMClientFactory:
    """Factory for creating hybrid LLM clients."""

    @staticmethod
    def create_smart_client() -> HybridLLMClient:
        """Create smart client with algorithmic processing priority."""
        config = HybridLLMConfig(
            enable_algorithmic=True,
            enable_local_llm=True,
            enable_openai=False,  # Disabled for core operations
            max_openai_calls_per_hour=0,
        )
        return HybridLLMClient(config)

    @staticmethod
    def create_complex_agent_client(agent_type: str) -> HybridLLMClient:
        """Create client for complex agents with minimal OpenAI usage."""
        config = HybridLLMConfig(
            enable_algorithmic=True,
            enable_local_llm=True,
            enable_openai=False,  # Algorithmic + Local only
            ollama_model=(
                "gemma2:2b" if agent_type in ["market", "logistics"] else "gemma2:7b"
            ),
        )
        return HybridLLMClient(config)

    @staticmethod
    def create_liaison_client() -> HybridLLMClient:
        """Create client for liaison agent with strategic Gemini usage (15% target)."""
        config = HybridLLMConfig(
            enable_algorithmic=True,
            enable_local_llm=True,
            enable_openai=False,  # Disabled for cost optimization
            enable_gemini=True,  # Strategic use for user communication
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_usage_percentage=0.15,  # 15% target usage
        )
        return HybridLLMClient(config)
