#!/usr/bin/env python3
"""
Test Fixed Agent Functionality
"""

import sys
import asyncio

sys.path.insert(0, "/app")

print("🔧 Fixed Agent Functionality Test")
print("=" * 50)


async def test_fixed_agents():
    # Test ExecutiveAgent with fixes
    print("🎯 Testing Fixed ExecutiveAgent:")
    try:
        from fs_agt_clean.agents.executive.executive_agent import ExecutiveAgent

        exec_agent = ExecutiveAgent(agent_id="test_executive")
        print("   ✅ Initialization successful")

        # Test get_status method (should work now)
        status = await exec_agent.get_status()
        print(f'   ✅ get_status(): {status.get("status", "unknown")}')

        # Test make_decision method (newly added)
        decision = await exec_agent.make_decision("test_decision", {"test": "data"})
        print(f'   ✅ make_decision(): {decision.get("decision", "none")}')

    except Exception as e:
        print(f"   ❌ ExecutiveAgent: {e}")

    print()
    print("📝 Testing Fixed ContentAgent:")
    try:
        from fs_agt_clean.agents.content.content_agent import ContentAgent

        content_agent = ContentAgent(agent_id="test_content")
        print("   ✅ Initialization successful")

        # Test generate_content method (newly added)
        content = await content_agent.generate_content(
            {"product_name": "Test Product", "category": "Electronics"}
        )
        print(f'   ✅ generate_content(): Title length {len(content.get("title", ""))}')
        print(f'       SEO Score: {content.get("seo_score", 0)}')

    except Exception as e:
        print(f"   ❌ ContentAgent: {e}")

    print()
    print("📊 Testing Fixed MarketAgent:")
    try:
        from fs_agt_clean.agents.market.market_agent import MarketAgent

        market_agent = MarketAgent(agent_id="test_market")
        print("   ✅ Initialization successful")

        # Test analyze_market method (newly added)
        analysis = await market_agent.analyze_market("iPhone")
        print(
            f'   ✅ analyze_market(): Found {len(analysis.get("listings", []))} listings'
        )
        print(
            f'       Competition level: {analysis.get("competition_level", "unknown")}'
        )

        # Test analyze_product_pricing method (newly added)
        pricing = await market_agent.analyze_product_pricing("iPhone", "Electronics")
        print(
            f'   ✅ analyze_product_pricing(): Recommended ${pricing.get("recommended_price", 0):.2f}'
        )

    except Exception as e:
        print(f"   ❌ MarketAgent: {e}")


# Run the test
if __name__ == "__main__":
    asyncio.run(test_fixed_agents())
    print("=" * 50)
    print("🎉 Agent fixes validation complete!")
