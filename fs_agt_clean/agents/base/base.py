"""Base agent implementation for FlipSync."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.core.monitoring.types import HealthStatus


class BaseUnifiedAgent(ABC):
    """Base class for all FlipSync agents."""

    def __init__(
        self,
        agent_id: str,
        config_manager: Optional[ConfigManager] = None,
        alert_manager: Optional[AlertManager] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize base agent.

        Args:
            agent_id: Unique identifier for the agent
            config_manager: Configuration manager instance
            alert_manager: Alert manager instance
            **kwargs: Additional configuration options
        """
        self.agent_id = agent_id
        self.config_manager = config_manager
        self.alert_manager = alert_manager
        self.status = HealthStatus.UNKNOWN
        self.created_at = datetime.now(timezone.utc)
        self.last_active = self.created_at
        self._is_running = False
        self._initialize_from_kwargs(**kwargs)

    def _initialize_from_kwargs(self, **kwargs: Any) -> None:
        """Initialize additional attributes from kwargs."""
        for key, value in kwargs.items():
            setattr(self, f"_{key}", value)

    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> None:
        """Process incoming message.

        Args:
            message: The message to process
        """
        pass

    @abstractmethod
    async def take_action(self, action: Dict[str, Any]) -> None:
        """Take an action based on current state.

        Args:
            action: The action to take
        """
        pass

    async def start(self) -> None:
        """Start the agent."""
        self._is_running = True
        self.status = HealthStatus.STARTING
        await self._on_start()
        self.status = HealthStatus.RUNNING

    async def stop(self) -> None:
        """Stop the agent."""
        self._is_running = False
        self.status = HealthStatus.STOPPING
        await self._on_stop()
        self.status = HealthStatus.STOPPED

    async def _on_start(self) -> None:
        """Hook called when agent starts."""
        pass

    async def _on_stop(self) -> None:
        """Hook called when agent stops."""
        pass

    @property
    def is_running(self) -> bool:
        """Check if agent is running."""
        return self._is_running

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, status={self.status})"
