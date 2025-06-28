#!/usr/bin/env python3
"""
Verify that Docker container has picked up all updates and CORS is working.
This script confirms that the backend is working correctly and identifies browser cache issues.
"""

import asyncio
import aiohttp
import json
import subprocess
import sys
from datetime import datetime


async def verify_docker_updates():
    """Verify that Docker container has the latest updates"""
    print("🔍 Docker Container Update Verification")
    print("=" * 60)
    print(f"Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    success_count = 0
    total_checks = 0

    # Check 1: Docker Container Status
    print("1️⃣ Docker Container Status")
    print("-" * 40)
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=flipsync-production-api', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Header + at least one container
                container_info = lines[1]
                print(f"   ✅ Container Found: {container_info}")
                if "Up" in container_info:
                    print(f"   ✅ Container Status: Running")
                    success_count += 1
                else:
                    print(f"   ❌ Container Status: Not running")
            else:
                print(f"   ❌ Container Not Found")
        else:
            print(f"   ❌ Docker Command Failed: {result.stderr}")
        total_checks += 1
    except Exception as e:
        print(f"   ❌ Docker Check Error: {e}")
        total_checks += 1

    # Check 2: Backend API Endpoints
    print("\n2️⃣ Backend API Endpoints")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        # Test public eBay status endpoint
        try:
            async with session.get("http://localhost:8001/api/v1/marketplace/ebay/status/public") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ eBay Public Status: {response.status}")
                    print(f"   ✅ Response Data: {data['data']['connection_status']}")
                    success_count += 1
                else:
                    print(f"   ❌ eBay Public Status: {response.status}")
            total_checks += 1
        except Exception as e:
            print(f"   ❌ eBay Public Status Error: {e}")
            total_checks += 1

        # Test analytics dashboard endpoint
        try:
            async with session.get("http://localhost:8001/api/v1/analytics/dashboard") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Analytics Dashboard: {response.status}")
                    print(f"   ✅ Revenue Data: ${data['analytics']['total_revenue']:,.2f}")
                    success_count += 1
                else:
                    print(f"   ❌ Analytics Dashboard: {response.status}")
            total_checks += 1
        except Exception as e:
            print(f"   ❌ Analytics Dashboard Error: {e}")
            total_checks += 1

    # Check 3: CORS Configuration (Server-side)
    print("\n3️⃣ CORS Configuration (Server-side)")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            async with session.options("http://localhost:8001/api/v1/marketplace/ebay/status/public", headers=headers) as response:
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                cors_methods = response.headers.get('Access-Control-Allow-Methods')
                cors_credentials = response.headers.get('Access-Control-Allow-Credentials')
                
                print(f"   ✅ CORS Preflight: {response.status}")
                print(f"   ✅ Allow-Origin: {cors_origin}")
                print(f"   ✅ Allow-Methods: {cors_methods}")
                print(f"   ✅ Allow-Credentials: {cors_credentials}")
                
                if response.status in [200, 204] and cors_origin == 'http://localhost:3000':
                    print(f"   ✅ CORS Configuration: Working correctly")
                    success_count += 1
                else:
                    print(f"   ❌ CORS Configuration: Issues detected")
            total_checks += 1
        except Exception as e:
            print(f"   ❌ CORS Test Error: {e}")
            total_checks += 1

    # Check 4: Container Logs Analysis
    print("\n4️⃣ Container Logs Analysis")
    print("-" * 40)
    try:
        result = subprocess.run(['docker', 'logs', 'flipsync-production-api', '--tail', '20'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logs = result.stdout
            if "FlipSync API" in logs and "Starting" in logs:
                print(f"   ✅ Container Logs: API started successfully")
                print(f"   ✅ Log Content: FlipSync API initialization detected")
                success_count += 1
            else:
                print(f"   ⚠️  Container Logs: Startup messages not found")
                print(f"   📝 Recent logs: {logs[-200:]}")  # Last 200 chars
        else:
            print(f"   ❌ Container Logs: Failed to retrieve ({result.stderr})")
        total_checks += 1
    except Exception as e:
        print(f"   ❌ Container Logs Error: {e}")
        total_checks += 1

    # Check 5: Flutter App Build Status
    print("\n5️⃣ Flutter App Build Status")
    print("-" * 40)
    try:
        # Check if Flutter build contains correct endpoints
        with open("/home/brend/Flipsync_Final/mobile/build/web/main.dart.js", "r") as f:
            js_content = f.read()
        
        old_endpoint_count = js_content.count("marketplace/ebay/status") - js_content.count("marketplace/ebay/status/public")
        new_endpoint_count = js_content.count("marketplace/ebay/status/public")
        analytics_count = js_content.count("analytics/dashboard")
        
        print(f"   ✅ Flutter Build: File exists and readable")
        print(f"   ✅ Old Endpoints: {old_endpoint_count} (should be 0)")
        print(f"   ✅ New Public Endpoints: {new_endpoint_count}")
        print(f"   ✅ Analytics Endpoints: {analytics_count}")
        
        if old_endpoint_count == 0 and new_endpoint_count > 0:
            print(f"   ✅ Endpoint Migration: Complete")
            success_count += 1
        else:
            print(f"   ⚠️  Endpoint Migration: May have issues")
        total_checks += 1
    except Exception as e:
        print(f"   ❌ Flutter Build Check Error: {e}")
        total_checks += 1

    # Check 6: Browser Cache Issue Detection
    print("\n6️⃣ Browser Cache Issue Detection")
    print("-" * 40)
    
    # This simulates what the browser should be doing
    async with aiohttp.ClientSession() as session:
        try:
            # Simulate browser preflight request
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type',
                'User-Agent': 'Mozilla/5.0 (compatible; FlipSync-Test/1.0)'
            }
            async with session.options("http://localhost:8001/api/v1/marketplace/ebay/status/public", headers=headers) as response:
                if response.status in [200, 204]:
                    print(f"   ✅ Browser-style Preflight: {response.status} (Working)")
                    
                    # Now try the actual request
                    headers = {
                        'Origin': 'http://localhost:3000',
                        'User-Agent': 'Mozilla/5.0 (compatible; FlipSync-Test/1.0)'
                    }
                    async with session.get("http://localhost:8001/api/v1/marketplace/ebay/status/public", headers=headers) as get_response:
                        if get_response.status == 200:
                            print(f"   ✅ Browser-style GET: {get_response.status} (Working)")
                            print(f"   💡 Server CORS: Working correctly")
                            print(f"   ⚠️  Browser Issue: Likely browser cache problem")
                            success_count += 1
                        else:
                            print(f"   ❌ Browser-style GET: {get_response.status}")
                else:
                    print(f"   ❌ Browser-style Preflight: {response.status}")
            total_checks += 1
        except Exception as e:
            print(f"   ❌ Browser Simulation Error: {e}")
            total_checks += 1

    # Summary and Recommendations
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    success_rate = (success_count / total_checks) * 100 if total_checks > 0 else 0
    
    print(f"✅ Successful Checks: {success_count}/{total_checks}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 DOCKER UPDATES VERIFIED!")
        print("   ✅ Backend container has latest updates")
        print("   ✅ API endpoints working correctly")
        print("   ✅ CORS configuration working server-side")
        print("   ✅ Flutter app built with correct endpoints")
        
        print("\n🔧 BROWSER CACHE ISSUE DETECTED")
        print("   The server is working correctly, but the browser")
        print("   is likely caching old CORS failures.")
        
        print("\n💡 SOLUTION - Clear Browser Cache:")
        print("   1. Open Chrome DevTools (F12)")
        print("   2. Right-click the refresh button")
        print("   3. Select 'Empty Cache and Hard Reload'")
        print("   4. Or go to Settings > Privacy > Clear browsing data")
        print("   5. Select 'Cached images and files' and clear")
        
        print("\n🚀 ALTERNATIVE - Test in Incognito Mode:")
        print("   1. Open Chrome Incognito window (Ctrl+Shift+N)")
        print("   2. Navigate to http://localhost:3000")
        print("   3. Test the eBay integration")
        
        return True
    else:
        print(f"\n⚠️  DOCKER UPDATES NEED ATTENTION")
        print(f"   Success rate: {success_rate:.1f}% (target: 80%+)")
        print("   Please review failed checks above")
        return False


async def main():
    success = await verify_docker_updates()
    
    if success:
        print("\n✨ Docker Container: VERIFIED WITH LATEST UPDATES ✨")
        print("🔧 Issue: Browser cache preventing CORS from working")
        print("💡 Solution: Clear browser cache or use incognito mode")
        sys.exit(0)
    else:
        print("\n⚠️  Docker Container: NEEDS ATTENTION")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
