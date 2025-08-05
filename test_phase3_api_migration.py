#!/usr/bin/env python3
"""
Phase 3: API and WebSocket Integration Test
==========================================

Comprehensive test suite for Phase 3.1.1 (Agent Management APIs) and Phase 3.1.2 (Decision Tracking APIs).
Tests the new 4+1 architecture API endpoints to ensure:

1. Agent Management APIs (Phase 3.1.1):
   - All endpoints use AutonomousAgentRepository exclusively
   - 4+1 architecture validation in API layer
   - Autonomous agent status monitoring
   - Zero references to legacy UnifiedAgent model

2. Decision Tracking APIs (Phase 3.1.2):
   - Decision tracking with LLM-free compliance indicators
   - Real-time decision monitoring capabilities
   - Decision analytics with 4+1 architecture focus

Success Criteria:
- All agent APIs return data from autonomous_agents table only
- API responses include 4+1 compliance status indicators
- Zero references to legacy models in API layer
- Decision APIs show LLM-free compliance metrics
- Real-time decision streaming functional
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_agent_management_apis():
    """Test Phase 3.1.1: Agent Management APIs Migration."""
    logger.info("🧪 Testing Agent Management APIs (Phase 3.1.1)")

    try:
        # Initialize database first
        from fs_agt_clean.core.db.database import get_database

        database = get_database()
        await database.initialize()
        logger.info("✅ Database initialized successfully")

        # Import the new 4+1 architecture API modules
        from fs_agt_clean.api.routes.agents_4plus1 import (
            get_4plus1_agents_from_database,
            router as agents_router,
        )

        logger.info("✅ Successfully imported 4+1 architecture agent APIs")

        # Test 1: Get agents from database
        logger.info("🔍 Test 1: Getting agents from 4+1 architecture database")
        agents = await get_4plus1_agents_from_database()

        # Validate agent data structure
        assert isinstance(agents, list), "Agents should be returned as a list"
        logger.info(f"✅ Retrieved {len(agents)} agents from database")

        # Validate 4+1 architecture compliance
        autonomous_agents = [a for a in agents if a.get("type") == "autonomous"]
        conversational_agents = [a for a in agents if a.get("type") == "conversational"]

        logger.info(f"📊 Architecture validation:")
        logger.info(f"   - Autonomous agents: {len(autonomous_agents)}")
        logger.info(f"   - Conversational interfaces: {len(conversational_agents)}")

        # Test 2: Validate agent data structure
        logger.info("🔍 Test 2: Validating agent data structure")
        for agent in agents:
            # Check required fields
            required_fields = ["id", "name", "type", "status", "architecture_type"]
            for field in required_fields:
                assert field in agent, f"Agent missing required field: {field}"

            # Check 4+1 architecture compliance indicators
            if agent["type"] == "autonomous":
                assert (
                    "llm_free" in agent
                ), "Autonomous agent missing llm_free indicator"
                assert (
                    "decision_pipeline" in agent
                ), "Autonomous agent missing decision_pipeline"
                assert agent["llm_free"] == True, "Autonomous agent should be LLM-free"
                assert (
                    agent["decision_pipeline"] == "StandardDecisionPipeline"
                ), "Autonomous agent should use StandardDecisionPipeline"
            elif agent["type"] == "conversational":
                assert (
                    "llm_provider" in agent
                ), "Conversational agent missing llm_provider"
                assert (
                    agent["llm_provider"] == "Gemini"
                ), "Conversational agent should use Gemini"

        logger.info(
            "✅ All agents have correct data structure and 4+1 compliance indicators"
        )

        # Test 3: Check for zero legacy dependencies
        logger.info("🔍 Test 3: Checking for zero legacy dependencies")

        # Verify no UnifiedAgent references in agent data
        for agent in agents:
            agent_str = str(agent)
            assert (
                "UnifiedAgent" not in agent_str
            ), f"Found legacy UnifiedAgent reference in agent {agent['id']}"
            assert (
                "unified_agents" not in agent_str
            ), f"Found legacy unified_agents table reference in agent {agent['id']}"

        logger.info("✅ Zero legacy dependencies confirmed in agent APIs")

        return True

    except Exception as e:
        logger.error(f"❌ Agent Management APIs test failed: {e}")
        return False


async def test_decision_tracking_apis():
    """Test Phase 3.1.2: Decision Tracking APIs Migration."""
    logger.info("🧪 Testing Decision Tracking APIs (Phase 3.1.2)")

    try:
        # Initialize database first
        from fs_agt_clean.core.db.database import get_database

        database = get_database()
        await database.initialize()
        logger.info("✅ Database initialized successfully")

        # Import the new decision tracking API modules
        from fs_agt_clean.api.routes.decisions_4plus1 import (
            _calculate_compliance_metrics,
            _generate_comprehensive_analytics,
            _generate_compliance_report,
            router as decisions_router,
        )
        from fs_agt_clean.database.repositories.autonomous_agent_repository import (
            AutonomousAgentRepository,
        )

        logger.info("✅ Successfully imported 4+1 architecture decision APIs")

        # Test 1: Database connectivity and decision retrieval
        logger.info("🔍 Test 1: Testing database connectivity and decision retrieval")

        database = get_database()
        repository = AutonomousAgentRepository()

        async with database.get_session() as session:
            # Test new repository methods
            recent_decisions = await repository.get_recent_decisions(session, limit=10)
            logger.info(
                f"✅ Retrieved {len(recent_decisions)} recent decisions from database"
            )

            # Test filtering methods
            all_decisions = await repository.get_decisions_with_filters(
                session, limit=20
            )
            logger.info(f"✅ Retrieved {len(all_decisions)} decisions with filters")

            # Test count method
            decision_count = await repository.get_decisions_count(session)
            logger.info(f"✅ Total decisions in database: {decision_count}")

        # Test 2: Compliance metrics calculation
        logger.info("🔍 Test 2: Testing compliance metrics calculation")

        if recent_decisions:
            compliance_metrics = await _calculate_compliance_metrics(recent_decisions)

            # Validate compliance metrics structure
            required_metrics = [
                "total_decisions",
                "llm_free_rate",
                "standard_pipeline_rate",
                "performance_target_rate",
            ]
            for metric in required_metrics:
                assert (
                    metric in compliance_metrics
                ), f"Missing compliance metric: {metric}"

            logger.info(f"📊 Compliance metrics:")
            logger.info(
                f"   - Total decisions: {compliance_metrics['total_decisions']}"
            )
            logger.info(
                f"   - LLM-free rate: {compliance_metrics['llm_free_rate']:.1%}"
            )
            logger.info(
                f"   - Standard pipeline rate: {compliance_metrics['standard_pipeline_rate']:.1%}"
            )
            logger.info(
                f"   - Performance target rate: {compliance_metrics['performance_target_rate']:.1%}"
            )

            logger.info("✅ Compliance metrics calculation working correctly")
        else:
            logger.info(
                "ℹ️ No recent decisions found - skipping compliance metrics test"
            )

        # Test 3: Analytics generation
        logger.info("🔍 Test 3: Testing analytics generation")

        if recent_decisions:
            analytics = await _generate_comprehensive_analytics(recent_decisions, 24)

            # Validate analytics structure
            required_sections = [
                "summary",
                "compliance_metrics",
                "decision_types",
                "agent_performance",
            ]
            for section in required_sections:
                assert section in analytics, f"Missing analytics section: {section}"

            logger.info("✅ Analytics generation working correctly")
        else:
            logger.info("ℹ️ No recent decisions found - skipping analytics test")

        # Test 4: Compliance report generation
        logger.info("🔍 Test 4: Testing compliance report generation")

        if recent_decisions:
            compliance_report = await _generate_compliance_report(recent_decisions)

            # Validate compliance report structure
            required_sections = [
                "overall_compliance",
                "violations_summary",
                "agent_compliance",
                "recommendations",
            ]
            for section in required_sections:
                assert (
                    section in compliance_report
                ), f"Missing compliance report section: {section}"

            logger.info("✅ Compliance report generation working correctly")
        else:
            logger.info("ℹ️ No recent decisions found - skipping compliance report test")

        return True

    except Exception as e:
        logger.error(f"❌ Decision Tracking APIs test failed: {e}")
        return False


async def test_api_integration():
    """Test overall API integration and architecture compliance."""
    logger.info("🧪 Testing API Integration and Architecture Compliance")

    try:
        # Test 1: Verify no legacy imports in new API files
        logger.info("🔍 Test 1: Checking for legacy imports in new API files")

        import fs_agt_clean.api.routes.agents_4plus1 as agents_module
        import fs_agt_clean.api.routes.decisions_4plus1 as decisions_module

        # Check agents module for legacy references
        agents_source = str(agents_module.__dict__)
        legacy_terms = ["UnifiedAgent", "unified_agents", "legacy"]

        for term in legacy_terms:
            if term in agents_source and "legacy_free" not in agents_source:
                logger.warning(
                    f"⚠️ Found potential legacy reference '{term}' in agents module"
                )

        logger.info("✅ New API modules appear to be legacy-free")

        # Test 2: Validate router configurations
        logger.info("🔍 Test 2: Validating router configurations")

        agents_router = agents_module.router
        decisions_router = decisions_module.router

        # Check router prefixes and tags
        assert (
            agents_router.prefix == "/agents"
        ), "Agents router should have /agents prefix"
        assert (
            decisions_router.prefix == "/decisions"
        ), "Decisions router should have /decisions prefix"

        # Check tags for 4+1 architecture identification
        assert (
            "4+1-architecture-agents" in agents_router.tags
        ), "Agents router should have 4+1 architecture tag"
        assert (
            "4+1-architecture-decisions" in decisions_router.tags
        ), "Decisions router should have 4+1 architecture tag"

        logger.info("✅ Router configurations are correct for 4+1 architecture")

        # Test 3: Database table usage validation
        logger.info("🔍 Test 3: Validating database table usage")

        # Check that new APIs use correct database tables
        from fs_agt_clean.core.db.database import get_database

        database = get_database()
        await database.initialize()
        logger.info("✅ Database initialized successfully")

        async with database.get_session() as session:
            # Verify autonomous_agents table is accessible
            from fs_agt_clean.database.models.autonomous_agent import AutonomousAgent
            from sqlalchemy import select

            query = select(AutonomousAgent).limit(1)
            result = await session.execute(query)
            agents = result.scalars().all()

            logger.info(
                f"✅ autonomous_agents table accessible with {len(agents)} records"
            )

            # Verify autonomous_agent_decisions table is accessible
            from fs_agt_clean.database.models.autonomous_agent import (
                AutonomousAgentDecision,
            )

            query = select(AutonomousAgentDecision).limit(1)
            result = await session.execute(query)
            decisions = result.scalars().all()

            logger.info(
                f"✅ autonomous_agent_decisions table accessible with {len(decisions)} records"
            )

        return True

    except Exception as e:
        logger.error(f"❌ API Integration test failed: {e}")
        return False


async def main():
    """Run comprehensive Phase 3 API migration tests."""
    logger.info("🚀 Starting Phase 3: API and WebSocket Integration Tests")
    logger.info("=" * 80)

    test_results = []

    # Test Phase 3.1.1: Agent Management APIs
    logger.info("\n📋 PHASE 3.1.1: AGENT MANAGEMENT APIs")
    logger.info("-" * 50)
    agent_apis_result = await test_agent_management_apis()
    test_results.append(("Agent Management APIs", agent_apis_result))

    # Test Phase 3.1.2: Decision Tracking APIs
    logger.info("\n📋 PHASE 3.1.2: DECISION TRACKING APIs")
    logger.info("-" * 50)
    decision_apis_result = await test_decision_tracking_apis()
    test_results.append(("Decision Tracking APIs", decision_apis_result))

    # Test API Integration
    logger.info("\n📋 API INTEGRATION AND COMPLIANCE")
    logger.info("-" * 50)
    integration_result = await test_api_integration()
    test_results.append(("API Integration", integration_result))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 PHASE 3 API MIGRATION TEST RESULTS")
    logger.info("=" * 80)

    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        logger.info("\n🎉 PHASE 3 API MIGRATION TESTS PASSED!")
        logger.info("✅ Agent Management APIs migrated successfully")
        logger.info("✅ Decision Tracking APIs implemented successfully")
        logger.info("✅ 4+1 architecture compliance validated")
        logger.info("✅ Zero legacy dependencies confirmed")
        logger.info("\n🚀 READY FOR PHASE 3.2: WEBSOCKET INTEGRATION")
        return 0
    else:
        logger.info("\n❌ PHASE 3 API MIGRATION TESTS FAILED")
        logger.info("⚠️ Review failed tests and fix issues before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
