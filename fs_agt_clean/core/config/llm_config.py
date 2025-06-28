"""
LLM Configuration Management for FlipSync
========================================

This module provides configuration management for LLM clients including
environment-based settings, fallback configurations, and provider selection.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.ai.simple_llm_client import (
    ComplexUnifiedAgentLLMConfig,
    ModelProvider,
    ModelType,
    SimpleLLMClientFactory,
)
from fs_agt_clean.core.ai.simple_llm_client import SimpleLLMConfig as LLMConfig

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class LLMProviderConfig:
    """Configuration for a specific LLM provider."""

    provider: ModelProvider
    model_type: ModelType
    temperature: float
    max_tokens: Optional[int]
    timeout: float
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority


class LLMConfigManager:
    """Manages LLM configuration across different environments."""

    def __init__(self, environment: Optional[Environment] = None):
        """Initialize LLM configuration manager."""
        self.environment = environment or self._detect_environment()
        self.provider_configs = self._load_provider_configs()

        logger.info(
            f"LLM Config Manager initialized for environment: {self.environment.value}"
        )

    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables."""
        env_name = os.getenv("FLIPSYNC_ENV", "development").lower()

        try:
            return Environment(env_name)
        except ValueError:
            logger.warning(
                f"Unknown environment '{env_name}', defaulting to development"
            )
            return Environment.DEVELOPMENT

    def _load_provider_configs(self) -> Dict[ModelProvider, LLMProviderConfig]:
        """Load provider configurations based on environment."""
        configs = {}

        # Ollama configuration (primary for local development)
        ollama_config = self._create_ollama_config()
        if ollama_config:
            configs[ModelProvider.OLLAMA] = ollama_config

        # OpenAI configuration (fallback for production)
        openai_config = self._create_openai_config()
        if openai_config:
            configs[ModelProvider.OPENAI] = openai_config

        # Local configuration (development only)
        if self.environment == Environment.DEVELOPMENT:
            local_config = self._create_local_config()
            if local_config:
                configs[ModelProvider.LOCAL] = local_config

        return configs

    def _create_ollama_config(self) -> Optional[LLMProviderConfig]:
        """Create Ollama provider configuration with service discovery."""
        # Use service discovery for base URL
        base_url = self._discover_ollama_base_url()

        # Determine model based on environment
        # Use unified gemma3:4b for all environments
        model_type = ModelType.GEMMA3_4B  # Unified model for all agents
        temperature = 0.7 if self.environment != Environment.PRODUCTION else 0.6

        # Priority based on environment: OpenAI first in production, Ollama first in development
        priority = 2 if self.environment == Environment.PRODUCTION else 1

        return LLMProviderConfig(
            provider=ModelProvider.OLLAMA,
            model_type=model_type,
            temperature=temperature,
            max_tokens=2048,
            timeout=float(
                os.getenv("OLLAMA_TIMEOUT", "300.0")
            ),  # EXTENDED: Extended for complex gemma3:4b processing (5 minutes)
            base_url=base_url,
            enabled=True,
            priority=priority,  # Lower priority in production
        )

    def _discover_ollama_base_url(self) -> str:
        """Discover Ollama base URL using multiple fallback methods."""
        # Method 1: Use explicit OLLAMA_BASE_URL if provided
        base_url = os.getenv("OLLAMA_BASE_URL")
        if base_url:
            logger.info(f"Using explicit OLLAMA_BASE_URL: {base_url}")
            return base_url

        # Method 2: Construct from OLLAMA_HOST and OLLAMA_PORT
        ollama_host = os.getenv("OLLAMA_HOST")
        ollama_port = os.getenv("OLLAMA_PORT", "11434")

        if ollama_host:
            if not ollama_host.startswith("http"):
                base_url = f"http://{ollama_host}:{ollama_port}"
            else:
                base_url = ollama_host
            logger.info(f"Using OLLAMA_HOST environment variable: {base_url}")
            return base_url

        # Method 3: Try common Docker service names
        service_names = ["ollama-cpu", "ollama", "ollama-service"]
        for service_name in service_names:
            base_url = f"http://{service_name}:{ollama_port}"
            logger.info(f"Trying service discovery for: {base_url}")
            return base_url

        # Method 4: Fallback to localhost
        base_url = f"http://localhost:{ollama_port}"
        logger.warning(f"Falling back to localhost: {base_url}")
        return base_url

    def _create_openai_config(self) -> Optional[LLMProviderConfig]:
        """Create OpenAI provider configuration."""
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key and self.environment == Environment.PRODUCTION:
            logger.warning("OpenAI API key not found in production environment")
            return None

        # Model selection based on environment
        if self.environment == Environment.PRODUCTION:
            model_type = ModelType.GPT_4O_MINI  # Cost-effective for production
            temperature = 0.6
        elif self.environment == Environment.STAGING:
            model_type = ModelType.GPT_4_TURBO
            temperature = 0.7
        else:
            model_type = ModelType.GPT_4O_MINI  # Fast for development
            temperature = 0.7

        # Priority based on environment: OpenAI first in production, Ollama first in development
        priority = 1 if self.environment == Environment.PRODUCTION else 2

        return LLMProviderConfig(
            provider=ModelProvider.OPENAI,
            model_type=model_type,
            temperature=temperature,
            max_tokens=2048,
            timeout=30.0,
            api_key=api_key,
            enabled=bool(api_key),
            priority=priority,  # Higher priority in production
        )

    def _create_local_config(self) -> Optional[LLMProviderConfig]:
        """Create local provider configuration (development only)."""
        return LLMProviderConfig(
            provider=ModelProvider.LOCAL,
            model_type=ModelType.LOCAL_LLAMA,
            temperature=0.7,
            max_tokens=1024,
            timeout=60.0,
            enabled=True,
            priority=3,  # Lowest priority
        )

    def get_primary_config(self) -> Optional[LLMProviderConfig]:
        """Get the primary (highest priority) LLM configuration."""
        if not self.provider_configs:
            return None

        # Sort by priority (lower number = higher priority) and enabled status
        enabled_configs = [
            config for config in self.provider_configs.values() if config.enabled
        ]

        if not enabled_configs:
            logger.warning("No enabled LLM providers found")
            return None

        primary_config = min(enabled_configs, key=lambda c: c.priority)
        logger.info(
            f"Primary LLM provider: {primary_config.provider.value} ({primary_config.model_type.value})"
        )

        return primary_config

    def get_fallback_configs(self) -> List[LLMProviderConfig]:
        """Get fallback configurations in priority order."""
        enabled_configs = [
            config for config in self.provider_configs.values() if config.enabled
        ]

        # Sort by priority, excluding the primary config
        fallback_configs = sorted(enabled_configs, key=lambda c: c.priority)[1:]

        return fallback_configs

    def get_config_for_provider(
        self, provider: ModelProvider
    ) -> Optional[LLMProviderConfig]:
        """Get configuration for a specific provider."""
        return self.provider_configs.get(provider)

    def create_llm_config(self, provider_config: LLMProviderConfig):
        """Create LLMConfig from provider configuration."""
        return LLMConfig(
            provider=provider_config.provider,
            model_type=provider_config.model_type,
            temperature=provider_config.temperature,
            max_tokens=provider_config.max_tokens,
            timeout=int(provider_config.timeout),  # Convert float to int for timeout
            base_url=provider_config.base_url,
            api_key=provider_config.api_key,
        )

    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment and configuration information."""
        return {
            "environment": self.environment.value,
            "providers": {
                provider.value: {
                    "enabled": config.enabled,
                    "model": config.model_type.value,
                    "priority": config.priority,
                    "temperature": config.temperature,
                }
                for provider, config in self.provider_configs.items()
            },
            "primary_provider": (
                self.get_primary_config().provider.value
                if self.get_primary_config()
                else None
            ),
        }

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current LLM configuration."""
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "provider_status": {},
        }

        # Check if we have at least one enabled provider
        enabled_providers = [p for p, c in self.provider_configs.items() if c.enabled]
        if not enabled_providers:
            validation_results["valid"] = False
            validation_results["issues"].append("No enabled LLM providers found")

        # Validate each provider configuration
        for provider, config in self.provider_configs.items():
            status = {"enabled": config.enabled, "issues": []}

            if config.enabled:
                # Provider-specific validation
                if provider == ModelProvider.OPENAI and not config.api_key:
                    if self.environment == Environment.PRODUCTION:
                        status["issues"].append("Missing OpenAI API key in production")
                        validation_results["valid"] = False
                    else:
                        validation_results["warnings"].append(
                            f"OpenAI API key not configured for {provider.value}"
                        )

                elif provider == ModelProvider.OLLAMA and not config.base_url:
                    status["issues"].append("Missing Ollama base URL")
                    validation_results["warnings"].append(
                        f"Ollama base URL not configured"
                    )

                # Temperature validation
                if not 0.0 <= config.temperature <= 2.0:
                    status["issues"].append(
                        f"Invalid temperature: {config.temperature}"
                    )
                    validation_results["warnings"].append(
                        f"Unusual temperature setting for {provider.value}"
                    )

                # Timeout validation
                if config.timeout <= 0:
                    status["issues"].append(f"Invalid timeout: {config.timeout}")
                    validation_results["valid"] = False

            validation_results["provider_status"][provider.value] = status

        return validation_results


# Global configuration manager instance
_config_manager: Optional[LLMConfigManager] = None


def get_llm_config_manager() -> LLMConfigManager:
    """Get the global LLM configuration manager instance."""
    global _config_manager

    if _config_manager is None:
        _config_manager = LLMConfigManager()

    return _config_manager


def create_configured_llm_client():
    """Create an LLM client using the current configuration."""
    # Import at function level to avoid scoping issues
    from fs_agt_clean.core.ai.simple_llm_client import (
        SimpleLLMClient,
        SimpleLLMClientFactory,
    )

    config_manager = get_llm_config_manager()
    primary_config = config_manager.get_primary_config()

    if not primary_config:
        logger.warning("No primary LLM configuration found, using mock client")
        # Return a mock configuration
        # Legacy LLMClient removed - using SimpleLLMClient architecture
        mock_config = LLMConfig(
            provider=ModelProvider.OPENAI,
            model_type=ModelType.GPT_4O_MINI,
            temperature=0.7,
        )
        return SimpleLLMClientFactory.create_client(
            provider=mock_config.provider,
            model_type=mock_config.model_type,
            temperature=mock_config.temperature,
        )

    llm_config = config_manager.create_llm_config(primary_config)
    # Use SimpleLLMClient instead of legacy LLMClient
    return SimpleLLMClientFactory.create_client(
        provider=llm_config.provider,
        model_type=llm_config.model_type,
        temperature=llm_config.temperature,
    )


def get_business_llm_client():
    """Get an LLM client optimized for business conversations using OpenAI GPT-4o-mini."""
    config_manager = get_llm_config_manager()

    # PRIMARY: Try to get OpenAI configuration for business use
    openai_config = config_manager.get_config_for_provider(ModelProvider.OPENAI)
    if openai_config and openai_config.enabled:
        # Create business-optimized configuration with OpenAI GPT-4o-mini
        business_config = LLMProviderConfig(
            provider=ModelProvider.OPENAI,
            model_type=ModelType.GPT_4O_MINI,  # Use OpenAI GPT-4o-mini for business
            temperature=0.7,  # Good balance for business conversations
            max_tokens=openai_config.max_tokens,
            timeout=openai_config.timeout,
            base_url=openai_config.base_url,
            enabled=True,
            priority=1,
        )

        llm_config = config_manager.create_llm_config(business_config)
        # Use SimpleLLMClient with OpenAI - ensure API key is passed
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        return SimpleLLMClientFactory.create_client(
            provider=llm_config.provider,
            model_type=llm_config.model_type,
            temperature=llm_config.temperature,
            api_key=api_key,
        )

    # Fallback to Ollama only if OpenAI not available
    ollama_config = config_manager.get_config_for_provider(ModelProvider.OLLAMA)
    if ollama_config and ollama_config.enabled:
        logger.warning(
            "OpenAI not available for business client, falling back to Ollama"
        )
        business_config = LLMProviderConfig(
            provider=ollama_config.provider,
            model_type=ModelType.GEMMA3_4B,
            temperature=0.7,
            max_tokens=ollama_config.max_tokens,
            timeout=ollama_config.timeout,
            base_url=ollama_config.base_url,
            enabled=True,
            priority=2,  # Lower priority
        )

        llm_config = config_manager.create_llm_config(business_config)
        return SimpleLLMClientFactory.create_client(
            provider=llm_config.provider,
            model_type=llm_config.model_type,
            temperature=llm_config.temperature,
        )

    # Final fallback to configured client
    return create_configured_llm_client()


def get_complex_agent_llm_client(agent_type: str):
    """Get an LLM client optimized for complex agents using OpenAI GPT-4o-mini."""
    config_manager = get_llm_config_manager()

    # PRIMARY: Try to get OpenAI configuration for complex agents
    openai_config = config_manager.get_config_for_provider(ModelProvider.OPENAI)
    if openai_config and openai_config.enabled:
        # Create complex agent configuration with OpenAI GPT-4o-mini
        complex_config = LLMProviderConfig(
            provider=ModelProvider.OPENAI,
            model_type=ModelType.GPT_4O_MINI,  # Use OpenAI GPT-4o-mini for complex analysis
            temperature=0.3,  # Lower temperature for more focused responses
            max_tokens=2048,  # Higher token limit for detailed analysis
            timeout=30.0,  # OpenAI timeout (much faster than Ollama)
            base_url=openai_config.base_url,
            enabled=True,
            priority=1,
        )

        llm_config = config_manager.create_llm_config(complex_config)
        # Ensure API key is passed for OpenAI
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        return SimpleLLMClientFactory.create_client(
            provider=llm_config.provider,
            model_type=llm_config.model_type,
            temperature=llm_config.temperature,
            base_url=llm_config.base_url,
            api_key=api_key,
        )

    # Fallback to Ollama only if OpenAI not available
    ollama_config = config_manager.get_config_for_provider(ModelProvider.OLLAMA)
    if ollama_config and ollama_config.enabled:
        logger.warning(
            f"OpenAI not available for complex agent {agent_type}, falling back to Ollama"
        )
        complex_config = LLMProviderConfig(
            provider=ollama_config.provider,
            model_type=ModelType.GEMMA3_4B,
            temperature=0.3,
            max_tokens=2048,
            timeout=300.0,  # Extended timeout for Ollama
            base_url=ollama_config.base_url,
            enabled=True,
            priority=2,  # Lower priority
        )

        llm_config = config_manager.create_llm_config(complex_config)
        return SimpleLLMClientFactory.create_client(
            provider=llm_config.provider,
            model_type=llm_config.model_type,
            temperature=llm_config.temperature,
            base_url=llm_config.base_url,
        )

    # Final fallback to configured client
    logger.warning(
        f"No LLM providers available for complex agent {agent_type}, using standard client"
    )
    return create_configured_llm_client()


def validate_llm_configuration() -> Dict[str, Any]:
    """Validate current LLM configuration."""
    config_manager = get_llm_config_manager()

    validation_results = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "environment": config_manager.environment.value,
        "primary_provider": None,
    }

    # Check if we have at least one enabled provider
    primary_config = config_manager.get_primary_config()
    if not primary_config:
        validation_results["valid"] = False
        validation_results["issues"].append("No enabled LLM providers found")
    else:
        validation_results["primary_provider"] = primary_config.provider.value

    return validation_results
