"""
Centralized UnifiedAgent Configuration Management

This module provides centralized configuration for all FlipSync agents,
eliminating configuration duplication and ensuring consistency.
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class UnifiedAgentType(str, Enum):
    """Standardized agent types."""

    CONTENT = "content"
    LOGISTICS = "logistics"
    EXECUTIVE = "executive"
    MARKET = "market"
    ANALYTICS = "analytics"
    ASSISTANT = "assistant"


class RequestType(str, Enum):
    """Standardized request types across agents."""

    # Content agent request types
    GENERATE = "generate"
    OPTIMIZE = "optimize"
    TEMPLATE = "template"
    ANALYZE = "analyze"

    # Logistics agent request types
    SHIPPING = "shipping"
    INVENTORY = "inventory"
    TRACKING = "tracking"
    OPTIMIZATION = "optimization"

    # Executive agent request types
    STRATEGIC = "strategic"
    FINANCIAL = "financial"
    INVESTMENT = "investment"
    RESOURCE = "resource"


@dataclass
class ApprovalThresholds:
    """Approval threshold configuration for agent requests."""

    auto_approve: float = 0.8
    requires_human: float = 0.6
    escalation: float = 0.4
    requires_human_approval: List[str] = field(default_factory=list)


@dataclass
class PerformanceSettings:
    """Performance configuration for agents."""

    max_response_time: float = (
        300.0  # seconds - extended for complex gemma3:4b processing
    )
    target_response_time: float = 60.0  # seconds - extended for gemma3:4b
    max_concurrent_requests: int = 10
    timeout_duration: float = (
        360.0  # seconds - extended for complex gemma3:4b processing (6 minutes)
    )
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds


@dataclass
class UnifiedAgentConfiguration:
    """Complete configuration for a specific agent type."""

    agent_type: UnifiedAgentType
    enabled: bool = True
    approval_thresholds: Dict[str, ApprovalThresholds] = field(default_factory=dict)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    capabilities: List[str] = field(default_factory=list)
    model_settings: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class UnifiedAgentSettingsManager:
    """
    Centralized manager for agent configuration settings.

    Provides unified configuration management across all FlipSync agents,
    eliminating duplication and ensuring consistency.
    """

    def __init__(self):
        """Initialize the agent settings manager."""
        self._configurations: Dict[UnifiedAgentType, UnifiedAgentConfiguration] = {}
        self._load_default_configurations()
        self._load_environment_overrides()

    def _load_default_configurations(self):
        """Load default configurations for all agent types."""

        # Content UnifiedAgent Configuration
        content_config = UnifiedAgentConfiguration(
            agent_type=UnifiedAgentType.CONTENT,
            approval_thresholds={
                RequestType.GENERATE.value: ApprovalThresholds(
                    auto_approve=0.85,
                    requires_human=0.6,
                    escalation=0.4,
                    requires_human_approval=["template_changes", "brand_guidelines"],
                ),
                RequestType.OPTIMIZE.value: ApprovalThresholds(
                    auto_approve=0.8, requires_human=0.65, escalation=0.45
                ),
                RequestType.TEMPLATE.value: ApprovalThresholds(
                    auto_approve=0.9,
                    requires_human=0.7,
                    escalation=0.5,
                    requires_human_approval=["template_changes"],
                ),
                RequestType.ANALYZE.value: ApprovalThresholds(
                    auto_approve=0.75, requires_human=0.5, escalation=0.3
                ),
            },
            performance=PerformanceSettings(
                max_response_time=25.0,
                target_response_time=4.0,
                max_concurrent_requests=15,
            ),
            capabilities=[
                "content_generation",
                "seo_optimization",
                "template_creation",
                "content_analysis",
                "keyword_research",
                "marketplace_optimization",
            ],
            model_settings={
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
            },
        )

        # Logistics UnifiedAgent Configuration
        logistics_config = UnifiedAgentConfiguration(
            agent_type=UnifiedAgentType.LOGISTICS,
            approval_thresholds={
                RequestType.SHIPPING.value: ApprovalThresholds(
                    auto_approve=0.8, requires_human=0.6, escalation=0.4
                ),
                RequestType.INVENTORY.value: ApprovalThresholds(
                    auto_approve=0.85,
                    requires_human=0.65,
                    escalation=0.45,
                    requires_human_approval=["inventory_rebalancing"],
                ),
                RequestType.TRACKING.value: ApprovalThresholds(
                    auto_approve=0.9, requires_human=0.7, escalation=0.5
                ),
                RequestType.OPTIMIZATION.value: ApprovalThresholds(
                    auto_approve=0.75,
                    requires_human=0.55,
                    escalation=0.35,
                    requires_human_approval=["carrier_changes", "cost_optimization"],
                ),
            },
            performance=PerformanceSettings(
                max_response_time=20.0,
                target_response_time=3.0,
                max_concurrent_requests=20,
            ),
            capabilities=[
                "shipping_optimization",
                "inventory_management",
                "package_tracking",
                "carrier_selection",
                "cost_optimization",
                "delivery_scheduling",
            ],
            model_settings={
                "temperature": 0.3,
                "max_tokens": 1500,
                "top_p": 0.8,
                "frequency_penalty": 0.0,
            },
        )

        # Executive UnifiedAgent Configuration
        executive_config = UnifiedAgentConfiguration(
            agent_type=UnifiedAgentType.EXECUTIVE,
            approval_thresholds={
                RequestType.STRATEGIC.value: ApprovalThresholds(
                    auto_approve=0.7,
                    requires_human=0.5,
                    escalation=0.3,
                    requires_human_approval=["strategic_decisions", "policy_changes"],
                ),
                RequestType.FINANCIAL.value: ApprovalThresholds(
                    auto_approve=0.75,
                    requires_human=0.55,
                    escalation=0.35,
                    requires_human_approval=["budget_changes", "investment_decisions"],
                ),
                RequestType.INVESTMENT.value: ApprovalThresholds(
                    auto_approve=0.8,
                    requires_human=0.6,
                    escalation=0.4,
                    requires_human_approval=["investment_decisions"],
                ),
                RequestType.RESOURCE.value: ApprovalThresholds(
                    auto_approve=0.85, requires_human=0.65, escalation=0.45
                ),
            },
            performance=PerformanceSettings(
                max_response_time=360.0,  # extended for complex gemma3:4b processing (6 minutes)
                target_response_time=90.0,  # extended for gemma3:4b
                max_concurrent_requests=8,
                timeout_duration=420.0,  # extended for complex gemma3:4b processing (7 minutes)
            ),
            capabilities=[
                "strategic_planning",
                "financial_analysis",
                "investment_evaluation",
                "resource_allocation",
                "risk_assessment",
                "performance_analysis",
                "decision_support",
            ],
            model_settings={
                "temperature": 0.5,
                "max_tokens": 3000,
                "top_p": 0.85,
                "frequency_penalty": 0.2,
            },
        )

        # Market UnifiedAgent Configuration
        market_config = UnifiedAgentConfiguration(
            agent_type=UnifiedAgentType.MARKET,
            approval_thresholds={
                "analysis": ApprovalThresholds(auto_approve=0.8, requires_human=0.6),
                "pricing": ApprovalThresholds(auto_approve=0.75, requires_human=0.55),
                "competition": ApprovalThresholds(
                    auto_approve=0.85, requires_human=0.65
                ),
            },
            capabilities=[
                "market_analysis",
                "competitor_research",
                "pricing_optimization",
                "trend_analysis",
            ],
        )

        # Analytics UnifiedAgent Configuration
        analytics_config = UnifiedAgentConfiguration(
            agent_type=UnifiedAgentType.ANALYTICS,
            approval_thresholds={
                "reporting": ApprovalThresholds(auto_approve=0.9, requires_human=0.7),
                "forecasting": ApprovalThresholds(auto_approve=0.8, requires_human=0.6),
            },
            capabilities=[
                "data_analysis",
                "reporting",
                "forecasting",
                "metrics_tracking",
            ],
        )

        # Assistant UnifiedAgent Configuration
        assistant_config = UnifiedAgentConfiguration(
            agent_type=UnifiedAgentType.ASSISTANT,
            approval_thresholds={
                "general": ApprovalThresholds(auto_approve=0.85, requires_human=0.6)
            },
            capabilities=[
                "general_assistance",
                "information_retrieval",
                "task_coordination",
            ],
        )

        # Store configurations
        self._configurations = {
            UnifiedAgentType.CONTENT: content_config,
            UnifiedAgentType.LOGISTICS: logistics_config,
            UnifiedAgentType.EXECUTIVE: executive_config,
            UnifiedAgentType.MARKET: market_config,
            UnifiedAgentType.ANALYTICS: analytics_config,
            UnifiedAgentType.ASSISTANT: assistant_config,
        }

    def _load_environment_overrides(self):
        """Load configuration overrides from environment variables."""
        try:
            # Global overrides
            if os.getenv("AGENT_AUTO_APPROVE_THRESHOLD"):
                threshold = float(os.getenv("AGENT_AUTO_APPROVE_THRESHOLD"))
                for config in self._configurations.values():
                    for approval_config in config.approval_thresholds.values():
                        approval_config.auto_approve = threshold

            if os.getenv("AGENT_MAX_RESPONSE_TIME"):
                max_time = float(os.getenv("AGENT_MAX_RESPONSE_TIME"))
                for config in self._configurations.values():
                    config.performance.max_response_time = max_time

            # UnifiedAgent-specific overrides
            for agent_type in UnifiedAgentType:
                prefix = f"AGENT_{agent_type.value.upper()}_"

                # Performance overrides
                if os.getenv(f"{prefix}MAX_RESPONSE_TIME"):
                    self._configurations[agent_type].performance.max_response_time = (
                        float(os.getenv(f"{prefix}MAX_RESPONSE_TIME"))
                    )

                if os.getenv(f"{prefix}MAX_CONCURRENT"):
                    self._configurations[
                        agent_type
                    ].performance.max_concurrent_requests = int(
                        os.getenv(f"{prefix}MAX_CONCURRENT")
                    )

                # Enable/disable agents
                if os.getenv(f"{prefix}ENABLED"):
                    self._configurations[agent_type].enabled = (
                        os.getenv(f"{prefix}ENABLED").lower() == "true"
                    )

        except Exception as e:
            logger.warning(f"Error loading environment overrides: {e}")

    def get_agent_config(self, agent_type: Union[UnifiedAgentType, str]) -> UnifiedAgentConfiguration:
        """Get configuration for a specific agent type."""
        if isinstance(agent_type, str):
            agent_type = UnifiedAgentType(agent_type)

        return self._configurations.get(
            agent_type, self._configurations[UnifiedAgentType.ASSISTANT]
        )

    def get_approval_thresholds(
        self, agent_type: Union[UnifiedAgentType, str], request_type: str
    ) -> ApprovalThresholds:
        """Get approval thresholds for a specific agent and request type."""
        config = self.get_agent_config(agent_type)
        return config.approval_thresholds.get(
            request_type, ApprovalThresholds()  # Default thresholds
        )

    def get_performance_settings(
        self, agent_type: Union[UnifiedAgentType, str]
    ) -> PerformanceSettings:
        """Get performance settings for a specific agent type."""
        config = self.get_agent_config(agent_type)
        return config.performance

    def is_agent_enabled(self, agent_type: Union[UnifiedAgentType, str]) -> bool:
        """Check if an agent type is enabled."""
        config = self.get_agent_config(agent_type)
        return config.enabled

    def get_agent_capabilities(self, agent_type: Union[UnifiedAgentType, str]) -> List[str]:
        """Get capabilities for a specific agent type."""
        config = self.get_agent_config(agent_type)
        return config.capabilities

    def get_model_settings(self, agent_type: Union[UnifiedAgentType, str]) -> Dict[str, Any]:
        """Get model settings for a specific agent type."""
        config = self.get_agent_config(agent_type)
        return config.model_settings

    def update_agent_config(self, agent_type: Union[UnifiedAgentType, str], **kwargs) -> None:
        """Update configuration for a specific agent type."""
        if isinstance(agent_type, str):
            agent_type = UnifiedAgentType(agent_type)

        config = self._configurations.get(agent_type)
        if config:
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)

    def get_all_configurations(self) -> Dict[UnifiedAgentType, UnifiedAgentConfiguration]:
        """Get all agent configurations."""
        return self._configurations.copy()


# Global settings manager instance
_global_settings_manager = None


def get_agent_settings() -> UnifiedAgentSettingsManager:
    """Get or create global agent settings manager."""
    global _global_settings_manager
    if _global_settings_manager is None:
        _global_settings_manager = UnifiedAgentSettingsManager()
    return _global_settings_manager


# Convenience functions
def get_approval_thresholds(agent_type: str, request_type: str) -> ApprovalThresholds:
    """Convenience function to get approval thresholds."""
    return get_agent_settings().get_approval_thresholds(agent_type, request_type)


def get_performance_settings(agent_type: str) -> PerformanceSettings:
    """Convenience function to get performance settings."""
    return get_agent_settings().get_performance_settings(agent_type)


def is_agent_enabled(agent_type: str) -> bool:
    """Convenience function to check if agent is enabled."""
    return get_agent_settings().is_agent_enabled(agent_type)


def get_agent_capabilities(agent_type: str) -> List[str]:
    """Convenience function to get agent capabilities."""
    return get_agent_settings().get_agent_capabilities(agent_type)
