"""UnifiedAgent Coordinator module for FlipSync.

This module provides the UnifiedAgentCoordinator class which is the main entry point
for agent coordination functionality. It wraps the core coordinator interfaces
and provides a simplified API for agent management.
"""

import logging
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.coordination.coordinator.coordinator import (
    UnifiedAgentCapability,
    UnifiedAgentInfo,
    UnifiedAgentStatus,
    UnifiedAgentType,
    Coordinator,
)
from fs_agt_clean.core.coordination.coordinator.in_memory_coordinator import (
    InMemoryCoordinator,
)

logger = logging.getLogger(__name__)


class UnifiedAgentCoordinator:
    """
    Main agent coordinator class for FlipSync.

    This class provides a simplified interface for agent coordination,
    wrapping the core coordinator functionality.
    """

    def __init__(self, coordinator: Optional[Coordinator] = None):
        """
        Initialize the agent coordinator.

        Args:
            coordinator: Optional coordinator instance. If None, uses InMemoryCoordinator.
        """
        self.coordinator = coordinator or InMemoryCoordinator()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def initialize(self) -> None:
        """Initialize the coordinator."""
        try:
            if hasattr(self.coordinator, "initialize"):
                await self.coordinator.initialize()
            self.logger.info("UnifiedAgent coordinator initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize agent coordinator: {e}")
            raise

    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        name: str,
        description: str = "",
        capabilities: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register an agent with the coordinator.

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of the agent (executive, specialist, utility, mobile, system)
            name: Human-readable name for the agent
            description: Description of the agent
            capabilities: List of capabilities the agent provides
            metadata: Additional metadata for the agent

        Returns:
            True if registration was successful
        """
        try:
            # Convert string agent_type to UnifiedAgentType enum
            agent_type_enum = UnifiedAgentType(agent_type.lower())

            # Convert capabilities dictionaries to UnifiedAgentCapability objects
            agent_capabilities = []
            if capabilities:
                for cap_dict in capabilities:
                    capability = UnifiedAgentCapability.from_dict(cap_dict)
                    agent_capabilities.append(capability)

            # Create UnifiedAgentInfo object
            agent_info = UnifiedAgentInfo(
                agent_id=agent_id,
                agent_type=agent_type_enum,
                name=name,
                description=description,
                capabilities=agent_capabilities,
                status=UnifiedAgentStatus.ACTIVE,
                metadata=metadata or {},
            )

            # Register with the coordinator
            result = await self.coordinator.register_agent(agent_info)

            if result:
                self.logger.info(f"Successfully registered agent {agent_id} ({name})")
            else:
                self.logger.warning(f"Failed to register agent {agent_id} ({name})")

            return result

        except Exception as e:
            self.logger.error(f"Error registering agent {agent_id}: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the coordinator.

        Args:
            agent_id: ID of the agent to unregister

        Returns:
            True if unregistration was successful
        """
        try:
            result = await self.coordinator.unregister_agent(agent_id)

            if result:
                self.logger.info(f"Successfully unregistered agent {agent_id}")
            else:
                self.logger.warning(f"Failed to unregister agent {agent_id}")

            return result

        except Exception as e:
            self.logger.error(f"Error unregistering agent {agent_id}: {e}")
            return False

    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            UnifiedAgent information as a dictionary, or None if not found
        """
        try:
            agent_info = await self.coordinator.get_agent_info(agent_id)

            if agent_info:
                return agent_info.to_dict()
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error getting agent info for {agent_id}: {e}")
            return None

    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """
        Get all registered agents.

        Returns:
            List of all agents as dictionaries
        """
        try:
            agents = await self.coordinator.get_all_agents()
            return [agent.to_dict() for agent in agents]

        except Exception as e:
            self.logger.error(f"Error getting all agents: {e}")
            return []

    async def find_agents_by_type(self, agent_type: str) -> List[Dict[str, Any]]:
        """
        Find agents by type.

        Args:
            agent_type: Type of agents to find

        Returns:
            List of matching agents as dictionaries
        """
        try:
            agent_type_enum = UnifiedAgentType(agent_type.lower())
            agents = await self.coordinator.find_agents_by_type(agent_type_enum)
            return [agent.to_dict() for agent in agents]

        except Exception as e:
            self.logger.error(f"Error finding agents by type {agent_type}: {e}")
            return []

    async def update_agent_status(self, agent_id: str, status: str) -> bool:
        """
        Update an agent's status.

        Args:
            agent_id: ID of the agent
            status: New status of the agent

        Returns:
            True if the update was successful
        """
        try:
            status_enum = UnifiedAgentStatus(status.lower())
            result = await self.coordinator.update_agent_status(agent_id, status_enum)

            if result:
                self.logger.debug(f"Updated agent {agent_id} status to {status}")
            else:
                self.logger.warning(
                    f"Failed to update agent {agent_id} status to {status}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error updating agent {agent_id} status: {e}")
            return False

    async def check_agent_health(self, agent_id: str) -> bool:
        """
        Check if an agent is healthy.

        Args:
            agent_id: ID of the agent

        Returns:
            True if the agent is healthy
        """
        try:
            return await self.coordinator.check_agent_health(agent_id)

        except Exception as e:
            self.logger.error(f"Error checking agent {agent_id} health: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the coordinator."""
        try:
            if hasattr(self.coordinator, "shutdown"):
                await self.coordinator.shutdown()
            self.logger.info("UnifiedAgent coordinator shutdown successfully")
        except Exception as e:
            self.logger.error(f"Error shutting down agent coordinator: {e}")


# Export the main class for easy importing
__all__ = ["UnifiedAgentCoordinator"]
