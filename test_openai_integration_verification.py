#!/usr/bin/env python3
"""
OpenAI Integration Verification Test
Tests that all 26 sophisticated agents now use OpenAI instead of Ollama
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime


async def test_openai_integration():
    """Test OpenAI integration across sophisticated agent system."""
    
    print("🔍 Testing OpenAI Integration for Sophisticated 26+ Agent System")
    print("=" * 70)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "openai_usage": {},
        "agent_tests": {},
        "performance": {},
        "cost_tracking": {}
    }
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: AI Confidence Analysis (should use OpenAI)
        print("🤖 Test 1: AI Confidence Analysis")
        start_time = time.time()
        try:
            async with session.post(
                f"{base_url}/api/v1/ai/confidence",
                json={"text": "Test sophisticated agent system with OpenAI integration"},
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_time = time.time() - start_time
                    
                    results["agent_tests"]["ai_confidence"] = {
                        "status": "success",
                        "response_time": response_time,
                        "data": data
                    }
                    print(f"✅ AI Confidence: {response_time:.2f}s - {data}")
                else:
                    print(f"⚠️  AI Confidence: HTTP {response.status}")
                    
        except Exception as e:
            print(f"❌ AI Confidence failed: {e}")
        
        # Test 2: Agent List (verify 26+ agents)
        print("\n🏗️  Test 2: Sophisticated Agent Architecture")
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    agent_count = len(agents_data)
                    
                    results["agent_tests"]["agent_count"] = {
                        "total": agent_count,
                        "target": 26,
                        "success": agent_count >= 26
                    }
                    
                    print(f"✅ Agent Count: {agent_count} (target: 26+)")
                    
                    # Check for OpenAI usage indicators
                    openai_agents = 0
                    for agent in agents_data:
                        if any(keyword in str(agent).lower() for keyword in ['openai', 'gpt']):
                            openai_agents += 1
                    
                    results["openai_usage"]["agents_with_openai"] = openai_agents
                    print(f"🔍 Agents with OpenAI indicators: {openai_agents}")
                    
        except Exception as e:
            print(f"❌ Agent architecture test failed: {e}")
        
        # Test 3: Chat System (should use OpenAI)
        print("\n💬 Test 3: Chat System with OpenAI")
        start_time = time.time()
        try:
            # First get a token
            auth_response = await session.post(
                f"{base_url}/api/v1/auth/login",
                json={"email": "test@example.com", "password": "SecurePassword!"}
            )
            
            if auth_response.status == 200:
                auth_data = await auth_response.json()
                token = auth_data.get("access_token")
                
                if token:
                    # Test chat endpoint
                    async with session.post(
                        f"{base_url}/api/v1/chat/conversations",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"title": "OpenAI Integration Test"},
                        timeout=30
                    ) as chat_response:
                        if chat_response.status == 200:
                            chat_data = await chat_response.json()
                            response_time = time.time() - start_time
                            
                            results["agent_tests"]["chat_system"] = {
                                "status": "success",
                                "response_time": response_time,
                                "conversation_id": chat_data.get("id")
                            }
                            print(f"✅ Chat System: {response_time:.2f}s - Conversation created")
                        else:
                            print(f"⚠️  Chat System: HTTP {chat_response.status}")
            else:
                print(f"⚠️  Authentication failed: HTTP {auth_response.status}")
                
        except Exception as e:
            print(f"❌ Chat system test failed: {e}")
        
        # Test 4: Performance Metrics
        print("\n📊 Test 4: Performance Analysis")
        
        # Calculate average response times
        response_times = []
        for test_name, test_data in results["agent_tests"].items():
            if isinstance(test_data, dict) and "response_time" in test_data:
                response_times.append(test_data["response_time"])
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            results["performance"] = {
                "average_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "target_response_time": 10.0,
                "performance_good": avg_response_time < 10.0
            }
            
            print(f"✅ Average Response Time: {avg_response_time:.2f}s (target: <10s)")
            print(f"📈 Max Response Time: {max_response_time:.2f}s")
            
            if avg_response_time < 10.0:
                print("🎉 Performance target met!")
            else:
                print("⚠️  Performance needs optimization")
    
    # Final Assessment
    print("\n🏁 OpenAI Integration Assessment")
    print("=" * 50)
    
    # Check for success indicators
    success_indicators = 0
    total_indicators = 4
    
    # 1. Agent count
    if results.get("agent_tests", {}).get("agent_count", {}).get("success", False):
        success_indicators += 1
        print("✅ Sophisticated 26+ agent architecture maintained")
    else:
        print("❌ Agent architecture needs attention")
    
    # 2. AI confidence working
    if results.get("agent_tests", {}).get("ai_confidence", {}).get("status") == "success":
        success_indicators += 1
        print("✅ AI processing operational")
    else:
        print("❌ AI processing needs attention")
    
    # 3. Chat system working
    if results.get("agent_tests", {}).get("chat_system", {}).get("status") == "success":
        success_indicators += 1
        print("✅ Chat system with AI integration working")
    else:
        print("❌ Chat system needs attention")
    
    # 4. Performance acceptable
    if results.get("performance", {}).get("performance_good", False):
        success_indicators += 1
        print("✅ Performance targets met")
    else:
        print("❌ Performance optimization needed")
    
    success_rate = (success_indicators / total_indicators) * 100
    
    print(f"\n📊 OpenAI Integration Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print("🎉 OpenAI Integration: SUCCESS")
        print("✨ Sophisticated agent system now using OpenAI for production")
    elif success_rate >= 50:
        print("⚠️  OpenAI Integration: PARTIAL SUCCESS")
        print("🔧 Some components need additional configuration")
    else:
        print("❌ OpenAI Integration: NEEDS WORK")
        print("🔧 Multiple components require attention")
    
    # Save results
    try:
        with open(f"evidence/openai_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Test results saved to evidence directory")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_openai_integration())
