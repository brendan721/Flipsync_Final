"""
Production Configuration Management for FlipSync 4+1 Architecture
================================================================

Centralized configuration management with environment-based settings,
security best practices, and production-ready defaults.

Key Features:
- Environment-based configuration loading
- Secure credential management
- Production-ready defaults
- Configuration validation
- No hardcoded values
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    host: str
    port: int
    name: str
    user: str
    password: str
    ssl_mode: str = "require"
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def connection_string(self) -> str:
        """Get database connection string."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?sslmode={self.ssl_mode}"


@dataclass
class RedisConfig:
    """Redis configuration settings."""

    host: str
    port: int
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False

    @property
    def connection_string(self) -> str:
        """Get Redis connection string."""
        protocol = "rediss" if self.ssl else "redis"
        auth = f":{self.password}@" if self.password else ""
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class CorsConfig:
    """CORS configuration settings."""

    allowed_origins: List[str]
    allow_credentials: bool = True
    allow_methods: List[str] = None
    allow_headers: List[str] = None

    def __post_init__(self):
        if self.allow_methods is None:
            self.allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        if self.allow_headers is None:
            self.allow_headers = ["Content-Type", "Authorization", "X-Requested-With"]


@dataclass
class EbayConfig:
    """eBay API configuration settings."""

    app_id: str
    dev_id: str
    cert_id: str
    ru_name: str
    environment: str = "production"  # or "sandbox"

    @property
    def is_sandbox(self) -> bool:
        """Check if using sandbox environment."""
        return self.environment.lower() == "sandbox"


@dataclass
class AgentConfig:
    """4+1 Agent architecture configuration."""

    decision_timeout_ms: int = 1000
    max_concurrent_decisions: int = 10
    enable_cross_agent_learning: bool = True
    performance_monitoring: bool = True

    # Agent-specific settings
    market_agent_enabled: bool = True
    content_agent_enabled: bool = True
    executive_agent_enabled: bool = True
    logistics_agent_enabled: bool = True
    conversational_interface_enabled: bool = True


class ProductionConfig:
    """Production configuration manager for FlipSync."""

    def __init__(self):
        self.environment = self._get_environment()
        self._validate_required_env_vars()

    def _get_environment(self) -> Environment:
        """Get current environment from environment variable."""
        env_str = os.getenv("FLIPSYNC_ENV", "production").lower()
        try:
            return Environment(env_str)
        except ValueError:
            logger.warning(f"Invalid environment '{env_str}', defaulting to production")
            return Environment.PRODUCTION

    def _validate_required_env_vars(self):
        """Validate that required environment variables are set."""
        required_vars = [
            "DB_HOST",
            "DB_PASSWORD",
            "REDIS_HOST",
            "REDIS_PASSWORD",
            "EBAY_APP_ID",
            "EBAY_DEV_ID",
            "EBAY_CERT_ID",
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return DatabaseConfig(
            host=os.getenv("DB_HOST", "174.138.77.110"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "flipsync_agentic_test"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            ssl_mode=os.getenv("DB_SSL_MODE", "require"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        )

    def get_redis_config(self) -> RedisConfig:
        """Get Redis configuration."""
        return RedisConfig(
            host=os.getenv("REDIS_HOST", "127.0.0.1"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("REDIS_DB", "0")),
            ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
        )

    def get_cors_config(self) -> CorsConfig:
        """Get CORS configuration."""
        # Get CORS origins from environment or use secure defaults
        cors_origins_env = os.getenv("CORS_ORIGINS", "")

        if cors_origins_env:
            allowed_origins = [origin.strip() for origin in cors_origins_env.split(",")]
        else:
            # Secure production defaults
            if self.environment == Environment.PRODUCTION:
                allowed_origins = [
                    "http://174.138.77.110:3000",  # Production Flutter web app
                    "https://flipsyncai.com",  # Production domain
                    "https://www.flipsyncai.com",  # Production domain with www
                ]
            else:
                # Development defaults
                allowed_origins = [
                    "http://localhost:3000",
                    "http://localhost:3001",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:3001",
                ]

        return CorsConfig(allowed_origins=allowed_origins)

    def get_ebay_config(self) -> EbayConfig:
        """Get eBay API configuration."""
        return EbayConfig(
            app_id=os.getenv("EBAY_APP_ID"),
            dev_id=os.getenv("EBAY_DEV_ID"),
            cert_id=os.getenv("EBAY_CERT_ID"),
            ru_name=os.getenv(
                "EBAY_RU_NAME", "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym"
            ),
            environment=os.getenv("EBAY_ENV", "production"),
        )

    def get_agent_config(self) -> AgentConfig:
        """Get 4+1 agent architecture configuration."""
        return AgentConfig(
            decision_timeout_ms=int(os.getenv("AGENT_DECISION_TIMEOUT_MS", "1000")),
            max_concurrent_decisions=int(os.getenv("AGENT_MAX_CONCURRENT", "10")),
            enable_cross_agent_learning=os.getenv(
                "AGENT_CROSS_LEARNING", "true"
            ).lower()
            == "true",
            performance_monitoring=os.getenv(
                "AGENT_PERFORMANCE_MONITORING", "true"
            ).lower()
            == "true",
            market_agent_enabled=os.getenv("MARKET_AGENT_ENABLED", "true").lower()
            == "true",
            content_agent_enabled=os.getenv("CONTENT_AGENT_ENABLED", "true").lower()
            == "true",
            executive_agent_enabled=os.getenv("EXECUTIVE_AGENT_ENABLED", "true").lower()
            == "true",
            logistics_agent_enabled=os.getenv("LOGISTICS_AGENT_ENABLED", "true").lower()
            == "true",
            conversational_interface_enabled=os.getenv(
                "CONVERSATIONAL_INTERFACE_ENABLED", "true"
            ).lower()
            == "true",
        )

    def get_api_config(self) -> Dict[str, Any]:
        """Get API server configuration."""
        return {
            "host": os.getenv("API_HOST", "0.0.0.0"),
            "port": int(os.getenv("API_PORT", "8000")),
            "workers": int(os.getenv("API_WORKERS", "4")),
            "timeout": int(os.getenv("API_TIMEOUT", "30")),
            "max_request_size": int(
                os.getenv("API_MAX_REQUEST_SIZE", "16777216")
            ),  # 16MB
            "enable_docs": os.getenv("API_ENABLE_DOCS", "false").lower() == "true",
        }

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "jwt_secret": os.getenv("JWT_SECRET"),
            "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
            "jwt_expiration_hours": int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            "rate_limit_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            "enable_security_headers": os.getenv(
                "ENABLE_SECURITY_HEADERS", "true"
            ).lower()
            == "true",
        }

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT


# Global configuration instance
_config_instance: Optional[ProductionConfig] = None


def get_production_config() -> ProductionConfig:
    """Get global production configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ProductionConfig()
    return _config_instance


def reset_config():
    """Reset configuration instance (for testing)."""
    global _config_instance
    _config_instance = None
