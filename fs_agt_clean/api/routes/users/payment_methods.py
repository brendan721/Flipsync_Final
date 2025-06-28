"""UnifiedUser payment methods endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.security.auth import get_current_user

router = APIRouter(tags=["user-payment-methods"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_payment_methods(
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Get user's payment methods."""
    # Mock implementation
    return [
        {
            "id": "pm_1",
            "type": "credit_card",
            "last_four": "1234",
            "brand": "visa",
            "is_default": True,
            "created_at": "2023-01-01T00:00:00Z",
        },
        {
            "id": "pm_2",
            "type": "bank_account",
            "last_four": "5678",
            "bank_name": "Chase",
            "is_default": False,
            "created_at": "2023-01-02T00:00:00Z",
        },
    ]


@router.post("/", response_model=Dict[str, Any])
async def add_payment_method(
    payment_data: Dict[str, Any],
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Add a new payment method."""
    # Mock implementation
    return {
        "id": "pm_new",
        "status": "success",
        "message": "Payment method added successfully",
    }


@router.delete("/{payment_method_id}", response_model=Dict[str, Any])
async def remove_payment_method(
    payment_method_id: str,
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Remove a payment method."""
    # Mock implementation
    return {
        "status": "success",
        "message": f"Payment method {payment_method_id} removed successfully",
    }
