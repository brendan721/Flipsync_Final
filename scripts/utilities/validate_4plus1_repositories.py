#!/usr/bin/env python3
"""
Validate 4+1 Architecture Repositories
=====================================

This script validates that the new 4+1 architecture repositories work correctly
with the database tables created in Phase 1.

Tests:
- AutonomousAgentRepository functionality
- ConversationalInterfaceRepository functionality
- 4+1 architecture compliance validation
- Database integration and CRUD operations
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append('/home/brend/Flipsync_Final')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@192.168.110.71:5432/flipsync_agentic_test"


class FourPlusOneRepositoryValidator:
    """Validate 4+1 architecture repositories."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Initialize database connection."""
        try:
            self.engine = create_async_engine(
                DATABASE_URL,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                echo=False
            )
            
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            
            logger.info("✅ Database connection initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize database connection: {e}")
            return False
    
    async def test_autonomous_agent_repository(self):
        """Test AutonomousAgentRepository functionality."""
        try:
            logger.info("🤖 Testing AutonomousAgentRepository...")
            
            from fs_agt_clean.database.repositories.autonomous_agent_repository import AutonomousAgentRepository
            from fs_agt_clean.database.models.autonomous_agent import AutonomousAgentType, AutonomousAgentStatus, DecisionStatus
            
            repo = AutonomousAgentRepository()
            
            async with self.session_factory() as session:
                # Test 1: Get existing agents
                agents = await repo.get_all_autonomous_agents(session)
                logger.info(f"✅ Found {len(agents)} existing autonomous agents")
                
                # Test 2: Get specific agent
                if agents:
                    agent = await repo.get_autonomous_agent(session, agents[0].agent_id)
                    if agent:
                        logger.info(f"✅ Retrieved agent: {agent.agent_id} ({agent.agent_type})")
                    else:
                        logger.error("❌ Failed to retrieve specific agent")
                        return False
                
                # Test 3: Update agent status
                if agents:
                    success = await repo.update_agent_heartbeat(session, agents[0].agent_id)
                    if success:
                        logger.info("✅ Updated agent heartbeat")
                    else:
                        logger.error("❌ Failed to update agent heartbeat")
                        return False
                
                # Test 4: Record a test decision
                if agents:
                    decision = await repo.record_decision(
                        session=session,
                        agent_id=agents[0].agent_id,
                        decision_id=f"test_decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        decision_type="test_decision",
                        context={"test": True, "validation": "4+1_architecture"},
                        result={"success": True, "message": "Test decision completed"},
                        execution_time_ms=150.5,
                        confidence=0.95,
                        status=DecisionStatus.COMPLETED,
                        algorithm_used="test_algorithm"
                    )
                    
                    if decision:
                        logger.info(f"✅ Recorded test decision: {decision.decision_id}")
                        
                        # Validate compliance constraints
                        if decision.used_llm == False and decision.used_standard_pipeline == True:
                            logger.info("✅ Decision compliance validated (LLM-free, standard pipeline)")
                        else:
                            logger.error("❌ Decision compliance violation detected")
                            return False
                    else:
                        logger.error("❌ Failed to record test decision")
                        return False
                
                # Test 5: Get agent decisions
                if agents:
                    decisions = await repo.get_agent_decisions(session, agents[0].agent_id, limit=5)
                    logger.info(f"✅ Retrieved {len(decisions)} decisions for agent")
                
                # Test 6: Generate compliance report
                compliance_report = await repo.get_architecture_compliance_report(session)
                if compliance_report:
                    logger.info(f"✅ Generated compliance report - Score: {compliance_report['compliance_score']:.2f}")
                    logger.info(f"   - Autonomous agents: {compliance_report['autonomous_agents_count']}/4")
                    logger.info(f"   - LLM-free compliance: {compliance_report['llm_free_compliance']}")
                    logger.info(f"   - Pipeline compliance: {compliance_report['pipeline_compliance']}")
                else:
                    logger.error("❌ Failed to generate compliance report")
                    return False
            
            logger.info("✅ AutonomousAgentRepository tests passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ AutonomousAgentRepository test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def test_conversational_interface_repository(self):
        """Test ConversationalInterfaceRepository functionality."""
        try:
            logger.info("💬 Testing ConversationalInterfaceRepository...")
            
            from fs_agt_clean.database.repositories.conversational_interface_repository import ConversationalInterfaceRepository
            from fs_agt_clean.database.models.autonomous_agent import ConversationalInterfaceType
            
            repo = ConversationalInterfaceRepository()
            
            async with self.session_factory() as session:
                # Test 1: Get strategic chat service
                strategic_chat = await repo.get_strategic_chat_service(session)
                if strategic_chat:
                    logger.info(f"✅ Found strategic chat service: {strategic_chat.interface_id}")
                    
                    # Validate Gemini-exclusive constraint
                    if strategic_chat.llm_provider == "gemini":
                        logger.info("✅ Gemini-exclusive constraint validated")
                    else:
                        logger.error(f"❌ LLM provider constraint violation: {strategic_chat.llm_provider}")
                        return False
                else:
                    logger.error("❌ Strategic chat service not found")
                    return False
                
                # Test 2: Record conversation activity
                success = await repo.record_conversation(
                    session=session,
                    interface_id=strategic_chat.interface_id,
                    conversation_data={"test": True, "validation": "4+1_architecture"},
                    cost=0.05,
                    message_count=3
                )
                
                if success:
                    logger.info("✅ Recorded conversation activity")
                else:
                    logger.error("❌ Failed to record conversation activity")
                    return False
                
                # Test 3: Get interface metrics
                metrics = await repo.get_interface_metrics(session, strategic_chat.interface_id)
                if metrics:
                    logger.info(f"✅ Retrieved interface metrics:")
                    logger.info(f"   - Total conversations: {metrics['total_conversations']}")
                    logger.info(f"   - Total messages: {metrics['total_messages']}")
                    logger.info(f"   - Total cost: ${metrics['total_cost']:.4f}")
                    logger.info(f"   - Budget utilization: {metrics['budget_utilization']:.1f}%")
                else:
                    logger.error("❌ Failed to retrieve interface metrics")
                    return False
                
                # Test 4: Update interface status
                success = await repo.update_interface_status(
                    session=session,
                    interface_id=strategic_chat.interface_id,
                    status="active",
                    health_status="healthy"
                )
                
                if success:
                    logger.info("✅ Updated interface status")
                else:
                    logger.error("❌ Failed to update interface status")
                    return False
                
                # Test 5: Validate 4+1 compliance
                compliance = await repo.validate_4plus1_compliance(session)
                if compliance:
                    logger.info(f"✅ Generated interface compliance report - Score: {compliance['compliance_score']:.2f}")
                    logger.info(f"   - Interface count: {compliance['conversational_interfaces_count']}/1")
                    logger.info(f"   - Gemini compliance: {compliance['gemini_exclusive_compliance']}")
                    logger.info(f"   - Strategic chat compliance: {compliance['strategic_chat_compliance']}")
                else:
                    logger.error("❌ Failed to generate interface compliance report")
                    return False
            
            logger.info("✅ ConversationalInterfaceRepository tests passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ ConversationalInterfaceRepository test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def test_4plus1_architecture_integrity(self):
        """Test overall 4+1 architecture integrity."""
        try:
            logger.info("🏗️ Testing 4+1 architecture integrity...")
            
            from fs_agt_clean.database.repositories.autonomous_agent_repository import AutonomousAgentRepository
            from fs_agt_clean.database.repositories.conversational_interface_repository import ConversationalInterfaceRepository
            
            agent_repo = AutonomousAgentRepository()
            interface_repo = ConversationalInterfaceRepository()
            
            async with self.session_factory() as session:
                # Test 1: Verify exactly 4 autonomous agents
                agents = await agent_repo.get_all_autonomous_agents(session)
                if len(agents) == 4:
                    logger.info("✅ Exactly 4 autonomous agents found")
                    
                    # Verify agent types
                    agent_types = {agent.agent_type for agent in agents}
                    expected_types = {"market", "content", "executive", "logistics"}
                    
                    if agent_types == expected_types:
                        logger.info("✅ All required agent types present")
                    else:
                        logger.error(f"❌ Missing agent types: {expected_types - agent_types}")
                        return False
                else:
                    logger.error(f"❌ Expected 4 autonomous agents, found {len(agents)}")
                    return False
                
                # Test 2: Verify exactly 1 conversational interface
                interfaces = await interface_repo.get_all_interfaces(session)
                if len(interfaces) == 1:
                    logger.info("✅ Exactly 1 conversational interface found")
                    
                    # Verify interface type
                    if interfaces[0].interface_type == "strategic_chat":
                        logger.info("✅ Strategic chat interface type validated")
                    else:
                        logger.error(f"❌ Unexpected interface type: {interfaces[0].interface_type}")
                        return False
                else:
                    logger.error(f"❌ Expected 1 conversational interface, found {len(interfaces)}")
                    return False
                
                # Test 3: Verify LLM-free constraints on autonomous agents
                llm_free_violations = [agent for agent in agents if not agent.llm_free]
                if not llm_free_violations:
                    logger.info("✅ All autonomous agents are LLM-free")
                else:
                    logger.error(f"❌ LLM-free violations: {[a.agent_id for a in llm_free_violations]}")
                    return False
                
                # Test 4: Verify Gemini-exclusive constraint on conversational interface
                gemini_violations = [i for i in interfaces if i.llm_provider != "gemini"]
                if not gemini_violations:
                    logger.info("✅ All conversational interfaces use Gemini exclusively")
                else:
                    logger.error(f"❌ Gemini-exclusive violations: {[i.interface_id for i in gemini_violations]}")
                    return False
                
                # Test 5: Generate combined compliance report
                agent_compliance = await agent_repo.get_architecture_compliance_report(session)
                interface_compliance = await interface_repo.validate_4plus1_compliance(session)
                
                overall_score = (agent_compliance['compliance_score'] + interface_compliance['compliance_score']) / 2
                
                logger.info(f"✅ Overall 4+1 architecture compliance score: {overall_score:.2f}")
                
                if overall_score >= 0.9:
                    logger.info("🎉 4+1 architecture integrity validation PASSED")
                    return True
                else:
                    logger.warning(f"⚠️ 4+1 architecture compliance below threshold (0.9): {overall_score:.2f}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ 4+1 architecture integrity test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def cleanup(self):
        """Cleanup database connection."""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ Database connection closed")


async def main():
    """Main validation function."""
    validator = FourPlusOneRepositoryValidator()
    
    try:
        # Initialize database connection
        if not await validator.initialize():
            return False
        
        # Test autonomous agent repository
        if not await validator.test_autonomous_agent_repository():
            logger.error("❌ Autonomous agent repository validation failed")
            return False
        
        # Test conversational interface repository
        if not await validator.test_conversational_interface_repository():
            logger.error("❌ Conversational interface repository validation failed")
            return False
        
        # Test overall 4+1 architecture integrity
        if not await validator.test_4plus1_architecture_integrity():
            logger.error("❌ 4+1 architecture integrity validation failed")
            return False
        
        logger.info("🎉 All 4+1 architecture repository validations PASSED!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation failed with exception: {e}")
        return False
    finally:
        await validator.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
