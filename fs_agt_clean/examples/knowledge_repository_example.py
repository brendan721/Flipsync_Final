"""
Example of using the Knowledge Repository component.

This example demonstrates how to use the Knowledge Repository component to store,
retrieve, and share knowledge between agents.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

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
    EmbeddingProvider,
    InMemoryKnowledgeRepository,
    InMemoryVectorStorage,
    KnowledgeCache,
    KnowledgeError,
    KnowledgeItem,
    KnowledgeStatus,
    KnowledgeType,
    KnowledgeValidator,
    LRUCache,
    SchemaValidator,
    SimpleEmbeddingProvider,
    TopicFilter,
    VectorStorage,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("knowledge_repository_example")


class MarketKnowledgeUnifiedAgent:
    """
    UnifiedAgent that provides market knowledge.
    """

    def __init__(self):
        """Initialize the market knowledge agent."""
        self.agent_id = "market_agent"
        self.name = "Market Knowledge UnifiedAgent"

        # Create publisher and subscriber
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

    async def start(self, repository):
        """
        Start the market knowledge agent.

        Args:
            repository: The knowledge repository
        """
        logger.info(f"Starting {self.name}")

        # Store the repository
        self.repository = repository

        # Subscribe to knowledge query events
        await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"knowledge_query"}),
            handler=self.handle_knowledge_query,
        )

        # Publish initial market knowledge
        await self.publish_market_knowledge()

        logger.info(f"{self.name} started")

    async def publish_market_knowledge(self):
        """Publish market knowledge to the repository."""
        # Publish crypto market knowledge
        for symbol, data in self.market_data["crypto"].items():
            await self.repository.publish_knowledge(
                knowledge_type=KnowledgeType.FACT,
                topic=f"market/crypto/{symbol}",
                content=data,
                metadata={
                    "market": "crypto",
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                },
                source_id=self.agent_id,
                tags={"market", "crypto", symbol},
            )

        # Publish stock market knowledge
        for symbol, data in self.market_data["stocks"].items():
            await self.repository.publish_knowledge(
                knowledge_type=KnowledgeType.FACT,
                topic=f"market/stocks/{symbol}",
                content=data,
                metadata={
                    "market": "stocks",
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                },
                source_id=self.agent_id,
                tags={"market", "stocks", symbol},
            )

        logger.info("Published market knowledge")

    async def handle_knowledge_query(self, event):
        """
        Handle a knowledge query event.

        Args:
            event: The knowledge query event
        """
        # Extract query information
        query = event.data.get("query")
        query_type = event.data.get("query_type")

        logger.info(f"Received knowledge query: {query} ({query_type})")


class AnalysisUnifiedAgent:
    """
    UnifiedAgent that analyzes market knowledge.
    """

    def __init__(self):
        """Initialize the analysis agent."""
        self.agent_id = "analysis_agent"
        self.name = "Analysis UnifiedAgent"

        # Create publisher and subscriber
        self.publisher = create_publisher(source_id=self.agent_id)
        self.subscriber = create_subscriber(subscriber_id=self.agent_id)

    async def start(self, repository):
        """
        Start the analysis agent.

        Args:
            repository: The knowledge repository
        """
        logger.info(f"Starting {self.name}")

        # Store the repository
        self.repository = repository

        # Subscribe to knowledge added events
        await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"knowledge_added"}),
            handler=self.handle_knowledge_added,
        )

        # Subscribe to market knowledge
        await self.repository.subscribe(
            filter=TopicFilter(topics={"market/crypto/bitcoin", "market/stocks/aapl"}),
            handler=self.handle_market_knowledge,
        )

        logger.info(f"{self.name} started")

    async def handle_knowledge_added(self, event):
        """
        Handle a knowledge added event.

        Args:
            event: The knowledge added event
        """
        # Extract knowledge information
        knowledge_id = event.data.get("knowledge_id")
        topic = event.data.get("topic")

        logger.info(f"Knowledge added: {knowledge_id} ({topic})")

    async def handle_market_knowledge(self, knowledge):
        """
        Handle market knowledge.

        Args:
            knowledge: The market knowledge
        """
        logger.info(f"Received market knowledge: {knowledge.topic}")

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
            await self.repository.publish_knowledge(
                knowledge_type=KnowledgeType.RELATION,
                topic=f"{knowledge.topic}/analysis",
                content={
                    "recommendation": recommendation,
                    "confidence": confidence,
                    "price": price,
                    "volume": volume,
                    "analysis": f"Based on price and volume analysis, the recommendation is to {recommendation} with {confidence:.1f} confidence.",
                },
                metadata={
                    "source_knowledge_id": knowledge.knowledge_id,
                    "timestamp": datetime.now().isoformat(),
                },
                source_id=self.agent_id,
                tags={"analysis", "recommendation", recommendation},
            )

            logger.info(
                f"Published analysis for {knowledge.topic}: {recommendation} ({confidence:.1f})"
            )


async def main():
    """Main function."""
    # Create and set the event bus
    event_bus = InMemoryEventBus(bus_id="example_bus")
    set_event_bus(event_bus)

    # Create the knowledge repository
    repository = InMemoryKnowledgeRepository(repository_id="example_repository")
    await repository.start()

    # Create agents
    market_agent = MarketKnowledgeUnifiedAgent()
    analysis_agent = AnalysisUnifiedAgent()

    # Start agents
    await market_agent.start(repository)
    await analysis_agent.start(repository)

    # Wait for a moment to allow processing
    await asyncio.sleep(1)

    # Search for knowledge
    logger.info("Searching for bitcoin knowledge...")
    results = await repository.search_knowledge("bitcoin", limit=5)
    for result in results:
        logger.info(f"Found: {result.knowledge.topic} (score: {result.score:.2f})")
        logger.info(f"Content: {result.knowledge.content}")

    # Get knowledge by topic
    logger.info("Getting knowledge by topic...")
    bitcoin_knowledge = await repository.get_knowledge_by_topic("market/crypto/bitcoin")
    if bitcoin_knowledge:
        logger.info(f"Bitcoin knowledge: {bitcoin_knowledge[0].content}")

    # Get knowledge by tag
    logger.info("Getting knowledge by tag...")
    buy_recommendations = await repository.get_knowledge_by_tag("buy")
    for knowledge in buy_recommendations:
        logger.info(f"Buy recommendation: {knowledge.topic}")
        logger.info(f"Content: {knowledge.content}")

    # Stop the repository
    await repository.stop()


if __name__ == "__main__":
    asyncio.run(main())
