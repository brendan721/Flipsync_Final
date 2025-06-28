"""
Configuration encryption handler for the ConfigManager.

This module provides functionality to encrypt and decrypt sensitive configuration values
using industry-standard encryption algorithms. It supports both transparent encryption
during configuration loading and explicit encryption/decryption of individual values.
"""

import base64
import hashlib
import json
import os
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class ConfigEncryptionHandler:
    """Handles encryption and decryption of configuration values.

    This class provides methods to encrypt and decrypt configuration values,
    as well as to identify and process encrypted values in configuration
    dictionaries. It uses Fernet symmetric encryption for secure storage.
    """

    # Prefix for encrypted values in YAML/JSON
    ENCRYPTED_PREFIX = "!encrypted:"

    # Default key file location (relative to config directory)
    DEFAULT_KEY_FILE = ".config_encryption_key"

    def __init__(
        self,
        key: Optional[Union[str, bytes]] = None,
        key_file: Optional[Union[str, Path]] = None,
        password: Optional[str] = None,
        salt: Optional[bytes] = None,
    ):
        """Initialize the encryption handler.

        Args:
            key: Encryption key as string or bytes. If not provided, will attempt to load from key_file.
            key_file: Path to file containing encryption key. If not provided, will use default location.
            password: Password to derive encryption key. Used if key and key_file are not provided.
            salt: Salt for password-based key derivation. Used only with password.
        """
        self._key = None
        self._fernet = None

        # Try to get key in order of precedence
        if key:
            self._set_key(key)
        elif key_file:
            self._load_key_from_file(key_file)
        elif password:
            self._derive_key_from_password(password, salt)

        # If no key is available, encryption/decryption will raise exceptions

    def encrypt(self, value: Any) -> str:
        """Encrypt a value.

        Args:
            value: The value to encrypt. Non-string values will be JSON serialized.

        Returns:
            A string with the encrypted value prefixed with ENCRYPTED_PREFIX.

        Raises:
            ValueError: If encryption key is not available.
        """
        if not self._fernet:
            raise ValueError(
                "Encryption key not available. Set key, key_file, or password."
            )

        # Serialize non-string values
        if not isinstance(value, str):
            value = json.dumps(value)

        # Encrypt and encode
        encrypted_bytes = self._fernet.encrypt(value.encode("utf-8"))
        encoded = base64.urlsafe_b64encode(encrypted_bytes).decode("ascii")

        return f"{self.ENCRYPTED_PREFIX}{encoded}"

    def decrypt(self, value: str) -> Any:
        """Decrypt an encrypted value.

        Args:
            value: The encrypted string to decrypt (including prefix).

        Returns:
            The decrypted value, converted from JSON if it was a non-string value.

        Raises:
            ValueError: If the value is not encrypted or key is not available.
        """
        if not self._fernet:
            raise ValueError(
                "Encryption key not available. Set key, key_file, or password."
            )

        if not self.is_encrypted(value):
            raise ValueError(
                f"Value is not encrypted with prefix {self.ENCRYPTED_PREFIX}"
            )

        # Strip prefix and decode
        encrypted_part = value[len(self.ENCRYPTED_PREFIX) :]
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_part.encode("ascii"))

        # Decrypt
        decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
        decrypted = decrypted_bytes.decode("utf-8")

        # Try to parse as JSON if it looks like JSON
        try:
            if decrypted.startswith("{") or decrypted.startswith("["):
                return json.loads(decrypted)
        except json.JSONDecodeError:
            pass

        return decrypted

    def is_encrypted(self, value: Any) -> bool:
        """Check if a value is encrypted.

        Args:
            value: The value to check.

        Returns:
            True if the value is encrypted, False otherwise.
        """
        return isinstance(value, str) and value.startswith(self.ENCRYPTED_PREFIX)

    def decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively decrypt all encrypted values in a configuration.

        Args:
            config: The configuration dictionary to process.

        Returns:
            A new dictionary with all encrypted values decrypted.
        """
        if not config:
            return {}

        result = {}

        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self.decrypt_config(value)
            elif isinstance(value, list):
                result[key] = [
                    (
                        self.decrypt_config(item)
                        if isinstance(item, dict)
                        else self.decrypt(item) if self.is_encrypted(item) else item
                    )
                    for item in value
                ]
            elif self.is_encrypted(value):
                result[key] = self.decrypt(value)
            else:
                result[key] = value

        return result

    def encrypt_config(
        self, config: Dict[str, Any], sensitive_keys: List[str]
    ) -> Dict[str, Any]:
        """Recursively encrypt sensitive values in a configuration.

        Args:
            config: The configuration dictionary to process.
            sensitive_keys: List of key names (or patterns) to encrypt.

        Returns:
            A new dictionary with sensitive values encrypted.
        """
        if not config:
            return {}

        result = {}

        for key, value in config.items():
            # For dictionaries, recursively process
            if isinstance(value, dict):
                result[key] = self.encrypt_config(value, sensitive_keys)
            # For lists, process each item
            elif isinstance(value, list):
                result[key] = [
                    (
                        self.encrypt_config(item, sensitive_keys)
                        if isinstance(item, dict)
                        else (
                            self.encrypt(item)
                            if key in sensitive_keys and not self.is_encrypted(item)
                            else item
                        )
                    )
                    for item in value
                ]
            # For scalar values, encrypt if key matches sensitive pattern
            elif key in sensitive_keys and not self.is_encrypted(value):
                result[key] = self.encrypt(value)
            # Otherwise, keep as is
            else:
                result[key] = value

        return result

    def generate_key(self) -> bytes:
        """Generate a new random encryption key.

        Returns:
            A new Fernet key as bytes.
        """
        key = Fernet.generate_key()
        self._set_key(key)
        return key

    def save_key_to_file(self, key_file: Union[str, Path]) -> None:
        """Save the current encryption key to a file.

        Args:
            key_file: Path to save the key to.

        Raises:
            ValueError: If no key is available.
        """
        if not self._key:
            raise ValueError("No encryption key available to save.")

        key_path = Path(key_file)
        key_path.parent.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions on the file
        with open(key_path, "wb") as f:
            f.write(self._key)

        # Try to set file permissions to be secure (0600)
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            # On some platforms this may fail, log a warning
            print(f"Warning: Could not set secure permissions on key file {key_path}")

    def _set_key(self, key: Union[str, bytes]) -> None:
        """Set the encryption key.

        Args:
            key: The key as string or bytes.
        """
        if isinstance(key, str):
            key = key.encode("utf-8")

        # If it's not a valid Fernet key, derive one
        if len(key) != 32 or not all(32 <= b <= 126 for b in key[:8]):
            key = self._derive_key_from_bytes(key)

        self._key = key
        self._fernet = Fernet(base64.urlsafe_b64encode(key))

    def _load_key_from_file(self, key_file: Union[str, Path]) -> None:
        """Load encryption key from a file.

        Args:
            key_file: Path to the key file.

        Raises:
            FileNotFoundError: If the key file does not exist.
        """
        key_path = Path(key_file)

        if not key_path.exists():
            raise FileNotFoundError(f"Encryption key file not found: {key_path}")

        with open(key_path, "rb") as f:
            key = f.read().strip()

        self._set_key(key)

    def _derive_key_from_password(
        self, password: str, salt: Optional[bytes] = None
    ) -> bytes:
        """Derive an encryption key from a password using PBKDF2.

        Args:
            password: The password to derive key from.
            salt: Optional salt for key derivation. If not provided, a default salt is used.

        Returns:
            The derived key as bytes.
        """
        if not salt:
            # Use a fixed salt by default for reproducibility
            salt = b"FlipSyncConfigEncryption"

        # Use PBKDF2 to derive a secure key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = kdf.derive(password.encode("utf-8"))
        self._set_key(key)
        return key

    def _derive_key_from_bytes(self, data: bytes) -> bytes:
        """Derive a 32-byte key from arbitrary bytes using SHA-256.

        Args:
            data: Bytes to derive key from.

        Returns:
            A 32-byte key.
        """
        return hashlib.sha256(data).digest()


def find_sensitive_keys(
    config: Dict[str, Any], patterns: List[str] = None
) -> List[str]:
    """Find potentially sensitive keys in a configuration.

    Args:
        config: The configuration dictionary to scan.
        patterns: List of patterns to identify sensitive keys. If not provided,
                 a default list of common sensitive key names is used.

    Returns:
        List of keys that match sensitive patterns.
    """
    if patterns is None:
        patterns = [
            "password",
            "secret",
            "key",
            "token",
            "credential",
            "auth",
            "private",
            "certificate",
            "access_key",
            "api_key",
        ]

    sensitive_keys = []

    def scan_dict(d: Dict[str, Any], path: str = ""):
        for key, value in d.items():
            current_path = f"{path}.{key}" if path else key

            # Check if key matches any sensitive pattern
            if any(pattern.lower() in key.lower() for pattern in patterns):
                sensitive_keys.append(current_path)

            # Recursively scan nested dictionaries
            if isinstance(value, dict):
                scan_dict(value, current_path)

    scan_dict(config)
    return sensitive_keys
