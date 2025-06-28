#!/usr/bin/env python3
"""
Comprehensive WebSocket Integration Test
Tests all WebSocket endpoints and real-time functionality for sophisticated agent system
"""

import asyncio
import websockets
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any


async def test_comprehensive_websocket_integration():
    """Comprehensive WebSocket integration test for sophisticated agent system."""
    
    print("🔌 Comprehensive WebSocket Integration Test")
    print("=" * 60)
    print("Testing sophisticated 26+ agent architecture WebSocket functionality")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "websocket_endpoints": {},
        "real_time_functionality": {},
        "agent_monitoring": {},
        "system_integration": {},
        "performance_metrics": {}
    }
    
    base_ws_url = "ws://localhost:8001/api/v1/ws"
    base_http_url = "http://localhost:8001"
    
    # Test 1: Basic WebSocket Endpoint
    print("🔧 Test 1: Basic WebSocket Endpoint")
    
    try:
        uri = f"{base_ws_url}?client_id=test_comprehensive_basic"
        async with websockets.connect(uri) as websocket:
            # Send test message
            test_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat(),
                "data": {"test": "comprehensive_basic"}
            }
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            
            results["websocket_endpoints"]["basic"] = {
                "status": "success",
                "response_type": response_data.get("type"),
                "connection_established": True
            }
            
            print("✅ Basic WebSocket: Connected and responsive")
            print(f"   Response type: {response_data.get('type')}")
            
    except Exception as e:
        print(f"❌ Basic WebSocket failed: {e}")
        results["websocket_endpoints"]["basic"] = {"status": "failed", "error": str(e)}
    
    # Test 2: Chat WebSocket Endpoint
    print("\n💬 Test 2: Chat WebSocket Endpoint")
    
    try:
        # First create a conversation via HTTP
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_http_url}/api/v1/chat/conversations",
                json={"title": "WebSocket Test Conversation"}
            ) as response:
                if response.status == 200:
                    conv_data = await response.json()
                    conversation_id = conv_data.get("id")
                    
                    # Now test WebSocket chat
                    uri = f"{base_ws_url}/chat/{conversation_id}?client_id=test_comprehensive_chat"
                    async with websockets.connect(uri) as websocket:
                        # Send chat message
                        chat_message = {
                            "type": "message",
                            "conversation_id": conversation_id,
                            "data": {
                                "content": "Test message for sophisticated agent system",
                                "message_type": "user"
                            }
                        }
                        await websocket.send(json.dumps(chat_message))
                        
                        # Wait for response
                        response = await asyncio.wait_for(websocket.recv(), timeout=10)
                        response_data = json.loads(response)
                        
                        results["websocket_endpoints"]["chat"] = {
                            "status": "success",
                            "conversation_id": conversation_id,
                            "response_type": response_data.get("type"),
                            "ai_processing": True
                        }
                        
                        print("✅ Chat WebSocket: Connected and processing")
                        print(f"   Conversation: {conversation_id}")
                        print(f"   Response type: {response_data.get('type')}")
                else:
                    print(f"⚠️  Conversation creation failed: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ Chat WebSocket failed: {e}")
        results["websocket_endpoints"]["chat"] = {"status": "failed", "error": str(e)}
    
    # Test 3: Agent WebSocket Endpoint
    print("\n🤖 Test 3: Agent WebSocket Endpoint")
    
    try:
        agent_id = "executive_agent"
        uri = f"{base_ws_url}/agent/{agent_id}?agent_type=executive"
        async with websockets.connect(uri) as websocket:
            # Send agent status request
            agent_message = {
                "type": "status_request",
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(agent_message))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            
            results["websocket_endpoints"]["agent"] = {
                "status": "success",
                "agent_id": agent_id,
                "response_type": response_data.get("type"),
                "agent_monitoring": True
            }
            
            print("✅ Agent WebSocket: Connected and monitoring")
            print(f"   Agent: {agent_id}")
            print(f"   Response type: {response_data.get('type')}")
            
    except Exception as e:
        print(f"❌ Agent WebSocket failed: {e}")
        results["websocket_endpoints"]["agent"] = {"status": "failed", "error": str(e)}
    
    # Test 4: System WebSocket Endpoint
    print("\n🏗️  Test 4: System WebSocket Endpoint")
    
    try:
        uri = f"{base_ws_url}/system?client_id=test_comprehensive_system"
        async with websockets.connect(uri) as websocket:
            # Send system subscription
            system_message = {
                "type": "subscribe",
                "channel": "agent_status",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(system_message))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            
            results["websocket_endpoints"]["system"] = {
                "status": "success",
                "response_type": response_data.get("type"),
                "system_monitoring": True
            }
            
            print("✅ System WebSocket: Connected and subscribed")
            print(f"   Response type: {response_data.get('type')}")
            
    except Exception as e:
        print(f"❌ System WebSocket failed: {e}")
        results["websocket_endpoints"]["system"] = {"status": "failed", "error": str(e)}
    
    # Test 5: Real-time Agent Monitoring
    print("\n📊 Test 5: Real-time Agent Monitoring")
    
    try:
        # Test WebSocket stats endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_http_url}/api/v1/ws/stats") as response:
                if response.status == 200:
                    stats_data = await response.json()
                    
                    # Test connections endpoint
                    async with session.get(f"{base_http_url}/api/v1/ws/connections") as conn_response:
                        if conn_response.status == 200:
                            conn_data = await conn_response.json()
                            
                            results["real_time_functionality"] = {
                                "stats_available": True,
                                "connections_tracked": True,
                                "active_connections": conn_data.get("stats", {}).get("active_connections", 0),
                                "messages_sent": conn_data.get("stats", {}).get("messages_sent", 0)
                            }
                            
                            print("✅ Real-time monitoring: Functional")
                            print(f"   Active connections: {conn_data.get('stats', {}).get('active_connections', 0)}")
                            print(f"   Messages sent: {conn_data.get('stats', {}).get('messages_sent', 0)}")
                        else:
                            print(f"⚠️  Connections endpoint: HTTP {conn_response.status}")
                else:
                    print(f"⚠️  Stats endpoint: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ Real-time monitoring failed: {e}")
        results["real_time_functionality"] = {"status": "failed", "error": str(e)}
    
    # Test 6: Agent Integration Verification
    print("\n🏗️  Test 6: Agent Integration Verification")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_http_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    
                    # Analyze agent WebSocket capabilities
                    websocket_capable_agents = 0
                    real_time_agents = 0
                    
                    for agent in agents_data:
                        agent_str = json.dumps(agent).lower()
                        if any(keyword in agent_str for keyword in ['websocket', 'real-time', 'monitoring']):
                            websocket_capable_agents += 1
                        if any(keyword in agent_str for keyword in ['status', 'health', 'performance']):
                            real_time_agents += 1
                    
                    results["agent_monitoring"] = {
                        "total_agents": len(agents_data),
                        "websocket_capable": websocket_capable_agents,
                        "real_time_monitoring": real_time_agents,
                        "sophisticated_architecture": len(agents_data) >= 26
                    }
                    
                    print(f"✅ Agent integration: {len(agents_data)} agents")
                    print(f"   WebSocket-capable: {websocket_capable_agents}")
                    print(f"   Real-time monitoring: {real_time_agents}")
                    
    except Exception as e:
        print(f"❌ Agent integration verification failed: {e}")
        results["agent_monitoring"] = {"status": "failed", "error": str(e)}
    
    # Test 7: Performance Metrics
    print("\n📈 Test 7: Performance Metrics")
    
    connection_times = []
    message_times = []
    
    # Test multiple rapid connections
    for i in range(3):
        try:
            start_time = time.time()
            uri = f"{base_ws_url}?client_id=perf_test_{i}"
            async with websockets.connect(uri) as websocket:
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
                
                # Test message round-trip
                msg_start = time.time()
                await websocket.send(json.dumps({"type": "ping", "test_id": i}))
                await websocket.recv()
                message_time = time.time() - msg_start
                message_times.append(message_time)
                
        except Exception as e:
            print(f"   Performance test {i} failed: {e}")
    
    if connection_times and message_times:
        results["performance_metrics"] = {
            "avg_connection_time": sum(connection_times) / len(connection_times),
            "avg_message_time": sum(message_times) / len(message_times),
            "max_connection_time": max(connection_times),
            "max_message_time": max(message_times),
            "performance_acceptable": all(t < 1.0 for t in connection_times + message_times)
        }
        
        avg_conn = sum(connection_times) / len(connection_times)
        avg_msg = sum(message_times) / len(message_times)
        
        print(f"✅ Performance metrics collected")
        print(f"   Avg connection time: {avg_conn:.3f}s")
        print(f"   Avg message time: {avg_msg:.3f}s")
    
    # Final Assessment
    print("\n🏁 Comprehensive WebSocket Integration Results")
    print("=" * 55)
    
    # Calculate scores
    endpoint_score = 0
    total_endpoints = 4
    
    for endpoint, data in results.get("websocket_endpoints", {}).items():
        if data.get("status") == "success":
            endpoint_score += 1
    
    endpoint_percentage = (endpoint_score / total_endpoints) * 100
    
    # Real-time functionality score
    realtime_score = 100 if results.get("real_time_functionality", {}).get("stats_available", False) else 0
    
    # Performance score
    perf_data = results.get("performance_metrics", {})
    performance_score = 100 if perf_data.get("performance_acceptable", False) else 50
    
    # Overall score
    overall_score = (endpoint_percentage * 0.5) + (realtime_score * 0.3) + (performance_score * 0.2)
    
    results["system_integration"] = {
        "endpoint_score": endpoint_percentage,
        "realtime_score": realtime_score,
        "performance_score": performance_score,
        "overall_score": overall_score,
        "grade": "A" if overall_score >= 90 else "B" if overall_score >= 80 else "C" if overall_score >= 70 else "D"
    }
    
    print(f"📊 WebSocket Integration Scores:")
    print(f"   Endpoint Functionality: {endpoint_percentage:.1f}%")
    print(f"   Real-time Features: {realtime_score:.1f}%")
    print(f"   Performance: {performance_score:.1f}%")
    print(f"🎯 Overall WebSocket Score: {overall_score:.1f}%")
    print(f"🏆 Grade: {results['system_integration']['grade']}")
    
    if overall_score >= 90:
        print("\n🎉 WEBSOCKET INTEGRATION: EXCELLENT")
        print("✨ All endpoints functional with real-time capabilities")
        print("🔌 Sophisticated agent monitoring operational")
    elif overall_score >= 80:
        print("\n✅ WEBSOCKET INTEGRATION: GOOD")
        print("🔧 Minor optimizations possible")
    elif overall_score >= 70:
        print("\n⚠️  WEBSOCKET INTEGRATION: ACCEPTABLE")
        print("🔧 Some endpoints need attention")
    else:
        print("\n❌ WEBSOCKET INTEGRATION: NEEDS WORK")
        print("🔧 Multiple endpoints require fixes")
    
    # Save results
    try:
        import os
        os.makedirs("evidence", exist_ok=True)
        with open(f"evidence/comprehensive_websocket_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Comprehensive WebSocket results saved to evidence directory")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_comprehensive_websocket_integration())
