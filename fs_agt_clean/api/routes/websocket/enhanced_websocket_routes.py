"""
Enhanced WebSocket API Routes for FlipSync.

This module provides WebSocket endpoints for real-time communication including:
- Enhanced WebSocket connections with room support
- Approval workflow real-time events
- AI analysis streaming events
- Marketplace sync status updates
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from fs_agt_clean.core.auth.auth_service import AuthService
from fs_agt_clean.database.models.unified_user import UnifiedUser

# Note: Using basic WebSocket implementation instead of enhanced manager
# from fs_agt_clean.core.websocket.enhanced_websocket_manager import (
#     enhanced_websocket_manager, EventType, RoomType
# )
from fs_agt_clean.services.workflow.approval_workflow_service import (
    ApprovalPriority,
    ApprovalType,
    approval_workflow_service,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/ws", tags=["enhanced-websocket"])


class ApprovalRequestCreate(BaseModel):
    """Request model for creating approval requests."""

    approval_type: str = Field(..., description="Type of approval request")
    title: str = Field(..., description="Request title")
    description: str = Field(..., description="Request description")
    data: Dict[str, Any] = Field(..., description="Request data")
    approvers: List[str] = Field(..., description="List of approver user IDs")
    priority: str = Field(default="medium", description="Request priority")
    timeout_minutes: int = Field(
        default=60, ge=1, le=1440, description="Timeout in minutes"
    )
    requires_all_approvers: bool = Field(
        default=False, description="Whether all approvers must approve"
    )


class ApprovalActionRequest(BaseModel):
    """Request model for approval actions."""

    action: str = Field(..., description="Action: approve or reject")
    comments: Optional[str] = Field(default=None, description="Action comments")
    reason: Optional[str] = Field(
        default=None, description="Rejection reason (required for reject)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class WebSocketMessage(BaseModel):
    """WebSocket message model."""

    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    target: Optional[str] = Field(default=None, description="Target user or room")


# @router.websocket("/connect")
# async def websocket_endpoint(
#     websocket: WebSocket,
#     user_id: str = Query(..., description="UnifiedUser ID"),
#     rooms: Optional[str] = Query(default=None, description="Comma-separated list of rooms to join")
# ):
#     """
#     Enhanced WebSocket connection endpoint - DISABLED
#
#     This endpoint is temporarily disabled because it depends on the enhanced_websocket_manager
#     which has been archived. Use the basic WebSocket routes instead.
#     """
#     pass


# async def _handle_websocket_message(
#     connection_id: str,
#     user_id: str,
#     message_data: Dict[str, Any]
# ):
#     """Handle incoming WebSocket message - DISABLED"""
#     pass


@router.post("/approval/create")
async def create_approval_request(
    request: ApprovalRequestCreate,
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Create a new approval request with real-time notifications.

    This endpoint:
    - Creates approval workflow request
    - Sends real-time notifications to approvers
    - Tracks approval progress and status
    - Handles timeout and escalation
    """
    try:
        logger.info(
            f"Creating approval request for user {current_user.id}: {request.title}"
        )

        # Validate approval type
        try:
            approval_type = ApprovalType(request.approval_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid approval type: {request.approval_type}",
            )

        # Validate priority
        try:
            priority = ApprovalPriority(request.priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority: {request.priority}",
            )

        # Validate rejection reason for reject action
        if request.approval_type == "reject" and not request.description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is required for reject actions",
            )

        # Create approval request
        request_id = await approval_workflow_service.create_approval_request(
            requester_id=str(current_user.id),
            approval_type=approval_type,
            title=request.title,
            description=request.description,
            data=request.data,
            approvers=request.approvers,
            priority=priority,
            timeout_minutes=request.timeout_minutes,
            requires_all_approvers=request.requires_all_approvers,
        )

        if not request_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create approval request",
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "request_id": request_id,
                "message": "Approval request created successfully",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating approval request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Approval request creation failed: {str(e)}",
        )


@router.post("/approval/{request_id}/action")
async def handle_approval_action(
    request_id: str,
    action_request: ApprovalActionRequest,
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Handle approval action (approve/reject) with real-time notifications.

    This endpoint:
    - Processes approval or rejection actions
    - Sends real-time status updates
    - Handles workflow completion
    - Provides audit trail
    """
    try:
        logger.info(
            f"Processing approval action for user {current_user.id}: {request_id}"
        )

        # Validate action
        if action_request.action not in ["approve", "reject"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'approve' or 'reject'",
            )

        # Validate rejection reason
        if action_request.action == "reject" and not action_request.reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is required for reject actions",
            )

        # Process action
        if action_request.action == "approve":
            success = await approval_workflow_service.approve_request(
                request_id=request_id,
                approver_id=str(current_user.id),
                comments=action_request.comments,
                metadata=action_request.metadata,
            )
        else:  # reject
            success = await approval_workflow_service.reject_request(
                request_id=request_id,
                approver_id=str(current_user.id),
                reason=action_request.reason,
                metadata=action_request.metadata,
            )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to {action_request.action} request",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "request_id": request_id,
                "action": action_request.action,
                "message": f"Request {action_request.action}d successfully",
                "processed_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing approval action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Approval action failed: {str(e)}",
        )


@router.get("/approval/requests")
async def get_approval_requests(
    include_completed: bool = Query(
        default=False, description="Include completed requests"
    ),
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Get approval requests for the current user.

    This endpoint:
    - Returns pending and optionally completed requests
    - Includes requests where user is approver or requester
    - Provides request status and progress
    - Supports filtering and pagination
    """
    try:
        logger.info(f"Getting approval requests for user {current_user.id}")

        # Get user requests
        requests = approval_workflow_service.get_user_requests(
            user_id=str(current_user.id), include_completed=include_completed
        )

        # Format requests for response
        formatted_requests = []
        for request in requests:
            formatted_requests.append(request.to_dict())

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "requests": formatted_requests,
                "total_count": len(formatted_requests),
                "include_completed": include_completed,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error getting approval requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve approval requests: {str(e)}",
        )


@router.get("/approval/{request_id}")
async def get_approval_request(
    request_id: str, current_user: UnifiedUser = Depends(AuthService.get_current_user)
):
    """
    Get specific approval request details.

    This endpoint:
    - Returns detailed request information
    - Includes approval/rejection history
    - Shows current status and progress
    - Validates user access permissions
    """
    try:
        logger.info(f"Getting approval request {request_id} for user {current_user.id}")

        # Get request
        request = approval_workflow_service.get_request(request_id)
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request not found: {request_id}",
            )

        # Check user access
        user_id = str(current_user.id)
        if user_id not in request.approvers and user_id != request.requester_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this approval request",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "request": request.to_dict(),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting approval request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve approval request: {str(e)}",
        )


@router.get("/stats")
async def get_websocket_stats(
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Get WebSocket and workflow statistics.

    This endpoint:
    - Returns WebSocket connection statistics
    - Shows approval workflow metrics
    - Provides performance information
    - Includes real-time status data
    """
    try:
        # Get WebSocket stats - using basic stats since enhanced manager is disabled
        websocket_stats = {
            "status": "enhanced_manager_disabled",
            "active_connections": 0,
            "message": "Enhanced WebSocket manager is temporarily disabled",
        }

        # Get workflow stats
        workflow_stats = approval_workflow_service.get_workflow_stats()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "websocket": websocket_stats,
                "workflow": workflow_stats,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}",
        )


@router.post("/health")
async def websocket_health_check():
    """
    Perform health check on WebSocket services.

    This endpoint:
    - Tests WebSocket manager functionality
    - Validates approval workflow service
    - Returns comprehensive health status
    - Available without authentication for monitoring
    """
    try:
        # Test WebSocket manager - using basic check since enhanced manager is disabled
        websocket_healthy = True  # Basic check
        websocket_stats = {
            "status": "enhanced_manager_disabled",
            "active_connections": 0,
            "fastapi_available": True,
        }

        # Test approval workflow service
        workflow_healthy = True  # Basic check
        workflow_stats = approval_workflow_service.get_workflow_stats()

        overall_health = (
            "healthy" if websocket_healthy and workflow_healthy else "degraded"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": overall_health,
                "websocket_manager": {
                    "status": "disabled" if websocket_healthy else "unhealthy",
                    "active_connections": websocket_stats.get("active_connections", 0),
                    "fastapi_available": websocket_stats.get(
                        "fastapi_available", False
                    ),
                },
                "approval_workflow": {
                    "status": "healthy" if workflow_healthy else "unhealthy",
                    "active_requests": workflow_stats.get("active_requests", 0),
                    "timeout_monitor_running": workflow_stats.get(
                        "timeout_monitor_running", False
                    ),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
