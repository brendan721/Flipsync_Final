#!/usr/bin/env python3
"""
Adaptive Learning Rate Adjustment System
=======================================

Phase 3.3 implementation for adaptive learning rate adjustment based on
performance feedback with automated scaling and resource optimization.

Features:
- Adaptive learning rate adjustment
- Performance-based feedback loops
- Automated scaling decisions
- Resource optimization algorithms
- Learning efficiency metrics
- Real-time adaptation algorithms

Technical Requirements:
- Learning adjustments <100ms
- Performance analysis <200ms
- Production database integration
- Real-time adaptation capabilities
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

from fs_agt_clean.core.coordination.event_system import get_event_bus, Event, EventType
from fs_agt_clean.core.db.database import get_database

logger = logging.getLogger(__name__)


class LearningStrategy(Enum):
    """Learning rate adjustment strategies."""

    GRADIENT_DESCENT = "gradient_descent"
    ADAPTIVE_MOMENTUM = "adaptive_momentum"
    PERFORMANCE_BASED = "performance_based"
    EXPONENTIAL_DECAY = "exponential_decay"
    CYCLICAL_LEARNING = "cyclical_learning"
    AUTO_ADAPTIVE = "auto_adaptive"


class PerformanceTrend(Enum):
    """Performance trend indicators."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


@dataclass
class LearningMetrics:
    """Learning performance metrics for an agent."""

    agent_id: str
    learning_rate: float = 0.01
    performance_score: float = 0.0
    learning_efficiency: float = 0.0
    convergence_rate: float = 0.0
    error_reduction_rate: float = 0.0
    adaptation_speed: float = 0.0
    stability_score: float = 0.0
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PerformanceWindow:
    """Performance measurement window for trend analysis."""

    window_size: int = 100
    performance_history: deque = field(default_factory=lambda: deque(maxlen=100))
    error_history: deque = field(default_factory=lambda: deque(maxlen=100))
    learning_rate_history: deque = field(default_factory=lambda: deque(maxlen=100))
    timestamp_history: deque = field(default_factory=lambda: deque(maxlen=100))


class AdaptiveLearningRateSystem:
    """
    Sophisticated adaptive learning rate adjustment system with performance
    feedback and automated optimization.
    """

    def __init__(self, db_session=None):
        """Initialize the adaptive learning system."""
        self.db_session = db_session or get_database()
        self.event_bus = get_event_bus()

        # Learning metrics tracking
        self.agent_metrics: Dict[str, LearningMetrics] = {}
        self.performance_windows: Dict[str, PerformanceWindow] = {}

        # System configuration
        self.default_learning_rate = 0.01
        self.min_learning_rate = 0.0001
        self.max_learning_rate = 0.1
        self.adaptation_interval = 10.0  # seconds
        self.performance_window_size = 100

        # Adaptation parameters
        self.adaptation_params = {
            "momentum_factor": 0.9,
            "decay_rate": 0.95,
            "improvement_threshold": 0.05,
            "stability_threshold": 0.02,
            "volatility_threshold": 0.1,
            "convergence_threshold": 0.001,
        }

        # Performance metrics
        self.system_metrics = {
            "total_adaptations": 0,
            "successful_adaptations": 0,
            "average_learning_rate": 0.01,
            "system_learning_efficiency": 0.0,
            "adaptation_success_rate": 0.0,
        }

        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()

        logger.info("AdaptiveLearningRateSystem initialized")

    async def start(self) -> None:
        """Start the adaptive learning system."""
        try:
            # Start background adaptation tasks
            self._background_tasks.add(
                asyncio.create_task(self._learning_rate_adapter())
            )
            self._background_tasks.add(
                asyncio.create_task(self._performance_analyzer())
            )
            self._background_tasks.add(asyncio.create_task(self._system_optimizer()))

            logger.info("Adaptive learning rate system started")

        except Exception as e:
            logger.error(f"Failed to start adaptive learning system: {e}")
            raise

    async def stop(self) -> None:
        """Stop the adaptive learning system."""
        try:
            # Signal shutdown
            self._shutdown_event.set()

            # Cancel background tasks
            for task in self._background_tasks:
                task.cancel()

            # Wait for tasks to complete
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            logger.info("Adaptive learning rate system stopped")

        except Exception as e:
            logger.error(f"Error stopping adaptive learning system: {e}")

    async def register_agent(
        self, agent_id: str, initial_learning_rate: Optional[float] = None
    ) -> None:
        """Register an agent for adaptive learning rate management."""
        try:
            learning_rate = initial_learning_rate or self.default_learning_rate

            self.agent_metrics[agent_id] = LearningMetrics(
                agent_id=agent_id, learning_rate=learning_rate
            )

            self.performance_windows[agent_id] = PerformanceWindow(
                window_size=self.performance_window_size
            )

            logger.info(
                f"Agent {agent_id} registered for adaptive learning (rate: {learning_rate})"
            )

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")

    async def update_performance_metrics(
        self,
        agent_id: str,
        performance_score: float,
        error_rate: float,
    ) -> None:
        """Update performance metrics for an agent."""
        start_time = time.perf_counter()

        try:
            if agent_id not in self.agent_metrics:
                await self.register_agent(agent_id)

            metrics = self.agent_metrics[agent_id]
            window = self.performance_windows[agent_id]

            # Update performance history
            current_time = datetime.now(timezone.utc)
            window.performance_history.append(performance_score)
            window.error_history.append(error_rate)
            window.learning_rate_history.append(metrics.learning_rate)
            window.timestamp_history.append(current_time)

            # Calculate derived metrics
            metrics.performance_score = performance_score
            metrics.learning_efficiency = await self._calculate_learning_efficiency(
                agent_id
            )
            metrics.convergence_rate = await self._calculate_convergence_rate(agent_id)
            metrics.error_reduction_rate = await self._calculate_error_reduction_rate(
                agent_id
            )
            metrics.stability_score = await self._calculate_stability_score(agent_id)
            metrics.last_update = current_time

            # Trigger adaptive learning rate adjustment
            await self._adapt_learning_rate(agent_id)

            elapsed_time = (time.perf_counter() - start_time) * 1000

            if elapsed_time > 100:  # Log if update takes too long
                logger.warning(
                    f"Performance update for {agent_id} took {elapsed_time:.2f}ms"
                )

        except Exception as e:
            logger.error(f"Failed to update performance metrics for {agent_id}: {e}")

    async def get_learning_rate(self, agent_id: str) -> float:
        """Get current learning rate for an agent."""
        if agent_id in self.agent_metrics:
            return self.agent_metrics[agent_id].learning_rate
        return self.default_learning_rate

    async def get_agent_learning_status(
        self, agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive learning status for an agent."""
        if agent_id not in self.agent_metrics:
            return None

        metrics = self.agent_metrics[agent_id]
        window = self.performance_windows[agent_id]

        # Calculate performance trend
        trend = await self._analyze_performance_trend(agent_id)

        return {
            "agent_id": agent_id,
            "current_learning_rate": metrics.learning_rate,
            "performance_score": metrics.performance_score,
            "learning_efficiency": metrics.learning_efficiency,
            "convergence_rate": metrics.convergence_rate,
            "error_reduction_rate": metrics.error_reduction_rate,
            "stability_score": metrics.stability_score,
            "performance_trend": trend.value,
            "last_update": metrics.last_update.isoformat(),
            "performance_history_size": len(window.performance_history),
            "recent_performance": (
                list(window.performance_history)[-10:]
                if window.performance_history
                else []
            ),
        }

    async def get_system_learning_dashboard(self) -> Dict[str, Any]:
        """Get system-wide learning performance dashboard."""
        try:
            # Calculate system-wide metrics
            if self.agent_metrics:
                avg_learning_rate = statistics.mean(
                    [m.learning_rate for m in self.agent_metrics.values()]
                )
                avg_performance = statistics.mean(
                    [m.performance_score for m in self.agent_metrics.values()]
                )
                avg_efficiency = statistics.mean(
                    [m.learning_efficiency for m in self.agent_metrics.values()]
                )
                avg_stability = statistics.mean(
                    [m.stability_score for m in self.agent_metrics.values()]
                )
            else:
                avg_learning_rate = avg_performance = avg_efficiency = avg_stability = (
                    0.0
                )

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system_overview": {
                    "total_agents": len(self.agent_metrics),
                    "average_learning_rate": avg_learning_rate,
                    "average_performance_score": avg_performance,
                    "average_learning_efficiency": avg_efficiency,
                    "average_stability_score": avg_stability,
                },
                "system_metrics": self.system_metrics.copy(),
                "agent_summaries": [
                    {
                        "agent_id": metrics.agent_id,
                        "learning_rate": metrics.learning_rate,
                        "performance_score": metrics.performance_score,
                        "learning_efficiency": metrics.learning_efficiency,
                        "stability_score": metrics.stability_score,
                    }
                    for metrics in self.agent_metrics.values()
                ],
            }

        except Exception as e:
            logger.error(f"Failed to generate learning dashboard: {e}")
            return {"error": str(e)}

    # Private adaptive learning methods

    async def _adapt_learning_rate(self, agent_id: str) -> None:
        """Adapt learning rate for an agent based on performance."""
        try:
            if agent_id not in self.agent_metrics:
                return

            metrics = self.agent_metrics[agent_id]
            self.performance_windows[agent_id]

            # Analyze performance trend
            trend = await self._analyze_performance_trend(agent_id)

            # Calculate new learning rate based on trend and metrics
            new_learning_rate = await self._calculate_adaptive_learning_rate(
                agent_id, trend
            )

            # Apply learning rate bounds
            new_learning_rate = max(
                self.min_learning_rate, min(self.max_learning_rate, new_learning_rate)
            )

            # Update learning rate if significantly different
            rate_change = (
                abs(new_learning_rate - metrics.learning_rate) / metrics.learning_rate
            )
            if rate_change > 0.01:  # 1% threshold for changes
                old_rate = metrics.learning_rate
                metrics.learning_rate = new_learning_rate

                # Update system metrics
                self.system_metrics["total_adaptations"] += 1

                # Publish adaptation event
                await self._publish_adaptation_event(
                    agent_id, old_rate, new_learning_rate, trend
                )

                logger.info(
                    f"Adapted learning rate for {agent_id}: {old_rate:.6f} -> {new_learning_rate:.6f} "
                    f"(trend: {trend.value})"
                )

        except Exception as e:
            logger.error(f"Error adapting learning rate for {agent_id}: {e}")

    async def _calculate_adaptive_learning_rate(
        self, agent_id: str, trend: PerformanceTrend
    ) -> float:
        """Calculate new learning rate based on performance trend and metrics."""
        try:
            metrics = self.agent_metrics[agent_id]
            current_rate = metrics.learning_rate

            # Base adjustment factor
            adjustment_factor = 1.0

            # Adjust based on performance trend
            if trend == PerformanceTrend.IMPROVING:
                # Performance is improving, maintain or slightly increase rate
                adjustment_factor = 1.05 if metrics.stability_score > 0.8 else 1.0

            elif trend == PerformanceTrend.DECLINING:
                # Performance is declining, reduce learning rate
                adjustment_factor = 0.8

            elif trend == PerformanceTrend.VOLATILE:
                # High volatility, reduce learning rate for stability
                adjustment_factor = 0.7

            elif trend == PerformanceTrend.STABLE:
                # Stable performance, can try increasing rate slightly
                adjustment_factor = 1.02 if metrics.convergence_rate < 0.001 else 1.0

            # Adjust based on learning efficiency
            if metrics.learning_efficiency > 0.8:
                adjustment_factor *= 1.1  # High efficiency, can increase rate
            elif metrics.learning_efficiency < 0.3:
                adjustment_factor *= 0.9  # Low efficiency, reduce rate

            # Adjust based on convergence rate
            if metrics.convergence_rate > 0.01:
                adjustment_factor *= (
                    0.95  # Fast convergence, reduce rate to avoid overshooting
                )
            elif metrics.convergence_rate < 0.001:
                adjustment_factor *= 1.05  # Slow convergence, increase rate

            # Apply exponential decay if performance has plateaued
            window = self.performance_windows[agent_id]
            if len(window.performance_history) >= 20:
                recent_variance = statistics.variance(
                    list(window.performance_history)[-20:]
                )
                if recent_variance < 0.001:  # Very low variance indicates plateau
                    adjustment_factor *= self.adaptation_params["decay_rate"]

            return current_rate * adjustment_factor

        except Exception as e:
            logger.error(f"Error calculating adaptive learning rate: {e}")
            return metrics.learning_rate

    async def _analyze_performance_trend(self, agent_id: str) -> PerformanceTrend:
        """Analyze performance trend for an agent."""
        try:
            window = self.performance_windows[agent_id]

            if len(window.performance_history) < 10:
                return PerformanceTrend.UNKNOWN

            # Get recent performance data
            recent_data = list(window.performance_history)[-20:]

            # Calculate trend using linear regression slope
            n = len(recent_data)
            x_values = list(range(n))
            y_values = recent_data

            # Calculate slope
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(y_values)

            numerator = sum(
                (x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)
            )
            denominator = sum((x - x_mean) ** 2 for x in x_values)

            if denominator == 0:
                return PerformanceTrend.STABLE

            slope = numerator / denominator

            # Calculate volatility (coefficient of variation)
            if y_mean > 0:
                volatility = statistics.stdev(y_values) / y_mean
            else:
                volatility = 0

            # Determine trend based on slope and volatility
            if volatility > self.adaptation_params["volatility_threshold"]:
                return PerformanceTrend.VOLATILE
            elif slope > self.adaptation_params["improvement_threshold"]:
                return PerformanceTrend.IMPROVING
            elif slope < -self.adaptation_params["improvement_threshold"]:
                return PerformanceTrend.DECLINING
            else:
                return PerformanceTrend.STABLE

        except Exception as e:
            logger.error(f"Error analyzing performance trend: {e}")
            return PerformanceTrend.UNKNOWN

    async def _calculate_learning_efficiency(self, agent_id: str) -> float:
        """Calculate learning efficiency for an agent."""
        try:
            window = self.performance_windows[agent_id]

            if len(window.performance_history) < 5:
                return 0.0

            # Calculate efficiency as performance improvement per learning rate unit
            recent_performance = list(window.performance_history)[-10:]
            recent_rates = list(window.learning_rate_history)[-10:]

            if len(recent_performance) < 2:
                return 0.0

            # Calculate performance improvement
            performance_improvement = recent_performance[-1] - recent_performance[0]

            # Calculate average learning rate
            avg_learning_rate = statistics.mean(recent_rates)

            # Efficiency = improvement per unit learning rate
            if avg_learning_rate > 0:
                efficiency = max(0, performance_improvement / avg_learning_rate)
                return min(1.0, efficiency)  # Cap at 1.0

            return 0.0

        except Exception as e:
            logger.error(f"Error calculating learning efficiency: {e}")
            return 0.0

    async def _calculate_convergence_rate(self, agent_id: str) -> float:
        """Calculate convergence rate for an agent."""
        try:
            window = self.performance_windows[agent_id]

            if len(window.performance_history) < 10:
                return 0.0

            # Calculate rate of change in performance
            recent_performance = list(window.performance_history)[-10:]

            # Calculate differences between consecutive measurements
            differences = [
                abs(recent_performance[i] - recent_performance[i - 1])
                for i in range(1, len(recent_performance))
            ]

            # Convergence rate is the average rate of change
            return statistics.mean(differences) if differences else 0.0

        except Exception as e:
            logger.error(f"Error calculating convergence rate: {e}")
            return 0.0

    async def _calculate_error_reduction_rate(self, agent_id: str) -> float:
        """Calculate error reduction rate for an agent."""
        try:
            window = self.performance_windows[agent_id]

            if len(window.error_history) < 5:
                return 0.0

            # Calculate error reduction over recent history
            recent_errors = list(window.error_history)[-10:]

            if len(recent_errors) < 2:
                return 0.0

            # Calculate percentage reduction in error
            initial_error = recent_errors[0]
            final_error = recent_errors[-1]

            if initial_error > 0:
                reduction_rate = (initial_error - final_error) / initial_error
                return max(0, reduction_rate)  # Only positive reductions

            return 0.0

        except Exception as e:
            logger.error(f"Error calculating error reduction rate: {e}")
            return 0.0

    async def _calculate_stability_score(self, agent_id: str) -> float:
        """Calculate stability score for an agent."""
        try:
            window = self.performance_windows[agent_id]

            if len(window.performance_history) < 5:
                return 0.0

            # Calculate stability as inverse of coefficient of variation
            recent_performance = list(window.performance_history)[-20:]

            if len(recent_performance) < 2:
                return 0.0

            mean_performance = statistics.mean(recent_performance)

            if mean_performance > 0:
                cv = statistics.stdev(recent_performance) / mean_performance
                stability = 1.0 / (1.0 + cv)  # Higher stability for lower CV
                return min(1.0, stability)

            return 0.0

        except Exception as e:
            logger.error(f"Error calculating stability score: {e}")
            return 0.0

    # Event publishing helpers

    async def _publish_adaptation_event(
        self, agent_id: str, old_rate: float, new_rate: float, trend: PerformanceTrend
    ) -> None:
        """Publish learning rate adaptation event."""
        try:
            event = Event(
                event_type=EventType.NOTIFICATION,
                source="adaptive_learning",
                target=agent_id,
                data={
                    "agent_id": agent_id,
                    "event_name": "learning_rate_adapted",
                    "old_learning_rate": old_rate,
                    "new_learning_rate": new_rate,
                    "performance_trend": trend.value,
                    "rate_change_percentage": ((new_rate - old_rate) / old_rate) * 100,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            await self.event_bus.publish(event)

        except Exception as e:
            logger.error(f"Failed to publish adaptation event: {e}")

    # Background monitoring tasks

    async def _learning_rate_adapter(self) -> None:
        """Background task for continuous learning rate adaptation."""
        while not self._shutdown_event.is_set():
            try:
                start_time = time.perf_counter()
                adaptations_made = 0

                # Process all registered agents
                for agent_id in list(self.agent_metrics.keys()):
                    try:
                        await self._adapt_learning_rate(agent_id)
                        adaptations_made += 1
                    except Exception as e:
                        logger.error(
                            f"Error adapting learning rate for {agent_id}: {e}"
                        )

                # Update system metrics
                if self.agent_metrics:
                    avg_rate = statistics.mean(
                        [m.learning_rate for m in self.agent_metrics.values()]
                    )
                    self.system_metrics["average_learning_rate"] = avg_rate

                elapsed_time = (time.perf_counter() - start_time) * 1000

                if elapsed_time > 100:  # Log if adaptation cycle takes too long
                    logger.warning(
                        f"Learning rate adaptation cycle took {elapsed_time:.2f}ms"
                    )

                # Wait before next adaptation cycle
                await asyncio.sleep(self.adaptation_interval)

            except Exception as e:
                logger.error(f"Learning rate adapter error: {e}")
                await asyncio.sleep(5.0)

    async def _performance_analyzer(self) -> None:
        """Background task for performance analysis and optimization."""
        while not self._shutdown_event.is_set():
            try:
                # Analyze system-wide performance trends
                if self.agent_metrics:
                    # Calculate system learning efficiency
                    efficiencies = [
                        m.learning_efficiency for m in self.agent_metrics.values()
                    ]
                    system_efficiency = (
                        statistics.mean(efficiencies) if efficiencies else 0.0
                    )
                    self.system_metrics["system_learning_efficiency"] = (
                        system_efficiency
                    )

                    # Calculate adaptation success rate
                    total_adaptations = self.system_metrics["total_adaptations"]
                    successful_adaptations = self.system_metrics[
                        "successful_adaptations"
                    ]

                    if total_adaptations > 0:
                        success_rate = (
                            successful_adaptations / total_adaptations
                        ) * 100
                        self.system_metrics["adaptation_success_rate"] = success_rate

                    # Identify agents needing attention
                    for agent_id, metrics in self.agent_metrics.items():
                        if metrics.learning_efficiency < 0.2:
                            logger.warning(
                                f"Agent {agent_id} has low learning efficiency: {metrics.learning_efficiency:.3f}"
                            )

                        if metrics.stability_score < 0.3:
                            logger.warning(
                                f"Agent {agent_id} has low stability: {metrics.stability_score:.3f}"
                            )

                # Wait before next analysis cycle
                await asyncio.sleep(30.0)  # Analyze every 30 seconds

            except Exception as e:
                logger.error(f"Performance analyzer error: {e}")
                await asyncio.sleep(10.0)

    async def _system_optimizer(self) -> None:
        """Background task for system-wide optimization."""
        while not self._shutdown_event.is_set():
            try:
                # Perform system-wide optimizations
                if len(self.agent_metrics) > 1:
                    # Analyze cross-agent learning patterns
                    await self._analyze_cross_agent_patterns()

                    # Optimize system parameters
                    await self._optimize_system_parameters()

                    # Clean up old performance data
                    await self._cleanup_old_data()

                # Wait before next optimization cycle
                await asyncio.sleep(60.0)  # Optimize every minute

            except Exception as e:
                logger.error(f"System optimizer error: {e}")
                await asyncio.sleep(15.0)

    async def _analyze_cross_agent_patterns(self) -> None:
        """Analyze learning patterns across agents."""
        try:
            # Find agents with similar performance patterns
            agent_trends = {}
            for agent_id in self.agent_metrics.keys():
                trend = await self._analyze_performance_trend(agent_id)
                agent_trends[agent_id] = trend

            # Group agents by trend
            trend_groups = defaultdict(list)
            for agent_id, trend in agent_trends.items():
                trend_groups[trend].append(agent_id)

            # Log insights about cross-agent patterns
            for trend, agents in trend_groups.items():
                if len(agents) > 1:
                    logger.info(
                        f"Cross-agent pattern: {len(agents)} agents showing {trend.value} trend"
                    )

        except Exception as e:
            logger.error(f"Error analyzing cross-agent patterns: {e}")

    async def _optimize_system_parameters(self) -> None:
        """Optimize system-wide parameters based on performance."""
        try:
            if not self.agent_metrics:
                return

            # Calculate system-wide metrics
            avg_efficiency = statistics.mean(
                [m.learning_efficiency for m in self.agent_metrics.values()]
            )
            avg_stability = statistics.mean(
                [m.stability_score for m in self.agent_metrics.values()]
            )

            # Adjust adaptation interval based on system performance
            if avg_efficiency > 0.8 and avg_stability > 0.8:
                # High performance, can adapt more frequently
                self.adaptation_interval = max(5.0, self.adaptation_interval * 0.9)
            elif avg_efficiency < 0.3 or avg_stability < 0.3:
                # Low performance, adapt less frequently for stability
                self.adaptation_interval = min(30.0, self.adaptation_interval * 1.1)

            # Adjust adaptation parameters based on system state
            if avg_stability < 0.5:
                # Increase stability threshold for volatile system
                self.adaptation_params["stability_threshold"] = min(
                    0.05, self.adaptation_params["stability_threshold"] * 1.1
                )

        except Exception as e:
            logger.error(f"Error optimizing system parameters: {e}")

    async def _cleanup_old_data(self) -> None:
        """Clean up old performance data to prevent memory bloat."""
        try:
            current_time = datetime.now(timezone.utc)
            cleanup_threshold = timedelta(hours=24)  # Keep 24 hours of data

            agents_to_remove = []
            for agent_id, metrics in self.agent_metrics.items():
                # Remove agents that haven't been updated in 24 hours
                if (current_time - metrics.last_update) > cleanup_threshold:
                    agents_to_remove.append(agent_id)

            for agent_id in agents_to_remove:
                del self.agent_metrics[agent_id]
                if agent_id in self.performance_windows:
                    del self.performance_windows[agent_id]
                logger.info(f"Cleaned up old data for inactive agent: {agent_id}")

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
