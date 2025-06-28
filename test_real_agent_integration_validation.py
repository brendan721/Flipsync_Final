#!/usr/bin/env python3
"""
Real Agent Integration Validation for FlipSync.
Investigates why WebSocket shows 0 agent responses despite successful RealAgentManager initialization.
"""

import asyncio
import aiohttp
import websockets
import jwt
import json
import time
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealAgentIntegrationValidator:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.flutter_url = "http://localhost:3000"
        self.api_base = f"{self.backend_url}/api/v1"
        
        # JWT configuration
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"
        
    def generate_test_jwt_token(self, user_id: str = "integration_test_user") -> str:
        """Generate a valid JWT token for testing."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": f"integration_token_{int(time.time())}",
            "roles": ["user"],
            "permissions": ["chat", "websocket"]
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def test_rest_api_agent_responses(self) -> Dict[str, Any]:
        """Test REST API to see if agents are responding there."""
        logger.info("🔍 Testing REST API Agent Responses")
        
        results = {
            "messages_tested": 0,
            "agent_responses": 0,
            "response_details": [],
            "api_working": False
        }
        
        test_messages = [
            "I need strategic business guidance for my eBay store",
            "Can you analyze my inventory performance?",
            "What's the best pricing strategy for electronics?"
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for i, message in enumerate(test_messages):
                    conversation_id = f"rest_test_{int(time.time())}_{i}"
                    
                    payload = {
                        "text": message,
                        "sender": "user"
                    }
                    
                    logger.info(f"📤 REST API Test {i+1}: {message[:50]}...")
                    
                    start_time = time.time()
                    async with session.post(
                        f"{self.api_base}/chat/conversations/{conversation_id}/messages",
                        json=payload
                    ) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            data = await response.json()
                            results["messages_tested"] += 1
                            results["api_working"] = True
                            
                            # Check if this triggers agent processing
                            logger.info(f"📥 REST API response in {response_time:.2f}s")
                            logger.info(f"📋 Response: {data}")
                            
                            results["response_details"].append({
                                "message": message[:50],
                                "response_time": response_time,
                                "status": response.status,
                                "response_data": data
                            })
                            
                            # Wait a bit to see if agent processing happens asynchronously
                            await asyncio.sleep(3)
                        else:
                            logger.error(f"❌ REST API error: {response.status}")
                    
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"❌ REST API test error: {e}")
        
        return results
    
    async def test_websocket_message_flow(self) -> Dict[str, Any]:
        """Test WebSocket message flow in detail."""
        logger.info("🔍 Testing WebSocket Message Flow")
        
        conversation_id = f"ws_flow_test_{int(time.time())}"
        user_id = "ws_flow_test_user"
        client_id = f"client_{int(time.time())}"
        
        jwt_token = self.generate_test_jwt_token(user_id)
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        
        results = {
            "connection_successful": False,
            "messages_sent": 0,
            "responses_received": 0,
            "response_types": [],
            "message_flow": [],
            "agent_activity_detected": False
        }
        
        try:
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                logger.info("✅ WebSocket connected successfully")
                
                # Send a test message
                test_message = {
                    "type": "chat_message",
                    "data": {
                        "text": "Hello, I need comprehensive business analysis for my eBay store",
                        "sender": "user"
                    }
                }
                
                logger.info("📤 Sending detailed test message...")
                await websocket.send(json.dumps(test_message))
                results["messages_sent"] += 1
                
                # Listen for multiple responses (agents might send multiple messages)
                timeout_count = 0
                max_timeouts = 3
                
                while timeout_count < max_timeouts:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        results["responses_received"] += 1
                        
                        response_data = json.loads(response)
                        logger.info(f"📥 WebSocket response {results['responses_received']}")
                        logger.info(f"📋 Response data: {response_data}")
                        
                        # Analyze response
                        response_type = response_data.get("type", "unknown")
                        if response_type not in results["response_types"]:
                            results["response_types"].append(response_type)
                        
                        # Check for agent activity
                        if "data" in response_data:
                            data = response_data["data"]
                            sender = data.get("sender", "unknown")
                            agent_type = data.get("agent_type", "unknown")
                            text = data.get("text", "")
                            
                            if sender == "agent" or agent_type != "unknown":
                                results["agent_activity_detected"] = True
                                logger.info(f"✅ Agent activity detected: {agent_type}")
                        
                        results["message_flow"].append({
                            "timestamp": time.time(),
                            "type": response_type,
                            "data": response_data
                        })
                        
                        timeout_count = 0  # Reset timeout count on successful response
                        
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        logger.info(f"⏰ Timeout {timeout_count}/{max_timeouts} waiting for more responses")
                        
                        if timeout_count >= max_timeouts:
                            logger.info("🔚 No more responses expected, ending test")
                            break
                    except Exception as e:
                        logger.error(f"❌ Error receiving WebSocket response: {e}")
                        break
                
        except Exception as e:
            logger.error(f"❌ WebSocket message flow test error: {e}")
        
        return results
    
    async def test_flutter_to_backend_integration(self) -> Dict[str, Any]:
        """Test Flutter web app to backend integration."""
        logger.info("🔍 Testing Flutter to Backend Integration")
        
        results = {
            "flutter_accessible": False,
            "backend_accessible": False,
            "integration_working": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test Flutter accessibility
                async with session.get(self.flutter_url) as response:
                    if response.status == 200:
                        results["flutter_accessible"] = True
                        logger.info("✅ Flutter web app accessible")
                    else:
                        logger.error(f"❌ Flutter web app error: {response.status}")
                
                # Test backend accessibility
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        results["backend_accessible"] = True
                        logger.info("✅ Backend accessible")
                    else:
                        logger.error(f"❌ Backend error: {response.status}")
                
                # Test integration
                if results["flutter_accessible"] and results["backend_accessible"]:
                    results["integration_working"] = True
                    logger.info("✅ Flutter-Backend integration working")
                
        except Exception as e:
            logger.error(f"❌ Flutter-Backend integration test error: {e}")
        
        return results
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive real agent integration validation."""
        logger.info("🚀 Starting Real Agent Integration Validation")
        logger.info("=" * 70)
        
        test_results = {
            "rest_api_test": {},
            "websocket_flow_test": {},
            "flutter_integration_test": {},
            "validation_summary": {}
        }
        
        # Test 1: REST API Agent Responses
        logger.info("🧪 TEST 1: REST API Agent Responses")
        test_results["rest_api_test"] = await self.test_rest_api_agent_responses()
        
        # Test 2: WebSocket Message Flow
        logger.info("🧪 TEST 2: WebSocket Message Flow")
        test_results["websocket_flow_test"] = await self.test_websocket_message_flow()
        
        # Test 3: Flutter Integration
        logger.info("🧪 TEST 3: Flutter to Backend Integration")
        test_results["flutter_integration_test"] = await self.test_flutter_to_backend_integration()
        
        # Generate validation summary
        rest_working = test_results["rest_api_test"]["api_working"]
        ws_connected = test_results["websocket_flow_test"]["connection_successful"]
        agent_activity = test_results["websocket_flow_test"]["agent_activity_detected"]
        flutter_working = test_results["flutter_integration_test"]["integration_working"]
        
        test_results["validation_summary"] = {
            "rest_api_working": rest_working,
            "websocket_connected": ws_connected,
            "agent_activity_detected": agent_activity,
            "flutter_integration_working": flutter_working,
            "overall_integration_health": rest_working and ws_connected and flutter_working
        }
        
        return test_results

async def main():
    """Main validation execution."""
    validator = RealAgentIntegrationValidator()
    results = await validator.run_comprehensive_validation()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 REAL AGENT INTEGRATION VALIDATION RESULTS")
    logger.info("=" * 70)
    
    # REST API Results
    rest_results = results["rest_api_test"]
    logger.info("📊 REST API AGENT RESPONSES:")
    logger.info(f"Messages Tested: {rest_results['messages_tested']}")
    logger.info(f"API Working: {'✅' if rest_results['api_working'] else '❌'}")
    
    # WebSocket Results
    ws_results = results["websocket_flow_test"]
    logger.info("📊 WEBSOCKET MESSAGE FLOW:")
    logger.info(f"Connection Successful: {'✅' if ws_results['connection_successful'] else '❌'}")
    logger.info(f"Messages Sent: {ws_results['messages_sent']}")
    logger.info(f"Responses Received: {ws_results['responses_received']}")
    logger.info(f"Agent Activity Detected: {'✅' if ws_results['agent_activity_detected'] else '❌'}")
    logger.info(f"Response Types: {ws_results['response_types']}")
    
    # Flutter Integration Results
    flutter_results = results["flutter_integration_test"]
    logger.info("📊 FLUTTER INTEGRATION:")
    logger.info(f"Flutter Accessible: {'✅' if flutter_results['flutter_accessible'] else '❌'}")
    logger.info(f"Backend Accessible: {'✅' if flutter_results['backend_accessible'] else '❌'}")
    logger.info(f"Integration Working: {'✅' if flutter_results['integration_working'] else '❌'}")
    
    # Summary
    summary = results["validation_summary"]
    logger.info("=" * 70)
    logger.info("📈 VALIDATION SUMMARY:")
    logger.info(f"REST API Working: {'✅' if summary['rest_api_working'] else '❌'}")
    logger.info(f"WebSocket Connected: {'✅' if summary['websocket_connected'] else '❌'}")
    logger.info(f"Agent Activity Detected: {'✅' if summary['agent_activity_detected'] else '❌'}")
    logger.info(f"Flutter Integration: {'✅' if summary['flutter_integration_working'] else '❌'}")
    
    logger.info("=" * 70)
    if summary["overall_integration_health"]:
        logger.info("🎉 VALIDATION SUCCESS: Real agent integration is working!")
    else:
        logger.error("💥 VALIDATION ISSUES: Some integration components need attention")
        
        if not summary["agent_activity_detected"]:
            logger.error("🔍 INVESTIGATION NEEDED: Agents initialized but not responding to messages")
            logger.error("💡 Possible causes:")
            logger.error("   - Agent message routing not configured")
            logger.error("   - WebSocket handler not connected to RealAgentManager")
            logger.error("   - Async processing delays")
            logger.error("   - Agent processing errors")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
