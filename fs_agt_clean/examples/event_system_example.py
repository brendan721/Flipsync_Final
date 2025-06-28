"""
Example of using the event system.

This example demonstrates how to use the event system to implement a simple
command-response flow between two agents.
"""

import asyncio
import logging
import uuid
from datetime import datetime

from fs_agt_clean.core.coordination.event_system import (  # Core components; Event bus; Publisher and subscriber; Subscription filters
    CompositeFilter,
    EventNameFilter,
    EventPriority,
    EventType,
    EventTypeFilter,
    InMemoryEventBus,
    create_publisher,
    create_subscriber,
    set_event_bus,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("event_system_example")


class MarketUnifiedAgent:
    """
    UnifiedAgent that provides market data.
    """

    def __init__(self):
        """Initialize the market agent."""
        self.agent_id = "market_agent"
        self.publisher = create_publisher(source_id=self.agent_id)
        self.subscriber = create_subscriber(subscriber_id=self.agent_id)

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

    async def start(self):
        """Start the market agent."""
        logger.info(f"Starting {self.agent_id}")

        # Subscribe to market data queries
        await self.subscriber.subscribe(
            filter=CompositeFilter(
                filters=[
                    EventTypeFilter(event_types={EventType.QUERY}),
                    EventNameFilter(event_names={"get_market_data"}),
                ],
                require_all=True,
            ),
            handler=self.handle_market_data_query,
        )

        logger.info(f"{self.agent_id} started")

    async def handle_market_data_query(self, event):
        """Handle a market data query."""
        logger.info(f"{self.agent_id} received query: {event.query_name}")

        # Extract parameters
        market = event.parameters.get("market")
        symbol = event.parameters.get("symbol")

        # Get market data
        if market in self.market_data:
            if symbol:
                if symbol in self.market_data[market]:
                    data = self.market_data[market][symbol]
                    success = True
                    error_message = None
                else:
                    data = None
                    success = False
                    error_message = f"Symbol {symbol} not found in market {market}"
            else:
                data = self.market_data[market]
                success = True
                error_message = None
        else:
            data = None
            success = False
            error_message = f"Market {market} not found"

        # Send response
        await self.publisher.publish_response(
            query_id=event.event_id,
            response_data=data,
            is_success=success,
            error_message=error_message,
            correlation_id=event.correlation_id,
        )

        logger.info(f"{self.agent_id} sent response to query {event.event_id}")


class ExecutiveUnifiedAgent:
    """
    UnifiedAgent that makes executive decisions based on market data.
    """

    def __init__(self):
        """Initialize the executive agent."""
        self.agent_id = "executive_agent"
        self.publisher = create_publisher(source_id=self.agent_id)
        self.subscriber = create_subscriber(subscriber_id=self.agent_id)

        # Track pending queries
        self.pending_queries = {}

    async def start(self):
        """Start the executive agent."""
        logger.info(f"Starting {self.agent_id}")

        # Subscribe to responses
        await self.subscriber.subscribe(
            filter=EventTypeFilter(event_types={EventType.RESPONSE}),
            handler=self.handle_response,
        )

        logger.info(f"{self.agent_id} started")

    async def get_market_data(self, market, symbol=None):
        """Get market data from the market agent."""
        logger.info(f"{self.agent_id} requesting market data for {market}/{symbol}")

        # Generate a correlation ID for this request
        correlation_id = str(uuid.uuid4())

        # Create a future to wait for the response
        future = asyncio.Future()
        self.pending_queries[correlation_id] = future

        # Send the query
        await self.publisher.publish_query(
            query_name="get_market_data",
            parameters={"market": market, "symbol": symbol},
            target="market_agent",
            correlation_id=correlation_id,
        )

        # Wait for the response
        try:
            response = await asyncio.wait_for(future, timeout=5.0)
            return response
        except asyncio.TimeoutError:
            logger.error(f"{self.agent_id} timed out waiting for market data")
            return None
        finally:
            # Clean up
            if correlation_id in self.pending_queries:
                del self.pending_queries[correlation_id]

    async def handle_response(self, event):
        """Handle a response event."""
        # Check if this is a response to one of our queries
        correlation_id = event.correlation_id
        if correlation_id in self.pending_queries:
            logger.info(
                f"{self.agent_id} received response for correlation ID {correlation_id}"
            )

            # Get the future
            future = self.pending_queries[correlation_id]

            # Set the result
            if not future.done():
                if event.is_success:
                    future.set_result(event.response_data)
                else:
                    future.set_exception(Exception(event.error_message))

    async def make_investment_decision(self, market, symbol):
        """Make an investment decision based on market data."""
        logger.info(f"{self.agent_id} making investment decision for {market}/{symbol}")

        # Get market data
        data = await self.get_market_data(market, symbol)

        if data:
            # Simple decision logic
            price = data["price"]
            volume = data["volume"]

            if volume > 1000000:
                if price < 100:
                    decision = "buy"
                    confidence = 0.8
                elif price < 1000:
                    decision = "hold"
                    confidence = 0.6
                else:
                    decision = "sell"
                    confidence = 0.7
            else:
                decision = "hold"
                confidence = 0.5

            logger.info(
                f"{self.agent_id} decided to {decision} {market}/{symbol} with confidence {confidence}"
            )

            # Publish the decision
            await self.publisher.publish_notification(
                notification_name="investment_decision",
                data={
                    "market": market,
                    "symbol": symbol,
                    "decision": decision,
                    "confidence": confidence,
                    "price": price,
                    "volume": volume,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            return decision, confidence
        else:
            logger.error(f"{self.agent_id} could not make decision due to missing data")
            return None, 0.0


async def main():
    """Main function."""
    # Create and set the event bus
    event_bus = InMemoryEventBus(bus_id="example_bus")
    set_event_bus(event_bus)

    # Create agents
    market_agent = MarketUnifiedAgent()
    executive_agent = ExecutiveUnifiedAgent()

    # Start agents
    await market_agent.start()
    await executive_agent.start()

    # Make some investment decisions
    await executive_agent.make_investment_decision("crypto", "bitcoin")
    await executive_agent.make_investment_decision("stocks", "aapl")
    await executive_agent.make_investment_decision("crypto", "dogecoin")

    # Try a non-existent market/symbol
    await executive_agent.make_investment_decision("forex", "usd_eur")

    # Get event bus metrics
    metrics = await event_bus.get_metrics()
    logger.info(f"Event bus metrics: {metrics}")


if __name__ == "__main__":
    asyncio.run(main())
