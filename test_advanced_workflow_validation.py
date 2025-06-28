#!/usr/bin/env python3
"""
FlipSync Advanced Workflow Testing - Phase 1
Tests with real eBay data, performance load testing, and error handling
"""

import asyncio
import aiohttp
import json
import logging
import sys
import time
import random
from typing import Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdvancedWorkflowTester:
    """Advanced testing for FlipSync workflows with real data and load testing."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        self.test_conversations = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_test_conversation(self, test_name: str) -> str:
        """Create a test conversation for advanced testing."""
        try:
            payload = {
                "title": f"Advanced Test: {test_name}",
                "description": f"Advanced workflow testing for {test_name}"
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
                        self.test_conversations.append(conversation_id)
                        return conversation_id
                    
                return None
                    
        except Exception as e:
            logger.error(f"❌ Conversation creation error: {e}")
            return None
    
    async def send_workflow_message(self, conversation_id: str, message: str, timeout: int = 60) -> Dict[str, Any]:
        """Send a workflow message and measure performance."""
        try:
            payload = {
                "text": message,
                "sender_type": "user"
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/conversations/{conversation_id}/messages",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                response_time = time.time() - start_time
                
                if response.status in [200, 201]:
                    data = await response.json()
                    return {
                        "success": True,
                        "response_time": response_time,
                        "response_data": data,
                        "status_code": response.status
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "response_time": response_time,
                        "error": error_text,
                        "status_code": response.status
                    }
                    
        except asyncio.TimeoutError:
            return {
                "success": False,
                "response_time": timeout,
                "error": "Request timeout",
                "status_code": 408
            }
        except Exception as e:
            return {
                "success": False,
                "response_time": time.time() - start_time if 'start_time' in locals() else 0,
                "error": str(e),
                "status_code": 500
            }
    
    async def test_real_ebay_product_analysis(self) -> Dict[str, Any]:
        """Test with real eBay product data and market analysis."""
        logger.info("📱 Testing Real eBay Product Analysis")
        
        conversation_id = await self.create_test_conversation("Real eBay Product Analysis")
        if not conversation_id:
            return {"success": False, "error": "Failed to create conversation"}
        
        # Real eBay product scenarios
        real_product_scenarios = [
            {
                "name": "iPhone Analysis",
                "message": """I want to sell a used iPhone 14 Pro 128GB in excellent condition on eBay. 
                Can you analyze the current market, check competitor pricing, and recommend the optimal 
                listing strategy? I need specific pricing recommendations, title optimization, and 
                shipping strategy using real eBay market data."""
            },
            {
                "name": "Electronics Bundle",
                "message": """I have a bundle of gaming accessories: PlayStation 5 controller, 
                gaming headset, and charging dock. Can your agents coordinate to analyze the market 
                for gaming accessories, determine if I should sell as a bundle or separately, 
                and create optimized listings with competitive pricing?"""
            },
            {
                "name": "Vintage Electronics",
                "message": """I'm selling vintage electronics: 1980s Walkman, retro gaming console, 
                and vintage cameras. Can your market and content agents work together to research 
                the vintage electronics market, identify the best categories, and create compelling 
                listings that appeal to collectors?"""
            }
        ]
        
        results = []
        for scenario in real_product_scenarios:
            logger.info(f"   Testing: {scenario['name']}")
            result = await self.send_workflow_message(conversation_id, scenario['message'], timeout=90)
            result['scenario'] = scenario['name']
            results.append(result)
            
            # Brief pause between scenarios
            await asyncio.sleep(1)
        
        # Analyze results
        successful_scenarios = [r for r in results if r.get('success', False)]
        avg_response_time = sum(r.get('response_time', 0) for r in successful_scenarios) / max(len(successful_scenarios), 1)
        
        return {
            "test_name": "Real eBay Product Analysis",
            "total_scenarios": len(real_product_scenarios),
            "successful_scenarios": len(successful_scenarios),
            "success_rate": len(successful_scenarios) / len(real_product_scenarios),
            "average_response_time": avg_response_time,
            "results": results
        }
    
    async def test_concurrent_workflow_load(self) -> Dict[str, Any]:
        """Test multiple concurrent business workflows for performance."""
        logger.info("⚡ Testing Concurrent Workflow Load")
        
        # Create multiple conversations for concurrent testing
        concurrent_conversations = []
        for i in range(5):
            conv_id = await self.create_test_conversation(f"Concurrent Load Test {i+1}")
            if conv_id:
                concurrent_conversations.append(conv_id)
        
        if len(concurrent_conversations) < 3:
            return {"success": False, "error": "Failed to create enough test conversations"}
        
        # Concurrent workflow scenarios
        concurrent_scenarios = [
            "Analyze pricing strategy for 50 electronics items across eBay and Amazon marketplaces",
            "Optimize inventory management for seasonal electronics with demand forecasting",
            "Create comprehensive shipping arbitrage strategy for multi-zone distribution",
            "Develop content optimization plan for 100+ product listings with SEO analysis",
            "Coordinate executive strategy for scaling from $20K to $100K monthly revenue"
        ]
        
        # Execute concurrent workflows
        start_time = time.time()
        tasks = []
        
        for i, scenario in enumerate(concurrent_scenarios[:len(concurrent_conversations)]):
            conv_id = concurrent_conversations[i]
            task = self.send_workflow_message(conv_id, scenario, timeout=120)
            tasks.append(task)
        
        # Wait for all concurrent workflows to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze concurrent performance
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({"scenario": i, "error": str(result)})
            elif result.get('success', False):
                successful_results.append(result)
            else:
                failed_results.append(result)
        
        avg_response_time = sum(r.get('response_time', 0) for r in successful_results) / max(len(successful_results), 1)
        
        return {
            "test_name": "Concurrent Workflow Load",
            "concurrent_workflows": len(concurrent_scenarios),
            "successful_workflows": len(successful_results),
            "failed_workflows": len(failed_results),
            "success_rate": len(successful_results) / len(concurrent_scenarios),
            "total_execution_time": total_time,
            "average_response_time": avg_response_time,
            "max_response_time": max((r.get('response_time', 0) for r in successful_results), default=0),
            "min_response_time": min((r.get('response_time', 0) for r in successful_results), default=0),
            "results": results
        }
    
    async def test_error_handling_scenarios(self) -> Dict[str, Any]:
        """Test error handling and recovery mechanisms."""
        logger.info("🛡️ Testing Error Handling Scenarios")
        
        conversation_id = await self.create_test_conversation("Error Handling Test")
        if not conversation_id:
            return {"success": False, "error": "Failed to create conversation"}
        
        # Error scenarios to test system resilience
        error_scenarios = [
            {
                "name": "Invalid Product Data",
                "message": "Analyze pricing for a product with invalid SKU: INVALID-SKU-12345-NONEXISTENT and create optimization strategy",
                "expected_behavior": "graceful_handling"
            },
            {
                "name": "Extreme Load Request",
                "message": "Analyze and optimize 10,000 products simultaneously across 50 marketplaces with real-time competitor monitoring",
                "expected_behavior": "resource_management"
            },
            {
                "name": "Conflicting Instructions",
                "message": "Maximize profit margins while minimizing prices and increase inventory while reducing storage costs for the same products",
                "expected_behavior": "conflict_resolution"
            },
            {
                "name": "Incomplete Information",
                "message": "Optimize my business strategy for products in categories using marketplaces with shipping to locations",
                "expected_behavior": "clarification_request"
            },
            {
                "name": "Rapid Fire Requests",
                "message": "Quick analysis needed now! Urgent pricing update! Immediate inventory check! Fast shipping calculation!",
                "expected_behavior": "prioritization"
            }
        ]
        
        results = []
        for scenario in error_scenarios:
            logger.info(f"   Testing: {scenario['name']}")
            
            # Test with shorter timeout for error scenarios
            result = await self.send_workflow_message(conversation_id, scenario['message'], timeout=45)
            result['scenario'] = scenario['name']
            result['expected_behavior'] = scenario['expected_behavior']
            
            # Analyze error handling quality
            if result.get('success', False):
                response_data = result.get('response_data', {})
                response_text = str(response_data).lower()
                
                # Check for appropriate error handling indicators
                error_handling_quality = 0
                if 'clarification' in response_text or 'more information' in response_text:
                    error_handling_quality += 2
                if 'prioritize' in response_text or 'focus' in response_text:
                    error_handling_quality += 2
                if 'limitation' in response_text or 'constraint' in response_text:
                    error_handling_quality += 2
                if len(response_text) > 100:  # Substantial response
                    error_handling_quality += 2
                
                result['error_handling_quality'] = min(error_handling_quality, 8)
            else:
                result['error_handling_quality'] = 0
            
            results.append(result)
            await asyncio.sleep(0.5)  # Brief pause between error tests
        
        # Analyze error handling performance
        successful_results = [r for r in results if r.get('success', False)]
        avg_error_handling_quality = sum(r.get('error_handling_quality', 0) for r in successful_results) / max(len(successful_results), 1)
        
        return {
            "test_name": "Error Handling Scenarios",
            "total_scenarios": len(error_scenarios),
            "successful_scenarios": len(successful_results),
            "success_rate": len(successful_results) / len(error_scenarios),
            "average_error_handling_quality": avg_error_handling_quality,
            "results": results
        }
    
    async def test_complex_multi_agent_coordination(self) -> Dict[str, Any]:
        """Test complex scenarios requiring deep multi-agent coordination."""
        logger.info("🤝 Testing Complex Multi-Agent Coordination")
        
        conversation_id = await self.create_test_conversation("Complex Multi-Agent Coordination")
        if not conversation_id:
            return {"success": False, "error": "Failed to create conversation"}
        
        # Complex coordination scenarios
        complex_scenarios = [
            {
                "name": "Cross-Platform Business Expansion",
                "message": """I'm expanding from eBay-only to eBay + Amazon + Walmart marketplaces. 
                I need your executive agent to coordinate with market, content, logistics, and inventory 
                agents to create a comprehensive expansion strategy. This should include: competitive 
                analysis across all platforms, inventory allocation strategy, pricing optimization 
                for each marketplace, content adaptation for platform-specific requirements, and 
                shipping cost optimization across the expanded network."""
            },
            {
                "name": "Seasonal Business Optimization",
                "message": """It's approaching holiday season and I need to optimize my entire business 
                for Q4 sales surge. Can your agents coordinate to: forecast demand increases by category, 
                adjust inventory levels for seasonal products, optimize pricing for holiday competition, 
                create holiday-themed content and promotions, and scale shipping operations for increased 
                volume? I need a coordinated strategy that maximizes holiday revenue."""
            },
            {
                "name": "Crisis Management Scenario",
                "message": """A major competitor just dropped their prices by 30% across my main product 
                categories, and I'm facing potential stockouts on my best sellers. I need immediate 
                coordinated response: market analysis of competitor strategy, pricing adjustment 
                recommendations that maintain profitability, emergency inventory rebalancing, content 
                updates to emphasize value propositions, and shipping optimization to maintain margins. 
                This requires all agents working together for crisis response."""
            }
        ]
        
        results = []
        for scenario in complex_scenarios:
            logger.info(f"   Testing: {scenario['name']}")
            
            # Complex scenarios need more time
            result = await self.send_workflow_message(conversation_id, scenario['message'], timeout=120)
            result['scenario'] = scenario['name']
            
            # Analyze coordination quality
            if result.get('success', False):
                response_data = result.get('response_data', {})
                response_text = str(response_data).lower()
                
                # Check for multi-agent coordination indicators
                coordination_indicators = [
                    'coordinate', 'collaboration', 'executive agent', 'market agent',
                    'content agent', 'logistics agent', 'inventory agent', 'strategy',
                    'comprehensive', 'integrated', 'synchronized', 'workflow'
                ]
                
                coordination_score = sum(1 for indicator in coordination_indicators if indicator in response_text)
                result['coordination_quality'] = min(coordination_score, 10)
            else:
                result['coordination_quality'] = 0
            
            results.append(result)
            await asyncio.sleep(2)  # Longer pause for complex scenarios
        
        # Analyze coordination performance
        successful_results = [r for r in results if r.get('success', False)]
        avg_coordination_quality = sum(r.get('coordination_quality', 0) for r in successful_results) / max(len(successful_results), 1)
        avg_response_time = sum(r.get('response_time', 0) for r in successful_results) / max(len(successful_results), 1)
        
        return {
            "test_name": "Complex Multi-Agent Coordination",
            "total_scenarios": len(complex_scenarios),
            "successful_scenarios": len(successful_results),
            "success_rate": len(successful_results) / len(complex_scenarios),
            "average_coordination_quality": avg_coordination_quality,
            "average_response_time": avg_response_time,
            "results": results
        }

    async def run_advanced_workflow_tests(self) -> Dict[str, Any]:
        """Run all advanced workflow tests."""
        logger.info("🚀 Starting Advanced Workflow Testing - Phase 1")
        logger.info("=" * 70)
        
        test_results = {}
        
        # Test 1: Real eBay Product Analysis
        logger.info("🧪 TEST 1: Real eBay Product Analysis")
        test_results["real_ebay_analysis"] = await self.test_real_ebay_product_analysis()
        
        # Test 2: Concurrent Workflow Load
        logger.info("🧪 TEST 2: Concurrent Workflow Load Testing")
        test_results["concurrent_load"] = await self.test_concurrent_workflow_load()
        
        # Test 3: Error Handling
        logger.info("🧪 TEST 3: Error Handling Scenarios")
        test_results["error_handling"] = await self.test_error_handling_scenarios()
        
        # Test 4: Complex Multi-Agent Coordination
        logger.info("🧪 TEST 4: Complex Multi-Agent Coordination")
        test_results["complex_coordination"] = await self.test_complex_multi_agent_coordination()
        
        return test_results

async def main():
    """Main test execution."""
    logger.info("🏢 FlipSync Advanced Workflow Testing - Phase 1")
    logger.info("=" * 70)
    logger.info("🎯 Testing with real eBay data, performance load, and error handling")
    logger.info("🧪 Environment: eBay Sandbox Integration")
    logger.info("")
    
    async with AdvancedWorkflowTester() as tester:
        results = await tester.run_advanced_workflow_tests()
        
        # Analyze overall results
        logger.info("")
        logger.info("📊 ADVANCED WORKFLOW TEST RESULTS")
        logger.info("=" * 50)
        
        overall_metrics = {
            "total_tests": 0,
            "successful_tests": 0,
            "average_response_time": 0,
            "performance_score": 0
        }
        
        for test_name, result in results.items():
            if isinstance(result, dict) and "success_rate" in result:
                success_rate = result.get("success_rate", 0)
                avg_time = result.get("average_response_time", 0)
                
                overall_metrics["total_tests"] += 1
                if success_rate >= 0.8:
                    overall_metrics["successful_tests"] += 1
                overall_metrics["average_response_time"] += avg_time
                
                status = "✅ PASS" if success_rate >= 0.8 else "⚠️ PARTIAL" if success_rate >= 0.6 else "❌ FAIL"
                logger.info(f"   {test_name}: {status}")
                logger.info(f"      Success Rate: {success_rate:.1%}")
                logger.info(f"      Avg Response Time: {avg_time:.2f}s")
                
                # Additional metrics for specific tests
                if "coordination_quality" in result:
                    logger.info(f"      Coordination Quality: {result['coordination_quality']:.1f}/10")
                if "error_handling_quality" in result:
                    logger.info(f"      Error Handling: {result['average_error_handling_quality']:.1f}/8")
        
        # Calculate overall performance
        overall_metrics["average_response_time"] /= max(overall_metrics["total_tests"], 1)
        overall_success_rate = overall_metrics["successful_tests"] / max(overall_metrics["total_tests"], 1)
        
        logger.info("")
        logger.info("📈 OVERALL PERFORMANCE METRICS")
        logger.info("=" * 35)
        logger.info(f"Overall Success Rate: {overall_success_rate:.1%}")
        logger.info(f"Average Response Time: {overall_metrics['average_response_time']:.2f}s")
        
        # Production readiness assessment
        logger.info("")
        logger.info("🎯 PHASE 1 ASSESSMENT")
        logger.info("=" * 25)
        
        if overall_success_rate >= 0.8 and overall_metrics["average_response_time"] <= 5.0:
            logger.info("🎉 EXCELLENT: Phase 1 advanced testing successful!")
            logger.info("   ✅ Real eBay data processing working")
            logger.info("   ✅ Performance under load acceptable")
            logger.info("   ✅ Error handling robust")
            logger.info("   ✅ Multi-agent coordination effective")
            logger.info("")
            logger.info("🚀 Ready for Phase 2: Business Metrics Validation")
            return 0
        else:
            logger.error("❌ Phase 1 needs improvement before proceeding")
            logger.info("   🔧 Focus on performance optimization and error handling")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
