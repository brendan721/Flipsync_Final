#!/usr/bin/env python3
"""
Priority-based Decision Arbitration System
==========================================

Phase 3.2 implementation for sophisticated priority-based decision arbitration
with real-time performance monitoring and adaptive load balancing.

Features:
- Priority-based decision arbitration
- Real-time performance monitoring
- Adaptive load balancing
- Resource allocation optimization
- Decision queue management
- Performance analytics and metrics

Technical Requirements:
- Arbitration decisions <100ms
- Load balancing <200ms
- Production database integration
- Backward compatibility with existing coordination
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, field
import heapq

from fs_agt_clean.core.protocols.agent_protocol import Priority
from fs_agt_clean.core.coordination.event_system import get_event_bus, Event, EventType
from fs_agt_clean.core.db.database import get_database

logger = logging.getLogger(__name__)


class ArbitrationStrategy(Enum):
    """Strategies for decision arbitration."""

    STRICT_PRIORITY = "strict_priority"
    WEIGHTED_PRIORITY = "weighted_priority"
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    RESOURCE_AWARE = "resource_aware"
    ADAPTIVE = "adaptive"


class LoadBalancingMode(Enum):
    """Load balancing modes for agent workload distribution."""

    EQUAL_DISTRIBUTION = "equal_distribution"
    CAPABILITY_BASED = "capability_based"
    PERFORMANCE_BASED = "performance_based"
    RESOURCE_BASED = "resource_based"


@dataclass
class ArbitrationRequest:
    """Request for decision arbitration."""

    request_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    decision_type: str = ""
    priority: Priority = Priority.NORMAL
    resources_required: Set[str] = field(default_factory=set)
    estimated_duration: float = 0.0  # seconds
    deadline: Optional[datetime] = None
    request_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    arbitration_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentWorkload:
    """Tracks agent workload and performance metrics."""

    agent_id: str
    active_requests: int = 0
    total_requests_processed: int = 0
    average_processing_time: float = 0.0
    success_rate: float = 100.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    capabilities: Set[str] = field(default_factory=set)
    performance_score: float = 100.0


class PriorityBasedDecisionArbitrationSystem:
    """
    Sophisticated priority-based decision arbitration system with real-time
    performance monitoring and adaptive load balancing.
    """

    def __init__(self, db_session=None):
        """Initialize the priority arbitration system."""
        self.db_session = db_session or get_database()
        self.event_bus = get_event_bus()

        # Arbitration queues (priority heaps)
        self.arbitration_queues: Dict[
            Priority, List[Tuple[float, ArbitrationRequest]]
        ] = {
            Priority.CRITICAL: [],
            Priority.HIGH: [],
            Priority.NORMAL: [],
            Priority.LOW: [],
        }

        # Agent workload tracking
        self.agent_workloads: Dict[str, AgentWorkload] = {}
        self.resource_allocations: Dict[str, str] = {}  # resource -> agent_id

        # Performance metrics
        self.performance_metrics = {
            "requests_arbitrated": 0,
            "average_arbitration_time": 0.0,
            "load_balance_operations": 0,
            "resource_conflicts_resolved": 0,
            "queue_sizes": {priority.name: 0 for priority in Priority},
        }

        # Configuration
        self.arbitration_strategy = ArbitrationStrategy.ADAPTIVE
        self.load_balancing_mode = LoadBalancingMode.PERFORMANCE_BASED
        self.max_queue_size = 1000
        self.arbitration_interval = 0.1  # seconds
        self.load_balance_interval = 5.0  # seconds

        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()

        logger.info("PriorityBasedDecisionArbitrationSystem initialized")

    async def start(self) -> None:
        """Start the arbitration system."""
        try:
            # Start background processing tasks
            self._background_tasks.add(
                asyncio.create_task(self._arbitration_processor())
            )
            self._background_tasks.add(asyncio.create_task(self._load_balancer()))
            self._background_tasks.add(asyncio.create_task(self._performance_monitor()))

            logger.info("Priority-based decision arbitration system started")

        except Exception as e:
            logger.error(f"Failed to start arbitration system: {e}")
            raise

    async def stop(self) -> None:
        """Stop the arbitration system."""
        try:
            # Signal shutdown
            self._shutdown_event.set()

            # Cancel background tasks
            for task in self._background_tasks:
                task.cancel()

            # Wait for tasks to complete
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            logger.info("Priority-based decision arbitration system stopped")

        except Exception as e:
            logger.error(f"Error stopping arbitration system: {e}")

    async def submit_arbitration_request(self, request: ArbitrationRequest) -> str:
        """Submit a request for decision arbitration."""
        start_time = time.perf_counter()

        try:
            # Validate request
            if not request.agent_id:
                raise ValueError("Agent ID is required for arbitration request")

            # Add timestamp for queue ordering
            queue_priority = self._calculate_queue_priority(request)

            # Add to appropriate priority queue
            heapq.heappush(
                self.arbitration_queues[request.priority], (queue_priority, request)
            )

            # Update queue size metrics
            self.performance_metrics["queue_sizes"][request.priority.name] = len(
                self.arbitration_queues[request.priority]
            )

            # Initialize agent workload if needed
            if request.agent_id not in self.agent_workloads:
                self.agent_workloads[request.agent_id] = AgentWorkload(
                    agent_id=request.agent_id
                )

            elapsed_time = (time.perf_counter() - start_time) * 1000
            logger.debug(
                f"Arbitration request {request.request_id} submitted "
                f"({elapsed_time:.2f}ms)"
            )

            return request.request_id

        except Exception as e:
            logger.error(f"Failed to submit arbitration request: {e}")
            raise

    async def register_agent_capabilities(
        self, agent_id: str, capabilities: Set[str]
    ) -> None:
        """Register agent capabilities for load balancing."""
        try:
            if agent_id not in self.agent_workloads:
                self.agent_workloads[agent_id] = AgentWorkload(agent_id=agent_id)

            self.agent_workloads[agent_id].capabilities = capabilities

            logger.debug(
                f"Registered capabilities for agent {agent_id}: {capabilities}"
            )

        except Exception as e:
            logger.error(f"Failed to register agent capabilities: {e}")

    async def update_agent_performance(
        self, agent_id: str, processing_time: float, success: bool
    ) -> None:
        """Update agent performance metrics."""
        try:
            if agent_id not in self.agent_workloads:
                return

            workload = self.agent_workloads[agent_id]

            # Update processing time (moving average)
            if workload.total_requests_processed > 0:
                workload.average_processing_time = (
                    workload.average_processing_time * 0.9 + processing_time * 0.1
                )
            else:
                workload.average_processing_time = processing_time

            # Update success rate
            total_requests = workload.total_requests_processed + 1
            current_successes = (
                workload.success_rate * workload.total_requests_processed / 100
            )
            new_successes = current_successes + (1 if success else 0)
            workload.success_rate = (new_successes / total_requests) * 100

            # Update counters
            workload.total_requests_processed += 1
            workload.last_activity = datetime.now(timezone.utc)

            # Calculate performance score
            workload.performance_score = self._calculate_performance_score(workload)

            logger.debug(
                f"Updated performance for agent {agent_id}: "
                f"score={workload.performance_score:.1f}"
            )

        except Exception as e:
            logger.error(f"Failed to update agent performance: {e}")

    async def get_arbitration_status(self) -> Dict[str, Any]:
        """Get current arbitration system status."""
        return {
            "arbitration_strategy": self.arbitration_strategy.value,
            "load_balancing_mode": self.load_balancing_mode.value,
            "queue_sizes": self.performance_metrics["queue_sizes"].copy(),
            "total_queued_requests": sum(
                len(queue) for queue in self.arbitration_queues.values()
            ),
            "active_agents": len(self.agent_workloads),
            "performance_metrics": self.performance_metrics.copy(),
            "resource_allocations": len(self.resource_allocations),
        }

    def _calculate_queue_priority(self, request: ArbitrationRequest) -> float:
        """Calculate queue priority for request ordering."""
        # Base priority from request priority level
        base_priority = request.priority.value * 1000

        # Add deadline urgency
        if request.deadline:
            time_to_deadline = (
                request.deadline - datetime.now(timezone.utc)
            ).total_seconds()
            urgency_factor = max(0, 1000 - time_to_deadline)
            base_priority += urgency_factor

        # Add timestamp for FIFO within same priority
        timestamp_factor = request.request_time.timestamp()

        return base_priority + timestamp_factor

    def _calculate_performance_score(self, workload: AgentWorkload) -> float:
        """Calculate agent performance score for load balancing."""
        # Base score from success rate
        score = workload.success_rate

        # Adjust for processing speed (lower time = higher score)
        if workload.average_processing_time > 0:
            speed_factor = min(100, 1000 / workload.average_processing_time)
            score = (score + speed_factor) / 2

        # Adjust for current load (lower load = higher score)
        load_factor = max(0, 100 - workload.active_requests * 10)
        score = (score + load_factor) / 2

        return min(100, max(0, score))

    # Background processing methods

    async def _arbitration_processor(self) -> None:
        """Process arbitration requests from priority queues."""
        while not self._shutdown_event.is_set():
            try:
                start_time = time.perf_counter()
                requests_processed = 0

                # Process requests in priority order
                for priority in [
                    Priority.CRITICAL,
                    Priority.HIGH,
                    Priority.NORMAL,
                    Priority.LOW,
                ]:
                    queue = self.arbitration_queues[priority]

                    while queue and not self._shutdown_event.is_set():
                        # Get highest priority request
                        _, request = heapq.heappop(queue)

                        # Process the arbitration request
                        success = await self._process_arbitration_request(request)

                        if success:
                            requests_processed += 1
                            self.performance_metrics["requests_arbitrated"] += 1

                        # Update queue size metrics
                        self.performance_metrics["queue_sizes"][priority.name] = len(
                            queue
                        )

                        # Break if we've processed enough for this cycle
                        if requests_processed >= 10:  # Process max 10 per cycle
                            break

                    if requests_processed >= 10:
                        break

                # Update performance metrics
                if requests_processed > 0:
                    processing_time = (time.perf_counter() - start_time) * 1000
                    self.performance_metrics["average_arbitration_time"] = (
                        self.performance_metrics["average_arbitration_time"] * 0.9
                        + processing_time * 0.1
                    )

                    logger.debug(
                        f"Processed {requests_processed} arbitration requests "
                        f"({processing_time:.2f}ms)"
                    )

                # Wait before next processing cycle
                await asyncio.sleep(self.arbitration_interval)

            except Exception as e:
                logger.error(f"Arbitration processor error: {e}")
                await asyncio.sleep(1.0)

    async def _process_arbitration_request(self, request: ArbitrationRequest) -> bool:
        """Process a single arbitration request."""
        try:
            # Select best agent for the request
            selected_agent = await self._select_agent_for_request(request)

            if not selected_agent:
                # No suitable agent available, requeue the request
                heapq.heappush(
                    self.arbitration_queues[request.priority],
                    (self._calculate_queue_priority(request), request),
                )
                return False

            # Allocate resources
            await self._allocate_resources(request, selected_agent)

            # Update agent workload
            if selected_agent in self.agent_workloads:
                self.agent_workloads[selected_agent].active_requests += 1

            # Publish arbitration result
            await self._publish_arbitration_result(request, selected_agent)

            return True

        except Exception as e:
            logger.error(
                f"Error processing arbitration request {request.request_id}: {e}"
            )
            return False

    async def _select_agent_for_request(
        self, request: ArbitrationRequest
    ) -> Optional[str]:
        """Select the best agent for a request based on current strategy."""
        try:
            if self.arbitration_strategy == ArbitrationStrategy.STRICT_PRIORITY:
                return await self._select_by_strict_priority(request)
            elif self.arbitration_strategy == ArbitrationStrategy.WEIGHTED_PRIORITY:
                return await self._select_by_weighted_priority(request)
            elif self.arbitration_strategy == ArbitrationStrategy.LOAD_BALANCED:
                return await self._select_by_load_balance(request)
            elif self.arbitration_strategy == ArbitrationStrategy.RESOURCE_AWARE:
                return await self._select_by_resource_availability(request)
            elif self.arbitration_strategy == ArbitrationStrategy.ADAPTIVE:
                return await self._select_by_adaptive_strategy(request)
            else:
                return await self._select_by_round_robin(request)

        except Exception as e:
            logger.error(f"Error selecting agent for request: {e}")
            return None

    async def _select_by_strict_priority(
        self, request: ArbitrationRequest
    ) -> Optional[str]:
        """Select agent based on strict priority (requesting agent gets priority)."""
        if request.agent_id in self.agent_workloads:
            workload = self.agent_workloads[request.agent_id]
            if workload.active_requests < 5:  # Max concurrent requests
                return request.agent_id
        return None

    async def _select_by_load_balance(
        self, request: ArbitrationRequest
    ) -> Optional[str]:
        """Select agent based on current load balancing."""
        best_agent = None
        lowest_load = float("inf")

        for agent_id, workload in self.agent_workloads.items():
            # Check if agent has required capabilities
            if request.arbitration_data.get("required_capabilities"):
                required_caps = set(request.arbitration_data["required_capabilities"])
                if not required_caps.issubset(workload.capabilities):
                    continue

            # Calculate load score (lower is better)
            load_score = workload.active_requests + (
                1 / max(0.1, workload.performance_score)
            )

            if load_score < lowest_load:
                lowest_load = load_score
                best_agent = agent_id

        return best_agent

    async def _select_by_adaptive_strategy(
        self, request: ArbitrationRequest
    ) -> Optional[str]:
        """Select agent using adaptive strategy based on system state."""
        # Use load balancing for high-load situations
        total_active_requests = sum(
            w.active_requests for w in self.agent_workloads.values()
        )

        if total_active_requests > len(self.agent_workloads) * 3:
            return await self._select_by_load_balance(request)
        else:
            return await self._select_by_weighted_priority(request)

    async def _select_by_weighted_priority(
        self, request: ArbitrationRequest
    ) -> Optional[str]:
        """Select agent based on weighted priority considering performance."""
        best_agent = None
        best_score = -1

        for agent_id, workload in self.agent_workloads.items():
            # Calculate weighted score
            priority_weight = 1.0 if agent_id == request.agent_id else 0.5
            performance_weight = workload.performance_score / 100
            load_weight = max(0, 1 - workload.active_requests / 10)

            total_score = priority_weight * performance_weight * load_weight

            if total_score > best_score:
                best_score = total_score
                best_agent = agent_id

        return best_agent

    async def _select_by_resource_availability(
        self, request: ArbitrationRequest
    ) -> Optional[str]:
        """Select agent based on resource availability."""
        for agent_id, workload in self.agent_workloads.items():
            # Check if agent can handle the required resources
            resource_conflicts = False
            for resource in request.resources_required:
                if resource in self.resource_allocations:
                    if self.resource_allocations[resource] != agent_id:
                        resource_conflicts = True
                        break

            if not resource_conflicts and workload.active_requests < 5:
                return agent_id

        return None

    async def _select_by_round_robin(
        self, request: ArbitrationRequest
    ) -> Optional[str]:
        """Select agent using round-robin strategy."""
        if not self.agent_workloads:
            return None

        # Simple round-robin based on total requests processed
        agent_list = list(self.agent_workloads.keys())
        total_requests = sum(
            w.total_requests_processed for w in self.agent_workloads.values()
        )
        selected_index = total_requests % len(agent_list)

        return agent_list[selected_index]

    async def _allocate_resources(
        self, request: ArbitrationRequest, agent_id: str
    ) -> None:
        """Allocate resources to the selected agent."""
        try:
            for resource in request.resources_required:
                self.resource_allocations[resource] = agent_id

            logger.debug(
                f"Allocated {len(request.resources_required)} resources to agent {agent_id}"
            )

        except Exception as e:
            logger.error(f"Error allocating resources: {e}")

    async def _publish_arbitration_result(
        self, request: ArbitrationRequest, selected_agent: str
    ) -> None:
        """Publish the arbitration result."""
        try:
            event = Event(
                event_type=EventType.NOTIFICATION,
                source="priority_arbitration",
                target=selected_agent,
                data={
                    "request_id": request.request_id,
                    "agent_id": selected_agent,
                    "decision_type": request.decision_type,
                    "priority": request.priority.name,
                    "resources_allocated": list(request.resources_required),
                    "arbitration_strategy": self.arbitration_strategy.value,
                },
            )
            await self.event_bus.publish(event)

        except Exception as e:
            logger.error(f"Error publishing arbitration result: {e}")

    async def _load_balancer(self) -> None:
        """Monitor and balance load across agents."""
        while not self._shutdown_event.is_set():
            try:
                start_time = time.perf_counter()

                # Analyze current load distribution
                load_analysis = await self._analyze_load_distribution()

                # Perform load balancing if needed
                if load_analysis["needs_balancing"]:
                    await self._perform_load_balancing(load_analysis)
                    self.performance_metrics["load_balance_operations"] += 1

                # Update arbitration strategy if needed
                await self._update_arbitration_strategy(load_analysis)

                elapsed_time = (time.perf_counter() - start_time) * 1000
                logger.debug(f"Load balancing cycle completed ({elapsed_time:.2f}ms)")

                # Wait before next load balancing cycle
                await asyncio.sleep(self.load_balance_interval)

            except Exception as e:
                logger.error(f"Load balancer error: {e}")
                await asyncio.sleep(5.0)

    async def _performance_monitor(self) -> None:
        """Monitor system performance and update metrics."""
        while not self._shutdown_event.is_set():
            try:
                # Update agent performance scores
                for agent_id, workload in self.agent_workloads.items():
                    workload.performance_score = self._calculate_performance_score(
                        workload
                    )

                # Clean up inactive agents
                await self._cleanup_inactive_agents()

                # Log performance metrics periodically
                logger.debug(f"Arbitration system metrics: {self.performance_metrics}")

                # Wait before next monitoring cycle
                await asyncio.sleep(30.0)  # Monitor every 30 seconds

            except Exception as e:
                logger.error(f"Performance monitor error: {e}")
                await asyncio.sleep(10.0)

    async def _analyze_load_distribution(self) -> Dict[str, Any]:
        """Analyze current load distribution across agents."""
        if not self.agent_workloads:
            return {"needs_balancing": False, "reason": "no_agents"}

        # Calculate load statistics
        loads = [w.active_requests for w in self.agent_workloads.values()]
        avg_load = sum(loads) / len(loads)
        max_load = max(loads)
        min_load = min(loads)
        load_variance = max_load - min_load

        # Determine if balancing is needed
        needs_balancing = (
            load_variance > 3  # High variance in load
            or max_load > avg_load * 2  # One agent heavily overloaded
            or any(
                w.performance_score < 50 for w in self.agent_workloads.values()
            )  # Poor performance
        )

        return {
            "needs_balancing": needs_balancing,
            "avg_load": avg_load,
            "max_load": max_load,
            "min_load": min_load,
            "load_variance": load_variance,
            "total_agents": len(self.agent_workloads),
            "overloaded_agents": [
                agent_id
                for agent_id, w in self.agent_workloads.items()
                if w.active_requests > avg_load * 1.5
            ],
            "underloaded_agents": [
                agent_id
                for agent_id, w in self.agent_workloads.items()
                if w.active_requests < avg_load * 0.5
            ],
        }

    async def _perform_load_balancing(self, analysis: Dict[str, Any]) -> None:
        """Perform load balancing based on analysis."""
        try:
            overloaded_agents = analysis["overloaded_agents"]
            underloaded_agents = analysis["underloaded_agents"]

            if not overloaded_agents or not underloaded_agents:
                return

            # Redistribute some requests from overloaded to underloaded agents
            for overloaded_agent in overloaded_agents:
                workload = self.agent_workloads[overloaded_agent]

                # Calculate how many requests to redistribute
                excess_requests = max(
                    0, workload.active_requests - analysis["avg_load"]
                )
                requests_to_move = min(
                    excess_requests, 2
                )  # Move max 2 requests at a time

                if requests_to_move > 0:
                    # Find best underloaded agent
                    best_target = min(
                        underloaded_agents,
                        key=lambda agent_id: self.agent_workloads[
                            agent_id
                        ].active_requests,
                    )

                    # Simulate request redistribution (in real implementation,
                    # this would involve actual request migration)
                    self.agent_workloads[
                        overloaded_agent
                    ].active_requests -= requests_to_move
                    self.agent_workloads[
                        best_target
                    ].active_requests += requests_to_move

                    logger.info(
                        f"Load balanced: moved {requests_to_move} requests from "
                        f"{overloaded_agent} to {best_target}"
                    )

        except Exception as e:
            logger.error(f"Error performing load balancing: {e}")

    async def _update_arbitration_strategy(self, analysis: Dict[str, Any]) -> None:
        """Update arbitration strategy based on system state."""
        try:
            # Switch to load balancing if system is under high load
            if analysis["max_load"] > 8:
                if self.arbitration_strategy != ArbitrationStrategy.LOAD_BALANCED:
                    self.arbitration_strategy = ArbitrationStrategy.LOAD_BALANCED
                    logger.info("Switched to load-balanced arbitration strategy")

            # Switch to adaptive strategy for normal load
            elif analysis["load_variance"] > 2:
                if self.arbitration_strategy != ArbitrationStrategy.ADAPTIVE:
                    self.arbitration_strategy = ArbitrationStrategy.ADAPTIVE
                    logger.info("Switched to adaptive arbitration strategy")

            # Switch to weighted priority for low load
            else:
                if self.arbitration_strategy != ArbitrationStrategy.WEIGHTED_PRIORITY:
                    self.arbitration_strategy = ArbitrationStrategy.WEIGHTED_PRIORITY
                    logger.info("Switched to weighted priority arbitration strategy")

        except Exception as e:
            logger.error(f"Error updating arbitration strategy: {e}")

    async def _cleanup_inactive_agents(self) -> None:
        """Clean up agents that have been inactive for too long."""
        try:
            current_time = datetime.now(timezone.utc)
            inactive_threshold = timedelta(minutes=10)

            agents_to_remove = []
            for agent_id, workload in self.agent_workloads.items():
                if (current_time - workload.last_activity) > inactive_threshold:
                    if workload.active_requests == 0:
                        agents_to_remove.append(agent_id)

            for agent_id in agents_to_remove:
                del self.agent_workloads[agent_id]
                logger.info(f"Cleaned up inactive agent: {agent_id}")

        except Exception as e:
            logger.error(f"Error cleaning up inactive agents: {e}")
