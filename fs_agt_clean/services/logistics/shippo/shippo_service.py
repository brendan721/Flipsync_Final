"""Shippo shipping service implementation."""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

try:
    import shippo
except ImportError:
    raise ImportError(
        "shippo package is required for shipping functionality. "
        "Please install it with: pip install shippo"
    )

from pydantic import BaseModel, ConfigDict

from fs_agt_clean.core.monitoring.exporters.prometheus import (
    API_ERROR_COUNT,
    REQUEST_COUNT as API_REQUEST_COUNT,
    REQUEST_LATENCY as API_REQUEST_DURATION,
)
from fs_agt_clean.services.metrics.service import MetricsService
from fs_agt_clean.services.notifications.service import (
    NotificationCategory,
    NotificationPriority,
    NotificationService,
)


class ShippingDimensions(BaseModel):
    length: float
    width: float
    height: float
    weight: float
    distance_unit: str = "in"
    mass_unit: str = "lb"


class ShippingRate(BaseModel):
    provider: str
    service: str
    amount: float
    currency: str = "USD"
    days: int
    trackable: bool
    insurance_amount: Optional[float] = None
    provider_image: Optional[str] = None
    estimated_days: Optional[int] = None
    arrives_by: Optional[datetime] = None


class ShippoService:
    def __init__(
        self,
        api_key: str,
        metrics_service: Optional[MetricsService] = None,
        notification_service: Optional[NotificationService] = None,
        test_mode: bool = False,
    ):
        """Initialize Shippo service.

        Args:
            api_key: Shippo API key
            metrics_service: Optional metrics service for tracking
            notification_service: Optional notification service
            test_mode: Whether to use test mode
        """
        self.metrics_service = metrics_service
        self.notification_service = notification_service
        self.test_mode = test_mode
        self.logger = logging.getLogger(__name__)

        # Initialize modern Shippo SDK v3.9.0 client
        self.client = shippo.Shippo(api_key_header=api_key)

        # For legacy compatibility, also set global config
        shippo.api_key = api_key
        shippo.test = test_mode

    def _validate_shippo_address(self, address: Dict[str, str]) -> Dict[str, str]:
        """Validate and format address for Shippo API requirements."""
        # Shippo requires specific field names
        validated_address = {}

        # Required fields mapping
        field_mapping = {
            "name": ["name", "company", "contact_name"],
            "street1": ["street1", "street", "address", "address_line_1"],
            "city": ["city"],
            "state": ["state", "province", "region"],
            "zip": ["zip", "postal_code", "zip_code"],
            "country": ["country", "country_code"],
        }

        # Map fields to Shippo format
        for shippo_field, possible_fields in field_mapping.items():
            for field in possible_fields:
                if field in address and address[field]:
                    validated_address[shippo_field] = str(address[field]).strip()
                    break

        # Set defaults for missing required fields
        if "name" not in validated_address:
            validated_address["name"] = "FlipSync Customer"
        if "country" not in validated_address:
            validated_address["country"] = "US"

        # Optional fields
        optional_mapping = {
            "street2": ["street2", "address_line_2", "apt", "suite"],
            "phone": ["phone", "phone_number"],
            "email": ["email", "email_address"],
        }

        for shippo_field, possible_fields in optional_mapping.items():
            for field in possible_fields:
                if field in address and address[field]:
                    validated_address[shippo_field] = str(address[field]).strip()
                    break

        return validated_address

    async def calculate_shipping_rates(
        self,
        dimensions: ShippingDimensions,
        from_address: Dict[str, str],
        to_address: Dict[str, str],
        insurance_amount: Optional[float] = None,
        signature_required: bool = False,
    ) -> List[ShippingRate]:
        """Calculate shipping rates based on dimensions and addresses."""
        try:
            API_REQUEST_COUNT.labels(
                endpoint="shipping_rates", method="POST", client_id="shippo"
            ).inc()
            start_time = time.time()

            # Validate and format addresses for Shippo API
            validated_from_address = self._validate_shippo_address(from_address)
            validated_to_address = self._validate_shippo_address(to_address)

            parcel = {
                "length": dimensions.length,
                "width": dimensions.width,
                "height": dimensions.height,
                "distance_unit": dimensions.distance_unit,
                "weight": dimensions.weight,
                "mass_unit": dimensions.mass_unit,
            }

            try:
                # Use modern Shippo SDK v3.9.0 client with validated addresses
                shipment_request = {
                    "address_from": validated_from_address,
                    "address_to": validated_to_address,
                    "parcels": [parcel],
                    "async": False,
                }

                if insurance_amount:
                    shipment_request["insurance_amount"] = str(insurance_amount)
                    shipment_request["insurance_currency"] = "USD"

                if signature_required:
                    shipment_request["extra"] = {"signature_confirmation": True}

                # Use legacy API for better compatibility with test environment
                # Modern client can be enabled for production deployment
                shipment = shippo.Shipment.create(**shipment_request)

            except Exception as e:
                raise ValueError(f"Failed to create shipment: {str(e)}")

            API_REQUEST_DURATION.labels(
                endpoint="shipping_rates", method="POST"
            ).observe(time.time() - start_time)

            if not shipment.rates:
                raise ValueError("No shipping rates available for the given parameters")

            rates = []
            for rate in shipment.rates:
                shipping_rate = ShippingRate(
                    provider=rate.provider,
                    service=rate.servicelevel.name,
                    amount=float(rate.amount),
                    currency=rate.currency,
                    days=rate.days,
                    trackable=rate.attributes and "TRACKING" in rate.attributes,
                    insurance_amount=insurance_amount,
                    provider_image=rate.provider_image_75,
                    estimated_days=rate.estimated_days,
                    arrives_by=rate.arrives_by if hasattr(rate, "arrives_by") else None,
                )
                rates.append(shipping_rate)

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="shipping_rates_calculated",
                    value=1.0,
                    labels={
                        "success": "true",
                        "rates_count": str(len(rates)),
                        "has_insurance": str(bool(insurance_amount)).lower(),
                    },
                )

            return rates

        except Exception as e:
            self.logger.error("Error calculating shipping rates: %s", str(e))
            API_ERROR_COUNT.labels(
                endpoint="shipping_rates",
                error_type=type(e).__name__,
                client_id="shippo",
            ).inc()

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="shipping_rates_calculated",
                    value=1.0,
                    labels={
                        "success": "false",
                        "error": str(e),
                    },
                )

            if self.notification_service:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="shipping_rates_error",
                    category=NotificationCategory.PIPELINE_ERROR,
                    data={
                        "dimensions": dimensions.dict(),
                        "from_address": from_address,
                        "to_address": to_address,
                        "error": str(e),
                        "timestamp": str(int(time.time())),
                    },
                    priority=NotificationPriority.HIGH,
                )

            raise

    async def compare_with_ebay_rates(
        self,
        dimensions: ShippingDimensions,
        ebay_rates: List[Dict],
        from_address: Dict[str, str],
        to_address: Dict[str, str],
    ) -> Dict[str, List[ShippingRate]]:
        """
        Compare Shippo rates with eBay rates and find optimal options.
        """
        try:
            shippo_rates = await self.calculate_shipping_rates(
                dimensions, from_address, to_address
            )
            ebay_shipping_rates = [
                ShippingRate(
                    provider="eBay",
                    service=rate["service_name"],
                    amount=float(rate["total_cost"]),
                    currency=rate["currency"],
                    days=rate.get("delivery_days", 7),
                    trackable=rate.get("trackable", True),
                )
                for rate in ebay_rates
            ]
            optimal_rates = self._find_optimal_rates(shippo_rates, ebay_shipping_rates)
            return {
                "shippo_rates": shippo_rates,
                "ebay_rates": ebay_shipping_rates,
                "optimal_rates": optimal_rates,
            }
        except Exception as e:
            self.metrics_service.track_error("rate_comparison_error", str(e))
            raise

    def _find_optimal_rates(
        self, shippo_rates: List[ShippingRate], ebay_rates: List[ShippingRate]
    ) -> List[ShippingRate]:
        """
        Find the most cost-effective shipping options.
        """
        optimal_rates = []
        speed_categories = {"express": [], "priority": [], "standard": []}
        for rate in shippo_rates:
            if rate.days <= 2:
                speed_categories["express"].append(rate)
            elif rate.days <= 3:
                speed_categories["priority"].append(rate)
            else:
                speed_categories["standard"].append(rate)
        for rate in ebay_rates:
            if rate.days <= 2:
                speed_categories["express"].append(rate)
            elif rate.days <= 3:
                speed_categories["priority"].append(rate)
            else:
                speed_categories["standard"].append(rate)
        for category, rates in speed_categories.items():
            if rates:
                rates.sort(key=lambda x: x.amount)
                optimal_rates.append(rates[0])
        return optimal_rates

    async def validate_address(self, address: Dict[str, str]) -> Dict[str, Any]:
        """Validate shipping address using Shippo API."""
        try:
            API_REQUEST_COUNT.labels(
                endpoint="validate_address", method="POST", client_id="shippo"
            ).inc()
            start_time = time.time()

            try:
                validation = shippo.Address.validate(address)
            except Exception as e:
                raise ValueError(f"Failed to validate address: {str(e)}")

            API_REQUEST_DURATION.labels(
                endpoint="validate_address", method="POST"
            ).observe(time.time() - start_time)

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="address_validation",
                    value=1.0,
                    labels={
                        "success": "true",
                        "is_valid": str(validation.validation_results.is_valid).lower(),
                    },
                )

            return {
                "is_valid": validation.validation_results.is_valid,
                "messages": validation.validation_results.messages,
                "suggested_address": (
                    validation.validation_results.address
                    if hasattr(validation.validation_results, "address")
                    else None
                ),
            }

        except Exception as e:
            self.logger.error("Error validating address: %s", str(e))
            API_ERROR_COUNT.labels(
                endpoint="validate_address",
                error_type=type(e).__name__,
                client_id="shippo",
            ).inc()

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="address_validation",
                    value=1.0,
                    labels={
                        "success": "false",
                        "error": str(e),
                    },
                )

            if self.notification_service:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="address_validation_error",
                    category=NotificationCategory.PIPELINE_ERROR,
                    data={
                        "address": address,
                        "error": str(e),
                        "timestamp": str(int(time.time())),
                    },
                    priority=NotificationPriority.HIGH,
                )

            raise

    async def create_shipping_label(
        self,
        rate_id: str,
        from_address: Dict[str, str],
        to_address: Dict[str, str],
        parcel: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a shipping label using Shippo API."""
        try:
            API_REQUEST_COUNT.labels(
                endpoint="create_label", method="POST", client_id="shippo"
            ).inc()
            start_time = time.time()

            try:
                transaction = shippo.Transaction.create(
                    rate=rate_id,
                    label_file_type="PDF",
                    async_=False,
                )
            except Exception as e:
                raise ValueError(f"Failed to create label: {str(e)}")

            API_REQUEST_DURATION.labels(endpoint="create_label", method="POST").observe(
                time.time() - start_time
            )

            if transaction.status != "SUCCESS":
                raise ValueError(f"Label creation failed: {transaction.messages}")

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="label_created",
                    value=1.0,
                    labels={
                        "success": "true",
                        "carrier": str(transaction.carrier),
                        "service": str(transaction.servicelevel.name),
                    },
                )

            return {
                "label_url": transaction.label_url,
                "tracking_number": transaction.tracking_number,
                "tracking_url_provider": transaction.tracking_url_provider,
                "eta": transaction.eta,
                "carrier": transaction.carrier,
                "service": transaction.servicelevel.name,
            }

        except Exception as e:
            self.logger.error("Error creating shipping label: %s", str(e))
            API_ERROR_COUNT.labels(
                endpoint="create_label",
                error_type=type(e).__name__,
                client_id="shippo",
            ).inc()

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="label_created",
                    value=1.0,
                    labels={
                        "success": "false",
                        "error": str(e),
                    },
                )

            if self.notification_service:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="label_creation_error",
                    category=NotificationCategory.PIPELINE_ERROR,
                    data={
                        "rate_id": rate_id,
                        "from_address": from_address,
                        "to_address": to_address,
                        "error": str(e),
                        "timestamp": str(int(time.time())),
                    },
                    priority=NotificationPriority.HIGH,
                )

            raise

    async def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """Track a shipment using Shippo API."""
        try:
            API_REQUEST_COUNT.labels(
                endpoint="track_shipment", method="GET", client_id=tracking_number
            ).inc()
            start_time = time.time()

            tracking = shippo.Track.get_status(tracking_number)

            API_REQUEST_DURATION.labels(
                endpoint="track_shipment", method="GET"
            ).observe(time.time() - start_time)

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="shipment_tracked",
                    value=1.0,
                    labels={
                        "success": "true",
                        "status": tracking.status,
                    },
                )

            return {
                "status": tracking.status,
                "status_details": tracking.status_details,
                "eta": tracking.eta,
                "tracking_history": tracking.tracking_history,
                "location": tracking.location,
                "exception": (
                    tracking.status_exception
                    if hasattr(tracking, "status_exception")
                    else None
                ),
            }

        except Exception as e:
            self.logger.error("Error tracking shipment %s: %s", tracking_number, str(e))
            API_ERROR_COUNT.labels(
                endpoint="track_shipment",
                error_type=type(e).__name__,
                client_id=tracking_number,
            ).inc()

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="shipment_tracked",
                    value=1.0,
                    labels={
                        "success": "false",
                        "error": str(e),
                    },
                )

            if self.notification_service:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="tracking_error",
                    category=NotificationCategory.PIPELINE_ERROR,
                    data={
                        "tracking_number": tracking_number,
                        "error": str(e),
                        "timestamp": str(int(time.time())),
                    },
                    priority=NotificationPriority.HIGH,
                )

            raise

    async def register_tracking_webhook(
        self, callback_url: str, event_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Register webhook for tracking updates."""
        try:
            if event_types is None:
                event_types = ["track_updated", "track_exception"]

            API_REQUEST_COUNT.labels(
                endpoint="register_webhook", method="POST", client_id="shippo"
            ).inc()
            start_time = time.time()

            webhook = shippo.Webhook.create(url=callback_url, event_types=event_types)

            API_REQUEST_DURATION.labels(
                endpoint="register_webhook", method="POST"
            ).observe(time.time() - start_time)

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="webhook_registered",
                    value=1.0,
                    labels={
                        "success": "true",
                        "url": callback_url,
                    },
                )

            return {
                "webhook_id": webhook.id,
                "url": webhook.url,
                "event_types": webhook.event_types,
            }

        except Exception as e:
            self.logger.error("Error registering webhook: %s", str(e))
            API_ERROR_COUNT.labels(
                endpoint="register_webhook",
                error_type=type(e).__name__,
                client_id="shippo",
            ).inc()

            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="webhook_registered",
                    value=1.0,
                    labels={
                        "success": "false",
                        "error": str(e),
                    },
                )

            if self.notification_service:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="webhook_registration_error",
                    category=NotificationCategory.PIPELINE_ERROR,
                    data={
                        "url": callback_url,
                        "error": str(e),
                        "timestamp": str(int(time.time())),
                    },
                    priority=NotificationPriority.HIGH,
                )

            raise

    async def process_tracking_webhook(self, webhook_data: Dict[str, Any]) -> None:
        """Process tracking webhook events."""
        try:
            event_type = webhook_data.get("event")
            tracking_data = webhook_data.get("data", {})

            if event_type == "track_updated":
                tracking_number = tracking_data.get("tracking_number")
                status = tracking_data.get("status")

                if self.metrics_service:
                    await self.metrics_service.record_metric(
                        name="tracking_updated",
                        value=1.0,
                        labels={
                            "tracking_number": tracking_number,
                            "status": status,
                        },
                    )

                if status == "DELIVERED":
                    await self.notification_service.send_notification(
                        user_id="system",
                        template_id="delivery_confirmation",
                        category=NotificationCategory.PIPELINE_ERROR,
                        data={
                            "tracking_number": tracking_number,
                            "status": status,
                            "timestamp": str(int(time.time())),
                        },
                        priority=NotificationPriority.LOW,
                    )

            elif event_type == "track_exception":
                tracking_number = tracking_data.get("tracking_number")
                exception = tracking_data.get("status_exception", {})

                if self.metrics_service:
                    await self.metrics_service.record_metric(
                        name="tracking_exception",
                        value=1.0,
                        labels={
                            "tracking_number": tracking_number,
                            "exception_code": exception.get("code"),
                        },
                    )

                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="tracking_exception",
                    category=NotificationCategory.PIPELINE_ERROR,
                    data={
                        "tracking_number": tracking_number,
                        "exception": exception,
                        "timestamp": str(int(time.time())),
                    },
                    priority=NotificationPriority.HIGH,
                )
        except Exception as e:
            self.metrics_service.track_error("webhook_processing_error", str(e))
            raise

    async def create_batch_labels(
        self, shipments: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Create shipping labels for multiple shipments in batch.
        """
        try:
            batch = shippo.Batch.create(
                default_carrier_account=self.carrier_account,
                default_servicelevel_token="usps_priority",
                batch_shipments=shipments,
            )
            while batch.status in ["VALIDATING", "PROCESSING"]:
                batch = shippo.Batch.retrieve(batch.id)
            if batch.status == "ERROR":
                raise Exception(f"Batch processing failed: {batch.messages}")
            results = []
            for shipment in batch.batch_shipments.results:
                if shipment.status == "SUCCESS":
                    results.append(
                        {
                            "label_url": shipment.label_url,
                            "tracking_number": shipment.tracking_number,
                            "tracking_url": shipment.tracking_url_provider,
                        }
                    )
                else:
                    await self.notification_service.send_alert(
                        "Label Creation Error",
                        f"Failed to create label: {shipment.messages}",
                    )
            return results
        except Exception as e:
            self.metrics_service.track_error("batch_label_creation_error", str(e))
            raise

    async def create_return_label(
        self,
        original_transaction_id: str,
        from_address: Dict[str, str],
        to_address: Dict[str, str],
        parcel: Dict[str, any],
    ) -> Dict[str, any]:
        """
        Create a return shipping label.
        """
        try:
            return_shipment = shippo.Shipment.create(
                address_from=from_address,
                address_to=to_address,
                parcels=[parcel],
                is_return=True,
                async_=False,
            )
            return_rate = min(return_shipment.rates, key=lambda x: float(x.amount))
            return_label = shippo.Transaction.create(
                rate=return_rate.id, label_file_type="PDF", async_=False
            )
            if return_label.status == "SUCCESS":
                return {
                    "label_url": return_label.label_url,
                    "tracking_number": return_label.tracking_number,
                    "tracking_url": return_label.tracking_url_provider,
                }
            else:
                raise Exception(
                    f"Return label creation failed: {return_label.messages}"
                )
        except Exception as e:
            self.metrics_service.track_error("return_label_creation_error", str(e))
            raise
