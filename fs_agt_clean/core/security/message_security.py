"""Message validation and encryption utilities for secure agent communication."""

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from fs_agt_clean.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class MessageSecurity:
    """Message security utilities for validation and encryption."""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        encryption_key: Optional[str] = None,
        hmac_algorithm: str = "sha256",
        encryption_algorithm: str = "AES-256-CBC",
    ):
        """Initialize message security.

        Args:
            secret_key: Secret key for HMAC validation (generated if not provided)
            encryption_key: Key for message encryption (generated if not provided)
            hmac_algorithm: HMAC algorithm to use
            encryption_algorithm: Encryption algorithm to use
        """
        self.secret_key = secret_key or self._generate_key()
        self.encryption_key = encryption_key or self._generate_key()
        self.hmac_algorithm = hmac_algorithm
        self.encryption_algorithm = encryption_algorithm

    def _generate_key(self, length: int = 32) -> str:
        """Generate a random key.

        Args:
            length: Key length in bytes

        Returns:
            Base64-encoded key
        """
        return base64.b64encode(os.urandom(length)).decode("utf-8")

    def validate_message(
        self,
        message: Dict[str, Any],
        signature: str,
    ) -> bool:
        """Validate a message using HMAC.

        Args:
            message: Message to validate
            signature: HMAC signature to verify

        Returns:
            True if the message is valid, False otherwise
        """
        # Convert message to canonical JSON string
        message_json = json.dumps(message, sort_keys=True)

        # Calculate HMAC
        key = base64.b64decode(self.secret_key)
        h = hmac.new(
            key, message_json.encode("utf-8"), getattr(hashlib, self.hmac_algorithm)
        )
        calculated_signature = base64.b64encode(h.digest()).decode("utf-8")

        # Compare signatures using constant-time comparison
        return hmac.compare_digest(calculated_signature, signature)

    def sign_message(self, message: Dict[str, Any]) -> str:
        """Sign a message using HMAC.

        Args:
            message: Message to sign

        Returns:
            HMAC signature
        """
        # Convert message to canonical JSON string
        message_json = json.dumps(message, sort_keys=True)

        # Calculate HMAC
        key = base64.b64decode(self.secret_key)
        h = hmac.new(
            key, message_json.encode("utf-8"), getattr(hashlib, self.hmac_algorithm)
        )
        return base64.b64encode(h.digest()).decode("utf-8")

    def encrypt_message(
        self,
        message: Dict[str, Any],
    ) -> Dict[str, str]:
        """Encrypt a message.

        Args:
            message: Message to encrypt

        Returns:
            Dictionary with encrypted message and metadata
        """
        # Convert message to JSON string
        message_json = json.dumps(message)

        # Generate initialization vector
        iv = os.urandom(16)

        # Derive encryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=iv,
            iterations=100000,
            backend=default_backend(),
        )
        key = kdf.derive(base64.b64decode(self.encryption_key))

        # Pad the message
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(message_json.encode("utf-8")) + padder.finalize()

        # Encrypt the message
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # Create encrypted message
        encrypted_message = {
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
            "iv": base64.b64encode(iv).decode("utf-8"),
            "algorithm": self.encryption_algorithm,
            "timestamp": int(time.time()),
        }

        # Sign the encrypted message
        encrypted_message["signature"] = self.sign_message(encrypted_message)

        return encrypted_message

    def decrypt_message(
        self,
        encrypted_message: Dict[str, str],
    ) -> Dict[str, Any]:
        """Decrypt a message.

        Args:
            encrypted_message: Encrypted message to decrypt

        Returns:
            Decrypted message

        Raises:
            ValidationError: If the message signature is invalid
        """
        # Verify signature
        signature = encrypted_message.pop("signature", "")
        if not self.validate_message(encrypted_message, signature):
            raise ValidationError("Invalid message signature")

        # Extract ciphertext and IV
        ciphertext = base64.b64decode(encrypted_message["ciphertext"])
        iv = base64.b64decode(encrypted_message["iv"])

        # Derive decryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=iv,
            iterations=100000,
            backend=default_backend(),
        )
        key = kdf.derive(base64.b64decode(self.encryption_key))

        # Decrypt the message
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Unpad the message
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()

        # Parse JSON
        return json.loads(data.decode("utf-8"))

    def create_secure_message(
        self,
        message: Dict[str, Any],
        encrypt: bool = True,
    ) -> Dict[str, Any]:
        """Create a secure message with validation and optional encryption.

        Args:
            message: Message to secure
            encrypt: Whether to encrypt the message

        Returns:
            Secure message
        """
        # Add timestamp and message ID if not present
        if "timestamp" not in message:
            message["timestamp"] = int(time.time())

        if "message_id" not in message:
            message["message_id"] = base64.b64encode(os.urandom(16)).decode("utf-8")

        if encrypt:
            # Encrypt the message
            secure_message = {
                "encrypted": True,
                "payload": self.encrypt_message(message),
            }
        else:
            # Sign the message
            signature = self.sign_message(message)
            secure_message = {
                "encrypted": False,
                "payload": message,
                "signature": signature,
            }

        return secure_message

    def verify_and_extract_message(
        self,
        secure_message: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Verify and extract a secure message.

        Args:
            secure_message: Secure message to verify and extract

        Returns:
            Extracted message

        Raises:
            ValidationError: If the message is invalid
        """
        if secure_message.get("encrypted", False):
            # Decrypt the message
            return self.decrypt_message(secure_message["payload"])
        else:
            # Verify the message signature
            payload = secure_message["payload"]
            signature = secure_message["signature"]

            if not self.validate_message(payload, signature):
                raise ValidationError("Invalid message signature")

            return payload


class MessageValidator:
    """Validator for agent messages."""

    def validate_event_message(
        self, message: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate an event message.

        Args:
            message: Message to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        required_fields = ["id", "type", "source", "data", "timestamp"]
        for field in required_fields:
            if field not in message:
                return False, f"Missing required field: {field}"

        # Validate field types
        if not isinstance(message["id"], str):
            return False, "Field 'id' must be a string"

        if not isinstance(message["type"], str):
            return False, "Field 'type' must be a string"

        if not isinstance(message["source"], str):
            return False, "Field 'source' must be a string"

        if not isinstance(message["data"], dict):
            return False, "Field 'data' must be a dictionary"

        # Validate timestamp format
        try:
            if isinstance(message["timestamp"], str):
                # Try to parse ISO format
                import datetime

                datetime.datetime.fromisoformat(
                    message["timestamp"].replace("Z", "+00:00")
                )
            elif not isinstance(message["timestamp"], (int, float)):
                return (
                    False,
                    "Field 'timestamp' must be a string in ISO format or a number",
                )
        except ValueError:
            return False, "Invalid timestamp format"

        return True, None

    def validate_command_message(
        self, message: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate a command message.

        Args:
            message: Message to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # First validate as event message
        is_valid, error = self.validate_event_message(message)
        if not is_valid:
            return is_valid, error

        # Check command-specific fields
        if message["type"] != "COMMAND_RECEIVED":
            return False, "Command message must have type 'COMMAND_RECEIVED'"

        if "target" not in message:
            return False, "Command message must have a 'target' field"

        if not isinstance(message["target"], str):
            return False, "Field 'target' must be a string"

        if "command" not in message["data"]:
            return False, "Command message must have a 'command' field in data"

        return True, None

    def validate_acknowledgment_message(
        self, message: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate an acknowledgment message.

        Args:
            message: Message to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # First validate as event message
        is_valid, error = self.validate_event_message(message)
        if not is_valid:
            return is_valid, error

        # Check acknowledgment-specific fields
        if message["type"] != "COMMAND_COMPLETED":
            return False, "Acknowledgment message must have type 'COMMAND_COMPLETED'"

        if "target" not in message:
            return False, "Acknowledgment message must have a 'target' field"

        if "original_event_id" not in message["data"]:
            return (
                False,
                "Acknowledgment message must have an 'original_event_id' field in data",
            )

        if "status" not in message["data"]:
            return False, "Acknowledgment message must have a 'status' field in data"

        return True, None
