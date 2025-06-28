#!/usr/bin/env python3
"""
FlipSync Business Workflow Coordination Testing
Tests real e-commerce business processes and multi-agent coordination
"""

import asyncio
import aiohttp
import json
import logging
import sys
import time
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BusinessWorkflowTester:
    """Test FlipSync's core business workflows and agent coordination."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        self.conversation_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def setup_test_conversation(self) -> str:
        """Create a test conversation for business workflow testing."""
        try:
            payload = {
                "title": "Business Workflow Testing",
                "description": "Testing multi-agent coordination for e-commerce workflows"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/conversations",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status in [200, 201]:
                    data = await response.json()
                    conversation_id = data.get('conversation_id') or data.get('id')
                    if conversation_id:
                        self.conversation_id = conversation_id
                        logger.info(f"✅ Test conversation created: {conversation_id}")
                        return conversation_id
                    
                logger.error("❌ Failed to get conversation ID from response")
                return None
                    
        except Exception as e:
            logger.error(f"❌ Conversation setup error: {e}")
            return None
    
    async def send_business_message(self, message: str, expected_workflow: str) -> Dict[str, Any]:
        """Send a business-focused message and analyze the response."""
        try:
            payload = {
                "text": message,
                "sender_type": "user"
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/conversations/{self.conversation_id}/messages",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                
                response_time = time.time() - start_time
                
                if response.status in [200, 201]:
                    data = await response.json()
                    
                    # Analyze response for business workflow indicators
                    analysis = self.analyze_business_response(data, expected_workflow, response_time)
                    
                    logger.info(f"✅ Message sent: {message[:50]}...")
                    logger.info(f"   Response time: {response_time:.2f}s")
                    logger.info(f"   Workflow detected: {analysis.get('workflow_detected', 'Unknown')}")
                    
                    return analysis
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Message failed: {response.status} - {error_text}")
                    return {"success": False, "error": error_text}
                    
        except Exception as e:
            logger.error(f"❌ Message sending error: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_business_response(self, response_data: Dict, expected_workflow: str, response_time: float) -> Dict[str, Any]:
        """Analyze response for business workflow indicators."""
        
        # Extract response content
        response_text = ""
        if "message" in response_data:
            response_text = str(response_data["message"])
        elif "response" in response_data:
            response_text = str(response_data["response"])
        elif "content" in response_data:
            response_text = str(response_data["content"])
        else:
            response_text = str(response_data)
        
        response_lower = response_text.lower()
        
        # Business workflow indicators
        workflow_indicators = {
            "pricing_optimization": [
                "pricing", "competitor", "market analysis", "profit margin", 
                "price strategy", "competitive pricing", "pricing recommendation"
            ],
            "listing_optimization": [
                "listing", "seo", "title optimization", "description", "keywords",
                "visibility", "search ranking", "content optimization"
            ],
            "inventory_management": [
                "inventory", "stock", "reorder", "demand forecasting", "stockout",
                "inventory levels", "supply chain", "warehouse"
            ],
            "shipping_arbitrage": [
                "shipping", "carrier", "shipping cost", "delivery", "logistics",
                "shipping optimization", "arbitrage", "shipping savings"
            ],
            "market_analysis": [
                "market trends", "competitor analysis", "market research", "demand",
                "market intelligence", "trend analysis", "market data"
            ],
            "multi_agent_coordination": [
                "coordinate", "agents", "executive", "market agent", "content agent",
                "logistics agent", "workflow", "collaboration"
            ]
        }
        
        # Detect workflows
        detected_workflows = []
        for workflow, keywords in workflow_indicators.items():
            if any(keyword in response_lower for keyword in keywords):
                detected_workflows.append(workflow)
        
        # Business value indicators
        business_value_indicators = [
            "profit", "revenue", "savings", "optimization", "efficiency",
            "roi", "cost reduction", "performance improvement", "automation"
        ]
        
        business_value_detected = any(indicator in response_lower for indicator in business_value_indicators)
        
        # Agent coordination indicators
        agent_indicators = [
            "executive agent", "market agent", "content agent", "logistics agent",
            "inventory agent", "coordination", "workflow", "analysis"
        ]
        
        agent_coordination_detected = any(indicator in response_lower for indicator in agent_indicators)
        
        return {
            "success": True,
            "response_time": response_time,
            "response_length": len(response_text),
            "expected_workflow": expected_workflow,
            "detected_workflows": detected_workflows,
            "workflow_detected": expected_workflow in detected_workflows,
            "business_value_detected": business_value_detected,
            "agent_coordination_detected": agent_coordination_detected,
            "response_quality_score": self.calculate_response_quality(
                response_text, detected_workflows, business_value_detected, agent_coordination_detected
            ),
            "raw_response": response_text[:200] + "..." if len(response_text) > 200 else response_text
        }
    
    def calculate_response_quality(self, response_text: str, workflows: List[str], 
                                 business_value: bool, agent_coordination: bool) -> float:
        """Calculate response quality score (0-10)."""
        score = 0.0
        
        # Base score for having a response
        if len(response_text) > 50:
            score += 2.0
        
        # Workflow detection bonus
        score += min(len(workflows) * 1.5, 4.0)
        
        # Business value bonus
        if business_value:
            score += 2.0
        
        # Agent coordination bonus
        if agent_coordination:
            score += 2.0
        
        return min(score, 10.0)
    
    async def test_pricing_optimization_workflow(self) -> Dict[str, Any]:
        """Test pricing optimization business workflow."""
        logger.info("💰 Testing Pricing Optimization Workflow")
        
        message = """I have 25 electronics items (smartphones, tablets, headphones) that I want to sell on eBay. 
        I need help with competitive pricing strategy. Can you analyze the market and recommend optimal pricing 
        that maximizes profit while staying competitive? Please coordinate between your market analysis and 
        executive decision-making agents."""
        
        return await self.send_business_message(message, "pricing_optimization")
    
    async def test_listing_optimization_workflow(self) -> Dict[str, Any]:
        """Test listing optimization business workflow."""
        logger.info("📝 Testing Listing Optimization Workflow")
        
        message = """I need to optimize my eBay listings for better visibility and sales conversion. 
        I'm selling consumer electronics and want to improve my SEO, titles, and descriptions. 
        Can your content and market agents work together to create optimized listings that will 
        rank higher in search results and convert better?"""
        
        return await self.send_business_message(message, "listing_optimization")
    
    async def test_inventory_management_workflow(self) -> Dict[str, Any]:
        """Test inventory management business workflow."""
        logger.info("📦 Testing Inventory Management Workflow")
        
        message = """I'm managing inventory across eBay and Amazon for 100+ products. I need help with 
        demand forecasting, reorder optimization, and preventing stockouts. Can your inventory and 
        logistics agents coordinate to create an automated inventory management strategy that 
        optimizes stock levels and reduces carrying costs?"""
        
        return await self.send_business_message(message, "inventory_management")
    
    async def test_shipping_arbitrage_workflow(self) -> Dict[str, Any]:
        """Test shipping arbitrage business workflow."""
        logger.info("🚚 Testing Shipping Arbitrage Workflow")
        
        message = """I want to optimize my shipping costs and delivery times for my eBay business. 
        I ship about 50 packages per week across different zones. Can your logistics agents analyze 
        carrier options and implement shipping arbitrage to reduce my costs while maintaining 
        good delivery times? I want to understand the potential savings."""
        
        return await self.send_business_message(message, "shipping_arbitrage")
    
    async def test_comprehensive_business_strategy(self) -> Dict[str, Any]:
        """Test comprehensive business strategy coordination."""
        logger.info("🎯 Testing Comprehensive Business Strategy Coordination")
        
        message = """I'm scaling my eBay business from $10K to $50K monthly revenue. I need a comprehensive 
        strategy that coordinates pricing optimization, inventory management, listing optimization, and 
        shipping cost reduction. Can your executive agent coordinate with all specialist agents to create 
        a complete business growth plan with specific KPIs and implementation steps?"""
        
        return await self.send_business_message(message, "multi_agent_coordination")

    async def run_business_workflow_tests(self) -> Dict[str, Any]:
        """Run comprehensive business workflow tests."""
        logger.info("🚀 Starting FlipSync Business Workflow Coordination Tests")
        logger.info("=" * 70)
        
        # Setup test conversation
        conversation_id = await self.setup_test_conversation()
        if not conversation_id:
            return {"error": "Failed to setup test conversation"}
        
        # Run business workflow tests
        test_results = {}
        
        # Test 1: Pricing Optimization
        test_results["pricing_optimization"] = await self.test_pricing_optimization_workflow()
        await asyncio.sleep(2)  # Brief pause between tests
        
        # Test 2: Listing Optimization  
        test_results["listing_optimization"] = await self.test_listing_optimization_workflow()
        await asyncio.sleep(2)
        
        # Test 3: Inventory Management
        test_results["inventory_management"] = await self.test_inventory_management_workflow()
        await asyncio.sleep(2)
        
        # Test 4: Shipping Arbitrage
        test_results["shipping_arbitrage"] = await self.test_shipping_arbitrage_workflow()
        await asyncio.sleep(2)
        
        # Test 5: Comprehensive Strategy
        test_results["comprehensive_strategy"] = await self.test_comprehensive_business_strategy()
        
        return test_results

async def main():
    """Main test execution."""
    logger.info("🏢 FlipSync Business Workflow Coordination Testing")
    logger.info("=" * 70)
    logger.info("🎯 Testing real e-commerce business processes and agent coordination")
    logger.info("🧪 Environment: eBay Sandbox Integration")
    logger.info("")
    
    async with BusinessWorkflowTester() as tester:
        results = await tester.run_business_workflow_tests()
        
        if "error" in results:
            logger.error(f"❌ Test setup failed: {results['error']}")
            return 1
        
        # Analyze results
        logger.info("")
        logger.info("📊 BUSINESS WORKFLOW TEST RESULTS")
        logger.info("=" * 50)
        
        total_tests = len(results)
        successful_tests = 0
        total_quality_score = 0
        total_response_time = 0
        
        for workflow_name, result in results.items():
            if result.get("success", False):
                successful_tests += 1
                quality_score = result.get("response_quality_score", 0)
                response_time = result.get("response_time", 0)
                workflow_detected = result.get("workflow_detected", False)
                business_value = result.get("business_value_detected", False)
                agent_coordination = result.get("agent_coordination_detected", False)
                
                total_quality_score += quality_score
                total_response_time += response_time
                
                status = "✅ PASS" if workflow_detected and quality_score >= 6.0 else "⚠️ PARTIAL"
                logger.info(f"   {workflow_name}: {status}")
                logger.info(f"      Quality Score: {quality_score:.1f}/10")
                logger.info(f"      Response Time: {response_time:.2f}s")
                logger.info(f"      Workflow Detected: {'✅' if workflow_detected else '❌'}")
                logger.info(f"      Business Value: {'✅' if business_value else '❌'}")
                logger.info(f"      Agent Coordination: {'✅' if agent_coordination else '❌'}")
            else:
                logger.info(f"   {workflow_name}: ❌ FAIL")
                logger.info(f"      Error: {result.get('error', 'Unknown error')}")
        
        # Summary metrics
        avg_quality = total_quality_score / max(successful_tests, 1)
        avg_response_time = total_response_time / max(successful_tests, 1)
        success_rate = successful_tests / total_tests
        
        logger.info("")
        logger.info("📈 SUMMARY METRICS")
        logger.info("=" * 30)
        logger.info(f"Success Rate: {success_rate:.1%} ({successful_tests}/{total_tests})")
        logger.info(f"Average Quality Score: {avg_quality:.1f}/10")
        logger.info(f"Average Response Time: {avg_response_time:.2f}s")
        
        # Production readiness assessment
        logger.info("")
        logger.info("🎯 PRODUCTION READINESS ASSESSMENT")
        logger.info("=" * 40)
        
        if success_rate >= 0.8 and avg_quality >= 7.0 and avg_response_time <= 10.0:
            logger.info("🎉 EXCELLENT: FlipSync business workflows are production-ready!")
            logger.info("   ✅ High success rate and quality scores")
            logger.info("   ✅ Agents are coordinating effectively")
            logger.info("   ✅ Business value is being delivered")
            return 0
        elif success_rate >= 0.6 and avg_quality >= 5.0:
            logger.info("⚠️ GOOD: FlipSync workflows are functional with room for improvement")
            logger.info("   ✅ Core functionality working")
            logger.info("   ⚠️ Some optimization needed")
            return 0
        else:
            logger.error("❌ NEEDS WORK: Business workflows need improvement")
            logger.info("   🔧 Focus on agent coordination and response quality")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
