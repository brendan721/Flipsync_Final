"""
Marketplace API routes package.

This package contains API routes for various marketplace integrations
including eBay, Amazon, and other e-commerce platforms.
"""

from fastapi import APIRouter

# Import marketplace route modules
try:
    from .ebay import router as ebay_router

    EBAY_AVAILABLE = True
except ImportError as e:
    print(f"eBay marketplace routes not available: {e}")
    EBAY_AVAILABLE = False

try:
    from .amazon import router as amazon_router

    AMAZON_AVAILABLE = True
except ImportError as e:
    print(f"Amazon marketplace routes not available: {e}")
    AMAZON_AVAILABLE = False

# Create main marketplace router
marketplace_router = APIRouter(tags=["marketplace"])

# Add available marketplace routers
if EBAY_AVAILABLE:
    marketplace_router.include_router(ebay_router, prefix="/ebay")

if AMAZON_AVAILABLE:
    marketplace_router.include_router(amazon_router, prefix="/amazon")


# Add general marketplace status endpoint
# OPTIONS handler for CORS preflight
@marketplace_router.options("/status")
async def options_marketplace_status():
    """Handle CORS preflight for marketplace status endpoint."""
    return {"message": "OK"}


@marketplace_router.get("/status")
async def get_marketplace_status():
    """Get general marketplace connection status."""
    # IMPORTANT: This endpoint should NOT return hardcoded connection status
    # Connection status should be based on actual user authentication, not module availability
    return {
        "status": "success",
        "message": "Marketplace status retrieved",
        "data": {
            "ebay_connected": False,  # Fixed: Should be False until user actually connects
            "amazon_connected": False,  # Fixed: Should be False until user actually connects
            "ebay_available": EBAY_AVAILABLE,  # Module availability (for debugging)
            "amazon_available": AMAZON_AVAILABLE,  # Module availability (for debugging)
            "available_marketplaces": [],
            "total_connections": 0,
        },
    }


__all__ = ["marketplace_router", "EBAY_AVAILABLE", "AMAZON_AVAILABLE"]
