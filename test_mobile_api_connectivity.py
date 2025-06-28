#!/usr/bin/env python3
"""
Mobile App API Connectivity Test
Tests the endpoints that the Flutter mobile app uses to connect to the production API
"""
import requests
import json
import time
import sys

class MobileAPIConnectivityTest:
    def __init__(self):
        self.api_base_url = "http://localhost:8001"
        self.mobile_app_url = "http://localhost:3000"
        self.test_results = []
        
    def test_endpoint(self, endpoint, description, method="GET", data=None, headers=None):
        """Test a single API endpoint"""
        print(f"🔍 Testing: {description}")
        print(f"   URL: {endpoint}")
        
        try:
            if headers is None:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'FlipSync-Mobile-App/1.0'
                }
            
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(endpoint, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(endpoint, json=data, headers=headers, timeout=10)
            else:
                response = requests.request(method, endpoint, json=data, headers=headers, timeout=10)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS - Status: {response.status_code}, Time: {response_time:.2f}s")
                try:
                    json_data = response.json()
                    if isinstance(json_data, dict) and len(json_data) > 0:
                        print(f"   📊 Response contains {len(json_data)} fields")
                    elif isinstance(json_data, list):
                        print(f"   📊 Response contains {len(json_data)} items")
                except:
                    print(f"   📊 Response length: {len(response.text)} chars")
                
                self.test_results.append({
                    'endpoint': endpoint,
                    'description': description,
                    'status': 'PASS',
                    'status_code': response.status_code,
                    'response_time': response_time
                })
                return True
            else:
                print(f"   ❌ FAILED - Status: {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")
                
                self.test_results.append({
                    'endpoint': endpoint,
                    'description': description,
                    'status': 'FAIL',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'error': response.text[:200]
                })
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ CONNECTION ERROR - Cannot connect to {endpoint}")
            self.test_results.append({
                'endpoint': endpoint,
                'description': description,
                'status': 'CONNECTION_ERROR',
                'error': 'Connection refused'
            })
            return False
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT - Request timed out")
            self.test_results.append({
                'endpoint': endpoint,
                'description': description,
                'status': 'TIMEOUT',
                'error': 'Request timeout'
            })
            return False
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            self.test_results.append({
                'endpoint': endpoint,
                'description': description,
                'status': 'ERROR',
                'error': str(e)
            })
            return False
    
    def test_mobile_app_access(self):
        """Test if the mobile app is accessible"""
        print(f"🔍 Testing: Mobile App Accessibility")
        print(f"   URL: {self.mobile_app_url}")
        
        try:
            response = requests.get(self.mobile_app_url, timeout=5)
            if response.status_code == 200 and 'flipsync' in response.text.lower():
                print(f"   ✅ SUCCESS - Mobile app is accessible")
                return True
            else:
                print(f"   ❌ FAILED - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            return False
    
    def run_tests(self):
        """Run all mobile API connectivity tests"""
        print("🚀 FlipSync Mobile API Connectivity Test")
        print("=" * 60)
        print()
        
        # Test mobile app accessibility
        mobile_app_accessible = self.test_mobile_app_access()
        print()
        
        # Test core API endpoints that mobile app uses
        endpoints = [
            (f"{self.api_base_url}/health", "API Health Check"),
            (f"{self.api_base_url}/api/v1/agents/", "Agent Status List"),
            (f"{self.api_base_url}/api/v1/agents/list", "Mobile Agent List"),
            (f"{self.api_base_url}/api/v1/agents/status", "All Agent Statuses"),
            (f"{self.api_base_url}/api/v1/agents/system/metrics", "System Metrics"),
            (f"{self.api_base_url}/docs", "API Documentation"),
            (f"{self.api_base_url}/openapi.json", "OpenAPI Schema"),
        ]
        
        passed = 0
        total = len(endpoints)
        
        for endpoint, description in endpoints:
            if self.test_endpoint(endpoint, description):
                passed += 1
            print()
        
        # Test POST endpoints
        print("🔄 Testing POST Endpoints...")
        print()
        
        post_endpoints = [
            (f"{self.api_base_url}/api/v1/agents/test-connections", "Agent Connection Test", {}),
        ]
        
        for endpoint, description, data in post_endpoints:
            if self.test_endpoint(endpoint, description, method="POST", data=data):
                passed += 1
            total += 1
            print()
        
        # Print summary
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Mobile App Accessible: {'✅ YES' if mobile_app_accessible else '❌ NO'}")
        print(f"API Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        if passed == total and mobile_app_accessible:
            print("🎉 ALL TESTS PASSED! Mobile app can successfully connect to production API!")
            return True
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return False

if __name__ == "__main__":
    tester = MobileAPIConnectivityTest()
    success = tester.run_tests()
    sys.exit(0 if success else 1)
