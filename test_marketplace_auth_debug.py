#!/usr/bin/env python3
"""
Debug marketplace authentication issues
"""
import asyncio
import aiohttp
import json

async def debug_marketplace_auth():
    print("🔍 DEBUGGING MARKETPLACE AUTHENTICATION")
    print("=" * 60)
    
    # First get auth token
    login_data = {'email': 'test@example.com', 'password': 'SecurePassword!'}
    
    async with aiohttp.ClientSession() as session:
        # Login
        print("1. Testing login...")
        async with session.post('http://localhost:8001/api/v1/auth/login', 
                              json=login_data) as response:
            print(f"   Login status: {response.status}")
            if response.status == 200:
                auth_data = await response.json()
                token = auth_data.get('access_token')
                print(f"   ✅ Got auth token: {token[:50]}...")
                
                # Test marketplace status
                print("\n2. Testing marketplace status...")
                headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
                async with session.get('http://localhost:8001/api/v1/marketplace/status', 
                                     headers=headers) as status_response:
                    print(f"   Status endpoint: {status_response.status}")
                    if status_response.status == 200:
                        status_data = await status_response.json()
                        print(f"   ✅ Status data: {status_data}")
                    else:
                        error_text = await status_response.text()
                        print(f"   ❌ Status error: {error_text}")
                
                # Test eBay OAuth with detailed debugging
                print("\n3. Testing eBay OAuth authorize...")
                oauth_data = {
                    'scopes': [
                        'https://api.ebay.com/oauth/api_scope',
                        'https://api.ebay.com/oauth/api_scope/sell.inventory'
                    ]
                }
                
                print(f"   Request URL: http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize")
                print(f"   Request headers: {headers}")
                print(f"   Request data: {oauth_data}")
                
                async with session.post('http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize',
                                      json=oauth_data, headers=headers) as oauth_response:
                    print(f"   OAuth status: {oauth_response.status}")
                    response_text = await oauth_response.text()
                    print(f"   OAuth response: {response_text}")
                    
                    if oauth_response.status == 200:
                        try:
                            oauth_result = json.loads(response_text)
                            auth_url = oauth_result.get('data', {}).get('authorization_url', '')
                            print(f"   ✅ OAuth URL generated: {auth_url[:100]}...")
                        except:
                            print(f"   ⚠️ OAuth response not JSON: {response_text}")
                    elif oauth_response.status == 401:
                        print(f"   ❌ Authentication failed - token may be invalid")
                    elif oauth_response.status == 404:
                        print(f"   ❌ Endpoint not found - routing issue")
                    elif oauth_response.status == 500:
                        print(f"   ⚠️ Server error - likely missing eBay credentials")
                    else:
                        print(f"   ❌ Unexpected status: {oauth_response.status}")
                
                # Test if eBay router is accessible
                print("\n4. Testing eBay status endpoint...")
                async with session.get('http://localhost:8001/api/v1/marketplace/ebay/status',
                                     headers=headers) as ebay_status_response:
                    print(f"   eBay status: {ebay_status_response.status}")
                    if ebay_status_response.status == 200:
                        ebay_data = await ebay_status_response.json()
                        print(f"   ✅ eBay status: {ebay_data}")
                    else:
                        ebay_error = await ebay_status_response.text()
                        print(f"   ❌ eBay status error: {ebay_error}")
                        
            else:
                error_text = await response.text()
                print(f"   ❌ Login failed: {response.status} - {error_text}")

if __name__ == "__main__":
    asyncio.run(debug_marketplace_auth())
