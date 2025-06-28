"""Webhook API endpoints for FlipSync."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Define Pydantic models for request/response validation
class WebhookNotification(BaseModel):
    sku: Optional[str] = None
    availableQuantity: Optional[int] = None
    timestamp: Optional[str] = None
    orderId: Optional[str] = None
    orderStatus: Optional[str] = None
    offerId: Optional[str] = None


class WebhookEvent(BaseModel):
    eventType: str
    notification: WebhookNotification


class WebhookRegistration(BaseModel):
    callbackUrl: str
    eventTypes: List[str]


class WebhookResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["webhooks"],
    responses={404: {"description": "Not found"}},
)


async def get_webhook_service(request: Request):
    """Get webhook service from app state."""
    return getattr(request.app.state, "webhook_service", None)


async def get_ebay_webhook_handler(request: Request):
    """Get eBay webhook handler from app state."""
    return getattr(request.app.state, "ebay_webhook_handler", None)


@router.post("/ebay/callback", response_model=WebhookResponse)
async def ebay_webhook_callback(
    request: Request,
    x_ebay_signature: Optional[str] = Header(None),
):
    """
    eBay webhook callback endpoint.

    This endpoint receives webhook notifications from eBay.
    """
    try:
        # Get webhook event data
        event_data = await request.json()

        # Get eBay webhook handler
        ebay_handler = await get_ebay_webhook_handler(request)

        if not ebay_handler:
            # Create a basic handler if not available
            from fs_agt_clean.services.webhooks.ebay_handler import EbayWebhookHandler

            ebay_handler = EbayWebhookHandler()

        # Validate eBay signature if provided
        if x_ebay_signature:
            # Simple validation for now, can be enhanced for proper HMAC signature validation
            if not x_ebay_signature.startswith("sha256="):
                logger.warning("Invalid eBay signature format")

        # Handle webhook event
        result = await ebay_handler.handle_webhook_event(event_data)

        if not result.get("success", False):
            logger.error(f"Error processing eBay webhook: {result.get('error')}")
            # We still return 200 to eBay to acknowledge receipt, but log the error

        return WebhookResponse(
            success=True,
            message="Webhook received and processed",
            data={
                "status": "received",
                "eventType": result.get("eventType"),
                "processingResult": result,
            },
        )

    except Exception as e:
        logger.error(f"Error handling eBay webhook: {e}")
        # We still return 200 to eBay to acknowledge receipt, but log the error
        return WebhookResponse(
            success=False, message="Error processing webhook", data={"error": str(e)}
        )


@router.post("/ebay/register", response_model=WebhookResponse)
async def register_ebay_webhook(
    registration: WebhookRegistration,
    request: Request,
):
    """
    Register webhook with eBay.

    This endpoint registers your callback URL with eBay for specified event types.
    """
    try:
        # Get eBay webhook handler
        ebay_handler = await get_ebay_webhook_handler(request)

        if not ebay_handler:
            # Create a basic handler if not available
            from fs_agt_clean.services.webhooks.ebay_handler import EbayWebhookHandler

            ebay_handler = EbayWebhookHandler()

        # Register webhook
        result = await ebay_handler.register_with_ebay(
            callback_url=registration.callbackUrl,
            event_types=registration.eventTypes,
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to register webhook with eBay: {result.get('error')}",
            )

        return WebhookResponse(
            success=True, message="Webhook registered successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering eBay webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ebay/test-event", response_model=WebhookResponse)
async def generate_test_event(
    event_type: str,
    request: Request,
) -> WebhookResponse:
    """
    Generate a test webhook event for testing purposes.

    This endpoint allows generating test webhook events to validate your webhook handling.
    """
    try:
        ebay_handler = await get_ebay_webhook_handler(request)

        if not ebay_handler:
            # Create a basic handler if not available
            from fs_agt_clean.services.webhooks.ebay_handler import EbayWebhookHandler

            ebay_handler = EbayWebhookHandler()

        # Create test data based on event type
        if event_type.startswith("INVENTORY_ITEM_"):
            test_data = {
                "eventType": event_type,
                "notification": {
                    "sku": "TEST_SKU_123",
                    "availableQuantity": 10,
                    "timestamp": "2023-07-20T14:30:00.000Z",
                },
            }
        elif event_type.startswith("OFFER_"):
            test_data = {
                "eventType": event_type,
                "notification": {
                    "offerId": "TEST_OFFER_456",
                    "sku": "TEST_SKU_123",
                    "timestamp": "2023-07-20T14:30:00.000Z",
                },
            }
        elif event_type.startswith("ORDER_"):
            test_data = {
                "eventType": event_type,
                "notification": {
                    "orderId": "TEST_ORDER_789",
                    "orderStatus": "PAID",
                    "timestamp": "2023-07-20T14:30:00.000Z",
                },
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported event type: {event_type}"
            )

        # Process test event
        result = await ebay_handler.handle_webhook_event(test_data)

        return WebhookResponse(
            success=True,
            message="Test event generated and processed",
            data={
                "testEvent": test_data,
                "result": result,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating test event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=WebhookResponse)
async def get_webhook_stats(request: Request):
    """Get webhook statistics."""
    try:
        webhook_service = await get_webhook_service(request)

        if webhook_service:
            stats = await webhook_service.get_webhook_stats()
        else:
            # Return basic stats if service not available
            stats = {
                "registered_webhooks": 0,
                "active_webhooks": 0,
                "total_deliveries": 0,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "success_rate": 1.0,
            }

        return WebhookResponse(
            success=True, message="Webhook statistics retrieved", data=stats
        )

    except Exception as e:
        logger.error(f"Error getting webhook stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registered", response_model=WebhookResponse)
async def get_registered_webhooks(request: Request):
    """Get all registered webhooks."""
    try:
        webhook_service = await get_webhook_service(request)

        if webhook_service:
            webhooks = await webhook_service.get_registered_webhooks()
        else:
            webhooks = {}

        return WebhookResponse(
            success=True,
            message="Registered webhooks retrieved",
            data={"webhooks": webhooks},
        )

    except Exception as e:
        logger.error(f"Error getting registered webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
