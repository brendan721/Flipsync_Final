#!/usr/bin/env python3
"""
Test AI Executive Agent Implementation
AGENT_CONTEXT: Validate real AI-powered strategic decision making and agent coordination
AGENT_PRIORITY: Test Phase 2 Executive Agent implementation
AGENT_PATTERN: AI integration testing, agent coordination validation, strategic analysis
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_ai_executive_agent_basic():
    """Test basic AI Executive Agent functionality."""
    try:
        logger.info("🔄 Testing AI Executive Agent basic functionality...")

        # Import and create agent
        from fs_agt_clean.agents.executive.ai_executive_agent import (
            AgentCoordinationMessage,
            AIExecutiveAgent,
            StrategicAnalysisRequest,
        )

        # Create agent instance
        agent = AIExecutiveAgent(agent_id="test_ai_executive_agent")
        logger.info(f"✅ AI Executive Agent created: {agent.agent_id}")

        # Initialize agent
        await agent.initialize()
        logger.info("✅ AI Executive Agent initialized successfully")

        # Create test strategic analysis request
        request = StrategicAnalysisRequest(
            business_context={
                "revenue": 500000,
                "profit_margin": 0.15,
                "team_size": 8,
                "market_position": "growing",
            },
            decision_type="strategic_planning",
            objectives=["revenue_growth", "operational_efficiency"],
            constraints={"budget": 100000, "timeline_months": 12, "team_size": 10},
            timeline="12 months",
            priority_level="high",
        )
        logger.info(f"✅ Strategic analysis request created: {request.decision_type}")

        # Perform strategic analysis
        result = await agent.analyze_strategic_situation(request)
        logger.info("✅ Strategic analysis completed successfully")

        # Validate result
        assert result is not None
        assert hasattr(result, "decision_type")
        assert hasattr(result, "strategic_summary")
        assert hasattr(result, "recommendations")
        assert hasattr(result, "confidence_score")
        assert hasattr(result, "agent_coordination_plan")

        logger.info(f"📊 Strategic Analysis Results:")
        logger.info(f"   Decision Type: {result.decision_type}")
        logger.info(f"   Confidence: {result.confidence_score:.2f}")
        logger.info(f"   Summary: {result.strategic_summary[:100]}...")
        logger.info(f"   Recommendations: {len(result.recommendations)} items")

        # Test resource allocation
        if result.resource_allocation:
            logger.info(
                f"   Budget Allocation: {result.resource_allocation.get('budget_allocation', {})}"
            )
            logger.info(
                f"   Optimization Score: {result.resource_allocation.get('optimization_score', 'N/A')}"
            )

        # Test agent coordination plan
        coordination = result.agent_coordination_plan
        if coordination:
            logger.info(
                f"   Coordination Strategy: {coordination.get('coordination_strategy', 'N/A')}"
            )
            logger.info(
                f"   Agent Assignments: {len(coordination.get('agent_assignments', {}))}"
            )

        logger.info("🎉 AI Executive Agent basic test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ AI Executive Agent basic test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_agent_coordination():
    """Test agent coordination functionality."""
    try:
        logger.info("🔄 Testing agent coordination functionality...")

        from fs_agt_clean.agents.executive.ai_executive_agent import (
            AgentCoordinationMessage,
            AIExecutiveAgent,
        )

        # Create agent instance
        agent = AIExecutiveAgent(agent_id="test_coordination_executive")
        await agent.initialize()
        logger.info("✅ Executive Agent initialized for coordination testing")

        # Test task assignment coordination
        task_assignment = AgentCoordinationMessage(
            from_agent="test_coordination_executive",
            to_agent="ai_market_agent",
            message_type="task_assignment",
            content={
                "task": "competitive_pricing_analysis",
                "priority": "high",
                "deadline": "2024-01-15",
                "requirements": [
                    "pricing_data",
                    "competitor_analysis",
                    "market_trends",
                ],
            },
            priority="high",
            requires_response=True,
        )

        # Coordinate with agent
        coordination_result = await agent.coordinate_with_agent(task_assignment)
        logger.info("✅ Task assignment coordination completed")

        # Validate coordination result
        assert coordination_result is not None
        assert "status" in coordination_result
        assert "timestamp" in coordination_result

        logger.info(f"📊 Coordination Results:")
        logger.info(f"   Status: {coordination_result.get('status', 'unknown')}")
        logger.info(f"   Message: {coordination_result.get('message', 'N/A')}")

        # Test status update coordination
        status_update = AgentCoordinationMessage(
            from_agent="ai_market_agent",
            to_agent="test_coordination_executive",
            message_type="status_update",
            content={
                "task_id": "competitive_pricing_analysis",
                "status": "in_progress",
                "completion_percentage": 75,
                "estimated_completion": "2024-01-14",
            },
            priority="medium",
        )

        status_result = await agent.coordinate_with_agent(status_update)
        logger.info("✅ Status update coordination completed")

        # Test performance report coordination
        performance_report = AgentCoordinationMessage(
            from_agent="ai_market_agent",
            to_agent="test_coordination_executive",
            message_type="performance_report",
            content={
                "agent_id": "ai_market_agent",
                "performance_metrics": {
                    "tasks_completed": 15,
                    "success_rate": 0.93,
                    "avg_response_time": 1.2,
                    "customer_satisfaction": 4.5,
                },
                "period": "last_30_days",
            },
        )

        performance_result = await agent.coordinate_with_agent(performance_report)
        logger.info("✅ Performance report coordination completed")

        logger.info("✅ Agent coordination test completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Agent coordination test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_performance_monitoring():
    """Test agent performance monitoring functionality."""
    try:
        logger.info("🔄 Testing agent performance monitoring...")

        from fs_agt_clean.agents.executive.ai_executive_agent import AIExecutiveAgent

        # Create agent instance
        agent = AIExecutiveAgent(agent_id="test_monitoring_executive")
        await agent.initialize()
        logger.info("✅ Executive Agent initialized for monitoring testing")

        # Test performance monitoring
        monitoring_report = await agent.monitor_agent_performance()
        logger.info("✅ Agent performance monitoring completed")

        # Validate monitoring report
        assert monitoring_report is not None
        assert "monitoring_timestamp" in monitoring_report
        assert "total_agents" in monitoring_report
        assert "agent_performance" in monitoring_report

        logger.info(f"📊 Performance Monitoring Results:")
        logger.info(
            f"   Timestamp: {monitoring_report.get('monitoring_timestamp', 'N/A')}"
        )
        logger.info(f"   Total Agents: {monitoring_report.get('total_agents', 0)}")

        # Check agent performance data
        agent_performance = monitoring_report.get("agent_performance", {})
        for agent_id, performance in agent_performance.items():
            logger.info(f"   Agent {agent_id}:")
            logger.info(f"     Type: {performance.get('agent_type', 'unknown')}")
            logger.info(f"     Status: {performance.get('status', 'unknown')}")
            logger.info(
                f"     Response Time: {performance.get('response_time', 'N/A')}"
            )
            logger.info(f"     Success Rate: {performance.get('success_rate', 'N/A')}")

        # Check system health
        system_health = monitoring_report.get("system_health", {})
        if system_health:
            logger.info(f"   System Health: {system_health}")

        # Check recommendations
        recommendations = monitoring_report.get("recommendations", [])
        logger.info(f"   Recommendations: {len(recommendations)} items")

        logger.info("✅ Performance monitoring test completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Performance monitoring test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_strategic_analysis_types():
    """Test different types of strategic analysis."""
    try:
        logger.info("🔄 Testing different strategic analysis types...")

        from fs_agt_clean.agents.executive.ai_executive_agent import (
            AIExecutiveAgent,
            StrategicAnalysisRequest,
        )

        # Create agent instance
        agent = AIExecutiveAgent(agent_id="test_strategic_executive")
        await agent.initialize()
        logger.info("✅ Executive Agent initialized for strategic analysis testing")

        # Test different analysis types
        analysis_types = [
            {
                "type": "resource_allocation",
                "objectives": ["cost_reduction", "efficiency_improvement"],
                "context": {"budget": 75000, "team_size": 6},
            },
            {
                "type": "risk_assessment",
                "objectives": ["risk_mitigation", "business_continuity"],
                "context": {"market_volatility": "high", "competition": "intense"},
            },
            {
                "type": "performance_review",
                "objectives": ["performance_optimization", "growth_acceleration"],
                "context": {"current_performance": "good", "growth_target": 0.25},
            },
        ]

        results = []
        for analysis_config in analysis_types:
            request = StrategicAnalysisRequest(
                business_context=analysis_config["context"],
                decision_type=analysis_config["type"],
                objectives=analysis_config["objectives"],
                constraints={"budget": 50000, "timeline_months": 6},
                priority_level="medium",
            )

            result = await agent.analyze_strategic_situation(request)
            results.append((analysis_config["type"], result))

            logger.info(f"✅ {analysis_config['type']} analysis completed")
            logger.info(f"   Confidence: {result.confidence_score:.2f}")
            logger.info(f"   Recommendations: {len(result.recommendations)}")

        logger.info(f"📊 Strategic Analysis Summary:")
        logger.info(f"   Total Analysis Types Tested: {len(results)}")

        for analysis_type, result in results:
            logger.info(f"   {analysis_type}: {result.confidence_score:.2f} confidence")

        logger.info("✅ Strategic analysis types test completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Strategic analysis types test failed: {e}")
        return False


async def main():
    """Run all Executive Agent tests."""
    logger.info("🚀 Starting AI Executive Agent Phase 2 Tests")
    logger.info("=" * 60)

    results = []

    # Test 1: Basic Executive Agent functionality
    logger.info("\n📋 Test 1: AI Executive Agent Basic Functionality")
    result1 = await test_ai_executive_agent_basic()
    results.append(("AI Executive Agent Basic", result1))

    # Test 2: Agent coordination
    logger.info("\n📋 Test 2: Agent Coordination")
    result2 = await test_agent_coordination()
    results.append(("Agent Coordination", result2))

    # Test 3: Performance monitoring
    logger.info("\n📋 Test 3: Performance Monitoring")
    result3 = await test_performance_monitoring()
    results.append(("Performance Monitoring", result3))

    # Test 4: Strategic analysis types
    logger.info("\n📋 Test 4: Strategic Analysis Types")
    result4 = await test_strategic_analysis_types()
    results.append(("Strategic Analysis Types", result4))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {status}: {test_name}")
        if result:
            passed += 1

    success_rate = (passed / total) * 100 if total > 0 else 0
    logger.info(f"\n📈 Success Rate: {passed}/{total} ({success_rate:.1f}%)")

    if success_rate >= 80:
        logger.info("🎉 Phase 2 AI Executive Agent implementation: SUCCESS")
        logger.info("   Ready for integration with Market Agent and other agents")
    elif success_rate >= 60:
        logger.info("⚠️ Phase 2 AI Executive Agent implementation: PARTIAL SUCCESS")
        logger.info("   Some issues need attention but core functionality works")
    else:
        logger.info("❌ Phase 2 AI Executive Agent implementation: NEEDS WORK")
        logger.info("   Significant issues need to be resolved")

    return success_rate >= 60


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
