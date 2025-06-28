"""Brain service for the FlipSync UnifiedAgentic System."""

# import asyncio # Remove unused
import logging

# from typing import Dict, List, Optional # Remove List
from typing import Dict, Optional

from fs_agt_clean.core.agent_coordination import UnifiedAgentOrchestrator
from fs_agt_clean.core.brain.decision import Decision, DecisionEngine

# from fs_agt_clean.core.brain.workflow import WorkflowState # Remove unused
from fs_agt_clean.core.memory.memory_manager import MemoryManager


class UnifiedAgentBrain:
    """Coordinates multi-agent activities and makes strategic decisions."""

    def __init__(self, min_confidence: float = 0.8):
        """Initialize the brain.

        Args:
            min_confidence: Minimum confidence threshold for decisions
        """
        self.logger = logging.getLogger(__name__)
        self._memory = MemoryManager()
        self._decision_engine = DecisionEngine(min_confidence)
        self._orchestrator = UnifiedAgentOrchestrator()
        self._active = False

    async def initialize(self) -> None:
        """Initialize brain components."""
        self._active = True
        self.logger.info("Brain initialized")

    async def process_event(self, event: Dict) -> Optional[Decision]:
        """Process an event and make a decision.

        Args:
            event: Event data

        Returns:
            Optional[Decision]: Decision if one was made
        """
        if not self._active:
            return None

        # Store event in memory
        await self._memory.store_short_term(event)

        # Get relevant context
        context = await self._memory.get_working_memory()

        # Make decision
        recent_memories = await self._memory.get_short_term(limit=10)
        memory_context = recent_memories if recent_memories else None

        decision = await self._decision_engine.make_decision(
            context=context,
            possible_actions=["action1", "action2"],  # TODO: Get from config
            memory_context=memory_context,
        )

        if decision:
            self.logger.info("Made decision: %s", decision)

        return decision

    async def start_workflow(self, config: Dict[str, bool]) -> str:
        """Start a new workflow.

        Args:
            config: Workflow configuration

        Returns:
            str: Workflow ID
        """
        return await self._orchestrator.start_workflow(config)

    async def get_system_state(self) -> Dict:
        """Get current system state.

        Returns:
            Dict: System state information
        """
        active_workflows = await self._orchestrator.get_active_workflows()
        memory_stats = await self._memory.get_memory_stats()

        return {
            "active": self._active,
            "workflows": len(active_workflows),
            "memory": memory_stats,
        }

    async def shutdown(self) -> None:
        """Shutdown brain components."""
        self._active = False
        await self._memory.clear_all()
        self.logger.info("Brain shutdown")
