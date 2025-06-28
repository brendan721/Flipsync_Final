#!/usr/bin/env python3
"""
Simple AI Executive Agent Test
AGENT_CONTEXT: Basic validation of AI Executive Agent functionality
AGENT_PRIORITY: Test Phase 2 Executive Agent implementation
AGENT_PATTERN: Simple testing, basic validation, agent coordination
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


async def test_ai_executive_agent_direct():
    """Test AI Executive Agent directly without complex imports."""
    try:
        logger.info("🔄 Testing AI Executive Agent direct functionality...")
        
        # Import directly from our implementation
        from fs_agt_clean.agents.executive.ai_executive_agent import (
            AIExecutiveAgent, 
            StrategicAnalysisRequest,
            AgentCoordinationMessage
        )
        
        # Create agent instance
        agent = AIExecutiveAgent(agent_id="test_direct_executive")
        logger.info(f"✅ AI Executive Agent created: {agent.agent_id}")
        
        # Initialize agent
        await agent.initialize()
        logger.info("✅ AI Executive Agent initialized successfully")
        
        # Test agent registry
        assert len(agent.managed_agents) > 0
        logger.info(f"✅ Agent registry initialized with {len(agent.managed_agents)} agents")
        
        # Test performance metrics initialization
        assert len(agent.performance_metrics) > 0
        logger.info(f"✅ Performance metrics initialized for {len(agent.performance_metrics)} agents")
        
        # Create strategic analysis request
        request = StrategicAnalysisRequest(
            business_context={
                "revenue": 500000,
                "profit_margin": 0.15,
                "team_size": 8,
                "market_position": "growing"
            },
            decision_type="strategic_planning",
            objectives=["revenue_growth", "operational_efficiency"],
            constraints={
                "budget": 100000,
                "timeline_months": 12,
                "team_size": 10
            },
            timeline="12 months",
            priority_level="high"
        )
        logger.info(f"✅ Strategic analysis request created: {request.decision_type}")
        
        # Perform strategic analysis
        result = await agent.analyze_strategic_situation(request)
        logger.info("✅ Strategic analysis completed successfully")
        
        # Validate result structure
        assert result is not None
        assert hasattr(result, 'decision_type')
        assert hasattr(result, 'strategic_summary')
        assert hasattr(result, 'recommendations')
        assert hasattr(result, 'confidence_score')
        assert hasattr(result, 'agent_coordination_plan')
        
        logger.info(f"📊 Strategic Analysis Results:")
        logger.info(f"   Decision Type: {result.decision_type}")
        logger.info(f"   Confidence: {result.confidence_score:.2f}")
        logger.info(f"   Summary: {result.strategic_summary[:100]}...")
        logger.info(f"   Recommendations: {len(result.recommendations)} items")
        
        # Validate resource allocation
        if result.resource_allocation:
            budget_allocation = result.resource_allocation.get('budget_allocation', {})
            optimization_score = result.resource_allocation.get('optimization_score', 0)
            logger.info(f"   Budget Allocation: {len(budget_allocation)} categories")
            logger.info(f"   Optimization Score: {optimization_score:.2f}")
        
        # Validate agent coordination plan
        coordination = result.agent_coordination_plan
        if coordination:
            strategy = coordination.get('coordination_strategy', 'unknown')
            assignments = coordination.get('agent_assignments', {})
            logger.info(f"   Coordination Strategy: {strategy}")
            logger.info(f"   Agent Assignments: {len(assignments)} agents")
        
        logger.info("🎉 AI Executive Agent direct test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ AI Executive Agent direct test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_coordination_simple():
    """Test simple agent coordination functionality."""
    try:
        logger.info("🔄 Testing simple agent coordination...")
        
        from fs_agt_clean.agents.executive.ai_executive_agent import (
            AIExecutiveAgent, 
            AgentCoordinationMessage
        )
        
        # Create agent instance
        agent = AIExecutiveAgent(agent_id="test_coordination_simple")
        await agent.initialize()
        logger.info("✅ Executive Agent initialized for coordination testing")
        
        # Test task assignment
        task_message = AgentCoordinationMessage(
            from_agent="test_coordination_simple",
            to_agent="ai_market_agent",
            message_type="task_assignment",
            content={
                "task": "competitive_pricing_analysis",
                "priority": "high",
                "requirements": ["pricing_data", "competitor_analysis"]
            },
            priority="high",
            requires_response=True
        )
        
        # Coordinate with agent
        result = await agent.coordinate_with_agent(task_message)
        logger.info("✅ Task assignment coordination completed")
        
        # Validate coordination result
        assert result is not None
        assert "status" in result
        assert "timestamp" in result
        
        logger.info(f"📊 Coordination Results:")
        logger.info(f"   Status: {result.get('status', 'unknown')}")
        logger.info(f"   Message: {result.get('message', 'N/A')[:50]}...")
        
        # Test coordination history
        assert len(agent.coordination_history) > 0
        logger.info(f"✅ Coordination history tracked: {len(agent.coordination_history)} messages")
        
        logger.info("✅ Simple agent coordination test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Simple agent coordination test failed: {e}")
        return False


async def test_performance_monitoring_simple():
    """Test simple performance monitoring functionality."""
    try:
        logger.info("🔄 Testing simple performance monitoring...")
        
        from fs_agt_clean.agents.executive.ai_executive_agent import AIExecutiveAgent
        
        # Create agent instance
        agent = AIExecutiveAgent(agent_id="test_monitoring_simple")
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
        logger.info(f"   Timestamp: {monitoring_report.get('monitoring_timestamp', 'N/A')}")
        logger.info(f"   Total Agents: {monitoring_report.get('total_agents', 0)}")
        
        # Check agent performance data
        agent_performance = monitoring_report.get("agent_performance", {})
        logger.info(f"   Agents Monitored: {len(agent_performance)}")
        
        for agent_id, performance in agent_performance.items():
            logger.info(f"     {agent_id}: {performance.get('agent_type', 'unknown')} - {performance.get('status', 'unknown')}")
        
        # Check system health
        system_health = monitoring_report.get("system_health", {})
        if system_health:
            logger.info(f"   System Health Available: Yes")
        
        logger.info("✅ Simple performance monitoring test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Simple performance monitoring test failed: {e}")
        return False


async def test_business_intelligence_gathering():
    """Test business intelligence gathering functionality."""
    try:
        logger.info("🔄 Testing business intelligence gathering...")
        
        from fs_agt_clean.agents.executive.ai_executive_agent import (
            AIExecutiveAgent, 
            StrategicAnalysisRequest
        )
        
        # Create agent instance
        agent = AIExecutiveAgent(agent_id="test_bi_executive")
        await agent.initialize()
        logger.info("✅ Executive Agent initialized for BI testing")
        
        # Create test request
        request = StrategicAnalysisRequest(
            business_context={
                "revenue_growth": 0.20,
                "profit_margin": 0.18,
                "cash_flow": "positive",
                "budget_utilization": 0.80
            },
            decision_type="performance_review",
            objectives=["performance_optimization"],
            constraints={"budget": 75000}
        )
        
        # Test business intelligence gathering
        business_intelligence = await agent._gather_business_intelligence(request)
        logger.info("✅ Business intelligence gathering completed")
        
        # Validate business intelligence
        assert business_intelligence is not None
        assert "market_data" in business_intelligence
        assert "financial_metrics" in business_intelligence
        assert "operational_metrics" in business_intelligence
        assert "agent_performance" in business_intelligence
        
        logger.info(f"📊 Business Intelligence Results:")
        logger.info(f"   Market Data: {len(business_intelligence.get('market_data', {}))}")
        logger.info(f"   Financial Metrics: {len(business_intelligence.get('financial_metrics', {}))}")
        logger.info(f"   Operational Metrics: {len(business_intelligence.get('operational_metrics', {}))}")
        logger.info(f"   Agent Performance: {len(business_intelligence.get('agent_performance', {}))}")
        
        # Check specific data
        market_data = business_intelligence.get("market_data", {})
        if market_data:
            logger.info(f"   Market Growth Rate: {market_data.get('market_growth_rate', 'N/A')}")
            logger.info(f"   Competition Intensity: {market_data.get('competition_intensity', 'N/A')}")
        
        financial_metrics = business_intelligence.get("financial_metrics", {})
        if financial_metrics:
            logger.info(f"   Revenue Growth: {financial_metrics.get('revenue_growth', 'N/A')}")
            logger.info(f"   Profit Margin: {financial_metrics.get('profit_margin', 'N/A')}")
        
        logger.info("✅ Business intelligence gathering test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Business intelligence gathering test failed: {e}")
        return False


async def main():
    """Run all simple Executive Agent tests."""
    logger.info("🚀 Starting AI Executive Agent Simple Tests")
    logger.info("=" * 60)
    
    results = []
    
    # Test 1: Direct Executive Agent functionality
    logger.info("\n📋 Test 1: AI Executive Agent Direct Functionality")
    result1 = await test_ai_executive_agent_direct()
    results.append(("AI Executive Agent Direct", result1))
    
    # Test 2: Simple agent coordination
    logger.info("\n📋 Test 2: Simple Agent Coordination")
    result2 = await test_agent_coordination_simple()
    results.append(("Simple Agent Coordination", result2))
    
    # Test 3: Simple performance monitoring
    logger.info("\n📋 Test 3: Simple Performance Monitoring")
    result3 = await test_performance_monitoring_simple()
    results.append(("Simple Performance Monitoring", result3))
    
    # Test 4: Business intelligence gathering
    logger.info("\n📋 Test 4: Business Intelligence Gathering")
    result4 = await test_business_intelligence_gathering()
    results.append(("Business Intelligence Gathering", result4))
    
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
        logger.info("   Ready for integration with Market Agent and coordination")
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
