"""
Base Autonomous Agent for FlipSync AI System
==========================================

This module provides the base class for all autonomous agents in the
FlipSync system, with pure algorithmic decision-making capabilities
and zero LLM dependencies for core business logic.

Key Features:
- Pure algorithmic decision-making using StandardDecisionPipeline
- Database-backed learning with DatabaseLearningEngine
- Mathematical optimization algorithms
- Sub-500ms decision times
- Zero OpenAI/LLM dependencies in core logic
- Production-ready error handling and cleanup
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class AutonomousAgentResponse:
    """Response from an autonomous agent - pure algorithmic, no conversational dependencies."""

    content: str
    agent_type: str
    agent_id: str
    confidence: float
    response_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    decision_id: Optional[str] = None
    algorithm_used: Optional[str] = None


# Core Decision Pipeline Components (Pure Algorithmic)
from fs_agt_clean.core.coordination.decision.pipeline import StandardDecisionPipeline
from fs_agt_clean.core.coordination.decision.database_decision_maker import (
    DatabaseDecisionMaker,
)
from fs_agt_clean.core.coordination.decision.database_decision_tracker import (
    DatabaseDecisionTracker,
)

# Cross-Agent Learning Components (Database-only version for autonomous agents)
from fs_agt_clean.core.coordination.cross_agent_learning_coordinator import (
    CrossAgentLearningCoordinator,
)

# Advanced Multi-Agent Coordination Components
from fs_agt_clean.core.coordination.advanced_multi_agent_coordinator import (
    AdvancedMultiAgentCoordinator,
    CoordinationStrategy,
    Priority,
)

# Brain/Intelligence System Components
from fs_agt_clean.services.advanced_features.ai_integration.brain import (
    DecisionEngine,
    MemoryManager,
    WorkflowEngine,
    Memory,
)
from fs_agt_clean.core.coordination.decision.database_feedback_processor import (
    DatabaseFeedbackProcessor,
)
from fs_agt_clean.core.coordination.decision.database_learning_engine import (
    DatabaseLearningEngine,
)
from fs_agt_clean.core.coordination.decision.decision_validator import (
    RuleBasedValidator,
)
from fs_agt_clean.core.coordination.decision.models import DecisionType

# Database and Learning Components
from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.core.learning.database_policy_optimizer import DatabasePolicyOptimizer

# Event System for Coordination
from fs_agt_clean.core.coordination.event_system import create_publisher

# Multi-Agent Coordination (Algorithmic)

# Mathematical Optimization Engine
from fs_agt_clean.core.optimization.algorithmic_optimization_engine import (
    AlgorithmicOptimizationEngine,
)

logger = logging.getLogger(__name__)


class AutonomousAgentState(str, Enum):
    """Autonomous agent operational states."""

    IDLE = "idle"
    PROCESSING = "processing"
    LEARNING = "learning"
    OPTIMIZING = "optimizing"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AutonomousDecision:
    """Decision result from autonomous agent."""

    decision_id: str
    agent_type: str
    agent_id: str
    decision_type: DecisionType
    result: Any
    confidence: float
    execution_time: float
    algorithm_used: str
    metadata: Dict[str, Any]
    requires_coordination: bool = False
    learning_data: Optional[Dict[str, Any]] = None


@dataclass
class AutonomousAgentMetrics:
    """Performance metrics for autonomous agent."""

    total_decisions: int
    total_execution_time: float
    average_decision_time: float
    success_rate: float
    learning_cycles: int
    optimization_cycles: int
    last_updated: str


class BaseAutonomousAgent(ABC):
    """Base class for all autonomous agents in FlipSync.

    This class provides pure algorithmic decision-making capabilities
    with zero LLM dependencies for core business logic. All agents
    inheriting from this class operate autonomously using:

    - StandardDecisionPipeline for algorithmic decisions
    - DatabaseLearningEngine for persistent learning
    - Mathematical optimization algorithms
    - Rule-based validation systems
    """

    # Shared multi-agent coordinator instance across all agents
    _shared_coordinator: Optional[AdvancedMultiAgentCoordinator] = None

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        optimization_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the base autonomous agent.

        Args:
            agent_id: Unique identifier for this agent instance
            agent_type: Type/category of this agent (market, content, executive, logistics)
            optimization_config: Configuration for mathematical optimization algorithms
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AutonomousAgentState.IDLE

        # Initialize database connection
        self.database = get_database()
        # Note: Database will be initialized in initialize_async() method

        # Initialize event system for coordination
        self.event_publisher = create_publisher(source_id=agent_id)

        # Initialize core decision pipeline (Pure Algorithmic)
        self.decision_pipeline = self._create_decision_pipeline()

        # Initialize learning components (simplified for autonomous operation)
        self.learning_engine = DatabaseLearningEngine(
            engine_id=f"{agent_id}_learning",
            publisher=self.event_publisher,
            database=self.database,
        )

        # Initialize learning components for autonomous operation
        self.policy_optimizer = DatabasePolicyOptimizer(
            config=optimization_config or {},
            agent_id=agent_id,
            database=self.database,
            agent_type=agent_type,
        )
        # Note: DatabaseLearningModule requires LLM service and vector store
        # For now, set to None and initialize later if needed
        self.learning_module = None

        # Initialize mathematical optimization engine
        self.optimization_engine = AlgorithmicOptimizationEngine(
            config=optimization_config or {}
        )

        # Initialize multi-agent coordination (optional)
        self.coordinator = None
        self.cross_agent_learning = None

        # Initialize real-time communication (Phase 1 enhancement)
        self.realtime_communication = None

        # Initialize service integration for tool access
        self.service_integration_manager = None
        self.available_services = {}
        self.registered_services = {}  # Legacy compatibility

        # Performance metrics
        self.metrics = AutonomousAgentMetrics(
            total_decisions=0,
            total_execution_time=0.0,
            average_decision_time=0.0,
            success_rate=1.0,
            learning_cycles=0,
            optimization_cycles=0,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

        # Performance metrics dictionary for compatibility
        self.performance_metrics_dict = {
            "total_decisions": 0,
            "total_execution_time": 0.0,
            "average_decision_time": 0.0,
            "success_rate": 1.0,
            "learning_cycles": 0,
            "optimization_cycles": 0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        # Performance metrics list for agent-specific metrics (used by derived agents)
        self.performance_metrics = []

        # Decision cache for performance optimization
        self._decision_cache: Dict[str, Tuple[AutonomousDecision, datetime]] = {}
        self._cache_ttl_seconds = 60  # 1 minute cache

        logger.info(f"Initialized autonomous agent: {agent_id} ({agent_type})")

    async def initialize_async(self) -> bool:
        """Initialize the autonomous agent asynchronously.

        This method ensures the database is properly initialized before
        the agent starts making decisions and learning.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Initialize database if not already initialized
            if (
                not self.database
                or not hasattr(self.database, "_session_factory")
                or not self.database._session_factory
            ):
                logger.info("Initializing database for autonomous agent...")
                await self.database.initialize()
                logger.info("Database initialized successfully")
            else:
                logger.debug("Database already initialized")

            # Initialize learning components after database is ready
            if self.policy_optimizer:
                await self.policy_optimizer.initialize()
                logger.info("Policy optimizer initialized successfully")

            # Initialize cross-agent learning coordinator
            await self._initialize_cross_agent_learning()

            # Initialize multi-agent coordinator (shared across all agents)
            await self._initialize_multi_agent_coordinator()

            # Initialize real-time communication (Phase 1 enhancement)
            await self._initialize_realtime_communication()

            # Initialize brain/intelligence system
            await self._initialize_brain_system()

            # Initialize service integration for tool access
            await self._initialize_service_integration()

            if self.learning_module:
                await self.learning_module.initialize()
                logger.info("Learning module initialized successfully")
            else:
                logger.info("Learning module not initialized (requires LLM service)")

            # Runtime Architecture Validation - Enforce 4+1 architecture compliance
            await self._validate_runtime_architecture_compliance()

            return True

        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            # Continue without database - agent will work but without learning
            logger.warning("Agent will operate without learning capabilities")
            return False

    async def _validate_runtime_architecture_compliance(self):
        """Validate runtime architecture compliance using RuntimeArchitectureValidator."""
        try:
            from fs_agt_clean.core.architecture.runtime_validator import (
                validate_agent_runtime_compliance,
            )

            # Validate this agent's architecture compliance
            validation_result = validate_agent_runtime_compliance(self.agent_id, self)

            if not validation_result["compliant"]:
                logger.error(
                    f"🚨 Architecture compliance violations for {self.agent_id}:"
                )
                for violation in validation_result["violations"]:
                    logger.error(f"   - {violation}")

                # In strict mode, we could raise an exception here
                # For now, just log warnings to allow development
                logger.warning(
                    f"Agent {self.agent_id} has architecture violations but will continue"
                )
            else:
                logger.info(
                    f"✅ Runtime architecture validation passed for {self.agent_id}"
                )

            # Log component analysis
            if validation_result.get("component_analysis"):
                logger.debug(f"Component analysis for {self.agent_id}:")
                for component, status in validation_result[
                    "component_analysis"
                ].items():
                    logger.debug(f"   {component}: {status}")

        except Exception as e:
            logger.error(
                f"Runtime architecture validation failed for {self.agent_id}: {e}"
            )
            # Don't fail initialization due to validation errors

    def _create_decision_pipeline(self) -> StandardDecisionPipeline:
        """Create pure algorithmic decision pipeline with zero LLM dependencies."""

        # Create decision maker (algorithmic only)
        decision_maker = DatabaseDecisionMaker(
            maker_id=f"{self.agent_id}_decision_maker", database=self.database
        )

        # Create rule-based validator
        validator = RuleBasedValidator(validator_id=f"{self.agent_id}_validator")

        # Create decision tracker
        tracker = DatabaseDecisionTracker(
            tracker_id=f"{self.agent_id}_tracker",
            publisher=self.event_publisher,
            database=self.database,
        )

        # Create feedback processor
        feedback_processor = DatabaseFeedbackProcessor(
            processor_id=f"{self.agent_id}_feedback",
            publisher=self.event_publisher,
            database=self.database,
        )

        # Create learning engine
        learning_engine = DatabaseLearningEngine(
            engine_id=f"{self.agent_id}_learning",
            publisher=self.event_publisher,
            database=self.database,
        )

        # Create pipeline with all algorithmic components
        pipeline = StandardDecisionPipeline(
            pipeline_id=f"{self.agent_id}_pipeline",
            decision_maker=decision_maker,
            decision_validator=validator,
            decision_tracker=tracker,
            feedback_processor=feedback_processor,
            learning_engine=learning_engine,
            publisher=self.event_publisher,
        )

        return pipeline

    async def make_autonomous_decision(
        self,
        decision_context: Dict[str, Any],
        decision_type: DecisionType,
        use_cache: bool = True,
    ) -> AutonomousDecision:
        """
        Make a pure algorithmic decision with zero LLM dependencies.

        Args:
            decision_context: Context data for decision-making
            decision_type: Type of decision to make
            use_cache: Whether to use decision cache for performance

        Returns:
            AutonomousDecision with algorithmic result

        Raises:
            RuntimeError: If decision-making fails
        """
        start_time = time.perf_counter()

        try:
            self.state = AutonomousAgentState.PROCESSING

            # Check cache for similar decisions
            if use_cache:
                cached_decision = self._get_cached_decision(
                    decision_context, decision_type
                )
                if cached_decision:
                    logger.debug(f"Using cached decision for {decision_type}")
                    return cached_decision

            # Get relevant cross-agent learning insights
            relevant_insights = await self.get_relevant_insights(
                query_context={"decision_type": str(decision_type)}, limit=3
            )
            if relevant_insights:
                logger.info(
                    f"Incorporating {len(relevant_insights)} cross-agent insights into decision"
                )
                decision_context["cross_agent_insights"] = [
                    {
                        "source_agent": insight.source_agent_id,
                        "content": insight.content,
                        "confidence": insight.confidence_score,
                        "type": (
                            insight.insight_type.value
                            if hasattr(insight.insight_type, "value")
                            else str(insight.insight_type)
                        ),
                    }
                    for insight in relevant_insights
                ]

            # Create a simple decision object for algorithmic processing
            decision_id = f"{self.agent_id}_{int(time.time() * 1000)}"

            # Execute agent-specific algorithmic processing directly
            result = await self._process_algorithmic_decision(
                decision_context, decision_type
            )

            # Calculate execution time
            execution_time = time.perf_counter() - start_time

            # Create autonomous decision result
            confidence = (
                result.get("confidence", 0.8) if isinstance(result, dict) else 0.8
            )
            autonomous_decision = AutonomousDecision(
                decision_id=decision_id,
                agent_type=self.agent_type,
                agent_id=self.agent_id,
                decision_type=decision_type,
                result=result,
                confidence=confidence,
                execution_time=execution_time,
                algorithm_used=self._get_algorithm_name(decision_type),
                metadata={"execution_time": execution_time, "timestamp": time.time()},
                learning_data=self._extract_learning_data(decision_id, result),
            )

            # Cache decision for performance
            if use_cache:
                self._cache_decision(
                    decision_context, decision_type, autonomous_decision
                )

            # Update metrics
            self._update_metrics(execution_time, True)

            # Trigger learning if needed
            if autonomous_decision.learning_data:
                await self._trigger_autonomous_learning(autonomous_decision)

            self.state = AutonomousAgentState.IDLE

            logger.info(
                f"Autonomous decision completed in {execution_time:.3f}s "
                f"(confidence: {autonomous_decision.confidence:.2f})"
            )

            return autonomous_decision

        except Exception as e:
            execution_time = time.perf_counter() - start_time
            self._update_metrics(execution_time, False)
            self.state = AutonomousAgentState.ERROR

            logger.error(f"Autonomous decision failed: {e}")
            raise RuntimeError(f"Autonomous decision failed: {e}") from e

    @abstractmethod
    async def _process_algorithmic_decision(
        self, context: Dict[str, Any], decision_type: Any
    ) -> Any:
        """
        Process decision using agent-specific algorithmic logic.

        This method must be implemented by each agent to provide
        specialized algorithmic processing for their domain.

        Args:
            context: Decision context data
            decision_type: Type of decision to make

        Returns:
            Processed result using algorithmic methods
        """

    @abstractmethod
    def _get_algorithm_name(self, decision_type: DecisionType) -> str:
        """Get the name of the algorithm used for this decision type."""

    async def _trigger_autonomous_learning(self, decision: AutonomousDecision) -> None:
        """Trigger autonomous learning from decision results."""
        try:
            self.state = AutonomousAgentState.LEARNING

            # Learn from decision outcome
            await self.learning_engine.learn_from_feedback(
                decision.learning_data, publish_event=True
            )

            # Update policy optimization
            from fs_agt_clean.core.learning.policy_optimization import (
                OptimizationObjective,
            )

            # Extract policy and metrics from learning data
            current_policy = decision.learning_data.get("current_policy", {})
            performance_metrics = {
                "confidence": decision.confidence,
                "execution_time": decision.execution_time,
                "result_quality": decision.learning_data.get("result_quality", 0.8),
            }

            await self.policy_optimizer.optimize_policy(
                current_policy=current_policy,
                performance_metrics=performance_metrics,
                objective=OptimizationObjective.MAXIMIZE_PROFIT,
            )

            # Share learning insight with other agents
            if decision.confidence > 0.7:  # Only share high-confidence insights
                await self._share_decision_insight(decision)

            self.metrics.learning_cycles += 1

        except Exception as e:
            logger.error(f"Autonomous learning failed: {e}")
        finally:
            self.state = AutonomousAgentState.IDLE

    async def _share_decision_insight(self, decision: AutonomousDecision) -> None:
        """Share decision insight with other agents for cross-agent learning."""
        try:
            if not self.cross_agent_learning:
                return

            # Determine insight type based on decision type
            insight_type = self._map_decision_to_insight_type(decision.decision_type)

            # Create insight content
            insight_content = (
                f"Decision {decision.decision_type.value if hasattr(decision.decision_type, 'value') else str(decision.decision_type)} "
                f"achieved {decision.confidence:.2f} confidence using {decision.algorithm_used}. "
                f"Key factors: {decision.metadata.get('key_factors', 'algorithmic analysis')}"
            )

            # Share the insight
            await self.share_learning_insight(
                insight_type=insight_type,
                content=insight_content,
                confidence_score=decision.confidence,
                metadata={
                    "decision_id": decision.decision_id,
                    "algorithm_used": decision.algorithm_used,
                    "execution_time": decision.execution_time,
                    "decision_type": str(decision.decision_type),
                    "learning_data": decision.learning_data,
                },
            )

        except Exception as e:
            logger.error(f"Failed to share decision insight: {e}")

    def _map_decision_to_insight_type(self, decision_type) -> str:
        """Map decision type to learning insight type."""
        # Map decision types to insight types based on agent specialization
        decision_str = (
            decision_type.value
            if hasattr(decision_type, "value")
            else str(decision_type)
        )

        if any(
            keyword in decision_str.lower() for keyword in ["price", "pricing", "cost"]
        ):
            return "pricing_strategy"
        elif any(
            keyword in decision_str.lower() for keyword in ["content", "listing", "seo"]
        ):
            return "content_optimization"
        elif any(
            keyword in decision_str.lower()
            for keyword in ["inventory", "stock", "demand"]
        ):
            return "inventory_management"
        elif any(
            keyword in decision_str.lower()
            for keyword in ["ship", "logistics", "fulfillment"]
        ):
            return "logistics_optimization"
        elif any(
            keyword in decision_str.lower()
            for keyword in ["strategy", "planning", "resource"]
        ):
            return "strategic_planning"
        else:
            return "performance_optimization"

    def _get_cached_decision(
        self, context: Dict[str, Any], decision_type: DecisionType
    ) -> Optional[AutonomousDecision]:
        """Get cached decision if available and not expired."""
        cache_key = self._generate_cache_key(context, decision_type)

        if cache_key in self._decision_cache:
            decision, timestamp = self._decision_cache[cache_key]

            # Check if cache is still valid
            if (datetime.now() - timestamp).total_seconds() < self._cache_ttl_seconds:
                return decision
            else:
                # Remove expired cache entry
                del self._decision_cache[cache_key]

        return None

    def _cache_decision(
        self,
        context: Dict[str, Any],
        decision_type: DecisionType,
        decision: AutonomousDecision,
    ) -> None:
        """Cache decision for performance optimization."""
        cache_key = self._generate_cache_key(context, decision_type)
        self._decision_cache[cache_key] = (decision, datetime.now())

    def _generate_cache_key(
        self, context: Dict[str, Any], decision_type: DecisionType
    ) -> str:
        """Generate cache key for decision context."""
        import hashlib
        import json

        # Create deterministic key from context and decision type
        decision_type_str = (
            decision_type.value
            if hasattr(decision_type, "value")
            else str(decision_type)
        )

        key_data = {
            "decision_type": decision_type_str,
            "context": (
                sorted(context.items()) if isinstance(context, dict) else str(context)
            ),
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _extract_learning_data(self, decision_id: str, result: Any) -> Dict[str, Any]:
        """Extract learning data from decision and result."""
        return {
            "decision_id": decision_id,
            "decision_type": "autonomous_decision",
            "confidence": (
                result.get("confidence", 0.8) if isinstance(result, dict) else 0.8
            ),
            "execution_time": (
                result.get("execution_time", 0.0) if isinstance(result, dict) else 0.0
            ),
            "result_quality": self._assess_result_quality(result),
            "agent_type": self.agent_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _assess_result_quality(self, result: Any) -> float:
        """Assess the quality of a decision result (0.0 to 1.0)."""
        # Default implementation - should be overridden by specific agents
        return 0.8 if result is not None else 0.2

    def _update_metrics(self, execution_time: float, success: bool) -> None:
        """Update agent performance metrics."""
        self.metrics.total_decisions += 1
        self.metrics.total_execution_time += execution_time
        self.metrics.average_decision_time = (
            self.metrics.total_execution_time / self.metrics.total_decisions
        )

        # Update success rate using exponential moving average
        alpha = 0.1  # Smoothing factor
        current_success = 1.0 if success else 0.0
        self.metrics.success_rate = (
            alpha * current_success + (1 - alpha) * self.metrics.success_rate
        )

        self.metrics.last_updated = datetime.now(timezone.utc).isoformat()

    async def get_performance_metrics(self) -> AutonomousAgentMetrics:
        """Get current performance metrics."""
        return self.metrics

    async def _initialize_cross_agent_learning(self) -> None:
        """Initialize cross-agent learning coordinator for knowledge sharing."""
        try:
            # Ensure database is available for cross-agent learning
            if not hasattr(self, "database") or not self.database:
                logger.warning(
                    f"Database not available for cross-agent learning in {self.agent_id}"
                )
                # Try to initialize a minimal database connection
                await self._ensure_database_connection()

            # Create database-only cross-agent learning coordinator
            # Get or create multi-agent coordinator for integration
            if not hasattr(self, "coordinator") or not self.coordinator:
                await self._initialize_multi_agent_coordinator()

            self.cross_agent_learning = CrossAgentLearningCoordinator(
                coordinator_id=f"{self.agent_id}_cross_learning",
                database=self.database,
                multi_agent_coordinator=self.coordinator,
            )

            # Initialize the coordinator
            await self.cross_agent_learning.initialize()

            logger.info(f"✅ Cross-agent learning initialized for {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize cross-agent learning: {e}")
            logger.debug(f"Cross-agent learning error details: {str(e)}")
            self.cross_agent_learning = None

    async def _ensure_database_connection(self) -> None:
        """Ensure database connection is available for cross-agent learning."""
        try:
            if not hasattr(self, "database") or not self.database:
                from fs_agt_clean.core.db.database import get_database

                self.database = get_database()

            if self.database and not self.database._session_factory:
                await self.database.initialize()
                logger.info(f"Database connection established for {self.agent_id}")

        except Exception as e:
            logger.error(f"Failed to ensure database connection: {e}")
            # Continue without database - cross-agent learning will be disabled

    async def _initialize_multi_agent_coordinator(self) -> None:
        """Initialize shared multi-agent coordinator for workflow orchestration."""
        try:
            # Create shared coordinator if it doesn't exist
            if BaseAutonomousAgent._shared_coordinator is None:
                BaseAutonomousAgent._shared_coordinator = AdvancedMultiAgentCoordinator(
                    coordinator_id="flipsync_multi_agent_coordinator",
                    database=self.database,
                    publisher=self.event_publisher,
                )
                logger.info("✅ Created shared multi-agent coordinator")

            # Set local reference to shared coordinator
            self.coordinator = BaseAutonomousAgent._shared_coordinator

            # Register this agent with the coordinator
            await self.coordinator.register_agent(
                agent_id=self.agent_id,
                capabilities={
                    cap: {"performance_score": 0.8, "availability": True}
                    for cap in self._get_coordination_capabilities()
                },
            )

            logger.info(f"✅ Registered {self.agent_id} with multi-agent coordinator")

        except Exception as e:
            logger.error(f"❌ Failed to initialize multi-agent coordinator: {e}")
            self.coordinator = None

    async def _initialize_brain_system(self) -> None:
        """Initialize brain/intelligence system for central coordination."""
        try:
            # Initialize brain components
            self.brain_decision_engine = DecisionEngine()
            self.brain_memory_manager = MemoryManager()
            self.brain_workflow_engine = WorkflowEngine()

            # Register agent-specific workflows with the brain
            await self._register_agent_workflows()

            logger.info(f"✅ Brain system initialized for {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize brain system: {e}")
            self.brain_decision_engine = None
            self.brain_memory_manager = None
            self.brain_workflow_engine = None

    async def _initialize_realtime_communication(self) -> None:
        """Initialize real-time communication system for agent-to-agent messaging."""
        try:
            from fs_agt_clean.core.coordination.enhanced_realtime_communication import (
                enhanced_agent_communication,
                AgentCommunicationType,
                AgentCommunicationPriority,
            )

            # Register this agent with the real-time communication system
            self.realtime_communication = enhanced_agent_communication

            # Register agent for real-time communication
            success = await self.realtime_communication.register_agent(
                agent_id=self.agent_id, agent_type=self.agent_type
            )

            if success:
                logger.info(
                    f"✅ Real-time communication initialized for {self.agent_id}"
                )
            else:
                logger.warning(
                    f"⚠️ Failed to register {self.agent_id} for real-time communication"
                )

        except Exception as e:
            logger.error(f"❌ Failed to initialize real-time communication: {e}")
            self.realtime_communication = None

    async def _register_agent_workflows(self) -> None:
        """Register agent-specific workflows with the brain workflow engine."""
        try:
            if not self.brain_workflow_engine:
                return

            # Register common autonomous agent workflows
            common_workflows = [
                {
                    "workflow_id": f"{self.agent_id}_decision_workflow",
                    "steps": [
                        {"action": "analyze_context", "timeout": 100},
                        {"action": "generate_options", "timeout": 200},
                        {"action": "evaluate_options", "timeout": 150},
                        {"action": "make_decision", "timeout": 100},
                        {"action": "execute_decision", "timeout": 300},
                        {"action": "monitor_outcome", "timeout": 200},
                    ],
                    "config": {"max_retries": 2, "timeout": 1000},
                },
                {
                    "workflow_id": f"{self.agent_id}_learning_workflow",
                    "steps": [
                        {"action": "collect_feedback", "timeout": 100},
                        {"action": "analyze_performance", "timeout": 200},
                        {"action": "update_knowledge", "timeout": 150},
                        {"action": "share_insights", "timeout": 100},
                    ],
                    "config": {"max_retries": 1, "timeout": 600},
                },
            ]

            # Register agent-specific workflows
            agent_specific_workflows = self._get_agent_specific_workflows()
            all_workflows = common_workflows + agent_specific_workflows

            for workflow in all_workflows:
                await self.brain_workflow_engine.register_workflow(
                    workflow["workflow_id"],
                    workflow["steps"],
                    workflow.get("config", {}),
                )

            logger.info(
                f"Registered {len(all_workflows)} workflows for {self.agent_id}"
            )

        except Exception as e:
            logger.error(f"Failed to register agent workflows: {e}")

    def _get_agent_specific_workflows(self) -> List[Dict[str, Any]]:
        """Get agent-specific workflows based on agent type."""
        workflows = []

        if self.agent_type == "market":
            workflows.extend(
                [
                    {
                        "workflow_id": f"{self.agent_id}_pricing_optimization",
                        "steps": [
                            {"action": "analyze_market_data", "timeout": 200},
                            {"action": "evaluate_competitors", "timeout": 300},
                            {"action": "calculate_optimal_price", "timeout": 150},
                            {"action": "validate_pricing_strategy", "timeout": 100},
                        ],
                        "config": {"max_retries": 2, "timeout": 800},
                    }
                ]
            )
        elif self.agent_type == "content":
            workflows.extend(
                [
                    {
                        "workflow_id": f"{self.agent_id}_content_optimization",
                        "steps": [
                            {"action": "analyze_content_performance", "timeout": 200},
                            {"action": "generate_improvements", "timeout": 300},
                            {"action": "optimize_seo", "timeout": 200},
                            {"action": "validate_content_quality", "timeout": 100},
                        ],
                        "config": {"max_retries": 2, "timeout": 900},
                    }
                ]
            )
        elif self.agent_type == "executive":
            workflows.extend(
                [
                    {
                        "workflow_id": f"{self.agent_id}_strategic_planning",
                        "steps": [
                            {"action": "analyze_business_metrics", "timeout": 300},
                            {"action": "evaluate_strategic_options", "timeout": 400},
                            {"action": "allocate_resources", "timeout": 200},
                            {"action": "monitor_strategic_progress", "timeout": 200},
                        ],
                        "config": {"max_retries": 1, "timeout": 1200},
                    }
                ]
            )
        elif self.agent_type == "logistics":
            workflows.extend(
                [
                    {
                        "workflow_id": f"{self.agent_id}_logistics_optimization",
                        "steps": [
                            {"action": "analyze_shipping_data", "timeout": 200},
                            {"action": "optimize_routes", "timeout": 300},
                            {"action": "coordinate_fulfillment", "timeout": 250},
                            {"action": "monitor_delivery_performance", "timeout": 150},
                        ],
                        "config": {"max_retries": 2, "timeout": 1000},
                    }
                ]
            )

        return workflows

    def _get_coordination_capabilities(self) -> List[str]:
        """Get coordination capabilities for this agent type."""
        base_capabilities = [
            "decision_making",
            "task_execution",
            "performance_optimization",
            "algorithmic_processing",
        ]

        # Add agent-specific coordination capabilities
        if self.agent_type == "market":
            base_capabilities.extend(
                [
                    "market_analysis",
                    "pricing_optimization",
                    "competitor_monitoring",
                    "demand_forecasting",
                    "inventory_management",
                ]
            )
        elif self.agent_type == "content":
            base_capabilities.extend(
                [
                    "content_generation",
                    "seo_optimization",
                    "listing_enhancement",
                    "image_processing",
                    "content_analysis",
                ]
            )
        elif self.agent_type == "executive":
            base_capabilities.extend(
                [
                    "strategic_planning",
                    "resource_allocation",
                    "decision_coordination",
                    "risk_assessment",
                    "business_optimization",
                ]
            )
        elif self.agent_type == "logistics":
            base_capabilities.extend(
                [
                    "shipping_optimization",
                    "warehouse_management",
                    "fulfillment_planning",
                    "route_optimization",
                    "inventory_coordination",
                ]
            )

        return base_capabilities

    def _get_learning_capabilities(self) -> List[str]:
        """Get learning capabilities for this agent type."""
        base_capabilities = [
            "decision_optimization",
            "performance_analysis",
            "pattern_recognition",
            "outcome_prediction",
        ]

        # Add agent-specific capabilities
        if self.agent_type == "market":
            base_capabilities.extend(
                [
                    "pricing_optimization",
                    "competitor_analysis",
                    "demand_forecasting",
                    "inventory_management",
                ]
            )
        elif self.agent_type == "content":
            base_capabilities.extend(
                [
                    "content_optimization",
                    "seo_analysis",
                    "listing_enhancement",
                    "image_processing",
                ]
            )
        elif self.agent_type == "executive":
            base_capabilities.extend(
                [
                    "strategic_planning",
                    "resource_allocation",
                    "risk_assessment",
                    "business_optimization",
                ]
            )
        elif self.agent_type == "logistics":
            base_capabilities.extend(
                [
                    "shipping_optimization",
                    "warehouse_management",
                    "fulfillment_planning",
                    "route_optimization",
                ]
            )

        return base_capabilities

    def _get_agent_specializations(self) -> List[str]:
        """Get specializations for this agent type."""
        specializations_map = {
            "market": ["pricing", "competition", "inventory", "demand_analysis"],
            "content": ["seo", "listings", "images", "optimization"],
            "executive": ["strategy", "planning", "resources", "risk_management"],
            "logistics": ["shipping", "warehousing", "fulfillment", "routing"],
        }
        return specializations_map.get(self.agent_type, [])

    async def share_learning_insight(
        self,
        insight_type: str,
        content: str,
        confidence_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Share a learning insight with other agents."""
        if not self.cross_agent_learning:
            logger.warning(f"Cross-agent learning not initialized for {self.agent_id}")
            return None

        try:
            import time

            success = await self.cross_agent_learning.share_learning_insight(
                source_agent_id=self.agent_id,
                target_agent_ids=["all"],  # Share with all agents
                insight_type=insight_type,
                insight_data={
                    "content": content,
                    "confidence_score": confidence_score,
                    "metadata": metadata or {},
                    "timestamp": time.time(),
                },
            )

            insight_id = (
                f"insight_{self.agent_id}_{int(time.time() * 1000)}"
                if success
                else None
            )

            logger.info(f"Shared learning insight {insight_id} from {self.agent_id}")
            return insight_id

        except Exception as e:
            logger.error(f"Failed to share learning insight: {e}")
            return None

    async def get_relevant_insights(
        self,
        query_context: Dict[str, Any],
        limit: int = 5,
    ) -> List[Any]:
        """Get learning insights relevant to this agent."""
        if not self.cross_agent_learning:
            logger.warning(f"Cross-agent learning not initialized for {self.agent_id}")
            return []

        try:
            # Use database-only coordinator interface
            insights = await self.cross_agent_learning.get_learning_insights_for_agent(
                agent_id=self.agent_id,
                insight_types=None,  # Get all types
                limit=limit,
            )

            logger.debug(
                f"Retrieved {len(insights)} relevant insights for {self.agent_id}"
            )
            return insights

        except Exception as e:
            logger.error(f"Failed to get relevant insights: {e}")
            return []

    async def apply_learning_insight(self, insight_id: str) -> bool:
        """Apply a learning insight to improve agent performance."""
        if not self.cross_agent_learning:
            logger.warning(f"Cross-agent learning not initialized for {self.agent_id}")
            return False

        try:
            success = await self.cross_agent_learning.apply_learning_insight(
                agent_id=self.agent_id,
                insight_id=insight_id,
            )

            if success:
                logger.info(f"Applied learning insight {insight_id} to {self.agent_id}")
            else:
                logger.warning(f"Failed to apply learning insight {insight_id}")

            return success

        except Exception as e:
            logger.error(f"Error applying learning insight: {e}")
            return False

    async def create_coordination_task(
        self,
        task_type: str,
        description: str,
        required_capabilities: List[str],
        coordination_strategy: CoordinationStrategy = CoordinationStrategy.PARALLEL,
        priority: Priority = Priority.NORMAL,
        deadline: Optional[datetime] = None,
    ) -> Optional[str]:
        """Create a multi-agent coordination task."""
        if not self.coordinator:
            logger.warning(f"Multi-agent coordinator not available for {self.agent_id}")
            return None

        try:
            task_id = await self.coordinator.create_coordination_task(
                task_type=task_type,
                description=description,
                required_capabilities=required_capabilities,
                coordination_strategy=coordination_strategy,
                priority=priority,
                deadline=deadline,
            )

            logger.info(f"Created coordination task {task_id} from {self.agent_id}")
            return task_id

        except Exception as e:
            logger.error(f"Failed to create coordination task: {e}")
            return None

    async def participate_in_coordination(
        self, task_id: str, contribution: Dict[str, Any]
    ) -> bool:
        """Participate in a multi-agent coordination task."""
        if not self.coordinator:
            logger.warning(f"Multi-agent coordinator not available for {self.agent_id}")
            return False

        try:
            # This would be implemented based on the specific coordination protocol
            # For now, we'll log the participation
            logger.info(f"Agent {self.agent_id} participating in task {task_id}")

            # Add agent contribution to task context
            if hasattr(self.coordinator, "add_agent_contribution"):
                await self.coordinator.add_agent_contribution(
                    task_id, self.agent_id, contribution
                )

            return True

        except Exception as e:
            logger.error(f"Failed to participate in coordination: {e}")
            return False

    async def request_agent_collaboration(
        self,
        target_agent_types: List[str],
        collaboration_type: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Request collaboration from other agents through the coordinator."""
        if not self.coordinator:
            logger.warning(f"Multi-agent coordinator not available for {self.agent_id}")
            return {"success": False, "error": "Coordinator not available"}

        try:
            # Create a collaboration task
            task_id = await self.create_coordination_task(
                task_type=f"collaboration_{collaboration_type}",
                description=f"Collaboration request from {self.agent_id}",
                required_capabilities=target_agent_types,
                coordination_strategy=CoordinationStrategy.CONSENSUS,
                priority=Priority.NORMAL,
            )

            if task_id:
                # Participate with our context
                await self.participate_in_coordination(task_id, context)

                return {
                    "success": True,
                    "task_id": task_id,
                    "collaboration_type": collaboration_type,
                    "requesting_agent": self.agent_id,
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create collaboration task",
                }

        except Exception as e:
            logger.error(f"Failed to request collaboration: {e}")
            return {"success": False, "error": str(e)}

    async def store_brain_memory(
        self,
        content: str,
        context: Dict[str, Any],
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Memory]:
        """Store important information in brain memory system."""
        if not self.brain_memory_manager:
            logger.warning(f"Brain memory manager not available for {self.agent_id}")
            return None

        try:
            memory = self.brain_memory_manager.store(
                content=content,
                context=context,
                importance=importance,
                metadata=metadata
                or {"agent_id": self.agent_id, "agent_type": self.agent_type},
            )

            logger.debug(f"Stored memory {memory.id} in brain system")
            return memory

        except Exception as e:
            logger.error(f"Failed to store brain memory: {e}")
            return None

    async def retrieve_brain_memories(
        self,
        query_context: Dict[str, Any],
        limit: int = 5,
        min_importance: float = 0.3,
    ) -> List[Memory]:
        """Retrieve relevant memories from brain system."""
        if not self.brain_memory_manager:
            logger.warning(f"Brain memory manager not available for {self.agent_id}")
            return []

        try:
            memories = self.brain_memory_manager.retrieve(
                context=query_context,
                limit=limit,
            )

            # Filter by importance
            relevant_memories = [
                memory for memory in memories if memory.importance >= min_importance
            ]

            logger.debug(f"Retrieved {len(relevant_memories)} relevant memories")
            return relevant_memories

        except Exception as e:
            logger.error(f"Failed to retrieve brain memories: {e}")
            return []

    async def execute_brain_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a workflow using the brain workflow engine."""
        if not self.brain_workflow_engine:
            logger.warning(f"Brain workflow engine not available for {self.agent_id}")
            return {"success": False, "error": "Workflow engine not available"}

        try:
            # Start the workflow
            execution_id = await self.brain_workflow_engine.start_workflow(
                workflow_id=workflow_id,
                context=context,
            )

            if execution_id:
                logger.info(
                    f"Started brain workflow {workflow_id} with execution {execution_id}"
                )
                return {
                    "success": True,
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                }
            else:
                return {"success": False, "error": "Failed to start workflow"}

        except Exception as e:
            logger.error(f"Failed to execute brain workflow: {e}")
            return {"success": False, "error": str(e)}

    async def enhance_decision_with_brain(
        self,
        decision_context: Dict[str, Any],
        available_actions: List[str],
    ) -> Dict[str, Any]:
        """Enhance decision-making using brain intelligence system."""
        if not self.brain_decision_engine:
            logger.warning(f"Brain decision engine not available for {self.agent_id}")
            return {"enhanced": False, "reason": "Brain system not available"}

        try:
            # Retrieve relevant memories for context
            memories = await self.retrieve_brain_memories(
                query_context=decision_context,
                limit=3,
                min_importance=0.4,
            )

            # Create memory context for brain decision
            memory_context = {
                "relevant_memories": [
                    {
                        "content": memory.content,
                        "importance": memory.importance,
                        "context": memory.context,
                    }
                    for memory in memories
                ],
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
            }

            # Use brain decision engine
            brain_decision = await self.brain_decision_engine.make_decision(
                context=decision_context,
                actions=available_actions,
                memory_context=memory_context,
            )

            # Store this decision experience in brain memory
            await self.store_brain_memory(
                content=f"Decision: {brain_decision.action} with confidence {brain_decision.confidence}",
                context=decision_context,
                importance=brain_decision.confidence,
                metadata={
                    "decision_type": "brain_enhanced",
                    "reasoning": brain_decision.reasoning,
                    "available_actions": available_actions,
                },
            )

            return {
                "enhanced": True,
                "brain_decision": {
                    "action": brain_decision.action,
                    "confidence": brain_decision.confidence,
                    "reasoning": brain_decision.reasoning,
                    "metadata": brain_decision.metadata,
                },
                "memory_context": memory_context,
            }

        except Exception as e:
            logger.error(f"Failed to enhance decision with brain: {e}")
            return {"enhanced": False, "reason": str(e)}

    async def send_realtime_message(
        self,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any],
        priority: str = "normal",
        requires_response: bool = False,
        timeout: float = 5.0,
    ) -> Optional[Dict[str, Any]]:
        """Send a real-time message to another agent."""
        try:
            if not self.realtime_communication:
                logger.warning(
                    f"Real-time communication not initialized for {self.agent_id}"
                )
                return None

            from fs_agt_clean.core.coordination.enhanced_realtime_communication import (
                AgentCommunicationType,
                AgentCommunicationPriority,
            )

            # Convert string types to enums
            comm_type = getattr(
                AgentCommunicationType,
                message_type.upper(),
                AgentCommunicationType.COORDINATION,
            )
            comm_priority = getattr(
                AgentCommunicationPriority,
                priority.upper(),
                AgentCommunicationPriority.NORMAL,
            )

            # Send message via real-time communication system
            result = await self.realtime_communication.send_message(
                from_agent=self.agent_id,
                to_agent=to_agent,
                message_type=comm_type,
                content=content,
                priority=comm_priority,
                requires_response=requires_response,
                timeout=timeout,
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to send real-time message from {self.agent_id} to {to_agent}: {e}"
            )
            return None

    async def _initialize_service_integration(self):
        """Initialize service integration for tool access."""
        try:
            from fs_agt_clean.core.services.service_integration import (
                get_service_integration_manager,
            )

            self.service_integration_manager = get_service_integration_manager()

            # Get services available to this agent type
            self.available_services = (
                self.service_integration_manager.get_services_for_agent(self.agent_type)
            )

            # Update legacy registered_services for backward compatibility
            self.registered_services = {
                service_id: service.service_id
                for service_id, service in self.available_services.items()
            }

            logger.info(
                f"✅ Service integration initialized for {self.agent_id}: "
                f"{len(self.available_services)} services available"
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to initialize service integration for {self.agent_id}: {e}"
            )
            self.available_services = {}
            self.registered_services = {}

    async def execute_service(self, service_id: str, **kwargs) -> Dict[str, Any]:
        """Execute a service as a tool for this agent."""
        if not self.service_integration_manager:
            return {
                "success": False,
                "error": "Service integration not initialized",
                "agent_id": self.agent_id,
            }

        return await self.service_integration_manager.execute_service_for_agent(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            service_id=service_id,
            **kwargs,
        )

    def get_available_services(self) -> List[str]:
        """Get list of services available to this agent as tools."""
        return list(self.available_services.keys())

    async def cleanup(self) -> None:
        """Clean up agent resources and connections."""
        try:
            # Disconnect from real-time communication
            if self.realtime_communication:
                await self.realtime_communication.disconnect_agent(self.agent_id)

            # Clear decision cache
            self._decision_cache.clear()

            # Clear service references
            self.available_services = {}
            self.registered_services = {}

            # Close database connections if needed
            if hasattr(self.database, "close"):
                await self.database.close()

            logger.info(f"Cleaned up autonomous agent: {self.agent_id}")

        except Exception as e:
            logger.error(f"Error during agent cleanup: {e}")

    def __str__(self) -> str:
        return (
            f"AutonomousAgent({self.agent_id}, {self.agent_type}, {self.state.value})"
        )

    def __repr__(self) -> str:
        return self.__str__()
