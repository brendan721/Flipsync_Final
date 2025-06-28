#!/usr/bin/env python3
"""
Test script to diagnose the Dio HTTPS issue
"""

import requests
import json
import time

def test_environment_file_access():
    """Test if the environment file is accessible and has correct content."""
    print("🔍 Testing Environment File Access")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:3000/assets/assets/config/.env.production")
        if response.status_code == 200:
            content = response.text
            print("✅ Environment file accessible")
            
            # Check for HTTP vs HTTPS URLs
            if "API_BASE_URL=http://localhost:8001" in content:
                print("✅ API_BASE_URL correctly set to HTTP")
            elif "API_BASE_URL=https://localhost:8001" in content:
                print("❌ API_BASE_URL incorrectly set to HTTPS")
                return False
            else:
                print("⚠️  API_BASE_URL not found in environment file")
                
            # Show relevant lines
            for line in content.split('\n'):
                if 'API_BASE_URL' in line or 'BASE_URL' in line:
                    print(f"  📝 {line}")
                    
            return True
        else:
            print(f"❌ Environment file not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing environment file: {e}")
        return False

def test_backend_connectivity():
    """Test backend connectivity on both HTTP and HTTPS."""
    print("\n🔗 Testing Backend Connectivity")
    print("=" * 50)
    
    # Test HTTP (should work)
    try:
        response = requests.get("http://localhost:8001/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ HTTP backend accessible on port 8001")
        else:
            print(f"⚠️  HTTP backend returned: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTP backend not accessible: {e}")
        
    # Test HTTPS (should fail)
    try:
        response = requests.get("https://localhost:8001/api/v1/health", timeout=5, verify=False)
        if response.status_code == 200:
            print("⚠️  HTTPS backend unexpectedly accessible on port 8001")
        else:
            print(f"✅ HTTPS backend correctly not accessible: {response.status_code}")
    except Exception as e:
        print(f"✅ HTTPS backend correctly not accessible: {e}")

def test_cors_configuration():
    """Test CORS configuration for OAuth endpoints."""
    print("\n🌐 Testing CORS Configuration")
    print("=" * 50)
    
    try:
        # Test preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = requests.options(
            "http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            cors_origin = response.headers.get("access-control-allow-origin", "")
            if cors_origin == "http://localhost:3000":
                print("✅ CORS correctly configured for HTTP")
            elif cors_origin == "https://localhost:3000":
                print("❌ CORS incorrectly configured for HTTPS")
                return False
            else:
                print(f"⚠️  CORS origin: {cors_origin}")
                
            print(f"  📝 CORS Origin: {cors_origin}")
            print(f"  📝 CORS Methods: {response.headers.get('access-control-allow-methods', '')}")
            return True
        else:
            print(f"❌ CORS preflight failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False

def test_oauth_url_generation():
    """Test OAuth URL generation."""
    print("\n🔗 Testing OAuth URL Generation")
    print("=" * 50)
    
    try:
        oauth_data = {
            "scopes": ["https://api.ebay.com/oauth/api_scope"]
        }
        
        response = requests.post(
            "http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize",
            json=oauth_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            oauth_response = data.get("data", {})
            auth_url = oauth_response.get("authorization_url", "")
            state = oauth_response.get("state", "")
            
            print("✅ OAuth URL generated successfully")
            print(f"  🔑 State: {state}")
            print(f"  🌐 Auth URL: {auth_url[:100]}...")
            return True
        else:
            print(f"❌ OAuth URL generation failed: {response.status_code}")
            print(f"  📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OAuth URL generation error: {e}")
        return False

def test_flutter_app_access():
    """Test Flutter app accessibility."""
    print("\n📱 Testing Flutter App Access")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:3000/", timeout=5)
        if response.status_code == 200:
            print("✅ Flutter app accessible")
            
            # Check if it contains Flutter bootstrap
            if "flutter_bootstrap.js" in response.text:
                print("✅ Flutter bootstrap found")
            else:
                print("⚠️  Flutter bootstrap not found")
                
            return True
        else:
            print(f"❌ Flutter app not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Flutter app access error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Dio HTTPS Issue Diagnostic Test")
    print("=" * 60)
    
    tests = [
        test_environment_file_access,
        test_backend_connectivity,
        test_cors_configuration,
        test_oauth_url_generation,
        test_flutter_app_access,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    test_names = [
        "Environment File Access",
        "Backend Connectivity", 
        "CORS Configuration",
        "OAuth URL Generation",
        "Flutter App Access"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📈 Overall Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The issue might be in the Flutter app configuration.")
        print("\n💡 Recommendations:")
        print("1. Check Flutter app environment loading logic")
        print("2. Verify no hardcoded HTTPS URLs in Flutter code")
        print("3. Clear browser cache and test in incognito mode")
        print("4. Check browser console for JavaScript errors")
    else:
        print("🔧 Some tests failed. Fix the failing components first.")

if __name__ == "__main__":
    main()
