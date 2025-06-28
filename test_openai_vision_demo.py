#!/usr/bin/env python3
"""
Real OpenAI Vision Demo for FlipSync
===================================

This script demonstrates the complete JPEG → analyzed → priced → listed workflow
using real OpenAI GPT-4o Vision API with actual image processing.

Features:
- Real image analysis with OpenAI Vision API
- Cost tracking and budget management
- Rate limiting and error handling
- Complete product listing generation
- Production simulation with real APIs
"""

import asyncio
import base64
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenAIVisionDemo:
    """Comprehensive demo of OpenAI Vision integration."""
    
    def __init__(self):
        self.start_time = time.time()
        self.test_results = {}
        
    def log(self, message: str):
        """Log message with timestamp."""
        elapsed = time.time() - self.start_time
        print(f"[{elapsed:6.2f}s] {message}")
        logger.info(message)
    
    def create_test_image_data(self) -> bytes:
        """Create test image data for demonstration."""
        # Create a simple test image (1x1 pixel PNG)
        import io
        from PIL import Image
        
        # Create a small test image
        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        return img_buffer.getvalue()
    
    async def test_openai_configuration(self) -> Dict[str, Any]:
        """Test 1: Verify OpenAI configuration and API access."""
        test_name = "openai_configuration"
        self.log(f"Starting Test 1: {test_name}")
        
        start_time = time.time()
        try:
            # Check environment variables
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": "OPENAI_API_KEY environment variable not set",
                    "duration": time.time() - start_time
                }
            
            # Import OpenAI client
            from fs_agt_clean.core.ai.openai_client import (
                create_openai_client,
                OpenAIModel,
                TaskComplexity
            )
            
            # Create client
            client = create_openai_client(
                api_key=api_key,
                model=OpenAIModel.GPT_4O_LATEST,
                daily_budget=5.0  # $5 budget for testing
            )
            
            # Test simple text generation
            response = await client.generate_text(
                "Say 'OpenAI integration working' if you can read this.",
                TaskComplexity.SIMPLE
            )
            
            duration = time.time() - start_time
            
            if response.success and "working" in response.content.lower():
                self.log(f"✅ OpenAI configuration test passed in {duration:.2f}s")
                return {
                    "test": test_name,
                    "status": "PASSED",
                    "response_time": response.response_time,
                    "cost": response.cost_estimate,
                    "model": response.model,
                    "duration": duration
                }
            else:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": response.error_message or "Unexpected response",
                    "duration": duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"❌ OpenAI configuration test failed: {e}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e),
                "duration": duration
            }
    
    async def test_vision_analysis_service(self) -> Dict[str, Any]:
        """Test 2: Test real vision analysis with OpenAI."""
        test_name = "vision_analysis_service"
        self.log(f"Starting Test 2: {test_name}")
        
        start_time = time.time()
        try:
            # Import vision service
            from fs_agt_clean.core.ai.vision_clients import VisionAnalysisService
            
            # Create service
            vision_service = VisionAnalysisService(config={"daily_budget": 5.0})
            
            # Create test image
            test_image_data = self.create_test_image_data()
            self.log(f"Created test image: {len(test_image_data)} bytes")
            
            # Analyze image
            result = await vision_service.analyze_image(
                image_data=test_image_data,
                analysis_type="product_identification",
                marketplace="ebay",
                additional_context="Test product for eBay listing optimization"
            )
            
            duration = time.time() - start_time
            
            # Validate result
            if result.confidence > 0:
                self.log(f"✅ Vision analysis test passed in {duration:.2f}s")
                self.log(f"   Confidence: {result.confidence:.2f}")
                self.log(f"   Product: {result.product_details.get('name', 'Unknown')}")
                
                return {
                    "test": test_name,
                    "status": "PASSED",
                    "confidence": result.confidence,
                    "product_name": result.product_details.get('name'),
                    "analysis_length": len(result.analysis),
                    "duration": duration
                }
            else:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": "Zero confidence result",
                    "duration": duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"❌ Vision analysis test failed: {e}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e),
                "duration": duration
            }
    
    async def test_complete_workflow(self) -> Dict[str, Any]:
        """Test 3: Complete JPEG → analyzed → priced → listed workflow."""
        test_name = "complete_workflow"
        self.log(f"Starting Test 3: {test_name}")
        
        start_time = time.time()
        try:
            # Import required components
            from fs_agt_clean.core.ai.vision_clients import GPT4VisionClient
            
            # Create GPT-4 Vision client
            gpt4_client = GPT4VisionClient()
            
            # Create test image
            test_image_data = self.create_test_image_data()
            
            # Step 1: Analyze image
            self.log("Step 1: Analyzing image...")
            analysis_result = await gpt4_client.analyze_image(
                image_data=test_image_data,
                analysis_type="product_identification",
                marketplace="ebay",
                additional_context="Vintage collectible item for eBay auction"
            )
            
            if "error" in analysis_result:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": f"Analysis failed: {analysis_result['error']}",
                    "duration": time.time() - start_time
                }
            
            # Step 2: Generate listing
            self.log("Step 2: Generating listing...")
            listing_result = await gpt4_client.generate_listing_from_image(
                image_data=test_image_data,
                marketplace="ebay",
                additional_context="Vintage collectible item for eBay auction"
            )
            
            if "error" in listing_result:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": f"Listing generation failed: {listing_result['error']}",
                    "duration": time.time() - start_time
                }
            
            duration = time.time() - start_time
            
            # Validate complete workflow
            required_fields = ["title", "description", "category", "price_suggestions"]
            missing_fields = [field for field in required_fields if field not in listing_result]
            
            if not missing_fields:
                self.log(f"✅ Complete workflow test passed in {duration:.2f}s")
                self.log(f"   Title: {listing_result['title']}")
                self.log(f"   Category: {listing_result['category']}")
                self.log(f"   Price: ${listing_result['price_suggestions'].get('buy_it_now', 0):.2f}")
                
                return {
                    "test": test_name,
                    "status": "PASSED",
                    "title": listing_result["title"],
                    "category": listing_result["category"],
                    "price_suggestions": listing_result["price_suggestions"],
                    "confidence": listing_result.get("confidence", 0),
                    "duration": duration
                }
            else:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": f"Missing required fields: {missing_fields}",
                    "duration": duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"❌ Complete workflow test failed: {e}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e),
                "duration": duration
            }
    
    async def test_cost_and_usage_tracking(self) -> Dict[str, Any]:
        """Test 4: Cost tracking and usage monitoring."""
        test_name = "cost_and_usage_tracking"
        self.log(f"Starting Test 4: {test_name}")
        
        start_time = time.time()
        try:
            # Import OpenAI client
            from fs_agt_clean.core.ai.openai_client import create_openai_client, OpenAIModel
            
            # Create client with budget tracking
            client = create_openai_client(
                model=OpenAIModel.GPT_4O_MINI,  # Use cheaper model for testing
                daily_budget=1.0  # $1 budget
            )
            
            # Get initial usage stats
            initial_stats = await client.get_usage_stats()
            
            # Make a few requests
            for i in range(3):
                response = await client.generate_text(f"Test request {i+1}")
                self.log(f"Request {i+1}: ${response.cost_estimate:.4f}")
            
            # Get final usage stats
            final_stats = await client.get_usage_stats()
            
            duration = time.time() - start_time
            
            # Validate cost tracking
            cost_increase = final_stats["total_cost"] - initial_stats["total_cost"]
            
            if cost_increase > 0:
                self.log(f"✅ Cost tracking test passed in {duration:.2f}s")
                self.log(f"   Total cost increase: ${cost_increase:.4f}")
                self.log(f"   Budget utilization: {final_stats['budget_utilization']:.1f}%")
                
                return {
                    "test": test_name,
                    "status": "PASSED",
                    "cost_increase": cost_increase,
                    "budget_utilization": final_stats["budget_utilization"],
                    "total_requests": final_stats["total_requests"],
                    "duration": duration
                }
            else:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": "No cost increase detected",
                    "duration": duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"❌ Cost tracking test failed: {e}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e),
                "duration": duration
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all OpenAI vision demo tests."""
        self.log("🚀 Starting OpenAI Vision Demo Tests")
        self.log("=" * 60)
        
        # Run tests sequentially
        tests = [
            self.test_openai_configuration,
            self.test_vision_analysis_service,
            self.test_complete_workflow,
            self.test_cost_and_usage_tracking
        ]
        
        results = {}
        passed_tests = 0
        
        for test_func in tests:
            result = await test_func()
            results[result["test"]] = result
            
            if result["status"] == "PASSED":
                passed_tests += 1
            
            self.log("-" * 40)
        
        # Summary
        total_tests = len(tests)
        success_rate = (passed_tests / total_tests) * 100
        
        self.log("=" * 60)
        self.log(f"📊 DEMO RESULTS SUMMARY")
        self.log(f"Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        self.log(f"Total duration: {time.time() - self.start_time:.2f}s")
        
        if success_rate >= 75:
            self.log("✅ OpenAI Vision integration is working correctly!")
        else:
            self.log("❌ OpenAI Vision integration needs attention")
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "total_duration": time.time() - self.start_time
            },
            "test_results": results
        }


async def main():
    """Run the OpenAI Vision demo."""
    demo = OpenAIVisionDemo()
    results = await demo.run_all_tests()
    
    # Save results to file
    with open("openai_vision_demo_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: openai_vision_demo_results.json")
    return results


if __name__ == "__main__":
    asyncio.run(main())
