#!/usr/bin/env python3
"""
Test script to verify Flutter web app can connect to the backend API
and that chat messages are processed by real agents instead of legacy fallbacks.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlutterBackendIntegrationTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.flutter_url = "http://localhost:3002"
        self.api_base = f"{self.backend_url}/api/v1"
        
    async def test_backend_health(self) -> bool:
        """Test if backend is accessible."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Backend health check passed: {data['status']}")
                        return True
                    else:
                        logger.error(f"❌ Backend health check failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Backend connection error: {e}")
            return False
    
    async def test_flutter_web_accessibility(self) -> bool:
        """Test if Flutter web app is accessible."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.flutter_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "flutter" in content.lower() or "flipsync" in content.lower():
                            logger.info("✅ Flutter web app is accessible")
                            return True
                        else:
                            logger.warning("⚠️ Flutter web app accessible but content unclear")
                            return True
                    else:
                        logger.error(f"❌ Flutter web app not accessible: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Flutter web app connection error: {e}")
            return False
    
    async def test_chat_api_with_real_agents(self) -> Dict[str, Any]:
        """Test chat API to verify it connects to real agents."""
        conversation_id = f"test_integration_{int(time.time())}"
        
        test_messages = [
            {
                "text": "Hello, can you help me analyze my inventory performance?",
                "expected_agent": "executive_agent",
                "description": "Executive analysis request"
            },
            {
                "text": "I need help optimizing my product listings for better visibility",
                "expected_agent": "content_agent", 
                "description": "Content optimization request"
            },
            {
                "text": "What's the best shipping strategy for my products?",
                "expected_agent": "logistics_agent",
                "description": "Logistics strategy request"
            }
        ]
        
        results = {
            "conversation_id": conversation_id,
            "messages_tested": 0,
            "real_agent_responses": 0,
            "generic_responses": 0,
            "errors": 0,
            "response_times": [],
            "agent_routing": {},
            "detailed_results": []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                for i, test_msg in enumerate(test_messages):
                    logger.info(f"🧪 Testing message {i+1}: {test_msg['description']}")
                    
                    start_time = time.time()
                    
                    # Send message to chat API
                    payload = {
                        "text": test_msg["text"],
                        "sender": "user"
                    }
                    
                    try:
                        async with session.post(
                            f"{self.api_base}/chat/conversations/{conversation_id}/messages",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            
                            response_time = time.time() - start_time
                            results["response_times"].append(response_time)
                            
                            if response.status == 200:
                                data = await response.json()
                                results["messages_tested"] += 1
                                
                                # Analyze response to determine if it came from real agents
                                response_text = data.get("text", "").lower()
                                
                                # Check for indicators of real agent processing
                                real_agent_indicators = [
                                    "executive", "strategic", "business guidance",
                                    "content optimization", "listing", "seo",
                                    "logistics", "shipping", "fulfillment",
                                    "market analysis", "pricing", "competition"
                                ]
                                
                                generic_error_indicators = [
                                    "i apologize, but i encountered an error",
                                    "please try again or contact support",
                                    "having trouble processing your request",
                                    "generic response", "fallback"
                                ]
                                
                                is_real_agent = any(indicator in response_text for indicator in real_agent_indicators)
                                is_generic_error = any(indicator in response_text for indicator in generic_error_indicators)
                                
                                if is_generic_error:
                                    results["generic_responses"] += 1
                                    logger.warning(f"⚠️ Generic error response detected")
                                elif is_real_agent:
                                    results["real_agent_responses"] += 1
                                    logger.info(f"✅ Real agent response detected")
                                else:
                                    logger.info(f"ℹ️ Response received (unclear if real agent)")
                                
                                # Track agent routing
                                agent_type = data.get("agent_type") or "unknown"
                                if agent_type not in results["agent_routing"]:
                                    results["agent_routing"][agent_type] = 0
                                results["agent_routing"][agent_type] += 1
                                
                                results["detailed_results"].append({
                                    "message": test_msg["text"][:50] + "...",
                                    "response_time": response_time,
                                    "response_length": len(data.get("text", "")),
                                    "agent_type": agent_type,
                                    "is_real_agent": is_real_agent,
                                    "is_generic_error": is_generic_error
                                })
                                
                                logger.info(f"📊 Response time: {response_time:.2f}s, Length: {len(data.get('text', ''))} chars")
                                
                            else:
                                results["errors"] += 1
                                logger.error(f"❌ API error: {response.status}")
                                
                    except Exception as e:
                        results["errors"] += 1
                        logger.error(f"❌ Request error: {e}")
                    
                    # Small delay between requests
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"❌ Chat API test error: {e}")
            results["errors"] += 1
        
        return results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all integration tests."""
        logger.info("🚀 Starting Flutter Backend Integration Tests")
        logger.info("=" * 60)
        
        test_results = {
            "backend_health": False,
            "flutter_accessibility": False,
            "chat_integration": {},
            "overall_success": False,
            "summary": {}
        }
        
        # Test 1: Backend Health
        logger.info("🧪 TEST 1: Backend Health Check")
        test_results["backend_health"] = await self.test_backend_health()
        
        # Test 2: Flutter Web Accessibility
        logger.info("🧪 TEST 2: Flutter Web App Accessibility")
        test_results["flutter_accessibility"] = await self.test_flutter_web_accessibility()
        
        # Test 3: Chat Integration with Real Agents
        logger.info("🧪 TEST 3: Chat Integration with Real Agents")
        test_results["chat_integration"] = await self.test_chat_api_with_real_agents()
        
        # Calculate overall success
        chat_success = (
            test_results["chat_integration"].get("real_agent_responses", 0) > 0 and
            test_results["chat_integration"].get("errors", 0) == 0
        )
        
        test_results["overall_success"] = (
            test_results["backend_health"] and
            test_results["flutter_accessibility"] and
            chat_success
        )
        
        # Generate summary
        chat_data = test_results["chat_integration"]
        test_results["summary"] = {
            "backend_accessible": test_results["backend_health"],
            "flutter_accessible": test_results["flutter_accessibility"],
            "messages_tested": chat_data.get("messages_tested", 0),
            "real_agent_responses": chat_data.get("real_agent_responses", 0),
            "generic_responses": chat_data.get("generic_responses", 0),
            "avg_response_time": sum(chat_data.get("response_times", [])) / max(len(chat_data.get("response_times", [])), 1),
            "agent_routing": chat_data.get("agent_routing", {}),
            "integration_success": test_results["overall_success"]
        }
        
        return test_results

async def main():
    """Main test execution."""
    tester = FlutterBackendIntegrationTest()
    results = await tester.run_comprehensive_test()
    
    # Print results
    logger.info("=" * 60)
    logger.info("🏁 FLUTTER BACKEND INTEGRATION TEST RESULTS")
    logger.info("=" * 60)
    
    summary = results["summary"]
    
    logger.info(f"Backend Accessible: {'✅' if summary['backend_accessible'] else '❌'}")
    logger.info(f"Flutter Accessible: {'✅' if summary['flutter_accessible'] else '❌'}")
    logger.info(f"Messages Tested: {summary['messages_tested']}")
    logger.info(f"Real Agent Responses: {summary['real_agent_responses']}")
    logger.info(f"Generic Responses: {summary['generic_responses']}")
    logger.info(f"Average Response Time: {summary['avg_response_time']:.2f}s")
    logger.info(f"Agent Routing: {summary['agent_routing']}")
    
    logger.info("=" * 60)
    if summary["integration_success"]:
        logger.info("🎉 INTEGRATION SUCCESS: Flutter app connects to real agents!")
    else:
        logger.error("💥 INTEGRATION ISSUES: Chat may be using legacy fallbacks")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
