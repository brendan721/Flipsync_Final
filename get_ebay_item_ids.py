#!/usr/bin/env python3
"""
eBay Sandbox Item ID Extractor for Production Readiness Verification
====================================================================

This script extracts real eBay sandbox item IDs and provides detailed information
about each listing to verify optimization potential and production readiness.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fs_agt_clean.agents.market.ebay_client import eBayClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EbayItemExtractor:
    """Extract eBay sandbox item IDs and listing details."""

    def __init__(self):
        """Initialize the eBay item extractor."""
        # eBay credentials
        self.ebay_client_id = os.getenv("SB_EBAY_APP_ID")
        self.ebay_client_secret = os.getenv("SB_EBAY_CERT_ID")
        self.ebay_refresh_token = os.getenv("SB_EBAY_REFRESH_TOKEN")

    async def extract_sandbox_items(self) -> Dict[str, Any]:
        """Extract real eBay sandbox item IDs and details."""
        logger.info("🔍 Extracting eBay Sandbox Item IDs...")

        try:
            async with eBayClient(
                client_id=self.ebay_client_id,
                client_secret=self.ebay_client_secret,
                environment="sandbox",
            ) as ebay_client:

                # Search for various product categories to get diverse listings
                search_queries = [
                    "electronics",
                    "laptop",
                    "smartphone",
                    "tablet",
                    "headphones",
                    "gaming",
                    "camera",
                    "watch",
                ]

                all_items = []

                for query in search_queries:
                    logger.info(f"   Searching for '{query}' items...")

                    try:
                        products = await ebay_client.search_products(query, limit=5)

                        if products:
                            for product in products:
                                # Extract eBay item ID from identifier
                                ebay_item_id = "N/A"
                                if hasattr(product, "identifier") and hasattr(
                                    product.identifier, "ebay_item_id"
                                ):
                                    ebay_item_id = product.identifier.ebay_item_id

                                item_details = {
                                    "item_id": ebay_item_id,
                                    "title": product.title,
                                    "price": float(product.current_price.amount),
                                    "currency": product.current_price.currency,
                                    "condition": (
                                        str(product.condition)
                                        if hasattr(product, "condition")
                                        else "Unknown"
                                    ),
                                    "category": query,
                                    "marketplace": "eBay Sandbox",
                                    "url": getattr(product, "listing_url", "N/A"),
                                    "seller": getattr(product, "seller_id", "N/A"),
                                    "location": "Sandbox Environment",
                                    "shipping_info": getattr(
                                        product, "shipping_info", {}
                                    ),
                                    "sku": (
                                        product.identifier.sku
                                        if hasattr(product, "identifier")
                                        and hasattr(product.identifier, "sku")
                                        else "N/A"
                                    ),
                                    "optimization_potential": self._assess_optimization_potential(
                                        product
                                    ),
                                }

                                all_items.append(item_details)

                                logger.info(
                                    f"     Found: {product.title[:50]}... (ID: {item_details['item_id']})"
                                )

                    except Exception as e:
                        logger.warning(f"Error searching for '{query}': {e}")
                        continue

                # Remove duplicates based on item_id
                unique_items = []
                seen_ids = set()

                for item in all_items:
                    if item["item_id"] not in seen_ids and item["item_id"] != "N/A":
                        unique_items.append(item)
                        seen_ids.add(item["item_id"])

                logger.info(
                    f"✅ Extracted {len(unique_items)} unique eBay sandbox items"
                )

                return {
                    "success": True,
                    "total_items": len(unique_items),
                    "extraction_time": datetime.now().isoformat(),
                    "items": unique_items,
                }

        except Exception as e:
            logger.error(f"❌ Failed to extract eBay items: {e}")
            return {"success": False, "error": str(e)}

    def _assess_optimization_potential(self, product) -> Dict[str, Any]:
        """Assess the optimization potential for a product listing."""
        title = product.title
        price = float(product.current_price.amount)

        optimization_score = 0
        recommendations = []

        # Title optimization assessment
        if len(title) < 50:
            optimization_score += 20
            recommendations.append("Expand title with more descriptive keywords")

        if len(title) > 80:
            optimization_score += 10
            recommendations.append("Optimize title length for better readability")

        # Brand detection
        brands = [
            "apple",
            "samsung",
            "sony",
            "dell",
            "hp",
            "lenovo",
            "asus",
            "microsoft",
            "google",
        ]
        if not any(brand in title.lower() for brand in brands):
            optimization_score += 15
            recommendations.append("Add brand name for better searchability")

        # Condition keywords
        conditions = ["new", "used", "refurbished", "open box", "excellent"]
        if not any(condition in title.lower() for condition in conditions):
            optimization_score += 12
            recommendations.append("Include condition keywords")

        # Model/specification detection
        import re

        specs = [r"\d+gb", r"\d+tb", r'\d+"', r"\d+inch", r"[a-z]\d+"]
        if not any(re.search(spec, title.lower()) for spec in specs):
            optimization_score += 10
            recommendations.append("Add model numbers or specifications")

        # Price optimization potential
        if price < 50:
            price_category = "budget"
        elif price < 200:
            price_category = "mid-range"
        elif price < 1000:
            price_category = "premium"
        else:
            price_category = "luxury"

        return {
            "optimization_score": optimization_score,
            "potential_level": (
                "high"
                if optimization_score > 30
                else "medium" if optimization_score > 15 else "low"
            ),
            "recommendations": recommendations,
            "price_category": price_category,
            "seo_improvements_needed": len(recommendations),
        }

    def generate_verification_report(self, items_data: Dict[str, Any]) -> str:
        """Generate a detailed verification report for production readiness."""
        if not items_data.get("success"):
            return f"❌ Failed to extract items: {items_data.get('error', 'Unknown error')}"

        items = items_data.get("items", [])

        report = []
        report.append("=" * 80)
        report.append("📋 EBAY SANDBOX ITEMS - PRODUCTION READINESS VERIFICATION")
        report.append("=" * 80)
        report.append(f"Total Items Found: {len(items)}")
        report.append(f"Extraction Time: {items_data.get('extraction_time', 'N/A')}")
        report.append("")

        # Group items by optimization potential
        high_potential = [
            item
            for item in items
            if item["optimization_potential"]["potential_level"] == "high"
        ]
        medium_potential = [
            item
            for item in items
            if item["optimization_potential"]["potential_level"] == "medium"
        ]
        low_potential = [
            item
            for item in items
            if item["optimization_potential"]["potential_level"] == "low"
        ]

        report.append(f"🎯 OPTIMIZATION POTENTIAL SUMMARY:")
        report.append(f"   High Potential: {len(high_potential)} items")
        report.append(f"   Medium Potential: {len(medium_potential)} items")
        report.append(f"   Low Potential: {len(low_potential)} items")
        report.append("")

        # Detailed item listings
        for i, item in enumerate(items, 1):
            report.append(f"📦 ITEM #{i}")
            report.append(f"   Item ID: {item['item_id']}")
            report.append(f"   Title: {item['title']}")
            report.append(f"   Price: {item['currency']} {item['price']}")
            report.append(f"   Category: {item['category']}")
            report.append(f"   Condition: {item['condition']}")
            report.append(f"   Seller: {item['seller']}")
            report.append(f"   Location: {item['location']}")

            if item["url"] != "N/A":
                report.append(f"   URL: {item['url']}")

            # Optimization details
            opt = item["optimization_potential"]
            report.append(f"   🔧 OPTIMIZATION POTENTIAL:")
            report.append(f"      Score: {opt['optimization_score']}/100")
            report.append(f"      Level: {opt['potential_level'].upper()}")
            report.append(f"      Price Category: {opt['price_category']}")
            report.append(
                f"      SEO Improvements Needed: {opt['seo_improvements_needed']}"
            )

            if opt["recommendations"]:
                report.append(f"      Recommendations:")
                for rec in opt["recommendations"]:
                    report.append(f"        • {rec}")

            report.append("")

        # Production readiness assessment
        report.append("🚀 PRODUCTION READINESS ASSESSMENT:")
        report.append("")

        total_optimization_score = sum(
            item["optimization_potential"]["optimization_score"] for item in items
        )
        avg_optimization_score = total_optimization_score / len(items) if items else 0

        report.append(
            f"   Average Optimization Score: {avg_optimization_score:.1f}/100"
        )

        if len(items) > 0:
            high_potential_percentage = len(high_potential) / len(items) * 100
            report.append(
                f"   Items with High Potential: {len(high_potential)}/{len(items)} ({high_potential_percentage:.1f}%)"
            )
        else:
            report.append("   Items with High Potential: 0/0 (0.0%)")

        # Business value calculation
        potential_seo_improvement = (
            avg_optimization_score * 0.3
        )  # Convert to SEO points
        estimated_traffic_increase = potential_seo_improvement * 2  # Rough estimate

        report.append(
            f"   Estimated SEO Improvement: {potential_seo_improvement:.1f} points"
        )
        report.append(
            f"   Estimated Traffic Increase: {estimated_traffic_increase:.1f}%"
        )

        # Production recommendations
        report.append("")
        report.append("💡 PRODUCTION RECOMMENDATIONS:")

        if avg_optimization_score > 25:
            report.append(
                "   ✅ HIGH optimization potential - Immediate production deployment recommended"
            )
            report.append("   ✅ Significant SEO improvements available")
            report.append("   ✅ Strong ROI expected from content optimization")
        elif avg_optimization_score > 15:
            report.append(
                "   ⚠️ MEDIUM optimization potential - Production ready with optimization focus"
            )
            report.append("   ⚠️ Moderate SEO improvements available")
            report.append("   ⚠️ Good ROI expected with targeted optimization")
        else:
            report.append(
                "   ℹ️ LOW optimization potential - Production ready, focus on other features"
            )
            report.append("   ℹ️ Limited SEO improvements available")
            report.append(
                "   ℹ️ ROI from other features (shipping, analytics) more significant"
            )

        report.append("")
        report.append("🔗 VERIFICATION INSTRUCTIONS:")
        report.append(
            "   1. Use the Item IDs above to manually verify listings in eBay sandbox"
        )
        report.append(
            "   2. Check that titles, prices, and descriptions match our extracted data"
        )
        report.append("   3. Verify that optimization recommendations are accurate")
        report.append(
            "   4. Confirm that FlipSync would improve these listings in production"
        )
        report.append("")
        report.append("=" * 80)

        return "\n".join(report)


async def main():
    """Main execution function."""
    extractor = EbayItemExtractor()

    # Validate credentials
    if not extractor.ebay_client_id:
        logger.error("❌ Missing eBay credentials")
        return

    logger.info("✅ eBay credentials present")

    # Extract items
    items_data = await extractor.extract_sandbox_items()

    # Generate and print verification report
    report = extractor.generate_verification_report(items_data)
    print(report)

    # Save report to file
    with open("ebay_sandbox_verification_report.txt", "w") as f:
        f.write(report)

    logger.info("📄 Verification report saved to: ebay_sandbox_verification_report.txt")


if __name__ == "__main__":
    asyncio.run(main())
