"""
Autonomous Agent Manager for FlipSync 4+1 Architecture
=====================================================

Manages exactly 4 autonomous agents + 1 conversational interface:
- MarketAutonomousAgent (LLM-free market analysis)
- ContentAutonomousAgent (LLM-free content optimization)
- ExecutiveAutonomousAgent (LLM-free strategic decisions)
- LogisticsAutonomousAgent (LLM-free shipping optimization)
- StrategicChatService (Gemini-powered conversational interface)

Key Features:
- Strict 4+1 architecture compliance
- Zero LLM dependencies in autonomous agents
- <1000ms decision time targets
- Production-ready error handling
- Health monitoring and status reporting
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AutonomousAgentManager:
    """Manages the 4+1 FlipSync agent architecture with strict compliance."""

    def __init__(self):
        """Initialize the autonomous agent manager."""
        # Core 4 autonomous agents
        self.autonomous_agents: Dict[str, Any] = {}

        # +1 conversational interface
        self.conversational_interface: Optional[Any] = None

        # Agent health and status tracking
        self.agent_health: Dict[str, Dict[str, Any]] = {}
        self.last_health_check: Optional[datetime] = None
        self.initialization_status = "not_started"

        # Performance metrics
        self.performance_metrics = {
            "agent_initialization_time": {},
            "decision_times": {},
            "total_decisions": 0,
            "successful_decisions": 0,
        }

        logger.info("AutonomousAgentManager initialized for 4+1 architecture")

    async def initialize(self) -> bool:
        """Initialize all 4 autonomous agents + 1 conversational interface."""
        try:
            self.initialization_status = "initializing"
            start_time = time.perf_counter()

            logger.info("🚀 Starting 4+1 agent architecture initialization...")

            # Initialize the 4 autonomous agents concurrently
            autonomous_results = await asyncio.gather(
                self._initialize_market_agent(),
                self._initialize_content_agent(),
                self._initialize_executive_agent(),
                self._initialize_logistics_agent(),
                return_exceptions=True,
            )

            # Initialize the +1 conversational interface
            await self._initialize_conversational_interface()

            # Verify 4+1 architecture compliance
            if not self._verify_architecture_compliance():
                raise Exception("4+1 architecture compliance verification failed")

            # Perform initial health check
            await self._perform_health_check()

            initialization_time = time.perf_counter() - start_time
            self.initialization_status = "completed"

            logger.info(
                f"✅ 4+1 architecture initialization completed in {initialization_time:.2f}s"
            )
            logger.info(f"   - Autonomous agents: {len(self.autonomous_agents)}")
            logger.info(
                f"   - Conversational interface: {'✅' if self.conversational_interface else '❌'}"
            )

            return True

        except Exception as e:
            self.initialization_status = "failed"
            logger.error(f"❌ 4+1 architecture initialization failed: {e}")
            return False

    async def _initialize_market_agent(self) -> None:
        """Initialize MarketAutonomousAgent with LLM-free decision making."""
        try:
            from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent

            logger.info("🤖 Initializing MarketAutonomousAgent...")
            start_time = time.perf_counter()

            agent = MarketAutonomousAgent("market_agent")
            await asyncio.wait_for(agent.initialize_async(), timeout=20.0)

            initialization_time = time.perf_counter() - start_time
            self.performance_metrics["agent_initialization_time"][
                "market"
            ] = initialization_time

            self.autonomous_agents["market_agent"] = {
                "instance": agent,
                "type": "autonomous",
                "agent_class": "MarketAutonomousAgent",
                "status": "active",
                "llm_free": True,
                "initialized_at": datetime.now(timezone.utc),
                "initialization_time": initialization_time,
            }

            logger.info(
                f"✅ MarketAutonomousAgent initialized in {initialization_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize MarketAutonomousAgent: {e}")
            raise

    async def _initialize_content_agent(self) -> None:
        """Initialize ContentAutonomousAgent with LLM-free decision making."""
        try:
            from fs_agt_clean.agents.content.content_agent import ContentAutonomousAgent

            logger.info("🤖 Initializing ContentAutonomousAgent...")
            start_time = time.perf_counter()

            agent = ContentAutonomousAgent("content_agent")
            await asyncio.wait_for(agent.initialize_async(), timeout=20.0)

            initialization_time = time.perf_counter() - start_time
            self.performance_metrics["agent_initialization_time"][
                "content"
            ] = initialization_time

            self.autonomous_agents["content_agent"] = {
                "instance": agent,
                "type": "autonomous",
                "agent_class": "ContentAutonomousAgent",
                "status": "active",
                "llm_free": True,
                "initialized_at": datetime.now(timezone.utc),
                "initialization_time": initialization_time,
            }

            logger.info(
                f"✅ ContentAutonomousAgent initialized in {initialization_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize ContentAutonomousAgent: {e}")
            import traceback

            logger.error(
                f"ContentAgent initialization traceback: {traceback.format_exc()}"
            )
            # Don't raise - continue with other agents

    async def _initialize_executive_agent(self) -> None:
        """Initialize ExecutiveAutonomousAgent with LLM-free decision making."""
        try:
            from fs_agt_clean.agents.executive.executive_agent import (
                ExecutiveAutonomousAgent,
            )

            logger.info("🤖 Initializing ExecutiveAutonomousAgent...")
            start_time = time.perf_counter()

            agent = ExecutiveAutonomousAgent("executive_agent")
            await asyncio.wait_for(agent.initialize_async(), timeout=20.0)

            initialization_time = time.perf_counter() - start_time
            self.performance_metrics["agent_initialization_time"][
                "executive"
            ] = initialization_time

            self.autonomous_agents["executive_agent"] = {
                "instance": agent,
                "type": "autonomous",
                "agent_class": "ExecutiveAutonomousAgent",
                "status": "active",
                "llm_free": True,
                "initialized_at": datetime.now(timezone.utc),
                "initialization_time": initialization_time,
            }

            logger.info(
                f"✅ ExecutiveAutonomousAgent initialized in {initialization_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize ExecutiveAutonomousAgent: {e}")
            import traceback

            logger.error(
                f"ExecutiveAgent initialization traceback: {traceback.format_exc()}"
            )
            # Don't raise - continue with other agents

    async def _initialize_logistics_agent(self) -> None:
        """Initialize LogisticsAutonomousAgent with LLM-free decision making."""
        try:
            from fs_agt_clean.agents.logistics.logistics_agent import (
                LogisticsAutonomousAgent,
            )

            logger.info("🤖 Initializing LogisticsAutonomousAgent...")
            start_time = time.perf_counter()

            agent = LogisticsAutonomousAgent("logistics_agent")
            await asyncio.wait_for(agent.initialize_async(), timeout=20.0)

            initialization_time = time.perf_counter() - start_time
            self.performance_metrics["agent_initialization_time"][
                "logistics"
            ] = initialization_time

            self.autonomous_agents["logistics_agent"] = {
                "instance": agent,
                "type": "autonomous",
                "agent_class": "LogisticsAutonomousAgent",
                "status": "active",
                "llm_free": True,
                "initialized_at": datetime.now(timezone.utc),
                "initialization_time": initialization_time,
            }

            logger.info(
                f"✅ LogisticsAutonomousAgent initialized in {initialization_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize LogisticsAutonomousAgent: {e}")
            import traceback

            logger.error(
                f"LogisticsAgent initialization traceback: {traceback.format_exc()}"
            )
            # Don't raise - continue with other agents

    async def _initialize_conversational_interface(self) -> None:
        """Initialize StrategicChatService as the +1 conversational interface."""
        try:
            from fs_agt_clean.services.communication.strategic_chat_service import (
                StrategicChatService,
            )

            logger.info(
                "💬 Initializing StrategicChatService (conversational interface)..."
            )
            start_time = time.perf_counter()

            # Initialize with production budget
            chat_service = StrategicChatService(daily_budget=10.0)

            initialization_time = time.perf_counter() - start_time

            self.conversational_interface = {
                "instance": chat_service,
                "type": "conversational",
                "service_class": "StrategicChatService",
                "llm_provider": "gemini",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "initialization_time": initialization_time,
            }

            logger.info(
                f"✅ StrategicChatService initialized in {initialization_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize StrategicChatService: {e}")
            import traceback

            logger.error(
                f"StrategicChatService initialization traceback: {traceback.format_exc()}"
            )
            # Don't raise - conversational interface is optional

    def _verify_architecture_compliance(self) -> bool:
        """Verify strict 4+1 architecture compliance."""
        try:
            # Verify exactly 4 autonomous agents
            if len(self.autonomous_agents) != 4:
                logger.error(
                    f"❌ Expected 4 autonomous agents, found {len(self.autonomous_agents)}"
                )
                return False

            # Verify required autonomous agents exist
            required_agents = [
                "market_agent",
                "content_agent",
                "executive_agent",
                "logistics_agent",
            ]
            for agent_id in required_agents:
                if agent_id not in self.autonomous_agents:
                    logger.error(f"❌ Required autonomous agent missing: {agent_id}")
                    return False

                # Verify LLM-free compliance
                agent_info = self.autonomous_agents[agent_id]
                if not agent_info.get("llm_free", False):
                    logger.error(f"❌ Agent {agent_id} is not LLM-free")
                    return False

            # Verify conversational interface exists
            if not self.conversational_interface:
                logger.error(
                    "❌ Conversational interface (StrategicChatService) missing"
                )
                return False

            # Verify conversational interface uses Gemini
            if self.conversational_interface.get("llm_provider") != "gemini":
                logger.error("❌ Conversational interface must use Gemini exclusively")
                return False

            logger.info("✅ 4+1 architecture compliance verified")
            return True

        except Exception as e:
            logger.error(f"❌ Architecture compliance verification failed: {e}")
            return False

    async def _perform_health_check(self) -> None:
        """Perform health check on all agents."""
        try:
            self.last_health_check = datetime.now(timezone.utc)

            # Check autonomous agents
            for agent_id, agent_info in self.autonomous_agents.items():
                instance = agent_info.get("instance")
                if instance and hasattr(instance, "get_health_status"):
                    health = await instance.get_health_status()
                    self.agent_health[agent_id] = health
                else:
                    self.agent_health[agent_id] = {
                        "status": "unknown",
                        "last_check": self.last_health_check,
                    }

            # Check conversational interface
            if self.conversational_interface:
                chat_service = self.conversational_interface.get("instance")
                if chat_service and hasattr(chat_service, "usage_stats"):
                    stats = chat_service.usage_stats
                    self.agent_health["strategic_chat_service"] = {
                        "status": "healthy",
                        "usage_stats": stats,
                        "last_check": self.last_health_check,
                    }

            logger.info("✅ Health check completed for all agents")

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")

    def get_agent_instance(self, agent_id: str) -> Optional[Any]:
        """Get autonomous agent instance by ID."""
        agent_info = self.autonomous_agents.get(agent_id)
        return agent_info.get("instance") if agent_info else None

    def get_conversational_interface(self) -> Optional[Any]:
        """Get the conversational interface (StrategicChatService) instance."""
        return (
            self.conversational_interface.get("instance")
            if self.conversational_interface
            else None
        )

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the 4+1 architecture."""
        return {
            "architecture": "4+1",
            "initialization_status": self.initialization_status,
            "autonomous_agents": {
                agent_id: {
                    "status": info["status"],
                    "agent_class": info["agent_class"],
                    "llm_free": info["llm_free"],
                    "initialization_time": info["initialization_time"],
                }
                for agent_id, info in self.autonomous_agents.items()
            },
            "conversational_interface": {
                "status": (
                    self.conversational_interface["status"]
                    if self.conversational_interface
                    else "missing"
                ),
                "service_class": (
                    self.conversational_interface.get("service_class")
                    if self.conversational_interface
                    else None
                ),
                "llm_provider": (
                    self.conversational_interface.get("llm_provider")
                    if self.conversational_interface
                    else None
                ),
            },
            "health_check": {
                "last_check": (
                    self.last_health_check.isoformat()
                    if self.last_health_check
                    else None
                ),
                "agent_health": self.agent_health,
            },
            "performance_metrics": self.performance_metrics,
        }

    async def shutdown(self) -> None:
        """Shutdown all agents gracefully."""
        logger.info("🔄 Shutting down 4+1 agent architecture...")

        # Shutdown autonomous agents
        for agent_id, agent_info in self.autonomous_agents.items():
            try:
                instance = agent_info.get("instance")
                if instance and hasattr(instance, "close"):
                    await instance.close()
                logger.info(f"✅ {agent_id} shut down successfully")
            except Exception as e:
                logger.error(f"❌ Error shutting down {agent_id}: {e}")

        # Shutdown conversational interface
        if self.conversational_interface:
            try:
                chat_service = self.conversational_interface.get("instance")
                if chat_service and hasattr(chat_service, "close"):
                    await chat_service.close()
                logger.info("✅ StrategicChatService shut down successfully")
            except Exception as e:
                logger.error(f"❌ Error shutting down StrategicChatService: {e}")

        # Clear all references
        self.autonomous_agents.clear()
        self.conversational_interface = None
        self.agent_health.clear()

        logger.info("✅ 4+1 agent architecture shutdown complete")
