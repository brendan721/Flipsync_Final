"""
UnifiedAgent service base class for FlipSync.

This module provides the base class for all agent services,
defining the common interface and functionality.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.models.chat import UnifiedAgentResponse, ChatMessage, MessageIntent

logger = logging.getLogger(__name__)


class UnifiedAgentService(ABC):
    """
    Abstract base class for all agent services.

    This class defines the common interface that all agent services
    must implement to work with the agent connectivity system.
    """

    def __init__(self, agent_type: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent service.

        Args:
            agent_type: Type identifier for this agent
            config: Optional configuration dictionary
        """
        self.agent_type = agent_type
        self.config = config or {}
        self.initialized = False
        self.status = "initializing"
        self.last_activity = datetime.now()

        logger.info(f"Initializing {agent_type} agent service")

    @abstractmethod
    async def process_message(
        self,
        message: ChatMessage,
        intent: MessageIntent,
        conversation_history: Optional[List[ChatMessage]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> UnifiedAgentResponse:
        """
        Process a user message and generate a response.

        Args:
            message: The user message to process
            intent: The recognized intent of the message
            conversation_history: Optional conversation history
            context: Optional context information

        Returns:
            UnifiedAgent response
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent service.

        Returns:
            Dictionary containing status information
        """
        pass

    async def initialize(self) -> bool:
        """
        Initialize the agent service.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            await self._initialize_agent()
            self.initialized = True
            self.status = "ready"
            logger.info(f"{self.agent_type} agent service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_type} agent service: {e}")
            self.status = "error"
            return False

    async def _initialize_agent(self) -> None:
        """
        Perform agent-specific initialization.

        Override this method in subclasses to implement
        agent-specific initialization logic.
        """
        pass

    async def shutdown(self) -> None:
        """
        Shutdown the agent service.
        """
        try:
            await self._shutdown_agent()
            self.status = "shutdown"
            logger.info(f"{self.agent_type} agent service shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down {self.agent_type} agent service: {e}")

    async def _shutdown_agent(self) -> None:
        """
        Perform agent-specific shutdown.

        Override this method in subclasses to implement
        agent-specific shutdown logic.
        """
        pass

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()

    def get_capabilities(self) -> List[str]:
        """
        Get the capabilities of this agent.

        Returns:
            List of capability strings
        """
        return self.config.get("capabilities", [])

    def supports_intent(self, intent_type: str) -> bool:
        """
        Check if this agent supports a specific intent type.

        Args:
            intent_type: The intent type to check

        Returns:
            True if the agent supports this intent type
        """
        supported_intents = self.config.get("supported_intents", [])
        return intent_type in supported_intents

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)


# MockUnifiedAgentService removed - FlipSync uses only real OpenAI-powered agents in production
