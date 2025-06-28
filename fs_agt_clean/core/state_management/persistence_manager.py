"""
Persistence Manager Module

This module provides functionality for persisting agent state across system restarts.
It handles saving, loading, and managing agent state data.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PersistenceManager:
    """
    Manages persistence of agent state across system restarts.

    This class provides functionality to save and load agent state data,
    ensuring that agents can recover their state after a system restart.
    """

    def __init__(self, storage_path: str = None):
        """
        Initialize the persistence manager.

        Args:
            storage_path: Path to the directory where state data will be stored.
                          If None, a default path will be used.
        """
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "agent_state",
        )

        # Create the storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(
            f"Persistence manager initialized with storage path: {self.storage_path}"
        )

    async def save_state(self, agent_id: str, state: Dict[str, Any]) -> bool:
        """
        Save agent state to storage.

        Args:
            agent_id: Unique identifier for the agent
            state: Dictionary containing the agent's state data

        Returns:
            True if the state was saved successfully, False otherwise
        """
        if not agent_id or not isinstance(state, dict):
            logger.error(f"Invalid agent_id or state: {agent_id}, {type(state)}")
            return False

        # Add metadata to the state
        state_with_metadata = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "state": state,
        }

        file_path = os.path.join(self.storage_path, f"{agent_id}.json")

        try:
            async with self._lock:
                # Create a temporary file first to avoid corruption if the process crashes
                temp_file_path = f"{file_path}.tmp"
                with open(temp_file_path, "w") as f:
                    json.dump(state_with_metadata, f, indent=2)

                # Rename the temporary file to the actual file
                os.replace(temp_file_path, file_path)

            logger.info(f"State saved for agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving state for agent {agent_id}: {e}")
            return False

    async def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Load agent state from storage.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Dictionary containing the agent's state data, or None if not found
        """
        if not agent_id:
            logger.error(f"Invalid agent_id: {agent_id}")
            return None

        file_path = os.path.join(self.storage_path, f"{agent_id}.json")

        try:
            if not os.path.exists(file_path):
                logger.warning(f"No state file found for agent: {agent_id}")
                return None

            async with self._lock:
                with open(file_path, "r") as f:
                    state_with_metadata = json.load(f)

            # Extract the actual state data
            state = state_with_metadata.get("state", {})

            logger.info(f"State loaded for agent: {agent_id}")
            return state
        except Exception as e:
            logger.error(f"Error loading state for agent {agent_id}: {e}")
            return None

    async def delete_state(self, agent_id: str) -> bool:
        """
        Delete agent state from storage.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            True if the state was deleted successfully, False otherwise
        """
        if not agent_id:
            logger.error(f"Invalid agent_id: {agent_id}")
            return False

        file_path = os.path.join(self.storage_path, f"{agent_id}.json")

        try:
            if not os.path.exists(file_path):
                logger.warning(f"No state file found for agent: {agent_id}")
                return False

            async with self._lock:
                os.remove(file_path)

            logger.info(f"State deleted for agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting state for agent {agent_id}: {e}")
            return False

    async def list_agents(self) -> List[str]:
        """
        List all agents with saved state.

        Returns:
            List of agent IDs with saved state
        """
        try:
            agent_ids = []

            async with self._lock:
                for filename in os.listdir(self.storage_path):
                    if filename.endswith(".json"):
                        agent_id = filename[:-5]  # Remove the .json extension
                        agent_ids.append(agent_id)

            return agent_ids
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return []

    async def get_state_metadata(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an agent's state.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Dictionary containing metadata about the agent's state, or None if not found
        """
        if not agent_id:
            logger.error(f"Invalid agent_id: {agent_id}")
            return None

        file_path = os.path.join(self.storage_path, f"{agent_id}.json")

        try:
            if not os.path.exists(file_path):
                logger.warning(f"No state file found for agent: {agent_id}")
                return None

            async with self._lock:
                with open(file_path, "r") as f:
                    state_with_metadata = json.load(f)

            # Extract metadata
            metadata = {
                "agent_id": state_with_metadata.get("agent_id"),
                "timestamp": state_with_metadata.get("timestamp"),
                "size": os.path.getsize(file_path),
            }

            return metadata
        except Exception as e:
            logger.error(f"Error getting metadata for agent {agent_id}: {e}")
            return None

    async def clear_all_states(self) -> bool:
        """
        Clear all agent states from storage.

        Returns:
            True if all states were cleared successfully, False otherwise
        """
        try:
            agent_ids = await self.list_agents()

            for agent_id in agent_ids:
                await self.delete_state(agent_id)

            logger.info(f"Cleared all agent states ({len(agent_ids)} agents)")
            return True
        except Exception as e:
            logger.error(f"Error clearing all agent states: {e}")
            return False
