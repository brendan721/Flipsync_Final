"""
FlipSync End-to-End Connectivity Validation API Routes
Week 3: Frontend Integration Updates - Objective 4

API endpoints for running and monitoring end-to-end connectivity validation.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from fs_agt_clean.core.validation.end_to_end_connectivity import (
    get_connectivity_validator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/validation", tags=["Connectivity Validation"])


class ValidationRequest(BaseModel):
    """Request model for validation."""

    run_full_validation: bool = True
    include_websocket_tests: bool = True
    include_resilience_tests: bool = True


class ValidationStatusResponse(BaseModel):
    """Response model for validation status."""

    validation_running: bool
    last_validation_time: str = None
    last_validation_success: bool = None
    total_tests_run: int = 0


@router.get("/status", response_model=ValidationStatusResponse)
async def get_validation_status():
    """
    Get the current status of connectivity validation.

    Returns:
        ValidationStatusResponse: Current validation status
    """
    try:
        validator = get_connectivity_validator()

        # Get basic status information
        return ValidationStatusResponse(
            validation_running=False,  # We'll track this if needed
            total_tests_run=len(validator.test_results),
        )

    except Exception as e:
        logger.error(f"Error getting validation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation status: {str(e)}",
        )


@router.post("/run")
async def run_connectivity_validation(request: ValidationRequest):
    """
    Run end-to-end connectivity validation.

    Args:
        request: Validation configuration
        background_tasks: FastAPI background tasks

    Returns:
        Dict: Validation results
    """
    try:
        validator = get_connectivity_validator()

        # Initialize validator if needed
        if validator.session is None:
            success = await validator.initialize()
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize connectivity validator",
                )

        # Run full validation
        logger.info("🔍 Starting end-to-end connectivity validation...")

        validation_report = await validator.run_full_validation()

        # Cleanup
        await validator.cleanup()

        return {
            "success": True,
            "message": "End-to-end connectivity validation completed",
            "validation_report": validation_report,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running connectivity validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run connectivity validation: {str(e)}",
        )


@router.get("/report")
async def get_latest_validation_report():
    """
    Get the latest validation report.

    Returns:
        Dict: Latest validation report
    """
    try:
        validator = get_connectivity_validator()

        if not validator.test_results:
            return {
                "success": False,
                "message": "No validation results available. Run validation first.",
                "test_results": [],
            }

        # Generate report from existing results
        successful_tests = [r for r in validator.test_results if r.success]
        failed_tests = [r for r in validator.test_results if not r.success]

        success_rate = len(successful_tests) / len(validator.test_results)
        avg_response_time = sum(
            r.response_time_ms for r in validator.test_results
        ) / len(validator.test_results)

        return {
            "success": True,
            "validation_summary": {
                "total_tests": len(validator.test_results),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "success_rate": success_rate,
                "average_response_time_ms": avg_response_time,
            },
            "connectivity_status": {
                "backend_url": validator.backend_base_url,
                "frontend_url": validator.frontend_url,
                "websocket_url": validator.websocket_url,
                "unified_websocket_endpoint": "/ws/flipsync",
            },
            "test_results": [result.dict() for result in validator.test_results],
            "recommendations": validator._generate_recommendations(failed_tests),
        }

    except Exception as e:
        logger.error(f"Error getting validation report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation report: {str(e)}",
        )


@router.get("/health-check")
async def quick_health_check():
    """
    Run a quick health check of critical endpoints.

    Returns:
        Dict: Quick health check results
    """
    try:
        validator = get_connectivity_validator()

        # Initialize if needed
        if validator.session is None:
            await validator.initialize()

        # Run just the backend health test
        await validator._test_backend_health()

        # Get the latest result
        if validator.test_results:
            latest_result = validator.test_results[-1]

            return {
                "success": latest_result.success,
                "backend_url": validator.backend_base_url,
                "response_time_ms": latest_result.response_time_ms,
                "details": latest_result.details,
                "error_message": latest_result.error_message,
                "timestamp": latest_result.timestamp,
            }
        else:
            return {"success": False, "message": "No health check results available"}

    except Exception as e:
        logger.error(f"Error running health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run health check: {str(e)}",
        )


@router.get("/websocket-test")
async def test_websocket_connectivity():
    """
    Test WebSocket connectivity specifically.

    Returns:
        Dict: WebSocket connectivity test results
    """
    try:
        validator = get_connectivity_validator()

        # Run WebSocket connectivity test
        await validator._test_websocket_connectivity()

        # Get the latest WebSocket test result
        websocket_results = [
            r for r in validator.test_results if "WebSocket" in r.test_name
        ]

        if websocket_results:
            latest_result = websocket_results[-1]

            return {
                "success": latest_result.success,
                "websocket_url": validator.websocket_url,
                "unified_endpoint": "/ws/flipsync",
                "response_time_ms": latest_result.response_time_ms,
                "details": latest_result.details,
                "error_message": latest_result.error_message,
                "timestamp": latest_result.timestamp,
            }
        else:
            return {"success": False, "message": "No WebSocket test results available"}

    except Exception as e:
        logger.error(f"Error testing WebSocket connectivity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test WebSocket connectivity: {str(e)}",
        )


@router.get("/configuration")
async def get_connectivity_configuration():
    """
    Get current connectivity configuration.

    Returns:
        Dict: Connectivity configuration
    """
    try:
        validator = get_connectivity_validator()

        return {
            "success": True,
            "configuration": {
                "backend_base_url": validator.backend_base_url,
                "frontend_url": validator.frontend_url,
                "websocket_url": validator.websocket_url,
                "unified_websocket_endpoint": "/ws/flipsync",
                "production_environment": {
                    "digitalocean_ip": "174.138.77.110",
                    "backend_port": 8001,
                    "frontend_port": 3000,
                    "websocket_protocol": "ws",
                },
                "test_endpoints": [
                    "/health",
                    "/api/v1/showcase/status",
                    "/api/v1/showcase/metrics",
                    "/api/v1/showcase/scenarios",
                    "/docs",
                    "/openapi.json",
                ],
            },
        }

    except Exception as e:
        logger.error(f"Error getting connectivity configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connectivity configuration: {str(e)}",
        )
