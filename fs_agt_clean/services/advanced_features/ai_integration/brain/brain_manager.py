import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fs_agt_clean.agents.executive.decision_engine import DecisionEngine
from fs_agt_clean.agents.executive.memory_manager import MemoryManager
from fs_agt_clean.core.agent_coordination import (
    UnifiedAgentOrchestrator,
    StrategyManager,
    WorkflowState,
)

"\nBrain module for the FlipSync UnifiedAgentic System.\nProvides central intelligence and decision-making capabilities.\n"


class Brain:
    """
    Central intelligence system that:
    - Coordinates agent activities
    - Makes high-level decisions
    - Manages system memory
    - Optimizes strategies
    """

    def __init__(self):
        self.decision_engine = DecisionEngine()
        self.memory_manager = MemoryManager()
        self.orchestrator = UnifiedAgentOrchestrator()
        self.strategy_manager = StrategyManager()
        self.active_workflows: Set[str] = set()
        self.system_state: Dict[str, Any] = {
            "initialized_at": datetime.utcnow(),
            "last_decision": None,
            "active_agents": set(),
            "performance_metrics": {},
        }
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize the brain and its components"""
        self.logger.info("Initializing brain components...")
        await self._initialize_strategies()
        await self._setup_monitoring()
        self.logger.info("Brain initialization complete")

    async def process_event(
        self, event: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process an incoming event"""
        self.logger.debug("Processing event: %s", event)
        await self.memory_manager.store_short_term(
            {
                "type": "event",
                "data": event,
                "context": context or {},
                "timestamp": datetime.utcnow(),
            }
        )
        decision = await self._make_decision(event, context)
        self.system_state["last_decision"] = {
            "event": event,
            "decision": decision,
            "timestamp": datetime.utcnow(),
        }
        return decision

    async def register_agent(self, agent_id: str, agent: Any) -> None:
        """Register a new agent with the brain"""
        await self.orchestrator.register_agent(agent_id, agent)
        self.system_state["active_agents"].add(agent_id)
        self.logger.info("Registered agent: %s", agent_id)

    async def start_workflow(self, workflow_id: str, config: Dict[str, Any]) -> None:
        """Start a new workflow"""
        await self.orchestrator.start_workflow(config=config, workflow_id=workflow_id)
        self.active_workflows.add(workflow_id)
        self.logger.info("Started workflow: %s", workflow_id)

    async def get_system_state(self) -> Dict[str, Any]:
        """Get current system state"""
        self.system_state["performance_metrics"] = {
            "memory": await self.memory_manager.get_memory_stats(),
            "workflows": len(self.active_workflows),
            "active_agents": len(self.system_state["active_agents"]),
        }
        return self.system_state

    async def optimize_performance(self) -> None:
        """Optimize system performance"""
        self.logger.info("Starting performance optimization")
        for workflow_id in self.active_workflows:
            strategy = await self.strategy_manager.get_active_strategy(workflow_id)
            if strategy:
                await self.strategy_manager.optimize_strategy(
                    strategy, {"performance_threshold": 0.8}
                )
        await self._cleanup_memory()
        self.logger.info("Performance optimization complete")

    async def shutdown(self) -> None:
        """Gracefully shutdown the brain"""
        self.logger.info("Initiating brain shutdown")
        for workflow_id in list(self.active_workflows):
            await self.orchestrator.update_workflow_state(
                workflow_id, WorkflowState.COMPLETED
            )
        await self.memory_manager.clear_all()
        self.logger.info("Brain shutdown complete")

    async def _initialize_strategies(self) -> None:
        """Initialize default strategies"""
        default_strategies = {
            "resource_optimization": {
                "rules": {"confidence_threshold": 0.7},
                "weights": {
                    "memory_usage": 0.3,
                    "workflow_count": 0.3,
                    "agent_load": 0.4,
                },
            },
            "workflow_management": {
                "rules": {"confidence_threshold": 0.8},
                "weights": {
                    "priority": 0.4,
                    "complexity": 0.3,
                    "resource_availability": 0.3,
                },
            },
        }
        for name, config in default_strategies.items():
            await self.strategy_manager.register_strategy(name, config)

    async def _setup_monitoring(self) -> None:
        """Set up system monitoring"""
        asyncio.create_task(self._monitor_memory())
        asyncio.create_task(self._monitor_workflows())

    async def _monitor_memory(self) -> None:
        """Monitor memory usage"""
        while True:
            stats = await self.memory_manager.get_memory_stats()
            if stats["short_term_usage"] > 0.8 or stats["long_term_usage"] > 0.8:
                await self._cleanup_memory()
            await asyncio.sleep(60)

    async def _monitor_workflows(self) -> None:
        """Monitor workflow performance"""
        while True:
            for workflow_id in self.active_workflows:
                metrics = await self.orchestrator.get_metrics()
                if metrics["workflows_failed"] > 0:
                    self.logger.warning("Workflow failure detected: %s", workflow_id)
            await asyncio.sleep(300)

    async def _make_decision(
        self, event: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a decision based on event and context"""
        memory_context = {
            "short_term": await self.memory_manager.get_short_term(limit=10),
            "working_memory": await self.memory_manager.get_working_memory(),
        }
        actions = await self._determine_actions(event)
        decision = await self.decision_engine.make_decision(
            context or {}, actions, memory_context
        )
        return {
            "action": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
        }

    async def _determine_actions(self, event: Dict[str, Any]) -> List[str]:
        """Determine available actions for an event"""
        actions = ["process", "defer", "ignore"]
        if "type" in event:
            if event["type"] == "error":
                actions.extend(["retry", "escalate"])
            elif event["type"] == "request":
                actions.extend(["approve", "reject"])
            elif event["type"] == "alert":
                actions.extend(["acknowledge", "investigate"])
        return actions

    async def _cleanup_memory(self) -> None:
        """Clean up system memory"""
        self.logger.info("Starting memory cleanup")
        short_term = await self.memory_manager.get_short_term()
        for item in short_term:
            if (datetime.utcnow() - item["timestamp"]).days > 7:
                await self.memory_manager.store_long_term(item)
        working_memory = await self.memory_manager.get_working_memory()
        working_memory["last_cleanup"] = datetime.utcnow()
        await self.memory_manager.update_working_memory(working_memory)
        self.logger.info("Memory cleanup complete")
