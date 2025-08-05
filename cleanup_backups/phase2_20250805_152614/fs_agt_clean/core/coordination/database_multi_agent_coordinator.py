"""
Database-backed Multi-Agent Coordinator for FlipSync Agentic System

This module extends the existing AdvancedMultiAgentCoordinator to add database persistence
for coordination state, enabling coordination to survive agent restarts and providing
cross-session coordination capabilities.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from fs_agt_clean.core.coordination.advanced_multi_agent_coordinator import (
    AdvancedMultiAgentCoordinator,
    CoordinationStrategy,
    CoordinationTask,
)
from fs_agt_clean.core.coordination.database_models import (
    AgentCapabilityRegistry,
    CoordinationState,
)
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class DatabaseMultiAgentCoordinator(AdvancedMultiAgentCoordinator):
    """Database-backed Multi-Agent Coordinator with persistent coordination state.

    This class extends the existing AdvancedMultiAgentCoordinator to add:
    - Persistent coordination state storage
    - Agent capability registration and tracking
    - Cross-session coordination recovery
    - Agent communication history
    - Coordination analytics and metrics
    """

    def __init__(
        self,
        coordinator_id: str,
        database: Database,
        max_concurrent_tasks: int = 10,
        task_timeout_seconds: int = 300,
        fast_init: bool = False,
    ):
        """Initialize the database-backed multi-agent coordinator.

        Args:
            coordinator_id: Unique identifier for this coordinator
            database: Database instance for persistence
            max_concurrent_tasks: Maximum number of concurrent coordination tasks
            task_timeout_seconds: Timeout for coordination tasks in seconds
            fast_init: Enable fast initialization mode (skip non-essential operations)
        """
        super().__init__(coordinator_id)

        self.database = database
        self.coordination_cache: Dict[str, CoordinationState] = {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_timeout_seconds = task_timeout_seconds

        # Performance optimization: Cache initialization state
        self._initialized = False
        self._initialization_cache = {}
        self._fast_init = fast_init

        logger.info(
            f"Initialized DatabaseMultiAgentCoordinator {coordinator_id} (fast_init: {fast_init})"
        )

    async def initialize(self) -> bool:
        """Initialize the database-backed coordinator with performance optimizations.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Performance optimization: Skip if already initialized
            if self._initialized:
                logger.debug(
                    f"DatabaseMultiAgentCoordinator {self.coordinator_id} already initialized"
                )
                return True

            # Parent coordinator is already initialized in __init__
            logger.debug("Parent AdvancedMultiAgentCoordinator initialized")

            # Performance optimization: Run initialization tasks in parallel
            if self._fast_init:
                # Fast initialization: Skip non-essential operations
                initialization_tasks = [
                    self._ensure_tables_exist(),
                ]
                logger.debug(
                    "Fast initialization mode: skipping state loading and capability registration"
                )
            else:
                initialization_tasks = [
                    self._ensure_tables_exist(),
                    self._load_active_coordination_states(),
                    self._register_coordinator_capabilities_optimized(),
                ]

            # Execute all initialization tasks concurrently
            results = await asyncio.gather(
                *initialization_tasks, return_exceptions=True
            )

            # Check for any failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    task_names = [
                        "table_creation",
                        "state_loading",
                        "capability_registration",
                    ]
                    logger.error(
                        f"Initialization task {task_names[i]} failed: {result}"
                    )
                    return False

            self._initialized = True
            logger.info(
                f"✅ DatabaseMultiAgentCoordinator initialized for {self.coordinator_id} (optimized)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize DatabaseMultiAgentCoordinator: {e}")
            return False

    async def coordinate_task(
        self, task: CoordinationTask, store_in_database: bool = True
    ) -> Dict[str, Any]:
        """Coordinate a task with database persistence.

        Args:
            task: Coordination task to execute
            store_in_database: Whether to store coordination state in database

        Returns:
            Coordination result with database persistence
        """
        start_time = time.time()
        coordination_id = str(uuid.uuid4())

        try:
            # Store initial coordination state in database
            if store_in_database:
                await self._store_coordination_state(
                    coordination_id=coordination_id,
                    task=task,
                    status="active",
                    current_step=0,
                    step_results=[],
                )

            # Execute coordination using parent class workflow
            # Create task in parent coordinator
            task_id = await self.create_coordination_task(
                task_type=task.task_type,
                description=task.description,
                required_capabilities=task.required_capabilities,
                coordination_strategy=task.coordination_strategy,
                priority=getattr(task, "priority", "normal"),
                deadline=getattr(task, "deadline", None),
            )

            # Assign agents and execute
            await self.assign_agents_to_task(task_id)
            result = await self.execute_coordination_task(task_id)

            # Update coordination state with results
            if store_in_database:
                execution_time_ms = int((time.time() - start_time) * 1000)
                await self._update_coordination_state(
                    coordination_id=coordination_id,
                    status="completed" if result.get("success") else "failed",
                    step_results=result.get("step_results", []),
                    final_result=result,
                    execution_time_ms=execution_time_ms,
                    error_message=(
                        result.get("error") if not result.get("success") else None
                    ),
                )

            # Update coordination metrics
            await self._update_coordination_metrics(
                task, result, time.time() - start_time
            )

            logger.debug(
                f"Coordination completed for task {task.task_id}: {result.get('success', False)}"
            )
            return result

        except Exception as e:
            logger.error(f"Coordination failed for task {task.task_id}: {e}")

            # Update coordination state with error
            if store_in_database:
                await self._update_coordination_state(
                    coordination_id=coordination_id,
                    status="failed",
                    error_message=str(e),
                )

            return {
                "success": False,
                "error": str(e),
                "coordination_id": coordination_id,
                "task_id": task.task_id,
            }

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
            # Register with parent coordinator
            await super().register_agent(agent_id, capabilities)

            # Register each capability in database
            for capability_name, capability_info in capabilities.items():
                await self.register_agent_capability(
                    agent_id=agent_id,
                    agent_type=capability_info.get("type", "unknown"),
                    capability_name=capability_name,
                    capability_type=capability_info.get("type", "unknown"),
                    capability_description=capability_info.get("description", ""),
                    proficiency_score=capability_info.get("proficiency", 0.8),
                )

            logger.info(
                f"📝 Registered agent for coordination: {agent_id} with {len(capabilities)} capabilities"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False

    async def register_agent_optimized(
        self, agent_id: str, capabilities: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Register an agent with optimized batch capability registration.

        Args:
            agent_id: Unique identifier for the agent
            capabilities: Dictionary of capabilities with their metadata

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            # Register with parent coordinator
            await super().register_agent(agent_id, capabilities)

            # Performance optimization: Batch register capabilities in database
            async with self.database.get_session() as session:
                # Check existing capabilities first
                existing_capabilities = await session.execute(
                    select(AgentCapabilityRegistry.capability_name).where(
                        AgentCapabilityRegistry.agent_id == agent_id
                    )
                )
                existing_names = {row[0] for row in existing_capabilities.fetchall()}

                # Only insert new capabilities
                new_capabilities = []
                for capability_name, capability_info in capabilities.items():
                    if capability_name not in existing_names:
                        new_capabilities.append(
                            AgentCapabilityRegistry(
                                agent_id=agent_id,
                                agent_type=capability_info.get("type", "unknown"),
                                capability_name=capability_name,
                                capability_type=capability_info.get("type", "unknown"),
                                capability_description=capability_info.get(
                                    "description", ""
                                ),
                                proficiency_score=capability_info.get(
                                    "proficiency", 0.8
                                ),
                            )
                        )

                if new_capabilities:
                    session.add_all(new_capabilities)
                    await session.commit()
                    logger.debug(
                        f"Batch registered {len(new_capabilities)} capabilities for {agent_id}"
                    )
                else:
                    logger.debug(f"All capabilities already exist for {agent_id}")

            logger.info(
                f"📝 Registered agent for coordination (optimized): {agent_id} with {len(capabilities)} capabilities"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register agent (optimized): {e}")
            return False

    async def register_agent_capability(
        self,
        agent_id: str,
        agent_type: str,
        capability_name: str,
        capability_type: str,
        capability_description: str,
        proficiency_score: float = 0.5,
    ) -> bool:
        """Register an agent capability in the database.

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (market, executive, content, logistics)
            capability_name: Name of the capability
            capability_type: Type of capability (analysis, optimization, etc.)
            capability_description: Description of the capability
            proficiency_score: Initial proficiency score (0.0 to 1.0)

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            async with self.database.get_session() as session:
                # Check if capability already exists
                existing_capability = await session.execute(
                    select(AgentCapabilityRegistry).where(
                        AgentCapabilityRegistry.agent_id == agent_id,
                        AgentCapabilityRegistry.capability_name == capability_name,
                    )
                )

                if existing_capability.scalar_one_or_none():
                    # Update existing capability
                    await session.execute(
                        update(AgentCapabilityRegistry)
                        .where(
                            AgentCapabilityRegistry.agent_id == agent_id,
                            AgentCapabilityRegistry.capability_name == capability_name,
                        )
                        .values(
                            capability_description=capability_description,
                            proficiency_score=proficiency_score,
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                else:
                    # Create new capability registration
                    capability_record = AgentCapabilityRegistry(
                        agent_id=agent_id,
                        agent_type=agent_type,
                        capability_name=capability_name,
                        capability_type=capability_type,
                        capability_description=capability_description,
                        proficiency_score=proficiency_score,
                    )
                    session.add(capability_record)

                await session.commit()

                # Update parent coordinator's agent registry
                if agent_id not in self.registered_agents:
                    self.registered_agents[agent_id] = {}

                self.registered_agents[agent_id][capability_name] = {
                    "type": capability_type,
                    "description": capability_description,
                    "proficiency": proficiency_score,
                }

                logger.debug(
                    f"Registered capability {capability_name} for agent {agent_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to register agent capability: {e}")
            return False

    async def get_coordination_history(
        self,
        limit: int = 50,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get coordination history from database.

        Args:
            limit: Maximum number of records to return
            agent_id: Optional filter by agent ID
            status: Optional filter by coordination status

        Returns:
            List of coordination history records
        """
        try:
            async with self.database.get_session() as session:
                query = (
                    select(CoordinationState)
                    .where(CoordinationState.coordinator_id == self.coordinator_id)
                    .order_by(CoordinationState.started_at.desc())
                    .limit(limit)
                )

                if status:
                    query = query.where(CoordinationState.coordination_status == status)

                result = await session.execute(query)
                coordination_records = result.scalars().all()

                history = []
                for record in coordination_records:
                    # Filter by agent_id if specified
                    if agent_id and agent_id not in record.assigned_agents:
                        continue

                    history.append(
                        {
                            "coordination_id": str(record.id),
                            "task_id": record.task_id,
                            "coordination_type": record.coordination_type,
                            "task_description": record.task_description,
                            "assigned_agents": record.assigned_agents,
                            "status": record.coordination_status,
                            "started_at": record.started_at.isoformat(),
                            "completed_at": (
                                record.completed_at.isoformat()
                                if record.completed_at
                                else None
                            ),
                            "execution_time_ms": record.execution_time_ms,
                            "step_results": record.step_results,
                            "error_message": record.error_message,
                        }
                    )

                return history

        except Exception as e:
            logger.error(f"Failed to get coordination history: {e}")
            return []

    async def _ensure_tables_exist(self):
        """Ensure coordination database tables exist."""
        try:
            # Tables are created by the main database initialization
            # This is a placeholder for any coordinator-specific table setup
            pass
        except Exception as e:
            logger.error(f"Failed to ensure coordination tables exist: {e}")
            raise

    async def _load_active_coordination_states(self):
        """Load active coordination states from database with performance optimization."""
        try:
            # Performance optimization: Check cache first
            cache_key = f"active_states_{self.coordinator_id}"
            if cache_key in self._initialization_cache:
                logger.debug("Active coordination states already loaded (cached)")
                return

            async with self.database.get_session() as session:
                # Performance optimization: Limit query and only get essential fields
                result = await session.execute(
                    select(
                        CoordinationState.task_id, CoordinationState.coordination_status
                    )
                    .where(
                        CoordinationState.coordinator_id == self.coordinator_id,
                        CoordinationState.coordination_status.in_(
                            ["pending", "active"]
                        ),
                    )
                    .limit(50)  # Limit to prevent excessive loading
                )

                active_states = result.fetchall()

                # Only cache task IDs for now, load full state when needed
                for task_id, status in active_states:
                    self.coordination_cache[task_id] = {
                        "status": status,
                        "loaded": False,
                    }
                    logger.debug(f"Cached active coordination state: {task_id}")

                logger.info(f"Cached {len(active_states)} active coordination states")

                # Cache the result
                self._initialization_cache[cache_key] = True

        except Exception as e:
            logger.error(f"Failed to load active coordination states: {e}")

    async def _register_coordinator_capabilities(self):
        """Register coordinator capabilities in the database."""
        try:
            coordinator_capabilities = [
                (
                    "sequential_coordination",
                    "coordination",
                    "Sequential agent task execution",
                ),
                (
                    "parallel_coordination",
                    "coordination",
                    "Parallel agent task execution",
                ),
                (
                    "hierarchical_coordination",
                    "coordination",
                    "Hierarchical agent coordination",
                ),
                (
                    "consensus_coordination",
                    "coordination",
                    "Consensus-based agent coordination",
                ),
                (
                    "competitive_coordination",
                    "coordination",
                    "Competitive agent coordination",
                ),
            ]

            for (
                capability_name,
                capability_type,
                description,
            ) in coordinator_capabilities:
                await self.register_agent_capability(
                    agent_id=self.coordinator_id,
                    agent_type="coordinator",
                    capability_name=capability_name,
                    capability_type=capability_type,
                    capability_description=description,
                    proficiency_score=0.8,
                )

            logger.debug(
                f"Registered coordinator capabilities for {self.coordinator_id}"
            )

        except Exception as e:
            logger.error(f"Failed to register coordinator capabilities: {e}")

    async def _register_coordinator_capabilities_optimized(self):
        """Register coordinator capabilities in the database with batch operations."""
        try:
            # Performance optimization: Check if capabilities already exist
            cache_key = f"coordinator_capabilities_{self.coordinator_id}"
            if cache_key in self._initialization_cache:
                logger.debug("Coordinator capabilities already registered (cached)")
                return

            coordinator_capabilities = [
                (
                    "sequential_coordination",
                    "coordination",
                    "Sequential agent task execution",
                ),
                (
                    "parallel_coordination",
                    "coordination",
                    "Parallel agent task execution",
                ),
                (
                    "hierarchical_coordination",
                    "coordination",
                    "Hierarchical agent coordination",
                ),
                (
                    "consensus_coordination",
                    "coordination",
                    "Consensus-based agent coordination",
                ),
                (
                    "competitive_coordination",
                    "coordination",
                    "Competitive agent coordination",
                ),
            ]

            # Performance optimization: Batch insert capabilities
            async with self.database.get_session() as session:
                # Check existing capabilities first
                existing_capabilities = await session.execute(
                    select(AgentCapabilityRegistry.capability_name).where(
                        AgentCapabilityRegistry.agent_id == self.coordinator_id
                    )
                )
                existing_names = {row[0] for row in existing_capabilities.fetchall()}

                # Only insert new capabilities
                new_capabilities = []
                for (
                    capability_name,
                    capability_type,
                    description,
                ) in coordinator_capabilities:
                    if capability_name not in existing_names:
                        new_capabilities.append(
                            AgentCapabilityRegistry(
                                agent_id=self.coordinator_id,
                                agent_type="coordinator",
                                capability_name=capability_name,
                                capability_type=capability_type,
                                capability_description=description,
                                proficiency_score=0.8,
                            )
                        )

                if new_capabilities:
                    session.add_all(new_capabilities)
                    await session.commit()
                    logger.debug(
                        f"Batch registered {len(new_capabilities)} coordinator capabilities"
                    )
                else:
                    logger.debug("All coordinator capabilities already exist")

            # Cache the result
            self._initialization_cache[cache_key] = True

        except Exception as e:
            logger.error(
                f"Failed to register coordinator capabilities (optimized): {e}"
            )
            raise

    async def _store_coordination_state(
        self,
        coordination_id: str,
        task: CoordinationTask,
        status: str,
        current_step: int,
        step_results: List[Dict[str, Any]],
    ):
        """Store coordination state in database."""
        try:
            async with self.database.get_session() as session:
                coordination_record = CoordinationState(
                    id=uuid.UUID(coordination_id),
                    coordinator_id=self.coordinator_id,
                    coordination_type=task.coordination_strategy.value,
                    task_id=task.task_id,
                    task_description=task.description,
                    task_context=getattr(
                        task, "context", {}
                    ),  # Handle missing context attribute
                    assigned_agents=task.assigned_agents,
                    agent_capabilities=task.required_capabilities,
                    coordination_status=status,
                    current_step=current_step,
                    total_steps=(
                        len(task.assigned_agents)
                        if task.coordination_strategy == CoordinationStrategy.SEQUENTIAL
                        else 1
                    ),
                    step_results=step_results,
                )

                session.add(coordination_record)
                await session.commit()

                # Cache the coordination state
                self.coordination_cache[task.task_id] = coordination_record

                logger.debug(f"Stored coordination state: {coordination_id}")

        except Exception as e:
            logger.error(f"Failed to store coordination state: {e}")
            raise

    async def _update_coordination_state(
        self,
        coordination_id: str,
        status: Optional[str] = None,
        current_step: Optional[int] = None,
        step_results: Optional[List[Dict[str, Any]]] = None,
        final_result: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ):
        """Update coordination state in database."""
        try:
            async with self.database.get_session() as session:
                update_values = {"last_updated": datetime.now(timezone.utc)}

                if status:
                    update_values["coordination_status"] = status
                    if status in ["completed", "failed"]:
                        update_values["completed_at"] = datetime.now(timezone.utc)

                if current_step is not None:
                    update_values["current_step"] = current_step

                if step_results is not None:
                    update_values["step_results"] = step_results

                if execution_time_ms is not None:
                    update_values["execution_time_ms"] = execution_time_ms

                if error_message is not None:
                    update_values["error_message"] = error_message

                if final_result is not None:
                    # Store final result in coordination metadata
                    update_values["coordination_metadata"] = {
                        "final_result": final_result,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }

                await session.execute(
                    update(CoordinationState)
                    .where(CoordinationState.id == uuid.UUID(coordination_id))
                    .values(**update_values)
                )

                await session.commit()
                logger.debug(f"Updated coordination state: {coordination_id}")

        except Exception as e:
            logger.error(f"Failed to update coordination state: {e}")

    async def _update_coordination_metrics(
        self, task: CoordinationTask, result: Dict[str, Any], execution_time: float
    ):
        """Update coordination metrics and agent performance."""
        try:
            # Update parent coordinator metrics
            await super()._update_coordination_metrics(task, result, execution_time)

            # Update agent capability metrics in database
            if result.get("success"):
                for agent_id in task.assigned_agents:
                    await self._update_agent_capability_metrics(
                        agent_id=agent_id,
                        capability_name=task.coordination_strategy.value,
                        success=True,
                        execution_time_ms=int(execution_time * 1000),
                    )

            logger.debug(f"Updated coordination metrics for task {task.task_id}")

        except Exception as e:
            logger.error(f"Failed to update coordination metrics: {e}")

    async def _update_agent_capability_metrics(
        self, agent_id: str, capability_name: str, success: bool, execution_time_ms: int
    ):
        """Update agent capability performance metrics."""
        try:
            async with self.database.get_session() as session:
                # Get current capability record
                result = await session.execute(
                    select(AgentCapabilityRegistry).where(
                        AgentCapabilityRegistry.agent_id == agent_id,
                        AgentCapabilityRegistry.capability_name == capability_name,
                    )
                )

                capability_record = result.scalar_one_or_none()
                if not capability_record:
                    return  # Capability not registered

                # Calculate updated metrics
                total_executions = capability_record.total_executions + 1
                successful_executions = (
                    capability_record.success_rate * capability_record.total_executions
                    + (1 if success else 0)
                )
                new_success_rate = successful_executions / total_executions

                # Calculate new average execution time
                total_time = (
                    capability_record.average_execution_time_ms
                    * capability_record.total_executions
                    + execution_time_ms
                )
                new_avg_time = int(total_time / total_executions)

                # Update capability record
                await session.execute(
                    update(AgentCapabilityRegistry)
                    .where(
                        AgentCapabilityRegistry.agent_id == agent_id,
                        AgentCapabilityRegistry.capability_name == capability_name,
                    )
                    .values(
                        success_rate=new_success_rate,
                        average_execution_time_ms=new_avg_time,
                        total_executions=total_executions,
                        last_used=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                )

                await session.commit()
                logger.debug(
                    f"Updated capability metrics for {agent_id}:{capability_name}"
                )

        except Exception as e:
            logger.error(f"Failed to update agent capability metrics: {e}")
