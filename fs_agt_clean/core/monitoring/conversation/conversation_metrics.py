"""
Conversation metrics collector for FlipSync.

This module provides metrics collection for conversational interactions, including:
- Conversation quality metrics
- Intent/response tracking
- Conversation flow tracking
- Dashboard data for visualization

It supports FlipSync's vision of a conversational interface by providing
visibility into conversation quality and effectiveness.
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from fs_agt_clean.core.monitoring.logger import get_logger
from fs_agt_clean.core.monitoring.metrics.collector import (
    MetricCategory,
    MetricType,
    record_metric,
)
from fs_agt_clean.core.monitoring.models import (
    ConversationMetrics,
    ConversationStatus,
)


class ConversationMetricsCollector:
    """
    Collects and analyzes metrics for conversational interactions.

    This class provides metrics collection for conversational interactions, including:
    - Conversation quality metrics (sentiment, satisfaction)
    - Intent/response tracking
    - Conversation flow tracking
    - Dashboard data for visualization

    It supports FlipSync's vision of a conversational interface by providing
    visibility into conversation quality and effectiveness.
    """

    _instance = None
    _lock = threading.RLock()
    _initialized = False
    _conversations: Dict[str, ConversationMetrics] = {}
    _intents: Dict[str, Dict[str, int]] = {}  # conversation_id -> intent -> count
    _responses: Dict[str, Dict[str, int]] = {}  # conversation_id -> response -> count

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConversationMetricsCollector, cls).__new__(cls)
            return cls._instance

    def __init__(
        self,
        storage_path: Optional[Union[str, Path]] = None,
        enable_sentiment_analysis: bool = True,
        enable_dashboard_data: bool = True,
        mobile_optimized: bool = False,
    ):
        """
        Initialize the conversation metrics collector.

        Args:
            storage_path: Path to store metrics data
            enable_sentiment_analysis: Whether to enable sentiment analysis
            enable_dashboard_data: Whether to generate dashboard data
            mobile_optimized: Whether to optimize for mobile environments
        """
        with self._lock:
            if self._initialized:
                return

            # Set up logger
            self.logger = get_logger("conversation_metrics")

            # Set up storage
            self.storage_path = (
                Path(storage_path)
                if storage_path
                else Path("logs/conversation_metrics")
            )
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Store configuration
            self.enable_sentiment_analysis = enable_sentiment_analysis
            self.enable_dashboard_data = enable_dashboard_data
            self.mobile_optimized = mobile_optimized

            # Initialize background task variables
            self._is_running = True
            self._cleanup_task = None

            self._initialized = True
            self.logger.info("Conversation metrics collector initialized")

    async def start_conversation(
        self,
        conversation_id: str,
        user_id: str,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMetrics:
        """
        Start tracking a new conversation.

        Args:
            conversation_id: Unique conversation ID
            user_id: UnifiedUser ID
            agent_id: UnifiedAgent ID
            metadata: Optional metadata

        Returns:
            ConversationMetrics instance
        """
        # Create conversation metrics
        metrics = ConversationMetrics(
            conversation_id=conversation_id,
            user_id=user_id,
            agent_id=agent_id,
            start_time=datetime.now(timezone.utc),
            status=ConversationStatus.ACTIVE,
            turns=0,
            user_turns=0,
            agent_turns=0,
            metadata=metadata or {},
        )

        # Store conversation
        self._conversations[conversation_id] = metrics

        # Initialize intent and response tracking
        self._intents[conversation_id] = {}
        self._responses[conversation_id] = {}

        # Log start
        self.logger.info(
            f"Conversation started: {conversation_id} (user: {user_id}, agent: {agent_id})",
            extra={
                "conversation_id": conversation_id,
                "user_id": user_id,
                "agent_id": agent_id,
            },
        )

        # Record metric
        await record_metric(
            name="conversations_started",
            value=1.0,
            metric_type=MetricType.COUNTER,
            category=MetricCategory.CONVERSATION,
            labels={"agent_id": agent_id},
        )

        return metrics

    async def end_conversation(
        self,
        conversation_id: str,
        status: ConversationStatus = ConversationStatus.COMPLETED,
        satisfaction_score: Optional[float] = None,
        success_rate: Optional[float] = None,
        completion_rate: Optional[float] = None,
    ) -> Optional[ConversationMetrics]:
        """
        End a conversation and finalize metrics.

        Args:
            conversation_id: Conversation ID
            status: Final conversation status
            satisfaction_score: Optional satisfaction score (0.0 to 1.0)
            success_rate: Optional success rate (0.0 to 1.0)
            completion_rate: Optional completion rate (0.0 to 1.0)

        Returns:
            Updated ConversationMetrics or None if not found
        """
        if conversation_id not in self._conversations:
            self.logger.warning(f"Conversation {conversation_id} not found")
            return None

        # Get conversation
        metrics = self._conversations[conversation_id]

        # Update metrics
        metrics.end_time = datetime.now(timezone.utc)
        metrics.status = status
        metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()

        if satisfaction_score is not None:
            metrics.satisfaction_score = max(0.0, min(1.0, satisfaction_score))

        if success_rate is not None:
            metrics.success_rate = max(0.0, min(1.0, success_rate))

        if completion_rate is not None:
            metrics.completion_rate = max(0.0, min(1.0, completion_rate))

        # Log end
        self.logger.info(
            f"Conversation ended: {conversation_id} (status: {status.name}, duration: {metrics.duration:.1f}s)",
            extra={
                "conversation_id": conversation_id,
                "status": status.name,
                "duration": metrics.duration,
                "turns": metrics.turns,
                "satisfaction_score": metrics.satisfaction_score,
                "success_rate": metrics.success_rate,
            },
        )

        # Record metrics
        await record_metric(
            name="conversation_duration",
            value=metrics.duration,
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.CONVERSATION,
            labels={
                "agent_id": metrics.agent_id,
                "status": status.name,
            },
        )

        if metrics.satisfaction_score is not None:
            await record_metric(
                name="conversation_satisfaction",
                value=metrics.satisfaction_score,
                metric_type=MetricType.GAUGE,
                category=MetricCategory.CONVERSATION,
                labels={"agent_id": metrics.agent_id},
            )

        # Store to disk if not mobile optimized
        if not self.mobile_optimized:
            await self._store_conversation(metrics)

        return metrics

    async def record_user_turn(
        self,
        conversation_id: str,
        intent: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        content_length: Optional[int] = None,
    ) -> Optional[ConversationMetrics]:
        """
        Record a user turn in a conversation.

        Args:
            conversation_id: Conversation ID
            intent: Optional user intent
            sentiment_score: Optional sentiment score (-1.0 to 1.0)
            content_length: Optional content length in characters

        Returns:
            Updated ConversationMetrics or None if not found
        """
        if conversation_id not in self._conversations:
            self.logger.warning(f"Conversation {conversation_id} not found")
            return None

        # Get conversation
        metrics = self._conversations[conversation_id]

        # Update metrics
        metrics.turns += 1
        metrics.user_turns += 1

        # Track intent
        if intent:
            if intent not in self._intents[conversation_id]:
                self._intents[conversation_id][intent] = 0
            self._intents[conversation_id][intent] += 1

        # Update sentiment score
        if sentiment_score is not None and self.enable_sentiment_analysis:
            # Clamp to valid range
            sentiment_score = max(-1.0, min(1.0, sentiment_score))

            # Update running average
            if metrics.sentiment_score is None:
                metrics.sentiment_score = sentiment_score
            else:
                # Weighted average (more weight to recent scores)
                metrics.sentiment_score = (
                    0.7 * sentiment_score + 0.3 * metrics.sentiment_score
                )

        # Log turn
        self.logger.debug(
            f"UnifiedUser turn in conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "intent": intent,
                "sentiment_score": sentiment_score,
                "content_length": content_length,
                "turn_number": metrics.turns,
            },
        )

        # Record metrics
        if content_length is not None:
            await record_metric(
                name="user_message_length",
                value=content_length,
                metric_type=MetricType.HISTOGRAM,
                category=MetricCategory.CONVERSATION,
                labels={"agent_id": metrics.agent_id},
            )

        return metrics

    async def record_agent_turn(
        self,
        conversation_id: str,
        response_type: Optional[str] = None,
        content_length: Optional[int] = None,
        processing_time: Optional[float] = None,
    ) -> Optional[ConversationMetrics]:
        """
        Record an agent turn in a conversation.

        Args:
            conversation_id: Conversation ID
            response_type: Optional response type
            content_length: Optional content length in characters
            processing_time: Optional processing time in seconds

        Returns:
            Updated ConversationMetrics or None if not found
        """
        if conversation_id not in self._conversations:
            self.logger.warning(f"Conversation {conversation_id} not found")
            return None

        # Get conversation
        metrics = self._conversations[conversation_id]

        # Update metrics
        metrics.turns += 1
        metrics.agent_turns += 1

        # Track response type
        if response_type:
            if response_type not in self._responses[conversation_id]:
                self._responses[conversation_id][response_type] = 0
            self._responses[conversation_id][response_type] += 1

        # Log turn
        self.logger.debug(
            f"UnifiedAgent turn in conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "response_type": response_type,
                "content_length": content_length,
                "processing_time": processing_time,
                "turn_number": metrics.turns,
            },
        )

        # Record metrics
        if content_length is not None:
            await record_metric(
                name="agent_message_length",
                value=content_length,
                metric_type=MetricType.HISTOGRAM,
                category=MetricCategory.CONVERSATION,
                labels={"agent_id": metrics.agent_id},
            )

        if processing_time is not None:
            await record_metric(
                name="agent_response_time",
                value=processing_time,
                metric_type=MetricType.HISTOGRAM,
                category=MetricCategory.CONVERSATION,
                labels={
                    "agent_id": metrics.agent_id,
                    "response_type": response_type or "unknown",
                },
            )

        return metrics

    async def get_conversation_metrics(
        self, conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation metrics or None if not found
        """
        if conversation_id not in self._conversations:
            return None

        # Get conversation
        metrics = self._conversations[conversation_id]

        # Create metrics data
        data = metrics.to_dict()

        # Add intent and response data
        data["intents"] = self._intents.get(conversation_id, {})
        data["responses"] = self._responses.get(conversation_id, {})

        return data

    async def get_agent_metrics(
        self, agent_id: str, time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for an agent.

        Args:
            agent_id: UnifiedAgent ID
            time_range_hours: Time range in hours

        Returns:
            Aggregated metrics
        """
        # Calculate time cutoff
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)

        # Filter conversations by agent and time
        agent_conversations = [
            c
            for c in self._conversations.values()
            if c.agent_id == agent_id and c.start_time >= cutoff_time
        ]

        # Calculate metrics
        total_conversations = len(agent_conversations)
        completed_conversations = sum(
            1 for c in agent_conversations if c.status == ConversationStatus.COMPLETED
        )
        abandoned_conversations = sum(
            1 for c in agent_conversations if c.status == ConversationStatus.ABANDONED
        )

        # Calculate averages
        avg_duration = 0.0
        avg_turns = 0.0
        avg_satisfaction = 0.0

        if total_conversations > 0:
            # Duration (only for completed conversations)
            completed_with_duration = [
                c
                for c in agent_conversations
                if c.status == ConversationStatus.COMPLETED and c.duration is not None
            ]
            if completed_with_duration:
                avg_duration = sum(c.duration for c in completed_with_duration) / len(
                    completed_with_duration
                )

            # Turns
            avg_turns = sum(c.turns for c in agent_conversations) / total_conversations

            # Satisfaction
            conversations_with_satisfaction = [
                c for c in agent_conversations if c.satisfaction_score is not None
            ]
            if conversations_with_satisfaction:
                avg_satisfaction = sum(
                    c.satisfaction_score for c in conversations_with_satisfaction
                ) / len(conversations_with_satisfaction)

        # Collect all intents and responses
        all_intents = {}
        all_responses = {}

        for c in agent_conversations:
            if c.conversation_id in self._intents:
                for intent, count in self._intents[c.conversation_id].items():
                    if intent not in all_intents:
                        all_intents[intent] = 0
                    all_intents[intent] += count

            if c.conversation_id in self._responses:
                for response, count in self._responses[c.conversation_id].items():
                    if response not in all_responses:
                        all_responses[response] = 0
                    all_responses[response] += count

        # Create metrics data
        return {
            "agent_id": agent_id,
            "time_range_hours": time_range_hours,
            "total_conversations": total_conversations,
            "completed_conversations": completed_conversations,
            "abandoned_conversations": abandoned_conversations,
            "completion_rate": (
                completed_conversations / total_conversations
                if total_conversations > 0
                else 0.0
            ),
            "avg_duration": avg_duration,
            "avg_turns": avg_turns,
            "avg_satisfaction": avg_satisfaction,
            "top_intents": dict(
                sorted(all_intents.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "top_responses": dict(
                sorted(all_responses.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
        }

    async def export_dashboard_data(
        self,
        format: str = "json",
        destination: Optional[Union[str, Path]] = None,
        time_range_hours: int = 24,
    ) -> Union[str, Dict[str, Any]]:
        """
        Export dashboard data for conversations.

        Args:
            format: Output format (json, html, csv)
            destination: Optional file destination
            time_range_hours: Time range in hours

        Returns:
            Dashboard data in the specified format
        """
        if not self.enable_dashboard_data:
            return {"error": "Dashboard data not enabled"}

        # Calculate time cutoff
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)

        # Filter conversations by time
        recent_conversations = [
            c for c in self._conversations.values() if c.start_time >= cutoff_time
        ]

        # Group by agent
        agents = {}
        for c in recent_conversations:
            if c.agent_id not in agents:
                agents[c.agent_id] = []
            agents[c.agent_id].append(c)

        # Calculate agent metrics
        agent_metrics = {}
        for agent_id, conversations in agents.items():
            total = len(conversations)
            completed = sum(
                1 for c in conversations if c.status == ConversationStatus.COMPLETED
            )
            abandoned = sum(
                1 for c in conversations if c.status == ConversationStatus.ABANDONED
            )

            # Calculate averages
            avg_duration = 0.0
            avg_turns = 0.0
            avg_satisfaction = 0.0

            if total > 0:
                # Duration (only for completed conversations)
                completed_with_duration = [
                    c
                    for c in conversations
                    if c.status == ConversationStatus.COMPLETED
                    and c.duration is not None
                ]
                if completed_with_duration:
                    avg_duration = sum(
                        c.duration for c in completed_with_duration
                    ) / len(completed_with_duration)

                # Turns
                avg_turns = sum(c.turns for c in conversations) / total

                # Satisfaction
                conversations_with_satisfaction = [
                    c for c in conversations if c.satisfaction_score is not None
                ]
                if conversations_with_satisfaction:
                    avg_satisfaction = sum(
                        c.satisfaction_score for c in conversations_with_satisfaction
                    ) / len(conversations_with_satisfaction)

            agent_metrics[agent_id] = {
                "total": total,
                "completed": completed,
                "abandoned": abandoned,
                "completion_rate": completed / total if total > 0 else 0.0,
                "avg_duration": avg_duration,
                "avg_turns": avg_turns,
                "avg_satisfaction": avg_satisfaction,
            }

        # Create dashboard data
        dashboard_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "time_range_hours": time_range_hours,
            "total_conversations": len(recent_conversations),
            "agent_metrics": agent_metrics,
            "conversation_status": {
                "completed": sum(
                    1
                    for c in recent_conversations
                    if c.status == ConversationStatus.COMPLETED
                ),
                "active": sum(
                    1
                    for c in recent_conversations
                    if c.status == ConversationStatus.ACTIVE
                ),
                "abandoned": sum(
                    1
                    for c in recent_conversations
                    if c.status == ConversationStatus.ABANDONED
                ),
                "error": sum(
                    1
                    for c in recent_conversations
                    if c.status == ConversationStatus.ERROR
                ),
            },
        }

        # Format output
        if format == "json":
            output = json.dumps(dashboard_data, indent=2)
        elif format == "html":
            # Simple HTML dashboard
            output = self._generate_html_dashboard(dashboard_data)
        elif format == "csv":
            # CSV format (just the agent metrics)
            output = "agent_id,total,completed,abandoned,completion_rate,avg_duration,avg_turns,avg_satisfaction\n"
            for agent_id, metrics in agent_metrics.items():
                output += f"{agent_id},{metrics['total']},{metrics['completed']},{metrics['abandoned']},{metrics['completion_rate']:.2f},{metrics['avg_duration']:.2f},{metrics['avg_turns']:.2f},{metrics['avg_satisfaction']:.2f}\n"
        else:
            output = json.dumps(dashboard_data, indent=2)

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
                # Clean up old conversations
                await self._cleanup_old_data()

                # Store data to disk
                if not self.mobile_optimized:
                    await self._store_data()
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")

            # Wait for next cleanup interval
            await asyncio.sleep(3600)  # 1 hour

    async def _cleanup_old_data(self) -> None:
        """Clean up old conversations."""
        # Calculate cutoff time (30 days)
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=30)

        # Find old conversations
        old_conversation_ids = [
            c_id
            for c_id, c in self._conversations.items()
            if c.end_time and c.end_time < cutoff_time
        ]

        # Remove old conversations
        for c_id in old_conversation_ids:
            del self._conversations[c_id]

            if c_id in self._intents:
                del self._intents[c_id]

            if c_id in self._responses:
                del self._responses[c_id]

        if old_conversation_ids:
            self.logger.info(
                f"Cleaned up {len(old_conversation_ids)} old conversations"
            )

    async def _store_conversation(self, metrics: ConversationMetrics) -> None:
        """Store a conversation to disk."""
        try:
            # Create file path
            file_path = self.storage_path / f"{metrics.conversation_id}.json"
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Create conversation data
            data = metrics.to_dict()
            data["intents"] = self._intents.get(metrics.conversation_id, {})
            data["responses"] = self._responses.get(metrics.conversation_id, {})

            # Write to file
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error storing conversation: {e}")

    async def _store_data(self) -> None:
        """Store all data to disk."""
        try:
            # Store active conversations index
            index_path = self.storage_path / "conversations_index.json"
            self.storage_path.mkdir(parents=True, exist_ok=True)
            with open(index_path, "w") as f:
                index_data = {
                    c_id: {
                        "user_id": c.user_id,
                        "agent_id": c.agent_id,
                        "start_time": c.start_time.isoformat(),
                        "status": c.status.name,
                    }
                    for c_id, c in self._conversations.items()
                }
                json.dump(index_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error storing data: {e}")

    def _generate_html_dashboard(self, data: Dict[str, Any]) -> str:
        """Generate HTML dashboard for conversation metrics."""
        # Simple HTML dashboard
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Conversation Metrics Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .card {{ border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 20px; }}
        .card h2 {{ margin-top: 0; color: #555; }}
        .stat {{ display: inline-block; margin-right: 20px; margin-bottom: 10px; }}
        .stat .value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .stat .label {{ font-size: 12px; color: #777; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Conversation Metrics Dashboard</h1>
    <p>Generated at: {data['generated_at']} (Last {data['time_range_hours']} hours)</p>

    <div class="card">
        <h2>Overview</h2>
        <div class="stat">
            <div class="value">{data['total_conversations']}</div>
            <div class="label">Total Conversations</div>
        </div>
        <div class="stat">
            <div class="value">{data['conversation_status']['completed']}</div>
            <div class="label">Completed</div>
        </div>
        <div class="stat">
            <div class="value">{data['conversation_status']['active']}</div>
            <div class="label">Active</div>
        </div>
        <div class="stat">
            <div class="value">{data['conversation_status']['abandoned']}</div>
            <div class="label">Abandoned</div>
        </div>
        <div class="stat">
            <div class="value">{data['conversation_status']['error']}</div>
            <div class="label">Error</div>
        </div>
    </div>

    <div class="card">
        <h2>UnifiedAgent Performance</h2>
        <table>
            <tr>
                <th>UnifiedAgent</th>
                <th>Total</th>
                <th>Completed</th>
                <th>Abandoned</th>
                <th>Completion Rate</th>
                <th>Avg Duration (s)</th>
                <th>Avg Turns</th>
                <th>Avg Satisfaction</th>
            </tr>
"""

        # Add agent rows
        for agent_id, metrics in data["agent_metrics"].items():
            html += f"""            <tr>
                <td>{agent_id}</td>
                <td>{metrics['total']}</td>
                <td>{metrics['completed']}</td>
                <td>{metrics['abandoned']}</td>
                <td>{metrics['completion_rate']:.1%}</td>
                <td>{metrics['avg_duration']:.1f}</td>
                <td>{metrics['avg_turns']:.1f}</td>
                <td>{metrics['avg_satisfaction']:.2f}</td>
            </tr>
"""

        html += """        </table>
    </div>
</body>
</html>
"""

        return html

    async def close(self) -> None:
        """Close the collector and clean up resources."""
        self._is_running = False
        if hasattr(self, "_cleanup_task") and self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


# Singleton instance
_conversation_metrics_collector_instance = None


def get_conversation_metrics_collector() -> ConversationMetricsCollector:
    """
    Get the conversation metrics collector instance.

    Returns:
        ConversationMetricsCollector instance
    """
    global _conversation_metrics_collector_instance
    if _conversation_metrics_collector_instance is None:
        _conversation_metrics_collector_instance = ConversationMetricsCollector()
    return _conversation_metrics_collector_instance


async def start_conversation(
    conversation_id: str,
    user_id: str,
    agent_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> ConversationMetrics:
    """
    Start tracking a new conversation.

    Args:
        conversation_id: Unique conversation ID
        user_id: UnifiedUser ID
        agent_id: UnifiedAgent ID
        metadata: Optional metadata

    Returns:
        ConversationMetrics instance
    """
    return await get_conversation_metrics_collector().start_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        agent_id=agent_id,
        metadata=metadata,
    )


async def end_conversation(
    conversation_id: str,
    status: ConversationStatus = ConversationStatus.COMPLETED,
    satisfaction_score: Optional[float] = None,
    success_rate: Optional[float] = None,
    completion_rate: Optional[float] = None,
) -> Optional[ConversationMetrics]:
    """
    End a conversation and finalize metrics.

    Args:
        conversation_id: Conversation ID
        status: Final conversation status
        satisfaction_score: Optional satisfaction score (0.0 to 1.0)
        success_rate: Optional success rate (0.0 to 1.0)
        completion_rate: Optional completion rate (0.0 to 1.0)

    Returns:
        Updated ConversationMetrics or None if not found
    """
    return await get_conversation_metrics_collector().end_conversation(
        conversation_id=conversation_id,
        status=status,
        satisfaction_score=satisfaction_score,
        success_rate=success_rate,
        completion_rate=completion_rate,
    )


async def record_user_turn(
    conversation_id: str,
    intent: Optional[str] = None,
    sentiment_score: Optional[float] = None,
    content_length: Optional[int] = None,
) -> Optional[ConversationMetrics]:
    """
    Record a user turn in a conversation.

    Args:
        conversation_id: Conversation ID
        intent: Optional user intent
        sentiment_score: Optional sentiment score (-1.0 to 1.0)
        content_length: Optional content length in characters

    Returns:
        Updated ConversationMetrics or None if not found
    """
    return await get_conversation_metrics_collector().record_user_turn(
        conversation_id=conversation_id,
        intent=intent,
        sentiment_score=sentiment_score,
        content_length=content_length,
    )


async def record_agent_turn(
    conversation_id: str,
    response_type: Optional[str] = None,
    content_length: Optional[int] = None,
    processing_time: Optional[float] = None,
) -> Optional[ConversationMetrics]:
    """
    Record an agent turn in a conversation.

    Args:
        conversation_id: Conversation ID
        response_type: Optional response type
        content_length: Optional content length in characters
        processing_time: Optional processing time in seconds

    Returns:
        Updated ConversationMetrics or None if not found
    """
    return await get_conversation_metrics_collector().record_agent_turn(
        conversation_id=conversation_id,
        response_type=response_type,
        content_length=content_length,
        processing_time=processing_time,
    )
