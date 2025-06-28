"""
Secret management using HashiCorp Vault.

This module provides functionality for storing and retrieving secrets from
HashiCorp Vault.
"""

import logging
import os
from typing import Any, Dict, Optional

# Optional HashiCorp Vault client
try:
    import hvac

    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False
    hvac = None

logger = logging.getLogger(__name__)


class VaultSecretManager:
    """Secret manager using HashiCorp Vault."""

    def __init__(
        self,
        vault_url: Optional[str] = None,
        vault_token: Optional[str] = None,
        mount_point: str = "secret",
    ):
        """Initialize the Vault secret manager.

        Args:
            vault_url: Vault server URL
            vault_token: Vault authentication token
            mount_point: Vault mount point
        """
        self.vault_url = vault_url or os.environ.get(
            "VAULT_ADDR", "http://localhost:8200"
        )
        self.vault_token = vault_token or os.environ.get("VAULT_TOKEN")
        self.mount_point = mount_point

        # Initialize Vault client
        if HVAC_AVAILABLE:
            self.client = hvac.Client(url=self.vault_url, token=self.vault_token)
        else:
            self.client = None
            logger.warning("HVAC not available - Vault functionality will be limited")

        # Check if we're using a development environment
        self.is_dev = os.environ.get("ENVIRONMENT", "development") == "development"

        # Development fallback secrets
        self.dev_secrets = {
            "jwt_secret": "dev_jwt_secret_key_do_not_use_in_production",
            "encryption_key": "dev_encryption_key_do_not_use_in_production",
        }

    async def get_secret(self, secret_name: str, version: Optional[int] = None) -> Any:
        """Get a secret from Vault.

        Args:
            secret_name: Name of the secret
            version: Version of the secret

        Returns:
            Any: Secret value
        """
        try:
            # In development, use fallback secrets
            if self.is_dev and secret_name in self.dev_secrets:
                logger.warning(
                    f"Using development fallback for secret {secret_name}. "
                    "This should not be used in production!"
                )
                return self.dev_secrets[secret_name]

            # Check if client is available and authenticated
            if not self.client or not self.client.is_authenticated():
                logger.error("Vault client is not available or not authenticated")
                # Fall back to dev secrets if available
                if self.is_dev and secret_name in self.dev_secrets:
                    logger.warning(
                        f"Using development fallback for secret {secret_name}"
                    )
                    return self.dev_secrets[secret_name]
                return None

            # Get secret from Vault
            if version:
                secret = self.client.secrets.kv.v2.read_secret_version(
                    path=secret_name,
                    version=version,
                    mount_point=self.mount_point,
                )
            else:
                secret = self.client.secrets.kv.v2.read_secret_version(
                    path=secret_name,
                    mount_point=self.mount_point,
                )

            # Extract data
            if secret and "data" in secret and "data" in secret["data"]:
                return secret["data"]["data"]

            logger.warning(f"Secret {secret_name} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting secret {secret_name}: {str(e)}")

            # In development, use fallback secrets as a last resort
            if self.is_dev and secret_name in self.dev_secrets:
                logger.warning(
                    f"Using development fallback for secret {secret_name} after error. "
                    "This should not be used in production!"
                )
                return self.dev_secrets[secret_name]

            return None

    async def set_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """Set a secret in Vault.

        Args:
            secret_name: Name of the secret
            secret_value: Value of the secret

        Returns:
            bool: True if successful
        """
        try:
            # Check if client is authenticated
            if not self.client.is_authenticated():
                logger.error("Vault client is not authenticated")
                return False

            # Set secret in Vault
            self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_name,
                secret=secret_value,
                mount_point=self.mount_point,
            )

            logger.debug(f"Set secret {secret_name}")
            return True
        except Exception as e:
            logger.error(f"Error setting secret {secret_name}: {str(e)}")
            return False

    async def delete_secret(self, secret_name: str) -> bool:
        """Delete a secret from Vault.

        Args:
            secret_name: Name of the secret

        Returns:
            bool: True if successful
        """
        try:
            # Check if client is authenticated
            if not self.client.is_authenticated():
                logger.error("Vault client is not authenticated")
                return False

            # Delete secret from Vault
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=secret_name,
                mount_point=self.mount_point,
            )

            logger.debug(f"Deleted secret {secret_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting secret {secret_name}: {str(e)}")
            return False
