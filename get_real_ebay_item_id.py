#!/usr/bin/env python3
"""
Get Real eBay Item ID
Retrieve the actual eBay item ID that can be verified on eBay.com
"""

import asyncio
import sys
import os
import json
import aiohttp
import ssl
sys.path.insert(0, ".")

async def get_real_ebay_item_details():
    """Get the real eBay item details including verifiable item ID"""
    print("🔍 Getting Real eBay Item Details...")
    
    try:
        # Get access token from Redis
        import redis
        redis_client = redis.Redis(
            host="localhost", 
            port=6379, 
            password="FlipSync2024SecureRedis!", 
            db=1
        )
        
        token_data = redis_client.get("marketplace:ebay:test_user_id")
        if not token_data:
            print("❌ No access token found")
            return None
        
        token_info = json.loads(token_data)
        access_token = token_info.get('access_token')
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Method 1: Try Inventory API
            print("\n📦 Method 1: Checking Inventory API...")
            inventory_url = "https://api.ebay.com/sell/inventory/v1/inventory_item"
            
            async with session.get(inventory_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    inventory_items = data.get('inventoryItems', [])
                    
                    print(f"✅ Found {len(inventory_items)} inventory items")
                    
                    for i, item in enumerate(inventory_items):
                        print(f"\n📦 Inventory Item {i+1}:")
                        print(f"   Raw data: {json.dumps(item, indent=2)}")
                        
                        sku = item.get('sku')
                        if sku:
                            # Try to get offers for this SKU (which might have item IDs)
                            print(f"\n🔍 Getting offers for SKU: {sku}")
                            offers_url = f"https://api.ebay.com/sell/inventory/v1/offer?sku={sku}"
                            
                            async with session.get(offers_url, headers=headers) as offers_response:
                                if offers_response.status == 200:
                                    offers_data = await offers_response.json()
                                    offers = offers_data.get('offers', [])
                                    
                                    print(f"✅ Found {len(offers)} offers for this SKU")
                                    
                                    for j, offer in enumerate(offers):
                                        print(f"\n💰 Offer {j+1}:")
                                        print(f"   Raw offer data: {json.dumps(offer, indent=2)}")
                                        
                                        # Check if offer has listing details
                                        listing = offer.get('listing')
                                        if listing:
                                            listing_id = listing.get('listingId')
                                            if listing_id:
                                                print(f"   🎯 FOUND LISTING ID: {listing_id}")
                                                return {
                                                    "item_id": listing_id,
                                                    "sku": sku,
                                                    "title": item.get('product', {}).get('title', 'N/A'),
                                                    "source": "inventory_api_offer",
                                                    "verification_url": f"https://www.ebay.com/itm/{listing_id}"
                                                }
                                else:
                                    print(f"⚠️ Offers API failed: HTTP {offers_response.status}")
                                    error_text = await offers_response.text()
                                    print(f"   Error: {error_text[:200]}...")
                
                # Method 2: Try Trading API GetMyeBaySelling
                print(f"\n📦 Method 2: Trying Trading API GetMyeBaySelling...")
                
                # Trading API XML request
                xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{access_token}</eBayAuthToken>
    </RequesterCredentials>
    <ActiveList>
        <Include>true</Include>
        <Pagination>
            <EntriesPerPage>10</EntriesPerPage>
            <PageNumber>1</PageNumber>
        </Pagination>
    </ActiveList>
    <SoldList>
        <Include>true</Include>
        <Pagination>
            <EntriesPerPage>10</EntriesPerPage>
            <PageNumber>1</PageNumber>
        </Pagination>
    </SoldList>
    <Version>1193</Version>
</GetMyeBaySellingRequest>"""
                
                trading_headers = {
                    "X-EBAY-API-COMPATIBILITY-LEVEL": "1193",
                    "X-EBAY-API-DEV-NAME": "e83908d0-476b-4534-a947-3a88227709e4",
                    "X-EBAY-API-APP-NAME": "BrendanB-Nashvill-PRD-7f5c11990-62c1c838",
                    "X-EBAY-API-CERT-NAME": "PRD-f5c119904e18-fb68-4e53-9b35-49ef",
                    "X-EBAY-API-CALL-NAME": "GetMyeBaySelling",
                    "X-EBAY-API-SITEID": "0",
                    "Content-Type": "text/xml"
                }
                
                trading_url = "https://api.ebay.com/ws/api.dll"
                
                async with session.post(trading_url, headers=trading_headers, data=xml_request) as trading_response:
                    if trading_response.status == 200:
                        xml_response = await trading_response.text()
                        print(f"✅ Trading API response received")
                        
                        # Parse XML for item IDs
                        import re
                        item_ids = re.findall(r'<ItemID>(.*?)</ItemID>', xml_response)
                        titles = re.findall(r'<Title>(.*?)</Title>', xml_response)
                        
                        if item_ids:
                            print(f"🎯 FOUND {len(item_ids)} REAL ITEM IDs:")
                            
                            for i, item_id in enumerate(item_ids):
                                title = titles[i] if i < len(titles) else 'N/A'
                                verification_url = f"https://www.ebay.com/itm/{item_id}"
                                
                                print(f"\n📦 Item {i+1}:")
                                print(f"   🆔 Item ID: {item_id}")
                                print(f"   📝 Title: {title}")
                                print(f"   🔗 Verify at: {verification_url}")
                            
                            # Return the first item for verification
                            return {
                                "item_id": item_ids[0],
                                "title": titles[0] if titles else 'N/A',
                                "source": "trading_api",
                                "verification_url": f"https://www.ebay.com/itm/{item_ids[0]}",
                                "all_items": [
                                    {
                                        "item_id": item_ids[i],
                                        "title": titles[i] if i < len(titles) else 'N/A',
                                        "verification_url": f"https://www.ebay.com/itm/{item_ids[i]}"
                                    }
                                    for i in range(len(item_ids))
                                ]
                            }
                        else:
                            print("📝 No item IDs found in Trading API response")
                            # Print part of the XML response for debugging
                            print(f"XML Response (first 500 chars): {xml_response[:500]}...")
                    else:
                        print(f"❌ Trading API failed: HTTP {trading_response.status}")
                        error_text = await trading_response.text()
                        print(f"   Error: {error_text[:200]}...")
                
                # Method 3: Try Browse API to search for seller's items
                print(f"\n📦 Method 3: Trying Browse API...")
                
                # First, get seller info
                browse_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
                }
                
                # Search for items by the authenticated seller
                search_url = "https://api.ebay.com/buy/browse/v1/item_summary/search?q=apple&filter=sellers:{seller_username}"
                
                async with session.get(search_url, headers=browse_headers) as browse_response:
                    if browse_response.status == 200:
                        browse_data = await browse_response.json()
                        items = browse_data.get('itemSummaries', [])
                        
                        print(f"✅ Browse API found {len(items)} items")
                        
                        for i, item in enumerate(items):
                            item_id = item.get('itemId')
                            title = item.get('title')
                            
                            if item_id:
                                print(f"\n📦 Browse Item {i+1}:")
                                print(f"   🆔 Item ID: {item_id}")
                                print(f"   📝 Title: {title}")
                                print(f"   🔗 Verify at: https://www.ebay.com/itm/{item_id}")
                                
                                return {
                                    "item_id": item_id,
                                    "title": title,
                                    "source": "browse_api",
                                    "verification_url": f"https://www.ebay.com/itm/{item_id}"
                                }
                    else:
                        print(f"⚠️ Browse API failed: HTTP {browse_response.status}")
                        error_text = await browse_response.text()
                        print(f"   Error: {error_text[:200]}...")
                
                print("\n❌ No verifiable eBay item IDs found")
                print("📝 This suggests:")
                print("   - The inventory items may not be actively listed")
                print("   - Items may be in draft/unlisted state")
                print("   - Different API permissions may be needed")
                
                return None
                
    except Exception as e:
        print(f"❌ Error getting real eBay item details: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("🚀 Getting Real eBay Item ID for Verification")
    print("=" * 60)
    
    item_details = await get_real_ebay_item_details()
    
    if item_details:
        print("\n" + "=" * 60)
        print("🎯 REAL EBAY ITEM FOUND!")
        print("=" * 60)
        print(f"🆔 Item ID: {item_details['item_id']}")
        print(f"📝 Title: {item_details['title']}")
        print(f"📊 Source: {item_details['source']}")
        print(f"🔗 Verification URL: {item_details['verification_url']}")
        print("\n✅ You can verify this is a real eBay listing by visiting the URL above!")
        
        if 'all_items' in item_details:
            print(f"\n📦 All Items Found ({len(item_details['all_items'])}):")
            for i, item in enumerate(item_details['all_items']):
                print(f"   {i+1}. {item['item_id']} - {item['title'][:50]}...")
        
        return True
    else:
        print("\n❌ FAILED: No verifiable eBay item IDs found")
        print("📝 The eBay account may not have any actively listed items")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
