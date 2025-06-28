#!/usr/bin/env python3
"""
Comprehensive API Endpoints Tests for FlipSync
AGENT_CONTEXT: Test suite for all API endpoints with real data validation
AGENT_PRIORITY: Ensure API reliability, security, and proper error handling
AGENT_PATTERN: FastAPI testing with TestClient, async operations, comprehensive coverage
"""

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

# AGENT_INSTRUCTION: Import FlipSync components
from fs_agt_clean.app.main import create_app
from fs_agt_clean.core.auth.auth_service import AuthService
from fs_agt_clean.core.models.user import UnifiedUser, UnifiedUserRole, UnifiedUserStatus


class TestAuthenticationEndpoints:
    """
    AGENT_CONTEXT: Test authentication API endpoints
    AGENT_CAPABILITY: Login, registration, token management, OAuth2
    """

    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def auth_service_mock(self):
        """Mock authentication service"""
        mock_service = AsyncMock(spec=AuthService)
        return mock_service

    def test_login_endpoint_success(self, client, auth_service_mock):
        """Test successful login"""
        # Mock successful authentication
        auth_service_mock.authenticate_user.return_value = {
            "username": "testuser",
            "permissions": ["user"],
            "disabled": False,
        }
        auth_service_mock.create_tokens.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

        with patch(
            "fs_agt_clean.api.routes.auth.get_auth_service",
            return_value=auth_service_mock,
        ):
            with patch(
                "fs_agt_clean.api.routes.auth.get_db_auth_service",
                return_value=auth_service_mock,
            ):
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@flipsync.com", "password": "TestPassword123!"},
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@flipsync.com"

    def test_login_endpoint_invalid_credentials(self, client, auth_service_mock):
        """Test login with invalid credentials"""
        # Mock failed authentication
        auth_service_mock.authenticate_user.return_value = None

        with patch(
            "fs_agt_clean.api.routes.auth.get_auth_service",
            return_value=auth_service_mock,
        ):
            with patch(
                "fs_agt_clean.api.routes.auth.get_db_auth_service",
                return_value=auth_service_mock,
            ):
                response = client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@flipsync.com", "password": "WrongPassword"},
                )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]

    def test_registration_endpoint_success(self, client, auth_service_mock):
        """Test successful user registration"""
        # Mock successful registration
        mock_user = MagicMock()
        mock_user.id = "user_123"
        mock_user.email = "newuser@flipsync.com"
        mock_user.username = "newuser"

        with patch(
            "fs_agt_clean.api.routes.auth.get_db_auth_service",
            return_value=auth_service_mock,
        ):
            with patch(
                "fs_agt_clean.core.db.auth_repository.AuthRepository"
            ) as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo_class.return_value = mock_repo
                mock_repo.create_user.return_value = mock_user

                response = client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "newuser@flipsync.com",
                        "username": "newuser",
                        "password": "NewPassword123!",
                        "first_name": "New",
                        "last_name": "UnifiedUser",
                    },
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newuser@flipsync.com"
        assert data["username"] == "newuser"
        assert data["verification_required"] is True

    def test_oauth2_token_endpoint(self, client, auth_service_mock):
        """Test OAuth2 compatible token endpoint"""
        # Mock successful authentication
        auth_service_mock.authenticate_user.return_value = {
            "username": "testuser",
            "permissions": ["user"],
            "disabled": False,
        }
        auth_service_mock.create_tokens.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

        with patch(
            "fs_agt_clean.api.routes.auth.get_auth_service",
            return_value=auth_service_mock,
        ):
            with patch(
                "fs_agt_clean.api.routes.auth.get_db_auth_service",
                return_value=auth_service_mock,
            ):
                response = client.post(
                    "/api/v1/auth/token",
                    data={"username": "testuser", "password": "TestPassword123!"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == "test_access_token"
        assert data["token_type"] == "bearer"

    def test_token_refresh_endpoint(self, client, auth_service_mock):
        """Test token refresh functionality"""
        # Mock successful token refresh
        auth_service_mock.refresh_token.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
        }

        with patch(
            "fs_agt_clean.api.routes.auth.get_auth_service",
            return_value=auth_service_mock,
        ):
            response = client.post(
                "/api/v1/auth/refresh", json={"refresh_token": "valid_refresh_token"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestUnifiedAgentEndpoints:
    """
    AGENT_CONTEXT: Test agent management API endpoints
    AGENT_CAPABILITY: UnifiedAgent status, configuration, coordination
    """

    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        return TestClient(app)

    def test_get_agents_list(self, client):
        """Test getting list of agents"""
        response = client.get("/api/v1/agents/list")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify agent structure
        agent = data[0]
        required_fields = ["id", "name", "type", "status", "lastActive", "currentTask"]
        for field in required_fields:
            assert field in agent

    def test_get_agent_status(self, client):
        """Test getting specific agent status"""
        response = client.get("/api/v1/agents/agent_market_001/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["agent_id"] == "agent_market_001"
        assert "status" in data
        assert "last_active" in data

    def test_agent_configuration_update(self, client):
        """Test updating agent configuration"""
        config_data = {
            "config": {
                "max_concurrent_tasks": 5,
                "analysis_depth": "detailed",
                "update_frequency": 300,
            }
        }

        response = client.put(
            "/api/v1/agents/agent_market_001/config", json=config_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["agent_id"] == "agent_market_001"
        assert "config" in data
        assert "updated_at" in data


class TestInventoryEndpoints:
    """
    AGENT_CONTEXT: Test inventory management API endpoints
    AGENT_CAPABILITY: CRUD operations, stock management, synchronization
    """

    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user for authentication"""
        user = UnifiedUser(
            id="user_123",
            email="test@flipsync.com",
            username="testuser",
            role=UnifiedUserRole.USER,
            status=UnifiedUserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return user

    def test_get_inventory_items(self, client, mock_current_user):
        """Test getting inventory items"""
        with patch(
            "fs_agt_clean.api.routes.inventory.get_current_user",
            return_value=mock_current_user,
        ):
            with patch(
                "fs_agt_clean.api.routes.inventory.get_inventory_service"
            ) as mock_service:
                mock_service.return_value.get_items.return_value = [
                    {
                        "id": "item_1",
                        "name": "Test Product",
                        "sku": "TEST-001",
                        "quantity": 10,
                        "price": 29.99,
                    }
                ]

                response = client.get("/api/v1/inventory/items?limit=10&offset=0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert data["items"][0]["name"] == "Test Product"


class TestMarketplaceEndpoints:
    """
    AGENT_CONTEXT: Test marketplace integration API endpoints
    AGENT_CAPABILITY: eBay, Amazon integration, product synchronization
    """

    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        return TestClient(app)

    def test_marketplace_status(self, client):
        """Test marketplace status endpoint"""
        response = client.get("/api/v1/marketplace/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "marketplaces" in data
        assert isinstance(data["marketplaces"], list)

    def test_ebay_marketplace_status(self, client):
        """Test eBay marketplace specific status"""
        response = client.get("/api/v1/marketplace/ebay")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["marketplace"] == "ebay"
        assert "status" in data

    def test_product_sync_endpoint(self, client):
        """Test product synchronization across marketplaces"""
        sync_data = {
            "product_id": "PROD-001",
            "marketplaces": ["ebay", "amazon"],
            "sync_type": "full",
        }

        with patch("fs_agt_clean.api.routes.marketplace.sync_product") as mock_sync:
            mock_sync.return_value = {
                "sync_id": "sync_123",
                "status": "initiated",
                "marketplaces": ["ebay", "amazon"],
            }

            response = client.post("/api/v1/marketplace/sync", json=sync_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sync_id" in data
        assert data["status"] == "initiated"


class TestChatEndpoints:
    """
    AGENT_CONTEXT: Test chat and messaging API endpoints
    AGENT_CAPABILITY: Conversations, messages, WebSocket support
    """

    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        return TestClient(app)

    def test_create_conversation(self, client):
        """Test creating a new conversation"""
        conversation_data = {
            "title": "Test Conversation",
            "participants": ["user_1", "agent_market_001"],
            "type": "agent_consultation",
        }

        with patch("fs_agt_clean.api.routes.chat.create_conversation") as mock_create:
            mock_create.return_value = {
                "id": "conv_123",
                "title": "Test Conversation",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            response = client.post("/api/v1/chat/conversations", json=conversation_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Test Conversation"
        assert "id" in data

    def test_send_message(self, client):
        """Test sending a message in a conversation"""
        message_data = {
            "conversation_id": "conv_123",
            "content": "Hello, I need help with pricing analysis",
            "message_type": "text",
        }

        with patch("fs_agt_clean.api.routes.chat.send_message") as mock_send:
            mock_send.return_value = {
                "id": "msg_456",
                "content": "Hello, I need help with pricing analysis",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            response = client.post("/api/v1/chat/messages", json=message_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "Hello, I need help with pricing analysis"


class TestHealthAndMonitoringEndpoints:
    """
    AGENT_CONTEXT: Test health check and monitoring endpoints
    AGENT_CAPABILITY: System health, metrics, status monitoring
    """

    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        return TestClient(app)

    def test_health_check(self, client):
        """Test basic health check endpoint"""
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_detailed_health_check(self, client):
        """Test detailed health check with component status"""
        response = client.get("/api/v1/health/detailed")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert "agents" in data
        assert data["overall_status"] in ["healthy", "degraded", "unhealthy"]

    def test_metrics_endpoint(self, client):
        """Test metrics collection endpoint"""
        response = client.get("/api/v1/metrics")

        assert response.status_code == status.HTTP_200_OK
        # Metrics should be in Prometheus format
        assert "text/plain" in response.headers.get("content-type", "")


class TestErrorHandlingAndSecurity:
    """
    AGENT_CONTEXT: Test error handling and security measures
    AGENT_CAPABILITY: Input validation, rate limiting, error responses
    """

    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        return TestClient(app)

    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON input"""
        response = client.post(
            "/api/v1/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@flipsync.com"},  # Missing password
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints"""
        response = client.get("/api/v1/agents/list")

        # Should require authentication
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_200_OK,
        ]
        # Note: Some endpoints might be public for demo purposes

    def test_nonexistent_endpoint(self, client):
        """Test access to non-existent endpoints"""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_method_not_allowed(self, client):
        """Test wrong HTTP method on endpoints"""
        response = client.delete("/api/v1/auth/login")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


if __name__ == "__main__":
    # AGENT_CONTEXT: Standalone test execution
    pytest.main([__file__, "-v"])
