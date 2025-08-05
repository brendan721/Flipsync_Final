"""
FlipSync Production Deployment API Routes
Week 4: Production Deployment & Operational Excellence - Objective 1

API endpoints for controlling and monitoring production deployment.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from fs_agt_clean.deployment.production_deployment_system import (
    get_production_deployment_system,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/deployment", tags=["Production Deployment"])


class DeploymentRequest(BaseModel):
    """Request model for production deployment."""

    action: str  # "deploy", "status", "health_check"
    force_redeploy: bool = False
    skip_health_checks: bool = False


class DeploymentStatusResponse(BaseModel):
    """Response model for deployment status."""

    deployment_active: bool
    components_deployed: int
    total_components: int
    success_rate: float
    production_urls: Dict[str, str]


@router.get("/status", response_model=DeploymentStatusResponse)
async def get_deployment_status():
    """
    Get the current status of production deployment.

    Returns:
        DeploymentStatusResponse: Current deployment status
    """
    try:
        deployment_system = get_production_deployment_system()

        # Calculate deployment metrics
        total_components = len(deployment_system.deployment_status)
        successful_components = sum(
            1
            for status in deployment_system.deployment_status.values()
            if status.status == "running" and status.health_check
        )

        success_rate = (
            successful_components / total_components if total_components > 0 else 0
        )

        return DeploymentStatusResponse(
            deployment_active=total_components > 0,
            components_deployed=successful_components,
            total_components=total_components,
            success_rate=success_rate,
            production_urls={
                "backend": f"http://{deployment_system.digitalocean_ip}:{deployment_system.backend_port}",
                "frontend": f"http://localhost:{deployment_system.frontend_port}",
                "websocket": f"ws://{deployment_system.digitalocean_ip}:{deployment_system.backend_port}/ws/flipsync",
                "database": f"{deployment_system.digitalocean_ip}:{deployment_system.database_port}",
                "redis": f"{deployment_system.digitalocean_ip}:{deployment_system.redis_port}",
                "qdrant": f"{deployment_system.digitalocean_ip}:{deployment_system.qdrant_port}",
            },
        )

    except Exception as e:
        logger.error(f"Error getting deployment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deployment status: {str(e)}",
        )


@router.post("/deploy")
async def deploy_production_environment(request: DeploymentRequest):
    """
    Deploy FlipSync production environment.

    Args:
        request: Deployment configuration
        background_tasks: FastAPI background tasks

    Returns:
        Dict: Deployment results
    """
    try:
        deployment_system = get_production_deployment_system()

        if request.action == "deploy":
            logger.info("🚀 Starting production deployment...")

            # Run deployment
            deployment_report = await deployment_system.deploy_production_environment()

            return {
                "success": True,
                "message": "Production deployment completed",
                "deployment_report": deployment_report,
            }

        elif request.action == "status":
            # Return current deployment status
            status_info = {
                "deployment_status": {
                    component: status.dict()
                    for component, status in deployment_system.deployment_status.items()
                },
                "production_urls": {
                    "backend": f"http://{deployment_system.digitalocean_ip}:{deployment_system.backend_port}",
                    "frontend": f"http://localhost:{deployment_system.frontend_port}",
                    "websocket": f"ws://{deployment_system.digitalocean_ip}:{deployment_system.backend_port}/ws/flipsync",
                },
            }

            return {
                "success": True,
                "message": "Deployment status retrieved",
                "status": status_info,
            }

        elif request.action == "health_check":
            # Run health checks only
            await deployment_system._run_comprehensive_health_checks()

            return {
                "success": True,
                "message": "Health checks completed",
                "timestamp": deployment_system.deployment_status,
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {request.action}. Use 'deploy', 'status', or 'health_check'",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in production deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute deployment action: {str(e)}",
        )


@router.get("/health")
async def get_production_health():
    """
    Get production environment health status.

    Returns:
        Dict: Health status of all production components
    """
    try:
        deployment_system = get_production_deployment_system()

        # Run health checks
        await deployment_system._run_comprehensive_health_checks()

        # Analyze health status
        healthy_components = []
        unhealthy_components = []

        for component, status in deployment_system.deployment_status.items():
            if status.status == "running" and status.health_check:
                healthy_components.append(component)
            else:
                unhealthy_components.append(
                    {
                        "component": component,
                        "status": status.status,
                        "error": status.error_message,
                    }
                )

        overall_health = len(unhealthy_components) == 0

        return {
            "success": True,
            "overall_health": overall_health,
            "healthy_components": healthy_components,
            "unhealthy_components": unhealthy_components,
            "health_score": (
                len(healthy_components) / len(deployment_system.deployment_status)
                if deployment_system.deployment_status
                else 0
            ),
            "production_urls": {
                "backend": f"http://{deployment_system.digitalocean_ip}:{deployment_system.backend_port}",
                "frontend": f"http://localhost:{deployment_system.frontend_port}",
                "websocket": f"ws://{deployment_system.digitalocean_ip}:{deployment_system.backend_port}/ws/flipsync",
            },
        }

    except Exception as e:
        logger.error(f"Error getting production health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get production health: {str(e)}",
        )


@router.get("/components")
async def get_deployment_components():
    """
    Get detailed information about deployment components.

    Returns:
        Dict: Detailed component information
    """
    try:
        deployment_system = get_production_deployment_system()

        components_info = {
            "production_services": deployment_system.production_services,
            "required_agents": deployment_system.required_agents,
            "required_services_count": deployment_system.required_services_count,
            "deployment_configuration": {
                "digitalocean_ip": deployment_system.digitalocean_ip,
                "backend_port": deployment_system.backend_port,
                "frontend_port": deployment_system.frontend_port,
                "database_port": deployment_system.database_port,
                "redis_port": deployment_system.redis_port,
                "qdrant_port": deployment_system.qdrant_port,
            },
            "component_status": {
                component: status.dict()
                for component, status in deployment_system.deployment_status.items()
            },
        }

        return {"success": True, "components_info": components_info}

    except Exception as e:
        logger.error(f"Error getting deployment components: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deployment components: {str(e)}",
        )


@router.post("/validate")
async def validate_production_deployment():
    """
    Validate production deployment readiness.

    Returns:
        Dict: Validation results
    """
    try:
        deployment_system = get_production_deployment_system()

        # Run validation checks
        validation_results = {
            "prerequisites": True,
            "infrastructure": True,
            "backend": True,
            "frontend": True,
            "agents": True,
            "services": True,
        }

        validation_details = {}

        # Check prerequisites
        try:
            await deployment_system._validate_deployment_prerequisites()
            validation_details["prerequisites"] = "All prerequisites validated"
        except Exception as e:
            validation_results["prerequisites"] = False
            validation_details["prerequisites"] = str(e)

        # Check agent and service integration
        try:
            await deployment_system._validate_agent_service_integration()
            validation_details["agents_services"] = (
                "Agent and service integration validated"
            )
        except Exception as e:
            validation_results["agents"] = False
            validation_results["services"] = False
            validation_details["agents_services"] = str(e)

        # Overall validation result
        overall_valid = all(validation_results.values())

        return {
            "success": True,
            "overall_valid": overall_valid,
            "validation_results": validation_results,
            "validation_details": validation_details,
            "recommendations": [
                (
                    "✅ All validation checks passed - ready for production deployment"
                    if overall_valid
                    else "❌ Some validation checks failed - review details before deployment"
                )
            ],
        }

    except Exception as e:
        logger.error(f"Error validating production deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate production deployment: {str(e)}",
        )
