"""
Strategic Gemini Service for FlipSync
====================================

Implements the 15% strategic Gemini usage for high-value tasks:
- Vision analysis (product image processing)
- Market trend and seasonality analysis
- Content enhancement for SEO/marketing
- Conversational interface responses

This service replaces OpenAI usage for strategic tasks while maintaining
cost optimization and performance targets.
"""

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from fs_agt_clean.core.ai.gemini_client import GeminiClient, GeminiModel, GeminiResponse

logger = logging.getLogger(__name__)


class StrategicUseCase(str, Enum):
    """Strategic use cases for Gemini integration."""
    
    VISION_ANALYSIS = "vision_analysis"
    MARKET_TRENDS = "market_trends"
    SEASONALITY_ANALYSIS = "seasonality_analysis"
    CONTENT_ENHANCEMENT = "content_enhancement"
    USER_COMMUNICATION = "user_communication"
    SEO_OPTIMIZATION = "seo_optimization"


@dataclass
class StrategicAnalysisRequest:
    """Request for strategic Gemini analysis."""
    
    use_case: StrategicUseCase
    content: str
    context: Dict[str, Any] = None
    image_data: Optional[bytes] = None
    priority: str = "normal"  # normal, high, critical
    max_tokens: int = 1000
    temperature: float = 0.7


@dataclass
class StrategicAnalysisResponse:
    """Response from strategic Gemini analysis."""
    
    success: bool
    content: str
    use_case: StrategicUseCase
    processing_time: float
    cost_estimate: float
    confidence_score: float
    model_used: str
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None


class StrategicGeminiService:
    """
    Strategic Gemini service for high-value FlipSync tasks.
    
    Implements 15% strategic LLM usage with cost optimization and
    intelligent routing for maximum business value.
    """
    
    def __init__(self, api_key: Optional[str] = None, daily_budget: float = 15.0):
        """Initialize strategic Gemini service."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable required")
        
        # Initialize Gemini client with cost controls
        self.gemini_client = GeminiClient(
            api_key=self.api_key,
            default_model=GeminiModel.FLASH_2_5,  # Cost-effective default
            daily_budget=daily_budget,
        )
        
        # Usage tracking for 15% target
        self.usage_stats = {
            "total_requests": 0,
            "strategic_requests": 0,
            "cost_total": 0.0,
            "use_case_breakdown": {},
        }
        
        # Model selection for different use cases
        self.use_case_models = {
            StrategicUseCase.VISION_ANALYSIS: GeminiModel.FLASH_2_5,
            StrategicUseCase.MARKET_TRENDS: GeminiModel.PRO_2_5,  # Higher quality for trends
            StrategicUseCase.SEASONALITY_ANALYSIS: GeminiModel.PRO_2_5,
            StrategicUseCase.CONTENT_ENHANCEMENT: GeminiModel.FLASH_2_5,
            StrategicUseCase.USER_COMMUNICATION: GeminiModel.FLASH_LITE_2_5,  # Cost-effective
            StrategicUseCase.SEO_OPTIMIZATION: GeminiModel.FLASH_2_5,
        }
        
        logger.info(f"Strategic Gemini service initialized with ${daily_budget} daily budget")

    async def analyze(self, request: StrategicAnalysisRequest) -> StrategicAnalysisResponse:
        """Perform strategic analysis using Gemini."""
        start_time = time.perf_counter()
        
        try:
            # Track usage
            self.usage_stats["total_requests"] += 1
            self.usage_stats["strategic_requests"] += 1
            
            use_case_count = self.usage_stats["use_case_breakdown"].get(request.use_case.value, 0)
            self.usage_stats["use_case_breakdown"][request.use_case.value] = use_case_count + 1
            
            # Select appropriate model for use case
            model = self.use_case_models.get(request.use_case, GeminiModel.FLASH_2_5)
            
            # Generate system prompt based on use case
            system_prompt = self._get_system_prompt(request.use_case)
            
            # Handle vision analysis separately
            if request.use_case == StrategicUseCase.VISION_ANALYSIS and request.image_data:
                response = await self._analyze_image(request, model, system_prompt)
            else:
                response = await self._analyze_text(request, model, system_prompt)
            
            processing_time = time.perf_counter() - start_time
            
            # Update cost tracking
            self.usage_stats["cost_total"] += response.usage.cost_estimate
            
            return StrategicAnalysisResponse(
                success=True,
                content=response.text,
                use_case=request.use_case,
                processing_time=processing_time,
                cost_estimate=response.usage.cost_estimate,
                confidence_score=0.85,  # High confidence for strategic analysis
                model_used=response.model_used,
                metadata={
                    "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                    "priority": request.priority,
                    "context_provided": bool(request.context),
                },
            )
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            logger.error(f"Strategic Gemini analysis failed: {e}")
            
            return StrategicAnalysisResponse(
                success=False,
                content="",
                use_case=request.use_case,
                processing_time=processing_time,
                cost_estimate=0.0,
                confidence_score=0.0,
                model_used="error",
                error_message=str(e),
            )

    async def _analyze_image(
        self, request: StrategicAnalysisRequest, model: GeminiModel, system_prompt: str
    ) -> GeminiResponse:
        """Analyze image using Gemini Vision."""
        return await self.gemini_client.analyze_image_with_text(
            image_data=request.image_data,
            prompt=f"{system_prompt}\n\n{request.content}",
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

    async def _analyze_text(
        self, request: StrategicAnalysisRequest, model: GeminiModel, system_prompt: str
    ) -> GeminiResponse:
        """Analyze text using Gemini."""
        # Include context if provided
        full_prompt = request.content
        if request.context:
            context_str = "\n".join([f"{k}: {v}" for k, v in request.context.items()])
            full_prompt = f"Context:\n{context_str}\n\nRequest: {request.content}"
        
        return await self.gemini_client.generate_content(
            prompt=full_prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

    def _get_system_prompt(self, use_case: StrategicUseCase) -> str:
        """Get system prompt for specific use case."""
        prompts = {
            StrategicUseCase.VISION_ANALYSIS: """
You are an expert product analyst specializing in e-commerce image analysis.
Analyze product images for:
- Product category and subcategory
- Key features and specifications
- Condition assessment
- Market appeal and positioning
- Suggested keywords for listings
- Estimated market value range
Provide structured, actionable insights for e-commerce optimization.
            """.strip(),
            
            StrategicUseCase.MARKET_TRENDS: """
You are a market intelligence analyst specializing in e-commerce trends.
Analyze market data for:
- Current market trends and patterns
- Seasonal demand fluctuations
- Competitive landscape insights
- Price trend analysis
- Consumer behavior patterns
- Market opportunity identification
Provide data-driven insights for strategic decision-making.
            """.strip(),
            
            StrategicUseCase.SEASONALITY_ANALYSIS: """
You are a seasonality expert for e-commerce markets.
Analyze seasonal patterns for:
- Historical seasonal trends
- Peak demand periods
- Inventory planning recommendations
- Pricing strategy adjustments
- Marketing timing optimization
- Risk assessment for seasonal items
Provide actionable seasonal intelligence for business planning.
            """.strip(),
            
            StrategicUseCase.CONTENT_ENHANCEMENT: """
You are an SEO and content optimization specialist for e-commerce.
Enhance content for:
- SEO keyword optimization
- Compelling product descriptions
- Marketing copy improvement
- Brand voice consistency
- Conversion rate optimization
- Search visibility enhancement
Provide optimized content that drives sales and engagement.
            """.strip(),
            
            StrategicUseCase.USER_COMMUNICATION: """
You are a customer service expert for FlipSync e-commerce platform.
Provide helpful, professional responses that:
- Address user questions clearly
- Maintain brand voice and tone
- Offer actionable solutions
- Escalate complex issues appropriately
- Enhance customer satisfaction
- Drive positive user experience
Be concise, helpful, and solution-oriented.
            """.strip(),
            
            StrategicUseCase.SEO_OPTIMIZATION: """
You are an SEO specialist for e-commerce platforms.
Optimize content for:
- Search engine visibility
- Keyword density and placement
- Meta descriptions and titles
- Product listing optimization
- Category page enhancement
- Long-tail keyword targeting
Provide SEO-optimized content that improves search rankings.
            """.strip(),
        }
        
        return prompts.get(use_case, "You are a helpful AI assistant.")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        strategic_percentage = (
            (self.usage_stats["strategic_requests"] / max(self.usage_stats["total_requests"], 1)) * 100
        )
        
        return {
            **self.usage_stats,
            "strategic_percentage": strategic_percentage,
            "target_percentage": 15.0,
            "on_target": 10.0 <= strategic_percentage <= 20.0,  # 15% ± 5% tolerance
        }

    async def analyze_product_image(self, image_data: bytes, product_context: Dict[str, Any] = None) -> StrategicAnalysisResponse:
        """Convenience method for product image analysis."""
        request = StrategicAnalysisRequest(
            use_case=StrategicUseCase.VISION_ANALYSIS,
            content="Analyze this product image for e-commerce optimization",
            context=product_context,
            image_data=image_data,
            priority="high",
        )
        return await self.analyze(request)

    async def analyze_market_trends(self, category: str, timeframe: str = "30d") -> StrategicAnalysisResponse:
        """Convenience method for market trend analysis."""
        request = StrategicAnalysisRequest(
            use_case=StrategicUseCase.MARKET_TRENDS,
            content=f"Analyze market trends for {category} over the past {timeframe}",
            context={"category": category, "timeframe": timeframe},
            priority="high",
        )
        return await self.analyze(request)

    async def enhance_content(self, content: str, content_type: str = "product_description") -> StrategicAnalysisResponse:
        """Convenience method for content enhancement."""
        request = StrategicAnalysisRequest(
            use_case=StrategicUseCase.CONTENT_ENHANCEMENT,
            content=f"Enhance this {content_type}: {content}",
            context={"content_type": content_type},
            priority="normal",
        )
        return await self.analyze(request)


# Factory function for easy service creation
def create_strategic_gemini_service(daily_budget: float = 15.0) -> StrategicGeminiService:
    """Create strategic Gemini service with FlipSync defaults."""
    return StrategicGeminiService(daily_budget=daily_budget)
