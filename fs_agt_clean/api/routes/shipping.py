"""
Shipping API routes for FlipSync.

This module provides shipping-related endpoints including shipment creation,
rate calculation, label generation, tracking, and webhook management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from fs_agt_clean.database.models.unified_user import UnifiedUserResponse
from fs_agt_clean.api.dependencies.dependencies import get_current_user

logger = logging.getLogger(__name__)

try:
    from fs_agt_clean.services.logistics.shippo.shippo_service import (
        ShippingDimensions,
        ShippoService,
    )

    SHIPPO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Shippo service not available: {e}")
    SHIPPO_AVAILABLE = False

    # Create mock classes for development
    class ShippingDimensions:
        pass

    class ShippoService:
        pass


# Create router without prefix (prefix will be added in main.py)
router = APIRouter(
    tags=["shipping"],
)


class AddressModel(BaseModel):
    """Address model for shipping operations."""

    name: str
    street1: str
    city: str
    state: str
    zip: str
    country: str
    street2: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class ParcelModel(BaseModel):
    """Parcel model for shipping dimensions."""

    length: float
    width: float
    height: float
    weight: float
    distance_unit: str = "in"
    mass_unit: str = "lb"


class ShipmentRequest(BaseModel):
    """Request model for creating a shipment."""

    from_address: AddressModel
    to_address: AddressModel
    parcel: ParcelModel
    insurance_amount: Optional[float] = None
    signature_required: bool = False


class BatchShipmentRequest(BaseModel):
    """Request model for batch shipment operations."""

    shipments: List[ShipmentRequest]


class WebhookRegistration(BaseModel):
    """Model for registering shipping webhooks."""

    callback_url: str
    event_types: Optional[List[str]] = None


# Get Shippo service instance
async def get_shippo_service() -> ShippoService:
    """Get the Shippo service instance."""
    # In a real implementation, the API key would be retrieved from a secure configuration
    # For now, we'll use a test key
    api_key = "shippo_test_cf1b6d0655e59fc71d3c42597adc5a1f4f043b60"
    # Note: In a real implementation, we would properly handle the type compatibility
    # between the metrics and notification services
    return ShippoService(
        api_key=api_key,
        metrics_service=None,  # Temporarily set to None to avoid type errors
        notification_service=None,  # Temporarily set to None to avoid type errors
        test_mode=True,
    )


@router.post("/shipments")
async def create_shipment(
    request: ShipmentRequest,
    current_user: UnifiedUserResponse = Depends(get_current_user),
    shippo_service: ShippoService = Depends(get_shippo_service),
) -> Dict[str, Any]:
    """
    Create a new shipment and get available rates.

    This endpoint creates a shipment using the provided address and parcel information,
    then returns available shipping rates from various carriers.
    """
    try:
        # Convert request data to the format expected by the shipping service
        dimensions = ShippingDimensions(
            length=request.parcel.length,
            width=request.parcel.width,
            height=request.parcel.height,
            weight=request.parcel.weight,
            distance_unit=request.parcel.distance_unit,
            mass_unit=request.parcel.mass_unit,
        )

        # Convert addresses to dictionaries
        from_address = request.from_address.model_dump()
        to_address = request.to_address.model_dump()

        # Calculate shipping rates
        rates = await shippo_service.calculate_shipping_rates(
            dimensions=dimensions,
            from_address=from_address,
            to_address=to_address,
            insurance_amount=request.insurance_amount,
            signature_required=request.signature_required,
        )

        # Convert rates to dictionaries
        rates_dict = []
        for rate in rates:
            rate_dict = {
                "provider": rate.provider,
                "service": rate.service,
                "amount": rate.amount,
                "currency": rate.currency,
                "days": rate.days,
                "trackable": rate.trackable,
                "insurance_amount": rate.insurance_amount,
                "provider_image": rate.provider_image,
                "estimated_days": rate.estimated_days,
                "arrives_by": rate.arrives_by.isoformat() if rate.arrives_by else None,
            }
            rates_dict.append(rate_dict)

        return {"rates": rates_dict}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate shipping rates",
        )


@router.post("/rates")
async def get_shipping_rates(
    request: ShipmentRequest,
    current_user: UnifiedUserResponse = Depends(get_current_user),
    shippo_service: ShippoService = Depends(get_shippo_service),
) -> Dict[str, Any]:
    """
    Get available shipping rates for a shipment.

    This endpoint calculates and returns available shipping rates for a shipment
    based on the provided address and parcel information.
    """
    try:
        # Convert request data to the format expected by the shipping service
        dimensions = ShippingDimensions(
            length=request.parcel.length,
            width=request.parcel.width,
            height=request.parcel.height,
            weight=request.parcel.weight,
            distance_unit=request.parcel.distance_unit,
            mass_unit=request.parcel.mass_unit,
        )

        # Convert addresses to dictionaries
        from_address = request.from_address.model_dump()
        to_address = request.to_address.model_dump()

        # Calculate shipping rates
        rates = await shippo_service.calculate_shipping_rates(
            dimensions=dimensions,
            from_address=from_address,
            to_address=to_address,
            insurance_amount=request.insurance_amount,
            signature_required=request.signature_required,
        )

        # Convert rates to dictionaries
        rates_dict = []
        for rate in rates:
            rate_dict = {
                "provider": rate.provider,
                "service": rate.service,
                "amount": rate.amount,
                "currency": rate.currency,
                "days": rate.days,
                "trackable": rate.trackable,
                "insurance_amount": rate.insurance_amount,
                "provider_image": rate.provider_image,
                "estimated_days": rate.estimated_days,
                "arrives_by": rate.arrives_by.isoformat() if rate.arrives_by else None,
            }
            rates_dict.append(rate_dict)

        return {"rates": rates_dict}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate shipping rates",
        )


@router.post("/transactions")
async def create_transaction(
    rate_id: str,
    request: ShipmentRequest,
    current_user: UnifiedUserResponse = Depends(get_current_user),
    shippo_service: ShippoService = Depends(get_shippo_service),
) -> Dict[str, Any]:
    """
    Create a shipping label using a selected rate.

    This endpoint generates a shipping label using the specified rate ID and
    shipment information.
    """
    try:
        # Convert addresses to dictionaries
        from_address = request.from_address.model_dump()
        to_address = request.to_address.model_dump()

        # Convert parcel to dictionary
        parcel = {
            "length": request.parcel.length,
            "width": request.parcel.width,
            "height": request.parcel.height,
            "weight": request.parcel.weight,
            "distance_unit": request.parcel.distance_unit,
            "mass_unit": request.parcel.mass_unit,
        }

        # Create shipping label
        label = await shippo_service.create_shipping_label(
            rate_id=rate_id,
            from_address=from_address,
            to_address=to_address,
            parcel=parcel,
        )

        return {
            "tracking_number": label.get("tracking_number"),
            "label_url": label.get("label_url"),
            "carrier": label.get("carrier"),
            "service": label.get("service"),
            "created_at": datetime.now().isoformat(),
            "status": "created",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shipping label",
        )


@router.post("/batch")
async def create_batch_labels(
    request: BatchShipmentRequest,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create shipping labels for multiple shipments in batch.

    This endpoint processes multiple shipment requests in a batch, generating
    shipping labels asynchronously.
    """
    try:
        # Mock implementation until proper service integration is complete
        return {
            "message": "Batch processing started",
            "shipment_count": len(request.shipments),
            "batch_id": "batch_12345",
            "estimated_completion_time": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/returns/{transaction_id}")
async def create_return_label(
    transaction_id: str,
    request: ShipmentRequest,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create a return shipping label.

    This endpoint generates a return shipping label for an existing transaction.
    """
    try:
        # Mock implementation until proper service integration is complete
        return {
            "tracking_number": f"9400987654321098765432",
            "label_url": f"https://api.flipsync.com/labels/return_{transaction_id}.pdf",
            "carrier": "USPS",
            "service": "Priority Mail Return",
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "original_transaction_id": transaction_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/track/{tracking_number}")
async def track_shipment(
    tracking_number: str,
    current_user: UnifiedUserResponse = Depends(get_current_user),
    shippo_service: ShippoService = Depends(get_shippo_service),
) -> Dict[str, Any]:
    """
    Track a shipment status.

    This endpoint retrieves the current tracking information for a shipment using
    the provided tracking number.
    """
    try:
        # Track shipment
        tracking = await shippo_service.track_shipment(tracking_number)

        # Format tracking events
        events = []
        tracking_history = tracking.get("tracking_history", [])
        if tracking_history:
            for event in tracking_history:
                events.append(
                    {
                        "timestamp": event.get("status_date"),
                        "location": event.get("location"),
                        "status": event.get("status"),
                        "description": event.get("status_details"),
                    }
                )

        return {
            "tracking_number": tracking_number,
            "carrier": tracking.get("carrier"),
            "status": tracking.get("status"),
            "estimated_delivery": tracking.get("eta"),
            "events": events,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track shipment",
        )


@router.post("/webhooks/register")
async def register_webhook(
    request: WebhookRegistration,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Register a webhook for tracking updates.

    This endpoint registers a webhook callback URL to receive shipping status
    updates and other shipping-related events.
    """
    try:
        # Mock implementation until proper service integration is complete
        return {
            "webhook_id": "wh_12345",
            "callback_url": request.callback_url,
            "event_types": request.event_types
            or ["tracking_update", "delivery_confirmation"],
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhooks/callback")
async def webhook_callback(webhook_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Webhook callback endpoint for tracking updates.

    This endpoint receives webhook callbacks from shipping providers with
    updates on shipment status.
    """
    try:
        # Mock implementation until proper service integration is complete
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ShippingArbitrageRequest(BaseModel):
    """Request model for shipping arbitrage analysis."""

    product_id: str
    dimensions: Dict[str, Any]
    weight: float
    value: float
    origin_address: Dict[str, str]
    profit_margin_threshold: Optional[float] = 0.15
    prioritize_speed: Optional[bool] = False
    enable_insurance: Optional[bool] = True
    enable_arbitrage: Optional[bool] = True


@router.post("/arbitrage")
async def shipping_arbitrage_analysis(
    request: ShippingArbitrageRequest,
    current_user: UnifiedUserResponse = Depends(get_current_user),
    shippo_service: ShippoService = Depends(get_shippo_service),
) -> Dict[str, Any]:
    """
    Analyze shipping arbitrage opportunities between eBay and Shippo.

    This endpoint compares eBay's USPS shipping rates with Shippo's dimensional
    shipping to find cost optimization opportunities for FlipSync's automated
    shipping strategy.
    """
    try:
        # Convert dimensions to ShippingDimensions
        dimensions = ShippingDimensions(
            length=request.dimensions.get("length", 12.0),
            width=request.dimensions.get("width", 9.0),
            height=request.dimensions.get("height", 3.0),
            weight=request.weight,
            distance_unit=request.dimensions.get("unit", "in"),
            mass_unit="lb",
        )

        # Mock destination for testing (would be dynamic in production)
        mock_destination = {
            "name": "Test Customer",
            "street1": "123 Main St",
            "city": "Los Angeles",
            "state": "CA",
            "zip": "90210",
            "country": "US",
        }

        # Use real Shippo API for all requests (no more mocks)
        try:
            # Calculate real Shippo rates using dimensional shipping
            shippo_rates = await shippo_service.calculate_shipping_rates(
                dimensions=dimensions,
                from_address=request.origin_address,
                to_address=mock_destination,
                insurance_amount=request.value if request.enable_insurance else None,
            )
        except Exception as e:
            logger.warning(f"Shippo API error, using fallback rates: {e}")
            # Fallback to basic rate calculation if Shippo API fails
            from fs_agt_clean.services.shipping_arbitrage import (
                shipping_arbitrage_service,
            )

            fallback_result = await shipping_arbitrage_service.calculate_arbitrage(
                origin_zip=request.origin_address.get("zip", "90210"),
                destination_zip=mock_destination.get("zip", "90210"),
                weight=dimensions.weight,
                package_type="standard",
            )

            # Convert fallback result to shippo_rates format
            shippo_rates = []
            if "carrier_rates" in fallback_result:
                for carrier, rate_info in fallback_result["carrier_rates"].items():
                    # Create mock rate object for compatibility
                    class FallbackRate:
                        def __init__(self, carrier, service, amount, days):
                            self.carrier = carrier.upper()
                            self.service_level = type(
                                "ServiceLevel", (), {"name": service}
                            )()
                            self.amount = str(amount)
                            self.estimated_days = days
                            self.object_id = f"fallback_{carrier}_{service}"

                    shippo_rates.append(
                        FallbackRate(carrier, "Ground", rate_info["rate"], 3)
                    )

        # Mock eBay rates for comparison (would integrate with eBay API)
        ebay_rates = [
            {
                "carrier": "USPS",
                "service": "Priority Mail",
                "amount": 15.99,
                "estimated_days": 3,
                "source": "ebay",
            },
            {
                "carrier": "USPS",
                "service": "Ground Advantage",
                "amount": 12.99,
                "estimated_days": 5,
                "source": "ebay",
            },
        ]

        # Analyze arbitrage opportunities
        recommendations = []
        total_savings = 0.0
        best_option = None
        best_savings = 0.0

        for shippo_rate in shippo_rates:
            shippo_cost = float(shippo_rate.amount)

            # Find comparable eBay rate
            comparable_ebay = None
            for ebay_rate in ebay_rates:
                if (
                    ebay_rate["carrier"] == shippo_rate.carrier
                    and abs(ebay_rate["estimated_days"] - shippo_rate.estimated_days)
                    <= 1
                ):
                    comparable_ebay = ebay_rate
                    break

            if comparable_ebay:
                ebay_cost = comparable_ebay["amount"]
                savings = ebay_cost - shippo_cost

                if savings > 0:  # Shippo is cheaper
                    total_savings += savings

                    recommendation = {
                        "id": f"arb_{shippo_rate.object_id}",
                        "carrier": shippo_rate.carrier,
                        "service": shippo_rate.service_level.name,
                        "cost": shippo_cost,
                        "delivery_days": shippo_rate.estimated_days,
                        "savings": savings,
                        "confidence": 0.85,
                        "notes": f"Save ${savings:.2f} vs eBay {comparable_ebay['service']}",
                        "is_recommended": savings > 2.0,  # Recommend if saves >$2
                        "metadata": {
                            "ebay_cost": ebay_cost,
                            "shippo_cost": shippo_cost,
                            "arbitrage_opportunity": True,
                        },
                    }

                    recommendations.append(recommendation)

                    if savings > best_savings:
                        best_savings = savings
                        best_option = recommendation

        # If no arbitrage opportunities, include best Shippo rates anyway
        if not recommendations:
            for rate in shippo_rates[:3]:  # Top 3 rates
                recommendations.append(
                    {
                        "id": f"std_{rate.object_id}",
                        "carrier": rate.carrier,
                        "service": rate.service_level.name,
                        "cost": float(rate.amount),
                        "delivery_days": rate.estimated_days,
                        "savings": 0.0,
                        "confidence": 0.75,
                        "notes": "Standard Shippo rate - no arbitrage opportunity",
                        "is_recommended": False,
                        "metadata": {
                            "arbitrage_opportunity": False,
                        },
                    }
                )

        # Calculate API cost (mock)
        api_cost = 0.05  # $0.05 for rate comparison

        arbitrage_result = {
            "recommendations": recommendations,
            "total_savings": total_savings,
            "best_carrier": best_option["carrier"] if best_option else "USPS",
            "best_service": best_option["service"] if best_option else "Priority Mail",
            "best_cost": best_option["cost"] if best_option else 15.99,
            "analysis": {
                "ebay_rates_count": len(ebay_rates),
                "shippo_rates_count": len(shippo_rates),
                "arbitrage_opportunities": len(
                    [r for r in recommendations if r["savings"] > 0]
                ),
                "max_savings": best_savings,
                "profit_margin_met": best_savings
                >= (request.value * request.profit_margin_threshold),
            },
            "api_cost": api_cost,
            "analyzed_at": datetime.now().isoformat(),
        }

        return arbitrage_result

    except Exception as e:
        logger.error(f"Error in shipping arbitrage analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Arbitrage analysis failed: {str(e)}",
        )


@router.post("/apply-strategy")
async def apply_shipping_strategy(
    product_id: str,
    recommendation: Dict[str, Any],
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Apply a shipping strategy recommendation to a product.

    This endpoint applies the selected shipping optimization strategy
    and returns the optimization result.
    """
    try:
        # Mock implementation for applying strategy
        original_cost = 15.99
        optimized_cost = recommendation.get("cost", 12.99)
        savings = original_cost - optimized_cost

        optimization_result = {
            "product_id": product_id,
            "selected_recommendation": recommendation,
            "original_cost": original_cost,
            "optimized_cost": optimized_cost,
            "savings": savings,
            "optimization_reason": f"Applied {recommendation.get('carrier')} {recommendation.get('service')} strategy",
            "timestamp": datetime.now().isoformat(),
        }

        return optimization_result

    except Exception as e:
        logger.error(f"Error applying shipping strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply strategy: {str(e)}",
        )


# V3 Additional Shipping Endpoints


@router.post("/shippo/poly")
async def calculate_dimensional_shipping_poly(
    request: Dict[str, Any],
    current_user: UnifiedUserResponse = Depends(get_current_user),
    shippo_service: ShippoService = Depends(get_shippo_service),
) -> Dict[str, Any]:
    """
    Calculate dimensional shipping via Shippo's 'poly' option for 10% user discount.

    This endpoint implements FlipSync's core revenue model:
    - Uses 2-dimension 'poly' shipping calculation (length + width only)
    - Provides 10% discount to users
    - Captures remaining savings as FlipSync revenue
    - Optimizes for USPS dimensional shipping rates
    """
    try:
        logger.info("Calculating dimensional shipping with poly option")

        # Extract request parameters
        origin_zip = request.get("origin_zip", "37203")  # Default Nashville
        destination_zip = request.get("destination_zip")
        weight = request.get("weight", 1.0)
        dimensions = request.get("dimensions", {})

        if not destination_zip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="destination_zip is required",
            )

        # Validate dimensions for poly calculation (2-dimension)
        length = dimensions.get("length", 12.0)
        width = dimensions.get("width", 8.0)
        height = dimensions.get(
            "height", 4.0
        )  # Height used for volume but not poly rate

        # Calculate poly dimensions (use 2 largest dimensions)
        poly_dimensions = sorted([length, width, height], reverse=True)[:2]
        poly_length = poly_dimensions[0]
        poly_width = poly_dimensions[1]

        # Create Shippo-compatible dimensions for poly calculation
        shippo_dimensions = {
            "length": poly_length,
            "width": poly_width,
            "height": 0.1,  # Minimal height for poly calculation
            "distance_unit": "in",
        }

        # Calculate standard 3D shipping rate for comparison
        standard_dimensions = {
            "length": length,
            "width": width,
            "height": height,
            "distance_unit": "in",
        }

        # Get both poly and standard rates
        poly_rates = await shippo_service.calculate_shipping_rates(
            dimensions=shippo_dimensions,
            from_address={"zip": origin_zip, "country": "US"},
            to_address={"zip": destination_zip, "country": "US"},
            weight=weight,
        )

        standard_rates = await shippo_service.calculate_shipping_rates(
            dimensions=standard_dimensions,
            from_address={"zip": origin_zip, "country": "US"},
            to_address={"zip": destination_zip, "country": "US"},
            weight=weight,
        )

        # Find best USPS rates for both calculations
        best_poly_rate = None
        best_standard_rate = None

        for rate in poly_rates:
            if rate.carrier.upper() == "USPS" and (
                not best_poly_rate or float(rate.amount) < float(best_poly_rate.amount)
            ):
                best_poly_rate = rate

        for rate in standard_rates:
            if rate.carrier.upper() == "USPS" and (
                not best_standard_rate
                or float(rate.amount) < float(best_standard_rate.amount)
            ):
                best_standard_rate = rate

        if not best_poly_rate or not best_standard_rate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to calculate USPS rates for given parameters",
            )

        # Calculate FlipSync revenue model
        poly_cost = float(best_poly_rate.amount)
        standard_cost = float(best_standard_rate.amount)

        # FlipSync savings = difference between standard and poly rates
        flipsync_savings = max(0, standard_cost - poly_cost)

        # User gets 10% discount from poly rate
        user_discount = poly_cost * 0.10
        user_final_cost = poly_cost - user_discount

        # FlipSync revenue = savings from poly + portion of user discount
        flipsync_revenue = flipsync_savings + (
            user_discount * 0.5
        )  # Keep 50% of discount as revenue

        # Prepare response
        response_data = {
            "success": True,
            "shipping_calculation": {
                "origin_zip": origin_zip,
                "destination_zip": destination_zip,
                "weight": weight,
                "dimensions_used": {
                    "poly_dimensions": {"length": poly_length, "width": poly_width},
                    "standard_dimensions": {
                        "length": length,
                        "width": width,
                        "height": height,
                    },
                },
            },
            "rate_comparison": {
                "standard_3d_rate": {
                    "amount": standard_cost,
                    "carrier": best_standard_rate.carrier,
                    "service": best_standard_rate.service_level,
                    "estimated_days": best_standard_rate.estimated_days,
                },
                "poly_2d_rate": {
                    "amount": poly_cost,
                    "carrier": best_poly_rate.carrier,
                    "service": best_poly_rate.service_level,
                    "estimated_days": best_poly_rate.estimated_days,
                },
            },
            "flipsync_revenue_model": {
                "user_pays": round(user_final_cost, 2),
                "user_discount_amount": round(user_discount, 2),
                "user_discount_percentage": 10.0,
                "flipsync_revenue": round(flipsync_revenue, 2),
                "total_savings_captured": round(flipsync_savings + user_discount, 2),
            },
            "recommended_rate": {
                "rate_id": best_poly_rate.object_id,
                "amount": round(user_final_cost, 2),
                "carrier": best_poly_rate.carrier,
                "service": best_poly_rate.service_level,
                "estimated_days": best_poly_rate.estimated_days,
            },
        }

        # Track FlipSync revenue
        await _track_shipping_revenue(
            user_id=str(current_user.id),
            revenue_amount=flipsync_revenue,
            savings_amount=flipsync_savings,
            user_discount=user_discount,
            metadata={
                "origin_zip": origin_zip,
                "destination_zip": destination_zip,
                "poly_rate": poly_cost,
                "standard_rate": standard_cost,
            },
        )

        logger.info(
            f"Poly shipping calculated: User pays ${user_final_cost:.2f}, FlipSync revenue ${flipsync_revenue:.2f}"
        )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating poly shipping: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Poly shipping calculation failed: {str(e)}",
        )


@router.get("/zones/{seller_zip}")
async def get_shipping_zones(
    seller_zip: str,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get USPS shipping zones from seller location.

    V3 endpoint for zone-based shipping calculations.
    """
    try:
        # Validate ZIP code format
        if not seller_zip.isdigit() or len(seller_zip) != 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ZIP code format. Must be 5 digits.",
            )

        # Mock USPS zone data (in production, integrate with USPS API)
        zones = {
            "seller_zip": seller_zip,
            "zones": {
                "zone_1": {"distance_miles": "0-50", "states": ["Local"]},
                "zone_2": {"distance_miles": "51-150", "states": ["Adjacent states"]},
                "zone_3": {"distance_miles": "151-300", "states": ["Regional"]},
                "zone_4": {
                    "distance_miles": "301-600",
                    "states": ["Extended regional"],
                },
                "zone_5": {"distance_miles": "601-1000", "states": ["Cross-country"]},
                "zone_6": {
                    "distance_miles": "1001-1400",
                    "states": ["Far cross-country"],
                },
                "zone_7": {"distance_miles": "1401-1800", "states": ["Coast-to-coast"]},
                "zone_8": {
                    "distance_miles": "1801+",
                    "states": ["Alaska, Hawaii, territories"],
                },
            },
            "average_shipping_costs": {
                "zone_1": 8.50,
                "zone_2": 9.75,
                "zone_3": 11.25,
                "zone_4": 13.50,
                "zone_5": 15.75,
                "zone_6": 18.25,
                "zone_7": 21.50,
                "zone_8": 28.75,
            },
        }

        logger.info(f"Retrieved shipping zones for ZIP {seller_zip}")
        return zones

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving shipping zones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve shipping zones: {str(e)}",
        )


# Helper function for tracking shipping revenue
async def _track_shipping_revenue(
    user_id: str,
    revenue_amount: float,
    savings_amount: float,
    user_discount: float,
    metadata: Dict[str, Any],
) -> None:
    """Track FlipSync revenue from shipping arbitrage."""
    try:
        logger.info(
            f"Tracking shipping revenue: ${revenue_amount:.2f} for user {user_id}"
        )

        # This would integrate with the revenue tracking system
        # For now, just log the revenue tracking
        revenue_data = {
            "user_id": user_id,
            "revenue_type": "shipping_arbitrage",
            "revenue_amount": revenue_amount,
            "savings_amount": savings_amount,
            "user_discount": user_discount,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Shipping revenue tracked: {revenue_data}")

    except Exception as e:
        logger.error(f"Error tracking shipping revenue: {e}")
        # Don't raise exception to avoid breaking the main flow
