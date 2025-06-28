"""
FlipSync Health Protocol

This module defines the protocols and interfaces for health checking, status reporting,
and dependency health monitoring within the FlipSync monitoring system.

This is part of the Phase 6 Monitoring Systems Consolidation effort.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union

from .monitoring_protocol import ComponentType, MonitoringStatus


class HealthStatus(Enum):
    """Health status values for components."""

    HEALTHY = "healthy"  # Completely healthy
    DEGRADED = "degraded"  # Functioning but with issues
    UNHEALTHY = "unhealthy"  # Not functioning properly
    CRITICAL = "critical"  # In critical condition, severe issues
    UNKNOWN = "unknown"  # Status cannot be determined


class HealthImpact(Enum):
    """Impact levels for health issues."""

    NONE = "none"  # No impact on system
    LOW = "low"  # Minor impact, not affecting users
    MEDIUM = "medium"  # Moderate impact, affecting some users
    HIGH = "high"  # Significant impact, affecting many users
    CRITICAL = "critical"  # Severe impact, system unusable


class HealthCheckResult:
    """Result of a health check."""

    def __init__(
        self,
        check_id: str,
        component_id: str,
        status: HealthStatus,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        impact: HealthImpact = HealthImpact.NONE,
        metrics: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
    ):
        self.check_id = check_id
        self.component_id = component_id
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = timestamp or datetime.utcnow()
        self.impact = impact
        self.metrics = metrics or {}
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        """Convert the health check result to a dictionary."""
        return {
            "check_id": self.check_id,
            "component_id": self.component_id,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "impact": self.impact.value,
            "metrics": self.metrics,
            "duration_ms": self.duration_ms,
        }


class HealthCheck:
    """Defines a health check for a component."""

    def __init__(
        self,
        check_id: Optional[str] = None,
        name: str = "",
        description: Optional[str] = None,
        component_id: str = "",
        enabled: bool = True,
        interval: timedelta = timedelta(minutes=1),
        timeout: timedelta = timedelta(seconds=10),
        critical: bool = False,
        dependencies: Optional[List[str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.check_id = check_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.component_id = component_id
        self.enabled = enabled
        self.interval = interval
        self.timeout = timeout
        self.critical = critical
        self.dependencies = dependencies or []
        self.labels = labels or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the health check to a dictionary."""
        return {
            "check_id": self.check_id,
            "name": self.name,
            "description": self.description,
            "component_id": self.component_id,
            "enabled": self.enabled,
            "interval": self.interval.total_seconds(),
            "timeout": self.timeout.total_seconds(),
            "critical": self.critical,
            "dependencies": self.dependencies,
            "labels": self.labels,
        }


class HealthDependency:
    """Represents a dependency relationship between components."""

    def __init__(
        self,
        source_id: str,
        target_id: str,
        dependency_type: str = "required",
        impact: HealthImpact = HealthImpact.HIGH,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.dependency_type = dependency_type
        self.impact = impact
        self.description = description
        self.labels = labels or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the health dependency to a dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "dependency_type": self.dependency_type,
            "impact": self.impact.value,
            "description": self.description,
            "labels": self.labels,
        }


class HealthProtocol(ABC):
    """Core protocol for health checking functionality."""

    @abstractmethod
    def register_health_check(self, health_check: HealthCheck) -> str:
        """
        Register a new health check.

        Returns:
            str: Check ID
        """
        pass

    @abstractmethod
    def unregister_health_check(self, check_id: str) -> None:
        """Unregister a health check."""
        pass

    @abstractmethod
    def get_health_check(self, check_id: str) -> Optional[HealthCheck]:
        """Get a health check by ID."""
        pass

    @abstractmethod
    def get_health_checks(
        self,
        component_id: Optional[str] = None,
        enabled_only: bool = True,
        critical_only: bool = False,
    ) -> List[HealthCheck]:
        """Get health checks based on criteria."""
        pass

    @abstractmethod
    def execute_health_check(self, check_id: str) -> HealthCheckResult:
        """Execute a specific health check and return the result."""
        pass

    @abstractmethod
    def get_health_status(
        self,
        component_id: Optional[str] = None,
        include_dependencies: bool = True,
        include_details: bool = False,
    ) -> Dict[str, Any]:
        """Get health status for a component or the entire system."""
        pass

    @abstractmethod
    def register_dependency(
        self,
        source_id: str,
        target_id: str,
        dependency_type: str = "required",
        impact: HealthImpact = HealthImpact.HIGH,
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Register a dependency between components."""
        pass

    @abstractmethod
    def unregister_dependency(self, source_id: str, target_id: str) -> None:
        """Unregister a dependency between components."""
        pass

    @abstractmethod
    def get_dependencies(
        self,
        component_id: str,
        recursive: bool = False,
        dependency_type: Optional[str] = None,
    ) -> List[HealthDependency]:
        """Get dependencies for a component."""
        pass

    @abstractmethod
    def get_dependents(
        self,
        component_id: str,
        recursive: bool = False,
        dependency_type: Optional[str] = None,
    ) -> List[HealthDependency]:
        """Get components that depend on the specified component."""
        pass


class HealthChecker(ABC):
    """Protocol for health checkers that perform health checks."""

    @property
    @abstractmethod
    def checker_id(self) -> str:
        """Unique identifier for this checker."""
        pass

    @property
    @abstractmethod
    def checker_name(self) -> str:
        """Human-readable name for this checker."""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the checker with configuration."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shutdown the checker."""
        pass

    @abstractmethod
    def check_health(
        self, component_id: str, check_id: str, timeout: Optional[timedelta] = None
    ) -> HealthCheckResult:
        """
        Perform a health check on a component.

        Returns:
            HealthCheckResult: The result of the health check
        """
        pass

    @abstractmethod
    def get_supported_component_types(self) -> List[ComponentType]:
        """Get the component types supported by this checker."""
        pass


class HealthReporter(ABC):
    """Protocol for health reporters that aggregate and report health information."""

    @property
    @abstractmethod
    def reporter_id(self) -> str:
        """Unique identifier for this reporter."""
        pass

    @property
    @abstractmethod
    def reporter_name(self) -> str:
        """Human-readable name for this reporter."""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the reporter with configuration."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shutdown the reporter."""
        pass

    @abstractmethod
    def report_health(
        self,
        component_id: Optional[str] = None,
        include_dependencies: bool = True,
        include_details: bool = False,
    ) -> Dict[str, Any]:
        """Generate a health report for a component or the entire system."""
        pass

    @abstractmethod
    def get_historical_health(
        self,
        component_id: str,
        from_time: datetime,
        to_time: Optional[datetime] = None,
        interval: Optional[timedelta] = None,
    ) -> List[Dict[str, Any]]:
        """Get historical health information for a component."""
        pass
