"""Inventory metrics tracking module.

This module defines metrics for tracking inventory operations including:
- Inventory synchronization status
- Inventory quantities
- Offer status
- Synchronization times
- Error rates
"""

from typing import Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

# Inventory sync status metrics
INVENTORY_SYNC_TOTAL = Counter(
    "inventory_sync_total",
    "Total number of inventory synchronization operations",
    ["marketplace", "operation_type", "status"],
)

INVENTORY_SYNC_ERRORS = Counter(
    "inventory_sync_errors",
    "Total number of inventory synchronization errors",
    ["marketplace", "operation_type", "error_type"],
)

# Inventory quantity metrics
INVENTORY_QUANTITY = Gauge(
    "inventory_quantity", "Current inventory quantities", ["marketplace", "sku"]
)

LOW_INVENTORY_ITEMS = Gauge(
    "low_inventory_items", "Number of items with low inventory", ["marketplace"]
)

# Offer metrics
OFFER_PRICES = Gauge(
    "offer_prices", "Current offer prices", ["marketplace", "sku", "currency"]
)

OFFER_STATUS = Gauge(
    "offer_status",
    "Offer status (1 for active, 0 for inactive)",
    ["marketplace", "sku", "status"],
)

# Performance metrics
INVENTORY_SYNC_DURATION = Histogram(
    "inventory_sync_duration_seconds",
    "Time taken to complete inventory synchronization",
    ["marketplace", "operation_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

INVENTORY_SYNC_BATCH_SIZE = Histogram(
    "inventory_sync_batch_size",
    "Size of inventory synchronization batches",
    ["marketplace", "operation_type"],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000],
)


# Utility functions for inventory metrics
def record_inventory_sync(
    marketplace: str, operation_type: str, status: str = "success"
) -> None:
    """Record an inventory synchronization operation.

    Args:
        marketplace: The marketplace (e.g., 'ebay', 'amazon')
        operation_type: Type of operation (e.g., 'create', 'update', 'delete')
        status: Status of the operation ('success' or 'failure')
    """
    INVENTORY_SYNC_TOTAL.labels(
        marketplace=marketplace, operation_type=operation_type, status=status
    ).inc()


def record_inventory_sync_error(
    marketplace: str, operation_type: str, error_type: str
) -> None:
    """Record an inventory synchronization error.

    Args:
        marketplace: The marketplace (e.g., 'ebay', 'amazon')
        operation_type: Type of operation (e.g., 'create', 'update', 'delete')
        error_type: Type of error (e.g., 'network', 'validation', 'timeout')
    """
    INVENTORY_SYNC_ERRORS.labels(
        marketplace=marketplace, operation_type=operation_type, error_type=error_type
    ).inc()


def update_inventory_quantity(marketplace: str, sku: str, quantity: int) -> None:
    """Update the inventory quantity metric.

    Args:
        marketplace: The marketplace (e.g., 'ebay', 'amazon')
        sku: The SKU of the inventory item
        quantity: The current quantity
    """
    INVENTORY_QUANTITY.labels(marketplace=marketplace, sku=sku).set(quantity)


def update_low_inventory_count(marketplace: str, count: int) -> None:
    """Update the count of items with low inventory.

    Args:
        marketplace: The marketplace (e.g., 'ebay', 'amazon')
        count: The count of items with low inventory
    """
    LOW_INVENTORY_ITEMS.labels(marketplace=marketplace).set(count)


def update_offer_price(
    marketplace: str, sku: str, price: float, currency: str = "USD"
) -> None:
    """Update the offer price metric.

    Args:
        marketplace: The marketplace (e.g., 'ebay', 'amazon')
        sku: The SKU of the inventory item
        price: The current price
        currency: The currency code (default: USD)
    """
    OFFER_PRICES.labels(marketplace=marketplace, sku=sku, currency=currency).set(price)


def update_offer_status(
    marketplace: str, sku: str, status: str, is_active: bool = True
) -> None:
    """Update the offer status metric.

    Args:
        marketplace: The marketplace (e.g., 'ebay', 'amazon')
        sku: The SKU of the inventory item
        status: The status description (e.g., 'published', 'draft')
        is_active: Whether the offer is active (default: True)
    """
    OFFER_STATUS.labels(marketplace=marketplace, sku=sku, status=status).set(
        1 if is_active else 0
    )


def observe_sync_duration(
    marketplace: str, operation_type: str, duration_seconds: float
) -> None:
    """Record the duration of an inventory synchronization operation.

    Args:
        marketplace: The marketplace (e.g., 'ebay', 'amazon')
        operation_type: Type of operation (e.g., 'create', 'update', 'delete', 'batch')
        duration_seconds: The duration in seconds
    """
    INVENTORY_SYNC_DURATION.labels(
        marketplace=marketplace, operation_type=operation_type
    ).observe(duration_seconds)


def observe_batch_size(marketplace: str, operation_type: str, size: int) -> None:
    """Record the size of an inventory synchronization batch.

    Args:
        marketplace: The marketplace (e.g., 'ebay', 'amazon')
        operation_type: Type of operation (e.g., 'create', 'update', 'delete')
        size: The batch size
    """
    INVENTORY_SYNC_BATCH_SIZE.labels(
        marketplace=marketplace, operation_type=operation_type
    ).observe(size)


def get_inventory_metrics_snapshot(marketplace: Optional[str] = None) -> Dict:
    """Get a snapshot of current inventory metrics.

    Args:
        marketplace: Optional marketplace filter

    Returns:
        Dict containing current inventory metrics
    """
    # Note: This would need implementation to collect from Prometheus
    # This is a placeholder for the function signature
    return {
        "inventory_sync_success_rate": 0.0,
        "inventory_sync_error_rate": 0.0,
        "low_inventory_count": 0,
        "avg_sync_duration": 0.0,
        "total_active_offers": 0,
    }
