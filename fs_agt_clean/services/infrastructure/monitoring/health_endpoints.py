"""Health check endpoints for FlipSync API.

This module provides health check endpoints for monitoring the API's health
and readiness status.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import Depends

from fs_agt_clean.core.config.manager import manager as config_manager

logger = logging.getLogger(__name__)


async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint.

    Returns:
        Dictionary with health status information.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": config_manager.get("app.version", "0.1.0"),
        "environment": config_manager.get_environment(),
    }


async def check_database_connection() -> Dict[str, Any]:
    """Check database connection.

    Returns:
        Dictionary with database connection status.
    """
    from fs_agt_clean.core.db.session import get_db

    try:
        # Get database session
        db = next(get_db())

        # Execute simple query
        result = db.execute("SELECT 1").fetchone()

        if result and result[0] == 1:
            return {"status": "ok"}
        else:
            return {"status": "error", "message": "Database query failed"}
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return {"status": "error", "message": str(e)}


async def check_redis_connection() -> Dict[str, Any]:
    """Check Redis connection.

    Returns:
        Dictionary with Redis connection status.
    """
    from fs_agt_clean.core.cache.redis import get_redis

    try:
        # Get Redis client
        redis = get_redis()

        # Ping Redis
        result = await redis.ping()

        if result:
            return {"status": "ok"}
        else:
            return {"status": "error", "message": "Redis ping failed"}
    except Exception as e:
        logger.error(f"Redis connection check failed: {str(e)}")
        return {"status": "error", "message": str(e)}


async def check_qdrant_connection() -> Dict[str, Any]:
    """Check Qdrant connection.

    Returns:
        Dictionary with Qdrant connection status.
    """
    from fs_agt_clean.core.vector.qdrant import get_qdrant_client

    try:
        # Get Qdrant client
        client = get_qdrant_client()

        # Check connection
        result = client.health()

        if result and result.get("status") == "ok":
            return {"status": "ok"}
        else:
            return {"status": "error", "message": "Qdrant health check failed"}
    except Exception as e:
        logger.error(f"Qdrant connection check failed: {str(e)}")
        return {"status": "error", "message": str(e)}


async def liveness_probe() -> Dict[str, Any]:
    """Liveness probe for Kubernetes.

    This endpoint checks if the application is alive and running.
    It should be a lightweight check that doesn't depend on external services.

    Returns:
        Dictionary with liveness status information.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": config_manager.get("app.version", "0.1.0"),
        "environment": config_manager.get_environment(),
    }


async def readiness_probe() -> Dict[str, Any]:
    """Readiness probe for Kubernetes.

    This endpoint checks if the application is ready to receive traffic.
    It should check all external dependencies that the application needs to function.

    Returns:
        Dictionary with readiness status information.
    """
    # Check all services
    services_status = {}

    # Check database connection
    services_status["database"] = await check_database_connection()

    # Check Redis connection
    services_status["redis"] = await check_redis_connection()

    # Check Qdrant connection
    services_status["qdrant"] = await check_qdrant_connection()

    # Determine overall status
    status = "ok"
    for service, service_status in services_status.items():
        if service_status.get("status") != "ok":
            status = "error"
            break

    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": config_manager.get("app.version", "0.1.0"),
        "environment": config_manager.get_environment(),
        "services": services_status,
    }
