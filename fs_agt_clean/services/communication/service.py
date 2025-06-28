#!/usr/bin/env python3
"""
Notification Service Implementation
Features:
1. Multiple delivery methods (push, email, in-app)
2. Templated notifications
3. Category-based routing
4. Retry logic
5. Delivery tracking
6. Database persistence
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.notifications.device_manager import DeviceManager
from fs_agt_clean.database.models import Notification as DbNotification
from fs_agt_clean.database.models import NotificationCategory as DbNotificationCategory
from fs_agt_clean.database.models import NotificationPriority as DbNotificationPriority
from fs_agt_clean.database.models import NotificationStatus as DbNotificationStatus
from fs_agt_clean.database.repositories.notification_repository import (
    NotificationRepository,
)
from fs_agt_clean.services.metrics.service import MetricsService
from fs_agt_clean.services.notifications.email_service import EmailService
from fs_agt_clean.services.notifications.push_service import PushService
from fs_agt_clean.services.notifications.templates.base import NotificationTemplate

# Comment out problematic imports for now
# These will be handled differently
# from fs_agt_clean.services.notifications.templates.email_alert import EmailAlertTemplate
# from fs_agt_clean.services.notifications.templates.sms_alert import SMSAlertTemplate
# from fs_agt_clean.services.notifications.templates.slack_alert import SlackAlertTemplate
# from fs_agt_clean.services.notifications.templates.ebay_token_alerts import EBAY_TOKEN_TEMPLATES
# from fs_agt_clean.services.notifications.templates.ebay_order_notifications import EBAY_ORDER_TEMPLATES

logger = logging.getLogger(__name__)


class NotificationCategory:
    MARKET_ANALYSIS = "market_analysis"
    CONTENT_GENERATION = "content_generation"
    PRICING_OPTIMIZATION = "pricing_optimization"
    INVENTORY_UPDATE = "inventory_update"
    LISTING_CREATION = "listing_creation"
    PIPELINE_ERROR = "pipeline_error"
    AGENT_DECISION = "agent_decision"
    SYSTEM_ALERT = "system_alert"


class NotificationPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """Handles notification delivery across multiple channels."""

    def __init__(
        self,
        config_manager: ConfigManager,
        database: Database,
        metrics_service: Optional[MetricsService] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize notification service.

        Args:
            config_manager: Configuration manager instance
            database: Database instance
            metrics_service: Optional metrics service for tracking
            max_retries: Maximum number of delivery attempts
            retry_delay: Delay between retry attempts in seconds
            config: Optional additional configuration
        """
        self.config = config_manager
        self.database = database
        self.notification_repository = NotificationRepository()
        self.metrics = metrics_service
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        self.templates: Dict[str, NotificationTemplate] = {}

        # Register default templates
        self._register_default_templates()

        # Set up email client
        self.email_config = self.config.get_section("email") or {}
        self.email_client = None
        if self.email_config:
            self._setup_email_client()

        # Set up SMS client
        self.sms_config = self.config.get_section("sms") or {}
        self.sms_client = None
        if self.sms_config:
            self._setup_sms_client()

        # Set up Slack client
        self.slack_config = self.config.get_section("slack") or {}
        self.slack_client = None
        if self.slack_config:
            self._setup_slack_client()

        # Initialize delivery services
        self.email_service = EmailService(config_manager)
        self.push_service = PushService(config_manager)
        self.device_manager = DeviceManager()

        # Track notification states
        self._pending: Dict[str, Dict] = {}
        self._failed: Dict[str, Dict] = {}
        self._delivered: Dict[str, Dict] = {}

        # UnifiedUser preferences
        self._user_preferences: Dict[str, Dict] = {}

        logger.info("NotificationService initialized")

    def _register_default_templates(self):
        """Register default notification templates."""
        try:
            # Skip template registration for now to avoid circular imports
            # and unhashable type errors
            self.logger.info("Skipping template registration for now")

            # Commented out problematic imports
            # from fs_agt_clean.core.notifications.templates.ebay_inventory_notifications import (
            #     EBAY_INVENTORY_TEMPLATES,
            # )
            # from fs_agt_clean.services.notifications.templates.ebay_order_notifications import (
            #     EBAY_ORDER_TEMPLATES,
            # )
            # from fs_agt_clean.services.notifications.templates.ebay_token_notifications import (
            #     EBAY_TOKEN_TEMPLATES,
            # )

            # # Register eBay token notification templates
            # if isinstance(EBAY_TOKEN_TEMPLATES, dict):
            #     for template_id, template in EBAY_TOKEN_TEMPLATES.items():
            #         self.register_template(template)

            # # Register eBay order notification templates
            # if isinstance(EBAY_ORDER_TEMPLATES, dict):
            #     for template_id, template in EBAY_ORDER_TEMPLATES.items():
            #         self.register_template(template)

            # # Register eBay inventory notification templates
            # if isinstance(EBAY_INVENTORY_TEMPLATES, dict):
            #     for template_id, template in EBAY_INVENTORY_TEMPLATES.items():
            #         self.register_template(template)
        except Exception as e:
            self.logger.warning(f"Error registering templates: {str(e)}")

    def register_template(self, template):
        """Register a notification template.

        Args:
            template: The template to register
        """
        try:
            if hasattr(template, "template_id"):
                self.templates[template.template_id] = template
                self.logger.debug("Registered template: %s", template.template_id)
            else:
                self.logger.warning(
                    f"Template missing template_id attribute: {template}"
                )
        except Exception as e:
            self.logger.warning(f"Error registering template: {str(e)}")

    async def send_notification(
        self,
        user_id: str,
        template_id: str,
        category: str,
        data: Dict,
        priority: str = NotificationPriority.MEDIUM,
        delivery_methods: Optional[Set[str]] = None,
    ) -> str:
        """Send a notification to a user.

        Args:
            user_id: Target user ID
            template_id: Notification template ID
            category: Notification category
            data: Template data
            priority: Notification priority
            delivery_methods: Set of delivery methods to use

        Returns:
            str: Notification ID
        """
        try:
            # Get user preferences
            user_prefs = self._user_preferences.get(user_id, {})
            if not delivery_methods:
                delivery_methods = user_prefs.get("delivery_methods", {"push", "email"})

            # Get template
            template = self.templates.get(template_id)
            title = data.get("title", "Notification")
            message = data.get("message", "You have a new notification")

            if template:
                title = template.render_title(data)
                message = template.render_body(data)

            # Create notification in database
            notification = await self.notification_repository.create_notification(
                user_id=user_id,
                template_id=template_id,
                title=title,
                message=message,
                category=category,
                priority=priority,
                data=data,
                delivery_methods=list(delivery_methods),
            )

            notification_id = notification.id

            # Track notification in memory for backward compatibility
            self._pending[notification_id] = {
                "user_id": user_id,
                "template_id": template_id,
                "category": category,
                "data": data,
                "priority": priority,
                "delivery_methods": delivery_methods,
                "attempts": 0,
                "created_at": datetime.utcnow(),
                "db_notification": notification,
            }

            # Attempt delivery
            await self._deliver_notification(notification_id)

            if self.metrics:
                await self.metrics.increment_counter(
                    "notifications_sent",
                    labels={
                        "category": category,
                        "priority": priority,
                        "status": (
                            "success"
                            if notification_id in self._delivered
                            else "pending"
                        ),
                    },
                )

            return notification_id

        except Exception as e:
            logger.error("Failed to send notification: %s", e)
            if self.metrics:
                await self.metrics.increment_counter(
                    "notifications_failed",
                    labels={"category": category, "priority": priority},
                )
            raise

    async def _deliver_notification(self, notification_id: str) -> bool:
        """Attempt to deliver a notification.

        Args:
            notification_id: ID of notification to deliver

        Returns:
            bool: True if delivered successfully
        """
        notification = self._pending.get(notification_id)
        if not notification:
            return False

        notification["attempts"] += 1

        try:
            tasks = []
            user_id = notification["user_id"]
            user_devices = await self.device_manager.get_user_devices(user_id)
            category = notification.get("category")

            if "push" in notification["delivery_methods"]:
                # Filter devices by category if specified
                eligible_devices = [
                    device
                    for device in user_devices
                    if device.enabled
                    and (not category or category in device.categories)
                ]

                if eligible_devices:
                    tasks.append(
                        self.push_service.send_push(
                            template_id=notification["template_id"],
                            user_id=notification["user_id"],
                            data=notification["data"],
                        )
                    )

            if "email" in notification["delivery_methods"]:
                tasks.append(
                    self.email_service.send_email(
                        template_id=notification["template_id"],
                        user_id=notification["user_id"],
                        data=notification["data"],
                    )
                )

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Update delivery attempts in database
            delivery_success = {}
            for i, method in enumerate(notification["delivery_methods"]):
                if i < len(results):
                    success = not isinstance(results[i], Exception)
                    delivery_success[method] = success
                    await self.notification_repository.update_delivery_attempts(
                        notification_id, method, success
                    )

            # Check if any delivery method succeeded
            success = any(delivery_success.values()) if delivery_success else False

            if success:
                # Mark as delivered in database
                await self.notification_repository.mark_as_delivered(notification_id)

                # Update in-memory tracking for backward compatibility
                self._delivered[notification_id] = notification
                self._pending.pop(notification_id, None)
                return True

            # Handle retry
            if notification["attempts"] < self.max_retries:
                await asyncio.sleep(self.retry_delay)
                return await self._deliver_notification(notification_id)

            # Mark as failed after max retries
            await self.notification_repository.mark_as_failed(notification_id)

            # Update in-memory tracking for backward compatibility
            self._failed[notification_id] = notification
            self._pending.pop(notification_id, None)
            return False

        except Exception as e:
            logger.error("Delivery attempt failed for %s: %s", notification_id, e)
            return False

    async def set_preferences(
        self,
        user_id: str,
        delivery_methods: Optional[Set[str]] = None,
        categories: Optional[Set[str]] = None,
        enabled: bool = True,
        push_enabled: Optional[bool] = None,
    ) -> None:
        """Set notification preferences for a user.

        Args:
            user_id: UnifiedUser ID
            delivery_methods: Set of preferred delivery methods
            categories: Set of notification categories to receive
            enabled: Whether notifications are enabled
            push_enabled: Whether push notifications are enabled
        """
        # Create a mutable copy of delivery_methods if it's provided
        delivery_methods_copy = set(delivery_methods) if delivery_methods else set()

        if push_enabled is not None:
            delivery_methods_copy = delivery_methods_copy or {"email"}
            if push_enabled:
                delivery_methods_copy.add("push")
            else:
                delivery_methods_copy.discard("push")

        # Convert sets to lists for JSON serialization
        delivery_methods_list = (
            list(delivery_methods_copy) if delivery_methods_copy else ["push", "email"]
        )

        # Get notification categories as a list
        notification_categories = []
        for attr in dir(NotificationCategory):
            if not attr.startswith("__") and not callable(
                getattr(NotificationCategory, attr)
            ):
                notification_categories.append(getattr(NotificationCategory, attr))

        # Ensure categories is properly handled
        categories_copy = set(categories) if categories else set()
        categories_list = (
            list(categories_copy) if categories_copy else notification_categories
        )

        self._user_preferences[user_id] = {
            "delivery_methods": delivery_methods_list,
            "categories": categories_list,
            "enabled": enabled,
            "updated_at": datetime.utcnow(),
        }

    async def get_preferences(self, user_id: str) -> Optional[Dict]:
        """Get notification preferences for a user.

        Args:
            user_id: UnifiedUser ID

        Returns:
            Optional[Dict]: UnifiedUser preferences if found
        """
        return self._user_preferences.get(user_id)

    async def get_notification_status(self, notification_id: str) -> Optional[str]:
        """Get the status of a notification.

        Args:
            notification_id: Notification ID

        Returns:
            Optional[str]: Status if found
        """
        try:
            # Try to get from database first
            notification = await self.notification_repository.find_by_id(
                notification_id
            )
            if notification:
                return notification.status.value

            # Fall back to in-memory tracking for backward compatibility
            if notification_id in self._delivered:
                return "delivered"
            if notification_id in self._pending:
                return "pending"
            if notification_id in self._failed:
                return "failed"
            return None
        except Exception as e:
            logger.error(f"Error getting notification status: {e}")
            # Fall back to in-memory tracking
            if notification_id in self._delivered:
                return "delivered"
            if notification_id in self._pending:
                return "pending"
            if notification_id in self._failed:
                return "failed"
            return None

    async def retry_failed(self, notification_id: str) -> bool:
        """Retry a failed notification.

        Args:
            notification_id: Notification ID

        Returns:
            bool: True if retry was successful
        """
        try:
            # Try to get from database first
            notification_db = await self.notification_repository.find_by_id(
                notification_id
            )
            if (
                notification_db
                and notification_db.status == DbNotificationStatus.FAILED
            ):
                # Reset delivery attempts in database
                await self.notification_repository.update(
                    notification_id,
                    {
                        "status": DbNotificationStatus.PENDING,
                        "delivery_attempts": {},
                    },
                )

                # Check if we have in-memory tracking for this notification
                if notification_id in self._failed:
                    notification = self._failed.pop(notification_id)
                    notification["attempts"] = 0
                    self._pending[notification_id] = notification
                else:
                    # Create in-memory tracking for backward compatibility
                    self._pending[notification_id] = {
                        "user_id": notification_db.user_id,
                        "template_id": notification_db.template_id,
                        "category": (
                            notification_db.category.value
                            if notification_db.category
                            else None
                        ),
                        "data": notification_db.data or {},
                        "priority": (
                            notification_db.priority.value
                            if notification_db.priority
                            else NotificationPriority.MEDIUM
                        ),
                        "delivery_methods": set(
                            notification_db.delivery_methods or ["push", "email"]
                        ),
                        "attempts": 0,
                        "created_at": notification_db.created_at,
                        "db_notification": notification_db,
                    }

                return await self._deliver_notification(notification_id)

            # Fall back to in-memory tracking for backward compatibility
            if notification_id in self._failed:
                notification = self._failed.pop(notification_id)
                notification["attempts"] = 0
                self._pending[notification_id] = notification
                return await self._deliver_notification(notification_id)

            return False
        except Exception as e:
            logger.error(f"Error retrying failed notification: {e}")
            # Fall back to in-memory tracking
            if notification_id in self._failed:
                notification = self._failed.pop(notification_id)
                notification["attempts"] = 0
                self._pending[notification_id] = notification
                return await self._deliver_notification(notification_id)
            return False
