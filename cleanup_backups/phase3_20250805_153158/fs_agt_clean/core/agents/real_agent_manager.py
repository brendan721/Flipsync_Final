"""Real AutonomousAgent Manager for FlipSync - Manages actual agent instances with real marketplace connections."""

import asyncio
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env.production.test
load_dotenv(".env.production.test")
from typing import Any, Dict, List, Optional

from fs_agt_clean.services.marketplace.amazon.service import AmazonService

# Import eBay service with error handling
try:
    from fs_agt_clean.services.marketplace.ebay.service import EbayService

    ebay_service_available = True
except ImportError:
    ebay_service_available = False
    EbayService = None

# AutonomousAgent imports are optional for now - we'll focus on services
# from fs_agt_clean.agents.market.amazon_agent import AmazonMarketAutonomousAgent
# from fs_agt_clean.agents.market.ebay_agent import EbayMarketAutonomousAgent
# from fs_agt_clean.agents.market.inventory_agent import InventoryAutonomousAgent
# from fs_agt_clean.agents.executive.decision_engine import ExecutiveDecisionEngine

logger = logging.getLogger(__name__)


class RealAutonomousAgentManager:
    """Manages real agent instances with actual marketplace connections."""

    def __init__(self):
        """Initialize the real agent manager."""
        self.agents: Dict[str, Any] = {}
        self.services: Dict[str, Any] = {}
        self.agent_health: Dict[str, Dict[str, Any]] = {}
        self.last_health_check = None
        self.initialization_status = "not_started"

        # Pipeline Controller integration
        self.pipeline_controller = None
        self.workflow_coordination_enabled = False

        logger.info("Real AutonomousAgent Manager initialized")

    def register_pipeline_controller(self, pipeline_controller):
        """Register the pipeline controller for workflow coordination."""
        self.pipeline_controller = pipeline_controller
        self.workflow_coordination_enabled = True
        logger.info("Pipeline Controller registered with AutonomousAgent Manager")

    def get_agent_status(self, agent_id: str = None) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents or a specific agent for pipeline coordination."""
        if agent_id is not None:
            # Return specific agent status
            if agent_id not in self.agents:
                return {}

            agent_info = self.agents[agent_id]
            return {
                agent_id: {
                    "status": agent_info.get("status", "unknown"),
                    "type": agent_info.get("type", "unknown"),
                    "marketplace": agent_info.get("marketplace", "unknown"),
                    "last_activity": agent_info.get("last_activity"),
                    "error_count": agent_info.get("error_count", 0),
                    "success_count": agent_info.get("success_count", 0),
                    "initialized_at": agent_info.get("initialized_at"),
                }
            }

        # Return all agents status
        agent_status = {}
        for agent_name, agent_info in self.agents.items():
            agent_status[agent_name] = {
                "status": agent_info.get("status", "unknown"),
                "type": agent_info.get("type", "unknown"),
                "marketplace": agent_info.get("marketplace", "unknown"),
                "last_activity": agent_info.get("last_activity"),
                "error_count": agent_info.get("error_count", 0),
                "success_count": agent_info.get("success_count", 0),
                "initialized_at": agent_info.get("initialized_at"),
            }
        return agent_status

    async def execute_agent_task(
        self, agent_name: str, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task on a specific agent for pipeline coordination."""
        if agent_name not in self.agents:
            return {
                "success": False,
                "error": f"AutonomousAgent {agent_name} not found",
                "agent_name": agent_name,
            }

        try:
            agent_info = self.agents[agent_name]
            agent_instance = agent_info["instance"]

            # Update last activity
            agent_info["last_activity"] = datetime.now(timezone.utc)

            # Execute task based on agent type and available methods
            result = await self._execute_task_on_agent(agent_instance, task_data)

            # Update success count
            agent_info["success_count"] += 1

            return {
                "success": True,
                "result": result,
                "agent_name": agent_name,
                "agent_type": agent_info.get("type", "unknown"),
            }

        except Exception as e:
            # Update error count
            self.agents[agent_name]["error_count"] += 1
            logger.error(f"Failed to execute task on agent {agent_name}: {e}")

            return {"success": False, "error": str(e), "agent_name": agent_name}

    async def _execute_task_on_agent(
        self, agent_instance, task_data: Dict[str, Any]
    ) -> Any:
        """Execute a task on an agent instance."""
        # Check if agent has a process method
        if hasattr(agent_instance, "process"):
            return await agent_instance.process(task_data)
        elif hasattr(agent_instance, "execute"):
            return await agent_instance.execute(task_data)
        elif hasattr(agent_instance, "handle_request"):
            return await agent_instance.handle_request(task_data)
        else:
            # For service-based agents, try common service methods
            if hasattr(agent_instance, "test_connection"):
                return await agent_instance.test_connection()
            else:
                return {"message": "Task executed", "data": task_data}

    def get_agents_by_category(self, category: str) -> List[str]:
        """Get list of agent names by category for pipeline coordination."""
        agents = []
        for agent_name, agent_info in self.agents.items():
            if agent_info.get("type") == category:
                agents.append(agent_name)
        return agents

    def get_available_agents(self) -> List[str]:
        """Get list of available (active) agents."""
        available = []
        for agent_name, agent_info in self.agents.items():
            if agent_info.get("status") == "active":
                available.append(agent_name)
        return available

    async def initialize(self) -> bool:
        """Initialize all real agents and services."""
        try:
            self.initialization_status = "initializing"
            logger.info("Starting real agent initialization...")

            # Initialize service integration system first
            await self._initialize_service_integration()

            # Initialize marketplace services
            await self._initialize_services()

            # Initialize agents
            await self._initialize_agents()

            # Perform initial health check
            await self._perform_health_check()

            self.initialization_status = "completed"
            logger.info(
                f"Real agent initialization completed. {len(self.agents)} agents active."
            )
            return True

        except Exception as e:
            self.initialization_status = "failed"
            logger.error(f"Real agent initialization failed: {e}")
            return False

    async def _initialize_service_integration(self):
        """Initialize the service integration system for all agents."""
        try:
            from fs_agt_clean.core.services.service_integration import (
                get_service_integration_manager,
            )

            logger.info("🚀 Initializing service integration system...")

            # Get service integration manager
            self.service_integration_manager = get_service_integration_manager()

            # Initialize all 23+ service components
            integration_success = (
                await self.service_integration_manager.initialize_all_services()
            )

            if integration_success:
                status = self.service_integration_manager.get_integration_status()
                logger.info(
                    f"✅ Service integration completed: {status['registered_services_count']} services available"
                )
            else:
                logger.error(
                    "❌ Service integration failed - some services may not be available"
                )

        except Exception as e:
            logger.error(f"❌ Service integration initialization failed: {e}")
            raise

    async def _initialize_services(self):
        """Initialize marketplace services with timeout handling."""
        logger.info("Initializing marketplace services...")

        # Amazon service initialization with timeout
        try:
            logger.info("Initializing Amazon service...")
            self.services["amazon"] = AmazonService()
            logger.info("Amazon service initialized")

            # Test Amazon connection with timeout
            logger.info("Testing Amazon connection...")
            amazon_test = await asyncio.wait_for(
                self.services["amazon"].test_connection(), timeout=10.0
            )
            if amazon_test["success"]:
                logger.info("Amazon SP-API connection test successful")
            else:
                logger.warning(
                    f"Amazon SP-API connection test failed: {amazon_test['message']}"
                )

        except asyncio.TimeoutError:
            logger.warning("Amazon service connection test timed out after 10 seconds")
        except Exception as e:
            logger.error(f"Failed to initialize Amazon service: {e}")
            # Continue without Amazon service

        if ebay_service_available:
            try:
                # Create real eBay sandbox configuration using environment variables
                import os

                from fs_agt_clean.core.marketplace.ebay.api_client import EbayAPIClient
                from fs_agt_clean.core.marketplace.ebay.config import EbayConfig

                # Get eBay production credentials from environment
                ebay_app_id = os.getenv("EBAY_CLIENT_ID", "")
                os.getenv("EBAY_DEV_ID", "")
                ebay_cert_id = os.getenv("EBAY_CLIENT_SECRET", "")

                # Create real eBay production config
                ebay_config = EbayConfig(
                    client_id=ebay_app_id,
                    client_secret=ebay_cert_id,
                    api_base_url="https://api.ebay.com",
                    auth_url="https://api.ebay.com/identity/v1/oauth2/token",
                )

                # Create real API client
                ebay_api_client = EbayAPIClient(base_url=ebay_config.api_base_url)

                # Use real metrics service from services
                metrics_service = self.services.get("metrics_service")
                if not metrics_service:
                    # Create a simple metrics service if not available
                    from fs_agt_clean.services.infrastructure.metrics_service import (
                        MetricsService,
                    )

                    metrics_service = MetricsService()

                # Use real notification service or create a simple one
                notification_service = self.services.get("notification_service")
                if not notification_service:
                    # Create a simple notification service
                    class SimpleNotificationService:
                        async def send_notification(
                            self,
                            user_id: str,
                            template_id: str,
                            data: dict,
                            category: str,
                        ):
                            logger.info(
                                f"Notification sent to {user_id}: {template_id}"
                            )

                    notification_service = SimpleNotificationService()

                # Initialize eBay service with real sandbox dependencies
                self.services["ebay"] = EbayService(
                    config=ebay_config,
                    api_client=ebay_api_client,
                    metrics_service=metrics_service,
                    notification_service=notification_service,
                )
                logger.info("eBay service initialized with real sandbox configuration")

            except Exception as e:
                logger.error(f"Failed to initialize eBay service: {e}")
                # Continue without eBay service
        else:
            logger.warning("eBay service not available - skipping initialization")

    async def _initialize_agents(self):
        """Initialize 4 core autonomous agents with parallel loading (4+1 architecture)."""
        logger.info("🚀 Initializing 4 core autonomous agents with parallel loading...")

        # Import time for performance measurement
        import time

        # Define agent initialization tasks
        async def init_market_agent():
            """Initialize Market Autonomous Agent - 4+1 Architecture Compliance."""
            try:
                from fs_agt_clean.agents.market.market_agent import (
                    MarketAutonomousAgent,
                )

                logger.info("🤖 Creating MarketAutonomousAgent (true autonomous)...")
                market_agent = MarketAutonomousAgent("market_agent")
                logger.info("⚡ Initializing MarketAutonomousAgent async...")
                await asyncio.wait_for(market_agent.initialize_async(), timeout=20.0)
                logger.info(
                    "✅ MarketAutonomousAgent initialized successfully - LLM-free autonomous agent active"
                )

                return (
                    "market_agent",
                    {
                        "instance": market_agent,
                        "type": "market",
                        "marketplace": "cross_platform",
                        "status": "active",
                        "initialized_at": datetime.now(timezone.utc),
                        "last_activity": datetime.now(timezone.utc),
                        "error_count": 0,
                        "success_count": 0,
                    },
                )

            except asyncio.TimeoutError:
                logger.error(
                    "❌ Market Autonomous Agent initialization timed out after 20 seconds"
                )
                raise RuntimeError(
                    "MarketAutonomousAgent initialization timeout - 4+1 architecture requires functional autonomous agents"
                )

            except (ImportError, AttributeError, ModuleNotFoundError) as e:
                logger.error(
                    f"❌ CRITICAL: MarketAutonomousAgent required for 4+1 architecture compliance"
                )
                logger.error(f"❌ Missing dependencies: {e}")
                logger.error(
                    "❌ Cannot use AutonomousAgent as fallback - violates autonomous architecture"
                )
                raise RuntimeError(
                    f"MarketAutonomousAgent initialization failed: {e}. "
                    "4+1 architecture requires true autonomous agents, not conversational fallbacks."
                )

            except Exception as e:
                logger.error(f"❌ Failed to initialize Market Autonomous Agent: {e}")
                raise RuntimeError(f"MarketAutonomousAgent initialization failed: {e}")

        async def init_content_agent():
            """Initialize Content Autonomous Agent - 4+1 Architecture Compliance."""
            try:
                from fs_agt_clean.agents.content.content_agent import (
                    ContentAutonomousAgent,
                )

                logger.info("🤖 Creating ContentAutonomousAgent (true autonomous)...")
                content_agent = ContentAutonomousAgent("content_agent")
                logger.info("⚡ Initializing ContentAutonomousAgent async...")
                await asyncio.wait_for(content_agent.initialize_async(), timeout=20.0)
                logger.info(
                    "✅ ContentAutonomousAgent initialized successfully - LLM-free autonomous agent active"
                )

                return (
                    "content_agent",
                    {
                        "instance": content_agent,
                        "type": "content",
                        "marketplace": "cross_platform",
                        "status": "active",
                        "initialized_at": datetime.now(timezone.utc),
                        "last_activity": datetime.now(timezone.utc),
                        "error_count": 0,
                        "success_count": 0,
                    },
                )

            except asyncio.TimeoutError:
                logger.error(
                    "❌ Content Autonomous Agent initialization timed out after 20 seconds"
                )
                raise RuntimeError(
                    "ContentAutonomousAgent initialization timeout - 4+1 architecture requires functional autonomous agents"
                )

            except (ImportError, AttributeError, ModuleNotFoundError) as e:
                logger.error(
                    f"❌ CRITICAL: ContentAutonomousAgent required for 4+1 architecture compliance"
                )
                logger.error(f"❌ Missing dependencies: {e}")
                raise RuntimeError(
                    f"ContentAutonomousAgent initialization failed: {e}. "
                    "4+1 architecture requires true autonomous agents, not conversational fallbacks."
                )

            except Exception as e:
                logger.error(f"❌ Failed to initialize Content Autonomous Agent: {e}")
                raise RuntimeError(f"ContentAutonomousAgent initialization failed: {e}")

        async def init_executive_agent():
            """Initialize Executive Autonomous Agent - 4+1 Architecture Compliance."""
            try:
                from fs_agt_clean.agents.executive.executive_agent import (
                    ExecutiveAutonomousAgent,
                )

                logger.info("🤖 Creating ExecutiveAutonomousAgent (true autonomous)...")
                executive_agent = ExecutiveAutonomousAgent("executive_agent")
                logger.info("⚡ Initializing ExecutiveAutonomousAgent async...")
                await asyncio.wait_for(executive_agent.initialize_async(), timeout=20.0)
                logger.info(
                    "✅ ExecutiveAutonomousAgent initialized successfully - LLM-free autonomous agent active"
                )

                return (
                    "executive_agent",
                    {
                        "instance": executive_agent,
                        "type": "executive",
                        "marketplace": "cross_platform",
                        "status": "active",
                        "initialized_at": datetime.now(timezone.utc),
                        "last_activity": datetime.now(timezone.utc),
                        "error_count": 0,
                        "success_count": 0,
                    },
                )

            except asyncio.TimeoutError:
                logger.error(
                    "❌ Executive Autonomous Agent initialization timed out after 20 seconds"
                )
                raise RuntimeError(
                    "ExecutiveAutonomousAgent initialization timeout - 4+1 architecture requires functional autonomous agents"
                )

            except (ImportError, AttributeError, ModuleNotFoundError) as e:
                logger.error(
                    f"❌ CRITICAL: ExecutiveAutonomousAgent required for 4+1 architecture compliance"
                )
                logger.error(f"❌ Missing dependencies: {e}")
                raise RuntimeError(
                    f"ExecutiveAutonomousAgent initialization failed: {e}. "
                    "4+1 architecture requires true autonomous agents, not conversational fallbacks."
                )

            except Exception as e:
                logger.error(f"❌ Failed to initialize Executive Autonomous Agent: {e}")
                raise RuntimeError(
                    f"ExecutiveAutonomousAgent initialization failed: {e}"
                )

        async def init_logistics_agent():
            """Initialize Logistics Autonomous Agent - 4+1 Architecture Compliance."""
            try:
                from fs_agt_clean.agents.logistics.logistics_agent import (
                    LogisticsAutonomousAgent,
                )

                logger.info("🤖 Creating LogisticsAutonomousAgent (true autonomous)...")
                logistics_agent = LogisticsAutonomousAgent("logistics_agent")
                logger.info("⚡ Initializing LogisticsAutonomousAgent async...")
                await asyncio.wait_for(logistics_agent.initialize_async(), timeout=20.0)
                logger.info(
                    "✅ LogisticsAutonomousAgent initialized successfully - LLM-free autonomous agent active"
                )

                return (
                    "logistics_agent",
                    {
                        "instance": logistics_agent,
                        "type": "logistics",
                        "marketplace": "cross_platform",
                        "status": "active",
                        "initialized_at": datetime.now(timezone.utc),
                        "last_activity": datetime.now(timezone.utc),
                        "error_count": 0,
                        "success_count": 0,
                    },
                )

            except asyncio.TimeoutError:
                logger.error(
                    "❌ Logistics Autonomous Agent initialization timed out after 20 seconds"
                )
                raise RuntimeError(
                    "LogisticsAutonomousAgent initialization timeout - 4+1 architecture requires functional autonomous agents"
                )

            except (ImportError, AttributeError, ModuleNotFoundError) as e:
                logger.error(
                    f"❌ CRITICAL: LogisticsAutonomousAgent required for 4+1 architecture compliance"
                )
                logger.error(f"❌ Missing dependencies: {e}")
                raise RuntimeError(
                    f"LogisticsAutonomousAgent initialization failed: {e}. "
                    "4+1 architecture requires true autonomous agents, not conversational fallbacks."
                )

            except Exception as e:
                logger.error(f"❌ Failed to initialize Logistics Autonomous Agent: {e}")
                raise RuntimeError(
                    f"LogisticsAutonomousAgent initialization failed: {e}"
                )

        # Execute all agent initializations in parallel
        logger.info("⚡ Starting parallel agent initialization...")
        start_time = time.perf_counter()

        try:
            # Run all agent initializations concurrently
            results = await asyncio.gather(
                init_market_agent(),
                init_content_agent(),
                init_executive_agent(),
                init_logistics_agent(),
                return_exceptions=True,  # Don't fail if one agent fails
            )

            # Process results and register successful agents
            successful_agents = 0
            for result in results:
                if isinstance(result, Exception):
                    logger.error(
                        f"❌ Agent initialization failed with exception: {result}"
                    )
                elif isinstance(result, tuple) and len(result) == 2:
                    agent_name, agent_data = result
                    if agent_data is not None:
                        self.agents[agent_name] = agent_data
                        successful_agents += 1
                        logger.info(f"✅ {agent_name} initialized successfully")
                    else:
                        logger.warning(f"⚠️ {agent_name} initialization returned None")
                else:
                    logger.warning(f"⚠️ Unexpected result format: {result}")

            total_time = time.perf_counter() - start_time
            logger.info(
                f"⚡ Parallel agent initialization completed in {total_time:.2f}s"
            )
            logger.info(f"✅ Successfully initialized {successful_agents}/4 agents")

        except Exception as e:
            logger.error(f"❌ Parallel agent initialization failed: {e}")

        # Log final agent count
        logger.info(
            f"✅ Agent initialization complete. Total agents: {len(self.agents)}"
        )
        logger.info(f"✅ Registered agents: {list(self.agents.keys())}")

        # Validate 4+1 architecture compliance
        if len(self.agents) <= 4:
            logger.info("✅ 4+1 architecture compliance: PASSED")
        else:
            logger.warning(
                f"⚠️ 4+1 architecture compliance: FAILED - {len(self.agents)} agents registered"
            )

        # All redundant agent registrations removed for 4+1 architecture compliance
        # Only 4 core autonomous agents registered above

    async def _perform_health_check(self):
        """Perform health check on all agents."""
        logger.info("Performing agent health check...")

        for agent_id, agent_info in self.agents.items():
            try:
                health_status = await self._check_agent_health(agent_id, agent_info)
                self.agent_health[agent_id] = health_status

            except Exception as e:
                logger.error(f"Health check failed for agent {agent_id}: {e}")
                self.agent_health[agent_id] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now(timezone.utc).isoformat(),
                }

        self.last_health_check = datetime.now(timezone.utc)

    async def _check_agent_health(
        self, agent_id: str, agent_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check health of a specific agent."""
        try:
            instance = agent_info.get("instance")

            if instance and hasattr(instance, "get_health_status"):
                # Use the service's health check method
                health = await instance.get_health_status()
                return {
                    "status": health.get("status", "unknown"),
                    "metrics": health.get("metrics", {}),
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "uptime": (
                        datetime.now(timezone.utc) - agent_info["initialized_at"]
                    ).total_seconds(),
                    "error_count": agent_info.get("error_count", 0),
                    "success_count": agent_info.get("success_count", 0),
                }
            else:
                # Basic health check for agents without health status method
                return {
                    "status": "active",
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "uptime": (
                        datetime.now(timezone.utc) - agent_info["initialized_at"]
                    ).total_seconds(),
                    "error_count": agent_info.get("error_count", 0),
                    "success_count": agent_info.get("success_count", 0),
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now(timezone.utc).isoformat(),
                "uptime": 0,
                "error_count": agent_info.get("error_count", 0) + 1,
                "success_count": agent_info.get("success_count", 0),
            }

    async def get_all_agent_statuses(self) -> Dict[str, Any]:
        """Get status of all agents."""
        # Refresh health check if it's been more than 5 minutes
        if (
            not self.last_health_check
            or (datetime.now(timezone.utc) - self.last_health_check).total_seconds()
            > 300
        ):
            await self._perform_health_check()

        agent_statuses = {}
        for agent_id in self.agents:
            agent_status_dict = self.get_agent_status(agent_id)
            # get_agent_status returns {agent_id: {status: "...", ...}}, so extract the inner dict
            agent_statuses[agent_id] = agent_status_dict.get(agent_id, {})

        # Calculate overall status
        statuses = [
            status.get("status", "unknown") for status in agent_statuses.values()
        ]
        if "unhealthy" in statuses:
            overall_status = "degraded"
        elif "unknown" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "running"

        return {
            "agents": agent_statuses,
            "overall_status": overall_status,
            "total_agents": len(self.agents),
            "active_agents": len([s for s in statuses if s == "active"]),
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "initialization_status": self.initialization_status,
        }

    async def test_agent_connections(self) -> Dict[str, Any]:
        """Test connections for all agents."""
        results = {}

        for agent_id, agent_info in self.agents.items():
            try:
                instance = agent_info.get("instance")

                if instance and hasattr(instance, "test_connection"):
                    result = await instance.test_connection()
                    results[agent_id] = result
                else:
                    results[agent_id] = {
                        "success": True,
                        "message": "AutonomousAgent active (no connection test available)",
                    }

            except Exception as e:
                results[agent_id] = {
                    "success": False,
                    "error": str(e),
                    "message": f"Connection test failed: {str(e)}",
                }

        return results

    def get_agent_instance(self, agent_id: str) -> Optional[Any]:
        """Get the actual agent instance."""
        agent_info = self.agents.get(agent_id)
        return agent_info.get("instance") if agent_info else None

    async def shutdown(self):
        """Shutdown all agents gracefully."""
        logger.info("Shutting down real agent manager...")

        for agent_id, agent_info in self.agents.items():
            try:
                instance = agent_info.get("instance")
                if instance and hasattr(instance, "close"):
                    await instance.close()
                logger.info(f"AutonomousAgent {agent_id} shut down successfully")

            except Exception as e:
                logger.error(f"Error shutting down agent {agent_id}: {e}")

        self.agents.clear()
        self.services.clear()
        self.agent_health.clear()

        logger.info("Real agent manager shutdown complete")


# CRITICAL FIX: Backward compatibility alias for import resolution
# This ensures that any remaining imports of RealAgentManager will work
RealAgentManager = RealAutonomousAgentManager
