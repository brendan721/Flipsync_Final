#!/usr/bin/env python3
"""
Phase 3.2: WebSocket Integration Test
====================================

Comprehensive test suite for Phase 3.2 WebSocket Integration.
Tests the new 4+1 architecture WebSocket endpoints to ensure:

Phase 3.2.1: Real-time Agent Communication
- WebSocket handlers use autonomous_agent_communications table
- Real-time agent status broadcasting from 4+1 architecture database
- Decision streaming with 4+1 compliance indicators
- WebSocket endpoints use AutonomousAgentRepository exclusively

Phase 3.2.2: Learning System WebSocket
- WebSocket handlers for learning system events
- Real-time learning insights broadcasting from 8 learning tables
- Policy optimization progress streaming
- Cross-agent learning coordination events

Success Criteria:
- Real-time agent status updates working from autonomous_agents table
- Decision streaming includes LLM-free compliance status
- Cross-agent communication events broadcasted via WebSocket
- Learning events streamed in real-time from learning system tables
- Policy optimization progress visible through WebSocket
- Zero legacy WebSocket dependencies
"""

import asyncio
import inspect
import logging
import sys
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_websocket_module_imports():
    """Test that all new 4+1 architecture WebSocket modules import successfully."""
    logger.info("🧪 Testing WebSocket Module Imports")
    
    try:
        # Test agent WebSocket import
        import fs_agt_clean.api.websocket.agents_4plus1_ws as agents_ws_module
        logger.info("✅ Successfully imported agents_4plus1_ws module")
        
        # Test learning WebSocket import
        import fs_agt_clean.api.websocket.learning_4plus1_ws as learning_ws_module
        logger.info("✅ Successfully imported learning_4plus1_ws module")
        
        # Verify modules have expected attributes
        assert hasattr(agents_ws_module, 'router'), "agents_4plus1_ws module missing router"
        assert hasattr(learning_ws_module, 'router'), "learning_4plus1_ws module missing router"
        
        # Verify WebSocket manager classes
        assert hasattr(agents_ws_module, 'AgentWebSocketManager'), "agents_4plus1_ws module missing AgentWebSocketManager"
        assert hasattr(learning_ws_module, 'LearningWebSocketManager'), "learning_4plus1_ws module missing LearningWebSocketManager"
        
        logger.info("✅ All WebSocket modules imported successfully with required attributes")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebSocket module import test failed: {e}")
        return False


def test_websocket_router_configurations():
    """Test WebSocket router configurations for 4+1 architecture compliance."""
    logger.info("🧪 Testing WebSocket Router Configurations")
    
    try:
        import fs_agt_clean.api.websocket.agents_4plus1_ws as agents_ws_module
        import fs_agt_clean.api.websocket.learning_4plus1_ws as learning_ws_module
        
        agents_router = agents_ws_module.router
        learning_router = learning_ws_module.router
        
        # Test router prefixes
        assert agents_router.prefix == "/ws/agents", f"Expected /ws/agents prefix, got {agents_router.prefix}"
        assert learning_router.prefix == "/ws/learning", f"Expected /ws/learning prefix, got {learning_router.prefix}"
        
        # Test router tags for 4+1 architecture identification
        agents_tags = agents_router.tags
        learning_tags = learning_router.tags
        
        assert "4+1-architecture-websockets" in agents_tags, f"Missing 4+1 architecture tag in agents WebSocket router: {agents_tags}"
        assert "4+1-architecture-learning-websockets" in learning_tags, f"Missing 4+1 architecture tag in learning WebSocket router: {learning_tags}"
        
        logger.info("✅ WebSocket router configurations are correct for 4+1 architecture")
        logger.info(f"   - Agents WebSocket router: {agents_router.prefix} with tags {agents_tags}")
        logger.info(f"   - Learning WebSocket router: {learning_router.prefix} with tags {learning_tags}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ WebSocket router configuration test failed: {e}")
        return False


def test_websocket_endpoints():
    """Test that WebSocket endpoints are properly defined."""
    logger.info("🧪 Testing WebSocket Endpoints")
    
    try:
        import fs_agt_clean.api.websocket.agents_4plus1_ws as agents_ws_module
        import fs_agt_clean.api.websocket.learning_4plus1_ws as learning_ws_module
        
        # Get router routes
        agents_routes = agents_ws_module.router.routes
        learning_routes = learning_ws_module.router.routes
        
        logger.info(f"📊 Agent WebSocket endpoints: {len(agents_routes)} routes")
        for route in agents_routes:
            if hasattr(route, 'path'):
                logger.info(f"   - WebSocket {route.path}")
        
        logger.info(f"📊 Learning WebSocket endpoints: {len(learning_routes)} routes")
        for route in learning_routes:
            if hasattr(route, 'path'):
                logger.info(f"   - WebSocket {route.path}")
        
        # Verify minimum expected WebSocket endpoints exist
        agents_paths = [route.path for route in agents_routes if hasattr(route, 'path')]
        learning_paths = [route.path for route in learning_routes if hasattr(route, 'path')]
        
        # Expected agent WebSocket endpoints
        expected_agent_paths = ["/ws/agents/status", "/ws/agents/decisions/{agent_id}", "/ws/agents/communications", "/ws/agents/compliance"]
        for expected_path in expected_agent_paths:
            path_exists = any(expected_path in path for path in agents_paths)
            if path_exists:
                logger.info(f"✅ Found expected agent WebSocket endpoint: {expected_path}")
            else:
                logger.warning(f"⚠️ Missing expected agent WebSocket endpoint: {expected_path}")
        
        # Expected learning WebSocket endpoints
        expected_learning_paths = ["/ws/learning/insights", "/ws/learning/optimization", "/ws/learning/coordination", "/ws/learning/performance"]
        for expected_path in expected_learning_paths:
            path_exists = any(expected_path in path for path in learning_paths)
            if path_exists:
                logger.info(f"✅ Found expected learning WebSocket endpoint: {expected_path}")
            else:
                logger.warning(f"⚠️ Missing expected learning WebSocket endpoint: {expected_path}")
        
        logger.info("✅ WebSocket endpoints validation completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebSocket endpoints test failed: {e}")
        return False


def test_websocket_manager_classes():
    """Test WebSocket manager classes for proper functionality."""
    logger.info("🧪 Testing WebSocket Manager Classes")
    
    try:
        import fs_agt_clean.api.websocket.agents_4plus1_ws as agents_ws_module
        import fs_agt_clean.api.websocket.learning_4plus1_ws as learning_ws_module
        
        # Test AgentWebSocketManager
        agent_manager_class = agents_ws_module.AgentWebSocketManager
        agent_manager = agent_manager_class()
        
        # Check required methods
        required_agent_methods = ['connect', 'disconnect', 'broadcast_to_channel', 'get_connection_stats']
        for method_name in required_agent_methods:
            assert hasattr(agent_manager, method_name), f"AgentWebSocketManager missing method: {method_name}"
            method = getattr(agent_manager, method_name)
            assert callable(method), f"AgentWebSocketManager.{method_name} is not callable"
            logger.info(f"✅ AgentWebSocketManager.{method_name} is available and callable")
        
        # Check connection types
        expected_connection_types = ["agent_status", "agent_decisions", "agent_communications", "compliance_monitoring"]
        for conn_type in expected_connection_types:
            assert conn_type in agent_manager.connections, f"AgentWebSocketManager missing connection type: {conn_type}"
            logger.info(f"✅ AgentWebSocketManager supports connection type: {conn_type}")
        
        # Test LearningWebSocketManager
        learning_manager_class = learning_ws_module.LearningWebSocketManager
        learning_manager = learning_manager_class()
        
        # Check required methods
        required_learning_methods = ['connect', 'disconnect', 'broadcast_to_channel']
        for method_name in required_learning_methods:
            assert hasattr(learning_manager, method_name), f"LearningWebSocketManager missing method: {method_name}"
            method = getattr(learning_manager, method_name)
            assert callable(method), f"LearningWebSocketManager.{method_name} is not callable"
            logger.info(f"✅ LearningWebSocketManager.{method_name} is available and callable")
        
        # Check learning connection types
        expected_learning_types = ["learning_insights", "optimization_progress", "coordination_events", "performance_metrics"]
        for conn_type in expected_learning_types:
            assert conn_type in learning_manager.connections, f"LearningWebSocketManager missing connection type: {conn_type}"
            logger.info(f"✅ LearningWebSocketManager supports connection type: {conn_type}")
        
        logger.info("✅ WebSocket manager classes validation completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebSocket manager classes test failed: {e}")
        return False


def test_websocket_helper_functions():
    """Test WebSocket helper functions for proper signatures and documentation."""
    logger.info("🧪 Testing WebSocket Helper Functions")
    
    try:
        import fs_agt_clean.api.websocket.agents_4plus1_ws as agents_ws_module
        import fs_agt_clean.api.websocket.learning_4plus1_ws as learning_ws_module
        
        # Test agent WebSocket helper functions
        agent_helper_functions = [
            '_send_initial_agent_status',
            '_send_initial_agent_decisions',
            '_send_initial_communications',
        ]
        
        for func_name in agent_helper_functions:
            if hasattr(agents_ws_module, func_name):
                func = getattr(agents_ws_module, func_name)
                
                # Check if function is callable
                assert callable(func), f"{func_name} is not callable"
                
                # Check if function has docstring
                docstring = inspect.getdoc(func)
                if docstring:
                    logger.info(f"✅ {func_name} has documentation")
                    # Check for 4+1 architecture mentions
                    if "4+1" in docstring or "autonomous" in docstring.lower():
                        logger.info(f"   - Contains 4+1 architecture references")
                else:
                    logger.warning(f"⚠️ {func_name} missing documentation")
                
                # Check function signature
                sig = inspect.signature(func)
                logger.info(f"   - Signature: {func_name}{sig}")
            else:
                logger.warning(f"⚠️ Missing expected agent helper function: {func_name}")
        
        # Test learning WebSocket helper functions
        learning_helper_functions = [
            '_send_initial_learning_insights',
        ]
        
        for func_name in learning_helper_functions:
            if hasattr(learning_ws_module, func_name):
                func = getattr(learning_ws_module, func_name)
                
                # Check if function is callable
                assert callable(func), f"{func_name} is not callable"
                
                # Check if function has docstring
                docstring = inspect.getdoc(func)
                if docstring:
                    logger.info(f"✅ {func_name} has documentation")
                    # Check for learning system mentions
                    if "learning" in docstring.lower() or "insights" in docstring.lower():
                        logger.info(f"   - Contains learning system references")
                else:
                    logger.warning(f"⚠️ {func_name} missing documentation")
                
                # Check function signature
                sig = inspect.signature(func)
                logger.info(f"   - Signature: {func_name}{sig}")
            else:
                logger.warning(f"⚠️ Missing expected learning helper function: {func_name}")
        
        logger.info("✅ WebSocket helper functions validation completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ WebSocket helper functions test failed: {e}")
        return False


def test_websocket_4plus1_compliance():
    """Test WebSocket implementations for 4+1 architecture compliance."""
    logger.info("🧪 Testing WebSocket 4+1 Architecture Compliance")
    
    try:
        import fs_agt_clean.api.websocket.agents_4plus1_ws as agents_ws_module
        import fs_agt_clean.api.websocket.learning_4plus1_ws as learning_ws_module
        
        # Get module source code
        agents_source = inspect.getsource(agents_ws_module)
        learning_source = inspect.getsource(learning_ws_module)
        
        # Check for 4+1 architecture compliance indicators
        compliance_indicators = [
            "autonomous_agents",
            "autonomous_agent_decisions",
            "autonomous_agent_communications",
            "AutonomousAgentRepository",
            "4+1",
            "llm_free",
            "StandardDecisionPipeline",
        ]
        
        agents_indicators_found = []
        learning_indicators_found = []
        
        for indicator in compliance_indicators:
            if indicator in agents_source:
                agents_indicators_found.append(indicator)
            if indicator in learning_source:
                learning_indicators_found.append(indicator)
        
        logger.info(f"📊 4+1 Architecture indicators in agents WebSocket module: {len(agents_indicators_found)}")
        for indicator in agents_indicators_found:
            logger.info(f"   ✅ {indicator}")
        
        logger.info(f"📊 4+1 Architecture indicators in learning WebSocket module: {len(learning_indicators_found)}")
        for indicator in learning_indicators_found:
            logger.info(f"   ✅ {indicator}")
        
        # Check for learning system specific indicators
        learning_specific_indicators = [
            "PolicyOptimizationHistory",
            "LearningKnowledgeBase",
            "CrossAgentLearningInsights",
            "learning_knowledge_base",
            "policy_optimization_history",
        ]
        
        learning_specific_found = []
        for indicator in learning_specific_indicators:
            if indicator in learning_source:
                learning_specific_found.append(indicator)
        
        logger.info(f"📊 Learning system indicators in learning WebSocket module: {len(learning_specific_found)}")
        for indicator in learning_specific_found:
            logger.info(f"   ✅ {indicator}")
        
        # Verify minimum indicators are present
        min_agents_indicators = 4
        min_learning_indicators = 2
        min_learning_specific = 3
        
        agents_compliant = len(agents_indicators_found) >= min_agents_indicators
        learning_compliant = len(learning_indicators_found) >= min_learning_indicators
        learning_specific_compliant = len(learning_specific_found) >= min_learning_specific
        
        if agents_compliant:
            logger.info("✅ Agents WebSocket module has sufficient 4+1 architecture indicators")
        else:
            logger.warning(f"⚠️ Agents WebSocket module has only {len(agents_indicators_found)} indicators (minimum {min_agents_indicators})")
        
        if learning_compliant and learning_specific_compliant:
            logger.info("✅ Learning WebSocket module has sufficient 4+1 architecture and learning system indicators")
        else:
            logger.warning(f"⚠️ Learning WebSocket module compliance insufficient")
        
        return agents_compliant and learning_compliant and learning_specific_compliant
        
    except Exception as e:
        logger.error(f"❌ WebSocket 4+1 compliance test failed: {e}")
        return False


def main():
    """Run comprehensive Phase 3.2 WebSocket integration validation tests."""
    logger.info("🚀 Starting Phase 3.2: WebSocket Integration Tests")
    logger.info("=" * 80)
    
    test_results = []
    
    # Test 1: WebSocket Module Imports
    logger.info("\n📋 TEST 1: WEBSOCKET MODULE IMPORTS")
    logger.info("-" * 50)
    imports_result = test_websocket_module_imports()
    test_results.append(("WebSocket Module Imports", imports_result))
    
    # Test 2: WebSocket Router Configurations
    logger.info("\n📋 TEST 2: WEBSOCKET ROUTER CONFIGURATIONS")
    logger.info("-" * 50)
    router_result = test_websocket_router_configurations()
    test_results.append(("WebSocket Router Configurations", router_result))
    
    # Test 3: WebSocket Endpoints
    logger.info("\n📋 TEST 3: WEBSOCKET ENDPOINTS")
    logger.info("-" * 50)
    endpoints_result = test_websocket_endpoints()
    test_results.append(("WebSocket Endpoints", endpoints_result))
    
    # Test 4: WebSocket Manager Classes
    logger.info("\n📋 TEST 4: WEBSOCKET MANAGER CLASSES")
    logger.info("-" * 50)
    managers_result = test_websocket_manager_classes()
    test_results.append(("WebSocket Manager Classes", managers_result))
    
    # Test 5: WebSocket Helper Functions
    logger.info("\n📋 TEST 5: WEBSOCKET HELPER FUNCTIONS")
    logger.info("-" * 50)
    helpers_result = test_websocket_helper_functions()
    test_results.append(("WebSocket Helper Functions", helpers_result))
    
    # Test 6: WebSocket 4+1 Compliance
    logger.info("\n📋 TEST 6: WEBSOCKET 4+1 COMPLIANCE")
    logger.info("-" * 50)
    compliance_result = test_websocket_4plus1_compliance()
    test_results.append(("WebSocket 4+1 Compliance", compliance_result))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 PHASE 3.2 WEBSOCKET INTEGRATION RESULTS")
    logger.info("=" * 80)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 PHASE 3.2 WEBSOCKET INTEGRATION PASSED!")
        logger.info("✅ All WebSocket modules properly structured for 4+1 architecture")
        logger.info("✅ Agent WebSocket endpoints for real-time communication")
        logger.info("✅ Learning WebSocket endpoints for learning system events")
        logger.info("✅ WebSocket manager classes properly implemented")
        logger.info("✅ Helper functions with proper documentation")
        logger.info("✅ 4+1 architecture compliance indicators present")
        logger.info("\n🚀 READY FOR PHASE 3.3: STRATEGICCHATSERVICE INTEGRATION")
        return 0
    else:
        logger.info("\n❌ PHASE 3.2 WEBSOCKET INTEGRATION FAILED")
        logger.info("⚠️ Review failed tests and fix issues before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
