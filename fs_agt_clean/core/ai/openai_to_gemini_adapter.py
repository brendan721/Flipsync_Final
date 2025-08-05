"""
OpenAI to Gemini Migration Adapter
=================================

Drop-in replacement adapter that provides OpenAI-compatible interface
while using Google Gemini backend for cost optimization.

Features:
- Backward-compatible OpenAI API interface
- Automatic routing to Strategic LLM Service
- Cost tracking and optimization
- Fallback mechanisms for reliability
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .strategic_llm_service import StrategicLLMService, StrategicTask
from .gemini_client import GeminiClient, GeminiModel

logger = logging.getLogger(__name__)


class OpenAIToGeminiAdapter:
    """
    Adapter that provides OpenAI-compatible interface using Gemini backend.
    
    This allows existing code to continue working while migrating to Gemini
    for cost optimization and strategic LLM usage.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-pro-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        """Initialize adapter with OpenAI-compatible parameters."""
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize Gemini backend
        self.strategic_llm = StrategicLLMService()
        self.gemini_client = GeminiClient()
        
        # Map OpenAI models to Gemini models
        self.model_mapping = {
            "gemini-pro-mini": GeminiModel.FLASH_2_5,
            "gemini-pro": GeminiModel.PRO_2_5,
            "gemini-pro": GeminiModel.PRO_2_5,
            "gemini-pro": GeminiModel.FLASH_LITE_2_5,
        }
        
        logger.info(f"OpenAI to Gemini adapter initialized (model: {model})")
    
    async def chat_completions_create(
        self,
        model: Optional[str] = None,
        messages: List[Dict[str, str]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completions interface.
        
        Args:
            model: Model name (mapped to Gemini equivalent)
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Returns:
            OpenAI-compatible response format
        """
        start_time = time.perf_counter()
        
        # Use provided parameters or defaults
        model_name = model or self.model
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens or self.max_tokens
        
        # Map to Gemini model
        gemini_model = self.model_mapping.get(model_name, GeminiModel.FLASH_2_5)
        
        try:
            # Extract prompt and system message from OpenAI format
            system_prompt = None
            user_prompt = ""
            
            if messages:
                for message in messages:
                    if message.get("role") == "system":
                        system_prompt = message.get("content", "")
                    elif message.get("role") == "user":
                        user_prompt = message.get("content", "")
                    elif message.get("role") == "assistant":
                        # For conversation context
                        user_prompt += f"\nAssistant: {message.get('content', '')}\nUser: "
            
            # Determine if this is a strategic task
            strategic_task = self._detect_strategic_task(user_prompt)
            
            if strategic_task:
                # Use Strategic LLM Service for high-value tasks
                result = await self._handle_strategic_task(
                    strategic_task, user_prompt, system_prompt
                )
                response_text = result.result.get("enhanced_content", result.result.get("raw_analysis", ""))
                cost = result.cost_estimate
            else:
                # Use direct Gemini client for general tasks
                response = await self.gemini_client.generate_content(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model=gemini_model,
                    temperature=temp,
                    max_tokens=max_tok,
                )
                
                if response.success:
                    response_text = response.text
                    cost = response.usage.cost_estimate
                else:
                    # Fallback response
                    response_text = "I apologize, but I'm unable to process that request at the moment."
                    cost = 0.0
            
            # Create OpenAI-compatible response
            processing_time = time.perf_counter() - start_time
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": len(user_prompt.split()) * 1.3,  # Rough estimate
                    "completion_tokens": len(response_text.split()) * 1.3,
                    "total_tokens": (len(user_prompt) + len(response_text)) * 1.3,
                },
                "gemini_metadata": {
                    "cost_estimate": cost,
                    "processing_time": processing_time,
                    "backend": "gemini",
                    "strategic_task": strategic_task.value if strategic_task else None,
                },
            }
            
        except Exception as e:
            logger.error(f"OpenAI to Gemini adapter error: {e}")
            
            # Return error in OpenAI format
            return {
                "error": {
                    "message": str(e),
                    "type": "adapter_error",
                    "code": "gemini_backend_error",
                }
            }
    
    def _detect_strategic_task(self, prompt: str) -> Optional[StrategicTask]:
        """
        Detect if the prompt requires strategic LLM usage.
        
        Args:
            prompt: User prompt to analyze
        
        Returns:
            StrategicTask if strategic usage is justified, None otherwise
        """
        prompt_lower = prompt.lower()
        
        # Image analysis keywords
        if any(keyword in prompt_lower for keyword in [
            "image", "photo", "picture", "analyze", "product", "visual", "identify"
        ]):
            return StrategicTask.PRODUCT_IMAGE_ANALYSIS
        
        # Market trend analysis keywords
        if any(keyword in prompt_lower for keyword in [
            "trend", "market", "price", "demand", "forecast", "competition", "sales"
        ]):
            return StrategicTask.MARKET_TREND_ANALYSIS
        
        # Content enhancement keywords
        if any(keyword in prompt_lower for keyword in [
            "seo", "optimize", "enhance", "improve", "title", "description", "keywords"
        ]):
            return StrategicTask.CONTENT_QUALITY_ENHANCEMENT
        
        # Default to general LLM usage (not strategic)
        return None
    
    async def _handle_strategic_task(
        self,
        task: StrategicTask,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Any:
        """Handle strategic LLM tasks using Strategic LLM Service."""
        
        if task == StrategicTask.PRODUCT_IMAGE_ANALYSIS:
            # Extract product context from prompt
            product_context = {
                "title": "Product from prompt analysis",
                "category": "General",
                "description": prompt,
            }
            return await self.strategic_llm.analyze_product_image(
                image_data=b"",  # No actual image data in text prompt
                product_context=product_context,
            )
        
        elif task == StrategicTask.MARKET_TREND_ANALYSIS:
            # Extract market data from prompt
            historical_data = {
                "prompt_analysis": prompt,
                "context": system_prompt or "",
            }
            return await self.strategic_llm.analyze_market_trends(
                product_category="General",
                historical_data=historical_data,
            )
        
        elif task == StrategicTask.CONTENT_QUALITY_ENHANCEMENT:
            # Extract content and keywords from prompt
            target_keywords = []
            # Simple keyword extraction
            if "keywords:" in prompt.lower():
                keyword_section = prompt.lower().split("keywords:")[1].split("\n")[0]
                target_keywords = [kw.strip() for kw in keyword_section.split(",")]
            
            return await self.strategic_llm.enhance_content_quality(
                content=prompt,
                content_type="general",
                target_keywords=target_keywords,
            )
        
        else:
            # Fallback to direct Gemini
            response = await self.gemini_client.generate_content(prompt)
            return type('Result', (), {
                'result': {'raw_analysis': response.text},
                'cost_estimate': response.usage.cost_estimate,
            })()


class AsyncOpenAI:
    """
    Drop-in replacement for OpenAI AsyncOpenAI client.
    
    Provides the same interface but uses Gemini backend for cost optimization.
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize with OpenAI-compatible parameters."""
        self.adapter = OpenAIToGeminiAdapter(api_key=api_key)
        self.chat = ChatCompletions(self.adapter)
        self.embeddings = Embeddings()
        
        logger.info("AsyncOpenAI compatibility layer initialized with Gemini backend")


class ChatCompletions:
    """OpenAI-compatible chat completions interface."""
    
    def __init__(self, adapter: OpenAIToGeminiAdapter):
        self.adapter = adapter
    
    async def create(self, **kwargs) -> Dict[str, Any]:
        """Create chat completion using Gemini backend."""
        return await self.adapter.chat_completions_create(**kwargs)


class Embeddings:
    """OpenAI-compatible embeddings interface (placeholder)."""
    
    async def create(self, **kwargs) -> Dict[str, Any]:
        """Create embeddings (placeholder - could integrate with Gemini embeddings)."""
        logger.warning("Embeddings not yet migrated to Gemini - using placeholder")
        return {
            "data": [{"embedding": [0.0] * 1536, "index": 0}],
            "model": "text-embedding-ada-002",
            "usage": {"prompt_tokens": 10, "total_tokens": 10},
        }


# Backward compatibility aliases
OpenAI = AsyncOpenAI  # For synchronous usage


def create_openai_compatible_client(**kwargs) -> AsyncOpenAI:
    """Create OpenAI-compatible client using Gemini backend."""
    return AsyncHybridLLMClient()


# Global instance for easy migration
openai_gemini_adapter = AsyncHybridLLMClient()
