#!/usr/bin/env python3
"""
WebSocket Recipients Fix Test for FlipSync.
Tests and fixes the "0 recipients" issue in WebSocket message broadcasting.
"""

import asyncio
import websockets
import jwt
import json
import time
import logging
import aiohttp
from typing import Dict, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSocketRecipientsFixTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        
        # JWT configuration
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"
        
    def generate_test_jwt_token(self, user_id: str = "recipients_test_user") -> str:
        """Generate a valid JWT token for testing."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": f"recipients_token_{int(time.time())}",
            "roles": ["user"],
            "permissions": ["chat", "websocket"]
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def test_websocket_recipients_with_maintained_connection(self) -> Dict[str, Any]:
        """Test WebSocket recipients with a maintained connection."""
        logger.info("🔍 Testing WebSocket Recipients with Maintained Connection")
        
        conversation_id = f"recipients_test_{int(time.time())}"
        user_id = "recipients_test_user"
        client_id = f"client_{int(time.time())}"
        
        jwt_token = self.generate_test_jwt_token(user_id)
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        
        results = {
            "connection_successful": False,
            "connection_maintained": False,
            "recipients_before_broadcast": 0,
            "recipients_after_broadcast": 0,
            "broadcast_successful": False,
            "message_received": False,
            "error_details": None
        }
        
        try:
            # Establish and maintain WebSocket connection
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                logger.info("✅ WebSocket connection established")
                
                # Wait for connection to be registered
                await asyncio.sleep(2)
                
                # Check WebSocket stats while connection is active
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.api_base}/ws/stats") as response:
                        if response.status == 200:
                            stats_data = await response.json()
                            active_connections = stats_data.get("active_connections", 0)
                            total_connections = stats_data.get("total_connections", 0)
                            logger.info(f"📊 WebSocket stats: {active_connections} active, {total_connections} total")
                            results["connection_maintained"] = active_connections > 0
                
                # Test broadcasting while connection is active
                if results["connection_maintained"]:
                    async with aiohttp.ClientSession() as session:
                        # Test broadcast endpoint
                        broadcast_url = f"{self.api_base}/ws/conversations/{conversation_id}/broadcast"
                        params = {
                            "message": "Test broadcast message",
                            "message_type": "system_notification"
                        }
                        
                        async with session.post(broadcast_url, params=params) as response:
                            if response.status == 200:
                                broadcast_data = await response.json()
                                recipients = broadcast_data.get("recipients", 0)
                                results["recipients_after_broadcast"] = recipients
                                results["broadcast_successful"] = recipients > 0
                                logger.info(f"📊 Broadcast reached {recipients} recipients")
                                
                                # Check if we receive the broadcast message
                                try:
                                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                    message_data = json.loads(message)
                                    logger.info(f"📥 Received broadcast message: {message_data}")
                                    results["message_received"] = True
                                except asyncio.TimeoutError:
                                    logger.warning("⏰ No broadcast message received within 5 seconds")
                            else:
                                response_text = await response.text()
                                logger.error(f"❌ Broadcast failed: {response.status} - {response_text}")
                
        except Exception as e:
            logger.error(f"❌ WebSocket recipients test error: {e}")
            results["error_details"] = str(e)
        
        return results
    
    async def test_multiple_connections_recipients(self) -> Dict[str, Any]:
        """Test recipients with multiple maintained connections."""
        logger.info("🔍 Testing Recipients with Multiple Maintained Connections")
        
        conversation_id = f"multi_recipients_test_{int(time.time())}"
        user_id = "multi_recipients_user"
        
        results = {
            "connections_established": 0,
            "connections_maintained": 0,
            "total_recipients": 0,
            "messages_received": 0,
            "broadcast_successful": False
        }
        
        connections = []
        
        try:
            # Establish multiple connections and keep them open
            for i in range(2):
                client_id = f"client_{int(time.time())}_{i}"
                jwt_token = self.generate_test_jwt_token(f"{user_id}_{i}")
                ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}_{i}&client_id={client_id}"
                
                try:
                    websocket = await websockets.connect(ws_uri)
                    connections.append(websocket)
                    results["connections_established"] += 1
                    logger.info(f"✅ Connection {i+1} established: {client_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to establish connection {i+1}: {e}")
            
            # Wait for all connections to be registered
            await asyncio.sleep(3)
            
            # Check active connections
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/ws/stats") as response:
                    if response.status == 200:
                        stats_data = await response.json()
                        active_connections = stats_data.get("active_connections", 0)
                        results["connections_maintained"] = active_connections
                        logger.info(f"📊 Active connections maintained: {active_connections}")
            
            # Test broadcasting to multiple connections
            if results["connections_maintained"] > 0:
                async with aiohttp.ClientSession() as session:
                    broadcast_url = f"{self.api_base}/ws/conversations/{conversation_id}/broadcast"
                    params = {
                        "message": "Multi-connection broadcast test",
                        "message_type": "system_notification"
                    }
                    
                    async with session.post(broadcast_url, params=params) as response:
                        if response.status == 200:
                            broadcast_data = await response.json()
                            recipients = broadcast_data.get("recipients", 0)
                            results["total_recipients"] = recipients
                            results["broadcast_successful"] = recipients > 0
                            logger.info(f"📊 Broadcast reached {recipients} recipients")
                            
                            # Check if all connections receive the message
                            for i, websocket in enumerate(connections):
                                try:
                                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                    message_data = json.loads(message)
                                    results["messages_received"] += 1
                                    logger.info(f"📥 Connection {i+1} received: {message_data.get('type', 'unknown')}")
                                except asyncio.TimeoutError:
                                    logger.warning(f"⏰ Connection {i+1} did not receive message")
                        else:
                            response_text = await response.text()
                            logger.error(f"❌ Multi-connection broadcast failed: {response.status} - {response_text}")
            
        except Exception as e:
            logger.error(f"❌ Error in multiple connections recipients test: {e}")
        
        finally:
            # Clean up connections
            for websocket in connections:
                try:
                    await websocket.close()
                except:
                    pass
        
        return results
    
    async def run_recipients_fix_tests(self) -> Dict[str, Any]:
        """Run comprehensive WebSocket recipients fix tests."""
        logger.info("🚀 Starting WebSocket Recipients Fix Tests")
        logger.info("=" * 70)
        
        test_results = {
            "single_connection_test": {},
            "multiple_connections_test": {},
            "recipients_fix_working": False
        }
        
        # Test 1: Single Connection Recipients
        logger.info("🧪 TEST 1: Single Connection Recipients")
        test_results["single_connection_test"] = await self.test_websocket_recipients_with_maintained_connection()
        
        # Test 2: Multiple Connections Recipients
        logger.info("🧪 TEST 2: Multiple Connections Recipients")
        test_results["multiple_connections_test"] = await self.test_multiple_connections_recipients()
        
        # Analyze results
        single_test = test_results["single_connection_test"]
        multi_test = test_results["multiple_connections_test"]
        
        test_results["recipients_fix_working"] = (
            single_test.get("broadcast_successful", False) and
            single_test.get("message_received", False) and
            multi_test.get("broadcast_successful", False) and
            multi_test.get("messages_received", 0) > 0
        )
        
        return test_results

async def main():
    """Main test execution."""
    tester = WebSocketRecipientsFixTest()
    results = await tester.run_recipients_fix_tests()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 WEBSOCKET RECIPIENTS FIX TEST RESULTS")
    logger.info("=" * 70)
    
    # Single Connection Results
    single_results = results["single_connection_test"]
    logger.info("📊 SINGLE CONNECTION TEST:")
    logger.info(f"Connection Successful: {'✅' if single_results.get('connection_successful') else '❌'}")
    logger.info(f"Connection Maintained: {'✅' if single_results.get('connection_maintained') else '❌'}")
    logger.info(f"Recipients Found: {single_results.get('recipients_after_broadcast', 0)}")
    logger.info(f"Broadcast Successful: {'✅' if single_results.get('broadcast_successful') else '❌'}")
    logger.info(f"Message Received: {'✅' if single_results.get('message_received') else '❌'}")
    
    # Multiple Connections Results
    multi_results = results["multiple_connections_test"]
    logger.info("📊 MULTIPLE CONNECTIONS TEST:")
    logger.info(f"Connections Established: {multi_results.get('connections_established', 0)}")
    logger.info(f"Connections Maintained: {multi_results.get('connections_maintained', 0)}")
    logger.info(f"Total Recipients: {multi_results.get('total_recipients', 0)}")
    logger.info(f"Messages Received: {multi_results.get('messages_received', 0)}")
    logger.info(f"Broadcast Successful: {'✅' if multi_results.get('broadcast_successful') else '❌'}")
    
    # Overall Assessment
    logger.info("=" * 70)
    logger.info("📈 OVERALL ASSESSMENT:")
    logger.info(f"Recipients Fix Working: {'✅' if results['recipients_fix_working'] else '❌'}")
    
    if results["recipients_fix_working"]:
        logger.info("🎉 SUCCESS: WebSocket recipients tracking and broadcasting working!")
    else:
        logger.error("💥 ISSUES: WebSocket recipients tracking needs attention")
        
        if not single_results.get("connection_maintained"):
            logger.error("❌ WebSocket connections not being maintained")
        if not single_results.get("broadcast_successful"):
            logger.error("❌ Broadcasting not reaching recipients")
        if not single_results.get("message_received"):
            logger.error("❌ Messages not being received by WebSocket clients")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
