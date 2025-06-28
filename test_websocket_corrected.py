#!/usr/bin/env python3
"""
Corrected WebSocket Authentication Test for FlipSync 12-Agent System.
Tests WebSocket connection with proper URL and validates all 12 agents.
"""

import asyncio
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

class CorrectedWebSocketTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        
        # JWT configuration (from websocket_basic.py)
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"
        
        # Expected 12-agent system architecture
        self.expected_agents = [
            "amazon_agent",      # Marketplace agent
            "ebay_agent",        # Marketplace agent  
            "inventory_agent",   # Inventory management
            "executive_agent",   # Strategic coordination
            "content_agent",     # Content optimization
            "logistics_agent",   # Logistics and shipping
            "market_agent",      # Market analysis
            "listing_agent",     # Listing optimization
            "auto_pricing_agent", # Automated pricing
            "auto_listing_agent", # Automated listing
            "auto_inventory_agent", # Automated inventory
            "ai_executive_agent"  # AI-powered executive
        ]
        
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
        
        return token
    
    async def test_corrected_websocket_connection(self) -> Dict[str, Any]:
        """Test WebSocket connection with corrected URL path."""
        logger.info("🔧 Testing Corrected WebSocket Connection")
        
        conversation_id = f"corrected_test_{int(time.time())}"
        user_id = "test_user_corrected"
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
            "error_details": None,
            "url_tested": None
        }
        
        # CORRECTED WebSocket URL with /ws prefix
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        results["url_tested"] = ws_uri[:100] + "..."
        
        logger.info(f"🔌 Connecting to CORRECTED WebSocket URL")
        logger.info(f"📍 URL: /api/v1/ws/chat/{conversation_id}")
        
        try:
            # Attempt WebSocket connection with corrected URL
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                results["authentication_successful"] = True
                logger.info("✅ WebSocket connection and authentication successful!")
                
                # Test message exchange with 12-agent system
                test_messages = [
                    {
                        "type": "chat_message",
                        "data": {
                            "text": "Hello, I need strategic business guidance for my eBay store",
                            "sender": "user"
                        }
                    },
                    {
                        "type": "chat_message", 
                        "data": {
                            "text": "Can you analyze my inventory performance and suggest optimizations?",
                            "sender": "user"
                        }
                    },
                    {
                        "type": "chat_message",
                        "data": {
                            "text": "What's the best pricing strategy for my electronics category?",
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
                        
                        # Check for agent response
                        if "data" in response_data:
                            agent_type = response_data["data"].get("agent_type", "unknown")
                            if agent_type not in results["agent_types"]:
                                results["agent_types"].append(agent_type)
                            
                            if response_data["data"].get("sender") == "agent":
                                results["agent_responses_received"] += 1
                                logger.info(f"✅ Agent response received from {agent_type}")
                                
                                # Log response content for analysis
                                response_text = response_data["data"].get("text", "")
                                logger.info(f"📋 Response preview: {response_text[:100]}...")
                        
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
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            results["error_details"] = str(e)
            
            # Check if it's still a 403 error
            if "403" in str(e):
                logger.error("🔒 Still getting HTTP 403 - investigating further...")
        
        return results
    
    async def verify_12_agent_system(self) -> Dict[str, Any]:
        """Verify the 12-agent system is properly initialized."""
        logger.info("🔍 Verifying 12-Agent System Architecture")
        
        results = {
            "agents_expected": len(self.expected_agents),
            "agents_found": 0,
            "agents_active": 0,
            "agent_details": {},
            "system_healthy": False
        }
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Check agent status endpoint
                async with session.get(f"{self.api_base}/agents/status") as response:
                    if response.status == 200:
                        agent_data = await response.json()
                        
                        # Analyze agent data
                        if "agents" in agent_data:
                            agents = agent_data["agents"]
                            results["agents_found"] = len(agents)
                            
                            for agent_id, agent_info in agents.items():
                                results["agent_details"][agent_id] = {
                                    "type": agent_info.get("type", "unknown"),
                                    "status": agent_info.get("status", "unknown"),
                                    "marketplace": agent_info.get("marketplace", "unknown")
                                }
                                
                                if agent_info.get("status") == "active":
                                    results["agents_active"] += 1
                            
                            logger.info(f"📊 Found {results['agents_found']} agents, {results['agents_active']} active")
                            
                            # Check if we have the expected agents
                            found_agent_ids = set(agents.keys())
                            expected_agent_ids = set(self.expected_agents)
                            
                            missing_agents = expected_agent_ids - found_agent_ids
                            extra_agents = found_agent_ids - expected_agent_ids
                            
                            if missing_agents:
                                logger.warning(f"⚠️ Missing expected agents: {missing_agents}")
                            if extra_agents:
                                logger.info(f"ℹ️ Additional agents found: {extra_agents}")
                            
                            # System is healthy if we have most expected agents active
                            results["system_healthy"] = (
                                results["agents_active"] >= 8 and  # At least 8 of 12 agents
                                len(missing_agents) <= 2  # At most 2 missing agents
                            )
                        
                    else:
                        logger.error(f"❌ Agent status endpoint returned {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error verifying agent system: {e}")
        
        return results
    
    async def run_corrected_tests(self) -> Dict[str, Any]:
        """Run all corrected tests."""
        logger.info("🚀 Starting Corrected WebSocket and 12-Agent System Tests")
        logger.info("=" * 70)
        
        test_results = {
            "agent_system_verification": {},
            "websocket_connection": {},
            "overall_success": False
        }
        
        # Test 1: Verify 12-Agent System
        logger.info("🧪 TEST 1: 12-Agent System Verification")
        test_results["agent_system_verification"] = await self.verify_12_agent_system()
        
        # Test 2: Corrected WebSocket Connection
        logger.info("🧪 TEST 2: Corrected WebSocket Connection")
        test_results["websocket_connection"] = await self.test_corrected_websocket_connection()
        
        # Calculate overall success
        agent_system_ok = test_results["agent_system_verification"]["system_healthy"]
        websocket_ok = test_results["websocket_connection"]["connection_successful"]
        
        test_results["overall_success"] = agent_system_ok and websocket_ok
        
        return test_results

async def main():
    """Main test execution."""
    tester = CorrectedWebSocketTest()
    results = await tester.run_corrected_tests()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 CORRECTED WEBSOCKET AND 12-AGENT SYSTEM RESULTS")
    logger.info("=" * 70)
    
    # Agent System Results
    agent_results = results["agent_system_verification"]
    logger.info("📊 12-AGENT SYSTEM STATUS:")
    logger.info(f"Expected Agents: {agent_results['agents_expected']}")
    logger.info(f"Found Agents: {agent_results['agents_found']}")
    logger.info(f"Active Agents: {agent_results['agents_active']}")
    logger.info(f"System Healthy: {'✅' if agent_results['system_healthy'] else '❌'}")
    
    if agent_results["agent_details"]:
        logger.info("🤖 AGENT DETAILS:")
        for agent_id, details in agent_results["agent_details"].items():
            status_icon = "✅" if details["status"] == "active" else "❌"
            logger.info(f"  {status_icon} {agent_id}: {details['type']} ({details['status']})")
    
    # WebSocket Results
    ws_results = results["websocket_connection"]
    logger.info("📊 WEBSOCKET CONNECTION STATUS:")
    logger.info(f"Connection Successful: {'✅' if ws_results['connection_successful'] else '❌'}")
    logger.info(f"Authentication Successful: {'✅' if ws_results['authentication_successful'] else '❌'}")
    logger.info(f"Messages Sent: {ws_results['messages_sent']}")
    logger.info(f"Agent Responses: {ws_results['agent_responses_received']}")
    logger.info(f"Agent Types Detected: {ws_results['agent_types']}")
    
    if ws_results.get("response_times"):
        avg_response_time = sum(ws_results["response_times"]) / len(ws_results["response_times"])
        logger.info(f"Average Response Time: {avg_response_time:.2f}s")
    
    if ws_results.get("error_details"):
        logger.error(f"Error Details: {ws_results['error_details']}")
    
    logger.info("=" * 70)
    if results["overall_success"]:
        logger.info("🎉 SUCCESS: 12-agent system and WebSocket integration working!")
    else:
        logger.error("💥 ISSUES: Some components need attention")
        
        if not agent_results["system_healthy"]:
            logger.error("❌ 12-agent system not fully healthy")
        if not ws_results["connection_successful"]:
            logger.error("❌ WebSocket connection failed")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
