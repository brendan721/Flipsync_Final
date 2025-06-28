#!/usr/bin/env python3
"""
Comprehensive Agent Diagnosis
Identifies what agents exist vs. what should exist and diagnoses AI issues.
"""

import asyncio
import sys
import os
import importlib
import inspect
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fs_agt_clean'))

async def diagnose_agent_system():
    """Comprehensive agent system diagnosis."""
    print("🔍 FlipSync Agent System Diagnosis")
    print("=" * 60)
    
    # 1. Check what agents are currently running
    print("\n1. 🤖 Currently Running Agents")
    print("-" * 30)
    
    try:
        import subprocess
        result = subprocess.run([
            "curl", "-s", "http://localhost:8001/api/v1/agents/status"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if "agents" in data:
                for agent in data["agents"]:
                    print(f"✅ {agent['agent_id']}: {agent['status']} (uptime: {agent['uptime']:.1f}s)")
            else:
                print("❌ No agent data found")
        else:
            print("❌ Failed to get agent status")
    except Exception as e:
        print(f"❌ Error checking running agents: {e}")
    
    # 2. Check agent implementations in codebase
    print("\n2. 📁 Agent Implementations in Codebase")
    print("-" * 40)
    
    agent_files = []
    agents_dir = Path("fs_agt_clean/agents")
    
    if agents_dir.exists():
        for agent_file in agents_dir.rglob("*agent*.py"):
            if not agent_file.name.startswith("test_") and agent_file.name != "__init__.py":
                agent_files.append(agent_file)
        
        print(f"Found {len(agent_files)} agent implementation files:")
        for file in sorted(agent_files):
            print(f"  📄 {file}")
    else:
        print("❌ Agents directory not found")
    
    # 3. Check specific agent classes
    print("\n3. 🏗️ Agent Class Analysis")
    print("-" * 30)
    
    expected_agents = {
        "Market Agents": [
            ("fs_agt_clean.agents.market.market_agent", "MarketAgent"),
            ("fs_agt_clean.agents.market.ai_market_agent", "AIMarketAgent"),
            ("fs_agt_clean.agents.market.ebay_agent", "eBayAgent"),
            ("fs_agt_clean.agents.market.amazon_agent", "AmazonAgent"),
            ("fs_agt_clean.agents.market.inventory_agent", "InventoryAgent"),
        ],
        "Executive Agents": [
            ("fs_agt_clean.agents.executive.executive_agent", "ExecutiveAgent"),
            ("fs_agt_clean.agents.executive.ai_executive_agent", "AIExecutiveAgent"),
        ],
        "Content Agents": [
            ("fs_agt_clean.agents.content.content_agent", "ContentAgent"),
            ("fs_agt_clean.agents.content.ai_content_agent", "AIContentAgent"),
        ],
        "Logistics Agents": [
            ("fs_agt_clean.agents.logistics.logistics_agent", "LogisticsAgent"),
            ("fs_agt_clean.agents.logistics.ai_logistics_agent", "AILogisticsAgent"),
            ("fs_agt_clean.agents.logistics.shipping_agent", "ShippingAgent"),
            ("fs_agt_clean.agents.logistics.warehouse_agent", "WarehouseAgent"),
        ],
        "Specialized Agents": [
            ("fs_agt_clean.agents.market.specialized.competitor_analyzer", "CompetitorAnalyzer"),
            ("fs_agt_clean.agents.market.specialized.listing_agent", "ListingAgent"),
            ("fs_agt_clean.agents.market.specialized.market_analyzer", "MarketAnalyzer"),
            ("fs_agt_clean.agents.market.specialized.trend_detector", "TrendDetector"),
            ("fs_agt_clean.agents.market.specialized.advertising_agent", "AdvertisingAgent"),
        ]
    }
    
    total_expected = 0
    total_found = 0
    
    for category, agents in expected_agents.items():
        print(f"\n{category}:")
        for module_path, class_name in agents:
            total_expected += 1
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, class_name):
                    agent_class = getattr(module, class_name)
                    if inspect.isclass(agent_class):
                        print(f"  ✅ {class_name}: Available")
                        total_found += 1
                    else:
                        print(f"  ⚠️ {class_name}: Not a class")
                else:
                    print(f"  ❌ {class_name}: Class not found in module")
            except ImportError as e:
                print(f"  ❌ {class_name}: Import error - {str(e)[:50]}...")
            except Exception as e:
                print(f"  ❌ {class_name}: Error - {str(e)[:50]}...")
    
    print(f"\nAgent Implementation Summary: {total_found}/{total_expected} agents available")
    
    # 4. Check AI integration
    print("\n4. 🧠 AI Integration Diagnosis")
    print("-" * 30)
    
    try:
        from fs_agt_clean.core.ai.llm_factory import FlipSyncLLMFactory
        print("✅ FlipSyncLLMFactory: Available")
        
        factory = FlipSyncLLMFactory()
        print("✅ Factory instance: Created")
        
        client = factory.create_client()
        print(f"✅ AI Client: {type(client).__name__}")
        
    except Exception as e:
        print(f"❌ AI Integration Error: {e}")
    
    # 5. Check orchestration
    print("\n5. 🎭 Agent Orchestration")
    print("-" * 25)
    
    try:
        from fs_agt_clean.services.agent_orchestration import AgentOrchestrationService
        print("✅ AgentOrchestrationService: Available")
        
        orchestration = AgentOrchestrationService()
        print(f"✅ Orchestration instance: Created")
        print(f"✅ Registered agents: {list(orchestration.agent_registry.keys())}")
        
        for name, agent in orchestration.agent_registry.items():
            print(f"   - {name}: {type(agent).__name__}")
            
    except Exception as e:
        print(f"❌ Orchestration Error: {e}")
    
    # 6. Recommendations
    print("\n6. 💡 Diagnosis Summary & Recommendations")
    print("-" * 45)
    
    if total_found < total_expected * 0.7:
        print("❌ CRITICAL: Many expected agents are missing")
        print("   Recommendation: Implement missing agent classes")
    elif total_found < total_expected:
        print("⚠️ WARNING: Some expected agents are missing")
        print("   Recommendation: Complete agent implementation")
    else:
        print("✅ GOOD: Most expected agents are implemented")
    
    print(f"\nKey Issues to Address:")
    print(f"1. Only 3 basic agents running vs. {total_expected} implemented")
    print(f"2. AI responses are generic error messages")
    print(f"3. No specialized agents (competitor analysis, trend detection, etc.) active")
    print(f"4. Missing marketplace-specific agents (Amazon, eBay, Walmart)")
    print(f"5. No automation agents (auto-pricing, auto-listing)")
    
    print(f"\nNext Steps:")
    print(f"1. Fix AI integration to enable real responses")
    print(f"2. Register and activate specialized agents")
    print(f"3. Implement missing automation agents")
    print(f"4. Test multi-agent coordination workflows")

def main():
    """Main diagnosis function."""
    asyncio.run(diagnose_agent_system())

if __name__ == "__main__":
    main()
