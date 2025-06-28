"""
Simple LLM Client Implementation for FlipSync
============================================

A clean, direct implementation that bypasses complex session management
and provides reliable OpenAI/Ollama integration with proper fallback.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"
    LOCAL = "local"  # For compatibility with legacy config


class ModelType(str, Enum):
    """Available model types - OpenAI models for production."""

    # OpenAI models (PRODUCTION)
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4O = "gpt-4o"

    # Legacy compatibility (deprecated - use GPT_4O_MINI)
    GEMMA3_4B = "gpt-4o-mini"  # Redirected to OpenAI for production
    GEMMA_2B = "gpt-4o-mini"  # Redirected to OpenAI for production
    GEMMA_7B = "gpt-4o-mini"  # Redirected to OpenAI for production
    LLAMA3_LATEST = "gpt-4o-mini"  # Redirected to OpenAI for production
    LOCAL_LLAMA = "gpt-4o-mini"  # Redirected to OpenAI for production


@dataclass
class SimpleLLMConfig:
    """Simple LLM configuration."""

    provider: ModelProvider
    model_type: ModelType
    temperature: float = 0.7
    max_tokens: Optional[int] = 512  # Optimized for fast OpenAI generation
    timeout: float = 30.0  # OpenAI timeout (fast response times)
    api_key: Optional[str] = None
    project_id: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class ComplexUnifiedAgentLLMConfig:
    """Configuration for complex internal agents using OpenAI GPT models."""

    provider: ModelProvider = ModelProvider.OPENAI
    model_type: ModelType = ModelType.GPT_4O_MINI
    temperature: float = 0.1  # Optimized for focused analysis
    max_tokens: int = 512  # OPTIMIZED: Reduced for faster responses
    timeout: float = 30.0  # OpenAI timeout (fast response times)
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    @classmethod
    def for_agent_type(cls, agent_type: str) -> "ComplexUnifiedAgentLLMConfig":
        """Create optimized config for specific agent type."""
        agent_configs = {
            "market": {"temperature": 0.1, "max_tokens": 512},
            "content": {"temperature": 0.2, "max_tokens": 768},
            "logistics": {"temperature": 0.1, "max_tokens": 512},
            "executive": {"temperature": 0.3, "max_tokens": 1024},
        }

        config = agent_configs.get(agent_type, {"temperature": 0.1, "max_tokens": 1024})
        api_key = os.getenv("OPENAI_API_KEY")

        return cls(
            temperature=config["temperature"],
            max_tokens=config["max_tokens"],
            api_key=api_key,
        )


@dataclass
class LLMResponse:
    """LLM response container."""

    content: str
    provider: ModelProvider
    model: str
    response_time: float
    metadata: Dict[str, Any]
    tokens_used: int = 0  # Add tokens_used attribute with default value
    confidence_score: float = 0.8  # Add confidence_score attribute with default value


class SimpleLLMClient:
    """Simple, reliable LLM client with OpenAI/Ollama support."""

    def __init__(self, config: SimpleLLMConfig):
        """Initialize the simple LLM client."""
        self.config = config
        self.provider = config.provider
        self.model = config.model_type.value

        logger.info(
            f"Initialized SimpleLLMClient: {self.provider.value} - {self.model}"
        )

    async def generate_response(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        start_time = time.time()

        try:
            if self.provider == ModelProvider.OPENAI:
                content = await self._generate_openai(prompt, system_prompt)
            else:
                raise ValueError(
                    f"Unsupported provider: {self.provider}. Only OpenAI is supported in production."
                )

            response_time = time.time() - start_time

            response = LLMResponse(
                content=content,
                provider=self.provider,
                model=self.model,
                response_time=response_time,
                metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
                tokens_used=(
                    len(content.split()) if content else 0
                ),  # Estimate tokens as word count
                confidence_score=0.8,  # Default confidence score
            )

            # Record performance metrics
            try:
                from fs_agt_clean.core.monitoring.ai_performance_monitor import (
                    record_ai_performance,
                )

                record_ai_performance(
                    model_name=self.model,
                    response_time=response_time,
                    prompt_length=len(prompt),
                    response_length=len(content),
                    success=True,
                )
            except Exception as monitor_error:
                logger.warning(
                    f"Failed to record AI performance metrics: {monitor_error}"
                )

            return response

        except Exception as e:
            response_time = time.time() - start_time

            # Record failed performance metrics
            try:
                from fs_agt_clean.core.monitoring.ai_performance_monitor import (
                    record_ai_performance,
                )

                record_ai_performance(
                    model_name=self.model,
                    response_time=response_time,
                    prompt_length=len(prompt),
                    response_length=0,
                    success=False,
                    error_message=str(e),
                )
            except Exception as monitor_error:
                logger.warning(
                    f"Failed to record AI performance metrics: {monitor_error}"
                )

            logger.error(f"Error generating response: {type(e).__name__}: {str(e)}")
            logger.error(f"Provider: {self.provider.value}, Model: {self.model}")
            raise

    async def _generate_openai(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate response using OpenAI API."""
        try:
            import openai

            if not self.config.api_key:
                raise ValueError("OpenAI API key is required")

            # Initialize OpenAI client with project ID and proper SSL configuration
            import ssl
            import httpx

            # Create proper SSL context for Docker environments
            ssl_context = ssl.create_default_context()

            # Create HTTP client with proper SSL configuration
            http_client = httpx.AsyncClient(verify=ssl_context, timeout=30.0)

            client_kwargs = {"api_key": self.config.api_key, "http_client": http_client}
            if self.config.project_id:
                client_kwargs["project"] = self.config.project_id
            client = openai.AsyncOpenAI(**client_kwargs)

            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Call OpenAI API
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            return response.choices[0].message.content

        except ImportError:
            logger.error(
                "OpenAI package not installed. Install with: pip install openai"
            )
            raise
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def _generate_ollama(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate response using Ollama API with improved timeout and error handling."""
        base_url = None
        timeout_seconds = None
        request_data = None

        try:
            # Use environment-based URL discovery
            base_url = self.config.base_url or self._discover_ollama_url()

            # Get timeout from environment or use config default - increased for gemma3:4b stability
            default_timeout = max(
                self.config.timeout, 60.0
            )  # Ensure minimum 60s for gemma3:4b
            timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT", str(default_timeout)))

            logger.info(f"🔄 [DEBUG] Starting Ollama generation")
            logger.info(f"🔄 [DEBUG] Base URL: {base_url}")
            logger.info(f"🔄 [DEBUG] Model: {self.model}")
            logger.info(f"🔄 [DEBUG] Timeout: {timeout_seconds}s")
            logger.info(f"🔄 [DEBUG] Config timeout: {self.config.timeout}s")
            logger.info(
                f"🔄 [DEBUG] OLLAMA_TIMEOUT env: {os.getenv('OLLAMA_TIMEOUT', 'NOT_SET')}"
            )
            logger.info(f"🔄 [DEBUG] Prompt length: {len(prompt)}")
            logger.info(
                f"🔄 [DEBUG] System prompt length: {len(system_prompt) if system_prompt else 0}"
            )

            # Test connectivity first
            logger.info(f"🔄 [DEBUG] Testing connectivity to {base_url}")
            test_timeout = aiohttp.ClientTimeout(
                total=10.0
            )  # Short timeout for connectivity test
            try:
                async with aiohttp.ClientSession(timeout=test_timeout) as test_session:
                    async with test_session.get(
                        f"{base_url}/api/tags"
                    ) as test_response:
                        if test_response.status == 200:
                            tags_data = await test_response.json()
                            logger.info(
                                f"✅ [DEBUG] Connectivity test passed. Available models: {len(tags_data.get('models', []))}"
                            )
                        else:
                            logger.error(
                                f"❌ [DEBUG] Connectivity test failed: {test_response.status}"
                            )
            except Exception as conn_e:
                logger.error(
                    f"❌ [DEBUG] Connectivity test exception: {type(conn_e).__name__}: {str(conn_e)}"
                )

            # Prepare messages for /api/chat endpoint (working endpoint)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Prepare request data for /api/chat endpoint with Gemma 3 optimizations
            options = {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens or 1024,
            }

            # Add Gemma 3 specific parameters if using ComplexUnifiedAgentLLMConfig
            if isinstance(self.config, ComplexUnifiedAgentLLMConfig):
                options.update(
                    {
                        "top_k": self.config.top_k,
                        "top_p": self.config.top_p,
                        "repeat_penalty": self.config.repeat_penalty,
                        "repeat_last_n": self.config.repeat_last_n,
                        "num_ctx": self.config.num_ctx,
                        "num_batch": 512,  # Optimized batch size for Gemma 3
                        "num_thread": 4,  # Match Docker CPU allocation
                        "use_mmap": True,  # Enable memory mapping for efficiency
                        "use_mlock": False,  # Disable memory locking for stability
                        "numa": False,  # Disable NUMA for Docker environment
                    }
                )

            # Enable streaming for better user experience
            enable_streaming = (
                isinstance(self.config, ComplexUnifiedAgentLLMConfig)
                and self.config.stream
            )

            request_data = {
                "model": self.model,
                "messages": messages,
                "stream": enable_streaming,  # OPTIMIZED: Enable streaming for real-time responses
                "options": options,
            }

            logger.info(f"🔄 [DEBUG] Request data prepared: {request_data}")
            logger.info(f"🔄 [DEBUG] About to make POST request to {base_url}/api/chat")

            # Make direct HTTP request with proper timeout from environment
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            logger.info(f"🔄 [DEBUG] Created aiohttp timeout: {timeout}")

            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.info(f"🔄 [DEBUG] Created aiohttp session")

                start_time = datetime.now()
                logger.info(f"🔄 [DEBUG] Starting POST request at {start_time}")

                async with session.post(
                    f"{base_url}/api/chat", json=request_data
                ) as response:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(
                        f"🔄 [DEBUG] Got response after {elapsed:.2f}s, status: {response.status}"
                    )

                    if response.status == 200:
                        logger.info(f"🔄 [DEBUG] Reading response JSON...")
                        data = await response.json()
                        # Extract response from chat API format
                        message = data.get("message", {})
                        content = message.get("content", "")
                        logger.info(
                            f"✅ [DEBUG] Ollama response received: {len(content)} characters"
                        )
                        logger.info(f"✅ [DEBUG] Total time: {elapsed:.2f}s")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"❌ [DEBUG] Ollama API error: HTTP {response.status} - {error_text}"
                        )
                        raise Exception(f"Ollama API error: {response.status}")

        except Exception as e:
            logger.error(f"❌ [DEBUG] Exception in _generate_ollama:")
            logger.error(f"❌ [DEBUG] Exception type: {type(e).__name__}")
            logger.error(f"❌ [DEBUG] Exception message: {str(e)}")
            logger.error(f"❌ [DEBUG] Base URL: {base_url}")
            logger.error(f"❌ [DEBUG] Timeout used: {timeout_seconds}s")
            logger.error(f"❌ [DEBUG] Model: {self.model}")
            logger.error(f"❌ [DEBUG] Provider: {self.provider.value}")

            # Log the full request data if available
            if request_data:
                logger.error(f"❌ [DEBUG] Request data: {request_data}")
            else:
                logger.error(f"❌ [DEBUG] Request data: Not prepared yet")

            # Re-raise with original error
            raise

    def _discover_ollama_url(self) -> str:
        """Discover Ollama service URL."""
        # Try environment variables first
        if base_url := os.getenv("OLLAMA_BASE_URL"):
            return base_url.rstrip("/")

        # Try host and port
        host = os.getenv("OLLAMA_HOST", "ollama-cpu")
        port = os.getenv("OLLAMA_PORT", "11434")

        return f"http://{host}:{port}"

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get LLM usage statistics."""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "total_requests": 0,  # TODO: Implement request tracking
            "total_tokens": 0,  # TODO: Implement token tracking
            "average_response_time": 0.0,  # TODO: Implement timing tracking
            "last_request_time": None,
            "status": "operational",
        }


class SimpleLLMClientFactory:
    """Factory for creating simple LLM clients."""

    @staticmethod
    def create_client(
        provider: ModelProvider,
        model_type: ModelType,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> SimpleLLMClient:
        """Create a simple LLM client."""
        # Get project_id from environment if not provided
        if not project_id:
            project_id = os.getenv("OPENAI_PROJECT_ID")

        config = SimpleLLMConfig(
            provider=provider,
            model_type=model_type,
            temperature=temperature,
            api_key=api_key,
            project_id=project_id,
            base_url=base_url,
        )
        return SimpleLLMClient(config)

    @staticmethod
    def create_ollama_client(
        model_type: ModelType = ModelType.GPT_4O_MINI,  # PRODUCTION: Use OpenAI instead of Ollama
        temperature: float = 0.7,
    ) -> SimpleLLMClient:
        """Create an OpenAI client (formerly Ollama - migrated for production)."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for production"
            )
        return SimpleLLMClientFactory.create_client(
            provider=ModelProvider.OPENAI,
            model_type=model_type,
            temperature=temperature,
            api_key=api_key,
        )

    @staticmethod
    def create_openai_client(
        model_type: ModelType = ModelType.GPT_4O_MINI,
        temperature: float = 0.7,
        api_key: Optional[str] = None,
    ) -> SimpleLLMClient:
        """Create an OpenAI client."""
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        return SimpleLLMClientFactory.create_client(
            provider=ModelProvider.OPENAI,
            model_type=model_type,
            temperature=temperature,
            api_key=api_key,
        )

    @staticmethod
    def create_smart_client() -> SimpleLLMClient:
        """Create a smart client using OpenAI exclusively for production."""
        # PRODUCTION: Use OpenAI exclusively - no fallbacks
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for production"
            )
        return SimpleLLMClientFactory.create_openai_client(api_key=api_key)

    @staticmethod
    def create_complex_agent_client(agent_type: str) -> SimpleLLMClient:
        """Create optimized LLM client for complex agents using OpenAI GPT-4o-mini with agent-specific tuning."""
        # Get agent-specific configuration
        agent_configs = {
            "market": {"temperature": 0.1, "max_tokens": 512},
            "content": {"temperature": 0.2, "max_tokens": 768},
            "logistics": {"temperature": 0.1, "max_tokens": 512},
            "executive": {"temperature": 0.3, "max_tokens": 1024},
        }

        agent_config = agent_configs.get(
            agent_type, {"temperature": 0.1, "max_tokens": 1024}
        )

        # PRODUCTION: Use OpenAI GPT-4o-mini exclusively for complex agents
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for production"
            )

        config = SimpleLLMConfig(
            provider=ModelProvider.OPENAI,
            model_type=ModelType.GPT_4O_MINI,
            temperature=agent_config["temperature"],
            max_tokens=agent_config["max_tokens"],
            timeout=30.0,  # OpenAI timeout (much faster than Ollama)
            api_key=api_key,
        )
        return SimpleLLMClient(config)

    @staticmethod
    def create_liaison_client() -> SimpleLLMClient:
        """Create LLM client for liaison/concierge agent using OpenAI GPT-4o-mini for fast intent recognition."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for production"
            )

        config = SimpleLLMConfig(
            provider=ModelProvider.OPENAI,
            model_type=ModelType.GPT_4O_MINI,
            temperature=0.7,
            max_tokens=256,  # OPTIMIZED: Reduced for faster liaison responses
            timeout=30.0,  # OpenAI timeout (much faster than Ollama)
            api_key=api_key,
        )
        return SimpleLLMClient(config)
