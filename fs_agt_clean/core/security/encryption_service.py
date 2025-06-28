"""Data encryption service for encrypting data at rest."""

import base64
import os
from typing import Any, Dict, Optional, TypedDict, Union

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, ConfigDict

from fs_agt_clean.core.utils.logging import get_logger
from fs_agt_clean.core.vault.vault_client import VaultClient

logger = get_logger(__name__)


class EncryptionConfig(BaseModel):
    """Encryption configuration."""

    algorithm: str = "AES-256-GCM"
    key_size: int = 32  # 256 bits
    salt_size: int = 16
    iterations: int = 100000


class EncryptedData(TypedDict):
    """Structure of encrypted data."""

    version: str
    algorithm: str
    salt: str
    nonce: str
    ciphertext: str
    context: str


class VaultSecretData(TypedDict, total=False):
    """Structure of vault secret data."""

    value: str


class EncryptionService:
    """Service for encrypting data at rest."""

    def __init__(
        self, vault_client: VaultClient, config: Optional[EncryptionConfig] = None
    ):
        """Initialize encryption service.

        Args:
            vault_client: Vault client for storing encryption keys
            config: Optional encryption configuration
        """
        self.vault_client = vault_client
        self.config = config or EncryptionConfig()
        self._master_key: Optional[bytes] = None

    async def initialize(self):
        """Initialize encryption service."""
        try:
            # Get or generate master key
            key_data = await self.vault_client.read_secret("encryption/master_key")
            if key_data and "value" in key_data:
                self._master_key = base64.b64decode(str(key_data["value"]))
            else:
                # Generate new master key
                self._master_key = os.urandom(self.config.key_size)
                secret_data: VaultSecretData = {
                    "value": base64.b64encode(self._master_key).decode()
                }
                await self.vault_client.write_secret(
                    "encryption/master_key", secret_data
                )

            logger.info("Successfully initialized encryption service")
        except Exception as e:
            logger.error("Failed to initialize encryption service: %s", str(e))
            raise

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key from master key.

        Args:
            salt: Salt for key derivation

        Returns:
            Derived key
        """
        if not self._master_key:
            raise RuntimeError("Encryption service not initialized")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.config.key_size,
            salt=salt,
            iterations=self.config.iterations,
        )
        return kdf.derive(self._master_key)

    async def encrypt(
        self, data: Union[str, bytes, Dict[str, Any]], context: str
    ) -> EncryptedData:
        """Encrypt data.

        Args:
            data: Data to encrypt
            context: Encryption context (e.g. table name, field name)

        Returns:
            Dictionary containing encrypted data and metadata
        """
        try:
            # Generate salt and nonce
            salt = os.urandom(self.config.salt_size)
            nonce = os.urandom(12)  # 96 bits as required by AES-GCM

            # Derive key
            key = self._derive_key(salt)

            # Convert data to bytes
            if isinstance(data, str):
                plaintext = data.encode()
            elif isinstance(data, dict):
                plaintext = str(data).encode()
            else:
                plaintext = data

            # Create cipher
            cipher = AESGCM(key)

            # Encrypt data
            ciphertext = cipher.encrypt(nonce, plaintext, context.encode())

            # Encode for storage
            return EncryptedData(
                version="1",
                algorithm=self.config.algorithm,
                salt=base64.b64encode(salt).decode(),
                nonce=base64.b64encode(nonce).decode(),
                ciphertext=base64.b64encode(ciphertext).decode(),
                context=context,
            )

        except Exception as e:
            logger.error("Failed to encrypt data: %s", str(e))
            raise

    async def decrypt(self, encrypted_data: EncryptedData) -> bytes:
        """Decrypt data.

        Args:
            encrypted_data: Dictionary containing encrypted data and metadata

        Returns:
            Decrypted data as bytes
        """
        try:
            # Validate version and algorithm
            if encrypted_data["version"] != "1":
                raise ValueError("Unsupported encryption version")
            if encrypted_data["algorithm"] != self.config.algorithm:
                raise ValueError("Unsupported encryption algorithm")

            # Decode components
            salt = base64.b64decode(encrypted_data["salt"])
            nonce = base64.b64decode(encrypted_data["nonce"])
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            context = encrypted_data["context"]

            # Derive key
            key = self._derive_key(salt)

            # Create cipher
            cipher = AESGCM(key)

            # Decrypt data
            plaintext = cipher.decrypt(nonce, ciphertext, context.encode())
            return plaintext

        except Exception as e:
            logger.error("Failed to decrypt data: %s", str(e))
            raise

    async def rotate_master_key(self) -> bool:
        """Rotate the master encryption key.

        Returns:
            bool: True if successful
        """
        try:
            # Generate new master key
            new_master_key = os.urandom(self.config.key_size)

            # Store new key with version
            secret_data: VaultSecretData = {
                "value": base64.b64encode(new_master_key).decode()
            }
            await self.vault_client.write_secret("encryption/master_key", secret_data)

            # Update current key
            self._master_key = new_master_key

            logger.info("Successfully rotated master encryption key")
            return True

        except Exception as e:
            logger.error("Failed to rotate master encryption key: %s", str(e))
            return False

    def get_config(self) -> EncryptionConfig:
        """Get current encryption configuration.

        Returns:
            Current encryption configuration
        """
        return self.config
