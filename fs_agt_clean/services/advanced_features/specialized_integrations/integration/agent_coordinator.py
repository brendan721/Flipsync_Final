from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

from fs_agt_clean.core.metrics_service.metrics_collector import MetricsCollector
from fs_agt_clean.core.services.communication import Event, EventBus, EventType


class UnifiedAgentCoordinator:
    """Coordinates interactions between different agents in the system."""

    def __init__(
        self,
        event_bus: EventBus,
        acquisition_agent: Mock,
        market_analysis_agent: Mock,
        listing_generation_agent: Mock,
        metrics_collector: MetricsCollector,
    ):
        self.event_bus = event_bus
        self.acquisition_agent = acquisition_agent
        self.market_analysis_agent = market_analysis_agent
        self.listing_generation_agent = listing_generation_agent
        self.metrics_collector = metrics_collector
        self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Set up event handlers for different event types."""
        self.event_bus.subscribe(EventType.DATA_ACQUIRED, self._handle_data_acquired)
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, self._handle_error)

    async def _handle_data_acquired(self, event: Event) -> None:
        """Handle data acquisition events."""
        try:
            if event.data.get("products"):
                await self.market_analysis_agent.analyze_products(
                    event.data["products"]
                )
        except Exception as e:
            await self._publish_error(str(e), "market_analysis_agent")

    async def _handle_error(self, event: Event) -> None:
        """Handle error events."""
        error_message = event.data.get("error_message", "Unknown error")
        error_context = {
            "source": event.data.get("source", "unknown"),
            "error_type": event.data.get("error_type", "Error"),
        }
        error = ValueError(error_message)
        await self.metrics_collector.record_error(error=error, context=error_context)

    async def _publish_error(self, error_message: str, source: str) -> None:
        """Publish an error event."""
        error_event = Event(
            type=EventType.ERROR_OCCURRED,
            data={
                "error_message": error_message,
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
            },
            source=source,
        )
        await self.event_bus.publish(error_event)

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics."""
        return {
            "data_acquisition_latency": await self.metrics_collector.get_average_latency(
                "data_acquisition_processing"
            ),
            "market_analysis_latency": await self.metrics_collector.get_average_latency(
                "market_analysis_processing"
            ),
            "total_errors": await self.metrics_collector.get_total_errors(),
            "success_rate": await self.metrics_collector.get_success_rate(),
        }
