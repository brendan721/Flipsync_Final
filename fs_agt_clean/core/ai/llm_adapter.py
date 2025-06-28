"""
LLM Adapter for FlipSync Chat Integration
========================================

Provides compatibility between the new SimpleLLMClient and existing
chat service interfaces, enabling seamless integration without breaking changes.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.ai.simple_llm_client import (
    LLMResponse,
    ModelProvider,
    ModelType,
    SimpleLLMClient,
    SimpleLLMClientFactory,
)

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Conversation context for compatibility."""

    conversation_id: str
    messages: List[Dict[str, str]]


class LLMClientAdapter:
    """Adapter to make SimpleLLMClient compatible with existing chat service."""

    def __init__(self, simple_client: SimpleLLMClient):
        """Initialize the adapter."""
        self.client = simple_client
        self.model_type = simple_client.config.model_type

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[ConversationContext] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate response with compatibility for existing interface."""
        try:
            # CRITICAL: Build enhanced system prompt with agent context
            enhanced_system_prompt = self._build_enhanced_system_prompt(
                system_prompt, context
            )

            # CRITICAL: Build context-aware prompt with conversation history
            enhanced_prompt = self._build_context_aware_prompt(prompt, context)

            logger.info(
                f"🎯 Generating response with agent context: conversation_id={getattr(context, 'conversation_id', 'none')}"
            )

            # Use the simple client to generate response
            response = await self.client.generate_response(
                prompt=enhanced_prompt, system_prompt=enhanced_system_prompt, **kwargs
            )

            logger.info(
                f"✅ Generated response using {response.provider.value} in {response.response_time:.2f}s"
            )
            return response

        except Exception as e:
            logger.error(f"❌ Error in LLM adapter: {type(e).__name__}: {str(e)}")
            raise

    def _build_enhanced_system_prompt(
        self, system_prompt: Optional[str], context: Optional[ConversationContext]
    ) -> str:
        """Build simple concierge system prompt aligned with FlipSync vision."""

        # Use provided system prompt or default
        if system_prompt:
            enhanced_prompt = system_prompt
        else:
            # OPTIMIZED: Ultra-short prompt for Gemma3 performance
            enhanced_prompt = """You are FlipSync Assistant. Help eBay sellers with friendly, practical advice.

Be: Helpful, encouraging, clear
Focus: Quick wins, simple improvements
Style: Friendly and supportive"""

        # Add conversation context if available
        if context:
            conversation_id = getattr(context, "conversation_id", None)
            if conversation_id:
                enhanced_prompt += f"\n\nConversation: {conversation_id}"

        return enhanced_prompt

    def _build_context_aware_prompt(
        self, user_prompt: str, context: Optional[ConversationContext]
    ) -> str:
        """Build simple context-aware prompt for concierge model."""

        # CORRECT: Keep it simple for Gemma3 concierge
        # Just use the user prompt directly - let the concierge be natural
        return user_prompt


class FlipSyncLLMFactory:
    """Factory for creating FlipSync-optimized LLM clients with proper fallback."""

    @staticmethod
    def create_fast_client() -> LLMClientAdapter:
        """Create a fast client for simple queries using OpenAI GPT-4o-mini for production."""
        # PRODUCTION: Use OpenAI GPT-4o-mini exclusively - no fallbacks
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for production"
            )

        simple_client = SimpleLLMClientFactory.create_openai_client(
            model_type=ModelType.GPT_4O_MINI, temperature=0.3
        )
        logger.info(
            "Created fast OpenAI client with GPT-4o-mini for sophisticated agent system"
        )
        return LLMClientAdapter(simple_client)

    @staticmethod
    def create_smart_client() -> LLMClientAdapter:
        """Create a smart client for complex queries using OpenAI GPT-4o-mini for production."""
        # PRODUCTION: Use OpenAI GPT-4o-mini exclusively - no fallbacks
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for production"
            )

        simple_client = SimpleLLMClientFactory.create_openai_client(
            model_type=ModelType.GPT_4O_MINI, temperature=0.7
        )
        logger.info(
            "Created smart OpenAI client with GPT-4o-mini for sophisticated agent system"
        )
        return LLMClientAdapter(simple_client)

    @staticmethod
    def create_business_client() -> LLMClientAdapter:
        """Create a business-optimized client using OpenAI GPT-4o-mini for production."""
        # PRODUCTION: Use OpenAI GPT-4o-mini exclusively - no fallbacks
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for production"
            )

        simple_client = SimpleLLMClientFactory.create_openai_client(
            model_type=ModelType.GPT_4O_MINI,
            temperature=0.6,  # Conservative for business operations
        )
        logger.info(
            "Created business OpenAI client with GPT-4o-mini for sophisticated agent system"
        )
        return LLMClientAdapter(simple_client)

    @staticmethod
    def create_complex_agent_client(agent_type: str) -> LLMClientAdapter:
        """Create a complex agent client using OpenAI GPT-4o-mini for production."""
        # PRODUCTION: Use OpenAI GPT-4o-mini exclusively - no fallbacks
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for production"
            )

        simple_client = SimpleLLMClientFactory.create_openai_client(
            model_type=ModelType.GPT_4O_MINI,
            temperature=0.3,  # Lower temperature for focused analysis
        )
        logger.info(
            f"Created complex agent client for {agent_type} using OpenAI GPT-4o-mini"
        )
        return LLMClientAdapter(simple_client)

    @staticmethod
    def create_liaison_client() -> LLMClientAdapter:
        """Create a liaison/concierge client using OpenAI GPT-4o-mini for fast intent recognition."""
        # PRODUCTION: Use OpenAI GPT-4o-mini exclusively - no fallbacks
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for production"
            )

        simple_client = SimpleLLMClientFactory.create_liaison_client()
        logger.info(
            "Created liaison client using OpenAI GPT-4o-mini for fast intent recognition"
        )
        return LLMClientAdapter(simple_client)


def test_llm_integration():
    """Test function to verify LLM integration works."""
    import asyncio

    async def run_test():
        try:
            # Test fast client
            fast_client = FlipSyncLLMFactory.create_fast_client()
            response = await fast_client.generate_response(
                prompt="Create an eBay title for a vintage camera",
                system_prompt="You are an eBay listing optimization expert.",
            )

            print(f"✅ Fast client test successful:")
            print(f"   Provider: {response.provider.value}")
            print(f"   Model: {response.model}")
            print(f"   Response time: {response.response_time:.2f}s")
            print(f"   Content: {response.content[:100]}...")

            return True

        except Exception as e:
            print(f"❌ LLM integration test failed: {e}")
            return False

    return asyncio.run(run_test())


if __name__ == "__main__":
    # Run integration test
    test_llm_integration()
