#!/usr/bin/env python3
"""
Simple Agent Test - Identify Import Issues
"""

import asyncio
import sys
import os

# Set environment variables
os.environ["DATABASE_URL"] = "sqlite:///flipsync_local.db"
os.environ["DB_NAME"] = "flipsync_agentic_test"
os.environ["REDIS_URL"] = "redis://:FlipSync2024SecureRedis!@localhost:6379/0"
os.environ["AUTH_SERVICE_TYPE"] = "database"
os.environ["ENVIRONMENT"] = "agentic_testing"

# Add project root to path
sys.path.insert(0, ".")

print("🚀 Starting Simple Agent Test...")

try:
    print("📦 Testing basic imports...")
    from fs_agt_clean.core.db.database import Database
    print("✅ Database import successful")
    
    print("🤖 Testing agent imports...")
    from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent
    print("✅ MarketAgent import successful")
    
    print("🔧 Testing agent manager import...")
    from fs_agt_clean.core.agents.autonomous_agent_manager import AutonomousAgentManager
    print("✅ AgentManager import successful")
    
    print("🎯 All imports successful!")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

async def test_basic_agent_creation():
    """Test basic agent creation without full initialization."""
    try:
        print("\n🤖 Testing basic agent creation...")
        
        # Test creating a market agent
        market_agent = MarketAutonomousAgent("test_market_agent")
        print("✅ MarketAgent created successfully")
        
        print("✅ Basic agent test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("\n" + "="*50)
    print("🧪 SIMPLE AGENT SYSTEM TEST")
    print("="*50)
    
    success = await test_basic_agent_creation()
    
    if success:
        print("\n✅ Simple agent test PASSED!")
        return True
    else:
        print("\n❌ Simple agent test FAILED!")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
