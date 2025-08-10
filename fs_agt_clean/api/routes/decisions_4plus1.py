"""
FlipSync 4+1 Architecture Decision Tracking API
==============================================

Pure 4+1 architecture implementation for decision tracking and analytics.
This module provides REST API endpoints exclusively using the new database schema:
- autonomous_agent_decisions table for decision tracking
- Real-time decision monitoring with LLM-free compliance
- Decision analytics and performance metrics

Phase 3.1.2: Decision Tracking APIs Migration
- All endpoints use autonomous_agent_decisions table exclusively
- LLM-free compliance reporting and validation
- Real-time decision monitoring capabilities
- Decision analytics with 4+1 architecture focus

Key Features:
- Decision history and audit trails from database
- LLM-free compliance tracking and reporting
- Performance analytics with <1000ms decision time validation
- Real-time decision streaming via WebSocket
- Cross-agent decision coordination insights

Security:
- JWT-based authentication for sensitive operations
- Rate limiting and request validation
- Secure decision data access

Performance:
- <500ms API response times
- Efficient database queries with proper indexing
- Real-time decision event streaming
- Optimized analytics calculations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse

# Import 4+1 architecture database components
from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.database.repositories.autonomous_agent_repository import (
    AutonomousAgentRepository,
)
from fs_agt_clean.database.models.autonomous_agent import (
    AutonomousAgent,
    AutonomousAgentDecision,
)
from fs_agt_clean.core.architecture.boundaries import (
    ArchitecturalBoundaries,
    ArchitecturalLayer,
)

# Import authentication dependencies
from fs_agt_clean.api.dependencies.dependencies import get_current_user_optional
from fs_agt_clean.core.models.user import UnifiedUserResponse

# Configure logging
logger = logging.getLogger(__name__)

# Create router without prefix (prefix will be added in main.py)
router = APIRouter(tags=["4+1-architecture-decisions"])

# Database and repository instances
database = get_database()
autonomous_agent_repository = AutonomousAgentRepository()


@router.get("/")
async def get_all_decisions(
    limit: int = Query(
        50, ge=1, le=1000, description="Number of decisions to retrieve"
    ),
    offset: int = Query(0, ge=0, description="Number of decisions to skip"),
    agent_id: Optional[str] = Query(None, description="Filter by specific agent ID"),
    decision_type: Optional[str] = Query(None, description="Filter by decision type"),
    status: Optional[str] = Query(None, description="Filter by decision status"),
    llm_free_only: bool = Query(False, description="Show only LLM-free decisions"),
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Get all decisions from 4+1 architecture database with filtering and pagination.

    Returns data exclusively from autonomous_agent_decisions table.
    Includes LLM-free compliance indicators and performance metrics.
    """
    try:
        logger.info(
            f"🔍 Fetching decisions from 4+1 architecture database (limit={limit}, offset={offset})"
        )

        async with database.get_session() as session:
            # Get decisions with filters
            decisions = await autonomous_agent_repository.get_decisions_with_filters(
                session=session,
                limit=limit,
                offset=offset,
                agent_id=agent_id,
                decision_type=decision_type,
                status=status,
                llm_free_only=llm_free_only,
            )

            # Get total count for pagination
            total_count = await autonomous_agent_repository.get_decisions_count(
                session=session,
                agent_id=agent_id,
                decision_type=decision_type,
                status=status,
                llm_free_only=llm_free_only,
            )

            # Calculate compliance metrics
            compliance_metrics = await _calculate_compliance_metrics(decisions)

            # Format decisions for API response
            formatted_decisions = []
            for decision in decisions:
                formatted_decision = {
                    "id": decision.id,
                    "decision_id": decision.decision_id,
                    "agent_id": decision.agent_id,
                    "decision_type": decision.decision_type,
                    "status": decision.status,
                    "execution_time_ms": decision.execution_time_ms,
                    "confidence": decision.confidence,
                    "context": json.loads(decision.context) if decision.context else {},
                    "result": json.loads(decision.result) if decision.result else {},
                    # 4+1 Architecture Compliance Indicators
                    "compliance": {
                        "used_llm": decision.used_llm,
                        "used_standard_pipeline": decision.used_standard_pipeline,
                        "algorithm_used": decision.algorithm_used,
                        "llm_free_compliant": not decision.used_llm,
                        "pipeline_compliant": decision.used_standard_pipeline,
                    },
                    "performance": {
                        "meets_1000ms_target": (
                            decision.execution_time_ms < 1000
                            if decision.execution_time_ms
                            else False
                        ),
                        "confidence_level": (
                            "high"
                            if decision.confidence > 0.8
                            else "medium" if decision.confidence > 0.5 else "low"
                        ),
                    },
                    "timestamps": {
                        "started_at": (
                            decision.started_at.isoformat()
                            if decision.started_at
                            else None
                        ),
                        "completed_at": (
                            decision.completed_at.isoformat()
                            if decision.completed_at
                            else None
                        ),
                        "created_at": decision.created_at.isoformat(),
                    },
                }
                formatted_decisions.append(formatted_decision)

            return {
                "decisions": formatted_decisions,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count,
                },
                "filters_applied": {
                    "agent_id": agent_id,
                    "decision_type": decision_type,
                    "status": status,
                    "llm_free_only": llm_free_only,
                },
                "compliance_metrics": compliance_metrics,
                "database_info": {
                    "source": "autonomous_agent_decisions table",
                    "legacy_free": True,
                    "architecture": "4+1",
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as e:
        logger.error(f"❌ Error fetching decisions from 4+1 architecture database: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve decisions: {str(e)}"
        )


@router.get("/analytics")
async def get_decision_analytics(
    time_range_hours: int = Query(
        24, ge=1, le=168, description="Time range in hours for analytics"
    ),
    agent_id: Optional[str] = Query(
        None, description="Filter analytics by specific agent"
    ),
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Get comprehensive decision analytics from 4+1 architecture database.

    Provides detailed analytics including:
    - LLM-free compliance rates
    - Performance metrics and trends
    - Decision type distribution
    - Agent-specific analytics
    """
    try:
        logger.info(
            f"📊 Generating decision analytics for {time_range_hours}h from 4+1 architecture database"
        )

        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_range_hours)

        async with database.get_session() as session:
            # Get decisions within time range
            decisions = await autonomous_agent_repository.get_decisions_in_time_range(
                session=session,
                start_time=start_time,
                end_time=end_time,
                agent_id=agent_id,
            )

            if not decisions:
                return {
                    "message": "No decisions found in specified time range",
                    "time_range": {
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "hours": time_range_hours,
                    },
                    "analytics": {
                        "total_decisions": 0,
                        "compliance_rate": 0.0,
                        "avg_execution_time": 0.0,
                    },
                }

            # Generate comprehensive analytics
            analytics = await _generate_comprehensive_analytics(
                decisions, time_range_hours
            )

            return {
                "analytics": analytics,
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "hours": time_range_hours,
                },
                "filters": {
                    "agent_id": agent_id,
                },
                "database_info": {
                    "source": "autonomous_agent_decisions table",
                    "legacy_free": True,
                    "architecture": "4+1",
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as e:
        logger.error(f"❌ Error generating decision analytics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate analytics: {str(e)}"
        )


@router.get("/compliance")
async def get_compliance_report(
    time_range_hours: int = Query(
        24, ge=1, le=168, description="Time range in hours for compliance report"
    ),
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Get 4+1 architecture compliance report.

    Provides detailed compliance analysis including:
    - LLM-free compliance rates by agent
    - StandardDecisionPipeline usage rates
    - Performance target compliance (<1000ms)
    - Compliance violations and trends
    """
    try:
        logger.info(
            f"📋 Generating 4+1 architecture compliance report for {time_range_hours}h"
        )

        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_range_hours)

        async with database.get_session() as session:
            # Get all decisions within time range
            decisions = await autonomous_agent_repository.get_decisions_in_time_range(
                session=session,
                start_time=start_time,
                end_time=end_time,
            )

            # Generate compliance report
            compliance_report = await _generate_compliance_report(decisions)

            return {
                "compliance_report": compliance_report,
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "hours": time_range_hours,
                },
                "architecture_requirements": {
                    "llm_free_required": True,
                    "standard_pipeline_required": True,
                    "max_decision_time_ms": 1000,
                    "architecture_type": "4+1",
                },
                "database_info": {
                    "source": "autonomous_agent_decisions table",
                    "legacy_free": True,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as e:
        logger.error(f"❌ Error generating compliance report: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate compliance report: {str(e)}"
        )


@router.get("/{decision_id}")
async def get_decision_details(
    decision_id: str = Path(..., description="Decision ID to retrieve details for"),
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Get detailed information for a specific decision from 4+1 architecture database.

    Includes:
    - Complete decision context and results
    - LLM-free compliance validation
    - Performance metrics and analysis
    - Related agent information
    """
    try:
        logger.info(
            f"🔍 Getting details for decision {decision_id} from 4+1 architecture database"
        )

        async with database.get_session() as session:
            # Get decision from database
            decision = await autonomous_agent_repository.get_decision_by_id(
                session, decision_id
            )

            if not decision:
                raise HTTPException(
                    status_code=404,
                    detail=f"Decision {decision_id} not found in 4+1 architecture database",
                )

            # Get related agent information
            agent = await autonomous_agent_repository.get_autonomous_agent(
                session, decision.agent_id
            )

            # Parse context and result
            try:
                context = json.loads(decision.context) if decision.context else {}
                result = json.loads(decision.result) if decision.result else {}
            except json.JSONDecodeError:
                context = {"raw": decision.context}
                result = {"raw": decision.result}

            # Build detailed decision response
            decision_details = {
                "id": decision.id,
                "decision_id": decision.decision_id,
                "agent_info": {
                    "agent_id": decision.agent_id,
                    "agent_name": agent.agent_type if agent else "Unknown",
                    "agent_type": agent.agent_type if agent else "Unknown",
                    "architecture_layer": ArchitecturalBoundaries.validate_agent_type(
                        decision.agent_id
                    ).value,
                },
                "decision_details": {
                    "decision_type": decision.decision_type,
                    "status": decision.status,
                    "context": context,
                    "result": result,
                    "confidence": decision.confidence,
                },
                "performance_metrics": {
                    "execution_time_ms": decision.execution_time_ms,
                    "meets_1000ms_target": (
                        decision.execution_time_ms < 1000
                        if decision.execution_time_ms
                        else False
                    ),
                    "confidence_level": (
                        "high"
                        if decision.confidence > 0.8
                        else "medium" if decision.confidence > 0.5 else "low"
                    ),
                    "performance_grade": _calculate_performance_grade(decision),
                },
                "compliance_validation": {
                    "used_llm": decision.used_llm,
                    "used_standard_pipeline": decision.used_standard_pipeline,
                    "algorithm_used": decision.algorithm_used,
                    "llm_free_compliant": not decision.used_llm,
                    "pipeline_compliant": decision.used_standard_pipeline,
                    "fully_compliant": not decision.used_llm
                    and decision.used_standard_pipeline,
                    "compliance_score": _calculate_compliance_score(decision),
                },
                "timestamps": {
                    "started_at": (
                        decision.started_at.isoformat() if decision.started_at else None
                    ),
                    "completed_at": (
                        decision.completed_at.isoformat()
                        if decision.completed_at
                        else None
                    ),
                    "created_at": decision.created_at.isoformat(),
                    "duration_ms": (
                        (decision.completed_at - decision.started_at).total_seconds()
                        * 1000
                        if decision.started_at and decision.completed_at
                        else None
                    ),
                },
                "database_metadata": {
                    "table_source": "autonomous_agent_decisions",
                    "legacy_free": True,
                    "architecture": "4+1",
                },
            }

            return decision_details

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting decision details for {decision_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve decision details: {str(e)}"
        )


# Helper functions


async def _calculate_compliance_metrics(
    decisions: List[AutonomousAgentDecision],
) -> Dict[str, Any]:
    """Calculate compliance metrics from decision list."""
    if not decisions:
        return {
            "total_decisions": 0,
            "llm_free_rate": 0.0,
            "standard_pipeline_rate": 0.0,
            "performance_target_rate": 0.0,
        }

    total = len(decisions)
    llm_free_count = sum(1 for d in decisions if not d.used_llm)
    standard_pipeline_count = sum(1 for d in decisions if d.used_standard_pipeline)
    performance_target_count = sum(
        1 for d in decisions if d.execution_time_ms and d.execution_time_ms < 1000
    )

    return {
        "total_decisions": total,
        "llm_free_rate": round(llm_free_count / total, 3),
        "standard_pipeline_rate": round(standard_pipeline_count / total, 3),
        "performance_target_rate": round(performance_target_count / total, 3),
        "fully_compliant_rate": round(
            sum(1 for d in decisions if not d.used_llm and d.used_standard_pipeline)
            / total,
            3,
        ),
    }


async def _generate_comprehensive_analytics(
    decisions: List[AutonomousAgentDecision], time_range_hours: int
) -> Dict[str, Any]:
    """Generate comprehensive analytics from decision data."""
    if not decisions:
        return {"total_decisions": 0}

    # Basic metrics
    total_decisions = len(decisions)
    successful_decisions = sum(1 for d in decisions if d.status == "completed")

    # Performance metrics
    execution_times = [d.execution_time_ms for d in decisions if d.execution_time_ms]
    avg_execution_time = (
        sum(execution_times) / len(execution_times) if execution_times else 0.0
    )

    # Compliance metrics
    llm_free_count = sum(1 for d in decisions if not d.used_llm)
    standard_pipeline_count = sum(1 for d in decisions if d.used_standard_pipeline)

    # Decision type analysis
    decision_types = {}
    for decision in decisions:
        decision_type = decision.decision_type
        if decision_type not in decision_types:
            decision_types[decision_type] = {
                "count": 0,
                "avg_time": 0.0,
                "success_rate": 0.0,
            }
        decision_types[decision_type]["count"] += 1

    # Calculate averages for each decision type
    for decision_type, stats in decision_types.items():
        type_decisions = [d for d in decisions if d.decision_type == decision_type]
        type_times = [
            d.execution_time_ms for d in type_decisions if d.execution_time_ms
        ]
        successful_type = sum(1 for d in type_decisions if d.status == "completed")

        stats["avg_time"] = (
            round(sum(type_times) / len(type_times), 1) if type_times else 0.0
        )
        stats["success_rate"] = (
            round(successful_type / len(type_decisions), 3) if type_decisions else 0.0
        )

    # Agent performance breakdown
    agent_performance = {}
    for decision in decisions:
        agent_id = decision.agent_id
        if agent_id not in agent_performance:
            agent_performance[agent_id] = {
                "decisions": 0,
                "avg_time": 0.0,
                "success_rate": 0.0,
                "llm_free_rate": 0.0,
            }
        agent_performance[agent_id]["decisions"] += 1

    # Calculate agent-specific metrics
    for agent_id, stats in agent_performance.items():
        agent_decisions = [d for d in decisions if d.agent_id == agent_id]
        agent_times = [
            d.execution_time_ms for d in agent_decisions if d.execution_time_ms
        ]
        successful_agent = sum(1 for d in agent_decisions if d.status == "completed")
        llm_free_agent = sum(1 for d in agent_decisions if not d.used_llm)

        stats["avg_time"] = (
            round(sum(agent_times) / len(agent_times), 1) if agent_times else 0.0
        )
        stats["success_rate"] = (
            round(successful_agent / len(agent_decisions), 3)
            if agent_decisions
            else 0.0
        )
        stats["llm_free_rate"] = (
            round(llm_free_agent / len(agent_decisions), 3) if agent_decisions else 0.0
        )

    return {
        "summary": {
            "total_decisions": total_decisions,
            "successful_decisions": successful_decisions,
            "success_rate": round(successful_decisions / total_decisions, 3),
            "avg_execution_time_ms": round(avg_execution_time, 1),
            "decisions_per_hour": round(total_decisions / time_range_hours, 1),
        },
        "compliance_metrics": {
            "llm_free_rate": round(llm_free_count / total_decisions, 3),
            "standard_pipeline_rate": round(
                standard_pipeline_count / total_decisions, 3
            ),
            "performance_target_rate": (
                round(
                    sum(1 for t in execution_times if t < 1000) / len(execution_times),
                    3,
                )
                if execution_times
                else 0.0
            ),
            "fully_compliant_decisions": sum(
                1 for d in decisions if not d.used_llm and d.used_standard_pipeline
            ),
        },
        "decision_types": decision_types,
        "agent_performance": agent_performance,
        "performance_distribution": (
            {
                "under_500ms": sum(1 for t in execution_times if t < 500),
                "500ms_to_1000ms": sum(1 for t in execution_times if 500 <= t < 1000),
                "over_1000ms": sum(1 for t in execution_times if t >= 1000),
            }
            if execution_times
            else {}
        ),
    }


async def _generate_compliance_report(
    decisions: List[AutonomousAgentDecision],
) -> Dict[str, Any]:
    """Generate detailed compliance report."""
    if not decisions:
        return {"total_decisions": 0, "compliance_status": "no_data"}

    total_decisions = len(decisions)

    # Overall compliance metrics
    llm_free_count = sum(1 for d in decisions if not d.used_llm)
    standard_pipeline_count = sum(1 for d in decisions if d.used_standard_pipeline)
    performance_compliant_count = sum(
        1 for d in decisions if d.execution_time_ms and d.execution_time_ms < 1000
    )

    # Compliance violations
    llm_violations = [d for d in decisions if d.used_llm]
    pipeline_violations = [d for d in decisions if not d.used_standard_pipeline]
    performance_violations = [
        d for d in decisions if d.execution_time_ms and d.execution_time_ms >= 1000
    ]

    # Agent-specific compliance
    agent_compliance = {}
    for decision in decisions:
        agent_id = decision.agent_id
        if agent_id not in agent_compliance:
            agent_compliance[agent_id] = {
                "total_decisions": 0,
                "llm_free_count": 0,
                "standard_pipeline_count": 0,
                "performance_compliant_count": 0,
                "violations": [],
            }

        stats = agent_compliance[agent_id]
        stats["total_decisions"] += 1

        if not decision.used_llm:
            stats["llm_free_count"] += 1
        else:
            stats["violations"].append(f"LLM used in decision {decision.decision_id}")

        if decision.used_standard_pipeline:
            stats["standard_pipeline_count"] += 1
        else:
            stats["violations"].append(
                f"Non-standard pipeline in decision {decision.decision_id}"
            )

        if decision.execution_time_ms and decision.execution_time_ms < 1000:
            stats["performance_compliant_count"] += 1
        elif decision.execution_time_ms:
            stats["violations"].append(
                f"Slow decision {decision.decision_id}: {decision.execution_time_ms}ms"
            )

    # Calculate compliance rates for each agent
    for agent_id, stats in agent_compliance.items():
        total = stats["total_decisions"]
        stats["llm_free_rate"] = (
            round(stats["llm_free_count"] / total, 3) if total > 0 else 0.0
        )
        stats["standard_pipeline_rate"] = (
            round(stats["standard_pipeline_count"] / total, 3) if total > 0 else 0.0
        )
        stats["performance_compliance_rate"] = (
            round(stats["performance_compliant_count"] / total, 3) if total > 0 else 0.0
        )
        stats["overall_compliance_rate"] = (
            round(
                (
                    stats["llm_free_count"]
                    + stats["standard_pipeline_count"]
                    + stats["performance_compliant_count"]
                )
                / (total * 3),
                3,
            )
            if total > 0
            else 0.0
        )

    # Overall compliance status
    overall_llm_free_rate = llm_free_count / total_decisions
    overall_pipeline_rate = standard_pipeline_count / total_decisions
    overall_performance_rate = performance_compliant_count / total_decisions

    if (
        overall_llm_free_rate >= 0.95
        and overall_pipeline_rate >= 0.95
        and overall_performance_rate >= 0.90
    ):
        compliance_status = "excellent"
    elif (
        overall_llm_free_rate >= 0.90
        and overall_pipeline_rate >= 0.90
        and overall_performance_rate >= 0.80
    ):
        compliance_status = "good"
    elif overall_llm_free_rate >= 0.80 and overall_pipeline_rate >= 0.80:
        compliance_status = "acceptable"
    else:
        compliance_status = "needs_improvement"

    return {
        "overall_compliance": {
            "total_decisions": total_decisions,
            "llm_free_rate": round(overall_llm_free_rate, 3),
            "standard_pipeline_rate": round(overall_pipeline_rate, 3),
            "performance_compliance_rate": round(overall_performance_rate, 3),
            "compliance_status": compliance_status,
        },
        "violations_summary": {
            "llm_violations": len(llm_violations),
            "pipeline_violations": len(pipeline_violations),
            "performance_violations": len(performance_violations),
            "total_violations": len(llm_violations)
            + len(pipeline_violations)
            + len(performance_violations),
        },
        "agent_compliance": agent_compliance,
        "recommendations": _generate_compliance_recommendations(
            overall_llm_free_rate, overall_pipeline_rate, overall_performance_rate
        ),
    }


def _calculate_performance_grade(decision: AutonomousAgentDecision) -> str:
    """Calculate performance grade for a decision."""
    score = 0

    # LLM-free compliance (40% weight)
    if not decision.used_llm:
        score += 40

    # Standard pipeline usage (30% weight)
    if decision.used_standard_pipeline:
        score += 30

    # Performance target (30% weight)
    if decision.execution_time_ms and decision.execution_time_ms < 1000:
        if decision.execution_time_ms < 500:
            score += 30  # Excellent performance
        elif decision.execution_time_ms < 750:
            score += 25  # Good performance
        else:
            score += 20  # Acceptable performance

    # Convert score to grade
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _calculate_compliance_score(decision: AutonomousAgentDecision) -> float:
    """Calculate compliance score (0.0 to 1.0) for a decision."""
    score = 0.0

    # LLM-free compliance (50% weight)
    if not decision.used_llm:
        score += 0.5

    # Standard pipeline usage (30% weight)
    if decision.used_standard_pipeline:
        score += 0.3

    # Performance target (20% weight)
    if decision.execution_time_ms and decision.execution_time_ms < 1000:
        score += 0.2

    return round(score, 3)


def _generate_compliance_recommendations(
    llm_free_rate: float, pipeline_rate: float, performance_rate: float
) -> List[str]:
    """Generate compliance improvement recommendations."""
    recommendations = []

    if llm_free_rate < 0.95:
        recommendations.append(
            f"LLM-free compliance is {llm_free_rate:.1%}. Ensure all autonomous agents use StandardDecisionPipeline without LLM dependencies."
        )

    if pipeline_rate < 0.95:
        recommendations.append(
            f"Standard pipeline usage is {pipeline_rate:.1%}. Verify all agents are properly configured to use StandardDecisionPipeline."
        )

    if performance_rate < 0.90:
        recommendations.append(
            f"Performance target compliance is {performance_rate:.1%}. Optimize decision algorithms to meet <1000ms target."
        )

    if not recommendations:
        recommendations.append(
            "Excellent compliance! All 4+1 architecture requirements are being met."
        )

    return recommendations


# WebSocket endpoints for real-time decision monitoring


async def authenticate_websocket_decisions(websocket: WebSocket) -> bool:
    """
    Authenticate WebSocket connection for decisions endpoints.

    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        # Check for token in query parameters
        token = websocket.query_params.get("token")

        # Check for token in headers if not in query params
        if not token:
            token = websocket.headers.get("Authorization")
            if token and token.startswith("Bearer "):
                token = token[7:]  # Remove "Bearer " prefix

        if not token:
            logger.warning(
                "🔒 Decisions WebSocket authentication failed: No token provided"
            )
            return False

        # PRODUCTION FIX: Use proper JWT validation with consistent secret logic
        from fs_agt_clean.core.websocket.mobile_auth_fix import _validate_jwt_token

        if _validate_jwt_token(token):
            logger.info(
                "🔒 Decisions WebSocket authentication successful with valid JWT"
            )
            return True
        else:
            logger.warning(
                "🔒 Decisions WebSocket authentication failed: Invalid JWT token"
            )
            return False

    except Exception as e:
        logger.error(f"🔒 Decisions WebSocket authentication error: {e}")
        return False


@router.websocket("/ws/live")
async def websocket_live_decisions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time decision monitoring across all agents.

    Security: Requires authentication token in query params (?token=...) or Authorization header.

    Streams live decision events including:
    - New decision starts and completions
    - LLM-free compliance status
    - Performance metrics updates
    - 4+1 architecture compliance alerts
    """
    # ✅ PHASE 3.2.2: WebSocket Authentication
    if not await authenticate_websocket_decisions(websocket):
        await websocket.close(code=1008, reason="Authentication required")
        return

    await websocket.accept()
    logger.info(
        "🔌 WebSocket connection established for live decision monitoring (authenticated)"
    )

    try:
        last_decision_count = 0

        while True:
            async with database.get_session() as session:
                # Get recent decisions across all agents
                recent_decisions = (
                    await autonomous_agent_repository.get_recent_decisions(
                        session, limit=20
                    )
                )

                current_decision_count = len(recent_decisions)

                # Send update if there are new decisions or initial connection
                if (
                    current_decision_count != last_decision_count
                    or last_decision_count == 0
                ):
                    # Calculate real-time metrics
                    compliance_metrics = await _calculate_compliance_metrics(
                        recent_decisions
                    )

                    # Format decisions for WebSocket
                    formatted_decisions = []
                    for decision in recent_decisions[:10]:  # Send last 10 decisions
                        formatted_decisions.append(
                            {
                                "decision_id": decision.decision_id,
                                "agent_id": decision.agent_id,
                                "decision_type": decision.decision_type,
                                "status": decision.status,
                                "execution_time_ms": decision.execution_time_ms,
                                "confidence": decision.confidence,
                                "used_llm": decision.used_llm,
                                "used_standard_pipeline": decision.used_standard_pipeline,
                                "algorithm_used": decision.algorithm_used,
                                "started_at": (
                                    decision.started_at.isoformat()
                                    if decision.started_at
                                    else None
                                ),
                                "completed_at": (
                                    decision.completed_at.isoformat()
                                    if decision.completed_at
                                    else None
                                ),
                                "compliance_score": _calculate_compliance_score(
                                    decision
                                ),
                                "performance_grade": _calculate_performance_grade(
                                    decision
                                ),
                            }
                        )

                    websocket_data = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "recent_decisions": formatted_decisions,
                        "live_metrics": {
                            "total_decisions": current_decision_count,
                            "new_decisions": current_decision_count
                            - last_decision_count,
                            **compliance_metrics,
                        },
                        "websocket_info": {
                            "connection_type": "live_decisions",
                            "data_source": "autonomous_agent_decisions table",
                            "update_frequency": "real-time",
                            "legacy_free": True,
                        },
                    }

                    await websocket.send_json(websocket_data)
                    last_decision_count = current_decision_count

            await asyncio.sleep(3)  # Check for new decisions every 3 seconds

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket connection closed for live decision monitoring")
    except Exception as e:
        logger.error(f"❌ WebSocket error in live decision monitoring: {e}")
        await websocket.close()


@router.websocket("/ws/compliance")
async def websocket_compliance_monitoring(websocket: WebSocket):
    """
    WebSocket endpoint for real-time 4+1 architecture compliance monitoring.

    Security: Requires authentication token in query params (?token=...) or Authorization header.

    Streams compliance updates including:
    - LLM-free compliance rate changes
    - Performance target violations
    - Architecture compliance alerts
    - Compliance trend analysis
    """
    # ✅ PHASE 3.2.2: WebSocket Authentication
    if not await authenticate_websocket_decisions(websocket):
        await websocket.close(code=1008, reason="Authentication required")
        return

    await websocket.accept()
    logger.info(
        "🔌 WebSocket connection established for compliance monitoring (authenticated)"
    )

    try:
        last_compliance_data = None

        while True:
            async with database.get_session() as session:
                # Get recent decisions for compliance analysis
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=1)  # Last hour

                recent_decisions = (
                    await autonomous_agent_repository.get_decisions_in_time_range(
                        session, start_time, end_time
                    )
                )

                if recent_decisions:
                    # Generate compliance report
                    compliance_report = await _generate_compliance_report(
                        recent_decisions
                    )

                    # Check for compliance changes
                    current_compliance_data = {
                        "llm_free_rate": compliance_report["overall_compliance"][
                            "llm_free_rate"
                        ],
                        "standard_pipeline_rate": compliance_report[
                            "overall_compliance"
                        ]["standard_pipeline_rate"],
                        "performance_compliance_rate": compliance_report[
                            "overall_compliance"
                        ]["performance_compliance_rate"],
                        "compliance_status": compliance_report["overall_compliance"][
                            "compliance_status"
                        ],
                    }

                    # Send update if compliance data changed or initial connection
                    if current_compliance_data != last_compliance_data:
                        # Detect compliance alerts
                        alerts = []
                        if current_compliance_data["llm_free_rate"] < 0.90:
                            alerts.append(
                                {
                                    "type": "llm_compliance_warning",
                                    "message": f"LLM-free compliance dropped to {current_compliance_data['llm_free_rate']:.1%}",
                                    "severity": (
                                        "high"
                                        if current_compliance_data["llm_free_rate"]
                                        < 0.80
                                        else "medium"
                                    ),
                                }
                            )

                        if (
                            current_compliance_data["performance_compliance_rate"]
                            < 0.80
                        ):
                            alerts.append(
                                {
                                    "type": "performance_warning",
                                    "message": f"Performance compliance dropped to {current_compliance_data['performance_compliance_rate']:.1%}",
                                    "severity": "medium",
                                }
                            )

                        websocket_data = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "compliance_status": current_compliance_data,
                            "compliance_report": compliance_report,
                            "alerts": alerts,
                            "trends": (
                                {
                                    "improving": last_compliance_data
                                    and (
                                        current_compliance_data["llm_free_rate"]
                                        > last_compliance_data["llm_free_rate"]
                                    ),
                                    "degrading": last_compliance_data
                                    and (
                                        current_compliance_data["llm_free_rate"]
                                        < last_compliance_data["llm_free_rate"]
                                    ),
                                }
                                if last_compliance_data
                                else {"improving": False, "degrading": False}
                            ),
                            "websocket_info": {
                                "connection_type": "compliance_monitoring",
                                "data_source": "autonomous_agent_decisions table",
                                "monitoring_window_hours": 1,
                                "legacy_free": True,
                            },
                        }

                        await websocket.send_json(websocket_data)
                        last_compliance_data = current_compliance_data

            await asyncio.sleep(10)  # Check compliance every 10 seconds

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket connection closed for compliance monitoring")
    except Exception as e:
        logger.error(f"❌ WebSocket error in compliance monitoring: {e}")
        await websocket.close()


# Health check endpoint
@router.get("/health")
async def decisions_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for 4+1 architecture decision tracking system.

    Validates:
    - Database connectivity to autonomous_agent_decisions table
    - Recent decision activity
    - Compliance status
    - System operational status
    """
    try:
        async with database.get_session() as session:
            # Test database connectivity and get recent decisions
            recent_decisions = await autonomous_agent_repository.get_recent_decisions(
                session, limit=10
            )

            # Calculate basic health metrics
            if recent_decisions:
                compliance_metrics = await _calculate_compliance_metrics(
                    recent_decisions
                )
                avg_execution_time = sum(
                    d.execution_time_ms for d in recent_decisions if d.execution_time_ms
                ) / len([d for d in recent_decisions if d.execution_time_ms])

                health_status = (
                    "healthy"
                    if (
                        compliance_metrics["llm_free_rate"] >= 0.90
                        and avg_execution_time < 1000
                    )
                    else "degraded"
                )
            else:
                health_status = "no_activity"
                compliance_metrics = {"llm_free_rate": 0.0, "total_decisions": 0}
                avg_execution_time = 0.0

            return {
                "status": health_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database": {
                    "connected": True,
                    "table": "autonomous_agent_decisions",
                    "recent_decisions": len(recent_decisions),
                    "legacy_free": True,
                },
                "compliance_health": {
                    "llm_free_rate": compliance_metrics.get("llm_free_rate", 0.0),
                    "avg_execution_time_ms": round(avg_execution_time, 1),
                    "meets_performance_target": avg_execution_time < 1000,
                },
                "architecture": {
                    "type": "4+1",
                    "decision_tracking": "operational",
                    "compliance_monitoring": "active",
                },
            }

    except Exception as e:
        logger.error(f"❌ Decision tracking health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "database": {
                "connected": False,
                "error": "Database connectivity failed",
            },
        }
