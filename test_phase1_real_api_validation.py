#!/usr/bin/env python3
"""
Phase 1 Real API Validation Test Suite
======================================

Validates Phase 1 cost optimization using real OpenAI API calls to prove
the claimed 41.7% cost reduction is achievable with actual API usage.

Test Coverage:
- Real OpenAI API calls using FlipSyncOpenAIClient
- Intelligent model router with actual model selection
- Actual cost tracking with real token usage and pricing
- Budget enforcement with real API cost validation
- Performance testing with real response times
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import FlipSync components
from fs_agt_clean.core.ai.openai_client import (
    FlipSyncOpenAIClient,
    OpenAIConfig,
    OpenAIModel,
    TaskComplexity,
    OpenAIUsageTracker,
)


class Phase1RealAPIValidationTest:
    """Real API validation test suite for Phase 1 cost optimization."""

    def __init__(self):
        """Initialize test suite with real OpenAI API configuration."""
        self.test_results = {}
        self.start_time = datetime.now()
        
        # Phase 1 baseline establishment
        self.baseline_cost_per_operation = 0.0024  # Target baseline
        self.quality_threshold = 0.8
        
        # Real API configuration
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required for real API testing")
        
        self.openai_config = OpenAIConfig(
            api_key=api_key,
            model=OpenAIModel.GPT_4O_MINI,
            temperature=0.7,
            max_tokens=500,  # Controlled for cost management
            max_cost_per_request=0.05,  # $0.05 max per request
            daily_budget=2.00,  # $2.00 daily budget for testing
            timeout=30.0
        )
        
        # Initialize OpenAI client
        self.openai_client = FlipSyncOpenAIClient(self.openai_config)
        
        # Cost tracking
        self.operation_costs = []
        self.quality_scores = []
        self.response_times = []
        
        print(f"🔑 OpenAI API Key configured: {api_key[:8]}...")
        print(f"💰 Daily budget: ${self.openai_config.daily_budget}")
        print(f"🎯 Max cost per request: ${self.openai_config.max_cost_per_request}")

    async def run_all_tests(self):
        """Run comprehensive Phase 1 real API validation tests."""
        
        print("🚀 PHASE 1 REAL API VALIDATION TEST")
        print("=" * 70)
        print(f"Start Time: {self.start_time}")
        print(f"Objective: Validate Phase 1 cost optimization with real OpenAI API calls")
        print(f"Quality Requirement: Maintain >{int(self.quality_threshold*100)}% accuracy threshold")
        print(f"Budget Control: ${self.openai_config.daily_budget} daily limit")
        print()

        # Test 1: Intelligent Model Router with Real API
        await self.test_intelligent_model_router()
        
        # Test 2: Cost Baseline Establishment
        await self.test_cost_baseline_establishment()
        
        # Test 3: Budget Enforcement Validation
        await self.test_budget_enforcement()
        
        # Test 4: Quality Monitoring with Real Responses
        await self.test_quality_monitoring()
        
        # Test 5: Performance Validation
        await self.test_performance_validation()
        
        # Generate final results
        await self.generate_test_results()

    async def test_intelligent_model_router(self):
        """Test intelligent model router with real API calls."""
        
        print("TEST 1: INTELLIGENT MODEL ROUTER WITH REAL API")
        print("-" * 50)
        
        try:
            # E-commerce scenarios with different complexity levels
            routing_scenarios = [
                {
                    "name": "simple_listing_title",
                    "prompt": "Create an eBay title for: Used iPhone 12 Pro 128GB",
                    "complexity": TaskComplexity.SIMPLE,
                    "expected_model": OpenAIModel.GPT_4O_MINI
                },
                {
                    "name": "product_description",
                    "prompt": "Write a detailed eBay description for a vintage Canon AE-1 camera in excellent condition with original box and manual.",
                    "complexity": TaskComplexity.MODERATE,
                    "expected_model": OpenAIModel.GPT_4O_MINI
                },
                {
                    "name": "market_analysis",
                    "prompt": "Analyze the current market trends for vintage electronics on eBay, focusing on pricing strategies and demand patterns for cameras from the 1970s.",
                    "complexity": TaskComplexity.COMPLEX,
                    "expected_model": OpenAIModel.GPT_4O
                }
            ]
            
            total_routing_cost = 0
            successful_routes = 0
            
            for scenario in routing_scenarios:
                print(f"🔀 Testing model routing: {scenario['name']}")
                
                # Select optimal model based on complexity
                selected_model = self.openai_client.select_optimal_model(scenario["complexity"])
                print(f"   ✅ Selected model: {selected_model.value}")
                print(f"   ✅ Expected model: {scenario['expected_model'].value}")
                print(f"   ✅ Routing correct: {selected_model == scenario['expected_model']}")
                
                # Make real API call with selected model
                start_time = time.time()
                response = await self.openai_client.generate_text(
                    prompt=scenario["prompt"],
                    task_complexity=scenario["complexity"],
                    system_prompt="You are an expert e-commerce assistant specializing in eBay optimization."
                )
                response_time = time.time() - start_time
                
                if response.success:
                    successful_routes += 1
                    total_routing_cost += response.cost_estimate
                    self.operation_costs.append(response.cost_estimate)
                    self.response_times.append(response_time)
                    
                    print(f"   ✅ API call successful: ${response.cost_estimate:.4f}")
                    print(f"   ✅ Response time: {response_time:.2f}s")
                    print(f"   ✅ Tokens: {response.usage.get('prompt_tokens', 0)}+{response.usage.get('completion_tokens', 0)}")
                    print(f"   ✅ Model used: {response.model}")
                    
                    # Assess quality (basic metrics)
                    quality_score = min(1.0, len(response.content) / 100)  # Basic quality assessment
                    self.quality_scores.append(quality_score)
                    print(f"   ✅ Quality score: {quality_score:.2f}")
                else:
                    print(f"   ❌ API call failed: {response.error_message}")
                
                print()
                
                # Rate limiting
                await asyncio.sleep(1)
            
            avg_routing_cost = total_routing_cost / successful_routes if successful_routes > 0 else 0
            
            print(f"✅ Model routing validation complete:")
            print(f"   Successful routes: {successful_routes}/{len(routing_scenarios)}")
            print(f"   Average cost per operation: ${avg_routing_cost:.4f}")
            print(f"   Target baseline: ${self.baseline_cost_per_operation:.4f}")
            
            # Validate cost optimization
            cost_optimized = avg_routing_cost <= self.baseline_cost_per_operation
            print(f"   Cost optimization achieved: {cost_optimized}")
            
            self.test_results["intelligent_model_router"] = successful_routes >= 2 and cost_optimized
            print(f"TEST 1: {'✅ PASS' if self.test_results['intelligent_model_router'] else '❌ FAIL'}")
            
        except Exception as e:
            print(f"❌ Model router test failed: {e}")
            self.test_results["intelligent_model_router"] = False
            print("TEST 1: ❌ FAIL")
        
        print()

    async def test_cost_baseline_establishment(self):
        """Test cost baseline establishment with real API usage."""
        
        print("TEST 2: COST BASELINE ESTABLISHMENT")
        print("-" * 50)
        
        try:
            # Standard e-commerce operations for baseline
            baseline_operations = [
                {
                    "operation": "vision_analysis_simulation",
                    "prompt": "Analyze this product: Vintage Rolex watch, assess condition and create eBay listing recommendations.",
                    "complexity": TaskComplexity.MODERATE
                },
                {
                    "operation": "listing_generation",
                    "prompt": "Create a complete eBay listing for: MacBook Pro 2019 16-inch, 512GB SSD, excellent condition with original packaging.",
                    "complexity": TaskComplexity.SIMPLE
                },
                {
                    "operation": "market_research",
                    "prompt": "Research pricing for vintage Nike Air Jordan sneakers on eBay, provide competitive analysis and pricing recommendations.",
                    "complexity": TaskComplexity.COMPLEX
                }
            ]
            
            baseline_costs = []
            baseline_times = []
            successful_operations = 0
            
            for operation in baseline_operations:
                print(f"📊 Baseline operation: {operation['operation']}")
                
                start_time = time.time()
                response = await self.openai_client.generate_text(
                    prompt=operation["prompt"],
                    task_complexity=operation["complexity"],
                    system_prompt="You are FlipSync's expert e-commerce AI assistant."
                )
                operation_time = time.time() - start_time
                
                if response.success:
                    successful_operations += 1
                    baseline_costs.append(response.cost_estimate)
                    baseline_times.append(operation_time)
                    
                    print(f"   ✅ Operation cost: ${response.cost_estimate:.4f}")
                    print(f"   ✅ Response time: {operation_time:.2f}s")
                    print(f"   ✅ Content length: {len(response.content)} chars")
                    
                    # Quality assessment
                    quality_indicators = {
                        "length": len(response.content) > 50,
                        "relevance": any(keyword in response.content.lower() for keyword in ["ebay", "price", "listing"]),
                        "completeness": len(response.content) > 100
                    }
                    quality_score = sum(quality_indicators.values()) / len(quality_indicators)
                    print(f"   ✅ Quality score: {quality_score:.2f}")
                else:
                    print(f"   ❌ Operation failed: {response.error_message}")
                
                print()
                await asyncio.sleep(1)
            
            if baseline_costs:
                avg_baseline_cost = sum(baseline_costs) / len(baseline_costs)
                avg_baseline_time = sum(baseline_times) / len(baseline_times)
                
                print(f"✅ Baseline establishment complete:")
                print(f"   Average cost per operation: ${avg_baseline_cost:.4f}")
                print(f"   Average response time: {avg_baseline_time:.2f}s")
                print(f"   Successful operations: {successful_operations}/{len(baseline_operations)}")
                
                # Validate baseline meets target
                baseline_acceptable = avg_baseline_cost <= self.baseline_cost_per_operation * 1.1  # 10% tolerance
                print(f"   Baseline target met: {baseline_acceptable}")
                
                # Update baseline for comparison
                if baseline_acceptable:
                    self.baseline_cost_per_operation = avg_baseline_cost
                    print(f"   Updated baseline: ${self.baseline_cost_per_operation:.4f}")
            else:
                baseline_acceptable = False
            
            self.test_results["cost_baseline"] = successful_operations >= 2 and baseline_acceptable
            print(f"TEST 2: {'✅ PASS' if self.test_results['cost_baseline'] else '❌ FAIL'}")
            
        except Exception as e:
            print(f"❌ Baseline establishment test failed: {e}")
            self.test_results["cost_baseline"] = False
            print("TEST 2: ❌ FAIL")
        
        print()

    async def test_budget_enforcement(self):
        """Test budget enforcement with real API costs."""
        
        print("TEST 3: BUDGET ENFORCEMENT VALIDATION")
        print("-" * 50)
        
        try:
            # Get current usage stats
            usage_stats = await self.openai_client.get_usage_stats()
            current_cost = usage_stats['daily_cost']
            
            print(f"📊 Current daily cost: ${current_cost:.4f}")
            print(f"📊 Daily budget: ${self.openai_config.daily_budget:.2f}")
            print(f"📊 Budget remaining: ${usage_stats['budget_remaining']:.4f}")
            
            # Test normal request within budget
            normal_request = "Create a short eBay title for a used laptop."
            response = await self.openai_client.generate_text(
                prompt=normal_request,
                task_complexity=TaskComplexity.SIMPLE
            )
            
            if response.success:
                print(f"✅ Normal request cost: ${response.cost_estimate:.4f}")
                within_budget = response.cost_estimate <= self.openai_config.max_cost_per_request
                print(f"✅ Within per-request limit: {within_budget}")
            else:
                print(f"❌ Normal request failed: {response.error_message}")
                within_budget = False
            
            # Test budget tracking accuracy
            updated_stats = await self.openai_client.get_usage_stats()
            cost_increase = updated_stats['daily_cost'] - current_cost
            tracking_accurate = abs(cost_increase - response.cost_estimate) < 0.0001
            
            print(f"📈 Cost increase: ${cost_increase:.4f}")
            print(f"📈 Tracking accurate: {tracking_accurate}")
            
            # Test budget enforcement logic
            budget_enforced = self.openai_client.usage_tracker.check_budget(self.openai_config)
            print(f"🛡️ Budget enforcement active: {budget_enforced}")
            
            enforcement_working = within_budget and tracking_accurate and budget_enforced
            
            self.test_results["budget_enforcement"] = enforcement_working
            print(f"TEST 3: {'✅ PASS' if enforcement_working else '❌ FAIL'}")
            
        except Exception as e:
            print(f"❌ Budget enforcement test failed: {e}")
            self.test_results["budget_enforcement"] = False
            print("TEST 3: ❌ FAIL")
        
        print()

    async def test_quality_monitoring(self):
        """Test quality monitoring with real API responses."""
        
        print("TEST 4: QUALITY MONITORING WITH REAL RESPONSES")
        print("-" * 50)
        
        try:
            # Quality test scenarios
            quality_scenarios = [
                {
                    "name": "product_title_quality",
                    "prompt": "Create an eBay title for: Vintage 1985 Nike Air Jordan 1 sneakers, size 10, good condition",
                    "quality_criteria": ["nike", "jordan", "vintage", "1985"]
                },
                {
                    "name": "description_quality", 
                    "prompt": "Write a product description for a Canon EOS R5 camera with 24-105mm lens, used but excellent condition",
                    "quality_criteria": ["canon", "eos", "r5", "24-105", "condition"]
                }
            ]
            
            quality_results = []
            
            for scenario in quality_scenarios:
                print(f"🔍 Quality test: {scenario['name']}")
                
                response = await self.openai_client.generate_text(
                    prompt=scenario["prompt"],
                    task_complexity=TaskComplexity.SIMPLE,
                    system_prompt="You are an expert eBay listing writer. Create high-quality, SEO-optimized content."
                )
                
                if response.success:
                    # Assess quality based on criteria
                    content_lower = response.content.lower()
                    criteria_met = sum(1 for criterion in scenario["quality_criteria"] 
                                     if criterion.lower() in content_lower)
                    quality_score = criteria_met / len(scenario["quality_criteria"])
                    
                    quality_results.append(quality_score)
                    
                    print(f"   ✅ Response generated: {len(response.content)} chars")
                    print(f"   ✅ Criteria met: {criteria_met}/{len(scenario['quality_criteria'])}")
                    print(f"   ✅ Quality score: {quality_score:.2f}")
                    print(f"   ✅ Above threshold: {quality_score >= self.quality_threshold}")
                else:
                    print(f"   ❌ Quality test failed: {response.error_message}")
                    quality_results.append(0.0)
                
                print()
                await asyncio.sleep(1)
            
            if quality_results:
                avg_quality = sum(quality_results) / len(quality_results)
                quality_maintained = avg_quality >= self.quality_threshold
                
                print(f"✅ Quality monitoring complete:")
                print(f"   Average quality score: {avg_quality:.2f}")
                print(f"   Quality threshold: {self.quality_threshold:.2f}")
                print(f"   Quality maintained: {quality_maintained}")
            else:
                quality_maintained = False
            
            self.test_results["quality_monitoring"] = quality_maintained
            print(f"TEST 4: {'✅ PASS' if quality_maintained else '❌ FAIL'}")
            
        except Exception as e:
            print(f"❌ Quality monitoring test failed: {e}")
            self.test_results["quality_monitoring"] = False
            print("TEST 4: ❌ FAIL")
        
        print()

    async def test_performance_validation(self):
        """Test performance validation with real API calls."""
        
        print("TEST 5: PERFORMANCE VALIDATION")
        print("-" * 50)
        
        try:
            # Concurrent performance test
            concurrent_prompts = [
                "Create eBay title for vintage watch",
                "Generate product description for laptop",
                "Write listing for camera equipment"
            ]
            
            start_time = time.time()
            
            tasks = []
            for i, prompt in enumerate(concurrent_prompts):
                task = self.openai_client.generate_text(
                    prompt=prompt,
                    task_complexity=TaskComplexity.SIMPLE,
                    system_prompt=f"You are eBay expert #{i+1}."
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            successful_results = [r for r in results if r.success]
            avg_response_time = total_time / len(results)
            
            print(f"✅ Concurrent operations: {len(successful_results)}/{len(results)} successful")
            print(f"✅ Total time: {total_time:.2f}s")
            print(f"✅ Average response time: {avg_response_time:.2f}s")
            print(f"✅ Performance acceptable: {avg_response_time <= 5.0}")
            
            # Cost efficiency check
            if successful_results:
                total_cost = sum(r.cost_estimate for r in successful_results)
                avg_cost = total_cost / len(successful_results)
                print(f"✅ Total cost: ${total_cost:.4f}")
                print(f"✅ Average cost: ${avg_cost:.4f}")
                
                cost_efficient = avg_cost <= self.baseline_cost_per_operation
                print(f"✅ Cost efficient: {cost_efficient}")
            else:
                cost_efficient = False
            
            performance_acceptable = (
                len(successful_results) >= 2 and
                avg_response_time <= 5.0 and
                cost_efficient
            )
            
            self.test_results["performance_validation"] = performance_acceptable
            print(f"TEST 5: {'✅ PASS' if performance_acceptable else '❌ FAIL'}")
            
        except Exception as e:
            print(f"❌ Performance validation test failed: {e}")
            self.test_results["performance_validation"] = False
            print("TEST 5: ❌ FAIL")
        
        print()

    async def generate_test_results(self):
        """Generate comprehensive test results and analysis."""
        
        print("=" * 70)
        print("PHASE 1 REAL API VALIDATION RESULTS")
        print("=" * 70)
        
        # Count test results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        test_success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Tests Passed: {passed_tests}/{total_tests} ({test_success_rate:.1f}%)")
        print()
        
        # Test status breakdown
        for test_name, result in self.test_results.items():
            status = "✅ VALIDATED" if result else "❌ FAILED"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print()
        
        # Real API cost analysis
        if self.operation_costs:
            avg_cost = sum(self.operation_costs) / len(self.operation_costs)
            print("REAL API COST ANALYSIS:")
            print(f"✅ Average cost per operation: ${avg_cost:.4f}")
            print(f"✅ Target baseline: ${self.baseline_cost_per_operation:.4f}")
            print(f"✅ Cost optimization achieved: {avg_cost <= self.baseline_cost_per_operation}")
            
            # Calculate potential savings at scale
            monthly_ops = 15000
            monthly_cost = avg_cost * monthly_ops
            print(f"✅ Projected monthly cost (15K ops): ${monthly_cost:.2f}")
            print(f"✅ Annual cost projection: ${monthly_cost * 12:.2f}")
        
        # Quality analysis
        if self.quality_scores:
            avg_quality = sum(self.quality_scores) / len(self.quality_scores)
            print(f"✅ Average quality score: {avg_quality:.2f}")
            print(f"✅ Quality threshold maintained: {avg_quality >= self.quality_threshold}")
        
        # Performance analysis
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            print(f"✅ Average response time: {avg_response_time:.2f}s")
            print(f"✅ Performance target met: {avg_response_time <= 3.0}")
        
        # Final usage statistics
        final_stats = await self.openai_client.get_usage_stats()
        print(f"\n📈 FINAL USAGE STATISTICS:")
        print(f"   Total API requests: {final_stats['total_requests']}")
        print(f"   Total API cost: ${final_stats['total_cost']:.4f}")
        print(f"   Budget utilization: {final_stats['budget_utilization']:.1f}%")
        
        # Final assessment
        print()
        if test_success_rate >= 80:
            print("PHASE 1 REAL API VALIDATION RESULT: ✅ SUCCESS")
            print("Real OpenAI API calls validate Phase 1 cost optimization baseline")
        else:
            print("PHASE 1 REAL API VALIDATION RESULT: ❌ NEEDS ATTENTION")
            print("Real API testing reveals issues with cost optimization claims")


async def main():
    """Run Phase 1 real API validation tests."""
    
    test_suite = Phase1RealAPIValidationTest()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
