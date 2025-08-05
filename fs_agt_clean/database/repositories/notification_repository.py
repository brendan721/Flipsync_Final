"""
Notification repository implementation using the base repository pattern.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fs_agt_clean.database.base_repository import BaseRepository
from fs_agt_clean.database.models import Notification, NotificationStatus

logger = logging.getLogger(__name__)


class NotificationRepository(BaseRepository[Notification]):
    """
    Notification repository for database operations related to notifications.

    This repository extends the BaseRepository to provide notification-specific
    database operations, including notification creation, updates, and queries.
    """

    def __init__(self):
        """Initialize the repository."""
        super().__init__(Notification, "notifications")

    async def get_by_user_id(self, user_id: str) -> List[Notification]:
        """
        Find notifications by user ID.

        Args:
            user_id: The user ID to search for

        Returns:
            A list of notifications for the user
        """
        try:
            return await self.find_by_criteria({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error finding notifications for user {user_id}: {e}")
            raise

    async def get_by_status(
        self, user_id: str, status: NotificationStatus
    ) -> List[Notification]:
        """
        Find notifications by user ID and status.

        Args:
            user_id: The user ID to search for
            status: The notification status to search for

        Returns:
            A list of notifications for the user with the specified status
        """
        try:
            return await self.find_by_criteria({"user_id": user_id, "status": status})
        except Exception as e:
            logger.error(
                f"Error finding notifications for user {user_id} with status {status}: {e}"
            )
            raise

    async def get_by_category(self, user_id: str, category: str) -> List[Notification]:
        """
        Find notifications by user ID and category.

        Args:
            user_id: The user ID to search for
            category: The notification category to search for

        Returns:
            A list of notifications for the user in the specified category
        """
        try:
            return await self.find_by_criteria(
                {"user_id": user_id, "category": category}
            )
        except Exception as e:
            logger.error(
                f"Error finding notifications for user {user_id} in category {category}: {e}"
            )
            raise

    async def get_unread(self, user_id: str) -> List[Notification]:
        """
        Find unread notifications for a user.

        Args:
            user_id: The user ID to search for

        Returns:
            A list of unread notifications for the user
        """
        try:
            return await self.find_by_criteria(
                {"user_id": user_id, "status": NotificationStatus.DELIVERED}
            )
        except Exception as e:
            logger.error(f"Error finding unread notifications for user {user_id}: {e}")
            raise

    async def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """
        Mark a notification as read.

        Args:
            notification_id: The notification ID

        Returns:
            The updated notification if found, None otherwise
        """
        try:
            notification = await self.find_by_id(notification_id)
            if not notification:
                return None

            notification.mark_read()
            return await self.update(
                notification_id,
                {
                    "status": NotificationStatus.READ,
                    "read_at": datetime.utcnow(),
                },
            )
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            raise

    async def mark_as_delivered(self, notification_id: str) -> Optional[Notification]:
        """
        Mark a notification as delivered.

        Args:
            notification_id: The notification ID

        Returns:
            The updated notification if found, None otherwise
        """
        try:
            notification = await self.find_by_id(notification_id)
            if not notification:
                return None

            notification.mark_delivered()
            return await self.update(
                notification_id,
                {
                    "status": NotificationStatus.DELIVERED,
                    "delivered_at": datetime.utcnow(),
                },
            )
        except Exception as e:
            logger.error(
                f"Error marking notification {notification_id} as delivered: {e}"
            )
            raise

    async def mark_as_archived(self, notification_id: str) -> Optional[Notification]:
        """
        Mark a notification as archived.

        Args:
            notification_id: The notification ID

        Returns:
            The updated notification if found, None otherwise
        """
        try:
            notification = await self.find_by_id(notification_id)
            if not notification:
                return None

            notification.mark_archived()
            return await self.update(
                notification_id,
                {
                    "status": NotificationStatus.ARCHIVED,
                },
            )
        except Exception as e:
            logger.error(
                f"Error marking notification {notification_id} as archived: {e}"
            )
            raise

    async def mark_as_failed(self, notification_id: str) -> Optional[Notification]:
        """
        Mark a notification as failed.

        Args:
            notification_id: The notification ID

        Returns:
            The updated notification if found, None otherwise
        """
        try:
            notification = await self.find_by_id(notification_id)
            if not notification:
                return None

            notification.mark_failed()
            return await self.update(
                notification_id,
                {
                    "status": NotificationStatus.FAILED,
                },
            )
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as failed: {e}")
            raise

    async def create_notification(
        self,
        user_id: str,
        template_id: str,
        title: str,
        message: str,
        category: str,
        priority: str = "medium",
        data: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        delivery_methods: Optional[List[str]] = None,
    ) -> Notification:
        """
        Create a new notification.

        Args:
            user_id: The user ID
            template_id: The template ID
            title: The notification title
            message: The notification message
            category: The notification category
            priority: The notification priority
            data: Additional notification data
            actions: Notification actions
            delivery_methods: Delivery methods

        Returns:
            The created notification
        """
        try:
            notification_data = {
                "user_id": user_id,
                "template_id": template_id,
                "title": title,
                "message": message,
                "category": category,
                "priority": priority,
                "status": NotificationStatus.PENDING,
                "data": data or {},
                "actions": actions or [],
                "delivery_methods": delivery_methods or ["push", "email"],
                "delivery_attempts": {},
                "created_at": datetime.utcnow(),
            }

            return await self.create(notification_data)
        except Exception as e:
            logger.error(f"Error creating notification for user {user_id}: {e}")
            raise

    async def update_delivery_attempts(
        self, notification_id: str, method: str, success: bool
    ) -> Optional[Notification]:
        """
        Update delivery attempts for a notification.

        Args:
            notification_id: The notification ID
            method: The delivery method
            success: Whether the delivery was successful

        Returns:
            The updated notification if found, None otherwise
        """
        try:
            notification = await self.find_by_id(notification_id)
            if not notification:
                return None

            delivery_attempts = notification.delivery_attempts or {}
            method_attempts = delivery_attempts.get(
                method, {"success": 0, "failure": 0}
            )

            if success:
                method_attempts["success"] = method_attempts.get("success", 0) + 1
            else:
                method_attempts["failure"] = method_attempts.get("failure", 0) + 1

            delivery_attempts[method] = method_attempts

            # If all methods have been attempted successfully, mark as delivered
            if all(
                attempts.get("success", 0) > 0
                for method, attempts in delivery_attempts.items()
                if method in notification.delivery_methods
            ):
                return await self.mark_as_delivered(notification_id)

            # Otherwise, just update the delivery attempts
            return await self.update(
                notification_id,
                {
                    "delivery_attempts": delivery_attempts,
                },
            )
        except Exception as e:
            logger.error(
                f"Error updating delivery attempts for notification {notification_id}: {e}"
            )
            raise
