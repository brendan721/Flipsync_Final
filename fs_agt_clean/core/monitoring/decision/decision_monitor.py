"""
Decision intelligence monitor for FlipSync.

This module provides monitoring for decision intelligence, including:
- Decision quality metrics
- Learning event logging
- Adaptation monitoring
- Visualization tools for decision patterns

It supports FlipSync's vision of intelligent decision making by providing
visibility into decision quality and adaptation.
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
    DecisionMetrics,
    DecisionOutcome,
)


class DecisionIntelligenceMonitor:
    """
    Monitors decision intelligence metrics and learning events.

    This class provides monitoring for decision intelligence, including:
    - Decision quality metrics
    - Learning event logging
    - Adaptation monitoring
    - Visualization tools for decision patterns

    It supports FlipSync's vision of intelligent decision making by providing
    visibility into decision quality and adaptation.
    """

    _instance = None
    _lock = threading.RLock()
    _initialized = False
    _decisions: Dict[str, DecisionMetrics] = {}
    _learning_events: List[Dict[str, Any]] = []

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DecisionIntelligenceMonitor, cls).__new__(cls)
            return cls._instance

    def __init__(
        self,
        storage_path: Optional[Union[str, Path]] = None,
        enable_visualization: bool = True,
        mobile_optimized: bool = False,
    ):
        """
        Initialize the decision intelligence monitor.

        Args:
            storage_path: Path to store decision data
            enable_visualization: Whether to enable visualization
            mobile_optimized: Whether to optimize for mobile environments
        """
        with self._lock:
            if self._initialized:
                return

            # Set up logger
            self.logger = get_logger("decision_intelligence")

            # Set up storage
            self.storage_path = (
                Path(storage_path)
                if storage_path
                else Path("logs/decision_intelligence")
            )
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Store configuration
            self.enable_visualization = enable_visualization
            self.mobile_optimized = mobile_optimized

            # Start background tasks
            self._is_running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            self._initialized = True
            self.logger.info("Decision intelligence monitor initialized")

    async def record_decision(
        self,
        decision_id: str,
        agent_id: str,
        decision_type: str,
        context: Dict[str, Any],
        options: List[Dict[str, Any]],
        selected_option: Dict[str, Any],
        confidence: float,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DecisionMetrics:
        """
        Record a decision made by an agent.

        Args:
            decision_id: Unique decision ID
            agent_id: UnifiedAgent ID
            decision_type: Type of decision
            context: Decision context
            options: Available options
            selected_option: Selected option
            confidence: Confidence level (0.0 to 1.0)
            reasoning: Optional reasoning for the decision
            metadata: Optional metadata

        Returns:
            DecisionMetrics instance
        """
        # Create decision metrics
        timestamp = datetime.now(timezone.utc)
        metrics = DecisionMetrics(
            decision_id=decision_id,
            agent_id=agent_id,
            decision_type=decision_type,
            timestamp=timestamp,
            context=context,
            options=options,
            selected_option=selected_option,
            confidence=max(0.0, min(1.0, confidence)),
            reasoning=reasoning,
            outcome=None,  # Will be set later
            execution_time=None,  # Will be set later
            metadata=metadata or {},
        )

        # Store decision
        self._decisions[decision_id] = metrics

        # Log decision
        self.logger.info(
            f"Decision recorded: {decision_id} (agent: {agent_id}, type: {decision_type})",
            extra={
                "decision_id": decision_id,
                "agent_id": agent_id,
                "decision_type": decision_type,
                "confidence": confidence,
                "num_options": len(options),
            },
        )

        # Record metric
        await record_metric(
            name="decisions_made",
            value=1.0,
            metric_type=MetricType.COUNTER,
            category=MetricCategory.DECISION,
            labels={
                "agent_id": agent_id,
                "decision_type": decision_type,
            },
        )

        await record_metric(
            name="decision_confidence",
            value=metrics.confidence,
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.DECISION,
            labels={
                "agent_id": agent_id,
                "decision_type": decision_type,
            },
        )

        # Store to disk if not mobile optimized
        if not self.mobile_optimized:
            await self._store_decision(metrics)

        return metrics

    async def record_decision_outcome(
        self,
        decision_id: str,
        outcome: DecisionOutcome,
        execution_time: Optional[float] = None,
        feedback: Optional[Dict[str, Any]] = None,
    ) -> Optional[DecisionMetrics]:
        """
        Record the outcome of a decision.

        Args:
            decision_id: Decision ID
            outcome: Decision outcome
            execution_time: Optional execution time in seconds
            feedback: Optional feedback data

        Returns:
            Updated DecisionMetrics or None if not found
        """
        if decision_id not in self._decisions:
            self.logger.warning(f"Decision {decision_id} not found")
            return None

        # Get decision
        metrics = self._decisions[decision_id]

        # Update metrics
        metrics.outcome = outcome
        metrics.execution_time = execution_time

        if feedback:
            if "feedback" not in metrics.metadata:
                metrics.metadata["feedback"] = []
            metrics.metadata["feedback"].append(feedback)

        # Log outcome
        self.logger.info(
            f"Decision outcome recorded: {decision_id} (outcome: {outcome.name})",
            extra={
                "decision_id": decision_id,
                "agent_id": metrics.agent_id,
                "decision_type": metrics.decision_type,
                "outcome": outcome.name,
                "execution_time": execution_time,
            },
        )

        # Record metrics
        await record_metric(
            name="decision_outcomes",
            value=1.0,
            metric_type=MetricType.COUNTER,
            category=MetricCategory.DECISION,
            labels={
                "agent_id": metrics.agent_id,
                "decision_type": metrics.decision_type,
                "outcome": outcome.name,
            },
        )

        if execution_time is not None:
            await record_metric(
                name="decision_execution_time",
                value=execution_time,
                metric_type=MetricType.HISTOGRAM,
                category=MetricCategory.DECISION,
                labels={
                    "agent_id": metrics.agent_id,
                    "decision_type": metrics.decision_type,
                    "outcome": outcome.name,
                },
            )

        # Store to disk if not mobile optimized
        if not self.mobile_optimized:
            await self._store_decision(metrics)

        return metrics

    async def record_learning_event(
        self,
        agent_id: str,
        event_type: str,
        data: Dict[str, Any],
        related_decision_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record a learning event.

        Args:
            agent_id: UnifiedAgent ID
            event_type: Type of learning event
            data: Learning event data
            related_decision_id: Optional related decision ID
            metadata: Optional metadata

        Returns:
            Learning event data
        """
        # Create learning event
        timestamp = datetime.now(timezone.utc)
        event_id = f"{agent_id}_{event_type}_{int(timestamp.timestamp())}_{len(self._learning_events)}"

        event = {
            "event_id": event_id,
            "agent_id": agent_id,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "data": data,
            "related_decision_id": related_decision_id,
            "metadata": metadata or {},
        }

        # Store event
        self._learning_events.append(event)

        # Log event
        self.logger.info(
            f"Learning event recorded: {event_id} (agent: {agent_id}, type: {event_type})",
            extra={
                "event_id": event_id,
                "agent_id": agent_id,
                "event_type": event_type,
                "related_decision_id": related_decision_id,
            },
        )

        # Record metric
        await record_metric(
            name="learning_events",
            value=1.0,
            metric_type=MetricType.COUNTER,
            category=MetricCategory.DECISION,
            labels={
                "agent_id": agent_id,
                "event_type": event_type,
            },
        )

        # Store to disk if not mobile optimized
        if not self.mobile_optimized:
            await self._store_learning_event(event)

        return event

    async def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a decision by ID.

        Args:
            decision_id: Decision ID

        Returns:
            Decision data or None if not found
        """
        if decision_id not in self._decisions:
            return None

        return self._decisions[decision_id].to_dict()

    async def get_agent_decisions(
        self, agent_id: str, decision_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get decisions for an agent.

        Args:
            agent_id: UnifiedAgent ID
            decision_type: Optional decision type filter
            limit: Maximum number of decisions to return

        Returns:
            List of decision data
        """
        # Filter decisions
        decisions = [
            d
            for d in self._decisions.values()
            if d.agent_id == agent_id
            and (decision_type is None or d.decision_type == decision_type)
        ]

        # Sort by timestamp (newest first)
        decisions.sort(key=lambda d: d.timestamp, reverse=True)

        # Limit results
        decisions = decisions[:limit]

        # Convert to dictionaries
        return [d.to_dict() for d in decisions]

    async def get_learning_events(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get learning events.

        Args:
            agent_id: Optional agent ID filter
            event_type: Optional event type filter
            limit: Maximum number of events to return

        Returns:
            List of learning event data
        """
        # Filter events
        events = self._learning_events.copy()

        if agent_id is not None:
            events = [e for e in events if e["agent_id"] == agent_id]

        if event_type is not None:
            events = [e for e in events if e["event_type"] == event_type]

        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e["timestamp"], reverse=True)

        # Limit results
        return events[:limit]

    async def get_decision_metrics(
        self,
        agent_id: Optional[str] = None,
        decision_type: Optional[str] = None,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get aggregated decision metrics.

        Args:
            agent_id: Optional agent ID filter
            decision_type: Optional decision type filter
            time_range_hours: Time range in hours

        Returns:
            Aggregated metrics
        """
        # Calculate time cutoff
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)

        # Filter decisions
        decisions = list(self._decisions.values())

        if agent_id is not None:
            decisions = [d for d in decisions if d.agent_id == agent_id]

        if decision_type is not None:
            decisions = [d for d in decisions if d.decision_type == decision_type]

        # Filter by time
        decisions = [d for d in decisions if d.timestamp >= cutoff_time]

        # Calculate metrics
        total_decisions = len(decisions)
        decisions_with_outcome = [d for d in decisions if d.outcome is not None]

        # Outcome counts
        outcome_counts = {}
        for d in decisions_with_outcome:
            outcome_name = d.outcome.name
            if outcome_name not in outcome_counts:
                outcome_counts[outcome_name] = 0
            outcome_counts[outcome_name] += 1

        # Success rate
        success_rate = 0.0
        if decisions_with_outcome:
            successful = sum(
                1
                for d in decisions_with_outcome
                if d.outcome == DecisionOutcome.SUCCESS
            )
            success_rate = successful / len(decisions_with_outcome)

        # Average confidence
        avg_confidence = 0.0
        if decisions:
            avg_confidence = sum(d.confidence for d in decisions) / len(decisions)

        # Average execution time
        avg_execution_time = 0.0
        decisions_with_execution_time = [
            d for d in decisions if d.execution_time is not None
        ]
        if decisions_with_execution_time:
            avg_execution_time = sum(
                d.execution_time for d in decisions_with_execution_time
            ) / len(decisions_with_execution_time)

        # Decision types
        decision_types = {}
        for d in decisions:
            if d.decision_type not in decision_types:
                decision_types[d.decision_type] = 0
            decision_types[d.decision_type] += 1

        # Create metrics data
        return {
            "time_range_hours": time_range_hours,
            "total_decisions": total_decisions,
            "decisions_with_outcome": len(decisions_with_outcome),
            "outcome_counts": outcome_counts,
            "success_rate": success_rate,
            "avg_confidence": avg_confidence,
            "avg_execution_time": avg_execution_time,
            "decision_types": decision_types,
            "agent_id": agent_id,
            "decision_type": decision_type,
        }

    async def export_visualization_data(
        self,
        format: str = "json",
        destination: Optional[Union[str, Path]] = None,
        time_range_hours: int = 24,
        agent_id: Optional[str] = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Export visualization data for decisions.

        Args:
            format: Output format (json, html, csv)
            destination: Optional file destination
            time_range_hours: Time range in hours
            agent_id: Optional agent ID filter

        Returns:
            Visualization data in the specified format
        """
        if not self.enable_visualization:
            return {"error": "Visualization not enabled"}

        # Get decision metrics
        metrics = await self.get_decision_metrics(
            agent_id=agent_id,
            time_range_hours=time_range_hours,
        )

        # Get decisions
        decisions = list(self._decisions.values())

        if agent_id is not None:
            decisions = [d for d in decisions if d.agent_id == agent_id]

        # Calculate time cutoff
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
        decisions = [d for d in decisions if d.timestamp >= cutoff_time]

        # Sort by timestamp
        decisions.sort(key=lambda d: d.timestamp)

        # Create time series data
        time_series = []
        for d in decisions:
            time_series.append(
                {
                    "timestamp": d.timestamp.isoformat(),
                    "decision_id": d.decision_id,
                    "agent_id": d.agent_id,
                    "decision_type": d.decision_type,
                    "confidence": d.confidence,
                    "outcome": d.outcome.name if d.outcome else None,
                }
            )

        # Create visualization data
        visualization_data = {
            "metrics": metrics,
            "time_series": time_series,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Format output
        if format == "json":
            output = json.dumps(visualization_data, indent=2)
        elif format == "html":
            # Simple HTML visualization
            output = self._generate_html_visualization(visualization_data)
        elif format == "csv":
            # CSV format (just the time series)
            output = "timestamp,decision_id,agent_id,decision_type,confidence,outcome\n"
            for entry in time_series:
                output += f"{entry['timestamp']},{entry['decision_id']},{entry['agent_id']},{entry['decision_type']},{entry['confidence']},{entry['outcome'] or ''}\n"
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
                # Clean up old data
                await self._cleanup_old_data()

                # Store data to disk
                if not self.mobile_optimized:
                    await self._store_data()
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")

            # Wait for next cleanup interval
            await asyncio.sleep(3600)  # 1 hour

    async def _cleanup_old_data(self) -> None:
        """Clean up old decisions and learning events."""
        # Calculate cutoff time (30 days)
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=30)

        # Clean up old decisions
        old_decision_ids = [
            d_id for d_id, d in self._decisions.items() if d.timestamp < cutoff_time
        ]

        for d_id in old_decision_ids:
            del self._decisions[d_id]

        # Clean up old learning events
        self._learning_events = [
            e
            for e in self._learning_events
            if datetime.fromisoformat(e["timestamp"]) >= cutoff_time
        ]

        if old_decision_ids:
            self.logger.info(f"Cleaned up {len(old_decision_ids)} old decisions")

    async def _store_decision(self, metrics: DecisionMetrics) -> None:
        """Store a decision to disk."""
        try:
            # Create file path
            file_path = self.storage_path / f"decision_{metrics.decision_id}.json"

            # Write to file
            with open(file_path, "w") as f:
                json.dump(metrics.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error storing decision: {e}")

    async def _store_learning_event(self, event: Dict[str, Any]) -> None:
        """Store a learning event to disk."""
        try:
            # Create file path
            file_path = self.storage_path / f"learning_event_{event['event_id']}.json"

            # Write to file
            with open(file_path, "w") as f:
                json.dump(event, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error storing learning event: {e}")

    async def _store_data(self) -> None:
        """Store all data to disk."""
        try:
            # Store decisions index
            decisions_path = self.storage_path / "decisions_index.json"
            with open(decisions_path, "w") as f:
                index_data = {
                    d_id: {
                        "agent_id": d.agent_id,
                        "decision_type": d.decision_type,
                        "timestamp": d.timestamp.isoformat(),
                        "outcome": d.outcome.name if d.outcome else None,
                    }
                    for d_id, d in self._decisions.items()
                }
                json.dump(index_data, f, indent=2)

            # Store learning events index
            events_path = self.storage_path / "learning_events_index.json"
            with open(events_path, "w") as f:
                json.dump(
                    [
                        {
                            "event_id": e["event_id"],
                            "agent_id": e["agent_id"],
                            "event_type": e["event_type"],
                            "timestamp": e["timestamp"],
                            "related_decision_id": e["related_decision_id"],
                        }
                        for e in self._learning_events
                    ],
                    f,
                    indent=2,
                )
        except Exception as e:
            self.logger.error(f"Error storing data: {e}")

    def _generate_html_visualization(self, data: Dict[str, Any]) -> str:
        """Generate HTML visualization for decision metrics."""
        metrics = data["metrics"]
        time_series = data["time_series"]

        # Simple HTML visualization
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Decision Intelligence Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .card {{ border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 20px; }}
        .card h2 {{ margin-top: 0; color: #555; }}
        .stat {{ display: inline-block; margin-right: 20px; margin-bottom: 10px; }}
        .stat .value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .stat .label {{ font-size: 12px; color: #777; }}
        .chart-container {{ height: 300px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>Decision Intelligence Visualization</h1>
    <p>Generated at: {data['generated_at']} (Last {metrics['time_range_hours']} hours)</p>

    <div class="card">
        <h2>Overview</h2>
        <div class="stat">
            <div class="value">{metrics['total_decisions']}</div>
            <div class="label">Total Decisions</div>
        </div>
        <div class="stat">
            <div class="value">{metrics['decisions_with_outcome']}</div>
            <div class="label">With Outcome</div>
        </div>
        <div class="stat">
            <div class="value">{metrics['success_rate']:.1%}</div>
            <div class="label">Success Rate</div>
        </div>
        <div class="stat">
            <div class="value">{metrics['avg_confidence']:.2f}</div>
            <div class="label">Avg Confidence</div>
        </div>
        <div class="stat">
            <div class="value">{metrics['avg_execution_time']:.2f}s</div>
            <div class="label">Avg Execution Time</div>
        </div>
    </div>

    <div class="card">
        <h2>Outcomes</h2>
        <div class="chart-container">
            <canvas id="outcomesChart"></canvas>
        </div>
    </div>

    <div class="card">
        <h2>Decision Types</h2>
        <div class="chart-container">
            <canvas id="typesChart"></canvas>
        </div>
    </div>

    <div class="card">
        <h2>Confidence Over Time</h2>
        <div class="chart-container">
            <canvas id="confidenceChart"></canvas>
        </div>
    </div>

    <script>
        // Outcomes chart
        const outcomesCtx = document.getElementById('outcomesChart').getContext('2d');
        new Chart(outcomesCtx, {{
            type: 'pie',
            data: {{
                labels: {json.dumps(list(metrics['outcome_counts'].keys()))},
                datasets: [{{
                    data: {json.dumps(list(metrics['outcome_counts'].values()))},
                    backgroundColor: ['#4CAF50', '#F44336', '#2196F3', '#FFC107', '#9C27B0'],
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
            }}
        }});

        // Decision types chart
        const typesCtx = document.getElementById('typesChart').getContext('2d');
        new Chart(typesCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(list(metrics['decision_types'].keys()))},
                datasets: [{{
                    label: 'Count',
                    data: {json.dumps(list(metrics['decision_types'].values()))},
                    backgroundColor: '#2196F3',
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Confidence over time chart
        const confidenceCtx = document.getElementById('confidenceChart').getContext('2d');
        new Chart(confidenceCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps([entry['timestamp'] for entry in time_series])},
                datasets: [{{
                    label: 'Confidence',
                    data: {json.dumps([entry['confidence'] for entry in time_series])},
                    borderColor: '#4CAF50',
                    tension: 0.1,
                    fill: false
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 1.0
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

        return html

    async def close(self) -> None:
        """Close the monitor and clean up resources."""
        self._is_running = False
        if hasattr(self, "_cleanup_task") and self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


# Singleton instance
_decision_intelligence_monitor_instance = None


def get_decision_intelligence_monitor() -> DecisionIntelligenceMonitor:
    """
    Get the decision intelligence monitor instance.

    Returns:
        DecisionIntelligenceMonitor instance
    """
    global _decision_intelligence_monitor_instance
    if _decision_intelligence_monitor_instance is None:
        _decision_intelligence_monitor_instance = DecisionIntelligenceMonitor()
    return _decision_intelligence_monitor_instance


async def record_decision(
    decision_id: str,
    agent_id: str,
    decision_type: str,
    context: Dict[str, Any],
    options: List[Dict[str, Any]],
    selected_option: Dict[str, Any],
    confidence: float,
    reasoning: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> DecisionMetrics:
    """
    Record a decision made by an agent.

    Args:
        decision_id: Unique decision ID
        agent_id: UnifiedAgent ID
        decision_type: Type of decision
        context: Decision context
        options: Available options
        selected_option: Selected option
        confidence: Confidence level (0.0 to 1.0)
        reasoning: Optional reasoning for the decision
        metadata: Optional metadata

    Returns:
        DecisionMetrics instance
    """
    return await get_decision_intelligence_monitor().record_decision(
        decision_id=decision_id,
        agent_id=agent_id,
        decision_type=decision_type,
        context=context,
        options=options,
        selected_option=selected_option,
        confidence=confidence,
        reasoning=reasoning,
        metadata=metadata,
    )


async def record_decision_outcome(
    decision_id: str,
    outcome: DecisionOutcome,
    execution_time: Optional[float] = None,
    feedback: Optional[Dict[str, Any]] = None,
) -> Optional[DecisionMetrics]:
    """
    Record the outcome of a decision.

    Args:
        decision_id: Decision ID
        outcome: Decision outcome
        execution_time: Optional execution time in seconds
        feedback: Optional feedback data

    Returns:
        Updated DecisionMetrics or None if not found
    """
    return await get_decision_intelligence_monitor().record_decision_outcome(
        decision_id=decision_id,
        outcome=outcome,
        execution_time=execution_time,
        feedback=feedback,
    )


async def record_learning_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    related_decision_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Record a learning event.

    Args:
        agent_id: UnifiedAgent ID
        event_type: Type of learning event
        data: Learning event data
        related_decision_id: Optional related decision ID
        metadata: Optional metadata

    Returns:
        Learning event data
    """
    return await get_decision_intelligence_monitor().record_learning_event(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        related_decision_id=related_decision_id,
        metadata=metadata,
    )
