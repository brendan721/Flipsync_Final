"""Configuration management package."""

from .agent_settings import (
    AutonomousAgentSettingsManager,
    AutonomousAgentType,
    ApprovalThresholds,
    PerformanceSettings,
    RequestType,
    get_agent_capabilities,
    get_agent_settings,
    get_approval_thresholds,
    get_performance_settings,
    is_agent_enabled,
)
from .config_manager import ConfigManager

_config_instance = None


def get_settings():
    """Get the global settings instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager("config")
    return _config_instance


__all__ = [
    "ConfigManager",
    "get_settings",
    "AutonomousAgentSettingsManager",
    "AutonomousAgentType",
    "RequestType",
    "ApprovalThresholds",
    "PerformanceSettings",
    "get_agent_settings",
    "get_approval_thresholds",
    "get_performance_settings",
    "is_agent_enabled",
    "get_agent_capabilities",
]
