"""
mfa_verification.py - FALLBACK MIGRATION

This file was migrated as part of the Flipsync clean-up project.
WARNING: This is a fallback migration due to issues with the automated migration.
"""

"""
MFA Verification Implementation

This module provides functionality for verifying MFA codes, including:
1. TOTP verification
2. SMS verification
3. Email verification
4. Backup code verification
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from fs_agt_clean.core.auth.mfa import MFAService
from fs_agt_clean.core.utils.logging import get_logger

logger = get_logger(__name__)


class MfaVerificationType(str, Enum):
    """MFA verification types."""

    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP = "backup"


class MfaVerificationStatus(str, Enum):
    """MFA verification status."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class MfaVerificationRequest(BaseModel):
    """MFA verification request."""

    user_id: str = Field(..., description="UnifiedUser ID")
    verification_type: MfaVerificationType = Field(..., description="Verification type")
    code: str = Field(..., description="Verification code")
    session_id: Optional[str] = Field(None, description="Session ID")


class MfaVerificationResponse(BaseModel):
    """MFA verification response."""

    success: bool = Field(..., description="Whether verification was successful")
    message: str = Field(..., description="Message describing the result")
    remaining_attempts: Optional[int] = Field(
        None, description="Remaining verification attempts"
    )
    locked_until: Optional[datetime] = Field(
        None, description="Time until account is unlocked"
    )
    verification_type: MfaVerificationType = Field(..., description="Verification type")
    user_id: str = Field(..., description="UnifiedUser ID")


class MfaVerificationManager:
    """
    Manager for MFA verification.

    This class provides methods for verifying MFA codes and managing
    verification attempts.
    """

    def __init__(
        self,
        mfa_service: MFAService,
        max_verification_attempts: int = 5,
        lockout_duration: int = 1800,  # 30 minutes
        verification_expiry: int = 300,  # 5 minutes
    ):
        """
        Initialize the MFA verification manager.

        Args:
            mfa_service: MFA service for TOTP and backup code operations
            max_verification_attempts: Maximum number of verification attempts
            lockout_duration: Duration of lockout in seconds
            verification_expiry: Expiry time for verification codes in seconds
        """
        self.mfa_service = mfa_service
        self.max_verification_attempts = max_verification_attempts
        self.lockout_duration = lockout_duration
        self.verification_expiry = verification_expiry

        # Store verification attempts
        self._verification_attempts: Dict[str, int] = {}
        self._lockout_times: Dict[str, datetime] = {}

        # Store verification codes
        self._verification_codes: Dict[str, Dict[str, Union[str, datetime]]] = {}

        logger.info("MFA verification manager initialized")

    def generate_verification_code(
        self, user_id: str, verification_type: MfaVerificationType
    ) -> str:
        """
        Generate a verification code for a user.

        Args:
            user_id: UnifiedUser ID
            verification_type: Verification type

        Returns:
            Verification code
        """
        import random
        import string

        # Generate a random code
        if (
            verification_type == MfaVerificationType.SMS
            or verification_type == MfaVerificationType.EMAIL
        ):
            # Generate a 6-digit code for SMS/Email
            code = "".join(random.choices(string.digits, k=6))
        else:
            # For other types, use a longer alphanumeric code
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

        # Store the code with expiration time
        self._verification_codes[f"{user_id}:{verification_type}"] = {
            "code": code,
            "expires_at": datetime.utcnow()
            + timedelta(seconds=self.verification_expiry),
        }

        return code

    def verify_code(
        self,
        user_id: str,
        verification_type: MfaVerificationType,
        code: str,
        totp_secret: Optional[str] = None,
    ) -> MfaVerificationResponse:
        """
        Verify a verification code.

        Args:
            user_id: UnifiedUser ID
            verification_type: Verification type
            code: Verification code
            totp_secret: TOTP secret (required for TOTP verification)

        Returns:
            Verification response
        """
        # Check if user is locked out
        if user_id in self._lockout_times:
            lockout_time = self._lockout_times[user_id]
            if datetime.utcnow() < lockout_time:
                return MfaVerificationResponse(
                    success=False,
                    message="Account is locked due to too many failed attempts",
                    locked_until=lockout_time,
                    verification_type=verification_type,
                    user_id=user_id,
                )
            else:
                # Lockout period has expired
                del self._lockout_times[user_id]
                self._verification_attempts[user_id] = 0

        # Initialize verification attempts if not exists
        if user_id not in self._verification_attempts:
            self._verification_attempts[user_id] = 0

        # Check verification attempts
        attempts = self._verification_attempts[user_id]
        if attempts >= self.max_verification_attempts:
            # Lock the account
            lockout_time = datetime.utcnow() + timedelta(seconds=self.lockout_duration)
            self._lockout_times[user_id] = lockout_time

            return MfaVerificationResponse(
                success=False,
                message="Too many failed attempts. Account is locked.",
                remaining_attempts=0,
                locked_until=lockout_time,
                verification_type=verification_type,
                user_id=user_id,
            )

        # Verify based on verification type
        success = False
        if verification_type == MfaVerificationType.TOTP:
            if not totp_secret:
                return MfaVerificationResponse(
                    success=False,
                    message="TOTP secret is required for TOTP verification",
                    remaining_attempts=self.max_verification_attempts - attempts,
                    verification_type=verification_type,
                    user_id=user_id,
                )

            success = self.mfa_service.verify_totp(totp_secret, code)
        elif (
            verification_type == MfaVerificationType.SMS
            or verification_type == MfaVerificationType.EMAIL
        ):
            # Get stored code
            key = f"{user_id}:{verification_type}"
            if key not in self._verification_codes:
                return MfaVerificationResponse(
                    success=False,
                    message=f"No {verification_type} verification code found",
                    remaining_attempts=self.max_verification_attempts - attempts,
                    verification_type=verification_type,
                    user_id=user_id,
                )

            stored_code_data = self._verification_codes[key]
            stored_code = stored_code_data["code"]
            expires_at = stored_code_data["expires_at"]

            # Check if code is expired
            if datetime.utcnow() > expires_at:
                # Remove expired code
                del self._verification_codes[key]

                return MfaVerificationResponse(
                    success=False,
                    message=f"{verification_type.value.upper()} verification code has expired",
                    remaining_attempts=self.max_verification_attempts - attempts,
                    verification_type=verification_type,
                    user_id=user_id,
                )

            # Verify code
            success = stored_code == code

            # Remove used code if successful
            if success:
                del self._verification_codes[key]
        elif verification_type == MfaVerificationType.BACKUP:
            # In a real implementation, you would verify against stored backup codes
            # For now, we'll just use a placeholder
            success = code == "BACKUP123"

        if success:
            # Reset verification attempts
            self._verification_attempts[user_id] = 0

            return MfaVerificationResponse(
                success=True,
                message=f"{verification_type.value.upper()} code verified successfully",
                remaining_attempts=self.max_verification_attempts,
                verification_type=verification_type,
                user_id=user_id,
            )
        else:
            # Increment verification attempts
            self._verification_attempts[user_id] += 1

            remaining_attempts = (
                self.max_verification_attempts - self._verification_attempts[user_id]
            )

            return MfaVerificationResponse(
                success=False,
                message=f"Invalid {verification_type.value.upper()} code",
                remaining_attempts=remaining_attempts,
                verification_type=verification_type,
                user_id=user_id,
            )

    def cleanup_expired_codes(self) -> int:
        """
        Clean up expired verification codes.

        Returns:
            Number of codes removed
        """
        now = datetime.utcnow()
        expired_keys = [
            key
            for key, data in self._verification_codes.items()
            if now > data["expires_at"]
        ]

        # Remove expired codes
        for key in expired_keys:
            del self._verification_codes[key]

        return len(expired_keys)

    def reset_verification_attempts(self, user_id: str) -> None:
        """
        Reset verification attempts for a user.

        Args:
            user_id: UnifiedUser ID
        """
        if user_id in self._verification_attempts:
            del self._verification_attempts[user_id]

        if user_id in self._lockout_times:
            del self._lockout_times[user_id]
