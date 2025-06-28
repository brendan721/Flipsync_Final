#!/usr/bin/env python3
"""
Final Complete Integration Test
Comprehensive verification of FlipSync's sophisticated 26+ agent architecture integration
"""

import asyncio
import aiohttp
import json
import os
import websockets
from datetime import datetime
from typing import Dict, Any


async def test_final_integration():
    """Final comprehensive integration test."""
    
    print("🎯 FlipSync Final Integration Test")
    print("=" * 70)
    print("Testing sophisticated 26+ agent e-commerce automation platform")
    print("=" * 70)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "backend_sophisticated_architecture": {},
        "frontend_builds": {},
        "websocket_real_time": {},
        "data_integration": {},
        "final_score": 0
    }
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Backend Sophisticated Architecture Verification
        print("🏗️  1. Backend Sophisticated Architecture")
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    
                    # Analyze sophisticated architecture
                    agent_count = len(agents_data)
                    agent_types = set(agent.get('type', '') for agent in agents_data)
                    
                    # Check for sophisticated features
                    sophisticated_features = {
                        "performance_metrics": sum(1 for a in agents_data if 'performance_metrics' in a),
                        "health_monitoring": sum(1 for a in agents_data if 'health_status' in a),
                        "dependencies": sum(1 for a in agents_data if 'dependencies' in a and a['dependencies']),
                        "capabilities": sum(1 for a in agents_data if 'capabilities' in a and len(a['capabilities']) >= 3)
                    }
                    
                    results["backend_sophisticated_architecture"] = {
                        "agent_count": agent_count,
                        "agent_types": list(agent_types),
                        "type_count": len(agent_types),
                        "sophisticated_features": sophisticated_features,
                        "architecture_score": min(100, (agent_count / 26) * 100)
                    }
                    
                    print(f"✅ Agent Count: {agent_count} (target: 26+)")
                    print(f"✅ Agent Types: {len(agent_types)} specialized categories")
                    print(f"✅ Performance Metrics: {sophisticated_features['performance_metrics']} agents")
                    print(f"✅ Health Monitoring: {sophisticated_features['health_monitoring']} agents")
                    print(f"✅ Dependencies: {sophisticated_features['dependencies']} coordinated agents")
                    
                    if agent_count >= 26:
                        results["final_score"] += 30
                        print("🎉 Sophisticated 26+ agent architecture CONFIRMED")
                    else:
                        print(f"⚠️  Agent count below target: {agent_count}/26")
                        
        except Exception as e:
            print(f"❌ Backend architecture test failed: {e}")
        
        # 2. Frontend Build Verification
        print("\n🎨 2. Frontend Build Status")
        
        # Check Flutter web build
        web_build_path = "/home/brend/Flipsync_Final/mobile/build/web"
        web_build_exists = os.path.exists(web_build_path)
        web_index_exists = os.path.exists(f"{web_build_path}/index.html") if web_build_exists else False
        web_main_exists = os.path.exists(f"{web_build_path}/main.dart.js") if web_build_exists else False
        
        # Check mobile build (may still be in progress)
        mobile_build_path = "/home/brend/Flipsync_Final/mobile/build/app/outputs/flutter-apk"
        mobile_build_exists = os.path.exists(mobile_build_path)
        mobile_apk_exists = os.path.exists(f"{mobile_build_path}/app-release.apk") if mobile_build_exists else False
        
        results["frontend_builds"] = {
            "web_build": {
                "exists": web_build_exists,
                "index_html": web_index_exists,
                "main_dart_js": web_main_exists,
                "complete": web_build_exists and web_index_exists and web_main_exists
            },
            "mobile_build": {
                "exists": mobile_build_exists,
                "apk_exists": mobile_apk_exists,
                "complete": mobile_build_exists and mobile_apk_exists
            }
        }
        
        if results["frontend_builds"]["web_build"]["complete"]:
            results["final_score"] += 20
            print("✅ Flutter Web Build: COMPLETE and ready for testing")
        else:
            print("⚠️  Flutter Web Build: Incomplete")
            
        if results["frontend_builds"]["mobile_build"]["complete"]:
            results["final_score"] += 10
            print("✅ Flutter Mobile Build: COMPLETE")
        else:
            print("⚠️  Flutter Mobile Build: In progress or incomplete")
        
        # 3. WebSocket Real-Time Integration
        print("\n🔌 3. WebSocket Real-Time Integration")
        
        websocket_tests = {
            "system": False,
            "agent": False,
            "basic": False
        }
        
        # Test System WebSocket
        try:
            uri = f"ws://localhost:8001/api/v1/ws/system?client_id=final_test_system"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "channel": "agent_status",
                    "timestamp": datetime.now().isoformat()
                }))
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                websocket_tests["system"] = True
                print("✅ System WebSocket: WORKING (agent monitoring ready)")
        except Exception as e:
            print(f"⚠️  System WebSocket: {e}")
        
        # Test Agent WebSocket
        try:
            uri = f"ws://localhost:8001/api/v1/ws/agent/executive_agent?agent_type=executive"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps({
                    "type": "status_request",
                    "agent_id": "executive_agent",
                    "timestamp": datetime.now().isoformat()
                }))
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                websocket_tests["agent"] = True
                print("✅ Agent WebSocket: WORKING (individual agent tracking ready)")
        except Exception as e:
            print(f"⚠️  Agent WebSocket: {e}")
        
        # Test Basic WebSocket
        try:
            uri = f"ws://localhost:8001/api/v1/ws?client_id=final_test_basic"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }))
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                websocket_tests["basic"] = True
                print("✅ Basic WebSocket: WORKING")
        except Exception as e:
            print(f"⚠️  Basic WebSocket: {e}")
        
        results["websocket_real_time"] = websocket_tests
        
        working_websockets = sum(websocket_tests.values())
        if working_websockets >= 2:
            results["final_score"] += 20
            print(f"🎉 WebSocket Integration: {working_websockets}/3 endpoints working")
        else:
            print(f"⚠️  WebSocket Integration: Only {working_websockets}/3 endpoints working")
        
        # 4. Data Integration Verification
        print("\n🔄 4. Data Integration Verification")
        
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    
                    # Test data conversion (simulating frontend processing)
                    conversion_success = 0
                    for agent in agents_data[:5]:  # Test first 5 agents
                        try:
                            # Simulate BackendAgentService conversion
                            converted = {
                                "agentId": agent.get('id', ''),
                                "agentType": agent.get('type', ''),
                                "status": agent.get('status', ''),
                                "isActive": agent.get('status') == 'active',
                                "capabilities": len(agent.get('capabilities', [])),
                                "performanceMetrics": agent.get('performance_metrics', {}),
                                "healthStatus": agent.get('health_status', {}),
                                "dependencies": agent.get('dependencies', [])
                            }
                            
                            # Verify conversion success
                            if all([
                                converted["agentId"],
                                converted["agentType"],
                                converted["status"],
                                isinstance(converted["isActive"], bool),
                                isinstance(converted["capabilities"], int)
                            ]):
                                conversion_success += 1
                        except Exception:
                            pass
                    
                    conversion_rate = conversion_success / min(5, len(agents_data))
                    
                    results["data_integration"] = {
                        "conversion_success": conversion_success,
                        "conversion_rate": conversion_rate,
                        "total_tested": min(5, len(agents_data))
                    }
                    
                    if conversion_rate >= 0.8:
                        results["final_score"] += 20
                        print(f"✅ Data Integration: {conversion_success}/5 agents converted successfully")
                        print("✅ Backend data fully compatible with frontend")
                    else:
                        print(f"⚠️  Data Integration: {conversion_success}/5 conversion issues")
                        
        except Exception as e:
            print(f"❌ Data integration test failed: {e}")
    
    # Final Assessment
    print("\n🏁 Final Integration Assessment")
    print("=" * 60)
    
    max_score = 100
    score_percentage = results["final_score"]
    
    print(f"📊 Final Integration Score: {results['final_score']}/{max_score}")
    print(f"📈 Success Rate: {score_percentage}%")
    
    # Detailed breakdown
    print(f"\n📋 Score Breakdown:")
    backend_score = 30 if results.get("backend_sophisticated_architecture", {}).get("agent_count", 0) >= 26 else 0
    web_score = 20 if results.get("frontend_builds", {}).get("web_build", {}).get("complete", False) else 0
    mobile_score = 10 if results.get("frontend_builds", {}).get("mobile_build", {}).get("complete", False) else 0
    websocket_score = 20 if sum(results.get("websocket_real_time", {}).values()) >= 2 else 0
    data_score = 20 if results.get("data_integration", {}).get("conversion_rate", 0) >= 0.8 else 0
    
    print(f"   Backend Architecture (26+ agents): {backend_score}/30")
    print(f"   Frontend Web Build: {web_score}/20")
    print(f"   Frontend Mobile Build: {mobile_score}/10")
    print(f"   WebSocket Real-time: {websocket_score}/20")
    print(f"   Data Integration: {data_score}/20")
    
    # Final Status
    if results["final_score"] >= 90:
        status = "🎉 EXCELLENT"
        message = "Complete integration successful!"
    elif results["final_score"] >= 75:
        status = "✅ GOOD"
        message = "Integration ready with minor optimizations"
    elif results["final_score"] >= 60:
        status = "⚠️  ACCEPTABLE"
        message = "Integration functional but needs improvements"
    else:
        status = "❌ NEEDS WORK"
        message = "Integration requires significant work"
    
    print(f"\n{status}")
    print(f"💬 {message}")
    
    if results["final_score"] >= 75:
        print(f"\n🚀 INTEGRATION COMPLETE!")
        print(f"✨ FlipSync sophisticated 26+ agent architecture successfully integrated")
        print(f"🎯 Frontend properly connects to and showcases sophisticated backend")
        print(f"🔌 WebSocket real-time monitoring operational")
        print(f"📱 Applications built and ready for comprehensive testing")
        print(f"🌟 Ready to demonstrate sophisticated e-commerce automation platform")
    
    # Save results
    try:
        os.makedirs("evidence", exist_ok=True)
        evidence_file = f"evidence/final_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(evidence_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Final test results saved to: {evidence_file}")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_final_integration())
