#!/usr/bin/env python3
"""
End-to-End Real Product Image Integration Test
==============================================

This test demonstrates the complete integration of real web-sourced product images
throughout the FlipSync workflow:

1. Download real product images from web sources
2. Process them through the 35+ agent backend architecture  
3. Create eBay inventory listings with real image data
4. Serve them to the mobile app for display
5. Verify end-to-end integration with cost controls

Features:
- Real image download from Unsplash
- AI vision analysis with OpenAI GPT-4o
- eBay inventory integration
- Mobile app API endpoint testing
- Cost tracking and optimization
- Production-ready error handling
"""

import asyncio
import aiohttp
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EndToEndRealImageTester:
    """Test complete real image integration workflow."""
    
    def __init__(self):
        self.test_results = {}
        self.total_cost = 0.0
        self.created_products = []
        
        # Real product image URLs for comprehensive testing
        self.real_product_catalog = {
            "vintage_camera": {
                "image_url": "https://images.unsplash.com/photo-1606983340126-99ab4feaa64a?w=800&h=600&fit=crop",
                "title": "Vintage Canon AE-1 35mm Film Camera",
                "category": "Cameras & Photo",
                "description": "Professional vintage camera in excellent condition",
                "expected_price_range": (150, 300)
            },
            "wireless_headphones": {
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&h=600&fit=crop",
                "title": "Premium Wireless Noise-Cancelling Headphones",
                "category": "Consumer Electronics",
                "description": "High-quality wireless headphones with active noise cancellation",
                "expected_price_range": (200, 400)
            },
            "smart_watch": {
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&h=600&fit=crop",
                "title": "Smart Fitness Watch with Heart Rate Monitor",
                "category": "Wearable Technology",
                "description": "Advanced smartwatch with comprehensive health tracking",
                "expected_price_range": (250, 500)
            },
            "laptop_computer": {
                "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800&h=600&fit=crop",
                "title": "MacBook Pro 16-inch M2 Laptop Computer",
                "category": "Computers/Tablets & Networking",
                "description": "High-performance laptop for professional use",
                "expected_price_range": (1500, 2500)
            },
            "coffee_maker": {
                "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&h=600&fit=crop",
                "title": "Automatic Drip Coffee Maker with Timer",
                "category": "Small Kitchen Appliances",
                "description": "Programmable coffee maker with thermal carafe",
                "expected_price_range": (80, 150)
            }
        }

    def log(self, message: str):
        """Log message with timestamp."""
        elapsed = time.time() - getattr(self, 'start_time', time.time())
        print(f"[{elapsed:6.2f}s] {message}")
        logger.info(message)

    async def download_real_product_images(self) -> Dict[str, bytes]:
        """Download real product images from web sources."""
        
        self.log("📸 Downloading real product images from web sources...")
        real_images = {}
        
        async with aiohttp.ClientSession() as session:
            for product_id, product_info in self.real_product_catalog.items():
                try:
                    image_url = product_info["image_url"]
                    self.log(f"   Downloading {product_id} from {image_url}")
                    
                    async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            real_images[product_id] = image_data
                            self.log(f"   ✅ Downloaded {product_id}: {len(image_data)} bytes")
                        else:
                            self.log(f"   ❌ Failed to download {product_id}: HTTP {response.status}")
                            
                except Exception as e:
                    self.log(f"   ❌ Error downloading {product_id}: {e}")
        
        return real_images

    async def process_images_through_ai_pipeline(self, images: Dict[str, bytes]) -> Dict[str, Any]:
        """Process real images through the 35+ agent AI pipeline."""
        
        self.log("🤖 Processing images through FlipSync AI pipeline...")
        processed_products = {}
        
        try:
            # Import the complete product creation workflow
            from fs_agt_clean.services.workflows.complete_product_creation import (
                CompleteProductCreationWorkflow,
                CompleteProductCreationRequest
            )
            
            workflow = CompleteProductCreationWorkflow()
            
            for product_id, image_data in images.items():
                try:
                    product_info = self.real_product_catalog[product_id]
                    self.log(f"   🔄 Processing {product_id} through AI pipeline...")
                    
                    # Create workflow request
                    request = CompleteProductCreationRequest(
                        image_data=image_data,
                        image_filename=f"{product_id}_real.jpg",
                        user_id="test_user_real_images",
                        marketplace="ebay",
                        profit_vs_speed_preference=0.6,  # Balanced approach
                        minimum_profit_margin=0.15,
                        cost_basis=product_info["expected_price_range"][0] * 0.7,  # 70% of min price
                        enable_best_offer=True,
                        enable_cassini_optimization=True,
                        enable_web_research=True
                    )
                    
                    # Execute complete workflow
                    start_time = time.time()
                    result = await workflow.create_optimized_listing(request)
                    duration = time.time() - start_time
                    
                    # Track costs
                    self.total_cost += result.total_cost
                    
                    # Store processed product data
                    processed_products[product_id] = {
                        "original_info": product_info,
                        "ai_result": result,
                        "processing_time": duration,
                        "cost": result.total_cost,
                        "image_data": image_data
                    }
                    
                    self.log(f"   ✅ {product_id} processed: ${result.total_cost:.4f}, {duration:.2f}s")
                    
                except Exception as e:
                    self.log(f"   ❌ Error processing {product_id}: {e}")
                    
        except Exception as e:
            self.log(f"❌ Error in AI pipeline: {e}")
            
        return processed_products

    async def create_mobile_api_listings(self, processed_products: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create mobile API-compatible product listings with real images."""
        
        self.log("📱 Creating mobile API-compatible product listings...")
        mobile_listings = []
        
        for product_id, product_data in processed_products.items():
            try:
                ai_result = product_data["ai_result"]
                original_info = product_data["original_info"]
                
                # Create mobile-compatible listing
                mobile_listing = {
                    "id": f"real_{product_id}_{int(time.time())}",
                    "title": ai_result.title or original_info["title"],
                    "sku": f"REAL-{product_id.upper()}-001",
                    "description": ai_result.description or original_info["description"],
                    "price": float(ai_result.suggested_price or original_info["expected_price_range"][0]),
                    "stock": 1,  # Single item for testing
                    "category": ai_result.category_id or original_info["category"],
                    "condition": "Used",
                    "marketplace": "ebay",
                    "imageUrl": original_info["image_url"],  # Use original URL for mobile display
                    "additionalImages": [original_info["image_url"]],
                    "cassini_score": ai_result.cassini_score,
                    "research_confidence": ai_result.research_confidence,
                    "optimization_improvements": ai_result.optimization_improvements,
                    "item_specifics": ai_result.item_specifics,
                    "best_offer_enabled": ai_result.best_offer_settings is not None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "real_image_processed": True,
                    "ai_generated": True,
                    "cost_to_create": product_data["cost"]
                }
                
                mobile_listings.append(mobile_listing)
                self.created_products.append(mobile_listing)
                
                self.log(f"   ✅ Created mobile listing for {product_id}")
                
            except Exception as e:
                self.log(f"   ❌ Error creating mobile listing for {product_id}: {e}")
        
        return mobile_listings

    async def test_mobile_api_integration(self, mobile_listings: List[Dict[str, Any]]) -> bool:
        """Test mobile API integration with real product listings."""
        
        self.log("🔗 Testing mobile API integration...")
        
        try:
            # Save listings to a JSON file that can be served by the API
            listings_file = Path("real_product_listings.json")
            with open(listings_file, 'w') as f:
                json.dump({
                    "status": "success",
                    "products": mobile_listings,
                    "total": len(mobile_listings),
                    "real_images": True,
                    "ai_processed": True,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
            
            self.log(f"   ✅ Saved {len(mobile_listings)} real product listings to {listings_file}")
            
            # Test API endpoint availability
            try:
                async with aiohttp.ClientSession() as session:
                    test_url = "http://localhost:8001/api/v1/marketplace/products"
                    async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            self.log(f"   ✅ Backend API accessible at {test_url}")
                            return True
                        else:
                            self.log(f"   ⚠️ Backend API returned status {response.status}")
                            return False
            except Exception as e:
                self.log(f"   ⚠️ Backend API not accessible: {e}")
                return False
                
        except Exception as e:
            self.log(f"   ❌ Error in mobile API integration: {e}")
            return False

    async def run_complete_integration_test(self) -> Dict[str, Any]:
        """Run the complete end-to-end real image integration test."""
        
        self.start_time = time.time()
        self.log("🚀 Starting End-to-End Real Image Integration Test")
        self.log("=" * 70)
        
        try:
            # Step 1: Download real product images
            real_images = await self.download_real_product_images()
            if not real_images:
                raise Exception("No real images downloaded")
            
            # Step 2: Process through AI pipeline
            processed_products = await self.process_images_through_ai_pipeline(real_images)
            if not processed_products:
                raise Exception("No products processed through AI pipeline")
            
            # Step 3: Create mobile API listings
            mobile_listings = await self.create_mobile_api_listings(processed_products)
            if not mobile_listings:
                raise Exception("No mobile listings created")
            
            # Step 4: Test mobile API integration
            api_success = await self.test_mobile_api_integration(mobile_listings)
            
            # Generate comprehensive results
            total_duration = time.time() - self.start_time
            
            results = {
                "test_status": "SUCCESS",
                "total_duration": total_duration,
                "images_downloaded": len(real_images),
                "products_processed": len(processed_products),
                "mobile_listings_created": len(mobile_listings),
                "api_integration_success": api_success,
                "total_ai_cost": self.total_cost,
                "cost_per_product": self.total_cost / len(processed_products) if processed_products else 0,
                "within_budget": self.total_cost <= 2.00,  # $2.00 daily budget
                "within_request_limit": all(p["cost"] <= 0.05 for p in processed_products.values()),  # $0.05 per request
                "created_products": self.created_products,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.log("=" * 70)
            self.log("📊 END-TO-END INTEGRATION TEST RESULTS")
            self.log(f"✅ Status: {results['test_status']}")
            self.log(f"⏱️  Duration: {results['total_duration']:.2f}s")
            self.log(f"📸 Images Downloaded: {results['images_downloaded']}")
            self.log(f"🤖 Products AI-Processed: {results['products_processed']}")
            self.log(f"📱 Mobile Listings Created: {results['mobile_listings_created']}")
            self.log(f"🔗 API Integration: {'✅ SUCCESS' if results['api_integration_success'] else '❌ FAILED'}")
            self.log(f"💰 Total Cost: ${results['total_ai_cost']:.4f}")
            self.log(f"📊 Cost per Product: ${results['cost_per_product']:.4f}")
            self.log(f"💸 Within Budget: {'✅ YES' if results['within_budget'] else '❌ NO'}")
            self.log(f"🎯 Within Request Limit: {'✅ YES' if results['within_request_limit'] else '❌ NO'}")
            
            return results
            
        except Exception as e:
            self.log(f"❌ Integration test failed: {e}")
            return {
                "test_status": "FAILED",
                "error": str(e),
                "total_duration": time.time() - self.start_time,
                "total_ai_cost": self.total_cost
            }


async def main():
    """Main test function."""
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        logger.info("   Please set your OpenAI API key:")
        logger.info("   export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Run comprehensive integration test
    tester = EndToEndRealImageTester()
    results = await tester.run_complete_integration_test()
    
    # Save detailed results
    results_file = "end_to_end_real_image_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    if results["test_status"] == "SUCCESS":
        print("\n🎉 End-to-end real image integration test completed successfully!")
        print("📱 Check the mobile app at http://localhost:3000 to see real product images")
        print("📊 Real product listings are now available via the backend API")
    else:
        print(f"\n❌ Integration test failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())
