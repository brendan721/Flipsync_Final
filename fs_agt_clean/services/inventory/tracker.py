"""
Inventory tracking service for FlipSync.

This module provides comprehensive inventory tracking capabilities including:
- Transaction tracking and history
- Stock movement monitoring
- Performance metrics calculation
- Audit trail maintenance
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class InventoryTracker:
    """Comprehensive inventory tracking service."""

    def __init__(self):
        """Initialize the inventory tracker."""
        self.transaction_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.audit_trail: List[Dict[str, Any]] = []

    async def track_transaction(self, transaction: Any) -> None:
        """Track an inventory transaction.

        Args:
            transaction: Inventory transaction to track
        """
        try:
            # Convert transaction to trackable format
            transaction_data = {
                "id": transaction.id,
                "item_id": transaction.item_id,
                "quantity": transaction.quantity,
                "transaction_type": transaction.transaction_type,
                "timestamp": transaction.timestamp,
                "notes": getattr(transaction, "notes", None),
                "tracked_at": datetime.now(timezone.utc),
            }

            # Add to transaction history
            self.transaction_history.append(transaction_data)

            # Update performance metrics
            await self._update_performance_metrics(transaction_data)

            # Add to audit trail
            await self._add_to_audit_trail(transaction_data)

            logger.debug(
                f"Tracked transaction {transaction.id} for item {transaction.item_id}"
            )

        except Exception as e:
            logger.error(f"Failed to track transaction {transaction.id}: {e}")

    async def get_item_history(self, item_id: str) -> List[Dict[str, Any]]:
        """Get transaction history for a specific item.

        Args:
            item_id: Item ID to get history for

        Returns:
            List of transactions for the item
        """
        try:
            item_transactions = [
                txn for txn in self.transaction_history if txn["item_id"] == item_id
            ]

            # Sort by timestamp (most recent first)
            item_transactions.sort(key=lambda x: x["timestamp"], reverse=True)

            return item_transactions

        except Exception as e:
            logger.error(f"Failed to get history for item {item_id}: {e}")
            return []

    async def get_performance_metrics(
        self, item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for an item or overall.

        Args:
            item_id: Optional item ID to get metrics for

        Returns:
            Performance metrics
        """
        try:
            if item_id:
                return self.performance_metrics.get(item_id, {})
            else:
                return self.performance_metrics.get("overall", {})

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}

    async def calculate_turnover_rate(self, item_id: str, days: int = 30) -> float:
        """Calculate inventory turnover rate for an item.

        Args:
            item_id: Item ID
            days: Number of days to calculate over

        Returns:
            Turnover rate
        """
        try:
            # Get sales transactions for the period
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            sales_transactions = [
                txn
                for txn in self.transaction_history
                if (
                    txn["item_id"] == item_id
                    and txn["transaction_type"] == "sale"
                    and txn["timestamp"] >= cutoff_date
                )
            ]

            if not sales_transactions:
                return 0.0

            # Calculate total quantity sold
            total_sold = sum(txn["quantity"] for txn in sales_transactions)

            # Get average inventory level (simplified)
            avg_inventory = self._calculate_average_inventory(item_id, days)

            if avg_inventory <= 0:
                return 0.0

            # Turnover rate = total sold / average inventory
            turnover_rate = total_sold / avg_inventory

            return turnover_rate

        except Exception as e:
            logger.error(f"Failed to calculate turnover rate for {item_id}: {e}")
            return 0.0

    async def get_stock_alerts(self) -> List[Dict[str, Any]]:
        """Get stock level alerts based on transaction patterns.

        Returns:
            List of stock alerts
        """
        try:
            alerts = []

            # Analyze recent transaction patterns
            recent_transactions = self._get_recent_transactions(days=7)

            # Group by item
            item_activity = {}
            for txn in recent_transactions:
                item_id = txn["item_id"]
                if item_id not in item_activity:
                    item_activity[item_id] = {"sales": 0, "restocks": 0}

                if txn["transaction_type"] == "sale":
                    item_activity[item_id]["sales"] += txn["quantity"]
                elif txn["transaction_type"] in ["add", "restock"]:
                    item_activity[item_id]["restocks"] += txn["quantity"]

            # Generate alerts for items with high sales and no restocks
            for item_id, activity in item_activity.items():
                if activity["sales"] > 5 and activity["restocks"] == 0:
                    alerts.append(
                        {
                            "item_id": item_id,
                            "alert_type": "high_sales_no_restock",
                            "message": f'Item {item_id} has high sales ({activity["sales"]}) but no restocks',
                            "severity": "medium",
                            "timestamp": datetime.now(timezone.utc),
                        }
                    )

            return alerts

        except Exception as e:
            logger.error(f"Failed to get stock alerts: {e}")
            return []

    async def _update_performance_metrics(
        self, transaction_data: Dict[str, Any]
    ) -> None:
        """Update performance metrics based on transaction."""
        try:
            item_id = transaction_data["item_id"]

            # Initialize metrics for item if not exists
            if item_id not in self.performance_metrics:
                self.performance_metrics[item_id] = {
                    "total_transactions": 0,
                    "total_sales": 0,
                    "total_quantity_sold": 0,
                    "last_sale_date": None,
                    "average_sale_quantity": 0,
                    "sales_velocity": 0,
                }

            metrics = self.performance_metrics[item_id]
            metrics["total_transactions"] += 1

            # Update sales-specific metrics
            if transaction_data["transaction_type"] == "sale":
                metrics["total_sales"] += 1
                metrics["total_quantity_sold"] += transaction_data["quantity"]
                metrics["last_sale_date"] = transaction_data["timestamp"]

                # Calculate average sale quantity
                if metrics["total_sales"] > 0:
                    metrics["average_sale_quantity"] = (
                        metrics["total_quantity_sold"] / metrics["total_sales"]
                    )

                # Update sales velocity (simplified)
                metrics["sales_velocity"] = self._calculate_sales_velocity(item_id)

            # Update overall metrics
            if "overall" not in self.performance_metrics:
                self.performance_metrics["overall"] = {
                    "total_transactions": 0,
                    "total_items_tracked": 0,
                    "active_items": set(),
                }

            overall = self.performance_metrics["overall"]
            overall["total_transactions"] += 1
            overall["active_items"].add(item_id)
            overall["total_items_tracked"] = len(overall["active_items"])

        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")

    async def _add_to_audit_trail(self, transaction_data: Dict[str, Any]) -> None:
        """Add transaction to audit trail."""
        try:
            audit_entry = {
                "audit_id": f"audit_{datetime.now().timestamp()}",
                "transaction_id": transaction_data["id"],
                "item_id": transaction_data["item_id"],
                "action": transaction_data["transaction_type"],
                "quantity": transaction_data["quantity"],
                "timestamp": transaction_data["timestamp"],
                "audit_timestamp": datetime.now(timezone.utc),
                "metadata": {
                    "notes": transaction_data.get("notes"),
                    "tracked_by": "InventoryTracker",
                },
            }

            self.audit_trail.append(audit_entry)

            # Keep audit trail manageable (last 1000 entries)
            if len(self.audit_trail) > 1000:
                self.audit_trail = self.audit_trail[-1000:]

        except Exception as e:
            logger.error(f"Failed to add to audit trail: {e}")

    def _calculate_average_inventory(self, item_id: str, days: int) -> float:
        """Calculate average inventory level for an item over a period."""
        try:
            # Simplified calculation - could be enhanced with more sophisticated tracking
            # For now, assume current quantity represents average

            # Get recent transactions to estimate inventory levels
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            item_transactions = [
                txn
                for txn in self.transaction_history
                if (txn["item_id"] == item_id and txn["timestamp"] >= cutoff_date)
            ]

            if not item_transactions:
                return 0.0

            # Simple estimation based on transaction volumes
            total_volume = sum(abs(txn["quantity"]) for txn in item_transactions)
            return total_volume / len(item_transactions) if item_transactions else 0.0

        except Exception as e:
            logger.error(f"Failed to calculate average inventory for {item_id}: {e}")
            return 0.0

    def _calculate_sales_velocity(self, item_id: str) -> float:
        """Calculate sales velocity for an item."""
        try:
            # Get sales transactions from last 30 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

            sales_transactions = [
                txn
                for txn in self.transaction_history
                if (
                    txn["item_id"] == item_id
                    and txn["transaction_type"] == "sale"
                    and txn["timestamp"] >= cutoff_date
                )
            ]

            if not sales_transactions:
                return 0.0

            total_sold = sum(txn["quantity"] for txn in sales_transactions)
            return total_sold / 30.0  # Units per day

        except Exception as e:
            logger.error(f"Failed to calculate sales velocity for {item_id}: {e}")
            return 0.0

    def _get_recent_transactions(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get transactions from the last N days."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            return [
                txn
                for txn in self.transaction_history
                if txn["timestamp"] >= cutoff_date
            ]

        except Exception as e:
            logger.error(f"Failed to get recent transactions: {e}")
            return []
