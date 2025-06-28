"""
Vault client for HashiCorp Vault integration.

This module provides a client for interacting with HashiCorp Vault.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Optional HashiCorp Vault client
try:
    import hvac

    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False
    hvac = None

logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Configuration for Vault client."""

    url: str = "http://localhost:8200"
    token: Optional[str] = None
    mount_point: str = "secret"
    development_mode: bool = True
    timeout: int = 30
    verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> "VaultConfig":
        """Create VaultConfig from environment variables."""
        return cls(
            url=os.environ.get("VAULT_ADDR", "http://localhost:8200"),
            token=os.environ.get("VAULT_TOKEN"),
            mount_point=os.environ.get("VAULT_MOUNT_POINT", "secret"),
            development_mode=os.environ.get("ENVIRONMENT", "development")
            == "development",
            timeout=int(os.environ.get("VAULT_TIMEOUT", "30")),
            verify_ssl=os.environ.get("VAULT_VERIFY_SSL", "true").lower() == "true",
        )


class VaultClient:
    """Client for HashiCorp Vault."""

    def __init__(self, config: VaultConfig):
        """Initialize Vault client.

        Args:
            config: Vault configuration
        """
        self.config = config
        self.client = None
        self._initialized = False

        # Development fallback secrets
        self.dev_secrets = {
            "jwt_secret": "dev_jwt_secret_key_do_not_use_in_production",
            "encryption_key": "dev_encryption_key_do_not_use_in_production",
        }

    async def initialize(self) -> bool:
        """Initialize the Vault client.

        Returns:
            True if initialization was successful
        """
        if self._initialized:
            return True

        if not HVAC_AVAILABLE:
            logger.warning("HVAC not available - Vault functionality will be limited")
            if self.config.development_mode:
                logger.info("Running in development mode - using fallback secrets")
                self._initialized = True
                return True
            return False

        try:
            self.client = hvac.Client(
                url=self.config.url,
                token=self.config.token,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )

            # Test authentication if token is provided
            if self.config.token and not self.client.is_authenticated():
                logger.error("Vault authentication failed")
                if self.config.development_mode:
                    logger.warning("Falling back to development mode")
                    self._initialized = True
                    return True
                return False

            self._initialized = True
            logger.info("Vault client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing Vault client: {str(e)}")
            if self.config.development_mode:
                logger.warning("Falling back to development mode")
                self._initialized = True
                return True
            return False

    async def get_secret(self, secret_name: str, version: Optional[int] = None) -> Any:
        """Get a secret from Vault.

        Args:
            secret_name: Name of the secret
            version: Version of the secret

        Returns:
            Secret value
        """
        if not self._initialized:
            await self.initialize()

        # In development mode or if client is not available, use fallback secrets
        if self.config.development_mode or not self.client:
            if secret_name in self.dev_secrets:
                logger.warning(
                    f"Using development fallback for secret {secret_name}. "
                    "This should not be used in production!"
                )
                return self.dev_secrets[secret_name]
            return None

        try:
            # Check if client is authenticated
            if not self.client.is_authenticated():
                logger.error("Vault client is not authenticated")
                return None

            # Get secret from Vault
            if version:
                secret = self.client.secrets.kv.v2.read_secret_version(
                    path=secret_name,
                    version=version,
                    mount_point=self.config.mount_point,
                )
            else:
                secret = self.client.secrets.kv.v2.read_secret_version(
                    path=secret_name,
                    mount_point=self.config.mount_point,
                )

            # Extract data
            if secret and "data" in secret and "data" in secret["data"]:
                return secret["data"]["data"]

            logger.warning(f"Secret {secret_name} not found")
            return None

        except Exception as e:
            logger.error(f"Error getting secret {secret_name}: {str(e)}")
            return None

    async def set_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """Set a secret in Vault.

        Args:
            secret_name: Name of the secret
            secret_value: Value of the secret

        Returns:
            True if successful
        """
        if not self._initialized:
            await self.initialize()

        # In development mode, just log the operation
        if self.config.development_mode or not self.client:
            logger.info(f"Development mode: would set secret {secret_name}")
            return True

        try:
            # Check if client is authenticated
            if not self.client.is_authenticated():
                logger.error("Vault client is not authenticated")
                return False

            # Set secret in Vault
            self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_name,
                secret=secret_value,
                mount_point=self.config.mount_point,
            )

            logger.debug(f"Set secret {secret_name}")
            return True

        except Exception as e:
            logger.error(f"Error setting secret {secret_name}: {str(e)}")
            return False

    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.

        Returns:
            True if authenticated
        """
        if self.config.development_mode:
            return True

        if not self.client:
            return False

        try:
            return self.client.is_authenticated()
        except Exception:
            return False

    async def close(self):
        """Close the Vault client."""
        if self.client:
            # HVAC client doesn't have an explicit close method
            self.client = None
        self._initialized = False
