#!/usr/bin/env python3
"""
Comprehensive Authentication System Tests for FlipSync
AGENT_CONTEXT: Test suite for authentication models, repositories, and endpoints
AGENT_PRIORITY: Ensure authentication system reliability and security
AGENT_PATTERN: Async testing with pytest-asyncio, comprehensive coverage
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import bcrypt
import pytest

from fs_agt_clean.core.db.auth_repository import AuthRepository

# AGENT_INSTRUCTION: Import authentication components
from fs_agt_clean.database.models.unified_user import UnifiedUnifiedUser, Permission, Role
from fs_agt_clean.database.init_auth_db import DatabaseInitializer


class TestUnifiedUnifiedUser:
    """
    AGENT_CONTEXT: Test UnifiedUnifiedUser model functionality
    AGENT_CAPABILITY: Password hashing, verification, token generation
    """

    def test_user_creation_with_password_hashing(self):
        """Test user creation automatically hashes password"""
        password = "TestPassword123!"
        user = UnifiedUnifiedUser(
            email="test@flipsync.com",
            username="testuser",
            password=password,
            first_name="Test",
            last_name="UnifiedUser",
        )

        # Password should be hashed, not stored in plain text
        assert user.hashed_password != password
        assert len(user.hashed_password) > 50  # Bcrypt hashes are long
        assert user.verify_password(password) is True
        assert user.verify_password("wrongpassword") is False

    def test_password_verification(self):
        """Test password verification functionality"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com",
            username="testuser",
            password="CorrectPassword123!",
        )

        assert user.verify_password("CorrectPassword123!") is True
        assert user.verify_password("WrongPassword") is False
        assert user.verify_password("") is False
        assert user.verify_password("correctpassword123!") is False  # Case sensitive

    def test_password_change(self):
        """Test password change functionality"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="OldPassword123!"
        )

        old_hash = user.hashed_password
        user.set_password("NewPassword456!")

        # Hash should change
        assert user.hashed_password != old_hash
        assert user.verify_password("NewPassword456!") is True
        assert user.verify_password("OldPassword123!") is False

    def test_email_verification_token_generation(self):
        """Test email verification token generation"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="TestPassword123!"
        )

        token = user.generate_verification_token()

        assert token is not None
        assert len(token) > 20  # URL-safe tokens are reasonably long
        assert user.email_verification_token == token
        assert user.email_verification_expires is not None
        assert user.is_verification_token_valid(token) is True
        assert user.is_verification_token_valid("invalid_token") is False

    def test_password_reset_token_generation(self):
        """Test password reset token generation"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="TestPassword123!"
        )

        token = user.generate_password_reset_token()

        assert token is not None
        assert len(token) > 20
        assert user.password_reset_token == token
        assert user.password_reset_expires is not None
        assert user.is_password_reset_token_valid(token) is True
        assert user.is_password_reset_token_valid("invalid_token") is False

    def test_email_verification_process(self):
        """Test complete email verification process"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="TestPassword123!"
        )

        # Initially not verified
        assert user.is_verified is False

        # Generate verification token
        token = user.generate_verification_token()
        assert user.is_verification_token_valid(token) is True

        # Verify email
        user.verify_email()
        assert user.is_verified is True
        assert user.email_verification_token is None
        assert user.email_verification_expires is None

    def test_login_tracking(self):
        """Test login success and failure tracking"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="TestPassword123!"
        )

        # Initial state
        assert user.failed_login_attempts == 0
        assert user.last_login is None
        assert user.is_locked() is False

        # Failed login attempts
        user.update_login_failure()
        assert user.failed_login_attempts == 1
        assert user.is_locked() is False

        # Multiple failures
        for _ in range(4):
            user.update_login_failure()

        assert user.failed_login_attempts == 5
        assert user.is_locked() is True

        # Successful login resets counter
        user.update_login_success()
        assert user.failed_login_attempts == 0
        assert user.last_login is not None
        assert user.is_locked() is False


class TestRole:
    """Test Role model functionality"""

    def test_role_creation(self):
        """Test role creation"""
        role = Role()
        role.name = "admin"
        role.description = "System administrator"

        assert role.name == "admin"
        assert role.description == "System administrator"
        assert role.id is not None  # UUID should be generated


class TestPermission:
    """Test Permission model functionality"""

    def test_permission_creation(self):
        """Test permission creation"""
        permission = Permission()
        permission.name = "users.read"
        permission.description = "Read user information"
        permission.resource = "users"
        permission.action = "read"

        assert permission.name == "users.read"
        assert permission.resource == "users"
        assert permission.action == "read"


@pytest.mark.asyncio
class TestDatabaseInitializer:
    """
    AGENT_CONTEXT: Test database initialization functionality
    AGENT_CAPABILITY: Table creation, default data seeding
    """

    @patch("fs_agt_clean.database.init_auth_db.create_async_engine")
    @patch("fs_agt_clean.database.init_auth_db.sessionmaker")
    async def test_database_initializer_creation(self, mock_sessionmaker, mock_engine):
        """Test DatabaseInitializer creation"""
        mock_engine.return_value = AsyncMock()
        mock_sessionmaker.return_value = AsyncMock()

        initializer = DatabaseInitializer(
            "postgresql+asyncpg://test:test@localhost/test"
        )

        assert (
            initializer.database_url == "postgresql+asyncpg://test:test@localhost/test"
        )
        mock_engine.assert_called_once()
        mock_sessionmaker.assert_called_once()

    @patch("fs_agt_clean.database.init_auth_db.create_async_engine")
    async def test_create_tables(self, mock_engine):
        """Test table creation"""
        mock_engine_instance = AsyncMock()
        mock_engine.return_value = mock_engine_instance
        mock_conn = AsyncMock()
        mock_engine_instance.begin.return_value.__aenter__.return_value = mock_conn

        initializer = DatabaseInitializer()
        await initializer.create_tables()

        mock_conn.run_sync.assert_called_once()


@pytest.mark.asyncio
class TestAuthRepository:
    """
    AGENT_CONTEXT: Test authentication repository functionality
    AGENT_CAPABILITY: UnifiedUser CRUD operations, authentication logic
    """

    @patch("fs_agt_clean.core.db.auth_repository.AsyncSession")
    async def test_create_user(self, mock_session):
        """Test user creation through repository"""
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        repo = AuthRepository(mock_session)

        user_data = {
            "email": "test@flipsync.com",
            "username": "testuser",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "UnifiedUser",
        }

        result = await repo.create_user(user_data)

        mock_session_instance.add.assert_called_once()
        mock_session_instance.commit.assert_called_once()
        assert result is not None

    @patch("fs_agt_clean.core.db.auth_repository.AsyncSession")
    async def test_get_user_by_email(self, mock_session):
        """Test getting user by email"""
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        # Mock user
        mock_user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="TestPassword123!"
        )
        mock_session_instance.execute.return_value.scalar_one_or_none.return_value = (
            mock_user
        )

        repo = AuthRepository(mock_session)
        result = await repo.get_user_by_email("test@flipsync.com")

        assert result == mock_user
        mock_session_instance.execute.assert_called_once()


class TestAuthenticationIntegration:
    """
    AGENT_CONTEXT: Integration tests for complete authentication flow
    AGENT_CAPABILITY: End-to-end authentication testing
    """

    def test_complete_user_registration_flow(self):
        """Test complete user registration process"""
        # Create user
        user = UnifiedUnifiedUser(
            email="newuser@flipsync.com",
            username="newuser",
            password="SecurePassword123!",
            first_name="New",
            last_name="UnifiedUser",
        )

        # UnifiedUser should be created but not verified
        assert user.is_verified is False
        assert user.is_active is True

        # Generate verification token
        token = user.generate_verification_token()
        assert token is not None

        # Verify email
        user.verify_email()
        assert user.is_verified is True

        # UnifiedUser should now be fully active
        assert user.is_active is True
        assert user.is_verified is True

    def test_complete_login_flow(self):
        """Test complete login process"""
        user = UnifiedUnifiedUser(
            email="loginuser@flipsync.com",
            username="loginuser",
            password="LoginPassword123!",
        )
        user.verify_email()  # Simulate verified user

        # Successful login
        assert user.verify_password("LoginPassword123!") is True
        user.update_login_success()

        assert user.last_login is not None
        assert user.failed_login_attempts == 0

        # Failed login attempts
        assert user.verify_password("WrongPassword") is False
        user.update_login_failure()
        assert user.failed_login_attempts == 1

    def test_password_reset_flow(self):
        """Test complete password reset process"""
        user = UnifiedUnifiedUser(
            email="resetuser@flipsync.com",
            username="resetuser",
            password="OldPassword123!",
        )

        # Generate reset token
        reset_token = user.generate_password_reset_token()
        assert user.is_password_reset_token_valid(reset_token) is True

        # Reset password
        user.set_password("NewPassword456!")

        # Old password should not work
        assert user.verify_password("OldPassword123!") is False
        # New password should work
        assert user.verify_password("NewPassword456!") is True


# AGENT_INSTRUCTION: Test configuration and fixtures
@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return UnifiedUnifiedUser(
        email="sample@flipsync.com",
        username="sampleuser",
        password="SamplePassword123!",
        first_name="Sample",
        last_name="UnifiedUser",
    )


@pytest.fixture
def admin_role():
    """Create an admin role for testing"""
    role = Role()
    role.name = "admin"
    role.description = "System administrator"
    return role


@pytest.fixture
def user_permission():
    """Create a user permission for testing"""
    permission = Permission()
    permission.name = "users.read"
    permission.description = "Read user information"
    permission.resource = "users"
    permission.action = "read"
    return permission


if __name__ == "__main__":
    # AGENT_CONTEXT: Standalone test execution
    pytest.main([__file__, "-v"])
