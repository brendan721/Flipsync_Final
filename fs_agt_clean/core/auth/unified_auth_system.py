"""
Unified Authentication System for FlipSync Agentic System
========================================================

Consolidates all authentication systems into a single, database-backed JWT approach
that works seamlessly with the autonomous agent architecture.
"""

import asyncio
import logging
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# from fs_agt_clean.core.db.database import Database
# Using optional import to avoid dependency issues
try:
    from fs_agt_clean.core.db.database import Database as DatabaseService
except ImportError:
    DatabaseService = None

logger = logging.getLogger(__name__)


@dataclass
class AuthUser:
    """Unified user representation."""

    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


@dataclass
class AuthToken:
    """JWT token representation."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user_id: str


class UnifiedAuthSystem:
    """Unified authentication system for FlipSync."""

    def __init__(self, database_service: Optional[DatabaseService] = None):
        self.database = database_service
        # FIXED: Use consistent JWT secret logic across all authentication components
        import os

        # SECURITY: JWT secret must always come from environment
        self.jwt_secret = os.getenv("JWT_SECRET")
        if not self.jwt_secret:
            environment = os.getenv("ENVIRONMENT", "").lower()
            if environment in ("development", "dev", "test"):
                logger.warning(
                    "Using insecure JWT secret for development - set JWT_SECRET environment variable"
                )
                self.jwt_secret = "development-jwt-secret-not-for-production-use"
            else:
                raise ValueError(
                    "JWT_SECRET environment variable must be set for production"
                )
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 30
        self.is_initialized = False

        # Test users for development/testing - passwords from environment
        test_password = os.getenv("TEST_USER_PASSWORD", "SecurePassword!")
        admin_password = os.getenv("ADMIN_USER_PASSWORD", "AdminPassword123!")

        self.test_users = {
            "test@example.com": {
                "password_hash": self._hash_password(test_password),
                "user_id": "test_user_001",
                "username": "testuser",
                "roles": ["user", "tester"],
                "permissions": ["read", "write", "test"],
                "is_active": True,
            },
            "admin@flipsync.com": {
                "password_hash": self._hash_password(admin_password),
                "user_id": "admin_user_001",
                "username": "admin",
                "roles": ["admin", "user"],
                "permissions": ["read", "write", "admin", "manage_agents"],
                "is_active": True,
            },
        }

        logger.info("Unified authentication system initialized")

    async def initialize(self) -> bool:
        """Initialize the authentication system."""
        try:
            if self.database:
                # Ensure user tables exist
                await self._ensure_user_tables()

                # Create test users in database if they don't exist
                await self._create_test_users()

            self.is_initialized = True
            logger.info("✅ Unified authentication system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize authentication system: {e}")
            return False

    async def authenticate_user(self, email: str, password: str) -> Optional[AuthUser]:
        """Authenticate user with email and password."""
        try:
            # Try database first if available
            if self.database and self.is_initialized:
                user_data = await self._authenticate_from_database(email, password)
                if user_data:
                    return self._create_auth_user(user_data)

            # Fallback to test users
            if email in self.test_users:
                user_data = self.test_users[email]
                if self._verify_password(password, user_data["password_hash"]):
                    return AuthUser(
                        user_id=user_data["user_id"],
                        username=user_data["username"],
                        email=email,
                        roles=user_data["roles"],
                        permissions=user_data["permissions"],
                        is_active=user_data["is_active"],
                        created_at=datetime.now(timezone.utc),
                    )

            logger.warning(f"Authentication failed for user: {email}")
            return None

        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None

    async def create_tokens(self, user: AuthUser) -> AuthToken:
        """Create JWT access and refresh tokens for user."""
        try:
            # Access token payload
            access_payload = {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "roles": user.roles,
                "permissions": user.permissions,
                "token_type": "access",
                "exp": datetime.utcnow()
                + timedelta(minutes=self.access_token_expire_minutes),
                "iat": datetime.utcnow(),
            }

            # Refresh token payload
            refresh_payload = {
                "user_id": user.user_id,
                "token_type": "refresh",
                "exp": datetime.utcnow()
                + timedelta(days=self.refresh_token_expire_days),
                "iat": datetime.utcnow(),
            }

            # Generate tokens
            access_token = jwt.encode(
                access_payload, self.jwt_secret, algorithm=self.jwt_algorithm
            )
            refresh_token = jwt.encode(
                refresh_payload, self.jwt_secret, algorithm=self.jwt_algorithm
            )

            # Update last login
            if self.database and self.is_initialized:
                await self._update_last_login(user.user_id)

            return AuthToken(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="Bearer",
                expires_in=self.access_token_expire_minutes * 60,
                user_id=user.user_id,
            )

        except Exception as e:
            logger.error(f"Token creation error for user {user.user_id}: {e}")
            raise

    async def verify_token(self, token: str) -> Optional[AuthUser]:
        """Verify and decode JWT token, returning an AuthUser object."""
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            # Check token type (handle both token_type and scope for backward compatibility)
            token_type = payload.get("token_type") or payload.get("scope")
            if token_type not in ("access", "access_token"):
                return None

            # Extract user information from token payload
            user_id = payload.get("sub") or payload.get("user_id")
            if not user_id:
                return None

            # Check if user is still active
            if user_id and self.database and self.is_initialized:
                is_active = await self._check_user_active(user_id)
                if not is_active:
                    return None

            # Create AuthUser dataclass from token payload
            return AuthUser(
                user_id=user_id,
                username=payload.get("username", ""),
                email=payload.get("email", ""),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                is_active=True,
                created_at=datetime.now(timezone.utc),
                last_login=datetime.now(timezone.utc),
            )

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[AuthToken]:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(
                refresh_token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            if payload.get("token_type") != "refresh":
                return None

            user_id = payload.get("user_id")
            if not user_id:
                return None

            # Get user data
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                return None

            # Create new tokens
            return await self.create_tokens(user)

        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID."""
        try:
            # Try database first
            if self.database and self.is_initialized:
                user_data = await self._get_user_from_database(user_id)
                if user_data:
                    return self._create_auth_user(user_data)

            # Fallback to test users
            for email, user_data in self.test_users.items():
                if user_data["user_id"] == user_id:
                    return AuthUser(
                        user_id=user_data["user_id"],
                        username=user_data["username"],
                        email=email,
                        roles=user_data["roles"],
                        permissions=user_data["permissions"],
                        is_active=user_data["is_active"],
                        created_at=datetime.now(timezone.utc),
                    )

            return None

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def check_permission(
        self, user_permissions: List[str], required_permission: str
    ) -> bool:
        """Check if user has required permission."""
        return required_permission in user_permissions or "admin" in user_permissions

    def check_role(self, user_roles: List[str], required_role: str) -> bool:
        """Check if user has required role."""
        return required_role in user_roles or "admin" in user_roles

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    async def _ensure_user_tables(self):
        """Ensure user tables exist in database."""
        if not self.database:
            return

        create_users_table = """
        CREATE TABLE IF NOT EXISTS auth_users (
            user_id VARCHAR(50) PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            roles TEXT[] DEFAULT '{}',
            permissions TEXT[] DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE
        );
        """

        await self.database.execute_query(create_users_table)
        logger.info("User tables ensured in database")

    async def _create_test_users(self):
        """Create test users in database."""
        if not self.database:
            return

        for email, user_data in self.test_users.items():
            insert_query = """
            INSERT INTO auth_users (user_id, username, email, password_hash, roles, permissions, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (email) DO NOTHING;
            """

            await self.database.execute_query(
                insert_query,
                user_data["user_id"],
                user_data["username"],
                email,
                user_data["password_hash"],
                user_data["roles"],
                user_data["permissions"],
                user_data["is_active"],
            )

        logger.info("Test users created in database")

    async def _authenticate_from_database(
        self, email: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user from database."""
        if not self.database:
            return None

        query = "SELECT * FROM auth_users WHERE email = $1 AND is_active = TRUE;"
        result = await self.database.fetch_one(query, email)

        if result:
            # Safely extract password hash
            password_hash = None
            if isinstance(result, dict):
                password_hash = result.get("password_hash")
            elif hasattr(result, "password_hash"):
                password_hash = result.password_hash
            elif hasattr(result, "__getitem__"):
                try:
                    password_hash = result["password_hash"]
                except (KeyError, TypeError):
                    pass

            if password_hash and self._verify_password(password, password_hash):
                # Ensure we return a dictionary
                if isinstance(result, dict):
                    return result
                else:
                    # Convert to dict if it's not already
                    try:
                        return dict(result)
                    except (TypeError, ValueError):
                        # Manual conversion for SQLAlchemy Row objects
                        if hasattr(result, "_mapping"):
                            return dict(result._mapping)
                        elif hasattr(result, "keys") and callable(result.keys):
                            return {
                                key: getattr(result, key, None) for key in result.keys()
                            }
                        else:
                            # Last resort: create dict from known attributes
                            return {
                                "user_id": getattr(
                                    result, "user_id", getattr(result, "id", None)
                                ),
                                "email": getattr(result, "email", None),
                                "username": getattr(result, "username", None),
                                "password_hash": password_hash,
                                "is_active": getattr(result, "is_active", True),
                                "roles": getattr(result, "roles", []),
                                "permissions": getattr(result, "permissions", []),
                                "created_at": getattr(result, "created_at", None),
                                "last_login": getattr(result, "last_login", None),
                            }

        return None

    async def _get_user_from_database(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user from database by ID."""
        if not self.database:
            return None

        query = "SELECT * FROM auth_users WHERE user_id = $1;"
        result = await self.database.fetch_one(query, user_id)

        if result:
            # Ensure we return a dictionary
            if isinstance(result, dict):
                return result
            else:
                # Convert to dict if it's not already
                try:
                    return dict(result)
                except (TypeError, ValueError):
                    # Manual conversion for SQLAlchemy Row objects
                    if hasattr(result, "_mapping"):
                        return dict(result._mapping)
                    elif hasattr(result, "keys") and callable(result.keys):
                        return {
                            key: getattr(result, key, None) for key in result.keys()
                        }
                    else:
                        # Last resort: create dict from known attributes
                        return {
                            "user_id": getattr(
                                result, "user_id", getattr(result, "id", None)
                            ),
                            "email": getattr(result, "email", None),
                            "username": getattr(result, "username", None),
                            "password_hash": getattr(result, "password_hash", None),
                            "is_active": getattr(result, "is_active", True),
                            "roles": getattr(result, "roles", []),
                            "permissions": getattr(result, "permissions", []),
                            "created_at": getattr(result, "created_at", None),
                            "last_login": getattr(result, "last_login", None),
                        }

        return None

    async def _check_user_active(self, user_id: str) -> bool:
        """Check if user is active."""
        if not self.database:
            return True  # Assume active if no database

        query = "SELECT is_active FROM auth_users WHERE user_id = $1;"
        result = await self.database.fetch_one(query, user_id)

        if result:
            # Safely extract is_active value
            if isinstance(result, dict):
                return result.get("is_active", False)
            elif hasattr(result, "is_active"):
                return result.is_active
            elif hasattr(result, "__getitem__"):
                try:
                    return result["is_active"]
                except (KeyError, TypeError):
                    return False

        return False

    async def _update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        if not self.database:
            return

        query = "UPDATE auth_users SET last_login = NOW() WHERE user_id = $1;"
        await self.database.execute_query(query, user_id)

    def _create_auth_user(self, user_data: Dict[str, Any]) -> AuthUser:
        """Create AuthUser from database data."""
        return AuthUser(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            roles=user_data.get("roles", []),
            permissions=user_data.get("permissions", []),
            is_active=user_data.get("is_active", True),
            created_at=user_data.get("created_at", datetime.now(timezone.utc)),
            last_login=user_data.get("last_login"),
        )


# Global unified auth system instance
_unified_auth_system: Optional[UnifiedAuthSystem] = None


def get_unified_auth_system(
    database_service: Optional[DatabaseService] = None,
) -> UnifiedAuthSystem:
    """Get the global unified authentication system instance."""
    global _unified_auth_system
    if _unified_auth_system is None:
        _unified_auth_system = UnifiedAuthSystem(database_service)
    return _unified_auth_system
