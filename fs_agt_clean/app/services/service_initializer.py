"""
Service Initialization Module for FlipSync Application
====================================================

This module handles the initialization of all core services in the correct order.
Extracted from main.py to improve maintainability and separation of concerns.

Services initialized:
- Redis connection and configuration
- Database connection and tables
- Authentication system
- Event bus and core services
- Token management and rotation
- Vector store (Qdrant)
- Business logic services
- WebSocket handlers
- Monitoring and metrics
"""

import logging
import os
from typing import Any, Dict

from fs_agt_clean.core.auth.auth_factory import AuthenticationFactory
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.db.connection_manager import DatabaseConnectionManager
from fs_agt_clean.core.events.bus.secure_event_bus import SecureEventBus
from fs_agt_clean.core.monitoring.logger import LogManager
from fs_agt_clean.core.monitoring.metrics.collector import MetricsCollector
from fs_agt_clean.core.redis.redis_manager import RedisConfig, RedisManager
from fs_agt_clean.core.security.audit_logger import ComplianceAuditLogger
from fs_agt_clean.core.monitoring.exporters.prometheus import SERVICE_STATUS

logger = logging.getLogger(__name__)


async def init_redis_service(
    config: ConfigManager, log_manager: LogManager
) -> RedisManager:
    """Initialize Redis connection with unified configuration."""
    logger = log_manager.get_logger(__name__)
    logger.info("Initializing Redis connection...")

    from fs_agt_clean.core.config.redis_config_unified import get_global_redis_config

    unified_redis_config = get_global_redis_config()
    logger.info(
        f"Connecting to Redis at {unified_redis_config.host}:{unified_redis_config.port} "
        f"(db: {unified_redis_config.db}, auth: {'yes' if unified_redis_config.password else 'no'})"
    )

    # Convert unified config to RedisManager compatible config
    redis_config = RedisConfig(
        host=unified_redis_config.host,
        port=unified_redis_config.port,
        db=unified_redis_config.db,
        password=unified_redis_config.password,
        encoding=unified_redis_config.encoding,
        decode_responses=unified_redis_config.decode_responses,
        socket_timeout=unified_redis_config.socket_timeout,
        socket_connect_timeout=unified_redis_config.socket_connect_timeout,
        retry_on_timeout=unified_redis_config.retry_on_timeout,
        max_connections=unified_redis_config.max_connections,
    )
    redis_manager = RedisManager(redis_config)
    await redis_manager.initialize()
    logger.info("Redis connection established successfully")

    return redis_manager


async def init_database_service(
    config: ConfigManager, log_manager: LogManager, app
) -> Any:
    """Initialize Database connection with retry capabilities."""
    logger = log_manager.get_logger(__name__)
    logger.info("Initializing Database...")

    from fs_agt_clean.core.db.database import Database

    try:
        # Get database configuration from config
        db_config = config.get_section("database") or {}
        connection_string = db_config.get("connection_string")

        # If no connection string is provided, check environment variables first
        if not connection_string:
            # Check for DATABASE_URL environment variable first
            connection_string = os.getenv("DATABASE_URL")

            if connection_string:
                # Convert from standard PostgreSQL URL to asyncpg format if needed
                if connection_string.startswith("postgresql://"):
                    connection_string = connection_string.replace(
                        "postgresql://", "postgresql+asyncpg://", 1
                    )
                logger.info(
                    f"Using DATABASE_URL environment variable: {connection_string}"
                )
            else:
                # Only use hardcoded default as last resort
                # Use the correct database name for FlipSync
                db_host = "localhost"
                connection_string = (
                    f"postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@"
                    f"{db_host}:5432/flipsync_agentic_test"
                )
                logger.warning(
                    f"No database connection string found in config or environment, "
                    f"using FlipSync default: {connection_string}"
                )

        # Create the database connection manager with retry capabilities
        connection_manager = DatabaseConnectionManager(
            config_manager=config,
            connection_string=connection_string,
            pool_size=db_config.get("pool_size", 5),
            max_overflow=db_config.get("max_overflow", 10),
            echo=db_config.get("echo", False),
            max_retries=db_config.get("max_retries", 3),
            retry_delay=db_config.get("retry_delay", 1.0),
            max_retry_delay=db_config.get("max_retry_delay", 30.0),
            jitter=db_config.get("jitter", True),
        )

        # Initialize the database connection with retry
        success = await connection_manager.initialize()
        if not success:
            raise Exception("Failed to initialize database connection after retries")

        logger.info("Database connection initialized successfully")

        # For backward compatibility, use the original Database class
        database = Database(
            config_manager=config,
            connection_string=connection_string,
            pool_size=db_config.get("pool_size", 5),
            max_overflow=db_config.get("max_overflow", 10),
            echo=db_config.get("echo", False),
        )

        # Initialize the database
        await database.initialize()

        # Create database tables if they don't exist
        await database.create_tables()
        logger.info("Database tables created successfully")

        # Initialize WebSocket handler with the database
        from fs_agt_clean.core.websocket.handlers import initialize_websocket_handler

        initialize_websocket_handler(database, app)
        logger.info("WebSocket handler initialized with database and app reference")

        # Store the connection manager for health checks and future use
        database.connection_manager = connection_manager

        return database

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        logger.error(
            "Database connection failed - production deployment requires functional database"
        )
        logger.error(
            "ALLOW_NO_DB environment variable is deprecated and removed for security"
        )
        raise Exception(
            "Database connection failed - production deployment requires functional database"
        ) from e


async def init_authentication_service(log_manager: LogManager) -> Any:
    """Initialize Unified Authentication System for FlipSync users."""
    logger = log_manager.get_logger(__name__)
    logger.info("Initializing Unified Authentication System for FlipSync users...")
    logger.info("📝 Note: This is separate from eBay OAuth integration")

    try:
        # Initialize unified authentication system using factory
        unified_auth_system = await AuthenticationFactory.get_auth_system()
        logger.info("✅ Unified FlipSync user authentication system initialized")

        logger.info(
            "✅ Authentication consolidation: Using UnifiedAuthSystem as primary"
        )
        logger.info("📝 Note: Legacy authentication systems have been removed")

        return unified_auth_system

    except Exception as e:
        logger.error(f"❌ Failed to initialize unified authentication system: {e}")
        logger.error("🚨 No fallback available - unified auth system is required")
        raise RuntimeError(f"Authentication system initialization failed: {e}") from e


async def init_webhook_database(database, log_manager: LogManager) -> None:
    """Initialize webhook database tables."""
    logger = log_manager.get_logger(__name__)

    try:
        from fs_agt_clean.core.db.init_webhook_db import init_webhook_db

        logger.info("Imported init_webhook_db function")
        logger.info("Getting database session for webhook initialization")

        async with database.get_session_context() as session:
            logger.info("Starting webhook database initialization")
            await init_webhook_db(session)
            logger.info("Webhook database initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing webhook database: {str(e)}", exc_info=True)


async def init_core_services() -> Dict[str, Any]:
    """Initialize core event bus and metrics services."""
    logger.info("Initializing core services...")

    event_bus = SecureEventBus()
    metrics_collector = MetricsCollector()
    compliance_audit_logger = ComplianceAuditLogger()

    return {
        "event_bus": event_bus,
        "metrics_collector": metrics_collector,
        "compliance_audit_logger": compliance_audit_logger,
    }


async def init_token_management_services(log_manager: LogManager) -> Dict[str, Any]:
    """Initialize token management and rotation services."""
    logger = log_manager.get_logger(__name__)
    logger.info("Initializing token management services...")

    try:
        from fs_agt_clean.core.security.token_manager import (
            SecurityAuditLogger,
            TokenManager,
            VaultSecretManager,
        )

        # Create mock instances for development
        security_audit_logger = SecurityAuditLogger()
        vault_secret_manager = VaultSecretManager()

        # Initialize token manager
        token_manager = TokenManager(
            secret_manager=vault_secret_manager, audit_logger=security_audit_logger
        )
        await token_manager.start()

        # Token rotation service is not implemented yet
        token_rotation_service = None

        logger.info("Token management services initialized successfully")

        return {
            "security_audit_logger": security_audit_logger,
            "token_manager": token_manager,
            "token_rotation_service": token_rotation_service,
        }

    except Exception as e:
        logger.warning(f"Failed to initialize token management services: {e}")
        return {
            "security_audit_logger": None,
            "token_manager": None,
            "token_rotation_service": None,
        }


async def init_vector_store_service(log_manager: LogManager) -> Any:
    """Initialize Vector Store (Qdrant) service."""
    logger = log_manager.get_logger(__name__)
    logger.info("Initializing Vector Store...")

    try:
        from fs_agt_clean.core.vector_store.models import (
            VectorDistanceMetric,
            VectorStoreConfig,
        )
        from fs_agt_clean.core.vector_store.providers.qdrant import QdrantVectorStore

        # Create Qdrant configuration
        qdrant_config = VectorStoreConfig(
            store_id="flipsync-vectors",
            dimension=1536,  # Standard OpenAI embedding dimension
            distance_metric=VectorDistanceMetric.COSINE,
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )

        # Initialize Qdrant vector store
        qdrant = QdrantVectorStore(qdrant_config)
        await qdrant.initialize()
        logger.info("Vector Store (Qdrant) initialized successfully")

        return qdrant

    except Exception as e:
        logger.warning(f"Failed to initialize Vector Store: {e}")
        return None


async def init_qdrant_service(log_manager: LogManager) -> Any:
    """Initialize SimpleQdrantService."""
    logger = log_manager.get_logger(__name__)
    logger.info("Initializing SimpleQdrantService...")

    try:
        from fs_agt_clean.services.qdrant.simple_service import SimpleQdrantService

        qdrant_service = SimpleQdrantService()
        await qdrant_service.init_schema()
        logger.info("SimpleQdrantService initialized successfully")

        return qdrant_service

    except Exception as e:
        logger.warning(f"Failed to initialize SimpleQdrantService: {e}")
        return None


async def init_agent_manager_service(log_manager: LogManager) -> Any:
    """Initialize Real Agent Manager with lazy loading."""
    logger = log_manager.get_logger(__name__)

    try:
        logger.info(
            "🚀 DYNAMIC IMPORT: Creating Real Agent Manager with dynamic import..."
        )

        # Dynamic import to avoid startup issues
        from fs_agt_clean.core.agents.autonomous_agent_manager import (
            AutonomousAgentManager,
        )

        real_agent_manager = AutonomousAgentManager()
        logger.info("✅ DYNAMIC IMPORT: Real Agent Manager created successfully")

        # Skip agent initialization during startup to prevent resource leaks
        logger.info(
            "🔧 RESOURCE LEAK FIX: Skipping agent initialization during startup"
        )
        logger.info("📝 Agents will be initialized on-demand when first requested")
        logger.info("✅ Real Agent Manager created (agents will initialize lazily)")

        return real_agent_manager

    except Exception as e:
        logger.error(f"Failed to initialize Real Agent Manager: {e}")
        logger.exception("Full Real Agent Manager initialization error:")
        return None


async def init_chat_and_realtime_services(
    database, log_manager: LogManager
) -> Dict[str, Any]:
    """Initialize chat and realtime services with database."""
    logger = log_manager.get_logger(__name__)
    logger.info("Initializing chat and realtime services...")

    try:
        from fs_agt_clean.services import realtime_service as realtime_module
        from fs_agt_clean.services.communication.strategic_chat_service import (
            StrategicChatService,
        )
        from fs_agt_clean.services.communication.strategic_chat_adapter import (
            StrategicChatAdapter,
        )
        from fs_agt_clean.services.realtime_service import RealtimeService

        # Initialize strategic chat service with Gemini integration (4+1 architecture)
        strategic_service = StrategicChatService(daily_budget=10.0)
        chat_service = StrategicChatAdapter(strategic_service, database)

        # Initialize realtime service with database
        realtime_service_instance = RealtimeService(database=database)

        # Update the global realtime_service instance
        realtime_module.realtime_service = realtime_service_instance

        logger.info("Chat and realtime services initialized successfully")

        return {
            "chat_service": chat_service,
            "realtime_service": realtime_service_instance,
        }

    except Exception as e:
        logger.error(f"Error initializing chat and realtime services: {e}")
        return {
            "chat_service": None,
            "realtime_service": None,
        }


async def init_services(app) -> Dict[str, Any]:
    """
    Initialize all core services in the correct order.

    This is the main orchestration function that coordinates the initialization
    of all FlipSync services. Extracted from main.py for better maintainability.

    Args:
        app: FastAPI application instance

    Returns:
        Dict containing all initialized services

    Raises:
        RuntimeError: If critical services fail to initialize
    """
    config = ConfigManager()
    log_manager = LogManager()
    logger = log_manager.get_logger(__name__)

    try:
        # 1. Initialize Redis first using unified configuration
        redis_manager = await init_redis_service(config, log_manager)

        # 2. Initialize Database
        database = await init_database_service(config, log_manager, app)

        # Create database tables if they don't exist (redundant but safe)
        await database.create_tables()
        logger.info("Database tables created successfully")

        # 3. Initialize Unified Authentication System (FlipSync Users Only)
        auth_service = await init_authentication_service(log_manager)
        db_auth_service = auth_service  # Use unified system for both

        # Initialize webhook database
        await init_webhook_database(database, log_manager)
        logger.info("Auth services initialized successfully")

        # 4. Initialize Event Bus and Core Services
        core_services = await init_core_services()

        # 5. Initialize Token Management and Rotation Services
        token_services = await init_token_management_services(log_manager)

        # 6. Initialize Vector Store
        qdrant = await init_vector_store_service(log_manager)

        # Set service status to up
        SERVICE_STATUS.labels(service="fs_agt").set(1)

        # Initialize SimpleQdrantService
        qdrant_service = await init_qdrant_service(log_manager)

        # Initialize Real Agent Manager (Skip initialization for faster startup)
        real_agent_manager = await init_agent_manager_service(log_manager)

        # Initialize chat and realtime services with database
        chat_realtime_services = await init_chat_and_realtime_services(
            database, log_manager
        )

        # Return all initialized services
        services = {
            "config": config,
            "log_manager": log_manager,
            "redis_manager": redis_manager,
            "auth_service": auth_service,
            "db_auth_service": db_auth_service,
            "database": database,
            "chat_service": chat_realtime_services["chat_service"],
            "realtime_service": chat_realtime_services["realtime_service"],
            "metrics_collector": core_services["metrics_collector"],
            "qdrant": qdrant,
            "event_bus": core_services["event_bus"],
            "token_manager": token_services["token_manager"],
            "token_rotation_service": token_services["token_rotation_service"],
            "security_audit_logger": token_services["security_audit_logger"],
            "qdrant_service": qdrant_service,
            "real_agent_manager": real_agent_manager,
        }

        return services

    except Exception as e:
        logger.error("Service initialization failed: %s", str(e))
        logger.exception("Full exception details:")
        # Set service status to down on error
        SERVICE_STATUS.labels(service="fs_agt").set(0)
        raise RuntimeError(f"Failed to initialize services: {str(e)}") from e
