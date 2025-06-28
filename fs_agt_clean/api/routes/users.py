"""UnifiedUser management API routes."""

from fastapi import APIRouter

from fs_agt_clean.api.routes.users.access_control import router as access_control_router
from fs_agt_clean.api.routes.users.audit import router as audit_router
from fs_agt_clean.api.routes.users.payment_methods import (
    router as payment_methods_router,
)
from fs_agt_clean.api.routes.users.permissions import router as permissions_router
from fs_agt_clean.api.routes.users.roles import router as roles_router
from fs_agt_clean.api.routes.users.user import router as user_router

# Create main router
router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# Include all user-related routers
router.include_router(user_router, prefix="/profile")
router.include_router(roles_router, prefix="/roles")
router.include_router(permissions_router, prefix="/permissions")
router.include_router(access_control_router, prefix="/access-control")
router.include_router(audit_router, prefix="/audit")
router.include_router(payment_methods_router, prefix="/payment-methods")
