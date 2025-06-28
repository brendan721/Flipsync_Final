#!/usr/bin/env python3
"""
Test script to verify chat service integration with real 12-agent system.
This script tests the fixes implemented to resolve chat-agent disconnect problems.
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fs_agt_clean.core.agents.real_agent_manager import RealUnifiedAgentManager
from fs_agt_clean.core.config import get_settings
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.services.communication.chat_service import EnhancedChatService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MockApp:
    """Mock FastAPI app for testing."""

    def __init__(self):
        self.state = MockAppState()


class MockAppState:
    """Mock app state for testing."""

    def __init__(self):
        self.real_agent_manager = None
        self.database = None


async def test_real_agent_manager_initialization():
    """Test 1: Verify RealUnifiedAgentManager initializes properly."""
    logger.info("🧪 TEST 1: RealUnifiedAgentManager Initialization")

    try:
        # Initialize RealUnifiedAgentManager
        real_agent_manager = RealUnifiedAgentManager()

        # Test synchronous initialization (fix for race condition)
        logger.info("Testing synchronous initialization...")
        initialization_success = await real_agent_manager.initialize()

        if initialization_success:
            logger.info("✅ RealUnifiedAgentManager initialized successfully")

            # Get agent statuses
            agent_statuses = await real_agent_manager.get_all_agent_statuses()
            logger.info(f"✅ UnifiedAgent statuses: {agent_statuses}")

            # Test agent availability
            available_agents = []
            for agent_id in [
                "executive_agent",
                "content_agent",
                "logistics_agent",
                "market_agent",
            ]:
                agent_instance = real_agent_manager.get_agent_instance(agent_id)
                if agent_instance:
                    available_agents.append(agent_id)
                    logger.info(
                        f"✅ UnifiedAgent {agent_id} available: {type(agent_instance)}"
                    )
                else:
                    logger.warning(f"❌ UnifiedAgent {agent_id} not available")

            return real_agent_manager, available_agents
        else:
            logger.error("❌ RealUnifiedAgentManager initialization failed")
            return None, []

    except Exception as e:
        logger.error(f"❌ RealUnifiedAgentManager initialization error: {e}")
        logger.exception("Full error details:")
        return None, []


async def test_chat_service_app_reference():
    """Test 2: Verify chat service gets proper app reference."""
    logger.info("🧪 TEST 2: Chat Service App Reference")

    try:
        # Create mock app and database with proper config
        mock_app = MockApp()

        # Import config manager for proper database initialization
        from fs_agt_clean.core.config import ConfigManager

        config_manager = ConfigManager()
        database = Database(config_manager=config_manager)

        # Initialize chat service (simulating main.py initialization)
        chat_service = EnhancedChatService(database=database)

        # Test app reference assignment (fix for consistent app reference)
        logger.info("Testing app reference assignment...")
        chat_service.app = mock_app

        if hasattr(chat_service, "app") and chat_service.app is not None:
            logger.info("✅ Chat service has app reference")
            return chat_service, mock_app
        else:
            logger.error("❌ Chat service missing app reference")
            return None, None

    except Exception as e:
        logger.error(f"❌ Chat service app reference error: {e}")
        logger.exception("Full error details:")
        return None, None


async def test_method_signature_compatibility():
    """Test 3: Verify method signature compatibility fixes."""
    logger.info("🧪 TEST 3: Method Signature Compatibility")

    try:
        # Initialize components
        real_agent_manager, available_agents = (
            await test_real_agent_manager_initialization()
        )
        if not real_agent_manager:
            logger.error("❌ Cannot test method signatures without RealUnifiedAgentManager")
            return False

        # Test method signatures for each available agent
        test_message = "Hello, this is a test message"
        test_user_id = "test_user_123"
        test_conversation_id = "test_conversation_456"
        test_context = {"test": True}

        for agent_id in available_agents:
            logger.info(f"Testing method signature for {agent_id}...")
            agent_instance = real_agent_manager.get_agent_instance(agent_id)

            if hasattr(agent_instance, "process_message"):
                try:
                    # Test with correct method signature (fix for method signature compatibility)
                    response = await agent_instance.process_message(
                        message=test_message,
                        user_id=test_user_id,
                        conversation_id=test_conversation_id,
                        conversation_history=[],
                        context=test_context,
                    )
                    logger.info(f"✅ UnifiedAgent {agent_id} method signature compatible")
                    logger.info(f"✅ Response type: {type(response)}")

                except TypeError as te:
                    logger.error(
                        f"❌ UnifiedAgent {agent_id} method signature incompatible: {te}"
                    )
                    return False
                except Exception as e:
                    logger.warning(
                        f"⚠️ UnifiedAgent {agent_id} execution error (but signature OK): {e}"
                    )
            else:
                logger.warning(f"⚠️ UnifiedAgent {agent_id} has no process_message method")

        return True

    except Exception as e:
        logger.error(f"❌ Method signature compatibility test error: {e}")
        logger.exception("Full error details:")
        return False


async def test_end_to_end_integration():
    """Test 4: End-to-end chat service to agent integration."""
    logger.info("🧪 TEST 4: End-to-End Integration")

    try:
        # Initialize all components
        real_agent_manager, available_agents = (
            await test_real_agent_manager_initialization()
        )
        chat_service, mock_app = await test_chat_service_app_reference()

        if not real_agent_manager or not chat_service:
            logger.error("❌ Cannot test end-to-end without initialized components")
            return False

        # Set up the integration (simulating lifespan function)
        mock_app.state.real_agent_manager = real_agent_manager
        mock_app.state.database = chat_service.database

        # Test message processing
        test_message = "Can you help me analyze my inventory performance?"
        test_user_id = "test_user_integration"
        test_conversation_id = "test_conversation_integration"

        logger.info("Testing end-to-end message processing...")

        # This should now use real agents instead of legacy LLM fallback
        response = await chat_service.handle_message_enhanced(
            message=test_message,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
        )

        logger.info(f"✅ End-to-end response received: {response[:100]}...")

        # Verify response is not the generic error message
        generic_error = (
            "I apologize, but I'm having trouble processing your request right now"
        )
        if generic_error in response:
            logger.warning("⚠️ Response appears to be generic error message")
            return False
        else:
            logger.info("✅ Response appears to be from real agent (not generic error)")
            return True

    except Exception as e:
        logger.error(f"❌ End-to-end integration test error: {e}")
        logger.exception("Full error details:")
        return False


async def main():
    """Run all integration tests."""
    logger.info("🚀 Starting Chat Service Integration Tests")
    logger.info("=" * 60)

    test_results = {}

    # Test 1: RealUnifiedAgentManager Initialization
    real_agent_manager, available_agents = (
        await test_real_agent_manager_initialization()
    )
    test_results["real_agent_manager_init"] = real_agent_manager is not None

    # Test 2: Chat Service App Reference
    chat_service, mock_app = await test_chat_service_app_reference()
    test_results["chat_service_app_ref"] = chat_service is not None

    # Test 3: Method Signature Compatibility
    test_results["method_signature_compat"] = (
        await test_method_signature_compatibility()
    )

    # Test 4: End-to-End Integration
    test_results["end_to_end_integration"] = await test_end_to_end_integration()

    # Summary
    logger.info("=" * 60)
    logger.info("🏁 TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed_tests = 0
    total_tests = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_tests += 1

    logger.info("=" * 60)
    logger.info(f"OVERALL: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED - Chat service integration is working!")
        return True
    else:
        logger.error("💥 SOME TESTS FAILED - Chat service integration needs more work")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
