"""
FlipSync Monitoring Protocol

This module defines the core protocols and interfaces for the unified monitoring system.
All monitoring components should implement or extend these protocols for consistency.

This is part of the Phase 6 Monitoring Systems Consolidation effort.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union


class MonitoringStatus(Enum):
    """Status values for monitoring components."""

    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    FAILING = "failing"
    STOPPED = "stopped"
    UNKNOWN = "unknown"


class MonitoringLevel(Enum):
    """Log and alert levels for the monitoring system."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class ComponentType(Enum):
    """Types of components that can be monitored."""

    SERVICE = "service"
    AGENT = "agent"
    DATABASE = "database"
    API = "api"
    NETWORK = "network"
    SYSTEM = "system"
    CUSTOM = "custom"


T = TypeVar("T", bound="MonitorableComponent")


class MonitorableComponent(ABC):
    """Protocol that all monitorable components must implement."""

    @property
    @abstractmethod
    def component_id(self) -> str:
        """Unique identifier for this component."""
        pass

    @property
    @abstractmethod
    def component_name(self) -> str:
        """Human-readable name for this component."""
        pass

    @property
    @abstractmethod
    def component_type(self) -> ComponentType:
        """The type of this component."""
        pass

    @property
    @abstractmethod
    def status(self) -> MonitoringStatus:
        """Current status of this component."""
        pass

    @abstractmethod
    def get_health(self) -> Dict[str, Any]:
        """Get detailed health information for this component."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metric values for this component."""
        pass

    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get IDs of components this component depends on."""
        pass


class MonitoringProtocol(ABC):
    """Core protocol for the monitoring system."""

    @abstractmethod
    def register_component(self, component: MonitorableComponent) -> None:
        """Register a component for monitoring."""
        pass

    @abstractmethod
    def unregister_component(self, component_id: str) -> None:
        """Unregister a component from monitoring."""
        pass

    @abstractmethod
    def get_component(self, component_id: str) -> Optional[MonitorableComponent]:
        """Get a registered component by ID."""
        pass

    @abstractmethod
    def get_all_components(self) -> List[MonitorableComponent]:
        """Get all registered components."""
        pass

    @abstractmethod
    def get_components_by_type(
        self, component_type: ComponentType
    ) -> List[MonitorableComponent]:
        """Get all components of a specific type."""
        pass

    @abstractmethod
    def get_component_metrics(self, component_id: str) -> Dict[str, Any]:
        """Get metrics for a specific component."""
        pass

    @abstractmethod
    def get_component_health(self, component_id: str) -> Dict[str, Any]:
        """Get health information for a specific component."""
        pass

    @abstractmethod
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        pass

    @abstractmethod
    def get_component_dependencies(self, component_id: str) -> Dict[str, Any]:
        """Get dependency information for a component."""
        pass

    @abstractmethod
    def register_backend(self, backend: "MonitoringBackend") -> None:
        """Register a monitoring backend."""
        pass

    @abstractmethod
    def unregister_backend(self, backend_id: str) -> None:
        """Unregister a monitoring backend."""
        pass

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the monitoring system."""
        pass


class MonitoringBackend(ABC):
    """Protocol for monitoring backends that store and process monitoring data."""

    @property
    @abstractmethod
    def backend_id(self) -> str:
        """Unique identifier for this backend."""
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable name for this backend."""
        pass

    @property
    @abstractmethod
    def status(self) -> MonitoringStatus:
        """Current status of this backend."""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the backend with configuration."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shutdown the backend."""
        pass

    @abstractmethod
    def store_metrics(self, component_id: str, metrics: Dict[str, Any]) -> None:
        """Store metrics for a component."""
        pass

    @abstractmethod
    def store_health(self, component_id: str, health: Dict[str, Any]) -> None:
        """Store health information for a component."""
        pass

    @abstractmethod
    def query_metrics(
        self, component_id: str, from_time: datetime, to_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Query metrics for a component within a time range."""
        pass

    @abstractmethod
    def query_health(
        self, component_id: str, from_time: datetime, to_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Query health information for a component within a time range."""
        pass


class MonitoringPlugin(ABC):
    """Protocol for plugins that extend monitoring functionality."""

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """Unique identifier for this plugin."""
        pass

    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Human-readable name for this plugin."""
        pass

    @abstractmethod
    def initialize(
        self: MonitoringProtocol, config: Dict[str, Any]
    ) -> None:
        """Initialize the plugin with the monitoring system and configuration."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shutdown the plugin."""
        pass
