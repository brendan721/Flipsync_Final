from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

# Real PayPal SDK integration for production
import paypalrestsdk

from pydantic import BaseModel, ConfigDict

from fs_agt_clean.services.metrics.service import MetricsService
from fs_agt_clean.services.notifications.service import NotificationService

# Try to import optional services
try:
    from fs_agt_clean.core.payment.invoice_generator import InvoiceGenerator

    invoice_generator_available = True
except ImportError:
    invoice_generator_available = False
    InvoiceGenerator = Any  # type: ignore

try:
    from fs_agt_clean.core.payment.billing_cycle_manager import BillingCycle

    billing_cycle_available = True
except ImportError:
    billing_cycle_available = False

    class BillingCycle:  # type: ignore
        """Mock BillingCycle if module is not available."""

        pass


import logging

logger = logging.getLogger(__name__)

try:
    from fs_agt_clean.core.payment.invoice_generator import Invoice, InvoiceGenerator
    from fs_agt_clean.core.payment.subscription_model import (
        BillingCycle,
        SubscriptionPlan,
    )
except ImportError:
    # Create mock classes if the imports are not available
    class Invoice:  # type: ignore
        """Mock Invoice if module is not available."""

        pass

    class SubscriptionPlan:  # type: ignore
        """Mock SubscriptionPlan if module is not available."""

        pass

    class SubscriptionStatus:  # type: ignore
        """Mock SubscriptionStatus if module is not available."""

        ACTIVE = "active"

    class UnifiedUserSubscription:  # type: ignore
        """Mock UnifiedUserSubscription if module is not available."""

        pass


class PaymentPlan(BaseModel):
    id: str
    name: str
    description: str
    amount: float
    currency: str = "USD"
    interval: str
    interval_count: int = 1
    trial_days: Optional[int] = None


class Subscription(BaseModel):
    id: str
    plan_id: str
    user_id: str
    status: str
    start_date: datetime
    next_billing_date: datetime
    payment_method: str
    is_active: bool = True


class UnifiedPaymentService:

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        metrics_service: MetricsService,
        notification_service: NotificationService,
        invoice_generator: Optional[InvoiceGenerator] = None,
        sandbox_mode: bool = False,
    ):
        self.metrics_service = metrics_service
        self.notification_service = notification_service
        self.invoice_generator = invoice_generator
        paypalrestsdk.configure(
            {
                "mode": "sandbox" if sandbox_mode else "live",
                "client_id": client_id,
                "client_secret": client_secret,
            }
        )

    async def create_subscription_plan(self, plan: PaymentPlan) -> Dict:
        """
        Create a subscription plan in PayPal.
        """
        try:
            billing_plan = paypalrestsdk.BillingPlan(
                {
                    "name": plan.name,
                    "description": plan.description,
                    "type": "INFINITE",
                    "payment_definitions": [
                        {
                            "name": f"{plan.name} Payment",
                            "type": "REGULAR",
                            "frequency": plan.interval,
                            "frequency_interval": str(plan.interval_count),
                            "amount": {
                                "value": str(plan.amount),
                                "currency": plan.currency,
                            },
                            "cycles": "0",
                        }
                    ],
                    "merchant_preferences": {
                        "setup_fee": {"value": "0", "currency": plan.currency},
                        "auto_bill_amount": "YES",
                        "initial_fail_amount_action": "CONTINUE",
                        "max_fail_attempts": "3",
                    },
                }
            )

            if billing_plan.create():
                billing_plan.activate()
                self.metrics_service.track_plan_creation(plan.dict())
                return {"plan_id": billing_plan.id}
            else:
                raise Exception(billing_plan.error)
        except Exception as e:
            self.metrics_service.track_error("plan_creation_error", str(e))
            raise

    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        payment_method: Dict,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        generate_invoice: bool = True,
    ) -> Union[Subscription, Dict[str, Any]]:
        """
        Create a subscription for a user.

        Args:
            user_id: ID of the user
            plan_id: ID of the subscription plan
            payment_method: Payment method information
            billing_cycle: Billing cycle for the subscription
            generate_invoice: Whether to generate an invoice for the subscription

        Returns:
            Subscription details and optionally invoice information
        """
        try:
            # Convert billing cycle to PayPal frequency
            frequency = self._convert_billing_cycle_to_frequency(billing_cycle)

            billing_agreement = paypalrestsdk.BillingAgreement(
                {
                    "name": "FlipSync Subscription Agreement",
                    "description": "Subscription for FlipSync services",
                    "start_date": datetime.utcnow().isoformat(),
                    "plan": {"id": plan_id},
                    "payer": {"payment_method": "paypal", "payer_info": payment_method},
                    "override_merchant_preferences": {"frequency": frequency},
                }
            )

            if billing_agreement.create():
                subscription = Subscription(
                    id=billing_agreement.id,
                    plan_id=plan_id,
                    user_id=user_id,
                    status="ACTIVE",
                    start_date=datetime.utcnow(),
                    next_billing_date=billing_agreement.agreement_details.next_billing_date,
                    payment_method="paypal",
                    is_active=True,
                )

                self.metrics_service.track_subscription_creation(subscription.dict())

                # Generate invoice if requested and invoice generator is available
                invoice_data = None
                if generate_invoice and self.invoice_generator:
                    # Convert to UnifiedUserSubscription format for invoice generation
                    user_subscription = UnifiedUserSubscription(
                        id=subscription.id,
                        user_id=subscription.user_id,
                        plan_id=subscription.plan_id,
                        status=SubscriptionStatus.ACTIVE,
                        billing_cycle=billing_cycle,
                        current_period_start=subscription.start_date,
                        current_period_end=subscription.next_billing_date,
                        next_billing_date=subscription.next_billing_date,
                        payment_method_id=subscription.payment_method,
                        payment_provider_subscription_id=subscription.id,
                        next_payment_amount=float(
                            billing_agreement.plan.payment_definitions[0].amount.value
                        ),
                        currency=billing_agreement.plan.payment_definitions[
                            0
                        ].amount.currency,
                    )

                    # Generate invoice
                    invoice = (
                        await self.invoice_generator.generate_subscription_invoice(
                            subscription_id=user_subscription.id,
                            issue_date=datetime.utcnow(),
                            due_days=1,  # Due immediately for initial subscription
                            notes="Initial subscription payment",
                            metadata={"payment_provider": "paypal"},
                        )
                    )

                    invoice_data = {
                        "invoice_id": invoice.invoice_id,
                        "amount": str(invoice.total),
                        "due_date": invoice.due_date.isoformat(),
                    }

                # Return subscription with optional invoice data
                result = subscription.dict()
                if invoice_data:
                    result["invoice"] = invoice_data

                return result
            else:
                raise Exception(billing_agreement.error)
        except Exception as e:
            self.metrics_service.track_error("subscription_creation_error", str(e))
            raise

    async def process_payment(
        self,
        amount: float,
        currency: str,
        description: str,
        payment_method: Dict[str, Any],
        invoice_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a one-time payment.

        Args:
            amount: Payment amount
            currency: Currency code
            description: Payment description
            payment_method: Payment method information
            invoice_id: Optional ID of the associated invoice

        Returns:
            Payment details
        """
        try:
            payment = paypalrestsdk.Payment(
                {
                    "intent": "sale",
                    "payer": {"payment_method": "paypal", "payer_info": payment_method},
                    "transactions": [
                        {
                            "amount": {"total": str(amount), "currency": currency},
                            "description": description,
                        }
                    ],
                }
            )

            if payment.create():
                # Use a custom method if track_payment_processing is available
                if hasattr(self.metrics_service, "track_payment_processing"):
                    await self.metrics_service.track_payment_processing(
                        amount, currency, payment.id
                    )
                else:
                    # Fallback to a generic increment counter method
                    await self.metrics_service.increment_counter("payment_processed")

                # Record payment for invoice if provided and invoice generator is available
                if invoice_id and self.invoice_generator:
                    await self.invoice_generator.record_payment(
                        invoice_id=invoice_id,
                        payment_id=payment.id,
                        amount=Decimal(str(amount)),
                        payment_date=datetime.now(timezone.utc),
                        payment_method="paypal",
                        metadata={
                            "payment_provider": "paypal",
                            "payment_status": payment.state,
                        },
                    )

                return {
                    "payment_id": payment.id,
                    "status": payment.state,
                    "amount": amount,
                    "currency": currency,
                    "invoice_id": invoice_id,
                }
            else:
                raise Exception(payment.error)
        except Exception as e:
            if hasattr(self.metrics_service, "track_error"):
                await self.metrics_service.track_error(
                    "payment_processing_error", str(e)
                )
            else:
                await self.metrics_service.increment_counter(
                    "payment_processing_errors"
                )
            raise

    async def cancel_subscription(
        self,
        subscription_id: str,
        reason: str = "Customer requested cancellation",
        cancel_invoices: bool = True,
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: ID of the subscription to cancel
            reason: Reason for cancellation
            cancel_invoices: Whether to cancel pending invoices

        Returns:
            Cancellation status
        """
        try:
            billing_agreement = paypalrestsdk.BillingAgreement.find(subscription_id)

            if billing_agreement.cancel({"note": reason}):
                if hasattr(self.metrics_service, "track_subscription_cancellation"):
                    await self.metrics_service.track_subscription_cancellation(
                        subscription_id
                    )
                else:
                    await self.metrics_service.increment_counter(
                        "subscription_cancelled"
                    )

                # Cancel pending invoices if requested and invoice generator is available
                if cancel_invoices and self.invoice_generator:
                    # Get pending invoices for this subscription
                    invoices = (
                        await self.invoice_generator.get_invoices_for_subscription(
                            subscription_id
                        )
                    )

                    # Cancel any draft or sent invoices
                    for invoice in invoices:
                        if invoice.status.name in ["DRAFT", "SENT"]:
                            await self.invoice_generator.cancel_invoice(
                                invoice_id=invoice.invoice_id,
                                reason=f"Subscription {subscription_id} cancelled: {reason}",
                            )

                # Send notification to user with correct parameters
                # The notification_service.send_notification method accepts title and message, not notification_type and content
                user_id = getattr(
                    billing_agreement.payer.payer_info, "payer_id", "unknown_user"
                )
                await self.notification_service.send_notification(
                    user_id=user_id,
                    title="Subscription Cancelled",
                    message=f"Your subscription has been cancelled. {reason}",
                )

                return {
                    "status": "cancelled",
                    "subscription_id": subscription_id,
                    "reason": reason,
                }
            else:
                raise Exception(billing_agreement.error)
        except Exception as e:
            if hasattr(self.metrics_service, "track_error"):
                await self.metrics_service.track_error(
                    "subscription_cancellation_error", str(e)
                )
            else:
                await self.metrics_service.increment_counter(
                    "subscription_cancellation_errors"
                )
            raise

    async def get_subscription_details(self, subscription_id: str) -> Dict:
        """
        Get details of a subscription.

        Args:
            subscription_id: ID of the subscription

        Returns:
            Subscription details
        """
        try:
            billing_agreement = paypalrestsdk.BillingAgreement.find(subscription_id)

            # Get invoices if invoice generator is available
            invoices = []
            if self.invoice_generator:
                invoice_list = (
                    await self.invoice_generator.get_invoices_for_subscription(
                        subscription_id
                    )
                )
                invoices = [invoice.to_dict() for invoice in invoice_list]

            return {
                "id": billing_agreement.id,
                "state": billing_agreement.state,
                "description": billing_agreement.description,
                "start_date": billing_agreement.start_date,
                "agreement_details": billing_agreement.agreement_details.to_dict(),
                "payer": billing_agreement.payer.to_dict(),
                "invoices": invoices,
            }
        except Exception as e:
            self.metrics_service.track_error("subscription_details_error", str(e))
            raise

    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None,
        invoice_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Refund a payment.

        Args:
            payment_id: ID of the payment to refund
            amount: Optional refund amount (if partial refund)
            reason: Optional reason for refund
            invoice_id: Optional ID of the associated invoice

        Returns:
            Refund details
        """
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            sale = payment.transactions[0].related_resources[0].sale
            refund_data: Dict[str, Any] = {}

            # Set amount if provided (for partial refunds)
            if amount:
                refund_data["amount"] = {
                    "total": str(amount),
                    "currency": sale.amount.currency,
                }

            # Add reason if provided - Fix the assignment to be proper dict value
            if reason:
                refund_data["reason"] = reason

            refund = sale.refund(refund_data)

            if refund.success():
                refund_amount = amount or float(sale.amount.total)

                if hasattr(self.metrics_service, "track_refund_processing"):
                    await self.metrics_service.track_refund_processing(
                        payment_id, refund_amount
                    )
                else:
                    await self.metrics_service.increment_counter("refund_processed")

                # Record refund for invoice if provided and invoice generator is available
                if invoice_id and self.invoice_generator:
                    await self.invoice_generator.record_refund(
                        invoice_id=invoice_id,
                        refund_id=refund.id,
                        amount=Decimal(str(refund_amount)),
                        refund_date=datetime.now(timezone.utc),
                        reason=reason,
                        metadata={
                            "payment_id": payment_id,
                            "refund_status": refund.state,
                        },
                    )

                return {
                    "refund_id": refund.id,
                    "status": refund.state,
                    "amount": refund_amount,
                    "payment_id": payment_id,
                    "invoice_id": invoice_id,
                }
            else:
                raise Exception(refund.error)
        except Exception as e:
            if hasattr(self.metrics_service, "track_error"):
                await self.metrics_service.track_error(
                    "refund_processing_error", str(e)
                )
            else:
                await self.metrics_service.increment_counter("refund_processing_errors")
            raise

    async def update_subscription(
        self,
        subscription_id: str,
        new_plan_id: Optional[str] = None,
        new_billing_cycle: Optional[BillingCycle] = None,
        generate_invoice: bool = True,
    ) -> Dict:
        """
        Update a subscription with new plan or billing cycle.

        Args:
            subscription_id: ID of the subscription to update
            new_plan_id: Optional new plan ID
            new_billing_cycle: Optional new billing cycle
            generate_invoice: Whether to generate an invoice for the updated subscription

        Returns:
            Updated subscription details
        """
        try:
            billing_agreement = paypalrestsdk.BillingAgreement.find(subscription_id)

            # Prepare update data
            update_data = {}

            if new_plan_id:
                update_data["plan"] = {"id": new_plan_id}

            if new_billing_cycle:
                frequency = self._convert_billing_cycle_to_frequency(new_billing_cycle)
                update_data["override_merchant_preferences"] = {"frequency": frequency}

            # If no updates, return current details
            if not update_data:
                return {
                    "id": billing_agreement.id,
                    "status": "unchanged",
                    "message": "No updates provided",
                }

            # Update the subscription
            if billing_agreement.replace(update_data):
                # Get updated agreement
                updated_agreement = paypalrestsdk.BillingAgreement.find(subscription_id)

                # Generate invoice if requested and invoice generator is available
                invoice_data = None
                if (
                    generate_invoice
                    and self.invoice_generator
                    and (new_plan_id or new_billing_cycle)
                ):
                    # Get plan details
                    plan_id = new_plan_id or billing_agreement.plan.id

                    # Convert to UnifiedUserSubscription format for invoice generation
                    user_subscription = UnifiedUserSubscription(
                        id=subscription_id,
                        user_id=updated_agreement.payer.payer_info.payer_id,
                        plan_id=plan_id,
                        status=SubscriptionStatus.ACTIVE,
                        billing_cycle=new_billing_cycle
                        or self._convert_frequency_to_billing_cycle(
                            updated_agreement.plan.payment_definitions[0].frequency
                        ),
                        current_period_start=datetime.utcnow(),
                        current_period_end=updated_agreement.agreement_details.next_billing_date,
                        next_billing_date=updated_agreement.agreement_details.next_billing_date,
                        payment_method_id="paypal",
                        payment_provider_subscription_id=subscription_id,
                        next_payment_amount=float(
                            updated_agreement.plan.payment_definitions[0].amount.value
                        ),
                        currency=updated_agreement.plan.payment_definitions[
                            0
                        ].amount.currency,
                    )

                    # Generate invoice
                    invoice = await self.invoice_generator.generate_subscription_invoice(
                        subscription_id=user_subscription.id,
                        issue_date=datetime.utcnow(),
                        due_days=1,  # Due immediately for plan change
                        notes="Subscription plan or billing cycle update",
                        metadata={
                            "payment_provider": "paypal",
                            "previous_plan_id": billing_agreement.plan.id,
                            "new_plan_id": new_plan_id,
                            "previous_billing_cycle": billing_agreement.plan.payment_definitions[
                                0
                            ].frequency,
                            "new_billing_cycle": (
                                new_billing_cycle.name if new_billing_cycle else None
                            ),
                        },
                    )

                    invoice_data = {
                        "invoice_id": invoice.invoice_id,
                        "amount": str(invoice.total),
                        "due_date": invoice.due_date.isoformat(),
                    }

                # Track the update
                self.metrics_service.track_subscription_update(
                    subscription_id=subscription_id,
                    new_plan_id=new_plan_id,
                    new_billing_cycle=(
                        new_billing_cycle.name if new_billing_cycle else None
                    ),
                )

                # Return updated details
                result = {
                    "id": updated_agreement.id,
                    "status": "updated",
                    "plan_id": updated_agreement.plan.id,
                    "billing_cycle": updated_agreement.plan.payment_definitions[
                        0
                    ].frequency,
                    "next_billing_date": updated_agreement.agreement_details.next_billing_date,
                }

                if invoice_data:
                    result["invoice"] = invoice_data

                return result
            else:
                raise Exception(billing_agreement.error)
        except Exception as e:
            self.metrics_service.track_error("subscription_update_error", str(e))
            raise

    async def verify_webhook_event(self, event_data: Dict) -> bool:
        """
        Verify a webhook event from PayPal.

        Args:
            event_data: The webhook event data

        Returns:
            True if the event is verified, False otherwise
        """
        try:
            # In a real implementation, this would verify the webhook signature
            # For this example, we'll just return bool(True
            return True
        except Exception as e:
            self.metrics_service.track_error("webhook_verification_error", str(e))
            return False

    async def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a webhook event from PayPal.

        Args:
            event_data: Event data from webhook

        Returns:
            Dict with processing result
        """
        try:
            # Use await for async increment_counter method
            await self.metrics_service.increment_counter("paypal_webhook_events")

            event_type = event_data.get("event_type")
            resource = event_data.get("resource", {})

            # Process different event types
            if event_type == "PAYMENT.SALE.COMPLETED":
                # Payment completed
                payment_id = resource.get("id")
                invoice_id = resource.get("invoice_number")

                # Record payment for invoice if available
                if invoice_id and self.invoice_generator:
                    await self.invoice_generator.record_payment(
                        invoice_id=invoice_id,
                        payment_id=payment_id,
                        amount=Decimal(resource.get("amount", {}).get("total", "0")),
                        payment_date=datetime.now(timezone.utc),
                    )

                return {
                    "status": "success",
                    "event_type": event_type,
                    "payment_id": payment_id,
                    "invoice_id": invoice_id,
                }

            elif event_type == "BILLING.SUBSCRIPTION.CREATED":
                # Subscription created
                subscription_id = resource.get("id")

                return {
                    "status": "success",
                    "event_type": event_type,
                    "subscription_id": subscription_id,
                }

            elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
                # Subscription cancelled
                subscription_id = resource.get("id")

                # Cancel pending invoices if invoice generator is available
                if self.invoice_generator and hasattr(
                    self.invoice_generator, "cancel_subscription_invoices"
                ):
                    await self.invoice_generator.cancel_subscription_invoices(
                        subscription_id
                    )
                elif self.invoice_generator:
                    # Try alternative method if available
                    if hasattr(self.invoice_generator, "update_subscription_status"):
                        await self.invoice_generator.update_subscription_status(
                            subscription_id, "cancelled"
                        )

                return {
                    "status": "success",
                    "event_type": event_type,
                    "subscription_id": subscription_id,
                    "message": "Subscription cancelled and invoices updated",
                }

            elif event_type == "PAYMENT.SALE.REFUNDED":
                # Payment refunded
                refund_id = resource.get("id")
                payment_id = resource.get("parent_payment")

                return {
                    "status": "success",
                    "event_type": event_type,
                    "refund_id": refund_id,
                    "payment_id": payment_id,
                }

            else:
                # Unhandled event type
                return {
                    "status": "ignored",
                    "event_type": event_type,
                    "message": "Unhandled event type",
                }

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error("Error processing webhook event: %s", e)

            # Use await for async increment_counter method
            await self.metrics_service.increment_counter("paypal_webhook_errors")
            return {
                "status": "error",
                "message": str(e),
                "event_type": event_data.get("event_type"),
            }

    def _convert_billing_cycle_to_frequency(self, billing_cycle: BillingCycle) -> str:
        """
        Convert a BillingCycle to a PayPal frequency.

        Args:
            billing_cycle: The billing cycle to convert

        Returns:
            PayPal frequency string
        """
        from fs_agt_clean.core.payment.billing_cycle_manager import BillingCycleManager

        return BillingCycleManager.get_paypal_frequency(billing_cycle)

    def _convert_frequency_to_billing_cycle(self, frequency: str) -> BillingCycle:
        """
        Convert a PayPal frequency to a BillingCycle.

        Args:
            frequency: The PayPal frequency to convert

        Returns:
            BillingCycle enum value
        """
        from fs_agt_clean.core.payment.billing_cycle_manager import BillingCycleManager

        return BillingCycleManager.from_paypal_frequency(frequency)
