"""
Inventory API endpoints for FlipSync.

This module implements the API endpoints for inventory management,
including:
- Inventory item creation, retrieval, update, and deletion
- Inventory quantity adjustments
- Inventory transaction history
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from fs_agt_clean.core.config import get_settings
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.models.api_response import ApiResponse
from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.security.auth import get_current_user
from fs_agt_clean.services.inventory.adapter import InventoryServiceAdapter

logger = logging.getLogger(__name__)


# Pydantic models for request/response validation
class InventoryItemCreate(BaseModel):
    """Model for creating inventory items."""

    sku: str = Field(
        ..., description="Stock Keeping Unit", min_length=1, max_length=100
    )
    name: str = Field(..., description="Item name", min_length=1, max_length=255)
    description: Optional[str] = Field(
        None, description="Item description", max_length=1000
    )
    quantity: int = Field(..., description="Initial quantity", ge=0)
    price: Optional[Decimal] = Field(None, description="Item price", ge=0)
    cost: Optional[Decimal] = Field(None, description="Item cost", ge=0)
    category: Optional[str] = Field(None, description="Item category", max_length=100)
    location: Optional[str] = Field(
        None, description="Storage location", max_length=100
    )
    low_stock_threshold: Optional[int] = Field(
        None, description="Minimum stock level", ge=0
    )


class InventoryItemUpdate(BaseModel):
    """Model for updating inventory items."""

    name: Optional[str] = Field(
        None, description="Item name", min_length=1, max_length=255
    )
    description: Optional[str] = Field(
        None, description="Item description", max_length=1000
    )
    price: Optional[Decimal] = Field(None, description="Item price", ge=0)
    cost: Optional[Decimal] = Field(None, description="Item cost", ge=0)
    category: Optional[str] = Field(None, description="Item category", max_length=100)
    location: Optional[str] = Field(
        None, description="Storage location", max_length=100
    )
    low_stock_threshold: Optional[int] = Field(
        None, description="Minimum stock level", ge=0
    )


class InventoryAdjustment(BaseModel):
    """Model for inventory quantity adjustments."""

    quantity: int = Field(..., description="Adjustment quantity (positive or negative)")
    transaction_type: str = Field(
        ...,
        description="Type of transaction",
        pattern="^(sale|purchase|adjustment|return|damage|transfer)$",
    )
    notes: Optional[str] = Field(None, description="Adjustment notes", max_length=500)
    reference: Optional[str] = Field(
        None, description="Reference number", max_length=100
    )


class InventoryItemResponse(BaseModel):
    """Model for inventory item responses."""

    id: str = Field(..., description="Item ID")
    sku: str = Field(..., description="Stock Keeping Unit")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    quantity: int = Field(..., description="Current quantity")
    price: Optional[Decimal] = Field(None, description="Item price")
    cost: Optional[Decimal] = Field(None, description="Item cost")
    category: Optional[str] = Field(None, description="Item category")
    location: Optional[str] = Field(None, description="Storage location")
    low_stock_threshold: Optional[int] = Field(None, description="Minimum stock level")
    status: str = Field(..., description="Item status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class InventoryTransactionResponse(BaseModel):
    """Model for inventory transaction responses."""

    id: str = Field(..., description="Transaction ID")
    item_id: str = Field(..., description="Item ID")
    quantity: int = Field(..., description="Transaction quantity")
    transaction_type: str = Field(..., description="Transaction type")
    notes: Optional[str] = Field(None, description="Transaction notes")
    reference: Optional[str] = Field(None, description="Reference number")
    created_at: datetime = Field(..., description="Transaction timestamp")


class InventoryListResponse(BaseModel):
    """Model for inventory list responses."""

    items: List[InventoryItemResponse] = Field(
        ..., description="List of inventory items"
    )
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Items skipped")
    has_more: bool = Field(..., description="Whether there are more items")


# Create router (no prefix here since it's added in main.py)
router = APIRouter(
    tags=["inventory"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_inventory_root():
    """
    Get inventory service information and available endpoints.

    Returns:
        Information about the inventory service and available endpoints
    """
    return {
        "service": "inventory",
        "status": "operational",
        "description": "FlipSync Inventory Management Service",
        "endpoints": {
            "items": "/api/v1/inventory/items",
            "create_item": "POST /api/v1/inventory/items",
            "get_item": "/api/v1/inventory/items/{item_id}",
            "update_item": "PUT /api/v1/inventory/items/{item_id}",
            "delete_item": "DELETE /api/v1/inventory/items/{item_id}",
            "adjust_quantity": "POST /api/v1/inventory/items/{item_id}/adjust",
            "get_transactions": "/api/v1/inventory/items/{item_id}/transactions",
            "get_by_sku": "/api/v1/inventory/items/sku/{sku}",
        },
        "authentication": "required",
        "documentation": "/docs",
    }


async def get_inventory_service():
    """Get inventory service instance with real database integration."""
    try:
        import os

        from fs_agt_clean.core.config.config_manager import ConfigManager
        from fs_agt_clean.core.db.database import Database

        # Initialize database with proper configuration
        config = ConfigManager()
        db_config = config.get_section("database") or {}
        connection_string = db_config.get("connection_string")

        # If no connection string is provided, check environment variables first
        if not connection_string:
            # Check for DATABASE_URL environment variable first
            connection_string = os.getenv("DATABASE_URL")

            if connection_string:
                # Convert from standard PostgreSQL URL to asyncpg format if needed
                if connection_string.startswith("postgresql://"):
                    connection_string = connection_string.replace(
                        "postgresql://", "postgresql+asyncpg://", 1
                    )
                logger.info(
                    f"Using DATABASE_URL environment variable for inventory service"
                )
            else:
                # Only use hardcoded default as last resort
                # Check if we're running in Docker
                in_docker = os.path.exists("/.dockerenv")
                db_host = "db" if in_docker else "localhost"
                connection_string = (
                    f"postgresql+asyncpg://postgres:postgres@{db_host}:5432/postgres"
                )
                logger.warning(
                    f"No database connection string found, using default: {connection_string}"
                )

        # Create database instance with proper configuration
        database = Database(
            config_manager=config,
            connection_string=connection_string,
            pool_size=db_config.get("pool_size", 5),
            max_overflow=db_config.get("max_overflow", 10),
            echo=db_config.get("echo", False),
        )

        # Initialize database connection
        await database.initialize()

        return InventoryServiceAdapter(database)
    except Exception as e:
        logger.error(f"Failed to initialize inventory service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inventory service unavailable",
        )


@router.get("/items", response_model=InventoryListResponse)
async def get_inventory_items(
    limit: int = Query(100, description="Maximum number of items to return", le=1000),
    offset: int = Query(0, description="Number of items to skip", ge=0),
    current_user: UnifiedUser = Depends(get_current_user),
    inventory_service: InventoryServiceAdapter = Depends(get_inventory_service),
):
    """
    Get inventory items for the current user.

    Args:
        limit: Maximum number of items to return
        offset: Number of items to skip
        current_user: Current authenticated user
        inventory_service: Inventory service

    Returns:
        List of inventory items
    """
    try:
        items = await inventory_service.get_items(
            limit=limit,
            offset=offset,
        )

        # Convert to response format
        total = len(items) if items else 0
        has_more = len(items) == limit if items else False

        return InventoryListResponse(
            items=items or [],
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory items: {str(e)}",
        )


@router.get("/items/{item_id}", response_model=Dict[str, Any])
async def get_inventory_item(
    item_id: str,
    current_user: UnifiedUser = Depends(get_current_user),
    inventory_service: InventoryServiceAdapter = Depends(get_inventory_service),
):
    """
    Get an inventory item by ID.

    Args:
        item_id: Inventory item ID
        current_user: Current authenticated user
        inventory_service: Inventory service

    Returns:
        Inventory item data
    """
    try:
        item = await inventory_service.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item not found: {item_id}",
            )

        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory item: {str(e)}",
        )


@router.get("/items/sku/{sku}", response_model=Dict[str, Any])
async def get_inventory_item_by_sku(
    sku: str,
    current_user: UnifiedUser = Depends(get_current_user),
    inventory_service: InventoryServiceAdapter = Depends(get_inventory_service),
):
    """
    Get an inventory item by SKU.

    Args:
        sku: SKU
        current_user: Current authenticated user
        inventory_service: Inventory service

    Returns:
        Inventory item data
    """
    try:
        item = await inventory_service.get_item_by_sku(sku)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item not found with SKU: {sku}",
            )

        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory item by SKU: {str(e)}",
        )


@router.post(
    "/items", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED
)
async def create_inventory_item(
    item_data: InventoryItemCreate,
    current_user: UnifiedUser = Depends(get_current_user),
    inventory_service: InventoryServiceAdapter = Depends(get_inventory_service),
):
    """
    Create a new inventory item.

    Args:
        item_data: Inventory item data
        current_user: Current authenticated user
        inventory_service: Inventory service

    Returns:
        Created inventory item data
    """
    try:
        # Create the inventory item
        item = await inventory_service.create_item(
            item_data=item_data.dict(),
        )

        return item
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inventory item: {str(e)}",
        )


@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: str,
    item_data: InventoryItemUpdate,
    current_user: UnifiedUser = Depends(get_current_user),
    inventory_service: InventoryServiceAdapter = Depends(get_inventory_service),
):
    """
    Update an inventory item.

    Args:
        item_id: Inventory item ID
        item_data: Inventory item data to update
        current_user: Current authenticated user
        inventory_service: Inventory service

    Returns:
        Updated inventory item data
    """
    try:
        # Check if the item exists
        existing_item = await inventory_service.get_item_by_id(item_id)
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item not found: {item_id}",
            )

        # Update the inventory item
        updated_item = await inventory_service.update_item(
            item_id=item_id,
            item_data=item_data.dict(exclude_unset=True),
        )

        if not updated_item:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update inventory item",
            )

        return updated_item
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update inventory item: {str(e)}",
        )


@router.delete("/items/{item_id}", response_model=ApiResponse)
async def delete_inventory_item(
    item_id: str,
    current_user: UnifiedUser = Depends(get_current_user),
    inventory_service: InventoryServiceAdapter = Depends(get_inventory_service),
):
    """
    Delete an inventory item.

    Args:
        item_id: Inventory item ID
        current_user: Current authenticated user
        inventory_service: Inventory service

    Returns:
        API response
    """
    try:
        # Check if the item exists
        existing_item = await inventory_service.get_item_by_id(item_id)
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item not found: {item_id}",
            )

        # Delete the inventory item
        result = await inventory_service.delete_item(item_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete inventory item",
            )

        return ApiResponse(
            status=status.HTTP_200_OK,
            message="Inventory item deleted successfully",
            success=True,
            data={"id": item_id},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete inventory item: {str(e)}",
        )


@router.post("/items/{item_id}/adjust", response_model=Dict[str, Any])
async def adjust_inventory(
    item_id: str,
    adjustment_data: InventoryAdjustment,
    current_user: UnifiedUser = Depends(get_current_user),
    inventory_service: InventoryServiceAdapter = Depends(get_inventory_service),
):
    """
    Adjust inventory quantity.

    Args:
        item_id: Inventory item ID
        adjustment_data: Adjustment data including quantity, type, and notes
        current_user: Current authenticated user
        inventory_service: Inventory service

    Returns:
        Updated inventory item data and transaction data
    """
    try:
        # Check if the item exists
        existing_item = await inventory_service.get_item_by_id(item_id)
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item not found: {item_id}",
            )

        # Adjust the inventory
        success = await inventory_service.adjust_quantity(
            item_id=item_id,
            adjustment_data=adjustment_data.dict(),
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to adjust inventory quantity",
            )

        # Get updated item
        updated_item = await inventory_service.get_item_by_id(item_id)

        return {
            "item": updated_item,
            "success": True,
            "message": "Inventory quantity adjusted successfully",
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to adjust inventory: {str(e)}",
        )


@router.get(
    "/items/{item_id}/transactions", response_model=List[InventoryTransactionResponse]
)
async def get_inventory_transactions(
    item_id: str,
    limit: int = Query(
        100, description="Maximum number of transactions to return", le=1000
    ),
    offset: int = Query(0, description="Number of transactions to skip", ge=0),
    current_user: UnifiedUser = Depends(get_current_user),
    inventory_service: InventoryServiceAdapter = Depends(get_inventory_service),
):
    """
    Get transactions for an inventory item.

    Args:
        item_id: Inventory item ID
        limit: Maximum number of transactions to return
        offset: Number of transactions to skip
        current_user: Current authenticated user
        inventory_service: Inventory service

    Returns:
        List of transaction data
    """
    try:
        # Check if the item exists
        existing_item = await inventory_service.get_item_by_id(item_id)
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory item not found: {item_id}",
            )

        # Get the transactions
        transactions = await inventory_service.get_transactions(item_id)

        return transactions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory transactions: {str(e)}",
        )
