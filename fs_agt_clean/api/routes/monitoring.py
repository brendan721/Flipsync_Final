import logging
import os
import platform
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

# get_request import removed - not used
from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.monitoring.types import HealthStatus
from fs_agt_clean.core.security.auth import get_current_user, require_permissions
from fs_agt_clean.services.monitoring.enhanced_dashboard import enhanced_dashboard

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])


@router.get("/")
async def get_monitoring_overview() -> Dict[str, Any]:
    """Get overview of monitoring system and available endpoints.

    Returns:
        Dict[str, Any]: Overview of monitoring capabilities.
    """
    try:
        from datetime import datetime, timezone

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "operational",
            "description": "FlipSync Monitoring System",
            "endpoints": {
                "metrics": "/api/v1/monitoring/metrics",
                "system_info": "/api/v1/monitoring/system-info",
                "status": "/api/v1/monitoring/status",
                "health": "/api/v1/monitoring/health/detailed",
                "ebay_tokens": "/api/v1/monitoring/token-status/ebay",
                "enhanced_dashboard": "/api/v1/monitoring/dashboard/enhanced",
                "performance_report": "/api/v1/monitoring/dashboard/performance",
                "ai_validation": "/api/v1/monitoring/dashboard/ai-validation",
            },
            "capabilities": [
                "System metrics collection",
                "Application health monitoring",
                "Database status tracking",
                "Token expiration monitoring",
                "Real-time status updates",
            ],
        }
    except Exception as e:
        logger.error(f"Error getting monitoring overview: {e}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "status": "error",
        }


@router.get("/metrics", tags=["monitoring"])
async def get_system_metrics(
    request: Request,
    user: UnifiedUser = Depends(require_permissions(["admin", "monitoring"])),
):
    """
    Get system metrics for monitoring.

    Returns:
        Dict with system metrics
    """
    # Initialize response structure
    response = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "uptime": 0,
        },
        "application": {
            "requests": {
                "total": 0,
                "success": 0,
                "error": 0,
                "avg_response_time": 0.0,
            },
            "active_users": 0,
            "active_agents": 0,
        },
        "database": {
            "connections": 0,
            "queries": {
                "total": 0,
                "avg_time": 0.0,
            },
        },
    }

    # Get monitoring manager if available
    monitoring_manager = None
    if hasattr(request.app.state, "monitoring_manager"):
        monitoring_manager = request.app.state.monitoring_manager

        # Get system metrics
        if hasattr(monitoring_manager, "system_monitor"):
            system_monitor = monitoring_manager.system_monitor
            system_metrics = (
                system_monitor.get_metrics()
                if hasattr(system_monitor, "get_metrics")
                else {}
            )

            if system_metrics:
                response["system"] = {
                    **response["system"],
                    **system_metrics,
                }

        # Get application metrics
        if hasattr(monitoring_manager, "app_monitor"):
            app_monitor = monitoring_manager.app_monitor
            app_metrics = (
                app_monitor.get_metrics() if hasattr(app_monitor, "get_metrics") else {}
            )

            if app_metrics:
                response["application"] = {
                    **response["application"],
                    **app_metrics,
                }

        # Get database metrics
        if hasattr(monitoring_manager, "db_monitor"):
            db_monitor = monitoring_manager.db_monitor
            db_metrics = (
                db_monitor.get_metrics() if hasattr(db_monitor, "get_metrics") else {}
            )

            if db_metrics:
                response["database"] = {
                    **response["database"],
                    **db_metrics,
                }

    # If no monitoring manager, use basic system info
    if not monitoring_manager:
        # Get basic system info
        import psutil

        try:
            response["system"] = {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "uptime": int(time.time() - psutil.boot_time()),
                "platform": platform.system(),
                "python_version": sys.version.split()[0],
            }
        except ImportError:
            # If psutil is not available, use minimal info
            response["system"] = {
                "platform": platform.system(),
                "python_version": sys.version.split()[0],
            }

    return response


@router.get("/system-info", tags=["monitoring"])
async def get_system_info(
    request: Request,
    user: UnifiedUser = Depends(require_permissions(["admin", "monitoring"])),
):
    """
    Get system information for monitoring.

    Returns:
        Dict with system information
    """
    # Initialize response structure
    response = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version.split()[0],
            "hostname": platform.node(),
            "cpu_count": os.cpu_count(),
            "architecture": platform.machine(),
        },
        "application": {
            "version": getattr(request.app, "version", "unknown"),
            "start_time": getattr(
                request.app.state, "start_time", datetime.now(timezone.utc).isoformat()
            ),
            "environment": os.environ.get("ENVIRONMENT", "development"),
        },
    }

    # Get additional system info if psutil is available
    try:
        import psutil

        # Get memory info
        memory = psutil.virtual_memory()
        response["system"]["memory_total"] = memory.total
        response["system"]["memory_available"] = memory.available
        response["system"]["memory_percent"] = memory.percent

        # Get disk info
        disk = psutil.disk_usage("/")
        response["system"]["disk_total"] = disk.total
        response["system"]["disk_free"] = disk.free
        response["system"]["disk_percent"] = disk.percent

        # Get network info
        net_io = psutil.net_io_counters()
        response["system"]["network_bytes_sent"] = net_io.bytes_sent
        response["system"]["network_bytes_recv"] = net_io.bytes_recv

        # Get process info
        process = psutil.Process()
        response["application"]["process_cpu_percent"] = process.cpu_percent()
        response["application"]["process_memory_percent"] = process.memory_percent()
        response["application"]["process_threads"] = process.num_threads()
        response["application"]["process_open_files"] = len(process.open_files())
        response["application"]["process_connections"] = len(process.connections())
    except (ImportError, Exception) as e:
        # If psutil is not available or fails, add a message
        response["system"]["extended_info"] = f"Not available: {str(e)}"

    return response


@router.get("/status", tags=["monitoring"])
async def get_system_status(
    request: Request,
    user: UnifiedUser = Depends(require_permissions(["admin", "monitoring"])),
):
    """
    Get system status information.

    Returns:
        Dict with system status information
    """
    # Initialize response structure
    response = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "operational",
        "components": {
            "api": {
                "status": "operational",
                "message": "API is functioning normally",
            },
            "database": {
                "status": "operational",
                "message": "Database is functioning normally",
            },
            "redis": {
                "status": "operational",
                "message": "Redis is functioning normally",
            },
            "auth": {
                "status": "operational",
                "message": "Authentication service is functioning normally",
            },
        },
    }

    # Check if database is available
    if hasattr(request.app.state, "db"):
        try:
            # Perform a simple database check
            db = request.app.state.db
            if hasattr(db, "is_connected") and callable(db.is_connected):
                is_connected = await db.is_connected()
                if not is_connected:
                    response["components"]["database"] = {
                        "status": "degraded",
                        "message": "Database connection issues detected",
                    }
                    response["status"] = "degraded"
        except Exception as e:
            response["components"]["database"] = {
                "status": "down",
                "message": f"Database error: {str(e)}",
            }
            response["status"] = "degraded"

    # Check if Redis is available
    if hasattr(request.app.state, "redis_manager"):
        try:
            # Perform a simple Redis check
            redis_manager = request.app.state.redis_manager
            if hasattr(redis_manager, "ping") and callable(redis_manager.ping):
                ping_result = await redis_manager.ping()
                if not ping_result:
                    response["components"]["redis"] = {
                        "status": "degraded",
                        "message": "Redis connection issues detected",
                    }
                    response["status"] = "degraded"
        except Exception as e:
            response["components"]["redis"] = {
                "status": "down",
                "message": f"Redis error: {str(e)}",
            }
            response["status"] = "degraded"

    # Check if auth service is available
    if hasattr(request.app.state, "auth"):
        try:
            # Perform a simple auth service check
            auth_service = request.app.state.auth
            if not auth_service:
                response["components"]["auth"] = {
                    "status": "degraded",
                    "message": "Auth service issues detected",
                }
                response["status"] = "degraded"
        except Exception as e:
            response["components"]["auth"] = {
                "status": "down",
                "message": f"Auth service error: {str(e)}",
            }
            response["status"] = "degraded"

    return response


@router.get("/token-status/ebay", tags=["monitoring"])
async def get_ebay_token_status(
    request: Request,
    token_id: Optional[str] = None,
    user: UnifiedUser = Depends(get_current_user),
):
    """
    Get eBay token monitoring status.

    Args:
        token_id: Optional specific token ID to get status for

    Returns:
        Token status information
    """
    # Check permissions - require admin or monitoring role
    if not user.has_permission("admin") and not user.has_permission("monitoring"):
        raise HTTPException(
            status_code=403, detail="Not authorized to access token monitoring"
        )

    # Get token monitor from app state
    token_monitor = request.app.state.ebay_token_monitor
    if not token_monitor:
        raise HTTPException(status_code=500, detail="eBay token monitor not available")

    # Get token status
    status = token_monitor.get_token_status(token_id)

    # Additional processing for timestamps to ensure JSON compatibility
    if "tokens" in status:
        for token in status["tokens"]:
            if "expiry" in token:
                token["expiry"] = token["expiry"].isoformat()
            if "last_updated" in token:
                token["last_updated"] = token["last_updated"].isoformat()
            if "last_refreshed" in token:
                token["last_refreshed"] = token["last_refreshed"].isoformat()

    if "refresh_history" in status:
        for refresh in status["refresh_history"]:
            if "timestamp" in refresh:
                refresh["timestamp"] = refresh["timestamp"].isoformat()

    return status


@router.get("/health/detailed", tags=["monitoring"])
async def get_detailed_health(
    request: Request,
    include_metrics: bool = False,
    include_dependencies: bool = True,
    user: UnifiedUser = Depends(require_permissions(["admin", "monitoring", "health_viewer"])),
):
    """
    Get detailed health status for all system components.

    Args:
        include_metrics: Whether to include detailed metrics in the response
        include_dependencies: Whether to include dependency health checks

    Returns:
        Detailed health status information
    """
    # Initialize response structure
    response = {
        "status": HealthStatus.RUNNING.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": (
            request.app.version if hasattr(request.app, "version") else "unknown"
        ),
        "components": {},
    }

    monitoring_manager = None
    if hasattr(request.app.state, "monitoring_manager"):
        monitoring_manager = request.app.state.monitoring_manager

    # Check database health
    try:
        if hasattr(request.app.state, "db"):
            db = request.app.state.db
            # Check database connection
            db_health = {"status": HealthStatus.RUNNING.value}

            # Get connection pool info if available
            if hasattr(db, "pool"):
                pool_metrics = {
                    "size": db.pool.size,
                    "available": db.pool.freesize,
                    "used": db.pool.size - db.pool.freesize,
                }
                db_health["pool"] = pool_metrics

                # Flag a warning if pool is nearly full
                if db.pool.freesize < 2:  # Less than 2 connections available
                    db_health["status"] = HealthStatus.DEGRADED.value
                    db_health["message"] = "Database connection pool nearly exhausted"
                    response["status"] = HealthStatus.DEGRADED.value

            # Check db monitor for detailed metrics
            if monitoring_manager and hasattr(monitoring_manager, "db_monitor"):
                db_monitor = monitoring_manager.db_monitor
                db_metrics = db_monitor.get_metrics()

                if db_metrics:
                    db_health["metrics"] = (
                        db_metrics
                        if include_metrics
                        else {
                            "query_count": db_metrics.get("query_count", 0),
                            "error_rate": db_metrics.get("error_rate", 0),
                            "avg_query_time": db_metrics.get("avg_query_time", 0),
                        }
                    )

                    # Flag issues based on metrics
                    if db_metrics.get("error_rate", 0) > 0.05:  # Error rate > 5%
                        db_health["status"] = HealthStatus.DEGRADED.value
                        db_health["message"] = (
                            f"High database error rate: {db_metrics.get('error_rate', 0)*100:.1f}%"
                        )
                        response["status"] = HealthStatus.DEGRADED.value

                    if (
                        db_metrics.get("avg_query_time", 0) > 500
                    ):  # Avg query time > 500ms
                        db_health["status"] = HealthStatus.DEGRADED.value
                        db_health["message"] = (
                            f"Slow database queries: {db_metrics.get('avg_query_time', 0):.1f}ms avg"
                        )
                        response["status"] = HealthStatus.DEGRADED.value

            response["components"]["database"] = db_health
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        response["components"]["database"] = {
            "status": HealthStatus.ERROR.value,
            "message": f"Database health check failed: {str(e)}",
        }
        response["status"] = HealthStatus.DEGRADED.value

    # Check Redis health
    try:
        if hasattr(request.app.state, "redis_manager"):
            redis_manager = request.app.state.redis_manager
            # Check Redis connection
            redis_health = {"status": HealthStatus.RUNNING.value}

            # Perform a ping test
            # This is a simple way to verify Redis is responding
            await redis_manager.ping()

            # Get Redis info if available
            if hasattr(redis_manager, "get_client"):
                redis_client = await redis_manager.get_client()
                redis_info = await redis_client.info()

                if redis_info:
                    redis_health["metrics"] = (
                        redis_info
                        if include_metrics
                        else {
                            "connected_clients": redis_info.get("connected_clients", 0),
                            "used_memory_human": redis_info.get(
                                "used_memory_human", "unknown"
                            ),
                            "uptime_in_days": redis_info.get("uptime_in_days", 0),
                        }
                    )

                    # Flag issues based on metrics
                    if (
                        redis_info.get("connected_clients", 0)
                        > redis_info.get("maxclients", 10000) * 0.9
                    ):
                        redis_health["status"] = HealthStatus.DEGRADED.value
                        redis_health["message"] = (
                            "Redis connection limit nearly reached"
                        )
                        response["status"] = HealthStatus.DEGRADED.value

                    # Check memory usage
                    used_memory = redis_info.get("used_memory", 0)
                    max_memory = redis_info.get("maxmemory", 0)
                    if max_memory > 0 and used_memory > max_memory * 0.9:
                        redis_health["status"] = HealthStatus.DEGRADED.value
                        redis_health["message"] = "Redis memory usage high"
                        response["status"] = HealthStatus.DEGRADED.value

            response["components"]["redis"] = redis_health
    except Exception as e:
        logger.error("Redis health check failed: %s", str(e))
        response["components"]["redis"] = {
            "status": HealthStatus.ERROR.value,
            "message": f"Redis health check failed: {str(e)}",
        }
        response["status"] = HealthStatus.DEGRADED.value

    # Check Qdrant health
    try:
        if hasattr(request.app.state, "vector_store"):
            vector_store = request.app.state.vector_store
            qdrant_health = {"status": HealthStatus.RUNNING.value}

            # Check if service is responding
            collections = await vector_store.list_collections()
            qdrant_health["collections_count"] = len(collections) if collections else 0

            # Get collection info if available
            if hasattr(vector_store, "get_collection_info") and collections:
                collection_info = {}
                for collection in collections[
                    :5
                ]:  # Limit to 5 collections to avoid large responses
                    try:
                        info = await vector_store.get_collection_info(collection)
                        collection_info[collection] = {
                            "vector_count": info.get("vectors_count", 0),
                            "status": "available",
                        }
                    except Exception as coll_e:
                        collection_info[collection] = {
                            "status": "error",
                            "message": str(coll_e),
                        }
                        qdrant_health["status"] = HealthStatus.DEGRADED.value
                        response["status"] = HealthStatus.DEGRADED.value

                qdrant_health["collections"] = (
                    collection_info
                    if include_metrics
                    else {
                        "count": len(collections),
                        "available": sum(
                            1
                            for c in collection_info.values()
                            if c.get("status") == "available"
                        ),
                    }
                )

            response["components"]["qdrant"] = qdrant_health
    except Exception as e:
        logger.error("Qdrant health check failed: %s", str(e))
        response["components"]["qdrant"] = {
            "status": HealthStatus.ERROR.value,
            "message": f"Qdrant health check failed: {str(e)}",
        }
        response["status"] = HealthStatus.DEGRADED.value

    # Check agent system health
    try:
        if hasattr(request.app.state, "agent_system") or hasattr(
            request.app.state, "agent_manager"
        ):
            agent_system = getattr(
                request.app.state,
                "agent_system",
                getattr(request.app.state, "agent_manager", None),
            )

            if agent_system:
                agent_health = {"status": HealthStatus.RUNNING.value}

                # Get active agents
                active_agents = (
                    await agent_system.get_active_agents()
                    if hasattr(agent_system, "get_active_agents")
                    else []
                )
                agent_health["active_agents"] = len(active_agents)

                # Get agent metrics if available
                if hasattr(agent_system, "get_health_metrics"):
                    metrics = await agent_system.get_health_metrics()
                    agent_health["metrics"] = (
                        metrics
                        if include_metrics
                        else {
                            "message_count": metrics.get("message_count", 0),
                            "error_rate": metrics.get("error_rate", 0),
                            "avg_response_time": metrics.get("avg_response_time", 0),
                        }
                    )

                    # Flag issues based on metrics
                    if metrics.get("error_rate", 0) > 0.1:  # Error rate > 10%
                        agent_health["status"] = HealthStatus.DEGRADED.value
                        agent_health["message"] = (
                            f"High agent error rate: {metrics.get('error_rate', 0)*100:.1f}%"
                        )
                        response["status"] = HealthStatus.DEGRADED.value

                response["components"]["agent_system"] = agent_health
    except Exception as e:
        logger.error("UnifiedAgent system health check failed: %s", str(e))
        response["components"]["agent_system"] = {
            "status": HealthStatus.UNKNOWN.value,
            "message": f"UnifiedAgent system health check failed: {str(e)}",
        }

    # Check eBay integration
    try:
        if hasattr(request.app.state, "ebay_token_monitor"):
            token_monitor = request.app.state.ebay_token_monitor
            token_status = await token_monitor.get_status()

            # Determine status based on token status
            ebay_status = HealthStatus.RUNNING
            for token in token_status.get("tokens", []):
                if token.get("status") == "expired":
                    ebay_status = HealthStatus.ERROR
                elif token.get("status") == "expiring_soon":
                    ebay_status = HealthStatus.DEGRADED

            # Create response
            ebay_health = {
                "status": ebay_status.value,
                "token_count": len(token_status.get("tokens", [])),
                "active_token_count": len(
                    [
                        t
                        for t in token_status.get("tokens", [])
                        if t.get("status") == "active"
                    ]
                ),
            }

            # Include full token details if requested
            if include_metrics:
                ebay_health["tokens"] = token_status.get("tokens", [])

            # Update overall status if eBay integration is unhealthy
            if ebay_status == HealthStatus.ERROR:
                response["status"] = HealthStatus.DEGRADED.value

            response["components"]["ebay"] = ebay_health
    except Exception as e:
        logger.error("eBay health check failed: %s", str(e))
        response["components"]["ebay"] = {
            "status": HealthStatus.ERROR.value,
            "message": f"eBay health check failed: {str(e)}",
        }
        response["status"] = HealthStatus.DEGRADED.value

    # Check Amazon SP-API health
    try:
        if hasattr(request.app.state, "sp_api_auth") or hasattr(
            request.app.state, "sp_api_client"
        ):
            sp_api_auth = getattr(request.app.state, "sp_api_auth", None)

            amazon_status = HealthStatus.RUNNING
            amazon_health = {"status": amazon_status.value}

            # Check auth status
            if sp_api_auth:
                try:
                    auth_status = await sp_api_auth.check_status()
                    amazon_health["auth_status"] = "ok"
                    amazon_health["auth_details"] = (
                        auth_status if include_metrics else {}
                    )
                except Exception as auth_e:
                    logger.error("Amazon SP-API auth check failed: %s", str(auth_e))
                    amazon_health["auth_status"] = "error"
                    amazon_health["auth_message"] = str(auth_e)
                    amazon_status = HealthStatus.ERROR
                    amazon_health["status"] = amazon_status.value

            # Check API availability
            sp_api_client = getattr(request.app.state, "sp_api_client", None)
            if sp_api_client:
                try:
                    api_status = await sp_api_client.check_health()
                    amazon_health["api_status"] = "ok"
                    amazon_health["api_details"] = api_status if include_metrics else {}
                except Exception as api_e:
                    logger.error("Amazon SP-API health check failed: %s", str(api_e))
                    amazon_health["api_status"] = "error"
                    amazon_health["api_message"] = str(api_e)
                    # Only degrade if we couldn't get auth either
                    if amazon_status == HealthStatus.ERROR:
                        amazon_health["status"] = HealthStatus.ERROR.value
                    else:
                        amazon_health["status"] = HealthStatus.DEGRADED.value
                        amazon_status = HealthStatus.DEGRADED

            response["components"]["amazon"] = amazon_health

            # Update overall status
            if amazon_status == HealthStatus.ERROR:
                response["status"] = HealthStatus.DEGRADED.value
    except Exception as e:
        logger.error("Amazon health check failed: %s", str(e))
        response["components"]["amazon"] = {
            "status": HealthStatus.ERROR.value,
            "message": f"Amazon health check failed: {str(e)}",
        }
        response["status"] = HealthStatus.DEGRADED.value

    # Check payment processor health
    try:
        if hasattr(request.app.state, "payment_service"):
            payment_service = request.app.state.payment_service

            if payment_service:
                payment_health = {"status": HealthStatus.RUNNING.value}
                payment_provider = "paypal"

                # Check if we can verify a webhook to test connectivity
                if hasattr(payment_service, "verify_webhook_event"):
                    try:
                        # Create a minimal test event to validate
                        test_event = {
                            "test": True,
                            "timestamp": datetime.now().isoformat(),
                        }
                        verification = await payment_service.verify_webhook_event(
                            test_event
                        )
                        payment_health["webhook_verification"] = (
                            "working" if verification else "failing"
                        )

                        if not verification:
                            payment_health["status"] = HealthStatus.DEGRADED.value
                            payment_health["message"] = (
                                "Payment webhook verification failing"
                            )
                            response["status"] = HealthStatus.DEGRADED.value
                    except Exception as webhook_e:
                        payment_health["webhook_verification"] = "error"
                        payment_health["webhook_message"] = str(webhook_e)
                        payment_health["status"] = HealthStatus.DEGRADED.value
                        response["status"] = HealthStatus.DEGRADED.value

                # Add metrics if we're including them
                if include_metrics and hasattr(payment_service, "metrics_service"):
                    # Try to get some basic metrics from the metrics service
                    metrics_service = payment_service.metrics_service
                    if metrics_service:
                        payment_health["metrics"] = {
                            "transaction_success_rate": await metrics_service.get_metric(
                                "payment_success_rate", 1.0
                            ),
                            "transaction_count": await metrics_service.get_metric(
                                "payment_transactions_total", 0
                            ),
                            "error_count": await metrics_service.get_metric(
                                "payment_errors_total", 0
                            ),
                        }

                response["components"]["payment_gateway"] = {
                    **payment_health,
                    "provider": payment_provider,
                }
    except Exception as e:
        logger.error("Payment processor health check failed: %s", str(e))
        response["components"]["payment_gateway"] = {
            "status": HealthStatus.ERROR.value,
            "message": f"Payment processor health check failed: {str(e)}",
        }

    # Check ML service health
    try:
        if hasattr(request.app.state, "ml_service_client"):
            ml_client = request.app.state.ml_service_client
            ml_health = {"status": HealthStatus.RUNNING.value}

            # Ping ML service
            ml_status = await ml_client.get_health()
            if ml_status:
                ml_health["api_status"] = ml_status.get("status", "unknown")
                ml_health["metrics"] = (
                    ml_status
                    if include_metrics
                    else {
                        "model_count": ml_status.get("model_count", 0),
                        "uptime": ml_status.get("uptime", 0),
                    }
                )

                # Check ML service status
                if ml_status.get("status") != "healthy":
                    ml_health["status"] = HealthStatus.DEGRADED.value
                    ml_health["message"] = (
                        f"ML service reports status: {ml_status.get('status')}"
                    )
                    response["status"] = HealthStatus.DEGRADED.value

            response["components"]["ml_service"] = ml_health
    except Exception as e:
        logger.error("ML service health check failed: %s", str(e))
        response["components"]["ml_service"] = {
            "status": HealthStatus.ERROR.value,
            "message": f"ML service health check failed: {str(e)}",
        }
        response["status"] = HealthStatus.DEGRADED.value

    # Return combined health response
    return response


@router.get("/dashboard/enhanced", tags=["monitoring", "dashboard"])
async def get_enhanced_dashboard(
    user: UnifiedUser = Depends(require_permissions(["admin", "monitoring"])),
):
    """
    Get enhanced performance dashboard with real-time metrics.

    Returns comprehensive performance metrics including:
    - API response times
    - AI analysis performance
    - WebSocket latency
    - Database performance
    - System health status
    """
    try:
        # Collect real-time metrics
        performance_metrics = await enhanced_dashboard.collect_real_time_metrics()

        # Validate AI accuracy
        ai_validation = await enhanced_dashboard.validate_ai_accuracy()

        # Check system health
        system_health = await enhanced_dashboard.check_system_health()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "operational",
            "performance_metrics": {
                "api_response_time": f"{performance_metrics.api_response_time*1000:.1f}ms",
                "ai_analysis_time": f"{performance_metrics.ai_analysis_time:.2f}s",
                "websocket_latency": f"{performance_metrics.websocket_latency*1000:.1f}ms",
                "database_query_time": f"{performance_metrics.database_query_time*1000:.1f}ms",
                "memory_usage": f"{performance_metrics.memory_usage:.1f}MB",
                "cpu_usage": f"{performance_metrics.cpu_usage:.1f}%",
                "active_connections": performance_metrics.active_connections,
                "success_rate": f"{performance_metrics.success_rate*100:.1f}%",
            },
            "ai_validation_metrics": {
                "total_validations": ai_validation.total_validations,
                "consensus_matches": ai_validation.consensus_matches,
                "average_accuracy": f"{ai_validation.average_accuracy*100:.1f}%",
                "confidence_improvements": ai_validation.confidence_improvements,
                "validation_success_rate": f"{ai_validation.validation_success_rate*100:.1f}%",
            },
            "system_health": {
                "overall_status": system_health.overall_status,
                "api_status": system_health.api_status,
                "database_status": system_health.database_status,
                "ai_services_status": system_health.ai_services_status,
                "cache_status": system_health.cache_status,
                "websocket_status": system_health.websocket_status,
                "uptime": f"{system_health.uptime/3600:.1f} hours",
            },
            "performance_thresholds": {
                "api_response_time": "100ms",
                "ai_analysis_time": "5s",
                "websocket_latency": "100ms",
                "database_query_time": "50ms",
                "success_rate": "95%",
            },
        }

    except Exception as e:
        logger.error(f"Error getting enhanced dashboard: {e}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "status": "error",
        }


@router.get("/dashboard/performance", tags=["monitoring", "dashboard"])
async def get_performance_report(
    time_range: str = "1h",
    user: UnifiedUser = Depends(require_permissions(["admin", "monitoring"])),
):
    """
    Get comprehensive performance report for specified time range.

    Args:
        time_range: Time range for report (1h, 24h, 7d)

    Returns:
        Detailed performance report with aggregated metrics
    """
    try:
        report = await enhanced_dashboard.generate_performance_report(time_range)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "operational",
            **report,
        }

    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "status": "error",
        }


@router.get("/dashboard/ai-validation", tags=["monitoring", "dashboard"])
async def get_ai_validation_metrics(
    user: UnifiedUser = Depends(require_permissions(["admin", "monitoring"])),
):
    """
    Get AI validation metrics and accuracy reports.

    Returns:
        AI validation metrics including consensus analysis and accuracy scores
    """
    try:
        ai_metrics = await enhanced_dashboard.validate_ai_accuracy()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "operational",
            "ai_validation": {
                "total_validations": ai_metrics.total_validations,
                "consensus_matches": ai_metrics.consensus_matches,
                "average_accuracy": ai_metrics.average_accuracy,
                "confidence_improvements": ai_metrics.confidence_improvements,
                "average_confidence_boost": ai_metrics.average_confidence_boost,
                "validation_success_rate": ai_metrics.validation_success_rate,
            },
            "accuracy_targets": {
                "minimum_accuracy": "75%",
                "target_accuracy": "85%",
                "consensus_threshold": "70%",
                "confidence_improvement_target": "5%",
            },
            "performance_status": {
                "accuracy_meets_target": ai_metrics.average_accuracy >= 0.75,
                "consensus_rate_good": ai_metrics.validation_success_rate >= 0.70,
                "overall_status": (
                    "good"
                    if ai_metrics.average_accuracy >= 0.75
                    and ai_metrics.validation_success_rate >= 0.70
                    else "needs_improvement"
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error getting AI validation metrics: {e}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "status": "error",
        }
