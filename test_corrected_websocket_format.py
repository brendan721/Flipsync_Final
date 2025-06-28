#!/usr/bin/env python3
"""
Corrected WebSocket Format Test for FlipSync.
Tests WebSocket with proper message format to verify agent responses are received.
"""

import asyncio
import websockets
import jwt
import json
import time
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CorrectedWebSocketFormatTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        
        # JWT configuration
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"
        
    def generate_test_jwt_token(self, user_id: str = "corrected_test_user") -> str:
        """Generate a valid JWT token for testing."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": f"corrected_token_{int(time.time())}",
            "roles": ["user"],
            "permissions": ["chat", "websocket"]
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def test_corrected_message_format(self) -> Dict[str, Any]:
        """Test WebSocket with corrected message format matching Flutter app."""
        logger.info("🔧 Testing Corrected WebSocket Message Format")
        
        conversation_id = f"corrected_format_test_{int(time.time())}"
        user_id = "corrected_format_user"
        client_id = f"client_{int(time.time())}"
        
        # Generate JWT token
        jwt_token = self.generate_test_jwt_token(user_id)
        
        results = {
            "connection_successful": False,
            "authentication_successful": False,
            "messages_sent": 0,
            "agent_responses_received": 0,
            "response_times": [],
            "agent_types": [],
            "message_validation_passed": False,
            "detailed_responses": [],
            "error_details": None
        }
        
        # Correct WebSocket URL
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        
        logger.info(f"🔌 Connecting to WebSocket with corrected format")
        logger.info(f"📍 URL: /api/v1/ws/chat/{conversation_id}")
        
        try:
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                results["authentication_successful"] = True
                logger.info("✅ WebSocket connection and authentication successful!")
                
                # Test messages using CORRECT format (matching Flutter app)
                test_messages = [
                    {
                        "type": "message",  # CORRECTED: was 'chat_message', now 'message'
                        "conversation_id": conversation_id,
                        "data": {
                            "id": f"msg_{int(time.time())}_1",
                            "content": "Hello, I need strategic business guidance for my eBay store. Can you help me analyze my current performance and suggest improvements?",
                            "sender": "user",
                            "timestamp": datetime.now().isoformat()
                        }
                    },
                    {
                        "type": "message",  # CORRECTED: was 'chat_message', now 'message'
                        "conversation_id": conversation_id,
                        "data": {
                            "id": f"msg_{int(time.time())}_2",
                            "content": "I have 100 electronics items in my inventory. What's the best pricing strategy to maximize my profits while staying competitive?",
                            "sender": "user",
                            "timestamp": datetime.now().isoformat()
                        }
                    },
                    {
                        "type": "message",  # CORRECTED: was 'chat_message', now 'message'
                        "conversation_id": conversation_id,
                        "data": {
                            "id": f"msg_{int(time.time())}_3",
                            "content": "Can you optimize my product listings for better visibility and conversion rates?",
                            "sender": "user",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                ]
                
                for i, message in enumerate(test_messages):
                    logger.info(f"📤 Sending corrected message {i+1}")
                    logger.info(f"📋 Message format: type='{message['type']}', conversation_id='{message['conversation_id']}'")
                    
                    start_time = time.time()
                    await websocket.send(json.dumps(message))
                    results["messages_sent"] += 1
                    results["message_validation_passed"] = True  # If we get here, validation passed
                    
                    # Wait for agent response with extended timeout
                    response_received = False
                    timeout_attempts = 0
                    max_timeout_attempts = 6  # 60 seconds total
                    
                    while not response_received and timeout_attempts < max_timeout_attempts:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                            response_time = time.time() - start_time
                            results["response_times"].append(response_time)
                            
                            # Parse response
                            response_data = json.loads(response)
                            logger.info(f"📥 Received response in {response_time:.2f}s")
                            logger.info(f"📋 Response type: {response_data.get('type', 'unknown')}")
                            
                            # Check for agent response
                            if "data" in response_data:
                                data = response_data["data"]
                                sender = data.get("sender", "unknown")
                                agent_type = data.get("agent_type", "unknown")
                                content = data.get("content", data.get("text", ""))
                                
                                logger.info(f"📋 Response sender: {sender}")
                                logger.info(f"📋 Response agent_type: {agent_type}")
                                logger.info(f"📋 Response content preview: {content[:100]}...")
                                
                                # Record detailed response
                                results["detailed_responses"].append({
                                    "message_index": i + 1,
                                    "response_time": response_time,
                                    "response_type": response_data.get("type"),
                                    "sender": sender,
                                    "agent_type": agent_type,
                                    "content_length": len(content),
                                    "content_preview": content[:200]
                                })
                                
                                if sender == "agent" or agent_type != "unknown":
                                    results["agent_responses_received"] += 1
                                    if agent_type not in results["agent_types"]:
                                        results["agent_types"].append(agent_type)
                                    logger.info(f"✅ Agent response detected from {agent_type}")
                                    response_received = True
                                else:
                                    logger.info(f"ℹ️ Non-agent response received: {sender}")
                            else:
                                logger.info(f"ℹ️ Response without data field: {response_data}")
                            
                        except asyncio.TimeoutError:
                            timeout_attempts += 1
                            logger.info(f"⏰ Timeout {timeout_attempts}/{max_timeout_attempts} waiting for response to message {i+1}")
                            
                            if timeout_attempts >= max_timeout_attempts:
                                logger.warning(f"⏰ Max timeouts reached for message {i+1}")
                                break
                        except Exception as e:
                            logger.error(f"❌ Error processing response {i+1}: {e}")
                            break
                    
                    # Small delay between messages
                    await asyncio.sleep(3)
                
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"❌ WebSocket connection failed with status {e.status_code}")
            results["error_details"] = f"HTTP {e.status_code}: {e}"
            
            if e.status_code == 422:
                logger.error("🔍 HTTP 422 - Message format validation failed")
                logger.error("💡 This indicates the message format is still incorrect")
                results["message_validation_passed"] = False
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            results["error_details"] = str(e)
        
        return results
    
    async def run_corrected_format_test(self) -> Dict[str, Any]:
        """Run the corrected format test."""
        logger.info("🚀 Starting Corrected WebSocket Format Test")
        logger.info("=" * 70)
        
        test_results = {
            "corrected_format_test": {},
            "validation_summary": {}
        }
        
        # Test: Corrected Message Format
        logger.info("🧪 TEST: Corrected WebSocket Message Format")
        test_results["corrected_format_test"] = await self.test_corrected_message_format()
        
        # Generate validation summary
        format_test = test_results["corrected_format_test"]
        test_results["validation_summary"] = {
            "connection_successful": format_test["connection_successful"],
            "message_validation_passed": format_test["message_validation_passed"],
            "agent_responses_received": format_test["agent_responses_received"],
            "total_messages_sent": format_test["messages_sent"],
            "agent_types_detected": format_test["agent_types"],
            "avg_response_time": sum(format_test["response_times"]) / max(len(format_test["response_times"]), 1),
            "format_fix_successful": (
                format_test["connection_successful"] and
                format_test["message_validation_passed"] and
                format_test["agent_responses_received"] > 0
            )
        }
        
        return test_results

async def main():
    """Main test execution."""
    tester = CorrectedWebSocketFormatTest()
    results = await tester.run_corrected_format_test()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 CORRECTED WEBSOCKET FORMAT TEST RESULTS")
    logger.info("=" * 70)
    
    # Format Test Results
    format_results = results["corrected_format_test"]
    logger.info("📊 WEBSOCKET FORMAT TEST:")
    logger.info(f"Connection Successful: {'✅' if format_results['connection_successful'] else '❌'}")
    logger.info(f"Message Validation Passed: {'✅' if format_results['message_validation_passed'] else '❌'}")
    logger.info(f"Messages Sent: {format_results['messages_sent']}")
    logger.info(f"Agent Responses Received: {format_results['agent_responses_received']}")
    logger.info(f"Agent Types Detected: {format_results['agent_types']}")
    
    if format_results["response_times"]:
        avg_response_time = sum(format_results["response_times"]) / len(format_results["response_times"])
        logger.info(f"Average Response Time: {avg_response_time:.2f}s")
    
    # Detailed Response Analysis
    if format_results["detailed_responses"]:
        logger.info("📋 DETAILED RESPONSE ANALYSIS:")
        for response in format_results["detailed_responses"]:
            logger.info(f"  Message {response['message_index']}: {response['agent_type']} responded in {response['response_time']:.2f}s")
            logger.info(f"    Content: {response['content_preview'][:100]}...")
    
    if format_results.get("error_details"):
        logger.error(f"Error Details: {format_results['error_details']}")
    
    # Summary
    summary = results["validation_summary"]
    logger.info("=" * 70)
    logger.info("📈 VALIDATION SUMMARY:")
    logger.info(f"Format Fix Successful: {'✅' if summary['format_fix_successful'] else '❌'}")
    logger.info(f"Agent Integration Working: {'✅' if summary['agent_responses_received'] > 0 else '❌'}")
    
    logger.info("=" * 70)
    if summary["format_fix_successful"]:
        logger.info("🎉 SUCCESS: WebSocket format corrected and agent responses received!")
        logger.info("✅ Flutter app can now properly communicate with the 12-agent system")
    else:
        logger.error("💥 ISSUES: WebSocket format or agent integration needs attention")
        
        if not summary["message_validation_passed"]:
            logger.error("❌ Message format validation still failing")
        if summary["agent_responses_received"] == 0:
            logger.error("❌ No agent responses received")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
