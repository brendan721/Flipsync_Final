import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import shippo  # Shippo API library

from fs_agt_clean.core.utils.config import get_settings
from fs_agt_clean.core.utils.metrics import MetricsMixin

# from pydantic import BaseSettings  # Requires pydantic-settings


"""
Shipping service implementation using Shippo API.
Handles shipping rate calculations, label generation, and tracking.
"""

logger: logging.Logger = logging.getLogger(__name__)


class ShippingSettings:  # BaseSettings commented out
    """Shipping service settings."""

    def __init__(self):
        """Initialize shipping settings from environment."""
        import os

        # Use SHIPPO_TEST_TOKEN from environment, fallback to test key
        self.SHIPPO_API_KEY = os.getenv("SHIPPO_TEST_TOKEN", "test_key")

    class Config:
        """Pydantic config."""

        env_prefix = "SHIPPING_"


class ShippingService(MetricsMixin):
    """Handles all shipping-related operations using Shippo API."""

    def __init__(self):
        """Initialize shipping service."""
        super().__init__()
        self.settings = ShippingSettings()
        shippo.api_key = self.settings.SHIPPO_API_KEY
        logger.info(
            "Shippo API initialized with key: %s",
            self.settings.SHIPPO_API_KEY[:8] + "...",
        )
        self.carriers = []
        self.parcel_templates = {}
        self._is_initialized = False

    async def ensure_initialized(self):
        """Ensure the service is initialized."""
        if not self.carriers:
            await self._initialize_service()
        return self

    async def _initialize_service(self):
        """Initialize shipping service configuration."""
        try:
            self.carriers = await self._get_carrier_accounts()
            self.parcel_templates = await self._get_parcel_templates()
            logger.info(
                "Shipping service initialized with %s carriers", len(self.carriers)
            )

        except Exception as e:
            logger.error("Failed to initialize shipping service: %s", str(e))
            # Don't raise the error, just continue with empty carriers and templates
            self.carriers = []
            self.parcel_templates = {}
            logger.info("Continuing with empty carriers and templates for testing")

    async def calculate_rates(
        self,
        from_address: Dict[str, Any],
        to_address: Dict[str, Any],
        parcel: Dict[str, Any],
        carrier_accounts: Optional[List[str]] = None,
        is_return: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Calculate shipping rates for a package.

        Args:
            from_address: Sender address details
            to_address: Recipient address details
            parcel: Package dimensions and weight
            carrier_accounts: Optional list of specific carrier accounts to use
            is_return: Whether this is a return shipment

        Returns:
            List of available shipping rates
        """
        start_time = datetime.utcnow()
        try:
            from_address = await self._validate_address(from_address)
            to_address = await self._validate_address(to_address)
            shipment = await self._create_shipment(
                from_address=from_address,
                to_address=to_address,
                parcel=parcel,
                carrier_accounts=carrier_accounts,
                is_return=is_return,
            )
            rates = shipment.rates
            sorted_rates = sorted(rates, key=lambda x: float(x.amount))
            # Convert rates to dictionaries
            rate_dicts = [
                {
                    "id": rate.object_id,
                    "carrier": rate.provider,
                    "service": rate.servicelevel.name,
                    "amount": float(rate.amount),
                    "currency": rate.currency,
                    "duration_terms": rate.duration_terms,
                    "estimated_days": rate.estimated_days,
                }
                for rate in sorted_rates
            ]
            await self.update_operation_metrics(
                operation="calculate_rates",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=True,
                additional_metrics={
                    "rate_count": len(rate_dicts),
                    "carrier_count": (
                        len(carrier_accounts)
                        if carrier_accounts
                        else len(self.carriers)
                    ),
                },
            )
            return rate_dicts
        except Exception as e:
            logger.error("Failed to calculate shipping rates: %s", str(e))
            await self.update_operation_metrics(
                operation="calculate_rates",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=False,
                additional_metrics={"error": str(e)},
            )
            return []

    async def _validate_address(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and format an address."""
        try:
            validated = await self.validate_address(address)
            if validated is None:
                logger.warning("Using unvalidated address: %s", address)
                return address
            return {
                "name": validated.name,
                "street1": validated.street1,
                "street2": validated.street2,
                "city": validated.city,
                "state": validated.state,
                "zip": validated.zip,
                "country": validated.country,
                "phone": validated.phone,
                "email": validated.email,
                "is_residential": validated.is_residential,
            }
        except Exception as e:
            logger.warning("Address validation failed, using as-is: %s", str(e))
            return address

    async def create_label(
        self, rate_id: str, is_test: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Create a shipping label using a selected rate.

        Args:
            rate_id: Selected rate ID to create label
            is_test: Whether to create a test label

        Returns:
            Shipping label details if successful
        """
        start_time = datetime.utcnow()
        try:
            transaction = shippo.Transaction.create(
                rate=rate_id, is_test=is_test, async_=False
            )
            if transaction.status != "SUCCESS":
                logger.error("Failed to create label: %s", transaction.messages)
                return None
            await self.update_operation_metrics(
                operation="create_label",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=True,
            )
            return {
                "label_url": transaction.label_url,
                "tracking_number": transaction.tracking_number,
                "tracking_url": transaction.tracking_url_provider,
                "eta": transaction.eta,
                "rate": transaction.rate,
                "messages": transaction.messages,
            }
        except Exception as e:
            logger.error("Failed to create shipping label: %s", str(e))
            await self.update_operation_metrics(
                operation="create_label",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=False,
                additional_metrics={"error": str(e)},
            )
            return None

    async def track_shipment(
        self, tracking_number: str, carrier: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for a shipment.

        Args:
            tracking_number: Shipment tracking number
            carrier: Carrier code

        Returns:
            Tracking details if available
        """
        start_time = datetime.utcnow()
        try:
            tracking = shippo.Track.get_status(
                carrier=carrier, tracking_number=tracking_number
            )
            await self.update_operation_metrics(
                operation="track_shipment",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=True,
            )
            return {
                "status": tracking.tracking_status.status,
                "status_details": tracking.tracking_status.status_details,
                "location": tracking.tracking_status.location,
                "eta": tracking.eta,
                "tracking_history": tracking.tracking_history,
            }
        except Exception as e:
            logger.error("Failed to get tracking info: %s", str(e))
            await self.update_operation_metrics(
                operation="track_shipment",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=False,
                additional_metrics={"error": str(e)},
            )
            return None

    async def validate_address(
        self, address: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Validate a shipping address.

        Args:
            address: Address details to validate

        Returns:
            Validated address if successful
        """
        start_time = datetime.utcnow()
        try:
            address_obj = shippo.Address.create(validation_results=True, **address)
            is_valid = address_obj.validation_results.is_valid
            messages = address_obj.validation_results.messages
            await self.update_operation_metrics(
                operation="validate_address",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=True,
                additional_metrics={"is_valid": is_valid},
            )
            if not is_valid:
                logger.warning("Invalid address: %s", messages)
                return None
            return address_obj
        except Exception as e:
            logger.error("Failed to validate address: %s", str(e))
            await self.update_operation_metrics(
                operation="validate_address",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=False,
                additional_metrics={"error": str(e)},
            )
            return None

    async def _get_carrier_accounts(self) -> List[Dict[str, Any]]:
        """Get list of available carrier accounts."""
        try:
            return shippo.CarrierAccount.all()
        except Exception as e:
            logger.error("Failed to get carrier accounts: %s", str(e))
            return []

    async def _get_parcel_templates(self) -> Dict[str, Any]:
        """Get available parcel templates."""
        try:
            templates = shippo.ParcelTemplate.all()
            return {t.token: t for t in templates}
        except Exception as e:
            logger.error("Failed to get parcel templates: %s", str(e))
            return {}

    async def _create_shipment(
        self,
        from_address: Dict[str, Any],
        to_address: Dict[str, Any],
        parcel: Dict[str, Any],
        carrier_accounts: Optional[List[str]] = None,
        is_return: bool = False,
    ) -> Any:
        """Create a shipment object for rate calculation."""
        try:
            shipment_data = {
                "address_from": from_address,
                "address_to": to_address,
                "parcels": [parcel],
                "async": False,
            }
            if carrier_accounts:
                shipment_data["carrier_accounts"] = carrier_accounts
            if is_return:
                shipment_data["is_return"] = True
            return shippo.Shipment.create(**shipment_data)
        except Exception as e:
            logger.error("Failed to create shipment: %s", str(e))
            raise

    async def get_refund(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Request a refund for a shipping label.

        Args:
            transaction_id: Transaction ID to refund

        Returns:
            Refund details if successful
        """
        start_time = datetime.utcnow()
        try:
            refund = shippo.Refund.create(transaction=transaction_id, async_=False)
            await self.update_operation_metrics(
                operation="get_refund",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=True,
                additional_metrics={"status": refund.status},
            )
            return {"status": refund.status, "messages": refund.messages}
        except Exception as e:
            logger.error("Failed to process refund: %s", str(e))
            await self.update_operation_metrics(
                operation="get_refund",
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                success=False,
                additional_metrics={"error": str(e)},
            )
            return None
