"""Metrics for knowledge sharing module."""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, Union

from fs_agt_clean.core.knowledge.config import DEFAULT_METRICS_WINDOW_SECONDS


class MetricEventType(str, Enum):
    """Types of metric events."""

    # Knowledge entry events
    KNOWLEDGE_PUBLISHED = "knowledge_published"
    KNOWLEDGE_VALIDATED = "knowledge_validated"
    KNOWLEDGE_REJECTED = "knowledge_rejected"
    KNOWLEDGE_UPDATED = "knowledge_updated"
    KNOWLEDGE_DELETED = "knowledge_deleted"

    # Subscription events
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_DELETED = "subscription_deleted"

    # Notification events
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_RECEIVED = "notification_received"
    NOTIFICATION_PROCESSED = "notification_processed"

    # Search events
    SEARCH_PERFORMED = "search_performed"

    # Error events
    VALIDATION_ERROR = "validation_error"
    SUBSCRIPTION_ERROR = "subscription_error"
    NOTIFICATION_ERROR = "notification_error"
    SEARCH_ERROR = "search_error"


@dataclass
class MetricEvent:
    """A metric event."""

    event_type: MetricEventType
    timestamp: float = field(default_factory=time.time)
    agent_id: Optional[str] = None
    knowledge_type: Optional[str] = None
    entry_id: Optional[str] = None
    subscription_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeSharingMetrics:
    """Metrics for knowledge sharing."""

    def __init__(
        self,
        window_seconds: int = DEFAULT_METRICS_WINDOW_SECONDS,
        callback: Optional[Callable[[MetricEventType, Dict[str, Any]], None]] = None,
    ):
        """Initialize metrics.

        Args:
            window_seconds: Window for metrics collection in seconds
            callback: Callback function for metrics events
        """
        self.window_seconds = window_seconds
        self.callback = callback
        self.events: Deque[MetricEvent] = deque()
        self.counters: Dict[MetricEventType, int] = defaultdict(int)
        self.agent_counters: Dict[str, Dict[MetricEventType, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self.knowledge_type_counters: Dict[str, Dict[MetricEventType, int]] = (
            defaultdict(lambda: defaultdict(int))
        )
        self.durations: Dict[MetricEventType, List[float]] = defaultdict(list)
        self.error_counts: Dict[MetricEventType, int] = defaultdict(int)

    def record_event(self, event: MetricEvent) -> None:
        """Record a metric event.

        Args:
            event: The metric event to record
        """
        # Add event to queue
        self.events.append(event)

        # Update counters
        self.counters[event.event_type] += 1

        # Update agent counters if agent_id is provided
        if event.agent_id:
            self.agent_counters[event.agent_id][event.event_type] += 1

        # Update knowledge type counters if knowledge_type is provided
        if event.knowledge_type:
            self.knowledge_type_counters[event.knowledge_type][event.event_type] += 1

        # Update durations if duration_ms is provided
        if event.duration_ms is not None:
            self.durations[event.event_type].append(event.duration_ms)

        # Update error counts if not successful
        if not event.success:
            self.error_counts[event.event_type] += 1

        # Call callback if provided
        if self.callback:
            self.callback(event.event_type, self._event_to_dict(event))

        # Clean up old events
        self._clean_old_events()

    def _event_to_dict(self, event: MetricEvent) -> Dict[str, Any]:
        """Convert event to dictionary.

        Args:
            event: The metric event to convert

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_type": event.event_type,
            "timestamp": event.timestamp,
            "agent_id": event.agent_id,
            "knowledge_type": event.knowledge_type,
            "entry_id": event.entry_id,
            "subscription_id": event.subscription_id,
            "tags": event.tags,
            "duration_ms": event.duration_ms,
            "success": event.success,
            "error_message": event.error_message,
            "metadata": event.metadata,
        }

    def _clean_old_events(self) -> None:
        """Clean up events older than the window."""
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove old events and update counters
        while self.events and self.events[0].timestamp < cutoff:
            event = self.events.popleft()
            self.counters[event.event_type] -= 1

            if event.agent_id:
                self.agent_counters[event.agent_id][event.event_type] -= 1
                if self.agent_counters[event.agent_id][event.event_type] == 0:
                    del self.agent_counters[event.agent_id][event.event_type]

            if event.knowledge_type:
                self.knowledge_type_counters[event.knowledge_type][
                    event.event_type
                ] -= 1
                if (
                    self.knowledge_type_counters[event.knowledge_type][event.event_type]
                    == 0
                ):
                    del self.knowledge_type_counters[event.knowledge_type][
                        event.event_type
                    ]

            if not event.success:
                self.error_counts[event.event_type] -= 1
                if self.error_counts[event.event_type] == 0:
                    del self.error_counts[event.event_type]

    def get_event_count(self, event_type: MetricEventType) -> int:
        """Get count of events by type.

        Args:
            event_type: The type of event to count

        Returns:
            Count of events
        """
        return self.counters.get(event_type, 0)

    def get_agent_event_count(self, agent_id: str, event_type: MetricEventType) -> int:
        """Get count of events by agent and type.

        Args:
            agent_id: The agent ID
            event_type: The type of event to count

        Returns:
            Count of events
        """
        return self.agent_counters.get(agent_id, {}).get(event_type, 0)

    def get_knowledge_type_event_count(
        self, knowledge_type: str, event_type: MetricEventType
    ) -> int:
        """Get count of events by knowledge type and event type.

        Args:
            knowledge_type: The knowledge type
            event_type: The type of event to count

        Returns:
            Count of events
        """
        return self.knowledge_type_counters.get(knowledge_type, {}).get(event_type, 0)

    def get_average_duration(self, event_type: MetricEventType) -> Optional[float]:
        """Get average duration of events by type.

        Args:
            event_type: The type of event

        Returns:
            Average duration in milliseconds, or None if no durations recorded
        """
        durations = self.durations.get(event_type, [])
        if not durations:
            return None
        return sum(durations) / len(durations)

    def get_error_rate(self, event_type: MetricEventType) -> float:
        """Get error rate of events by type.

        Args:
            event_type: The type of event

        Returns:
            Error rate as a fraction (0.0 to 1.0)
        """
        total = self.counters.get(event_type, 0)
        if total == 0:
            return 0.0
        errors = self.error_counts.get(event_type, 0)
        return errors / total

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of metrics.

        Returns:
            Dictionary with metrics summary
        """
        summary = {
            "window_seconds": self.window_seconds,
            "total_events": sum(self.counters.values()),
            "events_by_type": dict(self.counters),
            "error_rates": {
                event_type.value: self.get_error_rate(event_type)
                for event_type in MetricEventType
                if self.counters.get(event_type, 0) > 0
            },
            "average_durations": {
                event_type.value: self.get_average_duration(event_type)
                for event_type in MetricEventType
                if event_type in self.durations and self.durations[event_type]
            },
            "top_agents": self._get_top_agents(),
            "top_knowledge_types": self._get_top_knowledge_types(),
        }
        return summary

    def _get_top_agents(self, limit: int = 5) -> Dict[str, Dict[str, int]]:
        """Get top agents by event count.

        Args:
            limit: Maximum number of agents to return

        Returns:
            Dictionary with agent IDs and event counts
        """
        # Calculate total events per agent
        agent_totals = {
            agent_id: sum(counts.values())
            for agent_id, counts in self.agent_counters.items()
        }

        # Sort agents by total events
        top_agents = sorted(agent_totals.items(), key=lambda x: x[1], reverse=True)[
            :limit
        ]

        # Return detailed counts for top agents
        return {
            agent_id: {
                event_type.value: count
                for event_type, count in self.agent_counters[agent_id].items()
            }
            for agent_id, _ in top_agents
        }

    def _get_top_knowledge_types(self, limit: int = 5) -> Dict[str, Dict[str, int]]:
        """Get top knowledge types by event count.

        Args:
            limit: Maximum number of knowledge types to return

        Returns:
            Dictionary with knowledge types and event counts
        """
        # Calculate total events per knowledge type
        knowledge_type_totals = {
            knowledge_type: sum(counts.values())
            for knowledge_type, counts in self.knowledge_type_counters.items()
        }

        # Sort knowledge types by total events
        top_knowledge_types = sorted(
            knowledge_type_totals.items(), key=lambda x: x[1], reverse=True
        )[:limit]

        # Return detailed counts for top knowledge types
        return {
            knowledge_type: {
                event_type.value: count
                for event_type, count in self.knowledge_type_counters[
                    knowledge_type
                ].items()
            }
            for knowledge_type, _ in top_knowledge_types
        }


def create_metrics_callback(
    log_to_console: bool = True,
    log_to_file: bool = False,
    log_file_path: Optional[str] = None,
) -> Callable[[MetricEventType, Dict[str, Any]], None]:
    """Create a callback function for metrics events.

    Args:
        log_to_console: Whether to log events to console
        log_to_file: Whether to log events to file
        log_file_path: Path to log file

    Returns:
        Callback function
    """

    def callback(event_type: MetricEventType, event_data: Dict[str, Any]) -> None:
        """Callback function for metrics events.

        Args:
            event_type: Type of event
            event_data: Event data
        """
        timestamp = datetime.fromtimestamp(event_data["timestamp"]).isoformat()
        message = f"[{timestamp}] {event_type.value}"

        if event_data.get("agent_id"):
            message += f" | UnifiedAgent: {event_data['agent_id']}"

        if event_data.get("knowledge_type"):
            message += f" | Type: {event_data['knowledge_type']}"

        if event_data.get("entry_id"):
            message += f" | Entry: {event_data['entry_id']}"

        if event_data.get("duration_ms") is not None:
            message += f" | Duration: {event_data['duration_ms']:.2f}ms"

        if not event_data.get("success", True):
            message += f" | ERROR: {event_data.get('error_message', 'Unknown error')}"

        if log_to_console:
            print(message)

        if log_to_file and log_file_path:
            with open(log_file_path, "a") as f:
                f.write(message + "\n")

    return callback
