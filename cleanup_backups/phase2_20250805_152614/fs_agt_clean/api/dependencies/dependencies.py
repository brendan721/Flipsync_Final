"""
API dependencies module for authentication and authorization.

IMPORTANT: This module handles FlipSync's internal user authentication
(users logging into the FlipSync application). This is SEPARATE from
eBay OAuth integration which is handled in marketplace routes.
"""

from typing import Optional
import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)

from fs_agt_clean.core.models.account import UnifiedUserAccount
from fs_agt_clean.database.models.unified_user import UnifiedUserResponse

# Import unified authentication factory for FlipSync users
from fs_agt_clean.core.auth.auth_factory import AuthenticationFactory

# Global unified auth system instance for dependency injection
_unified_auth_instance = None


async def get_auth_service():
    """
    Get the unified authentication system for FlipSync users.

    Note: This is for FlipSync user authentication only, NOT eBay OAuth
    """
    global _unified_auth_instance

    if _unified_auth_instance is None:
        _unified_auth_instance = await AuthenticationFactory.get_auth_system()

    return _unified_auth_instance


# Alias for backward compatibility
get_unified_auth_service = get_auth_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UnifiedUserAccount:
    """
    Get current authenticated FlipSync user from JWT token.

    Note: This is for FlipSync user authentication only, NOT eBay OAuth

    Args:
        token: JWT token from Authorization header

    Returns:
        UnifiedUserAccount: Current authenticated FlipSync user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    from fastapi import HTTPException, status

    try:
        # Get unified auth system
        auth_system = await get_auth_service()

        # Verify token and get user
        user = await auth_system.verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_account(
    token: str = Depends(oauth2_scheme),
) -> UnifiedUserAccount:
    """Get the current authenticated user from the JWT token, as a UnifiedUserAccount object.

    Args:
        token: JWT token from the Authorization header

    Returns:
        UnifiedUserAccount object for the authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get unified auth system
        auth_system = await get_auth_service()

        # Verify token and get user
        user = await auth_system.verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert AuthUser to UnifiedUserAccount
        return UnifiedUserAccount(
            id=user.user_id,
            email=user.email,
            username=user.username,
            role="admin" if "admin" in user.roles else "user",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ENHANCED: Unified Authentication Dependencies for eBay and other endpoints
async def get_current_user_response(
    token: str = Depends(oauth2_scheme),
) -> UnifiedUserResponse:
    """Get the current authenticated user as UnifiedUserResponse for eBay endpoints."""
    try:
        # Get unified auth system
        auth_system = await get_auth_service()

        # Verify token and get user
        user = await auth_system.verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert AuthUser to UnifiedUserResponse for compatibility
        from fs_agt_clean.database.models.unified_user import UnifiedUserStatus
        from datetime import datetime

        return UnifiedUserResponse(
            id=user.user_id,
            email=user.email,
            username=user.username,
            status=UnifiedUserStatus.ACTIVE,
            is_active=user.is_active,
            is_verified=True,
            is_admin="admin" in user.roles,
            mfa_enabled=False,
            created_at=user.created_at,
            updated_at=datetime.now(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    request: Request,
) -> Optional[UnifiedUserResponse]:
    """Get the current authenticated user optionally using unified auth system."""
    try:
        # Extract token from request headers
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None

        token = authorization.split(" ")[1]

        # Get unified auth system
        auth_system = await get_auth_service()

        # Verify token and get user
        user = await auth_system.verify_token(token)
        if not user:
            return None

        # Convert AuthUser to UnifiedUserResponse
        from fs_agt_clean.database.models.unified_user import UnifiedUserStatus
        from datetime import datetime

        return UnifiedUserResponse(
            id=user.user_id,
            email=user.email,
            username=user.username,
            status=UnifiedUserStatus.ACTIVE,
            is_active=user.is_active,
            is_verified=True,
            is_admin="admin" in user.roles,
            mfa_enabled=False,
            created_at=user.created_at,
            updated_at=datetime.now(),
        )
    except Exception:
        # Optional authentication should not raise exceptions
        return None


# ENHANCED: Permission-based Authentication Dependencies
async def require_admin_permission(
    current_user: UnifiedUserResponse = Depends(get_current_user_response),
) -> UnifiedUserResponse:
    """Require admin permission for endpoint access."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin permission required"
        )
    return current_user


async def require_marketplace_permission(
    current_user: UnifiedUserResponse = Depends(get_current_user_response),
) -> UnifiedUserResponse:
    """Require marketplace access permission for eBay and other marketplace endpoints."""
    # For marketplace access, allow active users and admins
    if not (
        current_user.is_active and (current_user.is_admin or current_user.is_verified)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Marketplace access permission required",
        )
    return current_user


async def get_required_user(token: str = Depends(oauth2_scheme)) -> UnifiedUserResponse:
    """Get the current user for APIs that specifically require a UnifiedUserResponse object.

    This dependency can be used when the API specifically needs a UnifiedUserResponse object
    rather than a UnifiedUserAccount object.

    Args:
        token: JWT token from the Authorization header

    Returns:
        UnifiedUserResponse object

    Raises:
        HTTPException: If authentication fails
    """
    # Simply delegate to the get_current_user_response function
    return await get_current_user_response(token)


# Global instances for dependency injection
_agent_manager_instance: Optional["AutonomousAgentManager"] = None
_pipeline_controller_instance: Optional["PipelineController"] = None
_state_manager_instance: Optional["StateManager"] = None


async def get_agent_manager():
    """Get the global autonomous agent manager instance (4+1 architecture)."""
    global _agent_manager_instance

    if _agent_manager_instance is None:
        from fs_agt_clean.core.agents.autonomous_agent_manager import (
            AutonomousAgentManager,
        )

        _agent_manager_instance = AutonomousAgentManager()
        await _agent_manager_instance.initialize()

    return _agent_manager_instance


async def get_pipeline_controller():
    """Get the global pipeline controller instance."""
    global _pipeline_controller_instance

    if _pipeline_controller_instance is None:
        from fs_agt_clean.core.pipeline.controller import PipelineController

        agent_manager = await get_agent_manager()
        _pipeline_controller_instance = PipelineController(agent_manager=agent_manager)
        await _pipeline_controller_instance.setup_agent_communication_protocol()

    return _pipeline_controller_instance


async def get_state_manager():
    """Get the global state manager instance."""
    global _state_manager_instance

    if _state_manager_instance is None:
        from fs_agt_clean.core.state_management.state_manager import StateManager

        _state_manager_instance = StateManager()

    return _state_manager_instance


class DisabledOrchestrationService:
    """Disabled orchestration service for 4+1 architecture compliance."""

    def __init__(self):
        logger.warning(
            "OrchestrationService is disabled for 4+1 architecture compliance"
        )
        self.agent_registry = {}
        self.active_workflows = {}
        self.active_handoffs = {}

    def __getattr__(self, name):
        logger.warning(
            f"OrchestrationService.{name} called but service is disabled for 4+1 architecture"
        )
        return lambda *args, **kwargs: {
            "error": "OrchestrationService disabled for 4+1 architecture"
        }


async def get_orchestration_service():
    """Get the global orchestration service instance - DISABLED for 4+1 architecture compliance."""
    return DisabledOrchestrationService()


async def get_dashboard_service():
    """Get the global dashboard service instance."""
    from fs_agt_clean.services.dashboard.real_time_dashboard import (
        get_dashboard_service,
    )

    # Get required dependencies
    agent_manager = await get_agent_manager()
    pipeline_controller = await get_pipeline_controller()
    state_manager = await get_state_manager()

    # Get dashboard service with dependencies (orchestration_service removed for 4+1 architecture)
    return await get_dashboard_service(
        agent_manager=agent_manager,
        pipeline_controller=pipeline_controller,
        state_manager=state_manager,
    )
