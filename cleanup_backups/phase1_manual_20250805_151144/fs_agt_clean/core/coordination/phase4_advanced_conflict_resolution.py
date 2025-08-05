#!/usr/bin/env python3
"""
Phase 4: Advanced Conflict Resolution System
===========================================

Sophisticated distributed consensus conflict resolution building upon the existing
DistributedConsensusEngine with sub-200ms resolution times and production-grade reliability.

Features:
- Advanced conflict detection and classification
- Multi-tier resolution strategies
- Real-time conflict monitoring and analytics
- Automated escalation and recovery
- Performance optimization for sub-200ms targets
- Integration with Phase 4 coordination infrastructure

Technical Requirements:
- Conflict resolution <200ms
- Detection <50ms
- Production database integration
- 4+1 architecture compatibility
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum

# Import existing conflict resolution infrastructure
from fs_agt_clean.core.coordination.conflict.distributed_consensus_engine import (
    DistributedConsensusEngine,
    ConsensusResult,
    ConflictType,
)

logger = logging.getLogger(__name__)


class ConflictSeverity(Enum):
    """Conflict severity levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class ResolutionStrategy(Enum):
    """Conflict resolution strategies."""

    CONSENSUS = "consensus"
    PRIORITY_BASED = "priority_based"
    ROUND_ROBIN = "round_robin"
    PERFORMANCE_BASED = "performance_based"
    ESCALATION = "escalation"
    EMERGENCY_OVERRIDE = "emergency_override"


@dataclass
class ConflictContext:
    """Enhanced conflict context with additional metadata."""

    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    involved_agents: List[str]
    resource_or_decision: str
    conflict_data: Dict[str, Any]
    detected_at: datetime
    resolution_deadline: datetime
    priority_score: float
    previous_conflicts: List[str] = field(default_factory=list)
    escalation_level: int = 0
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolutionResult:
    """Enhanced resolution result with performance metrics."""

    conflict_id: str
    success: bool
    resolution: str
    strategy_used: ResolutionStrategy
    resolution_time_ms: float
    detection_time_ms: float
    total_time_ms: float
    winning_agent: Optional[str]
    consensus_details: Optional[ConsensusResult]
    performance_target_met: bool
    escalated: bool = False
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConflictMetrics:
    """Conflict resolution performance metrics."""

    total_conflicts: int = 0
    resolved_conflicts: int = 0
    failed_conflicts: int = 0
    escalated_conflicts: int = 0
    average_resolution_time_ms: float = 0.0
    sub_200ms_resolutions: int = 0
    performance_target_met_percentage: float = 0.0
    conflicts_by_severity: Dict[ConflictSeverity, int] = field(default_factory=dict)
    conflicts_by_type: Dict[ConflictType, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Phase4AdvancedConflictResolver:
    """
    Advanced conflict resolution system for Phase 4.

    Provides sophisticated conflict detection, classification, and resolution
    with sub-200ms performance targets and multi-tier resolution strategies.
    """

    def __init__(self, performance_target_ms: float = 200.0):
        """Initialize the advanced conflict resolver.

        Args:
            performance_target_ms: Target performance for conflict resolution (default: 200ms)
        """
        self.performance_target_ms = performance_target_ms
        self.resolver_id = f"phase4_resolver_{uuid.uuid4().hex[:8]}"

        # Use existing consensus engine as foundation
        self.consensus_engine = DistributedConsensusEngine()

        # Advanced conflict resolution state
        self.active_conflicts: Dict[str, ConflictContext] = {}
        self.conflict_history: List[ConflictContext] = []
        self.resolution_strategies: Dict[ConflictSeverity, ResolutionStrategy] = {}
        self.conflict_metrics = ConflictMetrics()

        # Agent performance tracking for resolution decisions
        self.agent_performance: Dict[str, Dict[str, float]] = {}

        # Conflict detection and monitoring
        self.conflict_detectors: List[Callable] = []
        self.is_monitoring = False
        self.monitoring_tasks: List[asyncio.Task] = []

        # Initialize default resolution strategies
        self._initialize_resolution_strategies()

        logger.info(
            f"🚀 Phase 4 Advanced Conflict Resolver initialized: {self.resolver_id}"
        )
        logger.info(f"🎯 Performance target: {self.performance_target_ms}ms")

    def _initialize_resolution_strategies(self):
        """Initialize default resolution strategies by severity."""
        self.resolution_strategies = {
            ConflictSeverity.LOW: ResolutionStrategy.ROUND_ROBIN,
            ConflictSeverity.MEDIUM: ResolutionStrategy.PERFORMANCE_BASED,
            ConflictSeverity.HIGH: ResolutionStrategy.PRIORITY_BASED,
            ConflictSeverity.CRITICAL: ResolutionStrategy.CONSENSUS,
            ConflictSeverity.EMERGENCY: ResolutionStrategy.EMERGENCY_OVERRIDE,
        }

    async def initialize(self) -> bool:
        """Initialize the conflict resolution system."""
        try:
            start_time = time.perf_counter()

            # Initialize consensus engine for 4+1 architecture
            autonomous_agents = [
                "market_agent",
                "executive_agent",
                "content_agent",
                "logistics_agent",
            ]

            for agent_id in autonomous_agents:
                await self.consensus_engine.register_agent(agent_id)

                # Initialize agent performance tracking
                self.agent_performance[agent_id] = {
                    "success_rate": 1.0,
                    "average_response_time": 100.0,
                    "reliability_score": 1.0,
                    "conflict_resolution_score": 1.0,
                }

                logger.info(f"✅ Registered agent for conflict resolution: {agent_id}")

            # Register default conflict detectors
            self._register_default_detectors()

            initialization_time = (time.perf_counter() - start_time) * 1000

            logger.info(
                f"✅ Phase 4 conflict resolver initialized in {initialization_time:.2f}ms"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize conflict resolver: {e}")
            return False

    async def start_monitoring(self) -> bool:
        """Start conflict monitoring and detection."""
        try:
            if self.is_monitoring:
                logger.warning("Conflict monitoring is already running")
                return True

            self.is_monitoring = True

            # Start conflict detection
            detection_task = asyncio.create_task(self._monitor_conflicts())
            self.monitoring_tasks.append(detection_task)

            # Start performance monitoring
            metrics_task = asyncio.create_task(self._monitor_performance())
            self.monitoring_tasks.append(metrics_task)

            # Start conflict cleanup
            cleanup_task = asyncio.create_task(self._cleanup_resolved_conflicts())
            self.monitoring_tasks.append(cleanup_task)

            logger.info("🚀 Phase 4 conflict monitoring started")
            return True

        except Exception as e:
            logger.error(f"Failed to start conflict monitoring: {e}")
            self.is_monitoring = False
            return False

    async def detect_and_resolve_conflict(
        self,
        conflict_type: ConflictType,
        involved_agents: List[str],
        resource_or_decision: str,
        conflict_data: Dict[str, Any],
        severity: ConflictSeverity = ConflictSeverity.MEDIUM,
        deadline_ms: float = 5000.0,
    ) -> ResolutionResult:
        """Detect and resolve a conflict with advanced strategies.

        Args:
            conflict_type: Type of conflict
            involved_agents: Agents involved in the conflict
            resource_or_decision: Resource or decision being contested
            conflict_data: Additional conflict information
            severity: Conflict severity level
            deadline_ms: Resolution deadline in milliseconds

        Returns:
            Resolution result with performance metrics
        """
        detection_start = time.perf_counter()
        conflict_id = str(uuid.uuid4())

        try:
            # Create conflict context
            conflict_context = ConflictContext(
                conflict_id=conflict_id,
                conflict_type=conflict_type,
                severity=severity,
                involved_agents=involved_agents,
                resource_or_decision=resource_or_decision,
                conflict_data=conflict_data,
                detected_at=datetime.now(timezone.utc),
                resolution_deadline=datetime.now(timezone.utc)
                + timedelta(milliseconds=deadline_ms),
                priority_score=self._calculate_priority_score(
                    severity, involved_agents, conflict_data
                ),
            )

            detection_time = (time.perf_counter() - detection_start) * 1000

            # Add to active conflicts
            self.active_conflicts[conflict_id] = conflict_context

            # Resolve the conflict
            resolution_result = await self._resolve_conflict(
                conflict_context, detection_time
            )

            # Update metrics
            await self._update_conflict_metrics(resolution_result)

            # Move to history
            self.conflict_history.append(conflict_context)
            self.active_conflicts.pop(conflict_id, None)

            return resolution_result

        except Exception as e:
            detection_time = (time.perf_counter() - detection_start) * 1000

            # Create failed result
            failed_result = ResolutionResult(
                conflict_id=conflict_id,
                success=False,
                resolution="failed",
                strategy_used=ResolutionStrategy.ESCALATION,
                resolution_time_ms=0.0,
                detection_time_ms=detection_time,
                total_time_ms=detection_time,
                winning_agent=None,
                consensus_details=None,
                performance_target_met=False,
                error_message=str(e),
            )

            await self._update_conflict_metrics(failed_result)

            logger.error(f"Failed to resolve conflict {conflict_id}: {e}")
            return failed_result

    async def _resolve_conflict(
        self, context: ConflictContext, detection_time_ms: float
    ) -> ResolutionResult:
        """Resolve a conflict using appropriate strategy."""
        resolution_start = time.perf_counter()

        try:
            # Select resolution strategy
            strategy = self.resolution_strategies.get(
                context.severity, ResolutionStrategy.CONSENSUS
            )

            # Execute resolution strategy
            if strategy == ResolutionStrategy.CONSENSUS:
                result = await self._resolve_with_consensus(context)
            elif strategy == ResolutionStrategy.PRIORITY_BASED:
                result = await self._resolve_with_priority(context)
            elif strategy == ResolutionStrategy.PERFORMANCE_BASED:
                result = await self._resolve_with_performance(context)
            elif strategy == ResolutionStrategy.ROUND_ROBIN:
                result = await self._resolve_with_round_robin(context)
            elif strategy == ResolutionStrategy.EMERGENCY_OVERRIDE:
                result = await self._resolve_with_emergency_override(context)
            else:
                # Default to consensus
                result = await self._resolve_with_consensus(context)

            resolution_time = (time.perf_counter() - resolution_start) * 1000
            total_time = detection_time_ms + resolution_time

            return ResolutionResult(
                conflict_id=context.conflict_id,
                success=result["success"],
                resolution=result["resolution"],
                strategy_used=strategy,
                resolution_time_ms=resolution_time,
                detection_time_ms=detection_time_ms,
                total_time_ms=total_time,
                winning_agent=result.get("winning_agent"),
                consensus_details=result.get("consensus_details"),
                performance_target_met=total_time < self.performance_target_ms,
                escalated=result.get("escalated", False),
            )

        except Exception as e:
            resolution_time = (time.perf_counter() - resolution_start) * 1000
            total_time = detection_time_ms + resolution_time

            logger.error(f"Error resolving conflict {context.conflict_id}: {e}")

            return ResolutionResult(
                conflict_id=context.conflict_id,
                success=False,
                resolution="error",
                strategy_used=strategy,
                resolution_time_ms=resolution_time,
                detection_time_ms=detection_time_ms,
                total_time_ms=total_time,
                winning_agent=None,
                consensus_details=None,
                performance_target_met=False,
                error_message=str(e),
            )

    async def _resolve_with_consensus(self, context: ConflictContext) -> Dict[str, Any]:
        """Resolve conflict using distributed consensus."""
        consensus_result = await self.consensus_engine.resolve_resource_conflict(
            conflicting_agents=context.involved_agents,
            resource=context.resource_or_decision,
            conflict_data=context.conflict_data,
        )

        return {
            "success": consensus_result.success,
            "resolution": consensus_result.resolution,
            "winning_agent": consensus_result.winning_option,
            "consensus_details": consensus_result,
        }

    async def _resolve_with_priority(self, context: ConflictContext) -> Dict[str, Any]:
        """Resolve conflict based on agent priority scores."""
        # Calculate priority scores for involved agents
        agent_scores = {}
        for agent_id in context.involved_agents:
            performance = self.agent_performance.get(agent_id, {})
            priority_score = (
                performance.get("success_rate", 0.5) * 0.4
                + (1.0 - performance.get("average_response_time", 200.0) / 1000.0) * 0.3
                + performance.get("reliability_score", 0.5) * 0.3
            )
            agent_scores[agent_id] = priority_score

        # Select highest priority agent
        winning_agent = max(agent_scores, key=agent_scores.get)

        return {
            "success": True,
            "resolution": f"priority_winner_{winning_agent}",
            "winning_agent": winning_agent,
        }

    async def _resolve_with_performance(
        self, context: ConflictContext
    ) -> Dict[str, Any]:
        """Resolve conflict based on recent performance metrics."""
        # Use performance-based selection
        best_agent = None
        best_score = 0.0

        for agent_id in context.involved_agents:
            performance = self.agent_performance.get(agent_id, {})
            performance_score = performance.get("conflict_resolution_score", 0.5)

            if performance_score > best_score:
                best_score = performance_score
                best_agent = agent_id

        return {
            "success": True,
            "resolution": f"performance_winner_{best_agent}",
            "winning_agent": best_agent or context.involved_agents[0],
        }

    async def _resolve_with_round_robin(
        self, context: ConflictContext
    ) -> Dict[str, Any]:
        """Resolve conflict using round-robin selection."""
        # Simple round-robin based on conflict count
        conflict_counts = {}
        for agent_id in context.involved_agents:
            # Count recent conflicts for this agent
            recent_conflicts = sum(
                1
                for conflict in self.conflict_history[-100:]  # Last 100 conflicts
                if agent_id in conflict.involved_agents
            )
            conflict_counts[agent_id] = recent_conflicts

        # Select agent with fewest recent conflicts
        winning_agent = min(conflict_counts, key=conflict_counts.get)

        return {
            "success": True,
            "resolution": f"round_robin_winner_{winning_agent}",
            "winning_agent": winning_agent,
        }

    async def _resolve_with_emergency_override(
        self, context: ConflictContext
    ) -> Dict[str, Any]:
        """Resolve emergency conflicts with immediate override."""
        # For emergency conflicts, use executive agent as default override
        override_agent = (
            "executive_agent"
            if "executive_agent" in context.involved_agents
            else context.involved_agents[0]
        )

        return {
            "success": True,
            "resolution": f"emergency_override_{override_agent}",
            "winning_agent": override_agent,
            "escalated": True,
        }

    def _calculate_priority_score(
        self, severity: ConflictSeverity, agents: List[str], data: Dict[str, Any]
    ) -> float:
        """Calculate priority score for conflict."""
        base_score = severity.value * 20.0  # Base score from severity

        # Add agent count factor
        agent_factor = len(agents) * 5.0

        # Add urgency factor from data
        urgency_factor = data.get("urgency", 1.0) * 10.0

        return base_score + agent_factor + urgency_factor

    def _register_default_detectors(self):
        """Register default conflict detection methods."""
        self.conflict_detectors = [
            self._detect_resource_conflicts,
            self._detect_decision_conflicts,
            self._detect_performance_conflicts,
        ]

    async def _detect_resource_conflicts(self) -> List[ConflictContext]:
        """Detect resource-based conflicts."""
        # Placeholder for resource conflict detection
        # In real implementation, this would check for resource contention
        return []

    async def _detect_decision_conflicts(self) -> List[ConflictContext]:
        """Detect decision-based conflicts."""
        # Placeholder for decision conflict detection
        # In real implementation, this would check for conflicting decisions
        return []

    async def _detect_performance_conflicts(self) -> List[ConflictContext]:
        """Detect performance-based conflicts."""
        # Placeholder for performance conflict detection
        # In real implementation, this would check for performance degradation
        return []

    async def _monitor_conflicts(self):
        """Monitor for conflicts using registered detectors."""
        logger.info("🔍 Starting conflict detection monitoring")

        while self.is_monitoring:
            try:
                await asyncio.sleep(5.0)  # Check every 5 seconds

                # Run all conflict detectors
                for detector in self.conflict_detectors:
                    try:
                        detected_conflicts = await detector()

                        # Process detected conflicts
                        for conflict in detected_conflicts:
                            if conflict.conflict_id not in self.active_conflicts:
                                logger.warning(
                                    f"🔍 Detected new conflict: {conflict.conflict_id}"
                                )
                                # Auto-resolve detected conflicts
                                await self.detect_and_resolve_conflict(
                                    conflict_type=conflict.conflict_type,
                                    involved_agents=conflict.involved_agents,
                                    resource_or_decision=conflict.resource_or_decision,
                                    conflict_data=conflict.conflict_data,
                                    severity=conflict.severity,
                                )
                    except Exception as e:
                        logger.error(f"Error in conflict detector: {e}")

            except Exception as e:
                logger.error(f"Error in conflict monitoring: {e}")

    async def _monitor_performance(self):
        """Monitor conflict resolution performance."""
        logger.info("📊 Starting conflict resolution performance monitoring")

        while self.is_monitoring:
            try:
                await asyncio.sleep(60.0)  # Report every minute

                metrics = self.conflict_metrics
                if metrics.total_conflicts > 0:
                    logger.info(
                        f"📊 Conflict Metrics: "
                        f"Total: {metrics.total_conflicts}, "
                        f"Resolved: {metrics.resolved_conflicts}, "
                        f"Failed: {metrics.failed_conflicts}, "
                        f"Avg Time: {metrics.average_resolution_time_ms:.2f}ms, "
                        f"Sub-200ms: {metrics.performance_target_met_percentage:.1f}%"
                    )

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")

    async def _cleanup_resolved_conflicts(self):
        """Clean up old resolved conflicts from history."""
        logger.info("🧹 Starting conflict cleanup monitoring")

        while self.is_monitoring:
            try:
                await asyncio.sleep(300.0)  # Clean up every 5 minutes

                # Keep only last 1000 conflicts in history
                if len(self.conflict_history) > 1000:
                    self.conflict_history = self.conflict_history[-1000:]
                    logger.info("🧹 Cleaned up old conflicts from history")

            except Exception as e:
                logger.error(f"Error in conflict cleanup: {e}")

    async def _update_conflict_metrics(self, result: ResolutionResult):
        """Update conflict resolution metrics."""
        metrics = self.conflict_metrics
        metrics.total_conflicts += 1

        if result.success:
            metrics.resolved_conflicts += 1
        else:
            metrics.failed_conflicts += 1

        if result.escalated:
            metrics.escalated_conflicts += 1

        if result.total_time_ms < 200.0:
            metrics.sub_200ms_resolutions += 1

        # Update average resolution time
        if metrics.total_conflicts > 0:
            metrics.average_resolution_time_ms = (
                metrics.average_resolution_time_ms * (metrics.total_conflicts - 1)
                + result.total_time_ms
            ) / metrics.total_conflicts

        # Update performance target percentage
        if metrics.total_conflicts > 0:
            metrics.performance_target_met_percentage = (
                metrics.sub_200ms_resolutions / metrics.total_conflicts * 100
            )

        metrics.last_updated = datetime.now(timezone.utc)

    async def get_conflict_status(self) -> Dict[str, Any]:
        """Get current conflict resolution status."""
        return {
            "resolver_id": self.resolver_id,
            "is_monitoring": self.is_monitoring,
            "performance_target_ms": self.performance_target_ms,
            "active_conflicts": len(self.active_conflicts),
            "conflict_history_size": len(self.conflict_history),
            "metrics": {
                "total_conflicts": self.conflict_metrics.total_conflicts,
                "resolved_conflicts": self.conflict_metrics.resolved_conflicts,
                "failed_conflicts": self.conflict_metrics.failed_conflicts,
                "escalated_conflicts": self.conflict_metrics.escalated_conflicts,
                "average_resolution_time_ms": self.conflict_metrics.average_resolution_time_ms,
                "sub_200ms_resolutions": self.conflict_metrics.sub_200ms_resolutions,
                "performance_target_met_percentage": self.conflict_metrics.performance_target_met_percentage,
                "last_updated": self.conflict_metrics.last_updated.isoformat(),
            },
            "resolution_strategies": {
                severity.name: strategy.value
                for severity, strategy in self.resolution_strategies.items()
            },
            "agent_performance": self.agent_performance,
        }

    async def stop_monitoring(self):
        """Stop conflict monitoring gracefully."""
        try:
            self.is_monitoring = False

            # Cancel all monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()

            # Wait for tasks to complete
            if self.monitoring_tasks:
                await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

            logger.info("✅ Phase 4 conflict monitoring stopped gracefully")

        except Exception as e:
            logger.error(f"Error stopping conflict monitoring: {e}")

    async def emergency_conflict_resolution(
        self,
        emergency_type: str,
        affected_agents: List[str],
        emergency_data: Dict[str, Any],
    ) -> ResolutionResult:
        """Handle emergency conflict resolution."""
        return await self.detect_and_resolve_conflict(
            conflict_type=ConflictType.RESOURCE_CONTENTION,
            involved_agents=affected_agents,
            resource_or_decision=f"emergency_{emergency_type}",
            conflict_data=emergency_data,
            severity=ConflictSeverity.EMERGENCY,
            deadline_ms=1000.0,  # 1 second emergency deadline
        )
