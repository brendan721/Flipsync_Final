#!/usr/bin/env python3
"""
Verify Your eBay Connection - Test your actual eBay account after OAuth
"""

import asyncio
import aiohttp
import json

async def verify_your_ebay_connection():
    """Verify your actual eBay connection after OAuth callback."""
    print("🎯 VERIFYING YOUR EBAY CONNECTION")
    print("=" * 60)
    print("🎉 OAuth callback completed successfully!")
    print("🔍 Testing if your eBay account is fully connected...")
    print("=" * 60)
    
    backend_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Authenticate
        print("\n🔐 STEP 1: FlipSync Authentication")
        print("-" * 50)
        try:
            login_data = {
                "email": "test@example.com",
                "password": "SecurePassword!"
            }
            async with session.post(f"{backend_url}/api/v1/auth/login", json=login_data) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    access_token = auth_data.get('access_token')
                    print(f"   ✅ Authentication: SUCCESS")
                else:
                    print(f"   ❌ Authentication: FAILED ({response.status})")
                    return False
        except Exception as e:
            print(f"   ❌ Authentication: ERROR - {e}")
            return False
        
        # Step 2: Check eBay connection status
        print("\n📊 STEP 2: eBay Connection Status")
        print("-" * 50)
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            async with session.get(f"{backend_url}/api/v1/marketplace/ebay/status", headers=headers) as response:
                if response.status == 200:
                    status_data = await response.json()
                    data = status_data.get('data', {})
                    ebay_connected = data.get('ebay_connected', False)
                    credentials_valid = data.get('credentials_valid', False)
                    
                    print(f"   📊 eBay Connected: {'✅ YES' if ebay_connected else '❌ NO'}")
                    print(f"   🔐 Credentials Valid: {'✅ YES' if credentials_valid else '❌ NO'}")
                    
                    if ebay_connected and credentials_valid:
                        print(f"   🎉 Your eBay account is connected!")
                        connection_success = True
                    else:
                        print(f"   ⚠️  Connection issues detected")
                        connection_success = False
                        
                else:
                    print(f"   ❌ Status check failed: {response.status}")
                    connection_success = False
        except Exception as e:
            print(f"   ❌ Status check error: {e}")
            connection_success = False
        
        # Step 3: Test inventory retrieval
        print("\n📦 STEP 3: Your eBay Inventory")
        print("-" * 50)
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            async with session.get(f"{backend_url}/api/v1/marketplace/ebay/listings", headers=headers) as response:
                print(f"   📊 Request Status: {response.status}")
                
                if response.status == 200:
                    listings_data = await response.json()
                    data = listings_data.get('data', {})
                    listings = data.get('listings', [])
                    total_count = data.get('total', 0)
                    
                    print(f"   ✅ Inventory Retrieved: SUCCESS")
                    print(f"   📦 Total Listings: {total_count}")
                    
                    if total_count > 0:
                        print(f"   🎉 Found your {total_count} eBay listings!")
                        
                        if listings:
                            print(f"\n   📝 Your eBay Listings:")
                            for i, listing in enumerate(listings[:5]):
                                print(f"      {i+1}. {listing.get('title', 'N/A')[:50]}...")
                                print(f"         Price: ${listing.get('price', 'N/A')}")
                                print(f"         Status: {listing.get('status', 'N/A')}")
                        
                        inventory_success = True
                    else:
                        print(f"   💡 No listings found")
                        print(f"   📋 Your eBay account may have no active listings")
                        inventory_success = True  # Connection works, just no listings
                        
                elif response.status == 401:
                    print(f"   ❌ Authentication required")
                    inventory_success = False
                else:
                    print(f"   ❌ Failed: {response.status}")
                    inventory_success = False
                    
        except Exception as e:
            print(f"   ❌ Inventory error: {e}")
            inventory_success = False
        
        # Final results
        print("\n" + "=" * 60)
        print("🎯 YOUR EBAY CONNECTION RESULTS")
        print("=" * 60)
        
        if connection_success and inventory_success:
            print("🎉 SUCCESS: YOUR EBAY ACCOUNT IS FULLY CONNECTED!")
            print("✅ OAuth flow completed")
            print("✅ eBay credentials stored and valid")
            print("✅ FlipSync can access your eBay data")
            print("✅ Inventory retrieval working")
            print()
            print("🚀 MISSION ACCOMPLISHED!")
            print("   You have successfully connected your eBay account to FlipSync")
            print("   and can now pull in your inventory!")
            
        elif connection_success:
            print("✅ PARTIAL SUCCESS:")
            print("✅ eBay account connected")
            print("⚠️  Inventory access needs verification")
            
        else:
            print("❌ CONNECTION ISSUES:")
            print("❌ eBay account not properly connected")
            print("💡 OAuth may need to be repeated")
        
        print("=" * 60)
        
        return connection_success and inventory_success

if __name__ == "__main__":
    success = asyncio.run(verify_your_ebay_connection())
    exit(0 if success else 1)
