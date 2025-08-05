"""
Autonomous Behavior Manager for FlipSync Agentic System

This module orchestrates autonomous agent behavior, enabling agents to proactively
monitor inventory, analyze markets, optimize pricing, and coordinate with other agents
without user input. Builds upon the existing sophisticated decision pipeline and
coordination infrastructure from Phases 1-4.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fs_agt_clean.core.coordination.database_multi_agent_coordinator import (
    DatabaseMultiAgentCoordinator,
)
from fs_agt_clean.core.coordination.cross_agent_learning_coordinator import (
    CrossAgentLearningCoordinator,
)
from fs_agt_clean.core.coordination.advanced_multi_agent_coordinator import (
    CoordinationTask,
    CoordinationStrategy,
)
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class AutonomousBehaviorManager:
    """Manages autonomous behavior for all FlipSync agents.

    This class orchestrates proactive agent actions including:
    - Autonomous inventory monitoring and management
    - Proactive market analysis and competitive intelligence
    - Autonomous pricing optimization based on market conditions
    - Autonomous content optimization for listings
    - Cross-agent coordination and learning without user intervention
    """

    def __init__(
        self,
        manager_id: str,
        database: Database,
        multi_agent_coordinator: DatabaseMultiAgentCoordinator,
        learning_coordinator: CrossAgentLearningCoordinator,
        monitoring_interval_seconds: int = 300,  # 5 minutes default
        performance_target_seconds: float = 0.272,  # Maintain established performance target
    ):
        """Initialize the autonomous behavior manager.

        Args:
            manager_id: Unique identifier for this behavior manager
            database: Database instance for persistence
            multi_agent_coordinator: Coordinator for multi-agent tasks
            learning_coordinator: Coordinator for cross-agent learning
            monitoring_interval_seconds: Interval between autonomous monitoring cycles
            performance_target_seconds: Target decision time performance
        """
        self.manager_id = manager_id
        self.database = database
        self.multi_agent_coordinator = multi_agent_coordinator
        self.learning_coordinator = learning_coordinator
        self.monitoring_interval = monitoring_interval_seconds
        self.performance_target = performance_target_seconds

        # Autonomous behavior state
        self.is_running = False
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        self.autonomous_tasks: Dict[str, asyncio.Task] = {}
        self.behavior_metrics: Dict[str, Any] = {
            "total_autonomous_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "average_decision_time": 0.0,
            "last_monitoring_cycle": None,
            "agents_active": 0,
            "coordination_events": 0,
            "learning_insights_generated": 0,
        }

        # Performance optimization: Cache initialization state
        self._initialized = False
        self._initialization_cache = {}

        logger.info(f"Initialized AutonomousBehaviorManager {manager_id}")

    async def initialize(self) -> bool:
        """Initialize the autonomous behavior manager with performance optimizations.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Performance optimization: Skip if already initialized
            if self._initialized:
                logger.debug(
                    f"AutonomousBehaviorManager {self.manager_id} already initialized"
                )
                return True

            # Performance optimization: Run initialization tasks in parallel
            initialization_tasks = [
                self._verify_database_connectivity(),
                self.multi_agent_coordinator.initialize(),
                self._load_autonomous_state(),
            ]

            # Execute initialization tasks concurrently
            results = await asyncio.gather(
                *initialization_tasks, return_exceptions=True
            )

            # Check results
            db_connectivity = results[0]
            coordinator_ready = results[1]
            state_loaded = results[2]

            # Check for failures
            if isinstance(db_connectivity, Exception):
                logger.error(f"Database connectivity check failed: {db_connectivity}")
                return False

            if isinstance(coordinator_ready, Exception):
                logger.error(f"Coordinator initialization failed: {coordinator_ready}")
                return False
            elif not coordinator_ready:
                logger.error("Failed to initialize coordination systems")
                return False

            if isinstance(state_loaded, Exception):
                logger.error(f"State loading failed: {state_loaded}")
                return False

            self._initialized = True
            logger.info(
                f"✅ AutonomousBehaviorManager initialized for {self.manager_id} (optimized)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize AutonomousBehaviorManager: {e}")
            return False

    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        autonomous_capabilities: List[str],
        agent_instance: Any = None,
    ) -> bool:
        """Register an agent for autonomous behavior management.

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (market, executive, content, logistics)
            autonomous_capabilities: List of autonomous capabilities the agent supports
            agent_instance: Optional reference to the actual agent instance

        Returns:
            True if registration was successful, False otherwise
        """
        try:
            agent_config = {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "autonomous_capabilities": autonomous_capabilities,
                "agent_instance": agent_instance,
                "last_autonomous_action": None,
                "autonomous_actions_count": 0,
                "average_decision_time": 0.0,
                "registered_at": datetime.now(timezone.utc),
                "status": "active",
            }

            self.registered_agents[agent_id] = agent_config

            # Performance optimization: Register with coordination systems using batch operations
            capabilities_dict = {
                cap: {
                    "type": "autonomous",
                    "description": f"Autonomous {cap} capability",
                    "proficiency": 0.8,
                }
                for cap in autonomous_capabilities
            }

            await self.multi_agent_coordinator.register_agent_optimized(
                agent_id=agent_id,
                capabilities=capabilities_dict,
            )

            # Register with learning coordinator
            # Note: CrossAgentLearningCoordinator doesn't require initialization

            self.behavior_metrics["agents_active"] = len(self.registered_agents)

            logger.info(
                f"📝 Registered agent for autonomous behavior: {agent_id} ({agent_type})"
            )
            logger.info(f"   Capabilities: {autonomous_capabilities}")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False

    async def start_autonomous_behavior(self) -> bool:
        """Start autonomous behavior monitoring and execution.

        Returns:
            True if autonomous behavior started successfully, False otherwise
        """
        try:
            if self.is_running:
                logger.warning("Autonomous behavior already running")
                return True

            self.is_running = True

            # Start autonomous monitoring tasks for each agent type
            autonomous_tasks = [
                self._start_inventory_monitoring(),
                self._start_market_analysis(),
                self._start_pricing_optimization(),
                self._start_content_optimization(),
                self._start_coordination_monitoring(),
                self._start_learning_validation(),
            ]

            # Start all autonomous tasks
            for i, task_coro in enumerate(autonomous_tasks):
                task_name = [
                    "inventory_monitoring",
                    "market_analysis",
                    "pricing_optimization",
                    "content_optimization",
                    "coordination_monitoring",
                    "learning_validation",
                ][i]

                self.autonomous_tasks[task_name] = asyncio.create_task(task_coro)
                logger.info(f"🚀 Started autonomous task: {task_name}")

            logger.info(
                f"✅ Autonomous behavior started with {len(self.autonomous_tasks)} tasks"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start autonomous behavior: {e}")
            self.is_running = False
            return False

    async def stop_autonomous_behavior(self) -> bool:
        """Stop autonomous behavior monitoring and execution.

        Returns:
            True if autonomous behavior stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                logger.warning("Autonomous behavior not running")
                return True

            self.is_running = False

            # Cancel all autonomous tasks
            for task_name, task in self.autonomous_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                logger.info(f"🛑 Stopped autonomous task: {task_name}")

            self.autonomous_tasks.clear()

            logger.info("✅ Autonomous behavior stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to stop autonomous behavior: {e}")
            return False

    async def get_autonomous_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics on autonomous behavior performance.

        Returns:
            Dictionary containing autonomous behavior metrics
        """
        try:
            # Update current metrics
            self.behavior_metrics.update(
                {
                    "is_running": self.is_running,
                    "registered_agents": len(self.registered_agents),
                    "active_tasks": len(
                        [t for t in self.autonomous_tasks.values() if not t.done()]
                    ),
                    "uptime_seconds": (
                        (
                            datetime.now(timezone.utc)
                            - self.behavior_metrics.get(
                                "started_at", datetime.now(timezone.utc)
                            )
                        ).total_seconds()
                        if self.is_running
                        else 0
                    ),
                    "performance_target_met": self.behavior_metrics.get(
                        "average_decision_time", 0
                    )
                    <= self.performance_target,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Add agent-specific metrics
            agent_metrics = {}
            for agent_id, config in self.registered_agents.items():
                agent_metrics[agent_id] = {
                    "agent_type": config["agent_type"],
                    "autonomous_actions_count": config["autonomous_actions_count"],
                    "average_decision_time": config["average_decision_time"],
                    "last_autonomous_action": (
                        config["last_autonomous_action"].isoformat()
                        if config["last_autonomous_action"]
                        else None
                    ),
                    "status": config["status"],
                }

            self.behavior_metrics["agent_metrics"] = agent_metrics

            return self.behavior_metrics

        except Exception as e:
            logger.error(f"Failed to get autonomous metrics: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    async def _verify_database_connectivity(self):
        """Verify database connectivity for autonomous operations."""
        try:
            from sqlalchemy import text

            async with self.database.get_session() as session:
                # Simple connectivity test
                result = await session.execute(text("SELECT 1"))
                result.scalar()
                logger.debug("Database connectivity verified for autonomous operations")

        except Exception as e:
            logger.error(f"Database connectivity check failed: {e}")
            raise

    async def _load_autonomous_state(self):
        """Load existing autonomous behavior state from database."""
        try:
            # In a production implementation, this would load state from database
            # For now, initialize with default state
            self.behavior_metrics["started_at"] = datetime.now(timezone.utc)
            logger.debug("Autonomous behavior state loaded")

        except Exception as e:
            logger.error(f"Failed to load autonomous state: {e}")

    async def _start_inventory_monitoring(self):
        """Start autonomous inventory monitoring task."""
        logger.info("🔍 Starting autonomous inventory monitoring")

        while self.is_running:
            try:
                start_time = time.time()

                # Find agents with inventory monitoring capability
                inventory_agents = [
                    agent_id
                    for agent_id, config in self.registered_agents.items()
                    if "inventory_monitoring" in config["autonomous_capabilities"]
                ]

                for agent_id in inventory_agents:
                    agent_config = self.registered_agents[agent_id]
                    agent_instance = agent_config.get("agent_instance")

                    if agent_instance and hasattr(agent_instance, "check_inventory"):
                        # Simulate autonomous inventory check for test SKUs
                        test_skus = ["AUTO_SKU_001", "AUTO_SKU_002", "AUTO_SKU_003"]

                        for sku in test_skus:
                            try:
                                inventory_result = await agent_instance.check_inventory(
                                    sku
                                )

                                # Update metrics
                                decision_time = time.time() - start_time
                                self._update_agent_metrics(agent_id, decision_time)

                                logger.debug(
                                    f"✅ Autonomous inventory check: {agent_id} -> {sku}"
                                )

                            except Exception as e:
                                logger.error(
                                    f"Autonomous inventory check failed for {agent_id}/{sku}: {e}"
                                )
                                self.behavior_metrics["failed_actions"] += 1

                self.behavior_metrics["last_monitoring_cycle"] = datetime.now(
                    timezone.utc
                ).isoformat()

                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                logger.info("Inventory monitoring task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in inventory monitoring: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    def _update_agent_metrics(self, agent_id: str, decision_time: float):
        """Update metrics for an agent's autonomous action."""
        if agent_id in self.registered_agents:
            config = self.registered_agents[agent_id]
            config["autonomous_actions_count"] += 1
            config["last_autonomous_action"] = datetime.now(timezone.utc)

            # Update average decision time
            current_avg = config["average_decision_time"]
            count = config["autonomous_actions_count"]
            config["average_decision_time"] = (
                (current_avg * (count - 1)) + decision_time
            ) / count

            # Update global metrics
            self.behavior_metrics["total_autonomous_actions"] += 1
            self.behavior_metrics["successful_actions"] += 1

            # Update global average decision time
            total_actions = self.behavior_metrics["total_autonomous_actions"]
            current_global_avg = self.behavior_metrics["average_decision_time"]
            self.behavior_metrics["average_decision_time"] = (
                (current_global_avg * (total_actions - 1)) + decision_time
            ) / total_actions

    async def _start_market_analysis(self):
        """Start autonomous market analysis task."""
        logger.info("📊 Starting autonomous market analysis")

        while self.is_running:
            try:
                start_time = time.time()

                # Find agents with market analysis capability
                market_agents = [
                    agent_id
                    for agent_id, config in self.registered_agents.items()
                    if "market_analysis" in config["autonomous_capabilities"]
                ]

                for agent_id in market_agents:
                    agent_config = self.registered_agents[agent_id]
                    agent_instance = agent_config.get("agent_instance")

                    if agent_instance and hasattr(
                        agent_instance, "monitor_competitors"
                    ):
                        try:
                            # Autonomous competitive analysis
                            analysis_result = await agent_instance.monitor_competitors(
                                {
                                    "product_id": "AUTO_PRODUCT_001",
                                    "marketplace": "ebay",
                                }
                            )

                            # Update metrics
                            decision_time = time.time() - start_time
                            self._update_agent_metrics(agent_id, decision_time)

                            logger.debug(f"✅ Autonomous market analysis: {agent_id}")

                        except Exception as e:
                            logger.error(
                                f"Autonomous market analysis failed for {agent_id}: {e}"
                            )
                            self.behavior_metrics["failed_actions"] += 1

                # Wait for next analysis cycle (longer interval for market analysis)
                await asyncio.sleep(self.monitoring_interval * 2)

            except asyncio.CancelledError:
                logger.info("Market analysis task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in market analysis: {e}")
                await asyncio.sleep(120)  # Wait before retrying

    async def _start_pricing_optimization(self):
        """Start autonomous pricing optimization task."""
        logger.info("💰 Starting autonomous pricing optimization")

        while self.is_running:
            try:
                start_time = time.time()

                # Find agents with pricing optimization capability
                pricing_agents = [
                    agent_id
                    for agent_id, config in self.registered_agents.items()
                    if "pricing_optimization" in config["autonomous_capabilities"]
                ]

                for agent_id in pricing_agents:
                    agent_config = self.registered_agents[agent_id]
                    agent_instance = agent_config.get("agent_instance")

                    if agent_instance and hasattr(agent_instance, "make_decision"):
                        try:
                            # Autonomous pricing decision
                            pricing_context = {
                                "product_id": "AUTO_PRODUCT_001",
                                "current_price": 29.99,
                                "competitor_prices": [27.99, 31.99, 28.49],
                                "market_conditions": "competitive",
                                "inventory_level": "medium",
                            }

                            pricing_result = await agent_instance.make_decision(
                                decision_type="pricing_optimization",
                                context=pricing_context,
                            )

                            # Update metrics
                            decision_time = time.time() - start_time
                            self._update_agent_metrics(agent_id, decision_time)

                            logger.debug(
                                f"✅ Autonomous pricing optimization: {agent_id}"
                            )

                        except Exception as e:
                            logger.error(
                                f"Autonomous pricing optimization failed for {agent_id}: {e}"
                            )
                            self.behavior_metrics["failed_actions"] += 1

                # Wait for next pricing cycle
                await asyncio.sleep(self.monitoring_interval * 3)

            except asyncio.CancelledError:
                logger.info("Pricing optimization task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in pricing optimization: {e}")
                await asyncio.sleep(180)  # Wait before retrying

    async def _start_content_optimization(self):
        """Start autonomous content optimization task."""
        logger.info("📝 Starting autonomous content optimization")

        while self.is_running:
            try:
                start_time = time.time()

                # Find agents with content optimization capability
                content_agents = [
                    agent_id
                    for agent_id, config in self.registered_agents.items()
                    if "content_optimization" in config["autonomous_capabilities"]
                ]

                for agent_id in content_agents:
                    agent_config = self.registered_agents[agent_id]
                    agent_instance = agent_config.get("agent_instance")

                    if agent_instance and hasattr(agent_instance, "make_decision"):
                        try:
                            # Autonomous content optimization decision
                            content_context = {
                                "listing_id": "AUTO_LISTING_001",
                                "current_title": "Premium Electronics Device",
                                "current_description": "High-quality electronic device with advanced features",
                                "performance_metrics": {
                                    "views": 150,
                                    "clicks": 12,
                                    "conversions": 2,
                                },
                                "optimization_target": "conversion_rate",
                            }

                            content_result = await agent_instance.make_decision(
                                decision_type="content_optimization",
                                context=content_context,
                            )

                            # Update metrics
                            decision_time = time.time() - start_time
                            self._update_agent_metrics(agent_id, decision_time)

                            logger.debug(
                                f"✅ Autonomous content optimization: {agent_id}"
                            )

                        except Exception as e:
                            logger.error(
                                f"Autonomous content optimization failed for {agent_id}: {e}"
                            )
                            self.behavior_metrics["failed_actions"] += 1

                # Wait for next content optimization cycle
                await asyncio.sleep(self.monitoring_interval * 4)

            except asyncio.CancelledError:
                logger.info("Content optimization task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in content optimization: {e}")
                await asyncio.sleep(240)  # Wait before retrying

    async def _start_coordination_monitoring(self):
        """Start autonomous coordination monitoring task."""
        logger.info("🤝 Starting autonomous coordination monitoring")

        while self.is_running:
            try:
                # Check for coordination opportunities
                coordination_opportunities = (
                    await self._identify_coordination_opportunities()
                )

                for opportunity in coordination_opportunities:
                    try:
                        # Create autonomous coordination task
                        coordination_task = CoordinationTask(
                            task_id=f"auto_coord_{uuid.uuid4()}",
                            task_type=opportunity["task_type"],
                            description=f"Autonomous {opportunity['description']}",
                            assigned_agents=opportunity["agents"],
                            required_capabilities=opportunity["capabilities"],
                            coordination_strategy=CoordinationStrategy.CONSENSUS,
                        )

                        # Execute coordination
                        start_time = time.time()
                        result = await self.multi_agent_coordinator.coordinate_task(
                            coordination_task, store_in_database=True
                        )

                        time.time() - start_time
                        self.behavior_metrics["coordination_events"] += 1

                        logger.debug(
                            f"✅ Autonomous coordination: {opportunity['task_type']}"
                        )

                    except Exception as e:
                        logger.error(f"Autonomous coordination failed: {e}")
                        self.behavior_metrics["failed_actions"] += 1

                # Wait for next coordination monitoring cycle
                await asyncio.sleep(self.monitoring_interval * 2)

            except asyncio.CancelledError:
                logger.info("Coordination monitoring task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in coordination monitoring: {e}")
                await asyncio.sleep(120)  # Wait before retrying

    async def _start_learning_validation(self):
        """Start autonomous learning validation task."""
        logger.info("🧠 Starting autonomous learning validation")

        while self.is_running:
            try:
                # Generate learning insights between agents
                learning_opportunities = await self._identify_learning_opportunities()

                for opportunity in learning_opportunities:
                    try:
                        # Share learning insight
                        insight_shared = (
                            await self.learning_coordinator.share_learning_insight(
                                source_agent=opportunity["source_agent"],
                                insight_data=opportunity["insight_data"],
                            )
                        )

                        if insight_shared:
                            self.behavior_metrics["learning_insights_generated"] += 1
                            logger.debug(
                                f"✅ Autonomous learning insight: {opportunity['insight_type']}"
                            )

                    except Exception as e:
                        logger.error(f"Autonomous learning insight sharing failed: {e}")
                        self.behavior_metrics["failed_actions"] += 1

                # Wait for next learning validation cycle
                await asyncio.sleep(self.monitoring_interval * 3)

            except asyncio.CancelledError:
                logger.info("Learning validation task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in learning validation: {e}")
                await asyncio.sleep(180)  # Wait before retrying

    async def _identify_coordination_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for autonomous coordination between agents."""
        opportunities = []

        try:
            # Example coordination opportunities based on agent capabilities
            if len(self.registered_agents) >= 2:
                list(self.registered_agents.keys())

                # Inventory-pricing coordination opportunity
                market_agents = [
                    aid
                    for aid, config in self.registered_agents.items()
                    if config["agent_type"] == "market"
                ]
                executive_agents = [
                    aid
                    for aid, config in self.registered_agents.items()
                    if config["agent_type"] == "executive"
                ]

                if market_agents and executive_agents:
                    opportunities.append(
                        {
                            "task_type": "inventory_pricing_coordination",
                            "description": "coordinate inventory levels with pricing strategy",
                            "agents": [market_agents[0], executive_agents[0]],
                            "capabilities": [
                                "inventory_monitoring",
                                "strategic_planning",
                            ],
                        }
                    )

                # Content-market coordination opportunity
                content_agents = [
                    aid
                    for aid, config in self.registered_agents.items()
                    if config["agent_type"] == "content"
                ]

                if market_agents and content_agents:
                    opportunities.append(
                        {
                            "task_type": "content_market_coordination",
                            "description": "align content optimization with market analysis",
                            "agents": [market_agents[0], content_agents[0]],
                            "capabilities": ["market_analysis", "content_optimization"],
                        }
                    )

        except Exception as e:
            logger.error(f"Error identifying coordination opportunities: {e}")

        return opportunities

    async def _identify_learning_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for autonomous learning sharing between agents."""
        opportunities = []

        try:
            # Example learning opportunities based on agent types
            agent_types = {
                config["agent_type"] for config in self.registered_agents.values()
            }

            if "market" in agent_types and "executive" in agent_types:
                market_agents = [
                    aid
                    for aid, config in self.registered_agents.items()
                    if config["agent_type"] == "market"
                ]
                executive_agents = [
                    aid
                    for aid, config in self.registered_agents.items()
                    if config["agent_type"] == "executive"
                ]

                opportunities.append(
                    {
                        "source_agent": market_agents[0],
                        "target_agents": executive_agents,
                        "insight_type": "market_intelligence",
                        "insight_data": {
                            "market_trend": "increasing_demand",
                            "competitive_pressure": "moderate",
                            "price_sensitivity": 0.7,
                            "recommendation": "maintain_current_strategy",
                        },
                    }
                )

            if "content" in agent_types and "market" in agent_types:
                content_agents = [
                    aid
                    for aid, config in self.registered_agents.items()
                    if config["agent_type"] == "content"
                ]
                market_agents = [
                    aid
                    for aid, config in self.registered_agents.items()
                    if config["agent_type"] == "market"
                ]

                opportunities.append(
                    {
                        "source_agent": content_agents[0],
                        "target_agents": market_agents,
                        "insight_type": "content_performance",
                        "insight_data": {
                            "optimization_strategy": "keyword_enhancement",
                            "conversion_improvement": 0.15,
                            "engagement_metrics": {"clicks": 1.2, "views": 1.8},
                            "recommendation": "apply_to_similar_listings",
                        },
                    }
                )

        except Exception as e:
            logger.error(f"Error identifying learning opportunities: {e}")

        return opportunities
