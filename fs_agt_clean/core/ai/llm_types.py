"""
Common LLM Types and Response Classes for FlipSync
=================================================

Shared types and response classes used across different LLM clients
to eliminate dependencies on SimpleLLMClient while maintaining compatibility.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class ModelProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    LOCAL = "local"  # For compatibility with legacy config


class ModelType(str, Enum):
    """Available model types - OpenAI models for production."""

    # OpenAI models (PRODUCTION)
    GPT_4O_MINI = "gemini-pro-mini"
    GPT_4_TURBO = "gemini-pro-turbo-preview"
    GPT_4O = "gemini-pro"

    # Gemini models (STRATEGIC)
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-flash"

    # Legacy compatibility (deprecated - use GPT_4O_MINI)
    GEMMA3_4B = "gemini-pro-mini"  # Redirected to OpenAI for production
    GEMMA_2B = "gemini-pro-mini"  # Redirected to OpenAI for production
    GEMMA_7B = "gemini-pro-mini"  # Redirected to OpenAI for production
    LLAMA3_LATEST = "gemini-pro-mini"  # Redirected to OpenAI for production
    LOCAL_LLAMA = "gemini-pro-mini"  # Redirected to OpenAI for production


@dataclass
class LLMResponse:
    """LLM response container - shared across all LLM clients."""

    content: str
    provider: ModelProvider
    model: str
    response_time: float
    metadata: Dict[str, Any]
    tokens_used: int = 0  # Add tokens_used attribute with default value
    confidence_score: float = 0.8  # Add confidence_score attribute with default value

    @property
    def token_usage(self) -> Dict[str, Any]:
        """Backward compatibility property for token usage."""
        return {
            "prompt_tokens": self.metadata.get("prompt_tokens", 0),
            "completion_tokens": self.metadata.get("completion_tokens", 0),
            "total_tokens": self.tokens_used,
        }


@dataclass
class SimpleLLMConfig:
    """Simple LLM configuration - shared configuration class."""

    provider: ModelProvider
    model: ModelType
    api_key: str
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.provider == ModelProvider.OPENAI and not self.api_key:
            raise ValueError("OpenAI API key is required for OpenAI provider")
        
        if self.provider == ModelProvider.GEMINI and not self.api_key:
            raise ValueError("Gemini API key is required for Gemini provider")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        
        if self.max_tokens < 1:
            raise ValueError("Max tokens must be positive")


# Factory functions for common configurations
def create_openai_config(
    api_key: str,
    model: ModelType = ModelType.GPT_4O_MINI,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> SimpleLLMConfig:
    """Create OpenAI configuration."""
    return SimpleLLMConfig(
        provider=ModelProvider.OPENAI,
        model=model,
        api_key=api_key,
        base_url="https://api.openai.com/v1",
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_gemini_config(
    api_key: str,
    model: ModelType = ModelType.GEMINI_FLASH,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> SimpleLLMConfig:
    """Create Gemini configuration."""
    return SimpleLLMConfig(
        provider=ModelProvider.GEMINI,
        model=model,
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta",
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_local_config(
    base_url: str = "http://localhost:11434",
    model: ModelType = ModelType.GEMMA3_4B,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> SimpleLLMConfig:
    """Create local/Ollama configuration."""
    return SimpleLLMConfig(
        provider=ModelProvider.LOCAL,
        model=model,
        api_key="",  # Not required for local
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
