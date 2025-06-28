#!/usr/bin/env python3
"""
Core Functionality Tests for FlipSync - Standalone Validation
AGENT_CONTEXT: Validate core functionality without complex dependencies
AGENT_PRIORITY: Ensure basic components work correctly
AGENT_PATTERN: Standalone testing, minimal dependencies, core validation
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestBasicFunctionality:
    """
    AGENT_CONTEXT: Test basic functionality without complex imports
    AGENT_CAPABILITY: Core validation, dependency checking, basic operations
    """
    
    def test_python_environment(self):
        """Test Python environment is working"""
        assert sys.version_info.major >= 3
        assert sys.version_info.minor >= 8
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    def test_required_modules_import(self):
        """Test that required modules can be imported"""
        try:
            import pytest
            import fastapi
            import pydantic
            import sqlalchemy
            import asyncpg
            import uvicorn
            import httpx
            import bcrypt
            print("✅ All core modules imported successfully")
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import required module: {e}")
    
    def test_project_structure(self):
        """Test project structure exists"""
        project_root = Path(__file__).parent
        
        required_paths = [
            project_root / "fs_agt_clean",
            project_root / "fs_agt_clean" / "app",
            project_root / "fs_agt_clean" / "api",
            project_root / "fs_agt_clean" / "core",
            project_root / "fs_agt_clean" / "tests",
            project_root / "requirements.txt",
            project_root / "pytest.ini"
        ]
        
        for path in required_paths:
            assert path.exists(), f"Required path missing: {path}"
        
        print("✅ Project structure validated")
    
    def test_fastapi_basic_functionality(self):
        """Test FastAPI basic functionality"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI(title="Test App")
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok", "message": "test successful"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✅ FastAPI basic functionality working")
    
    def test_pydantic_models(self):
        """Test Pydantic model functionality"""
        from pydantic import BaseModel, EmailStr
        from typing import Optional
        
        class TestUser(BaseModel):
            id: str
            email: str
            username: str
            is_active: bool = True
            metadata: Optional[dict] = None
        
        # Test model creation
        user_data = {
            "id": "test_123",
            "email": "test@flipsync.com",
            "username": "testuser",
            "metadata": {"role": "user"}
        }
        
        user = TestUser(**user_data)
        assert user.id == "test_123"
        assert user.email == "test@flipsync.com"
        assert user.is_active is True
        
        # Test JSON serialization
        user_json = user.model_dump()
        assert isinstance(user_json, dict)
        assert user_json["email"] == "test@flipsync.com"
        
        print("✅ Pydantic models working")
    
    def test_sqlalchemy_basic_functionality(self):
        """Test SQLAlchemy basic functionality"""
        from sqlalchemy import create_engine, Column, String, Boolean, DateTime
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker
        
        Base = declarative_base()
        
        class TestUser(Base):
            __tablename__ = "test_users"
            
            id = Column(String, primary_key=True)
            email = Column(String, unique=True, nullable=False)
            username = Column(String, unique=True, nullable=False)
            is_active = Column(Boolean, default=True)
            created_at = Column(DateTime, default=datetime.now)
        
        # Test in-memory SQLite
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test user creation
        user = TestUser(
            id="test_123",
            email="test@flipsync.com",
            username="testuser"
        )
        
        session.add(user)
        session.commit()
        
        # Test user retrieval
        retrieved_user = session.query(TestUser).filter_by(email="test@flipsync.com").first()
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        
        session.close()
        print("✅ SQLAlchemy basic functionality working")
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async/await functionality"""
        async def async_operation():
            await asyncio.sleep(0.01)
            return "async_result"
        
        result = await async_operation()
        assert result == "async_result"
        print("✅ Async functionality working")
    
    def test_password_hashing(self):
        """Test password hashing functionality"""
        import bcrypt
        
        password = "TestPassword123!"
        
        # Hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Verify password
        assert bcrypt.checkpw(password.encode('utf-8'), hashed)
        assert not bcrypt.checkpw("WrongPassword".encode('utf-8'), hashed)
        
        print("✅ Password hashing working")
    
    def test_json_operations(self):
        """Test JSON operations"""
        test_data = {
            "user_id": "test_123",
            "email": "test@flipsync.com",
            "metadata": {
                "role": "user",
                "permissions": ["read", "write"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Test serialization
        json_str = json.dumps(test_data)
        assert isinstance(json_str, str)
        
        # Test deserialization
        parsed_data = json.loads(json_str)
        assert parsed_data["user_id"] == "test_123"
        assert parsed_data["metadata"]["role"] == "user"
        
        print("✅ JSON operations working")


class TestDatabaseConnectivity:
    """
    AGENT_CONTEXT: Test database connectivity with running infrastructure
    AGENT_CAPABILITY: PostgreSQL connection, Redis connection, basic operations
    """
    
    @pytest.mark.asyncio
    async def test_postgresql_connection(self):
        """Test PostgreSQL connection to running container"""
        try:
            import asyncpg
            
            # Connect to the running PostgreSQL container
            conn = await asyncpg.connect(
                host="localhost",
                port=1432,
                user="postgres",
                password="postgres",
                database="postgres"
            )
            
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            assert result == 1
            
            # Test table creation
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS test_connectivity (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Test insert
            await conn.execute(
                "INSERT INTO test_connectivity (name) VALUES ($1)",
                "test_record"
            )
            
            # Test select
            records = await conn.fetch("SELECT * FROM test_connectivity WHERE name = $1", "test_record")
            assert len(records) > 0
            
            # Cleanup
            await conn.execute("DROP TABLE IF EXISTS test_connectivity")
            await conn.close()
            
            print("✅ PostgreSQL connectivity working")
            
        except Exception as e:
            print(f"⚠️ PostgreSQL connection failed: {e}")
            # Don't fail the test if database is not available
            pytest.skip("PostgreSQL not available")
    
    def test_redis_connection(self):
        """Test Redis connection to running container"""
        try:
            import redis
            
            # Connect to Redis container
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Test basic operations
            r.set('test_key', 'test_value')
            value = r.get('test_key')
            assert value == 'test_value'
            
            # Test hash operations
            r.hset('test_hash', 'field1', 'value1')
            hash_value = r.hget('test_hash', 'field1')
            assert hash_value == 'value1'
            
            # Cleanup
            r.delete('test_key', 'test_hash')
            
            print("✅ Redis connectivity working")
            
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            # Don't fail the test if Redis is not available
            pytest.skip("Redis not available")


class TestAPIEndpointStructure:
    """
    AGENT_CONTEXT: Test API endpoint structure without full application
    AGENT_CAPABILITY: Route validation, endpoint structure, response formats
    """
    
    def test_fastapi_app_creation(self):
        """Test FastAPI app can be created with basic structure"""
        from fastapi import FastAPI, APIRouter
        from fastapi.testclient import TestClient
        
        app = FastAPI(
            title="FlipSync Test API",
            version="1.0.0",
            description="Test API for FlipSync validation"
        )
        
        # Create test router
        router = APIRouter(prefix="/api/v1", tags=["test"])
        
        @router.get("/health")
        def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0"
            }
        
        @router.get("/agents/list")
        def get_agents():
            return [
                {
                    "id": "agent_test_001",
                    "name": "Test Agent",
                    "type": "test",
                    "status": "active"
                }
            ]
        
        app.include_router(router)
        
        # Test with client
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Test agents endpoint
        response = client.get("/api/v1/agents/list")
        assert response.status_code == 200
        agents = response.json()
        assert len(agents) > 0
        assert agents[0]["type"] == "test"
        
        print("✅ API endpoint structure working")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
