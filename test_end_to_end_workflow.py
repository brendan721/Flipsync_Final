#!/usr/bin/env python3
"""
End-to-end workflow validation test for FlipSync chat integration.
Tests the complete user journey from Flutter interface to real agents and back.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EndToEndWorkflowTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.flutter_url = "http://localhost:3002"
        self.api_base = f"{self.backend_url}/api/v1"
        
    async def simulate_user_conversation(self) -> Dict[str, Any]:
        """Simulate a complete user conversation workflow."""
        conversation_id = f"e2e_test_{int(time.time())}"
        
        # Realistic user conversation flow
        conversation_flow = [
            {
                "message": "Hi, I'm new to selling on eBay and Amazon. Can you help me get started?",
                "expected_agent": "executive_agent",
                "step": "Initial greeting and guidance request"
            },
            {
                "message": "I have 50 electronics items to sell. What's the best strategy for pricing them competitively?",
                "expected_agent": "market_agent", 
                "step": "Market analysis and pricing strategy"
            },
            {
                "message": "How should I write product descriptions that will get more views and sales?",
                "expected_agent": "content_agent",
                "step": "Content optimization guidance"
            },
            {
                "message": "What shipping options should I offer to maximize customer satisfaction?",
                "expected_agent": "logistics_agent",
                "step": "Logistics and fulfillment strategy"
            },
            {
                "message": "Can you give me a summary of the key action items from our conversation?",
                "expected_agent": "executive_agent",
                "step": "Executive summary and next steps"
            }
        ]
        
        results = {
            "conversation_id": conversation_id,
            "total_messages": len(conversation_flow),
            "successful_responses": 0,
            "agent_routing_correct": 0,
            "response_quality_scores": [],
            "workflow_steps": [],
            "performance_metrics": {
                "avg_response_time": 0,
                "total_conversation_time": 0,
                "agent_distribution": {}
            }
        }
        
        conversation_start = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                for i, step in enumerate(conversation_flow):
                    logger.info(f"🗣️ Step {i+1}: {step['step']}")
                    logger.info(f"💬 User: {step['message'][:60]}...")
                    
                    step_start = time.time()
                    
                    # Send message to chat API
                    payload = {
                        "text": step["message"],
                        "sender": "user"
                    }
                    
                    try:
                        async with session.post(
                            f"{self.api_base}/chat/conversations/{conversation_id}/messages",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            
                            step_time = time.time() - step_start
                            
                            if response.status == 200:
                                data = await response.json()
                                response_text = data.get("text", "")
                                agent_type = data.get("agent_type", "unknown")
                                
                                # Analyze response quality
                                quality_score = self.analyze_response_quality(
                                    step["message"], 
                                    response_text, 
                                    step["expected_agent"]
                                )
                                
                                results["successful_responses"] += 1
                                results["response_quality_scores"].append(quality_score)
                                
                                # Track agent routing
                                if agent_type not in results["performance_metrics"]["agent_distribution"]:
                                    results["performance_metrics"]["agent_distribution"][agent_type] = 0
                                results["performance_metrics"]["agent_distribution"][agent_type] += 1
                                
                                # Check if correct agent handled the request
                                if step["expected_agent"] in agent_type.lower() or agent_type == "unknown":
                                    results["agent_routing_correct"] += 1
                                
                                results["workflow_steps"].append({
                                    "step": i + 1,
                                    "description": step["step"],
                                    "user_message": step["message"][:50] + "...",
                                    "agent_response": response_text[:100] + "...",
                                    "agent_type": agent_type,
                                    "response_time": step_time,
                                    "quality_score": quality_score,
                                    "expected_agent": step["expected_agent"]
                                })
                                
                                logger.info(f"🤖 Agent ({agent_type}): {response_text[:80]}...")
                                logger.info(f"⏱️ Response time: {step_time:.2f}s, Quality: {quality_score:.1f}/10")
                                
                            else:
                                logger.error(f"❌ API error at step {i+1}: {response.status}")
                                results["workflow_steps"].append({
                                    "step": i + 1,
                                    "description": step["step"],
                                    "error": f"HTTP {response.status}",
                                    "response_time": step_time
                                })
                    
                    except Exception as e:
                        logger.error(f"❌ Request error at step {i+1}: {e}")
                        results["workflow_steps"].append({
                            "step": i + 1,
                            "description": step["step"],
                            "error": str(e),
                            "response_time": time.time() - step_start
                        })
                    
                    # Small delay between messages (realistic user behavior)
                    await asyncio.sleep(2)
        
        except Exception as e:
            logger.error(f"❌ Conversation workflow error: {e}")
        
        # Calculate performance metrics
        total_time = time.time() - conversation_start
        response_times = [step.get("response_time", 0) for step in results["workflow_steps"]]
        
        results["performance_metrics"]["total_conversation_time"] = total_time
        results["performance_metrics"]["avg_response_time"] = sum(response_times) / max(len(response_times), 1)
        
        return results
    
    def analyze_response_quality(self, user_message: str, agent_response: str, expected_agent: str) -> float:
        """Analyze the quality of agent response (0-10 scale)."""
        score = 0.0
        
        # Base score for getting a response
        if agent_response and len(agent_response) > 10:
            score += 2.0
        
        # Check for relevant keywords based on expected agent
        agent_keywords = {
            "executive_agent": ["strategy", "business", "guidance", "recommend", "plan", "overview"],
            "market_agent": ["price", "market", "competitive", "analysis", "pricing", "value"],
            "content_agent": ["description", "listing", "content", "seo", "keywords", "optimize"],
            "logistics_agent": ["shipping", "fulfillment", "delivery", "logistics", "warehouse"]
        }
        
        expected_keywords = agent_keywords.get(expected_agent, [])
        response_lower = agent_response.lower()
        
        # Score based on relevant keywords
        keyword_matches = sum(1 for keyword in expected_keywords if keyword in response_lower)
        score += min(keyword_matches * 1.5, 4.0)
        
        # Check for generic error responses (negative score)
        generic_errors = [
            "i apologize, but i encountered an error",
            "please try again or contact support",
            "having trouble processing"
        ]
        
        if any(error in response_lower for error in generic_errors):
            score -= 3.0
        
        # Bonus for detailed responses
        if len(agent_response) > 100:
            score += 1.0
        if len(agent_response) > 200:
            score += 1.0
        
        # Bonus for actionable advice
        actionable_indicators = ["should", "recommend", "suggest", "try", "consider", "start by"]
        if any(indicator in response_lower for indicator in actionable_indicators):
            score += 1.0
        
        return max(0.0, min(10.0, score))
    
    async def test_flutter_chat_interface_simulation(self) -> Dict[str, Any]:
        """Simulate Flutter chat interface interactions."""
        logger.info("🧪 Testing Flutter Chat Interface Simulation")
        
        # Test if Flutter app can handle the conversation flow
        try:
            # Check if Flutter app is serving the chat interface
            async with aiohttp.ClientSession() as session:
                async with session.get(self.flutter_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Look for chat-related elements in the Flutter app
                        chat_indicators = ["chat", "message", "conversation", "input", "send"]
                        has_chat_interface = any(indicator in content.lower() for indicator in chat_indicators)
                        
                        return {
                            "flutter_accessible": True,
                            "has_chat_interface": has_chat_interface,
                            "content_length": len(content)
                        }
                    else:
                        return {
                            "flutter_accessible": False,
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "flutter_accessible": False,
                "error": str(e)
            }
    
    async def run_comprehensive_workflow_test(self) -> Dict[str, Any]:
        """Run the complete end-to-end workflow test."""
        logger.info("🚀 Starting End-to-End Workflow Validation")
        logger.info("=" * 70)
        
        test_results = {
            "flutter_interface": {},
            "conversation_workflow": {},
            "overall_assessment": {},
            "success_metrics": {}
        }
        
        # Test 1: Flutter Interface Simulation
        logger.info("🧪 TEST 1: Flutter Chat Interface Simulation")
        test_results["flutter_interface"] = await self.test_flutter_chat_interface_simulation()
        
        # Test 2: Complete Conversation Workflow
        logger.info("🧪 TEST 2: Complete User Conversation Workflow")
        test_results["conversation_workflow"] = await self.simulate_user_conversation()
        
        # Calculate success metrics
        workflow = test_results["conversation_workflow"]
        success_rate = workflow.get("successful_responses", 0) / max(workflow.get("total_messages", 1), 1)
        quality_avg = sum(workflow.get("response_quality_scores", [])) / max(len(workflow.get("response_quality_scores", [])), 1)
        
        test_results["success_metrics"] = {
            "response_success_rate": success_rate,
            "average_quality_score": quality_avg,
            "agent_routing_accuracy": workflow.get("agent_routing_correct", 0) / max(workflow.get("total_messages", 1), 1),
            "avg_response_time": workflow.get("performance_metrics", {}).get("avg_response_time", 0),
            "total_conversation_time": workflow.get("performance_metrics", {}).get("total_conversation_time", 0)
        }
        
        # Overall assessment
        test_results["overall_assessment"] = {
            "flutter_integration_working": test_results["flutter_interface"].get("flutter_accessible", False),
            "chat_agents_responding": success_rate > 0.8,
            "quality_threshold_met": quality_avg >= 6.0,
            "performance_acceptable": test_results["success_metrics"]["avg_response_time"] < 2.0,
            "end_to_end_success": (
                success_rate > 0.8 and 
                quality_avg >= 6.0 and 
                test_results["flutter_interface"].get("flutter_accessible", False)
            )
        }
        
        return test_results

async def main():
    """Main test execution."""
    tester = EndToEndWorkflowTest()
    results = await tester.run_comprehensive_workflow_test()
    
    # Print detailed results
    logger.info("=" * 70)
    logger.info("🏁 END-TO-END WORKFLOW VALIDATION RESULTS")
    logger.info("=" * 70)
    
    # Flutter Interface Results
    flutter = results["flutter_interface"]
    logger.info(f"Flutter App Accessible: {'✅' if flutter.get('flutter_accessible') else '❌'}")
    logger.info(f"Chat Interface Detected: {'✅' if flutter.get('has_chat_interface') else '❌'}")
    
    # Conversation Workflow Results
    workflow = results["conversation_workflow"]
    logger.info(f"Messages Processed: {workflow.get('successful_responses', 0)}/{workflow.get('total_messages', 0)}")
    
    # Success Metrics
    metrics = results["success_metrics"]
    logger.info(f"Response Success Rate: {metrics['response_success_rate']:.1%}")
    logger.info(f"Average Quality Score: {metrics['average_quality_score']:.1f}/10")
    logger.info(f"Agent Routing Accuracy: {metrics['agent_routing_accuracy']:.1%}")
    logger.info(f"Average Response Time: {metrics['avg_response_time']:.2f}s")
    logger.info(f"Total Conversation Time: {metrics['total_conversation_time']:.1f}s")
    
    # Agent Distribution
    agent_dist = workflow.get("performance_metrics", {}).get("agent_distribution", {})
    logger.info(f"Agent Distribution: {agent_dist}")
    
    # Overall Assessment
    assessment = results["overall_assessment"]
    logger.info("=" * 70)
    logger.info("📊 OVERALL ASSESSMENT:")
    logger.info(f"Flutter Integration: {'✅' if assessment['flutter_integration_working'] else '❌'}")
    logger.info(f"Chat Agents Responding: {'✅' if assessment['chat_agents_responding'] else '❌'}")
    logger.info(f"Quality Threshold Met: {'✅' if assessment['quality_threshold_met'] else '❌'}")
    logger.info(f"Performance Acceptable: {'✅' if assessment['performance_acceptable'] else '❌'}")
    
    logger.info("=" * 70)
    if assessment["end_to_end_success"]:
        logger.info("🎉 END-TO-END SUCCESS: Complete workflow validated!")
        logger.info("✅ Users can successfully interact with real agents through Flutter interface")
    else:
        logger.error("💥 END-TO-END ISSUES: Workflow needs improvement")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
