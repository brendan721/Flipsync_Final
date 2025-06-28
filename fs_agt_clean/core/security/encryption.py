"""
Encryption handler for FlipSync.

This module provides encryption and decryption functionality for sensitive data
in the FlipSync application. It uses AES-GCM for authenticated encryption and
PBKDF2 for key derivation.
"""

import base64
import hashlib
import logging
import os
from typing import Any, Dict, Optional, TypedDict, Union

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fs_agt_clean.core.config.config_manager import ConfigManager
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EncryptionConfig(BaseModel):
    """Encryption configuration.

    Attributes:
        algorithm: Encryption algorithm to use
        key_size: Size of the encryption key in bytes
        salt_size: Size of the salt in bytes
        iterations: Number of iterations for key derivation
    """

    algorithm: str = "AES-256-GCM"
    key_size: int = 32  # 256 bits
    salt_size: int = 16
    iterations: int = 100000


class EncryptedData(TypedDict):
    """Structure of encrypted data.

    Attributes:
        version: Encryption version
        algorithm: Encryption algorithm
        salt: Base64-encoded salt
        nonce: Base64-encoded nonce
        ciphertext: Base64-encoded ciphertext
        context: Encryption context
    """

    version: str
    algorithm: str
    salt: str
    nonce: str
    ciphertext: str
    context: str


class EncryptionHandler:
    """Handler for encrypting and decrypting data.

    This class provides methods for encrypting and decrypting data using
    AES-GCM with key derivation from a master key.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Create a new instance or return the existing one."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the encryption handler.

        Args:
            config_manager: Optional configuration manager
        """
        if self._initialized:
            return

        self.config_manager = config_manager or ConfigManager()
        self.config = self._load_config()
        self._master_key = None
        self._initialized = True

    def _load_config(self) -> EncryptionConfig:
        """Load encryption configuration from config manager.

        Returns:
            Encryption configuration
        """
        encryption_config = self.config_manager.get_section("encryption") or {}
        return EncryptionConfig(
            algorithm=encryption_config.get("algorithm", "AES-256-GCM"),
            key_size=encryption_config.get("key_size", 32),
            salt_size=encryption_config.get("salt_size", 16),
            iterations=encryption_config.get("iterations", 100000),
        )

    def initialize(self, master_key: Optional[bytes] = None) -> bool:
        """Initialize the encryption handler with a master key.

        Args:
            master_key: Optional master key. If not provided, one will be generated
                or loaded from configuration.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            if master_key:
                self._master_key = master_key
            else:
                # Try to load from config
                key_str = self.config_manager.get("encryption.master_key")
                if key_str:
                    self._master_key = base64.b64decode(key_str)
                else:
                    # Generate new master key
                    self._master_key = os.urandom(self.config.key_size)
                    # Save to config
                    self.config_manager.set(
                        "encryption.master_key",
                        base64.b64encode(self._master_key).decode(),
                    )

            logger.info("Successfully initialized encryption handler")
            return True
        except Exception as e:
            logger.error("Failed to initialize encryption handler: %s", str(e))
            return False

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key from master key.

        Args:
            salt: Salt for key derivation

        Returns:
            Derived key

        Raises:
            RuntimeError: If encryption handler is not initialized
        """
        if not self._master_key:
            raise RuntimeError("Encryption handler not initialized")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.config.key_size,
            salt=salt,
            iterations=self.config.iterations,
        )
        return kdf.derive(self._master_key)

    def encrypt(
        self, data: Union[str, bytes, Dict[str, Any]], context: str = ""
    ) -> EncryptedData:
        """Encrypt data.

        Args:
            data: Data to encrypt
            context: Encryption context (e.g. table name, field name)

        Returns:
            Dictionary containing encrypted data and metadata

        Raises:
            RuntimeError: If encryption handler is not initialized
            ValueError: If data cannot be encrypted
        """
        if not self._master_key:
            raise RuntimeError("Encryption handler not initialized")

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
            elif isinstance(data, bytes):
                plaintext = data
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")

            # Create cipher
            cipher = AESGCM(key)

            # Encrypt data
            context_bytes = context.encode() if context else b""
            ciphertext = cipher.encrypt(nonce, plaintext, context_bytes)

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
            raise ValueError(f"Failed to encrypt data: {str(e)}")

    def decrypt(self, encrypted_data: EncryptedData) -> bytes:
        """Decrypt data.

        Args:
            encrypted_data: Dictionary containing encrypted data and metadata

        Returns:
            Decrypted data as bytes

        Raises:
            RuntimeError: If encryption handler is not initialized
            ValueError: If data cannot be decrypted
        """
        if not self._master_key:
            raise RuntimeError("Encryption handler not initialized")

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
            context_bytes = context.encode() if context else b""
            plaintext = cipher.decrypt(nonce, ciphertext, context_bytes)
            return plaintext

        except Exception as e:
            logger.error("Failed to decrypt data: %s", str(e))
            raise ValueError(f"Failed to decrypt data: {str(e)}")

    def rotate_master_key(self) -> bool:
        """Rotate the master encryption key.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate new master key
            new_master_key = os.urandom(self.config.key_size)

            # Store new key
            self.config_manager.set(
                "encryption.master_key",
                base64.b64encode(new_master_key).decode(),
            )

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

    def hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2.

        Args:
            password: Password to hash

        Returns:
            Base64-encoded password hash
        """
        salt = os.urandom(self.config.salt_size)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.config.iterations,
        )
        password_hash = kdf.derive(password.encode())

        # Combine salt and hash for storage
        combined = salt + password_hash
        return base64.b64encode(combined).decode()

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash.

        Args:
            password: Password to verify
            password_hash: Base64-encoded password hash

        Returns:
            True if password matches hash, False otherwise
        """
        try:
            # Decode hash
            decoded = base64.b64decode(password_hash)

            # Extract salt and hash
            salt = decoded[: self.config.salt_size]
            stored_hash = decoded[self.config.salt_size :]

            # Derive hash from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.config.iterations,
            )
            derived_hash = kdf.derive(password.encode())

            # Compare hashes - use a constant-time comparison
            if len(derived_hash) != len(stored_hash):
                return False

            result = 0
            for a, b in zip(derived_hash, stored_hash):
                result |= a ^ b
            return result == 0
        except Exception as e:
            logger.error("Failed to verify password: %s", str(e))
            return False


# Singleton instance
_encryption_handler_instance = None


def get_encryption_handler() -> EncryptionHandler:
    """Get a singleton instance of the EncryptionHandler.

    Returns:
        EncryptionHandler instance
    """
    global _encryption_handler_instance
    if _encryption_handler_instance is None:
        _encryption_handler_instance = EncryptionHandler()
    return _encryption_handler_instance
