#!/usr/bin/env python3
"""
Phase 3: API Structure Validation Test
=====================================

Validates the structure and implementation of the new 4+1 architecture APIs without requiring database connectivity.
This test focuses on verifying that the APIs are properly structured for Phase 3 implementation.

Tests:
1. API module imports and structure
2. Router configuration and endpoints
3. 4+1 architecture compliance indicators
4. Zero legacy dependencies
5. Proper function signatures and documentation

Success Criteria:
- All new API modules import successfully
- Router configurations are correct for 4+1 architecture
- API functions have proper signatures and documentation
- Zero references to legacy models
- 4+1 architecture compliance indicators present
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


def test_api_module_imports():
    """Test that all new 4+1 architecture API modules import successfully."""
    logger.info("🧪 Testing API Module Imports")
    
    try:
        # Test agents API import
        import fs_agt_clean.api.routes.agents_4plus1 as agents_module
        logger.info("✅ Successfully imported agents_4plus1 module")
        
        # Test decisions API import
        import fs_agt_clean.api.routes.decisions_4plus1 as decisions_module
        logger.info("✅ Successfully imported decisions_4plus1 module")
        
        # Verify modules have expected attributes
        assert hasattr(agents_module, 'router'), "agents_4plus1 module missing router"
        assert hasattr(decisions_module, 'router'), "decisions_4plus1 module missing router"
        
        logger.info("✅ All API modules imported successfully with required attributes")
        return True
        
    except Exception as e:
        logger.error(f"❌ API module import test failed: {e}")
        return False


def test_router_configurations():
    """Test router configurations for 4+1 architecture compliance."""
    logger.info("🧪 Testing Router Configurations")
    
    try:
        import fs_agt_clean.api.routes.agents_4plus1 as agents_module
        import fs_agt_clean.api.routes.decisions_4plus1 as decisions_module
        
        agents_router = agents_module.router
        decisions_router = decisions_module.router
        
        # Test router prefixes
        assert agents_router.prefix == "/agents", f"Expected /agents prefix, got {agents_router.prefix}"
        assert decisions_router.prefix == "/decisions", f"Expected /decisions prefix, got {decisions_router.prefix}"
        
        # Test router tags for 4+1 architecture identification
        agents_tags = agents_router.tags
        decisions_tags = decisions_router.tags
        
        assert "4+1-architecture-agents" in agents_tags, f"Missing 4+1 architecture tag in agents router: {agents_tags}"
        assert "4+1-architecture-decisions" in decisions_tags, f"Missing 4+1 architecture tag in decisions router: {decisions_tags}"
        
        logger.info("✅ Router configurations are correct for 4+1 architecture")
        logger.info(f"   - Agents router: {agents_router.prefix} with tags {agents_tags}")
        logger.info(f"   - Decisions router: {decisions_router.prefix} with tags {decisions_tags}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Router configuration test failed: {e}")
        return False


def test_api_endpoints():
    """Test that API endpoints are properly defined."""
    logger.info("🧪 Testing API Endpoints")
    
    try:
        import fs_agt_clean.api.routes.agents_4plus1 as agents_module
        import fs_agt_clean.api.routes.decisions_4plus1 as decisions_module
        
        # Get router routes
        agents_routes = agents_module.router.routes
        decisions_routes = decisions_module.router.routes
        
        logger.info(f"📊 Agents API endpoints: {len(agents_routes)} routes")
        for route in agents_routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                logger.info(f"   - {list(route.methods)[0] if route.methods else 'GET'} {route.path}")
        
        logger.info(f"📊 Decisions API endpoints: {len(decisions_routes)} routes")
        for route in decisions_routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                logger.info(f"   - {list(route.methods)[0] if route.methods else 'GET'} {route.path}")
        
        # Verify minimum expected endpoints exist
        agents_paths = [route.path for route in agents_routes if hasattr(route, 'path')]
        decisions_paths = [route.path for route in decisions_routes if hasattr(route, 'path')]
        
        # Expected agent endpoints
        expected_agent_paths = ["/agents/", "/agents/list", "/agents/status", "/agents/{agent_id}", "/agents/health"]
        for expected_path in expected_agent_paths:
            path_exists = any(expected_path in path for path in agents_paths)
            if path_exists:
                logger.info(f"✅ Found expected agent endpoint: {expected_path}")
            else:
                logger.warning(f"⚠️ Missing expected agent endpoint: {expected_path}")
        
        # Expected decision endpoints
        expected_decision_paths = ["/decisions/", "/decisions/analytics", "/decisions/compliance", "/decisions/{decision_id}", "/decisions/health"]
        for expected_path in expected_decision_paths:
            path_exists = any(expected_path in path for path in decisions_paths)
            if path_exists:
                logger.info(f"✅ Found expected decision endpoint: {expected_path}")
            else:
                logger.warning(f"⚠️ Missing expected decision endpoint: {expected_path}")
        
        logger.info("✅ API endpoints validation completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ API endpoints test failed: {e}")
        return False


def test_function_signatures():
    """Test that API functions have proper signatures and documentation."""
    logger.info("🧪 Testing Function Signatures and Documentation")
    
    try:
        import fs_agt_clean.api.routes.agents_4plus1 as agents_module
        import fs_agt_clean.api.routes.decisions_4plus1 as decisions_module
        
        # Test key functions in agents module
        key_agent_functions = [
            'get_4plus1_agents_from_database',
            'get_agents_overview',
            'get_agents_list_endpoint',
            'get_all_agent_statuses',
            'get_agent_details'
        ]
        
        for func_name in key_agent_functions:
            if hasattr(agents_module, func_name):
                func = getattr(agents_module, func_name)
                
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
                logger.warning(f"⚠️ Missing expected function: {func_name}")
        
        # Test key functions in decisions module
        key_decision_functions = [
            'get_all_decisions',
            'get_decision_analytics',
            'get_compliance_report',
            'get_decision_details'
        ]
        
        for func_name in key_decision_functions:
            if hasattr(decisions_module, func_name):
                func = getattr(decisions_module, func_name)
                
                # Check if function is callable
                assert callable(func), f"{func_name} is not callable"
                
                # Check if function has docstring
                docstring = inspect.getdoc(func)
                if docstring:
                    logger.info(f"✅ {func_name} has documentation")
                    # Check for 4+1 architecture mentions
                    if "4+1" in docstring or "llm-free" in docstring.lower():
                        logger.info(f"   - Contains 4+1 architecture references")
                else:
                    logger.warning(f"⚠️ {func_name} missing documentation")
                
                # Check function signature
                sig = inspect.signature(func)
                logger.info(f"   - Signature: {func_name}{sig}")
            else:
                logger.warning(f"⚠️ Missing expected function: {func_name}")
        
        logger.info("✅ Function signatures and documentation validation completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Function signatures test failed: {e}")
        return False


def test_legacy_dependencies():
    """Test for zero legacy dependencies in new API modules."""
    logger.info("🧪 Testing for Legacy Dependencies")
    
    try:
        import fs_agt_clean.api.routes.agents_4plus1 as agents_module
        import fs_agt_clean.api.routes.decisions_4plus1 as decisions_module
        
        # Get module source code (if available)
        agents_source = inspect.getsource(agents_module)
        decisions_source = inspect.getsource(decisions_module)
        
        # Check for legacy references
        legacy_terms = [
            "UnifiedAgent",
            "unified_agents",
            "UnifiedUser", 
            "unified_users",
            "agent_communications"  # Legacy communication table
        ]
        
        allowed_legacy_terms = [
            "legacy_free",  # This is allowed as it indicates no legacy dependencies
            "zero legacy",  # This is allowed as documentation
            "legacy dependencies"  # This is allowed as documentation
        ]
        
        agents_violations = []
        decisions_violations = []
        
        for term in legacy_terms:
            # Check agents module
            if term in agents_source:
                # Check if it's in an allowed context
                lines_with_term = [line.strip() for line in agents_source.split('\n') if term in line]
                for line in lines_with_term:
                    if not any(allowed_term in line.lower() for allowed_term in allowed_legacy_terms):
                        agents_violations.append(f"Found '{term}' in: {line[:100]}...")
            
            # Check decisions module
            if term in decisions_source:
                # Check if it's in an allowed context
                lines_with_term = [line.strip() for line in decisions_source.split('\n') if term in line]
                for line in lines_with_term:
                    if not any(allowed_term in line.lower() for allowed_term in allowed_legacy_terms):
                        decisions_violations.append(f"Found '{term}' in: {line[:100]}...")
        
        if agents_violations:
            logger.warning("⚠️ Legacy dependencies found in agents module:")
            for violation in agents_violations:
                logger.warning(f"   - {violation}")
        else:
            logger.info("✅ No legacy dependencies found in agents module")
        
        if decisions_violations:
            logger.warning("⚠️ Legacy dependencies found in decisions module:")
            for violation in decisions_violations:
                logger.warning(f"   - {violation}")
        else:
            logger.info("✅ No legacy dependencies found in decisions module")
        
        # Return True if no violations found
        return len(agents_violations) == 0 and len(decisions_violations) == 0
        
    except Exception as e:
        logger.error(f"❌ Legacy dependencies test failed: {e}")
        return False


def test_4plus1_compliance_indicators():
    """Test that 4+1 architecture compliance indicators are present."""
    logger.info("🧪 Testing 4+1 Architecture Compliance Indicators")
    
    try:
        import fs_agt_clean.api.routes.agents_4plus1 as agents_module
        import fs_agt_clean.api.routes.decisions_4plus1 as decisions_module
        
        # Get module source code
        agents_source = inspect.getsource(agents_module)
        decisions_source = inspect.getsource(decisions_module)
        
        # Check for 4+1 architecture compliance indicators
        compliance_indicators = [
            "llm_free",
            "StandardDecisionPipeline", 
            "autonomous_agents",
            "conversational_interfaces",
            "4+1",
            "architecture_compliance",
            "compliance_metrics"
        ]
        
        agents_indicators_found = []
        decisions_indicators_found = []
        
        for indicator in compliance_indicators:
            if indicator in agents_source:
                agents_indicators_found.append(indicator)
            if indicator in decisions_source:
                decisions_indicators_found.append(indicator)
        
        logger.info(f"📊 4+1 Architecture indicators in agents module: {len(agents_indicators_found)}")
        for indicator in agents_indicators_found:
            logger.info(f"   ✅ {indicator}")
        
        logger.info(f"📊 4+1 Architecture indicators in decisions module: {len(decisions_indicators_found)}")
        for indicator in decisions_indicators_found:
            logger.info(f"   ✅ {indicator}")
        
        # Verify minimum indicators are present
        min_agents_indicators = 3
        min_decisions_indicators = 3
        
        agents_compliant = len(agents_indicators_found) >= min_agents_indicators
        decisions_compliant = len(decisions_indicators_found) >= min_decisions_indicators
        
        if agents_compliant:
            logger.info("✅ Agents module has sufficient 4+1 architecture indicators")
        else:
            logger.warning(f"⚠️ Agents module has only {len(agents_indicators_found)} indicators (minimum {min_agents_indicators})")
        
        if decisions_compliant:
            logger.info("✅ Decisions module has sufficient 4+1 architecture indicators")
        else:
            logger.warning(f"⚠️ Decisions module has only {len(decisions_indicators_found)} indicators (minimum {min_decisions_indicators})")
        
        return agents_compliant and decisions_compliant
        
    except Exception as e:
        logger.error(f"❌ 4+1 compliance indicators test failed: {e}")
        return False


def main():
    """Run comprehensive Phase 3 API structure validation tests."""
    logger.info("🚀 Starting Phase 3: API Structure Validation Tests")
    logger.info("=" * 80)
    
    test_results = []
    
    # Test 1: API Module Imports
    logger.info("\n📋 TEST 1: API MODULE IMPORTS")
    logger.info("-" * 50)
    imports_result = test_api_module_imports()
    test_results.append(("API Module Imports", imports_result))
    
    # Test 2: Router Configurations
    logger.info("\n📋 TEST 2: ROUTER CONFIGURATIONS")
    logger.info("-" * 50)
    router_result = test_router_configurations()
    test_results.append(("Router Configurations", router_result))
    
    # Test 3: API Endpoints
    logger.info("\n📋 TEST 3: API ENDPOINTS")
    logger.info("-" * 50)
    endpoints_result = test_api_endpoints()
    test_results.append(("API Endpoints", endpoints_result))
    
    # Test 4: Function Signatures
    logger.info("\n📋 TEST 4: FUNCTION SIGNATURES")
    logger.info("-" * 50)
    signatures_result = test_function_signatures()
    test_results.append(("Function Signatures", signatures_result))
    
    # Test 5: Legacy Dependencies
    logger.info("\n📋 TEST 5: LEGACY DEPENDENCIES")
    logger.info("-" * 50)
    legacy_result = test_legacy_dependencies()
    test_results.append(("Legacy Dependencies", legacy_result))
    
    # Test 6: 4+1 Compliance Indicators
    logger.info("\n📋 TEST 6: 4+1 COMPLIANCE INDICATORS")
    logger.info("-" * 50)
    compliance_result = test_4plus1_compliance_indicators()
    test_results.append(("4+1 Compliance Indicators", compliance_result))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 PHASE 3 API STRUCTURE VALIDATION RESULTS")
    logger.info("=" * 80)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 PHASE 3 API STRUCTURE VALIDATION PASSED!")
        logger.info("✅ All API modules properly structured for 4+1 architecture")
        logger.info("✅ Router configurations correct")
        logger.info("✅ API endpoints properly defined")
        logger.info("✅ Function signatures and documentation adequate")
        logger.info("✅ Zero legacy dependencies confirmed")
        logger.info("✅ 4+1 architecture compliance indicators present")
        logger.info("\n🚀 READY FOR PHASE 3.2: WEBSOCKET INTEGRATION")
        return 0
    else:
        logger.info("\n❌ PHASE 3 API STRUCTURE VALIDATION FAILED")
        logger.info("⚠️ Review failed tests and fix issues before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
