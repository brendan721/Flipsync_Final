"""
Unified Payment Service for FlipSync
====================================

This module consolidates all payment functionality into a single, unified service,
eliminating duplication across:
- fs_agt_clean/core/payment/paypal_service.py
- fs_agt_clean/services/payment_processing/paypal_service.py

AGENT_CONTEXT: Complete payment processing system with PayPal integration, subscription management, and billing
AGENT_PRIORITY: Unified payment service with subscription management, invoice generation, and metrics tracking
AGENT_PATTERN: Async payment processing with comprehensive error handling and monitoring
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Real PayPal SDK integration for production
import paypalrestsdk
from pydantic import BaseModel, ConfigDict

# Import core payment models
try:
    from fs_agt_clean.core.payment.subscription_model import (
        BillingCycle,
        SubscriptionPlan,
        SubscriptionStatus,
    )
    from fs_agt_clean.core.payment.invoice_generator import Invoice, InvoiceGenerator
    from fs_agt_clean.core.payment.billing_cycle_manager import BillingCycleManager
    
    payment_models_available = True
except ImportError:
    payment_models_available = False
    # Create mock classes for graceful degradation
    class BillingCycle(str, Enum):
        MONTHLY = "monthly"
        YEARLY = "yearly"
    
    class SubscriptionPlan:
        pass
    
    class SubscriptionStatus(str, Enum):
        ACTIVE = "active"
        CANCELLED = "cancelled"
    
    class Invoice:
        pass
    
    class InvoiceGenerator:
        pass
    
    class BillingCycleManager:
        pass

# Import services
try:
    from fs_agt_clean.services.metrics.service import MetricsService
    from fs_agt_clean.services.notifications.service import NotificationService
    
    services_available = True
except ImportError:
    services_available = False
    # Mock services for graceful degradation
    class MetricsService:
        async def track_error(self, error_type: str, error_message: str):
            pass
        
        async def increment_counter(self, counter_name: str):
            pass
    
    class NotificationService:
        async def send_notification(self, user_id: str, message: str):
            pass

logger = logging.getLogger(__name__)


class PaymentProvider(str, Enum):
    """Supported payment providers."""
    PAYPAL = "paypal"
    STRIPE = "stripe"  # For future expansion
    SQUARE = "square"  # For future expansion


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentType(str, Enum):
    """Payment type enumeration."""
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    REFUND = "refund"


class PaymentRequest(BaseModel):
    """Payment request model."""
    amount: Decimal
    currency: str = "USD"
    description: str
    payment_method: Dict[str, Any]
    invoice_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    """Payment response model."""
    payment_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    provider: PaymentProvider
    created_at: datetime
    invoice_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionRequest(BaseModel):
    """Subscription creation request model."""
    user_id: str
    plan_id: str
    payment_method: Dict[str, Any]
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    generate_invoice: bool = True
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class UnifiedPaymentService:
    """
    Unified Payment Service - Consolidates all payment functionality
    
    This service combines features from:
    - PayPal service implementations
    - Subscription management
    - Invoice generation
    - Billing cycle management
    - Payment metrics and notifications
    """

    def __init__(
        self,
        paypal_client_id: str,
        paypal_client_secret: str,
        metrics_service: Optional[MetricsService] = None,
        notification_service: Optional[NotificationService] = None,
        invoice_generator: Optional[InvoiceGenerator] = None,
        billing_cycle_manager: Optional[BillingCycleManager] = None,
        sandbox_mode: bool = False,
    ):
        """Initialize the unified payment service."""
        self.paypal_client_id = paypal_client_id
        self.paypal_client_secret = paypal_client_secret
        self.sandbox_mode = sandbox_mode
        
        # Initialize services with graceful fallbacks
        self.metrics_service = metrics_service or MetricsService()
        self.notification_service = notification_service or NotificationService()
        self.invoice_generator = invoice_generator
        self.billing_cycle_manager = billing_cycle_manager
        
        # Configure PayPal SDK
        self._configure_paypal()
        
        logger.info(f"Unified Payment Service initialized (sandbox: {sandbox_mode})")

    def _configure_paypal(self):
        """Configure PayPal SDK."""
        paypalrestsdk.configure({
            "mode": "sandbox" if self.sandbox_mode else "live",
            "client_id": self.paypal_client_id,
            "client_secret": self.paypal_client_secret,
        })

    async def process_payment(
        self,
        payment_request: PaymentRequest
    ) -> PaymentResponse:
        """
        Process a one-time payment.
        
        Args:
            payment_request: Payment request details
            
        Returns:
            Payment response with transaction details
        """
        try:
            # Create PayPal payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal",
                    "payer_info": payment_request.payment_method
                },
                "transactions": [{
                    "amount": {
                        "total": str(payment_request.amount),
                        "currency": payment_request.currency
                    },
                    "description": payment_request.description,
                }],
            })

            if payment.create():
                # Track successful payment
                await self.metrics_service.increment_counter("payments_processed")
                
                # Record payment for invoice if provided
                if payment_request.invoice_id and self.invoice_generator:
                    await self.invoice_generator.record_payment(
                        invoice_id=payment_request.invoice_id,
                        payment_id=payment.id,
                        amount=payment_request.amount,
                        payment_date=datetime.now(timezone.utc),
                        payment_method="paypal",
                        metadata={
                            "payment_provider": "paypal",
                            "payment_status": payment.state,
                            **(payment_request.metadata or {})
                        },
                    )

                return PaymentResponse(
                    payment_id=payment.id,
                    status=PaymentStatus.COMPLETED,
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    provider=PaymentProvider.PAYPAL,
                    created_at=datetime.now(timezone.utc),
                    invoice_id=payment_request.invoice_id,
                    metadata=payment_request.metadata,
                )
            else:
                await self.metrics_service.track_error("payment_creation_failed", str(payment.error))
                raise Exception(f"Payment creation failed: {payment.error}")

        except Exception as e:
            await self.metrics_service.track_error("payment_processing_error", str(e))
            logger.error(f"Payment processing failed: {e}")
            raise

    async def create_subscription_plan(
        self,
        plan: SubscriptionPlan
    ) -> Dict[str, Any]:
        """Create a subscription plan with PayPal."""
        try:
            billing_plan = paypalrestsdk.BillingPlan({
                "name": plan.name,
                "description": plan.description,
                "type": "INFINITE",
                "payment_definitions": [{
                    "name": f"{plan.name} Payment",
                    "type": "REGULAR",
                    "frequency": "MONTH",
                    "frequency_interval": "1",
                    "amount": {
                        "value": str(plan.price),
                        "currency": plan.currency
                    },
                    "cycles": "0",
                }],
                "merchant_preferences": {
                    "auto_bill_amount": "YES",
                    "cancel_url": plan.cancel_url,
                    "initial_fail_amount_action": "CONTINUE",
                    "max_fail_attempts": "1",
                    "return_url": plan.return_url,
                    "setup_fee": {
                        "value": "0",
                        "currency": plan.currency
                    }
                }
            })

            if billing_plan.create():
                billing_plan.activate()
                await self.metrics_service.increment_counter("subscription_plans_created")
                return {"plan_id": billing_plan.id, "status": "active"}
            else:
                await self.metrics_service.track_error("plan_creation_failed", str(billing_plan.error))
                raise Exception(f"Plan creation failed: {billing_plan.error}")

        except Exception as e:
            await self.metrics_service.track_error("plan_creation_error", str(e))
            logger.error(f"Subscription plan creation failed: {e}")
            raise

    async def create_subscription(
        self,
        subscription_request: SubscriptionRequest
    ) -> Dict[str, Any]:
        """Create a subscription for a user."""
        try:
            # Convert billing cycle to PayPal frequency
            frequency = self._convert_billing_cycle_to_frequency(subscription_request.billing_cycle)

            billing_agreement = paypalrestsdk.BillingAgreement({
                "name": "FlipSync Subscription Agreement",
                "description": "Subscription for FlipSync services",
                "start_date": datetime.utcnow().isoformat(),
                "plan": {"id": subscription_request.plan_id},
                "payer": {
                    "payment_method": "paypal",
                    "payer_info": subscription_request.payment_method
                },
                "override_merchant_preferences": {"frequency": frequency},
            })

            if billing_agreement.create():
                await self.metrics_service.increment_counter("subscriptions_created")
                
                # Generate invoice if requested
                invoice_data = None
                if subscription_request.generate_invoice and self.invoice_generator:
                    invoice_data = await self.invoice_generator.generate_subscription_invoice(
                        user_id=subscription_request.user_id,
                        subscription_id=billing_agreement.id,
                        plan_id=subscription_request.plan_id,
                        billing_cycle=subscription_request.billing_cycle,
                    )

                # Send notification
                await self.notification_service.send_notification(
                    subscription_request.user_id,
                    "Your FlipSync subscription has been created successfully!"
                )

                return {
                    "subscription_id": billing_agreement.id,
                    "status": "active",
                    "user_id": subscription_request.user_id,
                    "plan_id": subscription_request.plan_id,
                    "billing_cycle": subscription_request.billing_cycle,
                    "invoice": invoice_data,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            else:
                await self.metrics_service.track_error("subscription_creation_failed", str(billing_agreement.error))
                raise Exception(f"Subscription creation failed: {billing_agreement.error}")

        except Exception as e:
            await self.metrics_service.track_error("subscription_creation_error", str(e))
            logger.error(f"Subscription creation failed: {e}")
            raise

    def _convert_billing_cycle_to_frequency(self, billing_cycle: BillingCycle) -> str:
        """Convert billing cycle to PayPal frequency."""
        frequency_map = {
            BillingCycle.MONTHLY: "MONTH",
            BillingCycle.YEARLY: "YEAR",
        }
        return frequency_map.get(billing_cycle, "MONTH")

    async def cancel_subscription(
        self,
        subscription_id: str,
        user_id: str,
        reason: str = "Customer requested cancellation",
        cancel_invoices: bool = True,
    ) -> Dict[str, Any]:
        """Cancel a subscription."""
        try:
            billing_agreement = paypalrestsdk.BillingAgreement.find(subscription_id)
            
            if billing_agreement.cancel({"note": reason}):
                await self.metrics_service.increment_counter("subscriptions_cancelled")
                
                # Cancel pending invoices if requested
                if cancel_invoices and self.invoice_generator:
                    await self.invoice_generator.cancel_subscription_invoices(subscription_id)

                # Send notification
                await self.notification_service.send_notification(
                    user_id,
                    "Your FlipSync subscription has been cancelled."
                )

                return {
                    "subscription_id": subscription_id,
                    "status": "cancelled",
                    "cancelled_at": datetime.now(timezone.utc).isoformat(),
                    "reason": reason,
                }
            else:
                await self.metrics_service.track_error("subscription_cancellation_failed", str(billing_agreement.error))
                raise Exception(f"Subscription cancellation failed: {billing_agreement.error}")

        except Exception as e:
            await self.metrics_service.track_error("subscription_cancellation_error", str(e))
            logger.error(f"Subscription cancellation failed: {e}")
            raise

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get the status of a payment."""
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            return {
                "payment_id": payment_id,
                "status": payment.state,
                "amount": payment.transactions[0].amount.total,
                "currency": payment.transactions[0].amount.currency,
                "created_at": payment.create_time,
                "updated_at": payment.update_time,
            }
        except Exception as e:
            await self.metrics_service.track_error("payment_status_error", str(e))
            logger.error(f"Failed to get payment status: {e}")
            raise

    async def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get the status of a subscription."""
        try:
            billing_agreement = paypalrestsdk.BillingAgreement.find(subscription_id)
            return {
                "subscription_id": subscription_id,
                "status": billing_agreement.state,
                "name": billing_agreement.name,
                "description": billing_agreement.description,
                "start_date": billing_agreement.start_date,
                "plan_id": billing_agreement.plan.id if billing_agreement.plan else None,
            }
        except Exception as e:
            await self.metrics_service.track_error("subscription_status_error", str(e))
            logger.error(f"Failed to get subscription status: {e}")
            raise

    async def process_refund(
        self,
        payment_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "Customer requested refund",
    ) -> Dict[str, Any]:
        """Process a refund for a payment."""
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            sale = payment.transactions[0].related_resources[0].sale
            
            refund_data = {"note_to_payer": reason}
            if amount:
                refund_data["amount"] = {
                    "total": str(amount),
                    "currency": payment.transactions[0].amount.currency
                }
            
            refund = sale.refund(refund_data)
            
            if refund:
                await self.metrics_service.increment_counter("refunds_processed")
                return {
                    "refund_id": refund.id,
                    "status": refund.state,
                    "amount": refund.amount.total,
                    "currency": refund.amount.currency,
                    "reason": reason,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }
            else:
                await self.metrics_service.track_error("refund_failed", "Refund creation failed")
                raise Exception("Refund processing failed")

        except Exception as e:
            await self.metrics_service.track_error("refund_error", str(e))
            logger.error(f"Refund processing failed: {e}")
            raise

    async def get_payment_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get payment history for a user."""
        try:
            # This would typically query a database for user payments
            # For now, return a placeholder structure
            return {
                "user_id": user_id,
                "payments": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            await self.metrics_service.track_error("payment_history_error", str(e))
            logger.error(f"Failed to get payment history: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on payment service."""
        try:
            # Test PayPal API connectivity
            paypalrestsdk.Payment.all({"count": 1})
            
            return {
                "status": "healthy",
                "provider": "paypal",
                "sandbox_mode": self.sandbox_mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            await self.metrics_service.track_error("health_check_failed", str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


# Export all classes
__all__ = [
    "UnifiedPaymentService",
    "PaymentProvider",
    "PaymentStatus", 
    "PaymentType",
    "PaymentRequest",
    "PaymentResponse",
    "SubscriptionRequest",
]
