"""
FlipSync 4+1 Architecture Agent Task Assignment API
==================================================

This module provides API endpoints for assigning real tasks to autonomous agents
and triggering actual decision-making processes.

Key Features:
- Direct task assignment to specific agents
- Real agent decision triggering
- Performance metrics tracking
- Task execution monitoring
- Cross-agent coordination support

API Endpoints:
- POST /agents/tasks/assign - Assign task to specific agent
- POST /agents/tasks/trigger - Trigger agent decision-making
- GET /agents/tasks/status - Get task execution status
- GET /agents/tasks/metrics - Get agent performance metrics
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import cache service
from fs_agt_clean.core.caching.agent_cache_service import agent_cache_service

# Import 4+1 architecture components
from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.database.repositories.autonomous_agent_repository import (
    AutonomousAgentRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/tasks", tags=["Agent Tasks"])


# Request/Response Models
class AgentTaskRequest(BaseModel):
    """Request model for agent task assignment."""

    agent_id: str
    task_type: str
    context: Dict[str, Any]
    priority: Optional[str] = "normal"
    timeout_seconds: Optional[int] = 30


class AgentTaskResponse(BaseModel):
    """Response model for agent task execution."""

    success: bool
    task_id: str
    agent_id: str
    execution_time_ms: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cached: Optional[bool] = False


class AgentTriggerRequest(BaseModel):
    """Request model for agent decision triggering."""

    agent_id: str
    decision_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class AgentMetricsResponse(BaseModel):
    """Response model for agent performance metrics."""

    agent_id: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    avg_execution_time_ms: float
    success_rate: float
    last_activity: Optional[str] = None


@router.post("/assign", response_model=AgentTaskResponse)
async def assign_agent_task(request: AgentTaskRequest):
    """
    Assign a real task to a specific autonomous agent.

    This endpoint triggers actual agent decision-making and updates
    performance metrics with real execution data.
    """
    try:
        # Get the showcase system to access real agent instances
        from fs_agt_clean.core.realtime.agent_showcase_system import (
            get_agent_showcase_system,
        )

        showcase_system = get_agent_showcase_system()

        # Initialize showcase system if not already done
        if showcase_system.agent_manager is None:
            logger.info(
                f"Initializing agent system for task assignment: {request.agent_id}"
            )
            success = await showcase_system.initialize()
            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to initialize agent system"
                )

        # Get the agent manager
        agent_manager = showcase_system.agent_manager

        # Map agent IDs to agent manager keys
        agent_key_mapping = {
            "market_autonomous_agent": "market_agent",
            "content_autonomous_agent": "content_agent",
            "executive_autonomous_agent": "executive_agent",
            "logistics_autonomous_agent": "logistics_agent",
        }

        agent_key = agent_key_mapping.get(request.agent_id)
        if not agent_key:
            raise HTTPException(
                status_code=400, detail=f"Unknown agent ID: {request.agent_id}"
            )

        # Get the real agent instance
        agent_instance = None
        if hasattr(agent_manager, "autonomous_agents"):
            agent_info = agent_manager.autonomous_agents.get(agent_key)
            if agent_info:
                agent_instance = agent_info.get("instance")

        if not agent_instance:
            raise HTTPException(
                status_code=404, detail=f"Agent instance not found for {agent_key}"
            )

        # Generate task ID
        task_id = str(uuid4())

        # Initialize cache service if not already done
        if agent_cache_service.redis_pool is None:
            await agent_cache_service.initialize()

        # Check cache first for Content and Market agents
        cache_parameters = request.context.copy() if request.context else {}
        cache_parameters["task_type"] = request.task_type

        # Remove timestamp and task_source to make cache key consistent
        cache_parameters.pop("timestamp", None)
        cache_parameters.pop("task_source", None)

        cached_result = await agent_cache_service.get_cached_decision(
            request.agent_id, request.task_type, cache_parameters
        )

        if cached_result:
            logger.info(
                f"🎯 Returning cached result for {request.agent_id}:{request.task_type}"
            )
            return AgentTaskResponse(
                success=cached_result["success"],
                task_id=task_id,
                agent_id=request.agent_id,
                execution_time_ms=cached_result["execution_time_ms"],
                result=cached_result["result"],
                cached=True,
            )

        # Execute the task
        start_time = time.perf_counter()

        try:
            # Use the agent's decision-making capability
            if hasattr(agent_instance, "make_decision"):
                result = await agent_instance.make_decision(
                    decision_type=request.task_type, context=request.context
                )
            elif hasattr(agent_instance, "make_autonomous_decision"):
                result = await agent_instance.make_autonomous_decision(request.context)
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Agent {request.agent_id} does not support decision-making",
                )

            execution_time = (time.perf_counter() - start_time) * 1000

            logger.info(
                f"✅ Task {task_id} completed for agent {request.agent_id} in {execution_time:.2f}ms"
            )

            # Cache the successful result for Content and Market agents
            if result and isinstance(result, dict):
                await agent_cache_service.cache_decision(
                    request.agent_id, request.task_type, cache_parameters, result
                )

            return AgentTaskResponse(
                success=True,
                task_id=task_id,
                agent_id=request.agent_id,
                execution_time_ms=execution_time,
                result=result,
                cached=False,
            )

        except asyncio.TimeoutError:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.warning(
                f"⏰ Task {task_id} timed out for agent {request.agent_id} after {execution_time:.2f}ms"
            )

            return AgentTaskResponse(
                success=False,
                task_id=task_id,
                agent_id=request.agent_id,
                execution_time_ms=execution_time,
                error="Task execution timed out",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign task to agent {request.agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Task assignment failed: {str(e)}")


@router.post("/trigger", response_model=AgentTaskResponse)
async def trigger_agent_decision(request: AgentTriggerRequest):
    """
    Trigger a decision-making process for a specific agent.

    This is a simplified interface for triggering agent decisions
    with predefined contexts based on agent type.
    """
    try:
        # Create appropriate context based on agent type and parameters
        context = await _create_agent_context(
            request.agent_id, request.parameters or {}
        )

        # Create task request
        task_request = AgentTaskRequest(
            agent_id=request.agent_id,
            task_type=request.decision_type or context["decision_type"],
            context=context["context"],
        )

        # Execute the task
        return await assign_agent_task(task_request)

    except Exception as e:
        logger.error(f"Failed to trigger agent {request.agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Agent trigger failed: {str(e)}")


@router.get("/metrics/{agent_id}", response_model=AgentMetricsResponse)
async def get_agent_metrics(agent_id: str):
    """
    Get performance metrics for a specific agent.

    Returns real metrics calculated from actual decision records.
    """
    try:
        database = get_database()
        agent_repo = AutonomousAgentRepository()  # Fixed: No parameters needed

        async with database.get_session() as session:
            # Get agent decisions for metrics calculation
            decisions = await agent_repo.get_agent_decisions(session, agent_id)

            if not decisions:
                return AgentMetricsResponse(
                    agent_id=agent_id,
                    total_tasks=0,
                    successful_tasks=0,
                    failed_tasks=0,
                    avg_execution_time_ms=0.0,
                    success_rate=0.0,
                )

            # Calculate metrics from real data
            total_tasks = len(decisions)
            successful_tasks = sum(1 for d in decisions if d.status == "completed")
            failed_tasks = total_tasks - successful_tasks

            # Calculate average execution time from real decision records
            execution_times = [
                d.execution_time_ms
                for d in decisions
                if d.execution_time_ms is not None
            ]
            avg_execution_time = (
                sum(execution_times) / len(execution_times) if execution_times else 0.0
            )

            success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0

            # Get last activity
            last_activity = None
            if decisions:
                last_decision = max(decisions, key=lambda d: d.created_at)
                last_activity = last_decision.created_at.isoformat()

            return AgentMetricsResponse(
                agent_id=agent_id,
                total_tasks=total_tasks,
                successful_tasks=successful_tasks,
                failed_tasks=failed_tasks,
                avg_execution_time_ms=avg_execution_time,
                success_rate=success_rate,
                last_activity=last_activity,
            )

    except Exception as e:
        logger.error(f"Failed to get metrics for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve agent metrics: {str(e)}"
        )


async def _create_agent_context(
    agent_id: str, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Create appropriate context for agent decision-making."""

    # Map agent IDs to types
    agent_type_mapping = {
        "market_autonomous_agent": "market",
        "content_autonomous_agent": "content",
        "executive_autonomous_agent": "executive",
        "logistics_autonomous_agent": "logistics",
    }

    agent_type = agent_type_mapping.get(agent_id, "unknown")

    # Context templates for different agent types
    context_templates = {
        "market": {
            "decision_type": "pricing_optimization",
            "context": {
                "product_id": parameters.get(
                    "product_id", f"TASK_PRODUCT_{int(time.time())}"
                ),
                "current_price": parameters.get("current_price", 29.99),
                "competitor_prices": parameters.get(
                    "competitor_prices", [27.99, 31.99, 28.49]
                ),
                "market_conditions": parameters.get("market_conditions", "competitive"),
                "inventory_level": parameters.get("inventory_level", "medium"),
                "task_source": "api_trigger",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        "content": {
            "decision_type": "content_optimization",
            "context": {
                "product_title": parameters.get(
                    "product_title", "Sample Product for Optimization"
                ),
                "category": parameters.get("category", "Electronics"),
                "target_keywords": parameters.get(
                    "target_keywords", ["product", "optimization", "test"]
                ),
                "optimization_type": parameters.get(
                    "optimization_type", "seo_enhancement"
                ),
                "task_source": "api_trigger",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        "executive": {
            "decision_type": "strategic_planning",
            "context": {
                "planning_horizon": parameters.get("planning_horizon", "quarterly"),
                "focus_area": parameters.get("focus_area", "performance_optimization"),
                "market_data": parameters.get(
                    "market_data", {"trend": "stable", "competition": "moderate"}
                ),
                "resource_constraints": parameters.get(
                    "resource_constraints", {"budget": 5000, "time": "14_days"}
                ),
                "task_source": "api_trigger",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        "logistics": {
            "decision_type": "shipping_optimization",
            "context": {
                "shipment_count": parameters.get("shipment_count", 8),
                "destination_zones": parameters.get(
                    "destination_zones", ["Zone2", "Zone4"]
                ),
                "package_weights": parameters.get("package_weights", [1.5, 3.0, 0.9]),
                "delivery_priority": parameters.get("delivery_priority", "standard"),
                "cost_optimization": parameters.get("cost_optimization", True),
                "task_source": "api_trigger",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    }

    return context_templates.get(
        agent_type,
        {
            "decision_type": "general_task",
            "context": {
                "task": parameters.get("task", "general_processing"),
                "task_source": "api_trigger",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


@router.get("/cache/stats")
async def get_cache_statistics():
    """
    Get comprehensive cache performance statistics.

    Returns cache hit rates, memory usage, and agent-specific metrics.
    """
    try:
        # Initialize cache service if not already done
        if agent_cache_service.redis_pool is None:
            await agent_cache_service.initialize()

        cache_stats = await agent_cache_service.get_cache_stats()

        return {
            "success": True,
            "cache_statistics": cache_stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Cache stats retrieval failed: {str(e)}"
        )


@router.post("/cache/invalidate/{agent_id}")
async def invalidate_agent_cache(agent_id: str):
    """
    Invalidate all cached decisions for a specific agent.

    Useful for forcing fresh decisions or after agent updates.
    """
    try:
        # Initialize cache service if not already done
        if agent_cache_service.redis_pool is None:
            await agent_cache_service.initialize()

        deleted_count = await agent_cache_service.invalidate_agent_cache(agent_id)

        return {
            "success": True,
            "agent_id": agent_id,
            "invalidated_entries": deleted_count,
            "message": f"Invalidated {deleted_count} cache entries for {agent_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to invalidate cache for {agent_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Cache invalidation failed: {str(e)}"
        )
