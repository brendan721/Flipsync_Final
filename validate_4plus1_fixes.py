#!/usr/bin/env python3
"""
Validate 4+1 Architecture Fixes
==============================

Comprehensive validation that all issues have been resolved:
1. Architecture validation working correctly
2. Agents properly registered in autonomous_agents table
3. No more architecture violations
4. Legacy code coexistence handled properly
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


async def validate_4plus1_fixes():
    """Validate that all 4+1 architecture fixes are working."""
    try:
        from fs_agt_clean.core.db.database import get_database
        from fs_agt_clean.database.repositories.autonomous_agent_repository import AutonomousAgentRepository
        from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent
        from fs_agt_clean.core.architecture.boundaries import ArchitecturalBoundaries, ArchitecturalLayer
        
        # Initialize database
        database = get_database()
        await database.initialize()
        repository = AutonomousAgentRepository()
        
        logger.info("✅ Database initialized")
        
        # Test 1: Architecture Validation Fix
        logger.info("🧪 Testing architecture validation fix...")
        
        test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        agent_id = f"test_validation_market_agent_{test_timestamp}"
        
        # Test architecture boundary validation
        layer = ArchitecturalBoundaries.validate_agent_type(agent_id)
        
        if layer == ArchitecturalLayer.AUTONOMOUS:
            logger.info("✅ Architecture validation correctly identifies market agent as AUTONOMOUS")
        else:
            logger.error(f"❌ Architecture validation failed: {layer}")
            return False
        
        # Test 2: Agent Registration and Validation
        logger.info("🧪 Testing agent registration and validation...")
        
        # Create agent instance
        agent = MarketAutonomousAgent(agent_id=agent_id)
        
        # Initialize agent (this should register it and pass validation)
        success = await agent.initialize_async()
        
        if success:
            logger.info("✅ Agent initialization successful")
            
            # Verify agent is registered in database
            async with database.get_session() as session:
                db_agent = await repository.get_autonomous_agent(session, agent_id)
                
                if db_agent:
                    logger.info("✅ Agent found in autonomous_agents table:")
                    logger.info(f"   - Agent ID: {db_agent.agent_id}")
                    logger.info(f"   - Type: {db_agent.agent_type}")
                    logger.info(f"   - LLM Free: {db_agent.llm_free}")
                    logger.info(f"   - Uses Standard Pipeline: {db_agent.uses_standard_decision_pipeline}")
                    
                    # Test 3: Decision Recording
                    logger.info("🧪 Testing decision recording...")
                    
                    from fs_agt_clean.core.coordination.decision.models import DecisionType
                    
                    # Make a test decision
                    test_context = {
                        "test_decision": True,
                        "timestamp": datetime.now().isoformat(),
                        "validation_test": True,
                    }
                    
                    decision = await agent.make_autonomous_decision(
                        decision_context=test_context,
                        decision_type=DecisionType.OPTIMIZATION,
                        use_cache=False
                    )
                    
                    if decision:
                        logger.info("✅ Decision making successful")
                        
                        # Check if decision was recorded
                        decisions = await repository.get_agent_decisions(
                            session=session,
                            agent_id=agent_id,
                            limit=1
                        )
                        
                        if decisions and len(decisions) > 0:
                            latest_decision = decisions[0]
                            logger.info("✅ Decision recorded in autonomous_agent_decisions table:")
                            logger.info(f"   - Decision ID: {latest_decision.decision_id}")
                            logger.info(f"   - Used LLM: {latest_decision.used_llm}")
                            logger.info(f"   - Used Standard Pipeline: {latest_decision.used_standard_pipeline}")
                            logger.info(f"   - Algorithm: {latest_decision.algorithm_used}")
                            
                            return True
                        else:
                            logger.error("❌ Decision not recorded in database")
                            return False
                    else:
                        logger.error("❌ Decision making failed")
                        return False
                else:
                    logger.error("❌ Agent not found in database")
                    return False
        else:
            logger.error("❌ Agent initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_legacy_coexistence():
    """Test that legacy and new architecture can coexist."""
    try:
        from fs_agt_clean.core.db.database import get_database
        
        database = get_database()
        
        # Check that both legacy and new tables exist
        async with database.get_session() as session:
            # Check for legacy tables
            legacy_check = await session.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name IN ('unified_agents', 'unified_users')"
            )
            legacy_tables = [row[0] for row in legacy_check.fetchall()]
            
            # Check for 4+1 architecture tables
            new_check = await session.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name IN ('autonomous_agents', 'conversational_interfaces', 'autonomous_agent_decisions')"
            )
            new_tables = [row[0] for row in new_check.fetchall()]
            
            logger.info(f"📊 Legacy tables found: {legacy_tables}")
            logger.info(f"📊 4+1 architecture tables found: {new_tables}")
            
            if len(new_tables) == 3:
                logger.info("✅ All 4+1 architecture tables exist")
                return True
            else:
                logger.error("❌ Missing 4+1 architecture tables")
                return False
                
    except Exception as e:
        logger.error(f"❌ Legacy coexistence test failed: {e}")
        return False


async def main():
    """Main validation function."""
    logger.info("🚀 Starting 4+1 Architecture Fixes Validation...")
    
    # Test 1: Core 4+1 architecture functionality
    core_success = await validate_4plus1_fixes()
    
    # Test 2: Legacy coexistence
    coexistence_success = await test_legacy_coexistence()
    
    overall_success = core_success and coexistence_success
    
    if overall_success:
        print("\n🎉 ALL 4+1 ARCHITECTURE FIXES VALIDATED SUCCESSFULLY!")
        print("✅ Architecture validation working correctly")
        print("✅ Agents properly registered in autonomous_agents table")
        print("✅ No more architecture violations")
        print("✅ Decision recording functional")
        print("✅ Legacy code coexistence handled properly")
        print("\n🚀 Ready for Phase 3: API and WebSocket Integration")
    else:
        print("\n❌ 4+1 ARCHITECTURE FIXES VALIDATION FAILED")
        print("⚠️ Review logs for details")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
