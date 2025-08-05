"""
Unified Performance Configuration for FlipSync Agentic System
===========================================================

Standardizes performance targets across all system components to meet
Docker-aware <1000ms decision time requirements.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PerformanceTarget(str, Enum):
    """Standardized performance targets for different system components."""
    
    # Core decision pipeline targets (Docker-aware)
    AGENT_DECISION = "agent_decision"  # 500ms base + 500ms Docker overhead = 1000ms
    SERVICE_EXECUTION = "service_execution"  # 200ms base + 300ms Docker overhead = 500ms
    DATABASE_QUERY = "database_query"  # 50ms base + 50ms Docker overhead = 100ms
    CACHE_ACCESS = "cache_access"  # 10ms base + 40ms Docker overhead = 50ms
    
    # Integration targets
    WEBSOCKET_MESSAGE = "websocket_message"  # 100ms total
    API_RESPONSE = "api_response"  # 800ms total
    AUTHENTICATION = "authentication"  # 200ms total
    
    # Service-specific targets
    PRICING_SERVICE = "pricing_service"  # 200ms
    FORECASTING_SERVICE = "forecasting_service"  # 300ms
    CONTENT_GENERATION = "content_generation"  # 250ms
    ROUTE_OPTIMIZATION = "route_optimization"  # 500ms


@dataclass
class PerformanceConfiguration:
    """Performance configuration for system components."""
    
    target_ms: int
    warning_threshold_ms: int
    error_threshold_ms: int
    timeout_ms: int
    description: str
    docker_overhead_ms: Optional[int] = None


class UnifiedPerformanceConfig:
    """Unified performance configuration manager."""
    
    def __init__(self):
        self.configurations = self._initialize_configurations()
        logger.info("Unified performance configuration initialized")
    
    def _initialize_configurations(self) -> Dict[PerformanceTarget, PerformanceConfiguration]:
        """Initialize all performance configurations."""
        return {
            # Core agent decision pipeline
            PerformanceTarget.AGENT_DECISION: PerformanceConfiguration(
                target_ms=1000,
                warning_threshold_ms=800,
                error_threshold_ms=1200,
                timeout_ms=2000,
                description="Agent decision processing with Docker overhead",
                docker_overhead_ms=500
            ),
            
            # Service execution
            PerformanceTarget.SERVICE_EXECUTION: PerformanceConfiguration(
                target_ms=500,
                warning_threshold_ms=400,
                error_threshold_ms=600,
                timeout_ms=1000,
                description="Service tool execution with Docker overhead",
                docker_overhead_ms=300
            ),
            
            # Database operations
            PerformanceTarget.DATABASE_QUERY: PerformanceConfiguration(
                target_ms=100,
                warning_threshold_ms=80,
                error_threshold_ms=150,
                timeout_ms=300,
                description="Database query execution with Docker overhead",
                docker_overhead_ms=50
            ),
            
            # Cache operations
            PerformanceTarget.CACHE_ACCESS: PerformanceConfiguration(
                target_ms=50,
                warning_threshold_ms=30,
                error_threshold_ms=80,
                timeout_ms=200,
                description="Redis cache access with Docker overhead",
                docker_overhead_ms=40
            ),
            
            # WebSocket communication
            PerformanceTarget.WEBSOCKET_MESSAGE: PerformanceConfiguration(
                target_ms=100,
                warning_threshold_ms=80,
                error_threshold_ms=150,
                timeout_ms=500,
                description="WebSocket message processing",
                docker_overhead_ms=None
            ),
            
            # API responses
            PerformanceTarget.API_RESPONSE: PerformanceConfiguration(
                target_ms=800,
                warning_threshold_ms=600,
                error_threshold_ms=1000,
                timeout_ms=2000,
                description="API endpoint response time",
                docker_overhead_ms=None
            ),
            
            # Authentication
            PerformanceTarget.AUTHENTICATION: PerformanceConfiguration(
                target_ms=200,
                warning_threshold_ms=150,
                error_threshold_ms=300,
                timeout_ms=1000,
                description="Authentication and authorization",
                docker_overhead_ms=None
            ),
            
            # Service-specific configurations
            PerformanceTarget.PRICING_SERVICE: PerformanceConfiguration(
                target_ms=200,
                warning_threshold_ms=150,
                error_threshold_ms=250,
                timeout_ms=500,
                description="Algorithmic pricing service execution",
                docker_overhead_ms=None
            ),
            
            PerformanceTarget.FORECASTING_SERVICE: PerformanceConfiguration(
                target_ms=300,
                warning_threshold_ms=250,
                error_threshold_ms=400,
                timeout_ms=800,
                description="Bayesian forecasting service execution",
                docker_overhead_ms=None
            ),
            
            PerformanceTarget.CONTENT_GENERATION: PerformanceConfiguration(
                target_ms=250,
                warning_threshold_ms=200,
                error_threshold_ms=350,
                timeout_ms=600,
                description="Template-based content generation",
                docker_overhead_ms=None
            ),
            
            PerformanceTarget.ROUTE_OPTIMIZATION: PerformanceConfiguration(
                target_ms=500,
                warning_threshold_ms=400,
                error_threshold_ms=700,
                timeout_ms=1200,
                description="Graph algorithm route optimization",
                docker_overhead_ms=None
            )
        }
    
    def get_configuration(self, target: PerformanceTarget) -> PerformanceConfiguration:
        """Get performance configuration for a specific target."""
        return self.configurations.get(target)
    
    def get_target_ms(self, target: PerformanceTarget) -> int:
        """Get target milliseconds for a performance target."""
        config = self.get_configuration(target)
        return config.target_ms if config else 1000  # Default fallback
    
    def get_timeout_ms(self, target: PerformanceTarget) -> int:
        """Get timeout milliseconds for a performance target."""
        config = self.get_configuration(target)
        return config.timeout_ms if config else 2000  # Default fallback
    
    def is_within_target(self, target: PerformanceTarget, actual_ms: float) -> bool:
        """Check if actual performance is within target."""
        config = self.get_configuration(target)
        if not config:
            return True  # No config means no constraint
        return actual_ms <= config.target_ms
    
    def is_warning_level(self, target: PerformanceTarget, actual_ms: float) -> bool:
        """Check if actual performance is at warning level."""
        config = self.get_configuration(target)
        if not config:
            return False
        return config.warning_threshold_ms < actual_ms <= config.target_ms
    
    def is_error_level(self, target: PerformanceTarget, actual_ms: float) -> bool:
        """Check if actual performance is at error level."""
        config = self.get_configuration(target)
        if not config:
            return False
        return actual_ms > config.error_threshold_ms
    
    def get_performance_status(self, target: PerformanceTarget, actual_ms: float) -> Dict[str, Any]:
        """Get comprehensive performance status for a target."""
        config = self.get_configuration(target)
        if not config:
            return {
                "status": "unknown",
                "actual_ms": actual_ms,
                "message": f"No configuration found for {target}"
            }
        
        if actual_ms <= config.warning_threshold_ms:
            status = "excellent"
        elif actual_ms <= config.target_ms:
            status = "good"
        elif actual_ms <= config.error_threshold_ms:
            status = "warning"
        else:
            status = "error"
        
        return {
            "status": status,
            "actual_ms": actual_ms,
            "target_ms": config.target_ms,
            "warning_threshold_ms": config.warning_threshold_ms,
            "error_threshold_ms": config.error_threshold_ms,
            "within_target": self.is_within_target(target, actual_ms),
            "description": config.description,
            "docker_overhead_ms": config.docker_overhead_ms
        }
    
    def get_all_targets(self) -> Dict[str, Dict[str, Any]]:
        """Get all performance targets and their configurations."""
        return {
            target.value: {
                "target_ms": config.target_ms,
                "warning_threshold_ms": config.warning_threshold_ms,
                "error_threshold_ms": config.error_threshold_ms,
                "timeout_ms": config.timeout_ms,
                "description": config.description,
                "docker_overhead_ms": config.docker_overhead_ms
            }
            for target, config in self.configurations.items()
        }


# Global performance configuration instance
_performance_config: Optional[UnifiedPerformanceConfig] = None


def get_performance_config() -> UnifiedPerformanceConfig:
    """Get the global performance configuration instance."""
    global _performance_config
    if _performance_config is None:
        _performance_config = UnifiedPerformanceConfig()
    return _performance_config


# Convenience functions for common performance checks
def check_agent_decision_performance(actual_ms: float) -> Dict[str, Any]:
    """Check agent decision performance against targets."""
    return get_performance_config().get_performance_status(
        PerformanceTarget.AGENT_DECISION, actual_ms
    )


def check_service_execution_performance(actual_ms: float) -> Dict[str, Any]:
    """Check service execution performance against targets."""
    return get_performance_config().get_performance_status(
        PerformanceTarget.SERVICE_EXECUTION, actual_ms
    )


def get_agent_decision_timeout() -> int:
    """Get timeout for agent decisions."""
    return get_performance_config().get_timeout_ms(PerformanceTarget.AGENT_DECISION)


def get_service_execution_timeout() -> int:
    """Get timeout for service execution."""
    return get_performance_config().get_timeout_ms(PerformanceTarget.SERVICE_EXECUTION)
