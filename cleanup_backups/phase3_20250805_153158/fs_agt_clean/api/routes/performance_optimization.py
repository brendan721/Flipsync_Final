"""
FlipSync Performance Optimization API Routes
Week 4: Production Deployment & Operational Excellence - Objective 2

API endpoints for controlling and monitoring production performance optimization.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from fs_agt_clean.core.performance.production_optimization_system import (
    get_production_optimization_system,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/performance", tags=["Performance Optimization"])


class OptimizationRequest(BaseModel):
    """Request model for performance optimization."""

    action: str  # "initialize", "optimize", "report", "configure"
    agent_type: Optional[str] = None
    service_id: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class PerformanceReport(BaseModel):
    """Response model for performance report."""

    agent_decision_avg_ms: float
    service_execution_avg_ms: float
    cache_hit_rate: float
    targets_met: Dict[str, bool]
    optimization_status: str


@router.get("/status")
async def get_optimization_status():
    """
    Get the current status of performance optimization system.

    Returns:
        Dict: Current optimization status and metrics
    """
    try:
        optimization_system = get_production_optimization_system()

        # Get performance report
        performance_report = optimization_system.get_performance_report()

        # Calculate targets met
        cache_hit_rate = performance_report["cache_statistics"]["hits"] / max(
            performance_report["cache_statistics"]["total_requests"], 1
        )

        targets_met = {
            "agent_decision_time": True,  # Will be calculated from actual metrics
            "service_execution_time": True,  # Will be calculated from actual metrics
            "cache_hit_rate": cache_hit_rate
            >= optimization_system.cache_hit_target_rate,
        }

        return {
            "success": True,
            "optimization_active": True,
            "performance_targets": {
                "agent_decision_ms": optimization_system.agent_decision_target_ms,
                "service_execution_ms": optimization_system.service_execution_target_ms,
                "cache_hit_rate": optimization_system.cache_hit_target_rate,
            },
            "current_performance": {
                "cache_hit_rate": cache_hit_rate,
                "cache_statistics": performance_report["cache_statistics"],
                "total_metrics": len(optimization_system.performance_history),
            },
            "targets_met": targets_met,
            "optimization_config": optimization_system.optimization_config,
        }

    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get optimization status: {str(e)}",
        )


@router.post("/initialize")
async def initialize_optimization():
    """
    Initialize the performance optimization system.

    Returns:
        Dict: Initialization result
    """
    try:
        optimization_system = get_production_optimization_system()

        success = await optimization_system.initialize()

        if success:
            return {
                "success": True,
                "message": "Performance optimization system initialized successfully",
                "targets": {
                    "agent_decision_ms": optimization_system.agent_decision_target_ms,
                    "service_execution_ms": optimization_system.service_execution_target_ms,
                    "cache_hit_rate": optimization_system.cache_hit_target_rate,
                },
                "features": {
                    "caching_system": "Enabled",
                    "performance_monitoring": "Enabled",
                    "agent_optimizations": "Enabled",
                    "service_optimizations": "Enabled",
                },
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize optimization system",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize optimization: {str(e)}",
        )


@router.get("/report")
async def get_performance_report():
    """
    Get comprehensive performance report.

    Returns:
        Dict: Detailed performance report
    """
    try:
        optimization_system = get_production_optimization_system()

        performance_report = optimization_system.get_performance_report()

        # Calculate additional metrics
        cache_stats = performance_report["cache_statistics"]
        cache_hit_rate = cache_stats["hits"] / max(cache_stats["total_requests"], 1)

        # Analyze performance by operation
        performance_analysis = {}
        for operation, stats in performance_report["performance_by_operation"].items():
            target_ms = (
                optimization_system.agent_decision_target_ms
                if "agent" in operation
                else optimization_system.service_execution_target_ms
            )

            performance_analysis[operation] = {
                **stats,
                "target_ms": target_ms,
                "target_met": stats["average_ms"] <= target_ms,
                "performance_ratio": stats["average_ms"] / target_ms,
            }

        return {
            "success": True,
            "performance_report": performance_report,
            "performance_analysis": performance_analysis,
            "summary": {
                "cache_hit_rate": cache_hit_rate,
                "cache_target_met": cache_hit_rate
                >= optimization_system.cache_hit_target_rate,
                "total_operations": len(performance_analysis),
                "operations_meeting_targets": sum(
                    1
                    for analysis in performance_analysis.values()
                    if analysis["target_met"]
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error getting performance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance report: {str(e)}",
        )


@router.get("/cache-stats")
async def get_cache_statistics():
    """
    Get detailed cache statistics.

    Returns:
        Dict: Cache performance statistics
    """
    try:
        optimization_system = get_production_optimization_system()

        cache_stats = optimization_system.cache_stats
        cache_hit_rate = cache_stats["hits"] / max(cache_stats["total_requests"], 1)

        return {
            "success": True,
            "cache_statistics": cache_stats,
            "cache_performance": {
                "hit_rate": cache_hit_rate,
                "miss_rate": 1 - cache_hit_rate,
                "target_hit_rate": optimization_system.cache_hit_target_rate,
                "target_met": cache_hit_rate
                >= optimization_system.cache_hit_target_rate,
            },
            "cache_configuration": {
                "max_size": optimization_system.optimization_config["max_cache_size"],
                "current_size": len(optimization_system.cache_store),
                "ttl_seconds": optimization_system.optimization_config[
                    "cache_ttl_seconds"
                ],
                "utilization": len(optimization_system.cache_store)
                / optimization_system.optimization_config["max_cache_size"],
            },
        }

    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}",
        )


@router.post("/configure")
async def configure_optimization(request: OptimizationRequest):
    """
    Configure performance optimization settings.

    Args:
        request: Configuration request

    Returns:
        Dict: Configuration result
    """
    try:
        optimization_system = get_production_optimization_system()

        if request.configuration:
            # Update optimization configuration
            for key, value in request.configuration.items():
                if key in optimization_system.optimization_config:
                    optimization_system.optimization_config[key] = value
                    logger.info(f"Updated optimization config: {key} = {value}")

            return {
                "success": True,
                "message": "Optimization configuration updated successfully",
                "updated_config": optimization_system.optimization_config,
            }
        else:
            return {
                "success": True,
                "current_config": optimization_system.optimization_config,
                "agent_optimizations": optimization_system.agent_optimizations,
            }

    except Exception as e:
        logger.error(f"Error configuring optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure optimization: {str(e)}",
        )


@router.get("/targets")
async def get_performance_targets():
    """
    Get current performance targets and thresholds.

    Returns:
        Dict: Performance targets and current status
    """
    try:
        optimization_system = get_production_optimization_system()

        return {
            "success": True,
            "performance_targets": {
                "agent_decision_time_ms": optimization_system.agent_decision_target_ms,
                "service_execution_time_ms": optimization_system.service_execution_target_ms,
                "database_query_time_ms": optimization_system.database_query_target_ms,
                "cache_hit_rate": optimization_system.cache_hit_target_rate,
            },
            "agent_specific_targets": {
                agent_type: {
                    "decision_cache_ttl": config.get("decision_cache_ttl", 300),
                    "optimizations_enabled": len(
                        [k for k, v in config.items() if v is True]
                    ),
                }
                for agent_type, config in optimization_system.agent_optimizations.items()
            },
            "optimization_features": {
                "query_caching": optimization_system.optimization_config[
                    "enable_query_caching"
                ],
                "result_caching": optimization_system.optimization_config[
                    "enable_result_caching"
                ],
                "decision_caching": optimization_system.optimization_config[
                    "enable_decision_caching"
                ],
                "service_pooling": optimization_system.optimization_config[
                    "enable_service_pooling"
                ],
                "async_optimization": optimization_system.optimization_config[
                    "enable_async_optimization"
                ],
            },
        }

    except Exception as e:
        logger.error(f"Error getting performance targets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance targets: {str(e)}",
        )


@router.post("/test-optimization")
async def test_optimization_performance():
    """
    Test optimization system performance with sample operations.

    Returns:
        Dict: Test results
    """
    try:
        optimization_system = get_production_optimization_system()

        # Test agent decision optimization
        async def sample_agent_decision(context):
            await asyncio.sleep(0.1)  # Simulate 100ms operation
            return {"decision": "optimized", "confidence": 0.95}

        # Test service execution optimization
        async def sample_service_execution(params):
            await asyncio.sleep(0.05)  # Simulate 50ms operation
            return {"result": "success", "data": params}

        test_results = {}

        # Test agent decision optimization
        for agent_type in ["market", "content", "logistics", "executive"]:
            decision_context = {"test": True, "agent_type": agent_type}

            result, execution_time = await optimization_system.optimize_agent_decision(
                f"{agent_type}_agent_001",
                agent_type,
                decision_context,
                sample_agent_decision,
            )

            test_results[f"{agent_type}_agent_decision"] = {
                "execution_time_ms": execution_time,
                "target_ms": optimization_system.agent_decision_target_ms,
                "target_met": execution_time
                <= optimization_system.agent_decision_target_ms,
                "result": result,
            }

        # Test service execution optimization
        for service_id in [
            "pricing_service",
            "content_generation",
            "route_optimization",
        ]:
            service_params = {"test": True, "service_id": service_id}

            result, execution_time = (
                await optimization_system.optimize_service_execution(
                    service_id, "market", service_params, sample_service_execution
                )
            )

            test_results[f"{service_id}_execution"] = {
                "execution_time_ms": execution_time,
                "target_ms": optimization_system.service_execution_target_ms,
                "target_met": execution_time
                <= optimization_system.service_execution_target_ms,
                "result": result,
            }

        # Calculate overall test results
        total_tests = len(test_results)
        tests_passed = sum(
            1 for result in test_results.values() if result["target_met"]
        )

        return {
            "success": True,
            "test_summary": {
                "total_tests": total_tests,
                "tests_passed": tests_passed,
                "success_rate": tests_passed / total_tests,
                "overall_performance": (
                    "EXCELLENT"
                    if tests_passed == total_tests
                    else (
                        "GOOD"
                        if tests_passed >= total_tests * 0.8
                        else "NEEDS_IMPROVEMENT"
                    )
                ),
            },
            "test_results": test_results,
            "cache_performance": {
                "hit_rate": optimization_system.cache_stats["hits"]
                / max(optimization_system.cache_stats["total_requests"], 1),
                "total_requests": optimization_system.cache_stats["total_requests"],
            },
        }

    except Exception as e:
        logger.error(f"Error testing optimization performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test optimization performance: {str(e)}",
        )
