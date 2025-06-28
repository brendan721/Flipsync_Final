#!/usr/bin/env python3
"""
Comprehensive Frontend-Backend Flow Test for FlipSync.
Tests the complete message flow: Flutter → WebSocket → Agent System → AI Model → Response → WebSocket → Flutter
"""

import asyncio
import websockets
import jwt
import json
import time
import logging
import aiohttp
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveFrontendBackendTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        
        # JWT configuration (matching Flutter app)
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"
        
    def generate_test_jwt_token(self, user_id: str = "frontend_test_user") -> str:
        """Generate a valid JWT token matching Flutter app format."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": f"frontend_token_{int(time.time())}",
            "roles": ["user"],
            "permissions": ["chat", "websocket"]
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def test_complete_message_flow(self) -> Dict[str, Any]:
        """Test the complete message flow from frontend to backend and back."""
        logger.info("🚀 Testing Complete Frontend-Backend Message Flow")
        
        # Use 'main' conversation ID like Flutter app
        conversation_id = "main"
        user_id = "frontend_test_user"
        client_id = f"client_{int(time.time())}"
        
        jwt_token = self.generate_test_jwt_token(user_id)
        
        # Build WebSocket URL exactly like Flutter app
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        
        results = {
            "connection_successful": False,
            "authentication_successful": False,
            "message_sent": False,
            "backend_processing_started": False,
            "ai_processing_attempted": False,
            "ai_response_received": False,
            "websocket_response_received": False,
            "total_time": 0.0,
            "ai_processing_time": 0.0,
            "error_details": None,
            "backend_logs": []
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Establish WebSocket connection
            logger.info("🔌 Step 1: Establishing WebSocket connection...")
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                logger.info("✅ WebSocket connection established")
                
                # Step 2: Wait for authentication confirmation
                logger.info("🔑 Step 2: Waiting for authentication confirmation...")
                try:
                    auth_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    auth_data = json.loads(auth_response)
                    
                    if auth_data.get("type") == "connection_established":
                        results["authentication_successful"] = True
                        logger.info("✅ Authentication successful")
                        logger.info(f"📋 Auth response: {auth_data}")
                    
                except asyncio.TimeoutError:
                    logger.warning("⏰ No authentication response received")
                
                # Step 3: Send test message (exactly like Flutter app)
                logger.info("📤 Step 3: Sending test message...")
                test_message = {
                    "type": "message",
                    "conversation_id": conversation_id,
                    "data": {
                        "id": f"msg_{int(time.time())}",
                        "content": "What are the best pricing strategies for eBay sellers?",
                        "sender": "user",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                message_start_time = time.time()
                await websocket.send(json.dumps(test_message))
                results["message_sent"] = True
                logger.info("✅ Message sent via WebSocket")
                
                # Step 4: Monitor backend processing and AI response
                logger.info("🔍 Step 4: Monitoring backend processing...")
                
                # Wait for response with extended timeout for AI processing
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    message_end_time = time.time()
                    
                    response_data = json.loads(response)
                    results["websocket_response_received"] = True
                    results["ai_processing_time"] = message_end_time - message_start_time
                    
                    logger.info(f"📥 Response received in {results['ai_processing_time']:.2f}s")
                    logger.info(f"📋 Response data: {response_data}")
                    
                    # Check if this is an actual AI response or error
                    if response_data.get("type") == "message":
                        response_content = response_data.get("data", {}).get("content", "")
                        if "error" not in response_content.lower() and len(response_content) > 50:
                            results["ai_response_received"] = True
                            logger.info("✅ AI response received successfully")
                        else:
                            logger.warning(f"⚠️ Received error or short response: {response_content[:100]}")
                    
                except asyncio.TimeoutError:
                    logger.error("⏰ No response received within 60 seconds")
                    results["error_details"] = "Response timeout after 60 seconds"
                
        except Exception as e:
            logger.error(f"❌ Test error: {e}")
            results["error_details"] = str(e)
        
        results["total_time"] = time.time() - start_time
        
        # Step 5: Check backend logs for processing details
        await self._check_backend_processing_logs(results)
        
        return results
    
    async def _check_backend_processing_logs(self, results: Dict[str, Any]):
        """Check backend logs to understand processing flow."""
        try:
            # Get recent Docker logs
            import subprocess
            log_result = subprocess.run(
                ["docker", "logs", "flipsync-api", "--tail=50"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if log_result.returncode == 0:
                logs = log_result.stdout
                results["backend_logs"] = logs.split('\n')[-20:]  # Last 20 lines
                
                # Analyze logs for processing stages
                if "WebSocket connection attempt" in logs:
                    results["backend_processing_started"] = True
                
                if "Starting Ollama generation" in logs or "POST request to http://host.docker.internal:11434" in logs:
                    results["ai_processing_attempted"] = True
                
                # Check for specific error patterns
                if "TimeoutError" in logs:
                    if not results["error_details"]:
                        results["error_details"] = "AI model timeout detected in backend logs"
                
                if "Executive Agent processing failed" in logs:
                    if not results["error_details"]:
                        results["error_details"] = "Executive Agent processing failed (fallback removed)"
                
        except Exception as e:
            logger.warning(f"Could not check backend logs: {e}")
    
    async def test_websocket_connection_persistence(self) -> Dict[str, Any]:
        """Test that WebSocket connections are maintained during AI processing."""
        logger.info("🔍 Testing WebSocket Connection Persistence")
        
        conversation_id = "persistence_test"
        user_id = "persistence_test_user"
        client_id = f"client_{int(time.time())}"
        
        jwt_token = self.generate_test_jwt_token(user_id)
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        
        results = {
            "connection_maintained": False,
            "multiple_messages_supported": False,
            "connection_stats_updated": False,
            "recipients_tracked": False
        }
        
        try:
            async with websockets.connect(ws_uri) as websocket:
                # Wait for connection to be registered
                await asyncio.sleep(2)
                
                # Check connection stats
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.api_base}/ws/stats") as response:
                        if response.status == 200:
                            stats = await response.json()
                            active_connections = stats.get("active_connections", 0)
                            results["connection_maintained"] = active_connections > 0
                            results["connection_stats_updated"] = True
                            logger.info(f"📊 Active connections: {active_connections}")
                
                # Test broadcasting to verify recipient tracking
                if results["connection_maintained"]:
                    async with aiohttp.ClientSession() as session:
                        broadcast_url = f"{self.api_base}/ws/conversations/{conversation_id}/broadcast"
                        params = {
                            "message": "Connection persistence test",
                            "message_type": "system_notification"
                        }
                        
                        async with session.post(broadcast_url, params=params) as response:
                            if response.status == 200:
                                broadcast_data = await response.json()
                                recipients = broadcast_data.get("recipients", 0)
                                results["recipients_tracked"] = recipients > 0
                                logger.info(f"📊 Broadcast recipients: {recipients}")
                
                # Test multiple message support
                for i in range(2):
                    test_message = {
                        "type": "message",
                        "conversation_id": conversation_id,
                        "data": {
                            "id": f"persistence_msg_{i}_{int(time.time())}",
                            "content": f"Persistence test message {i+1}",
                            "sender": "user",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    await asyncio.sleep(1)  # Small delay between messages
                
                results["multiple_messages_supported"] = True
                
        except Exception as e:
            logger.error(f"❌ Persistence test error: {e}")
        
        return results
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive frontend-backend tests."""
        logger.info("🚀 Starting Comprehensive Frontend-Backend Tests")
        logger.info("=" * 70)
        
        test_results = {
            "complete_flow_test": {},
            "persistence_test": {},
            "overall_success": False,
            "critical_issues": [],
            "recommendations": []
        }
        
        # Test 1: Complete Message Flow
        logger.info("🧪 TEST 1: Complete Message Flow")
        test_results["complete_flow_test"] = await self.test_complete_message_flow()
        
        # Test 2: WebSocket Connection Persistence
        logger.info("🧪 TEST 2: WebSocket Connection Persistence")
        test_results["persistence_test"] = await self.test_websocket_connection_persistence()
        
        # Analyze results
        flow_test = test_results["complete_flow_test"]
        persistence_test = test_results["persistence_test"]
        
        # Determine overall success
        critical_success = (
            flow_test.get("connection_successful", False) and
            flow_test.get("authentication_successful", False) and
            flow_test.get("message_sent", False) and
            persistence_test.get("connection_maintained", False)
        )
        
        test_results["overall_success"] = critical_success
        
        # Identify critical issues
        if not flow_test.get("ai_response_received", False):
            test_results["critical_issues"].append("AI responses not being received")
        
        if flow_test.get("ai_processing_time", 0) > 30:
            test_results["critical_issues"].append("AI processing time exceeds acceptable limits")
        
        if not persistence_test.get("recipients_tracked", False):
            test_results["critical_issues"].append("WebSocket recipient tracking not working")
        
        # Generate recommendations
        if "TimeoutError" in str(flow_test.get("error_details", "")):
            test_results["recommendations"].append("Increase AI model timeout or optimize model performance")
        
        if not flow_test.get("ai_response_received", False):
            test_results["recommendations"].append("Implement proper error handling for AI failures")
        
        if flow_test.get("ai_processing_time", 0) > 15:
            test_results["recommendations"].append("Consider implementing response streaming for better UX")
        
        return test_results

async def main():
    """Main test execution."""
    tester = ComprehensiveFrontendBackendTest()
    
    # Wait for services to be ready
    logger.info("⏳ Waiting for services to be ready...")
    await asyncio.sleep(5)
    
    results = await tester.run_comprehensive_tests()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 COMPREHENSIVE FRONTEND-BACKEND TEST RESULTS")
    logger.info("=" * 70)
    
    # Complete Flow Results
    flow_results = results["complete_flow_test"]
    logger.info("📊 COMPLETE MESSAGE FLOW TEST:")
    logger.info(f"Connection Successful: {'✅' if flow_results.get('connection_successful') else '❌'}")
    logger.info(f"Authentication Successful: {'✅' if flow_results.get('authentication_successful') else '❌'}")
    logger.info(f"Message Sent: {'✅' if flow_results.get('message_sent') else '❌'}")
    logger.info(f"Backend Processing Started: {'✅' if flow_results.get('backend_processing_started') else '❌'}")
    logger.info(f"AI Processing Attempted: {'✅' if flow_results.get('ai_processing_attempted') else '❌'}")
    logger.info(f"AI Response Received: {'✅' if flow_results.get('ai_response_received') else '❌'}")
    logger.info(f"WebSocket Response Received: {'✅' if flow_results.get('websocket_response_received') else '❌'}")
    logger.info(f"Total Time: {flow_results.get('total_time', 0):.2f}s")
    logger.info(f"AI Processing Time: {flow_results.get('ai_processing_time', 0):.2f}s")
    
    # Persistence Results
    persistence_results = results["persistence_test"]
    logger.info("📊 CONNECTION PERSISTENCE TEST:")
    logger.info(f"Connection Maintained: {'✅' if persistence_results.get('connection_maintained') else '❌'}")
    logger.info(f"Multiple Messages Supported: {'✅' if persistence_results.get('multiple_messages_supported') else '❌'}")
    logger.info(f"Recipients Tracked: {'✅' if persistence_results.get('recipients_tracked') else '❌'}")
    
    # Overall Assessment
    logger.info("=" * 70)
    logger.info("📈 OVERALL ASSESSMENT:")
    logger.info(f"Overall Success: {'✅' if results['overall_success'] else '❌'}")
    
    if results["critical_issues"]:
        logger.error("💥 CRITICAL ISSUES:")
        for issue in results["critical_issues"]:
            logger.error(f"   - {issue}")
    
    if results["recommendations"]:
        logger.info("💡 RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            logger.info(f"   - {rec}")
    
    # Error details
    if flow_results.get("error_details"):
        logger.error(f"❌ Error Details: {flow_results['error_details']}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
