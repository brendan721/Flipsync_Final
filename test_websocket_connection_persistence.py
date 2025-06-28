#!/usr/bin/env python3
"""
Test WebSocket Connection Persistence during AI Processing.
This test specifically checks why clients are disconnecting before receiving AI responses.
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

class WebSocketPersistenceTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        
        # JWT configuration
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"
        
    def generate_test_jwt_token(self, user_id: str = "persistence_test_user") -> str:
        """Generate a valid JWT token."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": f"persistence_token_{int(time.time())}",
            "roles": ["user"],
            "permissions": ["chat", "websocket"]
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def test_connection_during_ai_processing(self) -> Dict[str, Any]:
        """Test if WebSocket connection persists during AI processing."""
        logger.info("🔍 Testing WebSocket Connection Persistence During AI Processing")
        
        conversation_id = "persistence_test"
        user_id = "persistence_test_user"
        client_id = f"client_{int(time.time())}"
        
        jwt_token = self.generate_test_jwt_token(user_id)
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        
        results = {
            "connection_established": False,
            "message_sent": False,
            "ping_responses_received": 0,
            "connection_maintained_during_ai": False,
            "ai_response_received": False,
            "total_connection_time": 0.0,
            "disconnect_reason": None,
            "messages_received": []
        }
        
        start_time = time.time()
        
        try:
            logger.info(f"🔌 Connecting to: {ws_uri}")
            async with websockets.connect(ws_uri) as websocket:
                results["connection_established"] = True
                logger.info("✅ WebSocket connection established")
                
                # Listen for initial messages
                try:
                    initial_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    initial_data = json.loads(initial_message)
                    results["messages_received"].append(initial_data)
                    logger.info(f"📥 Initial message: {initial_data.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    logger.info("⏰ No initial message received")
                
                # Send a message that will trigger AI processing
                logger.info("📤 Sending message that will trigger AI processing...")
                test_message = {
                    "type": "message",
                    "conversation_id": conversation_id,
                    "data": {
                        "id": f"persistence_msg_{int(time.time())}",
                        "content": "What are the best eBay selling strategies?",
                        "sender": "user",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                await websocket.send(json.dumps(test_message))
                results["message_sent"] = True
                logger.info("✅ Message sent, now monitoring connection during AI processing...")
                
                # Monitor connection for up to 90 seconds (longer than AI processing time)
                monitoring_start = time.time()
                ai_response_received = False
                
                while time.time() - monitoring_start < 90:
                    try:
                        # Wait for any message with a short timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        message_data = json.loads(message)
                        results["messages_received"].append(message_data)
                        
                        message_type = message_data.get("type", "unknown")
                        logger.info(f"📥 Received during AI processing: {message_type}")
                        
                        if message_type == "ping":
                            results["ping_responses_received"] += 1
                            # Respond to ping with pong
                            pong_response = {
                                "type": "pong",
                                "timestamp": time.time(),
                                "data": message_data.get("data", {})
                            }
                            await websocket.send(json.dumps(pong_response))
                            logger.info("🏓 Responded to ping with pong")
                            
                        elif message_type == "message":
                            # This is the AI response
                            ai_response_received = True
                            results["ai_response_received"] = True
                            response_content = message_data.get("data", {}).get("content", "")
                            logger.info(f"🤖 AI response received: {response_content[:100]}...")
                            break
                            
                        elif message_type == "typing":
                            logger.info("⌨️ Typing indicator received")
                        
                    except asyncio.TimeoutError:
                        # No message received in 5 seconds, check if connection is still alive
                        current_time = time.time()
                        elapsed = current_time - monitoring_start
                        logger.info(f"⏰ No message for 5s (total elapsed: {elapsed:.1f}s)")
                        
                        # Try to send a ping to test connection
                        try:
                            ping_message = {
                                "type": "ping",
                                "timestamp": current_time
                            }
                            await websocket.send(json.dumps(ping_message))
                            logger.info("🏓 Sent ping to test connection")
                        except Exception as e:
                            logger.error(f"❌ Failed to send ping: {e}")
                            results["disconnect_reason"] = f"Failed to send ping: {e}"
                            break
                    
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.error(f"❌ WebSocket connection closed: {e}")
                        results["disconnect_reason"] = f"Connection closed: {e}"
                        break
                    
                    except Exception as e:
                        logger.error(f"❌ Error during monitoring: {e}")
                        results["disconnect_reason"] = f"Monitoring error: {e}"
                        break
                
                # Check if connection was maintained throughout AI processing
                if ai_response_received:
                    results["connection_maintained_during_ai"] = True
                    logger.info("✅ Connection maintained during entire AI processing cycle")
                else:
                    logger.warning("⚠️ Connection lost before AI response received")
                
        except Exception as e:
            logger.error(f"❌ Connection test error: {e}")
            results["disconnect_reason"] = str(e)
        
        results["total_connection_time"] = time.time() - start_time
        return results
    
    async def run_persistence_tests(self) -> Dict[str, Any]:
        """Run WebSocket persistence tests."""
        logger.info("🚀 Starting WebSocket Persistence Tests")
        logger.info("=" * 70)
        
        test_results = {
            "persistence_test": {},
            "connection_stable": False,
            "ai_processing_compatible": False,
            "issues_found": [],
            "recommendations": []
        }
        
        # Test connection persistence during AI processing
        logger.info("🧪 TEST: Connection Persistence During AI Processing")
        test_results["persistence_test"] = await self.test_connection_during_ai_processing()
        
        # Analyze results
        persistence_test = test_results["persistence_test"]
        
        # Determine if connection is stable
        test_results["connection_stable"] = (
            persistence_test.get("connection_established", False) and
            persistence_test.get("message_sent", False) and
            persistence_test.get("ping_responses_received", 0) > 0
        )
        
        # Determine if AI processing is compatible
        test_results["ai_processing_compatible"] = (
            persistence_test.get("connection_maintained_during_ai", False) and
            persistence_test.get("ai_response_received", False)
        )
        
        # Identify issues
        if not persistence_test.get("connection_established", False):
            test_results["issues_found"].append("WebSocket connection cannot be established")
        
        if not persistence_test.get("ai_response_received", False):
            test_results["issues_found"].append("AI responses not reaching WebSocket clients")
        
        if persistence_test.get("disconnect_reason"):
            test_results["issues_found"].append(f"Connection disconnect: {persistence_test['disconnect_reason']}")
        
        if persistence_test.get("ping_responses_received", 0) == 0:
            test_results["issues_found"].append("No ping/pong heartbeat detected")
        
        # Generate recommendations
        if not test_results["ai_processing_compatible"]:
            test_results["recommendations"].append("Implement connection keep-alive during AI processing")
            test_results["recommendations"].append("Add progress indicators to keep clients engaged")
        
        if persistence_test.get("total_connection_time", 0) < 30:
            test_results["recommendations"].append("Investigate premature connection termination")
        
        return test_results

async def main():
    """Main test execution."""
    tester = WebSocketPersistenceTest()
    
    # Wait for services to be ready
    logger.info("⏳ Waiting for services to be ready...")
    await asyncio.sleep(3)
    
    results = await tester.run_persistence_tests()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 WEBSOCKET PERSISTENCE TEST RESULTS")
    logger.info("=" * 70)
    
    # Persistence Test Results
    persistence_results = results["persistence_test"]
    logger.info("📊 CONNECTION PERSISTENCE TEST:")
    logger.info(f"Connection Established: {'✅' if persistence_results.get('connection_established') else '❌'}")
    logger.info(f"Message Sent: {'✅' if persistence_results.get('message_sent') else '❌'}")
    logger.info(f"Ping Responses Received: {persistence_results.get('ping_responses_received', 0)}")
    logger.info(f"Connection Maintained During AI: {'✅' if persistence_results.get('connection_maintained_during_ai') else '❌'}")
    logger.info(f"AI Response Received: {'✅' if persistence_results.get('ai_response_received') else '❌'}")
    logger.info(f"Total Connection Time: {persistence_results.get('total_connection_time', 0):.2f}s")
    
    if persistence_results.get("disconnect_reason"):
        logger.error(f"Disconnect Reason: {persistence_results['disconnect_reason']}")
    
    # Overall Assessment
    logger.info("=" * 70)
    logger.info("📈 OVERALL ASSESSMENT:")
    logger.info(f"Connection Stable: {'✅' if results['connection_stable'] else '❌'}")
    logger.info(f"AI Processing Compatible: {'✅' if results['ai_processing_compatible'] else '❌'}")
    
    if results["issues_found"]:
        logger.error("💥 ISSUES FOUND:")
        for issue in results["issues_found"]:
            logger.error(f"   - {issue}")
    
    if results["recommendations"]:
        logger.info("💡 RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            logger.info(f"   - {rec}")
    
    # Message log
    messages = persistence_results.get("messages_received", [])
    if messages:
        logger.info("=" * 70)
        logger.info("📋 MESSAGES RECEIVED DURING TEST:")
        for i, msg in enumerate(messages):
            logger.info(f"   {i+1}. {msg.get('type', 'unknown')}: {str(msg)[:100]}...")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
