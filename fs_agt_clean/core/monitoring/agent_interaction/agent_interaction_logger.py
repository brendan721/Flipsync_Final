"""
UnifiedAgent interaction logger for FlipSync.

This module provides specialized logging for agent interactions, including:
- Message flow tracking between agents
- Correlation ID system for tracking requests across components
- Visualization data structures for agent interaction patterns
- Performance metrics for agent communications

It builds on the core logging system to provide agent-specific monitoring
capabilities that support FlipSync's vision of an interconnected agent system.
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.monitoring.logger import (
    LogManager,
    get_correlation_id,
    get_log_manager,
    get_logger,
    set_correlation_id,
)
from fs_agt_clean.core.monitoring.metrics.collector import (
    MetricCategory,
    MetricsCollector,
    MetricType,
    get_metrics_collector,
    record_metric,
)
from fs_agt_clean.core.monitoring.models import (
    UnifiedAgentMessage,
    UnifiedAgentMessageStatus,
    UnifiedAgentMessageType,
)


class UnifiedAgentInteraction:
    """An interaction between agents."""

    def __init__(
        self,
        interaction_id: str,
        correlation_id: str,
        start_time: datetime,
        last_updated: datetime,
        agents: Set[str],
        messages: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an agent interaction.

        Args:
            interaction_id: Interaction ID
            correlation_id: Correlation ID
            start_time: Start time
            last_updated: Last updated time
            agents: Set of agent IDs involved
            messages: List of message IDs
            metadata: Optional metadata
        """
        self.interaction_id = interaction_id
        self.correlation_id = correlation_id
        self.start_time = start_time
        self.last_updated = last_updated
        self.agents = agents
        self.messages = messages
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "interaction_id": self.interaction_id,
            "correlation_id": self.correlation_id,
            "start_time": self.start_time.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "agents": list(self.agents),
            "messages": self.messages,
            "metadata": self.metadata,
        }


class UnifiedAgentInteractionLogger:
    """
    Specialized logger for agent interactions.

    This class provides logging capabilities specifically designed for
    tracking and analyzing interactions between agents, including:
    - Message flow tracking
    - Correlation ID system
    - Performance metrics
    - Visualization data

    It supports FlipSync's vision of an interconnected agent system by
    providing visibility into agent communications.
    """

    _instance = None
    _lock = threading.RLock()
    _initialized = False
    _interactions: Dict[str, UnifiedAgentInteraction] = {}
    _messages: Dict[str, UnifiedAgentMessage] = {}
    _active_correlations: Set[str] = set()

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UnifiedAgentInteractionLogger, cls).__new__(cls)
            return cls._instance

    def __init__(
        self,
        storage_path: Optional[Union[str, Path]] = None,
        enable_metrics: bool = True,
        enable_visualization: bool = True,
        mobile_optimized: bool = False,
    ):
        """
        Initialize the agent interaction logger.

        Args:
            storage_path: Path to store interaction logs
            enable_metrics: Whether to collect metrics
            enable_visualization: Whether to generate visualization data
            mobile_optimized: Whether to optimize for mobile environments
        """
        with self._lock:
            if self._initialized:
                return

            # Set up logger
            self.logger = get_logger("agent_interaction")

            # Set up storage
            self.storage_path = (
                Path(storage_path) if storage_path else Path("logs/agent_interactions")
            )
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Store configuration
            self.enable_metrics = enable_metrics
            self.enable_visualization = enable_visualization
            self.mobile_optimized = mobile_optimized

            # Set up metrics collector
            self.metrics_collector = get_metrics_collector()

            # Start background tasks
            self._is_running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            self._initialized = True
            self.logger.info("UnifiedAgent interaction logger initialized")

    async def log_message(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: UnifiedAgentMessageType,
        content: Any,
        interaction_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log a message between agents.

        Args:
            sender_id: ID of the sending agent
            receiver_id: ID of the receiving agent
            message_type: Type of message
            content: Message content
            interaction_id: Optional interaction ID
            correlation_id: Optional correlation ID
            metadata: Optional metadata

        Returns:
            Message ID
        """
        # Generate IDs if not provided
        message_id = str(uuid.uuid4())
        interaction_id = interaction_id or str(uuid.uuid4())
        correlation_id = (
            correlation_id or get_correlation_id("default") or str(uuid.uuid4())
        )

        # Set correlation ID for context
        set_correlation_id("default", correlation_id)
        self._active_correlations.add(correlation_id)

        # Create message
        timestamp = datetime.now(timezone.utc)
        message = UnifiedAgentMessage(
            message_id=message_id,
            interaction_id=interaction_id,
            correlation_id=correlation_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            status=UnifiedAgentMessageStatus.SENT,
            timestamp=timestamp,
            metadata=metadata or {},
        )

        # Store message
        self._messages[message_id] = message

        # Update or create interaction
        if interaction_id in self._interactions:
            self._interactions[interaction_id].messages.append(message_id)
            self._interactions[interaction_id].last_updated = timestamp
        else:
            interaction = UnifiedAgentInteraction(
                interaction_id=interaction_id,
                correlation_id=correlation_id,
                start_time=timestamp,
                last_updated=timestamp,
                agents={sender_id, receiver_id},
                messages=[message_id],
                metadata=metadata or {},
            )
            self._interactions[interaction_id] = interaction

        # Log message
        self.logger.info(
            f"UnifiedAgent message: {sender_id} -> {receiver_id} ({message_type.name})",
            extra={
                "message_id": message_id,
                "interaction_id": interaction_id,
                "correlation_id": correlation_id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "message_type": message_type.name,
            },
        )

        # Record metrics
        if self.enable_metrics:
            await record_metric(
                name="agent_messages",
                value=1.0,
                metric_type=MetricType.COUNTER,
                category=MetricCategory.AGENT,
                labels={
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "message_type": message_type.name,
                },
            )

        # Store to disk if not mobile optimized
        if not self.mobile_optimized:
            await self._store_message(message)

        return message_id

    async def update_message_status(
        self,
        message_id: str,
        status: UnifiedAgentMessageStatus,
        response_time: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Update the status of a message.

        Args:
            message_id: Message ID
            status: New status
            response_time: Optional response time in seconds
            error: Optional error message
        """
        if message_id not in self._messages:
            self.logger.warning(f"Message {message_id} not found")
            return

        # Update message
        message = self._messages[message_id]
        message.status = status
        message.response_time = response_time
        message.error = error

        # Update interaction
        interaction_id = message.interaction_id
        if interaction_id in self._interactions:
            self._interactions[interaction_id].last_updated = datetime.now(timezone.utc)

        # Log update
        self.logger.info(
            f"UnifiedAgent message status updated: {message_id} -> {status.name}",
            extra={
                "message_id": message_id,
                "interaction_id": message.interaction_id,
                "correlation_id": message.correlation_id,
                "status": status.name,
                "response_time": response_time,
                "error": error,
            },
        )

        # Record metrics
        if self.enable_metrics and response_time is not None:
            await record_metric(
                name="agent_message_response_time",
                value=response_time,
                metric_type=MetricType.HISTOGRAM,
                category=MetricCategory.AGENT,
                labels={
                    "sender_id": message.sender_id,
                    "receiver_id": message.receiver_id,
                    "message_type": message.message_type.name,
                    "status": status.name,
                },
            )

        # Store to disk if not mobile optimized
        if not self.mobile_optimized:
            await self._store_message(message)

    async def get_interaction(self, interaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an interaction by ID.

        Args:
            interaction_id: Interaction ID

        Returns:
            Interaction data or None if not found
        """
        if interaction_id not in self._interactions:
            return None

        interaction = self._interactions[interaction_id]

        # Get all messages in the interaction
        messages = []
        for message_id in interaction.messages:
            if message_id in self._messages:
                messages.append(self._messages[message_id].to_dict())

        # Create interaction data
        interaction_data = interaction.to_dict()
        interaction_data["messages"] = messages

        return interaction_data

    async def get_interactions_by_correlation(
        self, correlation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all interactions for a correlation ID.

        Args:
            correlation_id: Correlation ID

        Returns:
            List of interaction data
        """
        interactions = []

        for interaction_id, interaction in self._interactions.items():
            if interaction.correlation_id == correlation_id:
                interaction_data = await self.get_interaction(interaction_id)
                if interaction_data:
                    interactions.append(interaction_data)

        return interactions

    async def get_agent_interactions(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get all interactions involving an agent.

        Args:
            agent_id: UnifiedAgent ID

        Returns:
            List of interaction data
        """
        interactions = []

        for interaction_id, interaction in self._interactions.items():
            if agent_id in interaction.agents:
                interaction_data = await self.get_interaction(interaction_id)
                if interaction_data:
                    interactions.append(interaction_data)

        return interactions

    async def export_visualization_data(
        self,
        format: str = "json",
        destination: Optional[Union[str, Path]] = None,
        time_range_hours: int = 24,
    ) -> Union[str, Dict[str, Any]]:
        """
        Export visualization data for agent interactions.

        Args:
            format: Output format (json, html, cytoscape)
            destination: Optional file destination
            time_range_hours: Time range in hours

        Returns:
            Visualization data in the specified format
        """
        if not self.enable_visualization:
            return {"error": "Visualization not enabled"}

        # Calculate time cutoff
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)

        # Collect nodes (agents)
        agents = set()
        for interaction in self._interactions.values():
            if interaction.start_time >= cutoff_time:
                agents.update(interaction.agents)

        # Collect edges (messages)
        edges = []
        for message in self._messages.values():
            if message.timestamp >= cutoff_time:
                edges.append(
                    {
                        "source": message.sender_id,
                        "target": message.receiver_id,
                        "type": message.message_type.name,
                        "id": message.message_id,
                    }
                )

        # Create visualization data
        visualization_data = {
            "nodes": [{"id": agent_id, "label": agent_id} for agent_id in agents],
            "edges": edges,
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "time_range_hours": time_range_hours,
            },
        }

        # Format output
        if format == "json":
            output = json.dumps(visualization_data, indent=2)
        elif format == "html":
            # Simple HTML visualization
            output = self._generate_html_visualization(visualization_data)
        elif format == "cytoscape":
            # Cytoscape.js format
            output = json.dumps(
                {
                    "elements": {
                        "nodes": [
                            {"data": node} for node in visualization_data["nodes"]
                        ],
                        "edges": [
                            {"data": edge} for edge in visualization_data["edges"]
                        ],
                    },
                },
                indent=2,
            )
        else:
            output = json.dumps(visualization_data, indent=2)

        # Save to file if destination provided
        if destination:
            path = Path(destination)
            with open(path, "w") as f:
                f.write(output)

        return output

    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up old data."""
        while self._is_running:
            try:
                # Clean up old interactions and messages
                await self._cleanup_old_data()

                # Store data to disk
                if not self.mobile_optimized:
                    await self._store_data()
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")

            # Wait for next cleanup interval
            await asyncio.sleep(3600)  # 1 hour

    async def _cleanup_old_data(self) -> None:
        """Clean up old interactions and messages."""
        # Calculate cutoff time (30 days)
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=30)

        # Clean up old interactions
        old_interactions = []
        for interaction_id, interaction in self._interactions.items():
            if interaction.last_updated < cutoff_time:
                old_interactions.append(interaction_id)

        for interaction_id in old_interactions:
            del self._interactions[interaction_id]

        # Clean up old messages
        old_messages = []
        for message_id, message in self._messages.items():
            if message.timestamp < cutoff_time:
                old_messages.append(message_id)

        for message_id in old_messages:
            del self._messages[message_id]

        # Clean up old correlations
        old_correlations = set()
        for correlation_id in self._active_correlations:
            # Check if any interactions still use this correlation
            if not any(
                i.correlation_id == correlation_id for i in self._interactions.values()
            ):
                old_correlations.add(correlation_id)

        self._active_correlations -= old_correlations

        self.logger.info(
            f"Cleaned up old data: {len(old_interactions)} interactions, {len(old_messages)} messages, {len(old_correlations)} correlations"
        )

    async def _store_message(self, message: UnifiedAgentMessage) -> None:
        """Store a message to disk."""
        try:
            # Create directory for interaction
            interaction_dir = self.storage_path / message.interaction_id
            interaction_dir.mkdir(parents=True, exist_ok=True)

            # Store message
            message_path = interaction_dir / f"{message.message_id}.json"
            with open(message_path, "w") as f:
                json.dump(message.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error storing message: {e}")

    async def _store_data(self) -> None:
        """Store all data to disk."""
        try:
            # Store interactions
            interactions_path = self.storage_path / "interactions.json"
            self.storage_path.mkdir(parents=True, exist_ok=True)
            with open(interactions_path, "w") as f:
                interactions_data = {
                    interaction_id: interaction.to_dict()
                    for interaction_id, interaction in self._interactions.items()
                }
                json.dump(interactions_data, f, indent=2)

            # Store active correlations
            correlations_path = self.storage_path / "correlations.json"
            with open(correlations_path, "w") as f:
                json.dump(list(self._active_correlations), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error storing data: {e}")

    def _generate_html_visualization(self, data: Dict[str, Any]) -> str:
        """Generate HTML visualization for agent interactions."""
        nodes_json = json.dumps(data["nodes"])
        edges_json = json.dumps(data["edges"])

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>UnifiedAgent Interaction Visualization</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
    <style>
        #cy {{
            width: 100%;
            height: 800px;
            display: block;
        }}
    </style>
</head>
<body>
    <h1>UnifiedAgent Interaction Visualization</h1>
    <div id="cy"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const nodes = {nodes_json};
            const edges = {edges_json};

            const cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: {{
                    nodes: nodes.map(node => ({{
                        data: {{ id: node.id, label: node.label }}
                    }})),
                    edges: edges.map(edge => ({{
                        data: {{
                            id: edge.id,
                            source: edge.source,
                            target: edge.target,
                            label: edge.type
                        }}
                    }}))
                }},
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)',
                            'background-color': '#6FB1FC',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'width': '60px',
                            'height': '60px'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'label': 'data(label)',
                            'width': 3,
                            'line-color': '#ccc',
                            'target-arrow-color': '#ccc',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier'
                        }}
                    }}
                ],
                layout: {{
                    name: 'circle'
                }}
            }});
        }});
    </script>
</body>
</html>
"""
        return html

    async def close(self) -> None:
        """Close the logger and clean up resources."""
        self._is_running = False
        if hasattr(self, "_cleanup_task") and self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


# Singleton instance
_agent_interaction_logger_instance = None


def get_agent_interaction_logger() -> UnifiedAgentInteractionLogger:
    """
    Get the agent interaction logger instance.

    Returns:
        UnifiedAgentInteractionLogger instance
    """
    global _agent_interaction_logger_instance
    if _agent_interaction_logger_instance is None:
        _agent_interaction_logger_instance = UnifiedAgentInteractionLogger()
    return _agent_interaction_logger_instance


async def log_agent_message(
    sender_id: str,
    receiver_id: str,
    message_type: UnifiedAgentMessageType,
    content: Any,
    interaction_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Log a message between agents.

    Args:
        sender_id: ID of the sending agent
        receiver_id: ID of the receiving agent
        message_type: Type of message
        content: Message content
        interaction_id: Optional interaction ID
        correlation_id: Optional correlation ID
        metadata: Optional metadata

    Returns:
        Message ID
    """
    return await get_agent_interaction_logger().log_message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_type=message_type,
        content=content,
        interaction_id=interaction_id,
        correlation_id=correlation_id,
        metadata=metadata,
    )


async def update_agent_message_status(
    message_id: str,
    status: UnifiedAgentMessageStatus,
    response_time: Optional[float] = None,
    error: Optional[str] = None,
) -> None:
    """
    Update the status of a message.

    Args:
        message_id: Message ID
        status: New status
        response_time: Optional response time in seconds
        error: Optional error message
    """
    await get_agent_interaction_logger().update_message_status(
        message_id=message_id,
        status=status,
        response_time=response_time,
        error=error,
    )
