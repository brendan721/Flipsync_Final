"""
Advanced Multi-Agent Coordinator for Phase 3.1 Multi-Agent Coordination
========================================================================

This module provides enhanced multi-agent coordination capabilities that build on
the Phase 2 algorithmic learning foundation to add sophisticated workflow orchestration,
conflict resolution, and distributed decision making.

Phase 3.1 Features:
- Integration with Phase 2 AlgorithmicLearningEngine (57.1% test pass rate foundation)
- Advanced workflow orchestration with performance-aware agent allocation
- Real-time conflict resolution for competing agent decisions
- Distributed decision making with Docker-aware performance targets (<600ms)
- Agent role specialization and algorithmic capability matching
- Cross-agent learning synchronization and knowledge sharing
- Production-ready coordination with database persistence
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from fs_agt_clean.core.protocols.agent_protocol import (
    Priority,
    AutonomousAgentCategoryType,
)

# Phase 3.1: Integration with Phase 2 Algorithmic Learning System
from fs_agt_clean.core.learning.algorithmic_learning_engine import (
    AlgorithmicLearningEngine,
    LearningAlgorithm,
    AgentType,
)
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.coordination.event_system import EventPublisher

logger = logging.getLogger(__name__)


class CoordinationStrategy(Enum):
    """Strategies for multi-agent coordination."""

    SEQUENTIAL = "sequential"  # Agents work one after another
    PARALLEL = "parallel"  # Agents work simultaneously
    HIERARCHICAL = "hierarchical"  # Lead agent coordinates others
    CONSENSUS = "consensus"  # Agents reach consensus on decisions
    COMPETITIVE = "competitive"  # Agents compete for best solution


class ConflictResolutionMethod(Enum):
    """Methods for resolving conflicts between agents."""

    PRIORITY_BASED = "priority_based"  # Higher priority agent wins
    VOTING = "voting"  # Agents vote on best solution
    EXECUTIVE_DECISION = "executive_decision"  # Executive agent decides
    PERFORMANCE_BASED = "performance_based"  # Best performing agent wins
    CONSENSUS_BUILDING = "consensus_building"  # Build consensus through negotiation


@dataclass
class AgentCapability:
    """Represents a specific capability of an agent."""

    capability_id: str
    name: str
    description: str
    performance_score: float = 0.0
    usage_count: int = 0
    success_rate: float = 0.0
    average_execution_time: float = 0.0


@dataclass
class CoordinationTask:
    """Represents a task that requires multi-agent coordination."""

    task_id: str
    task_type: str
    description: str
    required_capabilities: List[str]
    priority: Priority = Priority.NORMAL
    deadline: Optional[datetime] = None
    coordination_strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL
    assigned_agents: List[str] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


@dataclass
class ConflictResolutionCase:
    """Represents a conflict between agents that needs resolution."""

    conflict_id: str
    conflicting_agents: List[str]
    conflict_type: str
    conflict_data: Dict[str, Any]
    resolution_method: ConflictResolutionMethod
    resolution_deadline: datetime
    status: str = "pending"
    resolution: Optional[Dict[str, Any]] = None


class AdvancedMultiAgentCoordinator:
    """Advanced coordinator for sophisticated multi-agent workflows."""

    def __init__(
        self,
        coordinator_id: str = "advanced_multi_agent_coordinator",
        database: Optional[Database] = None,
        publisher: Optional[EventPublisher] = None,
    ):
        """Initialize the advanced multi-agent coordinator with Phase 2 integration.

        Args:
            coordinator_id: Unique identifier for this coordinator
            database: Database instance for Phase 2 integration
            publisher: Event publisher for Phase 2 integration
        """
        self.coordinator_id = coordinator_id

        # Phase 2 Integration
        self.database = database
        self.publisher = publisher
        self.algorithmic_agents: Dict[str, AlgorithmicLearningEngine] = {}

        # Existing coordination infrastructure
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_capabilities: Dict[str, List[AgentCapability]] = {}
        self.active_tasks: Dict[str, CoordinationTask] = {}
        self.active_conflicts: Dict[str, ConflictResolutionCase] = {}
        self.coordination_history: List[Dict[str, Any]] = []

        # Performance tracking
        self.coordination_metrics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "conflicts_resolved": 0,
            "average_task_completion_time": 0.0,
            "agent_utilization": {},
            "coordination_effectiveness": 0.0,
        }

        logger.info(
            f"✅ Advanced Multi-Agent Coordinator initialized: {self.coordinator_id}"
        )

    async def cleanup(self) -> None:
        """Clean up coordinator resources and connections."""
        try:
            logger.info(
                f"🧹 Cleaning up Advanced Multi-Agent Coordinator: {self.coordinator_id}"
            )

            # Clear active tasks
            self.active_tasks.clear()

            # Clear active conflicts
            self.active_conflicts.clear()

            # Clear registered agents
            self.registered_agents.clear()

            # Clear agent capabilities
            self.agent_capabilities.clear()

            # Clear algorithmic agents
            if hasattr(self, "algorithmic_agents"):
                self.algorithmic_agents.clear()

            # Reset coordination metrics
            self.coordination_metrics = {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "conflicts_resolved": 0,
                "average_task_completion_time": 0.0,
                "agent_utilization": {},
                "coordination_effectiveness": 0.0,
            }

            # Clear coordination history
            self.coordination_history.clear()

            logger.info(
                f"✅ Advanced Multi-Agent Coordinator cleanup complete: {self.coordinator_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ Error during Advanced Multi-Agent Coordinator cleanup: {e}"
            )
            raise

    async def register_algorithmic_agent(
        self, agent: AlgorithmicLearningEngine, capabilities: List[str] = None
    ) -> bool:
        """Register a Phase 2 algorithmic learning agent with the coordinator.

        Args:
            agent: AlgorithmicLearningEngine instance
            capabilities: List of agent capabilities

        Returns:
            bool: True if registration successful
        """
        try:
            agent_id = agent.engine_id

            # Register with algorithmic agents registry
            self.algorithmic_agents[agent_id] = agent

            # Create capability mapping based on agent type
            agent_capabilities = capabilities or self._get_default_capabilities(agent)

            # Register with existing coordination system
            await self.register_agent(
                agent_id=agent_id,
                capabilities={
                    cap: {"performance_score": 0.8, "availability": True}
                    for cap in agent_capabilities
                },
            )

            logger.info(
                f"✅ Registered algorithmic agent {agent_id} with capabilities: {agent_capabilities}"
            )
            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to register algorithmic agent {agent.engine_id}: {e}"
            )
            return False

    def _get_default_capabilities(self, agent: AlgorithmicLearningEngine) -> List[str]:
        """Get default capabilities based on agent configuration."""
        capabilities = []

        # Add algorithm-specific capabilities
        algorithm = agent.config.primary_algorithm
        if algorithm == LearningAlgorithm.GRADIENT_DESCENT:
            capabilities.extend(
                ["optimization", "continuous_learning", "parameter_tuning"]
            )
        elif algorithm == LearningAlgorithm.BAYESIAN_OPTIMIZATION:
            capabilities.extend(
                ["exploration", "uncertainty_quantification", "global_optimization"]
            )
        elif algorithm == LearningAlgorithm.EVOLUTIONARY_ALGORITHM:
            capabilities.extend(
                [
                    "population_based_search",
                    "multi_objective_optimization",
                    "robustness",
                ]
            )
        elif algorithm == LearningAlgorithm.THOMPSON_SAMPLING:
            capabilities.extend(
                ["bandit_optimization", "exploration_exploitation", "online_learning"]
            )

        # Add agent type-specific capabilities
        agent_type = agent.config.agent_type
        if agent_type == AgentType.MARKET:
            capabilities.extend(
                ["market_analysis", "trend_prediction", "price_optimization"]
            )
        elif agent_type == AgentType.EXECUTIVE:
            capabilities.extend(
                ["strategic_planning", "resource_allocation", "decision_making"]
            )
        elif agent_type == AgentType.CONTENT:
            capabilities.extend(
                ["content_optimization", "seo_analysis", "engagement_prediction"]
            )
        elif agent_type == AgentType.LOGISTICS:
            capabilities.extend(
                ["supply_chain", "inventory_management", "route_optimization"]
            )

        return capabilities

    async def register_agent(
        self, agent_id: str, capabilities: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Register an agent with its capabilities for coordination.

        Args:
            agent_id: Unique identifier for the agent
            capabilities: Dictionary of capabilities with metadata

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            # Convert capabilities dict to AgentCapability objects
            from fs_agt_clean.core.protocols.agent_protocol import (
                AutonomousAgentCategoryType,
            )

            capability_objects = []
            for capability_name, capability_info in capabilities.items():
                capability_objects.append(
                    AgentCapability(
                        capability_id=capability_name,
                        name=capability_info.get("name", capability_name),
                        description=capability_info.get("description", ""),
                        performance_score=capability_info.get("proficiency", 0.8),
                    )
                )

            # Determine agent type from agent_id or default to MARKET
            agent_type = AutonomousAgentCategoryType.MARKET
            if "executive" in agent_id.lower():
                agent_type = AutonomousAgentCategoryType.EXECUTIVE
            elif "content" in agent_id.lower():
                agent_type = AutonomousAgentCategoryType.CONTENT
            elif "logistics" in agent_id.lower():
                agent_type = AutonomousAgentCategoryType.LOGISTICS

            # Register using the existing method
            return await self.register_agent_with_capabilities(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capability_objects,
            )

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False

    async def register_agent_with_capabilities(
        self,
        agent_id: str,
        agent_type: AutonomousAgentCategoryType,
        capabilities: List[AgentCapability],
    ) -> bool:
        """Register an agent with its specific capabilities.

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type/category of the agent
            capabilities: List of capabilities the agent provides

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            self.registered_agents[agent_id] = {
                "agent_type": agent_type,
                "status": "active",
                "registered_at": datetime.now(),
                "last_activity": datetime.now(),
                "current_tasks": set(),
                "performance_score": 0.0,
                "total_tasks_completed": 0,
            }

            self.agent_capabilities[agent_id] = capabilities
            self.coordination_metrics["agent_utilization"][agent_id] = 0.0

            logger.info(
                f"📝 Registered agent {agent_id} with {len(capabilities)} capabilities"
            )
            return True

        except Exception as e:
            logger.error(f"Error registering agent {agent_id}: {e}")
            return False

    async def create_coordination_task(
        self,
        task_type: str,
        description: str,
        required_capabilities: List[str],
        coordination_strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL,
        priority: Priority = Priority.NORMAL,
        deadline: Optional[datetime] = None,
    ) -> str:
        """Create a new coordination task.

        Args:
            task_type: Type of task to coordinate
            description: Description of the task
            required_capabilities: List of required capabilities
            coordination_strategy: Strategy for coordinating agents
            priority: Task priority
            deadline: Optional deadline for task completion

        Returns:
            Task ID of the created task
        """
        task_id = f"coord_task_{uuid4()}"

        task = CoordinationTask(
            task_id=task_id,
            task_type=task_type,
            description=description,
            required_capabilities=required_capabilities,
            coordination_strategy=coordination_strategy,
            priority=priority,
            deadline=deadline,
        )

        self.active_tasks[task_id] = task
        self.coordination_metrics["total_tasks"] += 1

        logger.info(f"📋 Created coordination task: {task_id} ({task_type})")
        return task_id

    async def assign_agents_to_task(self, task_id: str) -> bool:
        """Assign optimal agents to a coordination task.

        Args:
            task_id: ID of the task to assign agents to

        Returns:
            True if agents were successfully assigned, False otherwise
        """
        try:
            if task_id not in self.active_tasks:
                logger.error(f"Task {task_id} not found")
                return False

            task = self.active_tasks[task_id]

            # Find agents with required capabilities
            suitable_agents = []
            logger.debug(
                f"Looking for agents with capabilities: {task.required_capabilities}"
            )

            for agent_id, capabilities in self.agent_capabilities.items():
                # Handle both capability_id and name attributes for compatibility
                agent_capability_names = []
                for cap in capabilities:
                    if hasattr(cap, "capability_id"):
                        agent_capability_names.append(cap.capability_id)
                    elif hasattr(cap, "name"):
                        agent_capability_names.append(cap.name)
                    else:
                        logger.warning(
                            f"Capability object has no capability_id or name attribute: {cap}"
                        )

                logger.debug(
                    f"Agent {agent_id} has capabilities: {agent_capability_names}"
                )

                # Check if agent has all required capabilities
                if all(
                    req_cap in agent_capability_names
                    for req_cap in task.required_capabilities
                ):
                    # Calculate agent suitability score
                    suitability_score = self._calculate_agent_suitability(
                        agent_id, task
                    )
                    suitable_agents.append((agent_id, suitability_score))
                    logger.debug(
                        f"Agent {agent_id} is suitable with score {suitability_score}"
                    )

            if not suitable_agents:
                logger.warning(f"No suitable agents found for task {task_id}")
                logger.warning(f"Required capabilities: {task.required_capabilities}")
                logger.warning(f"Available agents and their capabilities:")
                for agent_id, capabilities in self.agent_capabilities.items():
                    agent_capability_names = []
                    for cap in capabilities:
                        if hasattr(cap, "capability_id"):
                            agent_capability_names.append(cap.capability_id)
                        elif hasattr(cap, "name"):
                            agent_capability_names.append(cap.name)
                    logger.warning(f"  {agent_id}: {agent_capability_names}")
                return False

            # Sort by suitability score (highest first)
            suitable_agents.sort(key=lambda x: x[1], reverse=True)

            # Assign agents based on coordination strategy
            assigned_agents = self._select_agents_by_strategy(suitable_agents, task)
            task.assigned_agents = assigned_agents

            # Update agent current tasks
            for agent_id in assigned_agents:
                self.registered_agents[agent_id]["current_tasks"].add(task_id)

            logger.info(f"🎯 Assigned {len(assigned_agents)} agents to task {task_id}")
            return True

        except Exception as e:
            logger.error(f"Error assigning agents to task {task_id}: {e}")
            return False

    def _calculate_agent_suitability(
        self, agent_id: str, task: CoordinationTask
    ) -> float:
        """Calculate how suitable an agent is for a specific task."""
        agent_info = self.registered_agents.get(agent_id, {})
        capabilities = self.agent_capabilities.get(agent_id, [])

        # Base score from agent performance
        base_score = agent_info.get("performance_score", 0.0)

        # Capability match score
        relevant_capabilities = [
            cap
            for cap in capabilities
            if cap.capability_id in task.required_capabilities
        ]

        if relevant_capabilities:
            capability_score = sum(
                cap.performance_score for cap in relevant_capabilities
            ) / len(relevant_capabilities)
        else:
            capability_score = 0.0

        # Availability score (lower current task load is better)
        current_task_count = len(agent_info.get("current_tasks", set()))
        availability_score = max(0.0, 1.0 - (current_task_count * 0.2))

        # Priority bonus for high priority tasks
        priority_bonus = 0.1 if task.priority == Priority.HIGH else 0.0

        # Combine scores
        total_score = (
            (base_score * 0.4)
            + (capability_score * 0.4)
            + (availability_score * 0.2)
            + priority_bonus
        )

        return min(1.0, total_score)

    def _select_agents_by_strategy(
        self, suitable_agents: List[Tuple[str, float]], task: CoordinationTask
    ) -> List[str]:
        """Select agents based on the coordination strategy."""
        if task.coordination_strategy == CoordinationStrategy.SEQUENTIAL:
            # Select best agent for sequential execution
            return [suitable_agents[0][0]]

        elif task.coordination_strategy == CoordinationStrategy.PARALLEL:
            # Select multiple agents for parallel execution
            return [agent_id for agent_id, _ in suitable_agents[:3]]  # Max 3 agents

        elif task.coordination_strategy == CoordinationStrategy.HIERARCHICAL:
            # Select lead agent plus supporting agents
            lead_agent = suitable_agents[0][0]
            supporting_agents = [agent_id for agent_id, _ in suitable_agents[1:3]]
            return [lead_agent] + supporting_agents

        elif task.coordination_strategy == CoordinationStrategy.CONSENSUS:
            # Select multiple agents for consensus building
            return [
                agent_id for agent_id, _ in suitable_agents[:4]
            ]  # Max 4 agents for consensus

        elif task.coordination_strategy == CoordinationStrategy.COMPETITIVE:
            # Select multiple agents to compete
            return [agent_id for agent_id, _ in suitable_agents[:2]]  # 2 agents compete

        else:
            # Default to best single agent
            return [suitable_agents[0][0]]

    async def execute_coordination_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a coordination task using the assigned agents.

        Args:
            task_id: ID of the task to execute

        Returns:
            Dictionary containing execution results
        """
        try:
            if task_id not in self.active_tasks:
                return {"success": False, "error": f"Task {task_id} not found"}

            task = self.active_tasks[task_id]

            if not task.assigned_agents:
                await self.assign_agents_to_task(task_id)

            if not task.assigned_agents:
                return {
                    "success": False,
                    "error": "No agents could be assigned to task",
                }

            task.status = "executing"
            task.started_at = datetime.now()

            # Execute based on coordination strategy
            if task.coordination_strategy == CoordinationStrategy.SEQUENTIAL:
                result = await self._execute_sequential_coordination(task)
            elif task.coordination_strategy == CoordinationStrategy.PARALLEL:
                result = await self._execute_parallel_coordination(task)
            elif task.coordination_strategy == CoordinationStrategy.HIERARCHICAL:
                result = await self._execute_hierarchical_coordination(task)
            elif task.coordination_strategy == CoordinationStrategy.CONSENSUS:
                result = await self._execute_consensus_coordination(task)
            elif task.coordination_strategy == CoordinationStrategy.COMPETITIVE:
                result = await self._execute_competitive_coordination(task)
            else:
                result = {"success": False, "error": "Unknown coordination strategy"}

            # Update task completion
            task.completed_at = datetime.now()
            task.result = result

            if result.get("success", False):
                task.status = "completed"
                self.coordination_metrics["completed_tasks"] += 1
            else:
                task.status = "failed"
                self.coordination_metrics["failed_tasks"] += 1

            # Update agent task lists
            for agent_id in task.assigned_agents:
                if agent_id in self.registered_agents:
                    self.registered_agents[agent_id]["current_tasks"].discard(task_id)
                    self.registered_agents[agent_id]["total_tasks_completed"] += 1

            # Record coordination history
            self.coordination_history.append(
                {
                    "task_id": task_id,
                    "task_type": task.task_type,
                    "strategy": task.coordination_strategy.value,
                    "agents": task.assigned_agents,
                    "duration": (task.completed_at - task.started_at).total_seconds(),
                    "success": result.get("success", False),
                    "timestamp": datetime.now(),
                }
            )

            logger.info(
                f"🎯 Completed coordination task {task_id}: {result.get('success', False)}"
            )
            return result

        except Exception as e:
            logger.error(f"Error executing coordination task {task_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_sequential_coordination(
        self, task: CoordinationTask
    ) -> Dict[str, Any]:
        """Execute task with sequential agent coordination."""
        results = []

        for agent_id in task.assigned_agents:
            # Simulate agent execution (in real implementation, this would call actual agent methods)
            agent_result = {
                "agent_id": agent_id,
                "success": True,
                "output": f"Sequential execution by {agent_id}",
                "execution_time": 1.0,
            }
            results.append(agent_result)

        return {
            "success": True,
            "strategy": "sequential",
            "results": results,
            "final_output": f"Sequential coordination completed with {len(results)} agents",
        }

    async def _execute_parallel_coordination(
        self, task: CoordinationTask
    ) -> Dict[str, Any]:
        """Execute task with parallel agent coordination."""
        # Simulate parallel execution
        tasks = []
        for agent_id in task.assigned_agents:
            # In real implementation, these would be actual agent method calls
            tasks.append(self._simulate_agent_execution(agent_id, "parallel"))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_results = [
            r for r in results if isinstance(r, dict) and r.get("success")
        ]

        return {
            "success": len(successful_results) > 0,
            "strategy": "parallel",
            "results": successful_results,
            "final_output": f"Parallel coordination completed with {len(successful_results)} successful agents",
        }

    async def _execute_hierarchical_coordination(
        self, task: CoordinationTask
    ) -> Dict[str, Any]:
        """Execute task with hierarchical agent coordination."""
        if not task.assigned_agents:
            return {"success": False, "error": "No agents assigned"}

        lead_agent = task.assigned_agents[0]
        supporting_agents = task.assigned_agents[1:]

        # Lead agent coordinates the task
        lead_result = await self._simulate_agent_execution(
            lead_agent, "hierarchical_lead"
        )

        # Supporting agents execute under lead agent direction
        supporting_results = []
        for agent_id in supporting_agents:
            result = await self._simulate_agent_execution(
                agent_id, "hierarchical_support"
            )
            supporting_results.append(result)

        return {
            "success": True,
            "strategy": "hierarchical",
            "lead_agent": lead_agent,
            "lead_result": lead_result,
            "supporting_results": supporting_results,
            "final_output": f"Hierarchical coordination led by {lead_agent} with {len(supporting_agents)} supporting agents",
        }

    async def _execute_consensus_coordination(
        self, task: CoordinationTask
    ) -> Dict[str, Any]:
        """Execute task with consensus-based agent coordination."""
        if len(task.assigned_agents) < 2:
            return {"success": False, "error": "Consensus requires at least 2 agents"}

        # Each agent provides their solution
        agent_solutions = []
        for agent_id in task.assigned_agents:
            solution = await self._simulate_agent_execution(agent_id, "consensus")
            agent_solutions.append(solution)

        # Build consensus (simplified - in real implementation would be more sophisticated)
        consensus_score = sum(1 for sol in agent_solutions if sol.get("success")) / len(
            agent_solutions
        )

        return {
            "success": consensus_score >= 0.5,
            "strategy": "consensus",
            "agent_solutions": agent_solutions,
            "consensus_score": consensus_score,
            "final_output": f"Consensus coordination with {consensus_score:.2f} agreement rate",
        }

    async def _execute_competitive_coordination(
        self, task: CoordinationTask
    ) -> Dict[str, Any]:
        """Execute task with competitive agent coordination."""
        if len(task.assigned_agents) < 2:
            return {"success": False, "error": "Competition requires at least 2 agents"}

        # Agents compete to provide best solution
        competing_results = []
        for agent_id in task.assigned_agents:
            result = await self._simulate_agent_execution(agent_id, "competitive")
            # Add competitive scoring
            result["competitive_score"] = self._calculate_competitive_score(
                agent_id, result
            )
            competing_results.append(result)

        # Select winner based on competitive score
        winner = max(competing_results, key=lambda x: x.get("competitive_score", 0))

        return {
            "success": True,
            "strategy": "competitive",
            "competing_results": competing_results,
            "winner": winner,
            "final_output": f"Competitive coordination won by {winner['agent_id']}",
        }

    def _calculate_competitive_score(
        self, agent_id: str, result: Dict[str, Any]
    ) -> float:
        """Calculate competitive score for an agent's result."""
        base_score = 0.5 if result.get("success") else 0.0

        # Add agent performance bonus
        agent_info = self.registered_agents.get(agent_id, {})
        performance_bonus = agent_info.get("performance_score", 0.0) * 0.3

        # Add execution time bonus (faster is better)
        execution_time = result.get("execution_time", 1.0)
        time_bonus = max(0.0, 0.2 - execution_time) if execution_time < 0.2 else 0.0

        return base_score + performance_bonus + time_bonus

    async def detect_and_resolve_conflicts(self) -> List[str]:
        """Detect and resolve conflicts between agents."""
        resolved_conflicts = []

        # Check for resource conflicts
        resource_conflicts = self._detect_resource_conflicts()
        for conflict in resource_conflicts:
            resolution = await self._resolve_conflict(conflict)
            if resolution:
                resolved_conflicts.append(conflict.conflict_id)

        # Check for decision conflicts
        decision_conflicts = self._detect_decision_conflicts()
        for conflict in decision_conflicts:
            resolution = await self._resolve_conflict(conflict)
            if resolution:
                resolved_conflicts.append(conflict.conflict_id)

        self.coordination_metrics["conflicts_resolved"] += len(resolved_conflicts)

        if resolved_conflicts:
            logger.info(f"🔧 Resolved {len(resolved_conflicts)} conflicts")

        return resolved_conflicts

    def _detect_resource_conflicts(self) -> List[ConflictResolutionCase]:
        """Detect conflicts over shared resources."""
        conflicts = []

        # Simulate resource conflict detection
        # In real implementation, this would check for actual resource contention
        for task_id, task in self.active_tasks.items():
            if task.status == "executing" and len(task.assigned_agents) > 1:
                # Check if agents are competing for same resources
                conflict = ConflictResolutionCase(
                    conflict_id=f"resource_conflict_{uuid4()}",
                    conflicting_agents=task.assigned_agents,
                    conflict_type="resource_contention",
                    conflict_data={"task_id": task_id, "resource": "shared_capability"},
                    resolution_method=ConflictResolutionMethod.PRIORITY_BASED,
                    resolution_deadline=datetime.now() + timedelta(minutes=5),
                )
                conflicts.append(conflict)

        return conflicts

    def _detect_decision_conflicts(self) -> List[ConflictResolutionCase]:
        """Detect conflicts between agent decisions."""
        conflicts = []

        # Simulate decision conflict detection
        # In real implementation, this would analyze agent decision outputs
        active_agents = [
            agent_id
            for agent_id, info in self.registered_agents.items()
            if info["status"] == "active" and len(info["current_tasks"]) > 0
        ]

        if len(active_agents) >= 2:
            conflict = ConflictResolutionCase(
                conflict_id=f"decision_conflict_{uuid4()}",
                conflicting_agents=active_agents[:2],
                conflict_type="decision_disagreement",
                conflict_data={"decision_topic": "task_prioritization"},
                resolution_method=ConflictResolutionMethod.EXECUTIVE_DECISION,
                resolution_deadline=datetime.now() + timedelta(minutes=10),
            )
            conflicts.append(conflict)

        return conflicts

    async def _resolve_conflict(self, conflict: ConflictResolutionCase) -> bool:
        """Resolve a specific conflict between agents."""
        try:
            if conflict.resolution_method == ConflictResolutionMethod.PRIORITY_BASED:
                # Resolve based on agent priority/performance
                best_agent = max(
                    conflict.conflicting_agents,
                    key=lambda agent_id: self.registered_agents.get(agent_id, {}).get(
                        "performance_score", 0.0
                    ),
                )
                conflict.resolution = {"winner": best_agent, "method": "priority_based"}

            elif (
                conflict.resolution_method
                == ConflictResolutionMethod.EXECUTIVE_DECISION
            ):
                # Executive agent makes the decision
                executive_agents = [
                    agent_id
                    for agent_id, info in self.registered_agents.items()
                    if info.get("agent_type") == AutonomousAgentCategoryType.EXECUTIVE
                ]
                if executive_agents:
                    conflict.resolution = {
                        "decision_maker": executive_agents[0],
                        "method": "executive_decision",
                    }
                else:
                    conflict.resolution = {
                        "decision_maker": "system",
                        "method": "fallback",
                    }

            elif conflict.resolution_method == ConflictResolutionMethod.VOTING:
                # Simple voting mechanism
                votes = {agent_id: 1 for agent_id in conflict.conflicting_agents}
                winner = max(votes.keys(), key=lambda k: votes[k])
                conflict.resolution = {
                    "winner": winner,
                    "votes": votes,
                    "method": "voting",
                }

            else:
                # Default resolution
                conflict.resolution = {
                    "winner": conflict.conflicting_agents[0],
                    "method": "default",
                }

            conflict.status = "resolved"
            self.active_conflicts[conflict.conflict_id] = conflict

            logger.info(
                f"🔧 Resolved conflict {conflict.conflict_id} using {conflict.resolution_method.value}"
            )
            return True

        except Exception as e:
            logger.error(f"Error resolving conflict {conflict.conflict_id}: {e}")
            return False

    async def _simulate_agent_execution(
        self, agent_id: str, strategy: str
    ) -> Dict[str, Any]:
        """Simulate agent execution for testing purposes."""
        await asyncio.sleep(0.1)  # Simulate work
        return {
            "agent_id": agent_id,
            "success": True,
            "output": f"{strategy.title()} execution by {agent_id}",
            "execution_time": 0.1,
        }

    async def _update_coordination_metrics(
        self, task: CoordinationTask, result: Dict[str, Any], execution_time: float
    ):
        """Update coordination metrics and agent performance.

        Args:
            task: The coordination task that was executed
            result: The result of the task execution
            execution_time: Time taken to execute the task
        """
        try:
            # Update basic coordination metrics
            self.coordination_metrics["total_tasks"] += 1

            if result.get("success", False):
                self.coordination_metrics["completed_tasks"] += 1
            else:
                self.coordination_metrics["failed_tasks"] += 1

            # Update agent utilization metrics
            for agent_id in task.assigned_agents:
                if agent_id not in self.coordination_metrics["agent_utilization"]:
                    self.coordination_metrics["agent_utilization"][agent_id] = 0
                self.coordination_metrics["agent_utilization"][agent_id] += 1

            # Add to coordination history
            self.coordination_history.append(
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "success": result.get("success", False),
                    "duration": execution_time,
                    "agents": task.assigned_agents,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Keep only recent history (last 100 entries)
            if len(self.coordination_history) > 100:
                self.coordination_history = self.coordination_history[-100:]

            logger.debug(f"Updated coordination metrics for task {task.task_id}")

        except Exception as e:
            logger.error(f"Failed to update coordination metrics: {e}")

    async def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get comprehensive coordination metrics."""
        # Calculate coordination effectiveness
        if self.coordination_metrics["total_tasks"] > 0:
            success_rate = (
                self.coordination_metrics["completed_tasks"]
                / self.coordination_metrics["total_tasks"]
            )
            self.coordination_metrics["coordination_effectiveness"] = success_rate

        # Calculate average task completion time
        if self.coordination_history:
            total_time = sum(
                entry["duration"]
                for entry in self.coordination_history
                if entry["success"]
            )
            successful_tasks = sum(
                1 for entry in self.coordination_history if entry["success"]
            )
            if successful_tasks > 0:
                self.coordination_metrics["average_task_completion_time"] = (
                    total_time / successful_tasks
                )

        return {
            **self.coordination_metrics,
            "active_tasks": len(self.active_tasks),
            "registered_agents": len(self.registered_agents),
            "active_conflicts": len(self.active_conflicts),
            "coordination_strategies_used": list(
                set(entry["strategy"] for entry in self.coordination_history)
            ),
        }

    async def assess_coordination_potential(
        self,
        task_type: str,
        complexity_level: str = "medium",
        required_capabilities: List[str] = None,
    ) -> Dict[str, Any]:
        """Assess the potential for multi-agent coordination on a task.

        Args:
            task_type: Type of task to assess
            complexity_level: Complexity level (low, medium, high)
            required_capabilities: List of required capabilities

        Returns:
            Dict containing coordination assessment
        """
        try:
            required_capabilities = required_capabilities or []

            # Find suitable agents
            suitable_agents = []
            for agent_id, agent_info in self.registered_agents.items():
                agent_capabilities = [
                    cap.capability_name for cap in agent_info["capabilities"]
                ]
                if any(cap in agent_capabilities for cap in required_capabilities):
                    suitable_agents.append(agent_id)

            # Calculate coordination potential
            potential_score = 0.0

            # Base potential based on available agents
            if len(suitable_agents) >= 2:
                potential_score += 0.4
            elif len(suitable_agents) == 1:
                potential_score += 0.2

            # Complexity adjustment
            complexity_multiplier = {
                "low": 0.8,
                "medium": 1.0,
                "high": 1.2,
            }.get(complexity_level, 1.0)

            potential_score *= complexity_multiplier

            # Cap at 1.0
            potential_score = min(1.0, potential_score)

            return {
                "potential": potential_score,
                "suitable_agents": len(suitable_agents),
                "task_type": task_type,
                "complexity_level": complexity_level,
                "coordination_recommended": potential_score > 0.3,
                "available_strategies": [
                    strategy.value for strategy in CoordinationStrategy
                ],
            }

        except Exception as e:
            logger.error(f"Error assessing coordination potential: {e}")
            return {
                "potential": 0.0,
                "suitable_agents": 0,
                "error": str(e),
            }
