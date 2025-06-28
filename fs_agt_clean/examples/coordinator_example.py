"""
Example of using the Coordinator component.

This example demonstrates how to use the Coordinator component to manage
agent registration, discovery, and task delegation.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta

from fs_agt_clean.core.coordination import (  # Event System; Coordinator
    UnifiedAgentCapability,
    UnifiedAgentInfo,
    UnifiedAgentStatus,
    UnifiedAgentType,
    Event,
    EventPriority,
    EventType,
    InMemoryCoordinator,
    InMemoryEventBus,
    Task,
    TaskPriority,
    TaskStatus,
    create_publisher,
    create_subscriber,
    set_event_bus,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("coordinator_example")


class MarketUnifiedAgent:
    """
    UnifiedAgent that provides market data.
    """

    def __init__(self):
        """Initialize the market agent."""
        self.agent_id = "market_agent"
        self.name = "Market UnifiedAgent"
        self.description = "Provides market data and analysis"
        self.agent_type = UnifiedAgentType.SPECIALIST

        # Create publisher and subscriber
        self.publisher = create_publisher(source_id=self.agent_id)
        self.subscriber = create_subscriber(subscriber_id=self.agent_id)

        # Define capabilities
        self.capabilities = [
            UnifiedAgentCapability(
                name="market_data",
                description="Provides market data for various assets",
                parameters={"market": "string", "symbol": "string"},
                tags={"market", "data", "finance"},
            ),
            UnifiedAgentCapability(
                name="market_analysis",
                description="Analyzes market trends and patterns",
                parameters={
                    "market": "string",
                    "symbol": "string",
                    "timeframe": "string",
                },
                tags={"market", "analysis", "finance"},
            ),
        ]

        # Market data
        self.market_data = {
            "crypto": {
                "bitcoin": {"price": 50000, "volume": 1000000},
                "ethereum": {"price": 3000, "volume": 500000},
                "dogecoin": {"price": 0.5, "volume": 2000000},
            },
            "stocks": {
                "aapl": {"price": 150, "volume": 5000000},
                "msft": {"price": 300, "volume": 3000000},
                "googl": {"price": 2500, "volume": 1000000},
            },
        }

    async def start(self, coordinator):
        """
        Start the market agent.

        Args:
            coordinator: The coordinator to register with
        """
        logger.info(f"Starting {self.name}")

        # Register with the coordinator
        agent_info = UnifiedAgentInfo(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            name=self.name,
            description=self.description,
            capabilities=self.capabilities,
        )

        await coordinator.register_agent(agent_info)

        # Subscribe to task events
        await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"execute_task"}),
            handler=self.handle_task,
        )

        logger.info(f"{self.name} started")

    async def handle_task(self, event):
        """
        Handle a task event.

        Args:
            event: The task event
        """
        # Extract task information
        task_id = event.data.get("task_id")
        task_type = event.data.get("task_type")
        parameters = event.data.get("parameters", {})

        logger.info(f"{self.name} received task: {task_id} ({task_type})")

        # Process the task
        if task_type == "get_market_data":
            # Extract parameters
            market = parameters.get("market")
            symbol = parameters.get("symbol")

            # Get market data
            result = None
            error = None

            try:
                if market in self.market_data:
                    if symbol:
                        if symbol in self.market_data[market]:
                            result = self.market_data[market][symbol]
                        else:
                            error = f"Symbol {symbol} not found in market {market}"
                    else:
                        result = self.market_data[market]
                else:
                    error = f"Market {market} not found"
            except Exception as e:
                error = str(e)

            # Publish task result
            if error:
                await self.publisher.publish_notification(
                    notification_name="task_failed",
                    data={"task_id": task_id, "error": error},
                )
            else:
                await self.publisher.publish_notification(
                    notification_name="task_completed",
                    data={"task_id": task_id, "result": result},
                )

        elif task_type == "analyze_market":
            # Extract parameters
            market = parameters.get("market")
            symbol = parameters.get("symbol")

            # Perform market analysis
            result = None
            error = None

            try:
                if market in self.market_data:
                    if symbol:
                        if symbol in self.market_data[market]:
                            data = self.market_data[market][symbol]

                            # Simple analysis
                            price = data["price"]
                            volume = data["volume"]

                            if volume > 1000000:
                                if price < 100:
                                    recommendation = "buy"
                                    confidence = 0.8
                                elif price < 1000:
                                    recommendation = "hold"
                                    confidence = 0.6
                                else:
                                    recommendation = "sell"
                                    confidence = 0.7
                            else:
                                recommendation = "hold"
                                confidence = 0.5

                            result = {
                                "recommendation": recommendation,
                                "confidence": confidence,
                                "price": price,
                                "volume": volume,
                                "analysis": f"Based on price and volume analysis, the recommendation is to {recommendation} with {confidence:.1f} confidence.",
                            }
                        else:
                            error = f"Symbol {symbol} not found in market {market}"
                    else:
                        error = "Symbol is required for market analysis"
                else:
                    error = f"Market {market} not found"
            except Exception as e:
                error = str(e)

            # Publish task result
            if error:
                await self.publisher.publish_notification(
                    notification_name="task_failed",
                    data={"task_id": task_id, "error": error},
                )
            else:
                await self.publisher.publish_notification(
                    notification_name="task_completed",
                    data={"task_id": task_id, "result": result},
                )

        else:
            # Unknown task type
            await self.publisher.publish_notification(
                notification_name="task_failed",
                data={"task_id": task_id, "error": f"Unknown task type: {task_type}"},
            )


class ExecutiveUnifiedAgent:
    """
    UnifiedAgent that makes executive decisions based on market data.
    """

    def __init__(self):
        """Initialize the executive agent."""
        self.agent_id = "executive_agent"
        self.name = "Executive UnifiedAgent"
        self.description = "Makes executive decisions based on market data"
        self.agent_type = UnifiedAgentType.EXECUTIVE

        # Create publisher and subscriber
        self.publisher = create_publisher(source_id=self.agent_id)
        self.subscriber = create_subscriber(subscriber_id=self.agent_id)

        # Define capabilities
        self.capabilities = [
            UnifiedAgentCapability(
                name="investment_decision",
                description="Makes investment decisions based on market data",
                parameters={"market": "string", "symbol": "string"},
                tags={"investment", "decision", "finance"},
            )
        ]

    async def start(self, coordinator):
        """
        Start the executive agent.

        Args:
            coordinator: The coordinator to register with
        """
        logger.info(f"Starting {self.name}")

        # Register with the coordinator
        agent_info = UnifiedAgentInfo(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            name=self.name,
            description=self.description,
            capabilities=self.capabilities,
        )

        await coordinator.register_agent(agent_info)

        # Store the coordinator for later use
        self.coordinator = coordinator

        logger.info(f"{self.name} started")

    async def make_investment_decision(self, market, symbol):
        """
        Make an investment decision based on market data and analysis.

        Args:
            market: The market to analyze
            symbol: The symbol to analyze

        Returns:
            The investment decision
        """
        logger.info(f"{self.name} making investment decision for {market}/{symbol}")

        # First, get market data
        market_data_capability = UnifiedAgentCapability(
            name="market_data", parameters={"market": market, "symbol": symbol}
        )

        # Find agents with market data capability
        market_data_agents = await self.coordinator.find_agents_by_capability(
            market_data_capability
        )

        if not market_data_agents:
            logger.error(
                f"No agents found with market_data capability for {market}/{symbol}"
            )
            return None

        # Delegate task to get market data
        market_data_task_id = await self.coordinator.delegate_task(
            task_id="",
            task_type="get_market_data",
            parameters={"market": market, "symbol": symbol},
            required_capability=market_data_capability,
            priority=TaskPriority.HIGH.value,
        )

        # Wait for the task to complete
        while True:
            task_status = await self.coordinator.get_task_status(market_data_task_id)
            if task_status["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.1)

        if task_status["status"] == "failed":
            logger.error(f"Failed to get market data for {market}/{symbol}")
            return None

        # Get the market data result
        market_data_result = await self.coordinator.get_task_result(market_data_task_id)
        market_data = market_data_result["result"]

        # Next, get market analysis
        market_analysis_capability = UnifiedAgentCapability(
            name="market_analysis", parameters={"market": market, "symbol": symbol}
        )

        # Find agents with market analysis capability
        market_analysis_agents = await self.coordinator.find_agents_by_capability(
            market_analysis_capability
        )

        if not market_analysis_agents:
            logger.error(
                f"No agents found with market_analysis capability for {market}/{symbol}"
            )
            return None

        # Delegate task to analyze market
        market_analysis_task_id = await self.coordinator.delegate_task(
            task_id="",
            task_type="analyze_market",
            parameters={"market": market, "symbol": symbol},
            required_capability=market_analysis_capability,
            priority=TaskPriority.HIGH.value,
        )

        # Wait for the task to complete
        while True:
            task_status = await self.coordinator.get_task_status(
                market_analysis_task_id
            )
            if task_status["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.1)

        if task_status["status"] == "failed":
            logger.error(f"Failed to analyze market for {market}/{symbol}")
            return None

        # Get the market analysis result
        market_analysis_result = await self.coordinator.get_task_result(
            market_analysis_task_id
        )
        market_analysis = market_analysis_result["result"]

        # Make the investment decision
        decision = {
            "market": market,
            "symbol": symbol,
            "price": market_data["price"],
            "volume": market_data["volume"],
            "recommendation": market_analysis["recommendation"],
            "confidence": market_analysis["confidence"],
            "analysis": market_analysis["analysis"],
            "decision_time": datetime.now().isoformat(),
        }

        logger.info(
            f"{self.name} decided to {decision['recommendation']} {market}/{symbol} "
            f"with confidence {decision['confidence']}"
        )

        # Publish the decision
        await self.publisher.publish_notification(
            notification_name="investment_decision", data=decision
        )

        return decision


async def main():
    """Main function."""
    # Create and set the event bus
    event_bus = InMemoryEventBus(bus_id="example_bus")
    set_event_bus(event_bus)

    # Create the coordinator
    coordinator = InMemoryCoordinator(coordinator_id="example_coordinator")
    await coordinator.start()

    # Create agents
    market_agent = MarketUnifiedAgent()
    executive_agent = ExecutiveUnifiedAgent()

    # Start agents
    await market_agent.start(coordinator)
    await executive_agent.start(coordinator)

    # Make some investment decisions
    await executive_agent.make_investment_decision("crypto", "bitcoin")
    await executive_agent.make_investment_decision("stocks", "aapl")

    # Try a non-existent market/symbol
    await executive_agent.make_investment_decision("forex", "usd_eur")

    # Stop the coordinator
    await coordinator.stop()


if __name__ == "__main__":
    asyncio.run(main())
