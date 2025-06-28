"""
Inventory optimization service for FlipSync.

This module provides intelligent inventory optimization capabilities including:
- Storage layout optimization
- Reorder point calculation
- Demand forecasting
- Stock level optimization
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.config.manager import ConfigManager

logger = logging.getLogger(__name__)


class InventoryOptimizer:
    """Intelligent inventory optimization service."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the inventory optimizer.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.optimization_config = config_manager.get("inventory_optimization", {})
        
        # Default optimization parameters
        self.default_safety_stock_days = self.optimization_config.get("safety_stock_days", 7)
        self.default_lead_time_days = self.optimization_config.get("lead_time_days", 14)
        self.min_reorder_quantity = self.optimization_config.get("min_reorder_quantity", 1)
        self.max_storage_utilization = self.optimization_config.get("max_storage_utilization", 0.85)

    async def optimize_storage(
        self, 
        items: List[Any], 
        current_layout: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Optimize storage layout for better efficiency.
        
        Args:
            items: List of inventory items
            current_layout: Current storage layout
            
        Returns:
            Optimized storage layout
        """
        try:
            # Create optimized layout based on item characteristics
            optimized_layout = {location: [] for location in current_layout.keys()}
            
            # Sort items by optimization criteria
            sorted_items = self._sort_items_for_optimization(items)
            
            # Assign items to optimal locations
            for item in sorted_items:
                optimal_location = self._find_optimal_location(item, optimized_layout)
                optimized_layout[optimal_location].append(item.id)
            
            logger.info(f"Storage optimization completed for {len(items)} items")
            return optimized_layout
            
        except Exception as e:
            logger.error(f"Storage optimization failed: {e}")
            # Return current layout if optimization fails
            return current_layout

    def calculate_reorder_point(self, item: Any) -> int:
        """Calculate optimal reorder point for an item.
        
        Args:
            item: Inventory item
            
        Returns:
            Reorder point quantity
        """
        try:
            # Get item-specific parameters
            lead_time_days = getattr(item, 'lead_time_days', self.default_lead_time_days)
            safety_stock_days = getattr(item, 'safety_stock_days', self.default_safety_stock_days)
            
            # Calculate average daily demand
            daily_demand = self._calculate_daily_demand(item)
            
            # Calculate reorder point: (lead time + safety stock) * daily demand
            reorder_point = (lead_time_days + safety_stock_days) * daily_demand
            
            # Ensure minimum reorder quantity
            reorder_point = max(reorder_point, self.min_reorder_quantity)
            
            logger.debug(f"Calculated reorder point for {item.id}: {reorder_point}")
            return int(reorder_point)
            
        except Exception as e:
            logger.error(f"Failed to calculate reorder point for {item.id}: {e}")
            # Return conservative default
            return max(10, int(item.quantity * 0.2))

    def calculate_optimal_order_quantity(self, item: Any) -> int:
        """Calculate optimal order quantity using Economic Order Quantity (EOQ) model.
        
        Args:
            item: Inventory item
            
        Returns:
            Optimal order quantity
        """
        try:
            # Get parameters for EOQ calculation
            annual_demand = self._calculate_annual_demand(item)
            ordering_cost = getattr(item, 'ordering_cost', 50.0)  # Default ordering cost
            holding_cost_rate = getattr(item, 'holding_cost_rate', 0.2)  # 20% of item cost
            item_cost = getattr(item, 'price', 0.0)
            
            if annual_demand <= 0 or item_cost <= 0:
                # Fallback to simple calculation
                return max(self.min_reorder_quantity, int(item.quantity * 0.5))
            
            # EOQ formula: sqrt((2 * D * S) / (H * C))
            # D = annual demand, S = ordering cost, H = holding cost rate, C = item cost
            holding_cost = holding_cost_rate * item_cost
            
            if holding_cost <= 0:
                holding_cost = item_cost * 0.2  # Default 20%
            
            eoq = ((2 * annual_demand * ordering_cost) / holding_cost) ** 0.5
            
            # Round to reasonable quantity and apply constraints
            optimal_quantity = max(self.min_reorder_quantity, int(eoq))
            
            logger.debug(f"Calculated EOQ for {item.id}: {optimal_quantity}")
            return optimal_quantity
            
        except Exception as e:
            logger.error(f"Failed to calculate EOQ for {item.id}: {e}")
            # Return conservative default
            return max(self.min_reorder_quantity, int(item.quantity * 0.5))

    def predict_demand(self, item: Any, days_ahead: int = 30) -> float:
        """Predict future demand for an item.
        
        Args:
            item: Inventory item
            days_ahead: Number of days to predict ahead
            
        Returns:
            Predicted demand
        """
        try:
            # Simple trend-based prediction
            daily_demand = self._calculate_daily_demand(item)
            
            # Apply seasonal and trend adjustments
            seasonal_factor = self._get_seasonal_factor(item)
            trend_factor = self._get_trend_factor(item)
            
            predicted_demand = daily_demand * days_ahead * seasonal_factor * trend_factor
            
            logger.debug(f"Predicted {days_ahead}-day demand for {item.id}: {predicted_demand}")
            return max(0, predicted_demand)
            
        except Exception as e:
            logger.error(f"Failed to predict demand for {item.id}: {e}")
            # Return conservative estimate
            return max(1, item.quantity * 0.1)

    def _sort_items_for_optimization(self, items: List[Any]) -> List[Any]:
        """Sort items by optimization criteria."""
        try:
            # Sort by: 1) Sales velocity (high first), 2) Value (high first), 3) Size (small first)
            return sorted(
                items,
                key=lambda item: (
                    -getattr(item, 'sales_velocity', 0),  # High velocity first
                    -getattr(item, 'price', 0),  # High value first
                    getattr(item, 'size_score', 1)  # Small size first
                )
            )
        except Exception as e:
            logger.error(f"Failed to sort items: {e}")
            return items

    def _find_optimal_location(self, item: Any, layout: Dict[str, List[str]]) -> str:
        """Find optimal storage location for an item."""
        try:
            # Prioritize locations based on item characteristics
            item_velocity = getattr(item, 'sales_velocity', 0)
            
            # High-velocity items go to easily accessible locations
            if item_velocity > 1.0:  # More than 1 unit per day
                # Prefer retail/front locations for fast-moving items
                for location in ['retail', 'front', 'warehouse']:
                    if location in layout:
                        current_count = len(layout[location])
                        max_capacity = self._get_location_capacity(location)
                        if current_count < max_capacity:
                            return location
            
            # Default to warehouse for slower-moving items
            for location in ['warehouse', 'storage', 'retail']:
                if location in layout:
                    current_count = len(layout[location])
                    max_capacity = self._get_location_capacity(location)
                    if current_count < max_capacity:
                        return location
            
            # Fallback to first available location
            return list(layout.keys())[0]
            
        except Exception as e:
            logger.error(f"Failed to find optimal location for {item.id}: {e}")
            return list(layout.keys())[0]

    def _calculate_daily_demand(self, item: Any) -> float:
        """Calculate average daily demand for an item."""
        try:
            # Use sales velocity if available
            sales_velocity = getattr(item, 'sales_velocity', 0)
            if sales_velocity > 0:
                return sales_velocity
            
            # Fallback calculation based on turnover
            initial_quantity = getattr(item, 'initial_quantity', item.quantity)
            current_quantity = item.quantity
            
            if initial_quantity > current_quantity:
                # Estimate based on quantity sold
                quantity_sold = initial_quantity - current_quantity
                # Assume 30 days since initial stock
                return quantity_sold / 30.0
            
            # Conservative default
            return 0.1
            
        except Exception as e:
            logger.error(f"Failed to calculate daily demand for {item.id}: {e}")
            return 0.1

    def _calculate_annual_demand(self, item: Any) -> float:
        """Calculate annual demand for an item."""
        daily_demand = self._calculate_daily_demand(item)
        return daily_demand * 365

    def _get_seasonal_factor(self, item: Any) -> float:
        """Get seasonal adjustment factor."""
        # Simple seasonal factor based on current month
        # This could be enhanced with historical data
        current_month = datetime.now().month
        
        # Basic seasonal patterns (could be item-category specific)
        seasonal_factors = {
            12: 1.3,  # December - holiday season
            11: 1.2,  # November - pre-holiday
            1: 0.8,   # January - post-holiday
            2: 0.9,   # February - low season
        }
        
        return seasonal_factors.get(current_month, 1.0)

    def _get_trend_factor(self, item: Any) -> float:
        """Get trend adjustment factor."""
        # Simple trend factor based on recent sales velocity
        # This could be enhanced with more sophisticated trend analysis
        sales_velocity = getattr(item, 'sales_velocity', 0)
        
        if sales_velocity > 2.0:
            return 1.2  # Growing trend
        elif sales_velocity < 0.5:
            return 0.8  # Declining trend
        else:
            return 1.0  # Stable trend

    def _get_location_capacity(self, location: str) -> int:
        """Get maximum capacity for a storage location."""
        # Default capacities - could be configured
        capacities = {
            'retail': 50,
            'front': 100,
            'warehouse': 1000,
            'storage': 500,
        }
        
        return capacities.get(location, 100)
