"""
Example of integrating the Knowledge Repository with the Coordinator component.

This example demonstrates how to integrate the Knowledge Repository with the Coordinator
component to enable knowledge sharing between agents.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from fs_agt_clean.core.coordination.coordinator import (
    UnifiedAgent,
    UnifiedAgentCapability,
    UnifiedAgentStatus,
    UnifiedAgentType,
    Coordinator,
    InMemoryCoordinator,
)
from fs_agt_clean.core.coordination.event_system import (
    Event,
    EventNameFilter,
    EventPriority,
    EventType,
    InMemoryEventBus,
    create_publisher,
    create_subscriber,
    set_event_bus,
)
from fs_agt_clean.core.coordination.knowledge_repository import (
    InMemoryKnowledgeRepository,
    KnowledgeError,
    KnowledgeItem,
    KnowledgeStatus,
    KnowledgeType,
    TopicFilter,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("knowledge_coordinator_integration")


class KnowledgeUnifiedAgent(UnifiedAgent):
    """
    UnifiedAgent that provides and consumes knowledge.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: UnifiedAgentType,
        capabilities: Set[UnifiedAgentCapability],
        knowledge_repository: InMemoryKnowledgeRepository,
    ):
        """
        Initialize the knowledge agent.

        Args:
            agent_id: UnifiedAgent ID
            name: UnifiedAgent name
            agent_type: UnifiedAgent type
            capabilities: UnifiedAgent capabilities
            knowledge_repository: Knowledge repository
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            capabilities=capabilities,
        )
        self.knowledge_repository = knowledge_repository
        self.publisher = create_publisher(source_id=agent_id)
        self.subscriber = create_subscriber(subscriber_id=agent_id)
        self.subscription_ids = []

    async def start(self) -> None:
        """Start the agent."""
        logger.info(f"Starting {self.name}")

        # Subscribe to knowledge-related events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"knowledge_added"}),
            handler=self.handle_knowledge_added,
        )
        self.subscription_ids.append(subscription_id)

        # Subscribe to knowledge by topic
        subscription_id = await self.knowledge_repository.subscribe(
            filter=TopicFilter(patterns={f"{self.agent_id}/.*"}),
            handler=self.handle_knowledge_update,
        )
        self.subscription_ids.append(subscription_id)

        # Set agent status to ACTIVE
        self.status = UnifiedAgentStatus.ACTIVE

        logger.info(f"{self.name} started")

    async def stop(self) -> None:
        """Stop the agent."""
        logger.info(f"Stopping {self.name}")

        # Unsubscribe from events
        for subscription_id in self.subscription_ids:
            await self.subscriber.unsubscribe(subscription_id)

        # Set agent status to INACTIVE
        self.status = UnifiedAgentStatus.INACTIVE

        logger.info(f"{self.name} stopped")

    async def handle_knowledge_added(self, event: Event) -> None:
        """
        Handle a knowledge added event.

        Args:
            event: Knowledge added event
        """
        # Extract knowledge information
        knowledge_id = event.data.get("knowledge_id")
        topic = event.data.get("topic")

        logger.info(
            f"UnifiedAgent {self.name} received knowledge added event: {knowledge_id} ({topic})"
        )

        # Get the knowledge item
        knowledge = await self.knowledge_repository.get_knowledge(knowledge_id)
        if knowledge:
            # Process the knowledge item
            await self.process_knowledge(knowledge)

    async def handle_knowledge_update(self, knowledge: KnowledgeItem) -> None:
        """
        Handle a knowledge update.

        Args:
            knowledge: Updated knowledge item
        """
        logger.info(
            f"UnifiedAgent {self.name} received knowledge update: {knowledge.knowledge_id} ({knowledge.topic})"
        )

        # Process the knowledge item
        await self.process_knowledge(knowledge)

    async def process_knowledge(self, knowledge: KnowledgeItem) -> None:
        """
        Process a knowledge item.

        Args:
            knowledge: Knowledge item to process
        """
        # This method should be implemented by subclasses
        pass

    async def publish_knowledge(
        self,
        topic: str,
        content: Any,
        knowledge_type: KnowledgeType = KnowledgeType.FACT,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
    ) -> str:
        """
        Publish knowledge to the repository.

        Args:
            topic: Knowledge topic
            content: Knowledge content
            knowledge_type: Knowledge type
            metadata: Knowledge metadata
            tags: Knowledge tags

        Returns:
            ID of the published knowledge item
        """
        # Publish the knowledge item
        knowledge_id = await self.knowledge_repository.publish_knowledge(
            knowledge_type=knowledge_type,
            topic=topic,
            content=content,
            metadata=metadata,
            source_id=self.agent_id,
            tags=tags,
        )

        logger.info(f"UnifiedAgent {self.name} published knowledge: {knowledge_id} ({topic})")

        return knowledge_id


class MarketUnifiedAgent(KnowledgeUnifiedAgent):
    """
    UnifiedAgent that provides market knowledge.
    """

    def __init__(self, knowledge_repository: InMemoryKnowledgeRepository):
        """
        Initialize the market agent.

        Args:
            knowledge_repository: Knowledge repository
        """
        super().__init__(
            agent_id="market_agent",
            name="Market UnifiedAgent",
            agent_type=UnifiedAgentType.SPECIALIST,
            capabilities={UnifiedAgentCapability.MARKET_ANALYSIS},
            knowledge_repository=knowledge_repository,
        )

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

    async def start(self) -> None:
        """Start the agent."""
        await super().start()

        # Publish initial market knowledge
        await self.publish_market_knowledge()

    async def publish_market_knowledge(self) -> None:
        """Publish market knowledge to the repository."""
        # Publish crypto market knowledge
        for symbol, data in self.market_data["crypto"].items():
            await self.publish_knowledge(
                topic=f"market/crypto/{symbol}",
                content=data,
                metadata={
                    "market": "crypto",
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                },
                tags={"market", "crypto", symbol},
            )

        # Publish stock market knowledge
        for symbol, data in self.market_data["stocks"].items():
            await self.publish_knowledge(
                topic=f"market/stocks/{symbol}",
                content=data,
                metadata={
                    "market": "stocks",
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                },
                tags={"market", "stocks", symbol},
            )

        logger.info("Published market knowledge")

    async def process_knowledge(self, knowledge: KnowledgeItem) -> None:
        """
        Process a knowledge item.

        Args:
            knowledge: Knowledge item to process
        """
        # Check if the knowledge item is a market request
        if knowledge.topic.startswith("request/market/"):
            # Extract the market and symbol from the topic
            parts = knowledge.topic.split("/")
            if len(parts) >= 4:
                market = parts[2]
                symbol = parts[3]

                # Check if we have data for this market and symbol
                if market in self.market_data and symbol in self.market_data[market]:
                    # Get the market data
                    data = self.market_data[market][symbol]

                    # Publish the market data
                    await self.publish_knowledge(
                        topic=f"response/market/{market}/{symbol}",
                        content=data,
                        metadata={
                            "market": market,
                            "symbol": symbol,
                            "timestamp": datetime.now().isoformat(),
                            "request_id": knowledge.knowledge_id,
                        },
                        tags={"market", market, symbol, "response"},
                    )

                    logger.info(f"Published market data for {market}/{symbol}")


class AnalysisUnifiedAgent(KnowledgeUnifiedAgent):
    """
    UnifiedAgent that analyzes market knowledge.
    """

    def __init__(self, knowledge_repository: InMemoryKnowledgeRepository):
        """
        Initialize the analysis agent.

        Args:
            knowledge_repository: Knowledge repository
        """
        super().__init__(
            agent_id="analysis_agent",
            name="Analysis UnifiedAgent",
            agent_type=UnifiedAgentType.SPECIALIST,
            capabilities={UnifiedAgentCapability.DATA_ANALYSIS},
            knowledge_repository=knowledge_repository,
        )

    async def start(self) -> None:
        """Start the agent."""
        await super().start()

        # Subscribe to market knowledge
        subscription_id = await self.knowledge_repository.subscribe(
            filter=TopicFilter(patterns={"market/crypto/.*", "market/stocks/.*"}),
            handler=self.handle_market_knowledge,
        )
        self.subscription_ids.append(subscription_id)

    async def handle_market_knowledge(self, knowledge: KnowledgeItem) -> None:
        """
        Handle market knowledge.

        Args:
            knowledge: Market knowledge
        """
        logger.info(f"Analyzing market knowledge: {knowledge.topic}")

        # Extract market data
        market_data = knowledge.content

        # Analyze market data
        if "price" in market_data and "volume" in market_data:
            price = market_data["price"]
            volume = market_data["volume"]

            # Simple analysis
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

            # Publish analysis
            await self.publish_knowledge(
                topic=f"{knowledge.topic}/analysis",
                content={
                    "recommendation": recommendation,
                    "confidence": confidence,
                    "price": price,
                    "volume": volume,
                    "analysis": f"Based on price and volume analysis, the recommendation is to {recommendation} with {confidence:.1f} confidence.",
                },
                knowledge_type=KnowledgeType.RELATION,
                metadata={
                    "source_knowledge_id": knowledge.knowledge_id,
                    "timestamp": datetime.now().isoformat(),
                },
                tags={"analysis", "recommendation", recommendation},
            )

            logger.info(
                f"Published analysis for {knowledge.topic}: {recommendation} ({confidence:.1f})"
            )

    async def process_knowledge(self, knowledge: KnowledgeItem) -> None:
        """
        Process a knowledge item.

        Args:
            knowledge: Knowledge item to process
        """
        # Check if the knowledge item is a request for analysis
        if knowledge.topic.startswith("request/analysis/"):
            # Extract the market and symbol from the topic
            parts = knowledge.topic.split("/")
            if len(parts) >= 4:
                market = parts[2]
                symbol = parts[3]

                # Request market data
                await self.publish_knowledge(
                    topic=f"request/market/{market}/{symbol}",
                    content={"request": "market_data"},
                    metadata={"timestamp": datetime.now().isoformat(), "priority": 0.8},
                    tags={"request", "market", market, symbol},
                )

                logger.info(f"Requested market data for {market}/{symbol}")


class ExecutiveUnifiedAgent(KnowledgeUnifiedAgent):
    """
    UnifiedAgent that makes executive decisions based on analysis.
    """

    def __init__(self, knowledge_repository: InMemoryKnowledgeRepository):
        """
        Initialize the executive agent.

        Args:
            knowledge_repository: Knowledge repository
        """
        super().__init__(
            agent_id="executive_agent",
            name="Executive UnifiedAgent",
            agent_type=UnifiedAgentType.EXECUTIVE,
            capabilities={UnifiedAgentCapability.DECISION_MAKING},
            knowledge_repository=knowledge_repository,
        )

        # Portfolio
        self.portfolio = {
            "crypto": {"bitcoin": 0.1, "ethereum": 1.0, "dogecoin": 1000.0},
            "stocks": {"aapl": 10, "msft": 5, "googl": 2},
        }

    async def start(self) -> None:
        """Start the agent."""
        await super().start()

        # Subscribe to analysis knowledge
        subscription_id = await self.knowledge_repository.subscribe(
            filter=TopicFilter(patterns={"market/.*/analysis"}),
            handler=self.handle_analysis,
        )
        self.subscription_ids.append(subscription_id)

        # Request analysis for portfolio items
        await self.request_portfolio_analysis()

    async def request_portfolio_analysis(self) -> None:
        """Request analysis for portfolio items."""
        # Request analysis for crypto portfolio
        for symbol in self.portfolio["crypto"]:
            await self.publish_knowledge(
                topic=f"request/analysis/crypto/{symbol}",
                content={
                    "request": "analysis",
                    "holdings": self.portfolio["crypto"][symbol],
                },
                metadata={"timestamp": datetime.now().isoformat(), "priority": 0.9},
                tags={"request", "analysis", "crypto", symbol},
            )

        # Request analysis for stock portfolio
        for symbol in self.portfolio["stocks"]:
            await self.publish_knowledge(
                topic=f"request/analysis/stocks/{symbol}",
                content={
                    "request": "analysis",
                    "holdings": self.portfolio["stocks"][symbol],
                },
                metadata={"timestamp": datetime.now().isoformat(), "priority": 0.9},
                tags={"request", "analysis", "stocks", symbol},
            )

        logger.info("Requested portfolio analysis")

    async def handle_analysis(self, knowledge: KnowledgeItem) -> None:
        """
        Handle analysis knowledge.

        Args:
            knowledge: Analysis knowledge
        """
        logger.info(f"Received analysis: {knowledge.topic}")

        # Extract analysis data
        analysis_data = knowledge.content

        # Make decision based on analysis
        if "recommendation" in analysis_data and "confidence" in analysis_data:
            recommendation = analysis_data["recommendation"]
            confidence = analysis_data["confidence"]

            # Extract market and symbol from topic
            parts = knowledge.topic.split("/")
            if len(parts) >= 3:
                market = parts[1]
                symbol = parts[2]

                # Check if we have this item in our portfolio
                if market in self.portfolio and symbol in self.portfolio[market]:
                    holdings = self.portfolio[market][symbol]

                    # Make decision
                    if recommendation == "buy" and confidence > 0.7:
                        decision = "buy"
                        amount = 1.0
                    elif recommendation == "sell" and confidence > 0.7:
                        decision = "sell"
                        amount = holdings * 0.5  # Sell half
                    else:
                        decision = "hold"
                        amount = 0.0

                    # Publish decision
                    await self.publish_knowledge(
                        topic=f"decision/{market}/{symbol}",
                        content={
                            "decision": decision,
                            "amount": amount,
                            "holdings": holdings,
                            "recommendation": recommendation,
                            "confidence": confidence,
                        },
                        knowledge_type=KnowledgeType.DECISION,
                        metadata={
                            "source_knowledge_id": knowledge.knowledge_id,
                            "timestamp": datetime.now().isoformat(),
                            "priority": 1.0,
                        },
                        tags={"decision", market, symbol, decision},
                    )

                    logger.info(
                        f"Made decision for {market}/{symbol}: {decision} {amount}"
                    )

    async def process_knowledge(self, knowledge: KnowledgeItem) -> None:
        """
        Process a knowledge item.

        Args:
            knowledge: Knowledge item to process
        """
        # Process knowledge specific to the executive agent
        pass


async def main():
    """Main function."""
    # Create and set the event bus
    event_bus = InMemoryEventBus(bus_id="example_bus")
    set_event_bus(event_bus)

    # Create the knowledge repository
    repository = InMemoryKnowledgeRepository(repository_id="example_repository")
    await repository.start()

    # Create the coordinator
    coordinator = InMemoryCoordinator(coordinator_id="example_coordinator")
    await coordinator.start()

    # Create agents
    market_agent = MarketUnifiedAgent(repository)
    analysis_agent = AnalysisUnifiedAgent(repository)
    executive_agent = ExecutiveUnifiedAgent(repository)

    # Register agents with the coordinator
    await coordinator.register_agent(market_agent)
    await coordinator.register_agent(analysis_agent)
    await coordinator.register_agent(executive_agent)

    # Start agents
    await coordinator.start_agent(market_agent.agent_id)
    await coordinator.start_agent(analysis_agent.agent_id)
    await coordinator.start_agent(executive_agent.agent_id)

    # Wait for processing to complete
    await asyncio.sleep(5)

    # Get all knowledge
    all_knowledge = await repository.get_all_knowledge()
    logger.info(f"Total knowledge items: {len(all_knowledge)}")

    # Get knowledge by type
    decisions = await repository.get_knowledge_by_type(KnowledgeType.DECISION)
    logger.info(f"Decision knowledge items: {len(decisions)}")
    for decision in decisions:
        logger.info(f"Decision: {decision.topic} - {decision.content}")

    # Get knowledge updates
    since_timestamp = datetime.now() - timedelta(minutes=5)
    updates = await repository.get_knowledge_updates(since_timestamp)
    logger.info(f"Recent updates: {len(updates)}")

    # Get critical updates
    critical_updates = await repository.get_critical_updates(
        since_timestamp, priority_threshold=0.8
    )
    logger.info(f"Critical updates: {len(critical_updates)}")
    for update in critical_updates:
        logger.info(f"Critical update: {update.topic} - {update.metadata}")

    # Stop agents
    await coordinator.stop_agent(executive_agent.agent_id)
    await coordinator.stop_agent(analysis_agent.agent_id)
    await coordinator.stop_agent(market_agent.agent_id)

    # Stop the coordinator
    await coordinator.stop()

    # Stop the repository
    await repository.stop()


if __name__ == "__main__":
    asyncio.run(main())
