"""API Routes module for FlipSync."""

from fastapi import APIRouter

# Create a main router that combines all route modules
router = APIRouter()

# Import and include all available route modules
try:
    from .agents import router as agents_router

    router.include_router(agents_router, prefix="/agents", tags=["agents"])
except ImportError:
    pass

try:
    from .analytics import router as analytics_router

    router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
except ImportError:
    pass

try:
    from .auth import router as auth_router

    router.include_router(auth_router, prefix="/auth", tags=["auth"])
except ImportError:
    pass

try:
    from .dashboard import router as dashboard_router

    router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
except ImportError:
    pass

try:
    from .inventory import router as inventory_router

    router.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
except ImportError:
    pass

try:
    from .marketplace import marketplace_router

    router.include_router(
        marketplace_router, prefix="/marketplace", tags=["marketplace"]
    )
except ImportError:
    pass

try:
    from .monitoring import router as monitoring_router

    router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
except ImportError:
    pass

try:
    from .shipping import router as shipping_router

    router.include_router(shipping_router, prefix="/shipping", tags=["shipping"])
except ImportError:
    pass

try:
    from .users import router as users_router

    router.include_router(users_router, prefix="/users", tags=["users"])
except ImportError:
    pass

__all__ = ["router"]
