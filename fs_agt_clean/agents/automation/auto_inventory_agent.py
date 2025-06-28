"""
Auto Inventory UnifiedAgent for FlipSync
Automated inventory management, purchasing, and stock optimization.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole

logger = logging.getLogger(__name__)


class InventoryAction(str, Enum):
    """Types of inventory actions."""

    REORDER = "reorder"
    PURCHASE = "purchase"
    LIQUIDATE = "liquidate"
    HOLD = "hold"
    MONITOR = "monitor"


class StockLevel(str, Enum):
    """Stock level categories."""

    OUT_OF_STOCK = "out_of_stock"
    LOW_STOCK = "low_stock"
    OPTIMAL = "optimal"
    OVERSTOCK = "overstock"
    EXCESS = "excess"


class PurchaseSource(str, Enum):
    """Sources for inventory purchases."""

    WHOLESALE = "wholesale"
    LIQUIDATION = "liquidation"
    RETAIL_ARBITRAGE = "retail_arbitrage"
    ONLINE_ARBITRAGE = "online_arbitrage"
    DIRECT_SUPPLIER = "direct_supplier"


@dataclass
class InventoryItem:
    """Represents an inventory item."""

    sku: str
    name: str
    category: str
    current_stock: int
    reorder_point: int
    max_stock: int
    cost: float
    selling_price: float
    sales_velocity: float  # units per day
    last_sold: Optional[datetime]
    supplier: str
    lead_time_days: int


@dataclass
class PurchaseRecommendation:
    """Automated purchase recommendation."""

    item_sku: str
    recommended_quantity: int
    estimated_cost: float
    source: PurchaseSource
    urgency: str  # high, medium, low
    reasoning: str
    confidence: float
    expected_roi: float
    payback_period_days: int
    timestamp: datetime


@dataclass
class InventoryAlert:
    """Inventory alert for attention."""

    item_sku: str
    alert_type: str
    severity: str  # critical, warning, info
    message: str
    recommended_action: InventoryAction
    timestamp: datetime


class AutoInventoryUnifiedAgent(BaseConversationalUnifiedAgent):
    """
    Automated inventory management agent.

    Capabilities:
    - Automated reorder point calculations
    - Purchase opportunity identification
    - Stock level optimization
    - Demand forecasting
    - Supplier performance monitoring
    - ROI-based purchasing decisions
    """

    def __init__(
        self, agent_id: str = "auto_inventory_agent", use_fast_model: bool = True
    ):
        """Initialize the auto inventory agent."""
        super().__init__(
            agent_role=UnifiedAgentRole.LOGISTICS,
            agent_id=agent_id,
            use_fast_model=use_fast_model,
        )

        # Inventory configuration
        self.inventory_items: Dict[str, InventoryItem] = {}
        self.purchase_recommendations: List[PurchaseRecommendation] = []
        self.inventory_alerts: List[InventoryAlert] = []
        self.auto_purchasing_enabled = False  # Safety feature
        self.monitoring_enabled = True

        # Configuration parameters
        self.min_roi_threshold = 0.20  # 20% minimum ROI
        self.max_payback_days = 90  # Maximum payback period
        self.safety_stock_multiplier = 1.5

        logger.info(f"AutoInventoryUnifiedAgent initialized: {self.agent_id}")

    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get agent-specific context for prompt generation."""
        return {
            "agent_type": "automated_inventory_specialist",
            "capabilities": [
                "Automated reorder management",
                "Purchase opportunity analysis",
                "Demand forecasting",
                "Stock optimization",
                "ROI-based purchasing",
                "Supplier performance tracking",
            ],
            "monitored_items": len(self.inventory_items),
            "active_recommendations": len(self.purchase_recommendations),
            "pending_alerts": len(self.inventory_alerts),
            "auto_purchasing": (
                "enabled" if self.auto_purchasing_enabled else "disabled"
            ),
        }

    async def analyze_inventory_needs(self) -> List[PurchaseRecommendation]:
        """Analyze inventory and generate purchase recommendations."""
        recommendations = []

        for sku, item in self.inventory_items.items():
            try:
                # Check stock level
                stock_level = self._categorize_stock_level(item)

                # Calculate reorder needs
                if stock_level in [StockLevel.OUT_OF_STOCK, StockLevel.LOW_STOCK]:
                    recommendation = await self._generate_reorder_recommendation(item)
                    if recommendation:
                        recommendations.append(recommendation)

                # Check for purchase opportunities
                opportunity = await self._identify_purchase_opportunity(item)
                if opportunity:
                    recommendations.append(opportunity)

            except Exception as e:
                logger.error(f"Error analyzing inventory for {sku}: {e}")

        self.purchase_recommendations = recommendations
        return recommendations

    def _categorize_stock_level(self, item: InventoryItem) -> StockLevel:
        """Categorize current stock level."""
        if item.current_stock == 0:
            return StockLevel.OUT_OF_STOCK
        elif item.current_stock <= item.reorder_point:
            return StockLevel.LOW_STOCK
        elif item.current_stock > item.max_stock:
            return StockLevel.OVERSTOCK
        elif item.current_stock > item.max_stock * 1.5:
            return StockLevel.EXCESS
        else:
            return StockLevel.OPTIMAL

    async def _generate_reorder_recommendation(
        self, item: InventoryItem
    ) -> Optional[PurchaseRecommendation]:
        """Generate reorder recommendation for low stock item."""
        try:
            # Calculate optimal order quantity
            daily_sales = item.sales_velocity
            lead_time_demand = daily_sales * item.lead_time_days
            safety_stock = lead_time_demand * self.safety_stock_multiplier

            # Economic Order Quantity (simplified)
            optimal_quantity = max(
                int(item.max_stock - item.current_stock),
                int(lead_time_demand + safety_stock),
            )

            # Calculate costs and ROI
            total_cost = optimal_quantity * item.cost
            expected_revenue = optimal_quantity * item.selling_price
            expected_roi = (
                (expected_revenue - total_cost) / total_cost if total_cost > 0 else 0
            )

            # Calculate payback period
            daily_profit = daily_sales * (item.selling_price - item.cost)
            payback_days = int(total_cost / daily_profit) if daily_profit > 0 else 999

            # Generate AI reasoning
            reasoning = await self._generate_purchase_reasoning(
                item, optimal_quantity, "reorder", expected_roi
            )

            # Determine urgency
            urgency = "high" if item.current_stock == 0 else "medium"

            return PurchaseRecommendation(
                item_sku=item.sku,
                recommended_quantity=optimal_quantity,
                estimated_cost=total_cost,
                source=PurchaseSource.DIRECT_SUPPLIER,
                urgency=urgency,
                reasoning=reasoning,
                confidence=0.8,
                expected_roi=expected_roi,
                payback_period_days=payback_days,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error(f"Error generating reorder recommendation: {e}")
            return None

    async def _identify_purchase_opportunity(
        self, item: InventoryItem
    ) -> Optional[PurchaseRecommendation]:
        """Identify potential purchase opportunities for profitable items."""
        try:
            # Only consider items with good sales velocity and profit margin
            if item.sales_velocity < 0.1:  # Less than 1 sale per 10 days
                return None

            profit_margin = (item.selling_price - item.cost) / item.selling_price
            if profit_margin < 0.15:  # Less than 15% margin
                return None

            # Check if we have room for more inventory
            if item.current_stock >= item.max_stock:
                return None

            # Calculate opportunity quantity
            opportunity_quantity = min(
                int(item.max_stock * 0.5),  # Don't overstock
                int(item.sales_velocity * 30),  # 30 days of sales
            )

            if opportunity_quantity < 1:
                return None

            # Calculate ROI
            total_cost = opportunity_quantity * item.cost
            expected_revenue = opportunity_quantity * item.selling_price
            expected_roi = (expected_revenue - total_cost) / total_cost

            # Only recommend if ROI meets threshold
            if expected_roi < self.min_roi_threshold:
                return None

            # Calculate payback period
            daily_profit = item.sales_velocity * (item.selling_price - item.cost)
            payback_days = int(total_cost / daily_profit) if daily_profit > 0 else 999

            if payback_days > self.max_payback_days:
                return None

            reasoning = await self._generate_purchase_reasoning(
                item, opportunity_quantity, "opportunity", expected_roi
            )

            return PurchaseRecommendation(
                item_sku=item.sku,
                recommended_quantity=opportunity_quantity,
                estimated_cost=total_cost,
                source=PurchaseSource.WHOLESALE,
                urgency="low",
                reasoning=reasoning,
                confidence=0.7,
                expected_roi=expected_roi,
                payback_period_days=payback_days,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error(f"Error identifying purchase opportunity: {e}")
            return None

    async def _generate_purchase_reasoning(
        self,
        item: InventoryItem,
        quantity: int,
        purchase_type: str,
        expected_roi: float,
    ) -> str:
        """Generate AI-powered reasoning for purchase recommendation."""
        try:
            prompt = f"""
            Analyze this inventory purchase recommendation:
            
            Item: {item.name} (SKU: {item.sku})
            Current Stock: {item.current_stock}
            Recommended Quantity: {quantity}
            Purchase Type: {purchase_type}
            
            Item Details:
            - Sales Velocity: {item.sales_velocity} units/day
            - Cost: ${item.cost:.2f}
            - Selling Price: ${item.selling_price:.2f}
            - Expected ROI: {expected_roi:.1%}
            - Supplier Lead Time: {item.lead_time_days} days
            
            Provide a clear, business-focused explanation for this purchase recommendation.
            """

            response = await self.llm_client.generate_response(
                prompt=prompt,
                system_prompt="You are an expert inventory analyst. Provide clear, data-driven reasoning for purchase decisions.",
            )

            return response.content

        except Exception as e:
            logger.error(f"Error generating purchase reasoning: {e}")
            return f"Automated {purchase_type} recommendation based on sales velocity and ROI analysis"

    async def forecast_demand(
        self, item_sku: str, days_ahead: int = 30
    ) -> Dict[str, Any]:
        """Forecast demand for an inventory item."""
        try:
            item = self.inventory_items.get(item_sku)
            if not item:
                raise ValueError(f"Item {item_sku} not found")

            # Simple demand forecasting (in production, would use more sophisticated models)
            base_demand = item.sales_velocity * days_ahead

            # Seasonal adjustments (simplified)
            current_month = datetime.now().month
            seasonal_multiplier = 1.0

            if item.category.lower() in ["electronics", "toys"] and current_month in [
                11,
                12,
            ]:
                seasonal_multiplier = 1.3  # Holiday boost
            elif item.category.lower() == "clothing" and current_month in [3, 4, 9, 10]:
                seasonal_multiplier = 1.1  # Season changes

            forecasted_demand = base_demand * seasonal_multiplier

            # Calculate confidence based on data quality
            confidence = min(
                1.0, item.sales_velocity * 10
            )  # More sales = higher confidence

            return {
                "item_sku": item_sku,
                "forecast_period_days": days_ahead,
                "forecasted_demand": round(forecasted_demand, 1),
                "confidence": confidence,
                "seasonal_factor": seasonal_multiplier,
                "base_velocity": item.sales_velocity,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error forecasting demand: {e}")
            raise

    async def _process_response(self, response: Any) -> str:
        """Process and format the response for inventory queries."""
        if hasattr(response, "content"):
            return response.content
        return str(response)

    async def handle_message(
        self, message: str, conversation_id: str, user_id: str
    ) -> UnifiedAgentResponse:
        """Handle inventory-related queries and requests."""
        try:
            system_prompt = """You are FlipSync's Auto Inventory UnifiedAgent, an expert in automated inventory management and purchasing optimization.

Your capabilities include:
- Automated reorder point calculations
- Purchase opportunity identification
- Demand forecasting and trend analysis
- Stock level optimization
- ROI-based purchasing decisions
- Supplier performance monitoring

Provide specific, data-driven inventory management advice and explain automated purchasing decisions clearly."""

            response = await self.llm_client.generate_response(
                prompt=message, system_prompt=system_prompt
            )

            return UnifiedAgentResponse(
                content=response.content,
                agent_type="auto_inventory",
                confidence=0.9,
                response_time=response.response_time,
                metadata={
                    "monitored_items": len(self.inventory_items),
                    "active_recommendations": len(self.purchase_recommendations),
                    "auto_purchasing_enabled": self.auto_purchasing_enabled,
                    "min_roi_threshold": self.min_roi_threshold,
                },
            )

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return UnifiedAgentResponse(
                content="I'm having trouble processing your inventory request right now. Please try again.",
                agent_type="auto_inventory",
                confidence=0.1,
                response_time=0.0,
            )
