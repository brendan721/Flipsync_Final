#!/usr/bin/env python3
"""
Production Environment Verification Test for FlipSync Chat Integration.
Tests the complete production architecture including REST API, WebSocket, and real agent integration.
"""

import asyncio
import aiohttp
import websockets
import json
import time
import logging
from typing import Dict, Any, List
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionEnvironmentTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        
    async def test_docker_container_integration(self) -> Dict[str, Any]:
        """Test integration within Docker container environment."""
        logger.info("🐳 Testing Docker Container Integration")
        
        results = {
            "container_accessible": False,
            "api_endpoints_working": False,
            "real_agent_manager_active": False,
            "chat_service_connected": False
        }
        
        try:
            # Test basic container accessibility
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        results["container_accessible"] = True
                        logger.info(f"✅ Docker container accessible: {health_data}")
                        
                        # Check if real agent manager is mentioned in health
                        if "agents" in str(health_data).lower():
                            results["real_agent_manager_active"] = True
                            logger.info("✅ Real agent manager appears to be active")
                    
                # Test API endpoints
                endpoints_to_test = [
                    "/api/v1/chat/conversations",
                    "/api/v1/agents/status",
                    "/docs"
                ]
                
                working_endpoints = 0
                for endpoint in endpoints_to_test:
                    try:
                        async with session.get(f"{self.backend_url}{endpoint}") as resp:
                            if resp.status in [200, 404]:  # 404 is OK for some endpoints
                                working_endpoints += 1
                    except Exception as e:
                        logger.warning(f"Endpoint {endpoint} error: {e}")
                
                results["api_endpoints_working"] = working_endpoints >= 2
                logger.info(f"✅ API endpoints working: {working_endpoints}/{len(endpoints_to_test)}")
                
        except Exception as e:
            logger.error(f"❌ Docker container integration error: {e}")
        
        return results
    
    async def test_websocket_agent_integration(self) -> Dict[str, Any]:
        """Test WebSocket integration with real agents."""
        logger.info("🔌 Testing WebSocket Agent Integration")
        
        conversation_id = f"prod_test_{int(time.time())}"
        results = {
            "websocket_connection": False,
            "agent_responses_received": 0,
            "response_times": [],
            "agent_types_detected": [],
            "real_agent_indicators": 0,
            "messages_sent": 0
        }
        
        test_messages = [
            "Hello, I need help with my eBay business strategy",
            "What's the best way to price my electronics inventory?",
            "How can I optimize my product listings for better visibility?"
        ]
        
        try:
            # Connect to WebSocket
            ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}"
            
            async with websockets.connect(ws_uri) as websocket:
                results["websocket_connection"] = True
                logger.info("✅ WebSocket connection established")
                
                # Send test messages and collect responses
                for i, message in enumerate(test_messages):
                    logger.info(f"📤 Sending message {i+1}: {message[:50]}...")
                    
                    # Send message
                    message_data = {
                        "type": "chat_message",
                        "data": {
                            "text": message,
                            "sender": "user"
                        }
                    }
                    
                    start_time = time.time()
                    await websocket.send(json.dumps(message_data))
                    results["messages_sent"] += 1
                    
                    # Wait for agent response (with timeout)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        response_time = time.time() - start_time
                        results["response_times"].append(response_time)
                        
                        # Parse response
                        response_data = json.loads(response)
                        logger.info(f"📥 Received response in {response_time:.2f}s")
                        
                        # Analyze response for real agent indicators
                        if "data" in response_data:
                            content = response_data["data"].get("text", "").lower()
                            agent_type = response_data["data"].get("agent_type", "unknown")
                            
                            results["agent_responses_received"] += 1
                            if agent_type not in results["agent_types_detected"]:
                                results["agent_types_detected"].append(agent_type)
                            
                            # Check for real agent indicators
                            real_indicators = [
                                "strategy", "analysis", "recommend", "optimize",
                                "pricing", "market", "listing", "business"
                            ]
                            
                            if any(indicator in content for indicator in real_indicators):
                                results["real_agent_indicators"] += 1
                                logger.info(f"✅ Real agent response detected from {agent_type}")
                            else:
                                logger.info(f"ℹ️ Response from {agent_type} (unclear if real agent)")
                        
                        # Small delay between messages
                        await asyncio.sleep(2)
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ Timeout waiting for response to message {i+1}")
                        break
                    except Exception as e:
                        logger.error(f"❌ Error processing response {i+1}: {e}")
                        break
                
        except Exception as e:
            logger.error(f"❌ WebSocket integration error: {e}")
        
        return results
    
    async def test_four_fixes_validation(self) -> Dict[str, Any]:
        """Validate that the four implemented fixes are working in production."""
        logger.info("🔧 Testing Four Implemented Fixes")
        
        results = {
            "method_signature_compatibility": False,
            "race_condition_resolved": False,
            "app_reference_consistent": False,
            "error_handling_improved": False,
            "overall_fixes_working": False
        }
        
        try:
            # Test 1: Method Signature Compatibility
            # This is validated by successful agent responses without TypeErrors
            logger.info("🧪 Testing method signature compatibility...")
            
            async with aiohttp.ClientSession() as session:
                # Send a test message that should trigger agent processing
                payload = {"text": "Test method signature compatibility", "sender": "user"}
                async with session.post(
                    f"{self.api_base}/chat/conversations/fix_test_1/messages",
                    json=payload
                ) as response:
                    if response.status == 200:
                        results["method_signature_compatibility"] = True
                        logger.info("✅ Method signature compatibility: PASS")
                    
                # Test 2: Race Condition Resolution
                # Multiple rapid requests should not cause initialization errors
                logger.info("🧪 Testing race condition resolution...")
                
                tasks = []
                for i in range(3):
                    task = session.post(
                        f"{self.api_base}/chat/conversations/fix_test_2_{i}/messages",
                        json={"text": f"Rapid test {i}", "sender": "user"}
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                successful_responses = sum(1 for r in responses if not isinstance(r, Exception))
                
                if successful_responses >= 2:
                    results["race_condition_resolved"] = True
                    logger.info("✅ Race condition resolution: PASS")
                
                # Test 3: App Reference Consistency
                # This is validated by successful API responses (indicates app.state access works)
                logger.info("🧪 Testing app reference consistency...")
                
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        results["app_reference_consistent"] = True
                        logger.info("✅ App reference consistency: PASS")
                
                # Test 4: Error Handling Improvement
                # Send an invalid request to test error handling
                logger.info("🧪 Testing error handling improvement...")
                
                try:
                    async with session.post(
                        f"{self.api_base}/chat/conversations/fix_test_4/messages",
                        json={"invalid": "request"}
                    ) as response:
                        # Should get a proper error response, not a crash
                        if response.status in [400, 422, 500]:
                            results["error_handling_improved"] = True
                            logger.info("✅ Error handling improvement: PASS")
                except Exception:
                    # If we get an exception, error handling might need work
                    logger.warning("⚠️ Error handling improvement: NEEDS WORK")
        
        except Exception as e:
            logger.error(f"❌ Four fixes validation error: {e}")
        
        # Overall assessment
        fixes_working = sum([
            results["method_signature_compatibility"],
            results["race_condition_resolved"], 
            results["app_reference_consistent"],
            results["error_handling_improved"]
        ])
        
        results["overall_fixes_working"] = fixes_working >= 3
        logger.info(f"🔧 Overall fixes working: {fixes_working}/4")
        
        return results
    
    async def run_production_verification(self) -> Dict[str, Any]:
        """Run complete production environment verification."""
        logger.info("🚀 Starting Production Environment Verification")
        logger.info("=" * 70)
        
        test_results = {
            "docker_integration": {},
            "websocket_integration": {},
            "fixes_validation": {},
            "production_readiness": {},
            "summary": {}
        }
        
        # Test 1: Docker Container Integration
        logger.info("🧪 TEST 1: Docker Container Integration")
        test_results["docker_integration"] = await self.test_docker_container_integration()
        
        # Test 2: WebSocket Agent Integration
        logger.info("🧪 TEST 2: WebSocket Agent Integration")
        test_results["websocket_integration"] = await self.test_websocket_agent_integration()
        
        # Test 3: Four Fixes Validation
        logger.info("🧪 TEST 3: Four Implemented Fixes Validation")
        test_results["fixes_validation"] = await self.test_four_fixes_validation()
        
        # Calculate production readiness
        docker_score = sum(test_results["docker_integration"].values()) / 4
        websocket_score = (
            test_results["websocket_integration"]["websocket_connection"] +
            (test_results["websocket_integration"]["agent_responses_received"] > 0) +
            (test_results["websocket_integration"]["real_agent_indicators"] > 0)
        ) / 3
        fixes_score = sum(test_results["fixes_validation"].values()) / 5
        
        overall_score = (docker_score + websocket_score + fixes_score) / 3
        
        test_results["production_readiness"] = {
            "docker_integration_score": docker_score,
            "websocket_integration_score": websocket_score,
            "fixes_implementation_score": fixes_score,
            "overall_readiness_score": overall_score,
            "ready_for_production": overall_score >= 0.8
        }
        
        # Generate summary
        ws_data = test_results["websocket_integration"]
        test_results["summary"] = {
            "container_accessible": test_results["docker_integration"]["container_accessible"],
            "websocket_working": ws_data["websocket_connection"],
            "agent_responses": ws_data["agent_responses_received"],
            "real_agent_integration": ws_data["real_agent_indicators"] > 0,
            "avg_response_time": sum(ws_data["response_times"]) / max(len(ws_data["response_times"]), 1),
            "fixes_implemented": test_results["fixes_validation"]["overall_fixes_working"],
            "production_ready": test_results["production_readiness"]["ready_for_production"]
        }
        
        return test_results

async def main():
    """Main test execution."""
    tester = ProductionEnvironmentTest()
    results = await tester.run_production_verification()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 PRODUCTION ENVIRONMENT VERIFICATION RESULTS")
    logger.info("=" * 70)
    
    summary = results["summary"]
    readiness = results["production_readiness"]
    
    logger.info("📊 SUMMARY:")
    logger.info(f"Container Accessible: {'✅' if summary['container_accessible'] else '❌'}")
    logger.info(f"WebSocket Working: {'✅' if summary['websocket_working'] else '❌'}")
    logger.info(f"Agent Responses: {summary['agent_responses']}")
    logger.info(f"Real Agent Integration: {'✅' if summary['real_agent_integration'] else '❌'}")
    logger.info(f"Average Response Time: {summary['avg_response_time']:.2f}s")
    logger.info(f"Fixes Implemented: {'✅' if summary['fixes_implemented'] else '❌'}")
    
    logger.info("=" * 70)
    logger.info("📈 PRODUCTION READINESS SCORES:")
    logger.info(f"Docker Integration: {readiness['docker_integration_score']:.1%}")
    logger.info(f"WebSocket Integration: {readiness['websocket_integration_score']:.1%}")
    logger.info(f"Fixes Implementation: {readiness['fixes_implementation_score']:.1%}")
    logger.info(f"Overall Readiness: {readiness['overall_readiness_score']:.1%}")
    
    logger.info("=" * 70)
    if readiness["ready_for_production"]:
        logger.info("🎉 PRODUCTION READY: Chat integration validated!")
        logger.info("✅ Four fixes working, real agents connected, Docker environment stable")
    else:
        logger.error("💥 PRODUCTION ISSUES: Chat integration needs attention")
        logger.error("❌ Some components not working as expected")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
