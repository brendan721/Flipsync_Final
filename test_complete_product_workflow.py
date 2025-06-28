#!/usr/bin/env python3
"""
Test Complete Product Creation Workflow
======================================

This script tests the complete image-to-listing workflow with sample images:
1. Image analysis with OpenAI Vision
2. Enhanced product research with web scraping
3. Cassini optimization
4. Best Offer configuration
5. Final optimized listing generation

Usage:
    python test_complete_product_workflow.py
"""

import asyncio
import base64
import json
import logging
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, List
import aiohttp

from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CompleteWorkflowTester:
    """Test the complete product creation workflow."""

    def __init__(self):
        self.test_results = {}
        self.total_cost = 0.0

        # Real product image URLs for testing
        self.real_product_images = {
            "vintage_camera": "https://images.unsplash.com/photo-1606983340126-99ab4feaa64a?w=800&h=600&fit=crop",
            "wireless_headphones": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&h=600&fit=crop",
            "smart_watch": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&h=600&fit=crop",
            "laptop_computer": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&h=600&fit=crop",
            "coffee_maker": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&h=600&fit=crop",
        }

    async def create_sample_product_images(self) -> Dict[str, bytes]:
        """Download real product images for testing, with synthetic fallbacks."""

        logger.info("📸 Attempting to download real product images...")

        # First try to download real images
        try:
            real_images = await self.download_real_product_images()
            if real_images:
                logger.info(
                    f"✅ Successfully downloaded {len(real_images)} real product images"
                )
                return real_images
        except Exception as e:
            logger.warning(f"⚠️ Failed to download real images: {e}")

        # Fallback to synthetic images
        logger.info("🎨 Falling back to synthetic product images...")
        return self._create_synthetic_images()

    async def download_real_product_images(self) -> Dict[str, bytes]:
        """Download real product images from web sources."""

        real_images = {}

        async with aiohttp.ClientSession() as session:
            for product_name, image_url in self.real_product_images.items():
                try:
                    logger.info(f"Downloading real image for {product_name}...")

                    async with session.get(
                        image_url, timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            real_images[product_name] = image_data
                            logger.info(
                                f"✅ Downloaded {product_name}: {len(image_data)} bytes"
                            )
                        else:
                            logger.warning(
                                f"❌ Failed to download {product_name}: HTTP {response.status}"
                            )

                except Exception as e:
                    logger.error(f"❌ Error downloading {product_name}: {e}")

        return real_images

    def _create_synthetic_images(self) -> Dict[str, bytes]:
        """Create synthetic product images as fallback."""

        sample_images = {}

        # Create different product category images
        products = [
            {
                "name": "vintage_camera",
                "text": "Vintage Camera\nFilm SLR\nExcellent Condition",
                "color": (30, 30, 30),
                "bg_color": (245, 245, 245),
            },
            {
                "name": "wireless_headphones",
                "text": "Wireless Headphones\nNoise Cancelling\nPremium Audio",
                "color": (50, 50, 50),
                "bg_color": (255, 255, 255),
            },
            {
                "name": "smart_watch",
                "text": "Smart Watch\nFitness Tracker\nBluetooth",
                "color": (20, 20, 20),
                "bg_color": (240, 240, 240),
            },
            {
                "name": "laptop_computer",
                "text": "Laptop Computer\nHigh Performance\nPortable",
                "color": (40, 40, 40),
                "bg_color": (250, 250, 250),
            },
            {
                "name": "coffee_maker",
                "text": "Coffee Maker\nAutomatic Brew\nStainless Steel",
                "color": (25, 25, 25),
                "bg_color": (248, 248, 248),
            },
        ]

        for product in products:
            try:
                # Create image
                img = Image.new("RGB", (800, 600), product["bg_color"])
                draw = ImageDraw.Draw(img)

                # Try to use a better font, fall back to default
                try:
                    font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
                    )
                    small_font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32
                    )
                except:
                    font = ImageFont.load_default()
                    small_font = ImageFont.load_default()

                # Draw product representation
                # Main product rectangle
                draw.rectangle(
                    [150, 150, 650, 450],
                    fill=product["color"],
                    outline=(100, 100, 100),
                    width=3,
                )

                # Product text
                lines = product["text"].split("\n")
                y_offset = 200
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                    x = (800 - text_width) // 2
                    draw.text((x, y_offset), line, fill=(255, 255, 255), font=font)
                    y_offset += 60

                # Add some product details
                draw.text(
                    (200, 500),
                    f"Premium {product['name'].replace('_', ' ').title()}",
                    fill=(100, 100, 100),
                    font=small_font,
                )
                draw.text(
                    (200, 530),
                    "Excellent Condition",
                    fill=(100, 100, 100),
                    font=small_font,
                )

                # Convert to bytes
                img_buffer = BytesIO()
                img.save(img_buffer, format="JPEG", quality=95)
                sample_images[product["name"]] = img_buffer.getvalue()

                logger.info(
                    f"Created synthetic image for {product['name']}: {len(sample_images[product['name']])} bytes"
                )

            except Exception as e:
                logger.error(
                    f"Error creating synthetic image for {product['name']}: {e}"
                )

        return sample_images

    async def test_complete_workflow(self):
        """Test the complete product creation workflow."""

        logger.info("🚀 Starting Complete Product Creation Workflow Test")
        logger.info("=" * 60)

        try:
            # Import the workflow service
            from fs_agt_clean.services.workflows.complete_product_creation import (
                CompleteProductCreationWorkflow,
                CompleteProductCreationRequest,
            )

            # Create workflow instance
            workflow = CompleteProductCreationWorkflow()

            # Create sample images (now async to support real image downloads)
            logger.info("📸 Creating sample product images...")
            sample_images = await self.create_sample_product_images()

            if not sample_images:
                logger.error("❌ No sample images created")
                return

            # Test each product category
            for product_name, image_data in sample_images.items():
                await self._test_single_product(workflow, product_name, image_data)

            # Generate summary report
            await self._generate_summary_report()

        except Exception as e:
            logger.error(f"❌ Error in complete workflow test: {e}")
            import traceback

            traceback.print_exc()

    async def _test_single_product(
        self, workflow, product_name: str, image_data: bytes
    ):
        """Test workflow for a single product."""

        logger.info(f"\n🔍 Testing {product_name.title()} Workflow")
        logger.info("-" * 40)

        start_time = time.time()

        try:
            # Create request with different preferences for variety
            preferences = {
                "vintage_camera": {
                    "profit_vs_speed": 0.4,
                    "min_margin": 0.18,
                },  # Speed leaning
                "wireless_headphones": {
                    "profit_vs_speed": 0.5,
                    "min_margin": 0.15,
                },  # Balanced
                "smart_watch": {
                    "profit_vs_speed": 0.7,
                    "min_margin": 0.20,
                },  # Profit leaning
                "laptop_computer": {
                    "profit_vs_speed": 0.8,
                    "min_margin": 0.25,
                },  # Profit focused
                "coffee_maker": {
                    "profit_vs_speed": 0.3,
                    "min_margin": 0.12,
                },  # Speed focused
            }

            pref = preferences.get(
                product_name, {"profit_vs_speed": 0.5, "min_margin": 0.15}
            )

            request = CompleteProductCreationRequest(
                image_data=image_data,
                image_filename=f"{product_name}_sample.jpg",
                user_id="test_user_001",
                marketplace="ebay",
                profit_vs_speed_preference=pref["profit_vs_speed"],
                minimum_profit_margin=pref["min_margin"],
                cost_basis=50.0,  # Sample cost basis
                enable_best_offer=True,
                enable_cassini_optimization=True,
                enable_web_research=True,  # Set to False to skip web scraping in testing
            )

            # Execute workflow
            logger.info(
                f"   🔄 Processing {product_name} image ({len(image_data)} bytes)..."
            )
            result = await workflow.create_optimized_listing(request)

            # Record results
            duration = time.time() - start_time
            self.total_cost += result.total_cost

            self.test_results[product_name] = {
                "success": True,
                "duration": duration,
                "cost": result.total_cost,
                "cassini_score": result.cassini_score,
                "research_confidence": result.research_confidence,
                "title": result.title,
                "category": result.category_id,
                "suggested_price": result.suggested_price,
                "item_specifics_count": len(result.item_specifics),
                "improvements_count": len(result.optimization_improvements),
                "sources_used": result.sources_used,
                "best_offer_configured": result.best_offer_settings is not None,
            }

            # Log results
            logger.info(
                f"   ✅ {product_name.title()} workflow completed successfully!"
            )
            logger.info(f"      📊 Cassini Score: {result.cassini_score}/100")
            logger.info(
                f"      🔬 Research Confidence: {result.research_confidence:.1%}"
            )
            logger.info(f"      💰 Suggested Price: ${result.suggested_price:.2f}")
            logger.info(f"      🏷️  Title: {result.title[:50]}...")
            logger.info(f"      📋 Item Specifics: {len(result.item_specifics)} fields")
            logger.info(f"      ⚡ Processing Time: {duration:.2f}s")
            logger.info(f"      💸 Cost: ${result.total_cost:.4f}")

            if result.optimization_improvements:
                logger.info(
                    f"      🚀 Improvements: {', '.join(result.optimization_improvements[:3])}"
                )

            if result.best_offer_settings:
                pref_text = (
                    "Speed"
                    if result.best_offer_settings.profit_vs_speed_preference < 0.4
                    else (
                        "Profit"
                        if result.best_offer_settings.profit_vs_speed_preference > 0.6
                        else "Balanced"
                    )
                )
                logger.info(f"      🤝 Best Offer: {pref_text} strategy configured")

        except Exception as e:
            logger.error(f"   ❌ Error testing {product_name}: {e}")
            self.test_results[product_name] = {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time,
                "cost": 0.0,
            }

    async def _generate_summary_report(self):
        """Generate summary report of all tests."""

        logger.info("\n📊 WORKFLOW TEST SUMMARY REPORT")
        logger.info("=" * 60)

        successful_tests = [
            name for name, result in self.test_results.items() if result.get("success")
        ]
        failed_tests = [
            name
            for name, result in self.test_results.items()
            if not result.get("success")
        ]

        logger.info(
            f"✅ Successful Tests: {len(successful_tests)}/{len(self.test_results)}"
        )
        logger.info(f"❌ Failed Tests: {len(failed_tests)}")
        logger.info(f"💰 Total Cost: ${self.total_cost:.4f}")

        if successful_tests:
            logger.info("\n🎯 Performance Metrics:")

            # Calculate averages
            avg_duration = sum(
                self.test_results[name]["duration"] for name in successful_tests
            ) / len(successful_tests)
            avg_cassini = sum(
                self.test_results[name].get("cassini_score", 0)
                for name in successful_tests
            ) / len(successful_tests)
            avg_confidence = sum(
                self.test_results[name].get("research_confidence", 0)
                for name in successful_tests
            ) / len(successful_tests)
            avg_specifics = sum(
                self.test_results[name].get("item_specifics_count", 0)
                for name in successful_tests
            ) / len(successful_tests)

            logger.info(f"   ⏱️  Average Processing Time: {avg_duration:.2f}s")
            logger.info(f"   📊 Average Cassini Score: {avg_cassini:.1f}/100")
            logger.info(f"   🔬 Average Research Confidence: {avg_confidence:.1%}")
            logger.info(f"   📋 Average Item Specifics: {avg_specifics:.1f} fields")

            # Best performing product
            best_product = max(
                successful_tests,
                key=lambda x: self.test_results[x].get("cassini_score", 0),
            )
            best_score = self.test_results[best_product].get("cassini_score", 0)
            logger.info(
                f"   🏆 Best Cassini Score: {best_product.title()} ({best_score}/100)"
            )

        if failed_tests:
            logger.info(f"\n❌ Failed Tests: {', '.join(failed_tests)}")
            for name in failed_tests:
                error = self.test_results[name].get("error", "Unknown error")
                logger.info(f"   {name}: {error}")

        # Save detailed results
        await self._save_test_results()

        logger.info(f"\n🎉 Complete Product Creation Workflow Test Completed!")
        logger.info(f"📁 Detailed results saved to test_results.json")

    async def _save_test_results(self):
        """Save detailed test results to file."""

        try:
            # Prepare results for JSON serialization
            json_results = {
                "test_summary": {
                    "total_tests": len(self.test_results),
                    "successful_tests": len(
                        [r for r in self.test_results.values() if r.get("success")]
                    ),
                    "total_cost": self.total_cost,
                    "test_timestamp": time.time(),
                },
                "individual_results": self.test_results,
            }

            # Save to file
            with open("test_results.json", "w") as f:
                json.dump(json_results, f, indent=2, default=str)

            logger.info("📁 Test results saved to test_results.json")

        except Exception as e:
            logger.error(f"Error saving test results: {e}")


async def main():
    """Main test function."""

    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        logger.info("   Please set your OpenAI API key:")
        logger.info("   export OPENAI_API_KEY='your-api-key-here'")
        return

    # Run tests
    tester = CompleteWorkflowTester()
    await tester.test_complete_workflow()


if __name__ == "__main__":
    asyncio.run(main())
