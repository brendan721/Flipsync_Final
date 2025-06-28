#!/usr/bin/env python3
"""
Test script to verify eBay OAuth functionality
"""
import requests
import json
import sys

def test_oauth_callback():
    """Test the eBay OAuth callback endpoint"""
    print("🔍 Testing eBay OAuth Callback...")
    
    # Test the callback with the authorization code
    callback_url = "http://localhost:8001/api/v1/marketplace/ebay/oauth/callback"
    params = {
        "code": "v^1.1#i^1#f^0#r^1#p^3#I^3#t^Ul41XzU6MUUzN0U4RkM5RTA4NDVBRjcyMUEwQUFBNkIxMkZERkJfMV8xI0VeMjYw",
        "state": "j29O_0uV37kfMue9fT-7UkKRxvegajL7_hzoJJbxEfs",
        "expires_in": "299"
    }
    
    try:
        response = requests.get(callback_url, params=params, allow_redirects=False)
        print(f"✅ Callback Response Status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"✅ Redirect Location: {response.headers.get('Location', 'No location header')}")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Callback test failed: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint to ensure API is running"""
    print("🔍 Testing API Health...")
    
    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_oauth_authorize():
    """Test the OAuth authorization endpoint"""
    print("🔍 Testing eBay OAuth Authorization...")
    
    try:
        response = requests.get("http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize", allow_redirects=False)
        print(f"✅ Authorization Response Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'ebay.com' in location:
                print(f"✅ Redirects to eBay: {location[:100]}...")
                return True
            else:
                print(f"❌ Unexpected redirect: {location}")
                return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authorization test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting eBay OAuth Tests...")
    print("=" * 50)
    
    tests = [
        ("API Health", test_health_endpoint),
        ("OAuth Authorization", test_oauth_authorize),
        ("OAuth Callback", test_oauth_callback),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        result = test_func()
        results.append((test_name, result))
        print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! eBay OAuth is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
