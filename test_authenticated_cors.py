#!/usr/bin/env python3
"""
Test Authenticated CORS - Replicate browser's authenticated requests
"""

import asyncio
import aiohttp
import json

async def test_authenticated_cors():
    """Test CORS with authenticated requests like the browser does."""
    print("🔐 TESTING AUTHENTICATED CORS FLOW")
    print("=" * 60)
    
    backend_url = "http://localhost:8001"
    frontend_url = "http://localhost:3000"
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Authenticate to get token
        print("\n1️⃣ Authenticating to get token...")
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
                    print(f"   🔑 Token: {access_token[:20]}...")
                else:
                    print(f"   ❌ Authentication: FAILED ({response.status})")
                    return
        except Exception as e:
            print(f"   ❌ Authentication: ERROR - {e}")
            return
        
        # Step 2: Test authenticated preflight requests
        print("\n2️⃣ Testing Authenticated Preflight Requests...")
        
        # eBay Status with auth
        try:
            headers = {
                'Origin': frontend_url,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'authorization,content-type',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            async with session.options(
                f"{backend_url}/api/v1/marketplace/ebay/status", 
                headers=headers
            ) as response:
                print(f"   📊 eBay Status Preflight: {response.status}")
                if response.status != 200:
                    response_text = await response.text()
                    print(f"   ❌ Failed: {response_text}")
                else:
                    print(f"   ✅ eBay Status Preflight: SUCCESS")
                    
        except Exception as e:
            print(f"   ❌ eBay Status Preflight Error: {e}")
        
        # Step 3: Test authenticated GET requests
        print("\n3️⃣ Testing Authenticated GET Requests...")
        
        try:
            headers = {
                'Origin': frontend_url,
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            async with session.get(
                f"{backend_url}/api/v1/marketplace/ebay/status", 
                headers=headers
            ) as response:
                print(f"   📊 eBay Status GET: {response.status}")
                if response.status == 200:
                    print(f"   ✅ eBay Status GET: SUCCESS")
                    data = await response.json()
                    print(f"   📋 Connected: {data.get('data', {}).get('ebay_connected', False)}")
                else:
                    print(f"   ❌ eBay Status GET: FAILED")
                    response_text = await response.text()
                    print(f"   📋 Error: {response_text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ eBay Status GET Error: {e}")
        
        # Step 4: Test inventory/listings endpoint
        print("\n4️⃣ Testing Inventory/Listings Endpoint...")
        
        try:
            # Preflight first
            headers = {
                'Origin': frontend_url,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'authorization,content-type',
            }
            
            async with session.options(
                f"{backend_url}/api/v1/marketplace/ebay/listings", 
                headers=headers
            ) as response:
                print(f"   📊 Listings Preflight: {response.status}")
                
            # Then actual request
            headers = {
                'Origin': frontend_url,
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
            }
            
            async with session.get(
                f"{backend_url}/api/v1/marketplace/ebay/listings", 
                headers=headers
            ) as response:
                print(f"   📊 Listings GET: {response.status}")
                if response.status == 200:
                    print(f"   ✅ Listings GET: SUCCESS")
                else:
                    print(f"   ❌ Listings GET: FAILED")
                    response_text = await response.text()
                    print(f"   📋 Error: {response_text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Listings Error: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 AUTHENTICATED CORS TEST COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_authenticated_cors())
