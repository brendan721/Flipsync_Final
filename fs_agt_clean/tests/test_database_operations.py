#!/usr/bin/env python3
"""
Comprehensive Database Operations Tests for FlipSync
AGENT_CONTEXT: Test suite for database models, repositories, and operations
AGENT_PRIORITY: Ensure data integrity, performance, and reliability
AGENT_PATTERN: Async database testing, transaction management, comprehensive coverage
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fs_agt_clean.core.db.auth_repository import AuthRepository

# AGENT_INSTRUCTION: Import FlipSync database components
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.database.models.unified_user import UnifiedUnifiedUser, Permission, Role
from fs_agt_clean.database.repositories.market_repository import MarketRepository


class TestDatabaseConnection:
    """
    AGENT_CONTEXT: Test database connection and session management
    AGENT_CAPABILITY: Connection pooling, session lifecycle, error handling
    """

    @pytest.fixture
    def mock_database_url(self):
        """Mock database URL for testing"""
        return "postgresql+asyncpg://test:test@localhost:5432/test_flipsync"

    @pytest.mark.asyncio
    async def test_database_initialization(self, mock_database_url):
        """Test database initialization"""
        with patch("fs_agt_clean.core.db.database.create_async_engine") as mock_engine:
            mock_engine.return_value = AsyncMock()

            db = Database(mock_database_url)

            assert db.database_url == mock_database_url
            mock_engine.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_management(self, mock_database_url):
        """Test database session creation and management"""
        with patch("fs_agt_clean.core.db.database.create_async_engine") as mock_engine:
            mock_engine_instance = AsyncMock()
            mock_engine.return_value = mock_engine_instance

            db = Database(mock_database_url)

            # Test session context manager
            async with db.get_session() as session:
                assert session is not None
                # Session should be properly configured
                assert hasattr(session, "execute")
                assert hasattr(session, "commit")
                assert hasattr(session, "rollback")

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_database_url):
        """Test database connection error handling"""
        with patch("fs_agt_clean.core.db.database.create_async_engine") as mock_engine:
            mock_engine.side_effect = Exception("Connection failed")

            with pytest.raises(Exception) as exc_info:
                Database(mock_database_url)

            assert "Connection failed" in str(exc_info.value)


class TestUnifiedUnifiedUserModel:
    """
    AGENT_CONTEXT: Test UnifiedUnifiedUser model operations
    AGENT_CAPABILITY: UnifiedUser creation, password management, token generation
    """

    def test_user_creation(self):
        """Test creating a new user"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com",
            username="testuser",
            password="TestPassword123!",
            first_name="Test",
            last_name="UnifiedUser",
        )

        assert user.email == "test@flipsync.com"
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "UnifiedUser"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.hashed_password != "TestPassword123!"  # Should be hashed

    def test_password_hashing_and_verification(self):
        """Test password hashing and verification"""
        password = "SecurePassword123!"
        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password=password
        )

        # Password should be hashed
        assert user.hashed_password != password
        assert len(user.hashed_password) > 50

        # Verification should work
        assert user.verify_password(password) is True
        assert user.verify_password("WrongPassword") is False

    def test_email_verification_workflow(self):
        """Test email verification token generation and validation"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="TestPassword123!"
        )

        # Generate verification token
        token = user.generate_verification_token()
        assert token is not None
        assert len(token) > 20
        assert user.email_verification_token == token
        assert user.email_verification_expires is not None

        # Validate token
        assert user.is_verification_token_valid(token) is True
        assert user.is_verification_token_valid("invalid_token") is False

        # Verify email
        user.verify_email()
        assert user.is_verified is True
        assert user.email_verification_token is None

    def test_password_reset_workflow(self):
        """Test password reset token generation and validation"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="OldPassword123!"
        )

        # Generate reset token
        reset_token = user.generate_password_reset_token()
        assert reset_token is not None
        assert user.password_reset_token == reset_token
        assert user.password_reset_expires is not None

        # Validate token
        assert user.is_password_reset_token_valid(reset_token) is True

        # Reset password
        user.set_password("NewPassword456!")
        assert user.verify_password("NewPassword456!") is True
        assert user.verify_password("OldPassword123!") is False

    def test_login_attempt_tracking(self):
        """Test login attempt tracking and account locking"""
        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="TestPassword123!"
        )

        # Initial state
        assert user.failed_login_attempts == 0
        assert user.is_locked() is False

        # Failed attempts
        for i in range(5):
            user.update_login_failure()
            if i < 4:
                assert user.is_locked() is False

        # Should be locked after 5 failures
        assert user.failed_login_attempts == 5
        assert user.is_locked() is True

        # Successful login resets counter
        user.update_login_success()
        assert user.failed_login_attempts == 0
        assert user.is_locked() is False
        assert user.last_login is not None


class TestAuthRepository:
    """
    AGENT_CONTEXT: Test authentication repository operations
    AGENT_CAPABILITY: UnifiedUser CRUD, authentication, role management
    """

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.mark.asyncio
    async def test_create_user(self, mock_session):
        """Test user creation through repository"""
        repo = AuthRepository(mock_session)

        user = await repo.create_user(
            email="newuser@flipsync.com",
            username="newuser",
            password="NewPassword123!",
            first_name="New",
            last_name="UnifiedUser",
        )

        assert user.email == "newuser@flipsync.com"
        assert user.username == "newuser"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, mock_session):
        """Test retrieving user by email"""
        repo = AuthRepository(mock_session)

        # Mock user
        mock_user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="TestPassword123!"
        )

        # Mock query result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        user = await repo.get_user_by_email("test@flipsync.com")

        assert user == mock_user
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user(self, mock_session):
        """Test user authentication through repository"""
        repo = AuthRepository(mock_session)

        # Mock user with correct password
        mock_user = UnifiedUnifiedUser(
            email="test@flipsync.com",
            username="testuser",
            password="CorrectPassword123!",
        )

        # Mock query result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        # Test successful authentication
        success, user = await repo.authenticate_user(
            "test@flipsync.com", "CorrectPassword123!"
        )

        assert success is True
        assert user == mock_user

        # Test failed authentication
        success, user = await repo.authenticate_user(
            "test@flipsync.com", "WrongPassword"
        )

        assert success is False
        assert user is None

    @pytest.mark.asyncio
    async def test_update_last_login(self, mock_session):
        """Test updating user's last login timestamp"""
        repo = AuthRepository(mock_session)

        user = UnifiedUnifiedUser(
            email="test@flipsync.com", username="testuser", password="TestPassword123!"
        )

        old_last_login = user.last_login
        await repo.update_last_login(user)

        assert user.last_login != old_last_login
        assert user.last_login is not None
        mock_session.commit.assert_called_once()


class TestMarketRepository:
    """
    AGENT_CONTEXT: Test market repository operations
    AGENT_CAPABILITY: Product management, pricing, competitive analysis
    """

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.mark.asyncio
    async def test_create_product(self, mock_session):
        """Test product creation through market repository"""
        repo = MarketRepository()

        # Mock product identifier
        from fs_agt_clean.core.models.marketplace_models import (
            MarketplaceType,
            ProductIdentifier,
        )

        product_id = ProductIdentifier(
            asin="B123456789", sku="TEST-SKU-001", internal_id="PROD-001"
        )

        with patch(
            "fs_agt_clean.database.repositories.market_repository.ProductModel"
        ) as mock_model:
            mock_product = MagicMock()
            mock_model.return_value = mock_product

            result = await repo.create_product(
                session=mock_session,
                product_id=product_id,
                title="Test Product",
                marketplace=MarketplaceType.AMAZON,
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()


if __name__ == "__main__":
    # AGENT_CONTEXT: Standalone test execution
    pytest.main([__file__, "-v"])
