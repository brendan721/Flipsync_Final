"""
Learning Metrics Collector for FlipSync Agentic System
Phase 2.3: Performance Optimization and Measurement

This module collects, analyzes, and reports measurable learning improvements
and effectiveness metrics for the algorithmic learning system.
"""

import logging
import time
import json
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
import statistics

from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


@dataclass
class LearningMetric:
    """Individual learning metric measurement."""

    metric_id: str
    agent_id: str
    metric_type: str
    metric_value: float
    baseline_value: Optional[float]
    improvement_percentage: Optional[float]
    confidence_score: float
    measurement_context: Dict[str, Any]
    timestamp: datetime


@dataclass
class LearningEffectivenessReport:
    """Comprehensive learning effectiveness report."""

    report_id: str
    agent_id: str
    time_period: str
    total_decisions: int
    learning_improvements: List[LearningMetric]
    performance_trends: Dict[str, List[float]]
    algorithm_effectiveness: Dict[str, float]
    cross_agent_learning_impact: float
    overall_learning_score: float
    generated_at: datetime


class LearningMetricsCollector:
    """
    Collects and analyzes measurable learning improvements.

    Features:
    - Decision accuracy improvement tracking
    - Learning convergence speed measurement
    - Cross-agent knowledge utilization metrics
    - Performance improvement rate calculation
    - Real-time learning effectiveness monitoring
    """

    def __init__(self, database: Database, agent_id: str):
        """Initialize the learning metrics collector.

        Args:
            database: Database instance for metrics storage
            agent_id: ID of the agent being monitored
        """
        self.database = database
        self.agent_id = agent_id

        # Metrics storage
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.baseline_metrics: Dict[str, float] = {}
        self.learning_reports: List[LearningEffectivenessReport] = []

        # Performance tracking
        self.decision_accuracy_history: deque = deque(maxlen=500)
        self.learning_convergence_times: deque = deque(maxlen=100)
        self.algorithm_performance: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=200)
        )

        # Cross-agent learning tracking
        self.cross_agent_insights_applied: List[Dict[str, Any]] = []
        self.knowledge_sharing_effectiveness: Dict[str, float] = {}

        # Measurement configuration
        self.measurement_interval = 60  # seconds
        self.baseline_period_days = 7
        self.min_samples_for_trend = 10

    async def initialize(self) -> bool:
        """Initialize the metrics collector."""
        try:
            # Create metrics tables
            await self._create_metrics_tables()

            # Load historical metrics
            await self._load_historical_metrics()

            # Calculate baseline metrics
            await self._calculate_baseline_metrics()

            logger.info(f"✅ LearningMetricsCollector initialized for {self.agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize LearningMetricsCollector: {e}")
            return False

    async def record_decision_outcome(
        self,
        decision_id: str,
        success: bool,
        execution_time: float,
        quality_score: float,
        context: Dict[str, Any],
    ):
        """Record a decision outcome for learning metrics."""
        try:
            # Record decision accuracy with unique ID
            unique_id = str(uuid.uuid4())[:8]
            accuracy_metric = LearningMetric(
                metric_id=f"accuracy_{decision_id}_{unique_id}",
                agent_id=self.agent_id,
                metric_type="decision_accuracy",
                metric_value=1.0 if success else 0.0,
                baseline_value=self.baseline_metrics.get("decision_accuracy"),
                improvement_percentage=None,
                confidence_score=quality_score,
                measurement_context=context,
                timestamp=datetime.now(timezone.utc),
            )

            # Record execution time performance with unique ID
            time_unique_id = str(uuid.uuid4())[:8]
            time_metric = LearningMetric(
                metric_id=f"execution_time_{decision_id}_{time_unique_id}",
                agent_id=self.agent_id,
                metric_type="execution_time",
                metric_value=execution_time,
                baseline_value=self.baseline_metrics.get("execution_time"),
                improvement_percentage=None,
                confidence_score=1.0,
                measurement_context=context,
                timestamp=datetime.now(timezone.utc),
            )

            # Record quality score with unique ID
            quality_unique_id = str(uuid.uuid4())[:8]
            quality_metric = LearningMetric(
                metric_id=f"quality_{decision_id}_{quality_unique_id}",
                agent_id=self.agent_id,
                metric_type="decision_quality",
                metric_value=quality_score,
                baseline_value=self.baseline_metrics.get("decision_quality"),
                improvement_percentage=None,
                confidence_score=quality_score,
                measurement_context=context,
                timestamp=datetime.now(timezone.utc),
            )

            # Store all metrics in a single batch operation
            await self._batch_store_metrics(
                [accuracy_metric, time_metric, quality_metric]
            )

            # Update history tracking
            self.decision_accuracy_history.append(accuracy_metric.metric_value)

            # Calculate improvements
            await self._calculate_metric_improvements()

        except Exception as e:
            logger.error(f"Error recording decision outcome: {e}")

    async def record_learning_convergence(
        self,
        algorithm_type: str,
        convergence_time: float,
        iterations: int,
        final_performance: float,
        context: Dict[str, Any],
    ):
        """Record learning algorithm convergence metrics."""
        try:
            convergence_unique_id = str(uuid.uuid4())[:8]
            convergence_metric = LearningMetric(
                metric_id=f"convergence_{algorithm_type}_{convergence_unique_id}",
                agent_id=self.agent_id,
                metric_type="learning_convergence",
                metric_value=convergence_time,
                baseline_value=self.baseline_metrics.get("learning_convergence"),
                improvement_percentage=None,
                confidence_score=final_performance,
                measurement_context={
                    "algorithm_type": algorithm_type,
                    "iterations": iterations,
                    "final_performance": final_performance,
                    **context,
                },
                timestamp=datetime.now(timezone.utc),
            )

            await self._store_metric(convergence_metric)
            self.learning_convergence_times.append(convergence_time)
            self.algorithm_performance[algorithm_type].append(final_performance)

        except Exception as e:
            logger.error(f"Error recording learning convergence: {e}")

    async def record_cross_agent_learning(
        self,
        insight_id: str,
        source_agent_id: str,
        application_success: bool,
        performance_improvement: float,
        context: Dict[str, Any],
    ):
        """Record cross-agent learning effectiveness."""
        try:
            cross_learning_record = {
                "insight_id": insight_id,
                "source_agent_id": source_agent_id,
                "application_success": application_success,
                "performance_improvement": performance_improvement,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": context,
            }

            self.cross_agent_insights_applied.append(cross_learning_record)

            # Update knowledge sharing effectiveness
            if source_agent_id not in self.knowledge_sharing_effectiveness:
                self.knowledge_sharing_effectiveness[source_agent_id] = 0.5

            # Update effectiveness based on success
            current_effectiveness = self.knowledge_sharing_effectiveness[
                source_agent_id
            ]
            success_score = 1.0 if application_success else 0.0
            self.knowledge_sharing_effectiveness[source_agent_id] = (
                current_effectiveness * 0.8 + success_score * 0.2
            )

            # Record as metric with unique ID
            cross_unique_id = str(uuid.uuid4())[:8]
            cross_learning_metric = LearningMetric(
                metric_id=f"cross_learning_{insight_id}_{cross_unique_id}",
                agent_id=self.agent_id,
                metric_type="cross_agent_learning",
                metric_value=performance_improvement,
                baseline_value=0.0,
                improvement_percentage=performance_improvement * 100,
                confidence_score=0.8,
                measurement_context=context,
                timestamp=datetime.now(timezone.utc),
            )

            await self._store_metric(cross_learning_metric)

        except Exception as e:
            logger.error(f"Error recording cross-agent learning: {e}")

    async def record_algorithm_performance(
        self,
        algorithm_type: str,
        performance_score: float,
        optimization_time: float,
        context: Dict[str, Any],
    ):
        """Record algorithm-specific performance metrics."""
        try:
            algorithm_unique_id = str(uuid.uuid4())[:8]
            algorithm_metric = LearningMetric(
                metric_id=f"algorithm_{algorithm_type}_{algorithm_unique_id}",
                agent_id=self.agent_id,
                metric_type="algorithm_performance",
                metric_value=performance_score,
                baseline_value=self.baseline_metrics.get(f"algorithm_{algorithm_type}"),
                improvement_percentage=None,
                confidence_score=1.0,
                measurement_context={
                    "algorithm_type": algorithm_type,
                    "optimization_time": optimization_time,
                    **context,
                },
                timestamp=datetime.now(timezone.utc),
            )

            await self._store_metric(algorithm_metric)
            self.algorithm_performance[algorithm_type].append(performance_score)

        except Exception as e:
            logger.error(f"Error recording algorithm performance: {e}")

    async def generate_learning_effectiveness_report(
        self, time_period_days: int = 7
    ) -> LearningEffectivenessReport:
        """Generate comprehensive learning effectiveness report."""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            # Get metrics for the time period
            period_metrics = await self._get_metrics_for_period(start_date)

            # Calculate performance trends
            performance_trends = await self._calculate_performance_trends(
                period_metrics
            )

            # Calculate algorithm effectiveness
            algorithm_effectiveness = await self._calculate_algorithm_effectiveness(
                period_metrics
            )

            # Calculate cross-agent learning impact
            cross_agent_impact = await self._calculate_cross_agent_impact(start_date)

            # Calculate overall learning score
            overall_score = await self._calculate_overall_learning_score(
                performance_trends, algorithm_effectiveness, cross_agent_impact
            )

            # Create report
            report = LearningEffectivenessReport(
                report_id=f"report_{self.agent_id}_{int(time.time())}",
                agent_id=self.agent_id,
                time_period=f"{time_period_days} days",
                total_decisions=len(
                    [m for m in period_metrics if m.metric_type == "decision_accuracy"]
                ),
                learning_improvements=await self._identify_learning_improvements(
                    period_metrics
                ),
                performance_trends=performance_trends,
                algorithm_effectiveness=algorithm_effectiveness,
                cross_agent_learning_impact=cross_agent_impact,
                overall_learning_score=overall_score,
                generated_at=datetime.now(timezone.utc),
            )

            self.learning_reports.append(report)
            await self._store_learning_report(report)

            return report

        except Exception as e:
            logger.error(f"Error generating learning effectiveness report: {e}")
            raise

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time learning metrics."""
        try:
            current_time = datetime.now(timezone.utc)

            # Calculate recent performance
            recent_accuracy = self._calculate_recent_average(
                self.decision_accuracy_history, window_size=50
            )

            recent_convergence = self._calculate_recent_average(
                self.learning_convergence_times, window_size=10
            )

            # Algorithm performance summary
            algorithm_summary = {}
            for alg_type, performance_history in self.algorithm_performance.items():
                if performance_history:
                    algorithm_summary[alg_type] = {
                        "recent_performance": self._calculate_recent_average(
                            performance_history, 20
                        ),
                        "trend": self._calculate_trend(list(performance_history)[-20:]),
                        "total_uses": len(performance_history),
                    }

            # Cross-agent learning summary
            recent_cross_learning = [
                record
                for record in self.cross_agent_insights_applied
                if datetime.fromisoformat(record["timestamp"])
                > current_time - timedelta(hours=24)
            ]

            cross_learning_success_rate = (
                sum(
                    1
                    for record in recent_cross_learning
                    if record["application_success"]
                )
                / len(recent_cross_learning)
                if recent_cross_learning
                else 0.0
            )

            return {
                "agent_id": self.agent_id,
                "timestamp": current_time.isoformat(),
                "decision_accuracy": {
                    "current": recent_accuracy,
                    "baseline": self.baseline_metrics.get("decision_accuracy", 0.0),
                    "improvement": recent_accuracy
                    - self.baseline_metrics.get("decision_accuracy", 0.0),
                },
                "learning_convergence": {
                    "average_time": recent_convergence,
                    "baseline": self.baseline_metrics.get("learning_convergence", 0.0),
                    "improvement": self.baseline_metrics.get(
                        "learning_convergence", 0.0
                    )
                    - recent_convergence,
                },
                "algorithm_performance": algorithm_summary,
                "cross_agent_learning": {
                    "success_rate": cross_learning_success_rate,
                    "insights_applied_24h": len(recent_cross_learning),
                    "knowledge_sharing_effectiveness": dict(
                        self.knowledge_sharing_effectiveness
                    ),
                },
                "total_metrics_collected": sum(
                    len(history) for history in self.metrics_history.values()
                ),
            }

        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {"error": str(e)}

    async def _create_metrics_tables(self):
        """Create database tables for metrics storage."""
        try:
            from sqlalchemy import text

            async with self.database.get_session() as session:
                await session.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS learning_metrics (
                        metric_id VARCHAR PRIMARY KEY,
                        agent_id VARCHAR NOT NULL,
                        metric_type VARCHAR NOT NULL,
                        metric_value FLOAT NOT NULL,
                        baseline_value FLOAT,
                        improvement_percentage FLOAT,
                        confidence_score FLOAT NOT NULL,
                        measurement_context JSONB,
                        timestamp TIMESTAMP NOT NULL
                    )
                """
                    )
                )

                await session.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS learning_effectiveness_reports (
                        report_id VARCHAR PRIMARY KEY,
                        agent_id VARCHAR NOT NULL,
                        time_period VARCHAR NOT NULL,
                        total_decisions INTEGER NOT NULL,
                        learning_improvements JSONB,
                        performance_trends JSONB,
                        algorithm_effectiveness JSONB,
                        cross_agent_learning_impact FLOAT,
                        overall_learning_score FLOAT,
                        generated_at TIMESTAMP NOT NULL
                    )
                """
                    )
                )

                await session.commit()

        except Exception as e:
            logger.error(f"Error creating metrics tables: {e}")
            raise

    async def _store_metric(self, metric: LearningMetric):
        """Store a learning metric in the database."""
        try:
            from sqlalchemy import text

            # Calculate improvement percentage if baseline exists
            if metric.baseline_value is not None:
                if metric.baseline_value != 0:
                    improvement = (
                        (metric.metric_value - metric.baseline_value)
                        / metric.baseline_value
                    ) * 100
                    metric.improvement_percentage = improvement

            async with self.database.get_session() as session:
                await session.execute(
                    text(
                        """
                    INSERT INTO learning_metrics
                    (metric_id, agent_id, metric_type, metric_value, baseline_value,
                     improvement_percentage, confidence_score, measurement_context, timestamp)
                    VALUES (:metric_id, :agent_id, :metric_type, :metric_value, :baseline_value,
                            :improvement_percentage, :confidence_score, :measurement_context, :timestamp)
                """
                    ),
                    {
                        "metric_id": metric.metric_id,
                        "agent_id": metric.agent_id,
                        "metric_type": metric.metric_type,
                        "metric_value": metric.metric_value,
                        "baseline_value": metric.baseline_value,
                        "improvement_percentage": metric.improvement_percentage,
                        "confidence_score": metric.confidence_score,
                        "measurement_context": json.dumps(metric.measurement_context),
                        "timestamp": metric.timestamp.replace(
                            tzinfo=None
                        ),  # Remove timezone
                    },
                )
                await session.commit()

            # Add to in-memory history
            self.metrics_history[metric.metric_type].append(metric)

        except Exception as e:
            logger.error(f"Error storing metric: {e}")

    async def _batch_store_metrics(self, metrics_batch: List[LearningMetric]):
        """Store multiple metrics in single database transaction for better performance."""
        if not metrics_batch:
            return

        try:
            async with self.database.get_session() as session:
                from sqlalchemy import text

                # Prepare batch data with improvement calculations
                batch_data = []
                for metric in metrics_batch:
                    # Calculate improvement percentage if baseline exists
                    if metric.baseline_value is not None and metric.baseline_value != 0:
                        improvement = (
                            (metric.metric_value - metric.baseline_value)
                            / metric.baseline_value
                        ) * 100
                        metric.improvement_percentage = improvement

                    batch_data.append(
                        {
                            "metric_id": metric.metric_id,
                            "agent_id": metric.agent_id,
                            "metric_type": metric.metric_type,
                            "metric_value": metric.metric_value,
                            "baseline_value": metric.baseline_value,
                            "improvement_percentage": metric.improvement_percentage,
                            "confidence_score": metric.confidence_score,
                            "measurement_context": json.dumps(
                                metric.measurement_context
                            ),
                            "timestamp": metric.timestamp.replace(
                                tzinfo=None
                            ),  # Remove timezone
                        }
                    )

                # Execute batch insert
                await session.execute(
                    text(
                        """
                        INSERT INTO learning_metrics
                        (metric_id, agent_id, metric_type, metric_value, baseline_value,
                         improvement_percentage, confidence_score, measurement_context, timestamp)
                        VALUES (:metric_id, :agent_id, :metric_type, :metric_value, :baseline_value,
                                :improvement_percentage, :confidence_score, :measurement_context, :timestamp)
                    """
                    ),
                    batch_data,
                )
                await session.commit()

                # Add to in-memory history
                for metric in metrics_batch:
                    self.metrics_history[metric.metric_type].append(metric)

                logger.debug(f"✅ Batch stored {len(metrics_batch)} metrics")

        except Exception as e:
            logger.error(f"Error batch storing metrics: {e}")

    async def _load_historical_metrics(self):
        """Load historical metrics from database."""
        try:
            from sqlalchemy import text

            async with self.database.get_session() as session:
                result = await session.execute(
                    text(
                        """
                    SELECT * FROM learning_metrics
                    WHERE agent_id = :agent_id
                    ORDER BY timestamp DESC
                    LIMIT 5000
                """
                    ),
                    {"agent_id": self.agent_id},
                )

                metrics = result.fetchall()

                for metric_row in metrics:
                    metric = LearningMetric(
                        metric_id=metric_row.metric_id,
                        agent_id=metric_row.agent_id,
                        metric_type=metric_row.metric_type,
                        metric_value=metric_row.metric_value,
                        baseline_value=metric_row.baseline_value,
                        improvement_percentage=metric_row.improvement_percentage,
                        confidence_score=metric_row.confidence_score,
                        measurement_context=metric_row.measurement_context or {},
                        timestamp=metric_row.timestamp,
                    )

                    self.metrics_history[metric.metric_type].append(metric)

                    # Populate specific histories
                    if metric.metric_type == "decision_accuracy":
                        self.decision_accuracy_history.append(metric.metric_value)
                    elif metric.metric_type == "learning_convergence":
                        self.learning_convergence_times.append(metric.metric_value)

        except Exception as e:
            logger.warning(f"Error loading historical metrics: {e}")

    async def get_historical_metrics(self) -> Dict[str, List[Any]]:
        """Get historical metrics for persistence testing."""
        try:
            # Load from database if not already loaded
            if not self.metrics_history or all(
                not metrics for metrics in self.metrics_history.values()
            ):
                await self._load_historical_metrics()

            # Return the metrics history
            return dict(self.metrics_history)

        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return {}

    async def _calculate_baseline_metrics(self):
        """Calculate baseline metrics from historical data."""
        try:
            baseline_period = datetime.now(timezone.utc) - timedelta(
                days=self.baseline_period_days
            )

            for metric_type, history in self.metrics_history.items():
                baseline_values = []
                for metric in history:
                    # Handle timezone-aware vs timezone-naive comparison
                    metric_time = metric.timestamp
                    if metric_time.tzinfo is None:
                        metric_time = metric_time.replace(tzinfo=timezone.utc)

                    if metric_time < baseline_period:
                        baseline_values.append(metric.metric_value)

                if baseline_values:
                    self.baseline_metrics[metric_type] = statistics.mean(
                        baseline_values
                    )
                else:
                    # Default baselines
                    if metric_type == "decision_accuracy":
                        self.baseline_metrics[metric_type] = 0.5
                    elif metric_type == "execution_time":
                        self.baseline_metrics[metric_type] = 1000.0  # 1 second
                    elif metric_type == "decision_quality":
                        self.baseline_metrics[metric_type] = 0.5
                    elif metric_type == "learning_convergence":
                        self.baseline_metrics[metric_type] = 5000.0  # 5 seconds
                    else:
                        self.baseline_metrics[metric_type] = 0.0

        except Exception as e:
            logger.error(f"Error calculating baseline metrics: {e}")

    def _calculate_recent_average(self, values: deque, window_size: int) -> float:
        """Calculate average of recent values."""
        if not values:
            return 0.0

        recent_values = list(values)[-window_size:]
        return statistics.mean(recent_values) if recent_values else 0.0

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "stable"

        # Simple linear trend calculation
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        if not first_half or not second_half:
            return "stable"

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        if second_avg > first_avg * 1.05:
            return "improving"
        elif second_avg < first_avg * 0.95:
            return "declining"
        else:
            return "stable"

    async def _get_metrics_for_period(
        self, start_date: datetime
    ) -> List[LearningMetric]:
        """Get metrics for a specific time period."""
        period_metrics = []

        for history in self.metrics_history.values():
            for metric in history:
                if metric.timestamp >= start_date:
                    period_metrics.append(metric)

        return period_metrics

    async def _calculate_performance_trends(
        self, metrics: List[LearningMetric]
    ) -> Dict[str, List[float]]:
        """Calculate performance trends from metrics."""
        trends = defaultdict(list)

        for metric in metrics:
            trends[metric.metric_type].append(metric.metric_value)

        return dict(trends)

    async def _calculate_algorithm_effectiveness(
        self, metrics: List[LearningMetric]
    ) -> Dict[str, float]:
        """Calculate algorithm effectiveness scores."""
        algorithm_metrics = [
            m for m in metrics if m.metric_type == "algorithm_performance"
        ]
        effectiveness = {}

        for metric in algorithm_metrics:
            alg_type = metric.measurement_context.get("algorithm_type", "unknown")
            if alg_type not in effectiveness:
                effectiveness[alg_type] = []
            effectiveness[alg_type].append(metric.metric_value)

        # Calculate average effectiveness
        for alg_type, values in effectiveness.items():
            effectiveness[alg_type] = statistics.mean(values) if values else 0.0

        return effectiveness

    async def _calculate_cross_agent_impact(self, start_date: datetime) -> float:
        """Calculate cross-agent learning impact."""
        recent_cross_learning = [
            record
            for record in self.cross_agent_insights_applied
            if datetime.fromisoformat(record["timestamp"]) >= start_date
        ]

        if not recent_cross_learning:
            return 0.0

        # Calculate average performance improvement from cross-agent learning
        improvements = [
            record["performance_improvement"]
            for record in recent_cross_learning
            if record["application_success"]
        ]

        return statistics.mean(improvements) if improvements else 0.0

    async def _calculate_overall_learning_score(
        self,
        performance_trends: Dict[str, List[float]],
        algorithm_effectiveness: Dict[str, float],
        cross_agent_impact: float,
    ) -> float:
        """Calculate overall learning effectiveness score."""
        try:
            score_components = []

            # Decision accuracy improvement
            if "decision_accuracy" in performance_trends:
                accuracy_trend = self._calculate_trend(
                    performance_trends["decision_accuracy"]
                )
                if accuracy_trend == "improving":
                    score_components.append(0.8)
                elif accuracy_trend == "stable":
                    score_components.append(0.6)
                else:
                    score_components.append(0.4)

            # Algorithm effectiveness
            if algorithm_effectiveness:
                avg_algorithm_score = statistics.mean(algorithm_effectiveness.values())
                score_components.append(avg_algorithm_score)

            # Cross-agent learning impact
            score_components.append(min(1.0, cross_agent_impact * 10))  # Scale to 0-1

            # Learning convergence improvement
            if "learning_convergence" in performance_trends:
                convergence_trend = self._calculate_trend(
                    performance_trends["learning_convergence"]
                )
                if convergence_trend == "declining":  # Faster convergence is better
                    score_components.append(0.8)
                elif convergence_trend == "stable":
                    score_components.append(0.6)
                else:
                    score_components.append(0.4)

            return statistics.mean(score_components) if score_components else 0.5

        except Exception as e:
            logger.error(f"Error calculating overall learning score: {e}")
            return 0.5

    async def _identify_learning_improvements(
        self, metrics: List[LearningMetric]
    ) -> List[LearningMetric]:
        """Identify significant learning improvements."""
        improvements = []

        for metric in metrics:
            if (
                metric.improvement_percentage is not None
                and metric.improvement_percentage > 5.0  # 5% improvement threshold
                and metric.confidence_score > 0.7
            ):
                improvements.append(metric)

        return improvements

    async def _store_learning_report(self, report: LearningEffectivenessReport):
        """Store learning effectiveness report in database."""
        try:
            from sqlalchemy import text

            async with self.database.get_session() as session:
                await session.execute(
                    text(
                        """
                    INSERT INTO learning_effectiveness_reports
                    (report_id, agent_id, time_period, total_decisions, learning_improvements,
                     performance_trends, algorithm_effectiveness, cross_agent_learning_impact,
                     overall_learning_score, generated_at)
                    VALUES (:report_id, :agent_id, :time_period, :total_decisions, :learning_improvements,
                            :performance_trends, :algorithm_effectiveness, :cross_agent_learning_impact,
                            :overall_learning_score, :generated_at)
                """
                    ),
                    {
                        "report_id": report.report_id,
                        "agent_id": report.agent_id,
                        "time_period": report.time_period,
                        "total_decisions": report.total_decisions,
                        "learning_improvements": json.dumps(
                            [asdict(imp) for imp in report.learning_improvements],
                            default=str,
                        ),
                        "performance_trends": json.dumps(report.performance_trends),
                        "algorithm_effectiveness": json.dumps(
                            report.algorithm_effectiveness
                        ),
                        "cross_agent_learning_impact": report.cross_agent_learning_impact,
                        "overall_learning_score": report.overall_learning_score,
                        "generated_at": report.generated_at.replace(
                            tzinfo=None
                        ),  # Remove timezone,
                    },
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Error storing learning report: {e}")

    async def _calculate_metric_improvements(self):
        """Calculate and update metric improvements."""
        try:
            for metric_type, history in self.metrics_history.items():
                if len(history) < self.min_samples_for_trend:
                    continue

                recent_metrics = list(history)[-self.min_samples_for_trend :]
                baseline = self.baseline_metrics.get(metric_type)

                if baseline is not None:
                    recent_avg = statistics.mean(
                        [m.metric_value for m in recent_metrics]
                    )

                    # Update improvement percentage for recent metrics
                    for metric in recent_metrics[-5:]:  # Update last 5 metrics
                        if metric.baseline_value is None:
                            metric.baseline_value = baseline

                        if baseline != 0:
                            improvement = (
                                (metric.metric_value - baseline) / baseline
                            ) * 100
                            metric.improvement_percentage = improvement

        except Exception as e:
            logger.error(f"Error calculating metric improvements: {e}")
