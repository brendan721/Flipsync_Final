#!/usr/bin/env python3
"""
Test script to verify Agent Communication Protocol implementation.

This test validates that agents can send and receive structured messages
through the AgentMessage protocol and event system integration.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from fs_agt_clean.core.agents.real_agent_manager import RealAgentManager
from fs_agt_clean.core.communication.communication_manager import CommunicationManager
from fs_agt_clean.core.pipeline.controller import PipelineController
from fs_agt_clean.core.protocols.agent_protocol import (
    AgentMessage,
    MessageType,
    Priority,
    UpdateMessage,
    AlertMessage,
    QueryMessage,
    CommandMessage,
    ResponseMessage,
    AgentCategoryType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_agent_communication_protocol():
    """Test the agent communication protocol implementation."""
    logger.info("🚀 Starting Agent Communication Protocol Test")
    
    try:
        # Step 1: Initialize Agent Manager
        logger.info("📋 Step 1: Initializing Agent Manager...")
        agent_manager = RealAgentManager()
        
        init_success = await agent_manager.initialize()
        if not init_success:
            logger.error("❌ Failed to initialize Agent Manager")
            return False
            
        logger.info(f"✅ Agent Manager initialized with {len(agent_manager.agents)} agents")
        
        # Step 2: Initialize Communication Manager
        logger.info("📋 Step 2: Initializing Communication Manager...")
        communication_manager = CommunicationManager(agent_manager=agent_manager)
        
        comm_init_success = await communication_manager.initialize()
        if not comm_init_success:
            logger.error("❌ Failed to initialize Communication Manager")
            return False
            
        logger.info("✅ Communication Manager initialized")
        
        # Step 3: Test Basic Message Sending
        logger.info("📋 Step 3: Testing basic agent-to-agent messaging...")
        
        # Create a test command message
        test_command = CommandMessage(
            sender_id="executive_agent",
            receiver_id="market_agent",
            command="analyze_market_trends",
            parameters={
                "product_category": "electronics",
                "time_period": "30_days",
                "analysis_type": "competitive"
            },
            priority=Priority.HIGH,
        )
        
        # Send the message
        message_sent = await communication_manager.send_agent_message(test_command)
        if message_sent:
            logger.info("✅ Command message sent successfully")
        else:
            logger.error("❌ Failed to send command message")
            return False
        
        # Wait a moment for message processing
        await asyncio.sleep(1)
        
        # Step 4: Test Query Message
        logger.info("📋 Step 4: Testing query messaging...")
        
        test_query = QueryMessage(
            sender_id="content_agent",
            receiver_id="executive_agent",
            query="What is the current pricing strategy for electronics?",
            context={
                "product_category": "electronics",
                "urgency": "high",
                "requester": "content_generation_workflow"
            },
        )
        
        query_sent = await communication_manager.send_agent_message(test_query)
        if query_sent:
            logger.info("✅ Query message sent successfully")
        else:
            logger.error("❌ Failed to send query message")
            return False
        
        # Step 5: Test Broadcast Messaging
        logger.info("📋 Step 5: Testing broadcast messaging...")
        
        broadcast_update = UpdateMessage(
            sender_id="system_coordinator",
            content={
                "update_type": "system_status",
                "message": "System maintenance scheduled for tonight",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "priority": "normal"
            },
        )
        
        broadcast_count = await communication_manager.broadcast_to_category(
            broadcast_update, AgentCategoryType.MARKET
        )
        
        logger.info(f"✅ Broadcast sent to {broadcast_count} market agents")
        
        # Step 6: Test Alert Messaging
        logger.info("📋 Step 6: Testing alert messaging...")
        
        test_alert = AlertMessage(
            sender_id="monitoring_agent",
            receiver_id="executive_agent",
            content={
                "alert_type": "performance_degradation",
                "metric": "response_time",
                "current_value": "2.5s",
                "threshold": "1.0s",
                "affected_services": ["market_analysis", "content_generation"]
            },
            severity="high",
            alert_type="performance",
        )
        
        alert_sent = await communication_manager.send_agent_message(test_alert)
        if alert_sent:
            logger.info("✅ Alert message sent successfully")
        else:
            logger.error("❌ Failed to send alert message")
            return False
        
        # Step 7: Test Pipeline Integration
        logger.info("📋 Step 7: Testing Pipeline Controller integration...")
        
        pipeline_controller = PipelineController(agent_manager=agent_manager)
        await communication_manager._integrate_with_pipeline_controller()
        
        # Test pipeline execution with communication
        from fs_agt_clean.core.pipeline.controller import PipelineStage, PipelineConfiguration
        
        test_stages = [
            PipelineStage("market_analysis", AgentCategoryType.MARKET),
            PipelineStage("executive_decision", AgentCategoryType.EXECUTIVE),
            PipelineStage("content_creation", AgentCategoryType.CONTENT),
        ]
        
        communication_pipeline = PipelineConfiguration(
            pipeline_id="communication_test_pipeline",
            stages=test_stages,
            description="Test pipeline with communication protocol",
        )
        
        pipeline_controller.register_pipeline(communication_pipeline)
        
        # Execute pipeline with communication
        pipeline_success, pipeline_result = await pipeline_controller.execute_pipeline(
            "communication_test_pipeline",
            {
                "product": "Smart Watch",
                "category": "Electronics",
                "test_mode": True,
                "communication_enabled": True
            }
        )
        
        if pipeline_success:
            logger.info("✅ Pipeline execution with communication successful")
        else:
            logger.error("❌ Pipeline execution with communication failed")
            return False
        
        # Step 8: Test Workflow Coordination
        logger.info("📋 Step 8: Testing multi-agent workflow coordination...")
        
        workflow_participants = ["executive_agent", "market_agent", "content_agent", "logistics_agent"]
        workflow_data = {
            "workflow_type": "product_launch",
            "product_name": "Smart Fitness Tracker",
            "target_market": "health_conscious_consumers",
            "launch_timeline": "Q2_2024"
        }
        
        workflow_result = await communication_manager.coordinate_workflow(
            "test_product_launch_workflow",
            workflow_participants,
            workflow_data
        )
        
        if workflow_result.get("status") == "initiated":
            logger.info(f"✅ Workflow coordination initiated with correlation ID: {workflow_result.get('correlation_id')}")
        else:
            logger.error("❌ Failed to initiate workflow coordination")
            return False
        
        # Step 9: Verify Communication Statistics
        logger.info("📋 Step 9: Verifying communication statistics...")
        
        comm_stats = await communication_manager.get_communication_stats()
        
        logger.info("📊 Communication Statistics:")
        logger.info(f"   Registered agents: {comm_stats.get('registered_agents', 0)}")
        logger.info(f"   Total messages: {comm_stats.get('total_messages', 0)}")
        logger.info(f"   Active workflows: {comm_stats.get('active_workflows', 0)}")
        logger.info(f"   Active conversations: {comm_stats.get('active_conversations', 0)}")
        
        # Verify we have meaningful communication activity
        if comm_stats.get('total_messages', 0) >= 5:  # We sent at least 5 messages
            logger.info("✅ Communication activity verified")
        else:
            logger.warning("⚠️ Lower than expected communication activity")
        
        # Step 10: Test Message History and Conversation Tracking
        logger.info("📋 Step 10: Testing message history and conversation tracking...")
        
        # Check if we can retrieve conversation history
        if workflow_result.get("correlation_id"):
            conversation_history = await communication_manager.message_router.get_conversation_history(
                workflow_result["correlation_id"]
            )
            logger.info(f"✅ Retrieved {len(conversation_history)} messages from workflow conversation")
        
        logger.info("🎉 Agent Communication Protocol Test Completed Successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Communication protocol test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test execution function."""
    logger.info("=" * 70)
    logger.info("FlipSync Agent Communication Protocol Test")
    logger.info("=" * 70)
    
    success = await test_agent_communication_protocol()
    
    if success:
        logger.info("🎉 ALL TESTS PASSED - Agent Communication Protocol is working!")
        return 0
    else:
        logger.error("❌ TESTS FAILED - Agent Communication Protocol needs fixes")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
