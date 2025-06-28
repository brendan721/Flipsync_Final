"""
Strategy UnifiedAgent for FlipSync executive decision making.

This agent provides strategic planning and coordination capabilities,
including strategy creation, optimization, and performance tracking.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from fs_agt_clean.agents.base.base import BaseUnifiedAgent

logger = logging.getLogger(__name__)


@dataclass
class Strategy:
    """Strategy model for decision making."""

    name: str
    description: str
    rules: Dict[str, Any]
    parameters: Dict[str, Any]
    tags: Set[str] = field(default_factory=set)
    strategy_id: UUID = field(default_factory=uuid4)
    performance: float = 0.5
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy to dictionary."""
        return {
            "strategy_id": str(self.strategy_id),
            "name": self.name,
            "description": self.description,
            "rules": self.rules,
            "parameters": self.parameters,
            "tags": list(self.tags),
            "performance": self.performance,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class StrategyUnifiedAgent(BaseUnifiedAgent):
    """
    Strategy UnifiedAgent for executive decision making.

    Provides strategic planning, coordination, and optimization capabilities
    for the FlipSync agent ecosystem.
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Strategy UnifiedAgent.

        Args:
            agent_id: Unique identifier for this agent instance
            config: Optional configuration dictionary
        """
        super().__init__(agent_id=agent_id, config=config or {})
        self.strategies: Dict[str, Strategy] = {}
        self.active_strategies: Set[str] = set()
        self.performance_history: List[Dict[str, Any]] = []

        logger.info(f"StrategyUnifiedAgent {agent_id} initialized")

    async def create_strategy(
        self,
        name: str,
        description: str,
        rules: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
    ) -> Strategy:
        """
        Create a new strategy.

        Args:
            name: Strategy name
            description: Strategy description
            rules: Strategy rules and conditions
            parameters: Optional strategy parameters
            tags: Optional strategy tags

        Returns:
            Created strategy instance
        """
        strategy = Strategy(
            name=name,
            description=description,
            rules=rules,
            parameters=parameters or {},
            tags=tags or set(),
        )

        self.strategies[str(strategy.strategy_id)] = strategy
        logger.info(f"Created strategy: {name} ({strategy.strategy_id})")

        return strategy

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status.

        Returns:
            UnifiedAgent status information
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": "StrategyUnifiedAgent",
            "total_strategies": len(self.strategies),
            "active_strategies": len(self.active_strategies),
            "status": "operational",
            "last_activity": datetime.utcnow().isoformat(),
        }

    async def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process incoming message.

        Args:
            message: Message to process
        """
        message_type = message.get("type", "unknown")

        if message_type == "create_strategy":
            await self.create_strategy(
                name=message.get("name", ""),
                description=message.get("description", ""),
                rules=message.get("rules", {}),
                parameters=message.get("parameters"),
                tags=message.get("tags"),
            )

        elif message_type == "get_status":
            self.get_status()

        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def take_action(self, action: Dict[str, Any]) -> None:
        """
        Take a specific action.

        Args:
            action: Action dictionary containing action type and parameters
        """
        action_type = action.get("type", "unknown")
        params = action.get("parameters", {})

        if action_type == "create_strategy":
            await self.create_strategy(
                name=params.get("name", ""),
                description=params.get("description", ""),
                rules=params.get("rules", {}),
                parameters=params.get("parameters"),
                tags=params.get("tags"),
            )

        else:
            logger.warning(f"Unknown action type: {action_type}")
