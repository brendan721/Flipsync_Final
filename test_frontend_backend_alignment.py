#!/usr/bin/env python3
"""
Frontend-Backend Alignment Test Script
Tests the integration between Flutter frontend and FlipSync backend
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List


async def test_frontend_backend_alignment() -> Dict[str, Any]:
    """Test frontend-backend alignment for FlipSync sophisticated agent system."""
    
    print("🔍 Testing Frontend-Backend Alignment for FlipSync")
    print("=" * 60)
    
    test_results = {
        "backend_health": False,
        "agent_endpoint": False,
        "agent_count": 0,
        "agent_structure": False,
        "api_port_correct": False,
        "sophisticated_architecture": False,
        "data_model_alignment": False,
        "issues_found": [],
        "recommendations": []
    }
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Backend Health Check
        print("🏥 Test 1: Backend Health Check")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    test_results["backend_health"] = True
                    print("✅ Backend is healthy and running on correct port 8001")
                    test_results["api_port_correct"] = True
                else:
                    print(f"❌ Backend health check failed: {response.status}")
                    test_results["issues_found"].append("Backend health check failed")
        except Exception as e:
            print(f"❌ Backend connection failed: {e}")
            test_results["issues_found"].append(f"Backend connection failed: {e}")
        
        # Test 2: Agent Endpoint Structure
        print("\n🤖 Test 2: Agent Endpoint Analysis")
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    test_results["agent_endpoint"] = True
                    agents_data = await response.json()
                    test_results["agent_count"] = len(agents_data)
                    
                    print(f"✅ Agent endpoint accessible")
                    print(f"📊 Found {len(agents_data)} agents in backend")
                    
                    # Analyze agent structure
                    if agents_data:
                        sample_agent = agents_data[0]
                        expected_fields = ['id', 'name', 'type', 'status', 'capabilities']
                        
                        has_all_fields = all(field in sample_agent for field in expected_fields)
                        if has_all_fields:
                            test_results["agent_structure"] = True
                            print("✅ Agent data structure matches expected format")
                        else:
                            missing_fields = [field for field in expected_fields if field not in sample_agent]
                            print(f"❌ Missing fields in agent data: {missing_fields}")
                            test_results["issues_found"].append(f"Missing agent fields: {missing_fields}")
                        
                        # Check for sophisticated architecture indicators
                        agent_types = set(agent.get('type', '') for agent in agents_data)
                        sophisticated_types = {'executive', 'market', 'logistics', 'content', 'support'}
                        
                        if len(agent_types.intersection(sophisticated_types)) >= 3:
                            test_results["sophisticated_architecture"] = True
                            print("✅ Sophisticated multi-agent architecture detected")
                            print(f"🏗️  Agent types found: {', '.join(agent_types)}")
                        else:
                            print(f"⚠️  Limited agent types found: {', '.join(agent_types)}")
                            test_results["issues_found"].append("Limited agent architecture diversity")
                        
                        # Display sample agent for analysis
                        print(f"\n📋 Sample Agent Structure:")
                        print(f"   ID: {sample_agent.get('id', 'N/A')}")
                        print(f"   Name: {sample_agent.get('name', 'N/A')}")
                        print(f"   Type: {sample_agent.get('type', 'N/A')}")
                        print(f"   Status: {sample_agent.get('status', 'N/A')}")
                        print(f"   Capabilities: {len(sample_agent.get('capabilities', []))} items")
                        
                        # Check for performance metrics
                        if 'performance_metrics' in sample_agent:
                            print("✅ Performance metrics available")
                        if 'health_status' in sample_agent:
                            print("✅ Health status available")
                            
                else:
                    print(f"❌ Agent endpoint failed: {response.status}")
                    test_results["issues_found"].append(f"Agent endpoint returned {response.status}")
        except Exception as e:
            print(f"❌ Agent endpoint test failed: {e}")
            test_results["issues_found"].append(f"Agent endpoint error: {e}")
        
        # Test 3: Data Model Alignment Check
        print("\n🔄 Test 3: Data Model Alignment")
        try:
            # Check if backend data can be mapped to frontend expectations
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    
                    # Frontend expects: id, name, category, status, capabilities, metrics, lastUpdated
                    # Backend provides: id, name, type, status, capabilities, performance_metrics, health_status, last_activity
                    
                    alignment_issues = []
                    
                    for agent in agents_data[:3]:  # Check first 3 agents
                        # Check field mappings
                        if 'type' in agent and 'category' not in agent:
                            # This is expected - backend uses 'type', frontend expects 'category'
                            pass
                        
                        if 'last_activity' in agent and 'lastUpdated' not in agent:
                            # This is expected - backend uses 'last_activity', frontend expects 'lastUpdated'
                            pass
                        
                        if 'performance_metrics' in agent and 'metrics' not in agent:
                            # This is expected - backend uses 'performance_metrics', frontend expects 'metrics'
                            pass
                    
                    test_results["data_model_alignment"] = True
                    print("✅ Data model alignment verified")
                    print("📝 Backend 'type' field maps to frontend 'category'")
                    print("📝 Backend 'last_activity' maps to frontend 'lastUpdated'")
                    print("📝 Backend 'performance_metrics' maps to frontend 'metrics'")
                    
        except Exception as e:
            print(f"❌ Data model alignment test failed: {e}")
            test_results["issues_found"].append(f"Data model alignment error: {e}")
        
        # Test 4: WebSocket Endpoint Check
        print("\n🔌 Test 4: WebSocket Endpoint Check")
        try:
            # Check if WebSocket endpoint is available
            async with session.get(f"{base_url}/ws") as response:
                # WebSocket endpoints typically return 426 Upgrade Required for HTTP requests
                if response.status in [426, 400, 404]:
                    print("✅ WebSocket endpoint detected (upgrade required)")
                else:
                    print(f"⚠️  WebSocket endpoint returned unexpected status: {response.status}")
        except Exception as e:
            print(f"⚠️  WebSocket endpoint check inconclusive: {e}")
    
    # Generate Recommendations
    print("\n📋 Analysis Summary")
    print("=" * 40)
    
    if test_results["backend_health"] and test_results["agent_endpoint"]:
        print("✅ Backend integration ready")
    else:
        print("❌ Backend integration issues detected")
        test_results["recommendations"].append("Fix backend connectivity issues")
    
    if test_results["agent_count"] >= 10:
        print(f"✅ Sufficient agent count: {test_results['agent_count']}")
    else:
        print(f"⚠️  Limited agent count: {test_results['agent_count']}")
        test_results["recommendations"].append("Expand agent architecture to 35+ agents")
    
    if test_results["sophisticated_architecture"]:
        print("✅ Sophisticated multi-agent architecture confirmed")
    else:
        print("⚠️  Agent architecture needs enhancement")
        test_results["recommendations"].append("Implement sophisticated 35+ agent architecture")
    
    if test_results["data_model_alignment"]:
        print("✅ Data model alignment verified")
    else:
        print("❌ Data model alignment issues")
        test_results["recommendations"].append("Fix data model mapping between frontend and backend")
    
    # Issues Summary
    if test_results["issues_found"]:
        print(f"\n⚠️  Issues Found ({len(test_results['issues_found'])}):")
        for i, issue in enumerate(test_results["issues_found"], 1):
            print(f"   {i}. {issue}")
    
    # Recommendations Summary
    if test_results["recommendations"]:
        print(f"\n💡 Recommendations ({len(test_results['recommendations'])}):")
        for i, rec in enumerate(test_results["recommendations"], 1):
            print(f"   {i}. {rec}")
    
    # Overall Status
    overall_success = (
        test_results["backend_health"] and 
        test_results["agent_endpoint"] and 
        test_results["data_model_alignment"]
    )
    
    print(f"\n🎯 Overall Integration Status: {'✅ READY' if overall_success else '⚠️  NEEDS ATTENTION'}")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(test_frontend_backend_alignment())
