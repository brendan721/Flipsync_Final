"""Notification API routes for FlipSync."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.security.auth import get_current_user

logger = logging.getLogger(__name__)


# Pydantic models for notifications
class PushTokenRequest(BaseModel):
    """Request model for registering push notification token."""

    token: str = Field(..., description="FCM or APNS token")
    device_type: str = Field(..., description="Device type (ios/android)")
    device_id: str = Field(..., description="Unique device identifier")


class PushTokenResponse(BaseModel):
    """Response model for push token registration."""

    success: bool
    message: str
    device_id: str


class NotificationRequest(BaseModel):
    """Request model for sending notifications."""

    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    category: str = Field(default="general", description="Notification category")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")
    target_users: Optional[List[str]] = Field(
        default=None, description="Target user IDs"
    )


class NotificationResponse(BaseModel):
    """Response model for notification operations."""

    success: bool
    message: str
    notification_id: Optional[str] = None


class UnifiedUserNotification(BaseModel):
    """Model for user notifications."""

    id: str
    title: str
    message: str
    category: str
    timestamp: datetime
    read: bool = False
    priority: str = "medium"
    data: Optional[Dict[str, Any]] = None


class NotificationListResponse(BaseModel):
    """Response model for notification list."""

    notifications: List[UnifiedUserNotification]
    unread_count: int
    total_count: int
    status: str = "operational"


# Create router
router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses={404: {"description": "Not found"}},
)

# In-memory storage for demo (replace with database in production)
_push_tokens: Dict[str, Dict[str, Any]] = {}
_user_notifications: Dict[str, List[UnifiedUserNotification]] = {}


@router.post("/push/register", response_model=PushTokenResponse)
async def register_push_token(
    request: PushTokenRequest, current_user: UnifiedUser = Depends(get_current_user)
) -> PushTokenResponse:
    """
    Register a push notification token for the current user.

    This endpoint allows mobile devices to register their FCM/APNS tokens
    for receiving push notifications.
    """
    try:
        user_id = str(current_user.id)

        # Store token information
        _push_tokens[request.device_id] = {
            "user_id": user_id,
            "token": request.token,
            "device_type": request.device_type,
            "registered_at": datetime.now(timezone.utc),
            "active": True,
        }

        logger.info(
            f"Push token registered for user {user_id}, device {request.device_id}"
        )

        return PushTokenResponse(
            success=True,
            message="Push token registered successfully",
            device_id=request.device_id,
        )

    except Exception as e:
        logger.error(f"Error registering push token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register push token",
        )


@router.delete("/push/unregister/{device_id}")
async def unregister_push_token(
    device_id: str, current_user: UnifiedUser = Depends(get_current_user)
) -> PushTokenResponse:
    """
    Unregister a push notification token.

    This endpoint allows devices to unregister their push tokens
    when the app is uninstalled or user logs out.
    """
    try:
        if device_id in _push_tokens:
            user_id = str(current_user.id)
            stored_user_id = _push_tokens[device_id].get("user_id")

            if stored_user_id == user_id:
                _push_tokens[device_id]["active"] = False
                logger.info(f"Push token unregistered for device {device_id}")

                return PushTokenResponse(
                    success=True,
                    message="Push token unregistered successfully",
                    device_id=device_id,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to unregister this device",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering push token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister push token",
        )


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    request: NotificationRequest, current_user: UnifiedUser = Depends(get_current_user)
) -> NotificationResponse:
    """
    Send a notification to users.

    This endpoint allows sending notifications to specific users or all users.
    Requires admin privileges for sending to multiple users.
    """
    try:
        notification_id = str(uuid4())

        # Determine target users
        if request.target_users:
            # Check if user has permission to send to others (admin only)
            if current_user.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can send notifications to other users",
                )
            target_users = request.target_users
        else:
            # Send to current user only
            target_users = [str(current_user.id)]

        # Create notification for each target user
        for user_id in target_users:
            notification = UnifiedUserNotification(
                id=notification_id,
                title=request.title,
                message=request.body,
                category=request.category,
                timestamp=datetime.now(timezone.utc),
                data=request.data,
            )

            if user_id not in _user_notifications:
                _user_notifications[user_id] = []

            _user_notifications[user_id].append(notification)

        # TODO: Implement actual push notification sending via FCM/APNS
        # For now, just log the notification
        logger.info(f"Notification sent: {request.title} to {len(target_users)} users")

        return NotificationResponse(
            success=True,
            message=f"Notification sent to {len(target_users)} users",
            notification_id=notification_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notification",
        )


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = 20,
    offset: int = 0,
    unread_only: bool = False,
    current_user: UnifiedUser = Depends(get_current_user),
) -> NotificationListResponse:
    """
    Get notifications for the current user.

    This endpoint returns a paginated list of notifications for the authenticated user.
    """
    try:
        user_id = str(current_user.id)
        user_notifications = _user_notifications.get(user_id, [])

        # Filter unread if requested
        if unread_only:
            user_notifications = [n for n in user_notifications if not n.read]

        # Sort by timestamp (newest first)
        user_notifications.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        total_count = len(user_notifications)
        paginated_notifications = user_notifications[offset : offset + limit]

        # Count unread notifications
        unread_count = len([n for n in user_notifications if not n.read])

        return NotificationListResponse(
            notifications=paginated_notifications,
            unread_count=unread_count,
            total_count=total_count,
            status="operational",
        )

    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications",
        )


@router.post("/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str, current_user: UnifiedUser = Depends(get_current_user)
) -> NotificationResponse:
    """
    Mark a notification as read.

    This endpoint marks a specific notification as read for the current user.
    """
    try:
        user_id = str(current_user.id)
        user_notifications = _user_notifications.get(user_id, [])

        # Find and mark notification as read
        for notification in user_notifications:
            if notification.id == notification_id:
                notification.read = True
                logger.info(
                    f"Notification {notification_id} marked as read for user {user_id}"
                )

                return NotificationResponse(
                    success=True, message="Notification marked as read"
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read",
        )


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: UnifiedUser = Depends(get_current_user),
) -> NotificationResponse:
    """
    Mark all notifications as read for the current user.

    This endpoint marks all notifications as read for the authenticated user.
    """
    try:
        user_id = str(current_user.id)
        user_notifications = _user_notifications.get(user_id, [])

        # Mark all notifications as read
        read_count = 0
        for notification in user_notifications:
            if not notification.read:
                notification.read = True
                read_count += 1

        logger.info(f"Marked {read_count} notifications as read for user {user_id}")

        return NotificationResponse(
            success=True, message=f"Marked {read_count} notifications as read"
        )

    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read",
        )
