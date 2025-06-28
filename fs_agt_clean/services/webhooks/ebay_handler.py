"""eBay webhook event handler for FlipSync."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fs_agt_clean.services.infrastructure.metrics_service import MetricsService

logger = logging.getLogger(__name__)

# Event types supported by eBay webhooks
SUPPORTED_EVENT_TYPES = [
    "INVENTORY_ITEM_CREATED",
    "INVENTORY_ITEM_UPDATED",
    "INVENTORY_ITEM_DELETED",
    "OFFER_CREATED",
    "OFFER_UPDATED",
    "OFFER_DELETED",
    "ORDER_CREATED",
    "ORDER_UPDATED",
    "ORDER_SHIPPED",
    "ORDER_REFUNDED",
    "PAYMENT_DISPUTE_CREATED",
    "PAYMENT_DISPUTE_UPDATED",
    "PAYMENT_DISPUTE_RESOLVED",
    "RETURN_CREATED",
    "RETURN_UPDATED",
    "RETURN_RESOLVED",
]


class EbayWebhookHandler:
    """Handler for eBay webhook events."""

    def __init__(
        self,
        ebay_service: Optional[Any] = None,
        metrics_service: Optional[MetricsService] = None,
        notification_service: Optional[Any] = None,
    ):
        """Initialize eBay webhook handler.

        Args:
            ebay_service: eBay API service (optional)
            metrics_service: Metrics service (optional)
            notification_service: Notification service (optional)
        """
        self.ebay_service = ebay_service
        self.metrics = metrics_service
        self.notifications = notification_service
        self.logger = logging.getLogger(__name__)

    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook event from eBay.

        Args:
            event_data: Webhook event data from eBay

        Returns:
            Processing result
        """
        start_time = datetime.now()
        event_type = event_data.get("eventType")

        # Log receipt of webhook
        self.logger.info(f"Received eBay webhook event: {event_type}")

        # Validate webhook data
        is_valid, validation_error = self._validate_webhook_event(event_data)
        if not is_valid:
            error_msg = f"Invalid eBay webhook data: {validation_error}"
            self.logger.error(error_msg)

            if self.metrics:
                await self.metrics.record_metric(
                    name="ebay_webhook_validation_error",
                    value=1.0,
                    labels={"event_type": str(event_type), "error": validation_error},
                )

            return {
                "success": False,
                "error": error_msg,
                "eventType": event_type,
            }

        # Process webhook through eBay service if available
        try:
            if self.ebay_service and hasattr(
                self.ebay_service, "process_webhook_event"
            ):
                await self.ebay_service.process_webhook_event(event_data)
            else:
                # Basic processing without eBay service
                await self._process_event_basic(event_data)

            # Record success metrics
            if self.metrics:
                processing_time = (datetime.now() - start_time).total_seconds()
                await self.metrics.record_metric(
                    name="ebay_webhook_processing_time",
                    value=processing_time,
                    labels={"event_type": str(event_type)},
                )
                await self.metrics.record_metric(
                    name="ebay_webhook_event_count",
                    value=1.0,
                    labels={"event_type": str(event_type)},
                )

            return {
                "success": True,
                "eventType": event_type,
                "processingTime": (datetime.now() - start_time).total_seconds(),
            }

        except Exception as e:
            error_msg = f"Error processing eBay webhook event: {str(e)}"
            self.logger.error(error_msg)

            # Record error metrics
            if self.metrics:
                await self.metrics.record_metric(
                    name="ebay_webhook_error",
                    value=1.0,
                    labels={"event_type": str(event_type), "error": str(e)},
                )

            # Send notification about the error
            if self.notifications:
                try:
                    await self.notifications.send_notification(
                        user_id="system",
                        template_id="ebay_webhook_error",
                        category="PIPELINE_ERROR",
                        data={
                            "event_type": str(event_type),
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                except Exception as notification_error:
                    self.logger.error(
                        f"Error sending notification: {notification_error}"
                    )

            return {
                "success": False,
                "error": error_msg,
                "eventType": event_type,
            }

    async def _process_event_basic(self, event_data: Dict[str, Any]) -> None:
        """Basic event processing when eBay service is not available.

        Args:
            event_data: Webhook event data
        """
        event_type = event_data.get("eventType")
        notification = event_data.get("notification", {})

        self.logger.info(
            f"Processing eBay webhook event {event_type} with basic handler"
        )

        # Log event details based on type
        if event_type.startswith("INVENTORY_ITEM_"):
            sku = notification.get("sku")
            quantity = notification.get("availableQuantity")
            self.logger.info(f"Inventory event for SKU {sku}, quantity: {quantity}")

        elif event_type.startswith("OFFER_"):
            offer_id = notification.get("offerId")
            sku = notification.get("sku")
            self.logger.info(f"Offer event for offer {offer_id}, SKU: {sku}")

        elif event_type.startswith("ORDER_"):
            order_id = notification.get("orderId")
            status = notification.get("orderStatus")
            self.logger.info(f"Order event for order {order_id}, status: {status}")

        else:
            self.logger.info(f"Generic event processing for {event_type}")

    def _validate_webhook_event(
        self, event_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate webhook event data.

        Args:
            event_data: Webhook event data

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for required fields
        if "eventType" not in event_data:
            return False, "Missing eventType in webhook data"

        event_type = event_data.get("eventType")

        # Validate event type
        if event_type not in SUPPORTED_EVENT_TYPES:
            return False, f"Unsupported event type: {event_type}"

        # Verify notification data is present
        if "notification" not in event_data:
            return False, "Missing notification data in webhook"

        notification = event_data.get("notification", {})

        # Validate based on event type
        if event_type.startswith("INVENTORY_ITEM_"):
            if "sku" not in notification:
                return False, f"Missing SKU in {event_type} notification"

        elif event_type.startswith("OFFER_"):
            if "offerId" not in notification:
                return False, f"Missing offerId in {event_type} notification"

        elif event_type.startswith("ORDER_"):
            if "orderId" not in notification:
                return False, f"Missing orderId in {event_type} notification"

        return True, None

    async def get_supported_event_types(self) -> List[str]:
        """Get list of supported event types.

        Returns:
            List of supported event types
        """
        return SUPPORTED_EVENT_TYPES.copy()

    async def register_with_ebay(
        self, callback_url: str, event_types: List[str]
    ) -> Dict[str, Any]:
        """Register webhook with eBay.

        Args:
            callback_url: URL for eBay to send webhooks to
            event_types: List of event types to subscribe to

        Returns:
            Registration result
        """
        try:
            if self.ebay_service and hasattr(self.ebay_service, "register_webhook"):
                result = await self.ebay_service.register_webhook(
                    callback_url=callback_url,
                    event_types=event_types,
                )
                return result
            else:
                # Mock registration when eBay service is not available
                self.logger.info(
                    f"Mock eBay webhook registration for URL: {callback_url}"
                )
                return {
                    "success": True,
                    "callback_url": callback_url,
                    "event_types": event_types,
                    "registration_id": "mock_registration_123",
                }

        except Exception as e:
            self.logger.error(f"Error registering eBay webhook: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def unregister_from_ebay(self, registration_id: str) -> Dict[str, Any]:
        """Unregister webhook from eBay.

        Args:
            registration_id: Registration ID to unregister

        Returns:
            Unregistration result
        """
        try:
            if self.ebay_service and hasattr(self.ebay_service, "unregister_webhook"):
                result = await self.ebay_service.unregister_webhook(registration_id)
                return result
            else:
                # Mock unregistration when eBay service is not available
                self.logger.info(
                    f"Mock eBay webhook unregistration for ID: {registration_id}"
                )
                return {
                    "success": True,
                    "registration_id": registration_id,
                }

        except Exception as e:
            self.logger.error(f"Error unregistering eBay webhook: {e}")
            return {
                "success": False,
                "error": str(e),
            }
