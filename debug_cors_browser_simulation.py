#!/usr/bin/env python3
"""
Debug CORS Browser Simulation - Exactly replicate what the browser is doing
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def debug_cors_browser_simulation():
    """Simulate exactly what the browser is doing when navigating to inventory screen."""
    print("🔍 DEBUGGING CORS - BROWSER SIMULATION")
    print("=" * 70)
    print("🎯 Goal: Replicate the exact CORS failures from Chrome logs")
    print("=" * 70)
    
    backend_url = "http://localhost:8001"
    frontend_url = "http://localhost:3000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Exact preflight request for eBay status
        print("\n1️⃣ Testing eBay Status Preflight (Exact Browser Simulation)")
        print("-" * 60)
        try:
            headers = {
                'Origin': frontend_url,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'content-type',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            async with session.options(
                f"{backend_url}/api/v1/marketplace/ebay/status/public", 
                headers=headers
            ) as response:
                print(f"   📊 Status Code: {response.status}")
                print(f"   📋 Status Text: {response.reason}")
                
                if response.status == 200:
                    print(f"   ✅ Preflight: SUCCESS")
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    cors_methods = response.headers.get('Access-Control-Allow-Methods')
                    cors_headers = response.headers.get('Access-Control-Allow-Headers')
                    cors_credentials = response.headers.get('Access-Control-Allow-Credentials')
                    
                    print(f"   🌐 Allow-Origin: {cors_origin}")
                    print(f"   🔧 Allow-Methods: {cors_methods}")
                    print(f"   📝 Allow-Headers: {cors_headers}")
                    print(f"   🔐 Allow-Credentials: {cors_credentials}")
                else:
                    print(f"   ❌ Preflight: FAILED")
                    response_text = await response.text()
                    print(f"   📋 Response: {response_text}")
                    
        except Exception as e:
            print(f"   ❌ Preflight Error: {e}")
        
        # Test 2: Exact preflight request for analytics dashboard
        print("\n2️⃣ Testing Analytics Dashboard Preflight (Exact Browser Simulation)")
        print("-" * 60)
        try:
            headers = {
                'Origin': frontend_url,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'content-type',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            async with session.options(
                f"{backend_url}/api/v1/analytics/dashboard", 
                headers=headers
            ) as response:
                print(f"   📊 Status Code: {response.status}")
                print(f"   📋 Status Text: {response.reason}")
                
                if response.status == 200:
                    print(f"   ✅ Preflight: SUCCESS")
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    cors_methods = response.headers.get('Access-Control-Allow-Methods')
                    cors_headers = response.headers.get('Access-Control-Allow-Headers')
                    cors_credentials = response.headers.get('Access-Control-Allow-Credentials')
                    
                    print(f"   🌐 Allow-Origin: {cors_origin}")
                    print(f"   🔧 Allow-Methods: {cors_methods}")
                    print(f"   📝 Allow-Headers: {cors_headers}")
                    print(f"   🔐 Allow-Credentials: {cors_credentials}")
                else:
                    print(f"   ❌ Preflight: FAILED")
                    response_text = await response.text()
                    print(f"   📋 Response: {response_text}")
                    
        except Exception as e:
            print(f"   ❌ Preflight Error: {e}")
        
        # Test 3: Follow up with actual GET requests
        print("\n3️⃣ Testing Actual GET Requests (After Preflight)")
        print("-" * 60)
        
        # eBay Status GET
        try:
            headers = {
                'Origin': frontend_url,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            async with session.get(
                f"{backend_url}/api/v1/marketplace/ebay/status/public", 
                headers=headers
            ) as response:
                print(f"   📊 eBay Status GET: {response.status}")
                if response.status == 200:
                    print(f"   ✅ eBay Status: SUCCESS")
                else:
                    print(f"   ❌ eBay Status: FAILED")
                    
        except Exception as e:
            print(f"   ❌ eBay Status GET Error: {e}")
        
        # Analytics Dashboard GET
        try:
            async with session.get(
                f"{backend_url}/api/v1/analytics/dashboard", 
                headers=headers
            ) as response:
                print(f"   📊 Analytics Dashboard GET: {response.status}")
                if response.status == 200:
                    print(f"   ✅ Analytics Dashboard: SUCCESS")
                else:
                    print(f"   ❌ Analytics Dashboard: FAILED")
                    
        except Exception as e:
            print(f"   ❌ Analytics Dashboard GET Error: {e}")
        
        # Test 4: Check if server is overloaded or timing out
        print("\n4️⃣ Testing Server Performance")
        print("-" * 60)
        
        start_time = datetime.now()
        try:
            async with session.get(f"{backend_url}/api/v1/health") as response:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                print(f"   📊 Health Check: {response.status}")
                print(f"   ⏱️  Response Time: {response_time:.3f}s")
                
                if response_time > 5.0:
                    print(f"   ⚠️  Server is slow (>{response_time:.1f}s)")
                elif response_time > 2.0:
                    print(f"   ⚠️  Server is sluggish (>{response_time:.1f}s)")
                else:
                    print(f"   ✅ Server response time is good")
                    
        except Exception as e:
            print(f"   ❌ Health Check Error: {e}")
        
        # Test 5: Check for rate limiting
        print("\n5️⃣ Testing Rate Limiting")
        print("-" * 60)
        
        for i in range(5):
            try:
                async with session.options(
                    f"{backend_url}/api/v1/marketplace/ebay/status/public",
                    headers={'Origin': frontend_url}
                ) as response:
                    rate_limit = response.headers.get('X-RateLimit-Limit')
                    rate_remaining = response.headers.get('X-RateLimit-Remaining')
                    print(f"   📊 Request {i+1}: {response.status} (Limit: {rate_limit}, Remaining: {rate_remaining})")
                    
                    if response.status == 429:
                        print(f"   ⚠️  Rate limited!")
                        break
                        
            except Exception as e:
                print(f"   ❌ Rate limit test {i+1} error: {e}")
        
        print("\n" + "=" * 70)
        print("🎯 CORS DEBUG ANALYSIS COMPLETE")
        print("=" * 70)
        print("📋 Key Findings:")
        print("   • Check if preflight requests are returning 200 OK")
        print("   • Verify CORS headers are present and correct")
        print("   • Monitor server response times")
        print("   • Check for rate limiting issues")
        print("   • Compare with actual browser behavior")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(debug_cors_browser_simulation())
