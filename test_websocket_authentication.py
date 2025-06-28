#!/usr/bin/env python3
"""
WebSocket Authentication Investigation and Testing for FlipSync.
Tests WebSocket connection with proper JWT authentication to resolve HTTP 403 errors.
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

class WebSocketAuthenticationTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        
        # JWT configuration (from websocket_basic.py)
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"
        
    def generate_test_jwt_token(self, user_id: str = "test_user_12345") -> str:
        """Generate a valid JWT token for testing."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,  # Subject (user ID)
            "iat": now,      # Issued at
            "exp": now + timedelta(hours=1),  # Expires in 1 hour
            "jti": f"test_token_{int(time.time())}",  # JWT ID
            "roles": ["user"],
            "permissions": ["chat", "websocket"]
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        logger.info(f"🔑 Generated JWT token for user {user_id}")
        logger.info(f"🔍 Token payload: {payload}")
        
        return token
    
    def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate a JWT token using the same logic as the WebSocket endpoint."""
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm], 
                options={"verify_exp": False}  # Same as WebSocket endpoint
            )
            logger.info(f"✅ Token validation successful: {payload}")
            return payload
        except Exception as e:
            logger.error(f"❌ Token validation failed: {e}")
            return {}
    
    async def test_websocket_with_authentication(self) -> Dict[str, Any]:
        """Test WebSocket connection with proper JWT authentication."""
        logger.info("🔐 Testing WebSocket with JWT Authentication")
        
        conversation_id = f"auth_test_{int(time.time())}"
        user_id = "test_user_websocket"
        client_id = f"client_{int(time.time())}"
        
        # Generate JWT token
        jwt_token = self.generate_test_jwt_token(user_id)
        
        # Validate token locally first
        token_payload = self.validate_jwt_token(jwt_token)
        if not token_payload:
            return {
                "connection_successful": False,
                "error": "JWT token validation failed locally"
            }
        
        results = {
            "connection_successful": False,
            "authentication_successful": False,
            "messages_sent": 0,
            "agent_responses_received": 0,
            "response_times": [],
            "agent_types": [],
            "error_details": None
        }
        
        # Construct WebSocket URL with authentication parameters
        ws_uri = f"{self.ws_url}/api/v1/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        
        logger.info(f"🔌 Connecting to WebSocket: {ws_uri[:100]}...")
        
        try:
            # Attempt WebSocket connection with authentication
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                results["authentication_successful"] = True
                logger.info("✅ WebSocket connection and authentication successful!")
                
                # Test message exchange
                test_messages = [
                    {
                        "type": "chat_message",
                        "data": {
                            "text": "Hello, I need help with my business strategy",
                            "sender": "user"
                        }
                    },
                    {
                        "type": "chat_message", 
                        "data": {
                            "text": "What's the best pricing strategy for electronics?",
                            "sender": "user"
                        }
                    }
                ]
                
                for i, message in enumerate(test_messages):
                    logger.info(f"📤 Sending test message {i+1}")
                    
                    start_time = time.time()
                    await websocket.send(json.dumps(message))
                    results["messages_sent"] += 1
                    
                    # Wait for response with timeout
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        response_time = time.time() - start_time
                        results["response_times"].append(response_time)
                        
                        # Parse response
                        response_data = json.loads(response)
                        logger.info(f"📥 Received response in {response_time:.2f}s")
                        logger.info(f"📋 Response data: {response_data}")
                        
                        # Check for agent response
                        if "data" in response_data:
                            agent_type = response_data["data"].get("agent_type", "unknown")
                            if agent_type not in results["agent_types"]:
                                results["agent_types"].append(agent_type)
                            
                            if response_data["data"].get("sender") == "agent":
                                results["agent_responses_received"] += 1
                                logger.info(f"✅ Agent response received from {agent_type}")
                        
                        # Small delay between messages
                        await asyncio.sleep(2)
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ Timeout waiting for response to message {i+1}")
                        break
                    except Exception as e:
                        logger.error(f"❌ Error processing response {i+1}: {e}")
                        break
                
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"❌ WebSocket connection closed: {e}")
            results["error_details"] = f"Connection closed: {e}"
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"❌ WebSocket connection failed with status {e.status_code}")
            results["error_details"] = f"HTTP {e.status_code}: {e}"
            
            if e.status_code == 403:
                logger.error("🔒 HTTP 403 - Authentication/Authorization failed")
                logger.error("💡 Possible causes:")
                logger.error("   - JWT token invalid or expired")
                logger.error("   - JWT secret mismatch")
                logger.error("   - Missing required parameters")
                logger.error("   - WebSocket endpoint authentication logic changed")
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            results["error_details"] = str(e)
        
        return results
    
    async def test_websocket_without_authentication(self) -> Dict[str, Any]:
        """Test WebSocket connection without authentication to confirm 403 behavior."""
        logger.info("🚫 Testing WebSocket without Authentication (expecting 403)")
        
        conversation_id = f"no_auth_test_{int(time.time())}"
        ws_uri = f"{self.ws_url}/api/v1/chat/{conversation_id}"
        
        results = {
            "connection_attempted": True,
            "expected_403_received": False,
            "error_details": None
        }
        
        try:
            async with websockets.connect(ws_uri) as websocket:
                logger.error("❌ Unexpected: Connection succeeded without authentication!")
                results["expected_403_received"] = False
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 403:
                logger.info("✅ Expected: HTTP 403 received for unauthenticated connection")
                results["expected_403_received"] = True
            else:
                logger.warning(f"⚠️ Unexpected status code: {e.status_code}")
            results["error_details"] = f"HTTP {e.status_code}"
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            results["error_details"] = str(e)
        
        return results
    
    async def run_websocket_authentication_tests(self) -> Dict[str, Any]:
        """Run comprehensive WebSocket authentication tests."""
        logger.info("🚀 Starting WebSocket Authentication Investigation")
        logger.info("=" * 70)
        
        test_results = {
            "jwt_token_generation": False,
            "jwt_token_validation": False,
            "websocket_with_auth": {},
            "websocket_without_auth": {},
            "authentication_working": False,
            "agent_integration_working": False
        }
        
        # Test 1: JWT Token Generation and Validation
        logger.info("🧪 TEST 1: JWT Token Generation and Validation")
        try:
            test_token = self.generate_test_jwt_token()
            test_results["jwt_token_generation"] = bool(test_token)
            
            token_payload = self.validate_jwt_token(test_token)
            test_results["jwt_token_validation"] = bool(token_payload)
            
            logger.info(f"✅ JWT token generation: {'PASS' if test_results['jwt_token_generation'] else 'FAIL'}")
            logger.info(f"✅ JWT token validation: {'PASS' if test_results['jwt_token_validation'] else 'FAIL'}")
        except Exception as e:
            logger.error(f"❌ JWT token test error: {e}")
        
        # Test 2: WebSocket without Authentication (should get 403)
        logger.info("🧪 TEST 2: WebSocket without Authentication")
        test_results["websocket_without_auth"] = await self.test_websocket_without_authentication()
        
        # Test 3: WebSocket with Authentication
        logger.info("🧪 TEST 3: WebSocket with Authentication")
        test_results["websocket_with_auth"] = await self.test_websocket_with_authentication()
        
        # Calculate overall results
        auth_test = test_results["websocket_with_auth"]
        test_results["authentication_working"] = auth_test.get("authentication_successful", False)
        test_results["agent_integration_working"] = auth_test.get("agent_responses_received", 0) > 0
        
        return test_results

async def main():
    """Main test execution."""
    tester = WebSocketAuthenticationTest()
    results = await tester.run_websocket_authentication_tests()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 WEBSOCKET AUTHENTICATION TEST RESULTS")
    logger.info("=" * 70)
    
    logger.info("📊 JWT TOKEN TESTS:")
    logger.info(f"Token Generation: {'✅' if results['jwt_token_generation'] else '❌'}")
    logger.info(f"Token Validation: {'✅' if results['jwt_token_validation'] else '❌'}")
    
    logger.info("📊 WEBSOCKET CONNECTION TESTS:")
    no_auth = results["websocket_without_auth"]
    logger.info(f"Expected 403 without auth: {'✅' if no_auth.get('expected_403_received') else '❌'}")
    
    with_auth = results["websocket_with_auth"]
    logger.info(f"Connection with auth: {'✅' if with_auth.get('connection_successful') else '❌'}")
    logger.info(f"Authentication successful: {'✅' if with_auth.get('authentication_successful') else '❌'}")
    logger.info(f"Messages sent: {with_auth.get('messages_sent', 0)}")
    logger.info(f"Agent responses: {with_auth.get('agent_responses_received', 0)}")
    logger.info(f"Agent types detected: {with_auth.get('agent_types', [])}")
    
    if with_auth.get("response_times"):
        avg_response_time = sum(with_auth["response_times"]) / len(with_auth["response_times"])
        logger.info(f"Average response time: {avg_response_time:.2f}s")
    
    logger.info("=" * 70)
    logger.info("📈 OVERALL ASSESSMENT:")
    logger.info(f"WebSocket Authentication: {'✅ WORKING' if results['authentication_working'] else '❌ FAILED'}")
    logger.info(f"Agent Integration: {'✅ WORKING' if results['agent_integration_working'] else '❌ FAILED'}")
    
    if results["authentication_working"] and results["agent_integration_working"]:
        logger.info("🎉 SUCCESS: WebSocket authentication and agent integration working!")
    elif results["authentication_working"]:
        logger.info("⚠️ PARTIAL: WebSocket authentication working, but agent integration needs attention")
    else:
        logger.error("💥 FAILED: WebSocket authentication not working")
        if with_auth.get("error_details"):
            logger.error(f"Error details: {with_auth['error_details']}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
