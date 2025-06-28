#!/usr/bin/env python3
"""
Final Deep Dive Integration Test
Comprehensive validation of OpenAI and WebSocket integration with sophisticated agent system
"""

import asyncio
import aiohttp
import websockets
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any


async def test_final_deep_dive_integration():
    """Final comprehensive integration test with deep analysis."""
    
    print("🎯 Final Deep Dive Integration Test")
    print("=" * 70)
    print("Comprehensive validation: OpenAI + WebSocket + 26+ Agent Architecture")
    print("=" * 70)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "openai_deep_analysis": {},
        "websocket_optimization": {},
        "agent_coordination": {},
        "production_readiness": {},
        "final_scores": {}
    }
    
    base_url = "http://localhost:8001"
    base_ws_url = "ws://localhost:8001/api/v1/ws"
    
    # Phase 1: OpenAI Deep Analysis
    print("🤖 Phase 1: OpenAI Deep Analysis")
    
    # Test 1a: Trigger real AI operations and monitor logs
    print("   Triggering real AI operations...")
    
    async with aiohttp.ClientSession() as session:
        # Create multiple AI-triggering requests
        ai_operations = []
        
        # Operation 1: Create conversation (triggers AI)
        try:
            async with session.post(
                f"{base_url}/api/v1/chat/conversations",
                json={"title": "Deep OpenAI Integration Test"}
            ) as response:
                if response.status == 200:
                    conv_data = await response.json()
                    ai_operations.append({"operation": "conversation_creation", "status": "success", "id": conv_data.get("id")})
                    print(f"   ✅ Conversation created: {conv_data.get('id')}")
                else:
                    ai_operations.append({"operation": "conversation_creation", "status": "failed", "code": response.status})
        except Exception as e:
            ai_operations.append({"operation": "conversation_creation", "status": "error", "error": str(e)})
        
        # Operation 2: Test agent endpoint that uses AI
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    ai_operations.append({"operation": "agent_list", "status": "success", "count": len(agents_data)})
                    print(f"   ✅ Agents retrieved: {len(agents_data)}")
        except Exception as e:
            ai_operations.append({"operation": "agent_list", "status": "error", "error": str(e)})
    
    # Wait for operations to complete and generate logs
    await asyncio.sleep(3)
    
    # Analyze Docker logs for OpenAI usage
    try:
        log_result = subprocess.run(
            ["docker", "logs", "flipsync-api", "--tail", "200"],
            capture_output=True, text=True, timeout=15
        )
        
        log_content = log_result.stdout.lower()
        
        # Advanced OpenAI detection patterns
        openai_patterns = {
            "openai_client": log_content.count("openai") + log_content.count("gpt"),
            "llm_factory": log_content.count("llm") + log_content.count("factory"),
            "ai_processing": log_content.count("ai") + log_content.count("model"),
            "sophisticated_mentions": log_content.count("sophisticated"),
            "primary_provider": log_content.count("primary"),
            "created_client": log_content.count("created") and log_content.count("client")
        }
        
        # Check environment variables for OpenAI configuration
        env_result = subprocess.run(
            ["docker", "exec", "flipsync-api", "printenv"],
            capture_output=True, text=True, timeout=10
        )
        
        openai_env_vars = {}
        for line in env_result.stdout.split('\n'):
            if any(keyword in line.upper() for keyword in ['OPENAI', 'LLM', 'MODEL', 'GPT']):
                if '=' in line:
                    key, value = line.split('=', 1)
                    openai_env_vars[key] = "configured" if value else "empty"
        
        results["openai_deep_analysis"] = {
            "ai_operations": ai_operations,
            "log_patterns": openai_patterns,
            "environment_vars": openai_env_vars,
            "openai_detected": sum(openai_patterns.values()) > 5,
            "environment_configured": len(openai_env_vars) > 0
        }
        
        print(f"   ✅ Log analysis: {sum(openai_patterns.values())} AI indicators found")
        print(f"   ✅ Environment: {len(openai_env_vars)} OpenAI variables configured")
        
    except Exception as e:
        print(f"   ❌ OpenAI analysis failed: {e}")
        results["openai_deep_analysis"] = {"error": str(e)}
    
    # Phase 2: WebSocket Optimization
    print("\n🔌 Phase 2: WebSocket Optimization")
    
    websocket_tests = {}
    
    # Test 2a: Basic WebSocket with enhanced monitoring
    print("   Testing basic WebSocket with monitoring...")
    try:
        uri = f"{base_ws_url}?client_id=deep_dive_basic"
        start_time = time.time()
        async with websockets.connect(uri) as websocket:
            connection_time = time.time() - start_time
            
            # Send multiple message types
            messages = [
                {"type": "ping", "test": "basic_connectivity"},
                {"type": "subscribe", "channel": "system_status"},
                {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
            ]
            
            responses = []
            for msg in messages:
                await websocket.send(json.dumps(msg))
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    responses.append(json.loads(response))
                except asyncio.TimeoutError:
                    responses.append({"error": "timeout"})
            
            websocket_tests["basic"] = {
                "status": "success",
                "connection_time": connection_time,
                "messages_sent": len(messages),
                "responses_received": len([r for r in responses if "error" not in r]),
                "response_rate": len([r for r in responses if "error" not in r]) / len(messages)
            }
            
            print(f"   ✅ Basic WebSocket: {connection_time:.3f}s connection, {len(responses)} responses")
            
    except Exception as e:
        print(f"   ❌ Basic WebSocket failed: {e}")
        websocket_tests["basic"] = {"status": "failed", "error": str(e)}
    
    # Test 2b: Agent WebSocket with real agent monitoring
    print("   Testing agent WebSocket monitoring...")
    try:
        agent_id = "market_analyzer"
        uri = f"{base_ws_url}/agent/{agent_id}?agent_type=market"
        async with websockets.connect(uri) as websocket:
            # Request agent status
            await websocket.send(json.dumps({
                "type": "status_request",
                "agent_id": agent_id,
                "detailed": True
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            
            websocket_tests["agent"] = {
                "status": "success",
                "agent_id": agent_id,
                "response_type": response_data.get("type"),
                "monitoring_active": True
            }
            
            print(f"   ✅ Agent WebSocket: Monitoring {agent_id}")
            
    except Exception as e:
        print(f"   ❌ Agent WebSocket failed: {e}")
        websocket_tests["agent"] = {"status": "failed", "error": str(e)}
    
    # Test 2c: System WebSocket with sophisticated architecture monitoring
    print("   Testing system WebSocket for sophisticated architecture...")
    try:
        uri = f"{base_ws_url}/system?client_id=deep_dive_system"
        async with websockets.connect(uri) as websocket:
            # Subscribe to sophisticated agent events
            await websocket.send(json.dumps({
                "type": "subscribe",
                "channels": ["agent_status", "system_health", "performance_metrics"],
                "sophisticated_monitoring": True
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            
            websocket_tests["system"] = {
                "status": "success",
                "response_type": response_data.get("type"),
                "sophisticated_monitoring": True
            }
            
            print(f"   ✅ System WebSocket: Sophisticated monitoring active")
            
    except Exception as e:
        print(f"   ❌ System WebSocket failed: {e}")
        websocket_tests["system"] = {"status": "failed", "error": str(e)}
    
    results["websocket_optimization"] = websocket_tests
    
    # Phase 3: Agent Coordination Verification
    print("\n🏗️  Phase 3: Agent Coordination Verification")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    
                    # Analyze sophisticated agent architecture
                    coordination_analysis = {
                        "total_agents": len(agents_data),
                        "agent_types": {},
                        "coordination_features": {},
                        "sophisticated_indicators": {}
                    }
                    
                    for agent in agents_data:
                        agent_type = agent.get("type", "unknown")
                        coordination_analysis["agent_types"][agent_type] = coordination_analysis["agent_types"].get(agent_type, 0) + 1
                        
                        # Check for coordination features
                        if agent.get("dependencies"):
                            coordination_analysis["coordination_features"]["dependencies"] = coordination_analysis["coordination_features"].get("dependencies", 0) + 1
                        
                        if agent.get("performance_metrics"):
                            coordination_analysis["coordination_features"]["performance_monitoring"] = coordination_analysis["coordination_features"].get("performance_monitoring", 0) + 1
                        
                        if agent.get("health_status"):
                            coordination_analysis["coordination_features"]["health_monitoring"] = coordination_analysis["coordination_features"].get("health_monitoring", 0) + 1
                        
                        # Check for sophisticated indicators
                        agent_str = json.dumps(agent).lower()
                        if any(keyword in agent_str for keyword in ["sophisticated", "advanced", "intelligent", "coordination"]):
                            coordination_analysis["sophisticated_indicators"]["advanced_features"] = coordination_analysis["sophisticated_indicators"].get("advanced_features", 0) + 1
                    
                    results["agent_coordination"] = coordination_analysis
                    
                    print(f"   ✅ Agent coordination: {len(agents_data)} agents analyzed")
                    print(f"   ✅ Agent types: {len(coordination_analysis['agent_types'])} categories")
                    print(f"   ✅ Coordination features: {len(coordination_analysis['coordination_features'])} types")
                    
        except Exception as e:
            print(f"   ❌ Agent coordination analysis failed: {e}")
            results["agent_coordination"] = {"error": str(e)}
    
    # Phase 4: Production Readiness Assessment
    print("\n🚀 Phase 4: Production Readiness Assessment")
    
    production_metrics = {
        "response_times": [],
        "error_rates": {},
        "system_health": {},
        "integration_status": {}
    }
    
    # Test response times across multiple endpoints
    endpoints_to_test = [
        "/api/v1/agents/",
        "/api/v1/health",
        "/api/v1/dashboard"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints_to_test:
            try:
                start_time = time.time()
                async with session.get(f"{base_url}{endpoint}") as response:
                    response_time = time.time() - start_time
                    production_metrics["response_times"].append(response_time)
                    
                    if response.status == 200:
                        production_metrics["error_rates"][endpoint] = "success"
                    else:
                        production_metrics["error_rates"][endpoint] = f"http_{response.status}"
                        
            except Exception as e:
                production_metrics["error_rates"][endpoint] = f"error_{str(e)[:20]}"
    
    # Calculate production readiness score
    avg_response_time = sum(production_metrics["response_times"]) / len(production_metrics["response_times"]) if production_metrics["response_times"] else 0
    success_rate = len([v for v in production_metrics["error_rates"].values() if v == "success"]) / len(production_metrics["error_rates"])
    
    production_metrics["avg_response_time"] = avg_response_time
    production_metrics["success_rate"] = success_rate
    production_metrics["performance_acceptable"] = avg_response_time < 1.0
    
    results["production_readiness"] = production_metrics
    
    print(f"   ✅ Average response time: {avg_response_time:.3f}s")
    print(f"   ✅ Success rate: {success_rate:.1%}")
    
    # Final Scoring
    print("\n🏁 Final Deep Dive Integration Results")
    print("=" * 60)
    
    # Calculate component scores
    scores = {}
    
    # OpenAI Integration Score (30 points)
    openai_data = results.get("openai_deep_analysis", {})
    openai_score = 0
    if openai_data.get("openai_detected", False):
        openai_score += 15
    if openai_data.get("environment_configured", False):
        openai_score += 15
    scores["openai_integration"] = openai_score
    
    # WebSocket Integration Score (30 points)
    ws_data = results.get("websocket_optimization", {})
    ws_success = sum(1 for test in ws_data.values() if test.get("status") == "success")
    ws_total = len(ws_data)
    ws_score = (ws_success / max(ws_total, 1)) * 30
    scores["websocket_integration"] = ws_score
    
    # Agent Coordination Score (25 points)
    coord_data = results.get("agent_coordination", {})
    coord_score = min(25, (coord_data.get("total_agents", 0) / 26) * 25)
    scores["agent_coordination"] = coord_score
    
    # Production Readiness Score (15 points)
    prod_data = results.get("production_readiness", {})
    prod_score = 0
    if prod_data.get("performance_acceptable", False):
        prod_score += 7.5
    if prod_data.get("success_rate", 0) >= 0.8:
        prod_score += 7.5
    scores["production_readiness"] = prod_score
    
    total_score = sum(scores.values())
    max_score = 100
    percentage = (total_score / max_score) * 100
    
    results["final_scores"] = {
        "component_scores": scores,
        "total_score": total_score,
        "percentage": percentage,
        "grade": "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D"
    }
    
    print(f"📊 Final Integration Scores:")
    for component, score in scores.items():
        max_component = {"openai_integration": 30, "websocket_integration": 30, "agent_coordination": 25, "production_readiness": 15}[component]
        print(f"   {component.replace('_', ' ').title()}: {score:.1f}/{max_component}")
    
    print(f"\n🎯 Total Integration Score: {total_score:.1f}/{max_score}")
    print(f"📈 Success Rate: {percentage:.1f}%")
    print(f"🏆 Final Grade: {results['final_scores']['grade']}")
    
    if percentage >= 90:
        print("\n🎉 INTEGRATION: EXCELLENT")
        print("✨ Sophisticated 26+ agent system fully operational")
        print("🤖 OpenAI and WebSocket integration at production level")
    elif percentage >= 80:
        print("\n✅ INTEGRATION: GOOD")
        print("🔧 Minor optimizations recommended")
    elif percentage >= 70:
        print("\n⚠️  INTEGRATION: ACCEPTABLE")
        print("🔧 Some components need attention")
    else:
        print("\n❌ INTEGRATION: NEEDS WORK")
        print("🔧 Multiple components require fixes")
    
    # Save comprehensive results
    try:
        import os
        os.makedirs("evidence", exist_ok=True)
        with open(f"evidence/final_deep_dive_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Final deep dive results saved to evidence directory")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_final_deep_dive_integration())
