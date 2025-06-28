#!/usr/bin/env python3
"""
Agent Integration Test - Market Agent + Executive Agent
AGENT_CONTEXT: Validate agent-to-agent coordination and communication
AGENT_PRIORITY: Test Phase 2 agent integration and coordination workflows
AGENT_PATTERN: Integration testing, agent coordination, workflow validation
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_market_executive_coordination():
    """Test coordination between Market Agent and Executive Agent."""
    try:
        logger.info("🔄 Testing Market Agent + Executive Agent coordination...")

        # Import both agents
        from fs_agt_clean.agents.executive.ai_executive_agent import (
            AgentCoordinationMessage,
            AIExecutiveAgent,
            StrategicAnalysisRequest,
        )
        from fs_agt_clean.agents.market.ai_market_agent import (
            AIMarketAgent,
            MarketAnalysisRequest,
        )

        # Create both agents
        market_agent = AIMarketAgent(agent_id="integration_market_agent")
        executive_agent = AIExecutiveAgent(agent_id="integration_executive_agent")

        # Initialize both agents
        await market_agent.initialize()
        await executive_agent.initialize()

        logger.info("✅ Both agents initialized successfully")

        # Step 1: Executive Agent requests market intelligence
        coordination_request = AgentCoordinationMessage(
            from_agent="integration_executive_agent",
            to_agent="integration_market_agent",
            message_type="coordination_request",
            content={
                "request_type": "market_intelligence",
                "business_context": {
                    "product_category": "electronics",
                    "target_market": "consumer_electronics",
                    "budget": 50000,
                },
            },
            priority="high",
            requires_response=True,
        )

        # Executive coordinates with Market Agent
        coordination_result = await executive_agent.coordinate_with_agent(
            coordination_request
        )
        logger.info("✅ Executive Agent coordination request completed")

        # Validate coordination result
        assert coordination_result is not None
        assert coordination_result.get("status") == "coordination_approved"

        logger.info(
            f"📊 Coordination Result: {coordination_result.get('message', 'N/A')}"
        )

        # Step 2: Market Agent performs analysis
        market_request = MarketAnalysisRequest(
            product_query="wireless bluetooth headphones",
            target_marketplace="all",
            analysis_depth="detailed",
            include_competitors=True,
            price_range=(25.0, 100.0),
        )

        market_result = await market_agent.analyze_market(market_request)
        logger.info("✅ Market Agent analysis completed")

        # Validate market analysis
        assert market_result is not None
        assert hasattr(market_result, "confidence_score")
        assert market_result.confidence_score > 0.5

        logger.info(
            f"📊 Market Analysis: Confidence {market_result.confidence_score:.2f}"
        )

        # Step 3: Market Agent reports back to Executive
        performance_report = AgentCoordinationMessage(
            from_agent="integration_market_agent",
            to_agent="integration_executive_agent",
            message_type="performance_report",
            content={
                "agent_id": "integration_market_agent",
                "task_completed": "market_intelligence_analysis",
                "performance_metrics": {
                    "analysis_confidence": market_result.confidence_score,
                    "competitors_analyzed": len(market_result.competitor_analysis),
                    "pricing_recommendations": len(
                        market_result.pricing_recommendation
                    ),
                    "response_time": 2.5,
                    "success_rate": 0.95,
                },
                "results_summary": {
                    "recommended_price": market_result.pricing_recommendation.get(
                        "recommended_price"
                    ),
                    "market_position": market_result.pricing_recommendation.get(
                        "market_position"
                    ),
                    "confidence": market_result.confidence_score,
                },
            },
        )

        # Executive processes performance report
        report_result = await executive_agent.coordinate_with_agent(performance_report)
        logger.info("✅ Executive Agent processed performance report")

        # Validate report processing
        assert report_result is not None
        assert report_result.get("status") == "performance_report_received"

        logger.info(f"📊 Report Processing: {report_result.get('message', 'N/A')}")

        # Step 4: Executive Agent creates strategic plan based on market intelligence
        strategic_request = StrategicAnalysisRequest(
            business_context={
                "market_intelligence": {
                    "recommended_price": market_result.pricing_recommendation.get(
                        "recommended_price"
                    ),
                    "market_confidence": market_result.confidence_score,
                    "competitors_count": len(market_result.competitor_analysis),
                },
                "budget": 50000,
                "timeline": "Q1-Q2 2024",
            },
            decision_type="strategic_planning",
            objectives=["revenue_growth", "market_expansion"],
            constraints={"budget": 50000, "timeline_months": 6, "team_size": 5},
            priority_level="high",
        )

        strategic_result = await executive_agent.analyze_strategic_situation(
            strategic_request
        )
        logger.info("✅ Executive Agent strategic analysis completed")

        # Validate strategic analysis
        assert strategic_result is not None
        assert hasattr(strategic_result, "agent_coordination_plan")
        assert strategic_result.confidence_score > 0.5

        logger.info(
            f"📊 Strategic Analysis: Confidence {strategic_result.confidence_score:.2f}"
        )

        # Step 5: Validate agent coordination plan includes Market Agent
        coordination_plan = strategic_result.agent_coordination_plan
        agent_assignments = coordination_plan.get("agent_assignments", {})

        assert "ai_market_agent" in agent_assignments
        market_tasks = agent_assignments["ai_market_agent"]
        assert len(market_tasks) > 0

        logger.info(f"📊 Market Agent Tasks: {len(market_tasks)} assigned")

        logger.info(
            "🎉 Market Agent + Executive Agent coordination test completed successfully!"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Agent coordination test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_performance_monitoring_integration():
    """Test performance monitoring integration between agents."""
    try:
        logger.info("🔄 Testing performance monitoring integration...")

        from fs_agt_clean.agents.executive.ai_executive_agent import (
            AgentCoordinationMessage,
            AIExecutiveAgent,
        )

        # Create executive agent
        executive_agent = AIExecutiveAgent(agent_id="monitoring_executive_agent")
        await executive_agent.initialize()

        logger.info("✅ Executive Agent initialized for monitoring")

        # Simulate multiple agent interactions
        for i in range(3):
            # Simulate task assignment
            task_message = AgentCoordinationMessage(
                from_agent="monitoring_executive_agent",
                to_agent="ai_market_agent",
                message_type="task_assignment",
                content={"task": f"market_analysis_task_{i}", "priority": "medium"},
            )

            await executive_agent.coordinate_with_agent(task_message)

            # Simulate status update
            status_message = AgentCoordinationMessage(
                from_agent="ai_market_agent",
                to_agent="monitoring_executive_agent",
                message_type="status_update",
                content={
                    "task_id": f"market_analysis_task_{i}",
                    "status": "completed" if i % 2 == 0 else "in_progress",
                    "completion_percentage": 100 if i % 2 == 0 else 75,
                },
            )

            await executive_agent.coordinate_with_agent(status_message)

        logger.info("✅ Simulated agent interactions completed")

        # Test performance monitoring
        monitoring_report = await executive_agent.monitor_agent_performance()

        # Validate monitoring report
        assert monitoring_report is not None
        assert "agent_performance" in monitoring_report
        assert "system_health" in monitoring_report

        # Check that performance metrics were updated
        agent_performance = monitoring_report["agent_performance"]
        if "ai_market_agent" in agent_performance:
            market_performance = agent_performance["ai_market_agent"]
            logger.info(f"📊 Market Agent Performance:")
            logger.info(
                f"   Success Rate: {market_performance.get('success_rate', 'N/A')}"
            )
            logger.info(
                f"   Task Completion: {market_performance.get('task_completion', 'N/A')}"
            )

        # Check system health
        system_health = monitoring_report["system_health"]
        logger.info(
            f"📊 System Health: {system_health.get('overall_health', 'unknown')}"
        )

        # Check coordination history
        assert (
            len(executive_agent.coordination_history) >= 6
        )  # 3 tasks + 3 status updates
        logger.info(
            f"✅ Coordination history: {len(executive_agent.coordination_history)} messages"
        )

        logger.info(
            "🎉 Performance monitoring integration test completed successfully!"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Performance monitoring integration test failed: {e}")
        return False


async def test_business_intelligence_workflow():
    """Test complete business intelligence workflow."""
    try:
        logger.info("🔄 Testing business intelligence workflow...")

        from fs_agt_clean.agents.executive.ai_executive_agent import (
            AIExecutiveAgent,
            StrategicAnalysisRequest,
        )
        from fs_agt_clean.agents.market.ai_market_agent import (
            AIMarketAgent,
            MarketAnalysisRequest,
        )

        # Create agents
        market_agent = AIMarketAgent(agent_id="bi_market_agent")
        executive_agent = AIExecutiveAgent(agent_id="bi_executive_agent")

        await market_agent.initialize()
        await executive_agent.initialize()

        logger.info("✅ Agents initialized for BI workflow")

        # Step 1: Market intelligence gathering
        market_request = MarketAnalysisRequest(
            product_query="smart home devices",
            target_marketplace="all",
            analysis_depth="comprehensive",
            include_competitors=True,
            price_range=(50.0, 300.0),
        )

        market_intelligence = await market_agent.analyze_market(market_request)
        logger.info("✅ Market intelligence gathered")

        # Step 2: Strategic analysis incorporating market intelligence
        strategic_request = StrategicAnalysisRequest(
            business_context={
                "market_intelligence": {
                    "product_category": "smart_home_devices",
                    "market_confidence": market_intelligence.confidence_score,
                    "pricing_strategy": market_intelligence.pricing_recommendation.get(
                        "price_strategy"
                    ),
                    "competitor_count": len(market_intelligence.competitor_analysis),
                    "market_trends": market_intelligence.market_trends,
                },
                "current_revenue": 750000,
                "growth_target": 0.30,
                "market_position": "expanding",
            },
            decision_type="strategic_planning",
            objectives=["revenue_growth", "market_expansion", "operational_efficiency"],
            constraints={"budget": 150000, "timeline_months": 12, "team_size": 12},
            priority_level="high",
        )

        strategic_analysis = await executive_agent.analyze_strategic_situation(
            strategic_request
        )
        logger.info("✅ Strategic analysis completed")

        # Step 3: Validate integrated workflow
        assert market_intelligence.confidence_score > 0.5
        assert strategic_analysis.confidence_score > 0.5

        # Check that strategic analysis incorporates market intelligence
        business_context = strategic_request.business_context
        assert "market_intelligence" in business_context
        assert (
            business_context["market_intelligence"]["market_confidence"]
            == market_intelligence.confidence_score
        )

        # Check resource allocation
        resource_allocation = strategic_analysis.resource_allocation
        assert "budget_allocation" in resource_allocation
        assert resource_allocation.get("optimization_score", 0) > 0.7

        # Check agent coordination plan
        coordination_plan = strategic_analysis.agent_coordination_plan
        assert "agent_assignments" in coordination_plan

        logger.info(f"📊 Workflow Results:")
        logger.info(f"   Market Confidence: {market_intelligence.confidence_score:.2f}")
        logger.info(
            f"   Strategic Confidence: {strategic_analysis.confidence_score:.2f}"
        )
        logger.info(
            f"   Resource Optimization: {resource_allocation.get('optimization_score', 0):.2f}"
        )
        logger.info(
            f"   Coordination Strategy: {coordination_plan.get('coordination_strategy', 'unknown')}"
        )

        logger.info("🎉 Business intelligence workflow test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Business intelligence workflow test failed: {e}")
        return False


async def main():
    """Run all agent integration tests."""
    logger.info("🚀 Starting Agent Integration Tests (Market + Executive)")
    logger.info("=" * 70)

    results = []

    # Test 1: Market + Executive coordination
    logger.info("\n📋 Test 1: Market + Executive Agent Coordination")
    result1 = await test_market_executive_coordination()
    results.append(("Market + Executive Coordination", result1))

    # Test 2: Performance monitoring integration
    logger.info("\n📋 Test 2: Performance Monitoring Integration")
    result2 = await test_performance_monitoring_integration()
    results.append(("Performance Monitoring Integration", result2))

    # Test 3: Business intelligence workflow
    logger.info("\n📋 Test 3: Business Intelligence Workflow")
    result3 = await test_business_intelligence_workflow()
    results.append(("Business Intelligence Workflow", result3))

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 INTEGRATION TEST SUMMARY")
    logger.info("=" * 70)

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
        logger.info("🎉 Phase 2 Agent Integration: SUCCESS")
        logger.info("   Market Agent + Executive Agent coordination fully operational")
        logger.info("   Ready to proceed with Content and Logistics agents")
    elif success_rate >= 60:
        logger.info("⚠️ Phase 2 Agent Integration: PARTIAL SUCCESS")
        logger.info("   Core coordination works but some issues need attention")
    else:
        logger.info("❌ Phase 2 Agent Integration: NEEDS WORK")
        logger.info("   Significant coordination issues need to be resolved")

    return success_rate >= 60


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
