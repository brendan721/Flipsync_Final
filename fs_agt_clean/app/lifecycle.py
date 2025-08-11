"""
Application Lifecycle Management for FlipSync
===========================================

This module handles the startup and shutdown lifecycle of the FlipSync application.
Extracted from main.py to improve maintainability and separation of concerns.

Responsibilities:
- Application startup sequence
- Service initialization coordination
- Graceful shutdown procedures
- Resource cleanup
- Error handling during lifecycle events
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI

from fs_agt_clean.app.services.service_initializer import init_services
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.logger import LogManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.

    This is the consolidated lifespan manager incorporating functionality from:
    - fs_agt/main.py
    - fs_agt/services/ml/app.py
    - fs_agt/services/api/main.py
    - fs_agt/services/dashboard/main.py
    """
    services = {}

    try:
        # Initialize core services
        services = await init_services(app)

        # Initialize global database instance for dependency injection
        logger.info("Initializing global database instance...")
        try:
            from fs_agt_clean.core.db.database import initialize_global_database

            await initialize_global_database()
            logger.info("Global database instance initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize global database instance: {e}")
            # Don't fail startup, as the main database is already initialized

        # Store services in app state for dependency injection
        app.state.redis = services.get("redis_manager")
        app.state.auth = services.get("auth_service")  # Unified auth system
        app.state.db_auth = services.get("db_auth_service")  # Also unified auth system
        app.state.unified_auth = services.get("auth_service")  # Explicit reference
        app.state.database = services.get("database")
        app.state.chat_service = services.get("chat_service")
        app.state.realtime_service = services.get("realtime_service")
        app.state.qdrant_service = services.get("qdrant_service")
        app.state.real_agent_manager = services.get("real_agent_manager")

        # ✅ CRITICAL FIX: Ensure chat service has app reference for RealAgentManager access
        if app.state.chat_service and not hasattr(app.state.chat_service, "app"):
            logger.info(
                "Setting app reference in chat service for RealAgentManager access"
            )
            app.state.chat_service.app = app
            logger.info("✅ Chat service app reference set successfully")
        elif app.state.chat_service and app.state.chat_service.app is None:
            logger.info("Updating null app reference in chat service")
            app.state.chat_service.app = app
            logger.info("✅ Chat service app reference updated successfully")
        else:
            logger.info(
                "Chat service already has app reference or chat service is None"
            )

        # Initialize additional services that depend on app state
        await _init_additional_services(app, services)

        logger.info("Services started successfully")
        yield services

    except Exception as e:
        logger.error("Error during application startup: %s", str(e))
        logger.exception(e)
        logger.error("Service status: down due to startup error")
        # Re-raise to prevent app startup with failed initialization
        raise

    finally:
        # Cleanup services
        await _cleanup_services(app, services)


async def _init_additional_services(app: FastAPI, services: Dict[str, Any]) -> None:
    """Initialize additional services that depend on the main services."""
    logger.info("Initializing additional services...")

    # Initialize metrics service
    await _init_metrics_service(app, services)

    # Initialize ML service
    await _init_ml_service(app, services)

    # Initialize Dashboard service
    await _init_dashboard_service(app, services)

    # Initialize enhanced monitoring services
    await _init_enhanced_monitoring_services(app, services)

    # Initialize eBay integration services
    await _init_ebay_services(app, services)

    # Initialize token lifecycle manager
    await _init_token_lifecycle_manager(app, services)


async def _init_metrics_service(app: FastAPI, services: Dict[str, Any]) -> None:
    """Initialize metrics service if available."""
    try:
        from fs_agt_clean.core.metrics.service import MetricsService

        logger.info("Initializing metrics service...")

        # Get the required services
        config_manager = services.get("config")
        log_manager = services.get("log_manager")

        # Make sure they are not None
        if not config_manager:
            config_manager = ConfigManager()
        if not log_manager:
            log_manager = LogManager()

        # Create the metrics service
        metrics_service = MetricsService()

        # Add it to the services dictionary
        services["metrics_service"] = metrics_service

        logger.info("Metrics service initialized successfully")

    except ImportError:
        logger.warning(
            "Metrics service not available - metrics capabilities will be disabled"
        )
    except Exception as e:
        logger.warning(f"Metrics service initialization failed: {str(e)}")


async def _init_ml_service(app: FastAPI, services: Dict[str, Any]) -> None:
    """Initialize ML service if available."""
    try:
        from fs_agt_clean.services.ml.service import MLService

        logger.info("Initializing ML service...")

        # Initialize ML service with config and metrics
        ml_service = MLService(
            config_manager=services.get("config"),
            metrics_service=services.get("metrics_service"),
        )

        # Add to services dictionary
        services["ml_service"] = ml_service

        # Make sure it's available in the app state
        app.state.ml_service = ml_service

        logger.info("ML service initialized successfully")

    except ImportError:
        logger.warning("ML service not available - ML capabilities will be disabled")
    except Exception as e:
        logger.warning(f"ML service initialization failed: {str(e)}")
        services["ml_service"] = None


async def _init_dashboard_service(app: FastAPI, services: Dict[str, Any]) -> None:
    """Initialize Dashboard service if available."""
    try:
        from fs_agt_clean.services.dashboard.service import DashboardService

        logger.info("Initializing Dashboard service...")

        # Create and initialize the dashboard service
        dashboard_service = DashboardService(
            config_manager=services.get("config"),
            metrics_service=services.get("metrics_service")
            or services.get("metrics_collector"),
            database=services.get("database"),
        )

        # Initialize the dashboard service
        await dashboard_service.initialize()

        # Add to services
        services["dashboard_service"] = dashboard_service

        # Make sure it's available in the app state
        app.state.dashboard_service = dashboard_service

        logger.info("Dashboard service initialized successfully")

    except ImportError:
        logger.warning("Dashboard service module not found - using placeholder")
        logger.info("Dashboard service initialization placeholder")
    except Exception as e:
        logger.warning(f"Dashboard service initialization failed: {str(e)}")
        logger.info("Dashboard service initialization placeholder")


async def _init_enhanced_monitoring_services(
    app: FastAPI, services: Dict[str, Any]
) -> None:
    """Initialize enhanced monitoring services."""
    logger.info("Initializing enhanced monitoring services...")

    try:
        from fs_agt_clean.core.monitoring.health_monitor import RealHealthMonitor
        from fs_agt_clean.services.monitoring.alert_service import EnhancedAlertService
        from fs_agt_clean.services.monitoring.metrics_collector import (
            MetricsCollector as EnhancedMetricsCollector,
        )
        from fs_agt_clean.services.monitoring.metrics_service import (
            MetricsService as EnhancedMetricsService,
        )

        # Create enhanced monitoring services
        enhanced_metrics_service = EnhancedMetricsService(services["database"])
        alert_service = EnhancedAlertService(services["database"])
        health_monitor = RealHealthMonitor()
        enhanced_metrics_collector = EnhancedMetricsCollector(
            metrics_service=enhanced_metrics_service,
            health_monitor=health_monitor,
            collection_interval=60,  # Collect metrics every minute
            service_name="flipsync-api",
        )

        # Store enhanced monitoring services
        services["enhanced_metrics_service"] = enhanced_metrics_service
        services["enhanced_alert_service"] = alert_service
        services["enhanced_health_monitor"] = health_monitor
        services["enhanced_metrics_collector"] = enhanced_metrics_collector

        # Start the metrics collector
        await enhanced_metrics_collector.start()

        logger.info("Enhanced monitoring services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize enhanced monitoring services: {e}")
        logger.warning("Continuing without enhanced monitoring")


async def _init_ebay_services(app: FastAPI, services: Dict[str, Any]) -> None:
    """Initialize eBay integration services."""
    import os

    # 🤖 Initialize eBay Agentic Integration Service
    if os.getenv("ENABLE_AGENTIC_INTEGRATION", "true").lower() == "true":
        logger.info("🤖 Initializing eBay Agentic Integration Service...")
        try:
            from fs_agt_clean.services.marketplace.ebay_inventory_integration import (
                get_ebay_integration_service,
            )

            ebay_integration = await get_ebay_integration_service()
            app.state.ebay_integration = ebay_integration
            services["ebay_integration"] = ebay_integration
            logger.info("🤖 eBay Agentic Integration Service initialized successfully")

        except Exception as e:
            logger.error(
                f"🤖 Failed to initialize eBay Agentic Integration Service: {e}"
            )
            logger.warning("🤖 Continuing without eBay Agentic Integration Service")
            app.state.ebay_integration = None
            services["ebay_integration"] = None
    else:
        logger.info("🤖 eBay Agentic Integration Service disabled via feature flag")
        app.state.ebay_integration = None
        services["ebay_integration"] = None


async def _init_token_lifecycle_manager(app: FastAPI, services: Dict[str, Any]) -> None:
    """Initialize eBay Token Lifecycle Manager."""
    logger.info("🔄 Initializing eBay Token Lifecycle Manager...")

    try:
        from fs_agt_clean.services.marketplace.ebay_token_lifecycle_manager import (
            get_token_lifecycle_manager,
        )

        token_lifecycle_manager = get_token_lifecycle_manager()
        await token_lifecycle_manager.start_background_services()
        app.state.token_lifecycle_manager = token_lifecycle_manager
        services["token_lifecycle_manager"] = token_lifecycle_manager
        logger.info("🔄 eBay Token Lifecycle Manager initialized successfully")
        logger.info("   - Proactive refresh: Every hour")
        logger.info("   - Refresh token monitoring: Daily")
        logger.info("   - Health monitoring: Every 15 minutes")

    except Exception as e:
        logger.error(f"🔄 Failed to initialize Token Lifecycle Manager: {e}")
        logger.warning("🔄 Continuing without Token Lifecycle Manager")
        app.state.token_lifecycle_manager = None
        services["token_lifecycle_manager"] = None


async def _cleanup_services(app: FastAPI, services: Dict[str, Any]) -> None:
    """Cleanup all services during application shutdown."""
    try:
        logger.info("Shutting down services...")

        # Shutdown Token Lifecycle Manager if it was initialized
        if (
            hasattr(app.state, "token_lifecycle_manager")
            and app.state.token_lifecycle_manager
        ):
            logger.info("🔄 Shutting down eBay Token Lifecycle Manager...")
            try:
                await app.state.token_lifecycle_manager.stop_background_services()
                logger.info("🔄 eBay Token Lifecycle Manager shutdown complete")
            except Exception as e:
                logger.error(f"🔄 Error shutting down Token Lifecycle Manager: {e}")

        # Shutdown ML service if it was initialized
        if "ml_service" in services and services["ml_service"]:
            logger.info("Shutting down ML service...")
            # ML service cleanup would go here if needed

        # Shutdown other services
        if "auth_service" in services:
            logger.info("AuthService shutdown skipped - no shutdown method available")

        if "redis_manager" in services and services["redis_manager"]:
            await services["redis_manager"].close()

        # Shutdown dashboard service if it was initialized
        if "dashboard_service" in services and services["dashboard_service"]:
            logger.info("Shutting down Dashboard service...")
            try:
                await services["dashboard_service"].shutdown()
                logger.info("Dashboard service shutdown complete")
            except Exception as e:
                logger.warning(f"Error shutting down Dashboard service: {str(e)}")

        # Shutdown enhanced monitoring services if they were initialized
        if (
            "enhanced_metrics_collector" in services
            and services["enhanced_metrics_collector"]
        ):
            logger.info("Shutting down enhanced metrics collector...")
            try:
                await services["enhanced_metrics_collector"].stop()
                logger.info("Enhanced metrics collector shutdown complete")
            except Exception as e:
                logger.warning(
                    f"Error shutting down enhanced metrics collector: {str(e)}"
                )

        # 🤖 Shutdown eBay Agentic Integration Service if it was initialized
        if "ebay_integration" in services and services["ebay_integration"] is not None:
            logger.info("🤖 Shutting down eBay Agentic Integration Service...")
            try:
                # The integration service doesn't have a shutdown method, so just log
                logger.info("🤖 eBay Agentic Integration Service shutdown complete")
            except Exception as e:
                logger.warning(
                    f"🤖 Error shutting down eBay Agentic Integration Service: {str(e)}"
                )

        # Shutdown real agent manager if it was initialized
        if "real_agent_manager" in services and services["real_agent_manager"]:
            logger.info("Shutting down real agent manager...")
            try:
                await services["real_agent_manager"].shutdown()
                logger.info("Real agent manager shutdown complete")
            except Exception as e:
                logger.warning(f"Error shutting down real agent manager: {str(e)}")

        # 🔧 CRITICAL FIX: Cleanup autonomous agents that may have been initialized during startup
        logger.info("🧹 Cleaning up autonomous agents...")
        try:
            # Import agent registry to find any registered agents
            from fs_agt_clean.core.registry.agent_registry import get_agent_registry

            agent_registry = get_agent_registry()
            registered_agents = await agent_registry.get_all_agents()

            # Clean up each registered agent
            for agent_info in registered_agents:
                try:
                    agent_instance = agent_info.get("instance")
                    agent_id = agent_info.get("agent_id", "unknown")

                    if agent_instance and hasattr(agent_instance, "cleanup"):
                        logger.info(f"🧹 Cleaning up agent: {agent_id}")
                        await agent_instance.cleanup()
                        logger.info(f"✅ Agent {agent_id} cleaned up successfully")
                    elif agent_instance and hasattr(agent_instance, "close"):
                        logger.info(f"🧹 Closing agent: {agent_id}")
                        await agent_instance.close()
                        logger.info(f"✅ Agent {agent_id} closed successfully")
                    else:
                        logger.debug(f"Agent {agent_id} has no cleanup method")

                except Exception as e:
                    logger.warning(f"Error cleaning up agent {agent_id}: {e}")

            # Shutdown the agent registry itself
            await agent_registry.shutdown()
            logger.info("✅ Agent registry shutdown complete")

        except Exception as e:
            logger.warning(f"Error during agent cleanup: {e}")

        # 🔧 CRITICAL FIX: Cleanup any global database connections
        logger.info("🧹 Cleaning up global database connections...")
        try:
            from fs_agt_clean.core.db.database import get_database

            global_db = get_database()
            if global_db and hasattr(global_db, "close"):
                await global_db.close()
                logger.info("✅ Global database connections closed")

        except Exception as e:
            logger.warning(f"Error cleaning up global database connections: {e}")

        logger.info("✅ Service shutdown complete")

    except Exception as e:
        logger.error(f"Error during service cleanup: {str(e)}")
        logger.exception("Full cleanup error details:")
