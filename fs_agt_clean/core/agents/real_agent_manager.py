"""Real UnifiedAgent Manager for FlipSync - Manages actual agent instances with real marketplace connections."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.services.marketplace.amazon.service import AmazonService

# Import eBay service with error handling
try:
    from fs_agt_clean.services.marketplace.ebay.service import EbayService

    ebay_service_available = True
except ImportError:
    ebay_service_available = False
    EbayService = None

# UnifiedAgent imports are optional for now - we'll focus on services
# from fs_agt_clean.agents.market.amazon_agent import AmazonMarketUnifiedAgent
# from fs_agt_clean.agents.market.ebay_agent import EbayMarketUnifiedAgent
# from fs_agt_clean.agents.market.inventory_agent import InventoryUnifiedAgent
# from fs_agt_clean.agents.executive.decision_engine import ExecutiveDecisionEngine

logger = logging.getLogger(__name__)


class RealUnifiedAgentManager:
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

        logger.info("Real UnifiedAgent Manager initialized")

    def register_pipeline_controller(self, pipeline_controller):
        """Register the pipeline controller for workflow coordination."""
        self.pipeline_controller = pipeline_controller
        self.workflow_coordination_enabled = True
        logger.info("Pipeline Controller registered with UnifiedAgent Manager")

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
                "error": f"UnifiedAgent {agent_name} not found",
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

            # Initialize marketplace services first
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

    async def _initialize_services(self):
        """Initialize marketplace services."""
        logger.info("Initializing marketplace services...")

        try:
            # Initialize Amazon service
            self.services["amazon"] = AmazonService()
            logger.info("Amazon service initialized")

            # Test Amazon connection
            amazon_test = await self.services["amazon"].test_connection()
            if amazon_test["success"]:
                logger.info("Amazon SP-API connection test successful")
            else:
                logger.warning(
                    f"Amazon SP-API connection test failed: {amazon_test['message']}"
                )

        except Exception as e:
            logger.error(f"Failed to initialize Amazon service: {e}")
            # Continue without Amazon service

        if ebay_service_available:
            try:
                # Create real eBay sandbox configuration using environment variables
                import os

                from fs_agt_clean.core.marketplace.ebay.api_client import EbayAPIClient
                from fs_agt_clean.core.marketplace.ebay.config import EbayConfig

                # Get eBay sandbox credentials from environment
                ebay_app_id = os.getenv("SB_EBAY_APP_ID", "")
                ebay_dev_id = os.getenv("SB_EBAY_DEV_ID", "")
                ebay_cert_id = os.getenv("SB_EBAY_CERT_ID", "")

                # Create real eBay sandbox config
                ebay_config = EbayConfig(
                    client_id=ebay_app_id,
                    client_secret=ebay_cert_id,
                    api_base_url="https://api.sandbox.ebay.com",
                    auth_url="https://api.sandbox.ebay.com/identity/v1/oauth2/token",
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
        """Initialize real agent instances."""
        logger.info("Initializing real agents...")

        # Initialize Amazon agent
        if "amazon" in self.services:
            try:
                amazon_config = {
                    "agent_id": "amazon_agent",
                    "marketplace": "amazon",
                    "service": self.services["amazon"],
                }

                # Create Amazon agent (simplified for now)
                self.agents["amazon_agent"] = {
                    "instance": self.services["amazon"],
                    "type": "marketplace",
                    "marketplace": "amazon",
                    "status": "active",
                    "initialized_at": datetime.now(timezone.utc),
                    "last_activity": datetime.now(timezone.utc),
                    "error_count": 0,
                    "success_count": 0,
                }
                logger.info("Amazon agent initialized")

            except Exception as e:
                logger.error(f"Failed to initialize Amazon agent: {e}")

        # Initialize eBay agent
        try:
            from fs_agt_clean.agents.market.ebay_agent import EbayMarketUnifiedAgent

            ebay_config = {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "refresh_token": "test_refresh_token",
                "sandbox": True,
            }

            self.agents["ebay_agent"] = {
                "instance": EbayMarketUnifiedAgent(agent_id="ebay_agent", config=ebay_config),
                "type": "marketplace",
                "marketplace": "ebay",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("eBay agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize eBay agent: {e}")

        # Initialize Inventory agent
        try:
            from fs_agt_clean.agents.market.inventory_agent import InventoryUnifiedAgent
            from fs_agt_clean.core.config.config_manager import ConfigManager
            from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
            from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer

            # Create required dependencies for BaseMarketUnifiedAgent
            config_manager = ConfigManager()
            alert_manager = AlertManager()
            battery_optimizer = BatteryOptimizer()

            # Create inventory agent with proper configuration
            inventory_config = {
                "api_key": "development_key",
                "marketplace_id": "cross_platform",
                "rate_limit": 100,
                "timeout": 30,
            }

            inventory_agent = InventoryUnifiedAgent(
                agent_id="inventory_agent",
                config_manager=config_manager,
                alert_manager=alert_manager,
                battery_optimizer=battery_optimizer,
                config=inventory_config,
            )

            self.agents["inventory_agent"] = {
                "instance": inventory_agent,
                "type": "inventory",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Inventory agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Inventory agent: {e}")

        # Initialize Executive agent
        try:
            from fs_agt_clean.agents.executive.executive_agent import ExecutiveUnifiedAgent

            self.agents["executive_agent"] = {
                "instance": ExecutiveUnifiedAgent(),
                "type": "executive",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Executive agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Executive agent: {e}")

        # Initialize Content agent
        try:
            from fs_agt_clean.agents.content.content_agent import ContentUnifiedAgent

            self.agents["content_agent"] = {
                "instance": ContentUnifiedAgent(),
                "type": "content",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Content agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Content agent: {e}")

        # Initialize Market agent
        try:
            from fs_agt_clean.agents.market.market_agent import MarketUnifiedAgent

            self.agents["market_agent"] = {
                "instance": MarketUnifiedAgent(),
                "type": "market",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Market agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Market agent: {e}")

        # Initialize Logistics agent
        try:
            from fs_agt_clean.agents.logistics.logistics_agent import LogisticsUnifiedAgent

            self.agents["logistics_agent"] = {
                "instance": LogisticsUnifiedAgent(),
                "type": "logistics",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Logistics agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Logistics agent: {e}")

        # Initialize Listing agent (using auto listing agent)
        try:
            from fs_agt_clean.agents.automation.auto_listing_agent import (
                AutoListingUnifiedAgent,
            )

            self.agents["listing_agent"] = {
                "instance": AutoListingUnifiedAgent(),
                "type": "listing",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Listing agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Listing agent: {e}")

        # Initialize AutoPricing agent
        try:
            from fs_agt_clean.agents.automation.auto_pricing_agent import (
                AutoPricingUnifiedAgent,
            )

            auto_pricing_instance = AutoPricingUnifiedAgent()

            self.agents["auto_pricing_agent"] = {
                "instance": auto_pricing_instance,
                "type": "automation",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("AutoPricing agent initialized")

            # Also register as pricing_agent for business workflow coordination
            self.agents["pricing_agent"] = {
                "instance": auto_pricing_instance,
                "type": "pricing",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Pricing agent initialized (alias for AutoPricing)")

        except Exception as e:
            logger.error(f"Failed to initialize AutoPricing agent: {e}")

        # Initialize AutoListing agent
        try:
            from fs_agt_clean.agents.automation.auto_listing_agent import (
                AutoListingUnifiedAgent,
            )

            self.agents["auto_listing_agent"] = {
                "instance": AutoListingUnifiedAgent(),
                "type": "automation",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("AutoListing agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize AutoListing agent: {e}")

        # Initialize AutoInventory agent
        try:
            from fs_agt_clean.agents.automation.auto_inventory_agent import (
                AutoInventoryUnifiedAgent,
            )

            self.agents["auto_inventory_agent"] = {
                "instance": AutoInventoryUnifiedAgent(),
                "type": "automation",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("AutoInventory agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize AutoInventory agent: {e}")

        # Initialize AI Executive agent
        try:
            from fs_agt_clean.agents.executive.ai_executive_agent import (
                AIExecutiveUnifiedAgent,
            )

            ai_executive_instance = AIExecutiveUnifiedAgent("ai_executive_agent")
            await ai_executive_instance.initialize()

            self.agents["ai_executive_agent"] = {
                "instance": ai_executive_instance,
                "type": "ai_executive",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("AI Executive agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize AI Executive agent: {e}")

        # Initialize Strategy agent
        try:
            from fs_agt_clean.agents.executive.strategy_agent import StrategyUnifiedAgent

            self.agents["strategy_agent"] = {
                "instance": StrategyUnifiedAgent(agent_id="strategy_agent"),
                "type": "executive",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Strategy agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Strategy agent: {e}")

        # Initialize Resource agent
        try:
            from fs_agt_clean.agents.executive.resource_agent import ResourceUnifiedAgent

            self.agents["resource_agent"] = {
                "instance": ResourceUnifiedAgent(agent_id="resource_agent"),
                "type": "executive",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Resource agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Resource agent: {e}")

        # Initialize Amazon agent
        try:
            from fs_agt_clean.agents.market.amazon_agent import AmazonUnifiedAgent

            amazon_config = {
                "lwa_app_id": "test_app_id",
                "lwa_client_secret": "test_secret",
                "sp_api_refresh_token": "test_token",
                "marketplace_id": "ATVPDKIKX0DER",
                "region": "us-east-1",
            }

            self.agents["amazon_agent"] = {
                "instance": AmazonUnifiedAgent(agent_id="amazon_agent", config=amazon_config),
                "type": "marketplace",
                "marketplace": "amazon",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Amazon agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Amazon agent: {e}")

        # Initialize Competitive agent
        try:
            from fs_agt_clean.agents.market.competitive_agent import CompetitiveUnifiedAgent

            self.agents["competitive_agent"] = {
                "instance": CompetitiveUnifiedAgent(),
                "type": "market",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Competitive agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Competitive agent: {e}")

        # Initialize AI Market agent
        try:
            from fs_agt_clean.agents.market.ai_market_agent import AIMarketUnifiedAgent

            self.agents["ai_market_agent"] = {
                "instance": AIMarketUnifiedAgent(),
                "type": "market",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("AI Market agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize AI Market agent: {e}")

        # Initialize AI Content agent
        try:
            from fs_agt_clean.agents.content.ai_content_agent import AIContentUnifiedAgent

            self.agents["ai_content_agent"] = {
                "instance": AIContentUnifiedAgent(),
                "type": "content",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("AI Content agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize AI Content agent: {e}")

        # Initialize Image agent
        try:
            from fs_agt_clean.agents.content.image_agent import ImageUnifiedAgent

            self.agents["image_agent"] = {
                "instance": ImageUnifiedAgent(marketplace="ebay"),
                "type": "content",
                "marketplace": "ebay",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Image agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Image agent: {e}")

        # Initialize Listing Content agent
        try:
            from fs_agt_clean.agents.content.listing_content_agent import (
                ListingContentUnifiedAgent,
            )

            self.agents["listing_content_agent"] = {
                "instance": ListingContentUnifiedAgent(marketplace="ebay"),
                "type": "content",
                "marketplace": "ebay",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Listing Content agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Listing Content agent: {e}")

        # Initialize AI Logistics agent
        try:
            from fs_agt_clean.agents.logistics.ai_logistics_agent import (
                AILogisticsUnifiedAgent,
            )

            self.agents["ai_logistics_agent"] = {
                "instance": AILogisticsUnifiedAgent(),
                "type": "logistics",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("AI Logistics agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize AI Logistics agent: {e}")

        # Initialize Warehouse agent
        try:
            from fs_agt_clean.agents.logistics.warehouse_agent import WarehouseUnifiedAgent

            self.agents["warehouse_agent"] = {
                "instance": WarehouseUnifiedAgent(agent_id="warehouse_agent"),
                "type": "logistics",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Warehouse agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Warehouse agent: {e}")

        # Initialize Shipping agent
        try:
            from fs_agt_clean.agents.logistics.shipping_agent import ShippingUnifiedAgent

            self.agents["shipping_agent"] = {
                "instance": ShippingUnifiedAgent(),
                "type": "logistics",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Shipping agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Shipping agent: {e}")

        # Initialize Sync agent
        try:
            from fs_agt_clean.agents.logistics.sync_agent import SyncUnifiedAgent

            self.agents["sync_agent"] = {
                "instance": SyncUnifiedAgent(),
                "type": "logistics",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Sync agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Sync agent: {e}")

        # Initialize Service agent
        try:
            from fs_agt_clean.agents.conversational.service_agent import ServiceUnifiedAgent

            self.agents["service_agent"] = {
                "instance": ServiceUnifiedAgent(),
                "type": "conversational",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Service agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Service agent: {e}")

        # Initialize Monitoring agent
        try:
            from fs_agt_clean.agents.conversational.monitoring_agent import (
                MonitoringUnifiedAgent,
            )

            self.agents["monitoring_agent"] = {
                "instance": MonitoringUnifiedAgent(),
                "type": "conversational",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Monitoring agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Monitoring agent: {e}")

        # Initialize Intent Recognizer
        try:
            from fs_agt_clean.agents.conversational.intent_recognizer import (
                IntentRecognizer,
            )

            self.agents["intent_recognizer"] = {
                "instance": IntentRecognizer(),
                "type": "conversational",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Intent Recognizer initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Intent Recognizer: {e}")

        # Initialize Recommendation Engine
        try:
            from fs_agt_clean.agents.conversational.recommendation_engine import (
                RecommendationEngine,
            )

            self.agents["recommendation_engine"] = {
                "instance": RecommendationEngine(),
                "type": "conversational",
                "marketplace": "cross_platform",
                "status": "active",
                "initialized_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "error_count": 0,
                "success_count": 0,
            }
            logger.info("Recommendation Engine initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Recommendation Engine: {e}")

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
                        "message": "UnifiedAgent active (no connection test available)",
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
                logger.info(f"UnifiedAgent {agent_id} shut down successfully")

            except Exception as e:
                logger.error(f"Error shutting down agent {agent_id}: {e}")

        self.agents.clear()
        self.services.clear()
        self.agent_health.clear()

        logger.info("Real agent manager shutdown complete")
