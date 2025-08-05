#!/usr/bin/env python3
"""
Test Repository Method Availability
==================================

Quick test to verify that the AutonomousAgentRepository has the record_autonomous_decision method.
"""

import asyncio
import logging
import os
import sys

# Add the project root to the Python path
sys.path.append('/home/brend/Flipsync_Final')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set environment variables for database connection
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test"
os.environ["DB_NAME"] = "flipsync_agentic_test"


async def test_repository_method():
    """Test that the repository has the record_autonomous_decision method."""
    try:
        logger.info("🧪 Testing repository method availability...")
        
        from fs_agt_clean.database.repositories.autonomous_agent_repository import AutonomousAgentRepository
        
        # Create repository instance
        repository = AutonomousAgentRepository()
        
        # Check if method exists
        if hasattr(repository, 'record_autonomous_decision'):
            logger.info("✅ record_autonomous_decision method exists")
            
            # Check method signature
            import inspect
            sig = inspect.signature(repository.record_autonomous_decision)
            logger.info(f"✅ Method signature: {sig}")
            
            return True
        else:
            logger.error("❌ record_autonomous_decision method does not exist")
            
            # List available methods
            methods = [method for method in dir(repository) if not method.startswith('_')]
            logger.info(f"📊 Available methods: {methods}")
            
            return False
            
    except Exception as e:
        logger.error(f"❌ Repository method test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_repository_instance():
    """Test that agents can create repository instances with the method."""
    try:
        logger.info("🧪 Testing agent repository instance...")
        
        from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent
        from datetime import datetime
        
        # Create test agent
        test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        agent_id = f"test_repo_method_agent_{test_timestamp}"
        
        agent = MarketAutonomousAgent(agent_id=agent_id)
        
        # Check if agent has repository
        if hasattr(agent, 'autonomous_agent_repository'):
            logger.info("✅ Agent has autonomous_agent_repository attribute")
            
            # Check if repository has method
            if hasattr(agent.autonomous_agent_repository, 'record_autonomous_decision'):
                logger.info("✅ Agent's repository has record_autonomous_decision method")
                return True
            else:
                logger.error("❌ Agent's repository missing record_autonomous_decision method")
                return False
        else:
            logger.error("❌ Agent missing autonomous_agent_repository attribute")
            return False
            
    except Exception as e:
        logger.error(f"❌ Agent repository instance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting Repository Method Test...")
    
    # Test 1: Repository method availability
    repo_success = await test_repository_method()
    
    # Test 2: Agent repository instance
    agent_success = await test_agent_repository_instance()
    
    overall_success = repo_success and agent_success
    
    if overall_success:
        print("\n🎉 REPOSITORY METHOD TEST PASSED!")
        print("✅ Repository has record_autonomous_decision method")
        print("✅ Agents can access the method")
        print("✅ Ready for decision recording testing")
    else:
        print("\n❌ REPOSITORY METHOD TEST FAILED")
        print("⚠️ Review logs for details")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
