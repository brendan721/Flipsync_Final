#!/usr/bin/env python3
"""
Real Image Analysis Workflow Demo for FlipSync
==============================================

This script demonstrates the complete JPEG → analyzed → priced → listed workflow
using real OpenAI GPT-4o Vision API with actual product images.

Features:
- Real image analysis with OpenAI Vision API
- Complete product listing generation
- Cost tracking and performance metrics
- Production-ready error handling
- Structured output validation
"""

import asyncio
import base64
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any
from io import BytesIO
import aiohttp
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RealImageWorkflowDemo:
    """Comprehensive demo of real image analysis workflow."""

    def __init__(self):
        self.start_time = time.time()
        self.test_results = {}
        self.total_cost = 0.0

    def log(self, message: str):
        """Log message with timestamp."""
        elapsed = time.time() - self.start_time
        print(f"[{elapsed:6.2f}s] {message}")
        logger.info(message)

    async def get_real_product_image(
        self, product_type: str = "vintage_camera"
    ) -> bytes:
        """Download a real product image for testing."""

        # Real product image URLs for different product types
        real_image_urls = {
            "vintage_camera": "https://images.unsplash.com/photo-1606983340126-99ab4feaa64a?w=800&h=600&fit=crop",
            "wireless_headphones": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&h=600&fit=crop",
            "smart_watch": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&h=600&fit=crop",
            "laptop": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&h=600&fit=crop",
            "coffee_maker": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&h=600&fit=crop",
        }

        image_url = real_image_urls.get(product_type, real_image_urls["vintage_camera"])

        try:
            self.log(f"Downloading real {product_type} image from web...")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    image_url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        self.log(
                            f"✅ Downloaded real {product_type} image: {len(image_data)} bytes"
                        )
                        return image_data
                    else:
                        self.log(f"❌ Failed to download image: HTTP {response.status}")
                        return self._create_fallback_image(product_type)
        except Exception as e:
            self.log(f"❌ Error downloading real image: {e}")
            return self._create_fallback_image(product_type)

    def _create_fallback_image(self, product_type: str) -> bytes:
        """Create a fallback synthetic image if real image download fails."""
        self.log(f"🎨 Creating fallback synthetic image for {product_type}")

        # Create a more realistic product image
        img = Image.new("RGB", (800, 600), color="white")
        draw = ImageDraw.Draw(img)

        # Draw a camera-like product
        # Camera body
        draw.rectangle([200, 200, 600, 400], fill="black", outline="gray", width=3)

        # Lens
        draw.ellipse([300, 250, 500, 350], fill="darkgray", outline="black", width=2)
        draw.ellipse([320, 270, 480, 330], fill="black")

        # Brand text
        try:
            # Try to use a font, fallback to default if not available
            font = ImageFont.load_default()
        except:
            font = None

        draw.text(
            (220, 180),
            f"{product_type.upper().replace('_', ' ')}",
            fill="black",
            font=font,
        )
        draw.text((220, 420), "Model: Premium", fill="black", font=font)
        draw.text((220, 440), "Excellent Condition", fill="black", font=font)

        # Convert to bytes
        img_buffer = BytesIO()
        img.save(img_buffer, format="JPEG", quality=85)
        return img_buffer.getvalue()

    async def test_real_image_analysis(self) -> Dict[str, Any]:
        """Test 1: Real image analysis with OpenAI Vision API."""
        test_name = "real_image_analysis"
        self.log(f"Starting Test 1: {test_name}")

        start_time = time.time()
        try:
            # Import vision service
            from fs_agt_clean.core.ai.vision_clients import VisionAnalysisService

            # Create service with production settings
            vision_service = VisionAnalysisService(config={"daily_budget": 10.0})

            # Get real product image
            product_image = await self.get_real_product_image("vintage_camera")
            self.log(f"Obtained product image: {len(product_image)} bytes")

            # Analyze image with detailed context
            result = await vision_service.analyze_image(
                image_data=product_image,
                analysis_type="product_identification",
                marketplace="ebay",
                additional_context="Vintage 35mm film camera in excellent condition, includes original case and manual. Perfect for photography enthusiasts and collectors.",
            )

            duration = time.time() - start_time

            # Validate comprehensive result
            if result.confidence > 0.7:
                self.log(f"✅ Real image analysis test passed in {duration:.2f}s")
                self.log(f"   Confidence: {result.confidence:.2f}")
                self.log(f"   Product: {result.product_details.get('name', 'Unknown')}")
                self.log(f"   Brand: {result.product_details.get('brand', 'Unknown')}")
                self.log(
                    f"   Condition: {result.product_details.get('condition', 'Unknown')}"
                )
                self.log(
                    f"   Category: {result.product_details.get('category', 'Unknown')}"
                )
                self.log(
                    f"   Features: {len(result.product_details.get('features', []))} identified"
                )

                return {
                    "test": test_name,
                    "status": "PASSED",
                    "confidence": result.confidence,
                    "product_details": result.product_details,
                    "analysis_length": len(result.analysis),
                    "marketplace_suggestions": len(result.marketplace_suggestions),
                    "duration": duration,
                }
            else:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": f"Low confidence: {result.confidence}",
                    "duration": duration,
                }

        except Exception as e:
            duration = time.time() - start_time
            self.log(f"❌ Real image analysis test failed: {e}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e),
                "duration": duration,
            }

    async def test_complete_listing_generation(self) -> Dict[str, Any]:
        """Test 2: Complete listing generation workflow."""
        test_name = "complete_listing_generation"
        self.log(f"Starting Test 2: {test_name}")

        start_time = time.time()
        try:
            # Import GPT-4 Vision client
            from fs_agt_clean.core.ai.vision_clients import GPT4VisionClient

            # Create client
            gpt4_client = GPT4VisionClient()

            # Get real product image
            product_image = await self.get_real_product_image("vintage_camera")

            # Generate complete listing
            self.log("Generating complete eBay listing...")
            listing_result = await gpt4_client.generate_listing_from_image(
                image_data=product_image,
                marketplace="ebay",
                additional_context="Vintage Canon AE-1 35mm film camera, excellent condition, includes leather case, manual, and original box. Perfect working order, recently serviced.",
            )

            duration = time.time() - start_time

            # Validate listing completeness
            required_fields = [
                "title",
                "description",
                "category",
                "price_suggestions",
                "keywords",
            ]
            missing_fields = [
                field for field in required_fields if field not in listing_result
            ]

            if not missing_fields and "error" not in listing_result:
                self.log(
                    f"✅ Complete listing generation test passed in {duration:.2f}s"
                )
                self.log(f"   Title: {listing_result['title']}")
                self.log(f"   Category: {listing_result['category']}")
                self.log(f"   Keywords: {len(listing_result['keywords'])} SEO keywords")
                self.log(
                    f"   Description length: {len(listing_result['description'])} chars"
                )
                self.log(
                    f"   Price range: ${listing_result['price_suggestions']['starting_price']:.2f} - ${listing_result['price_suggestions']['buy_it_now']:.2f}"
                )
                self.log(f"   Confidence: {listing_result.get('confidence', 0):.2f}")

                return {
                    "test": test_name,
                    "status": "PASSED",
                    "listing": listing_result,
                    "duration": duration,
                }
            else:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": (
                        f"Missing fields: {missing_fields}"
                        if missing_fields
                        else listing_result.get("error", "Unknown error")
                    ),
                    "duration": duration,
                }

        except Exception as e:
            duration = time.time() - start_time
            self.log(f"❌ Complete listing generation test failed: {e}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e),
                "duration": duration,
            }

    async def test_production_simulation(self) -> Dict[str, Any]:
        """Test 3: Production simulation with multiple products."""
        test_name = "production_simulation"
        self.log(f"Starting Test 3: {test_name}")

        start_time = time.time()
        try:
            from fs_agt_clean.core.ai.vision_clients import GPT4VisionClient
            from fs_agt_clean.core.ai.openai_client import create_openai_client

            # Create production-ready client with cost tracking
            client = create_openai_client(daily_budget=5.0)
            gpt4_client = GPT4VisionClient()

            # Simulate multiple product analyses
            products = [
                {
                    "name": "Vintage Camera",
                    "context": "Canon AE-1 35mm film camera, excellent condition",
                },
                {
                    "name": "Electronics",
                    "context": "Vintage electronics device, working condition",
                },
                {
                    "name": "Collectible",
                    "context": "Rare collectible item, mint condition",
                },
            ]

            results = []
            total_cost = 0.0

            for i, product in enumerate(products):
                self.log(f"Processing product {i+1}/3: {product['name']}")

                # Get real product image for variety
                product_types = ["vintage_camera", "wireless_headphones", "laptop"]
                product_type = product_types[i % len(product_types)]
                product_image = await self.get_real_product_image(product_type)

                # Analyze and generate listing
                listing = await gpt4_client.generate_listing_from_image(
                    image_data=product_image,
                    marketplace="ebay",
                    additional_context=product["context"],
                )

                if "error" not in listing:
                    results.append(
                        {
                            "product": product["name"],
                            "title": listing["title"],
                            "category": listing["category"],
                            "confidence": listing.get("confidence", 0),
                        }
                    )

                # Small delay to respect rate limits
                await asyncio.sleep(1)

            # Get usage statistics
            usage_stats = await client.get_usage_stats()
            total_cost = usage_stats["total_cost"]

            duration = time.time() - start_time

            if len(results) >= 2:  # At least 2/3 should succeed
                self.log(f"✅ Production simulation test passed in {duration:.2f}s")
                self.log(f"   Products processed: {len(results)}/3")
                self.log(f"   Total cost: ${total_cost:.4f}")
                self.log(
                    f"   Average confidence: {sum(r['confidence'] for r in results) / len(results):.2f}"
                )

                return {
                    "test": test_name,
                    "status": "PASSED",
                    "products_processed": len(results),
                    "total_cost": total_cost,
                    "results": results,
                    "duration": duration,
                }
            else:
                return {
                    "test": test_name,
                    "status": "FAILED",
                    "error": f"Only {len(results)}/3 products processed successfully",
                    "duration": duration,
                }

        except Exception as e:
            duration = time.time() - start_time
            self.log(f"❌ Production simulation test failed: {e}")
            return {
                "test": test_name,
                "status": "FAILED",
                "error": str(e),
                "duration": duration,
            }

    async def run_complete_workflow(self) -> Dict[str, Any]:
        """Run complete real image workflow demonstration."""
        self.log("🚀 Starting Real Image Analysis Workflow Demo")
        self.log("=" * 60)

        # Run tests sequentially
        tests = [
            self.test_real_image_analysis,
            self.test_complete_listing_generation,
            self.test_production_simulation,
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
        self.log(f"📊 REAL IMAGE WORKFLOW RESULTS")
        self.log(f"Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        self.log(f"Total duration: {time.time() - self.start_time:.2f}s")

        if success_rate >= 80:
            self.log("✅ Real image analysis workflow is fully operational!")
        else:
            self.log("❌ Real image analysis workflow needs attention")

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "total_duration": time.time() - self.start_time,
            },
            "test_results": results,
        }


async def main():
    """Run the real image workflow demo."""
    demo = RealImageWorkflowDemo()
    results = await demo.run_complete_workflow()

    # Save results to file
    with open("real_image_workflow_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: real_image_workflow_results.json")
    return results


if __name__ == "__main__":
    asyncio.run(main())
