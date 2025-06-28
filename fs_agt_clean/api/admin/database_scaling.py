"""
Database Scaling API

This module provides API endpoints for managing database scaling, including:
1. Getting scaling status
2. Configuring scaling parameters
3. Manual scaling operations
4. Monitoring database metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from fs_agt_clean.core.db.load_balancer import LoadBalancingStrategy
from fs_agt_clean.core.db.scaling_config import (
    DatabaseScalingConfig,
    ReplicaConfig,
    ScalingAction,
    ScalingMode,
)
from fs_agt_clean.core.db.scaling_init import (
    DatabaseScalingSystem,
    get_database_scaling_system,
    initialize_database_scaling,
)
from fs_agt_clean.core.security.access_control import (
    UnifiedUserSession,
    get_current_user_session,
)
from fs_agt_clean.core.utils.logging import get_logger
from fs_agt_clean.services.metrics.service import MetricsService, get_metrics_service
from fs_agt_clean.services.notifications.service import (
    NotificationService,
    get_notification_service,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin/database/scaling",
    tags=["admin", "database", "scaling"],
    responses={404: {"description": "Not found"}},
)


# Models for API requests and responses
class ScalingStatusResponse(BaseModel):
    """Response model for scaling status."""

    is_running: bool = Field(..., description="Whether the scaling system is running")
    metrics: Dict[str, Dict[str, float]] = Field(
        ..., description="Current database metrics"
    )
    scaling_status: Dict[str, Union[str, int, bool]] = Field(
        ..., description="Scaling status"
    )
    replicas: Dict[str, Dict[str, any]] = Field(..., description="Replica status")
    config: Dict[str, any] = Field(..., description="Scaling configuration")


class ScalingConfigUpdateRequest(BaseModel):
    """Request model for updating scaling configuration."""

    enabled: Optional[bool] = Field(None, description="Whether scaling is enabled")
    mode: Optional[ScalingMode] = Field(None, description="Scaling mode")
    min_pool_size: Optional[int] = Field(
        None, description="Minimum connection pool size"
    )
    max_pool_size: Optional[int] = Field(
        None, description="Maximum connection pool size"
    )
    min_replicas: Optional[int] = Field(None, description="Minimum number of replicas")
    max_replicas: Optional[int] = Field(None, description="Maximum number of replicas")
    load_balancing_strategy: Optional[LoadBalancingStrategy] = Field(
        None, description="Load balancing strategy"
    )


class ManualScalingRequest(BaseModel):
    """Request model for manual scaling operations."""

    action: ScalingAction = Field(..., description="Scaling action to perform")
    pool_size: Optional[int] = Field(None, description="New connection pool size")


class ReplicaConfigRequest(BaseModel):
    """Request model for replica configuration."""

    host: str = Field(..., description="Hostname or IP address")
    port: int = Field(5432, description="Port number")
    username: str = Field(..., description="UnifiedUsername for connection")
    password: str = Field(..., description="Password for connection")
    database: str = Field(..., description="Database name")
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Maximum connection overflow")
    weight: int = Field(1, description="Weight for load balancing")


class MetricsResponse(BaseModel):
    """Response model for database metrics."""

    metrics: Dict[str, List[Dict[str, Union[str, float]]]] = Field(
        ..., description="Database metrics history"
    )


# Dependencies
async def get_scaling_system(
    metrics_service: MetricsService = Depends(get_metrics_service),
    notification_service: NotificationService = Depends(get_notification_service),
    user_session: UnifiedUserSession = Depends(get_current_user_session),
) -> DatabaseScalingSystem:
    """
    Get the database scaling system.

    Args:
        metrics_service: Metrics service
        notification_service: Notification service
        user_session: UnifiedUser session

    Returns:
        The database scaling system
    """
    # Check if user has admin role
    if "admin" not in user_session.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    # Get or initialize scaling system
    scaling_system = get_database_scaling_system()

    if not scaling_system:
        scaling_system = await initialize_database_scaling(
            metrics_service=metrics_service,
            notification_service=notification_service,
        )

    return scaling_system


# API endpoints
@router.get("/status", response_model=ScalingStatusResponse)
async def get_scaling_status(
    scaling_system: DatabaseScalingSystem = Depends(get_scaling_system),
) -> ScalingStatusResponse:
    """
    Get the current database scaling status.

    Args:
        scaling_system: Database scaling system

    Returns:
        The current scaling status
    """
    try:
        # Get status from scaling system
        status = scaling_system.get_status()

        # Format response
        return ScalingStatusResponse(
            is_running=status["is_running"],
            metrics=status["metrics_collector"]["metrics"],
            scaling_status=status["scaling_manager"],
            replicas=status["load_balancer"]["replicas"],
            config=status["config"],
        )
    except Exception as e:
        logger.error("Error getting scaling status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting scaling status: {str(e)}",
        )


@router.post("/config", status_code=status.HTTP_200_OK)
async def update_scaling_config(
    config: ScalingConfigUpdateRequest,
    scaling_system: DatabaseScalingSystem = Depends(get_scaling_system),
) -> Dict[str, str]:
    """
    Update the database scaling configuration.

    Args:
        config: New scaling configuration
        scaling_system: Database scaling system

    Returns:
        Success message
    """
    try:
        # Update configuration
        if config.enabled is not None:
            scaling_system.scaling_config.enabled = config.enabled

            # Start or stop scaling system based on enabled flag
            if config.enabled and not scaling_system.is_running:
                await scaling_system.start()
            elif not config.enabled and scaling_system.is_running:
                await scaling_system.stop()

        if config.mode is not None:
            scaling_system.scaling_config.mode = config.mode

        if config.min_pool_size is not None:
            scaling_system.scaling_config.thresholds.min_pool_size = (
                config.min_pool_size
            )

        if config.max_pool_size is not None:
            scaling_system.scaling_config.thresholds.max_pool_size = (
                config.max_pool_size
            )

        if config.min_replicas is not None:
            scaling_system.scaling_config.thresholds.min_replicas = config.min_replicas

        if config.max_replicas is not None:
            scaling_system.scaling_config.thresholds.max_replicas = config.max_replicas

        if config.load_balancing_strategy is not None:
            scaling_system.load_balancer.set_strategy(config.load_balancing_strategy)

        return {"message": "Scaling configuration updated successfully"}
    except Exception as e:
        logger.error("Error updating scaling configuration: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating scaling configuration: {str(e)}",
        )


@router.post("/scale", status_code=status.HTTP_200_OK)
async def manual_scaling(
    request: ManualScalingRequest,
    scaling_system: DatabaseScalingSystem = Depends(get_scaling_system),
) -> Dict[str, str]:
    """
    Perform a manual scaling operation.

    Args:
        request: Manual scaling request
        scaling_system: Database scaling system

    Returns:
        Success message
    """
    try:
        # Perform scaling action
        if (
            request.action == ScalingAction.INCREASE_POOL
            or request.action == ScalingAction.DECREASE_POOL
        ):
            if request.pool_size is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pool size is required for pool scaling actions",
                )

            success = await scaling_system.scaling_manager.manual_scale_pool(
                request.pool_size
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to scale connection pool",
                )

            return {
                "message": f"Connection pool scaled to {request.pool_size} connections"
            }

        elif request.action == ScalingAction.ADD_REPLICA:
            success = await scaling_system.scaling_manager.manual_add_replica()

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to add replica",
                )

            return {"message": "Replica added successfully"}

        elif request.action == ScalingAction.REMOVE_REPLICA:
            success = await scaling_system.scaling_manager.manual_remove_replica()

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to remove replica",
                )

            return {"message": "Replica removed successfully"}

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported scaling action: {request.action}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error performing manual scaling: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing manual scaling: {str(e)}",
        )


@router.post("/replicas", status_code=status.HTTP_201_CREATED)
async def add_replica(
    request: ReplicaConfigRequest,
    scaling_system: DatabaseScalingSystem = Depends(get_scaling_system),
) -> Dict[str, str]:
    """
    Add a new database replica.

    Args:
        request: Replica configuration
        scaling_system: Database scaling system

    Returns:
        Success message
    """
    try:
        # Create replica ID
        replica_id = f"replica-{len(scaling_system.scaling_config.replicas) + 1}"

        # Create replica config
        replica_config = ReplicaConfig(
            id=replica_id,
            host=request.host,
            port=request.port,
            username=request.username,
            password=request.password,
            database=request.database,
            pool_size=request.pool_size,
            max_overflow=request.max_overflow,
            is_active=True,
            is_read_only=True,
            weight=request.weight,
        )

        # Add replica
        success = await scaling_system.load_balancer.add_replica(replica_config)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add replica",
            )

        return {"message": f"Replica {replica_id} added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding replica: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding replica: {str(e)}",
        )


@router.delete("/replicas/{replica_id}", status_code=status.HTTP_200_OK)
async def remove_replica(
    replica_id: str,
    scaling_system: DatabaseScalingSystem = Depends(get_scaling_system),
) -> Dict[str, str]:
    """
    Remove a database replica.

    Args:
        replica_id: Replica ID
        scaling_system: Database scaling system

    Returns:
        Success message
    """
    try:
        # Remove replica
        success = await scaling_system.load_balancer.remove_replica(replica_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to remove replica {replica_id}",
            )

        return {"message": f"Replica {replica_id} removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error removing replica: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing replica: {str(e)}",
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_database_metrics(
    metric_names: Optional[List[str]] = Query(
        None, description="Metric names to filter"
    ),
    window_seconds: int = Query(300, description="Time window in seconds"),
    scaling_system: DatabaseScalingSystem = Depends(get_scaling_system),
) -> MetricsResponse:
    """
    Get database metrics history.

    Args:
        metric_names: Optional list of metric names to filter
        window_seconds: Time window in seconds
        scaling_system: Database scaling system

    Returns:
        Database metrics history
    """
    try:
        # Get metrics history
        metrics = await scaling_system.metrics_collector.get_metrics_history(
            metric_names=metric_names,
            window_seconds=window_seconds,
        )

        return MetricsResponse(metrics=metrics)
    except Exception as e:
        logger.error("Error getting database metrics: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting database metrics: {str(e)}",
        )
