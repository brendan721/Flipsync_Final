"""Main listing generation and synchronization engine."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from fs_agt_clean.core.compliance.audit_logger import ComplianceAuditLogger
from fs_agt_clean.core.monitoring.metrics_collector import MetricsCollector

# Import rate limiter when needed
# from fs_agt_clean.core.security.rate_limiter import RateLimitConfig
from fs_agt_clean.core.services.communication import Event, EventBus, EventType

from .content_optimizer import ContentOptimizer
from .generation_models import ListingContent, OptimizationResult

logger = logging.getLogger(__name__)


class ListingGenerator:
    """Generates and synchronizes listing content across platforms."""

    def __init__(
        self,
        event_bus: EventBus,
        content_optimizer: ContentOptimizer,
        metrics_collector: MetricsCollector,
        audit_logger: ComplianceAuditLogger,
    ):
        """Initialize generator."""
        self.event_bus = event_bus
        self.content_optimizer = content_optimizer
        self.metrics_collector = metrics_collector
        self.audit_logger = audit_logger

        # We'll initialize rate limiter properly when we have Redis
        self.rate_limiter = None

        # Set up event subscriptions
        self._setup_subscriptions()

    def _setup_subscriptions(self) -> None:
        """Set up event subscriptions."""
        self.event_bus.subscribe(EventType.DATA_ACQUIRED, self._handle_market_analysis)

    async def _handle_market_analysis(self, event: Event) -> None:
        """Handle market analysis completion event."""
        try:
            analysis_results = event.data["analysis_results"]
            await self.generate_listing(analysis_results)
        except Exception as e:
            logger.error("Error handling market analysis: %s", str(e))
            await self._publish_error(str(e))

    async def process_asin(self, asin: str, sku: str) -> Dict[str, Any]:
        """Process an ASIN and generate listing content.

        Args:
            asin: Amazon ASIN
            sku: SKU to assign to the listing

        Returns:
            Dict containing processing results
        """
        try:
            # Rate limiting
            if self.rate_limiter:
                allowed, _ = await self.rate_limiter.is_allowed(
                    "api", "process_listing"
                )
                if not allowed:
                    # Wait a bit before retrying
                    await asyncio.sleep(1)

            # Generate listing content
            market_data = {
                "asin": asin,
                "sku": sku,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            listing_content = await self.generate_listing(market_data)

            if not listing_content:
                return {"success": False, "error": "Failed to generate listing content"}

            # Record success metrics
            await self.metrics_collector.record(
                "asin_processing_success", 1.0, {"asin": asin, "sku": sku}
            )

            # Convert ListingContent to dict
            content_dict = {
                "title": listing_content.title,
                "description": listing_content.description,
                "item_specifics": [
                    vars(spec) for spec in listing_content.item_specifics
                ],
                "keywords": [vars(kw) for kw in listing_content.keywords],
                "category_id": listing_content.category_id,
                "version": listing_content.version,
                "last_updated": listing_content.last_updated.isoformat(),
            }

            return {
                "success": True,
                "listing_id": str(uuid4()),  # Generate a unique listing ID
                "asin": asin,
                "sku": sku,
                "content": content_dict,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            error_msg = f"Error processing ASIN {asin}: {str(e)}"
            logger.error(error_msg)
            await self._publish_error(error_msg)

            # Record failure metrics
            await self.metrics_collector.record(
                "asin_processing_failure",
                1.0,
                {"asin": asin, "sku": sku, "error": str(e)},
            )

            return {"success": False, "error": error_msg, "asin": asin, "sku": sku}

    async def generate_listing(self, market_data: Dict) -> ListingContent:
        """Generate listing content from market data."""
        start_time = datetime.now(timezone.utc)

        try:
            # Rate limiting
            if self.rate_limiter:
                allowed, _ = await self.rate_limiter.is_allowed(
                    "api", "generate_listing"
                )
                if not allowed:
                    # Wait a bit before retrying
                    await asyncio.sleep(1)

            # Generate initial content
            content = await self._create_initial_content(market_data)

            # Optimize content
            optimization_result = await self.content_optimizer.optimize_listing(content)

            # Record metrics
            await self.metrics_collector.record(
                "listing_generation",
                (datetime.now(timezone.utc) - start_time).total_seconds(),
            )

            # Publish completion event
            await self._publish_completion(optimization_result)

            return optimization_result.optimized_content

        except Exception as e:
            logger.error("Error generating listing: %s", str(e))
            await self._publish_error(str(e))
            raise

    async def _create_initial_content(self, _market_data: Dict) -> ListingContent:
        """Create initial listing content from market data."""
        # Initial content creation logic here
        return ListingContent(
            title="",  # Placeholder
            description="",  # Placeholder
            item_specifics=[],  # Placeholder
            keywords=[],  # Placeholder
            category_id="",  # Placeholder
            metrics={},  # Placeholder
            last_updated=datetime.now(timezone.utc),
            version=1,
        )

    async def _publish_completion(self, result: OptimizationResult) -> None:
        """Publish listing generation completion event."""
        await self.event_bus.publish(
            Event(
                id=str(uuid4()),
                type=EventType.SYSTEM,
                data={
                    "listing": result.optimized_content,
                    "improvements": result.improvement_metrics,
                },
                timestamp=datetime.now(timezone.utc),
                source="listing_generator",
            )
        )

    async def _publish_error(self, error_message: str) -> None:
        """Publish error event."""
        await self.event_bus.publish(
            Event(
                id=str(uuid4()),
                type=EventType.ERROR_OCCURRED,
                data={"error_message": error_message},
                timestamp=datetime.now(timezone.utc),
                source="listing_generator",
            )
        )
