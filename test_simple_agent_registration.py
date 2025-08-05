#!/usr/bin/env python3
"""
Simple Agent Registration Test
=============================

Quick test to validate that agent registration in 4+1 architecture works correctly.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append('/home/brend/Flipsync_Final')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set environment variables for database connection
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test"
os.environ["DB_NAME"] = "flipsync_agentic_test"


async def test_simple_agent_registration():
    """Test simple agent registration."""
    try:
        from fs_agt_clean.core.db.database import get_database
        from fs_agt_clean.database.repositories.autonomous_agent_repository import AutonomousAgentRepository
        from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent
        
        # Initialize database
        database = get_database()
        await database.initialize()
        repository = AutonomousAgentRepository()
        
        logger.info("✅ Database initialized")
        
        # Create test agent
        test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        agent_id = f"test_simple_market_agent_{test_timestamp}"
        
        logger.info(f"Creating agent: {agent_id}")
        
        # Create agent instance
        agent = MarketAutonomousAgent(agent_id=agent_id)
        
        # Initialize agent (this should register it in the database)
        success = await agent.initialize_async()
        
        if success:
            logger.info("✅ Agent initialization successful")
            
            # Verify agent is registered in database
            async with database.get_session() as session:
                db_agent = await repository.get_autonomous_agent(session, agent_id)
                
                if db_agent:
                    logger.info(f"✅ Agent found in database:")
                    logger.info(f"   - ID: {db_agent.id}")
                    logger.info(f"   - Agent ID: {db_agent.agent_id}")
                    logger.info(f"   - Type: {db_agent.agent_type}")
                    logger.info(f"   - Class: {db_agent.agent_class}")
                    logger.info(f"   - Status: {db_agent.status}")
                    logger.info(f"   - LLM Free: {db_agent.llm_free}")
                    logger.info(f"   - Uses Standard Pipeline: {db_agent.uses_standard_decision_pipeline}")
                    
                    return True
                else:
                    logger.error("❌ Agent not found in database")
                    return False
        else:
            logger.error("❌ Agent initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting Simple Agent Registration Test...")
    
    success = await test_simple_agent_registration()
    
    if success:
        print("\n🎉 SIMPLE AGENT REGISTRATION TEST PASSED!")
        print("✅ Agent successfully registered in 4+1 architecture")
    else:
        print("\n❌ SIMPLE AGENT REGISTRATION TEST FAILED")
        print("⚠️ Review logs for details")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
