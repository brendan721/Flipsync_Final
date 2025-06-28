"""
Shipping Arbitrage Service for FlipSync Revenue Model.

This service provides shipping cost optimization and arbitrage calculations:
- Multi-carrier rate comparison
- Route optimization
- Cost savings tracking
- Revenue generation through shipping optimization
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fs_agt_clean.database.repositories.ai_analysis_repository import (
    RevenueCalculationRepository,
)
from fs_agt_clean.services.logistics.shippo.shippo_service import ShippoService
from fs_agt_clean.core.monitoring.cost_tracker import CostCategory, record_ai_cost

logger = logging.getLogger(__name__)


class ShippingCarrier:
    """Represents a shipping carrier with rate calculation capabilities."""

    def __init__(
        self,
        name: str,
        base_rate: float,
        per_pound_rate: float,
        zone_multipliers: Dict[str, float],
    ):
        self.name = name
        self.base_rate = base_rate
        self.per_pound_rate = per_pound_rate
        self.zone_multipliers = zone_multipliers

    def calculate_rate(
        self, weight: float, zone: str, package_type: str = "standard"
    ) -> float:
        """Calculate shipping rate for given parameters."""
        base_cost = self.base_rate + (weight * self.per_pound_rate)
        zone_multiplier = self.zone_multipliers.get(zone, 1.0)

        # Apply package type adjustments
        if package_type == "express":
            base_cost *= 1.5
        elif package_type == "overnight":
            base_cost *= 2.5

        return base_cost * zone_multiplier


class ShippingArbitrageService:
    """Service for shipping cost optimization and arbitrage calculations."""

    def __init__(self):
        """Initialize the shipping arbitrage service."""
        self._revenue_repository = None
        self._shippo_service = None
        self.carriers = self._initialize_carriers()
        self.zone_mapping = self._initialize_zone_mapping()

        logger.info("Shipping Arbitrage Service initialized")

    @property
    def revenue_repository(self):
        """Lazy initialization of revenue repository."""
        if self._revenue_repository is None:
            self._revenue_repository = RevenueCalculationRepository()
        return self._revenue_repository

    @property
    def shippo_service(self):
        """Lazy initialization of Shippo service."""
        if self._shippo_service is None:
            import os

            # Use test token for development, production token for live
            api_key = os.getenv("SHIPPO_TEST_TOKEN") or os.getenv("SHIPPO_TOKEN")
            if not api_key:
                raise ValueError(
                    "Shippo API key not configured. Set SHIPPO_TEST_TOKEN or SHIPPO_TOKEN environment variable."
                )

            self._shippo_service = ShippoService(
                api_key=api_key,
                test_mode=bool(
                    os.getenv("SHIPPO_TEST_TOKEN")
                ),  # Use test mode if test token is set
            )
        return self._shippo_service

    def _initialize_carriers(self) -> Dict[str, ShippingCarrier]:
        """Initialize shipping carrier configurations."""
        return {
            "usps": ShippingCarrier(
                name="USPS",
                base_rate=5.50,
                per_pound_rate=0.85,
                zone_multipliers={
                    "zone_1": 1.0,
                    "zone_2": 1.1,
                    "zone_3": 1.2,
                    "zone_4": 1.3,
                    "zone_5": 1.4,
                    "zone_6": 1.5,
                    "zone_7": 1.6,
                    "zone_8": 1.8,
                },
            ),
            "ups": ShippingCarrier(
                name="UPS",
                base_rate=7.25,
                per_pound_rate=0.95,
                zone_multipliers={
                    "zone_1": 1.0,
                    "zone_2": 1.15,
                    "zone_3": 1.25,
                    "zone_4": 1.35,
                    "zone_5": 1.45,
                    "zone_6": 1.55,
                    "zone_7": 1.65,
                    "zone_8": 1.85,
                },
            ),
            "fedex": ShippingCarrier(
                name="FedEx",
                base_rate=6.75,
                per_pound_rate=0.90,
                zone_multipliers={
                    "zone_1": 1.0,
                    "zone_2": 1.12,
                    "zone_3": 1.22,
                    "zone_4": 1.32,
                    "zone_5": 1.42,
                    "zone_6": 1.52,
                    "zone_7": 1.62,
                    "zone_8": 1.82,
                },
            ),
            "dhl": ShippingCarrier(
                name="DHL",
                base_rate=8.50,
                per_pound_rate=1.10,
                zone_multipliers={
                    "zone_1": 1.0,
                    "zone_2": 1.20,
                    "zone_3": 1.30,
                    "zone_4": 1.40,
                    "zone_5": 1.50,
                    "zone_6": 1.60,
                    "zone_7": 1.70,
                    "zone_8": 1.90,
                },
            ),
        }

    def _initialize_zone_mapping(self) -> Dict[str, str]:
        """Initialize ZIP code to zone mapping (simplified)."""
        # This is a simplified mapping - in production, use actual carrier zone charts
        return {
            # Zone 1 (local)
            "90210": "zone_1",
            "90211": "zone_1",
            "90212": "zone_1",
            # Zone 2 (regional)
            "94102": "zone_2",
            "94103": "zone_2",
            "94104": "zone_2",
            # Zone 3 (extended regional)
            "10001": "zone_3",
            "10002": "zone_3",
            "10003": "zone_3",
            # Zone 4 (national)
            "60601": "zone_4",
            "60602": "zone_4",
            "60603": "zone_4",
            # Zone 5 (extended national)
            "30301": "zone_5",
            "30302": "zone_5",
            "30303": "zone_5",
            # Zone 6 (far national)
            "80201": "zone_6",
            "80202": "zone_6",
            "80203": "zone_6",
            # Zone 7 (very far)
            "98101": "zone_7",
            "98102": "zone_7",
            "98103": "zone_7",
            # Zone 8 (furthest)
            "99501": "zone_8",
            "99502": "zone_8",
            "99503": "zone_8",
        }

    def _get_zone_from_zip(self, zip_code: str) -> str:
        """Get shipping zone from ZIP code."""
        # Remove any non-numeric characters and take first 5 digits
        clean_zip = "".join(filter(str.isdigit, zip_code))[:5]
        return self.zone_mapping.get(clean_zip, "zone_4")  # Default to zone 4

    async def calculate_real_shippo_arbitrage(
        self,
        origin_address: Dict[str, str],
        destination_address: Dict[str, str],
        dimensions: Dict[str, float],
        weight: float,
        ebay_shipping_cost: Optional[float] = None,
        insurance_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calculate shipping arbitrage using real Shippo API with dimensional shipping.

        This method focuses on USPS dimensional shipping arbitrage where FlipSync
        achieves revenue by comparing eBay's shipping costs with Shippo's dimensional
        shipping rates, specifically USPS "poly" rates that use the larger 2 out of 3 dimensions.
        """
        try:
            # Create ShippingDimensions object for Shippo API
            from fs_agt_clean.services.logistics.shippo.shippo_service import (
                ShippingDimensions,
            )

            shipping_dimensions = ShippingDimensions(
                length=dimensions.get("length", 12.0),
                width=dimensions.get("width", 9.0),
                height=dimensions.get("height", 3.0),
                weight=weight,
                distance_unit=dimensions.get("unit", "in"),
                mass_unit="lb",
            )

            # Get real Shippo rates
            shippo_rates = await self.shippo_service.calculate_shipping_rates(
                dimensions=shipping_dimensions,
                from_address=origin_address,
                to_address=destination_address,
                insurance_amount=insurance_amount,
                signature_required=False,
            )

            # Focus on USPS dimensional shipping for arbitrage
            usps_rates = [
                rate for rate in shippo_rates if rate.carrier.upper() == "USPS"
            ]

            # Find best USPS dimensional rate (poly rates use larger 2 dimensions)
            best_usps_rate = None
            if usps_rates:
                # Sort by amount to find cheapest
                usps_rates.sort(key=lambda r: float(r.amount))
                best_usps_rate = usps_rates[0]

            # Calculate arbitrage opportunity
            arbitrage_data = {
                "shippo_analysis": {
                    "total_rates_found": len(shippo_rates),
                    "usps_rates_found": len(usps_rates),
                    "best_usps_rate": (
                        {
                            "carrier": (
                                best_usps_rate.carrier if best_usps_rate else None
                            ),
                            "service": (
                                best_usps_rate.service_level.name
                                if best_usps_rate
                                else None
                            ),
                            "amount": (
                                float(best_usps_rate.amount) if best_usps_rate else None
                            ),
                            "estimated_days": (
                                best_usps_rate.estimated_days
                                if best_usps_rate
                                else None
                            ),
                            "rate_id": (
                                best_usps_rate.object_id if best_usps_rate else None
                            ),
                        }
                        if best_usps_rate
                        else None
                    ),
                },
                "dimensional_shipping": {
                    "length": shipping_dimensions.length,
                    "width": shipping_dimensions.width,
                    "height": shipping_dimensions.height,
                    "weight": shipping_dimensions.weight,
                    "uses_dimensional_pricing": True,
                    "poly_calculation": "Uses larger 2 out of 3 dimensions for USPS rates",
                },
            }

            # Calculate savings if eBay cost provided
            if ebay_shipping_cost and best_usps_rate:
                shippo_cost = float(best_usps_rate.amount)
                savings_amount = ebay_shipping_cost - shippo_cost
                savings_percentage = (
                    (savings_amount / ebay_shipping_cost * 100)
                    if ebay_shipping_cost > 0
                    else 0
                )

                arbitrage_data["arbitrage_opportunity"] = {
                    "ebay_shipping_cost": ebay_shipping_cost,
                    "shippo_usps_cost": shippo_cost,
                    "savings_amount": round(savings_amount, 2),
                    "savings_percentage": round(savings_percentage, 2),
                    "profitable": savings_amount > 0,
                    "revenue_potential": (
                        round(savings_amount * 0.8, 2) if savings_amount > 0 else 0
                    ),  # 80% of savings as revenue
                }

            arbitrage_data["calculated_at"] = datetime.now(timezone.utc).isoformat()
            arbitrage_data["api_source"] = "real_shippo_api"

            # Record cost tracking for Shippo API usage
            try:
                # Estimate cost based on number of rates calculated
                estimated_cost = len(shippo_rates) * 0.01  # $0.01 per rate calculation
                await record_ai_cost(
                    category=CostCategory.SHIPPING_SERVICES.value,
                    cost=estimated_cost,
                    tokens_used=len(shippo_rates),
                    model="shippo_api",
                    operation="shipping_rate_calculation",
                    agent_id="logistics_agent",
                )
            except Exception as cost_error:
                logger.warning(f"Failed to record Shippo cost tracking: {cost_error}")

            return arbitrage_data

        except Exception as e:
            logger.error(f"Error calculating real Shippo arbitrage: {e}")
            return {
                "error": str(e),
                "calculated_at": datetime.now(timezone.utc).isoformat(),
                "api_source": "real_shippo_api",
            }

    async def calculate_arbitrage(
        self,
        origin_zip: str,
        destination_zip: str,
        weight: float,
        package_type: str = "standard",
        current_carrier: Optional[str] = None,
        current_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calculate shipping arbitrage opportunities."""
        try:
            # Determine shipping zone
            zone = self._get_zone_from_zip(destination_zip)

            # Calculate rates for all carriers
            carrier_rates = {}
            for carrier_name, carrier in self.carriers.items():
                rate = carrier.calculate_rate(weight, zone, package_type)
                carrier_rates[carrier_name] = {
                    "rate": round(rate, 2),
                    "carrier": carrier_name.upper(),
                    "estimated_delivery": self._get_estimated_delivery(
                        carrier_name, zone, package_type
                    ),
                }

            # Find optimal carrier
            optimal_carrier = min(carrier_rates.items(), key=lambda x: x[1]["rate"])
            optimal_rate = optimal_carrier[1]["rate"]

            # Calculate savings if current rate provided
            savings_data = {}
            if current_rate:
                savings_amount = current_rate - optimal_rate
                savings_percentage = (
                    (savings_amount / current_rate) * 100 if current_rate > 0 else 0
                )

                savings_data = {
                    "original_rate": current_rate,
                    "optimized_rate": optimal_rate,
                    "savings_amount": round(savings_amount, 2),
                    "savings_percentage": round(savings_percentage, 2),
                }

            # Generate recommendations
            recommendations = self._generate_shipping_recommendations(
                carrier_rates, zone, weight, package_type
            )

            return {
                "arbitrage_analysis": {
                    "origin_zip": origin_zip,
                    "destination_zip": destination_zip,
                    "shipping_zone": zone,
                    "package_weight": weight,
                    "package_type": package_type,
                },
                "carrier_rates": carrier_rates,
                "optimal_carrier": {
                    "name": optimal_carrier[0].upper(),
                    "rate": optimal_rate,
                    "estimated_delivery": optimal_carrier[1]["estimated_delivery"],
                },
                "savings": savings_data,
                "recommendations": recommendations,
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating shipping arbitrage: {e}")
            return {
                "error": str(e),
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            }

    async def optimize_shipping(
        self, shipments: List[Dict[str, Any]], optimization_criteria: str = "cost"
    ) -> Dict[str, Any]:
        """Optimize shipping for multiple shipments."""
        try:
            optimized_shipments = []
            total_original_cost = 0
            total_optimized_cost = 0

            for shipment in shipments:
                # Calculate arbitrage for each shipment
                arbitrage_result = await self.calculate_arbitrage(
                    origin_zip=shipment.get("origin_zip", "90210"),
                    destination_zip=shipment.get("destination_zip", "10001"),
                    weight=shipment.get("weight", 1.0),
                    package_type=shipment.get("package_type", "standard"),
                    current_rate=shipment.get("current_rate"),
                )

                if "error" not in arbitrage_result:
                    optimized_shipments.append(
                        {
                            "shipment_id": shipment.get(
                                "id", f"shipment_{len(optimized_shipments) + 1}"
                            ),
                            "original_data": shipment,
                            "optimization": arbitrage_result,
                        }
                    )

                    # Track cost savings
                    if arbitrage_result.get("savings"):
                        total_original_cost += arbitrage_result["savings"].get(
                            "original_rate", 0
                        )
                        total_optimized_cost += arbitrage_result["savings"].get(
                            "optimized_rate", 0
                        )

            # Calculate overall savings
            total_savings = total_original_cost - total_optimized_cost
            savings_percentage = (
                (total_savings / total_original_cost * 100)
                if total_original_cost > 0
                else 0
            )

            return {
                "optimization_summary": {
                    "total_shipments": len(shipments),
                    "optimized_shipments": len(optimized_shipments),
                    "total_original_cost": round(total_original_cost, 2),
                    "total_optimized_cost": round(total_optimized_cost, 2),
                    "total_savings": round(total_savings, 2),
                    "savings_percentage": round(savings_percentage, 2),
                    "optimization_criteria": optimization_criteria,
                },
                "optimized_shipments": optimized_shipments,
                "optimized_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error optimizing shipping: {e}")
            return {
                "error": str(e),
                "optimized_at": datetime.now(timezone.utc).isoformat(),
            }

    async def track_savings(
        self,
        user_id: UUID,
        original_cost: float,
        optimized_cost: float,
        optimization_method: str,
        carrier_recommendations: Dict[str, Any],
        product_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Track shipping cost savings for revenue calculation."""
        try:
            savings_amount = original_cost - optimized_cost
            savings_percentage = (
                (savings_amount / original_cost * 100) if original_cost > 0 else 0
            )

            # Store in database
            calculation = await self.revenue_repository.create_arbitrage_calculation(
                user_id=user_id,
                original_shipping_cost=original_cost,
                optimized_shipping_cost=optimized_cost,
                savings_amount=savings_amount,
                savings_percentage=savings_percentage,
                optimization_method=optimization_method,
                carrier_recommendations=carrier_recommendations,
                product_id=product_id,
            )

            return {
                "calculation_id": str(calculation.id),
                "savings_tracked": {
                    "original_cost": original_cost,
                    "optimized_cost": optimized_cost,
                    "savings_amount": round(savings_amount, 2),
                    "savings_percentage": round(savings_percentage, 2),
                },
                "optimization_method": optimization_method,
                "tracked_at": calculation.created_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error tracking savings: {e}")
            return {
                "error": str(e),
                "tracked_at": datetime.now(timezone.utc).isoformat(),
            }

    def _get_estimated_delivery(
        self, carrier: str, zone: str, package_type: str
    ) -> str:
        """Get estimated delivery time for carrier and zone."""
        base_days = {
            "usps": {"standard": 3, "express": 2, "overnight": 1},
            "ups": {"standard": 3, "express": 2, "overnight": 1},
            "fedex": {"standard": 2, "express": 1, "overnight": 1},
            "dhl": {"standard": 4, "express": 2, "overnight": 1},
        }

        zone_adjustments = {
            "zone_1": 0,
            "zone_2": 0,
            "zone_3": 1,
            "zone_4": 1,
            "zone_5": 2,
            "zone_6": 2,
            "zone_7": 3,
            "zone_8": 4,
        }

        base = base_days.get(carrier, {}).get(package_type, 3)
        adjustment = zone_adjustments.get(zone, 1)
        total_days = base + adjustment

        return f"{total_days} business days"

    def _generate_shipping_recommendations(
        self, carrier_rates: Dict[str, Any], zone: str, weight: float, package_type: str
    ) -> List[str]:
        """Generate shipping optimization recommendations."""
        recommendations = []

        # Sort carriers by rate
        sorted_carriers = sorted(carrier_rates.items(), key=lambda x: x[1]["rate"])

        # Cost optimization recommendation
        cheapest = sorted_carriers[0]
        recommendations.append(
            f"Use {cheapest[0].upper()} for lowest cost (${cheapest[1]['rate']:.2f})"
        )

        # Speed vs cost recommendation
        if package_type == "standard" and len(sorted_carriers) > 1:
            second_cheapest = sorted_carriers[1]
            price_diff = second_cheapest[1]["rate"] - cheapest[1]["rate"]
            if price_diff < 2.00:
                recommendations.append(
                    f"Consider {second_cheapest[0].upper()} for only ${price_diff:.2f} more"
                )

        # Weight-based recommendations
        if weight > 5.0:
            recommendations.append(
                "Consider consolidating shipments to reduce per-pound costs"
            )

        # Zone-based recommendations
        if zone in ["zone_7", "zone_8"]:
            recommendations.append(
                "Consider regional fulfillment centers for distant zones"
            )

        return recommendations


# Global shipping arbitrage service instance
shipping_arbitrage_service = ShippingArbitrageService()
