"""
Warehouse UnifiedAgent for FlipSync logistics management.

This agent provides warehouse management capabilities including storage optimization,
picking efficiency, and inventory organization as described in AGENTIC_SYSTEM_OVERVIEW.md.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from fs_agt_clean.agents.base.base import BaseUnifiedAgent

logger = logging.getLogger(__name__)


@dataclass
class WarehouseLocation:
    """Represents a warehouse storage location."""

    location_id: str
    zone: str
    aisle: str
    shelf: str
    bin: str
    capacity: int
    current_stock: int = 0
    product_types: List[str] = field(default_factory=list)
    accessibility_score: float = 1.0
    last_accessed: Optional[datetime] = None


@dataclass
class PickingTask:
    """Represents a picking task in the warehouse."""

    order_id: str
    task_id: UUID = field(default_factory=uuid4)
    items: List[Dict[str, Any]] = field(default_factory=list)
    priority: str = "normal"  # low, normal, high, urgent
    estimated_time: int = 0  # minutes
    assigned_picker: Optional[str] = None
    status: str = "pending"  # pending, assigned, in_progress, completed
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class WarehouseMetrics:
    """Warehouse performance metrics."""

    total_locations: int = 0
    occupied_locations: int = 0
    utilization_rate: float = 0.0
    avg_picking_time: float = 0.0
    picking_accuracy: float = 0.0
    throughput_per_hour: float = 0.0
    space_efficiency: float = 0.0


class WarehouseUnifiedAgent(BaseUnifiedAgent):
    """
    Warehouse UnifiedAgent for logistics management.

    Provides warehouse management capabilities including:
    - Storage optimization
    - Picking efficiency
    - Inventory organization
    - Space utilization
    - Workflow management
    """

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Warehouse UnifiedAgent.

        Args:
            agent_id: Unique identifier for this agent instance
            config: Optional configuration dictionary
        """
        super().__init__(agent_id=agent_id, config=config or {})
        self.warehouse_locations: Dict[str, WarehouseLocation] = {}
        self.picking_tasks: Dict[str, PickingTask] = {}
        self.metrics = WarehouseMetrics()
        self.optimization_rules: Dict[str, Any] = {
            "fast_moving_items_near_dock": True,
            "heavy_items_ground_level": True,
            "fragile_items_secure_zones": True,
            "seasonal_items_flexible_zones": True,
        }

        logger.info(f"WarehouseUnifiedAgent {agent_id} initialized")

    async def add_warehouse_location(
        self,
        location_id: str,
        zone: str,
        aisle: str,
        shelf: str,
        bin: str,
        capacity: int,
        accessibility_score: float = 1.0,
    ) -> WarehouseLocation:
        """
        Add a new warehouse location.

        Args:
            location_id: Unique location identifier
            zone: Warehouse zone
            aisle: Aisle identifier
            shelf: Shelf identifier
            bin: Bin identifier
            capacity: Storage capacity
            accessibility_score: Accessibility rating (0.0-1.0)

        Returns:
            Created warehouse location
        """
        location = WarehouseLocation(
            location_id=location_id,
            zone=zone,
            aisle=aisle,
            shelf=shelf,
            bin=bin,
            capacity=capacity,
            accessibility_score=accessibility_score,
        )

        self.warehouse_locations[location_id] = location
        self._update_metrics()

        logger.info(f"Added warehouse location: {location_id}")
        return location

    async def optimize_storage_layout(self) -> Dict[str, Any]:
        """
        Optimize warehouse storage layout based on product characteristics.

        Returns:
            Optimization recommendations
        """
        recommendations = []

        # Analyze current layout efficiency
        high_traffic_zones = self._identify_high_traffic_zones()
        slow_moving_items = self._identify_slow_moving_items()

        # Generate recommendations
        for item_type, locations in slow_moving_items.items():
            if any(loc.zone in high_traffic_zones for loc in locations):
                recommendations.append(
                    {
                        "type": "relocate_slow_moving",
                        "item_type": item_type,
                        "current_zones": [loc.zone for loc in locations],
                        "recommended_zones": self._get_low_traffic_zones(),
                        "reason": "Move slow-moving items away from high-traffic areas",
                    }
                )

        # Check for heavy items on upper shelves
        for location in self.warehouse_locations.values():
            if location.shelf.startswith("upper") and location.current_stock > 0:
                # Check if heavy items are stored here
                if self._has_heavy_items(location):
                    recommendations.append(
                        {
                            "type": "relocate_heavy_items",
                            "location": location.location_id,
                            "reason": "Move heavy items to ground level for safety",
                        }
                    )

        optimization_result = {
            "recommendations": recommendations,
            "current_efficiency": self._calculate_layout_efficiency(),
            "potential_improvement": len(recommendations)
            * 0.05,  # 5% per recommendation
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Generated {len(recommendations)} storage optimization recommendations"
        )
        return optimization_result

    async def create_picking_task(
        self, order_id: str, items: List[Dict[str, Any]], priority: str = "normal"
    ) -> PickingTask:
        """
        Create a new picking task.

        Args:
            order_id: Order identifier
            items: List of items to pick
            priority: Task priority level

        Returns:
            Created picking task
        """
        # Estimate picking time based on item locations
        estimated_time = self._estimate_picking_time(items)

        task = PickingTask(
            order_id=order_id,
            items=items,
            priority=priority,
            estimated_time=estimated_time,
        )

        self.picking_tasks[str(task.task_id)] = task

        logger.info(
            f"Created picking task for order {order_id} with {len(items)} items"
        )
        return task

    async def optimize_picking_route(self, task_id: str) -> Dict[str, Any]:
        """
        Optimize picking route for a task.

        Args:
            task_id: Picking task identifier

        Returns:
            Optimized picking route
        """
        if task_id not in self.picking_tasks:
            raise ValueError(f"Picking task {task_id} not found")

        task = self.picking_tasks[task_id]

        # Get item locations
        item_locations = []
        for item in task.items:
            location = self._find_item_location(item.get("sku", ""))
            if location:
                item_locations.append(
                    {
                        "item": item,
                        "location": location,
                        "zone": location.zone,
                        "aisle": location.aisle,
                        "shelf": location.shelf,
                    }
                )

        # Optimize route using zone-based clustering
        optimized_route = self._calculate_optimal_route(item_locations)

        # Update estimated time with optimized route
        optimized_time = self._calculate_route_time(optimized_route)
        task.estimated_time = optimized_time

        route_result = {
            "task_id": task_id,
            "optimized_route": optimized_route,
            "estimated_time": optimized_time,
            "distance_saved": max(0, task.estimated_time - optimized_time),
            "efficiency_gain": max(
                0, (task.estimated_time - optimized_time) / task.estimated_time * 100
            ),
        }

        logger.info(
            f"Optimized picking route for task {task_id}, saved {route_result['distance_saved']} minutes"
        )
        return route_result

    def _identify_high_traffic_zones(self) -> List[str]:
        """Identify high-traffic warehouse zones."""
        zone_access_counts = {}

        for location in self.warehouse_locations.values():
            if location.last_accessed:
                zone_access_counts[location.zone] = (
                    zone_access_counts.get(location.zone, 0) + 1
                )

        # Return top 20% of zones by access count
        sorted_zones = sorted(
            zone_access_counts.items(), key=lambda x: x[1], reverse=True
        )
        high_traffic_count = max(1, len(sorted_zones) // 5)

        return [zone for zone, _ in sorted_zones[:high_traffic_count]]

    def _identify_slow_moving_items(self) -> Dict[str, List[WarehouseLocation]]:
        """Identify slow-moving items and their locations."""
        slow_moving = {}

        for location in self.warehouse_locations.values():
            if location.last_accessed:
                days_since_access = (datetime.utcnow() - location.last_accessed).days
                if days_since_access > 30:  # Not accessed in 30 days
                    for product_type in location.product_types:
                        if product_type not in slow_moving:
                            slow_moving[product_type] = []
                        slow_moving[product_type].append(location)

        return slow_moving

    def _get_low_traffic_zones(self) -> List[str]:
        """Get low-traffic warehouse zones."""
        high_traffic = self._identify_high_traffic_zones()
        all_zones = set(loc.zone for loc in self.warehouse_locations.values())
        return list(all_zones - set(high_traffic))

    def _has_heavy_items(self, location: WarehouseLocation) -> bool:
        """Check if location contains heavy items."""
        # This would typically check against product database
        # For now, use heuristic based on product types
        heavy_item_keywords = ["furniture", "appliance", "machinery", "equipment"]
        return any(
            keyword in product_type.lower()
            for product_type in location.product_types
            for keyword in heavy_item_keywords
        )

    def _calculate_layout_efficiency(self) -> float:
        """Calculate current warehouse layout efficiency."""
        if not self.warehouse_locations:
            return 0.0

        total_efficiency = 0.0
        for location in self.warehouse_locations.values():
            # Factor in utilization and accessibility
            utilization = (
                location.current_stock / location.capacity
                if location.capacity > 0
                else 0
            )
            efficiency = utilization * location.accessibility_score
            total_efficiency += efficiency

        return total_efficiency / len(self.warehouse_locations)

    def _estimate_picking_time(self, items: List[Dict[str, Any]]) -> int:
        """Estimate picking time for items in minutes."""
        base_time_per_item = 2  # 2 minutes per item
        travel_time = (
            len(set(item.get("zone", "A") for item in items)) * 3
        )  # 3 minutes per zone
        return len(items) * base_time_per_item + travel_time

    def _find_item_location(self, sku: str) -> Optional[WarehouseLocation]:
        """Find warehouse location for an item SKU."""
        # This would typically query inventory database
        # For now, return first available location
        for location in self.warehouse_locations.values():
            if location.current_stock > 0:
                return location
        return None

    def _calculate_optimal_route(
        self, item_locations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate optimal picking route."""
        # Sort by zone, then aisle, then shelf for efficient picking
        return sorted(item_locations, key=lambda x: (x["zone"], x["aisle"], x["shelf"]))

    def _calculate_route_time(self, route: List[Dict[str, Any]]) -> int:
        """Calculate time for optimized route."""
        if not route:
            return 0

        base_time = len(route) * 2  # 2 minutes per item

        # Add travel time between zones
        zones_visited = []
        for item in route:
            if item["zone"] not in zones_visited:
                zones_visited.append(item["zone"])

        travel_time = len(zones_visited) * 3  # 3 minutes per zone
        return base_time + travel_time

    def _update_metrics(self) -> None:
        """Update warehouse metrics."""
        if not self.warehouse_locations:
            return

        total_locations = len(self.warehouse_locations)
        occupied_locations = sum(
            1 for loc in self.warehouse_locations.values() if loc.current_stock > 0
        )

        self.metrics.total_locations = total_locations
        self.metrics.occupied_locations = occupied_locations
        self.metrics.utilization_rate = (
            occupied_locations / total_locations if total_locations > 0 else 0.0
        )
        self.metrics.space_efficiency = self._calculate_layout_efficiency()

    async def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process incoming message.

        Args:
            message: Message to process
        """
        message_type = message.get("type", "unknown")

        if message_type == "optimize_storage":
            await self.optimize_storage_layout()
        elif message_type == "create_picking_task":
            await self.create_picking_task(
                order_id=message.get("order_id", ""),
                items=message.get("items", []),
                priority=message.get("priority", "normal"),
            )
        elif message_type == "optimize_picking_route":
            await self.optimize_picking_route(message.get("task_id", ""))
        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def take_action(self, action: Dict[str, Any]) -> None:
        """
        Take a specific action.

        Args:
            action: Action dictionary containing action type and parameters
        """
        action_type = action.get("type", "unknown")
        params = action.get("parameters", {})

        if action_type == "optimize_storage":
            await self.optimize_storage_layout()
        elif action_type == "create_picking_task":
            await self.create_picking_task(
                order_id=params.get("order_id", ""),
                items=params.get("items", []),
                priority=params.get("priority", "normal"),
            )
        else:
            logger.warning(f"Unknown action type: {action_type}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status.

        Returns:
            UnifiedAgent status information
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": "WarehouseUnifiedAgent",
            "total_locations": self.metrics.total_locations,
            "utilization_rate": self.metrics.utilization_rate,
            "active_picking_tasks": len(
                [t for t in self.picking_tasks.values() if t.status != "completed"]
            ),
            "space_efficiency": self.metrics.space_efficiency,
            "status": "operational",
            "last_activity": datetime.utcnow().isoformat(),
        }
