"""
eBay API Service for Autonomous Agents

This service provides eBay marketplace integration specifically designed for
autonomous agents in the 4+1 architecture. It handles token management,
API calls, and data processing for agent decision-making.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import httpx
from dataclasses import dataclass

from fs_agt_clean.services.marketplace.ebay_oauth_service_v2 import get_ebay_oauth_service

logger = logging.getLogger(__name__)


@dataclass
class EbayListingData:
    """Structured eBay listing data for agent processing."""
    item_id: str
    title: str
    price: float
    currency: str
    condition: str
    category_id: str
    listing_type: str
    quantity_available: int
    watchers: int
    bids: int
    time_left: str
    shipping_cost: Optional[float] = None
    location: Optional[str] = None
    seller_feedback_score: Optional[int] = None
    image_urls: Optional[List[str]] = None


@dataclass
class EbayMarketData:
    """Market analysis data for autonomous agents."""
    category_id: str
    average_price: float
    price_range: Dict[str, float]  # min, max, median
    total_listings: int
    sold_listings: int
    success_rate: float
    trending_keywords: List[str]
    competition_level: str  # low, medium, high


class EbayAgentService:
    """
    eBay API service designed for autonomous agents.
    
    Provides high-level methods for market analysis, listing management,
    and data retrieval optimized for agent decision-making.
    """
    
    def __init__(self):
        self.oauth_service = get_ebay_oauth_service()
        self.base_urls = {
            "sandbox": "https://api.sandbox.ebay.com",
            "production": "https://api.ebay.com"
        }
        
    async def _get_authenticated_headers(self, user_id: str) -> Dict[str, str]:
        """Get authenticated headers for eBay API calls."""
        tokens = await self.oauth_service.get_user_tokens(user_id)
        if not tokens:
            raise ValueError(f"No valid eBay tokens found for user {user_id}")
            
        return {
            "Authorization": f"Bearer {tokens['access_token']}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "X-EBAY-C-ENDUSERCTX": f"affiliateCampaignId=<ePNCampaignId>,affiliateReferenceId=<referenceId>"
        }
    
    async def _make_api_call(
        self, 
        user_id: str, 
        endpoint: str, 
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated eBay API call."""
        try:
            tokens = await self.oauth_service.get_user_tokens(user_id)
            if not tokens:
                raise ValueError(f"No valid tokens for user {user_id}")
                
            base_url = self.base_urls[tokens["environment"]]
            headers = await self._get_authenticated_headers(user_id)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(
                        f"{base_url}{endpoint}",
                        headers=headers,
                        params=params or {}
                    )
                elif method.upper() == "POST":
                    response = await client.post(
                        f"{base_url}{endpoint}",
                        headers=headers,
                        json=data or {}
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"eBay API error for user {user_id}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"eBay API call failed for user {user_id}: {e}")
            raise
    
    async def search_marketplace(
        self, 
        user_id: str, 
        query: str, 
        category_id: Optional[str] = None,
        limit: int = 50,
        sort: str = "BestMatch"
    ) -> List[EbayListingData]:
        """
        Search eBay marketplace for listings.
        
        Optimized for autonomous agent market analysis.
        """
        try:
            params = {
                "q": query,
                "limit": limit,
                "sort": sort,
                "fieldgroups": "MATCHING_ITEMS,EXTENDED"
            }
            
            if category_id:
                params["category_ids"] = category_id
                
            response = await self._make_api_call(
                user_id=user_id,
                endpoint="/buy/browse/v1/item_summary/search",
                params=params
            )
            
            listings = []
            for item in response.get("itemSummaries", []):
                listing = EbayListingData(
                    item_id=item.get("itemId", ""),
                    title=item.get("title", ""),
                    price=float(item.get("price", {}).get("value", 0)),
                    currency=item.get("price", {}).get("currency", "USD"),
                    condition=item.get("condition", "Unknown"),
                    category_id=item.get("categories", [{}])[0].get("categoryId", ""),
                    listing_type=item.get("buyingOptions", [""])[0],
                    quantity_available=item.get("availableQuantity", 0),
                    watchers=item.get("watchCount", 0),
                    bids=item.get("bidCount", 0),
                    time_left=item.get("itemEndDate", ""),
                    shipping_cost=float(item.get("shippingOptions", [{}])[0].get("shippingCost", {}).get("value", 0)) if item.get("shippingOptions") else None,
                    location=item.get("itemLocation", {}).get("city", ""),
                    image_urls=[img.get("imageUrl") for img in item.get("image", {}).get("imageUrls", [])]
                )
                listings.append(listing)
                
            logger.info(f"Found {len(listings)} listings for query '{query}' (user: {user_id})")
            return listings
            
        except Exception as e:
            logger.error(f"Marketplace search failed for user {user_id}: {e}")
            return []
    
    async def get_user_listings(self, user_id: str, limit: int = 50) -> List[EbayListingData]:
        """
        Get user's active eBay listings.
        
        For autonomous agents to analyze current inventory.
        """
        try:
            params = {
                "limit": limit,
                "offset": 0
            }
            
            response = await self._make_api_call(
                user_id=user_id,
                endpoint="/sell/inventory/v1/inventory_item",
                params=params
            )
            
            listings = []
            for item in response.get("inventoryItems", []):
                # Convert inventory item to listing format
                listing = EbayListingData(
                    item_id=item.get("sku", ""),
                    title=item.get("product", {}).get("title", ""),
                    price=float(item.get("availability", {}).get("pickupAtLocationAvailability", [{}])[0].get("quantity", 0)),
                    currency="USD",  # Default for now
                    condition=item.get("condition", "Unknown"),
                    category_id="",  # Not available in inventory API
                    listing_type="FixedPrice",
                    quantity_available=item.get("availability", {}).get("shipToLocationAvailability", {}).get("quantity", 0),
                    watchers=0,
                    bids=0,
                    time_left="",
                    location=item.get("availability", {}).get("pickupAtLocationAvailability", [{}])[0].get("merchantLocationKey", "")
                )
                listings.append(listing)
                
            logger.info(f"Retrieved {len(listings)} user listings (user: {user_id})")
            return listings
            
        except Exception as e:
            logger.error(f"Failed to get user listings for {user_id}: {e}")
            return []
    
    async def analyze_market_trends(
        self, 
        user_id: str, 
        category_id: str,
        keywords: List[str]
    ) -> EbayMarketData:
        """
        Analyze market trends for autonomous agent decision-making.
        
        Provides comprehensive market data for pricing and strategy decisions.
        """
        try:
            all_listings = []
            
            # Search for each keyword to build market picture
            for keyword in keywords[:3]:  # Limit to avoid rate limits
                listings = await self.search_marketplace(
                    user_id=user_id,
                    query=keyword,
                    category_id=category_id,
                    limit=25
                )
                all_listings.extend(listings)
            
            if not all_listings:
                return EbayMarketData(
                    category_id=category_id,
                    average_price=0.0,
                    price_range={"min": 0, "max": 0, "median": 0},
                    total_listings=0,
                    sold_listings=0,
                    success_rate=0.0,
                    trending_keywords=keywords,
                    competition_level="unknown"
                )
            
            # Calculate market metrics
            prices = [listing.price for listing in all_listings if listing.price > 0]
            prices.sort()
            
            average_price = sum(prices) / len(prices) if prices else 0
            price_range = {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0,
                "median": prices[len(prices)//2] if prices else 0
            }
            
            # Determine competition level based on listing count
            total_listings = len(all_listings)
            if total_listings < 20:
                competition_level = "low"
            elif total_listings < 100:
                competition_level = "medium"
            else:
                competition_level = "high"
            
            market_data = EbayMarketData(
                category_id=category_id,
                average_price=average_price,
                price_range=price_range,
                total_listings=total_listings,
                sold_listings=0,  # Would need sold listings API
                success_rate=0.0,  # Would need historical data
                trending_keywords=keywords,
                competition_level=competition_level
            )
            
            logger.info(f"Market analysis complete for category {category_id} (user: {user_id})")
            return market_data
            
        except Exception as e:
            logger.error(f"Market analysis failed for user {user_id}: {e}")
            return EbayMarketData(
                category_id=category_id,
                average_price=0.0,
                price_range={"min": 0, "max": 0, "median": 0},
                total_listings=0,
                sold_listings=0,
                success_rate=0.0,
                trending_keywords=keywords,
                competition_level="unknown"
            )


# Global service instance
_ebay_agent_service = None

def get_ebay_agent_service() -> EbayAgentService:
    """Get global eBay agent service instance."""
    global _ebay_agent_service
    if _ebay_agent_service is None:
        _ebay_agent_service = EbayAgentService()
    return _ebay_agent_service
