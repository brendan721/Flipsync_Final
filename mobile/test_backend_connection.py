#!/usr/bin/env python3
"""
Test script to verify Flutter app can connect to the backend API
"""

import requests
import json
import sys

def test_endpoint(url, description):
    """Test a single API endpoint"""
    try:
        print(f"🔍 Testing {description}...")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS: {description}")
            print(f"   📊 Response: {json.dumps(data, indent=2)[:200]}...")
            return True
        else:
            print(f"   ❌ FAILED: {description} - Status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ ERROR: {description} - {str(e)}")
        return False

def main():
    print("🚀 FlipSync Backend Connection Test")
    print("=" * 50)
    
    base_url = "http://localhost:8001/api/v1"
    
    # Test endpoints that the Flutter app will use
    endpoints = [
        (f"{base_url}/marketplace/products", "Marketplace Products (Fixed Endpoint)"),
        (f"{base_url}/agents/", "Agent Status"),
        (f"{base_url}/health", "Health Check"),
        ("http://localhost:8001/health", "Root Health Check"),
    ]
    
    passed = 0
    total = len(endpoints)
    
    for url, description in endpoints:
        if test_endpoint(url, description):
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} endpoints working")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Flutter app can connect to backend!")
        print("🚀 Ready to start Flutter web app on port 3000")
    elif passed > 0:
        print("⚠️  PARTIAL SUCCESS - Some endpoints working")
        print("🔧 Flutter app may have limited functionality")
    else:
        print("❌ ALL TESTS FAILED - Backend connection issues")
        print("🛑 Check if backend is running on port 8001")
        sys.exit(1)
    
    print("\n📱 Next Steps:")
    print("1. Run: python3 serve_flutter_web.py")
    print("2. Open: http://localhost:3000")
    print("3. Test the Flutter app with the working backend")

if __name__ == "__main__":
    main()
