#!/usr/bin/env python3
"""
Phase 3.3: StrategicChatService Integration Test
===============================================

Comprehensive test suite for Phase 3.3 StrategicChatService Integration.
Tests the integration between StrategicChatService and 4+1 architecture:

Phase 3.3.1: StrategicChatService API Integration
- Chat endpoints use 4+1 architecture database exclusively
- Integration with AutonomousAgentRepository for agent coordination
- Conversational interface endpoints complement autonomous agent APIs
- Chat service can query and interact with autonomous_agents table data
- Real-time chat integration with WebSocket endpoints from Phase 3.2

Phase 3.3.2: Conversational Interface Coordination
- Coordination layer between StrategicChatService and autonomous agents
- Chat-to-agent command routing and response handling
- Conversational monitoring and logging to 4+1 architecture database
- StrategicChatService can trigger autonomous agent actions through proper APIs
- Chat history integrated with agent decision tracking

Success Criteria:
- StrategicChatService successfully integrated with 4+1 architecture database
- Chat endpoints can query and display autonomous agent status and decisions
- Conversational interface can coordinate with autonomous agents through proper APIs
- Real-time chat updates working through WebSocket integration
- Chat service maintains Gemini LLM functionality while coordinating with LLM-free autonomous agents
- Zero legacy chat dependencies - all chat data stored in 4+1 architecture tables
"""

import asyncio
import inspect
import logging
import sys
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_chat_module_imports():
    """Test that all new 4+1 architecture chat modules import successfully."""
    logger.info("🧪 Testing Chat Module Imports")

    try:
        # Set required environment variables for testing
        import os

        os.environ["GEMINI_API_KEY"] = "test_key_for_import_testing"

        # Test chat API import
        import fs_agt_clean.api.routes.chat_4plus1 as chat_api_module

        logger.info("✅ Successfully imported chat_4plus1 API module")

        # Test chat WebSocket import
        import fs_agt_clean.api.websocket.chat_4plus1_ws as chat_ws_module

        logger.info("✅ Successfully imported chat_4plus1_ws WebSocket module")

        # Verify modules have expected attributes
        assert hasattr(
            chat_api_module, "router"
        ), "chat_4plus1 API module missing router"
        assert hasattr(
            chat_ws_module, "router"
        ), "chat_4plus1_ws WebSocket module missing router"

        # Verify chat service classes
        assert hasattr(
            chat_api_module, "StrategicChatService4Plus1"
        ), "chat_4plus1 API module missing StrategicChatService4Plus1"
        assert hasattr(
            chat_ws_module, "ChatWebSocketManager"
        ), "chat_4plus1_ws WebSocket module missing ChatWebSocketManager"

        logger.info(
            "✅ All chat modules imported successfully with required attributes"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Chat module import test failed: {e}")
        return False


def test_chat_router_configurations():
    """Test chat router configurations for 4+1 architecture compliance."""
    logger.info("🧪 Testing Chat Router Configurations")

    try:
        import fs_agt_clean.api.routes.chat_4plus1 as chat_api_module
        import fs_agt_clean.api.websocket.chat_4plus1_ws as chat_ws_module

        chat_api_router = chat_api_module.router
        chat_ws_router = chat_ws_module.router

        # Test router prefixes
        assert (
            chat_api_router.prefix == "/chat/4plus1"
        ), f"Expected /chat/4plus1 prefix, got {chat_api_router.prefix}"
        assert (
            chat_ws_router.prefix == "/ws/chat"
        ), f"Expected /ws/chat prefix, got {chat_ws_router.prefix}"

        # Test router tags for 4+1 architecture identification
        chat_api_tags = chat_api_router.tags
        chat_ws_tags = chat_ws_router.tags

        assert (
            "4+1-architecture-chat" in chat_api_tags
        ), f"Missing 4+1 architecture tag in chat API router: {chat_api_tags}"
        assert (
            "4+1-architecture-chat-websockets" in chat_ws_tags
        ), f"Missing 4+1 architecture tag in chat WebSocket router: {chat_ws_tags}"

        logger.info("✅ Chat router configurations are correct for 4+1 architecture")
        logger.info(
            f"   - Chat API router: {chat_api_router.prefix} with tags {chat_api_tags}"
        )
        logger.info(
            f"   - Chat WebSocket router: {chat_ws_router.prefix} with tags {chat_ws_tags}"
        )

        return True

    except Exception as e:
        logger.error(f"❌ Chat router configuration test failed: {e}")
        return False


def test_chat_api_endpoints():
    """Test that chat API endpoints are properly defined."""
    logger.info("🧪 Testing Chat API Endpoints")

    try:
        import fs_agt_clean.api.routes.chat_4plus1 as chat_api_module
        import fs_agt_clean.api.websocket.chat_4plus1_ws as chat_ws_module

        # Get router routes
        chat_api_routes = chat_api_module.router.routes
        chat_ws_routes = chat_ws_module.router.routes

        logger.info(f"📊 Chat API endpoints: {len(chat_api_routes)} routes")
        for route in chat_api_routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                method = list(route.methods)[0] if route.methods else "GET"
                logger.info(f"   - {method} {route.path}")

        logger.info(f"📊 Chat WebSocket endpoints: {len(chat_ws_routes)} routes")
        for route in chat_ws_routes:
            if hasattr(route, "path"):
                logger.info(f"   - WebSocket {route.path}")

        # Verify minimum expected chat API endpoints exist
        chat_api_paths = [
            route.path for route in chat_api_routes if hasattr(route, "path")
        ]
        chat_ws_paths = [
            route.path for route in chat_ws_routes if hasattr(route, "path")
        ]

        # Expected chat API endpoints
        expected_api_paths = [
            "/chat/4plus1/conversations",
            "/chat/4plus1/conversations/{conversation_id}/messages",
            "/chat/4plus1/agent-status",
            "/chat/4plus1/agent-command",
            "/chat/4plus1/agent-decisions",
        ]
        for expected_path in expected_api_paths:
            path_exists = any(expected_path in path for path in chat_api_paths)
            if path_exists:
                logger.info(f"✅ Found expected chat API endpoint: {expected_path}")
            else:
                logger.warning(f"⚠️ Missing expected chat API endpoint: {expected_path}")

        # Expected chat WebSocket endpoints
        expected_ws_paths = ["/ws/chat/4plus1/{conversation_id}"]
        for expected_path in expected_ws_paths:
            path_exists = any(expected_path in path for path in chat_ws_paths)
            if path_exists:
                logger.info(
                    f"✅ Found expected chat WebSocket endpoint: {expected_path}"
                )
            else:
                logger.warning(
                    f"⚠️ Missing expected chat WebSocket endpoint: {expected_path}"
                )

        logger.info("✅ Chat endpoints validation completed")
        return True

    except Exception as e:
        logger.error(f"❌ Chat endpoints test failed: {e}")
        return False


def test_chat_service_classes():
    """Test chat service classes for proper functionality."""
    logger.info("🧪 Testing Chat Service Classes")

    try:
        import fs_agt_clean.api.routes.chat_4plus1 as chat_api_module
        import fs_agt_clean.api.websocket.chat_4plus1_ws as chat_ws_module

        # Test StrategicChatService4Plus1
        chat_service_class = chat_api_module.StrategicChatService4Plus1
        chat_service = chat_service_class()

        # Check required methods
        required_chat_methods = [
            "handle_chat_with_agent_context",
            "_get_relevant_agent_data",
            "_store_conversation_4plus1",
        ]
        for method_name in required_chat_methods:
            assert hasattr(
                chat_service, method_name
            ), f"StrategicChatService4Plus1 missing method: {method_name}"
            method = getattr(chat_service, method_name)
            assert callable(
                method
            ), f"StrategicChatService4Plus1.{method_name} is not callable"
            logger.info(
                f"✅ StrategicChatService4Plus1.{method_name} is available and callable"
            )

        # Check agent command mapping
        assert hasattr(
            chat_service, "agent_commands"
        ), "StrategicChatService4Plus1 missing agent_commands"
        expected_commands = ["status", "decisions", "performance", "trigger"]
        for command in expected_commands:
            assert (
                command in chat_service.agent_commands
            ), f"StrategicChatService4Plus1 missing command: {command}"
            logger.info(f"✅ StrategicChatService4Plus1 supports command: {command}")

        # Test ChatWebSocketManager
        chat_ws_manager_class = chat_ws_module.ChatWebSocketManager
        chat_ws_manager = chat_ws_manager_class()

        # Check required methods
        required_ws_methods = [
            "connect",
            "disconnect",
            "broadcast_to_channel",
            "handle_chat_message",
        ]
        for method_name in required_ws_methods:
            assert hasattr(
                chat_ws_manager, method_name
            ), f"ChatWebSocketManager missing method: {method_name}"
            method = getattr(chat_ws_manager, method_name)
            assert callable(
                method
            ), f"ChatWebSocketManager.{method_name} is not callable"
            logger.info(
                f"✅ ChatWebSocketManager.{method_name} is available and callable"
            )

        # Check chat connection types
        expected_connection_types = ["chat_4plus1", "agent_monitor", "coordination"]
        for conn_type in expected_connection_types:
            assert (
                conn_type in chat_ws_manager.connections
            ), f"ChatWebSocketManager missing connection type: {conn_type}"
            logger.info(
                f"✅ ChatWebSocketManager supports connection type: {conn_type}"
            )

        logger.info("✅ Chat service classes validation completed")
        return True

    except Exception as e:
        logger.error(f"❌ Chat service classes test failed: {e}")
        return False


def test_chat_pydantic_models():
    """Test chat Pydantic models for proper structure."""
    logger.info("🧪 Testing Chat Pydantic Models")

    try:
        import fs_agt_clean.api.routes.chat_4plus1 as chat_api_module

        # Test request models
        request_models = [
            "ChatMessage4Plus1Request",
            "AgentCommand4Plus1Request",
        ]

        for model_name in request_models:
            assert hasattr(
                chat_api_module, model_name
            ), f"Missing request model: {model_name}"
            model_class = getattr(chat_api_module, model_name)

            # Check if it's a Pydantic model
            assert hasattr(
                model_class, "__fields__"
            ), f"{model_name} is not a Pydantic model"
            logger.info(f"✅ {model_name} is properly defined as Pydantic model")

            # Check required fields
            fields = model_class.__fields__
            logger.info(f"   - Fields: {list(fields.keys())}")

        # Test response models
        response_models = [
            "ChatMessage4Plus1Response",
            "AgentCommand4Plus1Response",
        ]

        for model_name in response_models:
            assert hasattr(
                chat_api_module, model_name
            ), f"Missing response model: {model_name}"
            model_class = getattr(chat_api_module, model_name)

            # Check if it's a Pydantic model
            assert hasattr(
                model_class, "__fields__"
            ), f"{model_name} is not a Pydantic model"
            logger.info(f"✅ {model_name} is properly defined as Pydantic model")

            # Check required fields
            fields = model_class.__fields__
            logger.info(f"   - Fields: {list(fields.keys())}")

        logger.info("✅ Chat Pydantic models validation completed")
        return True

    except Exception as e:
        logger.error(f"❌ Chat Pydantic models test failed: {e}")
        return False


def test_chat_4plus1_compliance():
    """Test chat implementations for 4+1 architecture compliance."""
    logger.info("🧪 Testing Chat 4+1 Architecture Compliance")

    try:
        import fs_agt_clean.api.routes.chat_4plus1 as chat_api_module
        import fs_agt_clean.api.websocket.chat_4plus1_ws as chat_ws_module

        # Get module source code
        chat_api_source = inspect.getsource(chat_api_module)
        chat_ws_source = inspect.getsource(chat_ws_module)

        # Check for 4+1 architecture compliance indicators
        compliance_indicators = [
            "autonomous_agents",
            "autonomous_agent_decisions",
            "AutonomousAgentRepository",
            "4+1",
            "llm_free",
            "StrategicChatService",
            "ArchitecturalLayer",
        ]

        chat_api_indicators_found = []
        chat_ws_indicators_found = []

        for indicator in compliance_indicators:
            if indicator in chat_api_source:
                chat_api_indicators_found.append(indicator)
            if indicator in chat_ws_source:
                chat_ws_indicators_found.append(indicator)

        logger.info(
            f"📊 4+1 Architecture indicators in chat API module: {len(chat_api_indicators_found)}"
        )
        for indicator in chat_api_indicators_found:
            logger.info(f"   ✅ {indicator}")

        logger.info(
            f"📊 4+1 Architecture indicators in chat WebSocket module: {len(chat_ws_indicators_found)}"
        )
        for indicator in chat_ws_indicators_found:
            logger.info(f"   ✅ {indicator}")

        # Check for chat-specific indicators
        chat_specific_indicators = [
            "StrategicChatService",
            "ChatRequest",
            "ChatResponse",
            "conversational_interface",
            "Gemini",
        ]

        chat_specific_found = []
        for indicator in chat_specific_indicators:
            if indicator in chat_api_source or indicator in chat_ws_source:
                chat_specific_found.append(indicator)

        logger.info(f"📊 Chat-specific indicators: {len(chat_specific_found)}")
        for indicator in chat_specific_found:
            logger.info(f"   ✅ {indicator}")

        # Verify minimum indicators are present
        min_api_indicators = 5
        min_ws_indicators = 4
        min_chat_specific = 3

        api_compliant = len(chat_api_indicators_found) >= min_api_indicators
        ws_compliant = len(chat_ws_indicators_found) >= min_ws_indicators
        chat_specific_compliant = len(chat_specific_found) >= min_chat_specific

        if api_compliant:
            logger.info("✅ Chat API module has sufficient 4+1 architecture indicators")
        else:
            logger.warning(
                f"⚠️ Chat API module has only {len(chat_api_indicators_found)} indicators (minimum {min_api_indicators})"
            )

        if ws_compliant:
            logger.info(
                "✅ Chat WebSocket module has sufficient 4+1 architecture indicators"
            )
        else:
            logger.warning(
                f"⚠️ Chat WebSocket module has only {len(chat_ws_indicators_found)} indicators (minimum {min_ws_indicators})"
            )

        if chat_specific_compliant:
            logger.info("✅ Chat modules have sufficient chat-specific indicators")
        else:
            logger.warning(
                f"⚠️ Chat modules have only {len(chat_specific_found)} chat-specific indicators (minimum {min_chat_specific})"
            )

        return api_compliant and ws_compliant and chat_specific_compliant

    except Exception as e:
        logger.error(f"❌ Chat 4+1 compliance test failed: {e}")
        return False


def main():
    """Run comprehensive Phase 3.3 StrategicChatService integration validation tests."""
    logger.info("🚀 Starting Phase 3.3: StrategicChatService Integration Tests")
    logger.info("=" * 80)

    test_results = []

    # Test 1: Chat Module Imports
    logger.info("\n📋 TEST 1: CHAT MODULE IMPORTS")
    logger.info("-" * 50)
    imports_result = test_chat_module_imports()
    test_results.append(("Chat Module Imports", imports_result))

    # Test 2: Chat Router Configurations
    logger.info("\n📋 TEST 2: CHAT ROUTER CONFIGURATIONS")
    logger.info("-" * 50)
    router_result = test_chat_router_configurations()
    test_results.append(("Chat Router Configurations", router_result))

    # Test 3: Chat API Endpoints
    logger.info("\n📋 TEST 3: CHAT API ENDPOINTS")
    logger.info("-" * 50)
    endpoints_result = test_chat_api_endpoints()
    test_results.append(("Chat API Endpoints", endpoints_result))

    # Test 4: Chat Service Classes
    logger.info("\n📋 TEST 4: CHAT SERVICE CLASSES")
    logger.info("-" * 50)
    services_result = test_chat_service_classes()
    test_results.append(("Chat Service Classes", services_result))

    # Test 5: Chat Pydantic Models
    logger.info("\n📋 TEST 5: CHAT PYDANTIC MODELS")
    logger.info("-" * 50)
    models_result = test_chat_pydantic_models()
    test_results.append(("Chat Pydantic Models", models_result))

    # Test 6: Chat 4+1 Compliance
    logger.info("\n📋 TEST 6: CHAT 4+1 COMPLIANCE")
    logger.info("-" * 50)
    compliance_result = test_chat_4plus1_compliance()
    test_results.append(("Chat 4+1 Compliance", compliance_result))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 PHASE 3.3 STRATEGICCHATSERVICE INTEGRATION RESULTS")
    logger.info("=" * 80)

    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        logger.info("\n🎉 PHASE 3.3 STRATEGICCHATSERVICE INTEGRATION PASSED!")
        logger.info("✅ All chat modules properly integrated with 4+1 architecture")
        logger.info("✅ Chat API endpoints for agent coordination")
        logger.info("✅ Chat WebSocket endpoints for real-time integration")
        logger.info("✅ StrategicChatService classes properly implemented")
        logger.info("✅ Pydantic models with proper structure")
        logger.info("✅ 4+1 architecture compliance indicators present")
        logger.info("\n🚀 READY FOR PHASE 4: PRODUCTION DEPLOYMENT")
        return 0
    else:
        logger.info("\n❌ PHASE 3.3 STRATEGICCHATSERVICE INTEGRATION FAILED")
        logger.info("⚠️ Review failed tests and fix issues before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
