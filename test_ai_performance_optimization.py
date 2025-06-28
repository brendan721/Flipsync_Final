#!/usr/bin/env python3
"""
AI Performance Optimization Test for FlipSync.
Tests AI response times after optimization to ensure <10 second responses.
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

class AIPerformanceOptimizationTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        
        # JWT configuration
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"
        
        # Performance targets
        self.target_response_time = 10.0  # seconds
        self.acceptable_response_time = 15.0  # seconds
        
    def generate_test_jwt_token(self, user_id: str = "ai_perf_test_user") -> str:
        """Generate a valid JWT token for testing."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": f"ai_perf_token_{int(time.time())}",
            "roles": ["user"],
            "permissions": ["chat", "websocket"]
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def test_ai_response_time_single(self) -> Dict[str, Any]:
        """Test AI response time for a single message."""
        logger.info("🔍 Testing AI Response Time - Single Message")
        
        conversation_id = f"ai_perf_test_{int(time.time())}"
        user_id = "ai_perf_test_user"
        client_id = f"client_{int(time.time())}"
        
        jwt_token = self.generate_test_jwt_token(user_id)
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        
        results = {
            "connection_successful": False,
            "message_sent": False,
            "response_received": False,
            "response_time": 0.0,
            "response_content": "",
            "meets_target": False,
            "meets_acceptable": False,
            "error_details": None
        }
        
        try:
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                logger.info("✅ WebSocket connection established")
                
                # Wait for connection to be established
                await asyncio.sleep(1)
                
                # Send test message and measure response time
                test_message = {
                    "type": "message",
                    "conversation_id": conversation_id,
                    "data": {
                        "content": "What are the best pricing strategies for eBay sellers?",
                        "user_id": user_id
                    }
                }
                
                start_time = time.time()
                await websocket.send(json.dumps(test_message))
                results["message_sent"] = True
                logger.info("📤 Test message sent")
                
                # Wait for AI response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    end_time = time.time()
                    
                    response_data = json.loads(response)
                    results["response_received"] = True
                    results["response_time"] = end_time - start_time
                    results["response_content"] = response_data.get("data", {}).get("content", "")[:100] + "..."
                    
                    # Check performance targets
                    results["meets_target"] = results["response_time"] <= self.target_response_time
                    results["meets_acceptable"] = results["response_time"] <= self.acceptable_response_time
                    
                    logger.info(f"📥 AI response received in {results['response_time']:.2f}s")
                    
                except asyncio.TimeoutError:
                    results["response_time"] = 30.0
                    logger.warning("⏰ AI response timeout after 30 seconds")
                
        except Exception as e:
            logger.error(f"❌ AI performance test error: {e}")
            results["error_details"] = str(e)
        
        return results
    
    async def test_ai_response_time_multiple(self) -> Dict[str, Any]:
        """Test AI response times for multiple messages."""
        logger.info("🔍 Testing AI Response Time - Multiple Messages")
        
        conversation_id = f"ai_multi_perf_test_{int(time.time())}"
        user_id = "ai_multi_perf_test_user"
        client_id = f"client_{int(time.time())}"
        
        jwt_token = self.generate_test_jwt_token(user_id)
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"
        
        test_messages = [
            "How do I optimize my eBay listings?",
            "What are the best selling categories on eBay?",
            "How can I improve my seller rating?"
        ]
        
        results = {
            "connection_successful": False,
            "messages_sent": 0,
            "responses_received": 0,
            "response_times": [],
            "average_response_time": 0.0,
            "fastest_response": 0.0,
            "slowest_response": 0.0,
            "meets_target_count": 0,
            "meets_acceptable_count": 0,
            "error_details": None
        }
        
        try:
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                logger.info("✅ WebSocket connection established for multiple tests")
                
                # Wait for connection to be established
                await asyncio.sleep(1)
                
                for i, message_content in enumerate(test_messages):
                    test_message = {
                        "type": "message",
                        "conversation_id": conversation_id,
                        "data": {
                            "content": message_content,
                            "user_id": user_id
                        }
                    }
                    
                    start_time = time.time()
                    await websocket.send(json.dumps(test_message))
                    results["messages_sent"] += 1
                    logger.info(f"📤 Test message {i+1} sent: {message_content[:50]}...")
                    
                    # Wait for AI response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        end_time = time.time()
                        
                        response_time = end_time - start_time
                        results["response_times"].append(response_time)
                        results["responses_received"] += 1
                        
                        if response_time <= self.target_response_time:
                            results["meets_target_count"] += 1
                        if response_time <= self.acceptable_response_time:
                            results["meets_acceptable_count"] += 1
                        
                        logger.info(f"📥 Response {i+1} received in {response_time:.2f}s")
                        
                        # Small delay between messages
                        await asyncio.sleep(2)
                        
                    except asyncio.TimeoutError:
                        results["response_times"].append(30.0)
                        logger.warning(f"⏰ Response {i+1} timeout after 30 seconds")
                
                # Calculate statistics
                if results["response_times"]:
                    results["average_response_time"] = sum(results["response_times"]) / len(results["response_times"])
                    results["fastest_response"] = min(results["response_times"])
                    results["slowest_response"] = max(results["response_times"])
                
        except Exception as e:
            logger.error(f"❌ AI multiple performance test error: {e}")
            results["error_details"] = str(e)
        
        return results
    
    async def run_ai_performance_tests(self) -> Dict[str, Any]:
        """Run comprehensive AI performance optimization tests."""
        logger.info("🚀 Starting AI Performance Optimization Tests")
        logger.info("=" * 70)
        
        test_results = {
            "single_message_test": {},
            "multiple_messages_test": {},
            "performance_optimized": False,
            "target_performance_achieved": False
        }
        
        # Test 1: Single Message Performance
        logger.info("🧪 TEST 1: Single Message AI Performance")
        test_results["single_message_test"] = await self.test_ai_response_time_single()
        
        # Test 2: Multiple Messages Performance
        logger.info("🧪 TEST 2: Multiple Messages AI Performance")
        test_results["multiple_messages_test"] = await self.test_ai_response_time_multiple()
        
        # Analyze results
        single_test = test_results["single_message_test"]
        multi_test = test_results["multiple_messages_test"]
        
        # Check if performance targets are met
        single_meets_target = single_test.get("meets_target", False)
        multi_avg_meets_target = multi_test.get("average_response_time", 30.0) <= self.target_response_time
        
        test_results["target_performance_achieved"] = single_meets_target and multi_avg_meets_target
        
        # Check if acceptable performance is achieved
        single_meets_acceptable = single_test.get("meets_acceptable", False)
        multi_avg_meets_acceptable = multi_test.get("average_response_time", 30.0) <= self.acceptable_response_time
        
        test_results["performance_optimized"] = single_meets_acceptable and multi_avg_meets_acceptable
        
        return test_results

async def main():
    """Main test execution."""
    tester = AIPerformanceOptimizationTest()
    
    # Wait for services to be ready
    logger.info("⏳ Waiting for services to be ready...")
    await asyncio.sleep(10)
    
    results = await tester.run_ai_performance_tests()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 AI PERFORMANCE OPTIMIZATION TEST RESULTS")
    logger.info("=" * 70)
    
    # Single Message Results
    single_results = results["single_message_test"]
    logger.info("📊 SINGLE MESSAGE TEST:")
    logger.info(f"Connection Successful: {'✅' if single_results.get('connection_successful') else '❌'}")
    logger.info(f"Response Received: {'✅' if single_results.get('response_received') else '❌'}")
    logger.info(f"Response Time: {single_results.get('response_time', 0):.2f}s")
    logger.info(f"Meets Target (<10s): {'✅' if single_results.get('meets_target') else '❌'}")
    logger.info(f"Meets Acceptable (<15s): {'✅' if single_results.get('meets_acceptable') else '❌'}")
    
    # Multiple Messages Results
    multi_results = results["multiple_messages_test"]
    logger.info("📊 MULTIPLE MESSAGES TEST:")
    logger.info(f"Messages Sent: {multi_results.get('messages_sent', 0)}")
    logger.info(f"Responses Received: {multi_results.get('responses_received', 0)}")
    logger.info(f"Average Response Time: {multi_results.get('average_response_time', 0):.2f}s")
    logger.info(f"Fastest Response: {multi_results.get('fastest_response', 0):.2f}s")
    logger.info(f"Slowest Response: {multi_results.get('slowest_response', 0):.2f}s")
    logger.info(f"Target Performance Count: {multi_results.get('meets_target_count', 0)}/3")
    
    # Overall Assessment
    logger.info("=" * 70)
    logger.info("📈 OVERALL ASSESSMENT:")
    logger.info(f"Target Performance Achieved (<10s): {'✅' if results['target_performance_achieved'] else '❌'}")
    logger.info(f"Performance Optimized (<15s): {'✅' if results['performance_optimized'] else '❌'}")
    
    if results["target_performance_achieved"]:
        logger.info("🎉 SUCCESS: AI performance optimization achieved target goals!")
    elif results["performance_optimized"]:
        logger.info("✅ GOOD: AI performance optimization achieved acceptable goals!")
    else:
        logger.error("💥 ISSUES: AI performance optimization needs more work")
        logger.error("💡 Recommendations:")
        logger.error("   - Further reduce max_tokens in AI configurations")
        logger.error("   - Optimize Ollama container resource allocation")
        logger.error("   - Consider implementing response caching")
        logger.error("   - Enable streaming for real-time user feedback")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
