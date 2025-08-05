"""
Gemini LLM Types and Response Classes for FlipSync
=================================================

Gemini-specific types and response classes for FlipSync's exclusive use of Google Gemini.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class ModelProvider(str, Enum):
    """Supported LLM provider - Gemini only."""

    GEMINI = "gemini"


class ModelType(str, Enum):
    """Available Gemini model types."""

    # Gemini models (PRODUCTION)
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-flash"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_PRO = "gemini-2.5-pro"


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
        if self.provider == ModelProvider.GEMINI and not self.api_key:
            raise ValueError("Gemini API key is required for Gemini provider")

        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")

        if self.max_tokens < 1:
            raise ValueError("Max tokens must be positive")


# Factory function for Gemini configuration
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
