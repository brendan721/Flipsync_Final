"""API dependencies module for authentication and authorization."""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from fs_agt_clean.core.models.account import UnifiedUserAccount
from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.security.auth import get_current_user, verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user_account(token: str = Depends(oauth2_scheme)) -> UnifiedUserAccount:
    """Get the current authenticated user from the JWT token, as a UnifiedUserAccount object.

    Args:
        token: JWT token from the Authorization header

    Returns:
        UnifiedUserAccount object for the authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify the token and get the user data
        user_data = await verify_token(token)

        if user_data is None:
            raise credentials_exception

        # Create a UnifiedUserAccount object from the token data
        return UnifiedUserAccount(
            id=user_data["sub"],
            email=user_data.get("email", ""),
            username=user_data.get("username", ""),
            role=user_data.get("role", "user"),
        )
    except Exception:
        raise credentials_exception


async def get_required_user(
    request: Request, token: str = Depends(oauth2_scheme)
) -> UnifiedUser:
    """Get the current user for APIs that specifically require a UnifiedUser object.

    This dependency can be used when the API specifically needs a UnifiedUser object
    rather than a UnifiedUserAccount object.

    Args:
        request: The request object
        token: JWT token from the Authorization header

    Returns:
        UnifiedUser object

    Raises:
        HTTPException: If authentication fails
    """
    # Simply delegate to the core get_current_user function
    return await get_current_user(token)


# Global instances for dependency injection
_agent_manager_instance: Optional["RealUnifiedAgentManager"] = None
_pipeline_controller_instance: Optional["PipelineController"] = None
_state_manager_instance: Optional["StateManager"] = None
_orchestration_service_instance: Optional["UnifiedAgentOrchestrationService"] = None


async def get_agent_manager():
    """Get the global agent manager instance."""
    global _agent_manager_instance

    if _agent_manager_instance is None:
        from fs_agt_clean.core.agents.real_agent_manager import RealUnifiedAgentManager

        _agent_manager_instance = RealUnifiedAgentManager()
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


async def get_orchestration_service():
    """Get the global orchestration service instance."""
    global _orchestration_service_instance

    if _orchestration_service_instance is None:
        from fs_agt_clean.services.agent_orchestration import UnifiedAgentOrchestrationService

        _orchestration_service_instance = UnifiedAgentOrchestrationService()

    return _orchestration_service_instance


async def get_dashboard_service():
    """Get the global dashboard service instance."""
    from fs_agt_clean.services.dashboard.real_time_dashboard import (
        get_dashboard_service,
    )

    # Get required dependencies
    agent_manager = await get_agent_manager()
    pipeline_controller = await get_pipeline_controller()
    state_manager = await get_state_manager()
    orchestration_service = await get_orchestration_service()

    # Get dashboard service with dependencies
    return await get_dashboard_service(
        agent_manager=agent_manager,
        pipeline_controller=pipeline_controller,
        state_manager=state_manager,
        orchestration_service=orchestration_service,
    )
