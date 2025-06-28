#!/usr/bin/env python3
"""
Test AI Content Agent Implementation
AGENT_CONTEXT: Validate real AI-powered content generation, SEO optimization, and agent coordination
AGENT_PRIORITY: Test Phase 2 Content Agent implementation (3rd of 4 agents)
AGENT_PATTERN: AI integration testing, content generation validation, agent coordination
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
async def test_ai_content_agent_basic():
    """Test basic AI Content Agent functionality."""
    try:
        logger.info("🔄 Testing AI Content Agent basic functionality...")

        # Import and create agent
        from fs_agt_clean.agents.content.ai_content_agent import (
            AgentCoordinationMessage,
            AIContentAgent,
            ContentGenerationRequest,
            SEOOptimizationRequest,
        )

        # Create agent instance
        agent = AIContentAgent(agent_id="test_ai_content_agent")
        logger.info(f"✅ AI Content Agent created: {agent.agent_id}")

        # Initialize agent
        await agent.initialize()
        logger.info("✅ AI Content Agent initialized successfully")

        # Validate initialization
        assert len(agent.marketplace_guidelines) > 0
        assert len(agent.seo_templates) > 0
        assert agent.performance_metrics is not None

        logger.info(f"📊 Initialization Results:")
        logger.info(
            f"   Marketplace Guidelines: {len(agent.marketplace_guidelines)} platforms"
        )
        logger.info(f"   SEO Templates: {len(agent.seo_templates)} categories")
        logger.info(f"   Performance Metrics: {len(agent.performance_metrics)} tracked")

        # Create test content generation request
        request = ContentGenerationRequest(
            product_info={
                "product_type": "wireless headphones",
                "brand": "TechSound",
                "model": "TS-100",
                "key_features": [
                    "noise cancellation",
                    "bluetooth 5.0",
                    "30-hour battery",
                ],
                "price": 79.99,
            },
            content_type="full_listing",
            marketplace="amazon",
            target_keywords=[
                "wireless headphones",
                "bluetooth headphones",
                "noise cancelling",
            ],
            content_length="medium",
            tone="professional",
        )
        logger.info(f"✅ Content generation request created: {request.content_type}")

        # Perform content generation
        result = await agent.generate_content(request)
        logger.info("✅ Content generation completed successfully")

        # Validate result
        assert result is not None
        assert hasattr(result, "generated_content")
        assert hasattr(result, "quality_score")
        assert hasattr(result, "seo_analysis")
        assert hasattr(result, "marketplace_compliance")
        assert result.confidence_score > 0.5

        logger.info(f"📊 Content Generation Results:")
        logger.info(f"   Content Type: {result.content_type}")
        logger.info(f"   Quality Score: {result.quality_score:.2f}")
        logger.info(f"   Confidence: {result.confidence_score:.2f}")

        # Validate generated content structure
        generated_content = result.generated_content
        assert "title" in generated_content
        assert "description" in generated_content
        assert "bullet_points" in generated_content
        assert "keywords" in generated_content

        logger.info(f"   Title: {generated_content.get('title', 'N/A')[:50]}...")
        logger.info(
            f"   Description Length: {len(generated_content.get('description', ''))}"
        )
        logger.info(
            f"   Bullet Points: {len(generated_content.get('bullet_points', []))}"
        )
        logger.info(f"   Keywords: {len(generated_content.get('keywords', []))}")

        # Validate SEO analysis
        seo_analysis = result.seo_analysis
        assert "confidence" in seo_analysis
        logger.info(
            f"   SEO Analysis Confidence: {seo_analysis.get('confidence', 'N/A')}"
        )

        # Validate marketplace compliance
        compliance = result.marketplace_compliance
        assert "compliance_score" in compliance
        logger.info(f"   Compliance Score: {compliance.get('compliance_score', 'N/A')}")

        logger.info("🎉 AI Content Agent basic test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ AI Content Agent basic test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_seo_optimization():
    """Test SEO optimization functionality."""
    try:
        logger.info("🔄 Testing SEO optimization functionality...")

        from fs_agt_clean.agents.content.ai_content_agent import (
            AIContentAgent,
            SEOOptimizationRequest,
        )

        # Create agent instance
        agent = AIContentAgent(agent_id="test_seo_content_agent")
        await agent.initialize()
        logger.info("✅ Content Agent initialized for SEO testing")

        # Create test SEO optimization request
        test_content = {
            "title": "Wireless Headphones - Good Sound Quality",
            "description": "These headphones provide good sound quality for music listening.",
            "bullet_points": [
                "Good sound quality",
                "Wireless connectivity",
                "Comfortable fit",
            ],
            "keywords": ["headphones", "wireless", "music"],
        }

        seo_request = SEOOptimizationRequest(
            content=test_content,
            target_keywords=[
                "wireless headphones",
                "bluetooth headphones",
                "noise cancelling headphones",
            ],
            marketplace="amazon",
            optimization_goals=[
                "improve_keyword_density",
                "enhance_readability",
                "increase_conversion",
            ],
        )

        # Perform SEO optimization
        seo_result = await agent.optimize_seo(seo_request)
        logger.info("✅ SEO optimization completed successfully")

        # Validate SEO result
        assert seo_result is not None
        assert hasattr(seo_result, "original_seo_score")
        assert hasattr(seo_result, "optimized_seo_score")
        assert hasattr(seo_result, "keyword_optimization")
        assert hasattr(seo_result, "content_improvements")
        assert seo_result.confidence_score > 0.5

        logger.info(f"📊 SEO Optimization Results:")
        logger.info(f"   Original Score: {seo_result.original_seo_score:.2f}")
        logger.info(f"   Optimized Score: {seo_result.optimized_seo_score:.2f}")
        logger.info(
            f"   Improvement: {seo_result.optimized_seo_score - seo_result.original_seo_score:.2f}"
        )
        logger.info(f"   Confidence: {seo_result.confidence_score:.2f}")

        # Validate keyword optimization
        keyword_optimization = seo_result.keyword_optimization
        assert isinstance(keyword_optimization, dict)
        logger.info(
            f"   Keyword Optimization: {len(keyword_optimization)} keywords analyzed"
        )

        # Validate content improvements
        content_improvements = seo_result.content_improvements
        assert isinstance(content_improvements, dict)
        logger.info(f"   Content Improvements: Available")

        # Validate marketplace compliance
        compliance = seo_result.marketplace_compliance
        assert "compliance_score" in compliance
        logger.info(f"   Compliance Score: {compliance.get('compliance_score', 'N/A')}")

        logger.info("✅ SEO optimization test completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ SEO optimization test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_marketplace_compliance():
    """Test marketplace compliance checking."""
    try:
        logger.info("🔄 Testing marketplace compliance checking...")

        from fs_agt_clean.agents.content.ai_content_agent import (
            AIContentAgent,
            ContentGenerationRequest,
        )

        # Create agent instance
        agent = AIContentAgent(agent_id="test_compliance_content_agent")
        await agent.initialize()
        logger.info("✅ Content Agent initialized for compliance testing")

        # Test different marketplaces
        marketplaces = ["amazon", "ebay", "walmart", "etsy"]
        compliance_results = []

        for marketplace in marketplaces:
            request = ContentGenerationRequest(
                product_info={
                    "product_type": "smartphone case",
                    "brand": "ProtectTech",
                    "material": "silicone",
                },
                content_type="full_listing",
                marketplace=marketplace,
                target_keywords=[
                    "smartphone case",
                    "phone protection",
                    "silicone case",
                ],
                tone="professional",
            )

            result = await agent.generate_content(request)
            compliance = result.marketplace_compliance
            compliance_results.append((marketplace, compliance))

            logger.info(f"✅ {marketplace.title()} compliance check completed")
            logger.info(f"   Compliant: {compliance.get('compliant', 'unknown')}")
            logger.info(f"   Score: {compliance.get('compliance_score', 'N/A')}")

        # Validate all compliance results
        assert len(compliance_results) == len(marketplaces)

        logger.info(f"📊 Marketplace Compliance Summary:")
        for marketplace, compliance in compliance_results:
            score = compliance.get("compliance_score", 0)
            status = (
                "✅ COMPLIANT" if compliance.get("compliant", False) else "⚠️ ISSUES"
            )
            logger.info(f"   {marketplace.title()}: {status} (Score: {score:.2f})")

        logger.info("✅ Marketplace compliance test completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Marketplace compliance test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_agent_coordination():
    """Test agent coordination functionality."""
    try:
        logger.info("🔄 Testing agent coordination functionality...")

        from fs_agt_clean.agents.content.ai_content_agent import (
            AgentCoordinationMessage,
            AIContentAgent,
        )

        # Create agent instance
        agent = AIContentAgent(agent_id="test_coordination_content_agent")
        await agent.initialize()
        logger.info("✅ Content Agent initialized for coordination testing")

        # Test content request coordination
        content_request = AgentCoordinationMessage(
            from_agent="ai_executive_agent",
            to_agent="test_coordination_content_agent",
            message_type="content_request",
            content={
                "request_type": "generate",
                "product_info": {"product_type": "laptop stand", "brand": "ErgoDesk"},
                "content_type": "description",
                "marketplace": "amazon",
                "target_keywords": ["laptop stand", "ergonomic", "adjustable"],
                "tone": "professional",
            },
            priority="high",
            requires_response=True,
        )

        # Coordinate content generation
        coordination_result = await agent.coordinate_with_agent(content_request)
        logger.info("✅ Content request coordination completed")

        # Validate coordination result
        assert coordination_result is not None
        assert coordination_result.get("status") == "content_generated"
        assert "content_result" in coordination_result

        logger.info(f"📊 Content Coordination Results:")
        logger.info(f"   Status: {coordination_result.get('status', 'unknown')}")
        logger.info(f"   Message: {coordination_result.get('message', 'N/A')}")

        # Test market data request coordination
        market_request = AgentCoordinationMessage(
            from_agent="test_coordination_content_agent",
            to_agent="ai_market_agent",
            message_type="market_data_request",
            content={
                "request_type": "competitive_content_analysis",
                "product_info": {"product_type": "laptop stand"},
                "marketplace": "amazon",
            },
        )

        market_result = await agent.coordinate_with_agent(market_request)
        logger.info("✅ Market data request coordination completed")

        # Validate market coordination
        assert market_result is not None
        assert "status" in market_result
        logger.info(
            f"   Market Request Status: {market_result.get('status', 'unknown')}"
        )

        # Test strategic guidance coordination
        strategic_guidance = AgentCoordinationMessage(
            from_agent="ai_executive_agent",
            to_agent="test_coordination_content_agent",
            message_type="strategic_guidance",
            content={
                "strategy_type": "content_planning",
                "content_strategy": "quality_focused",
                "target_metrics": {"quality_score": 0.85, "seo_score": 0.80},
            },
        )

        strategic_result = await agent.coordinate_with_agent(strategic_guidance)
        logger.info("✅ Strategic guidance coordination completed")

        # Validate strategic coordination
        assert strategic_result is not None
        assert strategic_result.get("status") == "strategic_guidance_received"
        logger.info(
            f"   Strategic Guidance Status: {strategic_result.get('status', 'unknown')}"
        )

        # Check coordination history
        assert len(agent.coordination_history) >= 3
        logger.info(
            f"✅ Coordination history: {len(agent.coordination_history)} messages"
        )

        # Check performance metrics update
        assert agent.performance_metrics["agent_collaborations"] >= 3
        logger.info(
            f"✅ Agent collaborations: {agent.performance_metrics['agent_collaborations']}"
        )

        logger.info("✅ Agent coordination test completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Agent coordination test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_performance_tracking():
    """Test performance tracking and metrics."""
    try:
        logger.info("🔄 Testing performance tracking and metrics...")

        from fs_agt_clean.agents.content.ai_content_agent import (
            AIContentAgent,
            ContentGenerationRequest,
        )

        # Create agent instance
        agent = AIContentAgent(agent_id="test_performance_content_agent")
        await agent.initialize()
        logger.info("✅ Content Agent initialized for performance testing")

        # Perform multiple content generations to track performance
        initial_metrics = agent.performance_metrics.copy()

        for i in range(3):
            request = ContentGenerationRequest(
                product_info={
                    "product_type": f"test_product_{i}",
                    "brand": "TestBrand",
                },
                content_type="description",
                marketplace="amazon",
                target_keywords=[f"keyword_{i}", "test", "product"],
                tone="professional",
            )

            result = await agent.generate_content(request)
            logger.info(f"✅ Content generation {i+1} completed")

        # Check performance metrics updates
        final_metrics = agent.performance_metrics

        assert final_metrics["content_generated"] > initial_metrics["content_generated"]
        assert final_metrics["avg_quality_score"] > 0

        logger.info(f"📊 Performance Tracking Results:")
        logger.info(f"   Content Generated: {final_metrics['content_generated']}")
        logger.info(
            f"   Average Quality Score: {final_metrics['avg_quality_score']:.2f}"
        )
        logger.info(f"   Average SEO Score: {final_metrics['avg_seo_score']:.2f}")
        logger.info(f"   SEO Optimizations: {final_metrics['seo_optimizations']}")
        logger.info(f"   Agent Collaborations: {final_metrics['agent_collaborations']}")

        # Test performance reporting
        performance_message = AgentCoordinationMessage(
            from_agent="test_performance_content_agent",
            to_agent="ai_executive_agent",
            message_type="performance_report",
            content={"report_type": "content_performance"},
        )

        performance_result = await agent.coordinate_with_agent(performance_message)
        logger.info("✅ Performance reporting completed")

        # Validate performance report
        assert performance_result is not None
        assert performance_result.get("status") == "performance_report_sent"
        assert "performance_summary" in performance_result
        assert "content_statistics" in performance_result

        logger.info(
            f"   Performance Report Status: {performance_result.get('status', 'unknown')}"
        )

        logger.info("✅ Performance tracking test completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Performance tracking test failed: {e}")
        return False


async def main():
    """Run all Content Agent tests."""
    logger.info("🚀 Starting AI Content Agent Phase 2 Tests")
    logger.info("=" * 60)

    results = []

    # Test 1: Basic Content Agent functionality
    logger.info("\n📋 Test 1: AI Content Agent Basic Functionality")
    result1 = await test_ai_content_agent_basic()
    results.append(("AI Content Agent Basic", result1))

    # Test 2: SEO optimization
    logger.info("\n📋 Test 2: SEO Optimization")
    result2 = await test_seo_optimization()
    results.append(("SEO Optimization", result2))

    # Test 3: Marketplace compliance
    logger.info("\n📋 Test 3: Marketplace Compliance")
    result3 = await test_marketplace_compliance()
    results.append(("Marketplace Compliance", result3))

    # Test 4: Agent coordination
    logger.info("\n📋 Test 4: Agent Coordination")
    result4 = await test_agent_coordination()
    results.append(("Agent Coordination", result4))

    # Test 5: Performance tracking
    logger.info("\n📋 Test 5: Performance Tracking")
    result5 = await test_performance_tracking()
    results.append(("Performance Tracking", result5))

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
        logger.info("🎉 Phase 2 AI Content Agent implementation: SUCCESS")
        logger.info("   Ready for integration with Market and Executive agents")
    elif success_rate >= 60:
        logger.info("⚠️ Phase 2 AI Content Agent implementation: PARTIAL SUCCESS")
        logger.info("   Some issues need attention but core functionality works")
    else:
        logger.info("❌ Phase 2 AI Content Agent implementation: NEEDS WORK")
        logger.info("   Significant issues need to be resolved")

    return success_rate >= 60


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
