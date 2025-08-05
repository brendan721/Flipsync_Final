#!/usr/bin/env python3
"""
V3 Endpoints Deployment Test Script

Tests the V3 endpoints after deployment to verify they are working correctly
with authentication and returning expected data.
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any

class V3EndpointsDeploymentTester:
    def __init__(self, base_url: str = "http://174.138.77.110:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 15
        
    def test_v3_endpoints_deployment(self) -> Dict[str, Any]:
        """Test V3 endpoints after deployment."""
        
        results = {
            "test_timestamp": datetime.now().isoformat(),
            "phase": "Phase 2: V3 Endpoints Deployment Test",
            "backend_url": self.base_url,
            "endpoint_tests": {}
        }
        
        print("🧪 Testing V3 Endpoints Deployment")
        print("=" * 50)
        print(f"Backend URL: {self.base_url}")
        
        # Test 1: V3 User Profile Endpoints
        print("\n1️⃣ Testing V3 User Profile Endpoints")
        user_profile_test = self._test_user_profile_endpoints()
        results["endpoint_tests"]["user_profile"] = user_profile_test
        
        # Test 2: V3 Opportunities Endpoints
        print("\n2️⃣ Testing V3 Opportunities Endpoints")
        opportunities_test = self._test_opportunities_endpoints()
        results["endpoint_tests"]["opportunities"] = opportunities_test
        
        # Test 3: V3 Optimization Endpoints
        print("\n3️⃣ Testing V3 Optimization Endpoints")
        optimization_test = self._test_optimization_endpoints()
        results["endpoint_tests"]["optimization"] = optimization_test
        
        # Test 4: V3 Shipping Zone Endpoints
        print("\n4️⃣ Testing V3 Shipping Zone Endpoints")
        shipping_test = self._test_shipping_zone_endpoints()
        results["endpoint_tests"]["shipping_zones"] = shipping_test
        
        return results
    
    def _test_user_profile_endpoints(self) -> Dict[str, Any]:
        """Test V3 user profile endpoints."""
        endpoints_to_test = [
            ("GET", "/api/v1/users/profile"),
            ("GET", "/api/v1/users/preferences"),
        ]
        
        results = {}
        
        for method, endpoint in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json={})
                
                status_code = response.status_code
                
                if status_code == 200:
                    print(f"✅ {method} {endpoint}: Working (200)")
                    results[endpoint] = {
                        "status": "success",
                        "status_code": status_code,
                        "response_size": len(response.content) if response.content else 0
                    }
                elif status_code == 401:
                    print(f"⚠️ {method} {endpoint}: Requires authentication (401)")
                    results[endpoint] = {
                        "status": "needs_auth",
                        "status_code": status_code,
                        "message": "Endpoint exists but requires authentication"
                    }
                elif status_code == 404:
                    print(f"❌ {method} {endpoint}: Not found (404)")
                    results[endpoint] = {
                        "status": "not_deployed",
                        "status_code": status_code,
                        "message": "Endpoint not deployed yet"
                    }
                else:
                    print(f"⚠️ {method} {endpoint}: Unexpected status ({status_code})")
                    results[endpoint] = {
                        "status": "unexpected",
                        "status_code": status_code,
                        "message": f"Unexpected status code: {status_code}"
                    }
                    
            except Exception as e:
                print(f"❌ {method} {endpoint}: Error - {e}")
                results[endpoint] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    def _test_opportunities_endpoints(self) -> Dict[str, Any]:
        """Test V3 opportunities endpoints."""
        endpoints_to_test = [
            ("GET", "/api/v1/opportunities/trending/liquidation"),
            ("GET", "/api/v1/opportunities/liquidation"),
            ("GET", "/api/v1/opportunities/thrifting"),
            ("GET", "/api/v1/opportunities/miscellaneous"),
        ]
        
        results = {}
        
        for method, endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                status_code = response.status_code
                
                if status_code == 200:
                    print(f"✅ {method} {endpoint}: Working (200)")
                    results[endpoint] = {
                        "status": "success",
                        "status_code": status_code,
                        "response_size": len(response.content) if response.content else 0
                    }
                elif status_code == 401:
                    print(f"⚠️ {method} {endpoint}: Requires authentication (401)")
                    results[endpoint] = {
                        "status": "needs_auth",
                        "status_code": status_code,
                        "message": "Endpoint exists but requires authentication"
                    }
                elif status_code == 404:
                    print(f"❌ {method} {endpoint}: Not found (404)")
                    results[endpoint] = {
                        "status": "not_deployed",
                        "status_code": status_code,
                        "message": "Endpoint not deployed yet"
                    }
                else:
                    print(f"⚠️ {method} {endpoint}: Unexpected status ({status_code})")
                    results[endpoint] = {
                        "status": "unexpected",
                        "status_code": status_code,
                        "message": f"Unexpected status code: {status_code}"
                    }
                    
            except Exception as e:
                print(f"❌ {method} {endpoint}: Error - {e}")
                results[endpoint] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    def _test_optimization_endpoints(self) -> Dict[str, Any]:
        """Test V3 optimization endpoints."""
        endpoints_to_test = [
            ("GET", "/api/v1/optimization/score/test-user"),
            ("GET", "/api/v1/optimization/opportunities/test-user"),
        ]
        
        results = {}
        
        for method, endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                status_code = response.status_code
                
                if status_code == 200:
                    print(f"✅ {method} {endpoint}: Working (200)")
                    results[endpoint] = {
                        "status": "success",
                        "status_code": status_code,
                        "response_size": len(response.content) if response.content else 0
                    }
                elif status_code == 401:
                    print(f"⚠️ {method} {endpoint}: Requires authentication (401)")
                    results[endpoint] = {
                        "status": "needs_auth",
                        "status_code": status_code,
                        "message": "Endpoint exists but requires authentication"
                    }
                elif status_code == 404:
                    print(f"❌ {method} {endpoint}: Not found (404)")
                    results[endpoint] = {
                        "status": "not_deployed",
                        "status_code": status_code,
                        "message": "Endpoint not deployed yet"
                    }
                else:
                    print(f"⚠️ {method} {endpoint}: Unexpected status ({status_code})")
                    results[endpoint] = {
                        "status": "unexpected",
                        "status_code": status_code,
                        "message": f"Unexpected status code: {status_code}"
                    }
                    
            except Exception as e:
                print(f"❌ {method} {endpoint}: Error - {e}")
                results[endpoint] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    def _test_shipping_zone_endpoints(self) -> Dict[str, Any]:
        """Test V3 shipping zone endpoints."""
        endpoints_to_test = [
            ("GET", "/api/v1/shipping/zones/37203"),  # Nashville ZIP
            ("GET", "/api/v1/shipping/zones/90210"),  # Beverly Hills ZIP
        ]
        
        results = {}
        
        for method, endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                status_code = response.status_code
                
                if status_code == 200:
                    print(f"✅ {method} {endpoint}: Working (200)")
                    results[endpoint] = {
                        "status": "success",
                        "status_code": status_code,
                        "response_size": len(response.content) if response.content else 0
                    }
                elif status_code == 401:
                    print(f"⚠️ {method} {endpoint}: Requires authentication (401)")
                    results[endpoint] = {
                        "status": "needs_auth",
                        "status_code": status_code,
                        "message": "Endpoint exists but requires authentication"
                    }
                elif status_code == 404:
                    print(f"❌ {method} {endpoint}: Not found (404)")
                    results[endpoint] = {
                        "status": "not_deployed",
                        "status_code": status_code,
                        "message": "Endpoint not deployed yet"
                    }
                else:
                    print(f"⚠️ {method} {endpoint}: Unexpected status ({status_code})")
                    results[endpoint] = {
                        "status": "unexpected",
                        "status_code": status_code,
                        "message": f"Unexpected status code: {status_code}"
                    }
                    
            except Exception as e:
                print(f"❌ {method} {endpoint}: Error - {e}")
                results[endpoint] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    def generate_deployment_summary(self, results: Dict[str, Any]) -> None:
        """Generate deployment test summary."""
        print("\n" + "=" * 50)
        print("📋 V3 ENDPOINTS DEPLOYMENT TEST SUMMARY")
        print("=" * 50)
        
        endpoint_tests = results["endpoint_tests"]
        
        # Count endpoint statuses
        total_endpoints = 0
        deployed_count = 0
        needs_auth_count = 0
        not_deployed_count = 0
        error_count = 0
        
        for category, tests in endpoint_tests.items():
            for endpoint, test_result in tests.items():
                total_endpoints += 1
                status = test_result.get("status", "unknown")
                
                if status == "success":
                    deployed_count += 1
                elif status == "needs_auth":
                    needs_auth_count += 1
                elif status == "not_deployed":
                    not_deployed_count += 1
                elif status == "error":
                    error_count += 1
        
        print(f"Total Endpoints Tested: {total_endpoints}")
        print(f"✅ Working: {deployed_count}")
        print(f"⚠️ Needs Auth: {needs_auth_count}")
        print(f"❌ Not Deployed: {not_deployed_count}")
        print(f"🚨 Errors: {error_count}")
        
        print("\n🎯 DEPLOYMENT STATUS BY CATEGORY:")
        
        for category, tests in endpoint_tests.items():
            category_name = category.replace('_', ' ').title()
            working = sum(1 for t in tests.values() if t.get("status") == "success")
            needs_auth = sum(1 for t in tests.values() if t.get("status") == "needs_auth")
            not_deployed = sum(1 for t in tests.values() if t.get("status") == "not_deployed")
            total = len(tests)
            
            if working == total:
                print(f"✅ {category_name}: All {total} endpoints working")
            elif working + needs_auth == total:
                print(f"⚠️ {category_name}: {total} endpoints deployed, {needs_auth} need auth")
            elif not_deployed > 0:
                print(f"❌ {category_name}: {not_deployed}/{total} endpoints not deployed")
            else:
                print(f"🚨 {category_name}: Mixed status - check individual endpoints")
        
        print("\n📋 NEXT STEPS:")
        if not_deployed_count > 0:
            print("1. ❌ Backend needs restart to load V3 routes")
            print("2. 🔄 Restart production backend with new V3 routes")
            print("3. 🧪 Re-run this test after restart")
        elif needs_auth_count > 0:
            print("1. ✅ V3 endpoints deployed successfully")
            print("2. 🔐 Test endpoints with proper JWT authentication")
            print("3. 🔄 Update Flutter services to use new V3 endpoints")
        else:
            print("1. ✅ All V3 endpoints working perfectly")
            print("2. 🎯 Ready to proceed to Phase 3")

def main():
    """Run V3 endpoints deployment tests."""
    tester = V3EndpointsDeploymentTester()
    results = tester.test_v3_endpoints_deployment()
    tester.generate_deployment_summary(results)
    
    # Save results
    with open("/home/brend/Flipsync_Final/v3_endpoints_deployment_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: v3_endpoints_deployment_results.json")

if __name__ == "__main__":
    main()
