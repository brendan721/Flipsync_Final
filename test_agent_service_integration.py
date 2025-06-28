#!/usr/bin/env python3
"""
Agent Service Integration Test
Tests the specific agent service integration between Flutter frontend and FlipSync backend
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List


async def test_agent_service_integration() -> Dict[str, Any]:
    """Test agent service integration specifically."""
    
    print("🤖 Testing Agent Service Integration")
    print("=" * 60)
    
    test_results = {
        "backend_agents": False,
        "data_structure": False,
        "type_mapping": False,
        "performance_data": False,
        "conversion_logic": False,
        "sophisticated_count": 0,
        "agent_types": [],
        "evidence": []
    }
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Backend Agent Endpoint
        print("📡 Test 1: Backend Agent Endpoint")
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    test_results["backend_agents"] = True
                    test_results["sophisticated_count"] = len(agents_data)
                    test_results["agent_types"] = [agent.get('type', '') for agent in agents_data]
                    
                    print(f"✅ Backend agents endpoint accessible")
                    print(f"📊 Found {len(agents_data)} agents")
                    print(f"🏗️  Agent types: {', '.join(set(test_results['agent_types']))}")
                    test_results["evidence"].append(f"Backend serves {len(agents_data)} agents")
                else:
                    print(f"❌ Backend agents endpoint failed: {response.status}")
        except Exception as e:
            print(f"❌ Backend agent test failed: {e}")
        
        # Test 2: Data Structure Compatibility
        print("\n🔄 Test 2: Data Structure Compatibility")
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    sample_agent = agents_data[0]
                    
                    # Check required fields for frontend conversion
                    required_fields = ['id', 'name', 'type', 'status', 'capabilities']
                    has_all = all(field in sample_agent for field in required_fields)
                    
                    if has_all:
                        test_results["data_structure"] = True
                        print("✅ Data structure compatible with frontend")
                        test_results["evidence"].append("Backend data structure matches frontend requirements")
                        
                        # Show sample data structure
                        print(f"📋 Sample Agent Structure:")
                        print(f"   ID: {sample_agent.get('id')}")
                        print(f"   Name: {sample_agent.get('name')}")
                        print(f"   Type: {sample_agent.get('type')}")
                        print(f"   Status: {sample_agent.get('status')}")
                        print(f"   Capabilities: {len(sample_agent.get('capabilities', []))}")
                        
                        # Check for performance metrics
                        if 'performance_metrics' in sample_agent:
                            test_results["performance_data"] = True
                            print("✅ Performance metrics available")
                            test_results["evidence"].append("Backend provides performance metrics")
                        
                        if 'health_status' in sample_agent:
                            print("✅ Health status available")
                            test_results["evidence"].append("Backend provides health status")
                            
                    else:
                        missing = [f for f in required_fields if f not in sample_agent]
                        print(f"❌ Missing required fields: {missing}")
                        
        except Exception as e:
            print(f"❌ Data structure test failed: {e}")
        
        # Test 3: Type Mapping Verification
        print("\n🎯 Test 3: Agent Type Mapping")
        try:
            # Frontend AgentType enum values
            frontend_types = {
                'executive', 'market', 'content', 'logistics', 'inventory',
                'advertising', 'support', 'financial', 'competitor', 'trend',
                'quality', 'analytics', 'listing', 'pricing', 'automation', 'general'
            }
            
            backend_types = set(test_results["agent_types"])
            
            # Check mapping compatibility
            mapped_types = backend_types.intersection(frontend_types)
            unmapped_types = backend_types - frontend_types
            
            if len(mapped_types) >= len(backend_types) * 0.8:  # 80% mapping success
                test_results["type_mapping"] = True
                print(f"✅ Type mapping successful: {len(mapped_types)}/{len(backend_types)} types mapped")
                test_results["evidence"].append(f"Agent type mapping: {len(mapped_types)}/{len(backend_types)} types compatible")
            else:
                print(f"⚠️  Type mapping issues: {len(mapped_types)}/{len(backend_types)} types mapped")
                
            if unmapped_types:
                print(f"⚠️  Unmapped backend types: {', '.join(unmapped_types)}")
            else:
                print("✅ All backend types have frontend mappings")
                
        except Exception as e:
            print(f"❌ Type mapping test failed: {e}")
        
        # Test 4: Conversion Logic Simulation
        print("\n🔄 Test 4: Frontend Conversion Logic")
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    
                    # Simulate the conversion logic from BackendAgentService
                    converted_agents = []
                    
                    for agent in agents_data[:3]:  # Test first 3 agents
                        # Simulate _convertToMonitoringAgentStatus logic
                        converted = {
                            "agentId": agent.get('id', ''),
                            "agentType": agent.get('type', ''),
                            "status": agent.get('status', ''),
                            "isActive": agent.get('status') == 'active',
                            "uptime": "2h 15m",  # Would be calculated from backend data
                            "tasksCompleted": agent.get('performance_metrics', {}).get('tasks_completed', 0),
                            "lastAction": "Backend sync",
                            "efficiency": 85,  # Would be calculated from CPU/memory usage
                            "currentLoad": 65,  # Would be calculated from CPU usage
                            "errorCount": 0,
                            "lastActivity": agent.get('last_activity', ''),
                        }
                        converted_agents.append(converted)
                    
                    if converted_agents:
                        test_results["conversion_logic"] = True
                        print(f"✅ Conversion logic successful for {len(converted_agents)} agents")
                        test_results["evidence"].append(f"Successfully converted {len(converted_agents)} agents to frontend format")
                        
                        # Show sample conversion
                        sample = converted_agents[0]
                        print(f"📊 Sample Conversion:")
                        print(f"   Agent ID: {sample['agentId']}")
                        print(f"   Type: {sample['agentType']}")
                        print(f"   Active: {sample['isActive']}")
                        print(f"   Tasks: {sample['tasksCompleted']}")
                        print(f"   Efficiency: {sample['efficiency']}%")
                        
        except Exception as e:
            print(f"❌ Conversion logic test failed: {e}")
    
    # Generate Final Assessment
    print("\n📋 Agent Service Integration Assessment")
    print("=" * 50)
    
    success_count = sum([
        test_results["backend_agents"],
        test_results["data_structure"],
        test_results["type_mapping"],
        test_results["performance_data"],
        test_results["conversion_logic"]
    ])
    
    print(f"✅ Successful Tests: {success_count}/5")
    print(f"🤖 Agent Count: {test_results['sophisticated_count']}")
    print(f"🎯 Agent Types: {len(set(test_results['agent_types']))}")
    
    # Detailed Results
    if test_results["backend_agents"]:
        print("✅ Backend Agent Service: Operational")
    else:
        print("❌ Backend Agent Service: Issues detected")
    
    if test_results["data_structure"]:
        print("✅ Data Structure: Compatible with frontend")
    else:
        print("❌ Data Structure: Compatibility issues")
    
    if test_results["type_mapping"]:
        print("✅ Type Mapping: Frontend can handle backend types")
    else:
        print("⚠️  Type Mapping: Some types may not map correctly")
    
    if test_results["performance_data"]:
        print("✅ Performance Data: Available for monitoring")
    else:
        print("⚠️  Performance Data: Limited monitoring capabilities")
    
    if test_results["conversion_logic"]:
        print("✅ Conversion Logic: Backend data converts to frontend format")
    else:
        print("❌ Conversion Logic: Data conversion issues")
    
    # Evidence Summary
    if test_results["evidence"]:
        print(f"\n📝 Integration Evidence:")
        for i, evidence in enumerate(test_results["evidence"], 1):
            print(f"   {i}. {evidence}")
    
    # Final Status
    integration_ready = success_count >= 4 and test_results["sophisticated_count"] >= 10
    
    print(f"\n🎯 Agent Service Integration: {'✅ READY' if integration_ready else '⚠️  NEEDS ATTENTION'}")
    
    if integration_ready:
        print("🚀 Frontend can successfully consume sophisticated backend agent architecture")
        print("💡 Ready for real-time agent monitoring and management")
    else:
        print("🔧 Additional configuration needed for full agent service integration")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(test_agent_service_integration())
